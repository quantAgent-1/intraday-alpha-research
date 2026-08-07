## DR-X10 — Modality D (adversarial / prior-art) findings

Object under attack: **F2 — buyback-dosage afternoon support.** Exact tradeable claim = long a
high-10b-18-dose name (GOOGL, 4–6% of own ADV) after a *soft morning* (09:35→11:30 own-return in
TRAIN bottom tercile), enter 11:30:00+latency, exit 15:30:00 taker, ex-blackout; dose-ladder and
GOOGL-minus-placebo prongs attached. This memo builds the KILL case against that specific object.

### Verdict recommendation
**EXHAUSTED-BY-FIELD (confidence MED).** The *mechanism* F2 rests on — 10b-18 turning the buyback
algo into an intraday "dip-buyer of last resort" that supports afternoons — is well-known
practitioner folklore, and the two literatures that have actually *measured* its footprint kill the
directional read: (i) rigorous blackout studies find buyback presence/absence has **no** measurable
market effect (idiosyncratic; ~5% correlation to the index), and (ii) the direct-execution
literature (markets where daily repurchase data exists) finds the intraday footprint of buyback
trades is **seller-initiated liquidity provision** — impact neutral-to-negative, a variance-damping
"support" (fewer/shallower dips), **not** a long-side afternoon drift a soft-morning long could
harvest. Honest square-root-law impact for GOOGL's daily clip is ~11–33 bps *total* footprint, ~half
transient/reverting, impounded *continuously* from the open, of which only a state-conditional slice
(~1–3 bps) is even in principle tradeable — below the 5–6.5 bps 2×-cost floor. The one thing the
field has *not* done is run F2's exact single-name soft-morning-long 11:30→15:30 test head-on
(literature there is thin) — so this is a mechanism+magnitude+execution kill, not a direct
replication. That residual gap is why confidence is MED, not HIGH.

**What would flip it:** a direct study (or F2's own $0 XBRL+quotes screen) showing a GOOGL-minus-
placebo afternoon mean **> ~6 bps net** that survives the return-sign control — i.e., evidence the
state-conditional redistribution is materially larger than the ~1–3 bps the impact arithmetic
allows. Nothing in prior art suggests that number exists.

### Mechanism
Who pays: the corporation, via a broker POV/10b5-1 algo — volume-mandated, price-capped by 10b-18
(≤ max[highest independent bid, last independent transaction]), price-insensitive within the day.
F2's directional bet is that the price cap makes the algo *asymmetric* (passive into strength, active
into weakness) so that after a soft morning the afternoon carries net upward support. The adversarial
reading: the price cap makes the algo a **passive liquidity supplier** — it stands on the bid and
lets sellers hit it (the Canadian daily-data evidence: ~60% of repurchase trades are *seller*-
initiated, so their same-second price impact is *negative*). That is exactly "buy-the-dip" liquidity
provision, which **dampens** downside variance without generating a capturable positive drift. On a
1-tick book (NVDA 1c ≈ 0.6 bps) the price condition almost never binds for a 5% POV algo except at
fresh highs — F2 concedes this — so the asymmetry it needs largely does not exist; what remains is
level support already impounded as the algo trades, not a forecastable afternoon move. No coherent
*directional* payer survives; the coherent payer that does survive (liquidity provision) is a
variance object, out of scope for a long-side mean trade.

