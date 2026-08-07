"""Tests for apps/run_m11.py — the M11 cross-sectional OOS generalization cell.

Synthetic frames + hand-computed literals only (no disk, no network). Covers the
registered checks: the ref-as-mid basis math on a hand NOII frame (a 15:55:11
message excluded, a near/ref<=0 message skipped), the |basis|>=10 firing gate, the
conservative entry-cost sign (a buy pays MORE than ref, a sell receives LESS), the
net_bps decomposition sign, the sector-map completeness (all 28 covered), the
coverage helper, and the holdout guard.
"""

from __future__ import annotations

import polars as pl
import pytest

from enginev51.apps.run_basis_trial import basis_bps_of
from enginev51.apps.run_m11 import (
    FIRE_BASIS_BPS,
    SECTOR_OF,
    SECTORS,
    TAKER_COST_BPS,
    UNIVERSE_28,
    assert_before_holdout,
    conservative_entry_px,
    coverage,
    direction_of,
    near_ref_at,
    net_bps_for,
    sector_prong,
)
from enginev51.data.noii import NOII_SCHEMA, et_ns
from enginev51.protocol import SealViolation

# --------------------------------------------------------------------------- helpers


def _noii_row(ts: int, near: float, ref: float, side: str = "B",
              imb: float = 1000.0, paired: float = 500.0, far: float = 0.0) -> dict:
    return {
        "ts": ts, "side": side, "imbalance_shares": imb, "paired_shares": paired,
        "near_price": near, "far_price": far, "ref_price": ref,
    }


def _frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=NOII_SCHEMA, orient="row").sort("ts")


# --------------------------------------------------------------------------- basis math


def test_ref_as_mid_basis_hand_frame():
    """near/ref picked PIT from the last near>0 & ref>0 message; basis = 1e4*(near-ref)/ref.

    A 15:55:11 message (after the 15:55:10 signal) must be EXCLUDED, and a message
    whose near or ref is <= 0 must be SKIPPED — so the governing message is the
    15:55:09 one with near=100.10, ref=100.00 -> basis = 10.0 bps exactly.
    """
    session = "2024-03-15"
    ts_sig = et_ns(session, 15, 55, 10)
    frame = _frame([
        _noii_row(et_ns(session, 15, 55, 0), near=0.0, ref=100.00),   # near<=0: skipped
        _noii_row(et_ns(session, 15, 55, 9), near=100.10, ref=100.00),  # governs
        _noii_row(et_ns(session, 15, 55, 11), near=105.00, ref=100.00),  # after signal: excluded
    ])
    nr = near_ref_at(frame, ts_sig)
    assert nr is not None
    near, ref = nr
    assert near == pytest.approx(100.10)
    assert ref == pytest.approx(100.00)
    assert basis_bps_of(near, ref) == pytest.approx(10.0)
    assert direction_of(near, ref) == 1


def test_near_ref_at_none_when_no_valid_message():
    session = "2024-03-15"
    ts_sig = et_ns(session, 15, 55, 10)
    # Only messages with near<=0 OR ref<=0 before the signal -> no governing row.
    frame = _frame([
        _noii_row(et_ns(session, 15, 50, 0), near=0.0, ref=100.0),
        _noii_row(et_ns(session, 15, 54, 0), near=100.0, ref=0.0),
    ])
    assert near_ref_at(frame, ts_sig) is None


# --------------------------------------------------------------------------- firing gate


def test_fire_gate_threshold():
    """|basis| >= 10 fires; a 9.99 bps basis does not."""
    ref = 100.0
    # near for exactly +9.99 bps and +10.01 bps
    near_below = ref * (1 + 9.99e-4)
    near_above = ref * (1 + 10.01e-4)
    assert abs(basis_bps_of(near_below, ref)) < FIRE_BASIS_BPS
    assert abs(basis_bps_of(near_above, ref)) >= FIRE_BASIS_BPS
    # a negative (sell) basis of magnitude >= 10 also fires
    near_sell = ref * (1 - 12e-4)
    assert basis_bps_of(near_sell, ref) == pytest.approx(-12.0, abs=1e-6)
    assert abs(basis_bps_of(near_sell, ref)) >= FIRE_BASIS_BPS
    assert direction_of(near_sell, ref) == -1


