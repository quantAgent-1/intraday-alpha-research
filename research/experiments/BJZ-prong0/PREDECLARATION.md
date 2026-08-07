# BJZ quote-free retail fade — prong-0 + OOS pre-declaration

Written 2026-07-27, **before any BJZ signal, return, or portfolio statistic was computed
on any panel.** The only computation that preceded this document is the Phase-0 existence
check (sub-penny share of off-exchange prints: MU 48.2%, KLAC 51.3%, NVDA 53.6%, TXN 47.5%;
classifiable buy+sell 23–37%), which reads no returns and can motivate nothing about effect
size or direction.

## 0. What this is

The R2-A candidate (prior-day retail flow → open-print fade) has one measured positive
expression — the **daily equal-weight portfolio** (+22.36 mid [+4.28, +40.36], net +20.78
[+2.71, +38.76], T=513; independently corroborated; beta-hedged +22.09; drift term 1.5%) —
and one honest objection: **the daily unit was chosen after seeing the event-level gate
fail, and confirmation on unseen names was METHOD-BLOCKED because quote-based trade signing
does not exist outside the 10 discovery names.**

Boehmer–Jones–Zhang (JF 2021) signing removes the quote dependence: off-exchange retail
executions carry sub-penny price improvement, and the sub-penny fraction signs the trade
(fraction in (0.6, 1.0)¢ → retail BUY; (0, 0.4)¢ → retail SELL; midpoint band and round
pennies unclassified). Known accuracy in the literature ~65–77% (with the Barber et al.
critique disclosed) — far above the tick rule's ~coin-flip on odd-lots, and computable from
the trade price alone.

**Role discipline, fixed now:**
- The 10-name discovery panel is **design-only, permanently**. Nothing computed on it —
  including a Phase-1 pass — is ever evidence the effect is real. Phase 1 validates the
  *method* (does quote-free signing carry the signal at all?).
- The decisive evidence is **Phase 3**: the frozen rule applied to **16 names no expression
  of this phenomenon has ever touched**, plus the forward clock after registration.

## 1. The frozen signal (both phases, byte-identical rule)

Per name, per session t:

- **Inputs**: session t−1 RTH (09:30–16:00 ET) trades with `exchange == 'D'`, **all sizes**
  (BJZ-standard; the odd-lot-restricted variant is reported as a non-gating diagnostic).
- **Signing**: frac = round((price × 100) mod 1, 4); BUY if 0.6 < frac < 1.0 (exclusive of
  1−1e−4 float guard), SELL if 1e−4 < frac ≤ 0.4; else unclassified.
- **Imbalance**: RIMB = (buy_vol − sell_vol) / (buy_vol + sell_vol) over classified prints.
  Require **≥ 30 classified prints**, else the name-day is dropped (counted).
- **Fire rule**: |RIMB| ≥ that name's own 75th percentile of |RIMB| over its full sample in
  the phase's panel (the R2-A gate-b convention, unchanged).
- **Position**: −sign(RIMB) at the day-t opening cross (fade the herd), exit 15:40–15:45.
- **Prices — ONE lake (bars1m), per the M28 rule**: entry = 09:30 minute-bar open (verified
  within ~0.5–2 bps of the official open, m28_verify T3); exit = last minute-bar close ≤
  15:45, require ≥ 15:40; early-close sessions dropped. Cap: sessions < 2026-06-01 only.
- **Cost (flat, conservative, Amendment-1 convention)**: 3.0 bps exit half-spread + 0.206
  bps SEC fee = **3.206 bps per fire**. Entry at the cross = 0 spread. Sensitivities at
  0.85 bps (measured megacap median) and 6.0 bps reported, non-gating.

**Primary statistic (both phases)**: mean of the **daily equal-weight portfolio** of that
session's fires, net of cost, session-bootstrap 95% CI (seed 7, 2,000 reps). The daily unit
is primary **from birth** this time — that is the point of a fresh registration.

