# R2-A Stage 1 - exploratory re-analysis (NOT a look, NOT a gate)

Same 4,356 name-days as the frozen prong-0 result; cannot overturn it. Statistics computed by `r2a_prong0.gate_b_stats` verbatim (seed 7, 2000 session-clustered reps). Purpose: decide whether an out-of-sample panel expansion is worth building.

Fidelity: gate (a) rho +0.0067 vs published +0.0067; gate (b) mean +14.8744 vs published +14.8744 -> MATCH

## Decomposition - in-sample beta (upper bound) (n=4356)

| component | mean bps | 95% CI | se | t |
|---|---|---|---|---|
| signed fade RAW | +14.87 | [-1.17, +30.19] | 8.00 | 1.86 |
| factor (sector) | +8.58 | [-5.65, +21.89] | 7.03 | 1.22 |
| idiosyncratic | +6.30 | [-2.26, +14.85] | 4.36 | 1.44 |

SE ratio raw/idio 1.83x

## Decomposition - past-only expanding beta (implementable) (n=3756)

| component | mean bps | 95% CI | se | t |
|---|---|---|---|---|
| signed fade RAW | +13.57 | [-4.33, +31.19] | 9.06 | 1.50 |
| factor (sector) | +8.14 | [-7.00, +23.66] | 7.82 | 1.04 |
| idiosyncratic | +5.43 | [-3.35, +14.39] | 4.52 | 1.20 |

SE ratio raw/idio 2.00x

## Net of real exit cost (entry at the opening cross = 0 spread)

| name | top-q n | gross fade | half-spread 15:40-45 | SEC fee | NET |
|---|---|---|---|---|---|
| NVDA | 75 | +17.06 | 0.70 | 0.206 | +16.16 |
| TSLA | 47 | -9.35 | 0.78 | 0.206 | -10.34 |
| AMD | 47 | +31.54 | 0.62 | 0.206 | +30.71 |
| MU | 151 | +14.33 | 0.82 | 0.206 | +13.31 |
| GOOGL | 47 | +2.89 | 0.50 | 0.206 | +2.19 |
| KLAC | 145 | -1.65 | 3.60 | 0.206 | -5.45 |
| MRVL | 146 | +23.59 | 0.88 | 0.206 | +22.51 |
| LRCX | 145 | +15.67 | 1.72 | 0.206 | +13.74 |
| TXN | 145 | +22.25 | 0.97 | 0.206 | +21.08 |
| AMAT | 146 | +20.18 | 1.41 | 0.206 | +18.57 |
| **POOLED** | 1094 | +14.87 | | | **+13.29** |
