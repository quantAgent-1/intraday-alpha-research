"""Cell runner: load → features → state machine → attribution → outputs.

BUILD-SPEC §5, §7. Emits per-cell ``events.parquet`` (one row per raw trigger),
``summary.json`` (counts + pooled means per stream; NO verdicts), and
``report-skeleton.md``. Holdout is enforced at every load boundary
(max ts <= 2026-05-31, else SealViolation).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import polars as pl

from enginev51.config import PROJECT_ROOT, Settings, get_settings
from enginev51.data import calendar, store
from enginev51.protocol import HOLDOUT_START, SealViolation
from enginev51.reversion.features import (
    GateBaseline,
    build_gate_baseline,
    compute_session_features,
    session_gate_arrays,
)
from enginev51.reversion.meta import META_THRESHOLD
from enginev51.reversion.ou import OUCalibrator
from enginev51.reversion.signal import run_session

FEED = "sip"
NS_PER_S = 1_000_000_000
HOLDOUT_NS = int(datetime(HOLDOUT_START.year, HOLDOUT_START.month, HOLDOUT_START.day,
                          tzinfo=UTC).timestamp()) * NS_PER_S
HOLD_BARS = {"30m": 1800, "2h": 7200, "4h": 14400}
EXPERIMENT_DIR = PROJECT_ROOT / "research" / "experiments" / "M18-reversion-system"
META_POOLED_DIR = EXPERIMENT_DIR / "meta_pooled"
GATE_TRAILING_SESSIONS = 60

# Pooled-meta universe (BUILD-SPEC §4). MU first: it is the only name with a
# 2024 history, so it anchors months 1..12 of the pooled walk-forward (others
# start 2025-09). One pooled walk-forward per hold ceiling over these names.
DEV_END = "2026-05-31"
POOL_UNIVERSE = ["MU", "NVDA", "TSLA", "AMD"]
CELL_START = {"MU": "2024-01-02", "NVDA": "2025-09-02", "TSLA": "2025-09-02", "AMD": "2025-09-02"}

# engineV2 TRAIN window ∩ event_bars1s (BUILD-SPEC §7 anchor).
ANCHOR_SYMBOL = "TSLA"
ANCHOR_START = "2025-09-02"
ANCHOR_END = "2026-03-01"


def _assert_holdout(ts: np.ndarray, symbol: str, session: str) -> None:
    if ts.size and int(ts.max()) >= HOLDOUT_NS:
        raise SealViolation(
            f"{symbol} {session}: bar ts >= holdout {HOLDOUT_START} — refusing to load"
        )


def available_sessions(
    settings: Settings, symbol: str, start: str, end: str
) -> list[str]:
    """Sorted event_bars1s day-keys for symbol in [start, end] (inclusive),
    never into the holdout (< 2026-06-01)."""
    cap = HOLDOUT_START.isoformat()  # '2026-06-01' — hard seal
    days: set[str] = set()
    for root in settings.read_roots:
        d = root / FEED / "event_bars1s" / symbol.upper()
        if d.is_dir():
            for f in d.glob("*.parquet"):
                days.add(f.stem)
    return sorted(s for s in days if start <= s <= end and s < cap)


def _load_session(settings: Settings, symbol: str, session: str) -> pl.DataFrame | None:
    sd = date.fromisoformat(session)
    try:
        open_dt, close_dt = calendar.session_bounds_utc(sd)
    except ValueError:
        return None
    open_ns = int(open_dt.timestamp()) * NS_PER_S
    close_ns = int(close_dt.timestamp()) * NS_PER_S
    lf = store.scan_kind_multi(settings.read_roots, FEED, "event_bars1s", symbol)
    df = lf.filter((pl.col("ts") >= open_ns) & (pl.col("ts") < close_ns)).sort("ts").collect()
    if df.height == 0:
        return None
    _assert_holdout(df["ts"].to_numpy(), symbol, session)
    return df


@dataclass
class CellResult:
    symbol: str
    hold: str
    n_triggers: int
    events: pl.DataFrame
    summary: dict


def _base_events(
    symbol: str, hold: str, *, entry_model: str, start: str, end: str,
    with_gates: bool, settings: Settings,
) -> pl.DataFrame:
    """Base per-session simulation → one row per raw trigger, NO meta columns.

    This is the deterministic substrate the pooled meta trains on; it does not
    depend on the other names, so a name's base events are identical whether run
    for its own cell or as part of another cell's pooled training population."""
    max_hold_bars = HOLD_BARS[hold]
    sessions = available_sessions(settings, symbol, start, end)
    all_records: list[dict] = []
    prior_gate_arrays: list[dict[str, np.ndarray]] = []
    calibrator = OUCalibrator()
    for session in sessions:
        df = _load_session(settings, symbol, session)
        if df is None:
            continue
        feat = compute_session_features(df)
        baseline = (
            build_gate_baseline(prior_gate_arrays[-GATE_TRAILING_SESSIONS:])
            if with_gates else GateBaseline(float("nan"), float("nan"), float("nan"))
        )
        recs = run_session(
            feat, symbol, session, calibrator, baseline,
            entry_model=entry_model, max_hold_bars=max_hold_bars,
        )
        all_records.extend(recs)
        if with_gates:
            prior_gate_arrays.append(session_gate_arrays(feat))
    return _records_to_df(all_records)


