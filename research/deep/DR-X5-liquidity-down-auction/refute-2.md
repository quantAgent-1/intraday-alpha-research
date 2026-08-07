# DR-X5 refuter wave — agent 2 (independent)

**Role:** Attempt to REFUTE load-bearing claims via primary (T1/T2) sources.  
**Default:** `refuted=true` if no primary located.  
**Date:** 2026-07-18  
**Independence note:** This agent did not read a sibling refute-1 report. Primaries were re-fetched and re-read (B&M June 2021 PDF tables; Goyal–Jegadeesh–Wu JFQA Cambridge full text; Nasdaq open/close FAQ ©2025/1608-25; project `research/experiments/M11-oos-28/report.md` + `research/ledger.jsonl` M11 entry).

---

## Bundle claims under test

| ID | Claim (as charged) | Source class asserted by modalities |
|----|--------------------|-------------------------------------|
| C1 | B&M size cross-section: mean \|auction−4pm mid\| = **8.12 bps** overall; **20.6 bps** bottom size quintile vs **2.66 bps** top | T2 B&M 2010–2018 |
| C2 | Spread decomposition: full-sample half-spread **7.56 bps**, pure impact **0.55 bps**; large half-spread **~1.47** vs impact **~1.19**; small-tier half-spread **~22 bps** ≈ the 20.6 \|dev\| | T2 B&M Table 5 |
| C3 | Zero-auction days: **9.56%** small-quintile stock-days vs **0.21%** large; **2.48%** full sample | T2 B&M Table 1 |
| C4 | Goyal micro exception: closing-auction price impact **lower than continuous for all stocks except Nasdaq microcaps** (e.g. Nasdaq Micro 0.5% ADV auction **~31.6 bps** vs continuous **~15.6 bps**) | T2 Goyal–Jegadeesh–Wu JFQA 2026 / sample 2012–2021 |
| C5 | Nasdaq mechanics parity: **all** nationally-listed securities share the **same** Closing Cross / NOII schedule (MOC 15:55, late LOC→15:58, modify freeze 15:50; near/far only 15:55–16:00); no-cross → NOCP = last regular-way sale | T1 Nasdaq FAQ |
| C6 | M11 local: frozen near-vs-ref rule on **28 never-fit** Nasdaq names → net **−3.02 bps** [−3.46, −2.57], directional **0.470**, negative in **all 6** sectors | T1 project experiment / ledger |

---

## C1 — B&M size cross-section

**Attempted refutation path:** Check whether 20.6 / 2.66 / 8.12 are misquoted, are medians not means, or are confined to one venue.

**Primary located:** Bogousslavsky & Muravyev, *Who Trades at the Close?*, WP June 2, 2021 (later J. Financial Markets 2023). Full PDF read.  
URL: https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf  
Tier: **T2**. Sample: NYSE+Nasdaq common stocks, Jan 2010–Dec 2018, P>$5, mcap>$100M.

**What the primary says (Table 4, p.42 of WP PDF):**

| | All | Low | 2 | 3 | 4 | High |
|--|-----|-----|---|---|---|------|
| Mean \|dev\| (bps) | **8.12** | **20.60** | 8.99 | 5.49 | 3.97 | **2.66** |
| Count | 5,578,901 | 1,046,362 | … | … | … | 1,160,123 |

Definition: \|log(p_auc / p_4:00 mid)\| in bps. Text §3.2: “range from 20.6 bps for small stocks to 2.66 bps for large stocks.”

**Caveats (not refutations):**
- Size is **market-cap quintile**, not ADV-dollar tier. Mapping “Low” → pilot ADV $20–50M is an interpolation the paper does not make.
- Sample ends **2018** → any 2020–2026 claim of the same magnitudes is DECAY-UNKNOWN (not asserted by C1 as written).
- Absolute deviation is **unsigned**; it is not a signed strategy edge and is not net of continuous-entry half-spread.

**Verdict: `refuted = false`**  
Numbers 8.12 / 20.6 / 2.66 match Table 4 means exactly. Claim stands as a correct citation of B&M 2010–2018.

---

## C2 — Spread decomposition

**Attempted refutation path:** Check whether “most of 20.6 is half-spread” is overstated; whether large-cap residual is misstated.

**Primary:** Same B&M WP PDF, Table 5 (p.43) + §3.2 text.

**Table 5(a) half-spread means (bps):**

| All | Low | 2 | 3 | 4 | High |
|-----|-----|---|---|---|------|
| **7.56** | **22.19** | 8.29 | 4.43 | 2.73 | **1.47** |

**Table 5(b) price-impact means (bps):**

| All | Low | 2 | 3 | 4 | High |
|-----|-----|---|---|---|------|
| **0.55** | **−1.60** | 0.69 | 1.06 | 1.25 | **1.19** |

