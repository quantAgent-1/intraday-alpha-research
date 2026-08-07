"""OU MLE + epsilon ring buffer + periodic recalibration.

BUILD-SPEC A6/A7/A8, §1. Port target (authoritative): engineV2
``backtest/cpu/ou_mle_nb.py:58-92`` (``mle_ou``), ``indicators_nb.py:503-535``
(``ou_sample`` / ``ou_is_warm``), ``event_loop_nb.py:149-176`` (``_calibrate_ou``).

MLE (closed form on equispaced 1 Hz samples), verbatim from ou_mle_nb.mle_ou:
    μ      = mean(ε)
    α̂      = Σ(εᵢ−μ)(εᵢ₊₁−μ) / Σ(εᵢ−μ)²        (i = 0..n−2)
    κ̂      = −ln(α̂) / Δt                        (require 0 < α̂ < 1)
    σ²_disc = Σ((εᵢ₊₁−μ) − α̂(εᵢ−μ))² / (n−1)
    σ̂²     = 2κ̂ / max(1−α̂², 1e-18) · σ²_disc     (require σ̂² > 0)
    θ̂ = μ

DECLARED DEVIATION (output-neutral): engineV2's mle_ou returns NaN for n<30.
That branch is dead in the backtest — the calibrator only ever calls with
n >= OU_MIN_SAMPLES (=300). We lower the internal floor to n<2 so the
hand-computed 10-sample test fixture (BUILD-SPEC §6.1) can exercise the exact
estimator; the operative attempt gate n>=300 is enforced in ``OUCalibrator``.

Ring / calibration semantics = BACKTEST (BUILD-SPEC: "backtest wins"):
    * ε sampled on trade activity only (volume>0 bar), <= 1 sample / s.
    * ring capacity 4096, NO time-based eviction (ou_sample's fixed ring);
      A7's hot-path "evict >1200 s / latest 300" describes the LIVE ring and is
      NOT what the anchor engine does — the backtest calibrates on ALL ring
      samples (up to 4096). Matching this is required to reproduce the anchor.
    * calibrate every 60 s; attempt gate n >= 300; require κ>0, σ>0, finite θ.
    * cold-start (fresh buffer) every session (A8 WorkerJob semantics).
"""

from __future__ import annotations

import math
from typing import NamedTuple

import numpy as np

from enginev51.reversion.thresholds import solve_thresholds

# engineV2 indicators_nb.py:499-500
OU_SAMPLE_INTERVAL_NS = 1_000_000_000  # <= 1 sample / s
OU_MIN_SAMPLES = 300                    # backtest attempt gate (NOT live's 30)
OU_RING_CAP = 4096                      # engineV2 event_loop_nb.allocate_indicator_state ou_buf_cap

# engineV2 runner defaults (BacktestCPUConfig)
CALIB_INTERVAL_NS = 60_000_000_000     # ou_calib_interval_sec = 60.0
TRANSACTION_COST_C = 0.0008            # ou_transaction_cost_c
DISCOUNT_RHO = 0.01                    # ou_discount_rho
SAMPLE_DT_SEC = 1.0                    # ou_sample_dt_sec


class OUFit(NamedTuple):
    alpha: float
    kappa: float
    theta: float
    sigma: float
    valid: bool


class OUThresholds(NamedTuple):
    kappa: float
    theta: float
    sigma: float
    entry_long: float
    exit_long: float
    entry_short: float
    exit_short: float
    is_fresh: bool


def mle_ou(samples: np.ndarray, dt: float) -> OUFit:
    """Closed-form OU MLE. Verbatim engineV2 ou_mle_nb.mle_ou arithmetic (see
    module docstring for the n<30→n<2 declared, output-neutral floor change)."""
    s = np.asarray(samples, dtype=np.float64)
    n = s.size
    nan_fit = OUFit(math.nan, math.nan, math.nan, math.nan, False)
    if n < 2 or dt <= 0.0:
        return nan_fit
    mu = float(s.mean())
    a_arr = s[:-1] - mu
    b_arr = s[1:] - mu
    denom = float(np.dot(a_arr, a_arr))
    num = float(np.dot(a_arr, b_arr))
    if denom <= 1e-18:
        return nan_fit
    alpha = num / denom
    if not (alpha > 0.0 and alpha < 1.0):
        return nan_fit
    kappa = -math.log(alpha) / dt
    d = b_arr - alpha * a_arr
    res_acc = float(np.dot(d, d))
    sigma2_disc = res_acc / (n - 1)
    sigma2 = 2.0 * kappa / max(1.0 - alpha * alpha, 1e-18) * sigma2_disc
    if not (sigma2 > 0.0):
        return nan_fit
    return OUFit(alpha, kappa, mu, math.sqrt(sigma2), True)


