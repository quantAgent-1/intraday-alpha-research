# F3 prong 0 -- opening-imbalance -> intraday-return pre-check

PRE-DECLARED DIAGNOSTIC (ledger row `F3-prong0-predeclaration`, ts 2026-07-23T13:24:06Z). PASS/FAIL below is mechanical.

Roster (10): AMAT, AMD, GOOGL, KLAC, LRCX, MRVL, MU, NVDA, TSLA, TXN  |  cap ts < 2026-06-01 ET  |  dropped (<100 days): none
Main analysis set (11:00): n=11487 name-days over 1608 sessions.

## Snapshot side-code counts (state variable)

| name | B (+1) | A (-1) | N (0) | other |
|------|--------|--------|-------|-------|
| AMAT | 140 | 141 | 409 | 0 |
| AMD | 443 | 604 | 563 | 0 |
| GOOGL | 567 | 547 | 496 | 0 |
| KLAC | 92 | 94 | 504 | 0 |
| LRCX | 135 | 134 | 421 | 0 |
| MRVL | 107 | 168 | 415 | 0 |
| MU | 380 | 432 | 798 | 0 |
| NVDA | 542 | 604 | 464 | 0 |
| TSLA | 527 | 688 | 395 | 0 |
| TXN | 117 | 103 | 470 | 0 |

## GATE (a) INFO -- pooled winsorized rho(R, fwd_bps 11:00)

rho = -0.0004  |  95% CI (session-clustered) [-0.0219, 0.0213]  |  gate rho>=0.03 AND CI-lo>0  ->  FAIL
(n=11487 name-days, 1608 sessions; seed 7, 2000 reps)

## GATE (b) MAGNITUDE -- per-name |R| top-quartile signed fwd (11:00)

mean signed_fwd = 2.8612 bps  |  95% CI [-3.6577, 10.0146]  |  gate mean>=6.0 AND CI-lo>0  ->  FAIL
(top-quartile n=2874; names dropped for Q3==0: none)
non-gating winsor(1/99) mean = 2.3449 bps  CI [-3.7331, 9.0398]

## Support 1 -- other horizons (point estimates, no CI)

| horizon | n | rho_winsor | topq_n | topq_mean_signed_bps |
|---------|---|-----------|--------|----------------------|
| 1100(main) | 11487 | -0.0004 | 2874 | 2.8612 |
| 1005 | 11487 | 0.0035 | 2874 | 1.1184 |
| 1035 | 11487 | -0.0013 | 2874 | 0.9241 |
| 1545 | 11457 | 0.0188 | 2868 | 13.1284 |

## Support 2-3 -- R_paired variant and pre-cross snapshot (11:00)

R_paired rho_winsor = 0.0179 (n=11487)
pre-cross(<=09:29:55) rho_winsor = -0.0173 (n=11487); topq mean = -5.0353 bps (topq_n=2874)

## Support 4 -- per-name (main 11:00)

| name | n_days | rho_winsor | q3_absR | topq_n | topq_mean_bps |
|------|--------|-----------|--------|--------|---------------|
| AMAT | 690 | -0.0287 | 0.000224 | 173 | -1.2435 |
| AMD | 1608 | -0.0020 | 0.000291 | 402 | 6.0313 |
| GOOGL | 1608 | -0.0166 | 0.000708 | 402 | -2.0415 |
| KLAC | 687 | -0.0969 | 0.000034 | 172 | -14.0022 |
| LRCX | 690 | -0.0231 | 0.000221 | 173 | -9.2425 |
| MRVL | 690 | 0.0612 | 0.000219 | 173 | 11.2854 |
| MU | 1608 | 0.0358 | 0.000327 | 402 | 12.9146 |
| NVDA | 1608 | 0.0178 | 0.000385 | 402 | 8.8089 |
| TSLA | 1608 | 0.0044 | 0.000300 | 402 | 6.1619 |
| TXN | 690 | -0.1246 | 0.000103 | 173 | -13.4135 |

## Support 5 -- coverage / sparsity

