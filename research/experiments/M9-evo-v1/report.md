# M9 auction-evolution report — M9-evo-v1

Family `moc_meta_v1`, Cell A (registered 2026-07-17) — THE DECISIVE PROBE of the sequence-modeling thesis. The M8 meta-GBDT scores the classical |basis|>=10bps rule from a SNAPSHOT at 15:55:10 ET. M9 adds EXACTLY 5 registered PATH scalars over the legal decision window [15:50:00, 15:55:10] ET (imb_velocity, imb_accel, near_conv_slope, near_jitter, paired_frac_slope; winsorized 1/99 per fold) and retrains the SAME binary P(win) GBDT on the SAME walk-forward folds with the SAME gate. Snapshot-GBDT is the M8 baseline (identical folds/gate). Walk-forward OOS only (POST-HOLDOUT; forward paper is the sole clean validation). NO ledger writes; NO pass/fail verdict.

seed=7    snapshot_features=15    evo_features=+5 (imb_velocity, imb_accel, near_conv_slope, near_jitter, paired_frac_slope)    model=LightGBM(objective=binary) on y=(net_bps>0)
OOS span: 4735 candidates    symbols ['AMD', 'GOOGL', 'MU', 'NVDA', 'TSLA']    years ['2022', '2023', '2024', '2025', '2026']
Splits present: ['train', 'validate']

## 0. Funnel
```
{
  "events_rows": 7959,
  "candidates_basis_ge_10": 6198,
  "candidates_labeled": 6198,
  "candidates_dropped_null_net": 0,
  "evo_all_present_rows": 6195,
  "win_rate_all_candidates": 0.5415
}
```

## 1. Walk-forward folds (expanding, >=2y train, 6-mo blocks, 1-session embargo)

Identical fold builder to models/moc_gbm (reused). Each fold trains BOTH models on the SAME PIT train set, so the snapshot and evo OOS streams are paired row-for-row. Evo winsor bounds (1/99) are FIT on the train fold and applied to train+test — no test statistic touches a training bound.
```
[
  {
    "test_start": "2022-01-02",
    "test_end": "2022-07-02",
    "n_train": 491,
    "n_test": 125
  },
  {
    "test_start": "2022-07-02",
    "test_end": "2023-01-02",
    "n_train": 616,
    "n_test": 125
  },
  {
    "test_start": "2023-01-02",
    "test_end": "2023-07-02",
    "n_train": 741,
    "n_test": 124
  },
  {
    "test_start": "2023-07-02",
    "test_end": "2024-01-02",
    "n_train": 865,
    "n_test": 124
  },
  {
    "test_start": "2024-01-02",
    "test_end": "2024-07-02",
    "n_train": 989,
    "n_test": 125
  },
  {
    "test_start": "2024-07-02",
    "test_end": "2025-01-02",
    "n_train": 1114,
    "n_test": 124
  },
  {
    "test_start": "2025-01-02",
    "test_end": "2025-07-02",
    "n_train": 1238,
    "n_test": 123
  },
  {
    "test_start": "2025-07-02",
    "test_end": "2026-01-02",
    "n_train": 1361,
    "n_test": 124
  },
  {
    "test_start": "2026-01-02",
    "test_end": "2026-07-02",
    "n_train": 1485,
    "n_test": 102
  }
]
```

## 2. Headline comparison (q>=0.55) — baseline vs snapshot-GBDT vs evo-GBDT

SAME OOS span. net_bps mean CI day-clustered (session = cluster). Sharpe = per-trade mean/std. hit_rate = fraction net_bps>0.

| stream             | n_taken | n_sessions | hit_rate | net_bps_mean | ci_lo | ci_hi | net_bps_std | sharpe |
|--------------------|---------|------------|----------|--------------|-------|-------|-------------|--------|
| baseline (ungated) | 4735    | 1096       | 0.5364   | 2.21         | 1.503 | 2.928 | 19.366      | 0.1141 |
| snapshot q>=0.55   | 2844    | 1049       | 0.5774   | 4.031        | 3.109 | 5.003 | 20.623      | 0.1954 |
| evo q>=0.55        | 2821    | 1042       | 0.5814   | 3.932        | 2.958 | 4.919 | 20.686      | 0.1901 |

## 3. DECISIVE paired ablation (evo-GBDT vs snapshot-GBDT, same OOS)

Registered M9 success (Cell A): evo-gated (P>=0.55) net_bps CI-LOWER > the snapshot-gated MEAN, AND holds across >=3 symbols and >=3 years. Plus the per-session BOOK delta (evo - snapshot) on identical sessions (paired; day-clustered CI). If evo does NOT beat snapshot here, the sequence-modeling thesis is dead (documented, not hidden).
```
{
  "gate": 0.55,
  "snapshot_gated": {
    "n": 2844,
    "hit_rate": 0.5774,
    "net_mean": 4.031,
    "ci_lo": 3.109,
    "sharpe": 0.1954
  },
  "evo_gated": {
    "n": 2821,
    "hit_rate": 0.5814,
    "net_mean": 3.932,
    "ci_lo": 2.958,
    "sharpe": 0.1901,
    "n_symbols": 5,
    "n_years": 5
  },
  "evo_ci_lo_gt_snapshot_mean": false,
  "spans_ge_3_symbols_and_3_years": true,
  "REGISTERED_M9_SUCCESS": false
}
```

