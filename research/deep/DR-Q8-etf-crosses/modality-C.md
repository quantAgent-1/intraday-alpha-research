## DR-Q8 — C practitioner findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence MED) — Practitioner/vendor literature confirms the close is the passive-flow liquidity event, and Nasdaq-listed ETFs (QQQ, SMH, SOXX) admit the exact champion structure (15:55-ish NOII near vs mid → exit at listing-venue close). But the load-bearing claim that **ETF shells have larger predictable basis/imbalance edges than single names is NOT supported** by T2/T3 evidence: mega-ETF absolute auction deviations are ~1.7–3.6 bps (same order as large-cap stocks, smaller than the cross-section mean), Arca ETF auction share is only ~2% of ADV vs ~9% equities, and APs routinely MOC underlyings then create/redeem (NAV-risk-free) rather than force flow into the ETF close. Published “QQQ/SPY close strategies” in the practitioner lane are either (a) index-level MOC directional bets (often overnight / futures-swaps — out of mission or different structure) or (b) retail MOC-imbalance screeners with no published per-event bps economics. Vendor pitches that “imbalance reveals the edge” are systematically **CONFLICTED**.

What would flip it: A clean champion-clone backtest on QQQ (owned-path Nasdaq NOII + SIP mid) with net ≥ +2 bps/event at n≥250, or evidence that Arca SPY residual basis after 15:55 is systematically larger than Nasdaq single-name residual (unlikely a priori).

### Mechanism
- **Who pays (constituents, well-established):** Passive index funds / ETFs / rebalancers / option-delta unwinders who must hit the official close for NAV/tracking-error reasons. Price-insensitive. Documented by SSGA, Bogousslavsky–Muravyev, Nasdaq Economic Research, BMLL. This is the same payer the champion already harvests in single names.
- **Who pays (ETF shell itself, weaker):** Secondary-market MOC into SPY/QQQ does exist (creation/redemption cash-in-lieu, tactical ETF traders, mutual-fund substitutes), but APs and brokers can **sidestep the ETF auction** by MOCing the basket and packaging into the ETF (BMLL; Dimensional GMOC/create-redeem narrative; Matthews GMOC off-exchange product). That reduces forced price-insensitive flow *into the ETF cross* relative to a forced-MOC equity.
- **Why it persists:** Listing-exchange auction monopoly + high auction fees + overnight inventory risk for offsetters leave a residual liquidity premium (Nasdaq research ~1.7 bps avg for N100 offsetters, 2019). Competition is fierce and 80% of imbalance news is in continuous prices within ~300 ms — residual after 5–25 s retail latency is the only harvestable slice.
- **Capacity intuition at $10k:** Trivial for SPY/QQQ (billions ADV). Edge, not capacity, is the binding constraint.
- **Venue map (execution-critical):**
  - **Nasdaq primary close / NOII path:** QQQ, SMH, SOXX (and most Nasdaq-listed ETPs) — same data class as champion names; historical NOII purchasable cheaply.
  - **NYSE Arca primary close / Arca imbalance:** SPY, IWM, most sector ETFs historically on Arca — **not** on owned Nasdaq NOII; Databento `ARCX.PILLAR` imbalance historical exists; RT Order Imbalances ≈ **$1,000/mo** exchange license floor (CONFLICTED vendor).

### Claims
C1 [CONFIRMED] (T2, 2020/2021 paper, sample 2010–2018 stocks + large-ETF supplement): Large ETFs (SPY, QQQ, S&P sector ETFs) have mean absolute closing-auction deviation **3.63 bps**, p99 **16.32 bps** — “behave similar to large stocks” (large-cap stock mean abs ~2.66 bps); full-sample stock mean abs 8.12 bps. Deviations mostly reverse overnight. **NO-COST-MODEL for a tradable 15:55→close basis rule.** — Bogousslavsky & Muravyev, “Who Trades at the Close?”, June 2021 / JFM 2023; https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf

C2 [CONFIRMED] (T3/vendor-CONFLICTED, 24 Jun 2025, sample May 2025 venue vignette + 2024 Russell): NYSE Arca is the primary ETF auction venue; **~2% of Arca ETF volume is in the auction vs ~9% for NYSE equities**. Brokers can MOC underlyings and package into the ETF, guaranteeing NAV risk-free. Arca imbalance feed starts **15:00 ET** (earlier than NYSE/Nasdaq 15:50). Indicative price on Arca fluctuates more in the last 5 minutes than Nasdaq equities. — BMLL / Traders Magazine, Laible & Thakur; https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

