## DR-X5 — B primary/venue findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence **HIGH** on mechanics parity; **MED** on pilot economics until measured) — Nasdaq Closing Cross / NOII **rules are identical for mid/small-cap names**: same 15:50 modify freeze, 15:55 MOC cutoff, 15:55–15:58 late LOC, 15:58 LOC hard stop, 16:00 cross; same NOII cadence (3:50–3:55 every 10s reference/paired/imbalance; 3:55–4:00 every 1s + near/far); **all nationally-listed securities are eligible**. Degradation is **not rule-tiered** but **activity-conditioned**: (i) near/far remain 0 until ~15:55 (universal, not thin-only); (ii) thin books can show imbalance side **O** (insufficient interest) and can fail to produce a Closing Cross, in which case **NOCP = last regular-way last-sale**; (iii) LULD bands are wider for Tier 2 (most mid/small outside R1000/SP500) and double in the last 25 minutes for Tier 1 and for Tier 2 priced ≤$3; a pause existing at/after **3:50** routes to **LULD Closing Cross** (Rule 4754(b)(6)), not a free continuous close. Execution fees on the Closing Cross are **member volume tiers A–G ($0.0008–$0.0016/sh for MOC/LOC)**, not security liquidity tiers — irrelevant as a retail line item under commission-free, but continuous-book/IO in the cross is flat **$0.0011**. Free PIT mid/small membership is **partially available** (iShares IJH/IJR asOfDate holdings snapshots + ADV screens); full official S&P/Russell reconstitution histories are **not free**.

What would flip it: Measured pilot on ~20 Nasdaq-primary names in the $20–200M ADV band showing net |near−mid| basis **≤ 1× half-spread** at 15:55:10 (net prior ≤0 after entry cost) **or** near-price availability / cross-occurrence rate too low to reach n≥250.

### Mechanism
Who pays: same structural payer as the champion — **price-insensitive MOC / index-rebalance / benchmark-close flow** that must print the primary-listing official close. Mid/small S&P 400/600 and Russell constituents still face that force on rebalance and daily index-NAV windows; absolute MOC size is smaller but **fraction of ADV** can be larger. Why it persists: passive/benchmark mandates and official-close marking are rule-driven, not discretionary. Capacity at $1k–$10k is de minimis vs even thin-name close volume (the thesis: smallness is the edge). Venue mechanics do **not** strip the toolset as liquidity falls — they strip **signal quality** when on-close interest is too sparse for a stable near price or when LULD pauses convert the close into a special auction.

### Claims
C1 [CONFIRMED] (T1, Nasdaq Opening/Closing Crosses FAQ, ©2025/1608-25, rules in force): **All nationally-listed securities are eligible for the Opening and Closing Crosses** with identical order types and cutoffs: MOC prior to **15:55**; late LOC **15:55–15:58** (reprice to more aggressive of 15:50/15:55 Reference Prices; reject if no 15:55 Reference Price / no crossing interest); LOC hard cutoff **15:58**; modify/cancel of on-close freezes **15:50**; IO and continuous book participate; MOC **not guaranteed**. No mid/small exemption or alternate schedule. — https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf

C2 [CONFIRMED] (T1, same FAQ Q7–8 + ITCH product docs): **NOII dissemination schedule is universal, not liquidity-tiered**: 15:50–15:55 every **10s** (Current Reference Price, Paired Shares, Imbalance Shares/Side); **15:55–16:00 every 1s** adding **Near** (cross + continuous) and **Far** (on-close only). Near/far are defined only in the last 5 minutes — consistent with owned 2020–2026 observation that near/far = 0 until ~15:55. — openclose_faqs.pdf; https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTV-ITCH-V3_2.pdf (and ITCH 5.0 product overview)

C3 [CONFIRMED] (T1, openclose FAQ Q6 / cross price steps): **If a stock does not have a Closing Cross, NOCP = last regular-way last-sale-eligible trade prior to 16:00**. Cross optimization order is maximize shares → minimize imbalance → minimize distance to Nasdaq inside midpoint — independent of market-cap tier. Thin names with insufficient on-close interest can **skip the single-print auction path** entirely (exit becomes continuous last sale — fills champion structure). — openclose_faqs.pdf

