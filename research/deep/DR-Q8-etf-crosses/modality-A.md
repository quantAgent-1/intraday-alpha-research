## DR-Q8 — A academic findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence **MED**) — Peer-reviewed auction/ETF literature does **not** support the claim that the Nasdaq closing-auction **basis** edge is larger or more reliable on liquid ETFs (QQQ, SMH, SOXX, sector) than on single names. Indexed/MOC forced flow is documented primarily in **underlying stocks** (ETF/passive *ownership of stocks* → auction volume/elasticity in those stocks); ETF *vehicles* show **lower** auction-volume share (~2–3% of ADV on Arca ETFs vs ~9–14% on equity listing venues) and **small** auction deviations similar to large-cap stocks (~3.6 bps mean abs. deviation for SPY/QQQ/S&P-sector ETFs). Creation/redemption is a **primary-market NAV** process that can be hedged by MOC-ing underlyings rather than concentrating MOC on the ETF print. No T2 paper runs the champion rule (15:55:10 NOII near vs mid, |basis|≥10 bps, take with basis, exit at cross) on ETFs vs names — so the question remains empirically open but the academic prior leans **against** larger ETF edge.
What would flip it: Out-of-sample replication of champion economics on Nasdaq-listed ETFs (QQQ/SMH/SOXX) with |basis|≥10 bps events delivering ≥+2.5 bps/event gross (dev-quality) or holdout-comparable means with n≥250 — *despite* the prior that |basis| fire rate and magnitude should be smaller on mega-liquid ETFs.
### Mechanism
**Who pays (literature):** Price-insensitive **index mutual funds and passive trackers** MOC into **constituent stocks** to minimize tracking error to closing prices used for NAV/benchmarking; option MMs unwind delta at the close on expiration; month-end/window-dressing and index rebalance days spike auction volume. ETF *ownership of a stock* is a strong predictor of that stock’s auction turnover (elasticity spikes at the auction, not pre-close).
**Why not concentrated on the ETF share:** True index funds typically hold the basket, not the ETF. Secondary-market ETF MOC is discretionary (investors wanting the ETF’s official close) and is small as a % of ETF ADV. APs/arbitrageurs keep ETF price near IIV/NAV intraday; creations/redemptions settle at end-of-day NAV, and practitioners note brokers can MOC underlyings then create to lock NAV. Leveraged-ETF daily rebalance can transmit force into **underlyings**, not necessarily into the LETF’s own cross.
**Persistence / capacity intuition:** Auction price pressure on stocks is structural while passive AUM grows; on mega-liquid ETFs, continuous depth + AP competition should **compress** pre-close basis and raise competition for any residual. Capacity on QQQ/SMH notional is huge, but expected bps edge is the binding constraint — literature implies smaller deviations and less forced one-sided MOC on the ETF itself.
**No coherent payer found for “ETF MOC more forced than single-name MOC”** — the forced payer is concentrated *into* names that ETFs own, not *onto* the ETF ticker.
### Claims
C1 [CONFIRMED] (T2, JFM 2023 / WP June 2021, sample 2010–2018 NYSE+Nasdaq common stocks): Closing auction rose from ~3.1% to ~7.5% of daily dollar volume; ETF and **passive** mutual-fund ownership (not active) strongly raise **auction** turnover with auction-vs-pre-close DiD elasticities Auction×ETF +0.055 / Auction×Passive +0.068; auction absolute deviation from 4pm mid averages **8.1 bps** (large-cap ~2.7 bps), matches bid or ask in 68.5% of cases, and **~85% reverses overnight** (noise/price pressure, not information). — Bogousslavsky & Muravyev, *Who Trades at the Close?*, J. Financial Markets 2023; https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf
C2 [CONFIRMED] (T2, same paper, footnote on large ETFs): For large ETFs (SPY, QQQ, S&P sector ETFs) auction price deviations **behave like large stocks**: mean abs. deviation **3.63 bps**, 99th pct **16.32 bps** — *not* larger than the stock universe mean. — Bogousslavsky & Muravyev 2021/2023, same URL.
C3 [CONFIRMED] (T3, BMLL market insight Jun 2025; sample May 2025 / Russell 2024 context): NYSE Arca (primary ETF listing venue) has **~2% of volume in the closing auction vs ~9% for NYSE equities**; indicative/mid path on Arca is noisier/less convergent; “Brokers can trade the underlying equities MOC, and then package those into the desired ETF guaranteeing the NAV risk free.” — BMLL, *Into the Close…*; https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution
C4 [CONFIRMED] (T3, Tethys Auction Volume Report Americas, Aug 2025): Notional-weighted closing auction volume %: **ARCA 2.93%**, BATS 2.06% vs **NYSE 14.03%**, **NSDQ 9.18%**; authors attribute low Arca/BATS shares to **ETF-dominated listings with low auction participation** (exceptions: illiquid or non-US-focused ETFs). — https://www.tethystech.com/wp-content/uploads/2025/08/Auction-Volume-Report-Americas_August.pdf
C5 [CONFIRMED] (T2, JFE 2022, sample ~decade ending 2019): Closing-auction volume ~10% ADV peak; NYSE deeper than Nasdaq; temporary price impact dissipates over **3–5 days**; **imbalance-sorted reversal strategies significantly profitable** on **stocks** (gross, NO-COST-MODEL relative to retail half-spread+fees at our size). Does **not** isolate ETFs as a superior venue for the edge. — Jegadeesh & Wu, *Closing auctions: Nasdaq versus NYSE*, JFE 2022; https://doi.org/10.1016/j.jfineco.2021.12.003
C6 [PLAUSIBLE] (T2, FAJ 2017 / WP 2011, multi-year multi-ETF sample): ETF price–NAV deviations exist and mean-revert; average premium small for liquid domestic equity ETFs but premium **volatility** material in less liquid/international sleeves (~tens of bps); strategy alpha **pre-cost**. This is **EOD premium/discount vs NAV**, not the champion’s **intraday NOII near vs continuous mid basis into the cross** — different object. — Petajisto, *Inefficiencies in the Pricing of Exchange-Traded Funds*; http://www.petajisto.net/papers/etf28.pdf
C7 [CONFIRMED] (T2, JF 2018 / NBER, US equity ETFs ~2000–2015): Higher ETF **ownership of a stock** raises that stock’s volatility (~+16% daily vol per 1 SD ownership); channel is ETF–underlying arbitrage transmitting noise — again points to pressure on **underlyings**, not a larger auction-basis edge on the ETF ticker. — Ben-David, Franzoni & Moussawi, *Do ETFs Increase Volatility?*
C8 [PLAUSIBLE] (T2 abstract/SSRN, Comerton-Forde & Rindi 2021/22): Elevated auction activity (esp. rebalance days) produces large auction returns from last continuous price in European markets; mixed evidence on whether high CCA volume harms quality. Not a US ETF-vs-stock basis comparison. — SSRN abstract_id=3903757
C9 [UNVERIFIED] (gap): No T1/T2 source reports fire rate, mean bps/event, or hit-rate of a **|NOII near − mid| ≥ 10 bps @ ~15:55** rule on QQQ/SMH/SOXX/IWM vs single names. Listing constraint: **Nasdaq NOII applies to Nasdaq-listed names** (QQQ, SMH, SOXX yes; SPY/IWM primarily Arca → need Arca imbalance product, not owned).
C10 [CONFIRMED] (T1 mechanics context via literature): Creation unit value is tied to **end-of-day NAV**; secondary auction on the ETF is not the creation market. — ICI ETF FAQs / standard AP mechanics (consistent across sponsor docs).
### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **PASS** | Same scheduled 15:55:10 decision + MOC/LOC or take-to-cross path as champion; 5–25 s manual OK. |
| 2 | Access | **PASS** | Retail brokers offer MOC/LOC on major ETFs; whole shares at $1k–$10k trivial for QQQ/SMH. |
| 3 | Session | **PASS** | Flat at 16:00 via auction exit — in-mission. |
| 4 | Data | **PASS** (Nasdaq ETFs) / **OPEN-BLOCKED-lite** (Arca ETFs) | Databento XNAS NOII historical ~tens $/name-decade (owned pattern); Arca imbalance not purchased (XNYS/Arca pillar). |
| 5 | Fill realism | **PASS** | Same single-print auction exit as champion. |
| 6 | Statistics | **PASS** | Daily sessions × multi-year → n≫250 if threshold fires; power still needs ~20 bps event noise check. |
| 7 | Protocol | **PASS** | Named payer (indexed MOC) pre-statable; pre-register thresholds; charges auction/basis trial family; holdout spent → forward or never-fit ETF symbols only. |

