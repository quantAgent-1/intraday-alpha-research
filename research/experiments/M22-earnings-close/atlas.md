# M22 earnings-day closing crosses atlas -- M22-earnings-close

Family `earnings_close_v1` (registered 2026-07-23, M3_REGISTRATION.md § M22). ONE pooled look over TRAIN+VALIDATE (<= 2026-05-31); confirmation authority is FORWARD (M20F pattern). Cell A (champion 5, bbo-1s mid, exit AT the 16:00 cross) and Cell B (broad 12, ref-proxy, exit at the day0 raw close) are DISJOINT evidence classes -- never pooled (L9). NO ledger verdict here; the orchestrator owns it.

seed=7    holdout seal: 2026-06-01 (calendar max day0 structurally < seal)

## Cell A -- AMPLIFICATION (champion 5; day0 vs same-run non-day0 baseline)

Fired day0 events: 111 across 104 sessions.  PASS = n>=50 & sessions>=40 & CI-lo>0 & (day0 mean >= 2x baseline mean when baseline>0; ruling A8).
```
{
  "n_fired_day0": 111,
  "n_sessions_day0": 104,
  "day0_mean_net_bps": 3.7034,
  "day0_ci_lo": -1.0701,
  "day0_ci_hi": 8.2996,
  "n_baseline": 6087,
  "n_sessions_baseline": 1587,
  "baseline_mean_net_bps": 2.4604,
  "baseline_ci_lo": 1.8018,
  "baseline_ci_hi": 3.1488,
  "baseline_mean_positive": true,
  "amp_ratio_day0_over_baseline": 1.5052,
  "amp_prong_binds": true,
  "meets_n_sessions_floor": true,
  "meets_ci_lower_gt_0": false,
  "meets_2x_amplification": false,
  "underpowered": false,
  "pass": false,
  "per_era": [
    {
      "era": "2020-22",
      "n": 48,
      "n_sessions": 44,
      "mean_net_bps": -0.5952,
      "ci_lo": -7.9821,
      "ci_hi": 5.724
    },
    {
      "era": "2023-26",
      "n": 63,
      "n_sessions": 60,
      "mean_net_bps": 6.9785,
      "ci_lo": 0.5227,
      "ci_hi": 13.4552
    }
  ],
  "per_name": [
    {
      "symbol": "AMD",
      "n": 22,
      "n_sessions": 22,
      "mean_net_bps": 6.0344,
      "ci_lo": -5.6373,
      "ci_hi": 19.2484
    },
    {
      "symbol": "GOOGL",
      "n": 21,
      "n_sessions": 21,
      "mean_net_bps": -7.6283,
      "ci_lo": -16.5566,
      "ci_hi": 0.7261
    },
    {
      "symbol": "MU",
      "n": 23,
      "n_sessions": 23,
      "mean_net_bps": 8.159,
      "ci_lo": -1.1532,
      "ci_hi": 18.2162
    },
    {
      "symbol": "NVDA",
      "n": 24,
      "n_sessions": 24,
      "mean_net_bps": 8.304,
      "ci_lo": -0.1432,
      "ci_hi": 17.1839
    },
    {
      "symbol": "TSLA",
      "n": 21,
      "n_sessions": 21,
      "mean_net_bps": 2.4553,
      "ci_lo": -8.9322,
      "ci_hi": 13.1363
    }
  ]
}
```
Cell A funnel (run_basis_trial ALL-events):
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
Per-era day0 (reported, never gated):

| era     | n  | n_sessions | mean_net_bps | ci_lo   | ci_hi   |
|---------|----|------------|--------------|---------|---------|
| 2020-22 | 48 | 44         | -0.5952      | -7.9821 | 5.724   |
| 2023-26 | 63 | 60         | 6.9785       | 0.5227  | 13.4552 |

Per-name day0 (reported, never gated):

| symbol | n  | n_sessions | mean_net_bps | ci_lo    | ci_hi   |
|--------|----|------------|--------------|----------|---------|
| AMD    | 22 | 22         | 6.0344       | -5.6373  | 19.2484 |
| GOOGL  | 21 | 21         | -7.6283      | -16.5566 | 0.7261  |
| MU     | 23 | 23         | 8.159        | -1.1532  | 18.2162 |
| NVDA   | 24 | 24         | 8.304        | -0.1432  | 17.1839 |
| TSLA   | 21 | 21         | 2.4553       | -8.9322  | 13.1363 |

## Cell B -- CATALYST REVIVAL (broad 12; proxy-priced, day0 only)

