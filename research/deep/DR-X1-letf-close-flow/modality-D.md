## DR-X1 — D adversarial findings
### Verdict recommendation
**NOT-VIABLE-STRUCTURAL (HIGH)** as a *new residual / front-run / conditioning signal* — and **EXHAUSTED-BY-FIELD** on the classic LETF-close front-running trade. Independent T2/T3 survey + primary papers find: (a) rebalancing demand is fully predictable from same-day return × AUM long before 15:55, (b) post-2012 samples show economically insignificant late-day price impact after capital flows and rising close liquidity, (c) published front-running strategies do not clear costs outside the 2008 stress tail, and (d) much of the hedge is continuous last-half-hour swap-counterparty trading that can move *mid* before NOII near is live. If any LETF MOC still prints into the auction, it is already inside the champion’s near−mid basis by 15:55:10 — **payer identity, not a new cell**. Hard name-ranking negative: single-stock LETF AUM peaks on **TSLA/NVDA** while holdout carried **MU** and **TSLA ≈ 0**, so LETF-AUM intensity does **not** resolve the M11 alive/dead split.

What would flip it: Pre-registered evidence that predicted single-name LETF rebal notional (Σ (L²−L)·AUM·r) predicts **residual** 15:55:10→cross bps *orthogonal* to |near−mid| and *matches* alive/dead (MU ≫ GOOGL/TSLA) at n≥250 with net ≥+5 bps/event — i.e., residual not already in near. Absent that, cell collapses to “partial explanation of champion payer.”

### Mechanism
**Who would pay (classical story):** LETFs and inverse LETFs must restore target leverage daily; both long and inverse rebalance **in the same direction as the day’s return** (Cheng–Madhavan). Exposure is mostly synthetic (total-return swaps); **swap counterparties** re-hedge the underlying basket/name into the close (Tuzun; Shum et al.; Barbon/Beckmeyer). That hedge is price-insensitive in direction and size ≈ (L²−L)·AUM·r (or L(L−1)·AUM·r).

**Why residual fails for us:**
1. **Anticipation / sunshine liquidity.** Direction and rough size are public from ~midday once r_day and AUM are known. Bessembinder-line predictable-flow theory: liquidity *arrives* for known demand; spreads/depth improve rather than leaving free residual. Continuous mid and any MOC that later forms NOII near absorb the same information the retail trader would use.
2. **Impoundment by 15:55:10.** Champion already trades *with* residual auction basis after near becomes nonzero (~15:55). LETF-driven MOC, if present, is a *component* of that basis, not an orthogonal signal. Conditioning on predicted LETF flow either collinear with basis or adversarially selected when continuous already moved mid.
3. **Off-close / pre-close continuous hedge.** Sponsors submit MOC early in the day; brokers hedge before the auction and *spread* demand (Lenkey survey, fund-sponsor conversations). Empirical end-of-day papers attribute LETF impact to the **last ~30 minutes continuous + close**, not pure auction-only prints — so a large fraction never “touches NOII” as fresh imbalance after 15:55.
4. **Small vs 2024–2026 megacap close.** On a 1% day, 2× fund rebal ≈ 2·AUM·1% (e.g. ~$90M on $4.5B NVDL). NVDA dollar ADV order ~$25–35B; closing-auction share ~9–15% → auction notional multi-billion. Typical-day LETF rebal is low-single-digit % of auction / sub-1% ADV for mega underlyings; only multi-σ return days approach material share — exactly when continuous vol and competition peak.
5. **Name-rank hard negative.** Largest single-stock complexes are **TSLL (~$7.5B)** and **NVDL (~$4–4.5B)** (2025 trackers); single-stock LETF AUM overall ~$30–43B class. Holdout economics: **MU carried, GOOGL/TSLA ~0**. If LETF close flow were *the* name-specific mechanism, TSLA should dominate and MU should not. Ranking fails → mechanism does not explain M11 puzzle.

Persistence of *some* mechanical flow is real; persistence of **retail-capturable residual after 15:55:10** is not supported. Capacity intuition: absolute $ can be large on crisis days, but that is exactly when impact and competition scale; average-day residual after anticipation is the sub-bp field estimate.

### Claims
C1 [CONFIRMED] (T2, Lenkey survey Dec 2024, lit 2009–2023): Peer literature finds **statistically** significant associations of LETF rebal demand with late-day returns/vol, but **economic** associations are insignificant; **no evidence** of profitable front-running of LETF rebal after costs; market provides enough liquidity; impact likely *lower* today as closing-auction volume rose (3.1%→7.5% of dollar volume 2010–2018). — Lenkey, *The market impact of leveraged ETFs: A Survey of the literature*, QFE 8(4), 2024. https://www.aimspress.com/article/doi/10.3934/QFE.2024031

