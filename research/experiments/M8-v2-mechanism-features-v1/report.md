# M8-v2 mechanism-informed meta-gate — FINAL REPORT (2026-07-20)

**VERDICT: KILL — 4 of 5 registered bars failed at the frozen q=0.55 gate. M8-v1 stands;
F/ADV stays report-only. The M9 snapshot ceiling extends to mechanism features.**
Family moc_meta_v1, third look, one look as registered (ledger: registration line 96,
grading key line 97, this result). Adoption fence discharged trivially: nothing queues for
the M10 gate; the forward streams were never touched.

## Preconditions (both required, both met)

- Harness validity: corr(p_v1 from this code path, stored M8-meta-v1 p_win) = **1.0000**
  on n=4,735 — exact reproduction of the original run (folds/hyperparams/frame verbatim).
  The v1-gated stream also reproduces the corrected M15 audit exactly (n=2,844, +4.03).
- Redundancy kill (|corr| > 0.8 vs imbalance features): **did not fire** — norm_imb 0.017,
  imb_growth ≈ −0.005, paired_ratio 0.058; max overall = log_adv20 at 0.353 (mechanical:
  ADV sits in F/ADV's denominator). The mechanism features are genuinely NEW information.

## Bars (frozen key, q=0.55 streams; v1 n=2,844 vs v2 n=2,615 on identical folds/rows)

| bar | requirement | v1 | v2 | outcome |
|---|---|---|---|---|
| (i) | hit-rate improvement (strict) | 0.5774 | 0.5755 | **FAIL** (−0.19 pts) |
| (ii) | ci_lo up OR ≥1.2× per-trade Sharpe | 3.109 / 0.1954 | 2.853 / 0.1919 | **FAIL** (both lower; daily Sharpe agrees: 0.2436→0.2297) |
| (iii) | Δnet ≥ +1.0 bps/event | 4.031 | 3.916 | **FAIL** (−0.115) |
| (iv) | beats Occam filter on Sharpe | occam 0.1766 | 0.1919 | PASS (moot) |
| (v) | improvement in ≥3 symbols AND ≥3 years | — | 2 symbols (NVDA +0.26, MU +0.04), 1 year (2023 +0.12) | **FAIL** |

## Reading (interpretation, not wiggle room)

This is the cleanest form of a null: the new features were *not* redundant (corr ≈ 0.02 with
the feed), the model *did* use them (range_pos_1555 gain rank #3, day_vol_ratio #7), and
out-of-sample gating still got slightly worse — mild overfitting from 6 extra features on
~6k training rows, exactly what the raised third-look bar exists to catch. Mechanistically
consistent with M12's own design: F explains WHICH NAMES carry the edge (slow, cross-name),
while the M8 model already observes the live imbalance state at 15:55:10 — F's within-name
daily variation adds nothing at event level. The mechanism is real (M12 stands); it is
already priced into the champion's universe.

Context rows recorded and explicitly NOT usable: at q=0.60 v2 leads (5.40 vs 4.60, n=1,088)
— gate-shopping is forbidden by the frozen key and this pattern is exactly what a noise
process produces across a gate grid. The Occam standalone filter (+3.57, n=1,217) also
trails the v1 model — the M12 promotion object underperforms the model as a pure filter.

## Diagnostics for the record

9 folds; feature null rates 0.0 across all six (full span); F/ADV(pinned r) vs M12's
F/ADV(open→15:55): corr 0.775 on n=6,198 (two r-windows, expected sub-1); Occam boundary =
train-fold top-tercile of positive-complex |F|/ADV per the approved construction.
Outputs: events.parquet + metrics.json in this directory. Suite 494 green at run time.

## Consequences

- M8-v1 remains the meta-gate; the frozen forward model (research/forward/m8_model.txt)
  was never touched. At the M10 gate, the adoption decision has no v2 candidate.
- F/ADV remains a REPORT-ONLY forward annotation (as promoted by M12) — not a model feature.
- moc_meta_v1 family: three looks spent (M8 PASS, M9 NULL, M8-v2 KILL). Any fourth look
  needs a new mechanism or data class and clears a still-higher bar.
