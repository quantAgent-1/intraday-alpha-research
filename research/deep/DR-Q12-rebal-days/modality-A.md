## DR-Q12 — A academic findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence **HIGH**) — Peer-reviewed and practitioner T2/T3 evidence uniformly shows that scheduled index reconstitution, quarterly S&P/Nasdaq rebalances, Russell June, month-end, and options-expiry (quad/triple-witch) days massively concentrate price-insensitive MOC/auction volume at the close; high-frequency work also documents nontrivial continuous→auction price pressure on actual additions/deletions (≈+9/−30 bps) that largely reverses overnight. No T2 paper, however, conditions **NOII near-price vs mid basis** (our champion signal) on those calendar cells for non-add/delete megacaps, so amplification of *our* edge is still an empirical free option on owned 2020–2026 NOII.

What would flip it: A pre-registered calendar split on owned NOII (rebal/month-end/quad-witch vs ordinary days) showing either (a) |basis| and/or signed basis→cross payoff **not** larger on forced-flow days (kill amplification), or (b) payoff larger but n too small to clear Stage-A power after multiple-testing charge (kill deployability, keep as base-rate note).

### Mechanism
**Who pays:** Index trackers, ETFs, and other close-benchmarked institutions that must match official closing prices / index weights on reconstitution and rebalance effective dates; also month-end reporters and options MMs dropping delta hedges on expiry. Flow is **price-insensitive** by mandate (minimize tracking error / cash-settle / report period-end NAV), not by information. Persistence follows from the legal/benchmark structure of passive AUM (Russell-linked AUM multi-trillion; S&P 500 tracker share still large) even as multi-day *announcement-to-effective* “index effect” has decayed—because much remaining demand is still scheduled into the closing auction itself. Capacity intuition: rebal days raise auction notional by multiples (often 5–6× marketwide close; ~30× on add/delete names), so *absolute* imbalance dollars rise, but liquidity provision also rises; whether **basis** (near − mid at 15:55) widens enough to lift bps/event for our non-event megacaps is the open question. Chinco–Sammon document “excess” recon-day volume ~3× pure ETF need concentrated at the close—consistent with a large, repeated forced-MOC payer pool.

### Claims
C1 [CONFIRMED] (T2, Bogousslavsky & Muravyev 2021/2023 journal version of “Who Trades at the Close?”, sample **2010–2018** US NYSE/Nasdaq common stocks, **NO full strategy cost model** for a basis trade): Closing-auction turnover is ~**230–900% higher** on Russell index rebalancing days (coeff 2.307 on log auction turnover; ≈e^2.307−1) and ~**138% higher** on month-end days, with pre-close (3:55–4:00) also elevated; third-Friday/options-expiry days also spike auction volume. Auction volume ~3,000% higher on S&P 500 add/delete rebalancing stock-days. Mean |auction−4pm mid| ≈ **8.1 bps** (half-spread 7.6 bps; impact 0.55 bps); ~85–95% of deviations reverse overnight. On S&P rebal days |auction deviation| rises ~**+21 bps** raw but is **insignificant after controlling for turnover**—auction “matches large volumes cheaply.” — https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf ; ScienceDirect abstract https://www.sciencedirect.com/science/article/abs/pii/S1386418123000502

C2 [CONFIRMED] (T3/T2-adjacent, Dimensional Hendrix/Liu/Roberts Mar 2025, US HF sample **2019–2023** on 10 US indices; multi-index 2014–2023; **costs measured as price pressure to indexers**, not retail basis P&L): On reconstitution day, continuous-to-closing-auction (≈10 s) relative price move vs non-rebalanced stocks: **additions +9 bps**, **deletions −30 bps**; overnight open reverse **−13 bps / +63 bps** respectively. Volume on recon day averages **23×** (up to 149× by index); final seconds ~**75×** prior-month; S&P 500 add/delete 4pm volume ~**109×**. 20-day pre-recon excess +3.9% with post reverse −4.4% (15 indices). — https://www.dimensional.com/se-en/insights/measuring-the-costs-of-index-reconstitution-a-global-perspective

