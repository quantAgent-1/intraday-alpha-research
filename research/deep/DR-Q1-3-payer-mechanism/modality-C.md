## DR-Q1-3 — C practitioner findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence MED) — Practitioner/vendor literature (SSGA, Nasdaq Economic Research/Mackintosh, BMLL, Bogousslavsky–Muravyev, Vanguard MOC desks via TD Securities) converges on a **named multi-payer close**: passive/index MOC and NAV-alignment dominate *price-insensitive* force; option-expiry hedges, close-benchmarked active flow, and echo-print GMOC add size but are mixed-sensitivity. Forced close flow **does** scale with index membership and passive/ETF ownership in published DiD and rebalance-day evidence — a pre-registrable form for basis-persistence is writeable. Full dollar decomposition by payer class at the **name-day** level is **not** publicly available (no retail-cheap tagged-flow product ≤$100); proxies (index weight × passive share × rebal/expiry flags) are the practical substitute. PIT NDX/SPX **weights** and **passive-ownership** for 33 Nasdaq names are reconstructible for **$0–~$50** (issuer ETF holdings files + free membership lists + market-cap proxies), not via Norgate/commercial index licenses (those exceed $100). Late-window lit (BMLL 2025; Mackintosh 2019) confirms NOII cadence and **15:57–16:00 convergence**, so residual 15:55:10 basis is the harvestable slice — same structure as champion.

What would flip it: (a) name-level cross-section of |basis| or net edge showing **no** monotonic relation to passive-own / NDX-weight after vol controls (kills scaling claim); or (b) evidence that residual basis after 15:55 is pure HFT-arbed noise with mean net ≤0 at n≥250 on the M11 set.

### Mechanism
**Who pays (practitioner decomposition — price-insensitive first):**
1. **Index MOC / passive index funds** — Must print at official close to minimize tracking error vs index “virtual trade.” **Highly price-insensitive** on rebalance/add/delete days; **mostly zero need to trade** on normal market-cap days (weights self-adjust). Mackintosh (2020): rebal-day closes dominate; on **normal** days index **cash-flow** MOC ≈ **~5.5%** of close notional (~$300B/yr cash-flow estimate vs ~$23B normal-day close × 245 days). On rebal days index funds can be **~40%+** of MOC notional.
2. **Mutual-fund NAV alignment** — NAV struck on close; end-of-day cash invest/redeem and closet-indexers cluster at auction (Bogousslavsky–Muravyev; Greenwich survey: execute at official price + discovery). Price-insensitive relative to continuous book.
3. **ETF create/redeem channel** — APs acquire/deliver **basket** (often via MOC of underlyings or continuous) then swap for ETF; **ETF shell auction** is thin (~2% ADV on Arca ETFs per BMLL). Constituent MOC can still be forced; shell MOC is **not** the main passive pipe.
4. **Option/delta hedges** — Auction volume spikes on expiry/quad-witch as dealers drop stock hedges after options expire (Bogousslavsky–Muravyev). Partially price-insensitive (must flatten); size episodic.
5. **Pension / TDF** — Large AUM but trade mostly via **underlying funds** and glide-path rebalances (Vanguard TDF notes: TE tolerances looser than pure index; not pure daily MOC). Indirect, lower daily frequency than pure index cash-flow.
6. **Corporate buybacks** — Practitioners do **not** emphasize systematic MOC buyback as a major close-payer class in the sources reviewed; treat as **UNVERIFIED / minor for daily residual basis**.
7. **Close-benchmarked algos / active** — SSGA: actives migrate to close for deeper liquidity and tighter late spreads; “close-aware algorithms” stagger into auction. **Partially price-sensitive** (can size/time) but still add liquidity demand clustered at 16:00.
8. **Retail** — Not a primary driver of large-name auction imbalance in institutional notes; MOC retail tools exist but not load-bearing for NDX megacaps.
9. **Echo prints / off-exchange GMOC** — Mackintosh (2024): echo prints ~**30%** of MOC-priced volume on normal days (~20% on rebal days). Matthews GMOC = off-exchange close guarantee — **does not hit NOII**. Reduces visible exchange imbalance vs true close-priced demand.

**Why flow is price-insensitive:** Tracking-error / NAV / settlement / option-expiry constraints dominate price; payers accept auction clearing price.

