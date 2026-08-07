# M24 — opening-auction dislocation fade: harness design (frozen)

Architected directly by the orchestrator (orchestrator) 2026-07-23 per the amended standing rule.
Implements M3_REGISTRATION.md § M24 VERBATIM. Registered constants may not drift; anything
the registration underdetermines is decided HERE, now, pre-data — there is no separate
ambiguity round.

## 1. Modules

### `src/enginev51/research_screens/open_fade.py` (harness; template = earnings_close.py)

Frozen constants (each cites the registration):

```python
# M24 registration (2026-07-23, M3_REGISTRATION.md § M24). Do not tune.
SIGNAL_HMS      = (9, 28, 30)          # decision instant ET
THRESH_T25      = 25.0                 # |basis_open| >= 25 bps (gated cell t25)
THRESH_T50      = 50.0                 # nested gated cell t50 (t50 subset of t25)
START           = date(2020, 1, 2)
END             = date(2026, 5, 31)    # < holdout; assert_before_holdout
SEC_TAF_SELL_BPS = 0.3                 # import-or-pin equal to run_m11's constant (test-pinned)
CELL_T25_MIN_FIRED, CELL_T25_MIN_SESSIONS = 300, 150
UNDERPOWERED_BELOW = 150
MEAN_FLOOR_BPS  = 2.0                  # PASS floor (>= ~4x fee floor)
OUT_SUBDIR      = "M24-open-fade"
UNIVERSE        = tuple(sorted(<the 33 NOII symbol dirs>))   # pinned EXPLICIT tuple, not a
                                       # runtime glob — a lake change must fail a test, not
                                       # silently change the universe
```

UNIVERSE pin (from the 2026-07-23 scout of data/raw/noii/): AAPL ADBE AMAT AMD AMGN AVGO
BKNG CMCSA COST CSCO GILD GOOGL HON INTC INTU ISRG KLAC LRCX MDLZ META MRVL MSFT MU NFLX
NVDA PEP PLTR QCOM SBUX TMUS TSLA TXN VRTX (33 names).

Public functions:

