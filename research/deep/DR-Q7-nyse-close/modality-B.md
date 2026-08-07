## DR-Q7 — B primary/venue findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence MED) — Current T1 rules support a Nasdaq-style closing-auction **basis** port: MOC/LOC freeze at 15:50 ET, imbalance 1 Hz from 15:50, Closing D Orders eligible to 15:59:50, and Continuous Book Clearing Price as the NYSE analog of Nasdaq “near.” Databento `XNYS.PILLAR` / `schema=imbalance` is retail-buyable on usage rates with history from May 2018; 10–30 names × 3–6y should clear Gate 4 (≤$100) given ~73 B/msg and ~10 min window. Residual risk is structural late D-Order flow (~60% of D-Order volume after 15:57:30; D-Orders ≈60% of auction interest), plus DMM price discretion within the published band — both reduce signal fidelity vs Nasdaq champion but do not kill testability.

What would flip it: empirical |cont_book_clr − mid| at a pre-registered 15:55:10 (or 15:50/15:58) snapshot fails to predict close−mid with mean ≥~5 bps net of costs on n≥250 events (or Continuous Book Clearing Price is 0 / unusable on most events in owned pull).

### Mechanism
**Who pays:** (1) Index/mutual-fund MOC and rebalance flow that must print the Official Closing Price (price-insensitive); (2) late institutional D-Order agency flow routed via Floor brokers that can create or offset last-minute imbalances. **Why price-insensitive:** tracking mandates and benchmark closing prints dominate; D-Orders are discretionary but client-driven toward the close print. **Why persists:** hybrid Floor + electronic structure is unique to NYSE; D-Order cutoff 10 s before cross and Floor exclusivity create information/timing asymmetry vs continuous-book participants. **Capacity:** retail $1k–$10k whole-share MOC/LOC is a rounding error vs multi-million D-Order/MOC stacks; no capacity gate. **Incumbent advantage:** Floor-broker D-Orders can enter/modify/cancel through 15:59:50 and only partially appear in the public imbalance until late; electronic retail cannot use D-Orders directly (Alpaca has no D-Order; IBKR offers D-Quote via designated Floor broker as low-touch). Hu & Murphy (Mgmt Sci 2025) document stronger post-close reversals on NYSE vs Nasdaq causally linked to late Floor D-Order flexibility — consistent with larger last-minute dislocations (more raw material) **and** noisier pre-close indicative (harder signal).

