"""M24 opening-auction dislocation fade harness (family ``open_auction_fade_v1``).

Registered 2026-07-23 (M3_REGISTRATION.md, section "M24 -- opening-auction
dislocation fade (auction sandwich)") BEFORE any economics exist. Frozen design:
``research/experiments/M24-open-fade/DESIGN.md`` (the orchestrator's rulings D1-D6
mirror the registration). Nothing here may be tuned; the family has ONE registered
look, owned by the orchestrator, and the tests are synthetic-only -- the real-data
run is the orchestrator's alone.

The one auction x dislocation intersection never tested: FADE the opening cross's
own indicative divergence, held to the day's OTHER single print. Decision frozen at
09:28:30 ET on the opening NOII's near-vs-ref basis; direction AGAINST the basis
(basis > 0 => SELL SHORT at the official open, basis < 0 => BUY); exit = the same
session's official CLOSE print. Two NESTED gated cells, disclosed as such:

* t25 = |basis_open| >= 25 bps (the primary cell + the ADIA panel).
* t50 = |basis_open| >= 50 bps (t50 SUBSET of t25 -- one frame, two cell stats).

Both legs price AT the official prints from RAW bars1d (L2): an adjusted open or
close would corrupt same-day open->close on any ex-div date (landmine L2). The only
exit is the official close -- this module NEVER computes norm_imb or any timed
intraday exit (the M6b fence; the leg most suspect in M6b's design). PSR/MinTRL/
sr_native are IMPORTED from ``research_screens.sizing_shadow`` (already golden-
tested; never reimplemented). The one-look gate is hard-anchored to the canonical
experiments dir (M22 B1 lesson: no relocatable out-dir).
"""

from __future__ import annotations

import json
import math
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import polars as pl
import structlog

from enginev51.apps import run_m11
from enginev51.apps.run_m11 import SEC_TAF_SELL_BPS as M11_SEC_TAF_SELL_BPS
from enginev51.backtest import stress
from enginev51.config import Settings
from enginev51.data.noii import et_ns, noii_root, partition_path
from enginev51.protocol import (
    HOLDOUT_START,
    experiments_dir,
    ledger_append,
    refuse_end_on_or_after_holdout,
)

# ADIA Lab No.19 statistics: IMPORTED from the M23 sizing-shadow module (golden-
# tested there). NEVER reimplemented here -- identity-checked by test 12.
from enginev51.research_screens.sizing_shadow import (
    min_trl,
    psr,
    sample_moments,
    sr_native,
)

log = structlog.get_logger(__name__)

# --------------------------------------------------------------------------- #
# M24 registration (2026-07-23, M3_REGISTRATION.md section M24). Do not tune.
# --------------------------------------------------------------------------- #
SIGNAL_HMS = (9, 28, 30)          # decision instant ET (D1: ts <= 09:28:30.000000)
OPEN_WINDOW_ET = (9, 0, 0)        # morning NOII read window start (ET)
OPEN_WINDOW_END_ET = (9, 30, 30)  # morning NOII read window end (ET)
THRESH_T25 = 25.0                 # |basis_open| >= 25 bps (gated cell t25)
THRESH_T50 = 50.0                 # nested gated cell t50 (t50 subset of t25)
START = date(2020, 1, 2)
END = date(2026, 5, 31)           # < holdout; assert_before_holdout
# Sell-side SEC/TAF fee, pinned EQUAL to run_m11's constant (M11 convention;
# test 7 asserts the equality so a drift in either module fails).
SEC_TAF_SELL_BPS: float = 0.3
CELL_T25_MIN_FIRED, CELL_T25_MIN_SESSIONS = 300, 150
UNDERPOWERED_BELOW = 150
MEAN_FLOOR_BPS = 2.0              # PASS floor (>= ~4x fee floor)
OUT_SUBDIR = "M24-open-fade"

# UNIVERSE pin (2026-07-23 scout of data/raw/noii/): the 33 NOII-covered names, an
# EXPLICIT tuple -- a lake change must FAIL test 2, never silently move the universe.
UNIVERSE: tuple[str, ...] = tuple(sorted((
    "AAPL", "ADBE", "AMAT", "AMD", "AMGN", "AVGO", "BKNG", "CMCSA", "COST", "CSCO",
    "GILD", "GOOGL", "HON", "INTC", "INTU", "ISRG", "KLAC", "LRCX", "MDLZ", "META",
    "MRVL", "MSFT", "MU", "NFLX", "NVDA", "PEP", "PLTR", "QCOM", "SBUX", "TMUS",
    "TSLA", "TXN", "VRTX",
)))

# The champion 5 (M6-FINAL universe) vs the broad 28 -- REPORTED separately, NEVER
# gated (L9-analog: pooled gating disclosed).
CHAMPION_5: tuple[str, ...] = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")

# Raw bars1d root (L2) -- the same raw lake run_m11 reads (do NOT modify run_m11).
BARS1D_DIR = run_m11.BARS1D_DIR

