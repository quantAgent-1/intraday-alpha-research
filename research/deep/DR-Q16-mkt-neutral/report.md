# DR-Q16 — Market-neutral closing basket / variance cut

**Date:** 2026-07-17  
**Mode:** A deep-dive (OPEN_QUESTIONS #16)  
**Agents:** 4 modality  
**Orchestrator synthesis**

### Synthesis

| Lane | Verdict rec | Core thrust |
|------|-------------|-------------|
| A | OPEN-TESTABLE (MED) | Common close factor real; same-session residualization unmeasured in lit |
| B | OPEN-TESTABLE (HIGH access) | Multi-name + short QQQ MOC legal; Alpaca CLS≤15:50; locate required |
| C | OPEN-TESTABLE (MED) | Practitioners β-hedge residual books; no published retail σ-cut numbers |
| D | NOT-VIABLE-STRUCTURAL (HIGH) | Dual cost + idio residual + $1k capital kill **live dual-leg deploy** |

**Dissents:** D correctly kills **live dual-leg deploy at $1k**. A/C correctly keep **offline residualization** of champion PnL as a free method test. B confirms access exists for a $10k research-gate dual-leg if ever warranted.

### Verdict (orchestrator)

**Split:**

1. **Offline residualization (research transform):** `OPEN-TESTABLE` (confidence **MED–HIGH**) — $0 on owned NOII+SIP+QQQ/SMH. Method sub-family, not new alpha.

2. **Live multi-leg market-neutral book at $1k:** `NOT-VIABLE-STRUCTURAL` (confidence **HIGH**) — capital split, whole-share quantization, dual continuous entry after MOC cutoff, manual legging, double cost stack vs ~+2.5 mean.

3. **Live dual-leg at $10k gate:** `OPEN-TESTABLE` only **if** residualization shows R² and residual mean clear a-priori bars **and** dual costs ≤ residual mean; otherwise leave dead.

What would flip live dual-leg: Residual sd ≤ ~0.7× raw **and** two-leg cost add ≤ +0.8 bps/event on owned history.

### Mechanism

Champion mean payer unchanged (indexed MOC). Hedge is **risk control**, not a payer. Close window has a common institutional/passive factor (Cushing–Madhavan portfolio variance share; cross-sectional correlation of auction deviations). Beta hedge removes only the common slice; stock-specific auction residual (~our ~20 bps noise driver) largely remains.

### Claims

| ID | Status | Claim |
|----|--------|-------|
| C1 | **CONFIRMED** (T2) | Last minutes / auction deviations share common component |
| C2 | **CONFIRMED** (T1) | Short MOC permitted subject to Reg SHO locate; multi-security MOC not banned |
| C3 | **CONFIRMED** (T1) | Alpaca CLS after 15:50 rejected — dual MOC must be staged earlier or continuous |
| C4 | **PLAUSIBLE** | Daily market-model R² often ≪0.5; auction residual more idio → modest σ cut |
| C5 | **CONFIRMED** (structural) | Dual continuous entry after 15:55 doubles cost stack vs single-name champion |

### Constraint gates

| Path | 1 Lat | 2 Acc | 3 Ses | 4 Data | 5 Fill | 6 Stat | 7 Prot |
|------|-------|-------|-------|--------|--------|--------|--------|
| Offline residualize | PASS | PASS | PASS | PASS | N-A | PASS | PASS |
| Live dual $1k | **FAIL** | **FAIL** | PASS | PASS | **FAIL** | PASS | **FAIL** |
| Live dual $10k | stress | cond. | PASS | PASS | stress | PASS | cond. |

**Survivor-profile live dual $1k:** 2/5.  
**Offline residualize:** 3–4/5 as method.

### Economics sketch (bps **per event**)

| Item | Sketch |
|------|--------|
| Champion mean | +2.5 dev / +12.5 holdout |
| Noise | ~20 sd |
| After beta hedge (OM) | residual_sd ≈ 20√(1−R²) → often still mid-teens if R² 0.25–0.5 |
| Dual cost add | ~+1–2.5 vs single leg |
| Net prior live dual | ≈ 0 to worse than champion on residual Sharpe × capital |

### Proposed next test

**Offline only (NOW, $0):**  
Regress champion event net_bps on simultaneous 15:55:10→16:00 QQQ/SMH returns (and optional sector).  
**A-priori:** R² ≥ 0.20 and residual mean ≥ +2.0 to adopt residual as **reporting transform** for M10/M11.  
**Kill:** R² < 0.10 or residual mean < +1.  
**No promotion to live dual-leg** without separate cost study.  
**Family:** method/Q16 — does not open new mechanism family.

### Ledger-note suggestion

> `DR-Q16 2026-07-17: offline residualization OPEN-TESTABLE $0; live dual-leg at $1k NOT-VIABLE-STRUCTURAL; dual-leg $10k deferred pending R² result.`
