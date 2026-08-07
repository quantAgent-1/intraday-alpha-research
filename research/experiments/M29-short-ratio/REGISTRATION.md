# M29 `short_ratio_battery_v1` — PRE-REGISTRATION

Written 2026-07-27, **before any FINRA short-sale figure was joined to any return.** The
only prior computation is a source probe (format + coverage: header
`Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market`, ~10k symbols/day, all
M28-universe names present across 2024–2026; no return touched).

## 1. The information set — genuinely new, and exactly what the M28 null demanded

M28's adequately-powered null closed the **bar-derived** signal axis at the open-cross
structure and stated its successor condition: *"a new family in this space needs a
genuinely different information set, not a new estimator or a wider panel."*

This is that: **FINRA Reg SHO daily short-sale volume** — per-symbol, per-day short volume
vs total volume as reported by every TRF/exchange, published by FINRA the **same evening**
(≈ 6–8 pm ET). A day-t−1 file is therefore knowable the evening before a day-t 09:28
market-on-open decision — the exact timing our frozen execution structure needs. No family,
prong-0, diagnostic, or map row in this program has ever read it. Field literature
(Boehmer–Jones–Zhang class): elevated daily short-sale ratios predict negative returns over
days-to-weeks horizons, with the caveat that most short volume is market-maker liquidity
provision — which is why the battery is built on *relative* (z-scored) measures, not levels.

**Honest prior: ~0.10–0.15.** The documented effect concentrates in smaller caps and at
multi-day horizons; our universe is large-cap and our hold is intraday-only (the structure
captures only the intraday component of any drift). Stated before the data speaks: the
modal outcome is NULL-AT-ADMISSION, and that outcome would price this axis properly.

## 2. Structure, universe, split — inherited from M28 verbatim

Open-cross entry (0 spread) at 09:28 decision → exit 15:40–15:45; dollar-neutral top-vs-
bottom-decile cross-section, gross 1.0; **184-name universe and the exact M28 panel
outcomes** (`M28-open-cross-battery/panel.parquet`, verified 32/32 including the black-box
look-ahead test); flat 3.0 bps exit half-spread + 0.206 SEC fee (Amendment-1 convention);
TRAIN 2024-01-02…2025-05-30 (admission + signs only), VALIDATE 2025-06-02…2026-05-29
(single test, consumed once **by this family** — M28 never read it; each family's
consumption is its own), sealed holdout ≥ 2026-06-01 never fetched.

## 3. The battery — FOUR signals, frozen

For trade day t, all inputs come from files dated **≤ session t−1** (the t−1 file is
published t−1 evening). `sr = ShortVolume / TotalVolume` per name-day.

| # | name | definition |
|---|---|---|
| S1 | `sr_z21` | (sr_{t−1} − mean sr_{t−22…t−2}) / sd(same); ≥15 obs required |
| S2 | `sr_d1` | sr_{t−1} − sr_{t−2} |
| S3 | `sr_level` | sr_{t−1} raw (cross-sectional z-scoring happens in the harness) |
| S4 | `exempt_z21` | z-score of ShortExempt/ShortVolume vs its trailing 21 days |

Admission = **Benjamini–Hochberg FDR q = 0.10 across the 4 candidates** on train
session-IC (Spearman, ≥20 names/session), session-bootstrap p (seed 7, 2,000 reps); signs
set by train IC and frozen — the M28 convention exactly. Zero admitted →
**NULL-AT-ADMISSION**, validate NOT consumed. Composite = equal-weight admitted z-scores.

**PASS bar (validate)**: net CI-lo > 0 AND gross ≥ 2× mean daily cost. Outcomes PASS /
BETWEEN / FAIL / NULL-AT-ADMISSION as in M28 §9. One look, no re-tune, no threshold sweep.

## 4. PIT discipline and verification (before any statistic is interpreted)

- NaN → null at load + finite filters + the `assert`-style tripwire (the Amendment-2-NAN
  lesson applied from birth).
- **Black-box PIT test**: perturb (in a temp copy) the day-t file → the day-t signal must
  be UNCHANGED (it may only read ≤ t−1); perturb the day-t−1 file → the day-t signal must
  MOVE. Run on sampled names; any failure blocks interpretation.
- Disclosed risk (handed to deep research, DR-B): FINRA occasionally republishes corrected
  files; the archive we download today may differ from what was knowable that evening.
  Direction of bias unknown; flagged, not modeled.

## 5. Mandatory diagnostics (never gating)

Per-signal IC train (and validate if reached) incl. rejected; decile monotonicity;
turnover/legs-per-day; per-year; placebo (session-shuffled composite, 200 draws, seed 101);
cost sensitivities (0.85 / 3.0 / 6.0 bps); coverage funnel incl. names missing from FINRA
files.
