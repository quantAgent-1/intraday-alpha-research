## DR-X2 — B primary/venue findings
### Verdict recommendation
OPEN-TESTABLE (confidence HIGH) — Best free path is a **two-source recipe**, not a single vendor: **(1) primary truth = SEC EDGAR Form 8-K Item 2.02 `acceptanceDateTime`** (T1, $0, session-classifiable to BMO/AMC/during from ET hour); **(2) bootstrap/coverage = yfinance `Ticker.get_earnings_dates`** ($0, machine-readable, timestamps already encode BMO≈06–08 ET vs AMC≈16:00 ET, depth ≫2020 for megacaps). Vendor free tiers fail the window: Finnhub free = **1 month** history only; Alpha Vantage `EARNINGS` = fiscal period-end not announcement date / `EARNINGS_CALENDAR` = forward horizon only, no reliable historical BMO/AMC; FMP docs advertise `bmo`/`amc` but demo keys 401 and FAQ flags calendar endpoints as often premium; Nasdaq/Zacks are UI + bot-wall, not a stable free bulk API. Paid ≤$20 fallback if DIY fails: **EODHD Corporate Events Calendar** (~$19.99/mo) with explicit `before_after_market` field and multi-year history.

What would flip it: empirical validation fail rate >5% on a 20-name-quarter stratified sample vs company IR press-release times (i.e. SEC acceptance session-bucket disagrees with IR on BMO vs AMC), or discovery that >~15% of the 33-name set’s quarterly earnings lack a clean Item 2.02 8-K (then promote EODHD/FMP paid one-shot).

### Mechanism
No trading payer — this is a **calendar-flag data unblocking** charge for Q13 earnings-day diagnostic on owned NOII (2020–2026, 33 names). Wrong announcement dates / wrong BMO-vs-AMC poison pre- vs post-gap assignment: AMC same-day close = pre-announcement; next close = post-gap. Source must distinguish session timing. SEC Item 2.02 is the legal furnishing vehicle for earnings press releases (Reg FD / Form 8-K), so acceptance timestamp is the highest-authority free proxy for public-dissemination time; Yahoo/yfinance is a secondary aggregate convenient for fill but lower authority.

### Claims
C1 [CONFIRMED] (T1, 2026-07-17 live probe, sample AAPL/JPM/BAC/MSFT/NVDA/TSLA 2024–2026): SEC `data.sec.gov/submissions` returns columnar `form`, `items`, `acceptanceDateTime` for 8-Ks; filtering `form=="8-K"` and `"2.02" in items` yields acceptance hours that correctly separate bank BMO (~06:30–06:50 ET JPM/BAC) from tech AMC (~16:03–16:30 ET AAPL/MSFT/NVDA) — https://data.sec.gov/submissions/CIK##########.json ; https://www.sec.gov/search-filings/edgar-application-programming-interfaces

C2 [CONFIRMED] (T1, SEC bulk/API docs, reviewed 2025-04-08): Submissions API is free, no API key; fair-access ~10 req/s with declared User-Agent; recent block ≤1000 filings; older history via `filings.files[]` archive JSON parts and/or nightly `submissions.zip` bulk — https://www.sec.gov/search-filings/edgar-application-programming-interfaces ; https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip

C3 [CONFIRMED] (T3, 2026-07-17 live probe yfinance, sample 10 megacaps): `get_earnings_dates(limit=80)` returns DataFrame indexed by tz-aware ET timestamps with columns EPS Estimate / Reported EPS / Surprise(%); hour distribution maps BMO (JPM/BAC/WFC hour=6, C hour=8) vs AMC (AAPL/MSFT/NVDA/GOOGL/AMZN hour=16); reported history n≈48–99 quarters, oldest well before 2020 — library API, Yahoo-backed

C4 [CONFIRMED] (T3, Finnhub pricing/docs, 2026): Free-tier Earnings Calendar history = **1 month** (+ realtime updates US); 20-year history is paid All-In-One — fails 2020–2026 requirement — https://finnhub.io/pricing ; https://finnhub.io/docs/api/earnings-calendar