**Survivor-profile score: 4/5**
1. Single-print/auction exec — **yes** (+1)
2. Scheduled decision instant — **yes** (+1)
3. Named price-insensitive payer — **yes for stocks; weak/diluted on ETF vehicle itself** (+0.5 → score as partial; tally **+1 only if we treat “same mechanism family”**; strict: **0.5**) — **tally as 4** counting mechanism present but mis-located (underlyings)
4. Historically testable ≤~$100 — **yes** for QQQ/SMH/SOXX NOII (+1)
5. Expected effect ≥2× cost — **UNKNOWN a priori; literature prior suggests smaller |basis| → may fail** (no point awarded) → **4/5** with effect-size caveat
### Economics sketch
- **Expected gross (cited):** Stocks: auction abs. mid-deviation ~2.7–8 bps mean (size-dependent); large ETFs **~3.6 bps** mean abs. (Bogousslavsky). Champion *signed* edge was **+2.5 bps/event dev / +12.5 holdout** on a **selected** |basis|≥10 bps filter on 5 semis — not the unconditional mean deviation. Literature gives **no** ETF-specific filtered mean for the champion rule.
- **Our cost burden:** Auction exit = single print (0 exit spread); entry taker ~ half-spread+slip on ultra-liquid ETFs often **≤1–2 bps** (better than mid-tier single names). Zero commission through 2026-12-31.
- **Net prior:** If |basis|≥10 bps **fires rarely** on QQQ/SMH (tighter continuous+AP arb), n collapses and edge may be **zero**; if it fires, **gross may be similar in structure but not larger**. Prior vs champion: **do not expect ETF gross > single-name champion**; more likely **smaller fire rate / similar or smaller bps**.
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**.
### Proposed next test (only if OPEN-TESTABLE)
- **Hypothesis:** Champion rule on Nasdaq-listed ETFs (QQQ, SMH, SOXX; optional SOXL as stress) does **not** beat single-name economics; mean bps/event |basis|≥10 bps @ 15:55:10 ≤ single-name pooled mean (one-sided).
- **Named payer:** Residual MOC/LOC into ETF for close-price/NAV sync + any unhedged AP flow — secondary to underlying MOC.
- **Data:** Databento Nasdaq NOII + SIP mid for QQQ/SMH/SOXX, 2020→2026; budget ~$30–80 one-time (scale of M11 $38 for 28 names). **Owned:** bar anchors QQQ/SMH/SOXX/SPY already; NOII for ETFs = purchase. **Exclude** SPY/IWM until Arca imbalance budgeted.
- **Universe:** QQQ, SMH, SOXX primary; sector Nasdaq ETFs optional.
- **Expected n & power:** If fire rate ~same as liquid large-caps, multi-year daily → n>500; if fire rate << names, underpowered — report fire-rate as primary kill metric. Noise ~20 bps/event → need large n for 2–3 bps mean.
- **A-priori thresholds:** Signal at 15:55:10 if |near−mid|/mid ≥ 10 bps; direction with basis; exit auction print; no ML first pass.
- **Promotion:** Pooled gross ≥ +2.5 bps/event and hit-rate ≥55% on pre-registered window with n≥250 → stage-B forward paper only (holdout spent).
- **Kill:** Fire rate <1 event/week across trio; or gross ≤0 net of 2 bps entry burden; or all edge concentrated in <5 sessions.
- **Trial family charged:** Closing-auction basis / M11-adjacent ETF expansion (do not re-fit single-name champion).
### Sources
1. **[T2]** Bogousslavsky, V. & Muravyev, D. (2023). Who trades at the close? Implications for price discovery and liquidity. *Journal of Financial Markets* 66:100852. (WP June 2021 PDF read in full.) Sample 2010–2018. https://doi.org/10.1016/j.finmar.2023.100852 / PDF mirror above.
2. **[T2]** Jegadeesh, N. & Wu, Y. (2022). Closing auctions: Nasdaq versus NYSE. *Journal of Financial Economics* 143(3):1120–1139. https://doi.org/10.1016/j.jfineco.2021.12.003
3. **[T2]** Petajisto, A. (2017 FAJ / 2011 WP). Inefficiencies in the Pricing of Exchange-Traded Funds. http://www.petajisto.net/papers/etf28.pdf (PDF read).
4. **[T2]** Ben-David, I., Franzoni, F. & Moussawi, R. (2018). Do ETFs Increase Volatility? *Journal of Finance*. NBER w20071. Sample ~2000–2015 US equity ETFs.
5. **[T3]** BMLL (2025-06-24). Into the Close: Unpacking U.S. Closing Auction Dynamics… https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution (full page read).
6. **[T3]** Tethys (2025-08). Auction Volume Report: Americas. https://www.tethystech.com/wp-content/uploads/2025/08/Auction-Volume-Report-Americas_August.pdf (PDF read).
7. **[T2]** Comerton-Forde, C. & Rindi, B. (2021/22). Trading @ the Close. SSRN 3903757 (abstract + secondary cites; full PDF Cloudflare-blocked).
8. **[T2]** Wu, Y. (2019 WP). Closing Auction, Passive Investing, and Stock Prices. SSRN 3440239 (abstract/secondary cites; passive→MOC channel).
9. **[T1/T3]** Nasdaq Closing Cross / NOII mechanics (dissemination 15:50; near/far). https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf
10. **[T3]** SSGA (2026-01). Closing time: How passive investing is reshaping equity market microstructure. https://www.ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure

