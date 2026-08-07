## DR-Q4-6 — B primary/venue findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence **HIGH** on exchange mechanics; **MED** on broker-latency/routing edge cases) — Nasdaq exchange cutoffs are definitive: MOC ends **15:55:00 ET**, late LOC **15:55→15:58** (repriced), LOC hard stop **15:58**, cross **16:00**. Continuous book interest (incl. marketable limits/markets resting on Nasdaq) **does** enter the Closing Cross with price standing. Manual retail MOC/LOC is **broker-gated**, not just exchange-gated: Alpaca CLS reject after **15:50**; Schwab/TOS removes MOC/LOC after **15:45**; Fidelity "on the close" before **15:40** and docs claim Nasdaq is not accepted; IBKR Desktop exposes MOC/LOC and cites exchange deadlines (no earlier published internal cutoff found). Post-15:55:10 **basis signal cannot drive MOC** (MOC already closed); late LOC is exchange-legal but **blocked on Alpaca/Schwab/Fidelity** and only plausibly live on IBKR if route latency clears 15:58.
What would flip it: Live paper/live ticket proof that (a) IBKR accepts and fills LOC submitted 15:55:10–15:57:30 on Nasdaq names at retail size, or (b) Alpaca/Schwab extend CLS/MOC-LOC past 15:50/15:45 into the late-LOC window.

### Mechanism
Who pays in the Closing Cross is primarily **price-insensitive MOC/rebalance/index flow** that must print the official close; continuous and late LOC/IO supply offset. That payer is independent of retail MOC availability. For *our* program: the 15:55:10 near-vs-mid basis is only defined after full NOII near/far starts (~15:55), so **MOC entry on that signal is structurally impossible** at the exchange. Continuous marketable at 15:55 can (i) fill in continuous market and/or (ii) rest and participate in the 16:00 cross; it is **not** equivalent to MOC (fill price can differ from NOCP; continuous slippage). Late LOC can target the auction print with a price cap but is reprice-capped to the more aggressive of the 15:50/15:55 reference prices and may go unfilled. Capacity at $1k–$10k is de minimis vs ~10% ADV in the close for liquid Nasdaq names; no retail-size capacity guide is published by the exchange.

### Claims
C1 [CONFIRMED] (T1, Nasdaq Closing Cross FAQ / openclose FAQs, current as of crawl 2026-07; rules in force post-2018 cutoff change): **Nasdaq MOC cutoff is 15:55 ET (not 15:50); LOC entry until 15:58; cancel/modify of MOC/LOC freezes at 15:50** (error-correction only thereafter); IO until 16:00; cross at 16:00 sets NOCP from MOC+LOC+IO+continuous book. — https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf ; https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf

C2 [CONFIRMED] (T1, Nasdaq Closing Cross FAQ): **Late LOC (15:55–15:58)** accepted at limit unless more aggressive than the more aggressive of the 15:50 and 15:55 Reference Prices, in which case **repriced** to that cap; if no crossing interest / no 15:55 Reference Price, late LOC **rejected**. — same ClosingCrossfaq.pdf

C3 [CONFIRMED] (T1, ClosingCrossfaq + openclose FAQs): **Continuous market orders remain enterable until the cross** and are included in the auction with price standing; Near Indicative includes continuous interest, Far is on-close only. MOC fills are **not guaranteed**. — ClosingCrossfaq.pdf Q “How can Auction Imbalances be offset?”; openclose_faqs Q16–17

C4 [CONFIRMED] (T1, SEC/Nasdaq 2018 rule change): Closing Cross Cutoff moved to **15:55** and Late Cutoff to **15:58** (from prior 15:50/15:55 regime). — https://www.federalregister.gov/documents/2018/09/05/2018-19148/... ; SEC Order 34-84454

C5 [CONFIRMED] (T1, Alpaca Orders docs): Alpaca supports MOC/LOC via `time_in_force=cls` (market/limit); **CLS submitted after 15:50 ET and before 19:00 ET is rejected**; after 19:00 queued for next day; unfilled cancelled after close; whole shares only for CLS (not fractional). — https://docs.alpaca.markets/docs/orders-at-alpaca

C6 [CONFIRMED] (T1, Schwab thinkorswim Order Entry docs): TOS offers MOC and LOC for stocks; **must be submitted before 15:45 ET**; after that MOC/LOC disappear from the order-type menu. — https://toslc.thinkorswim.com/center/howToTos/thinkManual/Trade/Order-Entry-Tools

C7 [CONFIRMED] (T1, Fidelity Order Types help): Fidelity “on the close” orders require **minimum 100 shares**, must be placed **before 15:40 ET**; help text states **“Nasdaq does not accept on the close orders”** (as presented on Fidelity’s system). No short/stop with on-close. — https://www.fidelity.com/webcontent/ap002390-mlo-content/19.09/help/learn_order_types_conditions.shtml

