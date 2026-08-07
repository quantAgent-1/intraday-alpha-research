# M6b OPENING-imbalance trial report — M6b-open-imbalance-v1-t10-1000

Family: open_imbalance_v1 (M3_REGISTRATION.md M6b section)
Symbols: NVDA, TSLA, AMD, MU, GOOGL
Threshold (|norm_imb| of ADV$): 0.001  (0.100% of ADV$)
Exit cell: 1000  (market-out at 10:00:00 ET + U[5,25]s latency)    seed=7
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
| AMD    | 94       | 94         | 31.631       | -8.689  | 74.526 |
| GOOGL  | 298      | 298        | -15.508      | -25.708 | -5.469 |
| MU     | 140      | 140        | 14.187       | -16.458 | 44.916 |
| NVDA   | 124      | 124        | -6.174       | -40.877 | 26.565 |
| TSLA   | 74       | 74         | -39.078      | -89.866 | 11.907 |
| POOLED | 730      | 547        | -4.547       | -16.559 | 8.776  |

## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)

| split    | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------|----------|------------|--------------|---------|--------|
| train    | 693      | 521        | -3.152       | -16.32  | 10.673 |
| validate | 37       | 26         | -30.669      | -78.251 | 15.203 |

## 3b. By-year net_bps day-clustered CIs

| year | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|------|----------|------------|--------------|---------|--------|
| 2020 | 110      | 79         | -4.688       | -46.872 | 38.292 |
| 2021 | 103      | 86         | 3.377        | -22.331 | 30.682 |
| 2022 | 86       | 66         | -15.371      | -46.168 | 16.276 |
| 2023 | 82       | 62         | 4.556        | -27.321 | 33.878 |
| 2024 | 138      | 98         | -9.433       | -40.343 | 18.385 |
| 2025 | 152      | 114        | 2.811        | -32.17  | 35.379 |
| 2026 | 59       | 42         | -22.52       | -65.391 | 19.54  |

## 4. Ground-truth table (10 stratified events, PROTOCOL v6.1)

open_vs_bbomid_bps: official open (= MOO fill) vs the FIRST bbo-1s mid at 09:30:00-09:30:05 ET; open_dev_gt_20bps flags |dev| > 20 bps. exit_in_nbbo: the market-out fill sits within the prevailing BBO at the exit instant.

| session    | symbol | side | norm_imb  | open_px | open_bbo_mid | open_vs_bbomid_bps | open_dev_gt_20bps | exit_bid | exit_ask | exit_px     | exit_in_nbbo | net_bps     |
|------------|--------|------|-----------|---------|--------------|--------------------|-------------------|----------|----------|-------------|--------------|-------------|
| 2020-03-09 | AMD    | 1    | 0.001783  | 43.03   | 42.765       | 61.966561          | true              | 45.36    | 45.47    | 45.357732   | true         | 540.639384  |
| 2020-03-09 | MU     | 1    | 0.001434  | 45.48   | 45.295       | 40.84336           | true              | 48.0     | 48.09    | 47.9976     | true         | 553.245398  |
| 2022-03-18 | GOOGL  | 1    | 0.012116  | 2668.49 | 2665.69      | 10.503847          | false             | 2663.97  | 2664.53  | 2663.836801 | true         | -17.737048  |
| 2022-09-16 | GOOGL  | 1    | 0.013711  | 102.07  | 102.18       | -10.765316         | false             | 101.64   | 101.67   | 101.634918  | true         | -42.924566  |
| 2023-06-16 | GOOGL  | 1    | 0.016275  | 125.93  | 125.87       | 4.766823           | false             | 124.41   | 124.45   | 124.403779  | true         | -121.492306 |
| 2024-08-05 | NVDA   | -1   | -0.005084 | 92.06   | 92.075       | -1.629107          | false             | 100.57   | 100.6    | 100.60503   | true         | -928.502259 |
| 2025-02-27 | NVDA   | 1    | 0.0014    | 135.0   | 134.97       | 2.222716           | false             | 125.93   | 125.98   | 125.923704  | true         | -672.59809  |
| 2025-04-07 | NVDA   | -1   | -0.001925 | 87.46   | 87.535       | -8.568001          | false             | 94.26    | 94.29    | 94.294715   | true         | -781.767471 |
| 2025-10-06 | AMD    | -1   | -0.018314 | 226.445 | 226.43       | 0.662456           | false             | 207.94   | 208.08   | 208.090404  | true         | 810.254263  |

## 5. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_mean_net_bps": -4.547,
  "pooled_ci_lo": -16.559,
  "pooled_ci_hi": 8.776,
  "n_events": 730,
  "n_sessions": 547,
  "symbols_positive_point_estimate": 2,
  "per_symbol_point_estimate": {
    "AMD": 31.631,
    "GOOGL": -15.508,
    "MU": 14.187,
    "NVDA": -6.174,
    "TSLA": -39.078
  },
  "meets_pooled_lo_gt_0": false,
  "meets_n_ge_100": true,
  "meets_ge_3_of_5_symbols_positive": false
}
```

## 6. Exit-reason / side distribution

| exit_reason | side | count |
|-------------|------|-------|
| exit_1000   | -1   | 370   |
| exit_1000   | 1    | 360   |
