## DR-X4 — D adversarial findings

### Verdict recommendation
**NOT-VIABLE-STRUCTURAL** (confidence **HIGH**) — Hourly (or minutes–hours) statistical arbitrage on a 5–33 name retail book fails under §1 on independent structural axes that no amount of GP-style no-trade-band polish, deltas-only inventory expression, or modest retail cost improvement can repair: (i) **breadth math** — with realistic IC of the class already measured here (rank-IC +0.03–0.05, plan alpha ≈ 0) and effective independent names ≪ 5–33 because megacap/sector residual correlation is high, ex-ante IR before costs is << 0.2; (ii) **every documented intraday effect is crowded or decayed** (McLean–Pontiff-class post-publication arbitrage; Avellaneda–Lee Sharpe decay; Do–Faff post-2002 pairs wipeout; Gao et al. first→last half-hour is a published, capacity-hungry market-timing signal); (iii) **netting saves less than the M16 design intuition assumes** — correlated signals on a concentrated book produce correlated deltas, so turnover budget is not a free lunch; (iv) **manual 5–25 s keying of 10–30 orders/day** re-introduces the exact latency/execution gap that kills high-frequency pairs economics in Bowen et al.; (v) **field and retail failure corpus** is one-sided (day-trader loss rates, pairs-after-costs nulls, quant crowding unwind). Deltas-only inventory + flow features + better costs are NEW relative to our dead list, but they are *expression/cost* upgrades on a signal class whose *information* and *breadth* are already below the cost floor. They do not create a named price-insensitive payer.

What would flip it: A sealed measurement on owned data showing **independent** residual IC ≥ 0.15 at the hourly horizon on the live 5-name (or 28-name M11) book **after** residualizing shared factor/LETF flow, with Neff ≥ 8 independent bets/day and net edge ≥ 2× measured round-trip cost at our clip size — simultaneously. Absent that, the structure is dead under §1. (A named auction/flow payer expressed as inventory is a different thesis; this kill is for the *stat-arb / documented-intraday-effects book*.)

### Mechanism
**No coherent incremental payer for a continuous hourly book of known intraday patterns.** Documented effects (intraday momentum, residual mean-reversion, TOD seasonality, overnight/intraday decomposition) are either (a) market-level timing (Gao et al.) with no single-name cross-section to expand breadth, or (b) residual mean-reversion/pairs that have been industrially harvested since the 1990s and show explicit post-2002 / post-publication decay. The "payer" in residual MR is other market participants' temporary supply/demand imbalance — a pool that HFT, prop desks, and multi-strat quant books compete for at sub-second to minute horizons. At our profile (manual, RTH, flat 15:50, n≈5–33, $1k–$10k), we sit at the back of that queue: we neither provide liquidity at the inside (maker already killed under honest fills) nor react inside the signal half-life (Bowen one-period wait eliminates HF pairs excess returns).

Gârleanu–Pedersen (GP) formalizes optimal trading under costs as: (1) construct an **aim** portfolio that is a weighted average of the current Markowitz target and expected future Markowitz targets (aim *in front of* the moving target — slower-decaying signals get more weight); (2) trade **partially** toward the aim at a trading rate that falls in cost λ and rises in risk aversion. That math is correct for *institutional* quadratic impact. At our size the cost structure is **linear half-spread + slip + SEC/TAF**, not Kyle-λ impact; the continuous-rebalancing idealization does not match 10–30 manual tickets/day; and the GP result that **fast alpha-decay signals should be deweighted in the aim** is a direct indictment of hourly bar features — exactly the horizon where our measured IC already failed to produce plan economics. No-trade bands reduce turnover but cannot manufacture IR from insufficient IC×√BR.

Capacity intuition: even if a residual edge of a few bps existed, it is already the residue after industrial harvest. Small size does not *create* edge in a crowded residual; it only avoids impact. Impact was never our binding constraint — **information × breadth × transfer** is.

### Claims
C1 [CONFIRMED] (T2/T3 textbook, Grinold 1989 / Grinold–Kahn *Active Portfolio Management*; Clarke–de Silva–Thorley FAJ 2002): Fundamental law **IR ≈ IC × √BR**; with constraints **IR ≈ TC × IC × √BR**, TC typically **0.3–0.8** in practice. Breadth counts **independent** bets, not names on a blotter. — https://people.duke.edu/~charvey/Teaching/BA491_2005/Transfer_coefficient.pdf ; AnalystPrep / CFI summaries of the law