C4 [CONFIRMED] (T1, Nasdaq NOIS v2.10 spec, 2015 still the newswire product rule): **NOIS (newswire snapshot) filters to ≥50,000 imbalance shares** at open/close snapshots; **TotalView / NOIView / Databento XNAS.ITCH carry the full NOII range without that 50k gate**. Thin-name research must use TotalView-class NOII (owned path), not NOIS. Imbalance Direction can be **O = insufficient orders to calculate**. — https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/nois-v2_1.pdf

C5 [CONFIRMED] (T1, Nasdaq Price List — Trading, current as of fetch 2026-07-18): **Closing Cross MOC/LOC fees are member-activity tiers, not security tiers**: Tier A $0.0008 … Tier F $0.0016 per executed share (MOC/LOC volume or add-liquidity % of Consolidated Volume); Tier G $0.0010 (options-linked); **Imbalance-only and Continuous Book in the Closing Cross = $0.0011 flat**. No published higher fee for Capital Market / small-cap symbols. Retail under commission-free does not see these line items. — https://www.nasdaqtrader.com/trader.aspx?id=pricelisttrading2

C6 [CONFIRMED] (T1, LULD Plan site + Nasdaq LULD FAQ + Investor.gov): **LULD applies 9:30–16:00 to Tier 1 (S&P 500, Russell 1000, select ETPs) and Tier 2 (all other NMS ex rights/warrants)**. Percentage parameters by price and tier; **bands double in the last 25 minutes (from 15:35)** for all Tier 1 and for Tier 2 priced ≤$3.00; Tier 2 >$3 remains **10% all day including close**. Limit state 15s → 5-minute Trading Pause. **If a security is in a Trading Pause during the last 10 minutes of RTH, the primary listing exchange will not reopen continuous trading and will attempt a closing transaction under established closing procedures.** — https://www.luldplan.com/ ; https://www.nasdaqtrader.com/content/MarketRegulation/LULD_FAQ.pdf ; https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-market-circuit-breakers

C7 [CONFIRMED] (T1, Nasdaq Equity Rule 4120 / 4754 references via Listing Center + SEC LULD Closing Cross materials): **LULD pause existing at or after 15:50 → re-open via LULD Closing Cross under Rule 4754(b)(6)**; non-LULD trading halt at/after 15:50 → Hybrid Closing Cross 4754(b)(7). Insufficient interest for LULD Closing Cross → **no cross; NOCP = last sale on Nasdaq**. Mid/small (mostly Tier 2) have **wider ordinary bands** but still face last-10-minute pause → special closing auction path; pilot must **exclude or flag LULD-paused sessions** as a separate state (basis signal / continuous entry may be invalid). — https://listingcenter.nasdaq.com/rulebook/nasdaq/rules/Nasdaq%20Equity%204 ; https://www.sec.gov/files/rules/sro/nasdaq/2017/34-81188-ex5.pdf ; SR-NASDAQ LULD Closing Cross notices

C8 [CONFIRMED] (T1, iShares product pages + BlackRock holdings Excel endpoints, observed 2026-07): **Free point-in-time mid/small membership proxies exist as ETF holdings snapshots**: iShares **IJH** (S&P MidCap 400) and **IJR** (S&P SmallCap 600) expose multi-date holdings (`asOfDate` month-end + recent dailies) and Excel/CSV download via product page / varnish-api `get-fund-document` with `component=holdings` or `fundDownload`. Same pattern for MDY/SPSM (SPDR). This is **not** official S&P DJI reconstitution tape; weights track the index closely enough for **universe construction**, not for precise passive-flow notional. — https://www.ishares.com/us/products/239763/ishares-core-s-p-mid-cap-etf ; https://www.ishares.com/us/products/239774/ishares-core-sp-smallcap-etf

