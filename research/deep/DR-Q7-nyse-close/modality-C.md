## DR-Q7 — C practitioner findings
### Verdict recommendation
**NOT-VIABLE-STRUCTURAL** (confidence **HIGH**) — Practitioner/vendor evidence shows the NYSE close is *architected around* floor-broker D-Orders (~40–60% of closing auction volume; enter/modify/cancel until **15:59:50** ET; may flip imbalance either side; incorporated into the public imbalance feed only at **15:55**). That channel is the institutional edge and is **not** a retail order type; IBKR/Rosenblatt-style D-Quote routing is floor-intermediated agency, not something a $1k Alpaca manual book can own. A Nasdaq-style **15:55:10** basis decision-instant is weaker here because most D-Order mass still arrives **after 15:57:30** (NYSE Research Sep-2025; BMLL May-2025), and retail **MOC/LOC freezes at 15:50** (Alpaca rejects CLS after 15:50) so the champion “enter continuous / exit auction print” path cannot be re-armed after the signal. Real-time non-member imbalance redistribution starts at **~$1,000/mo** (Databento NYSE Order Imbalances) — deploy-grade feed fails Gate 4 without user override; historical imbalance alone does not unlock the missing order type.

What would flip it: T1 proof that our retail broker can (a) enter/exit the NYSE close **after** 15:55 without Significant-Imbalance-only restrictions **and** (b) a cheap historical XNYS imbalance backtest shows 15:55:10 |ind_match−mid| ≥10 bps still delivers ≥ champion net after the documented late D-Order flood.

### Mechanism
**Who pays (institutional close):** index / NAV / rebalance MOC flow that *must* print at the official close (price-insensitive); flexible capital and floor clients offset via D-Orders / CO with late information.  
**Why D-Orders persist:** exclusive floor entry window 15:50→15:59:50, no side restriction, discretionary limit, and **5 minutes of opacity** (D-interest not in public imbalance until 15:55) — Databento microstructure and Hu–Murphy document the info/timing privilege explicitly.  
**Why a retail champion-port fails the mechanism:** we cannot *be* the late flexible side; we would be trading a **partial** imbalance snapshot while institutions still inject ~half the auction after our decision, then we cannot freely MOC after 15:50. Overnight reverse of NYSE auction dislocations (Hu–Murphy: ~2× Nasdaq) is a *different* trade and is **out-of-mission** (no overnight).  
**Capacity intuition:** institutional / floor product (billions notional); irrelevant at $10k notional — the binding constraint is **access and decision timing**, not capacity.

### Claims
C1 [CONFIRMED] (T1, NYSE Research 2025-11-18, sample Sep 2025 S&P 500 NYSE-listed): Into the close, **D-Orders ≈60%** of auction interest vs **~20% MOC / ~20% LOC**; D-Order volume surges from ~**15:57:30**; with 100% third-party OMS (from 2025-08-29), share of D-Orders in final **10 seconds** rose **4.45%→13.4%** (Aug 2024→Sep 2025). — https://www.nyse.com/research/insights/nyse-closing-auction-timing-shifts-and-marketability-trends

C2 [CONFIRMED] (T1, NYSE D-Order page / auctions page, current 2026): Closing D-Orders **floor-broker only**; may be submitted/modified/cancelled to **15:59:50**; **no side restriction** (can flip imbalance); MOC/LOC cutoff **15:50** except Significant-Imbalance offset side to 16:00; Closing Offset (CO) offset-only, never adds imbalance. — https://www.nyse.com/article/trading/d-order ; https://www.nyse.com/trade/auctions ; https://www.nyse.com/publicdocs/nyse/NYSE_Auctions_Closing_Process_Fact_Sheet.pdf

C3 [CONFIRMED] (T1/T3, Databento microstructure guide, undated product page; mechanics match NYSE fact sheet): Public NYSE imbalance feed starts ~**15:50** (1s updates); **MOC/LOC in at 15:50**; **D-quote interest only from 15:55** → **15:50–15:55 informational advantage** for floor-routed D-Orders; electronic traders route via floor brokers (e.g. Rosenblatt low-touch). — https://databento.com/microstructure/d-quote

C4 [CONFIRMED] (T2, Hu–Murphy “Vestigial Tails”, SSRN 2020 / Mgmt Sci 2025, sample S&P 500 ~2011–2018 + COVID floor closure): NYSE late floor orders impair auction quality vs Nasdaq — absolute near-price error at **15:54** order-of-magnitude larger on NYSE (~**+100 bps** NYSE coefficient), jumps better at **15:55** when D-Orders enter (~**−45 bps** improvement at incorporation); **overnight reversals ~2×** Nasdaq; quality **improved** when floor closed (COVID) and reverted on reopen. — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3600230 ; slides https://microstructure.exchange/slides/20201006%20Microstructure%20Exchange%20-%20WEB.pdf

