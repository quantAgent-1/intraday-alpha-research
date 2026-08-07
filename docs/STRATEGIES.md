# Strategies we tried (M-series guide)

This page is the **longer explanation** of each research family: what we tried, how
it worked, and what we concluded.

**Start here if you want detail.** For a one-screen overview, use the
[README](../README.md).

**How to use this page**

- Each **M-number** is a *family* of experiments (one idea, sometimes several variants).  
- We usually wrote the rules **before** looking at results.  
- **Failed ideas stay in the archive on purpose** — that is how you know the process is real.  
- Numbers below are historical research results, **not** a promise of future profit.  
- The raw log is `research/ledger.jsonl`; write-ups live under `research/experiments/`.

**Status words in plain English**

| Label | Meaning |
|---|---|
| **Pass** | Cleared the pre-written pass/fail bar |
| **Fail / kill / closed** | Did not clear the bar; we stopped that idea |
| **Between / inconclusive** | One careful look; result fuzzy (often CI includes zero) |
| **Null-at-admission** | Many pre-declared signals; none survived the multiple-testing screen |
| **Diagnostic / report-only** | Measurement tool, not a trading green light |
| **Frozen / banned** | Policy: no more work in that direction |
| **Parked** | Written down but not built or not run |

---

## The story in five chapters

1. **M3–M5 — Same-day “pressure” trades**  
   Only trade when a known market pressure is active (gap, VWAP stretch, leveraged-ETF
   rebalance, …). Later try ML on top.  
   *Punchline:* early profits mostly vanished once fills were made realistic.

2. **M6–M15 — The closing auction**  
   Use the official 4:00 close as a clean exit. Study imbalance and “where the auction
   says it will clear.”  
   *Punchline:* one rule passed a locked final test; it did **not** generalize to most
   Nasdaq names; close work was later **stopped as a program direction**.

3. **M16–M18 — Costs and mean reversion**  
   Measure real trading friction; try mean reversion as a full *system* of filters.  
   *Punchline:* filters reduce losses but do not create edge from a mid-neutral trigger.

4. **M20–M27 — Other same-day ideas**  
   Economic releases, open fade, gap days, earnings days, sizing.  
   *Punchline:* mixed; several “interesting but not promotable” or cost-killed results.

5. **M28–M30 — Wide, careful batteries**  
   Many signals × many stocks, or clean tests on stocks never used in discovery.  
   *Punchline:* three strong null / not-confirmed outcomes on the open-print structure.

---

## Continuous named-payer line

### M3 — Named-payer detectors (`payer_detectors_v1`)

**Idea.** Only trade when a *documented forced-flow* state is active — not always-on
forecasts. Five classical detectors:

| Detector | Intuition |
|---|---|
| `gap_mr` | Fade a large opening gap after the first 15 minutes if it has not extended |
| `letf_window` | Trade *with* end-of-day LETF rebalance demand when the index has moved hard |
| `vwap_magnet` | Fade stretched deviation from session VWAP on range-like days |
| `cascade` | Fade a volume/spread flush after short-term stabilization (needs 1s event bars) |
| `expiry_pin` | Drift toward a nearby strike on monthly options expiry |

Plans are full objects (limit/market entry, stop, targets, hold, curfew) scored by the
causal replayer (k=2 slots, 5–25 s latency, L2-strict limits).

**Outcome.** Early positive nets were **harness-flattered** (odd-lot and late off-market
prints). Under quote-confirmed / condition-coded fills the continuous book lost its edge.
**Family closed** after entry-quality gates also failed.  
**Lesson:** execution realism dominates this horizon; “maker edge” is easy to invent in sim.

### M3-A1 — Bar-tier LightGBM overlay

**Idea.** Use walk-forward LGBM direction / MFE–MAE heads to veto or reprice A0 plans.

**Outcome.** **FAIL.** Forecast-magnitude selection anti-selected reversion states; pure
leg reprice ≈ A0. Bar-tier IC did not become plan-level EV.

### M3 side-ledger — Daily swing (`daily_swing_1d_5d`)

**Idea.** Replicate an external claim of strong 1d–5d IC on NVDA/TSLA (research-only;
system never holds overnight by mission).

**Outcome.** Claimed ICs **killed** on proper OOS; thin 1d cross-sectional IC survived only.

### M4 — Event-stream encoder (`m4_encoder_v1`)