# ADIA panel / CI conventions.
BOOK_NOTIONAL = 10_000.0  # $10k equal notional per fired event (D4)
SR0 = 0.0                 # SR0 = 0 everywhere in this panel
ALPHA = 0.05              # MinTRL / z_{1-alpha}
_CI_SEED = 7              # repo reproducibility constant
_CI_N_BOOT = 2000
RHO_UNDERPOWERED_BELOW = 30  # D5: n_overlap < 30 => UNDERPOWERED-rho flag

# Champion dev daily stream (M8-meta-v1 OOS parquet; read-only, report-only rho).
CHAMPION_OOS_PARQUET = "research/experiments/M8-meta-v1/oos_predictions.parquet"

_ET_TZ = "America/New_York"

# Event frame schema -- one row per fired (|basis_open| >= 25) event.
EVENT_SCHEMA: dict[str, pl.DataType] = {
    "session": pl.Utf8,
    "symbol": pl.Utf8,
    "basis_open_bps": pl.Float64,
    "side": pl.Int64,
    "open_px": pl.Float64,
    "close_px": pl.Float64,
    "gross_bps": pl.Float64,
    "net_bps": pl.Float64,
    "overnight_gap_bps": pl.Float64,   # report-only strata input (null when no prior close)
    "imb_side_agrees": pl.Boolean,     # report-only strata input
    "imbalance_shares": pl.Float64,
    "is_t50": pl.Boolean,              # nested flag: |basis_open| >= 50
}


# --------------------------------------------------------------------------- guard


def assert_before_holdout(end: date) -> None:
    """Refuse any run reaching the sealed holdout boundary (PROTOCOL v6 section 1).

    The registered span ends 2026-05-31 (< the 2026-06-01 seal); this guard is
    enforced in BOTH the builder and the CLI so the seal can never be silently
    crossed (landmine seal). Raises SealViolation — never a bare assert, which
    ``python -O`` would strip (code review B7/J2)."""
    refuse_end_on_or_after_holdout(end)


# --------------------------------------------------------------------------- paths


def canonical_out_dir() -> Path:
    """The ONE canonical M24 output/look-state directory. The one-look gate is
    anchored here so it can never be relocated (a fresh out-dir would otherwise find
    no look_state.json and defeat the single-registered-look guarantee); the CLI
    passes no directory and always resolves to this path (reviewer B1)."""
    return experiments_dir() / OUT_SUBDIR


def out_dir_for(out_dir: str | Path | None = None) -> Path:
    """Resolve the M24 output directory. ``out_dir`` exists ONLY for hermetic tests
    (a tmp path); the CLI never supplies it, so the default IS ``canonical_out_dir``
    and the look state is unrelocatable in production."""
    p = Path(out_dir) if out_dir is not None else canonical_out_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p


