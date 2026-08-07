# M28 `open_cross_battery_v1` — system design + PRE-REGISTRATION

Written 2026-07-26, **before any signal, return or portfolio statistic was computed on the
wide panel.** The minute-bar pull was already running when this was written; raw bytes on
disk contaminate nothing, and no derived quantity existed yet.

Supersedes nothing. Charges one new family. The sealed holdout (≥ 2026-06-01) is untouched.

---

## 1. Why this family exists (the argument, in one paragraph)

Twenty-two families have each spent one underpowered look on one signal and been closed at
t ≈ 1.5. The program's own doctrine says breadth is the binding constraint and that a
combination layer *multiplies* edge but cannot create it (M18). Two facts measured on
2026-07-26 change what is buildable: (a) **entry at the opening cross costs zero spread**
and the 15:40–15:45 exit is the cheapest continuous moment of the day, so the all-in floor
for this structure is ~0.5–2 bps instead of the 16–38 bps that killed M27; (b) **bar-derived
signals are free across hundreds of names**, while tape-derived ones are quote-limited to 10
(R2-A Stage 3, METHOD-BLOCKED). Together they permit, for the first time in this project, a
design whose standard error is ~1 bps rather than ~8 — i.e. one where **a null is a real
null**. This family is that design: one pre-registered battery of candidate signals, one
frozen combination rule, one out-of-sample test, with the multiple-testing correction
declared in advance rather than left to a later Q17 reckoning.

**Stated before the data speaks:** the modal outcome is that no signal survives FDR on
train, or that the composite is flat on validate. That is an acceptable and valuable result
— it is the first *adequately powered* null this program will have produced on the
continuous-intraday direction, and it prices the whole bar-signal axis at once instead of
one family at a time.

## 2. Execution structure — FROZEN

| element | specification |
|---|---|
| decision instant | **09:28:00 ET** — every input must be knowable strictly before this |
| entry | market-on-open, filled at the official opening cross print. **0 spread** (single print). SEC fee applies to a short-sale entry only |
| exit | taker at **15:40–15:45 ET** — last minute-bar close in the window; cost = half-spread + SEC fee on the sale leg |
| holding | one RTH session, flat by 15:45. **No overnight, no close auction, nothing after 15:45** |
| position | dollar-neutral cross-section, gross fixed at 1.0 (0.5 long + 0.5 short) |
| latency | none required — the order is keyed any time before 09:28. This is the K4 exception class (a pre-positioned single print) |

Mission compliance: RTH-only, flat before the 15:50 curfew, signal-only (no routing code),
close-auction direction untouched.

## 3. Data — ONE lake, by design

**Everything is derived from `data/raw/sip/bars1m`.** Daily aggregates (open, high, low,
close, volume, VWAP) are computed by aggregating minute bars, not by reading `bars1d`.

Rationale, and it is not stylistic: `bars1d` is RAW, `bars1m` is split/dividend-ADJUSTED and
`trades` is RAW. Mixing them produced three separate large spurious results on 2026-07-26
(−1248 bps; a constant OLI; |OLI| saturating at 1 on 32% of name-days). Sourcing every price
from a single lake makes that entire error class **structurally impossible** here. Within-day
and across-day ratios inside one adjusted lake are correct by construction.

Extended-hours bars are required (pre-market signals) and are present in this lake.

## 4. Universe — FROZEN, mechanical, outcome-blind

From `data/external/m17_daily_bars.parquet` (659 free symbols): keep symbols with ≥ 200
sessions in **calendar 2023** — strictly prior to the test window — rank by 2023 median daily
dollar volume, take the **top 200**. Of those, 15 index/sector ETFs and 1 duplicate share
class (GOOG, GOOGL retained) are excluded from the tradeable cross-section and retained as
factor/hedge references. **Tradeable universe = 184 names.** Frozen list:
`research/experiments/M28-open-cross-battery/universe.json`.

No return, signal or outcome data of any candidate was examined by the rule. Ranking on 2023
means the selection cannot see the test window.

Known and accepted bias: this is a large-cap liquid universe, so any effect that lives only
in small caps is out of scope, and results may not generalise below ~$249M median daily
dollar volume (the top-200 cutoff).

## 5. Train / validate split — FROZEN

| period | sessions | use |
|---|---|---|
| TRAIN | 2024-01-02 … 2025-05-30 | signal admission, sign determination — the **only** period any choice may look at |
| VALIDATE | 2025-06-02 … 2026-05-29 | the single test. Consumed once |
| HOLDOUT | ≥ 2026-06-01 | sealed, not fetched, not touched |

