"""M9 auction-EVOLUTION features for the ``moc_meta_v1`` family (M3_REGISTRATION.md,
"M9 auction-evolution features + calibrated sizing — registered 2026-07-17").

The M8 meta-model scores the classical |basis|>=10 rule from a SNAPSHOT of
reliability features at the 15:55:10 ET decision instant. M9 Cell A asks whether
the *path* of the auction over the legal decision window carries extra
reliability signal the snapshot throws away. It adds EXACTLY the five registered
path scalars, all computed STRICTLY over ``[15:50:00, 15:55:10]`` ET (the leakage
boundary — a message at 15:55:11 is out of window) from the NOII message STREAM
(every disseminated message in the window, not just the governing snapshot) plus
the fixed decision-instant scalars (side, m0=mid, adv20):

  1. ``imb_velocity``      slope of imb_shares/adv20 (the signed normalized
                           imbalance, in bps-of-ADV) over the LAST 90 s, per minute.
  2. ``imb_accel``         last-30 s velocity minus prior-30 s velocity (a
                           second-difference / acceleration proxy).
  3. ``near_conv_slope``   OLS slope (bps/min) of the signed basis
                           ``signed_basis(t) = side * 1e4 * (near(t) - m0) / m0``
                           with ``side`` and ``m0`` FIXED at 15:55:10; near(t) is
                           the indicative clearing price, which is BLANK (0) until
                           ~15:55:00 — those points are MASKED, never zero-filled.
  4. ``near_jitter``       std (ddof=1) of the first-differences of ``signed_basis``
                           over the same masked points (indicative instability).
  5. ``paired_frac_slope`` OLS slope of ``paired_ratio = paired/(paired+|imb|)``
                           over the window, per minute.

BLANK-UNTIL-POPULATED discipline (registered): near/far indicative prices are 0
before ~15:55:00; a masked point is DROPPED, not set to 0. When a window has fewer
than ``MIN_PTS`` (=3) usable points the slope/jitter is 0.0 and its ``*_present``
flag is False — the model gets an honest "not enough path" rather than a spurious
0-slope indistinguishable from a genuinely flat path.

WINSORIZATION (registered, 1/99): each raw scalar is winsorized at the 1st/99th
percentile of the TRAINING population and the SAME bounds applied to the test fold
(``fit_winsor_bounds`` on train -> ``apply_winsor`` on train and test) — computed
per walk-forward fold so no test-fold statistic ever touches a training bound.

LEAKAGE INVARIANT (unit-tested): ``reconstruct_basis_bps`` rebuilds the 15:55:10
basis from the raw NOII+BBO stream; it must equal the pre-computed
``events.parquet`` ``basis_bps`` to < 0.5 bps. ``signed_basis`` at 15:55:10 equals
``|basis_bps|`` by construction (side = sign(near - mid)), so the path features are
anchored to exactly the snapshot the M8 model already trusts.

This is the FEATURE layer only; ``apps/run_m9.py`` is the orchestration + report
+ walk-forward (with the per-fold winsorization) + paired-comparison layer. Nothing
here writes a ledger row or a verdict. POST-HOLDOUT: walk-forward OOS only.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from enginev51.data.noii import _side_sign, et_ns, load_noii_session

# The five REGISTERED evolution scalars, in a fixed, documented order. These are
# the ONLY columns M9 Cell A adds to the M8 meta feature set.
EVO_FEATURES: tuple[str, ...] = (
    "imb_velocity",
    "imb_accel",
    "near_conv_slope",
    "near_jitter",
    "paired_frac_slope",
)
# Parallel present-flag columns (True iff the window had >= MIN_PTS usable points).
EVO_PRESENT: tuple[str, ...] = tuple(f"{c}_present" for c in EVO_FEATURES)

# Legal decision window (ET) — STRICT: [15:50:00, 15:55:10]. 15:55:11 is out.
WINDOW_START_HMS: tuple[int, int, int] = (15, 50, 0)
DECISION_HMS: tuple[int, int, int] = (15, 55, 10)

# Sub-window spans (seconds back from the 15:55:10 decision instant).
VELOCITY_LOOKBACK_S: float = 90.0
ACCEL_HALF_S: float = 30.0

# Minimum usable points for a slope/jitter to be "present" (registered rule).
MIN_PTS: int = 3

NS_PER_S = 1_000_000_000
_MIN = 60.0  # seconds per minute (slopes are per-minute)


# --------------------------------------------------------------------------- math


def ols_slope(t_ns: np.ndarray, y: np.ndarray) -> tuple[float, bool]:
    """OLS slope of ``y`` on time (MINUTES), from epoch-ns times ``t_ns``.

    Returns ``(slope_per_min, present)``. ``present`` is False (and slope 0.0)
    when there are fewer than ``MIN_PTS`` points or the times have zero variance
    (a single instant): an honest "not enough path", never a spurious 0. The
    origin shift (t - mean) makes the slope invariant to the time zero-point.
    """
    t = np.asarray(t_ns, dtype=float)
    y = np.asarray(y, dtype=float)
    if t.shape[0] < MIN_PTS:
        return 0.0, False
    tm = (t / NS_PER_S) / _MIN  # minutes
    tc = tm - tm.mean()
    denom = float(np.dot(tc, tc))
    if denom <= 0.0:
        return 0.0, False
    slope = float(np.dot(tc, y - y.mean()) / denom)
    return slope, True


def _jitter(y: np.ndarray) -> tuple[float, bool]:
    """Std (ddof=1) of the first-differences of ``y`` (already time-ordered).

    ``(jitter, present)``; present False + 0.0 when < MIN_PTS points (so < 2
    first-differences, i.e. no dispersion to measure)."""
    y = np.asarray(y, dtype=float)
    if y.shape[0] < MIN_PTS:
        return 0.0, False
    d = np.diff(y)
    if d.shape[0] < 2:
        return 0.0, False
    return float(np.std(d, ddof=1)), True


# --------------------------------------------------------------------------- path build


def _window_stream(noii_frame: pl.DataFrame, session_iso: str) -> pl.DataFrame:
    """The NOII messages STRICTLY within [15:50:00, 15:55:10] ET, ts-sorted.

    ``ts <= decision`` and ``ts >= window_start`` — the 15:55:10 instant is IN,
    a 15:55:11 message is OUT (the registered leakage boundary)."""
    lo = et_ns(session_iso, *WINDOW_START_HMS)
    hi = et_ns(session_iso, *DECISION_HMS)
    return noii_frame.filter((pl.col("ts") >= lo) & (pl.col("ts") <= hi)).sort("ts")


def _norm_imb_series(win: pl.DataFrame, adv20: float) -> np.ndarray:
    """Signed normalized imbalance per message, in bps-of-ADV.

    ``sign(direction) * imbalance_shares * price / adv20 * 1e4`` where ``price`` is
    the near indicative clearing price when populated (>0) else the reference price
    — the SAME near->ref fallback ``data/noii.signal_at`` uses, so the endpoint of
    this path is exactly the M8 ``norm_imb`` snapshot (times 1e4). Instantaneous
    direction per message (the imbalance genuinely flips side across the auction)."""
    sides = np.array([_side_sign(s) for s in win["side"].to_list()], dtype=float)
    imb = win["imbalance_shares"].fill_null(0.0).to_numpy().astype(float)
    near = win["near_price"].fill_null(0.0).to_numpy().astype(float)
    ref = win["ref_price"].fill_null(0.0).to_numpy().astype(float)
    price = np.where(near > 0.0, near, ref)
    return sides * imb * price / float(adv20) * 1e4


def _paired_ratio_series(win: pl.DataFrame) -> np.ndarray:
    """``paired/(paired+|imb|)`` per message (0 where the denominator is 0)."""
    imb = win["imbalance_shares"].fill_null(0.0).to_numpy().astype(float)
    paired = win["paired_shares"].fill_null(0.0).to_numpy().astype(float)
    denom = paired + np.abs(imb)
    out = np.zeros_like(denom)
    nz = denom > 0.0
    out[nz] = paired[nz] / denom[nz]
    return out


def _signed_basis_series(
    win: pl.DataFrame, side: int, m0: float
) -> tuple[np.ndarray, np.ndarray]:
    """``(ts, signed_basis)`` over ONLY the messages whose near price is populated.

    ``signed_basis(t) = side * 1e4 * (near(t) - m0) / m0`` with ``side`` and ``m0``
    FIXED at 15:55:10. Points with ``near <= 0`` are MASKED (dropped), never
    zero-filled — the registered blank-until-populated rule. Returns the masked
    ts and value arrays (possibly empty)."""
    near = win["near_price"].fill_null(0.0).to_numpy().astype(float)
    ts = win["ts"].to_numpy().astype(np.int64)
    mask = near > 0.0
    sb = float(side) * 1e4 * (near[mask] - m0) / m0
    return ts[mask], sb


# --------------------------------------------------------------------------- reconstruct


def reconstruct_basis_bps(
    symbol: str,
    session: str,
    *,
    noii_frame: pl.DataFrame | None = None,
    bbo_frame: pl.DataFrame | None = None,
    noii_dir=None,
    bbo_dir=None,
) -> float | None:
    """Rebuild ``basis_bps`` at 15:55:10 ET from the raw NOII + BBO stream.

    ``1e4 * (near - mid)/mid`` where ``near`` = last NOII message at-or-before
    15:55:10 with ``near_price>0`` (the M6-FINAL ``near_at`` rule) and ``mid`` = the
    prevailing bbo-1s mid at 15:55:10. This is the LEAKAGE invariant: it must equal
    the pre-computed ``events.parquet`` ``basis_bps`` to < 0.5 bps (unit-tested).
    Returns ``None`` when near or mid is unavailable. Frames are injectable so the
    unit path never touches disk."""
    from enginev51.apps.run_basis_trial import near_at
    from enginev51.backtest.auction_replay import tape_from_bbo
    from enginev51.backtest.fills import prevailing_mid

    sym = symbol.upper()
    if noii_frame is None:
        noii_frame = load_noii_session(sym, session, out_dir=noii_dir)
    if noii_frame is None or noii_frame.height == 0:
        return None
    if bbo_frame is None:
        from enginev51.data.bbo1s import load_bbo_session

        bbo_frame = load_bbo_session(sym, session, out_dir=bbo_dir)
    if bbo_frame is None or bbo_frame.height == 0:
        return None

    ts_dec = et_ns(session, *DECISION_HMS)
    near = near_at(noii_frame, ts_dec)
    if near is None:
        return None
    tape = tape_from_bbo(sym, bbo_frame)
    mid = prevailing_mid(tape.q_ts, tape.q_bid, tape.q_ask, ts_dec)
    if not np.isfinite(mid) or mid <= 0.0:
        return None
    return 1e4 * (near - mid) / mid


# --------------------------------------------------------------------------- api


def _blank() -> dict:
    """All-zero, all-absent feature dict (no usable path)."""
    d: dict = {c: 0.0 for c in EVO_FEATURES}
    d.update({c: False for c in EVO_PRESENT})
    return d


def evo_features(
    symbol: str,
    session: str,
    *,
    adv20: float | None = None,
    side: int | None = None,
    m0: float | None = None,
    noii_frame: pl.DataFrame | None = None,
    bbo_frame: pl.DataFrame | None = None,
    noii_dir=None,
    bbo_dir=None,
) -> dict:
    """The 5 registered evolution scalars for one (symbol, session), + present flags.

    Computed STRICTLY over ``[15:50:00, 15:55:10]`` ET from the NOII message stream
    plus the decision-instant scalars ``side``/``m0``/``adv20``. Those three are
    injectable so the M9 join can pass the EXACT values from ``events.parquet``
    (``side``, ``entry_mid``, ``adv20_dollars``) — guaranteeing ``signed_basis`` at
    15:55:10 equals ``|basis_bps|``. When omitted they are derived from the raw
    stream (self-contained path used by the standalone/unit tests): ``adv20`` from
    ``auction_replay.adv20_dollars``, and ``side``/``m0`` from the reconstructed
    near vs prevailing bbo mid.

    RAW (un-winsorized) values — winsorization is a per-fold train-fit transform
    applied by the walk-forward (``fit_winsor_bounds``/``apply_winsor``). Returns
    a dict of ``EVO_FEATURES`` + ``EVO_PRESENT`` (all 0.0/False when there is no
    usable NOII window)."""
    sym = symbol.upper()
    if noii_frame is None:
        noii_frame = load_noii_session(sym, session, out_dir=noii_dir)
    if noii_frame is None or noii_frame.height == 0:
        return _blank()

    # Fixed decision-instant scalars (from events when provided, else derived).
    if adv20 is None:
        from enginev51.backtest.auction_replay import adv20_dollars
        from enginev51.config import get_settings

        adv20 = adv20_dollars(get_settings(), sym, session)
    if adv20 is None or adv20 <= 0.0:
        return _blank()

    if side is None or m0 is None:
        from enginev51.apps.run_basis_trial import direction_of, near_at
        from enginev51.backtest.auction_replay import tape_from_bbo
        from enginev51.backtest.fills import prevailing_mid

        if bbo_frame is None:
            from enginev51.data.bbo1s import load_bbo_session

            bbo_frame = load_bbo_session(sym, session, out_dir=bbo_dir)
        if bbo_frame is None or bbo_frame.height == 0:
            return _blank()
        ts_dec = et_ns(session, *DECISION_HMS)
        near0 = near_at(noii_frame, ts_dec)
        tape = tape_from_bbo(sym, bbo_frame)
        mid0 = prevailing_mid(tape.q_ts, tape.q_bid, tape.q_ask, ts_dec)
        if near0 is None or not np.isfinite(mid0) or mid0 <= 0.0:
            return _blank()
        side = direction_of(near0, mid0)
        m0 = float(mid0)
    if m0 is None or m0 <= 0.0 or side is None:
        return _blank()

    win = _window_stream(noii_frame, session)
    if win.height == 0:
        return _blank()

    ts = win["ts"].to_numpy().astype(np.int64)
    ts_dec = et_ns(session, *DECISION_HMS)

    # ---- imbalance velocity / acceleration (normalized imbalance path) --------
    imb = _norm_imb_series(win, float(adv20))
    lo90 = ts_dec - int(VELOCITY_LOOKBACK_S * NS_PER_S)
    m90 = ts >= lo90
    imb_velocity, vpres = ols_slope(ts[m90], imb[m90])

    lo30 = ts_dec - int(ACCEL_HALF_S * NS_PER_S)
    lo60 = ts_dec - int(2 * ACCEL_HALF_S * NS_PER_S)
    m_last = ts >= lo30
    m_prior = (ts >= lo60) & (ts < lo30)
    v_last, p_last = ols_slope(ts[m_last], imb[m_last])
    v_prior, p_prior = ols_slope(ts[m_prior], imb[m_prior])
    imb_accel = (v_last - v_prior) if (p_last and p_prior) else 0.0
    apres = bool(p_last and p_prior)

    # ---- near convergence slope / jitter (masked to populated near) -----------
    sb_ts, sb = _signed_basis_series(win, int(side), float(m0))
    near_conv_slope, cpres = ols_slope(sb_ts, sb)
    near_jitter, jpres = _jitter(sb)

    # ---- paired-fraction slope (full window) ----------------------------------
    pr = _paired_ratio_series(win)
    paired_frac_slope, ppres = ols_slope(ts, pr)

    return {
        "imb_velocity": imb_velocity,
        "imb_accel": imb_accel,
        "near_conv_slope": near_conv_slope,
        "near_jitter": near_jitter,
        "paired_frac_slope": paired_frac_slope,
        "imb_velocity_present": vpres,
        "imb_accel_present": apres,
        "near_conv_slope_present": cpres,
        "near_jitter_present": jpres,
        "paired_frac_slope_present": ppres,
    }


# --------------------------------------------------------------------------- winsor


def fit_winsor_bounds(
    df: pl.DataFrame, cols: tuple[str, ...] = EVO_FEATURES, *, lo_q: float = 0.01, hi_q: float = 0.99
) -> dict[str, tuple[float, float]]:
    """1/99 winsor bounds per column, fit on the TRAIN population (registered).

    Returns ``{col: (lo, hi)}`` where lo/hi are the ``lo_q``/``hi_q`` quantiles of
    the non-null training values. A column with no usable values maps to
    ``(-inf, +inf)`` (a no-op clip)."""
    bounds: dict[str, tuple[float, float]] = {}
    for c in cols:
        v = df[c].drop_nulls().to_numpy().astype(float)
        v = v[np.isfinite(v)]
        if v.size == 0:
            bounds[c] = (float("-inf"), float("inf"))
        else:
            bounds[c] = (float(np.quantile(v, lo_q)), float(np.quantile(v, hi_q)))
    return bounds


def apply_winsor(df: pl.DataFrame, bounds: dict[str, tuple[float, float]]) -> pl.DataFrame:
    """Clip each column to its ``bounds[col] = (lo, hi)`` (train-fit, test-applied)."""
    exprs = [
        pl.col(c).clip(lo, hi).alias(c)
        for c, (lo, hi) in bounds.items()
        if c in df.columns
    ]
    return df.with_columns(exprs) if exprs else df