C3 [CONFIRMED] (T2, Madhavan FAJ 2003, Russell **1996–2002**): Russell June reconstitution produces large addition/deletion return effects; Russell 3000 long-add/short-delete **mean June return +14.94%**, with July partial reverse (−4.97%); both temporary price pressure and permanent liquidity/membership components. Intraday volatility extreme on recon day; supplying immediacy profitable but high risk/cost. **DECAY-UNKNOWN for 2020s megacaps**; later work documents attenuation. — https://www.hillsdaleinv.com/uploads/The_Russell_Reconstitution_Effect,_Ananth_Madhaven,_Financial_Analysts_Journal,_JulyAugust_2003,_Pages_51-64.pdf

C4 [CONFIRMED] (T2, Greenwood & Sammon HBS WP 23-025 rev. Nov 2023, S&P 500 multi-decade through ~2020): Classic S&P addition abnormal return fell from **~7.4% (1990s) to ~0.3% (past decade)**; deletions from large negative to ~0; similar decline across other index families. Multiplier/elasticity rose sharply; front-running and migrations explain only part—liquidity provision improved. **Implication for DR-Q12:** multi-day index-effect alpha is largely exhausted, but that is *not* a kill of same-day closing-auction MOC pressure (orthogonal horizon). — https://www.hbs.edu/ris/Publication%20Files/23-025_563e45c6-df92-4d9c-ae05-608d4d0acab1.pdf

C5 [CONFIRMED] (T2, Chinco & Sammon Mar 2022 WP, Russell switchers **2001–2020**): Recon-day volume spikes with **no pre-recon run-up**; ETF rebalancing alone explains only ~1.39× average daily volume, but total relative volume implies **excess ≈3.15 shares per ETF share**, concentrated on recon day at the close. — https://www.alexchinco.com/excess-reconstitution-day-volume.pdf

C6 [CONFIRMED] (T3, Nasdaq Mackintosh Jun 2021; operational): On index rebalance days, ~**40% of MOC** estimated from index funds vs ~5% on normal days; close volumes typically **~6×** normal; triple/quad-witch open auctions ~10× and close ~5× (≈+$80B close). Large indexes (S&P, Nasdaq-100 Dec annual, FTSE global) schedule rebalances onto third-Friday liquidity. — https://www.nasdaq.com/articles/the-powerful-impact-of-triple-witching-2021-06-10

C7 [PLAUSIBLE] (T2, Baltussen/Da/Soebhag “End-of-Day Reversal” Apr 2025 WP, **1993–2019**): Cross-sectional end-of-day reversal in last 30 min **~3.78–6.86 bps/day** long-short (gross); authors attribute primarily retail attention + short-seller risk mgmt, **not** gamma/LETF alone; pattern is distinct from market intraday momentum. Useful as confounding continuous-window EOD effect, not as direct rebal-day NOII claim. **NO retail cost model for auction basis.** — https://academicweb.nd.edu/~zda/EOD.pdf ; SSRN abstract_id=5039009

C8 [CONFIRMED] (T2, Etula/Rinne/Suominen/Vaittinen RFS 2020 “Dash for Cash”, US focus **~1995–2013** and global): Month-end institutional cash/payment-cycle needs create systematic equity (and bond) price pressure and subsequent reversals; month-end is a genuine forced-flow calendar cell, not only index recon. Aligns with Bogousslavsky month-end auction-volume spike. — https://academic.oup.com/rfs/article/33/1/75/5494694

C9 [UNVERIFIED] (gap): **No T1/T2 source found that measures Nasdaq NOII near−mid basis magnitude or basis→16:00 cross payoff conditional on S&P/Nasdaq rebal, Russell June, month-end, or quad-witch**, for either add/delete names or continuous constituents. Literature measures volume, |auction−mid|, and multi-day add/delete returns—not our 15:55:10 basis object.

C10 [PLAUSIBLE] (T3, BMLL “Into the Close” Jun 2025 on **2024 Russell**): Recon day materially changes auction imbalance/dislocation/stability metrics; descriptive support that imbalance feeds carry rebal-day information, but vendor research (conflicted on auction data product). — https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **PASS** | Decision remains scheduled 15:55:10 snapshot; rebal is known calendar, no sub-5s need. |
| 2 | Access | **PASS** | Same retail MOC/LOC/taker-to-cross structure as champion; no new order types. |
| 3 | Session | **PASS** | Flat AT 16:00 cross; in-mission MOC/LOC exception. |
| 4 | Data | **PASS** | Owned Databento Nasdaq NOII 2020–2026 (5+28 names); calendar labels free (S&P/Nasdaq/Russell effective dates, month-end, third Fridays). $0 incremental. |
| 5 | Fill realism | **PASS** | Exit remains single 16:00 print; entry same as champion. |
| 6 | Statistics | **PASS with UNDERPOWERED-BY-DESIGN flag for pure rebal cells** | Ordinary + month-end days: n easily ≥250 events / ≥150 sessions on 2020–2026×names. Pure Russell June ≈1 day/year; S&P quarterly rebal days few; pooled “forced-flow calendar” (rebal ∪ month-end ∪ third-Friday) needed for power vs ~20 bps event noise. Per-name add/delete events rare in megacap 5-name core. |
| 7 | Protocol | **PASS** | Named payer = scheduled index/rebalance/month-end MOC; pre-registrable day-type dummies and a-priori |basis|≥10 bps (or stratified thresholds); charges a **calendar-conditioning / forced-flow amplification** trial family (new or under existing auction family—accounting note for harness). Holdout spent → forward M10 + M11 OOS only for promotion. |