Identity: \|dev\| = half-spread + price impact (signed impact can be negative when the print is *inside* half-spread). Arithmetic check: Low 22.19 + (−1.60) = **20.59 ≈ 20.60**; High 1.47 + 1.19 = **2.66**. Full sample 7.56 + 0.55 = **8.11 ≈ 8.12**.

Text: “The average half spread is 7.56 bps, while price impact is only 0.55 bps… For large stocks, the half-spread and price impact are about equal: 1.47 and 1.19 bps.” Also: 68.5% of auctions at pre-close bid or ask; tick binding 41.8%; \|dev\| exceeds half-spread in only 23.4% of cases.

**Caveats:**
- Low-quintile **mean impact is negative (−1.60)** — the small-stock “dislocation” is *more than fully* explained by half-spread on average (print often *inside* the quote). That **strengthens** the spread-eats-dev adversarial read; it does not refute the numbers.
- Half-spread here is **realized vs 4pm NBBO**, not the continuous taker half-spread a retail book pays at 15:55:10. Units are still bps of price, but the economic object for strategy cost is a related-not-identical quantity.

**Verdict: `refuted = false`**  
Decomposition numbers and large-cap 1.47 / 1.19 pair are primary-confirmed. Small-tier “~22 bps half-spread vs 20.6 \|dev\|” is exact (22.19 vs 20.60).

---

## C3 — Zero-auction days

**Attempted refutation path:** Check whether 9.56% is full-day zero volume, not zero auction; whether large is really 0.21%.

**Primary:** Same B&M WP PDF, Table 1 Panel (b) (p.39) + footnote text §3.1.

| | Low (small) | Mid | High (large) | Full sample |
|--|-------------|-----|--------------|-------------|
| No auction (%) | **9.56** | 0.61 | **0.21** | **2.48** |
| No volume (full day) (%) | 0.72 | 0.03 | 0.00 | 0.22 |
| Auction vol. share (%) | 6.06 | 5.69 | 5.67 | 5.69 |

Text: “0.72% of which have zero daily volume and **9.56% have zero auction volume**. Only **0.21%** of stock-days in the top size quintile do not have an auction… **2.48%** of stock-days have zero auction volume.”

**Caveats:**
- Zero-auction ≠ zero NOII messages; a thin name can still print NOII with side **O** (insufficient interest) and then fail to cross. Nasdaq mechanics (C5) make no-cross → last-sale NOCP — operationally kills the champion exit path even when some imbalance tape exists.
- 9.56% is bottom **mcap** quintile of a P>$5 / mcap>$100M sample — not microcaps below the B&M filter, which are worse.

**Verdict: `refuted = false`**  
9.56 / 0.21 / 2.48 match Table 1 exactly.

---

## C4 — Goyal micro exception

**Attempted refutation path:** Check whether “auction cheaper except micro” is abstract-only; whether 31.6 / 15.6 are fabricated; whether Small (non-micro) also flips.

**Primary located:** Goyal, A., Jegadeesh, N. & Wu, Y., *Price Impact in Closing Auctions, Opening Auctions, and Continuous Markets…*, *Journal of Financial and Quantitative Analysis* (FirstView / online 2026-03-05; abstract also on JFQA site 2026-01-08).  
DOI: https://doi.org/10.1017/S0022109026102592  
Cambridge full text read (Open Access CC-BY). Sample: Jan 2012–Dec 2021, NYSE+Nasdaq common stocks with TAQ ∩ auction data. Tier: **T2**.

**What the primary says:**
- Abstract: “We find that the price impact is lower in closing auctions than in the continuous market for **all stocks except Nasdaq microcaps**.”
- §V / Figure 7 discussion (Cambridge body):  
  - **Large** 0.5% / 5% ADV: NYSE auction **3.2 / 10.1** vs continuous **6.4 / 20.2**; Nasdaq auction **7.2 / 22.7** vs continuous **8.3 / 26.3**.  
  - **Small** 0.5% / 5%: NYSE auction **5.2 / 16.5** vs cont. **10.7 / 33.8**; Nasdaq auction **8.8 / 27.9** vs cont. **11.3 / 35.8**.  
  - **Micro Nasdaq** 0.5% / 5%: auction **31.6 / 100.0** vs continuous **15.6 / 49.4** — auction **worse**.  
- Size buckets: Large = above NYSE median mcap; Small = NYSE p20–p50; Micro = below NYSE p20.  
- Square-root 1% ADV mean auction impact **17.7 bps** (median **8.4**); linear JW-style understates (≈2.35 bps).

