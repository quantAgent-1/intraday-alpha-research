## DR-X5 — D adversarial findings
### Verdict recommendation
**NOT-VIABLE-STRUCTURAL** (confidence **HIGH**) — Liquidity-down does not create a free basis edge for a §1 retail manual book. Bogousslavsky–Muravyev (B&M) show that the headline small-stock |auction−4pm mid| of **20.6 bps** is essentially the **half-spread itself (~22 bps in the bottom size quintile)**, not residual free dislocation: sample-wide, average absolute deviation **8.12 bps** vs half-spread **7.56 bps**, and **68.5%** of auctions print exactly at pre-close bid or ask. Going down the liquidity curve therefore scales **cost and gross together**, so net-per-unit-spread is flat-to-worse. Goyal–Jegadeesh–Wu (GJ&W JFQA 2026) further show that closing-auction impact is *cheaper* than continuous **except for Nasdaq microcaps**, where auction impact is *higher* — the tier where 20.6 bps lives is exactly where auction economics flip against us. Project-internal **M11 already falsified a broad-Nasdaq mechanism** on 28 never-fit names (net **−3.02 bps**, directional 0.470); moving further into thin names is an anti-selected extension of a failed cross-section, not a new payer. Short-side borrow/locate and ~**10% zero-auction** days in small names destroy two-sided capacity even before half-spread arithmetic.

What would flip it: Owned SIP+NOII on a **mid-liquidity Nasdaq pilot** (ADV ~$50–200M, half-spread ≲5–8 bps at 15:55, auction almost always fires) showing residual |near−mid| **net of half-spread** ≥ **+4 bps/event** after honest continuous entry on ≥250 events — i.e. dislocation that is *not* just the quote. A pure re-run into microcaps with 15–30 bps half-spreads will not flip.

### Mechanism
**Thesis being killed ("smallness is the edge"):** Index/passive MOC is price-insensitive; thin books should produce larger NOII basis and larger auction vs mid gaps; at $1k–$10k size, impact is zero, so we harvest the larger gap that institutions cannot.

**Why that fails for us (adversarial):**
1. **Spread-eats-deviation (load-bearing kill).** B&M decompose absolute auction deviation = realized half-spread + price impact. Sample mean: half-spread **7.56 bps**, price impact **0.55 bps**. Bottom size quintile: |dev| **20.6 bps**, half-spread mean **~22 bps**. Large: |dev| **2.66 bps**, half-spread **~1.5 bps**, price impact **~1.2 bps**. The "bigger inefficiency" is almost entirely a wider bid-ask; residual beyond half-spread is small and **reverses overnight** (spread-adjusted reversal ≈ −0.95 to −0.98). A continuous taker entry at 15:55:10 *pays* that half-spread (plus adverse selection in a toxic last-5-min window); auction exit at the print does not refund entry cost. Net ≈ gross_basis − half_spread − AS ≲ 0 when |dev| ≈ half-spread.
2. **Payer is weaker, not stronger, down-curve.** ITG/The TRADE: S&P **large-caps grew MOC share more** than mid/small (by Q1 2018 large finished >1 pp above mid/small). Passive forced flow concentrates where index weights and ETF creation live — megacap/liquid mid — not in orphan microcaps. Thin names have thinner auctions *and* thinner continuous books; imbalance is often **idiosyncratic/informed** (earnings, news, retail short squeezes), not the indexed MOC payer that funds the champion.
3. **Toxic closes / adverse selection.** GJ&W: for Nasdaq **Micro**, closing-auction price impact **exceeds** continuous (e.g. 0.5% ADV auction impact **~31.6 bps** vs continuous **~15.6 bps** on Nasdaq micro). That is the opposite of the megacap auction-cheap regime. Joining a public NOII signal with-side in a thin book after 15:55 is joining the informed residual, not free-riding passive flow.
4. **NOII / cross sparsity.** B&M: **9.56%** of small-stock days have **zero auction volume** vs **0.21%** for large; **2.48%** overall. Nasdaq T1: if no Closing Cross, NOCP = last regular-way sale; late LOC after 15:55 requires a 15:55 reference price — if no crossing interest, late LOC is **not accepted**. Near/far are 0 until ~15:55 even on liquid names (project-owned history); on sparse books, indicative near is often uninformative or zero-imbalance (no tradeable basis ≥10 bps). Historical NOII per name is cheap (~$0.45/name-year), but **signal density** collapses — power dies before economics.
5. **Borrow/locate (short leg).** Champion is long *or* short with the basis. Hard-to-borrow is concentrated in small/low-float/controversial names (Acadian 2024: value-weight avg fee ~80 bp/yr easy; HTB tails 10–100%+ annualized; 100+ names/day >100%). Retail: Alpaca historically ETB-list constrained (HTB locate API only recently, 2026); IBKR inventory gaps on small-cap HTB are a known practitioner complaint. Same-day flat short still needs a locate at entry; HTB locate friction + rejection rate selectively removes the short half of events exactly where |dev| looks largest.
6. **20.6 bps is mostly untradeable micro/bottom-quintile structure, not a pilot universe.** B&M sample already filters P>$5 and mcap>$100M; the 20.6 figure is the **bottom mcap quintile of that filtered set**, further inflated by Tick Size Pilot binding ticks. True sub-$100M microcaps and sub-$5 names are worse (wider spreads, more zero auctions) and were never the champion habitat. M11's 28-name OOS (liquid-enough Nasdaq expansion names) already returned **coin-flip / negative** net — the tradeable frontier is **not** further down; if anything M11 says the frontier is a **narrow high-idiosyncratic-vol / high-activity subset of liquid names** (MU/NVDA/TSLA-like), the opposite of liquidity-down.