def look_state_path(out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / "look_state.json"


# --------------------------------------------------------------------------- time


def _months(start: date, end: date) -> list[str]:
    """Inclusive 'YYYY-MM' month keys spanning [start, end]."""
    y, m = start.year, start.month
    out: list[str] = []
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def _et_session_expr() -> pl.Expr:
    """UTC-ns ``ts`` -> ET calendar-date string via America/New_York (zoneinfo),
    NEVER a fixed UTC-4 offset (a naive offset breaks EST sessions -- reviewer
    attack 1; DST-boundary coverage in test 3)."""
    return (
        pl.from_epoch(pl.col("ts"), time_unit="ns")
        .dt.replace_time_zone("UTC")
        .dt.convert_time_zone(_ET_TZ)
    )


# --------------------------------------------------------------------------- loaders


def load_open_noii(
    sym: str, month: str, *, noii_dir: str | Path | None = None
) -> pl.DataFrame | None:
    """Opening-cross NOII messages for one (symbol, month), morning window only.

    Reads the monthly partition DIRECTLY (module-local root ``data/raw/noii``; the
    noii/bbo1s bypass convention -- ``load_noii_session`` filters to the 15:45-16:00
    CLOSING window, which is why we read the raw partition here) and keeps only the
    ET window [09:00:00, 09:30:30]. UTC-ns -> ET via America/New_York. Returns the
    NOII_SCHEMA columns plus a derived ``session`` (ET date) column; ``None`` when
    the partition is absent (so callers distinguish "no data" from "empty window")."""
    root = noii_root(noii_dir)
    path = partition_path(root, sym, month)
    if not path.exists():
        return None
    df = pl.read_parquet(path)
    if df.height == 0:
        return df.with_columns(pl.lit(None, dtype=pl.Utf8).alias("session"))
    et = _et_session_expr()
    # cast to Int64 BEFORE the arithmetic: dt.hour()/minute()/second() are Int8 and
    # 9*3600 overflows an Int8 (landmine: silent wraparound dropped the whole window).
    tod = (
        et.dt.hour().cast(pl.Int64) * 3600
        + et.dt.minute().cast(pl.Int64) * 60
        + et.dt.second().cast(pl.Int64)
    )
    lo = OPEN_WINDOW_ET[0] * 3600 + OPEN_WINDOW_ET[1] * 60 + OPEN_WINDOW_ET[2]
    hi = OPEN_WINDOW_END_ET[0] * 3600 + OPEN_WINDOW_END_ET[1] * 60 + OPEN_WINDOW_END_ET[2]
    df = df.with_columns(
        et.dt.strftime("%Y-%m-%d").alias("session"),
        tod.alias("_tod_s"),
    )
    return df.filter((pl.col("_tod_s") >= lo) & (pl.col("_tod_s") <= hi)).drop("_tod_s").sort("ts")


def load_daily_bars(sym: str, *, bars_dir: Path = BARS1D_DIR) -> pl.DataFrame:
    """Raw bars1d open+close (L2) for one symbol, keyed by UTC-date session.

    Read like ``run_m11._daily_closes_pairs`` (UTC-date key, raw lake) but keep BOTH
    the open and close columns -- do NOT modify run_m11. Returns a frame
    (session, open_px, close_px) sorted by session, empty when the parquet is
    absent. RAW both legs (landmine L2: an adjusted open/close corrupts same-day
    open->close on any ex-div date)."""
    schema = {"session": pl.Utf8, "open_px": pl.Float64, "close_px": pl.Float64}
    p = Path(bars_dir) / f"{sym.upper()}.parquet"
    if not p.exists():
        return pl.DataFrame(schema=schema)
    df = pl.read_parquet(p)
    rows: list[dict] = []
    for r in df.iter_rows(named=True):
        d = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
        rows.append({"session": d, "open_px": float(r["open"]), "close_px": float(r["close"])})
    if not rows:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame(rows, schema=schema, orient="row").sort("session")


# --------------------------------------------------------------------------- signal


def open_basis_at(msgs: pl.DataFrame | None, session_iso: str) -> tuple[dict | None, str | None]:
    """The M24 opening-basis signal for one session, PIT at 09:28:30 ET.

    The LAST NOII message at-or-before 09:28:30 ET (D1: ts <= 09:28:30.000000 ET
    inclusive) with near_price > 0 AND ref_price > 0 governs:
    ``basis_open_bps = 1e4*(near-ref)/ref``. Returns ``(sig, None)`` where ``sig`` =
    {basis_open_bps, near, ref, side_flag, imbalance_shares, ts}, or ``(None, reason)``:

    * ``no_msgs``   -- no message at-or-before the instant at all.
    * ``no_near_ref`` -- messages exist but none with near>0 AND ref>0.
    * ``zero_basis`` -- a qualifying message found but near == ref exactly (basis==0)."""
    if msgs is None or msgs.height == 0:
        return None, "no_msgs"
    signal_ts = et_ns(session_iso, *SIGNAL_HMS)
    prior = msgs.filter(pl.col("ts") <= signal_ts)
    if prior.height == 0:
        return None, "no_msgs"
    qual = prior.filter((pl.col("near_price") > 0.0) & (pl.col("ref_price") > 0.0))
    if qual.height == 0:
        return None, "no_near_ref"
    row = qual.sort("ts").row(-1, named=True)
    near = float(row["near_price"])
    ref = float(row["ref_price"])
    basis = 1e4 * (near - ref) / ref
    if basis == 0.0:
        return None, "zero_basis"
    return {
        "basis_open_bps": basis,
        "near": near,
        "ref": ref,
        "side_flag": row["side"],
        "imbalance_shares": float(row["imbalance_shares"] or 0.0),
        "ts": int(row["ts"]),
    }, None


def _imb_sign(side_flag: str | None) -> int:
    """+1 buy-side ('B'), -1 sell-side ('A'/'S'), 0 otherwise (Databento NOII side)."""
    if side_flag == "B":
        return 1
    if side_flag in ("A", "S"):
        return -1
    return 0


# --------------------------------------------------------------------------- fade kernel


def fade_event(
    sig: dict, open_px: float, close_px: float, *, prev_close: float | None = None
) -> dict:
    """The frozen fade round trip for ONE fired (sym, session) event.

    Direction is AGAINST the basis (the frozen fade): ``side = -1 if basis > 0 else
    +1`` (a WITH mutation flips the sign and fails test 5). Both legs price at the
    official prints (raw bars1d):

        gross_bps = side * (close_px/open_px - 1) * 1e4
        net_bps   = gross_bps - M11_SEC_TAF_SELL_BPS   (sell-side SEC/TAF, once per RT)

    ``sig`` carries ``basis_open_bps`` and (added by ``build_events``) ``symbol`` /
    ``session``; ``prev_close`` is the immediately-preceding raw close for the gap
    stratum. Report-only strata inputs are emitted alongside:

    * overnight_gap_bps = (open_px/prev_close - 1)*1e4 (None when no prior close ->
      the strata row is null but the EVENT is kept, D2).
    * imb_side_agrees  = the NOII side flag agrees with the basis sign (B & basis>0,
      or A/S & basis<0).
    """
    basis = float(sig["basis_open_bps"])
    side = -1 if basis > 0.0 else 1
    gross_bps = side * (close_px / open_px - 1.0) * 1e4
    # Subtract the IMPORTED M11 fee symbol (the M11 convention is the source of
    # truth); the local SEC_TAF_SELL_BPS constant is kept solely for the pin test
    # (test 7 asserts local == M11 == 0.3), so a drift in either module fails.
    net_bps = gross_bps - M11_SEC_TAF_SELL_BPS

    if prev_close is not None and prev_close > 0.0:
        overnight_gap_bps: float | None = (open_px / prev_close - 1.0) * 1e4
    else:
        overnight_gap_bps = None

    basis_sign = 1 if basis > 0.0 else (-1 if basis < 0.0 else 0)
    imb_side_agrees = bool(basis_sign != 0 and _imb_sign(sig.get("side_flag")) == basis_sign)

    return {
        "session": sig.get("session"),
        "symbol": sig.get("symbol"),
        "basis_open_bps": basis,
        "side": side,
        "open_px": float(open_px),
        "close_px": float(close_px),
        "gross_bps": float(gross_bps),
        "net_bps": float(net_bps),
        "overnight_gap_bps": overnight_gap_bps,
        "imb_side_agrees": imb_side_agrees,
        "imbalance_shares": float(sig.get("imbalance_shares", 0.0) or 0.0),
        "is_t50": bool(abs(basis) >= THRESH_T50),
    }


# --------------------------------------------------------------------------- builder


def _coverage(universe: tuple[str, ...], *, noii_dir: str | Path | None = None) -> dict:
    """How many universe names have a NOII partition present (funnel-reported)."""
    root = noii_root(noii_dir)
    present = [s for s in universe if (root / s.upper()).exists()
               and any((root / s.upper()).glob("*.parquet"))]
    return {
        "n_total": len(universe),
        "n_present": len(present),
        "present": sorted(present),
        "missing": sorted(set(universe) - set(present)),
    }


def build_events(
    settings: Settings,
    *,
    start: date = START,
    end: date = END,
    universe: tuple[str, ...] = UNIVERSE,
    noii_dir: str | Path | None = None,
    bars_dir: Path = BARS1D_DIR,
) -> tuple[pl.DataFrame, dict]:
    """Build the fired-event frame + the coverage/skip funnel over [start, end].

    Per (sym, month, session): opening-basis signal -> raw bars1d open/close lookup
    (missing/non-positive bar -> skip reason ``no_bar``, never imputed, D3) -> the
    |basis| >= 25 fire gate -> ``fade_event``. Every examined (sym, session) lands in
    EXACTLY one funnel bucket, so ``sum(counts) == candidates`` (test 14). The
    returned frame carries ALL fired (t25) rows plus the nested ``is_t50`` flag; the
    t50 cell is a SUBSET of this one frame (never a re-scan)."""
    assert_before_holdout(end)
    start_iso, end_iso, hold_iso = start.isoformat(), end.isoformat(), HOLDOUT_START.isoformat()
    months = _months(start, end)

    counts = {
        "no_msgs": 0,
        "no_near_ref": 0,
        "zero_basis": 0,
        "no_bar": 0,
        "below_t25": 0,
        "fired_t25": 0,
    }
    candidates = 0
    rows: list[dict] = []

    for sym in universe:
        bars = load_daily_bars(sym, bars_dir=bars_dir)
        # session -> (open, close); prev_close = the immediately-preceding raw close
        # in this symbol's OWN bars frame (D2: calendar-gap agnostic, off-by-one is
        # reviewer attack 3).
        bar_by_session: dict[str, tuple[float, float, float | None]] = {}
        prev_c: float | None = None
        for b in bars.iter_rows(named=True):
            bar_by_session[b["session"]] = (b["open_px"], b["close_px"], prev_c)
            prev_c = b["close_px"]

        for month in months:
            msgs = load_open_noii(sym, month, noii_dir=noii_dir)
            if msgs is None or msgs.height == 0:
                continue
            sessions = sorted(
                s for s in msgs["session"].unique().to_list()
                if s is not None and start_iso <= s <= end_iso and s < hold_iso
            )
            for session_iso in sessions:
                candidates += 1
                sess_msgs = msgs.filter(pl.col("session") == session_iso)
                sig, reason = open_basis_at(sess_msgs, session_iso)
                if reason is not None:
                    counts[reason] += 1
                    continue
                bar = bar_by_session.get(session_iso)
                if bar is None or not (bar[0] > 0.0) or not (bar[1] > 0.0):
                    counts["no_bar"] += 1
                    continue
                open_px, close_px, prev_close = bar
                if abs(sig["basis_open_bps"]) < THRESH_T25:
                    counts["below_t25"] += 1
                    continue
                sig["symbol"] = sym
                sig["session"] = session_iso
                rows.append(fade_event(sig, open_px, close_px, prev_close=prev_close))
                counts["fired_t25"] += 1

    df = (
        pl.DataFrame(rows, schema=EVENT_SCHEMA, orient="row")
        if rows
        else pl.DataFrame(schema=EVENT_SCHEMA)
    )
    funnel = {
        "candidates": candidates,
        "counts": counts,
        "reconciles": bool(sum(counts.values()) == candidates),
        "coverage": _coverage(universe, noii_dir=noii_dir),
        "n_early_close_flag": 0,  # D6: half-days are ordinary events; count is report-only
    }
    return df, funnel


# --------------------------------------------------------------------------- CI / stats


def _ci(df: pl.DataFrame) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n_events, n_sessions), day-clustered over ``net_bps`` (cluster
    key = ET ``session``; ``stress.clustered_mean_ci``, seed 7 / n_boot 2000)."""
    if df.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    m, lo, hi = stress.clustered_mean_ci(
        df["net_bps"].to_numpy(), df["session"].to_numpy(),
        n_boot=_CI_N_BOOT, seed=_CI_SEED,
    )
    return m, lo, hi, df.height, df["session"].n_unique()


def _round_or_none(v: float, ndigits: int) -> float | None:
    """Round a finite value; a non-finite (NaN/inf) becomes None so no invalid token
    reaches the JSON."""
    return round(float(v), ndigits) if np.isfinite(v) else None


def cell_stats(events: pl.DataFrame, *, thresh: float) -> dict:
    """Day-clustered cell statistics + the registered PASS/UNDERPOWERED/BETWEEN flags.

    The cell is the ``|basis_open| >= thresh`` SUBSET of the one fired frame (t25 =>
    all fired rows; t50 => the nested subset -- computed on THIS frame, never a
    re-scan, reviewer attack 4). PASS (registration) = n_fired >= 300 AND
    n_sessions >= 150 AND day-clustered CI-lower > 0 AND mean net >= 2.0 bps.
    UNDERPOWERED if n_fired < 150 (neither pass nor kill). BETWEEN THE BARS =
    point > 0 with the CI spanning 0 (report-only, look spent). Mutating any single
    PASS condition must fail test 10."""
    sub = events.filter(pl.col("basis_open_bps").abs() >= thresh)
    m, lo, hi, n, ns = _ci(sub)

    underpowered = n < UNDERPOWERED_BELOW
    meets_n_fired = n >= CELL_T25_MIN_FIRED
    meets_n_sessions = ns >= CELL_T25_MIN_SESSIONS
    meets_ci = bool(n and not math.isnan(lo) and lo > 0.0)
    meets_mean = bool(n and not math.isnan(m) and m >= MEAN_FLOOR_BPS)
    cell_pass = bool(
        (not underpowered) and meets_n_fired and meets_n_sessions and meets_ci and meets_mean
    )
    between = bool(
        n and not math.isnan(m) and m > 0.0
        and (math.isnan(lo) or lo <= 0.0) and not cell_pass
    )
    return {
        "thresh_bps": thresh,
        "n_fired": n,
        "n_sessions": ns,
        "mean_net_bps": _round_or_none(m, 4) if n else None,
        "ci_lo": _round_or_none(lo, 4) if n else None,
        "ci_hi": _round_or_none(hi, 4) if n else None,
        "meets_n_fired_floor": bool(meets_n_fired),
        "meets_n_sessions_floor": bool(meets_n_sessions),
        "meets_ci_lower_gt_0": meets_ci,
        "meets_mean_floor": meets_mean,
        "underpowered": bool(underpowered),
        "between_the_bars": between,
        "pass": cell_pass,
    }


# --------------------------------------------------------------------------- ADIA panel


def _daily_usd(events: pl.DataFrame) -> pl.DataFrame:
    """Session P&L (USD) at $10k equal notional per event: sum of book*net_bps/1e4."""
    return (
        events.group_by("session")
        .agg((BOOK_NOTIONAL * pl.col("net_bps") / 1e4).sum().alias("pnl_usd"))
        .sort("session")
    )


def adia_panel(events: pl.DataFrame) -> dict:
    """ADIA Lab No.19 panel on the daily-aggregated FIRED (t25) stream (D4).

    Equal $10k per event -> per-session P&L -> native-frequency SR, PSR[SR0=0],
    MinTRL(alpha=0.05). SR/PSR/MinTRL and the sample moments are IMPORTED from
    ``sizing_shadow`` (test 12 identity-checks them); t50 gets no separate panel
    (nested -- one panel, two cell stats)."""
    daily = _daily_usd(events)
    x = daily["pnl_usd"].to_numpy()
    t = int(x.shape[0])
    if t == 0:
        return {
            "T": 0, "mean_pnl_usd": None, "sr_native": None, "psr_sr0_0": None,
            "min_trl": None, "gamma3": None, "gamma4": None, "rho": None,
        }
    g3, g4, rho = sample_moments(x)
    sr = sr_native(x)
    return {
        "T": t,
        "mean_pnl_usd": round(float(np.mean(x)), 4),
        "sr_native": round(sr, 4),
        "psr_sr0_0": _round_or_none(psr(sr, SR0, t, rho, g3, g4), 4),
        "min_trl": _round_or_none(min_trl(sr, SR0, ALPHA, rho, g3, g4), 2),
        "gamma3": round(g3, 4),
        "gamma4": round(g4, 4),
        "rho": round(rho, 4),
    }


# --------------------------------------------------------------------------- rho vs champion


def load_champion_daily(path: str | Path = CHAMPION_OOS_PARQUET) -> pl.DataFrame | None:
    """Champion dev daily P&L stream from the M8-meta-v1 OOS parquet (READ-ONLY,
    the published stream), aggregated to sessions at $10k equal notional. ``None``
    when the parquet is absent."""
    p = Path(path)
    if not p.exists():
        return None
    df = pl.read_parquet(p)
    if df.height == 0 or "session" not in df.columns or "net_bps" not in df.columns:
        return None
    return _daily_usd(df.select("session", "net_bps"))


def rho_vs_champion(
    events: pl.DataFrame, champion_daily: pl.DataFrame | None
) -> float | None:
    """Realized daily-P&L Pearson correlation vs the champion dev daily stream, on
    OVERLAPPING sessions only (D5; report-only). ``None`` when either stream is
    absent, or fewer than 2 overlapping sessions, or a degenerate (zero-variance)
    overlap. The multi-signal hypothesis is rho ~ 0."""
    if champion_daily is None or events.height == 0 or champion_daily.height == 0:
        return None
    ours = _daily_usd(events)
    joined = ours.join(champion_daily, on="session", how="inner", suffix="_champ")
    if joined.height < 2:
        return None
    a = joined["pnl_usd"].to_numpy()
    b = joined["pnl_usd_champ"].to_numpy()
    if np.std(a) == 0.0 or np.std(b) == 0.0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def rho_panel(events: pl.DataFrame, champion_daily: pl.DataFrame | None) -> dict:
    """The rho report cell: {rho_hat, n_overlap, underpowered_rho} (D5: n_overlap<30
    => UNDERPOWERED-rho flag beside rho_hat)."""
    rho = rho_vs_champion(events, champion_daily)
    if champion_daily is None or events.height == 0 or champion_daily.height == 0:
        n_overlap = 0
    else:
        n_overlap = _daily_usd(events).join(
            champion_daily, on="session", how="inner"
        ).height
    return {
        "rho_hat": round(rho, 4) if rho is not None else None,
        "n_overlap": n_overlap,
        "underpowered_rho": bool(n_overlap < RHO_UNDERPOWERED_BELOW),
    }


# --------------------------------------------------------------------------- strata


def _group_means(df: pl.DataFrame, key: str, key_name: str) -> list[dict]:
    rows: list[dict] = []
    for k in (sorted(df[key].unique().to_list()) if df.height else []):
        if k is None:
            continue
        sub = df.filter(pl.col(key) == k)
        m, lo, hi, n, ns = _ci(sub)
        rows.append({
            key_name: str(k), "n": n, "n_sessions": ns,
            "mean_net_bps": _round_or_none(m, 4) if n else None,
            "ci_lo": _round_or_none(lo, 4) if n else None,
            "ci_hi": _round_or_none(hi, 4) if n else None,
        })
    return rows


def build_strata(events: pl.DataFrame) -> dict:
    """Report-only strata (no bars, no gates). The gap_mr FENCE diagnostic --
    corr(basis_open_bps, overnight_gap_bps) -- is computed here and MUST appear in
    cells.json (test 9): basis is orthogonal to the overnight gap by construction,
    so a near-zero correlation confirms M24 is not a disguised gap fade."""
    with_gap = events.filter(pl.col("overnight_gap_bps").is_not_null())
    corr_basis_gap: float | None = None
    if with_gap.height >= 2:
        a = with_gap["basis_open_bps"].to_numpy()
        b = with_gap["overnight_gap_bps"].to_numpy()
        if np.std(a) > 0.0 and np.std(b) > 0.0:
            corr_basis_gap = round(float(np.corrcoef(a, b)[0, 1]), 4)

    # gap-sign x basis-sign 2x2 (net_bps means), over events with a known gap.
    cells_2x2: list[dict] = []
    if with_gap.height:
        tagged = with_gap.with_columns(
            (pl.col("overnight_gap_bps") > 0.0).alias("_gap_pos"),
            (pl.col("basis_open_bps") > 0.0).alias("_basis_pos"),
        )
        for gp in (True, False):
            for bp in (True, False):
                sub = tagged.filter((pl.col("_gap_pos") == gp) & (pl.col("_basis_pos") == bp))
                m, _lo, _hi, n, _ns = _ci(sub)
                cells_2x2.append({
                    "gap_positive": gp, "basis_positive": bp, "n": n,
                    "mean_net_bps": _round_or_none(m, 4) if n else None,
                })

    champ = events.filter(pl.col("symbol").is_in(list(CHAMPION_5)))
    broad = events.filter(~pl.col("symbol").is_in(list(CHAMPION_5)))
    cm, clo, chi, cn, cns = _ci(champ)
    bm, blo, bhi, bn, bns = _ci(broad)

    return {
        "corr_basis_gap": corr_basis_gap,  # gap_mr fence diagnostic (test 9)
        "gap_x_basis_2x2": cells_2x2,
        "imb_side_agrees_split": _group_means(
            events.with_columns(pl.col("imb_side_agrees").cast(pl.Utf8).alias("_imb")),
            "_imb", "imb_side_agrees",
        ),
        "per_year": _group_means(
            events.with_columns(pl.col("session").str.slice(0, 4).alias("_year")),
            "_year", "year",
        ),
        "champion5": {
            "n": cn, "n_sessions": cns,
            "mean_net_bps": _round_or_none(cm, 4) if cn else None,
            "ci_lo": _round_or_none(clo, 4) if cn else None,
            "ci_hi": _round_or_none(chi, 4) if cn else None,
        },
        "broad28": {
            "n": bn, "n_sessions": bns,
            "mean_net_bps": _round_or_none(bm, 4) if bn else None,
            "ci_lo": _round_or_none(blo, 4) if bn else None,
            "ci_hi": _round_or_none(bhi, 4) if bn else None,
        },
    }


# --------------------------------------------------------------------------- ground truth


def ground_truth(events: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """<= k stratified fired events for the v6.1 hand-verification: biggest winners,
    biggest losers, largest |basis|, and (where possible) at least one per year."""
    schema = {
        "session": pl.Utf8, "symbol": pl.Utf8, "basis_open_bps": pl.Float64,
        "side": pl.Int64, "open_px": pl.Float64, "close_px": pl.Float64,
        "gross_bps": pl.Float64, "net_bps": pl.Float64,
        "overnight_gap_bps": pl.Float64, "is_t50": pl.Boolean,
    }
    if events.height == 0:
        return pl.DataFrame(schema=schema)
    d = events.with_columns(pl.arange(0, pl.len()).alias("_idx"))
    winners = d.sort("net_bps", descending=True).head(3)["_idx"].to_list()
    losers = d.sort("net_bps", descending=False).head(3)["_idx"].to_list()
    big = d.sort(pl.col("basis_open_bps").abs(), descending=True).head(4)["_idx"].to_list()
    # one-per-year seed: the first (earliest) event of each year.
    per_year: list[int] = []
    for _yr in sorted({s[:4] for s in d["session"].to_list()}):
        yidx = d.filter(pl.col("session").str.slice(0, 4) == _yr).sort("session").head(1)["_idx"].to_list()
        per_year.extend(yidx)
    picked: list[int] = []
    for i in [*winners, *losers, *big, *per_year]:
        if i not in picked:
            picked.append(i)
        if len(picked) >= k:
            break
    return d.filter(pl.col("_idx").is_in(picked)).drop("_idx").select(list(schema))


# --------------------------------------------------------------------------- writers


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


def build_atlas_md(
    trial_id: str,
    events: pl.DataFrame,
    funnel: dict,
    t25: dict,
    t50: dict,
    adia: dict,
    rho: dict,
    strata: dict,
    *,
    seed: int,
) -> str:
    """Assemble the M24 atlas markdown (ASCII only; no ledger verdict -- the
    orchestrator owns it)."""
    md: list[str] = [
        f"# M24 opening-auction dislocation fade atlas -- {trial_id}",
        "",
        "Family `open_auction_fade_v1` (registered 2026-07-23, M3_REGISTRATION.md "
        "section M24). ONE pooled look over TRAIN+VALIDATE (<= 2026-05-31); any PASS "
        "consequence is Stage-2 FORWARD-JUDGED registration only, never direct "
        "trading. Decision frozen 09:28:30 ET on the opening NOII near-vs-ref basis; "
        "direction AGAINST (fade); exit = the same-session official CLOSE print. Both "
        "legs raw bars1d (L2). NO ledger verdict here.",
        "",
        f"seed={seed}    holdout seal: {HOLDOUT_START.isoformat()}    "
        f"universe: {len(UNIVERSE)} NOII names (champion-5 vs broad-28 reported "
        "separately, NEVER gated).",
        "",
        "## Coverage / event funnel",
        "```",
        json.dumps(funnel, indent=2, default=str),
        "```",
        "",
        "## Cell t25 (|basis_open| >= 25 bps) -- PRIMARY",
        "",
        "PASS = n>=300 & sessions>=150 & CI-lo>0 & mean net>=2.0 bps.",
        "```",
        json.dumps(t25, indent=2, default=str),
        "```",
        "",
        "## Cell t50 (|basis_open| >= 50 bps) -- NESTED subset of t25",
        "```",
        json.dumps(t50, indent=2, default=str),
        "```",
        "",
        "## ADIA No.19 panel (t25 daily-aggregated, $10k/event; SR0=0)",
        "```",
        json.dumps(adia, indent=2, default=str),
        "```",
        "",
        "## rho vs champion (report-only; hypothesis rho ~ 0)",
        "```",
        json.dumps(rho, indent=2, default=str),
        "```",
        "",
        "## Strata (report-only) -- gap_mr FENCE = corr(basis_open, overnight_gap)",
        "```",
        json.dumps(strata, indent=2, default=str),
        "```",
        "",
        "## Per-year (reported, never gated)",
        "",
        _ascii(pl.DataFrame(strata["per_year"])) if strata["per_year"] else "(none)",
        "",
    ]
    return "\n".join(md)


def write_outputs(
    out_dir: Path,
    trial_id: str,
    events: pl.DataFrame,
    cells: dict,
    atlas_md: str,
    gt: pl.DataFrame,
) -> dict[str, Path]:
    """Write the M24 artifacts: atlas.md + cells.json + events.parquet +
    ground_truth.parquet."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "atlas": out_dir / "atlas.md",
        "cells": out_dir / "cells.json",
        "events": out_dir / "events.parquet",
        "ground_truth": out_dir / "ground_truth.parquet",
    }
    paths["atlas"].write_text(atlas_md, encoding="utf-8")
    paths["cells"].write_text(json.dumps(cells, indent=2, default=str), encoding="utf-8")
    events.write_parquet(paths["events"])
    gt.write_parquet(paths["ground_truth"])
    return paths


