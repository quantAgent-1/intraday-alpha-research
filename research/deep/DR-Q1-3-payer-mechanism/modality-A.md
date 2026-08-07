## DR-Q1-3 — A academic findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence **MED**) — Peer-reviewed and SSRN q-fin evidence (2010–2021 samples) identifies price-insensitive **indexed MOC / passive-benchmarked flow** as the dominant closing-cross payer class, with auction volume and close-price deviations scaling cross-sectionally and permanently with ETF/passive ownership and index membership; active-fund ownership does not. The literature does **not** resolve within-megacap **name selectivity** (why NVDA lives, GOOGL dies under the same frozen rule) via volatility — consistent with M11 — but supplies a pre-registrable prediction of the form basis-persistence ∝ f(index weight, passive share, auction share of ADV) that is testable on owned NOII + free/cheap passive proxies. Academic average large-stock |auction−4pm-mid| is only ~2.7 bps (gross, NO-COST-MODEL for retail taker), so the harvestable near-vs-mid basis at 15:55:10 is a related but distinct object; late-window (15:55–16:00) literature shows imbalance informativeness rises into the MOC/LOC freeze with weak price-discovery contribution from the auction print itself on large names.

What would flip it: A clean cross-sectional null that our 15:55:10 near−mid basis persistence / directional hit-rate is **orthogonal** to index weight, summed major-ETF ownership, and auction share of ADV on the 33 names (after pre-registered controls) would push toward EXHAUSTED-BY-FIELD on the passive-scaling mechanism as an explanation of name selectivity.

### Mechanism
**Who pays:** Closing-auction volume is primarily uninformed / liquidity-driven. Load-bearing classes with academic size evidence:

| Class | Price-insensitive? | Evidence of size / association |
|---|---|---|
| Index-tracker + passive MF MOC | **Yes** — minimize tracking error vs official close / NAV | ETF ownership strongly predicts auction turnover; passive MF coef ~0.037; active MF ≈0 or negative (B&M 2010–2018). Auction share of ADV rose 3.1%→7.5% aggregate as passive grew. |
| Index rebalance / inclusion flow | **Yes** — mechanical at recon effective date | Russell recon: auction turnover +230%, pre-close +78%, intraday only +7.8%. S&P 500 addition: permanent +20% auction-to-intraday volume; deletion −15% (B&M published version). Chinco–Sammon: ~83% of recon-day volume at/after close; implied true passive share ~33% of US market (2021). |
| Month-end / quarter-end institutional rebal | **Yes** — report & benchmark at month-end closes | Auction turnover +87% last day of month; +60% option-expiration days (delta-hedge unwind). |
| Option delta-hedgers | Partially (expire-at-close pins / unwind) | Auction +60% on option expiration Fridays. |
| ETF create/redeem → AP stock MOC | Indirectly yes | Jegadeesh–Wu: ETF arb / create-redeem activity significantly related to constituent closing-auction volume. |
| Active MF, earnings-informed, retail on-close | No / not primary | Active ownership raises *intraday/pre-close* not auction; auction flat or lower around earnings (B&M). Retail share of cross not quantified in T2. |
| Buyback programs close-benchmarked | Plausible, thin T2 | Not cleanly isolated in reviewed papers. |
| Close-benchmarked institutional algos (non-index) | Mixed | Month-end / reporting motives partially covered under institutional rebal. |

**Why flow is price-insensitive:** Official closing prices set NAVs, index levels, performance benchmarks, and many derivative settlements. Passive managers and AP-driven stock legs submit MOC/LOC to hit the print regardless of indicative near price within normal ranges; Chinco–Sammon document prearranged recon trades executed at whatever the close is.

**Why it persists:** Structural growth of passive AUM; listing-venue monopoly on official close; exchange fees + execution uncertainty deter external liquidity providers from fully offsetting imbalance (B&M segmentation hypothesis; half of large-stock reversal occurs in first 20–40 min after-hours). Deviations reverse ~85% overnight (large stocks complete), so the pressure is temporary — consistent with a liquidity-payer story rather than information.

**Capacity intuition:** Aggregate US closing auction ~$15B/day (2018 B&M); large-stock |dev| mean ~2.7 bps; our $10k notional is negligible vs name-level auction size. Name selectivity must come from *relative* forced-flow intensity vs continuous-market depth / adverse-selection (not raw vol).

**Who plausibly pays the near-vs-mid basis we harvest:** Indexed MOC and other price-insensitive on-close interest that has already entered by ~15:55, so the NOII near price (on-close + continuous book) diverges from continuous mid; liquidity providers / discretionary offsetters who wait for the freeze or who only partially offset before 16:00 leave residual basis that reverts into the cross or overnight. Academic object is mostly auction-price vs 4pm mid; our object is near vs mid at 15:55:10 — same payer class, earlier measurement.

