# A0 trial report — M3-A0-raw-rerun/ext2024-MU

Pooled plan-results rows: 1202  (taken=902)
Sessions: 400
Splits present: ['train']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 22       | 11    | 6         | 5        | 0    |
| gap_mr      | 49       | 49    | 0         | 0        | 0    |
| letf_window | 295      | 253   | 42        | 0        | 0    |
| vwap_magnet | 836      | 589   | 157       | 90       | 0    |
| TOTAL       | 1202     | 902   | 205       | 95       | 0    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|-------------|----------|---------|------------|--------------|---------|--------|
| expiry_pin  | train    | 11      | 10         | -9.866       | -33.15  | 10.266 |
| expiry_pin  | validate | 0       | 0          | null         | null    | null   |
| gap_mr      | train    | 49      | 49         | -6.58        | -46.004 | 32.133 |
| gap_mr      | validate | 0       | 0          | null         | null    | null   |
| letf_window | train    | 253     | 253        | -4.932       | -12.455 | 3.145  |
| letf_window | validate | 0       | 0          | null         | null    | null   |
| vwap_magnet | train    | 589     | 272        | -1.38        | -5.631  | 3.109  |
| vwap_magnet | validate | 0       | 0          | null         | null    | null   |
| POOLED      | train    | 902     | 399        | -2.762       | -7.091  | 1.493  |
| POOLED      | validate | 0       | 0          | null         | null    | null   |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 257   |
| curfew      | 241   |
| stop        | 219   |
| hold        | 170   |
| mixed       | 15    |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|----------------|---------|------------|--------------|---------|---------|
| base           | 902     | 399        | -2.762       | -7.091  | 1.493   |
| drop_top5      | 890     | 394        | -5.255       | -8.955  | -1.63   |
| double_spread  | 902     | 399        | -5.613       | -9.91   | -1.396  |
| double_latency | 902     | 399        | -5.983       | -10.312 | -1.696  |
| post_promo     | 902     | 399        | -16.762      | -21.091 | -12.507 |

Concentration:

```
{
  "n_plans": 902,
  "n_sessions": 399,
  "total_net_bps": -2491.7292155749155,
  "top5_session_share": -0.8770870536205126,
  "top_symbol_share": 1.0000000000000007,
  "top_payer_share": 0.04355656176577689,
  "effective_n": 1.5896690726381273
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": -1.77,
  "latency_drag_bps": -0.734,
  "spread_cost_bps": 1.426,
  "fees_bps": 0.3,
  "net_bps": -2.762
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
  "entry_gate": false,
  "gate_counts": null,
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
    "vwap_magnet": 836,
    "cascade": 0,
    "expiry_pin": 24
  },
  "plans_authored": 1202,
  "symbols": [
    "MU"
  ]
}
```