**Capacity intuition:** Notional capacity at $10k is irrelevant (true). **Economic** capacity is the binding constraint: half-spread + AS + short-side reject rate → expected net ≤ 0. No coherent incremental payer appears that is *both* larger *and* still net of our cost function.

### Claims
C1 [CONFIRMED] (T2, B&M J. Financial Markets 2023 / WP June 2021, sample NYSE+Nasdaq common stocks Jan 2010–Dec 2018, P>$5, mcap>$100M): Absolute auction−4pm-mid deviation averages **8.12 bps** overall; **20.6 bps** bottom size quintile vs **2.66 bps** top; sample half-spread mean **7.56 bps**; price impact residual mean only **0.55 bps** — so most "dislocation" **is** the half-spread. — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840 ; PDF https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf

C2 [CONFIRMED] (T2, same B&M, same sample): **68.5%** of auctions match pre-close best bid or ask (deviation = half-spread); tick binding in **41.8%**; deviations exceed half-spread in only **23.4%** of cases; Tick Size Pilot **causally raised** small-stock closing deviations. — same source

C3 [CONFIRMED] (T2, same B&M): Bottom size quintile half-spread mean **~22.2 bps** vs |dev| **20.6 bps** → **dev/half-spread ≲ 1** in the "20.6 bps" tier; large-stock half-spread **~1.47 bps** and price impact **~1.19 bps**. Net of entry half-spread, small-stock "edge" is not larger than large. — Table 5 + §3.2 text of WP PDF

C4 [CONFIRMED] (T2, same B&M): **9.56%** of small-stock days have **zero auction**; **0.72%** zero full-day volume; large: **0.21%** no auction. Auction volume *share* is similar across size (~5.7–6.1%), but **cross reliability collapses** in the tail — many "events" never print a cross. — Table 1 / §3.1

C5 [CONFIRMED] (T2, Goyal–Jegadeesh–Wu JFQA 2026 / SSRN 4300417, sample Jan 2012–Dec 2021 NYSE+Nasdaq): Closing-auction price impact is **lower than continuous for all size buckets except Nasdaq microcaps**. Nasdaq micro 0.5% ADV auction impact **~31.6 bps** vs continuous **~15.6 bps**; small Nasdaq 0.5%/5% ADV auction **8.8 / 27.9 bps**. Square-root 1% ADV mean impact **17.7 bps** (median 8.4). — https://doi.org/10.1017/S0022109025102592 ; Cambridge PDF

C6 [PLAUSIBLE] (T3, ITG / The TRADE "Liquidity is for Closers," Sep 2018, US equities ~2016–2018): S&P **large-cap names grew MOC share more than mid or small**; large finished **>1 percentage point** above mid/small by Q1 2018 after starting similar in Q2 2016. Passive-close flow is **not** preferentially a small-cap gift. — https://www.thetradenews.com/thought-leadership/liquidity-is-for-closers/

