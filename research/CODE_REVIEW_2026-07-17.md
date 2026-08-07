# Code Review Report — enginev5.1

**Date:** 2026-07-17  
**Scope:** Full project source under `src/enginev51/`, critical trial apps, tests, and representative experiment outputs.  
**Not in scope:** Research verdicts (OPEN_QUESTIONS / EXHAUSTION_MAP), deep-research agent prose, data lake contents as science.  
**Method:** Two read-only deep passes (fill/auction path; data/protocol/models) + independent re-verification against source and real experiment parquets/reports.  
**Automation:** `uv run pytest` → **414 passed**; `uv run ruff check src tests` → **clean**.

---

## 1. Executive summary

enginev5.1 is a serious research engine: point-in-time discipline, holdout seals, condition-aware fills, and a large automated test suite are real strengths. The residual risk is not “amateur backtester quality.” It is a small set of **high-leverage correctness gaps** that can mislead reports, edge-case PnL, or data-lake ops.

**Top verified finding:** Frame-level stress arms in `backtest/stress.py` treat `spread_cost_bps` / `latency_drag_bps` as non-negative costs, but `decompose.plan_pnl` emits **signed** values (negative = maker earn). On published **M3-A0-v1.1**, the report’s “double_spread” arm **improves** mean net from **+4.345 → +9.331 bps** — the opposite of a stress. An honest re-sim path (`widen_tape`) already exists and appears used for ledger-style spread2x numbers; the **report §4 frame battery remains wrong** for maker-signed books.

**Recommended fix order:** (1) stress frame signs + regression test, (2) replayer full-exit invariant, (3) multi-target same-print handling, (4) incomplete-day backfill refresh, (5) cross-validation metric (`bar_close`) definition, (6) XNAS vs NBBO documentation/comparability.

---

## 2. Project shape (what’s built)

| Layer | Role | Health (high level) |
|-------|------|---------------------|
| `backtest/fills.py` | L1/L2 fill primitives, quote-confirmed limits | Strong; well tested |
| `backtest/replay.py` | Continuous multi-leg plan replayer | Good core; exit bookkeeping gaps |
| `backtest/auction_replay.py` | MOC/basis single-print path | Solid; BBO source caveats |
| `backtest/decompose.py` | PnL identity (signed costs) | Correct as designed |
| `backtest/stress.py` | Frame stress + clustered CIs | **Broken for maker-signed costs** |
| `backtest/tape.py` | Session tape + `widen_tape` | Honest stress path present |
| `data/*` | SIP, NOII, BBO-1s, QA, costs | Strong atomic writes; ops hazards |
| `protocol.py` / seals | Holdout / splits | Strong enforcement culture |
| `apps/run_*` | Trials (M3–M11, meta, paper) | Generally careful; some metrics mislabeled |
| `models/*` | LGBM, meta, encoders | Walk-forward discipline good |
| `tests/` | 414 tests | Green |

Core research lesson encoded in software: continuous-market fills are hard; auction single-print exits are cleaner. Implementation quality matches that ambition better than most research codebases.

---

## 3. What looks solid

These were re-checked and should remain design anchors:

1. **PIT / holdout sealing** — Trial runners and meta paths assert session bounds; holdout is treated as spent for clean validation.
2. **Fill kernel guards** — `prevailing_idx` avoids wrapping future quotes; limit windows are open-after-place; stops decide on quotes and fill after latency (gap-through honest).
3. **v1.4 condition filtering** — Known late/off-market print failure mode is consciously mitigated; quote-confirmation remains for legacy empty conditions.
4. **PnL identity** — `net_bps == gross_mid_bps - latency_drag_bps - spread_cost_bps - fees_bps` with residual audit when mids are finite.
5. **Deterministic latency** — Seeded draws (not unstable `hash()`).
6. **Auction exit modeling** — Exit at official cross / daily-close fallback; zero exit-spread in decomp for single print.
7. **Atomic parquet writes** — tmp + replace pattern on store/NOII/BBO/preds.
8. **Honest maker spread stress exists** — `widen_tape` scales quotes around mid and is documented as the correct maker path (ledger 2026-07-15).
9. **Test and lint baseline** — 414 passed; ruff clean.

---

## 4. Findings (verified)

Severity labels:

- **bug** — incorrect behavior under stated contracts, or numbers that can mislead decisions/reports.
- **suggestion** — real risk or debt; not proven to have flipped a historical gate alone.
- **nit** — clarity, consistency, low-frequency edge.

Each finding notes **verification status**: Confirmed (code + data), Confirmed (code), or Plausible (code only).

