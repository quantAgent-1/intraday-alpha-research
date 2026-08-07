## DR-Q12 — D adversarial findings
### Verdict recommendation
**NOT-VIABLE-STRUCTURAL** (confidence **MED–HIGH**) — Rebal-day *amplification as a Stage-A / promotable edge* fails Gate 6 by design: major US rebal calendars yield ~8–20 event days/year; even 6 years of owned history × a few core names cannot reach n≥250 without pooling that dilutes the treatment. The residual hypothesis that rebal days *amplify the champion NOII-basis mean* in our mega-liquid Nasdaq universe is weakly supported: continuous→close rebal share-change impacts are ~0.15 bps per 2% share move (Dimensional 2019–2023), multi-day index effects have largely decayed (Greenwood–Sammon JF 2025), and ADV/auction-depth spikes can absorb MOC flow that would otherwise widen |basis|. A free diagnostic stratum of the champion is cheap but must be pre-flagged **UNDERPOWERED-BY-DESIGN** and must not charge a trial family for promotion.
What would flip it: Owned NOII shows |basis| and/or hit-rate on rebal/quad-witch/month-end sessions in our 5–28 names systematically ≥2× non-rebal with stable sign, *and* a pre-registered pooling scheme that still yields n≥250 *without* contaminating the calendar definition (e.g. add/delete-conditioned names only with multi-year multi-name panel).

### Mechanism
**Who would pay (in theory):** Index/ETF trackers forced to trade at the effective-date close for tracking-error reasons — genuine price-insensitive MOC/LOC flow on announced calendars. That payer is real and large (Russell recon alone: hundreds of $B in final moments; rebal/expiry days lift auction share of ADV to ~20%).

**Why the skeptic rejects amplification for *us*:**
1. **Crowding / anticipatory liquidity:** Multi-strat index-arb pods (Millennium-scale capital; 2022 Russell overcrowding losses) and better anticipation have compressed multi-day index effects toward zero; liquidity providers pre-position and unwind *into* the auction, so residual 15:55→16:00 dislocation need not grow with passive AUM.
2. **Universe mismatch:** Violent rebal flow is concentrated in adds/deletes and small/mid names (BMLL Russell-day dislocation sample: SMCI, MSTR, ALAB, …). Our champion names (NVDA/TSLA/AMD/MU/GOOGL-class) are already-in mega constituents; proportional reweight sells/buys are often rounding error vs ADV. Share-change (not add/delete) is the common event type — and its continuous→close impact is sub-bps.
3. **ADV/depth spikes can *reduce* residual basis:** 8–27× closing-auction volume multiples on rebal share-change names (Dimensional) deepen the auction book; NYSE notes rebal-day early auction liquidity in Russell 1000 names leaves late orders *smaller relative* to existing auction liquidity. Larger absolute imbalance ≠ larger mid→close basis in bps if depth scales faster.
4. **Confounds & special order types:** Many rebal days co-locate with triple-witching; NYSE D-orders / late LOC / imbalance-offsetting and Nasdaq 15:50–15:55 cancel-lock create noisier indicative paths. Higher vol of basis without higher E[edge] is pure noise tax under ~20 bps/event sd.
5. **Calendar sparsity:** The schedule is public and sparse — not a daily structural edge like the champion’s every-session close.

**Capacity intuition:** Institutional rebal arb is capacity-constrained and crowded at multi-day horizon; our retail $1k–$10k size is irrelevant for capacity but also irrelevant for *power* — the n bottleneck is calendar density, not dollars.

### Claims
C1 [CONFIRMED] (T2, JF Apr 2025 / SSRN 2024, sample 1980–2020 S&P and other index families): Multi-day S&P 500 addition abnormal returns fell from ~7.4% (1990s) to <1% / ~0.3–0.8% in the 2010s (indistinguishable from zero); deletions similarly collapsed; pattern generalizes across Russell/Nasdaq index families — index-change *predictable-flow alpha is largely arbitraged*. — Greenwood & Sammon, *Journal of Finance* 80(2); https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4294297 ; summary https://alphaarchitect.com/disappearing-index-effect/

