"""M8-v2 mechanism-informed meta-gate -- walk-forward evaluation harness
(M3_REGISTRATION.md "M8-v2 -- mechanism-informed meta-gate", REGISTERED
2026-07-20; M8-v2-FEATURE-DRAFT.md). Builds THREE streams on the IDENTICAL
OOS span with IDENTICAL folds (``models.moc_gbm.walk_forward_folds_calendar``,
M8-v1's exact fold builder, reused verbatim -- NOT reimplemented):

  (a) baseline1 -- a binary P(win) LightGBM retrained on M8-v1's
      ``moc_meta.FEATURE_COLS`` alone, IN THIS SAME code path (so the
      v1-vs-v2 comparison is same-frame / same-fold / same-seed, not a
      cross-run diff);
  (b) v2 -- M8-v1's FEATURE_COLS + the 6 frozen M8-v2 mechanism features
      (``models.m8v2_features.FEATURE_COLS``);
  (c) occam -- baseline2, the M12-promotion-object NO-MODEL filter:
      ``flow_aligned > 0 AND abs_f_over_adv >= its trailing in-sample
      top-tercile boundary`` -- see ``occam_boundary`` for the exact,
      FLAGGED construction (M12's report never pins a single forward
      threshold; this operationalizes the task-spec text against M12 Cell
      A's own tercile methodology).

Frozen hyperparameters / folds / candidate universe are M8-v1's, reused
verbatim (``models.moc_meta``: ``META_PARAMS``, ``CANDIDATE_BASIS_BPS``,
``build_meta_frame``; ``models.moc_gbm.walk_forward_folds_calendar``). This
module and ``apps/run_m8v2.py`` are NEW code paths; M8-v1's own files
(``models/moc_meta.py``, ``apps/run_meta_trial.py``) are untouched.

NO pass/fail verdicts anywhere in this module -- every function returns
numbers; ``apps/run_m8v2.py``'s CLI assembles them into metrics.json / an
event parquet / report.md for the orchestrator's ONE registered look.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from enginev51.backtest import stress
from enginev51.models import lgbm as lgbm_model
from enginev51.models import m8v2_features, moc_meta
from enginev51.models.moc_gbm import Fold, walk_forward_folds_calendar

# --------------------------------------------------------------------------- constants

V1_FEATURE_COLS: tuple[str, ...] = moc_meta.FEATURE_COLS
V2_FEATURE_COLS: tuple[str, ...] = moc_meta.FEATURE_COLS + m8v2_features.FEATURE_COLS
LABEL_COL = moc_meta.LABEL_COL  # "y_meta"
NET_COL = moc_meta.NET_COL  # "net_bps"

P_V1 = "p_v1"
P_V2 = "p_v2"
OCCAM_TAKEN_COL = "occam_gate"
OCCAM_BOUNDARY_COL = "occam_boundary"

# The registered comparison gate (mirrors M8-v1's / M9's q=0.55 convention).
COMPARE_GATE: float = 0.55
CONTEXT_GATES: tuple[float, ...] = (0.50, 0.55, 0.60)  # matches moc_meta.GATES

DEFAULT_M8V1_OOS = "research/experiments/M8-meta-v1/oos_predictions.parquet"


# --------------------------------------------------------------------------- Occam gate (baseline2)
#
# FLAGGED CONSTRUCTION (spec under-determined -- see module docstring + build
# report): M3_REGISTRATION.md / M12-mechanism/report.md never
# state a single numeric forward-filter threshold for F/ADV ("F/ADV becomes
# the forward name/event FILTER candidate" -- no operationalized cutoff). The
# task spec text supplies the operationalization directly: "gate =
# flow_aligned > 0 AND abs_f_over_adv >= its trailing in-sample tercile
# boundary". Two residual choices, resolved here against M12 Cell A's OWN
# methodology (scripts/m12_cell_a.py):
#   (a) WHICH tercile edge -- the T2/T3 (2/3 quantile, "top tercile") cut:
#       M12's registered headline lift concentrated in T3 (+2.91 bps vs T2
#       +1.93 vs T1 -0.14 vs the zero-complex control -0.38), so "the tercile
#       boundary" operationalizes as top-tercile MEMBERSHIP, not the T1/T2
#       (1/3 quantile) edge.
#   (b) WHICH population the quantile is fit on -- rows with a genuine
#       complex (abs_f_over_adv > 0) only, exactly mirroring M12's own
#       ``has = ev.filter(flow_coef > 0)`` restriction before computing
#       T1/T2/T3 (a population dominated by exact zero-complex rows would
#       collapse the boundary toward 0 and admit the wrong events).
# "Trailing in-sample" = fit on the fold's TRAINING rows only (PIT-safe,
# reusing the SAME walk-forward folds as v1/v2), applied to that fold's test
# rows -- never fit on OOS data.


def occam_boundary(train_df: pl.DataFrame) -> float:
    """The trailing in-sample top-tercile (2/3 quantile) boundary of
    ``abs_f_over_adv``, fit on ``train_df`` restricted to rows with a genuine
    LETF complex (``abs_f_over_adv > 0``) -- see the FLAGGED CONSTRUCTION note
    above. Returns ``+inf`` (gate never fires) when the training fold has no
    positive-complex row."""
    pos = train_df.filter(pl.col("abs_f_over_adv") > 0.0)["abs_f_over_adv"].drop_nulls()
    if pos.len() == 0:
        return float("inf")
    return float(pos.quantile(2.0 / 3.0, interpolation="linear"))


def occam_gate(df: pl.DataFrame, boundary: float) -> np.ndarray:
    """The Occam (no-model) TAKE rule: ``flow_aligned > 0 AND abs_f_over_adv
    >= boundary``. Deterministic, pure; ``boundary`` comes from
    ``occam_boundary`` on the SAME fold's training rows (never fit on
    ``df`` itself when ``df`` is a test/OOS fold)."""
    aligned = df["flow_aligned"].fill_null(0.0).to_numpy() > 0.0
    intense = df["abs_f_over_adv"].fill_null(0.0).to_numpy() >= boundary
    return aligned & intense


# --------------------------------------------------------------------------- pre-model diagnostic


def redundancy_diagnostic(features_df: pl.DataFrame, train_end_iso: str) -> dict:
    """Pre-model redundancy diagnostic (registered, KILL-checked by the
    orchestrator, NOT by this function): Pearson corr(``abs_f_over_adv``,
    each M8-v1 numeric feature already in the frame) on the PROTOCOL TRAIN
    split (``session <= train_end_iso``, i.e. ``protocol.TRAIN_END`` --
    the codebase's one canonical "training span", not any single fold's
    training set). > 0.8 with the imbalance features (``norm_imb`` primarily;
    all 10 v1 numeric features reported for completeness) => REDUNDANT per
    the registered kill rule. This function ONLY computes and returns the
    numbers -- it does not grade them."""
    train = features_df.filter(pl.col("session") <= train_end_iso)
    out: dict[str, float | None] = {}
    x = train["abs_f_over_adv"].to_numpy()
    x_valid = np.isfinite(x)
    for feat in moc_meta.NUMERIC_FEATURES:
        y = train[feat].to_numpy().astype(float)
        mask = x_valid & np.isfinite(y)
        if mask.sum() < 2 or np.std(x[mask]) == 0.0 or np.std(y[mask]) == 0.0:
            out[feat] = None
            continue
        out[feat] = float(np.corrcoef(x[mask], y[mask])[0, 1])
    return {
        "train_span": f"session <= {train_end_iso}",
        "n_train_rows": train.height,
        "corr_abs_f_over_adv_vs_v1_feature": out,
    }


# --------------------------------------------------------------------------- three-stream walk-forward


def run_three_stream_walk_forward(
    frame: pl.DataFrame,
    *,
    initial_train_years: int = 2,
    test_block_months: int = 6,
    embargo_sessions: int = 1,
) -> tuple[pl.DataFrame, pl.DataFrame, list[Fold]]:
    """ONE expanding walk-forward producing all THREE streams' OOS output on
    IDENTICAL rows. Reuses ``moc_gbm.walk_forward_folds_calendar`` EXACTLY
    (>=2y initial train, 6-month blocks, 1-session embargo -- M8-v1's own
    folds). Per fold:
      * baseline1-GBDT: binary classifier on ``V1_FEATURE_COLS`` -> ``p_v1``;
      * v2-GBDT: binary classifier on ``V2_FEATURE_COLS`` -> ``p_v2``;
      * Occam: ``occam_boundary`` fit on the SAME train rows -> ``occam_gate``
        (boolean) + ``occam_boundary`` (float) on the test rows.
    All three share the fold's exact PIT train set, so every OOS stream is
    paired row-for-row. Returns ``(oos_df, v2_importances_df, folds)``."""
    sessions = sorted(frame["session"].unique().to_list())
    folds = walk_forward_folds_calendar(
        sessions,
        initial_train_years=initial_train_years,
        test_block_months=test_block_months,
        embargo_sessions=embargo_sessions,
    )
    oos_parts: list[pl.DataFrame] = []
    imp_accum: dict[str, list[float]] = {c: [] for c in V2_FEATURE_COLS}
    for fold in folds:
        tr = frame.filter(pl.col("session").is_in(list(fold.train_sessions)))
        te = frame.filter(pl.col("session").is_in(list(fold.test_sessions)))
        if tr.height == 0 or te.height == 0:
            continue
        # PIT guard (defence in depth): no training row at/after the test-block start.
        assert (tr["session"].max() or "") < fold.test_start, (
            f"leakage: train row >= test_start {fold.test_start}"
        )

        b1 = lgbm_model.train_one(tr, V1_FEATURE_COLS, LABEL_COL, params=moc_meta.META_PARAMS)
        p1 = lgbm_model.predict(b1, te, V1_FEATURE_COLS)

        b2 = lgbm_model.train_one(tr, V2_FEATURE_COLS, LABEL_COL, params=moc_meta.META_PARAMS)
        p2 = lgbm_model.predict(b2, te, V2_FEATURE_COLS)

        boundary = occam_boundary(tr)
        occam_taken = occam_gate(te, boundary)

        oos_parts.append(
            te.with_columns(
                pl.Series(P_V1, p1),
                pl.Series(P_V2, p2),
                pl.Series(OCCAM_TAKEN_COL, occam_taken),
                pl.lit(boundary).alias(OCCAM_BOUNDARY_COL),
                pl.lit(fold.test_start).alias("fold"),
            )
        )
        gains = b2.feature_importance(importance_type="gain")
        names = b2.feature_name()
        for name, g in zip(names, gains, strict=True):
            if name in imp_accum:
                imp_accum[name].append(float(g))

    oos_df = (
        pl.concat(oos_parts)
        if oos_parts
        else frame.head(0).with_columns(
            pl.lit(None, dtype=pl.Float64).alias(P_V1),
            pl.lit(None, dtype=pl.Float64).alias(P_V2),
            pl.lit(None, dtype=pl.Boolean).alias(OCCAM_TAKEN_COL),
            pl.lit(None, dtype=pl.Float64).alias(OCCAM_BOUNDARY_COL),
            pl.lit(None, dtype=pl.Utf8).alias("fold"),
        )
    )
    imp_rows = [
        {
            "feature": c,
            "mean_gain": float(np.mean(imp_accum[c])) if imp_accum[c] else 0.0,
            "n_folds": len(imp_accum[c]),
            "is_v2_new": c in m8v2_features.FEATURE_COLS,
        }
        for c in V2_FEATURE_COLS
    ]
    importances_df = pl.DataFrame(
        imp_rows,
        schema={
            "feature": pl.Utf8, "mean_gain": pl.Float64, "n_folds": pl.Int64,
            "is_v2_new": pl.Boolean,
        },
    ).sort("mean_gain", descending=True)
    return oos_df, importances_df, folds


# --------------------------------------------------------------------------- metrics (numbers only)


def _ci(df: pl.DataFrame) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n_events, n_sessions) day-clustered over net_bps (house
    ``stress.clustered_mean_ci``)."""
    if df.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    m, lo, hi = stress.clustered_mean_ci(df[NET_COL].to_numpy(), df["session"].to_numpy())
    return m, lo, hi, df.height, df["session"].n_unique()


