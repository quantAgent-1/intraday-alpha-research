# Amendment 2 — Stage 3 UNBLOCKED: the original quote-signed rule runs on the 16 virgin names

Written 2026-07-27, **before any quote data for a non-discovery name was bulk-pulled and
before any OOS return statistic was computed.** Continues `PREDECLARATION.md` (universe,
window, outcome vocabulary unchanged) and supersedes the BJZ Phase-3 plan (that method
failed its own Phase-1 gate; ledger row of 2026-07-27).

## 1. What changed

Stage 3 was METHOD-BLOCKED on the assumption that quote history for non-discovery names is
unaffordable. That assumption came from Databento pricing and was falsified by a direct
probe today: **Alpaca's free tier serves full historical SIP quotes** — one full RTH day of
QCOM = 49,082 rows / 3.0 s; CSCO = 192,981 rows / 6.2 s. All 16 OOS names × 604 sessions ≈
**11 hours of free background pulling.**

Consequently the decisive test uses **the original frozen rule** — `r2a_prong0.process_symbol`
verbatim (quote-mid signing, ≥30 signed odd-lot prints, per-name Q3(|OLI|) fires, open-print
→ last-bbo-mid ≤ 15:45) — on names it has never touched. No method substitution, no V1/V2/V3
translation gates needed. The three quote-free attempts (tick 0.457, minute-VWAP 0.111, BJZ
all-size corr 0.066 / gate-fail) are dead and stay dead.

## 2. Quote-source fidelity gate (V-QS) — must pass BEFORE the bulk pull is consumed

The discovery `bbo1s` lake is Databento 1-second-sampled BBO. The OOS quotes are Alpaca raw
SIP ticks, downsampled by us to the identical convention: for each second boundary B, the
last quote with ts ≤ B, stamped B (state-at-boundary; a trade in [B−1, B) can only see
quotes stamped ≤ B−1 — the completed-second rule). Written to `data/raw/bbo1s/{SYM}/{YYYY-MM}.parquet`
schema-identical to the owned lake, so the frozen code reads it unmodified.

On ≥5 owned (name, day) pairs spanning tiers (KLAC/TXN/NVDA class), comparing
Alpaca-downsampled vs owned Databento bbo1s **on the same days**:

| # | check | threshold |
|---|---|---|
| V-QS1 | matched-second mids | median \|Δmid\| ≤ 0.5 bps AND ≥ 99% of seconds within 2 bps |
| V-QS2 | day-level OLI recomputed with each quote source (same trades, frozen signing) | max \|ΔOLI\| ≤ 0.05 |
| V-QS3 | exit_mid (last mid ≤ 15:45) | \|Δ\| ≤ 1.0 bps every sampled day |

**Fail any → the bulk pull is not consumed for a verdict** until the convention defect is
found and fixed (fixes are convention-level, outcome-blind by construction: no OOS return
exists yet). If Alpaca and Databento SIP genuinely disagree, that is reported and the test
halts — a verdict cannot rest on a quote source that fails to reproduce the discovery lake.

## 3. The decisive statistic and outcomes (carried over, fixed)

- **Primary**: mean of the **daily equal-weight portfolio** of that session's fires across
  the 16 names, **net**, session-bootstrap 95% CI (seed 7, 2,000 reps).
- **Cost**: measured per-name exit half-spread (median 15:40–15:45 quoted spread ÷ 2 from
  that name's own new quote data, full-window median, untuned) + 0.206 bps SEC fee. Flat
  3.0 and 6.0 bps stresses reported non-gating. Entry at the cross = 0 spread.
- **Outcomes** (identical to PREDECLARATION §3): **CONFIRMED** (net CI-lo > 0 AND gross ≥
  2× cost) / **REFUTED** (CI-hi < 0) / **NOT-CONFIRMED** (CI spans 0, point < +6.0) /
  **PARK-UNDERPOWERED** (CI spans 0, point ≥ +6.0; widening-only follow-up).
- Mandatory non-gating diagnostics: per-name signs (16), tech-adjacent vs rest split, year
  split, fires/day, funnel, intercept-preserving beta decomposition vs the 16-name EW
  universe (the OLS-residual-mean trap is on record), session-shuffled placebo (200 draws,
  seed 101), cost sensitivities.

**This single run consumes the 16 virgin names for this phenomenon.** No re-analysis of
them may ever be used to argue for the effect regardless of outcome.

## 4. Registration

`retail_fade_daily_v1` is registered in the ledger **after V-QS passes and before the OOS
runner executes** (marker file `registration_marker.json` in this directory; the runner
refuses without it). Phase 3 = the family's single sanctioned historical look. CONFIRMED →
forward T+1 clock on the 26-name panel through the live-engine shell (dark-until-gate
pattern); anything else → family closed at its stated outcome.

## 5. Honesty inventory (updated)

Expressions of this one phenomenon so far: quote-OLI event mean (pre-declared FAIL) →
daily unit (post-hoc, positive, tainted) → BJZ signing (METHOD-FAILED) → **this test**.
The FDR debt is why only the 16 virgin names + forward sessions count, and why the daily
unit had to be declared primary *before* this test rather than after it.
