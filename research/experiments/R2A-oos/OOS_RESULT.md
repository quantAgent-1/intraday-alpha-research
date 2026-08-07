# M30 `retail_fade_daily_v1` — DECISIVE OOS RESULT: **NOT-CONFIRMED** (family closed)

2026-08-01. The one registered historical look (`scripts/r2a_oos_run.py`) ran on the 16
virgin names after both backfills completed (trades 604/604 per name 2026-07-28; NBBO
quotes 375/375 monthly partitions 2026-07-29). All three refusal gates passed (V-NB
marker, registration marker, data completeness). Raw output: `phase3_result.json`.
Registration: ledger row `M30-retail-fade-daily-v1` (2026-07-28); spec =
`PREDECLARATION.md` + Amendments 2–3, all frozen before any OOS return existed.

## Headline

| quantity | value |
|---|---|
| fires / sessions | 2,402 events / **T = 589** (4.08 fires/day) |
| daily portfolio **MID** | **−1.45 bps [−8.44, +5.81]** |
| daily portfolio **NET** | **−3.85 bps [−10.84, +3.40]** |
| mean measured cost | 2.40 bps (per-name median 15:40–45 NBBO half-spread + 0.206 SEC) |
| names positive | 7 / 16 |
| tech-adjacent (QCOM/ADBE/INTU) vs rest | −0.2 vs +0.4 |
| beta vs universe / hedged MID | +0.088 / −1.67 [−8.71, +5.52] |
| sign-shuffle placebo (200 draws) | real mean at the **38.0th percentile** |

**Gate trace (pre-fixed outcomes):** CONFIRMED requires net CI-lo > 0 AND mid ≥ 2× cost —
failed (net CI-lo −10.84). REFUTED requires net CI-hi < 0 — failed (+3.40). Point
(−3.85) < +6 floor ⇒ **NOT-CONFIRMED** (not PARK-UNDERPOWERED: this is not a power
problem at these point estimates; the mean has the wrong sign).

## Adjudication (verbatim against the pre-committed reading)

Per `research/deep/DR-INTAKE-2026-07-28.md` §2, written before any OOS number existed:

> **REFUTED / NOT-CONFIRMED** → consistent with the event-level gate failure, the
> attenuation seen in related open/overnight reversals, and signing-noise dilution. It
> does NOT prove Brown's 2013–22 in-sample result spurious, and does NOT retroactively
> invalidate the discovery-panel dailies — it prices the effect as
> not-generalising-at-tradeable-size. Action: family closed; the program's next move is
> the DR-A options axis as a data decision.

Applied without modification:

- **Family CLOSED; the one look is SPENT.** No re-parameterisation, no panel widening,
  no threshold movement.
- **`scripts/rfd_live.py` stays permanently dark** — its gate refuses on
  `verdict != "CONFIRMED"` by construction (built before the verdict existed).
- The discovery-panel result (V-NB-bridged **+24.82 [+7.79, +43.31]**, T=508, 5 semis)
  stands as a **panel-local fact**: real on those names in that era, absent OOS.
- This was, per DR-C, the **first out-of-sample estimate of the Brown effect anywhere**
  (zero independent replications exist). The answer: it does not travel.

## What the diagnostics add (non-gating)

1. **Cost was not the story.** Mean cost 2.40 bps at the day's cheapest exit window and
   the MID itself is negative. Unlike M27 (real effect, 2× cost floor), here the effect
   is simply absent at mid. The open-cross → 15:40–45 execution structure remains
   validated — 2.40 bps mean all-in confirms the Session-9 cost analysis on a fresh
   16-name universe.
2. **No refuge in the pre-registered splits.** Tech-adjacent −0.2 vs rest +0.4 (both ≈0);
   hedging does not rescue it (hedged −1.67, CI unchanged); 7/16 names positive is a
   coin flip; placebo percentile 38 means the observed mean sits inside the sign-shuffle
   noise body.
3. **Program-level: third adequately-powered null in a row at this structure** — M28
   (14 bar signals, 100k name-days), M29 (short-ratio battery, "exactly zero"), M30
   (retail flow OOS). The open-print information set is now priced empty across bar,
   short-ratio, and retail-flow axes at daily-portfolio size.

## Next move (pre-committed)

The registered sequence names the **DR-A reconstructed-GEX axis** ($0–29/mo, ~2y
history) as the post-verdict data decision — the one genuinely new near-free
information class. That is a **user decision**, not a research default. Per DR-E, no
other in-scope post-2020 candidate exists in the field; a null program outcome after
this failure is honest, not lazy.

*Supersedes the METHOD-BLOCKED status in `RESULT.md` (2026-07-26): the quote unlock +
XNAS→NBBO bridge later made the test runnable; the method-block finding (trade-side
classification requires contemporaneous quotes) remains durable.*