**Idea.** GPU sequence models (TCN / PatchTST) on 1s event bars: multi-task heads for
forward z, MFE/MAE, barrier first-passage; use adverse-barrier probability to skip or
reprice plans.

**Outcome.** **FAIL.** Modest barrier AUCs; selector almost never fired; leg arms harmful.
Stop-risk moments co-located with winners — skipping cut the right tail.

### M5 — Stage A gate

**Idea.** Formal promotion bar on the continuous plan stream (N, mean, CI, stresses).

**Outcome.** **FAIL** at the registered bar (even before the harshest fill restatements).
Holdout remained sealed for this line.

---

## Closing-auction line (historical; later frozen/banned)

### M6 — Closing imbalance / basis (`moc_imbalance_v1`)

**Idea.** Nasdaq closing auction is a *single-print* exit regime: fill ambiguity collapses.
Trade **with** the auction signal into the official cross.

Evolution of the family:

| Cell | What it tested | Result |
|---|---|---|
| Classical NOII @15:50 | \|norm imbalance\| → taker → cross | Positive lean; failed registered bar |
| M6-GBM | LightGBM on NOII features @15:50 | **FAIL** (features degenerate: near/far blank until ~15:55) |
| **M6-FINAL basis** | \|near − mid\| ≥ 10 bps at **15:55:10**, trade with basis, exit at cross | **PASS** (dev ~+2.5 bps/event) |
| **Holdout** (≥2026-06-01) | One-shot sealed confirmation | **PASS** (~+12.5 bps; MU-heavy; seal **spent**) |

**Mechanism intuition (later M12):** name selectivity tracks single-stock **LETF rebalance
flow**, not “all Nasdaq closes.”

**Policy:** user decision later **terminated** further close-auction strategy development.
Artifacts remain for study.

### M6b — Opening imbalance (`open_imbalance_v1`)

**Idea.** Same WITH-imbalance logic on the **open** (MOO + timed exit).

**Outcome.** **FAIL** — all cells negative. Open ≠ close.

### M7 — Daily cross-sectional reversal (`daily_xs_reversal_v1`)

**Idea.** Short-horizon CS reversal on a megacap panel, MOC–MOC (research-only overnight).

**Outcome.** **FAIL.** Megacaps behaved momentum-ish at 5d; costs/splits further hurt.

### M8 — Meta-labeling (`moc_meta_v1`)

**Idea.** Keep classical basis fires; train LightGBM **P(win)** and only take when
`P ≥ 0.55` (headline gate). Does *not* re-pick direction.

**Outcome.** **PASS** on walk-forward OOS: higher hit rate and net vs ungated classical;
incremental ML value modest but real vs count-matched basis threshold.

### M9 — Evolution features + sizing

**Idea.**  
(A) Path features over [15:50, 15:55:10] into the same GBDT.  
(B) Calibrated probability sizing as a **deploy lens**.

**Outcome.** (A) **NULL** — snapshot at 15:55:10 is near-sufficient. (B) no Sharpe gain
from sizing vs flat gated.

### M10 — Forward paper clock

**Idea.** After the holdout is spent, score frozen classical + meta on **new** sessions
only (the live judge).

**Outcome.** Instrument built; clock later **stopped** with the close-auction ban
(partial sessions banked at freeze). Not a full multi-month gate completion in the archive.

### M11 — Cross-sectional OOS (28 names)

**Idea.** If the edge is a general Nasdaq close mechanism, the frozen rule should work
on never-fit names.

**Outcome.** **FAIL** — broad panel net negative; directional ~coin flip. Edge is
**name-narrow**, not universal. High-vol mechanism also falsified.

### M12 — Mechanism horse race (`moc_mechanism_v1`)

**Idea.** Explain name selectivity: single-stock **LETF flow** vs passive **index weight**.

**Outcome.** **LETF flow WINS** (joint regression survives controls; index weight ~null;
GOOGL/no-complex control behaves as predicted). Index-LETF leg dilutes. Promotion path
was report-only F/ADV filter + possible M8-v2 (later killed).

### M13 — Residualization

**Idea.** Hedge close-window common factor to cut variance for reporting.

**Outcome.** **Not adopted** — R² real (~25% market/sector) but residual mean too thin
for the adoption bar.

### M14 — Calendar diagnostic

**Idea.** Forced-flow calendar days (month-end, quad-witch, opex) vs ordinary.

