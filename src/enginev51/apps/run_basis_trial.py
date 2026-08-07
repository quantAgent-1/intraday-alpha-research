"""M6-FINAL near-price basis trial runner — the closing family's LAST experiment.

Drives the registered ``moc_imbalance_v1`` M6-FINAL cell (M3_REGISTRATION.md,
"M6-FINAL cell — near-price basis at 15:55:10"). The mechanism's cleanest
expression: the closing auction's OWN indicative clearing price (NOII near price,
populated from ~15:55) against the prevailing market mid. ``moc_imbalance_v1``
CLOSES after this run, pass or fail.

Per (symbol, session), all instants ET:

    1. near = last NOII message at-or-before 15:55:10 with near_price > 0 (PIT;
       skip + count if none).
    2. mid  = prevailing bbo-1s mid at 15:55:10 (skip + count if none).
       basis_bps = 1e4 * (near - mid) / mid.
    3. Classical cells: ACTIVE iff |basis_bps| >= {5, 10}; direction = sign(near -
       mid) (buy iff near > mid); entry = taker MARKET at 15:55:10 + latency
       (tape_from_bbo + fills.market_fill + slip); exit AT the official cross
       (cross_price_for; skip + count if absent); net via decompose.plan_pnl
       (SEC/TAF on the sell leg) inside replay_moc_event.
    4. GBM cell: registered PIT features at 15:55:10 (the M6-GBM set, now
       populated: imbalance growth vs 15:53/15:51, near-ref bps, near-far bps,
       near drift, msg count, norm_imb, side, paired_ratio, log ADV20$, vol20,
       symbol one-hot) + basis_bps. LightGBM regression on the ALL-events net
       (every session-symbol with a valid basis + cross, regardless of the
       classical threshold), same walk-forward as ``models/moc_gbm`` (6-month
       blocks, >=2y initial, 1-session embargo), fixed gate pred > 0.

DATA-REALITY (VERIFIED on the owned tape 2026-07-17, documented per task):
  * The Nasdaq closing-cross NOII near/far indicative clearing prices are 0 until
    ~15:55:00 ET; ``near_price`` first turns > 0 at exactly 15:55:00 across the
    full 2020->2026 span (checked NVDA/TSLA/AMD/MU/GOOGL, early + late era). At
    15:55:10 there are ~40 disseminated messages, near/far/ref all populated, so
    the basis is well defined for every covered session.
  * Consequently the growth features vs 15:53/15:51 are meaningful (the imbalance
    SHARES evolve over the 15:50->15:55 window; at 15:53/15:51 ``near`` is still 0
    so ``norm_imb`` there uses the near->ref price fallback of ``signal_at`` — the
    imbalance magnitude still carries). ``near_ref_bps`` / ``near_far_bps`` at
    15:55:10 are meaningful (near, far, ref all > 0). The ``near_drift_51_55``
    feature DEGENERATES to 0 (near is 0 at 15:51, so the drift base is missing) —
    computed exactly per formula; visible in the importance table.

This app writes NO ledger row (the orchestrator owns verdicts) and NO pass/fail
interpretation. Hard PIT/holdout guard: refuses any ``--end`` on/after
``protocol.HOLDOUT_START`` and hard-filters every session strictly before it.

    uv run python -m enginev51.apps.run_basis_trial --trial-id M6-FINAL-basis-v1 \
        --symbols NVDA,TSLA,AMD,MU,GOOGL --start 2020-01-02 --end 2026-05-31 --seed 7
"""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import click
import numpy as np
import polars as pl
import structlog

from enginev51.backtest import stress
from enginev51.backtest.auction_replay import (
    adv20_dollars,
    cross_price_for,
    load_raw_trades,
    official_daily_closes,
    replay_moc_event,
    tape_from_bbo,
)
from enginev51.backtest.fills import prevailing_idx, prevailing_mid
from enginev51.config import Settings, get_settings
from enginev51.data import calendar, store
from enginev51.data.bbo1s import load_bbo_session
from enginev51.data.noii import ET, _side_sign, et_ns, load_noii_session, signal_at
from enginev51.models import lgbm as lgbm_model
from enginev51.models.moc_gbm import (
    ONEHOT_FEATURES,
    symbol_onehot,
    trailing_vol20,
    walk_forward_folds_calendar,
)
from enginev51.models.moc_gbm import gate as gbm_gate
from enginev51.protocol import (
    HOLDOUT_START,
    experiments_dir,
    refuse_end_on_or_after_holdout,
    split_of,
)

log = structlog.get_logger(__name__)

NS_PER_S = 1_000_000_000
SYMBOLS_DEFAULT = "NVDA,TSLA,AMD,MU,GOOGL"

# Registered PIT instants (ET). Signal at 15:55:10; the growth references are the
# 15:50:10 registered set shifted onto the 15:55:10 signal (15:53 = -2 min,
# 15:51 = -4 min), matching the M6-GBM registered feature geometry.
SIGNAL_HMS = (15, 55, 10)
T1553_HMS = (15, 53, 0)
T1551_HMS = (15, 51, 0)

# Registered classical cells: |basis_bps| >= 5 and >= 10.
CLASSICAL_THRESHOLDS_BPS: tuple[float, ...] = (5.0, 10.0)

