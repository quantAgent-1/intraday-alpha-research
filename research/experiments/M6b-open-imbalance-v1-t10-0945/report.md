# M6b OPENING-imbalance trial report — M6b-open-imbalance-v1-t10-0945

Family: open_imbalance_v1 (M3_REGISTRATION.md M6b section)
Symbols: NVDA, TSLA, AMD, MU, GOOGL
Threshold (|norm_imb| of ADV$): 0.001  (0.100% of ADV$)
Exit cell: 0945  (market-out at 09:45:00 ET + U[5,25]s latency)    seed=7
Signal: LAST opening-NOII at-or-before 09:28:30 ET; ENTRY = MOO at daily bar OPEN (official open = opening cross), ts 09:30:00 ET, zero spread/slip.
Sessions in range (< holdout): 1610
Events evaluated (rows): 730
Splits present: ['train', 'validate']

Message window verified: opening-cross NOII disseminates 09:25-09:30 ET in the owned imbalance-schema partitions; near_price populates from ~09:28 (near->ref fallback before that). Loaded [09:00, 09:30], signal picks the last message at-or-before 09:28:30 ET (PIT).

## 1. Event funnel / skipped-session counts

```
{
  "no_noii_partition": 0,
  "no_noii_msgs": 0,
  "no_adv": 0,
  "no_signal": 0,
  "inactive": 7320,
  "events_fired": 730,
  "skipped_no_open": 0,
  "skipped_no_bbo": 0,
  "void": 0
}
```

## 2. Pooled + per-symbol net_bps day-clustered CIs (stress.clustered_mean_ci)

| symbol | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|--------|----------|------------|--------------|---------|--------|
| AMD    | 94       | 94         | 31.544       | -0.035  | 64.302 |
| GOOGL  | 298      | 298        | -13.337      | -22.482 | -3.629 |
| MU     | 140      | 140        | 6.105        | -20.301 | 32.216 |
| NVDA   | 124      | 124        | -4.731       | -27.36  | 16.945 |
| TSLA   | 74       | 74         | -35.796      | -75.624 | 4.179  |
| POOLED | 730      | 547        | -4.644       | -13.972 | 5.578  |

## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)

| split    | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------|----------|------------|--------------|---------|--------|
| train    | 693      | 521        | -4.561       | -14.574 | 5.583  |
| validate | 37       | 26         | -6.189       | -60.283 | 51.782 |

## 3b. By-year net_bps day-clustered CIs

| year | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|------|----------|------------|--------------|---------|--------|
| 2020 | 110      | 79         | -11.039      | -36.545 | 14.287 |
| 2021 | 103      | 86         | -4.058       | -25.434 | 17.964 |
| 2022 | 86       | 66         | -18.556      | -44.847 | 7.542  |
| 2023 | 82       | 62         | -2.963       | -30.12  | 22.992 |
| 2024 | 138      | 98         | -9.77        | -32.301 | 12.092 |
| 2025 | 152      | 114        | 9.367        | -15.562 | 33.583 |
| 2026 | 59       | 42         | 0.092        | -40.823 | 43.503 |

## 4. Ground-truth table (10 stratified events, PROTOCOL v6.1)

open_vs_bbomid_bps: official open (= MOO fill) vs the FIRST bbo-1s mid at 09:30:00-09:30:05 ET; open_dev_gt_20bps flags |dev| > 20 bps. exit_in_nbbo: the market-out fill sits within the prevailing BBO at the exit instant.

| session    | symbol | side | norm_imb  | open_px | open_bbo_mid | open_vs_bbomid_bps | open_dev_gt_20bps | exit_bid | exit_ask | exit_px     | exit_in_nbbo | net_bps     |
|------------|--------|------|-----------|---------|--------------|--------------------|-------------------|----------|----------|-------------|--------------|-------------|
| 2022-02-24 | TSLA   | -1   | -0.00182  | 700.39  | 700.655      | -3.782175          | false             | 735.38   | 735.92   | 735.956796  | true         | -508.114161 |
| 2022-03-18 | GOOGL  | 1    | 0.012116  | 2668.49 | 2665.69      | 10.503847          | false             | 2649.57  | 2651.26  | 2649.437522 | true         | -71.695834  |
| 2022-09-16 | GOOGL  | 1    | 0.013711  | 102.07  | 102.18       | -10.765316         | false             | 101.57   | 101.59   | 101.564921  | true         | -49.782056  |
| 2023-06-16 | GOOGL  | 1    | 0.016275  | 125.93  | 125.87       | 4.766823           | false             | 124.13   | 124.15   | 124.123793  | true         | -143.725102 |
| 2024-08-05 | NVDA   | -1   | -0.005084 | 92.06   | 92.075       | -1.629107          | false             | 97.43    | 97.47    | 97.474874   | true         | -588.489605 |
| 2025-01-21 | TSLA   | -1   | -0.001018 | 432.64  | 432.59       | 1.155829           | false             | 412.12   | 412.34   | 412.360617  | true         | 468.435739  |
| 2025-02-27 | NVDA   | 1    | 0.0014    | 135.0   | 134.97       | 2.222716           | false             | 129.27   | 129.29   | 129.263537  | true         | -425.210475 |
| 2025-10-06 | AMD    | -1   | -0.018314 | 226.445 | 226.43       | 0.662456           | false             | 215.0    | 215.08   | 215.090754  | true         | 501.11297   |
| 2026-05-06 | AMD    | 1    | 0.001688  | 409.49  | 409.74       | -6.10143           | false             | 429.48   | 429.56   | 429.458526  | true         | 487.329172  |

## 5. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_mean_net_bps": -4.644,
  "pooled_ci_lo": -13.972,
  "pooled_ci_hi": 5.578,
  "n_events": 730,
  "n_sessions": 547,
  "symbols_positive_point_estimate": 2,
  "per_symbol_point_estimate": {
    "AMD": 31.544,
    "GOOGL": -13.337,
    "MU": 6.105,
    "NVDA": -4.731,
    "TSLA": -35.796
  },
  "meets_pooled_lo_gt_0": false,
  "meets_n_ge_100": true,
  "meets_ge_3_of_5_symbols_positive": false
}
```

## 6. Exit-reason / side distribution

| exit_reason | side | count |
|-------------|------|-------|
| exit_0945   | -1   | 370   |
| exit_0945   | 1    | 360   |
