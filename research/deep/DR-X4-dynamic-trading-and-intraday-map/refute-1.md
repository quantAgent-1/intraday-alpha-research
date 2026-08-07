# DR-X4 — Refuter-1 (claim verification)

**Date:** 2026-07-18  
**Role:** Independent primary-source refuter (default `refuted=true` if no T1/T2 primary located).  
**Scope:** Six load-bearing claims from DR-X4 modality synthesis (dynamic trading + intraday map).  
**Rule:** CONFIRMED requires a refuter-located T1/T2 primary. PLAUSIBLE is not used here — each row is binary `refuted` true/false + reason.

---

## Summary table

| # | Claim (compressed) | Primary found? | refuted | Status for synthesis |
|---|--------------------|----------------|---------|----------------------|
| R1 | GP JF 2013 / NBER 15205: partial adj. \(x_t=(1-a/\lambda)x_{t-1}+(a/\lambda)\mathrm{aim}_t\); aim in front of Markowitz; slow signals weighted more under costs | YES T2 | **false** | CONFIRMED |
| R2 | Quadratic costs → continuous partial trade (no no-trade band); no-trade bands under proportional/linear costs (Constantinides / Davis–Norman) | YES T2 | **false** | CONFIRMED |
| R3 | Gao–Han–Li–Zhou JFE 2018: first HH (prev close→10:00) predicts last HH on SPY | YES T2 | **false** | CONFIRMED |
| R4 | Rosa J. Futures Markets 2022: post-pub / OOS overnight→last-HH link disappears on ES futures | YES T2 | **false** | CONFIRMED |
| R5 | Lou–Polk–Skouras JFE 2019: overnight vs intraday clientele tug-of-war; overnight momentum / intraday anomalies split | YES T2 | **false** | CONFIRMED |
| R6 | No published T2 retail minutes–hours multi-name US equity inventory book with honest continuous fills at ~$1–10k survives | Negative search; closest T2 fails constraints | **false** | CONFIRMED (gap claim; no counterexample) |

**Net:** 0/6 refuted. All six survive primary-source checks. Caveats and scope limits are noted per claim (they do not flip `refuted`).

---

## R1 — Gârleanu–Pedersen partial adjustment / aim portfolio

**Claim:** Gârleanu–Pedersen (*JF* 2013 / NBER WP 15205): optimal policy is partial adjustment  
\(x_t = (1-a/\lambda)x_{t-1} + (a/\lambda)\,\mathrm{aim}_t\) toward an aim portfolio that aims in front of Markowitz; slow signals weighted more under costs.

**refuted: false**

**Primary located (T2):**
- NBER WP 15205 (Aug 2009), full PDF: https://www.nber.org/system/files/working_papers/w15205/w15205.pdf  
- Author PDF (Mar 2012 preprint of JF version): https://nbgarleanu.github.io/DynTrad.pdf  
- Journal: *Journal of Finance* 68(6), 2309–2340, Dec 2013, DOI 10.1111/jofi.12080

**What the primary states (verbatim structure):**
1. Abstract: optimal strategy = (i) **aim in front of the target** and (ii) **trade partially towards the current aim**; aim is a weighted average of current Markowitz and expected future Markowitz; **predictors with slower mean reversion get more weight**.
2. Proposition 2 (Trade Partially Towards the Aim):  
   \(x_t = x_{t-1} + \Lambda^{-1}A_{xx}(\mathrm{aim}_t - x_{t-1})\); under Assumption A (\(\Lambda=\lambda\Sigma\)) trading rate is scalar \(a/\lambda < 1\), so  
   \(x_t = (1 - a/\lambda)\,x_{t-1} + (a/\lambda)\,\mathrm{aim}_t\).  
   \(a\) is decreasing in transaction cost \(\lambda\) and increasing in risk aversion \(\gamma\).
3. Proposition 3 (Aim in Front of the Target): aim = exponential average of current and future Markowitz portfolios.
4. Proposition 4 (Weight Signals Based on Alpha Decay): with diagonal \(\Phi\), each factor \(f^k\) scaled by \(1/(1+\varphi^k a/\gamma)\) — persistent (small \(\varphi\)) down-weighted less; relative weight of slow vs fast **increases** in costs.

