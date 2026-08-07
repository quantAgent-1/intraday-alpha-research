## DR-X4 — B primary/venue findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence **HIGH** on exchange/broker mechanics; **MED** on name-level TOD half-spreads for the exact megacap set until measured on owned SIP) — Venue rules supply hard, non-optional bounds for the M16 cost-aware position book: (i) continuous inventory must be flat by **15:50 ET** under mission rules, coinciding with the Nasdaq **on-close cancel/modify freeze** and Alpaca **CLS reject after 15:50**; residual risk may only ride to the **16:00 cross** via MOC/LOC submitted before the tighter of exchange and broker cutoffs; (ii) liquid Nasdaq megacaps are structurally **1-tick** markets under the Reg NMS penny-tick regime (≥$1), so half-spread floors are **0.5¢/share** (~0.1–0.5 bps one-way at $100–$500 prices) and round-trip continuous cost priors start there before adverse selection; (iii) **intraday short legs** are Reg SHO–locate gated and, at Alpaca (current broker), require **≥$2,000 equity** plus ETB (or explicit HTB locate) — most target megacaps are ETB with **$0 borrow fee**, so same-day flat shorts do not accrue overnight stock-loan charges. These are design parameters, not an alpha claim.
What would flip it: Live confirmation that (a) the intended short universe routinely leaves the Alpaca ETB list mid-session or fails the $2k margin floor at deploy size, or (b) owned-SIP measurement shows midday effective half-spreads systematically **≫** 1 tick for $1k–$10k marketable clips on the target names (DR-X3 domain).

### Mechanism
No continuous-market “payer” is claimed in this lane. The microstructure facts that **bound** M16 are:

1. **Session / auction clock (Nasdaq Closing Cross).** On-close interest freezes for cancel/modify at **15:50**; MOC entry ends **15:55**; late LOC **15:55–15:58** (reprice-capped); cross **16:00** sets NOCP from MOC+LOC+IO+continuous book. Continuous marketable interest remains enterable until the cross and **does** participate with price standing. Broker gates (Alpaca CLS ≤15:50; others earlier) are often **tighter** than exchange MOC. Mission “flat by 15:50 or AT the close via MOC/LOC” therefore maps 1:1 onto exchange/broker state machines: last continuous rebalance ≤15:50; optional MOC residual if pre-broker-cutoff.

2. **LULD adjacency.** Tier-1 names (S&P 500 / Russell 1000 / select ETPs — covers the megacap book) have **doubled** price bands in the **last 25 minutes** (from **15:35**). A Trading Pause in the **last 10 minutes** prevents continuous reopen; the primary attempts a closing transaction via established close procedures. Manual hourly books that count on continuous exit after 15:50 are structurally wrong; books that pre-schedule MOC/LOC or hard-flat at 15:50 are robust.

3. **Short-sale / locate (Reg SHO + retail broker practice).** Rule 203(b) requires a documented locate (or borrow/arrangement) **before** effecting a short. Retail brokers operationalize this via **Easy-to-Borrow (ETB)** lists (reasonable-grounds basis when current) and HTB locate desks. Same-day buy-to-cover can allow locate reuse for non-HTB/non-threshold names under SEC guidance cited by FINRA; HTB/threshold require fresh locates. Rule 201 (−10% from prior official close) forces short sales **above** NBB for the rest of day + next day when triggered — rare for diversified megacaps, material for single-name crash days.

4. **TOD cost floor.** Exchanges do **not** publish free, name-level, minute-binned NBBO spread tables for free public consumption that can be treated as a finished M16 parameter file. Structural floors (penny tick, MM obligations, RTH vs overnight quality) plus owned SIP measurement are the operational path. Capacity at $1k–$10k is de minimis vs top-of-book depth on NVDA/TSLA/AAPL/etc.; impact is not the binding constraint — **spread + adverse selection + manual latency** are.

