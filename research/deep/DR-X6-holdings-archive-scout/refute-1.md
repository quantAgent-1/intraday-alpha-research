# DR-X6 — refute-1 (holdings archive claim bundle)

**Role:** Attempt to REFUTE via live HTTP + Internet Archive CDX + SEC EDGAR. Default `refuted=true` if cannot verify at T1.
**Date:** 2026-07-17 (probes); written 2026-07-18
**Lane:** DR-X6-holdings-archive-scout
**Scope:** 5 claims from modality-B / WAVE3 holdings-archive scout. Not an alpha claim review.

---

## Claim 1

**Claim:** SSGA SPY daily XLSX URL works live but Wayback has sparse density (order ~2–5 captures/year 2020–2026, not daily).

**refuted:** **false**

**Reason:** Live probe returns real XLSX (not HTML shell). CDX 200-OK archive is sparse — **19 distinct digests total** for 2020–2026, **not** daily; per archive-year of capture: **2020:5, 2021:4, 2022:2, 2023:0, 2024:3, 2025:4, 2026:1**. “Order ~2–5 / year” is a correct order-of-magnitude characterization of sparsity (mean ≈ 2.7/yr if 2026 partial counted; **2023 is a hard zero**). File is snapshot-only (no `asOfDate`); `Last-Modified` on probe = 2026-07-17.

**Live probe (2026-07-17):**
- URL: `https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx`
- HTTP **200**, `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, size **54440**, magic `PK\x03\x04` (ZIP/XLSX)

**CDX (filter statuscode:200, from=2020 to=2026):**
- Endpoint: `https://web.archive.org/cdx/search/cdx?url=www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx&from=2020&to=2026&output=json&fl=timestamp,statuscode,mimetype,digest,length&filter=statuscode:200`
- **n=19** rows; **19 distinct digests**; mimetype consistently spreadsheet XLSX

**Caveat (not a refute):** Density is *uneven* — 2023 has **0** captures; “2–5 every year” is slightly overstated as a floor, but the claim’s substance (“sparse, not daily”) stands.

---

## Claim 2

**Claim:** Invesco QQQ legacy holdings download URL largely dead live; sparse Wayback CSV captures.

**refuted:** **false**

**Reason:** All three live legacy `action=download&ticker=QQQ` audience variants **301 → product hub HTML** (`…/us/en/financial-products/etfs.html`, ~388 KB `text/html`) — endpoint retired for live use. Wayback CDX for the same path with `ticker=QQQ` yields **exactly 6** `text/csv` 200-OK captures (2021-06, 2021-11, 2022-12, 2023-03, 2024-07, 2025-02) — sparse, not daily/monthly. Archived CSVs are **full schedules** (~100–103 data rows + header; Weight/Holding Ticker columns), not top-10 stubs. Live replacement is dng-api snapshot JSON (works; no historical `asOfDate`).

**Live probes (2026-07-17):**
| URL | Result |
|-----|--------|
| `…/holdings/main/holdings/0?audienceType=Investor&action=download&ticker=QQQ` | **301** → ETF hub HTML |
| same, `Advisor` | **301** → hub |
| same, `Institutional` | **301** → hub |
| `https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46090E103/holdings/fund?idType=cusip&productType=ETF` | **200** JSON, `effectiveDate=2026-07-16`, `totalNumberOfHoldings=108`, fields `ticker` / `percentageOfTotalNetAssets` / `units` |

**CDX (`matchType=prefix` on holdings/0, filter `original:.*ticker=QQQ.*`):**
- Pure **ticker=QQQ** CSV 200s (exclude QQQJ/QQQM/QQQS):
  1. 20210602153126 Investor
  2. 20211122021905 Investor
  3. 20221203032928 Institutional
  4. 20230309053522 Investor
  5. 20240720162818 Investor
  6. 20250207152018 Investor
- **n=6 distinct digests**; one later 302 on bare `ticker=QQQ&action=download` (2025-08)

**Wayback body check:**
- `web/20210602153126id_/…ticker=QQQ` → **103 lines**, full weights as-of 06/01/2021 (AAPL 10.699 etc.)
- `web/20250207152018id_/…ticker=QQQ` → **102 lines**, as-of 02/05/2025

**Caveat:** “Largely dead” is accurate for legacy download; dng-api is alive for **forward** collection only (not archive).

---

## Claim 3

**Claim:** BlackRock/iShares API with `asOfDate` and `portfolioId` can return IVV/IJH/IJR holdings for month-end dates (IDs ~239726/239763/239774).

**refuted:** **false**

