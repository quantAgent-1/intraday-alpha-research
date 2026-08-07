# DR-X5 — refute-1 (claim bundle)

**Role:** Attempt to REFUTE via primary sources. Default `refuted=true` if no T1/T2 (or, for claim 5 only, no local ledger/report primary).
**Date:** 2026-07-18
**Lane:** DR-X5-liquidity-down-auction

---

## Claim 1

**Claim:** Bogousslavsky–Muravyev: |auction−4pm mid| ~**2.66 bps** large-cap quintile vs ~**20.6 bps** small (2010–2018); full-sample half-spread ~**7.56** vs residual impact ~**0.55** bps.

**refuted:** **false**

**Reason:** Located T2 primary (author WP June 2021 + AEA conference PDF text of the same paper; published JFM 2023). Table 4(a) absolute auction deviation means: size-quintile **Low = 20.60 bps**, **High = 2.66 bps**; full-sample mean **8.12 bps**. Decomposition (main text + Table IA.1): average **half-spread 7.56 bps**, **price impact 0.55 bps**. Sample stated as NYSE+Nasdaq common stocks Jan 2010–Dec 2018, price >$5, mcap >$100M. Numbers match the claim; no material misquote found.

**Source located:**
- **[T2]** Bogousslavsky & Muravyev, *Who Trades at the Close?*, WP June 2, 2021 (→ J. Financial Markets 2023). PDF: https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf ; AEA conf text: https://www.aeaweb.org/conference/2021/preliminary/paper/H9T4hef7 ; DOI: https://doi.org/10.1016/j.finmar.2023.100852
- Sample period: **2010–2018**. Unit: bps absolute |log auction − log 4pm mid|.

**Caveat (not a refute):** Residual impact 0.55 is a *full-sample mean* of the walk-the-book residual; large-cap half-spread ≈ impact (1.47 vs 1.19) is a different slice and does not overturn the full-sample 7.56 / 0.55 pair as stated.

---

## Claim 2

**Claim:** B&M: **68.5%** of auctions print at pre-close bid/ask; **9.56%** small-stock days have zero auction.

**refuted:** **false**

**Reason:** Same T2 primary. Abstract / body: “The closing price matches the pre-close best bid or ask price in **68.5%** of all auctions.” Footnote on zero-auction incidence: “**2.48%** of stock-days have zero auction volume… mostly driven by small stocks… **9.56%** have zero auction volume. Only **0.21%** of stock-days in the top size quintile do not have an auction.” Table 1 size-quintile Low: **No auction (%) 9.56**. Both figures match exactly.

**Source located:**
- **[T2]** Same B&M WP/AEA as Claim 1 (abstract; § near Table 1 / footnote on zero auction; Table 1 Low quintile).
- Sample: **2010–2018**.

---

## Claim 3

**Claim:** Goyal–Jegadeesh–Wu JFQA 2026: auction price impact lower than continuous except Nasdaq microcaps.

**refuted:** **false**

**Reason:** Located T2 primary (JFQA open-access article, published online 05 Mar 2026 / JFQA 2026). Abstract verbatim: “We find that the price impact is lower in closing auctions than in the continuous market for **all stocks except Nasdaq microcaps**.” Conclusion restates: “price impact is notably smaller in closing auctions than that in the continuous market for all stocks except Nasdaq Micro stocks.” Body also states strategic-execution rule: continuous for Nasdaq Micro; closing auction for all other stocks. Claim is an accurate paraphrase of the paper’s headline finding.

**Source located:**
- **[T2]** Goyal, A., Jegadeesh, N. & Wu, Y. (2026). *Price Impact in Closing Auctions, Opening Auctions, and Continuous Markets…* JFQA. https://doi.org/10.1017/S0022109026102592 ; Cambridge Core: https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/price-impact-in-closing-auctions-opening-auctions-and-continuous-markets-a-benchmark-for-cost-of-trading-on-anomalies/0F72910A79C5B42CF6E85F55164CE846
- Sample period (paper): **Jan 2012–Dec 2021**, NYSE+Nasdaq common stocks with TAQ∩auction data. Micro = below 20th NYSE mcap percentile.

---

## Claim 4

**Claim:** Nasdaq Closing Cross schedule/cutoffs (**15:50 / 15:55 / 15:58 / 16:00** near/far) are **IDENTICAL for all listed names** regardless of size/liquidity (**T1**).

**refuted:** **false**