C7 [CONFIRMED] (T1, Nasdaq Opening & Closing Crosses FAQ / Rule 4754 mechanics, current): If a stock has **no Closing Cross**, NOCP = last regular-way last-sale eligible trade before 16:00; Late LOC after 15:55 requires a 15:55 Reference Price — if **no crossing interest**, late LOC **not accepted**. Thin-name "auction exit" is not guaranteed. — https://www.nasdaq.com/docs/2020/04/03/openclose_faqs.pdf ; Closing Cross FAQ https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf

C8 [CONFIRMED] (T1 project ledger + AGENT_BRIEF, M11 2026-07-17): Frozen champion-style rule on **28 never-fit Nasdaq names** (2023–2026, n=17,747): net **−3.02 bps [−3.46, −2.57]**, directional **0.470** (below coin flip), negative in all 6 sector buckets. Edge is **narrow / concentrated**, not a universal Nasdaq liquidity-down mechanism. Broadening *down* liquidity is the wrong direction given this OOS kill.

C9 [PLAUSIBLE] (T3, Acadian "Incredible Cost of Short Selling," May 2024; IBKR Campus borrow-fee notes 2025): Dollar-weighted US borrow is cheap (~**80 bp/yr** value-weight), but HTB tails are extreme (fees **10–100%+** annualized; 100+ names/day >100%); small/low-float/meme names dominate HTB. Retail short of the "fat deviation" side is friction-bound even for same-day flat. — https://www.acadian-asset.com/investment-insights/owenomics/the-incredible-cost-of-short-selling ; https://www.interactivebrokers.com/campus/traders-insight/securities/short-selling/the-risks-of-shorting-series-part-ii-borrow-fees/

C10 [PLAUSIBLE] (T1/T3, Alpaca forum + Alpaca HTB API launch Jun 2026; practitioner short-broker guides): Primary retail path (Alpaca) long relied on **ETB lists**; HTB locates were unavailable or non-API until recently; IBKR not a small-cap HTB specialist. Two-sided liquidity-down book is **structurally short-constrained** at retail. — https://alpaca.markets/blog/htb-trading-api-locates ; forum threads on ETB criteria

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **PASS (weak)** | 15:55:10 remains scheduled; 5–25 s ok *if* signal exists. Thin books move more in those seconds → latency cost **higher** than megacap, not lower. |
| 2 Access | **FAIL (short leg + auction exit)** | Long continuous entry possible; short needs locate (HTB common in tier); auction exit still blocked by retail CLS cutoffs (DR-Q4-6) and by **no-cross** days on thin names. |
| 3 Session | **PASS (narrow)** | Flat-at-close in-mission *when* a cross fires; ~10% small-name days it does not. |
| 4 Data | **PASS for hist / FAIL for live density** | Historical NOII cheap (~$0.45/name-yr; 20 names ~$15 in budget); live NOII still ~$199/mo. Density of usable near≠0 + |basis|≥10 bps events **drops** with ADV — n may fail Stage A without expanding years. |
| 5 Fill realism | **FAIL** | Entry pays half-spread that **equals** the measured "edge" in the small tier; continuous toxic window AS unmeasured and sign-negative; auction exit missing on no-cross days. |
| 6 Statistics | **FAIL / UNDERPOWERED at frontier** | Micro/zero-auction tail destroys event count; tradeable mid-tier (where spread does not eat all) is exactly where M11 already showed null. |
| 7 Protocol | **FAIL as "liquidity-down champion"** | Named payer (passive MOC) is **weaker** down-curve (ITG); pre-registering "smaller ADV → bigger net" contradicts B&M decomposition and M11. Would charge a trial family with a **negative prior**. |

**Survivor-profile score: 1/5**
1. Single-print/auction execution — **0** (no-cross days; retail CLS; continuous entry still pays spread)
2. Scheduled decision instant — **1** (15:55:10 schedule holds)
3. Named price-insensitive payer — **0** (payer thinner down-curve; residual often informed)
4. Historically testable cheaply — **0 for the claim that matters** (history tests gross |dev|, not net after half-spread; M11 already tests mid-tier and fails)
5. Expected effect ≥ 2× cost burden at size — **0** (cost ≈ gross in the 20.6 bps tier)

