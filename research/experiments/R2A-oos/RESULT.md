# R2-A Stage 3 — RESULT: METHOD-BLOCKED (no OOS statistic exists)

> **SUPERSEDED 2026-08-01:** the quote unlock (Alpaca free historical quotes) + the
> XNAS→NBBO bridge (V-NB PASS) later made the decisive test runnable; the registered
> M30 look ran and returned **NOT-CONFIRMED** — see `OOS_RESULT.md`. The durable
> finding below (trade-side classification requires contemporaneous quotes) stands.

2026-07-26. Pre-declaration: `PREDECLARATION.md`; method amendment:
`PREDECLARATION_AMENDMENT_1.md`; gate output: `validation.md`.

**No out-of-sample number was produced, and none may be quoted.** The pre-declared
admissibility gate failed, so the test was abandoned exactly as the pre-declaration
required. The frozen prong-0 result is untouched and remains the mechanical KILL.

## Why

The frozen statistic classifies each off-exchange odd-lot print as buyer- or
seller-initiated by comparing it to the **prevailing quote mid** (`bbo1s`). `bbo1s` exists
for the 10 discovery names only, and quote history for the 16 test names is not affordable
here. Two quote-free substitutes were tested against the pre-declared gate. Both failed.

| variant | V1 corr vs quote-signed OLI (need ≥ 0.90) | V2 fade on discovery panel (need +10.4…+19.3) | V3 exit-proxy error (need ≤ 3.0 bps) |
|---|---|---|---|
| attempt 1 — tick rule | **0.4566** FAIL | void (defect, see below) | void |
| attempt 2 — minute-VWAP reference | **0.1106** FAIL | **−2.11** FAIL | **5.97** FAIL |

Per-name V1 for attempt 1: NVDA 0.469, TSLA 0.012, AMD 0.438, MU 0.602, GOOGL −0.001,
KLAC 0.702, MRVL 0.639, LRCX 0.658, TXN 0.676, AMAT 0.585.

## The durable finding

**Trade-side classification cannot be reconstructed without contemporaneous quotes.**
Both substitutes fail for mechanistically clear reasons:

- The **tick rule** compares consecutive odd-lot prints. In a megacap book quoted 0.6–1.6
  bps wide, consecutive retail prints differ by sub-penny price improvement — i.e. by
  noise. It degrades exactly where spreads are tightest (TSLA 0.012, GOOGL −0.001) and is
  least bad in the wider-spread semis (KLAC 0.702).
- The **minute-VWAP reference** compares an off-exchange odd-lot print to the consolidated
  average price of that minute — a different population (round lots, on-exchange) with a
  systematic price-improvement offset. It produces an imbalance measure ~7× more dispersed
  than the quote-based one (sd 0.50 vs 0.068) and essentially uncorrelated with it.
- Separately, **V3 shows the entry/exit proxy alone injects ~6 bps of median error** into a
  ~15 bps effect, independent of any signing question.

**Consequence for the program, stated generally:** free bar data widens panels for
*bar-anchored* families, but **flow/tape-anchored families are quote-limited, and quote
history is the binding cost**. Any future family that needs signed order flow inherits the
10-name panel ceiling until quote data is bought. This qualifies the "widen the panel with
free data" recommendation in `research/BREAKTHROUGH_ANALYSIS_2026-07-26.md` §5 — that lever
is real for bar-anchored designs and does not exist for this one.

## Three implementation defects found and fixed en route (all mine, all the same class)

Recorded because the same landmine has now produced large spurious numbers three times:

1. Adjusted `bars1m` exit close ÷ raw `bars1d` open → V2 read **−1248 bps**. Detected via
   the KLAC ratio 0.0991 (10:1 split); TXN 0.9645 (dividends).
2. Raw trade prints signed against an **adjusted** VWAP reference → KLAC OLI constant,
   correlation `nan`; degradation tracked each name's adjustment factor.
3. Scale factor denominated on the **last extended-hours** bar rather than the RTH close →
   after-hours drift shifted the whole reference; symptom was |OLI| saturating at 1 on
   **32%** of name-days (fixed: 0.0–0.7%).

**Standing rule (add to the landmine list): `data/raw/sip/bars1d` is RAW, `data/raw/sip/bars1m`
is split/dividend-ADJUSTED, and `data/raw/sip/trades` is RAW. Never compare or divide prices
across those lakes without an explicit same-day scale factor built on the RTH close.** Each
defect was caught by an outcome-independent sanity check, not by the gate — the gate would
have accepted the last one as a clean failure.

## What survives, and the open decision

Unaffected by this: the Stage-1 findings that costs are ~11% of the effect (not ~200%) and
that the SOXL expression is not explained by market drift. Those remain **exploratory,
same-data** results and are not evidence the effect is real.

The only remaining route to confirmation is **quote history for names outside the discovery
panel**. Rough sizing from bar metadata: ~2.5–3 h of free Alpaca pulling per name for the
604-session window; 5 names ≈ 14 h and still underpowered (se ≈ 9.7 bps, needs ≈ +19 to
pass); 10 names ≈ 28 h (se ≈ 6.8 bps, needs ≈ +13.3). **That is a user decision about time,
not a research step, and it is not taken here.**

## Data state

`data/raw/sip/trades/VRTX/` holds a partial backfill (~2 months) from the pull that was
stopped when the gate failed; the remaining 15 test names were never fetched. The backfill
is resumable and skips existing partitions. `bars1m` was backfilled for the 5 discovery
semis + all 16 test names (609 partitions) and is schema-identical to the existing lake —
it is reusable and harmless. Nothing was written to `research/ledger.jsonl`; no family was
registered or charged; the sealed holdout (≥ 2026-06-01) was never touched.
