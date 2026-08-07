# M18 reversion_system_v1 — BUILD SPEC (harness only; no economics interpretation)

Author: orchestrator. Implementer: coding agent (Opus). Governing doc: REGISTRATION.md in this
directory (spec of record for rule, gates, cells, bars). This file specifies the CODE. Appendix A
(exact engineV2 formulas, verbatim) is inserted before the build is dispatched — placeholders
[A1]..[A11] refer to it. Any conflict between this spec and REGISTRATION.md → STOP and report.

## 0. Ground rules for the builder

- No parameter tuning, no added cells, no holdout access (assert max loaded ts ≤ 2026-05-31
  everywhere data enters), no commits, no result interpretation.
- Follow house conventions: loaders/partition style per `src/enginev51/data/store.py`; tests in
  `tests/`; ruff clean; suite must stay green (437+).
- Determinism: fixed seeds everywhere (LightGBM, any sampling); byte-stable outputs given same
  inputs.

## 1. Package layout (new: `src/enginev51/reversion/`)

| file | contents |
|---|---|
| `ou.py` | epsilon buffer (1 Hz, 300 samples/300 s), OU MLE (alpha, kappa=-ln(alpha)/dt, theta, sigma) [A6][A8]; recalibrate every 60 s; validity flag requires kappa>0, sigma>0, finite; session-boundary reset per [A8] |
| `thresholds.py` | smooth-pasting solver port [A6]: Kummer F± implementation, Brent on exit_long, reflection entry_long = 2*theta − exit_long; engineV2 failure/fallback semantics preserved |
| `features.py` | epsilon = mid − VWAP_5m [A7]; ofi_5s [A1]; rho_t [A2]; sigma_5m [A5]; microprice [A4]; vwap bands [A3]; 30-min trend filter [A10]; spread_bps; G1/G2 gate columns — trailing 60-session in-name percentile baselines ENDING AT SESSION t−1 (never same-day) |
| `signal.py` | entry/exit state machine: triggers + entry gates exactly per REGISTRATION §2–3; exit priority chain [A9]; max one open position per name; min_hold 30 s; 15:50 ET curfew force-flat |
| `fills.py` | fill models + fee model (§3 below) |
| `meta.py` | pooled LightGBM meta-label walk-forward (§4 below) |
| `runner.py` | cell runner (name × hold ceiling), emits per-event parquet (§5) |
| `apps/run_reversion_system.py` | CLI: `--cell NAME:HOLD`, `--all`, `--validate-anchor` |

## 2. Data substrate

- Primary: `data/raw/sip/event_bars1s/{SYM}/{YYYY-MM-DD}.parquet` (1 s bars with ohlc, volume,
  dollar_vol, ofi, micro_dev_bps, bid/ask/sizes, spread_bps, mid). Universe/windows:
  MU 2024-01-02→2026-05-31; NVDA, TSLA, AMD 2025-09-02→2026-05-31. RTH only.
- VWAP_5m = rolling Σ(dollar_vol)/Σ(volume) over trailing 300 s of bars, session-local,
  subject to [A7] exact semantics (update cadence, warmup).
- bbo1s is NOT used in the 12 verdict cells (reserved for a later declared diagnostic).

## 3. Execution / fills (all quantities per-trade, logged)

- Decision instant t0 = close of 1 s bar that triggers entry (all features from ≤ t0).
- MAKER ENTRY: post limit at current bid (long) / ask (short) starting bar t0+1. Filled at the
  limit price at the first bar where low ≤ limit (long) / high ≥ limit (short) — "touch" rule.
  Cancel if unfilled after 60 s. Unfilled = no trade (logged with reason).
- B5 sensitivity columns in the SAME run: (a) "through" fills only (low < limit strict / high >
  limit); (b) 50% of touch-only fills kept, deterministic hash of (sym, ts) — both re-price the
  same trade stream, no re-simulation of the state machine.
- TAKER EXITS (all exits): fill at opposite quote of bar t_exit+2 (≈2 s ≥ engineV2's 1500 ms
  latency). Exit reasons per [A9] priority; stop/TP breach tests per [A9] exactly.
- Fees: $0.005/share per side both legs; +0.5 bps slippage on taker legs only (engineV2
  REALISTIC preset [A10]). Maker legs: no slippage (price = limit), fees still charged.
- Sizing: engineV2 rule — shares = floor(200 / stop_dist_usd), stop_dist = max(entry×75bps,
  1.5×sigma_5m), clamp [1, 5000]. Also emit ret_bps on trade notional for comparability.
- Attribution per trade (mandatory columns): mid-to-mid P&L, spread paid/earned, latency cost
  (decision-vs-fill price drift), fees — engineV2 REPORT.md decomposition convention.

## 4. Meta-label (fixed design; no search)

