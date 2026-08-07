## DR-X3 — C practitioner findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence MED on overall E/Q prior; LOW on last-15-min) — Practitioner broker-shootout experiments (Schwarz et al. 2022→JoF 2025; Huang/Jorion/Lee/Schwarz Fed FEDS 2024-080) with controlled simultaneous market orders at ~$100 clips show **broker-level E/Q for small retail marketables ranges ~0.09–0.58**, with volume-weighted wholesaler aggregates ~0.40–0.45 in industry/vendor commentary (Fidelity Capital Markets 2025; Citadel OCR comment 2023). Alpaca is a classic PFOF wholesaler broker (Virtu/Citadel/Jane Street; marketable PFOF = **12% of spread**, cap 5¢/sh per 606 Q3 2025) with **no published client E/Q** — not in any controlled shootout. IBKR Lite E/Q ~0.53–0.58 (worst among zero-commission accounts in experiments); IBKR Pro SmartRouting → exchanges/ATS often **worse** on pure PI than PFOF brokers. Last-15-min E/Q for liquid Nasdaq small clips is **UNKNOWN** from practitioner sources (no public E/Q×TOD table for retail marketables). Phase-0 live micro-order audit on Alpaca at our profile is the only way to pin Alpaca and late-window numbers.

What would flip it: (a) a live Alpaca log of n≥100 marketable fills at $400–$3k on the 5 megacaps showing median E/Q ≥0.90 (or one-way shortfall ≥ quoted half-spread), which would keep full half-spread + slip as the honest cost prior; or (b) a public Rule 605 summary / 606-linked E/Q for Alpaca small-bucket marketables on liquid Nasdaq proving E/Q ≤0.30, which would cut M16 cost burden sharply. **Timeline note (updated 2026-07-21):** the modernized Rule 605 (odd-lot + E/Q buckets) that would supply (b) without a live experiment does NOT publish until Aug 2026 data → round-lot reports by end-Sep 2026, and odd-lot data in reports only by the first business day of **Nov 2026** (SEC extended compliance from Dec 14 2025 to **Aug 1 2026**). So through at least Q3 2026 the **Phase-0 live micro-order audit is the only path to an Alpaca-specific / last-15-min number.**

### Mechanism
**Who pays (execution-quality framing, not alpha):**
1. **Wholesalers (Citadel, Virtu, Jane Street, G1X, …)** internalize uninformed retail flow and share part of the quoted spread as price improvement (PI) to the client and PFOF to the broker. Source of funds is the same anticipated inventory/spread profit — 606 material-aspects text (Alpaca, standard industry language) states explicitly that more PFOF ⇔ less room for PI.
2. **Retail broker** chooses the wholesaler pool and routing style (proportional slice vs selective/smart). Best-execution duty (FINRA 5310) requires monitoring and re-routing when material differences persist; experiments show **most large PFOF brokers do not re-route aggressively** on small odd-lot flow (Huang et al.).
3. **Why PI exists and persists:** Retail flow has low adverse selection vs co-mingled exchange flow; wholesalers can safely price inside NBBO. Concentration (Top-4 ~94% of experiment flow) coexists with PI because brokers can switch (selective brokers do) and entry (Jane Street @ Robinhood) compresses incumbent E/Q ~14% in one case. Persistence of *dispersion across brokers* is the puzzle: same venue, same trade, systematically different PI by broker (Schwarz et al. “broker execution” attribution).
4. **Capacity at $400–$3k:** Irrelevant — odd-lot / small-notional is the core wholesaler product; our size is *inside* the segment experiments study, not above internalization thresholds.

**Alpaca mapping:** Routes non-directed NMS equity flow to Virtu / Citadel / Jane Street (Q3 2025 S&P500: Virtu ~43%, Citadel ~39%, JNST ~17%). Marketable core-session PFOF = 12% of spread / share, cap 5¢. Closing-auction fills on Citadel path: **12 mils/sh charge to Alpaca** (no rebate). No customer-facing PI dashboard. Closest experiment analogue = mid-tier PFOF proportional broker (E*Trade/Schwab/RH range), **not** Fidelity/TD best-in-class and **not** IBKR Pro exchange-routing.

