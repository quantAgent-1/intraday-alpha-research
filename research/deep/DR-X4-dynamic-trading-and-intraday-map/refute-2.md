# DR-X4 — Independent refuter #2 (wave 1)

**Role:** Independent REFUTER. Attempt to REFUTE load-bearing claims via primary T1/T2 sources.  
**Default:** `refuted=true` if a primary T1/T2 source supporting the claim cannot be located (or if the primary text contradicts the claim).  
**Date:** 2026-07-18  
**Scope:** Same wave-1 claim bundle as twin: GP formulas; quadratic vs proportional bands; Gao 2018; Rosa 2022 OOS kill; LPS 2019; no retail minutes–hours honest-cost book.

**Method:** Fetched and read NBER WP 15205 (GP 2009), GP continuous-time WP (2014/JET 2016), Gao–Han–Li–Zhou WP/JFE path, LPS *JFE* 2019 full text (LSE PDF), Rosa abstract + secondary cites; Janeček–Shreve / asymptotic no-trade literature for \(c^{1/3}\) scaling; targeted search for retail min–hr honest-cost counterexamples.

---

## Claim bundle summary

| ID | Claim (load-bearing one-liner) | refuted | Status if survives |
|----|--------------------------------|---------|-------------------|
| R1 | GP closed-form partial trade toward aim + scalar \(a/\lambda\) under Ass. A + signal decay weights | **false** | CONFIRMED (T2) |
| R2 | Quadratic TC ⇒ always trade a little; proportional TC ⇒ no-trade band with width \(\sim c^{1/3}\) | **false** (core); **partial caveat** on \(c^{1/3}\) attribution | CONFIRMED core (T2); power law PLAUSIBLE with better cite |
| R3 | Gao et al. 2018: first→last half-hour market mom; \(R^2=1.6\%\); timing ~6.67% ann gross; post-dec net still positive in sample | **false** | CONFIRMED (T2) for IS/OS-in-sample-window figures |
| R4 | Rosa 2022: post-pub / OOS kill of overnight→last-HH predictability (disappears, not gradual decay) | **false** | CONFIRMED (T2 abstract; instrument/spec nuance) |
| R5 | LPS 2019: overnight-sort 3F alpha +3.47%/mo ON / −3.02% ID; intraday-sort reverse; costs make trade unattractive; sample ~1993–2013 | **false** | CONFIRMED (T2 full text) |
| R6 | No T2/T3 documents a profitable retail/small-scale US-equity **minutes–hours** multi-name inventory book with honest continuous fills at ~$1–10k and ≤30 manual orders/day | **false** (gap stands) | CONFIRMED as gap finding (search; no counterexample) |

**Majority:** 0/6 fully refuted. Core theory and effect magnitudes locate in T2 primaries. Caveats are scope/attribution, not fabrications.

---

## R1 — GP formulas (aim + partial trade + \(a/\lambda\) + decay weights)

**Claim under test:** With quadratic \(TC(\Delta x)=\tfrac12\Delta x^\top\Lambda\Delta x\) and predictable returns \(r_{t+1}=Bf_t+u\), factors \(\Delta f=-\Phi f+\varepsilon\), optimal policy is
\[
x_t=x_{t-1}+\Lambda^{-1}A_{xx}(\mathrm{aim}_t-x_{t-1}),\quad\mathrm{aim}_t=A_{xx}^{-1}A_{xf}f_t;
\]
under Ass. A (\(\Lambda=\lambda\Sigma\)) trading rate is scalar \(a/\lambda\in(0,1)\) with
\[
a=\frac{-(\gamma(1-\rho)+\lambda\rho)+\sqrt{(\gamma(1-\rho)+\lambda\rho)^2+4\gamma\lambda(1-\rho)^2}}{2(1-\rho)},
\]
\[
x_t=\Bigl(1-\frac{a}{\lambda}\Bigr)x_{t-1}+\frac{a}{\lambda}\,\mathrm{aim}_t,
\]
and (diag \(\Phi\)) aim down-weights fast signals: \(\tilde f^k=f^k/(1+\varphi^k a/\gamma)\). Continuous-time limit: \(\bar M^{\mathrm{rate}}=a/\lambda=\tfrac12(\sqrt{\rho^2+4\gamma/\lambda}-\rho)\); patient \(\rho\approx0\Rightarrow\sqrt{\gamma/\lambda}\).

**Primary located:** Yes — T2.

**Verdict: refuted = false**

