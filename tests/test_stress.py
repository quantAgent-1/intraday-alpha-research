"""Tests for enginev51.backtest.stress.

Every expectation below is computed independently in this file (via scipy/numpy
primitives or plain arithmetic in comments) -- none of it is a mirror of the
module's own output.
"""

from __future__ import annotations

import math

import numpy as np
import polars as pl
import pytest
from scipy import stats

from enginev51.backtest.stress import (
    clustered_mean_ci,
    concentration_report,
    double_latency,
    double_spread,
    drop_top_sessions,
    min_n_for_power,
    post_promo,
    power_of_test,
    power_table,
    stress_report,
)

SCHEMA_COLS = [
    "session",
    "symbol",
    "payer",
    "net_bps",
    "gross_mid_bps",
    "latency_drag_bps",
    "spread_cost_bps",
    "fees_bps",
    "exit_reason",
    "taken",
]


def _row(
    session,
    net,
    spread,
    latency,
    symbol="AAA",
    payer="p1",
    taken=True,
    fees=1.0,
    exit_reason="target",
):
    return {
        "session": session,
        "symbol": symbol,
        "payer": payer,
        "net_bps": float(net),
        "gross_mid_bps": float(net) + float(spread) + float(latency) + float(fees),
        "latency_drag_bps": float(latency),
        "spread_cost_bps": float(spread),
        "fees_bps": float(fees),
        "exit_reason": exit_reason,
        "taken": taken,
    }


# --------------------------------------------------------------------------- #
# 1. Power: monotonicity + independent scipy anchor
# --------------------------------------------------------------------------- #


def test_power_of_test_monotone_in_n():
    # Fixed true edge, fixed dispersion: more plans -> strictly more power to
    # detect the same effect (t-test power is monotone increasing in N).
    mean, sigma = 10.0, 130.0
    ns = [100, 150, 250, 400, 600, 1000]
    powers = [power_of_test(mean, sigma, n) for n in ns]
    for a, b in zip(powers, powers[1:], strict=False):
        assert b > a


def test_power_of_test_monotone_in_mean():
    # Fixed N, fixed dispersion: a bigger true edge is easier to detect.
    sigma, n = 130.0, 250
    means = [5.0, 8.0, 10.0, 13.0, 15.0, 20.0]
    powers = [power_of_test(m, sigma, n) for m in means]
    for a, b in zip(powers, powers[1:], strict=False):
        assert b > a


def test_power_table_matches_power_of_test_and_is_monotone():
    tbl = power_table()
    for row in tbl.iter_rows(named=True):
        expect = power_of_test(row["mean_bps"], row["sigma_bps"], row["n"], row["alpha"])
        assert row["power"] == pytest.approx(expect, abs=1e-12)
    # within each mean, power must rise as n rises (grid is built n-ascending
    # per mean already, so simple adjacent-row comparison works within a group)
    for _mean_bps, grp in tbl.group_by("mean_bps"):
        vals = grp.sort("n")["power"].to_list()
        for a, b in zip(vals, vals[1:], strict=False):
            assert b > a


