"""Smooth-pasting free-boundary threshold solver (OU reversion, Cartea Ch 11).

BUILD-SPEC A6. Port target: engineV2 ``backtest/cpu/ou_mle_nb.py:105-297``
(``_hyp1f1`` / ``_C_norm`` / ``_F_plus`` / ``_F_minus`` / ``_F_plus_prime`` /
``_f_exit_long`` / ``_brent`` / ``_brent_with_expansion`` / ``solve_thresholds``).

Every mathematical expression below is transcribed VERBATIM from those lines.
The only declared substitution (BUILD-SPEC A6 directive) is the numerics:
engineV2's pure-Numba series ``_hyp1f1`` and hand-rolled ``_brent`` are replaced
by ``scipy.special.hyp1f1`` and ``scipy.optimize.brentq`` (xtol=1e-8,
maxiter=100). For our regime (z <= ~30) engineV2's series already converges to
double precision, so the two agree to numerical tolerance; the bracket /
expansion / safe-limit logic and the exact ``sigma_eff`` expression are kept
identical so the located root matches.

ODE (Cartea/Jaimungal/Penalva §11.3), κ>0, σ>0, discount ρ>0:
    (σ²/2) F''(ε) + κ(θ − ε) F'(ε) − ρ F(ε) = 0
    a       = ρ / (2κ)
    σ_eff   = σ / √(2κ)
    y       = (ε − θ) / σ_eff
    z       = y² / 2
    C(a)    = √2 · Γ(a + 1/2) / Γ(a)               (= √2·exp(lgamma(a+½)−lgamma(a)))
    F+(ε)   = M(a, 1/2, z) + C(a)·y·M(a + 1/2, 3/2, z)
    F−(ε)   = F+(2θ − ε)
Exit-long solves Eq (11.2): F+(ε)/F+'(ε) = ε − θ − c, root above θ + c.
Reflection (exact for symmetric cost c): entry_long = 2θ − exit_long,
exit_short = entry_long, entry_short = exit_long.
Failed solve → NaN (backtest ``is_fresh`` blocks entries until next good calib).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import brentq
from scipy.special import hyp1f1

_SQRT_2 = math.sqrt(2.0)

# Brent controls — engineV2 ou_mle_nb.py:185 (_brent) / 245-249 (_brent_with_expansion).
_XTOL = 1e-8
_MAXITER = 100
_MAX_EXPANSIONS = 5
_EXPANSION_FACTOR = 2.0


def _c_norm(a: float) -> float:
    """C(a) = √2·Γ(a+½)/Γ(a). engineV2 ou_mle_nb.py:123-127 (``_C_norm``)."""
    return _SQRT_2 * math.exp(math.lgamma(a + 0.5) - math.lgamma(a))


def f_plus(eps: float, kappa: float, theta: float, sigma: float, rho: float) -> float:
    """Exact F+ for the OU+discount ODE. engineV2 ou_mle_nb.py:130-147 (``_F_plus``)."""
    sigma_eff = sigma / math.sqrt(2.0 * kappa)
    if sigma_eff <= 0.0:
        return float("nan")
    y = (eps - theta) / sigma_eff
    z = 0.5 * y * y
    a = rho / (2.0 * kappa)
    even = hyp1f1(a, 0.5, z)
    odd = hyp1f1(a + 0.5, 1.5, z)
    return float(even + _c_norm(a) * y * odd)


def f_minus(eps: float, kappa: float, theta: float, sigma: float, rho: float) -> float:
    """F−(ε) = F+(2θ − ε). engineV2 ou_mle_nb.py:150-153 (``_F_minus``)."""
    return f_plus(2.0 * theta - eps, kappa, theta, sigma, rho)


def _f_plus_prime(eps: float, kappa: float, theta: float, sigma: float, rho: float) -> float:
    """Central-difference F+'. engineV2 ou_mle_nb.py:156-164 (``_F_plus_prime``);
    step h = max(1e-6, 1e-5·σ_eff)."""
    sigma_eff = sigma / math.sqrt(2.0 * kappa) if kappa > 0.0 else 1.0
    h = max(1e-6, 1e-5 * sigma_eff)
    return (
        f_plus(eps + h, kappa, theta, sigma, rho)
        - f_plus(eps - h, kappa, theta, sigma, rho)
    ) / (2.0 * h)


def _f_exit_long(
    eps: float, kappa: float, theta: float, sigma: float, rho: float, c: float
) -> float:
    """Eq (11.2) residual F+(ε)/F+'(ε) − (ε − θ − c). engineV2 ou_mle_nb.py:167-174."""
    fp = f_plus(eps, kappa, theta, sigma, rho)
    fpp = _f_plus_prime(eps, kappa, theta, sigma, rho)
    if abs(fpp) < 1e-18 or not np.isfinite(fp) or not np.isfinite(fpp):
        return float("nan")
    return fp / fpp - (eps - theta - c)