**Reason:** NBER WP 15205 (Gârleanu & Pedersen, Aug 2009; *JF* 2013) Proposition 2 states exactly (7)–(10): trade \(\Lambda^{-1}A_{xx}\) toward aim; under Ass. A scalar \(a/\lambda\) with the displayed radical formula for \(a\); \(x_t=(1-a/\lambda)x_{t-1}+(a/\lambda)\mathrm{aim}_t\). Prop. 3: aim in front of Markowitz with \(z=\gamma/(\gamma+a)\). Prop. 4: diag-\(\Phi\) factor scaling \(f^k/(1+\phi^k a/\gamma)\); relative weight of slow vs fast **increases in \(\lambda\)**. Continuous-time companion (WP Mar 2014 / *JET* 2016) Prop. 1(iv) Ass. A2: \(\bar M^{\mathrm{rate}}=a/\lambda=\tfrac12(\sqrt{\rho^2+4\gamma/\lambda}-\rho)\) and \(\bar M^{\mathrm{aim}}=\gamma^{-1}\Sigma^{-1}B(I+a/\gamma\Phi)^{-1}\). Commodity-futures multiperiod illustration and “~20% better net SR vs best static” is in the same papers (empirical section / abstract).

**Sources (T2):**
- https://www.nber.org/system/files/working_papers/w15205/w15205.pdf (read: Props 2–4, eqs 7–15)
- https://w4.stern.nyu.edu/facdir/lpederse/papers/DynamicPortfolioChoiceWithFrictions.pdf (read: Prop 1, eqs 8–14)
- Also: http://pages.stern.nyu.edu/~lpederse/papers/DynamicTrading.pdf

**Caveat (non-killing):** Empirical illustration is **commodity futures**, multiperiod days-to-years signal half-lives — not hourly equity residuals. Formulae themselves are general LQ theory, not an equity edge claim.

---

## R2 — Quadratic vs proportional bands

**Claim under test:** Quadratic costs ⇒ **always trade a little** (no discrete no-trade band). **Proportional** costs (Constantinides 1986; Davis–Norman 1990) produce a **no-trade band** whose width scales as \(\sim(\mathrm{cost})^{1/3}\) times a function of risk aversion and volatility.

**Primary located:** Yes for structural distinction; asymptotic \(c^{1/3}\) is T2 but not the Constantinides 1986 text itself.

**Verdict: refuted = false** (core distinction); **attribution caveat on \(c^{1/3}\)**

**Reason:**
1. **Quadratic ⇒ continuous partial trade (no NT band):** GP 2013/2016 optimal policy is always a positive trading intensity toward aim whenever \(x\neq\mathrm{aim}\). GP 2016 p.2–5 explicitly contrast proportional-cost models (numerical, long no-trade intervals) with quadratic costs that yield **smooth continuous trading** / finite turnover — “qualitatively different from the strategy with proportional or fixed transaction costs, which exhibits long periods of no trading.” Discrete GP never has a hard dead zone from the LQ solution itself.
2. **Proportional ⇒ no-trade region:** Constantinides (1986) *JPE* — two-asset intertemporal model with proportional TC; demand for risky asset characterized by a no-trade region (classic citation; abstract + standard restatement in GP 2016 footnote literature review). Davis–Norman (1990) more formal single-risky analysis of the wedge. Confirmed as T2 canon.
3. **Width \(\sim c^{1/3}\):** This **is** the standard small-cost asymptotic (e.g. Janeček & Shreve 2004 *Finance Stochastics*; later surveys state no-trade width order \(\varepsilon^{1/3}\), welfare loss \(\varepsilon^{2/3}\)). **However**, Constantinides 1986 itself is **not** the source of the cube-root expansion — it shows existence/comparative statics (wider zone for higher proportional costs), not the precise power. Attributing the \(^{1/3}\) law jointly to “Constantinides 1986; Davis–Norman 1990” is **loose**. Prefer cite: Janeček–Shreve (2004) or equivalent asymptotic paper.

**Sources (T2):**
- GP 2016 WP: https://w4.stern.nyu.edu/facdir/lpederse/papers/DynamicPortfolioChoiceWithFrictions.pdf (quadratic vs proportional contrast)
- Constantinides, G.M. (1986). Capital Market Equilibrium with Transaction Costs. *JPE* 94:842–862
- Davis, M.H.A. & Norman, A.R. (1990). Portfolio Selection with Transaction Costs. *Math. of OR*
- Janeček, K. & Shreve, S.E. (2004). Asymptotic analysis for optimal investment and consumption with transaction costs. *Finance and Stochastics* 8:181–206

