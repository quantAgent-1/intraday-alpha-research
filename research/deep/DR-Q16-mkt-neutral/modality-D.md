## DR-Q16 — D adversarial findings

### Verdict recommendation
**NOT-VIABLE-STRUCTURAL** (confidence **HIGH**) — Market-neutral / hedged closing basket fails our profile on multiple independent structural axes at once: (i) two-leg cost burden roughly doubles the already-thin cost envelope that leaves the champion at only +2.5 bps/event net, (ii) beta (or index) hedge cannot remove the stock-specific auction residual that dominates our ~20 bps/event noise, (iii) manual 5–25 s dual-leg entry is not simultaneous and injects legging risk the single-name champion never carries, and (iv) $1k whole-share capital cannot size both legs with a meaningful beta-matched hedge without collapsing notional. Field prior-art on pairs/stat-arb at any frequency shows extreme sensitivity to TC and latency; the close-specific economics make the same math worse, not better.

What would flip it: A sealed measurement on owned NOII+BBO showing that the residual of champion net_bps after a 15:55:10→16:00 QQQ/SMH beta hedge has sd ≤ ~8 bps (i.e., ≥60% variance cut) **and** that two-leg entry+fee cost adds ≤ +0.8 bps vs the single-leg fill kernel — simultaneously. Absent both, the structure is dead under §1.

### Mechanism
**No coherent incremental payer for the hedge leg.** The champion's payer is indexed MOC/rebalance flow that prints at the single-name closing cross after the NOII near has already announced direction — a price-insensitive, named, scheduled flow. A market-neutral book (long imbalance-name / short index, or dual-name long/short) does not create a second payer; it only attempts variance reduction. The index short has no auction-imbalance edge of its own at our decision instant, so its expected contribution is ~0 gross while adding a full second cost stack and a second residual. Residual basis risk remains because the dominant noise term in the 15:55:10→cross PnL is name-specific auction clearing residual and name continuous path, not market beta. Capacity intuition: even if noise fell modestly, dual-leg capital and short-locate constraints at retail size make the structure capacity-*worse* than the single-name champion, not better.