def test_power_of_test_anchor_mean13_sigma130_n250():
    # Independent scipy computation of the exact non-central-t power for
    # mean=13, sigma=130, N=250, alpha=0.05 (one-sided), matching the module's
    # own documented formula (not calling into the module):
    #   d   = mean / sigma           = 13 / 130            = 0.1
    #   ncp = d * sqrt(N)            = 0.1 * sqrt(250)      = 0.1 * 15.811388... = 1.5811388...
    #   df  = N - 1                                        = 249
    #   t_crit = t.ppf(0.95, df=249)                        (~1.6510)
    #   power  = P(T' > t_crit) for noncentral-t(df=249, ncp=1.5811388...)
    mean_bps, sigma_bps, n, alpha = 13.0, 130.0, 250, 0.05
    d = mean_bps / sigma_bps
    assert d == pytest.approx(0.1)
    ncp = d * math.sqrt(n)
    assert ncp == pytest.approx(1.5811388300841898)
    df = n - 1
    t_crit = float(stats.t.ppf(1.0 - alpha, df))
    expected = float(stats.nct.sf(t_crit, df, ncp))

    got = power_of_test(mean_bps, sigma_bps, n, alpha)
    assert got == pytest.approx(expected, abs=1e-6)

    # Sanity cross-check against the classic normal approximation
    #   power ~= 1 - Phi(z_alpha - mean/(sigma/sqrt(N)))
    # z_alpha = Phi^-1(0.95) = 1.644854...
    # mean/(sigma/sqrt(N)) = 13 / (130/sqrt(250)) = 13 / 8.2219... = 1.581139...
    # power ~= 1 - Phi(1.644854 - 1.581139) = 1 - Phi(0.063715) ~= 1 - 0.52540 = 0.47460
    z_a = float(stats.norm.ppf(1.0 - alpha))
    se = sigma_bps / math.sqrt(n)
    normal_approx = 1.0 - float(stats.norm.cdf(z_a - mean_bps / se))
    assert normal_approx == pytest.approx(0.47460, abs=1e-4)
    # The exact non-central-t value and the normal approximation should be
    # close (df=249 is large) but need not match to high precision -- they are
    # two different (both textbook-standard) approximations of the same power.
    assert got == pytest.approx(normal_approx, abs=5e-3)

    # Falls in the expected mid-power band for this regime.
    assert 0.45 <= got <= 0.75


# --------------------------------------------------------------------------- #
# 2. min_n_for_power: inverse consistency
# --------------------------------------------------------------------------- #


def test_min_n_for_power_inverse_consistency():
    mean_bps, sigma_bps, target = 10.0, 130.0, 0.8
    n = min_n_for_power(mean_bps, sigma_bps, target)
    assert n is not None
    # Module's own documented contract: power_of_test(n) >= target and
    # power_of_test(n-1) < target (the "smallest N that reaches target" rounding
    # convention -- verified directly, not assumed).
    assert power_of_test(mean_bps, sigma_bps, n) >= target
    assert power_of_test(mean_bps, sigma_bps, n - 1) < target


def test_min_n_for_power_nonpositive_mean_returns_none():
    # mean_bps <= 0 can never reach power > alpha as N grows -> None by contract.
    assert min_n_for_power(-5.0, 130.0, 0.8) is None
    assert min_n_for_power(0.0, 130.0, 0.8) is None


# --------------------------------------------------------------------------- #
# 3. clustered_mean_ci: wider than naive iid bootstrap + determinism
# --------------------------------------------------------------------------- #


def _naive_iid_bootstrap_ci(values, n_boot, seed, ci):
    """Same methodology as clustered_mean_ci but resampling raw VALUES (not
    clusters) with replacement -- the textbook iid bootstrap that ignores the
    within-cluster correlation structure."""
    values = np.asarray(values, dtype=float)
    n = values.shape[0]
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for b in range(n_boot):
        draw = rng.integers(0, n, n)
        means[b] = values[draw].mean()
    alpha = (1.0 - ci) / 2.0
    return (
        float(values.mean()),
        float(np.quantile(means, alpha)),
        float(np.quantile(means, 1.0 - alpha)),
    )


def test_clustered_ci_wider_than_naive_iid_when_perfectly_clustered():
    # 10 clusters x 20 identical-within-cluster values, cluster means spread
    # 0, 100, 200, ..., 900. Every value in cluster i equals 100*i, so within-
    # cluster variance is exactly 0 -- all sampling variability comes from
    # WHICH clusters get drawn, not which values within them. The clustered
    # bootstrap should therefore have a much wider CI than an iid bootstrap
    # over the 200 flattened values (which sees fake extra "independence").
    n_clusters, per_cluster = 10, 20
    cluster_ids = np.repeat(np.arange(n_clusters), per_cluster)
    values = np.repeat(np.arange(n_clusters) * 100.0, per_cluster)
    # overall mean = 100 * mean(0..9) = 100 * 4.5 = 450.0
    assert values.mean() == pytest.approx(450.0)

    n_boot, seed, ci = 2000, 123, 0.95
    c_mean, c_lo, c_hi = clustered_mean_ci(values, cluster_ids, n_boot=n_boot, seed=seed, ci=ci)
    i_mean, i_lo, i_hi = _naive_iid_bootstrap_ci(values, n_boot=n_boot, seed=seed, ci=ci)

    assert c_mean == pytest.approx(450.0)
    assert i_mean == pytest.approx(450.0)
    assert (c_hi - c_lo) > (i_hi - i_lo)
    # The iid bootstrap effectively has ~200 "independent" draws and should be
    # noticeably tighter; clustered has only 10 independent draws.
    assert (c_hi - c_lo) > 2.0 * (i_hi - i_lo)


