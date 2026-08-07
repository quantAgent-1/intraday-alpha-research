# Code Review Report — enginev5.1 (full project)

**Date:** 2026-07-28  
**Scope:** Full project under `src/enginev51/` (~120 modules), critical apps, research screens, scripts samples, `config/`, tests. Not in scope as science: deep-research prose, data lake contents, experiment *verdicts*.  
**Method:** Four parallel read-only deep passes (backtest; protocol/data; live/apps; models/features/screens) + orchestrator re-verification of high-severity claims against source + automation.  
**Baseline:** Prior review `research/CODE_REVIEW_2026-07-17.md` (F1–F17).  
**Automation:** `uv run pytest` → **749 passed** in ~46s; `uv run ruff check src tests` → **7 style findings** (all auto-fixable `I`/`UP017`, not correctness).

---

## 1. Executive summary

enginev5.1 remains a serious research engine: holdout seals, causal fills, signal-only live path, algebraic PnL identity, and a large green test suite are real strengths. The 2026-07-17 P1 harness bugs (F1–F3, F7) and F4/F6 are **fixed** in code with regression tests. Residual risk is not “amateur backtester quality.” It is a smaller set of **high-leverage correctness / ops / protocol gaps** that can still mislead reports, leak ~60s of feature look-ahead into the encoder path, freeze bad partitions, or print a ticket the meta gate should have blocked.

**Dominant risk areas today**

| Area | Risk |
|------|------|
| Encoder static features | Pre-F2 asof on bar-close features at decision open (~60s look-ahead) |
| Live cockpit ticket | Meta NO-GO does not block `ticket_ok` / ORDER TICKET when model loaded |
| Data completeness | Presence-is-complete + no primary overwrite; NOII/BBO end-day by max(ts) date |
| Continuous fills | Already-through stop waits for *later* quote; condition-code filter still brittle |
| Protocol hygiene | Bare `assert` holdout guards (stripped under `-O`); family counts under-updated; dual constants |

**Recommended fix order:** (1) encoder static F2 lag, (2) cockpit meta gates ticket, (3) stop already-through semantics + test, (4) primary overwrite / content completeness, (5) `SealViolation` not bare assert, (6) condition tokens, (7) constant single-sourcing.

---

## 2. Project shape

| Layer | Role | Health |
|-------|------|--------|
| `backtest/fills.py` | L1/L2 fill primitives | Strong; stop arm edge open |
| `backtest/replay.py` | Continuous multi-leg replayer | Good post v1.5–v1.6 |
| `backtest/auction_replay.py` | MOC single-print path | Solid; path/key footguns |
| `backtest/decompose.py` | PnL identity (signed costs) | Correct as designed |
| `backtest/stress.py` | Frame stress + CIs | F1 fixed; maker gate weak |
| `data/*` | Lake, NOII, BBO, QA, costs | Strong atomic writes; ops hazards |
| `protocol.py` | Splits, seal, ledger | Strong culture; assert footguns elsewhere |
| `live/*` + cockpit | Signal-only decide path | Clean routing; ticket/meta bug |
| `models/*` | LGBM, meta, encoders | Walk-forward good; encoder static lag |
| `research_screens/*` | M20–M27 harnesses | Careful but large + copy-paste |
| `tests/` | 63 files, **749** tests | Green |

**Alive pipeline (champion):** NOII + BBO-1s → `run_basis_trial` → `auction_replay` → optional M8 meta → `forward_paper` / `live_cockpit`.  
**Historical pipeline:** detectors → plans → continuous `replay` — family closed; machinery retained.

---

## 3. Prior findings (2026-07-17) — status

