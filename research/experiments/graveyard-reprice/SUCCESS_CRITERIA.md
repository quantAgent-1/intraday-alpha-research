# Statistical-edge success criteria — experiment phase

Written 2026-07-27. Binding for signal/strategy discovery until adoption gates.

## What counts as success

**Statistical edge**, not dollar P&L at a small small-account lens.

- **No $1,000 deploy constraint** in any promotion rule, training objective, or kill bar.
- Economics reported in **bps** (and optional $ at the **$10k research notional** for ADIA panels only).
- Deploy-lens ($1k, whole-share, LETF translation) is **report-only** and may not appear in gates.

## PASS bar (single stream or portfolio stream)

All required, on the **taken** event stream or the **daily portfolio PnL** series as declared:

1. **Power floor:** N ≥ 250 events across ≥ 150 sessions (or daily series T ≥ 150 sessions).
2. **Mean net > 0** with **day-clustered 95% CI lower bound > 0**.
3. **Cost realism:** mean gross mid-alpha ≥ **2×** mean modeled all-in RT cost under the **primary** cost model for that expression.
4. **Stress:** mean net under **2× primary cost** still has CI-lo ≥ 0 *or* is reported as PROMO-FRAGILE (not a hard kill in experiment phase; hard kill at adoption).
5. **Report ADIA:** native-frequency SR, PSR(SR₀=0), MinTRL — display for experiment phase; PSR ≥ 0.95 is a **strengthen**, not required to declare a working primary.

## Explicit non-goals (this phase)

- Material monthly dollars at $1k.
- Live feed cost recovery.
- Broker exit-leg fill-ins.

## Re-price policy

Re-pricing **already published** mid-alphas under corrected cost / portfolio shape is **not** a new family look. It may not invent new thresholds or conditioners. New thresholds require a **new registration**.