---

### F1 — Frame stress arms invert for maker-signed costs  
**Severity:** bug  
**Verification:** Confirmed (code + data)  
**Files:** `src/enginev51/backtest/stress.py` (~24–32, 239–253); `src/enginev51/backtest/decompose.py` (~46, 126–128); consumers: `apps/run_trial.py` §4 via `stress.stress_report`; published `research/experiments/M3-A0-v1.1/report.md` §4–§5.

**Description**

`stress.py` documents cost columns as **non-negative magnitudes** and implements:

```python
net_bps' = net_bps - spread_cost_bps   # double_spread
net_bps' = net_bps - latency_drag_bps  # double_latency
```

`decompose.plan_pnl` documents and emits **signed** `spread_cost_bps` (negative when maker fills earn vs mid). Subtracting a negative **improves** stressed net.

**Evidence (M3-A0-v1.1 taken stream, n=827)**

| Quantity | Value |
|----------|------:|
| mean `net_bps` (base) | +4.345 |
| mean `spread_cost_bps` | **−4.985** |
| mean `latency_drag_bps` | −0.373 |
| frame `double_spread` mean net | **+9.331** |
| frame `double_latency` mean net | +4.718 |

Decomposition block in the same report shows `gross_mid ≈ −0.71` and spread “earn” driving the book — consistent with maker-heavy economics.

**Nuance (do not overclaim)**

- `tape.widen_tape` is the **honest** 2× spread re-sim; ledger-style `spread2x ≈ +4.02` is *worse* than base, as expected.
- Promotion may have used re-sim, not frame arms. The **report §4 battery is still inverted** and remains easy to misread as “survives stress.”

**Impact**

Anyone reading frame stress tables for maker books will conclude robustness that is not there. Taker-heavy auction books are less affected (spread_cost usually positive).

**Recommendation**

1. Fix `double_spread` / `double_latency` to operate on **positive cost magnitudes**, e.g. stress by `max(spread_cost_bps, 0)` only if “extra taker charge” is intended, **or** better: redefine stress inputs as `spread_paid = max(spread_cost, 0)` and `maker_earn = max(-spread_cost, 0)` and document that frame stress cannot reverse maker earn without re-sim.
2. Prefer primary §4 arms from **re-replay** (`widen_tape`, 2× latency draws) for gate reporting.
3. Regression test: on a frame with mean `spread_cost_bps < 0`, assert `double_spread` mean net ≤ base mean net.

---

### F2 — Incomplete exit can still mark plan TAKEN  
**Severity:** bug  
**Verification:** Confirmed (code); frequency not quantified on history  
**File:** `src/enginev51/backtest/replay.py` (~252–323)

**Description**

On stop trigger, if `market_fill` returns `None`, the code comments “use hard end” but **`break`s**. If any target already filled (`exit_fills` non-empty) and `remaining > 0`, the plan is returned as **`STATUS_TAKEN`** with PnL only on partial exit fractions. Leftover size is not mark-to-marketed and not voided.

Same structure if terminal market-out also fails after partial targets.

**Impact**

Optimistic or incomplete bookkeeping on tape-edge / quote-gap paths. Likely rare when RTH quotes are continuous; still a contract violation relative to “taken = fully modeled round-trip.”

**Recommendation**

1. On stop `mk is None`, fall through to hard-end market-out (match the comment).
2. If still incomplete: **void** or force-flat at last mid with an explicit flag.
3. Assert `sum(exit qty_frac) ≈ entry qty_frac` (within ε) before `STATUS_TAKEN`.
4. Unit test: partial target + stop with empty post-stop quotes → not TAKEN with leftover.

---

### F3 — Multi-target same-print underfill  
**Severity:** bug (logic); modest historical impact  
**Verification:** Confirmed (code + synthetic)  
**File:** `src/enginev51/backtest/replay.py` (~238–285); `fills.target_fill_ts` / `_first_print` open bound

**Description**

After a target fills at `f_ts`, `cursor = f_ts`. Later targets search **strictly after** `cursor` (`searchsorted(..., side="right")`). One aggressive through-print that clears multiple target prices fills only the first assigned target; other open targets miss that print.

**Synthetic check**

- Print at ts=2000, price=11.01  
- Long targets at 10.5 and 11.0 both fill at 2000 when armed before 2000  
- After first fill with `cursor=2000`, second target **does not** fill at 2000; waits for a later print

**Historical context**

On M3-A0-v1.1, exit reasons: targets 348, stop 178, curfew 179, hold 115, **mixed 7**. Multi-leg partial paths are uncommon but not zero.

