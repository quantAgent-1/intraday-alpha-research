# M7 daily cross-sectional reversal report -- M7-daily-xs-reversal-v1-daily

Family: daily_xs_reversal_v1 (M3_REGISTRATION.md M7 section). Research-only (the deployable system never holds overnight; deployment would need the overnight constraint amended by the user).
Cell: daily  (hold = 1 session(s), MOC->MOC)
Universe (12): TSLA, NVDA, AMD, MU, AVGO, PLTR, COIN, MSTR, SMCI, META, AMZN, GOOGL
Signal: trailing 5-session close-to-close return, residualized vs the equal-weight eligible-universe mean; LONG bottom-3, SHORT top-3, $10,000/leg.
Costs: zero commission + SEC/TAF 0.3 bp on the SELL leg. Borrow-stress arm: 50 bps/yr pro-rated on short-leg calendar days.
Universe-entry gate: a name trades only once it has >= 30 trailing sessions.
Range: 2020-01-01 .. 2026-05-31  (sessions with data < holdout: 1651)
Splits present: ['train', 'validate']

Fills are the official closing print = the daily-bar CLOSE (closing cross = a single clearing price, no queue). Entry and exit fills EQUAL the daily closes exactly, by construction -- verified in section 7 (PROTOCOL v6.1).

## 0. Universe-entry dates (first session with >= 30 trailing sessions)

| symbol | entry_date | split |
|--------|------------|-------|
| TSLA   | 2019-12-13 | train |
| NVDA   | 2019-12-13 | train |
| AMD    | 2019-12-13 | train |
| MU     | 2019-12-13 | train |
| AVGO   | 2019-12-13 | train |
| PLTR   | 2020-11-10 | train |
| COIN   | 2021-05-25 | train |
| MSTR   | 2019-12-13 | train |
| SMCI   | 2019-12-13 | train |
| META   | 2019-12-13 | train |
| AMZN   | 2019-12-13 | train |
| GOOGL  | 2019-12-13 | train |

## 1. Rebalance funnel

```
{
  "entry_candidates": 1610,
  "too_few_eligible": 0,
  "no_exit_session_in_range": 1,
  "rebalances": 1609
}
```

## 2. Pooled per-rebalance net CI (day-clustered on entry session)

BASE (net of SEC/TAF):        mean=-8.506  95%CI=[-17.220, 0.729]  n_rebalances=1609
BORROW-STRESS (−50bps/yr HTB): mean=-8.605  95%CI=[-17.321, 0.631]  n_rebalances=1609

Long-only eligible-universe drift baseline (context only): mean=17.307  95%CI=[4.878, 29.602]  n_rebalances=1609
Average per-rebalance name turnover: 0.293

## 3. Per-year table (>=4/7-year prong)

| year | n_rebalances | book_net_mean | ci_lo   | ci_hi  | positive_point | borrow_net_mean | borrow_positive |
|------|--------------|---------------|---------|--------|----------------|-----------------|-----------------|
| 2020 | 253          | 4.635         | -16.882 | 27.876 | true           | 4.535           | true            |
| 2021 | 252          | -9.986        | -30.233 | 8.935  | false          | -10.085         | false           |
| 2022 | 251          | -17.094       | -45.948 | 11.689 | false          | -17.194         | false           |
| 2023 | 250          | 2.528         | -17.031 | 21.515 | true           | 2.428           | true            |
| 2024 | 252          | -23.714       | -55.691 | 7.007  | false          | -23.813         | false           |
| 2025 | 250          | -8.886        | -26.645 | 9.062  | false          | -8.986          | false           |
| 2026 | 101          | -4.811        | -39.212 | 26.834 | false          | -4.911          | false           |

## 4. Per-name contribution (leg-trips)

| symbol | n_trips | n_long | n_short | net_bps_mean | net_bps_sum | long_net_mean | short_net_mean |
|--------|---------|--------|---------|--------------|-------------|---------------|----------------|
| TSLA   | 962     | 475    | 487     | 7.595        | 7306.519    | 31.699        | -15.915        |
| AMD    | 779     | 405    | 374     | 6.638        | 5170.905    | 34.873        | -23.938        |
| NVDA   | 673     | 275    | 398     | 5.111        | 3439.567    | 28.99         | -11.389        |
| AMZN   | 623     | 338    | 285     | 2.832        | 1764.051    | -0.639        | 6.948          |
| SMCI   | 1031    | 515    | 516     | -0.079       | -81.959     | 35.671        | -35.76         |
| GOOGL  | 610     | 282    | 328     | -7.719       | -4708.331   | -5.374        | -9.734         |
| META   | 686     | 353    | 333     | -9.196       | -6308.557   | -13.944       | -4.163         |
| AVGO   | 639     | 305    | 334     | -13.024      | -8322.361   | 9.524         | -33.614        |
| PLTR   | 796     | 379    | 417     | -11.719      | -9328.561   | 7.241         | -28.952        |
| COIN   | 861     | 488    | 373     | -11.837      | -10191.246  | -2.896        | -23.533        |
| MU     | 851     | 395    | 456     | -28.129      | -23937.433  | 6.859         | -58.436        |
| MSTR   | 1143    | 617    | 526     | -32.3        | -36918.712  | -9.415        | -59.143        |

