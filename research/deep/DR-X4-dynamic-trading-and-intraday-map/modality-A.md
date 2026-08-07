## DR-X4 — A academic findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence **MED**) — Academic dynamic-trading theory (Gârleanu–Pedersen 2013/2016 and descendants) supplies a **closed-form, turnover-aware partial-adjustment rule** that is directly usable as the position engine for an hourly multi-signal book (n≈5–33, RTH, flat 15:50/MOC). The known pure-pattern intraday effects (first→last half-hour market momentum; HKS half-hour TOD continuation; Lou–Polk–Skouras overnight/intraday clienteles; unconditional late-day drift) are either **post-pub weak/decayed**, **out-of-mission (overnight)**, **NO-COST-MODEL**, or already killed under continuous-fill realism by our own trials. The open cell for M16 is **not** re-running dead bar-tier ML or pure TOD patterns: it is **flow-anticipation (slow, half-life hours–days) + optional faster residual, mixed under a GP-style aim portfolio with explicit turnover/risk norms**, with deltas-only inventory and named payers (LETF rebal F(t), calendar, auction). Pure “intraday anomaly harvest” as a standalone edge is **EXHAUSTED-BY-FIELD / EXHAUSTED-BY-US**; **turnover-controlled multi-signal inventory control** is OPEN as method.
What would flip it: A Stage-A result that GP-style partial adjustment on owned hourly forecasts + LETF/calendar features delivers ≤0 net bps/plan after honest taker/auction costs on n≥250 plans across ≥150 sessions; or that no combination of owned signals has gross IC large enough that even full partial-adjustment still fails the 2× cost gate.
### Mechanism
**Who pays / why it persists (framework, not a single payer):** Gârleanu–Pedersen (GP) is a **portfolio-control theory**, not an anomaly. With quadratic market-impact costs, the optimal policy is continuous partial adjustment toward an “aim portfolio” that **aims in front of** the moving Markowitz target — overweighting slow-decaying signals relative to fast ones. Persistence of the *method* does not require a free lunch; it is the correct way to spend a turnover budget when forecasts have different half-lives. Separate known *payers* that can feed the forecast layer: (i) mechanical LETF end-of-day rebal (price-insensitive; last 30–60 min; DR-X1), (ii) index/passive MOC and calendar rebalance flow, (iii) clientele timing (institutions late day vs retail open — Lou–Polk–Skouras). Pure first→last half-hour market momentum has a weak microfoundation (infrequent rebalancing + late-informed traders; Bogousslavsky 2016) and has **failed clean post-pub OOS** on futures (Rosa 2022). Continuous-market minute-scale stat-arb at retail size collides with fill realism and our dead list (sub-15 min taker, bar-tier ML, maker capture).
**Capacity intuition:** GP trading rate falls in cost λ and rises in risk aversion γ; at $1k–$10k, market impact is near zero on mega-caps so λ is dominated by **half-spread + adverse selection**, not Kyle lambda. Capacity is **manual order count** (~10–30/day) and **turnover budget**, not AUM.
### Claims
C1 [CONFIRMED] (T2, NBER WP 15205 Aug 2009 / *JF* 2013, theory + commodity-futures illustration): **Optimal policy = partial trade toward aim portfolio.** With quadratic TC \(TC(\Delta x_t)=\tfrac12\Delta x_t^\top\Lambda\Delta x_t\) and returns \(r_{t+1}=Bf_t+u_{t+1}\), factors \(\Delta f_{t+1}=-\Phi f_t+\varepsilon_{t+1}\):
\[
x_t=x_{t-1}+\Lambda^{-1}A_{xx}(\mathrm{aim}_t-x_{t-1}),\qquad\mathrm{aim}_t=A_{xx}^{-1}A_{xf}f_t.
\]
Under Ass. A (\(\Lambda=\lambda\Sigma\)): scalar trading rate \(a/\lambda\in(0,1)\),
\[
a=\frac{-(\gamma(1-\rho)+\lambda\rho)+\sqrt{(\gamma(1-\rho)+\lambda\rho)^2+4\gamma\lambda(1-\rho)^2}}{2(1-\rho)},
\]
\[
x_t=\Bigl(1-\frac{a}{\lambda}\Bigr)x_{t-1}+\frac{a}{\lambda}\,\mathrm{aim}_t.
\]
Markowitz (no cost): \(\mathrm{Markowitz}_t=(\gamma\Sigma)^{-1}Bf_t\). Aim-in-front: \(\mathrm{aim}_t=z\,\mathrm{Markowitz}_t+(1-z)E_t[\mathrm{aim}_{t+1}]\) with \(z=\gamma/(\gamma+a)\), or \(\mathrm{aim}_t=\sum_{\tau=t}^\infty z(1-z)^{\tau-t}E_t[\mathrm{Markowitz}_\tau]\). — Gârleanu & Pedersen, *Dynamic Trading with Predictable Returns and Transaction Costs*; https://www.nber.org/system/files/working_papers/w15205/w15205.pdf

