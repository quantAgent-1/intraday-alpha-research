"""Tests for the named-payer / flow toolkit (enginev51.flows).

Black–Scholes + GEX golden values are hand-computed; the GEX assertions use a
constructed synthetic chain with a known dominant strike so the walls/pin are
deterministic. Ported from engineV2 tests/unit/test_gamma.py (imports adapted).

The macro-calendar and forced-flow (ffcal) sanity cases are derived from the
sources' own docstrings / acceptance anchors (news_engine/calendar.py seed
windows; quantresearch ffcal.py selftest() anchors that do not depend on the
external overrides.toml, which is not shipped into this repo).
"""

from __future__ import annotations

import datetime as dt
import math
from zoneinfo import ZoneInfo

import numpy as np

from enginev51.flows import bs, ffcal
from enginev51.flows.gex import _zero_cross, compute_gamma_map
from enginev51.flows.macro import MacroCalendar

# ----------------------------- Black–Scholes -----------------------------

def test_gamma_golden_atm():
    # S=K=100, tau=1, sigma=0.2, r=0:
    #   d1 = (0 + 0.5*0.04)/0.2 = 0.1 ; phi(0.1)=0.3969525
    #   gamma = phi(d1)/(S*sigma*sqrt(tau)) = 0.3969525/(100*0.2) = 0.01984762
    g = float(bs.gamma(100.0, 100.0, 1.0, 0.2, r=0.0))
    assert math.isclose(g, 0.01984762, rel_tol=0, abs_tol=1e-7)


def test_gamma_call_equals_put():
    # Gamma is identical for calls and puts (it has no is_call arg); sanity-check
    # that prices differ but the single gamma value is shared.
    args = dict(S=100.0, K=105.0, tau=0.5, sigma=0.3, r=0.04)
    call = float(bs.bs_price(**args, is_call=True))
    put = float(bs.bs_price(**args, is_call=False))
    assert not math.isclose(call, put, abs_tol=1e-6)
    g = float(bs.gamma(100.0, 105.0, 0.5, 0.3, r=0.04))
    assert g > 0.0


def test_gamma_array_broadcast():
    K = np.array([90.0, 100.0, 110.0])
    g = bs.gamma(100.0, K, 0.25, 0.5, r=0.0)
    assert g.shape == (3,)
    # ATM gamma is the largest of the three.
    assert g[1] > g[0] and g[1] > g[2]


def test_implied_vol_roundtrip():
    S, K, tau, r = 100.0, 105.0, 0.08, 0.04
    for sig_true, is_call in [(0.45, True), (0.6, False), (0.25, True)]:
        price = float(bs.bs_price(S, K, tau, sig_true, r=r, is_call=is_call))
        iv = bs.implied_vol(price, S, K, tau, r=r, is_call=is_call)
        assert math.isclose(iv, sig_true, abs_tol=1e-3)


def test_implied_vol_failures_return_nan():
    assert math.isnan(bs.implied_vol(0.0, 100.0, 100.0, 0.05))         # zero price
    assert math.isnan(bs.implied_vol(5.0, 100.0, 90.0, 0.05, is_call=True))  # below intrinsic (10)
    assert math.isnan(bs.implied_vol(-1.0, 100.0, 100.0, 0.05))        # negative price


# ----------------------------- zero-cross / flip -----------------------------

def test_zero_cross_linear():
    grid = np.linspace(90.0, 110.0, 21)
    curve = grid - 100.0  # crosses zero exactly at 100
    assert math.isclose(_zero_cross(grid, curve, 100.0), 100.0, abs_tol=1e-9)


def test_zero_cross_none():
    grid = np.linspace(90.0, 110.0, 21)
    assert math.isnan(_zero_cross(grid, np.ones_like(grid), 100.0))


def test_zero_cross_picks_nearest_spot():
    grid = np.linspace(80.0, 120.0, 41)
    # two crossings: at 90 and 110; spot 108 -> nearest is 110
    curve = (grid - 90.0) * (grid - 110.0)  # zero at 90 and 110
    assert math.isclose(_zero_cross(grid, curve, 108.0), 110.0, abs_tol=1e-6)


# ----------------------------- GEX map -----------------------------

def _synthetic_chain():
    # spot 100; strikes 90..110; a call and a put at each strike.
    strikes = [90.0, 95.0, 100.0, 105.0, 110.0]
    K, sign, oi = [], [], []
    for k in strikes:
        # call
        K.append(k)
        sign.append(+1.0)
        oi.append(100000.0 if k == 105.0 else (50000.0 if k == 100.0 else 100.0))
        # put
        K.append(k)
        sign.append(-1.0)
        oi.append(100000.0 if k == 95.0 else (50000.0 if k == 100.0 else 100.0))
    n = len(K)
    return dict(
        symbol="TEST", ts=0, spot=100.0,
        strike=K, sign=sign, oi=oi,
        tau=[0.05] * n, sigma=[0.5] * n, mult=[100.0] * n,
    )