**Attempted refutation angles (failed):**
- Wrong formula / wrong journal year: **fail** — formula matches under Ass. A; JF 2013 + NBER 15205 confirmed.
- “Always trade to Markowitz”: **fail** — paper explicitly rejects that; aim ≠ Markowitz when TC > 0.
- Empirical half of claim overstated for equities: **out of scope** — claim is about the *theory* policy; empirical illustration is commodity futures, not a refutation of the policy math.

**Caveat (does not refute):** Empirical commodity illustration uses 5-day / 12-month / 5-year signals (half-lives days–years), not hourly equity residuals. Theory still applies to any AR signal speeds.

---

## R2 — Quadratic costs: continuous partial trade vs proportional no-trade band

**Claim:** Under quadratic costs, GP implies continuous partial trade (NO no-trade band); no-trade bands arise under proportional (linear) costs (Constantinides / Davis–Norman).

**refuted: false**

**Primary located (T2):**
1. **GP contrast (same sources as R1):** DynTrad.pdf literature section:  
   *“Our trade-partially-towards-the-aim strategy is qualitatively different from the optimal strategy with proportional or fixed transaction costs, which exhibits periods of no trading.”*  
   Continuous-time companion: Gârleanu & Pedersen, *Dynamic Portfolio Choice with Frictions*, *Journal of Economic Theory* 165 (2016) 487–516; WP https://w4.stern.nyu.edu/facdir/lpederse/papers/DynamicPortfolioChoiceWithFrictions.pdf — again: strategy with proportional/fixed costs “exhibits long periods of no trading”; quadratic → smooth finite-turnover trading.
2. **Constantinides (1986):** *Capital Market Equilibrium with Transaction Costs*, *JPE* 94(4), 842–862. Abstract: with proportional TC, policy characterized by a **region of no transactions** (interval). JSTOR/IDEAS: https://ideas.repec.org/a/ucp/jpolec/v94y1986i4p842-62.html
3. **Davis & Norman (1990):** *Portfolio Selection with Transaction Costs*, *Mathematics of Operations Research* 15(4), 676–713. Formal continuous-time solution with proportional costs; optimal policy = local time at boundaries of a **no-trade region** (buy/sell barriers).

**What holds:**
- Quadratic (linear price impact / TC quadratic in trade size) → always trade a fraction toward aim (rate \(a/\lambda \in (0,1)\)); no inaction region in the GP setup.
- Proportional (linear in |trade|) or fixed costs → inaction / no-trade band; trade only when portfolio exits the band (to the boundary).

**Attempted refutation angles (failed):**
- “GP also has a no-trade band”: **fail** — GP’s own text contrasts against that literature.
- “Retail half-spreads are proportional, so GP irrelevant”: **not a refutation of the claim** — claim is about the *theoretical mapping* cost technology → policy shape, not about which technology retail faces. (Useful design note: retail may approximate proportional half-spread with a hard no-trade band of width ~ cost^{1/3}-class, per classic asymptotics — still consistent with the claim.)

---

## R3 — Gao–Han–Li–Zhou market intraday momentum (SPY)

**Claim:** Gao–Han–Li–Zhou (*JFE* 2018): first half-hour predicts last half-hour market momentum on SPY.

**refuted: false**

**Primary located (T2):**
- Working paper PDF (June 2017 / first draft Mar 2014): https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/ee7dac49-530b-4950-b5d0-e0b5eee08f2e.pdf (SSRN 2440866 lineage)
- Journal: *Journal of Financial Economics* 129(2), 394–414, 2018 — https://doi.org/10.1016/j.jfineco.2018.05.009 ; IDEAS: https://ideas.repec.org/a/eee/jfinec/v129y2018i2p394-414.html

**What the primary states:**
- Sample: high-frequency **S&P 500 ETF (SPY)** **1993–2013**.
- First half-hour return = return from **previous day’s market close** through first 30 min of RTH (**includes overnight gap**), predicts last half-hour return (15:30–16:00).
- In-sample \(R^2 \approx 1.6\%\) (\(r_1\) alone); \(\approx 2.6\%\) with \(r_{12}\) (15:00–15:30). OOS \(R^2_{OS} \approx 1.4\%\) / \(2.0\%\).
- Sign-timing on \(r_1\): ~**+6.67% ann** average return, sd ~6.19%, Sharpe ~**1.08** vs buy-hold ~0.29; mean-variance CER gains ~**6.02%** (γ=5). Stronger on high-vol, high-volume, recession, major macro-news days.
- Also present for other liquid ETFs; similar with S&P futures (internet appendix).