### Claims
C1 [CONFIRMED] (T3, State Street / Bartolini & Kaplanian, sample ~1990s–2020s US): buyback **blackout
periods do not negatively impact** stock/market performance; buyback amount normalized by market cap
has only ~**5% correlation** to the S&P 500; high-buyback firms show "mostly idiosyncratic"
performance. — Symmetric implication: if the *absence* of the flow isn't measurable, the *presence*
providing intraday support isn't either. [SSGA PDF; Alpha Architect summary]
C2 [CONFIRMED] (T2/T3, Råsbrant, Swedish/Nasdaq-OMX daily repurchase data, ~2000–2009): average
abnormal return on *actual repurchase days* ≈ **+0.12%** (equal-wtd benchmark), ≈**+0.7% on the first
repurchase day**, statistically significant only in the **first ~3 days of a program**, and the
reaction is **permanent** (read as an undervaluation *signal*, not intraday pressure). — For a mature
multi-year GOOGL program this is the *decayed steady-state*, not the initiation spike; the effect is
a permanent signaling component, not a repeatable afternoon drift. [Nasdaq/DiVA]
C3 [CONFIRMED] (T2, Canadian open-market repurchase study cited in Råsbrant): the **average intraday
price impact of repurchase trades is negative**, because ~**60% are seller-initiated** — the algo
provides liquidity into weakness rather than pushing price up. — Directly contradicts F2's
"afternoon support pushes price up after a soft morning." [Nasdaq/DiVA lit review]
C4 [CONFIRMED] (T2, Hillert–Maug–Obernberger, JFE 2016, US 2004–2010, 50,204 repurchase-months):
repurchases **improve liquidity** and provide support **when other investors sell / in crisis** — an
IV-identified *liquidity/variance* result, **not** a directional-return result. — The sophisticated
version of the mechanism resolves to depth provision, not a long-side edge. [SSRN 2369470; JFE 119(1)]
C5 [CONFIRMED] (T3, Elm Wealth / Advisor Perspectives, 2025; Grinold-Kahn calc): $1.5T/yr buybacks ≈
$6bn/day ≈ **0.5% of daily volume**, moving the market ~**0.07%/day (~7 bps)** by the naive formula,
which the authors call **too high**; realistic whole-program impact "**3–5%**" for a 3%-of-cap annual
buyback (multiplier ~1–1.7×), **well below** Gabaix-Koijen's aggressive "$1 → $5" (multiplier 5). —
The order of magnitude everyone cites is a *slow, months-scale* inelastic-market repricing, not an
intraday-capturable drift; even the day-level number is flagged as overstated. [elmwealth.com]
C6 [CONFIRMED] (T1/T3, SEC Rule 10b-18 FAQ; Guzman/Raymond James practitioner guides): the 25%-ADTV
volume cap is recomputed **weekly** (4-week trailing ADTV), algos carry **±10–20% discretion** around
volume targets, and programs execute via **10b5-1 grids and ASRs** (bulk forward with a bank; the
bank bears the hedging over weeks). — F2's "quarterly ÷ 62 = uniform daily dose" is exactly the crude
proxy this reality breaks: US firms **do not disclose daily** repurchases, so the event-defining dose
is unobservable and lumpy; intraday discretion decouples daily dosage from any given afternoon's
presence. [SEC FAQ; StockTitan; Guzman guide]
C7 [CONFIRMED] (T3, practitioner folklore — EBC/Convex/RIA/WRAL-Goldman-2018): the tradeable "buyback"
idea in circulation is the **blackout-window / demand-vacuum trade** (weeks-scale, *index* level,
keyed to the earnings calendar), popularized after Q4-2018 when Goldman noted executions fell >50% in
the blackout. — The *crowded* buyback trade is a different object from F2 (calendar-timed index vol,
not intraday single-name long); F2 is less crowded, but the mechanism it borrows is the same one the
rigorous studies (C1) find not measurable. [WRAL; RIA; EBC — T3/T4, folklore-tagged]
C8 [CONFIRMED] (T2, ANcerno/BME-LSE impact studies): metaorder impact is **~50% transient** —
R_perm/R_temp ≈ **0.51 (BME), 0.73 (LSE)**; temporary impact decays over minutes-to-hours after the
child order stops. — Half of GOOGL's daily buyback footprint reverts intraday; the persistent piece a
third party could ride is smaller still. [arXiv 1901.05332; Lillo lecture notes]
C9 [PLAUSIBLE] (T2, asset-pricing meta-evidence): US buyback *announcement* drift has **decayed /
disappeared for recent repurchases** (post-publication returns ~50% smaller; long-run drift persists
mainly *outside* the US). — The one buyback effect that was ever robustly tradeable has itself decayed
in exactly our universe. [ScienceDirect S0929119919309368; Publication-Bias lit]
C10 [UNVERIFIED / GAP] (T-none): **no published study runs F2's exact object** — soft-morning-
conditioned single-name intraday long in high-dose megacaps, 11:30→15:30. The intraday-buyback
literature is thin and non-US (disclosure-driven). Absence of a head-on refutation is why this is
EXHAUSTED-BY-FIELD-on-mechanism, not a cited direct kill. A gap, reported as a gap.