### Claims
C1 [CONFIRMED] (T1, Nasdaq Closing Cross FAQ, current; rules post-2018 cutoff change): **Nasdaq on-close timeline:** accept MOC/LOC/IO prior to 15:50; at **15:50** early NOII starts and **MOC/LOC/IO may not be canceled or modified** (except legitimate error correction under exchange process); at **15:55** MOC entry stops and full NOII (with Near/Far) begins every **1 s**; late LOC until **15:58** (reprice to more aggressive of 15:50/15:55 Reference Prices if more aggressive); IO until 16:00; Closing Cross at **16:00** maximizes paired shares over on-close + continuous interest → NOCP. — https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf

C2 [CONFIRMED] (T1, same FAQ + openclose FAQs): **NOII schedule:** 15:50–15:55 every **10 s** — paired shares, imbalance side/qty, Current Reference Price; 15:55–16:00 every **1 s** adds **Near** (on-close + continuous) and **Far** (on-close only) indicative clearing prices. Continuous market orders remain enterable until the cross and are included with price standing. ~**10%** of Nasdaq ADV prints in the closing auction (exchange FAQ). — ClosingCrossfaq.pdf ; https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf

C3 [CONFIRMED] (T1, Alpaca Orders docs): Alpaca MOC/LOC via `time_in_force=cls`; **CLS submitted after 15:50 ET and before 19:00 ET is rejected**; after 19:00 queued next day; whole shares only for CLS. This makes Alpaca’s retail on-close gate **equal to the exchange freeze clock**, not the exchange MOC 15:55 door. — https://docs.alpaca.markets/docs/orders-at-alpaca

C4 [CONFIRMED] (T1, LULD Plan / luldplan.com; Investor.gov summary of bands): For **Tier 1** NMS stocks (S&P 500, Russell 1000, select ETPs), percentage price bands are **doubled during the last 25 minutes** of RTH (i.e., from **15:35**). Limit State lasting **15 s** → **5-minute** Trading Pause (extendable). **If a security is in a Trading Pause during the last 10 minutes of RTH, the primary listing exchange will not reopen continuous trading** and will attempt to execute a closing transaction under its established closing procedures. Formula: Price Band = Reference Price ± (Reference Price × Percentage Parameter). — https://www.luldplan.com/ ; Nasdaq Rule 4120 / 4754 LULD Closing Cross provisions

C5 [CONFIRMED] (T1, SEC Key Points About Regulation SHO, modified 2022-05-31): **Rule 203(b) locate:** broker-dealer must borrow, arrange to borrow, or have **reasonable grounds** to believe the security can be borrowed for settlement **before** effecting a short sale; locate must be **documented prior** to the short (applies even if covered same day). **Rule 201:** listing market flags a **≥10%** decline from prior RTH close → trading centers must prevent short sales at ≤ NBB for remainder of day **and the following day** (exceptions apply). **Rule 200** marking: long / short / short exempt. — https://www.sec.gov/investor/pubs/regsho.htm ; 17 CFR § 242.201

C6 [CONFIRMED] (T1, FINRA 2023 Exam/Risk Monitoring — Regulation SHO): SEC guidance (Q4.4): if a locate is obtained, the short is executed and **covered same day**, the locate may be **reused** for a subsequent short that day for quantity ≤ original locate, **provided** the locate source deemed it good for the entire day — **except** hard-to-borrow or **threshold** securities, for which locates may **not** be re-applied across intraday cover cycles. — https://www.finra.org/rules-guidance/guidance/reports/2023-finras-examination-and-risk-monitoring-program/regulation-sho