**Attempted refutation angles (failed):**
- “Not SPY / not first→last HH”: **fail** — primary uses SPY and that exact design.
- “Only abstract-level; no quantities”: **fail** — full WP PDF read; quantities above are in abstract/body.
- Post-2013 decay (Rosa): **does not refute the 2018 paper’s in-sample claim**; it is a separate OOS claim (R4).

**Caveats (do not flip refuted):**
- Units = annualized last-HH market-timing PnL, **not** bps/event on a multi-name book.
- First HH includes overnight — not a pure 09:30–10:00 open bar.
- Post-decimalization net-of-spread results exist in paper but still pre-2014 sample for full economics.

---

## R4 — Rosa (2022) post-publication / OOS disappearance on ES

**Claim:** Rosa (*Journal of Futures Markets* 2022): post-publication OOS of overnight/last-HH momentum link **disappears** on ES futures.

**refuted: false**

**Primary located (T2):**
- Carlo Rosa, “Understanding Intraday Momentum Strategies,” *Journal of Futures Markets* 42(12), 2218–2234, Dec 2022. DOI: 10.1002/fut.22375  
- Full-text body confirmed via Wiley abstract + vLex full article text: https://onlinelibrary.wiley.com/doi/abs/10.1002/fut.22375 ; https://law-journals-books.vlex.com/vid/understanding-intraday-momentum-strategies-1049461706  
- Author page: https://sites.google.com/view/carlorosa/research

**What the primary states:**
- Data (§2): **5-min prices on E-mini S&P 500 (ES)** futures; continuous front-month; sample **September 1997 – December 2020**. Explicit choice of futures over cash for lower TC / integration with cash.
- Design: overnight return predicts last half-hour return (extension of Gao et al. 2018).
- OOS protocol: McLean–Pontiff-style split into in-sample / post-sample / post-publication; Gao sample ends 2013 → ~7 years of live data after.
- **Main result:** *“I document that the predictability disappears in the out-of-sample period. The disappearance of the relationship, rather than decay, suggests that the predictability of returns is likely due to data mining.”*
- Markov-switching: two regimes; high-predictability state rare in 2014–2020 (mostly Mar–Dec 2020 COVID window). Thresholded strategy (trade only when |overnight| large) improves craftsmanship alpha when active.

**Attempted refutation angles (failed):**
- “Rosa is not on ES / not futures”: **fail** — primary §2 is E-mini S&P 500.
- “Rosa only finds gradual decay, not disappearance”: **fail** — primary language is **disappears**, not gradual decay; author interprets as data-mining consistent.
- “Rosa contradicts Gao in-sample”: **fail** — Rosa is an OOS extension; does not claim Gao’s IS result is a fabrication of code.

**Caveats:**
- Kill is on **ES futures OOS**, not a sealed SPY cash OOS paper of equal length. Equity SPY post-2013 peer-reviewed OOS remains thinner → DECAY-LIKELY for cash, CONFIRMED kill for futures path.
- Regime view: calendar OOS can miss high-predictability states; still does **not** reinstate an always-on overnight→last-HH edge for 2014–2019.

---

## R5 — Lou–Polk–Skouras overnight vs intraday tug-of-war

**Claim:** Lou–Polk–Skouras (*JFE* 2019): overnight vs intraday clientele tug-of-war; overnight momentum / intraday anomalies split.

**refuted: false**

**Primary located (T2):**
- Dong Lou, Christopher Polk, Spyros Skouras, “A tug of war: Overnight versus intraday expected returns,” *Journal of Financial Economics* 134(1), 192–213, 2019. DOI: 10.1016/j.jfineco.2019.03.011  
- Author PDF: https://personal.lse.ac.uk/polk/research/TugOfWar.pdf  
- Alternate: https://personal.lse.ac.uk/loud/ATugofWar.pdf

**What the primary states:**
- Strong overnight and intraday firm-level return **continuation** with **cross-period reversal**, lasting years.
- Sort on past 1-month **overnight** returns: overnight 3-factor alpha **+3.47%/month** (t≈16.8); intraday alpha **−3.02%/month** (t≈−9.7).
- Sort on past **intraday**: intraday alpha **+2.41%/month** (t≈7.7); overnight **−1.77%/month** (t≈−7.9).
- Across **14 trading strategies**: profits earned **entirely overnight** (reversal + momentum family) **or entirely intraday** (value, profitability, investment, etc.), often with opposite-sign other component.
- Explicit: *“transaction costs will make the actual profitability of a trading strategy exploiting these overnight/intraday patterns much less attractive.”*
- Institutional tug-of-war linked especially to momentum decomposition.

