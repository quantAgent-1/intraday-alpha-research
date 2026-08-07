# DR-X6 refute-2 — holdings archive scout (independent)

**Role:** Attempt to REFUTE five load-bearing claims from modality-B via live primary probes.  
**Default:** `refuted=true` if no primary located.  
**Date:** 2026-07-18 (live probes same day)  
**Independence note:** This agent did not read a sibling refute-1 report. All counts and HTTP behaviors below were re-fetched independently (Internet Archive CDX, SSGA, Invesco, BlackRock varnish-api / iShares ajax, SEC `data.sec.gov` + EDGAR XML). User-Agent used: `DR-X6-refute-2 research contact@example.com`.

---

## Bundle claims under test

| ID | Claim (as charged from modality-B C1–C4 + open verdict recipe) | Asserted class |
|----|----------------------------------------------------------------|----------------|
| C1 | SSGA SPY daily XLSX Wayback 200-OK **distinct digests n=19** for 2020–2026; by archive-year **2020:5, 2021:4, 2022:2, 2023:0, 2024:3, 2025:4, 2026:1** — sparse, not a dense free archive | T1 CDX |
| C2 | Invesco QQQ **legacy** `action=download` is **live-dead (301→hub)**; Wayback **≈6** CSV 200s; live **dng-api** is snapshot-only (no historical `asOfDate`); **0** useful CDX history on dng holdings path | T1 live + CDX |
| C3 | iShares product **ajax `asOfDate` CSV is bare-HTTP HTML shell**; **BlackRock varnish-api** serves real historical IVV holdings CSVs with `asOfDate` back to **≥2010** (month-ends / trading days) | T1 live |
| C4 | QQQ (UIT, CIK `0001067839`) **files Form NPORT-P**; public `primary_doc.xml` carries full `<invstOrSec>` weight vector (`cusip`/`balance`/`valUSD`/`pctVal`); recent bucket **≥27** NPORT-P; sample ~**102** names | T1 SEC |
| C5 | **$0 quarterly-or-better** SPX/NDX weight proxies for 2020–2026 are reachable without paid vendors: primary SPX = IVV varnish-api month-ends; primary NDX = QQQ public NPORT-P quarter-ends; SPY XLSX + dng-api = **forward-only** | T1/T3 synthesis |

---

## C1 — SPY Wayback density (n=19 / year split)

**Attempted refutation path:** Re-query CDX without trusting modality counts; check non-200 noise, digest collapse, alternate URL density, predecessor coverage.

**Primary probes (2026-07-18):**

```
GET https://web.archive.org/cdx/search/cdx
  ?url=www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx
  &output=json&filter=statuscode:200
  &fl=timestamp,original,statuscode,digest,length
```

| Metric | Result |
|--------|--------|
| 200-OK rows | **19** |
| Distinct digests | **19** (1:1 with captures) |
| Captures / distinct digests by archive year | 2020:**5**, 2021:**4**, 2022:**2**, 2023:**0**, 2024:**3**, 2025:**4**, 2026:**1** |
| All-status CDX (no filter) | still **19** rows, all status 200, mime XLSX |
| Live URL | HTTP **200**, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, **54 440** bytes, PK zip magic — snapshot overwrite confirmed usable **forward** |

First capture in window: `20200902083504` digest `6DPRH54Z…`. Latest: `20260517153630` digest `3NNQ6PCN…`.

Predecessor probe:

```
CDX us.spdrs.com/site-content/xls/SPY_All_Holdings.xls (prefix)
→ 1 hit: 20190412175205 status 200
```

Not a 2020–2026 density source (matches modality).

**Caveats (not refutations):**
- Distinct digests ≈ distinct file bytes at crawl time, **not** guaranteed unique *as-of* portfolio dates if SSGA republished identical bytes (here digests are all unique, so 19 content versions).
- Zero **2023** captures is a real hole — any backtest relying on Wayback SPY alone misses an entire calendar year.
- Density ~3/year average is **not** monthly/daily PIT history.

**Verdict: `refuted = false`**  
Counts and year split reproduce exactly. Claim that SPY XLSX Wayback is **sparse** stands. No denser free SSGA historical endpoint found in this probe.

---

## C2 — QQQ endpoints (legacy dead / dng snapshot / Wayback ≈6)

**Attempted refutation path:** (1) Confirm legacy not silently alive under other audienceTypes. (2) Re-count CDX digests more carefully (all audienceTypes). (3) Force historical query params on dng-api. (4) Challenge “0 CDX on dng-api.”

### Live legacy download

| audienceType | HTTP (no follow) | Location |
|--------------|------------------|----------|
| Investor | **301** | `https://www.invesco.com/us/en/financial-products/etfs.html` |
| Advisor | **301** | same hub |
| Institutional | **301** | same hub |

