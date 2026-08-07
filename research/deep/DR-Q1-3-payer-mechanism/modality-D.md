## DR-Q1-3 — D adversarial findings
### Verdict recommendation
**EXHAUSTED-BY-FIELD (MED)** for the load-bearing sub-hypothesis that passive/index ownership or index weight *scales* close-auction basis edge in a name-selection sense for liquid Nasdaq names; **OPEN residual only as already-known champion (not a new scaling story)**. Two independent T2/T3 lines kill naive ownership-scaling: (1) ITG 2012 — continuous prices react to the *first* imbalance print within seconds and average subsequent returns ≈ 0 even for large imbalances, so post-announcement imbalance-following is not profitable; (2) Bogousslavsky–Muravyev (sample 2010–2018; JFM 2023) — large-cap mean |auction−4pm mid| ≈ **2.66 bps**, 68% of closes match pre-close bid/ask, and S&P-add/delete volume shocks do **not** produce abnormal residuals once turnover is controlled (auction absorbs indexed flow). Add NYSE 2022: ~**23%** of closing-price volume is internalized off-exchange and **invisible** to NOII — visible imbalance is a censored proxy for "who pays." NVDA (and holdout MU concentration) is a tournament-winner threat until multi-name pre-registered power settles M10/M11; M11 already shows high-vol LRCX/AVGO/NFLX dead while NVDA lives — not a vol story, consistent with selection.

What would flip it: A pre-registered panel where passive ownership / index weight *linearly* predicts |near−mid|≥10 bps event rate **or** bps/event **after** ADV/spread/vol controls, with edge surviving in bottom-half passive-weight names (not just mega-tech), n≥250, net ≥+5 bps/event — *and* that panel surviving after excluding the post-hoc winners (NVDA/MU).

### Mechanism
**Adversarial mechanism (why passive scaling fails as a predictor):**

1. **Upstream netting/internalization:** Broker-dealers pre-match client MOC off-exchange (~23% of closing-price volume, NYSE S&P1500 Mar–Sep 2022; similar rates claimed for other listings). Pre-matched interest never enters the auction book and is absent from paired/imbalance quantities. Visible NOII is a *residual after internalization*, not the full passive demand shock. Ownership stock does not map 1:1 to visible imbalance flow.

2. **Depth absorption + early price reaction:** Predicted passive/rebalance flow is anticipated. Continuous quotes reprice at first NOII (ITG: reaction within seconds; post-print drift ≈ 0). Close LPs (Optiver and peers; public Kaggle "Trading at the Close"; IO/offset interest) compete to absorb residual imbalance between 15:50–16:00. By 15:55:10, any remaining |near−mid| in liquid names is either (i) half-spread/tick artifact, (ii) adverse-selection tail, or (iii) rare one-sided rebalance day — not a smooth function of index weight.

3. **LP arbitrage of weight/ownership scaling:** Large-cap auctions are the *most* watched (Greenwich/industry: imbalance feeds standard). Mean large-cap |deviation| ~2.7 bps is below our 10 bps gate; conditioning on ≥10 bps selects the right tail of an already-arbed distribution. Jegadeesh–Wu document imbalance *declining* from first print to close — the predictable component is harvested in continuous/IO competition. Published reversal strategies (Wu–Jegadeesh multi-day MOC-imbalance) are a different trade (overnight/multi-day, not 15:55:10→cross) and face standard post-publication decay risk (DECAY-UNKNOWN post-2020 for that specific alpha).

4. **Tournament-winner critique of NVDA:** Edge concentration (brief: MU +52 bps carried holdout; GOOGL/TSLA ≈ 0; M11 NVDA alive / LRCX·AVGO·NFLX dead) is the textbook selection pattern: name picked after seeing results. Field anomalies routinely fail this test (McLean–Pontiff / Chordia–Subrahmanyam–Tong attenuation). Without pre-registered multi-name promotion rules, "NVDA works" is not evidence that passive weight is the scaler.

**Who still might pay (does not rescue scaling):** Price-insensitive indexed MOC that *misses* early internalization and arrives after continuous absorption has partially run — residual basis on *event days*, not a stock-level ownership beta. That is the champion's existing narrative, not a new DR-Q1-3 scaling claim.

### Claims
C1 [CONFIRMED] (T3, ITG/Bacidore et al. 2012-11-07, sample pre-2012 US equity closes): Prices react to the **initial** imbalance message within seconds; average return from first print to close is **not statistically different from zero** even for relatively large imbalances; closing prints tend to occur at the 4pm bid or offer (~0.5× spread median) regardless of imbalance size — imbalances predict *direction* of mid→close move but magnitude is already in the continuous book; "**this strategy is not profitable**" (post-announcement imbalance follow). — https://mrtopstep.com/wp-content/uploads/2024/02/ITG-Trading-Around-The-Close-11-7-2012-1-1.pdf