**Why it persists:** Listing-exchange auction monopoly + high auction fees + overnight inventory risk for offsetters → residual liquidity premium (Mackintosh ~1.7 bps gross for N100 offsetters, 2019). Passive AUM still growing → US close share **~13–15%** ADV recently (SSGA/Instinet to Dec 2025) vs ~8% in 2018 and ~3% in 2010.

**Capacity intuition at $10k:** Irrelevant — exchange close notional is tens of $B/day. Edge and name-selectivity bind, not capacity.

**Scaling with weight / passive ownership (pre-registrable form):**
- Bogousslavsky–Muravyev DiD: **ETF + passive MF ownership** (not active) strongly associated with auction volume share; S&P 500 **add → +20%** relative auction volume; **delete → −15%**.
- Mackintosh bottoms-up: index trackers may own ~**25% of float** in multi-indexed names; S&P adds trade ~**14–18% of float** at close on inclusion day.
- **Pre-registrable form (practitioner-aligned):**  
  `E[signed residual basis | 15:55:10] ≈ f( signed_NOII/ADV, passive_share_proxy, NDX_or_SPX_weight, I_rebal, I_expiry )`  
  with a priori: higher `passive_share × weight` → larger |imbalance| and **slower** post-15:55 convergence (more residual basis for manual latency) on non-rebal days; rebal/expiry days are **regime switches** (mean shift, not same slope). This is the mechanism lens for **name-selectivity** (NVDA alive vs LRCX/AVGO/NFLX dead at same vol): differential **index weight × passive share × options/ETF basket intensity**, not vol class.

**NOII 15:55–16:00 cadence + late convergence (Q3 residual):**
- Nasdaq: imbalance from **15:50** every **10 s** until 15:55; **every 1 s** after; **near/far** indicative prices only from **~15:55** (T1 FAQ; BMLL 2025). Matches owned-data reality (near/far 0 until ~15:55).
- BMLL (May 2025 vignette, Nasdaq equities): indicative vs mid **converge 15:57–15:58**; final minute tandem move toward close.
- Mackintosh (2019 N100): ~**80%** of ultimate close move priced within **300 ms** of imbalance news; mean move ~**5.5 bps**; offsetter premium ~**1.7 bps**. Manual 5–25 s captures **residual** only — champion’s design is correct; late LOC/IO and continuous offset continue after 15:55.

### Claims
C1 [CONFIRMED] (T3/exchange research, 6 Feb 2020, sample US closes ~2009–2019): Index funds are a **small** share of **normal-day** MOC (~**5.5%** cash-flow estimate) but **large** on rebal days (~**41%** of rebal-day close notional when Credit Suisse index-rebal trading ~$300B vs rebal-day close ~$725B in 2019). Cap-weight indexes **do not** need daily rebalance for price moves. — Phil Mackintosh, Nasdaq Economic Research; https://www.nasdaq.com/articles/market-on-close-moc-is-more-active-than-people-think-2020-02-06

C2 [CONFIRMED] (T2, June 2021 paper / JFM 2023, sample US equities 2010–2018): Auction share of daily volume **3.1%→7.5%** (2010→2018); **ETF and passive MF ownership** (not active) are major determinants of auction volume (DiD); S&P 500 add **+20%** / delete **−15%** relative auction volume; option-expiry spikes; mean abs close−mid deviation **8.1 bps**; deviations largely reverse overnight. **NO-COST-MODEL** for 15:55→close basis rule. — Bogousslavsky & Muravyev, “Who Trades at the Close?”; https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf

C3 [CONFIRMED] (T3 asset-manager, 23 Jan 2026, Instinet volume to Dec 2025): US closing-auction share rose to **~13.1%** (Q4 2025) / **~15.4%** (Dec 2025) of daily volume from **~8.4%** (from Jan 2018 baseline). Passive/indexing + NAV alignment = structural driver; close can shift price-revealing → **price-forming** on heavy MOC/rebal days; desks use **close-aware algorithms**. — Elise Ryan, SSGA; https://www.ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure

C4 [CONFIRMED] (T3 vendor-CONFLICTED, 24 Jun 2025, sample May 2025 venue vignette + Russell 2024): Typical 2024 close ~**$50B**/day (~**9%** ADV); rebal/expiry days ~**20%** ADV. Nasdaq NOII: **10 s** to 15:55 then **1 s**; near/far from 15:55. Nasdaq equities: indicative–mid **convergence 15:57–15:58**. Russell Day 2024: some adds **>34%** of notional in auction. BMLL sells imbalance datasets — **CONFLICTED**. — Laible & Thakur, BMLL / Traders Magazine; https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