**Caveats (not refutations of C4 as stated):**
- This is **price impact of a %ADV order into the auction**, not \|auction−mid\| dislocation and not the champion NOII-basis residual. C4 correctly bounds the *venue-cost* frontier (exclude micro), not the *net basis edge*.
- At project size ($10k), even 0.5% ADV is enormous vs a $20M ADV name (0.5% = $100k) — self-impact is sub-bps; the micro exception is a **toxicity / design** flag, not a capacity flag.

**Verdict: `refuted = false`**  
Exception statement and 31.6 vs 15.6 Nasdaq-micro figures are in the published JFQA body. Non-micro Small remains auction-cheaper than continuous.

---

## C5 — Nasdaq mechanics parity (mid/small = same rules)

**Attempted refutation path:** Find a liquidity-tier alternate schedule, different NOII fields, or small-cap exclusion from the Closing Cross.

**Primary located:** Nasdaq, *The Nasdaq Opening and Closing Crosses — Frequently Asked Questions*, ©2025, doc id **1608-25**.  
URL: https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf  
Tier: **T1** (fetched 2026-07-18; full PDF read).

**What the primary says (no tier carve-outs):**
1. **Eligibility:** “**All nationally-listed securities are eligible for the Crosses.**” (Q1) — not Nasdaq-listed only; not large-cap only.
2. **Cutoffs (Closing):** MOC prior to **3:55 p.m.**; late LOC after 3:55 re-prices to more aggressive of 3:50 / 3:55 Reference Prices; LOC hard stop **3:58 p.m.**; if no 3:55 Reference Price / no crossing interest, late LOC **not accepted**. Modify/cancel of on-close freezes prior to **3:50 p.m.** (Q10, Q17, Q25).
3. **NOII cadence:** 3:50–3:55 every **10s** (Reference, Paired, Imbalance shares/side); 3:55–4:00 every **1s** adding **Near** and **Far** indicative clearing prices (Q7–Q8). Universal schedule — no ADV-conditioned cadence.
4. **Imbalance side O:** “O = no marketable on-open or on-close orders” (Q7) — thin-interest code exists for *any* name.
5. **No Cross:** Closing Cross sets NOCP; “If a stock does not have a closing cross, the last regular way last-sale eligible trade reported prior to 4:00 p.m. is used as the NOCP” (Q6 / Q19).

**What would have refuted C5 (not found):** A rule saying Capital Market / non-NDX names use different MOC cutoffs, omit near/far, or skip the Cross by policy. None in this FAQ. Fee schedule (member activity tiers on the Price List) is orthogonal to security liquidity tiers and is not part of C5 as charged.

**Caveats:**
- Parity of **rules** ≠ parity of **signal quality**. Near can be uninformative or zero-interest (side O) on thin books; no-cross rate rises with thinness (C3). That is activity degradation, not rule degradation — modalities already separate these.
- LULD Closing Cross (Rule 4754(b)(6)) is a *state-conditioned* alternate path, not a size tier. Out of C5’s parity claim as stated.

**Verdict: `refuted = false`**  
T1 FAQ confirms universal eligibility and identical cutoffs/NOII schedule. Mechanics parity holds.

---

## C6 — M11 local (broad-Nasdaq OOS kill)

**Attempted refutation path:** Check whether −3.02 is gross not net, whether directional 0.470 is invented, whether any sector was positive, whether n is too small.

**Primary located (project T1):**
1. `research/experiments/M11-oos-28/report.md` (M11 cell, registered before download; pure OOS frozen near-vs-ref rule, 2023–2026).
2. `research/ledger.jsonl` entry `trial_id=M11-xsection-oos-v1` (ts 2026-07-17T06:22:11Z).

**What the primaries say:**

| Quantity | Source value |
|----------|--------------|
| Pooled net_bps mean | **−3.016** (report §2) / ledger **−3.02** |
| Day-clustered 95% CI | **[−3.458, −2.570]** |
| n events | **17,747** (26/28 names with NOII partition; BKNG/PLTR missing) |
| Sessions | 846 in CI window |
| Sectors with net > 0 | **0 / 6** (Comm −2.99, Consumer −2.84, Health −3.58, MegaTech −2.58, Other −0.41, Semis −3.23) |
| Directional (ledger) | **0.470** (“BELOW coin flip”) |
| Ungated hit_rate after fixed 2.5 bps entry cost (report §7) | **0.3942** (distinct metric — net-positive rate, not raw directional) |

Method (report header): FIRE iff \|basis\|≥10 at 15:55:10 near-vs-ref; side = sign(near−ref); entry = ref×(1+side×2.5 bps) conservative taker; exit = official daily close. Zero parameter search. Names never fit on original-5.

