## DR-X6 — B primary/venue findings

> Consolidated: prior-session live probe (2026-07-17) + re-scout (2026-07-21). New in re-scout is
> marked **[RS 07-21]**; prior live-probe claims retained and marked **[07-17]**. Re-scout
> INDEPENDENTLY corroborated the prior numbers (SPY Wayback n=19; QQQ NPORT-P quarterly, n=27) and
> ADDED a second, byte-verified $0 SPX path (Wayback IVV `aaData` JSON) that de-risks reliance on
> the BlackRock varnish-api.

### Verdict recommendation
OPEN-TESTABLE (confidence HIGH) — **$0 quarterly-or-better SPX/NDX weight proxies for 2020–2026 are
reachable without paid vendors, now via TWO independent SPX paths.** Primary SPX path is the
**BlackRock varnish-api historical `asOfDate` CSVs for IVV** (live-verified month-ends and recent
dailies back to ≥2010; not the bot-gated `ishares.com` ajax shell) **[07-17]**. **Redundant SPX
path [RS 07-21]:** the **Wayback Machine holds ≥185 distinct archived IVV holdings responses** whose
raw bodies are the real `{"aaData":[...]}` JSON (byte-verified: 505 equity rows + per-name weight
`raw` for asOfDate=20161130) — this survives even if varnish-api is rate-limited/killed. Primary NDX
path is **SEC Form NPORT-P for Invesco QQQ Trust (CIK 0001067839)** — QQQ is a UIT but **does file
N-PORT**; 27 public NPORT-P accessions 2019Q2→2026, `primary_doc.xml` carries
`cusip`/`balance`/`valUSD`/`pctVal`. SSGA SPY daily XLSX and the Invesco download CSV are good
live/forward collectors but **sparse** free archives (SPY ≈19 distinct 200-OK digests 2020–2026;
QQQ download CSVs ≈14).

What would flip it: BOTH SPX paths fail — varnish-api starts bot-shelling historical `asOfDate`
**and** the Wayback IVV JSON captures turn out (on scaled audit) to be predominantly SPA-shell
captures rather than `aaData` payload (recent 2026-era captures ARE shells; filter on stored
mimetype=application/json + compressed length ≈30–120 KB). For NDX: discovery that public NPORT-P
for QQQ omits the full equity schedule for material 2020–2022 quarters (→ Wayback + N-CSRS fallback).

### Mechanism
No trading payer — this is a **data-reachability** charge feeding M12 Cell B PassiveForce and the A2
index-LETF leg. Index weights are needed as **point-in-time (PIT) proxies** for who is in SPX/NDX
(and at what weight) when sizing/attributing rebalance and LETF-related flow. Full-replication
issuer files track the index closely (SPY/IVV≈SPX float-weights; QQQ≈NDX modified-cap). SEC N-PORT
is the legal monthly portfolio report but **only fiscal-quarter-end N-PORTs are public** (≈60-day
lag), so the SEC free PIT floor is **quarterly** unless an issuer site or Wayback preserves denser
snapshots — which, for IVV, Wayback does.

### Claims
C1 [CONFIRMED] (T1, 07-17 live + CDX, sample 2020–2026): SSGA SPY daily holdings
`https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx`
returns live XLSX (HTTP 200); **snapshot-only** (overwritten daily; no `asOfDate`). **[RS 07-21]
re-confirmed** Wayback 200-OK distinct-digest captures **n=19**, by capture-year: 2020:5, 2021:4,
2022:2, 2023:0, 2024:3, 2025:4, 2026:1; actual snapshot dates irregular / NOT month-aligned
(2020-09-02, 2020-12-14…2026-05-17). Institutional-path variant +7. Long `/us/en/individual/…` URL
301-redirects (1 capture). — CDX `web.archive.org/cdx/search/cdx?url=...spy.xlsx&output=json`.

