# M28 `open_cross_battery_v1` — RESULT: NULL-AT-ADMISSION

2026-07-27. Registration: `REGISTRATION.md` (frozen pre-data, ledgered before any economics).
Amendments: `AMENDMENT_1_COST.md` (cost estimator failed, outcome-blind), `AMENDMENT_2_NAN.md`
(NaN defect voided the first train run). Diagnostics: `diagnostics.md`. Verification:
`m28_verify.py`, 32/32.

---

## The verdict

**NULL-AT-ADMISSION.** Zero of the 14 pre-declared signals cleared Benjamini–Hochberg FDR at
q = 0.10 on the train period. Per the registration, no composite was formed and **the validate
period was never read** — it remains a clean, unconsumed 250-session out-of-sample window.

| | |
|---|---|
| panel | 176 names × 604 sessions = **100,271 name-days** (universe: top 200 by 2023 dollar volume, less ETFs) |
| train | 2024-01-02 … 2025-05-30, 58,259 name-days, 354 sessions |
| smallest p-value | **0.158** (`dvol_z`) against an FDR threshold of **0.0071** |
| largest \|IC\| | **0.0138** (`pm_range`) |
| median per-signal IC standard error | **0.0103** → detectable IC at t=2 is **0.0207** |

This misses by more than an order of magnitude. It is not a near-miss, and no amount of
additional data at this design would rescue it.

## Why this null is worth more than the 22 kills before it

Every prior family in this program died at t ≈ 1.5 on a few hundred to a few thousand events,
leaving the honest question — *was the effect absent, or was the test too weak?* — unanswered.
This one answers it:

- **The effects are not merely insignificant; they are too small to trade.** A dollar-neutral
  decile book at this breadth needs a daily cross-sectional IC of roughly 0.02–0.03 to clear a
  3 bps round-trip. Every one of the 14 candidates sits at or below **0.0138**. Even taking
  each point estimate at face value and ignoring significance entirely, none of them pays.
- **Breadth was not the binding constraint.** Mean pairwise ρ across the 14 candidate streams
  is **+0.040**, giving an effective breadth of **N_eff = 9.21 of 14**. The program's standing
  doctrine — that streams at ρ 0.83–0.98 collapse to effective breadth ~1 — does not apply
  here. The battery is close to genuinely independent. It simply contains nothing that predicts.
- **It closes the bar-tier reopening condition directly.** The documented condition for
  reopening bar-tier forecasting (`EXHAUSTION_MAP.md`) is *residual IC ≥ 0.15 AND N_eff ≥ 8 AND
  net ≥ 2× cost*. The breadth leg is now **met** (9.21). The IC leg is missed by a factor of
  **~11** (0.0138 vs 0.15). That cell was previously closed by inference from a 16-name study;
  it is now closed by direct measurement on a 176-name panel.

## What was actually tested

Fourteen signals, all computable strictly before the 09:28 ET market-on-open cutoff, all
sourced from `bars1m` alone: nine from completed prior sessions (`ret1`, `ret5`, `ret21`,
`clv`, `dvol_z`, `rvol21`, `ret1_x_dvol`, `on_prev`, `id_minus_on`) and five from the current
session's pre-market 04:00–09:28 window (`pm_ret`, `pm_vol_z`, `pm_range`, `pm_late`,
`pm_accel`). Outcome: opening-cross print → last minute-bar close in 15:40–15:45.

Full per-signal table with CIs and FDR thresholds in `diagnostics.md`.

## What survives from the design (and is reusable)

The *structure* was never the problem and remains the most valuable artefact of the last two
days:

- **Entry at the opening cross costs zero spread**; the 15:40–15:45 exit is the day's cheapest
  minute. All-in cost for this shape is ~1–3 bps against the 16–38 bps that killed M27.
- **A 176-name × 604-session bar panel is free** and rebuilds in 5 seconds from a 1.2 GB
  minute-bar lake that now exists on disk (200 symbols, 2023-10 … 2026-05).
- **The harness is generic.** `m28_panel` / `m28_run` / `m28_diagnostics` / `m28_verify` take a
  signal list and a frozen combination rule; swapping the 14 formulas is a new registration,
  not a rebuild.
- **The live instrument is built and correctly dark** (`m28_live.py`): it hard-refuses every
  real-data path because the verdict is not PASS. Selftest 6/6, including the refusal.

## Two defects found and fixed en route

Both were caught by an **impossibility in the output**, not by any statistical threshold:

1. **Cost estimator anti-informative** (`AMENDMENT_1_COST.md`). The bars-only half-spread
   proxy correlated **−0.515** (log-log) with the ten measured `bbo1s` half-spreads — it
   tracked volatility, not spread, ranking NVDA (true 0.70 bps) as more expensive than KLAC
   (true 3.60). Replaced, outcome-blind, by the pre-declared flat 3.0 bps stress, which makes
   the 2× promotion test strictly harder.
2. **NaN masquerading as data** (`AMENDMENT_2_NAN.md`). polars propagates NaN through
   `mean`/`std`/`quantile`, so one name with no pre-market prints poisoned an entire session's
   z-scores; and `drop_nulls()` does not remove NaN, so the poisoned rows were *ranked* rather
   than excluded. The five pre-market signals returned **byte-identical ICs** — five different
   formulas cannot do that, and that impossibility is what exposed it. `z_pm_*` had 47 finite
   values out of 100,271; after the fix, ~65,500. A hard tripwire (`assert_no_nan_z`) now makes
   the failure impossible to repeat silently.

**Standing lesson, now twice-earned:** a result that *cannot be true* is worth more than a
result that merely looks good, and it must never be explained away. Both bugs would have
produced a confident, publishable-looking number.

## Program consequences

- The **bar-signal axis at the open-cross structure is priced** — not "underpowered, unknown".
  A new family in this space needs a genuinely different information set, not a new estimator
  or a wider panel.
- The **validate period is preserved**. 2025-06-02 … 2026-05-29 has never been read by any
  M28 code and is available as a clean out-of-sample window for the next family.
- The **sealed holdout (≥ 2026-06-01) was never fetched.**
- No trading decision, no adoption, no forward clock. One look spent, family closed.