**Reason:** Live **BlackRock varnish-api** returns real CSV holdings (not HTML shell) for historical and recent `asOfDate` values across all three portfolio IDs. Month-end and recent daily samples succeed; **non-trading calendar dates** return empty shell (`Fund Holdings as of,"-"` + ~4.5 KB) — use last NYSE session. Classic `ishares.com` ajax path is a separate, bot-fragile surface; the claim is satisfied by varnish-api (the free automation path).

**Working URL pattern:**
```
https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document
  ?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US
  &portfolioId={ID}&userType=individual&asOfDate=YYYYMMDD&component=holdings
```

**Live matrix (HTTP 200 + real as-of header unless noted):**

| Fund | portfolioId | asOfDate | Size | Header as-of |
|------|-------------|----------|------|--------------|
| IVV | 239726 | 20101231 | 79282 | Dec 31, 2010 |
| IVV | 239726 | 20201231 | 88099 | Dec 31, 2020 |
| IVV | 239726 | 20200331 / 0630 / 0930 | ~87–88 KB | matching QE 2020 |
| IVV | 239726 | 20210331…20251231 sample | ~87–88 KB | matching |
| IVV | 239726 | 20240628 | 87953 | Jun 28, 2024 (Fri) |
| IVV | 239726 | **20240630** | **4567** | **"-"** (Sun — empty shell) |
| IVV | 239726 | 20260630 | 88765 | Jun 30, 2026 |
| IVV | 239726 | 20260715 | 88786 | Jul 15, 2026 |
| IJH | 239763 | 20250630 | 78896 | Jun 30, 2025 |
| IJR | 239774 | 20250630 | 119311 | Jun 30, 2025 |

**CSV schema (IVV 20240328):** columns include `Ticker,Name,Sector,Asset Class,Market Value,Weight (%),…`; n equities ≈ **507**, weight sum ≈ **99.97%** (ex-parse noise).

**Caveat (precision, not refute):** Claim says “BlackRock/iShares API” generically — the **verified** free path is varnish-api. Bare `www.ishares.com/...ajax?fileType=csv&asOfDate=…` is known-fragile (prior wave bot-gate); do not treat ajax as interchangeable without a browser session.

---

## Claim 4

**Claim:** Invesco QQQ Trust (CIK 0001067839) files NPORT-P with full holdings `pctVal` in public XML.

**refuted:** **false**

**Reason:** SEC submissions JSON lists **27 NPORT-P** accessions in the recent window (plus early NPORT-EX), spanning **2019–2026** at ~**4/year** (2020–2025 all have 4; 2026 has 2 so far). Live download of `primary_doc.xml` for recent and 2020 filings returns full XML with **`invstOrSec` nodes carrying `title`, `cusip`, `balance`, `valUSD`, `pctVal`**. Sample sums of `pctVal` ≈ 100. UIT structure does **not** exempt QQQ from N-PORT.

**SEC submissions:**
- `https://data.sec.gov/submissions/CIK0001067839.json` — name **INVESCO QQQ TRUST, SERIES 1**, tickers `['QQQ']`, form counts include **NPORT-P: 27**
- Year histogram (recent NPORT-like): 2019:2, **2020–2025:4 each**, 2026:2

**Live XML samples (UA: `EngineV5 Research Bot contact@example.com`):**

| Accession | Size | invstOrSec | Σ pctVal | repPdDate | seriesName |
|-----------|------|------------|----------|-----------|------------|
| 0001067839-26-000024 | 111284 | **102** | **99.88** | 2026-03-31 | Invesco QQQ Trust, Series 1 |
| 0001752724-25-039757 | 109297 | **101** | **100.03** | 2024-12-31 | same |
| 0001752724-20-043463 | 110671 | **103** | **99.98** | 2019-12-31 | same |

**Top holdings (2026-03-31 report, by pctVal):** NVDA 8.68, AAPL 7.63, MSFT 5.63, AMZN 4.58, TSLA 3.80, META 3.46, … — full equity book, not top-10 only.

**Archives path pattern:**  
`https://www.sec.gov/Archives/edgar/data/1067839/{accession_nodash}/primary_doc.xml`

**Caveats (not refute):**
1. Public N-PORT is **quarter-end + lag** — monthly filings exist in the system but non-QE months are not public; free history is **quarterly**, not daily.
2. Bare curl without a contact UA can get **HTTP 403** from SEC; fair-access UA required.
3. `pctVal` is percent of NAV (e.g. 8.68 = 8.68%); weight = `pctVal/100`.

---

## Claim 5

**Claim:** Quarterly-or-better SPX/NDX weights 2020–2026 at **$0** is achievable via iShares API + N-PORT (+ sparse Wayback fill).

**refuted:** **false**

