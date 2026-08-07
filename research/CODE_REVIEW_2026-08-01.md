# Code Quality Report — enginev5.1 (full codebase)

**Date:** 2026-08-01  
**Audience:** A stronger thinking / refactor agent. This is **not** a science review and not a rubber-stamp of working code.  
**Scope:** Entire `src/enginev51/`, representative `scripts/`, `tests/`, config, and layer boundaries. Experiment *verdicts* and deep-research prose are out of scope.  
**Method:** Structural audit (LOC, ownership, duplication, choke points, layer inversion) + re-verification of open items from `research/CODE_REVIEW_2026-07-28.md`.  
**Prior baselines:** `CODE_REVIEW_2026-07-17.md` (F1–F17), `CODE_REVIEW_2026-07-28.md` (B1–B7, S1–S16).

---

## 0. How to use this document

Prefer **fewer, larger moves** over nits. The codebase is mature on protocol culture and fill correctness; residual risk is:

1. **Architectural gravity** — apps/scripts grew into the real library; the library never reclaimed ownership.
2. **Duplication that drifts** — holdout guards, CIs, fees, gates, daily closes, markdown report shells.
3. **Open correctness items** from 2026-07-28 that can still lie in reports or tickets.
4. **Dead-weight surface area** — closed families still ship full apps + tests at ~champion size.

If you only act on five things, do **§2 code-judo moves J1–J5**. Correctness P0s from the prior review remain blocking for any path that touches them (B1 encoder lag, B2 cockpit meta, B3 stop already-through).

---

## 1. Executive shape

| Slice | LOC (approx) | Files | Role |
|-------|-------------:|------:|------|
| `apps/` | **10.8k** | 31 | CLI + most “business” assembly |
| `research_screens/` | **5.7k** | 9 | One-shot registered screens (often 800–930 lines) |
| `models/` | 3.6k | 16 | LGBM / meta / encoder / sizing |
| `data/` | 2.4k | 9 | Lake, NOII, BBO, QA, costs |
| `flows/` | 1.8k | 7 | LETF / GEX / macro / ffcal |
| `reversion/` | 1.7k | 8 | Closed / side family |
| `backtest/` | 1.5k | 8 | Economics spine (best layer) |
| `events/` | 1.3k | 10 | Detectors + context (mostly historical) |
| root (`protocol`, `config`, `positioning`, `contracts`) | ~0.5k | 4 | Thin choke points |
| **src total** | **~28–30k** | ~120 py | |
| `scripts/` | large | 46 | Second, parallel codebase |
| `tests/` | large | 60+ | Green culture; hermetic screens |

**Champion-path rough LOC ~7.2k** (basis trial, auction replay, NOII/BBO, forward, cockpit, live, meta).  
**Dormant continuous/encoder/reversion/detectors rough LOC ~8.3k** — larger than the alive path.

`apps/` alone is ~40% of package LOC. That is the central structural fact.

---

## 2. Code-judo moves (highest leverage)

These delete categories of complexity rather than polishing them.

### J1 — Invert the layer: apps must not be the library

**Problem.** Production and research kernels live under `apps/` and are imported *upward* into models, live, and research_screens:

| Consumer | Imports from `apps` |
|----------|---------------------|
| `models/evolution_features.py` | `run_basis_trial.near_at`, `direction_of` |
| `live/engine.py` | `forward_paper.*`, `live_cockpit.decide_one` |
| `research_screens/earnings_close.py` | `run_m11`, `run_basis_trial` |
| `research_screens/open_fade.py` | `run_m11.SEC_TAF_SELL_BPS` |
| `research_screens/sizing_shadow.py` | `forward_paper.load_ledger` |
| `apps/run_m11.py` | `run_basis_trial.basis_*` |

Design intent for live (“import by identity”) is good; **placement** is wrong. Library modules depend on Click apps.

**Move.** Carve a pure package, e.g. `enginev51/moc/` or `enginev51/signals/champion/`:

