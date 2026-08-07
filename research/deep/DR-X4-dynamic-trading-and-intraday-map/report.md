# DR-X4 — Cost-aware position book + decay-graded intraday map

**Synthesis date:** 2026-07-18  
**Agents:** 4 modalities + 2 refuter waves (6/6 claims unrefuted)  
**Protocol:** HARNESS Mode A

### Synthesis
| Lane | Verdict rec | Core yield |
|------|-------------|------------|
| A academic | OPEN-TESTABLE MED (method) / EXHAUSTED patterns | GP formulas + effects map with decay |
| B primary | OPEN-TESTABLE HIGH (mechanics bounds) | 15:50 freeze, LULD, short locate, TOD cost floor |
| C practitioner | OPEN-TESTABLE MED | Carver/NBIM/Robeco practice params |
| D adversarial | **NOT-VIABLE-STRUCTURAL HIGH** for hourly stat-arb / published-effects book | Breadth, crowding, manual lag |

**Orchestrator resolution (applied in order):**  
1. Pure pattern harvest (Gao first→last HH, HKS TOD mom, residual MR, published TOD alphas) → **EXHAUSTED-BY-FIELD** (Rosa OOS kill **CONFIRMED**; McLean–Pontiff-class decay; no honest retail min–hr T2 survivor).  
2. Hourly multi-name **stat-arb / bar-feature book** re-skinning dead IC class → **NOT-VIABLE-STRUCTURAL** under §1 (D + our own rank-IC 0.03–0.05 → plan α≈0).  
3. **GP-style inventory control as method** for a *named flow payer* (LETF F(t), calendar, auction residual) → **OPEN-TESTABLE** as M16 *expression layer*, not as a free anomaly book.  
4. Venue bounds from B are hard design constraints (not alpha).

## Verdict recommendation
**Split verdict:**

| Object | Verdict | Confidence |
|--------|---------|------------|
| Documented pure intraday pattern harvest as edge | **EXHAUSTED-BY-FIELD** (+ EXHAUSTED-BY-US where we already tested) | HIGH |
| Hourly 5–33 name residual/stat-arb inventory without new payer | **NOT-VIABLE-STRUCTURAL** | HIGH |
| GP partial-adjustment + no-trade band **method** on **named flow/calendar/auction** forecasts (M16 design) | **OPEN-TESTABLE** | MED |

**What would flip structural kill:** residual IC ≥ 0.15 hourly after factor residualization, N_eff ≥ 8, net ≥ 2× RT cost — simultaneously (D’s bar).  
**What would flip method OPEN:** Stage-A GP book on owned F(t)+calendar ≤0 net after honest costs on n≥250.

### Mechanism
GP is **portfolio control**, not a payer. With quadratic impact, trade partially toward an **aim** that overweights **slow** signals; proportional costs yield **no-trade bands**. At our size λ is half-spread+AS, not Kyle impact; manual 10–30 orders/day caps turnover. Viable only if aim is built from **price-insensitive flow** (LETF rebal, passive/calendar close), not from published half-hour momentum.

### Claims (post-refute)
C1 [CONFIRMED] (T2, GP JF 2013 / NBER 15205): \(x_t=(1-a/\lambda)x_{t-1}+(a/\lambda)\mathrm{aim}_t\); slow signals weighted more under cost.  
C2 [CONFIRMED] (T2): Quadratic → continuous partial trade; proportional → no-trade band (Constantinides/Davis–Norman).  
C3 [CONFIRMED] (T2, Gao et al. JFE 2018): First HH predicts last HH on SPY (IS).  
C4 [CONFIRMED] (T2, Rosa 2022): Post-pub OOS link **disappears** on ES → **DECAYED**.  
C5 [CONFIRMED] (T2, LPS JFE 2019): Overnight vs intraday clientele split; ON leg out-of-mission.  
C6 [CONFIRMED gap]: No T2 retail minutes–hours multi-name honest continuous book at $1–10k.  
C7 [CONFIRMED] (T1, B): Nasdaq on-close freeze 15:50; MOC 15:55; LOC 15:58; Alpaca CLS rejects after 15:50.  
C8 [PLAUSIBLE] Breadth: IC 0.03–0.05 × √N_eff(~1.5–2.5) → IR scale ≪ cost floor (project + Grinold).

### Decay-graded known-effects map
| Effect | Size (cited) | Cost model | Decay | M16 use |
|--------|--------------|------------|-------|---------|
| Gao first→last HH | ~2.6 bps/day gross hist | net ~1.8 post-2005 SPY | **DECAYED** (Rosa) | Do not feature |
| HKS lag-13 TOD mom | large hist | NO-COST-MODEL | **DECAY-LIKELY** | Do not feature |
| LPS overnight/intraday | ±%/mo alphas | costs kill | ON **out-of-mission** | Skip |
| TOD U/L vol/spread | structural | — | **ALIVE** microstructure | Cost/vol prior only |
| LETF last-30 flow | ≪1–low bps avg | contested net | **WEAKENED** as trade; OK as F(t) | Aim signal |
| Residual MR / pairs | hist SR decay | after-cost null post-2002 | **EXHAUSTED-BY-FIELD** | Dead |
| Bar-tier ML here | IC 0.03–0.05 | plan α≈0 | **EXHAUSTED-BY-US** | Dead |

