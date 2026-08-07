"""Tests for models/m8v2_run.py -- the M8-v2 three-stream (v1 / v2 / Occam)
walk-forward harness (M3_REGISTRATION.md "M8-v2", REGISTERED 2026-07-20).

Synthetic frames + hand literals only (no disk, no network). Covers: the
Occam (baseline2) gate's boundary construction and TAKE rule, fold-boundary /
embargo PIT reuse of M8-v1's exact fold scheme (mirrors
tests/test_moc_meta.py::test_fold_pit_and_embargo_no_leakage), the pre-model
redundancy diagnostic's correlation math and train-span filtering, and basic
stream-metrics/shape sanity.
"""

from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np
import polars as pl

from enginev51.models import m8v2_features as f2
from enginev51.models import moc_meta
from enginev51.models.m8v2_run import (
    OCCAM_TAKEN_COL,
    P_V1,
    P_V2,
    V1_FEATURE_COLS,
    V2_FEATURE_COLS,
    build_streams,
    occam_boundary,
    occam_gate,
    redundancy_diagnostic,
    run_three_stream_walk_forward,
    stream_block,
)
from enginev51.models.moc_meta import LABEL_COL, NET_COL
from enginev51.models.moc_meta import UNIVERSE as V1_UNIVERSE


def _oh(sym: str) -> dict:
    return {f"oh_{s}": (1.0 if s == sym else 0.0) for s in V1_UNIVERSE}


def _trading_days(start: date, end: date) -> list[str]:
    out: list[str] = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _synth_row(session: str, symbol: str, *, net: float, rng: np.random.Generator) -> dict:
    row = {
        "session": session, "symbol": symbol, NET_COL: net,
        "basis_bps": float(rng.normal(0, 20)),
        "near_far_bps": 0.0, "near_ref_bps": 1.0, "paired_ratio": 0.7,
        "norm_imb": float(rng.normal(0, 0.001)),
        "imb_growth_53": 0.0, "imb_growth_51": 0.0, "msg_count": 40.0,
        "vol20": 0.02, "log_adv20": 21.0,
        "abs_f_over_adv": float(abs(rng.normal(0, 0.001))),
        "flow_aligned": float(rng.choice([-1.0, 0.0, 1.0])),
        "complex_intensity": float(abs(rng.normal(0, 0.01))),
        "range_pos_1555": float(rng.uniform(0, 1)),
        "month_end": float(rng.choice([0.0, 1.0], p=[0.9, 0.1])),
        "day_vol_ratio": float(abs(rng.normal(1.0, 0.3))),
    }
    row.update(_oh(symbol))
    return row


def _synthetic_frame(n_years: float = 4.0, seed: int = 3) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    days = _trading_days(date(2021, 1, 4), date(2021, 1, 4) + timedelta(days=int(365 * n_years)))
    rows: list[dict] = []
    for sess in days:
        for sym in ("NVDA", "TSLA", "AMD"):
            latent = float(rng.normal(0, 1))
            net = 20.0 * latent + float(rng.normal(0, 5))
            rows.append(_synth_row(sess, sym, net=net, rng=rng))
    df = pl.DataFrame(rows, orient="row")
    return df.with_columns((pl.col(NET_COL) > 0.0).cast(pl.Int8).alias(LABEL_COL))


# --------------------------------------------------------------------------- structural


def test_v2_feature_cols_extends_v1_verbatim():
    assert V2_FEATURE_COLS == V1_FEATURE_COLS + f2.FEATURE_COLS
    assert len(V1_FEATURE_COLS) == 15
    assert len(V2_FEATURE_COLS) == 21


# --------------------------------------------------------------------------- Occam gate (baseline2)


def test_occam_boundary_fits_on_positive_population_only():
    """The trailing top-tercile boundary is fit on abs_f_over_adv > 0 rows
    only (zero-complex rows must not drag the quantile down)."""
    train = pl.DataFrame(
        {
            "abs_f_over_adv": [0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "flow_aligned": [0.0] * 9,
        }
    )
    b = occam_boundary(train)
    expected = float(np.quantile(np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]), 2.0 / 3.0))
    assert math.isclose(b, expected, rel_tol=1e-9)


def test_occam_boundary_inf_when_no_positive_rows():
    train = pl.DataFrame({"abs_f_over_adv": [0.0, 0.0], "flow_aligned": [0.0, 1.0]})
    assert occam_boundary(train) == float("inf")


def test_occam_gate_rule_hand():
    df = pl.DataFrame(
        {
            "flow_aligned": [1.0, 1.0, -1.0, 0.0, 1.0],
            "abs_f_over_adv": [5.0, 0.5, 5.0, 5.0, 10.0],
        }
    )
    taken = occam_gate(df, boundary=2.0)
    assert taken.tolist() == [True, False, False, False, True]


def test_occam_gate_deterministic():
    df = pl.DataFrame({"flow_aligned": [1.0, -1.0], "abs_f_over_adv": [9.0, 9.0]})
    a = occam_gate(df, boundary=1.0)
    b = occam_gate(df, boundary=1.0)
    assert a.tolist() == b.tolist() == [True, False]


# --------------------------------------------------------------------------- fold PIT / embargo


