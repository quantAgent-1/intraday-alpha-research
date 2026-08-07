# A0 trial report — M4-tst-legs

Pooled plan-results rows: 668  (taken=551)
Sessions: 124
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 26       | 21    | 5         | 0        | 0    |
| gap_mr      | 15       | 15    | 0         | 0        | 0    |
| letf_window | 153      | 142   | 11        | 0        | 0    |
| vwap_magnet | 474      | 373   | 61        | 39       | 1    |
| TOTAL       | 668      | 551   | 77        | 39       | 1    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|-------------|----------|---------|------------|--------------|---------|---------|
| expiry_pin  | train    | 11      | 3          | 16.267       | 13.341  | 24.036  |
| expiry_pin  | validate | 10      | 3          | -3.173       | -22.974 | 22.462  |
| gap_mr      | train    | 6       | 6          | -22.736      | -92.487 | 40.672  |
| gap_mr      | validate | 9       | 7          | 37.288       | -39.862 | 107.445 |
| letf_window | train    | 70      | 42         | -6.431       | -16.291 | 3.653   |
| letf_window | validate | 72      | 52         | -6.887       | -18.268 | 4.268   |
| vwap_magnet | train    | 187     | 52         | 8.078        | 2.747   | 13.37   |
| vwap_magnet | validate | 186     | 54         | 2.796        | -3.1    | 7.866   |
| POOLED      | train    | 274     | 60         | 4.026        | -0.598  | 8.374   |
| POOLED      | validate | 277     | 63         | 1.184        | -4.338  | 6.897   |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 279   |
| curfew      | 126   |
| stop        | 97    |
| hold        | 46    |
| mixed       | 3     |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------------|---------|------------|--------------|---------|--------|
| base           | 551     | 123        | 2.597        | -1.105  | 6.355  |
| drop_top5      | 524     | 118        | 0.785        | -2.532  | 3.876  |
| double_spread  | 551     | 123        | 5.881        | 1.751   | 9.963  |
| double_latency | 551     | 123        | 3.258        | -0.631  | 7.283  |
| post_promo     | 551     | 123        | -11.403      | -15.105 | -7.645 |

Concentration:

```
{
  "n_plans": 551,
  "n_sessions": 123,
  "total_net_bps": 1430.9618963908988,
  "top5_session_share": 0.7124545220136574,
  "top_symbol_share": 0.8354504271713118,
  "top_payer_share": 1.4190468471549247,
  "effective_n": 1.951962717279971
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -1.049,
  "latency_drag_bps": -0.661,
  "spread_cost_bps": -3.284,
  "fees_bps": 0.3,
  "net_bps": 2.597
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
  "arm": "m4",
  "preds_dir": "data/preds/m4_v1_tst",
  "overlay_counts": {
    "kept": 544,
    "vetoed": 0,
    "no_pred": 124
  },
  "m4_mode": "legs",
  "p_skip": 0.45,
  "drop_counts": {},
  "sessions_in_range": 124,
  "symbol_sessions_seen": 248,
  "symbol_sessions_ok": 244,
  "skip_counts": {
    "no_context": 0,
    "no_event_bars": 4,
    "no_quote": 0
  },
  "state_counts": {
    "gap_mr": 15,
    "letf_window": 153,
    "vwap_magnet": 474,
    "cascade": 0,
    "expiry_pin": 30
  },
  "plans_authored": 668,
  "symbols": [
    "NVDA",
    "TSLA"
  ]
}
```
