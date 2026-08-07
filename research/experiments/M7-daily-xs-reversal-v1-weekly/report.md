# M7 daily cross-sectional reversal report -- M7-daily-xs-reversal-v1-weekly

Family: daily_xs_reversal_v1 (M3_REGISTRATION.md M7 section). Research-only (the deployable system never holds overnight; deployment would need the overnight constraint amended by the user).
Cell: weekly  (hold = 5 session(s), MOC->MOC)
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
  "entry_candidates": 335,
  "too_few_eligible": 0,
  "no_exit_session_in_range": 2,
  "rebalances": 333
}
```

## 2. Pooled per-rebalance net CI (day-clustered on entry session)

BASE (net of SEC/TAF):        mean=-20.993  95%CI=[-66.402, 22.752]  n_rebalances=333
BORROW-STRESS (−50bps/yr HTB): mean=-21.513  95%CI=[-66.921, 22.227]  n_rebalances=333

Long-only eligible-universe drift baseline (context only): mean=83.102  95%CI=[19.866, 143.737]  n_rebalances=333
Average per-rebalance name turnover: 0.452

## 3. Per-year table (>=4/7-year prong)

| year | n_rebalances | book_net_mean | ci_lo    | ci_hi   | positive_point | borrow_net_mean | borrow_positive |
|------|--------------|---------------|----------|---------|----------------|-----------------|-----------------|
| 2020 | 53           | -42.293       | -166.235 | 67.303  | false          | -42.812         | false           |
| 2021 | 52           | -95.104       | -182.965 | -4.754  | false          | -95.618         | false           |
| 2022 | 52           | -27.437       | -157.744 | 103.089 | false          | -27.959         | false           |
| 2023 | 52           | 89.681        | -6.494   | 188.836 | true           | 89.16           | true            |
| 2024 | 52           | -85.28        | -235.969 | 53.122  | false          | -85.8           | false           |
| 2025 | 52           | -6.612        | -85.391  | 69.197  | false          | -7.137          | false           |
| 2026 | 20           | 86.891        | -48.833  | 213.074 | true           | 86.377          | true            |

## 4. Per-name contribution (leg-trips)

| symbol | n_trips | n_long | n_short | net_bps_mean | net_bps_sum | long_net_mean | short_net_mean |
|--------|---------|--------|---------|--------------|-------------|---------------|----------------|
| SMCI   | 215     | 109    | 106     | 36.381       | 7821.873    | 238.732       | -171.697       |
| TSLA   | 189     | 96     | 93      | 32.046       | 6056.734    | 62.85         | 0.249          |
| AMZN   | 129     | 66     | 63      | 43.641       | 5629.752    | 25.401        | 62.751         |
| AMD    | 175     | 87     | 88      | 29.869       | 5227.023    | 100.016       | -39.481        |
| META   | 151     | 79     | 72      | 33.399       | 5043.177    | 47.004        | 18.471         |
| COIN   | 183     | 101    | 82      | 27.168       | 4971.786    | 37.641        | 14.269         |
| AVGO   | 129     | 64     | 65      | -29.962      | -3865.04    | 34.277        | -93.212        |
| NVDA   | 132     | 53     | 79      | -53.282      | -7033.288   | -55.508       | -51.789        |
| PLTR   | 171     | 80     | 91      | -47.979      | -8204.387   | 63.337        | -145.839       |
| GOOGL  | 124     | 59     | 65      | -76.04       | -9428.988   | -50.835       | -98.919        |
| MU     | 175     | 82     | 93      | -111.915     | -19585.069  | 17.124        | -225.691       |
| MSTR   | 225     | 123    | 102     | -127.015     | -28578.327  | 29.855        | -316.181       |

## 5. Borrow-stress arm (mandatory)

Pooled BASE:          mean=-20.993  95%CI=[-66.402, 22.752]  n_rebalances=333
Pooled BORROW-STRESS: mean=-21.513  95%CI=[-66.921, 22.227]  n_rebalances=333
Per-year borrow columns are in section 3 (borrow_net_mean / borrow_positive).

## 6. Split-contamination diagnostic (raw-close caveat)

```
{
  "n_legs": 1998,
  "n_split_suspect": 38,
  "split_suspect_pct": 1.9,
  "split_suspect_net_bps_mean": 402.919,
  "clean_net_bps_mean": -29.212,
  "note": "Raw (unadjusted) closes: a leg is split-suspect when |trailing-5d return| or |holding return| exceeds 40% -- almost certainly a split discontinuity, not a real move. Reported, not removed (removing would void the trial)."
}
```

## 7. Ground-truth: 10 stratified leg-trips vs the raw daily bars (PROTOCOL v6.1)

entry_match / exit_match: the MOC fill EQUALS the daily-bar close exactly. By construction the fills ARE the closes, so every row must match -- this table verifies that identity holds on sampled winners/losers/signal-extremes.

| entry_session | exit_session | symbol | side | resid    | entry_close | bar_entry_close | entry_match | exit_close | bar_exit_close | exit_match | net_bps   | split_suspect |
|---------------|--------------|--------|------|----------|-------------|-----------------|-------------|------------|----------------|------------|-----------|---------------|
| 2020-08-28    | 2020-09-04   | TSLA   | -1   | 0.03358  | 2213.4      | 2213.4          | true        | 418.32     | 418.32         | true       | 8109.757  | true          |
| 2022-06-03    | 2022-06-10   | AMZN   | -1   | 0.06144  | 2447.0      | 2447.0          | true        | 109.65     | 109.65         | true       | 9551.6    | true          |
| 2022-07-15    | 2022-07-22   | GOOGL  | 1    | -0.0368  | 2235.55     | 2235.55         | true        | 107.9      | 107.9          | true       | -9517.359 | true          |
| 2022-07-22    | 2022-07-29   | GOOGL  | 1    | -0.98768 | 107.9       | 107.9           | true        | 116.32     | 116.32         | true       | 780.029   | true          |
| 2024-06-07    | 2024-06-14   | NVDA   | -1   | 0.06044  | 1208.88     | 1208.88         | true        | 131.88     | 131.88         | true       | 8908.773  | true          |
| 2024-06-14    | 2024-06-24   | NVDA   | 1    | -0.84559 | 131.88      | 131.88          | true        | 118.11     | 118.11         | true       | -1044.4   | true          |
| 2024-08-02    | 2024-08-09   | MSTR   | 1    | -0.09528 | 1447.99     | 1447.99         | true        | 135.37     | 135.37         | true       | -9065.146 | true          |
| 2024-08-09    | 2024-08-16   | MSTR   | 1    | -0.83202 | 135.37      | 135.37          | true        | 133.04     | 133.04         | true       | -172.416  | true          |
| 2024-09-27    | 2024-10-04   | SMCI   | 1    | -0.13451 | 419.74      | 419.74          | true        | 41.23      | 41.23          | true       | -9017.755 | true          |
| 2024-10-04    | 2024-10-11   | SMCI   | 1    | -0.83046 | 41.23       | 41.23           | true        | 47.8       | 47.8           | true       | 1593.152  | true          |

## 8. Registered promotion bar (diagnostic echo, not a gate in this app)

```
{
  "pooled_book_net_mean": -20.993,
  "pooled_ci_lo": -66.402,
  "pooled_ci_hi": 22.752,
  "n_rebalances": 333,
  "borrow_stress_mean": -21.513,
  "borrow_stress_ci_lo": -66.921,
  "years_with_data": 7,
  "years_positive_point": 2,
  "meets_pooled_lo_gt_0": false,
  "meets_ge_4_of_7_years_positive": false,
  "meets_borrow_stress_lo_gt_0": false
}
```
