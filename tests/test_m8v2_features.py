"""Tests for models/m8v2_features.py -- the M8-v2 mechanism-informed meta-gate's
6 frozen feature builders (M3_REGISTRATION.md "M8-v2", REGISTERED 2026-07-20).

Synthetic frames + hand literals only (no disk, no network). Covers the
registered checks: 15:55:10 leakage/parity (all 6 features unchanged by
post-decision bbo-1s mutation), the AUM step-function strictly-t-1 rule (BOTH
the session-level F(t) coefficient and the month-level complex_intensity
AUM), month_end correctness on 3 known month-ends (+ a quad-witch negative
control), F(t) reflection sanity (sign(F) == sign(r) for a realistic
multi-fund complex), and hand-computed range_pos_1555 / day_vol_ratio
arithmetic.
"""

from __future__ import annotations

import math
from datetime import date

import polars as pl

from enginev51.data.bbo1s import BBO_SCHEMA
from enginev51.data.noii import et_ns
from enginev51.models.m8v2_features import (
    FEATURE_COLS,
    attach_complex_aum,
    attach_flow_coef,
    build_v2_feature_row,
    is_month_end,
)

SESSION = "2024-03-14"  # ordinary Thursday (Mar quad-witch is 2024-03-15)


def _bbo(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=BBO_SCHEMA, orient="row")


def _row(ts: int, bid: float, ask: float) -> dict:
    return {"ts": ts, "bid": bid, "ask": ask, "bid_size": 100.0, "ask_size": 100.0}


def _hand_bbo() -> pl.DataFrame:
    """5 ticks spanning 09:30->15:55:10: mids 100.1 / 99.1 / 101.1 / 100.6 / 100.9
    -> day_low=99.1 (09:31), day_high=101.1 (12:00), p_1555=100.9."""
    return _bbo(
        [
            _row(et_ns(SESSION, 9, 30, 0), 100.0, 100.2),   # mid 100.1
            _row(et_ns(SESSION, 9, 31, 0), 99.0, 99.2),      # mid 99.1  (day low)
            _row(et_ns(SESSION, 12, 0, 0), 101.0, 101.2),    # mid 101.1 (day high)
            _row(et_ns(SESSION, 15, 55, 0), 100.5, 100.7),   # mid 100.6
            _row(et_ns(SESSION, 15, 55, 10), 100.8, 101.0),  # mid 100.9 (P@15:55:10)
        ]
    )


_BASE_KW = dict(
    session=SESSION,
    basis_bps=20.0,
    adv20_dollars=1_000_000_000.0,
    flow_coef=5.0e9,
    complex_aum_usd=2.0e8,
    vol20=0.05,
    prior_close=100.0,
)


# --------------------------------------------------------------------------- structural


def test_feature_cols_shape():
    assert FEATURE_COLS == (
        "abs_f_over_adv", "flow_aligned", "complex_intensity",
        "range_pos_1555", "month_end", "day_vol_ratio",
    )
    assert len(FEATURE_COLS) == 6


def test_missing_bbo_gives_null_not_zero():
    """No bbo coverage -> abs_f_over_adv/flow_aligned/range_pos_1555/day_vol_ratio
    are None (unknown), NOT 0 -- distinct from a genuine flow_coef==0 zero."""
    feat = build_v2_feature_row(bbo_frame=None, **_BASE_KW)
    assert feat["abs_f_over_adv"] is None
    assert feat["flow_aligned"] is None
    assert feat["range_pos_1555"] is None
    assert feat["day_vol_ratio"] is None
    # complex_intensity and month_end never touch bbo -> still defined
    assert feat["complex_intensity"] == _BASE_KW["complex_aum_usd"] / _BASE_KW["adv20_dollars"]
    assert feat["month_end"] in (0.0, 1.0)


def test_zero_complex_is_a_legitimate_zero_not_null():
    kw = dict(_BASE_KW)
    kw["flow_coef"] = 0.0
    feat = build_v2_feature_row(bbo_frame=_hand_bbo(), **kw)
    assert feat["abs_f_over_adv"] == 0.0
    assert feat["flow_aligned"] == 0.0  # sign(0)*sign(basis) == 0, not None


# --------------------------------------------------------------------------- hand arithmetic


def test_range_pos_1555_hand_value():
    feat = build_v2_feature_row(bbo_frame=_hand_bbo(), **_BASE_KW)
    assert math.isclose(feat["p_1555"], 100.9, abs_tol=1e-9)
    assert math.isclose(feat["day_low"], 99.1, abs_tol=1e-9)
    assert math.isclose(feat["day_high"], 101.1, abs_tol=1e-9)
    expected = (100.9 - 99.1) / (101.1 - 99.1)
    assert math.isclose(feat["range_pos_1555"], expected, abs_tol=1e-9)


