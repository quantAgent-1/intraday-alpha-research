## DR-Q16 — A academic findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence MED) — Academic literature strongly supports that closing-period returns carry a **common institutional / passive-flow factor** (portfolio-level variance share ≫ single-name), that auction price deviations reverse, and that **cross-sectional long/short imbalance books** can be profitable at multi-day horizons; but **no peer-reviewed paper delivers a same-session market-neutral closing-auction basis book** that isolates residual alpha while cutting ~20 bps per-event noise. The variance-reduction framing is therefore **statistically coherent and free to test on owned NOII+SIP**, yet **structurally constrained for deploy** at $1k–$10k (capital split long+short, multi-leg manual latency, rare same-day opposite signals). It is a residualization / power tool on the champion, not a new payer-family.

What would flip it: a pre-registered residualization on owned history showing that SPY/QQQ/SMH (or equal-weight opposite-imbalance basket) 15:55:10→16:00 returns explain **R² ≥ 0.35–0.40 of per-event champion PnL variance while preserving mean ≥ +2 bps**, with residual n ≥ 250.

### Mechanism
- **Who pays the champion mean (unchanged by hedging):** price-insensitive indexed MOC / passive rebalance / ETF create-redeem flow that pushes the indicative near away from continuous mid; liquidity providers and discretionary traders absorb it into the 16:00 cross. Academic consensus (Bogousslavsky–Muravyev; Jegadeesh–Wu; Cushing–Madhavan; Wu passive-flow paper) identifies passive/index demand as the structural closer of auction volume and temporary price pressure.
- **What a hedge would remove:** the **common component** of 15:55→16:00 returns (market/sector beta, correlated auction deviations across names). Cushing–Madhavan show the last five minutes explain ~18% of **portfolio** daily-return variance vs ~4% for single names — evidence of a common immediacy factor. Bogousslavsky–Muravyev document auction deviations are highly cross-sectionally correlated yet small in aggregate, so diversified / index-hedged books shrink market exposure without eliminating stock-specific auction noise.
- **Why it may persist as a variance tool:** residualization does not require a new payer; it is portfolio construction. Persistence of the mean still rests on passive MOC price-insensitivity. Capacity of the **hedge leg** is high (index ETFs); capacity of the **alpha leg** remains the single-name basis capacity.
- **No coherent new payer** for “market-neutral close books” as a standalone edge: published L/S imbalance profits are largely multi-day reversals of temporary impact (out-of-mission overnight), not same-print residual capture.

### Claims
C1 [CONFIRMED] (T2, 2021/2023 pub, sample 2010–2018): Closing auction absolute price deviation (log auction vs 4pm mid) averages **8.1 bps** (large-cap ~**2.66 bps**, small ~**20.6 bps**); auction price matches pre-close bid or ask in **68.5%** of cases; deviations reverse almost fully overnight and are highly cross-sectionally correlated — implying a hedgeable common component and limited auction price discovery. — Bogousslavsky & Muravyev, *J. Financial Markets* 2023 / WP 2021, https://ssrn.com/abstract=3485840 ; https://doi.org/10.1016/j.finmar.2023.100852

C2 [CONFIRMED] (T2, 2000, sample Jun 1997–Jul 1998 Russell 1000): Last five minutes of the day explain a **disproportionate share of return variation** (~**18%** of portfolio daily-return variance vs ~**4%** single-name) and MOC imbalance publications predict **systematic overnight reversals** consistent with temporary liquidity-driven price pressure. — Cushing & Madhavan, *Journal of Financial Markets* 2000, https://www.chesler.us/resources/academia/trading_at_the_close.pdf

C3 [CONFIRMED] (T2, 2022, sample ~2010–2020 US): Closing auction volume ~**10%** of daily volume by 2019; Nasdaq auction price impact **~58% larger** than NYSE; temporary component ~**85%** (Nasdaq) / ~**62%** (NYSE) of impact, fully reversing over **3–5 days**; **long/short strategies exploiting impact + reversal are significantly profitable** (multi-day hold; NO-COST-MODEL flag on net retail economics). — Jegadeesh & Wu, *JFE* 2022, https://doi.org/10.1016/j.jfineco.2021.12.003