### Claims
C1 [CONFIRMED] (T1, live 2026-07, ongoing): NYSE Closing Auction timeline — MOC/LOC entry/mod/cancel cutoff 15:50 ET; after 15:50 only offsetting MOC/LOC to a published **Significant** Closing Imbalance until 16:00; Closing D Orders enterable/modifiable until 15:59:50; auction process begins 16:00. — [NYSE Auctions page](https://www.nyse.com/trade/auctions); Rule 7.35 series; NYSE RM-26-03 (2026-03-20).

C2 [CONFIRMED] (T1, 2024-10-28 effective): Significant Closing Imbalance (replaces static 500-round-lot Regulatory Imbalance) at 15:50 if Closing Imbalance ≥ 30%/50%/70% of 20-day Average Closing Size (S&P 500 / 400+600 / other) **and** notional ≥ $200k. — SR-NYSE-2024-13 approved SEC Rel. 34-100327 (2024-06-13); [NYSE Research 2024-11-04](https://www.nyse.com/data-insights/the-nyse-significant-imbalance-enhanced-trading-opportunities-at-the-nyse-closing-auction).

C3 [CONFIRMED] (T1, 2024-06-13 approved): Closing D Orders included in Total Imbalance / Paired / Unpaired beginning **ten minutes** before Core end (15:50), up from five minutes pre-amendment. Pre-2024 hist will show 15:55 D-inclusion. — SEC Rel. 34-100327 / SR-NYSE-2024-13.

C4 [CONFIRMED] (T1, Pillar Imbalances Spec v2.2j 2024-02-22): NYSE closing imbalance feed publishes every 1 s from 15:50 if changed. For NYSE, **IndicativeMatchPrice is always 0**; usable price fields are **ContinuousBookClearingPrice** (price closest to ref where imbalance = 0; default 0 if not reached / regulatory path) and **AuctionInterestClearingPrice** (closing-only interest). Also: ReferencePrice, PairedQty, TotalImbalanceQty, UnpairedQty/Side, ImbalanceSide, SignificantImbalance flag. — [Pillar Order Imbalances Client Spec v2.2j](https://www.nyse.com/publicdocs/nyse/data/Pillar_Order_Imbalances_Client_Specification_v2.2j.pdf).

C5 [CONFIRMED] (T1, 2025-08 / catalog): Databento product = dataset `XNYS.PILLAR`, schema `imbalance` (L3 Imbalance; also `definition`). History from **2018-05-01** (~8 y). Fields map to Pillar: `ref_price`, `total_imbalance_qty`, `paired_qty`, `cont_book_clr_price`, `auct_interest_clr_price`, `ind_match_price` (0 on NYSE), `ssr_filling_price`. Historical = usage-based (metered $/GB; new accounts $125 free credit). Real-time imbalance requires Plus/Unlimited + exchange non-display license (Order Imbalances tier from ~$1,000/mo vs Integrated ~$7,500+/mo) — **not needed for Stage A hist test**. — [Databento NYSE Integrated](https://databento.com/datasets/nyse-integrated); [Databento NYSE imbalance blog 2025-08-14](https://databento.com/blog/NYSE-imbalance-feeds).

C6 [PLAUSIBLE] (T1 + size math, 2026-07): 10–30 NYSE names × 3–6 y of `imbalance` only is expected ≪$100 one-time (msgs ~1/s × ~600 s × ~73 B × ~250 d × n-years; order-of-magnitude tens of MB to low hundreds of MB). Exact $ via `metadata.get_cost` before pull. Free/partial hist: NYSE Auction GUI trailing 3 months for top-1000 auctions (not bulk research-grade); NYSE TAQ Order Imbalances is paid (from 2008). — Databento sample size 347 B; project prior Nasdaq NOII 28-name decade $38.20.

C7 [CONFIRMED] (T1, Alpaca docs live): Alpaca `time_in_force=cls` (MOC/LOC) **rejects after 15:50 ET for all symbols** (NYSE and Nasdaq). Does **not** exploit Nasdaq’s later MOC 15:55 / LOC 15:58 windows. For NYSE-listed, Alpaca cutoff = exchange MOC/LOC cutoff (aligned). No D-Order. IBKR: MOC/LOC to exchange rules; optional D-Quote electronic path to designated Floor broker. — [Alpaca Orders docs](https://docs.alpaca.markets/docs/orders-at-alpaca); IBKR Campus D-Quote glossary.

C8 [CONFIRMED] (T1/T3, NYSE Research 2025-11-18): D-Orders ≈60% of late auction interest (MOC/LOC ~20% each) in NYSE S&P 500 names (Sep 2025); >60% of D-Order volume entered after 15:57:30; final-10-second D-Order share rose 4.45%→13.4% as third-party OMS usage hit 100% (Aug 2024–Sep 2025). — [NYSE Closing Auction Timing Shifts](https://www.nyse.com/research/insights/nyse-closing-auction-timing-shifts-and-marketability-trends).

C9 [PLAUSIBLE] (T2, Hu & Murphy Mgmt Sci 2025 / SSRN; sample incl. COVID floor closure): NYSE closing auction price changes reverse overnight more than Nasdaq; larger last-minute abnormal imbalances (Floor D-Order channel) explain the gap; floor-closure natural experiment supports causality. NO-COST-MODEL for a live taker basis strategy; useful as mechanism evidence of larger dislocations. — [Hu & Murphy 2025](https://pubsonline.informs.org/doi/10.1287/mnsc.2023.00884).

C10 [CONFIRMED] (T1, 2026 FR / SEC): DMM sets Closing Auction Price within last-published Imbalance Reference Price (Exchange Last Sale bound by BBO) and last-published Continuous Book Clearing Price band — i.e., **not** a pure algorithmic cross like Nasdaq; residual DMM discretion inside the disseminated band. — Rule 7.35B(g); SEC Rel. cited in FR 2026-04-29 (e.g. SR-NYSE-2026-11 context).

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **PASS** | Decision instant is scheduled (15:50–15:59 band); 5–25 s manual is pre-positionable before MOC send or continuous-side entry. |
| 2 Access | **PASS** | Alpaca `cls` MOC/LOC available; cutoff 15:50 matches NYSE exchange rule for NYSE-listed. No D-Order needed for basis (enter WITH basis into continuous book, exit at 16:00 cross via MOC/LOC or hold to single print). |
| 3 Session | **PASS** | Flat AT 16:00 cross via MOC/LOC — in-mission exception. |
| 4 Data | **PASS** (pending get_cost) | `XNYS.PILLAR` imbalance hist from 2018; expected ≤$100 for 10–30×3–6y; confirm with `metadata.get_cost` before buy. Real-time not required for Stage A. |
| 5 Fill realism | **PASS** | Exit = Official Closing Price single print (same as champion). Entry = taker continuous book pre-close (same structure as Nasdaq basis). |
| 6 Statistics | **PASS** | 10–30 liquid NYSE names × ~250 sess/y × 3–6y → n ≫ 250; Stage A power OK. |
| 7 Protocol | **PASS** | Named payer (index MOC + late D-Order flow); a-priori |basis| threshold; charges a new trial family (NYSE-close-basis). Holdout spent — use forward/M11-style never-fit names. |

**Survivor-profile score: 4/5**
1. Single-print auction exit — **YES**
2. Scheduled decision instant — **YES** (with late-D noise caveat)
3. Named price-insensitive payer — **YES** (index MOC; D-Order is mixed)
4. Hist testable ≤~$100 — **YES** (expected)
5. Expected effect ≥2× cost burden — **UNKNOWN until Stage A** (structure rhymes with champion +2.5/+12.5 bps; late D-Orders may compress)

### Economics sketch
- Expected gross: **UNKNOWN** (no NYSE-specific basis trial yet). Champion analog: +2.5 bps/event dev / +12.5 holdout. Field: Hu–Murphy stronger NYSE reversals ⇒ potentially **larger** raw close dislocation; late D-Orders ⇒ potentially **weaker** 15:55 indicative→close mapping.
- Our cost burden: zero commission through 2026-12-31; taker spread on entry (SIP mid→touch, megacap ~1–3 bps half-spread); exit at close print (0). Net prior: gross − ~1–3 bps entry − any locates if short.
- Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout**. Promote only if NYSE Stage A net ≥ ~+2 bps/event with n≥250 and no single-name concentration like MU.

### Proposed next test (OPEN-TESTABLE)
- **Hypothesis:** At 15:55:10 ET, if |ContinuousBookClearingPrice − market mid| ≥ 10 bps, entering taker WITH the basis and exiting at the 16:00 Official Closing Price has positive mean bps/event on NYSE-listed liquid names (same structure as Nasdaq champion).
- **Named payer:** Index/rebalance MOC + residual uninformed close flow; late D-Orders as noise/adversary.
- **Data:** Buy Databento `XNYS.PILLAR` `imbalance` (+ SIP/Alpaca mid for basis) for 10–30 NYSE primaries, 2020→2026 (or 2018→). Owned? No. **$:** run `get_cost` first; budget ≤$100. Also pull `mbp-1` or use owned SIP for mid if needed.
- **Universe:** Liquid NYSE Tape A (e.g. mega/large-cap S&P names not in Nasdaq champion set); freeze list pre-test.
- **Expected n & power:** ≥1,500 name-sessions (20 names × 250 × 3y filtered) vs ~20 bps/event noise — adequate for 5–10 bps mean.
- **A-priori thresholds:** |basis|≥10 bps primary; secondary cuts 5/15 bps. Snapshot times pre-reg: 15:50:10, 15:55:10, 15:58:10 (test D-Order inclusion evolution). Drop events where cont_book_clr_price==0.
- **Promotion rule:** Stage A pooled mean net ≥+2 bps/event, 95% CI lower >0, n≥250, no single name >40% of PnL.
- **Kill criteria:** mean ≤0 after costs; or cont_book_clr zero-rate >50% of events; or signal decays to 0 post-2024 D-Order-at-15:50 rule / OMS late-entry regime.
- **Trial family charged:** NYSE-close-basis (new; do not reuse Nasdaq NOII family).

### Sources
1. **[T1]** NYSE Auctions (live) — https://www.nyse.com/trade/auctions — MOC/LOC 15:50, D-Order 15:59:50, 1 s imbalance.
2. **[T1]** Pillar Order Imbalances Feed Client Spec v2.2j (2024-02-22) — https://www.nyse.com/publicdocs/nyse/data/Pillar_Order_Imbalances_Client_Specification_v2.2j.pdf — field dictionary; NYSE IndicativeMatchPrice=0; D-Orders in qty at T−5m (pre-2024 text).
3. **[T1]** SEC Rel. 34-100327 / SR-NYSE-2024-13 (2024-06-13) — https://www.sec.gov/files/rules/sro/nyse/2024/34-100327.pdf — Significant Imbalance; D-Orders into Total Imbalance at T−10m.
4. **[T1]** NYSE Research “Significant Imbalance” (2024-11-04) — https://www.nyse.com/data-insights/the-nyse-significant-imbalance-enhanced-trading-opportunities-at-the-nyse-closing-auction — thresholds; Oct 28 2024 go-live.
5. **[T1]** NYSE Research “Timing Shifts and Marketability Trends” (2025-11-18) — https://www.nyse.com/research/insights/nyse-closing-auction-timing-shifts-and-marketability-trends — D-Order ~60% volume; late entry.
6. **[T1]** NYSE RM-26-03 Q1 2026 Expiration (2026-03-20) — https://www.nyse.com/publicdocs/nyse/markets/nyse/rule-interpretations/2026/Q1_2026_Quarterly_Expiration_RM_3.20.2026.pdf — current Significant Imbalance ops.
7. **[T1]** Databento NYSE Integrated / XNYS.PILLAR — https://databento.com/datasets/nyse-integrated — product, schemas, 2018-05-01 hist, pricing model.
8. **[T1]** Databento “Real-time NYSE imbalance feeds” (2025-08-14) — https://databento.com/blog/NYSE-imbalance-feeds — field map; $1k vs $7.5k license tiers.
9. **[T1]** Databento D-quote microstructure — https://databento.com/microstructure/d-quote — D-Order windows; (note: 3:55 D-inclusion may be pre-2024-amendment).
10. **[T1]** Alpaca Orders / TIF `cls` — https://docs.alpaca.markets/docs/orders-at-alpaca — 15:50 reject for CLS all symbols.
11. **[T2]** Hu & Murphy, “Vestigial Tails? Floor Brokers at the Close…”, Management Science (2025) — https://pubsonline.informs.org/doi/10.1287/mnsc.2023.00884 — NYSE>Nasdaq reverse; D-Order mechanism.
12. **[T1]** BMLL “Into the Close” (2025-06-24) — https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution — cross-venue schedule summary (secondary confirm).
13. **[T1]** NYSE Opening and Closing Auctions Fact Sheet — https://www.nyse.com/publicdocs/nyse/markets/nyse/NYSE_Opening_and_Closing_Auctions_Fact_Sheet.pdf — order-type summary (verify vs live Rule 7.35; older sheets had pre-Pillar times).

#### Queries used
- NYSE Rule 7.35 closing auction MOC LOC D-Orders cutoffs 2024 2025 2026
- NYSE closing auction imbalance dissemination schedule Pillar XDP
- Databento XNYS dataset pricing imbalance closing auction
- SEC filing NYSE closing auction amendments 2023 2024 2025
- NYSE D-Order closing auction window advantage floor broker
- Databento NYSE XNYS schema historical data pricing site:databento.com
- Alpaca MOC LOC order cutoff NYSE closing auction
- Interactive Brokers NYSE MOC LOC cutoff time closing auction
- NYSE closing auction indicative match price when published 3:50 Pillar Imbalance Reference Price
- Databento XNYS.PILLAR imbalance historical cost get_cost schema
- Alpaca market on close order type MOC CLS deadline NYSE
- NYSE free historical closing auction imbalance data sample tool
- "Vestigial Tails" Brogaard NYSE closing auction reversal D-Orders floor broker
- NYSE Rule 7.35B Closing D Orders included imbalance five minutes Continuous Book Clearing Price
- Nasdaq NOII near price zero until 15:55 vs NYSE clearing price when non-zero
- SR-NYSE-2024-13 Closing D Orders ten minutes approved effective date
- Databento historical imbalance schema price per GB XNYS.PILLAR cost estimate
- Nasdaq NOII historical cost per name Databento tens of dollars imbalance
