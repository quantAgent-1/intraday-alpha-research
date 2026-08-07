# LIVE SIGNAL ENGINE — design proposal v0 (2026-07-23, orchestrator)

Goal: a quant/statistical live layer that tracks market state during the scheduled windows
where our edges live and emits complete signals with realtime probabilities. Hard bounds:
signal-only (no code path routes orders, ever); imports REGISTERED artifacts only (no new
thresholds/models outside registration); staged per the ledgered data-decision framework
(buy nothing pre-gate). Status: PROPOSAL — engineering, not research; no ledger look
involved; build phases L0/L1 are $0 and gate-independent.

## 1. Architecture — one state machine, three input adapters

Core loop (window-scoped, dormant otherwise — the corpus says continuous-tape attention
pays us nothing at manual latency, so dormancy is a feature, not a gap):

- `SessionClock` — ET/DST-aware schedule: OPEN window [09:25–09:30], CLOSE window
  [15:50–16:00]; half-day aware (13:00 closes); everything else = dormant.
- `MarketState` — per-symbol snapshot store: latest NOII (near/far/ref/imbalance/paired),
  latest TOB (bid/ask), PIT context computed once pre-open from owned data (trailing-20
  raw vol, ADV20$, F/ADV from the LETF registry on public-date AUM). Append-only ring,
  every snapshot timestamped; no retro-mutation — PIT by construction.
- `SignalKernels` — pure functions IMPORTED from registered modules (the live_cockpit
  no-drift convention, proven): champion basis kernel (|basis|≥10 at 15:55:10), frozen-M8
  P(win) scorer, M23 tier×vol-norm sizing (report-only), CUSUM display state.
- `DecisionEmitter` — at each registered instant: freeze state → compute → emit a complete
  TradePlan (side/qty/order-type/limit/deadline per PLAYBOOK) + probability panel (p_win,
  tier size at deploy lens, expected net with CI) → append to a **signals journal**
  (append-only parquet; the live analog of the forward ledger).
- `Reconciler` (T+1) — joins yesterday's live emissions against forward_paper's replay of
  the same session. Divergence = data/keying alarm. This implements the ADIA lifecycle
  "live testing" stage: running PSR of live-vs-simulated (P[SR < SR_live | SR = SR_ref]),
  display-only — sequential monitors NEVER gate trading (that idea is 3× dead).

Input adapters (identical kernels, three sources — the same-pipeline guarantee):

- **A. ReplayAdapter ($0, now):** owned T+1 NOII/bbo1s drives the full loop in rehearsal.
  Acceptance bar: byte-agreement with forward_paper's replay on ≥20 sessions.
- **B. ManualAdapter ($3/mo, adoption-ready):** human reads a TotalView display (Webull
  $2.99 / moomoo free) at 15:55:05 and keys 3–4 numbers (near, ref/bid/ask); engine
  computes plan + probabilities in <1s; human keys the order (5–25s budget already in the
  economics). Deployable with the classical stream at $1k per the data framework.
- **C. FeedAdapter ($179/mo, GATED on adoption):** Databento live XNAS.ITCH imbalance —
  schema-identical to our lake, so every kernel runs UNCHANGED (this identity is why the
  program standardized on Databento historical). Auto-snapshots; still signal-only.

## 2. The statistical layer (what makes it a model, not a ticker)

- Realtime P(win): frozen m8_model.txt scored on the snapshot (<1 ms; already the meta
  stream's object).
- Realtime expectancy panel: E[net] from the dev win/loss distributions conditioned on the
  tier, shown WITH its CI — display, never a gate.
- ADIA-standard monitors: running native-frequency SR, PSR vs the dev reference, MinTRL
  countdown ("N sessions until this comparison means anything") for each stream — the
  honest antidote to reading three-day streaks.
- Sizing: M23 tiers × vol-norm at the $1k deploy lens (whole-share), report-only until
  M23's own MinTRL (~130 sessions) is satisfied and a NEW registration adopts it.

## 3. Scope fences

- No continuous scanning; dormant outside the two windows.
- No broker API, no routing — emissions are instructions for a human.
- No new signals/thresholds — anything new enters via registration, then gets a kernel slot.
- An OPEN-window instance exists only if an M24 descendant ever passes forward judgment
  (slot reserved, dormant; M24 closed BETWEEN — its ρ≈0 fact is why the slot stays).

## 4. Build plan

- **L0 (now, $0):** SessionClock + MarketState + kernel imports + ReplayAdapter + signals
  journal + `rehearse` command; acceptance = 20-session byte-agreement with forward_paper.
- **L1 (now, $0):** ManualAdapter as an upgrade of live_cockpit `decide` (3 keyed numbers →
  full plan + probability panel + checklist) + Reconciler + the ADIA monitor panel.
- **L2 (adoption-gated, $179/mo):** FeedAdapter, auto-snapshot at 15:55:10, window alerts.

L0+L1 serve the CURRENT program directly: rehearsal fidelity, Phase-0 support (the blotter
workflow gains the probability panel), and a shorter, safer path to live at adoption time.
L2 is deliberately unreachable until the three deployment gates pass.
