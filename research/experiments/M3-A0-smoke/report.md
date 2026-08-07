# A0 trial report — M3-A0-smoke

Pooled plan-results rows: 59  (taken=48)
Sessions: 11
Splits present: ['validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 4        | 2     | 2         | 0        | 0    |
| letf_window | 17       | 15    | 2         | 0        | 0    |
| vwap_magnet | 38       | 31    | 7         | 0        | 0    |
| TOTAL       | 59       | 48    | 11        | 0        | 0    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|-------------|----------|---------|------------|--------------|---------|---------|
| expiry_pin  | train    | 0       | 0          | null         | null    | null    |
| expiry_pin  | validate | 2       | 1          | -20.408      | -20.408 | -20.408 |
| letf_window | train    | 0       | 0          | null         | null    | null    |
| letf_window | validate | 15      | 10         | -16.655      | -32.59  | -1.147  |
| vwap_magnet | train    | 0       | 0          | null         | null    | null    |
| vwap_magnet | validate | 31      | 10         | -7.758       | -31.845 | 15.224  |
| POOLED      | train    | 0       | 0          | null         | null    | null    |
| POOLED      | validate | 48      | 11         | -11.065      | -28.756 | 4.208   |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 15    |
| stop        | 14    |
| curfew      | 13    |
| hold        | 6     |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------------|---------|------------|--------------|---------|--------|
| base           | 48      | 11         | -11.065      | -28.756 | 4.208  |
| drop_top5      | 30      | 6          | -25.158      | -50.954 | -6.633 |
| double_spread  | 48      | 11         | -6.128       | -25.939 | 11.879 |
| double_latency | 48      | 11         | -12.028      | -29.306 | 3.035  |
| post_promo     | 48      | 11         | -25.065      | -42.756 | -9.792 |

Concentration:

```
{
  "n_plans": 48,
  "n_sessions": 11,
  "total_net_bps": -531.1362134808303,
  "top5_session_share": -0.42099047840153064,
  "top_symbol_share": 0.1745089280650327,
  "top_payer_share": 0.07684579057286288,
  "effective_n": 1.3826901954973434
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -14.74,
  "latency_drag_bps": 0.962,
  "spread_cost_bps": -4.937,
  "fees_bps": 0.3,
  "net_bps": -11.065
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
  "sessions_in_range": 11,
  "symbol_sessions_seen": 22,
  "symbol_sessions_ok": 22,
  "skip_counts": {
    "no_context": 0,
    "no_event_bars": 0,
    "no_quote": 0
  },
  "state_counts": {
    "gap_mr": 0,
    "letf_window": 17,
    "vwap_magnet": 38,
    "cascade": 0,
    "expiry_pin": 5
  },
  "plans_authored": 59,
  "symbols": [
    "NVDA",
    "TSLA"
  ]
}
```
