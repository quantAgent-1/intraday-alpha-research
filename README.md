# intraday-research-engine

**A research lab for testing stock-trading ideas honestly — without placing real orders.**

> **Tagline:** Signal-only research for plan-level economics: realistic fills, sealed holdouts, registered experiments.

---

## Picture this in your head

Imagine you want to answer:

> “If I traded this idea by hand during market hours — with a few seconds of delay,
> only two trades open at once, and I must be flat by the afternoon — would I make money
> *after* spreads and fees?”

Most backtests skip that question. They use mid prices, ignore delay, or “fill” on
prints that a real limit order would never get.

**This project is the software that asks the hard version of the question.**

```
  Idea for a trade
        │
        ▼
  Write a full plan
  (buy/sell, entry, stop, targets, when to quit)
        │
        ▼
  Replay against historical quotes & trades
  as if a human typed the order 5–25 seconds later
        │
        ▼
  Score the plan: profit, costs, and what went wrong
        │
        ▼
  Log the result in a research ledger
  (pass, fail, or “not enough evidence”)
```

**Important:** the code never sends orders to a broker. It only *simulates* and *records*.

| | |
|---|---|
| **Market** | US stocks, regular trading hours |
| **Horizon** | Minutes to a few hours (same day, flat by close) |
| **Output** | Complete trade plans + measured P&amp;L under realistic rules |
| **Code package** | `enginev51` (Python 3.13) |

This public GitHub tree is a cleaned portfolio build of a larger private lab.
Market data files and API keys are **not** included.

---

## What problem it solves

Amateur and even many “pro” backtests look profitable for the wrong reasons:

1. **Fake fills** — counting tiny or delayed prints as if you traded there  
2. **Looking into the future** — using prices or labels that weren’t knowable yet  
3. **Trying too many ideas** — then reporting the one that “worked”  
4. **Ignoring costs** — especially on less liquid names  

This repo treats those as **engineering bugs**, not footnotes.

What I built to fight them:

| Piece | In plain English |
|---|---|
| **Fill engine** | Rules for when a limit, stop, or market order would actually fill |
| **Plan replayer** | Walks through a day event-by-event with human-like delay and limited “attention slots” |
| **P&amp;L breakdown** | Splits results into: market move, delay cost, spread cost, fees |
| **Research protocol** | Write down the rules *before* looking at results; lock a final test period |
| **Experiment archive** | Dozens of named ideas (M3–M30), including the ones that failed |

---

## How a single experiment works

1. **State the idea** — e.g. “fade a big opening gap” or “trade with the closing auction signal.”  
2. **Register it** — hypothesis, rules, and pass/fail criteria go in the ledger *first*.  
3. **Build the signal** — detectors, models, or simple rules produce candidate trades.  
4. **Turn each signal into a plan** — not just “buy NVDA,” but entry style, stop, targets, time limit.  
5. **Replay** — simulate fills and exits on historical data under fixed constraints.  
6. **Decide** — pass, fail, “between the bars,” or “not enough power,” then stop tuning that look.

If something went wrong in the simulator (for example, phantom profitable fills), we fixed the
simulator and **retracted** the claim — we did not keep the flattering number.

---

## Strategies we tried (big picture)

We did **not** chase one lucky model. We ran a **program of families** (M3, M4, … M30).
Each family is one *kind* of idea, tested under the rules above.

### The story in five chapters

| Chapter | IDs | Plain English |
|---|---|---|
| **1. Intraday “forced flow” plans** | M3–M5 | Trade only when a known pressure exists (gap, VWAP stretch, LETF rebalance, …). Add ML later. |
| **2. Closing auction** | M6–M15 | Use the official close print as a clean exit; study imbalance / price-gap signals into 4:00. |
| **3. Execution & mean reversion** | M16–M18 | Measure real costs; try a full “reversion *system*” (rules + filters + maker entries). |
| **4. Other same-day ideas** | M20–M27 | Macro news windows, open fade, gap days, earnings-day closes, position sizing. |
| **5. Wide, honest batteries** | M28–M30 | Many signals, many stocks, pre-committed tests — including clean out-of-sample on new names. |

### What we learned (without the jargon)

- **Many mid-day strategies looked good until fills were realistic** — then they died.  
- **One closing-auction idea passed a locked final test** (holdout), then further work on
  close strategies was **stopped by policy** (program focus moved elsewhere). That edge also
  looked **narrow** (not “all of Nasdaq”).  
- **Why some names worked better** pointed to **leveraged-ETF rebalance flow**, not “high
  volatility” alone.  
- **Cheap structure helps:** enter at the open’s single print and exit late afternoon often
  costs only a few basis points — but **cheap isn’t enough**; several big tests found **no
  usable signal** on top of that structure (M28–M30).  
- **A long fail list is a feature** of the process, not a bug. Weak ideas are supposed to die
  with a paper trail.

### Full list (M3–M30)