@dataclass
class PooledHold:
    hold: str
    events_by_name: dict[str, pl.DataFrame]   # per-name events + meta columns
    folds: list
    trained: bool


def run_pooled_hold(
    hold: str, *, settings: Settings | None = None, persist: bool = True,
) -> PooledHold:
    """ONE pooled meta walk-forward for a hold ceiling (BUILD-SPEC §4).

    Runs the maker-first, gated base simulation for every name in POOL_UNIVERSE,
    pools the GATED trades into a single monthly walk-forward, scores each name's
    trades from that shared model, and (optionally) persists the pooled fold models
    + feature importances under ``meta_pooled/{hold}/``. Deterministic: the pooled
    training population and the LightGBM seed are fixed, so the per-name scored
    events are identical regardless of which cell triggered the run."""
    settings = settings or get_settings()
    if hold not in HOLD_BARS:
        raise ValueError(f"hold must be one of {sorted(HOLD_BARS)}, got {hold!r}")

    base = {
        nm: _base_events(nm, hold, entry_model="maker", start=CELL_START[nm],
                         end=DEV_END, with_gates=True, settings=settings)
        for nm in POOL_UNIVERSE
    }
    non_empty = [df for df in base.values() if df.height > 0]
    if non_empty:
        from enginev51.reversion.meta import walk_forward
        pooled = pl.concat(non_empty, how="diagonal_relaxed")
        mres = walk_forward(pooled)
        scored = mres.events
        events_by_name = {
            nm: (_ensure_meta_columns(scored.filter(pl.col("symbol") == nm))
                 if scored.height else _ensure_meta_columns(base[nm]))
            for nm in POOL_UNIVERSE
        }
        folds, trained, boosters = mres.folds, mres.trained, mres.boosters
    else:
        events_by_name = {nm: _ensure_meta_columns(base[nm]) for nm in POOL_UNIVERSE}
        folds, trained, boosters = [], False, []

    if persist:
        _persist_pooled_meta(hold, folds, boosters)
    return PooledHold(hold, events_by_name, folds, trained)