C2 [CONFIRMED] (T2, same): **Signal weighting by alpha decay (half-life).** If \(\Phi=\mathrm{diag}(\varphi^1,\ldots,\varphi^K)\),
\[
\mathrm{aim}_t=(\gamma\Sigma)^{-1}B\begin{pmatrix}f_t^1/(1+\varphi^1 a/\gamma)\\\vdots\\f_t^K/(1+\varphi^K a/\gamma)\end{pmatrix}.
\]
Persistent signals (small \(\varphi\)) are down-weighted less; relative weight of slow vs fast **increases** in transaction cost \(\lambda\). Half-life of signal \(k\): \(t_{1/2}=\ln 2/\varphi^k\) (discrete AR(1)). Empirical commodity example: 5-day signal \(\varphi\approx0.20\) (half-life ~3 days), 1-year \(\varphi\approx0.0034\) (~205 d), 5-year \(\varphi\approx0.0010\) (~700 d). — same GP 2009/2013.

C3 [CONFIRMED] (T2, *JET* 2016 / WP Mar 2014): **Continuous-time limit (hourly discretization OK).** Trading intensity \(\tau_t=dx_t/dt=\bar M^{\mathrm{rate}}(\bar M^{\mathrm{aim}}(f_t)-x_t)\). Under Ass. A2 (\(\Lambda=\lambda\Sigma\)):
\[
\bar M^{\mathrm{rate}}=\frac{a}{\lambda}=\tfrac12\bigl(\sqrt{\rho^2+4\gamma/\lambda}-\rho\bigr),\qquad
\bar M^{\mathrm{aim}}=\gamma^{-1}\Sigma^{-1}B(I+a/\gamma\,\Phi)^{-1}.
\]
Patient agent \(\rho\approx0\): rate \(\approx\sqrt{\gamma/\lambda}\). Quadratic costs → **always trade a little** (no no-trade band). **Proportional** costs (Constantinides 1986; Davis–Norman 1990) produce a **no-trade band** whose width scales as \(\sim(\mathrm{cost})^{1/3}\) times a function of risk aversion and volatility — different technology. For retail half-spread costs, either: (i) GP partial-adjust with \(\lambda\) calibrated to bps×notional, or (ii) hard no-trade band around aim of width \(k\cdot\sigma_{\mathrm{hour}}\cdot\sqrt{c}\) for proportional-cost approximation. — Gârleanu & Pedersen, *Dynamic Portfolio Choice with Frictions*; https://w4.stern.nyu.edu/facdir/lpederse/papers/DynamicPortfolioChoiceWithFrictions.pdf

C4 [CONFIRMED] (T2, *JFE* 2018, sample Feb 1993–Dec 2013, SPY half-hours; first draft Mar 2014): **First half-hour return (prev close→10:00) predicts last half-hour (15:30–16:00).** In-sample \(R^2=1.6\%\) (\(r_1\) alone); \(R^2=2.6\%\) with \(r_{12}\) (15:00–15:30). OOS \(R^2_{OS}=1.4\%\) / \(2.0\%\). Sign-timing strategy \(\eta(r_1)=\mathrm{sign}(r_1)\cdot r_{13}\): **+6.67% ann gross**, sd 6.19%, Sharpe 1.08 vs always-long last-HH −1.11% / buy-hold 6.04% Sharpe 0.29. Mean-variance CER (γ=5, |w| capped) **+6.02% ann**. Post-decimalization **net of bid/ask at 15:30** (entry at ask if long / bid if short; exit at close print): **+4.46% ann** (full sample post-2001); after 2005: **+6.52% net** (spread ~1.2 bps mid-2000s). Stronger on high-vol, high-volume, recession, FOMC-minutes days. **Units: annualized half-hour timing PnL, not bps/event.** — Gao, Han, Li & Zhou, *Market Intraday Momentum*; https://doi.org/10.1016/j.jfineco.2018.05.009 ; WP https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/ee7dac49-530b-4950-b5d0-e0b5eee08f2e.pdf