**Caveats (scope, not numeric refutation):**
- M11 universe is **liquid Nasdaq expansion** (AAPL, MSFT, META, AVGO, …) — **not** the DR-X5 $20–200M ADV pilot band. C6 falsifies “universal Nasdaq closing-auction mechanism,” which is the load-bearing implication for *indiscriminate* liquidity-down expansion; it does **not** by itself measure mid/small residual after honest half-spread.
- Cost model is fixed **2.5 bps** taker (2 bps half-spread + 0.5 slip), *wider* than true megacap half-spreads → nets are conservative (understate edge). Still deeply negative.
- “Directional 0.470” is ledgered; report’s 0.3942 is post-cost hit-rate. Both are adverse; do not conflate units.

**Verdict: `refuted = false`**  
Net −3.02 [−3.46, −2.57], n=17,747, all-six-sectors negative, directional 0.470 are primary-confirmed in project report + ledger.

---

## Summary table

| Claim | refuted | Primary located | Tier | One-line reason |
|-------|---------|-----------------|------|-----------------|
| C1 B&M size cross-section 8.12 / 20.6 / 2.66 | **false** | B&M WP 2021 Table 4 | T2 | Exact match |
| C2 Spread decomp 7.56 / 0.55; large 1.47/1.19; small HS 22.19 | **false** | B&M WP 2021 Table 5 | T2 | Exact match; Low impact mean −1.60 (inside-spread) |
| C3 Zero-auction 9.56 / 0.21 / 2.48 | **false** | B&M WP 2021 Table 1 | T2 | Exact match |
| C4 Goyal micro exception; 31.6 vs 15.6 | **false** | Goyal–Jegadeesh–Wu JFQA 2026 §V / Fig 7 | T2 | Abstract + body numbers confirmed |
| C5 Nasdaq mechanics parity | **false** | Nasdaq open/close FAQ ©2025 1608-25 | T1 | All NMS eligible; universal cutoffs/NOII |
| C6 M11 net −3.02 / dir 0.470 / 6/6 negative | **false** | M11-oos-28 report + ledger M11-xsection-oos-v1 | T1 project | Exact match |

**Majority rule for this agent:** **0 / 6 claims refuted.** All six load-bearing numeric/mechanics claims survive independent primary re-check.

---

## Implications for DR-X5 synthesis (refuter scope only — not a verdict)

These confirmations **do not** promote liquidity-down. They fix the factual base the orchestrator must use:

1. **Gross \|dev\| really does scale with thinness** in 2010–2018 (C1) — but **almost entirely as half-spread** (C2), with small-quintile mean pure impact **negative**.
2. **Cross reliability degrades** in the small quintile (~10% no auction) (C3); rules still fire the same way (C5), exit path does not.
3. **Auction remains the cheaper venue except Nasdaq micro** (C4) — so a pilot must **exclude micro**, not chase the 20.6 bin into Goyal’s exception zone.
4. **Broad liquid-Nasdaq transfer already failed** on owned data (C6). Liquidity-down is not “M11 but thinner”; if anything M11 says the residual edge is **narrow/name-specific among liquid names**, the opposite direction of the 20.6 bps headline.

Any Stage-A registration that treats “20.6 bps small-cap dislocation” as a **net** prior without subtracting entry half-spread is **not supported** by the primaries that survive this refute wave.

---

## Sources actually opened this pass

1. **[T2]** Bogousslavsky & Muravyev (June 2021 WP / JFM 2023). Full PDF. Tables 1, 4, 5. https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf
2. **[T2]** Goyal, Jegadeesh & Wu, JFQA 2026 (FirstView; DOI 10.1017/S0022109026102592). Cambridge full text + abstract. https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/price-impact-in-closing-auctions-opening-auctions-and-continuous-markets-a-benchmark-for-cost-of-trading-on-anomalies/0F72910A79C5B42CF6E85F55164CE846
3. **[T1]** Nasdaq Opening and Closing Crosses FAQ ©2025 / 1608-25. https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf
4. **[T1 project]** `research/experiments/M11-oos-28/report.md` (pooled net, sector table, hit_rate).
5. **[T1 project]** `research/ledger.jsonl` — `M11-xsection-oos-v1` (directional 0.470, sector list, verdict language).

### Queries used
1. `Bogousslavsky Muravyev "20.6" OR "2.66" auction deviation half-spread size quintile`
2. `Bogousslavsky Muravyev "9.56" OR "zero" auction days size quintile half-spread 7.56 0.55`
3. `Goyal Jegadeesh Wu Price Impact Closing Auctions Nasdaq microcaps JFQA`
4. Direct PDF open: B&M squarespace June 2021; Nasdaq openclose_faqs.pdf; Cambridge JFQA article body
5. Local: M11-oos-28 report + ledger.jsonl M11 entry
