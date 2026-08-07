# Wave 4 synthesis — DR-X7 + DR-X8 (2026-07-20)

Run in-session: 8 Opus research agents (2 lanes × modalities A/B/C/D per HARNESS Mode A) +
2 refuter agents on the load-bearing DR-X7 keystones. Raw outputs:
`DR-X7-letf-intraday-rehedge/modality-{A..D}.md`, `DR-X8-small-size-cost-floor/modality-{A..D}.md`.
Refuter evidence trails in session scratchpad (k1/k2/k3 extracts, EDGAR FTS JSON).

## DR-X7 — LETF re-hedge timing & intraday reversion → **KILLED PRE-REGISTRATION**

M19 ("intraday dislocation reversion conditional on high-F LETF re-hedge states") is never
registered. $0 spent, no trial family charged. 4/4 modalities converged
(EXHAUSTED-BY-FIELD ×2, NOT-VIABLE-STRUCTURAL ×2); both refuters returned HOLDS /
HOLDS-WITH-CAVEAT on every keystone.

The kill, by independent legs:
1. **Primary documents (refuter-STRENGTHENED):** the close-of-day rebalance template is
   industry-standard — EDGAR FTS: 415 filings across exactly 5 fund families. The only
   disclosed intraday component is Direxion's discretionary, unquantified
   volatility-triggered escape (153 filings, one issuer, no threshold, no window).
   GraniteShares (NVDL/AMDL — our NVDA/AMD complexes) discloses **no intraday mechanism at
   all**: "orders to the swap provider(s) for execution at close." Leverage Shares/Themes and
   T-Rex use the same close-only template; "typically" is liability boilerplate.
   "intraday rebalance" as a literal phrase: **0 hits on all of EDGAR**.
2. **Academic (refuter-verified verbatim, and stronger than quoted):** Barbon-Beckmeyer-
   Buraschi-Moerke slid the hedge window across 10:00–16:00 — "virtually no impact of
   rebalancing for any hedging window different from the last one." LETF impact ≈2/3
   permanent; the reverting third lands at the **next open**, largely via the options-gamma
   channel. Caveat carried: index-era sample (2012–2019), single-stock extrapolation.
3. **Payer exoneration (HOLDS-WITH-CAVEAT — the one soft spot):** Baltussen-Da-Soebhag's
   single-name EOD reversal is attributed to retail attention + short-covering, "cannot be
   explained by liquidity- or gamma-hedging" — but their LETF control is index-level and the
   sample ends 2019, **structurally blind to the single-stock-LETF era**. The kill does not
   rest on this leg alone; it rests on legs 1–2 (timing), which are doubly sourced.
4. **Practitioner consensus:** ~100% close-window (Abdelmessih/Nomura/Tier1Alpha/Chan);
   intraday the flow is negative-gamma **momentum**; documented reversal is overnight
   (out-of-mission). No vendor sells an intraday single-stock LETF-reversion metric.
5. **Internal:** M18's NVDA/MU embers ≈ the expected 3–4 spurious ~2σ pockets from ~160
   inherited trials. Motivation, never evidence.

**Residues (the value extracted from the kill):**
- **M12 mechanism strengthened:** Barbon et al.'s flow proxy (leverage-adjusted AUM ×
  since-prior-close return, ranked 15:30) is exactly M12's F; the r-window is
  disclosure-pinned to since-prior-close; the flow prints INTO the cross the champion trades
  (Cheng-Madhavan 2009 snapshot: 16.8%/50.2% of MOC volume on 1%/5% days — cite as
  crisis-era, index-product, order-of-magnitude only).
- **F_t-as-champion-feature:** candidate a-priori thresholds folded into
  `research/experiments/M8-v2-FEATURE-DRAFT.md` (wave-4 note). No new family.
- **Optional $0 diagnostic (LOW priority, non-trading):** descriptive regression of intraday
  signed OFI on live F_t (owned 1s bars) to bound any pre-15:45 footprint. A-priori
  expectation: null. Only a material pre-15:45 reverting footprint would reopen anything.
- Corrections recorded: modality-D.md C1 sample-tag error (1993–2019 belongs to the
  EOD-reversal paper, not JFE-2021); T-Rex TSLA/NVDA ticker-level base text unread (gap, not
  refutation).

## DR-X8 — true cost floor at our size → maker economics **CLOSED**, cost model **CORRECTED**

Verdicts: maker-REBATE capture **NOT-VIABLE-STRUCTURAL (HIGH)** — sell-side regulatory fees
alone (~$0.0037/sh at $170) exceed the entire Nasdaq base add-rebate ($0.0013); Alpaca
retains rebates (PFOF model); IBKR-tiered commission ($0.0035/sh) exceeds every rebate
reachable below ~1.5% of consolidated volume. Maker-entry-on-signal (spread saving)
**EXHAUSTED-BY-US** — distinct-in-kind from dead M3 spread-capture (honest concession:
M18 had a signal, M3 didn't) but empirically landed negative on every stream (M18 receipt),
and the fill correction only deepens it.

**The two-sided correction that reconciles the lane:**
- Fees were OVER-charged: registered $0.005/sh/side ≈ 2.4× the true Alpaca floor
  (~$0.58 vs $1.41 per 141-sh round-trip). On fees alone the M18 NVDA ember re-prices from
  −$0.94 to ≈ break-even.
- Fills were OVER-credited by more: touch=fill is the canonical phantom-fill fallacy —
  favorable-subset ("kiss-and-bounce") fills run ~2–15% in the literature vs ~100% in our
  sim; retail limit fills average ~16 min, not 60 s; each realized fill carries −0.5..−1 bp
  adverse markout ≈ the entire M18 gross. **M18 ember reclassified: most-likely-phantom**
  (the M3 scar in a 60-second-touch disguise). Explicit UNKNOWN: no source measures a
  small-tick megacap at 1s/60s granularity — priors are cross-instrument extrapolations.
- **Adopted:** `research/COST_MODEL.md` v1 (Alpaca floor; slip separate; never credit maker
  rebates or maker half-spread; gross ≥ 2× floor before slip-recapture).
- **The one door left ajar:** M16 Phase-0 gains a pre-thresholded **resting-limit arm**
  (PROTOCOL-DRAFT amended): fill ≥ ~80% AND markout ≥ −0.2 bp reopens fee-boundary work on
  Alpaca; fill ≤ ~65% OR markout ≤ −0.5 bp closes maker-first intraday permanently.
- **Regulatory facts (T1):** PDT abolished eff 2026-06-04 (SR-FINRA-2025-017); at $1k the
  binding constraints are cash-account T+1 recycling (~1 round-trip/day/tranche) and odd-lot
  mechanics (unprotected, sub-round-lot clips); §475(f) MTM election neutralizes wash-sale
  bookkeeping for any future high-count ledger.

## Bookkeeping

EXHAUSTION_MAP: 3 new rows (continuous-market regime). OPEN_QUESTIONS: wave-4 block.
Ledger: notes `DR-X7-verdict`, `DR-X8-verdict`. Amended: M16-phase0 PROTOCOL-DRAFT,
M8-v2-FEATURE-DRAFT. Created: COST_MODEL.md. Wave-3 lanes remain out with the user and are
untouched by this wave.