### Economics sketch
| Line | Gross / cost | Notes |
|------|----------------|-------|
| B&M small-stock \|auction−mid\| | **+20.6 bps** gross abs | Not a strategy return; unsigned deviation from mid |
| B&M small half-spread | **~22 bps** | Entry taker cost scale |
| B&M residual price impact (all) | **+0.55 bps** mean | The only part that is "beyond quote" |
| B&M large \|dev\| / half-spread | **2.66 / ~1.5 bps** | Residual ~1.2 bps impact — small absolute |
| GJ&W Nasdaq micro auction impact @0.5% ADV | **~31.6 bps** | Worse than continuous ~15.6 — toxic tier |
| Continuous half-spread mid/liquid mega (champion habitat) | **~1–5 bps** | Where champion lives |
| Continuous half-spread bottom-quintile / thin small | **15–30+ bps** | Where 20.6 lives |
| Short HTB fee (intraday prorated) | **0 to many bps/day** | Tail names; locate reject = zero fill |
| M11 28-name OOS net | **−3.02 bps/event** | Already the "not megacap" expansion |
| **Liquidity-down net prior (adversarial)** | **≤ 0 bps/event, often negative** | Gross scales with spread; residual does not clear 2× cost |
| Champion comparison | **+2.5 bps/event dev / +12.5 holdout** | Holdout concentration-caveated (MU); still the only positive sealed result — and it is **not** a small-cap result |

**Tradeable frontier (adversarial map):**
| Tier (illustrative) | \|dev\| prior | Half-spread prior | Net residual prior | Cross reliability | Verdict |
|---------------------|-------------|-------------------|--------------------|-------------------|---------|
| Mega / top liquid (champion names) | ~2–5 bps | ~1–4 bps | thin; need idio-vol + NOII basis filter | high | Only known positive habitat (narrow) |
| Upper mid / ADV ~$200M+ | ~4–8 bps | ~3–8 bps | **flat** | high | M11-like null expected |
| Liquid small / S&P 600 core ADV ~$50–100M | ~8–15 bps | ~8–15 bps | **≤0 after entry** | medium | Kill by spread arithmetic |
| Bottom B&M quintile / micro | **20.6 bps** | **~22 bps** | **≤0; often toxic** | low (~10% no auction) | **Untradeable "edge"** — do not pilot here |
| Sub-$100M / sub-$5 | larger | larger | worse + HTB | very low | Out of mission |

**Where the frontier actually sits:** not "further down ADV." If anywhere beyond the original-5, it is **high-activity, high-idiosyncratic-vol liquid Nasdaq** with reliable NOII near and half-spread still single-digit — i.e. **sideways or slightly down from mega, not into the 20.6 bps bin.** Liquidity-down as a registration thesis has a **negative prior**.

### Proposed next test (only if OPEN-TESTABLE)
*None as a liquidity-down champion probe.* Optional **measurement-only** (does **not** promote; does **not** charge a deploy family until residual clears):
- **Hypothesis (kill-seeking):** In Nasdaq names with 20d ADV ∈ [$50M, $200M], mean |near−mid| at 15:55:10 **minus contemporaneous half-spread** ≤ 0.
- **Data:** Owned SIP quotes + historical NOII (~$15 for ~20 names × few years).
- **Kill:** residual ≤ 0 on n≥250 → close the lane. Residual > +4 bps would reopen as **OPEN-TESTABLE** mid-tier (not micro).
- Do **not** register a "smaller is better" family; that hypothesis is already rejected by B&M decomposition + M11.