C5 [CONFIRMED] (T3/exchange research, 31 Oct 2024): Rebal-day close ~**$240B** avg (~**30%+** of day) vs typical ~**$40B** (<10%). Bottoms-up float-share traded on adds implies index trackers can hold ~**25% of float** in multi-indexed names; S&P adds typically **14–18% of float** at close. Echo prints ~**30%** of MOC-priced volume normal days. — Mackintosh, Nasdaq; https://www.nasdaq.com/articles/how-many-investors-really-track-major-indexes

C6 [CONFIRMED] (T3/exchange research, 27 Sep 2019, sample Nasdaq-100 Q2-2019): On NOII publication, N100 moves avg **~5.5 bps**; **~80%** of ultimate close move within **300 ms**; liquidity premium to imbalance offsetters avg **~1.7 bps** gross (< half spread). — Mackintosh, Nasdaq; https://www.nasdaq.com/articles/how-much-does-the-moc-imbalance-matter-2019-09-27

C7 [CONFIRMED] (T1, Nasdaq Closing Cross FAQ, current rules): MOC until **15:55**; LOC until **15:58**; IO until **16:00**. NOII from **15:50** (10 s) then **1 s** with near/far after 15:55. Close maximizes matched shares from on-close + continuous. Auction historically ~**10%** of Nasdaq ADV (FAQ headline; now higher per SSGA market-wide). — https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf

C8 [PLAUSIBLE] (T3 broker note, Oct 2019, RBC Capital Markets market-structure): Early-look MOC (15:50 publish / cancel lock) increases flip risk **15:50–15:55** and price/volume volatility in that window; late LOC use shrinks. Desk-level model of Nasdaq close competition with NYSE D-quotes. — RBC “Nasdaq – Early Look MOC”; https://www.rbccm.com/assets/rbccm/docs/housing-market/Nasdaq_Close.pdf

C9 [CONFIRMED] (T3 practitioner, 9 May 2025, TD Securities Bid Out ep. 71): Vanguard US close PMs (Birkett, Kraynak) confirm **index dealing desks** run systematic MOC for tracking; multi-market MOC expertise is a specialized desk function — validates “who pays” as institutional index flow, not retail. No public per-name bps edge disclosure. — https://www.tdsecurities.com/ca/en/bid-out-episode-71

C10 [CONFIRMED] (T3 data-vendor map, 2024–2026 pricing public): **≤$100 PIT path** for 33 Nasdaq names: (i) **free** QQQ/IVV/VOO/SPY/QQQM etc. **daily holdings** (issuer sites / historical scrapes) → weight **proxy** for NDX/SPX; (ii) **free** SPX membership reconstruction (Robot Wealth method / Wikipedia + historical lists) or Sharadar S&P500 constituents if already owned; (iii) **free** SEC N-PORT / 13F + ETF shares outstanding → **passive ownership %** = Σ passive ETF shares held / shares out (quarterly lag); (iv) market-cap free-float proxy from free EOD prices for intra-quarter weight drift. **Norgate Platinum** historical constituents SPX/NDX ≈ **$630/yr** — **FAILS ≤$100**. Commercial S&P/Nasdaq official weight feeds — **FAILS**. Licensed Compustat/WRDS — not retail. **CONFLICTED** if buying a vendor that sells “edge from ownership data.”

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **PASS** | Decision instant is scheduled 15:55:10; 5–25 s manual is pre-positionable. Not the 300 ms first print. |
| 2 | Access | **PASS** | Retail MOC/LOC + continuous taker on Nasdaq names; same as champion path. |
| 3 | Session | **PASS** | Enter late RTH; flat **at** 16:00 cross. In-mission. |
| 4 | Data | **PASS** | Weights + passive proxies reconstructible **$0–~$50** labor/scraping (issuer holdings + free membership + free EOD). Owned NOII + SIP already cover signal/fill path. No new recurring feed required. |
| 5 | Fill realism | **PASS** | Auction single-print exit; entry continuous taker (champion kernel). No maker assumption. |
| 6 | Statistics | **PASS** | Daily name-events × 33 names × multi-year owned NOII → n ≫ 250; cross-section test of scaling has power. |
| 7 | Protocol | **PASS** | Named payer = residual auction liquidity demand from price-insensitive passive/NAV/hedge flow; pre-register functional form linking |basis| or net edge to passive×weight **before** looking at M11 outcomes; charges auction / payer-decomposition trial family. |