def test_clustered_ci_deterministic_in_seed():
    n_clusters, per_cluster = 10, 20
    cluster_ids = np.repeat(np.arange(n_clusters), per_cluster)
    values = np.repeat(np.arange(n_clusters) * 100.0, per_cluster)
    a = clustered_mean_ci(values, cluster_ids, n_boot=500, seed=42, ci=0.95)
    b = clustered_mean_ci(values, cluster_ids, n_boot=500, seed=42, ci=0.95)
    assert a == b


# --------------------------------------------------------------------------- #
# 4. Stress transforms on a tiny hand frame
# --------------------------------------------------------------------------- #


@pytest.fixture
def hand_frame():
    # 6 plans, 3 sessions (2 plans each). Session net sums:
    #   S1: 100 + 50 = 150   (biggest -> dropped by drop_top_sessions(k=1))
    #   S2: 30 + 20  = 50
    #   S3: 10 + 5   = 15
    rows = [
        _row("S1", 100, spread=5, latency=3),
        _row("S1", 50, spread=2, latency=1),
        _row("S2", 30, spread=4, latency=2, symbol="BBB", payer="p2"),
        _row("S2", 20, spread=1, latency=1, symbol="BBB", payer="p2"),
        _row("S3", 10, spread=3, latency=1, symbol="CCC", payer="p3"),
        _row("S3", 5, spread=1, latency=0.5, symbol="CCC", payer="p3"),
    ]
    return pl.DataFrame(rows, schema={c: pl.DataFrame(rows).schema[c] for c in SCHEMA_COLS})


def test_drop_top_sessions_removes_best_session_only(hand_frame):
    out = drop_top_sessions(hand_frame, k=1)
    # S1 (sum=150) is strictly the largest -> every S1 row gone, S2/S3 remain.
    assert set(out["session"].unique().to_list()) == {"S2", "S3"}
    assert out.height == 4
    assert out.filter(pl.col("session") == "S1").height == 0


def test_double_spread_subtracts_spread_once_more(hand_frame):
    out = double_spread(hand_frame)
    # Row 0: original net_bps=100, spread_cost_bps=5 -> new net_bps = 100 - 5 = 95
    row0 = out.row(0, named=True)
    assert row0["net_bps"] == pytest.approx(95.0)
    # Row 2 (S2 first plan): net=30, spread=4 -> 30 - 4 = 26
    row2 = out.row(2, named=True)
    assert row2["net_bps"] == pytest.approx(26.0)
    # Untouched columns are unaffected.
    assert row0["spread_cost_bps"] == pytest.approx(5.0)


def test_double_latency_subtracts_latency_once_more(hand_frame):
    out = double_latency(hand_frame)
    # Row 0: net=100, latency_drag_bps=3 -> new net_bps = 100 - 3 = 97
    row0 = out.row(0, named=True)
    assert row0["net_bps"] == pytest.approx(97.0)
    # Row 5 (S3 second plan): net=5, latency=0.5 -> 5 - 0.5 = 4.5
    row5 = out.row(5, named=True)
    assert row5["net_bps"] == pytest.approx(4.5)


