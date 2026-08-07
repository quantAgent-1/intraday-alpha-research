## DR-Q7 — D adversarial findings
### Verdict recommendation
**NOT-VIABLE-STRUCTURAL** (confidence **HIGH**) — Porting the Nasdaq closing-basis edge to NYSE fails on hard market-structure asymmetry, not on a missing backtest. Floor-broker-only Closing D-Orders may be entered, modified, cancelled, or flipped until **15:59:50 ET** and now constitute **~46%+ of NYSE close executed volume**; any outsider snapshot of the public imbalance feed (even post–Aug-2024 full inclusion at 15:50) is therefore adversarially incomplete. Quantities are **round-lot truncated**; indicative clearing fields are often **0** until late; there is no Nasdaq-style locked-near at a scheduled 15:55:10 decision for non-floor participants. Prior-art (Jegadeesh–Wu JFE 2022; Bogousslavsky–Muravyev; Bacidore D-quote literature) treats NYSE MOC-imbalance following as a known, crowded, and partially floor-privileged game. Gate 4 also fails independently: historical NYSE Order Imbalances are ~**$1,000/content-month** (TAQ) / real-time non-display **$1,000–$2,500/mo** — far above ≤$100.

What would flip it: Post-2024-08-12 historical XNYS imbalance + continuous mid showing that a scheduled outsider snapshot (e.g. 15:55:10) still predicts the 16:00 print at ≥2.5 bps net *after* late D-Order path noise, on n≥250, at ≤$100 total data — currently impossible on cost and structurally implausible given 15:59:50 discretionary flips.

### Mechanism
**Who pays (champion story, Nasdaq):** Index/ETF MOC and rebalance flow locks by 15:55; NOII near vs continuous mid is a temporary basis continuous mid is expected to close into the single auction print.

**Why NYSE does not transfer the same residual to outsiders (adversarial):**
1. **D-Order channel is the residual edge, reserved for floor brokers.** D-Orders bypass MOC/LOC side and cancel restrictions; they can *add to or flip* the imbalance until 10 seconds before the cross. Floor interest ≈ 40–46%+ of close volume. Outsiders reading the public feed race against agents who can still rewrite the auction book.
2. **Published imbalance is systematically stale for non-floor.** Even after the Aug 12 2024 change that *includes* already-entered D-Orders in the 15:50 feed (was 15:55), *new/modified* D-Orders continue until 15:59:50 — and Nov 2025 NYSE research shows the share submitted in the final 10 seconds *rose* (to ~13.4%) as OMS automation spread. A 15:50 or 15:55 “basis” for a manual outsider is therefore a lower-bound / mis-signed signal with non-trivial probability.
3. **Coarse fields + weaker near analogue.** Imbalance/paired qty truncated to round lots (e.g. 1575→1500). Continuous-book and closing-only clearing prices default to 0 until a zero-imbalance price is reached. Reference price is last-sale bracketed by bid/offer — not the champion’s near/far clearing construct that appears only after Nasdaq MOC freeze.
4. **Rule changes already harvested early-window advantages.** SR-NYSE-2018-58 / SEC Rel. 34-85021 (approved 2019-01-31) moved MOC/LOC cutoff *and* public imbalance start from **15:45→15:50**, compressing the old early-imbalance arb window. Bacidore (2019) notes this cut the D-quote pre-reveal trading window from 10 min to 5 min. The 2024 D-Order inclusion move (15:55→15:50) further equalized *initial* transparency while leaving late discretionary power intact — i.e. transparency for locked MOC/LOC, privilege for D-Orders.

**Capacity intuition:** At $10k notional, market-impact capacity is fine; *information* capacity is zero for outsiders without floor access. The residual “basis” is either (a) already competed away by public imbalance-followers post-2018 cutoff extensions, or (b) held by floor/D-Order agents who can still flip the book after a retail decision.

### Claims
C1 [CONFIRMED] (T1, NYSE current auction timeline / D-Order product page): MOC/LOC hard cutoff **15:50 ET** (offsetting only thereafter if Significant Imbalance); **Closing D-Orders enterable/modifiable/cancellable until 15:59:50**; no side restriction — D-Orders can flip imbalance direction; eligible Closing D-Orders are added to the imbalance feed (at discretionary range) from **15:50** (post-2024). — https://www.nyse.com/trade/auctions ; https://www.nyse.com/article/trading/d-order

C2 [CONFIRMED] (T1, NYSE Research Aug 29 2024; SR-NYSE-2024-13 / SEC approval Jun 2024): Until **2024-08-09**, Closing D-Orders entered the public Closing Auction Imbalance only at **15:55**; from **2024-08-12** they enter at **15:50**. As of Aug 2024, Closing D-Orders ≈ **46%+** of NYSE close executed volume (ahead of MOC by >8 pp). — https://www.nyse.com/data-insights/nyse-closing-auction-price-discovery-opportunities-reach-new-highs