# GBM feature order — the registered M6-GBM numeric set recomputed at 15:55:10,
# PLUS basis_bps, PLUS the shared symbol one-hot. basis_bps is placed last among
# the numeric features (the M6-FINAL addition to the registered set).
NUMERIC_FEATURES: tuple[str, ...] = (
    "norm_imb",
    "side",
    "paired_ratio",
    "imb_growth_53",
    "imb_growth_51",
    "near_ref_bps",
    "near_far_bps",
    "near_drift_51_55",
    "msg_count",
    "log_adv20",
    "vol20",
    "basis_bps",
)
FEATURE_COLS: tuple[str, ...] = NUMERIC_FEATURES + ONEHOT_FEATURES
LABEL_COL = "net_bps"

# Per-event results / context schema (one row per ALL-events event).
EVENT_SCHEMA: dict[str, pl.DataType] = {
    "session": pl.Utf8,
    "symbol": pl.Utf8,
    "side": pl.Int64,
    "near_price": pl.Float64,
    "entry_mid": pl.Float64,
    "basis_bps": pl.Float64,
    "adv20_dollars": pl.Float64,
    "entry_ts": pl.Int64,
    "entry_px": pl.Float64,
    "entry_bid": pl.Float64,
    "entry_ask": pl.Float64,
    "exit_ts": pl.Int64,
    "exit_px": pl.Float64,
    "exit_reason": pl.Utf8,
    "cross_px": pl.Float64,
    "cross_size": pl.Float64,
    "bar_close": pl.Float64,
    "net_bps": pl.Float64,
    "hold_s": pl.Float64,
    # GBM features
    "norm_imb": pl.Float64,
    "paired_ratio": pl.Float64,
    "imb_growth_53": pl.Float64,
    "imb_growth_51": pl.Float64,
    "near_ref_bps": pl.Float64,
    "near_far_bps": pl.Float64,
    "near_drift_51_55": pl.Float64,
    "msg_count": pl.Float64,
    "log_adv20": pl.Float64,
    "vol20": pl.Float64,
    "oh_NVDA": pl.Float64,
    "oh_TSLA": pl.Float64,
    "oh_AMD": pl.Float64,
    "oh_MU": pl.Float64,
    "oh_GOOGL": pl.Float64,
}


# --------------------------------------------------------------------------- guard


def assert_before_holdout(end: date) -> None:
    """Refuse any run reaching the sealed holdout boundary (PROTOCOL v6 §1).

    Raises SealViolation (never a bare assert: ``python -O`` strips those)."""
    refuse_end_on_or_after_holdout(end)


# --------------------------------------------------------------------------- signal


def near_at(noii_frame: pl.DataFrame | None, ts_signal: int) -> float | None:
    """The registered basis ``near`` price at ``ts_signal`` (PIT).

    RULE (M6-FINAL): the LAST NOII message at-or-before ``ts_signal`` whose
    ``near_price`` > 0 governs; ``None`` when there is no such message (the near
    indicative clearing price has not populated yet). A message strictly AFTER
    ``ts_signal`` can never govern (PIT); a ``near_price`` <= 0 message is skipped.
    """
    if noii_frame is None or noii_frame.height == 0:
        return None
    prior = noii_frame.filter((pl.col("ts") <= ts_signal) & (pl.col("near_price") > 0.0))
    if prior.height == 0:
        return None
    return float(prior.sort("ts").row(-1, named=True)["near_price"])


def basis_bps_of(near: float, mid: float) -> float:
    """``1e4 * (near - mid) / mid`` — the near-price basis in basis points."""
    return 1e4 * (near - mid) / mid


def direction_of(near: float, mid: float) -> int:
    """Trade direction: WITH the basis. +1 buy iff near > mid, -1 sell iff near <
    mid, 0 when they coincide (no tradable basis)."""
    if near > mid:
        return 1
    if near < mid:
        return -1
    return 0


# --------------------------------------------------------------------------- features


def _governing_row(frame: pl.DataFrame, ts: int) -> dict | None:
    """The last NOII message at-or-before ``ts`` (PIT), or ``None``."""
    prior = frame.filter(pl.col("ts") <= ts)
    if prior.height == 0:
        return None
    return prior.sort("ts").row(-1, named=True)


def _norm_imb_at(frame: pl.DataFrame, ts: int, adv20: float) -> float:
    """``norm_imb`` at ``ts`` via the registered ``signal_at`` (near->ref price
    fallback); 0.0 when no message has been disseminated at-or-before ``ts``."""
    sig = signal_at(frame, ts, adv20)
    return float(sig["norm_imb"]) if sig is not None else 0.0