**Survivor-profile score: 5/5**
1. Single-print/auction exit — yes  
2. Scheduled decision instant — yes (calendar known weeks ahead)  
3. Named price-insensitive payer — yes (index MOC / recon / month-end)  
4. Historically testable on owned or ≤$100 data — yes ($0)  
5. Expected effect ≥2× cost burden at size — yes if amplification ≥ champion baseline; else still free stratification of existing edge  

### Economics sketch
- **Cited gross (literature objects, not our P&L):** Dimensional continuous→auction pressure on **add/delete** stocks +9 / −30 bps (2019–2023); Bogousslavsky mean |auction−mid| 8.1 bps ordinary, +~21 bps raw on S&P rebal stock-days (volume-adjusted null); classic multi-week Russell June effects large historically but **decayed** for S&P-style adds. None of these equal “bps per basis trade.”
- **Our cost burden:** Same structure as champion (taker entry WITH basis ≤15:55:10; exit at cross). Alpaca zero commission through 2026-12-31; post-promo stress annotation only.
- **Net prior:** If rebal/month-end only **scales volume** without widening |basis| or hit-rate, expected **net ≈ champion** (+2.5 bps/event dev / +12.5 holdout) with higher notional opportunities but same bps. If |basis| and signed edge amplify with forced MOC intensity, **net > champion** on those cells—magnitude UNKNOWN until trial. Literature’s “auction cheap given volume” (C1) is a bearish prior on *extra* bps for already-liquid megacaps.
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**.

### Proposed next test (OPEN-TESTABLE)
- **Hypothesis:** On scheduled forced-flow calendar days (S&P/Nasdaq rebal effective closes, Russell June recon Friday, month-end, third-Friday/quad-witch), mean |NOII near−mid basis| at 15:55:10 and/or mean signed basis→16:00 cross payoff (when |basis|≥10 bps) is larger than on ordinary RTH sessions for owned Nasdaq names.
- **Named payer:** Index-tracker and benchmarked institutional MOC / recon closing-auction demand (plus month-end reporting and expiry hedge collapse as secondary cells).
- **Data:** Owned Databento Nasdaq NOII 2020→2026; 5 core + 28 M11 names; free public calendar of rebal/recon/month-end/third-Friday. $0.
- **Universe:** Primary = continuous large Nasdaq names in owned set (not only add/delete); secondary split = any name that is itself an add/delete/weight-change on that date if present.
- **Expected n & power:** Ordinary days dominate. Pooled forced-flow cells over 2020–2026: month-ends ≈72; third-Fridays ≈72; S&P quarterly rebal days ≈24; Russell ≈6; overlap on June third-Friday. With 5–33 names, event-days can exceed Stage-A n≥250 for **month-end ∪ third-Friday**; pure Russell/S&P-rebal alone is **UNDERPOWERED-BY-DESIGN** (report base rates, do not gate). Power vs σ≈20 bps/event: need large effect (≥5–10 bps mean lift) or pooled cells.
- **A-priori thresholds:** (i) primary: |basis|≥10 bps as champion; (ii) calendar dummy interaction on |basis| and on signed payoff; (iii) optional continuous proxy = auction/day volume ratio if available from SIP, else pure calendar.
- **Promotion rule:** Interaction significant at pre-reg α after family charge; holdout **not** reopened—forward M10 paper + M11 28-name OOS must show same sign lift; net bps/event on forced-flow days ≥ champion lower bound (~+2.5) after costs.
- **Kill criteria:** Interaction null or wrong-sign on full 2020–2026; or lift only on rare pure-recon days with n≪100; or lift only from add/delete names absent from deploy universe.
- **Trial family charged:** New **“auction calendar / forced-flow amplification”** family (or explicit sub-family of closing-auction basis)—do not bury under unregistered fishing.

