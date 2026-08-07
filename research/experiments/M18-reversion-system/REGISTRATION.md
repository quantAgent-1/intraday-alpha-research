# M18 — reversion_system_v1 (REGISTERED 2026-07-20)

Status: REGISTERED 2026-07-20 (user sign-off in session; ledgered same day). No economics may run before this line.

## 0. One-line hypothesis

The engineV2 OU-reversion trigger — mid-alpha ≈ 0 unconditionally at taker (its recorded
verdict) — becomes net-positive **as a system**: entries conditioned by supporting gates,
losers vetoed by a meta-label model, fills expressed maker-first. The unit of verification is
the combined system; the bare signal is an attribution row, not a gate.

## 1. Why this is not a dead-family reopen

- `daily_xs_reversal_v1` (M7, FAIL/closed): daily cross-sectional. This is intraday
  single-name time-series. Different object.
- engineV2 verdict (0/75 cells, TRAIN 2025-09→2026-03): every cell was **taker at BBO,
  1500 ms latency, hold ceiling ≤ 1 h**, unconditioned beyond the original gates. Recorded
  decomposition: gross −$4.293/trade = mid +$0.25 (≈0) − spread $4.543. Loss was 100%
  execution. Untested: maker-first fills, holds > 1 h, conditioning, meta-labeling.
  Passive-capture ceiling $9.087/trade vs fee floor ~$0.61 (engineV2 LEDGER.md) — the
  economics are sign-flippable iff conditioned mid-alpha > 0.
- Kalman stretch-fade (V5 dead): unconditional fade, different signal family. Not reopened.
- "Uncertainty/toxicity filters" (V5 dead): that death was filters-as-rescue on an edgeless
  forecast. Here the filter is meta-labeling on a *conditioned* entry stream, with M8 as the
  in-house existence proof (+2.5 → +4.0 ref on the champion). Precedent respected: engineV2's
  P8 abort overlay died in red-team as overfit → our grid is declared and tiny (§5).

## 2. Frozen primary rule (engineV2, byte-faithful)

Source of truth: engineV2 `src/engine/strategy/params.py` (ReversionDefaults/RiskDefaults),
`strategy/reversion.py`, `backtest/cpu/strategies/reversion_nb.py`, `hot/ou_calibration.py`.

- State: ε_t = mid_t − VWAP_5m; OU MLE on 1 Hz samples, window 300 s, min 300 samples,
  recalibrated every 60 s; require κ̂ > 0, σ̂ > 0.
- Thresholds: smooth-pasting free-boundary solve (c = 0.0008, ρ = 0.01), reflection
  entry_long = 2θ − exit_long.
- Entry triggers and gates exactly as engineV2 defaults: OFI 5s neutral zone ±1.0, rho gates
  ±0.2, max_spread 30 bps, trend filter 50 bps non-directional, min_hold 30 s.
- Exits: strategy exit (ε crosses exit threshold / microprice vs VWAP band), TP 10 bps,
  hard stop max(75 bps, 1.5σ_5m), 15:50 ET curfew. Sizing $200 risk/trade, [1, 5000] shares.

No parameter of the primary rule is re-tuned. Ever. (That re-tuning is engineV2-dead.)

## 3. The system under test (all deltas declared here)

1. **Execution maker-first**: entry via passive limit at bid (long) / ask (short), M3 fill
   realism (odd-lot fill retraction, maker-book stress rules, cancel-if-unfilled window
   60 s); unfilled = no trade. Taker columns computed in the same run for attribution only.
2. **Hold ceiling**: max_hold ∈ {30 m, 2 h, 4 h} (declared axis; engineV2 tp/stop unchanged).
3. **Supporting gates** (both must pass at trigger; from event_bars1s / bbo1s features,
   decision-time only):
   - G1 dislocation quality: |micro_dev_bps| percentile ≥ p70 in-name trailing 60 d AND
     signed OFI agrees with trade direction.
   - G2 cost state: spread_bps ≤ trailing 60 d median AND σ_5m not in top decile.
   - M14 calendar strata (MONTH_END etc.): stratification columns only, not gates.