- `load_open_noii(sym: str, month: str, *, noii_dir=None) -> pl.DataFrame`
  Read the monthly partition (module-local root `data/raw/noii`, the noii/bbo1s bypass
  convention), filter to ET window [09:00:00, 09:30:30]. Columns: ts, side,
  imbalance_shares, paired_shares, near_price, far_price, ref_price. UTC-ns → ET via
  America/New_York (reuse the repo's tz idiom; never naive UTC-4).
- `open_basis_at(msgs: pl.DataFrame, session_iso: str) -> tuple[dict|None, str|None]`
  Last message at-or-before 09:28:30 ET with near>0 AND ref>0 →
  `{basis_open_bps, near, ref, side_flag, imbalance_shares, ts}`; else (None, reason)
  with reason ∈ {no_msgs, no_near_ref}. basis == 0 exactly → (None, "zero_basis").
- `fade_event(sig: dict, open_px: float, close_px: float) -> dict`
  side = -1 if basis>0 else +1 (AGAINST — the frozen direction).
  gross_bps = side · (close_px/open_px − 1) · 1e4 ; net_bps = gross − SEC_TAF_SELL_BPS.
  Emits: session, symbol, basis_open_bps, side, open_px, close_px, gross_bps, net_bps,
  plus report-only strata inputs: overnight_gap_bps = (open_px/prev_close − 1)·1e4 (prev
  raw close from the SAME bars frame; None if no prior close → strata row null, event kept),
  imb_side_agrees (bool: NOII side flag B with basis>0 / A with basis<0).
- `load_daily_bars(sym) -> pl.DataFrame` — raw bars1d open+close (L2; read like
  run_m11._daily_closes but keep BOTH columns; do NOT modify run_m11).
- `build_events(settings, *, start, end, universe=UNIVERSE) -> (pl.DataFrame, dict)`
  Loop (sym, month, session): signal → bars lookup (missing bar → skip reason no_bar) →
  fade_event. Funnel counts {no_msgs, no_near_ref, zero_basis, no_bar, below_t25, fired_t25}.
  Fired = |basis| ≥ 25; the frame carries all fired rows + `is_t50` flag (nested).
- `cell_stats(events, *, thresh) -> dict` — day-clustered CI (stress.clustered_mean_ci,
  seed 7/2000), n/sessions floors, PASS/UNDERPOWERED/BETWEEN flags per the registered bars
  (PASS = n≥300 & sessions≥150 & ci_lo>0 & mean≥2.0; UNDERPOWERED if n<150).
- `adia_panel(events) -> dict` — daily-aggregated fired stream (equal $10k per event,
  session P&L) → sr_native / psr(SR0=0) / min_trl imported FROM
  `research_screens.sizing_shadow` (already golden-tested; do not reimplement).
- `rho_vs_champion(events, champion_daily: pl.DataFrame|None) -> float|None` — realized
  daily-P&L correlation vs the champion dev daily stream on overlapping sessions
  (report-only; champion daily loaded from the M8-meta-v1 OOS parquet aggregated to
  sessions at $10k equal notional — the published stream, read-only).
- Strata (report-only, no bars): gap-sign × basis-sign 2×2 means; imb_side_agrees split;
  per-year; champion-5 vs broad-28; corr(basis_open_bps, overnight_gap_bps) — the gap_mr
  fence diagnostic, MUST appear in the atlas.
- One-look gate: copy the M22 idiom EXACTLY — `canonical_out_dir()`, `out_dir_for()` whose
  param exists only for tests, `assert_look_not_spent(defect_rerun, reason)`,
  `mark_look_spent(trial_id, git_sha)`. No CLI out-dir option (B1 lesson).
- Writers: atlas.md + cells.json + events parquet + ground_truth.parquet (10 stratified:
  biggest winners/losers, largest |basis|, one per year minimum where possible).

### `src/enginev51/apps/run_m24_open_fade.py`

Options: --trial-id (M24-open-fade), --start 2020-01-02, --end 2026-05-31, --defect-rerun,
--reason. Flow: assert_before_holdout → assert_look_not_spent → build_events → cell_stats
t25/t50 → adia_panel → rho_vs_champion → strata → ground truth → write → mark_look_spent.
ASCII_MARKDOWN table config; no non-ascii output.

## 2. Decisions the registration left to the design (ruled here, pre-data)

- D1: The 09:28:30 cutoff uses message ts ≤ 09:28:30.000000 ET inclusive.
- D2: prev_close for the gap stratum = the immediately preceding row in the symbol's bars1d
  frame (calendar-gap agnostic); missing → gap stratum null, event retained.
- D3: Sessions present in NOII but missing in bars1d (or with open/close ≤ 0) are skips
  (no_bar), never imputed.
- D4: The ADIA daily aggregation uses $10k equal notional per fired event (t25 stream);
  t50's panel omitted (nested — one panel, two cell stats).
- D5: rho_vs_champion uses ONLY sessions where both streams have events; n_overlap reported
  beside ρ̂; if n_overlap < 30 report ρ̂ with an UNDERPOWERED-ρ flag.
- D6: Early-close sessions (half-days) are ordinary events (close print exists at 13:00);
  flagged in a report-only count.

## 3. Tests — `tests/test_m24_open_fade.py` (synthetic only; M22 style)

1. test_holdout_guard — build_events refuses end ≥ 2026-06-01; synthetic post-seal session
   never enters.
2. test_universe_pinned — UNIVERSE is the explicit 33-tuple; a glob of data/raw/noii is NOT
   used at runtime (assert constant length 33 and alphabetical).
3. test_signal_instant_pin — SIGNAL_HMS == (9,28,30); a message at 09:28:31 is ignored,
   09:28:30.000 exact is used (D1).
4. test_signal_requires_near_and_ref — near=0 or ref=0 rows never selected; no_near_ref
   funnel reason emitted when nothing qualifies.
5. test_direction_pin_fade — basis>0 → side=-1; basis<0 → side=+1 (a WITH mutation fails).
6. test_threshold_pins_nested — THRESH 25/50; is_t50 ⇒ fired_t25 (subset asserted on a
   synthetic frame).
7. test_fee_pin — net = gross − 0.3 exactly; constant equals run_m11's SEC_TAF_SELL_BPS.
8. test_price_source_pins — entry from `open`, exit from `close`, same session row, raw
   bars1d path (no adjusted source imported).
9. test_gap_stratum_and_fence — overnight_gap uses prior close; corr(basis, gap) computed
   and emitted in cells.json (fence diagnostic present).
10. test_pass_bar_logic — synthetic cells exercise PASS / UNDERPOWERED (n<150) / BETWEEN
    (point>0, CI spans 0) flags exactly per registration.
11. test_one_look_gate_not_relocatable — no CLI out-dir; gate anchored to canonical dir;
    spent look refuses a second no-arg invocation; --defect-rerun requires --reason.
12. test_adia_helpers_imported — psr/min_trl/sr_native are sizing_shadow's objects
    (identity check), not local reimplementations.
13. test_clustered_ci_session_cluster — 2-reporter session = 1 cluster (golden).
14. test_funnel_reconciles — synthetic month: skips + fired == candidates, per-reason
    counts exact.

## 4. Landmines

L2: BOTH legs raw bars1d (an adjusted open or close corrupts same-day open→close on any
ex-div date). L4-analog: signal strictly ≤ 09:28:30; nothing after the instant enters.
Seal: assert_before_holdout in CLI + builder. L9-analog: all XNAS-internal (NOII + official
prints); champion-5 vs broad-28 reported separately, pooled gating disclosed. B1: gate
canonical-dir only. M6b fence: this module must never compute norm_imb or any timed exit —
reviewer checks by inspection.

## 5. Build order & reviewer attack list

Order: loaders + signal (tests 3,4) → fade_event + fee/price pins (5,7,8) → build_events +
funnel (14) → cell_stats + bars (10,13) → adia_panel via imports (12) → strata/ρ (9, D5) →
gate + CLI (11) → writers + ground truth.

Reviewer attacks: (1) tz conversion (UTC-ns → ET; a naive UTC-4 breaks DST sessions —
check a March-DST and a November-DST synthetic case); (2) direction sign chain end-to-end
(basis>0 ⇒ short ⇒ profits when close<open — one hand-computed synthetic event); (3) the
gap stratum's prev_close alignment (off-by-one session); (4) nestedness (t50 stats computed
on the SAME frame subset, not a re-scan); (5) any accidental norm_imb/timed-exit reuse from
run_open_trial (M6b fence); (6) one-look gate locality; (7) PASS floor uses mean≥2.0 AND
ci_lo>0 AND both n-floors (mutating any single condition must fail test 10).