def test_fold_pit_and_embargo_no_leakage():
    """Mirrors tests/test_moc_meta.py::test_fold_pit_and_embargo_no_leakage --
    proves this module's three-stream loop reuses M8-v1's IDENTICAL fold
    semantics (expanding calendar, >=2y initial train, 1-session embargo)."""
    frame = _synthetic_frame(n_years=4.0)
    oos, importances, folds = run_three_stream_walk_forward(frame)
    assert len(folds) >= 4
    all_sessions = sorted(frame["session"].unique().to_list())
    for f in folds:
        assert max(f.train_sessions) < f.test_start
        assert max(f.train_sessions) < min(f.test_sessions)
        assert all(f.test_start <= s < f.test_end for s in f.test_sessions)
        before = [s for s in all_sessions if s < f.test_start]
        assert before[-1] not in f.train_sessions
        assert f.train_sessions == tuple(before[:-1])
    assert folds[0].test_start >= "2023-01-04"

    assert oos.height > 0
    p1 = oos[P_V1].to_numpy()
    p2 = oos[P_V2].to_numpy()
    assert np.all((p1 >= 0.0) & (p1 <= 1.0))
    assert np.all((p2 >= 0.0) & (p2 <= 1.0))
    assert oos[OCCAM_TAKEN_COL].dtype == pl.Boolean
    assert set(importances["feature"].to_list()) == set(V2_FEATURE_COLS)
    new_feats_used = importances.filter(pl.col("is_v2_new"))["feature"].to_list()
    assert set(new_feats_used) == set(f2.FEATURE_COLS)


def test_oos_span_equals_beyond_initial_train():
    frame = _synthetic_frame(n_years=4.0)
    oos, _imp, folds = run_three_stream_walk_forward(frame)
    test_sessions: set = set()
    for f in folds:
        test_sessions |= set(f.test_sessions)
    assert set(oos["session"].unique().to_list()) == test_sessions
    assert oos["session"].min() >= folds[0].test_start


# --------------------------------------------------------------------------- redundancy diagnostic


def test_redundancy_diagnostic_detects_correlated_feature():
    rng = np.random.default_rng(5)
    n = 500
    norm_imb = rng.normal(0, 1, n)
    abs_f = norm_imb * 2.0 + rng.normal(0, 0.01, n)  # near-perfectly correlated
    sessions = [f"2024-01-{(i % 27) + 1:02d}" for i in range(n)]
    data = {
        "session": sessions, "abs_f_over_adv": abs_f, "norm_imb": norm_imb,
    }
    for c in moc_meta.NUMERIC_FEATURES:
        if c != "norm_imb":
            data[c] = np.zeros(n)
    df = pl.DataFrame(data)
    out = redundancy_diagnostic(df, train_end_iso="2024-12-31")
    assert out["n_train_rows"] == n
    corr = out["corr_abs_f_over_adv_vs_v1_feature"]["norm_imb"]
    assert corr > 0.95
    # a constant feature (std 0) reports None rather than NaN/crashing
    assert out["corr_abs_f_over_adv_vs_v1_feature"]["msg_count"] is None


def test_redundancy_diagnostic_respects_train_span():
    data = {"session": ["2020-01-01", "2026-05-01"], "abs_f_over_adv": [1.0, 1.0]}
    for c in moc_meta.NUMERIC_FEATURES:
        data[c] = [0.5, 999.0]
    df = pl.DataFrame(data)
    out = redundancy_diagnostic(df, train_end_iso="2020-06-01")
    # only the first row (session <= train_end_iso) enters the diagnostic
    assert out["n_train_rows"] == 1
    assert out["train_span"] == "session <= 2020-06-01"


# --------------------------------------------------------------------------- streams / metrics shape


def _tiny_oos() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "session": ["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-04"],
            "symbol": ["NVDA", "TSLA", "NVDA", "AMD"],
            NET_COL: [5.0, -3.0, 8.0, 2.0],
            P_V1: [0.6, 0.4, 0.7, 0.5],
            P_V2: [0.65, 0.3, 0.8, 0.4],
            OCCAM_TAKEN_COL: [True, False, True, False],
        }
    )


def test_build_streams_keys_present():
    streams = build_streams(_tiny_oos())
    assert "ungated_baseline" in streams
    for q in (0.50, 0.55, 0.60):
        assert f"baseline1_v1_gated_q{q:.2f}" in streams
        assert f"v2_gated_q{q:.2f}" in streams
    assert "occam_gated" in streams
    # occam_gated is exactly the True rows
    assert streams["occam_gated"].height == 2


def test_stream_block_basic_shape():
    block = stream_block(_tiny_oos())
    assert block["n"] == 4
    assert block["n_sessions"] == 3
    assert block["hit_rate"] == 0.75  # 3 of 4 rows have net_bps > 0
    assert set(block["symbols"]) == {"NVDA", "TSLA", "AMD"}
    assert block["n_years"] == 1
    assert "NVDA" in block["per_symbol"]
    assert block["per_symbol"]["NVDA"]["n"] == 2


def test_stream_block_empty_is_safe():
    empty = _tiny_oos().head(0)
    block = stream_block(empty)
    assert block["n"] == 0
    assert block["hit_rate"] is None
    assert block["net_bps_mean"] is None
    assert block["per_symbol"] == {}