**Last-15-min mechanics (practitioner):** Continuous book spreads and one-sided late flow rise into the close; retail dollar volume is **less** concentrated at the close than institutional on-exchange flow (Brown/Johnson/Kothari/So 2024/25). Institutional TCA vendors (BestEx Research 2025 TOD paper) claim **lower** market-impact in the final hour for schedule algos — a different structure (participation-rate impact, not retail E/Q). No wholesaler or broker whitepaper publishes retail E/Q broken by clock minute for 15:45–16:00. **UNKNOWN** whether PI fraction holds when quoted half-spread is already tight (our 0.73 bps at 15:55:10) and flow is auction-aware.

### Claims
C1 [CONFIRMED] (T3 experiment / T2 JoF path, Sep 2022 WP → JoF 2025, sample Dec 2021–Jun 2022, n≈85k simultaneous market orders, ~$100 clips, 128 stocks stratified): Mean account-level **round-trip cost −7 to −46 bps** of notional (ex commissions); average PI **$0.03–$0.08/sh ≈ 19–47% of NBBO**. Best: TD Ameritrade / Fidelity; worst: IBKR Pro then IBKR Lite. Dispersion is **same-venue different-PI-by-broker**, not venue choice. PFOF $/sh (~0.1–0.2¢) cannot explain the gap. **Gross of commissions; net of PI.** — Schwarz, Barber, Huang, Jorion, Odean, “The ‘Actual Retail Price’ of Equity Trades”; https://microstructure.exchange/papers/Schwartz_et_al_,_2022_WP,_The_'Actual_Retail_Price'_of_Equity_Trades.pdf ; JoF summary https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467

C2 [CONFIRMED] (T3 Fed staff WP, 20 Jul 2024, sample Dec 21 2021–May 31 2023, n≈150k trades, ~$100 or 1 share, parallel across 6 brokers): Broker-level average **E/Q** (effective/quoted full spread): **TD Ameritrade 0.093, Fidelity 0.142, Schwab 0.229, E\*Trade 0.322, Robinhood 0.421, IBKR Lite 0.527**. Within-broker max−min wholesaler E/Q gap = **42–151% of broker mean**, persistent. Proportional brokers (ET/FD/SC/TD) barely re-route on past E/Q; selective (RH, IBKR Lite) do. Hypothetical re-route to prior-month best wholesaler **cuts E/Q ~34% average**. Jane Street entry at RH → incumbents cut E/Q ~**14%**. Trades end by **15:50 ET** (no last-10-min coverage). — Huang, Jorion, Lee, Schwarz, FEDS 2024-080; https://www.federalreserve.gov/econres/feds/files/2024080pap.pdf

C3 [CONFIRMED] (T3 vendor-CONFLICTED, Dec 2025, Fidelity Capital Markets whitepaper, industry aggregate): Retail **E/Q improved ~60%**, from **>100% in 2011 to ~41% in 2025**. E/Q framed as the standardized benchmark for immediately marketable retail. Fidelity also markets Q4 2025 PI share stats (Nasdaq ~94% of shares price-improved) — **CONFLICTED** (broker selling execution quality). — https://clearingcustody.fidelity.com/app/literature/view?itemCode=9921945&renditionType=PDF ; overview https://clearingcustody.fidelity.com/insights/topics/working-with-clients/the-benefits-of-enhanced-execution-reporting-quality-for-investors

C4 [CONFIRMED] (T3 wholesaler-CONFLICTED, 31 Mar 2023, Citadel Securities OCR comment): Wholesale E/Q for market orders improved ~**60% over a decade** to ~**45%** (“retail pays ~45% of the quoted half-spread”); wholesaler–exchange E/Q gap **>50%** even for smallest orders; market-order fill rates “essentially 100%” vs exchange ~58% (SEC figure cited); cites Schwab study $3.4B client savings 2021 via wholesalers. **CONFLICTED** (defending status-quo internalization). — https://www.citadelsecurities.com/wp-content/uploads/sites/2/2023/03/Citadel-Securities-Response-to-the-Auctions-Proposal-Final.pdf