- `basis.py` — `basis_bps_of`, `near_at`, `direction_of`, `basis_pit_features`
- `decision.py` — `decide_one`, `classify_basis`, sizing helpers (today in `live_cockpit`)
- `forward.py` — `compute_session_events`, `score_events`, ledger I/O
- Thin `apps/*` become click wrappers only

**Payoff.** Live, models, screens, and tests import a stable core. Apps stop being load-bearing. Identity tests still work.

---

### J2 — One holdout choke point; delete nine `assert_before_holdout` clones

**Problem.** Protocol claims: *every research assembly goes through `apply_seal`*. Reality is a patchwork:

- Proper: `apply_seal` (sched_window, earnings_regime, daily_swing)
- Bare `assert end < HOLDOUT_START` **copied 9×** (basis, moc, open, trial, m11, xs, open_fade, gap_day, sizing_shadow) — **stripped under `python -O`**
- Local `strip_holdout` in `sizing_shadow` (filter only; **no** split-drift check, **no** unseal ceremony)
- Session list filter `d < HOLDOUT_START` without sealing the event frame
- Reversion correctly raises `SealViolation` on bar ts — good outlier

**Move.**

```python
# protocol.py (canonical)
def refuse_end_on_or_after_holdout(end: date) -> None:
    if end >= HOLDOUT_START:
        raise SealViolation(...)

def apply_seal(df, *, unseal=False) -> pl.DataFrame:  # already exists; only path
    ...
```

Delete every local `assert_before_holdout` / `strip_holdout`. Route every frame with a `session` column through `apply_seal`. CLI date guards call `refuse_end_*` (raise, never assert).

**Payoff.** One mental model; `-O` cannot disable protocol; F11-style dual sources stay checked at the choke point.

---

### J3 — Single stats + costs facade; kill 14× `_ci` and fee scatter

**Problem.**

- **~14 local `_ci` wrappers** around the same `stress.clustered_mean_ci` call shape (mean/lo/hi/n/n_sessions).
- **Fee constants triplicated:** `sec_taf_sell_bps=0.3` hardcoded in auction_replay defaults, replay defaults, run_m11, open_fade, xs_reversal, gap_day `FEES_RT_BPS=0.25`, sched_window `FEES_BPS_RT=0.25`, while `ResearchConfig.sec_taf_sell_bps` and `data/costs.py` already exist.
- **Meta gate 0.55** redeclared in forward_paper, live_cockpit, run_m11, m8v2, run_m9, sizing, moc_meta.GATES, reversion.meta, sizing_shadow.
- **Deploy $1000** in positioning, live_cockpit, sizing_shadow, live/engine.

`stress.clustered_mean_ci` is already the right primitive. Screens still re-wrap it for report shape; some screens import `cluster_ci` from *sched_window* (M20 ownership of a generic statistic).

**Move.**

- `enginev51.stats.report_ci(df, value_col, cluster_col) -> ReportCI` — one place for the 5-tuple + empty handling.
- `enginev51.costs.constants` (or extend ResearchConfig + `assert_protocol_consistent`) for SEC/TAF, slip, meta gate, deploy capital, research notional.
- ADIA helpers (`psr`, `min_trl`, `sr_native`) leave `sizing_shadow` → `stats/adia.py` so M24/M27 do not import a research screen for pure math.

**Payoff.** Drift stops being a test-pinning industry (`test 7 asserts local == M11 == 0.3`).

---

### J4 — Research-screen template instead of 800–930 line monoliths

**Problem.** Pattern repeated across M20–M27:

1. Frozen registration constants  
2. Lake loaders (BBO / NOII / bars1d)  
3. Event assembly + seal  
4. Cell stats + stress CI  
5. Markdown + parquet + ledger  
6. `__all__` export surface for tests  

Largest offenders: `sched_window.py` (929), `earnings_regime.py` (893), `gap_day.py` (821), `open_fade.py` (790), `sizing_shadow.py` (576), plus apps that only orchestrate them.

Also: **three economics dialects**

| Dialect | Used by | Kernel |
|---------|---------|--------|
| Continuous `TradePlan` + `replay` | historical detectors / run_trial | fills.py |
| MOC `replay_moc_event` | champion basis / m11 | auction_replay |
| Hand-rolled net_bps | open_fade, gap_day, xs_reversal, … | local arithmetic |