def basis_pit_features(
    frame: pl.DataFrame,
    session_iso: str,
    adv20: float,
    near: float,
    mid: float,
) -> dict:
    """Registered M6-GBM PIT feature vector at 15:55:10 ET + ``basis_bps`` (pure).

    ``near`` is the basis near price (last near>0 message, from ``near_at``);
    ``mid`` is the prevailing bbo-1s mid. All NOII-derived features use the last
    message at-or-before 15:55:10 as the governing row (which carries near>0 on
    real data); the growth features look back to 15:53 / 15:51.
    """
    ts_sig = et_ns(session_iso, *SIGNAL_HMS)
    ts_53 = et_ns(session_iso, *T1553_HMS)
    ts_51 = et_ns(session_iso, *T1551_HMS)

    gov = _governing_row(frame, ts_sig)
    # gov is guaranteed non-None here (near_at already found a governing message).
    side = _side_sign(gov["side"]) if gov is not None else 0
    imb_shares = float(gov["imbalance_shares"] or 0.0) if gov is not None else 0.0
    paired = float(gov["paired_shares"] or 0.0) if gov is not None else 0.0
    near_g = float(gov["near_price"] or 0.0) if gov is not None else 0.0
    far_g = float(gov["far_price"] or 0.0) if gov is not None else 0.0
    ref_g = float(gov["ref_price"] or 0.0) if gov is not None else 0.0

    norm_imb = float(side) * imb_shares * near / adv20
    denom = paired + abs(imb_shares)
    paired_ratio = (paired / denom) if denom > 0.0 else 0.0

    near_ref_bps = ((near_g - ref_g) / ref_g * 1e4) if (near_g > 0.0 and ref_g > 0.0) else 0.0
    near_far_bps = ((near_g - far_g) / far_g * 1e4) if (near_g > 0.0 and far_g > 0.0) else 0.0

    gov_51 = _governing_row(frame, ts_51)
    near_51 = float(gov_51["near_price"] or 0.0) if gov_51 is not None else 0.0
    near_drift = (near_g - near_51) / near_51 * 1e4 if (near_g > 0.0 and near_51 > 0.0) else 0.0

    imb_growth_53 = norm_imb - _norm_imb_at(frame, ts_53, adv20)
    imb_growth_51 = norm_imb - _norm_imb_at(frame, ts_51, adv20)
    msg_count = float(frame.filter(pl.col("ts") <= ts_sig).height)

    return {
        "norm_imb": norm_imb,
        "side": float(side),
        "paired_ratio": paired_ratio,
        "imb_growth_53": imb_growth_53,
        "imb_growth_51": imb_growth_51,
        "near_ref_bps": near_ref_bps,
        "near_far_bps": near_far_bps,
        "near_drift_51_55": near_drift,
        "msg_count": msg_count,
        "basis_bps": basis_bps_of(near, mid),
    }


# --------------------------------------------------------------------------- helpers


def _session_closes(settings: Settings, symbol: str) -> dict[str, float]:
    """Per-session OFFICIAL daily close (bars1d), falling back to the last RTH
    1m-bar close only where the daily file lacks the session.

    ``bar_close`` feeds ``cross_vs_close_bps``, the "cross print is sane against
    the official close" validation — so it must BE the official close. The last
    1-minute bar (the old source, code review 2026-07-17 F6) is the 15:59 bar,
    not the closing cross, and validated the cross against the wrong reference.
    """
    feed = settings.data_feed_type
    out: dict[str, float] = {}
    bars = store.load_bars(settings.read_roots, feed, symbol)
    if bars.height > 0:
        per = (
            bars.with_columns(
                pl.from_epoch(pl.col("ts"), time_unit="ns")
                .dt.convert_time_zone(str(ET))
                .dt.date()
                .cast(pl.Utf8)
                .alias("session")
            )
            .sort("ts")
            .group_by("session")
            .agg(pl.col("close").last().alias("close"))
        )
        out = dict(zip(per["session"].to_list(), per["close"].to_list(), strict=True))
    out.update(official_daily_closes(symbol))  # official close wins where present
    return out


def _prevailing_nbbo(tape, ts: int) -> tuple[float | None, float | None]:
    """Prevailing (bid, ask) at ``ts`` from a SessionTape; (None, None) if none."""
    i = prevailing_idx(tape.q_ts, ts)
    if i < 0:
        return None, None
    return float(tape.q_bid[i]), float(tape.q_ask[i])


def _load_daily_closes(symbol: str) -> list[tuple[str, float]]:
    """Daily (session_iso, close) pairs from ``data/raw/sip/bars1d`` (UTC-date key,
    the convention ``auction_replay._daily_closes`` uses)."""
    from datetime import UTC, datetime

    p = Path("data/raw/sip/bars1d") / f"{symbol.upper()}.parquet"
    if not p.exists():
        return []
    df = pl.read_parquet(p)
    out: list[tuple[str, float]] = []
    for r in df.iter_rows(named=True):
        d = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
        out.append((d, float(r["close"])))
    return out


# --------------------------------------------------------------------------- run