**Attempted refutation angles (failed):**
- “Only about open/close microstructure bounce”: **fail** — authors stress multi-year lag persistence and joint t > 20; mid-quote robustness discussed in related versions; patterns last up to 60 months.
- “Momentum is not overnight-only”: **fail** — primary: 100% of abnormal returns on momentum strategies occur overnight in their decomposition.
- Wrong journal/year: **fail** — JFE 2019 confirmed.

**Caveat for enginev5.1 mission:** Overnight leg is **out-of-session** under flat-15:50/MOC RTH rule. Claim itself is still true as field fact.

---

## R6 — No T2 retail minutes–hours multi-name inventory book with honest continuous fills @ ~$1–10k

**Claim:** No published T2 retail minutes–hours multi-name US equity inventory book with honest continuous fills at ~$1–10k survives.

**refuted: false** (gap claim stands; no counterexample located)

**Search coverage (negative claim protocol):**
Queries used (see appendix). Targets: peer-reviewed / SSRN / arXiv q-fin for multi-name US equity continuous/minutes–hours books with realistic TC and small notional.

**Closest T2 priors (do NOT falsify the claim):**

| Paper | Why it fails the claim’s constraints |
|-------|--------------------------------------|
| Avellaneda & Lee, *Quantitative Finance* 10(7), 2010, 761–782 — “Statistical arbitrage in the US equities market” | Multi-name PCA/ETF residual MR; **5 bps/trade (10 bps RT)** costs; Sharpe ~1.44 (1997–2007) → **~0.9 (2003–2007)**. **Daily EOD** estimation / multi-day holds — **not** minutes–hours continuous fills; not retail $1–10k inventory; institutional universe. PDF: https://traders.berkeley.edu/papers/Statistical%20arbitrage%20in%20the%20US%20equities%20market.pdf |
| Gatev, Goetzmann, Rouwenhorst *RFS* 2006 pairs | Multi-day pairs; commissions era; not minutes–hours continuous retail |
| Do & Faff *J. Fin. Research* 2012 | Pairs largely unprofitable **after 2002** once commissions + impact + short fees enter — opposite of a surviving edge |
| Bowen, Hutchinson, O’Sullivan (2010 WP) high-frequency pairs | Shows **extreme** sensitivity: +15 bp TC cuts returns >50%; **one-period execution delay eliminates** excess returns — supports *impossibility* at manual retail latency |

**What would flip R6 to refuted=true:** A T2 (or T1 performance) paper documenting a multi-name US equity book that (i) holds minutes–hours (not multi-day EOD only), (ii) uses continuous-market fills with condition-coded / quote-realistic costs (not mid-touch fantasy), (iii) sizes at ~$1k–$10k per name or total plan, (iv) survives net of costs out-of-sample post-2010. **None found.**

**Epistemic status:** Universal negatives are unprovable; status is **coverage-backed gap**, not metaphysical impossibility. For synthesis, treat as CONFIRMED gap under §6 evidence rules (“If you cannot establish something, write UNKNOWN” / coverage note). Closest honest-cost multi-name prior (Avellaneda–Lee) is **wrong horizon and wrong size class**.

---

## Cross-claim notes for synthesizer

1. **R1–R2 are theory CONFIRMED** — usable as position-engine math. They do **not** by themselves prove a retail edge; GP deweights *fast* signals under costs (indicts pure hourly residual chase if IC is low).
2. **R3 CONFIRMED historically; R4 CONFIRMED as OOS kill on ES** — pure first→last HH market momentum is not a durable standalone payer for M16.
3. **R5 CONFIRMED** — overnight/intraday clientele structure is real; overnight capture is out-of-mission without user rule change.
4. **R6 CONFIRMED as gap** — no T2 template for the exact retail continuous multi-name minutes–hours book; any M16 trial is **first-of-class under honest fills**, not a replication of a published profitable retail book.

**Majority rule:** 0/6 refuted → none of these six claims die in verification. Downstream verdict still depends on economics + gates (not this refuter’s job).

---

## Sources (≥6; tiered)

