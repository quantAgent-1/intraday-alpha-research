# A0 trial report — M3-A0-v1.1-ext2024-MU

Pooled plan-results rows: 808  (taken=673)
Sessions: 361
Splits present: ['train']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 7        | 5     | 0         | 2        | 0    |
| gap_mr      | 46       | 46    | 0         | 0        | 0    |
| letf_window | 284      | 259   | 25        | 0        | 0    |
| vwap_magnet | 471      | 363   | 70        | 38       | 0    |
| TOTAL       | 808      | 673   | 95        | 40       | 0    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|-------------|----------|---------|------------|--------------|---------|--------|
| expiry_pin  | train    | 5       | 4          | 5.22         | -7.476  | 17.919 |
| expiry_pin  | validate | 0       | 0          | null         | null    | null   |
| gap_mr      | train    | 46      | 46         | -1.678       | -44.928 | 38.935 |
| gap_mr      | validate | 0       | 0          | null         | null    | null   |
| letf_window | train    | 259     | 259        | -5.506       | -12.554 | 1.921  |
| letf_window | validate | 0       | 0          | null         | null    | null   |
| vwap_magnet | train    | 363     | 193        | 0.899        | -4.295  | 5.857  |
| vwap_magnet | validate | 0       | 0          | null         | null    | null   |
| POOLED      | train    | 673     | 359        | -1.71        | -7.019  | 3.43   |
| POOLED      | validate | 0       | 0          | null         | null    | null   |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| curfew      | 207   |
| stop        | 203   |
| targets     | 157   |
| hold        | 96    |
| mixed       | 10    |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------------|---------|------------|--------------|---------|--------|
| base           | 673     | 359        | -1.71        | -7.019  | 3.43   |
| drop_top5      | 662     | 354        | -4.628       | -9.219  | -0.486 |
| double_spread  | 673     | 359        | -1.904       | -7.241  | 3.405  |
| double_latency | 673     | 359        | -1.733       | -7.062  | 3.356  |
| post_promo     | 673     | 359        | -15.71       | -21.019 | -10.57 |

Concentration:

```
{
  "n_plans": 673,
  "n_sessions": 359,
  "total_net_bps": -1150.9329098938395,
  "top5_session_share": -1.6621488362627406,
  "top_symbol_share": 0.999999999999999,
  "top_payer_share": -0.28348358568859966,
  "effective_n": 0.4162744557730274
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -1.193,
  "latency_drag_bps": 0.023,
  "spread_cost_bps": 0.194,
  "fees_bps": 0.3,
  "net_bps": -1.71
}
```

## 6. Cost table (deterministic fallback, no network)

```
{
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
  "sessions_in_range": 417,
  "symbol_sessions_seen": 417,
  "symbol_sessions_ok": 417,
  "skip_counts": {
    "no_context": 0,
    "no_event_bars": 0,
    "no_quote": 0
  },
  "state_counts": {
    "gap_mr": 52,
    "letf_window": 295,
    "vwap_magnet": 835,
    "cascade": 0,
    "expiry_pin": 24
  },
  "plans_authored": 808,
  "symbols": [
    "MU"
  ]
}
```
