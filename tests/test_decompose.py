"""Hand-computed tests for backtest/decompose.py.

Every expected value below is derived from raw literals (not the module's own
intermediates) so the tests cannot merely echo the implementation. The four
components are, per the module:

    k               = side / entry_vwap * 1e4
    fees_bps        = sec_taf * (sell_notional / entry_notional)
    net_bps         = side*(exit_vwap - entry_vwap)/entry_vwap*1e4 - fees_bps
    gross_mid_bps   = k * (exit_mid_dec - entry_mid_dec)
    latency_drag    = k * ((en_mid_act-en_mid_dec) - (ex_mid_act-ex_mid_dec))
    spread_cost     = k * ((en_vwap-en_mid_act)   - (ex_vwap-ex_mid_act))
    identity        = net - (gross - latency - spread - fees)  MUST be ~0
"""

from __future__ import annotations

import math
import warnings
from types import SimpleNamespace

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from enginev51.backtest.decompose import (
    PlanPnl,
    plan_pnl,
    session_summary,
)
from enginev51.backtest.fills import Fill

LONG = 1
SHORT = -1


def mkfill(price: float, mid_dec: float, mid_act: float, qty: float = 1.0) -> Fill:
    """Build a Fill; only price/qty/mids matter to decompose."""
    return Fill(
        ts=0,
        price=price,
        qty_frac=qty,
        leg="x",
        decision_ts=0,
        mid_at_decision=mid_dec,
        mid_at_action=mid_act,
        maker=False,
    )


TOL = 1e-9


def test_single_fill_long_round_trip() -> None:
    # entry vwap=100.05  mid_dec=100.00  mid_act=100.01  notional=100.05
    # exit  vwap=100.95  mid_dec=101.00  mid_act=100.99  notional=100.95
    en = mkfill(100.05, 100.00, 100.01, 1.0)
    ex = mkfill(100.95, 101.00, 100.99, 1.0)
    r = plan_pnl(LONG, (en,), (ex,), sec_taf_sell_bps=0.3)

    # fees = 0.3 * (100.95 / 100.05)   (long -> sell notional is the exit leg)
    exp_fees = 0.3 * (100.95 / 100.05)
    # net + fees = (100.95 - 100.05)/100.05 * 1e4
    exp_net = (100.95 - 100.05) / 100.05 * 1e4 - exp_fees
    # gross = (101.00 - 100.00)/100.05 * 1e4
    exp_gross = (101.00 - 100.00) / 100.05 * 1e4
    # latency = ((100.01-100.00) - (100.99-101.00))/100.05 * 1e4
    exp_lat = ((100.01 - 100.00) - (100.99 - 101.00)) / 100.05 * 1e4
    # spread = ((100.05-100.01) - (100.95-100.99))/100.05 * 1e4
    exp_spread = ((100.05 - 100.01) - (100.95 - 100.99)) / 100.05 * 1e4

    assert r.fees_bps == pytest.approx(exp_fees, abs=TOL)
    assert r.net_bps == pytest.approx(exp_net, abs=TOL)
    assert r.gross_mid_bps == pytest.approx(exp_gross, abs=TOL)
    assert r.latency_drag_bps == pytest.approx(exp_lat, abs=TOL)
    assert r.spread_cost_bps == pytest.approx(exp_spread, abs=TOL)
    # net + fees identity check on raw price move
    assert (r.net_bps + r.fees_bps) == pytest.approx(
        (100.95 - 100.05) / 100.05 * 1e4, abs=TOL
    )
    assert r.identity_residual_bps == pytest.approx(0.0, abs=TOL)


def test_maker_entry_negative_spread() -> None:
    # Long entry filled BELOW mid_act (100.00 < 100.02) -> passive/maker earn.
    # Exit is placed exactly at its mid_act (101.00 == 101.00) so the exit
    # spread term is zero and the entry earn is isolated.
    #   spread = k * ((100.00-100.02) - (101.00-101.00))
    #          = (1/100.00*1e4) * (-0.02) < 0
    en = mkfill(100.00, 100.00, 100.02, 1.0)
    ex = mkfill(101.00, 101.00, 101.00, 1.0)
    r = plan_pnl(LONG, (en,), (ex,), sec_taf_sell_bps=0.0)

    exp_spread = ((100.00 - 100.02) - (101.00 - 101.00)) / 100.00 * 1e4
    assert exp_spread < 0.0
    assert r.spread_cost_bps == pytest.approx(exp_spread, abs=TOL)
    assert r.spread_cost_bps < 0.0
    assert r.identity_residual_bps == pytest.approx(0.0, abs=TOL)