### Claims
C1 [CONFIRMED] (T2, Bowen/Hutchinson/O'Sullivan 2010, sample FTSE100 2007 HF pairs): High-frequency equity pairs excess returns are extremely sensitive to transaction costs and execution speed — 15 bps of TC cut excess returns by more than 50% (e.g., 15.2%→7.0% ann. under a j=3 trigger); a one-period wait before execution eliminates the strategy's excess returns. — https://www.ucc.ie/en/media/research/centreforinvestmentresearch/wp/wp1004high-frequency-equity-pairs-trading.pdf

C2 [CONFIRMED] (T2, Gatev/Goetzmann/Rouwenhorst RFS 2006, sample US equities 1962–2002): Classical pairs profits require two legs × two round-trips; conservative microstructure estimate of pair round-trip costs ~162 bp per pair over the trading window, and profits load little on market beta — i.e., residual/relative risk, not beta, is the economic object. NO-COST-MODEL for sub-hour auction residual. — http://stat.wharton.upenn.edu/~steele/Courses/434/434Context/PairsTrading/PairsTradingGGR.pdf

C3 [CONFIRMED] (T2, Bogousslavsky/Muravyev 2020/2023, sample NYSE+Nasdaq 2010–2018): Closing auction absolute deviation from 4pm mid averages **8.1 bps** (matches half-spread order of magnitude); deviations reverse largely overnight; auctions charge high fees to both sides and have imperfect external LP participation — two-sided auction participation is costly by design. — https://www.aeaweb.org/conference/2021/preliminary/paper/H9T4hef7 ; J. Fin. Markets 2023 abstract https://www.sciencedirect.com/science/article/abs/pii/S1386418123000502

C4 [CONFIRMED] (T2, Jegadeesh/Wu JFE 2022, Nasdaq vs NYSE closing auctions): Temporary component of closing-auction price impact takes **3–5 days** to fully dissipate; Nasdaq imbalance collapses ~80% after first NOII dissemination — residual post-announcement path is small and noisy, not a large systematic factor one can hedge away with an index. — https://ideas.repec.org/a/eee/jfinec/v143y2022i3p1120-1139.html

C5 [PLAUSIBLE] (T2, Herskovic et al. / CIV literature; common market-model fact): At the individual-stock level, almost all return variation is idiosyncratic; typical daily market-model R² is far below 50% for single names, so a beta hedge removes only a minority of variance (residual sd scale ≈ σ√(1−R²)). For a ~5-minute 15:55→16:00 window the systematic fraction is not higher a priori — auction residual is *more* name-specific (NOII is per-symbol). — e.g. https://w4.stern.nyu.edu/finance/docs/pdfs/Seminars/CIVpaper_20140410.pdf ; quant folklore + CAPM R² discussion https://quant.stackexchange.com/questions/74450/capm-yields-very-poor-fit-low-r-squared-is-that-normal

C6 [CONFIRMED] (T1, Nasdaq Closing Cross FAQs / rulebook): Nasdaq MOC entry cutoff is **3:55 p.m. ET**; LOC until 3:58 under constraints; NOII near/far meaningful only after ~15:55. Our champion decision at 15:55:10 is *after* MOC cutoff — entry is continuous taker, not dual MOC. Dual-leg therefore cannot "both print at auction entry"; both legs are continuous-market entries with dual half-spreads/slip. — https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf

C7 [CONFIRMED] (T1, Alpaca short-selling docs, Nov 2025 / HTB 2026): Alpaca ETB shorts carry $0 borrow for Trading API users; HTB requires locates (round lots of 100, non-refundable locate fees, single-use). Intraday cover-at-close limits borrow accrual, but short availability, margin, and locate friction remain real constraints; HTB is not free. — https://alpaca.markets/support/short-selling-fees ; https://docs.alpaca.markets/us/docs/margin-and-short-selling

C8 [CONFIRMED] (T2, Engelberg/Reed/Ringgenberg-line / JF 2025 "Anomalies and Their Short-Sale Costs"): Mean stock borrow fee ~1.64%/yr with extreme right tail (p99 ~30%/yr); high-fee stocks (~12% of stock-months >1%/yr) wipe anomaly long-short nets after fees. Even GC names are not free of short-side operational risk at retail. — https://onlinelibrary.wiley.com/doi/10.1111/jofi.13501

C9 [PLAUSIBLE] (T3+T1 structural, multi-leg execution literature): Multi-leg *stock* simultaneous orders are not a standard retail equity product the way multi-leg *options* are; sequential manual legs create unbalanced exposure if one fills and the other does not (classic legging risk). Manual 5–25 s reaction on two tickets is structurally worse than one. — e.g. IB multi-leg options framing https://www.interactivebrokers.com/campus/traders-insight/securities/options/multi-leg-options-can-reduce-risk-improve-executions/

C10 [CONFIRMED] (project internal T1-equivalent, AGENT_BRIEF / M6-FINAL): Champion economics are single-leg taker entry + 0.5 bp slip + SEC/TAF ~0.3 bp sell, exit at single print; net dev **+2.5 bps/event**, noise ~**20 bps** sd. Any dual-leg structure must clear a cost bar of roughly **2×** that entry burden against the *same* gross mean (or a diluted mean if capital is split). Already-known: mean small vs noise; two-leg cost burden.

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **FAIL** | Dual continuous-market legs cannot be keyed simultaneously in 5–25 s manual; legging risk is new and unpriced in the champion. Scheduled decision helps the *signal* only. |
| 2 | Access | **FAIL / marginal** | Long+short at $1k whole shares: megacap share prices leave 1–few shares per leg; beta-matched QQQ/SMH hedge is granular and crude. Margin + short locate required. |
| 3 | Session | **PASS** | Still RTH; both legs can be flat at/via the close. |
| 4 | Data | **PASS** | Owned NOII + BBO + QQQ/SMH anchors suffice for a residual-variance study. |
| 5 | Fill realism | **FAIL** | Two continuous taker entries (post-15:55 MOC cutoff) vs champion's one; dual half-spread/slip; hedge leg has no single-print *entry* advantage. |
| 6 | Statistics | **PASS (testable)** | n can match champion (~thousands of events); but expected mean after 2× costs is near 0 → power against 20 bps noise is hopeless unless variance collapses dramatically (it does not). |
| 7 | Protocol | **FAIL** | No new named payer; hedge is a variance transform of an existing family (moc_imbalance_v1), not a pre-registrable new mechanism. Charges multiple-testing budget for a structurally handicapped re-skin. |

**Survivor-profile score: 2/5**
1. Single-print/auction execution — **0** (entry dual continuous; only exits can be cross)
2. Scheduled decision instant — **1** (15:55:10 still works for the signal)
3. Named price-insensitive payer — **0** (hedge leg has none; signal payer unchanged)
4. Historically testable on owned/≤$100 data — **1**
5. Expected effect ≥ 2× cost burden at our size — **0** (double costs vs +2.5 mean)

### Economics sketch
- **Champion (benchmark):** gross edge small; net **+2.5 bps/event** dev / **+12.5** holdout; noise **~20 bps** sd/event; single cost stack (taker + ~0.5 bp slip + ~0.3 bp SEC/TAF).
- **MN structure cost burden:** two taker entries ≈ **2×** half-spread+slip; two SEC/TAF legs if both sell sides fire over time; short locate/borrow 0 for ETB GC but operational. Approximate added cost vs champion: **+1.0 to +2.5 bps/event** (name-dependent), before any legging slippage.
- **Gross:** edge lives only on the signal leg. If capital is split 50/50 long/short, dollar exposure to the signal halves → **half the bps on account equity**. If full gross with margin, account risk and Reg-T usage double for the same signal notional.
- **Noise after beta hedge (order-of-magnitude):** suppose last-5-min name-vs-QQQ R² ∈ [0.25, 0.50] (optimistic for megacaps). Residual sd scale factor √(1−R²) ∈ [0.71, 0.87] → noise ~14–17 bps, **not** ~8. Auction residual is largely orthogonal to the index — so realized cut is at the low end of that range. Hedge residual **adds** QQQ path noise with no mean.
- **Net prior:** mean after 2× costs and/or half-sizing ≈ **0 to slightly negative**; noise still ~15+ bps → t-stat and Sharpe strictly worse than single-name champion. **Comparison line: champion = +2.5 bps/event dev / +12.5 holdout.**

### Proposed next test (only if OPEN-TESTABLE)
*Not proposed — structure is NOT-VIABLE-STRUCTURAL. Optional cheap autopsy (does not open a trial family):*
- On owned M6-FINAL event set, regress per-event residual PnL on contemporaneous 15:55:10→16:00 QQQ and SMH returns; report R² and residual sd. Kill confirmation if residual sd > 0.75 × raw sd (i.e., <44% variance cut). No promotion path; do not charge a registered family.

### Sources
1. **T2** Bowen, Hutchinson, O'Sullivan (2010). *High Frequency Equity Pairs Trading: Transaction Costs, Speed of Execution and Patterns in Returns.* UCC Centre for Investment Research. Sample: FTSE100, 2007. https://www.ucc.ie/en/media/research/centreforinvestmentresearch/wp/wp1004high-frequency-equity-pairs-trading.pdf
2. **T2** Gatev, Goetzmann, Rouwenhorst (2006). *Pairs Trading: Performance of a Relative-Value Arbitrage Rule.* Review of Financial Studies 19(3). Sample: US 1962–2002. http://stat.wharton.upenn.edu/~steele/Courses/434/434Context/PairsTrading/PairsTradingGGR.pdf
3. **T2** Bogousslavsky & Muravyev (2020 working / 2023 J. Fin. Markets). *Who Trades at the Close?* Sample: NYSE+Nasdaq common stocks 2010–2018. https://www.aeaweb.org/conference/2021/preliminary/paper/H9T4hef7
4. **T2** Jegadeesh & Wu (2022). *Closing Auctions: Nasdaq versus NYSE.* Journal of Financial Economics 143(3). https://ideas.repec.org/a/eee/jfinec/v143y2022i3p1120-1139.html
5. **T1** Nasdaq Closing Cross FAQ / cutoff times (MOC 3:55 p.m. ET). https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf
6. **T1** Alpaca short-selling fees / ETB $0 / HTB locates. https://alpaca.markets/support/short-selling-fees ; https://docs.alpaca.markets/us/docs/margin-and-short-selling
7. **T2** "Anomalies and Their Short-Sale Costs" (Journal of Finance, 2025). Borrow-fee distribution and anomaly wipeout net of fees. https://onlinelibrary.wiley.com/doi/10.1111/jofi.13501
8. **T2/T3** Swedroe summary of rising short costs (2025); S3 Partners US borrow fee stats (2022–23 GC ~0.30%). https://larryswedroe.substack.com/p/the-rising-cost-of-short-selling ; https://www.s3partners.com/articles/us-stock-borrow-fees
9. **T2** Herskovic / CIV idiosyncratic-variance factor structure (near-all stock-level variance idiosyncratic). https://w4.stern.nyu.edu/finance/docs/pdfs/Seminars/CIVpaper_20140410.pdf
10. **T1/project** enginev5.1 AGENT_BRIEF + M6-FINAL holdout (+2.5 / +12.5, ~20 bps noise; single-leg cost stack).
11. **T3** Multi-leg execution / legging risk (options literature as analogy; stock multi-leg not retail-standard). https://www.interactivebrokers.com/campus/traders-insight/securities/options/multi-leg-options-can-reduce-risk-improve-executions/
12. **T2** Bogousslavsky (cross-section of intraday/overnight; last half-hour anomaly reversal patterns). Context for close-window risk not being pure beta. ScienceDirect / Bocconi PDF.

#### Queries used
- market neutral pairs trade closing auction costs double transaction costs
- closing auction imbalance market neutral hedge residual idiosyncratic risk
- retail short selling borrow fees hard to borrow stocks cost bps 2024 2025
- site:ssrn.com OR site:arxiv.org closing auction imbalance arbitrage hedge
- idiosyncratic volatility closing auction stock residual risk market beta hedge
- pairs trading transaction costs kill edge half-life market microstructure
- Alpaca short selling availability hard to borrow retail short locate fees
- "closing auction" OR "market on close" pairs OR hedge OR "market neutral" execution risk OR legging
- retail MOC order dual leg simultaneous both legs failure lag risk
- fraction of stock return variance idiosyncratic vs systematic single day last hour
- Jegadeesh Wu closing auctions Nasdaq NYSE imbalance mean reversion bps
- Bogousslavsky Muravyev who trades at the close fees auction cost
- Gatev Goetzmann Rouwenhorst pairs trading residual risk correlation not beta hedge
- R-squared single stock daily returns market model idiosyncratic fraction megacap
- Nasdaq MOC cutoff time 15:55 imbalance publication continuous trading hedge
- Alpaca margin buying power Reg T short sale collateral both legs $1000
- "residual risk" OR "idiosyncratic" closing auction return variance stock-specific
- Gatev pairs trading correlation residual systematic factor not market beta
