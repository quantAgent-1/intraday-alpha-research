# M21 earnings-reaction-regime diagnostic

**NO-COST-MODEL (research-only diagnostic; returns are gross, no fills/fees/slippage)**

Family `earnings_reaction_regime_v1` (registered 2026-07-22). VERDICT CLASS DIAGNOSTIC: no promotion rule, no trading path. Outcomes are cumulative close-to-close returns over day0+1..+5 and day0+1..+20; means/CIs in bps (1 bps = 0.01%). CR0 95% CI clustered by day0_session date (`cluster_ci` imported from the M20 harness).

generated: 2026-07-22T08:12:20.823742+00:00
estimation events (sealed, day0 <= VALIDATE end): 824    feature-complete (status=ok): 813
sector reference: SMH    streak base: gap (>0 reaction; hi>= 5 of 8 priors)
runup60_rel tercile edges (frozen): T1<= -0.064246 < T2 <= 0.036042 < T3

TRAIN and VALIDATE are POOLED for this diagnostic (single estimation pass, no promotion decision); the holdout (>= 2026-06-01) and all forward events are stripped by `apply_seal`. OUTCOME CONTAINMENT (literal-seal): an event enters estimation only if day0 + 20 trading sessions <= VALIDATE end; events failing this are excluded with reason `outcome_crosses_seal` (see drop table) — both windows share one event set. UNDERPOWERED flags cells below N=30.

## Full cells — runup tercile x gap sign x streak x window (24)

| bucket    | window | N  | n_dates | mean_bps | ci_lo_bps | ci_hi_bps | median_bps | hit_rate | underpowered |
|-----------|--------|----|---------|----------|-----------|-----------|------------|----------|--------------|
| T1/pos/hi | d1_5   | 28 | 28      | 133.7467 | -36.5595  | 304.053   | 181.3175   | 0.6071   | true         |
| T1/pos/lo | d1_5   | 69 | 64      | -52.6238 | -218.6005 | 113.3529  | 24.0529    | 0.5507   | false        |
| T1/neg/hi | d1_5   | 46 | 46      | 121.0069 | -22.6656  | 264.6794  | 88.5939    | 0.5435   | false        |
| T1/neg/lo | d1_5   | 76 | 71      | 20.2182  | -109.6915 | 150.1279  | -60.1716   | 0.4605   | false        |
| T2/pos/hi | d1_5   | 48 | 45      | 122.6319 | -45.3625  | 290.6263  | 25.2484    | 0.5417   | false        |
| T2/pos/lo | d1_5   | 57 | 54      | 82.8101  | -60.9568  | 226.577   | 47.2492    | 0.5263   | false        |
| T2/neg/hi | d1_5   | 35 | 35      | 140.5394 | -18.8333  | 299.912   | 62.5873    | 0.5714   | false        |
| T2/neg/lo | d1_5   | 53 | 50      | 7.4374   | -212.121  | 226.9959  | -14.3618   | 0.4906   | false        |
| T3/pos/hi | d1_5   | 48 | 46      | 119.5342 | -81.2848  | 320.3533  | 26.259     | 0.5833   | false        |
| T3/pos/lo | d1_5   | 56 | 54      | 325.5768 | 69.5509   | 581.6027  | 136.3585   | 0.6429   | false        |
| T3/neg/hi | d1_5   | 40 | 39      | 276.7401 | 35.9549   | 517.5253  | 175.9534   | 0.7      | false        |
| T3/neg/lo | d1_5   | 58 | 53      | 76.0091  | -66.4662  | 218.4844  | 61.583     | 0.5862   | false        |
| T1/pos/hi | d1_20  | 28 | 28      | 318.1013 | 3.261     | 632.9415  | 115.3036   | 0.5357   | true         |
| T1/pos/lo | d1_20  | 69 | 64      | 389.0126 | 118.6511  | 659.3742  | 283.8015   | 0.6232   | false        |
| T1/neg/hi | d1_20  | 46 | 46      | 471.8895 | 179.6776  | 764.1014  | 556.4327   | 0.6522   | false        |
| T1/neg/lo | d1_20  | 76 | 71      | 246.7969 | -56.6805  | 550.2742  | 55.1698    | 0.5526   | false        |
| T2/pos/hi | d1_20  | 48 | 45      | 32.5037  | -240.7859 | 305.7934  | -4.5112    | 0.4792   | false        |
| T2/pos/lo | d1_20  | 57 | 54      | 150.9208 | -141.6214 | 443.4629  | 159.1896   | 0.5965   | false        |
| T2/neg/hi | d1_20  | 35 | 35      | 68.9464  | -246.7296 | 384.6224  | -144.1544  | 0.4      | false        |
| T2/neg/lo | d1_20  | 53 | 50      | 174.3214 | -83.4856  | 432.1283  | 117.2046   | 0.566    | false        |
| T3/pos/hi | d1_20  | 48 | 46      | 649.6827 | 192.8111  | 1106.5543 | 457.4509   | 0.6458   | false        |
| T3/pos/lo | d1_20  | 56 | 54      | 375.0122 | -5.5882   | 755.6125  | 392.3278   | 0.6429   | false        |
| T3/neg/hi | d1_20  | 40 | 39      | 401.6653 | -16.0931  | 819.4237  | 288.5304   | 0.625    | false        |
| T3/neg/lo | d1_20  | 58 | 53      | 150.965  | -145.9368 | 447.8667  | 59.1584    | 0.5517   | false        |

