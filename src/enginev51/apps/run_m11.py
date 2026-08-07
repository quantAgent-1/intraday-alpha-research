"""M11 cross-sectional out-of-sample generalization runner.

Applies the FROZEN ``moc_imbalance_v1`` near-basis rule (M3_REGISTRATION.md, "M11
cross-sectional out-of-sample generalization", registered 2026-07-17) to 28 Nasdaq
names it was NEVER fit on. This is a FROZEN-rule OOS test — zero parameter changes,
not a search. It writes NO ledger row and NO pass/fail verdict.

FROZEN signal (near-vs-REF variant; the registration's verified equivalent to the
validated near-vs-mid rule: corr 0.9999). Per (symbol, session), all instants ET:

    1. near, ref = the LAST NOII message at-or-before 15:55:10 with BOTH
       near_price > 0 AND ref_price > 0 (PIT; skip + count if none). ``ref_price``
       from the SAME NOII message is the mid proxy — NO quote feed needed (the 28
       names have NOII partitions but no bbo-1s and no tick tape; DATA NOTE).
    2. basis_bps = 1e4 * (near - ref) / ref.
    3. FIRE iff |basis_bps| >= 10; side = sign(near - ref) (buy iff near > ref).
    4. ENTRY = a CONSERVATIVE fixed taker cost off ref: entry_px = ref * (1 + side *
       (2 bps half-spread + 0.5 bp slip) / 1e4). The 2 bps half-spread is DELIBERATELY
       wider than the ~1 bp these liquid megacaps run, so this UNDERSTATES the edge
       versus the bbo-1s taker fills used on the original 5 names — a conservative
       floor, not the true fill.
    5. EXIT = the official daily close (``auction_replay.cross_price_for`` →
       ``_daily_closes``; the Nasdaq official close IS the closing-cross price).
    6. net_bps via ``decompose.plan_pnl`` (SEC/TAF 0.3 bp on the sell leg) — the
       SAME decomposition the validated pipeline uses, fed two synthetic Fills
       (entry at entry_px with mid=ref; exit AT the close with zero spread/slip),
       so net_bps == side*(close - entry_px)/entry_px*1e4 - fees. Identical in
       spirit to ``replay_moc_event``; only the entry FILL is a fixed conservative
       cost instead of a tick/bbo cross (no quote tape exists for these names).

Report (research/experiments/<trial_id>/report.md): (1) POOLED classical net_bps
day-clustered CI on the 28-name pool (pure OOS — the rule was never fit on these);
(2) per-symbol table; (3) per-SECTOR table + how many sectors are net-positive
(the registered majority-of-sectors prong); (4) n_events and whether >= 500;
(5) by-year; (6) META-TRANSFER — the M8 meta model TRAINED ONLY on the original 5
names (frozen), applied to the 28, testing whether gating by that 5-name-trained
P(win) >= 0.55 improves the 28-name hit rate. Plus a 10-event stratified v6.1
ground-truth (near/ref vs the daily close).

Hard PIT/holdout guard: refuses any ``--end`` on/after ``protocol.HOLDOUT_START``
and hard-filters every session strictly before it.

    uv run python -m enginev51.apps.run_m11 --trial-id M11-oos-28 \
        --start 2020-01-02 --end 2026-05-31 --seed 7
"""

from __future__ import annotations

import json
import time
from datetime import UTC, date, datetime
from pathlib import Path

import click
import numpy as np
import polars as pl
import structlog

from enginev51.apps.run_basis_trial import basis_bps_of, basis_pit_features
from enginev51.backtest import stress
from enginev51.backtest.auction_replay import adv20_dollars, cross_price_for
from enginev51.backtest.decompose import plan_pnl
from enginev51.backtest.fills import Fill
from enginev51.config import Settings, get_settings
from enginev51.data import calendar
from enginev51.data.noii import et_ns, load_noii_session, noii_root
from enginev51.models import moc_meta
from enginev51.models.moc_gbm import symbol_onehot, trailing_vol20
from enginev51.protocol import (
    HOLDOUT_START,
    experiments_dir,
    refuse_end_on_or_after_holdout,
    split_of,
)

log = structlog.get_logger(__name__)

# --------------------------------------------------------------------------- constants