C2 [CONFIRMED] (T2, Ivanov & Lenkey 2018, sample U.S. equity LETFs **2006–2014**): Capital flows **substantially cut** rebalancing demand; after flows + risk factors, LETF rebal accounts for **<1.8% of late-day returns** and **1.2–6.6% of late-day vol** → implied amplification **≲0.9 bps** of average late-day returns and **≲6 bps** of late-day vol for a typical stock. **Economically insignificant.** — *Do leveraged ETFs really amplify late-day returns and volatility?*, J. Financial Markets 41. https://ideas.repec.org/a/eee/finmar/v41y2018icp36-56.html

C3 [CONFIRMED] (T2/T3, Shum et al. 2016 + Lenkey synthesis; sample **2006–2011** for Shum): Late-day vol correlates with rebal/volume ratio in crisis-era data; front-running constructions (e.g. mid-afternoon SSO/SDS on ≥2% moves) showed **gross** gains concentrated in **late 2008**, and **after transaction costs** literature consensus (Shum; Brøgger 2021) is **no significant profit**. CXO summary of Shum WP: 0.60% gross/trade, 104% cum gross — **NO-COST-MODEL / stress-concentrated / DECAY-UNKNOWN post-2012**. — Shum, Hejazi, Haryanto, Rodier, *Rev. Finance* 20 (2016); CXO 2012-11-19. https://www.cxoadvisory.com/volatility-effects/front-running-leveraged-etfs-at-the-end-of-the-day/

C4 [CONFIRMED] (T2, Brøgger 2021, sample leveraged VIX products **2010–2017**): Price impact of predictable LETF-style rebal **declines over time**; average price move ~**5.9 bps** (~40% of half-spread) — not a multi-bp residual after costs. Complements equity-LETF nulls on post-crisis samples. — *The market impact of predictable flows: evidence from leveraged VIX products*, J. Banking & Finance 133. (via Lenkey survey table)

C5 [CONFIRMED] (T2/T3, Cheng & Madhavan 2009 + Lenkey restatement): Rebal demand scales ~**A·x(x−1)·r** (A=AUM, x=leverage). At **$19B** aggregate equity LETF AUM (2009 snapshot), a **1% / 5%** index day implied **$0.79B / $3.9B** aggregate rebal ≈ **17% / 50% of then-median MOC volume**. Sensational early capacity claims used crisis-era liquidity; **aggregate U.S. LETF AUM later >$80B (2023 survey)** without the predicted systemic close breakdown — liquidity scaled. — Cheng & Madhavan, *JOIM* 2009; Lenkey 2024 §2–3.

C6 [CONFIRMED] (T2/T3, Barbon / Beckmeyer / Buraschi / Moerke; end-of-day windows): LETFs are synthetic; **swap counterparties** re-hedge physical exposure. LETF rebal impact is concentrated in the **last half-hour / end-of-day window** (coefficients near zero for earlier windows); option MM hedges have more timing discretion. Sponsors may **MOC early**; **brokers pre-hedge and spread** demand (Lenkey fund-sponsor footnote). Implies substantial flow in **continuous** 15:30–16:00 path — **moves mid before / alongside NOII**, not only as post-15:55 residual imbalance. — Working paper / FoFI 2022 versions; https://wp.lancs.ac.uk/fofi2022/files/2022/08/FoFI-2022-027-Mathis-Moerke.pdf ; Lenkey 2024 n.6.

C7 [CONFIRMED] (T3, ETF.com / VettaFi-class trackers 2025–2026): Single-stock leveraged ETFs ~**$31–43B** AUM class; largest names **TSLL ~$7.5B**, **NVDL ~$4.5B** (2025 snapshots); total leveraged ETF market ~**$170B+**. Concentration is **TSLA/NVDA**, not MU. — ETF.com Oct 2025 / May 2026 features. https://www.etf.com/sections/features/tesla-and-nvidia-drive-43-billion-boom-single-stock-etfs

C8 [PLAUSIBLE] (T3 sizing + owned market microstructure priors): On a **1%** day, 2× rebal ≈ **2% of fund AUM** (~$90M per $4.5B fund). NVDA ADV ~**130–160M sh** × ~$200+ ≈ **~$25–35B** dollar ADV; auction share **~9–15%** → **~$2.5–5B** auction notional. Typical-day single-stock LETF rebal is **low-single-digit % of close** / **≪1% ADV** for mega underlyings; only large-|r| days matter — when continuous liquidity provision and competition are highest. Index LETFs (e.g. TQQQ ~$30B+) dilute into full basket weights (NVDA ~high-single-digit % of NDX), so per-name flow is smaller than headline AUM suggests.

