# M8 meta-labeling report — M8-meta-v1

Family `moc_meta_v1` (registered 2026-07-17). META-LABELING on the classical |basis|>=10bps rule at 15:55:10 ET (direction UNCHANGED = sign(near-mid)). A LightGBM BINARY classifier predicts P(net_bps>0) per candidate from reliability features; a registered gate TAKEs iff P(win) >= q, q in {0.50, 0.55, 0.60}. Walk-forward OOS only (POST-HOLDOUT: the seal was spent by M6-FINAL; forward paper is the sole clean validation). NO ledger writes; NO pass/fail verdict.

seed=7    features=15 (reliability set, NO `side`)    model=LightGBM(lgbm.DEFAULT_PARAMS, objective=binary) on y=(net_bps>0)
OOS span: 4735 candidates    symbols ['AMD', 'GOOGL', 'MU', 'NVDA', 'TSLA']    years ['2022', '2023', '2024', '2025', '2026']
Splits present: ['train', 'validate']

## 0. Meta-frame funnel
```
{
  "events_rows": 7959,
  "candidates_basis_ge_10": 6198,
  "candidates_labeled": 6198,
  "candidates_dropped_null_net": 0,
  "win_rate_all_candidates": 0.5415
}
```

## 1. Walk-forward folds (expanding, >=2y train, 6-mo blocks, 1-session embargo)

Identical fold builder to models/moc_gbm (reused, not re-implemented); a fold model trains strictly on candidate sessions before its test block (minus the 1-session embargo).
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

## 2. Comparison — baseline (ungated classical) vs each gate, SAME OOS span

net_bps mean CI is day-clustered (session = cluster unit). Sharpe = per-trade mean/std. hit_rate = fraction with net_bps > 0.

| stream   | n_taken | n_sessions | hit_rate | net_bps_mean | ci_lo | ci_hi | net_bps_std | sharpe |
|----------|---------|------------|----------|--------------|-------|-------|-------------|--------|
| baseline | 4735    | 1096       | 0.5364   | 2.21         | 1.503 | 2.928 | 19.366      | 0.1141 |
| q>=0.50  | 4059    | 1093       | 0.5543   | 2.913        | 2.111 | 3.724 | 20.047      | 0.1453 |
| q>=0.55  | 2844    | 1049       | 0.5774   | 4.031        | 3.109 | 5.003 | 20.623      | 0.1954 |
| q>=0.60  | 1238    | 687        | 0.5953   | 4.595        | 3.233 | 6.08  | 20.225      | 0.2272 |

## 3. Registered success criteria (diagnostic echo — orchestrator owns the verdict)

Registered M8 success (honest, post-holdout): hit-rate improves AND (net mean CI-lower > classical mean OR Sharpe improves >=20%) AND holds across >=3 symbols and >=3 years.
```
{
  "baseline": {
    "hit_rate": 0.5364,
    "net_bps_mean": 2.21,
    "sharpe": 0.1141
  },
  "gates": {
    "q>=0.50": {
      "n_taken": 4059,
      "hit_rate": 0.5543,
      "hit_rate_improved": true,
      "net_mean_ci_lo": 2.111,
      "ci_lo_gt_classical_mean": false,
      "sharpe": 0.1453,
      "sharpe_improved_ge_20pct": true,
      "n_symbols": 5,
      "n_years": 5,
      "spans_ge_3_symbols_and_3_years": true
    },
    "q>=0.55": {
      "n_taken": 2844,
      "hit_rate": 0.5774,
      "hit_rate_improved": true,
      "net_mean_ci_lo": 3.109,
      "ci_lo_gt_classical_mean": true,
      "sharpe": 0.1954,
      "sharpe_improved_ge_20pct": true,
      "n_symbols": 5,
      "n_years": 5,
      "spans_ge_3_symbols_and_3_years": true
    },
    "q>=0.60": {
      "n_taken": 1238,
      "hit_rate": 0.5953,
      "hit_rate_improved": true,
      "net_mean_ci_lo": 3.233,
      "ci_lo_gt_classical_mean": true,
      "sharpe": 0.2272,
      "sharpe_improved_ge_20pct": true,
      "n_symbols": 5,
      "n_years": 4,
      "spans_ge_3_symbols_and_3_years": true
    }
  }
}
```

