# ISO institutional-sweep imbalance — prong-0 PRE-DECLARATION

Written 2026-07-27, **before any return statistic involving ISO flow was computed.** The
only prior computation is an existence probe (counts only): ISO-flagged prints are 27.6–33.8%
of all prints on the 10-name panel (NVDA ~392k/day, KLAC ~12k/day) — sample is not a constraint.

## 0. Why this axis is genuinely new (fence audit)

Every consumed tape expression in this program has been **retail** (odd-lot off-exchange:
R2-A and its variants) or **book state** (F1 depth — killed because *depth* did not predict
flow). The **signed aggressive institutional flow** channel — prints flagged as Intermarket
Sweep Orders, the mechanism informed/urgent traders use to take multiple venues at once
(trade-through-exempt under Reg NMS; Chakravarty et al. find ISOs are the more informed
subset of trades) — has never been read by any registered family, prong-0, or diagnostic.
Not M3/M5 (price-pattern payer detectors), not F1 (depth→flow, the reverse direction), not
M28 (bars only), not DR-X4/M18 (reversion systems / lead-lag). The round-1 "retail
marketable flow — EMPTY (horizon)" note concerned retail, not institutional, flow.

## 1. Hypothesis (direction fixed now)

**Continuation.** Day t−1 net ISO buying pressure predicts a **positive** day-t open→15:45
return (the unexecuted remainder of urgent parent orders keeps pressing; the payer is the
completing institution). The fade direction is reported as a mirror diagnostic but is NOT
the hypothesis. Honest prior: **~0.10** — daily-horizon order-flow predictability on
megacaps is weak in the field; the ISO subset being more informed is what makes it worth
one $0 look.

## 2. Frozen statistic

Per name, session t: prints of day t−1, RTH, condition list containing `F` (any venue),
signed by the **frozen** `r2a_prong0.sign_prints` against the owned `bbo1s` prevailing mid;
IIMB = size-weighted (buy−sell)/(buy+sell) over signed ISO prints, ≥30 signed required.
Fire when |IIMB| ≥ that name's own Q3(|IIMB|); position **+sign(IIMB)** (follow) entered at
the day-t opening cross, exit = last bbo1s mid 15:40–15:45 (frozen `exit_mid`); outcome ret
in bps from the RAW `bars1d` open (identical L2 convention to R2-A so results are directly
comparable). Cap < 2026-06-01.

**Primary**: mean of the daily equal-weight portfolio of fires, **net** of measured
per-name exit half-spread (the ten `bbo1s`-measured values) + 0.206 SEC fee; entry at the
cross = 0. Session bootstrap, seed 7, 2,000 reps.

**Gates (prong-0 vocabulary, no family charged):**
- **PASS-CANDIDATE** — net CI-lo > 0 AND gross ≥ 2× mean cost → registration proposal
  (which would additionally require NBBO re-validation, given the V-QS finding).
- **KILL** — mid CI-hi < **+2.0** bps (no tradeable effect is hiding in the interval).
- **PARK-UNDERPOWERED** — otherwise.

## 3. Disclosed limitations

- Signing uses the owned **XNAS** quote lake (the V-QS finding applies): exact for the
  megacaps, noisy for KLAC-class names. Acceptable for a $0 prong-0; any PASS graduates
  only through NBBO re-validation (semis NBBO quotes are landing tonight regardless).
- Ragged trades coverage (NVDA ~298 days; TSLA/AMD/GOOGL ~186) — same panel as R2-A.
- Power: expected T ≈ 510, se ≈ 8–10 bps/day ⇒ detects ≥ ~16–20 bps; smaller true effects
  land in PARK. Declared so a PARK is not read as support.

## 4. Non-gating diagnostics

Event-level CI; per-name means; year table; corr(IIMB, retail OLI) on matched name-days
(is institutional aggression just the mirror of retail?); the fade-direction mirror; a
block-print variant (notional ≥ $100k, same pipeline, report-only); fires/day; funnel.

One primary statistic, one direction, one look. This document is the whole search space.