C5 [CONFIRMED] (T2, *J. Futures Markets* 2022, sample ES futures Sep 1997–Dec 2020): **Post-publication OOS of the overnight→last-half-hour link: predictability disappears.** Rosa documents that the relationship **vanishes** in the out-of-sample period (not gradual decay), consistent with regime / publication effects rather than a durable payer. — Rosa, *Understanding Intraday Momentum Strategies*; https://doi.org/10.1002/fut.22375 . **Verdict for our map: DECAYED (post-pub OOS kill on futures; equity SPY post-2013 sparse in peer review → DECAY-LIKELY).**

C6 [CONFIRMED] (T2, *JF* 2010, sample NYSE/AMEX TAQ 1986–2007-ish half-hours): **Heston–Korajczyk–Sadka (HKS) half-hour return continuation at lags that are multiples of a trading day (13, 26, …) for ≥40 trading days.** Volume, OI, vol, spreads show similar TOD periodicity but **do not explain** return continuation. Short-horizon reversal (<1 hour) is liquidity/bid-ask bounce. Timing trades can save ~1 effective spread. **NO-COST-MODEL** for trading the lag-13 cross-section as a standalone profit strategy; magnitude of hedge-portfolio returns not a clean retail bps/event. Interday CS momentum literature later finds last-half-hour strength **~75% weaker** OOS vs HKS era. — Heston, Korajczyk & Sadka; https://www.bauer.uh.edu/departments/finance/documents/Heston-Korajczyk-Sadka-jf-2010-01-07.pdf . **DECAY-UNKNOWN→DECAY-LIKELY.**

C7 [CONFIRMED] (T2, *JFE* 2019, sample US equities ~1993–2013 CRSP+TAQ open/close): **Lou–Polk–Skouras overnight vs intraday “tug of war.”** Sort on past 1-month overnight returns: overnight 3-factor alpha **+3.47%/month** (t=16.8), intraday alpha **−3.02%/month** (t=−9.7). Sort on past intraday: intraday alpha **+2.41%/month**, overnight **−1.77%/month**. Patterns persist with lags up to 60 months. Momentum family earns **entirely overnight**; most other anomalies (value, profitability, investment, …) earn **entirely intraday**, often with opposite-sign overnight. Authors explicitly: **transaction costs make trading the overnight/intraday patterns much less attractive.** Bid-ask bounce not the driver (mid-quote robustness halves but does not kill). — Lou, Polk & Skouras; https://doi.org/10.1016/j.jfineco.2019.03.011 ; https://personal.lse.ac.uk/polk/research/TugOfWar.pdf . **For M16 (RTH only, flat 15:50/MOC): overnight leg OUT-OF-MISSION. Intraday-leg anomalies = close-to-close style factors, not a free half-hour edge. DECAY-UNKNOWN at our size/horizon.**

C8 [CONFIRMED] (T2 structure, classic + Gao Fig 2): **TOD seasonality of volume/vol/spreads.** Volume and volatility **U-shaped** (open and close ~3× midday); spreads **L-shaped / declining** through the day (last 30-min half-spreads often ~0.5–1.5 bps on liquid ETFs/mega-caps post-decimalization). This is **market microstructure**, not a return premium per se. Last-30-min is where flow-driven drift (LETF rebal, MOC, institutional) concentrates — **mechanism for features**, not for pure TOD long/short. — Jain & Joh 1988; Admati–Pfleiderer 1988; Gao et al. 2018 Fig 2; Bogousslavsky–Muravyev 2023 auction share. **Not “dead”; not tradable alone.**

C9 [CONFIRMED] (T2, Barbon et al. 2021 WP + Lenkey 2024 survey; sample equity LETFs 2012–2019): **Late-day flow-driven drift from LETF rebal.** Both option γ and LETF rebal explain last-30-min returns; LETF channel **declines over sample**. Average economic impact after capital-flow adjust is **sub-bps to low-bps** on liquid large-caps (Ivanov–Lenkey 2018: ≪1 bps average). Formulaic intensity \(\Omega^{\mathrm{LETF}}_{j,t}=\sum_i L_i(L_i-1)A_{i,t-1}w_{i,j}r^{\mathrm{pre}}_{i,t}/\mathrm{ADV}^{\mathrm{end}}_j\). **NO clean net-of-cost front-run established.** — aligns with DR-X1 modality A. **Use as F(t) feature / aim-portfolio signal, not unconditional last-30 long.**