### Sources
1. **[T2]** Bogousslavsky, V. & Muravyev, D. (WP June 2021 / *J. Financial Markets* 2023). *Who Trades at the Close?* Sample 2010–2018. 8.12 / 20.6 / 2.66 bps; half-spread 7.56; 68.5% at bid/ask; 9.56% small zero-auction. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840 ; PDF https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf
2. **[T2]** Goyal, A., Jegadeesh, N. & Wu, Y. (JFQA 2026). *Price Impact in Closing Auctions…* Sample 2012–2021. Auction cheaper except Nasdaq microcaps; micro auction impact > continuous. https://doi.org/10.1017/S0022109025102592 ; SSRN 4300417
3. **[T2]** Jegadeesh, N. & Wu, Y. (JFE 2022). *Closing auctions: Nasdaq versus NYSE.* Temporary impact ~85% Nasdaq / ~62% NYSE; reverse 3–5d. Context only.
4. **[T3]** Clark, Giritharan & Stanton / ITG (Sep 2018). *Liquidity is for Closers.* The TRADE. Large-cap MOC share growth > mid/small. https://www.thetradenews.com/thought-leadership/liquidity-is-for-closers/
5. **[T1]** Nasdaq Closing Cross FAQ. NOII cadence, near/far, MOC 15:55 / LOC 15:58. https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf
6. **[T1]** Nasdaq Opening & Closing Crosses FAQ. No cross → NOCP = last sale; late LOC needs 15:55 ref. https://www.nasdaq.com/docs/2020/04/03/openclose_faqs.pdf
7. **[T3]** Acadian Asset Management (May 2024). *The Incredible Cost of Short Selling.* HTB fee tails; value-weight ~80 bp. https://www.acadian-asset.com/investment-insights/owenomics/the-incredible-cost-of-short-selling
8. **[T1/T3]** IBKR Campus (Jun 2025). *Risks of Shorting, Part II: Borrow Fees.* ETB vs HTB fee structure. https://www.interactivebrokers.com/campus/traders-insight/securities/short-selling/the-risks-of-shorting-series-part-ii-borrow-fees/
9. **[T1]** Alpaca (Jun 2026). HTB trading / locate API launch (implies prior ETB-only regime). https://alpaca.markets/blog/htb-trading-api-locates
10. **[T1 project]** AGENT_BRIEF + research/ledger.jsonl M11 result (2026-07-17): 28-name OOS net −3.02 bps, directional 0.470.
11. **[T3]** BMLL / Traders Magazine (2025). *Into the Close* — Russell-day dislocations elevated; liquid-name convergence cleaner on Nasdaq (context for tier toxicity). https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution
12. **[T1]** SEC/FINRA Reg SHO locate framework (context for retail short obligation). https://www.sec.gov/investor/pubs/regsho.htm

#### Queries used
1. `Bogousslavsky Muravyev closing auction small-cap 20.6 bps large-cap 2.66 half-spread`
2. `closing auction price impact Nasdaq microcaps Goyal Jegadeesh Wu 2026 spread`
3. `small cap closing auction adverse selection toxic flow NOII sparse imbalance`
4. `effective spread small-cap mid-cap US equities 15:55 end of day bps ADV tier`
5. `hard to borrow small cap short locate cost retail closing auction`
6. `"closing auction" small-cap OR microcap dislocation OR deviation spread 2020 2021 2022 2023 2024`
7. `Bogousslavsky Muravyev half spread size quintile auction deviation table small stocks`
8. `retail broker short stock hard to borrow Alpaca Interactive Brokers small cap locate`
9. `S&P 600 small cap average bid ask spread bps 2023 2024 ADV`
10. `closing auction volume share mid-cap small-cap vs large-cap MOC growth`
11. `Nasdaq NOII near far price zero thin stocks low volume closing cross participation`
12. `Nasdaq closing cross no auction no closing price thin stock low volume`
13. `Acadian short selling cost microcap hard to borrow fee annualized small cap`
14. `US equity average bid-ask spread small cap mid cap large cap basis points 2024 TAQ`
15. `Who Trades at the Close` PDF tables half-spread price impact size quintile (direct PDF read)
16. `Price Impact in Closing Auctions` Goyal JFQA 2026 Cambridge PDF (direct PDF read)
17. `Liquidity is for Closers` ITG The TRADE MOC large vs small (direct page read)

---

## Addendum — independent re-run corroboration (2026-07-21)

A fresh independent modality-D sweep (different sources) **corroborates the NOT-VIABLE-STRUCTURAL
HIGH verdict above** and adds three genuinely-new evidence points not in the original. No finding
contradicts the original; the spread-eats-deviation kill stands.