C9 [CONFIRMED as structural prior] (T2, Bessembinder et al. 2016 / sunshine-trading line): Around **large predictable** ETF liquidity demand (commodity roll analogy; theory general), markets show **narrower spreads, deeper book, more accounts providing liquidity** — not free predatory rent. Predictable LETF rebal is the equity analogue. — *Liquidity, resiliency and market quality around predictable trades*, JFE 2016.

C10 [CONFIRMED project-internal hard negative] (T1 ledger + brief): Intraday continuous **letf_window** payer detector already **EXHAUSTED-BY-US** (M3/M5, honest fills). Holdout concentration **MU ≫ TSLA≈0** conflicts with LETF-AUM ranking (TSLA complex largest). M11 name puzzle is **not** solved by LETF close-flow intensity.

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | PASS | Day’s r known by mid-afternoon; 15:55:10 decision still scheduled — but that does not create residual edge |
| 2 | Access | PASS | Would trade underlyings via retail MOC/LOC/taker same as champion |
| 3 | Session | PASS | Close-exit structure in-mission |
| 4 | Data | PASS (AUM+bars) / N-A for residual | Predicted flow from free/issuer AUM + owned bars is cheap; **residual test needs owned NOII already** — data not the blocker; **mechanism residual is** |
| 5 | Fill realism | PASS if auction; FAIL if continuous front-run | Pure continuous 15:30–15:55 front-run reopens M3/M5 continuous-fill death; auction-only expression collapses into champion |
| 6 | Statistics | PASS calendar, FAIL effect size | Daily events n≫250 easy; field prior mean residual **≲1 bp** << 20 bps noise → **underpowered for economic edge**, not for volume studies |
| 7 | Protocol | FAIL as new signal | Named payer exists classically, but is **already inside** champion’s price-insensitive MOC story; orthogonal LETF conditioner not pre-statable without double-counting. Charges a trial family that prior art + our kill of letf_window already tax |

**Survivor-profile score: 2 / 5**
1. Single-print/auction execution → **+1** (only if expression is pure auction; continuous re-hedge fails this)
2. Scheduled decision instant → **+1** (r known early; 15:55 still scheduled)
3. Named price-insensitive payer → **0** for *new* cell (payer is real but **already the champion’s class**; residual after anticipation not named as free)
4. Historically testable on owned / ≤$100 data → **+0** net (testable at $0 as *alignment of predicted flow with basis*, but that tests explanation, not promotion)
5. Expected effect ≥2× cost → **0** (field: ≲1 bp mean late-day amplification; front-run post-cost null)

### Economics sketch
- **Expected gross (field):** Ivanov–Lenkey-style late-day attribution **≲1 bp** mean for typical stock after flows; Brøgger-scale ~**6 bps** impact vs half-spread on VIX products; Shum-era **gross** afternoon front-run was crisis-concentrated and **does not survive costs** in later samples. NO-COST-MODEL on 2006–2011 front-run anecdotes.
- **Our cost burden:** Same as champion for auction structure (taker entry + single-print exit). Continuous anticipatory trading adds full continuous spread/impact and re-enters dead M3 fill regime.
- **Net prior for *new residual*:** ≈ **0 to slightly negative** after costs. For *explanation* of champion: LETF MOC may be a **minor component** of megacap close imbalance on high-|r| days, not the dominant MU-specific driver.
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**. LETF residual as separate signal does not clear 2× cost; as conditioning, expected lift is unmotivated once near already prices known flow.

### Proposed next test (only if OPEN-TESTABLE)
**N/A under NOT-VIABLE-STRUCTURAL for promotion.** Optional **kill-only / mechanism-map** (does not charge a promotion family if pre-registered as adversarial falsification):

- **Hypothesis (kill):** Cross-sectional rank of predicted LETF rebal intensity (Σ (L²−L)·AUM·r over funds referencing name) does **not** predict residual 15:55:10→cross bps after controlling for |near−mid|, and does **not** match alive/dead (MU vs TSLA).
- **Payer claimed:** none new; test is whether LETF flow is already in near.
- **Data:** owned NOII + bars; AUM from free issuer/ETF.com/SEC N-PORT (quarterly lag OK for rank study).
- **Universe:** M11 + core names with any linked single-stock or material index-weight LETF.
- **Expected n:** ≥250 sessions easy.
- **A-priori kill:** partial corr of predicted flow with residual PnL insignificant; rank correlation with holdout/name economics opposite of LETF-AUM ordering.
- **Promotion:** never from this cell alone.
- **Trial family:** adversarial DR-X1 kill / mechanism map; do not open a LETF-conditioning promotion family unless another modality returns OPEN-TESTABLE with residual orthogonal to near.

