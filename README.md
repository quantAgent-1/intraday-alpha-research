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

## Overview

**Focus**

- Making **false edges die fast** (bad fills, leakage, unsealed holdouts, multiple testing)
- Building **measurement systems** that survive contact with tape, not just attractive IC plots
- Clear separation between **research gates** and report-only lenses (capital adequacy, sizing)

**What is in this repo**

- An event-time **plan replayer** with seeded manual latency on every leg
- A **PIT fill kernel** hardened after real phantom-edge failures (odd lots, off-market prints)
- A **protocol layer** (holdout seal, pre-registration ledger, constant tripwires) enforced in code + tests
- A large **registered research archive** — including closed families and null results

**AI-assisted development** (summary; detail below)

The human remains architect and final authority on protocol, thresholds, and verdicts.
Agents implement and attack under written specs; results that matter are human-gated.

**Key paths**

| Topic | Location |
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

## Research program (M-series)

Each family was **pre-registered** (hypothesis, mechanism, gates) before economics when
the protocol required it. Full narrative — what each strategy tried, how it worked, and
the ledger outcome — is in:

**[`docs/STRATEGIES.md`](docs/STRATEGIES.md)**

### Arc

| Phase | IDs | What we were testing |
|---|---|---|
| Continuous named payers + ML | M3–M5 | Hours-scale plans on gap / LETF / VWAP / cascade / pin; LGBM & GPU overlays |
| Closing auction | M6–M15 | NOII / near–mid basis into the official cross; meta-gate; mechanism; breadth |
| Execution & reversion | M16–M18 | Manual E/Q audit, flow book, OU reversion *as a system* |
| Intraday after close ban | M20–M27 | Macro windows, open fade, gap-day, earnings×close, sizing shadow |
| Powered batteries / OOS | M28–M30 | Open-cross bar signals, short-ratio, retail-flow fade on virgin names |

### Index (status at a glance)

| ID | Strategy (one line) | Status |
|---|---|---|
| **M3** | Named-payer detectors → complete plans under causal replay | **Closed** — edge did not survive honest fills |
| **M3-A1** | Bar-tier LGBM veto / leg reprice on M3 | **Fail** |
| **M4** | TCN/PatchTST on 1s event bars (select / reprice plans) | **Fail** |
| **M5** | Stage A promotion gate on continuous book | **Fail** (holdout not used) |
| **M6 / FINAL** | Close auction: \|near−mid\|≥10 bps @15:55:10 → cross | **Pass + holdout pass** → later **frozen/banned** as a direction |
| **M6b** | Open auction WITH-imbalance | **Fail** |
| **M7** | Daily megacap cross-sectional reversal | **Fail** |
| **M8** | Meta-label: take classical basis only if P(win)≥0.55 | **Pass** (walk-forward OOS) |
| **M8-v2** | Add LETF mechanism features to M8 | **Kill** |
| **M9** | Auction path features + calibrated sizing | **Null** / no sizing Sharpe gain |
| **M10** | Forward paper clock on frozen close signals | Partial; stopped with ban |
| **M11** | Frozen close rule on 28 never-fit Nasdaq names | **Fail** — edge is name-narrow |
| **M12** | Why name-selective? LETF flow vs index weight | **LETF flow wins** |
| **M13** | Hedge close-window common factor | Not adopted |
| **M14** | Calendar strata (month-end, opex, …) | Diagnostic only |
| **M15** | Top-3 by p_win portfolio shadow | Report-only |
| **M16** | Phase-0 manual E/Q audit + LETF flow book | Audit / **between** |
| **M17** | Slow CS / factor momentum (research-only) | Between / replication pass |
| **M18** | OU reversion + gates + maker + meta as a *system* | **Fail** |
| **M20** | Macro release-window continuation screen | **Spent** (validate confirm fail) |
| **M21** | Earnings crowded-setup regimes | Diagnostic |
| **M22** | Earnings day × closing basis | **Between** |
| **M23** | Dynamic sizing vs equal notional (ADIA stats) | Report-only |
| **M24** | Fade open near–ref into close | **Between** |
| **M25** | Calendar overlay on close stream | Withdrawn |
| **M26** | 13:02 Treasury results forward | Parked / unbuilt |
| **M27** | Fade large gaps (low-ADV semis) | **Kill** (mid-alpha real; cost ~2×) |
| **M28** | 14 bar signals, wide panel, open-cross structure | **Null-at-admission** |
| **M29** | Short-ratio signals, same structure | **Null-at-admission** |
| **M30** | Retail odd-lot fade OOS (16 virgin names) | **Not-confirmed** |

**How to read this:** a long list of **fails and nulls is intentional**. The process is
designed so weak ideas die with a receipt. The durable engineering is the fill/replay
stack and protocol; the durable *structure* finding is cheap open-cross → late-day exit
(~1–3 bps all-in) even when signals miss.

Related prong-0 kills (**F1** depth footprint, **F2** buyback, **F3** opening residue)
are written up in [`docs/STRATEGIES.md`](docs/STRATEGIES.md).

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

## Research archive

| Path | Contents |
|---|---|
| [`docs/STRATEGIES.md`](docs/STRATEGIES.md) | **Strategy-by-strategy explanations (M3–M30)** |
| [`research/ledger.jsonl`](research/ledger.jsonl) | Append-only registrations and results |
| [`research/experiments/`](research/experiments/) | Per-family reports and registrations |
| [`research/deep/`](research/deep/) | Deep-research lanes + [`EXHAUSTION_MAP.md`](research/deep/EXHAUSTION_MAP.md) |

Use the strategies page for orientation; use the ledger/experiments for receipts.

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
