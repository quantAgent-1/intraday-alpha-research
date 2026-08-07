## DR-Q1-3 — B primary/venue findings

### Verdict recommendation
**OPEN-TESTABLE** (confidence **HIGH**) — Venue mechanics for the late-window NOII path are fully T1-specified and already owned (Databento `XNAS.ITCH` imbalance). The actionable data gap (point-in-time NDX/SPX weights + per-name passive share for 33 Nasdaq names) is **unblockable ≤$100 via free ETF-holdings files + SEC bulk**, without buying Nasdaq GIW / S&P DJI official weight licenses. Official GIW NDX weight history and S&P DJI official SPX weight history remain **licensed products (>>$100; quote-only)** — treat them as non-blocking once QQQ/IVV/SPY/VOO holdings are used as weight proxies and 13F/N-PORT as passive-share proxies. Pre-registrable scaling test is executable on owned NOII + free holdings/13F.

What would flip it: Discovery that free QQQ (or IVV/SPY) daily holdings files cannot be reconstructed for ≥80% of 2020–2026 session-days for the 33 names (Wayback + provider retention fail), **or** that official GIW/S&P weights are required by protocol and cannot be proxied (in which case verdict → OPEN-BLOCKED(GIW/S&P license, quote-only, typically multi-k$/yr)).

### Mechanism
**Who pays (venue-side):** Closing Cross residual imbalance is cleared against continuous-book liquidity after MOC lock at 15:55. Price-insensitive classes that must print at NOCP (indexed MOC, NAV-driven mutual fund windows, ETF create/redeem netting into underlyings, close-benchmarked algos) are the structural payers; late IO/LOC can offset but do not remove inelastic residual after 15:55.

**Why price-insensitive:** Benchmarking to official close / index close; MOC cannot cancel freely after cutoffs; tracking-error minimization forces participation at the Cross price regardless of near-vs-mid basis.

**Why persists:** Nasdaq Closing Cross is the official NOCP setter; NOII transparency (Near/Far from 15:55 @ 1s) invites offsetting liquidity but does not eliminate forced flow. BMLL venue evidence shows late-window **indicative↔mid convergence** (esp. 15:57–15:58) then tandem move to the print — residual basis at 15:55:10 is the champion window before that convergence completes.

**Capacity intuition:** Megacap Nasdaq auction notional is large; $1k–$10k is negligible. Name selectivity (NVDA alive / LRCX·AVGO·NFLX dead despite high vol) is **not** explained by venue rules alone — requires cross-sectional passive/index-weight scaling, which this modality unblocks with free data products.

### Claims
C1 [CONFIRMED] (T1, Closing Cross FAQ / openclose / FR 2022-03876, schedule ongoing): **Closing NOII dissemination cadence:** 15:50–15:55 ET every **10 s** (paired qty, imbalance side/qty, Current Reference Price); **15:55–16:00 ET every 1 s** with **Near** (cross+continuous) and **Far** (cross-only) indicative clearing prices; Cross executes **16:00**. EOII language in FR describes the pre-15:55 10s stream. — https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf ; https://www.nasdaqtrader.com/trader.aspx?id=openclose ; https://www.federalregister.gov/documents/2022/02/24/2022-03876/self-regulatory-organizations-the-nasdaq-stock-market-llc-order-approving-proposed-rule-change-to

C2 [CONFIRMED] (T1, ClosingCrossfaq + project owned NOII 2020–2026): **Near and Far are unpopulated / 0 until ~15:55:00**; champion decision instant 15:55:10 is the first valid near-vs-mid basis snapshot under the feed. — ClosingCrossfaq.pdf field definitions; ITCH/Databento imbalance mapping

C3 [CONFIRMED] (T3 venue analytics, BMLL 2025-06-24, sample last 2 weeks May 2025, 10 Nasdaq tickers): **Late-window indicative-price convergence on Nasdaq:** clear convergence of indicative close vs continuous midpoint between **15:57 and 15:58**; in the final minute indicative and mid converge to each other then move in tandem toward the closing print. Supports residual basis at 15:55:10 as pre-convergence edge window. NO-COST-MODEL (descriptive microstructure, not a tradeable backtest). — https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

