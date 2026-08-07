# Deep-Research Wave 2 — Plan (2026-07-17)

Orchestrator: Claude Code session (synthesis stays here — agents only research).
Protocol: `research/deep/HARNESS.md` v1.0, Mode A. Agents receive `AGENT_BRIEF.md` **verbatim**
at the top of their prompt, then their lane's charge block, then their one modality focus block.
Never summarize the brief. Agents share no other context.

## Wave goal (decision linkage — why these four lanes)

M11 falsified the broad-Nasdaq thesis AND the high-vol mechanism. The surviving edge is
name-specific (NVDA strongest, TSLA partial) with **no known mechanism**. This wave attacks the
two candidate mechanisms that remain, plus the one cheap universe expansion, plus one data
convenience:

| Lane | Area | Decides |
|------|------|---------|
| 1 | DR-Q1-3 payer decomposition + passive-ownership scaling | Whether index/passive concentration is the name-specificity mechanism → registers the M12 index-weight conditioning test (or kills name-focus) |
| 2 | DR-X1 LETF/single-stock-LETF close flow | The competing name-specific mechanism: single-stock LETF rebal AUM (NVDA's complex is plausibly the largest) → registers the LETF-flow conditioning test |
| 3 | DR-Q7 NYSE closing auction | Whether the mechanism ports to a second venue (≈2x universe) and what the data costs |
| 4 | DR-X2 earnings-calendar source scout | Unblocks the Q13 earnings-day diagnostic (source only, light lane) |

Priority if you run fewer agents: **Lane 1 > Lane 2 > Lane 3 > Lane 4.**
Lanes 1 and 2 are complementary answers to the same question ("why NVDA and not LRCX/AVGO/NFLX").

## Run instructions (external deep-research agents)

1. One agent per modality per lane (A academic, B primary/venue, C practitioner, D adversarial).
   Lane 4 runs B only. Total: 3×4 + 1 = 13 agents.
2. Each agent's prompt = `AGENT_BRIEF.md` (verbatim, full text) + the lane's `## Your charge`
   block + that agent's single `Modality focus` block. Nothing else.
3. Collect each agent's markdown output unmodified as
   `research/deep/DR-<lane-slug>/modality-<A|B|C|D>.md`.
4. Do NOT let any agent write verdict syntheses, ledger entries, or map updates — recommendations
   only (the brief already says this; enforce it if the product wants to "conclude").
5. Bring the raw files back; the orchestrator (this session) runs claim extraction, the refuter
   wave, synthesis, report.md, map + OPEN_QUESTIONS updates, and registration sketches.

Refuter wave (AFTER modality results return; ≤16 calls/lane): for each load-bearing claim the
orchestrator extracts (≤8/lane), 2 independent agents get `AGENT_BRIEF.md` + this template:

> Attempt to REFUTE via primary sources: "<claim + citation>". Default refuted=true if you
> cannot locate a primary (T1/T2) source. Return: refuted true/false + reason + the source you
> located (URL, date, tier).

---

# LANE 1 — DR-Q1-3-payer-mechanism

## Your charge

Area: DR-Q1-3 — Closing-cross payer decomposition & passive-ownership scaling
(OPEN_QUESTIONS.md #1, #2, #3-residual)

Question(s):
1. **Who pays at the Nasdaq close, decomposed?** Classes of closing-cross participants on
   megacap Nasdaq names — index-tracker MOC, mutual-fund NAV-driven flow, ETF create/redeem
   netting, pension/target-date rebalancers, buyback programs benchmarked to the close,
   option delta-hedgers, retail on-close, close-benchmarked institutional algos. For each:
   evidence of size, and whether it is **price-insensitive** (submits regardless of the
   indicative near price). Which class plausibly pays the near-vs-mid basis we harvest?
2. **Does forced close flow scale with index membership / passive ownership per name?**
   Cross-sectional and time-series evidence (2015→2026) that auction volume, imbalance size, or
   close-price deviation scales with index weight or % passively-held shares. We need a
   pre-registrable cross-sectional prediction of the form: basis-persistence ∝ f(index weight,
   passive share, auction share of ADV).
3. **Data sourcing (the actionable blocker):** free or ≤$100 one-time sources for
   point-in-time (a) NDX-100 membership + weights 2020-2026, (b) SPX membership + weights
   2020-2026, (c) per-name passive-ownership % (or a defensible proxy: e.g. summed daily
   holdings files of the major index ETFs — iShares/Vanguard/SSGA publish daily holdings;
   is a 2020-2026 archive reachable, e.g. via Wayback Machine?), for our 33 Nasdaq names.
   Quarterly granularity is acceptable; name exact products, access paths, and $.
4. **Q3 residual sliver only:** the NOII dissemination cadence between 15:55:00 and 16:00:00
   (update frequency, any final-minute acceleration) at T1, and any literature on late-window
   (15:55→16:00) indicative-price convergence / price discovery in the Nasdaq closing cross.

Already known (do not re-derive):
- Champion + holdout numbers: see brief §3. M11 (2026-07-17, our ledger): the frozen rule on
  28 never-fit Nasdaq names = net −3.0 bps, directional 0.470, negative in ALL 6 sectors.
  Vol-tercile test within the 28: HIGH-vol tercile is the WORST; LRCX/AVGO/NFLX (~130% ann
  vol, same class as NVDA/TSLA) are all dead (dir 0.45-0.49). NVDA is positive in all three
  views (backtest +4.3, holdout +12.2, broad dir 0.614); TSLA 2-of-3; GOOGL dead everywhere.
  So the mechanism you research must explain NAME selectivity, not volatility.
- Wave-1 (DR-Q4-6/Q8/Q12 reports, refuter-confirmed): payer narrative = indexed MOC flow at
  the listing-venue close. ETF-shell basis is collapsed by AP/iNAV arb; forced flow concentrates
  in CONSTITUENTS (Arca ETF auction share ~2% ADV vs ~9% for equities, BMLL 2025). Exchange and
  broker on-close cutoffs are fully mapped (Nasdaq freeze 15:50 / MOC 15:55 / LOC 15:58; Alpaca
  CLS 15:50; Schwab 15:45; Fidelity 15:40) — do NOT re-research cutoffs.
- We already OWN per-event realized cross price/size and NOII imbalance fields (norm_imb,
  paired_ratio, near/far/ref) 2020-2026 for 5 names + 2023-2026 for 28 more. Realized auction
  volume per name is NOT a data gap. The gaps are index weights and passive-ownership series.
- S&P/NDX rebal calendars and Russell recon dates are mapped (wave-1); do not re-derive.

Depth: ≥8 distinct searches, ≥6 sources fetched AND read; stop early only per brief §10.
Deliver: brief §9 schema. Your verdict is a RECOMMENDATION; synthesis happens upstream.

## Modality focus blocks (append exactly ONE to each agent's prompt)

**Modality A (academic):** SSRN/arXiv q-fin/journals on closing-auction participation,
imbalance predictability, passive ownership and close-price formation. Anchors to chase
forward and backward: Bogousslavsky & Muravyev "Who Trades at the Close"; Cushing & Madhavan;
recent (2020-2026) closing-auction price-discovery and index-inclusion-flow papers; anything
quantifying MOC flow as % of close volume by index membership. Sample periods and cost
treatment mandatory; per-event vs per-day units explicit.

**Modality B (primary/venue):** owns mechanics + data-product claims. Nasdaq NOII dissemination
schedule 15:55→16:00 at T1 (nasdaqtrader.com specs/notices). Index-weight data products at T1:
Nasdaq's official NDX weighting data (what's free vs licensed), S&P availability, and the
ETF-holdings-file route (iShares/Vanguard/SSGA daily holdings: file formats, history retention,
Wayback coverage). SEC 13F bulk data as a passive-share proxy: exactly what's derivable, at
what granularity, free. Name exact products/URLs/$ for everything.

**Modality C (practitioner/vendor):** named practitioners/vendors on who pays the close and how
desks model MOC flow (index-fund dealing desks, transition managers, close-benchmark algos).
Vendor research on auction share growth (BMLL, Nasdaq economic research, big-broker
market-structure notes). Practical sources quants actually use for historical index weights and
passive-ownership estimates (tag conflicted vendor content).

**Modality D (adversarial/prior-art):** the strongest case that (a) passive/index flow does NOT
predict close-auction basis persistence (e.g. flow is netted/internalized upstream, or absorbed
by depth), (b) any weight/ownership-scaling effect is already arbitraged by close-auction
liquidity providers, and (c) our NVDA result is survivorship/selection (the tournament-winner
critique — we picked NVDA after seeing three views). Who has tried imbalance-following at the
close and failed? Decay evidence post-2020?

---

# LANE 2 — DR-X1-letf-close-flow

## Your charge

Area: DR-X1 — Leveraged-ETF & single-stock-LETF daily rebalance flow at the close (new cell;
adjacent to OPEN_QUESTIONS #1-#2)

Question(s):
1. **Universe:** enumerate US-listed leveraged/inverse ETFs referencing NDX-100, SOX/semis, and
   SPX, AND all single-stock leveraged/inverse ETFs on NVDA, TSLA, AMD, MU, GOOGL, AVGO, NFLX,
   LRCX (issuers incl. Direxion, ProShares, GraniteShares, REX/T-Rex, Tradr, Leverage Shares).
   For each: leverage factor, inception date, and current AUM.
2. **AUM history sourcing:** free or ≤$100 sources for daily-or-better AUM / shares-outstanding
   history 2022-2026 per fund (issuer daily files, SEC N-PORT/N-CEN cadence and lag, any
   aggregator with history). Name exact access paths. Quarterly-only granularity = degraded
   but usable; say so explicitly.
3. **Where does the re-hedge flow execute?** The mechanism question that decides everything:
   is the daily rebalance (fund or its swap counterparties) executed (a) as MOC in the closing
   auction — i.e. it appears in NOII imbalance and is partially IN our near price by 15:55 —
   (b) as continuous trading ~15:30-16:00, or (c) netted OTC and never reaching the market?
   T1 (prospectus/SAI execution language) and T3 (practitioner accounts) both wanted.
4. **Magnitude per name:** with flow ≈ (L²−L)·AUM·r_day summed over funds referencing the name
   (single-stock funds direct; index funds × the name's index weight), rank our names by
   predicted close-flow intensity 2024-2026. Is NVDA's single-stock complex genuinely the
   largest? Does the ranking match NVDA > TSLA ≫ AVGO/NFLX/LRCX (which would make this THE
   name-specificity mechanism candidate)?

Already known (do not re-derive):
- Our ledger KILLED the intraday continuous-market LETF-window detector (M3/M5 under honest
  fills) — this charge is ONLY about the close-auction expression and data sourcing. Do not
  propose intraday LETF trades.
- M11 name-specificity puzzle (see brief §3 + this: LRCX/AVGO/NFLX are as volatile as NVDA and
  dead; the mechanism must be name-selective). A LETF-AUM ranking that matches the alive/dead
  split is the bull case for this cell; one that doesn't match kills it cheaply.
- Known lit anchors: Cheng & Madhavan (2009) rebalance-flow model; Tuzun (Fed, 2013); the
  2010-2012 "LETF cascade" debate. We need the 2022-2026 single-stock-ETF era, not a rehash.
- We own NOII imbalance + realized cross size per event — if rebal flow is MOC, we can later
  test alignment on owned data at $0. Predicted flow needs only AUM history + daily returns
  (owned bars).

Depth: ≥8 distinct searches, ≥6 sources fetched AND read; stop early only per brief §10.
Deliver: brief §9 schema. Your verdict is a RECOMMENDATION; synthesis happens upstream.

## Modality focus blocks

**Modality A (academic):** LETF rebalancing impact literature 2009→2026, with priority on
anything covering (a) execution venue/timing of rebal flow, (b) single-stock ETFs 2022-2026
(price impact, close behavior of underlyings), (c) estimates of rebal flow as % of close
volume. Flag NO-COST-MODEL papers; per-event vs per-day units explicit.

**Modality B (primary/venue):** prospectus/SAI language on rebalance execution and timing for
the largest funds found (do they hold swaps? who hedges? any disclosure of MOC usage);
N-PORT/N-CEN what's in them, cadence, lag, bulk access; issuer daily holdings/AUM file
availability and history retention at T1.

**Modality C (practitioner/vendor):** desk/practitioner accounts of how LETF re-hedge flow
actually executes (swap dealer delta-hedge at the close print vs auction), single-stock-ETF
AUM trackers, ETF-analyst commentary on NVDL/TSLL-class funds' market footprint 2024-2026.

**Modality D (adversarial/prior-art):** the case that LETF close flow is (a) fully anticipated
and provided-against by close liquidity suppliers (crowded, in the near price with no residual
persistence), (b) small vs megacap close volume in 2024-2026, or (c) executed off-close so it
never touches NOII. Prior art: who has published/attempted LETF-rebalance front-running at the
close and what happened post-2012? If the flow is real but already impounded by 15:55:10, say
exactly that — it converts this cell from "new conditioning signal" to "explanation of the
champion's payer," which is still a verdict-relevant finding.

---

# LANE 3 — DR-Q7-nyse-close

## Your charge

Area: DR-Q7 — NYSE closing auction: does the mechanism port? (OPEN_QUESTIONS.md #7)

Question(s):
1. **Current (2026) NYSE closing-auction mechanics at T1:** order types (MOC/LOC/Closing
   Offset/D-Orders), entry + cancel cutoffs, the imbalance-data dissemination schedule (start
   time, update frequency, fields — reference price, paired quantity, imbalance quantity,
   indicative/book clearing prices), and floor-broker D-Order/e-Quote windows (how late can
   discretionary interest enter?). CRITICAL: NYSE amended closing-auction rules during
   2023-2026 — locate the current rule text and the SEC filings for any changes; distrust
   pre-2023 secondary sources.
2. **The decision-instant comparison:** given (1), at what clock time does a retail-visible
   indicative clearing price / imbalance first exist on NYSE, and how does the usable decision
   window compare to our Nasdaq 15:55:10 snapshot? Is the "earlier imbalance = more decision
   time" intuition true in 2026?
3. **Data:** the exact Databento product for NYSE auction imbalances (XNYS pillar — dataset id,
   schema name, fields, history start), whether it carries an indicative match/near-equivalent
   price, and the realistic one-time cost pattern for ~10-30 liquid NYSE names × 3-6 years
   (per-name-decade $ if quotable from public pricing docs; otherwise describe the quote path).
   Also: any FREE historical NYSE imbalance source.
4. **Evidence of exploitability:** academic/practitioner evidence of predictable
   imbalance-to-close price behavior on NYSE specifically (not pooled US), and the adversarial
   case that floor brokers with late discretionary D-Orders are structurally advantaged
   incumbents who arb exactly this basis.

Already known (do not re-derive):
- Champion mechanics + numbers: brief §3. Everything we validated is Nasdaq-listed; a NYSE test
  means a NEW universe of NYSE-listed liquid names — note universe suggestions but don't
  belabor them.
- Broker on-close cutoffs at Alpaca/Schwab/Fidelity were mapped in wave-1 for Nasdaq; whether
  broker cutoffs differ for NYSE-listed symbols is IN scope (one B-lane check), the Nasdaq ones
  are not.
- Databento is our vendor (API key, ~$30 credit remaining); historical Nasdaq NOII cost
  ~tens-of-$ per name-decade as a reference pattern. Gate 4 bar: ≤~$100 one-time.

Depth: ≥8 distinct searches, ≥6 sources fetched AND read; stop early only per brief §10.
Deliver: brief §9 schema. Your verdict is a RECOMMENDATION; synthesis happens upstream.

## Modality focus blocks

**Modality A (academic):** NYSE closing-auction studies — price discovery, imbalance
predictability, D-Order informativeness, close deviation/reversal magnitudes; 2019-2026
preferred, sample period + venue explicitly NYSE (not pooled). Compare effect sizes in bps to
our champion (+2.5 dev / +12.5 holdout per event).

**Modality B (primary/venue):** owns everything in questions 1-3 at T1: NYSE rules (Rule 7.35
series), SEC rule filings 2023-2026, NYSE XDP/Pillar imbalance feed specs, Databento XNYS
dataset/schema docs + public pricing. Also the one broker check: do Alpaca/IBKR handle
on-close order cutoffs differently for NYSE-listed symbols?

**Modality C (practitioner/vendor):** how institutions work the NYSE close (D-Orders via floor
brokers, closing-offset usage), practitioner commentary on NYSE vs Nasdaq auction quality,
vendor/broker products that surface NYSE imbalances to non-members (and their latency).

**Modality D (adversarial/prior-art):** the strongest structural case AGAINST porting: floor
broker discretionary access until seconds before 16:00 means the published imbalance is
systematically stale/adversely selected for outsiders; published NYSE imbalance fields may be
rounded/coarse; any evidence that imbalance-following on NYSE specifically has been arbed away
post-2018. If the 15:50-vs-15:55 advantage died with a rule change, prove it with the filing.

---

# LANE 4 — DR-X2-earnings-calendar (light, modality B only)

## Your charge

Area: DR-X2 — Historical earnings-date source for the Q13 earnings-day diagnostic (new cell,
data-scout only)

Question(s): identify the best FREE (or ≤$20) source for historical earnings announcement
dates WITH session timing (BMO/AMC/during-market) for 33 specific US megacap/large-cap names,
2020-2026, machine-readable. Candidates to evaluate (add your own): SEC EDGAR 8-K/press-release
acceptance timestamps (T1, free, bulk — assess DIY effort honestly), Nasdaq.com earnings
archives, yfinance `get_earnings_dates`, Alpha Vantage / FMP free tiers, Zacks. For the top 2:
exact access method, rate limits, history depth, timing-field reliability, and a concrete
validation plan (e.g. cross-check 20 random name-quarters against company IR pages). Deliver
the SOURCE recommendation + access recipe, not the dataset itself.

Already known (do not re-derive): the diagnostic it unblocks is a $0 calendar-flag test on
owned NOII (2020-2026, 33 names); wrong dates poison it, so timing-field accuracy matters more
than convenience. AMC vs BMO matters: an AMC announcement makes the SAME day's close the
pre-announcement close and the NEXT day's close the post-gap close — the source must let us
distinguish these.

Depth: ≥5 distinct searches, ≥3 candidate sources actually probed; stop early per brief §10.
Deliver: brief §9 schema (gates 1-3, 5-7 may be N-A; this is a data-scout lane).

---

# On-return synthesis protocol (orchestrator = this session; do not delegate)

1. File raw outputs under `research/deep/DR-<lane-slug>/modality-*.md` (create dirs then).
2. Extract ≤8 load-bearing claims per lane → refuter wave (2 agents/claim, template above).
   CONFIRMED requires a refuter-located T1/T2 source; otherwise PLAUSIBLE max.
3. Run local **modality E** probes before verdicts (repo access needed, so it happens here):
   - Lane 1/2: join-feasibility of a weight/AUM series against our 33-name × session panel;
     n of champion events per name; cross_size distributions (owned).
   - Lane 3: Databento XNYS quote via metadata API against the ≤$100 gate.
4. Write `report.md` per lane in brief §9 + `### Synthesis` header (lane table, dissents),
   verdict per HARNESS decision rules, unit table, "what would flip it."
5. Update `EXHAUSTION_MAP.md` rows (Q1-3, Q7 verdicts; X1/X2 new rows already seeded as
   UNMAPPED) and the OPEN_QUESTIONS priority section.
6. Hand the user: verdict + confidence + 3-5 driving claims + registration SKETCHES
   (M12 index-weight conditioning / LETF-flow conditioning / NYSE port / Q13 flags).
   NO ledger writes, NO registrations, NO holdout contact by anyone in this wave.

## Success criteria for the wave

- Lane 1 or 2 produces a named, pre-registrable, name-selective mechanism variable we can
  compute for 2020-2026 at ≤$100 — or a clean kill of the respective mechanism story.
- Lane 3 produces a PASS/FAIL on "portable + testable ≤$100" with the exact data product named.
- Lane 4 produces one validated source recipe.
- Every CONFIRMED claim refuter-verified; every number carries units (bps per WHAT).
