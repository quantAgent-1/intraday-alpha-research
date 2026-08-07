# A0 trial report — M3-A0-v1

Pooled plan-results rows: 1034  (taken=857)
Sessions: 185
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 41       | 31    | 10        | 0        | 0    |
| gap_mr      | 29       | 29    | 0         | 0        | 0    |
| letf_window | 226      | 202   | 24        | 0        | 0    |
| vwap_magnet | 738      | 595   | 104       | 38       | 1    |
| TOTAL       | 1034     | 857   | 138       | 38       | 1    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|-------------|----------|---------|------------|--------------|---------|---------|
| expiry_pin  | train    | 21      | 6          | 11.37        | 5.191   | 20.268  |
| expiry_pin  | validate | 10      | 3          | 13.267       | -22.382 | 24.382  |
| gap_mr      | train    | 20      | 19         | 30.334       | -16.369 | 79.737  |
| gap_mr      | validate | 9       | 7          | 53.097       | -20.888 | 114.077 |
| letf_window | train    | 132     | 86         | -5.579       | -15.856 | 5.18    |
| letf_window | validate | 70      | 48         | -3.875       | -17.238 | 8.242   |
| vwap_magnet | train    | 412     | 108        | 13.027       | 8.242   | 17.625  |
| vwap_magnet | validate | 183     | 55         | 14.849       | 6.484   | 22.529  |
| POOLED      | train    | 585     | 121        | 9.361        | 4.909   | 13.646  |
| POOLED      | validate | 272     | 63         | 11.238       | 4.285   | 17.72   |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 412   |
| curfew      | 184   |
| stop        | 161   |
| hold        | 92    |
| mixed       | 8     |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo  | ci_hi  |
|----------------|---------|------------|--------------|--------|--------|
| base           | 857     | 184        | 9.956        | 5.962  | 13.66  |
| drop_top5      | 827     | 179        | 8.256        | 4.696  | 11.799 |
| double_spread  | 857     | 184        | 20.469       | 15.129 | 25.462 |
| double_latency | 857     | 184        | 10.226       | 6.201  | 13.957 |
| post_promo     | 857     | 184        | -4.044       | -8.038 | -0.34  |

Concentration:

```
{
  "n_plans": 857,
  "n_sessions": 184,
  "total_net_bps": 8532.692901122111,
  "top5_session_share": 0.19979702914658315,
  "top_symbol_share": 0.6800796413942628,
  "top_payer_share": 0.9474595905204556,
  "effective_n": 21.89361564361871
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -0.525,
  "latency_drag_bps": -0.269,
  "spread_cost_bps": -10.513,
  "fees_bps": 0.3,
  "net_bps": 9.956
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
    "vwap_magnet": 738,
    "cascade": 0,
    "expiry_pin": 45
  },
  "plans_authored": 1034,
  "symbols": [
    "NVDA",
    "TSLA"
  ]
}
```