## 6. The signal battery — 14 candidates, FROZEN

All are computable at 09:28 from `bars1m`. Group A uses completed prior sessions; group B
uses the current session's pre-market (04:00–09:28).

**A. prior-session structure**

| # | name | definition |
|---|---|---|
| A1 | `ret1` | prior session open→close return |
| A2 | `ret5` | close→close over the prior 5 sessions |
| A3 | `ret21` | close→close over the prior 21 sessions |
| A4 | `clv` | close location in the prior session's range: (close−low)/(high−low) − 0.5 |
| A5 | `dvol_z` | prior-session dollar volume, z-scored against its own trailing 21-session mean/sd |
| A6 | `rvol21` | realised vol of the prior 21 daily close→close returns |
| A7 | `ret1_x_dvol` | `ret1 × dvol_z` — attention-weighted reversal |
| A8 | `on_prev` | prior session's overnight return (close_{t−2} → open_{t−1}) |
| A9 | `id_minus_on` | prior session intraday return minus its overnight return |

**B. current-session pre-market (04:00–09:28)**

| # | name | definition |
|---|---|---|
| B1 | `pm_ret` | last pre-market trade price ≤ 09:28 ÷ prior close − 1 |
| B2 | `pm_vol_z` | pre-market volume vs its trailing 21-session mean/sd for that name |
| B3 | `pm_range` | (pre-market high − low) ÷ prior close |
| B4 | `pm_late` | return over 08:58 → 09:28 |
| B5 | `pm_accel` | `pm_late − (pm_ret − pm_late)` — late vs early pre-market divergence |

**Name-day admission guards** (all pre-declared): the name must have ≥ 300 RTH minute bars
on session t; a valid opening bar at 09:30 and an exit bar in 15:40–15:45; ≥ 22 prior
sessions of history; and for group B, ≥ 5 pre-market bars with volume > 0 (name-days failing
only the B guard keep their A signals and are excluded from B signals, counted separately).

## 7. Signal → portfolio — FROZEN

1. **Cross-sectional standardisation.** Per session, each raw signal is winsorised at the
   1st/99th cross-sectional percentile and z-scored across the names available that session.
   This makes every signal dollar-neutral in construction and removes the market-factor
   exposure that Stage 1 showed dominates the variance.
2. **Sign.** Each signal's sign is set by the **sign of its TRAIN IC** and then frozen. No
   sign may be revisited on validate.
3. **Admission.** A signal is admitted iff its train IC is significant under
   **Benjamini–Hochberg FDR at q = 0.10 across all 14 candidates** (session-clustered
   bootstrap p-values, seed 7, 2000 reps). This is the multiple-testing correction, declared
   before any IC is computed. If **zero** signals are admitted, the family reports a null and
   the validate period is **not consumed**.
4. **Composite.** Equal-weight mean of the admitted, sign-corrected z-scores. Equal weight,
   not fitted weights: M9 (NULL) and M8-v2 (KILL) both say a learned combiner on this data
   hits a ceiling; a fitted weight vector is a second selection step this design does not pay
   for. A learned layer is earned only after the equal-weight version validates.
5. **Portfolio.** Long the top decile / short the bottom decile of the composite, equal
   weight within leg, **gross 1.0, net 0.0**, rebalanced daily, entered at the cross and
   exited 15:40–15:45.

## 8. Cost model — FROZEN

Entry at the cross costs **0 spread**. The exit crosses one half-spread. Explicit fees per
`COST_MODEL.md` v1: SEC §31 **0.206 bps** on the sale leg, FINRA TAF negligible at this size.

No quotes exist for 184 names, so the exit half-spread is estimated per name-day by a
**bar-based estimator calibrated against the 10 names where the 15:40–15:45 quoted spread is
measured** (`bbo1s`). The calibration is fitted on those 10 names only, its fit quality is
reported, and the primary statistic is additionally reported under a **flat 3.0 bps
half-spread stress** — roughly 2× the measured megacap value — so the conclusion's dependence
on the cost estimate is visible rather than assumed.

## 9. The primary statistic — ONE number

> **Mean daily NET return of the frozen composite portfolio over the VALIDATE period, in bps
> of gross exposure, with a session-clustered bootstrap 95% CI (seed 7, 2000 reps).**