C7 [CONFIRMED] (T1, Alpaca Margin & Short Selling docs + Short Selling Fees support, 2025–2026): Shorting requires **≥$2,000 account equity** (below that: 1× BP, no margin/short). **5,000+ ETB** names; **$0 locate and $0 borrow fees** on ETB for Trading API users. HTB: requires approved locate (API: quote → request → track); locate requests in **100-share round lots**; locates currently **single-use** (cover does not replenish); locate fees **non-refundable** if unused; daily HTB borrow fee = Σ(HTB short MV × rate)/360, charged on nearest round lot; Friday EOD short accrues **3 calendar days**. Short maintenance (illustrative table): price ≥$5 → greater of $5/share or 30% SMV. Assets endpoint exposes `shortable` / `borrow_status`. — https://docs.alpaca.markets/docs/margin-and-short-selling ; https://alpaca.markets/support/short-selling-fees

C8 [CONFIRMED] (T1, IBKR Short-Securities Availability / SLB): IBKR exposes electronic **Securities Loan Borrow** search: quantity available, lender count, **indicative borrow rate**, historical rates; updates **periodically through the day**; lists are **indicative and subject to change**; US short sales require DTC CNS eligibility and IBKR approval. Separate short-sale cost = borrow fee net of short-proceeds interest. Pre-borrow tooling exists for some account types. — https://www.interactivebrokers.com/en/trading/short-securities-availability.php

C9 [CONFIRMED] (T1, structural / Reg NMS tick + exchange quality framing): For NMS stocks priced **≥$1**, minimum quotation increment is **$0.01**. Therefore the **minimum displayed half-spread is 0.5¢/share**. In bps of mid: half-spread_bps = 10000 × 0.005 / P. Examples: P=$50 → **1.0 bps**; P=$100 → **0.5 bps**; P=$200 → **0.25 bps**; P=$500 → **0.10 bps**. Round-trip at 1-tick market (cross bid+ask) = **2×** those figures before fees/adverse selection. Exchanges do **not** ship a free public TOD×symbol half-spread parameter file for M16; name-level RTH quality must be measured on owned SIP (or Rule 605 aggregates, which are market-center/month, not minute-of-day). Overnight vs RTH: Nasdaq-published research notes materially **wider** overnight quoted spreads and **shallower** depth vs RTH for continuously traded overnight names — reinforcing RTH-only mission as the better cost regime. — Reg NMS Rule 612 (sub-penny); Nasdaq market-quality / 24-hour trading notes

C10 [CONFIRMED] (T1, synthesis for M16 session engine): **Auction-adjacent design rules that M16 must hard-code:** (1) last **continuous** inventory rebalance / flatten clock = **15:50 ET** (mission + Alpaca CLS + exchange freeze coincidence); (2) MOC residual inventory only if submitted **before min(broker CLS cutoff, exchange 15:55)** — on Alpaca that is **15:50**, so MOC must be staged **with** the final continuous pass, not after a 15:55 signal; (3) continuous marketable after 15:50 can still trade and can enter the cross, but violates mission session rule unless user amends; (4) short opens require pre-checked ETB (or HTB locate) and equity ≥$2k on Alpaca; same-day cover on ETB does not create overnight borrow fee; (5) Rule 201 days: short marketable at/through bid may reject or reprice — plan must detect short-sale circuit-breaker list (Nasdaq publishes daily).

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **PASS** (scheduled cadence) | Hourly rebalance + 15:50 flatten are clock-scheduled; 5–25 s manual is inside the hour, not fighting sub-second microstructure |
| 2 Access | **PASS** long; **CONDITIONAL** short | Long continuous + Alpaca CLS available; shorts need margin equity ≥$2k + ETB/HTB path; Fidelity/Schwab also require margin agreement ($2k floor industry-standard) |
| 3 Session | **PASS** if engine enforces 15:50 | Continuous flat ≤15:50 **or** MOC/LOC AT 16:00 is in-mission; LULD last-10-min pause forces auction path |
| 4 Data | **PASS** | Mechanics $0; TOD spread calibration on **owned SIP** (no new $); optional Rule 605 free public files for cross-check |
| 5 Fill realism | **PASS** for design bounds; **FAIL** if maker assumed | Cost floor uses taker half-spread / marketable; maker rebate capture is dead (M3) and out of brief |
| 6 Statistics | **N-A** for mechanics; **PASS** for cost map | Venue facts are deterministic; SIP-estimated half-spreads by TOD bin easily n≫250 name-sessions |
| 7 Protocol | **PASS** | Pre-register M16 with a-priori cost model parameters from C9 + measured SIP TOD; no new alpha family claimed here |

