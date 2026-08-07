"""Tests for apps/run_basis_trial.py — the M6-FINAL near-price basis cell.

Synthetic frames + hand-computed literals only (no disk, no network). Covers the
registered checks: basis PIT (a 15:55:11 message excluded, a near_price=0 message
skipped), a hand-computed basis + entry fill on a synthetic BBO, the direction
sign, the holdout guard, a hand-built GBM feature vector, and the GBM fold embargo
/ OOS-span / determinism.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from enginev51.apps.run_basis_trial import (
    FEATURE_COLS,
    _session_closes,
    assert_before_holdout,
    basis_bps_of,
    basis_pit_features,
    direction_of,
    near_at,
    run_walk_forward_basis,
)
from enginev51.backtest.auction_replay import tape_from_bbo
from enginev51.backtest.fills import market_fill, prevailing_mid
from enginev51.data.bbo1s import BBO_SCHEMA
from enginev51.data.noii import NOII_SCHEMA, et_ns
from enginev51.protocol import SealViolation

SESSION = "2025-06-02"
SLIP = 0.5
TOL = 1e-9


def _row(ts, side, imb, near, ref, far, paired):
    return {
        "ts": ts, "side": side, "imbalance_shares": imb, "paired_shares": paired,
        "near_price": near, "far_price": far, "ref_price": ref,
    }


# --------------------------------------------------------------------------- basis PIT


def test_near_at_excludes_message_after_signal():
    """A NOII message strictly AFTER 15:55:10 can never govern the basis (PIT)."""
    frame = pl.DataFrame(
        [
            _row(et_ns(SESSION, 15, 55, 0), "B", 100_000.0, 100.5, 100.4, 100.6, 500_000.0),
            _row(et_ns(SESSION, 15, 55, 10), "B", 200_000.0, 101.0, 100.9, 101.3, 600_000.0),
            _row(et_ns(SESSION, 15, 55, 11), "B", 300_000.0, 999.0, 999.0, 999.0, 700_000.0),
        ],
        schema=NOII_SCHEMA, orient="row",
    )
    ts_sig = et_ns(SESSION, 15, 55, 10)
    # the 15:55:11 near=999 is excluded; the governing near is the 15:55:10 value.
    assert near_at(frame, ts_sig) == pytest.approx(101.0, abs=TOL)


def test_near_at_skips_zero_near_messages():
    """A message whose near_price is 0 (indicative price not yet computable) is
    skipped; the last STRICTLY-POSITIVE near at-or-before 15:55:10 governs."""
    frame = pl.DataFrame(
        [
            _row(et_ns(SESSION, 15, 55, 8), "B", 100_000.0, 101.0, 100.9, 101.3, 500_000.0),
            _row(et_ns(SESSION, 15, 55, 10), "B", 200_000.0, 0.0, 100.9, 0.0, 600_000.0),
        ],
        schema=NOII_SCHEMA, orient="row",
    )
    ts_sig = et_ns(SESSION, 15, 55, 10)
    # the 15:55:10 message has near_price=0 -> skipped -> the 15:55:08 near governs.
    assert near_at(frame, ts_sig) == pytest.approx(101.0, abs=TOL)


def test_near_at_none_when_no_positive_near():
    frame = pl.DataFrame(
        [_row(et_ns(SESSION, 15, 55, 0), "B", 100_000.0, 0.0, 100.4, 0.0, 500_000.0)],
        schema=NOII_SCHEMA, orient="row",
    )
    assert near_at(frame, et_ns(SESSION, 15, 55, 10)) is None
    assert near_at(None, et_ns(SESSION, 15, 55, 10)) is None
    assert near_at(pl.DataFrame(schema=NOII_SCHEMA), et_ns(SESSION, 15, 55, 10)) is None


# --------------------------------------------------------------------------- basis + fill


def _bbo_row(ts, bid, ask):
    return {"ts": ts, "bid": bid, "ask": ask, "bid_size": 100.0, "ask_size": 100.0}


def test_hand_computed_basis_and_entry_fill():
    """A synthetic BBO (bid 99, ask 100 -> mid 99.5) and near 100.0 give a
    hand-computed basis and a taker market-buy entry fill."""
    bbo = pl.DataFrame(
        [_bbo_row(et_ns(SESSION, 15, 55, 9), 99.0, 100.0)],
        schema=BBO_SCHEMA, orient="row",
    )
    tape = tape_from_bbo("NVDA", bbo)
    ts_sig = et_ns(SESSION, 15, 55, 10)
    mid = prevailing_mid(tape.q_ts, tape.q_bid, tape.q_ask, ts_sig)
    assert mid == pytest.approx(99.5, abs=TOL)

    near = 100.0
    basis = basis_bps_of(near, mid)
    assert basis == pytest.approx(1e4 * (100.0 - 99.5) / 99.5, abs=TOL)  # ~50.25 bps
    assert direction_of(near, mid) == 1  # near > mid -> buy

    # taker market BUY at the signal instant: lifts ask*(1+slip).
    mk = market_fill(tape.q_ts, tape.q_bid, tape.q_ask, ts_sig, 1, SLIP)
    assert mk is not None
    entry_px, entry_mid = mk
    assert entry_px == pytest.approx(100.0 * (1.0 + SLIP * 1e-4), abs=TOL)
    assert entry_mid == pytest.approx(99.5, abs=TOL)


def test_direction_sign():
    assert direction_of(101.0, 100.0) == 1   # near > mid -> buy
    assert direction_of(99.0, 100.0) == -1   # near < mid -> sell
    assert direction_of(100.0, 100.0) == 0   # coincide -> no tradable basis
    assert basis_bps_of(101.0, 100.0) == pytest.approx(100.0, abs=TOL)
    assert basis_bps_of(99.0, 100.0) == pytest.approx(-100.0, abs=TOL)


# --------------------------------------------------------------------------- holdout guard


def test_holdout_guard():
    from datetime import date

    assert_before_holdout(date(2026, 5, 31))  # ok
    # SealViolation, not AssertionError: the guard must survive `python -O` (B7/J2).
    with pytest.raises(SealViolation):
        assert_before_holdout(date(2026, 6, 1))  # the sealed boundary
    with pytest.raises(SealViolation):
        assert_before_holdout(date(2026, 7, 1))


# --------------------------------------------------------------------------- feature vector


def _hand_noii_frame():
    """Prior 15:51 / 15:53 messages (near not yet populated -> 0) and the 15:55:10
    governing message with near/far/ref all > 0 — exercises every feature."""
    return pl.DataFrame(
        [
            _row(et_ns(SESSION, 15, 51, 0), "B", 200_000.0, 0.0, 100.1, 0.0, 800_000.0),
            _row(et_ns(SESSION, 15, 53, 0), "B", 300_000.0, 0.0, 100.4, 0.0, 900_000.0),
            _row(et_ns(SESSION, 15, 55, 10), "B", 400_000.0, 101.0, 100.9, 101.3, 1_000_000.0),
        ],
        schema=NOII_SCHEMA, orient="row",
    )


def test_hand_built_feature_vector():
    adv = 1_000_000_000.0
    near, mid = 101.0, 100.0
    feat = basis_pit_features(_hand_noii_frame(), SESSION, adv, near, mid)

    # norm_imb uses the basis near price (101.0) and the buy-side (+1) imbalance.
    assert feat["norm_imb"] == pytest.approx(400_000.0 * 101.0 / adv, abs=TOL)
    assert feat["side"] == 1.0
    assert feat["paired_ratio"] == pytest.approx(1_000_000.0 / 1_400_000.0, abs=TOL)

    # growth vs 15:53/15:51 uses signal_at's near->ref fallback there (near=0).
    imb53 = 300_000.0 * 100.4 / adv
    imb51 = 200_000.0 * 100.1 / adv
    assert feat["imb_growth_53"] == pytest.approx(feat["norm_imb"] - imb53, abs=1e-15)
    assert feat["imb_growth_51"] == pytest.approx(feat["norm_imb"] - imb51, abs=1e-15)

    # near-ref / near-far bps from the 15:55:10 governing row.
    assert feat["near_ref_bps"] == pytest.approx((101.0 - 100.9) / 100.9 * 1e4, abs=1e-9)
    assert feat["near_far_bps"] == pytest.approx((101.0 - 101.3) / 101.3 * 1e4, abs=1e-9)
    # near_drift DEGENERATES to 0 (near is 0 at 15:51 -> no drift base).
    assert feat["near_drift_51_55"] == 0.0

    assert feat["msg_count"] == 3.0
    # basis_bps = 1e4*(101-100)/100 = 100 bps.
    assert feat["basis_bps"] == pytest.approx(100.0, abs=TOL)


def test_feature_pit_message_after_signal_ignored():
    adv = 1_000_000_000.0
    base = basis_pit_features(_hand_noii_frame(), SESSION, adv, 101.0, 100.0)
    later = pl.concat([
        _hand_noii_frame(),
        pl.DataFrame(
            [_row(et_ns(SESSION, 15, 55, 20), "S", 9_999_999.0, 50.0, 50.0, 50.0, 1.0)],
            schema=NOII_SCHEMA, orient="row",
        ),
    ])
    after = basis_pit_features(later, SESSION, adv, 101.0, 100.0)
    assert after == base


# --------------------------------------------------------------------------- GBM folds


def _synthetic_events(n_years: float = 4.0) -> pl.DataFrame:
    from datetime import date, timedelta

    rng = np.random.default_rng(3)
    rows = []
    d = date(2021, 1, 4)
    end = d + timedelta(days=int(365 * n_years))
    while d <= end:
        if d.weekday() < 5:
            sess = d.isoformat()
            for sym in ("NVDA", "TSLA"):
                ni = float(rng.normal(0, 0.01))
                basis = float(rng.normal(0, 30))
                rows.append({
                    "session": sess, "symbol": sym, "net_bps": float(rng.normal(2, 50)),
                    "norm_imb": ni, "side": 1.0 if basis >= 0 else -1.0,
                    "paired_ratio": float(rng.uniform(0.5, 0.9)),
                    "imb_growth_53": ni, "imb_growth_51": ni,
                    "near_ref_bps": float(rng.normal(0, 5)),
                    "near_far_bps": float(rng.normal(0, 5)),
                    "near_drift_51_55": 0.0, "msg_count": 40.0,
                    "log_adv20": float(rng.uniform(20, 24)),
                    "vol20": float(rng.uniform(0.01, 0.05)), "basis_bps": basis,
                    "oh_NVDA": 1.0 if sym == "NVDA" else 0.0,
                    "oh_TSLA": 1.0 if sym == "TSLA" else 0.0,
                    "oh_AMD": 0.0, "oh_MU": 0.0, "oh_GOOGL": 0.0,
                })
        d += timedelta(days=1)
    return pl.DataFrame(rows)


def test_gbm_fold_embargo_and_oos_span():
    feat = _synthetic_events()
    oos1, imp1, folds = run_walk_forward_basis(feat)
    oos2, imp2, _ = run_walk_forward_basis(feat)

    assert oos1.height > 0 and len(folds) >= 4
    days = sorted(feat["session"].unique().to_list())
    for f in folds:
        # test block fully inside [test_start, test_end)
        assert all(f.test_start <= s < f.test_end for s in f.test_sessions)
        # train strictly before the test block, with the 1-session embargo gap
        assert max(f.train_sessions) < min(f.test_sessions)
        before = [s for s in days if s < f.test_start]
        assert before[-1] not in f.train_sessions          # embargoed session
        assert f.train_sessions == tuple(before[:-1])
    # OOS covers only events beyond the initial-train span
    assert oos1["session"].min() >= folds[0].test_start
    # basis_bps is a real feature the model can use
    assert "basis_bps" in FEATURE_COLS
    assert set(imp1["feature"].to_list()) == set(FEATURE_COLS)
    # deterministic run-to-run
    assert np.allclose(oos1["pred"].to_numpy(), oos2["pred"].to_numpy())
    assert imp1.equals(imp2)


# --------------------------------------------------------------------------- bar_close source


def test_session_closes_prefers_official_daily_close(monkeypatch):
    """F6 regression (code review 2026-07-17): ``bar_close`` feeds the
    cross-vs-official-close validation, so it must carry the bars1d OFFICIAL
    close wherever one exists — the last RTH 1m bar (the old source) is the
    15:59 bar, not the closing cross. The 1m close remains only a fallback for
    sessions the daily file lacks."""
    import types

    from enginev51.apps import run_basis_trial as rbt

    # 1m bars: last bar of each session closes at 100.00 / 200.00
    bars = pl.DataFrame(
        {
            "ts": [
                et_ns("2026-01-05", 15, 59, 0),
                et_ns("2026-01-06", 15, 59, 0),
            ],
            "close": [100.00, 200.00],
        }
    )
    monkeypatch.setattr(rbt.store, "load_bars", lambda roots, feed, symbol: bars)
    # official daily close exists only for the 5th, and differs from the 1m bar
    monkeypatch.setattr(rbt, "official_daily_closes", lambda symbol: {"2026-01-05": 100.55})

    settings = types.SimpleNamespace(data_feed_type="sip", read_roots=[])
    closes = _session_closes(settings, "NVDA")
    assert closes["2026-01-05"] == pytest.approx(100.55)  # official close wins
    assert closes["2026-01-06"] == pytest.approx(200.00)  # 1m fallback only
