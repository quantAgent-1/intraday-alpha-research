## DR-X3 — D adversarial findings

### Verdict recommendation
**OPEN-TESTABLE** (confidence **MED–HIGH** on the *skeptical* cost prior; **LOW** on any sub-half-spread fill assumption) — Published retail price-improvement / low-E/Q statistics systematically **overstate** what a $400–$3,000 marketable clip on liquid Nasdaq names pays in the last 15 minutes. Headline wholesaler / broker E/Q (~0.28–0.55) is dominated by (a) wide-spread and small-cap names, (b) low-priced odd lots where sub-penny PI is large in %, (c) an NBBO benchmark wholesalers can widen (odd-lot / hidden liquidity ignored), (d) *uninformed average* retail flow, and (e) market-order rather than marketable-limit bins. For OUR use the load-bearing prior is: **overall liquid E/Q ≈ 0.7–1.0 of quoted spread; last-15-min / signal-timed E/Q ≈ 0.9–2.0** (project sim already shows entry shortfall 1.46 bps vs 0.73 bps quoted half-spread at 15:55:10 → E/Q ≈ 2.0). There is **no clean T1/T2 evidence of secular deterioration 2024–2026** (industry claims continued E/Q *improvement*); the hard adversarial case is **selection + timing + benchmark**, not decay. Note: the champion itself trades AT the 16:00 cross (single MOC print) and pays no continuous effective spread — this charge prices the *new* minutes-hours M16 book only.

**What would flip it:** Broker-account-level (Alpaca) fills on champion names at 15:50–15:59 showing effective half-spread ≤ 0.5× quoted half-spread on n ≥ 100 marketable clips, with mid fixed at order *decision* time (not post-fill mid) and an odd-lot-aware benchmark — i.e., realized E/Q ≤ 0.5. Absent that live receipt, keep the conservative charge.

### Mechanism
**Who pays (optimistic PI story):** Wholesalers segment low-toxicity retail flow from institutional flow; reduced adverse selection lets them fill inside the NBBO and still earn positive realized spreads. Brokers route on aggregated execution quality; scale at Citadel/Virtu/Jane Street transfers some surplus as price improvement.

**Why that story fails for *us* (adversarial):**
1. **Wrong stock set.** Equal-weighted / full-universe averages put mass on wide-spread small-caps where PI as % of spread is large; dollar-volume-weighted liquid megacaps (our universe) trade at 1–2-tick quotes where sub-penny PI is a few mills — small in bps.
2. **Wrong information set.** PI is compensation for *uninformed* flow. A 15:55:10 basis trade is publicly conditioned on NOII near/far; mid is already drifting; the wholesaler adverse-selection filter treats this closer to toxic than to a Robinhood lottery ticket. Project shortfall (1.46 vs 0.73 bps half-spread) is the receipt.
3. **Wrong order type / routing.** Wholesalers preferentially internalize *market* orders; marketable *limits* are more often re-routed to exchanges and receive PI less often (SEC study: 100-sh NYSE market orders 68.2% PI-rate vs 53.6% for marketable-limit). A "smart" marketable-limit habit is structurally the worse 605 bin.
4. **Gamed benchmark.** Rule 605 PI/E/Q are measured vs NBBO, which excludes odd-lots and hidden liquidity; wholesalers also have incentive to keep on-exchange quotes wide (they post there) to inflate the referenced benchmark. NBBO-based PI overstates true economic savings by up to **4×** (Adams; Ernst ~400%). SEC's 2024 605 rewrite adds a "best available displayed price" (odd-lot-inclusive) benchmark and mandatory E/Q *precisely because* the old stats were gamed.
5. **Broker dispersion.** Identical simultaneous orders get 7–46 bps round-trip cost across six accounts; PFOF does NOT explain the gap; Alpaca is not in the best-broker set of that experiment and publishes no PI stats of its own.
6. **Time-of-day.** Effective spreads follow an intraday **U-shape — widest at open and close**; PI is higher early and thins late, exactly in the 15:45–16:00 window our inventory book would trade.

