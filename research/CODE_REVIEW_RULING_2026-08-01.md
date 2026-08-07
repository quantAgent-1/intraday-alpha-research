# Ruling on CODE_REVIEW_2026-07-28 + CODE_REVIEW_2026-08-01

**Date:** 2026-08-01 (session 11, post-M30-verdict). **Ruled by:** orchestrator (orchestrator).
**Inputs:** `CODE_REVIEW_2026-07-28.md` (correctness, B1–B7/S1–S16/N1–N4),
`CODE_REVIEW_2026-08-01.md` (structural, J1–J5/S-A..S-J). Load-bearing claims
spot-verified against source before ruling (B2 ticket_ok, B3 strict-after stop, B7 bare
asserts, protocol seal API, sizing_shadow ADIA ownership + importers).

## 1. The context that re-weights both reviews

Both reviews treat the **champion MOC path as the alive production path. It is not.**
The close-auction direction is banned (binding user decision 2026-07-23); the champion is
frozen undeployed; forward_paper/cockpit are a stopped clock. And as of today M30 is
NOT-CONFIRMED, so `rfd_live` is permanently dark too. **What is actually alive:**

- the **data lake + backfill machinery** (the next axis — GEX or anything else — starts
  with a multi-day pull; B4–B6 class bugs poison exactly that),