Survivor-profile score: **3/5** as *infrastructure for a cost-aware book* (not a standalone edge).
1. Single-print/auction: **+1** if residual inventory exits via MOC/cross; **0** for pure continuous hourly legs  
2. Scheduled decision: **+1** (hourly + 15:50 clocks)  
3. Named payer: **0** (this lane maps costs/constraints, not a payer)  
4. Testable cheap: **+1** (owned SIP + $0 T1 docs)  
5. ≥2× cost at size: **N-A / 0** until signal gross is specified (M16 open design)

### Economics sketch
- **Gross:** Not applicable as a signal; this lane sets the **cost side** of M16. Continuous marketable RT cost prior on 1-tick megacaps: **~0.2–2 bps** round-trip from half-spread alone at $50–$500 prices (C9), **plus** adverse selection over 5–25 s manual lag (measure on SIP; DR-X3 owns effective-spread empirics). Auction residual exit ≈ **0 continuous exit spread** if filled at NOCP (champion structure).
- **Our cost burden for this structure:** (i) per rebalance leg: ≥ half-spread floor; (ii) n≈5–33 names × hourly cadence with turnover budget → order count must stay in manual band (~10–30 tickets/day feasible per brief) so **partial adjustment / no-trade band** (Modality A formulas) is mandatory, not optional; (iii) ETB shorts same-day: **$0 borrow** on Alpaca; HTB locate fee + borrow if used; (iv) post-promo commission stress (after 2026-12-31) is annotation, not gate.
- **Net prior:** Venue facts do **not** create edge; they **cap** how often M16 may trade. If per-leg cost is ~1 bps RT and hourly signals are sub-bps after costs, no-trade bands must dominate — consistent with Garleanu–Pedersen style partial adjustment (academic lane).
- Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout** (auction single-print). Continuous hourly book must clear a **higher** cost bar per event than the champion unless gross is large or turnover is tiny.

### Proposed next test (only if OPEN-TESTABLE)
**Hypothesis (mechanics / cost map, not alpha):** On the M16 universe (5–33 liquid Nasdaq names), SIP-measured share-weighted quoted half-spread in RTH by 30-min bin is **≤ 1.0 tick** for ≥90% of name-minutes in 10:00–15:30, and **elevated** in 09:30–10:00 and 15:30–16:00 (U-shape), so M16 should apply **TOD-scaled cost** c_t with midday baseline = 0.5¢ and open/close multipliers estimated from data (a-priori: open mult ∈ [1.5, 3], close mult ∈ [1.2, 2] pending measurement).
**Named payer:** None — cost-model registration only.
**Data needed:** Owned Alpaca historical SIP quotes (free to project). No purchase.
**Universe:** Champion 5 + M11 liquid expansion; filter `shortable`/ETB for short-leg eligibility.
**Expected n:** Years of RTH minutes × names ≫ 250; power is not the issue.
**A-priori thresholds:** Publish TOD half-spread table (median, p90) in bps and cents; fail-open if midday median half-spread > 2 ticks on >20% of name-days (would break “1-tick prior”).
**Promotion rule:** Freeze the TOD cost table + 15:50 flatten/MOC residual SOP as M16 Phase-0 inputs; shorts restricted to ETB unless HTB locate budget approved.
**Kill criteria:** If SIP shows effective spreads at our size dominate any plausible hourly IC×vol edge after no-trade bands (joint with Modality A/D), M16 continuous book is NOT-VIABLE-STRUCTURAL — auction residual remains the only in-profile path.
**Trial family:** M16 Phase-0 cost/session harness (charges new family; does not revive dead intraday alpha families).