**Capacity intuition:** At $400–$3,000 notional, size improvement is free; the binding cost is the effective half-spread on liquid 1-tick names under adverse mid drift in the last 15 minutes. No payer improves our continuous-taker fill beyond the NBBO when we are the informed side.

### Claims
C1 [CONFIRMED] (T2, Dyhrberg/Shkilko/Werner, Dec-2023 WP / JFE 2025, sample Rule 605 2019–2022): Wholesaler full-sample **E/Q ≈ 0.76** (eff 53.16 / quoted 69.60 bps); exchanges ≈ 0.97. The flattering "≈47% of quoted spread PI" is the **S&P 500 equal-weight** figure — not dollar-volume-weighted liquid Nasdaq, not last-15-min; wholesalers also quote wider on-exchange to inflate the internalization benchmark, worst in small/heavily-internalized names. — ssrn 4313095; aeaweb 2024 program.
C2 [CONFIRMED] (T2, Brown/Johnson/Kothari/So, 2024 WP, 2016–2022 TAQ+605, $-volume weighted): Off-exchange effective spread ~**1.8 bp** vs on-exchange ~**4.6 bp**; the *additional* off-exchange PI is larger in **wide-spread / low-price / small-cap** names — i.e. concentrated where we do NOT trade; on liquid high-price names the bp saving shrinks. Retail is *less* concentrated at the close than on-exchange flow, so average retail PI is not estimated on our toxic last-15-min window. — travislakejohnson.com WP.
C3 [CONFIRMED] (T2, Adams/Kasten/Kelley, JBF 2024, zero-commission era): NBBO-based PI **overstates true economic savings, in some subsamples by ≥4×**, because NBBO ignores odd-lot/hidden liquidity and exchange effective spreads already sit inside the quote. — sciencedirect S0378426624001432 / ssrn 4403011.
C4 [CONFIRMED] (T2, Schwarz/Barber/Huang/Jorion/Odean, J. Finance 2025, ~85k simultaneous market orders, 6 accounts / 5 brokers, Dec-2021→Jun-2022): Round-trip cost dispersion **7–46 bps for identical trades**; PI 19–47% of NBBO across brokers; **PFOF does not explain** the gap; S&P 500 median quoted spread ~6 bps → residual effective half-spread still ~**1–2 bps even at a good broker**. Odd lots (>60% of trades) sit outside the round-lot NBBO the rule benchmarks. Alpaca not among the best accounts. — doi 10.1111/jofi.13467.
C5 [CONFIRMED] (T2/T3, Ernst, Wharton WIFPR spotlight 2022, randomized-experiment work): Direct exchange orders already execute ~4 bp better than NBBO; subtracting that bias leaves true wholesaler PI of order **1–5 bp**, not 5–9 bp; in the extreme a broker can show ~0 true PI after controls while collecting higher PFOF (NBBO overstatement ~**400%**). — wifpr.wharton.upenn.edu spotlight.
C6 [CONFIRMED] (T1/T3, SEC Best-Ex Proposal Table 5 re-parsed by Lewis/SIFMA, Aug-2024; corroborated by SEC preferencing-study PI rates): Wholesaler marketable mix ~**79% market / 21% marketable-limit**; exchange marketable ~**99.7% marketable-limit**. Marketable-limit orders get PI less often (68.2% vs 53.6% on 100-sh) and are the worse-executed bin — using pooled "marketable" E/Q for a marketable-limit strategy is apples-to-oranges. — sifma.org best-ex blog.
C7 [CONFIRMED] (T3, Robinhood S3-audited, Q1-2026, **1–99 share** market/marketable-limit): **EFQ 28.06%**, net PI **$3.70 per 100 shares**, 96.59% at-or-better-than-NBBO. This is the canonical flattering headline — but it is odd-lot, pooled all-day, all names (not megacap-at-close), and thus overstates our reality. Fidelity Prime (Dec-2025, 100–1,999 sh): 94.3% PI-rate on NASDAQ, 98.5% at/within NBBO (percent-only, no E/Q). — robinhood.com execution-quality; prime.fidelity.com statistics.
C8 [CONFIRMED] (T1, SEC Rule 605 amendments, adopted Mar-6-2024, Fed.Reg. Apr-2024, **compliance Dec-15-2025**): Adds mandatory **E/Q**, multi-horizon realized spreads, **odd-lot & fractional buckets**, replaces share-count with **notional** buckets (aggregated <$200k category), splits **S&P 500 vs all-other**, and benchmarks PI against **best available displayed price (incl. odd-lot liquidity)** — a *tighter* benchmark that will make honest odd-lot E/Q look **worse** than legacy stats. First clean odd-lot/time-relevant numbers arrive only from Dec-2025 compliance reports onward. — sec.gov 34-99679; sidley / natlawreview summaries.
C9 [CONFIRMED] (T1 project + T2 Brown et al.): Project sim shortfall at **15:55:10 = 1.46 bps** vs quoted half-spread **0.73 bps** → implied **E/Q ≈ 2.0** (pay ~full quoted spread or more once mid-drift is included). This is consistent with the U-shape (spreads widest at the close) and with retail PI being estimated off-peak, not in our window. — AGENT_BRIEF charge + Brown/Johnson WP §1 + intraday U-shape literature (SSRN 4792199).
C10 [CONFIRMED, conflicted] (T1/T3, Alpaca 606 filings + IBKR): **Alpaca routes equity flow to Virtu Americas, Citadel Execution Services, Jane Street**; historic PFOF ≈ $0.0020–0.0021/sh from Citadel (2019); **Alpaca publishes NO price-improvement statistics** and concedes 606 averages "tell you nothing about the PI for any given order" — we cannot verify our live broker's quality from disclosure, only by direct audit. IBKR **Pro** SmartRouting claims netted PI ~**$0.02/sh** and explicitly flags that rivals' PI stats "ignore dis-improved/unimproved orders"; SmartRouting is **Pro-only** (Lite routes to wholesalers). — Alpaca 606 + learn article; interactivebrokers.com best-execution.
C11 [UNVERIFIED → UNKNOWN] (T3 industry 2025–2026): Aggregate retail E/Q has **not** been shown to deteriorate 2024–2026 (Fidelity claims E/Q improved to ~41% by 2025; record wholesaler PI dollars into 2026). What remains **UNKNOWN and load-bearing** is E/Q *conditional on liquid Nasdaq + last 15 min + signal-timed side* — no public 605 time-of-day split exists pre-full-rollout. — Fidelity white paper; industry PI reports.

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **PASS (narrow)** | Cost measurement is a fill-economics input, not a sub-5s edge; the audit instant is scheduled/manual. |
| 2 Access | **PASS** | Marketable clips ($400–$3,000) on Alpaca/IBKR are the ordinary retail path; no exotic order type to *measure* E/Q. |
| 3 Session | **PASS** | Last-15-min continuous and pre-15:50 flat are in-mission; the close-cross itself is separate (champion/auction charges). |
| 4 Data | **PASS for SIP shortfall; OPEN-BLOCKED($0) for broker-true E/Q** | Owned SIP ticks measure mid→fill shortfall (done at 15:55:10). True broker-level PI needs Alpaca fill blotter logging ($0) or post-Dec-2025 broker 605 summaries. No real-time SIP, so benchmark = timestamped SIP replay vs our fills. |
| 5 Fill realism | **This IS the probe; FAIL if sim assumes E/Q≪1** | Full half-spread charge is the *optimistic* continuous-taker bound for the toxic close; project shortfall already exceeds it. Crediting average retail PI (E/Q~0.4) for signal-timed liquid flow is the known trap. |
| 6 Statistics | **PASS for measurement** | n≥250 marketable clips over ≥150 sessions is trivial on owned history; power is for *mean E/Q*, not alpha. Close-window tail claims UNDERPOWERED below ~250 close clips. |
| 7 Protocol | **PASS as cost calibration** | Pre-register: "E/Q on liquid Nasdaq $400–$3k marketable, overall and 15:45–15:59, market vs marketable-limit, decision-time mid." Charges a *measurement* family, not a new edge family. |