C5 [CONFIRMED] (T1, Alpaca Securities Rule 606(a) Q3 2025, held NMS): Non-directed equity flow routed to **Virtu (NITE), Citadel (CDRG), Jane Street (JNST)** only in the report (S&P500 July: Virtu 43.4% / Citadel 39.4% / JNST 17.1% of non-directed). **Marketable orders filled in core session: PFOF = 12% of spread per share, capped at 5 cents/share.** Non-marketable ≥$1: 20 mils/sh rebate. **Primary closing auction/cross on Citadel path: 12 mils/sh charge against Alpaca.** Material-aspects text: PI and PFOF draw from the same market-maker profit pool (explicit conflict). **No E/Q or PI $ disclosed.** — https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2025Q3.pdf

C6 [CONFIRMED] (T1/T3, IBKR order-routing disclosures + experiment): **IBKR-PRO** → SmartRouting (exchanges, dark pools, IBKR ATS); **IBKR-LITE** → OTC market makers with PFOF; Lite disclosure warns PFOF “may reduce price improvement.” Experiments place **IBKR Lite E/Q ~0.53–0.58** and **IBKR Pro among the worst pure-PI outcomes** (exchange fills lack wholesaler midpoint PI). Pro is **not** the PI champion for small marketables; it optimizes all-in cost including exchange fees/rebates for active/large flow. — IBKR routing PDF https://gdcdyn.interactivebrokers.com/Universal/servlet/Registration_v2.formSampleView?formdb=3074 ; SmartRouting https://www.interactivebrokers.com/en/trading/smart-routing.php ; E/Q numbers from C2

C7 [CONFIRMED] (T2/T3 Rule-605 landscape, Dyhrberg/Shkilko/Werner Dec 2023 WP → JFE 2025, multi-year Rule 605): Wholesaler liquidity-demanding orders: **E/Q ≈ 0.76** vs exchanges **0.97**; effective spread ~53 bps vs ~51 bps on wider quoted spreads (wholesaler QS 69.6 bps vs exch 52.9); 66% of wholesaler shares improved vs 9% exchange. **Equal-weighted across stock-months** → higher E/Q than volume-weighted large-cap experience. Pre-modernization 605 **excludes odd lots**. — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4313095 ; table excerpt via AEA program PDF

C8 [CONFIRMED] (T3, Brown/Johnson/Kothari/So Jun 2024 WP, sample RH + TAQ odd lots 2016–2022 + 605 round lots 2019–2022; **Robinhood data relationship — CONFLICTED annotation**): Dollar-volume-weighted off-exchange round-lot retail: PI **>50% of half-spread**; off-exchange effective spreads ~**1.8 bps** vs on-exchange ~**4.6 bps**. Retail less concentrated at close (when QS is tightest) than on-exchange; TOD quote differences can flip odd-lot effective-spread ranking, but **E/Q still lower off-exchange**. Total retail cost “below 6 bps” under zero-commission model. — https://www.travislakejohnson.com/pdfs/Brown%20Johnson%20Kothari%20So%202025%20(WP).pdf