def test_double_spread_maker_earn_does_not_improve():
    # F1 regression (code review 2026-07-17): spread_cost_bps is SIGNED and a
    # maker book carries NEGATIVE values (earn vs mid). The old signed
    # subtraction turned net = 4, spread = -5 into 4 - (-5) = 9 — a stress arm
    # that IMPROVED the book. The arm must never raise net above base.
    rows = [
        _row("S1", 4.0, spread=-5.0, latency=1.0),
        _row("S2", 2.0, spread=-1.0, latency=0.5),
    ]
    df = pl.DataFrame(rows, schema={c: pl.DataFrame(rows).schema[c] for c in SCHEMA_COLS})
    out = double_spread(df)
    for base_row, out_row in zip(df.iter_rows(named=True), out.iter_rows(named=True), strict=True):
        assert out_row["net_bps"] <= base_row["net_bps"]
    # maker earn is left untouched (frame arithmetic cannot re-price a maker
    # fill on a wider book — that is widen_tape's job), not doubled.
    assert out.row(0, named=True)["net_bps"] == pytest.approx(4.0)


def test_double_spread_mixed_signs_stresses_only_paid_spread():
    # taker row (spread=+3) pays one more spread; maker row (spread=-5) is a
    # no-op — never a credit.
    rows = [
        _row("S1", 10.0, spread=3.0, latency=1.0),
        _row("S1", 4.0, spread=-5.0, latency=1.0),
    ]
    df = pl.DataFrame(rows, schema={c: pl.DataFrame(rows).schema[c] for c in SCHEMA_COLS})
    out = double_spread(df)
    assert out.row(0, named=True)["net_bps"] == pytest.approx(7.0)  # 10 - 3
    assert out.row(1, named=True)["net_bps"] == pytest.approx(4.0)  # unchanged


def test_double_latency_favorable_drift_does_not_improve():
    # Same F1 failure mode on the latency arm: a favorable drift (negative
    # drag) must not be doubled into extra profit. net = 4, drag = -0.4 stays 4.
    rows = [
        _row("S1", 4.0, spread=1.0, latency=-0.4),
        _row("S2", 6.0, spread=1.0, latency=2.0),
    ]
    df = pl.DataFrame(rows, schema={c: pl.DataFrame(rows).schema[c] for c in SCHEMA_COLS})
    out = double_latency(df)
    assert out.row(0, named=True)["net_bps"] == pytest.approx(4.0)  # unchanged
    assert out.row(1, named=True)["net_bps"] == pytest.approx(4.0)  # 6 - 2


def test_post_promo_subtracts_14bps(hand_frame):
    out = post_promo(hand_frame)
    # Row 0: net=100 -> 100 - 14 = 86
    row0 = out.row(0, named=True)
    assert row0["net_bps"] == pytest.approx(86.0)
    # Row 4 (S3 first plan): net=10 -> 10 - 14 = -4
    row4 = out.row(4, named=True)
    assert row4["net_bps"] == pytest.approx(-4.0)

    # Custom extra_bps is honored too: net=100 -> 100 - 7 = 93
    out2 = post_promo(hand_frame, extra_bps=7.0)
    assert out2.row(0, named=True)["net_bps"] == pytest.approx(93.0)


# --------------------------------------------------------------------------- #
# 5. concentration_report
# --------------------------------------------------------------------------- #


def test_concentration_report_dominant_session():
    # 6 sessions, one carries 900 of a 1000 total net; the other 5 share 100
    # evenly (20 each).
    #   total = 900 + 5*20 = 1000
    #   top5_session_share: top-5 of 6 sessions by summed net = {900,20,20,20,20}
    #       (drops the smallest 20) -> share = (900+20*4)/1000 = 980/1000 = 0.98
    #   effective_n = (sum w)^2 / sum(w^2)
    #       sum w = 1000, sum w^2 = 900^2 + 5*20^2 = 810000 + 2000 = 812000
    #       effective_n = 1000^2 / 812000 = 1000000/812000 = 1.231527...
    rows = [_row("DOM", 900, spread=0, latency=0, symbol="X", payer="pX")]
    for i in range(5):
        rows.append(_row(f"S{i}", 20, spread=0, latency=0, symbol=f"Y{i}", payer=f"p{i}"))
    df = pl.DataFrame(rows, schema={c: pl.DataFrame(rows).schema[c] for c in SCHEMA_COLS})

    rep = concentration_report(df)
    assert rep["n_sessions"] == 6
    assert rep["total_net_bps"] == pytest.approx(1000.0)
    assert rep["top5_session_share"] == pytest.approx(0.98)
    assert rep["top5_session_share"] >= 0.9
    assert rep["effective_n"] == pytest.approx(1000000 / 812000)
    assert rep["effective_n"] < 2.0