**Survivor-profile score: 2/5** (as an *edge* claim of sub-half-spread fills; as a *cost prior* it is load-bearing):
1. Single-print/auction execution — **0** (continuous marketable fills).
2. Scheduled decision instant — **1** (measurable at fixed clock times).
3. Named price-insensitive payer — **0 for us** (PI payer is the *uninformed* retail pool; we are not in it on the basis trade).
4. Historically testable cheaply — **1** (SIP shortfall + blotter; ≤$0).
5. Effect ≥ 2× cost burden — **0** (the cost burden *is* the object; "free PI" is not an effect for us).

### Economics sketch
| Line | Value | Notes |
|------|-------|-------|
| Headline broker odd-lot E/Q (flattering) | ~0.28 | Robinhood Q1-2026 EFQ 28.06%, $3.70/100sh — odd-lot, all-day, all-names |
| Optimistic S&P market-order E/Q (good broker) | ~0.40–0.55 | Fidelity ~41% (2025); Dyhrberg S&P ~47% PI → E/Q ~0.53 |
| Full-sample wholesaler E/Q (equal-weight 605) | ~0.76 | Dyhrberg; small-cap-heavy |
| $-vol-weighted off-ex effective (all retail) | ~1.8 bp one-way | Brown et al.; vs 4.6 bp on-ex |
| Liquid S&P residual after ~45% PI | ~1–2 bp half | Schwarz et al., good broker; worst brokers far worse |
| **Project 15:55:10 shortfall (known)** | **1.46 bps** vs **0.73 bps** half | Implied **E/Q ≈ 2.0** at decision window |
| NBBO-overstatement haircut | up to **4×** on "PI dollars" | Adams; Ernst ~400% |
| Marketable-limit vs market penalty | worse (PI-rate 53.6% vs 68.2%) | SEC/Lewis; magnitude in bps UNKNOWN |
| **Skeptic prior — liquid Nasdaq overall** | **E/Q ≈ 0.7–1.0** | Do NOT use 0.28–0.4 |
| **Skeptic prior — last 15 min / signal-timed** | **E/Q ≈ 0.9–2.0** | Full half-spread is *floor*, not ceiling; sim already 2.0 |
| Champion comparison | +2.5 bps/event dev / **+12.5 holdout** | Champion is MOC single-print → pays 0 continuous spread; a continuous M16 taker entry of 0.7–1.5 bps half (or 1.5 bps shortfall) would eat most of a modal +2.5 |

