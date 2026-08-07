## DR-X4 — Practitioner (modality C) findings: cost-aware target-position books + intraday-effects map

### Verdict recommendation
**OPEN-TESTABLE (confidence MED)** — but split the verdict by layer. The *turnover-control FRAMEWORK*
(Garleanu-Pedersen partial-adjustment / aim-portfolio + turnover-budgeted signal mixing + Carver-style buffering
and speed limits) is a mature, cheaply-implementable **execution/inventory layer**, directly buildable on owned
data at hourly cadence with the deltas-only expression M16 wants — this is the reusable part. The *intraday alphas
that layer would trade*, however, are almost all documented-and-decayed: intraday momentum is OOS-weak, LETF
end-of-day front-running has decayed to ~zero excess profit, overnight/intraday tug-of-war is out-of-mission.
No credible T2/T3 example of a **retail / small-scale US-equity minutes-hours inventory book that survives honest
continuous-market costs** was found. So M16's value is NOT a new signal — it is a better *wrapper* (turnover
budget + deltas inventory) around the champion's flow-signal family; as a standalone intraday-momentum book it is
EXHAUSTED-BY-FIELD. (Converges with the independent prior-wave modality-C on this repo.)
**What would flip it:** a named practitioner audit of a 5–33-name RTH book at minutes-hours horizon, account
≤~$100k, with published *net* bps/event after measured half-spread+slippage, n≥250 sessions — OR our own Stage-A
M16 paper showing the deltas/turnover wrapper lifts *net* per-plan PnL over the naive one-shot expression on a
signal we already believe (the auction/LETF-flow family). That is an internal M16 test, not a literature question.

### Mechanism
The framework has **no payer of its own** — it is a cost-optimal control law. It only earns if fed a signal with
a real payer. The one payer that recurs in the practitioner literature and matches our champion is **indexed /
leveraged-ETF rebalance flow**: LETFs must trade in the same direction as the day's move near the close to
re-hit their leverage ratio; that flow is price-insensitive and mechanically forecastable from the intraday
return F(t). This is the *same* mechanism as the live auction-basis edge, and the same one Barbon et al. (already
held) documents. GP's contribution is telling you, given that signal's half-life and your cost, *how far to trade
toward the target each hour* rather than snapping to it — exactly the "deltas-only inventory" question M16 poses.
Persistence of the *framework* is certain (it is arithmetic); persistence of the *flow edge* is the open question,
and the practitioner record below says it has largely decayed since 2011.

