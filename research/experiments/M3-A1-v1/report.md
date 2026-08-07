# A0 trial report — M3-A1-v1

Pooled plan-results rows: 493  (taken=386)
Sessions: 159
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 17       | 13    | 4         | 0        | 0    |
| gap_mr      | 29       | 29    | 0         | 0        | 0    |
| letf_window | 107      | 99    | 8         | 0        | 0    |
| vwap_magnet | 340      | 245   | 73        | 22       | 0    |
| TOTAL       | 493      | 386   | 85        | 22       | 0    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|-------------|----------|---------|------------|--------------|---------|---------|
| expiry_pin  | train    | 10      | 6          | 22.839       | -5.488  | 49.428  |
| expiry_pin  | validate | 3       | 3          | 37.162       | 31.75   | 47.117  |
| gap_mr      | train    | 20      | 19         | 17.173       | -25.61  | 67.786  |
| gap_mr      | validate | 9       | 7          | 38.258       | -37.297 | 107.765 |
| letf_window | train    | 60      | 38         | -18.869      | -36.773 | 0.983   |
| letf_window | validate | 39      | 33         | -13.461      | -32.003 | 4.237   |
| vwap_magnet | train    | 176     | 79         | 9.519        | 0.005   | 19.292  |
| vwap_magnet | validate | 69      | 35         | -0.214       | -18.091 | 16.44   |
| POOLED      | train    | 266     | 101        | 4.192        | -4.794  | 12.735  |
| POOLED      | validate | 120     | 55         | -0.699       | -12.81  | 12.427  |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 115   |
| hold        | 112   |
| curfew      | 92    |
| stop        | 60    |
| mixed       | 7     |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------------|---------|------------|--------------|---------|--------|
| base           | 386     | 156        | 2.671        | -4.755  | 9.535  |
| drop_top5      | 370     | 151        | -1.236       | -7.782  | 5.045  |
| double_spread  | 386     | 156        | 8.248        | -0.303  | 16.548 |
| double_latency | 386     | 156        | 4.045        | -3.225  | 10.867 |
| post_promo     | 386     | 156        | -11.329      | -18.755 | -4.465 |

Concentration:

```
{
  "n_plans": 386,
  "n_sessions": 156,
  "total_net_bps": 1031.081212569035,
  "top5_session_share": 1.4434235362358725,
  "top_symbol_share": 1.5872067962909016,
  "top_payer_share": 1.6104683866111744,
  "effective_n": 0.5259475537747551
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -3.979,
  "latency_drag_bps": -1.374,
  "spread_cost_bps": -5.576,
  "fees_bps": 0.3,
  "net_bps": 2.671
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
  "arm": "a1",
  "preds_dir": "data/preds/a1_v1",
  "overlay_counts": {
    "kept": 464,
    "vetoed": 541,
    "no_pred": 29
  },
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
  "plans_authored": 493,
  "symbols": [
    "NVDA",
    "TSLA"
  ]
}
```