C5 [CONFIRMED] (T3, Alpha Vantage docs + live IBM demo 2026-07-17): `function=EARNINGS` returns `fiscalDateEnding` + EPS, **not** announcement date/time; `EARNINGS_CALENDAR` is forward `horizon` CSV (3/6/12 month), not multi-year historical BMO/AMC archive — https://www.alphavantage.co/documentation/

C6 [PLAUSIBLE] (T3, FMP docs/FAQ 2025–2026): FMP documents per-symbol earnings with `bmo`/`amc` timing and historical calendar endpoints (`/stable/earnings?symbol=`, legacy `/api/v3/historical/earning_calendar/{sym}`); free plan ~250 calls/day; FAQ states some calendar endpoints are premium-only — free usability for full 33×~28 quarters needs a real key and plan check before commit — https://site.financialmodelingprep.com/developer/docs/stable/earnings-company ; https://site.financialmodelingprep.com/faqs

C7 [CONFIRMED] (T3, EODHD docs 2026): `GET /api/calendar/earnings` returns `report_date` + `before_after_market` ∈ {BeforeMarket, AfterMarket, null}; symbol-list and date-window modes; history “from the beginning”; standalone calendar product marketed ~$19.99/mo (within ≤$20 one-month budget); free = 20 calls/day insufficient for bulk rebuild — https://eodhd.com/financial-apis/calendar-upcoming-earnings-ipos-and-splits ; https://eodhd.com/lp/calendar-and-news-api

C8 [PLAUSIBLE] (T3/T4, Nasdaq earnings page + Zacks attribution): Nasdaq earnings calendar shows Pre-Market / After Hours / Time Not Supplied and attributes data to Zacks; web-only / scraper-hostile; **not** a reliable free machine-readable bulk source for 2020–2026 — https://www.nasdaq.com/market-activity/earnings

C9 [CONFIRMED] (T1, Form 8-K Item 2.02): Public announcement of completed-period results triggers Item 2.02 furnishing with press-release exhibit; acceptance time is public dissemination clock on EDGAR (not identical to newswire, but same session for US megacap practice in probed sample) — https://www.sec.gov/files/form8-k.pdf

C10 [UNVERIFIED] (T3): Exact free-vs-premium lock on FMP historical `time` field for all 33 names 2020–2026 without a registered key — treat as UNKNOWN until key test.

### Constraint gates
| Gate | Result | Note |
|------|--------|------|
| 1 Latency | N-A | Data-scout calendar build; not a live signal path |
| 2 Access | N-A | Research data only; no broker order types required |
| 3 Session | N-A | Diagnostic bookkeeping on owned NOII; not a hold rule |
| 4 Data | **PASS** | Primary recipe $0 (SEC + yfinance); optional EODHD ≤$20 one-month if DIY stalls |
| 5 Fill realism | N-A | No fills; calendar flags only |
| 6 Statistics | N-A | Source selection; diagnostic n later from 33×~4–6 yrs quarters |
| 7 Protocol | N-A | Infrastructure for Q13; not a trial family by itself |

Survivor-profile score: **4/5** (as data enabler, not a trade): (1) single-print N-A→0 for trade, but calendar is deterministic once dates fixed → score as data; point tally for *source fitness*: scheduled/testable=1, retail-cheap=1, mechanism-clear (Item 2.02)=1, history depth=1, effect N-A. **Trade survivor score N-A** — this charge does not propose a strategy.

### Economics sketch
Expected gross: N-A (no alpha claim). Cost burden: **$0** for SEC+yfinance recipe; optional **≤$20** one-month EODHD. Net prior: unlocks $0 calendar-flag test on owned NOII. Comparison line: "champion = +2.5 bps/event dev / +12.5 holdout" — this source does not move champion economics; it only protects Q13 from date-poisoning false nulls/false positives.

### Proposed next test (only if OPEN-TESTABLE)
**Hypothesis:** A machine-built table `{symbol, announce_date_ET, session ∈ {BMO,AMC,DURING,UNKNOWN}, source, accession}` for 33 names × 2020-01-01…2026-07 covers ≥95% of quarterly earnings with session label agreeing with company IR on a holdout sample.

**Named payer:** N-A (data QA).

**Data needed:** owned none beyond CIK map; SEC free + yfinance free; optional EODHD $≤20.

