# M6 MOC-imbalance trial report — MOC-t05-nopersist

Symbols: NVDA, TSLA, AMD, MU, GOOGL
Threshold (|norm_imb| of ADV$): 0.0005  (0.050% of ADV$)
Persistence prong: OFF    seed=7
Sessions in range (< holdout): 604
Events evaluated (rows): 1445
Splits present: ['train', 'validate']

NOTE: sessions whose official closing-cross print is absent (legacy condition-stripped NVDA/TSLA tick exports) are SKIPPED and counted below under 'skipped_no_cross' — they resolve once the conditioned re-download completes. Not a result, a coverage gap.

## 1. Event funnel / skipped-session counts

```
{
  "no_noii_partition": 0,
  "no_noii_msgs": 30,
  "no_adv": 0,
  "no_signal": 0,
  "inactive": 174,
  "events_fired": 2816,
  "skipped_no_cross": 0,
  "skipped_no_tape": 1371,
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
| AMD    | 171      | 171        | 3.824        | -1.393 | 9.224 |
| GOOGL  | 179      | 179        | 1.72         | -1.446 | 4.763 |
| MU     | 568      | 568        | -1.329       | -4.629 | 2.17  |
| NVDA   | 360      | 360        | 3.638        | -0.104 | 7.167 |
| TSLA   | 167      | 167        | -3.808       | -9.535 | 1.456 |
| POOLED | 1445     | 588        | 0.609        | -1.558 | 2.786 |

## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)

| split    | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|----------|----------|------------|--------------|--------|-------|
| train    | 1149     | 525        | 0.919        | -1.509 | 3.177 |
| validate | 296      | 63         | -0.592       | -6.005 | 5.086 |

## 4. Cross-print ground-truth table (10 stratified events, PROTOCOL v6.1)

entry_in_nbbo: entry fill sits within the prevailing NBBO at the signal instant. cross_vs_close_bps: official cross print vs the session's last 1m-bar close (should be ~0 for a real cross).

| session    | symbol | side | norm_imb  | entry_bid | entry_ask | entry_px   | exit_reason | cross_px | bar_close | cross_vs_close_bps | entry_in_nbbo | net_bps     |
|------------|--------|------|-----------|-----------|-----------|------------|-------------|----------|-----------|--------------------|---------------|-------------|
| 2024-08-06 | NVDA   | 1    | 0.005695  | 105.74    | 105.76    | 105.705285 | moc         | 104.25   | 101.38    | 283.093312         | true          | -137.969686 |
| 2024-09-20 | NVDA   | -1   | -0.083052 | 115.99    | 116.01    | 115.884206 | moc         | 116.0    | 115.89    | 9.491759           | true          | -10.292259  |
| 2024-09-20 | MU     | 1    | 0.134859  | 90.58     | 90.59     | 90.584529  | moc         | 90.9     | 90.58     | 35.327887          | true          | 34.525101   |
| 2024-12-18 | MU     | 1    | 0.023848  | 105.04    | 105.1     | 105.40527  | moc         | 103.9    | 86.67     | 1988.000462        | false         | -143.103566 |
| 2025-04-07 | MU     | -1   | -0.029625 | 67.35     | 67.37     | 67.306635  | moc         | 68.37    | 69.17     | -115.657077        | true          | -158.288214 |
| 2025-04-08 | MU     | 1    | 0.029119  | 63.82     | 63.87     | 64.19321   | moc         | 65.54    | 64.33     | 188.092647         | false         | 209.496349  |
| 2025-04-10 | MU     | 1    | 0.004763  | 68.94     | 68.98     | 68.903445  | moc         | 70.05    | 69.15     | 130.151844         | true          | 166.095251  |
| 2026-03-20 | GOOGL  | 1    | 0.078521  | 300.45    | 300.49    | 300.575028 | moc         | 301.0    | 302.4     | -46.296296         | true          | 13.838209   |
| 2026-05-29 | NVDA   | -1   | -0.22875  | 214.73    | 214.83    | 214.299284 | moc         | 211.14   | 212.24    | -51.828119         | false         | 147.123941  |

## 5. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_mean_net_bps": 0.609,
  "pooled_ci_lo": -1.558,
  "pooled_ci_hi": 2.786,
  "n_events": 1445,
  "n_sessions": 588,
  "symbols_positive_point_estimate": 3,
  "per_symbol_point_estimate": {
    "AMD": 3.824,
    "GOOGL": 1.72,
    "MU": -1.329,
    "NVDA": 3.638,
    "TSLA": -3.808
  },
  "meets_pooled_lo_gt_0": false,
  "meets_n_ge_100": true,
  "meets_ge_3_of_5_symbols_positive": true
}
```

## 6. Exit-reason distribution

| exit_reason | count |
|-------------|-------|
| moc         | 1445  |