### Claims
C1 [CONFIRMED] (T2, Dec 2020 / JFM 2023, sample 2010–2018 TAQ common stocks >$5, mcap >$100M): Aggregate closing-auction share of daily dollar volume rose from 3.11% (2010) to 7.48% (2018); average stock-day auction share ≈5.7% of ADV; last-five-minutes volume exceeds prior 25 minutes — **Bogousslavsky & Muravyev, "Who Trades at the Close?", J. Financial Markets 2023 / AEA 2020 draft**, https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840

C2 [CONFIRMED] (T2, same sample): ETF ownership and **passive** mutual-fund ownership strongly predict auction turnover; **active** mutual-fund ownership does not (point estimate near zero/negative). ETF turnover-elasticity spikes at the auction (~5× the 15:30–15:35 elasticity); passive elasticity is flat pre-close and spikes only in the auction. DiD vs active ownership supports causal interpretation — B&M 2020/2023.

C3 [CONFIRMED] (T2, same + published abstract): Auction-to-intraday volume **permanently** rises ~20% after S&P 500 **addition** and falls ~15% after **deletion** (relative to controls), linking index membership to sustained close-flow intensity beyond event day — B&M JFM 2023 abstract/body (ScienceDirect summary).

C4 [CONFIRMED] (T2, 2010–2018): Mean absolute auction-price deviation from 4pm midquote = **8.12 bps** full sample, **2.66 bps** large-cap quintile, **20.6 bps** small-cap; 85% of deviation reverses by next-morning 9:45 mid (large stocks ~complete); auction contributes little weighted price discovery vs continuous intervals with similar volume; higher auction turnover → larger deviations (~0.88 bps per 1% turnover) — B&M. **NO-COST-MODEL** for retail taker path; unit = per stock-day, gross.

C5 [CONFIRMED] (T2, calendar): Auction turnover +230% on Russell rebalancing days, +87% month-end, +60% option-expiration; ~flat around earnings (while intraday rises) — B&M. Confirms price-insensitive calendar payers vs informed.

C6 [CONFIRMED] (T2, 1997–1998 Russell 1000 TAQ + NYSE MOC imbalance indications): Last 5 minutes explain ~18% of portfolio daily-return variation (~1.3% of trade time); MOC imbalance publications predict overnight reversals (temporary price pressure from institutional liquidity trading), stronger on index-expiration days — **Cushing & Madhavan, "Stock returns and trading at the close", J. Financial Markets 2000**, https://www.chesler.us/resources/academia/trading_at_the_close.pdf. **DECAY-UNKNOWN** for post-2000 microstructure; unit = per day / overnight, gross.

C7 [CONFIRMED] (T2, 2010–2020 / JFE 2022): Closing auction ~10% ADV by 2019; Nasdaq price impact ~58% larger than NYSE; temporary component ~85% Nasdaq / ~62% NYSE, fully reverses in 3–5 days; ETF arb and create/redeem activity significantly related to constituent auction volume — **Jegadeesh & Wu, "Closing auctions: Nasdaq versus NYSE", JFE 2022**. **NO-COST-MODEL** for our structure; unit = per-event price impact vs size.

C8 [CONFIRMED] (T2, recon volumes 2000–2021): True passive-ownership share of US market ≈ **33.3%** in 2021 (vs ~16% formal index-fund holdings); recon-day volume concentrated at/after close (e.g. 83.6% for YETI Russell add); methodology: AUM_indexed ≈ recon_day_close_volume × price / index_weight — **Chinco & Sammon, "The Passive-Ownership Share Is Double What You Think It Is", 2023**, https://www.hbs.edu/ris/Publication%20Files/double-what-you-think-it-is%20may%2023_3c1ae213-5aec-407d-b656-13e3822f0b8b.pdf.

C9 [CONFIRMED] (T1, exchange): Nasdaq NOII: begins **15:50** ET; **every 10 seconds** 15:50–15:55 (EOII / subset: reference, paired, imbalance); **every 1 second** 15:55–16:00 with **Near** (on-close + continuous) and **Far** (on-close only) indicative clearing prices — Nasdaq Closing Cross FAQ / Rule 4754; BMLL 2025 confirms same cadence. Aligns with owned data: near/far ≈0 until ~15:55.

C10 [PLAUSIBLE] (T2/T3, MSc 2020 + B&M DiD): Late-window imbalance → forward return predictability **increases** approaching Nasdaq MOC (15:55) / LOC (15:58) cutoffs for S&P names on Nasdaq; model captures ~30% of spread in thesis sample; B&M DiD finds imbalance-info WPC lift at dissemination start is economically small for **large** stocks (~0.5% WPC), larger for small — **Morand, Imperial College MSc 2020**, https://www.imperial.ac.uk/media/imperial-college/faculty-of-natural-sciences/department-of-mathematics/math-finance/MORAND_CLEA_01805978.pdf; B&M §3.3. Unit: per-minute forward return / WPC; thesis cost treatment informal.

