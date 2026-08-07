# M28 exit-cost calibration (bars-only half-spread estimator)

estimator: hs_est = k * P25[(high-low)/close] over 15:40-15:45 minute bars
fitted k = **0.1438** (single parameter, log-space least squares, n=10 names)

| name | raw P25 range (bps) | predicted half-spread | MEASURED | abs % err | LOO % err |
|---|---|---|---|---|---|
| KLAC | 4.40 | 0.63 | 3.60 | 82% | 86% |
| TXN | 5.26 | 0.76 | 0.97 | 22% | 24% |
| MRVL | 8.88 | 1.28 | 0.88 | 45% | 51% |
| NVDA | 8.36 | 1.20 | 0.70 | 72% | 82% |
| MU | 8.64 | 1.24 | 0.82 | 52% | 59% |
| GOOGL | 5.04 | 0.73 | 0.50 | 45% | 51% |
| AMAT | 6.44 | 0.93 | 1.41 | 34% | 37% |
| AMD | 8.74 | 1.26 | 0.62 | 103% | 119% |
| TSLA | 10.02 | 1.44 | 0.78 | 85% | 98% |
| LRCX | 6.46 | 0.93 | 1.72 | 46% | 50% |

log-log correlation **-0.515**; median abs err **49%**; median leave-one-out err **55%**

## Estimated half-spread across the 184 tradeable names

median **0.68** bps; p10 0.48; p90 1.05; max 2.05