**Recommendation**

On a multi-level through, either:

- allow same-timestamp fills for all resting targets whose limits are cleared by that print, or  
- scan once per print and allocate eligible targets before advancing cursor.

Add a unit test with a single through-print and two targets.

---

### F4 — Incomplete “today” tick partitions can freeze forever  
**Severity:** bug (ops hazard)  
**Verification:** Confirmed (code path); lake not proven currently corrupt  
**Files:** `src/enginev51/data/alpaca_hist.py` (`clamp_end_for_feed`); `src/enginev51/data/backfill.py` (`plan_ticks` / `run_ticks`); config `sip_recency_margin_minutes` (default 20)

**Description**

1. SIP request end is clamped to `now − margin` (~20 minutes).  
2. Tick partitions are marked complete by **file presence**.  
3. Resume skips existing partitions.

A mid-session (or same-day) backfill can write a partial RTH day and never re-fetch the rest of the close — the region detectors and MOC care about most.

**Recommendation**

- Treat the current calendar session (or any day whose stored max(ts) is before official close − ε) as incomplete: always re-fetch / overwrite.  
- Optionally stamp partitions with `complete=true` only when end ≥ session close.  
- Document ops rule: never backfill “today” without `--force` semantics for that day.

---

### F5 — MOC entry BBO is XNAS, not SIP NBBO  
**Severity:** suggestion (docs overclaim + comparability)  
**Verification:** Confirmed (code)  
**File:** `src/enginev51/data/bbo1s.py` (DATASET = `XNAS.ITCH`, SCHEMA = `bbo-1s`); `auction_replay` consumers

**Description**

BBO-1s acquisition is explicitly Nasdaq ITCH top-of-book subsampled at 1s. Purpose comments still speak of “prevailing NBBO.” Continuous SIP fills and XNAS BBO fills are **not the same economic object**.

On Nasdaq-listed megacaps, XNAS is often close to NBBO but not identical; bias direction is not established here.

**Recommendation**

- Rename/document consistently: “XNAS TOB-1s,” not NBBO.  
- Optional: measure XNAS−SIP mid/spread gap on the MOC window in bps and stress economics.  
- Do not pool XNAS-entry nets with SIP-entry nets without an adjustment arm.

---

### F6 — `bar_close` validation metric is last 1m bar, not official daily close  
**Severity:** bug (metric mislabel / false validation)  
**Verification:** Confirmed (code)  
**Files:** `apps/run_basis_trial.py` `_session_closes` (~282–300); report prose in basis/meta/moc apps claiming “official daily close”; exit path uses `_daily_closes` / bars1d in `auction_replay.py`

**Description**

Ground-truth helper used for `bar_close` / `cross_vs_close_bps` is **last 1-minute RTH bar close**, while the cross price often comes from **bars1d official close** (or a conditioned 16:00 print). Report text that expects `cross_vs_close_bps ≈ 0` as confirmation of the cross is checking the wrong reference.

Also: RTH trade fetches are documented as excluding the 16:00 cross print (`auction_replay` comments) — so cross-from-tape is often absent by design; daily close fallback is intentional and correct for **exit price**, but not for the 1m-based validation column.

**Recommendation**

- Set `bar_close` from `_daily_closes` / bars1d for validation columns named “official close.”  
- Keep last-1m as a separate column if useful (`rth_last_1m_close`).  
- Only require cross when the trial exit path needs it (persistence-only cells should not skip solely for missing cross).

---

### F7 — Slot occupancy not released on some post-admission voids  
**Severity:** suggestion  
**Verification:** Confirmed (code reading)  
**File:** `src/enginev51/backtest/replay.py` (~189–200 area)

**Description**

Slot can be reserved at authoring, then chase/entry failure returns VOID without appending occupancy through failure time. Concurrent plans in the same window can over-admit relative to the attention-reservation model.

**Recommendation**

On any post-admission failure, append `_Slot(symbol, acquired, failure_ts)` so occupancy matches the reservation story.

---

### F8 — Condition filtering edge cases  
**Severity:** suggestion  
**Verification:** Confirmed (code)  
**File:** `src/enginev51/backtest/tape.py` (~48–55)

**Description**

- Bad-condition filter uses `str.contains_any` over **single characters** of a code string.  
- Filtering applies only when some non-empty conditions exist that day; empty-condition rows still pass (intentional legacy fallback).

Usually fine for single-letter SIP codes; brittle if packing changes. Mixed partial re-downloads can leave blank conditions on coded days.

