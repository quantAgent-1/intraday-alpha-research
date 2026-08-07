## DR-X3 — modality A (academic) findings
### Verdict recommendation
OPEN-TESTABLE (confidence MED) — Academic Rule 605 / field-experiment literature consistently shows that small marketable retail flow internalized by wholesalers pays substantially less than the full quoted half-spread: typical wholesaler E/Q ≈ 0.5–0.76 overall, with liquid S&P/Nasdaq names closer to ~0.4–0.55 under dollar-volume weighting, and experimental PI of ~19–47% of the NBBO spread depending on broker. BJZZ subpenny identification is systematically incomplete (≈35% recall; 28% sign error) and cannot alone ground last-15-minute cost claims. No clean peer-reviewed study isolates retail price improvement in 15:45–16:00 specifically; TOD evidence is indirect (retail volume tilts away from the tight-spread close; absolute quoted spreads often compress into the close). Predicted E/Q for $400–$3,000 marketable clips on liquid Nasdaq is therefore a literature-calibrated distribution, not a measured one — Phase 0 live micro-order audit is the right next measurement.
What would flip it: a broker-tagged Rule 605 / post-2024 modernization panel (or our own Phase 0 fills) showing E/Q ≥ 0.90 (≈ full half-spread) on 100–499 / odd-lot marketable orders in NVDA/TSLA/AMD/MU/GOOGL in the last 15 minutes would kill the “retail pays far less than sim half-spread” prior and re-validate full-half-spread + slip cost burden.

### Mechanism
Who pays: wholesalers (Citadel, Virtu, G1/Susquehanna, Jane Street, Two Sigma, UBS, etc.) compete for segmented retail flow that is, on average, less toxic than exchange-mixed institutional flow; they internalize marketable retail against their inventory and rebate a portion of the spread as price improvement (and a smaller portion as PFOF to the broker). Why price-insensitive: retail marketable orders are size-small, typically non-informed at the name-microstructure horizon, and routed by brokers under best-execution + PFOF contracts rather than smart-routing for each clip. Why it persists: Reg NMS tick/display rules historically excluded odd lots from NBBO protection and from legacy Rule 605; subpenny internalization is retail-only by construction; broker monitoring of wholesaler E/Q/realized spreads reallocates flow to lower-cost wholesalers (Dyhrberg–Shkilko–Werner). Capacity: for $400–$3k clips, capacity is effectively unlimited at wholesaler scale; size thresholds for internalization failure (walking the book / partial externalization) are far above our notional on liquid Nasdaq. The “payer” for our edge is not this mechanism — this mechanism is the cost baseline that sims currently overstate if they charge full half-spread without PI.

### Claims
C1 [CONFIRMED] (T2, Dec 2023 / JFE 2025, sample Rule 605 Jan 2019–Dec 2022, share-volume then equal-weight stocks): Wholesaler liquidity-demanding orders show effective/quoted spread ratio E/Q = 0.76 vs exchanges 0.97; price improvement 66.1% of shares improved vs 9.0% on exchanges; wholesaler effective spread 53.16 bps, quoted 69.60 bps (gross, no commission). S&P 500 retail PI ≈ 47% of quoted spread (full-sample PI ≈ 24% of quoted = ~12% discount each side). **Hard liquid-name anchors read directly from the paper's tables** — S&P 500 wholesaler orders: share-weighted (Table A1) quoted 8.16 bps / effective 4.36 bps / **E/Q 0.53**, 76.1% improved; **dollar-volume-weighted (Table A5, the best proxy for our high-$-volume megacaps) quoted 3.92 bps / effective 1.87 bps / E/Q 0.48 / price impact 1.42 bps / realized 0.46 bps, 83.2% improved.** (Note quoted spread base for the S&P500 dollar-wtd bucket, 3.92 bps, is still wider than our 5 megacaps' ~1.46 bps quoted at 15:55:10, i.e. our names are even tighter than the S&P500 average.) — Dyhrberg, Shkilko, Werner, “The Retail Execution Quality Landscape,” https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4313095 ; AEA 2024 program PDF (full PDF incl. internet appendix read).