## 4. Per-symbol (n + mean net_bps per stream)

| symbol | baseline|n | baseline|mean | q>=0.50|n | q>=0.50|mean | q>=0.55|n | q>=0.55|mean | q>=0.60|n | q>=0.60|mean |
|--------|------------|---------------|-----------|--------------|-----------|--------------|-----------|--------------|
| AMD    | 965        | 2.11          | 870       | 2.43         | 638       | 3.24         | 290       | 4.23         |
| GOOGL  | 908        | -0.26         | 611       | 0.85         | 323       | 1.53         | 99        | 3.49         |
| MU     | 911        | 0.82          | 782       | 1.39         | 569       | 2.07         | 228       | 2.7          |
| NVDA   | 972        | 4.42          | 876       | 4.99         | 641       | 6.51         | 290       | 7.04         |
| TSLA   | 979        | 3.69          | 920       | 4.05         | 673       | 5.27         | 331       | 4.41         |

## 5. Per-year (n + mean net_bps per stream)

| year | baseline|n | baseline|mean | q>=0.50|n | q>=0.50|mean | q>=0.55|n | q>=0.55|mean | q>=0.60|n | q>=0.60|mean |
|------|------------|---------------|-----------|--------------|-----------|--------------|-----------|--------------|
| 2022 | 987        | 3.62          | 939       | 3.89         | 735       | 4.58         | 258       | 6.12         |
| 2023 | 1042       | 1.46          | 879       | 2.2          | 599       | 3.62         | 247       | 3.96         |
| 2024 | 1112       | 1.87          | 866       | 2.82         | 645       | 4.01         | 380       | 4.83         |
| 2025 | 1119       | 1.6           | 938       | 2.35         | 671       | 2.58         | 353       | 3.68         |
| 2026 | 475        | 3.16          | 437       | 3.61         | 194       | 8.31         | 0         | null         |

## 6. P(win)-proportional sizing overlay (REPORT-ONLY $ view; PROTOCOL v6 §3)

$10k research book. equal = flat $10k/plan; p_win = notional proportional to P(win), average notional held at $10k (pure reallocation of the SAME taken stream toward higher-confidence plans). Never a gate or training objective.

| stream   | n    | equal_pnl_$ | pwin_pnl_$ | equal_bps | pwin_bps |
|----------|------|-------------|------------|-----------|----------|
| baseline | 4735 | 10464.69    | 11659.81   | 2.21      | 2.462    |
| q>=0.50  | 4059 | 11822.74    | 12383.5    | 2.913     | 3.051    |
| q>=0.55  | 2844 | 11463.68    | 11595.5    | 4.031     | 4.077    |
| q>=0.60  | 1238 | 5688.47     | 5734.64    | 4.595     | 4.632    |

## 7. Feature importances (mean LightGBM gain across folds)

| feature       | mean_gain  | n_folds |
|---------------|------------|---------|
| paired_ratio  | 313.827246 | 9       |
| vol20         | 213.485276 | 9       |
| near_far_bps  | 183.241587 | 9       |
| log_adv20     | 134.193747 | 9       |
| norm_imb      | 128.415188 | 9       |
| imb_growth_53 | 90.556416  | 9       |
| basis_bps     | 88.310922  | 9       |
| near_ref_bps  | 86.720964  | 9       |
| imb_growth_51 | 84.949665  | 9       |
| oh_NVDA       | 15.177694  | 9       |
| oh_AMD        | 1.785729   | 9       |
| oh_MU         | 1.763773   | 9       |
| oh_TSLA       | 1.26652    | 9       |
| oh_GOOGL      | 0.225012   | 9       |
| msg_count     | 0.0        | 9       |

## 8. Calibration — predicted P(win) decile vs realized win rate (baseline OOS)

Equal-count deciles by predicted P(win); realized_win_rate is the realized fraction of winners in the bin. Monotone rising ⇒ the score ranks reliability.