C3 [CONFIRMED] (T3 exchange research, 27 Sep 2019, sample Nasdaq-100, Q2-2019): On NOII publication, N100 closes move **avg 5.5 bps** immediately; **~80% of the ultimate close move is priced within 300 ms**; liquidity premium earned by imbalance offsetters **avg 1.7 bps** (gross, < half spread). Larger imbalances → larger impact. Implication for 5–25 s manual latency: most of the announcement edge is gone; residual is small. — Phil Mackintosh, Nasdaq Economic Research; https://www.nasdaq.com/articles/how-much-does-the-moc-imbalance-matter-2019-09-27

C4 [PLAUSIBLE] (T3 asset-manager, 23 Jan 2026, Instinet volume stats to Dec 2025): US closing-auction share of daily volume rose to **~13–15%** recently (Q4 2025 / Dec 2025); passive/ETF NAV-alignment is the structural driver; close can shift from price-revealing to price-forming on rebalance days. No per-name tradable-edge bps. — SSGA (Elise Ryan); https://www.ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure

C5 [UNVERIFIED] (T3 subscription blog, Jan 2024 + update Jan 2025): Index-level MOC imbalance treated as directional signal (any size in 2024 variant; previously >$1.5B only), implemented via **SPX leveraged swaps long/short**, claimed **+25% calendar-2024 return**, max DD 3.0% vs SPX 8.5%. **Not** a 15:55 ETF-basis → close trade; structure is overnight/index and out of champion session rules without amendment. NO-COST-MODEL detail; single-author; treat as hypothesis only. — “Nick” / Sell-Side Research Substack; https://sellside.substack.com/p/exclusive-research-moc-imbalance

C6 [CONFIRMED] (T3 vendor-CONFLICTED, 11 Oct 2024 + product pages): MarketChameleon retail product screens MOC imbalances >50k shares, attributes them to “ETFs and mutual funds” portfolio changes, pushes momentum/contrarian narratives. **No published QQQ/SPY per-event bps backtest** with costs. — MarketChameleon; https://marketchameleon.com/articles/b/2024/10/11/moc-order-imbalances-a-guide-for-traders-to-understand-institutional-activity

C7 [CONFIRMED] (T1/T3 vendor, 14 Aug 2025): Databento markets real-time + historical **NYSE Arca Order Imbalances** (`ARCX.PILLAR`, schema `imbalance`) with explicit **SPY** example; historical available usage-based / US Equities plans; RT Order Imbalances license **from ~$1,000/mo** (vs Integrated non-display **~$7,500+/mo**). Nasdaq NOII already known path for Nasdaq-listed names. **CONFLICTED** (sells the data that “reveals” the edge). — https://databento.com/blog/NYSE-imbalance-feeds

C8 [CONFIRMED] (T3 asset manager / product note): Institutional “Guaranteed MOC” (GMOC) for ETFs is an **off-exchange** LP block tied to official close — **not** the listing-exchange MOC auction. Confirms that large ETF close flow often never hits the exchange imbalance book. — Matthews Asia “Understanding Guaranteed Market-on-Close”; https://www.matthewsasia.com/insights/understanding-guaranteed-market-on-close/

C9 [PLAUSIBLE] (T3 issuer guidance): Dimensional: ETF closing auctions show **lower average volume** than continuous session; dealers often freer to provide liquidity intraday; investors should be “mindful of potentially higher costs” in the closing auction. Aligns with BMLL 2% figure; **contradicts** “ETF close is where the concentrated edge lives.” — https://www.dimensional.com/us-en/insights/trading-etfs

C10 [UNVERIFIED] (T2 cited, not re-fetched full text): Wu & Jegadeesh (2020) “Closing auctions: Information content and timeliness of price reaction” — cited by Bogousslavsky–Muravyev as finding **profitable reversal strategies based on MOC order imbalances** (stock cross-section). Not ETF-specific; sample/cost treatment UNKNOWN here. — cited in Who Trades at the Close

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **PASS** | Decision at fixed ~15:55 snapshot; 5–25 s pre-positionable (same as champion). Not the 300 ms first-print. |
| 2 | Access | **PASS** (Nasdaq ETFs) / **N-A→verify** (Arca) | QQQ/SMH/SOXX: retail MOC/LOC + taker entry at mid path same as names. SPY/IWM: Arca listing; MOC cutoffs follow Arca rules — confirm retail broker routes to Arca close. |
| 3 | Session | **PASS** | Enter late RTH, flat **at** 16:00 cross via auction exit (or MOC). In-mission. |
| 4 | Data | **PASS** (Nasdaq ETFs) / **OPEN-BLOCKED-lite** (Arca shell) | QQQ etc.: Databento Nasdaq NOII historical, same class as owned 5+28 names (~tens of $ per name-decade). SPY/IWM: need Arca imbalance historical (usage-based — expect ≤$100 for few symbols if imbalance schema only; **verify quote before buy**). RT Arca/NYSE imbalances ≈ $1k/mo — user approval. |
| 5 | Fill realism | **PASS** | Auction single-print exit; entry as continuous taker priced to mid (same kernel as champion). No maker assumption. |
| 6 | Statistics | **PASS** | Daily events on liquid ETFs → n ≫ 250 over multi-year history. Power OK even if mean is only 1–2 bps (need longer sample / multi-ETF pool). |
| 7 | Protocol | **PASS** | Named payer = residual auction liquidity demand from passive/ETF/rebal flow not fully offset pre-close; pre-register basis threshold (e.g. |near−mid| ≥ X bps at 15:55:10) **before** results; charges auction-family trial. |