Hand-rolled paths re-express slip/fees and risk double-count or mismatch with COST_MODEL.

**Move.** A frozen `ScreenSpec` + pipeline:

```text
load(injectable) → assemble → apply_seal → cell_stats → write_artifacts
```

Shared: early-close list (one module), raw bars1d loader, BBO session loader, report skeleton.  
**Screens own only:** universe, signal function, gate thresholds, PASS bar.  
Prefer calling `replay_moc_event` / fill primitives for any taker RT rather than local `gross - FEES`.

**Payoff.** Next family is ~150 lines of pure policy, not another 850-line clone. File-size rule (<1k) stops being a near-miss every time.

---

### J5 — Archive closed families; shrink the default cognitive graph

**Problem.** Design says almost everything is dead; the package still ships full continuous replay, five detectors, encoder (TCN/TST), reversion stack, train_a1, run_trial, run_open_trial, run_moc_trial, daily_swing, empty `dashboard/`. Dormant LOC ≈ champion LOC. New agents cannot see the spine.

**Move (behavioral-preserving archive, not delete-from-git):**

- `src/enginev51/_archive/` or `research/graveyard/code/` with frozen imports  
- Or keep packages but **remove from default package docs / ORIENTATION “alive map”** and gate tests into `tests/archive/`  
- Document one **alive import graph**: NOII+BBO → basis kernel → auction_replay → meta → forward/live

**Payoff.** Thinking agent starts from 7k LOC of truth, not 28k of history.

---

## 3. Structural findings (ordered by severity)

### S-A — Library logic lives in Click apps (layer inversion)

See **J1**. This is the largest maintainability regression relative to the *stated* architecture (contracts + backtest + data as spine). Live deliberately imports apps; models do too for `near_at`. That freezes accidental placement.

**Remediation priority:** P0 for any work on champion live path or M8 feature evolution.

---

### S-B — Protocol seal is social, not structural

See **J2** and prior **B7/B8**. Multiple parallel “seals” teach agents that any filter is fine. `apply_seal` also requires a `session` column — assemblies that never build that column cannot use it and invent date filters instead.

**Ambition check:** extend `apply_seal` (or `seal_sessions(list[date])`) so every entry style shares one implementation.

---

### S-C — Constant dual-sourcing (protocol / toml / magic numbers)

Prior F11 / S5 / S10 still open and worse in practice:

| Constant | Canonical aspirant | Actual homes |
|----------|-------------------|--------------|
| Split dates | `protocol.py` | + `settings.toml` (checked once) |
| Deploy capital | `ResearchConfig.deploy_equity_usd` | + positioning, cockpit, sizing_shadow |
| Meta gate 0.55 | should be `moc_meta.HEADLINE_GATE` | ≥6 modules |
| SEC/TAF 0.3 | `ResearchConfig.sec_taf_sell_bps` | hardcoded defaults in backtest + apps |
| Slip 0.5 | costs config | hardcoded in trial runners |

**Move:** `assert_protocol_consistent()` expands beyond splits to capital + costs; production code **reads** ResearchConfig / single module only.

---

### S-D — Giant files at the health boundary

| File | Lines | Issue |
|------|------:|-------|
| `scripts/r2a_prong0.py` | **1099** | Crosses 1k; one-off science script as monolith |
| `research_screens/sched_window.py` | 929 | Atlas + loaders + floors + CI |
| `apps/phase0_blotter.py` | 927 | Ops + accounting + UI-ish |
| `scripts/f3_prong0.py` | 907 | Same family as r2a |
| `research_screens/earnings_regime.py` | 893 | |
| `flows/ffcal.py` | 878 | Vendored calendar; intentional bulk |
| `apps/run_basis_trial.py` | 873 | **Champion kernel + CLI + report** — extract kernel |
| `research_screens/gap_day.py` / `open_fade.py` | 821 / 790 | |
| `apps/live_cockpit.py` | 749 | Decision kernel + render + CLI |
| `data/qa.py` | 752 | |

