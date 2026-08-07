## DR-Q8 — B primary/venue findings

### Verdict recommendation
**OPEN-TESTABLE** (confidence **HIGH**) — Nasdaq-listed ETFs (QQQ, SMH, etc.) use the **same** Closing Cross + NOII product, schedule, MOC/LOC/IO eligibility, and Databento `XNAS.ITCH` / `imbalance` schema as Nasdaq equities. Near/far indicative prices populate only from **~15:55 ET** (every 1s thereafter), identical to the champion. The only load-bearing ETP-specific rule is a **tighter price collar** on the cross (3% if ETP >$50.01; greater of 5% or $0.50 if ≤$50 vs 10%/$0.50 equities). Creation-unit size does **not** constrain secondary-market MOC/LOC on the exchange. Champion structure is portable once QQQ/SMH (and peers) NOII history is on disk.

What would flip it: Discovery that Databento does **not** emit Closing Cross `imbalance` records with populated `cont_book_clr_price` (near) for QQQ/SMH at 15:55:10 on a non-trivial fraction of sessions, or that retail brokers reject MOC/LOC on these symbols after a T1-verified cutoff earlier than Nasdaq's.

### Mechanism
**Who pays:** Same class as champion — price-insensitive on-close flow (index/ETF rebalancers, mutual-fund cash windows, derivatives settlement, MOC basket traders) that must print at the official close. For ETFs the *secondary* auction still clears MOC/LOC/IO + continuous book at a single NOCP; APs separately create/redeem in primary market against NAV and can arbitrage ETF vs underlyings, which tends to **reduce** auction share of ADV vs single-name equities but does not eliminate price-insensitive residual imbalance.

**Why price-insensitive:** Benchmarking to NOCP / index close; MOC must fill at the cross price; cutoffs lock MOC after 15:55 so residual imbalance is inelastic.

**Why persists:** Closing Cross is the official NOCP setter for Nasdaq-listed ETPs; index/ETF product design keeps end-of-day demand recurring. Tighter ETP collars *constrain* extreme prints but do not remove imbalance or NOII transparency.

**Capacity intuition:** Liquid Nasdaq ETPs (QQQ, SMH) have large absolute close volume; retail $1k–$10k is negligible. Thin ETPs risk odd-lot-only or no-cross NOCP (T-WAM fallback) — exclude those; QQQ/SMH are not in that set.

### Claims
C1 [CONFIRMED] (T1, FAQ copyright 2025 / openclose_faqs 2025, mechanics ongoing): **All nationally-listed securities are eligible for Nasdaq Opening and Closing Crosses**; QQQ/SMH as Nasdaq-listed ETPs are in-scope for the same Cross process as equities. — Nasdaq Trader Opening/Closing Crosses page; openclose_faqs.pdf Q1 (“All nationally-listed securities are eligible for the Crosses.”) https://www.nasdaqtrader.com/trader.aspx?id=openclose ; https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf

C2 [CONFIRMED] (T1, Closing Cross FAQ 2025 / ITCH 5.0, schedule ongoing): **Closing NOII schedule is identical for ETPs and stocks**: dissemination from **15:50 ET** every **10 s** (paired, imbalance side/qty, current reference price); from **15:55–16:00** every **1 s** with **Near** and **Far** indicative clearing prices; Cross at **16:00**. — https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf ; ITCH v5.0 §1.6 https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf

C3 [CONFIRMED] (T1, Closing Cross FAQ 2025): **MOC/LOC/IO eligibility cutoffs are not ETF-specific**: MOC accepted until **15:55** (no cancel/mod after 15:50); LOC until **15:58** (late LOC reprice rules vs 15:50/15:55 reference prices); IO until **16:00**. Same order types for all Cross-eligible securities. — https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf ; openclose_faqs.pdf On-Close / IO sections