**Survivor-profile score: 4/5**
1. Single-print/auction execution — **YES**
2. Scheduled decision instant — **YES**
3. Named price-insensitive payer — **PARTIAL** (clean for constituents; diluted for ETF shell by create/redeem + GMOC off-exchange path)
4. Historically testable ≤~$100 — **YES** for Nasdaq-listed ETFs; Arca TBD but likely
5. Expected effect ≥2× cost burden — **UNKNOWN a priori** (spreads tiny, residual basis also likely tiny; must measure)

### Economics sketch
- **Gross cited (not champion structure):**
  - Auction abs deviation mega-ETFs ~**3.6 bps** mean (Bogousslavsky; mid@4pm→close, not 15:55→close).
  - Imbalance-offset liquidity premium N100 ~**1.7 bps** gross (Nasdaq 2019).
  - Immediate post-NOII move ~**5.5 bps** of which ~80% is gone in 300 ms → residual for manual latency likely **≪ 2 bps** unless a stable near-price basis remains (the champion’s actual signal).
- **Our cost burden (this structure):** Taker half-spread on SPY/QQQ is often **sub-1 bps** (1-cent tick on high-priced QQQ ≈ 0.14 bps; SPY half-spread often ~0.5–1 bps). Zero commission through 2026-12-31. Auction exit = single print (no exit spread). Dominant cost is entry half-spread + any adverse selection into the last 5 minutes.
- **Net prior:** **UNKNOWN; prior is modest-to-null** relative to champion. If residual |basis| distribution for QQQ mirrors large-cap Nasdaq names, net might approach champion’s **+2.5 bps/event dev**; if ETF shell is more efficiently arbitraged (AP create/redeem + dense HFT), net may compress toward **0–1 bps**. **Not** expected to *exceed* single-name edges on average.
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**.

### Proposed next test (OPEN-TESTABLE)
- **Hypothesis:** On Nasdaq-listed liquid ETFs, at 15:55:10 ET, signed (NOII near − market mid) predicts signed (close − mid_entry) with mean gross ≥ +2 bps/event when |basis| ≥ 5–10 bps (pre-register exact threshold).
- **Named payer:** Residual closing-auction liquidity demand (passive rebal / cash-flow MOC into the ETF shell) not fully absorbed in continuous market after NOII publication.
- **Data needed:**
  - **Primary (cheap):** Databento Nasdaq NOII + SIP quotes for **QQQ, SMH, SOXX** (and optionally other Nasdaq ETPs). Same product class as M11 names. Expect **≪ $100** one-time for multi-year imbalance+trades on 3 symbols (confirm cost quote).
  - **Secondary (optional expansion):** Databento `ARCX.PILLAR` imbalance historical for **SPY, IWM** — get usage estimate first; if >$100, flag OPEN-BLOCKED.
  - **Owned already usable as anchors:** SIP event bars / quotes for QQQ/SMH/SOXX/SPY if present in the 12-name + anchors set for mid construction; still need listing-venue NOII for near price.
- **Universe:** Stage A: QQQ + SMH + SOXX. Stage B (if A survives): SPY/IWM if Arca data ≤$100.
- **Expected n & power:** ~250 sessions/year × 3 names ≈ 750 name-events/year; 4 years → n≈3,000 before filters. At ~20 bps event noise, detecting +2 bps mean needs n≈400+ events post-filter — achievable.
- **A-priori thresholds (lock before run):**
  - Signal: |NOII near − mid| ≥ 10 bps at 15:55:10 (champion default); also pre-register 5 bps sensitivity.
  - Direction: take WITH basis (same as champion).
  - Exit: listing-venue official close only.
  - Filters: skip if near/far still 0 (pre-15:55 data reality); skip halt/LULD days.