**Survivor-profile score: 5/5**
1. Single-print/auction execution — **YES**
2. Scheduled decision instant — **YES**
3. Named price-insensitive payer — **YES** (index/passive MOC + NAV; option expiry episodic)
4. Historically testable ≤~$100 — **YES** (proxies free/cheap; NOII owned)
5. Expected effect ≥2× cost burden — **YES if** residual basis scales as claimed (champion already clears bar; this charge is **selectivity/mechanism**, not new structure)

### Economics sketch
- **Gross cited (related, not identical structure):**
  - Offsetter liquidity premium N100 ~**1.7 bps** gross (Mackintosh 2019).
  - Mean abs auction deviation stocks ~**8.1 bps** (Bogousslavsky; mid@4pm→close, full cross-section).
  - Immediate NOII move ~**5.5 bps** with ~80% gone in 300 ms → **residual** for 15:55:10 snapshot is the only manual-harvestable piece (champion already measures this).
- **Our cost burden:** Same as champion (taker half-spread entry + zero commission through 2026-12-31 + single-print exit). No new fee class.
- **Net prior for *this charge*:** Not a new edge; a **filter/scaler**. Prior: names with higher passive×weight should show larger |NOII residual| and higher hit-rate / mean bps — if true, improves M11 name selection and explains NVDA vs dead same-vol names. If false, payer is **not** passive-scaled (or is saturated/arbed in mega-liquid names) and name-selectivity must come from elsewhere (options GEX banned; earnings; idiosyncratic rebal).
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**.

### Proposed next test (OPEN-TESTABLE)
- **Hypothesis:** At 15:55:10, |NOII near − mid| and signed (close − mid_entry) | net edge **increase** in the cross-section with a pre-registered **PassiveForce** score = `z(passive_own_proxy) + z(log NDX_weight) + β_rebal·I_rebal + β_exp·I_expiry`, controlling for ADV and recent vol. Name-level mean net ≥ +2 bps when PassiveForce is top-tercile; bottom-tercile ≈ 0 (explains M11 dead names).
- **Named payer:** Price-insensitive index/passive/NAV MOC and episodic option-hedge MOC scaled by index weight and passive share.
- **Data needed (owned / ≤$100):**
  - **Owned:** Databento Nasdaq NOII + SIP mids for 5 core + 28 M11 names (already paid).
  - **Weights (≤$0–$20):** Reconstruct NDX weights from **historical QQQ holdings** (Invesco daily holdings files / archived portfolio CSVs) + market-cap drift between rebalances; SPX weights from **IVV/VOO/SPY** holdings files. Flag modified-cap rules (NDX caps) as approximation error.
  - **Passive ownership (≤$0–$50 labor):** Quarterly: sum shares held by large passive vehicles (QQQ, QQQM, IVV, VOO, SPY, VTI, IWB, and major sector passives if material) from free issuer holdings + N-PORT, divide by shares outstanding (free EOD). Optional: 13F “index fund” tags (quarterly lag — document lag as feature, not bug for *slow* ownership).
  - **Do NOT buy:** Norgate Platinum ($630/yr), official S&P index weights license, FactSet Ownership full feed.
- **Universe:** M11 28 + core 5 Nasdaq names (fixed list); no cherry-pick after results.
- **Expected n & power:** ~250 sessions/year × ~30 names ≈ 7,500 name-events/year raw; post |basis|≥10 bps filter still n≫250. Cross-section regression of edge on PassiveForce: power adequate if slope ≥ few bps per SD.
- **A-priori thresholds (lock before run):**
  - Signal unchanged: |near−mid| ≥ 10 bps at 15:55:10; take WITH basis; exit official close.
  - Scaling: pre-register terciles of PassiveForce on **prior quarter** ownership (no same-day leak).
  - Rebal/expiry: separate strata; do not pool without interaction terms.
  - Skip near/far still 0; skip halt days.
- **Promotion rule:** Top-tercile PassiveForce mean net ≥ +2 bps/event AND significantly > bottom-tercile (bootstrap CI excludes 0) at n≥250 per tercile pooled; then use as **M10/M11 name filter** only on forward data (holdout spent).
- **Kill criteria:** No monotone relation of edge or |basis| to PassiveForce after vol/ADV controls at n≥500; or relation driven solely by rebal days (then charge folds into rebal calendar family, not daily mechanism); or concentration trap (≤2 names carry all tercile gap).
- **Trial family charged:** Auction / closing-cross payer-decomposition family (DR-Q1-3); shares multiple-testing budget with champion/M11 — not a free trial.