def test_concentration_report_uniform_sessions():
    # 10 sessions, each with identical summed net (100 bps) -> perfectly
    # spread book: effective_n should equal n_sessions exactly.
    #   sum w = 1000, sum w^2 = 10 * 100^2 = 100000
    #   effective_n = 1000^2 / 100000 = 1000000/100000 = 10.0
    rows = [_row(f"S{i}", 100, spread=0, latency=0, symbol=f"Z{i}", payer=f"q{i}") for i in range(10)]
    df = pl.DataFrame(rows, schema={c: pl.DataFrame(rows).schema[c] for c in SCHEMA_COLS})

    rep = concentration_report(df)
    assert rep["n_sessions"] == 10
    assert rep["effective_n"] == pytest.approx(10.0)


def test_concentration_report_empty_taken_stream():
    rows = [_row("S1", 10, spread=0, latency=0, taken=False)]
    df = pl.DataFrame(rows, schema={c: pl.DataFrame(rows).schema[c] for c in SCHEMA_COLS})
    rep = concentration_report(df)
    assert rep["n_plans"] == 0
    assert rep["n_sessions"] == 0
    assert math.isnan(rep["effective_n"])


# --------------------------------------------------------------------------- #
# 6. stress_report: keys + taken filtering
# --------------------------------------------------------------------------- #


def test_stress_report_keys_and_shapes(hand_frame):
    rep = stress_report(hand_frame, n_boot=200, seed=1)
    expected_keys = {"base", "drop_top5", "double_spread", "double_latency", "post_promo", "concentration"}
    assert set(rep.keys()) == expected_keys

    for name in ("base", "drop_top5", "double_spread", "double_latency", "post_promo"):
        arm = rep[name]
        assert isinstance(arm, tuple)
        assert len(arm) == 5
        mean, lo, hi, n_plans, n_sessions = arm
        assert isinstance(n_plans, int)
        assert isinstance(n_sessions, int)

    assert isinstance(rep["concentration"], dict)
    # base arm covers all 6 hand-frame plans across 3 sessions.
    assert rep["base"][3] == 6
    assert rep["base"][4] == 3


def test_stress_report_excludes_not_taken_rows(hand_frame):
    # Add a not-taken plan with an extreme value that would badly distort the
    # mean/CI/n_plans if it leaked into any arm.
    extra = _row("S1", -999999.0, spread=0, latency=0, taken=False, symbol="ZZZ", payer="pZ")
    df = hand_frame.vstack(pl.DataFrame([extra], schema=hand_frame.schema))

    rep_with_extra = stress_report(df, n_boot=200, seed=1)
    rep_baseline = stress_report(hand_frame, n_boot=200, seed=1)

    # n_plans/n_sessions and the point estimate (mean) must be identical to the
    # baseline (without the not-taken row) for every CI arm, since the extra
    # row is never taken. Note: drop_top5 removes ALL 3 sessions here (k=5 >=
    # n_sessions=3, per the module's documented "<=k sessions -> everything
    # removed" rule), so that arm's mean is nan in both baseline and
    # with-extra runs -- compare with equal_nan semantics.
    for name in ("base", "drop_top5", "double_spread", "double_latency", "post_promo"):
        assert rep_with_extra[name][3] == rep_baseline[name][3]
        assert rep_with_extra[name][4] == rep_baseline[name][4]
        got, base = rep_with_extra[name][0], rep_baseline[name][0]
        if math.isnan(base):
            assert math.isnan(got)
        else:
            assert got == pytest.approx(base)

    # Sanity: base n_plans is still 6, not 7.
    assert rep_with_extra["base"][3] == 6