C4 [PLAUSIBLE] (T2 abstract, 2019 SSRN, US equities): Stocks in highest quintile of closing-auction imbalance quantity experience price pressure that **reverses**; a **long/short trading strategy** exploiting this pattern is proposed; results not subsumed by continuous order imbalance (Chordia–Subrahmanyam). Gross multi-day; DECAY-UNKNOWN post-pub OOS. — Wu, “Closing Auction, Passive Investing, and Stock Prices,” SSRN 3440239, https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3440239

C5 [CONFIRMED] (T2 thesis, Sep 2020, S&P/R2k on Nasdaq & NYSE): Pre-close continuous forward returns (seconds–minutes) are predictable from venue imbalance features; predictability **rises toward Nasdaq MOC/LOC cutoff (15:55)**; claimed capture ~**30% of the spread** in best Nasdaq S&P setting; **R² collapses after 15:55** when only IO/late LOC remain — supports timing of champion snapshot, not post-cutoff residual prediction. NO-COST-MODEL / student thesis. — Morand, Imperial College MSc 2020, https://www.imperial.ac.uk/media/imperial-college/faculty-of-natural-sciences/department-of-mathematics/math-finance/MORAND_CLEA_01805978.pdf

C6 [PLAUSIBLE] (T2, 2026 arXiv): Optimal / RL market-making that **anticipates the closing auction** as terminal liquidation improves session PnL vs Avellaneda–Stoikov / TWAP benchmarks by treating auction clearing and imbalance risk explicitly — mechanism for single-name inventory risk into the cross, **not** multi-name market-neutral books. Simulation + limited S&P mid path; not a retail L/S design. — Graf & Mastrolia, arXiv:2601.17247, https://arxiv.org/pdf/2601.17247

C7 [CONFIRMED] (T2 classic + 2024, multi-decade equities): Equity pairs / market-neutral long–short construction achieves **material variance reduction** as the number of close pairs M increases (std and extremes fall); market neutrality is the explicit design goal. Confirms portfolio math, **not** auction-specific residualization. — Gatev, Goetzmann, Rouwenhorst *RFS* 2006; Zhu, Yale 2024 pairs profitability, https://economics.yale.edu/sites/default/files/2024-05/Zhu_Pairs_Trading.pdf

C8 [PLAUSIBLE] (T3, 2019 Nasdaq research): US-style close allows LPs to **pre-position continuous liquidity** against published MOC imbalances before 16:00 (unlike European closes where futures remain open for hedge); imbalance info reduces into-cross volatility — describes institutional LP behavior that is the **other side** of our basis trade, not a retail hedge recipe. — Nasdaq “How Much Does the MOC Imbalance Matter?” 2019-09-27

C9 [UNVERIFIED] (no T1/T2 source found): A **same-session** long-imbalance / short-index (or opposite-imbalance pair) book, entered ~15:55 and both legs flat at the 16:00 cross, **cuts per-event residual sd from ~20 bps toward single-digit** while preserving a +2–3 bps mean on the basis signal. **No academic paper measures this residualization for the NOII near-vs-mid basis specifically.**

C10 [CONFIRMED] (T2, 2023, sample 2010–2018): Auction-to-intraday volume **spikes permanently after S&P 500 additions** and on rebalance/option-expiry days; passive ownership is a first-order driver of closing volume — strengthens mechanism that same-day multi-name imbalances can co-move (hedge relevance) and that rebal days amplify forced flow. — Bogousslavsky & Muravyev 2023 (as C1)

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | PASS | Decision at scheduled 15:55:10; hedge leg (ETF short / opposite name) can be pre-sized if signal list is short; 5–25 s manual still pre-positionable. Multi-leg same second is harder but not sub-5s required. |
| 2 | Access | PASS / stressed | Retail long+short equities available (Alpaca/IBKR); MOC/LOC on ETFs generally available — **verify broker cutoffs T1 before deploy**. $10k gate assumes full long **and** short notional; $1k whole-share multi-leg is tight. |
| 3 | Session | PASS | Both legs can be flat at 16:00 cross (MOC hedge or continuous short closed into print). Overnight L/S from Jegadeesh–Wu / Wu is **out-of-mission** unless user amends. |
| 4 | Data | PASS | Residualization testable on **owned** Nasdaq NOII + SIP 1s bars + QQQ/SMH/SOXX/SPY anchors. $0 incremental. |
| 5 | Fill realism | PASS for alpha leg; stressed for hedge | Alpha leg retains single-print auction exit. Hedge leg: continuous short into thinning book or ETF MOC — need condition-coded fill model; not free of continuous-market ambiguity if not MOC. |
| 6 | Statistics | PASS if residualization; FAIL if same-day opposite-pair only | Residualization keeps n (events with \|basis\|≥10 bps). Requiring opposite-imbalance pair same session **collapses n** and is UNDERPOWERED at 5-core names. Power vs 20 bps sd: mean 2.5 needs n≫ (20/2.5)² for tight CI; variance cut multiplies effective power. |
| 7 | Protocol | PASS | Named mechanism: remove common 15:55→16:00 factor from champion PnL. Pre-registrable thresholds (R², residual mean, residual sd). Charges a **method / portfolio-construction** sub-family under auction, not a new signal family. Holdout spent → forward or M11-style OOS only. |

