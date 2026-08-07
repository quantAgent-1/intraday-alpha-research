# daily_swing_v1 — daily 1d/3d/5d side-ledger (research-only)

Registered daily side-ledger family (PROTOCOL v6 §2). NO plan-level claim, NO ledger write, NO dashboard; the deployable system never holds overnight. rank-IC bookkeeping only — the orchestrator owns any verdict.

## Setup

- feature_version: v1
- universe: 12 bar_signal names, one near-close row per session
- near-close row modal ET time (NVDA): 15:55:00
- pooled pre-holdout sessions: 720 (holdout >= 2026-06-01 stripped BEFORE label shift)
- labels: l_fwd_{h}d = log(close[t+h]/close[t]), SESSION-INDEXED (calendar-safe); z = label / (f_vol20 * sqrt(h))
- horizons: [1, 3, 5]  (longest 5d)
- model: pooled cross-symbol LightGBM per horizon (lgbm.DEFAULT_PARAMS)
- CV: purged expanding walk-forward, embargo_sessions=6 (> longest horizon 5), 23 folds
- wall time: 3.1s

## Pooled cross-sectional rank-IC (day-clustered 95% CI)

Per session: Spearman(pred, realized z) across the ~12 names; one value per
session, bootstrapped over sessions (the day cluster).

| horizon | mean_IC | CI_lo | CI_hi | n_sessions | n_rows | pos_share |
|---------|---------|-------|-------|------------|--------|-----------|
| 1d | +0.0375 | +0.0066 | +0.0675 | 429 | 5628 | +0.5455 |
| 3d | +0.0111 | -0.0201 | +0.0420 | 408 | 5604 | +0.4975 |
| 5d | -0.0190 | -0.0526 | +0.0122 | 383 | 5580 | +0.4804 |

## Per-symbol time-series rank-IC — NVDA / TSLA (grok E5 arm)

Per symbol: Spearman(pred, realized z) across the symbol's OOS sessions;
session-resampled bootstrap CI.

| horizon | symbol | mean_IC | CI_lo | CI_hi | n_sessions | grok_E5_claim |
|---------|--------|---------|-------|-------|------------|---------------|
| 1d | NVDA | +0.0407 | -0.0505 | +0.1340 | 469 | +0.27 |
| 1d | TSLA | +0.0415 | -0.0509 | +0.1284 | 469 | +0.23 |
| 3d | NVDA | +0.0156 | -0.0743 | +0.1062 | 467 | - |
| 3d | TSLA | +0.0099 | -0.0815 | +0.0975 | 467 | - |
| 5d | NVDA | -0.0930 | -0.1791 | -0.0029 | 465 | - |
| 5d | TSLA | -0.0370 | -0.1290 | +0.0505 | 465 | +0.45 |

## grok E5 comparison

grok E5 reported per-symbol time-series ICs on ~43 sessions: TSLA 1d 0.23, TSLA 5d 0.45, NVDA 1d 0.27. Pre-registered expectation was that these are materially LOWER on 450+ OOS sessions (a short, favourable window over-states IC). Measured here:
- TSLA 1d: +0.0415 vs grok 0.23
- TSLA 5d: -0.0370 vs grok 0.45
- NVDA 1d: +0.0407 vs grok 0.27

CONFIRMED: every measured per-symbol IC is materially below the grok E5 claim, consistent with those figures being small-sample (~43 session) over-statements.

## Notes / judgment calls

- The holdout is stripped BEFORE the session shift, so no pre-holdout label can reference a sealed close; holdout rows and labels are excluded entirely.
- evaluate.per_session_ic gates sessions at n>=30 rows (intraday-calibrated) and returns ZERO daily cross-sections (only ~12 names/session). The pooled metric mirrors its Spearman-on-ranks formula with min_symbols=5 and reuses evaluate.bootstrap_mean_ci for the day-clustered CI.
- Per-symbol ICs are time-series (one row/session), so per_session_ic is inapplicable there; a session-resampled bootstrap is used.
- Research-only: no ledger write (orchestrator owns verdicts), no plan-level economics, no dashboard.