C2 [CONFIRMED] (T3/T2-adjacent vendor research, Aug 2025, sample 2019–2023, 10 US equity indices): Stocks with index *share changes* show 8×–27× closing-auction volume vs 30-day median; continuous mid→close return is only **+0.15 bps per +2% share increase** (and −0.15 bps for decreases), with next-open reverse ~0.55 bps — **orders of magnitude below the champion’s 10 bps basis gate**. — Dimensional, “Another Hidden Cost for Index Funds: Index Share Changes”; https://www.dimensional.com/nl-nl/insights/another-hidden-cost-for-index-funds-index-share-changes

C3 [CONFIRMED] (T1/T3 venue research, Jan 2024): On rebalance days, prices are *more sensitive* to large late imbalance changes (Russell 1000: median ~1.77× spread reference-price move vs ~0.71× on standard days for top-tail orders) — elevates **noise/vol**, not a free mean-edge gift; also early rebal-day auction liquidity in widely held names reduces relative size of late orders vs the book. — NYSE Data Insights, Poser; https://www.nyse.com/data-insights/closing-auction-order-impact-size-opportunities-late-in-the-day

C4 [CONFIRMED] (T3, Jun 2025, 2024 Russell recon case): On rebal/option-expiry days auction ≈20% of daily volume (vs ~9% typical); Russell day shows sharp auction notional spikes and elevated mid→close *dislocation for add names* — but cited names are rebal *targets*, not mega-core holds. — BMLL / Traders Magazine; https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

C5 [CONFIRMED] (T3, Jul 2022 + practitioner 2024–26): Index rebalance is a **crowded** multi-strat trade; June 2022 Russell saw widespread arb losses when adds sold off pre-effective (factor/energy exposure + overcrowding); Candriam/HFJ and Resonanz document capacity/crowding as first-order risk. — Resonanz Capital; https://resonanzcapital.com/insights/an-overcrowded-russell-rebalance ; Hedge Fund Journal / Candriam index arb note

C6 [PLAUSIBLE] (T3, Jan 2026): On rebalance days passive+active MOC cluster can push close away from pre-auction equilibrium (“price-forming” vs “price-revealing”) — **supports large dislocation in *less-liquid* names**, not that residual NOII basis in mega-liquid names is more *tradable* at 15:55 after continuous pricing. — SSGA, “Closing time…”; https://www.ssga.com/is/en_gb/institutional/insights/how-passive-investing-reshaping-microstructure

C7 [CONFIRMED] (T1 calendar mechanics): US rebal density is sparse — S&P family quarterly (3rd Fri Mar/Jun/Sep/Dec, co-located with triple-witch), MSCI ~quarterly effective dates, Russell recon historically 1×/year (semi-annual from Dec 2026). Rough upper bound ~10–20 “major rebal” sessions/year before name-level filters. — NYSE rebal definition footnote; LSEG Russell recon materials; Nasdaq trading calendar

C8 [PLAUSIBLE] (T2/T3, excess volume literature): Reconstitution-day volume far exceeds ETF rebalancing alone (Sammon/Chinco-style excess volume; 3×+ “someone else”); excess includes arbs and hedgers — consistent with **competition for the residual** at the close, not an uncontested retail free lunch. — Excess reconstitution-day volume literature (e.g. alexchinco.com / marcosammon.com PDFs)

C9 [UNVERIFIED] (none primary for our exact structure): That rebal days *increase* E[champion bps/event] or hit-rate in NVDA/TSLA/AMD/MU/GOOGL after a 15:55:10 NOII basis ≥10 bps filter. No T1/T2 study of NOII-basis economics stratified by rebal calendar was found. — gap

C10 [PLAUSIBLE] (T3, Alphanume 2026 + Greenwood–Sammon mechanism): Naive multi-day index front-run is dead; surviving institutional trade is probability-weighted multi-event liquidity provision with 5–10× leverage — retail manual 5–25 s cannot compete on that book, only on single-print residual basis which may be *smaller* when depth is largest. — https://alphanume.substack.com/p/a-cracked-quants-guide-to-the-index