C3 [CONFIRMED] (T1, NYSE Research Nov 18 2025): After Floor brokers moved to third-party OMS automation (Aug 29 2025), share of D-Orders submitted in the **final 10 seconds** rose from **4.45% → 13.4%** (Aug 2024–Sep 2025); D-Orders ≈ **60%** of open auction interest leading into close in Sep 2025 sample; late D-Order volume uptick from ~15:57:30. — https://www.nyse.com/research/insights/nyse-closing-auction-timing-shifts-and-marketability-trends

C4 [CONFIRMED] (T1, SEC Rel. **34-85021**, File SR-NYSE-2018-58, **2019-01-31**): Approved Rule 123C amendments extending MOC/LOC entry/cancel cutoff and Mandatory/Informational Imbalance Publication from **15:45 → 15:50 ET**. This is the filing that killed the pre-2019 “15:45 early imbalance” outsider window (and, per Bacidore, cut D-quote pre-reveal open-market window from 10→5 min). — https://www.sec.gov/files/rules/sro/nyse/2019/34-85021.pdf

C5 [CONFIRMED] (T1, NYSE Pillar / XDP Imbalances Client Specs): For NYSE, imbalance and paired **quantity fields are truncated to round lots** (explicit example: 1575 shares published as 1500). Continuous Book Clearing Price and Closing-Only Clearing Price **default to 0** until a zero-imbalance price is reached / for regulatory cases. — https://www.nyse.com/publicdocs/nyse/data/Pillar_Order_Imbalances_Client_Specification_v2.2j.pdf ; legacy XDP/Order Imbalances specs

C6 [CONFIRMED] (T1/T3, Databento microstructure + NYSE; Bacidore 2019): D-Orders are floor-broker-only; electronic traders must route an extra hop to a floor broker (Rosenblatt/IBKR NYSEFLOOR etc.). Primary use-case is bypassing MOC/LOC timing and side restrictions, not pure discretionary pricing. Pre-2024 feed inclusion at 15:55 gave D-quote users a documented **5-minute informational advantage** (place D-quote → trade continuous before reveal). — https://databento.com/microstructure/d-quote ; https://www.bacidore.com/post/the-nyse-d-quote-the-disney-fastpass-of-trading

C7 [PLAUSIBLE] (T2, Jegadeesh & Wu, *J. Financial Economics* 2022, sample **2010–2020**): NYSE closing auctions offer more depth than Nasdaq; temporary component of close impact ≈ **62% NYSE / 85% Nasdaq**, fully reversing over **3–5 days**; **“Trading strategies that exploit this price impact and its reversals are significantly profitable”** (institutional, multi-day — out-of-mission for flat-by-close; also prior-art crowding signal for pure imbalance-following). **NO-COST-MODEL / DECAY-UNKNOWN** post-publication for single-session continuous-basis ports. — https://www.sciencedirect.com/science/article/abs/pii/S0304405X21005092 ; abstract also on SSRN 3732955

C8 [PLAUSIBLE] (T2, Jegadeesh & Wu / Bogousslavsky–Muravyev descriptions of imbalance path, samples through ~2018–2020): Nasdaq imbalances drop ~**80%** right after first dissemination then decline gradually; **NYSE imbalances stay nearly flat until ~15:55 then drop sharply when floor/D-Order interest enters the feed** — structural evidence that the *informative* NYSE close interest arrives late via floor, not at the first public MOC snapshot. Floor/D-Order share of NYSE close historically cited ~20–40%+ (rising further post-2022 connectivity). — same JFE paper; Bogousslavsky & Muravyev “Who Trades at the Close” (SSRN 3485840 / JFM 2023)

C9 [PLAUSIBLE] (T2, Brogaard–Ringgenberg–Roesch / “Vestigial Tails? Floor Brokers at the Close…”, SSRN 3600230, Mgmt Sci 2026): Floor-closure natural experiment (COVID) halted D-Orders; authors conclude D-Order may be a **“vestigial tail”** of NYSE structure that **benefits some investors at the expense of others**; NYSE close price changes more likely to reverse vs Nasdaq (greater inefficiency / imperfect competition via exclusive late access). — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3600230

