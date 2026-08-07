# Intraday minutes-to-hours: combination hypotheses (orchestrator, 2026-07-23)

> **REVISED SAME DAY under the binding user decision terminating the close-auction
> direction.** H3 (intraday F̂ pre-close drift), H4 (basis nowcasting), H5 (two-print day),
> and every close-window pool component are WITHDRAWN — banned direction. What stands:
> H0 (slow constrained flow, now expressed only in continuous windows), H1 restricted to
> the INTRADAY pool (macro-release windows pending the DR-X9 refuter verdict; earnings-day0
> intraday windows only if the field fence is re-examined; open-window morning states), and
> H2 (basket common-vs-idio split — horizon-agnostic, applies to any window family).
> The DR-X9 wave (4 modalities + 3 refuters, 2026-07-23) governs which release classes, if
> any, survive into an H1 registration; modality D's steelman (index beta + killed intraday
> momentum) must be answered by a residualization prong in any H1 design.

First-principles hypothesis generation, per user directive. Not registrations — candidate
science. Each hypothesis states: the information, the MECHANISM (who pays and why they are
slow), the expression, honest power arithmetic, and the protocol path. Constraint set:
manual 5–25s latency, ~2 bps round-trip cost floor on megacaps, owned data only ($0).

## 0. The structural insight the corpus points to but never exploited jointly

Every surviving or near-surviving result in this program is the SAME phenomenon at a
different clock: **price-insensitive scheduled flow, executed slowly, by an agent whose
constraint (not information) sets the trade** — LETF issuers at the close (champion),
vol-target re-levering after macro releases (M20 screen), attention/fund flow at the open
(M24 t50 near-miss), index/pension flow at calendar closes (M14/M25). Individually, each
event family is statistically starved: N per family ~10²–10³, per-event noise 30–300 bps,
so per-family CIs straddle zero forever. **Hypothesis zero: these are not separate edges —
they are one edge (slow constrained flow) sampled at different windows.** If true, the
correct estimator is not another per-family cell; it is a POOLED model over all scheduled
event-windows with the event class as a feature. Pooling buys the N that no family has
alone; the mechanism prong is inherited per-class from work already done.

## H1 — The pooled scheduled-event-window meta-model (the ML pipeline candidate)

**Hypothesis.** Over the union of scheduled event-windows — macro releases (10:00 cluster,
13:02 auctions, 14:00 FOMC), earnings day0 sessions, calendar-flow days (month-end,
quad-witch), and high-F̂ days (LETF re-hedge pressure computable intraday, see H3) — the
minutes-to-hours continuation/reversion structure is jointly learnable: a classifier on
window-state features can select the subset of event-windows where slow-flow continuation
clears 2× cost, even though no single family passes alone.

**Event inventory (owned, 2020–2026, 5 names):** macro windows ~1,100; earnings day0 ~170
(5-name) / ~340 (with proxy names); calendar-flag sessions ~500; high-F̂ days ~400–600.
Union ≈ 2,000–2,500 event-window observations with h ∈ {30m, 60m, 120m} mid-to-mid labels
from owned 1s TOB. Deduplicate overlaps (an FOMC month-end exists) with type dummies.

**Features (all PIT, all owned):**
- reaction: 5-min post-anchor return (M20 object), its |magnitude| percentile (PAST-ONLY)
- decomposition: basket-common reaction (5-name mean) vs name residual — H2's split
- state: trailing-20 vol, spread at decision, overnight gap, day-of-week/announcement dummies
- flow: F̂_t/ADV (H3), calendar flags (M25 definitions), earnings-day0 flag
- positioning proxies: prior-3-day cumulative return (crowding), open-auction basis (M24)

**Model + promotion (protocol-shaped):** LightGBM classifier P(net_h > cost floor | state),
walk-forward yearly folds, seed 7 — the M8 architecture (proven), NOT sequence models
(M4 dead). Promotion currency = plan-level paired EV of the gated stream vs its own
ungated baseline (never IC). DSR at honest counts (this family inherits the M20 40-cell
debt + M22/M24 looks + its own grid). MinTRL computed at registration from the dev CI.
Known ceiling risk: M9/M8-v2 showed snapshot-GBDT ceilings on the CLOSE family — the bet
here is that the ceiling binds per-family, not on the pooled cross-window structure. That
is exactly what the experiment tests.

**Sequencing:** REGISTER ONLY AFTER the DR-X9 wave verdict (in flight): if the macro
classes die by prior art, the pool shrinks to earnings/calendar/F̂ windows (~1,000 events)
and the registration must say so; if a timed slow payer returns, macro classes anchor the
pool. Screen → forward-judged Stage-2 (M20F pattern), never direct trading.