**Non-killing design note:** Modality A’s optional retail band \(\kappa\cdot\sigma_h\) is a **practical hybrid**, not the pure GP quadratic optimum — correctly labeled “proportional-cost approximation” in the modality text.

---

## R3 — Gao, Han, Li & Zhou (2018) market intraday momentum

**Claim under test:** First half-hour return (prev close→~10:00) predicts last half-hour (15:30–16:00) on SPY 1993–2013; IS \(R^2=1.6\%\) (\(r_1\)); \(2.6\%\) with \(r_{12}\); OS \(R^2_{OS}=1.4\%/2.0\%\); sign-timing \(\eta(r_1)\): **+6.67% ann** gross, sd 6.19%, Sharpe 1.08 vs always-long last-HH −1.11% / buy-hold 6.04% Sharpe 0.29; CER (γ=5) **+6.02% ann**; post-decimalization net of bid/ask @15:30: **+4.46% ann** (after 2001); after 2005: **+6.52% net**. Units: annualized last-HH timing PnL.

**Primary located:** Yes — T2 (WP full text read; *JFE* 2018 abstract matches).

**Verdict: refuted = false**

**Reason:** WP text (SSRN 2440866 path / Super.so PDF) states:
- Sample SPY TAQ half-hours **Feb 1993–Dec 2013**
- Predictive \(R^2=1.6\%\) (\(r_1\to r_{13}\)); joint with \(r_{12}\) → \(2.6\%\)
- OS \(R^2_{OS}=1.4\%\) / \(2.0\%\) (recursive from ~1998)
- Sign timing avg return **6.67%** ann, sd **6.19%**, SR **1.08**; buy-hold **6.04%** / sd 20.57% / SR **0.29**; always-long last HH negative in their tables
- CER gains **6.02%** (γ=5)
- Table 10 transaction costs: after 2001-07-01 \(\eta(r_1)\) **4.46%** ann net of bid–ask; after 2005-01-01 **6.52%**

All load-bearing numbers in modality A C4 match the primary. Cost treatment is **bid/ask at 15:30 entry, close print exit** — not full retail adverse-selection + multi-name inventory; flag NO full retail fill model, but claim does not assert otherwise.

**Sources (T2):**
- Gao, L., Han, Y., Li, S.Z. & Zhou, G. (2018). Market Intraday Momentum. *JFE* 129:394–414. https://doi.org/10.1016/j.jfineco.2018.05.009
- WP PDF read: https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/ee7dac49-530b-4950-b5d0-e0b5eee08f2e.pdf (also SSRN 2440866)

**Caveat (non-killing):** This is **market-level** timing (breadth ≈ 1 bet/day), not a 5–33 name cross-section expander. Sample ends **2013** — post-pub equity OOS is separate (see R4).

---

## R4 — Rosa (2022) OOS kill

**Claim under test:** Rosa, *Journal of Futures Markets* 2022: post-publication / out-of-sample, the **overnight → last half-hour** predictability **disappears** (not gradual decay), on ES futures sample spanning into 2020. Supports map verdict **DECAYED** for this channel on futures; equity SPY post-2013 **DECAY-LIKELY**.

**Primary located:** Yes — T2 (abstract + bibliographic identity; full Wiley body paywalled this session but abstract is explicit and multi-indexed).

**Verdict: refuted = false**

**Reason:** Abstract (Wiley / IDEAS / vLex mirrors, consistent wording):
> “This paper studies the out-of-sample performance of the intraday momentum strategy where the **overnight return predicts the return of the last half-hour** of trading. **The predictability disappears in the out-of-sample period.** A Markov-switching model endogenously identifies two distinct regimes…”

Publication: Rosa, C. (2022). Understanding Intraday Momentum Strategies. *J. Futures Markets* **42**(12):2218–2234. DOI **10.1002/fut.22375**. Sample context in field cites: **ES futures**, ~**1997–2020**.

**Scope discipline (must keep when synthesizing):**
- Rosa’s predictor is **overnight**, not the full Gao \(r_1\) (prev close→10:00 = overnight + first RTH half-hour). Related family, not identical regression.
- Instrument is **ES futures**, not SPY cash ETF.
- “Disappears” rather than fades is the paper’s own language (regime / publication-consistent).

These nuances **do not refute** the map use: overnight→last-HH OOS kill on liquid equity-index futures is a clean T2 decay anchor; treating pure Gao-style last-HH timing as **DECAYED / DECAY-LIKELY** for M16 remains justified. Overclaiming “Rosa killed Gao’s exact SPY \(r_1\) regression on equities post-2013” would be false — modality A already hedges this.

