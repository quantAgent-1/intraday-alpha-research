"""Pure-unit tests for the GEX snapshot parser (no network).

Exercises parse_option_snapshots and the OCC symbol parser over a canned,
minimal Alpaca option-snapshot payload. Covers array correctness, the OI/IV
filters, strike-band + expiry windowing, and the reference-OI fallback map.
NO live-API test lives here.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from enginev51.flows.gex_collect import _occ_parse, parse_option_snapshots

_ET = ZoneInfo("America/New_York")


def _now_ns() -> int:
    return int(datetime(2026, 7, 15, 12, 0, tzinfo=_ET).timestamp() * 1_000_000_000)


def test_occ_parse_call_and_put():
    exp, sign, strike = _occ_parse("NVDA260801C00120000")
    assert exp == date(2026, 8, 1) and sign == 1 and strike == 120.0
    exp, sign, strike = _occ_parse("NVDA260801P00118500")
    assert exp == date(2026, 8, 1) and sign == -1 and strike == 118.5
    # Root length is irrelevant — trailing 15 chars are fixed-width.
    _, s2, k2 = _occ_parse("A260801C00050000")
    assert s2 == 1 and k2 == 50.0
    assert _occ_parse("garbage") is None
    assert _occ_parse("NVDA260801X00120000") is None  # not C/P


def test_parse_keeps_valid_and_computes_arrays():
    snaps = {
        "NVDA260801C00120000": {
            "impliedVolatility": 0.50,
            "openInterest": 1000,
            "greeks": {"gamma": 0.01},
        },
        "NVDA260801P00118000": {
            "impliedVolatility": 0.45,
            "openInterest": 800,
        },
    }
    out = parse_option_snapshots("nvda", snaps, spot=120.0, now_ns=_now_ns())

    assert out["underlying"] == "NVDA" and out["spot"] == 120.0
    assert len(out["strike"]) == 2
    # arrays aligned by contract
    by_sym = dict(zip(out["symbol"], out["strike"], strict=True))
    assert by_sym["NVDA260801C00120000"] == 120.0
    assert by_sym["NVDA260801P00118000"] == 118.0
    assert out["sign"] == [1, -1]
    assert out["iv"] == [0.50, 0.45]
    assert out["oi"] == [1000.0, 800.0]
    assert out["mult"] == [100.0, 100.0]
    # tau: ~17 days to 2026-08-01 16:00 ET -> a bit under 0.05y, strictly positive
    assert all(t > 0 for t in out["tau_years"])
    assert 0.0 < out["tau_years"][0] < 0.06


def test_iv_and_oi_filters_drop_bad_contracts():
    snaps = {
        "NVDA260801C00120000": {"impliedVolatility": 0.50, "openInterest": 1000},  # keep
        "NVDA260801C00121000": {"impliedVolatility": 0.0, "openInterest": 1000},   # IV<=0 drop
        "NVDA260801C00122000": {"impliedVolatility": 0.50, "openInterest": 0},     # OI<=0 drop
        "NVDA260801P00119000": {"openInterest": 500},                              # IV missing drop
    }
    out = parse_option_snapshots("NVDA", snaps, spot=120.0, now_ns=_now_ns())
    assert out["symbol"] == ["NVDA260801C00120000"]


def test_strike_band_and_expiry_window_filters():
    snaps = {
        "NVDA260801C00120000": {"impliedVolatility": 0.5, "openInterest": 100},  # keep
        "NVDA260801C00300000": {"impliedVolatility": 0.5, "openInterest": 100},  # 300 vs 120 -> out of band
        "NVDA270201C00120000": {"impliedVolatility": 0.5, "openInterest": 100},  # ~200d -> beyond window
        "NVDA260714C00120000": {"impliedVolatility": 0.5, "openInterest": 100},  # expired (tau<=0)
    }
    out = parse_option_snapshots(
        "NVDA", snaps, spot=120.0, now_ns=_now_ns(),
        expiry_within_days=45, strike_band_pct=0.25,
    )
    assert out["symbol"] == ["NVDA260801C00120000"]


def test_oi_fallback_map_used_when_snapshot_lacks_oi():
    snaps = {
        "NVDA260801C00120000": {"impliedVolatility": 0.5},  # no openInterest in snapshot
        "NVDA260801P00118000": {"impliedVolatility": 0.5},  # no OI and not in map -> dropped
    }
    oi_map = {"NVDA260801C00120000": 4200.0}
    out = parse_option_snapshots(
        "NVDA", snaps, spot=120.0, now_ns=_now_ns(), oi_map=oi_map
    )
    assert out["symbol"] == ["NVDA260801C00120000"]
    assert out["oi"] == [4200.0]


def test_snake_case_and_multiplier_fields_tolerated():
    snaps = {
        "NVDA260801C00120000": {
            "implied_volatility": 0.5,
            "open_interest": 300,
            "size": 100,
        },
    }
    out = parse_option_snapshots("NVDA", snaps, spot=120.0, now_ns=_now_ns())
    assert out["iv"] == [0.5] and out["oi"] == [300.0] and out["mult"] == [100.0]


def test_empty_payload_returns_empty_arrays():
    out = parse_option_snapshots("NVDA", {}, spot=120.0, now_ns=_now_ns())
    assert out["strike"] == [] and out["spot"] == 120.0
    assert out["underlying"] == "NVDA"


def test_expiry_ns_is_1600_et():
    # Sanity: an expiry maps to 16:00 ET that day, and tau shrinks toward it.
    now = int(datetime(2026, 7, 31, 12, 0, tzinfo=_ET).timestamp() * 1e9)
    snaps = {"NVDA260731C00120000": {"impliedVolatility": 0.5, "openInterest": 10}}
    out = parse_option_snapshots("NVDA", snaps, spot=120.0, now_ns=now)
    # 4 hours to 16:00 ET / 365.25 days
    expected = (4 * 3600) / (365.25 * 86400)
    assert math.isclose(out["tau_years"][0], expected, rel_tol=1e-6)
    # cross-check the UTC epoch of 16:00 ET
    exp_utc = datetime(2026, 7, 31, 16, 0, tzinfo=_ET).astimezone(UTC)
    assert exp_utc.hour == 20  # EDT -> 20:00 UTC
