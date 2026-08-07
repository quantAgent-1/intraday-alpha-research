## DR-Q4-6 — C practitioner findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence **MED**) — Named retail brokers (IBKR, Schwab/tos, Alpaca with Elite Smart Router) document live MOC/LOC order types; practitioner and vendor evidence says auction impact at $1k–$10k notional in liquid Nasdaq names is negligible vs ADV/auction size. The binding retail frictions are **broker cutoff clocks** (often *earlier* than exchange cutoffs) and **Alpaca paper-auction fidelity**, not capacity. Champion cost assumption (cross BBO +0.5 bp) is in the same ballpark as half-spread / ITG “~0.5× spread to 4pm quote” stylized facts for liquid names; it is not contradicted by practitioner reports at our size. LOC-at-near is the realistic post-15:55 exit path on Nasdaq when MOC is already closed at the broker.

What would flip it: Live fills log showing that Alpaca (or chosen broker) systematically refuses post-15:50 CLS/LOC on Nasdaq names, or that continuous-book entry at 15:55:10 routinely costs ≥ half the holdout edge after fees.

### Mechanism
Who pays: Index / ETF / NAV-benchmarked MOC flow (price-insensitive to hit the official close) and residual continuous-book liquidity that absorbs pre-close imbalance reaction. SSGA (2026) and BMLL (2025) document structural migration of volume into the close as indexing grew; that is the persistent payer for any basis that remains after the first imbalance print. Capacity intuition at retail: $10k is << 0.01% ADV and << 1% of typical megacap closing-cross size — impact models and EliteTrader practitioners treat this as noise. No coherent story that retail is *crowded out* of MOC/LOC; the story is **access timing** (broker vs exchange cutoff) and **fill-model honesty** (paper ≠ live auction print).

### Claims
C1 [CONFIRMED] (T3-broker-docs, 2022–2026, ongoing): Alpaca supports MOC/LOC via `time_in_force=cls` (market→MOC, limit→LOC); **CLS submitted after 3:50pm ET and before 7:00pm is rejected**; after 7:00pm queues for next day. Learn article also states OPG/CLS available only to **Elite Smart Router** users. — https://docs.alpaca.markets/us/docs/orders-at-alpaca ; https://alpaca.markets/learn/13-order-types-you-should-know-about

C2 [CONFIRMED] (T3-broker-docs, undated/current): Schwab thinkorswim offers MOC and LOC for stocks, but UI removes them after **3:45 p.m. ET** (stricter than Nasdaq 3:55 MOC / 3:58 LOC). — https://toslc.thinkorswim.com/center/howToTos/thinkManual/Trade/Order-Entry-Tools

C3 [CONFIRMED] (T3-broker-education, current): IBKR supports MOC and LOC (all platforms, Smart/Directed/Lite); education page cites **Nasdaq MOC stop 3:55 ET, NYSE MOC stop 3:50 ET**. LOC is standard priced-on-close protection. — https://www.interactivebrokers.com/campus/trading-lessons/ibkr-desktop-market-on-close-order/ ; https://www.interactivebrokers.com/en/trading/ordertypes.php

C4 [PLAUSIBLE] (T3-practitioner, 2015, sample CEF/open-gap strategies live vs backtest): Ernie Chan: MOC/LOC is the correct way to capture the *official/auction* close and avoid bid-ask; consolidated “close” ≠ primary-exchange auction print; strategies needing open/close execution require TAQ with cross flags. Live open-gap reversion underperformed mid-price +5 bp TC walk-forward. — http://epchan.blogspot.com/2015/04/beware-of-low-frequency-data.html

C5 [PLAUSIBLE] (T3-vendor, ITG Bacidore et al. 2012, US equities pre-2012 sample): Imbalance impact is realized **at first imbalance message**; thereafter mean return ≈ 0. Median |close − 4pm quote| ≈ **0.5× spread** roughly independent of imbalance size (direction predicted, magnitude not). Implies trading *with* published imbalance into the auction is not free money. — https://mrtopstep.com/wp-content/uploads/2024/02/ITG-Trading-Around-The-Close-11-7-2012-1-1.pdf (CONFLICTED: sell-side execution research)

C6 [PLAUSIBLE] (T3-forum practitioners, 2019): EliteTrader: (a) last-trade-to-close is wrong impact benchmark — measure from imbalance release; (b) old ITG replication ~**4 bp price impact per 1% ADV** imbalance; (c) IB trader at **0.01–0.05% ADV** LOO/MOC considers impact “not material”; (d) impact better as %ADV than %auction. — https://www.elitetrader.com/et/threads/moc-orders-for-opening-and-closing-positions.336885/ ; https://www.elitetrader.com/et/threads/price-impact-in-the-opening-closing-auction.328743/ (T3, not T1)

C7 [CONFIRMED] (T3-vendor, SSGA/Instinet, as-of Dec 2025): US equities close-auction share of daily volume rose to ~**13–15%** (Q4’25 / Dec’25); passive/index NAV mechanics drive MOC concentration; spreads compress into the close vs the open. — https://www.ssga.com/is/en_gb/institutional/insights/how-passive-investing-reshaping-microstructure (CONFLICTED: asset manager marketing)

