# M28 Amendment 1 — the bars-only cost estimator failed; primary cost becomes the flat stress

Written 2026-07-26, **after the cost calibration was run and BEFORE any train IC, composite,
portfolio return or validate statistic was computed.** No return-bearing quantity had been
produced at the time of this decision, so nothing here can be outcome-motivated.

## What failed

REGISTRATION.md §8 specified estimating each name's 15:40–15:45 exit half-spread from minute
bars, calibrated against the ten names whose true quoted half-spread is measured from `bbo1s`.
The estimator was `hs = k * P25[(high-low)/close]` over the exit-window minute bars.

It does not work. Fit quality (`cost_calibration.md`):

- **log-log correlation with the measured truth: −0.515** — the wrong sign
- median absolute error **49%**, median leave-one-out error **55%**

The failure is mechanistic and obvious in hindsight: a minute bar's high-low range is
dominated by **volatility**, not by the spread. The most liquid, fastest-moving names have the
widest minute ranges and the *tightest* spreads (NVDA range 8.36 → true half-spread 0.70;
TSLA 10.02 → 0.78; AMD 8.74 → 0.62), while KLAC — the widest true spread in the panel at
3.60 — has the *narrowest* range at 4.40 because it is a slow, high-priced stock. The
estimator ranks names almost exactly backwards.

Using it would charge the least cost precisely to the names that cost the most. That is not a
noisy estimate; it is an anti-informative one, and it must not price a result.

## What replaces it

The registration already declared a **flat 3.0 bps half-spread stress** as the reported
sensitivity. That value is now promoted to the **primary** cost assumption. Nothing new is
invented: the number was pre-declared, it requires no post-hoc fitting, and it is
conservative — roughly **3.5× the measured megacap median** (~0.85 bps across the ten
measured names) for a universe consisting entirely of top-200-by-dollar-volume large caps.

Reported alongside it, so the dependence is fully visible:

| label | exit half-spread | rationale |
|---|---|---|
| **primary** | **3.0 bps** | the pre-declared stress; conservative for this universe |
| measured-median | 0.85 bps | median of the ten `bbo1s`-measured names — an optimistic bound |
| double-stress | 6.0 bps | 2× the primary |

The SEC §31 fee of 0.206 bps on the sale leg is unchanged, and entry at the opening cross
still costs zero spread.

**The PASS bar is unchanged**: validate CI-lo > 0 AND gross ≥ 2 × mean daily cost. Moving to a
*higher* cost makes the 2× test strictly harder, so this amendment cannot manufacture a pass.

## Standing note

A bar-range statistic is not a spread proxy on liquid names. If a future family needs a
cost model without quotes, use a genuine spread estimator (Corwin-Schultz, Abdi-Ranaldo) and
validate it against measured quotes before use — or, as here, fall back to a conservative
flat charge. The ten-name `bbo1s` truth set is the only spread ground truth this project
owns, and any estimator that cannot reproduce its *ordering* is unusable.