def _hit_rate(df: pl.DataFrame) -> float:
    if df.height == 0:
        return float("nan")
    return float((df[NET_COL] > 0.0).cast(pl.Float64).mean())


def _sharpe_per_trade(df: pl.DataFrame) -> tuple[float, float]:
    """(std, Sharpe = mean/std) of PER-TRADE net_bps (sample std, ddof=1) --
    matches M8-v1's/M9's own reported Sharpe convention exactly (apples-to-
    apples with baseline1's numbers)."""
    if df.height < 2:
        return float("nan"), float("nan")
    net = df[NET_COL].to_numpy()
    sd = float(np.std(net, ddof=1))
    mean = float(np.mean(net))
    return sd, (mean / sd if sd > 0 else float("nan"))


def _daily_sharpe(df: pl.DataFrame) -> tuple[float, float]:
    """(n_days, Sharpe) of the PER-SESSION MEAN net_bps -- an explicitly
    requested ADDITIONAL stat, distinct from the per-trade Sharpe above.
    Definition (stated exactly, since the draft does not pin one): group
    taken events by session, take each session's mean net_bps (the day's
    average edge on the taken stream), then Sharpe = mean/std (ddof=1) across
    those per-session means. Not annualized."""
    if df.height == 0:
        return 0, float("nan")
    per_day = df.group_by("session").agg(pl.col(NET_COL).mean().alias("day_mean"))
    if per_day.height < 2:
        return per_day.height, float("nan")
    vals = per_day["day_mean"].to_numpy()
    sd = float(np.std(vals, ddof=1))
    mean = float(np.mean(vals))
    return per_day.height, (mean / sd if sd > 0 else float("nan"))