C9 [CONFIRMED] (T1 gap / commercial reality): **Official free bulk historical S&P 400/600 and Russell 2000 reconstitution membership files are not published** by S&P DJI / FTSE Russell for 2020–2026; Wikipedia/current lists are **point-in-time only** (survivorship risk if used as static universe). Paid alternatives (EODHD index constituents ~£30/mo, Bloomberg, Compustat) exist. **Survivorship-safe free recipe = ADV + primary-listing screen at each selection date**, optionally **seeded** by IJH/IJR holdings on that `asOfDate`, not by a frozen 2026 Wikipedia list. — S&P/FTSE product pages (no free hist constituents API); EODHD S&P historical constituents marketing

C10 [PLAUSIBLE] (T1 mechanics + program-owned NOII cost model): **Pilot data cost for ~20 never-fit Nasdaq-primary names ≈ $15–$55 one-time** depending on history depth (~$0.45/name-year Databento NOII; M11 28-name precedent $38.20). Continuous SIP ticks for 15:55 mid may use owned Alpaca SIP for overlap names or Databento BBO — still within ≤$100 gate if scoped. Mechanics do not block; **power and net-of-spread do**.

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **PASS** | Same scheduled 15:55:10 decision instant as champion; 5–25 s manual pre-positionable |
| 2 Access | **PASS** continuous entry; **CONDITIONAL** MOC/LOC | Same broker gates as DR-Q4-6 (Alpaca CLS ≤15:50; Schwab ≤15:45; Fidelity ≤15:40; IBKR nearer exchange). Thin names: odd-lot / whole-share OK at $5–$50; Fidelity 100-sh min may bind on high-priced midcaps |
| 3 Session | **PASS** | Auction exit at 16:00 still in-mission; LULD Closing Cross still a single print when it occurs |
| 4 Data | **PASS** | NOII ~$0.45/name-year × 20 × years ≤~$100 for Stage A; membership free via IJH/IJR + ADV |
| 5 Fill realism | **PASS** if exit is cross print; **FAIL path** if no-cross last-sale | Must condition on Closing Cross occurrence (paired qty / cross trade present); continuous entry ≠ NOCP |
| 6 Statistics | **PASS** designable | 20 names × ~250 sessions/year × event rate ~0.2–0.4 (10 bps basis filter) → n can clear 250 if rate holds; UNDERPOWERED if thin names fire rarely |
| 7 Protocol | **PASS** | Named payer = index/benchmark MOC at primary close; pre-register ADV-band universe, 10 bps basis, LULD-exclude |

Survivor-profile score: **4/5** (same structure as champion; point 5 uncertain until spread-adjusted measurement)
1. Single-print/auction: **+1** (when cross occurs)
2. Scheduled decision: **+1**
3. Named payer: **+1** (index MOC / close-marking)
4. Testable cheap: **+1** (~$15–55 NOII)
5. ≥2× cost at size: **0 pending** — wider half-spreads at $20–50M ADV may absorb B&M-style gross; this is the registration question

### Economics sketch
- **Expected gross (prior only; not T1)**: Field baseline B&M (2010–2018) **large-cap |auction−mid| ≈ 2.66 bps vs small-cap ≈ 20.6 bps** (known program prior; post-2020 refresh is Modality A). Champion own result: **+2.5 bps/event dev / +12.5 holdout** on liquid names. Mid-band prior for pilot registration: **gross |basis| ~6–15 bps** at 15:55:10 in $20–200M ADV (interpolate; measure, do not assume).
- **Our cost burden**: Continuous marketable entry ≈ **half-spread + adverse selection in last 5 min**. Order-of-magnitude half-spread priors at 15:55 (to be measured on SIP, not cited as fact): liquid mega ~1–3 bps; **$50–200M ADV ~3–10 bps**; **$20–50M ADV ~8–25 bps**. Exchange MOC/LOC fee tiers ≪1 bps if ever passed through; commission-free through 2026-12-31. LULD-paused sessions: entry may be impossible or toxic — exclude.
- **Net prior**: **Open** — if gross scales faster than half-spread down the curve, liquidity-down wins; if net-per-unit-spread is flat/worse, thesis dies. Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout**.
- **Cross-size prior**: UNKNOWN at T1 without sample; pilot Stage-0 should report median paired shares and cross $ notional by ADV band before promoting economic tests.

