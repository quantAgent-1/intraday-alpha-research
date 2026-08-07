"""Tests for models/sizing.py — the M9 Cell B calibrated sizing overlay.

Synthetic frames + hand literals only (no disk, no network). Covers the registered
Cell-B guarantees: isotonic calibration is fit train / apply test with NO LEAKAGE
(a fold's calibrator never sees its own rows; the earliest fold falls back to
identity), the sizing weight is normalized per book (mean 1) and clipped at the cap,
and the three-stream report + calibration curve are well-formed. Sizing is a
deploy-lens view only — these tests assert its mechanics, not a promotion verdict.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from enginev51.models.sizing import (
    CAP,
    calibrated_sizing,
    calibration_curve,
    isotonic_calibrate_oos,
    sizing_weights,
)

UNIVERSE = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")


def _oh(sym: str) -> dict:
    return {f"oh_{s}": (1.0 if s == sym else 0.0) for s in UNIVERSE}


def _row(session, symbol, *, basis, net, p_win, fold, y=None):
    y = int(net > 0.0) if y is None else y
    r = {
        "session": session, "symbol": symbol, "basis_bps": basis, "net_bps": net,
        "p_win": p_win, "y_meta": y, "fold": fold,
    }
    r.update(_oh(symbol))
    return r


def _synthetic_oos(n_folds: int = 4, per_fold: int = 120, seed: int = 5) -> pl.DataFrame:
    """A folded OOS frame where a higher p_win genuinely predicts more winners, so
    isotonic has something monotone to learn."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for k in range(n_folds):
        fold = f"20{22 + k}-01-02"
        for i in range(per_fold):
            p = float(rng.uniform(0.4, 0.72))
            win = rng.random() < p  # calibrated-ish latent
            net = (abs(rng.normal(6, 15)) if win else -abs(rng.normal(6, 15)))
            basis = float(rng.choice([-1, 1]) * rng.uniform(10, 400))
            sym = UNIVERSE[i % len(UNIVERSE)]
            # session within the fold's half-year (unique-ish day per row)
            sess = f"20{22 + k}-{1 + (i % 6):02d}-{1 + (i % 27):02d}"
            rows.append(_row(sess, sym, basis=basis, net=net, p_win=p, fold=fold,
                             y=int(win)))
    return pl.DataFrame(rows, orient="row")


# --------------------------------------------------------------------------- calibration no-leakage


def test_isotonic_no_leakage_fit_train_apply_test():
    oos = _synthetic_oos()
    cal = isotonic_calibrate_oos(oos)
    folds = sorted(oos["fold"].unique().to_list())

    # earliest fold has no prior data -> identity (p_win_cal == p_win, cal_fitted False)
    first = cal.filter(pl.col("fold") == folds[0])
    assert not first["cal_fitted"].any()
    assert np.allclose(first["p_win_cal"].to_numpy(), first["p_win"].to_numpy())

    # every later fold IS fitted, and its calibrated values are reproducible when we
    # refit isotonic on ONLY the strictly-earlier folds (proves no own-fold leakage).
    from sklearn.isotonic import IsotonicRegression
    for k in range(1, len(folds)):
        te = cal.filter(pl.col("fold") == folds[k])
        assert te["cal_fitted"].all()
        prior = oos.filter(pl.col("fold").is_in(folds[:k]))
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(prior["p_win"].to_numpy().astype(float),
                prior["y_meta"].to_numpy().astype(float))
        expect = np.clip(iso.predict(te["p_win"].to_numpy().astype(float)), 0.0, 1.0)
        assert np.allclose(te["p_win_cal"].to_numpy(), expect)

    # calibrated probabilities stay in [0,1]; row count + order preserved
    assert cal.height == oos.height
    pc = cal["p_win_cal"].to_numpy()
    assert np.all((pc >= 0.0) & (pc <= 1.0))


def test_isotonic_calibration_reduces_error_on_miscalibrated_input():
    """If raw p_win is systematically off (compressed toward 0.5) but ranks winners,
    isotonic pulls it toward the realized rate — mean abs error drops."""
    oos = _synthetic_oos(n_folds=5, per_fold=200, seed=9)
    # compress raw probabilities toward 0.5 (miscalibrate while keeping the ranking)
    oos = oos.with_columns((0.5 + (pl.col("p_win") - 0.5) * 0.3).alias("p_win"))
    cal = isotonic_calibrate_oos(oos)
    curve = calibration_curve(cal)
    # over the fitted rows the calibrated map is at least as close on average
    assert float(curve["abs_err_cal"].mean()) <= float(curve["abs_err_raw"].mean()) + 1e-9