**Power:** pooled n≈2,000, per-event σ≈60 bps at h60 ⇒ se≈1.3 bps pooled; a gated top-30%
subset (n≈600) needs mean ≥ ~5 bps for CI>0 — plausible if M20's +9–13 bps cells are real
members of a broader structure. This is the first minutes-to-hours design in the program
with honest power BEFORE conditioning.

## H2 — Common-vs-idiosyncratic reaction split (a free upgrade to any window family)

**Hypothesis.** Slow re-levering flow is INDEX-level; single-name expressions of
announcement drift are mostly beta carriers plus idio noise. Therefore (a) the tradable
continuation signal is the basket-common reaction, not the name's own; (b) trading the
5-name BASKET (equal-weight, one decision, five tickets — manual-feasible at our k=2…
relaxed to basket-as-one-position) cuts per-event σ by ~√3–2× (idio diversification),
which is worth more than any feature. M20 measured per-name; its se≈18 bps VALIDATE
failure was partly THIS design error. Basket labels on owned data are free to construct.
Feeds H1 as features and as the preferred expression.

## H3 — Intraday F̂: the champion's payer is observable BEFORE the close

**Hypothesis.** The LETF rebalance flow F = (L²−L)·AUM·r_day is deterministic in r, and
r_open→t is observable all day: F̂_t is a real-time forecast of the close's forced flow.
On high-|F̂| afternoons in complex names, the last hours drift toward the flow direction
(others pre-hedge the same predictable close flow). FENCE HONESTY: DR-X1 closed
"LETF front-run as a standalone family" by field, and the conditioner path is reserved to
champion features — so H3 enters ONLY as (i) an H1 feature and (ii) a post-forward-gate
champion feature (already the F/ADV plan). No standalone registration. Its testable
residue inside H1: does F̂_t/ADV interact with afternoon windows' continuation?

## H4 — Basis nowcasting: predict the 15:55 dislocation from 15:35–15:50 tape state

**Hypothesis.** The champion observes the dislocation at 15:55:10 and pays taker spread to
ride it 5 minutes. If pre-close tape state (quote-intensity asymmetry, signed volume where
tape is owned, spread dynamics, F̂_t, calendar flag) predicts the SIGN of the coming basis
with ≥60% hit BEFORE NOII near/far populate, a passive entry at ~15:50 earns the spread
instead of paying it and captures the dislocation's FORMATION (15:50→cross), roughly
doubling the champion's per-event take. Distinct from dead M6-GBM (whose 15:50 features
were NOII-degenerate — tape features are not). Risks, pre-stated: maker-fill phantom
class (L1/DR-X8) — economics must be replay-grade with quote-confirmation, and the
maker leg is exactly what Phase-0 arm-B audits live. Protocol path: new family, one
screen look (sign-prediction accuracy vs 0.5, NO economics), economics only if the screen
clears 0.55 with CI — then replay with the v1.4+ fill stack. Champion-adjacent: any
adoption is a post-forward-gate registration.

## H5 — Auction-sandwich completion: the day as a two-print market

**Hypothesis.** M24 showed open dislocations revert by the close on broad names (t50
+37 bps, near-miss) with ρ≈0 to the champion. The general object: BOTH daily auctions are
liquidity events of the same flow system; the intraday drift between them is partially
determined by the pair (open dislocation, expected close flow F̂). A 2-feature model
(basis_open, F̂_day-so-far) on the open→close return is the minimal combination version —
enters H1 as features; standalone revival stays fenced to the M24 forward-judged path.

## What is deliberately NOT here

Lead-lag/stat-arb at minutes (crowded, DR-X4 structural), sequence models on bars (M4),
regime gating by trailing PnL (3× dead), path/breakout prediction (doctrine-banned),
anything requiring data we don't own or latency we don't have.

## Execution order

1. DR-X9 wave returns (in flight) → refuters → lane verdict.
2. Register H1 (pooled event-window meta-model) with the wave-informed pool; H2 basket
   expression and H3/H5 features inside it; screen look on TRAIN+VALIDATE pooled with
   ADIA panel; PASS ⇒ forward-judged Stage-2 via the dark sched_window_forward instrument
   (extended to the pooled anchor set).
3. H4 registered separately (sign-screen first, no economics) — the only maker-class idea,
   so it waits for Phase-0 arm-B reality before any economic claim.