C2 [CONFIRMED] (T2, Jun 2024 WP, sample Rule 605 Apr 2019–May 2022 round lots + TAQ/Robinhood odd lots Aug 2016–Dec 2022): Dollar-volume-weighted off-exchange retail PI ≈ 53% of the half-spread for round lots (on-exchange ≈ −19%); off-exchange effective spreads ≈ 1.8 bp vs on-exchange ≈ 4.6 bp (round lots); Robinhood effective ≈ 2.0 bp with near-zero price impact. Zero-commission PFOF model yields total retail costs “below 6 bp.” — Brown, Johnson, Kothari, So, “Anatomy of Trading Costs for Retail Investors,” https://www.travislakejohnson.com/pdfs/Brown%20Johnson%20Kothari%20So%202025%20(WP).pdf

C3 [CONFIRMED] (T2, JoF Jul 2025 / experiment Dec 2021–Jun 2022, n≈85,000 parallel market orders, main size ~$100, robustness $1k/$5k): Mean PI as % of NBBO full spread: TD Ameritrade 47.2% (7.84¢/sh), Fidelity 35.8%, E*Trade 36.1%, Robinhood 26.8%, IBKR Lite 19.5%, IBKR Pro 18.8%. Round-trip costs ex-commission 7.2–46.2 bp across brokers. Wholesalers systematically give different prices to different brokers for identical simultaneous orders; PFOF ($0.001–0.003/sh) is an order of magnitude too small to explain PI dispersion. — Schwarz, Barber, Huang, Jorion, Odean, “The ‘Actual Retail Price’ of Equity Trades,” https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467 ; CQA slides https://cqa.org/wp-content/uploads/2024/04/Huang_Actual-Retail-Price_CQA.pdf

C4 [CONFIRMED] (T2, JoF 2024, experiment Dec 2021–Jun 2022, same 85k trades): BJZZ (Boehmer–Jones–Zhang–Zhang 2021) subpenny TRF algorithm identifies only ≈35% of true retail trades as retail (false negatives dominate; higher recall when spread ≤5¢), incorrectly signs ≈28% of identified trades, and produces uninformative order-imbalance signals for ≈30% of stocks. Midpoint-signing of subpenny prints improves sign accuracy. — Barber, Huang, Jorion, Odean, Schwarz, “A (Sub)penny for Your Thoughts,” Journal of Finance 79(4), 2024, https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4202874

C5 [CONFIRMED] (T2, Boehmer et al. JoF 2021, sample ~2010–2015 TAQ): Foundational method: off-exchange (TRF code D) prints with subpenny prices in (0,0.4) and (0.6,1.0) fractions identify marketable retail buys/sells; institutional flow generally cannot receive subpenny PI. Effective spreads, 1-min price impacts, realized spreads computed for identified retail; method underpins subsequent PI literature but is incomplete post-zero-commission era (see C4). — Boehmer, Jones, Zhang, Zhang, “Tracking Retail Investor Activity,” JoF 76(5) 2021.

C6 [PLAUSIBLE] (T2, Brown et al. 2024 + Dyhrberg et al. 2023): Time-of-day: retail (esp. odd-lot / RH) volume is less concentrated at the close — when quoted spreads are tightest — than on-exchange institutional volume; this raises average quoted spreads facing retail relative to exchange averages, but E/Q remains lower off-exchange even for odd lots. Absolute effective spreads for odd-lot retail can appear slightly higher off-exchange purely from timing, not from worse improvement rates. No paper in the 2021–2026 set reports BJZZ- or experiment-based PI by clock minute in 15:45–16:00. — Brown et al. §5.1 / Figure 2; Dyhrberg sample excludes auctions by Rule 605 design (RTH covered orders only).

