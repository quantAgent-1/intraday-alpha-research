# M11 cross-sectional OOS generalization report — M11-oos-28

Family `moc_imbalance_v1`, M11 cell (registered 2026-07-17 BEFORE download). The FROZEN near-vs-REF rule (registration's verified equivalent to the validated near-vs-mid rule: corr 0.9999) applied to 28 Nasdaq names it was NEVER fit on. PURE OUT-OF-SAMPLE: zero parameter changes, not a search. NO ledger writes; NO pass/fail verdict (the orchestrator owns the verdict).

Signal at 15:55:10 ET: near, ref = last NOII message with near>0 AND ref>0 (ref_price is the mid proxy — no quote feed); basis_bps = 1e4*(near-ref)/ref; FIRE iff |basis| >= 10; side = sign(near-ref). ENTRY = a CONSERVATIVE fixed taker cost: entry_px = ref*(1 + side*2.5bps) (2bps half-spread + 0.5bp slip). The 2bps half-spread is WIDER than the ~1bp these liquid names run, so this UNDERSTATES the edge vs the bbo-1s fills on the original 5. EXIT = official daily close. net via decompose.plan_pnl (SEC/TAF 0.3bp on the sell leg) — identical in spirit to the validated pipeline.

seed=7    universe=28 names    sessions in range (< holdout 2026-06-01): 854
Events fired (rows): 17747    years: ['2023', '2024', '2025', '2026']
Splits present: ['train', 'validate']

## 0. NOII coverage (fraction of the 28 names with a partition present)
```
{
  "n_total": 28,
  "n_present": 26,
  "present": [
    "AAPL",
    "ADBE",
    "AMAT",
    "AMGN",
    "AVGO",
    "CMCSA",
    "COST",
    "CSCO",
    "GILD",
    "HON",
    "INTC",
    "INTU",
    "ISRG",
    "KLAC",
    "LRCX",
    "MDLZ",
    "META",
    "MRVL",
    "MSFT",
    "NFLX",
    "PEP",
    "QCOM",
    "SBUX",
    "TMUS",
    "TXN",
    "VRTX"
  ],
  "missing": [
    "BKNG",
    "PLTR"
  ],
  "fraction": 0.9286
}
```

## 1. Event funnel / skipped-session counters
```
{
  "no_noii_partition": 2802,
  "no_noii_msgs": 199,
  "no_near_ref": 0,
  "zero_basis": 1209,
  "inactive": 1955,
  "no_close": 0,
  "fired": 17747
}
```

## 2. POOLED classical net_bps — day-clustered CI on the 28-name pool (pure OOS)

- Pooled (day-clustered): mean=-3.016  95%CI=[-3.458, -2.570]  n=17747  sessions=846
- Pooled CI-lower > 0 (registered pass prong): False

## 3. Per-symbol net_bps day-clustered CIs

| symbol | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi  |
|--------|----------|------------|--------------|--------|--------|
| AAPL   | 741      | 741        | -1.837       | -2.889 | -0.739 |
| ADBE   | 696      | 696        | -2.971       | -3.933 | -1.987 |
| AMAT   | 739      | 739        | -3.136       | -4.507 | -1.751 |
| AMGN   | 719      | 719        | -3.304       | -4.239 | -2.389 |
| AVGO   | 755      | 755        | -2.801       | -4.185 | -1.418 |
| CMCSA  | 694      | 694        | -3.414       | -4.298 | -2.511 |
| COST   | 680      | 680        | -3.125       | -3.883 | -2.449 |
| CSCO   | 653      | 653        | -3.139       | -3.941 | -2.301 |
| GILD   | 722      | 722        | -2.697       | -3.621 | -1.745 |
| HON    | 148      | 148        | -0.408       | -2.01  | 1.213  |
| INTC   | 739      | 739        | -3.887       | -5.413 | -2.396 |
| INTU   | 694      | 694        | -3.196       | -4.263 | -2.105 |
| ISRG   | 391      | 391        | -3.115       | -4.346 | -1.843 |
| KLAC   | 704      | 704        | -5.277       | -6.836 | -3.761 |
| LRCX   | 711      | 711        | -3.926       | -5.432 | -2.416 |
| MDLZ   | 723      | 723        | -3.459       | -4.223 | -2.668 |
| META   | 747      | 747        | -1.873       | -2.984 | -0.753 |
| MRVL   | 739      | 739        | -1.424       | -3.19  | 0.333  |
| MSFT   | 752      | 752        | -1.586       | -2.658 | -0.614 |
| NFLX   | 705      | 705        | -4.17        | -5.151 | -3.185 |
| PEP    | 681      | 681        | -2.238       | -2.949 | -1.513 |
| QCOM   | 756      | 756        | -3.012       | -4.289 | -1.709 |
| SBUX   | 702      | 702        | -2.507       | -3.559 | -1.467 |
| TMUS   | 715      | 715        | -2.575       | -3.364 | -1.758 |
| TXN    | 744      | 744        | -2.581       | -3.812 | -1.409 |
| VRTX   | 697      | 697        | -5.05        | -6.086 | -4.031 |
| POOLED | 17747    | 846        | -3.016       | -3.458 | -2.57  |

## 4. Per-SECTOR net_bps day-clustered CIs + majority-of-sectors prong

| sector   | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi  |
|----------|----------|------------|--------------|--------|--------|
| Comm     | 1409     | 823        | -2.988       | -3.573 | -2.396 |
| Consumer | 2786     | 845        | -2.839       | -3.283 | -2.374 |
| Health   | 2529     | 843        | -3.583       | -4.158 | -2.993 |
| MegaTech | 4335     | 846        | -2.579       | -3.182 | -1.986 |
| Other    | 148      | 148        | -0.408       | -2.01  | 1.213  |
| Semis    | 6540     | 846        | -3.228       | -3.967 | -2.455 |
| POOLED   | 17747    | 846        | -3.016       | -3.458 | -2.57  |

```
{
  "n_sectors_represented": 6,
  "n_sectors_net_positive": 0,
  "per_sector_point_estimate": {
    "Comm": -2.988,
    "Consumer": -2.839,
    "Health": -3.583,
    "MegaTech": -2.579,
    "Other": -0.408,
    "Semis": -3.228
  },
  "majority_of_sectors_positive": false
}
```

## 5. Event count vs registered threshold
```
{
  "n_events": 17747,
  "min_required": 500,
  "meets_ge_500": true
}
```

## 6. By-year net_bps day-clustered CIs

| year   | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi  |
|--------|----------|------------|--------------|--------|--------|
| 2023   | 4720     | 248        | -2.995       | -3.738 | -2.276 |
| 2024   | 5139     | 249        | -2.358       | -3.134 | -1.512 |
| 2025   | 5476     | 247        | -3.879       | -4.892 | -2.956 |
| 2026   | 2412     | 102        | -2.502       | -3.426 | -1.572 |
| POOLED | 17747    | 846        | -3.016       | -3.458 | -2.57  |

## 7. META-TRANSFER — M8 meta model trained ONLY on the original 5 (frozen)

The M8 LightGBM reliability model is trained on the 5-name |basis|>=10 candidate universe (frozen; symbol one-hots are the 5 originals, all-zero for every M11 name) and applied to the 28-name candidates. Does gating by the 5-name-trained P(win) >= 0.55 improve the 28-name hit rate? This tests whether the meta learned a TRANSFERABLE reliability signal or overfit to 5 names.
```
{
  "available": true,
  "gate": 0.55,
  "five_name_events": "research\\experiments\\M6-FINAL-basis\\events.parquet",
  "n_5name_train_candidates": 6198,
  "n_28name_candidates": 17747,
  "n_gated": 6588,
  "ungated_hit_rate": 0.3942,
  "gated_hit_rate": 0.4372,
  "hit_rate_improved": true,
  "ungated_net_bps_mean": -3.016,
  "gated_net_bps_mean": -1.838,
  "ungated_ci_lo": -3.458,
  "gated_ci_lo": -2.561,
  "mean_p_win": 0.5167
}
```

## 8. PROTOCOL v6.1 ground-truthing — 10 stratified events (near/ref vs daily close)

entry_cost_bps: realized signed entry cost vs ref (must equal the fixed 2.5bps conservative taker cost). ref_vs_close_bps: how far ref sat from the official close (the move captured toward). net_bps: the realized decomposed pnl.

| session    | symbol | sector   | side | near_price | ref_price | basis_bps   | entry_px   | entry_cost_bps | bar_close | ref_vs_close_bps | net_bps     |
|------------|--------|----------|------|------------|-----------|-------------|------------|----------------|-----------|------------------|-------------|
| 2024-01-09 | MRVL   | Semis    | -1   | 57.07      | 63.41     | -999.842296 | 63.394147  | 2.5            | 63.47     | 9.46223          | -12.265221  |
| 2024-07-17 | MRVL   | Semis    | -1   | 67.74      | 68.58     | -122.484689 | 68.562855  | 2.5            | 67.93     | -94.779819       | 92.002895   |
| 2024-08-05 | MRVL   | Semis    | 1    | 58.0       | 57.0      | 175.438596  | 57.01425   | 2.5            | 57.67     | 117.54386        | 114.711655  |
| 2025-04-07 | INTC   | Semis    | 1    | 19.65      | 19.36     | 149.793388  | 19.36484   | 2.5            | 19.57     | 108.471074       | 105.64141   |
| 2025-04-08 | LRCX   | Semis    | -1   | 57.04      | 59.5      | -413.445378 | 59.485125  | 2.5            | 60.25     | 126.05042        | -128.882566 |
| 2025-04-08 | MRVL   | Semis    | -1   | 48.34      | 49.16     | -166.802278 | 49.14771   | 2.5            | 50.03     | 176.973149       | -179.818028 |
| 2025-04-09 | TXN    | Semis    | 1    | 189.8      | 172.55    | 999.710229  | 172.593138 | 2.5            | 169.5     | -176.760359      | -179.510179 |
| 2025-04-30 | LRCX   | Semis    | 1    | 78.77      | 71.61     | 999.860355  | 71.627903  | 2.5            | 71.67     | 8.378718         | 5.577072    |
| 2025-12-01 | CSCO   | Semis    | -1   | 68.41      | 76.01     | -999.868438 | 75.990998  | 2.5            | 76.04     | 3.946849         | -6.748461   |
| 2026-02-12 | PEP    | Consumer | -1   | 150.51     | 167.23    | -999.820606 | 167.188192 | 2.5            | 167.2     | -1.793936        | -1.00624    |
