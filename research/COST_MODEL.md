# Research cost model — house standard v1 (2026-07-20)

Source: wave-4 DR-X8 (T1 fee schedules, dated; refuter-checked where load-bearing).
Applies to FUTURE intraday registrations (M19+); already-registered families keep the cost
model frozen in their registration. Full derivation:
`research/deep/DR-X8-small-size-cost-floor/modality-{A..D}.md` + `research/deep/WAVE4_SYNTHESIS.md`.

## Explicit fees (live broker = Alpaca, zero commission through 2026-12-31)

- Per side: $0 commission. Sell side adds SEC §31 **0.206 bps of notional** (FY2026 rate,
  eff 2026-04-04) + FINRA TAF **$0.000195/sh** (cap $9.79, eff 2026-01-01). CAT
  ≈ $0.000016/sh both sides (negligible).
- Round-trip explicit floor ≈ **0.206 bps of one-side notional + ~$0.03** (e.g. ~$0.58 at a
  141-sh/$187 clip). The old flat $0.005/sh/side proxy (≈ IBKR Fixed) runs ~2.4× this floor
  — do not reuse it for Alpaca-priced registrations.
- Post-promo stress annotation (per AGENT_BRIEF §1): re-add a commission scenario for 2027+.
- Do NOT price registrations on IBKR numbers (strictly worse at our size).

## Slippage / fills (modeled separately from fees)

- Marketable/taker legs: 0.5 bps slippage. Single-print auction legs (MOC/LOC at the cross):
  0 spread, 0 slip (fee per exchange schedule if routed to a venue charging one).
- **Maker rules (hard, until measured otherwise):**
  1. Never credit a venue maker rebate at retail tiers — structurally unreachable (sell-side
     reg fees alone exceed base rebates; Alpaca retains rebates; IBKR commission exceeds
     accessible rebates).
  2. Never credit a maker fill with the half-spread. Book ≈ 0 gross capture plus an
     adverse-selection charge. Literature priors: touch-fill 20–50% blended and only
     **2–15% on the favorable (profit-bearing) subset**; post-fill markout **−0.5..−1 bp**.
  3. "Bar low touched the limit" is NOT a fill (M3 scar; wave-4 confirmation). Realistic fill
     rules require trade-through-with-volume on condition-coded prints, or measured rates.
- The ONLY path to relaxing the maker rules: the M16 Phase-0 resting-limit arm's measured
  fill rate and markout (thresholds pre-registered in its PROTOCOL).

## Promotion arithmetic

Gross expectancy must be ≥ **2× the all-in floor** for the structure before any
slip-recapture or fill-improvement assumption may enter a registration.

## Small-account frictions (small-account lens $1k)

- PDT rule abolished eff 2026-06-04 (SR-FINRA-2025-017); never applied to cash accounts.
- Binding constraints instead: cash-account **T+1 settlement recycling** (~1 full-size
  round-trip/day per settled tranche; GFV risk beyond) and **odd-lot mechanics** (3–7 sh
  megacap clips are unprotected quotes; fee-boundary streams are only discussable at the
  $10k research clip).
- High-count ledgers (if ever): assume IRC §475(f) MTM election (kills wash-sale
  bookkeeping); election is calendar-gated — plan ahead.