Fired day0 events: 171 across 133 sessions.  PASS = n>=60 & CI-lo>0.
```
{
  "n_fired": 171,
  "n_sessions": 133,
  "mean_net_bps": 0.9846,
  "ci_lo": -4.3579,
  "ci_hi": 8.1487,
  "meets_n_ge_60": true,
  "meets_ci_lower_gt_0": false,
  "underpowered": false,
  "pass": false,
  "per_era": [
    {
      "era": "2020-22",
      "n": 31,
      "n_sessions": 29,
      "mean_net_bps": 14.7529,
      "ci_lo": -5.3772,
      "ci_hi": 49.7594
    },
    {
      "era": "2023-26",
      "n": 140,
      "n_sessions": 104,
      "mean_net_bps": -2.0642,
      "ci_lo": -5.991,
      "ci_hi": 1.7007
    }
  ],
  "per_name": [
    {
      "symbol": "AAPL",
      "n": 17,
      "n_sessions": 17,
      "mean_net_bps": -6.3029,
      "ci_lo": -14.6325,
      "ci_hi": 1.5089
    },
    {
      "symbol": "AMAT",
      "n": 9,
      "n_sessions": 9,
      "mean_net_bps": -11.4015,
      "ci_lo": -22.6297,
      "ci_hi": 0.6195
    },
    {
      "symbol": "AVGO",
      "n": 19,
      "n_sessions": 19,
      "mean_net_bps": 28.582,
      "ci_lo": -2.402,
      "ci_hi": 80.6109
    },
    {
      "symbol": "INTC",
      "n": 13,
      "n_sessions": 13,
      "mean_net_bps": -0.4997,
      "ci_lo": -11.7436,
      "ci_hi": 12.0755
    },
    {
      "symbol": "KLAC",
      "n": 12,
      "n_sessions": 12,
      "mean_net_bps": -2.0832,
      "ci_lo": -19.9189,
      "ci_hi": 16.8664
    },
    {
      "symbol": "LRCX",
      "n": 12,
      "n_sessions": 12,
      "mean_net_bps": 4.9894,
      "ci_lo": -7.7973,
      "ci_hi": 17.2656
    },
    {
      "symbol": "META",
      "n": 12,
      "n_sessions": 12,
      "mean_net_bps": -9.4627,
      "ci_lo": -25.6901,
      "ci_hi": 8.5444
    },
    {
      "symbol": "MRVL",
      "n": 11,
      "n_sessions": 11,
      "mean_net_bps": -7.8687,
      "ci_lo": -22.9884,
      "ci_hi": 7.1372
    },
    {
      "symbol": "MSFT",
      "n": 25,
      "n_sessions": 25,
      "mean_net_bps": 1.7281,
      "ci_lo": -6.2656,
      "ci_hi": 9.5833
    },
    {
      "symbol": "NFLX",
      "n": 12,
      "n_sessions": 12,
      "mean_net_bps": -6.9745,
      "ci_lo": -13.0181,
      "ci_hi": -1.3856
    },
    {
      "symbol": "QCOM",
      "n": 17,
      "n_sessions": 17,
      "mean_net_bps": -2.2608,
      "ci_lo": -13.1706,
      "ci_hi": 9.7812
    },
    {
      "symbol": "TXN",
      "n": 12,
      "n_sessions": 12,
      "mean_net_bps": 7.1432,
      "ci_lo": -4.7462,
      "ci_hi": 19.2331
    }
  ]
}
```
Cell B funnel:
```
{
  "pairs_considered": 406,
  "out_of_range": 96,
  "no_noii_partition": 96,
  "no_noii_msgs": 0,
  "no_near_ref": 0,
  "zero_basis": 13,
  "inactive": 30,
  "no_close": 0,
  "fired": 171
}
```
Per-era (reported, never gated):

| era     | n   | n_sessions | mean_net_bps | ci_lo   | ci_hi   |
|---------|-----|------------|--------------|---------|---------|
| 2020-22 | 31  | 29         | 14.7529      | -5.3772 | 49.7594 |
| 2023-26 | 140 | 104        | -2.0642      | -5.991  | 1.7007  |

Per-name (reported, never gated):

| symbol | n  | n_sessions | mean_net_bps | ci_lo    | ci_hi   |
|--------|----|------------|--------------|----------|---------|
| AAPL   | 17 | 17         | -6.3029      | -14.6325 | 1.5089  |
| AMAT   | 9  | 9          | -11.4015     | -22.6297 | 0.6195  |
| AVGO   | 19 | 19         | 28.582       | -2.402   | 80.6109 |
| INTC   | 13 | 13         | -0.4997      | -11.7436 | 12.0755 |
| KLAC   | 12 | 12         | -2.0832      | -19.9189 | 16.8664 |
| LRCX   | 12 | 12         | 4.9894       | -7.7973  | 17.2656 |
| META   | 12 | 12         | -9.4627      | -25.6901 | 8.5444  |
| MRVL   | 11 | 11         | -7.8687      | -22.9884 | 7.1372  |
| MSFT   | 25 | 25         | 1.7281       | -6.2656  | 9.5833  |
| NFLX   | 12 | 12         | -6.9745      | -13.0181 | -1.3856 |
| QCOM   | 17 | 17         | -2.2608      | -13.1706 | 9.7812  |
| TXN    | 12 | 12         | 7.1432       | -4.7462  | 19.2331 |

## Cell C -- MECHANISM PRONG (report-only, no bar)

day0 fired rows (Cell A day0 + Cell B) x single-stock complex presence x |F|/ADV tercile. AUM on public_date (rulings A4/A5). Prediction: amplification concentrates in complex names. NO promotion consequence.

| complex_present | f_adv_tercile | n   | mean_net_bps |
|-----------------|---------------|-----|--------------|
| false           | lo            | 223 | 0.704981     |
| true            | hi            | 59  | 7.15636      |