### Constraint gates
| Gate | Verdict | Clause |
|---|---|---|
| 1 Latency | PASS | 11:30 & 15:30 are scheduled instants; 5–25 s pre-positionable. |
| 2 Access | PASS | GOOGL long $1k–$10k, plain market order, any retail broker. |
| 3 Session | PASS | RTH, flat 15:30 — inside 15:50 rule; no auction. |
| 4 Data | PASS (mechanism) / **FAIL (dose)** | Owned quotes suffice for the *screen*; but the daily dose that *defines* the event is **not disclosed** for US names — XBRL quarterly ÷ 62 is a proxy the execution reality (C6) breaks. |
| 5 Fill realism | PASS | Taker legs, continuous but liquid GOOGL; no maker assumption. |
| 6 Statistics | PARTIAL | ~513 GOOGL soft-morning TRAIN events, se ≈ 4 bps → detects ≥ 8 bps; but the honest effect (~1–3 bps net) is **below detectable AND below cost floor** → structurally underpowered against its own prior. |
| 7 Protocol | PASS-form / FAIL-substance | Payer *is* nameable and pre-registrable (its strength), but the named payer resolves to a *liquidity/variance* provider (C3–C4), not a directional one — the a-priori mechanism is contradicted before results. |

**Survivor-profile score: 2 / 5.**
1. Single-print/auction execution — **NO** (continuous-market taker, both legs). 0
2. Scheduled decision instant — **YES** (11:30 / 15:30 frozen). 1
3. Named *price-insensitive* payer — **HALF→NO**: payer is named and price-insensitive, but its
   documented intraday action is passive seller-side liquidity provision (C3), not directional
   support → the *directional* payer F2 needs is not the one that exists. 0 (generous: the mechanism
   as *directional* fails prior art).
4. Testable on owned/≤$100 data — **YES** ($0 XBRL + owned quotes). 1
5. Effect ≥ 2× cost burden — **NO**: honest ~1–3 bps net vs 5–6.5 bps floor. 0
   → **2/5** (below the "extraordinary reason to research at all" line of ≤2 in the brief).

### Economics sketch
Honest square-root impact of GOOGL's *own* daily clip: I = Y·σ_d·√(Q/V) with Y≈0.5, σ_d≈100–150 bps,
Q/V≈0.05 → I ≈ **11–17 bps** (Y=0.5) up to ~34 bps at the aggressive Y=1 — this is the **total**
footprint of the *whole day's* buying, not an afternoon event. Net it down the way the field forces:
(a) ~**50% is transient and reverts** intraday (C8) → ~6–8 bps persistent; (b) it is impounded
**continuously from 09:30**, so by 11:30 a large share is already in the price — the *incremental*
afternoon drift is a few bps at most; (c) F2 only claims the **state-conditional redistribution**
(the *extra* support on soft mornings vs normal), a fraction of that → **~1–3 bps** capturable in the
best honest case. Cost burden: GOOGL RT ≈ 2.5–3.3 bps → **2× floor ≈ 5–6.5 bps**. **Net prior:
negative to ~breakeven.** Even F2's own optimistic +4–8 bps gross *straddles* the floor and *assumes*
the state-conditioning C3–C4 say is a liquidity effect, not a drift. Comparison line: **champion =
+2.5 bps/event dev / +12.5 holdout**, single-print, 5/5 survivor — F2 is a continuous-market 2/5 with
a net-negative honest prior.