**Recommendation**

Parse conditions into a token set; intersect with an explicit bad-code set. Once a symbol-day is “condition-coded,” quarantine empty-condition trades for **fill evidence** (keep raw tape for cross search if needed).

---

### F9 — Static cost hurdles vs realized fill costs  
**Severity:** suggestion  
**Verification:** Confirmed (code)  
**Files:** `data/costs.py`; `apps/run_trial.py` (sample_nbbo=False path)

**Description**

Authoring EV hurdles often use **static fallback spreads**; realized PnL uses tape mid/spread + slip + SEC/TAF. Maker join plans can be charged like full taker RT at authoring. Can keep/kill plans inconsistently with realized economics.

**Recommendation**

Separate “authoring hurdle cost” from “report cost model”; for maker plans use half-spread or expected join cost; optional cached NBBO medians without network at trial start.

---

### F10 — Family-wise testing undercount  
**Severity:** suggestion (protocol/statistics)  
**Verification:** Plausible (code + research process)  
**File:** `protocol.py` `INHERITED_TRIAL_FAMILIES`; many MOC/M8/M9/M3 cells

**Description**

Inherited family counters emphasize older engines. Current work multiplies cells (MOC thresholds, persistence, meta gates, detector variants). Selecting the best reported stream without inflating trial count under-penalizes DSR/PBO.

**Recommendation**

Extend family counters for auction/meta families; headline only pre-registered primary gates; treat secondary gates as diagnostics.

---

### F11 — Config vs protocol dual sources  
**Severity:** suggestion  
**Verification:** Confirmed (code presence of dual definitions)  
**Files:** `protocol.py` hardcoded seals; `config` / `settings.toml` research dates; plan validity `VALID_FOR_S` vs `plan_valid_min_s`

**Description**

Seal/split boundaries and plan-validity knobs exist in more than one place. Only some are enforced. Drift can make config look authoritative while code ignores it.

**Recommendation**

Single source of truth: load splits from toml into protocol at import, or assert equality at startup. Wire plan validity from research config if toml is intended to control it.

---

### F12 — LETF AUM static snapshot  
**Severity:** suggestion  
**Verification:** Confirmed (design)  
**Files:** `config/letf_aum.toml`; `flows/letf.py`; detector uses direction primarily

**Description**

Static AUM applied across history. Direction from return sign is OK; any intensity/sizing that uses AUM dollars is historically wrong (look-ahead of current AUM scale).

**Recommendation**

Keep AUM out of Stage A gates unless point-in-time series is used (aligns with deep-research LETF lane).

---

### F13 — M11 fill kernel ≠ M6-FINAL economics  
**Severity:** suggestion  
**Verification:** Confirmed (code/docs)  
**File:** `apps/run_m11.py`

**Description**

M11 uses a simplified cost model (e.g. fixed adverse bps off ref, daily close exit) vs M6-FINAL bbo-1s + latency + slip. Valid as a **conservative cross-sectional floor**, but nets are not strictly comparable without an adjustment arm.

**Recommendation**

Keep labels explicit; never pool M11 nets with bbo-taker nets for a single CI without a bridge study.

---

### F14 — LGBM early-stopping on train-tail  
**Severity:** suggestion  
**Verification:** Plausible  
**File:** `models/lgbm.py` and MOC/meta train paths

**Description**

Early stopping on the chronological tail of the same fold train set is mild hyperparameter selection into the next regime (not label leakage across embargo, but not pure train-only either).

**Recommendation**

Fixed `num_boost_round` for registered cells, or nested purge (train / early-stop / test) with extra embargo.

---

### F15 — QA coverage holes  
**Severity:** suggestion  
**Verification:** Confirmed (code structure)  
**File:** `data/qa.py`

**Description**

Audits can focus on sessions present in the lake rather than the full requested calendar range, so leading/trailing multi-day holes may look clean.

**Recommendation**

For a requested `[start, end]`, enumerate full trading days and flag every missing partition.

---

### F16 — BPS constant naming  
**Severity:** nit  
**Verification:** Confirmed  
**Files:** `fills.py` (`BPS = 1e-4` slip fraction); `decompose.py` (`BPS = 1e4` scale)

**Recommendation**

Rename (`SLIP_UNIT`, `BPS_SCALE`) or share helpers to prevent copy-paste mistakes.

---

### F17 — Daily bar session dating via UTC timestamp  
**Severity:** nit / suggestion  
**Verification:** Plausible  
**File:** `auction_replay._daily_closes`

**Description**

