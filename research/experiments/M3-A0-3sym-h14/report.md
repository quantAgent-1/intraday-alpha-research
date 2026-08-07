# A0 trial report — M3-A0-3sym-h14

Pooled plan-results rows: 1636  (taken=1078)
Sessions: 187
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 45       | 28    | 17        | 0        | 0    |
| gap_mr      | 66       | 64    | 2         | 0        | 0    |
| letf_window | 356      | 208   | 148       | 0        | 0    |
| vwap_magnet | 1169     | 778   | 278       | 111      | 2    |
| TOTAL       | 1636     | 1078  | 445       | 111      | 2    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|-------------|----------|---------|------------|--------------|---------|--------|
| expiry_pin  | train    | 13      | 5          | -7.702       | -32.872 | 9.946  |
| expiry_pin  | validate | 15      | 3          | -14.658      | -42.92  | 20.82  |
| gap_mr      | train    | 41      | 32         | -11.044      | -56.74  | 33.01  |
| gap_mr      | validate | 23      | 18         | 13.806       | -81.288 | 97.949 |
| letf_window | train    | 132     | 83         | 7.208        | -6.913  | 21.96  |
| letf_window | validate | 76      | 50         | -7.206       | -30.032 | 16.96  |
| vwap_magnet | train    | 505     | 114        | -2.284       | -6.746  | 2.225  |
| vwap_magnet | validate | 273     | 60         | -2.335       | -10.141 | 5.678  |
| POOLED      | train    | 691     | 124        | -1.093       | -6.074  | 3.782  |
| POOLED      | validate | 387     | 63         | -2.81        | -11.616 | 6.293  |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 368   |
| stop        | 290   |
| hold        | 215   |
| curfew      | 194   |
| mixed       | 11    |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|----------------|---------|------------|--------------|---------|---------|
| base           | 1078    | 187        | -1.709       | -6.049  | 2.889   |
| drop_top5      | 1044    | 182        | -4.318       | -8.166  | -0.271  |
| double_spread  | 1078    | 187        | -2.937       | -7.215  | 1.786   |
| double_latency | 1078    | 187        | -1.064       | -5.469  | 3.64    |
| post_promo     | 1078    | 187        | -15.709      | -20.049 | -11.111 |

Concentration:

```
{
  "n_plans": 1078,
  "n_sessions": 187,
  "total_net_bps": -1842.4453378586127,
  "top5_session_share": -1.4468765806514041,
  "top_symbol_share": 0.0017638731057141306,
  "top_payer_share": -0.2191110741398369,
  "effective_n": 0.5365871769993177
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -0.826,
  "latency_drag_bps": -0.645,
  "spread_cost_bps": 1.228,
  "fees_bps": 0.3,
  "net_bps": -1.709
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
  "plans_authored": 1636,
  "symbols": [
    "AMD",
    "MU",
    "GOOGL"
  ]
}
```
