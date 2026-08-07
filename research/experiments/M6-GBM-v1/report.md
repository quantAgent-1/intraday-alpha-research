# M6-GBM report — M6-GBM-v1

Family `moc_imbalance_v1`, M6-GBM cell (registered 2026-07-17). LightGBM regression on realized closing-auction net_bps of the registered base events (MOC-max-t10-persist: threshold 0.001, persistence ON), expanding calendar walk-forward, FIXED gate `pred > 0`.

seed=7    features=16    model=LightGBM(lgbm.DEFAULT_PARAMS, objective=huber) on net_bps

Base events joined with PIT features (norm_imb & adv20$ reproduce the base file exactly, so this augments the already-evaluated events).

DATA-REALITY NOTE: Nasdaq closing-cross NOII disseminates only from 15:50:00 ET and near/far indicative prices are 0 until ~15:55. So at the registered 15:50:10 PIT instant the growth-vs-15:48/15:46, near-ref/near-far bps, near-drift and msg_count features are degenerate on real data (implemented exactly per the registered formula; see feature importances). Not a deviation — a property of the dissemination clock.

## 0. Feature-build funnel
```
{
  "rows": 6811,
  "built": 6811,
  "no_features": 0
}
```

## 1. Walk-forward folds (expanding, >=2y train, 6-month test blocks, 1-session embargo)
```
[
  {
    "test_start": "2022-01-02",
    "test_end": "2022-07-02",
    "n_train_sessions": 500,
    "n_test_sessions": 125
  },
  {
    "test_start": "2022-07-02",
    "test_end": "2023-01-02",
    "n_train_sessions": 625,
    "n_test_sessions": 125
  },
  {
    "test_start": "2023-01-02",
    "test_end": "2023-07-02",
    "n_train_sessions": 750,
    "n_test_sessions": 124
  },
  {
    "test_start": "2023-07-02",
    "test_end": "2024-01-02",
    "n_train_sessions": 874,
    "n_test_sessions": 124
  },
  {
    "test_start": "2024-01-02",
    "test_end": "2024-07-02",
    "n_train_sessions": 998,
    "n_test_sessions": 125
  },
  {
    "test_start": "2024-07-02",
    "test_end": "2025-01-02",
    "n_train_sessions": 1123,
    "n_test_sessions": 124
  },
  {
    "test_start": "2025-01-02",
    "test_end": "2025-07-02",
    "n_train_sessions": 1247,
    "n_test_sessions": 123
  },
  {
    "test_start": "2025-07-02",
    "test_end": "2026-01-02",
    "n_train_sessions": 1370,
    "n_test_sessions": 124
  },
  {
    "test_start": "2026-01-02",
    "test_end": "2026-07-02",
    "n_train_sessions": 1494,
    "n_test_sessions": 102
  }
]
```
OOS events (beyond initial-train span): 4757    OOS years: ['2022', '2023', '2024', '2025', '2026']

## 2. Gated vs ungated-same-span baseline (pooled, day-clustered 95% CI)

- UNGATED baseline (all OOS events):  mean=0.228  95%CI=[-1.047, 1.513]  n=4757  sessions=1096
- GATED (pred > 0) taken stream:      mean=0.108  95%CI=[-1.279, 1.542]  n=3866  sessions=1089

## 3. Registered anti-concentration prongs on the gated stream (diagnostic echo)
```
{
  "pooled_mean_net_bps": 0.108,
  "pooled_ci_lo": -1.279,
  "pooled_ci_hi": 1.542,
  "n_taken": 3866,
  "n_sessions": 1089,
  "symbols_spanned": [
    "AMD",
    "GOOGL",
    "MU",
    "NVDA",
    "TSLA"
  ],
  "n_symbols": 5,
  "years_spanned": [
    "2022",
    "2023",
    "2024",
    "2025",
    "2026"
  ],
  "n_years": 5,
  "meets_pooled_lo_gt_0": false,
  "meets_n_taken_ge_800": true,
  "meets_ge_3_symbols": true,
  "meets_ge_4_years": true
}
```

## 4. Gated per-symbol net_bps day-clustered CIs

| symbol | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi  |
|--------|----------|------------|--------------|--------|--------|
| AMD    | 685      | 685        | -0.115       | -2.663 | 2.688  |
| GOOGL  | 679      | 679        | -1.143       | -2.902 | 0.724  |
| MU     | 772      | 772        | -2.741       | -5.389 | -0.051 |
| NVDA   | 942      | 942        | 2.179        | -0.327 | 4.525  |
| TSLA   | 788      | 788        | 1.694        | -1.241 | 4.578  |
| POOLED | 3866     | 1089       | 0.108        | -1.279 | 1.542  |

## 5. Gated per-year net_bps day-clustered CIs