C4 [CONFIRMED] (T1 product pages + specs, ongoing): **Official NDX weights product = Nasdaq Global Index Watch (GIW)** at indexes.nasdaqomx.com / indexes.nasdaq.com: web UI + GIW Web Services API (UFFWeighting.ashx SOD/EOD pipe/csv, auth required) + premium **GIFFD** SFTP. Methodology explicitly points weightings to GIW. Public free layer: index overview, factsheets, methodology PDFs, index-level history export — **not** full historical constituent weight panels. Licensing: “Any Nasdaq Data … for benchmarking … requires an appropriate license”; sales via DataSales@nasdaq.com / indexservices@nasdaq.com. **Published retail $ for US GIW full history: UNKNOWN (quote-only; European GIS pricelist legacy showed ~€400/historical calendar month — not a US retail SKU).** → official NDX weights **not** free and **not** ≤$100 one-time. — https://indexes.nasdaqomx.com/ ; https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/giw_webservice_spec_current.pdf ; https://indexes.nasdaq.com/docs/Methodology_NDX.pdf ; https://www.nasdaq.com/solutions/global-indexes/data/giw

C5 [CONFIRMED] (T1/T3 free path, ongoing): **Free NDX weight proxy = Invesco QQQ daily holdings** (physical NDX tracker). Product page exports holdings with ticker, shares, %TNA, CUSIP, market value (as-of daily). URL path: invesco.com QQQ product / holdings export. Current free; multi-year history reconstructible via Wayback + ongoing scrape (≤$0). Slickcharts NDX weights = current-only free table, no PIT history. — https://www.invesco.com/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html ; https://www.slickcharts.com/nasdaq100

C6 [CONFIRMED] (T1/T3 free path, ongoing): **Free SPX weight proxies = SPY / IVV / VOO daily holdings (not official S&P DJI):**
- **SPY (SSGA):** direct daily XLSX free — `https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx` (also linked from SPY product page “Download All Holdings: Daily”). Format: Excel; fields include Name, Shares Held, Weight. History: provider retains current; Wayback for past snapshots.
- **IVV (iShares):** free CSV via product ajax `…/products/{id}/….ajax?fileType=csv&fileName=IVV_holdings&dataType=fund` (+ `asOfDate` for historical months). Community tools (talsan/ishares, etf-scraper) document **month-end history back ~2010** and recent daily for major iShares. $0.
- **VOO (Vanguard):** current full holdings on investor.vanguard.com product page + portfolio composition export; historical depth thinner on free web than iShares/SSGA.
Official S&P DJI constituent/weight history = licensed (SPDJI / Compustat / CRSP path) — **not free, not ≤$100 retail.** Wikipedia List of S&P 500 companies + revision history = free membership/changes proxy (weights incomplete). — https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy ; https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf ; https://en.wikipedia.org/wiki/List_of_S%26P_500_companies

C7 [CONFIRMED] (T1 SEC DERA, free, 2013→present): **SEC Form 13F bulk data sets — free passive-ownership proxy.** URL: https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets . Quarterly ZIP TSV (tab-delimited UTF-8); key table **INFOTABLE**: ACCESSION_NUMBER, CUSIP, NAMEOFISSUER, VALUE ($, post-2023 nearest dollar), SSHPRNAMT (shares), SSHPRNAMTTYPE, PUTCALL, INVESTMENTDISCRETION, voting authority fields. Coverage: managers ≥$100M AUM; **quarterly** report date with ~45-day filing lag. **Derivable for our 33 names:** sum SSHPRNAMT across known passive/index filers (Vanguard, BlackRock, State Street, Invesco, etc.) / shares outstanding ≈ institutional passive-share proxy. **Not derivable cleanly:** true “% passively held” (active sleeves inside same manager, double-counting multi-manager, non-13F holders, short/loaned shares). Granularity: CUSIP×manager×quarter — not daily. $0. — https://www.sec.gov/files/form_13f_readme.pdf

C8 [CONFIRMED] (T1 SEC DERA, free, 2019Q4→present): **SEC Form N-PORT bulk — free monthly fund holdings (incl. ETFs/index mutual funds).** URL: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets . Quarterly ZIP bulk of monthly portfolio positions. Complements 13F: actual fund-level holdings (QQQ/IVV/SPY/VOO and broad index mutual funds) rather than manager aggregates. Public dissemination historically lagged (quarterly public for third month of fiscal quarter under older rules; 2024–2026 amendments/proposals alter public cadence — use as-filed bulk as source of truth). $0. Better per-name passive % proxy when restricted to known index-tracking series. — N-PORT data sets page; formn-port.pdf

C9 [PLAUSIBLE] (T2, Bogousslavsky & Muravyev JFM 2023, sample NYSE+Nasdaq common stocks Jan 2010–Dec 2018): **Forced close flow scales with passive ownership:** ETF and passive mutual fund ownership (not active) strongly associated with closing-auction turnover; 1% ↑ passive MF ownership ≈ **+3.7%** auction turnover vs **+0.6%** in 15:55–16:00 continuous window (DiD). Auction volume spikes on index rebal / OPEX / month-end. Venue-consistent with “passive pays the cross.” Gross descriptive; NO single-name near-mid basis economics. — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840 ; JFM 66 (2023)

