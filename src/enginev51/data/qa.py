"""Data-quality audit for the raw tick / quote / bar lake.

Everything here is READ-ONLY. It answers a single question the backfill-repair
plan depends on: *for each (symbol, session), is the stored data trustworthy?*

Three entry points:

- ``audit_day(trades, quotes, session_iso, bounds_ns)`` — pure, frame-in / dict-out.
  Tolerates reduced legacy schemas (trades possibly only ``ts,price,size``;
  quotes possibly only ``ts,bid,ask,bid_size,ask_size``) and zero-row frames.
- ``audit_symbol(settings, symbol, ...)`` — walks the lake partitions that exist
  across ``settings.read_roots``, intersects them with the NYSE calendar, runs
  ``audit_day`` per session, and returns ``(DataFrame, coverage_dict)``.
- ``audit_bars(settings, symbol)`` — bars1m monthly coverage + thin-session flags.

Session bounds are RTH (regular NYSE open→close, half-days honored). A "gap" is
measured strictly inside RTH and includes the open→first-event and last-event→close
edges, so a session that only trades in its second half is caught.

All timestamps are UTC epoch nanoseconds (Int64 "ts"), same as the store.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import click
import numpy as np
import polars as pl
import structlog

from enginev51.backtest import fills
from enginev51.config import Settings, get_settings
from enginev51.data import bbo1s, calendar, store

log = structlog.get_logger(__name__)

NS_PER_S = 1_000_000_000
NS_PER_MIN = 60 * NS_PER_S
# Below this many RTH 1-minute bars a full session is suspect (RTH ideal = 390).
MIN_RTH_BARS = 300
# A session shorter than this (ns) is treated as a half-day and exempt from the
# thin-bar flag (half-days are ~210 RTH minutes and legitimately short).
_HALF_DAY_NS = 6 * 3600 * NS_PER_S

# --- cross-source QA thresholds (SIM_AUDIT_2026-07-21 F1 detection method) ------
# On the corrected RAW primary bars1m lake, bar-VWAP tracks the raw tape to ~0 bps
# (the audit measured <=0.035); the old dividend-adjusted lake read -12 bps (NVDA)
# to -83 bps (MU-2024). PASS demands the raw-lake regime.
BAR_TAPE_PASS_ABS_BPS = 1.0          # |median bar-vs-tape offset| must be < this
BBO_QUOTE_PASS_MEDIAN_TICKS = 1.0    # median |bbo-mid - sip-mid| must be <= this
BBO_QUOTE_FLAG_TICKS = 2.0           # a single sample exceeding this is flagged
_TICK_USD = 0.01                     # penny tick (every signal symbol trades > $1)


# ----------------------------------------------------------------- small helpers


def _series(df: pl.DataFrame | None, name: str) -> pl.Series | None:
    """Column ``name`` if the (non-empty) frame has it, else None. Reduced-schema safe."""
    if df is None or df.height == 0 or name not in df.columns:
        return None
    return df.get_column(name)


def _is_monotonic(ts: pl.Series | None) -> bool:
    """True if ts is non-decreasing (vacuously true for <2 rows)."""
    if ts is None or ts.len() < 2:
        return True
    return bool((ts.diff().drop_nulls() >= 0).all())


def _within_frac(ts: pl.Series | None, open_ns: int, close_ns: int) -> float | None:
    """Fraction of rows with open_ns <= ts <= close_ns (RTH). None if no rows."""
    if ts is None or ts.len() == 0:
        return None
    within = ((ts >= open_ns) & (ts <= close_ns)).sum()
    return float(within) / float(ts.len())


def _max_gap_s(ts: pl.Series | None, open_ns: int, close_ns: int) -> float | None:
    """Largest silent stretch (seconds) inside RTH, edges included.

    Considers open→first-event, every consecutive intra-RTH diff, and
    last-event→close. If no event falls inside RTH the whole session is the gap.
    None only when there is no session window at all.
    """
    if close_ns <= open_ns:
        return None
    rth = None
    if ts is not None and ts.len():
        rth = ts.filter((ts >= open_ns) & (ts <= close_ns)).sort()
    if rth is None or rth.len() == 0:
        return float(close_ns - open_ns) / NS_PER_S
    first = int(rth[0])
    last = int(rth[-1])
    gap = max(first - open_ns, close_ns - last)
    if rth.len() >= 2:
        gap = max(gap, int(rth.diff().drop_nulls().max()))
    return float(gap) / NS_PER_S


# ----------------------------------------------------------------------- per-day


def audit_day(
    trades: pl.DataFrame | None,
    quotes: pl.DataFrame | None,
    session_iso: str,
    session_bounds_utc_ns: tuple[int, int],
) -> dict[str, Any]:
    """Audit one (symbol, session). Pure: takes frames, returns a flat dict of metrics.

    ``session_bounds_utc_ns`` = (rth_open_ns, rth_close_ns). Both frames may be
    None / zero-row and may carry reduced legacy schemas.
    """
    open_ns, close_ns = session_bounds_utc_ns
    notes: list[str] = []

    t_ts = _series(trades, "ts")
    q_ts = _series(quotes, "ts")
    rows_trades = 0 if trades is None else trades.height
    rows_quotes = 0 if quotes is None else quotes.height

    # --- schema-reduction notes (informational, never fatal) ---
    if trades is not None and trades.height and "conditions" not in trades.columns:
        notes.append("trades: reduced schema (no exchange/conditions/tape)")
    if quotes is not None and quotes.height and "conditions" not in quotes.columns:
        notes.append("quotes: reduced schema (no exchange/conditions/tape)")

    # --- price / size sanity ---
    nonpos_price = 0
    nonpos_size = 0
    t_price = _series(trades, "price")
    t_size = _series(trades, "size")
    if t_price is not None:
        nonpos_price += int((t_price <= 0).sum())
    if t_size is not None:
        nonpos_size += int((t_size <= 0).sum())
    q_bid = _series(quotes, "bid")
    q_ask = _series(quotes, "ask")
    q_bsz = _series(quotes, "bid_size")
    q_asz = _series(quotes, "ask_size")
    if q_bid is not None and q_ask is not None:
        nonpos_price += int(((q_bid <= 0) | (q_ask <= 0)).sum())
    if q_bsz is not None and q_asz is not None:
        nonpos_size += int(((q_bsz <= 0) | (q_asz <= 0)).sum())

    # --- crossed / locked + spread (two-sided quotes only) ---
    crossed_frac: float | None = None
    spread_bps_p50: float | None = None
    if q_bid is not None and q_ask is not None and q_bid.len():
        crossed_frac = float((q_bid >= q_ask).sum()) / float(q_bid.len())
        qf = pl.DataFrame({"bid": q_bid, "ask": q_ask}).filter(
            (pl.col("bid") > 0) & (pl.col("ask") > 0) & (pl.col("ask") > pl.col("bid"))
        )
        if qf.height:
            spread_bps = (
                (pl.col("ask") - pl.col("bid"))
                / ((pl.col("ask") + pl.col("bid")) / 2.0)
                * 10_000.0
            )
            spread_bps_p50 = float(qf.select(spread_bps.median()).item())

    # --- monotonicity, within-session, gaps ---
    mono_t = _is_monotonic(t_ts)
    mono_q = _is_monotonic(q_ts)
    within_t = _within_frac(t_ts, open_ns, close_ns)
    within_q = _within_frac(q_ts, open_ns, close_ns)
    gap_t = _max_gap_s(t_ts, open_ns, close_ns)
    gap_q = _max_gap_s(q_ts, open_ns, close_ns)

    if rows_trades == 0:
        notes.append("no trades")
    if rows_quotes == 0:
        notes.append("no quotes")
    if not mono_t:
        notes.append("trades: ts not monotonic")
    if not mono_q:
        notes.append("quotes: ts not monotonic")
    if within_t is not None and within_t < 1.0:
        notes.append(f"trades: {1.0 - within_t:.3f} of rows outside RTH")
    if within_q is not None and within_q < 1.0:
        notes.append(f"quotes: {1.0 - within_q:.3f} of rows outside RTH")
    if crossed_frac:
        notes.append(f"quotes: crossed/locked frac {crossed_frac:.4f}")
    if nonpos_price:
        notes.append(f"nonpositive price rows: {nonpos_price}")
    if nonpos_size:
        notes.append(f"nonpositive size rows: {nonpos_size}")

    return {
        "session": session_iso,
        "rows_trades": rows_trades,
        "rows_quotes": rows_quotes,
        "ts_monotonic_trades": mono_t,
        "ts_monotonic_quotes": mono_q,
        "ts_within_session_trades": within_t,
        "ts_within_session_quotes": within_q,
        "max_gap_s_trades": gap_t,
        "max_gap_s_quotes": gap_q,
        "crossed_or_locked_frac": crossed_frac,
        "nonpositive_price_rows": nonpos_price,
        "nonpositive_size_rows": nonpos_size,
        "spread_bps_p50": spread_bps_p50,
        "notes": notes,
    }


# schema for the per-session audit frame (keeps zero-session frames well-typed)
_AUDIT_SCHEMA: dict[str, pl.DataType] = {
    "symbol": pl.Utf8,
    "session": pl.Utf8,
    "rows_trades": pl.Int64,
    "rows_quotes": pl.Int64,
    "ts_monotonic_trades": pl.Boolean,
    "ts_monotonic_quotes": pl.Boolean,
    "ts_within_session_trades": pl.Float64,
    "ts_within_session_quotes": pl.Float64,
    "max_gap_s_trades": pl.Float64,
    "max_gap_s_quotes": pl.Float64,
    "crossed_or_locked_frac": pl.Float64,
    "nonpositive_price_rows": pl.Int64,
    "nonpositive_size_rows": pl.Int64,
    "spread_bps_p50": pl.Float64,
    "notes": pl.List(pl.Utf8),
}


# --------------------------------------------------------------- lake discovery


def _partition_map(
    roots: tuple[Path, ...], feed: str, kind: str, symbol: str
) -> dict[str, Path]:
    """{part_stem -> winning file path}, primary root first (matches scan_kind_multi)."""
    seen: dict[str, Path] = {}
    for root in roots:
        d = root / feed / kind / symbol.upper()
        if not d.is_dir():
            continue
        for f in d.glob("*.parquet"):
            seen.setdefault(f.stem, f)
    return seen


def _bounds_ns(day: date) -> tuple[int, int]:
    op, cl = calendar.session_bounds_utc(day)
    return int(op.timestamp() * NS_PER_S), int(cl.timestamp() * NS_PER_S)


def _read_part(pmap: dict[str, Path], key: str) -> pl.DataFrame | None:
    p = pmap.get(key)
    if p is None:
        return None
    return pl.read_parquet(p)


def audit_symbol(
    settings: Settings,
    symbol: str,
    kinds: tuple[str, ...] = ("trades", "quotes"),
    start: date | None = None,
    end: date | None = None,
    feed: str = "sip",
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Audit every calendar session that has a partition for ``symbol``.

    Sessions are the union of partition dates across ``settings.read_roots`` for
    the requested ``kinds``, intersected with the NYSE calendar. Returns the
    per-session audit DataFrame and a coverage-summary dict (expected sessions,
    present-nonempty counts, and per-kind missing-session lists — where "missing"
    means no partition, or an empty partition on a day the other kind has data).
    """
    symbol = symbol.upper()
    roots = settings.read_roots
    pmaps = {k: _partition_map(roots, feed, k, symbol) for k in kinds}

    # present partition dates (as calendar dates), union across kinds
    present: set[date] = set()
    for pmap in pmaps.values():
        for stem in pmap:
            try:
                present.add(date.fromisoformat(stem))
            except ValueError:
                continue
    if start is not None:
        present = {d for d in present if d >= start}
    if end is not None:
        present = {d for d in present if d <= end}

    if not present:
        empty = pl.DataFrame(schema=_AUDIT_SCHEMA)
        return empty, {
            "symbol": symbol,
            "kinds": list(kinds),
            "first_session": None,
            "last_session": None,
            "expected_sessions": 0,
            "present_nonempty": 0,
            "per_kind": {k: {"present": 0, "nonempty": 0, "missing_sessions": []} for k in kinds},
        }

    first, last = min(present), max(present)
    cal_days = calendar.trading_days(first, last)
    cal_set = set(cal_days)
    audit_days = sorted(present & cal_set)

    rows: list[dict[str, Any]] = []
    # per-date rows-by-kind, for coverage bookkeeping
    day_rows: dict[date, dict[str, int]] = {}
    for d in audit_days:
        iso = d.isoformat()
        bounds = _bounds_ns(d)
        frames: dict[str, pl.DataFrame | None] = {
            "trades": _read_part(pmaps.get("trades", {}), iso) if "trades" in kinds else None,
            "quotes": _read_part(pmaps.get("quotes", {}), iso) if "quotes" in kinds else None,
        }
        res = audit_day(frames["trades"], frames["quotes"], iso, bounds)
        res["symbol"] = symbol
        rows.append(res)
        day_rows[d] = {
            "trades": res["rows_trades"],
            "quotes": res["rows_quotes"],
        }

    df = (
        pl.DataFrame(rows, schema_overrides=_AUDIT_SCHEMA).select(list(_AUDIT_SCHEMA))
        if rows
        else pl.DataFrame(schema=_AUDIT_SCHEMA)
    )

    # --- coverage summary ---
    per_kind: dict[str, Any] = {}
    for k in kinds:
        present_dates = {date.fromisoformat(s) for s in pmaps[k] if _iso_ok(s)} & cal_set
        nonempty = sum(1 for d in audit_days if day_rows.get(d, {}).get(k, 0) > 0)
        missing: list[str] = []
        for d in cal_days:
            has_part = d in present_dates
            n_here = day_rows.get(d, {}).get(k, 0)
            other_nonempty = any(
                day_rows.get(d, {}).get(o, 0) > 0 for o in kinds if o != k
            )
            if not has_part:
                missing.append(d.isoformat())
            elif n_here == 0 and other_nonempty:
                missing.append(d.isoformat())
        per_kind[k] = {
            "present": len(present_dates),
            "nonempty": nonempty,
            "missing_sessions": missing,
        }

    present_nonempty = sum(
        1 for d in audit_days if all(day_rows.get(d, {}).get(k, 0) > 0 for k in kinds)
    )
    coverage = {
        "symbol": symbol,
        "kinds": list(kinds),
        "first_session": first.isoformat(),
        "last_session": last.isoformat(),
        "expected_sessions": len(cal_days),
        "present_nonempty": present_nonempty,
        "per_kind": per_kind,
    }
    return df, coverage


