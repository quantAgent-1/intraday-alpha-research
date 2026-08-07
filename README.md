# intraday-research-engine

**Signal-only research system for plan-level economics: causal fills, sealed holdouts, registered experiments.**

A signal-only system that authors complete trade plans under real constraints
(human latency, limited concurrent slots, session curfew) and scores them with a
**causal fill model** — not a spreadsheet of mid prices.

This public repo is a portfolio build of a private research lab: core library,
tests, experiment tooling, and research notes. Market data and credentials are not included.

> **Project / repo name:** `intraday-research-engine` · **Python package (imports):** `enginev51`

| | |
|---|---|
| **Domain** | US equities, RTH, minutes-to-hours horizons |
| **Output** | Complete plans (side, entry, stop, targets, hold, confidence) |
| **Hard rule** | **No order routing.** Nothing here submits to a broker. |
| **Stack** | Python 3.13 · polars/numpy · LightGBM · optional PyTorch |

---

## For recruiters (60-second read)

**What I care about**

- Making **false edges die fast** (bad fills, leakage, unsealed holdouts, multiple testing)
- Building **measurement systems** that survive contact with tape, not just attractive IC plots
- Clear separation between **research gates** and report-only lenses (capital adequacy, sizing)

**What I built here**

- An event-time **plan replayer** with seeded manual latency on every leg
- A **PIT fill kernel** hardened after real phantom-edge failures (odd lots, off-market prints)
- A **protocol layer** (holdout seal, pre-registration ledger, constant tripwires) enforced in code + tests
- A large **registered research archive** — including closed families and null results

**How I work with AI agents** (summary; detail below)

I stay the architect and final authority on protocol, thresholds, and verdicts.
Agents implement and attack under written specs; results that matter are human-gated.

**Where to look if you have five minutes**

| If you care about… | Open this |
|---|---|
| Simulation correctness | [`src/enginev51/backtest/fills.py`](src/enginev51/backtest/fills.py), [`replay.py`](src/enginev51/backtest/replay.py) |
| Research integrity | [`src/enginev51/protocol.py`](src/enginev51/protocol.py), [`PROTOCOL.md`](PROTOCOL.md) |
| PnL auditability | [`src/enginev51/backtest/decompose.py`](src/enginev51/backtest/decompose.py) |
| Stats discipline | [`src/enginev51/stats/adia.py`](src/enginev51/stats/adia.py) |
| Test culture | [`tests/test_fills.py`](tests/test_fills.py), [`tests/test_protocol.py`](tests/test_protocol.py), [`tests/test_isolation_guard.py`](tests/test_isolation_guard.py) |
| Architecture map | [`ARCHITECTURE.md`](ARCHITECTURE.md) |

```bash
uv sync --extra dev
uv run pytest tests/test_fills.py tests/test_protocol.py tests/test_replay.py tests/test_decompose.py -q
```

Core kernels and protocol tests run **without** a market-data lake.

---

## Interests

| Interest | How it shows up in this repo |
|---|---|
| **Market microstructure & execution realism** | Limit/stop/target semantics, quote confirmation, condition filters, latency model |
| **Research design under multiple testing** | Pre-registration ledger, family counts, sealed holdout, one-look screens |
| **Systems that encode policy** | Seals and refusals as runtime errors, not wiki rules |
| **Causal, auditable simulation** | Strict event time; void/unfilled as first-class outcomes; PnL identity residual ≈ 0 |
| **AI-assisted engineering at high rigor** | Spec → implement → adversarial review → human gate (see workflow) |

Not a primary interest of this repo: broker integration, UI productization, or claiming a live deployable edge.

---

## Skills (with proof)

### Core engineering

| Skill | Evidence |
|---|---|
| Event-time / PIT correctness | Prevailing quote lookups guarded against wraparound; trade windows strictly after placement ([`fills.py`](src/enginev51/backtest/fills.py)) |
| Simulation design | k-slot admission at decision time, per-leg seeded latency, curfew force-flat ([`replay.py`](src/enginev51/backtest/replay.py)) |
| Numerical / data pipelines | Polars lake I/O, atomic partitions, multi-root primary-first reads ([`data/store.py`](src/enginev51/data/store.py)) |
| Testing as product | Hundreds of unit tests; isolation guards so tests cannot touch real lakes ([`tests/conftest.py`](tests/conftest.py)) |
| API / tooling | Click CLIs for backfill, trials, paper-signal shells under `apps/` |

### Quantitative research engineering

| Skill | Evidence |
|---|---|
| Cost-aware evaluation | Spread sampling, fee constants, stress arms ([`data/costs.py`](src/enginev51/data/costs.py), [`backtest/stress.py`](src/enginev51/backtest/stress.py)) |
| Walk-forward / OOS discipline | Seal boundaries, embargoed CV patterns, registered promotion rules |
| Model integration (not model worship) | LightGBM meta-gates, optional sequence encoder; promotion only on plan-level EV rules ([`PROTOCOL.md`](PROTOCOL.md)) |
| Reporting standards | Native-frequency SR, PSR, MinTRL ([`stats/adia.py`](src/enginev51/stats/adia.py)) |