### Claims
C1 [CONFIRMED] (T2, Garleanu-Pedersen, J.Finance 2013, sample ~1996–2009, commodity futures): Optimal cost-aware
policy = **trade partially toward an "aim" portfolio that sits in front of the moving Markowitz target**; closed
form xₜ = (1 − a/λ)·xₜ₋₁ + (a/λ)·aimₜ, aimₜ a decay-weighted blend of the current and *expected future* Markowitz
targets, slower-decaying signals weighted more. Net-of-cost returns beat Markowitz-with-costs and static
benchmarks. — nber.org/papers/w15205, Wiley 10.1111/jofi.12080.
C2 [CONFIRMED] (T3, FactSet, Nov 2024): For a signal with first-order autocorrelation ρ and gross leverage L,
**turnover ≈ L·(1−ρ)/(1+ρ)**; blending fast+slow signals to a target turnover reduces to controlling the
*aggregate* signal's ρ. Worked example: SLOW ρ=94.2%→30.6% turnover; INTERMEDIATE ρ=64.0%→85.1%; FAST
ρ=12.8%→128.9%. — insight.factset.com/navigating-portfolio-turnover-with-autocorrelation-insights.
C3 [CONFIRMED] (T3, R. Carver, "Systematic Trading"/qoppac): two operational rules practitioners actually use —
(a) **speed limit**: size trading so expected costs consume no more than ~1/3 of pre-cost Sharpe (roughly a cap
of ~0.13 SR-units of annual cost), reject any faster signal; (b) **position buffering / inertia band**: don't
trade until the target moves beyond a no-trade zone ~10% of the average position, then trade only to the band
edge — the discrete-implementation analogue of GP's no-trade region. NBIM/large-fund practice uses the same idea
as **corridor bands** around target weights. — qoppac.blogspot.com; corroborated by prior-wave modality-C.
C4 [CONFIRMED] (T3, FactSet, Apr 2026): Standard signal-combination weights in practice = Equal-Weight,
Risk-Parity (by signal vol), or Max-IR (mean-variance on signal ICs); pick under a turnover constraint, favoring
slower signals when the cap binds. — insight.factset.com/a-practical-approach-to-weighting-signals.
C5 [CONFIRMED] (T2, Gao-Han-Li-Zhou "Market Intraday Momentum," JFE 2018, SPY 1993–2013): first-half-hour return
predicts last-half-hour; best OOS R²=1.8% (1st+12th half-hour), stronger on high-vol/high-volume/news days.
**Gross**, no full cost gate in headline. — ssrn 2440866.
C6 [PLAUSIBLE→DECAY] (T2/T3): replications report the intraday-momentum predictability **weakens/disappears
out-of-sample** and is better explained by hedging demand than a standalone tradable; McLean-Pontiff baseline
~58% post-publication decay for anomalies generally. — academicweb.nd.edu/~zda/intramom.pdf; McLean-Pontiff 2016.
C7 [CONFIRMED→DECAY] (T3, CXO/Shum et al.): LETF end-of-day front-run (buy SSO/SDS at 2:45pm on ≥2% moves, sell
at close) made **0.60%/trade, 104% cumulative gross, Jun 2006–Jul 2011, profits concentrated in late-2008**.
Later predictable-flow work finds **larger/more-predictable flows have SMALLER price impact and no excess
front-running profit** — the edge decayed. — cxoadvisory.com; ScienceDirect S0378426621002363.
C8 [CONFIRMED] (T2, Lou-Polk-Skouras "A Tug of War," JFE 2019, ~1993–2013): strategy profits accrue *either*
entirely overnight *or* entirely intraday, usually opposite signs (momentum overnight, reversal intraday,
institutional-vs-retail clienteles). Overnight leg is **out-of-mission**; intraday leg is a reversal, not
momentum, and not shown net-of-cost. — personal.lse.ac.uk/polk/research/TugOfWar.pdf.
C9 [CONFIRMED] (T2): Intraday **U-shape** — spread highest at open, falls to a midday floor, widens into the
close; volume/volatility high at open and close. A close-oriented book pays the *wide* end — the cost model must
be time-of-day-specific, not flat bps. — SSRN 4792199; utexas Hinich NYSE study.
C10 [CONFIRMED] (T3, Ernie Chan): a book-example intraday MR strategy showed Sharpe 4.8 gross → 3.5 after 10bps
round-trip; Chan's caveat: "very difficult to get [live] Sharpe 3 over 3 years unless one is an HFT"; an
independent retail implementation dropped to Sharpe **0.4** after 1.7pt/side + 10s slippage. Direct testimony
that retail minutes-cadence stat-arb rarely survives honest costs. — epchan.blogspot.com.
C11 [CONFIRMED] (T3, Qian "Information Horizon, Portfolio Turnover, and Optimal Alpha Models," JPM 2007): signal
**half-life** governs optimal turnover — fast signals (1-month reversal) force high turnover and are
cost-fragile; long-horizon signals decay slowly and are cheap to hold. Half-life h = ln2/(mean-reversion rate);
for AR(1) with per-step autocorr ρ, **h = ln(0.5)/ln(ρ)** steps. — JPM_FA_07_Qian.pdf.