**Predicted net E/Q distribution — $400–$3,000 marketable clips, liquid Nasdaq megacaps (NVDA/TSLA/AMD/MU/GOOGL; note these are odd lots at our size):**
- **Overall / midday:** E/Q ≈ **0.70–1.00** (median ~0.80). Far above the 0.28 odd-lot headline because these names are tick-constrained; effective half-spread ~0.5–0.7 bps on ~0.73 bps quoted.
- **Last 15 min (15:45–16:00):** E/Q ≈ **0.90–2.0** (median ~1.0); effectively "pay the now-wider spread," and worse once mid drifts with NOII. Absolute effective half-spread ~0.8–1.5 bps as the quote itself widens — the range the sim's 1.46 bps already encodes.
- **Confidence MED / partially UNKNOWN** — no public megacap-odd-lot-at-close E/Q exists; the Phase-0 live audit is the correct resolver. Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout**, and the adversarial cost prior says charge **≥ full half-spread (E/Q ≥ 1.0)** for last-15-min liquid marketable, **≥ 1.5 bps** when mid drifts with NOII.

### Proposed next test (OPEN-TESTABLE — Phase-0 cost calibration, not an edge)
**Hypothesis:** On liquid Nasdaq names (NVDA/TSLA/AMD/MU/GOOGL + M11 set), $400–$3,000 marketable clips, decision-time-mid benchmark: overall E/Q ≥ 0.7 and 15:45–15:59 E/Q ≥ 0.9; marketable-limit E/Q ≥ market E/Q; signal-side (with NOII basis) E/Q ≥ uninformed-side E/Q.
**Named payer:** none for alpha — this kills optimistic PI padding used as free alpha.
**Data:** owned SIP ticks (mid, NBBO, condition codes) + Alpaca fill blotter (price, time, order type, size). **$0.** Optional cross-check: post-Dec-2025 broker 605 odd-lot summaries when clean.
**Universe / n / power:** 12-name liquid set × RTH 2024–2026; target n ≥ 500 fills overall, ≥ 150 in last 15 min; per-fill shortfall sd ~few bps → mean E/Q estimable to ±0.05.
**A-priori thresholds:** kill "E/Q ≤ 0.5 last-15" if realized mean (last-15) > 0.7 on n≥150; default "charge full half-spread" if last-15 mean E/Q ∈ [0.9, 1.2]; escalate to "charge ≥ 1.5× half-spread" if mean shortfall/half-spread ≥ 1.3 in 15:50–15:59.
**Promotion / kill:** does NOT promote a trading edge — feeds the fill kernel / M16 economics. Kill the optimistic model only if the blotter shows durable E/Q ≤ 0.5 on liquid last-15 AND odd-lot-aware benchmark ≤ 0.6. If audited close E/Q ≥ 1.0, the minutes-hours taker book is cost-dead at our size → return to auction-only.
**Trial family charged:** cost-model / fill-realism measurement (aligns with §7 trap "fills without ground-truthing"), not a new alpha family.