C2 [CONFIRMED] (T1, 07-17 live + CDX; **[RS 07-21]** density re-count): Invesco QQQ download pattern
`https://www.invesco.com/us/financial-products/etfs/holdings/main/holdings/0?audienceType={Investor|Advisor|Institutional}&action=download&ticker=QQQ`
→ CSV (cols incl. **Weight**, **Date**). Wayback QQQ-specific 200s ≈**14** (2021–2025); the broader
all-ticker `action=download` family = 88 captures 2020–2025. Live 2026 301→hub per 07-17.
Current live JSON API `https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46090E103/holdings/fund?idType=cusip&productType=ETF`
(`ticker`, `percentageOfTotalNetAssets`, `units`, `effectiveDate`) — snapshot only; 0 Wayback hits.
— WebSearch + CDX 07-21; live cusip probe 07-17.

C3 [CONFIRMED] (T1, 07-17 live probes; **[RS 07-21]** re-probed identical result): iShares classic
ajax `https://www.ishares.com/us/products/239726/.../1467271812596.ajax?fileType=csv&asOfDate=YYYYMMDD`
from this box returns **HTTP 200 but the SPA HTML shell (~2.1–2.2 MB, identical body for two
different dates)** — bot/edge gate for bare curl. **Two working free paths instead:**
(a) **[07-17] BlackRock varnish-api**
`https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US&portfolioId={239726|239763|239774}&userType=individual&asOfDate=YYYYMMDD&component=holdings`
→ real CSV `Fund Holdings as of,"Mon DD, YYYY"`; live-verified IVV month-ends ≥2010, quarter-ends
2021–2026, recent dailies; non-trading dates return an empty `as of,"-"` shell → use last trading
day of month. IJH/IJR same API OK. (b) **[RS 07-21] Wayback replay** — see C6.
— live probe 07-17; re-probe + PyPI etf-scraper / talsan-ishares 07-21.

C4 [CONFIRMED] (T1, **[RS 07-21]** EDGAR submissions JSON; corroborates 07-17): Invesco QQQ Trust
Series 1 (UIT) **files Form NPORT-P quarterly** — **27 NPORT-P accessions** (first NPORT-EX 2019-08,
NPORT-P from 2020-02) through 2026-05, ~one per calendar quarter; each `primary_doc.xml` carries the
full equity schedule (`title`, `cusip`, `balance`, `valUSD`, `pctVal`) → weight = pctVal/100. Also
N-CEN (annual), N-CSRS, N-30B-2 (semi-annual narrative SOI). SPY CIK 0000884394 same NPORT-P
quarterly cadence for SPX cross-check. Public N-PORT = quarter-end + lag (non-QE months not public).
— data.sec.gov/submissions/CIK0001067839.json (curl, non-"naver" UA).

C5 [CONFIRMED] (T1, **[RS 07-21]** byte-verification — the key new evidence): The iShares IVV
holdings `.ajax` endpoint is archived in Wayback **391 captures / 185 distinct `asOfDate`s
(2006–2026), 348 stored as `application/json` HTTP 200**. A raw `id_` replay of asOfDate=20161130
returned the genuine payload `{"aaData":[["AAPL","APPLE INC","Information Technology","Equity",
{...},{"raw":3.12501}...]` — **505 "Equity" rows, 476 ISINs, per-name weights** (Apple 3.125% at
2016-11-30). In-window distinct as-of dates: 2020:10, 2021:12, 2022:11, 2023:15, 2024:26, 2025:24,
2026:4 (**≈102 dates**, better-than-monthly 2023–26, ~monthly 2020–22), sampled dates are
month-ends. Caveat: recent 2026-era captures replay as the ~700 KB+ SPA shell — MUST filter CDX on
`mimetype=application/json` + compressed `length` ≈30–120 KB before `id_` fetch. — Wayback CDX +
`web.archive.org/web/<ts>id_/<url>` fetch.

C6 [CONFIRMED] (T1, **[RS 07-21]**): iShares endpoint generalizes by product ID — IVV=239726,
**IJH=239763, IJR=239774** — same `/…/1467271812596.ajax?fileType={json|csv}&asOfDate=…` tail, so
IJH/IJR PIT weights reachable by both varnish-api (C3a) and Wayback (C5); per-name Wayback density
for IJH/IJR not separately counted this lane (UNKNOWN). talsan/ishares config confirms
`FIRST_AVAILABLE_HOLDINGS_DATE=2006-09-29`. — iShares product pages + scraper config.

