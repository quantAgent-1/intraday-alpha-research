## DR-Q12 — C practitioner findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence **MED**) — Practitioner/vendor consensus strongly confirms that rebalance, month-end, and quad-witch days amplify closing-auction volume (~2× share of day; Russell/S&P rebal closes often 6× notional vs normal) and elevate mid→close dislocation / notional imbalance, driven by price-insensitive MOC from passive indexers minimizing tracking error. Multi-day “index effect” harvesting of adds/deletes is field-known and largely decayed to ~0 post-2010s (crowded institutional desk trade); pure overnight reverse after rebal prints is also competed. The *intraday* 15:55 basis→16:00-cross structure on special days is the relevant overlay for the live champion and is **not** pre-empted by practitioner claims of full crowding of that micro-window on our megacap universe. Test as calendar/regime stratification of the existing NOII basis rule on owned data (no new $).

What would flip it: Owned stratified holdout/forward where mean |basis| or event PnL on rebal∪ME∪quad days is **not** ≥1.5× non-special days at matched |basis|≥10 bps (or net after costs fails 2× burden vs champion baseline).

### Mechanism
**Who pays:** Passive/index-tracking funds and ETFs (~$10–12T+ benchmarked to Russell US; multi-trillion S&P family) forced to rebalance at the official close on effective dates so the fund print equals the index print (tracking-error / career risk dominates price). Secondary payers on the same calendar: month-end/quarter-end portfolio rebalancers, option dealers dropping delta hedges into the close on expiry, and flow desks packaging MOC.

**Why price-insensitive:** Index methodology incorporates the closing auction price; buying earlier risks tracking error if the name moves against the fund before 16:00. Ryedale’s “indexer dilemma”: MOC zeros TE but maximizes impact paid to liquidity providers.

**Why it persists:** Indexed AUM has grown even as multi-day announcement→effective edges decayed (anticipatory capital + predictability). The residual pressure concentrates into the last minutes and the single-print auction; exchanges explicitly solicit offsetting liquidity (Nasdaq IO, NYSE CO/D-orders, Significant Imbalance post-cutoff MOC/LOC).

**Capacity intuition:** Institutional multi-name reconstitution books are capacity-constrained and crowded at desk scale (5–10× levered baskets). For a $10k retail MOC/basis ticket in liquid megacaps, capacity is not the binding constraint; *edge size and hit-rate amplification vs baseline champion* is. Small-cap Russell adds/deletes show larger mid→close prints than megacaps — our owned universe is the harder, smaller-effect end.

### Claims
C1 [CONFIRMED] (T3, 2025-06-24, sample 2024–2025 auction L3 / Russell 2024 day): On typical 2024 days closing auctions match ~$50B (~9% of daily volume); on index rebalance or option-expiration days the auction share rises to ~**20%** of daily volume. Russell Reconstitution 2024 final moments: NYSE **$275B** + Nasdaq **$103B**; auction volume for major Russell 1000 adds >34% of that day’s notional. Mid→close dislocation and absolute notional imbalance **spike** on Russell Day vs non-event; next-open stability was not outsized in their liquid-add sample. — BMLL / Traders Magazine, https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

C2 [CONFIRMED] (T3/T1-adjacent, 2026-06-26, event day): Nasdaq Closing Cross on 2026 Russell reconstitution executed **4.59B shares / $334.027B** in ~1.63s (record; prior 2025: $102.5B). Confirms rebal-day auction as the year’s largest single liquidity event and primary venue for forced index flow. — Nasdaq IR, https://ir.nasdaq.com/news-releases/news-release-details/record-trading-volume-nasdaq-closing-cross-during-june-2026

C3 [CONFIRMED] (T3, 2025-03 / sample 2019–2023 reconstitutions, **gross** relative to non-rebal stocks): Dimensional: additions **+9 bps** from end of continuous (4pm mid) to closing auction (~≤10s), reverse **−13 bps** by next open; deletions **−30 bps** mid→close, reverse **+63 bps** next open. Volume multipliers on rebal stocks up to **27×** (S&P 500 window) / **112×** (S&P 600 4pm window). Same pattern for index *share changes* at smaller scale (2% weight change ≈ 0.15 bps mid→close, 0.55 bps reverse). NO-COST-MODEL for a taker basis trade; documents the exact mid→close print the champion structure harvests. — Dimensional / Alpha Architect summary, https://www.dimensional.com/se-en/insights/measuring-the-costs-of-index-reconstitution-a-global-perspective ; https://alphaarchitect.com/cost-of-index-rebalancing/