def test_day_vol_ratio_hand_value():
    """1-min grid 09:30->15:55 (386 pts): mid is 100.1 at k=0, 99.1 for
    k=1..149, 101.1 for k=150..384, 100.6 at k=385 (last grid point, NOT
    15:55:10). Only 3 non-zero log-return transitions -> realized_vol_1min =
    sqrt(r1^2+r2^2+r3^2) with r1=ln(99.1/100.1), r2=ln(101.1/99.1),
    r3=ln(100.6/101.1)."""
    feat = build_v2_feature_row(bbo_frame=_hand_bbo(), **_BASE_KW)
    r1 = math.log(99.1 / 100.1)
    r2 = math.log(101.1 / 99.1)
    r3 = math.log(100.6 / 101.1)
    expected_rv = math.sqrt(r1 * r1 + r2 * r2 + r3 * r3)
    expected_ratio = expected_rv / _BASE_KW["vol20"]
    assert math.isclose(feat["day_vol_ratio"], expected_ratio, rel_tol=1e-9)


def test_f_usd_and_abs_f_over_adv_hand_value():
    """r = P@15:55:10/prior_close - 1 = 100.9/100.0 - 1 = 0.009;
    F_usd = flow_coef * r; abs_f_over_adv = |F_usd|/adv20."""
    feat = build_v2_feature_row(bbo_frame=_hand_bbo(), **_BASE_KW)
    r = 100.9 / 100.0 - 1.0
    assert math.isclose(feat["r_pinned"], r, rel_tol=1e-9)
    f_usd = _BASE_KW["flow_coef"] * r
    assert math.isclose(feat["F_usd"], f_usd, rel_tol=1e-9)
    assert math.isclose(feat["abs_f_over_adv"], abs(f_usd) / _BASE_KW["adv20_dollars"], rel_tol=1e-9)
    # basis_bps=20 (positive), r positive -> F positive -> aligned
    assert feat["flow_aligned"] == 1.0


# --------------------------------------------------------------------------- leakage / parity


def test_leakage_bbo_after_1555_10_leaves_all_6_features_unchanged():
    """Mutating (appending wild rows to) bbo-1s data dated AFTER 15:55:10 must
    leave every one of the 6 frozen features byte-identical."""
    base = build_v2_feature_row(bbo_frame=_hand_bbo(), **_BASE_KW)
    polluted_rows = _hand_bbo().to_dicts() + [
        _row(et_ns(SESSION, 15, 55, 11), 1.0, 500.0),   # 1s after decision: wild
        _row(et_ns(SESSION, 16, 30, 0), 0.01, 999.0),   # after-hours: wild
    ]
    polluted = pl.DataFrame(polluted_rows, schema=BBO_SCHEMA, orient="row")
    mutated = build_v2_feature_row(bbo_frame=polluted, **_BASE_KW)
    for c in FEATURE_COLS:
        assert base[c] is not None, f"{c} unexpectedly null in the base fixture"
        assert math.isclose(base[c], mutated[c], abs_tol=1e-12), (
            f"{c} changed from post-15:55:10 bbo mutation: {base[c]} -> {mutated[c]}"
        )
    # diagnostics too (p_1555 / day_low / day_high / r_pinned feed the features)
    for c in ("p_1555", "day_low", "day_high", "r_pinned", "F_usd"):
        assert math.isclose(base[c], mutated[c], abs_tol=1e-9), c


def test_leakage_bbo_before_0930_does_not_move_day_range():
    """A wild pre-open (< 09:30 ET) print must not move day_low/day_high (only
    [09:30, 15:55:10] mids count for the day range)."""
    base = build_v2_feature_row(bbo_frame=_hand_bbo(), **_BASE_KW)
    rows = _hand_bbo().to_dicts() + [_row(et_ns(SESSION, 9, 0, 0), 0.5, 0.6)]  # pre-open, wild
    polluted = pl.DataFrame(rows, schema=BBO_SCHEMA, orient="row")
    mutated = build_v2_feature_row(bbo_frame=polluted, **_BASE_KW)
    assert math.isclose(base["day_low"], mutated["day_low"], abs_tol=1e-9)
    assert math.isclose(base["day_high"], mutated["day_high"], abs_tol=1e-9)
    assert math.isclose(base["range_pos_1555"], mutated["range_pos_1555"], abs_tol=1e-9)


# --------------------------------------------------------------------------- AUM step function