C2 [CONFIRMED] (T2, Bogousslavsky & Muravyev, J. Financial Markets 2023 / WP Jun 2021, sample Jan 2010–Dec 2018 US common stocks): Mean |auction−4pm mid| = **8.12 bps** full sample; **large-cap quintile mean 2.66 bps** (p50=1.73); closes match pre-close bid or ask in **68%** of cases; tick binding in **41.8%**; auction price impact lower than continuous; deviations reverse ~fully overnight (spread-adjusted reversal coeff ≈ −0.95 to −0.98). — https://doi.org/10.1016/j.finmar.2023.100852 ; PDF https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf

C3 [CONFIRMED] (T2, same BM sample/method): On S&P 500 add/delete days auction volume +~3000% vs baseline, absolute auction deviation +~21 bps raw — but deviation is **insignificant once controlling for turnover**; auction absorbs extreme indexed flow without abnormal residual given volume. Passive *flow shocks* do not leave free residual basis proportional to ownership. — same as C2 Table 9 / § rebalancing

C4 [CONFIRMED] (T1/T3, NYSE Data Insights 2022-11-17, sample Mar–Sep 2022 S&P 400/500/600): Broker-dealer **on-close internalization ≈ 23%** of total closing-price trading volume (TRF prints near close / (auction + TRF)); "similar internalization rates… for securities listed on other markets." Pre-matched interest is **excluded** from paired/imbalance feed quantities. High-internalization names show *higher* late price drift and auction slippage — visible NOII is censored and selectively informative. — https://www.nyse.com/data-insights/closing-auction-internalization-effect-throughout-imbalance-period

C5 [CONFIRMED] (T2, Goyal–Jegadeesh–Wu, JFQA 2026 / online, multi-year US): Closing-auction price impact is **lower** than continuous market for all stocks except Nasdaq microcaps; e.g. large NYSE 0.5% ADV impact ~**3.2 bps** auction vs ~6.4 bps continuous. Liquid-name depth absorbs institutional-size flow at the close. — https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/price-impact-in-closing-auctions-opening-auctions-and-continuous-markets-a-benchmark-for-cost-of-trading-on-anomalies/0F72910A79C5B42CF6E85F55164CE846

C6 [PLAUSIBLE] (T3, Morand MSc thesis Imperial 2020, sample Apr–Aug 2020 S&P/Russell, NO-COST-MODEL): After Nasdaq **15:55 MOC/LOC cutoff**, linear models of imbalance features on short-horizon *forward continuous* returns yield **R² ≈ 0** (only IO/offset liquidity remains); pre-15:55 some short-horizon predictability of continuous moves exists. Consistent with ITG: predictable continuous drift is early; post-cutoff residual is hard. (Note: champion structure is mid→*cross* via near, not continuous forward — still a hard negative for "imbalance momentum after 15:55.") — https://www.imperial.ac.uk/media/imperial-college/faculty-of-natural-sciences/department-of-mathematics/math-finance/MORAND_CLEA_01805978.pdf

C7 [CONFIRMED] (T2/T3, Jegadeesh & Wu JFE 2022 / WP, sample ~2010s): Temporary component of auction price impact dissipates over **3–5 days**; strategies exploiting impact *and multi-day reversals* claimed profitable in-sample. **Different trade** from 15:55:10 taker→cross (requires overnight — out of mission). Post-2020 OOS for that reversal alpha: **DECAY-UNKNOWN**. Imbalance declines from first dissemination to close (offset competition). — https://doi.org/10.1016/j.jfineco.2021.12.004

C8 [CONFIRMED] (T3, BMLL 2025-06-24, 2024 Russell reconstitution panel): Russell Day shows sharp auction volume, dislocation, and one-sided imbalance spikes — yet auction→next-open stability is **not** outsized (prices "highly stable"). Extreme passive rebalance flow is absorbed without persistent overnight dislocation in studied names. — https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

C9 [PLAUSIBLE as selection critique] (T3 internal + field pattern): Holdout concentration (MU carried; GOOGL/TSLA ~0) + M11 NVDA-alive / LRCX·AVGO·NFLX-dead is isomorphic to top-decile / tournament-winner traps already banned in §7 of AGENT_BRIEF. Field: Chordia–Subrahmanyam–Tong 2014 and McLean–Pontiff-style publication/attenuation — published microstructure anomalies decay under liquidity and competition. Claiming "passive weight explains NVDA" without pre-registered cross-name slope is circular.

