"""M18 §6.5 — fill models + sizing (hand-computed)."""

from __future__ import annotations

import numpy as np

from enginev51.reversion.fills import (
    MAKER_CANCEL_BARS,
    keep_hash_50,
    maker_fill_bar,
    size_and_levels,
)


def _low(vals):
    return np.array(vals, dtype=np.float64)


def test_maker_long_touch_vs_through():
    # limit 100. px_low: bar0..4 = [101, 100, 99.5, 98, 97]; window opens AFTER t0=0.
    px_low = _low([101.0, 100.0, 99.5, 98.0, 97.0])
    px_high = px_low + 0.5
    # touch (<=100): first bar in (0, ...] with low<=100 → bar1 (100.0).
    assert maker_fill_bar(px_low, px_high, 0, +1, 100.0, strict=False) == 1
    # through (<100): bar1 is exactly 100 (no), bar2 99.5 (<100) → bar2.
    assert maker_fill_bar(px_low, px_high, 0, +1, 100.0, strict=True) == 2


def test_maker_short_touch_vs_through():
    px_high = _low([99.0, 100.0, 100.5, 101.0])
    px_low = px_high - 0.5
    # touch (>=100): bar1 (100.0). through (>100): bar2 (100.5).
    assert maker_fill_bar(px_low, px_high, 0, -1, 100.0, strict=False) == 1
    assert maker_fill_bar(px_low, px_high, 0, -1, 100.0, strict=True) == 2


def test_maker_no_touch_and_place_bar_excluded():
    px_low = _low([100.0, 101.0, 102.0, 103.0])  # never dips to 100 AFTER bar0
    px_high = px_low + 0.5
    # bar0 low==100 would touch, but the window opens STRICTLY after t0=0 → excluded.
    assert maker_fill_bar(px_low, px_high, 0, +1, 100.0, strict=False) is None


def test_maker_cancel_after_60s():
    # Touch only arrives at bar 61 (> cancel window of 60) → cancelled (None).
    n = 80
    px_low = np.full(n, 200.0)
    px_low[61] = 99.0
    px_high = px_low + 0.5
    assert maker_fill_bar(px_low, px_high, 0, +1, 100.0, cancel_bars=MAKER_CANCEL_BARS) is None
    # A touch AT the last in-window bar (t0+60) fills.
    px_low2 = np.full(n, 200.0)
    px_low2[60] = 99.0
    assert maker_fill_bar(px_low2, px_low2 + 0.5, 0, +1, 100.0, cancel_bars=MAKER_CANCEL_BARS) == 60


def test_size_and_levels_bps_floor_governs():
    # entry 100, sigma 0.5: stop_dist = max(100·75bps=0.75, 1.5·0.5=0.75) = 0.75.
    # shares = floor(200/0.75) = 266; hard_stop long = floor_tick(100-0.75)=99.25;
    # tp long = floor_tick(100 + 100·10bps=0.10) = 100.10.
    sz = size_and_levels(100.0, +1, 0.5)
    assert sz.shares == 266
    assert sz.hard_stop == 99.25
    assert abs(sz.take_profit - 100.10) < 1e-9
    assert abs(sz.stop_dist_usd - 0.75) < 1e-9


def test_size_and_levels_vol_governs_and_short_side():
    # entry 100, sigma 2.0: stop_dist = max(0.75, 3.0) = 3.0; shares = floor(200/3)=66.
    # short hard_stop = ceil_tick(100+3)=103.0; short tp = ceil_tick(100-0.1)=99.90.
    sz = size_and_levels(100.0, -1, 2.0)
    assert sz.shares == 66
    assert sz.hard_stop == 103.0
    assert abs(sz.take_profit - 99.90) < 1e-9


def test_size_and_levels_share_clamp():
    # entry 5, sigma 0: stop_dist = 5·75bps = 0.0375; 200/0.0375 = 5333 → clamp 5000.
    sz = size_and_levels(5.0, +1, 0.0)
    assert sz.shares == 5000


def test_keep_hash_50_deterministic_and_balanced():
    a = keep_hash_50("TSLA", 1234567890)
    assert keep_hash_50("TSLA", 1234567890) is a  # deterministic
    kept = sum(keep_hash_50("MU", t) for t in range(2000))
    assert 850 < kept < 1150  # ~50 % split