| ID | Topic | Status 2026-07-28 |
|----|--------|-------------------|
| **F1** | Frame stress inverts maker-signed costs | **Fixed** — `.clip(lower_bound=0)`; residual: arm is near-no-op on maker books |
| **F2** | Incomplete exit can mark TAKEN | **Fixed** — remaining → VOID; stop fail → hard-end |
| **F3** | Multi-target same-print underfill | **Fixed** + regression test |
| **F4** | Incomplete “today” tick partitions freeze | **Fixed** forward (`_fetch_window_final`); heal/overwrite still weak |
| **F5** | BBO is XNAS not NBBO | **Documented** + dual-source QA; pooling enforcement soft |
| **F6** | `bar_close` = last 1m not official close | **Fixed** — prefers bars1d official close |
| **F7** | Slot not held on post-admission voids | **Fixed** (v1.5 + v1.6) |
| **F8** | Condition filtering edge cases | **Open** |
| **F9** | Static authoring costs vs tape | Still applicable outside champion path |
| **F10** | Family-wise trial undercount | **Open** |
| **F11** | Config vs protocol dual sources | **Partial** — split dates asserted; capital/plan knobs still dual |
| SIM F1 | `adjustment="all"` default | Mitigated for primary signal bars; API default still dangerous |

---

## 4. What looks solid

1. **Signal-only hard rule** — no `submit_order` / trading client in production code; live + cockpit tests deny broker/network tokens.  
2. **PnL identity** — `net = gross_mid − latency_drag − spread_cost − fees` with residual audit.  
3. **PIT fill windows** — strict-after open, inclusive close; prevailing quote never wraps future.  
4. **Deterministic latency** — sha256 seed, not process-salted `hash()`.  
5. **Holdout culture** — `apply_seal` + token + ledger note; many paths refuse holdout end dates.  
6. **Atomic parquet** — store / NOII / BBO / live journal use tmp + `os.replace`.  
7. **Auction economics spine** — exit at cross / daily-close fallback; zero exit spread in decomp.  
8. **Kernel identity** — live/forward share decision functions by identity tests.  
9. **F2 lag on A1/M4 pred consumers** — overlays use `PRED_STAMP_TO_AVAILABILITY_NS`.  
10. **TCN causality** — left-pad / right-trim; PatchTST on past-only window.  
11. **Best research-screen template** — M20/M21 route assembly through `apply_seal` + outcome containment.  
12. **Test baseline** — 749 passed; prior P1 harness bugs pinned by regression tests.

---

## 5. Findings (verified)

Severity: **bug** (incorrect under stated contract / decision risk) · **suggestion** (real debt) · **nit** (low-frequency / clarity).

---

### B1 — Encoder static features omit F2 availability lag  
**Severity:** bug  
**Verification:** Confirmed (code)  
**Files:** `models/encoder/dataset.py:650-657`; contrast `plans/overlay_a1.py` / `overlay_m4.py`; contract `features/grid.py` (`PRED_STAMP_TO_AVAILABILITY_NS`)

**Description**

`_static_vector` does asof `ts <= decision` with no one-bar lag. Materialized slow features are stamped at bar **open** but contain that bar’s **close**. At a decision on the bar open, the encoder can consume features only knowable ~60s later. Fine stream correctly ends at completed seconds (`e = offset - 1`); overlays lag correctly; static `f_*` channels do not.

**Impact**

Up to ~60s look-ahead in the 37 static feature channels for M4 / encoder arms. Not on the champion MOC-basis path, but any encoder-dependent economics or reopening is contaminated.

**Suggestion**

```python
avail_ts = ts - PRED_STAMP_TO_AVAILABILITY_NS
k = int(np.searchsorted(feat_ts, avail_ts, side="right")) - 1
```

Add a unit test: truncating the current minute’s bars must not change static features at the open stamp.

---

### B2 — Cockpit ORDER TICKET ignores meta NO-GO when model loaded  
**Severity:** bug  
**Verification:** Confirmed (code + module contract)  
**File:** `apps/live_cockpit.py:397-424` (header L15–17, checklist L730)

**Description**