**Outcome.** **Diagnostic only.** Month-end strongest stratum; no standalone promotion.

### M15 — Positioning shadow

**Idea.** Top-3 by p_win, equal notional — portfolio layer on the meta stream;
CUSUM as human-review tripwire only.

**Outcome.** Built as **shadow** reporting stream; selection effect small once true M8
p_win is used. Not a new alpha source.

### M8-v2 — Mechanism features in the meta gate

**Idea.** Add six LETF/mechanism features to M8; same folds/gate.

**Outcome.** **KILL** — OOS degraded vs v1; non-redundant features still did not help.
M8-v1 remains the snapshot ceiling for that line.

---

## Execution, cost, and continuous reversion

### M16 — Phase-0 execution audit + Stage A flow book

**Phase-0.** Manual keying audit of entry/exit quality (user blotter) — **registered**,
not a model family.

**Stage A flow book.** Continuous expression of LETF-flow conditioning into a mid-day book.

**Outcome.** Stage A **BETWEEN** (positive lean, CI spans 0). Costs not the killer;
variance is. Report-only.

### M17 — Cross-sectional / factor momentum (research-only)

**Idea.** Slow momentum replications outside the RTH mission core.

**Outcome.** Stock 12-1 **BETWEEN** (underpowered). Factor/sector ETF momentum
**PASS as replication** (research-only; deploy would need mission amendment).

### M18 — Reversion system (`reversion_system_v1`)

**Idea.** Port engineV2 OU mean-reversion as a **system**: G1/G2 microstructure gates +
maker entries + pooled meta veto @0.55.

**Outcome.** **FAIL.** Filters cut losses but no stream crossed zero. Doctrine:
mid-neutral triggers cannot be conditioned into positive expectancy without mid-alpha
first.

### Cost model (related, not M-number)

Wave-4 work crystallized hard rules: no maker-rebate fantasies at retail; measured
name/time cost surface; see `research/COST_MODEL.md`.

---

## Post ban — continuous intraday (minutes-to-hours)

### M20 — Scheduled macro windows (`sched_window_v1`)

**Idea.** Mid-to-mid continuation after scheduled releases (FOMC, 10:00 cluster, 8:30,
Treasury results, etc.), mid-alpha screen first.

**Outcome.** Train: 2/40 cells pass (10:00 magnitude-gated continuation). Validate:
**confirm failed** (underpowered / wrong sign). Family **spent**.  
Deep research (DR-X9) later **exhausted** FOMC/8:30/10:00 for this shape; only
13:02 Treasury-results cell survived as a parked forward idea (**M26**).

### M21 — Earnings reaction regimes

**Idea.** Diagnostic: do crowded setups break or continue after earnings?

**Outcome.** **Diagnostic complete.** Crowded setups continued on average; no clean
ex-ante “break” bucket for trading. No cost model; no deploy path.

### M22 — Earnings × close (`earnings_close_v1`)

**Idea.** Champion-style close rule on earnings day0 (and broad panel).

**Outcome.** **BETWEEN** both cells; look spent; closed. Mechanism strata echoed M12
but not gated.

### M23 — Sizing shadow (`sizing_shadow_v1`)

**Idea.** Probability-tier × vol-norm allocation vs equal notional — **report-only**
beside the forward clock; ADIA SR/PSR/MinTRL.

**Outcome.** **Measured, report-only.** Large MinTRL (~130 sessions) for adoption claims.
Sizing multiplies; does not create edge.

### M24 — Open auction fade (`open_auction_fade_v1`)

**Idea.** Fade open near-vs-ref dislocation at 09:28:30 into the same-day close print.

**Outcome.** **BETWEEN**; look spent. Near-zero ρ vs close champion → open is an
**independent axis**, but economics not promotion-ready.

### M25 — Calendar overlay

**Idea.** Forward-only boost on month-end / quad-witch for the classical stream.

**Outcome.** **Withdrawn** pre-evaluation with the close-auction freeze.

### M26 — Treasury results 13:02 forward

**Idea.** Sole DR-X9 survivor: forward-only registration around 13:02 auction results.

**Outcome.** **Registered / parked / unbuilt** (side-support priority).

### M27 — Gap-day reversion (`gap_day_reversion_v1`)

**Idea.** Fade large open gaps on lower-ADV semis with open-cross style entry and late exit.

