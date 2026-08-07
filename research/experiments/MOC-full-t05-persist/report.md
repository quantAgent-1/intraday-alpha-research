# M6 MOC-imbalance trial report — MOC-full-t05-persist

Symbols: NVDA, TSLA, AMD, MU, GOOGL
Threshold (|norm_imb| of ADV$): 0.0005  (0.050% of ADV$)
Persistence prong: ON    seed=7
Entry-fill source: bbo1s
Sessions in range (< holdout): 1610
Events evaluated (rows): 2910
Splits present: ['train', 'validate']

NOTE: sessions whose official closing-cross print is absent (legacy condition-stripped NVDA/TSLA tick exports) are SKIPPED and counted below under 'skipped_no_cross' — they resolve once the conditioned re-download completes. Not a result, a coverage gap.

## 1. Event funnel / skipped-session counts

```
{
  "no_noii_partition": 0,
  "no_noii_msgs": 60,
  "no_adv": 4380,
  "no_signal": 0,
  "inactive": 223,
  "events_fired": 3387,
  "skipped_no_cross": 477,
  "skipped_no_bbo": 0,
  "skipped_no_tape": 0,
  "void": 0,
  "persistence_exits": 727
}
```

Per-symbol skipped (no cross print):

```
{
  "NVDA": 88,
  "TSLA": 90,
  "AMD": 99,
  "MU": 99,
  "GOOGL": 101
}
```

## 2. Pooled + per-symbol net_bps day-clustered CIs (stress.clustered_mean_ci)

| symbol | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|--------|----------|------------|--------------|--------|-------|
| AMD    | 573      | 573        | 2.179        | -0.471 | 5.008 |
| GOOGL  | 603      | 603        | 1.044        | -0.883 | 2.951 |
| MU     | 587      | 587        | -0.537       | -3.611 | 2.712 |
| NVDA   | 587      | 587        | 3.072        | 0.129  | 5.958 |
| TSLA   | 560      | 560        | 1.114        | -2.21  | 4.433 |
| POOLED | 2910     | 618        | 1.371        | -0.308 | 3.046 |

## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)

| split    | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|----------|----------|------------|--------------|--------|-------|
| train    | 2614     | 555        | 1.377        | -0.406 | 2.984 |
| validate | 296      | 63         | 1.314        | -3.733 | 6.73  |

## 3b. By-year net_bps day-clustered CIs

| year | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|------|----------|------------|--------------|--------|-------|
| 2023 | 94       | 20         | -1.625       | -5.932 | 2.557 |
| 2024 | 1163     | 249        | 2.157        | -0.292 | 4.629 |
| 2025 | 1171     | 247        | 0.166        | -2.622 | 3.237 |
| 2026 | 482      | 102        | 2.988        | -0.637 | 6.752 |

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
  "pooled_mean_net_bps": 1.371,
  "pooled_ci_lo": -0.308,
  "pooled_ci_hi": 3.046,
  "n_events": 2910,
  "n_sessions": 618,
  "symbols_positive_point_estimate": 4,
  "per_symbol_point_estimate": {
    "AMD": 2.179,
    "GOOGL": 1.044,
    "MU": -0.537,
    "NVDA": 3.072,
    "TSLA": 1.114
  },
  "meets_pooled_lo_gt_0": false,
  "meets_n_ge_100": true,
  "meets_ge_3_of_5_symbols_positive": true
}
```

## 6. Exit-reason distribution

| exit_reason | count |
|-------------|-------|
| moc         | 2183  |
| persistence | 727   |
