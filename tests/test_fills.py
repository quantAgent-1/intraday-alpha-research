"""Hand-computed tests for the PIT fill kernel in enginev51.backtest.fills.

Every expected value below is derived by hand from the arrays declared in the
test (arithmetic shown in comments), never read back from the implementation.

Conventions used throughout:
  * searchsorted(a, x, side="right") = number of elements <= x (first index
    strictly past x). prevailing_idx = that minus 1.
  * Fill/trigger windows open STRICTLY AFTER the anchor (place/arm/from ts) and
    close INCLUSIVELY at the bound (cancel/to ts).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from enginev51.backtest.fills import (
    FRAC_PER_BP,
    limit_fill_ts,
    market_fill,
    prevailing_idx,
    prevailing_mid,
    stop_trigger_ts,
    target_fill_ts,
)


def _ts(*vals: int) -> np.ndarray:
    return np.array(vals, dtype=np.int64)


def _px(*vals: float) -> np.ndarray:
    return np.array(vals, dtype=np.float64)


# --------------------------------------------------------------------------
# 1. prevailing_idx / prevailing_mid guard against the arr[-1] wrap
# --------------------------------------------------------------------------
def test_prevailing_before_first_quote_is_guarded():
    # Three quotes at ts 100, 200, 300.
    q_ts = _ts(100, 200, 300)
    q_bid = _px(10.0, 20.0, 30.0)
    q_ask = _px(12.0, 22.0, 32.0)
    # Last quote's mid = 0.5*(30+32) = 31.0 -- the TRAP value an unguarded
    # arr[-1] would return for a t before the first quote.
    trap_last_mid = 31.0

    # t = 50 precedes the first quote (100). searchsorted(right)=0 -> idx -1.
    assert prevailing_idx(q_ts, 50) == -1
    result = prevailing_mid(q_ts, q_bid, q_ask, 50)
    assert math.isnan(result)  # nan, NOT the wrapped last mid
    assert result != trap_last_mid

    # Sanity: at-or-after first quote resolves normally.
    # t=250 -> searchsorted(right)=2 -> idx 1 -> mid 0.5*(20+22)=21.0
    assert prevailing_idx(q_ts, 250) == 1
    assert prevailing_mid(q_ts, q_bid, q_ask, 250) == 21.0
    # t exactly at a quote ts is at-or-before: t=100 -> idx 0 -> mid 0.5*(10+12)=11.0
    assert prevailing_mid(q_ts, q_bid, q_ask, 100) == 11.0


# --------------------------------------------------------------------------
# 2. limit_fill_ts BUY (side=+1): fills need price <= limit (touch) / < limit (strict)
# --------------------------------------------------------------------------
def test_limit_buy_at_limit_fills_touch_only():
    # Single print at ts=10, price exactly at the limit 100.
    t_ts = _ts(10)
    t_price = _px(100.0)
    # place_ts=5 (print at 10 is strictly after), cancel_ts=100 (10 <= 100).
    # strict: 100 < 100 -> False -> no fill.
    assert limit_fill_ts(t_ts, t_price, 5, 100, 100.0, side=+1, strict=True) is None
    # touch: 100 <= 100 -> True -> fills at ts 10.
    assert limit_fill_ts(t_ts, t_price, 5, 100, 100.0, side=+1, strict=False) == 10


def test_limit_buy_below_limit_fills_both():
    t_ts = _ts(10)
    t_price = _px(99.0)  # 99 < 100 and 99 <= 100
    assert limit_fill_ts(t_ts, t_price, 5, 100, 100.0, side=+1, strict=True) == 10
    assert limit_fill_ts(t_ts, t_price, 5, 100, 100.0, side=+1, strict=False) == 10


def test_limit_buy_print_at_place_ts_never_fills():
    # Print sits exactly at place_ts=10; window opens STRICTLY after -> excluded.
    t_ts = _ts(10)
    t_price = _px(50.0)  # deep below the limit, would fill if the window let it
    # lo = searchsorted([10],10,right)=1, hi = searchsorted([10],100,right)=1 -> empty.
    assert limit_fill_ts(t_ts, t_price, 10, 100, 100.0, side=+1, strict=True) is None


def test_limit_buy_prints_after_cancel_never_fill():
    # Only print is at ts=20, past cancel_ts=15.
    t_ts = _ts(20)
    t_price = _px(50.0)
    # lo = searchsorted([20],5,right)=0, hi = searchsorted([20],15,right)=0 -> None.
    assert limit_fill_ts(t_ts, t_price, 5, 15, 100.0, side=+1, strict=True) is None


def test_limit_buy_earliest_qualifying_print_across_window():
    # ts:   10   20   30   40   50
    # px:    99  100   98   97  ...
    t_ts = _ts(10, 20, 30, 40, 50)
    t_price = _px(99.0, 100.0, 98.0, 97.0, 96.0)
    # place_ts=10 (excl), cancel_ts=40 (incl): window = ts 20,30,40.
    # strict price<100: 100(no), 98(YES@30) -> 30.
    assert limit_fill_ts(t_ts, t_price, 10, 40, 100.0, side=+1, strict=True) == 30
    # touch price<=100: 100(YES@20) -> 20.
    assert limit_fill_ts(t_ts, t_price, 10, 40, 100.0, side=+1, strict=False) == 20


# --------------------------------------------------------------------------
# 3. limit_fill_ts SELL (side=-1) mirror: price >= limit (touch) / > limit (strict)
# --------------------------------------------------------------------------
def test_limit_sell_mirror():
    # At-limit print: 100 at ts=10.
    t_ts = _ts(10)
    at = _px(100.0)
    # strict: 100 > 100 -> False; touch: 100 >= 100 -> True@10.
    assert limit_fill_ts(t_ts, at, 5, 100, 100.0, side=-1, strict=True) is None
    assert limit_fill_ts(t_ts, at, 5, 100, 100.0, side=-1, strict=False) == 10
    # Above-limit print: 101 fills strict and touch.
    above = _px(101.0)
    assert limit_fill_ts(t_ts, above, 5, 100, 100.0, side=-1, strict=True) == 10
    assert limit_fill_ts(t_ts, above, 5, 100, 100.0, side=-1, strict=False) == 10


# --------------------------------------------------------------------------
# 4. market_fill both sides + guard
# --------------------------------------------------------------------------
def test_market_fill_both_sides_exact():
    q_ts = _ts(100, 200)
    q_bid = _px(10.0, 20.0)
    q_ask = _px(12.0, 22.0)
    # exec_ts=250 -> prevailing idx 1: bid=20, ask=22, mid=0.5*(20+22)=21.0
    # slip_bps=50 -> slip = 50 * 1e-4 = 0.005
    assert FRAC_PER_BP == 1e-4
    # BUY lifts ask*(1+slip) = 22 * 1.005 = 22.11
    buy = market_fill(q_ts, q_bid, q_ask, 250, side=+1, slip_bps=50.0)
    assert buy is not None
    assert buy[0] == pytest.approx(22.11)
    assert buy[1] == pytest.approx(21.0)
    # SELL hits bid*(1-slip) = 20 * 0.995 = 19.9
    sell = market_fill(q_ts, q_bid, q_ask, 250, side=-1, slip_bps=50.0)
    assert sell is not None
    assert sell[0] == pytest.approx(19.9)
    assert sell[1] == pytest.approx(21.0)


def test_market_fill_before_first_quote_is_none():
    q_ts = _ts(100, 200)
    q_bid = _px(10.0, 20.0)
    q_ask = _px(12.0, 22.0)
    # exec_ts=50 precedes first quote -> idx -1 -> None (never crosses future quote).
    assert market_fill(q_ts, q_bid, q_ask, 50, side=+1, slip_bps=50.0) is None


# --------------------------------------------------------------------------
# 5. stop_trigger_ts LONG (side=+1): first quote with bid <= stop
# --------------------------------------------------------------------------
def test_stop_long_triggers_on_first_bid_at_or_below():
    # ts:  10    20    30
    # bid: 101  100.5 99.9   (stop=100)
    q_ts = _ts(10, 20, 30)
    q_bid = _px(101.0, 100.5, 99.9)
    q_ask = q_bid + 0.1  # asks irrelevant for a long stop
    # bid<=100: 101(no),100.5(no),99.9(YES@30) -> decision ts 30.
    assert stop_trigger_ts(q_ts, q_bid, q_ask, 0, 100, 100.0, side=+1) == 30


def test_stop_long_gap_through_returns_decision_ts_unclamped():
    # bid gaps 101 -> 95 (straight through stop=100) at ts 10,20.
    q_ts = _ts(10, 20)
    q_bid = _px(101.0, 95.0)
    q_ask = q_bid + 0.1
    # 95 <= 100 first True at index 1 -> decision ts = 20.
    # The function returns only the quote TS: no price clamping to stop happens.
    got = stop_trigger_ts(q_ts, q_bid, q_ask, 0, 100, 100.0, side=+1)
    assert got == 20
    assert isinstance(got, int)


def test_stop_long_already_through_at_arm_decides_at_arm():
    # B3 (code review 2026-07-28): the book is ALREADY through the stop at the arm
    # instant and no later quote ever arrives. A stop is a LEVEL, not a transition:
    # the prevailing quote at from_ts (ts 10, bid 95 <= stop 100) triggers, so the
    # decision ts is the arm instant itself.
    # PRE-FIX this returned None (window opened strictly after from_ts, nothing
    # after it), and the caller rode the position to hold/curfew.
    q_ts = _ts(10)
    q_bid = _px(95.0)
    q_ask = q_bid + 0.1
    assert stop_trigger_ts(q_ts, q_bid, q_ask, 10, 100, 100.0, side=+1) == 10


def test_stop_long_already_through_before_arm_decides_at_arm():
    # The only quote (ts 5) precedes the arm (ts 40) and is through the stop:
    # prevailing_idx(q_ts, 40) = 0 -> bid 95 <= 100 -> decision at from_ts = 40,
    # NOT at the quote's own (pre-arm) ts. Latency is the caller's business.
    q_ts = _ts(5)
    q_bid = _px(95.0)
    q_ask = q_bid + 0.1
    assert stop_trigger_ts(q_ts, q_bid, q_ask, 40, 100, 100.0, side=+1) == 40


def test_stop_short_already_through_at_arm_decides_at_arm():
    # SHORT mirror: prevailing ask 105 >= stop 100 at the arm -> decision at arm.
    q_ts = _ts(10)
    q_ask = _px(105.0)
    q_bid = q_ask - 0.1
    assert stop_trigger_ts(q_ts, q_bid, q_ask, 10, 100, 100.0, side=-1) == 10


def test_stop_prevailing_not_through_still_waits_for_a_later_quote():
    # The level check must not fire when the arm-instant book is INSIDE the stop:
    # prevailing at from_ts=10 is bid 101 > 100 -> no trigger there; the first
    # strictly-later quote through the stop (ts 30, bid 99.9) decides. Unchanged
    # behaviour, and the quote at from_ts is not double-counted.
    q_ts = _ts(10, 20, 30)
    q_bid = _px(101.0, 100.5, 99.9)
    q_ask = q_bid + 0.1
    assert stop_trigger_ts(q_ts, q_bid, q_ask, 10, 100, 100.0, side=+1) == 30


def test_stop_no_quote_before_arm_is_none():
    # No quote precedes the arm and none lies in the window -> None (the level
    # check must not wrap to the future via arr[-1], and nothing else qualifies).
    q_ts = _ts(500)
    q_bid = _px(95.0)
    q_ask = q_bid + 0.1
    assert stop_trigger_ts(q_ts, q_bid, q_ask, 10, 100, 100.0, side=+1) is None


def test_stop_long_to_ts_inclusive():
    # Triggering quote sits exactly at to_ts -> included.
    q_ts = _ts(10)
    q_bid = _px(95.0)
    q_ask = q_bid + 0.1
    # from_ts=0 -> lo=0; to_ts=10 -> hi=searchsorted([10],10,right)=1 -> considered.
    assert stop_trigger_ts(q_ts, q_bid, q_ask, 0, 10, 100.0, side=+1) == 10


# --------------------------------------------------------------------------
# 6. stop_trigger_ts SHORT (side=-1) mirror: first quote with ask >= stop
# --------------------------------------------------------------------------
def test_stop_short_triggers_on_first_ask_at_or_above():
    # ts:  10   20    30
    # ask: 99  99.5 100.1   (stop=100)
    q_ts = _ts(10, 20, 30)
    q_ask = _px(99.0, 99.5, 100.1)
    q_bid = q_ask - 0.1
    # ask>=100: 99(no),99.5(no),100.1(YES@30) -> 30.
    assert stop_trigger_ts(q_ts, q_bid, q_ask, 0, 100, 100.0, side=-1) == 30


# --------------------------------------------------------------------------
# 7. target_fill_ts LONG strict (resting SELL): print strictly above fills
# --------------------------------------------------------------------------
def test_target_long_strict_vs_touch():
    # Resting sell at 105. Prints: 105.0 @10, 106.0 @20.
    t_ts = _ts(10, 20)
    t_price = _px(105.0, 106.0)
    # strict price>105: 105(no),106(YES@20) -> 20.
    assert target_fill_ts(t_ts, t_price, 0, 100, 105.0, side=+1, strict=True) == 20
    # At-price print alone under touch: 105>=105 -> fills @10.
    single = _px(105.0)
    assert target_fill_ts(_ts(10), single, 0, 100, 105.0, side=+1, strict=False) == 10
    # ...but strict at-price does not fill.
    assert target_fill_ts(_ts(10), single, 0, 100, 105.0, side=+1, strict=True) is None


def test_target_short_mirror():
    # SHORT exit = resting BUY at 105; print strictly below fills (< / <=).
    t_ts = _ts(10, 20)
    t_price = _px(105.0, 104.0)
    # strict price<105: 105(no),104(YES@20) -> 20.
    assert target_fill_ts(t_ts, t_price, 0, 100, 105.0, side=-1, strict=True) == 20
    # at-price touch fills, strict does not.
    single = _px(105.0)
    assert target_fill_ts(_ts(10), single, 0, 100, 105.0, side=-1, strict=False) == 10
    assert target_fill_ts(_ts(10), single, 0, 100, 105.0, side=-1, strict=True) is None


# --------------------------------------------------------------------------
# 8. Empty arrays / inverted (hi<=lo) windows -> None / nan / -1, never raise
# --------------------------------------------------------------------------
def test_empty_arrays_everywhere():
    e_ts = np.array([], dtype=np.int64)
    e_px = np.array([], dtype=np.float64)

    # prevailing: searchsorted on empty = 0 -> idx -1 -> nan.
    assert prevailing_idx(e_ts, 123) == -1
    assert math.isnan(prevailing_mid(e_ts, e_px, e_px, 123))

    assert limit_fill_ts(e_ts, e_px, 0, 100, 100.0, side=+1) is None
    assert limit_fill_ts(e_ts, e_px, 0, 100, 100.0, side=-1) is None
    assert market_fill(e_ts, e_px, e_px, 123, side=+1, slip_bps=50.0) is None
    assert stop_trigger_ts(e_ts, e_px, e_px, 0, 100, 100.0, side=+1) is None
    assert stop_trigger_ts(e_ts, e_px, e_px, 0, 100, 100.0, side=-1) is None
    assert target_fill_ts(e_ts, e_px, 0, 100, 100.0, side=+1) is None
    assert target_fill_ts(e_ts, e_px, 0, 100, 100.0, side=-1) is None


def test_inverted_windows_return_none():
    # Non-empty arrays, but hi <= lo because the window is inverted/degenerate.
    t_ts = _ts(10, 20, 30)
    t_price = _px(50.0, 50.0, 50.0)
    # place_ts=30 >= cancel_ts=20: lo>=hi -> None.
    assert limit_fill_ts(t_ts, t_price, 30, 20, 100.0, side=+1) is None
    assert target_fill_ts(t_ts, t_price, 30, 20, 100.0, side=+1) is None

    q_ts = _ts(10, 20, 30)
    q_bid = _px(50.0, 50.0, 50.0)
    q_ask = _px(60.0, 60.0, 60.0)
    # from_ts=30 > to_ts=5: inverted window -> None. This also pins the B3 level
    # check to the window: the prevailing quote at 30 IS through the stop
    # (bid 50 <= 100), and an unguarded level check would return 30 > to_ts.
    assert stop_trigger_ts(q_ts, q_bid, q_ask, 30, 5, 100.0, side=+1) is None
    # Degenerate equal bounds with everything at/after: from_ts=to_ts=5 (both < first ts)
    # -> no prevailing quote at 5, lo=0, hi=0 -> None.
    assert stop_trigger_ts(q_ts, q_bid, q_ask, 5, 5, 100.0, side=+1) is None