### Judgment under uncertainty

Many registered families were **closed** after honest fills or powered nulls. The archive
keeps obituaries and coverage notes on purpose. The durable product is the **measurement
stack and the rules that force the truth**, not a single frozen strategy headline.

---

## Workflow with AI agents

This lab was built with a deliberate **human + multi-agent** loop. The goal is leverage
without diluting scientific control.

```
┌─────────────────────────────────────────────────────────────┐
│  HUMAN (orchestrator)                                       │
│  · problem framing & architecture                           │
│  · registration (hypothesis, gates, trial budget)           │
│  · thresholds, fill semantics, holdout / unseal decisions   │
│  · final audit & ledger verdicts                            │
└───────────────────────────┬─────────────────────────────────┘
                            │ written specs / acceptance criteria
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐
   │ Implementer │  │ Researcher  │  │ Adversarial      │
   │ agents      │  │ agents      │  │ reviewer agents  │
   │ code, tests │  │ literature  │  │ attack diffs,    │
   │ ports, CLIs │  │ modality    │  │ look-ahead,      │
   │             │  │ sweeps      │  │ protocol breaks  │
   └──────┬──────┘  └──────┬──────┘  └────────┬─────────┘
          │                │                  │
          └────────────────┼──────────────────┘
                           ▼
              human merge only after review
              economics only after registration
```

### Division of labor

| Role | Owns | Does **not** own |
|---|---|---|
| **Human** | Specs, protocol actions, gate outcomes, “what counts as a look” | Typing every mechanical port |
| **Implementer agents** | Code, tests, scaffolding from a frozen spec | Changing thresholds after seeing results |
| **Research agents** | Structured deep-research passes (academic / venue / practitioner / adversarial modalities) | Final family verdicts |
| **Adversarial agents** | Finding leakage, seal bypasses, fill bugs, silent look-ahead | Shipping without human audit |

### Operating rules (how rigor is preserved)

1. **Register before economics** — hypothesis, mechanism, features, gates, and budget land in
   [`research/ledger.jsonl`](research/ledger.jsonl) *before* results exist.
2. **Specs before agents code** — agents do not invent promotion rules mid-flight.
3. **Separate adversarial pass** — implementation and attack are different roles, not the same chat.
4. **Human-only irreversible decisions** — holdout unseal, family kill/pass, deployment stance.
5. **Agents don’t rewrite history** — no casual revert of tracked research artifacts they didn’t create.
6. **Incidents become guards** — every painful bug (phantom fills, lake isolation, stamp≠availability)
   is encoded as a permanent test + comment, not a Slack memory.

### Why this matters to employers

- Shows I can **direct** AI systems, not only prompt them for snippets  
- Shows I know where automation is safe (mechanical) vs dangerous (gates, labels, economics)  
- Matches how serious teams will ship software in an agent-assisted world: **spec → parallel work → review → human sign-off**

More detail (role cards, prompting patterns, anti-patterns):
[`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md).

---

## System shape

```
market data lake (optional local)
        │
        ▼
features / detectors / models ──► complete TradePlan
        │
        ▼
causal replayer (latency · k-slots · curfew · honest fills)
        │
        ▼
PnL decompose + stress + ADIA stats
        │
        ▼
research ledger / reports   (signal-only; no broker)
```

Deeper map: [`ARCHITECTURE.md`](ARCHITECTURE.md) · design intent: [`DESIGN.md`](DESIGN.md) ·
binding rules: [`PROTOCOL.md`](PROTOCOL.md).

---

## Quickstart

```bash
# Python 3.13+
uv sync --extra dev
# optional GPU encoder stack:
# uv sync --extra dev --extra gpu

cp .env.example .env   # only if you need vendor downloads
uv run pytest -q       # pure-logic surface does not need a lake
```

| | |
|---|---|
| **Credentials** | Local `.env` only — see [`.env.example`](.env.example). Never commit secrets. |
| **Data** | The multi‑GB research lake is **not** in git. Kernels and most unit tests still run. |
| **License** | [MIT](LICENSE) |

---

## Research archive (optional deep dive)

Under [`research/`](research/):

- Append-only **ledger** of registrations, results, and notes  
- Per-family registrations and reports  
- Multi-modality deep-research lanes and an exhaustion map  

Read this if you want process depth — **not** required to evaluate the engineering core.

---

## What this repository is not

- A live trading bot or broker integration  
- Investment advice  
- A claim that any strategy is currently deployable  
- A redistribution of proprietary market data  

---

## License & reuse

MIT — see [LICENSE](LICENSE). Contribution norms: [CONTRIBUTING.md](CONTRIBUTING.md).

If you fork the research process: **register before looking, seal the holdout, and never
promote on IC alone.**