**Universe:** the same 33 NOII names as M11/Q13.

**Expected n:** ~33 × 26 quarters ≈ **850** name-quarters (2020Q1–2026Q2); power N-A for source QA — use **agreement rate** not bps.

**A-priori thresholds / promotion:**
- Build SEC primary calendar (recipe below).
- Cross-fill gaps from yfinance only when SEC has no 2.02 within ±1 calendar day of yfinance date.
- **Validation plan (mandatory before any Q13 gate):** sample **20 stratified name-quarters** (mix AMC tech, BMO banks, 2020 vs 2025, at least 2 “messy” names e.g. TSLA multi-2.02, one bank heavy-filer). For each, open company IR newsroom / press-release timestamp (or GlobeNewswire/BusinessWire page). Score: date match exact; session bucket match (BMO if release <09:30 ET; AMC if ≥16:00 ET; DURING else).
- **Promote source if** session agreement ≥19/20 and date agreement ≥19/20.
- **Kill / fallback if** session agreement ≤17/20 → purchase one month EODHD calendar, re-run same 20, then full rebuild if EODHD ≥19/20.

**Kill criteria:** cannot reach ≥90% labeled coverage on 33 names without paid data >$20.

**Trial family charged:** none yet (data prep for Q13 earnings-day diagnostic family when registered).

---

### SOURCE RECIPE (deliverable — not the dataset)

#### Primary — SEC EDGAR Item 2.02 acceptance (accuracy-first, $0)

**Access method:**
1. Ticker→CIK: `https://www.sec.gov/files/company_tickers.json` (or company_tickers_exchange.json).
2. Per CIK: `GET https://data.sec.gov/submissions/CIK{cik:010d}.json` with header `User-Agent: {AppName} {contact@email}` (required).
3. From `filings.recent`: zip arrays `form`, `items`, `acceptanceDateTime`, `filingDate`, `accessionNumber`, `primaryDocument`.
4. Keep rows where `form in {"8-K","8-K/A"}` and `items` contains `2.02`.
5. Convert `acceptanceDateTime` (UTC Z) → America/New_York. Session rule (a-priori):
   - `time < 09:30` → **BMO**
   - `time >= 16:00` → **AMC**
   - else → **DURING**
6. **Earnings disambiguation (required for multi-2.02 names):** keep quarterly cadence (~1 per fiscal quarter); drop amendments that only restate; optional keyword check on primary doc / EX-99.1 (“results of operations”, “earnings”, “quarter ended”). TSLA-class names show ~8 Item 2.02/year — do **not** treat every 2.02 as an earnings day.
7. **History depth for heavy filers (banks):** if target quarter not in `recent` (≤1000 filings), walk `filings.files[]` archive parts (`https://data.sec.gov/submissions/{name}`) whose `filingFrom`/`filingTo` overlap 2020–2026, **or** download nightly bulk `https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip` once and filter offline (preferred for 33 names).
8. **Rate limits:** ≤10 req/s per SEC fair-access policy; bulk zip preferred over chatty per-file crawling for banks (JPM alone has 60+ archive parts historically).
9. **DIY effort (honest):** ~0.5–1 day for clean tech names; **1–2 days** engineering for robust multi-2.02 filters + bank archive pagination; runtime minutes with bulk zip. **Not zero-effort** — but free, T1, and session-accurate on live probe.

**Timing-field reliability:** HIGH for session **bucket** (BMO vs AMC) on megacap earnings 8-Ks in probe; MED for exact minute vs newswire; MED-LOW if Item 2.02 non-earnings not filtered.

#### Runner-up — yfinance `get_earnings_dates` (bootstrap, $0)