Rule of thumb: **do not grow these further**. Decompose before adding cells.

`run_basis_trial` is the highest-value split: pure event builder vs markdown vs click.

---

### S-E — Duplicated data helpers

`_load_daily_closes` / official close merge appears in:

- `run_basis_trial`
- `models/moc_gbm`
- `models/m8v2_features`
- plus `auction_replay.official_daily_closes` / `adv20_dollars`

BBO/NOII session loaders reimplemented in screens (`load_bbo_for_session` in sched_window **and** gap_day) instead of always using `data.bbo1s` / `data.noii`.

**Move:** `data/daily_bars.py` (raw closes, official closes, ADV20) as the only import.

---

### S-F — Typed contracts stop at the tape

`contracts.py` has Bar / TradeTick / QuoteTick / DetectorState.  
`plans/schema.py` has TradePlan (good validation).  

Champion path mostly speaks **ad-hoc polars frames and dicts** (`decide_one` → dict, event frames with implicit columns). That forces every consumer to re-learn column names and optional None fields.

**Move (ambitious but high ROI for the champion only):** frozen `MocEvent`, `BasisDecision`, `MetaVerdict` dataclasses (slots) as the cross-layer language. Polars at I/O boundaries only.

Do **not** invent a generic schema framework for dead families.

---

### S-G — Scripts are a second engine