C10 [CONFIRMED gap] (T2 scan; Avellaneda–Lee 2010 is the closest honest-cost prior art): **No T2/T3 paper documents profitable minutes-to-hours retail/small-scale US equity stat-arb with condition-coded continuous fills at ~$1–10k notional and ≤30 manual orders/day.** Avellaneda–Lee (*QF* 2010): **daily EOD** PCA/ETF residual MR, entry |z|>1.25, exit |z|<0.5, **5 bps per trade / 10 bps RT**, SR~1.44 (1997–2007) → **~0.9 (2003–2007)**; ETF+volume SR 1.51 late sample. Holding is multi-day, not RTH flat. Gatev et al. pairs, Guijarro-Ordonez et al. 2025 attention factors: institutional universes, daily or multi-day, 5 bps cost models. **Minutes–hours continuous retail = gap / our dead list territory.** Say so: **none found that pass §1+honest costs.**

C11 [PLAUSIBLE] (T2, SSRN 5039009 / EFMA 2024; US stocks, recent sample — **NEW effect, not in the pre-2024 canon**): **End-of-Day Reversal (Baltussen–Da–Soebhag).** Rank all stocks by prev-close→15:30 ET return; the bottom decile *minus* top decile earns **≈+0.24%/day (≈24 bps) gross in the 15:30–16:00 window**, driven mostly by **upward price pressure on the day's intraday losers**. Explicitly **distinct from Gao market intraday momentum** (that is index-level continuation; this is cross-sectional reversal) and **not explained by liquidity- or gamma-hedging**. Proposed mechanism: **attention-induced retail buying of losers + short-seller EOD risk-management/covering** — both scheduled, partly price-insensitive close flows. Caveats: **NO-COST-MODEL** (gross decile long-short), decile concentration + two-leg cost, and the tradable slice on our 5–33 mostly-megacap universe is a fraction of the full-cross-section spread. 2nd prize, Quantpedia Awards 2025. **This is the one NEW-to-us, owned-data-testable last-30-min effect** and the natural fast-signal candidate to fold into the M16 aim portfolio. — Baltussen, Da & Soebhag; https://academicweb.nd.edu/~zda/EOD.pdf ; SSRN 5039009. **DECAY-UNKNOWN (2024, no post-pub OOS yet).**

C12 [PLAUSIBLE, tension with C5] (T3, SSRN 4824172, SPY 2007–early 2024; conflicted — Concretum sells it): **A demand/supply-imbalance variant of intraday momentum survives net-of-cost to 2024** — 19.6% annualized, Sharpe 1.33, beta≈0, net of commissions+slippage; performance concentrates in high-VIX regimes (Sharpe→3.5 at VIX>40). This **contradicts Rosa 2022's OOS-kill (C5)**: Rosa tests the *raw first-HH→last-HH sign rule on ES futures* (vanishes OOS), whereas Zarattini–Aziz–Barbon test an *imbalance/trend variant on SPY with active trailing stops* (survives). Read together: the **naive sign rule is dead (Rosa); a conditioned, dynamically-managed intraday-momentum variant may persist but is practitioner/conflicted evidence and leveraged single-index, not a cross-sectional retail edge.** — Zarattini, Aziz & Barbon; https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/ . **DECAY: NAIVE=DEAD, CONDITIONED-VARIANT=DECAY-UNKNOWN.**

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **PASS** (scheduled hourly / late-day) / **FAIL** (sub-minute MR) | GP rebalance at discrete hourly clocks or 15:30/15:50 is pre-positionable for 5–25 s manual. Continuous mid-bar chase fails. |
| 2 | Access | **PASS** | Long/short mega-caps + SPY/QQQ at retail; MOC/LOC for flat-at-close path. No colocation / maker rebate needed. |
| 3 | Session | **PASS** if flat 15:50 or MOC | Overnight LPS / multi-day Avellaneda holds = out-of-mission unless user amends. |
| 4 | Data | **PASS** | Owned 1s bars + SIP history + Databento NOII; free/≤$100 AUM for LETF F(t). No new real-time SIP required for historical Stage A. |
| 5 | Fill realism | **PASS** (auction/taker-priced plans) / **FAIL** (passive mid fills, tape-without-condition-codes) | Economics must use taker or auction single-print; maker assumptions banned. |
| 6 | Statistics | **PASS** for daily×name book; **marginal** for rare high-|F| only | n≈5–33 names × ~250 sessions/year → easy n≥250 plans. Per-event noise ~20 bps → need gross ≳4–6 bps mean to clear costs with power. |
| 7 | Protocol | **PASS** | Named payers (LETF rebal identity, calendar, optional residual) pre-statable; GP rate/half-life as a-priori hyperparameters; charges **M16 dynamic book** family (not reopening bar-tier ML / sequence / trailing-PnL regime). Holdout spent → forward / never-fit names. |

