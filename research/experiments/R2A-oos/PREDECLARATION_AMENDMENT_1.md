# Amendment 1 to the R2-A Stage-3 pre-declaration

Written **2026-07-26, after attempt 1's validation gate was run and before attempt 2 was
implemented or run.** The universe (16 names), the window, the primary statistic, the
power arithmetic and the outcome definitions in `PREDECLARATION.md` are **unchanged**.
This amendment concerns only the *signing method* whose admissibility gate failed.

## What happened to attempt 1 (tick-rule signing)

**V1 FAILED on the merits: pooled corr(OLI quote-signed, OLI tick-signed) = 0.4566**,
against a pre-declared threshold of 0.90. Per name:

| NVDA | TSLA | AMD | MU | GOOGL | KLAC | MRVL | LRCX | TXN | AMAT |
|---|---|---|---|---|---|---|---|---|---|
| 0.469 | 0.012 | 0.438 | 0.602 | −0.001 | 0.702 | 0.639 | 0.658 | 0.676 | 0.585 |

This is a real result and it is recorded permanently: **on off-exchange odd-lot prints,
the tick rule is not a usable substitute for quote-based signing** — and it is worst
exactly where spreads are tightest (TSLA 0.012, GOOGL −0.001), which is mechanistically
sensible: consecutive retail prints in a 0.6 bps-wide megacap book differ by sub-penny
price improvement, i.e. by noise, so the tick rule has almost nothing to classify on.
V1 involves no bar data and is unaffected by the defect below.

## What was VOID in attempt 1

V2 (−1248 bps) and V3 were computed with an implementation defect of mine, not a property
of the method: the return divided a **`bars1m` (split/dividend-ADJUSTED)** exit close by a
**`bars1d` (RAW)** open. Measured ratios on 2025-03-06: KLAC 0.0991 (10:1 split), TXN
0.9645 (dividends), NVDA 0.9996. This is the raw-vs-adjusted landmine already on record
(`SIM_AUDIT_2026-07-21.md` finding F-A; the M27 split-guard standing note).

**Those two numbers are void — they are evidence of nothing, in either direction.** Any
variant tested from here computes its return **entirely inside `bars1m`** (open of the
09:30 bar → last close ≤ 15:45), so the adjustment factor cancels within the day.

## What is permitted from here — exactly one more attempt

To keep this from degenerating into shopping for a method that passes:

1. **Exactly ONE further signing variant may be tested: minute-anchored signing** — each
   odd-lot print is signed against the contemporaneous `bars1m` **VWAP** of the minute
   containing it (a volume-weighted average price reference in place of the 1-second quote
   mid), with the frozen tick-rule fallback and carry-last handling unchanged. Rationale: a
   centred price reference should track the prevailing mid far better than either a stale
   previous-minute close or the tick rule. Self-contamination is negligible (one odd-lot
   print carries ~0.1% of a minute's volume).
2. **The thresholds are unchanged**: V1 ≥ 0.90, V2 same-sign and within ±30% of +14.87,
   V3 median |Δreturn| ≤ 3.0 bps. They are not renegotiable.
3. **If attempt 2 fails any of V1/V2/V3, Stage 3 is METHOD-BLOCKED and closed.** No third
   variant, no partial-universe rescue, no "directionally consistent" language. The honest
   conclusion in that case is stated in advance: *R2-A cannot be confirmed out of sample on
   owned or free data, because confirmation requires quote history for the test names and
   that is not affordable at this project's budget.* That conclusion goes to the user as a
   data-purchase decision, not as evidence about the effect.
4. The running trades backfill continues regardless — the trade data is required by any
   variant and is reusable if the axis is ever revisited.

## Standing note added for future families

Any statistic that mixes `data/raw/sip/bars1d` (raw) with `data/raw/sip/bars1m` (adjusted)
is wrong unless both legs are same-day ratios. Prefer computing a return entirely within
one lake. This is the second time the adjustment convention has produced a large spurious
number in this project.
