"""M18 §6.1 — OU MLE hand-computed fixtures + degeneracy guards.

The expected alpha/kappa/theta/sigma are recomputed independently in the test
from the closed-form estimator (engineV2 ou_mle_nb.mle_ou), never read back from
the implementation, then asserted equal.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from enginev51.reversion.ou import OUCalibrator, mle_ou


def _reference_mle(s: np.ndarray, dt: float) -> tuple[float, float, float, float]:
    """Independent closed-form reference (the 'hand computation')."""
    n = s.size
    mu = s.mean()
    a = s[:-1] - mu
    b = s[1:] - mu
    denom = float((a * a).sum())
    num = float((a * b).sum())
    alpha = num / denom
    kappa = -math.log(alpha) / dt
    d = b - alpha * a
    sigma2 = 2.0 * kappa / max(1.0 - alpha * alpha, 1e-18) * float((d * d).sum()) / (n - 1)
    return alpha, kappa, mu, math.sqrt(sigma2)


def test_mle_ou_ten_sample_fixture_exact():
    # A gently decaying 10-sample series → positive AR(1) autocorrelation, 0<α<1.
    s = np.array([1.00, 0.62, 0.40, 0.27, 0.18, 0.13, 0.09, 0.06, 0.045, 0.03])
    dt = 1.0
    alpha_e, kappa_e, theta_e, sigma_e = _reference_mle(s, dt)
    fit = mle_ou(s, dt)
    assert fit.valid
    assert fit.alpha == pytest.approx(alpha_e, rel=1e-12)
    assert fit.kappa == pytest.approx(kappa_e, rel=1e-12)
    assert fit.theta == pytest.approx(theta_e, rel=1e-12)
    assert fit.sigma == pytest.approx(sigma_e, rel=1e-12)
    # theta is exactly the sample mean; kappa = -ln(alpha).
    assert fit.theta == pytest.approx(float(s.mean()), rel=1e-12)
    assert math.exp(-fit.kappa * dt) == pytest.approx(fit.alpha, rel=1e-12)


def test_mle_ou_second_fixture_exact():
    s = np.array([-0.5, -0.2, -0.05, 0.0, 0.03, 0.05, 0.04, 0.02, 0.0, -0.01])
    alpha_e, kappa_e, theta_e, sigma_e = _reference_mle(s, 1.0)
    fit = mle_ou(s, 1.0)
    assert fit.valid
    assert (fit.alpha, fit.kappa, fit.theta, fit.sigma) == pytest.approx(
        (alpha_e, kappa_e, theta_e, sigma_e), rel=1e-11
    )


def test_mle_ou_degenerate_returns_invalid():
    # Constant series → denom 0 → invalid.
    assert not mle_ou(np.ones(10), 1.0).valid
    # Anti-correlated (alpha<0) → invalid (kappa would be complex).
    s = np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0])
    assert not mle_ou(s, 1.0).valid
    # dt<=0 and n<2 → invalid.
    assert not mle_ou(np.array([1.0, 2.0, 3.0]), 0.0).valid
    assert not mle_ou(np.array([1.0]), 1.0).valid


def test_calibrator_attempt_gate_and_reset():
    # < OU_MIN_SAMPLES (300) → no thresholds even if MLE would be valid.
    cal = OUCalibrator()
    rng = np.random.default_rng(0)
    ts = 0
    for _ in range(250):
        ts += 1_000_000_000
        cal.sample(ts, 100.0 + rng.normal(0, 0.02), 100.0)
    assert cal.n_samples == 250
    assert not cal.is_warm
    assert cal.maybe_calibrate(ts) is None  # n<300 → unchanged (None)
    # Feed past 300 → warm; a calibration may now populate thresholds.
    for _ in range(120):
        ts += 1_000_000_000
        cal.sample(ts, 100.0 + rng.normal(0, 0.02), 100.0)
    assert cal.is_warm
    cal.reset()
    assert cal.n_samples == 0
    assert cal.thresholds is None
    assert math.isnan(cal.latest_eps)
