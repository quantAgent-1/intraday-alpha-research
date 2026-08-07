# LIVE SIGNAL ENGINE — L0/L1 build design (frozen; orchestrator, 2026-07-23)

Implements PROPOSAL v0 phases L0+L1 (research/LIVE_SIGNAL_ENGINE_PROPOSAL.md).
Engineering, not research: no registered look, no ledger row, no new thresholds — every
kernel is IMPORTED from registered/production modules. Signal-only: no order routing, no
broker/network imports in the live package, ever.

## 0. Reuse contracts (scouted 2026-07-23; the build relies on these EXACT publics)

- Replay kernels: `forward_paper.compute_session_events(settings, asof, *, seed, noii_dir,
  bbo_dir)` → per-event frame; `forward_paper.score_events(events, booster)` → adds p_win /
  taken_classical / taken_meta; booster = `lgb.Booster(model_file=forward_paper.MODEL_PATH)`
  (never train — L1 engine loads-or-fails-classical like the cockpit); optional
  `positioning.apply_positioning` for M15 columns. These are the forward clock's own
  functions → byte-agreement by construction.
- Manual kernel: `live_cockpit.decide_one(symbol, near, bid, ask, *, session_iso, booster,
  ...optional M8 features..., capital_usd, clip_cap_usd, spread_abort_bps, gate_q)` → dict.
  live_cockpit is NOT modified.
- Sizing display: `sizing_shadow.tier`, `sizing_shadow.vol_norm`, `sizing_shadow.
  trailing_raw_vol`, `champion_sigma_med5` (M23 constants; report-only display).
- Stats: `sizing_shadow.psr`, `min_trl`, `sr_native`, `sample_moments` (ADIA panel).
- Early closes: `research_screens.sched_window.EARLY_CLOSE_DATES` (frozenset, ICE/NYSE-
  verified). NOTE (scouted): forward_paper/auction_replay silently no-op on half-days; the
  engine must be EXPLICIT: half-day ⇒ close window ABSENT + a labeled warning.
- Journal write convention: atomic tmp+os.replace and append-dedup-by-keys, copied from the
  `sched_window_forward._write_atomic/_append_dedup` pattern (cite in comment; those are
  private — reimplement the ~20 lines locally, do not import privates).

## 1. Modules (all NEW; nothing existing modified)

### `src/enginev51/live/__init__.py` (empty)

### `src/enginev51/live/engine.py`

Constants:
```python
JOURNAL_PATH   = PROJECT_ROOT / "research" / "live" / "signals_journal.parquet"  # gitignored
JOURNAL_KEYS   = ("session", "symbol", "source", "window")
OPEN_WINDOW_ET  = ((9, 25, 0), (9, 30, 0))     # dormant elsewhere — scope fence
CLOSE_WINDOW_ET = ((15, 50, 0), (16, 0, 0))
SOURCES = ("replay", "manual")                  # "feed" reserved for L2, refused for now
```

`JOURNAL_SCHEMA` (order pinned; test 2): ts_emit(i64 UTC ns), session(str), symbol(str),
window(str: "close"|"open"), source(str), basis_bps(f64), p_win(f64|null), side(i64),
taken_classical(bool), taken_meta(bool|null), tier(f64|null), vol_norm(f64|null),
size_notional_research(f64|null), size_shares_deploy(i64|null), expected_net_bps(f64|null),
order_type(str), limit_px(f64|null), deadline_et(str), spread_abort(bool|null),
engine_git_sha(str|null), note(str).

Functions:
- `_write_atomic(df, path)` / `_append_dedup(new, path, schema, keys)` — the copied pattern.
- `session_windows(session_iso) -> dict` — ET/DST-aware window bounds via zoneinfo;
  `session in EARLY_CLOSE_DATES` ⇒ `{"close": None, "early_close": True, ...}` (close
  window ABSENT on half-days; open window unaffected). Test 3 covers EDT, EST, half-day.
- `emit(rows: list[dict], *, source) -> int` — validates source ∈ SOURCES, stamps ts_emit
  (time.time_ns), engine_git_sha, appends dedup'd. Refuses source="feed" (L2 gate).
- `replay_session(settings, asof, *, seed=7) -> pl.DataFrame` — the ReplayAdapter:
  compute_session_events → booster load (Booster or None → classical-only, p_win null) →
  score_events → attach M23 display fields (tier(p_win), vol_norm from trailing raw vol —
  same loaders as sizing_shadow; null on vol-history skip) → map to JOURNAL_SCHEMA rows
  (window="close", order_type per PLAYBOOK: "LOC_late_or_MKT1559", deadline "15:58:00") →
  `emit(source="replay")` → return the frame for display.
- `manual_decide(**decide_one_kwargs) -> dict` — the ManualAdapter: call
  `live_cockpit.decide_one` verbatim; attach tier/vol_norm display; emit(source="manual");
  return the enriched dict for rendering.
- `monitor_panel(journal: pl.DataFrame, *, ref_sr: float|None) -> dict` — daily-aggregate
  the journal's taken_classical rows ($10k/event), native SR, PSR[SR0=0], and if ref_sr
  given also the ADIA live-testing probe PSR[SR0=ref_sr] (P[SR<live|SR=ref] semantics per
  the adopted standard); MinTRL; T. Pure display.