def stream_block(df: pl.DataFrame) -> dict:
    """Every number the registered bars (i)-(v) need for ONE stream: n,
    hit-rate, mean net_bps, day-clustered CI, per-trade AND daily Sharpe,
    per-symbol and per-year breakdowns. NO pass/fail flags."""
    m, lo, hi, n, n_sess = _ci(df)
    sd, sharpe_pt = _sharpe_per_trade(df)
    n_days, sharpe_daily = _daily_sharpe(df)
    symbols = sorted(df["symbol"].unique().to_list()) if n else []
    years = sorted({s[:4] for s in df["session"].to_list()}) if n else []
    per_symbol = {}
    for sym in symbols:
        sub = df.filter(pl.col("symbol") == sym)
        per_symbol[sym] = {
            "n": sub.height, "net_bps_mean": round(float(sub[NET_COL].mean()), 3),
            "hit_rate": round(_hit_rate(sub), 4),
        }
    per_year = {}
    for yr in years:
        sub = df.filter(pl.col("session").str.starts_with(yr))
        per_year[yr] = {
            "n": sub.height, "net_bps_mean": round(float(sub[NET_COL].mean()), 3),
            "hit_rate": round(_hit_rate(sub), 4),
        }
    return {
        "n": n,
        "n_sessions": n_sess,
        "hit_rate": round(_hit_rate(df), 4) if n else None,
        "net_bps_mean": round(m, 3) if n else None,
        "ci_lo": round(lo, 3) if n else None,
        "ci_hi": round(hi, 3) if n else None,
        "net_bps_std": round(sd, 3) if n >= 2 else None,
        "sharpe_per_trade": round(sharpe_pt, 4) if n >= 2 else None,
        "n_days": n_days,
        "sharpe_daily": round(sharpe_daily, 4) if n_days >= 2 else None,
        "n_symbols": len(symbols),
        "symbols": symbols,
        "n_years": len(years),
        "years": years,
        "per_symbol": per_symbol,
        "per_year": per_year,
    }