def _iso_ok(s: str) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


# ------------------------------------------------------------------- bars1m QA


def audit_bars(
    settings: Settings, symbol: str, feed: str = "sip"
) -> dict[str, Any]:
    """bars1m coverage for ``symbol``: per-month rows, thin RTH sessions, missing months."""
    symbol = symbol.upper()
    roots = settings.read_roots
    pmap = _partition_map(roots, feed, "bars1m", symbol)

    if not pmap:
        return {
            "symbol": symbol,
            "first_month": None,
            "last_month": None,
            "months": [],
            "months_missing": [],
            "suspicious_sessions": [],
        }

    lf = store.scan_kind_multi(roots, feed, "bars1m", symbol)
    bars = lf.collect()

    # month string + ET session date per bar (RTH classification below)
    et = pl.from_epoch(pl.col("ts"), time_unit="ns").dt.convert_time_zone("America/New_York")
    bars = bars.with_columns(
        et.dt.strftime("%Y-%m").alias("_month"),
        et.dt.date().alias("_etdate"),
        et.dt.hour().alias("_hh"),
        et.dt.minute().alias("_mm"),
    )
    # RTH wall-clock: 09:30 <= t < 16:00 ET (half-days handled via bounds below)
    rth_mask = ((pl.col("_hh") > 9) | ((pl.col("_hh") == 9) & (pl.col("_mm") >= 30))) & (
        pl.col("_hh") < 16
    )
    rth = bars.filter(rth_mask)

    # per-session RTH bar counts
    per_sess = (
        rth.group_by("_etdate").agg(pl.len().alias("rth_bars")).sort("_etdate")
        if rth.height
        else pl.DataFrame(schema={"_etdate": pl.Date, "rth_bars": pl.UInt32})
    )

    # half-day exemption: any session whose calendar length < 6h is not flagged thin
    suspicious: list[dict[str, Any]] = []
    for row in per_sess.iter_rows(named=True):
        d = row["_etdate"]
        n = int(row["rth_bars"])
        if n >= MIN_RTH_BARS:
            continue
        try:
            op, cl = _bounds_ns(d)
        except ValueError:
            continue
        if (cl - op) < _HALF_DAY_NS:
            continue  # legitimate half-day
        suspicious.append({"session": d.isoformat(), "rth_bars": n})

    # per-month summary
    months: list[dict[str, Any]] = []
    month_rows = (
        bars.group_by("_month").agg(pl.len().alias("rows")).sort("_month")
    )
    sess_by_month = (
        per_sess.with_columns(pl.col("_etdate").dt.strftime("%Y-%m").alias("_month"))
        .group_by("_month")
        .agg(pl.len().alias("sessions"))
    )
    susp_by_month: dict[str, int] = {}
    for s in suspicious:
        m = s["session"][:7]
        susp_by_month[m] = susp_by_month.get(m, 0) + 1
    sess_map = {r["_month"]: r["sessions"] for r in sess_by_month.iter_rows(named=True)}
    for r in month_rows.iter_rows(named=True):
        m = r["_month"]
        months.append(
            {
                "month": m,
                "rows": int(r["rows"]),
                "sessions": int(sess_map.get(m, 0)),
                "suspicious_sessions": int(susp_by_month.get(m, 0)),
            }
        )

    present_months = {m["month"] for m in months}
    first_m = min(present_months)
    last_m = max(present_months)
    months_missing = [
        m for m in _month_range(first_m, last_m) if m not in present_months
    ]

    return {
        "symbol": symbol,
        "first_month": first_m,
        "last_month": last_m,
        "months": months,
        "months_missing": months_missing,
        "suspicious_sessions": suspicious,
    }