**Outcome.** **FAMILY KILL.** Mid-alpha real-ish (+7–11 bps gross lean) but **taker floor
~2×** the effect. Classic “edge exists, execution class cannot carry it.”

### F1 / F2 / F3 — Prong-0 kills (related)

| ID | Idea | Outcome |
|---|---|---|
| F1 | Displayed depth footprint predicts flow | Killed at prong-0 (ρ gate) |
| F2 | Buyback support as drift payer | Killed at deep-research wave |
| F3 | Opening-auction quantity residue | Killed at prong-0; completes open-axis adjudication with M24 |

---

## Batteries and OOS on the open-cross structure

**Durable structural finding (not a strategy):** entry at the **opening cross** (zero
spread print) and exit in the **15:40–15:45** cheap window → all-in cost often **~1–3 bps**,
vs much higher mid-day taker floors. Later families reuse this **shape** even when signals fail.

### M28 — Open-cross bar battery (`open_cross_battery_v1`)

**Idea.** 14 pre-declared bar signals (prior session + pre-market), wide panel (~176 names),
FDR admission, then optional validate. MOO-style structure.

**Outcome.** **NULL-AT-ADMISSION** — 0/14 at BH-FDR q=0.10. Effects too small to trade even
at face value; breadth was *not* the constraint. Validate deliberately unread.

### M29 — Short-ratio battery (`short_ratio_battery_v1`)

**Idea.** Short interest / short-ratio style signals on the same structure.

**Outcome.** **NULL-AT-ADMISSION** — ICs essentially zero; validate unread.

### M30 — Retail fade daily (`retail_fade_daily_v1` / R2A OOS)

**Idea.** Odd-lot imbalance (OLI) retail-flow fade: discovery on a small panel, then one
pre-committed OOS look on **16 virgin names** after a quote-source bridge (V-NB).

**Outcome.** **NOT-CONFIRMED.** Discovery panel effect did not travel; OOS mid ~flat/negative
with CI spanning zero. Mean cost low (~2.4 bps) — failure is **missing mid-alpha**, not cost
alone. Live instrument stays dark without a CONFIRMED verdict.

---

## Quick index (M-number → status)

| ID | One-line | Status |
|---|---|---|
| M3 | Named-payer continuous plans | Closed (fill truth) |
| M3-A1 | LGBM overlay on M3 | Fail |
| M4 | Event-stream encoder | Fail |
| M5 | Stage A gate on continuous book | Fail |
| M6 / FINAL | Close basis @15:55:10 | Pass + holdout pass → later **frozen/banned** |
| M6b | Open imbalance | Fail |
| M7 | Daily XS reversal | Fail |
| M8 | Meta P(win) gate | Pass (walk-forward) |
| M8-v2 | Mechanism features in meta | Kill |
| M9 | Path features + sizing | Null / no gain |
| M10 | Forward paper clock | Partial; stopped with ban |
| M11 | 28-name OOS breadth | Fail (narrow edge) |
| M12 | LETF vs weight mechanism | LETF wins |
| M13 | Factor residualization | Not adopted |
| M14 | Calendar diagnostic | Diagnostic |
| M15 | Top-3 positioning shadow | Report-only |
| M16 | Phase-0 + flow book | Audit / between |
| M17 | Momentum replications | Research-only |
| M18 | OU reversion system | Fail |
| M20 | Macro window screen | Spent (confirm fail) |
| M21 | Earnings regimes | Diagnostic |
| M22 | Earnings × close | Between |
| M23 | Sizing shadow | Report-only |
| M24 | Open fade | Between |
| M25 | Calendar overlay | Withdrawn |
| M26 | 13:02 Tsy forward | Parked |
| M27 | Gap-day reversion | Kill (cost) |
| M28 | Open-cross bar battery | Null-at-admission |
| M29 | Short-ratio battery | Null-at-admission |
| M30 | Retail fade OOS | Not-confirmed |

---

## Where to go deeper

| Want… | Open… |
|---|---|
| Append-only registry | [`research/ledger.jsonl`](../research/ledger.jsonl) |
| Per-family writeups | [`research/experiments/`](../research/experiments/) |
| Dead vs open solution space | [`research/deep/EXHAUSTION_MAP.md`](../research/deep/EXHAUSTION_MAP.md) |
| Binding rules | [`PROTOCOL.md`](../PROTOCOL.md) |
| Architecture | [`ARCHITECTURE.md`](../ARCHITECTURE.md) |
