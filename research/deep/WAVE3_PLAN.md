# Deep-Research Wave 3 — Plan (2026-07-18)

Orchestrator: Claude Code session (synthesis stays here). Protocol: `HARNESS.md` v1.0 Mode A.
Each agent gets `AGENT_BRIEF.md` **verbatim** + its lane's charge block + ONE modality focus
block. Collect raw outputs as `research/deep/DR-<lane-slug>/modality-<X>.md`; refuters run on
return, orchestrated here.

## Wave goal (what each lane unblocks)

| Lane | Area | Unblocks |
|------|------|----------|
| 1 | DR-X3 retail execution quality | The Phase-0 "smallness audit" prior + the M16 intraday-book cost model — the user's core thesis (tiny size ⇒ better effective costs) made measurable |
| 2 | DR-X4 dynamic trading w/ costs + known intraday effects | The M16 design (inventory book, no-trade bands, turnover budget) + a map of already-harvested intraday patterns so features start where the field ends |
| 3 | DR-X5 liquidity-down auction mechanics | The liquidity-down champion probe: pilot universe spec + expected deviation/spread priors by tier |
| 4 | DR-X6 holdings-archive reachability (light) | M12 Cell B (PassiveForce) AND the A2 index-LETF leg — the one remaining build gap in the mechanism horse race |

Priority if fewer agents: **1 > 2 > 3 > 4** (lane 4 is mechanical but cheap — run it if possible).

---

# LANE 1 — DR-X3-retail-execution-quality

## Your charge

Area: DR-X3 — What effective spread does small retail flow ACTUALLY pay? (new; feeds M16 Phase 0)

Question(s):
1. **Rule 605 ground truth:** From wholesaler/market-center Rule 605 reports (Citadel Securities,
   Virtu, G1/Susquehanna, Jane Street, Two Sigma Securities; 2023-2026, INCLUDING the post-2024
   Rule 605 modernization with odd-lot buckets): what is the effective/quoted spread ratio (E/Q)
   and average price improvement for MARKETABLE orders in the smallest size buckets (odd-lot,
   100-499 shares) on liquid Nasdaq-listed names? Numbers with sample periods and bucket
   definitions, not vibes.
2. **Broker layer:** What is known at T1 about Alpaca's execution quality (their 606 filings:
   which wholesalers, PFOF received, any published price-improvement stats) and IBKR
   (Lite vs Pro SmartRouting effective-spread claims)? Which retail broker measurably delivers
   the best marketable-order improvement for our profile?
3. **Time-of-day:** Does price improvement survive the 15:45-16:00 window (wider spreads,
   one-sided flow)? Academic evidence using retail-print identification (the
   Boehmer-Jones-Zhang-Zhang subpenny method and successors) on improvement BY TIME OF DAY;
   any evidence specific to the final minutes.
4. **Mechanics that matter for the measurement design:** market vs marketable-limit treatment
   by wholesalers; midpoint fill frequency; how improvement scales with quoted spread (fixed
   cents vs % of spread); minimum sizes where internalization behavior changes.

Already known (do not re-derive): Our sims charge FULL half-spread + 0.5-1 bp slip
(conservative); our historical sim entry-shortfall median is 1.46 bps ≈ 2x the quoted
half-spread median 0.73 bps on the 5 megacap names at 15:55:10. Alpaca is the live broker
(zero commission through 2026-12-31). The decision this feeds: a live micro-order audit
(Phase 0) then re-pricing a minutes-hours inventory book (M16) with MEASURED costs.

Depth: ≥8 distinct searches, ≥6 sources fetched AND read. Deliver: brief §9 schema; the
economics sketch MUST end with a predicted E/Q ratio distribution (or explicit UNKNOWN) for
$400-$3,000 marketable clips on liquid Nasdaq names, overall and in the last 15 minutes.

## Modality focus blocks

**A (academic):** BJZZ/subpenny retail-identification literature 2021-2026; price-improvement
measurement papers; critiques (does subpenny identify retail cleanly post-tick-pilot?);
time-of-day execution-cost studies. Sample periods + units mandatory.
**B (primary/venue):** Actual Rule 605 files (post-2024 format) from the major wholesalers —
locate, read, extract the small-bucket E/Q numbers; Alpaca 606/disclosures; IBKR execution
stats pages; SEC 605 modernization adopting release (what changed in the metrics).
**C (practitioner/vendor):** broker-comparison studies with methodology (e.g., published
execution-quality shootouts), wholesaler commentary, anything from retail-execution analytics
vendors (tag conflicts).
**D (adversarial):** the case that measured improvement overstates OUR reality: improvement
concentrated in wide-spread/small-cap names; adverse selection of the moment (improvement
shrinks exactly when you need liquidity, e.g., 15:55); marketable-limit orders treated worse
than pure market; PFOF brokers' improvement stats gamed via benchmark choice. Also: any
evidence retail improvement DETERIORATED 2024-2026.