**Access method:**
```python
# pip install yfinance
import yfinance as yf
df = yf.Ticker("AAPL").get_earnings_dates(limit=80)  # index = ET timestamp
# session: hour <= 9 -> BMO; hour >= 16 -> AMC; else DURING/UNKNOWN
```
- No API key; ~33 calls for full universe; re-pull if Yahoo shape breaks (historical breakage risk — library issues #1953, #2552, #2566).
- **History depth:** confirmed reported rows back through 2000s for AAPL/JPM/MU/AMD/INTC; **covers 2020–2026**.
- **Timing reliability:** MED — hours are coarse conventions (16:00 not 16:30; banks 06:00/07:00/08:00) but **bucket-correct** on probe set; occasional dirty duplicate/surprise rows → drop rows with null Reported EPS for historical completed events.
- **Use:** fill symbol-quarters where SEC pipeline gaps; never override SEC when both present and session disagrees without IR check.

#### Paid fallback — EODHD calendar (≤$20)

- `GET https://eodhd.com/api/calendar/earnings?symbols=AAPL.US,...&api_token=TOKEN&fmt=json`
- Field: `before_after_market` = BeforeMarket | AfterMarket | null; `report_date`.
- Buy **one month** Corporate Events Calendar / plan that includes calendar (~$19.99 marketed), dump all 33 symbols, cancel. Free 20 calls/day insufficient.

#### Rejected / insufficient alone
| Source | Why not primary |
|--------|-----------------|
| Finnhub free | 1 month history only |
| Alpha Vantage free | No historical announcement+BMO/AMC archive |
| FMP free | Timing claimed but free/premium gate + no verified key probe; re-check only if SEC DIY blocked |
| Nasdaq.com / Zacks web | UI/scrape, bot walls, Zacks commercial behind Nasdaq page; not bulk machine recipe |
| sec-api.io paid datasets | Exceeds free/≤$20 intent when official EDGAR already exposes acceptance times |

### Sources
1. [T1] SEC EDGAR Application Programming Interfaces — submissions JSON, bulk zip, rate policy context (page updated 2025-04-08; fetched 2026-07-17). https://www.sec.gov/search-filings/edgar-application-programming-interfaces
2. [T1] SEC Form 8-K (Item 2.02 Results of Operations). https://www.sec.gov/files/form8-k.pdf
3. [T1] SEC Developer / fair-access: ≤10 req/s, User-Agent required. https://www.sec.gov/about/webmaster-frequently-asked-questions
4. [T1/T3] Live EDGAR probe 2026-07-17: AAPL/JPM/BAC/MSFT/NVDA/TSLA Item 2.02 acceptanceDateTime session separation (agent run).
5. [T3] yfinance `Ticker.get_earnings_dates` docs + live probe 2026-07-17 (AAPL/JPM/BAC/C/WFC/TSLA/NVDA/GOOGL/AMZN/MSFT/MU/AMD/INTC). https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.get_earnings_dates.html
6. [T3] Finnhub pricing — Earnings Calendar free vs paid history depth. https://finnhub.io/pricing
7. [T3] Alpha Vantage documentation — EARNINGS / EARNINGS_CALENDAR. https://www.alphavantage.co/documentation/
8. [T3] FMP Earnings Report / Calendar docs + FAQ (free limits; premium calendar note). https://site.financialmodelingprep.com/developer/docs/stable/earnings-company ; https://site.financialmodelingprep.com/faqs
9. [T3] EODHD Calendar API — `before_after_market` schema + pricing context. https://eodhd.com/financial-apis/calendar-upcoming-earnings-ipos-and-splits
10. [T3] Nasdaq Earnings Calendar (Zacks provider attribution). https://www.nasdaq.com/market-activity/earnings

#### Queries used
- historical earnings announcement dates BMO AMC free API machine readable
- yfinance get_earnings_dates BMO AMC session timing accuracy
- SEC EDGAR 8-K Item 2.02 earnings release acceptance timestamp historical bulk download
- Financial Modeling Prep FMP free tier earnings calendar historical BMO AMC
- Alpha Vantage earnings calendar free API historical dates timing
- Nasdaq.com earnings calendar historical archive BMO AMC scrape API
- SEC EDGAR 8-K acceptance time vs actual earnings press release BMO AMC accuracy
- Finnhub free tier historical earnings calendar hour BMO AMC limit
- FMP historical earning_calendar AAPL time bmo amc free plan limit 250
- EODHD earnings calendar free plan price historical reportTime BMO AMC
- yfinance get_earnings_dates columns EPS Estimate Reported Surprise time
- SEC EDGAR free API submissions.json 8-K acceptanceDateTime Item 2.02 rate limit
- Zacks earnings calendar historical free download BMO AMC
- FMP free plan earnings calendar premium only historical time field