**Reason:** Located T1 Nasdaq primary FAQ (©2025 / 1608-25). Explicit eligibility: “**All nationally-listed securities are eligible for the Crosses.**” Cutoffs stated without size, ADV, or listing-tier (Global Select / Global / Capital) carve-outs:
- On-close modify/cancel freeze: **prior to 3:50 p.m.**
- MOC must be received **prior to 3:55 p.m.**
- Late LOC accepted **after 3:55** under reprice rules; LOC hard cutoff **prior to 3:58 p.m.**
- Closing Cross executes **at 4:00 p.m.**
- NOII: **3:50–3:55** every **10s** (reference / paired / imbalance); **3:55–4:00** every **1s** adding **Near** and **Far**.

No security-size or liquidity tier appears in the schedule. Activity-conditioned *outcomes* (imbalance side **O** = insufficient interest; no cross → NOCP = last regular-way last-sale) are not alternate *schedules*.

**Source located:**
- **[T1]** Nasdaq, *The Nasdaq Opening and Closing Crosses — Frequently Asked Questions* (©2025, 1608-25). https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf
- Supporting T1 (same schedule language): Nasdaq Trader Closing Cross materials / openclose pages.

**Caveats (not schedule refute):**
1. **ETP cross-price thresholds** (greater of 5%/$0.50 etc.) differ from cash equities — a *price-collar* difference, not a cutoff/NOII-cadence difference; claim is about schedule/cutoffs.
2. **LULD pause at/after 15:50** routes to LULD Closing Cross under Rule 4754(b)(6) — special auction path, still not a size-tiered daily schedule for ordinary names.
3. Fees are **member activity tiers**, not security liquidity tiers — out of claim scope.

---

## Claim 5

**Claim:** M11 project result: champion rule on **28 never-fit Nasdaq names** net **−3.0 bps**, dir **0.47** — verify **only** against `research/ledger.jsonl` and `research/experiments/M11-oos-28/report.md` (local, not web).

**refuted:** **false**

**Reason:** Local primaries match within rounding.

| Source | Quantity | Value |
|--------|----------|-------|
| `research/experiments/M11-oos-28/report.md` §2 | Pooled day-clustered mean net_bps | **−3.016** CI [−3.458, −2.570], n=17747, sessions=846 |
| same report §2 / title | Universe | **28** Nasdaq names never-fit; frozen near-vs-ref rule; pure OOS |
| `research/ledger.jsonl` trial `M11-xsection-oos-v1` (2026-07-17T06:22:11Z) | numbers | **net −3.02 [−3.46,−2.57]**, **directional 0.470**, 28 new names, n=17747; all 6 sectors negative |
| same ledger line | verdict | FAIL — broad-Nasdaq thesis falsified |

Claim’s “−3.0 bps” and “dir 0.47” are the ledger’s rounded forms of −3.016 / 0.470. Report does not print directional hit in §2 but ledger records directional **0.470** for the same trial; report’s ungated_hit_rate **0.3942** (§7) is a different metric (gated-transfer panel), not a contradiction of dir 0.47 on the classical stream.

**Source located (local only, as charged):**
- `<repo-root>\research\experiments\M11-oos-28\report.md`
- `<repo-root>\research\ledger.jsonl` — `trial_id: M11-xsection-oos-v1` result row

**Note:** Project-internal ledger/report are the binding primary for this claim (orchestrator charge: local-only). No web T1/T2 applies.

---

## Bundle summary

| # | Claim (short) | refuted | Tier of source that decided |
|---|---------------|---------|-----------------------------|
| 1 | B&M |dev| 2.66 vs 20.6; HS 7.56 / impact 0.55 | **false** | T2 B&M WP/JFM |
| 2 | B&M 68.5% at bid/ask; 9.56% small zero-auction | **false** | T2 B&M WP |
| 3 | Goyal et al. auction PI < continuous except Nasdaq microcaps | **false** | T2 JFQA 2026 OA |
| 4 | Nasdaq Closing Cross schedule identical all listed names | **false** | T1 Nasdaq openclose FAQ ©2025 |
| 5 | M11 28-name OOS −3.0 bps / dir 0.47 | **false** | local ledger + M11 report |

**Majority refuted?** No — **0/5 refuted**. All five load-bearing claims **survive** with located primary (T1/T2 or charged local) support. Default-true path not triggered on any claim.

#### Queries / fetches used
1. Bogousslavsky Muravyev who trades at the close large-cap 2.66 small 20.6 half-spread 7.56
2. Fetched WP PDF + AEA conf PDF text (Tables 1, 4, IA.1; abstract 68.5%; zero-auction footnote)
3. Goyal Jegadeesh Wu JFQA price impact closing auctions Nasdaq microcaps
4. Fetched Cambridge Core OA abstract/body/conclusion for Goyal–Jegadeesh–Wu 2026
5. Fetched `https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf` (T1)
6. Read local `research/experiments/M11-oos-28/report.md` + `research/ledger.jsonl` M11 result row