C10 [CONFIRMED] (T1, NYSE Historical Pricing PDF + Databento live license schedule, current): **TAQ NYSE Order Imbalances** historical: **$1,000/data-content-month** for first 12 months of history (+ recurring access fees). Real-time NYSE Order Imbalances non-display via Databento/exchange: **from ~$1,000–$2,500/firm/mo** (Order Imbalances tier; full Integrated non-display upwards of **$7,500/mo**). Project owns Nasdaq NOII historical; **XNYS pillar / NYSE imbalance not purchased**. One year of TAQ history alone ≈ **$12k >> Gate 4 $100**. — https://www.nyse.com/publicdocs/nyse/data/NYSE_Historical_Market_Data_Pricing.pdf ; https://databento.com/blog/NYSE-imbalance-feeds

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **FAIL** | Even if a snapshot were informative, late D-Order flips through 15:59:50 make a 5–25 s manual decision on a 15:50/15:55 print adversarially timed; true auction book is not frozen at decision. |
| 2 Access | **FAIL** | Residual late-entry instrument is D-Order (floor-only). Retail MOC/LOC on NYSE freezes at 15:50 *before* full D-Order path resolves; continuous taker + auction exit inherits same retail CLS problems as DR-Q4-6. |
| 3 Session | **PASS (narrow)** | MOC/LOC flat-at-close is in-mission *if* order reaches the cross — mechanism, not session, is the kill. |
| 4 Data | **FAIL** | Historical NYSE imbalance ≥~$1k/content-month (TAQ) or usage+license via Databento; real-time $1k–$2.5k/mo. Not owned; **>>$100** one-time gate. |
| 5 Fill realism | **FAIL** | Champion fill model (continuous taker @ basis + single-print auction exit) assumes a stable near. NYSE late D-Orders can flip side after entry decision; continuous mid moves into a moving target. |
| 6 Statistics | **N-A** | Structural + data kills precede power; field papers use institutional multi-day reversals, not §1 single-session retail n. |
| 7 Protocol | **FAIL** | Cannot pre-register a named-payer rule that uses *public* NYSE imbalance at a scheduled instant while D-Orders remain free to rewrite the book until 15:59:50; any test that ignores D-Order path is non-causal. |

**Survivor-profile score: 1/5**
1. Single-print/auction execution — **0** (auction exit reachable via MOC only if entered by 15:50 *before* informative late D-Order flow; continuous+auction hybrid fails fill realism)
2. Scheduled decision instant — **1** (clock time is scheduled; but the *state* at that clock is not a sufficient statistic of the auction)
3. Named price-insensitive payer — **0 for outsider capture** (index MOC exists; residual is floor-privileged / already arbed)
4. Historically testable cheaply — **0** (XNYS imbalance not owned; TAQ ≥$1k/mo of history)
5. Expected effect ≥ 2× cost burden at size — **0** (no cited outsider gross ≥ 2× half-spread + late-flip risk; prior art is multi-day institutional)

### Economics sketch
| Line | Gross | Notes |
|------|-------|-------|
| Champion Nasdaq (sim / holdout) | **+2.5 bps/event dev / +12.5 holdout** | Near locked post-15:55; no late discretionary flip channel |
| NYSE outsider public-imbalance basis (this charge) | **UNKNOWN; structural prior ≈ 0 to negative** | Signal incomplete until 15:59:50; D-Order ~half of close |
| Field multi-day impact/reversal (J&W 2022) | “significantly profitable” (inst.) | **Out-of-mission** (overnight/multi-day); crowded post-pub; **DECAY-UNKNOWN** |
| Round-lot truncation + 0 clearing prices | measurement noise | Coarsens small-name signals; zeros kill near-analogue early |
| Data cost (hist. 1y TAQ OI) | ~**$12,000** | vs Gate 4 **$100** |
| Real-time NYSE OI license | **$1,000–$2,500/mo** | vs champion Nasdaq NOII ~$199/mo (also not purchased) |
| **Net prior (adversarial, §1 profile)** | **≤ 0 bps/event** | Structure + cost bind before any backtest |

Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout** rides on Nasdaq’s locked post-15:55 near and the *absence* of a floor D-Order rewrite channel. NYSE is the opposite market design on both dimensions; porting the same rule is not a data exercise, it is a mechanism mismatch.

### Proposed next test (only if OPEN-TESTABLE)
*None — structural.* Optional **instrument-only** (does not promote, does not charge a trial family): if user ever buys ≤$100 of *any* NYSE imbalance slice, measure fraction of sessions where imbalance **side flips** between 15:55:00 and 15:59:50 and the distribution of |Δ paired/imbalance qty| in that window — a base-rate study of signal instability. Kill path already open: if flip rate is material (NYSE’s own charts and late D-Order share imply it is), outsider 15:55:10 basis is non-actionable under §1.