### Constraint gates
| Gate | Result | Clause |
|---|---|---|
| 1 Latency | PASS | Decision is scheduled (15:55 snapshot → close); same as champion. |
| 2 Access | PASS | Retail MOC/LOC path same as champion; no special institutional rebal order type required for *our* side. |
| 3 Session | PASS | Flat at 16:00 cross via MOC/LOC; in-mission. |
| 4 Data | PASS | Owned Databento Nasdaq NOII + SIP; calendar flags free/public; $0 incremental. |
| 5 Fill realism | PASS | Single-print exit at close; same structure as champion. |
| 6 Statistics | **FAIL** | Calendar n: ~10–20 major rebal days/year × 5 names ≈ 50–100 name-days/year → ~300–600 over 6y *before* |basis| filter and “name actually has rebal flow” filter. After filters, n≪250 events *and* sessions ≪150 for the rebal stratum alone. Brief: flag **UNDERPOWERED-BY-DESIGN**. Pooling all sessions kills the “rebal amplification” estimand. |
| 7 Protocol | FAIL-as-promotion | Calendar conditioning is pre-statable, but Stage A promotion of a rebal-only or rebal-amplified *mean* cannot clear power; any registered look must be diagnostic-only or pooled with explicit multiplicity cost. |

**Survivor-profile score: 2/5**
1. Single-print/auction execution → **+1** (same as champion)
2. Scheduled decision instant → **+1**
3. Named price-insensitive payer → **0** for *our names on rebal day* (payer exists market-wide; not clearly active as forced flow *in mega-core holds* vs add/delete targets)
4. Historically testable cheaply → **0** for *inference* (data cheap; **power** not)
5. Expected effect ≥2× cost burden at our size → **0** (no evidence E[gross] rises; Dimensional continuous→close ~0.15 bps/2% share change argues against large mid→close residual in liquid names)

### Economics sketch
- **Cited rebal-related gross (not our structure):** multi-day index effect ~0 in recent decade (C1); continuous→close share-change impact **0.15 bps / 2% shares** (C2); Russell-day mid→close *dislocation spikes* in add names (C4, magnitude not standardized to our 15:55 basis unit in sources).
- **Our cost burden:** same as champion (taker entry into mid/NOII side; exit at single print) — spread + slippage in last ~5 min; not the multi-day borrow/factor book of institutional rebal arb.
- **Net prior for “rebal amplification of champion”:** ~0 to slightly negative (higher basis vol without higher mean; possible anti-select when depth is deepest). Not a +2.5 bps/event *uplift*.
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**; rebal stratum has **no independent cited mean** in our units and fails power to estimate one cleanly.

### Proposed next test (only if OPEN-TESTABLE)
*Not proposed as OPEN-TESTABLE for promotion.* If orchestrator still wants a **$0 diagnostic** (does not flip NOT-VIABLE-STRUCTURAL for Stage A):
- **Hypothesis (diagnostic):** On major rebal ∪ triple-witch sessions, P(|basis|≥10 bps) and mean signed basis→close bps differ from non-event sessions in the 5–28 Nasdaq NOII names.
- **Named payer:** Index/ETF MOC on effective dates (mechanism pre-stated; effect in mega-names is the open question).
- **Data:** owned NOII + public rebal calendars; $0.
- **Universe:** core 5 first; expand to M11 28 only if descriptive n needs padding.
- **Expected n & power:** rebal-only cells: **UNDERPOWERED-BY-DESIGN** (~dozens–low hundreds name-events over full history post-|basis| filter). Report only descriptive means/CIs; do **not** claim Stage A pass.
- **A-priori thresholds:** none for promotion; kill “amplification edge” narrative if rebal mean ≤ non-rebal mean or CI width > |mean|.
- **Promotion rule:** none. Diagnostic only.
- **Kill criteria:** any attempt to promote rebal-stratum edge without n≥250 & ≥150 sessions fails protocol.
- **Trial family:** do **not** charge a new family for promotion; if logged, tag as base-rate/diagnostic under Q12 with UNDERPOWERED flag.

