"""Black–Scholes gamma + implied-vol inversion for the gamma map.

Practitioner methodology — NOT from Cartea/Jaimungal/Penalva. Gamma and the
implied-vol inversion follow standard Black–Scholes–Merton (Hull, *Options,
Futures, and Other Derivatives*, gamma = ∂²V/∂S²).

Two uses in `flows/gex.py`:
  1. Per-contract dealer gamma, and re-evaluation of gamma across hypothetical
     spot levels for the gamma-flip scan.
  2. Recovering IV for 0DTE contracts whose Alpaca snapshot omits greeks
     (a known gap): solve IV from the option mid, then compute gamma.

All functions broadcast: pass scalars or numpy arrays for any of S, K, tau,
sigma and they broadcast together.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.optimize import brentq
from scipy.special import ndtr  # vectorized standard-normal CDF

# Time-to-expiry floor (years). As tau → 0 (0DTE) d1 and gamma blow up; Alpaca's
# own 0DTE examples floor tau at 1e-6 (~31s) to avoid division errors.
TAU_FLOOR = 1e-6
# Implied-vol search bracket for the inverter.
IV_LO = 1e-4
IV_HI = 5.0

_SQRT_2PI = math.sqrt(2.0 * math.pi)


def _norm_pdf(x: Any) -> Any:
    return np.exp(-0.5 * np.asarray(x, dtype=float) ** 2) / _SQRT_2PI


def d1(S: Any, K: Any, tau: Any, sigma: Any, r: float = 0.0, q: float = 0.0) -> Any:
    tau = np.maximum(tau, TAU_FLOOR)
    sigma = np.asarray(sigma, dtype=float)
    return (np.log(S / K) + (r - q + 0.5 * sigma * sigma) * tau) / (sigma * np.sqrt(tau))


def gamma(S: Any, K: Any, tau: Any, sigma: Any, r: float = 0.0, q: float = 0.0) -> Any:
    """BS gamma (identical for calls and puts): φ(d1)·e^{-qτ} / (S·σ·√τ).

    Non-finite results (σ≤0, degenerate inputs) propagate as nan/inf for the
    caller to mask — they are not silently zeroed here.
    """
    tau = np.maximum(tau, TAU_FLOOR)
    sigma = np.asarray(sigma, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        g = np.exp(-q * tau) * _norm_pdf(d1(S, K, tau, sigma, r, q)) / (S * sigma * np.sqrt(tau))
    return g


def bs_price(
    S: Any, K: Any, tau: Any, sigma: Any,
    r: float = 0.0, q: float = 0.0, is_call: bool = True,
) -> Any:
    """Black–Scholes price. `is_call` is a scalar bool (per-contract use)."""
    tau = np.maximum(tau, TAU_FLOOR)
    sigma = np.asarray(sigma, dtype=float)
    _d1 = d1(S, K, tau, sigma, r, q)
    _d2 = _d1 - sigma * np.sqrt(tau)
    disc_r = np.exp(-r * tau)
    disc_q = np.exp(-q * tau)
    if is_call:
        return S * disc_q * ndtr(_d1) - K * disc_r * ndtr(_d2)
    return K * disc_r * ndtr(-_d2) - S * disc_q * ndtr(-_d1)


def implied_vol(
    price: float, S: float, K: float, tau: float,
    r: float = 0.0, q: float = 0.0, is_call: bool = True,
) -> float:
    """Invert BS price → σ via Brent. Scalar only.

    Returns nan (caller skips + logs) when IV is not recoverable: non-positive
    inputs, price at/under intrinsic (deep ITM / stale), price outside the
    [IV_LO, IV_HI] bracket, or non-convergence. Near-expiry deep OTM/ITM is the
    fragile regime this guards.
    """
    if not (price > 0.0) or not (S > 0.0) or not (K > 0.0):
        return math.nan
    tau = max(float(tau), TAU_FLOOR)
    intrinsic = max(0.0, (S - K) if is_call else (K - S))
    if price <= intrinsic + 1e-8:
        return math.nan

    def f(sig: float) -> float:
        return float(bs_price(S, K, tau, sig, r, q, is_call)) - price

    try:
        if f(IV_LO) * f(IV_HI) > 0.0:
            return math.nan  # not bracketed
        return float(brentq(f, IV_LO, IV_HI, maxiter=100, xtol=1e-6))
    except (ValueError, RuntimeError):
        return math.nan