## 5. Borrow-stress arm (mandatory)

Pooled BASE:          mean=-8.506  95%CI=[-17.220, 0.729]  n_rebalances=1609
Pooled BORROW-STRESS: mean=-8.605  95%CI=[-17.321, 0.631]  n_rebalances=1609
Per-year borrow columns are in section 3 (borrow_net_mean / borrow_positive).

## 6. Split-contamination diagnostic (raw-close caveat)

```
{
  "n_legs": 9654,
  "n_split_suspect": 127,
  "split_suspect_pct": 1.32,
  "split_suspect_net_bps_mean": 83.457,
  "clean_net_bps_mean": -9.732,
  "note": "Raw (unadjusted) closes: a leg is split-suspect when |trailing-5d return| or |holding return| exceeds 40% -- almost certainly a split discontinuity, not a real move. Reported, not removed (removing would void the trial)."
}
```

## 7. Ground-truth: 10 stratified leg-trips vs the raw daily bars (PROTOCOL v6.1)

entry_match / exit_match: the MOC fill EQUALS the daily-bar close exactly. By construction the fills ARE the closes, so every row must match -- this table verifies that identity holds on sampled winners/losers/signal-extremes.

| entry_session | exit_session | symbol | side | resid    | entry_close | bar_entry_close | entry_match | exit_close | bar_exit_close | exit_match | net_bps   | split_suspect |
|---------------|--------------|--------|------|----------|-------------|-----------------|-------------|------------|----------------|------------|-----------|---------------|
| 2020-08-28    | 2020-08-31   | TSLA   | -1   | 0.03358  | 2213.4      | 2213.4          | true        | 498.32     | 498.32         | true       | 7748.322  | true          |
| 2022-06-03    | 2022-06-06   | AMZN   | -1   | 0.06144  | 2447.0      | 2447.0          | true        | 124.79     | 124.79         | true       | 9489.729  | true          |
| 2022-07-15    | 2022-07-18   | GOOGL  | 1    | -0.0368  | 2235.55     | 2235.55         | true        | 109.03     | 109.03         | true       | -9512.305 | true          |
| 2022-07-19    | 2022-07-20   | GOOGL  | 1    | -0.97399 | 113.81      | 113.81          | true        | 113.9      | 113.9          | true       | 7.608     | true          |
| 2022-07-20    | 2022-07-21   | GOOGL  | 1    | -1.02264 | 113.9       | 113.9           | true        | 114.34     | 114.34         | true       | 38.329    | true          |
| 2022-07-21    | 2022-07-22   | GOOGL  | 1    | -1.04723 | 114.34      | 114.34          | true        | 107.9      | 107.9          | true       | -563.516  | true          |
| 2022-07-22    | 2022-07-25   | GOOGL  | 1    | -0.98768 | 107.9       | 107.9           | true        | 107.51     | 107.51         | true       | -36.443   | true          |
| 2024-06-07    | 2024-06-10   | NVDA   | -1   | 0.06044  | 1208.88     | 1208.88         | true        | 121.79     | 121.79         | true       | 8992.239  | true          |
| 2024-08-07    | 2024-08-08   | MSTR   | 1    | -0.08419 | 1246.85     | 1246.85         | true        | 135.99     | 135.99         | true       | -8909.364 | true          |
| 2024-09-30    | 2024-10-01   | SMCI   | 1    | -0.13036 | 416.4       | 416.4           | true        | 40.55      | 40.55          | true       | -9026.206 | true          |

## 8. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_book_net_mean": -8.506,
  "pooled_ci_lo": -17.22,
  "pooled_ci_hi": 0.729,
  "n_rebalances": 1609,
  "borrow_stress_mean": -8.605,
  "borrow_stress_ci_lo": -17.321,
  "years_with_data": 7,
  "years_positive_point": 2,
  "meets_pooled_lo_gt_0": false,
  "meets_ge_4_of_7_years_positive": false,
  "meets_borrow_stress_lo_gt_0": false
}
```