- the **protocol layer** (seal, ledger, registration culture — the program's core asset),
- the **battery harness** (M28/M29 pattern — the declared template for the next family),
- the **stats/costs kernels** (ADIA panel, clustered CIs, cost model — every future
  report flows through them),
- the **continuous fill kernel** (`backtest/fills.py` — any future minutes-to-hours
  family with stops prices against it).

Value therefore concentrates in correctness-of-shared-kernels and protocol integrity,
not in beautifying the frozen champion assembly.

## 2. ACCEPTED (phased)

**Phase 0 — correctness, surgical, each with a regression test:**

| Item | Ruling |
|---|---|
| **B7/J2** seal choke point | ACCEPT. `protocol.refuse_end_on_or_after_holdout()` raising `SealViolation`; every bare `assert … HOLDOUT` clone converted. Failure-mode-only change: **zero numeric change to any frozen screen**. Add a source-grep tripwire test so the pattern cannot return. |
| **B3** already-through stop | ACCEPT. Level-check prevailing quote at arm; already-through ⇒ decision at arm + latency. Fill kernel is future-family infrastructure. |
| **B2** cockpit meta NO-GO doesn't block ticket | ACCEPT. Frozen path, but it ships, and the cockpit is the template for any future live cockpit. One-line gate + test. |
| **B1** encoder static F2 lag | ACCEPT. Dormant path, cheap fix, kills a known ~60s look-ahead so any encoder revival starts clean. |
| **B4–B6** presence-as-complete, zero-row markers, max(ts) end-day | ACCEPT. Protects every future backfill (the GEX pull, if keyed, is exactly this shape). Fail-open on metadata → fail-closed. |
| **S6** forward ledger non-atomic | ACCEPT. tmp + `os.replace`, same as live journal. |
| **S8** `adjustment="all"` default | ACCEPT. Flip default to `raw`; audit call sites; explicit `"all"` for total-return only. |
| **S1** condition-code filter brittle | ACCEPT (tokens, not substring). |

**Phase 1 — single-sourcing (drift-killers):**

| Item | Ruling |
|---|---|
| **J3a** ADIA helpers out of sizing_shadow | ACCEPT via **move + re-export**: definitions to `enginev51/stats/adia.py`; `sizing_shadow` re-imports so every existing importer (rfd_live, live/engine, m28/m29 scripts, screens) keeps working with **identity preserved** (test: `sizing_shadow.psr is stats.adia.psr`). |
| **J3b** shared `report_ci` | ACCEPT for **future code only**. The 14 local `_ci` clones in *closed* screens are frozen artifacts — they stay. New screens must use the shared helper (anti-pattern list + tripwire). |
| **J3c** constants tripwire | ACCEPT as **assert-equality, not rewrite**: canonical homes (meta gate → `moc_meta`, SEC/TAF + deploy + notional → config/costs) + an extended `assert_protocol_consistent()` that fails the suite if any registered copy drifts. Frozen screens are not edited to import the canon — their copies are *pinned* centrally. |
| **S9** in-house family count | ACCEPT (protocol-owned count for DSR/PBO honesty). |
| **S11/S-J** hardcoded machine paths | ACCEPT (env override, current values as fallback). |
| **N1–N4 + ruff 7** | ACCEPT (bundled, mechanical). |

**Phase 2 — future-facing:**

| Item | Ruling |
|---|---|
| **J4** screen template | ACCEPT the *principle*, DEFER the framework: build `ScreenSpec` **when the next family registers** (build-when-used; the M28 battery harness already is the battery template). Shared loaders (daily closes/ADV, early-close calendar) may consolidate now if zero-risk. |
| **J5** archive closed families | ACCEPT the **docs form only** now: ORIENTATION rewritten around the alive map (§1 above), dormant packages labeled ARCHIVED-IN-PLACE. No physical moves — 749 green tests pin history; churn there buys no science. |

## 3. REJECTED (with reasons)

| Item | Ruling |
|---|---|
| **J1 / S-A** full champion-kernel extraction (`enginev51/moc/`) | REJECT for now. It restructures the **banned, frozen** line. If close-auction is ever un-banned, do it then. The *rule* it implies is adopted prospectively: **no new pure logic under `apps/`** (anti-pattern list). |
| **S-F** typed contracts (MocEvent/BasisDecision) | REJECT — champion-only payoff on a frozen path; the reviewer's own caveat ("don't invent frameworks for dead families") applies to the champion now too. |
| **S2/S3/S4** maker-stress / limit mid_at_action / quote max-age | DEFER — continuous-replay refinements on a dormant path with no revival candidate. Recorded, not scheduled. |
| **S7** cockpit vs engine sizing basis | DEFER — both consumers frozen. |
| **S13** fold-helper unification | DEFER — both consumers (M8v2/M25) dead/withdrawn. |
| **S15** MOC entry-before-exit guard | DEFER — production callers already safe; public API unused by alive code. |
| **S12** ONE_SHOT hardening | DEFER — social control has held through 30+ families; ops discipline is demonstrated. |
| Physical `_archive/` moves, replayer merging, renames | REJECT per both reviews' own warnings. |

## 4. Execution rules (binding on all agents)

1. **Never touch:** `scripts/r2a_*.py`, `scripts/rfd_live.py`, `research/experiments/**`,
   `research/ledger.jsonl`, `data/**` (the lake), `logs/**`, any `PREDECLARATION*`.
2. **Frozen registered screens** (`research_screens/*` for closed families, m28/m29
   scripts): failure-mode changes only (assert→raise); **zero numeric-path edits**.
3. Agents never git-revert/checkout files they didn't create (standing rule).
4. Move-don't-rewrite: kernels relocate with re-exports preserving import identity.
5. Every fix lands with a test that fails on the old behavior; suite must be green.
6. Agents do not commit — the orchestrator audits, runs the full suite, commits.

## 5. Lanes

- **Wave 1 (parallel, file-disjoint):**
  A (Opus) protocol refuse-helper + assert conversions (all clones except sizing_shadow);
  B (Opus) B3 fills + B2 cockpit + B1 encoder + replay-adjacent nits;
  C (Opus) B4–B6 data completeness + S8 default + S6 atomic ledger + S1 tokens;
  E (Sonnet) S11 config env paths + ruff + N1/N4 + docstring nits.
- **Wave 2 (after A):** D (Opus) `stats/adia.py` move + re-export identity,
  `report_ci`, constants tripwire in `assert_protocol_consistent`, S9, sizing_shadow
  seal routing.
- **Wave 3:** separate adversarial reviewer attacks the combined diff against this
  ruling; orchestrator audits, full suite, commit.
- ORIENTATION alive-map rewrite: orchestrator-authored at session end (post-suite).

---

## 6. EXECUTION ADDENDUM (wave-1 outcomes + orchestrator rulings, 2026-08-01)

**Scale corrections found by the lanes (the reviews undercounted):**
- B7/J2 was "9 clones"; reality = **24 bare holdout asserts across 15 files** (the 9
  named `assert_before_holdout` clones + 15 frame/session-level asserts). All converted
  except sizing_shadow (wave-2). AST tripwire test added so the pattern cannot return.
- B3 needed an **inverted-window guard the review did not mention** — without it the
  already-through fix would return a trigger past `to_ts`. Landed with the fix.

**Rulings on items flagged by lanes:**
1. **S8 residual (lane C):** the LETF bars1m lake and the R2-A Stage-3 OOS bars1m are
   back-adjusted (`"all"`) while fills price the raw tape — F1-class *if consumed*.
   RULING: behavior-preserving pin stands; **no refetch now** — zero alive consumers
   (M28/M30 closed, LETF flows dormant), and the standing registration rule (raw-lake
   citation + bar-vs-tape gate, 2026-07-21) already blocks any future family from
   adopting the adjusted lake. Refetch-to-raw becomes a registered data-migration task
   only if a family reopens on those names. NOTE: `r2a_prong0` reads trades+BBO only —
   the M30 verdict has **no bars1m dependence** (verified by grep before this ruling).
2. **S1 second half** ("quarantine empty-condition coded days"): lane C correctly did
   NOT implement — numeric-path change on frozen screens. DEFERRED with the S2–S4 class.
3. **`assert_forward_only`** (lane A flag): same `-O` fragility, different boundary
   (forward go-live). RULED IN SCOPE → wave-2 task 5.
4. **Lane B touching `decompose.py`** (N2's true home, outside its four assigned
   files): ACCEPTED — failure-mode-only, no owner collision; noted for the reviewer.
**Wave-3 adversarial review verdict: APPROVE-WITH-FIXES** (independent verification:
840 green ×2, ruff clean, 11 guards probed under `python -O`, ADIA move AST-byte-identical,
`strip_holdout` reroute empirically identical over 8 adversarial frame shapes, B3 probed over
12 degenerate kernel cases + 4 end-to-end replays with no double-exit, synthetic dual-root
lake reproduces HEAD planning exactly at default flags, no-touch compliance perfect). All 11
findings ruled IN SCOPE and fixed in a wave-4 pass:
- [major] three `-O`-strippable seal asserts in `scripts/` backfill tooling
  (`refetch_bars1m_raw`, `backfill_bars1m_oos`, `backfill_bars1m_wide`) + tripwire extended
  to scan `scripts/`;
- [major] fail-closed vendor probe gains an operator escape hatch
  (`--skip-condition-probe`, default stays fail-closed; log distinguishes "vendor says
  degraded" from "probe unavailable");
- [minor] two tautological constant pins removed (import-aliases can't drift); the 0.25/0.3
  docstring corrected to the honest reading — **same economic quantity at two registered
  vintages**, frozen, pinned to each other and deliberately not cross-vintage;
- [minor] `LEGACY_DATA_DIR` field-name env route restored in `get_settings()` (precedence:
  `ENGINEV51_LEGACY_DATA_DIR` > `LEGACY_DATA_DIR` > default); bbo1s close margin 60→300 s
  (perpetual-refetch guard, credits nearly exhausted); cockpit block order = spread abort
  before meta; plus four nits (docstrings, LF normalization, test convention).
- **Deferral-record update (reviewer):** B3's level-check reads the prevailing quote with no
  max age, making the DEFERRED **S4** (quote max-age) more load-bearing than when deferred —
  direction is conservative (stale-through ⇒ more stops), cannot manufacture edge; S4 moves
  to the head of the deferred list if the continuous path ever reopens.
- **Wording corrections to lane claims:** Lane C's tape-token identity is *empirically
  supported on a 150-of-14,265-partition random sample*, not proven; `session_summary` has
  zero production callers, so the out-of-lane N2 fix is provably inert for registered numbers.

5. **DATA INCIDENT** (ledger note this date): a short-lived `validation_alias`
   experiment in config.py silently broke `Settings(legacy_data_dir=...)` kwarg
   isolation; a pre-existing test destroyed NVDA 2026-01-05 trades+quotes in the REAL
   engineV5 legacy lake (0-row overwrite) and a new test wrote spurious 2026-07-16
   files. M30 unaffected (primary lake + no NVDA among OOS names). Code holes closed
   same session (env-override design with explicit-kwargs-win + autouse isolation
   fixtures + repo-wide conftest guard in wave-2). **File remediation pending USER**
   (permission classifier blocks agent deletion/backfill): delete the four files, rerun
   `backfill ticks --symbols NVDA --start 2026-01-05 --end 2026-01-05`, QA counts.
   The 0-row overwrite is finding **B5 realized in the wild** — the sidecar/content
   completeness fix landed this same session.