---

# LANE 2 — DR-X4-dynamic-trading-and-intraday-map

## Your charge

Area: DR-X4 — Turnover-controlled dynamic trading + the map of known intraday effects
(new; feeds the M16 design)

Question(s):
1. **The cost-aware trading framework:** Garleanu-Pedersen "Dynamic Trading with Predictable
   Returns and Transaction Costs" and its practical descendants: the aim-portfolio /
   partial-adjustment rule, no-trade bands (width vs cost, vol, signal half-life), discrete
   implementations at hourly cadence. Extract the actual FORMULAS with parameter definitions,
   not just citations.
2. **What intraday structure is already documented (and how dead is it):** first-half-hour →
   last-half-hour predictability (Gao-Han-Li-Zhou intraday momentum) and its post-publication
   OOS record; time-of-day seasonality of returns/volume/spreads; overnight-vs-intraday return
   decomposition (Lou-Polk-Skouras line); late-day flow-driven drift (we already hold Barbon
   et al. on LETF last-30-min concentration — extend: anything on PRE-positioning ahead of
   known EOD flows). For EACH effect: sample period, size in bps, cost treatment, and
   post-publication decay status (or DECAY-UNKNOWN).
3. **Signal mixing under a turnover budget:** standard practice for combining a slow
   flow-anticipation signal with faster mean-reversion/momentum signals in one target
   position; forecast-to-position mapping at small cross-section (n≈5-33 names); risk
   normalization at hourly horizon.
4. **Prior art on retail/small-scale stat-arb at minutes-hours cadence** with honest cost
   accounting — does ANY credible documented example exist (T2/T3)? If none: say so, that is
   a finding.

Already known (do not re-derive): our own kills — bar-tier ML forecast→plan economics dead
(engineV5 + A1, rank-IC +0.03-0.05 REAL, plan-expression alpha ≈ 0); sequence models dead
(M4/M9); trailing-PnL regime gating dead (3x). The NEW elements motivating M16: deltas-only
inventory expression (never tested here) + flow features (LETF F(t) accumulates intraday;
calendar states) + possibly better-than-assumed retail costs (Lane 1). Mission: RTH-only,
flat by 15:50 (or at the close via MOC), manual keying (~10-30 small orders/day feasible).

Depth: ≥8 searches, ≥6 sources read. Deliver: brief §9 + a design cheat-sheet section
(formulas + recommended starting parameters for an hourly 5-33 name book) + the known-effects
table with decay verdicts.

## Modality focus blocks

**A (academic):** the GP framework + no-trade-band theory + the intraday-effects canon;
insist on post-publication OOS evidence for each effect.
**B (primary/venue):** exchange/TOD microstructure facts that bound the design: spread/depth
by time of day on Nasdaq megacaps (exchange or vendor research), auction-adjacent constraints
(15:50 freeze interactions), any short-sale mechanics relevant to intraday shorts (locate
practice at retail brokers, T1).
**C (practitioner):** how practitioners actually implement cost-aware target-position books
(quant blogs of substance, fund letters, engineering posts); realistic turnover numbers;
signal half-life measurement practice.
**D (adversarial):** why hourly stat-arb on a 5-33 name book should fail: breadth math
(IC×√breadth at n=5), crowding of every documented intraday effect, the "netting saves you
less than you think" case (signals correlated → deltas don't cancel), manual-execution slippage
at 10-30 orders/day, and the strongest published FAILURES of small-scale intraday systems.

---

# LANE 3 — DR-X5-liquidity-down-auction

## Your charge

Area: DR-X5 — Closing-auction mechanics and inefficiency scale DOWN the liquidity curve
(feeds the liquidity-down champion probe; the "smallness is the edge" thesis in its strongest form)

Question(s):
1. **Mechanics parity:** Do mid/small-cap Nasdaq names get the IDENTICAL closing-cross/NOII
   treatment (same 15:50/15:55 schedule, near/far fields, LOC 15:58)? Where does it degrade:
   near/far zero-rates for low-activity names, LULD interactions near the close, minimum
   cross activity, fee differences? T1 only for mechanics.
2. **Inefficiency scale, fresh:** beyond B&M's 2010-2018 small-cap |auction−mid| ≈ 20.6 bps —
   any 2020-2026 evidence (academic, BMLL/exchange research) on closing-auction dislocations
   by market-cap/ADV tier? How does dislocation-per-unit-spread trend with liquidity (the
   quantity that decides if the trade nets out)?
