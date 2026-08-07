# M22 — earnings-day closing crosses: harness design (frozen)

Produced by the architect agent 2026-07-23; ambiguities ruled by the orchestrator same day
(rulings mirrored in the registration's "Pre-data clarifications" block — that block is
authoritative). Implements `research/experiments/M3_REGISTRATION.md` § M22 VERBATIM. No
constant below may drift from the registration; the build must not "improve" the spec.

## 0. Orchestrator rulings on the architect's ambiguity list (A1–A8)

- A1: CI = `backtest.stress.clustered_mean_ci` (session bootstrap, seed 7, 2000 boots),
  cluster key = ET session string. Single-sourced with the reused pipelines.
- A2: Cell A mid = `fills.prevailing_mid` via `run_basis_trial` VERBATIM (the M6-FINAL
  champion convention). The registration's "completed-bucket" phrase refers to this audited
  lookup; do NOT introduce M20's `≤ ts−1s` variant.
- A3: baseline row has no minimum-N floor (report-only).
- A4: Cell C AUM = the M12 dated anchor series joined on `public_date` (F3-corrected
  artifact in `data/external/`), never the single-snapshot toml.
- A5: F per M12 Cell A verbatim: F = Σ(L²−L)·AUM·r, r = open→15:50 day0 return; complex
  membership from the LETF fund registry. Report-only.
- A6: 342/128/214 are registration-time inventory; realized counts reconcile via the
  reported funnel (per-reason skip counts). No hard assert on totals.
- A7: Cell A latency-draw seed = 7, pinned.
- A8: the 2× amplification prong binds only if baseline_mean > 0; else Cell A PASS reduces
  to n/sessions floors + CI-lower > 0, ratio reported ungated.
- A5' (post-build ruling, 2026-07-23): Cell C's r uses the day0 open→close daily return
  (raw bars1d) as a pool-wide consistent proxy for open→15:50 — the broad-12 have no owned
  intraday quotes, and a mixed-precision pool would be worse than a uniform proxy. Report-only
  prong, no bar; the atlas must label the proxy. `cell_c_strata` keeps an injectable
  `r_by_event` override if the exact window is ever supplied.

## 1. Module layout

### 1a. Harness — `src/enginev51/research_screens/earnings_close.py`

Registered constants (module-level, registration cited in comment):

```python
# M22 registration (2026-07-23, M3_REGISTRATION.md § M22). Do not tune.
SIGNAL_HMS        = (15, 55, 10)
FIRE_BASIS_BPS    = 10.0
START             = date(2020, 1, 2)
END               = date(2026, 5, 31)
EVENTS_PARQUET    = "research/experiments/M21-earnings-regime/events.parquet"
CELL_A_UNIVERSE   = ("NVDA","TSLA","AMD","MU","GOOGL")
CELL_B_UNIVERSE   = ("AAPL","AVGO","MSFT","QCOM","AMAT","INTC",
                     "KLAC","LRCX","META","MRVL","NFLX","TXN")
CELL_A_MIN_FIRED = 50; CELL_A_MIN_SESSIONS = 40; CELL_A_AMP_MULT = 2.0
CELL_B_MIN_FIRED = 60
OUT_SUBDIR       = "M22-earnings-close"
```

Cost/fee constants are IMPORTED, never re-declared: Cell A uses `replay_moc_event(...,
slip_bps=0.5, sec_taf_sell_bps=0.3)` via `run_basis_trial`; Cell B uses
`run_m11.TAKER_COST_BPS` (2.5), `run_m11.SEC_TAF_SELL_BPS`, `run_m11.FIRE_BASIS_BPS`.

Public functions (signatures as designed; keep):

- `load_day0_whitelist(events_path, universe, *, end=END) -> set[tuple[str, str]]`
  — read M21 events.parquet; keep symbol ∈ universe AND day0_session ≤ end; return
  {(symbol, day0_session_iso)}. day0_session IS the ET reaction session (M21 already
  resolved AMC/BMO) — used directly, NEVER re-mapped. `status` ignored per registration.
  Calls `assert_before_holdout` on the max day0 regardless.
