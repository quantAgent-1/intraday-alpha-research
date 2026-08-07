# A0 trial report — M3-A0-v1.1-4sym-kinf

Pooled plan-results rows: 2187  (taken=1716)
Sessions: 187
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 75       | 55    | 20        | 0        | 0    |
| gap_mr      | 70       | 70    | 0         | 0        | 0    |
| letf_window | 484      | 420   | 64        | 0        | 0    |
| vwap_magnet | 1558     | 1171  | 261       | 124      | 2    |
| TOTAL       | 2187     | 1716  | 345       | 124      | 2    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|-------------|----------|---------|------------|--------------|---------|--------|
| expiry_pin  | train    | 30      | 6          | 2.956        | -7.473  | 14.872 |
| expiry_pin  | validate | 25      | 3          | -5.626       | -20.556 | 11.908 |
| gap_mr      | train    | 46      | 36         | 7.847        | -35.91  | 52.499 |
| gap_mr      | validate | 24      | 17         | 13.797       | -88.38  | 90.028 |
| letf_window | train    | 268     | 89         | 1.588        | -9.588  | 13.895 |
| letf_window | validate | 152     | 53         | -6.245       | -23.155 | 9.905  |
| vwap_magnet | train    | 791     | 118        | 5.161        | 1.08    | 9.072  |
| vwap_magnet | validate | 380     | 60         | 4.926        | -1.853  | 11.585 |
| POOLED      | train    | 1135    | 124        | 4.368        | 0.356   | 8.662  |
| POOLED      | validate | 581     | 63         | 1.916        | -5.789  | 9.204  |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 663   |
| stop        | 387   |
| curfew      | 382   |
| hold        | 267   |
| mixed       | 17    |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------------|---------|------------|--------------|---------|--------|
| base           | 1716    | 187        | 3.538        | -0.365  | 7.621  |
| drop_top5      | 1657    | 182        | 1.75         | -1.748  | 5.23   |
| double_spread  | 1716    | 187        | 6.97         | 2.684   | 11.261 |
| double_latency | 1716    | 187        | 3.843        | -0.121  | 7.986  |
| post_promo     | 1716    | 187        | -10.462      | -14.365 | -6.379 |

Concentration:

```
{
  "n_plans": 1716,
  "n_sessions": 187,
  "total_net_bps": 6070.751531116355,
  "top5_session_share": 0.5223521232142607,
  "top_symbol_share": 0.603728547653409,
  "top_payer_share": 0.9808202208794894,
  "effective_n": 3.206570531891769
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": 0.1,
  "latency_drag_bps": -0.306,
  "spread_cost_bps": -3.433,
  "fees_bps": 0.3,
  "net_bps": 3.538
}
```

## 6. Cost table (deterministic fallback, no network)

```
{
  "NVDA": {
    "spread_bps": 1.5,
    "sec_taf_sell_bps": 0.3,
    "slippage_market_bps": 0.5,
    "commission_usd": 0.0,
    "rt_cost_bps": 2.3,
    "source": "fallback"
  },
  "TSLA": {
    "spread_bps": 2.0,
    "sec_taf_sell_bps": 0.3,
    "slippage_market_bps": 0.5,
    "commission_usd": 0.0,
    "rt_cost_bps": 2.8,
    "source": "fallback"
  },
  "AMD": {
    "spread_bps": 2.0,
    "sec_taf_sell_bps": 0.3,
    "slippage_market_bps": 0.5,
    "commission_usd": 0.0,
    "rt_cost_bps": 2.8,
    "source": "fallback"
  },
  "MU": {
    "spread_bps": 2.5,
    "sec_taf_sell_bps": 0.3,
    "slippage_market_bps": 0.5,
    "commission_usd": 0.0,
    "rt_cost_bps": 3.3,
    "source": "fallback"
  }
}
```

## 7. Detector PARAMS provenance (frozen; mirrors M3_REGISTRATION.md)

### gap_mr

```
{
  "sigma_mult": 0.75,
  "min_gap_bps": 30.0,
  "extension_frac": 0.35,
  "stop_gap_mult": 0.25,
  "min_stop_bps": 25.0,
  "target0_halfway": 0.5,
  "expected_gross_mult": 0.5,
  "sigma_h_div": 4.0,
  "hold_max_min": 120,
  "decision_et": [
    9,
    45
  ],
  "min_window_bars": 2,
  "strength_norm_bps": 100.0
}
```

### letf_window

```
{
  "min_index_ret": 0.005,
  "stop_range_mult": 1.2,
  "expected_gross_per_unit_bps": 10.0,
  "expected_gross_cap_bps": 30.0,
  "hold_max_min": 55,
  "decision_et": [
    15,
    0
  ]
}
```

### vwap_magnet

```
{
  "decision_window_et": [
    "10:30",
    "14:30"
  ],
  "sigma_dev_window": 30,
  "sigma_dev_ddof": 1,
  "sigma_dev_includes_current_bar": true,
  "dev_sigma_mult": 1.5,
  "min_dev_bps": 20.0,
  "range_day_frac": 0.35,
  "stop_dev_mult": 2.5,
  "stop_min_bps": 20.0,
  "expected_gross_mult": 0.8,
  "sigma_h_sqrt_horizon": 3.0,
  "rearm_min": 60,
  "hold_max_min": 90,
  "strength_ref_bps": 100.0
}
```

### cascade

```
{
  "decision_window_et": [
    "09:45",
    "14:30"
  ],
  "lookback_bars": 30,
  "sigma_30m_window": 30,
  "sigma_30m_ddof": 1,
  "flush_sigma_mult": 2.5,
  "volume_mult": 3.0,
  "spread_mult": 2.0,
  "spread_window_min": 5,
  "stabilize_bars": 5,
  "ofi_window_min": 5,
  "stop_amp_frac": 0.3,
  "t0_retrace": 0.382,
  "t1_retrace": 0.618,
  "expected_gross_retrace": 0.382,
  "episode_reset_retrace": 0.5,
  "episode_reset_min": 60,
  "hold_max_min": 120,
  "strength_ref_bps": 150.0
}
```

### expiry_pin

```
{
  "decision_window_et": [
    "13:00",
    "14:30"
  ],
  "step_min": 5,
  "grid_hi": 5.0,
  "grid_lo": 2.5,
  "grid_price_threshold": 200.0,
  "min_dist_frac": 0.0005,
  "max_dist_frac": 0.003,
  "stop_far_frac": 0.006,
  "rearm_min": 60,
  "hold_max_min": 170,
  "strength_ref_frac": 0.003
}
```

## 8. Run plumbing counters

```
{
  "arm": "a0",
  "preds_dir": null,
  "overlay_counts": null,
  "m4_mode": null,
  "p_skip": null,
  "drop_counts": null,
  "sessions_in_range": 187,
  "symbol_sessions_seen": 748,
  "symbol_sessions_ok": 744,
  "skip_counts": {
    "no_context": 0,
    "no_event_bars": 4,
    "no_quote": 0
  },
  "state_counts": {
    "gap_mr": 71,
    "letf_window": 484,
    "vwap_magnet": 1558,
    "cascade": 0,
    "expiry_pin": 80
  },
  "plans_authored": 2187,
  "symbols": [
    "NVDA",
    "TSLA",
    "AMD",
    "MU"
  ]
}
```
