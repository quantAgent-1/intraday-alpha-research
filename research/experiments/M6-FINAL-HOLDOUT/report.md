# M6-FINAL near-price basis report — M6-FINAL-HOLDOUT

Family `moc_imbalance_v1`, M6-FINAL cell (registered 2026-07-17) — THE FAMILY'S LAST EXPERIMENT (the family closes after this run, pass or fail). Signal at 15:55:10 ET: basis_bps = 1e4 * (near - mid)/mid, near = last NOII message at-or-before 15:55:10 with near_price>0, mid = prevailing bbo-1s mid. Direction WITH the basis (buy iff near>mid). Entry = taker market at 15:55:10 + U[5,25]s latency (bbo-1s cross + 0.5bp slip); exit AT the official closing cross. Net via decompose.plan_pnl (SEC/TAF 0.3bp on the sell leg). NO ledger writes; NO pass/fail interpretation.

Symbols: NVDA, TSLA, AMD, MU, GOOGL    seed=7
Sessions in range (< holdout 2026-06-01): 31
ALL-events universe (valid basis + cross): 155 events    years: ['2026']
Splits present: ['holdout']

DATA-REALITY (VERIFIED on the owned tape, documented per task): NOII near/far indicative prices are 0 until ~15:55:00 ET; near first turns >0 at exactly 15:55:00 across the full 2020->2026 span. At 15:55:10 there are ~40 disseminated messages with near/far/ref all populated, so the basis is well defined every covered session. Growth vs 15:53/15:51 is meaningful (imbalance shares evolve; at 15:53/15:51 near is still 0 so norm_imb there uses signal_at's near->ref price fallback). near_drift_51_55 DEGENERATES to 0 (near=0 at 15:51) — computed exactly per formula; see importances.

## 1. Event funnel / skipped-session counters
```
{
  "no_noii_partition": 0,
  "no_noii_msgs": 0,
  "no_near": 0,
  "no_bbo": 0,
  "no_mid": 0,
  "zero_basis": 0,
  "no_adv": 0,
  "no_cross": 0,
  "void": 0,
  "events": 155
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

- Pooled (day-clustered): mean=13.036  95%CI=[6.908, 19.855]  n=143  sessions=31

Per-symbol:

| symbol | n_events | n_sessions | net_bps_mean | ci_lo  | ci_hi  |
|--------|----------|------------|--------------|--------|--------|
| AMD    | 28       | 28         | 2.891        | -9.129 | 16.098 |
| GOOGL  | 28       | 28         | -0.958       | -6.673 | 4.648  |
| MU     | 28       | 28         | 52.441       | 32.854 | 73.584 |
| NVDA   | 30       | 30         | 11.286       | 4.956  | 17.459 |
| TSLA   | 29       | 29         | 0.108        | -6.35  | 6.9    |
| POOLED | 143      | 31         | 13.036       | 6.908  | 19.855 |

Per-year:

| year   | n_events | n_sessions | net_bps_mean | ci_lo | ci_hi  |
|--------|----------|------------|--------------|-------|--------|
| 2026   | 143      | 31         | 13.036       | 6.908 | 19.855 |
| POOLED | 143      | 31         | 13.036       | 6.908 | 19.855 |

Stiffened prongs (>=3/5 symbols positive AND >=4/7 years positive):

```
{
  "pooled_mean_net_bps": 13.036,
  "pooled_ci_lo": 6.908,
  "pooled_ci_hi": 19.855,
  "n_events": 143,
  "n_sessions": 31,
  "symbols_positive_point_estimate": 4,
  "per_symbol_point_estimate": {
    "AMD": 2.891,
    "GOOGL": -0.958,
    "MU": 52.441,
    "NVDA": 11.286,
    "TSLA": 0.108
  },
  "years_positive_point_estimate": 1,
  "per_year_point_estimate": {
    "2026": 13.036
  },
  "meets_pooled_lo_gt_0": true,
  "meets_ge_3_of_5_symbols_positive": true,
  "meets_ge_4_of_7_years_positive": false
}
```

## 3. Classical cell |basis_bps| >= 10

### |basis| >= 10 bps

- Pooled (day-clustered): mean=12.506  95%CI=[6.867, 18.523]  n=140  sessions=31

Per-symbol:

| symbol | n_events | n_sessions | net_bps_mean | ci_lo   | ci_hi  |
|--------|----------|------------|--------------|---------|--------|
| AMD    | 27       | 27         | -1.206       | -11.303 | 8.686  |
| GOOGL  | 27       | 27         | -1.535       | -7.689  | 4.236  |
| MU     | 28       | 28         | 52.441       | 32.854  | 73.584 |
| NVDA   | 29       | 29         | 12.183       | 5.593   | 18.783 |
| TSLA   | 29       | 29         | 0.108        | -6.35   | 6.9    |
| POOLED | 140      | 31         | 12.506       | 6.867   | 18.523 |

Per-year:

| year   | n_events | n_sessions | net_bps_mean | ci_lo | ci_hi  |
|--------|----------|------------|--------------|-------|--------|
| 2026   | 140      | 31         | 12.506       | 6.867 | 18.523 |
| POOLED | 140      | 31         | 12.506       | 6.867 | 18.523 |

Stiffened prongs (>=3/5 symbols positive AND >=4/7 years positive):

```
{
  "pooled_mean_net_bps": 12.506,
  "pooled_ci_lo": 6.867,
  "pooled_ci_hi": 18.523,
  "n_events": 140,
  "n_sessions": 31,
  "symbols_positive_point_estimate": 3,
  "per_symbol_point_estimate": {
    "AMD": -1.206,
    "GOOGL": -1.535,
    "MU": 52.441,
    "NVDA": 12.183,
    "TSLA": 0.108
  },
  "years_positive_point_estimate": 1,
  "per_year_point_estimate": {
    "2026": 12.506
  },
  "meets_pooled_lo_gt_0": true,
  "meets_ge_3_of_5_symbols_positive": true,
  "meets_ge_4_of_7_years_positive": false
}
```

## 4. GBM cell (LightGBM regression on ALL-events net, fixed gate pred>0)

Model: LightGBM (lgbm.DEFAULT_PARAMS, objective=huber) on event net_bps; expanding calendar walk-forward (>=2y initial train, 6-month test blocks, 1-session embargo); FIXED gate pred>0. Features: the registered M6-GBM set recomputed at 15:55:10 + basis_bps (17 cols).

Walk-forward folds:
```
[]
```
OOS events (beyond initial-train span): 0    GATED (pred>0) taken: 0

- UNGATED same-span baseline (all OOS events): n=0
- GATED (pred>0) taken stream:                 n=0

### GBM-gated (pred > 0) taken stream

- Pooled (day-clustered): n=0

Per-symbol:

| symbol | n_events | n_sessions | net_bps_mean | ci_lo | ci_hi |
|--------|----------|------------|--------------|-------|-------|
| POOLED | 0        | 0          | null         | null  | null  |

Per-year:

| year   | n_events | n_sessions | net_bps_mean | ci_lo | ci_hi |
|--------|----------|------------|--------------|-------|-------|
| POOLED | 0        | 0          | null         | null  | null  |

Stiffened prongs (>=3/5 symbols positive AND >=4/7 years positive):

```
{
  "pooled_mean_net_bps": null,
  "pooled_ci_lo": null,
  "pooled_ci_hi": null,
  "n_events": 0,
  "n_sessions": 0,
  "symbols_positive_point_estimate": 0,
  "per_symbol_point_estimate": {},
  "years_positive_point_estimate": 0,
  "per_year_point_estimate": {},
  "meets_pooled_lo_gt_0": false,
  "meets_ge_3_of_5_symbols_positive": false,
  "meets_ge_4_of_7_years_positive": false
}
```

## 5. GBM feature importances (mean LightGBM gain across folds)

| feature          | mean_gain | n_folds |
|------------------|-----------|---------|
| norm_imb         | 0.0       | 0       |
| side             | 0.0       | 0       |
| paired_ratio     | 0.0       | 0       |
| imb_growth_53    | 0.0       | 0       |
| imb_growth_51    | 0.0       | 0       |
| near_ref_bps     | 0.0       | 0       |
| near_far_bps     | 0.0       | 0       |
| near_drift_51_55 | 0.0       | 0       |
| msg_count        | 0.0       | 0       |
| log_adv20        | 0.0       | 0       |
| vol20            | 0.0       | 0       |
| basis_bps        | 0.0       | 0       |
| oh_NVDA          | 0.0       | 0       |
| oh_TSLA          | 0.0       | 0       |
| oh_AMD           | 0.0       | 0       |
| oh_MU            | 0.0       | 0       |
| oh_GOOGL         | 0.0       | 0       |

## 6. PROTOCOL v6.1 ground-truthing — 10 stratified events (near vs mid vs cross vs realized)

near_price: NOII indicative clearing price. entry_mid: prevailing bbo-1s mid at 15:55:10. basis_bps: near vs mid. entry_in_nbbo: entry fill within the prevailing NBBO. cross_vs_mid_bps: realized clearing (cross) vs the market mid. cross_vs_close_bps: cross vs the official daily close (0 confirms the daily-close cross source, RTH fetch excludes the 16:00 print). basis_agrees_cross: did sign(near-mid) predict sign(cross-mid).

| session    | symbol | side | near_price | entry_mid | basis_bps   | entry_bid | entry_ask | entry_px    | entry_in_nbbo | cross_px | cross_vs_mid_bps | bar_close | cross_vs_close_bps | basis_agrees_cross | net_bps    |
|------------|--------|------|------------|-----------|-------------|-----------|-----------|-------------|---------------|----------|------------------|-----------|--------------------|--------------------|------------|
| 2026-06-05 | MU     | -1   | 858.53     | 874.43    | -181.832737 | 874.18    | 874.68    | 874.866254  | true          | 864.01   | -119.163341      | 857.86    | 71.690019          | true               | 123.790447 |
| 2026-06-08 | AMD    | 1    | 514.75     | 489.93    | 506.602984  | 489.83    | 490.03    | 490.41452   | true          | 490.33   | 8.164432         | 489.565   | 15.626117          | true               | -2.023378  |
| 2026-06-09 | MU     | 1    | 924.02     | 914.99    | 98.689603   | 914.6     | 915.38    | 915.04575   | true          | 935.89   | 228.417797       | 919.39    | 179.46682          | true               | 227.487787 |
| 2026-06-10 | MU     | 1    | 901.68     | 901.38    | 3.32823     | 901.14    | 901.62    | 898.85494   | false         | 891.88   | -105.393951      | 876.87    | 171.177027         | false              | -77.895738 |
| 2026-06-11 | MU     | 1    | 1033.68    | 992.605   | 413.810126  | 992.35    | 992.86    | 992.709633  | true          | 995.87   | 32.893246        | 998.73    | -28.636368         | true               | 31.534809  |
| 2026-06-16 | AMD    | -1   | 486.63     | 509.58    | -450.370894 | 509.49    | 509.67    | 508.404579  | false         | 507.29   | -44.938969       | 511.0     | -72.60274          | true               | 21.623062  |
| 2026-06-24 | MU     | 1    | 1039.0     | 1030.695  | 80.576698   | 1030.39   | 1031.0    | 1032.321614 | false         | 1048.51  | 172.844537       | 1213.77   | -1361.542961       | true               | 156.510636 |
| 2026-07-01 | AMD    | -1   | 517.39     | 540.37    | -425.264171 | 540.29    | 540.45    | 539.76301   | true          | 540.88   | 9.437978         | 544.104   | -59.253378         | false              | -20.994073 |
| 2026-07-02 | AMD    | -1   | 507.82     | 514.49    | -129.642947 | 514.31    | 514.67    | 514.344281  | true          | 517.82   | 64.72429         | 519.5     | -32.338787         | false              | -67.87572  |
| 2026-07-07 | AMD    | -1   | 508.0      | 513.755   | -112.018375 | 513.62    | 513.89    | 513.654316  | true          | 516.11   | 45.83897         | 512.15    | 77.321097          | false              | -48.108106 |

## 7. Exit-reason distribution (ALL events)

| exit_reason | count |
|-------------|-------|
| moc         | 155   |
