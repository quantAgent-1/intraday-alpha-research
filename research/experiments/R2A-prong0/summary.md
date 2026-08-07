# R2-A prong 0 -- off-exchange odd-lot -> open-print intraday fade

PRE-DECLARED DIAGNOSTIC (ledger row `R2A-prong0-predeclaration`, ts 2026-07-23T17:43Z). pass_a / pass_b / label below are mechanical field values, not a verdict.

Panel (10): NVDA, TSLA, AMD, MU, GOOGL, KLAC, MRVL, LRCX, TXN, AMAT  |  cap ts < 2026-06-01 ET
Analysis set: n=4356 name-days over 603 sessions.

## Adjudication (mechanical)

pass_a = False  |  pass_b = False  |  label = KILL

## GATE (a) INCREMENTAL INFO -- pooled residual rho(OLI_{t-1}, ret_t)

rho = 0.0067  |  95% CI (session-clustered) [-0.0269, 0.0396]  |  gate rho<=-0.03 AND CI-hi<0  ->  pass_a=False
(n=4356 name-days, 603 sessions; residualized per-name on [1, gap_t, ret_(t-1)]; seed 7, 2000 reps)

## GATE (b) MAGNITUDE -- per-name top-quartile |OLI| signed fade

signed_fade = -sign(OLI_(t-1)) * ret_t (RAW)
mean = 14.8744 bps  |  95% CI [-1.1658, 30.1876]  |  gate mean>=6.0 AND CI-lo>0  ->  pass_b=False
(top-quartile n=1094; names dropped Q3==0: none)
non-gating winsor(1/99) mean = 13.3511 bps  CI [-1.5693, 27.5193]

## Support -- raw (unresidualized) winsorized rho(OLI, ret_t)

rho = -0.0130  CI [-0.0475, 0.0221]  (n=4356)

## Support -- horizons (open -> exit)

| horizon | ga_rho | ga_ci_lo | ga_ci_hi | ga_n | gb_mean | gb_ci_lo | gb_ci_hi | gb_n |
|---------|--------|----------|----------|------|---------|----------|----------|------|
| 1545(main) | 0.0067 | -0.0269 | 0.0396 | 4356 | 14.8744 | -1.1658 | 30.1876 | 1094 |
| 1000 | -0.0011 | -0.0327 | 0.0308 | 4356 | 3.5641 | -5.8924 | 12.9280 | 1094 |
| 1100 | 0.0025 | -0.0291 | 0.0367 | 4356 | 4.6590 | -7.2001 | 15.7705 | 1094 |

## Support -- tier split (megacap-5 vs semi-5)

| tier | ga_rho | ga_ci_lo | ga_ci_hi | ga_n | gb_mean | gb_ci_lo | gb_ci_hi | gb_n |
|------|--------|----------|----------|------|---------|----------|----------|------|
| mega | -0.0125 | -0.0666 | 0.0423 | 1459 | 12.5960 | -11.1043 | 37.4754 | 367 |
| semi | 0.0132 | -0.0240 | 0.0480 | 2897 | 16.0246 | -0.9178 | 33.7368 | 727 |

## Support -- mean ret_t (bps) by gap-quartile (rows) x OLI-quartile (cols), per-name quartiles

| gap\OLI | Q1 | Q2 | Q3 | Q4 |
|---------|----|----|----|----|
| gapQ1 | 30.60 (n=252) | -5.65 (n=261) | 8.03 (n=296) | 22.29 (n=282) |
| gapQ2 | -8.94 (n=274) | 3.09 (n=277) | -7.66 (n=261) | -11.22 (n=273) |
| gapQ3 | -3.71 (n=284) | 10.76 (n=275) | 37.84 (n=254) | 5.80 (n=273) |
| gapQ4 | 14.49 (n=281) | -4.63 (n=272) | -3.66 (n=275) | -20.99 (n=266) |

first-stage pooled rho(OLI_(t-1), gap_t) = -0.0238 (n=4356)

## Support -- per-name

| name | tier | n_kept | n_resid | raw_rho | resid_rho | topq_n | topq_mean_fade_bps |
|------|------|--------|---------|---------|-----------|--------|--------------------|
| NVDA | mega | 298 | 298 | -0.0556 | -0.0409 | 75 | 17.06 |
| TSLA | mega | 186 | 186 | 0.0431 | 0.0587 | 47 | -9.35 |
| AMD | mega | 186 | 186 | 0.0587 | 0.0649 | 47 | 31.54 |
| MU | mega | 603 | 603 | -0.0418 | -0.0296 | 151 | 14.33 |
| GOOGL | mega | 186 | 186 | -0.0316 | -0.0086 | 47 | 2.89 |
| KLAC | semi | 578 | 578 | 0.0321 | 0.0799 | 145 | -1.65 |
| MRVL | semi | 581 | 581 | -0.0606 | -0.0467 | 146 | 23.59 |
| LRCX | semi | 580 | 580 | -0.0184 | -0.0172 | 145 | 15.67 |
| TXN | semi | 577 | 577 | -0.0534 | -0.0210 | 145 | 22.25 |
| AMAT | semi | 581 | 581 | -0.0422 | 0.0005 | 146 | 20.18 |

