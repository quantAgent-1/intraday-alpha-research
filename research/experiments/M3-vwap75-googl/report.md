# A0 trial report — M3-vwap75-googl

Pooled plan-results rows: 483  (taken=396)
Sessions: 163
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 11       | 9     | 2         | 0        | 0    |
| gap_mr      | 25       | 25    | 0         | 0        | 0    |
| letf_window | 98       | 92    | 6         | 0        | 0    |
| vwap_magnet | 349      | 270   | 54        | 24       | 1    |
| TOTAL       | 483      | 396   | 62        | 24       | 1    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|-------------|----------|---------|------------|--------------|---------|--------|
| expiry_pin  | train    | 6       | 4          | 9.218        | 6.363   | 13.037 |
| expiry_pin  | validate | 3       | 2          | 9.499        | -16.453 | 22.475 |
| gap_mr      | train    | 16      | 16         | -8.896       | -65.193 | 46.643 |
| gap_mr      | validate | 9       | 9          | 27.91        | -28.662 | 80.218 |
| letf_window | train    | 62      | 62         | -4.124       | -12.043 | 4.128  |
| letf_window | validate | 30      | 30         | 6.857        | -6.27   | 19.876 |
| vwap_magnet | train    | 179     | 75         | 2.523        | -2.172  | 7.512  |
| vwap_magnet | validate | 91      | 44         | 2.547        | -5.502  | 10.092 |
| POOLED      | train    | 263     | 106        | 0.414        | -4.913  | 5.422  |
| POOLED      | validate | 133     | 54         | 5.392        | -2.19   | 12.629 |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 149   |
| stop        | 93    |
| curfew      | 77    |
| hold        | 75    |
| mixed       | 2     |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo  | ci_hi  |
|----------------|---------|------------|--------------|--------|--------|
| base           | 396     | 160        | 2.086        | -2.11  | 6.333  |
| drop_top5      | 380     | 155        | -0.225       | -4.098 | 3.516  |
| double_spread  | 396     | 160        | 3.903        | -0.912 | 8.837  |
| double_latency | 396     | 160        | 2.827        | -1.34  | 6.946  |
| post_promo     | 396     | 160        | -11.914      | -16.11 | -7.667 |

Concentration:

```
{
  "n_plans": 396,
  "n_sessions": 160,
  "total_net_bps": 826.0205547600041,
  "top5_session_share": 1.1033539502411398,
  "top_symbol_share": 1.0,
  "top_payer_share": 0.8272732199154221,
  "effective_n": 0.930688304127571
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -0.173,
  "latency_drag_bps": -0.741,
  "spread_cost_bps": -1.817,
  "fees_bps": 0.3,
  "net_bps": 2.086
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
