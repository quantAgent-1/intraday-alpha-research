# R2-A Stage 3 — out-of-sample test on unseen names: PRE-DECLARATION

Written **2026-07-26, before any new symbol's trade data was fetched, and before any
statistic was computed on any name outside the discovery panel.** Everything below is
frozen at the moment of writing. If a choice here turns out to be inconvenient, the
inconvenience is the result.

---

## 0. What this is, and what it can never be

The frozen prong-0 result (`research/experiments/R2A-prong0/`, ledger row
`R2A-prong0-predeclaration`, mechanical label KILL) is **untouched by this document**.
Nothing here can revive, overturn, or re-adjudicate it. Its data is the *discovery*
sample and is permanently spent for confirmation purposes.

This is a **new test, on names the discovery sample never contained**, of the single
question that discovery cannot answer about itself: *does the top-quartile signed fade
appear in stocks we have never looked at?*

Stage-1 re-analysis (exploratory, same data, `stage1.md` / `stage1_instrument.md`) found:
costs are ~11% of the effect rather than ~200%; the effect splits ~58/42 sector vs
idiosyncratic; a SOXL expression of the sector half is not explained by market drift.
**None of that is evidence the effect is real.** It is why this test is worth its cost.

## 1. Universe — frozen

The discovery panel is NVDA TSLA AMD MU GOOGL KLAC MRVL LRCX TXN AMAT. The test universe
is **16 names, none of them in the discovery panel**:

```
VRTX BKNG ISRG AMGN HON INTU TMUS GILD MDLZ COST PEP ADBE CMCSA SBUX CSCO QCOM
```

**Selection rule (mechanical, outcome-blind):** every symbol in the pre-existing
`data/raw/sip/bars1d/` lake (37 names, assembled in earlier sessions for unrelated
reasons — not chosen by me) that is *not* in the discovery panel, ranked by estimated
download cost `sum over sessions of ceil(bars1d.trade_count / 10000)`, cheapest 16 taken
until the ~9.5 h budget at 150 req/min is exhausted. Cost is computed from bar metadata
only; **no trade, quote or return data of any candidate was examined.**

**Declared bias (stated now, not after):** ranking by download cost selects toward *lower
trade count*, i.e. relatively less-traded names. In the discovery panel the effect looked
larger in the less-liquid semis tier, so this selection is, if anything, tilted *toward*
finding an effect. Two consequences, both binding: (a) a liquidity-tier split is a
mandatory secondary diagnostic, and (b) a PASS driven only by the lowest-liquidity third
must be reported as such and does not license a broad claim.

Note this universe is overwhelmingly **not semiconductors** (QCOM aside). That is
deliberate and it is the harder test: the source hypothesis (Brown, retail odd-lot flow
→ open-print reversal) is a claim about US stocks generally, not about semis.

**Window:** ET sessions `2024-01-02 .. 2026-05-31`, identical to the discovery backfill.
The sealed holdout (≥ 2026-06-01) is **not touched** and remains sealed.

## 2. Method — forced deviation, with a pre-declared validation gate

The frozen prong-0 signs each odd-lot print against the prevailing `bbo1s` quote mid.
**`bbo1s` exists for the 10 discovery names only, and quote history for 16 more names is
not affordable at any budget this project has.** The test therefore requires a
**quote-free variant**:

- **signing**: tick rule against the previous off-exchange odd-lot print price, with the
  existing carry-last-nonzero tie handling (`_ffill_sign`). This is already the frozen
  rule's *fallback* path; the variant simply makes it the only path.
- **exit**: last `bars1m` close at or before 15:45 ET (require ≥ 15:40), replacing the
  `bbo1s` exit mid.
- **early-close guard**: last available minute bar of session t < 15:45 ET.
- everything else — `exchange=='D'`, `size<100`, RTH, ≥30 signed prints, per-name
  top-quartile `|OLI|`, `-sign(OLI)*ret`, seed-7 2000-rep session-clustered bootstrap —
  is the frozen machinery, called verbatim.

**VALIDATION GATE (runs on the 10 discovery names, where both methods are computable;
thresholds fixed here, before the comparison is run):**