C7 [CONFIRMED] (T1/T3, 07-17 CDX): ETF.com `www.etf.com/{QQQ,SPY}` Wayback = top-holdings marketing
HTML, not full weight files (top-10 cross-check only). Nasdaq **`indexes.nasdaqomx.com/Index/Weighting/NDX`**
public weight table = **[RS 07-21]** 41 Wayback captures 2013–2026 (~2–6/yr) but full-100-name
table serialization UNVERIFIED — possible supplementary NDX source, lower confidence than NPORT-P.

C8 [CONFIRMED] (T1, both sessions): Effort ranking for quarterly-or-better 2020–2026 at $0 —
(1) IVV varnish-api month-end loop (low, dense SPX); (2) **Wayback IVV `aaData` JSON (low, dense SPX,
varnish-independent)**; (3) QQQ NPORT-P EDGAR parse (med, quarterly NDX); (4) SPY NPORT-P (SPX
cross-check); (5) Wayback SPY XLSX + Invesco QQQ CSV (sparse gap-fill); (6) live dng-api / SPY XLSX
(forward only).

### Constraint gates
| Gate | Result | Note |
|------|--------|------|
| 1 Latency | N-A | Research data assembly; not a live signal |
| 2 Access | **PASS** | No broker orders; all sources public/free web + SEC |
| 3 Session | N-A | Holdings history, not a hold rule |
| 4 Data | **PASS** | Full recipe $0; two independent SPX paths + free EDGAR NDX |
| 5 Fill realism | N-A | Weights for mechanism tests, not fills |
| 6 Statistics | **PASS (construction)** | SPX ≈102 weight-dates + NDX ≈27 quarter-ends in-window |
| 7 Protocol | **PASS** | Deterministic pipeline; charges no alpha trial family |

Survivor-profile score (as **data enabler**): **5/5** source-fitness — deterministic once built, $0,
clear legal/issuer mechanism, depth ≥2020 (SPX ~monthly, NDX quarterly), effect N-A. **Trade
survivor score N-A** (this is infrastructure, not an edge candidate).

### Economics sketch
Expected gross: N-A (no alpha claim). Cost burden: **$0** one-time assembly (HTTP + XML/CSV/JSON
parse; SEC fair-access UA, avoid "naver" token; ≤10 req/s). Net prior: unlocks PIT SPX weights at
month-end (or better recent) via TWO redundant paths and NDX at public NPORT quarter-ends for
2020–2026 without paying index licensors (vendor PIT-constituent history = $hundreds–thousands/yr).
Comparison line retained: "champion = +2.5 bps/event dev / +12.5 holdout" — this scout claims no
edge; it unblocks PassiveForce / index-LETF attribution that would otherwise be OPEN-BLOCKED on data.

### Proposed next test (only if OPEN-TESTABLE)
**Hypothesis:** A machine-built table `{asof_date, index∈{SPX,NDX}, ticker, weight, source}` covering
**≥24 quarter-ends 2020Q1–2026Q2** for both indices (SPX also ≥72 month-ends) is constructible at $0
with weight-sum ≈1 and mega-cap ranks matching known history.
**Named payer:** N-A (data QA). **Data:** owned none; BlackRock varnish-api free; Wayback free; SEC
EDGAR free (declared UA with contact, no "naver"). **Universe:** IVV (SPX), QQQ (NDX); SPY NPORT
cross-check. **Expected n:** SPX month-ends ≈78; NDX public NPORT ≈24–28 quarter-ends; power N-A —
use coverage + sum-of-weights gates.
**A-priori thresholds / promotion:**
1. Build IVV month-end weights via varnish-api (`asOfDate` = last NYSE session); reject `as of,"-"`
   or body <10 KB. In parallel, build the **Wayback IVV `aaData`** panel (C5 filter) and reconcile
   the two SPX sources (weights within tolerance on overlapping dates = pipeline validation).
2. Pull all public QQQ NPORT-P 2020–2026 from submissions JSON + `primary_doc.xml`; map pctVal →
   weight (units: percent of NAV, e.g. 1.73 = 1.73%).
3. QA 8 quarter-ends (2/yr 2020/22/24/26): top-10 IVV(varnish) vs IVV(Wayback) vs SPY(NPORT);
   QQQ NPORT vs dng-api on latest overlap; weight-sum ex-cash ∈ [0.98, 1.02].