| year   | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|--------|----------|------------|--------------|--------|-------|
| 2022   | 1002     | 250        | -1.518       | -4.35  | 1.35  |
| 2023   | 740      | 244        | -1.431       | -3.946 | 1.142 |
| 2024   | 598      | 246        | 1.547        | -2.046 | 5.251 |
| 2025   | 1105     | 247        | 0.476        | -2.382 | 3.587 |
| 2026   | 421      | 102        | 3.671        | -0.169 | 7.614 |
| POOLED | 3866     | 1089       | 0.108        | -1.279 | 1.542 |

## 5b. Gated split-wise (train-period vs validate-period sessions)

| split    | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|----------|----------|------------|--------------|--------|-------|
| train    | 3620     | 1026       | -0.053       | -1.505 | 1.385 |
| validate | 246      | 63         | 2.478        | -2.793 | 8.217 |
| POOLED   | 3866     | 1089       | 0.108        | -1.279 | 1.542 |

## 6. Feature importances (mean LightGBM gain across folds)

| feature          | mean_gain   | n_folds |
|------------------|-------------|---------|
| vol20            | 4145.077302 | 9       |
| log_adv20        | 2043.853629 | 9       |
| norm_imb         | 669.155376  | 9       |
| paired_ratio     | 597.898227  | 9       |
| near_ref_bps     | 574.998371  | 9       |
| oh_NVDA          | 484.810928  | 9       |
| oh_GOOGL         | 280.644019  | 9       |
| side             | 97.657179   | 9       |
| oh_TSLA          | 58.806145   | 9       |
| near_far_bps     | 58.24566    | 9       |
| oh_AMD           | 32.108853   | 9       |
| oh_MU            | 21.127096   | 9       |
| imb_growth_48    | 0.0         | 9       |
| imb_growth_46    | 0.0         | 9       |
| near_drift_46_50 | 0.0         | 9       |
| msg_count        | 0.0         | 9       |

## 7. Prediction-weighted sizing view (REPORT-ONLY; w = clip(pred, 0, 10) bps)
```
{
  "weighted_mean_net_bps": 0.671,
  "n_weighted": 3866,
  "sum_weight": 6712.23,
  "cap_bps": 10.0
}
```

## 8. Ground-truth: 10 stratified gated fills (PROTOCOL v6.1)

entry_in_nbbo: entry fill within the prevailing NBBO at 15:50:10. cross_vs_close_bps: official cross print vs the session's daily close (~0 for a real cross; the cross IS the official close by construction).

| session    | symbol | side | norm_imb  | pred     | entry_bid | entry_ask | entry_px   | exit_reason | cross_px | bar_close | cross_vs_close_bps | entry_in_nbbo | net_bps     |
|------------|--------|------|-----------|----------|-----------|-----------|------------|-------------|----------|-----------|--------------------|---------------|-------------|
| 2022-09-02 | NVDA   | -1   | -0.001685 | 4.427302 | 136.55    | 136.58    | 136.673166 | moc         | 136.47   | null      | null               | true          | 14.565098   |
| 2022-09-06 | NVDA   | -1   | -0.014562 | 4.431147 | 135.05    | 135.12    | 135.103245 | moc         | 134.65   | null      | null               | true          | 33.24801    |
| 2024-08-06 | NVDA   | 1    | 0.005695  | 2.94731  | 105.74    | 105.76    | 105.695285 | moc         | 104.25   | 101.38    | 283.093312         | true          | -137.036577 |
| 2024-11-25 | TSLA   | -1   | -0.003849 | 3.216588 | 344.89    | 345.05    | 344.872755 | moc         | 338.59   | 334.41    | 124.996262         | true          | 181.876046  |
| 2024-12-20 | TSLA   | -1   | -0.06997  | 2.595881 | 429.65    | 429.81    | 428.57857  | moc         | 421.06   | 423.28    | -52.447552         | false         | 175.130377  |
| 2025-04-07 | TSLA   | -1   | -0.007217 | 0.597577 | 228.97    | 229.01    | 228.738563 | moc         | 233.29   | 239.5     | -259.290188        | false         | -199.279894 |
| 2025-04-07 | MU     | -1   | -0.029625 | 0.592143 | 67.33     | 67.37     | 67.316634  | moc         | 68.37    | 69.17     | -115.657077        | true          | -156.779303 |
| 2025-04-08 | MU     | 1    | 0.029119  | 0.592143 | 63.82     | 63.85     | 64.173209  | moc         | 65.54    | 64.33     | 188.092647         | false         | 212.678364  |
| 2025-06-27 | GOOGL  | 1    | 0.329227  | 0.593756 | 176.04    | 176.06    | 176.738837 | moc         | 178.53   | 177.62    | 51.232969          | false         | 101.042172  |
| 2026-05-29 | NVDA   | -1   | -0.22875  | 0.961974 | 214.73    | 214.81    | 214.559271 | moc         | 211.14   | 212.24    | -51.828119         | true          | 159.062561  |
