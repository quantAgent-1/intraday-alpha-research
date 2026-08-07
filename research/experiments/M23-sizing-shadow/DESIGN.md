# M23 — dynamic-sizing shadow: harness design (frozen)

Architect design 2026-07-23; orchestrator rulings same day (authoritative mirror in the
registration's "Pre-data clarifications" block). Implements M3_REGISTRATION.md § M23
VERBATIM. REPORT-ONLY family: no gate, no look-state, no promotion rule; stateless
idempotent derived reports.

## 0. Rulings on the architect's ambiguities (A1–A8)

- A1 dev p_win = the OOS walk-forward column in `research/experiments/M8-meta-v1/
  oos_predictions.parquet` (leakage-free; the frozen-model-in-sample alternative is
  optimistic). Panel notes that forward uses the frozen model's stored p_win.
- A2 vol returns = SIMPLE close-to-close, ddof=1.
- A3 trailing-20 = 20 returns from 21 prior closes.
- A4 degenerate session (Σw_raw=0, all p<0.55): sized book falls back to EQUAL (Δt=0);
  participation is the meta family's object, this family measures pure allocation; count
  of such sessions reported.
- A5 three-M10-stream display panel = DAILY-aggregated session P&L.
- A6 base universe = classical (`taken_classical`, |basis|≥10, all p). Confirmed.
- A7 SR₀ = 0 everywhere in this family (Δt panel and display panel).
- A8 CI = `stress.clustered_mean_ci` by session on the daily Δt series (degenerates to
  ordinary bootstrap; intended). Seed 7, 2000 boots.
- Extra (reviewer-hardening): an off-anchor PSR unit test (SR₀≠0, ρ≠0, hand-derived) is
  REQUIRED so swapping bracket(SR₀) vs bracket(SR̂) cannot pass.

## 1. Key facts verified by the architect (contracts the build relies on)

- `forward_paper.LEDGER_SCHEMA` already stores per-(session,symbol): basis_bps, **p_win**,
  side, entry_px, exit_px, cross_px, net_bps, taken_classical, taken_meta, M15 columns.
  Forward path = read `research/forward/ledger.parquet` via `forward_paper.load_ledger()`;
  NO model reload; forward_paper.py NEVER modified; no write API imported.
- Equal-notional $-convention to match: `run_meta_trial.sizing_overlay` (lines ~152-192):
  pnl_$ = Σ notional_i·net_bps_i/1e4 with BOOK_NOTIONAL=10_000. M23 difference (mandated):
  renormalization is PER SESSION, not global-mean.
- Dev stream source: `research/experiments/M8-meta-v1/oos_predictions.parquet` (4,735 rows,
  2022-01-03..2026-05-29, cols incl. session, symbol, side, basis_bps, net_bps, p_win, fold).
- Vol source: `data/raw/sip/bars1d/{SYM}.parquet` raw closes, loaded like
  `run_basis_trial._load_daily_closes`. Do NOT reuse `moc_gbm.trailing_vol20` (log returns).

## 2. Modules

`src/enginev51/research_screens/sizing_shadow.py` — constants (UNIVERSE=champion 5;
P_CUT_LO=0.55, P_CUT_HI=0.60; TIER_LO/MID/HI=0.0/1.0/1.5; VOL_WINDOW=20;
VOL_CLIP_LO/HI=0.5/2.0; CANDIDATE_BASIS_BPS=10.0 imported-or-pinned to moc_meta's;
BOOK_NOTIONAL=10_000; DEPLOY_CAPITAL_USD=1200 report-only; ALPHA=0.05; seed 7/2000 boots)
+ functions per the architect's signatures: tier, vol_norm, trailing_raw_vol,
champion_sigma_med5, event_weights, matched_gross_notional, daily_paired_diff, sr_native,
sigma_sr, psr, min_trl, sizing_panel, stream_psr_panel, artifact writers.

`src/enginev51/apps/run_sizing_shadow.py` — click group: `dev-reference` and `forward`
subcommands; stateless; overwrite derived artifacts each run.

## 3. Statistics (ADIA Lab No.19; Pearson kurtosis MANDATORY)

bracket(SR) = (1+ρ)/(1−ρ) − ((1+ρ+ρ²)/(1−ρ²))·γ₃·SR + ((1+ρ²)/(1−ρ²))·((γ₄−1)/4)·SR²
sigma_sr(SR) = sqrt(bracket(SR)/T)
psr(sr_hat, sr0) = Φ((sr_hat − sr0)/sigma_sr(sr0))        # bracket at the BENCHMARK
displayed SE = sigma_sr(sr_hat)                            # bracket at the ESTIMATE
min_trl(sr_hat, sr0, α) = bracket(sr0)·(z_{1−α}/(sr_hat − sr0))²

scipy: `kurtosis(x, fisher=False, bias=False)`, `skew(x, bias=False)` — Normal ⇒ kurt≈3.
Golden anchor (must reproduce within abs 5e-3): (0.036%,0.079%,−2.448,10.164,0.2,24) →
SR*=0.456; sigma_sr(SR*)=0.379; PSR(SR₀=0)=0.966; MinTRL(α=.05,SR₀=0)=19.54.
Worked intermediates: bracket(SR*)=1.5+1.44186+0.51608=3.4579; bracket(0)=1.5;
Φ(0.456/0.25)=Φ(1.824)=0.9659; 1.5·(1.6449/0.4557)²=19.55.

## 4. Matched-gross renormalization (the doctrinal core)

Per session t: equal_notional_i = BOOK; sized_notional_i = BOOK·n_t·w_raw_i/Σ_t w_raw.
With T≡1, v≡1 ⇒ sized ≡ equal bit-identically ⇒ Δt ≡ 0 (the invariant test's hook).
Σw=0 session ⇒ ruling A4 fallback to equal, Δt=0, counted and reported.
Single-event sessions renormalize to equal (Δt=0) — signal lives in multi-event sessions;
report the multi-event session count so the panel's effective T is honest.

## 5. Artifacts — `research/experiments/M23-sizing-shadow/`

panel.md + panel.json: dev-reference and forward-to-date in STRICTLY SEPARATE sections
(L9-analog: no statistic ever mixes them; source tag + no-pool guard). Each section: daily
Δt table, mean + day-clustered CI, sr_native, PSR(SR₀=0), sigma_sr(SR*), MinTRL, T-to-date,
degenerate/single-event session counts, multiple-testing context line. Plus the
"M10 gate untouched — display only" PSR/MinTRL panel for classical/meta/portfolio streams
(daily-aggregated). Deploy lens = labeled informational column only.

## 6. Tests (`tests/test_m23_sizing_shadow.py`, synthetic only)

test_psr_mintrl_golden (abs 5e-3); test_psr_off_anchor (SR₀≠0, ρ≠0 hand-derived — bracket
swap must fail); test_kurtosis_pearson_convention; test_matched_gross_invariant;
test_matched_gross_degenerate_session (A4 fallback, no NaN/inf); test_vol_window_past_only;
test_vol_simple_returns_ddof1 (log-returns implementation must fail it);
test_raw_bars_pin; test_tier_pins (0.549→0, 0.55→1.0, 0.599→1.0, 0.60→1.5);
test_clip_pins; test_forward_ledger_read_only (no write API imported; source contains no
ledger write); test_holdout_guard_dev; test_clustered_ci_session_cluster;
test_dev_forward_never_pooled (source-tag guard raises on mixed frames).

## 7. Build order & reviewer attack list

Order: stats helpers+goldens → vol window → tier/norm/weights → matched-gross+invariant →
panels+writers+no-pool → CLI+guards. Reviewer attacks: (1) PSR evaluation-point swap;
(2) kurtosis convention; (3) per-session vs global normalization (reusing sizing_overlay's
global mean_pw would be silently wrong); (4) degenerate-session NaN poisoning the SR;
(5) dev/forward pooling; (6) any write path to the forward ledger.