C10 [CONFIRMED] (T3, Eastspring 2020s rebalance execution research; SSGA 2026 microstructure note): Closing auctions in developed markets with active LP participation **effectively absorb** large rebalancing flows; "close execution outperforms" alternative benchmarks in Europe/Japan panels — mechanism is matching passive with contra, not leaving systematic unarbed basis proportional to weight. — Eastspring rebalancing insights; SSGA "Closing time: How passive investing is reshaping equity market microstructure"

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | PASS | 15:55:10 remains scheduled; adversarial claim is about *edge existence*, not reaction speed |
| 2 | Access | PASS | Retail MOC/LOC/taker path unchanged |
| 3 | Session | PASS | Exit at cross in-mission |
| 4 | Data | PASS for residual basis; FAIL for ownership-scaler research | Owned NOII+SIP suffice for residual basis; clean passive-ownership / float-adjusted index-weight history at name-day grain for multi-year panel may need 13F/ETF holdings product — often >$100 unless free proxies (e.g. crude ETF AUM × weight) accepted as noisy |
| 5 | Fill realism | PASS | Single-print exit still clean; adversarial null is about gross mean→0 not fill model |
| 6 | Statistics | FAIL for ownership-scaling claim | Expected mean under absorption prior ≈ 0–3 bps large-cap residual; detecting ownership *slope* vs ~20 bps noise needs large n and is underpowered if true slope is near 0 |
| 7 | Protocol | FAIL for scaling; PASS for residual champion | Ownership-scaling was not a pre-registered family with a-priori thresholds; post-hoc NVDA/MU concentration charges multiple-testing. Residual basis champion already protocolled (M8–M11) |

**Survivor-profile score (for *passive-ownership scaling as filter*): 1 / 5**
1. Single-print/auction execution → **+1** (same structure)
2. Scheduled decision instant → **+1**
3. Named price-insensitive payer → **0** (payer is residual after internalization+LP; not "passive ownership stock")
4. Historically testable ≤$100 → **0** (clean ownership panel borderline; free proxies noisy)
5. Expected effect ≥2× cost → **0** (field prior large-cap residual ~2.7 bps mean abs; conditioned ≥10 bps tail may be adverse-selected; not ≥2× cost with confidence)

(Champion residual basis without ownership-scaling still scores 5/5 under Wave-1 — this modality does not re-kill the champion, only the scaling/decomposition extension.)

### Economics sketch
- **Field gross priors (adversarial):** large-cap mean |auction−mid| ≈ **2.7 bps** (C2); half-spread often explains most of that (68% at bid/ask). ITG: post-first-print drift ≈ **0**. Goyal–Jegadeesh–Wu: auction impact for 0.5% ADV large-cap order ~**3–7 bps** (venue-dependent) — *provider* rent scale, not retail residual.
- **Our cost burden:** taker entry (half-spread + impact) at 15:55:10 on liquid names ~1–5 bps typical; zero commission through 2026-12-31; exit free at cross print.
- **Net prior under adversarial view for ownership-scaled filter:** ≈ **0 to negative** after costs in liquid high-ownership names (most arbed). Conditioning |basis|≥10 bps may salvage a *rare-event* residual (champion path) but severs the link to passive *weight* as continuous scaler.
- **Comparison:** champion = **+2.5 bps/event dev / +12.5 holdout** — holdout concentration (MU) is exactly what the tournament critique flags; adversarial prior says forward mean regresses toward field ~few-bps residual, not holdout +12.5.

### Proposed next test (only if OPEN-TESTABLE)
**N/A under EXHAUSTED-BY-FIELD for ownership-scaling.** Optional *kill-only* confirmation (does not promote; adversarial falsification of residual champion, not a new family):

- **Hypothesis (kill residual, not scaling):** On M11 28-name panel, pooled 15:55:10 |near−mid|≥10 bps events deliver net **< +2 bps/event** OOS (or CI upper < +5), and/or edge is entirely in ≤2 names (concentration kill).
- **Payer claimed:** none new; test is existence/concentration.
- **Data:** owned Databento NOII + SIP (no new $).
- **Do not** spend budget on paid ownership panels solely to fit a weight slope — field already predicts null slope in liquid names.
- **Kill criteria:** n≥250; mean net < +2 bps or Herfindahl of dollar-PnL in top-2 names > 0.5.
- **Trial family:** adversarial DR-Q1-3 / M11 concentration audit — do **not** charge a promotion family for passive-weight filters.

