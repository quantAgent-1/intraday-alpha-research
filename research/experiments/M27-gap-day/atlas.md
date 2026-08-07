# M27 gap-day reversion atlas -- M27-gap-day

Family `gap_day_reversion_v1` (registered 2026-07-23, M3_REGISTRATION.md section M27). ONE pooled look over the purchased window (2023-08-01..2026-05-31, < holdout). FADE the opening gap: side = -sign(g); entry TAKER 09:35 ET, exit TAKER 15:45 ET; XNAS TOB (L9 -- never NBBO). Spread lives in the fills; only the 0.25 bps fees are subtracted separately. NO-COST-MODEL beyond COST_MODEL v1 taker. NO ledger verdict here.

seed=7    holdout seal: 2026-06-01

## Cost floors (frozen; written BEFORE any conditional mean)

```
{
  "generated_ts": "2026-07-23T07:44:23.608364+00:00",
  "family": "gap_day_reversion_v1",
  "params": {
    "slip_bps_per_leg": 0.5,
    "slip_bps_rt": 1.0,
    "fees_rt_bps": 0.25,
    "decision_hms": [
      9,
      35,
      0
    ],
    "exit_hms": [
      15,
      45,
      0
    ]
  },
  "per_name": {
    "KLAC": {
      "median_rt_spread_bps": 37.2187,
      "floor_bps": 38.4687,
      "n_sessions": 683
    },
    "MRVL": {
      "median_rt_spread_bps": 10.2161,
      "floor_bps": 11.4661,
      "n_sessions": 683
    },
    "LRCX": {
      "median_rt_spread_bps": 19.4686,
      "floor_bps": 20.7186,
      "n_sessions": 683
    },
    "TXN": {
      "median_rt_spread_bps": 13.8725,
      "floor_bps": 15.1225,
      "n_sessions": 683
    },
    "AMAT": {
      "median_rt_spread_bps": 14.7484,
      "floor_bps": 15.9984,
      "n_sessions": 683
    }
  },
  "pooled_floor_bps": 15.9984
}
```

## Cell t50 (|g| >= 50 bps)

N=2292  sessions=641  mean_net_bps=-8.7072  CI=[-23.1166, 5.689]
pooled_floor_bps=15.9984  bar(2x)=31.9968  names_positive=1/5
PASS=False  UNDERPOWERED=False  BETWEEN=False
```
{
  "thresh_bps": 50.0,
  "N": 2292,
  "n_sessions": 641,
  "mean_net_bps": -8.7072,
  "ci_lo": -23.1166,
  "ci_hi": 5.689,
  "pooled_floor_bps": 15.9984,
  "bar_2x_floor_bps": 31.9968,
  "per_name_mean": {
    "AMAT": 4.5197,
    "KLAC": -15.2612,
    "LRCX": -12.4547,
    "MRVL": -9.6498,
    "TXN": -11.3246
  },
  "n_names_positive": 1,
  "meets_n_sessions_floor": true,
  "meets_ci_lower_gt_0": false,
  "meets_2x_floor": false,
  "meets_3of5_names": false,
  "underpowered": false,
  "between": false,
  "pass": false
}
```

## Cell t100 (nested) (|g| >= 100 bps)

N=1481  sessions=514  mean_net_bps=-12.1365  CI=[-30.759, 7.8908]
pooled_floor_bps=15.9984  bar(2x)=31.9968  names_positive=1/5
PASS=False  UNDERPOWERED=False  BETWEEN=False
```
{
  "thresh_bps": 100.0,
  "N": 1481,
  "n_sessions": 514,
  "mean_net_bps": -12.1365,
  "ci_lo": -30.759,
  "ci_hi": 7.8908,
  "pooled_floor_bps": 15.9984,
  "bar_2x_floor_bps": 31.9968,
  "per_name_mean": {
    "AMAT": 4.284,
    "KLAC": -19.4555,
    "LRCX": -13.0099,
    "MRVL": -8.3758,
    "TXN": -33.1763
  },
  "n_names_positive": 1,
  "meets_n_sessions_floor": true,
  "meets_ci_lower_gt_0": false,
  "meets_2x_floor": false,
  "meets_3of5_names": false,
  "underpowered": false,
  "between": false,
  "pass": false
}
```

## ADIA No.19 daily panel (t50 stream; $10k per event; SR0=0)

```
{
  "T": 641,
  "n_events": 2292,
  "mean_usd": -31.134,
  "ci_lo_usd": -83.1817,
  "ci_hi_usd": 19.9216,
  "sr_native": -0.0462,
  "psr_sr0_0": 0.1016,
  "min_trl": 1071.38,
  "gamma3": 0.3086,
  "gamma4": 10.2642,
  "rho": -0.0837
}
```

## Funnel (skips + below + fired == candidates)

```
{
  "candidates": 3550,
  "no_bar": 0,
  "early_close": 35,
  "below_t50": 1143,
  "no_quote_entry": 80,
  "no_quote_exit": 0,
  "stale_quote": 0,
  "fired": 2292
}
```

## Report-only strata (no bar)

### per_name

| symbol | n   | mean_net_bps |
|--------|-----|--------------|
| AMAT   | 473 | 4.5197       |
| KLAC   | 461 | -15.2612     |
| LRCX   | 476 | -12.4547     |
| MRVL   | 512 | -9.6498      |
| TXN    | 370 | -11.3246     |

### per_year

| year | n   | mean_net_bps |
|------|-----|--------------|
| 2023 | 316 | 11.634       |
| 2024 | 838 | -28.4961     |
| 2025 | 824 | 2.5309       |
| 2026 | 314 | -5.8568      |

### gap_sign

| gap_sign | n    | mean_net_bps |
|----------|------|--------------|
| down_gap | 1050 | -2.9679      |
| up_gap   | 1242 | -13.5592     |

### abs_g_tercile

| abs_g_tercile | n   | mean_net_bps |
|---------------|-----|--------------|
| hi            | 764 | -16.3662     |
| lo            | 764 | -2.8155      |
| mid           | 764 | -6.9399      |

### entry_spread_tercile

| entry_spread_tercile | n   | mean_net_bps |
|----------------------|-----|--------------|
| hi                   | 764 | -14.7849     |
| lo                   | 764 | 0.1019       |
| mid                  | 764 | -11.4386     |