Module header and checklist require, when M8 is loaded: `P(win) >= 0.55` in addition to classical `|basis| >= 10`. `decide_one` sets `ticket_ok` from classical GO + spread abort + whole-share sizing only. Meta is displayed but **never** sets `ticket_block`. Human can key a meta-rejected clip from a full ORDER TICKET.

**Suggestion**

When `meta["available"]`, require `meta["go"]` for `ticket_ok` (or explicit stream selector: classical-only vs champion-meta). Add regression test: model loaded + meta NO-GO ⇒ no ORDER TICKET.

---

### B3 — Already-through stop can miss until hard_end  
**Severity:** bug  
**Verification:** Confirmed (code)  
**Files:** `backtest/fills.py:181-205` (`stop_trigger_ts`); `backtest/replay.py` stop arm call

**Description**

Stop search opens **strictly after** `from_ts` (arm). If the book is already through the stop at the arm instant (gap entry / immediate breach), the trigger waits for a *later* quote update. Sparse quotes can ride to hold/curfew — optimistic vs a human who would market out once armed and through.

**Suggestion**

Level-check the prevailing quote at `stop_arm`; treat already-through as decision at arm (then apply stop latency). Unit test: entry mid already through stop, single quote, no later quotes → stop/hard-end, not full hold.

---

### B4 — Primary tick partitions cannot be force-overwritten  
**Severity:** bug (ops)  
**Verification:** Confirmed (code)  
**Files:** `data/backfill.py:94-123`; CLI notes primary still skips under force

**Description**

Presence still means complete. `force=True` only re-fetches when the **primary** file is absent. Truncated, empty, or corrupt primary days are skipped forever and can shadow good legacy data under dual-root primary-first reads. F4 fixed *forward* incomplete-today planning; the heal path is incomplete.

**Suggestion**

Content completeness (max(ts) near RTH close − ε) + `--force-overwrite` that rewrites primary. Document: delete primary path to heal today.

---

### B5 — Zero-row partition is a permanent completeness marker  
**Severity:** bug (ops)  
**Verification:** Confirmed (code)  
**Files:** `data/store.py` empty writes; `backfill.py` module contract

**Description**

Empty partitions are intentional for holidays/unlisted, but under dual-lake primary-first, an accidental empty primary permanently holes a liquid name-day.

**Suggestion**

Treat zero-row primary on an RTH liquid session as incomplete unless an explicit empty_ok sidecar exists.

---

### B6 — NOII/BBO end-month skip uses calendar date of max(ts)  
**Severity:** bug (ops residual)  
**Verification:** Confirmed (code)  
**Files:** `data/noii.py` / `bbo1s.py` end-month coverage; condition-guard fail-open

**Description**

Any rows on `end_d` (even pre-close) satisfy “covered.” Fail-open on metadata exceptions still proceeds. NOII cares about 15:45–16:00 ET — early-day rows can lock a partial month.

**Suggestion**

Require `max(ts) >= session_close − ε` (or NOII ≥ 15:55 ET) before skip-exists; on metadata fail-open, prefer leave incomplete.

---

### B7 — Holdout guards as bare `assert` (stripped under `-O`)  
**Severity:** bug (latent)  
**Verification:** Confirmed (code pattern)  
**Files:** e.g. `research_screens/open_fade.py:124-133`, `gap_day.py:128-136`, `run_basis_trial.assert_before_holdout`, `moc_meta.py`, many apps

**Description**

`protocol.apply_seal` correctly raises `SealViolation`. Many assembly paths only `assert end < HOLDOUT_START`. Under `python -O` / `PYTHONOPTIMIZE=1`, asserts are compiled out.

**Suggestion**

Replace with `raise SealViolation(...)` or always route through `apply_seal`. Keep asserts for test-only internals.

---

### B8 — Local strip_holdout bypasses protocol choke point  
**Severity:** suggestion (protocol)  
**Files:** `research_screens/sizing_shadow.py` and similar; contrast M20/M21 `apply_seal`