C8 [CONFIRMED] (T1, IBKR Campus Desktop lessons): IBKR offers MOC and LOC (no fractional shares); published guidance cites **exchange** cutoffs — Nasdaq MOC **15:55**, LOC **15:58** (cancel/mod after 15:55 restricted), NYSE MOC/LOC **15:50**. No separate earlier IBKR equity MOC internal cutoff found in T1 pages reviewed. — https://www.interactivebrokers.com/campus/trading-lessons/ibkr-desktop-market-on-close-order/ ; …/ibkr-desktop-limit-on-close/

C9 [PLAUSIBLE] (T1 fee schedule + T2 JFQA-style auction impact lit): Nasdaq member **Closing Cross MOC/LOC fees** ~**$0.0008–$0.0012+/share** by MOC/LOC volume tier (retail typically does not see these line items under commission-free; economics land in broker routing/PFOF). Academic/industry notes price impact in closing auctions often **lower** than continuous for non-microcaps; no exchange document sets a retail capacity limit — at $1k–$10k impact is operationally zero on liquid names. — https://www.nasdaqtrader.com/trader.aspx?id=pricelisttrading2 ; Cambridge/JFQA “Price Impact in Closing Auctions…” (2026 abstract)

C10 [CONFIRMED] (T1 synthesis for program): **Manual MOC cannot express the champion 15:55:10 near-price basis** (MOC door closed at 15:55:00; near prices ~0 until ~15:55:00). Continuous marketable at 15:55:10 is the only universally retail-available entry that still reaches the 16:00 single print for exit; late LOC is the only post-signal *auction-only* entry and is **exchange-open but broker-closed** on Alpaca/Schwab/Fidelity.

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **PASS** (scheduled) / **FAIL** for post-signal MOC | Decision instant for full near basis is ≥15:55; 5–25 s manual OK for continuous/late-LOC only if broker still open |
| 2 Access | **PASS** continuous all brokers; **CONDITIONAL** MOC/LOC | IBKR: likely to exchange cutoff; Alpaca CLS≤15:50; Schwab≤15:45; Fidelity≤15:40 + Nasdaq denial + 100-sh min |
| 3 Session | **PASS** | MOC/LOC flat **at** 16:00 cross is in-mission |
| 4 Data | **PASS** | Mechanics need no new data $; auction economics testable on owned NOII + SIP |
| 5 Fill realism | **PASS** auction print; **FAIL** if continuous entry assumed = NOCP | MOC/LOC/cross = single print; continuous entry ≠ guaranteed close |
| 6 Statistics | **N-A** | This charge is execution mechanics, not a new signal family |
| 7 Protocol | **PASS** if testing LOC vs continuous entry | Named mechanism: auction vs continuous entry path on same basis signal |

Survivor-profile score: **4/5** for *using auction exit* (already champion); **2/5** for *MOC entry on 15:55:10 signal* (fails scheduled decision + access on most retail brokers).
1. Single-print/auction: **+1** for MOC/LOC/cross exit  
2. Scheduled decision: **+1** for pre-cutoff MOC; **0** for MOC after 15:55:10 signal  
3. Named payer: **+1** (index MOC flow)  
4. Testable cheap: **+1**  
5. ≥2× cost at size: **+1** if both legs auction; continuous entry still the cost burden of champion  

### Economics sketch
- **Gross**: Unchanged from champion basis (~+2.5 bps/event dev / +12.5 holdout) if entry *and* exit are both at/near NOCP; MOC-entry redesign would need a **pre-15:55** signal (early NOII only — near/far = 0) and is a different hypothesis.  
- **Our cost burden**: Continuous marketable entry ≈ half-spread + adverse selection in last 5 min (champion’s known cost); pure MOC/LOC entry would remove continuous entry cost but **cannot use 15:55:10 near basis**. Late LOC may miss or reprice. Exchange auction fees ≪1 bps on liquid names if passed through; commission-free promo through 2026-12-31.  
- **Net prior**: No improvement path from “switch entry to MOC after signal” — **structurally blocked**. Possible test: pre-15:55 MOC on early NOII (separate family) or IBKR late-LOC vs continuous at 15:55:10.  
- Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout**.