C9 [CONFIRMED — timeline REVISED 2026-07-21] (T1, SEC Rule 605 modernization adopted Mar 2024 / FR Apr 2024; **compliance date EXTENDED** by SEC release 34-104147, FR 2 Oct 2025, from **Dec 14 2025 → Aug 1 2026**): Summary + detailed reports will require **E/Q**, notional order-size buckets ($250→$200k+), odd-lot and fractional buckets, size improvement, realized spreads at multiple horizons; reporters include broker-dealers with >100k accounts. **Sequence:** market centers begin collecting under the amended rule **Aug 1 2026**; first reports (Aug 2026 data) public by **end-Sep 2026**; SIPs disseminate odd-lot info from **first business day May 2026**, and reporting entities must fold odd-lot data into 605 reports by **first business day Nov 2026**. **Consequence for us:** there is **no public modernized odd-lot / E/Q report as of 2026-07-21** — the regulatory substitute for a live audit is 3–5 months away for round lots and ~4 months away for odd lots. — SEC extension https://www.federalregister.gov/documents/2025/10/02/2025-19316/extension-of-compliance-date-for-disclosure-of-order-execution-information ; SEC FAQ (Apr 1 2026) https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/frequently-asked-questions-rule-605-regulation-nms ; Katten summary https://quickreads.ext.katten.com/post/102j23y/the-effective-spread-of-order-execution-quality-reporting ; SEC final 34-99679 https://www.sec.gov/files/rules/final/2024/34-99679.pdf

C11 [CONFIRMED] (T1/T3 broker-CONFLICTED, refreshed 2026 disclosures): Current-year broker PI headline stats confirm the ~2–3¢/sh PI regime but remain size-unmatched to our clip: **Schwab Q2 2026** clients received **$966M** price improvement on exchange-listed equity orders; **Fidelity 2025** reports **>$3.2B** client savings with PI averaging **$26.04 per 1,000-share equity order (≈2.6¢/sh)**; **Robinhood Q1 2026 Rule 606** shows PFOF **up to 137.89¢ per 100-share market order** on S&P 500 names (≈1.38¢/sh PFOF — competes with client PI). A **SEC December 2025 enforcement/review** note flags PFOF-heavy brokers underperforming on **larger** orders. None publishes a small-clip ($400–$3k) E/Q broken by time of day → confirms the last-15-min gap is still **UNKNOWN**. **CONFLICTED** (brokers marketing execution quality). — Schwab https://www.schwab.com/execution-quality ; Fidelity https://www.fidelity.com/trading/execution-quality/overview ; RHF 606 https://cdn.robinhood.com/assets/robinhood/legal/RHF%20SEC%20Rule%20606%20and%20607%20Disclosure.pdf

C12 [CONFIRMED] (T2, Schwarz/Barber/Huang/Jorion/Odean, now **published** Journal of Finance 2025, vol. via doi 10.1111/jofi.13467; sample Dec 2021–Jun 2022): The "Actual Retail Price" broker-shootout is no longer a working paper — **peer-reviewed JoF 2025**, raising C1 from T3→**T2**. Core result unchanged: large same-venue PI dispersion across brokers not explained by PFOF $/sh; TD Ameritrade/Fidelity best, IBKR worst. — https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467

C13 [CONFIRMED] (T1, Alpaca Securities Rule 606(a) **Q4 2025**, held NMS — routing set unchanged vs Q3): The Q4 2025 606 report exists and continues to route non-directed NMS equity flow to the **same three wholesalers (Virtu / Citadel / Jane Street)** — no new venue, no structural change vs the Q3 2025 figures in C5. (PDF confirmed present at the disclosure library; per-field figures not re-parsed this pass — routing composition materially unchanged.) — https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2025Q4.pdf