### Constraint gates (FRAMEWORK applied at hourly, 5–33 names, deltas-only)
| Gate | Verdict | Clause |
|---|---|---|
| 1 Latency | PASS | hourly/scheduled rebalance; 5–25s manual keying immaterial at this cadence |
| 2 Access | PASS | whole-share deltas via retail broker; ~10–30 small orders/day feasible manually |
| 3 Session | PASS | RTH; close leg via MOC/LOC or flat by 15:50 — no overnight if the C8 overnight leg is excluded |
| 4 Data | PASS | owned bars/ticks + held NOII/LETF flow; framework itself needs no new purchase ($0) |
| 5 Fill realism | PARTIAL | continuous-market hourly deltas incur spread/impact each rebalance — must use C9 time-of-day cost U, not flat bps; auction/MOC legs are clean |
| 6 Statistics | PASS-CONDITIONAL | per-plan not per-event; n≥150 sessions reachable, but this tests a *wrapper* → power is vs. the baseline-expression PnL, not vs 0 |
| 7 Protocol | PASS | pre-registrable (turnover budget, trade-rate a/λ, buffer width, kill = net ≤ naive expression); charges the M16 dynamic-trading family |

**Survivor-profile score: 2/5 standalone intraday book; up to 4/5 as a wrapper on the champion's flow signal.**
(1) single-print exec: NO for hourly deltas / YES only for the MOC close leg → 0.5; (2) scheduled instant: YES
(hourly clock) → 1; (3) named price-insensitive payer: only if fed the LETF/index-flow signal → 0.5 (0 as pure
momentum); (4) testable on owned/≤$100 data → 1; (5) effect ≥2× cost: UNPROVEN — the whole open question; the
literature says the tradable intraday alphas have decayed below cost → 0.

### Economics sketch
The framework carries **no standalone gross** — it re-expresses an existing signal. The intraday alphas it could
trade, net-of-cost and post-decay: intraday momentum OOS R²≈1.8% gross → ~0 after realistic close-side spread
(C5/C6/C9); LETF front-run 0.60%/trade in 2006–11 → ~0 excess today (C7); retail MR ~Sharpe 0.4 after honest
costs (C10). Our cost burden for hourly deltas on 5–33 names at $10k notional: each rebalance pays ~half-spread +
impact, ~1–3 bps/side on megacaps but *time-varying* (C9 close-U is the expensive window). Net prior for a *new*
standalone intraday book from this literature: **≈ 0 to slightly negative** — does not clear the champion.
Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout.** The framework only earns its keep if it lifts
the champion-family's *net* per-plan number by smoothing entries/exits under a turnover cap — the sole reason to
build M16, and an internal test, not a literature bet.

### Proposed next test (framework-as-wrapper only)
- **Hypothesis:** expressing the flow/auction signal as a GP partial-adjustment deltas book (trade fraction a/λ of
  the gap each hour, with a ~10%-of-average-position no-trade buffer, C3) yields *net* per-plan PnL ≥ the naive
  one-shot expression, at equal or lower turnover.
- **Named payer:** LETF/indexed EOD rebalance flow (same as champion); the wrapper adds no payer.
- **Data:** owned (1s event bars + held NOII/LETF flow F(t)); **$0 new**.
- **Universe:** 5 core + up to 33 M11 names, hourly grid, RTH, close leg MOC.
- **Expected n & power:** per-*plan* over ≥150 sessions; paired session-level comparison vs. baseline-expression
  distribution — the ~20 bps/event single-event sd is not the relevant noise here.
- **A-priori thresholds:** trade-rate a/λ, buffer width, and turnover budget set from measured signal half-life
  (C11) and the C9 time-of-day cost U *before* seeing results; turnover fixed via C2 (target aggregate ρ).
