# M16 Phase 0 — live retail execution-quality audit (PROTOCOL DRAFT, 2026-07-18)

STATUS: REGISTERED 2026-07-18 (ledger: M16-phase0-execution-audit-v1, after DR-X3 returned
with the E/Q prior). Arm-B amendment ledgered 2026-07-20 (M16-phase0-armB-amendment) BEFORE
any arm-B order. Execution is MANUAL (the user keys every order; signal-only program — no
code path routes orders, ever). Awaiting user screen time during US RTH to begin.

## Purpose

Measure what OUR flow actually pays: effective spread vs quoted spread (E/Q ratio) and price
improvement for small marketable orders at the live broker (Alpaca). This is the load-bearing
number for the user's smallness thesis and the M16 intraday-book cost model. Sims charge full
half-spread + 0.5-1 bp; if measured E/Q ≈ 0.4-0.6, the intraday arithmetic changes materially;
if ≈ 1.0, the thesis is bounded honestly.

## Design (v0 — finalize benchmarks per DR-X3)

- **Instrument set:** NVDA, TSLA, AMD, MU, GOOGL (owned reference data for ground truth).
- **Order profile:** marketable limit (limit = touch + 1 tick through), 1-N shares targeting
  $200-800 clips — the deploy-relevant size. Both sides (buy then sell to flatten; each pair
  = one round-trip observation).
- **Timing buckets (pre-registered):** (a) mid-session 13:00-14:30 ET (calm baseline),
  (b) 15:45-15:54 (pre-close), (c) 15:55:10-15:58 (the champion's actual entry window).
  Balanced count per bucket.
- **Sample size:** 60 round-trips (~20/bucket) over ≥10 sessions — enough for median/p75 E/Q
  per bucket at the effect sizes that matter (we care about 0.5 vs 1.0, not 0.90 vs 0.95).
- **Total exposure bound:** ≤$800 notional at any instant; flatten within minutes; expected
  measurement cost = paid spreads ≈ 60 × ~1-2 bp × ~$500 ≈ **$3-6 total** (that is the real
  price of the number).
- **Ground truth per fill:** NBBO snapshot at send (from the quote we key against) + broker
  fill price/time; E = 2·|fill − mid|/mid; Q = quoted spread/mid at send; log venue if the
  broker reports it. Reconcile weekly against owned SIP data (case-level fill ground-truthing,
  PROTOCOL v6.1 discipline).
- **Confounds to log:** spread state at send, order side vs last tick direction, size, tick
  constraint (spread = 1 tick ⇒ improvement capped at midpoint), any reject/partial.

## Pre-registered outcomes

- **Primary:** median E/Q per bucket, pooled E/Q, and improvement % of half-spread.
- **Decision rule (feeds M16 cost model):** M16 Phase A prices costs at measured
  p60 E/Q per bucket (conservative-of-center). If pooled median E/Q ≥ 0.9 → smallness gives
  no execution subsidy; M16 proceeds (if at all) on the full-spread cost model and the thesis
  is recorded as bounded. If ≤ 0.6 → re-price the dead intraday arithmetic and the M16
  registered look becomes live.
- **Also informs:** the forward-paper entry-cost annotation (live vs sim divergence rule
  already registered under M10).

## What DR-X3 must settle before registration

1. Benchmark definition parity with Rule 605 (so our numbers are comparable to wholesaler
   disclosures); 2. whether marketable-limit orders are treated differently from market
   orders by wholesalers (would change the order type used); 3. expected E/Q prior by bucket
   (so the sample size can be power-checked); 4. any Alpaca-specific routing facts.

## Wave-4 amendment (2026-07-20): resting-limit arm (arm B)

Alongside the marketable arm (arm A), an equal-count **touch-RESTING (non-marketable) limit
arm** on the same names and timing buckets: post at the touch, cancel if unfilled after 60 s;
log fill-within-window, NBBO at send, and 1–5 s post-fill mid markout per fill.

- **Pre-registered thresholds (frozen now, from wave-4 DR-X8 convergence):** resting fill
  ≥ ~80% AND mean markout ≥ −0.2 bp → fee-boundary registrations may reopen on
  COST_MODEL-floor pricing. Fill ≤ ~65% OR markout ≤ −0.5 bp → maker-first intraday is
  closed PERMANENTLY (EXHAUSTION_MAP row updates from literature-prior to measured).
- **Priors going in (falsifiable):** blended touch-fill 20–50%; favorable-subset fill
  2–15%; markout −0.5..−1 bp (`research/deep/WAVE4_SYNTHESIS.md` §DR-X8).
- **Cost**: adds ≈ $2–4 to the measurement budget (unfilled posts are free; filled posts
  flatten immediately per arm-A rules).
- All future intraday cost assumptions: `research/COST_MODEL.md` v1.

## Non-negotiables

Register (ledger + M3_REGISTRATION.md) BEFORE the first order; no mid-audit design changes;
all fills ground-truthed against owned SIP; the audit measures execution ONLY — no
directional intent, flatten immediately; abort the audit if any single round-trip loses
> $5 to an execution anomaly (record it — that datum matters too).
