"""SessionContext — the per-(symbol, session) fact sheet detectors read from.

A SessionContext bundles everything a named-payer detector needs for ONE RTH
session, computed once and PIT-honestly:

* this session's 1-min RTH bars with running session derivations
  (cum_vwap, day_high_run, day_low_run, minute_idx);
* trailing-20-session statistics computed from sessions STRICTLY BEFORE the
  context session (prev_close, sigma_d_bps, avg 15:00-15:45 range, avg
  cumulative-volume-by-minute) — the PIT seal for the detector family;
* optional same-session 1-second event bars and mapped-index 1-min bars;
* calendar facts (RTH open/close, curfew, monthly-opex flag).

Feed is "sip" throughout (matches backtest/tape). Timestamps are UTC ns.

PIT discipline (PROTOCOL, binding): trailing stats use only sessions dated
strictly before ``session``. Trailing bars are loaded with an end bound at this
session's open, so a store that also contains future sessions produces identical
trailing statistics (verified in tests/test_context.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
import structlog

from enginev51.config import Settings
from enginev51.data import calendar, store
from enginev51.flows import ffcal

log = structlog.get_logger(__name__)

ET = ZoneInfo("America/New_York")
FEED = "sip"
NS_PER_S = 1_000_000_000
NS_PER_MIN = 60 * NS_PER_S

# RTH minute-of-day bounds (ET) used to fence trailing-session bars. Half-day
# closes (13:00 ET) fall inside [OPEN, CLOSE) so the last bar is still the true
# close; the 15:00-15:45 window simply has no bars on those days (skipped).
_RTH_OPEN_MIN = 9 * 60 + 30      # 09:30
_RTH_CLOSE_MIN = 16 * 60         # 16:00
_RANGE_START_MIN = 15 * 60       # 15:00
_RANGE_END_MIN = 15 * 60 + 45    # 15:45

CURFEW_MIN_BEFORE_CLOSE = 10     # curfew = close - 10 min
TRAILING_LOOKBACK_SESSIONS = 20
TRAILING_MIN_SESSIONS = 12       # < this available -> load returns None
_CALENDAR_LOOKBACK_DAYS = 45     # calendar window to harvest >= 20 prior sessions

# Mapped index per signal symbol (semis complex -> SOXX, TSLA -> QQQ).
INDEX_MAP: dict[str, str] = {
    "NVDA": "SOXX",
    "AMD": "SOXX",
    "MU": "SOXX",
    "TSLA": "QQQ",
    "GOOGL": "QQQ",  # out-of-family extension (ledger M3-A0-v1.1-ext-googl)
}


def et_close_ns(session: str, hour: int, minute: int) -> int:
    """UTC-ns instant of ``hour:minute`` ET wall time on ``session`` (ISO date).

    Detectors use this for their fixed decision instants (09:45, 15:00 ET). The
    value is a bar-CLOSE instant; the corresponding decision bar OPEN is this
    minus one minute.
    """
    y, m, d = (int(x) for x in session.split("-"))
    dt = datetime(y, m, d, hour, minute, tzinfo=ET)
    return int(dt.timestamp()) * NS_PER_S


@dataclass(slots=True)
class SessionContext:
    symbol: str
    session: str
    session_open_ts: int
    session_close_ts: int
    curfew_ts: int
    bars: pl.DataFrame
    prev_close: float
    sigma_d_bps: float
    avg_range_1500_1545_bps: float
    avg_cum_volume_by_minute: np.ndarray
    event_bars: pl.DataFrame | None
    index_bars: pl.DataFrame | None
    is_monthly_opex: bool

    def quote_at(self, ts: int) -> tuple[float, float] | None:
        """(bid, ask) from the last COMPLETED event-bar second at ts.

        Event-bar row ts is the bucket START covering [ts, ts+1s); a bucket
        containing the decision instant is not complete yet and would leak up
        to 1 s of future quote state, so only buckets with END <= ts qualify.
        None if event bars are absent or none qualifies.
        """
        ev = self.event_bars
        if ev is None or ev.height == 0:
            return None
        sub = ev.filter(
            (pl.col("ts") <= ts - 1_000_000_000)
            & pl.col("bid").is_not_null()
            & pl.col("ask").is_not_null()
        )
        if sub.height == 0:
            return None
        row = sub.tail(1)
        return float(row["bid"][0]), float(row["ask"][0])


# --------------------------------------------------------------------------- helpers

def _et_cols(lf: pl.LazyFrame | pl.DataFrame) -> pl.Expr:
    """ET wall-clock datetime expression from the UTC-ns `ts` column."""
    return (
        pl.from_epoch(pl.col("ts"), time_unit="ns")
        .dt.replace_time_zone("UTC")
        .dt.convert_time_zone("America/New_York")
    )


def _derive_session_bars(bars: pl.DataFrame) -> pl.DataFrame:
    """Attach running session derivations to ts-sorted RTH bars."""
    cum_pv = (pl.col("vwap") * pl.col("volume")).cum_sum()
    cum_v = pl.col("volume").cum_sum()
    return bars.with_columns(
        pl.when(cum_v > 0).then(cum_pv / cum_v).otherwise(pl.col("vwap")).alias("cum_vwap"),
        pl.col("high").cum_max().alias("day_high_run"),
        pl.col("low").cum_min().alias("day_low_run"),
        pl.int_range(0, pl.len(), dtype=pl.Int64).alias("minute_idx"),
    )


def _load_rth_bars(
    settings: Settings, symbol: str, open_ns: int, close_ns: int
) -> pl.DataFrame:
    """This-session RTH 1-min bars in [open_ns, close_ns), ts-sorted."""
    return store.load_bars(settings.read_roots, FEED, symbol, start_ns=open_ns, end_ns=close_ns)


def _trailing_stats(
    settings: Settings,
    symbol: str,
    session: str,
    session_open_ns: int,
    cur_bar_count: int,
) -> tuple[float, float, float, np.ndarray] | None:
    """Compute (prev_close, sigma_d_bps, avg_range_bps, avg_cum_vol) from up to
    the 20 most-recent sessions dated strictly before `session`.

    Returns None when fewer than TRAILING_MIN_SESSIONS sessions carry data.
    Uses an end bound at session_open_ns so future sessions never leak in.
    """
    start_ns = session_open_ns - _CALENDAR_LOOKBACK_DAYS * 86400 * NS_PER_S
    df = store.load_bars(settings.read_roots, FEED, symbol, start_ns=start_ns, end_ns=session_open_ns)
    if df.height == 0:
        return None

    et = _et_cols(df)
    df = df.with_columns(
        et.dt.date().alias("_sdate"),
        (et.dt.hour().cast(pl.Int32) * 60 + et.dt.minute().cast(pl.Int32)).alias("_etmin"),
    ).filter((pl.col("_etmin") >= _RTH_OPEN_MIN) & (pl.col("_etmin") < _RTH_CLOSE_MIN))
    if df.height == 0:
        return None

    # Most-recent-first distinct prior session dates (all are < session by the
    # end bound); keep the newest TRAILING_LOOKBACK_SESSIONS with data.
    sdates = df.select("_sdate").unique().sort("_sdate", descending=True)["_sdate"].to_list()
    sdates = sdates[:TRAILING_LOOKBACK_SESSIONS]
    if len(sdates) < TRAILING_MIN_SESSIONS:
        return None

    closes: list[float] = []          # chronological (oldest -> newest)
    ranges_bps: list[float] = []
    cum_vol_arrays: list[np.ndarray] = []
    for sd in sorted(sdates):
        sub = df.filter(pl.col("_sdate") == sd).sort("ts")
        closes.append(float(sub["close"][-1]))
        cum_vol_arrays.append(sub["volume"].cum_sum().to_numpy().astype(np.float64))
        rng = sub.filter((pl.col("_etmin") >= _RANGE_START_MIN) & (pl.col("_etmin") < _RANGE_END_MIN))
        if rng.height > 0:
            first_open = float(rng.sort("ts")["open"][0])
            if first_open > 0:
                hi = float(rng["high"].max())
                lo = float(rng["low"].min())
                ranges_bps.append((hi - lo) / first_open * 1e4)

    prev_close = closes[-1]  # immediately preceding session's official close

    close_arr = np.asarray(closes, dtype=np.float64)
    rets = np.diff(close_arr) / close_arr[:-1]
    sigma_d_bps = float(np.std(rets, ddof=1) * 1e4) if rets.size >= 2 else 0.0

    avg_range_bps = float(np.mean(ranges_bps)) if ranges_bps else float("nan")

    max_len = max(a.size for a in cum_vol_arrays)
    target_len = max(max_len, cur_bar_count)
    sums = np.zeros(target_len, dtype=np.float64)
    counts = np.zeros(target_len, dtype=np.float64)
    for a in cum_vol_arrays:
        sums[: a.size] += a
        counts[: a.size] += 1.0
    avg_cum_vol = np.zeros(target_len, dtype=np.float64)
    nz = counts > 0
    avg_cum_vol[nz] = sums[nz] / counts[nz]
    # Pad the ragged tail (indices beyond the shortest prior sessions) forward.
    if not nz.all():
        last = 0.0
        for i in range(target_len):
            if nz[i]:
                last = avg_cum_vol[i]
            else:
                avg_cum_vol[i] = last

    return prev_close, sigma_d_bps, avg_range_bps, avg_cum_vol


def _load_event_bars(settings: Settings, symbol: str, open_ns: int, close_ns: int) -> pl.DataFrame | None:
    lf = store.scan_kind_multi(settings.read_roots, FEED, "event_bars1s", symbol)
    ev = lf.filter((pl.col("ts") >= open_ns) & (pl.col("ts") < close_ns)).sort("ts").collect()
    return ev if ev.height > 0 else None


def _is_monthly_opex(session: str) -> bool:
    """True iff `session` is the monthly equity-options expiry trading day.

    ffcal has no scalar helper; the F1 generator's own rule is the observed
    third-Friday, walked back to the prior business day on a holiday.
    """
    y, m, d = (int(x) for x in session.split("-"))
    sd = date(y, m, d)
    hols = ffcal.us_holidays(y) | ffcal.us_holidays(y - 1) | ffcal.us_holidays(y + 1)
    opex = ffcal.prev_bd(ffcal.nth_weekday(y, m, 4, 3), hols)  # 3rd Friday -> prior BD if holiday
    return sd == opex


def load_session_context(
    settings: Settings, symbol: str, session_iso: str
) -> SessionContext | None:
    """Build the SessionContext for (symbol, session_iso), or None when this
    session's RTH bars are missing/empty or trailing data is insufficient."""
    symbol = symbol.upper()
    try:
        sd = date.fromisoformat(session_iso)
    except ValueError:
        log.warning("session_context_bad_date", symbol=symbol, session=session_iso)
        return None
    try:
        open_dt, close_dt = calendar.session_bounds_utc(sd)
    except ValueError:
        log.warning("session_context_not_trading_day", symbol=symbol, session=session_iso)
        return None

    open_ns = int(open_dt.timestamp()) * NS_PER_S
    close_ns = int(close_dt.timestamp()) * NS_PER_S
    curfew_ts = close_ns - CURFEW_MIN_BEFORE_CLOSE * NS_PER_MIN

    raw = _load_rth_bars(settings, symbol, open_ns, close_ns)
    if raw.height == 0:
        log.info("session_context_no_bars", symbol=symbol, session=session_iso)
        return None
    bars = _derive_session_bars(raw)

    stats = _trailing_stats(settings, symbol, session_iso, open_ns, bars.height)
    if stats is None:
        log.info("session_context_insufficient_trailing", symbol=symbol, session=session_iso)
        return None
    prev_close, sigma_d_bps, avg_range_bps, avg_cum_vol = stats

    event_bars = _load_event_bars(settings, symbol, open_ns, close_ns)
    if event_bars is None:
        log.info("session_context_no_event_bars", symbol=symbol, session=session_iso)

    index_bars = None
    idx_sym = INDEX_MAP.get(symbol)
    if idx_sym is not None:
        ib = _load_rth_bars(settings, idx_sym, open_ns, close_ns)
        if ib.height > 0:
            index_bars = _derive_session_bars(ib)
        else:
            log.info("session_context_no_index_bars", symbol=symbol, index=idx_sym, session=session_iso)

    return SessionContext(
        symbol=symbol,
        session=session_iso,
        session_open_ts=open_ns,
        session_close_ts=close_ns,
        curfew_ts=curfew_ts,
        bars=bars,
        prev_close=prev_close,
        sigma_d_bps=sigma_d_bps,
        avg_range_1500_1545_bps=avg_range_bps,
        avg_cum_volume_by_minute=avg_cum_vol,
        event_bars=event_bars,
        index_bars=index_bars,
        is_monthly_opex=_is_monthly_opex(session_iso),
    )
