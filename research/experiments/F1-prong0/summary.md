# F1 prong 0 -- mechanism pre-check (PRE-DECLARED DIAGNOSTIC)

No economics: correlations between contemporaneous state variables only. No returns or P&L were computed.

## GATE -- predictive rho(depth_state[t], signed_flow[t+1])

rho = -0.0036  |  95% CI (session-clustered) [-0.0182, 0.0110]  |  gate |rho|>=0.1  ->  FAIL
(33051 (t,t+1) pairs over 1581 sessions; seed 7, 2000 draws)

## Contemporaneous rho(depth_state[t], signed_flow[t])

rho = 0.0117  (34632 pairs)

## Per-name

| name | rho_contemp | rho_predictive | n_pred_pairs | n_contemp |
|------|-------------|----------------|--------------|-----------|
| MU | 0.0189 | -0.0154 | 13338 | 13976 |
| NVDA | -0.0925 | -0.0521 | 6711 | 7032 |
| TSLA | 0.0930 | 0.0838 | 4390 | 4600 |
| AMD | 0.0167 | 0.0069 | 4621 | 4842 |
| GOOGL | 0.0519 | 0.0295 | 3991 | 4182 |

## Persistence -- AR(1) of depth_state across buckets

pooled AR(1) slope = 0.6038  (lag-1 corr = 0.5978, 33201 pairs)

| lag (x15min) | horizon min | autocorr | n |
|--------------|-------------|----------|---|
| 1 | 15 | 0.5978 | 33201 |
| 2 | 30 | 0.5017 | 31620 |
| 3 | 45 | 0.4457 | 30039 |
| 4 | 60 | 0.4045 | 28458 |
| 5 | 75 | 0.3713 | 26877 |
| 6 | 90 | 0.3562 | 25296 |

| name | AR(1) slope | lag1 corr | n |
|------|-------------|-----------|---|
| MU | 0.5841 | 0.5791 | 13398 |
| NVDA | 0.6042 | 0.5923 | 6741 |
| TSLA | 0.6954 | 0.6894 | 4410 |
| AMD | 0.6092 | 0.6033 | 4641 |
| GOOGL | 0.6070 | 0.6042 | 4011 |

## Coverage

total sessions used = 1581  |  total (t,t+1) pairs = 33051

| name | sessions | mean buckets/session | min | max | pred pairs |
|------|----------|----------------------|-----|-----|------------|
| MU | 638 | 22.00 | 22 | 22 | 13338 |
| NVDA | 321 | 22.00 | 22 | 22 | 6711 |
| TSLA | 210 | 22.00 | 22 | 22 | 4390 |
| AMD | 221 | 22.00 | 22 | 22 | 4621 |
| GOOGL | 191 | 22.00 | 22 | 22 | 3991 |

## Data quality

| name | seen | used | no-codes sess | no-cond-col | missing bbo | trades total | after blacklist | after minsize |
|------|------|------|---------------|-------------|-------------|--------------|-----------------|---------------|
| MU | 638 | 638 | 0 | 0 | 0 | 238271051 | 231381216 | 52595392 |
| NVDA | 321 | 321 | 0 | 0 | 0 | 496204026 | 488454585 | 144840638 |
| TSLA | 210 | 210 | 0 | 0 | 0 | 287303599 | 282517603 | 40178074 |
| AMD | 221 | 221 | 0 | 0 | 0 | 120482501 | 116931519 | 28247962 |
| GOOGL | 191 | 191 | 0 | 0 | 0 | 129346999 | 124560542 | 17668477 |
