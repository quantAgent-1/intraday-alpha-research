"""M27 gap-day reversion harness (family ``gap_day_reversion_v1``).

Registered 2026-07-23 (M3_REGISTRATION.md, section "M27 -- every-day gap-day
reversion, low-liquidity broad names") BEFORE the bbo-1s download. Frozen design:
``research/experiments/M27-gap-day/DESIGN.md`` (the orchestrator's D1-D6 rulings +
14-test plan + build order). Nothing here may be tuned; the family has ONE
registered look, owned by the orchestrator.

The object: an intraday QUOTE-PATH fade of the opening gap on the 5 least-liquid
broad NOII names. g = open_print / prev_close_raw - 1 (both known by 09:31, raw
bars1d L2). Gated cells, nested en bloc: t50 = |g| >= 50 bps, t100 = |g| >= 100
bps. Direction is AGAINST the gap (FADE): position side = -sign(g). Entry TAKER at
09:35:00 ET, exit TAKER at 15:45:00 ET, each at the prevailing quote reached at
decision + a seeded U[5,25]s latency draw, +/- 0.5 bps adverse slip. Fees 0.25 bps
are subtracted separately -- the SPREAD already lives in the fills (buy at ask,
sell at bid), so it is never double-counted (reviewer attack #1).

NO-COST-MODEL beyond COST_MODEL v1 taker: SLIP_BPS per leg + FEES_RT_BPS round
trip. Cost floors are frozen to ``cost_floors.json`` BEFORE any conditional mean
exists (M20 ordering); ``cell_stats`` REFUSES to run without that file on disk.

This module is PURE + injectable: every lake-touching helper takes an injectable
loader so the whole test suite is synthetic/hermetic (no real lake, no network --
the one registered look is the orchestrator's). Landmines respected: raw bars for
prev_close/open (L2); the ``fills.prevailing_idx`` searchsorted>=0 guard (never
wrap to a future quote); the ``latency.latency_ns`` sha256 seeding (never python
hash()); L9 XNAS-internal labeling; the M22 one-look canonical-dir gate.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import polars as pl
import structlog

from enginev51.backtest import stress
from enginev51.backtest.fills import FRAC_PER_BP, prevailing_idx
from enginev51.backtest.latency import latency_ns as _latency_ns
from enginev51.data.bbo1s import bbo_root, partition_path
from enginev51.data.noii import et_ns
from enginev51.protocol import (
    HOLDOUT_START,
    experiments_dir,
    ledger_append,
    refuse_end_on_or_after_holdout,
)

# The early-close drop list is imported BY IDENTITY from the M20 screen (test 8);
# gap-day never re-declares NYSE half-days.
from enginev51.research_screens.sched_window import EARLY_CLOSE_DATES

# ADIA Lab No.19 statistics imported BY IDENTITY from the M23 shadow (test 13); the
# gap-day panel never re-implements SR/PSR/MinTRL -- it reuses the audited kernels.
from enginev51.research_screens.sizing_shadow import (
    min_trl,
    psr,
    sample_moments,
    sr_native,
)

log = structlog.get_logger(__name__)

# --------------------------------------------------------------------------- #
# M27 registration constants (2026-07-23, M3_REGISTRATION.md section M27 +
# DESIGN.md section 1). Frozen; every constant is a counted variant. Do not tune.
# --------------------------------------------------------------------------- #
UNIVERSE: tuple[str, ...] = ("KLAC", "MRVL", "LRCX", "TXN", "AMAT")  # bottom-5 ADV
START, END = date(2023, 8, 1), date(2026, 5, 31)  # purchased window; < holdout
DECISION_HMS: tuple[int, int, int] = (9, 35, 0)
EXIT_HMS: tuple[int, int, int] = (15, 45, 0)
THRESH_T50, THRESH_T100 = 50.0, 100.0  # |gap| bps, nested cells
LATENCY_LO_S, LATENCY_HI_S = 5, 25  # seeded U[5,25] per (sym, session, leg)
SLIP_BPS = 0.5  # per leg, COST_MODEL v1 taker adverse slip
FEES_RT_BPS = 0.25  # SEC/TAF sell side at the $10k clip (round trip)
CELL_MIN_FIRED, CELL_MIN_SESSIONS, UNDERPOWERED_BELOW = 400, 250, 200
MEAN_FLOOR_MULT = 2.0  # mean net must clear 2x the pooled RT floor
STALE_MAX_S = 60  # entry/exit quote staleness bound (D5); wider spreads are NOT skipped
SEED = 7  # repo reproducibility constant (latency + bootstrap)
N_BOOT = 2000  # clustered-CI bootstrap draws
ALPHA = 0.05  # MinTRL / z_{1-alpha}
SR0 = 0.0  # SR0 = 0 everywhere in this family
BOOK_NOTIONAL = 10_000.0  # $10k-per-event research book (gate-currency convention)
OUT_SUBDIR = "M27-gap-day"

# Raw bars1d ONLY (L2) for prev_close/open -- the same lake sizing_shadow reads.
RAW_BARS1D_DIR = Path("data/raw/sip/bars1d")

NS_PER_S = 1_000_000_000

# (symbol, session_iso) -> normalized bbo frame | None
BboGetter = Callable[[str, str], "pl.DataFrame | None"]
# symbol -> list[(session_iso, open, close)] from raw bars1d
BarsLoader = Callable[[str], "list[tuple[str, float, float]]"]

EVENTS_SCHEMA: dict[str, pl.DataType] = {
    "symbol": pl.Utf8,
    "session": pl.Utf8,
    "year": pl.Utf8,
    "prev_close": pl.Float64,
    "open_px": pl.Float64,
    "g_bps": pl.Float64,
    "is_t100": pl.Boolean,
    "side": pl.Int64,  # position side = -sign(g)
    "entry_bid": pl.Float64,
    "entry_ask": pl.Float64,
    "entry_spread_bps": pl.Float64,
    "entry_fill": pl.Float64,
    "entry_lat_s": pl.Float64,
    "exit_bid": pl.Float64,
    "exit_ask": pl.Float64,
    "exit_spread_bps": pl.Float64,
    "exit_fill": pl.Float64,
    "exit_lat_s": pl.Float64,
    "gross_bps": pl.Float64,
    "net_bps": pl.Float64,
}


# =========================================================================== guards


def assert_before_holdout(end: date) -> None:
    """Refuse any run reaching the sealed holdout (PROTOCOL v6 section 1).

    The purchased window is strictly <= 2026-05-31; an ``end`` on/after the
    2026-06-01 seal raises SealViolation (the download and every look stay
    pre-holdout). Never a bare assert — ``python -O`` strips those (B7/J2)."""
    refuse_end_on_or_after_holdout(end)


# =========================================================================== loaders


@lru_cache(maxsize=16)
def _read_month(path_str: str) -> pl.DataFrame:
    return pl.read_parquet(path_str)


def load_bbo_month(
    sym: str, month: str, *, out_dir: str | Path | None = None
) -> pl.DataFrame | None:
    """One (symbol, month) bbo-1s partition, ts-sorted, sane-filtered.

    Reads ``data/raw/bbo1s/{SYM}/{YYYY-MM}.parquet`` -- the same module-local layout
    the champion names use, via ``bbo1s.partition_path``. Applies the fill sanity
    filter (bid > 0 AND ask > bid -- never cross a broken book, the tape/bbo1s
    discipline). ``None`` when the partition is absent or filters to empty."""
    root = bbo_root(out_dir)
    path = partition_path(root, sym, month)
    if not path.exists():
        return None
    df = _read_month(str(path))
    if df.height == 0:
        return None
    df = df.filter((pl.col("bid") > 0.0) & (pl.col("ask") > pl.col("bid"))).sort("ts")
    return df if df.height else None


def load_bbo_for_session(
    sym: str, session_iso: str, *, out_dir: str | Path | None = None
) -> pl.DataFrame | None:
    """One (symbol, session)'s 1s BBO rows, sliced to the ET calendar day.

    Reads the month partition via ``load_bbo_month`` and restricts to
    [midnight ET, next-midnight ET). ``None`` when the partition is absent or the
    slice is empty."""
    df = load_bbo_month(sym, session_iso[:7], out_dir=out_dir)
    if df is None:
        return None
    lo = et_ns(session_iso, 0, 0, 0)
    next_day = (date.fromisoformat(session_iso) + timedelta(days=1)).isoformat()
    hi = et_ns(next_day, 0, 0, 0)
    df = df.filter((pl.col("ts") >= lo) & (pl.col("ts") < hi)).sort("ts")
    return df if df.height else None


def make_bbo_getter(*, out_dir: str | Path | None = None) -> BboGetter:
    """A ``(symbol, session_iso) -> frame|None`` bbo loader over the real lake.

    Injected by the CLI; tests pass their own synthetic getter instead (no lake)."""

    def getter(symbol: str, session_iso: str) -> pl.DataFrame | None:
        return load_bbo_for_session(symbol, session_iso, out_dir=out_dir)

    return getter


def load_raw_bars(sym: str, *, bars_dir: Path = RAW_BARS1D_DIR) -> list[tuple[str, float, float]]:
    """Daily ``(session_iso, open, close)`` from RAW bars1d (L2), ts-sorted.

    Mirrors ``sizing_shadow.load_raw_closes`` (UTC-date key, raw prices) but keeps
    BOTH the open and the close -- gap = open / prev_close - 1. ``[]`` when the raw
    bar file is absent (that symbol contributes no candidates)."""
    p = Path(bars_dir) / f"{sym.upper()}.parquet"
    if not p.exists():
        return []
    df = pl.read_parquet(p).sort("ts")
    out: list[tuple[str, float, float]] = []
    for r in df.iter_rows(named=True):
        d = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
        out.append((d, float(r["open"]), float(r["close"])))
    return out


def make_bars_loader(*, bars_dir: Path = RAW_BARS1D_DIR) -> BarsLoader:
    """A ``symbol -> [(session_iso, open, close)]`` loader over the raw bars1d lake."""

    def loader(sym: str) -> list[tuple[str, float, float]]:
        return load_raw_bars(sym, bars_dir=bars_dir)

    return loader


# =========================================================================== quotes


def _arrays(bbo: pl.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return bbo["ts"].to_numpy(), bbo["bid"].to_numpy(), bbo["ask"].to_numpy()


def quote_lookup(
    ts: np.ndarray, bid: np.ndarray, ask: np.ndarray, ts_ns: int, *, stale_max_s: int = STALE_MAX_S
) -> tuple[tuple[float, float] | None, str | None]:
    """Prevailing (bid, ask) at-or-before ``ts_ns``, or a miss reason.

    ``prevailing_idx`` (fills.py: ``searchsorted(side='right') - 1``, guarded ``< 0``
    -- a lookup before the first tick returns a MISS, never numpy's wrap to the last
    (future) quote). A prevailing quote older than ``stale_max_s`` is a ``stale_quote``
    miss (D5). Returns ((bid, ask), None) on success else (None, reason) with reason in
    {'no_quote', 'stale_quote'}."""
    i = prevailing_idx(ts, ts_ns)
    if i < 0:
        return None, "no_quote"
    if int(ts_ns) - int(ts[i]) > stale_max_s * NS_PER_S:
        return None, "stale_quote"
    return (float(bid[i]), float(ask[i])), None


def quote_at(
    ts: np.ndarray, bid: np.ndarray, ask: np.ndarray, ts_ns: int, *, stale_max_s: int = STALE_MAX_S
) -> tuple[float, float] | None:
    """Prevailing (bid, ask) at ``ts_ns`` or ``None`` (no-quote OR stale) -- the
    thin DESIGN-named wrapper over ``quote_lookup``."""
    q, _ = quote_lookup(ts, bid, ask, ts_ns, stale_max_s=stale_max_s)
    return q


def latency_ns(sym: str, session: str, leg: str, *, seed: int = SEED) -> int:
    """Seeded U[5,25]s latency (ns) for one (sym, session, leg), deterministic.

    Reuses ``backtest.latency.latency_ns`` VERBATIM with ``plan_id = f"{sym}:{session}"``
    so the hashed string is exactly ``sha256(f"{seed}:{sym}:{session}:{leg}")`` -- the
    repo sha256 convention, NEVER python ``hash()`` (salted per process). Legs are
    "entry" / "exit", so the two legs of one session draw independently."""
    return _latency_ns(seed, f"{sym}:{session}", leg, float(LATENCY_LO_S), float(LATENCY_HI_S))


@dataclass(frozen=True, slots=True)
class LegFill:
    """One taker leg's outcome: fill price, the raw prevailing quote it crossed, the
    quoted spread (bps), the latency draw (s), and a miss reason (None = filled)."""

    price: float
    bid: float
    ask: float
    spread_bps: float
    latency_s: float
    reason: str | None


def taker_fill(
    ts: np.ndarray,
    bid: np.ndarray,
    ask: np.ndarray,
    ts_decision: int,
    side: int,
    leg: str,
    sym: str,
    session: str,
    *,
    seed: int = SEED,
) -> LegFill:
    """TAKER fill at the quote reached at ``ts_decision + latency(sym,session,leg)``.

    A BUY (side > 0) pays ask * (1 + SLIP_BPS bp); a SELL (side < 0) hits
    bid * (1 - SLIP_BPS bp). The SPREAD is INSIDE this fill (ask vs bid) -- the net
    subtracts only the separate FEES_RT_BPS, so the spread is never double-counted
    (reviewer attack #1). A no-quote/stale lookup returns a ``reason``-tagged NaN
    ``LegFill`` (the event is then skipped -- D4: both legs must be fillable)."""
    lat = latency_ns(sym, session, leg, seed=seed)
    q, reason = quote_lookup(ts, bid, ask, ts_decision + lat)
    lat_s = lat / NS_PER_S
    if q is None:
        return LegFill(float("nan"), float("nan"), float("nan"), float("nan"), lat_s, reason)
    b, a = q
    mid = 0.5 * (a + b)
    spread_bps = (a - b) / mid * 1e4
    slip = SLIP_BPS * FRAC_PER_BP
    price = a * (1.0 + slip) if side > 0 else b * (1.0 - slip)
    return LegFill(price, b, a, spread_bps, lat_s, None)


def gap_of(prev_close: float, open_px: float) -> float:
    """g_bps = (open / prev_close - 1) * 1e4 (raw bars1d, L2; both known by 09:31)."""
    return (open_px / prev_close - 1.0) * 1e4


# =========================================================================== build


def _leg_skip_reason(leg: str, reason: str | None) -> str | None:
    """Map a leg miss to the funnel skip reason: 'stale_quote' is leg-agnostic
    (D5), a plain no-quote becomes no_quote_entry / no_quote_exit."""
    if reason is None:
        return None
    if reason == "stale_quote":
        return "stale_quote"
    return f"no_quote_{leg}"


def build_events(
    *,
    universe: tuple[str, ...] = UNIVERSE,
    start: date = START,
    end: date = END,
    load_bars: BarsLoader,
    get_bbo: BboGetter,
    seed: int = SEED,
) -> tuple[pl.DataFrame, dict]:
    """Build the FIRED gap-fade events (t50 frame; is_t100 nested) + the funnel.

    Per (sym, session in [start, end]): prev_close = the immediately preceding raw
    bar's close (D1, calendar-gap agnostic; missing predecessor -> ``no_bar``),
    open = this session's raw open; g = gap_of(...). Skip reasons, one per candidate
    (funnel reconciles -- test 12): ``no_bar``, ``early_close`` (EARLY_CLOSE_DATES,
    imported), ``below_t50`` (|g| < 50), ``no_quote_entry`` / ``no_quote_exit`` /
    ``stale_quote`` (D4: BOTH legs must be fillable). A fired row: side = -sign(g)
    (FADE), entry TAKER at 09:35 (side), exit TAKER at 15:45 (-side),
    gross = side * (exit_fill/entry_fill - 1) * 1e4, net = gross - FEES_RT_BPS.
    ``is_t100`` flags |g| >= 100 in the SAME frame (nested, reviewer attack #7)."""
    start_iso, end_iso = start.isoformat(), end.isoformat()
    funnel = {
        "candidates": 0,
        "no_bar": 0,
        "early_close": 0,
        "below_t50": 0,
        "no_quote_entry": 0,
        "no_quote_exit": 0,
        "stale_quote": 0,
        "fired": 0,
    }
    rows: list[dict] = []

    for sym in universe:
        bars = load_bars(sym)
        prev_close: float | None = None
        for session, open_px, close_px in bars:
            if start_iso <= session <= end_iso:
                funnel["candidates"] += 1
                _build_one(sym, session, open_px, prev_close, get_bbo, seed, funnel, rows)
            prev_close = close_px  # carry THIS session's close forward as next prev_close

    events = (
        pl.DataFrame(rows, schema=EVENTS_SCHEMA, orient="row")
        if rows
        else pl.DataFrame(schema=EVENTS_SCHEMA)
    )
    events = events.sort(["symbol", "session"])
    return events, funnel


def _build_one(
    sym: str,
    session: str,
    open_px: float,
    prev_close: float | None,
    get_bbo: BboGetter,
    seed: int,
    funnel: dict,
    rows: list[dict],
) -> None:
    """Resolve ONE candidate into either a funnel skip or an appended fired row."""
    if session in EARLY_CLOSE_DATES:
        funnel["early_close"] += 1
        return
    if prev_close is None or prev_close <= 0.0 or open_px is None or open_px <= 0.0:
        funnel["no_bar"] += 1
        return

    g = gap_of(prev_close, open_px)
    if abs(g) < THRESH_T50:
        funnel["below_t50"] += 1
        return

    bbo = get_bbo(sym, session)
    if bbo is None or bbo.height == 0:
        funnel["no_quote_entry"] += 1
        return
    ts, bid, ask = _arrays(bbo)

    side = -1 if g > 0 else 1  # FADE: short an up-gap, long a down-gap
    decision_ts = et_ns(session, *DECISION_HMS)
    exit_ts = et_ns(session, *EXIT_HMS)

    entry = taker_fill(ts, bid, ask, decision_ts, side, "entry", sym, session, seed=seed)
    if entry.reason is not None:
        funnel[_leg_skip_reason("entry", entry.reason)] += 1
        return
    exit_leg = taker_fill(ts, bid, ask, exit_ts, -side, "exit", sym, session, seed=seed)
    if exit_leg.reason is not None:
        funnel[_leg_skip_reason("exit", exit_leg.reason)] += 1
        return

    gross_bps = side * (exit_leg.price / entry.price - 1.0) * 1e4
    net_bps = gross_bps - FEES_RT_BPS
    funnel["fired"] += 1
    rows.append(
        {
            "symbol": sym,
            "session": session,
            "year": session[:4],
            "prev_close": prev_close,
            "open_px": open_px,
            "g_bps": g,
            "is_t100": bool(abs(g) >= THRESH_T100),
            "side": int(side),
            "entry_bid": entry.bid,
            "entry_ask": entry.ask,
            "entry_spread_bps": entry.spread_bps,
            "entry_fill": entry.price,
            "entry_lat_s": entry.latency_s,
            "exit_bid": exit_leg.bid,
            "exit_ask": exit_leg.ask,
            "exit_spread_bps": exit_leg.spread_bps,
            "exit_fill": exit_leg.price,
            "exit_lat_s": exit_leg.latency_s,
            "gross_bps": gross_bps,
            "net_bps": net_bps,
        }
    )


# =========================================================================== cost floors


def _spread_bps_at(bbo: pl.DataFrame | None, ts_ns: int) -> float | None:
    """Prevailing quoted spread (bps of mid) at ``ts_ns``, or None (no/stale quote)."""
    if bbo is None or bbo.height == 0:
        return None
    ts, bid, ask = _arrays(bbo)
    q = quote_at(ts, bid, ask, ts_ns)
    if q is None:
        return None
    b, a = q
    return (a - b) / (0.5 * (a + b)) * 1e4


def out_dir_for(out_dir: str | Path | None = None) -> Path:
    """Resolve the M27 output directory (defaults to the canonical experiments dir)."""
    p = Path(out_dir) if out_dir is not None else canonical_out_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p


def canonical_out_dir() -> Path:
    """The ONE canonical M27 output/look-state directory (M22 idiom): the one-look
    gate is anchored here so a fresh --out-dir can never sidestep it. The CLI passes
    no directory and always resolves to this path."""
    return experiments_dir() / OUT_SUBDIR


def floors_path(out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / "cost_floors.json"


def write_cost_floors_first(
    *,
    universe: tuple[str, ...] = UNIVERSE,
    start: date = START,
    end: date = END,
    load_bars: BarsLoader,
    get_bbo: BboGetter,
    out_dir: str | Path | None = None,
) -> dict:
    """Compute and WRITE ``cost_floors.json`` FIRST (M20 ordering; test-enforced).

    RT_floor(name) = median over sessions of (spread_bps@09:35 + spread_bps@15:45)
    + 2 * SLIP_BPS + FEES_RT_BPS. The POOLED floor (the screen bar) is the median of
    the per-name floors. Written to disk BEFORE any conditional mean exists; the
    stats functions REFUSE to run until this file is present (reviewer attack #6)."""
    start_iso, end_iso = start.isoformat(), end.isoformat()
    rt_spreads: dict[str, list[float]] = {s: [] for s in universe}
    for sym in universe:
        for session, _open_px, _close_px in load_bars(sym):
            if not (start_iso <= session <= end_iso) or session in EARLY_CLOSE_DATES:
                continue
            bbo = get_bbo(sym, session)
            s_open = _spread_bps_at(bbo, et_ns(session, *DECISION_HMS))
            s_close = _spread_bps_at(bbo, et_ns(session, *EXIT_HMS))
            if s_open is None or s_close is None:
                continue
            rt_spreads[sym].append(s_open + s_close)

    slip_fee = 2.0 * SLIP_BPS + FEES_RT_BPS
    per_name: dict[str, dict] = {}
    name_floors: list[float] = []
    for sym in universe:
        vals = rt_spreads[sym]
        if not vals:
            per_name[sym] = {"median_rt_spread_bps": None, "floor_bps": None, "n_sessions": 0}
            continue
        med = float(np.median(vals))
        floor = med + slip_fee
        per_name[sym] = {
            "median_rt_spread_bps": round(med, 4),
            "floor_bps": round(floor, 4),
            "n_sessions": len(vals),
        }
        name_floors.append(floor)
    pooled = round(float(np.median(name_floors)), 4) if name_floors else None

    out = {
        "generated_ts": datetime.now(UTC).isoformat(),
        "family": "gap_day_reversion_v1",
        "params": {
            "slip_bps_per_leg": SLIP_BPS,
            "slip_bps_rt": round(2.0 * SLIP_BPS, 4),
            "fees_rt_bps": FEES_RT_BPS,
            "decision_hms": list(DECISION_HMS),
            "exit_hms": list(EXIT_HMS),
        },
        "per_name": per_name,
        "pooled_floor_bps": pooled,
    }
    fp = floors_path(out_dir)
    fp.write_text(json.dumps(out, indent=2), encoding="utf-8")
    log.info("m27_cost_floors_written", path=str(fp), pooled_floor_bps=pooled)
    return out


def _require_floors(out_dir: str | Path | None) -> dict:
    """Load cost_floors.json or RAISE (the floors-before-means ordering guard)."""
    fp = floors_path(out_dir)
    if not fp.exists():
        raise FileNotFoundError(
            f"cost_floors.json missing at {fp}; write_cost_floors_first must run FIRST "
            "(PROTOCOL: floors are frozen BEFORE any conditional mean exists)."
        )
    return json.loads(fp.read_text(encoding="utf-8"))


# =========================================================================== stats


def _ci(vals: np.ndarray, sessions: np.ndarray) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n, n_sessions) via the day-clustered bootstrap (seed 7/2000)."""
    if vals.shape[0] == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    mean, lo, hi = stress.clustered_mean_ci(vals, sessions, n_boot=N_BOOT, seed=SEED)
    return mean, lo, hi, int(vals.shape[0]), int(np.unique(sessions).shape[0])


def cell_stats(events: pl.DataFrame, thresh: float, *, out_dir: str | Path | None = None) -> dict:
    """Per-cell net stats + the registered PASS / UNDERPOWERED / BETWEEN flags.

    REQUIRES ``cost_floors.json`` on disk (raises otherwise -- reviewer attack #6).
    The cell is the FIRED subset with |g| >= ``thresh`` (t100 is is_t100 within the
    t50 frame; nested, same frame). PASS (registration): n >= 400 AND sessions >= 250
    AND day-clustered CI-lo > 0 AND mean net >= 2x the POOLED RT floor AND >= 3/5
    names with positive point estimates (reviewer attack #5). UNDERPOWERED if
    n < 200. BETWEEN (house vocab): point > 0 but CI spans 0 -> report-only."""
    floors = _require_floors(out_dir)
    pooled = floors.get("pooled_floor_bps")

    cell = events.filter(pl.col("is_t100")) if thresh >= THRESH_T100 else events
    vals = cell["net_bps"].to_numpy() if cell.height else np.array([], dtype=float)
    sess = cell["session"].to_numpy() if cell.height else np.array([], dtype=object)
    mean, lo, hi, n, n_sessions = _ci(vals, sess)

    per_name: dict[str, float] = {}
    if cell.height:
        g = cell.group_by("symbol").agg(pl.col("net_bps").mean().alias("m"))
        for r in g.sort("symbol").iter_rows(named=True):
            per_name[r["symbol"]] = round(float(r["m"]), 4)
    n_names_positive = sum(1 for v in per_name.values() if v > 0.0)

    bar = (MEAN_FLOOR_MULT * pooled) if pooled is not None else None
    n_ok = (n >= CELL_MIN_FIRED) and (n_sessions >= CELL_MIN_SESSIONS)
    ci_ok = bool(n and not np.isnan(lo) and lo > 0.0)
    floor_ok = bool(bar is not None and n and mean >= bar)
    names_ok = n_names_positive >= 3
    underpowered = n < UNDERPOWERED_BELOW
    cell_pass = bool((not underpowered) and n_ok and ci_ok and floor_ok and names_ok)
    spans_zero = bool(n and (np.isnan(lo) or lo <= 0.0))
    between = bool((not cell_pass) and (not underpowered) and n and mean > 0.0 and spans_zero)

    return {
        "thresh_bps": thresh,
        "N": n,
        "n_sessions": n_sessions,
        "mean_net_bps": round(mean, 4) if n else None,
        "ci_lo": round(lo, 4) if (n and not np.isnan(lo)) else None,
        "ci_hi": round(hi, 4) if (n and not np.isnan(hi)) else None,
        "pooled_floor_bps": pooled,
        "bar_2x_floor_bps": round(bar, 4) if bar is not None else None,
        "per_name_mean": per_name,
        "n_names_positive": n_names_positive,
        "meets_n_sessions_floor": bool(n_ok),
        "meets_ci_lower_gt_0": ci_ok,
        "meets_2x_floor": floor_ok,
        "meets_3of5_names": bool(names_ok),
        "underpowered": bool(underpowered),
        "between": between,
        "pass": cell_pass,
    }


# =========================================================================== ADIA panel


def adia_panel(events: pl.DataFrame) -> dict:
    """ADIA No.19 daily-panel over the t50 stream (D6): $10k-per-event aggregation.

    Each event books ``net_bps`` on a $10k notional; the daily series is the per-
    session sum of those USD P&Ls. SR at native frequency, PSR[SR0=0], MinTRL, the
    sample moments, and a day-clustered CI -- all via the kernels IMPORTED from
    ``sizing_shadow`` (test 13). t100 gets ``cell_stats`` only (D6)."""
    if events.height == 0:
        return {
            "T": 0, "n_events": 0, "mean_usd": None, "ci_lo_usd": None, "ci_hi_usd": None,
            "sr_native": None, "psr_sr0_0": None, "min_trl": None,
            "gamma3": None, "gamma4": None, "rho": None,
        }
    per_event = events.with_columns(
        (pl.col("net_bps") * FRAC_PER_BP * BOOK_NOTIONAL).alias("_usd")
    )
    daily = (
        per_event.group_by("session")
        .agg(pl.col("_usd").sum().alias("delta_usd"))
        .sort("session")
    )
    x = daily["delta_usd"].to_numpy()
    t = int(x.shape[0])
    mean, lo, hi = stress.clustered_mean_ci(x, daily["session"].to_numpy(), n_boot=N_BOOT, seed=SEED)
    g3, g4, rho = sample_moments(x)
    sr = sr_native(x)
    p = psr(sr, SR0, t, rho, g3, g4)
    mtrl = min_trl(sr, SR0, ALPHA, rho, g3, g4)
    return {
        "T": t,
        "n_events": int(events.height),
        "mean_usd": round(float(mean), 4),
        "ci_lo_usd": round(float(lo), 4),
        "ci_hi_usd": round(float(hi), 4),
        "sr_native": round(sr, 4),
        "psr_sr0_0": round(p, 4) if np.isfinite(p) else None,
        "min_trl": round(mtrl, 2) if np.isfinite(mtrl) else None,
        "gamma3": round(g3, 4),
        "gamma4": round(g4, 4),
        "rho": round(rho, 4),
    }


# =========================================================================== strata
# Report-only (no bars, no CI, no gate): per-name, per-year, gap-sign, |g| tercile,
# entry-spread tercile -- over the t50 fired stream.


def _mean_by(events: pl.DataFrame, key: str) -> pl.DataFrame:
    return (
        events.group_by(key)
        .agg(pl.len().alias("n"), pl.col("net_bps").mean().round(4).alias("mean_net_bps"))
        .sort(key)
    )


def _tercile_col(events: pl.DataFrame, src: str, name: str) -> pl.DataFrame:
    """Attach a lo/mid/hi tercile label on ``src`` (fewer than 3 rows -> 'all')."""
    if events.height >= 3:
        q = events[src].qcut(3, labels=["lo", "mid", "hi"], allow_duplicates=True)
        return events.with_columns(q.cast(pl.Utf8).alias(name))
    return events.with_columns(pl.lit("all", dtype=pl.Utf8).alias(name))


def report_strata(events: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """The five report-only strata over the t50 fired stream (no bar)."""
    if events.height == 0:
        empty = pl.DataFrame(schema={"key": pl.Utf8, "n": pl.Int64, "mean_net_bps": pl.Float64})
        return {k: empty for k in ("per_name", "per_year", "gap_sign", "abs_g_tercile",
                                   "entry_spread_tercile")}
    signed = events.with_columns(
        pl.when(pl.col("g_bps") > 0).then(pl.lit("up_gap")).otherwise(pl.lit("down_gap")).alias(
            "gap_sign"
        ),
        pl.col("g_bps").abs().alias("_abs_g"),
    )
    g_terc = _tercile_col(signed, "_abs_g", "abs_g_tercile")
    s_terc = _tercile_col(signed, "entry_spread_bps", "entry_spread_tercile")
    return {
        "per_name": _mean_by(events, "symbol"),
        "per_year": _mean_by(events, "year"),
        "gap_sign": _mean_by(signed, "gap_sign"),
        "abs_g_tercile": _mean_by(g_terc, "abs_g_tercile"),
        "entry_spread_tercile": _mean_by(s_terc, "entry_spread_tercile"),
    }


# =========================================================================== ground truth


def ground_truth(events: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """<= ``k`` stratified fills vs raw quotes (v6.1): the biggest winners/losers,
    the largest |g|, and the widest entry spreads -- deduped, capped at k. Each row
    carries the raw prevailing bid/ask it crossed so a reviewer can recompute the
    fill and the net by hand."""
    if events.height == 0:
        return events
    e = events.with_columns(pl.col("g_bps").abs().alias("_abs_g"))
    picks: list[pl.DataFrame] = [
        e.sort("net_bps", descending=True).head(3),  # biggest winners
        e.sort("net_bps", descending=False).head(3),  # biggest losers
        e.sort("_abs_g", descending=True).head(2),  # largest |g|
        e.sort("entry_spread_bps", descending=True).head(2),  # widest entry spread
    ]
    gt = pl.concat(picks, how="vertical").unique(subset=["symbol", "session"], keep="first")
    gt = gt.sort(["symbol", "session"]).head(k).drop("_abs_g")
    return gt


# =========================================================================== one-look gate


def look_state_path(out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / "look_state.json"


def assert_look_not_spent(
    out_dir: str | Path | None = None, *, defect_rerun: bool = False, reason: str | None = None
) -> None:
    """Enforce the family's SINGLE registered look (M22 idiom verbatim).

    A present ``look_state.json`` refuses a second look UNLESS ``defect_rerun`` is set
    with a non-empty ``reason`` (a ledgered code-defect fix; never threshold motion)."""
    path = look_state_path(out_dir)
    if not path.exists():
        return
    if not defect_rerun:
        raise RuntimeError(
            f"M27 look already spent ({path}); the family has ONE registered look. "
            "A ledgered code-defect fix may re-run with --defect-rerun and --reason."
        )
    if not (reason and reason.strip()):
        raise ValueError("--defect-rerun requires a non-empty --reason (ledgered).")
    ledger_append("note", {
        "event": "M27_DEFECT_RERUN",
        "reason": reason.strip(),
        "look_state": str(path),
    })


def mark_look_spent(
    out_dir: str | Path | None = None, *, trial_id: str, git_sha: str | None = None
) -> Path:
    """Record the spent look (``look_state.json``): trial id, git sha, timestamp."""
    path = look_state_path(out_dir)
    path.write_text(
        json.dumps({
            "trial_id": trial_id,
            "git_sha": git_sha,
            "spent_ts": datetime.now(UTC).isoformat(),
            "family": "gap_day_reversion_v1",
        }, indent=2),
        encoding="utf-8",
    )
    return path


# =========================================================================== writers


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
    t50: dict,
    t100: dict,
    panel: dict,
    strata: dict[str, pl.DataFrame],
    funnel: dict,
    floors: dict,
    *,
    seed: int,
) -> str:
    """Assemble the ASCII atlas markdown (NO ledger verdict; the orchestrator owns it)."""
    def cell_md(label: str, c: dict) -> list[str]:
        return [
            f"## {label} (|g| >= {c['thresh_bps']:.0f} bps)",
            "",
            f"N={c['N']}  sessions={c['n_sessions']}  mean_net_bps={c['mean_net_bps']}  "
            f"CI=[{c['ci_lo']}, {c['ci_hi']}]",
            f"pooled_floor_bps={c['pooled_floor_bps']}  bar(2x)={c['bar_2x_floor_bps']}  "
            f"names_positive={c['n_names_positive']}/5",
            f"PASS={c['pass']}  UNDERPOWERED={c['underpowered']}  BETWEEN={c['between']}",
            "```",
            json.dumps(c, indent=2, default=str),
            "```",
            "",
        ]

    md: list[str] = [
        f"# M27 gap-day reversion atlas -- {trial_id}",
        "",
        "Family `gap_day_reversion_v1` (registered 2026-07-23, M3_REGISTRATION.md "
        "section M27). ONE pooled look over the purchased window (2023-08-01.."
        "2026-05-31, < holdout). FADE the opening gap: side = -sign(g); entry TAKER "
        "09:35 ET, exit TAKER 15:45 ET; XNAS TOB (L9 -- never NBBO). Spread lives in "
        "the fills; only the 0.25 bps fees are subtracted separately. NO-COST-MODEL "
        "beyond COST_MODEL v1 taker. NO ledger verdict here.",
        "",
        f"seed={seed}    holdout seal: {HOLDOUT_START.isoformat()}",
        "",
        "## Cost floors (frozen; written BEFORE any conditional mean)",
        "",
        "```",
        json.dumps(floors, indent=2, default=str),
        "```",
        "",
    ]
    md += cell_md("Cell t50", t50)
    md += cell_md("Cell t100 (nested)", t100)
    md += [
        "## ADIA No.19 daily panel (t50 stream; $10k per event; SR0=0)",
        "",
        "```",
        json.dumps(panel, indent=2, default=str),
        "```",
        "",
        "## Funnel (skips + below + fired == candidates)",
        "",
        "```",
        json.dumps(funnel, indent=2, default=str),
        "```",
        "",
        "## Report-only strata (no bar)",
        "",
    ]
    for name, df in strata.items():
        md += [f"### {name}", "", _ascii(df) if df.height else "(none)", ""]
    return "\n".join(md)


def write_outputs(
    out_dir: Path,
    trial_id: str,
    events: pl.DataFrame,
    t50: dict,
    t100: dict,
    panel: dict,
    strata: dict[str, pl.DataFrame],
    funnel: dict,
    floors: dict,
    atlas_md: str,
    gt: pl.DataFrame,
) -> dict[str, Path]:
    """Write the M27 artifacts: atlas.md, cells.json, events.parquet,
    ground_truth.parquet, cost_floors.json (already on disk), look_state.json (later).
    PASS/UNDERPOWERED/BETWEEN are FLAGS, not verdicts (the orchestrator owns those)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "atlas": out_dir / "atlas.md",
        "cells": out_dir / "cells.json",
        "events": out_dir / "events.parquet",
        "ground_truth": out_dir / "ground_truth.parquet",
    }
    paths["atlas"].write_text(atlas_md, encoding="utf-8")
    paths["cells"].write_text(
        json.dumps(
            {
                "trial_id": trial_id,
                "t50": t50,
                "t100": t100,
                "adia_panel": panel,
                "funnel": funnel,
                "cost_floors": floors,
                "strata": {k: v.to_dicts() for k, v in strata.items()},
            },
            indent=2, default=str,
        ),
        encoding="utf-8",
    )
    events.write_parquet(paths["events"])
    gt.write_parquet(paths["ground_truth"])
    return paths


__all__ = [
    "ALPHA",
    "BOOK_NOTIONAL",
    "CELL_MIN_FIRED",
    "CELL_MIN_SESSIONS",
    "EARLY_CLOSE_DATES",
    "END",
    "FEES_RT_BPS",
    "LATENCY_HI_S",
    "LATENCY_LO_S",
    "MEAN_FLOOR_MULT",
    "OUT_SUBDIR",
    "SEED",
    "SLIP_BPS",
    "SR0",
    "START",
    "STALE_MAX_S",
    "THRESH_T100",
    "THRESH_T50",
    "UNDERPOWERED_BELOW",
    "UNIVERSE",
    "LegFill",
    "adia_panel",
    "assert_before_holdout",
    "assert_look_not_spent",
    "build_atlas_md",
    "build_events",
    "canonical_out_dir",
    "cell_stats",
    "floors_path",
    "gap_of",
    "ground_truth",
    "latency_ns",
    "load_bbo_for_session",
    "load_bbo_month",
    "load_raw_bars",
    "look_state_path",
    "make_bars_loader",
    "make_bbo_getter",
    "mark_look_spent",
    "min_trl",
    "out_dir_for",
    "psr",
    "quote_at",
    "quote_lookup",
    "report_strata",
    "sample_moments",
    "sr_native",
    "taker_fill",
    "write_cost_floors_first",
    "write_outputs",
]