### Proposed next test (only if OPEN-TESTABLE)
**Hypothesis**: On Nasdaq-primary equities with trailing 20d dollar ADV in **[$20M, $200M]** and price ≥$5, the 15:55:10 near-vs-mid basis (same ≥10 bps threshold as champion) has **gross mean ≥ +5 bps/event** and **net (after half-spread entry, auction exit) ≥ +2 bps/event** on sessions with a true Closing Cross, over 2021–2025 OOS never-fit names.

**Named payer**: Price-insensitive MOC / index-benchmark close flow in mid/small primary closes (S&P 400/600 and Russell-adjacent).

**Data needed**:
- Databento `XNAS.ITCH` schema `imbalance` (~$0.45/name-year) for ~20 symbols — budget **~$15–55**
- SIP/BBO mid at 15:55:10 (Alpaca hist SIP where entitled; else Databento BBO-1s)
- Cross occurrence flag (Closing Cross trade / non-zero paired at 15:59:xx)
- Free IJH/IJR holdings `asOfDate` for membership seed

**Pilot universe recipe (no survivorship)**:
1. **As-of dates**: freeze selection on last trading day of each calendar year 2020–2024 (and optional mid-year) using **trailing 20-session dollar ADV and primary listing as of that date** (Alpaca/Databento definition), never using 2026 membership for historical eligibility.
2. **Seed (optional)**: download IJH + IJR holdings for nearest `asOfDate` ≤ selection date; keep only **Nasdaq primary** common stocks (exclude ETFs, preferreds, warrants, rights).
3. **Hard filters at selection date**:
   - Primary listing = **Nasdaq** (Global Select / Global / Capital)
   - Price ≥ **$5** (and preferably ≤ $200 for whole-share size at $10k)
   - Trailing 20d ADV ∈ **[$20M, $200M]** dollar volume
   - Not in champion 5 + M11 28 (never-fit)
   - Exclude any name with >N LULD pauses in prior 60 sessions (N pre-register, e.g. 3)
4. **Stratify ~20 names**: ~10 in **$50–200M** (mid-liquid), ~10 in **$20–50M** (upper-small); max 2 per GICS sector.
5. **Hold frozen** for the test window; re-select annually with the same recipe for multi-year panels (PIT, no look-ahead).

**Per-tier prior table (registration priors — measure to promote)**:

| ADV band ($M/day) | Role | Gross \|near−mid\| prior | 15:55 half-spread prior | Cross reliability | LULD band class | Net prior (sketch) |
|-------------------|------|--------------------------|-------------------------|-------------------|-----------------|--------------------|
| >500 (champ ref) | baseline | ~2.5–12.5 bps (owned) | ~1–3 bps | very high | often Tier 1 | **+2.5 / +12.5** owned |
| 50–200 | pilot A | ~6–12 bps (interp.) | ~3–10 bps | high if cross | mostly Tier 2 10% | open: +0 to +6 |
| 20–50 | pilot B | ~10–20 bps (→B&M small) | ~8–25 bps | medium; no-cross risk | Tier 2 | open: −5 to +8 |
| <20 | OUT | 20.6+ bps field | often > half of gross | last-sale NOCP risk | Tier 2 / pauses | **do not register** |

**Expected n & power**: 20 names × ~1,000 sessions (2021–2025) × event rate 0.15–0.35 ≈ **300–700 events** if filter is 10 bps; power to detect 5 bps mean vs 20 bps event noise at n≈250 is marginal — Stage A target **n≥250** pooled, report per-band separately (band B may be UNDERPOWERED alone).

**A-priori thresholds**:
- Cross occurrence ≥ **85%** of sessions in band A; ≥ **70%** in band B
- Near price non-zero by 15:55:10 on ≥ **90%** of cross-sessions
- Gross mean basis (signed with-basis entry) ≥ **+5 bps** pooled before cost
- Net mean ≥ **+2 bps** after half-spread entry cost model

**Promotion rule**: If Stage A clears thresholds in band A (or pooled) with pre-registered costs → promote to sealed forward / M10-style paper on the frozen 20; if only band B shows gross but net ≤0 → kill liquidity-down, keep champion liquid universe.

