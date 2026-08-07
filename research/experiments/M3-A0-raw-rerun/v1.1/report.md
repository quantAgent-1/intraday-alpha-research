# A0 trial report — M3-A0-raw-rerun/v1.1

Pooled plan-results rows: 1035  (taken=803)
Sessions: 185
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 40       | 26    | 11        | 3        | 0    |
| gap_mr      | 29       | 29    | 0         | 0        | 0    |
| letf_window | 226      | 197   | 29        | 0        | 0    |
| vwap_magnet | 740      | 551   | 129       | 59       | 1    |
| TOTAL       | 1035     | 803   | 169       | 62       | 1    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|-------------|----------|---------|------------|--------------|---------|--------|
| expiry_pin  | train    | 16      | 6          | 12.455       | 4.386   | 17.024 |
| expiry_pin  | validate | 10      | 3          | -4.541       | -22.382 | 0.32   |
| gap_mr      | train    | 20      | 19         | 4.767        | -41.756 | 57.945 |
| gap_mr      | validate | 9       | 7          | 21.752       | -65.438 | 83.139 |
| letf_window | train    | 128     | 86         | -6.086       | -16.329 | 5.007  |
| letf_window | validate | 69      | 49         | -5.279       | -18.216 | 6.895  |
| vwap_magnet | train    | 379     | 109        | -3.553       | -8.292  | 0.817  |
| vwap_magnet | validate | 172     | 54         | -2.859       | -10.781 | 4.35   |
| POOLED      | train    | 543     | 121        | -3.372       | -7.838  | 1.166  |
| POOLED      | validate | 260     | 63         | -2.714       | -9.429  | 3.624  |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 283   |
| stop        | 211   |
| curfew      | 179   |
| hold        | 122   |
| mixed       | 8     |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|----------------|---------|------------|--------------|---------|---------|
| base           | 803     | 184        | -3.159       | -6.948  | 0.547   |
| drop_top5      | 782     | 179        | -4.762       | -8.194  | -1.411  |
| double_spread  | 803     | 184        | -5.3         | -9.044  | -1.576  |
| double_latency | 803     | 184        | -6.046       | -9.827  | -2.232  |
| post_promo     | 803     | 184        | -17.159      | -20.948 | -13.453 |

Concentration:

```
{
  "n_plans": 803,
  "n_sessions": 184,
  "total_net_bps": -2536.7152033207976,
  "top5_session_share": -0.46801269657931976,
  "top_symbol_share": 0.1391083534753265,
  "top_payer_share": -0.11475545791473922,
  "effective_n": 2.7617488081981
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -2.239,
  "latency_drag_bps": -0.402,
  "spread_cost_bps": 1.022,
  "fees_bps": 0.3,
  "net_bps": -3.159
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
  "arm": "a0",
  "preds_dir": null,
  "overlay_counts": null,
  "m4_mode": null,
  "p_skip": null,
  "drop_counts": null,
  "entry_gate": false,
  "gate_counts": null,
  "sessions_in_range": 187,
  "symbol_sessions_seen": 374,
  "symbol_sessions_ok": 370,
  "skip_counts": {
    "no_context": 0,
    "no_event_bars": 4,
    "no_quote": 0
  },
  "state_counts": {
    "gap_mr": 30,
    "letf_window": 226,
    "vwap_magnet": 740,
    "cascade": 0,
    "expiry_pin": 43
  },
  "plans_authored": 1035,
  "symbols": [
    "NVDA",
    "TSLA"
  ]
}
```