**Survivor-profile score: 3/5**
1. Single-print/auction execution — **yes** for alpha leg; hedge leg maybe (point if both MOC).
2. Scheduled decision instant — **yes**.
3. Named price-insensitive payer — **yes** for mean (passive MOC); hedge is not a payer.
4. Historically testable ≤~$100 — **yes** ($0 owned).
5. Expected effect ≥2× cost burden — **unknown until residualization**; multi-leg doubles cost burden and splits capital → **point fails a priori** without measured R².

### Economics sketch
- **Expected gross (cited field, not our residual):** Champion own: **+2.5 bps/event dev / +12.5 holdout**. Field auction L/S: multi-day reversal books “significantly profitable” (Jegadeesh–Wu) and Wu long/short on imbalance quintiles — **not comparable units** (days not 5-min events; often NO-COST-MODEL). Auction abs deviation ~2.7–8 bps large-cap (B–M) is the scale of temporary pressure, not free alpha.
- **Our cost burden for market-neutral structure:** two spreads (or one taker + one MOC), borrow on short if not MOC sell, capital split → **effective alpha notional ~½** at fixed $10k long+short gate; at $1k whole shares multi-leg often infeasible.
- **Variance math (sketch, not measured):** residual_sd ≈ 20 × √(1−R²_hedge). To halve noise need R²≈0.75 of PnL variance hedgeable — aggressive for megacap 5-min residuals. Even R²=0.25 → sd≈17.3 bps (modest Sharpe lift 0.125→0.144). Mean must not be beta-contamination; if champion mean is pure idiosyncratic basis, residual mean ≈ gross mean.
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**. Hedged book must beat that on **residual Sharpe × capital efficiency**, not raw mean.

### Proposed next test (OPEN-TESTABLE)
- **Hypothesis:** Over 15:55:10→16:00, a non-trivial share of champion event PnL variance is common (market/sector); residualizing onto SPY/QQQ/SMH (and optionally equal-weight opposite-basis names) **cuts residual sd** while **residual mean stays ≥ +2 bps**.
- **Named payer (unchanged):** indexed MOC / passive flow driving near–mid basis; hedge is pure risk control.
- **Data needed:** owned Databento Nasdaq NOII + SIP 1s + QQQ/SMH/SOXX/SPY — **$0**.
- **Universe:** champion names (and M11 28 if power allows); events with \|basis\|≥10 bps at 15:55:10.
- **Expected n & power:** n on order of historical basis events (hundreds–thousands across 2020–2026). Power target: detect residual mean ≥2 bps vs residual_sd with SE ≤1 bps (need n ≥ (residual_sd)²). Kill if residual_sd falls <10% or residual mean collapses.
- **A-priori thresholds:**
  - Primary: R² of event PnL on simultaneous index (and sector ETF) 15:55:10→16:00 return ≥ 0.20; residual mean ≥ +2.0 bps; residual hit-rate ≥ 55%.
  - Secondary: same-day opposite-basis pair book residual_sd vs single-name (report only; not promotion-critical if n small).