Per-session paired book-delta (evo - snapshot), each registered/context gate:
```
[
  {
    "gate": 0.5,
    "n_sessions": 1096,
    "evo_gated_n": 3836,
    "snap_gated_n": 4059,
    "per_session_book_delta_mean": 0.426,
    "per_session_book_delta_ci_lo": -0.2095,
    "per_session_book_delta_ci_hi": 1.0791,
    "book_delta_ci_lo_gt_0": false,
    "evo_gated_bps_mean": 3.204,
    "snap_gated_bps_mean": 2.913,
    "bps_mean_delta_evo_minus_snap": 0.291
  },
  {
    "gate": 0.55,
    "n_sessions": 1096,
    "evo_gated_n": 2821,
    "snap_gated_n": 2844,
    "per_session_book_delta_mean": -0.3389,
    "per_session_book_delta_ci_lo": -1.2222,
    "per_session_book_delta_ci_hi": 0.5492,
    "book_delta_ci_lo_gt_0": false,
    "evo_gated_bps_mean": 3.932,
    "snap_gated_bps_mean": 4.031,
    "bps_mean_delta_evo_minus_snap": -0.099
  },
  {
    "gate": 0.6,
    "n_sessions": 1096,
    "evo_gated_n": 1196,
    "snap_gated_n": 1238,
    "per_session_book_delta_mean": 0.0709,
    "per_session_book_delta_ci_lo": -0.8986,
    "per_session_book_delta_ci_hi": 1.0988,
    "book_delta_ci_lo_gt_0": false,
    "evo_gated_bps_mean": 4.821,
    "snap_gated_bps_mean": 4.595,
    "bps_mean_delta_evo_minus_snap": 0.226
  }
]
```

## 4. All gates side-by-side (snapshot vs evo at q in {0.50, 0.55, 0.60})

| stream             | n_taken | n_sessions | hit_rate | net_bps_mean | ci_lo | ci_hi | net_bps_std | sharpe |
|--------------------|---------|------------|----------|--------------|-------|-------|-------------|--------|
| baseline (ungated) | 4735    | 1096       | 0.5364   | 2.21         | 1.503 | 2.928 | 19.366      | 0.1141 |
| snapshot q>=0.55   | 2844    | 1049       | 0.5774   | 4.031        | 3.109 | 5.003 | 20.623      | 0.1954 |
| evo q>=0.55        | 2821    | 1042       | 0.5814   | 3.932        | 2.958 | 4.919 | 20.686      | 0.1901 |
| snapshot q>=0.50   | 4059    | 1093       | 0.5543   | 2.913        | 2.111 | 3.724 | 20.047      | 0.1453 |
| evo q>=0.50        | 3836    | 1089       | 0.5615   | 3.204        | 2.39  | 4.019 | 20.16       | 0.1589 |
| snapshot q>=0.60   | 1238    | 687        | 0.5953   | 4.595        | 3.233 | 6.08  | 20.225      | 0.2272 |
| evo q>=0.60        | 1196    | 679        | 0.5903   | 4.821        | 3.483 | 6.1   | 19.3        | 0.2498 |

## 5. Per-symbol (n + mean net_bps per stream)

| symbol | baseline    | baseline (ungated)|mean | snapshot  | snapshot     | evo q>=0.55|n | evo q>=0.55|mean | snapshot  | snapshot     | evo q>=0.50|n | evo q>=0.50|mean | snapshot q>=0.60|n | snapshot     | evo q>=0.60|n | evo q>=0.60|mean |
|        | (ungated)|n |                         | q>=0.55|n | q>=0.55|mean |               |                  | q>=0.50|n | q>=0.50|mean |               |                  |                    | q>=0.60|mean |               |                  |
|--------|-------------|-------------------------|-----------|--------------|---------------|------------------|-----------|--------------|---------------|------------------|--------------------|--------------|---------------|------------------|
| AMD    | 965         | 2.11                    | 638       | 3.24         | 633           | 3.11             | 870       | 2.43         | 834           | 2.74             | 290                | 4.23         | 290           | 4.01             |
| GOOGL  | 908         | -0.26                   | 323       | 1.53         | 363           | 1.39             | 611       | 0.85         | 569           | 0.87             | 99                 | 3.49         | 118           | 2.55             |
| MU     | 911         | 0.82                    | 569       | 2.07         | 550           | 2.11             | 782       | 1.39         | 731           | 1.6              | 228                | 2.7          | 224           | 1.95             |
| NVDA   | 972         | 4.42                    | 641       | 6.51         | 616           | 6.79             | 876       | 4.99         | 825           | 5.37             | 290                | 7.04         | 259           | 7.84             |
| TSLA   | 979         | 3.69                    | 673       | 5.27         | 659           | 4.98             | 920       | 4.05         | 877           | 4.46             | 331                | 4.41         | 305           | 6.02             |

## 6. Per-year (n + mean net_bps per stream)