**Description**

Protocol requires research assembly through `apply_seal` (split drift check + unseal ceremony). Local filters only strip a column.

**Suggestion**

Route all research frames through `apply_seal`; keep `assert_before_holdout` as CLI UX only.

---

### S1 — F8 condition filtering still brittle  
**Severity:** suggestion  
**File:** `backtest/tape.py:48-55`

Character-wise `contains_any` on a code string; empty conditions still pass on coded days. Parse token sets; quarantine empty conditions on coded symbol-days for fill evidence.

---

### S2 — Frame `double_spread` is a no-op on maker books  
**Severity:** suggestion  
**File:** `backtest/stress.py:247-278`

F1 inversion fixed; for mean `spread_cost < 0` the arm barely moves. Prefer `widen_tape` re-sim for §4 maker gates; report frame arm as n/a when mean spread signed earn.

---

### S3 — Limit entry mid_at_action at placement, not fill  
**Severity:** suggestion  
**File:** `backtest/replay.py` limit entry fill construction

Net prices correct; spread/gross attribution mis-books adverse selection for resting makers. Set mid at fill or document a separate fill-wait component.

---

### S4 — Stale quote / no max age on market_fill  
**Severity:** suggestion  
**File:** `backtest/fills.py:158-178`

Prevailing quote is last `ts ≤ exec` with no max age. Optional `max_quote_age_ns` → void or policy.

---

### S5 — Meta gate and deploy capital triplicated  
**Severity:** suggestion  
**Files:** `forward_paper.META_GATE_Q=0.55`; `positioning` / `sizing_shadow` / `live_cockpit` `$1000`

Promote single `HEADLINE_META_GATE` in `moc_meta` and one deploy constant module; import everywhere.

---

### S6 — Forward ledger non-atomic write  
**Severity:** suggestion  
**File:** `apps/forward_paper.py` `append_ledger`

Live journal is atomic; forward ledger uses in-place `write_parquet`. Crash can corrupt the production validation clock.

---

### S7 — Replay journal vs cockpit size price basis  
**Severity:** suggestion  
**Files:** `live/engine.py` uses `entry_px`; cockpit uses bid/ask

Deploy share counts can disagree for the same session. Align on bid/ask sizing rule.

---

### S8 — `fetch_bars_multi` default still `adjustment="all"`  
**Severity:** suggestion  
**File:** `data/alpaca_hist.py`

SIM_AUDIT F1 class. Flip default to `raw`; require explicit `"all"` for total-return studies.

---

### S9 — Family trial undercount (F10)  
**Severity:** suggestion  
**File:** `protocol.INHERITED_TRIAL_FAMILIES`

Still only pre-v5.1 families. Maintain protocol-owned in-house cell counts for DSR/PBO.

---

### S10 — Dual protocol knobs outside splits (F11 residual)  
**Severity:** suggestion  

Capital/deploy and plan-validity live in toml and code without equality asserts. Extend `assert_splits_consistent` → full protocol/config consistency.

---

### S11 — Hardcoded absolute Windows paths  
**Severity:** suggestion  
**File:** `config.py:26-58`

hardcoded machine-local credentials / lake paths. Prefer env/relative; breaks clones.

---

### S12 — Unseal “ONE_SHOT” is social  
**Severity:** suggestion  
**File:** `protocol.py`

Token in-repo; ledger notes but does not refuse second unseal. Fine if ops are disciplined; name overclaims.

---

### S13 — MONTH_END / walk-forward fold helpers diverge  
**Severity:** suggestion  

Reversion/M8-v2 vs M25 calendar definitions differ; two fold builders (`cv` session blocks vs `moc_gbm` calendar months). Shared helpers + loud names.

---

### S14 — Giant research_screen modules + fee constant copy  
**Severity:** suggestion  

800+ LOC screens mix loaders/stats/CLI; SEC/TAF and seal helpers duplicated. Extract `_seal` / `_ci` / `_paths`.

