# A0 trial report — M3-A0-v1.1-4sym

Pooled plan-results rows: 2187  (taken=1448)
Sessions: 187
Splits present: ['train', 'validate']

## 1. Authored / taken / not_taken / unfilled / void — per payer

| payer       | authored | taken | not_taken | unfilled | void |
|-------------|----------|-------|-----------|----------|------|
| expiry_pin  | 75       | 45    | 30        | 0        | 0    |
| gap_mr      | 70       | 68    | 2         | 0        | 0    |
| letf_window | 484      | 306   | 178       | 0        | 0    |
| vwap_magnet | 1558     | 1029  | 417       | 110      | 2    |
| TOTAL       | 2187     | 1448  | 627       | 110      | 2    |

## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)

train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.

| payer       | split    | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi   |
|-------------|----------|---------|------------|--------------|---------|---------|
| expiry_pin  | train    | 28      | 6          | 1.511        | -9.653  | 14.257  |
| expiry_pin  | validate | 17      | 3          | -7.559       | -26.849 | 6.188   |
| gap_mr      | train    | 45      | 36         | 9.037        | -35.882 | 54.37   |
| gap_mr      | validate | 23      | 17         | 18.133       | -88.489 | 105.485 |
| letf_window | train    | 196     | 83         | 1.101        | -11.926 | 13.538  |
| letf_window | validate | 110     | 49         | -8.069       | -28.111 | 10.789  |
| vwap_magnet | train    | 682     | 118        | 5.291        | 0.742   | 9.531   |
| vwap_magnet | validate | 347     | 60         | 4.608        | -2.254  | 11.62   |
| POOLED      | train    | 951     | 124        | 4.494        | 0.062   | 9.139   |
| POOLED      | validate | 497     | 63         | 2.012        | -6.132  | 9.889   |

## 3. Exit-reason distribution (taken)

| exit_reason | count |
|-------------|-------|
| targets     | 577   |
| stop        | 334   |
| curfew      | 284   |
| hold        | 236   |
| mixed       | 17    |

## 4. Stress battery on the pooled taken frame (stress.stress_report)

| arm            | n_plans | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------------|---------|------------|--------------|---------|--------|
| base           | 1448    | 187        | 3.642        | -0.686  | 7.85   |
| drop_top5      | 1404    | 182        | 1.502        | -2.306  | 5.286  |
| double_spread  | 1448    | 187        | 6.957        | 2.348   | 11.589 |
| double_latency | 1448    | 187        | 3.915        | -0.479  | 8.253  |
| post_promo     | 1448    | 187        | -10.358      | -14.686 | -6.15  |

Concentration:

```
{
  "n_plans": 1448,
  "n_sessions": 187,
  "total_net_bps": 5273.23006023515,
  "top5_session_share": 0.600180870139366,
  "top_symbol_share": 0.4652330494218587,
  "top_payer_share": 0.9875138916282993,
  "effective_n": 2.8290834410779873
}
```

## 5. Decomposition means (taken; bps on entry notional)

```
{
  "gross_mid_bps": 0.354,
  "latency_drag_bps": -0.273,
  "spread_cost_bps": -3.315,
  "fees_bps": 0.3,
  "net_bps": 3.642
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
  },
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
  "symbol_sessions_seen": 748,
  "symbol_sessions_ok": 744,
  "skip_counts": {
    "no_context": 0,
    "no_event_bars": 4,
    "no_quote": 0
  },
  "state_counts": {
    "gap_mr": 71,
    "letf_window": 484,
    "vwap_magnet": 1558,
    "cascade": 0,
    "expiry_pin": 80
  },
  "plans_authored": 2187,
  "symbols": [
    "NVDA",
    "TSLA",
    "AMD",
    "MU"
  ]
}
```
