"""ADIA Lab Research Paper No.19 Sharpe inference — the house statistics kernel.

Lopez de Prado, Lipton & Zoonekynd (2026). The project standard (adopted
2026-07-23): report SR at the NATIVE frequency (never annualized by sqrt-scaling),
PSR under the GENERALIZED (non-Normal, AR(1)) sampling variance evaluated with the
bracket at the BENCHMARK SR0, and MinTRL at alpha next to any significance claim.
Pearson kurtosis (``fisher=False``) throughout — a Normal sample gives ~3, not ~0.

``_bracket()`` is the generalized sampling variance's leading factor; the PSR
denominator uses bracket at the BENCHMARK SR0, the displayed SE uses bracket at the
ESTIMATE SR_hat — the two must not be swapped.

PROVENANCE: these definitions were written and golden-anchored inside
``research_screens.sizing_shadow`` (M23) and were MOVED here VERBATIM by the
2026-08-01 structural review (J3a) so that M24/M27/the live engine/the m28-m29
battery scripts no longer import a closed research screen to get pure math.
``sizing_shadow`` re-imports every name, so object IDENTITY is preserved for every
historical importer (``sizing_shadow.psr is stats.adia.psr``); the M23 golden
anchors (``tests/test_m23_sizing_shadow.py``) still pin the formulas unchanged.
Bodies are byte-identical to the M23 originals — do not "clean up" the math.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import kurtosis, norm, skew


def _bracket(sr: float, rho: float, g3: float, g4: float) -> float:
    """(1+rho)/(1-rho) - ((1+rho+rho^2)/(1-rho^2))*g3*sr
    + ((1+rho^2)/(1-rho^2))*((g4-1)/4)*sr^2."""
    a = (1.0 + rho) / (1.0 - rho)
    b = (1.0 + rho + rho * rho) / (1.0 - rho * rho)
    c = (1.0 + rho * rho) / (1.0 - rho * rho)
    return a - b * g3 * sr + c * ((g4 - 1.0) / 4.0) * sr * sr


def lag1_autocorr(x: np.ndarray | list[float]) -> float:
    """Lag-1 autocorrelation rho_hat of the demeaned series (0.0 for a constant)."""
    x = np.asarray(x, dtype=float)
    if x.size < 2:
        return 0.0
    x = x - x.mean()
    denom = float(np.dot(x, x))
    if denom == 0.0:
        return 0.0
    return float(np.dot(x[:-1], x[1:]) / denom)


def sample_moments(x: np.ndarray | list[float]) -> tuple[float, float, float]:
    """(skew, Pearson-kurtosis, lag-1 rho) of ``x``.

    ``kurtosis(fisher=False)`` (Pearson) => a Normal sample yields ~3, NOT ~0 -- the
    convention pin (test_kurtosis_pearson_convention). A constant/degenerate series
    returns the Normal fallback (0.0, 3.0, 0.0) so a zero-variance delta series never
    poisons PSR/SR with NaN (reviewer attack 4)."""
    x = np.asarray(x, dtype=float)
    if x.size < 2 or not np.isfinite(np.std(x, ddof=1)) or np.std(x, ddof=1) == 0.0:
        return 0.0, 3.0, 0.0
    g3 = float(skew(x, bias=False))
    g4 = float(kurtosis(x, fisher=False, bias=False))
    return g3, g4, lag1_autocorr(x)


def sr_native(x: np.ndarray | list[float]) -> float:
    """Native-frequency Sharpe = mean / stdev(ddof=1). A degenerate (constant) series
    -> 0.0, never NaN."""
    x = np.asarray(x, dtype=float)
    if x.size < 2:
        return 0.0
    sd = float(np.std(x, ddof=1))
    if sd == 0.0 or not np.isfinite(sd):
        return 0.0
    return float(np.mean(x) / sd)


def sigma_sr(sr: float, t: int, rho: float, g3: float, g4: float) -> float:
    """Displayed SE of a Sharpe estimate = sqrt(bracket(sr)/T). Evaluated at the point
    passed in: call with SR_hat for the DISPLAYED SE, with SR0 inside ``psr``.

    Guarded against a NEGATIVE bracket (a pathological high-kurtosis/high-SR region
    where the generalized variance factor goes negative): returns NaN rather than a
    real sqrt of a negative number. The panel converts a non-finite SE to None so no
    NaN can leak into the JSON (N3)."""
    if t <= 0:
        return float("nan")
    br = _bracket(sr, rho, g3, g4)
    if br < 0.0:
        return float("nan")
    return float(np.sqrt(br / t))


def psr(sr_hat: float, sr0: float, t: int, rho: float, g3: float, g4: float) -> float:
    """PSR = Phi((SR_hat - SR0) / sigma_sr(SR0)) -- bracket at the BENCHMARK SR0.

    Swapping in sigma_sr(SR_hat) is the classic error; test_psr_off_anchor (SR0!=0,
    rho!=0, g3!=0) is calibrated so the swap changes the value."""
    se0 = sigma_sr(sr0, t, rho, g3, g4)
    if se0 == 0.0 or not np.isfinite(se0):
        return float("nan")
    return float(norm.cdf((sr_hat - sr0) / se0))


def min_trl(sr_hat: float, sr0: float, alpha: float, rho: float, g3: float, g4: float) -> float:
    """Minimum track record length = bracket(SR0) * (z_{1-alpha} / (SR_hat - SR0))^2.

    SR_hat == SR0 (no edge over the benchmark) => +inf (an undefined/infinite track
    requirement), reported honestly rather than raising."""
    d = sr_hat - sr0
    if d == 0.0:
        return float("inf")
    z = float(norm.ppf(1.0 - alpha))
    return float(_bracket(sr0, rho, g3, g4) * (z / d) ** 2)