**Survivor-profile score: 3/5** (method path) / **1–2/5** (pure pattern path)
1. Single-print/auction exec — **only if exit is MOC/auction or tight late-day taker** (+1 method / 0 pure continuous)
2. Scheduled decision instant — **yes for hourly clock + 15:50** (+1)
3. Named price-insensitive payer — **yes if forecast = flow F(t)/calendar; no if forecast = pure first-HH momentum** (+1 flow / 0 pattern)
4. Historically testable ≤~$100 — **yes** (+1)
5. Expected effect ≥2× cost — **UNKNOWN a priori** for mixed book; pure Gao/HKS field prior post-pub is **weak** (0)

### Economics sketch
- **Expected gross (cited, units explicit):**
  - Gao sign-timing last HH: **~2.6 bps per trading day** equivalent (6.67%/252) **gross**; **~1.8 bps/day** net of ~1–2 bps half-spread entry post-2005 on SPY. **Rosa OOS: ~0.**
  - LPS overnight/intraday decile: **hundreds of bps/month** gross cross-section — **not capturable RTH-flat** without overnight; authors flag costs kill.
  - HKS lag-13: statistically large historically; **no clean modern net bps/event** for liquid mega-caps; OOS weakened ~75% in related interday work.
  - LETF last-30 impact (Ivanov–Lenkey / Barbon / Lenkey survey): **≪1 to low-single-digit bps** average; conditional high-|F| days larger, still contested net.
  - Avellaneda daily residual book: net Sharpe 0.9–1.5 **historical**, multi-day hold, 10 bps RT — **not our session rule**.
- **Our cost burden (manual retail, mega-cap):** round-trip taker ~**2–6 bps** (spread+slip) per name touched; auction exit ≈0 exit spread. At ~10–30 orders/day across 5–33 names, **daily cost drag is order-count × bps**, not AUM impact. Zero commission through 2026-12-31 (promo); post-promo fee stress required.
- **Net prior for M16 method:** Field pure-pattern prior ≈ **0 net**. Edge, if any, is **conditional flow + GP turnover control** so that slow F(t)/calendar signals dominate aim and fast residual does not churn. Compare: champion = **+2.5 bps/event dev / +12.5 holdout**.
- **Comparison line:** champion = **+2.5 bps/event dev / +12.5 holdout**.

### Proposed next test (only if OPEN-TESTABLE)
- **Hypothesis:** An hourly (or 30-min) discrete GP partial-adjustment book on n∈{5,12,33} liquid names, with aim portfolio = risk-normed mix of (i) slow LETF/calendar/flow-anticipation forecast \(f^{\mathrm{slow}}\) (half-life ≳1 session) and (ii) optional faster residual \(f^{\mathrm{fast}}\) (half-life 1–3 hours), **down-weighting fast by \(1/(1+\varphi^{\mathrm{fast}}a/\gamma)\)**, produces positive net bps/plan after taker/auction costs when flat by 15:50 or MOC — and beats both (a) static Markowitz full-adjust and (b) equal-weight signal blend without alpha-decay scaling.
- **Named payer:** LETF rebal + passive/calendar close flow (price-insensitive); residual MR only as secondary if it survives cost gate.
- **Data:** Owned 1s→hourly bars + SIP; free AUM/shares for F(t); Databento NOII optional as late-day conditioner. **$0 new** for Stage A.
- **Universe:** Start 5 (NVDA, TSLA, AMD, MU, GOOGL) → 12 bar universe → 28–33 M11-class; anchors SPY/QQQ/SMH.
- **Expected n & power:** ~250–500 sessions × multi-name plans; filter active |aim−x| days → n≥250 easy. Noise ~20 bps/event → design for ≥5 bps gross mean or kill.
- **A-priori thresholds (pre-register):**
  - Discrete GP: choose \(\Delta t=1\mathrm{h}\); \(\gamma\) so that Markowitz gross risk ≈ target hourly vol (e.g. 10–20 bps book sd); \(\lambda\) so trading rate \(a/\lambda\in[0.15,0.50]\) per hour (start **0.25**); \(\varphi^{\mathrm{slow}}\approx\ln2/6.5\) (half-life ~1 session), \(\varphi^{\mathrm{fast}}\approx\ln2/2\) (half-life ~2 h).
  - Risk norm: aim \(=(\gamma\Sigma_h)^{-1}B\tilde f\) with \(\tilde f_k=f_k/(1+\varphi_k a/\gamma)\); \(\Sigma_h\) = hourly residual covariance (EWMA 20–60 d).
  - Hard caps: |position| ≤ whole-share budget; max **30** orders/day; flat 15:50 or MOC.
  - Optional proportional-cost band: no trade if \(|\mathrm{aim}-x|<c\cdot\sigma_h\) with \(c\in[0.5,1.0]\).