### Design cheat-sheet (venue bounds for M16) — formulas & parameters

**Session state machine (hard):**
```
if clock < 15:50 ET:
    allow continuous open/adjust/close (manual)
if clock ≥ 15:50 ET:
    continuous NEW risk: FORBIDDEN under mission
    MOC/LOC: only if already accepted by broker before its cutoff
      Alpaca CLS cutoff = 15:50 (reject after)
      Exchange MOC cutoff = 15:55; LOC = 15:58; freeze cancel/mod = 15:50
if 15:35 ≤ clock < 16:00:
    LULD bands = 2× normal Tier-1 parameters
if TradingPause active and clock ≥ 15:50:
    no continuous reopen; closing procedures only
flat_at_close_ok := MOC/LOC working toward 16:00 cross
```

**Half-spread floor (structural, cents and bps):**
```
tick = 0.01 USD                    # stocks with P ≥ $1
half_spread_floor_usd = tick / 2   # 0.005
half_spread_floor_bps(P) = 1e4 * half_spread_floor_usd / P
# RT taker-taker at 1-tick market:
rt_spread_bps(P) = 2 * half_spread_floor_bps(P)
```
Starting **cost parameter** for no-trade band width (hand-off to GP formulas in Modality A): use `c = half_spread_floor_bps(P) + AS_buffer`, with `AS_buffer` calibrated from SIP (start **0.5–1.0×** half-spread midday; higher near open).

**Short eligibility gate (Alpaca-centric):**
```
allow_short(symbol) :=
    account_equity ≥ 2000
    AND asset.shortable
    AND (borrow_status == easy_to_borrow
         OR active_htb_locate_qty ≥ order_qty)
# Same-day flat ETB: borrow_fee ≈ 0
# Rule 201 active: short only at price > NBB (broker/exchange enforce)
```

**Order-count budget (manual feasibility):**
```
max_tickets_per_day ≈ 10–30   # brief operational bound
⇒ with n_names ∈ [5, 33] and hourly checks (≈6.5 RTH hours to 15:50):
   average turns_per_name_per_day must be ≪ 1
   ⇒ no-trade bands / partial adjustment mandatory
```

**Known microstructure effects that are facts (not alpha):**
| Effect | Status | Design implication |
|--------|--------|-------------------|
| U-shaped spreads/volume (open & close elevated) | Field consensus; measure on SIP | Scale `c_t` by TOD; avoid first 15–30 min for discretionary adds if cost-sensitive |
| Closing auction ~10% ADV (Nasdaq FAQ) | T1 fact | Residual MOC is high-capacity at our size |
| 15:50 freeze of on-close cancel/mod | T1 fact | Cannot “undo” MOC after 15:50 except error process |
| Near/Far NOII only after ~15:55 | T1 + our data | Cannot drive MOC with 15:55:10 near-basis on Alpaca (CLS already closed) |
| LULD band double after 15:35; pause last 10 min → no reopen | T1 fact | Continuous exit optionality dies in extreme moves near close |
| Penny-tick half-spread floor | T1 structural | Cost model floor in bps shrinks as price rises |
| ETB locate for liquid megacaps; $0 ETB borrow (Alpaca) | T1 broker | Same-day short legs economically clean if ETB |
| Rule 201 short uptick-style limit after −10% | T1 | Crash-day short adds may be delayed/rejected |

