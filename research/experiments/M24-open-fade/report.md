# M24 — opening-auction dislocation fade (`open_auction_fade_v1`) — REPORT

Registered 2026-07-23 pre-data (M3_REGISTRATION.md § M24). Single registered look executed
2026-07-23, window 2020-01-02..2026-05-31, harness commit 4717ae2. Look SPENT. This spent
the exhaustion map's ONE sanctioned remaining opening-cross look (Q10).

## VERDICT: BETWEEN THE BARS (both cells) — family CLOSED, look SPENT, no Stage-2

| cell | n | sessions | mean net bps | 95% CI (day-clustered) | class |
|---|---|---|---|---|---|
| t25 (|basis|≥25) | 1,392 | 642 | +3.16 | [−14.19, +20.81] | BETWEEN (weak) |
| t50 (|basis|≥50) | 324 | 182 | **+37.06** | [−4.63, +82.61] | BETWEEN (near-miss) |

Adequate registered power in both cells (floors met), so neither UNDERPOWERED nor a clean
kill: both point-positive with CIs spanning zero → report-only, no iteration, no threshold
motion, kill/park final at family level. ADIA panel (t25 daily stream, $10k/event): native
SR 0.014/day, PSR[0]=0.632, MinTRL ≈ 15,323 sessions — the pooled t25 stream carries no
detectable edge; whatever exists lives in the t50 tail.

## The two facts that outlive the family

1. **Orthogonality confirmed:** realized daily-P&L ρ̂ vs the champion dev stream = **−0.073**
   (n_overlap = 609, adequately powered). The opening auction is a genuinely independent
   axis — the first measured near-zero-ρ stream in the program. Any future open-auction
   family inherits this breadth property.
2. **Reported-not-gated structure (post-hoc; maximally suspect by construction):**
   - Gap-agreement 2×2: fade profits when the auction dislocation POINTS WITH the overnight
     gap (open overshoots the gap: +18.0 n=462 / +27.9 n=483) and loses hard when it opposes
     it (−41.1 n=238 / −36.5 n=209).
   - Liquidity gradient: broad-28 +15.35 [−4.91, …] vs champion-5 −19.63 — the mirror of the
     close family; consistent with the attention/liquidity mechanism (megacap opens
     equilibrate; less-liquid opens dislocate and revert).
   - Years choppy (2022, 2024 negative) — no clean era story.
   These are 3+ conditioning choices observed AFTER the look. Under the adopted ADIA
   standard they are hypothesis-generating only; any future registration citing them must
   charge the implied search (≥ 4-cell 2×2 × threshold × universe) at honest counts and be
   FORWARD-JUDGED (M20F pattern). Nothing here authorizes iteration inside this family.

## Fences held

- corr(basis_open, overnight gap) = **0.138** — the conditioning object is the
  auction-internal dislocation, not a gap proxy (gap_mr fence holds).
- M6b fence: no norm_imb, no timed exits anywhere in the harness (reviewer-verified).
- Funnel reconciles exactly: 34,986 candidates = 216 no_near_ref + 19,222 zero_basis +
  14,156 below_t25 + 1,392 fired (+0 no_msgs/no_bar); 33/33 names covered. Notable data
  fact: 55% of name-days have basis exactly 0 at 09:28:30 — most liquid opens clear at the
  reference price; the signal is sparse by nature.

## Ground-truthing (v6.1)

10 stratified events hand-verified: side = AGAINST basis in 10/10; net arithmetic exact to
4 decimals on independent recompute (row-0 hand check +366.5815); prints = official raw
open/close; extractions plausible incl. the 2025-04 tariff-crash tails that dominate the
extremes (AMD 2025-04-09 short −2,224 bps; PLTR 2025-04-07 long +1,679) — the tail variance
is real and is exactly why the CIs are wide.

## Process

orchestrator-architected (first family under the amended rule) → coder → adversarial reviewer
(APPROVE-WITH-FIXES: n-floor test vacuity, writer smoke, fee-symbol source; coder had
independently caught a polars Int8 overflow in tod arithmetic) → orchestrator audit → one
look → this verdict. 15 tests; suite 704 green at look commit.
