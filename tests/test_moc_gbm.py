"""Tests for models/moc_gbm.py — the M6-GBM cell.

Synthetic frames + hand-computed literals only (no disk, no network). Covers the
four registered checks: feature PIT (a post-15:50:10 message cannot move a
feature), fold embargo (1-session gap, train strictly before test), gate
determinism, and one fully hand-built feature vector.
"""

from __future__ import annotations

import math

import numpy as np
import polars as pl

from enginev51.data.noii import NOII_SCHEMA, et_ns
from enginev51.models.moc_gbm import (
    FEATURE_COLS,
    build_features,
    gate,
    noii_pit_features,
    run_walk_forward,
    trailing_vol20,
    walk_forward_folds_calendar,
)

SESSION = "2025-06-02"


def _row(ts, side, imb, near, ref, far, paired):
    return {
        "ts": ts, "side": side, "imbalance_shares": imb, "paired_shares": paired,
        "near_price": near, "far_price": far, "ref_price": ref,
    }


def _hand_frame():
    """3 in-window messages at 15:46 / 15:48 / 15:50:10, all buy-side, with
    non-zero near/far so the price features are actually exercised."""
    return pl.DataFrame(
        [
            _row(et_ns(SESSION, 15, 46, 0), "B", 200_000.0, 100.0, 100.1, 100.2, 800_000.0),
            _row(et_ns(SESSION, 15, 48, 0), "B", 300_000.0, 100.5, 100.4, 100.7, 900_000.0),
            _row(et_ns(SESSION, 15, 50, 10), "B", 400_000.0, 101.0, 100.9, 101.3, 1_000_000.0),
        ],
        schema=NOII_SCHEMA, orient="row",
    )


ADV = 1_000_000_000.0
CLOSES = [
    ("2025-05-27", 100.0), ("2025-05-28", 101.0),
    ("2025-05-29", 102.0), ("2025-05-30", 103.0),
    ("2025-06-02", 999.0),  # the event day itself — must be excluded (PIT)
]


# --------------------------------------------------------------------------- hand vector