def test_partial_exits_qty_weighted() -> None:
    # Entry: single fill 1.0 @ 100.00 (mid_dec 100.00, mid_act 100.00).
    # Exit legs (qtys sum to 1.0):
    #   0.5 @ 101.5  mid_dec 101.4  mid_act 101.45
    #   0.3 @ 102.0  mid_dec 101.9  mid_act 101.95
    #   0.2 @ 100.8  mid_dec 100.7  mid_act 100.75
    en = mkfill(100.00, 100.00, 100.00, 1.0)
    ex0 = mkfill(101.5, 101.4, 101.45, 0.5)
    ex1 = mkfill(102.0, 101.9, 101.95, 0.3)
    ex2 = mkfill(100.8, 100.7, 100.75, 0.2)
    r = plan_pnl(LONG, (en,), (ex0, ex1, ex2), sec_taf_sell_bps=0.2)

    # exit filled fraction F = 0.5+0.3+0.2 = 1.0
    F = 0.5 + 0.3 + 0.2
    # exit notional = 101.5*0.5 + 102.0*0.3 + 100.8*0.2
    #              = 50.75 + 30.6 + 20.16 = 101.51
    ex_notional = 101.5 * 0.5 + 102.0 * 0.3 + 100.8 * 0.2
    ex_vwap = ex_notional / F
    # exit mid_dec = (101.4*0.5 + 101.9*0.3 + 100.7*0.2)/1.0
    #             = 50.7 + 30.57 + 20.14 = 101.41
    ex_mid_dec = (101.4 * 0.5 + 101.9 * 0.3 + 100.7 * 0.2) / F
    # exit mid_act = (101.45*0.5 + 101.95*0.3 + 100.75*0.2)/1.0
    #             = 50.725 + 30.585 + 20.15 = 101.46
    ex_mid_act = (101.45 * 0.5 + 101.95 * 0.3 + 100.75 * 0.2) / F

    # entry vwap/mids all 100.00, entry notional 100.00
    exp_fees = 0.2 * (ex_notional / 100.00)
    exp_net = (ex_vwap - 100.00) / 100.00 * 1e4 - exp_fees
    k = 1.0 / 100.00 * 1e4
    exp_gross = k * (ex_mid_dec - 100.00)
    exp_lat = k * ((100.00 - 100.00) - (ex_mid_act - ex_mid_dec))
    exp_spread = k * ((100.00 - 100.00) - (ex_vwap - ex_mid_act))

    assert r.fees_bps == pytest.approx(exp_fees, abs=TOL)
    assert r.net_bps == pytest.approx(exp_net, abs=TOL)
    assert r.gross_mid_bps == pytest.approx(exp_gross, abs=TOL)
    assert r.latency_drag_bps == pytest.approx(exp_lat, abs=TOL)
    assert r.spread_cost_bps == pytest.approx(exp_spread, abs=TOL)
    assert r.identity_residual_bps == pytest.approx(0.0, abs=TOL)


def test_short_round_trip_fees_on_entry() -> None:
    # SHORT: sell the entry, buy back the exit. Fees hit the SELL (entry) leg,
    # so sell_notional == entry_notional and fees ratio == 1 exactly.
    # entry: sell 1.0 @ 100.00, mid_dec 100.10, mid_act 100.05
    #        (price 100.00 < mid_act 100.05 -> hitting the bid == a cost short)
    # exit:  buy  1.0 @  99.00, mid_dec  98.90, mid_act  98.95
    en = mkfill(100.00, 100.10, 100.05, 1.0)
    ex = mkfill(99.00, 98.90, 98.95, 1.0)
    r = plan_pnl(SHORT, (en,), (ex,), sec_taf_sell_bps=0.4)

    # fees ratio exactly 1 -> fees_bps == sec_taf
    assert r.fees_bps == pytest.approx(0.4, abs=TOL)
    # net = -1*(99.00-100.00)/100.00*1e4 - 0.4
    exp_net = SHORT * (99.00 - 100.00) / 100.00 * 1e4 - 0.4
    assert r.net_bps == pytest.approx(exp_net, abs=TOL)

    # spread for shorting at the bid: k = -1/100.00*1e4 (negative).
    #   spread = k*((100.00-100.05) - (99.00-98.95))
    #          = (-1/100*1e4)*((-0.05) - (0.05)) = (-100)*(-0.10) = +10  -> cost
    k = SHORT / 100.00 * 1e4
    exp_spread = k * ((100.00 - 100.05) - (99.00 - 98.95))
    assert r.spread_cost_bps == pytest.approx(exp_spread, abs=TOL)
    assert r.spread_cost_bps > 0.0  # entry below mid on a short == crossing cost

    assert r.identity_residual_bps == pytest.approx(0.0, abs=TOL)


def test_nan_mid_keeps_net_finite() -> None:
    # A single fill carries nan mids. net_bps + fees read PRICES only and stay
    # finite & exact; gross/latency/spread (and hence residual) go nan.
    en = mkfill(100.05, float("nan"), float("nan"), 1.0)
    ex = mkfill(100.95, 101.00, 100.99, 1.0)
    r = plan_pnl(LONG, (en,), (ex,), sec_taf_sell_bps=0.3)

    exp_fees = 0.3 * (100.95 / 100.05)
    exp_net = (100.95 - 100.05) / 100.05 * 1e4 - exp_fees
    assert math.isfinite(r.net_bps)
    assert r.net_bps == pytest.approx(exp_net, abs=TOL)
    assert math.isfinite(r.fees_bps)
    assert math.isnan(r.gross_mid_bps)
    assert math.isnan(r.latency_drag_bps)
    assert math.isnan(r.spread_cost_bps)
    assert math.isnan(r.identity_residual_bps)


