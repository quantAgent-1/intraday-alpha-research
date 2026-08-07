# M8-v2 — mechanism-informed meta-gate: CANDIDATE FEATURE DRAFT (2026-07-19)

**STATUS: REGISTERED 2026-07-20** (ledger M8-v2-mechanism-features-v1; frozen bars in
M3_REGISTRATION.md §M8-v2). Run EARLY on user instruction — the draft's after-the-gate
precondition superseded, with a HARD ADOPTION FENCE: forward streams judge frozen M8-v1
until the M10 gate regardless of this look's outcome; a PASS queues for gate-time adoption.
Family: `moc_meta_v1` (extends M8/M9) — this will be the family's THIRD look; the bar rises.
Provenance: `research/deep/EXT-ML-MOMENTUM-2026-07-19.md` (verified external ML-momentum
suggestions) + M12 promotion path (HANDOFF: "trading adoption only via M8-v2 registration
after the forward gate").

## Thesis — and why this is not M9 re-skinned

M9's NULL established that the snapshot GBDT is the ceiling **on the auction-feed information
set** (within-window path scalars added nothing). M8-v2 does not add more feed detail; it adds
variables from OUTSIDE the feed, each tied to an identified payer (M12 single-stock LETF flow),
a registered diagnostic fact (M14 calendar), or a cheap owned day-state. Momentum enters only
as conditioning information on the champion — never as a standalone signal (doctrine 2026-07-19).

## Frozen candidate set (final registration may REMOVE candidates, never add)

All features must be strictly observable at the 15:55:10 ET decision instant (M9 leakage
boundary + parity unit-test discipline). Day return proxy = prev close → last bbo-1s price
≤ 15:55:10. Data: owned only (NOII, bbo-1s core 5, LETF AUM anchors, calendar); $0.

| # | Feature | Definition (exact form frozen at registration) | Receipt / prior |
|---|---|---|---|
| 1 | `abs_f_over_adv` | \|F(t)\|/ADV20; F(t) per M12's frozen computation: Σ over the name's complex of AUM×(L²−L)×day-return proxy | M12 Cell C: +0.510 bps/sd [0.093, 0.883] surviving controls; monotone tercile lift |
| 2 | `flow_aligned` | sign(F(t))·sign(basis) | M12 Cell A: aligned vs anti +1.63 bps / +3.7 dir pts — the ONE legitimate entry point for day-direction "momentum" (flow re-hedges WITH the move) |
| 3 | `complex_intensity` | complex total AUM / dollar ADV20, month t−1 (slow scale) | M12 rank test: name-year tercile dir T1 −0.14 → T3 +2.91 |
| 4 | `range_pos_1555` | (P@15:55 − day low)/(day high − day low), bbo-1s | day-shape/close-location state; weak-medium prior; only non-flow continuation candidate |
| 5 | `month_end` | last-trading-day-of-month dummy | M14: MONTH_END +5.55 vs ordinary +1.27, all 7 years (quad-witching dummy reported alongside, never decisive — cell still UNMAPPED) |
| 6 | `day_vol_ratio` | realized vol 09:30→15:55 (1-min sampled bbo-1s) / vol20 | DR-X4: TOD vol structure ALIVE as prior; day-stress conditioning |

Explicitly NOT in v2: sequence/NN models (M4/M9 dead), regime/trailing-PnL features (3× dead),
path/duration/range features (DOCTRINE-BANNED), news/sentiment (no sourced payer), any
candidate beyond these six.

## Evaluation design (frozen intent)

- Model: LightGBM binary P(net_bps>0), **M8's frozen hyperparameters — no search**; identical
  expanding walk-forward folds (6-mo blocks, ≥2y train, 1-session embargo). One spec, one look.
  Drop-column ablation REPORT-ONLY.
- **Two mandatory baselines on the identical OOS span:**
  1. M8-v1 gated stream (P≥0.55) — model-vs-model delta of the new information.
  2. **Occam gate:** the single-feature `abs_f_over_adv`+`flow_aligned` filter (the M12
     promotion object). If the full model does not beat the simple filter on gated-stream
     Sharpe, ADOPT THE FILTER — this operationalizes the verified ML lesson that complex f
     must beat simple rank, not merely exist.
- Success template (numbers frozen at registration, mirroring M8's registered form): gated
  hit-rate AND (CI-lower or ≥20% Sharpe) improvement vs baseline 1, breadth ≥3 symbols ×
  ≥3 years, plus the Occam gate vs baseline 2. KILL: no improvement over EITHER baseline →
  the snapshot ceiling extends to mechanism features; M8-v1 stands and the F/ADV filter
  remains report-only.

## Preconditions before registration

1. M10 forward gate met (the clock decides when).
2. F/ADV forward filter numbers reported next to the M10 streams (promised M12 promotion step).
3. Q18 wave input (meta-labeling at small n — calibration + feature-count priors) folded in
   if available; desirable, not blocking.

## Wave-4 note (2026-07-20): external validation + candidate thresholds for F_t

- DR-X7 (modalities A/B, refuter-verified): the F formula has published support — Barbon et
  al.'s leverage-adjusted AUM × since-prior-close return is exactly M12's F; the r-window is
  disclosure-pinned to since-prior-close; prospectus template = close-only execution, so the
  flow prints INTO the cross this trade reads. Mechanism prior for this registration is
  strengthened.
- Candidate a-priori thresholds (from DR-X7-B; finalize at registration): F_t must add
  ≥ +1.0 bps/event net incremental over NOII-only, OR lift hit-rate ≥ 2 pts with
  corr(F_t stream, NOII stream) < 0.6. KILL: corr(F_t, observed NOII imbalance) > 0.8
  (redundant — the M9 snapshot-ceiling outcome) or incremental ≤ 0.
- Gating unchanged: M10 forward gate first.

## Build plan (per standing delegation rule, 2026-07-19)

At registration time: feature builders + eval harness are written by a delegated agent (Sonnet;
mechanical from this spec + registration text) with unit tests for the 15:55:10 parity/leakage
boundary; orchestrator writes the registration, reviews the code line-by-line, runs the one look, and
owns the verdict.
