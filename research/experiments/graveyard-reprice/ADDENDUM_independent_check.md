# Independent check of the graveyard-reprice headline — corroborated, with one correction

2026-07-27. Computed from the cached `R2A-prong0/panel.parquet` and the frozen prong-0
definitions, **without reading `scripts/graveyard_reprice.py`**, so agreement is corroboration
rather than a re-run. Probe: session scratch, reproduced below in method.

## Corroborated

| statistic | reprice report | independent check |
|---|---|---|
| daily portfolio, mid | +22.42 [+4.35, +40.47] | **+22.36 [+4.28, +40.36]** |
| daily portfolio, net (open entry + late exit) | +20.30 [+2.16, +38.31] | **+20.78 [+2.71, +38.76]** |
| T (sessions with ≥1 fire) | 513 | **513** |
| event-level mid (session-clustered) | +15.2 [−0.71, +30.5] | **+14.87 [−1.17, +30.19]** |
| year means (event, mid) | 9.6 / 19.1 / 26.6 | **9.6 / 18.3 / 26.6** |

The event-level figure reproduces the frozen prong-0 gate (b) value exactly, which anchors the
whole comparison. Small net differences reflect a slightly different cost expression; the mid
series agree to ~0.06 bps. **Mean fires/session = 2.13**, mean daily cost 1.58 bps,
gross/cost ≈ 14×.

## Correction: the edge is NOT a disguised market bet

The report's interpretation §5 states that *"market-beta residualization of the daily fade
series also collapses mean toward 0 — the edge co-moves with the day's common return; it is
not pure CS idio alpha."* Direct measurement does not support that:

| quantity | value |
|---|---|
| universe mean open→exit return (the drift available) | +2.26 bps/day |
| mean tilt of the book | +0.151 (net long on 51.5% of days — near balanced) |
| **drift term** = mean(tilt) × mean(market) | **+0.34 bps/day (1.5% of the result)** |
| **timing term** = gross − drift | **+22.02 bps/day (98.5%)** |
| regression book ~ universe | **beta +0.121, R² 0.012** |
| **beta-hedged book** = book − β·market | **+22.09 [+3.67, +40.00]** |

The likely cause of the discrepancy: an **OLS residual series has mean ≈ 0 by construction**
(the intercept absorbs it), so residualising and then reading the residual mean will always
"collapse toward zero" regardless of the truth. The tradeable object is `book − β·market`,
which keeps the intercept — and that is essentially unchanged at +22.09.

This is the same failure mode already flagged in the report's own §5 for session-demeaning
("they zero by construction"); it applies to the beta case too.

**Consequence:** the edge survives beta-hedging, so it is *stronger* than the report concluded,
not weaker — and a hedged expression remains available as a later, separate registration.

## What this does NOT change

1. **The daily-portfolio unit was not pre-declared.** Frozen gate (b) was the EVENT mean, and
   it FAILS (+14.87, CI-lo −1.17). Switching the aggregation unit after seeing that is a
   post-hoc specification change. The report is right to refuse to rewrite prong-0, and right
   that the only clean path is a **new registration judged forward-only**.
2. **Thin books.** 2.13 fires/session means the daily mean is a small-sample average each day;
   net CI-lo (+2.71) is not far from zero.
3. **Ragged panel composition.** Trades coverage is uneven — MU and the semis span the whole
   window while NVDA (298 days), TSLA/AMD/GOOGL (186 days each) only enter late. The rising
   year means (+9.6 → +18.3 → +26.6) are therefore **partly a composition effect, not
   necessarily a strengthening regime**, and should not be read as a trend.
4. **Quote dependence stands.** R2-A's signal needs contemporaneous quotes to sign prints
   (R2-A Stage 3, METHOD-BLOCKED), so this family is confined to the 10-name panel until quote
   data is bought. That is the binding constraint on ever widening it.

## Method (for reproduction)

Per name: top quartile of |OLI| by that name's own distribution (frozen gate-b rule);
`fade = -sign(OLI) * ret`; `ret` = opening-cross print → last bbo mid ≤ 15:45. Cost = the
measured 15:40–15:45 quoted half-spread per name (stage1.md) + 0.206 bps SEC fee; entry at the
cross is free. Daily portfolio = equal-weight mean of that session's fires. Bootstrap: seed 7,
2000 reps, resampling sessions.