def test_flow_coef_step_function_strictly_t_minus_1_session_level():
    """F(t)'s AUM anchor is the SESSION-level step function: strictly BEFORE
    the session date, no interpolation, no exact-date match."""
    anchors = pl.DataFrame(
        {
            "ticker": ["FOO", "FOO"],
            "underlying": ["NVDA", "NVDA"],
            "adate": [date(2024, 1, 31), date(2024, 2, 29)],
            "aum_usd": [100.0, 200.0],
            "lev_era": [2.0, 2.0],
            "coef": [200.0, 400.0],  # L(L-1)*aum = 2*1*100, 2*1*200
        }
    )
    df = pl.DataFrame(
        {"symbol": ["NVDA", "NVDA", "NVDA"], "session": ["2024-01-31", "2024-02-01", "2024-03-01"]}
    ).with_columns(pl.col("session").str.to_date().alias("_dte"))
    out = attach_flow_coef(df, anchors).sort("session")
    got = dict(zip(out["session"].to_list(), out["flow_coef"].to_list(), strict=True))
    # exactly ON the first anchor date -> NOT used (strictly before) -> 0
    assert got["2024-01-31"] == 0.0
    # the very next session -> the 2024-01-31 anchor governs
    assert got["2024-02-01"] == 200.0
    # after the second anchor -> the 2024-02-29 anchor governs
    assert got["2024-03-01"] == 400.0


def test_complex_aum_step_function_is_month_level_not_session_level():
    """complex_intensity's AUM anchor is a COARSER MONTH-level step function
    (FLAGGED CHOICE #1): an anchor dated WITHIN the session's own month does
    NOT count, even though it is strictly before the session date -- only an
    anchor from a PRIOR calendar month counts."""
    anchors = pl.DataFrame(
        {
            "ticker": ["FOO"], "underlying": ["NVDA"], "adate": [date(2024, 1, 15)],
            "aum_usd": [500.0], "lev_era": [2.0], "coef": [500.0],
        }
    )
    df = pl.DataFrame(
        {"symbol": ["NVDA", "NVDA"], "session": ["2024-01-20", "2024-02-05"]}
    ).with_columns(
        pl.col("session").str.to_date().alias("_dte"),
    ).with_columns(
        pl.date(pl.col("_dte").dt.year(), pl.col("_dte").dt.month(), 1).alias("_month_start"),
    )
    out = attach_complex_aum(df, anchors).sort("session")
    got = dict(zip(out["session"].to_list(), out["complex_aum_usd"].to_list(), strict=True))
    # 2024-01-20 is AFTER the 2024-01-15 anchor (session-level would use it),
    # but the anchor is NOT from a PRIOR month -> month-level step function gives 0.
    assert got["2024-01-20"] == 0.0
    # 2024-02-05's month (Feb) start is 2024-02-01, strictly after the Jan
    # anchor's month -> the anchor now governs.
    assert got["2024-02-05"] == 500.0


# --------------------------------------------------------------------------- month_end (M14 reuse)


def test_month_end_known_dates():
    # 3 verified last-trading-days-of-month (ffcal.trading_days ground truth)
    assert is_month_end("2024-01-31") is True
    assert is_month_end("2024-02-29") is True  # leap day
    assert is_month_end("2025-01-31") is True
    # negative controls: an ordinary mid-month day, and the QUAD_WITCH 3rd
    # Friday of the SAME month as one of the fixtures above (must not collide)
    assert is_month_end("2024-01-15") is False
    assert is_month_end("2024-06-21") is False  # 3rd Friday of June 2024 (quad-witch)
    assert is_month_end("2024-06-28") is True   # actual last trading day of June 2024


# --------------------------------------------------------------------------- F reflection sanity


def test_f_reflection_sign_matches_r_for_realistic_complex():
    """A realistic multi-fund complex (bull 2x + bear -1x + bear -2x, mirroring
    MU's MUU/MUD/MUZ pattern) always has flow_coef > 0 (L(L-1) > 0 for every
    L outside (0,1), which no real LETF uses) -> sign(F) == sign(r) always."""
    anchors = pl.DataFrame(
        {
            "ticker": ["BULL2X", "BEAR1X", "BEAR2X"],
            "underlying": ["MU", "MU", "MU"],
            "adate": [date(2023, 1, 1)] * 3,
            "aum_usd": [100.0, 50.0, 30.0],
            "lev_era": [2.0, -1.0, -2.0],
            "coef": [200.0, 100.0, 180.0],  # 2*1*100, -1*-2*50, -2*-3*30
        }
    )
    df = pl.DataFrame({"symbol": ["MU"], "session": ["2024-06-01"]}).with_columns(
        pl.col("session").str.to_date().alias("_dte")
    )
    out = attach_flow_coef(df, anchors)
    flow_coef = float(out["flow_coef"][0])
    assert flow_coef == 200.0 + 100.0 + 180.0
    assert flow_coef > 0.0

    kw = dict(_BASE_KW)
    kw["flow_coef"] = flow_coef
    kw["prior_close"] = 100.0

    up = build_v2_feature_row(bbo_frame=_hand_bbo(), **kw)  # p_1555=100.9 > prior_close -> r>0
    assert up["F_usd"] > 0.0

    kw_down = dict(kw)
    kw_down["prior_close"] = 200.0  # p_1555=100.9 < prior_close -> r<0
    down = build_v2_feature_row(bbo_frame=_hand_bbo(), **kw_down)
    assert down["F_usd"] < 0.0