# Registered 28-name OOS universe, grouped by sector (NONE in the original 5:
# NVDA/TSLA/AMD/MU/GOOGL). The sector map is part of the registered majority-of-
# sectors prong.
SECTORS: dict[str, tuple[str, ...]] = {
    "MegaTech": ("AAPL", "MSFT", "META", "NFLX", "ADBE", "INTU"),
    "Semis": ("AVGO", "QCOM", "AMAT", "MRVL", "LRCX", "KLAC", "TXN", "INTC", "CSCO"),
    "Consumer": ("PEP", "COST", "SBUX", "MDLZ"),
    "Health": ("AMGN", "GILD", "VRTX", "ISRG"),
    "Comm": ("TMUS", "CMCSA"),
    "Other": ("HON", "BKNG", "PLTR"),
}
SECTOR_OF: dict[str, str] = {
    sym: sector for sector, syms in SECTORS.items() for sym in syms
}
UNIVERSE_28: tuple[str, ...] = tuple(sorted(SECTOR_OF))

# Registered instant.
SIGNAL_HMS = (15, 55, 10)

# Registered frozen firing threshold.
FIRE_BASIS_BPS: float = 10.0

# Conservative fixed taker entry cost off ref (documented understatement vs the
# ~1 bp real half-spread on these liquid names; wider than the bbo-1s fills on the
# original 5, so the edge is UNDERSTATED not inflated).
HALF_SPREAD_BPS: float = 2.0
SLIP_BPS: float = 0.5
TAKER_COST_BPS: float = HALF_SPREAD_BPS + SLIP_BPS  # 2.5 bps in the adverse direction
SEC_TAF_SELL_BPS: float = 0.3

# Registered pass prong: >= 500 events.
MIN_EVENTS: int = 500

# Meta-transfer gate (registered): P(win) >= 0.55.
META_GATE: float = 0.55

# Daily-bar fetch bounds (reuse the run_xs_reversal layout / adjustment=raw).
BARS1D_DIR = Path("data/raw/sip/bars1d")
FETCH_START = datetime(2019, 11, 1, tzinfo=UTC)
FETCH_END = datetime(2026, 6, 2, tzinfo=UTC)
BARS1D_SCHEMA: dict[str, pl.DataType] = {
    "ts": pl.Int64, "open": pl.Float64, "high": pl.Float64, "low": pl.Float64,
    "close": pl.Float64, "volume": pl.Float64, "trade_count": pl.Int64, "vwap": pl.Float64,
}

# Meta feature columns carried on every event row (the M8 reliability set; the
# symbol one-hots are the ORIGINAL 5 names, so they are all-zero for every M11
# name — that all-zero one-hot IS the transfer test).
_META_NUMERIC = moc_meta.NUMERIC_FEATURES  # basis_bps, near_far_bps, ... , log_adv20
_META_ONEHOT = moc_meta.ONEHOT_FEATURES  # oh_NVDA .. oh_GOOGL