### `src/enginev51/live/reconcile.py`

- `reconcile(journal: pl.DataFrame, ledger: pl.DataFrame, *, tol_replay=1e-9,
  tol_manual=1.0) -> pl.DataFrame` — inner-join on (session, symbol); per-field diffs for
  basis_bps / p_win / net-relevant columns; a row FLAGS when |diff| > tol for its source
  (replay must match to 1e-9 — same functions; manual gets 1.0 bps keying tolerance on
  basis, p_win 0.01). Ledger is READ (forward_paper.load_ledger or read_parquet) — no write
  API imported (test 8).
- `reconcile_report(flags) -> str` — ASCII table + counts.

### `src/enginev51/apps/live_engine.py` (click group)

- `rehearse --asof DATE [--seed 7]` — replay_session on owned data; prints the emission
  table + monitor panel. (Recomputes already-published pipeline rows for display/journal —
  not a research look; no gating output.)
- `decide --symbol --near --bid --ask [M8 feature options, same names as live_cockpit]` —
  manual_decide; prints the cockpit ticket + tier/vol panel.
- `reconcile [--sessions N]` — journal vs forward ledger; prints report.
- `monitor` — monitor_panel over the journal to date.
- `selftest` — synthetic in-memory round trip (emit → read → reconcile clean) proving the
  plumbing without touching real paths.
Windows console: ASCII only; PYTHONIOENCODING note in docstring.

## 2. Design rulings (pre-stated)

- R1: Journal dedup keys include `source` — a replay row never blocks a manual row for the
  same (session, symbol); re-running rehearse is idempotent.
- R2: Booster load failure ⇒ classical-only emission with p_win/taken_meta/tier = null and
  note="no_model" (mirrors the cockpit's degrade path); never train.
- R3: Half-day sessions: close-window emissions REFUSED with reason "early_close" (explicit,
  vs the silent upstream skip); open window unaffected.
- R4: vol display fields use M23's exact loaders/rules incl. the neutral-1.0 history-skip
  ruling; skip surfaces as vol_norm=null + note.
- R5: The engine NEVER writes research/forward/ledger.parquet or any lake path; its only
  write target is JOURNAL_PATH (+ .tmp sibling). Enforced by test 8 (source grep + no
  import of append_ledger) — the M23 read-only idiom.
- R6: source="feed" refused until an L2 design exists (explicit error naming the gate).

## 3. Tests — `tests/test_live_engine.py` (synthetic only; ~12)

1. test_journal_atomic_append_dedup — append twice, keys deduped, tmp file gone, idempotent.
2. test_journal_schema_pin — column list + dtypes exact.
3. test_session_windows_dst_and_halfday — EDT session, EST session (zone-aware bounds),
   half-day from EARLY_CLOSE_DATES ⇒ close window None + early_close flag.
4. test_replay_wiring — monkeypatched compute_session_events/score_events ⇒ journal rows
   source="replay", correct column mapping, git sha stamped.
5. test_manual_wiring — monkeypatched decide_one ⇒ source="manual" row + ticket dict
   enriched with tier/vol fields.
6. test_kernel_identity — engine references forward_paper.compute_session_events,
   forward_paper.score_events, live_cockpit.decide_one, moc_meta.predict_pwin (transitive),
   sizing_shadow.tier/vol_norm/psr/min_trl BY IDENTITY (no local reimplementations).
7. test_reconcile_exact_and_flags — identical synthetic frames ⇒ 0 flags; basis off by
   2 bps ⇒ flagged for manual tol, off by 1e-6 ⇒ flagged for replay tol.
8. test_no_ledger_write_path — live package source contains no write to the forward ledger
   and never imports forward_paper.append_ledger; journal path is the sole write target.
9. test_monitor_panel_psr — hand case: PSR[SR0=0] and the ref-probe PSR both match
   sizing_shadow.psr called directly.
10. test_dormancy_refusal — emit for a window outside session_windows ⇒ refused with
    reason; source="feed" ⇒ refused naming L2.
11. test_no_routing_imports — live package imports contain no broker/network modules
    (requests/httpx/websocket/alpaca/ib etc. — explicit denylist grep).
12. test_halfday_close_refusal — R3: close-window emit on an EARLY_CLOSE_DATES session
    refused with "early_close".

## 4. Build order & reviewer attack list

Order: journal helpers (1,2) → session_windows (3,12) → emit + refusals (10,11) →
replay/manual wiring (4,5,6) → reconcile (7,8) → monitor (9) → CLI + selftest.

Reviewer attacks: (1) any drift between engine output and forward_paper rows (must be the
same objects, not lookalikes — identity test 6 is the guard, verify it bites); (2) journal
non-atomicity or dedup dropping newer rows; (3) DST window bounds; (4) silent half-day
leak-through; (5) any write path beyond JOURNAL_PATH; (6) monitor stats reimplementation
instead of sizing_shadow imports; (7) hidden network/broker import.

## 5. Post-build ops (orchestrator)

After merge: run `rehearse --asof` for the 3 banked forward sessions and `reconcile` — the
real byte-agreement acceptance (replay rows must match the forward ledger at 1e-9). Then
PLAYBOOK gains a one-line pointer to `live_engine decide` as the L1 path (doc edit only).