C10 [PLAUSIBLE] (T3 vendor-CONFLICTED, BestEx Research Jul 2025 “Time of Day Effect”): Holding participation rate and order size fixed, **institutional** market-impact cost is **lower in the final hour** than earlier RTH (Russell 2000 vignette). **Does not measure retail E/Q or PI**; sells Pulse Analytics / AMS — **CONFLICTED**. Useful only as a reminder that late-day **liquidity** can improve even as continuous spreads and auction risk change. S3 Matching sells BD best-ex dashboards (routing scorecards) — infrastructure, not public E/Q series. — https://www.bestexresearch.com/insights/the-time-of-day-effect-a-breakthrough-in-trading-cost-optimization ; S3 https://s3.com/best-execution-analytics/

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **PASS / N-A** | Cost measurement is post-fill; 5–25 s manual reaction does not change E/Q definition. Champion continuous entry still subject to fill clock. |
| 2 | Access | **PASS** | Marketable market/limit at $400–$3k on Alpaca/IBKR is native retail product; wholesaler internalization is the default path. |
| 3 | Session | **PASS** | RTH marketables including 15:45–15:50 window are in-mission; 15:55 continuous entry is the champion path (MOC blocked on Alpaca post-15:50 — separate DR-Q4-6). |
| 4 | Data | **PASS** | Phase-0 audit uses **owned** broker tickets + free SIP/Alpaca quote snapshot at send; optional 606(b)(1) venue request ($0). No commercial TCA feed required. Recurring BestEx/S3 TCA = FAIL ≤$100 if purchased. |
| 5 | Fill realism | **PASS** | Measurement *is* the fill; no maker assumption. Prefer market + marketable-limit both logged. |
| 6 | Statistics | **PASS** | n≥100 fills stratified by name × TOD bucket is achievable in weeks at $400–$3k; power vs ~20 bps event noise is for *edge* trials — for cost prior, SE of median E/Q tightens at n~50–100. |
| 7 | Protocol | **PASS** | Named mechanism = wholesaler PI on low-toxicity small retail vs full half-spread sim; pre-register E/Q and shortfall-vs-mid distributions before opening the sealed audit window; charges Phase-0 / M16 cost-model family (not an alpha family). |

**Survivor-profile score: 3/5** (this charge is a **cost prior**, not a new edge — scored as “does the measurement support deployable economics”)
1. Single-print/auction execution — **NO** (continuous marketable fill; auction exit separate)
2. Scheduled decision instant — **PARTIAL** (15:55:10 entry is scheduled; fill quality is not)
3. Named price-insensitive payer — **N-A** for cost study (wholesaler is the *liquidity provider*, not the alpha payer)
4. Historically testable ≤~$100 — **YES** (live tickets $0 data; 605/606 free)
5. Expected effect ≥2× cost burden — **YES if** measured E/Q ≲0.5: one-way cost falls from sim 0.73–1.46 bps toward ~0.3–0.5 bps, widening net edge room vs champion +2.5 / +12.5

### Economics sketch
**Definitions used:** E/Q = (effective spread) / (NBBO quoted spread), with effective = 2|exec − mid|. One-way cost in bps of mid ≈ **E/Q × quoted_half_spread_bps**. E/Q = 0 → mid fill; E/Q = 1 → fill at NBBO; E/Q > 1 → worse than NBBO (slip / walk).

**Gross cited (practitioner / experiment):**
| Source | Profile match | E/Q (full) | Notes |
|--------|---------------|------------|-------|
| Huang et al. 2024 broker means | ~$100 market, mixed names, RTH ex last 10 min | **0.09–0.53** | TD best, IBKR Lite worst |
| Huang Table 7 originals | same | mean **~0.31** across 6 accounts | re-route → ~0.23 |
| Fidelity CM 2025 | industry retail aggregate | **~0.41** | CONFLICTED |
| Citadel 2023 OCR | wholesaler market orders | **~0.45** | CONFLICTED |
| Dyhrberg et al. 605 | equal-wt stock-months, round lots | wholesaler **0.76** | wide-spread names pull up |
| Brown et al. vol-wt | large-cap heavy, round lots | off-ex effective **~1.8 bps** full (≈ E/Q×QS) | PI >50% of half-spread |
| Schwarz et al. | ~$100, 6 accounts | PI 19–47% of NBBO → E/Q ≈ **0.06–0.62** | consistent with C2 |

**Our cost burden for this structure (continuous marketable entry):**
- Quoted half-spread prior (owned sim, 5 megacaps @ 15:55:10): **0.73 bps median**.
- Sim fill model today: **full half-spread + 0.5–1 bp slip → shortfall median 1.46 bps** (≈ E/Q_implied ~2.0 if vs 0.73 half — i.e. *worse than NBBO*, conservative).
- Zero commission through 2026-12-31 (Alpaca promo); post-promo fee = stress annotation only.
- Alpaca PFOF 12% of spread is paid by wholesaler from same pool as client PI — does **not** appear as a line-item client fee, but **competes** with PI.