C2 [CONFIRMED] (T2 project-equivalent + field, enginev5.1 AGENT_BRIEF dead list; rank-IC class): Our own bar-tier ML (30m–4h) produced **rank-IC +0.03–0.05 REAL** with **deployable plan alpha ≈ 0** (A1 re-test failed 3 registered variants). Sequences and trailing-PnL gates also dead. This is the realistic IC prior for any "hourly forecast book" built from bars/event features on our universe — not a 0.10–0.20 IC fantasy. — AGENT_BRIEF §4

C3 [CONFIRMED] (T2 structural math from C1+C2): At IC=0.05 and N=5 **independent** names, √BR_names = √5 ≈ 2.24 → raw IR scale ≈ 0.11 **before** frequency, TC, and costs. With realistic pairwise residual correlation ρ≈0.4–0.6 among tech megacaps, effective N_eff = N/(1+(N−1)ρ) collapses toward **~1.5–2.5**, so √N_eff ≈ 1.2–1.6 and IR scale ≈ **0.06–0.08**. Expanding to N=33 with still-elevated residual correlation (same session factors, same LETF flow, same beta) does not restore industrial breadth; independent bets remain O(1)–O(few) per rebalance. Multiplying by hourly rebalances does **not** multiply breadth linearly when successive signals are autocorrelated (same slow factor). — standard GRINOLD independent-bet definition; Hentschel-type N_eff under average signal correlation ρ