# --------------------------------------------------------------------------- one-look gate


def assert_look_not_spent(
    out_dir: str | Path | None = None,
    *,
    defect_rerun: bool = False,
    reason: str | None = None,
) -> None:
    """Enforce the family's SINGLE registered look.

    A present ``look_state.json`` refuses a second look UNLESS ``defect_rerun`` is
    set with a non-empty ``reason`` (a ledgered code-defect fix; never threshold
    motion). A defect rerun appends a ledger note so the extra look is auditable."""
    path = look_state_path(out_dir)
    if not path.exists():
        return
    if not defect_rerun:
        raise RuntimeError(
            f"M24 look already spent ({path}); the family has ONE registered look. "
            "A ledgered code-defect fix may re-run with --defect-rerun and --reason."
        )
    if not (reason and reason.strip()):
        raise ValueError("--defect-rerun requires a non-empty --reason (ledgered).")
    ledger_append("note", {
        "event": "M24_DEFECT_RERUN",
        "reason": reason.strip(),
        "look_state": str(path),
    })


def mark_look_spent(
    out_dir: str | Path | None = None,
    *,
    trial_id: str,
    git_sha: str | None = None,
) -> Path:
    """Record the spent look (``look_state.json``): trial id, git sha, timestamp."""
    path = look_state_path(out_dir)
    path.write_text(
        json.dumps({
            "trial_id": trial_id,
            "git_sha": git_sha,
            "spent_ts": datetime.now(UTC).isoformat(),
            "family": "open_auction_fade_v1",
        }, indent=2),
        encoding="utf-8",
    )
    return path


__all__ = [
    "BARS1D_DIR",
    "BOOK_NOTIONAL",
    "CELL_T25_MIN_FIRED",
    "CELL_T25_MIN_SESSIONS",
    "CHAMPION_5",
    "END",
    "EVENT_SCHEMA",
    "M11_SEC_TAF_SELL_BPS",
    "MEAN_FLOOR_BPS",
    "OUT_SUBDIR",
    "SEC_TAF_SELL_BPS",
    "SIGNAL_HMS",
    "START",
    "THRESH_T25",
    "THRESH_T50",
    "UNDERPOWERED_BELOW",
    "UNIVERSE",
    "adia_panel",
    "assert_before_holdout",
    "assert_look_not_spent",
    "build_atlas_md",
    "build_events",
    "build_strata",
    "canonical_out_dir",
    "cell_stats",
    "fade_event",
    "ground_truth",
    "load_champion_daily",
    "load_daily_bars",
    "load_open_noii",
    "look_state_path",
    "mark_look_spent",
    "min_trl",
    "open_basis_at",
    "out_dir_for",
    "psr",
    "rho_panel",
    "rho_vs_champion",
    "sample_moments",
    "sr_native",
    "write_outputs",
]
