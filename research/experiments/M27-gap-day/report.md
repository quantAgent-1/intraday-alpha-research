# M27 — gap-day reversion (`gap_day_reversion_v1`) — REPORT

Registered 2026-07-23 pre-download; data purchased $15.70 post-registration; single look
executed 2026-07-23 (seed 7, 2023-08-01..2026-05-31, harness commit df833b2). Look SPENT.

## VERDICT: FAMILY KILL — obituary

Both gated cells failed their bars at adequate registered power; per the registration the
kill is final. No threshold motion, no conditional resurrection.

| cell | n | sessions | mean net bps | 95% CI | names positive |
|---|---|---|---|---|---|
| t50 (|g|≥50) | 2,292 | 641 | **−8.71** | [−23.12, +5.69] | 1/5 |
| t100 (|g|≥100) | 1,481 | 514 | **−12.14** | [−30.76, +7.89] | 1/5 |

ADIA panel (t50 daily): SR −0.046, PSR 0.102, MinTRL n/a-negative. Floors (frozen before
any mean): pooled RT 16.0 bps — KLAC alone 38.5 bps; 09:35 entry spreads run far wider
than the day's median (ground truth shows 60–90 bps KLAC morning spreads).

## The durable lesson (what the family bought)

Implied mid-to-mid gross ≈ net + realized spread/slip ≈ **+7 to +11 bps** of genuine
gap-reversion mid-alpha on these names — fully consistent with M24's print-to-print
measurements (+15/+37 on costless auction legs). **The effect is real; the taker floor is
~2× the effect.** The only expression that harvested it was auction-print legs — the
execution class this program has retired. M18's corollary lands again from the other side:
execution cannot create edge, and here the edge exists but only inside an execution venue
we no longer use. Filters could shrink the loss; nothing in the registered space crosses
the floor.

Strata (report-only): up-gap fades much worse (−13.6) than down-gap (−2.97); 2024 was the
kill year (−28.5); AMAT the lone positive (+4.5). Data-quality note: one fired event is a
split artifact (LRCX 2024-10-03, 10:1 split read as −9,018 bps "gap" on raw bars) —
immaterial (Δmean ≈ +0.04 bps, verdict unchanged) but any future gap family MUST carry a
split guard on raw bars; recorded as a standing design note.

## Ground-truthing (v6.1)

10 stratified fills hand-verified: side logic 10/10; entry/exit fills exact to the
convention (bid·(1−slip) / ask·(1+slip)) on independent recompute; the extreme losers are
the April-2025 tariff-crash continuation days — real, not artifact; the split artifact
identified above via this very sample (the sampler doing its job).

## Coverage note

Tested: unconditional fade, 5 least-liquid broad names (exogenous rule), 09:35→15:45 taker
legs, 683 sessions. NOT tested (open, would need new registrations and in most cases new
data or banned venues): the 7 other broad names; megacap universe (M24 says opens are
efficient there); conditional subsets (post-hoc here); maker entries (phantom class);
auction-leg expressions (retired venue).

## Process

Registered → data purchased → orchestrator-designed → coder → adversarial review (outright
APPROVE, 10/10 attack surfaces clean) → one look → kill. Total family cost: $15.70 and
one session. The registered machinery priced a real hypothesis honestly in under a day.