def test_hand_built_feature_vector():
    feat = build_features("NVDA", SESSION, adv20=ADV, noii_frame=_hand_frame(), closes=CLOSES)
    assert feat is not None

    # norm_imb = +1 * 400000 * 101.0 / 1e9
    assert feat["norm_imb"] == 400_000.0 * 101.0 / ADV
    assert feat["side"] == 1.0
    # paired_ratio = 1_000_000 / (1_000_000 + 400_000)
    assert feat["paired_ratio"] == 1_000_000.0 / 1_400_000.0

    imb48 = 300_000.0 * 100.5 / ADV
    imb46 = 200_000.0 * 100.0 / ADV
    assert math.isclose(feat["imb_growth_48"], feat["norm_imb"] - imb48, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(feat["imb_growth_46"], feat["norm_imb"] - imb46, rel_tol=0, abs_tol=1e-15)

    # near-ref bps = (101.0 - 100.9)/100.9 * 1e4 ; near-far = (101.0-101.3)/101.3*1e4
    assert math.isclose(feat["near_ref_bps"], (101.0 - 100.9) / 100.9 * 1e4, abs_tol=1e-9)
    assert math.isclose(feat["near_far_bps"], (101.0 - 101.3) / 101.3 * 1e4, abs_tol=1e-9)
    # near drift 15:46->15:50 = (101.0 - 100.0)/100.0 * 1e4 = 100 bps
    assert math.isclose(feat["near_drift_46_50"], 100.0, abs_tol=1e-9)

    assert feat["msg_count"] == 3.0
    assert math.isclose(feat["log_adv20"], math.log(ADV), abs_tol=1e-12)

    # trailing vol = sample std of log-returns of [100,101,102,103]
    rets = np.diff(np.log(np.array([100.0, 101.0, 102.0, 103.0])))
    assert math.isclose(feat["vol20"], float(np.std(rets, ddof=1)), abs_tol=1e-12)

    # symbol one-hot
    assert feat["oh_NVDA"] == 1.0
    assert feat["oh_TSLA"] == 0.0 and feat["oh_GOOGL"] == 0.0
    # every feature column present
    for c in FEATURE_COLS:
        assert c in feat


def test_vol20_excludes_event_day():
    # event-day close (999.0) must never enter the trailing window (PIT)
    v = trailing_vol20(CLOSES, SESSION)
    rets = np.diff(np.log(np.array([100.0, 101.0, 102.0, 103.0])))
    assert math.isclose(v, float(np.std(rets, ddof=1)), abs_tol=1e-12)


# --------------------------------------------------------------------------- PIT


def test_feature_pit_message_after_signal_is_ignored():
    base = noii_pit_features(_hand_frame(), SESSION, ADV)
    assert base is not None
    # a NOII message strictly AFTER 15:50:10 must not change any feature
    later = pl.concat([
        _hand_frame(),
        pl.DataFrame(
            [_row(et_ns(SESSION, 15, 50, 20), "S", 9_999_999.0, 50.0, 50.0, 50.0, 1.0)],
            schema=NOII_SCHEMA, orient="row",
        ),
    ])
    after = noii_pit_features(later, SESSION, ADV)
    assert after == base


def test_feature_pit_via_build_features():
    a = build_features("NVDA", SESSION, adv20=ADV, noii_frame=_hand_frame(), closes=CLOSES)
    later = pl.concat([
        _hand_frame(),
        pl.DataFrame(
            [_row(et_ns(SESSION, 15, 59, 0), "S", 5_000_000.0, 200.0, 200.0, 200.0, 5.0)],
            schema=NOII_SCHEMA, orient="row",
        ),
    ])
    b = build_features("NVDA", SESSION, adv20=ADV, noii_frame=later, closes=CLOSES)
    assert a == b


# --------------------------------------------------------------------------- folds


def test_fold_embargo_and_no_leakage():
    # daily sessions across ~4.5 years so >=2y train + 6-month blocks produce folds
    from datetime import date, timedelta

    days: list[str] = []
    d = date(2021, 1, 4)
    end = date(2025, 6, 30)
    while d <= end:
        if d.weekday() < 5:
            days.append(d.isoformat())
        d += timedelta(days=1)

    folds = walk_forward_folds_calendar(days, initial_train_years=2,
                                        test_block_months=6, embargo_sessions=1)
    assert len(folds) >= 4
    for f in folds:
        # test block fully at/after its start, before its end
        assert all(f.test_start <= s < f.test_end for s in f.test_sessions)
        # every train session strictly before the test block start
        assert max(f.train_sessions) < f.test_start
        assert max(f.train_sessions) < min(f.test_sessions)
        # 1-session embargo: the session immediately before test_start is NOT in train
        before = [s for s in days if s < f.test_start]
        embargoed = before[-1]
        assert embargoed not in f.train_sessions
        assert f.train_sessions == tuple(before[:-1])
    # first block starts >= first_session + 2y
    assert folds[0].test_start >= "2023-01-04"


# --------------------------------------------------------------------------- gate


def test_gate_rule_and_determinism():
    assert gate(0.5) is True
    assert gate(-0.5) is False
    assert gate(0.0) is False  # strict > 0
    arr = np.array([-1.0, 0.0, 1e-9, 3.0])
    out = gate(arr)
    assert out.tolist() == [False, False, True, True]
    # deterministic: identical input -> identical output
    assert gate(arr).tolist() == gate(arr.copy()).tolist()


def _synthetic_feat_df(n_years: float = 4.0) -> pl.DataFrame:
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
                rows.append({
                    "session": sess, "symbol": sym, "net_bps": float(rng.normal(2, 50)),
                    "norm_imb": ni, "side": 1.0 if ni >= 0 else -1.0,
                    "paired_ratio": float(rng.uniform(0.5, 0.9)),
                    "imb_growth_48": ni, "imb_growth_46": ni,
                    "near_ref_bps": 0.0, "near_far_bps": 0.0, "near_drift_46_50": 0.0,
                    "msg_count": 2.0, "log_adv20": float(rng.uniform(20, 22)),
                    "vol20": float(rng.uniform(0.01, 0.05)),
                    "oh_NVDA": 1.0 if sym == "NVDA" else 0.0,
                    "oh_TSLA": 1.0 if sym == "TSLA" else 0.0,
                    "oh_AMD": 0.0, "oh_MU": 0.0, "oh_GOOGL": 0.0,
                })
        d += timedelta(days=1)
    return pl.DataFrame(rows)


def test_walk_forward_determinism_and_oos_span():
    feat = _synthetic_feat_df()
    oos1, imp1, folds = run_walk_forward(feat)
    oos2, imp2, _ = run_walk_forward(feat)
    assert oos1.height > 0 and len(folds) >= 4
    # OOS only covers events beyond the initial-train span (first block start)
    assert oos1["session"].min() >= folds[0].test_start
    # deterministic predictions run-to-run
    assert np.allclose(oos1["pred"].to_numpy(), oos2["pred"].to_numpy())
    # importances cover every feature
    assert set(imp1["feature"].to_list()) == set(FEATURE_COLS)
    assert imp1.equals(imp2)