### Proposed next test
N/A — verdict is EXHAUSTED-BY-FIELD, not OPEN-TESTABLE. If the orchestrator registers anyway, do it
**only** as the pre-declared $0 diagnostic (GOOGL-minus-placebo afternoon mean on owned quotes, dose
frozen PIT-lagged), with the a-priori kill written in: **PASS requires placebo-diff > 6 bps net AND
survival of the {sign(r_morning), sign(gap)} control** — because C3 (seller-initiated intraday
footprint) and C6 (no US daily dose, lumpy ASR execution) make the modal outcome a NULL that prices
the buyback-support axis permanently and admits GOOGL dose only as a passive long-side *conditioner*,
never a standalone plan. Charges the reversion/dip-buy family debt (adjacent to M18/DR-X7); the
placebo-diff prong is what keeps it from being generic dip-buying in disguise.

### Sources
1. [T3] SSGA (Bartolini & Kaplanian), "Buyback Blackout Periods Do Not Negatively Impact Performance,"
   ssga.com PDF; summarized via Alpha Architect (alphaarchitect.com/buyback-blackout-periods-do-not-
   negatively-impact-market-performance). Sample ~1990s–2020s US. — C1.
2. [T2/T3] Jonas Råsbrant, "The Price Impact of Open Market Share Repurchases," 2011 (Swedish/Nasdaq-
   OMX daily data ~2000–2009), nasdaq.com/docs/…2011.pdf; diva-portal.org diva2:621450. — C2, C3.
3. [T2] Hillert, Maug, Obernberger, "Stock Repurchases and Liquidity," JFE 119(1):186–209, 2016 (US
   2004–2010, 50,204 repurchase-months), SSRN abstract_id=2369470. — C4.
4. [T3] Elm Wealth / Advisor Perspectives, "The Impact of U.S. Stock Buybacks: Theory vs Practice,"
   2025 (Grinold-Kahn + Gabaix-Koijen 2023 discussion), elmwealth.com/stock-buybacks. — C5.
5. [T1] SEC Division of Trading & Markets, Rule 10b-18 Safe Harbor FAQ, sec.gov; plus Guzman & Co.
   "Share Buybacks Practitioner's Guide" 2025 and StockTitan 10b-18 guide (weekly ADTV, ±10–20%
   discretion, 10b5-1/ASR mechanics). — C6.
6. [T3/T4 folklore] WRAL/Goldman "blackout deepening turbulence"; RealInvestmentAdvice; EBC Financial;
   ConvexTrade blackout glossary — the crowded blackout-window/demand-vacuum trade. — C7.
7. [T2] "Slow decay of impact in equity markets (ANcerno)," arXiv 1901.05332; Lillo Imperial lecture
   notes (temporary vs permanent impact ~½; R_perm/R_temp ≈ 0.51 BME / 0.73 LSE). — C8.
8. [T2] "Repurchases after being well known as good news," ScienceDirect S0929119919309368; asset-
   pricing publication-bias / anomaly-decay literature (post-pub returns ~50% smaller). — C9.

#### Queries used
- `buyback blackout window trading strategy anomaly returns decay`
- `corporate buyback intraday price support 10b-18 safe harbor empirical study`
- `share repurchase execution algorithm participation rate VWAP institutional trader`
- `buyback price impact magnitude basis points square root law repurchase execution`
- `"buyback" OR "repurchase" execution desk lumpy discretion "10b5-1" tranche timing weeks`
- `buyback anomaly returns monthly announcement drift not intraday post-publication decay replication`
- `stocks with buybacks intraday afternoon return pattern reversal U-shape empirical evidence`
- `"buyback blackout" trade crowded sell-side note Deutsche Bank Goldman flow desk market impact overstated`
- `POV algorithm temporary impact reversion permanent impact fraction intraday price recovery`
- `buybacks estimated market impact SPX support billions daily overstated myth research`
- `Alphabet Google GOOGL buyback daily execution 10b5-1 accelerated share repurchase ASR tranche`
- `Hillert Maug Obernberger stock repurchases liquidity actual daily execution market quality price support`
- `actual repurchase days abnormal return price effect same-day intraday firm buying own stock evidence`
- `buyback trades seller-initiated passive liquidity provision buy the dip intraday not push price up`
