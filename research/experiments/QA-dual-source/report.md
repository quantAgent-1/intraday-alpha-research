# Cross-source dual-feed QA — "backtest runs properly on both feeds" as a tested property

**Date:** 2026-07-21. Executor: one Opus agent (seam inventory + QA tooling + smokes);
filed by the orchestrator (subagent file-write restriction). Follows
`research/SIM_AUDIT_2026-07-21.md`. Touched: `src/enginev51/data/qa.py`
(+`bar_tape_offset`, `bbo_quote_agreement`, `cross-source` CLI),
`tests/test_qa_cross_source.py` (9 tests), this report.

## Headline

**Seam verdict: CLEAN across all 5 axes** (ts epoch/unit, tz/ET, price scale,
symbol case, half-day calendar) — with two latent low-severity findings (F-A, F-C)
and one repo-hygiene finding (F-B, fixed at filing time). F1's fix is empirically
confirmed: bar-VWAP vs raw-tape offset now +0.02..+0.03 bps (was −12 / −5.75).
All four end-to-end smokes exit 0. Full suite **539 passed** (+9 new).

## Seam inventory

The A0 detector/plan/replay family is Alpaca-only; cross-vendor fusion lives in the
MOC/auction family:

| # | Seam | Alpaca side | Databento side | Fused how |
|---|------|-------------|----------------|-----------|
| S1 | `apps/run_moc_trial.py:189-261` | session tape, adv20_dollars, cross price, closes | NOII session, signal_at, bbo-1s tape | NOII side/size × Alpaca $ADV → norm_imb; entry on Alpaca ticks or bbo-1s; exit at Alpaca official close |
| S2 | `backtest/auction_replay.py:168-438` | adv20, closing cross, official closes | `tape_from_bbo` SessionTape | replay crosses prevailing quote at signal+latency; exit at official close |
| S3 | `apps/forward_paper.py:206-413` | `_extend_bars1d` (raw, pinned), tick backfill | `download_noii`/`download_bbo1s` | daily forward collection; ledger append idempotent |
| S4 | `data/qa.py` (new) | bars1m VWAP + raw-trade VWAP | — | the F1 price-scale tripwire |

Per-axis receipts (verified in source): epoch = UTC ns Int64 everywhere
(`alpaca_hist.py:34-49,157`; `noii.py:161-168`; `bbo1s.py:159-166`); ET via
`America/New_York` + pandas_market_calendars, DST-proof; price scale raw via
primary-first shadowing (`store.py:103-121`) with every signal-symbol consumer
resolving the new raw lake; symbols uppercased at ingest+path; half-days: the
15:45-16:00 NOII window is empty on ~13:00 closes → session skipped, never
mis-priced.

## Findings

- **F-A (latent, price-scale tails).** The raw refetch spans 2024-01→2026-05; the
  legacy adjusted lake spans 2023-07→2026-07. Two tails still resolve adjusted:
  (i) 2023-07..2023-12 — no current claim reaches it; any future A0 trial into
  2023-H2 must refetch first. (ii) 2026-06..07 — only touched by the forward
  clock's `adv20_dollars` denominator (~0.1% dividend scaling, ≪ the 0.05%/0.10%
  ADV thresholds) — benign but real. Close by refetching the tails raw or
  computing ADV off bars1d.
- **F-B (repo hygiene — FIXED at filing).** The unanchored `.gitignore` rule
  `data/` also shadowed the SOURCE package `src/enginev51/data/` — the entire
  data layer (alpaca_hist, noii, bbo1s, store, calendar, backfill, costs, qa) was
  never in version control. Rule anchored to `/data/`; package tracked as of
  Session 5 pt9. Lesson: never use unanchored directory patterns in .gitignore.
- **F-C (MU bbo-quote WARN — investigated, NOT a defect).** Full-day XNAS-TOB vs
  SIP-NBBO mid gap on the wide-spread mid-cap (2.5t / 1.5t medians) collapses to
  0.5-1.0t in the 15:50-16:00 window the MOC family actually consumes; NVDA 0.0t
  everywhere. The check is an honest tripwire; optionally sample only the
  consumption window for MOC symbols.

## QA CLI real-runs

```
NVDA 2026-05-15  bar-tape PASS +0.0322 bps (n=390) | bbo-quote PASS 0.000t max 1.000t  -> PASS
MU   2026-05-15  bar-tape PASS +0.0251 bps (n=390) | bbo-quote WARN 2.500t max 11.500t -> WARN (F-C)
NVDA 2026-02-17  bar-tape PASS +0.0223 bps (n=390) | bbo-quote PASS 0.000t max 0.500t  -> PASS
MU   2026-02-17  bar-tape PASS -0.0106 bps (n=390) | bbo-quote WARN 1.500t max 10.000t -> WARN (F-C)
```

Old-lake offsets at the same probes were −11.64 / −1.51 / −12.16 / −5.75 bps.

## End-to-end smokes (merged code + corrected lake, 2026-02-17..18)

- A0 `run_trial` (5 symbols, k=2, seed 7): exit 0, 10/10 symbol-sessions, 36 plans, 16 taken.
- MOC `run_moc_trial` (threshold 5 bps, seed 7): exit 0, 10 events, 0 no-cross, 0 void.
- Forward clock: `status` exit 0; `run --asof 2026-07-17` exit 0 and idempotent
  (downloads skipped 5/5, bars1d appended 0, ledger 5→5 unchanged).
- Full suite: **539 passed, 0 failed**; ruff clean on touched files.

## Bottom line

The two-feed merge is verified clean at every seam over the refetched window; the
F1 class is now guarded by a permanent CLI (`python -m enginev51.data.qa
cross-source --symbol NVDA --session 2026-05-15`) and synthetic-frame tests. Open
items: F-A tails (low), F-C optional window-scoped sampling (cosmetic).
