# DR-Q1-3 — Closing-cross payer decomposition & passive-ownership scaling

**Date:** 2026-07-17
**Mode:** Wave-2 deep-dive (OPEN_QUESTIONS #1, #2, #3-residual)
**Agents:** 4 modality + 3 claim-refuters completed (payer-scaling bundle 1/2 — twin lost to a session limit after its pair confirmed at full text; adv+data bundle 2/2)
**Orchestrator synthesis — not delegated**

### Synthesis

| Lane | Verdict rec | Core thrust |
|------|-------------|-------------|
| A | OPEN-TESTABLE (MED) | Passive/ETF ownership robustly predicts auction VOLUME; name-selectivity unresolved in lit; pre-registrable scaling form |
| B | OPEN-TESTABLE (HIGH data) | Free data path: ETF holdings files + SEC 13F/N-PORT bulk; official GIW/S&P licenses NOT needed |
| C | OPEN-TESTABLE (MED) | Multi-payer decomposition; index MOC small on normal days (~5.5%) vs ~41% on rebal days; PassiveForce score |
| D | EXHAUSTED-BY-FIELD (MED) on scaling | Internalization censors the feed; auctions absorb indexed flow; ITG post-print null; NVDA = tournament winner |

**Dissents & refuter resolutions:**
1. **A/C vs D is not a factual conflict — it is volume vs price.** Refuter-confirmed B&M (full text): passive/ETF ownership → auction TURNOVER (elasticity real, active ≈ 0) **and** deviations insignificant once turnover is controlled (adds/deletes absorbed). The field supports "passive pays the cross" as payer identity and rejects "more passive ⇒ more unarbed basis" as an automatic price effect. Whether passive weight explains OUR names' basis persistence is not settled either way — that is precisely the cheap owned-data test.
2. **D's ITG anchor survives but weakened as a kill** (refuters, full text): the zero-drift window is first-print→16:00 CONTINUOUS end, not to the closing print; ITG itself documents a median ~0.5-spread predictable-direction move from the 4pm quote INTO the print; the "not profitable" sentence's direct referent is beat-the-close self-impact. 2012 mechanics, DECAY-UNKNOWN. Our own ledgered +2.5 bps / 63% on |basis|≥10 (n≈8k, 6 years) is direct evidence the conditional tail ITG never tested is non-empty.
3. **D's internalization censoring is real and matters** (refuters, T1 verbatim): ~23% of closing-price volume in NYSE-listed names prints off-exchange and is excluded from imbalance/paired feed quantities (NYSE 2022; exchange-authored stat, CONFLICTED tag; nuance: internalized interest partially correlates with published imbalance). Ownership STOCK → visible imbalance FLOW mapping is censored; any scaling test must treat ownership as a noisy instrument, not a direct measure.
4. **Data path verified live with two degradations** (refuter, 2026-07-17): SPY daily holdings XLSX = T1-live but snapshot-only (history requires Wayback/self-archive); iShares historical `asOfDate` CSV endpoint is bot-gated for automation (UNVERIFIED-AUTOMATION-BLOCKED; community tooling suggests browser sessions work); SEC 13F (2013Q2→) and N-PORT (2019Q4→) bulk confirmed free — with the caveat that N-PORT public granularity is effectively QUARTERLY for most of the archive. QQQ/Invesco daily-holdings history was NOT refuter-verified this wave — verify at build time.

### Verdict (orchestrator)

**`OPEN-TESTABLE`** (confidence **MED**) — as a **$0, kill-oriented, pre-registered cross-sectional diagnostic** with D's field priors as the explicit null. NOT as a promotion-seeking scaling family: the field prediction is a weak-to-null slope in liquid names, and the test's value is mechanism resolution for the name-focus question either way.

**Priority demotion within the wave:** DR-X1's LETF-AUM(t) variable now leads the name-selectivity race — it has sharper identification (a 10x within-name AUM change in H1-2026 coinciding with the holdout window) than slow-moving passive weights. **Recommendation: register ONE name-selectivity mechanism family (working title M12) carrying BOTH pre-registered variables** — PassiveForce (this lane) and LETF-F/ADV (DR-X1) — as competing regressors in the same design, one family charge, horse-race framing.

What would flip to EXHAUSTED: pre-registered panel shows neither variable separates alive from dead names (esp. both failing the GOOGL counter-example) at n≥250/tercile with controls — then name-focus has no mechanism and forward-paper NVDA/TSLA is downgraded to pure luck-monitoring.

### Mechanism (post-refute consensus)

Payer identity CONFIRMED and now decomposed: price-insensitive close flow = index-tracker/passive-MF NAV flow (small on normal days ~5.5% of close notional; ~41% on rebal days), ETF create/redeem netting into constituents, month-end/OpEx episodic hedge unwinds; ~23% of close-priced demand internalizes off-exchange and never shows in NOII; echo/GMOC prints another ~30% of MOC-priced volume off-feed. The VISIBLE 15:55 imbalance is a censored residual — consistent with the champion harvesting what offsetting liquidity has not yet arbed in the 15:55→16:00 window (BMLL: convergence completes ~15:57-15:58; Mackintosh: ~80% of the NOII price move is impounded within 300ms of first print — the residual after the first second is the manual-latency-harvestable slice, which is what the champion measures).

NOII cadence locked at T1 (multi-source + owned-data match): reference/paired/imbalance every 10s from 15:50; near/far populated from ~15:55:00, 1s cadence to 16:00.

### Claims (load-bearing, post-refute)

| ID | Status | Claim |
|----|--------|-------|
| C1 | **CONFIRMED** (T2 full text, refuter) | B&M JFM 2023 (2010-18): passive/ETF ownership → auction turnover (active ≈0); large-cap mean |dev| 2.66 bps, 68.5% at bid/ask; add/delete deviations insignificant once turnover controlled; auction share 3.11%→7.48% |
| C2 | **CONFIRMED** (T3, refuter; conflict-noted) | Mackintosh 2020: normal-day index MOC ≈5.5% of close notional; rebal-day ~41%; $300B/yr figure is secondhand (Credit Suisse, unlocated) |
| C3 | **CONFIRMED** (T1 mechanics, refuter ×2; stat CONFLICTED) | NYSE 2022: ~23% of closing-price volume internalized, EXCLUDED from imbalance/paired feed fields; high-internalization names show higher auction slippage |
| C4 | **CONFIRMED-weakened** (T3 full text, refuter ×2) | ITG 2012 (authors Bacidore/Polidore/Xu/Yang — lane D's author list corrected): post-first-print drift ≈0 to 16:00; median ~0.5-spread predictable-direction move 4pm→print; beat-the-close unprofitable. 2012 mechanics, DECAY-UNKNOWN |
| C5 | **CONFIRMED** (T1 live probes, refuter ×2) | Free data: SPY XLSX live (snapshot-only); SEC 13F bulk 2013Q2→, N-PORT 2019Q4→ (quarterly-public granularity); iShares asOfDate endpoint bot-gated (browser-only until proven); QQQ history UNVERIFIED this wave |
| C6 | **CONFIRMED** (T1 multi-source + owned data) | NOII: 10s cadence 15:50-15:55 (no near/far), 1s with near/far 15:55-16:00 |
| C7 | PLAUSIBLE (T3, BMLL/Mackintosh) | Late-window convergence 15:57-15:58; ~80% of NOII move impounded in 300ms; offsetter premium ~1.7 bps gross (N100 2019) |

### Constraint gates (diagnostic path)

| # | Gate | Result |
|---|------|--------|
| 1 Latency | **PASS** | Analysis of owned events; champion instant unchanged |
| 2 Access | **PASS** | No new execution path |
| 3 Session | **PASS** | Champion structure |
| 4 Data | **PASS** ($0) | Owned NOII + free 13F/N-PORT + self-archived/Wayback holdings; quarterly ownership granularity accepted a-priori; iShares/QQQ paths verify at build |
| 5 Fill realism | **PASS** | No new fills |
| 6 Statistics | **PASS with null-prior flag** | n≫250/tercile achievable; expected slope weak-to-null (D) — powered as a kill test |
| 7 Protocol | **PASS** | Named payer; a-priori PassiveForce; charges the joint M12 name-selectivity family (shared with DR-X1 variable) |

**Survivor-profile score: 4/5 as diagnostic** (effect ≥2× cost unknown and not the point — mechanism resolution is).

### Economics sketch (bps per event)

Champion = +2.5 dev / +12.5 holdout (MU-carried). Field priors: large-cap unconditional |dev| ~2.7 bps mostly inside spread; offsetter premium ~1.7 gross. This lane proposes NO new mean — it prices the name-selection decision: if high-PassiveForce (or high-LETF-F) tercile ≥ +2 bps while bottom ≤0 with controls, the forward book has a mechanism; if flat, name-focus is luck.

### Proposed next test (user decides) — fold into joint "M12 name-selectivity mechanism" family

**Variables (lock construction before economics):** (i) PassiveForce_i,t = z(passive share proxy from 13F/N-PORT quarterly) + z(log index-weight proxy from archived QQQ/SPY holdings); (ii) LETF-F/ADV from DR-X1. Controls: log ADV, spread, vol20. Strata: rebal/OpEx flags separate (DR-Q12 flags).
**A-priori:** monotone tercile separation in dir and net on the 33-name panel (pooled 2023-26 for the 28, 2020-26 for core 5); GOOGL clause from DR-X1 applies to both variables; leave-one-name-out stability; no promotion from backtest — winner variable (if any) becomes the M10 forward-book filter.
**Kill:** neither variable separates; or separation driven by ≤2 names; or ownership-proxy coverage <70% of panel.
**Cost:** $0 data; ~1-2 days build (holdings archive assembly is the long pole).

### Ledger-note suggestion (user only)

> `DR-Q1-3 2026-07-17: payer identity CONFIRMED (passive/index MOC, feed censored ~23% internalization + ~30% echo prints); ownership->basis scaling has null field prior (B&M absorption) but is $0-testable; register JOINT M12 name-selectivity family = PassiveForce + LETF-F/ADV horse race (one family charge); ITG post-print null weakened on full-text read (window ends 16:00; 0.5-spread predictable move into print).`

### Sources / modality files

`modality-A.md` … `modality-D.md`; refuter reports summarized in Claims (3 completed agents, 2026-07-17; payer-scaling bundle single-refuter full-text confirmation — twin terminated by session limit, not re-run because its pair had already located and read the primary sources).
