# M6 MOC-imbalance trial report — MOC-full-t10-nopersist

Symbols: NVDA, TSLA, AMD, MU, GOOGL
Threshold (|norm_imb| of ADV$): 0.001  (0.100% of ADV$)
Persistence prong: OFF    seed=7
Entry-fill source: bbo1s
Sessions in range (< holdout): 1610
Events evaluated (rows): 2744
Splits present: ['train', 'validate']

NOTE: sessions whose official closing-cross print is absent (legacy condition-stripped NVDA/TSLA tick exports) are SKIPPED and counted below under 'skipped_no_cross' — they resolve once the conditioned re-download completes. Not a result, a coverage gap.

## 1. Event funnel / skipped-session counts

```
{
  "no_noii_partition": 0,
  "no_noii_msgs": 60,
  "no_adv": 4380,
  "no_signal": 0,
  "inactive": 432,
  "events_fired": 3178,
  "skipped_no_cross": 434,
  "skipped_no_bbo": 0,
  "skipped_no_tape": 0,
  "void": 0,
  "persistence_exits": 0
}
```

Per-symbol skipped (no cross print):

```
{
  "NVDA": 76,
  "TSLA": 72,
  "AMD": 89,
  "MU": 97,
  "GOOGL": 100
}
```

## 2. Pooled + per-symbol net_bps day-clustered CIs (stress.clustered_mean_ci)

| symbol | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|--------|----------|------------|--------------|--------|-------|
| AMD    | 533      | 533        | 2.541        | -0.435 | 5.521 |
| GOOGL  | 592      | 592        | 1.154        | -0.782 | 3.035 |
| MU     | 565      | 565        | -1.017       | -4.349 | 2.27  |
| NVDA   | 554      | 554        | 2.899        | -0.245 | 6.191 |
| TSLA   | 500      | 500        | 0.869        | -3.078 | 4.757 |
| POOLED | 2744     | 618        | 1.277        | -0.494 | 3.035 |

## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)

| split    | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|----------|----------|------------|--------------|--------|-------|
| train    | 2463     | 555        | 1.383        | -0.518 | 3.08  |
| validate | 281      | 63         | 0.344        | -5.268 | 6.187 |

## 3b. By-year net_bps day-clustered CIs

| year | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|------|----------|------------|--------------|--------|-------|
| 2023 | 86       | 20         | -1.886       | -6.728 | 2.701 |
| 2024 | 1096     | 249        | 1.687        | -0.857 | 4.22  |
| 2025 | 1105     | 247        | 0.6          | -2.304 | 3.739 |
| 2026 | 457      | 102        | 2.525        | -1.498 | 6.62  |

## 4. Cross-print ground-truth table (10 stratified events, PROTOCOL v6.1)

entry_in_nbbo: entry fill sits within the prevailing NBBO at the signal instant. cross_vs_close_bps: official cross print vs the session's last 1m-bar close (should be ~0 for a real cross).

| session    | symbol | side | norm_imb  | entry_bid | entry_ask | entry_px   | exit_reason | cross_px | bar_close | cross_vs_close_bps | entry_in_nbbo | net_bps     |
|------------|--------|------|-----------|-----------|-----------|------------|-------------|----------|-----------|--------------------|---------------|-------------|
| 2024-09-20 | MU     | 1    | 0.134859  | 90.58     | 90.59     | 90.584529  | moc         | 90.9     | 90.58     | 35.327887          | true          | 34.525101   |
| 2024-09-20 | GOOGL  | 1    | 0.115866  | 163.02    | 163.04    | 163.068153 | moc         | 163.59   | 162.61    | 60.266896          | true          | 31.700813   |
| 2024-11-25 | TSLA   | -1   | -0.003849 | 344.89    | 345.05    | 344.872755 | moc         | 338.59   | 334.41    | 124.996262         | true          | 181.876046  |
| 2024-12-20 | TSLA   | -1   | -0.06997  | 429.65    | 429.81    | 428.57857  | moc         | 421.06   | 423.28    | -52.447552         | false         | 175.130377  |
| 2025-04-07 | TSLA   | -1   | -0.007217 | 228.97    | 229.01    | 228.738563 | moc         | 233.29   | 239.5     | -259.290188        | false         | -199.279894 |
| 2025-04-07 | MU     | -1   | -0.029625 | 67.33     | 67.37     | 67.316634  | moc         | 68.37    | 69.17     | -115.657077        | true          | -156.779303 |
| 2025-04-08 | MU     | 1    | 0.029119  | 63.82     | 63.85     | 64.173209  | moc         | 65.54    | 64.33     | 188.092647         | false         | 212.678364  |
| 2025-05-07 | NVDA   | -1   | -0.006604 | 115.37    | 115.39    | 115.214239 | moc         | 117.06   | 116.71    | 29.988861          | false         | -160.502508 |
| 2025-06-27 | GOOGL  | 1    | 0.329227  | 176.04    | 176.06    | 176.738837 | moc         | 178.53   | 177.62    | 51.232969          | false         | 101.042172  |
| 2026-05-29 | NVDA   | -1   | -0.22875  | 214.73    | 214.81    | 214.559271 | moc         | 211.14   | 212.24    | -51.828119         | true          | 159.062561  |

## 5. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_mean_net_bps": 1.277,
  "pooled_ci_lo": -0.494,
  "pooled_ci_hi": 3.035,
  "n_events": 2744,
  "n_sessions": 618,
  "symbols_positive_point_estimate": 4,
  "per_symbol_point_estimate": {
    "AMD": 2.541,
    "GOOGL": 1.154,
    "MU": -1.017,
    "NVDA": 2.899,
    "TSLA": 0.869
  },
  "meets_pooled_lo_gt_0": false,
  "meets_n_ge_100": true,
  "meets_ge_3_of_5_symbols_positive": true
}
```

## 6. Exit-reason distribution

| exit_reason | count |
|-------------|-------|
| moc         | 2744  |