C4 [CONFIRMED] (T1, System Settings + openclose_faqs Q3–Q4 + ETA 2022-63): **ETP-only tighter Closing Cross thresholds**: Closing Cross collar **3% for ETPs >$50.01**; **greater of 5% or $0.50 for ETPs ≤$50.00** (equities remain greater of 10% or $0.50). Opening ETP collar greater of 5% or $0.50. Methodology otherwise same (threshold applied vs QBBO). — https://www.nasdaqtrader.com/Trader.aspx?id=SYSTEMSETTINGS ; openclose_faqs.pdf ; https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2022-63

C5 [CONFIRMED] (T1, SR-NASDAQ-2025-047 / FR 2025-07-02, operative ~July 2025): **ETP-specific NOCP fallback (Rule 4754(b)(4))**: if a Nasdaq-listed ETP has **no Closing Cross**, or Closing Cross trade **&lt; one round lot**, NOCP = **time-weighted average midpoint (T-WAM) of NBBO** (last two minutes detail in rule), not the odd-lot cross print. Round-lot+ Closing Cross still sets NOCP. Irrelevant for QQQ/SMH liquidity; material only for thin ETPs. — https://www.federalregister.gov/documents/2025/07/02/2025-12301/self-regulatory-organizations-the-nasdaq-stock-market-llc-notice-of-filing-and-immediate

C6 [CONFIRMED] (T1, ITCH 5.0 NOII message “I”): **Near/Far semantics (champion basis inputs)**: Far Price = hypothetical auction-clearing price for **cross orders only**; Near Price = hypothetical auction-clearing for **cross + continuous** orders; Current Reference Price = price at which paired/imbalance quantities are calculated within Nasdaq BBO maximizing paired, then minimizing imbalance, then distance to midpoint. Cross Type `"C"` = Closing Cross. — ITCH v5.0 pp.18–19 https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf

C7 [CONFIRMED] (T1, Databento catalog + XNAS.ITCH docs + imbalance schema refs, 2022–2025): **Databento maps Nasdaq NOII into schema `imbalance` on dataset `XNAS.ITCH` for all Nasdaq TotalView symbols (including listed ETPs)** — no separate ETF NOII product. Normalized fields used for pricing: `ref_price` ← Current Reference Price; `cont_book_clr_price` ← Near (cross+continuous); `auct_interest_clr_price` ← Far (cross only); `paired_qty`; `total_imbalance_qty` (+ side/status enums). Vendor note: `auct_interest_clr_price` / `cont_book_clr_price` **not populated until after 15:55** (and 9:28 open), matching ITCH near/far schedule. — https://databento.com/datasets/XNAS.ITCH ; https://databento.com/docs/venues-and-datasets/xnas-itch ; https://databento.com/docs/schemas-and-data-formats/imbalance ; https://databento.com/catalog/us-equities

C8 [CONFIRMED] (T1, FAQ example + ITCH schedule + project known): **Near and Far are 0 / unpopulated before ~15:55** in disseminated NOII (FAQ example shows Near/Far $0 at 15:50 print; near/far fields begin with 1s cadence at 15:55). Champion decision instant **15:55:10** is valid for ETPs under the same feed. — ClosingCrossfaq.pdf example block; ITCH §1.6

C9 [CONFIRMED] (T1 exchange rules silence + openclose eligibility): **No exchange rule ties MOC/LOC size or eligibility to ETF creation-unit (basket) size.** Creation/redemption is primary-market AP process; secondary Closing Cross accepts share-level MOC/LOC/IO like any equity. Creation-unit constraints do **not** affect retail close eligibility or NOII pricing mechanics. — openclose_faqs.pdf eligibility/order sections; Rule 4754 framework as summarized in SR-NASDAQ-2025-047 (no CU linkage)

