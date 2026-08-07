# M18 reversion_system_v1 — FINAL REPORT (2026-07-20)

**VERDICT: FAIL — obituary, family closed.** Registered bars B1 and B2 failed on the exact
registered design; per REGISTRATION.md, no re-tuning. Ledger: registered + adjudication +
addendum + result (lines 84–87).

## 1. What was tested

The combined system — frozen engineV2 OU-reversion trigger + G1 dislocation-quality gate +
G2 cost-state gate + pooled LightGBM meta-veto (τ=0.55, 17 monthly walk-forward folds,
first scored month 2025-01) + maker-first entries (touch fills, 60 s cancel) with taker
exits — on NVDA/TSLA/AMD/MU event_bars1s, dev ≤ 2026-05-31, holdout untouched. Verdict
unit = the system; bare-signal streams are attribution rows.

## 2. Verdict vs pre-registered bars

| bar | requirement | outcome |
|---|---|---|
| B1 | pooled system net > 0, day-clustered CI excludes 0, ≥300 trades | **FAIL** — pooled n=1,494, mean **−$3.46/trade**; a negative point estimate cannot clear a CI-above-zero bar at any width; n-requirement met, so the failure is powered |
| B2 | positive excluding top-5 sessions | **FAIL** (moot — mean already negative) |
| B3 | per-trade attribution decomposition | PASS (mid / spread / latency / fees on every stream) |
| B4 | meta veto adds value | directionally PASS, moot — improved 3 of 4 names (MU −6.46→−3.44, TSLA −5.63→−3.51, NVDA −1.43→−0.94; AMD −7.89→−8.11); veto rate ≈33% |
| B5 | real fill accounting; pessimistic re-pricings keep B1 sign | PASS — fill rates 90.0/98.2/96.6/92.9% (MU/NVDA/TSLA/AMD); through-fill and 50%-haircut re-pricings on the system streams keep the (negative) sign |

Fallback clause (B4-only fail → gates-only demotion): not applicable.

## 3. The loss-reduction ladder (the result worth keeping)

$/trade, 30m cells (2h/4h byte-identical — the hold axis is empirically inert: exits fire
at p50 ≈ 200 s, MAX_HOLD fired once in 6,625 anchor trades):

| stream | NVDA | TSLA | AMD | MU |
|---|---|---|---|---|
| raw taker (engineV2 expression) | −6.26 | −8.15 | −16.01 | −17.26 |
| raw maker | −2.95 | −2.54 | −4.64 | −6.45 |
| + G1/G2 gates | −1.43 | −5.63 | −7.89 | −6.46 |
| + pooled meta veto (SYSTEM) | **−0.94** | **−3.51** | **−8.11** | **−3.44** |

Every layer of the user's hypothesis does reduce losses (monotone on NVDA and MU; gates
anti-select on TSLA/AMD before meta recovers part of it). **No stream on any name crosses
zero.** The doctrine holds: execution and filters multiply an edge; they cannot create one
from a mid-neutral trigger.

## 4. Embers (facts, not actions)

- NVDA system stream: mid-alpha **+$2.19**, gross **+$1.79**, net −$0.94 — the loss is
  entirely the registered conservative fee model ($0.005/sh/side at ~141 shares). MU system
  stream mid-alpha +$2.15. Under literal zero-commission economics NVDA would be roughly
  breakeven-to-positive. This is a post-hoc, 1-of-4-names observation inside a 12-cell grid
  with ~160 inherited family trials — exactly the pocket noise manufactures. It is recorded
  for a possible future *ex-ante* registration and is NOT actionable under this one.

## 5. Caveats carried

- **Bar-cadence expression**: the anchor adjudication + forensic addendum (ledger 85–86)
  establish this verdict applies to the 1 s-bar expression of the frozen rule — a
  different-but-overlapping trade population vs the tick original (57%/19% entry-time
  match), with matched per-trade profiles. The bar cadence is the only one this desk could
  trade anyway (signal-only, human execution 5–25 s).
- **Spec-fidelity completion** applied before grading: pooled meta (was per-cell), real
  fill-rate accounting (was tautological 1.0), B5 re-pricings on system streams. Suite 470
  green; `--cell` ≡ `--all` byte-identical; zero holdout violations (max session
  2026-05-29).
- TSLA event_bars1s end 2026-05-22 (183 sessions) vs 2026-05-29 elsewhere — data-coverage
  tail gap, inside the dev window.

## 6. Assets left behind

Harness modules `src/enginev51/reversion/` (OU MLE, smooth-pasting solver, gate/feature
stack, maker/taker fill attribution, pooled walk-forward meta) + 33 tests — reusable for
any future intraday state-machine family. Cells + pooled fold models under this directory.
The engineV2 formula extraction (BUILD-SPEC Appendix A) documents three traps (share-unit
OFI gate ≈ no-op; sigma_5m is dollar VWAP-dispersion, not a returns std; failed threshold
solve must NaN-block) for any future port.

## 7. Portfolio-doctrine accounting

The family died before the adoption gate, so S_eff was never computed. The doctrine layer
this family pioneered — ρ-hypothesis at registration, realized P&L correlation in the
verdict, adoption bar S_new > ρ·S_book — remains adopted for all future families
(REGISTRATION.md §7; book baseline ρ 0.83–0.98, S_book 0.249/day).