- `build_cell_a_events(settings, *, whitelist, start, end, seed, ...) -> (DataFrame, dict)`
  — `run_basis_trial.run_basis_trial(CELL_A_UNIVERSE, start, end, seed)` VERBATIM, then
  annotate `is_day0` (keyed (symbol, session)) and `cell="A"`. Returns ALL events + funnel.
- `cell_a_stats(events) -> dict` — fired = |basis|≥10; day0 vs baseline via `is_day0`
  filters of ONE frame; day-clustered CIs; per-era (2020-22/2023-26) + per-name rows
  (reported, never gated); PASS/UNDERPOWERED flags per registration + ruling A8.
- `build_cell_b_events(settings, *, whitelist, ...) -> (DataFrame, dict)` — iterate ONLY
  whitelisted (sym, session) pairs; call `run_m11.fire_near_ref_event` (§1c); tag `cell="B"`.
- `cell_b_stats(events) -> dict` — PASS: n_fired ≥ 60 AND CI-lower > 0.
- `cell_c_strata(cell_a_events, cell_b_events, *, aum_source) -> DataFrame` — report-only;
  complex presence × |F|/ADV terciles; AUM on public_date (rulings A4/A5).
- `build_atlas_md(...)`, `write_outputs(...)` — A and B in separate files/sections ALWAYS;
  `write_outputs` asserts the `cell` tag sets are exactly {"A"} and {"B"}.
- One-look gate: `look_state_path`, `assert_look_not_spent(out_dir, *, defect_rerun,
  reason)`, `mark_look_spent(out_dir, *, trial_id, git_sha)`. Defect rerun requires a
  non-empty reason and appends a ledger note.

### 1b. CLI — `src/enginev51/apps/run_m22_earnings_close.py`

Options: `--trial-id` (default M22-earnings-close), `--start 2020-01-02`, `--end 2026-05-31`,
`--seed 7`, `--events <EVENTS_PARQUET>`, `--defect-rerun` flag, `--reason`.
Flow: `assert_before_holdout(end)` → `assert_look_not_spent` → whitelists → Cell A build+stats
→ Cell B build+stats → Cell C → ground-truth samples → `write_outputs` → `mark_look_spent`.

### 1c. Refactor — `run_m11.py` internals → `fire_near_ref_event` (ZERO behavior change)

Extract the per-(sym, session) firing body into:

```python
def fire_near_ref_event(settings, sym, session_iso, noii, *, closes, bars_dir=BARS1D_DIR
                        ) -> tuple[dict | None, str | None]
```

Pure translation: near_ref_at → basis_bps_of → direction_of → FIRE gate →
cross_price_for(None) raw daily close → conservative_entry_px → net_bps_for → _meta_feats.
Skip reasons {'no_near_ref','zero_basis','inactive','no_close'}. `run_m11.run_m11` becomes a
thin loop over it. UNIVERSE_28, SECTORS, all M11 constants and report paths UNTOUCHED.
The reproduction guard test lands BEFORE anything depends on the refactor.

## 2. Data flow

- Cell A: NOII near_at + bbo1s prevailing_mid at 15:55:10 → basis_pit_features →
  |basis|≥10 → taker entry (market_fill, U[5,25]s latency, 0.5bp slip) → exit AT the cross
  (replay_moc_event moc branch) → plan_pnl fees. day0/baseline = one flag on one frame.
- Cell B: per whitelisted pair → load_noii_session → fire_near_ref_event → basis_ref =
  1e4*(near−ref)/ref → |basis_ref|≥10 → entry = ref*(1 + side*2.5bps) → exit = day0 RAW
  bars1d close → net_bps_for. Proxy-priced evidence class; never pooled with A.
- Cell C: union of A+B day0 fired rows → strata only (no CI gate).

## 3. Statistics

`_ci(df)` wraps `stress.clustered_mean_ci(values, clusters=df["session"], n_boot=2000,
seed=7)` → (mean, lo, hi, n_events, n_sessions). A session with 2+ reporters = 1 cluster
automatically via the session cluster key.