46 scripts under `scripts/` (backfills, M12/M16/M17/M28, r2a/*, letf/*, graveyard). Some >900 LOC, with local CI, panels, and cost math. ORIENTATION still says “19 one-off” — docs drift.

**Move:** scripts that produce **reusable lake products** (earnings calendar, macro calendar, daily bars, LETF AUM) graduate into `src/enginev51/data/` or `flows/` with tests. True one-shots stay scripts but import library helpers (no private `_side_sign` style leaks).

---

### S-H — Identity-import culture fights modularity

Live and screens **pin** functions by import identity and test that pins. That freezes bad homes (stats living in M23, early-close list in M20, fees in M11).

**Better pattern:** identity-pin against the **canonical module** after J1–J3, not against the first screen that implemented the helper.

---

### S-I — Hand-rolled economics vs fill kernel

Screens that compute `net_bps = gross - FEES` without `plan_pnl` / `market_fill` re-create COST_MODEL with different RT fee conventions (0.25 vs 0.3). Reviews already note this; structurally it means **three truths** for “net edge.”

**Move:** any new screen that claims economics must call auction or continuous fill path; mid-alpha screens must label outputs `mid_alpha_bps` never `net_bps`.

---

### S-J — Config hardcodes absolute Windows paths

`config.py` points at a machine-local credentials file and engineV5 legacy lake. Breaks clones; couples machines.

**Move:** env-only + optional `ENGINEV51_LEGACY_DATA_DIR`; no machine paths in repo.

---

## 4. Open correctness items (still actionable)

Reconfirmed present in tree as of this review (do not re-litigate; fix or re-verify):

| ID | Issue | Files |
|----|--------|-------|
| **B1** | Encoder static features: asof `ts` with no F2 bar lag (~60s look-ahead) | `models/encoder/dataset.py` `_static_vector` |
| **B2** | Cockpit `ticket_ok` ignores meta NO-GO when model loaded | `apps/live_cockpit.py` `decide_one` |
| **B3** | Stop search strict-after arm misses already-through | `backtest/fills.py` `stop_trigger_ts` |
| **B4–B6** | Presence-as-complete / empty partition / max(ts) end-day | `data/backfill.py`, store, noii, bbo1s |
| **B7** | Bare assert holdout guards | many apps/screens |
| **S1** | Condition filtering brittle | `backtest/tape.py` |
| **S6** | Forward ledger non-atomic write | `apps/forward_paper.py` |
| **S8** | `fetch_bars_multi` default `adjustment="all"` | `data/alpaca_hist.py` |
| **S9** | `INHERITED_TRIAL_FAMILIES` undercounts in-house cells | `protocol.py` |

Champion MOC path is largely insulated from B1/B3; **B2, B6, S6** still hit the alive production clock.

---

## 5. What is strong (do not “improve” away)

1. **Signal-only architecture** — no order routing in production packages.  
2. **Causal fill discipline** — PIT searchsorted, latency seeding, PnL identity in `decompose`.  
3. **Auction path separate from continuous path** — correct domain split.  
4. **Holdout culture** — even when incomplete, the *idea* of a choke point is right; complete it (J2).  
5. **Atomic lake writes** in store / NOII / BBO / live journal.  
6. **Hermetic research screens** — injectable loaders + synthetic tests.  
7. **Registration-before-results** process (docs + ledger) — rare and valuable.  
8. **Large green test suite** — prior P1 harness bugs pinned.

Preserve these while refactoring. Prefer moving kernels, not rewriting fill math.

---

## 6. Suggested workstreams for the thinking agent

Ordered for leverage × risk:

| Phase | Work | Risk to results |
|------:|------|-----------------|
| **0** | Fix B1, B2, B3 + tests; SealViolation not assert (B7) | Low if tests pin behavior |
| **1** | J1 extract `moc` / champion kernel from apps | Medium — needs identity tests updated |
| **2** | J2 single seal path; delete strip_holdout clones | Low–medium |
| **3** | J3 costs + stats facade; expand `assert_protocol_consistent` | Low |
| **4** | J4 screen template; migrate one screen as prototype (gap_day or open_fade) | Medium |
| **5** | J5 archive map + ORIENTATION alive graph | Docs only first |
| **6** | Data completeness B4–B6; atomic forward ledger S6 | Ops correctness |
| **7** | Scripts graduation / 1k-line splits | Low for science |

Avoid: large “clean architecture” rewrites of continuous replay or encoder unless a family reopens. Avoid renaming for aesthetics. Avoid merging MOC and continuous into one mega-replayer.

---

## 7. Anti-patterns to refuse in future diffs

1. New `assert_before_holdout` copy-paste.  
2. New `_ci` local wrapper — use shared report helper.  
3. New fee/gate/capital literal — import config.  
4. New import of pure logic from `apps.*` — put it under library first.  
5. Growing any file past ~800 lines without extraction.  
6. Hand-rolled `net_bps` in a screen that claims economics.  
7. `strip_holdout` that bypasses `apply_seal`.  
8. Feature logic in `live_cockpit` render functions.

---

## 8. Package health snapshot (for prioritization)

```
apps/               ████████████████████  10.8k   ← invert / extract
research_screens/   ███████████            5.7k   ← template
models/             ███████                3.6k   ← fix B1; stop importing apps
data/               █████                  2.4k   ← completeness + daily_bars
flows/              ████                   1.8k   ← ok; ffcal bulk is special
reversion/          ███                    1.7k   ← archive candidate
backtest/           ███                    1.5k   ← protect; fix B3/S1
events/             ██                     1.3k   ← archive candidate
live/               █                      0.7k   ← thin after J1
protocol/config     ▌                      0.2k   ← thicken slightly (J2/J3)
dashboard/          empty
```

---

## 9. One-paragraph brief for the next agent

enginev5.1’s economics spine and protocol *culture* are solid; the failure mode is **apps and research_screens becoming the library**, with holdout/fees/gates/CIs reimplemented until drift is inevitable. Highest judo: extract the champion MOC kernel out of `apps`, make `apply_seal`/`SealViolation` the only seal, centralize costs+stats, stop shipping closed families in the cognitive default path, and fix the still-open B1–B3 correctness bugs before trusting encoder or cockpit tickets. Do not rewrite the fill kernel or invent a framework for dead detectors.

---

## 10. Artifacts

| Artifact | Path |
|----------|------|
| This report | `research/CODE_REVIEW_2026-08-01.md` |
| Prior full review (bugs + ops) | `research/CODE_REVIEW_2026-07-28.md` |
| Prior harness review | `research/CODE_REVIEW_2026-07-17.md` |
| Architecture intent | `DESIGN.md`, `ORIENTATION.md` |

*End of structural quality report.*