### Sources
1. **[T2]** Dyhrberg, Shkilko, Werner — *The Retail Execution Quality Landscape* (Dec-2023 WP / JFE 2025). Rule 605 2019–2022; wholesaler E/Q 0.76; ~47% quote PI in S&P 500; benchmark-widening in small names. ssrn 4313095 ; aeaweb.org/conference/2024/program/paper/5Gtsa7ra
2. **[T2]** Brown, Johnson, Kothari, So — *Anatomy of Trading Costs for Retail Investors* (2024 WP). $-vol-weighted off-ex ~1.8 bp vs on-ex ~4.6 bp; PI concentrated in wide-spread/small-cap/low-price; retail less concentrated at close. travislakejohnson.com/pdfs/Brown Johnson Kothari So 2025 (WP).pdf
3. **[T2]** Adams, Kasten, Kelley — *How Free Is Free? Retail Trading Costs with Zero Commissions* (JBF 2024). NBBO PI overstates savings up to 4×. ssrn 4403011 ; sciencedirect S0378426624001432
4. **[T2]** Schwarz, Barber, Huang, Jorion, Odean — *The "Actual Retail Price" of Equity Trades* (J. Finance 2025; sample Dec-2021→Jun-2022). 85k simultaneous orders; 7–46 bps round-trip dispersion; PI 19–47% NBBO; PFOF not main driver; S&P quoted ~6 bps median. doi 10.1111/jofi.13467 ; ssrn 4189239
5. **[T2]** Huang, Jorion, Lee, Schwarz — *Who Is Minding the Store? Order Routing and Competition in Retail Trade Execution* (FEDS 2024-080, Sep-2024). Persistent within-broker wholesaler cost dispersion; imperfect competition. federalreserve.gov FEDS 2024-080
6. **[T2/T3]** Ernst — Wharton WIFPR Research Spotlight on PFOF and price improvement (2022). NBBO overstates PI ~400%; broker PI-vs-PFOF tradeoff. wifpr.wharton.upenn.edu spotlight
7. **[T3, conflicted]** BestEx Research (Mittal/Berkow) — *The Good, the Bad & the Ugly of PFOF* (May-2021). NBBO-benchmark critique; ~25% lit-spread counterfactual. bestexresearch.com
8. **[T1/T3]** Lewis (ex-SEC Chief Economist) via SIFMA — *Rethinking the Economic Analysis in the SEC's Best Execution Proposal* (Aug-2024). Market vs marketable-limit mix 79/21 vs 99.7%; re-weight reverses SEC conclusion. sifma.org best-ex blog
9. **[T1]** SEC Rule 605 amendments, Final Rule 34-99679 (adopted Mar-6-2024; **compliance Dec-15-2025**) — mandatory E/Q, odd-lot/notional buckets, "best available displayed price" benchmark, S&P-500 vs other split. sec.gov/files/rules/final/2024/34-99679.pdf ; sidley.com ; natlawreview.com
10. **[T3]** Robinhood, *Our Execution Quality*, Q1-2026 (S3-audited): 1–99 sh EFQ 28.06%, net PI $3.70/100sh, 96.59% at/better NBBO. robinhood.com/us/en/about-us/our-execution-quality
11. **[T3]** Fidelity Prime, execution-quality statistics, Dec-2025 (100–1,999 sh: NASDAQ 94.3% PI-rate, 98.5% at/within NBBO); Fidelity white paper claims industry E/Q ~41% by 2025 (improvement, not decay). prime.fidelity.com/trade-execution-quality/statistics
12. **[T3]** Interactive Brokers, *Dedicated to Best Price Execution*, Q1-2025 (netted PI ~$0.02/sh; SmartRouting Pro-only; rivals' PI stats ignore dis-/unimproved). interactivebrokers.com/en/trading/smart-routing.php
13. **[T1, conflicted]** Alpaca Form 606 (2019, 2025Q3) + learn/PFOF article — Virtu/Citadel/Jane Street; ~$0.0020/sh Citadel PFOF; no published PI stats; explicit PI-vs-PFOF conflict language. files.alpaca.markets 606 ; alpaca.markets/learn
14. **[T1/T2]** Intraday effective-spread U-shape (widest at open/close; PI thins late) — SSRN 4792199 and predecessors; internalization/adverse-selection arXiv 2212.07827.
15. **[T1 project]** AGENT_BRIEF charge — sims charge full half-spread + 0.5–1 bp slip; shortfall 1.46 vs 0.73 bps half-spread at 15:55:10; champion +2.5 dev / +12.5 holdout.

#### Queries used
- Rule 605 odd-lot effective spread price improvement wholesaler 2024 2025 report
- retail price improvement declining 2024 2025 payment for order flow execution quality deterioration
- effective spread price improvement time of day intraday close final minutes retail orders Boehmer subpenny
- Schwarz "Actual Retail Price" equity trades odd-lot fractional retail pays more true cost findings
- FEDS 2024-080 Federal Reserve retail execution quality effective spread odd lot
- price improvement widens spread volatility adverse selection shrinks retail liquidity marketable limit treated worse wholesaler
- Alpaca 606 order routing disclosure Citadel Virtu payment for order flow price improvement
- IBKR effective spread price improvement per 100 shares vs industry Lite Pro SmartRouting statistics 2024
- Citadel Securities Virtu effective quoted spread ratio E/Q 605 marketable orders 2024 basis points
- effective spread U-shaped intraday wider at open and close price improvement lower final minutes retail wholesaler
- "Who is Minding the Store" order routing competition retail execution Huang Jorion Lee Schwarz broker dispersion
- Rule 605 amendment size categories buckets definition 100-499 500-1999 odd lot fractional order size
- retail effective spread increased 2022 2023 2024 price improvement declined wholesaler tightened after zero commission
- price improvement scales with quoted spread fixed fraction half-spread megacap tight spread minimal subpenny
- marketable limit order less price improvement than market order wholesaler internalization midpoint fill rate retail percentage