def test_walls_and_pin_deterministic():
    gm = compute_gamma_map(**_synthetic_chain())
    # call@105 has 100k OI (others tiny / ATM 50k) -> call wall at 105
    assert gm.call_wall == 105.0
    # put@95 has 100k OI -> put wall at 95
    assert gm.put_wall == 95.0
    # ATM (100) carries the highest combined gamma concentration -> pin 100
    assert gm.pin == 100.0
    assert gm.regime in (1, -1)
    assert set(gm.per_strike) == {90.0, 95.0, 100.0, 105.0, 110.0}


def test_flip_in_band_or_nan():
    gm = compute_gamma_map(**_synthetic_chain())
    assert math.isnan(gm.gamma_flip) or (80.0 <= gm.gamma_flip <= 120.0)


def test_all_puts_no_positive_flip():
    # Dealers short all puts -> net GEX < 0 everywhere -> no zero crossing.
    gm = compute_gamma_map(
        symbol="TEST", ts=0, spot=100.0,
        strike=[95.0, 100.0, 105.0], sign=[-1.0, -1.0, -1.0],
        oi=[1000.0, 1000.0, 1000.0], tau=[0.05] * 3,
        sigma=[0.5] * 3, mult=[100.0] * 3,
    )
    assert gm.net_gex < 0.0 and gm.regime == -1
    assert math.isnan(gm.gamma_flip)


def test_empty_chain_is_safe():
    gm = compute_gamma_map(
        symbol="TEST", ts=0, spot=100.0,
        strike=[100.0], sign=[1.0], oi=[0.0],   # OI=0 -> dropped
        tau=[0.05], sigma=[0.5], mult=[100.0],
    )
    assert gm.net_gex == 0.0 and gm.regime == 0
    assert math.isnan(gm.call_wall) and math.isnan(gm.pin)


# ----------------------------- macro calendar (news_engine) -----------------------------

_ET = ZoneInfo("America/New_York")


def _et_ns(y: int, m: int, d: int, hh: int, mm: int) -> int:
    return int(dt.datetime(y, m, d, hh, mm, tzinfo=_ET).timestamp() * 1_000_000_000)


def test_macro_fomc_window_active_inside_and_labeled():
    # FOMC (14:00 ET) uses the (15 min pre, 60 min post) window; 14:30 ET is inside.
    cal = MacroCalendar(macro=[("2026-06-17", "14:00", "FOMC")], tsla_events=[])
    st = cal.blackout(_et_ns(2026, 6, 17, 14, 30))
    assert st.active is True
    assert st.label == "FOMC" and st.kind == "macro"
    # window ends at 15:00 ET -> ~30 minutes (1800 s) remaining from 14:30.
    assert 1700 <= st.ends_in_s <= 1800


def test_macro_outside_window_is_inactive():
    # 11:30 ET is past the 09:30+90min opening caution and before the 13:45 FOMC pre-window.
    cal = MacroCalendar(macro=[("2026-06-17", "14:00", "FOMC")], tsla_events=[])
    st = cal.blackout(_et_ns(2026, 6, 17, 11, 30))
    assert st.active is False
    assert st.label is None and st.ends_in_s is None


def test_macro_tsla_event_covers_whole_rth():
    # TSLA event days black out the whole RTH session (09:30-16:00 ET).
    cal = MacroCalendar(macro=[], tsla_events=[("2026-07-22", "TSLA Q2 earnings (after close)")])
    st = cal.blackout(_et_ns(2026, 7, 22, 12, 0))
    assert st.active is True and st.kind == "earnings"


# ----------------------------- forced-flow calendar (ffcal) -----------------------------

def _ffctx():
    # Pure compute: no overrides file (overrides.toml is not shipped), ov={}.
    return ffcal.Ctx(dt.date(2026, 7, 6), dt.date(2026, 6, 1), dt.date(2026, 10, 15), ov={})


def test_ffcal_f1_us_opex_jul17():
    # 3rd-Friday US monthly opex for July 2026 = Jul 17 (selftest anchor).
    evs = ffcal.build(_ffctx())
    assert any(e.feed == "F1" and e.date == dt.date(2026, 7, 17) for e in evs)


def test_ffcal_f11_krx_monthly_expiry_jul9():
    # 2nd-Thursday KOSPI200 monthly expiry for July 2026 = Jul 9, size L (selftest anchor).
    evs = ffcal.build(_ffctx())
    assert any(e.feed == "F11" and e.date == dt.date(2026, 7, 9) and e.size == "L" for e in evs)


def test_ffcal_cpi_dst_render_kst():
    # DST render: CPI 08:30 ET -> 21:30 KST in summer, 22:30 KST in winter (selftest anchor).
    assert ffcal.et_to_kst(dt.date(2026, 7, 14), "08:30")[1] == "21:30"
    assert ffcal.et_to_kst(dt.date(2026, 12, 10), "08:30")[1] == "22:30"
    evs = ffcal.build(_ffctx())
    assert any(e.label == "US CPI" and e.date == dt.date(2026, 7, 14) and e.time == "21:30"
               for e in evs)