C8 [CONFIRMED] (T3-vendor, BMLL 2025-06-24): Nasdaq MOC until 3:55, LOC until 3:58, IO until 4:00; NYSE MOC/LOC 3:50 with D-Orders to 3:59:50 (~46% of NYSE close volume as of Aug 2024). Typical day ~$50B notional at close (~9% ADV); rebalance days much higher. Nasdaq indicative↔mid converge hard **3:57–3:58**. — https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution (CONFLICTED: data vendor selling L3/auction data)

C9 [PLAUSIBLE] (T3-forum, Alpaca paper 2021-04-06→05-12, n=1000 auction fills / 183 liquid names): Alpaca **paper** CLS/OPG does *not* fill at official auction — treated as continuous market at bid/ask; systematic MOC-buy discrepancy **+12 to +22 bps** vs Tiingo adjusted close (99% bootstrap CI). Alpaca staff confirmed paper ≠ live auction. — https://forum.alpaca.markets/t/accurate-opg-and-cls-prices-for-paper-trading/3762

C10 [UNVERIFIED] (T3-education/marketing, various): “LOC-at-near” as an explicit named retail tactic for capturing NOII near is **not** documented in broker education; practitioners discuss LOC for *price protection* and MOC for *certainty*, and Nasdaq late-LOC reprice-to-ref rules. Whether setting LOC limit = NOII near at ~15:55:30–15:57 systematically improves fill rate vs MOC without killing expected edge is UNKNOWN in public T3 — needs live/paper-correct experiment.

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **PASS** | Decision instant scheduled (15:55:10); 5–25 s human keying still inside Nasdaq LOC window to 15:58 if broker allows. |
| 2 | Access | **PASS with caveats** | IBKR: full MOC/LOC. Schwab: MOC/LOC but broker cutoff 15:45. Alpaca: CLS exists but Elite Smart Router required per learn docs + hard reject after 15:50 — **blocks MOC after signal; LOC may also be blocked if broker maps CLS cutoff to both**. Fidelity: MOC via ATP reported, LOC less clear. |
| 3 | Session | **PASS** | Exit is AT the 16:00 cross via MOC/LOC — explicitly in-mission. |
| 4 | Data | **PASS** | Mechanics claims from free broker docs; historical economics on owned SIP+NOII. No new paid feed required for access study. |
| 5 | Fill realism | **PASS (exit) / stress (entry)** | Exit = single auction print (zero exit-spread ambiguity if true MOC/LOC). Entry = continuous taker at 15:55:10 — must price half-spread + any imbalance-already-priced move (ITG). Do **not** trust Alpaca paper for auction fills. |
| 6 | Statistics | **N-A** (this charge is execution reality, not a new edge family) | Capacity at $10k does not reduce n. |
| 7 | Protocol | **PASS** | Payer named a priori (index MOC / NAV flow); pre-registerable. Does not invent a new trial family — annotates champion execution. |

Survivor-profile score: **5/5** for the *champion structure* as already specified (single-print exit, scheduled decision, named payer, testable on owned data, edge vs cost). This modality does not propose a new candidate; it stress-tests retail executability of that structure.

### Economics sketch
- **Expected gross (champion, already measured)**: dev ≈ +2.5 bps/event; holdout **+12.5 bps/event [6.9, 18.5], n=140**.
- **Our cost burden (practitioner-consistent)**:
  - Entry: cross BBO ≈ half-spread. Megacap spreads often 1 cent → ~0.5–2+ bps depending on price; champion models **+0.5 bp** (aggressive but not absurd at whole-share size in NVDA/TSLA-class names if mid→aggressive side only once).
  - Exit MOC/LOC: **0 spread** vs official close by construction if true auction order; residual risk is *missed LOC* (limit not marketable → overnight inventory = mission violation) or *broker rejection*.
  - Auction self-impact at $10k: practitioner/ITG scaling → **≪ 0.1 bp** (immaterial).
  - Commissions: $0 through 2026-12-31 at current Alpaca promo; post-promo stress = per-share fee annotation only.
- **Net prior**: holdout +12.5 − ~0.5 entry − ~0 exit impact ≈ **+12 bps/event** if live MOC/LOC works; if forced to exit continuous near 15:59 instead of auction, subtract another half-spread and reintroduce fill ambiguity — that would be a different, worse structure.
- Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout**.

### Proposed next test (only if OPEN-TESTABLE)
**Hypothesis:** On liquid Nasdaq names, a $1k–$10k round-trip (taker entry ≤15:55:25 WITH basis; LOC exit limit = NOII near ±0–2 ticks, submitted ≤15:57:30) fills both legs at costs ≤ champion model (entry ≤1 bp vs mid; exit = official close when LOC marketable).

**Named payer:** Index/ETF MOC flow creating temporary near-vs-mid basis (unchanged).