def _month_range(first: str, last: str) -> list[str]:
    """Inclusive YYYY-MM range (calendar months, no trading-day filter)."""
    fy, fm = (int(x) for x in first.split("-"))
    ly, lm = (int(x) for x in last.split("-"))
    out: list[str] = []
    y, m = fy, fm
    while (y, m) <= (ly, lm):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def _now_utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


# =============================================================== cross-source QA
# Two PERMANENT checks that the Alpaca-sourced and Databento-sourced lakes agree
# at the seams SIM_AUDIT_2026-07-21 flagged:
#   * bar_tape_offset      — Alpaca minute-bar VWAP vs Alpaca RAW tick-tape VWAP.
#     This is the F1 price-scale detector: dividend-adjusted bars carry a nonzero
#     offset against the raw traded tape; the corrected raw primary lake reads ~0.
#   * bbo_quote_agreement  — Databento XNAS bbo-1s mid vs Alpaca SIP NBBO mid at
#     aligned RTH instants (the cross-vendor quote sanity the MOC family rests on).
# Each has a PURE core (frames in, dict out) so it is unit-testable without a lake,
# mirroring ``audit_day``. All timestamps are UTC epoch ns, as everywhere here.


def _read_partition(
    settings: Settings, kind: str, symbol: str, session: str, feed: str = "sip"
) -> pl.DataFrame | None:
    """First-existing daily partition for (kind, symbol, session) across read_roots.

    Primary lake first, then legacy — the same resolution order as
    ``backtest/tape`` and ``auction_replay.load_raw_trades``. ``None`` when no root
    carries the partition.
    """
    for root in settings.read_roots:
        p = store.partition_path(root, feed, kind, symbol, session)
        if p.exists():
            return pl.read_parquet(p)
    return None