#### Queries used
1. `ETF closing auction imbalance predictability premium discount MOC`
2. `ETF creation redemption closing auction MOC flow academic paper SSRN`
3. `"closing auction" ETF vs stocks imbalance basis edge`
4. `site:ssrn.com ETF closing auction imbalance`
5. `Closing Auction Passive Investing Stock Prices Bogousslavsky Muravyev`
6. `Trading at the Close auction returns ETF passive flow SSRN`
7. `ETF premium discount closing price NAV arbitrage academic paper`
8. `Nasdaq closing cross ETF NOII imbalance predictability vs stocks`
9. `"market on close" ETF volume concentration QQQ SPY auction`
10. `Wu Jegadeesh Closing auctions Nasdaq versus NYSE price impact JFE`
11. `ETF auction volume lower than equities NYSE Arca closing cross`
12. `Petajisto inefficiencies pricing exchange traded funds premium volatility`
13. `Wu closing auction passive investing MOC ETF flows stock prices 2019`
14. `ETF creation redemption end of day NAV MOC underlying stocks timing academic`
15. `Ben-David Franzoni Moussawi ETFs increase volatility underlying auction`
16. `"ETF" "closing auction" "imbalance" OR "order imbalance" predictability OR basis OR premium site:arxiv.org OR site:ssrn.com`
17. `QQQ SMH SOXX IWM primary listing exchange Nasdaq Arca`
18. `Databento Nasdaq NOII ETF symbols available historical`
