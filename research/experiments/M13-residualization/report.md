# M13 close-factor residualization (Q16 offline) — RESULT 2026-07-17

Registered before running (ledger `M13-residualization-v1`; spec in M3_REGISTRATION.md).
Panel: M6-FINAL-basis events (5 names, 2020-2026, n=7,959; all |basis|>=10, net of sim costs).

## Numbers (hedge = net − β·factor, β in-sample from covariance; factors side-signed)

| Factor | Window | n | R² | β | raw mean/sd | hedged mean/sd |
|---|---|---|---|---|---|---|
| F1 LOO cross-name mean | 2020-2026 | 7,959 | 0.047 | 0.37 | +1.55 / 21.4 | +0.98 / 20.8 |
| F1 | 2023-07→2026-07 | 3,605 | 0.050 | 0.38 | +1.36 / 18.6 | +0.84 / 18.2 |
| F2 TQQQ/3 (NDX proxy) | 2023-07→2026-07 | 3,605 | **0.208** | 0.73 | +1.36 / 18.6 | +1.30 / 16.6 |
| F3 SOXL/3 (semis proxy) | 2023-07→2026-07 | 3,605 | **0.247** | 0.64 | +1.36 / 18.6 | +1.56 / 16.2 |
| Joint F1+F2+F3 | 2023-07→2026-07 | 3,605 | **0.276** | — | +1.36 / 18.6 | +1.25 / 15.9 |

Per-name F1 (full sample): AMD R² 0.117, NVDA 0.108, MU 0.059, TSLA 0.022, GOOGL 0.001;
hedged means: NVDA +2.00, TSLA +2.67, AMD +0.65, MU +0.06, GOOGL −0.54.

## Verdict vs registered thresholds (adopt iff R²≥0.20 AND hedged mean ≥ +2.0; kill iff R²<0.10 OR mean <+1.0)

- **F1 (LOO): KILLED** — R² 0.047 and hedged mean 0.98 both breach kill bounds. Cross-name
  same-session co-movement is NOT the main common factor.
- **F2/F3/joint: REPORT-ONLY, NOT ADOPTED** — the R² bar clears (0.21-0.28: a quarter of event
  variance IS a common close-window market/sector factor, real and economically sensible) but
  the hedged mean (1.25-1.56) cannot reach +2.0 because the raw subsample mean is only +1.36.
  The adoption failure is a MEAN-thinness fact, not a hedge failure: sd falls 18.6→15.9 (−15%)
  with mean roughly preserved; per-event Sharpe 0.073→0.079 (marginal).

## Implications

1. M10 forward reporting stays RAW (registered gate untouched; no secondary residual metric).
2. The confirmed factor loading (β≈0.6-0.7 on side-signed NDX/semis close-window returns) is a
   real risk-model fact: champion events carry ~25% market-factor variance in the last 5 minutes.
   If forward-paper ever needs a variance-cut, re-register with FROZEN β from this window.
3. Honest flag: pooled 2023-07+ raw mean is +1.36 (GOOGL and MU drag) vs +2.5 full-sample
   headline — consistent with M11's narrow-edge conclusion, and another reason the M12 name
   filter matters more than variance engineering.
