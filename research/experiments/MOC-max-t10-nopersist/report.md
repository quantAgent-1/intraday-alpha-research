# M6 MOC-imbalance trial report — MOC-max-t10-nopersist

Symbols: NVDA, TSLA, AMD, MU, GOOGL
Threshold (|norm_imb| of ADV$): 0.001  (0.100% of ADV$)
Persistence prong: OFF    seed=7
Entry-fill source: bbo1s
Sessions in range (< holdout): 1610
Events evaluated (rows): 6811
Splits present: ['train', 'validate']

NOTE: sessions whose official closing-cross print is absent (legacy condition-stripped NVDA/TSLA tick exports) are SKIPPED and counted below under 'skipped_no_cross' — they resolve once the conditioned re-download completes. Not a result, a coverage gap.

## 1. Event funnel / skipped-session counts

```
{
  "no_noii_partition": 0,
  "no_noii_msgs": 60,
  "no_adv": 0,
  "no_signal": 0,
  "inactive": 1179,
  "events_fired": 6811,
  "skipped_no_cross": 0,
  "skipped_no_bbo": 0,
  "skipped_no_tape": 0,
  "void": 0,
  "persistence_exits": 0
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
| AMD    | 1306     | 1306       | 1.059        | -1.093 | 3.181 |
| GOOGL  | 1511     | 1511       | -0.786       | -2.182 | 0.671 |
| MU     | 1434     | 1434       | -1.276       | -3.231 | 0.787 |
| NVDA   | 1376     | 1376       | 2.712        | 0.474  | 4.986 |
| TSLA   | 1184     | 1184       | 3.11         | 0.34   | 5.648 |
| POOLED | 6811     | 1597       | 0.849        | -0.445 | 2.139 |

## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)

| split    | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|----------|----------|------------|--------------|--------|-------|
| train    | 6530     | 1534       | 0.871        | -0.392 | 2.243 |
| validate | 281      | 63         | 0.344        | -5.268 | 6.187 |

## 3b. By-year net_bps day-clustered CIs

| year | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi  |
|------|----------|------------|--------------|--------|--------|
| 2020 | 1018     | 250        | 5.245        | -0.002 | 10.466 |
| 2021 | 1036     | 251        | 1.703        | -0.506 | 4.108  |
| 2022 | 1054     | 250        | -2.393       | -5.344 | 0.588  |
| 2023 | 1045     | 248        | -2.36        | -4.655 | 0.024  |
| 2024 | 1096     | 249        | 1.687        | -0.857 | 4.22   |
| 2025 | 1105     | 247        | 0.6          | -2.304 | 3.739  |
| 2026 | 457      | 102        | 2.525        | -1.498 | 6.62   |

## 4. Cross-print ground-truth table (10 stratified events, PROTOCOL v6.1)

entry_in_nbbo: entry fill sits within the prevailing NBBO at the signal instant. cross_vs_close_bps: official cross print vs the session's last 1m-bar close (should be ~0 for a real cross).

| session    | symbol | side | norm_imb  | entry_bid | entry_ask | entry_px    | exit_reason | cross_px | bar_close | cross_vs_close_bps | entry_in_nbbo | net_bps     |
|------------|--------|------|-----------|-----------|-----------|-------------|-------------|----------|-----------|--------------------|---------------|-------------|
| 2020-02-04 | TSLA   | 1    | 0.004158  | 953.22    | 954.81    | 946.537325  | moc         | 887.06   | null      | null               | false         | -628.648599 |
| 2020-02-28 | GOOGL  | -1   | -0.006086 | 1306.0    | 1307.14   | 1306.364679 | moc         | 1339.25  | null      | null               | true          | -252.031557 |
| 2020-03-12 | MU     | 1    | 0.010126  | 39.7      | 39.72     | 39.741987   | moc         | 38.6     | null      | null               | true          | -287.641632 |
| 2020-03-13 | NVDA   | 1    | 0.009285  | 231.21    | 231.33    | 231.581579  | moc         | 240.93   | null      | null               | false         | 403.365141  |
| 2020-03-16 | AMD    | -1   | -0.004263 | 40.41     | 40.44     | 40.297985   | moc         | 38.71    | null      | null               | false         | 393.760646  |
| 2020-03-18 | NVDA   | 1    | 0.006438  | 194.05    | 194.4     | 194.649732  | moc         | 202.82   | null      | null               | false         | 419.42947   |
| 2020-12-18 | TSLA   | 1    | 0.50092   | 656.32    | 657.17    | 659.23296   | moc         | 658.34   | null      | null               | false         | -13.845033  |
| 2020-12-18 | MU     | -1   | -0.166925 | 71.36     | 71.39     | 71.19644    | moc         | 71.46    | null      | null               | false         | -37.318705  |
| 2025-06-27 | GOOGL  | 1    | 0.329227  | 176.04    | 176.06    | 176.738837  | moc         | 178.53   | 177.62    | 51.232969          | false         | 101.042172  |
| 2026-05-29 | NVDA   | -1   | -0.22875  | 214.73    | 214.81    | 214.559271  | moc         | 211.14   | 212.24    | -51.828119         | true          | 159.062561  |

## 5. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_mean_net_bps": 0.849,
  "pooled_ci_lo": -0.445,
  "pooled_ci_hi": 2.139,
  "n_events": 6811,
  "n_sessions": 1597,
  "symbols_positive_point_estimate": 3,
  "per_symbol_point_estimate": {
    "AMD": 1.059,
    "GOOGL": -0.786,
    "MU": -1.276,
    "NVDA": 2.712,
    "TSLA": 3.11
  },
  "meets_pooled_lo_gt_0": false,
  "meets_n_ge_100": true,
  "meets_ge_3_of_5_symbols_positive": true
}
```

## 6. Exit-reason distribution

| exit_reason | count |
|-------------|-------|
| moc         | 6811  |