C5 [PLAUSIBLE] (T3, BMLL / Traders Magazine 2025-06-24, sample 10 names/venue last 2 weeks May 2025 + 10 NYSE D-Order profile): Nasdaq indicative/mid **converge cleanly ~15:57–15:58**; NYSE shows **more late volatility / slower final convergence**, consistent with D-Order dump; **51%** of inferred D-Order insert volume in **last 3 minutes**; Closing D-Orders **>46%** of NYSE close executed volume as of Aug 2024 (cite to NYSE). CONFLICTED-VENDOR-ish (BMLL sells L3/auction data). — https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

C6 [CONFIRMED] (T1, Databento blog 2025-08-14 + product FAQ): Historical NYSE/Arca/American imbalance available on **XNYS.PILLAR / ARCX.PILLAR / XASE.PILLAR** (`imbalance` schema; history from **2018**); real-time Order Imbalances license **from ~$1,000/mo** vs full Integrated non-display **upwards of ~$7,500/mo**; RT included only on Plus/Unlimited + license. Sample L3 imbalance footprint **~347 B** (tiny vs book) → historical usage-based cost class expected **comparable to owned Nasdaq NOII** (tens of $ for multi-name multi-year), **not** the RT fee. — https://databento.com/blog/NYSE-imbalance-feeds ; https://databento.com/datasets/nyse-integrated

C7 [CONFIRMED] (T1, Alpaca docs): Alpaca **CLS** (MOC/LOC) submitted **after 15:50 ET rejected**; i.e. retail path used today **cannot** place NYSE on-close after the 15:50 freeze (Significant-Imbalance offset path not a reliable retail product). — https://docs.alpaca.markets/us/docs/orders-at-alpaca

C8 [CONFIRMED] (T1, IBKR Campus glossary / Inter-IL note): IBKR surfaces **NYSE Closing Auction D-Quote** as electronic send to **IB’s designated NYSE floor broker** — confirms D-Order is a **brokered floor product**, not a self-directed retail order type on the continuous book. — https://www.interactivebrokers.com/campus/glossary-terms/nyse-closing-auction-d-quote/

C9 [PLAUSIBLE] (T1, NYSE Significant Imbalance 2024-11-04; sample post-2024-10-28 rule change): Significant Imbalance flag (dynamic % of 20d avg close size) extends **offsetting** MOC/LOC to 16:00; NYSE claims **−2.4 bps (−25%)** median slippage compression for flagged symbols post-change — institutional offset opportunity, **not** a free late MOC for either side. — https://www.nyse.com/data-insights/the-nyse-significant-imbalance-enhanced-trading-opportunities-at-the-nyse-closing-auction

C10 [UNVERIFIED] (T3, Massive blog 2026-05-13): Massive WebSocket “NOI” streams NYSE open/close imbalance (qty, paired, indicative) to non-members — latency/pricing for retail not established here; does not grant D-Order entry. — https://massive.com/blog/build-a-nyse-order-imbalance-tracker-with-massives-websocket-api/

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **FAIL** (for champion-parity) | Scheduled 15:55:10 snapshot is **not** a stable decision instant: D-Orders keep reshaping imbalance until 15:59:50; 60% D-volume after 15:57:30. |
| 2 Access | **FAIL** | D-Orders floor-only; retail MOC/LOC hard-stop 15:50 (Alpaca CLS reject); CO/Significant-Imbalance offset only; IB D-Quote = agency floor hop, not our profile. |
| 3 Session | **PASS** (auction flat) | MOC/LOC/CO/D-Order all resolve at 16:00 cross — in-mission **if** order type available. |
| 4 Data | **PASS hist / FAIL RT** | Historical XNYS `imbalance` usage-based: expected **≤$100** Gate-4 class (tiny schema; analog to owned NOII). RT: **≥~$1,000/mo** Order Imbalances — needs user approval. |
| 5 Fill realism | **FAIL** (port of champion) | Auction single-print exit OK in principle, but **cannot reliably enter the auction after signal**; continuous exit reintroduces fill ambiguity the champion avoided. |
| 6 Statistics | **N-A / PASS if hist bought** | NYSE-listed liquid names × years → n≫250 trivial **if** testing only indicative vs close; power not the blocker. |
| 7 Protocol | **FAIL** | Named payer for *our* capture would be “late floor D-Order residual” — we are not that payer and cannot pre-register a D-Order strategy; pre-15:50 MOC is a **different**, lower-info family. |

**Survivor-profile score: 1/5**
1. Single-print/auction execution — **0** (cannot secure auction exit after 15:55 signal on retail NYSE path)
2. Scheduled decision instant pre-positionable — **0** (late D-Order mass after any 15:55 snapshot)
3. Named price-insensitive payer — **1** (index MOC still exists; mechanism real but we cannot sit on the flexible side)
4. Testable ≤~$100 data — **0** as *deploy* story (hist yes; without access, hist is autopsy only) — tally as **0** toward deployable survivor; note hist data itself is Gate-4 friendly
5. Expected effect ≥2× cost at our size — **0** (no practitioner gross for retail NYSE basis; structural drag from incomplete feed)

(If scoring pure *data autopsy* only: point 4 becomes 1 → still **2/5**, ≤2 threshold for extraordinary reason.)