**Predicted E/Q for our profile ($400–$3,000 marketable, liquid Nasdaq, Alpaca wholesaler path):**

| Window | Predicted E/Q | Implied one-way cost @ 0.73 bp half | Confidence |
|--------|---------------|--------------------------------------|------------|
| **Overall RTH** (ex last 15) | **0.35–0.55** (central **0.45**) | **0.26–0.40 bps** (central **~0.33**) | **MED** — maps to mid-tier PFOF experiment brokers + industry ~0.41–0.45; Alpaca unmeasured → band not point |
| **Last 15 minutes** (15:45–16:00 continuous) | **UNKNOWN** | **UNKNOWN** | **LOW** — no retail E/Q×TOD table; plausible stress band 0.45–0.80 if PI fraction erodes when flow is one-sided / auction-informed, but **not** a finding |
| **Vs current sim** | E/Q 0.45 vs sim ~1.0+ | **~0.33 vs 0.73–1.46 bps** | If Phase-0 confirms, sim overstates entry cost by **~0.4–1.1 bps** one-way |

**Net prior for M16 / Phase-0:** Treat **E/Q = 0.45 (one-way ≈ 0.33 bps at 0.73 half)** as the **central deployable prior** for small Alpaca marketables in normal RTH; keep **full half-spread (E/Q=1.0)** as **stress / kill-if-worse** bound; do **not** credit last-15-min improvement over the central prior until measured. Round-trip continuous (enter+exit continuous) ≈ 2 × one-way; champion structure is enter continuous + exit single-print close → **one** marketable leg of spread cost.

**Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**. A 0.5–1.0 bp reduction in entry shortfall vs current sim is material relative to +2.5 dev mean and small vs +12.5 holdout — still worth locking with Phase-0 because M16 multiplies cost across many minutes-hours plans.

### Proposed next test (OPEN-TESTABLE)
- **Hypothesis:** On Alpaca live (or paper if fill path identical), marketable market orders of $400–$3,000 notional in NVDA/TSLA/AMD/MU/GOOGL during RTH have median E/Q ≤ 0.55 and median one-way shortfall ≤ 0.50 bps vs mid at send; last-15-min bucket is not worse than overall by >0.15 E/Q points.
- **Named payer / mechanism:** Wholesaler (Virtu/Citadel/JNST) price improvement on low-toxicity small retail; PFOF 12%-of-spread is the competing claim on the same surplus.
- **Data needed:** Owned broker fill tape + NBBO/mid snapshot at order-accept time (Alpaca SIP historical or concurrent quote); optional Rule 606(b)(1) venue ID per fill ($0 request). **No** commercial TCA. Cost **$0** data + small notional risk (round-trip scratch trades).
- **Universe:** 5 core megacaps; optional +5 liquid Nasdaq from M11.
- **Expected n & power:** Target **n≥100** overall, **n≥30** in 15:45–15:50, **n≥20** in 15:50–15:55 (pre-MOC continuous). For median E/Q, n=50 already informative; not an alpha power calc vs 20 bps sd.
- **A-priori thresholds (lock before first live ticket):**
  - Primary: median E/Q ≤ 0.55 overall → adopt central prior 0.45 (or sample median) for M16.
  - Kill / keep conservative sim: median E/Q ≥ 0.90 **or** median shortfall ≥ quoted half-spread.
  - Last-15: if n≥30 and median E/Q_last15 − E/Q_rest > 0.15, flag late window as **elevated cost** and do not share prior with midday.
  - Stratify market vs marketable-limit; record venue via 606(b)(1).
  - Exclude auctions (separate fill economics); exclude halt/LULD.