C6b [PLAUSIBLE] (T2, Bogousslavsky & Muravyev, JFM 2023, sample ~2010–2018; close magnitudes abstract/secondary-only): Liquidity worsens materially into the bell — market-wide effective spread rises ≈**+10 bps** and displayed depth falls ≈**−63%** at the close; closing-auction volume ≈7.5% of daily volume. Market-wide (small/mid-dominated), so megacap widening is smaller, but this establishes 15:45–16:00 as a *wider-quoted-spread* window → the E/Q *ratio* may hold or even improve (%-wise, wider spread = more sub-penny room) while *absolute* bps cost rises. This is the single biggest reason the last-15-min E/Q slice cannot be assumed equal to all-day and must be measured in Phase 0. — Bogousslavsky & Muravyev, “Who Trades at the Close?” SSRN 3485840.

C7 [PLAUSIBLE] (T2/T3, SEC/industry + Citadel 2023 comment on Best Execution Proposal): Industry/SEC summaries state wholesale broker-dealers fill >44% of retail marketable shares at midpoint or better; retail on average pays ≈45% of the quoted half-spread (E/Q ≈ 0.45) under that framing; aggregate Rule 605 PI savings ≈$3B in 2022. Post-2024 Rule 605 modernization adds explicit E/Q, odd-lot/fractional buckets, and broker coverage — compliance date extended (reports begin ~Aug 2026 per Citadel 605 page) so 2024–2026 modernized odd-lot E/Q panels are not yet in the academic record. — Citadel Securities response to Best Execution Proposal; Katten / Federal Register Rule 605 Amendments Mar 6, 2024.

C8 [UNVERIFIED] (gap): Broker-specific (Alpaca 606; IBKR Lite vs Pro SmartRouting) marketable improvement for $400–$3k liquid-Nasdaq clips is not in the peer-reviewed sample. Schwarz ranks IBKR Lite/Pro worst PI among six brokers on ~$100 clips (C3); Alpaca is absent from all academic field experiments. Rule 606 aggregates do not break execution quality by broker–wholesaler pair at the stock level (pre-modernization).

C9 [PLAUSIBLE] (T2, mechanics synthesis): Market vs marketable-limit: Rule 605 and experiments treat both as liquidity-demanding; marketable limits can improve fill control but reduce midpoint-capture vs pure market. Midpoint fill frequency: industry claims 44–50%+ of retail marketable at midpoint or better (C7); experimental CDFs (Schwarz) show large mass at 50% PI (midpoint) for best brokers. Size thresholds: legacy Rule 605 covered 100–9,999 shares; odd lots (~6% of retail share volume per Battalio–Jennings back-out, but ~40–80% of retail trade counts) were excluded until modernization. Internalization of our $400–$3k clips is the default path; book-walk risk is negligible on liquid Nasdaq.

C10 [CONFIRMED] (T2, Battalio–Jennings–Saglam–Wu / Battalio–Jennings 2022–2023 WPs): Independent critique of BJZZ: substantial false negatives (retail without subpenny PI, midpoint fills) and false positives (some non-retail TRF subpennies); proprietary wholesaler order data needed for ground truth. Reinforces that any TOD study using only BJZZ will miss a large share of retail, especially high-PI midpoint prints. — https://microstructure.exchange/papers/BoehmerJonesAlgorithmPaper20221125.pdf ; Battalio–Jennings “Absolute and Relative Wholesaler Execution Quality in May 2022.”

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | PASS | Cost measurement is passive; manual 5–25 s does not change the fill economics of a marketable clip once sent. |
| 2 Access | PASS | Executable at $1k–$10k via Alpaca (zero commission through 2026-12-31) or IBKR Lite/Pro; order types are plain market / marketable limit. |
| 3 Session | PASS / N-A | Continuous RTH marketable fills; flat-by-15:50 / MOC is orthogonal — this charge is the cost of the continuous entry leg, including last-15-min entries. |
| 4 Data | PASS | Phase 0 live micro-order audit uses owned Alpaca + SIP history; Rule 605 public free; no >$100 data needed for academic prior. |
| 5 Fill realism | PASS (as cost prior) | Grounded in Rule 605 actual fills + controlled field experiments, not tape phantoms; maker assumptions not required. |
| 6 Statistics | PASS | Phase 0 can accumulate n≫250 micro-orders across ≥150 sessions; literature already n in millions of orders. |
| 7 Protocol | PASS | Named mechanism (wholesaler PI on segmented retail) pre-statable; cost-recalibration trial family, not a new edge claim. |