def _minute_vwap(
    df: pl.DataFrame,
    price_col: str,
    weight_col: str,
    open_ns: int,
    close_ns: int,
    out_col: str,
) -> pl.DataFrame:
    """Per-RTH-minute volume-weighted mean price, keyed by the minute-open ns.

    Rows are fenced to ``[open_ns, close_ns)`` and to strictly-positive
    price/weight, then bucketed by ``ts`` floored to the minute (Alpaca 1-min bars
    are stamped at the interval OPEN, so a trade at 14:30:30 shares the minute-open
    key 14:30:00 with the 14:30 bar). Empty in -> empty out.
    """
    sub = df.filter(
        (pl.col("ts") >= open_ns)
        & (pl.col("ts") < close_ns)
        & (pl.col(price_col) > 0)
        & (pl.col(weight_col) > 0)
    )
    if sub.height == 0:
        return pl.DataFrame(schema={"minute": pl.Int64, out_col: pl.Float64})
    return (
        sub.with_columns(((pl.col("ts") // NS_PER_MIN) * NS_PER_MIN).alias("minute"))
        .group_by("minute")
        .agg(
            (
                (pl.col(price_col) * pl.col(weight_col)).sum()
                / pl.col(weight_col).sum()
            ).alias(out_col)
        )
    )


def _empty_offset(symbol: str, session: str, notes: list[str]) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "session": session,
        "n_minutes": 0,
        "median_offset_bps": None,
        "mean_offset_bps": None,
        "p25_offset_bps": None,
        "p75_offset_bps": None,
        "max_abs_offset_bps": None,
        "notes": notes,
    }


def _bar_tape_offset(
    bars: pl.DataFrame | None,
    trades: pl.DataFrame | None,
    symbol: str,
    session: str,
    bounds: tuple[int, int],
) -> dict[str, Any]:
    """Pure core: median per-minute (bar_vwap / tape_vwap - 1) in bps over RTH."""
    open_ns, close_ns = bounds
    notes: list[str] = []
    if bars is None or bars.height == 0:
        notes.append("no bars")
    if trades is None or trades.height == 0:
        notes.append("no trades")
    if bars is None or bars.height == 0 or trades is None or trades.height == 0:
        return _empty_offset(symbol, session, notes)

    bv = _minute_vwap(bars, "vwap", "volume", open_ns, close_ns, "bar_vwap")
    tv = _minute_vwap(trades, "price", "size", open_ns, close_ns, "tape_vwap")
    joined = bv.join(tv, on="minute", how="inner").filter(
        (pl.col("bar_vwap") > 0) & (pl.col("tape_vwap") > 0)
    )
    if joined.height == 0:
        return _empty_offset(symbol, session, ["no overlapping RTH minutes"])

    off = joined.select(
        ((pl.col("bar_vwap") / pl.col("tape_vwap") - 1.0) * 1e4).alias("off_bps")
    )["off_bps"]
    return {
        "symbol": symbol,
        "session": session,
        "n_minutes": int(off.len()),
        "median_offset_bps": float(off.median()),
        "mean_offset_bps": float(off.mean()),
        "p25_offset_bps": float(off.quantile(0.25)),
        "p75_offset_bps": float(off.quantile(0.75)),
        "max_abs_offset_bps": float(off.abs().max()),
        "notes": notes,
    }


def bar_tape_offset(
    symbol: str,
    session: str,
    *,
    settings: Settings | None = None,
    bars: pl.DataFrame | None = None,
    trades: pl.DataFrame | None = None,
    session_bounds_ns: tuple[int, int] | None = None,
    feed: str = "sip",
) -> dict[str, Any]:
    """Median per-minute Alpaca bar-VWAP / raw tape-VWAP offset (bps) over RTH.

    SIM_AUDIT F1 detector. Minute-bar VWAP carries whatever price scale the bars1m
    lake holds (raw or dividend-adjusted); the raw tick tape is always the true
    traded scale. On the corrected RAW primary lake the median offset is ~0
    (|.| < ``BAR_TAPE_PASS_ABS_BPS``); the old adjusted lake read -12 bps (NVDA) to
    -83 bps (MU-2024).

    Pure when ``bars`` and ``trades`` frames are supplied (unit tests); otherwise
    both are resolved from the lake via ``settings`` (default ``get_settings()``) —
    bars1m through ``store.load_bars`` (primary-first shadow) and the raw ``trades``
    partition through ``read_roots``. Missing/empty data yields a clean zero-minute
    dict with a note, never a traceback.
    """
    symbol = symbol.upper()
    if session_bounds_ns is None:
        try:
            session_bounds_ns = _bounds_ns(date.fromisoformat(session))
        except (ValueError, KeyError) as exc:
            return _empty_offset(symbol, session, [f"no session bounds: {exc}"])
    open_ns, close_ns = session_bounds_ns

    if bars is None or trades is None:
        settings = settings or get_settings()
        if bars is None:
            bars = store.load_bars(settings.read_roots, feed, symbol, open_ns, close_ns)
        if trades is None:
            trades = _read_partition(settings, "trades", symbol, session, feed)

    return _bar_tape_offset(bars, trades, symbol, session, session_bounds_ns)


def _empty_agree(symbol: str, session: str, notes: list[str]) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "session": session,
        "n_samples": 0,
        "median_abs_ticks": None,
        "max_abs_ticks": None,
        "n_flagged": 0,
        "notes": notes,
    }


def _two_sided(df: pl.DataFrame) -> pl.DataFrame:
    """bid>0 & ask>bid rows, ts-sorted (never mid a broken/one-sided book)."""
    return df.filter((pl.col("bid") > 0) & (pl.col("ask") > pl.col("bid"))).sort("ts")


def _bbo_quote_agreement(
    bbo: pl.DataFrame | None,
    quotes: pl.DataFrame | None,
    symbol: str,
    session: str,
    bounds: tuple[int, int],
    sample_every_min: int,
) -> dict[str, Any]:
    """Pure core: median |bbo-1s mid - SIP quote mid| (ticks) at aligned instants."""
    open_ns, close_ns = bounds
    notes: list[str] = []
    if bbo is None or bbo.height == 0:
        notes.append("no bbo1s")
    if quotes is None or quotes.height == 0:
        notes.append("no quotes")
    if bbo is None or bbo.height == 0 or quotes is None or quotes.height == 0:
        return _empty_agree(symbol, session, notes)

    b = _two_sided(bbo)
    q = _two_sided(quotes)
    if b.height == 0 or q.height == 0:
        return _empty_agree(symbol, session, ["no two-sided quotes on one/both feeds"])

    b_ts = b["ts"].to_numpy().astype(np.int64)
    b_bid = b["bid"].to_numpy().astype(np.float64)
    b_ask = b["ask"].to_numpy().astype(np.float64)
    q_ts = q["ts"].to_numpy().astype(np.int64)
    q_bid = q["bid"].to_numpy().astype(np.float64)
    q_ask = q["ask"].to_numpy().astype(np.float64)

    step = max(1, int(sample_every_min)) * NS_PER_MIN
    diffs: list[float] = []
    t = open_ns + step  # first interior 15-min mark (a prevailing quote must exist)
    while t < close_ns:
        mb = fills.prevailing_mid(b_ts, b_bid, b_ask, t)
        mq = fills.prevailing_mid(q_ts, q_bid, q_ask, t)
        if np.isfinite(mb) and np.isfinite(mq) and mb > 0 and mq > 0:
            diffs.append(abs(mb - mq) / _TICK_USD)
        t += step

    if not diffs:
        return _empty_agree(
            symbol, session, ["no aligned samples with quotes on both feeds"]
        )
    arr = np.asarray(diffs, dtype=np.float64)
    return {
        "symbol": symbol,
        "session": session,
        "n_samples": int(arr.size),
        "median_abs_ticks": float(np.median(arr)),
        "max_abs_ticks": float(arr.max()),
        "n_flagged": int((arr > BBO_QUOTE_FLAG_TICKS).sum()),
        "sample_every_min": int(sample_every_min),
        "notes": notes,
    }


def bbo_quote_agreement(
    symbol: str,
    session: str,
    *,
    settings: Settings | None = None,
    bbo: pl.DataFrame | None = None,
    quotes: pl.DataFrame | None = None,
    sample_every_min: int = 15,
    session_bounds_ns: tuple[int, int] | None = None,
    feed: str = "sip",
    bbo_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Spot-check Databento XNAS bbo-1s mid vs Alpaca SIP NBBO mid across RTH.

    At every ``sample_every_min`` mark strictly inside the session, take each feed's
    PIT prevailing mid (last quote at-or-before the mark, via ``fills.prevailing_mid``)
    and record ``|mid_bbo - mid_sip|`` in ticks ($0.01). Returns the median and max
    tick difference and the count exceeding ``BBO_QUOTE_FLAG_TICKS``. The two books
    are different economic objects (XNAS venue TOB vs consolidated SIP NBBO) but
    agree to ~1 tick on Nasdaq megacaps in RTH — a divergence is a real seam flag.

    Pure when ``bbo`` and ``quotes`` frames are supplied (unit tests); otherwise the
    bbo-1s frame is resolved via ``bbo1s.load_bbo_session`` and the SIP quotes via
    ``read_roots``. Missing/empty data yields a clean zero-sample dict with a note.
    """
    symbol = symbol.upper()
    if session_bounds_ns is None:
        try:
            session_bounds_ns = _bounds_ns(date.fromisoformat(session))
        except (ValueError, KeyError) as exc:
            return _empty_agree(symbol, session, [f"no session bounds: {exc}"])

    if bbo is None:
        bbo = bbo1s.load_bbo_session(symbol, session, out_dir=bbo_dir)
    if quotes is None:
        settings = settings or get_settings()
        quotes = _read_partition(settings, "quotes", symbol, session, feed)

    return _bbo_quote_agreement(
        bbo, quotes, symbol, session, session_bounds_ns, sample_every_min
    )


# --------------------------------------------------------------------------- cli


@click.group()
def main() -> None:
    """Data-quality checks (read-only)."""
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety


def _fmt_bar_tape(bt: dict[str, Any]) -> tuple[str, bool]:
    med = bt["median_offset_bps"]
    ok = med is not None and abs(med) < BAR_TAPE_PASS_ABS_BPS
    status = "PASS" if ok else "WARN"
    lines = [
        "[bar-tape offset] Alpaca bar-VWAP vs raw tick-tape VWAP (SIM_AUDIT F1)",
    ]
    if med is None:
        lines.append(
            f"  {status}: no data  (n_minutes={bt['n_minutes']}, notes={bt['notes']})"
        )
    else:
        lines.append(
            f"  {status}: median={med:+.4f} bps   "
            f"(PASS |median| < {BAR_TAPE_PASS_ABS_BPS} bps)"
        )
        lines.append(
            f"        n_minutes={bt['n_minutes']}  "
            f"p25={bt['p25_offset_bps']:+.4f}  p75={bt['p75_offset_bps']:+.4f}  "
            f"max_abs={bt['max_abs_offset_bps']:.4f} bps"
        )
        if bt["notes"]:
            lines.append(f"        notes={bt['notes']}")
    return "\n".join(lines), ok


def _fmt_bbo_quote(bq: dict[str, Any]) -> tuple[str, bool]:
    med = bq["median_abs_ticks"]
    ok = med is not None and med <= BBO_QUOTE_PASS_MEDIAN_TICKS
    status = "PASS" if ok else "WARN"
    lines = [
        "[bbo-quote agreement] Databento XNAS bbo-1s mid vs Alpaca SIP NBBO mid",
    ]
    if med is None:
        lines.append(
            f"  {status}: no data  (n_samples={bq['n_samples']}, notes={bq['notes']})"
        )
    else:
        lines.append(
            f"  {status}: median={med:.3f} ticks  max={bq['max_abs_ticks']:.3f}  "
            f"flagged(>{BBO_QUOTE_FLAG_TICKS})={bq['n_flagged']}/{bq['n_samples']}   "
            f"(PASS median <= {BBO_QUOTE_PASS_MEDIAN_TICKS} tick)"
        )
        if bq["notes"]:
            lines.append(f"        notes={bq['notes']}")
    return "\n".join(lines), ok


@main.command("cross-source")
@click.option("--symbol", required=True, help="Ticker (e.g. NVDA).")
@click.option("--session", required=True, help="Session ISO date (YYYY-MM-DD).")
@click.option("--feed", default="sip", help="Alpaca lake feed (default sip).")
@click.option(
    "--sample-every-min",
    default=15,
    type=int,
    help="bbo-vs-quote sample cadence in RTH minutes (default 15).",
)
@click.option("--bbo-dir", default=None, help="BBO-1s lake root (default data/raw/bbo1s).")
def cross_source_cmd(
    symbol: str, session: str, feed: str, sample_every_min: int, bbo_dir: str | None
) -> None:
    """Run both cross-source checks for one (symbol, session) and print PASS/WARN."""
    settings = get_settings()
    bt = bar_tape_offset(symbol, session, settings=settings, feed=feed)
    bq = bbo_quote_agreement(
        symbol,
        session,
        settings=settings,
        feed=feed,
        sample_every_min=sample_every_min,
        bbo_dir=bbo_dir,
    )
    bt_txt, bt_ok = _fmt_bar_tape(bt)
    bq_txt, bq_ok = _fmt_bbo_quote(bq)
    click.echo(f"cross-source QA  symbol={symbol.upper()}  session={session}  feed={feed}")
    click.echo("")
    click.echo(bt_txt)
    click.echo("")
    click.echo(bq_txt)
    click.echo("")
    click.echo(f"overall: {'PASS' if (bt_ok and bq_ok) else 'WARN'}")


if __name__ == "__main__":
    main()