C4 [CONFIRMED] (T2, Bowen/Hutchinson/O'Sullivan 2010, sample FTSE100 2007, 60-min pairs): High-frequency equity pairs excess returns are extremely sensitive to TC and execution speed — **15 bps of TC cut excess returns by more than 50%** (e.g. ~15.2%→7.0% ann. under a j=3 trigger); **a one-period wait before execution eliminates the strategy's excess returns**. Our manual 5–25 s reaction plus multi-name sequential keying is a strict super-set of "wait one interval" relative to the signal half-life of residual MR. — https://www.ucc.ie/en/media/research/centreforinvestmentresearch/wp/wp1004high-frequency-equity-pairs-trading.pdf

C5 [CONFIRMED] (T2, Do & Faff J. Fin. Research 2012, US equities 1963–2009): After commissions, market impact, and short fees, classical pairs trading is **largely unprofitable after 2002**; full-sample net is modest (~30 bps/month only for refined industry pairs) and the post-2002 window is the relevant prior for any 2020s retail implementation. On average, pairs excess drops from ~93 bps/month gross-style to ~12 bps once costs enter. — https://onlinelibrary.wiley.com/doi/10.1111/j.1475-6803.2012.01317.x

C6 [CONFIRMED] (T2, Avellaneda & Lee *Quantitative Finance* 2010, US equities ~1997–2007, daily signals, costs included): PCA residual mean-reversion stat-arb achieved average Sharpe **1.44** over 1997–2007 **but only 0.9 during 2003–2007** — explicit within-sample degradation as the strategy became known/crowded; ETF-based strategies similarly degraded after 2002. Paper itself studies the Aug 2007 liquidity crisis in the same framework as Khandani–Lo. Industrial residual MR was already decaying **before** the 2010s retail-API era. — abstract + body via Quantitative Finance 10(7)

C7 [CONFIRMED] (T2, McLean & Pontiff JF 2016, 97 published characteristics): Average post-publication decay of anomaly returns ≈ **32–35%** (arbitrage + bias), with higher volume, short interest, and cross-characteristic correlation after publication — the statistical signature of **crowding**. Documented intraday effects (Gao et al. 2018 JFE market intraday momentum; Heston–Korajczyk–Sadka intraday patterns; textbook residual MR) are more public and more automatable than most monthly characteristics → if anything *more* exposed to this channel. DECAY-UNKNOWN on post-2018 pure OOS for some effects, but direction of prior is one-sided. — https://www.fmg.ac.uk/sites/default/files/2020-08/Jeffrey-Pontiff.pdf

C8 [CONFIRMED] (T2, Gao/Han/Li/Zhou JFE 2018, SPY/ETFs 1993–2013): First half-hour return predicts last half-hour return (IS R² ~1.6%, OOS R² ~1.2%; market-timing Sharpe claims look large **gross**). This is a **market-level** signal (breadth ≈ 1 time-series bet/day), not a cross-sectional expander for a 5–33 name book. Implementing it as "tilt the whole book last-30-min" collides with our flat-by-15:50 (or MOC) session rule and with every other desk that read the same paper. NO-COST-MODEL for retail multi-name expression; DECAY-UNKNOWN post-2013 at full economic strength but publication + capacity → crowded prior. — https://ideas.repec.org/a/eee/jfinec/v129y2018i2p394-414.html

C9 [CONFIRMED] (T2, Gârleanu & Pedersen JF 2013): Optimal policy under trading costs = trade partially toward an **aim** that overweights **slow** mean-reversion (persistent) signals and deweights **fast** alpha-decay signals. Empirical illustration uses 5-day / 1-year / 5-year commodity signals (half-lives days–years), not hourly equity residuals. Quadratic cost Λ is institutional impact. **Implication for M16:** an hourly bar/feature book is exactly the fast-decay object GP says not to chase aggressively; no-trade bands help only if the aim itself has positive net value — which C2–C3 deny. — http://pages.stern.nyu.edu/~lpederse/papers/DynamicTrading.pdf (JoF 2013)

C10 [CONFIRMED] (T2, Barber/Lee/Liu/Odean line, Taiwan complete account data 1992–2006; Barber–Odean US active-trader underperformance): Aggregate day-trader performance is **negative**; vast majority unprofitable; heavy day traders earn gross profits that **do not cover costs**; <~1% predictably profitable net of fees in related work. Barber et al. (learning paper): day traders lose ~7 bps **before** costs on average; costs more than triple the losses. This is the population prior for "manual high-turnover equity speculation," of which a 10–30 order/day inventory book is a member even if signals are "systematic." — https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/Day%20Trading%20and%20Learning%20110217.pdf ; earlier Taiwan day-trader papers

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **FAIL** | Hourly residual/MR signals have short half-lives; Bowen shows one-period delay kills HF pairs. Manual 5–25 s × multi-name sequential tickets is structural lag vs co-located residual harvesters. Scheduled decision does **not** exist for continuous inventory (unlike 15:55:10 NOII). |
| 2 | Access | **PASS (marginal)** | Long/short megacaps at $1k–$10k whole shares is possible; short locate/ETB constraints remain. Not the binding kill. |
| 3 | Session | **PASS** | Can force flat by 15:50 or MOC — but forced flat truncates the very last-half-hour effects (Gao) that papers use for economic value. |
| 4 | Data | **PASS** | Owned SIP bars/ticks + anchors suffice to **kill** the thesis; no expensive data required to show IR×cost failure. |
| 5 | Fill realism | **FAIL** | Continuous-market multi-name inventory requires repeated taker (or gamed maker) fills; our own M3 maker path was phantom under condition codes. Cost stack per rebalance multiplies with turnover; netting only helps if deltas cancel (they mostly don't — see Mechanism). |
| 6 | Statistics | **FAIL as economics; PASS as autopsy** | n of hourly events is large, but expected **mean after costs ≈ 0 or negative** given IC×√N_eff. Power to detect a true +2 bps net is hopeless against ~tens of bps path noise without industrial breadth. |
| 7 | Protocol | **FAIL** | No new named price-insensitive payer. "Apply GP + no-trade bands to known TOD/MR/momentum features" is a re-skin of exhausted bar-tier / payer-detector families. Charges multiple-testing budget for a structure the field already stress-tested. |

**Survivor-profile score: 1/5**
1. Single-print/auction execution — **0** (continuous multi-fill inventory)
2. Scheduled decision instant — **0** (hourly reactive book; flat-15:50 is a constraint not a decision edge)
3. Named price-insensitive payer — **0** (residual MR / published patterns = competed pool)
4. Historically testable on owned/≤$100 data — **1**
5. Expected effect ≥ 2× cost burden at our size — **0** (IC×√N_eff too small; costs linear in un-netted turnover)

### Economics sketch
**Breadth ceiling (order-of-magnitude, per rebalance):**
- IC_real ≈ 0.03–0.05 (our bar-tier measurement; field residual MR often similar order after costs)
- N_eff ≈ 1.5–4 for a 5–33 name, factor-correlated book → √N_eff ≈ 1.2–2.0
- TC_manual+constraints ≈ 0.3–0.5 (Clarke range, low end: whole-share, sequential keying, flat deadline, risk caps)
- **IR_ex_ante ≈ TC × IC × √N_eff ≈ 0.3×0.05×1.6 ≈ 0.024** (per independent decision unit) — *before* TC drag from trading costs in the return stream
- Annualizing by counting quasi-independent hourly bets is double-counting when signals are persistent factors; honest annual IR remains << 0.5 even before costs

**Cost burden at our structure (conservative, aligned with project kernel):**
- Round-trip taker on liquid Nasdaq megacap: half-spread ~0.5–1.5 bps/side historically at mid-day; project 15:55 entry-shortfall median **1.46 bps** vs half-spread 0.73 bps; +0.5–1 bp slip; SEC/TAF ~0.3 bp sell
- Per name round-trip ≈ **2–4 bps** of traded notional under honest fills
- At 10–30 orders/day on a $10k book, if average order is ~$1–3k and many are one-way deltas: daily cost drag **~2–15 bps of equity** is easy to reach when netting fails
- GP no-trade bands cut turnover by factor κ < 1, but also cut captured gross α by a related factor — they do not raise IR above the information bound

**Netting critique (why "deltas-only inventory" under-delivers):**
- Suppose two signals S1, S2 on the same name with corr(S1,S2)=ρ_s. Position target w ∝ S1+S2. Turnover from signal noise scales with var(ΔS1+ΔS2) = varΔS1 + varΔS2 + 2cov — **netting benefit appears only when signals push opposite ways**. On a 5-name tech book, LETF flow, intraday momentum, and residual stretch **co-move on high-vol days** → same-direction deltas → turnover adds, not cancels.
- Cross-sectionally, if all names load on a common residual factor, the "book" is one bet with 5 tickets of cost.

**Published failure anchors:**
- Bowen: +15 bp TC → >50% return cut; 1-period delay → returns eliminated
- Do–Faff: pairs ~unprofitable after 2002 net of costs
- Avellaneda–Lee: Sharpe 1.44 → 0.9 as crowding rose
- Barber line: day traders lose money net; costs dominate gross

**Net prior for M16-style hourly 5–33 name book using documented effects:** **0 to negative** after honest costs; noise still large → worse than idle cash and strictly dominated by the champion auction structure.

**Comparison line: champion = +2.5 bps/event dev / +12.5 holdout.**

### Proposed next test (only if OPEN-TESTABLE)
*Not proposed as a promotion path — structure is NOT-VIABLE-STRUCTURAL for the hourly documented-effects book.*

Optional cheap **autopsy only** (does not open a trial family; does not charge M16):
1. On owned 12-name (or 5-core) 1s/bar history, compute rolling hourly residual IC of candidate features (after market/sector residualization) and estimate N_eff from residual correlation matrix. Kill confirmation if median |IC| < 0.08 **or** N_eff < 4.
2. Simulate a GP-style partial-adjustment book with no-trade band width ∈ {0.5, 1, 2}× cost and report **net** bps/day under the audited fill kernel. Kill if net ≤ 0 over ≥150 sessions.
3. Explicitly measure signal-pair correlations and fraction of delta volume that is same-direction (anti-netting). Report; do not promote.

If autopsy somehow clears both IC and N_eff bars **and** a **named** flow payer (not residual MR folklore) is attached, re-open under a new mechanism label — that would be a different DR, not a revival of bar-tier.

### Design cheat-sheet (GP formulas + starting parameters for an hourly 5–33 name book)
*Provided as the M16 method spec / autopsy engine — NOT an endorsement; the adversarial verdict above says this engine has nothing profitable to drive on the documented-effects signal set.*

**Gârleanu–Pedersen core (linear-quadratic, verified against JF 2013 + arXiv 2507.17162 restatement):**
- Frictionless target (Markowitz): `Mkw_t = (γ Σ)⁻¹ μ_t`, with `μ_t = B f_t` (signals `f_t` → expected returns via loading matrix `B`), `Σ` = return covariance, `γ` = absolute risk aversion.
- Partial-adjustment update: `x_t = x_{t−1} + (a/λ)·(aim_t − x_{t−1})`, trade-rate ratio `a/λ ∈ (0,1)`. (Trade a fixed fraction of the remaining gap each step; never jump to target.)
- Scalar trade rate (one-asset, discount→0 limit of `A_qq = (λ/2)(√(ρ²+4γσ²/λ) − ρ)`): **`a ≈ √(γ σ² λ)` ⇒ trade fraction `a/λ ≈ √(γ σ² / λ)`.** Load-bearing comparative statics: trade fraction **falls ∝ 1/√λ** (higher cost → trade slower / wider no-trade region) and **rises ∝ √(γσ²)** (higher risk → close the gap faster). Cost, not signal, sets the speed.
- Aim = persistence-weighted blend of current and *expected future* Markowitz targets: `aim_t = Σ_{k≥0} w_k·E[Mkw_{t+k}]`. Each signal `i` with mean-reversion rate `φ_i` (decay per step) enters the aim scaled ≈ `1/(1 + φ_i·z)` for a cost/risk constant `z`: **fast-decaying signals (high φ_i) are down-weighted; slow signals get "aim in front of the target."** ⇒ an hourly bar/residual signal (half-life ≈ 1 bar) is exactly what GP tells you *not* to chase — a formula-level indictment of the M16 fast leg.
- At our size use the **proportional-cost** variant (no-trade band), not GP's quadratic-impact `Λ`: trade only when `|Mkw_t − x_{t−1}| > h`; band half-width `h ∝ (cost/(γσ²))^{1/3}` (Constantinides/Davis-Norman shape). Inside the band, do nothing.

**Recommended starting parameters (autopsy defaults for a 5–33 name RTH book):**
| Knob | Start value | Rationale |
|------|-------------|-----------|
| Rebalance cadence | hourly (6–7/session) | matches manual capacity; but is the fast-decay regime GP penalizes |
| Trade-rate ratio a/λ | 0.10–0.30 | slow partial adjustment; turnover ≈ 10–30% of gap/step |
| No-trade band h | ≥ 2× round-trip cost (≈ 4–8 bps of price) | below this, E[edge] < cost — do not trade |
| Position sizing | inverse-vol (∝ 1/σ_i), residualized to market+sector β | express deltas only; kill shared-factor risk |
| Gross / per-name caps | ≤ $10k gross; ≤ 20–30% per name | whole-share, small-book reality |
| Signal half-life floor | ≥ several hours | only slow signals (LETF F(t), calendar) survive manual keying + GP aim weighting |
| Kill gate | median residual \|IC\| ≥ 0.08 AND N_eff ≥ 4 AND net ≥ 2× cost | all three or dead |

### Known intraday-effects map — with decay verdicts (adversarial read)
| # | Effect | Source (tier, yr) | Sample | Size / unit | Cost treatment | Decay verdict | Usable for our 5–33 book? |
|---|--------|-------------------|--------|-------------|----------------|---------------|---------------------------|
| 1 | Market intraday momentum (1st 30m → last 30m) | Gao–Han–Li–Zhou, JFE (T2, 2018) | SPY/ETF 1993–2013 | OOS R²≈1.2%; timing Sharpe large **gross** | NO-COST-MODEL for multi-name expression | DECAY-UNKNOWN post-2013; published + automatable → crowded prior | **NO** — market-level (breadth≈1 TS bet/day); collides with flat-15:50/MOC |
| 2 | Cross-sectional ½-hour periodicity (continuation at 1-day lags, ~40d) | Heston–Korajczyk–Sadka, JF (T2, 2010) | US TAQ ~2001–2005 | small per-interval continuation | "timing trades saves ≈ one effective spread" — i.e. edge ≈ spread | DECAY-UNKNOWN; liquidity-provision flavor → HFT-competed | **NO/MARGINAL** — as a *taker* you pay the spread the effect is worth |
| 3 | Short-horizon residual reversal (<1 hr) | HKS 2010; textbook (T2) | US intraday | reverts; temp-liquidity + bid-ask bounce | bounce-driven → phantom to a taker | crowded since 1990s | **NO** — maker/liquidity edge; our M3 killed it under honest fills |
| 4 | Overnight-vs-intraday "tug of war" | Lou–Polk–Skouras, JFE (T2, 2019) | US 1993–2013 | momentum profit **entirely overnight**; reversal intraday; large, opposite-signed legs | close-to-close; no intraday-capturable momentum net | robust in-sample | **NO** — capturable-intraday leg is reversal (liquidity); momentum leg needs OVERNIGHT hold = out-of-mission |
| 5 | LETF last-30-min rebalance flow | Barbon et al. (held) (T2/T3) | US ETF era | concentrated EOD flow | mechanistic | live / mechanistic | **YES but as a flow-anticipation PAYER** (DR-X1/X7), not a stat-arb pattern in this book |
| 6 | Classic pairs / PCA residual MR | Gatev+ 2006; Do–Faff 2012; Avellaneda–Lee 2010 (T2) | US 1963–2009 / 1997–2007 | ~93 bps/mo gross → ~12 net; refined ~30 bps/mo; Sharpe 1.44→0.9 | full cost models | **DECAYED** post-2002; crowded | **NO** — largely unprofitable net after 2002 |
| 7 | TOD seasonality of vol / spread / volume | microstructure lit. (T2) | broad | U-shaped spreads & vol | — | stable, but it is a **cost** pattern, not alpha | **Use only to time entries** (cut cost), never as edge |

### Sources
1. **T2** Grinold (1989); Grinold & Kahn, *Active Portfolio Management* — IR = IC × √BR; independent-bet definition of breadth.
2. **T2** Clarke, de Silva, Thorley (2002). *Portfolio Constraints and the Fundamental Law of Active Management.* FAJ 58(5). TC typically 0.3–0.8. https://people.duke.edu/~charvey/Teaching/BA491_2005/Transfer_coefficient.pdf
3. **T2** Gârleanu & Pedersen (2013). *Dynamic Trading with Predictable Returns and Transaction Costs.* Journal of Finance 68(6), 2309–2340. Aim portfolio + partial trade; fast signals deweighted. http://pages.stern.nyu.edu/~lpederse/papers/DynamicTrading.pdf
4. **T2** Bowen, Hutchinson, O'Sullivan (2010). *High Frequency Equity Pairs Trading: Transaction Costs, Speed of Execution and Patterns in Returns.* UCC. FTSE100 2007; 15 bp TC → >50% cut; one-period wait eliminates excess returns. https://www.ucc.ie/en/media/research/centreforinvestmentresearch/wp/wp1004high-frequency-equity-pairs-trading.pdf
5. **T2** Do & Faff (2012). *Are Pairs Trading Profits Robust to Trading Costs?* Journal of Financial Research 35(2). US 1963–2009; largely unprofitable after 2002 once costs included. https://onlinelibrary.wiley.com/doi/10.1111/j.1475-6803.2012.01317.x
6. **T2** Avellaneda & Lee (2010). *Statistical Arbitrage in the US Equities Market.* Quantitative Finance 10(7). PCA Sharpe 1.44 (1997–2007) vs 0.9 (2003–2007) after costs; crowding/degradation. DOI 10.1080/14697680903124632
7. **T2** McLean & Pontiff (2016). *Does Academic Research Destroy Stock Return Predictability?* Journal of Finance 71(1). ~32–35% post-publication decay. https://www.fmg.ac.uk/sites/default/files/2020-08/Jeffrey-Pontiff.pdf
8. **T2** Gao, Han, Li, Zhou (2018). *Market Intraday Momentum.* Journal of Financial Economics 129(2). First half-hour → last half-hour; market-level breadth. https://ideas.repec.org/a/eee/jfinec/v129y2018i2p394-414.html
9. **T2** Barber, Lee, Liu, Odean, Zhang (2017 working / related JFQA-line). *Do Day Traders Rationally Learn About Their Ability?* Taiwan 1992–2006 complete data; aggregate day trading negative; majority unprofitable. https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/Day%20Trading%20and%20Learning%20110217.pdf
10. **T2** Khandani & Lo (2007/2011). *What Happened to the Quants in August 2007?* Crowded long/short equity / mean-reversion unwind. https://web.mit.edu/Alo/www/Papers/august07.pdf
11. **T2** Gatev, Goetzmann, Rouwenhorst (2006). *Pairs Trading.* RFS. Classic pairs; ~162 bp round-trip cost estimate per pair; residual not beta risk. http://stat.wharton.upenn.edu/~steele/Courses/434/434Context/PairsTrading/PairsTradingGGR.pdf
12. **T1/project** enginev5.1 AGENT_BRIEF: dead list (bar-tier IC +0.03–0.05 / plan α≈0; sequences; trailing-PnL; maker phantom fills); champion +2.5 / +12.5; manual 5–25 s; $1k–$10k; flat 15:50.
13. **T3** Practitioner stat-arb notes (QuantInsti / quant guides): high turnover makes TC decisive; 2 bp alpha vs 3 bp impact is a net loser — qualitative reinforcement only.
14. **T2** Heston, Korajczyk & Sadka (2010). *Intraday Patterns in the Cross-section of Stock Returns.* Journal of Finance 65(4). ½-hour continuation at 1-day lags persists ~40 days; short-horizon reversal is temp-liquidity + bid-ask bounce; timing saves ≈ one effective spread. https://arxiv.org/pdf/1005.3535
15. **T2** Lou, Polk & Skouras (2019). *A Tug of War: Overnight Versus Intraday Expected Returns.* Journal of Financial Economics 134(1). Momentum profits accrue **entirely overnight**; reversal intraday; legs opposite-signed. https://personal.lse.ac.uk/polk/research/TugOfWar.pdf
16. **T2** arXiv 2507.17162 (2025) restatement of Gârleanu–Pedersen constant-vol solution — used to confirm scalar trade-rate form `A_qq=(λ/2)(√(ρ²+4γσ²/λ)−ρ)` and aim = persistence-weighted Markowitz blend. https://arxiv.org/html/2507.17162
17. **T2/T3** Brazilian day-trader census (Chague–De-Losso–Giovannetti line) + SEBI 2022–23 intraday study + FINRA 2020: 97% of persistent BR index-futures day traders lost money (1.1% > minimum wage); SEBI >70% intraday losers FY22–23; FINRA 72% of 2020 day traders net-negative — population prior for manual high-turnover speculation. (via aggregated day-trading statistics reviews)

#### Queries used
- Grinold Kahn fundamental law active management IR = IC × √breadth small N portfolio
- Garleanu Pedersen dynamic trading transaction costs no-trade band small cross section
- intraday momentum Gao Han Li Zhou post publication decay out of sample failure
- statistical arbitrage high frequency transaction costs kill profits pairs trading failure
- crowding mean reversion statistical arbitrage capacity decay alpha
- retail day trading performance Barber Odean day traders lose money 2020
- signal correlation portfolio construction netting turnover transaction costs multi-signal
- site:arxiv.org OR site:ssrn.com small universe equity market neutral minutes hours costs
- Do Faff pairs trading profits robust trading costs post 2000 decay
- McLean Pontiff anomaly publication decay alpha arbitrage crowding
- Avellaneda Lee statistical arbitrage PCA mean reversion transaction costs 2010
- Bowen Hutchinson high frequency equity pairs trading transaction costs 15 bps
- Clarke de Silva Thorley portfolio constraints transfer coefficient IR = TC × IC × sqrt(N)
- Khandani Lo August 2007 quant meltdown long short equity crowded strategies
- "effective number of independent bets" OR "correlated signals" breadth reduction Grinold portfolio IR
- Gârleanu Pedersen aim portfolio trading rate formula lambda kappa signal half life
- intraday momentum effect disappeared after 2013 SPY last half hour first half hour
- manual execution latency slippage human trader reaction time market impact retail
- Heston Korajczyk Sadka intraday periodicity cross-section half-hour seasonality
- Lou Polk Skouras tug of war overnight intraday returns momentum decomposition
- Garleanu Pedersen optimal trade rate formula aim portfolio (1-a) scalar one asset
- Gao Han Li Zhou market intraday momentum out-of-sample decay after 2018
- Bowen Hutchinson O'Sullivan high frequency equity pairs transaction costs speed execution FTSE
- Do Faff pairs trading profits robust trading costs post 2002 unprofitable
- Avellaneda Lee statistical arbitrage PCA Sharpe decline 2003 2007 crowding
- retail day traders lose money percentage profitable 2020 2023 Brazil Taiwan