**Kill criteria**: Cross occurrence <60%; near-zero rate after 15:55:10 >20%; net mean ≤0 after honest half-spread; or effect concentrated in top 2 names (concentration kill as MU-in-holdout).

**Trial family**: New **liquidity-down auction** family (charges a new registered family; not a rehash of dead continuous small-cap taker).

### Sources
1. **[T1]** Nasdaq, *The Nasdaq Opening and Closing Crosses — Frequently Asked Questions* (©2025, 1608-25) — eligibility all nationally-listed; cutoffs 15:50/15:55/15:58; NOII 10s then 1s + near/far; no-cross → last sale NOCP; MOC not guaranteed. https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf (fetched 2026-07-18)
2. **[T1]** Nasdaq Trader, *Price List — Trading* — Closing Cross MOC/LOC tiers A–G $0.0008–$0.0016; IO/continuous book $0.0011. https://www.nasdaqtrader.com/trader.aspx?id=pricelisttrading2 (fetched 2026-07-18)
3. **[T1]** Nasdaq, *Limit Up-Limit Down: Frequently Asked Questions* — tier bands, double last 25 min, pause mechanics. https://www.nasdaqtrader.com/content/MarketRegulation/LULD_FAQ.pdf (fetched 2026-07-18)
4. **[T1]** LULD Plan operating site — permanent plan summary; Tier 1/2; last-10-minute pause → primary closing procedures. https://www.luldplan.com/ (fetched 2026-07-18)
5. **[T1]** Nasdaq, *NASDAQ Net Order Imbalance SnapShot (NOIS) Version 2.10* — 50k share filter on newswire only; full NOII via TotalView/NOIView; direction code O. https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/nois-v2_1.pdf (fetched 2026-07-18)
6. **[T1]** Nasdaq Listing Center Equity Rules (4120 / 4754 series) — LULD Closing Cross at/after 15:50; Hybrid Closing Cross for other late halts. https://listingcenter.nasdaq.com/rulebook/nasdaq/rules/Nasdaq%20Equity%204 (fetched/search 2026-07-18)
7. **[T1]** SEC / Nasdaq Exhibit 5, Rel. 34-81188 — LULD Closing Cross insufficient interest → last sale NOCP. https://www.sec.gov/files/rules/sro/nasdaq/2017/34-81188-ex5.pdf (fetched 2026-07-18)
8. **[T1]** Investor.gov, *Stock Market Circuit Breakers* — LULD tier definition and double-band last 25 minutes. https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-market-circuit-breakers
9. **[T1]** iShares / BlackRock IJH & IJR product holdings pages — multi-date `asOfDate` holdings + Excel download endpoints (free membership proxy). https://www.ishares.com/us/products/239763/ishares-core-s-p-mid-cap-etf ; https://www.ishares.com/us/products/239774/ishares-core-sp-smallcap-etf
10. **[T1]** Nasdaq TotalView-ITCH product materials (v3.2 / v5.0 overview) — NOII for Opening/Closing/Halt; dissemination windows. https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTV-ITCH-V3_2.pdf ; ctfassets ITCH 5.0 overview
11. **[T1]** Databento US Equities / XNAS.ITCH catalog — historical imbalance/NOII schema available; per-name history pricing model consistent with owned M11 cost. https://databento.com/datasets/XNAS.ITCH ; https://databento.com/docs/schemas-and-data-formats/imbalance
12. **[T3/conflicted]** EODHD S&P historical constituents marketing — paid (~£30/mo) full hist S&P 400/600; confirms free official bulk is absent. https://eodhd.com/lp/spglobal