4. **Promote** if ≥7/8 quarters pass and SPX month-end coverage ≥95% of trading month-ends.
5. **Kill/degrade** if BOTH varnish-api AND Wayback-IVV fail >20% of month-ends → SPY NPORT quarterly
   only for SPX; if QQQ NPORT incomplete → Wayback QQQ CSV + N-CSRS (flag NDX quarterly-sparse).
**Kill criteria:** cannot reach quarterly NDX AND monthly SPX 2020–2026 at $0 (or ≤$20 if amended).
**Trial family charged:** none (data prep for M12 Cell B / A2).

---

### SOURCE RECIPE (deliverable — data reachability)

#### Per-source table
| Source | URL pattern | History density (2020–2026) | Effort | Role |
|--------|-------------|-----------------------------|--------|------|
| **BlackRock varnish-api (IVV)** | `blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document?...&portfolioId={239726\|239763\|239774}&asOfDate=YYYYMMDD&component=holdings` | Live historical month-ends ≥2010 + recent dailies (trading-day dates) | Low–med (date loop) | **Primary SPX (IVV)** |
| **Wayback IVV `aaData` JSON** | CDX `ishares.com/us/products/239726/.../1467271812596.ajax` → filter `mime=application/json`, len≈30–120 KB → `web.archive.org/web/<ts>id_/<original>` | **≈102 distinct as-of dates** (better-than-monthly 2023–26; ~monthly 2020–22); full 500-name weights | Low | **Redundant SPX (varnish-independent)** |
| **SEC NPORT-P QQQ** | EDGAR CIK `0001067839`, form `NPORT-P` → `primary_doc.xml` `<invstOrSec>` | Public quarter-ends, **27 filings** 2019–2026 (~4/yr) | Med (XML + UA) | **Primary NDX history** |
| **SEC NPORT-P SPY** | CIK `0000884394`, `NPORT-P` | Quarterly public | Med | SPX cross-check |
| **SSGA SPY daily XLSX** | `ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx` | Wayback **n=19** irregular (+7 institutional path) | Low | Forward collector / sparse backfill |
| **Invesco QQQ download CSV** | `.../holdings/main/holdings/0?audienceType=Investor&action=download&ticker=QQQ` (Weight+Date cols) | Wayback **≈14** QQQ 200s; live 301 dead | Low | Sparse NDX backfill |
| **Invesco dng-api (live)** | `dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46090E103/holdings/fund?idType=cusip&productType=ETF` | Live snapshot; 0 Wayback | Low | Forward NDX collector |
| **iShares ajax (bare HTTP)** | `ishares.com/us/products/{pid}/...ajax?fileType=csv&asOfDate=YYYYMMDD` | SPA shell from this box | High/fragile | **Avoid** — use varnish-api or Wayback |
| **Nasdaq NDX Weighting page** | `indexes.nasdaqomx.com/Index/Weighting/NDX` | Wayback 41 caps 2013–26; full-table serialization UNVERIFIED | Med | Supplementary NDX (verify payload first) |
| **ETF.com / Nasdaq factsheets Wayback** | `etf.com/{QQQ,SPY}`; FS_XNDX.pdf | Top-10 marketing only | High/low-yield | Optional top-10 cross-check |

#### Recommended assembly recipe (quarterly-or-better NDX/SPX, 2020–2026, $0)
1. **SPX weights (target monthly), two redundant sources:**
   a. For each month 2020-01…2026-06, `asOfDate`=last NYSE session (YYYYMMDD); GET varnish-api
      `portfolioId=239726`; parse CSV Ticker/Weight(%).
   b. In parallel, from Wayback CDX of the IVV `.ajax` (matchType=prefix, limit high), keep
      `mimetype=application/json & statuscode=200 & 30 KB≲length≲120 KB`, dedupe `asOfDate`, fetch
      each raw body via `.../web/<ts>id_/<original>`, parse `aaData` rows → (ticker, weight `raw`).
   c. Reconcile (a)&(b) on overlapping dates = built-in QA; weight-sum ex-cash ∈ [0.98,1.02].
