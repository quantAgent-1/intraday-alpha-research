# DR-X6 — Point-in-time index-weight archive reachability

**Synthesis date:** 2026-07-18  
**Agents:** 1 light modality B (scout) + **2 independent refuter waves** (`refute-1.md`, `refute-2.md`)  
**Refuter status:** All 5 load-bearing claims **unrefuted** (0/5 refuted) on independent live re-probes: SPY CDX n=19 year-split exact; QQQ legacy 301 + ~6 CSV; varnish-api IVV historical real; QQQ NPORT-P full weights; $0 quarterly-or-better recipe stands. Residual risk is build QA (sum-of-weights), not reachability.

### Synthesis
Wayback is **not** a dense free daily archive for SPY/QQQ holdings (SPY XLSX ≈ **19** distinct digests 2020–2026; QQQ download CSVs ≈ **6**). That does **not** block M12 Cell B / A2: free **monthly SPX** via BlackRock varnish-api (IVV) and free **quarterly NDX** via QQQ **NPORT-P** XML are live-verified.

## Verdict recommendation
**OPEN-TESTABLE** (confidence **HIGH** on $0 quarterly-or-better recipe; **do not claim dense free daily NDX**)

**What would flip it:** varnish-api historical `asOfDate` bot-gates or empties >20% of month-ends; **or** public QQQ NPORT-P missing full equity schedule for material 2020–2022 quarters.

### Mechanism
N-A (data enabler). Weights proxy SPX/NDX membership for PassiveForce / index-LETF attribution.

### Claims
C1 [CONFIRMED] (T1 live+CDX): SPY daily XLSX live snapshot; Wayback **n=19** digests (2020:5 … 2023:0 … 2026:1) — sparse.  
C2 [CONFIRMED] (T1): QQQ legacy download live **301 dead**; Wayback CSV ~**6**; dng-api live snapshot only.  
C3 [CONFIRMED] (T1 live): BlackRock varnish-api IVV/IJH/IJR with `asOfDate` returns real holdings CSV; month-ends ≥2010; use **trading-day** dates. iShares bare ajax → HTML shell.  
C4 [CONFIRMED] (T1 SEC): QQQ CIK 0001067839 files **NPORT-P** with full `<invstOrSec>` + `pctVal` (sample n=102). Public = quarter-end + lag.  
C5 [CONFIRMED] (T1 synthesis): $0 recipe = IVV monthly + QQQ NPORT quarterly + sparse Wayback fill + forward SPY/dng collectors.

### Constraint gates
Data gate **PASS** at $0. Other gates N-A (not a trade).

### Economics sketch
$0 assembly; unblocks M12 Cell B PassiveForce and A2 index-LETF leg. Champion line N-A.

### Recommended assembly recipe (deliverable)
1. **SPX monthly:** loop last NYSE day each month →  
   `https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document?...&portfolioId=239726&asOfDate=YYYYMMDD&component=holdings`  
2. **NDX quarterly:** `data.sec.gov/submissions/CIK0001067839.json` → NPORT-P `primary_doc.xml` → `pctVal/100`. Declared User-Agent; no “naver”.  
3. **Fill:** Wayback SPY XLSX + QQQ CSV digests only.  
4. **Forward:** daily SPY XLSX + Invesco dng-api `46090E103`.  
5. **QA:** 8 quarter-ends weight-sum ∈ [0.98,1.02]; promote if ≥7/8 pass and SPX month-end coverage ≥95%.

### Proposed next test
Build the weight table (engineering, not research family). No ledger write. Kill only if both monthly SPX and quarterly NDX unreachable without paid >$0.

### Sources
`modality-B.md` (full per-source table + queries).

---

## Addendum — wave-3 verification pass (2026-07-21, 1 Opus re-verify agent; byte-verified live, no refuters needed)

Verdict STANDS (OPEN-TESTABLE HIGH, $0 recipe). Deltas — recipe gains redundancy:

1. **New varnish-independent SPX path (byte-verified):** Wayback holds **391 captures / 185 distinct asOfDates** of the iShares IVV `.ajax` endpoint; raw `id_` replay returns real `{"aaData":[...]}` JSON with 505 constituents + per-name weights (~102 in-window dates, better-than-monthly 2023–26). Filter CDX on `mimetype=application/json` + compressed length ≈30–120KB to skip SPA-shell captures. Use as fallback if varnish-api ever bot-gates (the stated flip condition now has a mitigation).
2. **NDX quarterly re-confirmed on EDGAR:** QQQ Trust (CIK 0001067839) NPORT-P — **27 accessions 2019→2026**, `primary_doc.xml` carries pctVal weights.
3. Sparse paths re-confirmed: SPY XLSX 19 irregular Wayback dates (none in 2023); QQQ download CSV ~14; live iShares bare `.ajax` still bot-gated from this box.
4. Assembly remains engineering (no research family, no ledger write); M12 Cell B / A2 unblocked at $0.