EVENT_SCHEMA: dict[str, pl.DataType] = {
    "session": pl.Utf8,
    "symbol": pl.Utf8,
    "sector": pl.Utf8,
    "side": pl.Int64,
    "near_price": pl.Float64,
    "ref_price": pl.Float64,
    "basis_bps": pl.Float64,
    "adv20_dollars": pl.Float64,
    "entry_px": pl.Float64,
    "exit_ts": pl.Int64,
    "exit_px": pl.Float64,
    "bar_close": pl.Float64,
    "net_bps": pl.Float64,
    # M8 meta reliability features (for the meta-transfer test):
    "norm_imb": pl.Float64,
    "paired_ratio": pl.Float64,
    "imb_growth_53": pl.Float64,
    "imb_growth_51": pl.Float64,
    "near_ref_bps": pl.Float64,
    "near_far_bps": pl.Float64,
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


def near_ref_at(noii_frame: pl.DataFrame | None, ts_signal: int) -> tuple[float, float] | None:
    """(near, ref) from the LAST NOII message at-or-before ``ts_signal`` with BOTH
    ``near_price`` > 0 AND ``ref_price`` > 0 (PIT); ``None`` if none.

    ref_price is the registered mid proxy for the near-vs-ref variant (DATA NOTE:
    no quote feed for these names). A message strictly after ``ts_signal`` can
    never govern; a message with near<=0 or ref<=0 is skipped (the indicative
    near price is 0 before ~15:55:00 ET).
    """
    if noii_frame is None or noii_frame.height == 0:
        return None
    prior = noii_frame.filter(
        (pl.col("ts") <= ts_signal)
        & (pl.col("near_price") > 0.0)
        & (pl.col("ref_price") > 0.0)
    )
    if prior.height == 0:
        return None
    row = prior.sort("ts").row(-1, named=True)
    return float(row["near_price"]), float(row["ref_price"])


def direction_of(near: float, ref: float) -> int:
    """Trade direction WITH the basis: +1 buy iff near > ref, -1 sell iff near <
    ref, 0 when they coincide (no tradable basis)."""
    if near > ref:
        return 1
    if near < ref:
        return -1
    return 0


def conservative_entry_px(ref: float, side: int) -> float:
    """Fixed conservative taker entry off the ref-price mid proxy.

    A BUY pays MORE than ref (crosses up half the conservative spread + slip); a
    SELL receives LESS than ref. entry_px = ref * (1 + side * TAKER_COST_BPS/1e4).
    """
    return ref * (1.0 + side * TAKER_COST_BPS / 1e4)


def net_bps_for(side: int, ref: float, entry_px: float, exit_close: float) -> float:
    """net_bps via ``decompose.plan_pnl`` (SEC/TAF 0.3 bp on the sell leg).

    Two synthetic Fills: entry at ``entry_px`` (mid = ref, no further spread/slip —
    the conservative cost is already baked into entry_px); exit AT ``exit_close``
    with mid == fill price (an auction clearing has zero spread/slip). This is the
    SAME decomposition ``replay_moc_event`` runs, so the number is identical in
    spirit to the validated pipeline: net == side*(close-entry_px)/entry_px*1e4 -
    fees, fees == 0.3 * (sell notional / entry notional).
    """
    entry_fill = Fill(
        ts=0, price=float(entry_px), qty_frac=1.0, leg="entry",
        decision_ts=0, mid_at_decision=float(ref), mid_at_action=float(ref), maker=False,
    )
    exit_fill = Fill(
        ts=0, price=float(exit_close), qty_frac=1.0, leg="moc",
        decision_ts=0, mid_at_decision=float(exit_close), mid_at_action=float(exit_close),
        maker=False,
    )
    return plan_pnl(side, (entry_fill,), (exit_fill,), SEC_TAF_SELL_BPS).net_bps


# --------------------------------------------------------------------------- daily bars


def fetch_missing_bars(
    settings: Settings, symbols: list[str], *, out_dir: Path = BARS1D_DIR
) -> dict[str, int]:
    """Fetch daily bars (1Day, adjustment=raw, SIP) for missing ``symbols`` into
    ``data/raw/sip/bars1d/{SYM}.parquet`` (reuse-if-present; idempotent).

    Returns {symbol: rows_written} for the ones actually fetched. Requires Alpaca
    creds; only reached on the real-run path (tests never call it).
    """
    from enginev51.data.alpaca_hist import AlpacaHist

    out_dir.mkdir(parents=True, exist_ok=True)
    todo = [s for s in symbols if not (out_dir / f"{s}.parquet").exists()]
    if not todo:
        return {}
    hist = AlpacaHist(settings)
    written: dict[str, int] = {}
    try:
        bars = hist.fetch_bars_multi(
            todo, FETCH_START, FETCH_END, feed="sip", timeframe="1Day", adjustment="raw",
        )
        for sym in todo:
            rows = bars.get(sym.upper(), [])
            df = (
                pl.DataFrame(rows, schema=BARS1D_SCHEMA) if rows
                else pl.DataFrame(schema=BARS1D_SCHEMA)
            ).sort("ts")
            df.write_parquet(out_dir / f"{sym}.parquet")
            written[sym] = df.height
    finally:
        hist.close()
    return written


def _daily_closes_pairs(symbol: str, *, bars_dir: Path = BARS1D_DIR) -> list[tuple[str, float]]:
    """Daily (session_iso, close) pairs from bars1d (UTC-date key, the convention
    ``auction_replay._daily_closes`` uses). Empty when the parquet is absent."""
    p = bars_dir / f"{symbol.upper()}.parquet"
    if not p.exists():
        return []
    df = pl.read_parquet(p)
    out: list[tuple[str, float]] = []
    for r in df.iter_rows(named=True):
        d = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
        out.append((d, float(r["close"])))
    return out


# --------------------------------------------------------------------------- coverage


def coverage(symbols: list[str], *, noii_dir: str | Path | None = None) -> dict:
    """How many of ``symbols`` have a NOII partition present (any month parquet).

    A trial is only EXECUTED when coverage is high enough (>= 24/28); otherwise the
    code + tests ship and the exact run command is printed for when data completes.
    """
    root = noii_root(noii_dir)
    present: list[str] = []
    missing: list[str] = []
    for s in symbols:
        d = root / s.upper()
        if d.exists() and any(d.glob("*.parquet")):
            present.append(s)
        else:
            missing.append(s)
    return {
        "n_total": len(symbols),
        "n_present": len(present),
        "present": sorted(present),
        "missing": sorted(missing),
        "fraction": round(len(present) / len(symbols), 4) if symbols else 0.0,
    }


# --------------------------------------------------------------------------- run


def _meta_feats(
    noii: pl.DataFrame, session_iso: str, adv: float | None, near: float, ref: float,
    sym: str, closes: list[tuple[str, float]],
) -> dict:
    """The M8 meta reliability features for one event (ref used as the mid proxy).

    When ADV20$ is unavailable (< 20 prior daily bars, the first ~month of the
    span) the ADV-dependent features are null — LightGBM treats them as missing;
    the classical firing above is unaffected (it needs only near/ref).
    """
    oh = symbol_onehot(sym)  # all-zero for M11 names (universe = original 5)
    vol20 = trailing_vol20(closes, session_iso)
    if adv is None or adv <= 0.0:
        base = {
            "norm_imb": None, "paired_ratio": None, "imb_growth_53": None,
            "imb_growth_51": None, "near_ref_bps": None, "near_far_bps": None,
            "msg_count": None, "log_adv20": None, "vol20": vol20,
        }
        return {**base, **oh}
    # Reuse the M6-FINAL feature builder with mid == ref (the near-vs-ref variant).
    feats = basis_pit_features(noii, session_iso, float(adv), near, ref)
    return {
        "norm_imb": feats["norm_imb"],
        "paired_ratio": feats["paired_ratio"],
        "imb_growth_53": feats["imb_growth_53"],
        "imb_growth_51": feats["imb_growth_51"],
        "near_ref_bps": feats["near_ref_bps"],
        "near_far_bps": feats["near_far_bps"],
        "msg_count": feats["msg_count"],
        "log_adv20": float(np.log(adv)),
        "vol20": vol20,
        **oh,
    }


def fire_near_ref_event(
    settings: Settings,
    sym: str,
    session_iso: str,
    noii: pl.DataFrame,
    *,
    closes_cache: dict[str, list[tuple[str, float]]],
    bars_dir: Path = BARS1D_DIR,
) -> tuple[dict | None, str | None]:
    """Fire the frozen near-vs-ref rule for ONE (sym, session) NOII frame.

    Pure translation of the former ``run_m11`` inner body (near_ref_at ->
    basis_bps_of -> direction_of -> FIRE gate -> cross_price_for(None) raw daily
    close -> conservative_entry_px -> net_bps_for -> _meta_feats). Returns
    ``(row, None)`` on a fire or ``(None, reason)`` where ``reason`` is one of
    ``{'no_near_ref','zero_basis','inactive','no_close'}`` — the exact funnel keys
    the thin ``run_m11`` loop increments. ``noii`` is assumed non-empty (the loop
    handles the partition/empty skips).

    ``closes_cache`` is the caller's mutable per-symbol daily-close cache. The lazy
    ``_daily_closes_pairs`` load lives HERE, AFTER every skip gate — exactly where
    the pre-refactor inline body placed it — so a symbol with non-empty NOII that
    never fires never triggers a bars read (ZERO behavior change; ``bars_dir`` is
    the raw-lake root for that load). Guarded by the reproduction test.

    Extracted 2026-07-23 for M22 Cell B reuse (M3_REGISTRATION.md § M22): the
    catalyst-conditioned broad-12 cell runs THIS exact apparatus behind a day0
    whitelist. UNIVERSE_28, SECTORS, all M11 constants and report paths untouched.
    """
    signal_ts = et_ns(session_iso, *SIGNAL_HMS)
    nr = near_ref_at(noii, signal_ts)
    if nr is None:
        return None, "no_near_ref"
    near, ref = nr
    basis = basis_bps_of(near, ref)  # 1e4 * (near - ref) / ref
    side = direction_of(near, ref)
    if side == 0:
        return None, "zero_basis"
    if abs(basis) < FIRE_BASIS_BPS:
        return None, "inactive"

    # EXIT: official daily close (no tick tape for these names, so
    # cross_price_for falls straight through to the daily close).
    cross = cross_price_for(sym, session_iso, None)
    if cross is None:
        return None, "no_close"
    exit_ts, exit_close, _sz = cross

    entry_px = conservative_entry_px(ref, side)
    net = net_bps_for(side, ref, entry_px, exit_close)

    adv = adv20_dollars(settings, sym, session_iso)
    # Lazy daily-close load (post-gate; mirrors the pre-refactor placement so a
    # never-firing symbol never reads bars).
    if sym not in closes_cache:
        closes_cache[sym] = _daily_closes_pairs(sym, bars_dir=bars_dir)
    feats = _meta_feats(noii, session_iso, adv, near, ref, sym, closes_cache[sym])

    row = {
        "session": session_iso,
        "symbol": sym,
        "sector": SECTOR_OF.get(sym, "Unknown"),
        "side": side,
        "near_price": float(near),
        "ref_price": float(ref),
        "basis_bps": float(basis),
        "adv20_dollars": float(adv) if adv is not None else None,
        "entry_px": float(entry_px),
        "exit_ts": int(exit_ts),
        "exit_px": float(exit_close),
        "bar_close": float(exit_close),
        "net_bps": float(net),
        **feats,
    }
    return row, None


def run_m11(
    settings: Settings,
    *,
    symbols: list[str],
    start: date,
    end: date,
    noii_dir: str | Path | None = None,
    bars_dir: Path = BARS1D_DIR,
) -> tuple[pl.DataFrame, dict]:
    """Execute the frozen near-vs-ref rule over [start, end] sessions on ``symbols``.

    One row per (symbol, session) that FIRES (|basis_bps| >= 10). Returns
    ``(events_df, stats)``; the funnel counters record every skipped session.
    Thin loop over ``fire_near_ref_event`` (the per-(sym, session) body).
    """
    assert_before_holdout(end)
    symbols = [s.strip().upper() for s in symbols]

    counts = {
        "no_noii_partition": 0,
        "no_noii_msgs": 0,
        "no_near_ref": 0,   # no message with near>0 AND ref>0 at-or-before 15:55:10
        "zero_basis": 0,    # near == ref exactly
        "inactive": 0,      # |basis| < 10
        "no_close": 0,      # no official daily close for the exit
        "fired": 0,
    }
    closes_cache: dict[str, list[tuple[str, float]]] = {}
    rows: list[dict] = []

    sessions = [d for d in calendar.trading_days(start, end) if d < HOLDOUT_START]
    for sd in sessions:
        session_iso = sd.isoformat()
        for sym in symbols:
            noii = load_noii_session(sym, session_iso, out_dir=noii_dir)
            if noii is None:
                counts["no_noii_partition"] += 1
                continue
            if noii.height == 0:
                counts["no_noii_msgs"] += 1
                continue
            row, reason = fire_near_ref_event(
                settings, sym, session_iso, noii,
                closes_cache=closes_cache, bars_dir=bars_dir,
            )
            if reason is not None:
                counts[reason] += 1
                continue
            rows.append(row)
            counts["fired"] += 1

    df = (
        pl.DataFrame(rows, schema=EVENT_SCHEMA, orient="row")
        if rows
        else pl.DataFrame(schema=EVENT_SCHEMA)
    )
    stats = {
        "symbols": symbols,
        "sessions_in_range": len(sessions),
        "counts": counts,
        "coverage": coverage(symbols, noii_dir=noii_dir),
    }
    return df, stats


# --------------------------------------------------------------------------- CI helpers


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


def sector_prong(df: pl.DataFrame) -> dict:
    """Per-sector point estimate + the registered majority-of-sectors prong: how
    many represented sectors have a positive net_bps point estimate, and whether
    that is a strict majority of the sectors present."""
    per_sector: dict[str, float | None] = {}
    n_pos = 0
    sectors = sorted(df["sector"].unique().to_list()) if df.height else []
    for sec in sectors:
        sub = df.filter(pl.col("sector") == sec)
        pe = float(sub["net_bps"].mean()) if sub.height else float("nan")
        per_sector[sec] = round(pe, 3) if sub.height else None
        if sub.height and pe > 0:
            n_pos += 1
    n_sectors = len(sectors)
    return {
        "n_sectors_represented": n_sectors,
        "n_sectors_net_positive": n_pos,
        "per_sector_point_estimate": per_sector,
        "majority_of_sectors_positive": bool(n_sectors and n_pos * 2 > n_sectors),
    }


def _hit_rate(df: pl.DataFrame) -> float:
    if df.height == 0:
        return float("nan")
    return float((df["net_bps"] > 0.0).cast(pl.Float64).mean())


# --------------------------------------------------------------------------- meta transfer


def meta_transfer(
    events: pl.DataFrame, five_name_events_path: str | Path
) -> dict:
    """Train the M8 meta model on ONLY the original 5 names (frozen), apply it to
    the 28-name candidates, and report whether gating by P(win) >= 0.55 improves
    the 28-name hit rate.

    Trains a SINGLE booster on the full 5-name |basis|>=10 candidate set (no walk-
    forward: the 28 names are an entirely disjoint universe, so every 5-name row is
    legitimately "in-sample for the source, out-of-sample for the target"). Returns
    a summary dict; ``available=False`` if the 5-name events or the 28-name
    candidates are missing so the caller can degrade gracefully.
    """
    path = Path(five_name_events_path)
    out: dict = {"available": False, "gate": META_GATE, "five_name_events": str(path)}
    if not path.exists() or events.height == 0:
        out["reason"] = "no 5-name events file" if not path.exists() else "no 28-name events"
        return out

    five = pl.read_parquet(path)
    meta5 = moc_meta.build_meta_frame(five)  # candidates |basis|>=10, y=(net_bps>0); asserts < holdout
    if meta5.height == 0:
        out["reason"] = "no 5-name candidates"
        return out
    booster = moc_meta.train_fold(meta5)

    cand = events.filter(
        (pl.col("basis_bps").abs() >= moc_meta.CANDIDATE_BASIS_BPS)
        & pl.col("net_bps").is_not_null()
    )
    if cand.height == 0:
        out["reason"] = "no 28-name candidates"
        return out
    moc_meta.assert_features_present(cand)
    p_win = moc_meta.predict_pwin(booster, cand)
    cand = cand.with_columns(pl.Series(moc_meta.PRED_COL, p_win))
    gated = cand.filter(pl.col(moc_meta.PRED_COL) >= META_GATE)

    ung_hit = _hit_rate(cand)
    g_hit = _hit_rate(gated)
    ung = _ci(cand)
    g = _ci(gated)
    out.update({
        "available": True,
        "n_5name_train_candidates": meta5.height,
        "n_28name_candidates": cand.height,
        "n_gated": gated.height,
        "ungated_hit_rate": round(ung_hit, 4),
        "gated_hit_rate": round(g_hit, 4) if gated.height else None,
        "hit_rate_improved": bool(gated.height and g_hit > ung_hit),
        "ungated_net_bps_mean": round(ung[0], 3),
        "gated_net_bps_mean": round(g[0], 3) if gated.height else None,
        "ungated_ci_lo": round(ung[1], 3),
        "gated_ci_lo": round(g[1], 3) if gated.height else None,
        "mean_p_win": round(float(np.mean(p_win)), 4),
    })
    return out


# --------------------------------------------------------------------------- ground truth


def stratified_ground_truth(df: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """<= k stratified events (biggest winners, biggest losers, largest |basis|)
    laid out near/ref vs the daily close (PROTOCOL v6.1 sanity).

    entry_cost_bps: realized |entry_px - ref|/ref*1e4 — must equal the fixed
    conservative TAKER_COST_BPS (2.5). ref_vs_close_bps: how far ref sat from the
    official close (the move the trade actually captured toward)."""
    schema = {
        "session": pl.Utf8, "symbol": pl.Utf8, "sector": pl.Utf8, "side": pl.Int64,
        "near_price": pl.Float64, "ref_price": pl.Float64, "basis_bps": pl.Float64,
        "entry_px": pl.Float64, "entry_cost_bps": pl.Float64, "bar_close": pl.Float64,
        "ref_vs_close_bps": pl.Float64, "net_bps": pl.Float64,
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
        (pl.col("side") * (pl.col("entry_px") - pl.col("ref_price"))
         / pl.col("ref_price") * 1e4).alias("entry_cost_bps"),
        pl.when(pl.col("bar_close").is_not_null() & (pl.col("bar_close") > 0))
        .then((pl.col("bar_close") - pl.col("ref_price")) / pl.col("ref_price") * 1e4)
        .otherwise(None).alias("ref_vs_close_bps"),
    ).select(list(schema))


# --------------------------------------------------------------------------- report


def build_report_md(
    trial_id: str, events: pl.DataFrame, stats: dict, meta: dict, seed: int,
) -> str:
    years = sorted({s[:4] for s in events["session"].to_list()}) if events.height else []
    pooled = _ci(events)
    _m, lo, _hi, n, _ns = pooled
    md: list[str] = [
        f"# M11 cross-sectional OOS generalization report — {trial_id}",
        "",
        "Family `moc_imbalance_v1`, M11 cell (registered 2026-07-17 BEFORE download). "
        "The FROZEN near-vs-REF rule (registration's verified equivalent to the "
        "validated near-vs-mid rule: corr 0.9999) applied to 28 Nasdaq names it was "
        "NEVER fit on. PURE OUT-OF-SAMPLE: zero parameter changes, not a search. "
        "NO ledger writes; NO pass/fail verdict (the orchestrator owns the verdict).",
        "",
        "Signal at 15:55:10 ET: near, ref = last NOII message with near>0 AND ref>0 "
        "(ref_price is the mid proxy — no quote feed); basis_bps = 1e4*(near-ref)/ref; "
        f"FIRE iff |basis| >= {FIRE_BASIS_BPS:.0f}; side = sign(near-ref). ENTRY = a "
        f"CONSERVATIVE fixed taker cost: entry_px = ref*(1 + side*{TAKER_COST_BPS:.1f}bps) "
        f"({HALF_SPREAD_BPS:.0f}bps half-spread + {SLIP_BPS:.1f}bp slip). The "
        f"{HALF_SPREAD_BPS:.0f}bps half-spread is WIDER than the ~1bp these liquid "
        "names run, so this UNDERSTATES the edge vs the bbo-1s fills on the original "
        "5. EXIT = official daily close. net via decompose.plan_pnl (SEC/TAF 0.3bp "
        "on the sell leg) — identical in spirit to the validated pipeline.",
        "",
        f"seed={seed}    universe={len(stats['symbols'])} names    "
        f"sessions in range (< holdout {HOLDOUT_START.isoformat()}): "
        f"{stats['sessions_in_range']}",
        f"Events fired (rows): {events.height}    years: {years}",
        f"Splits present: "
        f"{sorted(set(split_of(s) for s in events['session'].unique())) if events.height else []}",
        "",
        "## 0. NOII coverage (fraction of the 28 names with a partition present)",
        "```",
        json.dumps(stats["coverage"], indent=2, default=str),
        "```",
        "",
        "## 1. Event funnel / skipped-session counters",
        "```",
        json.dumps(stats["counts"], indent=2, default=str),
        "```",
        "",
        "## 2. POOLED classical net_bps — day-clustered CI on the 28-name pool (pure OOS)",
        "",
        f"- Pooled (day-clustered): {_fmt_ci(pooled)}",
        f"- Pooled CI-lower > 0 (registered pass prong): {bool(n and lo > 0)}",
        "",
        "## 3. Per-symbol net_bps day-clustered CIs",
        "",
        _ascii(_grouped_ci_table(events, "symbol", "symbol")),
        "",
        "## 4. Per-SECTOR net_bps day-clustered CIs + majority-of-sectors prong",
        "",
        _ascii(_grouped_ci_table(events, "sector", "sector")),
        "",
        "```",
        json.dumps(sector_prong(events), indent=2, default=str),
        "```",
        "",
        "## 5. Event count vs registered threshold",
        "```",
        json.dumps({
            "n_events": events.height,
            "min_required": MIN_EVENTS,
            "meets_ge_500": bool(events.height >= MIN_EVENTS),
        }, indent=2, default=str),
        "```",
        "",
        "## 6. By-year net_bps day-clustered CIs",
        "",
        _ascii(_grouped_ci_table(_year_col(events), "year", "year")),
        "",
        "## 7. META-TRANSFER — M8 meta model trained ONLY on the original 5 (frozen)",
        "",
        "The M8 LightGBM reliability model is trained on the 5-name |basis|>=10 "
        "candidate universe (frozen; symbol one-hots are the 5 originals, all-zero "
        "for every M11 name) and applied to the 28-name candidates. Does gating by "
        f"the 5-name-trained P(win) >= {META_GATE} improve the 28-name hit rate? "
        "This tests whether the meta learned a TRANSFERABLE reliability signal or "
        "overfit to 5 names.",
        "```",
        json.dumps(meta, indent=2, default=str),
        "```",
        "",
        "## 8. PROTOCOL v6.1 ground-truthing — 10 stratified events (near/ref vs daily close)",
        "",
        "entry_cost_bps: realized signed entry cost vs ref (must equal the fixed "
        f"{TAKER_COST_BPS:.1f}bps conservative taker cost). ref_vs_close_bps: how far "
        "ref sat from the official close (the move captured toward). net_bps: the "
        "realized decomposed pnl.",
        "",
        _ascii(stratified_ground_truth(events)),
        "",
    ]
    return "\n".join(md)


def write_outputs(
    out_dir: Path, trial_id: str, events: pl.DataFrame, report_md: str,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    events_path = out_dir / "events.parquet"
    report_path = out_dir / "report.md"
    events.write_parquet(events_path)
    report_path.write_text(report_md, encoding="utf-8")
    return events_path, report_path


# --------------------------------------------------------------------------- CLI


DEFAULT_FIVE_EVENTS = "research/experiments/M6-FINAL-basis/events.parquet"


@click.command()
@click.option("--trial-id", default="M11-oos-28", help="Experiment id -> research/experiments/<id>/.")
@click.option("--start", default="2020-01-02", help="First session (ISO date), inclusive.")
@click.option("--end", default="2026-05-31", help="Last session (ISO date), inclusive; < holdout.")
@click.option("--seed", default=7, type=int, help="CI bootstrap seed echo.")
@click.option("--noii-dir", default=None, help="NOII lake root (default data/raw/noii).")
@click.option("--five-name-events", default=DEFAULT_FIVE_EVENTS,
              help="M6-FINAL 5-name events.parquet for the frozen meta-transfer model.")
@click.option("--fetch-bars/--no-fetch-bars", default=True,
              help="Fetch missing daily bars (1Day raw SIP) for the 28 names before running.")
@click.option("--min-coverage", default=24, type=int,
              help="Minimum NOII-present names to EXECUTE (else print the run command).")
def main(
    trial_id: str,
    start: str,
    end: str,
    seed: int,
    noii_dir: str | None,
    five_name_events: str,
    fetch_bars: bool,
    min_coverage: int,
) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    settings = get_settings()
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    assert_before_holdout(end_d)

    symbols = list(UNIVERSE_28)
    cov = coverage(symbols, noii_dir=noii_dir)
    click.echo(f"NOII coverage: {cov['n_present']}/{cov['n_total']} present  "
               f"missing={cov['missing']}")

    if cov["n_present"] < min_coverage:
        cmd = (
            f"uv run python -m enginev51.apps.run_m11 --trial-id {trial_id} "
            f"--start {start} --end {end} --seed {seed}"
        )
        click.echo(
            f"coverage {cov['n_present']}/{cov['n_total']} < {min_coverage} - NOT running "
            "the full trial (NOII partitions incomplete). Ship code + tests; download "
            "the remaining NOII names, then run:\n  " + cmd
        )
        return

    if fetch_bars:
        written = fetch_missing_bars(settings, symbols)
        if written:
            click.echo(f"fetched daily bars: {json.dumps(written, default=str)}")

    t0 = time.time()
    events, stats = run_m11(
        settings, symbols=symbols, start=start_d, end=end_d, noii_dir=noii_dir,
    )
    meta = meta_transfer(events, five_name_events)
    report_md = build_report_md(trial_id, events, stats, meta, seed)
    wall_s = time.time() - t0

    out_dir = experiments_dir() / trial_id
    events_path, report_path = write_outputs(out_dir, trial_id, events, report_md)

    click.echo(f"trial: {trial_id}  {start}..{end}  seed={seed}")
    click.echo(f"event funnel: {json.dumps(stats['counts'], default=str)}")
    click.echo("")
    click.echo(f"POOLED net_bps: {_fmt_ci(_ci(events))}")
    click.echo(f"events: {events.height}  (>= {MIN_EVENTS}: {events.height >= MIN_EVENTS})")
    click.echo(f"sectors net-positive: {json.dumps(sector_prong(events), default=str)}")
    click.echo(f"meta-transfer: {json.dumps(meta, default=str)}")
    click.echo(f"events:  {events_path}")
    click.echo(f"report:  {report_path}")
    click.echo(f"wall: {wall_s:.1f}s")


if __name__ == "__main__":
    main()