# --------------------------------------------------------------------------- entry cost sign


def test_conservative_entry_cost_sign():
    """A BUY pays MORE than ref; a SELL receives LESS. Magnitude == TAKER_COST_BPS."""
    ref = 200.0
    buy = conservative_entry_px(ref, +1)
    sell = conservative_entry_px(ref, -1)
    assert buy > ref
    assert sell < ref
    assert (buy - ref) / ref * 1e4 == pytest.approx(TAKER_COST_BPS)
    assert (ref - sell) / ref * 1e4 == pytest.approx(TAKER_COST_BPS)


def test_net_bps_decomposition_sign():
    """net_bps == side*(close-entry_px)/entry_px*1e4 - fees; a favourable close wins.

    Long: ref=100, entry pays 2.5bps -> entry_px=100.025, close=101 -> strong win.
    A close BELOW the conservative entry loses. Fees (~0.3bp) make a flat trade
    slightly negative."""
    ref = 100.0
    entry = conservative_entry_px(ref, +1)  # 100.025
    win = net_bps_for(+1, ref, entry, 101.0)
    lose = net_bps_for(+1, ref, entry, 99.0)
    flat = net_bps_for(+1, ref, entry, entry)
    assert win > 0
    assert lose < 0
    assert flat < 0  # only the SEC/TAF fee, no price move
    assert flat == pytest.approx(-0.3, abs=0.05)
    # short symmetry: a close below entry wins
    entry_s = conservative_entry_px(ref, -1)  # 99.975
    win_s = net_bps_for(-1, ref, entry_s, 99.0)
    assert win_s > 0


# --------------------------------------------------------------------------- sector map


def test_sector_map_completeness():
    """All 28 registered names are covered, each maps to exactly one sector, and no
    name is duplicated across sectors."""
    assert len(UNIVERSE_28) == 28
    assert len(SECTOR_OF) == 28
    # every universe name has a sector, and it is the one that lists it
    for sym in UNIVERSE_28:
        sec = SECTOR_OF[sym]
        assert sym in SECTORS[sec]
    # no duplicates across sector lists
    flat = [s for syms in SECTORS.values() for s in syms]
    assert len(flat) == len(set(flat)) == 28
    # NONE of the original 5 leaked into the OOS universe
    assert not (set(UNIVERSE_28) & {"NVDA", "TSLA", "AMD", "MU", "GOOGL"})


def test_sector_prong_counts_positive_sectors():
    df = pl.DataFrame(
        {
            "session": ["2024-01-02", "2024-01-03", "2024-01-02", "2024-01-03"],
            "sector": ["Semis", "Semis", "Consumer", "Consumer"],
            "net_bps": [5.0, 7.0, -3.0, -1.0],
        }
    )
    p = sector_prong(df)
    assert p["n_sectors_represented"] == 2
    assert p["n_sectors_net_positive"] == 1
    assert p["majority_of_sectors_positive"] is False  # 1 of 2 is not a majority
    assert p["per_sector_point_estimate"]["Semis"] == pytest.approx(6.0)


# --------------------------------------------------------------------------- coverage


def test_coverage_counts_present_partitions(tmp_path):
    root = tmp_path / "noii"
    # Two present names (AAPL, MSFT), rest missing.
    for sym in ("AAPL", "MSFT"):
        d = root / sym
        d.mkdir(parents=True)
        pl.DataFrame(schema=NOII_SCHEMA).write_parquet(d / "2024-03.parquet")
    # An empty directory (no parquet) must NOT count as present.
    (root / "PEP").mkdir(parents=True)
    cov = coverage(list(UNIVERSE_28), noii_dir=root)
    assert cov["n_total"] == 28
    assert cov["n_present"] == 2
    assert set(cov["present"]) == {"AAPL", "MSFT"}
    assert "PEP" in cov["missing"]


# --------------------------------------------------------------------------- holdout guard


def test_holdout_guard():
    from datetime import date

    assert_before_holdout(date(2026, 5, 31))  # ok
    # SealViolation, not AssertionError: the guard must survive `python -O` (B7/J2).
    with pytest.raises(SealViolation):
        assert_before_holdout(date(2026, 6, 1))  # the seal boundary
    with pytest.raises(SealViolation):
        assert_before_holdout(date(2026, 7, 1))