Reported alongside it, per the adopted ADIA Lab No.19 standard: native-frequency Sharpe,
PSR, and MinTRL.

**PASS bar (both required):**
1. bootstrap **CI-lo > 0**, and
2. mean **gross ≥ 2 × mean daily cost** (the house 2× promotion rule).

**Outcomes, fixed now:**
- **PASS** — both conditions met. Licenses a forward-paper registration through the existing
  live engine. Not a trading decision.
- **BETWEEN** — CI spans 0. Family closed, look spent, no iteration, no re-tune.
- **FAIL** — CI-hi < 0, or gross < 2× cost. Family closed; the bar-signal axis at this
  structure is priced.
- **NULL-AT-ADMISSION** — no signal clears FDR on train. Validate is not consumed and the
  axis is priced at train only.

One look. No horizon menu, no threshold sweep, no universe subsetting, no re-tune. The
combination rule, decile cut, gross, and cost model are all fixed above.

## 10. Power, computed in advance

184 names × ~250 validate sessions ≈ 46,000 name-days; the portfolio statistic is a daily
series of ~250 observations. From the 2026-07-26 measurement, a dollar-neutral cross-sectional
daily series on a comparable panel has sd ≈ 85–95 bps per unit gross, so **se ≈ 90/√250 ≈ 5.7
bps/day**, and CI-lo > 0 needs ≈ **+11 bps/day**.

That is an honest and demanding bar: it is roughly a 1.0 daily-Sharpe strategy. **If the true
effect is 3–5 bps/day (a plausible, still-tradeable size), this design will not detect it**,
and the outcome will be BETWEEN rather than PASS. Recorded now so a BETWEEN is not later
misread as a refutation. The corresponding MinTRL is reported so the forward requirement is
explicit.

## 11. Mandatory diagnostics (always reported, never gating)

1. Per-signal IC, train and validate, with CIs — including for signals FDR rejected.
2. **ρ matrix** across admitted signal streams (the breadth doctrine's requirement) and the
   implied effective breadth.
3. Drift vs timing decomposition of the portfolio return (the check that mattered on SOXL).
4. **Placebo**: the identical pipeline with the composite replaced by a session-shuffled
   composite, 200 draws, seed 101. The real statistic must sit in the tail.
5. Cost sensitivity: primary statistic at estimated cost, at 2× estimated, and at the flat
   3.0 bps stress.
6. Turnover and the implied number of name-legs per day (manual-execution feasibility at the
   $10k research book and the $1k deploy lens).
7. Decile monotonicity across all ten composite deciles.
8. Per-year and per-quarter breakdown of the validate period.
9. Coverage funnel: name-days offered, dropped by guard, per signal group.

## 12. Fences — what this is NOT

- **Not bar-tier ML** (EXHAUSTED-BY-US, engineV5: 16 names, continuous taker entry, 30 m–4 h).
  No estimator is fitted at all here — signals are fixed formulas and weights are equal. What
  changed is the execution venue (zero-spread entry) and the panel width. The documented
  reopening bar for that cell is residual IC ≥ 0.15 / N_eff ≥ 8 / net ≥ 2× cost; §9 tests
  net ≥ 2× cost explicitly and §11 reports N_eff.
- **Not M27** (`gap_day_reversion_v1`, KILLED). M27 conditioned on the overnight gap and
  entered as a taker at 09:35. Here the gap is **unknowable** — a market-on-open order is
  submitted before the opening price exists — so the gap is not and cannot be an input.
- **Not the "pre-market EMPTY" round-1 note.** That note dismissed pre-market as duplicating
  gap information for a 09:35 taker entry. Under an open-cross entry the gap does not exist
  yet and pre-market is the only pre-cross information there is.
- **Not M24 / F3** (Q10, closed): those consumed NOII feed state. Nothing here reads NOII.
- **Not R2-A**: no tape, no trade signing, no quote dependence.
- **Not M7 / daily-swing** (EXHAUSTED): those hold overnight to multi-day. This is flat by
  15:45 every day.
- **Close-auction ban**: nothing in this family reads or trades the close.

## 13. Provenance

Universe + pull: `scripts/backfill_bars1m_wide.py`. Panel/signals/portfolio:
`scripts/m28_*.py` (written after this document). Cost calibration anchors: the measured
15:40–15:45 quoted spreads in `research/experiments/R2A-prong0/stage1.md`. Reporting
standard: ADIA Lab No.19, adopted program-wide 2026-07-23.