- Pooled across names, LightGBM binary, label y = 1{net_bps > 0} (maker-entry system trade).
- Features (decision-time only): spread_bps, sigma_5m, |eps|/sigma_5m, ofi_5s, micro_dev_bps,
  time-of-day bucket (30-min), calendar strata (MONTH_END etc. per M14 definitions), name
  (categorical), kappa_hat, (eps−theta)/sigma_stationary.
- Walk-forward: train on pooled months [start .. m−1], score month m; first scored month =
  13th month of pooled trade history; retrain monthly. Persist fold models + feature
  importances under this experiment dir.
- Veto at p_win < 0.55, fixed. Gates-only fallback stream (no meta) logged in same run (B4).
- Leakage tests mandatory (§6).

## 5. Outputs (per cell → `research/experiments/M18-reversion-system/cells/{SYM}_{HOLD}/`)

`events.parquet` — one row per raw trigger with flags: passed_G1, passed_G2, meta_p, meta_kept,
maker_filled, fill_wait_s, plus full attribution columns and both B5 re-pricings; `summary.json`
— counts + pooled means per stream (raw-taker, raw-maker, gated, gated+meta) — NO verdicts;
runner also writes `report-skeleton.md` (tables empty of interpretation).

## 6. Tests (extend suite; all must pass before cells run)

1. OU MLE fixtures: hand-computed 10-sample series → exact alpha/kappa/theta/sigma.
2. Threshold solver: reproduces engineV2 known outputs [A6 fixtures if extracted]; reflection
   identity property (entry_long + exit_long = 2*theta) across random valid params.
3. No-lookahead: mutating any bar > t0 leaves the t0 decision and features unchanged.
4. Gate causality: G1/G2 percentile baselines use only sessions ≤ t−1.
5. Fill rules: synthetic bars covering touch/through/no-touch/cancel/curfew/min_hold.
6. Meta: fold boundaries — max(train ts) < min(score-month ts) for every fold.
7. Exit priority: synthetic cases where multiple exits trigger same bar → [A9] order wins.

## 7. HARNESS VALIDATION ANCHOR (gate before any cell is read)

Run `--validate-anchor`: TSLA, taker-entry bare-rule mode (no gates, no meta, engineV2 hold
defaults), event_bars1s window ∩ engineV2 TRAIN (2025-09-02→2026-03-01), REALISTIC preset.
PASS band [A11]: trade count within ±15% of engineV2's recorded n (=2508 on its tick data;
tolerance covers substrate difference), net $/trade within [−9.5, −5.5], mid-to-mid $/trade
within [−1.0, +1.5]. Outside band → STOP, report divergence, cells do not run.

## 8. Definition of done

All §6 tests green + full suite green + ruff clean; anchor §7 result reported (pass/fail only);
12 cells runnable end-to-end on MU smoke month (2024-02) with plausible row counts; NO cell
economics reported beyond summary.json emission. Hand back for orchestrator review.

---

# APPENDIX A — exact engineV2 semantics (extracted 2026-07-20; engineV2 repo is READ-ONLY
# reference — copy exact expressions from the cited file:line, never re-derive)

Port target = engineV2's **CPU backtest** semantics (`reversion_nb.py`, `event_loop_nb.py`,
`ou_mle_nb.py`, `riskgate_nb.py`), which cold-starts state daily and is the anchor's engine.
Where live and backtest differ, backtest wins.

- **A1 ofi_5s** (`hot/ofi.py:54-109`; `indicators_nb.py:205-345`): Cont-Kukanov-Stoikov L1
  events (e_bid − e_ask from bid/ask price-size transitions), rolling SUM over trailing 5 s.
  RAW SHARE UNITS — the ±1.0 neutral-zone gate is a 1.0-SHARE threshold, i.e. effectively a
  no-op; reproduce as-is (do NOT normalize; fidelity over sense). Our substrate: use the
  event_bars1s `ofi` column summed over trailing 5 bars IF
  `src/enginev51/apps/build_event_bars.py` implements CKS-per-second (builder: verify and
  state; fallback = CKS on successive 1 s L1 snapshots — declare which was used).
- **A2 rho_t** (`hot/imbalance.py:73`): instantaneous (bid_size − ask_size)/(bid_size +
  ask_size) from current L1, no window, ∈ [−1, 1]. From close-of-second sizes.
- **A3 VWAP bands** (`hot/vwap.py:105-116`): VWAP_300s = Σpv/Σv over TRADES; σ_vw =
  sqrt(Σv(p−vwap)²/Σv) same window; bands = vwap ± 1.5·σ_vw. On event bars, use per-second
  p_s = dollar_vol/volume: σ_vw ≈ sqrt(Σ v_s(p_s−VWAP)²/Σ v_s) — DECLARED deviation
  (within-second variance truncated); anchor §7 is the guard. Zero-volume bars update
  nothing in VWAP/ε.
