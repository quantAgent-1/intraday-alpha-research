# A0 trial report — M3-H2-v1-3sym

Pooled plan-results rows: 1337  (taken=938)
Sessions: 187
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 38       | 23    | 14        | 1        | 0    |
| gap_mr      | 49       | 48    | 1         | 0        | 0    |
| letf_window | 303      | 201   | 102       | 0        | 0    |
| vwap_magnet | 947      | 666   | 183       | 96       | 2    |
| TOTAL       | 1337     | 938   | 300       | 97       | 2    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|-------------|----------|---------|------------|--------------|---------|--------|
| expiry_pin  | train    | 10      | 5          | -5.327       | -23.584 | 11.898 |
| expiry_pin  | validate | 13      | 3          | -7.378       | -25.382 | 20.82  |
| gap_mr      | train    | 28      | 23         | -16.865      | -79.532 | 39.041 |
| gap_mr      | validate | 20      | 16         | -0.879       | -95.665 | 94.516 |
| letf_window | train    | 128     | 83         | 11.175       | -2.935  | 25.488 |
| letf_window | validate | 73      | 48         | -7.959       | -30.865 | 16.576 |
| vwap_magnet | train    | 440     | 110        | -2.69        | -7.984  | 2.144  |
| vwap_magnet | validate | 226     | 60         | -1.639       | -10.263 | 7.05   |
| POOLED      | train    | 606     | 123        | -0.46        | -5.796  | 4.962  |
| POOLED      | validate | 332     | 63         | -3.207       | -13.677 | 7.304  |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 313   |
| stop        | 237   |
| curfew      | 192   |
| hold        | 189   |
| mixed       | 7     |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|----------------|---------|------------|--------------|---------|---------|
| base           | 938     | 186        | -1.432       | -6.505  | 3.567   |
| drop_top5      | 904     | 181        | -4.339       | -8.511  | 0.271   |
| double_spread  | 938     | 186        | -2.719       | -7.953  | 2.396   |
| double_latency | 938     | 186        | -0.635       | -5.972  | 4.495   |
| post_promo     | 938     | 186        | -15.432      | -20.505 | -10.433 |

Concentration:

```
{
  "n_plans": 938,
  "n_sessions": 186,
  "total_net_bps": -1343.516618604766,
  "top5_session_share": -1.9192448698384348,
  "top_symbol_share": 0.04273242151856724,
  "top_payer_share": -0.6322088923867195,
  "effective_n": 0.30354319797085577
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -0.643,
  "latency_drag_bps": -0.798,
  "spread_cost_bps": 1.287,
  "fees_bps": 0.3,
  "net_bps": -1.432
}
```

## 6. Cost table (deterministic fallback, no network)

```
{
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
  },
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
  "entry_gate": true,
  "gate_counts": {
    "allowed": 1337,
    "gated": 299,
    "no_features": 0
  },
  "sessions_in_range": 187,
  "symbol_sessions_seen": 561,
  "symbol_sessions_ok": 561,
  "skip_counts": {
    "no_context": 0,
    "no_event_bars": 0,
    "no_quote": 0
  },
  "state_counts": {
    "gap_mr": 66,
    "letf_window": 356,
    "vwap_magnet": 1170,
    "cascade": 0,
    "expiry_pin": 49
  },
  "plans_authored": 1337,
  "symbols": [
    "AMD",
    "MU",
    "GOOGL"
  ]
}
```
