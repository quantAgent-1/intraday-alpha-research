# M6b OPENING-imbalance trial report — M6b-open-imbalance-v1-t05-1000

Family: open_imbalance_v1 (M3_REGISTRATION.md M6b section)
Symbols: NVDA, TSLA, AMD, MU, GOOGL
Threshold (|norm_imb| of ADV$): 0.0005  (0.050% of ADV$)
Exit cell: 1000  (market-out at 10:00:00 ET + U[5,25]s latency)    seed=7
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
| AMD    | 241      | 241        | 14.787       | -6.554  | 35.454 |
| GOOGL  | 544      | 544        | -11.176      | -19.231 | -3.074 |
| MU     | 309      | 309        | 12.743       | -8.196  | 31.374 |
| NVDA   | 322      | 322        | 1.317        | -16.192 | 18.722 |
| TSLA   | 218      | 218        | -24.667      | -51.122 | 2.778  |
| POOLED | 1634     | 1039       | -2.162       | -10.123 | 6.042  |

## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)

| split    | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|----------|----------|------------|--------------|---------|--------|
| train    | 1551     | 990        | -2.102       | -10.18  | 6.215  |
| validate | 83       | 49         | -3.274       | -39.856 | 37.767 |

## 3b. By-year net_bps day-clustered CIs

| year | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|------|----------|------------|--------------|---------|--------|
| 2020 | 187      | 127        | -2.27        | -35.567 | 32.758 |
| 2021 | 219      | 149        | 7.154        | -10.484 | 25.008 |
| 2022 | 237      | 158        | -5.288       | -25.269 | 14.69  |
| 2023 | 224      | 154        | 2.815        | -12.686 | 18.814 |
| 2024 | 313      | 179        | 0.341        | -18.069 | 17.974 |
| 2025 | 321      | 192        | -6.363       | -24.396 | 13.303 |
| 2026 | 133      | 80         | -15.909      | -47.663 | 18.523 |

## 4. Ground-truth table (10 stratified events, PROTOCOL v6.1)

open_vs_bbomid_bps: official open (= MOO fill) vs the FIRST bbo-1s mid at 09:30:00-09:30:05 ET; open_dev_gt_20bps flags |dev| > 20 bps. exit_in_nbbo: the market-out fill sits within the prevailing BBO at the exit instant.

| session    | symbol | side | norm_imb  | open_px | open_bbo_mid | open_vs_bbomid_bps | open_dev_gt_20bps | exit_bid | exit_ask | exit_px     | exit_in_nbbo | net_bps     |
|------------|--------|------|-----------|---------|--------------|--------------------|-------------------|----------|----------|-------------|--------------|-------------|
| 2020-03-13 | TSLA   | -1   | -0.00069  | 595.0   | 595.275      | -4.619714          | false             | 560.08   | 561.13   | 561.158057  | true         | 568.47216   |
| 2020-09-02 | TSLA   | 1    | 0.000874  | 478.99  | 478.9        | 1.879307           | false             | 443.84   | 444.1    | 443.817808  | true         | -734.577059 |
| 2022-03-18 | GOOGL  | 1    | 0.012116  | 2668.49 | 2665.69      | 10.503847          | false             | 2663.97  | 2664.53  | 2663.836801 | true         | -17.737048  |
| 2022-09-16 | GOOGL  | 1    | 0.013711  | 102.07  | 102.18       | -10.765316         | false             | 101.64   | 101.67   | 101.634918  | true         | -42.924566  |
| 2023-06-16 | GOOGL  | 1    | 0.016275  | 125.93  | 125.87       | 4.766823           | false             | 124.41   | 124.45   | 124.403779  | true         | -121.492306 |
| 2024-08-05 | NVDA   | -1   | -0.005084 | 92.06   | 92.075       | -1.629107          | false             | 100.57   | 100.6    | 100.60503   | true         | -928.502259 |
| 2025-04-07 | NVDA   | -1   | -0.001925 | 87.46   | 87.535       | -8.568001          | false             | 94.26    | 94.29    | 94.294715   | true         | -781.767471 |
| 2025-10-06 | AMD    | -1   | -0.018314 | 226.445 | 226.43       | 0.662456           | false             | 207.94   | 208.08   | 208.090404  | true         | 810.254263  |
| 2025-12-19 | MU     | 1    | 0.000833  | 251.75  | 251.67       | 3.178766           | false             | 266.78   | 266.98   | 266.766661  | true         | 596.173108  |

## 5. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_mean_net_bps": -2.162,
  "pooled_ci_lo": -10.123,
  "pooled_ci_hi": 6.042,
  "n_events": 1634,
  "n_sessions": 1039,
  "symbols_positive_point_estimate": 3,
  "per_symbol_point_estimate": {
    "AMD": 14.787,
    "GOOGL": -11.176,
    "MU": 12.743,
    "NVDA": 1.317,
    "TSLA": -24.667
  },
  "meets_pooled_lo_gt_0": false,
  "meets_n_ge_100": true,
  "meets_ge_3_of_5_symbols_positive": true
}
```

## 6. Exit-reason / side distribution

| exit_reason | side | count |
|-------------|------|-------|
| exit_1000   | -1   | 880   |
| exit_1000   | 1    | 754   |