## 2. Phase 1 — method validation on the discovery 10 (NOT confirmation)

Gates (all pre-declared):
- **G1**: daily-portfolio **net** CI-lo > 0.
- **G2**: daily-portfolio **gross ≥ 2 ×** mean daily cost.

Outcomes:
- **METHOD-VALIDATED** (G1 ∧ G2) → register the family and arm Phase 3.
- **METHOD-FAILED** (else) → the BJZ path is closed for this program. Fallback (pre-committed):
  probe Alpaca free-tier **historical quotes** feasibility with a one-day pull (the Stage-3
  "quotes unaffordable" assumption came from Databento pricing and was never tested against
  Alpaca); if ≤ ~2 min/name-day, pull quotes for ~8 mid-liquidity names (2025-01+) in
  background and run the ORIGINAL frozen quote-signed rule out of sample. If that is also
  infeasible, the honest state is: one in-sample daily-unit result, forward-only proof.

Supporting (non-gating): event-level mean/CI; corr(RIMB, quote-signed OLI) on matched
name-days; odd-lot-only variant; per-name signs; year table; fires/day.

## 3. Phase 3 — the decisive out-of-sample test (16 virgin names)

Universe (frozen 2026-07-26, outcome-blind, download-cost-ranked):
VRTX BKNG ISRG AMGN HON INTU TMUS GILD MDLZ COST PEP ADBE CMCSA SBUX CSCO QCOM — mostly
**non-tech**, deliberately the harder, broader test. Window 2024-01-02 … 2026-05-30.
No expression of this phenomenon has ever read these names' trades.

Same frozen rule, same primary statistic, same cost. Pre-committed outcomes (Stage-3
vocabulary, thresholds fixed now):
- **CONFIRMED** — daily net CI-lo > 0 AND gross ≥ 2× cost → forward clock starts; live
  instrument may arm per its own gate.
- **REFUTED** — daily net CI-hi < 0 → family closed, axis priced.
- **NOT-CONFIRMED** — CI spans 0 with point < +6.0 bps → failed replication; family closed.
- **PARK-UNDERPOWERED** — CI spans 0 with point ≥ +6.0 bps → no pass claim; the only
  permitted follow-up is widening (more names/years of trades), never re-analysis of these 16.

Power, computed in advance: ≈16 × 600 ≈ 9,600 name-days → ≈2,400 fires ≈ 4/session over
~600 sessions; expected daily se ≈ 5–8 bps ⇒ CI-lo > 0 needs roughly **+10–16 bps/day**.
If the true OOS effect is half of discovery (~+10), power is ~50% — hence the PARK outcome
exists. A null here is informative against effects ≥ ~15 bps/day.

Mandatory diagnostics (never gating): per-name signs (16), tier split (tech-adjacent QCOM/
ADBE/INTU vs rest), year split, drift-vs-timing decomposition with **intercept-preserving**
beta hedge (the OLS-residual-mean trap is documented in the graveyard-reprice addendum),
session-shuffled placebo (200 draws, seed 101), cost sensitivities, fires/day, funnel.

## 4. Registration plan (if Phase 1 validates)

Family `retail_fade_daily_v1`, registered in the ledger **before Phase 3 runs**: Phase 3 =
its single sanctioned historical look; PASS bar = the CONFIRMED outcome above; forward
clock = T+1 accrual on the full 26-name panel through the existing live-engine shell
(m28_live pattern: dark until its gate; daily book emitted before 09:28; reconcile T+1;
ADIA No.19 panel). Deploy-lens expressions (report-only): SOXL sector variant.

## 5. Honesty inventory — expressions of this phenomenon consumed so far

Quote-OLI event mean (pre-declared: FAIL) → daily unit (post-hoc: positive, tainted) →
BJZ signing (this document). That is three expressions of one underlying phenomenon; the
FDR debt is real and is why **only virgin-name and forward evidence counts**. Phase 1
cannot pass this family into existence on discovery data no matter what it shows.