### Sources
1. [T3] Phil Mackintosh, “Market-On-Close (MOC) Is More Active Than People Think,” Nasdaq Economic Research, 2020-02-06. https://www.nasdaq.com/articles/market-on-close-moc-is-more-active-than-people-think-2020-02-06
2. [T3] Phil Mackintosh, “How Many Investors Really Track the Major Indexes?,” Nasdaq, 2024-10-31. https://www.nasdaq.com/articles/how-many-investors-really-track-major-indexes
3. [T3] Phil Mackintosh, “How Much Does the MOC Imbalance Matter?,” Nasdaq, 2019-09-27. https://www.nasdaq.com/articles/how-much-does-the-moc-imbalance-matter-2019-09-27
4. [T2] Vincent Bogousslavsky & Dmitriy Muravyev, “Who Trades at the Close? Implications for Price Discovery and Liquidity,” June 2021 (JFM 2023). PDF: https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf
5. [T3] Elise Ryan, “Closing time: How passive investing is reshaping equity market microstructure,” SSGA, 2026-01-23 (Instinet volume stats). https://www.ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure
6. [T3 vendor-CONFLICTED] Rob Laible & Shaurya Thakur, “Into the Close: Unpacking U.S. Closing Auction Dynamics…,” BMLL / Traders Magazine, 2025-06-24. https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution
7. [T1] Nasdaq, “Nasdaq Closing Cross — Frequently Asked Questions.” https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf
8. [T3] RBC Capital Markets, “Nasdaq – Early Look MOC,” Oct 2019. https://www.rbccm.com/assets/rbccm/docs/housing-market/Nasdaq_Close.pdf
9. [T3] TD Securities Bid Out Episode 71, “Exploring Market on Close Facilities, Part 1: The Americas” (Vanguard MOC PMs), 2025-05-09. https://www.tdsecurities.com/ca/en/bid-out-episode-71
10. [T3] Russell Investments, “The case for MOC as a TM trading strategy,” 2025-03-11 (transition-manager MOC vs IS benchmark conflict). https://russellinvestments.com/uk/blog/the-case-for-moc
11. [T3] Norgate Data stock packages pricing (historical constituents Platinum ~$630/12mo — over budget). https://norgatedata.com/stockmarketpackages.php
12. [T3] Robot Wealth, “How To Get Historical S&P 500 Constituents Data For Free,” 2020-05-12. https://robotwealth.com/how-to-get-historical-spx-constituents-data-for-free/
13. [T3] Sharadar / Nasdaq Data Link product pages (S&P 500 constituents + institutional ownership; package pricing gated — often above free path). https://data.nasdaq.com/publishers/SHARADAR
14. [T3] Matthews Asia, “Understanding Guaranteed Market-on-Close” (off-exchange GMOC path). https://www.matthewsasia.com/insights/understanding-guaranteed-market-on-close/

#### Queries used
- Nasdaq closing cross who pays MOC flow index fund ETF creation practitioner
- BMLL Nasdaq closing auction share growth market structure research
- close-benchmarked algorithms MOC flow modeling transition manager desk
- passive ownership index weight closing auction impact price insensitive flow
- Who Trades at the Close Bogousslavsky Muravyev MOC composition index funds
- Nasdaq Economic Research closing auction volume share Phil Mackintosh MOC
- point-in-time S&P 500 NDX index weights free historical data source cheap
- ETF ownership institutional passive ownership stock free data 13F OR Sharadar
- How much does the MOC imbalance matter Mackintosh Nasdaq 15:55 near price
- Norgate OR Sharadar S&P 500 historical weights price point-in-time under $100
- close-aware algorithm MOC participation broker Goldman Citi JPMorgan market structure note
- Norgate Data S&P 500 Nasdaq-100 historical constituents weights pricing
- Sharadar SF1 SFP S&P 500 constituents historical price Nasdaq Data Link cost
- QQQ holdings historical free reconstruct NDX weight market cap free float proxy
- ETF ownership percent of shares outstanding free data iShares Vanguard holdings file
- buybacks MOC pension TDF target date fund closing auction flow