---

### S15 — MOC API lacks entry-before-exit guard  
**Severity:** suggestion  
**File:** `auction_replay.replay_moc_event`

Can book ok with negative hold if signal near cross. Production 15:50/15:55 callers safe; public API unconstrained.

---

### S16 — bars1d / feed path hardcoding  
**Severity:** suggestion  
**File:** `auction_replay` ADV/`_daily_closes`; `tape.load_session_tape` feed `"sip"`

Ignore `Settings.read_roots` / `data_feed_type` in places. Resolve via shared store loaders.

---

### N1–N4 (nits)

- `TargetSpec.frac` not validated in `(0,1]`.  
- `session_summary` AttributeError if `pnl is None` (voids).  
- Dead terminal `market_fill` fallback when latency ≥ 0.  
- `exit_reason` `"targets"` vs docs `"target"`.  
- Ruff: 7 auto-fixable import/UTC-alias findings.  
- Encoder train docstring float16 vs bfloat16.

---

## 6. Architecture strengths (preserve)

- Single economics spine: continuous + MOC both emit `Fill` → `plan_pnl`.  
- Causal k-slot attention model matches manual 5–25s thesis.  
- Auction path deliberately separate (curfew-exempt, single clearing price).  
- Research vs small-account lenss separated; deploy metrics must not gate Stage A.  
- Documented debt (XNAS≠NBBO, maker frame-stress caveat) better than hidden debt.  
- Adversarial harness reviews for M22–M27 show process maturity.

---

## 7. Severity rollup

| Severity | Count (this review) | Top items |
|----------|--------------------:|-----------|
| bug | 7 | B1 encoder F2, B2 cockpit meta, B3 stop through, B4–B6 data completeness, B7 assert seals |
| suggestion | 16 | F8, maker stress, constants, atomic ledger, F10/F11, paths, folds, screens |
| nit | ~6 | frac validation, docs, ruff |

**Gate impact**

- **Champion MOC path:** largely insulated from B1/B3 continuous issues; still depends on NOII/BBO completeness (B6), ticket UX (B2), forward ledger integrity (S6), XNAS entry book honesty (F5 residual).  
- **Continuous / encoder / reopening:** B1 and B3 are material before any economics trust.  
- **Ops / lake:** B4–B6 can silently poison any path that trusts presence-as-complete.

---

## 8. Recommended fix order

1. **P0** — B1 encoder static F2 lag + test.  
2. **P0** — B2 cockpit meta gates `ticket_ok` + test.  
3. **P0** — B3 already-through stop + test.  
4. **P1** — B4–B6 completeness / overwrite / max(ts) window.  
5. **P1** — B7 `SealViolation` instead of bare assert; route assembly via `apply_seal`.  
6. **P1** — S1 condition tokens; S5 single-source constants; S6 atomic forward ledger.  
7. **P2** — S2–S4 fill/stress attribution; S8 bars default; S9–S10 protocol counts; S11 paths; screen extraction.

---

## 9. Automation snapshot

```
uv run pytest -q   →  749 passed in 46.23s
uv run ruff check src tests  →  7 errors (all [*] fixable style)
```

---

## 10. Artifacts from this review pass

| Artifact | Path |
|----------|------|
| This report | `research/CODE_REVIEW_2026-07-28.md` |
| Backtest pass | `%TEMP%/grok-researcher/grok-review-backtest-6ad2f35d.md` |
| Data/protocol pass | `%TEMP%/grok-researcher/grok-review-data-6ad2f35d.md` |
| Live/apps pass | `%TEMP%/grok-researcher/grok-review-live-6ad2f35d.md` |
| Models/screens pass | `%TEMP%/grok-researcher/grok-review-models-6ad2f35d.md` |
| Prior review | `research/CODE_REVIEW_2026-07-17.md` |

---

*End of full project review.*