## Support -- coverage / sparsity

| name | cand | kept | oddlot_p50 | OLI_p10 | OLI_p50 | OLI_p90 |
|------|------|------|------------|---------|---------|---------|
| NVDA | 1649 | 298 | 488159 | -0.059 | -0.008 | 0.045 |
| TSLA | 1649 | 186 | 668279 | -0.018 | 0.013 | 0.044 |
| AMD | 1649 | 186 | 172236 | -0.048 | -0.010 | 0.027 |
| MU | 1649 | 603 | 58631 | -0.067 | -0.015 | 0.039 |
| GOOGL | 1649 | 186 | 282476 | -0.037 | 0.005 | 0.047 |
| KLAC | 1649 | 578 | 12122 | -0.158 | -0.005 | 0.145 |
| MRVL | 1649 | 581 | 35340 | -0.063 | -0.006 | 0.053 |
| LRCX | 1649 | 580 | 28233 | -0.090 | -0.004 | 0.083 |
| TXN | 1649 | 577 | 23654 | -0.089 | -0.012 | 0.067 |
| AMAT | 1649 | 581 | 27505 | -0.089 | -0.007 | 0.075 |

### Drop funnel (first-failing guard; order: no_trades_tm1, no_bbo_tm1, no_bbo_t, early_close_t, bars_missing, few_odd_signs, no_exit_t)

| name | no_trades_tm1 | no_bbo_tm1 | no_bbo_t | early_close_t | bars_missing | few_odd_signs | no_exit_t |
|------|------|------|------|------|------|------|------|
| NVDA | 1351 | 0 | 0 | 0 | 0 | 0 | 0 |
| TSLA | 1463 | 0 | 0 | 0 | 0 | 0 | 0 |
| AMD | 1463 | 0 | 0 | 0 | 0 | 0 | 0 |
| MU | 1046 | 0 | 0 | 0 | 0 | 0 | 0 |
| GOOGL | 1463 | 0 | 0 | 0 | 0 | 0 | 0 |
| KLAC | 1046 | 19 | 1 | 0 | 0 | 0 | 5 |
| MRVL | 1046 | 19 | 1 | 0 | 0 | 0 | 2 |
| LRCX | 1046 | 19 | 1 | 0 | 0 | 0 | 3 |
| TXN | 1046 | 19 | 1 | 0 | 0 | 0 | 6 |
| AMAT | 1046 | 19 | 1 | 0 | 0 | 0 | 2 |

## Implementation notes (faithful-simplest choices)

1. Signing reuses the f1_prong0 machinery verbatim (sign_prints): prevailing mid = last bbo1s quote (bid>0 AND ask>bid) with ts<=trade ts (searchsorted right-1, guarded, completed-second, never a future quote); px>mid=+1, px<mid=-1; px==mid or no-prior-quote -> tick vs the previous ODD-LOT print price; remaining ties carry the last non-zero sign. The 'previous print' is the previous row of the t-1 off-exchange odd-lot subset (the gated print universe), sorted by ts. >=30 SIGNED prints (sign!=0) are required. 2. bars1d RAW open/close columns are the price anchors (this lake is the raw refetch; column names verified as 'open'/'close'). Session t-1/t-2 are that name's prior bars1d SESSIONS (rows), not calendar days; ET session date = bars1d ts converted to America/New_York. 3. bbo1s carries extended hours; the early-close guard (last valid two-sided quote of day t < 15:45 ET) and all exit windows use ET seconds-of-day via searchsorted on each session's monotone sec array. exit_mid = last mid <= 15:45, required >= 15:40 (else drop). 4. A name-day enters iff trades[t-1], bbo[t], bars1d[t] exist; bbo[t-1] is also required to quote-sign (a day with no valid t-1 quotes is dropped as no_bbo_tm1 rather than signed purely by tick rule). Only the two stated scientific guards (>=30 signed prints on t-1; early-close on t) gate the panel; the other funnel rows are data-availability / missing-exit attributions. 5. GATE (a): per-name OLS (numpy lstsq) of OLI and ret on [1, gap, ret_prev]; residuals pooled; both pooled residual series winsorized at pooled 1/99 (numpy percentile, linear); Pearson rho. A name with < 5 kept rows is skipped from (a) (counted). The bootstrap resamples the FIXED winsorized residuals by session -- residuals and winsor bounds are computed once and reused (no per-rep refit). 6. GATE (b): per-name Q3 of |OLI| over that name's kept sample; top-quartile = |OLI| >= Q3; signed_fade = -sign(OLI)*ret RAW; a name with Q3==0 is dropped (counted). Winsor(1/99) mean is reported non-gating. 7. Bootstrap = fresh numpy default_rng(7) per gate; n_sessions draws of distinct ET session dates with replacement, each drawn date contributing all its rows (repeats included); 2000 reps; 2.5/97.5 percentile CI. 8. Supporting horizons refit the per-name residualization on each horizon's own kept subset (rows with a valid exit for that horizon). Tier splits reuse the identical per-name residualization (a name's regression is independent of the pool) and winsorize within the tier. The 4x4 table bins each name-day by that name's own gap and OLI quartiles (searchsorted, ties to the upper bin); cells are pooled across names.
