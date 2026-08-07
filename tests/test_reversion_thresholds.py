"""M18 §6.2 — smooth-pasting solver: reflection identity + F± properties.

The reflection entry_long + exit_long = 2θ is EXACT for the symmetric OU process
(engineV2 ou_mle_nb docstring), so it must hold across random valid params.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from enginev51.reversion.thresholds import f_minus, f_plus, solve_thresholds

RHO = 0.01
C = 0.0008


def test_reflection_identity_random_valid_params():
    rng = np.random.default_rng(7)
    n_ok = 0
    for _ in range(200):
        kappa = rng.uniform(0.001, 0.2)
        theta = rng.uniform(-2.0, 2.0)
        sigma = rng.uniform(0.01, 1.0)
        el, xl, es, xs = solve_thresholds(kappa, theta, sigma, RHO, C)
        if not math.isfinite(xl):
            continue
        n_ok += 1
        # reflection: entry_long + exit_long = 2θ (exact).
        assert (el + xl) == pytest.approx(2.0 * theta, abs=1e-6)
        # exit_short = entry_long, entry_short = exit_long.
        assert es == pytest.approx(xl, abs=1e-12)
        assert xs == pytest.approx(el, abs=1e-12)
        # exit_long lies strictly above θ + c (the cited bracket start).
        assert xl > theta + C
    assert n_ok > 150  # the solver succeeds on the vast majority of valid params


def test_f_minus_is_reflection_of_f_plus():
    kappa, theta, sigma = 0.03, 0.1, 0.2
    for eps in (-0.5, -0.1, 0.0, 0.1, 0.3):
        # F−(ε) = F+(2θ − ε), exact.
        assert f_minus(eps, kappa, theta, sigma, RHO) == pytest.approx(
            f_plus(2.0 * theta - eps, kappa, theta, sigma, RHO), rel=1e-12
        )


def test_f_plus_at_theta_is_one_and_increasing():
    kappa, theta, sigma = 0.05, -0.2, 0.3
    # y=0 at ε=θ → M(a,½,0)=1 and the odd term vanishes → F+ = 1.
    assert f_plus(theta, kappa, theta, sigma, RHO) == pytest.approx(1.0, rel=1e-12)
    # strictly increasing on R for ρ>0, κ>0, σ>0.
    xs = [theta + d for d in (-0.4, -0.2, 0.0, 0.2, 0.4)]
    vals = [f_plus(x, kappa, theta, sigma, RHO) for x in xs]
    assert all(b > a for a, b in zip(vals[:-1], vals[1:], strict=True))


def test_failed_solve_returns_nan():
    # Non-positive kappa / sigma → all-NaN (entries blocked upstream).
    for bad in [(-0.1, 0.0, 0.2), (0.05, 0.0, 0.0), (0.0, 0.0, 0.2)]:
        out = solve_thresholds(*bad, RHO, C)
        assert all(math.isnan(x) for x in out)