Survivor-profile score: **3/5**
1. Single-print/auction execution → 0 (continuous-market fills; PI is real but multi-venue)
2. Scheduled decision instant → 1 (cost is state, not a reaction race)
3. Named price-insensitive payer → 1 (wholesaler competition for uninformed retail is the mechanism)
4. Historically testable on owned / ≤$100 data → 1 (Rule 605 + own fills)
5. Expected effect ≥ 2× cost burden → 0 (this is a cost recalibration, not an edge; if E/Q~0.5 then continuous-leg cost halves vs full half-spread sims — material for M16 re-pricing, not a 2× edge by itself)

### Economics sketch
**Gross (literature, one-way, marketable retail):**
- Quoted half-spread on liquid megacaps at late day (project known): median ≈ 0.73 bps (5 megacaps @ 15:55:10).
- Wholesaler E/Q: full-sample Rule 605 equal-weight ≈ **0.76** (Dyhrberg); S&P 500 and dollar-volume-weighted estimates imply **≈0.45–0.55** effective/quoted for liquid names (Dyhrberg S&P PI 47% of quoted spread; Brown volume-weighted PI ≈53% of half-spread → E/Q ≈ 0.47; Citadel framing ≈0.45 of half-spread).
- Field experiment PI(% of full NBBO): best broker ~47% (≈ E/Q ~0.06 if mapped 1−2·PI_frac), worst (IBKR Pro) ~19% (≈ E/Q ~0.62). Mapping: one-way effective half-spread / quoted half-spread = E/Q.

**Our cost burden structure:**
- Sims currently charge full half-spread + 0.5–1 bp slip → historical entry-shortfall median 1.46 bps ≈ 2× quoted half-spread 0.73 bps.
- Under academic prior for PFOF retail on liquid Nasdaq small clips: expect to pay roughly **0.4–0.7 × quoted half-spread** one-way (plus residual slip/latency), not 1.0 × half-spread, **if** Alpaca routing resembles mid-tier PFOF brokers rather than IBKR Pro.
- IBKR Pro (no PFOF, SmartRouting) experimentally worst PI → closer to 0.6–0.8 × half-spread; still better than full half-spread on average.
- Last 15 minutes: absolute quoted spreads often tight; retail PI rate not shown to collapse; residual risk is higher adverse selection into the close / auction window — **directionally modest E/Q degradation, not elimination of PI**.

**Net prior vs champion:**
- Cost recalibration only: if true one-way entry cost ≈ 0.4–0.6 bps instead of 1.46 bps on liquid names, continuous-market candidates gain ~0.8–1.0 bps/event of headroom — still short of champion +2.5 bps/event dev / +12.5 holdout unless paired with a real payer.
- Does **not** resurrect maker/passive or sub-15-min edges killed under v1.4 fills; it only says sim full-half-spread is a conservative upper bound for small retail taker clips.

**Predicted E/Q ratio distribution for $400–$3,000 marketable clips on liquid Nasdaq (literature prior, not measured):**

| Window | Central | Plausible range | Notes |
|--------|---------|-----------------|-------|
| Overall RTH | **0.50** | 0.35–0.70 | Volume-weighted liquid-name Rule 605 + mid-tier PFOF broker experiment; IBKR Pro toward upper end |
| Last 15 min (15:45–16:00) | **0.55** | 0.40–0.80 | Directional: PI survives but adverse-selection / auction-adjacent toxicity may lift E/Q; **no direct BJZZ/experiment clock-slice → treat as UNKNOWN with mild upward bias vs RTH** |
| Best-case (high-PI broker, 1¢ tick, midpoint-heavy) | **0.20–0.40** | — | TD/Fidelity-class experimental mass at midpoint |
| Worst-case (IBKR Pro-like / toxic moment) | **0.70–1.0** | — | Near-NBBO fills; rare adverse walk |

