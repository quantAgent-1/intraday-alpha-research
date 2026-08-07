# M16 Phase 0 — live retail execution-quality audit (REGISTERED 2026-07-18)

Supersedes PROTOCOL-DRAFT.md. Finalized with DR-X3 (wave 3; 6/6 claims refuter-confirmed).
Registered in ledger as `M16-phase0-execution-audit-v1` BEFORE any order. Cost-model family,
not alpha. Execution is MANUAL — the user keys every order (signal-only program).

## Purpose

Measure OUR effective/quoted spread ratio (E/Q) at Alpaca for $400-$3,000 marketable clips on
the champion names, in two time regimes. DR-X3 priors: mid-day E/Q 0.55-0.70 (CONFIRMED class,
605 + literature); last-15-minutes UNKNOWN (stress 0.9-1.5+; our sim shortfall at 15:55:10 =
1.46 bps vs 0.73 half-spread implies E/Q ≈ 2.0 with mid-drift). The number decides the M16
cost model and bounds the smallness-subsidy thesis.

## Design (frozen)

- **Names:** NVDA, TSLA, AMD, MU, GOOGL (owned SIP ground truth).
- **Order-type contrast (DR-X3 C8: marketable-limits fill WORSE than market in 605):**
  50% plain market, 50% marketable limit at touch + 1 tick through. Randomize by coin flip
  per clip; log which.
- **Buckets:** (a) MID-DAY 13:00-14:30 ET; (b) LAST-15 15:45-16:00 ET (record the 15:55:10-
  15:58 sub-window tag for champion-window analysis).
- **Clips:** target ≥250 round-trips total (≥100/bucket), ~10-15/day over ~4 weeks, both
  sides alternating (buy→flatten / short→cover only if locate is trivial; else long-side
  pairs only — log the choice). Clip size $400-800 nominal, whole shares.
- **Exposure bound:** ≤$800 at any instant; flatten within 5 minutes; abort-and-record any
  round-trip losing >$5 to an execution anomaly.
- **Per-fill log (the blotter):** symbol, side, order type, decision-time NBBO (bid/ask/mid
  from the screen at send), send time, fill price/time/venue-if-shown, size. Weekly
  reconciliation vs owned SIP quotes (PROTOCOL v6.1 case-level fill ground-truthing).
- **Metrics:** E = 2·|fill − mid_decision|/mid; Q = (ask−bid)/mid at decision; E/Q per clip;
  medians + p75 per bucket × order type. Estimated total measurement cost (paid spreads):
  ~$10-20 across the full audit.

## Pre-registered outcomes and decision rules

- **Hypotheses (DR-X3 bounds):** mid-day median E/Q ∈ [0.40, 0.75]; last-15 median ∈ [0.50, 1.20].
- **Promote:** two-bucket E/Q enters the sim fill kernel as
  `cost = 0.5 · quoted_spread · E/Q_bucket + 0.3 bp residual` (M16 + forward-paper annotation).
- **Kill the optimistic M16 pad:** last-15 median E/Q ≥ 0.95 → no cost cut near the close;
  M16 (if run) prices full shortfall there.
- **Bound the smallness thesis:** mid-day median E/Q ≥ 0.95 → no retail execution subsidy
  exists for us; recorded as the thesis's honest bound.
- **Order-type rule:** whichever type shows lower median E/Q at n≥50/type becomes the deploy
  default (with the market-order price-collar caveat logged).

## Non-negotiables

No mid-audit design changes; every fill ground-truthed; no directional intent (flatten
immediately); the audit never coexists with a live champion position in the same name+minute.
