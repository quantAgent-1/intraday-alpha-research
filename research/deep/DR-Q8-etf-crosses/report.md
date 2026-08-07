# DR-Q8 — ETF closing crosses

**Date:** 2026-07-17  
**Mode:** A deep-dive (OPEN_QUESTIONS #8)  
**Agents:** 4 modality + 2 claim-refuters  
**Orchestrator synthesis**

### Synthesis

| Lane | Verdict rec | Core thrust |
|------|-------------|-------------|
| A | OPEN-TESTABLE (MED) | Lit does **not** support larger ETF basis edge; force is in underlyings |
| B | OPEN-TESTABLE (HIGH) | Nasdaq ETFs: same NOII/Closing Cross; portable mechanics |
| C | OPEN-TESTABLE (MED) | Residual prior modest; vendor MOC screeners conflicted |
| D | NOT-VIABLE-STRUCTURAL (MED–HIGH) | AP/MM collapse shell basis; thinner auction share |

**Dissents:** D over-kills portable **test** on QQQ (mechanics work; economics may be null). A/C agree prior is ≤ single-name, not ≥. B owns mechanics: portable for Nasdaq-listed ETFs only.

### Verdict (orchestrator)

**`OPEN-TESTABLE`** (confidence **MED**) for a **cheap null/kill test** of the champion rule on **Nasdaq-listed** liquid ETFs (QQQ, SMH, SOXX).  

**Prior:** effect size expected **≤ single-name**, not larger. Do not spend as if this is the highest-EV expansion; rank below Q4–6 cost log and Q12 diagnostic.

**`OPEN-BLOCKED(Arca imbalance data $ TBD; RT ~$1k/mo)`** for SPY/IWM/most Arca sector shells until a usage quote ≤$100 for historical imbalance is confirmed.

What would flip it: Pre-registered QQQ/SMH/SOXX |basis|≥10 events deliver net ≥ +2 bps/event at n≥250 with no concentration artifact — would reopen “ETF shell is a superior venue” (low prior).

### Mechanism

Forced MOC payer is strongest in **constituents** (tracking/NAV). On the **ETF share**, APs create/redeem and continuous secondary arb tighten mid vs iNAV; listing-venue auction share is lower (~2% Arca ETFs vs ~9% equities — T3). Residual near−mid on QQQ may still exist and is **testable** on the same NOII product as names, but the “most concentrated payer → largest edge” intuition is **mislocated** (payer concentrates in underlyings, not the shell).

### Claims (post-refute)

| ID | Status | Claim |
|----|--------|-------|
| C1 | **CONFIRMED** (T1, refuter) | Nasdaq-listed ETFs use same Closing Cross + NOII schedule as equities |
| C2 | **CONFIRMED** (T2, refuter) | Large ETFs mean \|auction−4pm mid\| ≈ 3.63 bps (Bogousslavsky–Muravyev 2010–18) |
| C3 | **CONFIRMED** (T3) | Arca ETF auction share ~2% ADV vs equities ~9% (BMLL 2025) |
| C4 | **PLAUSIBLE** (T3) | Brokers can MOC underlyings and package to ETF at NAV risk-free → less forced flow into ETF cross |
| C5 | **CONFIRMED** (T1) | Databento XNAS.ITCH imbalance schema applies to Nasdaq ETPs; near 0 until ~15:55 |

### Constraint gates (QQQ/SMH/SOXX path)

| # | Gate | Result |
|---|------|--------|
| 1 Latency | **PASS** | Same 15:55:10 |
| 2 Access | **PASS** | Retail continuous + on-close (broker caveats as Q4–6) |
| 3 Session | **PASS** | Flat at cross |
| 4 Data | **PASS** Nasdaq ETFs / **OPEN-BLOCKED** Arca | ~tens $/name-decade pattern |
| 5 Fill realism | **PASS** | Single-print exit |
| 6 Statistics | **PASS** | Daily liquid events |
| 7 Protocol | **PASS** | Named residual auction demand; charges auction-ETF family |

**Survivor-profile:** 4/5 (point 5 — effect ≥2× cost — unknown; prior leans weak).

### Economics sketch (bps **per event**)

| Object | Prior |
|--------|--------|
| Large-ETF \|close−mid\| (unfiltered) | ~3.6 mean abs (not tradable basis filter) |
| N100 imbalance-offset premium (2019) | ~1.7 gross (T3) |
| Champion single-name | +2.5 dev / +12.5 holdout |
| ETF shell net prior | **0 to modest positive**; **not** expected to beat names |

### Proposed next test

**Hypothesis (two-sided kill preferred):** Champion rule on QQQ+SMH+SOXX does **not** dominate single-name economics; fire rate and mean net ≥ +2 bps/event are secondary promotion bars.  
**Data:** Databento Nasdaq NOII + SIP; expect ≤~$100 for multi-year 3 symbols.  
**Universe:** QQQ, SMH, SOXX.  
**A-priori:** |basis|≥10 @15:55:10; WITH basis; exit NOCP.  
**Promotion:** only if net ≥ +2 and n≥250 and not concentration-driven **and** beats or matches name panel — else **kill ETF-superiority narrative**.  
**Family:** auction / M11-adjacent ETF cell.

### Ledger-note suggestion

> `DR-Q8 2026-07-17: OPEN-TESTABLE cheap null on Nasdaq ETFs; prior ≤ single-name; Arca shells blocked pending $ quote; do not prioritize over Q4-6 cost log.`