### Sources
1. **[T3]** Bacidore, J., Berkow, K., Wong, J. (ITG), *Trading Around the Close*, 2012-11-07. https://mrtopstep.com/wp-content/uploads/2024/02/ITG-Trading-Around-The-Close-11-7-2012-1-1.pdf — post-first-imbalance drift ≈ 0; follow strategy not profitable.
2. **[T2]** Bogousslavsky, V. & Muravyev, D., *Who Trades at the Close? Implications for Price Discovery and Liquidity*, Journal of Financial Markets 2023 (WP Jun 2021). https://doi.org/10.1016/j.finmar.2023.100852 ; PDF above — large-cap |dev| 2.66 bps; 68% at bid/ask; S&P rebal absorption.
3. **[T1/T3]** NYSE (Choey Li), *Closing Auction: Internalization effect throughout imbalance period*, 2022-11-17. https://www.nyse.com/data-insights/closing-auction-internalization-effect-throughout-imbalance-period — ~23% closing-price volume internalized; invisible to NOII.
4. **[T2]** Goyal, A., Jegadeesh, N. & Wu, Y., *Price Impact in Closing Auctions, Opening Auctions, and Continuous Markets…*, JFQA 2026. https://doi.org/10.1017/S0022109026102592 — auction impact < continuous for non-microcaps.
5. **[T2]** Jegadeesh, N. & Wu, Y., *Closing auctions: Nasdaq versus NYSE*, Journal of Financial Economics 2022. https://doi.org/10.1016/j.jfineco.2021.12.004 — 3–5 d temporary impact; multi-day reversal strategies in-sample; imbalance declines to close.
6. **[T3]** Morand, C., *Predicting US stock returns using closing auction imbalance data*, Imperial College MSc thesis, 2020. https://www.imperial.ac.uk/media/imperial-college/faculty-of-natural-sciences/department-of-mathematics/math-finance/MORAND_CLEA_01805978.pdf — post-15:55 R²≈0 for continuous forward returns from imbalance.
7. **[T3]** BMLL (Laible & Thakur), *Into the Close… Russell Reconstitution*, 2025-06-24. https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution — Russell Day absorption / next-open stable.
8. **[T3]** Eastspring Investments, *Navigating index rebalancing effects*. https://www.eastspring.com/insights/deep-dives/navigating-index-rebalancing-effects-key-insights-for-smarter-execution — auctions absorb rebalance flows in developed markets.
9. **[T3]** SSGA, *Closing time: How passive investing is reshaping equity market microstructure*, 2026-01-23. https://www.ssga.com/is/en_gb/institutional/insights/how-passive-investing-reshaping-microstructure — close as LP focal point; predictable contra.
10. **[T1]** Nasdaq Trader, Opening and Closing Crosses / NOII schedule. https://www.nasdaqtrader.com/trader.aspx?id=openclose ; Closing Cross FAQ. https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf — 15:50 NOII; 15:55 MOC cutoff; 15:55–16:00 1s cadence + near/far.
11. **[T2]** Hu, E. & Murphy, D., *Vestigial Tails? Floor Brokers at the Close…*, Management Science 2025 (WP 2020). https://doi.org/10.1287/mnsc.2023.00884 — NYSE late flexibility → more reversals vs Nasdaq efficiency; Nasdaq residual harder to harvest.
12. **[T2/T3]** Chordia, T., Subrahmanyam, A. & Tong, Q., *Have capital market anomalies attenuated…*, JAE 2014; McLean–Pontiff publication-decay line — general attenuation prior for published anomalies.
13. **[T3]** Optiver / Kaggle, *Optiver - Trading at the Close* competition 2023. https://www.kaggle.com/competitions/optiver-trading-at-the-close — public signal that prop LPs model close auction microstructure at industrial scale.
14. **[T3]** NYSE, *The NYSE Significant Imbalance…*, 2024-11-04. https://www.nyse.com/data-insights/the-nyse-significant-imbalance-enhanced-trading-opportunities-at-the-nyse-closing-auction — exchange actively flags LP opportunities at 15:50.

#### Queries used
- close auction imbalance trading strategy failure decay post-2020
- closing auction arbitrage liquidity providers absorb index rebalancing flow
- passive ownership index MOC flow does not predict closing price impact academic paper
- NOII closing cross trading edge decay Nasdaq auction market makers
- Wu Jegadeesh Closing auctions information content timeliness price reaction profitability
- Bogousslavsky Muravyev Who Trades at the Close auction deviation reverse
- "Trading Around the Close" imbalance message price reaction not profitable
- Optiver trading at the close competition NOII feature importance decay overcrowding
- index fund MOC netting internalization pre-trade matching reduces closing auction impact
- closing auction price impact liquid large cap stocks small basis points Nasdaq absorption
- anomaly decay publication effect closing auction imbalance strategy post 2020
- Mayhew McCormick Spatt information content market-on-close imbalances specialist
- Nasdaq large cap closing auction deviation midquote 2-3 bps liquid stocks
- Hu Murphy closing auction Nasdaq NYSE imbalance accuracy price discovery 2020