#### Queries used
1. `Nasdaq closing cross eligibility fees by tier Rule 4754`
2. `Nasdaq NOII fields thin names near price far price dissemination schedule`
3. `LULD limit up limit down near close 3:35 auction Nasdaq`
4. `Databento Nasdaq NOII schema near price far price zero thin symbols`
5. `S&P 400 600 Russell 2000 membership history free download point in time`
6. `Nasdaq Rule 4754 Closing Cross NOII dissemination all securities eligible`
7. `iShares IJH IJR holdings historical download free asOfDate`
8. `Nasdaq TotalView ITCH NOII near price zero when no imbalance closing cross`
9. `Nasdaq LULD Closing Cross Rule 4754 pause after 3:50 last 10 minutes`
10. `free historical S&P MidCap 400 SmallCap 600 constituents list download`
11. `Nasdaq official closing price no closing cross last sale thin stock`
12. `iShares holdings CSV asOfDate historical free Wayback IJR IJH MDY`
13. `Databento imbalance schema near_price far_price ref_price closing auction`
14. `Nasdaq listed primary listing Closing Cross eligibility only Nasdaq listed OR all nationally listed`
15. `retail stock bid ask spread by ADV average daily volume 20 million 50 million 200 million bps`

---

## Verification pass — 2026-07-21 (independent modality-B re-run)

An independent modality-B agent re-ran this charge without seeing the above. It **corroborates every load-bearing conclusion**: (a) identical Rule 4754 closing-cross machinery for all Nasdaq-listed names, no market-cap/ADV gate, no minimum cross size; (b) NOII cadence (5–10s from 15:50, 1s from 15:55) with Near (cross+continuous) / Far (on-close only) defined only in the last 5 min; (c) no-cross → **NOCP = last regular-way last-sale before 16:00**, i.e. the champion's near/far signal is *undefined* for names with no on-close interest — the structural dropout that bites hardest exactly where B&M's 20.6 bps small-cap dislocation lives; (d) LULD pause at/after 15:50 → single-print LULD Closing Cross; (e) closing-cross MOC/LOC fee **$0.0008–$0.0016/sh, member-volume tiers not security tiers**, negligible/broker-absorbed at $10k; (f) free membership only via iShares **IJH/IJR** daily holdings, no free official S&P 400/600 or Russell back-history. Verdict concurs: **OPEN-TESTABLE**, with the **mid tier ($50–200M ADV, S&P 400 / large-end S&P 600) as the sweet spot** and the deep-small/micro tier structurally weak (entry spread + near/far dropout eat the larger gross dislocation).

Note: this box could NOT fetch sec.gov (WAF 403 to curl+browser-UA and WebFetch) nor parse the Nasdaq FAQ PDFs (binary) — the prior 2026-07-18 pass's direct T1 citations stand as the authoritative record; this pass reproduced them via search snippets and the fetchable Nasdaq price-list page.

**Additive sources not in the original body (worth folding into any future revision):**
- **[T3] NYSE Data Insights, "Closing Auction Order Impact: Size Opportunities Late in the Day," 2024-01-11** — largest late-day orders move price **~0.5–0.71× spread on standard days, 0.72–1.77× on rebalance days**, impact scaling inversely with liquidity (spread *multiples*, not bps; NYSE not Nasdaq — directional corroboration of "dislocation-per-unit-spread rises down-cap"). https://www.nyse.com/data-insights/closing-auction-order-impact-size-opportunities-late-in-the-day
- **[T3] BMLL / Traders Magazine, "Into the Close … Russell Reconstitution," 2025-06-24** — closing-auction dislocation (final mid vs auction) spikes sharply on Russell-recon day across added small/mid names with one-sided imbalances, yet next-day open shows no outsized deviation (charts, not tabular bps). https://www.tradersmagazine.com/am/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution/
- **[T3] Nasdaq/Traders Magazine, "Real Impact of No Round Lots" (2021) + NMS-II odd-lot series** — odd lots (<100 sh) excluded from NBBO/SIP; for low-priced small-caps the round-lot NBBO can understate true crossing cost and odd-lot orders get lower priority — a fill-realism caveat sharpening Gate 5 down-cap.
- **[T1/T2, could-not-fetch] SEC DERA, "A Characterization of Market Quality for Small-Cap US Equities" (2013 data)** — spreads worsen ~monotonically as cap falls (<$1B ≫ $1–5B; <$100M "exceptionally illiquid"); pre-2020 → DECAY-UNKNOWN for exact levels, directional only. sec.gov/marketstructure/research/small_cap_liquidity.pdf (WAF-blocked here; snippet-only).