4. **Meta-label veto**: LightGBM P(win) on decision-time features (spread/vol state, OFI,
   micro_dev, time-of-day, ε/σ stretch, calendar), walk-forward by month, veto at P < 0.55
   (single declared τ, M8 precedent; no τ sweep). NN-on-bars stays banned.

## 4. Universe, data, splits

- Universe: registered tick universe [NVDA, TSLA, AMD, MU]. GOOGL excluded (not registered).
- Primary lake: bbo1s 2020-01→2026-05-31 (XNAS top-of-book, 1 Hz — label all fills XNAS-TOB;
  not SIP NBBO). Cost cross-check: MU SIP full tick 2024-01→2026-05-31 (cleanest series).
- Splits: dev = train+validate ≤ 2026-05-31 per config/settings.toml. HOLDOUT ≥ 2026-06-01
  sealed, untouched; consumed only by one frozen finalist on user sign-off.
- $0 new data spend.

## 5. Declared grid and trial accounting

- Cells: 4 names × 3 hold ceilings = **12 system cells**. Gates/τ/meta-features are fixed
  above, not swept. Baseline (bare-rule taker + bare-rule maker) columns fall out of the same
  runs at no extra trials — attribution rows, not verdict rows.
- Family inherits engineV2's ~160 reversion trials + ~21 enginev5.1 families for DSR context.
  MinBTL note: ~5.4 y dev supports ≤ 45 independent configs total; 12 declared. Any
  post-hoc extra cell requires a new registration.

## 6. Pre-registered bars (system verdict; pooled dev unless stated)

- B1 existence: combined-system net expectancy > 0 with day-clustered 95% CI excluding 0,
  ≥ 300 system trades pooled.
- B2 tail: still positive excluding top-5 P&L sessions (V5 kill-signal).
- B3 attribution: mandatory decomposition per trade — mid-alpha / spread paid-or-earned /
  latency / fees (engineV2's own lesson; no aggregate-only reporting).
- B4 filter value: meta-filtered vs unfiltered-conditioned expectancy delta > 0 (realized
  performance comparison, not spanning alpha), and vetoed-trade mean P&L < kept-trade mean.
- B5 fill honesty: maker fill rate reported per M3 rules; economics recomputed at 50% haircut
  on assumed queue priority must keep B1 sign.
- FAIL any of B1/B2/B5 → family obituary, no re-tune. B4 fail alone → system demotes to
  gates-only variant (declared fallback, same run).

## 7. Portfolio-combination gate (the doctrine layer)

- ρ-hypothesis: |ρ(daily P&L, champion classical stream)| < 0.2 on overlapping dev days
  (different window/mechanism).
- Measured book baseline (scout 2026-07-20, dev 2022-01-03→2026-05-29, n=1,049 overlap days,
  day-mean net_bps convention; robust ±0.05 across conventions): ρ(classical, meta) = 0.835;
  ρ(classical, portfolio) = 0.825; ρ(meta, portfolio) = 0.982. Book effective breadth ≈ 1.
  Daily Sharpe (unannualized): classical 0.174, meta 0.244, portfolio 0.249 = S_book.
  Implication: another champion refinement must beat 0.83 × S_book ≈ 0.21/day to add value;
  this sleeve at ρ ≤ 0.2 needs only > 0.05/day. That asymmetry is this family's justification.
- CAVEAT inherited from the same scout: M15's dev Panel A gated on the wrong column
  (M6-GBM continuous `pred` renamed to `p_win`; real M8 classifier gate gives n=2,844,
  mean ≈ +4.03 vs reported +3.08/n=3,956). ρ/S_book above use the REAL p_win gate. The
  forward REF_PORTFOLIO_BPS=+3.4 rests on the mislabeled gate — separate correction item,
  not part of this registration.
- Adoption bar if B1–B5 pass: incremental value per S_eff = (S_new − ρ·S_book)/√(1−ρ²) > 0,
  measured on realized daily P&L at the $10k research basis; runs as a SEPARATE sleeve
  (fourth forward stream next to M10's three), never blended into champion scores.

## 8. Deliverables

report.md (verdict vs bars), attribution table, per-cell economics, meta-model feature
importances + walk-forward stability, ρ row vs existing streams, ledger entries
(registered → result), obituary-or-promotion note in HANDOFF.
