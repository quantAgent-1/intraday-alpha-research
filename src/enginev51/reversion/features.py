"""Per-session feature computation on the event_bars1s (1 s) substrate.

BUILD-SPEC §2, A1-A5, A7, A10, §3.3. One row per RTH second (contiguous — the
builder emits exactly one bar per second in [open, close), so a fixed row-window
equals a fixed time-window). Everything here is causal within the session; the
sequential state machine in ``signal.py`` consumes these arrays.

Feature → engineV2 source (transcribed):
  * mid / bid / ask                 close-of-second quote state, forward-filled
                                    across empty-quote buckets (engineV2 LOB/imb
                                    state persists across ticks).
  * rho_t   (A2, imbalance.py:73)   (bid_size−ask_size)/(bid_size+ask_size) from
                                    close-of-second sizes → the imb_close column.
  * ofi_5s  (A1, indicators_nb ofi) trailing-5-bar SUM of the event_bars ``ofi``
                                    column. VERDICT (BUILD-SPEC step 2): the
                                    builder's ofi IS Cont-Kukanov-Stoikov L1
                                    per-second (events summed within each 1 s
                                    bucket) — see enginev51/events/event_bars.py
                                    _ofi (lines 100-115). PRIMARY path used;
                                    fallback (recompute CKS on 1 s L1 snapshots)
                                    NOT needed.
  * microprice (A4, lob.py:41-53)   raw=(bs·ask+as·bid)/(bs+as); reject
                                    bs+as<100 (state holds prior); sticky MEDIAN
                                    of last 3 accepted raws (per-bar cadence).
  * vwap_5m / sigma_5m (A3/A5)      rolling 300 s volume-weighted price and σ_vw
                                    from per-second p_s=dollar_vol/volume.
                                    sigma_5m IS σ_vw in ABSOLUTE DOLLARS (A5
                                    aliasing). DECLARED A3 deviation: within-
                                    second price variance truncated (one p_s per
                                    second) — anchor §7 is the guard.
  * vwap_30m (A10)                  rolling 1800 s VWAP, no bands (trend filter).
  * spread_bps                      spread_bps_close (close-of-second).
  * micro_dev_bps                   raw column (G1 feature; NOT the sticky micro).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

NS_PER_S = 1_000_000_000
# engineV2 LOB_MIN_QUOTE_SIZE = 100 SHARES. The event_bars1s bid_size/ask_size
# are in ROUND LOTS (verified: p50=1 = 100 shares), so engineV2's 100-share
# minimum maps to 1 round lot. (Only the min-size FILTER is unit-sensitive:
# microprice, rho_t and the precomputed ofi are ratios/summed events where the
# lot↔share factor cancels.) Using 100 here rejected ~99.9% of quotes and froze
# the sticky microprice — the unit reconciliation, declared.
MICRO_MIN_QUOTE_SIZE = 1.0     # 1 round lot == engineV2's 100-share threshold
MICRO_STICKY_N = 3             # engineV2 LOB_STICKY_N
VWAP_SHORT_S = 300
VWAP_LONG_S = 1800
OFI_WINDOW_S = 5
IMB_WARMUP = 200              # engineV2 IMB_WARMUP
LOB_WARMUP = MICRO_STICKY_N   # engineV2 lob_is_warm
OFI_Z_MIN = 4                # engineV2 z_n>=4 for ofi_z (warmth only)


@dataclass(slots=True)
class SessionFeatures:
    ts: np.ndarray            # Int64 UTC ns, one per second
    et_minute: np.ndarray     # Int32 ET minute-of-day
    mid: np.ndarray           # ffilled 0.5(bid+ask)
    bid: np.ndarray           # ffilled close-of-second bid (fills)
    ask: np.ndarray           # ffilled close-of-second ask (fills)
    px_low: np.ndarray        # trade low in the second (maker touch)
    px_high: np.ndarray       # trade high in the second (maker touch)
    spread_bps: np.ndarray    # ffilled spread_bps_close
    rho_t: np.ndarray         # ffilled imb_close
    ofi_5s: np.ndarray        # trailing-5-bar ofi sum
    micro: np.ndarray         # sticky-3 microprice (holds prior on reject)
    micro_dev_bps: np.ndarray # ffilled raw micro deviation (G1 feature)
    vwap_5m: np.ndarray
    sigma_5m: np.ndarray
    vwap_30m: np.ndarray
    eps: np.ndarray           # mid − vwap_5m
    volume: np.ndarray
    warm: np.ndarray          # bool: all engineV2 warm gates satisfied at bar i


def _et_minute_expr() -> pl.Expr:
    et = (
        pl.from_epoch(pl.col("ts"), time_unit="ns")
        .dt.replace_time_zone("UTC")
        .dt.convert_time_zone("America/New_York")
    )
    return (et.dt.hour().cast(pl.Int32) * 60 + et.dt.minute().cast(pl.Int32)).alias("et_minute")


def _sticky_microprice(
    bid: np.ndarray, ask: np.ndarray, bs: np.ndarray, as_: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """engineV2 lob.py / indicators_nb.lob_update: raw microprice with min-size
    reject + sticky median of last 3 accepted. Uses RAW (non-ffilled) quote
    columns — an empty-quote bar (null bid) is a reject (state holds prior).
    Returns (sticky, accepted_count)."""
    n = bid.size
    out = np.full(n, np.nan, dtype=np.float64)
    accepted = np.zeros(n, dtype=np.int64)
    hist: list[float] = []
    cnt = 0
    prev = np.nan
    for i in range(n):
        b = bid[i]
        a = ask[i]
        qb = bs[i]
        qa = as_[i]
        denom = qb + qa
        ok = (
            b == b and a == a and b > 0.0 and a > 0.0 and a >= b  # noqa: PLR0124 (b==b: not-NaN)
            and denom >= MICRO_MIN_QUOTE_SIZE
        )
        if ok:
            raw = (qb * a + qa * b) / denom
            hist.append(raw)
            if len(hist) > MICRO_STICKY_N:
                hist.pop(0)
            cnt += 1
            m = len(hist)
            if m == 1:
                prev = hist[0]
            elif m == 2:
                prev = 0.5 * (hist[0] + hist[1])
            else:
                prev = float(sorted(hist)[1])
        out[i] = prev
        accepted[i] = cnt
    return out, accepted


def compute_session_features(df: pl.DataFrame) -> SessionFeatures:
    """Compute the full causal feature frame for one ts-sorted session."""
    df = df.sort("ts")
    # Vectorised rolling aggregates. Zero-volume bars contribute 0 to sums; the
    # per-bar p²·v term guards volume==0.
    pp_term = (
        pl.when(pl.col("volume") > 0)
        .then(pl.col("dollar_vol") * pl.col("dollar_vol") / pl.col("volume"))
        .otherwise(0.0)
    )
    df = df.with_columns(
        _et_minute_expr(),
        pl.col("mid").forward_fill().alias("mid_f"),
        pl.col("bid").forward_fill().alias("bid_f"),
        pl.col("ask").forward_fill().alias("ask_f"),
        pl.col("spread_bps_close").forward_fill().alias("spread_f"),
        pl.col("imb_close").forward_fill().alias("rho_f"),
        pl.col("micro_dev_bps").forward_fill().alias("micro_dev_f"),
        pl.col("ofi").rolling_sum(window_size=OFI_WINDOW_S, min_samples=1).alias("ofi_5s"),
        pl.col("dollar_vol").rolling_sum(window_size=VWAP_SHORT_S, min_samples=1).alias("s_pv"),
        pl.col("volume").rolling_sum(window_size=VWAP_SHORT_S, min_samples=1).alias("s_v"),
        pp_term.rolling_sum(window_size=VWAP_SHORT_S, min_samples=1).alias("s_pp"),
        pl.col("dollar_vol").rolling_sum(window_size=VWAP_LONG_S, min_samples=1).alias("s_pv_l"),
        pl.col("volume").rolling_sum(window_size=VWAP_LONG_S, min_samples=1).alias("s_v_l"),
        (pl.col("n_quotes") > 0).cast(pl.Int64).cum_sum().alias("qbar_count"),
    )
    vwap_5m = pl.when(pl.col("s_v") > 0).then(pl.col("s_pv") / pl.col("s_v")).otherwise(None)
    var5 = pl.when(pl.col("s_v") > 0).then(pl.col("s_pp") / pl.col("s_v") - vwap_5m * vwap_5m).otherwise(None)
    sigma_5m = pl.when(var5.is_not_null()).then(
        pl.when(var5 > 0).then(var5).otherwise(0.0).sqrt()
    ).otherwise(None)
    vwap_30m = pl.when(pl.col("s_v_l") > 0).then(pl.col("s_pv_l") / pl.col("s_v_l")).otherwise(None)
    df = df.with_columns(
        vwap_5m.alias("vwap_5m"),
        sigma_5m.alias("sigma_5m"),
        vwap_30m.alias("vwap_30m"),
    ).with_columns(
        (pl.col("mid_f") - pl.col("vwap_5m")).alias("eps"),
    )

    ts = df["ts"].to_numpy()
    mid = df["mid_f"].to_numpy()
    bid = df["bid_f"].to_numpy()
    ask = df["ask_f"].to_numpy()
    vwap_5m_a = df["vwap_5m"].to_numpy()
    # sticky micro from RAW quote columns (null → reject/hold)
    micro, micro_accepted = _sticky_microprice(
        df["bid"].to_numpy(), df["ask"].to_numpy(),
        df["bid_size"].to_numpy(), df["ask_size"].to_numpy(),
    )
    qbar_count = df["qbar_count"].to_numpy()

    # engineV2 run_day `warm` gate, mapped to the bar grid:
    #   lob(>=3 accepted micro) & imb(>=200 quote bars) & ofi_z(>=4 quote bars)
    #   & vwap not nan & ou(>=300 eps samples). OU warmth is added in signal.py
    #   (it depends on the sequential eps ring); here we expose the non-OU part.
    vwap_ok = ~np.isnan(vwap_5m_a)
    warm_non_ou = (
        (micro_accepted >= LOB_WARMUP)
        & (qbar_count >= IMB_WARMUP)
        & (qbar_count >= OFI_Z_MIN)
        & vwap_ok
    )

    return SessionFeatures(
        ts=ts,
        et_minute=df["et_minute"].to_numpy(),
        mid=mid,
        bid=bid,
        ask=ask,
        px_low=df["px_low"].to_numpy(),
        px_high=df["px_high"].to_numpy(),
        spread_bps=df["spread_f"].to_numpy(),
        rho_t=df["rho_f"].to_numpy(),
        ofi_5s=df["ofi_5s"].to_numpy(),
        micro=micro,
        micro_dev_bps=df["micro_dev_f"].to_numpy(),
        vwap_5m=vwap_5m_a,
        sigma_5m=df["sigma_5m"].to_numpy(),
        vwap_30m=df["vwap_30m"].to_numpy(),
        eps=df["eps"].to_numpy(),
        volume=df["volume"].to_numpy(),
        warm=warm_non_ou,
    )


# --------------------------------------------------------------------------- gates

@dataclass(slots=True, frozen=True)
class GateBaseline:
    """Trailing-60-session in-name baselines, computed from sessions ENDING AT
    t−1 (never same-day). NaN when < ``min_sessions`` prior sessions available."""

    micro_dev_p70: float   # G1: p70 of |micro_dev_bps|
    spread_median: float   # G2: median spread_bps
    sigma_p90: float       # G2: p90 sigma_5m


def session_gate_arrays(feat: SessionFeatures) -> dict[str, np.ndarray]:
    """Per-session pooled samples used to build the next sessions' baselines:
    |micro_dev_bps|, spread_bps, sigma_5m (finite bars only)."""
    amd = np.abs(feat.micro_dev_bps)
    return {
        "abs_micro_dev": amd[np.isfinite(amd)],
        "spread_bps": feat.spread_bps[np.isfinite(feat.spread_bps)],
        "sigma_5m": feat.sigma_5m[np.isfinite(feat.sigma_5m)],
    }


def build_gate_baseline(
    prior_session_arrays: list[dict[str, np.ndarray]], *, min_sessions: int = 20
) -> GateBaseline:
    """Pool the prior sessions' arrays and take p70/median/p90. Causal by
    construction — the caller passes ONLY sessions strictly before t."""
    nan = float("nan")
    if len(prior_session_arrays) < min_sessions:
        return GateBaseline(nan, nan, nan)
    amd = np.concatenate([a["abs_micro_dev"] for a in prior_session_arrays]) if prior_session_arrays else np.array([])
    spr = np.concatenate([a["spread_bps"] for a in prior_session_arrays]) if prior_session_arrays else np.array([])
    sig = np.concatenate([a["sigma_5m"] for a in prior_session_arrays]) if prior_session_arrays else np.array([])
    return GateBaseline(
        micro_dev_p70=float(np.quantile(amd, 0.70)) if amd.size else nan,
        spread_median=float(np.median(spr)) if spr.size else nan,
        sigma_p90=float(np.quantile(sig, 0.90)) if sig.size else nan,
    )


def eval_gates(
    *, side: int, micro_dev_bps: float, ofi_5s: float, spread_bps: float,
    sigma_5m: float, baseline: GateBaseline,
) -> tuple[bool, bool]:
    """Decision-time G1/G2 (BUILD-SPEC §3.3 / REGISTRATION §3.3).

    G1 dislocation quality: |micro_dev_bps| >= trailing p70 AND signed OFI agrees
        with the entry direction (sign(ofi_5s) == side).
    G2 cost state: spread_bps <= trailing median AND sigma_5m not in the top
        decile (sigma_5m < trailing p90).
    A NaN baseline (insufficient history) → that gate fails (conservative).
    """
    g1 = (
        np.isfinite(baseline.micro_dev_p70)
        and abs(micro_dev_bps) >= baseline.micro_dev_p70
        and ((side > 0 and ofi_5s > 0.0) or (side < 0 and ofi_5s < 0.0))
    )
    g2 = (
        np.isfinite(baseline.spread_median)
        and np.isfinite(baseline.sigma_p90)
        and spread_bps <= baseline.spread_median
        and sigma_5m < baseline.sigma_p90
    )
    return bool(g1), bool(g2)