### Sources
1. **[T1]** Nasdaq Closing Cross FAQ (PDF) — 15:50 freeze, 15:55 MOC stop, 15:58 LOC stop, NOII 10 s / 1 s, Near/Far, continuous inclusion, ~10% ADV. https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf (fetched/read 2026-07-18)
2. **[T1]** Nasdaq Opening and Closing Crosses FAQs (PDF) — MOC prior to 15:55; late LOC reprice rules; reject after cutoffs. https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf
3. **[T1]** SEC “Key Points About Regulation SHO” (modified 2022-05-31) — Rules 200/201/203/204; locate documentation; circuit breaker −10%. https://www.sec.gov/investor/pubs/regsho.htm
4. **[T1]** 17 CFR § 242.201 — Short sale price test circuit breaker text. https://www.law.cornell.edu/cfr/text/17/242.201
5. **[T1]** FINRA Examination and Risk Monitoring Program 2023 — Regulation SHO section (locate reuse Q4.4; HTB/threshold exception). https://www.finra.org/rules-guidance/guidance/reports/2023-finras-examination-and-risk-monitoring-program/regulation-sho
6. **[T1]** Limit Up-Limit Down Plan site — Tier 1/2 bands; last-25-min doubling; last-10-min pause → no reopen continuous. https://www.luldplan.com/
7. **[T1]** Alpaca “Margin and Short Selling” — $2k equity, ETB $0 fees, HTB locate API, margin tables, borrow fee formula /360. https://docs.alpaca.markets/docs/margin-and-short-selling
8. **[T1]** Alpaca Support “What are the fees for short selling?” (Nov 2025) — ETB only historically; $0 ETB borrow; HTB path evolving. https://alpaca.markets/support/short-selling-fees
9. **[T1]** Alpaca “Placing Orders” — CLS after 15:50 reject; OPG/CLS auction TIFs. https://docs.alpaca.markets/docs/orders-at-alpaca
10. **[T1]** IBKR Short-Securities Availability / SLB — indicative quantity, rates, intraday updates. https://www.interactivebrokers.com/en/trading/short-securities-availability.php
11. **[T1]** Nasdaq Trader Short Sale Circuit Breaker page — Rule 201 implementation; daily list. https://www.nasdaqtrader.com/trader.aspx?id=shortsalecircuitbreaker
12. **[T1]** Nasdaq Rule 4754 / Equity 4 (Closing Cross, LULD Closing Cross) — listingcenter.nasdaq.com rulebook
13. **[T1]** Schwab / Fidelity margin+short help — margin account required; ~$2k minimum equity industry practice. https://www.schwab.com/margin/margin-rates-and-requirements ; https://www.fidelity.com/webcontent/ap002390-mlo-content/19.09/help/learn_margin_selling_short.shtml
14. **[T1/T3]** Nasdaq “Looking All Day for Data on 24-Hour Trading” — overnight quoted spreads ~40% higher, depth ~47% of RTH for daily overnight names (RTH cost regime superior). https://www.nasdaq.com/articles/looking-all-day-data-24-hour-trading

#### Queries used
1. `Nasdaq Closing Cross FAQ MOC LOC freeze 15:50 15:55 cutoff`
2. `Nasdaq market hours continuous trading LULD market maker obligations RTH`
3. `FINRA Rule 4320 4210 locate requirement short sale retail broker`
4. `SEC Regulation SHO locate borrow requirement broker-dealer short sale`
5. `Nasdaq Trader market quality statistics average spreads by time of day`
6. `Alpaca short selling locate easy to borrow stock borrow fees`
7. `FINRA Rule 201 short sale circuit breaker tick test Reg SHO`
8. `site:nasdaqtrader.com Closing Cross FAQ cancel modify freeze 15:50`
9. `Cboe OR Nasdaq market quality report quoted spreads intraday U-shape megacap`
10. `Interactive Brokers short stock availability locate HTB easy to borrow retail`
11. `SEC Rule 605 report effective spread Nasdaq stocks by time of day`
12. `LULD limit up limit down last 25 minutes closing auction Nasdaq`
13. `SEC FAQ Regulation SHO locate same day cover reuse easy to borrow`
14. `Schwab OR Fidelity short sell easy to borrow locate requirement margin account`
15. `Nasdaq Rule 4754 Closing Cross MOC LOC cutoff 15:50 15:55 15:58`
16. `Nasdaq NOII dissemination schedule 15:50 every 10 seconds 15:55 every 1 second near far price`