def run_basis_trial(
    settings: Settings,
    *,
    symbols: list[str],
    start: date,
    end: date,
    seed: int,
    noii_dir: str | Path | None = None,
    bbo_dir: str | Path | None = None,
    lat_lo_s: float = 5.0,
    lat_hi_s: float = 25.0,
    holdout_only: bool = False,
) -> tuple[pl.DataFrame, dict]:
    """Execute the M6-FINAL event scan over [start, end] sessions.

    Returns ``(events_df, stats)``. ``events_df`` is the ALL-events universe: one
    row per (symbol, session) with a valid basis (near>0 msg + bbo mid + a
    tradable direction) AND a cross AND a non-void auction replay. The classical
    cells are ``|basis_bps| >= threshold`` subsets; the GBM cell trains on every
    row. The funnel counters record every skipped session.
    """
    # HOLDOUT CEREMONY (PROTOCOL v6 §1): the sealed window is reachable ONLY via
    # holdout_only, which the CLI gates on the ENGINEV51_UNSEAL_TOKEN env token —
    # the same mechanism protocol.apply_seal enforces. The normal path stays
    # strictly before the seal.
    if not holdout_only:
        assert_before_holdout(end)
    symbols = [s.strip().upper() for s in symbols]

    counts = {
        "no_noii_partition": 0,
        "no_noii_msgs": 0,
        "no_near": 0,        # no near>0 NOII message at-or-before 15:55:10
        "no_bbo": 0,         # no bbo-1s session for the mid / entry
        "no_mid": 0,         # no prevailing bbo mid at 15:55:10
        "zero_basis": 0,     # near == mid exactly (no tradable direction)
        "no_adv": 0,         # no ADV20$ (features would be undefined)
        "no_cross": 0,       # no official closing-cross price
        "void": 0,           # auction replay void (no quote before entry action)
        "events": 0,         # ALL-events rows produced
    }
    per_symbol_no_cross: dict[str, int] = dict.fromkeys(symbols, 0)

    closes_cache: dict[str, dict[str, float]] = {}
    rows: list[dict] = []

    if holdout_only:
        sessions = [d for d in calendar.trading_days(start, end) if d >= HOLDOUT_START]
    else:
        sessions = [d for d in calendar.trading_days(start, end) if d < HOLDOUT_START]
    for sd in sessions:
        session_iso = sd.isoformat()
        signal_ts = et_ns(session_iso, *SIGNAL_HMS)
        for sym in symbols:
            noii = load_noii_session(sym, session_iso, out_dir=noii_dir)
            if noii is None:
                counts["no_noii_partition"] += 1
                continue
            if noii.height == 0:
                counts["no_noii_msgs"] += 1
                continue

            near = near_at(noii, signal_ts)
            if near is None:
                counts["no_near"] += 1
                continue

            bbo = load_bbo_session(sym, session_iso, out_dir=bbo_dir)
            if bbo is None or bbo.height == 0:
                counts["no_bbo"] += 1
                continue
            tape = tape_from_bbo(sym, bbo)

            mid = prevailing_mid(tape.q_ts, tape.q_bid, tape.q_ask, signal_ts)
            if not np.isfinite(mid) or mid <= 0.0:
                counts["no_mid"] += 1
                continue

            side = direction_of(near, mid)
            if side == 0:
                counts["zero_basis"] += 1
                continue

            adv = adv20_dollars(settings, sym, session_iso)
            if adv is None or adv <= 0.0:
                counts["no_adv"] += 1
                continue

            cross = cross_price_for(sym, session_iso, load_raw_trades(settings, sym, session_iso))
            if cross is None:
                counts["no_cross"] += 1
                per_symbol_no_cross[sym] += 1
                continue

            plan_id = f"{sym}-{session_iso}-basis"
            res = replay_moc_event(
                tape, signal_ts, side, cross, seed, plan_id,
                symbol=sym, persistence_exit_ts=None,
                lat_lo_s=lat_lo_s, lat_hi_s=lat_hi_s,
                slip_bps=0.5, sec_taf_sell_bps=0.3,
            )
            if res.status != "ok":
                counts["void"] += 1
                continue

            feats = basis_pit_features(noii, session_iso, float(adv), near, mid)

            if sym not in closes_cache:
                closes_cache[sym] = _session_closes(settings, sym)
            bar_close = closes_cache[sym].get(session_iso)
            bid, ask = _prevailing_nbbo(tape, signal_ts)
            oh = symbol_onehot(sym)
            vol20 = trailing_vol20(_daily_closes_cache(sym), session_iso)

            rows.append(
                {
                    "session": session_iso,
                    "symbol": sym,
                    "side": side,
                    "near_price": float(near),
                    "entry_mid": float(mid),
                    "basis_bps": feats["basis_bps"],
                    "adv20_dollars": float(adv),
                    "entry_ts": res.entry_ts,
                    "entry_px": res.entry_px,
                    "entry_bid": bid,
                    "entry_ask": ask,
                    "exit_ts": res.exit_ts,
                    "exit_px": res.exit_px,
                    "exit_reason": res.exit_reason,
                    "cross_px": float(cross[1]),
                    "cross_size": float(cross[2]),
                    "bar_close": bar_close,
                    "net_bps": res.net_bps,
                    "hold_s": res.hold_s,
                    "norm_imb": feats["norm_imb"],
                    "paired_ratio": feats["paired_ratio"],
                    "imb_growth_53": feats["imb_growth_53"],
                    "imb_growth_51": feats["imb_growth_51"],
                    "near_ref_bps": feats["near_ref_bps"],
                    "near_far_bps": feats["near_far_bps"],
                    "near_drift_51_55": feats["near_drift_51_55"],
                    "msg_count": feats["msg_count"],
                    "log_adv20": float(np.log(adv)),
                    "vol20": vol20,
                    **oh,
                }
            )
            counts["events"] += 1

    df = (
        pl.DataFrame(rows, schema=EVENT_SCHEMA, orient="row")
        if rows
        else pl.DataFrame(schema=EVENT_SCHEMA)
    )
    stats = {
        "symbols": symbols,
        "seed": seed,
        "classical_thresholds_bps": list(CLASSICAL_THRESHOLDS_BPS),
        "sessions_in_range": len(sessions),
        "counts": counts,
        "per_symbol_no_cross": per_symbol_no_cross,
    }
    return df, stats


# per-symbol daily-close cache (module-level: vol20 needs the full close history).
_DAILY_CLOSES_CACHE: dict[str, list[tuple[str, float]]] = {}