| year | baseline    | baseline (ungated)|mean | snapshot  | snapshot     | evo q>=0.55|n | evo q>=0.55|mean | snapshot  | snapshot     | evo q>=0.50|n | evo q>=0.50|mean | snapshot q>=0.60|n | snapshot     | evo q>=0.60|n | evo q>=0.60|mean |
|      | (ungated)|n |                         | q>=0.55|n | q>=0.55|mean |               |                  | q>=0.50|n | q>=0.50|mean |               |                  |                    | q>=0.60|mean |               |                  |
|------|-------------|-------------------------|-----------|--------------|---------------|------------------|-----------|--------------|---------------|------------------|--------------------|--------------|---------------|------------------|
| 2022 | 987         | 3.62                    | 735       | 4.58         | 839           | 4.14             | 939       | 3.89         | 922           | 3.94             | 258                | 6.12         | 193           | 3.41             |
| 2023 | 1042        | 1.46                    | 599       | 3.62         | 546           | 3.51             | 879       | 2.2          | 773           | 2.7              | 247                | 3.96         | 324           | 4.6              |
| 2024 | 1112        | 1.87                    | 645       | 4.01         | 586           | 3.87             | 866       | 2.82         | 818           | 3.36             | 380                | 4.83         | 314           | 5.65             |
| 2025 | 1119        | 1.6                     | 671       | 2.58         | 641           | 2.91             | 938       | 2.35         | 939           | 2.35             | 353                | 3.68         | 333           | 4.18             |
| 2026 | 475         | 3.16                    | 194       | 8.31         | 209           | 7.5              | 437       | 3.61         | 384           | 4.19             | 0                  | null         | 32            | 14.07            |

## 7. evo-GBDT feature importances (mean LightGBM gain across folds)

Do the evo features rank above noise (the symbol one-hots / the weakest snapshot features are the noise floor)? Are they used at all?
evo features USED (gain>0): ['imb_velocity', 'imb_accel', 'near_conv_slope', 'near_jitter', 'paired_frac_slope']
evo feature ranks: [{"rank": 3, "feature": "near_jitter", "mean_gain": 143.30352647105852}, {"rank": 5, "feature": "imb_accel", "mean_gain": 110.24015335241954}, {"rank": 8, "feature": "near_conv_slope", "mean_gain": 79.48091289069917}, {"rank": 10, "feature": "imb_velocity", "mean_gain": 66.31200665897794}, {"rank": 11, "feature": "paired_frac_slope", "mean_gain": 64.22396669122908}]

| feature           | mean_gain  | n_folds | is_evo |
|-------------------|------------|---------|--------|
| paired_ratio      | 328.043732 | 9       | false  |
| vol20             | 210.478152 | 9       | false  |
| near_far_bps      | 170.623111 | 9       | false  |
| near_jitter       | 143.303526 | 9       | true   |
| norm_imb          | 131.042181 | 9       | false  |
| imb_accel         | 110.240153 | 9       | true   |
| log_adv20         | 106.234106 | 9       | false  |
| basis_bps         | 87.447631  | 9       | false  |
| near_conv_slope   | 79.480913  | 9       | true   |
| near_ref_bps      | 69.25397   | 9       | false  |
| imb_velocity      | 66.312007  | 9       | true   |
| paired_frac_slope | 64.223967  | 9       | true   |
| imb_growth_51     | 56.997171  | 9       | false  |
| imb_growth_53     | 43.388929  | 9       | false  |
| oh_NVDA           | 9.875756   | 9       | false  |
| oh_AMD            | 2.156829   | 9       | false  |
| oh_MU             | 1.768427   | 9       | false  |
| msg_count         | 0.0        | 9       | false  |
| oh_TSLA           | 0.0        | 9       | false  |
| oh_GOOGL          | 0.0        | 9       | false  |

## 8. Calibration — evo P(win) decile vs realized win rate (OOS)

Equal-count deciles by predicted evo P(win); realized_win_rate is the realized fraction of winners. Monotone rising => the score ranks reliability.

| bin | n   | pred_lo  | pred_hi  | pred_mean | realized_win_rate |
|-----|-----|----------|----------|-----------|-------------------|
| 0   | 474 | 0.315764 | 0.470297 | 0.435437  | 0.417722          |
| 1   | 473 | 0.470596 | 0.503017 | 0.487042  | 0.437632          |
| 2   | 474 | 0.503153 | 0.527945 | 0.515866  | 0.495781          |
| 3   | 473 | 0.527962 | 0.549358 | 0.538865  | 0.524313          |
| 4   | 474 | 0.549364 | 0.55551  | 0.554105  | 0.588608          |
| 5   | 473 | 0.55551  | 0.567708 | 0.56065   | 0.566596          |
| 6   | 474 | 0.567849 | 0.589184 | 0.577878  | 0.561181          |
| 7   | 473 | 0.589206 | 0.61187  | 0.600277  | 0.581395          |
| 8   | 474 | 0.611937 | 0.644521 | 0.62717   | 0.57384           |
| 9   | 473 | 0.644576 | 0.779533 | 0.672511  | 0.617336          |