_price = st.floats(min_value=50.0, max_value=150.0, allow_nan=False, allow_infinity=False)
_qty = st.floats(min_value=0.05, max_value=1.0, allow_nan=False, allow_infinity=False)


@st.composite
def _leg(draw: st.DrawFn) -> list[tuple[float, float, float, float]]:
    n = draw(st.integers(min_value=2, max_value=4))
    return [
        (draw(_price), draw(_price), draw(_price), draw(_qty)) for _ in range(n)
    ]


@settings(max_examples=300, deadline=None)
@given(side=st.sampled_from([LONG, SHORT]), en=_leg(), ex=_leg(), taf=_price)
def test_identity_holds_property(
    side: int,
    en: list[tuple[float, float, float, float]],
    ex: list[tuple[float, float, float, float]],
    taf: float,
) -> None:
    # Normalize exit qtys so both legs' filled fractions match (qty sums equal).
    en_qsum = sum(q for *_, q in en)
    ex_qsum = sum(q for *_, q in ex)
    scale = en_qsum / ex_qsum
    entry = tuple(mkfill(p, d, a, q) for (p, d, a, q) in en)
    exit_ = tuple(mkfill(p, d, a, q * scale) for (p, d, a, q) in ex)
    r = plan_pnl(side, entry, exit_, sec_taf_sell_bps=taf * 0.001)
    # Algebraic identity is exact; only fp rounding remains.
    assert abs(r.identity_residual_bps) < 1e-6


def test_session_summary_mixed_shapes() -> None:
    # r1: plain mapping         net 10.0, reason "target"
    # r2: object with .pnl obj  net 20.0, reason "stop"
    # r3: object holding PlanPnl net 30.0, reason "target"
    r1 = {"net_bps": 10.0, "exit_reason": "target"}
    r2 = SimpleNamespace(pnl=SimpleNamespace(net_bps=20.0), exit_reason="stop")
    planpnl = PlanPnl(
        net_bps=30.0,
        gross_mid_bps=0.0,
        latency_drag_bps=0.0,
        spread_cost_bps=0.0,
        fees_bps=0.0,
        identity_residual_bps=0.0,
    )
    r3 = SimpleNamespace(pnl=planpnl, exit_reason="target")

    out = session_summary([r1, r2, r3])
    assert out["n_plans"] == 3
    # sum = 10 + 20 + 30 = 60 ; mean = 60/3 = 20
    assert out["sum_net_bps"] == pytest.approx(60.0, abs=TOL)
    assert out["mean_net_bps"] == pytest.approx(20.0, abs=TOL)
    assert out["exit_reason_counts"] == {"target": 2, "stop": 1}


def test_session_summary_empty() -> None:
    out = session_summary([])
    assert out["n_plans"] == 0
    assert out["sum_net_bps"] == 0.0
    assert math.isnan(out["mean_net_bps"])
    assert out["exit_reason_counts"] == {}


def test_session_summary_tolerates_void_results() -> None:
    # N2 (code review 2026-07-28): VOID / NOT_TAKEN / UNFILLED PlanResults carry
    # pnl=None and exit_reason=None. Summarizing a mixed list used to raise
    # AttributeError ('...' object has no attribute 'net_bps') and take the whole
    # report down; a void must count as an outcome and contribute nan instead.
    taken = SimpleNamespace(pnl=SimpleNamespace(net_bps=12.0), exit_reason="stop")
    void = SimpleNamespace(pnl=None, exit_reason=None)

    out = session_summary([taken, void])
    assert out["n_plans"] == 2                       # the void is counted
    assert out["sum_net_bps"] == pytest.approx(12.0, abs=TOL)   # nan-aware
    assert out["mean_net_bps"] == pytest.approx(12.0, abs=TOL)  # over the priced leg
    assert out["exit_reason_counts"] == {"stop": 1, "unknown": 1}

    # an all-void session summarizes to nan silently (no nanmean empty-slice warning)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        allvoid = session_summary([void, void])
    assert allvoid["n_plans"] == 2
    assert allvoid["sum_net_bps"] == 0.0
    assert math.isnan(allvoid["mean_net_bps"])


def test_session_summary_missing_reason_bucketed_unknown() -> None:
    # dict with no exit_reason -> "unknown"; also exercises np.nansum path.
    out = session_summary([{"net_bps": 5.0}])
    assert out["exit_reason_counts"] == {"unknown": 1}
    assert out["sum_net_bps"] == pytest.approx(5.0, abs=TOL)


def test_import_numpy_available() -> None:
    # guard: module relies on numpy float64 aggregation
    assert np.float64(1.0) == 1.0
