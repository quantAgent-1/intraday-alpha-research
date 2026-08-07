# M6 MOC-imbalance trial report — MOC-full-t10-persist

Symbols: NVDA, TSLA, AMD, MU, GOOGL
Threshold (|norm_imb| of ADV$): 0.001  (0.100% of ADV$)
Persistence prong: ON    seed=7
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
  "persistence_exits": 655
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
| AMD    | 533      | 533        | 2.466        | -0.379 | 5.371 |
| GOOGL  | 592      | 592        | 0.909        | -0.981 | 2.832 |
| MU     | 565      | 565        | -0.469       | -3.646 | 2.738 |
| NVDA   | 554      | 554        | 3.614        | 0.565  | 6.709 |
| TSLA   | 500      | 500        | 1.541        | -2.334 | 5.403 |
| POOLED | 2744     | 618        | 1.589        | -0.176 | 3.301 |

## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)

| split    | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|----------|----------|------------|--------------|--------|-------|
| train    | 2463     | 555        | 1.592        | -0.268 | 3.274 |
| validate | 281      | 63         | 1.56         | -3.639 | 7.22  |

## 3b. By-year net_bps day-clustered CIs

| year | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|------|----------|------------|--------------|--------|-------|
| 2023 | 86       | 20         | -0.85        | -5.497 | 3.665 |
| 2024 | 1096     | 249        | 2.285        | -0.248 | 4.856 |
| 2025 | 1105     | 247        | 0.476        | -2.382 | 3.587 |
| 2026 | 457      | 102        | 3.071        | -0.667 | 6.919 |

## 4. Cross-print ground-truth table (10 stratified events, PROTOCOL v6.1)

entry_in_nbbo: entry fill sits within the prevailing NBBO at the signal instant. cross_vs_close_bps: official cross print vs the session's last 1m-bar close (should be ~0 for a real cross).

| session    | symbol | side | norm_imb  | entry_bid | entry_ask | entry_px   | exit_reason | cross_px | bar_close | cross_vs_close_bps | entry_in_nbbo | net_bps     |
|------------|--------|------|-----------|-----------|-----------|------------|-------------|----------|-----------|--------------------|---------------|-------------|
| 2024-08-06 | NVDA   | 1    | 0.005695  | 105.74    | 105.76    | 105.695285 | moc         | 104.25   | 101.38    | 283.093312         | true          | -137.036577 |
| 2024-09-20 | MU     | 1    | 0.134859  | 90.58     | 90.59     | 90.584529  | moc         | 90.9     | 90.58     | 35.327887          | true          | 34.525101   |
| 2024-09-20 | GOOGL  | 1    | 0.115866  | 163.02    | 163.04    | 163.068153 | moc         | 163.59   | 162.61    | 60.266896          | true          | 31.700813   |
| 2024-11-25 | TSLA   | -1   | -0.003849 | 344.89    | 345.05    | 344.872755 | moc         | 338.59   | 334.41    | 124.996262         | true          | 181.876046  |
| 2024-12-20 | TSLA   | -1   | -0.06997  | 429.65    | 429.81    | 428.57857  | moc         | 421.06   | 423.28    | -52.447552         | false         | 175.130377  |
| 2025-04-07 | TSLA   | -1   | -0.007217 | 228.97    | 229.01    | 228.738563 | moc         | 233.29   | 239.5     | -259.290188        | false         | -199.279894 |
| 2025-04-07 | MU     | -1   | -0.029625 | 67.33     | 67.37     | 67.316634  | moc         | 68.37    | 69.17     | -115.657077        | true          | -156.779303 |
| 2025-04-08 | MU     | 1    | 0.029119  | 63.82     | 63.85     | 64.173209  | moc         | 65.54    | 64.33     | 188.092647         | false         | 212.678364  |
| 2025-06-27 | GOOGL  | 1    | 0.329227  | 176.04    | 176.06    | 176.738837 | moc         | 178.53   | 177.62    | 51.232969          | false         | 101.042172  |
| 2026-05-29 | NVDA   | -1   | -0.22875  | 214.73    | 214.81    | 214.559271 | moc         | 211.14   | 212.24    | -51.828119         | true          | 159.062561  |

## 5. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_mean_net_bps": 1.589,
  "pooled_ci_lo": -0.176,
  "pooled_ci_hi": 3.301,
  "n_events": 2744,
  "n_sessions": 618,
  "symbols_positive_point_estimate": 4,
  "per_symbol_point_estimate": {
    "AMD": 2.466,
    "GOOGL": 0.909,
    "MU": -0.469,
    "NVDA": 3.614,
    "TSLA": 1.541
  },
  "meets_pooled_lo_gt_0": false,
  "meets_n_ge_100": true,
  "meets_ge_3_of_5_symbols_positive": true
}
```

## 6. Exit-reason distribution

| exit_reason | count |
|-------------|-------|
| moc         | 2089  |
| persistence | 655   |