def _daily_closes_cache(symbol: str) -> list[tuple[str, float]]:
    if symbol not in _DAILY_CLOSES_CACHE:
        _DAILY_CLOSES_CACHE[symbol] = _load_daily_closes(symbol)
    return _DAILY_CLOSES_CACHE[symbol]


# --------------------------------------------------------------------------- GBM


def run_walk_forward_basis(
    events_df: pl.DataFrame,
    *,
    initial_train_years: int = 2,
    test_block_months: int = 6,
    embargo_sessions: int = 1,
    params: dict | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, list]:
    """Expanding calendar walk-forward LightGBM on the ALL-events ``net_bps``.

    Mirrors ``models/moc_gbm.run_walk_forward`` exactly (same fold builder, same
    ``lgbm.DEFAULT_PARAMS`` regressor) but with the M6-FINAL ``FEATURE_COLS`` that
    add ``basis_bps``. Returns ``(oos_df, importances_df, folds)``: ``oos_df`` is
    every event beyond the initial-train span with an OOS ``pred`` + ``fold``
    column; ``importances_df`` is the mean LightGBM gain per feature across folds.
    """
    if events_df.height == 0:
        empty = events_df.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("pred"),
            pl.lit(None, dtype=pl.Utf8).alias("fold"),
        )
        imp = pl.DataFrame(
            {"feature": list(FEATURE_COLS),
             "mean_gain": [0.0] * len(FEATURE_COLS),
             "n_folds": [0] * len(FEATURE_COLS)},
            schema={"feature": pl.Utf8, "mean_gain": pl.Float64, "n_folds": pl.Int64},
        )
        return empty, imp, []

    sessions = sorted(events_df["session"].unique().to_list())
    folds = walk_forward_folds_calendar(
        sessions,
        initial_train_years=initial_train_years,
        test_block_months=test_block_months,
        embargo_sessions=embargo_sessions,
    )
    oos_parts: list[pl.DataFrame] = []
    imp_accum: dict[str, list[float]] = {c: [] for c in FEATURE_COLS}
    for fold in folds:
        tr = events_df.filter(pl.col("session").is_in(list(fold.train_sessions)))
        te = events_df.filter(pl.col("session").is_in(list(fold.test_sessions)))
        if tr.height == 0 or te.height == 0:
            continue
        booster = lgbm_model.train_one(tr, FEATURE_COLS, LABEL_COL, params=params)
        preds = lgbm_model.predict(booster, te, FEATURE_COLS)
        oos_parts.append(
            te.with_columns(
                pl.Series("pred", preds),
                pl.lit(fold.test_start).alias("fold"),
            )
        )
        gains = booster.feature_importance(importance_type="gain")
        names = booster.feature_name()
        for name, g in zip(names, gains, strict=True):
            if name in imp_accum:
                imp_accum[name].append(float(g))

    oos_df = (
        pl.concat(oos_parts)
        if oos_parts
        else events_df.head(0).with_columns(
            pl.lit(None, dtype=pl.Float64).alias("pred"),
            pl.lit(None, dtype=pl.Utf8).alias("fold"),
        )
    )
    imp_rows = [
        {"feature": c,
         "mean_gain": float(np.mean(imp_accum[c])) if imp_accum[c] else 0.0,
         "n_folds": len(imp_accum[c])}
        for c in FEATURE_COLS
    ]
    importances_df = pl.DataFrame(
        imp_rows,
        schema={"feature": pl.Utf8, "mean_gain": pl.Float64, "n_folds": pl.Int64},
    ).sort("mean_gain", descending=True)
    return oos_df, importances_df, folds


# --------------------------------------------------------------------------- report


def _ascii(df: pl.DataFrame) -> str:
    with pl.Config(
        tbl_formatting="ASCII_MARKDOWN",
        tbl_hide_dataframe_shape=True,
        tbl_hide_column_data_types=True,
        tbl_rows=200,
        tbl_cols=-1,
        tbl_width_chars=260,
    ):
        return str(df)