2. **NDX weights (target quarterly public):** from `data.sec.gov/submissions/CIK0001067839.json`
   (UA `AppName contact@email`, NOT containing "naver") list 27 NPORT-P; download each
   `primary_doc.xml`; extract `invstOrSec` → weight=pctVal/100 (verify sum≈1); CUSIP→ticker via owned
   map / OpenFIGI. Densify optionally with Wayback QQQ CSV (~14) — do not claim dense daily NDX.
3. **Forward (optional, $0):** daily cron on SPY XLSX + Invesco dng-api to stop relying on IA after
   the scout date.
4. **Do not:** scrape `ishares.com` ajax bare (SPA shell); use a SEC UA containing "naver"; treat
   Yahoo/Schwab/ETF.com top-10 as full index weights.

### Sources
1. [T1] SSGA SPY holdings XLSX live + Wayback — ssga.com/library-content/.../holdings-daily-us-en-spy.xlsx — 07-17 + 07-21
2. [T1] Internet Archive CDX API + `id_` replay — SPY XLSX, Invesco download, iShares IVV ajax, Nasdaq Weighting, ETF.com — 07-17 + 07-21 (IVV `aaData` body byte-verified)
3. [T1] Invesco QQQ product page + dng-api JSON + legacy download CSV — invesco.com/... ; dng-api.invesco.com/.../46090E103/holdings/fund — 07-17 / 07-21
4. [T1] BlackRock varnish-api IVV/IJH/IJR `asOfDate` CSVs — portfolioIds 239726/239763/239774 — 07-17
5. [T1] SEC data.sec.gov/submissions CIK 0001067839 (QQQ, 27 NPORT-P), 0000884394 (SPY); NPORT-P `primary_doc.xml` — 07-21 / 07-17
6. [T1] SEC fund-reporting modernization (N-PORT applies to UIT ETFs) — release/law-firm summaries; QQQ prospectus N-PORT exhibit language
7. [T3] etf-scraper (PyPI) / talsan/ishares (GitHub) — month-end iShares history ~2010+, `FIRST_AVAILABLE_HOLDINGS_DATE=2006-09-29`, ScrapingBee (live scrape needs bot-evasion) — pypi.org/project/etf-scraper ; github.com/talsan/ishares
8. [T1] Nasdaq index pages — indexes.nasdaqomx.com/Index/Weighting/NDX + FS_XNDX.pdf factsheet — 07-21

#### Queries used
- WebSearch: `Invesco QQQ holdings download CSV URL endpoint invesco.com product detail`
- WebSearch: `SSGA SPY daily holdings xlsx URL library-content fund-data`
- WebSearch: `Invesco QQQ Trust Series 1 UIT SEC N-30D N-CEN holdings filing form annual report`
- WebSearch: `iShares IVV holdings CSV asOfDate parameter historical month-end download url pattern`
- WebSearch: `invesco.com etfs holdings action=download ticker=QQQ audienceType CSV endpoint`
- WebSearch: `Nasdaq-100 index weightings historical factsheet download indexes.nasdaqomx.com quarterly rebalance`
- WebSearch: `iShares IJH IJR product id url 239763 239774 core mid small cap holdings`
- CDX: `ssga.com/library-content/.../holdings-daily-us-en-spy.xlsx` (+ `/us/en/individual/` and `/us/en/institutional/` variants)
- CDX: `ishares.com/us/products/239726/ishares-core-sp-500-etf/1467271812596.ajax&matchType=prefix` (density + asOfDate extraction + mimetype/length filtering)
- CDX: `invesco.com/us/financial-products/etfs/holdings/main/holdings/0` filter `ticker=QQQ` / `action=download`
- CDX: `indexes.nasdaqomx.com/Index/Weighting/NDX` ; `indexes.nasdaq.com/Index/Weighting/NDX`
- Live probe: iShares IVV `.ajax?fileType=csv&asOfDate=20240628`/`20240627` (browser UA → SPA shell)
- Wayback `id_` replay: IVV asOfDate=20161130 (body: `aaData`, 505 Equity rows, ISIN count, weight `raw`)
- curl EDGAR: `data.sec.gov/submissions/CIK0001067839.json`
- WebFetch: github.com/talsan/ishares config (`FIRST_AVAILABLE_HOLDINGS_DATE`, ajax id)