## 4. Artifacts — `research/experiments/M22-earnings-close/`

`atlas.md` (cells in separate sections; funnels; amplification ratio; strata), `cells.json`
(disjoint keys cell_a/cell_b/cell_c; pass/underpowered FLAGS, not verdicts), 
`cell_a_events.parquet`, `cell_b_events.parquet` (never merged), `cell_c_strata.parquet`,
`ground_truth_a.parquet` (10 stratified fills via run_basis_trial._stratified_ground_truth),
`ground_truth_b.parquet` (10 extraction rows via run_m11.stratified_ground_truth),
`look_state.json`.

## 5. Test plan — `tests/test_m22_earnings_close.py` (synthetic fixtures ONLY)

1. test_holdout_guard_refuses_ge_20260601 — whitelist/CLI refuse day0 ≥ 2026-06-01.
2. test_apply_seal_strips_holdout_day0 — synthetic holdout-era row never enters a whitelist.
3. test_threshold_pin_is_10 — earnings_close.FIRE_BASIS_BPS == 10.0 == run_m11.FIRE_BASIS_BPS.
4. test_day0_join_amc_bmo_known_cases — 3 AMC + 2 BMO pinned events land on exactly
   day0_session, unchanged.
5. test_day0_join_keyed_by_symbol_session — NVDA-day0 session: TSLA row is baseline.
6. test_no_pooling_cell_tag_disjoint — cell tags exactly {"A"}/{"B"}; atlas/writer raise on
   a mixed frame.
7. test_cost_pin_cell_b_entry_2p5bps — TAKER_COST_BPS == 2.5 and realized entry_cost_bps == 2.5.
8. test_cost_pin_cell_a_costmodel_v1 — replay_moc_event called with slip 0.5 / sec_taf 0.3.
9. test_baseline_same_pipeline — day0 ∪ baseline == full fired set; disjoint; one build call.
10. test_m11_reproduction_unchanged — run_m11 on a fixed synthetic fixture is row-identical
    pre/post refactor.
11. test_clustered_ci_session_cluster — 2-reporter session counts as one cluster (golden).
12. test_cli_refuses_second_look — look_state present → raise; --defect-rerun without
    --reason → raise; with both → proceeds + ledger note.
13. test_cell_a_pass_bar_logic — PASS/UNDERPOWERED flags per bars incl. ruling A8
    (baseline_mean ≤ 0 → 2× prong vacuous).
14. test_cell_b_pass_bar_logic — n≥60 AND ci_lo>0 → PASS; else flags correct.

## 6. Landmines applied

L1 n/a (single-print cross exit both cells — stated in code comment). L2: Cell B exit MUST
be raw bars1d (run_m11 fetch adjustment="raw"); adjusted close would corrupt same-day
ref→close on splits. L4: ruling A2 (champion prevailing_mid verbatim). L5: ruling A4
(public_date join). L9: A/B price objects never pooled (tag + separate files + guard test);
all Cell A objects XNAS-internal. Seal: assert_before_holdout in CLI + whitelist loader +
inherited run_basis_trial session filter.

## 7. Build order

1. run_m11 extraction + reproduction guard test FIRST.
2. load_day0_whitelist + day0-join tests.
3. build_cell_a_events + same-pipeline test.
4. build_cell_b_events + cost-pin test.
5. cell_a_stats/cell_b_stats + _ci + pass-bar tests.
6. cell_c_strata (rulings A4/A5).
7. Ground-truth samplers + atlas + write_outputs + no-pooling guard.
8. One-look gate + CLI + second-look test.

Reviewer attack list: (1) byte-exactness of the run_m11 extraction incl. funnel mapping;
(2) whitelist keying uses day0_session directly (no AMC/BMO re-derivation — double-shift
risk); (3) A2 mid convention (no 1s leak vs champion path); (4) any accidental A/B pooling
in CI calls, atlas rows, or parquet; (5) A8 branch + seed pinning.