C4 [CONFIRMED] (T3, 2022-05, practitioner exec): Index managers face the MOC dilemma — trade MOC for zero TE and pay impact to counterparties who know the flow, or take TE risk trading early/late. Explicit that “other market participants … trade against indexers.” Harvest paths: pre-trade, post-trade delay, ADV-participation schedules, projections vs pro-forma. — Ryedale (Rushman), https://www.ryedale.com/insights/thought-leadership/planning-and-executing-index-rebalance-trades

C5 [CONFIRMED] (T3, 2026-07-14, practitioner note; cites Greenwood/Sammon): Multi-day S&P add/delete free lunch decayed: add announcement→effective ~**+7%** (1990s) → **~0.8% / ~0** (2010s); deletes similarly near zero. Forced buying did not shrink — edge moved into more sophisticated probability-weighted, hedged, levered (5–10×) reconstitution books. Closing auctions now ~**9.4%** of US dollar volume (Q2 2024 peak cited), ~**20%** on big rebal days. — Alphanume Research, https://alphanume.substack.com/p/a-cracked-quants-guide-to-the-index (partial free; abstract-level quantities from free section + Greenwood/Sammon)

C6 [CONFIRMED] (T2, Greenwood & Sammon JoF 2025 / working paper 1980–2020): S&P 500 addition abnormal return fell from ~**7.4–7.6%** (1990s) to **<1% / ~0.3–0.8%** (2010s); deletions from large negatives to ~**−0.1 to −0.6%**. Multi-day index-effect harvest = EXHAUSTED-BY-FIELD for new research; residual is microstructure at the close. — https://onlinelibrary.wiley.com/doi/10.1111/jofi.13410

C7 [CONFIRMED] (T2/T3, Bogousslavsky & Muravyev 2021 working paper; sample 2010–2018 NYSE+Nasdaq common stocks): Closing auction ~**7.5%** of daily $ volume (2018, up from 3.1% in 2010). Mean |close − 4pm mid| = **8.1 bps** (half-spread 7.6 bps); matches pre-close bid or ask in 68.5%; exceeds **63 bps** in 1% of auctions. Deviations reverse almost fully overnight (uninformed pressure). Auction volume spikes on **index rebalancing days and end-of-month days** and on option expiries (MM hedge drop). ETF/passive ownership strongly associated with auction volume. — https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf

C8 [CONFIRMED] (T1/T3, NYSE Data Insights 2024-11-04 + 2023-08-22): Month-ends still produce mass Significant Imbalance flags (e.g. **435** symbols 2024-10-31 under new dynamic thresholds). Flag explicitly marketed as “significant trading opportunities” — post-3:50 offsetting MOC/LOC allowed to 16:00. Immediate impact of large late auction orders on R1000: ~**0.3× daily avg spread** at ~2.5% CADV size; impact rises in last 3 minutes. Confirms ME is a known high-imbalance regime and that offsetting the published imbalance is a *designed* participant role. — https://www.nyse.com/data-insights/the-nyse-significant-imbalance-enhanced-trading-opportunities-at-the-nyse-closing-auction ; https://www.nyse.com/data-insights/closing-auction-immediate-market-impact-price-drift-and-transaction-cost-of-trading

C9 [PLAUSIBLE] (T3, various 2021–2026): Quad-witch / S&P quarterly rebalance days: closing volume ~**26%** of daily (vs ~10% normal); Russell rebal day ~**30%**. Nasdaq estimate: on index rebalance days close volumes ~**6×** normal and ~**40%** of MOC attributable to index funds (vs ~5% normal days). Volume amplification is robust; *directional* equity edge from quad-witch alone is not practitioner-consensus (volume ≠ volatility). — Traders Magazine closing-volume notes; Nasdaq “Powerful Impact of Triple Witching” (2021, cited in secondary); Investopedia/Cboe structural notes.

C10 [PLAUSIBLE] (T3/T4 mixed): Close-imbalance strategies are **known and partially crowded** as a category: exchanges and retail vendors (MarketChameleon MOC screens, NYSE SI marketing) advertise them; Reddit practitioners report month-end/quarter-end MOCs “provide opportunity” while daily MOC has “less edge”; institutional reconstitution is openly described as a major desk franchise. **Unknown** whether the specific 15:55:10 NOII-basis→cross rule on rebal days is saturated in our 5–28 name liquid set — that is the empirical question. No practitioner source claims that mid–indicative basis at 15:55 is fully arbitraged to zero on special days in megacaps.