### Sources
1. **[T2]** Greenwood, R. & Sammon, M. “The Disappearing Index Effect.” *Journal of Finance* 80(2), Apr 2025 (SSRN Sep 2024; sample 1980–2020). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4294297
2. **[T3]** Swedroe/Alpha Architect summary of Greenwood–Sammon, 2024-11-08. https://alphaarchitect.com/disappearing-index-effect/
3. **[T3]** Dimensional Fund Advisors, “Another Hidden Cost for Index Funds: Index Share Changes,” 2025-08-29 (sample 2019–2023). https://www.dimensional.com/nl-nl/insights/another-hidden-cost-for-index-funds-index-share-changes
4. **[T1/T3]** NYSE Data Insights (Poser), “Closing Auction Order Impact: Size Opportunities Late in the Day,” 2024-01-11. https://www.nyse.com/data-insights/closing-auction-order-impact-size-opportunities-late-in-the-day
5. **[T1/T3]** NYSE Data Insights (Li), “Closing auction: Liquidity momentum around rebalances,” 2022-08-25. https://www.nyse.com/data-insights/closing-auction-liquidity-momentum-around-rebalances
6. **[T3]** BMLL / Traders Magazine, “Into the Close… Russell Reconstitution,” 2025-06-24. https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution
7. **[T3]** SSGA, “Closing time: How passive investing is reshaping equity market microstructure,” 2026-01-23. https://www.ssga.com/is/en_gb/institutional/insights/how-passive-investing-reshaping-microstructure
8. **[T3]** Resonanz Capital, “An Overcrowded Russell Rebalance,” 2022-07-20. https://resonanzcapital.com/insights/an-overcrowded-russell-rebalance
9. **[T3]** Alphanume Research, “A Cracked Quant’s Guide to The Index Rebalancing Trade,” 2026-07-14 (partial free; index-effect decay cites Greenwood–Sammon). https://alphanume.substack.com/p/a-cracked-quants-guide-to-the-index
10. **[T3]** Candriam / The Hedge Fund Journal, index arbitrage overcrowding (Russell 2022 losses), 2024. https://thehedgefundjournal.com/candriam-index-arbitrage-absolute-return-equity-market-neutral/
11. **[T1]** Nasdaq Closing Cross FAQ / cutoff times (MOC 15:55, LOC 15:58, IO to 16:00). https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf
12. **[T1/T3]** LSEG / FTSE Russell reconstitution key facts & semi-annual shift (2026). https://www.lseg.com/en/ftse-russell/russell-reconstitution
13. **[T2/T3]** Excess reconstitution-day volume (Sammon/Chinco-related PDFs; excess volume beyond ETF needs). https://www.alexchinco.com/excess-reconstitution-day-volume.pdf
14. **[T3]** Euronext Espresso, index rebalancing day volumes/imbalances (EU; context only), 2025-11-05. https://www.euronext.com/en/news/index-rebalancing-and-auction-imbalance-keen-find-balance

#### Queries used
1. `index rebalancing day arbitrage decay overcrowded closing auction`
2. `Russell rebalance S&P reconstitution closing auction predictability arbitraged`
3. `ETF rebalance day ADV spike basis compression closing auction microstructure`
4. `index rebalance arbitrage crowded trade losses decay alpha`
5. `closing auction price impact rebalance day front-running reduces dislocation`
6. `Nasdaq MOC LOC rebalance day special order handling cutoff`
7. `"closing auction" "basis" OR "dislocation" OR "premium" rebalance OR reconstitution megacap`
8. `how many index rebalance days per year S&P quarterly Russell MSCI calendar frequency`
9. `Greenwood Sammon disappearing index effect reconstitution returns decay`
10. `closing auction liquidity depth rebalance day reduces price impact megacap`
11. `statistical power closing auction rebalance days sample size annual events`
