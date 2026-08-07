# A0 trial report — M3-A0-googl-h13

Pooled plan-results rows: 483  (taken=371)
Sessions: 163
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 11       | 8     | 3         | 0        | 0    |
| gap_mr      | 25       | 25    | 0         | 0        | 0    |
| letf_window | 98       | 83    | 15        | 0        | 0    |
| vwap_magnet | 349      | 255   | 65        | 28       | 1    |
| TOTAL       | 483      | 371   | 83        | 28       | 1    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|-------------|----------|---------|------------|--------------|---------|--------|
| expiry_pin  | train    | 5       | 4          | 7.935        | 5.404   | 12.888 |
| expiry_pin  | validate | 3       | 2          | 9.499        | -16.453 | 22.475 |
| gap_mr      | train    | 16      | 16         | -16.83       | -70.142 | 34.804 |
| gap_mr      | validate | 9       | 9          | 27.91        | -28.662 | 80.218 |
| letf_window | train    | 56      | 56         | -7.353       | -15.193 | 0.926  |
| letf_window | validate | 27      | 27         | 7.023        | -6.231  | 21.459 |
| vwap_magnet | train    | 170     | 75         | -2.789       | -8.337  | 2.759  |
| vwap_magnet | validate | 85      | 44         | -2.411       | -10.64  | 5.085  |
| POOLED      | train    | 247     | 106        | -4.516       | -10.115 | 0.655  |
| POOLED      | validate | 124     | 54         | 2.132        | -6.098  | 9.641  |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 123   |
| stop        | 101   |
| hold        | 72    |
| curfew      | 72    |
| mixed       | 3     |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|----------------|---------|------------|--------------|---------|---------|
| base           | 371     | 160        | -2.294       | -6.664  | 1.948   |
| drop_top5      | 359     | 155        | -4.541       | -8.59   | -0.633  |
| double_spread  | 371     | 160        | -3.463       | -8.118  | 0.978   |
| double_latency | 371     | 160        | -1.74        | -6.174  | 2.489   |
| post_promo     | 371     | 160        | -16.294      | -20.664 | -12.052 |

Concentration:

```
{
  "n_plans": 371,
  "n_sessions": 160,
  "total_net_bps": -851.160038083172,
  "top5_session_share": -0.9153734198708829,
  "top_symbol_share": 0.9999999999999991,
  "top_payer_share": -0.08009305141733918,
  "effective_n": 1.0450884766461737
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -1.38,
  "latency_drag_bps": -0.554,
  "spread_cost_bps": 1.168,
  "fees_bps": 0.3,
  "net_bps": -2.294
}
```

## 6. Cost table (deterministic fallback, no network)

```
{
  "GOOGL": {
    "spread_bps": 1.5,
    "sec_taf_sell_bps": 0.3,
    "slippage_market_bps": 0.5,
    "commission_usd": 0.0,
    "rt_cost_bps": 2.3,
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
  "symbol_sessions_seen": 187,
  "symbol_sessions_ok": 187,
  "skip_counts": {
    "no_context": 0,
    "no_event_bars": 0,
    "no_quote": 0
  },
  "state_counts": {
    "gap_mr": 25,
    "letf_window": 98,
    "vwap_magnet": 350,
    "cascade": 0,
    "expiry_pin": 14
  },
  "plans_authored": 483,
  "symbols": [
    "GOOGL"
  ]
}
```