C10 [PLAUSIBLE] (T1 secondary / T3 color only for magnitude): **ETF auction share of ADV is often lower than single-name equities** because APs can hedge via underlyings MOC and create/redeem to NAV — structural dampener on residual secondary imbalance, not a rules block. Magnitude not quantified on Nasdaq QQQ/SMH in T1 docs read here (BMLL 2025 cites ~2% auction share for Arca ETFs vs ~9% NYSE equities — different listing venue; treat as hypothesis for economics modality). — BMLL “Into the Close” 2025-06-24 (T3) https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **PASS** | Decision at scheduled 15:55:10 snapshot; 5–25 s manual entry is pre-positionable; exit is 16:00 single print |
| 2 | Access | **PASS** | MOC/LOC are standard Nasdaq on-close types; retail brokers that already support champion names typically support QQQ/SMH (broker cutoff still to verify at T1 broker docs outside this charge) |
| 3 | Session | **PASS** | Flat at 16:00 cross via MOC/LOC — in-mission |
| 4 | Data | **PASS** | Same Databento `XNAS.ITCH` imbalance product already used for equities; historical NOII ~tens of $/name-decade per project notes; no new recurring feed required for Stage A |
| 5 | Fill realism | **PASS** | Single-print auction exit; entry is continuous taker at mid/basis (same structure as champion) |
| 6 | Statistics | **PASS** | Liquid daily closes → n ≥ 250 events / ≥ 150 sessions on multi-year history is feasible for QQQ/SMH alone |
| 7 | Protocol | **PASS** | Named payer (on-close price-insensitive flow) + a-priori |basis|≥10 bps threshold portable; charges a new or existing auction-family trial (not a dead list item) |

**Survivor-profile score: 5/5**
1. Single-print/auction execution — **yes**
2. Scheduled decision instant — **yes** (15:55:10)
3. Named price-insensitive payer — **yes** (MOC/index/close-benchmark flow)
4. Historically testable on owned/≤~$100 data — **yes** (Databento imbalance; same SKU)
5. Expected effect ≥ 2× cost burden at size — **presumed portable** from champion; Stage A must re-estimate ETF residual (C10 dampener is the main economic risk, not mechanics)

### Economics sketch
- **Expected gross:** Unknown a priori for QQQ/SMH; mechanics do not guarantee equity-name bps. Champion reference: **dev ≈ +2.5 bps/event**, holdout **+12.5 bps/event [6.9, 18.5], n=140**. ETF residual may be **smaller** if AP arbitrage compresses basis (C10).
- **Our cost burden:** Same structure — continuous taker entry + auction exit; zero commission through 2026-12-31 promo; stress post-promo separately. Spread/impact at $10k notional on QQQ/SMH is typically well under a few bps.
- **Net prior:** Mechanics **do not block** champion net; **economics unproven until Stage A** on ETF NOII. Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout**.

### Proposed next test (OPEN-TESTABLE)
- **Hypothesis:** At 15:55:10 ET, for Nasdaq-listed liquid ETPs (QQQ, SMH, optionally SOXX/QQQM), |NOII near − market mid| ≥ 10 bps predicts signed close print vs entry mid with mean gross ≥ +2 bps/event after costs (portable champion rule).
- **Named payer:** On-close MOC/LOC and benchmark-sensitive flow into Nasdaq Closing Cross; AP arb is a competing stabilizer, not the payer.
- **Data needed:** Databento `XNAS.ITCH` schema `imbalance` (+ mid from owned SIP/MBP) for QQQ/SMH over 2020→ present. **Owned pattern cost:** ~tens of $ per name-decade (M11 precedent $38.20/28 names). Real-time NOII ≈ $199/mo **not required** for Stage A.
- **Universe:** QQQ, SMH primary; optional liquid Nasdaq ETPs with round-lot closes daily.
- **Expected n & power:** ~250–1,000+ sessions × 2 names; against ~20 bps/event noise, mean +2.5 bps needs large n — power-check before promotion; flag UNDERPOWERED if |basis|≥10 bps fires &lt;~150 times.
- **A-priori thresholds:** Signal if |near/mid − 1| ≥ 10 bps at first NOII snapshot ≥ 15:55:10 with near &gt; 0; side = sign(near − mid); enter taker with basis; exit at Closing Cross print (Cross Type C / NOCP when cross ≥ round lot).
- **Promotion rule:** Stage A pooled mean net ≥ +2 bps/event, hit-rate ≥ 55%, n ≥ 250, no single-name concentration &gt;50% of total PnL; then register Stage B OOS family.
- **Kill criteria:** Mean net ≤ 0 after costs; near unpopulated &gt;5% of sessions; or basis events &lt;100 over full history.
- **Trial family charged:** New **auction-ETF / M11-adjacent** family (extension of Nasdaq closing basis; not a dead-list rehash).

