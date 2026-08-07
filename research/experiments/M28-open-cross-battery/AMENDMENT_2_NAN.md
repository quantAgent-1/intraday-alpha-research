# M28 Amendment 2 — NaN defect voided the first train run; train re-run, validate untouched

Written 2026-07-27, after the first `train` run and **before any validate statistic was
computed**. The validate period was never consumed (the run stopped at NULL-AT-ADMISSION and
`stage_validate` was never invoked), so nothing about the single test is contaminated.

## The defect

The first train run reported **identical statistics for all five pre-market signals** —
IC −0.0049, CI [−0.0156, +0.0064], p 0.4110 for `pm_ret`, `pm_vol_z`, `pm_range`, `pm_late`
and `pm_accel` alike. Five different formulas cannot produce identical ICs to four decimals,
and the raw panel columns are demonstrably different (pairwise correlations from −0.83 to
+0.31). That impossibility is what exposed the bug.

Cause, in two parts:

1. **polars propagates NaN through `mean`, `std` and `quantile`.** `zscore_panel` computes
   its winsorisation bounds and moments with `.over("date")`, so a *single* name with a NaN
   pre-market value poisoned the z-score for **every** name in that session. Roughly 35% of
   name-days have no usable pre-market prints, so essentially every session was poisoned:
   `z_pm_*` ended up with **47 finite values out of 100,271**.
2. **`drop_nulls()` does not remove NaN.** The poisoned rows were NaN, not null, so they
   passed every downstream filter into `session_ic`, where `argsort(argsort(x))` ranked them.
   Ranking an all-NaN array yields a deterministic but meaningless order — and the *same*
   order for all five signals, because they carry NaN in the same rows. Hence the identical
   ICs.

The nine group-A signals were unaffected (0 NaN throughout) and their reported ICs stand.
**Group B was never actually evaluated.** The first run's NULL-AT-ADMISSION verdict therefore
covered only 9 of the 14 candidates and is void as a family verdict.

## The fix

1. NaN → NULL on every signal column at load, so polars' null-skipping semantics apply
   everywhere downstream.
2. A hard tripwire, `assert_no_nan_z`, raises if any z column ever contains NaN or has zero
   finite values. This defect cannot recur silently.
3. Defence in depth: explicit `is_finite()` filters in both `session_ic` and the portfolio
   builder, so neither can rank or trade a non-finite value even if a future path reintroduces
   one.

Coverage after the fix: `z_pm_*` carries **65,458–65,520** finite values (was 47); group A
unchanged at 100,271.

## What is re-run, and what is not

`train` is re-run in full. **Nothing else changes**: the universe, the split, the 14 signal
definitions, the FDR rule and q=0.10, the sign convention, the composite rule, the decile
construction, the cost assumption from Amendment 1, and the PASS bar are all exactly as
registered. Re-running a computation that was demonstrably broken is not a goalpost move; the
thresholds it is judged against are untouched, and the validate period has still never been
read.

## Standing note

This is the second distinct class of silent-corruption bug in two days (the first being
raw-vs-adjusted lake mixing). Both were caught by an *impossibility* in the output — a −1248
bps mean, five identical ICs — rather than by any threshold. Sanity checks that assert
structural impossibilities are worth more than tighter statistical gates: **when a result
cannot be true, that is information, and it must never be explained away.**