| name | cand | w/opening | oc med | frac_state0 | absR_p50 | absR_p90 | absR_p99 |
|------|------|-----------|--------|-------------|-------|-------|-------|
| AMAT | 690 | 690 | 139 | 0.593 | 0.000000 | 0.000822 | 0.003500 |
| AMD | 1610 | 1610 | 138 | 0.350 | 0.000077 | 0.000635 | 0.002150 |
| GOOGL | 1610 | 1610 | 138 | 0.308 | 0.000228 | 0.001477 | 0.005990 |
| KLAC | 690 | 690 | 139 | 0.729 | 0.000000 | 0.000528 | 0.002982 |
| LRCX | 690 | 690 | 139 | 0.610 | 0.000000 | 0.000829 | 0.003416 |
| MRVL | 690 | 690 | 139 | 0.601 | 0.000000 | 0.000700 | 0.002416 |
| MU | 1610 | 1610 | 138 | 0.496 | 0.000005 | 0.000815 | 0.003196 |
| NVDA | 1610 | 1610 | 138 | 0.288 | 0.000138 | 0.000804 | 0.003632 |
| TSLA | 1610 | 1610 | 138 | 0.245 | 0.000106 | 0.000626 | 0.002008 |
| TXN | 690 | 690 | 139 | 0.681 | 0.000000 | 0.000509 | 0.003319 |

### Drop fractions (first-failing guard, order: early_close, no_snapshot, imb_null, no_adv, no_anchor, no_exit_1100)

| name | cand | early_close | no_snapshot | imb_null | no_adv | no_anchor | no_exit_1100 | main_days |
|------|------|-------------|-------------|----------|--------|-----------|--------------|-----------|
| AMAT | 690 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 690 |
| AMD | 1610 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 | 1608 |
| GOOGL | 1610 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 | 1608 |
| KLAC | 690 | 0.001 | 0.000 | 0.000 | 0.000 | 0.003 | 0.000 | 687 |
| LRCX | 690 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 690 |
| MRVL | 690 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 690 |
| MU | 1610 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 | 1608 |
| NVDA | 1610 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 | 1608 |
| TSLA | 1610 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 | 1608 |
| TXN | 690 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 690 |

## Support 6 -- contemporaneous sanity

rho_raw(R, open->anchor return) = -0.0310 (n=11487) -- labels how much state is already spent by 09:35.

## Implementation notes (faithful-simplest choices)

1. NOII `side` is coded {B, A, N}; 'S' never appears. 'N' rows have imbalance_shares==0. The gated 'sell -> -1' is realized as A -> -1 ('A'=ask/sell side); the literal token 'S' is also honored but is absent. Snapshot side-code counts are reported for audit. 2. Opening rows are isolated by ET time-of-day [09:00:00, 09:35:00) before applying the snapshot [09:27:30, 09:28:35] and pre-cross (<=09:29:55) sub-windows; closing-auction rows (15:5x) and any stray rows are thereby excluded. On this tape opening NOII disseminates ~every 10s from 09:25 and ~every 1s from 09:28. 3. bbo1s carries EXTENDED HOURS (valid two-sided quotes ~04:00-20:00 ET; ~17:00 on exchange half-days). The early-close guard (last valid quote < 15:45 ET) therefore fires only on truly truncated sessions and does NOT exclude exchange half-days, whose post-market quotes run past 15:45. All gated intraday windows sit inside RTH and are unaffected. 'Last quote of the day' uses the last valid two-sided mid. 4. mid=(bid+ask)/2 with bid>0 AND ask>bid. anchor/exit found via searchsorted on the per-session ET-seconds array (monotone within a session), guarded against index -1 wrap. 5. ADV20 = shift(1).rolling_mean(20, min_samples=20) of daily bars1d volume (bars1d ts is ET-midnight; date via America/New_York); a session date not present in bars1d, or with <20 prior bars, drops (no_adv). 6. Session date = ET calendar date; joins across NOII/bbo1s/bars1d are by that date string. Candidates = bbo1s sessions with ET date < 2026-06-01. Duplicate NOII ts within the snapshot window -> last by ts order. 7. Winsorization = numpy clip at pooled 1st/99th percentiles (numpy linear interpolation). Per-name and per-horizon rho re-use the pooled winsor bounds where a pooled set exists; supporting-horizon top-quartile Q3 breakpoints are recomputed over each horizon's own kept set. The open->anchor sanity rho is raw (spec did not request winsor). 8. Bootstrap: a fresh numpy default_rng(7) per gate; n_sessions draws of distinct session dates with replacement, each drawn date contributing all its rows; 2000 reps; 2.5/97.5 percentile CI.
