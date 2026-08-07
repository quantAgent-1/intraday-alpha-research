# M6 MOC-imbalance trial report — MOC-max-t05-persist

Symbols: NVDA, TSLA, AMD, MU, GOOGL
Threshold (|norm_imb| of ADV$): 0.0005  (0.050% of ADV$)
Persistence prong: ON    seed=7
Entry-fill source: bbo1s
Sessions in range (< holdout): 1610
Events evaluated (rows): 7325
Splits present: ['train', 'validate']

NOTE: sessions whose official closing-cross print is absent (legacy condition-stripped NVDA/TSLA tick exports) are SKIPPED and counted below under 'skipped_no_cross' — they resolve once the conditioned re-download completes. Not a result, a coverage gap.

## 1. Event funnel / skipped-session counts

```
{
  "no_noii_partition": 0,
  "no_noii_msgs": 60,
  "no_adv": 0,
  "no_signal": 0,
  "inactive": 665,
  "events_fired": 7325,
  "skipped_no_cross": 0,
  "skipped_no_bbo": 0,
  "skipped_no_tape": 0,
  "void": 0,
  "persistence_exits": 1698
}
```

Per-symbol skipped (no cross print):

```
{
  "NVDA": 0,
  "TSLA": 0,
  "AMD": 0,
  "MU": 0,
  "GOOGL": 0
}
```

## 2. Pooled + per-symbol net_bps day-clustered CIs (stress.clustered_mean_ci)

| symbol | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|--------|----------|------------|--------------|--------|-------|
| AMD    | 1425     | 1425       | 0.821        | -1.142 | 2.824 |
| GOOGL  | 1544     | 1544       | -1.192       | -2.544 | 0.089 |
| MU     | 1493     | 1493       | -0.9         | -2.736 | 0.944 |
| NVDA   | 1474     | 1474       | 3.115        | 1.21   | 5.165 |
| TSLA   | 1389     | 1389       | 3.049        | 0.787  | 5.239 |
| POOLED | 7325     | 1598       | 0.93         | -0.209 | 2.033 |

## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)

| split    | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|----------|----------|------------|--------------|--------|-------|
| train    | 7029     | 1535       | 0.914        | -0.249 | 2.138 |
| validate | 296      | 63         | 1.314        | -3.733 | 6.73  |

## 3b. By-year net_bps day-clustered CIs

| year | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|------|----------|------------|--------------|--------|-------|
| 2020 | 1123     | 251        | 3.536        | -0.72  | 8.167 |
| 2021 | 1122     | 251        | 1.803        | -0.214 | 4.034 |
| 2022 | 1131     | 250        | -1.262       | -4.0   | 1.538 |
| 2023 | 1133     | 248        | -1.672       | -3.778 | 0.622 |
| 2024 | 1163     | 249        | 2.157        | -0.292 | 4.629 |
| 2025 | 1171     | 247        | 0.166        | -2.622 | 3.237 |
| 2026 | 482      | 102        | 2.988        | -0.637 | 6.752 |

## 4. Cross-print ground-truth table (10 stratified events, PROTOCOL v6.1)

entry_in_nbbo: entry fill sits within the prevailing NBBO at the signal instant. cross_vs_close_bps: official cross print vs the session's last 1m-bar close (should be ~0 for a real cross).

| session    | symbol | side | norm_imb  | entry_bid | entry_ask | entry_px   | exit_reason | cross_px | bar_close | cross_vs_close_bps | entry_in_nbbo | net_bps     |
|------------|--------|------|-----------|-----------|-----------|------------|-------------|----------|-----------|--------------------|---------------|-------------|
| 2020-02-04 | TSLA   | 1    | 0.004158  | 953.22    | 954.81    | 946.537325 | moc         | 887.06   | null      | null               | false         | -628.648599 |
| 2020-03-12 | NVDA   | 1    | 0.014734  | 221.83    | 222.18    | 221.881094 | moc         | 216.31   | null      | null               | true          | -251.37711  |
| 2020-03-12 | MU     | 1    | 0.010126  | 39.7      | 39.72     | 39.741987  | moc         | 38.6     | null      | null               | true          | -287.641632 |
| 2020-03-13 | NVDA   | 1    | 0.009285  | 231.21    | 231.33    | 231.581579 | moc         | 240.93   | null      | null               | false         | 403.365141  |
| 2020-03-16 | NVDA   | -1   | -0.006707 | 204.27    | 204.31    | 204.269786 | moc         | 196.4    | null      | null               | true          | 384.964319  |
| 2020-03-16 | AMD    | -1   | -0.004263 | 40.41     | 40.44     | 40.297985  | moc         | 38.71    | null      | null               | false         | 393.760646  |
| 2020-12-18 | TSLA   | 1    | 0.50092   | 656.32    | 657.17    | 659.23296  | moc         | 658.34   | null      | null               | false         | -13.845033  |
| 2020-12-18 | MU     | -1   | -0.166925 | 71.36     | 71.39     | 71.19644   | moc         | 71.46    | null      | null               | false         | -37.318705  |
| 2025-06-27 | GOOGL  | 1    | 0.329227  | 176.04    | 176.06    | 176.738837 | moc         | 178.53   | 177.62    | 51.232969          | false         | 101.042172  |
| 2026-05-29 | NVDA   | -1   | -0.22875  | 214.73    | 214.81    | 214.559271 | moc         | 211.14   | 212.24    | -51.828119         | true          | 159.062561  |

## 5. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_mean_net_bps": 0.93,
  "pooled_ci_lo": -0.209,
  "pooled_ci_hi": 2.033,
  "n_events": 7325,
  "n_sessions": 1598,
  "symbols_positive_point_estimate": 3,
  "per_symbol_point_estimate": {
    "AMD": 0.821,
    "GOOGL": -1.192,
    "MU": -0.9,
    "NVDA": 3.115,
    "TSLA": 3.049
  },
  "meets_pooled_lo_gt_0": false,
  "meets_n_ge_100": true,
  "meets_ge_3_of_5_symbols_positive": true
}
```

## 6. Exit-reason distribution

| exit_reason | count |
|-------------|-------|
| moc         | 5627  |
| persistence | 1698  |