### Sources
1. **[T1]** NYSE Auctions page — 15:50 MOC/LOC cutoff; 15:59:50 D-Order freeze; 1s imbalance dissemination. https://www.nyse.com/trade/auctions (crawled 2026-07)
2. **[T1]** NYSE “D Orders: The Floor Broker’s modern trading tool” — Closing D-Orders at 15:50 on feed; enter/mod/cancel to 15:59:50; can flip imbalance; floor >40% close volume. https://www.nyse.com/article/trading/d-order
3. **[T1]** NYSE Opening and Closing Auctions Fact Sheet — MOC/LOC/CO/D-Order rules; Significant Imbalance offset path. https://www.nyse.com/publicdocs/nyse/markets/nyse/NYSE_Opening_and_Closing_Auctions_Fact_Sheet.pdf
4. **[T1]** SEC Release No. **34-85021** (SR-NYSE-2018-58), **2019-01-31** — Rule 123C: extend cutoffs and imbalance publication **15:45→15:50**. https://www.sec.gov/files/rules/sro/nyse/2019/34-85021.pdf
5. **[T1]** NYSE Research, Bazinas, **2024-08-29** — D-Order feed inclusion moved 15:55→15:50 effective **2024-08-12**; D-Orders >46% close volume. https://www.nyse.com/data-insights/nyse-closing-auction-price-discovery-opportunities-reach-new-highs
6. **[T1]** NYSE Research, **2025-11-18** — OMS automation; final-10s D-Order share 4.45%→13.4%; ~60% of open interest D-Orders. https://www.nyse.com/research/insights/nyse-closing-auction-timing-shifts-and-marketability-trends
7. **[T1]** NYSE Pillar Order Imbalances Client Spec v2.2j — qty truncated to round lots; clearing prices default 0. https://www.nyse.com/publicdocs/nyse/data/Pillar_Order_Imbalances_Client_Specification_v2.2j.pdf
8. **[T1]** NYSE Historical Market Data Pricing — TAQ NYSE Order Imbalance **$1,000/data content month** (first 12 mo). https://www.nyse.com/publicdocs/nyse/data/NYSE_Historical_Market_Data_Pricing.pdf
9. **[T1]** Databento — NYSE Order Imbalances real-time license **from ~$1,000/mo**; Integrated non-display **~$7,500+/mo**; hist. via usage. https://databento.com/blog/NYSE-imbalance-feeds ; https://databento.com/datasets/nyse-integrated
10. **[T1/T3]** Databento Microstructure “D-quote” — floor-only; pre-2024 15:55 feed inclusion; cancel-to-15:59:50; gaming example. https://databento.com/microstructure/d-quote
11. **[T3]** Bacidore, **2019-07-22** — “The NYSE D-Quote: The Disney Fastpass of Trading”; 15:45→15:50 reduced D-quote relative value; greater impact of large D-quotes (cites Bacidore–Polidore–Xu *J. Trading* 2014). https://www.bacidore.com/post/the-nyse-d-quote-the-disney-fastpass-of-trading
12. **[T2]** Jegadeesh & Wu, *JFE* **2022** — Closing auctions Nasdaq vs NYSE; depth, 62%/85% temporary impact, 3–5d reversal, profitable impact/reversal strategies; sample **2010–2020**. https://doi.org/10.1016/j.jfineco.2021.12.003
13. **[T2]** Bogousslavsky & Muravyev, “Who Trades at the Close…”, SSRN 3485840 / *J. Financial Markets* **2023** — auction deviations, D-quote exclusive access, last-5-min volume migration. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840
14. **[T2]** Brogaard, Ringgenberg, Roesch, “Vestigial Tails? Floor Brokers at the Close…”, SSRN **3600230** / *Management Science* **2026** — D-Order as vestigial privilege; floor-closure experiment. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3600230
15. **[T1]** NYSE Closing Auction Dynamics **2023-10-11** — D-Orders to 15:59:50; >2/3 of D-Orders in last ~5 min of entry window. https://www.nyse.com/data-insights/nyse-closing-auction-dynamics-2023
16. **[T1]** Project AGENT_BRIEF — owned Nasdaq NOII; XNYS pillar **not purchased**; Gate 4 ≤$100; champion mechanics.

#### Queries used
- NYSE closing auction imbalance floor broker discretionary access D-Order
- NYSE Rule 123C closing auction imbalance dissemination schedule cutoff
- NYSE closing auction rule change 15:50 15:55 imbalance advantage SEC filing
- NYSE imbalance feed field rounding reference price paired quantity precision
- "closing auction" NYSE imbalance following strategy arbitrage decay 2018 2019
- Vestigial Tails Floor Brokers Close D-Orders Clark-Joseph SSRN
- Databento NYSE XNYS imbalance feed historical price cost
- NYSE Closing D Order imbalance inclusion 15:55 vs 15:50 SR-NYSE-2024
- Bacidore Cost of the D-Quote NYSE closing auction
- Jegadeesh Wu Closing auctions Nasdaq versus NYSE price impact reversal sample period
- NYSE Pillar order imbalances clearing price initially 0 continuous book clearing price
- Databento historical NYSE order imbalances pricing per GB OR usage cost
- TAQ NYSE Order Imbalances historical pricing cost per month