| ID | Idea in one sentence | Result |
|---|---|---|
| M3 | Plans only when a named flow state is “on” (gap, VWAP, LETF, …) | Closed after honest fills |
| M3-A1 | Use LightGBM to veto or reprice those plans | Failed |
| M4 | Deep models on second-by-second market data | Failed |
| M5 | Official “is the continuous book good enough?” gate | Failed |
| M6 | Closing-auction signal → trade into the close print | **Passed** (incl. locked holdout); later frozen as a line |
| M6b | Same idea at the **open** | Failed |
| M7 | Daily long/short reversal among large stocks | Failed |
| M8 | Only take close trades when a model says “likely win” | **Passed** (out-of-sample) |
| M8-v2 | Feed mechanism features into that model | Killed |
| M9 | Richer auction path + smarter size | No gain |
| M10 | Score frozen rules on brand-new days going forward | Partial; stopped when close line froze |
| M11 | Same close rule on 28 stocks never used in design | Failed (not a broad effect) |
| M12 | Explain *why* some names work (LETF vs index weight) | LETF flow explained better |
| M13 | Subtract market move to clean the signal | Not adopted |
| M14 | Does month-end / options week change results? | Diagnostic only |
| M15 | Hold at most 3 names, ranked by confidence | Report-only |
| M16 | Manual fill-quality study + flow-based day book | Mixed / incomplete for promotion |
| M17 | Classic multi-month momentum (research only) | Mixed / not for same-day mission |
| M18 | Mean-reversion as a full trading system | Failed |
| M20 | Trade after scheduled economic releases | Screen yes, confirmation no |
| M21 | Earnings “crowded setup” behavior | Diagnostic |
| M22 | Close-auction idea on earnings day | Inconclusive |
| M23 | Size positions by confidence vs equal size | Report-only |
| M24 | Fade a mispriced open into the close | Inconclusive |
| M25 | Calendar boost on the close stream | Withdrawn |
| M26 | Trade around 1:02 pm Treasury results | Parked, not built |
| M27 | Fade large opening gaps on thinner semis | Killed (costs too high) |
| M28 | 14 simple bar signals × many stocks at the open | No signal cleared the bar |
| M29 | Short-interest style signals, same setup | No signal cleared the bar |
| M30 | Retail order-flow fade on 16 new stocks | Not confirmed out of sample |

**Longer write-ups** (what each idea tried and how):  
[`docs/STRATEGIES.md`](docs/STRATEGIES.md)

---

## What’s in the code (map)

```
src/enginev51/
  backtest/     # “Would this order fill?” + day replay + P&L split
  protocol/     # research rules enforced in code (e.g. sealed test period)
  data/         # download/store/QA market data (needs your own keys + disk)
  events/       # detectors for gap, VWAP, LETF, …
  plans/        # turn a detector hit into a full trade plan
  models/       # LightGBM, optional GPU sequence models
  stats/        # honest performance stats (Sharpe-style, with caveats)
  apps/         # command-line tools to run trials

research/       # ledger + experiment reports (the paper trail)
tests/          # automated tests (many pure tests need no market data)
```

More detail: [`ARCHITECTURE.md`](ARCHITECTURE.md) · rules: [`PROTOCOL.md`](PROTOCOL.md)

| If you want to see… | Open… |
|---|---|
| Fill / replay logic | `src/enginev51/backtest/` |
| Research rules in code | `src/enginev51/protocol.py` |
| Strategy stories | [`docs/STRATEGIES.md`](docs/STRATEGIES.md) |
| Raw experiment log | `research/ledger.jsonl` |

---

## How AI agents fit in

I use AI agents as **helpers**, not as the decision-maker.

| Who | Job |
|---|---|
| **Me** | Design the experiment, freeze the rules, accept or reject results |
| **Coding agents** | Implement from a written spec + tests |
| **Research agents** | Gather literature / venue rules in a structured way |
| **Reviewer agents** | Try to break the change (lookahead bugs, rule violations) |

Rules of thumb:

- Write the experiment rules **before** anyone runs numbers.  
- Don’t let the same agent both build and “sign off.”  
- When a bug fools the research (fake fills, data leaks), add a **permanent test** so it can’t return quietly.

More: [`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md)

---

## Run it yourself

```bash
# Python 3.13+
uv sync --extra dev
uv run pytest tests/test_fills.py tests/test_protocol.py tests/test_replay.py tests/test_decompose.py -q
```

Those tests exercise the core simulator and research rules **without** downloading market data.

Optional: copy [`.env.example`](.env.example) → `.env` only if you want to pull data from vendors yourself.

| | |
|---|---|
| **Secrets** | Never commit `.env` |
| **Data** | Large historical files are not in this repo |
| **License** | [MIT](LICENSE) |

---

## What this is not

- A live trading bot  
- Investment advice  
- A claim that any strategy is “ready to trade with real money” today  
- A dump of paid market data  

---

## Further reading

| Doc | Why open it |
|---|---|
| [`docs/STRATEGIES.md`](docs/STRATEGIES.md) | Each M-series idea explained |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | How packages fit together |
| [`PROTOCOL.md`](PROTOCOL.md) | Research rules that void bad claims |
| [`research/deep/EXHAUSTION_MAP.md`](research/deep/EXHAUSTION_MAP.md) | What idea-space is considered closed vs open |

---

## License

MIT — see [LICENSE](LICENSE). See also [CONTRIBUTING.md](CONTRIBUTING.md).
