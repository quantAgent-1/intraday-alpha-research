# M15 positioning — backtest reference & monitor calibration — RESULT 2026-07-18

> ## CORRECTION 2026-07-20 (supersede-in-place; approved by user 2026-07-20)
>
> **What was wrong.** Panel A below (dev, walk-forward OOS) built its meta/portfolio
> streams from the WRONG column. `scripts/m15_backtest_reference.py` loaded
> `M6-FINAL-basis/oos_predictions.parquet` and renamed its `pred` column — the M6-GBM
> **continuous bps regression** (range ~−3.3..+6.8) — to `p_win`, then gated at 0.55.
> That is a category error: it thresholds a bps forecast as if it were a probability.
> The honest classifier probabilities are the M8 meta model's walk-forward OOS `p_win`
> (`M8-meta-v1/oos_predictions.parquet`, the |basis|≥10 candidate set, real
> p_win ∈ [0.35, 0.75]). **Panel B (holdout) was never affected** — it always scored
> the real frozen model via `predict_pwin`; its figures stand.
>
> **Reproduced buggy vs corrected (Panel A only).** Convention key: *pooled* = pooled
> event-mean net_bps (the forward-reference convention, = `stress.clustered_mean_ci`);
> *day* = day-mean net_bps (equal weight per session). Classical is byte-identical
> (same |basis|≥10 events, same net_bps). CIs are day-clustered 95%.
>
> | Panel A stream | BUGGY pooled | BUGGY day | BUGGY n | CORRECTED pooled | CORRECTED day | CORRECTED n |
> |---|---|---|---|---|---|---|
> | classical | +2.21 [1.50, 2.93] | +2.04 | 4,735 | +2.21 [1.50, 2.93] | +2.04 | 4,735 |
> | meta (p_win≥0.55) | +3.08 [2.29, 3.87] | +2.83 | 3,956 | **+4.03 [3.11, 5.00]** | +3.65 | **2,844** |
> | portfolio (top-3) | +3.40 [2.57, 4.26] | +3.29 | 3,085 | **+4.06 [3.14, 5.02]** | +3.83 | **2,515** |
>
> (buggy over 1,094/1,096 sessions; corrected meta/portfolio over 1,049 sessions.)
>
> **Selection-effect story weakens.** On the honest gate the top-3 portfolio adds only
> +0.03 pooled / +0.18 day over the meta stream (buggy: +0.32 / +0.47). Once the REAL
> p_win gates the set it is already well-selected, so top-3-by-p_win has little left to
> add; the §1 "M8's ranking is informative within the gated set" reading is far weaker
> than the mislabeled run implied, though the direction (portfolio ≥ meta) survives.
>
> **Code changed.**
> - `scripts/m15_backtest_reference.py`: Panel A now loads
>   `M8-meta-v1/oos_predictions.parquet` and gates its real `p_win` (dropped the
>   `pred`→`p_win` rename). Panel B untouched.
> - `src/enginev51/apps/forward_paper.py`: `REF_PORTFOLIO_BPS` +3.4 → **+4.1**
>   (corrected portfolio pooled event-mean, rounded 1 dp; pooled-event-mean convention,
>   matching `REF_META_BPS=+4.0`). DISPLAY-ONLY constant — it feeds neither the M10 gate
>   nor the CUSUM monitor (own frozen k=1.25/h=150); the status line is annotated
>   `superseded +3.4 mislabeled gate`. No gate/CUSUM logic changed.
>
> The §1 table and REF line below are the ORIGINAL (buggy) figures, kept per
> supersede-in-place house style — read them through this correction.

Registered before running (`M15-backtest-reference-v1`). Honest p_win throughout:
Panel A = M8 walk-forward OOS predictions (M6-FINAL `oos_predictions.parquet`, n=5,467,
2022-01→2026-05); Panel B = the frozen forward model (trained <2026-06-01) scored on the
sealed-holdout events — post-seal OOS by construction, the exact forward-harness procedure.
Frozen v1 policy applied verbatim (`positioning.apply_positioning`).

## 1. Selection-effect check — PASS on both panels (registered kill bar: meta − 2 bps)

| Stream | Panel A (2022-26 OOS) | Panel B (holdout) |
|---|---|---|
| classical | +2.21 [1.50, 2.93] n=4,735 | +12.51 [6.87, 18.52] n=140 |
| meta (P≥0.55) | +3.08 [2.29, 3.87] n=3,956 | +18.00 [7.46, 31.84] n=56 |
| **portfolio (top-3)** | **+3.40 [2.57, 4.26] n=3,085 / 1,094 sessions** | **+18.95 [8.13, 33.51] n=53 / 25 sessions** |

Top-3-by-p_win selection *improves* on the meta stream (+0.32 / +0.95) — M8's ranking is
informative within the gated set. **REF_PORTFOLIO_BPS = +3.4** now shown in the forward status
(informational; the M10 gate is untouched).

## 2. Implementability — v1.2 capital-basis amendment (user decision 2026-07-18)

**Primary sizing basis moved to the $10k research-gate currency** (brief §1: "$10k notional
per plan"); the $1,000 deploy account remains as a single reported flag
(`implementable_deploy`). On the $10k basis, implementability is **100% in every year and on
the holdout** — the research stream is unconstrained by capital, as the research standard
intends. The deploy lens preserves the original finding unchanged: pooled **85.2%**, by year
2022 78.3% / 2023 90.1% / 2024 88.3% / 2025 91.8% / **2026 67.6%**, holdout **58.5%** —
at current prices ~$400/slot cannot buy one share of a third-plus of selected signals.
Options when adoption time comes (user decision, new registration): max_positions 3→2,
more capital, or fractional-share entry. Recorded — not decided here.

## 3. CUSUM: v1 parameters were miscalibrated; the FINDING is bigger than the fix

- v1 (k=1.25, h=30): **48% of ALIVE history in alert** — the stationary excursion of S under
  ~14.2 bps/day noise exceeds h even at a healthy +3.3 mean. Registered-as-frozen, but no
  forward data existed yet, so a pre-data amendment is clean (v1.1 below).
- **The regime finding (third kill):** evaluated as an implementable state classifier
  (block day t iff alert at t−1), every parameter setting forfeits PnL for nothing —
  blocked-day means +2.5…+3.1 vs calm +3.3…+3.5; e.g. (1.5,120) blocks 16.3% of days that
  earned +2.92. Trailing-performance regime gating has NO next-day predictive content on this
  edge — consistent with the engineV5 and M4 skip-filter kills. The 2023-10→2024-03 "soft
  stretch" raised S yet paid ≈ normal forward — drawdown ≠ death here. Varma-style
  risk-states on this book must come from EXOGENOUS variables (M12 F-intensity, calendar),
  never trailing PnL, and any such gate needs its own registration.
- Also: the meta-filtered stream never died in 2022-23 (+4.2 / +2.8 by year) — the "weak
  2022-23" lore applies to the unfiltered classical stream, not the operated one.

## 4. v1.1 amendment (pre-forward-data, this session): CUSUM as tripwire only

k=1.25, **h=150**: ~5.2% benign alert time on alive history; dead-edge detection median
**69 sessions**, range [18,148], 20/20 synthetic restarts detected. Role: catastrophic-death
HUMAN-REVIEW tripwire, months-scale by design (bleed at $1,000 while waiting ≈ noise). It
must never become a trading filter without new registration + evidence (see §3).
Code/tests updated (`positioning.py`, 437 tests green); parameters now frozen for the shadow.

## Files

`scripts/m15_backtest_reference.py` (reproducible run), forward status now shows the
portfolio reference. Registration doc carries the v1.1 amendment.