**Sources (T2):**
- https://doi.org/10.1002/fut.22375
- https://ideas.repec.org/a/wly/jfutmk/v42y2022i12p2218-2234.html
- Abstract corroboration: vLex / ResearchGate abstract mirrors (2026-07-18)

**Not refuted by:** Li–Sakkas–Urquhart international first→last HH OOS in *other* equity markets (mixed positives) — different sample/spec; does not resurrect ES overnight OOS null.

---

## R5 — Lou–Polk–Skouras (2019) tug of war

**Claim under test:** US equities ~1993–2013: sort on past 1-month **overnight** returns → subsequent overnight 3-factor alpha **+3.47%/month** (t≈16.8), intraday alpha **−3.02%/month** (t≈−9.7). Sort on past **intraday** → intraday alpha **+2.41%/month**, overnight **−1.77%/month**. Patterns persist with long lags (up to 60 months). Momentum family earns **entirely overnight**; many other anomalies earn **entirely intraday**. Authors: **transaction costs make trading the overnight/intraday patterns much less attractive.** Mid-quote robustness halves but does not kill. For RTH-flat M16: overnight leg **OUT-OF-MISSION**.

**Primary located:** Yes — T2 full journal PDF.

**Verdict: refuted = false**

**Reason:** *Journal of Financial Economics* 134 (2019) 192–213, full text (LSE PDF) Table 1:
| Sort | Horizon | 10−1 3-Factor |
|------|---------|----------------|
| 1m overnight | subsequent overnight | **+3.47%** (t=16.83) |
| 1m overnight | subsequent intraday | **−3.02%** (t=−9.74) |
| 1m intraday | subsequent overnight | **−1.77%** (t=−7.89) |
| 1m intraday | subsequent intraday | **+2.41%** (t=7.70) |

Sample stated in table notes: **1993–2013**; exclude price <$5 and bottom NYSE size quintile. Abstract + body: overnight and intraday continuation + cross-period reversal lasting years; 14 strategies earn entirely overnight or entirely intraday. Explicit TC language (intro / body): transaction costs make actual profitability of exploiting overnight/intraday patterns **much less attractive**; mid-quote open robustness: overnight alpha ~1.88% / intraday −1.43% (still significant). Momentum profits “remarkably” all overnight (abstract + §4).

**Sources (T2):**
- Lou, D., Polk, C. & Skouras, S. (2019). A tug of war: Overnight versus intraday expected returns. *JFE* 134:192–213. https://doi.org/10.1016/j.jfineco.2019.03.011
- Full text read: https://personal.lse.ac.uk/polk/research/TugOfWar.pdf

**Caveat (non-killing):** Alphas are **%/month** on value-weight decile long–short portfolios (close-to-open / open-to-close components), **not** bps per half-hour event at retail size. Overnight premium harvesting is out of mission for M16 regardless of decay.

---

## R6 — No retail minutes–hours honest-cost book (gap claim)

**Claim under test:** No T2/T3 paper documents a **profitable** retail / small-scale (≤~$10k–few $100k) **US equity** **minutes-to-hours** multi-name (n≈5–33) **inventory book** with **honest continuous-market** half-spread+slippage accounting, **flat-by-close** discipline, and manual-order feasibility. Closest honest-cost prior art is multi-day / institutional (Avellaneda–Lee 2010 daily EOD residual MR, 5 bps/side, SR 1.44→0.9).

**Primary / counterexample search:** Targeted web + literature scan; **no qualifying counterexample found**.

**Verdict: refuted = false** (the **gap claim stands**)

**Reason:** Refuting a gap claim requires locating a T2/T3 that meets the **conjunction**:
1. US equities (or clearly transferable),
2. minutes–hours cadence (not EOD/daily hold),
3. small/retail capital scale OR explicit retail-realistic costs,
4. honest net-of-cost economics (spread/slip; not NO-COST),
5. multi-name inventory / stat-arb book (not single-name discretionary day-trade folklore),
6. preferably RTH-flat or comparable session.

