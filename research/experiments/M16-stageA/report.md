# M16 Stage A — GP flow book — RESULT 2026-07-19

Registered before economics (`M16-stageA-flow-book-v1`; frozen spec in M3_REGISTRATION.md).
Panel: 5 names x 1,105 test days (walk-forward by year, 2022-2026; first fold trains
pre-LETF-era so 2022 runs calendar-only — correct PIT behavior). Sim: theta=0.25 partial
adjustment, no-trade band, whole shares at $10k, two-regime DR-X3 costs, flat 15:50
(primary) / ride-to-close MOC lens (registered secondary).

## Numbers (bps of the $10k book per day; session-bootstrap CIs)

| Stream | mean/day | 95% CI | sd/day |
|---|---|---|---|
| gross | +2.30 | [+0.05, +4.96] | 44.0 |
| **net (primary, E/Q 0.65)** | **+1.69** | **[-0.64, +4.25]** | 43.8 |
| net (stress E/Q 1.0) | +1.61 | [-0.97, +4.42] | 43.8 |
| net (MOC-exit lens) | +1.98 | [-0.72, +4.68] | 47.2 |

Orders/day mean 14.2 (max 40 — 30/day cap exceeded on rare days; a live operator would
skip deltas, mean is well inside). Costs ~0.6 bps/day — the turnover control works; the
stress run barely moves (costs are NOT the binding constraint; variance is).

By year: 2022 (calendar-only fold) -0.76; **2023 +2.42; 2024 +0.42; 2025 +4.32; 2026 +2.64**
— positive every year the flow feature has training data, best exactly when the single-stock
complexes peaked (2025) — consistent with the M12 mechanism.

## Verdict vs registered bars

- KILL test (pooled net <= 0): **NOT killed** (+1.69 > 0).
- SUCCESS bar (CI-lower > 0 + attribution): **NOT met** (CI-lower -0.64).
- Attribution: with only the 3 named features, PnL is definitionally flow/calendar; the
  year-split is the sharper evidence — the calendar-only fold is ~flat-negative and the
  economics appear exactly when F(t) enters training. No pattern-mining escape hatch exists
  in a 3-feature ridge.

**Outcome: REPORT-ONLY — alive but unproven.** Annualized shape ~ +4.2%/yr on book at
Sharpe ~0.6 (point estimates); at sd 44 bps/day, proving +1.7 needs ~2,600 days pooled —
or a stronger signal, or more LETF-era data. Per registration: NO promotion to
forward-shadow; NO parameter iteration (one look, spent). Re-evaluation only via a NEW
registration once materially more LETF-era data has accrued (the panel grows daily with
forward collection; complexes' AUM path is the driver to watch).

Post-hoc observation (labeled as such, not a registered claim): the LETF-era subset
(2023+, n=854) runs ~ +2.4/day — the era split was not a pre-registered test.

## Files

`scripts/m16_stage_a.py` (frozen params inline); panel `research/experiments/M16-flow-book/`.
