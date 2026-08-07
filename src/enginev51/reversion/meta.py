"""Pooled LightGBM meta-label, walk-forward by month.

BUILD-SPEC §4; REGISTRATION §3.4. Binary P(win) on decision-time features; label
y = 1{net_bps > 0} for the maker-entry system trade. ONE pooled walk-forward per
hold ceiling: the training population is the UNION of GATED trades across all four
names (the runner concatenates the per-name base events before calling this).
Train on pooled months [start .. m−1], score month m; first scored month = the
13th month of pooled trade history; retrain monthly. Veto at p_win < 0.55 (fixed).
Deterministic (fixed seed, single-threaded).

Training/scoring population = GATED maker-filled trades (passed_G1 & passed_G2),
per BUILD-SPEC §4. When gate columns are absent (unit fixtures) the population
falls back to all maker-filled trades. Trades in months before the first fold —
or in any month whose fold was skipped for insufficient training data — are
UNSCORED: ``meta_scored`` stays False and they are excluded from the ``gated_meta``
verdict stream (see runner ``_summarise``). ``meta_kept`` defaults True (no veto)
and is meaningful only where ``meta_scored`` is True.

Features (decision-time only, BUILD-SPEC §4):
    spread_bps, sigma_5m, |eps|/sigma_5m, ofi_5s, micro_dev_bps,
    time-of-day bucket (30-min), calendar stratum (categorical, M14 defs),
    name (categorical), kappa_hat, (eps−theta)/sigma_stationary
where sigma_stationary = sigma / sqrt(2·kappa) (OU stationary s.d.).

Calendar strata use the M14 LOCKED definitions (M3_REGISTRATION.md §M14):
QUAD_WITCH = 3rd Friday Mar/Jun/Sep/Dec (prior BD if holiday); MONTHLY_OPEX =
3rd Friday other months; MONTH_END = last trading session of the month; else
ORDINARY. NOTE: exact M14 windowing beyond these category names was not part of
the BUILD-SPEC contract — this is a self-contained proxy over the locked names.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import numpy as np
import polars as pl

from enginev51.flows import ffcal

META_THRESHOLD = 0.55
SEED = 42
MIN_TRAIN_MONTHS = 12  # first scored month is the 13th

FEATURE_NUMERIC = [
    "spread_bps", "sigma_5m", "abs_eps_over_sigma5", "ofi_5s", "micro_dev_bps",
    "tod_bucket", "kappa", "eps_over_sigma_stat",
]
FEATURE_CATEGORICAL = ["name_code", "stratum_code"]
FEATURES = FEATURE_NUMERIC + FEATURE_CATEGORICAL

_STRATA = ["ORDINARY", "MONTH_END", "MONTHLY_OPEX", "QUAD_WITCH"]
_STRATUM_CODE = {s: i for i, s in enumerate(_STRATA)}


def calendar_stratum(session_iso: str) -> str:
    """M14 locked strata over {QUAD_WITCH, MONTHLY_OPEX, MONTH_END, ORDINARY}."""
    y, m, d = (int(x) for x in session_iso.split("-"))
    sd = dt.date(y, m, d)
    hols = ffcal.us_holidays(y) | ffcal.us_holidays(y - 1) | ffcal.us_holidays(y + 1)
    opex = ffcal.prev_bd(ffcal.nth_weekday(y, m, 4, 3), hols)  # 3rd Friday → prior BD
    if sd == opex:
        return "QUAD_WITCH" if m in (3, 6, 9, 12) else "MONTHLY_OPEX"
    tds = ffcal.trading_days(y, m, hols)
    if tds and sd == tds[-1]:
        return "MONTH_END"
    return "ORDINARY"


def _month_key(ts_ns: int) -> str:
    d = dt.datetime.fromtimestamp(ts_ns / 1e9, tz=dt.UTC)
    return f"{d.year:04d}-{d.month:02d}"


def build_feature_frame(events: pl.DataFrame) -> pl.DataFrame:
    """Attach decision-time meta features + month key + label to the event rows."""
    names = sorted(events["symbol"].unique().to_list())
    name_code = {nm: i for i, nm in enumerate(names)}
    sessions = events["session"].unique().to_list()
    stratum = {s: calendar_stratum(s) for s in sessions}

    abs_eps_over_sigma5 = pl.when(pl.col("sigma_5m") > 0).then(
        pl.col("eps_trigger").abs() / pl.col("sigma_5m")
    ).otherwise(None)
    sigma_stat = pl.when((pl.col("kappa") > 0) & (pl.col("ou_sigma") > 0)).then(
        pl.col("ou_sigma") / (2.0 * pl.col("kappa")).sqrt()
    ).otherwise(None)
    eps_over_sigma_stat = pl.when(sigma_stat.is_not_null() & (sigma_stat > 0)).then(
        (pl.col("eps_trigger") - pl.col("theta")) / sigma_stat
    ).otherwise(None)

    return events.with_columns(
        (pl.col("et_minute") // 30).alias("tod_bucket"),
        abs_eps_over_sigma5.alias("abs_eps_over_sigma5"),
        eps_over_sigma_stat.alias("eps_over_sigma_stat"),
        pl.col("symbol").replace_strict(name_code, default=-1).alias("name_code"),
        pl.col("session").replace_strict(stratum, default="ORDINARY")
        .replace_strict(_STRATUM_CODE, default=0).alias("stratum_code"),
        pl.col("trigger_ts").map_elements(_month_key, return_dtype=pl.Utf8).alias("month_key"),
        (pl.col("net_bps") > 0).cast(pl.Int8).alias("meta_label"),
    )


@dataclass
class Fold:
    score_month: str
    train_months: list[str]
    n_train: int
    n_score: int
    max_train_ts: int
    min_score_ts: int
    importances: dict[str, float] = field(default_factory=dict)


@dataclass
class MetaResult:
    events: pl.DataFrame          # with meta_p, meta_kept, meta_scored
    folds: list[Fold]
    trained: bool
    boosters: list = field(default_factory=list)  # aligned with folds; LightGBM Boosters


def _lgb_params() -> dict:
    return {
        "objective": "binary", "num_leaves": 31, "learning_rate": 0.05,
        "min_data_in_leaf": 40, "feature_fraction": 0.9, "bagging_fraction": 0.8,
        "bagging_freq": 1, "seed": SEED, "deterministic": True, "num_threads": 1,
        "verbose": -1, "force_row_wise": True,
    }


def walk_forward(events: pl.DataFrame) -> MetaResult:
    """Monthly pooled walk-forward P(win). Adds meta_p / meta_kept / meta_scored.

    Training/scoring population = GATED maker-filled trades (passed_G1 & passed_G2)
    which carry a finite net_bps label; without gate columns it falls back to all
    maker-filled trades (unit fixtures). When fewer than 13 pooled months exist —
    or for any month before the first successful fold — nothing is scored for those
    rows: meta_p = NaN, meta_scored = False, meta_kept = True (no veto)."""
    import lightgbm as lgb  # local import: heavy, only needed here

    ev = build_feature_frame(events)
    n = ev.height
    meta_p = np.full(n, np.nan, dtype=np.float64)
    meta_kept = np.ones(n, dtype=bool)   # default: no veto (meaningful only where scored)
    meta_scored = np.zeros(n, dtype=bool)  # default: unscored

    # Training population: GATED trades (BUILD-SPEC §4). Gate columns absent in the
    # meta unit fixtures → fall back to all maker-filled (behaviour-preserving).
    gated = np.ones(n, dtype=bool)
    if "passed_G1" in ev.columns and "passed_G2" in ev.columns:
        gated = ev["passed_G1"].to_numpy() & ev["passed_G2"].to_numpy()
    labelable = ev["maker_filled"].to_numpy() & np.isfinite(ev["net_bps"].to_numpy()) & gated
    months = sorted(m for m in ev["month_key"].unique().to_list() if m is not None)
    folds: list[Fold] = []
    boosters: list = []
    trained = False

    if len(months) > MIN_TRAIN_MONTHS:
        month_arr = ev["month_key"].to_numpy()
        ts_arr = ev["trigger_ts"].to_numpy()
        x_all = ev.select(FEATURES).to_numpy().astype(np.float64)
        y_all = ev["meta_label"].to_numpy()
        cat_idx = [FEATURES.index(c) for c in FEATURE_CATEGORICAL]

        for k in range(MIN_TRAIN_MONTHS, len(months)):
            score_month = months[k]
            train_months = months[:k]
            train_mask = np.isin(month_arr, train_months) & labelable
            score_mask = (month_arr == score_month) & labelable
            if train_mask.sum() < 100 or score_mask.sum() == 0:
                continue
            dtrain = lgb.Dataset(
                x_all[train_mask], label=y_all[train_mask],
                categorical_feature=cat_idx, free_raw_data=False,
            )
            booster = lgb.train(_lgb_params(), dtrain, num_boost_round=200)
            preds = booster.predict(x_all[score_mask])
            idx = np.nonzero(score_mask)[0]
            meta_p[idx] = preds
            meta_kept[idx] = preds >= META_THRESHOLD
            meta_scored[idx] = True
            imp = dict(zip(FEATURES, booster.feature_importance(importance_type="gain").tolist(), strict=True))
            folds.append(Fold(
                score_month=score_month, train_months=train_months,
                n_train=int(train_mask.sum()), n_score=int(score_mask.sum()),
                max_train_ts=int(ts_arr[train_mask].max()),
                min_score_ts=int(ts_arr[score_mask].min()),
                importances=imp,
            ))
            boosters.append(booster)
            trained = True

    ev = ev.with_columns(
        pl.Series("meta_p", meta_p),
        pl.Series("meta_kept", meta_kept),
        pl.Series("meta_scored", meta_scored),
    )
    return MetaResult(events=ev, folds=folds, trained=trained, boosters=boosters)