### Design cheat-sheet (M16 starting params)
| Param | Start |
|-------|--------|
| Clock | Hourly 10:00…15:00; special 15:30/15:50 |
| θ = a/λ | **0.25** / hour (band 0.15–0.50) |
| φ_slow | ln2/6.5 (~1 session HL) |
| φ_fast | ln2/2 (~2 h HL) — **deweight** in aim |
| No-trade band (proportional approx) | skip if \|aim−x\| < 0.5–1.0 · σ_hour |
| Max orders | 30/day; whole shares; flat 15:50 or MOC staged **with** last continuous pass |
| Risk | target book hourly sd ~15 bps via γ |

### Constraint gates (method path / pattern path)
| Gate | Method (flow+GP) | Pattern book |
|------|------------------|--------------|
| 1 Latency | PASS if scheduled hourly/15:50 | FAIL residual MR |
| 2 Access | PASS | PASS |
| 3 Session | PASS if flat 15:50/MOC | PASS but kills Gao last-HH |
| 4 Data | PASS $0 | PASS |
| 5 Fill realism | PASS taker/auction | FAIL multi-fill inventory |
| 6 Statistics | PASS n plans | FAIL economics power |
| 7 Protocol | PASS if named payer | FAIL re-skin |

Survivor: method **3/5**; pattern **1/5**.

### Economics sketch
Field pure-pattern net prior ≈ **0**. Champion = **+2.5 / +12.5**. M16 only worth Stage A if gross from **named flow** clears ~2–6 bps RT per name touched after order-count drag.

### Proposed next test (user decides)
- **M16 Stage A (method only):** hourly GP on aim = slow LETF-F/calendar (+ optional residual deweighted); n∈{5,12}; flat 15:50/MOC; pre-register θ, φ, kill if net≤0 or only pure TOD works.  
- **Do not register** first→last HH / HKS / bar-ML reboots.  
- **Family:** M16 dynamic flow book (new). No ledger write this wave.

### Sources
modality-A/B/C/D.md; refute-1/2.md (GP NBER 15205, Gao JFE, Rosa 2022, LPS JFE, Nasdaq openclose FAQ).

---

## Addendum — wave-3 verification pass (2026-07-21, 4 Opus re-verify agents + 2 refuters)

All four modality files independently re-verified; 2026-07-18 verdicts STAND unchanged. Deltas:

1. **NEW effect adjudicated — End-of-Day Reversal (Baltussen/Da/Soebhag, SSRN 5039009, posted Dec 2024, sample 1993–2019).** Modality-A's claimed "+24 bps/day gross, close→15:30 sort" was **REFUTED 2/2** (`refute-3-eod-reversal-r1/r2.md`) — the number does not appear in the paper. Corrected, refuter-confirmed entry for the known-effects map:

   | Effect | Size (actual) | Cost model | Decay | M16 use |
   |--------|---------------|------------|-------|---------|
   | EOD reversal (prior-close→**15:00** sort, skip 15:00–15:30, trade 15:30–16:00) | quintile L/S **3.78 bps/day VW / 6.86 EW** gross; largest-quintile alpha **3.41 bps/day** (t=10.61); smallest-quintile 14.71 | **NO-COST-MODEL** (authors: "might not be exploitable … after transaction costs") | Sample ends **2019**; no replication/critique 2024–26 → **DECAY-UNKNOWN** | Marginal: megacap slice ~3.4 bps/day gross vs ~2–3 bps RT cost floor → **feature candidate at most**, never a standalone book. Do not register standalone. |

2. **Mechanics re-verified same-day (T1):** Alpaca CLS rejects after **15:50** (tighter than exchange 15:55 MOC door — a 15:55:10 signal cannot drive an Alpaca MOC); LULD Tier-1 bands double 15:35→close; pause in final 10 min → no continuous reopen. C7 stands.
3. **Caveat flagged:** the exact GP discrete trade-rate scalar `a` in the cheat-sheet is **UNVERIFIED** (paywalled PDFs would not extract) — pull Prop. 1 from the published JF 2013 paper before hard-coding θ = a/λ in any M16 registration.
4. Practitioner turnover control added (T3, FactSet/Carver): turnover ≈ L·(1−ρ)/(1+ρ); ~10%-of-position no-trade buffer; "costs ≤ 1/3 pre-cost Sharpe" speed limit — starting params for the M16 Stage-A sketch.