# --------------------------------------------------------------------------- weights


def test_weight_normalization_mean_one():
    oos = _synthetic_oos()
    cal = isotonic_calibrate_oos(oos)
    w, raw = sizing_weights(cal)
    # normalized per book: mean weight is exactly 1 (fixed total notional)
    assert w.mean() == np.float64(w.mean())
    assert abs(float(w.mean()) - 1.0) < 1e-12
    assert w.shape[0] == cal.height
    assert np.all(w >= 0.0)


def test_weight_cap_clip():
    # two events: a modest basis and a huge basis; the huge one clips at the cap.
    rows = [
        _row("2023-01-03", "NVDA", basis=50.0, net=5.0, p_win=0.6, fold="2023-01-02"),
        _row("2023-01-04", "TSLA", basis=5000.0, net=5.0, p_win=0.9, fold="2023-01-02"),
    ]
    df = pl.DataFrame(rows, orient="row").with_columns(
        pl.col("p_win").alias("p_win_cal")
    )
    _w, raw = sizing_weights(df, cap=CAP)
    # raw = clip(p_win_cal*|basis|, 0, cap): 0.6*50=30 (uncapped), 0.9*5000=4500 -> capped
    assert raw[0] == 30.0
    assert raw[1] == CAP
    assert raw.max() <= CAP + 1e-12


def test_weight_zero_fallback_equal():
    # all |basis| = 0 -> raw weights all 0 -> equal-weight fallback (mean 1)
    rows = [
        _row("2023-01-03", "NVDA", basis=0.0, net=5.0, p_win=0.6, fold="2023-01-02"),
        _row("2023-01-04", "TSLA", basis=0.0, net=-2.0, p_win=0.4, fold="2023-01-02"),
    ]
    df = pl.DataFrame(rows, orient="row").with_columns(pl.col("p_win").alias("p_win_cal"))
    w, _raw = sizing_weights(df)
    assert np.allclose(w, 1.0)


# --------------------------------------------------------------------------- report


def test_calibrated_sizing_streams_and_report():
    oos = _synthetic_oos(n_folds=4, per_fold=150, seed=1)
    res = calibrated_sizing(oos)
    table = res["table"]
    assert set(table["stream"].to_list()) == {
        "flat_all", "flat_gated_P>=0.55", "calibrated_sized"
    }
    # flat_all and calibrated_sized cover the SAME OOS events; the gate is a subset
    n_all = table.filter(pl.col("stream") == "flat_all")["n"][0]
    n_sized = table.filter(pl.col("stream") == "calibrated_sized")["n"][0]
    n_gated = table.filter(pl.col("stream") == "flat_gated_P>=0.55")["n"][0]
    assert n_all == n_sized == oos.height
    assert n_gated <= n_all

    # flat_all net-per-notional == plain mean net_bps (weights are 1)
    flat_mean = float(oos["net_bps"].mean())
    got = table.filter(pl.col("stream") == "flat_all")["net_per_notional_bps"][0]
    assert abs(got - round(flat_mean, 3)) < 1e-6

    # summary carries the deploy-lens comparison scalars
    s = res["summary"]
    for key in (
        "sharpe_flat_all", "sharpe_flat_gated", "sharpe_calibrated_sized",
        "net_per_unit_calibrated_sized", "sized_beats_flat_gated_sharpe",
        "calibration_mae_raw", "calibration_mae_cal",
    ):
        assert key in s
    assert isinstance(s["sized_beats_flat_gated_sharpe"], bool)

    # calibration curve: 10 equal-count bins with both error columns present
    curve = res["calibration_curve"]
    assert curve.height == 10
    assert set(curve.columns) >= {"raw_mean", "cal_mean", "realized_win_rate",
                                  "abs_err_raw", "abs_err_cal"}


def test_calibrated_sizing_deterministic():
    oos = _synthetic_oos(seed=3)
    a = calibrated_sizing(oos)["table"]
    b = calibrated_sizing(oos)["table"]
    assert a.equals(b)


def test_empty_oos_is_safe():
    schema = {
        "session": pl.Utf8, "symbol": pl.Utf8, "basis_bps": pl.Float64,
        "net_bps": pl.Float64, "p_win": pl.Float64, "y_meta": pl.Int8, "fold": pl.Utf8,
    }
    empty = pl.DataFrame(schema=schema)
    cal = isotonic_calibrate_oos(empty)
    assert cal.height == 0
    assert "p_win_cal" in cal.columns
    curve = calibration_curve(cal)
    assert curve.height == 0
