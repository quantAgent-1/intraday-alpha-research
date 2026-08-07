# M6b OPENING-imbalance trial report — M6b-open-imbalance-v1-t05-0945

Family: open_imbalance_v1 (M3_REGISTRATION.md M6b section)
Symbols: NVDA, TSLA, AMD, MU, GOOGL
Threshold (|norm_imb| of ADV$): 0.0005  (0.050% of ADV$)
Exit cell: 0945  (market-out at 09:45:00 ET + U[5,25]s latency)    seed=7
Signal: LAST opening-NOII at-or-before 09:28:30 ET; ENTRY = MOO at daily bar OPEN (official open = opening cross), ts 09:30:00 ET, zero spread/slip.
Sessions in range (< holdout): 1610
Events evaluated (rows): 1634
Splits present: ['train', 'validate']

Message window verified: opening-cross NOII disseminates 09:25-09:30 ET in the owned imbalance-schema partitions; near_price populates from ~09:28 (near->ref fallback before that). Loaded [09:00, 09:30], signal picks the last message at-or-before 09:28:30 ET (PIT).

## 1. Event funnel / skipped-session counts

```
{
  "no_noii_partition": 0,
  "no_noii_msgs": 0,
  "no_adv": 0,
  "no_signal": 0,
  "inactive": 6416,
  "events_fired": 1634,
  "skipped_no_open": 0,
  "skipped_no_bbo": 0,
  "void": 0
}
```

## 2. Pooled + per-symbol net_bps day-clustered CIs (stress.clustered_mean_ci)

| symbol | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|--------|----------|------------|--------------|---------|--------|
| AMD    | 241      | 241        | 10.399       | -6.483  | 26.847 |
| GOOGL  | 544      | 544        | -8.658       | -15.838 | -1.914 |
| MU     | 309      | 309        | 8.603        | -8.408  | 24.043 |
| NVDA   | 322      | 322        | 0.237        | -12.203 | 12.908 |
| TSLA   | 218      | 218        | -16.367      | -37.151 | 5.631  |
| POOLED | 1634     | 1039       | -1.859       | -8.313  | 4.515  |

## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)

| split    | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------|----------|------------|--------------|---------|--------|
| train    | 1551     | 990        | -2.779       | -9.275  | 3.619  |
| validate | 83       | 49         | 15.344       | -17.494 | 51.282 |

## 3b. By-year net_bps day-clustered CIs

| year | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|------|----------|------------|--------------|---------|--------|
| 2020 | 187      | 127        | -4.273       | -25.358 | 17.374 |
| 2021 | 219      | 149        | 3.589        | -10.08  | 17.045 |
| 2022 | 237      | 158        | -11.147      | -28.163 | 5.309  |
| 2023 | 224      | 154        | 2.113        | -11.433 | 15.544 |
| 2024 | 313      | 179        | -2.043       | -15.972 | 11.289 |
| 2025 | 321      | 192        | -1.536       | -16.808 | 13.909 |
| 2026 | 133      | 80         | 2.085        | -25.686 | 30.614 |

## 4. Ground-truth table (10 stratified events, PROTOCOL v6.1)

open_vs_bbomid_bps: official open (= MOO fill) vs the FIRST bbo-1s mid at 09:30:00-09:30:05 ET; open_dev_gt_20bps flags |dev| > 20 bps. exit_in_nbbo: the market-out fill sits within the prevailing BBO at the exit instant.

| session    | symbol | side | norm_imb  | open_px | open_bbo_mid | open_vs_bbomid_bps | open_dev_gt_20bps | exit_bid | exit_ask | exit_px     | exit_in_nbbo | net_bps     |
|------------|--------|------|-----------|---------|--------------|--------------------|-------------------|----------|----------|-------------|--------------|-------------|
| 2020-07-13 | TSLA   | 1    | 0.000739  | 1659.0  | 1658.45      | 3.31635            | false             | 1758.43  | 1759.95  | 1758.342079 | true         | 598.489019  |
| 2022-02-24 | TSLA   | -1   | -0.00182  | 700.39  | 700.655      | -3.782175          | false             | 735.38   | 735.92   | 735.956796  | true         | -508.114161 |
| 2022-03-18 | GOOGL  | 1    | 0.012116  | 2668.49 | 2665.69      | 10.503847          | false             | 2649.57  | 2651.26  | 2649.437522 | true         | -71.695834  |
| 2022-05-26 | NVDA   | -1   | -0.000667 | 160.36  | 160.305      | 3.43096            | false             | 168.74   | 168.82   | 168.828441  | true         | -528.389361 |
| 2022-09-16 | GOOGL  | 1    | 0.013711  | 102.07  | 102.18       | -10.765316         | false             | 101.57   | 101.59   | 101.564921  | true         | -49.782056  |
| 2023-06-16 | GOOGL  | 1    | 0.016275  | 125.93  | 125.87       | 4.766823           | false             | 124.13   | 124.15   | 124.123793  | true         | -143.725102 |
| 2024-08-05 | NVDA   | -1   | -0.005084 | 92.06   | 92.075       | -1.629107          | false             | 97.43    | 97.47    | 97.474874   | true         | -588.489605 |
| 2025-10-06 | AMD    | -1   | -0.018314 | 226.445 | 226.43       | 0.662456           | false             | 215.0    | 215.08   | 215.090754  | true         | 501.11297   |
| 2025-12-19 | MU     | 1    | 0.000833  | 251.75  | 251.67       | 3.178766           | false             | 266.26   | 266.47   | 266.246687  | true         | 575.519349  |

## 5. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_mean_net_bps": -1.859,
  "pooled_ci_lo": -8.313,
  "pooled_ci_hi": 4.515,
  "n_events": 1634,
  "n_sessions": 1039,
  "symbols_positive_point_estimate": 3,
  "per_symbol_point_estimate": {
    "AMD": 10.399,
    "GOOGL": -8.658,
    "MU": 8.603,
    "NVDA": 0.237,
    "TSLA": -16.367
  },
  "meets_pooled_lo_gt_0": false,
  "meets_n_ge_100": true,
  "meets_ge_3_of_5_symbols_positive": true
}
```

## 6. Exit-reason / side distribution

| exit_reason | side | count |
|-------------|------|-------|
| exit_0945   | -1   | 880   |
| exit_0945   | 1    | 754   |
