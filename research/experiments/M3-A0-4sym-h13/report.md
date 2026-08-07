# A0 trial report — M3-A0-4sym-h13

Pooled plan-results rows: 2187  (taken=1287)
Sessions: 187
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 75       | 38    | 37        | 0        | 0    |
| gap_mr      | 70       | 64    | 6         | 0        | 0    |
| letf_window | 484      | 205   | 279       | 0        | 0    |
| vwap_magnet | 1558     | 980   | 441       | 135      | 2    |
| TOTAL       | 2187     | 1287  | 763       | 135      | 2    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|-------------|----------|---------|------------|--------------|---------|--------|
| expiry_pin  | train    | 23      | 6          | 4.795        | -6.644  | 14.533 |
| expiry_pin  | validate | 15      | 3          | -5.589       | -26.849 | 6.188  |
| gap_mr      | train    | 44      | 36         | -0.96        | -43.982 | 43.165 |
| gap_mr      | validate | 20      | 17         | 9.585        | -61.389 | 75.799 |
| letf_window | train    | 131     | 83         | -0.053       | -13.073 | 13.545 |
| letf_window | validate | 74      | 49         | -1.011       | -15.385 | 12.119 |
| vwap_magnet | train    | 643     | 118        | -1.736       | -6.477  | 2.989  |
| vwap_magnet | validate | 337     | 60         | -1.782       | -8.643  | 5.448  |
| POOLED      | train    | 841     | 124        | -1.254       | -5.917  | 3.348  |
| POOLED      | validate | 446     | 63         | -1.272       | -7.809  | 5.661  |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 475   |
| stop        | 347   |
| hold        | 249   |
| curfew      | 200   |
| mixed       | 16    |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|----------------|---------|------------|--------------|---------|---------|
| base           | 1287    | 187        | -1.261       | -5.051  | 2.524   |
| drop_top5      | 1249    | 182        | -3.26        | -6.734  | 0.225   |
| double_spread  | 1287    | 187        | -2.051       | -5.931  | 1.904   |
| double_latency | 1287    | 187        | -0.428       | -4.231  | 3.519   |
| post_promo     | 1287    | 187        | -15.261      | -19.051 | -11.476 |

Concentration:

```
{
  "n_plans": 1287,
  "n_sessions": 187,
  "total_net_bps": -1622.3380484128197,
  "top5_session_share": -1.5095483855122693,
  "top_symbol_share": -0.7606834570645281,
  "top_payer_share": -0.09212147330349683,
  "effective_n": 0.41485175480142295
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -1.003,
  "latency_drag_bps": -0.833,
  "spread_cost_bps": 0.79,
  "fees_bps": 0.3,
  "net_bps": -1.261
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