## Margins — runup tercile x gap sign, streak collapsed (12)

| bucket     | window | N   | n_dates | mean_bps | ci_lo_bps | ci_hi_bps | median_bps | hit_rate | underpowered |
|------------|--------|-----|---------|----------|-----------|-----------|------------|----------|--------------|
| T1/pos/any | d1_5   | 124 | 114     | 8.969    | -103.57   | 121.508   | 74.3981    | 0.5726   | false        |
| T1/neg/any | d1_5   | 147 | 130     | 74.4288  | -17.3959  | 166.2536  | 1.4006     | 0.5034   | false        |
| T2/pos/any | d1_5   | 146 | 134     | 48.1454  | -43.8982  | 140.1891  | 16.5625    | 0.5205   | false        |
| T2/neg/any | d1_5   | 125 | 118     | 8.802    | -103.2543 | 120.8583  | -22.3691   | 0.472    | false        |
| T3/pos/any | d1_5   | 138 | 125     | 209.7093 | 73.2058   | 346.2129  | 109.2333   | 0.6304   | false        |
| T3/neg/any | d1_5   | 133 | 121     | 86.9963  | -23.966   | 197.9586  | 73.7944    | 0.5789   | false        |
| T1/pos/any | d1_20  | 124 | 114     | 340.163  | 153.1377  | 527.1883  | 236.0252   | 0.5887   | false        |
| T1/neg/any | d1_20  | 147 | 130     | 326.5819 | 125.3274  | 527.8364  | 246.4439   | 0.5714   | false        |
| T2/pos/any | d1_20  | 146 | 134     | 62.515   | -101.9034 | 226.9333  | 61.0582    | 0.5274   | false        |
| T2/neg/any | d1_20  | 125 | 118     | 76.5874  | -84.2216  | 237.3963  | 0.0        | 0.488    | false        |
| T3/pos/any | d1_20  | 138 | 125     | 457.8131 | 222.2206  | 693.4056  | 425.8648   | 0.6522   | false        |
| T3/neg/any | d1_20  | 133 | 121     | 194.4787 | -7.7772   | 396.7346  | 104.8974   | 0.5489   | false        |

## Per-year margin (status=ok events)

| year | window | N   | mean_bps | hit_rate |
|------|--------|-----|----------|----------|
| 2018 | d1_5   | 96  | -51.77   | 0.5104   |
| 2019 | d1_5   | 96  | 6.88     | 0.5104   |
| 2020 | d1_5   | 94  | 86.47    | 0.5532   |
| 2021 | d1_5   | 97  | 206.41   | 0.6598   |
| 2022 | d1_5   | 95  | 26.59    | 0.5684   |
| 2023 | d1_5   | 96  | 62.88    | 0.5104   |
| 2024 | d1_5   | 100 | 49.58    | 0.5      |
| 2025 | d1_5   | 100 | 215.93   | 0.55     |
| 2026 | d1_5   | 39  | 44.57    | 0.5641   |
| 2018 | d1_20  | 96  | 101.23   | 0.4896   |
| 2019 | d1_20  | 96  | 96.22    | 0.5312   |
| 2020 | d1_20  | 94  | 344.29   | 0.6383   |
| 2021 | d1_20  | 97  | 197.2    | 0.5773   |
| 2022 | d1_20  | 95  | -16.67   | 0.4526   |
| 2023 | d1_20  | 96  | 449.85   | 0.5833   |
| 2024 | d1_20  | 100 | 501.48   | 0.68     |
| 2025 | d1_20  | 100 | 268.07   | 0.57     |
| 2026 | d1_20  | 39  | 228.95   | 0.5128   |

