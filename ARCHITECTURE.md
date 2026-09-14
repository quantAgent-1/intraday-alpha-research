# Architecture

Public map of **Intraday Alpha Research** (Python package: `enginev51`).
For binding rules, see `PROTOCOL.md`. For design rationale, see `DESIGN.md`.

---

## 1. System shape

The project is a **signal-only** research stack for RTH, minutes-to-hours horizons.
Plans are complete enough for a human to key manually; simulation charges **seeded
latency at every leg**, k concurrent slots, and a session curfew.

```
                    ┌─────────────────────────────────────┐
                    │         protocol.py (seal)          │
                    └─────────────────────────────────────┘
                                      │
   lake ──► data/* ──► features / events / models ──► plans
                                      │
                                      ▼
                            backtest/replay (causal)
                                      │
                          decompose + stress + stats
                                      │
                          apps/* CLIs + research ledger
```

**Hard rule:** nothing in this repository submits orders.

---

## 2. Layers

### 2.1 Protocol (`enginev51.protocol`)

- Fixed train / validate / holdout dates (holdout sealed by default)
- `apply_seal(df)` strips holdout sessions from research frames
- `refuse_end_on_or_after_holdout(end)` for date-arg CLIs
- Append-only research ledger helpers
- `assert_protocol_consistent()` tripwire for gate/capital/fee copies

### 2.2 Data (`enginev51.data`)

| Module | Role |
|---|---|
| `store` | Atomic parquet partitions, multi-root primary-first reads, `.empty_ok` sidecars |
| `alpaca_hist` | Historical SIP REST client (bars/trades/quotes) |
| `backfill` | Resumable download planner with content-completeness checks |
| `noii` / `bbo1s` | Optional Databento acquisition for auction microstructure |
| `qa` | Coverage / gap / cross-source (bar-vs-tape, BBO-vs-SIP) audits |
| `costs` | Round-trip cost table from sampled NBBO spreads + fees |
| `calendar` | NYSE session bounds |

Dual-root reads are **optional**: primary `data/raw` always; a secondary root only if
`ENGINEV51_LEGACY_DATA_DIR` is set.

### 2.3 Backtest (`enginev51.backtest`)

| Module | Role |
|---|---|
| `fills` | PIT primitives: limit / market / stop / target |
| `latency` | Deterministic per-(plan, leg) human delay |
| `tape` | Session tape load + condition filters + spread widen for stress |
| `replay` | Causal plan replayer (k-slots, curfew, void/unfilled first-class) |
| `auction_replay` | Closing-cross path (historical auction research) |
| `decompose` | Exact PnL identity into mid / latency / spread / fees |
| `stress` | Day-clustered CIs, power tables, robustness arms |

### 2.4 Events, features, plans

- **Event bars:** 28-channel 1-second bars for sequence models
- **Detectors:** named payers (gap MR, LETF window, VWAP magnet, cascade, expiry pin)
- **Constructor A0:** detector state → complete `TradePlan`
- **Overlays:** optional LGBM / encoder reprice-or-skip on top of A0

### 2.5 Models

- LightGBM walk-forward utilities
- Closing-auction meta-labeling (historical line)
- Optional GPU encoder (TCN / PatchTST) on event streams
- Reversion harness (historical system port)

### 2.6 Stats

- `stats.adia` — ADIA Lab Paper No.19 SR / PSR / MinTRL kernels
- `stats.report` — house day-clustered CI wrapper for new screens

### 2.7 Apps (`enginev51.apps`)

Click CLIs for backfill, event-bar build, trial runners, paper-signal shells, and
research screens. Treat as **research tooling**, not production deployment.

---

## 3. Two historical pipelines (museum + reusable kernels)

### Continuous plan pipeline

```
lake → detectors → TradePlan → causal replay → research book
```

Used for named-payer / overlay ablations. Many families closed after honest fills;
kernels remain reusable.

### Auction pipeline (frozen under project direction in the private program)

```
NOII + quotes → basis / imbalance features → auction_replay → meta gate
```

Retained for mechanism study and fill-ground-truthing lessons. Public docs do not
claim a live deploy routine.

---

## 4. Research corpus (`research/`)

| Path | Contents |
|---|---|
| `ledger.jsonl` | Append-only trial registry |
| `experiments/` | Per-family registrations and reports |
| `deep/` | Multi-modality deep-research lanes + exhaustion map |
| `COST_MODEL.md` | Cost realism notes |

Some experiment directories may reference private-run artifacts that are not in this
repo (parquet panels, models). Reports and registration prose remain for audit trail.

---

## 5. Configuration

| File | Role |
|---|---|
| `config/settings.toml` | Universe, execution, splits, books, costs |
| `.env` (local only) | API keys |
| `config/letf_aum.toml` | LETF AUM anchors for rebalance-demand estimates |

Research book notional (default **$10,000** per plan) is the **gate currency**.
The small-account lens (default **$1,000**) is **report-only** and must not steer learning.

---

## 6. Testing

```bash
uv run pytest
```

`tests/conftest.py` sandboxes secondary-lake and credential paths so the suite cannot
touch real external lakes or secret files. Data-dependent integration tests require a
local lake and will skip or fail without it — that is expected in this public build.
