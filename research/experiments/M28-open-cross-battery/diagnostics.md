# M28 diagnostics -- NULL-AT-ADMISSION (train only)

No signal cleared Benjamini-Hochberg FDR at q=0.10 across the 14 candidates, so no composite exists. **The validate period (2025-06-02..2026-05-29) was never read** and remains clean for a future, better-powered family. Everything below is computed on TRAIN only.

## 1. Per-signal train IC (all 14)

| signal | train IC | 95% CI | p | sessions | FDR threshold at its rank | admitted |
|---|---|---|---|---|---|---|
| dvol_z | -0.0078 | [-0.0190, +0.0031] | 0.1580 | 351 | 0.0071 | no |
| ret1_x_dvol | -0.0092 | [-0.0224, +0.0038] | 0.1740 | 351 | 0.0143 | no |
| pm_range | -0.0138 | [-0.0365, +0.0080] | 0.2080 | 351 | 0.0214 | no |
| pm_ret | -0.0134 | [-0.0366, +0.0116] | 0.2970 | 351 | 0.0286 | no |
| pm_late | -0.0068 | [-0.0210, +0.0076] | 0.3610 | 351 | 0.0357 | no |
| rvol21 | -0.0108 | [-0.0362, +0.0144] | 0.3930 | 351 | 0.0429 | no |
| ret21 | +0.0084 | [-0.0131, +0.0310] | 0.4460 | 351 | 0.0500 | no |
| id_minus_on | +0.0066 | [-0.0128, +0.0264] | 0.5210 | 351 | 0.0571 | no |
| clv | +0.0051 | [-0.0113, +0.0218] | 0.5530 | 351 | 0.0643 | no |
| ret5 | +0.0058 | [-0.0149, +0.0280] | 0.5930 | 351 | 0.0714 | no |
| on_prev | -0.0052 | [-0.0281, +0.0169] | 0.6120 | 351 | 0.0786 | no |
| ret1 | +0.0036 | [-0.0148, +0.0229] | 0.7410 | 351 | 0.0857 | no |
| pm_accel | +0.0024 | [-0.0190, +0.0228] | 0.8360 | 351 | 0.0929 | no |
| pm_vol_z | +0.0003 | [-0.0127, +0.0131] | 0.9670 | 351 | 0.1000 | no |

Smallest p-value is **0.1580** (dvol_z); the FDR threshold it had to clear is **0.0071**. The battery misses by more than an order of magnitude -- this is not a near-miss.

## 2. What this null rules out

- median per-signal IC standard error on train: **0.0103**
- an IC of **0.0207** (t=2) would have been detectable for a single signal; none of the 14 reached half of that
- largest |IC| observed: **0.0138**

A daily cross-sectional IC of ~0.02-0.03 is the rough threshold below which a dollar-neutral decile book cannot clear a 3 bps round-trip cost at this breadth. Every candidate here sits at or below **0.014**, i.e. the observed effects are not merely insignificant -- they are too small to be tradeable even if real.

## 3. Breadth of the candidate battery (train L/S streams)

- mean pairwise rho across the 14 candidate streams: **+0.040**
- implied effective breadth **N_eff = 9.21** of 14
- max |rho| between any two candidates: **0.810**

Breadth was NOT the binding constraint: the candidates are close to independent. The constraint is that none of them predicts.

## 4. Coverage funnel

- names processed: 184
- name-days kept: 100,271
- dropped `no_hist`: 110
- dropped `few_rth`: 5,025
- dropped `no_exit`: 1
- dropped `bad_price`: 0
- dropped `no_pm`: 34,751
- train: 58,259 name-days over 354 sessions