def _persist_pooled_meta(hold: str, folds: list, boosters: list) -> None:
    """Write the pooled fold models + importances once per hold ceiling."""
    from enginev51.reversion.meta import FEATURES, MIN_TRAIN_MONTHS, SEED
    d = META_POOLED_DIR / hold
    d.mkdir(parents=True, exist_ok=True)
    if folds:
        fold_rows = [
            {"score_month": f.score_month, "n_train": f.n_train, "n_score": f.n_score,
             "max_train_ts": f.max_train_ts, "min_score_ts": f.min_score_ts,
             **{f"imp_{k}": v for k, v in f.importances.items()}}
            for f in folds
        ]
        pl.DataFrame(fold_rows).write_parquet(d / "folds.parquet")
        for f, b in zip(folds, boosters, strict=True):
            b.save_model(str(d / f"fold_{f.score_month}.txt"))
    meta = {
        "hold": hold, "pooled": True, "universe": POOL_UNIVERSE,
        "threshold": META_THRESHOLD, "seed": SEED, "min_train_months": MIN_TRAIN_MONTHS,
        "n_folds": len(folds), "features": FEATURES,
        "first_score_month": folds[0].score_month if folds else None,
        "last_score_month": folds[-1].score_month if folds else None,
    }
    (d / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _write_cell(out_dir: Path, events: pl.DataFrame, summary: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    events.write_parquet(out_dir / "events.parquet", compression="zstd")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out_dir / "report-skeleton.md").write_text(_report_skeleton(summary), encoding="utf-8")


def run_cell(
    symbol: str, hold: str, *, entry_model: str, start: str, end: str,
    with_gates: bool = True, with_meta: bool = True,
    settings: Settings | None = None, out_dir: Path | None = None,
    write: bool = True,
) -> CellResult:
    """Run one (symbol, hold) cell end-to-end.

    The system-under-test path (maker entry, gated, meta) routes through the
    POOLED walk-forward: it runs all four names' base sims to build the shared
    training population, then extracts this symbol's scored events. The anchor /
    bare-rule path (with_meta=False or taker) runs only this symbol. ``start`` /
    ``end`` govern the single-symbol path; the pooled path uses the fixed
    POOL_UNIVERSE windows."""
    settings = settings or get_settings()
    symbol = symbol.upper()
    if hold not in HOLD_BARS:
        raise ValueError(f"hold must be one of {sorted(HOLD_BARS)}, got {hold!r}")

    if with_meta and with_gates and entry_model == "maker" and symbol in POOL_UNIVERSE:
        ph = run_pooled_hold(hold, settings=settings, persist=write)
        events = ph.events_by_name[symbol]
        trained = ph.trained
    else:
        events = _ensure_meta_columns(
            _base_events(symbol, hold, entry_model=entry_model, start=start, end=end,
                         with_gates=with_gates, settings=settings)
        )
        trained = False

    summary = _summarise(events, symbol, hold, entry_model, trained)
    if write:
        _write_cell(out_dir or (EXPERIMENT_DIR / "cells" / f"{symbol}_{hold}"), events, summary)
    return CellResult(symbol, hold, events.height, events, summary)


def run_all_cells(
    settings: Settings | None = None, *, write: bool = True,
) -> list[CellResult]:
    """Re-run all 12 system cells efficiently: one pooled walk-forward per hold
    ceiling (each hold's 4 names share the pooled meta), writing every cell."""
    settings = settings or get_settings()
    results: list[CellResult] = []
    for hold in ("30m", "2h", "4h"):
        ph = run_pooled_hold(hold, settings=settings, persist=write)
        for sym in POOL_UNIVERSE:
            events = ph.events_by_name[sym]
            summary = _summarise(events, sym, hold, "maker", ph.trained)
            if write:
                _write_cell(EXPERIMENT_DIR / "cells" / f"{sym}_{hold}", events, summary)
            results.append(CellResult(sym, hold, events.height, events, summary))
    return results


def _records_to_df(records: list[dict]) -> pl.DataFrame:
    if not records:
        return pl.DataFrame()
    keys: list[str] = []
    seen: set[str] = set()
    for r in records:
        for k in r:
            if k not in seen:
                seen.add(k)
                keys.append(k)
    rows = [{k: r.get(k) for k in keys} for r in records]
    return pl.DataFrame(rows, infer_schema_length=None)


def _ensure_meta_columns(events: pl.DataFrame) -> pl.DataFrame:
    if events.height == 0:
        return events
    cols = []
    if "meta_p" not in events.columns:
        cols.append(pl.lit(None, dtype=pl.Float64).alias("meta_p"))
    if "meta_kept" not in events.columns:
        cols.append(pl.lit(True).alias("meta_kept"))
    if "meta_scored" not in events.columns:
        cols.append(pl.lit(False).alias("meta_scored"))
    return events.with_columns(cols) if cols else events


def _stream_means(df: pl.DataFrame, prefix: str) -> dict:
    """Pooled means for a stream (no verdicts)."""
    if df.height == 0:
        return {"n": 0}
    out = {"n": df.height}
    for metric in ("net", "gross", "mid_to_mid"):
        col = f"{prefix}_{metric}"
        if col in df.columns:
            v = df[col].drop_nulls().drop_nans()
            out[f"mean_{metric}"] = float(v.mean()) if v.len() else float("nan")
    if "shares" in df.columns:
        s = df["shares"].drop_nulls()
        out["mean_shares"] = float(s.mean()) if s.len() else float("nan")
    return out


def _b5_through(df: pl.DataFrame) -> pl.DataFrame:
    """B5 (a): keep only fills that went THROUGH the limit (strict)."""
    return df.filter(pl.col("maker_fill_through")) if "maker_fill_through" in df.columns else df


def _b5_haircut50(df: pl.DataFrame) -> pl.DataFrame:
    """B5 (b): keep all through-fills + a deterministic 50 % of touch-only fills."""
    if "keep_50" not in df.columns:
        return df
    if "maker_fill_through" in df.columns:
        return df.filter(pl.col("maker_fill_through") | pl.col("keep_50"))
    return df.filter(pl.col("keep_50"))


def _summarise(
    events: pl.DataFrame, symbol: str, hold: str, entry_model: str, meta_trained: bool
) -> dict:
    if events.height == 0:
        return {"symbol": symbol, "hold": hold, "entry_model": entry_model,
                "n_triggers": 0, "streams": {}}
    opened = events.filter(pl.col("opened")) if "opened" in events.columns else events
    filled = opened.filter(pl.col("maker_filled")) if "maker_filled" in opened.columns else opened
    gated = filled.filter(pl.col("passed_G1") & pl.col("passed_G2")) if "passed_G1" in filled.columns else filled

    # Meta veto partition of the GATED stream. Scored trades (in a fold's score
    # month) are kept iff meta_p >= threshold; trades in unscored months remain in
    # `gated` but are EXCLUDED from `gated_meta` and counted as n_unscored so
    # nothing is silently dropped: n_gated == n_scored + n_unscored,
    # n_gated_meta == n_scored − n_vetoed.
    if "meta_scored" in gated.columns:
        gated_scored = gated.filter(pl.col("meta_scored"))
        gated_meta = gated_scored.filter(pl.col("meta_kept"))
        n_scored = gated_scored.height
        n_vetoed = gated_scored.filter(~pl.col("meta_kept")).height
        n_unscored = gated.height - n_scored
    else:  # no meta columns (defensive) — treat all gated as kept, none scored
        gated_meta = gated
        n_scored, n_vetoed, n_unscored = gated.height, 0, 0

    # §3/§5 maker fill rate = filled / posted, where posts = maker orders placed
    # (filled + cancelled-after-60s). Computed from the maker_posted flag, never
    # 1.0-by-construction.
    if "maker_posted" in events.columns:
        posted = events.filter(pl.col("maker_posted"))
        n_posted = posted.height
        n_filled = posted.filter(pl.col("maker_filled")).height if "maker_filled" in posted.columns else n_posted
    else:
        n_posted, n_filled = 0, filled.height
    n_cancelled = n_posted - n_filled
    maker_fill_rate = (n_filled / n_posted) if n_posted else 0.0
    n_open = opened.height

    return {
        "symbol": symbol, "hold": hold, "entry_model": entry_model,
        "n_triggers": events.height, "n_opened": n_open,
        "n_posted": n_posted, "n_filled": n_filled, "n_cancelled": n_cancelled,
        "maker_fill_rate": maker_fill_rate, "meta_trained": meta_trained,
        "meta": {
            "pooled": True, "trained": meta_trained, "threshold": META_THRESHOLD,
            "n_gated": gated.height, "n_scored": n_scored, "n_vetoed": n_vetoed,
            "n_unscored": n_unscored,
        },
        "streams": {
            "raw_taker": _stream_means(opened, "taker"),
            "raw_maker": _stream_means(filled, "maker"),
            "gated": _stream_means(gated, "maker"),
            "gated_meta": _stream_means(gated_meta, "maker"),
            # B5 re-pricings on the raw maker population (attribution) …
            "b5_through": _stream_means(_b5_through(filled), "maker"),
            "b5_haircut50": _stream_means(_b5_haircut50(filled), "maker"),
            # … and on the system verdict streams (REGISTRATION B5 / §5).
            "gated_b5_through": _stream_means(_b5_through(gated), "maker"),
            "gated_b5_haircut50": _stream_means(_b5_haircut50(gated), "maker"),
            "gated_meta_b5_through": _stream_means(_b5_through(gated_meta), "maker"),
            "gated_meta_b5_haircut50": _stream_means(_b5_haircut50(gated_meta), "maker"),
        },
    }


def _report_skeleton(summary: dict) -> str:
    return (
        f"# M18 cell {summary['symbol']}:{summary['hold']} — report skeleton (no interpretation)\n\n"
        f"entry_model={summary['entry_model']} n_triggers={summary['n_triggers']} "
        f"n_opened={summary.get('n_opened', 0)}\n\n"
        "## Streams (means; fill in verdict language downstream)\n\n"
        "| stream | n | mean_net | mean_gross | mean_mid_to_mid | mean_shares |\n"
        "|---|---|---|---|---|---|\n"
        + "".join(
            f"| {name} | {s.get('n', 0)} | {s.get('mean_net', '')} | {s.get('mean_gross', '')} "
            f"| {s.get('mean_mid_to_mid', '')} | {s.get('mean_shares', '')} |\n"
            for name, s in summary.get("streams", {}).items()
        )
        + "\n(attribution / B-bar verdicts intentionally omitted — harness output only)\n"
    )


# --------------------------------------------------------------------------- anchor

@dataclass
class AnchorResult:
    n: int
    gross_per_trade: float
    net_per_trade: float
    mid_to_mid_per_trade: float
    avg_shares: float
    table: list[dict]
    passed: bool


# A11 PASS bands.
_ANCHOR_BANDS = {
    "n": (2508 * 0.85, 2508 * 1.15),
    "gross_per_trade": (-5.5, -3.0),
    "net_per_trade": (-9.5, -5.5),
    "mid_to_mid_per_trade": (-1.0, 1.5),
    "avg_shares": (48.0, 74.0),
}


def run_anchor(settings: Settings | None = None) -> AnchorResult:
    """BUILD-SPEC §7: TSLA taker bare-rule, engineV2 TRAIN window, REALISTIC.
    Compares the raw-taker stream to the A11 PASS bands."""
    settings = settings or get_settings()
    res = run_cell(
        ANCHOR_SYMBOL, "30m", entry_model="taker",
        start=ANCHOR_START, end=ANCHOR_END,
        with_gates=False, with_meta=False, settings=settings, write=False,
    )
    ev = res.events
    opened = ev.filter(pl.col("opened")) if ev.height and "opened" in ev.columns else ev
    n = opened.height
    gross = float(opened["taker_gross"].mean()) if n else float("nan")
    net = float(opened["taker_net"].mean()) if n else float("nan")
    m2m = float(opened["taker_mid_to_mid"].mean()) if n else float("nan")
    shares = float(opened["shares"].mean()) if n else float("nan")

    observed = {
        "n": n, "gross_per_trade": gross, "net_per_trade": net,
        "mid_to_mid_per_trade": m2m, "avg_shares": shares,
    }
    table = []
    all_pass = True
    for metric, (lo, hi) in _ANCHOR_BANDS.items():
        val = observed[metric]
        ok = bool(np.isfinite(val) and lo <= val <= hi)
        all_pass = all_pass and ok
        table.append({"metric": metric, "band": f"[{lo:g}, {hi:g}]",
                      "observed": val, "pass": ok})
    return AnchorResult(n, gross, net, m2m, shares, table, all_pass)