def _brent_with_expansion(
    kappa: float, theta: float, sigma: float, rho: float, c: float,
    a: float, b: float, lo: float, hi: float,
) -> float:
    """Locate exit_long by scipy.brentq once a sign-changing bracket [a,b] is found,
    expanding the bracket up to _MAX_EXPANSIONS times (factor 2, clamped to
    [lo,hi]). engineV2 ou_mle_nb.py:244-261 (``_brent_with_expansion``) — same
    bracket/expansion loop; scipy.brentq replaces the hand-rolled ``_brent``.
    """
    def fn(x: float) -> float:
        return _f_exit_long(x, kappa, theta, sigma, rho, c)

    for _ in range(_MAX_EXPANSIONS + 1):
        fa = fn(a)
        fb = fn(b)
        if np.isfinite(fa) and np.isfinite(fb) and fa * fb < 0.0:
            try:
                return float(brentq(fn, a, b, xtol=_XTOL, maxiter=_MAXITER))
            except (ValueError, RuntimeError):
                return float("nan")
        width = b - a
        new_a = max(lo, a - _EXPANSION_FACTOR * width)
        new_b = min(hi, b + _EXPANSION_FACTOR * width)
        if new_a == a and new_b == b:
            return float("nan")
        a, b = new_a, new_b
    return float("nan")


def solve_thresholds(
    kappa: float, theta: float, sigma: float, rho_discount: float, c: float
) -> tuple[float, float, float, float]:
    """Return (entry_long, exit_long, entry_short, exit_short).

    engineV2 ou_mle_nb.py:264-297 (``solve_thresholds``), verbatim bracket/limits:
        a0 = max(θ + 0.1·σ_eff, θ + c + 1e-12)
        b0 = θ + 3.0·σ_eff
        safe_lo = θ − 10·σ_eff ; safe_hi = θ + 10·σ_eff
    Reflection: entry_long = 2θ − exit_long, exit_short = entry_long,
    entry_short = exit_long. NaN on any failure.
    """
    nan = float("nan")
    if not (kappa > 0.0 and sigma > 0.0 and np.isfinite(theta)):
        return nan, nan, nan, nan
    sigma_eff = sigma / math.sqrt(2.0 * kappa)
    if sigma_eff <= 0.0:
        return nan, nan, nan, nan
    a0 = max(theta + 0.1 * sigma_eff, theta + c + 1e-12)
    b0 = theta + 3.0 * sigma_eff
    safe_lo = theta - 10.0 * sigma_eff
    safe_hi = theta + 10.0 * sigma_eff
    exit_long = _brent_with_expansion(
        kappa, theta, sigma, rho_discount, c, a0, b0, safe_lo, safe_hi
    )
    if not np.isfinite(exit_long):
        return nan, nan, nan, nan
    entry_long = 2.0 * theta - exit_long
    exit_short = entry_long
    entry_short = exit_long
    return entry_long, exit_long, entry_short, exit_short