### Sources
1. **[T2]** Bogousslavsky, V. & Muravyev, D. (2021 WP / 2023 J. Financial Markets). *Who Trades at the Close?* Sample 2010–2018. PDF: https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf ; journal: https://www.sciencedirect.com/science/article/abs/pii/S1386418123000502
2. **[T3]** Hendrix, K., Liu, J., Roberts, T. (Dimensional, 19 Mar 2025). *Measuring the Costs of Index Reconstitution: A Global Perspective.* US HF 2019–2023; multi-index 2014–2023. https://www.dimensional.com/se-en/insights/measuring-the-costs-of-index-reconstitution-a-global-perspective
3. **[T2]** Madhavan, A. (2003). *The Russell Reconstitution Effect.* FAJ 59(4). Sample 1996–2002. https://www.hillsdaleinv.com/uploads/The_Russell_Reconstitution_Effect,_Ananth_Madhaven,_Financial_Analysts_Journal,_JulyAugust_2003,_Pages_51-64.pdf
4. **[T2]** Greenwood, R. & Sammon, M. (rev. Nov 2023). *The Disappearing Index Effect.* HBS WP 23-025. https://www.hbs.edu/ris/Publication%20Files/23-025_563e45c6-df92-4d9c-ae05-608d4d0acab1.pdf
5. **[T2]** Chinco, A. & Sammon, M. (17 Mar 2022). *Excess Reconstitution-Day Volume.* Sample 2001–2020. https://www.alexchinco.com/excess-reconstitution-day-volume.pdf
6. **[T3]** Mackintosh, P. (Nasdaq, 10 Jun 2021). *The Powerful Impact of “Triple Witching.”* https://www.nasdaq.com/articles/the-powerful-impact-of-triple-witching-2021-06-10
7. **[T2]** Baltussen, G., Da, Z., Soebhag, A. (Apr 2025 WP). *End-of-Day Reversal.* Sample 1993–2019. https://academicweb.nd.edu/~zda/EOD.pdf ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5039009
8. **[T2]** Etula, E., Rinne, K., Suominen, M., Vaittinen, L. (2020). *Dash for Cash.* RFS 33(1). https://academic.oup.com/rfs/article/33/1/75/5494694
9. **[T3]** BMLL Technologies (24 Jun 2025). *Into the Close… Russell Reconstitution.* https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution
10. **[T3]** LSEG / FTSE Russell recon FAQ (ops). Closing notional figures e.g. Jun 2025 NYSE/Nasdaq close moments. https://www.lseg.com/en/ftse-russell/russell-reconstitution
11. **[T2 abstract-only / related]** Madhavan, A., Ribando, J., Udevbulu, N. (2022). *Demystifying Index Rebalancing.* JPM 48(6)—recent rebalance cost framing; full PDF not retrieved here.
12. **[T2 related]** Beckmeyer et al. / LETF+options EOD pressure papers (end-of-day mechanical rebalancing; complementary payer, not calendar-rebal primary).

#### Queries used
1. `index reconstitution price pressure S&P Russell rebalance closing auction academic paper`
2. `Russell reconstitution price impact closing prices MOC flow SSRN`
3. `S&P 500 rebalancing day end-of-day price pressure forced flow academic`
4. `index rebalance month-end quad witching closing auction imbalance basis`
5. `"Closing Auction, Passive Investing, and Stock Prices" Bogousslavsky Muravyev`
6. `end-of-day reversal closing auction institutional flow paper sample period bps`
7. `month-end rebalancing price pressure closing auction MOC academic paper`
8. `Bogousslavsky Muravyev institutional price pressure close sample period bps auction`
9. `Madhavan 2003 Russell reconstitution effect price pressure bps sample`
10. `S&P Nasdaq rebalance closing auction MOC imbalance larger basis pressure site:ssrn.com OR site:arxiv.org`
11. `Wu "Closing Auction Passive Investing" MOC price impact rebalancing days sample`
12. `Madhavan Ribando Udevbulu 2022 demystifying index rebalancing costs liquidity`
13. `"NOII" OR "indicative near price" OR "imbalance" rebalance reconstitution closing auction basis`
14. `Etula Rinne Suominen Vaittinen month-end price pressure sample period`