### Constraint gates
| # | Gate | Result | Note |
|---|------|--------|------|
| 1 | Latency | **PASS** | Decision instant scheduled (15:55 NOII / known calendar); 5–25 s manual fine. |
| 2 | Access | **PASS** | Retail MOC/LOC or continuous taker + exit at cross; Alpaca/IBKR order types; $1k–$10k whole shares. |
| 3 | Session | **PASS** | Flat AT 16:00 cross via MOC/LOC or single-print exit — in-mission. |
| 4 | Data | **PASS** | Owned Databento Nasdaq NOII + SIP ticks/quotes; calendar of Russell/S&P/ME/quad is free. No new feed. |
| 5 | Fill realism | **PASS** | Same champion structure: enter taker with basis, exit single auction print — no continuous-exit ambiguity. |
| 6 | Statistics | **PASS** if stratification / **UNDERPOWERED-BY-DESIGN** if pure rebal-only | Pure Russell days ~1–2/yr (semi-annual from 2026); S&P quarterly + ME ≈ 12–16 special sessions/yr. Prefer: filter all champion events by special-day flag (n reuses full NOII history). Power vs ~20 bps/event noise needs n≥250 pooled. |
| 7 | Protocol | **PASS** | Named payer (indexed MOC / ME rebal / expiry hedge drop) stated a priori; calendar flags pre-registrable; charges a **calendar-conditioning sub-family of the auction-basis family**, not a new freestanding edge. |

**Survivor-profile score: 5/5** (as champion overlay)
1. Single-print/auction execution — yes  
2. Scheduled decision instant — yes  
3. Named price-insensitive payer — yes (indexed MOC; amplified on calendar)  
4. Historically testable on owned / ≤$100 data — yes (owned)  
5. Expected effect ≥2× cost burden at size — **hypothesis** (amplification of already-passing champion); must clear empirically  

If framed as pure rebal-day-only standalone: drop to **3/5** (stats/power and rare-event capacity fail).

### Economics sketch
- **Gross cited (external, special-day mid→close pressure):** Dimensional reconstitution adds **+9 bps** / deletes **−30 bps** mid→close (2019–2023, relative, gross, rebal names vs non-rebal). Bogousslavsky unconditional mean |dev| **8.1 bps**. Champion live: dev **+2.5 bps/event**, holdout **+12.5 bps/event [6.9, 18.5]**.  
- **Amplification prior (practitioner):** Special days show larger |imbalance| and dislocation (BMLL qualitative spike; volume 2–6×). Plausible special-day gross for a ≥10 bps basis filter: **1.5–3×** non-special mean — prior only, not a claim.  
- **Our cost burden:** Same as champion (taker entry spread + any MOC fee; zero commission through 2026-12-31). Auction exit = single print.  
- **Net prior:** If amplification holds, special-day net should clear champion by construction; if competition tightens basis on special days, filter may *reduce* rate of |basis|≥10 bps events even as conditional mean rises — both moments must be measured.  
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**.

### Proposed next test (OPEN-TESTABLE)
**Hypothesis:** On Nasdaq names in the owned NOII universe, the existing 15:55:10 basis rule (|near − mid| ≥ 10 bps, taker with basis, exit at 16:00 cross) has higher mean event PnL and/or higher |basis| distribution on **special days** (Russell recon effective, S&P/other major index rebal effective, month-end, quad-witch Friday) than on ordinary RTH sessions.

**Named payer:** Indexed MOC / ME institutional rebal / expiry delta-hedge drop (price-insensitive scheduled flow).

**Data:** Owned Databento Nasdaq NOII 2020→2026 + SIP mids; free calendar flags. **$0** incremental.

**Universe:** Champion core (NVDA/TSLA/AMD/MU/GOOGL) + M11 28-name expansion where NOII owned.

**Expected n & power:** Special-day *sessions* ~15–25/yr × ~5–28 names with |basis|≥10 → tens to low hundreds of special events over 2020–2026; pool with non-special for interaction test. Power interaction term vs ~20 bps sd: report CI; flag UNDERPOWERED if special n < 80.

**A-priori thresholds:**  
- Primary: special-day mean PnL − ordinary mean PnL ≥ **+2 bps/event** at matched |basis| gate, or special-day P(|basis|≥10) and E[PnL | fire] jointly dominate ordinary on a pre-registered score.  
- Secondary: |basis| distribution stochastically larger on special days (KS / quantile at p50/p90).

**Promotion rule:** Special-day stratum clears ≥ champion holdout lower bound on its own CI **or** interaction term positive with p pre-registered and not driven by top-2 sessions/names (concentration kill).

**Kill criteria:** Special mean ≤ ordinary mean; or special fires are 100% concentration in one name (MU-style); or next-open reverse absorbs the print such that any *overnight* extension fails (out-of-mission anyway).

**Trial family charged:** Auction-basis calendar-conditioning sub-family (extends live champion; does **not** open a new multi-day index-effect family — that is field-exhausted).