### Sources
1. **[T2]** Lenkey, S.L. (2024-12-23). *The market impact of leveraged ETFs: A Survey of the literature.* Quantitative Finance and Economics 8(4):815–840. https://www.aimspress.com/article/doi/10.3934/QFE.2024031 — synthesis: economic insignificance; no profitable front-run; broker pre-hedge of MOC; close-volume rise mitigates impact.
2. **[T2]** Ivanov, I.T. & Lenkey, S.L. (2018). *Do leveraged ETFs really amplify late-day returns and volatility?* Journal of Financial Markets 41:36–56. https://ideas.repec.org/a/eee/finmar/v41y2018icp36-56.html — flows cut rebal; ≲0.9 bps late-day return attribution.
3. **[T2]** Shum, P., Hejazi, W., Haryanto, E., Rodier, A. (2016). *Intraday share price volatility and leveraged ETF rebalancing.* Review of Finance 20:2379–2409. (SSRN 2012 WP abstract_id=2161057) — crisis-era vol association; front-run profitability contested after costs.
4. **[T3]** CXO Advisory (2012-11-19). *Front-running Leveraged ETFs at the End of the Day?* https://www.cxoadvisory.com/volatility-effects/front-running-leveraged-etfs-at-the-end-of-the-day/ — 0.60% gross/trade 2006–2011; stress-concentrated; NO-COST-MODEL.
5. **[T2]** Brøgger, S. (2021). *The market impact of predictable flows: evidence from leveraged VIX products.* Journal of Banking & Finance 133:106280. — impact declines over time; ~5.9 bps vs half-spread.
6. **[T2]** Cheng, M. & Madhavan, A. (2009). *The dynamics of leveraged and inverse exchange-traded funds.* Journal of Investment Management. — rebal formula A·x(x−1)·r; early MOC % stress scenarios.
7. **[T2]** Tuzun, T. (2013/2014 FEDS). *Are Leveraged and Inverse ETFs the New Portfolio Insurers?* Federal Reserve Board. https://www.federalreserve.gov/econres/feds/are-leveraged-and-inverse-etfs-the-new-portfolio-insurers.htm — early systemic concern; sample ≤2011; later work fails to confirm economic size.
8. **[T2]** Barbon, A., Beckmeyer, H., Buraschi, A., Moerke, M. (2021/2022 WP). *Liquidity Provision to Leveraged ETFs and Equity Options Rebalancing Flows.* https://wp.lancs.ac.uk/fofi2022/files/2022/08/FoFI-2022-027-Mathis-Moerke.pdf — swap-counterparty end-of-day concentration; last-window only for LETF.
9. **[T2]** Bessembinder, H., Carrion, A., Tuttle, L., Venkataraman, K. (2016). *Liquidity, resiliency and market quality around predictable trades.* Journal of Financial Economics 121:142–166. — sunshine liquidity to predictable ETF demand.
10. **[T3]** ETF.com (2025-10-14; 2026-05-20). Single-stock / leveraged AUM features (TSLL, NVDL, ~$31–43B single-stock class; TQQQ ~$31B). https://www.etf.com/sections/features/tesla-and-nvidia-drive-43-billion-boom-single-stock-etfs ; https://www.etf.com/sections/news/nvdl-returned-172-one-year-new-era-leveraged-etfs-working
11. **[T3]** Bogousslavsky & Muravyev (2023) as cited in Lenkey — close auction share rise 3.1%→7.5% (2010–2018); liquidity providers migrate to close.
12. **[T1 project]** AGENT_BRIEF.md / EXHAUSTION_MAP.md — letf_window EXHAUSTED-BY-US; holdout MU vs TSLA≈0; champion near−mid at 15:55:10.

#### Queries used
- LETF rebalance front-running close auction post-2012
- leveraged ETF rebalancing end of day volume impact academic paper
- single stock LETF AUM 2024 2025 TSLQ NVDL TSLR rebalance close
- LETF rebalance executed MOC vs continuous market closing auction
- "leveraged ETF" rebalancing anticipatory trading close price impounded
- Shum Hejazi Haryanto Rodier 2016 leveraged ETF rebalancing profit front run
- Brogger 2021 leveraged ETF rebalancing price impact declined
- LETF rebalancing swap counterparty total return swap not MOC equity
- single stock leveraged ETF AUM NVDL TSLL vs NVDA TSLA ADV volume rebalance size
- Cheng Madhavan 2009 leveraged ETF rebalancing formula exposure AUM
- Lenkey 2018 Do leveraged ETFs really amplify late-day returns capital flows
- "swap counterparty" leveraged ETF rebalance last 15 minutes continuous trading
- Tuzun 2014 leveraged ETF rebalancing destabilizing financial stocks FEDS
- NVDA TSLA closing auction volume percent of ADV 2024 2025
- Bessembinder predictable ETF order flows market quality 2015 2016 liquidity around predictable trades
- single stock LETF rebalance notional formula 2x AUM times return exposure hedge size
