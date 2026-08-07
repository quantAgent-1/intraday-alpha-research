# M27 — gap-day reversion: harness design (frozen; orchestrator, 2026-07-23)

Implements M3_REGISTRATION.md § M27 VERBATIM. Underdetermined choices are decided HERE,
pre-look. No auction-print legs, no close contact, no NOII — quotes and daily bars only.

## 1. Modules

### `src/enginev51/research_screens/gap_day.py`

Constants (registration-cited):
```python
UNIVERSE   = ("KLAC", "MRVL", "LRCX", "TXN", "AMAT")   # exogenous bottom-5 ADV rule
START, END = date(2023, 8, 1), date(2026, 5, 31)        # purchased window; < holdout
DECISION_HMS, EXIT_HMS = (9, 35, 0), (15, 45, 0)
THRESH_T50, THRESH_T100 = 50.0, 100.0                    # |gap| bps, nested cells
LATENCY_LO_S, LATENCY_HI_S = 5, 25                       # seeded U[5,25] per (sym, session, leg)
SLIP_BPS = 0.5                                           # per leg, COST_MODEL v1 taker
FEES_RT_BPS = 0.25                                       # SEC/TAF sell side at $10k clip
CELL_MIN_FIRED, CELL_MIN_SESSIONS, UNDERPOWERED_BELOW = 400, 250, 200
MEAN_FLOOR_MULT = 2.0
OUT_SUBDIR = "M27-gap-day"
```

Functions:
- `load_bbo_month(sym, month)` — read `data/raw/bbo1s/{SYM}/{YYYY-MM}.parquet` (the same
  module-local layout the champion names use; loader mirrors existing bbo1s read paths).
- `quote_at(quotes, ts_ns)` — prevailing bid/ask at-or-before ts (searchsorted guarded ≥0
  — the fills.py landmine); staleness > 60s ⇒ None (skip reason stale_quote).
- `latency_ns(sym, session, leg)` — seeded uniform per the latency.py convention:
  sha256(f"7:{sym}:{session}:{leg}") — NEVER python hash(). Legs: "entry", "exit".
- `taker_fill(quotes, ts_decision, side, leg, sym, session)` — quote AT
  (decision + latency); buys pay ask, sells hit bid; ± SLIP_BPS adverse.
- `gap_of(prev_close, open_px)` — g_bps = (open/prev_close − 1) · 1e4; raw bars1d only (L2).
- `build_events(...)` — per (sym, session): prev_close+open from raw bars1d; g; skip
  reasons {no_bar, early_close (EARLY_CLOSE_DATES import), below_t50, no_quote_entry,
  no_quote_exit, stale_quote}; fired rows carry is_t100 flag (nested, same frame);
  side = −sign(g) (FADE); gross = side·(exit_fill/entry_fill − 1)·1e4;
  net = gross − FEES_RT_BPS (spread+slip already inside the fills — do NOT double-count).
- `write_cost_floors_first(...)` — RT_floor(name) = median(spread_bps@09:35 +
  spread_bps@15:45) over the full window + 2·SLIP_BPS + FEES_RT_BPS, written to
  cost_floors.json BEFORE any mean is computed (M20 ordering, test-enforced: the stats
  functions REFUSE to run if cost_floors.json is absent).
- `cell_stats(events, thresh, floors)` — mean net, day-clustered CI (stress.clustered_mean_ci,
  seed 7/2000), floors: n≥400 & sessions≥250 & ci_lo>0 & mean ≥ 2× pooled RT floor &
  ≥3/5 names positive point estimates; UNDERPOWERED n<200; BETWEEN per house vocab.
- `adia_panel(events)` — daily $10k-per-event aggregation; sr_native/psr/min_trl IMPORTED
  from sizing_shadow (identity test).
- Report-only strata (no bars): per-name, per-year, gap-sign split, |g| tercile,
  entry-spread tercile.
- One-look gate: M22 canonical-dir idiom verbatim; no out-dir option.
- Writers: atlas.md, cells.json, events parquet, ground_truth.parquet (10 stratified:
  biggest winners/losers/largest |g|/widest spread), cost_floors.json, look_state.json.

### `src/enginev51/apps/run_m27_gap_day.py`
Options: --trial-id M27-gap-day, --start/--end (defaults; assert_before_holdout), --seed 7,
--defect-rerun/--reason. Flow: holdout guard → look gate → floors FIRST → build → stats →
panel → strata → ground truth → write → mark spent. ASCII only.

## 2. Design rulings (pre-look)

- D1: prev_close = immediately preceding session's raw close in bars1d (calendar-gap
  agnostic); missing either bar ⇒ no_bar skip, never imputed.
- D2: quotes are XNAS TOB (L9: never called NBBO; all-XNAS internal consistency).
- D3: 09:35/15:45 are ET wall-clock, zoneinfo-converted (DST test both directions).
- D4: an event needs BOTH legs fillable (entry and exit quotes present, non-stale) else
  skip with reason — no partial economics.
- D5: entry quote staleness bound 60s; wider spreads are NOT skipped (they are the cost
  reality of these names — the floor and strata capture them).
- D6: the ADIA daily aggregation uses the t50 stream; t100 gets cell stats only.

## 3. Tests — `tests/test_m27_gap_day.py` (~14, synthetic only)

1 holdout guard; 2 instant pins + DST (EDT+EST); 3 nested thresholds (t100 ⊂ t50, same
frame); 4 direction pin (g>0 ⇒ side −1; mutation to WITH fails); 5 latency determinism
(sha256 convention; same (sym,session,leg) ⇒ same draw; ≠ across legs) + bounds [5,25];
6 taker fill semantics (buy pays ask + slip; sell hits bid − slip; hand-computed event);
7 floors-before-means ORDER enforced (stats refuse without cost_floors.json; floor formula
pinned); 8 early-close drop (EARLY_CLOSE_DATES import identity); 9 searchsorted guard
(quote before first tick ⇒ None, never wrap to last); 10 pass-bar all-of logic incl.
3/5-names prong and UNDERPOWERED band (each single-condition mutation fails); 11 one-look
gate locality; 12 funnel reconciles (skips + below + fired == candidates); 13 ADIA helpers
imported by identity; 14 writer smoke end-to-end in tmp dir (4 artifacts, ASCII atlas,
ground truth ≤10 rows).

## 4. Landmines

L2 raw bars for prev_close/open; fills.py wrap-to-future guard (test 9); latency.py
sha256-not-hash; L9 XNAS-internal labeling; M20 floors-first ordering; B1 gate locality;
no spread double-count (spread lives in fills, only fees subtracted separately).

## 5. Build order & reviewer attack list

Order: loaders+quote_at (9) → latency+fills (5,6) → gap+build_events+funnel (1-4,8,12) →
floors (7) → stats+panel (10,13) → writers+gate+CLI (11,14).
Reviewer attacks: (1) spread double-counting between fills and floor; (2) latency seeding
(process-salted hash() would be nondeterministic across runs); (3) staleness/searchsorted
edge (pre-open quote gaps on illiquid names); (4) DST; (5) the 3/5-names prong wiring;
(6) floors-first enforcement actually refusing; (7) nested-cell frame identity.
