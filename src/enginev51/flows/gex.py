"""Dealer gamma-exposure (GEX) map: pin, walls, gamma-flip, regime.

Practitioner methodology — NOT in Cartea/Jaimungal/Penalva. The dealer
long-call / short-put gamma convention popularized by SqueezeMetrics (2017 GEX
white paper) and SpotGamma. Black–Scholes gamma from `flows/bs.py`.

Pure numpy over per-contract arrays — no I/O. Dealer dollar-gamma per contract,
in $ per 1% move of the underlying:

    GEX_i = sign_i · γ_i · OI_i · multiplier · S² · 0.01     (sign = +1 call, −1 put)

Aggregates:
  * net GEX(S)  = Σ GEX_i ; regime = sign(net GEX) (+1 long/stabilizing, −1 short/amplifying)
  * gamma-flip  = hypothetical spot where Σ GEX = 0 (BS gamma re-evaluated per contract)
  * call wall   = strike ≥ spot of max call-gamma notional (resistance)
  * put wall    = strike ≤ spot of max put-gamma notional (support)
  * pin         = strike of max total gamma concentration near spot (magnet)

Caveats baked into the inputs, not hidden: dealer sign is an ASSUMPTION (not
data); OI is prior-day EOD; the flip scan holds each contract's IV fixed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

# v5.1: import rewritten from `from engine.gamma import blackscholes as bs`.
from enginev51.flows import bs


@dataclass(frozen=True, slots=True)
class GammaMap:
    symbol: str
    ts: int                          # ns epoch
    spot: float
    net_gex: float                   # $ per 1% move, summed (dealer convention)
    regime: int                      # +1 long gamma (stabilizing), −1 short (amplifying)
    gamma_flip: float                # zero-gamma spot; nan if no crossing in scan band
    call_wall: float                 # nan if no calls ≥ spot
    put_wall: float                  # nan if no puts ≤ spot
    pin: float                       # nan if no strikes near spot
    per_strike: dict[float, float]   # strike -> net GEX ($/1% move)


def _per_contract_dollar_gamma(
    spot: float, K: Any, tau: Any, sigma: Any, oi: Any, mult: Any, r: float,
) -> Any:
    """Unsigned $-gamma magnitude per contract at `spot`. Non-finite → 0."""
    g = bs.gamma(spot, K, tau, sigma, r)
    notional = g * oi * mult * (spot * spot) * 0.01
    return np.where(np.isfinite(notional), notional, 0.0)


def _zero_cross(grid: np.ndarray, curve: np.ndarray, spot: float) -> float:
    """Linear-interpolated zero crossing of `curve` over `grid`, nearest `spot`.

    Returns nan if the curve never changes sign over the grid.
    """
    s = np.sign(curve)
    idx = np.where(np.diff(s) != 0)[0]
    if idx.size == 0:
        return float("nan")
    crossings = []
    for i in idx:
        x0, x1 = grid[i], grid[i + 1]
        y0, y1 = curve[i], curve[i + 1]
        x = x0 if y1 == y0 else x0 - y0 * (x1 - x0) / (y1 - y0)
        crossings.append(x)
    arr = np.asarray(crossings, dtype=float)
    return float(arr[np.argmin(np.abs(arr - spot))])


def _gamma_flip(
    spot: float, K: np.ndarray, T: np.ndarray, IV: np.ndarray,
    sgn: np.ndarray, OI: np.ndarray, M: np.ndarray,
    r: float, pct: float, steps: int,
) -> float:
    grid = np.linspace(spot * (1.0 - pct), spot * (1.0 + pct), int(steps))
    # gamma at every (grid spot, contract) pair → (steps, n)
    g = bs.gamma(grid[:, None], K[None, :], T[None, :], IV[None, :], r)
    g = np.where(np.isfinite(g), g, 0.0)
    weight = (sgn * OI * M)[None, :]
    curve = (weight * g * (grid[:, None] ** 2) * 0.01).sum(axis=1)
    return _zero_cross(grid, curve, spot)


def compute_gamma_map(
    *,
    symbol: str,
    ts: int,
    spot: float,
    strike: Any,
    tau: Any,            # years to expiry
    sign: Any,           # +1 call, −1 put
    oi: Any,             # open interest
    sigma: Any,          # implied vol per contract
    mult: Any,           # contract multiplier (size)
    r: float = 0.045,
    flip_scan_pct: float = 0.20,
    flip_scan_steps: int = 201,
    pin_window_pct: float = 0.15,
) -> GammaMap:
    """Build the GEX map from per-contract arrays. Invalid contracts (OI≤0,
    σ≤0/non-finite, bad strike/τ/mult) are dropped before aggregation.
    """
    spot = float(spot)
    K = np.asarray(strike, dtype=float)
    T = np.asarray(tau, dtype=float)
    sgn = np.asarray(sign, dtype=float)
    OI = np.asarray(oi, dtype=float)
    IV = np.asarray(sigma, dtype=float)
    M = np.asarray(mult, dtype=float)

    valid = (
        (OI > 0) & np.isfinite(IV) & (IV > 0)
        & np.isfinite(K) & (K > 0) & np.isfinite(T) & (T > 0)
        & np.isfinite(M) & (M > 0)
    )
    K, T, sgn, OI, IV, M = (a[valid] for a in (K, T, sgn, OI, IV, M))

    if K.size == 0 or not (spot > 0):
        return GammaMap(symbol, int(ts), spot, 0.0, 0, float("nan"),
                        float("nan"), float("nan"), float("nan"), {})

    cg = _per_contract_dollar_gamma(spot, K, T, IV, OI, M, r)  # ≥ 0 magnitude
    net_gex = float((sgn * cg).sum())
    regime = 1 if net_gex > 0 else -1

    # per-strike call/put gamma notional (cg is unsigned magnitude)
    is_call = sgn > 0
    per_strike: dict[float, float] = {}
    call_notional: dict[float, float] = {}
    put_notional: dict[float, float] = {}
    for k in np.unique(K):
        mk = k == K
        c = float(cg[mk & is_call].sum())
        p = float(cg[mk & ~is_call].sum())
        kf = float(k)
        call_notional[kf] = c
        put_notional[kf] = p
        per_strike[kf] = c - p   # calls +, puts −

    calls_above = [(k, v) for k, v in call_notional.items() if k >= spot and v > 0]
    puts_below = [(k, v) for k, v in put_notional.items() if k <= spot and v > 0]
    call_wall = max(calls_above, key=lambda kv: kv[1])[0] if calls_above else float("nan")
    put_wall = max(puts_below, key=lambda kv: kv[1])[0] if puts_below else float("nan")

    lo, hi = spot * (1.0 - pin_window_pct), spot * (1.0 + pin_window_pct)
    near = [(k, call_notional[k] + put_notional[k]) for k in per_strike if lo <= k <= hi]
    pin = max(near, key=lambda kv: kv[1])[0] if near else float("nan")

    flip = _gamma_flip(spot, K, T, IV, sgn, OI, M, r, flip_scan_pct, flip_scan_steps)

    return GammaMap(symbol, int(ts), spot, net_gex, regime, flip,
                    call_wall, put_wall, pin, per_strike)