### Sources
1. **[T1]** Nasdaq Closing Cross FAQ (2025 copyright on extracted text). https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf
2. **[T1]** The Nasdaq Opening and Closing Crosses FAQs (openclose_faqs.pdf, 2025 footer). https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf — eligibility, ETP thresholds, order cutoffs, NOII fields.
3. **[T1]** Nasdaq Trader — Opening and Closing Crosses. https://www.nasdaqtrader.com/trader.aspx?id=openclose — all nationally-listed securities eligible; NOII 15:50–16:00.
4. **[T1]** Nasdaq System Settings — Opening/Closing Cross thresholds including **For Exchange Traded Products (ETPs) Only**. https://www.nasdaqtrader.com/Trader.aspx?id=SYSTEMSETTINGS
5. **[T1]** Equity Trader Alert #2022-63 (2022-07-05) — Tighten Cross Thresholds for ETPs. https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2022-63
6. **[T1]** Nasdaq TotalView-ITCH Specification v5.0 — §1.6 NOII message (Near/Far/Ref/Paired/Imbalance/Cross Type C). https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf
7. **[T1]** Federal Register / SR-NASDAQ-2025-047 (2025-07-02) — Rule 4754(b)(4) ETP NOCP when no cross or odd-lot-only cross → T-WAM. https://www.federalregister.gov/documents/2025/07/02/2025-12301/self-regulatory-organizations-the-nasdaq-stock-market-llc-notice-of-filing-and-immediate
8. **[T1]** Databento XNAS.ITCH product + US Equities catalog — NOII via TotalView; `imbalance` schema. https://databento.com/datasets/XNAS.ITCH ; https://databento.com/catalog/us-equities
9. **[T1]** Databento docs (imbalance schema; XNAS.ITCH venue page) — field names `cont_book_clr_price` / `auct_interest_clr_price` / `ref_price`; near/far unpopulated before 15:55. https://databento.com/docs/schemas-and-data-formats/imbalance ; https://databento.com/docs/venues-and-datasets/xnas-itch
10. **[T1]** Databento blog “Introducing real-time NYSE imbalance data” (2025-08-14) — normalized imbalance field dictionary (also documents Nasdaq-style near/far mapping language). https://databento.com/blog/NYSE-imbalance-feeds
11. **[T3, non-load-bearing for mechanics]** BMLL “Into the Close…” (2025-06-24) — auction share / Arca ETF vs equity comparison. https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

#### Queries used
- `Nasdaq ETF closing cross auction NOII schedule QQQ`
- `NasdaqTrader closing cross MOC LOC ETF eligibility rules`
- `Databento NOII schema ETF Nasdaq imbalance`
- `Nasdaq Rule 4754 Closing Cross ETF exchange traded product`
- `Nasdaq ETF closing auction creation unit MOC vs stocks difference`
- `site:databento.com imbalance schema near_price far_price NOII fields`
- `Nasdaq Rule 4754 ETP closing cross threshold 3% site:sec.gov OR site:nasdaqtrader.com`
- `QQQ SMH Nasdaq listed ETF Closing Cross TotalView NOII same as equity`
- `Databento imbalance schema fields near_price far_price ref_price paired_qty`
- `Nasdaq TotalView ITCH NOII message format near far indicative clearing price`
- `Nasdaq Rule 4754 Closing Cross MOC LOC all securities eligible ETF`
- `Databento XNAS.ITCH imbalance near_price far_price continuous book clearing`
- `"cont_book_clr_price" OR "auct_interest_clr_price" databento nasdaq OR near_price`
- `site:github.com databento ImbalanceMsg near_price far_price`
