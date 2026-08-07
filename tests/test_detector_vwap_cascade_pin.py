"""Hand-built fixtures for the vwap_magnet / cascade / expiry_pin detectors.

The SessionContext contract (events/context.py, authored in parallel) is
replicated here as a local dataclass so these tests do not depend on that
module's landing or on the session loader — every fixture is constructed
directly, per the task. Derived bar columns (cum_vwap, day_high_run,
day_low_run, minute_idx) are supplied explicitly in the fixtures: the detectors
READ these columns, they never recompute them, so full literal control is exact.

All timestamps are UTC epoch ns. ET times map through America/New_York (July =
EDT, UTC-4). A decision at 1-min bar i has ts = bars.ts[i] + 60s (the bar close).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
import pytest

from enginev51.events.detectors import cascade, expiry_pin, vwap_magnet

ET = ZoneInfo("America/New_York")
NS_PER_S = 1_000_000_000


def et_ns(y: int, mo: int, d: int, hh: int, mm: int) -> int:
    return int(datetime(y, mo, d, hh, mm, tzinfo=ET).timestamp()) * NS_PER_S


# --------------------------------------------------------------------------- #
# Local stand-in for events.context.SessionContext (the shared CONTRACT shape).
# --------------------------------------------------------------------------- #
@dataclass
class SessionContext:
    symbol: str
    session: str
    session_open_ts: int
    session_close_ts: int
    curfew_ts: int
    bars: pl.DataFrame
    prev_close: float = 100.0
    sigma_d_bps: float = 100.0
    avg_range_1500_1545_bps: float = 50.0
    avg_cum_volume_by_minute: np.ndarray = field(default_factory=lambda: np.zeros(1))
    event_bars: pl.DataFrame | None = None
    index_bars: pl.DataFrame | None = None
    is_monthly_opex: bool = False

    def quote_at(self, ts: int) -> tuple[float, float] | None:  # unused by these detectors
        return None


def _bars_frame(
    open_ns: int,
    *,
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    cum_vwaps: list[float],
    day_high: list[float],
    day_low: list[float],
    volumes: list[float],
) -> pl.DataFrame:
    n = len(closes)
    ts = [open_ns + k * 60 * NS_PER_S for k in range(n)]
    return pl.DataFrame(
        {
            "ts": ts,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
            "vwap": cum_vwaps,  # per-bar vwap unused by detectors; mirror is fine
            "cum_vwap": cum_vwaps,
            "day_high_run": day_high,
            "day_low_run": day_low,
            "minute_idx": list(range(n)),
        },
        schema_overrides={"ts": pl.Int64, "minute_idx": pl.Int64},
    )


# ======================================================================== #
# vwap_magnet
# ======================================================================== #
VOPEN = et_ns(2026, 7, 16, 9, 30)  # RTH open; bar 59 closes at 10:30 ET


def _vwap_ctx(n: int, signal_idx: list[int], *, day_hi=100.50, day_lo=99.50):
    closes = [100.00] * n
    cumv = [100.00] * n
    for s in signal_idx:
        closes[s] = 100.20  # dev = +20 bps vs cum_vwap 100.00
    opens = [100.00] * n
    highs = [100.50] * n
    lows = [99.50] * n
    return SessionContext(
        symbol="NVDA",
        session="2026-07-16",
        session_open_ts=VOPEN,
        session_close_ts=et_ns(2026, 7, 16, 16, 0),
        curfew_ts=et_ns(2026, 7, 16, 15, 50),
        bars=_bars_frame(
            VOPEN,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            cum_vwaps=cumv,
            day_high=[day_hi] * n,
            day_low=[day_lo] * n,
            volumes=[1000.0] * n,
        ),
    )


def test_vwap_active_exact_anchors():
    ctx = _vwap_ctx(65, signal_idx=[59])
    states = vwap_magnet.detect(ctx)
    assert len(states) == 1
    s = states[0]
    assert s.payer == "vwap_magnet"
    assert s.active is True
    assert s.direction == -1  # price above VWAP -> fade short
    assert s.horizon_min == 90
    # decision instant = bar-59 close
    assert s.ts == VOPEN + 59 * 60 * NS_PER_S + 60 * NS_PER_S
    assert datetime.fromtimestamp(s.ts // NS_PER_S, tz=ET).strftime("%H:%M") == "10:30"

    meta = dict(s.meta)
    # dev = 0.0020; V = 100.00; P0 = 100.20
    # dev_dist = 100*1.5*0.002 = 0.30 ; min_dist = 0.002*100.20 = 0.2004 ; stop = 100.20+0.30
    assert meta["stop_px"] == pytest.approx(100.50)
    assert meta["t0_px"] == pytest.approx(100.00)          # target = session VWAP
    assert meta["expected_gross_bps"] == pytest.approx(16.0)  # 0.8 * 20 bps
    assert meta["dev_bps"] == pytest.approx(20.0)

    dev_window = np.array([0.0] * 29 + [0.002])  # bars 30..59, dev included for bar 59
    sigma_dev = float(np.std(dev_window, ddof=1))
    assert meta["sigma_h_bps"] == pytest.approx(sigma_dev * 1e4 * math.sqrt(3.0))
    assert s.strength == pytest.approx(0.2)  # 20 / 100 ref


def test_vwap_range_day_filter_kills():
    # narrow day range -> |close-open| exceeds 0.35 * range -> trend day, stand down
    ctx = _vwap_ctx(65, signal_idx=[59], day_hi=100.21, day_lo=100.19)
    assert vwap_magnet.detect(ctx) == []


def test_vwap_rearm_suppresses_same_side():
    # signals at 10:30, 10:45 (within 60 min -> suppressed), 11:36 (re-armed)
    ctx = _vwap_ctx(130, signal_idx=[59, 74, 125])
    states = vwap_magnet.detect(ctx)
    assert len(states) == 2
    assert [s.direction for s in states] == [-1, -1]
    got = [s.ts for s in states]
    assert got == [
        VOPEN + 60 * 60 * NS_PER_S,   # bar 59 close = 10:30
        VOPEN + 126 * 60 * NS_PER_S,  # bar 125 close = 11:36
    ]


# ======================================================================== #
# cascade
# ======================================================================== #
COPEN = et_ns(2026, 7, 16, 9, 30)


def _cascade_bars():
    # 36 bars: flat 100 (0-20), steady 10-bar decline to 98.00 trough at bar 30,
    # gentle recovery (31-35) that sets no new low.
    closes = [100.00] * 21 + [
        99.80, 99.60, 99.40, 99.20, 99.00, 98.80, 98.60, 98.40, 98.20, 98.00,
    ] + [98.10, 98.20, 98.30, 98.40, 98.50]
    highs = [100.00] * 21 + [
        100.00, 99.80, 99.60, 99.40, 99.20, 99.00, 98.80, 98.60, 98.40, 98.20,
    ] + [98.10, 98.20, 98.30, 98.40, 98.50]
    lows = [100.00] * 21 + [
        99.80, 99.60, 99.40, 99.20, 99.00, 98.80, 98.60, 98.40, 98.20, 98.00,
    ] + [98.05, 98.15, 98.25, 98.35, 98.45]
    vols = [5000.0] * 21 + [20000.0] * 10 + [5000.0] * 5
    return closes, highs, lows, vols


def _cascade_event_bars(open_ns: int, decision_ts: int):
    n_sec = (decision_ts - open_ns) // NS_PER_S  # 2160 s
    ts = [open_ns + s * NS_PER_S for s in range(n_sec)]
    cutoff = n_sec - 300  # last 5 minutes
    spread = [10.0 if s >= cutoff else 2.0 for s in range(n_sec)]
    ofi = [100.0 if s >= cutoff else 0.0 for s in range(n_sec)]
    return pl.DataFrame(
        {"ts": ts, "spread_bps_close": spread, "ofi": ofi},
        schema_overrides={"ts": pl.Int64},
    )


def _cascade_ctx(with_event_bars: bool = True):
    closes, highs, lows, vols = _cascade_bars()
    n = len(closes)
    bars = _bars_frame(
        COPEN,
        opens=closes,  # opens irrelevant to cascade
        highs=highs,
        lows=lows,
        closes=closes,
        cum_vwaps=closes,
        day_high=[100.00] * n,
        day_low=[98.00] * n,
        volumes=vols,
    )
    avg_cum = np.array([1000.0 * (m + 1) for m in range(n)])  # flat 1000/min increment
    decision_ts = COPEN + 35 * 60 * NS_PER_S + 60 * NS_PER_S
    eb = _cascade_event_bars(COPEN, decision_ts) if with_event_bars else None
    return SessionContext(
        symbol="NVDA",
        session="2026-07-16",
        session_open_ts=COPEN,
        session_close_ts=et_ns(2026, 7, 16, 16, 0),
        curfew_ts=et_ns(2026, 7, 16, 15, 50),
        bars=bars,
        avg_cum_volume_by_minute=avg_cum,
        event_bars=eb,
    )


def test_cascade_full_sequence_exact_anchors():
    ctx = _cascade_ctx(with_event_bars=True)
    states = cascade.detect(ctx)
    assert len(states) == 1
    s = states[0]
    assert s.payer == "cascade"
    assert s.direction == 1  # against a down-flush = long
    assert s.horizon_min == 120
    assert s.ts == COPEN + 36 * 60 * NS_PER_S  # bar 35 close = 10:06 ET

    meta = dict(s.meta)
    # peak high 100.00, trough low 98.00 -> amplitude 2.00
    assert meta["amplitude"] == pytest.approx(2.00)
    assert meta["stop_px"] == pytest.approx(97.40)   # 98.00 - 0.3*2.00
    assert meta["t0_px"] == pytest.approx(98.764)    # 98.00 + 0.382*2.00
    assert meta["t1_px"] == pytest.approx(99.236)    # 98.00 + 0.618*2.00
    # expected_gross = 0.382*amplitude / close[35] * 1e4 ; close[35] = 98.50
    assert meta["expected_gross_bps"] == pytest.approx(0.382 * 2.0 / 98.50 * 1e4)

    closes = _cascade_bars()[0]
    lr = np.diff(np.log(np.array(closes)))  # 35 returns; window is the last 30
    sigma_30m = float(np.std(lr[-30:], ddof=1)) * math.sqrt(30)
    assert meta["sigma_h_bps"] == pytest.approx(sigma_30m * 1e4)
    # the flush must clear the 2.5-sigma bar for this to have emitted at all
    assert math.log(100.00 / 98.00) >= 2.5 * sigma_30m


def test_cascade_no_event_bars_emits_nothing():
    ctx = _cascade_ctx(with_event_bars=False)
    assert cascade.detect(ctx) == []


def test_cascade_spread_prong_required():
    # flat-spread event bars (no last-5-min widening) -> spread prong fails -> no state
    ctx = _cascade_ctx(with_event_bars=True)
    eb = ctx.event_bars.with_columns(pl.lit(2.0).alias("spread_bps_close"))
    ctx.event_bars = eb
    assert cascade.detect(ctx) == []


def test_cascade_ofi_prong_required():
    # OFI does not flip against the down-flush (stays negative) -> no state
    ctx = _cascade_ctx(with_event_bars=True)
    eb = ctx.event_bars.with_columns((pl.col("ofi") * -1.0).alias("ofi"))
    ctx.event_bars = eb
    assert cascade.detect(ctx) == []


# ======================================================================== #
# expiry_pin
# ======================================================================== #
POPEN = et_ns(2026, 7, 17, 9, 30)  # third-Friday monthly opex


def _pin_ctx(active_close: float = 200.45, *, opex: bool = True):
    # bars opening 12:55..13:10 ET; only the 12:59-open bar (decision 13:00) is
    # on a 5-min mark with an active price; others sit dead on the $200 strike.
    base_open = et_ns(2026, 7, 17, 12, 55)
    n = 16  # opens 12:55 .. 13:10
    closes = [200.00] * n
    closes[4] = active_close  # bar opening 12:59 -> decision 13:00
    bars = _bars_frame(
        base_open,
        opens=closes,
        highs=[c + 0.01 for c in closes],
        lows=[c - 0.01 for c in closes],
        closes=closes,
        cum_vwaps=closes,
        day_high=[201.0] * n,
        day_low=[199.0] * n,
        volumes=[1000.0] * n,
    )
    return SessionContext(
        symbol="NVDA",
        session="2026-07-17",
        session_open_ts=POPEN,
        session_close_ts=et_ns(2026, 7, 17, 16, 0),
        curfew_ts=et_ns(2026, 7, 17, 15, 50),
        bars=bars,
        is_monthly_opex=opex,
    )


def test_pin_active_exact_anchors():
    ctx = _pin_ctx(active_close=200.45)
    states = expiry_pin.detect(ctx)
    assert len(states) == 1
    s = states[0]
    assert s.payer == "expiry_pin"
    assert s.direction == -1  # strike 200.00 below price 200.45 -> short toward strike
    assert s.horizon_min == 170
    assert datetime.fromtimestamp(s.ts // NS_PER_S, tz=ET).strftime("%H:%M") == "13:00"

    meta = dict(s.meta)
    assert meta["strike"] == pytest.approx(200.00)         # grid $5, round(200.45/5)*5
    assert meta["t0_px"] == pytest.approx(200.00)
    assert meta["stop_px"] == pytest.approx(200.45 * 1.006)  # 0.6% beyond far side
    assert meta["expected_gross_bps"] == pytest.approx(0.45 / 200.45 * 1e4)
    assert meta["sigma_h_bps"] == 0.0


def test_pin_inactive_when_not_opex():
    ctx = _pin_ctx(active_close=200.45, opex=False)
    assert expiry_pin.detect(ctx) == []


def test_pin_inactive_dead_on_strike():
    # price exactly on the $200 strike -> |dist|/price = 0, below the 0.05% floor
    ctx = _pin_ctx(active_close=200.00)
    assert expiry_pin.detect(ctx) == []