C10 [CONFIRMED] (T1 product policy + free proxies above): **Actionable data matrix for 33 Nasdaq names ≤$100 one-time:**
| Need | Official product | $ | Free/≤$100 substitute | Cadence |
|------|------------------|---|------------------------|---------|
| NDX membership+weights 2020–26 | GIW / GIFFD | license (quote) | QQQ daily holdings + Nasdaq rebal press releases | daily / quarterly events |
| SPX membership+weights 2020–26 | S&P DJI | license | SPY/IVV/VOO daily holdings + Wikipedia changes | daily / event |
| Per-name passive % | vendor (FactSet etc.) | multi-k$ | 13F bulk (institutional) + N-PORT (fund) + major ETF share counts / float | quarterly / monthly |
| Auction volume / imbalance / basis | owned Databento NOII | owned | — | 1s from 15:55 |

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **PASS** | Scheduled 15:55:10 NOII snapshot; 5–25 s manual is pre-positionable; exit = 16:00 single print |
| 2 | Access | **PASS** | Same MOC/LOC path as champion; retail brokers already in use |
| 3 | Session | **PASS** | Flat at close via MOC/LOC — in-mission |
| 4 | Data | **PASS** | Owned NOII + free QQQ/SPY/IVV holdings + free SEC 13F/N-PORT; official GIW/S&P **not required** if proxies accepted in pre-reg |
| 5 | Fill realism | **PASS** | Auction single-print exit; continuous taker entry (champion structure) |
| 6 | Statistics | **PASS** | 33 names × multi-year sessions → n ≫ 250 for pooled basis events; cross-section power for weight/passive tertiles is the design target |
| 7 | Protocol | **PASS** | Named payer (price-insensitive indexed/passive MOC) + a-priori scaling f(index weight, passive share, auction/ADV); pre-registrable; charges auction/passive-scaling family (not a dead-list rehash) |

**Survivor-profile score: 5/5**
1. Single-print/auction execution — **yes**
2. Scheduled decision instant — **yes** (15:55:10)
3. Named price-insensitive payer — **yes** (indexed/passive close flow; T2 scaling support C9)
4. Historically testable on owned/≤~$100 data — **yes** (free ETF holdings + SEC bulk + owned NOII)
5. Expected effect ≥ 2× cost burden at size — **conditional on Stage A** (champion reference +2.5/+12.5; name selectivity is the open economic question)

### Economics sketch
- **Expected gross:** Not re-estimated here (modality B = mechanics/data). Champion reference: **dev ≈ +2.5 bps/event**, holdout **+12.5 bps/event [6.9, 18.5], n=140**. Scaling hypothesis: basis-persistence and/or event frequency ∝ index weight / passive share → if true, name filter could lift OOS (M11 was net −3.0 bps pooled; NVDA alive suggests high-weight/high-passive concentration).
- **Our cost burden:** Same as champion (taker entry + auction exit; zero commission promo through 2026-12-31). Data cost for unblocking: **$0** (ETF files + SEC bulk) or tens of $ only if re-pulling Databento gaps.
- **Net prior:** Mechanics and data do **not** block; economics gate is the cross-sectional scaling test. Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout**.

### Proposed next test (only if OPEN-TESTABLE)
- **Hypothesis:** At 15:55:10, |NOII near − mid| basis size and/or directional persistence to the 16:00 print scales with (a) QQQ %TNA weight of the name, (b) SPY/IVV weight, (c) 13F/N-PORT passive-share proxy — pre-register: basis-persistence ∝ f(index weight, passive share, auction share of ADV).
- **Named payer:** Price-insensitive indexed MOC / passive close-benchmark flow into Nasdaq Closing Cross.
- **Data needed:** Owned Databento NOII (33 names); free QQQ+SPY (or IVV) holdings history 2020–2026 (scrape + Wayback); free SEC 13F 2020Q1→ + N-PORT for major index funds; shares outstanding from free sources (e.g. already-owned fundamentals or Yahoo/SEC). **$0–≤$50** if any Databento gap-fill.
- **Universe:** 33 Nasdaq names (5 core + 28 M11); flag NDX membership periods via QQQ holdings presence.
- **Expected n & power:** Daily events × years × names → thousands of name-sessions; against ~20 bps/event noise, test slope of basis→close residual on weight/passive terciles; require n≥250 per tercile for Stage A.
- **A-priori thresholds:** (i) Spearman corr(basis bps, QQQ weight) > 0 at p<0.05 name-day pooled; (ii) top passive/weight tercile mean net ≥ +2 bps/event with hit-rate ≥55%; (iii) bottom tercile ≤0 or significantly worse — explains M11 name selectivity.
- **Promotion rule:** Stage A confirms monotonic scaling + top-tercile economics ≥ champion floor; then freeze weight/passive filter for M10 forward.
- **Kill criteria:** No significant weight/passive gradient; or top-tercile net ≤0 after costs; or holdings coverage <70% of session-days.
- **Trial family charged:** New **auction-passive-scaling / DR-Q1-3** family (mechanism extension of champion; not dead-list).