- **Promotion rule:** Dev mean net ≥ +2 bps/event AND hit-rate ≥ 55% on pooled Stage A with n≥250; then forward-paper only (holdout is spent).
- **Kill criteria:** Dev net ≤ 0 at n≥250; or concentration in ≤2 sessions/names drives all profit (top-decile trap); or basis |mean| on ETFs systematically < half-spread.
- **Trial family charged:** Auction / closing-cross family (same family as champion / M11 expansion — not a free trial).

### Sources
1. **[T2]** Bogousslavsky & Muravyev (2021/2023). Who Trades at the Close? — auction share, ETF-driven volume, ETF deviations 3.63 bps mean abs. https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf
2. **[T3 CONFLICTED]** BMLL (24 Jun 2025). Into the Close — Arca ETF auction ~2% ADV, NAV packaging path, imbalance timing. https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution
3. **[T3]** Mackintosh / Nasdaq Economic Research (27 Sep 2019). How Much Does the MOC Imbalance Matter? — 5.5 bps move, 1.7 bps premium, 300 ms efficiency. https://www.nasdaq.com/articles/how-much-does-the-moc-imbalance-matter-2019-09-27
4. **[T3]** SSGA Elise Ryan (23 Jan 2026). Closing time: passive investing reshaping microstructure — US close share ~13–15%. https://www.ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure
5. **[T3]** Sell-Side Research / Nick (Jan 2024; update 4 Jan 2025). MOC Imbalance exclusive — claimed 25% 2024 SPX-swap strategy. https://sellside.substack.com/p/exclusive-research-moc-imbalance
6. **[T3 CONFLICTED]** MarketChameleon (11 Oct 2024). MOC Order Imbalances guide + imbalance reports. https://marketchameleon.com/articles/b/2024/10/11/moc-order-imbalances-a-guide-for-traders-to-understand-institutional-activity
7. **[T1/T3 CONFLICTED]** Databento (14 Aug 2025). Real-time NYSE/Arca imbalance feeds; SPY example; $1k/mo RT floor. https://databento.com/blog/NYSE-imbalance-feeds
8. **[T3]** Matthews Asia. Understanding Guaranteed Market-on-Close (GMOC) for ETFs. https://www.matthewsasia.com/insights/understanding-guaranteed-market-on-close/
9. **[T3]** Dimensional. Trading ETFs — lower auction volume, careful with close costs. https://www.dimensional.com/us-en/insights/trading-etfs
10. **[T3]** TraderVPS / Tommy Sinclair (30 Jul 2025). MOC Imbalance retail synthesis (aggregates Nasdaq 1.7 bps, MarketChameleon, sellside). https://www.tradervps.com/blog/moc-imbalance-in-trading-what-it-is-and-how-to-use-it
11. **[T3]** Alpha Architect (21 Jul 2025). End-of-day reversal summary (Baltussen et al.) — overnight hold, out-of-mission. https://alphaarchitect.com/end-of-trading/
12. **[T1]** NYSE Auctions / imbalance docs; free 3-mo largest-1000 imbalance tool. https://www.nyse.com/trade/auctions ; https://www.nyse.com/data-insights/nyse-introduces-closing-auction-imbalance-analysis-tool

#### Queries used
- ETF closing auction imbalance strategy QQQ SPY
- ETF MOC close basis trade practitioner vendor
- "closing auction" ETF arbitrage imbalance edge quant
- NYSE Arca ETF closing auction imbalance vendor data BMLL
- ETF closing auction price deviation SPY QQQ practitioner hedge fund
- "closing imbalance" OR "close imbalance" ETF strategy blog OR quant OR vendor
- site:ssrn.com ETF closing auction imbalance MOC
- sellside substack MOC imbalance exclusive research
- MarketChameleon MOC order imbalances guide traders
- Databento NYSE Arca imbalance historical pricing cost ETF
- Who Trades at the Close auction price deviations QQQ SPY Bogousslavsky
- ETF closing auction lower volume Arca vs equity MOC basis trade
- QQQ primary listing exchange Nasdaq OR Arca closing auction
- Wu Jegadeesh market-on-close order imbalances profitable reversal
- "ETF" "closing auction" OR "close imbalance" OR "basis" edge OR profit OR strategy quant blog
- quantifiedstrategies imbalance trading strategy MOC returns
- SMH SOXX IWM primary listing exchange Arca Nasdaq
- "closing auction" ETF premium discount NAV close SPY QQQ arbitrage
- Databento historical NYSE Arca imbalance schema cost per symbol QQQ SPY
- Databento historical imbalance cost tens of dollars per symbol decade Nasdaq ETF