- **Promotion:** OOS (forward M10 window or never-fit names) net ≥+2 bps/plan after 2 bps entry cost assumption, n≥250, and GP mix beats both static full-Markowitz and no-decay blend on pre-registered metric.
- **Kill:** Net ≤0 on n≥250; or GP rate/decay parameters unstable (any grid search that needs post-hoc half-lives); or pure first-HH / pure TOD signal is the only thing that “works” (reduces to dead/decaying patterns).
- **Trial family charged:** **M16 dynamic trading + flow book** (new). Does **not** reopen bar-tier ML, sequence models, trailing-PnL regime gating, or continuous LETF-window detectors.

### Design cheat-sheet (formulas + starting parameters + effects table)

#### A. Discrete hourly GP implementation (recommended for M16)
| Symbol | Meaning | Starting value |
|--------|---------|----------------|
| \(\Delta t\) | Decision clock | 1 hour (RTH 10:00…15:00; special 15:30/15:50) |
| \(x_t\) | Position vector (shares or $ notional) | carry from \(t-1\); 0 overnight |
| \(f_t\) | Forecast vector (expected excess return over next \(\Delta t\)) | z-scored; clip ±3 |
| \(B\) | Loadings (usually I if \(f\) already in return units) | I |
| \(\Sigma_h\) | Hourly return covariance | EWMA 20–60d on residual returns |
| \(\gamma\) | Absolute risk aversion | set so \(\mathrm{sd}(\mathrm{Markowitz}^\top r_h)\approx 15\) bps book |
| \(\lambda\) | Cost scalar (\(\Lambda=\lambda\Sigma\)) | imply \(a/\lambda\in[0.15,0.50]\); **start 0.25** |
| \(\rho\) | Discount per period | \(\approx0\) (patient) or \(1-e^{-r\Delta t}\) small |
| \(\varphi_k\) | Mean-reversion of signal \(k\) per hour | slow: \(\ln2/6.5\); fast: \(\ln2/2\) |
| \(a\) | From C1 formula | compute from \(\gamma,\lambda,\rho\) |
| Trade | \(x_t=(1-\theta)x_{t-1}+\theta\,\mathrm{aim}_t\), \(\theta=a/\lambda\) | whole-share round; skip if |Δx|<1 share |

**Aim construction (multi-signal):**
\[
\tilde f_t^k=\frac{f_t^k}{1+\varphi^k a/\gamma},\qquad
\mathrm{aim}_t=(\gamma\Sigma_h)^{-1}B\tilde f_t.
\]
**Forecast-to-position (Grinold single-period baseline, for comparison):**
\[
w^\star=\frac{1}{\gamma}\Sigma^{-1}\alpha,\quad\alpha=\mathrm{IC}\cdot\sigma\cdot z
\]
then apply partial adjust \(x_t=(1-\theta)x_{t-1}+\theta w^\star\) (GP nests this when \(\Phi\to0\) and single period).

**Turnover budget:** daily share turnover \(T=\sum_t\|x_t-x_{t-1}\|_1/(2\cdot\mathrm{gross\,notional})\). Target \(T\) such that \(T\times\mathrm{bps\_RT}\lesssim 0.5\times\) expected gross. Manual cap: **≤30 orders/day**.

**No-trade band (optional, proportional-cost approx):** trade only if \(|\mathrm{aim}_i-x_i|>\delta_i\) with \(\delta_i=\kappa\,\sigma_{h,i}\), \(\kappa\in[0.5,1.0]\); trade to boundary not to aim (halves turnover; Grinold–Kahn practice).

#### B. Known-effects table (decay verdicts)