- **Promotion rule:** residualization becomes **default reporting transform** for M10/M11 if R²≥0.20 and residual mean holds on forward paper; deploy multi-leg only if residual Sharpe × capital-efficiency > unhedged at $10k gate **and** broker MOC short/ETF path verified T1.
- **Kill criteria:** R² < 0.10; residual mean < +1 bps; or hedge leg cost (measured half-spread + borrow) ≥ residual mean.
- **Trial family charged:** statistical/method sub-family under auction (OPEN_QUESTIONS #16) — does **not** consume a new mechanism family if framed as residualization of champion.

### Sources
1. [T2] Bogousslavsky, V. & Muravyev, D. (2021 WP / 2023 JFM). “Who Trades at the Close? Implications for Price Discovery and Liquidity.” https://ssrn.com/abstract=3485840 ; https://doi.org/10.1016/j.finmar.2023.100852 — sample 2010–2018.
2. [T2] Cushing, D. & Madhavan, A. (2000). “Stock Returns and Trading at the Close.” *Journal of Financial Markets*. https://www.chesler.us/resources/academia/trading_at_the_close.pdf — sample 1997–1998 Russell 1000.
3. [T2] Jegadeesh, N. & Wu, Y. (2022). “Closing Auctions: Nasdaq versus NYSE.” *Journal of Financial Economics* 143(3). https://doi.org/10.1016/j.jfineco.2021.12.003 — sample ~2010–2020.
4. [T2] Wu, Y. (2019). “Closing Auction, Passive Investing, and Stock Prices.” SSRN 3440239. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3440239 — abstract-level quantities used where full PDF blocked.
5. [T2] Morand, C. (2020). “Predicting US stock returns using closing auction imbalance data.” Imperial College MSc thesis. https://www.imperial.ac.uk/media/imperial-college/faculty-of-natural-sciences/department-of-mathematics/math-finance/MORAND_CLEA_01805978.pdf
6. [T2] Graf, J. & Mastrolia, T. (2026). “Learning Market Making with Closing Auctions.” arXiv:2601.17247. https://arxiv.org/pdf/2601.17247
7. [T2] Gatev, E., Goetzmann, W., Rouwenhorst, K. (2006). “Pairs Trading: Performance of a Relative-Value Arbitrage Rule.” *RFS*. http://stat.wharton.upenn.edu/~steele/Courses/434/434Context/PairsTrading/PairsTradingGGR.pdf
8. [T2] Zhu (2024). “Examining Pairs Trading Profitability.” Yale. https://economics.yale.edu/sites/default/files/2024-05/Zhu_Pairs_Trading.pdf
9. [T3] Nasdaq (2019-09-27). “How Much Does the MOC Imbalance Matter?” https://www.nasdaq.com/articles/how-much-does-the-moc-imbalance-matter-2019-09-27
10. [T2] Hu, E. & Murphy, D. (related; floor-broker / NYSE close). “Vestigial Tails? Floor Brokers at the Close…” *Management Science* 2025 / SSRN 3600230 — NYSE vs Nasdaq reversal differential; used as design contrast only.
11. [T3] SSGA (2026). “Closing time: How passive investing is reshaping equity market microstructure.” https://www.ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure

#### Queries used
- hedged closing auction market neutral strategy variance reduction
- closing auction pairs trading imbalance market neutral site:ssrn.com OR site:arxiv.org
- "closing auction" OR "closing cross" market-neutral OR hedged OR pairs liquidity provision academic
- index futures hedge closing auction MOC imbalance strategy
- "closing auction" imbalance predictability hedge OR residual OR market-neutral arxiv OR SSRN
- Bogousslavsky Muravyev closing auction imbalance returns
- "order imbalance" close auction reverse OR momentum residual beta hedge academic paper
- variance reduction pairs trading auction cross-sectional long short close
- site:ssrn.com closing auction passive investing stock prices imbalance quintile returns
- "Who Trades at the Close" Bogousslavsky Muravyev auction deviation bps
- Wu Jegadeesh closing auctions information content price reaction SSRN
- Cushing Madhavan stock returns trading at the close order imbalance
- "cross-sectional" closing auction long short imbalance portfolio returns hedge
- market making closing auction inventory hedge index futures liquidity provision
- Jegadeesh Wu closing auctions Nasdaq versus NYSE price impact resiliency 2022 abstract returns
- "Closing Auction, Passive Investing, and Stock Prices" quintile returns overnight reversal bps
- site:arxiv.org closing auction imbalance long-short portfolio market neutral residual returns