Session keys from `datetime.fromtimestamp(..., UTC).date()` are correct only if bars1d timestamps are calendar-aligned as assumed. Minute-bar ADV path uses ET date (safer).

**Recommendation**

Key daily bars via ET session date or store explicit `session` at download; unit-test ADV equality minute vs daily on overlapping spans.

---

## 5. Impact matrix

| ID | Affects champion MOC path? | Affects M3 continuous path? | Affects reports? | Affects gates? |
|----|----------------------------|-----------------------------|------------------|----------------|
| F1 frame stress | Low (taker costs usually +) | **High** | **High** | Medium (if someone uses §4 frame arms) |
| F2 incomplete exit | Low | Medium (rare) | Low | Low |
| F3 multi-target | N/A (single exit) | Medium if multi-target books return | Low | Low–med |
| F4 partial day freeze | High if lake incomplete near close | High | Indirect | Indirect |
| F5 XNAS BBO | Medium (entry book) | N/A | Medium | Medium for absolute bps |
| F6 bar_close metric | Validation only | N/A | Medium | Low |
| F10 multi-testing | Process | Process | High | High for “significance” claims |

---

## 6. Recommended work plan

### P0 — fix before trusting maker stress tables again

1. Repair `stress.double_spread` / `double_latency` semantics + regression test using M3-style negative mean spread.  
2. Optionally stop printing frame arms as primary §4 when `mean(spread_cost) < 0`; require re-sim arms instead.

### P1 — replayer invariants

3. Full-exit or void (F2).  
4. Same-print multi-target (F3).  
5. Slot release on void (F7).

### P2 — data integrity

6. Incomplete-day refresh (F4).  
7. Official-close validation column (F6).  
8. Condition empty-row quarantine on coded days (F8).

### P3 — honesty / comparability

9. XNAS vs NBBO documentation and optional basis study (F5).  
10. Family counters + registered-gate discipline (F10).  
11. Config/protocol single source (F11).

### P4 — polish

12. BPS naming, QA calendar holes, LGBM ES policy, LETF AUM PIT if used for intensity.

---

## 7. Suggested regression tests (concrete)

| Test | Assert |
|------|--------|
| `test_stress_maker_earn_does_not_improve` | Frame with `spread_cost_bps = -5`, `net=4` → after `double_spread`, net ≤ 4 |
| `test_replay_partial_exit_not_taken` | Stop after partial target with no quotes → not TAKEN with leftover, or force-flat |
| `test_multi_target_same_print` | Single through-print clears both targets at that ts |
| `test_backfill_today_incomplete` | Partial max(ts) day is re-planned / not skippable without complete stamp |
| `test_cross_vs_official_close` | `bar_close` from bars1d matches `cross_px` when exit used daily-close fallback |

---

## 8. What this review does *not* claim

- It does **not** claim the champion Nasdaq basis edge is invalid.  
- It does **not** claim M3 promotion used the broken frame stress (ledger spread2x numbers look like honest re-sim).  
- It does **not** re-open research map verdicts or write the ledger.  
- It does **not** audit every experiment report line-by-line; M3-A0-v1.1 was the smoking-gun stress case.

---

## 9. Bottom line

| Layer | Assessment |
|-------|------------|
| Fill primitives | Careful and well tested |
| Auction / basis path | Usable; document XNAS vs NBBO; fix close-validation metric |
| Continuous multi-leg replay | Partial-exit + multi-target logic holes |
| Frame stress battery | **Inverted for maker-signed costs — do not trust §4 for maker books** |
| Honest stress re-sim | Exists (`widen_tape`) and should be the gate path |
| Data lake ops | Incomplete-day freeze is a real silent hazard |
| Protocol / research hygiene | Strong culture; multiple-testing bookkeeping lags cell count |
| Test baseline | 414 green, ruff clean |

**One sentence:** The engine is research-grade and mostly careful, but **report-level maker stress is currently lying in a measurable way**, and a few replayer/data-ops edge cases should be closed before the next promotion-sensitive continuous or stress-gated campaign.

---

## 10. Appendix — verification commands used

```text
uv run pytest -q --tb=line          # 414 passed
uv run ruff check src tests         # clean

# Stress sign on real results
# M3-A0-v1.1: mean net 4.345, mean spread_cost -4.985,
# frame double_spread mean net 9.331

# Multi-target synthetic via fills.target_fill_ts
# print 11.01 @ t=2000 clears 10.5 and 11.0 from open<2000;
# after cursor=2000 second target misses that print
```

---

*End of report. No ledger writes; no map updates; no code changes applied.*