Followed Investor URL → final **200 HTML** product hub (~388 KB), **not** `text/csv`. Endpoint retired for automation.

### Live dng-api

```
GET https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46090E103/holdings/fund?idType=cusip&productType=ETF
→ 200, ~38 400 bytes JSON
  cusip=46090E103, effectiveDate=2026-07-16, totalNumberOfHoldings=108
  holdings[]: ticker, units, percentageOfTotalNetAssets, cusip, …
```

Historical param stress (same path):

| Query addon | Result |
|-------------|--------|
| `asOfDate=20200131` | **200**, same live body (`effectiveDate` still **2026-07-16**) — param **ignored** |
| `date=20200131` / `asOf=20200131` | same ignore |
| `effectiveDate=2020-01-31` | **400** Bad Request |

No free historical holdings API on this surface.

### Wayback QQQ `action=download` — **count correction**

CDX prefix on  
`www.invesco.com/us/financial-products/etfs/holdings/main/holdings/0`  
filtered to `ticker=QQQ` + `action=download` + status 200 + `text/csv`:

| Metric | Live re-count | Modality claim |
|--------|---------------|----------------|
| 200 CSV rows | **13** | ≈6 |
| Distinct digests | **13** | ≈6 |
| Unique capture calendar days | **11** | (not stated) |
| Unique capture months | **10** | listed 6 months |

Capture months observed: 2021-06 (2 digests), 2021-11, 2022-12, 2023-01 (2), 2023-03, 2023-12 (2), 2024-06, 2024-07, 2025-02, 2025-03.  
AudienceTypes mix Investor / Institutional / Advisor; digests still unique across rows.

**Partial fact refute:** `n≈6` **under-counts** archived QQQ CSV snapshots by ~2× if digests are the unit. **Does not** rescue a dense free NDX archive (still ~10 sparse months over 2021–2025; no 2020 CSV hits in this filter).

### dng-api CDX — **“0 hits” does not hold**

CDX on `dng-api.invesco.com/.../46090E103/holdings/*` status 200 returned **≥3** holdings-related captures (2025-09, 2026-05, 2026-06).  
Wayback replay of `20260530001220` holdings/fund URL returned **live-shaped JSON** (`effectiveDate=2026-05-28`, 105 holdings) — so IA has **at least one** reconstructible dng holdings snapshot, not zero.

Caveat: CDX mimetype is often `text/html` and lengths are small; this is **not** a multi-year daily archive and does not create an `asOfDate` API. Density remains useless for 2020–2024 NDX rebuild.

**Verdict: `refuted = false` on the load-bearing parts** (legacy dead; dng snapshot-only; free NDX daily history **not** on issuer API).  
**`refuted = true` on two numeric/side claims:** Wayback QQQ CSV digests are **~13 not ≈6**; dng-api holdings path has **non-zero** CDX (sparse), not zero. Correct synthesis language: “sparse single-digit-to-low-teens CSV digests; dng IA incidental only.”

---

## C3 — iShares ajax shell vs BlackRock varnish-api history

**Attempted refutation path:** Prove ajax returns real CSV under bare or browser-like HTTP; prove varnish historical empty/bot-gated; prove 2010 claim fails on trading-day month-ends.

### ajax

```
GET https://www.ishares.com/us/products/239726/.../1467271812596.ajax
  ?fileType=csv&fileName=IVV_holdings&dataType=fund&asOfDate=20240628
```

| Setup | HTTP | Content-Type | Body |
|-------|------|--------------|------|
| Scout UA | 200 | `text/csv;charset=UTF-8` | **HTML** `<!DOCTYPE html>…` (~2.1 MB product shell) |
| Chrome UA + `Referer: ishares.com/.../239726` + `Accept: text/csv` | 200 | `text/csv` | **still HTML shell** |

`content-disposition: attachment; filename=IVV_holdings.csv` is a lie for automation — body is not holdings CSV. Matches “bare HTTP → HTML shell”; browser-session paths were **not** proven here and must not be the primary recipe.

### varnish-api

```
GET https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document
  ?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US
  &portfolioId=239726&userType=individual&component=holdings&asOfDate=YYYYMMDD
```