class OUCalibrator:
    """Per-session epsilon ring + periodic recalibration (backtest semantics).

    Feed ``sample(ts_ns, mid, vwap_5m)`` on every bar; it appends ε = mid − vwap
    to the ring at most once per second (only when mid>0 and vwap>0, i.e. trade
    activity). Call ``maybe_calibrate(ts_ns)`` every bar; it recomputes
    thresholds at most every 60 s and returns the current OUThresholds (or None
    before the first successful calibration). ``latest_eps`` is updated on every
    accepted sample (engineV2 state_ou[3]).
    """

    def __init__(
        self,
        *,
        cost_c: float = TRANSACTION_COST_C,
        discount_rho: float = DISCOUNT_RHO,
        sample_dt_sec: float = SAMPLE_DT_SEC,
        calib_interval_ns: int = CALIB_INTERVAL_NS,
        min_samples: int = OU_MIN_SAMPLES,
        ring_cap: int = OU_RING_CAP,
    ) -> None:
        self._cost_c = cost_c
        self._rho = discount_rho
        self._dt = sample_dt_sec
        self._interval_ns = calib_interval_ns
        self._min_samples = min_samples
        self._ring_cap = ring_cap
        self._buf: list[float] = []
        self._last_sample_ts: int = -1
        self._last_calib_ts: int = -1
        self.latest_eps: float = math.nan
        # Persisted snapshot (engineV2 snap[SNAP_OU_*]); unchanged when a
        # calibration attempt returns early (n<300 or invalid MLE).
        self._thr: OUThresholds | None = None

    def reset(self) -> None:
        """Cold-start all OU state for a new session (A8)."""
        self._buf.clear()
        self._last_sample_ts = -1
        self._last_calib_ts = -1
        self.latest_eps = math.nan
        self._thr = None

    @property
    def n_samples(self) -> int:
        return len(self._buf)

    @property
    def is_warm(self) -> bool:
        """ou_is_warm: ring has reached OU_MIN_SAMPLES (indicators_nb.py:533-535)."""
        return len(self._buf) >= self._min_samples

    def sample(self, ts_ns: int, mid: float, vwap_5m: float) -> None:
        """engineV2 indicators_nb.ou_sample: ε=mid−vwap; store latest always;
        push to ring only when >= 1 s since the last push."""
        if not (vwap_5m > 0.0 and mid > 0.0):
            return
        eps = mid - vwap_5m
        self.latest_eps = eps
        if self._last_sample_ts >= 0 and (ts_ns - self._last_sample_ts) < OU_SAMPLE_INTERVAL_NS:
            return
        self._last_sample_ts = ts_ns
        self._buf.append(eps)
        if len(self._buf) > self._ring_cap:
            # Fixed ring: drop oldest (engineV2 head advance, no time eviction).
            del self._buf[0]

    def maybe_calibrate(self, ts_ns: int) -> OUThresholds | None:
        """engineV2 event_loop_nb: attempt at most every 60 s; ``_calibrate_ou``
        leaves the persisted thresholds UNCHANGED on n<300 or invalid MLE, and
        overwrites them (possibly to NaN → is_fresh False) on a valid MLE."""
        if self._last_calib_ts >= 0 and (ts_ns - self._last_calib_ts) < self._interval_ns:
            return self._thr
        self._last_calib_ts = ts_ns
        if len(self._buf) < self._min_samples:
            return self._thr  # unchanged
        fit = mle_ou(np.asarray(self._buf, dtype=np.float64), self._dt)
        if not (fit.valid and fit.kappa > 0.0 and fit.sigma > 0.0 and np.isfinite(fit.theta)):
            return self._thr  # unchanged
        el, xl, es, xs = solve_thresholds(fit.kappa, fit.theta, fit.sigma, self._rho, self._cost_c)
        is_fresh = not (math.isnan(el) or math.isnan(xl))
        self._thr = OUThresholds(fit.kappa, fit.theta, fit.sigma, el, xl, es, xs, is_fresh)
        return self._thr

    @property
    def thresholds(self) -> OUThresholds | None:
        return self._thr