### Constraint gates
| Gate | Result | Clause |
|---|---|---|
| 1. Latency | **PASS** | Decision instant scheduled (15:55:10); 5–25 s manual pre-positionable before cross. |
| 2. Access | **PASS** | MOC/LOC / taker-to-cross path already in champion; retail brokers offer CLS/MOC with known cutoffs (not re-derived). |
| 3. Session | **PASS** | Flat AT 16:00 cross via on-close exit; RTH. |
| 4. Data | **PASS / partial-block** | Mechanism test uses **owned** NOII + realized cross; index weights / passive % series are the residual gap — free/cheap paths exist (ETF daily holdings, Wayback, CRSP-free proxies) at ≤$100 one-time (see charge Q3; academic free B&M auction panel 2010–2018 is supplementary). |
| 5. Fill realism | **PASS** | Auction single-print exit; no continuous-maker assumption. |
| 6. Statistics | **PASS** | 33 names × multi-year sessions ≫ Stage-A n≥250; ~20 bps/event noise requires mean ≥~4–5 bps for power or meta-filter. |
| 7. Protocol | **PASS** | Named payer (indexed MOC) a priori; pre-registrable cross-section: basis-persistence ∝ f(index weight, passive share, auction/ADV); charges a new trial family under close-auction / payer-decomposition. |

**Survivor-profile score: 5/5**
1. Single-print/auction execution — yes.
2. Scheduled decision instant — yes.
3. Named price-insensitive payer — yes (indexed MOC / passive).
4. Historically testable on owned or ≤$100 data — yes (owned NOII; passive series ≤$100).
5. Expected effect ≥2× cost at our size — champion already clears; academic gross large-name deviations small but our near-mid object and holdout (+12.5) already passed.

### Economics sketch
- **Academic gross (related object):** large-stock |auction − 4pm mid| mean ~2.7 bps; full-sample 8.1 bps; ~85% overnight reversal (B&M, per stock-day, NO-COST-MODEL). Jegadeesh–Wu: temporary impact dominates and reverses 3–5 days; Nasdaq impact > NYSE.
- **Our structure cost burden:** taker entry into continuous (spread + fee) then exit at single cross print; champion dev **+2.5 bps/event**, holdout **+12.5 bps/event [6.9, 18.5]** on sealed n=140 — already net of that burden in ledgered tests.
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**. Academic work explains *why a payer exists* and *that volume scales with passive/index*, not the per-event economics of the 15:55:10 near−mid rule. For name selection, if basis-persistence scales with passive share, expected gross should concentrate in high-passive / high-auction-share names (NVDA-class) vs low (hypothesis for GOOGL-class) — that is the test, not a new edge claim.

### Proposed next test (OPEN-TESTABLE)
**Hypothesis:** Within the 33 Nasdaq names, cross-sectional and time-series variation in **15:55:10 near−mid basis magnitude, directional hit-rate, and net bps/event** is increasing in (a) contemporaneous index weight (NDX-100 and/or SPX), (b) % passively held (or defensible proxy: sum of QQQ/IVV/VOO/SPY/VTI/IWM etc. holdings), (c) auction share of ADV — after controlling for ADV, spread, and realized vol. **Not** explained by vol tercile (M11 already killed pure-vol).

**Named payer:** Index-tracker MOC + passive MF NAV-driven MOC + AP create/redeem stock legs + month-end rebal (price-insensitive at the listing-venue close).

**Data needed:**
- **Owned:** Databento NOII + realized cross price/size 2020–2026 (5 deep + 28 M11).
- **To acquire (≤$100 or free):** point-in-time NDX-100 / SPX weights 2020–2026 (quarterly OK); per-name passive % or ETF-holdings sum archive. Academic free artifact: B&M auction volume/deviation panel 2010–2018 (Dropbox via bogousslavsky.github.io) for external validation of auction-share construction only.

**Universe:** 33 Nasdaq names in champion/M11 set.

**Expected n & power:** ~33 × ~750 sessions ≈ 20k+ name-days; filter |basis|≥10 bps → thousands of events; against ~20 bps/event noise, detectable slope if high-passive tercile mean exceeds low by ≥3–4 bps.

**A-priori thresholds:** Pre-register (i) rank-IC of passive/index/auction-share features vs next-event net bps > 0.05, (ii) high-tercile dir ≥0.55 and net ≥ +2 bps/event, (iii) low-tercile net ≤ 0 — all OOS on a held calendar block or leave-one-sector-out.

**Promotion rule:** Pass thresholds + sign-stable in ≥4/6 sectors → promote to forward-paper (M10) as a **name filter** on the frozen champion rule (not a new entry rule).

