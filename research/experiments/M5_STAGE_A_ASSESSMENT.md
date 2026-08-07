# M5 — Stage A Assessment (2026-07-15)

## Verdict: FAIL at the registered bar. The sealed holdout is NOT consumed.

Evaluated book: A0 v1.1 (hand-rule plans on registered payer detectors; L2-strict odd-lot-robust
fills; 5–25 s per-leg latency; k=2 slots; zero-commission + spread + SEC/TAF), NVDA/TSLA/AMD/MU,
187 sessions 2025-09-02 → 2026-05-31. Champion sub-book: vwap_magnet (the only ALIVE payer).

| Stage A condition (PROTOCOL v6 §4) | Result | Pass? |
|---|---|---|
| N ≥ 250 plans, ≥ 150 sessions | 1029 / 178 (vwap book) | ✓ |
| mean net ≥ +10 bps/plan, CI > 0 | **+5.06 [1.27, 8.62]** | ✗ (half the bar) |
| top-5 sessions removed ≥ 0 | +3.16 [−0.35, 6.42] | marginal (mean ✓, CI touches 0) |
| concentration | top-5 = 39.9% of P&L, **effective n = 6.6** | ✗ (tail-concentration kill-signal) |
| 2× spread / 2× latency stresses > 0 | +10.6 ✓ / +5.6 (frame) but replay-level 2× latency CI touches 0 | mixed |
| validate-split standalone | +4.61 [−2.25, +11.62] | inconclusive |
| DSR ≥ 0.95 at family counts | not computed — moot below the mean bar | — |
| fresh-eyes adversarial review | not reached | — |

## What was PROVEN (the assets)

1. **A real, small execution-capture edge exists.** vwap_magnet: 2-symbol +6.20 [2.60, 9.99]
   (n=571), 4-symbol +5.06 [1.27, 8.62] (n=1029). Zero mid-alpha; the entire net is passive
   spread/bounce capture at detector-gated moments. Survives fill-hardening (odd-lot exclusion
   cut the naive result in half and it stayed positive), 2× spread stress, and is symmetric
   long/short. Heavily symbol-concentrated: NVDA +11.23 [5.74, 16.54]; MU +9.01 [−0.06, 17.61];
   TSLA +0.61 and AMD −0.40 ≈ nothing.
2. **A falsification machine that works.** Same-day retraction of a flattered +9.96 headline
   (odd-lot fill evidence); A1 bar-tier overlay killed in 3 registered variants (its failure
   correctly re-attributed by instrumentation); M4 event-tier encoder killed with a precise
   mechanism (stop-risk co-locates with payoff); grok E5 daily-swing killed on 465 sessions;
   letf_window / expiry_pin / cascade honestly closed (below).
3. **Real GPU deliverable:** trained TCN/PatchTST encoders with PIT-verified walk-forward
   emissions and a plan-level ablation harness that would have detected a real improvement.

## Payer dispositions (this run, ledgered)

- vwap_magnet: **ALIVE** (only payer with pooled CI > 0; NVDA-concentrated).
- letf_window: **CLOSED — no evidence** (3rd consecutive negative-lean look: −2.19 [−13.11, +9.18] n=306).
- expiry_pin: **CLOSED — no evidence** (−1.92 [−11.59, +7.52] n=45; the 2-symbol +8.5 was small-n noise).
- gap_mr: **UNPROVABLE at feasible N** (+12.11 [−31.57, +54.06] n=68; per-plan σ≈170 bps ⇒
  proving even +15 needs N≈500+, ~7 more years of 4-symbol gaps). Left registered, not pursued.
- cascade: **CLOSED — no-fire** (0 states in 748 symbol-sessions as registered).

## Why it fails, in one paragraph

The edge is real but half the size the bar demands, its P&L is tail-concentrated (effective
n ≈ 7), the validate window alone cannot distinguish it from zero, and it degrades with
execution latency. Deployed at the $1,000 account it is ~$1–2/session. The bar was set to mean
"worth trading seriously"; +5 bps/plan with this concentration does not clear it, and per
PROTOCOL the holdout stays sealed for a finalist that does.

## Paths forward (user decision)

A. **Forward-paper the vwap book (free, recommended).** Build the M6 dashboard in shadow mode
   for vwap_magnet on all 4 names (symbol-tiering would be post-hoc selection — forward data
   adjudicates NVDA-concentration instead). Pre-registered forward gate (≥4 weeks, ≥100 plans,
   live-vs-sim fill parity). Real OOS at zero cost; revisit Stage A with it.
B. **Buy fill-truth (paid).** The edge is 100% execution; the binding uncertainty is maker-fill
   realism. Databento (~$179–199/mo) MBP-10 enables a queue-position fill model — the single
   highest-leverage data spend for THIS finding. Needs approval.
C. **Widen the search (free, weeks).** New registered payers / more tick symbols. Diminishing
   prior after this cycle's kills.
D. **Stop here.** Bank the machinery, protocol, and honest record.

Recommendation: A now; B if forward paper confirms the sim.