| # | test | threshold |
|---|---|---|
| V1 | pooled Pearson corr( OLI quote-signed , OLI tick-signed ) over the 4,356 discovery name-days | **≥ 0.90** |
| V2 | quote-free top-quartile signed fade on the discovery panel vs the published +14.87 | **same sign AND within ±30%**, i.e. in [+10.41, +19.33] |
| V3 | median absolute difference between the `bars1m` exit return and the `bbo1s` exit return | **≤ 3.0 bps** |

**If any of V1–V3 fails, Stage 3 is abandoned and reported as METHOD-BLOCKED.** The
quote-free variant would then be a different statistic wearing the same name, and no
result computed with it would mean anything. There is no repair clause, no
threshold-softening clause, and no "close enough" clause.

## 3. The primary statistic — one number, frozen

> Pooled mean of `-sign(OLI_{t-1}) * ret_t` over the **top quartile of per-name `|OLI|`**,
> across the **16 test names only**, `ret_t` = open-print → last minute-bar close ≤ 15:45,
> with the seed-7 2000-rep session-clustered bootstrap 95% CI.

Exactly one primary statistic. No horizon menu, no name subsets, no threshold sweep.

## 4. Power, computed in advance

Discovery: se ≈ 8.00 bps at n = 1,094 top-quartile name-days. The test universe should
yield ≈ 16 × 600 = 9,600 name-days → ≈ 2,400 in the top quartile → **se ≈ 5.4 bps**
(assuming comparable per-name-day variance; the realised se is reported either way).

- CI-lo > 0 requires an observed mean ≳ **+10.5 bps**.
- Discovery point estimate was +14.87, which winner's curse says is biased upward. If the
  true effect is ~10 bps, this test has roughly **45–50% power**; at ~15 bps, ~85%.

**This is stated so that a null is interpreted correctly**: with this design, a null is
informative about effects ≥ 15 bps and *weak* evidence against effects near 8–10 bps.

## 5. Outcomes — fixed now

- **CONFIRMED** — CI-lo > 0. The effect appears in unseen names. Licenses a registration
  proposal (family `open_print_retail_fade_v1`), not a trading decision.
- **REFUTED** — CI-hi < 0. The effect reverses out of sample; the axis is closed.
- **NOT-CONFIRMED** — CI spans 0 with point estimate < +6.0 bps. The discovery estimate
  does not generalise; treated as a failed replication and the axis is closed at $0.
- **UNDERPOWERED-INCONCLUSIVE** — CI spans 0 with point estimate ≥ +6.0 bps. Recorded as
  such, explicitly NOT as support. The only permitted follow-up is a further universe
  expansion declared in a new document; **no re-analysis of these 16 names may be used to
  argue for the effect.**

## 6. Mandatory secondary diagnostics (reported always, gating never)

Run and reported regardless of the primary outcome, precisely so that a PASS can be
attacked as hard as a FAIL:

1. **Per-name signs** — how many of 16 are positive; binomial p.
2. **Liquidity-tier split** — thirds by median trade count (the declared-bias check).
3. **Year split** — 2024 / 2025 / 2026 separately.
4. **Drift vs timing** — mean position, buy-and-hold over the traded sessions, and the
   decomposition `gross = drift + timing` (the check that caught nothing on SOXL and must
   be run again here).
5. **Placebo** — the identical pipeline with `OLI` replaced by a session-shuffled `OLI`
   (seed 101, 200 draws): the placebo distribution must contain the real statistic's
   sign-flipped mirror at roughly the expected rate. A real effect must sit in the tail.
6. **Cost** — net of a 1.5 bps assumed exit half-spread (no quotes for these names), and
   the sensitivity of the sign of the net to that assumption.
7. **Coverage/funnel** — candidate days, drops by reason, per name; any name with < 100
   kept days is reported and its influence on the pooled mean is shown.

## 7. Provenance

- Discovery panel + frozen machinery: `scripts/r2a_prong0.py` (unmodified).
- Panel cache: `scripts/r2a_panel_build.py`.
- Stage-1 exploratory re-analysis: `scripts/r2a_stage1.py`, `scripts/r2a_stage1_instrument.py`.
- Data pull: `scripts/backfill_trades_oos.py` (thin wrapper over the verified
  `scripts/backfill_trades_semis.py`; symbol list and log path overridden, fetch/write
  path untouched).
- This document is written before the wrapper is executed for the first time.