def _ci(df: pl.DataFrame) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n_events, n_sessions) day-clustered over net_bps."""
    if df.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    m, lo, hi = stress.clustered_mean_ci(
        df["net_bps"].to_numpy(), df["session"].to_numpy()
    )
    return m, lo, hi, df.height, df["session"].n_unique()


def _fmt_ci(t: tuple[float, float, float, int, int]) -> str:
    m, lo, hi, n, ns = t
    if n == 0:
        return "n=0"
    return f"mean={m:.3f}  95%CI=[{lo:.3f}, {hi:.3f}]  n={n}  sessions={ns}"


def _grouped_ci_table(df: pl.DataFrame, key: str, key_name: str) -> pl.DataFrame:
    rows: list[dict] = []
    keys = sorted(df[key].unique().to_list()) if df.height else []
    for k in [*keys, "__POOLED__"]:
        sub = df if k == "__POOLED__" else df.filter(pl.col(key) == k)
        m, lo, hi, n, ns = _ci(sub)
        rows.append({
            key_name: "POOLED" if k == "__POOLED__" else str(k),
            "n_events": n,
            "n_sessions": ns,
            "net_bps_mean": round(m, 3) if n else None,
            "ci_lo": round(lo, 3) if n else None,
            "ci_hi": round(hi, 3) if n else None,
        })
    return pl.DataFrame(
        rows,
        schema={
            key_name: pl.Utf8, "n_events": pl.Int64, "n_sessions": pl.Int64,
            "net_bps_mean": pl.Float64, "ci_lo": pl.Float64, "ci_hi": pl.Float64,
        },
        orient="row",
    )


def _year_col(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.col("session").str.slice(0, 4).alias("year"))


def stiffened_prongs(df: pl.DataFrame) -> dict:
    """The M6-FINAL stiffened promotion prongs (diagnostic echo, NOT a gate here):
    pooled day-clustered CI lower > 0 AND positive point estimate in >=3 of 5
    symbols AND positive point estimate in >=4 of the 7 years."""
    m, lo, hi, n, ns = _ci(df)
    syms = sorted(df["symbol"].unique().to_list()) if df.height else []
    per_sym: dict[str, float | None] = {}
    sym_pos = 0
    for sym in syms:
        sub = df.filter(pl.col("symbol") == sym)
        pe = float(sub["net_bps"].mean()) if sub.height else float("nan")
        per_sym[sym] = round(pe, 3) if sub.height else None
        if sub.height and pe > 0:
            sym_pos += 1

    years = sorted({s[:4] for s in df["session"].to_list()}) if df.height else []
    per_year: dict[str, float | None] = {}
    yr_pos = 0
    for yr in years:
        sub = df.filter(pl.col("session").str.starts_with(yr))
        pe = float(sub["net_bps"].mean()) if sub.height else float("nan")
        per_year[yr] = round(pe, 3) if sub.height else None
        if sub.height and pe > 0:
            yr_pos += 1

    return {
        "pooled_mean_net_bps": round(m, 3) if n else None,
        "pooled_ci_lo": round(lo, 3) if n else None,
        "pooled_ci_hi": round(hi, 3) if n else None,
        "n_events": n,
        "n_sessions": ns,
        "symbols_positive_point_estimate": sym_pos,
        "per_symbol_point_estimate": per_sym,
        "years_positive_point_estimate": yr_pos,
        "per_year_point_estimate": per_year,
        "meets_pooled_lo_gt_0": bool(n and lo > 0),
        "meets_ge_3_of_5_symbols_positive": bool(sym_pos >= 3),
        "meets_ge_4_of_7_years_positive": bool(yr_pos >= 4),
    }


def _cell_block(title: str, df: pl.DataFrame) -> list[str]:
    """One evaluated-stream block: pooled CI, per-symbol, per-year, prongs."""
    return [
        f"### {title}",
        "",
        f"- Pooled (day-clustered): {_fmt_ci(_ci(df))}",
        "",
        "Per-symbol:",
        "",
        _ascii(_grouped_ci_table(df, "symbol", "symbol")),
        "",
        "Per-year:",
        "",
        _ascii(_grouped_ci_table(_year_col(df), "year", "year")),
        "",
        "Stiffened prongs (>=3/5 symbols positive AND >=4/7 years positive):",
        "",
        "```",
        json.dumps(stiffened_prongs(df), indent=2, default=str),
        "```",
        "",
    ]


def _stratified_ground_truth(df: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """<=k stratified events laid out near vs mid vs cross vs realized (v6.1).

    Stratified: biggest winners, biggest losers, largest |basis|. Columns:
    near_price (indicative), entry_mid (market), basis_bps (near vs mid), entry_px
    + entry_in_nbbo (fill sanity), cross_px + cross_vs_mid_bps (realized clearing
    vs market), cross_vs_close_bps (cross vs the official daily close — 0 confirms
    the daily-close cross source), net_bps (realized pnl), and basis_agrees_cross
    (did the near-vs-mid sign predict the cross-vs-mid sign)."""
    schema = {
        "session": pl.Utf8, "symbol": pl.Utf8, "side": pl.Int64,
        "near_price": pl.Float64, "entry_mid": pl.Float64, "basis_bps": pl.Float64,
        "entry_bid": pl.Float64, "entry_ask": pl.Float64, "entry_px": pl.Float64,
        "entry_in_nbbo": pl.Boolean, "cross_px": pl.Float64,
        "cross_vs_mid_bps": pl.Float64, "bar_close": pl.Float64,
        "cross_vs_close_bps": pl.Float64, "basis_agrees_cross": pl.Boolean,
        "net_bps": pl.Float64,
    }
    if df.height == 0:
        return pl.DataFrame(schema=schema)
    d = df.with_columns(pl.arange(0, pl.len()).alias("_idx"))
    winners = d.sort("net_bps", descending=True).head(3)["_idx"].to_list()
    losers = d.sort("net_bps", descending=False).head(3)["_idx"].to_list()
    big = d.sort(pl.col("basis_bps").abs(), descending=True).head(4)["_idx"].to_list()
    picked: list[int] = []
    for i in [*winners, *losers, *big]:
        if i not in picked:
            picked.append(i)
        if len(picked) >= k:
            break
    sub = d.filter(pl.col("_idx").is_in(picked)).drop("_idx")
    return sub.with_columns(
        pl.when(pl.col("entry_bid").is_not_null() & pl.col("entry_ask").is_not_null())
        .then(
            (pl.col("entry_px") >= pl.col("entry_bid") * 0.999)
            & (pl.col("entry_px") <= pl.col("entry_ask") * 1.001)
        )
        .otherwise(None).alias("entry_in_nbbo"),
        ((pl.col("cross_px") - pl.col("entry_mid")) / pl.col("entry_mid") * 1e4)
        .alias("cross_vs_mid_bps"),
        pl.when(pl.col("bar_close").is_not_null() & (pl.col("bar_close") > 0))
        .then((pl.col("cross_px") - pl.col("bar_close")) / pl.col("bar_close") * 1e4)
        .otherwise(None).alias("cross_vs_close_bps"),
    ).with_columns(
        (pl.col("basis_bps").sign() == pl.col("cross_vs_mid_bps").sign())
        .alias("basis_agrees_cross"),
    ).select(list(schema))


def build_report_md(
    trial_id: str,
    events: pl.DataFrame,
    cells: dict[str, pl.DataFrame],
    gated: pl.DataFrame,
    oos: pl.DataFrame,
    importances: pl.DataFrame,
    folds: list,
    stats: dict,
) -> str:
    counts = stats["counts"]
    years = sorted({s[:4] for s in events["session"].to_list()}) if events.height else []
    fold_meta = [
        {"test_start": f.test_start, "test_end": f.test_end,
         "n_train_sessions": len(f.train_sessions), "n_test_sessions": len(f.test_sessions)}
        for f in folds
    ]
    md: list[str] = [
        f"# M6-FINAL near-price basis report — {trial_id}",
        "",
        "Family `moc_imbalance_v1`, M6-FINAL cell (registered 2026-07-17) — THE "
        "FAMILY'S LAST EXPERIMENT (the family closes after this run, pass or fail). "
        "Signal at 15:55:10 ET: basis_bps = 1e4 * (near - mid)/mid, near = last "
        "NOII message at-or-before 15:55:10 with near_price>0, mid = prevailing "
        "bbo-1s mid. Direction WITH the basis (buy iff near>mid). Entry = taker "
        "market at 15:55:10 + U[5,25]s latency (bbo-1s cross + 0.5bp slip); exit AT "
        "the official closing cross. Net via decompose.plan_pnl (SEC/TAF 0.3bp on "
        "the sell leg). NO ledger writes; NO pass/fail interpretation.",
        "",
        f"Symbols: {', '.join(stats['symbols'])}    seed={stats['seed']}",
        f"Sessions in range (< holdout {HOLDOUT_START.isoformat()}): {stats['sessions_in_range']}",
        f"ALL-events universe (valid basis + cross): {events.height} events    years: {years}",
        f"Splits present: {sorted(set(split_of(s) for s in events['session'].unique())) if events.height else []}",
        "",
        "DATA-REALITY (VERIFIED on the owned tape, documented per task): NOII "
        "near/far indicative prices are 0 until ~15:55:00 ET; near first turns >0 "
        "at exactly 15:55:00 across the full 2020->2026 span. At 15:55:10 there are "
        "~40 disseminated messages with near/far/ref all populated, so the basis is "
        "well defined every covered session. Growth vs 15:53/15:51 is meaningful "
        "(imbalance shares evolve; at 15:53/15:51 near is still 0 so norm_imb there "
        "uses signal_at's near->ref price fallback). near_drift_51_55 DEGENERATES "
        "to 0 (near=0 at 15:51) — computed exactly per formula; see importances.",
        "",
        "## 1. Event funnel / skipped-session counters",
        "```",
        json.dumps(counts, indent=2, default=str),
        "```",
        "Per-symbol skipped (no cross print):",
        "```",
        json.dumps(stats["per_symbol_no_cross"], indent=2, default=str),
        "```",
        "",
        "## 2. Classical cell |basis_bps| >= 5",
        "",
        *_cell_block("|basis| >= 5 bps", cells["5.0"]),
        "## 3. Classical cell |basis_bps| >= 10",
        "",
        *_cell_block("|basis| >= 10 bps", cells["10.0"]),
        "## 4. GBM cell (LightGBM regression on ALL-events net, fixed gate pred>0)",
        "",
        "Model: LightGBM (lgbm.DEFAULT_PARAMS, objective=huber) on event net_bps; "
        "expanding calendar walk-forward (>=2y initial train, 6-month test blocks, "
        "1-session embargo); FIXED gate pred>0. Features: the registered M6-GBM set "
        f"recomputed at 15:55:10 + basis_bps ({len(FEATURE_COLS)} cols).",
        "",
        "Walk-forward folds:",
        "```",
        json.dumps(fold_meta, indent=2, default=str),
        "```",
        f"OOS events (beyond initial-train span): {oos.height}    "
        f"GATED (pred>0) taken: {gated.height}",
        "",
        f"- UNGATED same-span baseline (all OOS events): {_fmt_ci(_ci(oos))}",
        f"- GATED (pred>0) taken stream:                 {_fmt_ci(_ci(gated))}",
        "",
        *_cell_block("GBM-gated (pred > 0) taken stream", gated),
        "## 5. GBM feature importances (mean LightGBM gain across folds)",
        "",
        _ascii(importances),
        "",
        "## 6. PROTOCOL v6.1 ground-truthing — 10 stratified events (near vs mid vs cross vs realized)",
        "",
        "near_price: NOII indicative clearing price. entry_mid: prevailing bbo-1s "
        "mid at 15:55:10. basis_bps: near vs mid. entry_in_nbbo: entry fill within "
        "the prevailing NBBO. cross_vs_mid_bps: realized clearing (cross) vs the "
        "market mid. cross_vs_close_bps: cross vs the official daily close (0 "
        "confirms the daily-close cross source, RTH fetch excludes the 16:00 "
        "print). basis_agrees_cross: did sign(near-mid) predict sign(cross-mid).",
        "",
        _ascii(_stratified_ground_truth(events)),
        "",
        "## 7. Exit-reason distribution (ALL events)",
        "",
    ]
    if events.height:
        er = events.group_by("exit_reason").agg(pl.len().alias("count")).sort(
            "count", descending=True
        )
        md.append(_ascii(er))
    else:
        md.append("(no events)")
    md.append("")
    return "\n".join(md)


def write_outputs(
    out_dir: Path,
    trial_id: str,
    events: pl.DataFrame,
    oos: pl.DataFrame,
    report_md: str,
) -> tuple[Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    events_path = out_dir / "events.parquet"
    oos_path = out_dir / "oos_predictions.parquet"
    report_path = out_dir / "report.md"
    events.write_parquet(events_path)
    oos.write_parquet(oos_path)
    report_path.write_text(report_md, encoding="utf-8")
    return events_path, oos_path, report_path


def evaluate(events: pl.DataFrame, seed: int) -> dict:
    """Assemble the three evaluated streams from the ALL-events universe.

    Returns ``{cells, gated, oos, importances, folds}`` — the two classical
    |basis| subsets, the GBM OOS + gated (pred>0) stream, feature importances and
    the walk-forward folds. Pure over ``events`` (LightGBM seed is fixed in
    ``lgbm.DEFAULT_PARAMS``)."""
    cells = {
        f"{thr}": events.filter(pl.col("basis_bps").abs() >= thr)
        for thr in CLASSICAL_THRESHOLDS_BPS
    }
    oos, importances, folds = run_walk_forward_basis(events)
    gated = (
        oos.filter(pl.Series(gbm_gate(oos["pred"].to_numpy()))) if oos.height else oos
    )
    return {
        "cells": cells, "gated": gated, "oos": oos,
        "importances": importances, "folds": folds,
    }


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--trial-id", default="M6-FINAL-basis-v1", help="Experiment id -> research/experiments/<id>/.")
@click.option("--symbols", default=SYMBOLS_DEFAULT, help="Comma-separated Nasdaq universe.")
@click.option("--start", required=True, help="First session (ISO date), inclusive.")
@click.option("--end", required=True, help="Last session (ISO date), inclusive; < holdout.")
@click.option("--seed", default=7, type=int, help="Latency-draw seed.")
@click.option("--noii-dir", default=None, help="NOII lake root (default data/raw/noii).")
@click.option("--bbo-dir", default=None, help="BBO-1s lake root (default data/raw/bbo1s).")
@click.option("--unseal-holdout", is_flag=True, help="HOLDOUT CEREMONY: run ONLY sealed "
              "sessions (>= holdout). Requires ENGINEV51_UNSEAL_TOKEN=I_UNDERSTAND_ONE_SHOT.")
def main(
    trial_id: str,
    symbols: str,
    start: str,
    end: str,
    seed: int,
    noii_dir: str | None,
    bbo_dir: str | None,
    unseal_holdout: bool,
) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    settings = get_settings()
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    if unseal_holdout:
        import os as _os

        from enginev51.protocol import ledger_append
        if _os.environ.get("ENGINEV51_UNSEAL_TOKEN") != "I_UNDERSTAND_ONE_SHOT":
            raise SystemExit(
                "unseal-holdout requires ENGINEV51_UNSEAL_TOKEN=I_UNDERSTAND_ONE_SHOT "
                "(PROTOCOL v6 §1 one-shot ceremony)."
            )
        ledger_append("note", {"event": "HOLDOUT_UNSEALED", "trial_id": trial_id,
                               "window": f"{start}..{end}"})
    else:
        assert_before_holdout(end_d)

    t0 = time.time()
    events, stats = run_basis_trial(
        settings,
        symbols=sym_list,
        start=start_d,
        end=end_d,
        seed=seed,
        noii_dir=noii_dir,
        bbo_dir=bbo_dir,
        holdout_only=unseal_holdout,
    )
    ev = evaluate(events, seed)
    report_md = build_report_md(
        trial_id, events, ev["cells"], ev["gated"], ev["oos"],
        ev["importances"], ev["folds"], stats,
    )
    wall_s = time.time() - t0

    out_dir = experiments_dir() / trial_id
    events_path, oos_path, report_path = write_outputs(
        out_dir, trial_id, events, ev["oos"], report_md
    )

    click.echo(f"trial: {trial_id}  symbols={','.join(sym_list)}  {start}..{end}  seed={seed}")
    click.echo(f"sessions in range (< holdout): {stats['sessions_in_range']}")
    click.echo(f"event funnel: {json.dumps(stats['counts'], default=str)}")
    click.echo("")
    for thr in CLASSICAL_THRESHOLDS_BPS:
        click.echo(f"classical |basis|>={thr}:  {_fmt_ci(_ci(ev['cells'][str(thr)]))}")
    click.echo(f"GBM ungated same-span:   {_fmt_ci(_ci(ev['oos']))}")
    click.echo(f"GBM gated (pred>0):      {_fmt_ci(_ci(ev['gated']))}")
    click.echo("")
    click.echo(f"events:  {events_path}")
    click.echo(f"oos:     {oos_path}")
    click.echo(f"report:  {report_path}")
    click.echo(f"wall: {wall_s:.1f}s")


if __name__ == "__main__":
    main()
