# Intraday Alpha Research — Design

> Public name: **Intraday Alpha Research**. PROTOCOL.md = binding rules.
> ARCHITECTURE.md = package map. This file = why the engine is shaped this way.

## Mission

Minutes-to-hours, RTH-only, flat-by-close engine that authors **complete trade plans**
(side, entry, stop, targets, hold window, expected magnitude, confidence, market-vs-limit)
for manual execution (5–25 s human latency). Hybrid classical + ML with optional CUDA GPU training.
North star: honest positive net expectancy on the k-slot taken plan stream.

## Why shaped this way (predecessor evidence)

- engineV2: sub-15-min taker signals are mid-neutral; the crossed spread was the entire loss.
- engineV5: bar-tier 30m–4h LightGBM IC is real (+0.03–0.05, CI>0) but a 2-slot manual account
  monetizes ~none of it; bar-tier information is exhausted by trees; passive limit entries earn
  +2.21 bps [2.09, 2.34] vs crossing — a banked execution fact.
- Therefore Intraday Alpha Research is **not** a re-run: it changes the horizon (hours-end, σ√h ≫ spread),
  the trigger (named-payer flow states, not always-on forecasts), the data tier for ML
  (raw tick/quote event stream), the objective (plan-level economics under deployment reality),
  and the execution prior (limit-first).

## Five pivots

1. **Hours-end horizon (1–4 h):** per-trade σ√h 50–150+ bps vs 3–5 bps RT cost; attack the √N
   constraint via per-trade edge and selectivity (~0.5–1.5 taken plans/session portfolio-wide,
   sized for statistical power: N≥250 over ≥150 sessions).
2. **Named payers:** plans are authored only when a documented flow state is active —
   opening-gap MR, LETF close-rebalance pressure, VWAP magnetization, cascade/V-reversal
   exhaustion, expiry pinning. Classical detectors (`events/detectors/`) compute the state.
3. **GPU on the event stream:** multi-task encoder on tick/quote sequences (the tier trees never
   saw). Leg-pricing heads (MFE/MAE quantiles, first-passage barriers, fill-prob/adverse-selection,
   RV) train unconditionally — they price plan legs; directional heads must beat LGBM on
   plan-level EV in registered ablations (A0 classical → A1 +LGBM → A2/A3/A4 encoder arms).
4. **Plan-level objective:** the causal replayer (k slots, seeded latency at every leg, L2-strict
   limit fills, curfew) is the only source of economics. P&L decomposes into mid-alpha +
   spread paid/earned + latency drag on every fill.
5. **Limit-first execution:** market-vs-limit is a modeled recommendation per plan (fillnet).

## Universe & data

Plan authoring: tick-covered names only (NVDA, TSLA + AMD, MU after backfill). 16-name bar lake
(engineV5, reused read-only) = context features. LETFs (SOXL/SOXS/TQQQ/SQQQ) = deploy lens only.
GEX/dealer-gamma: no historical OI exists → forward-collect snapshots from M1; excluded from
Stage A gates. Databento deferred until an edge plausibly scales with depth data (user approves
any spend).

## Books

Research book (gate currency): $10k/plan, underlying stock, long/short/flat.
Small-account lens (report-only): example $1000 whole-share / LETF translation for capital
adequacy reporting only. One-way flow: plans → report lens. Never backwards into learning.

## Working mode

Research process: register hypotheses before economics; adversarial review of builds;
protocol actions and gate verdicts stay explicit and ledgered.

## Milestones

M0 scaffold/ports → M1 data (backfills, QA, 1s event bars, flow collectors) → M2 causal
plan replayer + fills + stress + power → M3 detectors + A0/A1 (registered) → M4 GPU encoder
ablations (gated) → M5 Stage A verdict + holdout ceremony → M6 dashboard + forward paper gate.