### Economics sketch
- **Expected gross (retail NYSE basis port):** **UNKNOWN / no clean practitioner quote**. Field evidence is *quality degradation and late floor flow*, not a published bps/event edge for non-members trading 15:55 basis into the cross.
- **Hu–Murphy scale (context, not our edge):** near-price error drops by tens of bps when D-Orders hit the feed at 15:55; overnight reverse ~2× Nasdaq — wrong horizon for mission.
- **Our cost burden:** continuous entry spread (taker) + any auction fee passthrough; **no** D-Order fee path. RT data **~$1,000/mo** alone is catastrophic vs ~$10k notional.
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 bps holdout**. Practitioner C finds **no** transferable institutional product that delivers a similar scheduled, single-print, retail-accessible NYSE port; D-Order advantage is **anti-edge** for our side of the book.

### Proposed next test (only if OPEN-TESTABLE)
*(none — verdict is NOT-VIABLE-STRUCTURAL)*

Coverage note if autopsy ever forced: one-time Databento `XNYS.PILLAR` / `imbalance` pull for a NYSE liquid panel (budget ≤$100), measure |ind_match_price − mid| at 15:55:10 vs close and vs 15:59:00 residual after D-Order window — kill if residual noise >> Nasdaq holdout; would **not** restore Access/Latency gates.

### Sources
1. **[T1]** NYSE Research, “NYSE Closing Auction: Timing Shifts and Marketability Trends,” 2025-11-18. https://www.nyse.com/research/insights/nyse-closing-auction-timing-shifts-and-marketability-trends
2. **[T1]** NYSE, “D Orders — The Floor Broker’s modern trading tool.” https://www.nyse.com/article/trading/d-order
3. **[T1]** NYSE Auctions page (cutoffs: MOC/LOC 15:50; D-Orders 15:59:50). https://www.nyse.com/trade/auctions
4. **[T1]** NYSE Closing Process Fact Sheet (MOC/LOC/CO rules). https://www.nyse.com/publicdocs/nyse/NYSE_Auctions_Closing_Process_Fact_Sheet.pdf
5. **[T1]** NYSE, “The NYSE Significant Imbalance…,” 2024-11-04. https://www.nyse.com/data-insights/the-nyse-significant-imbalance-enhanced-trading-opportunities-at-the-nyse-closing-auction
6. **[T1]** Databento, “Introducing real-time NYSE imbalance data,” 2025-08-14 ($1k / $7.5k tiers; XNYS.PILLAR). https://databento.com/blog/NYSE-imbalance-feeds
7. **[T1]** Databento, NYSE Integrated product/FAQ (hist usage-based; imbalance fields). https://databento.com/datasets/nyse-integrated
8. **[T3]** Databento Microstructure, “D-quote” (15:55 incorporation; floor-only; Rosenblatt). https://databento.com/microstructure/d-quote
9. **[T2]** Hu & Murphy, “Vestigial Tails? Floor Brokers at the Close…,” SSRN 3600230 / Management Science 2025. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3600230
10. **[T2/T3]** Hu–Murphy Microstructure Exchange slides, 2020-10-06 (near-price bps, 2× overnight reverse, COVID floor). https://microstructure.exchange/slides/20201006%20Microstructure%20Exchange%20-%20WEB.pdf
11. **[T3]** BMLL / Laible–Thakur, “Into the Close…,” 2025-06-24. https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution
12. **[T1]** Alpaca order docs (CLS reject after 15:50). https://docs.alpaca.markets/us/docs/orders-at-alpaca
13. **[T1]** IBKR Campus, “NYSE Closing Auction D-Quote.” https://www.interactivebrokers.com/campus/glossary-terms/nyse-closing-auction-d-quote/
14. **[T2]** Jegadeesh & Wu, “Closing auctions: Nasdaq versus NYSE,” JFE 2022 (NYSE deeper — complementary quality dimension). https://ideas.repec.org/a/eee/jfinec/v143y2022i3p1120-1139.html
15. **[T3]** Massive, NYSE NOI WebSocket tracker, 2026-05-13. https://massive.com/blog/build-a-nyse-order-imbalance-tracker-with-massives-websocket-api/

#### Queries used
- NYSE closing auction D-Order floor broker institutional how it works 2024 2025
- NYSE closing offset order CO imbalance dissemination retail access
- Databento XNYS NYSE imbalance data cost price
- NYSE vs Nasdaq closing auction quality institutional commentary
- Databento historical NYSE imbalance XNYS.PILLAR pricing cost per GB
- Interactive Brokers D-Order D-Quote NYSE floor broker access retail
- Databento historical imbalance schema cost usage based NYSE XNYS
- Vestigial Tails floor brokers closing auction NYSE price reversal Nasdaq comparison
- Bloomberg NYSE closing auction imbalance feed vendor retail latency
- Databento XNYS.PILLAR imbalance historical price per GB estimate cost
- Alpaca MOC LOC NYSE closing auction order cutoff retail
- Rosenblatt floor broker D-Order electronic routing NYSE closing