- **A4 microprice** (`hot/lob.py:41-53`): raw = (bid_size·ask + ask_size·bid)/(bid_size+
  ask_size); quotes with bid_size+ask_size < 100 REJECTED (state holds prior); consumed value
  = sticky MEDIAN of last 3 accepted raws. On 1 s bars: apply per-bar (declared approximation
  of per-quote cadence).
- **A5 sigma_5m** — MISLABELED in engineV2 contracts: it is NOT a returns std. It is an alias
  of A3's σ_vw, ABSOLUTE DOLLARS (`loop.py:184`; `event_loop_nb.py:280-281`;
  `strategy_api.py:80`). Feeds stop distance max(entry·75 bps, 1.5·σ_vw), trailing offset
  2.0·σ_vw floored at 20 bps of entry, and sizing. Implement exactly this aliasing.
- **A6 solve_thresholds** (`ou_calibration.py:180-225`; `ou_mle_nb.py:264-297`): inputs
  (κ, θ, σ from MLE; discount ρ=0.01 — NOT A2's rho; c=0.0008 in $ of ε). Use
  scipy.special.hyp1f1 + scipy.optimize.brentq (xtol=1e-8, maxiter=100). Only exit_long is
  solved; entry_long = 2θ − exit_long; exit_short = entry_long; entry_short = exit_long.
  Bracket/expansion/safe-limits: copy verbatim from cited lines (incl. the exact σ_eff
  expression used there). FAILED SOLVE → thresholds NaN → entries blocked until the next
  successful calibration (backtest `is_fresh` semantics, `event_loop_nb.py:172-175`). Do not
  "fix" this into carrying stale thresholds.
- **A7 ε sampling** (`hot/loop.py:119-121`, `ou.py:90-110`): ε = mid − VWAP_300s, computed on
  trade activity only (zero-volume bars: no new sample); calibration ring stores ≤1 sample/s;
  ring evicts >1200 s; calibration every 60 s consuming latest 300 samples; ATTEMPT gate
  n ≥ 300 (backtest `OU_MIN_SAMPLES`, not live's 30). κ = −ln(α̂)/Δt; require κ>0, σ>0 finite.
- **A8 session boundaries**: cold-start ALL indicator/OU/risk state every session (backtest
  `WorkerJob` semantics). VWAP warm gate: ≥30 trades AND ≥60 s. Practical consequence: no
  entries before ~09:35 anyway; plus blackouts below.
- **A9 risk/exit engine** (`riskgate_nb.py:209-287`): tested on A4 sticky microprice, every
  bar, point-in-time level test (no intrabar high/low breach). Priority: TP(+10 bps) → hard
  stop → trailing (activates after +250 bps, trails 2.0·σ_vw) → max_hold deadline. Strategy
  evaluation order within a bar: ENTRY-long → ENTRY-short → EXIT-long → EXIT-short, first
  hit wins (an entry proposal suppresses same-bar strategy-exit generation). Risk gate runs
  BEFORE strategy each bar; a risk close stamps cooldowns that deterministically block
  same-bar re-entry. Cooldowns: 5 s after any close, 60 s after a stop. Entry blackouts:
  09:30–09:40 and 15:50–16:00 ET (`params.py` RiskDefaults — NOT the stale SQL seed values).
  Curfew force-flat 15:50 ET (backtest-only concept; we keep it, reason code force_exit=6).
  Exit-reason codes: 1 tp, 2 hard, 3 trailing, 4 max_hold, 5 strategy, 6 force.
- **A10 costs** (`archive/research/goal_run/costs.py:38-54`): REALISTIC = 0.5 bps/side
  slippage on notional + $0.005/share per side, both legs, applied POST-HOC to trade records
  (do not bake into fill prices). Our maker legs: fees yes, slippage no (maker price is the
  limit). Trend filter: |mid − vwap_30m|/vwap_30m·1e4 > 50 bps blocks BOTH sides; vwap_30m =
  same VWAP class, 1800 s window, no bands.
- **A11 anchor numbers** (TRAIN 2025-09-02..2026-03-01, TSLA, RiskDefaults, GROSS/REALISTIC):
  n = 2508; gross −$4.293/trade; net −$7.533 (REALISTIC, inferred-confident); mid-to-mid
  +$0.25; avg shares 60.8. §7 PASS bands: n within ±15% of 2508; gross/trade ∈ [−5.5, −3.0];
  net/trade ∈ [−9.5, −5.5]; mid-to-mid ∈ [−1.0, +1.5]; shares ∈ [48, 74]. Do NOT compare to
  the 3991-trade full-history run (different window).