1. **[T2]** Gârleanu, N. & Pedersen, L.H. (2009/2013). *Dynamic Trading with Predictable Returns and Transaction Costs.* NBER WP 15205; *Journal of Finance* 68(6), 2309–2340. https://www.nber.org/system/files/working_papers/w15205/w15205.pdf ; https://nbgarleanu.github.io/DynTrad.pdf  
2. **[T2]** Gârleanu, N. & Pedersen, L.H. (2016). *Dynamic Portfolio Choice with Frictions.* *Journal of Economic Theory* 165, 487–516. WP: https://w4.stern.nyu.edu/facdir/lpederse/papers/DynamicPortfolioChoiceWithFrictions.pdf  
3. **[T2]** Constantinides, G.M. (1986). *Capital Market Equilibrium with Transaction Costs.* *JPE* 94(4), 842–862. https://ideas.repec.org/a/ucp/jpolec/v94y1986i4p842-62.html  
4. **[T2]** Davis, M.H.A. & Norman, A.R. (1990). *Portfolio Selection with Transaction Costs.* *Mathematics of Operations Research* 15(4), 676–713.  
5. **[T2]** Gao, L., Han, Y., Li, S.Z. & Zhou, G. (2018). *Market Intraday Momentum.* *JFE* 129(2), 394–414. WP PDF: https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/ee7dac49-530b-4950-b5d0-e0b5eee08f2e.pdf ; DOI: https://doi.org/10.1016/j.jfineco.2018.05.009  
6. **[T2]** Rosa, C. (2022). *Understanding Intraday Momentum Strategies.* *Journal of Futures Markets* 42(12), 2218–2234. DOI: https://doi.org/10.1002/fut.22375 ; body via vLex: https://law-journals-books.vlex.com/vid/understanding-intraday-momentum-strategies-1049461706  
7. **[T2]** Lou, D., Polk, C. & Skouras, S. (2019). *A tug of war: Overnight versus intraday expected returns.* *JFE* 134(1), 192–213. https://personal.lse.ac.uk/polk/research/TugOfWar.pdf ; DOI: https://doi.org/10.1016/j.jfineco.2019.03.011  
8. **[T2]** Avellaneda, M. & Lee, J.-H. (2010). *Statistical arbitrage in the US equities market.* *Quantitative Finance* 10(7), 761–782. https://traders.berkeley.edu/papers/Statistical%20arbitrage%20in%20the%20US%20equities%20market.pdf  
9. **[T2]** Do, B. & Faff, R. (2012). Pairs trading profitability post-costs (post-2002 wipeout). *Journal of Financial Research* — used as negative control for R6.  
10. **[T2 meta]** McLean, R.D. & Pontiff, J. (2016). Post-publication anomaly decay framework (cited by Rosa for OOS split design).

#### Queries used
1. `Gârleanu Pedersen Dynamic Trading with Predictable Returns and Transaction Costs JF 2013 NBER 15205`
2. `Gao Han Li Zhou first half-hour predicts last half-hour market return SPY JFE 2018`
3. `Rosa overnight last half-hour momentum ES futures post-publication Journal of Futures Markets 2022`
4. `Lou Polk Skouras Tug of War overnight intraday momentum JFE 2019`
5. `Constantinides proportional transaction costs no-trade band Davis Norman 1990`
6. `Carlo Rosa Understanding Intraday Momentum Strategies Journal Futures Markets 2022 ES futures out-of-sample`
7. `Avellaneda Lee Statistical Arbitrage equity markets 2010 retail continuous fills minutes hours`
8. `retail statistical arbitrage minutes hours multi-stock continuous fills honest costs equity`
9. `"Understanding Intraday Momentum Strategies" Rosa "E-mini" OR "ES" OR "S&P 500 futures"`
10. `Gârleanu Pedersen Dynamic Portfolio Choice with Frictions Journal of Economic Theory 2016`
11. `"Gârleanu" Pedersen Journal of Finance 2013 "Dynamic Trading" volume pages`
12. `site:researchgate.net Rosa Understanding intraday momentum strategies ES E-mini`

#### PDFs / pages fully or substantially read
- NBER w15205.pdf; nbgarleanu DynTrad.pdf  
- DynamicPortfolioChoiceWithFrictions.pdf (Stern)  
- Gao et al. Market Intraday Momentum WP PDF (super.so)  
- Lou–Polk–Skouras TugOfWar.pdf  
- Rosa JFM article body (vLex extract of §§1–2 + abstract results)  
- Avellaneda–Lee QF 2010 PDF (Berkeley traders copy)