**Kill criteria:** Rank-IC ≤0 or high-tercile net ≤ low-tercile net on OOS → mechanism fails to explain name selectivity; return EXHAUSTED-BY-FIELD for passive-scaling as name filter (payer narrative for the champion structure remains intact from wave-1 + this literature).

**Trial family charged:** Close-auction payer decomposition / passive-ownership scaling (new family under DR-Q1-3; does not re-open dead intraday or daily families).

### Sources
1. **[T2]** Bogousslavsky, V. & Muravyev, D. (2020 draft / 2023 JFM). *Who Trades at the Close? Implications for Price Discovery and Liquidity.* Sample 2010–2018. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840 ; AEA PDF https://www.aeaweb.org/conference/2021/preliminary/paper/H9T4hef7 ; data https://bogousslavsky.github.io/data/
2. **[T2]** Cushing, D. & Madhavan, A. (2000). *Stock returns and trading at the close.* J. Financial Markets. Sample Jun 1997–Jul 1998 Russell 1000. https://www.chesler.us/resources/academia/trading_at_the_close.pdf
3. **[T2]** Jegadeesh, N. & Wu, Y. (2022). *Closing auctions: Nasdaq versus NYSE.* JFE 143:1120–1139. Sample ~2010–2020. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3732955
4. **[T2]** Chinco, A. & Sammon, M. (2023). *The Passive-Ownership Share Is Double What You Think It Is.* Sample recon 2000–2021. https://www.hbs.edu/ris/Publication%20Files/double-what-you-think-it-is%20may%2023_3c1ae213-5aec-407d-b656-13e3822f0b8b.pdf
5. **[T2]** Wu, Y. (2019). *Closing Auction, Passive Investing, and Stock Prices.* SSRN. Abstract/secondary cites only for full text path issues. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3440239
6. **[T2/T3]** Morand, C. (2020). *Predicting US stock returns using closing auction imbalance data.* Imperial College MSc. https://www.imperial.ac.uk/media/imperial-college/faculty-of-natural-sciences/department-of-mathematics/math-finance/MORAND_CLEA_01805978.pdf
7. **[T1]** Nasdaq. *Nasdaq Closing Cross FAQ.* NOII cadence 10s then 1s; Near/Far definitions. https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf
8. **[T1]** Nasdaq Rule 4754 / SR filings (EOII 10s from 15:50; full NOII 1s from 15:55). e.g. https://www.sec.gov/files/rules/sro/nasdaq/2020/34-89334-ex5.pdf
9. **[T3]** BMLL (2025). *Into the Close: Unpacking U.S. Closing Auction Dynamics…* Confirms cadence; Russell recon auction share. https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution
10. **[T2]** Goyal, A. et al. / related (JFQA path). *Price Impact in Closing Auctions…* Square-root impact; closing auctions cheaper than continuous for non-microcaps; sample 2012–2021. Secondary cite via Cambridge.
11. **[T2]** De Rossi, G. & Steliaros, M. (2022). Passive/ETF ownership and near-close volatility (cited: +2.99% relative vol near close for +2 SD ETF ownership). Secondary.
12. **[T2]** Hu, E. & Murphy, D. (2020/2025). *Vestigial Tails? Floor Brokers at the Close…* NYSE D-Quotes vs Nasdaq; imbalance accuracy. Secondary via B&M cites / Management Science 2025.

#### Queries used
1. Bogousslavsky Muravyev "Who Trades at the Close" closing auction
2. Cushing Madhavan stock returns to the close auction MOC
3. closing auction price discovery passive ownership index MOC flow 2020..2026 site:ssrn.com OR site:arxiv.org
4. Nasdaq closing cross imbalance predictability NOII price discovery academic paper
5. "Closing Auction" "Passive Investing" stock prices SSRN index funds MOC
6. index inclusion closing auction volume passive ownership price pressure academic 2015..2026
7. arXiv closing auction imbalance ETF indexing "market on close" equity
8. Jegadeesh Wu closing auctions Nasdaq versus NYSE price impact sample period findings
9. Wu Jegadeesh "Closing auctions" Information content SSRN
10. "Closing Auction, Passive Investing, and Stock Prices" Wu SSRN abstract findings
11. S&P 500 addition auction volume permanent increase Bogousslavsky ETF ownership
12. Hu Murphy auction order imbalance information NYSE Nasdaq quality 2020
13. Smith Nasdaq electronic closing cross empirical analysis NOII 2006
14. Nasdaq NOII disseminate every 10 seconds 3:50 3:55 every second near far indicative closing cross
15. "auction-to-intraday volume" S&P 500 addition permanent Bogousslavsky OR Muravyev
16. site:papers.ssrn.com closing auction passive ownership index weight MOC volume cross-section
17. The passive ownership share is double Chinco Sammon reconstitution closing auction
