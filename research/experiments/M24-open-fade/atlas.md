# M24 opening-auction dislocation fade atlas -- M24-open-fade

Family `open_auction_fade_v1` (registered 2026-07-23, M3_REGISTRATION.md section M24). ONE pooled look over TRAIN+VALIDATE (<= 2026-05-31); any PASS consequence is Stage-2 FORWARD-JUDGED registration only, never direct trading. Decision frozen 09:28:30 ET on the opening NOII near-vs-ref basis; direction AGAINST (fade); exit = the same-session official CLOSE print. Both legs raw bars1d (L2). NO ledger verdict here.

seed=7    holdout seal: 2026-06-01    universe: 33 NOII names (champion-5 vs broad-28 reported separately, NEVER gated).

## Coverage / event funnel
```
{
  "candidates": 34986,
  "counts": {
    "no_msgs": 0,
    "no_near_ref": 216,
    "zero_basis": 19222,
    "no_bar": 0,
    "below_t25": 14156,
    "fired_t25": 1392
  },
  "reconciles": true,
  "coverage": {
    "n_total": 33,
    "n_present": 33,
    "present": [
      "AAPL",
      "ADBE",
      "AMAT",
      "AMD",
      "AMGN",
      "AVGO",
      "BKNG",
      "CMCSA",
      "COST",
      "CSCO",
      "GILD",
      "GOOGL",
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
      "MU",
      "NFLX",
      "NVDA",
      "PEP",
      "PLTR",
      "QCOM",
      "SBUX",
      "TMUS",
      "TSLA",
      "TXN",
      "VRTX"
    ],
    "missing": []
  },
  "n_early_close_flag": 0
}
```

## Cell t25 (|basis_open| >= 25 bps) -- PRIMARY

PASS = n>=300 & sessions>=150 & CI-lo>0 & mean net>=2.0 bps.
```
{
  "thresh_bps": 25.0,
  "n_fired": 1392,
  "n_sessions": 642,
  "mean_net_bps": 3.162,
  "ci_lo": -14.1922,
  "ci_hi": 20.8145,
  "meets_n_fired_floor": true,
  "meets_n_sessions_floor": true,
  "meets_ci_lower_gt_0": false,
  "meets_mean_floor": true,
  "underpowered": false,
  "between_the_bars": true,
  "pass": false
}
```

## Cell t50 (|basis_open| >= 50 bps) -- NESTED subset of t25
```
{
  "thresh_bps": 50.0,
  "n_fired": 324,
  "n_sessions": 182,
  "mean_net_bps": 37.064,
  "ci_lo": -4.627,
  "ci_hi": 82.6057,
  "meets_n_fired_floor": true,
  "meets_n_sessions_floor": true,
  "meets_ci_lower_gt_0": false,
  "meets_mean_floor": true,
  "underpowered": false,
  "between_the_bars": true,
  "pass": false
}
```

## ADIA No.19 panel (t25 daily-aggregated, $10k/event; SR0=0)
```
{
  "T": 642,
  "mean_pnl_usd": 6.856,
  "sr_native": 0.0142,
  "psr_sr0_0": 0.6318,
  "min_trl": 15322.96,
  "gamma3": 1.6397,
  "gamma4": 21.2132,
  "rho": 0.0643
}
```

## rho vs champion (report-only; hypothesis rho ~ 0)
```
{
  "rho_hat": -0.0734,
  "n_overlap": 609,
  "underpowered_rho": false
}
```

## Strata (report-only) -- gap_mr FENCE = corr(basis_open, overnight_gap)
```
{
  "corr_basis_gap": 0.1379,
  "gap_x_basis_2x2": [
    {
      "gap_positive": true,
      "basis_positive": true,
      "n": 462,
      "mean_net_bps": 18.044
    },
    {
      "gap_positive": true,
      "basis_positive": false,
      "n": 238,
      "mean_net_bps": -41.0982
    },
    {
      "gap_positive": false,
      "basis_positive": true,
      "n": 209,
      "mean_net_bps": -36.515
    },
    {
      "gap_positive": false,
      "basis_positive": false,
      "n": 483,
      "mean_net_bps": 27.9053
    }
  ],
  "imb_side_agrees_split": [
    {
      "imb_side_agrees": "true",
      "n": 1392,
      "n_sessions": 642,
      "mean_net_bps": 3.162,
      "ci_lo": -14.1922,
      "ci_hi": 20.8145
    }
  ],
  "per_year": [
    {
      "year": "2020",
      "n": 29,
      "n_sessions": 21,
      "mean_net_bps": 61.9649,
      "ci_lo": -51.9306,
      "ci_hi": 191.504
    },
    {
      "year": "2021",
      "n": 10,
      "n_sessions": 10,
      "mean_net_bps": 12.4998,
      "ci_lo": -107.3901,
      "ci_hi": 148.2539
    },
    {
      "year": "2022",
      "n": 129,
      "n_sessions": 88,
      "mean_net_bps": -19.8079,
      "ci_lo": -83.9016,
      "ci_hi": 44.7411
    },
    {
      "year": "2023",
      "n": 221,
      "n_sessions": 115,
      "mean_net_bps": 8.2538,
      "ci_lo": -35.0187,
      "ci_hi": 45.6955
    },
    {
      "year": "2024",
      "n": 329,
      "n_sessions": 152,
      "mean_net_bps": -22.4584,
      "ci_lo": -49.7702,
      "ci_hi": 3.9587
    },
    {
      "year": "2025",
      "n": 378,
      "n_sessions": 166,
      "mean_net_bps": 15.0583,
      "ci_lo": -21.1009,
      "ci_hi": 51.4995
    },
    {
      "year": "2026",
      "n": 296,
      "n_sessions": 90,
      "mean_net_bps": 16.5792,
      "ci_lo": -19.5232,
      "ci_hi": 50.7122
    }
  ],
  "champion5": {
    "n": 485,
    "n_sessions": 369,
    "mean_net_bps": -19.6312,
    "ci_lo": -52.4078,
    "ci_hi": 12.884
  },
  "broad28": {
    "n": 907,
    "n_sessions": 440,
    "mean_net_bps": 15.3502,
    "ci_lo": -4.9131,
    "ci_hi": 37.4571
  }
}
```

## Per-year (reported, never gated)

| year | n   | n_sessions | mean_net_bps | ci_lo     | ci_hi    |
|------|-----|------------|--------------|-----------|----------|
| 2020 | 29  | 21         | 61.9649      | -51.9306  | 191.504  |
| 2021 | 10  | 10         | 12.4998      | -107.3901 | 148.2539 |
| 2022 | 129 | 88         | -19.8079     | -83.9016  | 44.7411  |
| 2023 | 221 | 115        | 8.2538       | -35.0187  | 45.6955  |
| 2024 | 329 | 152        | -22.4584     | -49.7702  | 3.9587   |
| 2025 | 378 | 166        | 15.0583      | -21.1009  | 51.4995  |
| 2026 | 296 | 90         | 16.5792      | -19.5232  | 50.7122  |
