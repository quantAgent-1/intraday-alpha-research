# Deep-Research Wave 4 — Plan (2026-07-20)

Orchestrator: Claude Code session (synthesis stays here). Protocol: `HARNESS.md` v1.0 Mode A.
Each agent gets `AGENT_BRIEF.md` **verbatim** + its lane's charge block + ONE modality focus
block. Collect raw outputs as `research/deep/DR-<lane-slug>/modality-<X>.md`; refuters run on
return, orchestrated here. Complements wave 3 (DR-X3..X6, still outstanding) — do not re-run
those lanes.

## Wave goal (what each lane unblocks)

| Lane | Area | Unblocks |
|------|------|----------|
| 1 | DR-X7 LETF re-hedge timing & intraday reversion | The ONLY legitimate revival path for reversion: an ex-ante M19 registration "intraday dislocation reversion conditional on high-F LETF re-hedge states" — or a kill-before-build if the timing evidence says re-hedge flow is EOD-only |
| 2 | DR-X8 true cost floor for small maker-first intraday trading | Whether fee-boundary results (M18's NVDA/MU embers: positive mid-alpha, killed by $0.005/sh/side) can EVER be actionable at retail-accessible venue tiers; the cost model for all future intraday registrations |

Priority if fewer agents: **1 > 2**.

Context both lanes must respect (from the ledger, do not re-litigate): M12 Cell A PASSED
(single-stock LETF re-hedge flow F=(L²−L)·AUM(t)·r explains the champion's close-window
name-selectivity; +0.510 bps/sd with controls; MU predicted ex-ante by its AUM ramp;
index-weight NULL). LETF front-running as a STANDALONE family is DEAD (field). M18
reversion_system_v1 is DEAD (obituary 2026-07-20): unconditional and G1/G2-conditioned
intraday reversion has no positive-expectancy stream; its NVDA/MU embers (mid-alpha
+2.19/+2.15 $/trade, fee-killed) are MOTIVATION for lane 1's question, NOT evidence.
Doctrine: conditioning hypotheses may only be registered on triggers with demonstrated
conditional mid-alpha — lane 1 exists to establish (or kill) the mechanism prior ex-ante.

---

# LANE 1 — DR-X7-letf-intraday-rehedge

## Your charge

Area: DR-X7 — Does single-stock-LETF re-hedging create INTRADAY price pressure that
mean-reverts, in the names where complexes concentrate? (new; feeds M19 registration or its
pre-registration kill)

Question(s):
1. **Re-hedge timing distribution (the decisive question):** When do single-stock LETF
   issuers/swap counterparties actually adjust hedges — concentrated in the closing auction /
   last minutes (as index-LETF folklore says), distributed intraday (continuous delta
   management by the swap desk), or threshold-triggered on intraday moves? Primary evidence:
   prospectuses/SAI hedging language (Direxion, GraniteShares, T-Rex/REX, Leverage Shares),
   N-CEN/N-PORT swap disclosures, issuer methodology docs, measured intraday footprints.
   Deliver a % split (intraday vs close-window) or an explicit UNKNOWN.
2. **Impact and reversal:** Measured price impact of LETF rebalance flow at intraday horizons
   and evidence on whether it REVERTS (same day / next open): Cheng-Madhavan (2009), Tuzun
   (2014), and especially post-2022 single-stock-ETF literature. Magnitudes in bps per $ of
   flow with sample periods.
3. **PIT computability:** Can an intraday flow-state proxy F_t = (L²−L)·AUM(t)·r_t be computed
   point-in-time during the session (AUM from T-1 anchors, r_t live)? What r-window does the
   hedge desk actually respond to (since-prior-close vs rolling)? Any disclosure pinning this?
4. **Competition:** Who already trades intraday LETF-hedge anticipation (market-maker/prop
   commentary, front-running literature since 2023)? Is the intraday expression arbitraged
   while the close-window expression (our verified edge) persists — and why?

Already known (do not re-derive): M12 Cell A verdict + F formula + 454 AUM anchors on disk;
champion trades the 15:55 close window only; M18 obituary numbers above; our data lake has
1-second bars with OFI/microprice for NVDA/TSLA/AMD/MU and 1-minute LETF bars
(TQQQ/SQQQ/SOXL/SOXS). The decision this feeds: register M19 ex-ante ONLY IF a nonzero
intraday re-hedge share is supported AND an intraday F-state is PIT-computable; otherwise
record the kill and close the reversion question permanently.

Depth: ≥8 distinct searches, ≥6 sources fetched AND read. Deliver: brief §9 schema; MUST end
with (a) the timing-split verdict (or UNKNOWN), (b) a yes/no on PIT intraday F-state, (c) a
one-paragraph honest read on whether M19 deserves registration.

## Modality focus blocks

**A (academic):** LETF rebalancing impact/reversal literature 2009-2026; single-stock ETF
papers post-2022; intraday price-pressure-and-reversal methodology (how to attribute
reversion to a flow cause). Sample periods + units mandatory.
**B (primary/venue):** prospectuses/SAIs + N-CEN/N-PORT of the single-stock LETF complexes on
our names (who is the swap counterparty, what does the hedging language commit to);
issuer methodology/FAQ pages; exchange/venue notices on LETF-driven close imbalances.
**C (practitioner/vendor):** market-maker and ETF-desk commentary on WHEN single-stock LETF
hedge flow hits (SpotGamma-class analysts, desk notes, podcasts with named practitioners —
tag conflicts); any vendor products claiming to track it (what they publish implies what's
computable).
**D (adversarial):** the case AGAINST: intraday re-hedge share ≈ 0 (all EOD); the M18 ember
is pure multiple-testing residue; intraday LETF anticipation is a crowded HFT trade with
nothing left at 1-second/human latency; AUM anchors too stale for intraday F. Also: the case
that conditioning on F just re-discovers the close window we already trade.

---

# LANE 2 — DR-X8-small-size-cost-floor

## Your charge

Area: DR-X8 — The true all-in cost/rebate floor for OUR size and broker tier, maker-first
intraday. (new; feeds the cost model of every future intraday registration)

Question(s):
1. **Alpaca reality:** With zero commission through 2026-12-31, what does a resting limit
   order actually pay/earn all-in (SEC fee, FINRA TAF, any pass-throughs)? Where do Alpaca
   resting limits route; does Alpaca retain venue rebates; any published execution-quality
   stats for limit (not marketable) orders?
2. **IBKR Pro tiered:** At our clip sizes (~$400–$10k notional, 60-210 shares), what net
   maker rebate per share is realistically accessible on Nasdaq-listed megacaps? Include
   exchange fee schedules (Nasdaq/ARCA/BX inverted venues) at the lowest volume tier and
   IBKR's tiered commission stack — a defensible per-share table, not marketing claims.
3. **Touch-fill realism:** For small resting limits at the touch on NVDA-class names, what do
   literature + practitioner evidence say about queue position, expected fill rates, and the
   adverse-selection cost of touch fills (filled exactly when wrong)? How much of M18's
   90-98% touch-fill optimism survives?
4. **Small-account frictions:** PDT rules at the $1k small-account lens (4×/5-day limit — does it
   bind an intraday-trade-per-day sleeve?), wash-sale bookkeeping at thousands of
   trades/year, and any broker-level limits on order rate/cancels for retail.

Already known (do not re-derive): registered cost model $0.005/sh/side + 0.5 bps taker slip;
M18 ember arithmetic (NVDA system stream gross +$1.79/trade at 141 sh — net −$0.94 under the
registered fees; sign flips iff all-in cost < ~$1.27/side-equivalent); Alpaca is the live
broker; research basis $10k/plan, small-account lens $1k; engineV5's +2.21 bps passive-vs-cross
fact. The decision this feeds: the fee/rebate table any future M19+ registration must use,
and an explicit verdict on whether fee-boundary streams are actionable at ANY accessible tier.

Depth: ≥6 distinct searches, ≥5 sources fetched AND read. Deliver: brief §9 schema; MUST end
with the per-share cost/rebate table (Alpaca vs IBKR-Pro-tiered, at our clips, with dates of
the fee schedules used) + a fill-rate/adverse-selection prior for touch-resting limits + the
PDT verdict for the small-account lens.

## Modality focus blocks

**A (academic):** maker-taker economics, queue-position value, adverse selection of passive
fills (Battalio-Corwin-Jennings class and successors); retail limit-order execution studies.
**B (primary/venue):** current Nasdaq/NYSE-Arca/BX/EDGA fee schedules (lowest tiers, 2026
vintage); IBKR tiered pricing pages; Alpaca fee docs + 606/605 filings; SEC/FINRA fee rates;
PDT rule text.
**C (practitioner/vendor):** broker-comparison shootouts with methodology; small-prop/retail
practitioner accounts of resting-limit fill quality at touch on megacaps; order-rate limits.
**D (adversarial):** the case that maker economics NEVER work at our scale: rebate tiers
require volume we lack; touch fills are pure adverse selection at 1-second granularity;
IBKR's stack eats the rebate; and the M18 fill model (touch within 60 s on 1 s bars)
overstates realizable fills by 2-5×.
