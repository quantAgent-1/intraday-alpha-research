# M23 dynamic-sizing shadow -- panel

REPORT-ONLY (family sizing_shadow_v1). No gate, no promotion rule. delta_t = sized - equal at matched gross; SR0=0 (ruling A7).

> dev-reference p_win = leakage-free OOS walk-forward column (M8-meta-v1/oos_predictions.parquet, ruling A1). The FORWARD path uses the frozen model's stored p_win.

Multiple-testing context: 202 inherited trial families (protocol.INHERITED_TRIAL_FAMILIES) + ~23 in-house families. PSR/MinTRL are read against these honest counts; SR0=0 (ruling A7).

## Dev reference

### Dev reference section (source=dev)

- T-to-date (sessions): 1096
- mean delta_t (USD, $10k book): 5.4895
- day-clustered 95% CI: [3.3176, 7.7715]
- native-frequency SR: 0.1494
- PSR[SR0=0]: 1.0000
- displayed SE sigma_sr(SR_hat): 0.0301
- MinTRL(alpha=0.05): 130.4300
- (gamma3, gamma4, rho): (1.0341, 14.4411, 0.0367)
- degenerate / single-event / multi-event sessions: 47 / 4 / 1092
- vol-history skips (events sized at v=1.0 NEUTRAL, <21 prior closes): 0
- deploy lens ($1k, informational only): mean 0.6587

## Forward to date

### Forward to date section (source=forward)

- T-to-date (sessions): 3
- mean delta_t (USD, $10k book): 45.5092
- day-clustered 95% CI: [0.0000, 131.9923]
- native-frequency SR: 0.6073
- PSR[SR0=0]: 0.8893
- displayed SE sigma_sr(SR_hat): n/a
- MinTRL(alpha=0.05): 5.4300
- (gamma3, gamma4, rho): (1.7249, 1.5000, -0.1495)
- degenerate / single-event / multi-event sessions: 1 / 0 / 3
- vol-history skips (events sized at v=1.0 NEUTRAL, <21 prior closes): 0
- deploy lens ($1k, informational only): mean 5.4611

## M10 streams

### M10 display streams (gate UNTOUCHED -- display only)

| stream | T | SR | PSR[SR0=0] | sigma_sr | MinTRL |
| --- | --- | --- | --- | --- | --- |
| classical | 3 | 0.4757 | 0.8428 | n/a | 8.0200 |
| meta | 2 | 0.4946 | 0.8871 | 0.4082 | 3.6900 |
| portfolio | 2 | 0.8556 | 0.9820 | 0.4082 | 1.2300 |