- **Promotion rule:** paired net-PnL uplift > 0 at equal-or-lower turnover, robust ex-top-session (guard the
  tail-concentration trap that turned engineV5's +10.3 into −1.5).
- **Kill criteria:** net ≤ naive expression, OR uplift vanishes once the C9 time-varying cost model replaces flat bps.
- **Trial family:** M16 dynamic-trading / turnover-controlled family (new).

---

### Design cheat-sheet — hourly 5–33-name cost-aware book

**1. Garleanu-Pedersen control law (spine of M16)**
- Partial-adjustment: `x_t = (1 − a/λ)·x_{t−1} + (a/λ)·aim_t` — hold most of yesterday's book, close only fraction
  `trade_rate = a/λ ∈ (0,1)` of the gap to `aim_t` each period.
- Aim portfolio: `aim_t = Σ_i z_i · E[Markowitz_target_{t+i}]` — decay-weighted blend of current and expected
  future targets; **slower-mean-reverting signals get MORE weight** (you can afford to aim where they'll still be).
  Practical rule: down-weight fast (high mean-reversion φ) predictors in the aim.
- Trading-rate scalar `a`: solves a scalar Riccati/quadratic in (γ risk-aversion, λ per-trade quadratic cost, ρ
  target mean-reversion). **Qualitative and sufficient to parameterize:** `a/λ` ↑ when cost λ↓, risk-aversion γ↑,
  or signal faster; `a/λ` ↓ (wider inertia) when cost↑ or signal slower. *(Exact closed form for `a` is UNVERIFIED
  here — the NBER/Wiley PDFs would not text-extract; pull Prop. 1 from the published paper before hard-coding the
  scalar. The structural law C1 and the calibration constants below ARE confirmed.)*
- GP calibration constants (daily commodity futures) as a starting reference: `ρ = 1−exp(−0.02/260)` (~2%/yr
  decay), `λ = 1e−6`, `γ = 1e−9`. Rescale γ,λ to $10k-notional, hourly units.

**2. Turnover budget + no-trade buffer (C2, C3)**
- `turnover ≈ L·(1−ρ)/(1+ρ)`, L = gross leverage, ρ = autocorr of the *aggregate* signal. Invert to hit a manual
  keying cap: pick target aggregate ρ, then set blend weights so the combined signal has that ρ.
- **Buffer / inertia band (Carver):** no-trade zone ~10% of average position; trade only to the band edge — the
  discrete analogue of GP's no-trade region; kills churn from small signal wiggles (the main manual-keying saver).
- **Speed limit (Carver):** size so expected costs ≤ ~1/3 of pre-cost Sharpe; if a signal can't clear that at our
  spread, don't trade it.
- Half-life ↔ autocorr (C11): `half_life = ln(0.5)/ln(ρ)` periods; measure ρ empirically (AR(1) fit), don't assume.

**3. Signal mixing at n≈5–33 (C4)**
- Combine Equal-Weight → Risk-Parity (∝1/signal-vol) → Max-IR (mean-var on signal ICs), increasing sophistication;
  at n≈5–33 keep Risk-Parity or *shrunk* Max-IR (Max-IR overfits at tiny cross-section).
- Normalize each signal to unit ex-ante vol (rolling z-score) BEFORE combining so the turnover formula's ρ is
  well-defined. Risk-normalize target notionals by rolling hourly realized vol per name (equal risk contribution);
  cap per-name at whole-share granularity for the $1k live account.

**4. Cost model — do NOT use flat bps (C9)**
- Spread/impact follows the intraday U: widest at open and into the close. A close-oriented deltas book pays the
  expensive end. Use a time-of-day cost curve; route the final adjustment through MOC/LOC (single print) rather
  than sweeping the widening close spread.

### Known-intraday-effects table with decay verdicts
| Effect | Source / sample | Size (unit, gross/net) | Cost treatment | Decay verdict |
|---|---|---|---|---|
| Intraday momentum (1st→last ½hr) | Gao-Han-Li-Zhou, JFE 2018; SPY 1993–2013 | OOS R² 1.8% (gross) | NO-COST-MODEL in headline | **DECAY-CONFIRMED (partial)** — OOS weakens; reads as hedging-demand, not standalone tradable (C6) |
| Intraday time-series momentum (global) | global replications ~2021 | mixed, market-dependent | partial | DECAY / regime-dependent |
| LETF end-of-day rebalance front-run | Shum/CXO; SSO-SDS 2006–2011 | 0.60%/trade, 104% cum (gross) | gross; conc. 2008 | **DECAY-CONFIRMED** — recent flow work: bigger flows→smaller impact, ~no excess profit (C7) |
| Pre-positioning ahead of known EOD flow | predictable leveraged-product flow lit. | ~0 excess today | modeled | **DECAY-CONFIRMED** — corroborates held Barbon; no free front-run |
| Overnight vs intraday tug-of-war | Lou-Polk-Skouras, JFE 2019; 1993–2013 | opposite-sign legs | not net-of-cost | LIVE but **overnight leg OUT-OF-MISSION**; intraday leg = reversal, unproven net |
| Intraday U-shape (spread/vol/volume) | multiple; NYSE/Nasdaq | robust structural | descriptive | **NOT-DECAYED (structural)** — use as cost model, not alpha |
| Retail minutes-hours stat-arb, honest cost | Chan + independent retail impl. | Sharpe 4.8→3.5 (10bps) but live ~0.4 | explicit | **No credible surviving retail example found** — practitioner consensus: rarely clears live cost |

### Sources
1. [T2] Garleanu & Pedersen, "Dynamic Trading with Predictable Returns and Transaction Costs," J. Finance 2013 — nber.org/papers/w15205 ; wiley 10.1111/jofi.12080 (formulas via verified search summaries; PDFs did not text-extract).
2. [T3] FactSet, "Navigating Portfolio Turnover with Autocorrelation Insights," Nov 2024.
3. [T3] FactSet, "A Practical Approach to Weighting Signals," Apr 2026.
4. [T3] R. Carver, "Systematic Trading" / qoppac.blogspot.com (buffering, speed limit); corroborated by prior-wave modality-C (NBIM corridor bands).
5. [T2] Gao, Han, Li, Zhou, "Market Intraday Momentum," JFE 2018 (SSRN 2440866); "First Half-Hour Predicts the Last" (SSRN 2552752).
6. [T3] Da/Zhang, "Hedging demand and market intraday momentum" — academicweb.nd.edu/~zda/intramom.pdf.
7. [T3] CXO Advisory, "Front-running Leveraged ETFs at the End of the Day?" (Shum et al., 2006–2011).
8. [T2] "The market impact of predictable flows: Evidence from leveraged VIX products," JBF — S0378426621002363.
9. [T2] Lou, Polk, Skouras, "A Tug of War: Overnight Versus Intraday Expected Returns," JFE 2019.
10. [T2] Hua/Kong/Wang, "Intraday Dynamics of NASDAQ Stocks… U-Shape," SSRN 4792199; Hinich NYSE intraday spread study.
11. [T3] Ernie Chan, epchan.blogspot.com ("enduring profitability of mean-reversion"; "Beware of Low Frequency Data").
12. [T3] Qian, "Information Horizon, Portfolio Turnover, and Optimal Alpha Models," JPM 2007.
13. [T3] McLean & Pontiff, "Does Academic Research Destroy Stock Return Predictability?" 2016 (~58% post-pub decay).

#### Queries used
- Garleanu Pedersen dynamic trading aim portfolio implementation practitioner turnover
- no-trade band optimal rebalancing transaction cost signal half-life quant blog
- combining alpha signals turnover budget forecast to position sizing practitioner
- Gao Han Li Zhou intraday momentum first half hour last half hour out-of-sample decay
- retail stat arb minutes hours cadence cost accounting realistic profitability
- Garleanu Pedersen "aim portfolio" trading rate formula implementation python blog example
- retail algorithmic trading intraday mean reversion transaction costs honest backtest small account fails
- Ernie Chan intraday mean reversion strategy realistic transaction costs Sharpe retail after costs
- leveraged ETF end of day rebalance front-running pre-positioning last 30 minutes predictable flow strategy
- signal half-life measurement autocorrelation decay practitioner alpha horizon Grinold Kahn information horizon
- intraday U-shape volume spread time of day seasonality open close bid-ask practitioner
- Lou Polk Skouras overnight intraday return decomposition tug of war momentum reversal
- market intraday momentum replication 2020 2023 out-of-sample decay declining profitability post-publication