### Proposed next test (only if OPEN-TESTABLE)
**Hypothesis**: On IBKR, a LOC submitted 15:55:10–15:57:00 with limit = mid ± buffer (respecting late-LOC reprice cap) fills at NOCP with fill rate ≥80% on liquid Nasdaq names at 1–50 share size; vs continuous marketable at same clock, auction LOC reduces entry shortfall vs NOCP by ≥1 bps median.  
**Named payer**: Same closing-auction imbalance / basis residual.  
**Data needed**: Owned Databento NOII + SIP; **live/paper IBKR tickets** (ops, $0 data). Optional: log Alpaca CLS reject timestamps to confirm 15:50 hard gate.  
**Universe**: Champion 5 names + M11 liquid subset.  
**Expected n**: Forward only; ≥50 events for fill-rate CI (UNDERPOWERED for economic edge; Stage-A mechanics).  
**A-priori thresholds**: LOC accept rate ≥95% before 15:57:30; fill rate ≥80%; median |fill − NOCP| ≤ 0.5 bps when filled.  
**Promotion rule**: If LOC path beats continuous entry shortfall by ≥1 bps net and is operable under 5–25 s manual on IBKR → amend execution SOP; else keep continuous entry.  
**Kill criteria**: IBKR rejects/reroutes post-15:55 LOC; fill rate <50%; or no economic difference vs continuous.  
**Trial family**: Execution-path / auction-entry subtest of champion (charges open Q4–6 family, not a new alpha family).

### Sources
1. **[T1]** Nasdaq Closing Cross FAQ (PDF) — cutoffs 15:50/15:55/15:58/16:00, late LOC reprice, continuous inclusion, ~10% ADV. https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf (fetched/read 2026-07-17)
2. **[T1]** Nasdaq Opening and Closing Crosses FAQs (PDF) — MOC prior to 15:55; LOC prior to 15:58; reject rules; modify/cancel prior to 15:50. https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf (fetched/read)
3. **[T1]** Federal Register / SR-NASDAQ cutoff change to 15:55 / 15:58 (2018-09-05). https://www.federalregister.gov/documents/2018/09/05/2018-19148/...
4. **[T1]** SEC Order 34-84454 (approving cutoff change). https://www.sec.gov/files/rules/sro/nasdaq/2018/34-84454.pdf
5. **[T1]** Alpaca “Placing Orders” / TIF `cls` — post-15:50 reject. https://docs.alpaca.markets/docs/orders-at-alpaca (fetched/read)
6. **[T1]** Schwab thinkorswim Order Entry — MOC/LOC before 15:45 ET. https://toslc.thinkorswim.com/center/howToTos/thinkManual/Trade/Order-Entry-Tools (fetched/read)
7. **[T1]** Fidelity Order Types and Conditions — on-close before 15:40; min 100 sh; “Nasdaq does not accept on the close orders.” https://www.fidelity.com/webcontent/ap002390-mlo-content/19.09/help/learn_order_types_conditions.shtml (fetched/read)
8. **[T1]** IBKR Desktop MOC / LOC lessons — exchange cutoffs Nasdaq 15:55/15:58, NYSE 15:50; no fractional. https://www.interactivebrokers.com/campus/trading-lessons/ibkr-desktop-market-on-close-order/ ; …/ibkr-desktop-limit-on-close/ (fetched/read)
9. **[T1]** Nasdaq Price List Trading — Closing Cross MOC/LOC per-share fee tiers ~$0.0008–$0.0012+. https://www.nasdaqtrader.com/trader.aspx?id=pricelisttrading2 (fetched)
10. **[T1]** Nasdaq Trader Opening/Closing Crosses hub. https://www.nasdaqtrader.com/trader.aspx?id=openclose
11. **[T2]** Price impact in closing vs continuous auctions (JFQA/Cambridge abstract, 2026) — lower impact in close ex-microcaps. https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/price-impact-in-closing-auctions-opening-auctions-and-continuous-markets-a-benchmark-for-cost-of-trading-on-anomalies/0F72910A79C5B42CF6E85F55164CE846
12. **[T4]** Alpaca forum CLS non-fill discussion (hypothesis only) — thin-name auction non-match; cites 15:58 LOC. https://forum.alpaca.markets/t/why-did-my-limit-order-on-close-cls-not-execute/9929

#### Queries used
1. `Nasdaq LOC MOC cutoff time 15:50 late order rules closing cross`
2. `site:nasdaqtrader.com Market On Close Limit On Close cutoff`
3. `Interactive Brokers MOC LOC order cutoff time retail`
4. `Schwab Fidelity MOC LOC order types cutoff deadline`
5. `Alpaca Markets MOC LOC closing auction order support`
6. `Fidelity "market on close" OR "limit on close" OR MOC OR LOC order cutoff 3:40`
7. `Charles Schwab "market on close" OR MOC OR "on close" order type thinkorswim`
8. `Nasdaq closing cross retail capacity impact MOC order fees auction participation`
9. `IBKR LOC MOC cutoff time Nasdaq 3:55 broker deadline vs exchange`
10. `Schwab thinkorswim MOC LOC cutoff time deadline market on close`
11. `Nasdaq price list MOC LOC closing cross fee per share`
12. `IBKR broker cutoff MOC before exchange 3:50 OR 3:45 internal deadline`
13. `continuous market order participate Nasdaq closing cross 15:55 marketable limit`