Units: E/Q = average effective spread / average quoted spread at order receipt (Rule 605 definition); one-way cost in bps ≈ E/Q × quoted_half_spread_bps. Commission = 0 through 2026-12-31 (Alpaca); post-promo stress is additive, not in E/Q.

### Proposed next test (OPEN-TESTABLE)
- **Hypothesis:** For marketable market/marketable-limit orders of $400–$3,000 notional in NVDA/TSLA/AMD/MU/GOOGL (and 12-name bar universe), realized E/Q under Alpaca routing is in [0.35, 0.70] overall and does not exceed 0.80 in 15:45–16:00, i.e., true one-way entry shortfall is closer to 0.5–0.8 bps than the sim 1.46 bps median.
- **Named payer/mechanism:** Wholesaler internalization PI on uninformed small retail (status-quo market structure), measured not assumed.
- **Data needed:** Owned — Alpaca live fills + historical SIP NBBO at send/receipt timestamps (already entitled); optional free Rule 605 monthly files for wholesaler benchmarks. $0 incremental.
- **Universe:** 5 megacaps + optional 12-name set; RTH only.
- **Expected n & power:** Phase 0 micro-order audit target n ≥ 250 orders across ≥ 150 sessions; noise ~20 bps/event is for *alpha* events — for *cost* measurement, per-order shortfall sd is much smaller (sub-bp to few bp on tight names); n=100 already informative for mean E/Q.
- **A-priori thresholds:** Mean E/Q < 0.70 → adopt reduced cost burden for M16 re-pricing; mean E/Q ∈ [0.70, 0.90] → partial credit (keep half-spread stress); mean E/Q ≥ 0.90 or systematic last-15-min E/Q ≥ 1.0 → retain full half-spread + slip.
- **Promotion rule:** If Phase 0 confirms E/Q ≤ 0.70 overall and ≤ 0.80 last-15, re-price continuous-entry candidates and re-run holdout-style economics with audited fills; does not alone promote any continuous edge.
- **Kill criteria:** Alpaca fills systematically at or outside NBBO (E/Q ≥ 0.95) on liquid names; or last-15-min degradation to E/Q ≥ 1.0 with material frequency.
- **Trial family charged:** M16 Phase 0 cost-audit / fill-kernel recalibration (not a new alpha family).