- **Promotion rule:** If median E/Q ≤ 0.55 and shortfall ≤ 0.5 bps on n≥100 → re-price M16 inventory-book cost model with measured distribution (p25/p50/p75 E/Q); publish Phase-0 receipt to ledger.
- **Kill criteria:** E/Q ≥ 0.90 median; or fills systematically outside NBBO; or Alpaca paper path diverges from live (document and switch to live-only).
- **Trial family charged:** Phase-0 smallness audit / M16 cost model (not an alpha family; does not spend sealed holdout).

### Sources
1. **[T3/T2]** Schwarz, Barber, Huang, Jorion, Odean (2022 WP / JoF 2025). “The ‘Actual Retail Price’ of Equity Trades.” Sample Dec 2021–Jun 2022. https://microstructure.exchange/papers/Schwartz_et_al_,_2022_WP,_The_'Actual_Retail_Price'_of_Equity_Trades.pdf
2. **[T3]** Huang, Jorion, Lee, Schwarz (20 Jul 2024). “Who is Minding the Store? Order Routing and Competition in Retail Trade Execution.” FEDS 2024-080. Sample Dec 2021–May 2023. https://www.federalreserve.gov/econres/feds/files/2024080pap.pdf
3. **[T3 CONFLICTED]** Fidelity Capital Markets (2025). “The benefits of enhanced execution quality reporting for investors.” E/Q ~41% in 2025. https://clearingcustody.fidelity.com/app/literature/view?itemCode=9921945&renditionType=PDF
4. **[T3 CONFLICTED]** Citadel Securities (31 Mar 2023). Comment on Order Competition Rule. E/Q ~45%, PI claims. https://www.citadelsecurities.com/wp-content/uploads/sites/2/2023/03/Citadel-Securities-Response-to-the-Auctions-Proposal-Final.pdf
5. **[T1]** Alpaca Securities LLC Rule 606(a) Held NMS Report, Q3 2025. Virtu/Citadel/JNST routing; 12% spread PFOF. https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2025Q3.pdf
6. **[T1/T3]** Interactive Brokers order routing / PFOF disclosure (Pro SmartRouting vs Lite wholesalers). https://gdcdyn.interactivebrokers.com/Universal/servlet/Registration_v2.formSampleView?formdb=3074 ; https://www.interactivebrokers.com/en/trading/smart-routing.php
7. **[T2]** Dyhrberg, Shkilko, Werner (2023 WP / JFE 2025). “The Retail Execution Quality Landscape.” Rule 605 E/Q 0.76 wholesaler vs 0.97 exchange. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4313095
8. **[T3 CONFLICTED-data]** Brown, Johnson, Kothari, So (Jun 2024 WP). “Anatomy of Trading Costs for Retail Investors.” Vol-wt off-ex ~1.8 bps effective; PI >50% half-spread; TOD note. https://www.travislakejohnson.com/pdfs/Brown%20Johnson%20Kothari%20So%202025%20(WP).pdf
9. **[T1/T3]** Katten (6 Mar 2024). Rule 605 modernization summary (E/Q metric, odd lots, summary report). https://quickreads.ext.katten.com/post/102j23y/the-effective-spread-of-order-execution-quality-reporting
10. **[T3 CONFLICTED]** BestEx Research (14 Jul 2025). “The Time of Day Effect” (institutional impact, last-hour cheaper). https://www.bestexresearch.com/insights/the-time-of-day-effect-a-breakthrough-in-trading-cost-optimization
11. **[T3]** SIFMA / Craig Lewis (6 Aug 2024). Best Execution proposal critique; SEC admits wholesaler lower E/Q; ~45% midpoint-or-better cite. https://www.sifma.org/news/blog/rethinking-the-economic-analysis-in-the-secs-best-execution-proposal
12. **[T3]** Charles Schwab (2022). “U.S. Equity Market Structure: Order Routing Practices…” (cited by Citadel/Huang; PDF access denied this session — claims via secondary). https://content.schwab.com/web/retail/public/about-schwab/Schwab-2022-order-routing-whitepaper.pdf
13. **[T3 CONFLICTED]** S3 Matching Technologies — Best Execution Analytics product (BD routing scorecards). https://s3.com/best-execution-analytics/
14. **[T1]** SEC Final Rule 34-99679 (2024). Disclosure of Order Execution Information. https://www.sec.gov/files/rules/final/2024/34-99679.pdf
15. **[T1]** SEC Release 34-104147 / Federal Register (2 Oct 2025). **Extension of Compliance Date** for Disclosure of Order Execution Information (Dec 14 2025 → Aug 1 2026; odd-lot in reports by 1st bus. day Nov 2026). https://www.federalregister.gov/documents/2025/10/02/2025-19316/extension-of-compliance-date-for-disclosure-of-order-execution-information ; https://www.sec.gov/files/rules/final/2025/34-104147.pdf
16. **[T1]** SEC Staff FAQ: Rule 605 of Regulation NMS (Apr 1 2026). Order-size notional buckets, odd-lot/fractional, E/Q metric, reporter scope. https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/frequently-asked-questions-rule-605-regulation-nms
17. **[T2]** Schwarz, Barber, Huang, Jorion, Odean (2025). "The 'Actual Retail Price' of Equity Trades." **Journal of Finance 2025**, doi 10.1111/jofi.13467 (peer-reviewed publication of ref 1). https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467
18. **[T1/T3 CONFLICTED]** Alpaca Rule 606(a) Q4 2025 (routing unchanged); Schwab execution-quality (Q2 2026 $966M PI); Fidelity execution-quality (2025 $26.04/1,000-sh); Robinhood RHF Rule 606 (Q1 2026, up to 137.89¢/100-sh order). https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2025Q4.pdf ; https://www.schwab.com/execution-quality ; https://www.fidelity.com/trading/execution-quality/overview ; https://cdn.robinhood.com/assets/robinhood/legal/RHF%20SEC%20Rule%20606%20and%20607%20Disclosure.pdf

