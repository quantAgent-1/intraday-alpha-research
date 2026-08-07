"""Tests for models/moc_meta.py — the M8 meta-labeling cell.

Synthetic frames + hand literals only (no disk, no network). Covers the five
registered checks: meta-label correctness, fold PIT/embargo (no train row dated
>= its test-block start), gate determinism, feature-frame completeness, and a
monotonic-ish calibration curve on a separable synthetic case.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import polars as pl

from enginev51.models.moc_meta import (
    CANDIDATE_BASIS_BPS,
    FEATURE_COLS,
    LABEL_COL,
    NET_COL,
    PRED_COL,
    build_meta_frame,
    calibration_table,
    candidates,
    gate,
    run_walk_forward,
)

UNIVERSE = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")


def _oh(sym: str) -> dict:
    return {f"oh_{s}": (1.0 if s == sym else 0.0) for s in UNIVERSE}


def _feat_row(session: str, symbol: str, *, basis: float, net: float, sep: float = 0.0) -> dict:
    """One synthetic candidate row carrying every registered feature column.

    ``sep`` optionally injects a signal into ``near_far_bps`` correlated with the
    label, used by the calibration test; the base rows leave it at 0.
    """
    row = {
        "session": session, "symbol": symbol, NET_COL: net,
        "basis_bps": basis,
        "near_far_bps": sep,
        "near_ref_bps": 1.0,
        "paired_ratio": 0.7,
        "norm_imb": 0.001 * np.sign(basis),
        "imb_growth_53": 0.0,
        "imb_growth_51": 0.0,
        "msg_count": 40.0,
        "vol20": 0.02,
        "log_adv20": 21.0,
    }
    row.update(_oh(symbol))
    return row


def _trading_days(start: date, end: date) -> list[str]:
    out: list[str] = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


# --------------------------------------------------------------------------- meta-label


def test_meta_label_correctness():
    events = pl.DataFrame([
        _feat_row("2021-01-04", "NVDA", basis=12.0, net=5.0),    # win  -> 1
        _feat_row("2021-01-04", "TSLA", basis=-15.0, net=-3.0),  # loss -> 0
        _feat_row("2021-01-05", "AMD", basis=11.0, net=0.0),     # exactly 0 -> 0 (strict >)
        _feat_row("2021-01-05", "MU", basis=9.9, net=8.0),       # |basis|<10 -> NOT a candidate
    ], orient="row")
    meta = build_meta_frame(events)
    # |basis| >= 10 keeps 3 of the 4 rows
    assert meta.height == 3
    labels = dict(zip(
        (meta["symbol"] + "|" + meta["session"]).to_list(),
        meta[LABEL_COL].to_list(), strict=True,
    ))
    assert labels["NVDA|2021-01-04"] == 1
    assert labels["TSLA|2021-01-04"] == 0
    assert labels["AMD|2021-01-05"] == 0  # net==0 is NOT a win (strict > 0)
    # label is exactly the indicator net_bps > 0
    chk = meta.with_columns((pl.col(NET_COL) > 0.0).cast(pl.Int8).alias("_y"))
    assert chk[LABEL_COL].to_list() == chk["_y"].to_list()
    # MU (|basis| 9.9) is excluded from the candidate universe
    assert "MU" not in meta["symbol"].to_list()


def test_candidate_threshold():
    events = pl.DataFrame([
        _feat_row("2021-01-04", "NVDA", basis=10.0, net=1.0),   # exactly 10 -> kept (>=)
        _feat_row("2021-01-04", "TSLA", basis=-10.0, net=1.0),  # -10 kept
        _feat_row("2021-01-04", "AMD", basis=9.999, net=1.0),   # just under -> dropped
    ], orient="row")
    c = candidates(events)
    assert c.height == 2
    assert set(c["symbol"].to_list()) == {"NVDA", "TSLA"}
    assert CANDIDATE_BASIS_BPS == 10.0


# --------------------------------------------------------------------------- feature completeness


def test_feature_frame_completeness():
    events = pl.DataFrame([
        _feat_row("2021-01-04", "NVDA", basis=12.0, net=5.0),
    ], orient="row")
    meta = build_meta_frame(events)
    for c in FEATURE_COLS:
        assert c in meta.columns, f"missing registered feature {c}"
    # exactly 10 numeric + 5 one-hot = 15 features; `side` MUST NOT be a feature
    assert len(FEATURE_COLS) == 15
    assert "side" not in FEATURE_COLS
    # one-hot columns are the fixed universe in order
    assert FEATURE_COLS[-5:] == tuple(f"oh_{s}" for s in UNIVERSE)


# --------------------------------------------------------------------------- gate


def test_gate_rule_and_determinism():
    # registered gate: TAKE iff P(win) >= q (inclusive threshold)
    assert gate(0.60, 0.60) is True   # exactly q -> taken
    assert gate(0.59, 0.60) is False
    assert gate(0.75, 0.50) is True
    arr = np.array([0.49, 0.50, 0.55, 0.60, 0.61])
    assert gate(arr, 0.50).tolist() == [False, True, True, True, True]
    assert gate(arr, 0.55).tolist() == [False, False, True, True, True]
    assert gate(arr, 0.60).tolist() == [False, False, False, True, True]
    # deterministic: identical input -> identical output
    assert gate(arr, 0.55).tolist() == gate(arr.copy(), 0.55).tolist()


# --------------------------------------------------------------------------- fold PIT / embargo


def _synthetic_meta_df(n_years: float = 4.0, sep: float = 0.0, seed: int = 3) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    days = _trading_days(date(2021, 1, 4), date(2021, 1, 4) + timedelta(days=int(365 * n_years)))
    rows: list[dict] = []
    for sess in days:
        for sym in ("NVDA", "TSLA", "AMD"):
            # separable signal: near_far_bps carries the label when sep>0
            latent = float(rng.normal(0, 1))
            signal = sep * latent
            net = 20.0 * latent + float(rng.normal(0, 5))  # sign(net) ~ sign(latent) as sep drives it
            basis = 12.0 * (1 if rng.random() > 0.5 else -1)
            r = _feat_row(sess, sym, basis=basis, net=net, sep=signal)
            rows.append(r)
    events = pl.DataFrame(rows, orient="row")
    return build_meta_frame(events)


def test_fold_pit_and_embargo_no_leakage():
    meta = _synthetic_meta_df(n_years=4.0)
    oos, importances, folds = run_walk_forward(meta)
    assert len(folds) >= 4
    all_sessions = sorted(meta["session"].unique().to_list())
    for f in folds:
        # every train session strictly before the test-block start (PIT)
        assert max(f.train_sessions) < f.test_start
        assert max(f.train_sessions) < min(f.test_sessions)
        # test block within [test_start, test_end)
        assert all(f.test_start <= s < f.test_end for s in f.test_sessions)
        # 1-session embargo: the session immediately before test_start is excluded
        before = [s for s in all_sessions if s < f.test_start]
        assert before[-1] not in f.train_sessions
        assert f.train_sessions == tuple(before[:-1])
    # first block starts >= first_session + 2y
    assert folds[0].test_start >= "2023-01-04"
    # OOS carries a p_win in [0,1] for every emitted candidate (binary prob)
    assert oos.height > 0
    pw = oos[PRED_COL].to_numpy()
    assert np.all((pw >= 0.0) & (pw <= 1.0))
    # importances cover exactly the registered features
    assert set(importances["feature"].to_list()) == set(FEATURE_COLS)


def test_oos_span_equals_beyond_initial_train():
    """OOS candidates are exactly the union of the folds' test sessions (every
    candidate beyond the initial-train span, none before)."""
    meta = _synthetic_meta_df(n_years=4.0)
    oos, _imp, folds = run_walk_forward(meta)
    test_sessions: set = set()
    for f in folds:
        test_sessions |= set(f.test_sessions)
    assert set(oos["session"].unique().to_list()) == test_sessions
    # no OOS session precedes the first test block
    assert oos["session"].min() >= folds[0].test_start


# --------------------------------------------------------------------------- calibration


def test_calibration_bins_and_monotonic_separable():
    # strongly separable: net sign is driven by near_far_bps -> model ranks reliability
    meta = _synthetic_meta_df(n_years=5.0, sep=8.0, seed=11)
    oos, _imp, _folds = run_walk_forward(meta)
    cal = calibration_table(oos, n_bins=10)
    # equal-count deciles, all present, counts within +/-1 of each other
    assert cal.height == 10
    ns = cal["n"].to_list()
    assert max(ns) - min(ns) <= 1
    # realized win rate is monotonic-ish: top decile clearly beats bottom decile,
    # and Spearman rank correlation of (bin, realized) is strongly positive.
    realized = cal["realized_win_rate"].to_numpy()
    assert realized[-1] > realized[0] + 0.15
    bins = cal["bin"].to_numpy().astype(float)
    # Spearman == Pearson on ranks; bins are already ranks 0..9
    rank_r = np.corrcoef(bins, realized)[0, 1]
    assert rank_r > 0.8


def test_calibration_empty_frame():
    empty = pl.DataFrame(schema={PRED_COL: pl.Float64, LABEL_COL: pl.Int8})
    cal = calibration_table(empty)
    assert cal.height == 0
    assert set(cal.columns) == {
        "bin", "n", "pred_lo", "pred_hi", "pred_mean", "realized_win_rate"
    }