| Effect | Sample (paper) | Size (units) | Cost treatment | Post-pub decay |
|--------|----------------|--------------|----------------|----------------|
| Gao first→last HH market mom | SPY 1993–2013 | \(R^2\) 1.6%; timing **~2.6 bps/day gross** (~6.7% ann); **~1.8 bps/day net** post-dec | Bid/ask @15:30; close print exit | **DECAYED naive** (Rosa 2022 ES OOS disappears); **conditioned variant survives to 2024** (Zarattini net SR 1.33, conflicted T3) |
| **End-of-Day Reversal (loser−winner 15:30–16:00)** | US stocks, recent (BDS 2024) | **+24 bps/day gross** decile L-S; pressure on losers | **NO-COST-MODEL** | **NEW / untested-by-us — OPEN-TESTABLE** (2-leg cost + concentration unproven; owned-data-testable) |
| HKS half-hour lag-13 CS mom | TAQ 1980s–2000s | Stat. large; ≥40 days | Mostly NO-COST-MODEL | **DECAY-LIKELY** (~75% weaker in later interday CS work) |
| LPS overnight continuation | US CS ~1993–2013 | **+3.47%/mo** ON alpha; **−3.02%** ID | Authors: costs make trade unattractive | **DECAY-UNKNOWN**; **OUT-OF-MISSION** (overnight) |
| LPS intraday anomaly premia | same | Premia **entirely ID** for value/profit/etc. | NO retail RT model | **DECAY-UNKNOWN** as half-hour trade; close-to-close factors |
| TOD U-shape vol/volume; L-shape spreads | classical + Gao | Open/close vol ~3× midday; last-HH half-spread ~1 bps liquid | Structural | **ALIVE** (microstructure, not alpha) |
| LETF last-30 rebal drift | 2006–2019 equity LETFs | Avg impact **≪1–low bps**; conditional higher | Front-run gross ≠ net | **WEAKENED**; use as **F(t) feature** |
| Avellaneda residual MR | US EOD 1997–2007 | Net SR 1.44→0.9; 10 bps RT | 5 bps/side explicit | **DECAYED mid-2000s**; **multi-day**, not RTH-flat |
| Bar-tier ML / sequence / regime gate | our ledger | deployable α≈0 | honest v1.4 fills | **EXHAUSTED-BY-US** |

#### C. Signal-mix recipe under turnover budget (n≈5–33)
1. Build \(f^{\mathrm{slow}}\) = signed predicted flow intensity (LETF \(F(t)\), calendar dummies, optional NOII basis at 15:55) scaled to expected hourly return units.
2. Optional \(f^{\mathrm{fast}}\) = residual MR / short momentum on 30–60 min returns (only if Stage A IC survives costs). **Concrete candidate: the End-of-Day Reversal signal (C11)** — rank names by prev-close→15:30 return, tilt toward the intraday losers for the 15:30→16:00 leg, exit at the 16:00 cross via MOC (single-print exit = clean fill). Trade the cross-sectional *spread* (demean), not the level.
3. Apply GP decay scaling (C2); slow gets higher aim weight.
4. Risk-norm at hourly \(\Sigma_h\); partial-adjust with \(\theta\approx0.25\).
5. Flatten: force aim→0 by 15:50 or convert residual to MOC.
6. Never use trailing-PnL regime gate (dead 3×); never sequence models on bars (M4/M9).