#### Queries used
##### Refresh pass (2026-07-21)
- modernized Rule 605 odd-lot bucket execution quality report 2025 effective quoted spread E/Q retail
- Alpaca Rule 606 order routing report Q1 2026 PFOF Citadel Virtu Jane Street
- new Rule 605 report odd lot price improvement wholesaler 100-499 shares October 2025 first reports
- retail price improvement time of day final minutes close effective spread Boehmer subpenny
- Citadel Securities new format Rule 605 report 2026 odd lot E/Q effective spread price improvement statistics
- Alpaca 606 disclosure library latest 2026 marketable PFOF percent of spread
- SEC extends Rule 605 compliance date August 1 2026 odd lot November 2026 order execution
- retail broker execution quality comparison 2025 2026 effective spread price improvement Schwab Fidelity Robinhood experiment update
- Huang Jorion Schwarz "who is minding the store" retail order routing E/Q published Journal 2025 2026

##### Original pass
- retail execution quality Rule 605 price improvement E/Q ratio small orders
- broker comparison execution quality Alpaca Interactive Brokers retail spreads methodology
- Schwab order routing whitepaper retail execution quality E/Q price improvement wholesaler
- Citadel Virtu Jane Street wholesaler retail E/Q ratio Rule 605 small orders
- Battalio Schwarz study broker execution quality experiment SSRN price improvement
- "effective over quoted" retail E/Q 40% 45% wholesaler marketable orders 2023 2024 2025
- Alpaca Markets Rule 606 order routing PFOF wholesaler Citadel Virtu execution quality
- IBKR Pro Lite SmartRouting execution quality effective spread price improvement retail
- retail execution analytics vendor S3 Matching Technologies BestEx Research price improvement dashboard
- time of day price improvement retail last 15 minutes close wholesaler execution quality
- Fidelity E/Q 41% 2025 retail execution quality reporting white paper
- Dyhrberg Shkilko Werner retail execution quality landscape E/Q wholesaler 0.76
- Battalio Jennings wholesaler execution quality May 2022 E/Q price improvement absolute relative
- Schwab 2022 order routing whitepaper E/Q 45% price improvement market orders site:pdf