### Sources
1. [T2] Dyhrberg, A.H., Shkilko, A., Werner, I.M. (2023 WP / JFE 2025). “The Retail Execution Quality Landscape.” Sample: Rule 605 Jan 2019–Dec 2022. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4313095 ; https://www.aeaweb.org/conference/2024/program/paper/5Gtsa7ra
2. [T2] Brown, T.K., Johnson, T.L., Kothari, S.P., So, E.C. (Jun 2024 WP). “Anatomy of Trading Costs for Retail Investors.” Sample: Rule 605 04/2019–05/2022; RH 08/2016–12/2022. https://www.travislakejohnson.com/pdfs/Brown%20Johnson%20Kothari%20So%202025%20(WP).pdf
3. [T2] Schwarz, C., Barber, B., Huang, X., Jorion, P., Odean, T. (JoF Jul 2025; experiment 12/2021–06/2022). “The ‘Actual Retail Price’ of Equity Trades.” https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467 ; CQA slides https://cqa.org/wp-content/uploads/2024/04/Huang_Actual-Retail-Price_CQA.pdf
4. [T2] Barber, B., Huang, X., Jorion, P., Odean, T., Schwarz, C. (JoF 2024). “A (Sub)penny for Your Thoughts: Tracking Retail Investor Activity in TAQ.” https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4202874
5. [T2] Boehmer, E., Jones, C.M., Zhang, X., Zhang, X. (JoF 2021). “Tracking Retail Investor Activity.” https://onlinelibrary.wiley.com/doi/10.1111/jofi.13033
6. [T2] Battalio, R., Jennings, R. (and Saglam, Wu). Critiques of BJZZ / wholesaler execution quality WPs 2022–2023. https://microstructure.exchange/papers/BoehmerJonesAlgorithmPaper20221125.pdf
7. [T2] Adams, S., Kasten, C., Kelley, E.K. (2023/2024 JBF). “How free is free? Retail trading costs with zero commissions.” (BJZZ-based PI ~3.1 bp incremental vs exchange; equal-weight.)
8. [T1] SEC Rule 605 Amendments (Mar 6, 2024; FR Apr 15, 2024): E/Q metric, odd-lot/fractional buckets, broker coverage. Katten summary: https://quickreads.ext.katten.com/post/102j23y/the-effective-spread-of-order-execution-quality-reporting
9. [T3] Citadel Securities (2023). Response to Best Execution Proposal — 44% midpoint-or-better; ~45% of half-spread paid; ~$3B PI 2022. https://www.citadelsecurities.com/wp-content/uploads/sites/2/2023/03/Citadel-Securities-Response-to-the-Best-Execution-Proposal-Final.pdf
10. [T3] Charles Schwab (2022). “U.S. Equity Market Structure: Order Routing Practices…” E/Q trend; midpoint ≥50% claims. https://content.schwab.com/web/retail/public/about-schwab/Schwab-2022-order-routing-whitepaper.pdf
11. [T2] Ernst, T., Spatt, C. (2022 NBER w29883). “Payment for Order Flow and Asset Choice.” Equity subpenny PI ~0.5 bp/trade; PFOF small in stocks. https://www.nber.org/system/files/working_papers/w29883/w29883.pdf
12. [T1] Citadel Securities Rule 605 page — modernized 605 compliance note (reports under Mar 2024 amendments begin Aug 2026). https://www.citadelsecurities.com/rule-605-606-statements/
13. [T2] Bogousslavsky, V., Muravyev, D. (JFM 2023, sample ~2010–2018). “Who Trades at the Close? Implications for Price Discovery and Liquidity.” Close eff-spread/depth figures abstract-only. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840
14. [T2] Jones, C.M., Lipson, M.L. (2005 WP, NYSE SuperDOT Nov 2002 — DECAY-UNKNOWN/historical). “Are Retail Orders Different?” Retail effective spread 2.60¢ full sample, 1.69¢ for 100–499-share orders (vs 2.57¢ institutional); retail advantage far larger for market (1.20¢) than marketable-limit (0.30¢) orders; intraday spreads U-shaped, higher near close. Full PDF read; historical context for the durable market-vs-marketable-limit structural point. https://www.darden.virginia.edu/sites/default/files/inline-files/Retail_2005_WP.pdf

#### Queries used
- BJZZ retail identification subpenny trades price improvement 2021 2022 2023
- Battalio Jennings Zheng Zhang retail order identification subpenny method
- retail price improvement effective spread odd lots Rule 605 2023 2024 2025 academic
- time of day retail price improvement closing minutes BJZZ execution quality
- Boehmer Jones Zhang Zhang 2021 Tracking Retail Investor Activity price improvement effective spread
- Schwarz Barber Huang Jorion "actual retail price" execution quality price improvement cents per share
- Dyhrberg Shkilko Werner 2023 retail trading off-exchange price improvement
- Adams Kasten Kelley 2023 retail execution quality wholesalers
- intraday pattern effective spreads retail trading last 15 minutes closing auction time-of-day execution costs
- Ernst Spatt 2022 payment for order flow price improvement retail E/Q
- Rule 605 E/Q ratio wholesalers marketable orders 100-499 odd lot effective over quoted spread
- retail price improvement time of day last hour close midpoint fill frequency wholesaler
- Barber Huang Jorion Odean Schwarz subpenny algorithm 35% false positive 2024 Journal of Finance
- "last 15 minutes" OR "closing minutes" OR "15:45" retail effective spread price improvement BJZZ OR subpenny