### Sources
1. **[T1]** Nasdaq Closing Cross FAQ — NOII 15:50@10s / 15:55@1s Near/Far. https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf
2. **[T1]** Nasdaq Trader — Opening and Closing Crosses (eligibility, NOII window 15:50–16:00). https://www.nasdaqtrader.com/trader.aspx?id=openclose
3. **[T1]** Federal Register 2022-03876 — EOII every 10s from 15:50; NOII every 1s from 15:55. https://www.federalregister.gov/documents/2022/02/24/2022-03876/self-regulatory-organizations-the-nasdaq-stock-market-llc-order-approving-proposed-rule-change-to
4. **[T1]** Nasdaq openclose_faqs.pdf — Cross process, order types, Near/Far definitions. https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf
5. **[T1]** Nasdaq-100 Methodology — weightings via GIW. https://indexes.nasdaq.com/docs/Methodology_NDX.pdf
6. **[T1]** GIW Web Service specification — UFFWeighting auth endpoints, SOD/EOD. https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/giw_webservice_spec_current.pdf
7. **[T1]** Nasdaq GIW / index data product pages — licensed weight/component data; contact sales. https://indexes.nasdaqomx.com/ ; https://www.nasdaq.com/solutions/global-indexes/data
8. **[T1]** SSGA SPY product — free daily holdings XLSX. https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy ; https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx
9. **[T1]** SEC Form 13F Data Sets + readme — free quarterly bulk INFOTABLE schema. https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets ; https://www.sec.gov/files/form_13f_readme.pdf
10. **[T1]** SEC Form N-PORT Data Sets — free bulk monthly fund holdings 2019Q4→. https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
11. **[T3]** BMLL “Into the Close…” (2025-06-24) — Nasdaq 15:57–15:58 indicative/mid convergence. https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution
12. **[T2]** Bogousslavsky & Muravyev (2023), *Journal of Financial Markets* — passive ownership → auction volume elasticity. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840
13. **[T3]** iShares/Invesco holdings download patterns (community-documented free CSV/export; etf-scraper, talsan/ishares) — month-end history for IVV-class funds. https://github.com/talsan/ishares ; https://pypi.org/project/etf-scraper/
14. **[T3]** Slickcharts NDX/SPX current weights (no PIT history). https://www.slickcharts.com/nasdaq100 ; https://www.slickcharts.com/sp500

#### Queries used
- `Nasdaq NOII dissemination schedule closing cross 15:55 16:00`
- `Nasdaq NDX-100 index weights historical data free download official`
- `S&P 500 membership weights historical free data product`
- `iShares Vanguard SPDR ETF daily holdings file format history retention Wayback`
- `Nasdaq Global Index Watch GIW NDX weight data product pricing license`
- `SEC 13F bulk data free download EDGAR passive ownership proxy`
- `QQQ Invesco holdings daily CSV download historical Wayback archive`
- `iShares holdings download CSV daily historical IVV IWM QQQ ETF holdings file URL`
- `SPDR SSGA SPY daily holdings download CSV historical archive`
- `Vanguard ETF holdings daily download CSV VOO historical`
- `closing auction NOII indicative price convergence literature paper Nasdaq near price`
- `Wayback Machine iShares holdings CSV historical archive`
- `SEC Form N-PORT bulk data free ETF holdings historical quarterly`
- `Nasdaq GIW FlexFile Delivery pricing cost index weights subscription`
- `iShares holdings asOfDate parameter historical monthly download ajax`
- `Who Trades at the Close Bogousslavsky Muravyev closing auction passive`
- `Nasdaq market data price list GIW index weights non-professional cost`
- `iShares product page holdings ajax fileType=csv download URL pattern historical dates`
- `S&P Dow Jones Indices historical constituents free Wikipedia changes list weights license`
- `Invesco QQQ holdings download file format daily CSV historical free`