### Sources
1. **[T2]** Gârleanu, N. & Pedersen, L.H. (2009/2013). Dynamic Trading with Predictable Returns and Transaction Costs. NBER WP 15205; *Journal of Finance* 68:2309–2340. https://www.nber.org/system/files/working_papers/w15205/w15205.pdf
2. **[T2]** Gârleanu, N. & Pedersen, L.H. (2016). Dynamic Portfolio Choice with Frictions. *Journal of Economic Theory* 165:487–516. WP Mar 2014: https://w4.stern.nyu.edu/facdir/lpederse/papers/DynamicPortfolioChoiceWithFrictions.pdf
3. **[T2]** Gao, L., Han, Y., Li, S.Z. & Zhou, G. (2018). Market Intraday Momentum. *Journal of Financial Economics* 129:394–414. WP: https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/ee7dac49-530b-4950-b5d0-e0b5eee08f2e.pdf
4. **[T2]** Rosa, C. (2022). Understanding Intraday Momentum Strategies. *Journal of Futures Markets* 42:2218–2234. Sample ES 1997–2020. https://doi.org/10.1002/fut.22375
5. **[T2]** Heston, S.L., Korajczyk, R.A. & Sadka, R. (2010). Intraday Patterns in the Cross-Section of Stock Returns. *Journal of Finance* 65:1369–1407. https://www.bauer.uh.edu/departments/finance/documents/Heston-Korajczyk-Sadka-jf-2010-01-07.pdf
6. **[T2]** Lou, D., Polk, C. & Skouras, S. (2019). A Tug of War: Overnight Versus Intraday Expected Returns. *Journal of Financial Economics* 134:192–213. https://personal.lse.ac.uk/polk/research/TugOfWar.pdf
7. **[T2]** Avellaneda, M. & Lee, J.-H. (2010). Statistical Arbitrage in the US Equities Market. *Quantitative Finance* 10:761–782. https://math.nyu.edu/inmemoriam/avellaneda/AvellanedaLeeStatArb20090616.pdf
8. **[T2]** Barbon, A., Beckmeyer, H., Buraschi, A. & Moerke, M. (2021 WP). Liquidity Provision to Leveraged ETFs and Equity Options Rebalancing Flows. SSRN 3925725.
9. **[T2]** Ivanov, I.T. & Lenkey, S.L. (2018). Do Leveraged ETFs Really Amplify Late-Day Returns and Volatility? *Journal of Financial Markets* 41:36–56.
10. **[T2]** Lenkey, S.L. (2024). The Market Impact of Leveraged ETFs: A Survey. *Quantitative Finance and Economics* 8:815–840.
11. **[T2]** Constantinides, G.M. (1986). Capital Market Equilibrium with Transaction Costs. *Journal of Political Economy* 94:842–862. (no-trade region under proportional costs)
12. **[T2]** Bogousslavsky, V. (2016). Infrequent Rebalancing, Return Autocorrelation, and Seasonality. *Journal of Finance* 71:2967–3006. (theory for Gao-style ID momentum)
13. **[T2]** Grinold, R.C. & Kahn, R.N. (2000). *Active Portfolio Management*, 2nd ed. McGraw-Hill. (α = IC·σ·z; turnover/value-added frontier)
14. **[T2]** Bogousslavsky, V. & Muravyev, D. (2023). Who Trades at the Close? *Journal of Financial Markets* 66:100852.
15. **[T2]** Baltussen, G., Da, Z. & Soebhag, A. (2024). End-of-Day Reversal. SSRN 5039009; EFMA 2024. https://academicweb.nd.edu/~zda/EOD.pdf (2nd prize, Quantpedia Awards 2025)
16. **[T3, conflicted]** Zarattini, C., Aziz, A. & Barbon, A. (2024). Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY). SSRN 4824172. https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/

#### Queries used
1. `Garleanu Pedersen Dynamic Trading Predictable Returns Transaction Costs aim portfolio formula`
2. `Gao Han Li Zhou "First Half-Hour Return Predicts Last Half-Hour" post-publication out-of-sample`
3. `Lou Polk Skouras overnight returns vs intraday A New Historical Perspective`
4. `Heston Korajczyk Sadka 2010 intraday patterns momentum half-hour returns`
5. `no-trade band transaction costs optimal portfolio width volatility signal half-life formula`
6. `intraday momentum first half hour last half hour decay post publication out of sample 2014 2023`
7. `retail statistical arbitrage transaction costs minutes hours academic paper small capital`
8. `Gârleanu Pedersen 2016 Dynamic portfolio choice with frictions Journal of Economic Theory aim portfolio`
9. `Constantinides no-trade region proportional transaction costs width formula risk aversion volatility`
10. `Grinold Kahn forecast to position alpha volatility risk aversion turnover budget multi-signal`
11. `"Understanding intraday momentum strategies" out-of-sample disappears overnight last half-hour`
12. `Avellaneda Lee 2010 statistical arbitrage 5 bps transaction cost daily mean reversion residual signal formula`
13. `Gao Han Li Zhou market intraday momentum transaction costs bps last half hour table`
14. `Rosa 2022 Understanding intraday momentum strategies sample period futures ES SPX`
15. `time of day seasonality stock returns volume spreads U-shape academic Heston`
16. `Baltussen Da Soebhag "End-of-Day Reversal" liquidity provision last 30 minutes reversal returns bps mechanism`
17. `intraday momentum out-of-sample 2018-2024 decay replication SPY last half hour trading strategy live` (Zarattini–Aziz–Barbon)
18. `leveraged ETF rebalancing predictable end of day flow front-running pre-positioning Shum returns` / `"leveraged ETF" rebalancing no excess profits predictable flow price impact out-of-sample decay`
19. `Bogousslavsky infrequent rebalancing intraday cross-section end-of-day return seasonality`

_(v1.1 addendum — second research pass: added C11 End-of-Day Reversal (BDS 2024, NEW effect), C12 Zarattini vs Rosa OOS tension, EOD-Reversal table row + fast-signal recipe. All GP formulas, Rosa/HKS/LPS/Avellaneda claims, and the design cheat-sheet are retained from the v1.0 pass, which extracted the exact discrete GP trade-rate formula the second pass's PDF fetches could not render.)_