## Per-symbol margin (status=ok events)

| symbol | window | N  | mean_bps | hit_rate |
|--------|--------|----|----------|----------|
| AAPL   | d1_5   | 33 | 103.64   | 0.5152   |
| ADI    | d1_5   | 33 | 53.19    | 0.5152   |
| AMAT   | d1_5   | 33 | 85.56    | 0.5455   |
| AMD    | d1_5   | 32 | 276.63   | 0.6875   |
| AMZN   | d1_5   | 34 | 8.29     | 0.6176   |
| ARM    | d1_5   | 9  | 256.05   | 0.4444   |
| ASML   | d1_5   | 34 | -9.15    | 0.5294   |
| AVGO   | d1_5   | 32 | 135.18   | 0.5625   |
| GOOGL  | d1_5   | 34 | -38.53   | 0.5      |
| INTC   | d1_5   | 34 | 5.63     | 0.4706   |
| KLAC   | d1_5   | 34 | 200.75   | 0.7353   |
| LRCX   | d1_5   | 34 | 58.19    | 0.5      |
| MCHP   | d1_5   | 34 | 59.25    | 0.5294   |
| META   | d1_5   | 34 | -4.28    | 0.5294   |
| MRVL   | d1_5   | 33 | -98.68   | 0.3939   |
| MSFT   | d1_5   | 34 | 66.06    | 0.6765   |
| MU     | d1_5   | 33 | -56.75   | 0.4848   |
| NFLX   | d1_5   | 34 | -77.28   | 0.4118   |
| NVDA   | d1_5   | 33 | -76.72   | 0.4545   |
| NXPI   | d1_5   | 34 | 180.89   | 0.7353   |
| ON     | d1_5   | 33 | 185.01   | 0.6061   |
| QCOM   | d1_5   | 34 | 49.57    | 0.5294   |
| SMCI   | d1_5   | 33 | 273.05   | 0.4242   |
| TSLA   | d1_5   | 34 | 299.67   | 0.6176   |
| TXN    | d1_5   | 34 | 76.13    | 0.5588   |
| AAPL   | d1_20  | 33 | 187.06   | 0.6364   |
| ADI    | d1_20  | 33 | -51.77   | 0.5152   |
| AMAT   | d1_20  | 33 | 43.98    | 0.4848   |
| AMD    | d1_20  | 32 | 514.14   | 0.5625   |
| AMZN   | d1_20  | 34 | 17.67    | 0.5588   |
| ARM    | d1_20  | 9  | 354.09   | 0.6667   |
| ASML   | d1_20  | 34 | 286.26   | 0.5882   |
| AVGO   | d1_20  | 32 | 299.19   | 0.625    |
| GOOGL  | d1_20  | 34 | 41.89    | 0.5      |
| INTC   | d1_20  | 34 | 165.01   | 0.5      |
| KLAC   | d1_20  | 34 | 535.16   | 0.6471   |
| LRCX   | d1_20  | 34 | 294.14   | 0.5      |
| MCHP   | d1_20  | 34 | 289.28   | 0.6176   |
| META   | d1_20  | 34 | 74.69    | 0.5294   |
| MRVL   | d1_20  | 33 | 192.6    | 0.5758   |
| MSFT   | d1_20  | 34 | 180.11   | 0.5588   |
| MU     | d1_20  | 33 | 324.3    | 0.4545   |
| NFLX   | d1_20  | 34 | 164.18   | 0.5588   |
| NVDA   | d1_20  | 33 | 107.04   | 0.6061   |
| NXPI   | d1_20  | 34 | 275.31   | 0.5882   |
| ON     | d1_20  | 33 | 345.11   | 0.6364   |
| QCOM   | d1_20  | 34 | 282.42   | 0.5588   |
| SMCI   | d1_20  | 33 | 701.07   | 0.4545   |
| TSLA   | d1_20  | 34 | 274.77   | 0.6176   |
| TXN    | d1_20  | 34 | 286.43   | 0.6176   |

## Dropped / excluded events (never silent)

| status               | n  |
|----------------------|----|
| outcome_crosses_seal | 10 |
| short_runup_history  | 1  |