**New corroborating claims**
- A1 [CONFIRMED] (T3, NYSE Data Insights, sample **2023 YTD** — fresher than B&M's 2010–18): For
  stocks **not in the Russell 1000**, the immediate closing-auction price move is **< 0.3× the
  daily average spread** vs **0.34–0.40×** for Russell 1000, and "the market takes more time to
  digest and react to information in auctions of less-active stocks." Post-auction price *drift*
  0.5–0.9× spread (other) vs 0.6–1.7× (R1000). → Fresh, independent confirmation that the
  payer/signal is **weaker and slower down-curve**, reinforcing C6/ITG. —
  https://www.nyse.com/data-insights/closing-auction-immediate-market-impact-price-drift-and-transaction-cost-of-trading
- A2 [PLAUSIBLE] (T2, Morand, Imperial MSc 2021, TAQ): Closing-auction-imbalance return-prediction
  models have **R² → 0 (negative) beyond ~60 s** horizon; imbalance "contributes to price
  discovery for small stocks but only weak evidence for large stocks." → The NOII basis signal is
  short-horizon and fragile precisely where the thesis needs it strong; supports the density/
  power kill (gate 6). —
  https://www.imperial.ac.uk/media/imperial-college/faculty-of-natural-sciences/department-of-mathematics/math-finance/MORAND_CLEA_01805978.pdf
- A3 [CONFIRMED] (T3, BMLL 2024, Russell reconstitution): Even on the largest small-cap auction
  event, dislocation-from-mid spikes but closing prices stay **stable** with one-sided imbalances
  — the dislocation is a *known scheduled flow already priced in*, not a 5-min-ahead convergence a
  taker captures. Consistent with "residual beyond half-spread is small."

**New for the brief's deliverables (not in original): pilot-universe construction, no survivorship.**
Original gives the frontier *map* but no *point-in-time membership recipe*. If the orchestrator
ever runs the kill-seeking measurement-only test (§ "Proposed next test" above), use:
- **Point-in-time membership (free):** iShares **IJR** or SPDR **SPSM** historical daily-holdings
  CSVs via Wayback Machine snapshots; cross-check `pyndex` (GitHub, Russell reconstruction 1989+,
  WRDS-backed) and **Siblis Research** (constituents since 1996). Avoids selecting on survival.
- **Screen recipe:** primary listing = **Nasdaq** (NOII exists; NYSE names need unowned XNYS
  pillar) → 20-day median **$ADV ≥ $30M** (keeps borrow easy + half-spread ≲ ~15 bps, the only
  band worth measuring) → **price ≥ $10** (≤1,000 sh at $10k, whole-share friendly, avoids sub-$5
  microstructure) → exclude <6-mo IPOs, pending M&A, and names historically printing <~1,000
  on-close paired shares (cross reliability). Yields ~20 Nasdaq S&P-600 names, ADV $30–150M.
- Note this recipe deliberately targets the **upper** small-cap band — the original's frontier map
  already shows the sub-band (B&M bottom quintile / micro) is untradeable; a point-in-time IJR
  screen is how you *avoid* accidentally sampling that toxic tail.

**Odd-lot caveat (minor, additive):** odd-lot-vs-NBBO distortion is worst for *high-priced* names;
a $10–60 small-cap pilot is less exposed, though displayed round-lot size at 15:55 is thin (noisier
mid benchmark). SIP odd-lot dissemination begins **May 2026** — helps forward, not the historical
backtest. — SEC RegNMS 2024, https://www.sec.gov/newsroom/speeches-statements/gensler-statement-regulation-nms-091824

Bottom line of re-run: **verdict unchanged — NOT-VIABLE-STRUCTURAL, HIGH.** The independent sources
(2023 NYSE tier data, Imperial signal-fragility, BMLL Russell) all point the same way as B&M +
GJ&W + M11. The only thing added is a clean point-in-time universe recipe *for the measurement-only
kill test*, not a reason to reopen.

#### Queries used (re-run)
- closing auction small cap deviation from mid bid-ask spread transaction cost net
- Nasdaq closing cross NOII near far indicative price zero low activity small cap
- closing auction price efficiency adverse selection informed trading small illiquid stocks 2022 2023
- closing auction volume growth market cap liquidity BMLL research 2023 2024 dislocation
- closing auction price deviation reflects bid-ask spread noise not information small stocks reversal
- NYSE closing auction immediate market impact price drift transaction cost by tier
- closing auction imbalance predict price move mid to close small cap thin unreliable
- IJR / SPSM historical daily holdings point-in-time membership survivorship free; Russell reconstitution github pyndex Siblis
- odd-lot NBBO round lot small cap high priced stocks 2024 rule
- S&P 600 constituents easy to borrow general collateral short interest institutional ownership
