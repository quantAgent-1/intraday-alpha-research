# DR-Q4-6 — Retail MOC/LOC execution reality

**Date:** 2026-07-17  
**Mode:** A deep-dive (OPEN_QUESTIONS #4, #5, #6)  
**Agents:** 4 modality (A academic, B primary/venue, C practitioner, D adversarial) + 4 claim-refuters  
**Orchestrator synthesis — not delegated**

### Synthesis

| Lane | Verdict rec | Core thrust |
|------|-------------|-------------|
| A | OPEN-TESTABLE (MED) | Self-impact at $1k–$10k ≪ 1 bp on liquid names; entry half-spread is the cost |
| B | OPEN-TESTABLE (HIGH mech) | Exchange MOC=15:55 / LOC=15:58; brokers close earlier; post-signal MOC impossible |
| C | OPEN-TESTABLE (MED) | Capacity fine; Alpaca paper auction untrustworthy; prefer IBKR for late LOC |
| D | NOT-VIABLE-STRUCTURAL (HIGH) | Retail cannot capture via MOC on near-signal; continuous path toxic |

**Dissents:** D collapses “cannot MOC after near exists” into “cannot capture champion at all.” B/C correctly separate **three paths**: (1) continuous taker @15:55:10 → cross exit (champion), (2) late LOC @15:55–15:58 (exchange-legal, broker-gated), (3) pre-cutoff MOC (cannot use near price). A’s capacity story is uncontested. C’s “LOC-at-near as exit” is slightly misframed (exit is the cross; LOC is an *entry* path).

### Verdict (orchestrator)

**Split verdict (do not flatten):**

1. **Champion continuous-entry path:** `OPEN-TESTABLE` (confidence **MED–HIGH**)  
   Continuous marketable at 15:55:10 + exit at official cross remains the only universally retail-available expression of the 15:55:10 near basis. Capacity/self-impact at deploy size is not binding. Binding open work = honest **live fill-cost log** (not paper CLS).

2. **Post-signal MOC entry:** `NOT-VIABLE-STRUCTURAL` (confidence **HIGH**)  
   Near exists only ~15:55; exchange MOC ends 15:55; Alpaca CLS rejects after 15:50; Schwab MOC/LOC gone after 15:45; Fidelity on-close before 15:40 and help text denies Nasdaq on-close. Signal-timed MOC is impossible under §1.

3. **Late LOC (15:55:10–15:57:30) on IBKR:** `OPEN-TESTABLE` (confidence **MED**)  
   Exchange allows late LOC to 15:58 (reprice caps). Only IBKR among checked brokers plausibly reaches that window. Ops/paper ticket test required.

What would flip it: Live log on production broker showing continuous entry cost systematically ≥ half the holdout mean, **or** IBKR late-LOC accept+fill rates failing a priori thresholds.

### Mechanism

Payer remains indexed/ETF/rebal **MOC flow** at the listing-venue close (price-insensitive). Retail does not need to *be* the MOC order to harvest residual near−mid basis: continuous interest can fill continuous and/or participate in the cross; exit at NOCP is single-print. What fails is using **retail on-close order types after the near price exists** on Alpaca/Schwab/Fidelity.

### Claims (load-bearing, post-refute)

| ID | Status | Claim |
|----|--------|-------|
| C1 | **CONFIRMED** (T1, refuter + PDF) | Nasdaq: cancel/mod freeze 15:50; MOC stop 15:55; LOC stop 15:58; near/far in full NOII from ~15:55 |
| C2 | **CONFIRMED** (T1, refuter + docs) | Alpaca `cls` rejected after 15:50 ET until 19:00 |
| C3 | **CONFIRMED** (T1, refuter) | Schwab TOS: MOC/LOC before 15:45 only |
| C4 | **CONFIRMED** (T1, refuter) | Fidelity: on-close before 15:40, min 100 sh, help text “Nasdaq does not accept on the close orders” |
| C5 | **CONFIRMED** (T1, B) | IBKR publishes exchange cutoffs (MOC 15:55 / LOC 15:58 Nasdaq); no earlier internal cutoff found in T1 |
| C6 | **CONFIRMED** (T2, A) | Closing-auction self-impact scales √(%ADV); at $10k on multi-B ADV names expected self-impact ≪ 1 bp |
| C7 | **PLAUSIBLE** (T2/T3) | Continuous 15:55 entry cost dominated by half-spread + last-minute adverse selection; sim BBO+0.5bp is order-of-magnitude OK for liquid names but needs live calibration |
| C8 | **CONFIRMED** (structural) | MOC cannot express 15:55:10 near-basis signal |

### Constraint gates (champion continuous path)

| # | Gate | Result |
|---|------|--------|
| 1 Latency | **PASS** | Scheduled 15:55:10; 5–25 s pre-positionable for continuous entry |
| 2 Access | **PASS** continuous / **FAIL** post-signal MOC on Alpaca–Schwab–Fidelity | Continuous market always; on-close broker-gated |
| 3 Session | **PASS** | Flat at 16:00 cross in-mission |
| 4 Data | **PASS** / **OPEN-BLOCKED** for RT NOII | Hist owned; live NOII ~$199/mo not purchased (M10 paper may use delayed) |
| 5 Fill realism | **PASS** exit / **stress** entry | Auction exit single print; entry continuous needs condition-coded cost log |
| 6 Statistics | **N-A** (execution charge) | Not a new signal family |
| 7 Protocol | **PASS** | Execution SOP / cost annotation of champion; not new alpha family |

**Survivor-profile (continuous champion):** 5/5 structure preserved.  
**Survivor-profile (post-signal MOC):** 1–2/5 — structural fail.

### Economics sketch (units: bps **per event**)

| Component | Estimate | Source |
|-----------|----------|--------|
| Champion gross | +2.5 dev / +12.5 holdout | project |
| Entry continuous | ~ half-spread + AS (sim: BBO cross + 0.5) | sim / A+C |
| Exit self-impact @ $10k | ~0–0.2 | Goyal et al. square-root |
| Exchange auction fee | ≤~0.7 if fully passed | T1 fee list |
| Net prior @ retail size | Holdout still positive if entry cost ≤ ~5–6 | synthesis |

### Proposed next tests (user decides registration)

**T1 — Continuous cost realism (NOW, $0 data)**  
Hypothesis: On |basis|≥10 events, realized continuous entry shortfall vs 15:55:10 mid ≤ half-spread + 1 bp median.  
Data: owned SIP + forward paper/live tickets.  
Kill: median entry ≥ 5 bps or p90 ≥ 10 bps on liquid names.  
Family: M10 / champion execution annotation — **no new alpha family**.

**T2 — IBKR late LOC (optional ops)**  
Hypothesis: LOC submitted 15:55:10–15:57 with limit near±buffer fills at NOCP ≥80% on liquid Nasdaq names.  
Kill: accept rate <95% or fill <50%.  
Family: execution path only.

**Do not register:** “Switch entry to MOC after 15:55:10” — structural corpse.

### Unit table

| Quantity | Unit | Value |
|----------|------|-------|
| Holdout edge | bps/event | +12.5 [6.9, 18.5] |
| Dev edge | bps/event | +2.5 |
| Self-impact bound $10k | bps/event | ≪1 |
| Alpaca CLS hard gate | clock | 15:50 ET |
| Exchange MOC hard gate | clock | 15:55 ET |

### Ledger-note suggestion (user only)

> `DR-Q4-6 2026-07-17: post-signal MOC NOT-VIABLE-STRUCTURAL on Alpaca/Schwab/Fidelity; continuous entry remains OPEN-TESTABLE; IBKR late-LOC ops test optional; capacity non-binding at $10k.`

### Sources / modality files

See `modality-A.md` … `modality-D.md` in this directory. Refuters confirmed C1–C4 primary claims (refuted=false).
