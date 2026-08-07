"""gap_mr and letf_window detector tests — hand-computed stops/targets/expected
values on synthetic sessions, plus the trend-day (extension) kill and the
below-threshold stand-down. No network."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from enginev51.config import Settings
from enginev51.data import calendar, store
from enginev51.events import context
from enginev51.events.detectors import gap_mr, letf_window

NS = 1_000_000_000
FEED = "sip"
RANGE_LO_IDX = 330  # 15:00 ET open bar (normal 09:30-16:00 session)
RANGE_HI_IDX = 375  # exclusive (15:45)
GAP_DECISION_IDX = 14   # 09:44 open bar -> 09:45 close decision
LETF_DECISION_IDX = 329  # 14:59 open bar -> 15:00 close decision


def _open_ns(day: date) -> int:
    open_dt, _ = calendar.session_bounds_utc(day)
    return int(open_dt.timestamp()) * NS


def _n_min(day: date) -> int:
    o, c = calendar.session_bounds_utc(day)
    return (int(c.timestamp()) - int(o.timestamp())) // 60


def _flat_rows(day: date, base: float, *, with_range: bool = False, vol: float = 1000.0) -> list[dict]:
    open_ns = _open_ns(day)
    rows = []
    for i in range(_n_min(day)):
        hi = lo = base
        if with_range and RANGE_LO_IDX <= i < RANGE_HI_IDX:
            hi, lo = base + 0.1, base - 0.1
        rows.append({"ts": open_ns + i * 60 * NS, "open": base, "high": hi, "low": lo,
                     "close": base, "volume": vol, "trade_count": 1, "vwap": base})
    return rows


def _apply(rows: list[dict], idx: int, **fields: float) -> None:
    rows[idx].update(fields)


def _write_symbol(raw_dir: Path, symbol: str, day_rows: dict[date, list[dict]]) -> None:
    by_month: dict[str, list[dict]] = {}
    for day, rows in day_rows.items():
        by_month.setdefault(store.month_key(day), []).extend(rows)
    for part, rows in by_month.items():
        store.write_partition(raw_dir, FEED, "bars1m", symbol, part, rows)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "data", legacy_data_dir=tmp_path / "nolegacy")


def _priors(day: date, n: int) -> list[date]:
    alld = calendar.trading_days(date(day.year - 1, 12, 1), day)
    return alld[alld.index(day) - n : alld.index(day)]


def _pick_day() -> date:
    return calendar.trading_days(date(2026, 1, 1), date(2026, 3, 15))[30]


# --------------------------------------------------------------------------- gap_mr

def _gap_session(day: date, open0: float, *, window_high: float, p945: float) -> list[dict]:
    """Flat session at open0 with a window (bars 0..14) high spike and a decision
    bar (idx 14) close of p945."""
    rows = _flat_rows(day, open0)
    _apply(rows, 5, high=window_high)                 # window extreme
    _apply(rows, GAP_DECISION_IDX, high=open0, low=p945, close=p945)
    return rows


def test_gap_active_hand_values(tmp_path: Path) -> None:
    s = _settings(tmp_path)
    day = _pick_day()
    rows = {d: _flat_rows(d, 100.0, with_range=True) for d in _priors(day, 22)}
    # gap up 50 bps: open0 = 100.5 vs prev_close 100; window high 100.55; p945 100.4
    rows[day] = _gap_session(day, 100.5, window_high=100.55, p945=100.4)
    _write_symbol(s.raw_dir, "AMD", rows)

    ctx = context.load_session_context(s, "AMD", day.isoformat())
    assert ctx is not None
    states = gap_mr.detect(ctx)
    assert len(states) == 1
    st = states[0]
    assert st.payer == "gap_mr"
    assert st.direction == -1  # fade a gap up
    assert st.horizon_min == 120
    assert st.ts == context.et_close_ns(day.isoformat(), 9, 45)
    meta = dict(st.meta)
    # stop = adverse extreme (window high 100.55) + 0.25*|gap|(0.5)=0.125 -> 100.675
    # min-stop 25bps from p945 100.4 = 100.651 -> the wider 100.675 wins
    assert abs(meta["stop_px"] - 100.675) < 1e-6
    assert abs(meta["t0_px"] - 100.2) < 1e-6      # halfway 100.4 -> 100
    assert abs(meta["t1_px"] - 100.0) < 1e-6      # prev_close
    # expected_gross = 0.5 * |100.4-100|/100.4 * 1e4
    assert abs(meta["expected_gross_bps"] - (0.5 * 0.4 / 100.4 * 1e4)) < 1e-6
    assert abs(meta["gap_bps"] - 50.0) < 1e-6


def test_gap_min_stop_distance_binds(tmp_path: Path) -> None:
    """When the adverse extreme sits close to the 09:45 price, the 25bps floor
    pushes the stop out."""
    s = _settings(tmp_path)
    day = _pick_day()
    rows = {d: _flat_rows(d, 100.0, with_range=True) for d in _priors(day, 22)}
    # gap up 50 bps but window barely moved (high 100.5) and p945 == 100.5:
    # raw stop = 100.5 + 0.125 = 100.625; floor = 100.5*1.0025 = 100.75 -> floor wins
    rows[day] = _gap_session(day, 100.5, window_high=100.5, p945=100.5)
    _write_symbol(s.raw_dir, "AMD", rows)
    ctx = context.load_session_context(s, "AMD", day.isoformat())
    assert ctx is not None
    meta = dict(gap_mr.detect(ctx)[0].meta)
    assert abs(meta["stop_px"] - 100.5 * 1.0025) < 1e-6


def test_gap_extension_kill(tmp_path: Path) -> None:
    s = _settings(tmp_path)
    day = _pick_day()
    rows = {d: _flat_rows(d, 100.0, with_range=True) for d in _priors(day, 22)}
    # window high 100.8 -> extension 0.3 > 0.35*|gap|(0.175) -> trend day -> stand down
    rows[day] = _gap_session(day, 100.5, window_high=100.8, p945=100.4)
    _write_symbol(s.raw_dir, "AMD", rows)
    ctx = context.load_session_context(s, "AMD", day.isoformat())
    assert ctx is not None
    assert gap_mr.detect(ctx) == []


def test_gap_below_threshold(tmp_path: Path) -> None:
    s = _settings(tmp_path)
    day = _pick_day()
    rows = {d: _flat_rows(d, 100.0, with_range=True) for d in _priors(day, 22)}
    # gap of 20 bps (< 30 bps floor) -> inactive
    rows[day] = _gap_session(day, 100.2, window_high=100.22, p945=100.15)
    _write_symbol(s.raw_dir, "AMD", rows)
    ctx = context.load_session_context(s, "AMD", day.isoformat())
    assert ctx is not None
    assert gap_mr.detect(ctx) == []


# --------------------------------------------------------------------------- letf_window

def _letf_lake(tmp_path: Path, day: date, *, index_close_1500: float) -> Settings:
    """NVDA (with trailing 15:00-15:45 range) + SOXX current session whose 15:00
    close encodes the index day-return."""
    s = _settings(tmp_path)
    nvda = {d: _flat_rows(d, 100.0, with_range=True) for d in _priors(day, 22)}
    nvda[day] = _flat_rows(day, 100.0, with_range=True)  # NVDA price flat at 100
    _write_symbol(s.raw_dir, "NVDA", nvda)
    # SOXX current session only: open0 = 100, decision (idx 329) close encodes r
    soxx = _flat_rows(day, 100.0)
    _apply(soxx, LETF_DECISION_IDX, close=index_close_1500)
    _write_symbol(s.raw_dir, "SOXX", {day: soxx})
    return s


def test_letf_long_hand_values(tmp_path: Path) -> None:
    day = _pick_day()
    # SOXX +1% on the day (100 -> 101): demand > 0 -> long
    s = _letf_lake(tmp_path, day, index_close_1500=101.0)
    ctx = context.load_session_context(s, "NVDA", day.isoformat())
    assert ctx is not None and ctx.index_bars is not None
    states = letf_window.detect(ctx)
    assert len(states) == 1
    st = states[0]
    assert st.payer == "letf_window" and st.direction == 1 and st.horizon_min == 55
    assert st.ts == context.et_close_ns(day.isoformat(), 15, 0)
    meta = dict(st.meta)
    # expected_gross = min(10 * 0.01/0.005, 30) = 20
    assert abs(meta["expected_gross_bps"] - 20.0) < 1e-6
    # stop = p1500(100) * (1 - 1.2 * avg_range(20bps)/1e4) = 100 * (1 - 0.0024)
    assert abs(meta["stop_px"] - 100.0 * (1 - 1.2 * 20.0 / 1e4)) < 1e-6
    assert abs(meta["sigma_h_bps"] - 20.0) < 1e-6
    assert abs(meta["index_ret_bps"] - 100.0) < 1e-6  # +1% = 100 bps


def test_letf_short_hand_values(tmp_path: Path) -> None:
    day = _pick_day()
    # SOXX -1% on the day (100 -> 99): demand < 0 -> short
    s = _letf_lake(tmp_path, day, index_close_1500=99.0)
    ctx = context.load_session_context(s, "NVDA", day.isoformat())
    assert ctx is not None
    states = letf_window.detect(ctx)
    assert len(states) == 1
    st = states[0]
    assert st.direction == -1
    meta = dict(st.meta)
    # short stop sits ABOVE price: 100 * (1 + 0.0024)
    assert abs(meta["stop_px"] - 100.0 * (1 + 1.2 * 20.0 / 1e4)) < 1e-6
    assert abs(meta["expected_gross_bps"] - 20.0) < 1e-6


def test_letf_below_threshold(tmp_path: Path) -> None:
    day = _pick_day()
    # SOXX +0.3% (< 0.5%) -> inactive
    s = _letf_lake(tmp_path, day, index_close_1500=100.3)
    ctx = context.load_session_context(s, "NVDA", day.isoformat())
    assert ctx is not None
    assert letf_window.detect(ctx) == []


def test_letf_builds_valid_plan(tmp_path: Path) -> None:
    """The emitted state must construct a real TradePlan (stop on the right side,
    market entry, no target) through the registered constructor."""
    from enginev51.plans.constructor import build_plan

    day = _pick_day()
    s = _letf_lake(tmp_path, day, index_close_1500=101.0)
    ctx = context.load_session_context(s, "NVDA", day.isoformat())
    st = letf_window.detect(ctx)[0]
    plan = build_plan(st, bid=99.99, ask=100.01, rt_cost_bps=4.0,
                      curfew_ts=ctx.curfew_ts, plan_seq=0)
    assert plan is not None
    assert plan.payer == "letf_window" and plan.entry.type == "market"
    assert plan.stop.price < 100.01  # long stop below entry ref
    assert plan.targets == ()