What exists and **fails** the conjunction:
- **Avellaneda & Lee (2010) *QF*** — honest 5 bps/side, PCA/ETF residual MR, net SR 1.44 (1997–2007) → 0.9 (2003–2007); **daily EOD**, multi-day holds, institutional universe — **not** minutes–hours RTH-flat.
- **Do & Faff (2012)** — pairs unprofitable after 2002 once full costs; **daily** pairs, not min–hr retail book.
- **Gatev–Goetzmann–Rouwenhorst** — classic pairs; multi-day; cost sensitivity well known.
- **Bowen et al. (2010)** — 60-min pairs; TC/speed kill — **failure** evidence, not a surviving retail recipe.
- **Guijarro-Ordonez / Attention-factor 2025-class** — daily large-cap panels, institutional AUM framing.
- HF pairs / cointegration systems (e.g. 2012–13 US HF pairs papers) — claim high SR but **not** retail-scale + manual ≤30 orders/day + condition-coded fill honesty at $1–10k.
- Practitioner blogs (Carver, Portfolio123, QuantStart) — futures CTA, multi-day equity, or education; **no audited** min–hr US equity net book at our profile.
- Indian futures pairs retail papers, Taiwan day-trader aggregates — wrong market / wrong structure / aggregate losses.

**Absence is not proof of impossibility**, but under harness rules the claim is an **evidence-coverage finding**: after modality A/C/D scans + this refuter’s independent search, **no T2/T3 passes**. Default for *unsupported positive* edge claims remains kill; for *documented gap*, refuted=false until a counterexample appears.

**What would flip R6 to refuted=true:** A named T2/T3 with sample period, cost model (bps RT), n names, holding horizon minutes–hours, capital scale or ADV-fraction, and **positive net** economics that survives condition-code-aware fills.

**Sources (T2 anchors for “closest but not it”):**
- Avellaneda, M. & Lee, J.-H. (2010). Statistical Arbitrage in the US Equities Market. *Quantitative Finance* 10:761–782. https://math.nyu.edu/inmemoriam/avellaneda/AvellanedaLeeStatArb20090616.pdf
- Do & Faff (2012) *J. Financial Research*; Bowen et al. (2010) UCC WP (failure under TC/delay)

---

## Cross-cutting notes for orchestrator synthesis

1. **Theory layer (R1–R2) is solid.** GP formulae and quadratic-vs-proportional qualitative distinction are primary-confirmed. Use Janeček–Shreve (or peer asymptotic) if quoting \(c^{1/3}\) width; do not hang the power law solely on Constantinides 1986.
2. **Pattern layer (R3–R5) is solid on IS magnitudes; decay is one-sided.** Gao numbers exact; LPS numbers exact; Rosa OOS disappearance exact for **overnight→last-HH on ES**. Map labels DECAYED / OUT-OF-MISSION / DECAY-UNKNOWN for pure patterns remain supported.
3. **R6 gap is the M16-relevant prior:** machinery exists; **documented retail min–hr honest net book does not.** That is a finding, not a free pass for Stage A optimism.
4. **Do not upgrade modality “CONFIRMED” claims that were only abstract-confirmed when full text was unavailable** — here R1, R3, R5 were **full-text** confirmed; R4 abstract-level but unambiguous; R2 core full-text, power-law attribution refined.
5. **Twin independence:** This file is refute-**2**; do not merge with refute-1 until both land. CONFIRMED status for synthesis requires majority refuted=false **and** a refuter-located T1/T2 (HARNESS §5).

---

## Queries used (this refuter)

1. `Gârleanu Pedersen Dynamic Trading Predictable Returns Transaction Costs aim portfolio formula trading rate a/lambda`
2. `Gârleanu Pedersen 2016 Dynamic Portfolio Choice with Frictions quadratic proportional no-trade`
3. `Gao Han Li Zhou Market Intraday Momentum 2018 R-squared 1.6% timing Sharpe`
4. `Rosa 2022 Understanding Intraday Momentum Strategies Journal of Futures Markets out-of-sample disappears`
5. `Lou Polk Skouras Tug of War overnight intraday 3.47% alpha 2019`
6. `Janecek Shreve asymptotic no-trade region proportional transaction costs epsilon^{1/3}`
7. `retail statistical arbitrage minutes hours honest transaction costs US equity small capital peer-reviewed`
8. `Constantinides 1986 no-trade region proportional transaction costs width`
9. `Carlo Rosa Understanding Intraday Momentum Strategies ES futures sample`
10. `Avellaneda Lee 2010 statistical arbitrage 5 bps daily mean reversion`

---

## Bottom line

| Question | Answer |
|----------|--------|
| Any claim fully killed (refuted=true)? | **No** among the six |
| Strongest soft spot | R2’s \(c^{1/3}\) attribution; R4’s overnight-vs-\(r_1\) / futures-vs-SPY scope |
| Safe to treat as T2-backed for report.md | R1 formulas; R2 qualitative; R3 Gao IS/net-in-sample; R4 Rosa OOS disappearance (scoped); R5 LPS alphas; R6 gap |
| Flip condition for R6 | Publishable counterexample meeting all six conjunction filters |
