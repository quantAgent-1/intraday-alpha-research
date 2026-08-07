# A0 trial report — M3-A0-ext-googl-h12

Pooled plan-results rows: 483  (taken=391)
Sessions: 163
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 11       | 9     | 2         | 0        | 0    |
| gap_mr      | 25       | 25    | 0         | 0        | 0    |
| letf_window | 98       | 89    | 9         | 0        | 0    |
| vwap_magnet | 349      | 268   | 56        | 24       | 1    |
| TOTAL       | 483      | 391   | 67        | 24       | 1    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|-------------|----------|---------|------------|--------------|---------|--------|
| expiry_pin  | train    | 6       | 4          | 9.218        | 6.363   | 13.037 |
| expiry_pin  | validate | 3       | 2          | 9.499        | -16.453 | 22.475 |
| gap_mr      | train    | 16      | 16         | -8.896       | -65.193 | 46.643 |
| gap_mr      | validate | 9       | 9          | 27.91        | -28.662 | 80.218 |
| letf_window | train    | 61      | 61         | -4.446       | -12.611 | 4.075  |
| letf_window | validate | 28      | 28         | 6.737        | -7.358  | 21.317 |
| vwap_magnet | train    | 178     | 75         | 3.035        | -2.088  | 8.237  |
| vwap_magnet | validate | 90      | 44         | 1.47         | -6.846  | 9.227  |
| POOLED      | train    | 261     | 106        | 0.697        | -4.958  | 5.876  |
| POOLED      | validate | 130     | 54         | 4.62         | -3.292  | 12.018 |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 152   |
| stop        | 96    |
| curfew      | 77    |
| hold        | 64    |
| mixed       | 2     |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------------|---------|------------|--------------|---------|--------|
| base           | 391     | 160        | 2.002        | -2.513  | 6.356  |
| drop_top5      | 375     | 155        | -0.343       | -4.418  | 3.629  |
| double_spread  | 391     | 160        | 3.85         | -1.303  | 8.83   |
| double_latency | 391     | 160        | 2.746        | -1.691  | 7.058  |
| post_promo     | 391     | 160        | -11.998      | -16.513 | -7.644 |

Concentration:

```
{
  "n_plans": 391,
  "n_sessions": 160,
  "total_net_bps": 782.6282987929563,
  "top5_session_share": 1.1645286063390055,
  "top_symbol_share": 1.0000000000000002,
  "top_payer_share": 0.8592928266590052,
  "effective_n": 0.7909288557915325
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -0.292,
  "latency_drag_bps": -0.745,
  "spread_cost_bps": -1.849,
  "fees_bps": 0.3,
  "net_bps": 2.002
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
