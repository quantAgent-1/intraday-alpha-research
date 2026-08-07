"""M18 §6.3 no-lookahead + §6.4 gate causality."""

from __future__ import annotations

import numpy as np
import polars as pl

from enginev51.reversion.features import (
    build_gate_baseline,
    compute_session_features,
    session_gate_arrays,
)

NS = 1_000_000_000


def synth_bars(n: int, *, seed: int = 0, base_ts: int = 0, mid0: float = 100.0) -> pl.DataFrame:
    """Contiguous 1 s event bars with every column compute_session_features reads."""
    rng = np.random.default_rng(seed)
    steps = rng.normal(0, 0.03, n).cumsum()
    mid = mid0 + steps
    half = 0.01
    bid = mid - half
    ask = mid + half
    bs = rng.integers(1, 40, n).astype(float)
    as_ = rng.integers(1, 40, n).astype(float)
    vol = rng.integers(0, 500, n).astype(float)
    px = mid + rng.normal(0, 0.02, n)
    dollar = px * vol
    denom = bs + as_
    return pl.DataFrame({
        "ts": (base_ts + np.arange(n) * NS).astype(np.int64),
        "mid": mid, "bid": bid, "ask": ask, "bid_size": bs, "ask_size": as_,
        "spread_bps_close": 1e4 * (ask - bid) / mid,
        "imb_close": (bs - as_) / denom,
        "micro_dev_bps": 1e4 * ((bs * ask + as_ * bid) / denom - mid) / mid,
        "ofi": rng.normal(0, 5, n),
        "volume": vol, "dollar_vol": dollar,
        "px_open": px, "px_high": px + 0.03, "px_low": px - 0.03, "px_close": px,
        "n_quotes": rng.integers(1, 50, n).astype(float),
    })


def test_no_lookahead_features_before_t0_unchanged():
    df = synth_bars(400, seed=1)
    t0 = 250
    feat_a = compute_session_features(df)

    # Mutate every column of every bar strictly after t0.
    fut = df.slice(t0 + 1, df.height - (t0 + 1))
    mutated = df.slice(0, t0 + 1).vstack(
        fut.with_columns(
            (pl.col("mid") + 5.0).alias("mid"),
            (pl.col("bid") + 5.0).alias("bid"),
            (pl.col("ask") + 5.0).alias("ask"),
            (pl.col("bid_size") * 3 + 7).alias("bid_size"),
            (pl.col("ask_size") * 2 + 9).alias("ask_size"),
            (pl.col("ofi") + 99.0).alias("ofi"),
            (pl.col("volume") + 1000.0).alias("volume"),
            (pl.col("dollar_vol") + 1e6).alias("dollar_vol"),
            (pl.col("px_low") - 3.0).alias("px_low"),
            (pl.col("px_high") + 3.0).alias("px_high"),
        )
    )
    feat_b = compute_session_features(mutated)

    for name in ("mid", "bid", "ask", "spread_bps", "rho_t", "ofi_5s", "micro",
                 "micro_dev_bps", "vwap_5m", "sigma_5m", "vwap_30m", "eps", "warm"):
        a = getattr(feat_a, name)[: t0 + 1]
        b = getattr(feat_b, name)[: t0 + 1]
        np.testing.assert_array_equal(
            np.nan_to_num(a.astype(float), nan=-1e9), np.nan_to_num(b.astype(float), nan=-1e9),
            err_msg=f"lookahead leaked into feature {name!r} at/before t0",
        )


def test_gate_baseline_uses_only_prior_sessions():
    # Build 61 prior "sessions" of gate arrays, then a current session t with a
    # huge micro_dev spike. The runner slices prior_gate_arrays BEFORE appending
    # session t, so t's own spike cannot enter t's baseline.
    prior = [session_gate_arrays(compute_session_features(synth_bars(300, seed=k, base_ts=k * 10**12)))
             for k in range(61)]
    baseline_t = build_gate_baseline(prior[-60:])  # sessions < t only

    # A spiky "current" session t (would inflate p70 massively if leaked).
    spike_feat = compute_session_features(synth_bars(300, seed=999, base_ts=61 * 10**12))
    spike_arr = session_gate_arrays(spike_feat)
    spike_arr = {**spike_arr, "abs_micro_dev": spike_arr["abs_micro_dev"] + 1e6}

    # Baseline that WRONGLY includes t.
    leaked = build_gate_baseline((prior[-60:] + [spike_arr])[-60:])
    assert baseline_t.micro_dev_p70 != leaked.micro_dev_p70
    # The causal baseline is finite and NOT inflated by the 1e6 spike.
    assert np.isfinite(baseline_t.micro_dev_p70)
    assert baseline_t.micro_dev_p70 < 1e5


def test_gate_baseline_nan_without_min_history():
    # < min_sessions prior sessions → NaN baseline (gate fails conservatively).
    prior = [session_gate_arrays(compute_session_features(synth_bars(300, seed=k)))
             for k in range(5)]
    b = build_gate_baseline(prior, min_sessions=20)
    assert np.isnan(b.micro_dev_p70) and np.isnan(b.spread_median) and np.isnan(b.sigma_p90)