3. **Universe construction without survivorship:** free point-in-time membership sources for
   liquid mid/small caps (S&P 400/600 membership histories, IJH/IJR/MDY daily holdings
   archives, Russell lists); a defensible screen recipe (ADV band, price floor, primary
   listing) for a ~20-name pilot.
4. **Retail execution reality in the tier:** typical quoted spreads at 15:55 by ADV tier
   ($20M/$50M/$200M), odd-lot NBBO caveats, MOC/LOC acceptance and cross reliability for
   less-active names, share-price distributions (whole-share friendliness at $10k).

Already known (do not re-derive): the champion structure and its Nasdaq mechanics (wave-1/2:
cutoffs, NOII cadence, near/far zero-until-15:55); NOII history cost ≈ $0.45/name-year;
capacity is irrelevant at our size (that IS the thesis); B&M large-cap 2.66 bps vs small-cap
20.6 bps (2010-18). The decision this feeds: a registered ~20-name liquidity-down probe
(~$15 NOII) — the universe spec and priors come from this lane.

Depth: ≥8 searches, ≥6 sources read. Deliver: brief §9 + a recommended pilot-universe recipe
+ a per-tier prior table (expected |deviation|, spread, cross size).

## Modality focus blocks

**A (academic):** liquidity-tier cross-sections of auction quality/dislocation, 2019-2026
preferred; small-cap auction papers; anything on cross participation by tier.
**B (primary/venue):** Nasdaq rules/FAQs for cross eligibility and fees by tier; LULD near
the close; NOII field behavior for thin names (T1); S&P/Russell membership data availability
(free paths).
**C (practitioner):** market-maker/prop commentary on small-cap closes (who provides there,
what they say about the tail), transition-manager or index-fund notes on small-cap MOC
execution pain (their pain = our prior).
**D (adversarial):** why liquidity-down fails for us: wider spreads eat the bigger deviation
(net-per-unit-spread flat or worse), toxic closes in small caps (adverse selection at the
print — informed flow), data quality (NOII sparse/unreliable), borrow/locate friction on the
short side, and the possibility that the 20.6 bps figure is mostly untradeable microcaps —
find where the tradeable frontier actually sits.

---

# LANE 4 — DR-X6-holdings-archive-scout (light; modality B only, ≥5 searches)

## Your charge

Area: DR-X6 — Point-in-time index-weight archive reachability (feeds M12 Cell B PassiveForce
AND the A2 index-LETF leg)

Question(s): For 2020-2026, name the concrete retrievable-history paths for daily-or-monthly
fund holdings usable as index-weight proxies: (1) Wayback Machine coverage DENSITY for the
exact SSGA SPY daily-holdings XLSX URL and predecessors (how many distinct dates actually
archived per year?); (2) same for Invesco QQQ holdings download URLs (find the actual
file/endpoint pattern first); (3) iShares IVV/IJH/IJR `asOfDate` CSV behavior in a real
browser session (documented by others; is month-end history truly reachable back to ~2010?);
(4) N-PORT-derived weights as the fallback (QQQ trust files? Invesco QQQ Trust is a UIT —
which SEC form carries its holdings?); (5) any OTHER free PIT weight source we missed
(Nasdaq index factsheets archives, ETF.com snapshots in Wayback). Deliver: a per-source
table (URL pattern, archived-date density by year, effort) + a recommended assembly recipe
for quarterly-or-better NDX/SPX weights 2020-2026 at $0.

Already known: SPY XLSX live-verified but snapshot-only; iShares ajax bot-gated for
automation (T4 tooling claims history works); SEC 13F/N-PORT bulk confirmed free
(quarterly-public granularity); sec.gov blocks UAs containing "naver".

---

# On-return protocol (orchestrator = this session)

File raw outputs under `research/deep/DR-X3-…/DR-X4-…/DR-X5-…/DR-X6-…`; I extract ≤8
load-bearing claims per lane → refuter wave (2 per bundle, cheap models); local E-probes
(e.g., our own 605-style measurement design; universe screen dry-run on owned bars1d);
reports + map/OPEN_QUESTIONS updates; registration sketches to you (Phase 0 audit spec,
M16 design, liquidity-down probe). No ledger writes by agents.

## Success criteria

- Lane 1 → a numeric E/Q prior (or honest UNKNOWN) for our exact order profile + the Phase-0
  measurement design validated against how 605 defines improvement.
- Lane 2 → formulas + starting parameters for M16 and a decay-graded map of known intraday
  effects (so we neither rediscover nor re-fund dead anomalies).
- Lane 3 → a pilot universe recipe + tier priors that make the liquidity-down registration
  concrete.
- Lane 4 → a working $0 recipe for PIT weights (Cell B/A2 unblocked) or a clear verdict that
  a small paid source is required (name + $).