| bin | n   | pred_lo  | pred_hi  | pred_mean | realized_win_rate |
|-----|-----|----------|----------|-----------|-------------------|
| 0   | 474 | 0.348711 | 0.485277 | 0.444505  | 0.424051          |
| 1   | 473 | 0.485349 | 0.515757 | 0.501985  | 0.427061          |
| 2   | 474 | 0.515841 | 0.535302 | 0.526121  | 0.523207          |
| 3   | 473 | 0.535346 | 0.550031 | 0.543035  | 0.522199          |
| 4   | 474 | 0.550135 | 0.562562 | 0.55674   | 0.575949          |
| 5   | 473 | 0.562601 | 0.576551 | 0.569321  | 0.547569          |
| 6   | 474 | 0.576551 | 0.592552 | 0.584681  | 0.552743          |
| 7   | 473 | 0.592765 | 0.611873 | 0.602457  | 0.579281          |
| 8   | 474 | 0.612052 | 0.643165 | 0.625232  | 0.57384           |
| 9   | 473 | 0.643267 | 0.750584 | 0.672188  | 0.638478          |

## 9. PROTOCOL v6.1 ground-truthing — 10 stratified gated events (join-correctness)

Confirming the join for the `q>=0.60` gated stream (economics already fill-verified upstream in M6-FINAL). entry_in_nbbo: entry fill within the prevailing NBBO at 15:55:10. cross_vs_close_bps: cross print vs the official daily close (~0 confirms the cross IS the official close). net_bps + y_meta echo the labeled economics.

| session    | symbol | side | basis_bps   | p_win    | entry_mid | entry_bid | entry_ask | entry_px   | entry_in_nbbo | cross_px | bar_close | cross_vs_close_bps | net_bps    | y_meta |
|------------|--------|------|-------------|----------|-----------|-----------|-----------|------------|---------------|----------|-----------|--------------------|------------|--------|
| 2022-01-28 | MU     | 1    | 995.945261  | 0.601146 | 78.92     | 78.91     | 78.93     | 79.00395   | true          | 79.27    | null      | null               | 33.374521  | 1      |
| 2023-09-20 | TSLA   | -1   | -111.388952 | 0.735176 | 263.94    | 263.93    | 263.95    | 264.026798 | true          | 262.59   | 263.0599  | -17.862852         | 54.118643  | 1      |
| 2023-10-18 | AMD    | -1   | -128.474427 | 0.750584 | 102.355   | 102.35    | 102.36    | 102.334883 | true          | 102.17   | 102.1     | 6.856024           | 15.812101  | 1      |
| 2024-08-01 | NVDA   | -1   | -134.425928 | 0.65264  | 108.61    | 108.6     | 108.62    | 108.444578 | false         | 109.21   | 107.92    | 119.532987         | -70.881906 | 0      |
| 2024-12-18 | NVDA   | -1   | -285.889008 | 0.601764 | 130.82    | 130.81    | 130.83    | 130.543473 | false         | 128.91   | 131.3     | -182.025895        | 124.828623 | 1      |
| 2024-12-18 | MU     | -1   | -444.772846 | 0.601678 | 104.885   | 104.86    | 104.91    | 104.734763 | false         | 103.9    | 86.67     | 1988.000462        | 79.402572  | 1      |
| 2025-02-05 | NVDA   | -1   | -52.820451  | 0.609515 | 124.005   | 124.0     | 124.01    | 124.003799 | true          | 124.83   | 124.47    | 28.922632          | -66.927031 | 0      |
| 2025-03-11 | NVDA   | -1   | -135.252061 | 0.611469 | 109.795   | 109.79    | 109.8     | 109.774511 | true          | 108.76   | 109.27    | -46.673378         | 92.11772   | 1      |
| 2025-05-01 | TSLA   | 1    | 55.506452   | 0.61248  | 282.85    | 282.82    | 282.88    | 282.664132 | true          | 280.52   | 277.5389  | 107.41197          | -76.152149 | 0      |
| 2025-06-27 | GOOGL  | 1    | 1000.647395 | 0.603002 | 177.635   | 177.62    | 177.65    | 177.898895 | false         | 178.53   | 177.62    | 51.232969          | 35.174451  | 1      |