**Reason:** Composition of Claims 1–4:

| Leg | Target | Verified free path | Cadence 2020–2026 | Cost |
|-----|--------|--------------------|-------------------|------|
| **SPX proxy** | IVV weights | BlackRock varnish-api `portfolioId=239726` + month-end `asOfDate` | **Monthly** (month-ends 2010→2026 live-probed; better than quarterly) | **$0** |
| **NDX proxy** | QQQ weights | SEC NPORT-P CIK 0001067839 `primary_doc.xml` → `pctVal` | **Quarterly public** (~24–28 quarter-ends) | **$0** |
| Optional densify | SPY XLSX / QQQ CSV | Wayback (SPY n=19 digests; QQQ n=6 CSV) | Sparse only | **$0** |
| Forward | daily | SPY XLSX live + Invesco dng-api | Ongoing snapshot | **$0** |

No paid index license (GIW / S&P DJI official weights) is required if ETF full-replication holdings are accepted as **proxies**. QA anchors from this refute: IVV weight sum ≈ 1; QQQ NPORT Σ pctVal ≈ 100; QQQ Wayback CSVs full book.

**What would flip Claim 5 (kill criteria — not currently hit):**
- varnish-api historical empties for >20% of month-ends, **and** SPY NPORT quarterly alone insufficient for intended use; **or**
- QQQ NPORT public XML missing full equity schedule for material 2020–2022 quarters (samples 2020 + 2024–2026 OK here).

**Caveats (scope, not refute):**
1. “Quarterly-or-better” is **met** (SPX monthly + NDX quarterly). **Daily** free PIT for 2020–2026 is **not** claimed and is **not** supported by Wayback density.
2. “iShares API” = varnish-api as verified; ajax shell does not block the $0 path.
3. Official S&P / Nasdaq weight feeds remain licensed products — out of claim if proxies accepted.

---

## Bundle summary

| # | Claim (short) | refuted | Deciding evidence |
|---|---------------|---------|-------------------|
| 1 | SPY XLSX live OK; Wayback sparse ~2–5/yr | **false** | Live 200 XLSX + CDX n=19 digests (2023:0) |
| 2 | QQQ legacy download dead; sparse Wayback CSV | **false** | Live 301→hub; CDX n=6 QQQ CSV; full-book IA bodies |
| 3 | varnish-api asOfDate IVV/IJH/IJR (IDs 239726/763/774) | **false** | Live CSV matrix 2010–2026; empty shell on non-trading days |
| 4 | QQQ CIK 0001067839 NPORT-P full pctVal XML | **false** | submissions JSON + 3 primary_doc.xml parses |
| 5 | $0 quarterly+ SPX/NDX 2020–26 via API+NPORT(+WB) | **false** | Composition of 1–4; monthly SPX + quarterly NDX |

**Majority refuted?** No — **0/5 refuted**. All five load-bearing archive-reachability claims **survive** T1 live/CDX/SEC verification. Default-true path **not** triggered.

**Implication for modality-B OPEN-TESTABLE:** Scout verdict **not overturned**. Primary SPX path = IVV varnish-api month-ends; primary NDX path = QQQ NPORT-P; SPY XLSX + QQQ legacy CDX = sparse fill / forward only. Dense free **daily** NDX history remains **not** established.

---

#### Fetches / queries used (this refute)

1. Live GET SSGA SPY XLSX — headers + body size + ZIP magic  
2. CDX SPY XLSX `from=2020&to=2026` filter 200 — count by year / distinct digests  
3. Live GET Invesco legacy download (Investor/Advisor/Institutional) + dng-api cusip 46090E103  
4. CDX `www.invesco.com/…/holdings/0` prefix + filter `ticker=QQQ` — list CSV 200s  
5. Wayback `id_` replay of QQQ CSV 20210602 and 20250207 — line counts / schema  
6. Live GET BlackRock varnish-api matrix: IVV/IJH/IJR × dates incl. 20101231, 2020 QEs, 20240628/30, 2025–2026  
7. Parse IVV 20240328 CSV weight sum  
8. SEC `data.sec.gov/submissions/CIK0001067839.json` — NPORT-P inventory  
9. SEC Archives `primary_doc.xml` accessions 000106783926000024, 000175272425039757, 000175272420043463 — parse `invstOrSec` / `pctVal`  
10. Confirm empty-shell behavior for non-trading `asOfDate` (20240630)

#### Absolute paths
- This file: `<repo-root>\research\deep\DR-X6-holdings-archive-scout\refute-1.md`
- Scout under review: `<repo-root>\research\deep\DR-X6-holdings-archive-scout\modality-B.md`
