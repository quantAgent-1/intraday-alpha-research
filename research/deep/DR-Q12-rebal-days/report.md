# DR-Q12 — Rebal / reconstitution / calendar forced-flow days

**Date:** 2026-07-17  
**Mode:** A deep-dive (OPEN_QUESTIONS #12 + unmapped calendar cells)  
**Agents:** 4 modality + 2 claim-refuters  
**Orchestrator synthesis**

### Synthesis

| Lane | Verdict rec | Core thrust |
|------|-------------|-------------|
| A | OPEN-TESTABLE (HIGH) | Forced MOC concentration on recon/ME days is real; basis amplification unmeasured |
| B | OPEN-TESTABLE (HIGH) | Exact calendars + cutoffs **unchanged** on rebal days; free event flags |
| C | OPEN-TESTABLE (MED) | Volume 2–6×; multi-day index effect dead; close micro still open |
| D | NOT-VIABLE-STRUCTURAL (MED–HIGH) | Pure rebal stratum UNDERPOWERED; mega-name share-change impact ~0.15 bps/2% |

**Dissents:** D correctly kills **promotion of a rebal-only edge** under Gate 6. A/B/C correctly keep a **$0 calendar-conditioning diagnostic** of the champion. Multi-day add/delete harvest = EXHAUSTED-BY-FIELD (Greenwood–Sammon) — out of scope for this charge if framed as close-basis overlay.

### Verdict (orchestrator)

**`OPEN-TESTABLE`** (confidence **HIGH**) as a **calendar-conditioning / diagnostic stratum** of the existing champion on owned NOII — **$0**, pre-registered event flags, **UNDERPOWERED-BY-DESIGN** for pure rebal-only Stage A promotion.

**Not** a freestanding Stage A family with n≥250 on rebal days alone.  
**Not** multi-day index-effect revival (field-exhausted).

What would flip pure-rebal promotion: Pre-reg pooling that still yields n≥250 **without** diluting the calendar definition (e.g. multi-year × many names with actual rebal flow) **and** special-day mean ≥ non-special by a pre-reg margin.

### Mechanism

Index trackers/ETFs forced to match effective-date closes (tracking error). Auction volume multiplies; whether **15:55:10 near−mid basis** and champion **payoff** amplify on mega-liquid Nasdaq holds is the open empirical question. Depth spikes can absorb flow → possible **null amplification** even when volume is extreme.

### Claims (post-refute)

| ID | Status | Claim |
|----|--------|-------|
| C1 | **CONFIRMED** (T1, refuter) | S&P U.S. quarterly rebal effective after close third Friday Mar/Jun/Sep/Dec |
| C2 | **CONFIRMED** (T1, refuter) | Nasdaq Closing Cross cutoffs **unchanged** on Russell recon day |
| C3 | **CONFIRMED** (T1, B) | NDX rebal MOC day = third Friday (effective next open) |
| C4 | **CONFIRMED** (T2/T3) | Auction volume massively elevated on recon/ME/expiry days |
| C5 | **CONFIRMED** (T2) | Multi-day S&P add AR decayed to ~0 in 2010s (Greenwood–Sammon) |
| C6 | **PLAUSIBLE** (T3) | Share-change mid→close impact ~0.15 bps per 2% shares (Dimensional) — bearish for mega-core amplification |
| C7 | **UNVERIFIED** | Champion basis mean/hit-rate higher on special days in our 5–28 names |

### Constraint gates (diagnostic stratum)

| # | Gate | Result |
|---|------|--------|
| 1–5 | **PASS** | Same as champion; calendars free |
| 6 Statistics | **PASS** as interaction on full sample / **FAIL** pure rebal-only | Flag UNDERPOWERED for rare cells |
| 7 Protocol | **PASS** diagnostic / **FAIL** if promoted as Stage A alone | Charges auction calendar sub-family |

**Survivor-profile (as champion overlay):** 5/5 mechanism fit.  
**As standalone rebal edge:** 2–3/5 (power + mega-name payer doubt).

### Economics sketch

Literature objects ≠ champion P&L units. Volume/imbalance spikes are confirmed; **extra bps for our megacaps** is unknown and may be zero. Cost = champion structure. Comparison: champion +2.5 / +12.5 holdout.

### Proposed next test ($0 diagnostic)

**Event flags (MOC session) — lock before run:**

| Flag | Definition |
|------|------------|
| SPX_REBAL / NDX_REBAL / QUAD_WITCH | 3rd Friday Mar/Jun/Sep/Dec (prior RTH if holiday) |
| RUSSELL_RECON | FTSE effective-close Friday (2026: Jun 26, Dec 11; hist ≈ 4th Fri June) |
| MONTH_END | last RTH day of calendar month |
| COMPOSITE_INDEX_EVENT | SPX∨NDX∨RUSSELL |

**Hypothesis:** On COMPOSITE_INDEX_EVENT ∪ MONTH_END, |basis| distribution and/or signed basis→cross mean differ from ordinary days for |basis|≥10 events.  
**Data:** owned NOII 2020–2026; $0.  
**Power:** report strata; do **not** promote on rare-day subset alone.  
**Kill narrative:** special mean ≤ ordinary; or all lift is one name/session.  
**Family:** auction calendar diagnostic — **no new freestanding family charge for promotion**.

### Unmapped cells status

| Cell | After DR-Q12 |
|------|----------------|
| Quad-witching closes | **OPEN-TESTABLE** (calendar flag; often = SPX/NDX rebal) |
| Month/quarter-end | **OPEN-TESTABLE** (better n than pure recon) |
| Half-day 13:00 | still **UNMAPPED** (not researched this pass) |
| Index ADD/DELETE → effective close | **OPEN-TESTABLE** diagnostic; multi-day alpha EXHAUSTED-BY-FIELD |
| IPO opens | still **UNMAPPED** |

### Ledger-note suggestion

> `DR-Q12 2026-07-17: OPEN-TESTABLE $0 calendar diagnostic of champion; pure rebal Stage A UNDERPOWERED; multi-day index effect stays dead; cutoffs unchanged on recon day (T1).`
