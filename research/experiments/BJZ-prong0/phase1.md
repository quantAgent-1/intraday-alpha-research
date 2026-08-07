# BJZ prong-0 — Phase 1 (discovery 10) — METHOD VALIDATION ONLY

Gates pre-declared in PREDECLARATION.md before any computation. A pass here can
NEVER confirm the effect (design-only panel, third expression of one phenomenon);
it only licenses the Phase-3 virgin-name test.

## discovery-10 (rimb)
- name-days 1,118 fires; T=514 sessions; 2.18 fires/day
- daily MID    -0.84  [ -18.43,  +16.31]
- daily NET (primary, cost 3.21)    -4.05  [ -21.63,  +13.10]
- daily NET (optimistic, cost 1.06)    -1.90  [ -19.48,  +15.25]
- daily NET (double, cost 6.21)    -7.05  [ -24.63,  +10.10]
- event-level mid   +0.08 [ -16.35,  +16.31]
- per-name means: AMAT -34.8, AMD +30.5, GOOGL +28.8, KLAC +31.2, LRCX -19.9, MRVL -12.3, MU -2.6, NVDA +12.7, TSLA +74.9, TXN -9.3
- by year: 2024 -5.8 (n=517), 2025 -2.7 (n=378), 2026 +18.4 (n=223)

- corr(BJZ RIMB, quote-signed odd-lot OLI) on 4,348 matched name-days: **+0.0661** (support, non-gating)

## discovery-10 odd-lot variant (rimb_odd)
- name-days 1,118 fires; T=520 sessions; 2.15 fires/day
- daily MID   +15.71  [  -0.53,  +32.17]
- daily NET (primary, cost 3.21)   +12.50  [  -3.73,  +28.97]
- daily NET (optimistic, cost 1.06)   +14.65  [  -1.58,  +31.12]
- daily NET (double, cost 6.21)    +9.50  [  -6.73,  +25.97]
- event-level mid  +14.30 [  -1.52,  +30.74]
- per-name means: AMAT -14.2, AMD +55.1, GOOGL +18.1, KLAC +29.6, LRCX +17.3, MRVL +17.3, MU +19.1, NVDA +10.9, TSLA -16.6, TXN +14.0
- by year: 2024 +1.3 (n=556), 2025 +20.4 (n=364), 2026 +39.7 (n=198)

## GATES
- G1 daily net (primary cost) CI-lo > 0: -21.63 -> FAIL
- G2 gross >= 2x cost (6.41): -0.84 -> FAIL

## VERDICT: METHOD-FAILED
