"""M18 runner summary invariants — maker fill-rate definition (§3/§5), meta veto
partition, and the B5 re-pricings on the system verdict streams.

These exercise ``runner._summarise`` directly on a hand-built event frame so the
counts are exact and data-free.
"""

from __future__ import annotations

import polars as pl

from enginev51.reversion.runner import _summarise

# Columns every summarised event frame carries (metrics null for cancels).
_METRIC_COLS = (
    "maker_net", "maker_gross", "maker_mid_to_mid",
    "taker_net", "taker_gross", "taker_mid_to_mid", "shares",
)


def _row(*, opened, posted, filled, g1=False, g2=False, scored=False, kept=True,
         through=False, keep50=False, net=1.0):
    r = {
        "symbol": "MU", "session": "2025-03-03",
        "opened": opened, "maker_posted": posted, "maker_filled": filled,
        "passed_G1": g1, "passed_G2": g2, "meta_scored": scored, "meta_kept": kept,
        "maker_fill_through": through, "keep_50": keep50,
    }
    for c in _METRIC_COLS:
        r[c] = (net if filled else None)
    return r


def _frame():
    rows = []
    # filled, gated, scored+kept  (→ gated_meta)          ×3
    rows += [_row(opened=True, posted=True, filled=True, g1=True, g2=True,
                  scored=True, kept=True, through=(i == 0), keep50=(i == 1))
             for i in range(3)]
    # filled, gated, scored+vetoed                         ×2
    rows += [_row(opened=True, posted=True, filled=True, g1=True, g2=True,
                  scored=True, kept=False) for _ in range(2)]
    # filled, gated, UNSCORED (pre-first-fold month)       ×4
    rows += [_row(opened=True, posted=True, filled=True, g1=True, g2=True,
                  scored=False, kept=True) for _ in range(4)]
    # filled, NOT gated                                    ×5
    rows += [_row(opened=True, posted=True, filled=True, g1=False, g2=True)
             for _ in range(5)]
    # maker POSTS that cancelled after 60 s (unfilled)     ×6
    rows += [_row(opened=False, posted=True, filled=False) for _ in range(6)]
    return pl.DataFrame(rows)


def test_maker_fill_rate_is_filled_over_posted():
    s = _summarise(_frame(), "MU", "30m", "maker", meta_trained=True)
    # 14 filled opens + 6 cancels = 20 posts; rate is NOT 1.0-by-construction.
    assert s["n_posted"] == 20
    assert s["n_filled"] == 14
    assert s["n_cancelled"] == 6
    assert s["n_posted"] == s["n_filled"] + s["n_cancelled"]
    assert abs(s["maker_fill_rate"] - 14 / 20) < 1e-12
    # cancels are excluded from the traded streams (opened=False).
    assert s["streams"]["raw_maker"]["n"] == 14


def test_meta_veto_partition_no_silent_drop():
    s = _summarise(_frame(), "MU", "30m", "maker", meta_trained=True)
    meta = s["meta"]
    # 9 gated = 5 scored + 4 unscored; gated_meta = 5 scored − 2 vetoed = 3.
    assert meta["n_gated"] == 9
    assert meta["n_scored"] == 5
    assert meta["n_vetoed"] == 2
    assert meta["n_unscored"] == 4
    assert meta["n_gated"] == meta["n_scored"] + meta["n_unscored"]
    assert s["streams"]["gated"]["n"] == 9
    assert s["streams"]["gated_meta"]["n"] == meta["n_scored"] - meta["n_vetoed"] == 3


def test_b5_repricings_on_system_streams_present_and_subset():
    s = _summarise(_frame(), "MU", "30m", "maker", meta_trained=True)
    st = s["streams"]
    for key in ("gated_b5_through", "gated_b5_haircut50",
                "gated_meta_b5_through", "gated_meta_b5_haircut50"):
        assert key in st, f"missing B5 stream {key}"
    # through ⊆ haircut ⊆ stream; and gated_meta B5 ⊆ gated B5.
    assert st["gated_b5_through"]["n"] <= st["gated_b5_haircut50"]["n"] <= st["gated"]["n"]
    assert st["gated_meta_b5_through"]["n"] <= st["gated_meta_b5_haircut50"]["n"] <= st["gated_meta"]["n"]
    # raw-population B5 columns are retained too (attribution).
    assert "b5_through" in st and "b5_haircut50" in st