def build_streams(oos: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Ordered streams on the SAME OOS span: the ungated baseline + v1/v2
    gated at each context gate + the Occam (no-model) stream."""
    streams: dict[str, pl.DataFrame] = {"ungated_baseline": oos}
    if oos.height:
        for q in CONTEXT_GATES:
            streams[f"baseline1_v1_gated_q{q:.2f}"] = oos.filter(pl.col(P_V1) >= q)
            streams[f"v2_gated_q{q:.2f}"] = oos.filter(pl.col(P_V2) >= q)
        streams["occam_gated"] = oos.filter(pl.col(OCCAM_TAKEN_COL))
    else:
        for q in CONTEXT_GATES:
            streams[f"baseline1_v1_gated_q{q:.2f}"] = oos
            streams[f"v2_gated_q{q:.2f}"] = oos
        streams["occam_gated"] = oos
    return streams


# --------------------------------------------------------------------------- cross-checks (report-only)


def cross_check_v1_reproduction(
    oos: pl.DataFrame, reference_path: str | Path = DEFAULT_M8V1_OOS
) -> dict:
    """Sanity cross-check ONLY: Pearson corr(``p_v1`` from THIS code path,
    ``p_win`` from the ALREADY-COMPUTED ``research/experiments/M8-meta-v1/
    oos_predictions.parquet``) on overlapping (symbol, session) -- confirms
    this module's re-derivation of M8-v1's frame/folds/hyperparameters
    reproduces the original run closely. Report corr/n only; not a gate."""
    p = Path(reference_path)
    if not p.exists() or oos.height == 0:
        return {"available": False, "n_overlap": 0, "corr": None}
    ref = pl.read_parquet(p).select(["symbol", "session", "p_win"])
    mine = oos.select(["symbol", "session", P_V1]).drop_nulls()
    joined = mine.join(ref, on=["symbol", "session"], how="inner").drop_nulls()
    if joined.height < 2:
        return {"available": True, "n_overlap": joined.height, "corr": None}
    corr = float(np.corrcoef(joined[P_V1].to_numpy(), joined["p_win"].to_numpy())[0, 1])
    return {"available": True, "n_overlap": joined.height, "corr": corr}


# --------------------------------------------------------------------------- top-level evaluate


def evaluate(
    events: pl.DataFrame,
    *,
    bbo_dir: str | Path | None = None,
    registry_path: str | Path = m8v2_features.DEFAULT_REGISTRY_PATH,
    anchors_path: str | Path = m8v2_features.DEFAULT_ANCHORS_PATH,
    cellA_path: str | Path = "research/experiments/M12-mechanism/cellA_events.parquet",
    v1_oos_path: str | Path = DEFAULT_M8V1_OOS,
    train_end_iso: str = "2026-02-28",
    initial_train_years: int = 2,
    test_block_months: int = 6,
    embargo_sessions: int = 1,
) -> dict:
    """Build the meta frame (M8-v1's ``build_meta_frame``, unmodified), the 6
    v2 features, run the three-stream walk-forward, assemble streams +
    cross-checks. Pure over ``events`` given the data lake (LightGBM seed
    fixed in ``lgbm.DEFAULT_PARAMS``). Returns a dict bundling every
    intermediate the CLI needs; computes NOTHING resembling a verdict."""
    n_cand_raw = events.filter(pl.col("basis_bps").abs() >= moc_meta.CANDIDATE_BASIS_BPS).height
    meta = moc_meta.build_meta_frame(events)
    meta_counts = {
        "events_rows": events.height,
        "candidates_basis_ge_10": n_cand_raw,
        "candidates_labeled": meta.height,
        "candidates_dropped_null_net": n_cand_raw - meta.height,
    }

    features_df, feature_funnel = m8v2_features.build_features_frame(
        meta, bbo_dir=bbo_dir, registry_path=registry_path, anchors_path=anchors_path
    )

    # Pre-model redundancy diagnostic -- EMITTED FIRST (computed before any
    # model training; placed first in both the returned dict and metrics.json).
    redundancy = redundancy_diagnostic(features_df, train_end_iso)

    oos, v2_importances, folds = run_three_stream_walk_forward(
        features_df,
        initial_train_years=initial_train_years,
        test_block_months=test_block_months,
        embargo_sessions=embargo_sessions,
    )
    streams = build_streams(oos)

    cross_v1_repro = cross_check_v1_reproduction(oos, v1_oos_path)
    cross_f_adv_m12 = m8v2_features.f_adv_cross_check(features_df, cellA_path)

    return {
        "meta_counts": meta_counts,
        "features_df": features_df,
        "feature_funnel": feature_funnel,
        "redundancy_diagnostic": redundancy,
        "oos": oos,
        "v2_importances": v2_importances,
        "folds": folds,
        "streams": streams,
        "cross_check_v1_reproduction": cross_v1_repro,
        "cross_check_f_adv_vs_m12": cross_f_adv_m12,
    }