| asOfDate | as-of header in CSV | ~size | holdings usable? |
|----------|---------------------|-------|------------------|
| 20100331 / 20100630 | Mar 31 / Jun 30, **2010** | ~79 KB | **yes** (~500 rows, weights sum ≈100) |
| 20151231 | Dec 31, 2015 | ~87 KB | yes |
| 20200115 (intra-month) | Jan 15, 2020 | ~88 KB | yes (dailies exist when date is a session) |
| 20200131 | Jan 31, 2020 | ~88 KB | yes; MSFT/AAPL top weights period-correct |
| 20200228 (month-end session) | Feb 28, 2020 | ~88 KB | yes |
| 20200229 (Sat) / 20200101 / 20200230 | `Fund Holdings as of,"-"` | **4 567 B** shell | **no** — HTTP 200 trap |
| 20210630 … 20250630, 20260331, 20260630 | matching labels | ~88 KB | yes |
| 20090131 | `as of,"-"` | shell | no (pre-claim window) |
| 20260717 (near “today”) | `as of,"-"` | shell | lag / not yet published |

Weight QA samples: 20200131 sum **100.0%** (n=510 rows); 20240628 sum **100.03%**; 20100630 sum **99.94%**.

**Caveats:**
- Empty historical responses are **HTTP 200 with a holdings header table and `as of,"-"`** — must reject on body rules (`as of,"-"` or size ≪ 10 KB), not status code alone (modality already flags this).
- Calendar month-end that falls on weekend/holiday → empty; use last NYSE session (e.g. 2020-02-28 not 02-29).
- This probe does **not** audit BlackRock ToS/rate limits; cash cost is $0 but operational/legal risk is unmeasured.
- ajax remains unusable for unattended scrape in this environment even with browser-ish headers.

**Verdict: `refuted = false`**  
Varnish historical IVV CSVs with correct `Fund Holdings as of` labels are **live and deep (≥2010 trading days)**. Ajax is **not** a bare-HTTP CSV source. Claim stands; empty-200 footgun is the main implementation risk, not absence of history.

---

## C4 — QQQ NPORT-P full public weight vector

**Attempted refutation path:** Show QQQ lacks NPORT-P; show public XML is summary-only / confidential schedule; show 2020–2022 gaps; show pctVal unusable.

**Primary probes:**

```
GET https://data.sec.gov/submissions/CIK0001067839.json
→ name INVESCO QQQ TRUST, SERIES 1; tickers ["QQQ"]
→ NPORT-P (+ not counting /A separately in pure NPORT-P filter): 27 in recent bucket
→ by filing year: 2019:1, 2020:4, 2021:4, 2022:4, 2023:4, 2024:4, 2025:4, 2026:2
```

Sample accession `0001067839-26-000024` (filed 2026-05-28):

```
GET https://www.sec.gov/Archives/edgar/data/1067839/000106783926000024/primary_doc.xml
→ 200, ~111 KB XML
→ <invstOrSec> = 102; <cusip>=102; <balance>=102; <valUSD>=102; <pctVal>=102
→ repPdDate = 2026-03-31 (~58-day lag vs file date — consistent with ~60-day public lag)
→ sum(pctVal) ≈ 99.88  → units are percent of NAV (8.68 = 8.68%), not fraction of 1
→ top: NVDA 8.68, AAPL 7.63, MSFT 5.63, …
```

Older full schedules (fund CIK path works even when accession prefix is third-party filer `0001752724-…`):

| Filing date | Accession | repPdDate | invstOrSec | sum pctVal |
|-------------|-----------|-----------|------------|------------|
| 2020-11-30 | 0001752724-20-251748 | 2020-09-30 | **103** | ≈99.98 |
| 2022-11-25 | 0001752724-22-266948 | 2022-09-30 | **102** | ≈99.97 |
| 2026-05-28 | 0001067839-26-000024 | 2026-03-31 | **102** | ≈99.88 |

SPY CIK `0000884394` likewise shows **27** NPORT-P in recent bucket (same quarterly public cadence) — available as SPX cross-check, not required for the NDX primary path.

**Caveats:**
- Public EDGAR surface is **quarter-end** N-PORT (≈4/yr), not monthly confidential filings. Cannot free-upgrade NDX to true monthly from NPORT alone.
- First `<invstOrSec>` in document order is **not** top weight (ordering is not rank-sorted) — parsers must sort by `pctVal`.
- Accession numbers often use filer CIK `1752724`; archive URL still resolves under **fund** CIK `1067839` in tested cases.

**Verdict: `refuted = false`**  
QQQ **does** file NPORT-P with full equity schedule XML usable as a quarterly NDX proxy from at least 2020–2026. Core claim confirmed at T1.

---

## C5 — $0 quarterly-or-better SPX/NDX recipe (2020–2026)

**Attempted refutation path:** Kill either leg (SPX varnish or NDX NPORT); show paid vendor is required for *quarterly* coverage; show “or-better” overclaims free NDX density.

**What live probes support:**