### Sources
1. **[T3]** BMLL / Laible & Thakur, “Into the Close: Unpacking U.S. Closing Auction Dynamics and the Impact of the Russell Reconstitution,” 2025-06-24. https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution  
2. **[T1/T3]** Nasdaq IR, “Record Trading Volume on the Nasdaq Closing Cross During the June 2026 Russell Reconstitution,” 2026-06-26. https://ir.nasdaq.com/news-releases/news-release-details/record-trading-volume-nasdaq-closing-cross-during-june-2026  
3. **[T3]** Dimensional (Hendrix/Liu/Roberts), “Measuring the Costs of Index Reconstitution: A Global Perspective,” 2025-03-19. https://www.dimensional.com/se-en/insights/measuring-the-costs-of-index-reconstitution-a-global-perspective  
4. **[T3]** Dimensional, “Another Hidden Cost for Index Funds: Index Share Changes,” 2025-08-29. https://www.dimensional.com/nl-nl/insights/another-hidden-cost-for-index-funds-index-share-changes  
5. **[T3]** Alpha Architect, “Index rebalancing: what it really costs investors,” 2025-03-21 (Dimensional summary). https://alphaarchitect.com/cost-of-index-rebalancing/  
6. **[T3]** Ryedale / Jon Rushman, “Planning and Executing Index Rebalance Trades,” 2022-05-17. https://www.ryedale.com/insights/thought-leadership/planning-and-executing-index-rebalance-trades  
7. **[T3]** Alphanume Research, “A Cracked Quant’s Guide to The Index Rebalancing Trade,” 2026-07-14 (partial free). https://alphanume.substack.com/p/a-cracked-quants-guide-to-the-index  
8. **[T2]** Greenwood & Sammon, “The Disappearing Index Effect,” *Journal of Finance* 80(2) 2025 / NBER. https://onlinelibrary.wiley.com/doi/10.1111/jofi.13410  
9. **[T2]** Bogousslavsky & Muravyev, “Who Trades at the Close? Implications for Price Discovery and Liquidity,” 2021-06-02. PDF: squarespace link above.  
10. **[T1/T3]** NYSE Data Insights, “The NYSE Significant Imbalance…,” 2024-11-04. https://www.nyse.com/data-insights/the-nyse-significant-imbalance-enhanced-trading-opportunities-at-the-nyse-closing-auction  
11. **[T1/T3]** NYSE Data Insights, “Closing Auction: Immediate market impact, price drift…,” 2023-08-22. https://www.nyse.com/data-insights/closing-auction-immediate-market-impact-price-drift-and-transaction-cost-of-trading  
12. **[T3]** Cboe Insights, “Russell Reconstitution: Opportunities to Harvest Volatility,” 2022-06-03 (vol/options harvest path; not cash basis). https://www.cboe.com/insights/posts/russell-reconstitution-opportunities-to-harvest-volatility/  
13. **[T3]** CME Group, “The 2026 Russell Reconstitution…” (BTIC/EFRP institutional avoidance of cash auction), 2026-05. https://www.cmegroup.com/articles/2026/the-2026-russell-reconstitution.html  
14. **[T3]** LSEG / FTSE Russell reconstitution facts (AUM, semi-annual 2026, close notional). https://www.lseg.com/en/ftse-russell/russell-reconstitution  
15. **[T3]** ITG Bacidore et al., “Trading Around the Close,” 2012 (auction mechanics; rebalance vs flow strategy difference). https://mrtopstep.com/wp-content/uploads/2024/02/ITG-Trading-Around-The-Close-11-7-2012-1-1.pdf  
16. **[T4 hypothesis only]** r/FuturesTrading “Do you trade MOO/MOC imbalances?” (ME/QE more opportunity than daily). https://www.reddit.com/r/FuturesTrading/comments/1e8zk5h/do_you_trade_moo_moc_imbalances/

#### Queries used
- rebalance day closing auction MOC edge traders  
- quad witching month-end close imbalance strategy crowded  
- index reconstitution harvest closing auction practitioner  
- Russell reconstitution MOC flow basis trade  
- month end rebalancing MOC imbalance trade edge crowded  
- "closing auction" imbalance strategy crowded decay OR capacity  
- index rebalancing trade additions deletions close pressure practitioner blog  
- site:reddit.com MOC imbalance trade rebalance month end edge  
- "basis" OR "indicative" closing auction rebalance day dislocation bps  
- month-end equity rebalancing close pressure bps practitioner quant  
- "closing auction" "price pressure" OR dislocation rebalance "basis points" OR bps additions deletions  
- "imbalance only" OR "IO orders" OR "offset imbalance" closing auction arb crowded HFT  
- quad witching closing auction volume MOC rebalance same day  
- BMLL Russell Day auction dislocation mid price closing basis points magnitude  
- Greenwood Sammon disappearing index effect S&P additions returns 2010s  
