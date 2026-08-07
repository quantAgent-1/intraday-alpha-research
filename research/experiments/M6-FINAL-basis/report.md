# M6-FINAL near-price basis report — M6-FINAL-basis

Family `moc_imbalance_v1`, M6-FINAL cell (registered 2026-07-17) — THE FAMILY'S LAST EXPERIMENT (the family closes after this run, pass or fail). Signal at 15:55:10 ET: basis_bps = 1e4 * (near - mid)/mid, near = last NOII message at-or-before 15:55:10 with near_price>0, mid = prevailing bbo-1s mid. Direction WITH the basis (buy iff near>mid). Entry = taker market at 15:55:10 + U[5,25]s latency (bbo-1s cross + 0.5bp slip); exit AT the official closing cross. Net via decompose.plan_pnl (SEC/TAF 0.3bp on the sell leg). NO ledger writes; NO pass/fail interpretation.

Symbols: NVDA, TSLA, AMD, MU, GOOGL    seed=7
Sessions in range (< holdout 2026-06-01): 1610
ALL-events universe (valid basis + cross): 7959 events    years: ['2020', '2021', '2022', '2023', '2024', '2025', '2026']
Splits present: ['train', 'validate']

DATA-REALITY (VERIFIED on the owned tape, documented per task): NOII near/far indicative prices are 0 until ~15:55:00 ET; near first turns >0 at exactly 15:55:00 across the full 2020->2026 span. At 15:55:10 there are ~40 disseminated messages with near/far/ref all populated, so the basis is well defined every covered session. Growth vs 15:53/15:51 is meaningful (imbalance shares evolve; at 15:53/15:51 near is still 0 so norm_imb there uses signal_at's near->ref price fallback). near_drift_51_55 DEGENERATES to 0 (near=0 at 15:51) — computed exactly per formula; see importances.

## 1. Event funnel / skipped-session counters
```
{
  "no_noii_partition": 0,
  "no_noii_msgs": 60,
  "no_near": 0,
  "no_bbo": 0,
  "no_mid": 0,
  "zero_basis": 31,
  "no_adv": 0,
  "no_cross": 0,
  "void": 0,
  "events": 7959
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

## 2. Classical cell |basis_bps| >= 5

### |basis| >= 5 bps

- Pooled (day-clustered): mean=2.152  95%CI=[1.532, 2.807]  n=6740  sessions=1597

Per-symbol:

| symbol | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|--------|----------|------------|--------------|--------|-------|
| AMD    | 1411     | 1411       | 2.185        | 1.044  | 3.289 |
| GOOGL  | 1267     | 1267       | -0.384       | -1.262 | 0.461 |
| MU     | 1264     | 1264       | 1.455        | 0.225  | 2.782 |
| NVDA   | 1350     | 1350       | 3.84         | 2.582  | 5.197 |
| TSLA   | 1448     | 1448       | 3.374        | 2.243  | 4.603 |
| POOLED | 6740     | 1597       | 2.152        | 1.532  | 2.807 |

Per-year:

| year   | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|--------|----------|------------|--------------|--------|-------|
| 2020   | 882      | 251        | 3.151        | 0.477  | 6.16  |
| 2021   | 875      | 250        | 1.943        | 0.628  | 3.358 |
| 2022   | 1070     | 250        | 3.117        | 1.359  | 4.909 |
| 2023   | 1114     | 248        | 1.211        | -0.024 | 2.338 |
| 2024   | 1153     | 249        | 1.743        | 0.43   | 3.193 |
| 2025   | 1160     | 247        | 1.585        | 0.085  | 3.075 |
| 2026   | 486      | 102        | 3.072        | 1.089  | 5.02  |
| POOLED | 6740     | 1597       | 2.152        | 1.532  | 2.807 |

Stiffened prongs (>=3/5 symbols positive AND >=4/7 years positive):

```
{
  "pooled_mean_net_bps": 2.152,
  "pooled_ci_lo": 1.532,
  "pooled_ci_hi": 2.807,
  "n_events": 6740,
  "n_sessions": 1597,
  "symbols_positive_point_estimate": 4,
  "per_symbol_point_estimate": {
    "AMD": 2.185,
    "GOOGL": -0.384,
    "MU": 1.455,
    "NVDA": 3.84,
    "TSLA": 3.374
  },
  "years_positive_point_estimate": 7,
  "per_year_point_estimate": {
    "2020": 3.151,
    "2021": 1.943,
    "2022": 3.117,
    "2023": 1.211,
    "2024": 1.743,
    "2025": 1.585,
    "2026": 3.072
  },
  "meets_pooled_lo_gt_0": true,
  "meets_ge_3_of_5_symbols_positive": true,
  "meets_ge_4_of_7_years_positive": true
}
```

## 3. Classical cell |basis_bps| >= 10

### |basis| >= 10 bps

- Pooled (day-clustered): mean=2.483  95%CI=[1.854, 3.178]  n=6198  sessions=1588

Per-symbol:

| symbol | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|--------|----------|------------|--------------|--------|-------|
| AMD    | 1293     | 1293       | 2.535        | 1.323  | 3.831 |
| GOOGL  | 1144     | 1144       | 0.076        | -0.865 | 0.996 |
| MU     | 1177     | 1177       | 1.475        | 0.173  | 2.696 |
| NVDA   | 1245     | 1245       | 4.322        | 3.038  | 5.696 |
| TSLA   | 1339     | 1339       | 3.664        | 2.481  | 4.882 |
| POOLED | 6198     | 1588       | 2.483        | 1.854  | 3.178 |

Per-year:

| year   | n_events | n_sessions | net_bps_mean | ci_lo | ci_hi |
|--------|----------|------------|--------------|-------|-------|
| 2020   | 717      | 247        | 4.209        | 1.19  | 7.477 |
| 2021   | 746      | 245        | 2.554        | 1.118 | 4.06  |
| 2022   | 987      | 250        | 3.624        | 1.784 | 5.487 |
| 2023   | 1042     | 248        | 1.457        | 0.171 | 2.654 |
| 2024   | 1112     | 249        | 1.866        | 0.519 | 3.327 |
| 2025   | 1119     | 247        | 1.604        | 0.153 | 3.087 |
| 2026   | 475      | 102        | 3.156        | 1.158 | 5.102 |
| POOLED | 6198     | 1588       | 2.483        | 1.854 | 3.178 |

Stiffened prongs (>=3/5 symbols positive AND >=4/7 years positive):

```
{
  "pooled_mean_net_bps": 2.483,
  "pooled_ci_lo": 1.854,
  "pooled_ci_hi": 3.178,
  "n_events": 6198,
  "n_sessions": 1588,
  "symbols_positive_point_estimate": 5,
  "per_symbol_point_estimate": {
    "AMD": 2.535,
    "GOOGL": 0.076,
    "MU": 1.475,
    "NVDA": 4.322,
    "TSLA": 3.664
  },
  "years_positive_point_estimate": 7,
  "per_year_point_estimate": {
    "2020": 4.209,
    "2021": 2.554,
    "2022": 3.624,
    "2023": 1.457,
    "2024": 1.866,
    "2025": 1.604,
    "2026": 3.156
  },
  "meets_pooled_lo_gt_0": true,
  "meets_ge_3_of_5_symbols_positive": true,
  "meets_ge_4_of_7_years_positive": true
}
```

## 4. GBM cell (LightGBM regression on ALL-events net, fixed gate pred>0)

Model: LightGBM (lgbm.DEFAULT_PARAMS, objective=huber) on event net_bps; expanding calendar walk-forward (>=2y initial train, 6-month test blocks, 1-session embargo); FIXED gate pred>0. Features: the registered M6-GBM set recomputed at 15:55:10 + basis_bps (17 cols).

Walk-forward folds:
```
[
  {
    "test_start": "2022-01-02",
    "test_end": "2022-07-02",
    "n_train_sessions": 501,
    "n_test_sessions": 125
  },
  {
    "test_start": "2022-07-02",
    "test_end": "2023-01-02",
    "n_train_sessions": 626,
    "n_test_sessions": 125
  },
  {
    "test_start": "2023-01-02",
    "test_end": "2023-07-02",
    "n_train_sessions": 751,
    "n_test_sessions": 124
  },
  {
    "test_start": "2023-07-02",
    "test_end": "2024-01-02",
    "n_train_sessions": 875,
    "n_test_sessions": 124
  },
  {
    "test_start": "2024-01-02",
    "test_end": "2024-07-02",
    "n_train_sessions": 999,
    "n_test_sessions": 125
  },
  {
    "test_start": "2024-07-02",
    "test_end": "2025-01-02",
    "n_train_sessions": 1124,
    "n_test_sessions": 124
  },
  {
    "test_start": "2025-01-02",
    "test_end": "2025-07-02",
    "n_train_sessions": 1248,
    "n_test_sessions": 123
  },
  {
    "test_start": "2025-07-02",
    "test_end": "2026-01-02",
    "n_train_sessions": 1371,
    "n_test_sessions": 124
  },
  {
    "test_start": "2026-01-02",
    "test_end": "2026-07-02",
    "n_train_sessions": 1495,
    "n_test_sessions": 102
  }
]
```
OOS events (beyond initial-train span): 5467    GATED (pred>0) taken: 4409

- UNGATED same-span baseline (all OOS events): mean=1.638  95%CI=[1.013, 2.299]  n=5467  sessions=1096
- GATED (pred>0) taken stream:                 mean=2.547  95%CI=[1.838, 3.290]  n=4409  sessions=1096

### GBM-gated (pred > 0) taken stream

- Pooled (day-clustered): mean=2.547  95%CI=[1.838, 3.290]  n=4409  sessions=1096

Per-symbol:

| symbol | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi |
|--------|----------|------------|--------------|--------|-------|
| AMD    | 944      | 944        | 2.138        | 0.964  | 3.361 |
| GOOGL  | 726      | 726        | 0.371        | -0.616 | 1.343 |
| MU     | 864      | 864        | 1.233        | -0.126 | 2.691 |
| NVDA   | 918      | 918        | 4.727        | 3.294  | 6.219 |
| TSLA   | 957      | 957        | 3.697        | 2.416  | 4.937 |
| POOLED | 4409     | 1096       | 2.547        | 1.838  | 3.29  |

Per-year:

| year   | n_events | n_sessions | net_bps_mean | ci_lo | ci_hi |
|--------|----------|------------|--------------|-------|-------|
| 2022   | 1028     | 250        | 3.473        | 1.705 | 5.268 |
| 2023   | 937      | 248        | 1.943        | 0.535 | 3.225 |
| 2024   | 963      | 249        | 2.537        | 1.078 | 4.154 |
| 2025   | 971      | 247        | 1.926        | 0.414 | 3.512 |
| 2026   | 510      | 102        | 2.994        | 1.064 | 4.955 |
| POOLED | 4409     | 1096       | 2.547        | 1.838 | 3.29  |

Stiffened prongs (>=3/5 symbols positive AND >=4/7 years positive):

```
{
  "pooled_mean_net_bps": 2.547,
  "pooled_ci_lo": 1.838,
  "pooled_ci_hi": 3.29,
  "n_events": 4409,
  "n_sessions": 1096,
  "symbols_positive_point_estimate": 5,
  "per_symbol_point_estimate": {
    "AMD": 2.138,
    "GOOGL": 0.371,
    "MU": 1.233,
    "NVDA": 4.727,
    "TSLA": 3.697
  },
  "years_positive_point_estimate": 5,
  "per_year_point_estimate": {
    "2022": 3.473,
    "2023": 1.943,
    "2024": 2.537,
    "2025": 1.926,
    "2026": 2.994
  },
  "meets_pooled_lo_gt_0": true,
  "meets_ge_3_of_5_symbols_positive": true,
  "meets_ge_4_of_7_years_positive": true
}
```

## 5. GBM feature importances (mean LightGBM gain across folds)

| feature          | mean_gain   | n_folds |
|------------------|-------------|---------|
| paired_ratio     | 7258.084191 | 9       |
| basis_bps        | 3404.503083 | 9       |
| vol20            | 3377.685158 | 9       |
| near_far_bps     | 2518.678348 | 9       |
| norm_imb         | 2198.919175 | 9       |
| near_ref_bps     | 2138.070645 | 9       |
| log_adv20        | 1548.268164 | 9       |
| imb_growth_51    | 849.157027  | 9       |
| imb_growth_53    | 709.55112   | 9       |
| oh_NVDA          | 233.375988  | 9       |
| side             | 33.769422   | 9       |
| oh_GOOGL         | 29.808842   | 9       |
| oh_TSLA          | 8.831108    | 9       |
| oh_AMD           | 8.339378    | 9       |
| oh_MU            | 5.193127    | 9       |
| near_drift_51_55 | 0.0         | 9       |
| msg_count        | 0.0         | 9       |

## 6. PROTOCOL v6.1 ground-truthing — 10 stratified events (near vs mid vs cross vs realized)

near_price: NOII indicative clearing price. entry_mid: prevailing bbo-1s mid at 15:55:10. basis_bps: near vs mid. entry_in_nbbo: entry fill within the prevailing NBBO. cross_vs_mid_bps: realized clearing (cross) vs the market mid. cross_vs_close_bps: cross vs the official daily close (0 confirms the daily-close cross source, RTH fetch excludes the 16:00 print). basis_agrees_cross: did sign(near-mid) predict sign(cross-mid).

| session    | symbol | side | near_price | entry_mid | basis_bps    | entry_bid | entry_ask | entry_px    | entry_in_nbbo | cross_px | cross_vs_mid_bps | bar_close | cross_vs_close_bps | basis_agrees_cross | net_bps     |
|------------|--------|------|------------|-----------|--------------|-----------|-----------|-------------|---------------|----------|------------------|-----------|--------------------|--------------------|-------------|
| 2020-03-12 | NVDA   | 1    | 221.5      | 220.91    | 26.707709    | 220.85    | 220.97    | 220.041002  | false         | 216.31   | -208.229596      | null      | null               | false              | -169.85429  |
| 2020-03-12 | AMD    | 1    | 39.93      | 39.755    | 44.01962     | 39.75     | 39.76     | 39.741987   | true          | 39.01    | -187.397812      | null      | null               | false              | -184.479276 |
| 2020-03-13 | AMD    | 1    | 42.75      | 42.595    | 36.389248    | 42.58     | 42.61     | 42.642132   | true          | 43.8862  | 303.134171       | null      | null               | true               | 291.437448  |
| 2020-03-13 | MU     | 1    | 43.0       | 41.895    | 263.754625   | 41.89     | 41.9      | 41.942097   | false         | 42.99    | 261.367705       | null      | null               | true               | 249.537666  |
| 2020-03-13 | GOOGL  | -1   | 1192.0     | 1193.525  | -12.777277   | 1192.97   | 1194.08   | 1193.870304 | true          | 1214.27  | 173.812865       | null      | null               | false              | -171.17029  |
| 2020-03-16 | NVDA   | -1   | 199.97     | 201.195   | -60.886205   | 201.19    | 201.2     | 200.98995   | true          | 196.4    | -238.326002      | null      | null               | true               | 228.06714   |
| 2020-06-26 | AMD    | -1   | 44.77      | 49.775    | -1005.524862 | 49.77     | 49.78     | 49.737513   | true          | 50.1     | 65.293822        | null      | null               | false              | -73.180001  |
| 2022-02-14 | AMD    | -1   | 103.2      | 114.635   | -997.513848  | 114.63    | 114.64    | 114.60427   | true          | 114.27   | -31.840188       | null      | null               | true               | 28.867282   |
| 2025-06-27 | GOOGL  | 1    | 195.41     | 177.635   | 1000.647395  | 177.62    | 177.65    | 177.898895  | false         | 178.53   | 50.384215        | 177.62    | 51.232969          | true               | 35.174451   |
| 2026-05-08 | AMD    | 1    | 501.68     | 456.03    | 1001.030634  | 455.96    | 456.1     | 455.592779  | true          | 455.19   | -18.419841       | 461.1995  | -130.301529        | false              | -9.140492   |

## 7. Exit-reason distribution (ALL events)

| exit_reason | count |
|-------------|-------|
| moc         | 7959  |