| Leg | Free? | Cadence reachable 2020–2026 | Notes |
|-----|-------|------------------------------|-------|
| SPX via IVV varnish `asOfDate` | **Yes ($0 HTTP)** | **Month-end+** (and many dailies) from **2010→** on trading days | Primary SPX path confirmed this session |
| SPX via SPY NPORT-P | Yes | Quarterly | Independent backup; same lag |
| SPX via SPY XLSX Wayback | Yes | **Sparse** (19 digests; **no 2023**) | Gap-fill only |
| NDX via QQQ NPORT-P | Yes | **Quarterly** (~4/yr, ~60d lag) | Primary NDX history confirmed |
| NDX via QQQ legacy CSV Wayback | Yes | **Sparse** (~11–13 digests, 2021–2025) | Not monthly |
| NDX via live dng-api | Yes forward | **Snapshot only** | Historical params ignored |
| iShares ajax history | **No (bare HTTP)** | n/a | HTML shell |

**Load-bearing conclusion:** A **zero cash-outlay** rebuild of **quarterly** SPX+NDX weights for 2020–2026 is live-verified (IVV varnish month-ends **or** SPY NPORT for SPX; QQQ NPORT for NDX). SPX can be **better than quarterly** (monthly) for free; NDX free history remains **quarterly**, not monthly.

**Residual challenges (weaken packaging, do not kill $0 quarterly):**

1. **Numeric side-claims in C2** (Wayback ≈6; dng CDX=0) are wrong — correct before writing pipeline docs; still sparse.
2. **Varnish empty-200** on non-sessions / unpublished dates requires hard QA gates or month-end calendars.
3. **ToS / bulk scraping / rate limits** on BlackRock were not cleared; “$0” means no vendor invoice, not zero operational risk.
4. **NPORT lag (~60 days)** means the latest quarter is not immediately available — fine for historical research, bad for live PIT until lag elapses.
5. **ETF≠index**: IVV/QQQ are full-replication proxies, not licensed official SPX/NDX weight files; acceptable for M12-style passive-force work only if that approximation is explicitly accepted.

**Verdict: `refuted = false`** on the decisive claim (“$0 quarterly-or-better SPX/NDX proxies reachable without paid vendors for 2020–2026”).  
**Do not overread “or-better”** as free daily/monthly NDX — free **NDX** densification beyond quarter-ends still fails. Free **SPX** monthly via varnish is the “better” half.

---

## Summary table

| ID | Topic | `refuted` | Disposition |
|----|-------|-----------|-------------|
| C1 | SPY Wayback density n=19 / year split | **false** | Exact reproduce; 2023 hole real; sparse stands |
| C2 | QQQ legacy dead + dng snapshot | **false** (core) | **Side-claim corrections:** CSV digests **13≠≈6**; dng holdings CDX **≠0** (still useless for history API) |
| C3 | ajax shell + varnish historical IVV | **false** | Varnish ≥2010 trading-day CSVs live; ajax HTML-as-csv; empty-200 trap |
| C4 | QQQ NPORT-P full weights | **false** | 27 public NPORT-P; 2020/2022/2026 XML full schedules; pctVal sums ~100 |
| C5 | $0 quarterly-or-better recipe | **false** | SPX monthly free (varnish) + NDX quarterly free (NPORT); NDX not free-monthly |

**Majority:** 5/5 load-bearing claims **not refuted**. Two ancillary density/CDX numbers in C2 should be patched in synthesis.

**What would flip C5 later:** varnish-api starts returning empty shells for historical `asOfDate` (or ToS/enforcement blocks bulk month-end loops) **and** concurrent discovery that public QQQ NPORT-P schedules are incomplete for material 2020–2022 quarters (not observed — 2020-09 and 2022-09 samples are full).

---

## Probe inventory (this agent)

1. IA CDX — SPY XLSX (filtered + unfiltered); SPY predecessor XLS; Invesco holdings prefix; dng-api holdings prefix  
2. Live SSGA SPY XLSX (200, 54 440 B, OOXML)  
3. Live Invesco legacy download ×3 audienceTypes (301→hub)  
4. Live dng-api holdings + historical param matrix  
5. Wayback replay dng holdings timestamp `20260530001220`  
6. Live iShares ajax `asOfDate=20240628` (scout UA + browser-like headers)  
7. Live BlackRock varnish-api IVV `portfolioId=239726` date matrix (2010→2026, bad dates, month-ends)  
8. SEC submissions CIK 0001067839 (QQQ) + 0000884394 (SPY)  
9. EDGAR `primary_doc.xml` NPORT-P: 0001067839-26-000024; 0001752724-20-251748; 0001752724-22-266948  

**Tier tags:** all above **T1 live** (issuer HTTP or SEC/IA primary interfaces), 2026-07-18.
