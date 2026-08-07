"""Tests for models/evolution_features.py — the M9 auction-evolution path scalars.

Four registered checks (hand-built synthetic frames + literals; the leakage check
also runs against the real events.parquet when the data lake is present):

  1. LEAKAGE (mandatory): a basis reconstructed at 15:55:10 from the stream equals
     the pre-computed events.parquet basis_bps to < 0.5 bps.
  2. window boundary: a 15:55:11 message is EXCLUDED (strict [15:50:00, 15:55:10]).
  3. slope math on a hand series (ols_slope + near_conv_slope, bps/min).
  4. masked < 3-point near window -> slope 0.0 with present flag False.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from enginev51.data.noii import NOII_SCHEMA, et_ns
from enginev51.models.evolution_features import (
    DECISION_HMS,
    EVO_FEATURES,
    apply_winsor,
    evo_features,
    fit_winsor_bounds,
    ols_slope,
    reconstruct_basis_bps,
)

SESSION = "2025-03-14"
ADV = 1_000_000_000.0
M0 = 100.0  # fixed mid at 15:55:10
SIDE = 1


def _row(ts, side, imb, near, ref, far=0.0, paired=1_000_000.0):
    return {
        "ts": ts, "side": side, "imbalance_shares": imb, "paired_shares": paired,
        "near_price": near, "far_price": far, "ref_price": ref,
    }


# --------------------------------------------------------------------------- slope math


def test_ols_slope_hand_series():
    # y = 2 * t(min); t at 0/60/120 s -> 0/1/2 min ; slope = 2.0 per min
    t = np.array([0, 60 * 1_000_000_000, 120 * 1_000_000_000], dtype=np.int64)
    y = np.array([0.0, 2.0, 4.0])
    slope, present = ols_slope(t, y)
    assert present is True
    assert math.isclose(slope, 2.0, abs_tol=1e-9)


def test_ols_slope_too_few_points_is_zero_absent():
    t = np.array([0, 60 * 1_000_000_000], dtype=np.int64)
    y = np.array([0.0, 5.0])
    slope, present = ols_slope(t, y)
    assert slope == 0.0
    assert present is False


def test_near_conv_slope_hand_series():
    """near>0 at 15:55:08/09/10 with near = 100.00/100.10/100.20 (m0=100, side=+1)
    -> signed_basis = 0/10/20 bps at 1-second spacing (1/60 min) -> slope 600 bps/min.
    Earlier near=0 messages are masked out (blank-until-populated)."""
    win = pl.DataFrame(
        [
            _row(et_ns(SESSION, 15, 50, 0), "B", 100_000.0, 0.0, 100.0),   # near=0 masked
            _row(et_ns(SESSION, 15, 54, 0), "B", 120_000.0, 0.0, 100.0),   # near=0 masked
            _row(et_ns(SESSION, 15, 55, 8), "B", 200_000.0, 100.00, 100.0),
            _row(et_ns(SESSION, 15, 55, 9), "B", 210_000.0, 100.10, 100.0),
            _row(et_ns(SESSION, 15, 55, 10), "B", 220_000.0, 100.20, 100.0),
        ],
        schema=NOII_SCHEMA, orient="row",
    )
    f = evo_features("NVDA", SESSION, adv20=ADV, side=SIDE, m0=M0, noii_frame=win)
    assert f["near_conv_slope_present"] is True
    # signed_basis 0,10,20 at t=0,1/60,2/60 min -> slope = 10 / (1/60) = 600 bps/min
    # (abs_tol loose for the float representation of the near prices / 1e4 basis)
    assert math.isclose(f["near_conv_slope"], 600.0, abs_tol=1e-2)
    # jitter = std(ddof=1) of first-diffs [10, 10] = 0
    assert f["near_jitter_present"] is True
    assert math.isclose(f["near_jitter"], 0.0, abs_tol=1e-9)


# --------------------------------------------------------------------------- window boundary


def test_window_boundary_excludes_1555_11():
    """A 15:55:11 message (out of the strict [15:50:00, 15:55:10] window) with a
    wild near price must NOT change any evolution feature; a 15:49:59 pre-window
    message is likewise excluded."""
    base_rows = [
        _row(et_ns(SESSION, 15, 55, 8), "B", 200_000.0, 100.00, 100.0),
        _row(et_ns(SESSION, 15, 55, 9), "B", 210_000.0, 100.10, 100.0),
        _row(et_ns(SESSION, 15, 55, 10), "B", 220_000.0, 100.20, 100.0),
    ]
    base = pl.DataFrame(base_rows, schema=NOII_SCHEMA, orient="row")
    polluted = pl.DataFrame(
        [
            _row(et_ns(SESSION, 15, 49, 59), "S", 9_000_000.0, 50.0, 50.0),   # before window
            *base_rows,
            _row(et_ns(SESSION, 15, 55, 11), "S", 9_000_000.0, 999.0, 999.0),  # after decision
        ],
        schema=NOII_SCHEMA, orient="row",
    )
    a = evo_features("NVDA", SESSION, adv20=ADV, side=SIDE, m0=M0, noii_frame=base)
    b = evo_features("NVDA", SESSION, adv20=ADV, side=SIDE, m0=M0, noii_frame=polluted)
    for c in EVO_FEATURES:
        assert math.isclose(a[c], b[c], abs_tol=1e-9), c


# --------------------------------------------------------------------------- masked <3


def test_masked_near_window_under_3_points_is_zero_absent():
    """Only ONE populated near point in the whole window -> near_conv_slope and
    near_jitter are 0.0 with present=False (masked, not zero-filled)."""
    win = pl.DataFrame(
        [
            _row(et_ns(SESSION, 15, 50, 0), "B", 100_000.0, 0.0, 100.0),
            _row(et_ns(SESSION, 15, 53, 0), "B", 120_000.0, 0.0, 100.0),
            _row(et_ns(SESSION, 15, 54, 30), "B", 130_000.0, 0.0, 100.0),
            _row(et_ns(SESSION, 15, 55, 0), "B", 140_000.0, 0.0, 100.0),
            _row(et_ns(SESSION, 15, 55, 10), "B", 220_000.0, 100.20, 100.0),  # sole near>0
        ],
        schema=NOII_SCHEMA, orient="row",
    )
    f = evo_features("NVDA", SESSION, adv20=ADV, side=SIDE, m0=M0, noii_frame=win)
    assert f["near_conv_slope"] == 0.0
    assert f["near_conv_slope_present"] is False
    assert f["near_jitter"] == 0.0
    assert f["near_jitter_present"] is False
    # imbalance / paired paths still populate (ref-price fallback, no near mask):
    # last-90s window has 15:54:30 / 15:55:00 / 15:55:10 -> 3 points -> present.
    assert f["imb_velocity_present"] is True
    assert f["paired_frac_slope_present"] is True


def test_empty_window_returns_blank():
    # NOII exists but nothing in [15:50, 15:55:10] -> all-zero, all-absent
    win = pl.DataFrame(
        [_row(et_ns(SESSION, 15, 45, 0), "B", 100_000.0, 0.0, 100.0)],
        schema=NOII_SCHEMA, orient="row",
    )
    f = evo_features("NVDA", SESSION, adv20=ADV, side=SIDE, m0=M0, noii_frame=win)
    for c in EVO_FEATURES:
        assert f[c] == 0.0
        assert f[f"{c}_present"] is False


# --------------------------------------------------------------------------- winsor


def test_winsor_fit_and_apply_clip():
    df = pl.DataFrame({"imb_velocity": [float(x) for x in range(0, 101)]})
    bounds = fit_winsor_bounds(df, ("imb_velocity",))
    lo, hi = bounds["imb_velocity"]
    assert math.isclose(lo, 1.0, abs_tol=1e-6) and math.isclose(hi, 99.0, abs_tol=1e-6)
    clipped = apply_winsor(
        pl.DataFrame({"imb_velocity": [-50.0, 50.0, 500.0]}), bounds
    )
    assert clipped["imb_velocity"].to_list() == [1.0, 50.0, 99.0]


# --------------------------------------------------------------------------- leakage (synthetic)


def test_reconstruct_basis_matches_snapshot_synthetic():
    """Hermetic leakage check: reconstruct basis at 15:55:10 from a hand NOII+BBO
    stream and compare to the canonical 1e4*(near-mid)/mid snapshot."""
    ts_dec = et_ns(SESSION, *DECISION_HMS)
    noii = pl.DataFrame(
        [
            _row(et_ns(SESSION, 15, 54, 0), "B", 100_000.0, 0.0, 100.0),      # near=0
            _row(et_ns(SESSION, 15, 55, 5), "B", 200_000.0, 100.50, 100.0),   # last near>0
            _row(ts_dec + 1_000_000_000, "S", 9_000_000.0, 200.0, 200.0),     # after -> ignored
        ],
        schema=NOII_SCHEMA, orient="row",
    )
    # bbo with prevailing mid = (99.9 + 100.1)/2 = 100.0 at 15:55:10
    bbo = pl.DataFrame(
        {
            "ts": [et_ns(SESSION, 15, 55, 0), et_ns(SESSION, 15, 55, 20)],
            "bid": [99.9, 90.0],
            "ask": [100.1, 90.2],
            "bid_size": [100.0, 100.0],
            "ask_size": [100.0, 100.0],
        }
    )
    recon = reconstruct_basis_bps("NVDA", SESSION, noii_frame=noii, bbo_frame=bbo)
    snapshot = 1e4 * (100.50 - 100.0) / 100.0  # 50 bps
    assert recon is not None
    assert abs(recon - snapshot) < 0.5


# --------------------------------------------------------------------------- leakage (real data)

_EVENTS = Path("research/experiments/M6-FINAL-basis/events.parquet")
_NOII = Path("data/raw/noii")
_BBO = Path("data/raw/bbo1s")


@pytest.mark.skipif(
    not (_EVENTS.exists() and _NOII.exists() and _BBO.exists()),
    reason="events.parquet or the NOII/BBO data lake is not present",
)
def test_reconstruct_basis_matches_events_parquet_real():
    """MANDATORY leakage invariant on REAL data: a basis reconstructed at 15:55:10
    from the raw NOII+BBO stream equals the pre-computed events.parquet basis_bps to
    < 0.5 bps — the decision-instant snapshot the M8/M9 models trust is exactly what
    the path features are anchored to (no forward information)."""
    ev = pl.read_parquet(_EVENTS).filter(pl.col("basis_bps").abs() >= 10.0)
    assert ev.height > 0
    sample = ev.sample(min(40, ev.height), seed=17)
    worst = 0.0
    for r in sample.iter_rows(named=True):
        recon = reconstruct_basis_bps(r["symbol"], r["session"])
        assert recon is not None, (r["symbol"], r["session"])
        d = abs(recon - r["basis_bps"])
        worst = max(worst, d)
        assert d < 0.5, (r["symbol"], r["session"], r["basis_bps"], recon)
    assert worst < 0.5
