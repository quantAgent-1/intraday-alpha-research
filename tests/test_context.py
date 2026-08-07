"""SessionContext loader tests — synthetic lake, hand-checked trailing stats,
and a point-in-time no-future-leak assertion. No network."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np

from enginev51.config import Settings
from enginev51.data import calendar, store
from enginev51.events import context

NS = 1_000_000_000
FEED = "sip"
RANGE_LO_IDX = 330  # 15:00 ET open bar on a normal 09:30-16:00 session
RANGE_HI_IDX = 375  # exclusive (15:45)


def _flat_session_rows(day: date, base: float, *, with_range: bool, vol: float = 1000.0) -> list[dict]:
    open_dt, close_dt = calendar.session_bounds_utc(day)
    open_ns = int(open_dt.timestamp()) * NS
    n_min = (int(close_dt.timestamp()) - int(open_dt.timestamp())) // 60
    rows = []
    for i in range(n_min):
        hi = lo = base
        if with_range and RANGE_LO_IDX <= i < RANGE_HI_IDX:
            hi, lo = base + 0.1, base - 0.1
        rows.append(
            {"ts": open_ns + i * 60 * NS, "open": base, "high": hi, "low": lo,
             "close": base, "volume": vol, "trade_count": 1, "vwap": base}
        )
    return rows


def _write_symbol(raw_dir: Path, symbol: str, day_rows: dict[date, list[dict]]) -> None:
    by_month: dict[str, list[dict]] = {}
    for day, rows in day_rows.items():
        by_month.setdefault(store.month_key(day), []).extend(rows)
    for part, rows in by_month.items():
        store.write_partition(raw_dir, FEED, "bars1m", symbol, part, rows)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "data", legacy_data_dir=tmp_path / "nolegacy")


def _trading_days_before(day: date, n: int) -> list[date]:
    alld = calendar.trading_days(date(day.year - 1, 12, 1), day)
    idx = alld.index(day)
    return alld[idx - n : idx]


def _next_trading_day(day: date) -> date:
    alld = calendar.trading_days(day, date(day.year, day.month + 1 if day.month < 12 else 12, 28))
    return alld[alld.index(day) + 1]


def test_load_basic_and_derivations(tmp_path: Path) -> None:
    s = _settings(tmp_path)
    day = calendar.trading_days(date(2026, 1, 1), date(2026, 3, 15))[30]
    priors = _trading_days_before(day, 22)
    rows = {d: _flat_session_rows(d, 100.0, with_range=True) for d in priors}
    rows[day] = _flat_session_rows(day, 100.0, with_range=True)
    _write_symbol(s.raw_dir, "AMD", rows)

    ctx = context.load_session_context(s, "AMD", day.isoformat())
    assert ctx is not None
    # derived columns present + running semantics
    for col in ("cum_vwap", "day_high_run", "day_low_run", "minute_idx"):
        assert col in ctx.bars.columns
    assert ctx.bars["minute_idx"].to_list()[:3] == [0, 1, 2]
    # all-100 prior closes -> prev_close 100, sigma_d ~ 0
    assert abs(ctx.prev_close - 100.0) < 1e-9
    assert ctx.sigma_d_bps < 1e-6
    # 15:00-15:45 range = 0.2 on a 100 open = 20 bps
    assert abs(ctx.avg_range_1500_1545_bps - 20.0) < 1e-6
    # cumulative-volume vector: non-decreasing, length >= session bar count
    v = ctx.avg_cum_volume_by_minute
    assert v.shape[0] >= ctx.bars.height
    assert np.all(np.diff(v) >= -1e-9)
    assert abs(v[0] - 1000.0) < 1e-6  # one bar of 1000 vol


def test_missing_session_returns_none(tmp_path: Path) -> None:
    s = _settings(tmp_path)
    day = calendar.trading_days(date(2026, 1, 1), date(2026, 3, 15))[30]
    # write only priors, not `day` itself
    priors = _trading_days_before(day, 22)
    _write_symbol(s.raw_dir, "AMD", {d: _flat_session_rows(d, 100.0, with_range=True) for d in priors})
    assert context.load_session_context(s, "AMD", day.isoformat()) is None


def test_insufficient_trailing_returns_none(tmp_path: Path) -> None:
    s = _settings(tmp_path)
    day = calendar.trading_days(date(2026, 1, 1), date(2026, 3, 15))[30]
    priors = _trading_days_before(day, 5)  # < TRAILING_MIN_SESSIONS
    rows = {d: _flat_session_rows(d, 100.0, with_range=True) for d in priors}
    rows[day] = _flat_session_rows(day, 100.0, with_range=True)
    _write_symbol(s.raw_dir, "AMD", rows)
    assert context.load_session_context(s, "AMD", day.isoformat()) is None


def test_pit_no_future_leak(tmp_path: Path) -> None:
    """Trailing stats for S must be identical whether or not the store also
    contains a later session S+1 (no future leakage)."""
    day = calendar.trading_days(date(2026, 1, 1), date(2026, 3, 15))[30]
    priors = _trading_days_before(day, 22)
    nxt = _next_trading_day(day)

    # varied prior closes so sigma_d is a real, non-trivial number to compare
    def rows_for(d: date, base: float) -> list[dict]:
        return _flat_session_rows(d, base, with_range=True)

    base_rows: dict[date, list[dict]] = {}
    for k, d in enumerate(priors):
        base_rows[d] = rows_for(d, 100.0 + 0.1 * (k % 5))
    base_rows[day] = rows_for(day, 101.0)

    # lake WITHOUT S+1
    s1 = _settings(tmp_path / "a")
    _write_symbol(s1.raw_dir, "AMD", base_rows)
    ctx1 = context.load_session_context(s1, "AMD", day.isoformat())

    # lake WITH a future session S+1 added
    s2 = _settings(tmp_path / "b")
    with_future = dict(base_rows)
    with_future[nxt] = rows_for(nxt, 250.0)  # wild future close that must NOT leak
    _write_symbol(s2.raw_dir, "AMD", with_future)
    ctx2 = context.load_session_context(s2, "AMD", day.isoformat())

    assert ctx1 is not None and ctx2 is not None
    assert ctx1.prev_close == ctx2.prev_close
    assert ctx1.sigma_d_bps == ctx2.sigma_d_bps
    assert ctx1.avg_range_1500_1545_bps == ctx2.avg_range_1500_1545_bps
    assert np.array_equal(ctx1.avg_cum_volume_by_minute, ctx2.avg_cum_volume_by_minute)
    assert ctx1.sigma_d_bps > 0  # the varied priors gave a real vol


def test_quote_at_reads_event_bars(tmp_path: Path) -> None:
    s = _settings(tmp_path)
    day = calendar.trading_days(date(2026, 1, 1), date(2026, 3, 15))[30]
    priors = _trading_days_before(day, 22)
    rows = {d: _flat_session_rows(d, 100.0, with_range=True) for d in priors}
    rows[day] = _flat_session_rows(day, 100.0, with_range=True)
    _write_symbol(s.raw_dir, "AMD", rows)

    open_dt, _ = calendar.session_bounds_utc(day)
    open_ns = int(open_dt.timestamp()) * NS
    # two 1-second event bars with quotes at open and open+10s
    from enginev51.events.event_bars import EVENT_BARS_SCHEMA
    evb = []
    for sec, bid, ask in ((0, 99.9, 100.1), (10, 100.0, 100.2)):
        row = {c: 0.0 for c in EVENT_BARS_SCHEMA}
        row["ts"] = open_ns + sec * NS
        row["bid"], row["ask"] = bid, ask
        evb.append(row)
    import polars as pl
    p = store.partition_path(s.raw_dir, FEED, "event_bars1s", "AMD", day.isoformat())
    p.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(evb, schema=EVENT_BARS_SCHEMA).write_parquet(p)

    ctx = context.load_session_context(s, "AMD", day.isoformat())
    assert ctx is not None and ctx.event_bars is not None
    assert ctx.quote_at(open_ns + 5 * NS) == (99.9, 100.1)
    assert ctx.quote_at(open_ns + 20 * NS) == (100.0, 100.2)
    assert ctx.quote_at(open_ns - 5 * NS) is None