**Data needed:** Owned SIP ticks + Databento NOII (already held). Live/paper **fill log** from broker that actually supports post-15:55 LOC (prefer IBKR if Alpaca CLS hard-stops at 15:50 for both MOC and LOC). **$0** incremental data.

**Universe:** Same champion 5 core + any M11 names with reliable short locate.

**Expected n & power:** Forward paper/live n≥50 events / ≥30 sessions in 2–3 months; power vs ~20 bps sd is weak for mean estimation — this test is **execution QA**, not edge re-estimation (holdout spent). Kill on execution, not on mean.

**A-priori thresholds:**
- CLS/LOC reject rate after signal: **≤5%** of signals.
- LOC non-fill (limit unmarketable at cross): **≤10%** when limit = near ±2 ticks.
- Entry slippage vs mid: median ≤ **1.0 bp**, p90 ≤ **3 bp**.
- Exit fill price = primary official close on ≥ **95%** of filled LOC/MOC.

**Promotion rule:** All four thresholds met over ≥50 live/paper-correct events → annotate champion deploy playbook with broker+cutoff+LOC-at-near procedure; feed M10 harness.

**Kill criteria:** Broker cannot accept any on-close order after 15:50 on Nasdaq *and* no alternative broker onboards within one sprint; OR median entry slip ≥ 5 bp; OR LOC non-fill ≥ 30%.

**Trial family charged:** Execution annotation of **champion / M10 forward harness** — not a new alpha family.

### Sources
1. [T3-broker] Alpaca Placing Orders / TIF `cls` — docs.alpaca.markets (current). Cutoff 3:50pm ET reject.
2. [T3-broker] Alpaca Learn “Order Types and Time in Force” (Satoshi Ido; page dated Mar 4, 2022, content current). OPG/CLS Elite Smart Router only; CLS after 3:50 rejected.
3. [T3-broker] Schwab thinkorswim Order Entry manual — MOC/LOC stocks only, must submit before 3:45pm ET.
4. [T3-broker] IBKR Campus “Market on Close Order” lesson — Nasdaq 3:55 / NYSE 3:50 MOC stops.
5. [T3-broker] IBKR order types page — LOC Smart/Directed/Lite, all platforms.
6. [T3-practitioner] Ernie Chan, “Beware of Low Frequency Data,” Quantitative Trading blog, 2015-04-13 — MOC/LOC vs consolidated close; live vs backtest gap.
7. [T3-vendor CONFLICTED] ITG (Bacidore et al.), “Trading Around the Close,” 2012-11-07 — imbalance impact at first message; median close vs 4pm ~0.5× spread.
8. [T3-forum] EliteTrader threads 336885 (2019-10) and 328743 (2019-01) — MOC impact benchmarks, 0.01–0.05% ADV practice, ITG citation.
9. [T3-vendor CONFLICTED] SSGA, “Closing time: How passive investing is reshaping equity market microstructure,” 2026-01-23 — US close ~13–15% ADV; index MOC mechanism.
10. [T3-vendor CONFLICTED] BMLL / Traders Magazine, “Into the Close…,” 2025-06-24 — venue cutoffs, D-Orders, ~$50B typical close, Nasdaq convergence 3:57–3:58.
11. [T3-forum] Alpaca Community, “Accurate OPG and CLS prices for Paper trading,” 2020–2021 — paper MOC bias +12–22 bps; staff: paper treats as market orders.
12. [T3-broker-adjacent] Lime Trading, “Trading the Close…,” 2025-08-14 — last-30m liquidity/MOC narrative (marketing).
13. [T3-forum] Portfolio123 / Fidelity ATP / Bogleheads practitioner notes — MOC available at IB and Fidelity ATP for liquid names (secondary corroboration only).

#### Queries used
- retail broker MOC LOC order availability Alpaca Interactive Brokers Schwab Fidelity
- closing auction MOC LOC retail execution slippage practitioner experience
- LOC limit on close near price tactic closing auction retail
- "market on close" retail trading small account capacity basis NOII
- Quantopian OR Ernie Chan OR "Market on Close" auction arbitrage retail
- Alpaca market on close MOC LOC order type support
- "closing auction" OR MOC "slippage" OR "implementation shortfall" retail OR IBKR OR "Interactive Brokers" site:blog OR practitioner
- FlexTrade OR ITG OR Virtu OR Liquidnet closing auction execution quality MOC
- Schwab Fidelity "market on close" order type support retail
- closing auction imbalance arbitrage retail "basis" OR "near price" NOII practitioner
- pre-close last 5 minutes bid ask spread slippage megacap NVDA TSLA retail
- ITG "Trading Around the Close" market impact MOC
- Alpaca Elite Smart Router OPG CLS required market on close
- "limit on close" near price OR indicative OR "reference price" retail OR broker OR IBKR
- IBKR "limit on close" cutoff time Nasdaq 3:58 OR "3:55" retail
- Fidelity "market on close" OR MOC OR "limit on close" order types
- Schwab thinkorswim market on close MOC LOC order
