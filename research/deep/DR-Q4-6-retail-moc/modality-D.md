## DR-Q4-6 — D adversarial findings
### Verdict recommendation
**NOT-VIABLE-STRUCTURAL** (confidence **HIGH**) — Retail cannot capture the champion closing-basis edge under §1 constraints. The load-bearing near-price signal only exists from ~15:55:00 ET, after (i) Alpaca CLS hard-reject at 15:50, (ii) Fidelity on-close hard-stop at 15:40 with explicit “Nasdaq does not accept on the close,” (iii) Nasdaq MOC hard-stop at 15:55, and (iv) EOII deliberately excluding near/far until full NOII at 15:55. Continuous-taker entry at 15:55:10 with auction exit therefore cannot be staged with retail order types; continuous-only exit reintroduces half-spread + adverse selection that plausibly consumes the +2.5–12.5 bps gross. Economic capacity is zero even at $10k once realistic fills replace the sim’s cheap-taker assumption.

What would flip it: A live retail path that (a) receives real-time NOII near/far by 15:55:00, (b) can place Nasdaq late LOC (or equivalent) after continuous entry through 15:58 without re-price kill, and (c) shows net ≥ half-spread after honest continuous fills on ≥50 forward sessions — none of which holds on Alpaca today.

### Mechanism
**Who pays (champion story):** Index/ETF MOC and rebalance flow is price-insensitive; NOII near vs continuous mid creates a temporary basis that continuous mid is expected to close into the auction print.

**Why retail still loses (adversarial):** The residual “basis” is the public race among everyone with TotalView/NOII after 15:55. Institutional MOC is already locked by 15:50–15:55; the continuous book from 15:55–16:00 is where informed imbalance reaction, ETF arb completion, and prop thrashing concentrate (~7% of daily volume in the last five minutes alone). A 5–25 s manual taker joins that queue *with* the informed side and is adversely selected on entry; auction exit requires order types the retail stack either rejects or re-prices away from the true near. No coherent retail-accessible payer remains once cutoffs and fill costs are applied — the payer exists, but the capture instrument does not for §1.

**Capacity intuition:** Market impact capacity at $10k is irrelevant (tiny vs auction ADV). Economic capacity is zero: net bps after half-spread + latency slippage ≤ 0 on the modal event; holdout +12.5 is concentration-driven (MU) and assumes free continuous entry + perfect auction exit.

### Claims
C1 [CONFIRMED] (T1, current docs, mechanics ongoing): Alpaca rejects all CLS (MOC/LOC) submitted after 15:50 ET and before 19:00 ET — five minutes *before* the champion signal and coarser than the Nasdaq MOC cutoff — so the project’s primary retail broker cannot place any on-close order after the near price exists. — https://docs.alpaca.markets/us/docs/orders-at-alpaca

C2 [CONFIRMED] (T1, Nasdaq Closing Cross FAQ / Rule 4754, ongoing): Nasdaq timeline: EOII from 15:50 (every 10s); MOC/LOC cannot be canceled/modified after 15:50; MOC entry stops at 15:55; Late LOC until 15:58 only, re-priced to the more aggressive of the 15:50 and 15:55 reference prices if more aggressive than those refs; full NOII (with near/far) every second from 15:55. — https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf ; Fed. Reg. EOII/NOII description https://www.federalregister.gov/documents/2022/02/24/2022-03876/...

C3 [CONFIRMED] (T1, SEC/Nasdaq rule text, 2019–2022 filings): EOII deliberately **excludes** indicative near/far clearing prices; near/far appear only in the post-15:55 NOII — so pre-15:50 LOC/MOC cannot condition on the true near signal that the champion uses. — Nasdaq SR / Fed. Reg. language: “early release of the NOII should exclude indicative prices, including Near and Far Clearing Prices.”

C4 [CONFIRMED] (T1, Fidelity help, current): Fidelity on-close: minimum 100 shares, must be placed before **15:40 ET**; explicit statement “Nasdaq does not accept on the close orders” (Fidelity routing path) — champion Nasdaq names cannot use Fidelity MOC/LOC for auction exit at all under that help text. — https://www.fidelity.com/webcontent/ap002390-mlo-content/19.09/help/learn_order_types_conditions.shtml

C5 [CONFIRMED] (T1, IBKR Campus, current): IBKR supports MOC/LOC and cites exchange cutoffs (Nasdaq MOC 15:55 / LOC 15:58; NYSE 15:50) — the only major retail path that *might* reach late LOC — but still cannot cancel after exchange locks, and Smart routing is not exchange-guaranteed for late auction eligibility. — https://www.interactivebrokers.com/campus/trading-lessons/ibkr-desktop-market-on-close-order/ ; LOC lesson cites 15:58.

C6 [CONFIRMED] (T1, Alpaca Support Nov 2022): Actively targeting open/close auction as primary method is an explicit non-retail flag criterion; flagged accounts lose commission-free status (forum reports ~$0.004/share) — stress annotation that turns a thin bps edge negative at $10k. — https://alpaca.markets/support/what-flags-an-account-as-non-retail-and-what-are-the-implications-of-being-flagged

C7 [PLAUSIBLE] (T2, Bogousslavsky & Muravyev 2021/2023, sample US stocks 2010–2018): Mean absolute auction vs 16:00 mid deviation ≈ **8.1 bps** (half-spread ≈ 7.6 bps); closing price matches pre-close bid or ask in **68.5%** of auctions; deviations reverse almost fully overnight — continuous market already prices most of the auction, leaving little uncontested basis for a post-15:55 retail taker. — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840 ; published J. Financial Markets 2023

C8 [PLAUSIBLE] (T2, Bogousslavsky & Muravyev; volume shares 2018): Last five minutes (15:55–16:00 continuous) ≈ **7.0%** of daily volume and auction ≈ **7.5%** (up from ~3% in 2010); volume migrates *into* the last five minutes and the auction — crowded thrashing zone for imbalance reaction and ETF completion, not a quiet retail niche. — same source, sample 2010–2018

C9 [PLAUSIBLE] (T2, Jegadeesh & Wu JFE 2022, US auctions): Temporary component of closing-auction price impact ~85% (Nasdaq) / ~62% (NYSE) reverses over 3–5 days; published strategies that trade impact/reversals are “significantly profitable” for institutions — prior-art crowding / decay risk for any public-imbalance close arb; **DECAY-UNKNOWN** post-publication for retail-scale continuous basis. — JFE 2022 abstract/IDEAS

C10 [CONFIRMED] (T1 project + vendor economics, AGENT_BRIEF): Real-time Nasdaq NOII ≈ **$199/mo** (not purchased); historical NOII owned shows near/far = 0 until ~15:55:00 across 2020–2026 — live champion signal is data-blocked without recurring spend the user has not approved, and even with data the order-type stack fails (C1–C5).

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **FAIL** | Decision needs true near at 15:55:00+; 5–25 s manual is fine *if* order types work, but continuous toxic window + auction locks make latency a cost (mid moves toward near while human keys). |
| 2 Access | **FAIL** | Alpaca CLS hard-reject after 15:50; Fidelity no Nasdaq on-close / 15:40 cutoff; late LOC not available on primary broker; real-time NOII not owned. |
| 3 Session | **PASS (narrow)** | Auction flat-at-close is in-mission *if* MOC/LOC actually reaches the cross — which retail stack mostly prevents. |
| 4 Data | **FAIL / OPEN-BLOCKED** | Live near requires real-time NOII ~$199/mo (not purchased); history already shows near absent pre-15:55. |
| 5 Fill realism | **FAIL** | Sim assumes cheap continuous taker + single-print auction exit; retail cannot stage auction exit after 15:55:10 continuous entry on Alpaca; continuous exit reintroduces ambiguous half-spread. |
| 6 Statistics | **N-A** | Structural kill precedes power; holdout n=140 already spent and concentration-caveated. |
| 7 Protocol | **FAIL** | Cannot pre-register an executable retail rule that uses true near *and* retail order types without inventing a broker path that does not exist. |

**Survivor-profile score: 1/5**
1. Single-print/auction execution — **0** (auction exit not reachable after signal for retail)
2. Scheduled decision instant — **1** (15:55:10 is scheduled; latency pre-positionable in principle)
3. Named price-insensitive payer — **0 for retail capture** (payer real; capture path blocked)
4. Historically testable cheaply — **0 for live path** (history tests the *signal*, not retail *execution*)
5. Expected effect ≥ 2× cost burden at size — **0** (half-spread + adverse selection ≥ modal +2.5 bps)

### Economics sketch
| Line | Gross | Notes |
|------|-------|-------|
| Champion (sim) | +2.5 bps/event dev / **+12.5 bps holdout** | Assumes cheap continuous taker entry + perfect auction exit |
| Auction | mid gap (field) | ~8.1 bps mean abs; often ≤ half-spread (B&M) |
| Continuous one-way half-spread (liquid mega) | ~1–5 bps | Name-dependent; round-trip continuous 2–10 bps |
| Adverse selection / latency (15:55 toxic window) | **UNKNOWN, sign negative** | Joining informed flow after public NOII; mid converges toward near |
| Alpaca non-retail stress | ~4 mills/share | If auction-primary flag trips |
| Real-time NOII | $199/mo | Fixed cost vs $10k notional |
| **Retail net prior (adversarial)** | **≤ 0 to modestly negative bps/event** | Cheap-taker sim is the optimistic bound; structural blockers bind first |

Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout** is not a deployable retail net; it is an upper bound conditional on order types and fills the retail stack does not provide.

### Proposed next test (only if OPEN-TESTABLE)
*None — structural.* Optional **instrument-only** measurement (does not promote to deploy): on IBKR paper/live, log whether late LOC (15:55–15:58) is accepted for Nasdaq names after a continuous entry, and measure continuous mid→close residual after 15:55:10 on owned NOII history with half-spread costs. Kill if residual net ≤ 0 after half-spread on holdout-style sample. Does **not** charge a trial family for deployment until Access gate flips.

### Sources
1. **[T1]** Alpaca Docs — Placing Orders / Time in Force CLS reject after 3:50pm ET. https://docs.alpaca.markets/us/docs/orders-at-alpaca (crawled 2026-07)
2. **[T1]** Nasdaq Closing Cross FAQ — MOC 15:55 / LOC 15:58 / no cancel after 15:50 / late LOC re-price. https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf
3. **[T1]** Nasdaq Opening & Closing Crosses FAQ — MOC prior 3:55; Late LOC re-price to 15:50/15:55 refs. https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf
4. **[T1]** Federal Register / Nasdaq Rule 4754 — EOII 15:50 every 10s; NOII 15:55 every 1s; Late LOC handling. https://www.federalregister.gov/documents/2022/02/24/2022-03876/...
5. **[T1]** Nasdaq / SEC filings — EOII excludes Near and Far Clearing Prices by design.
6. **[T1]** Fidelity Help — On the close before 3:40pm ET; min 100 sh; “Nasdaq does not accept on the close orders.” https://www.fidelity.com/webcontent/ap002390-mlo-content/19.09/help/learn_order_types_conditions.shtml
7. **[T1]** IBKR Campus — MOC/LOC lessons; Nasdaq MOC 15:55, LOC 15:58. https://www.interactivebrokers.com/campus/trading-lessons/ibkr-desktop-market-on-close-order/
8. **[T1]** Alpaca Support (Nov 2022) — Non-retail flag includes open/close auction as primary method. https://alpaca.markets/support/what-flags-an-account-as-non-retail-and-what-are-the-implications-of-being-flagged
9. **[T2]** Bogousslavsky & Muravyev (2021 WP / 2023 JFM) — Who Trades at the Close; 8.1 bps mean abs auction deviation; 68.5% match bid/ask; last-5-min & auction volume shares; overnight reversal. SSRN 3485840
10. **[T2]** Jegadeesh & Wu (JFE 2022) — Closing auctions Nasdaq vs NYSE; impact reversal 3–5d; profitable institutional strategies on impact/reversal.
11. **[T3]** NBIM Asset Manager Perspectives (2020) — Closing imbalances usable for liquidity arb; opportunistic delay until just before cross. https://www.nbim.no/contentassets/.../asset-manager-perspectives-the-role-of-closing-auctions...
12. **[T3/T4]** Alpaca forum — LOC non-fill, paper CLS mispricing, commission when auction-heavy (hypothesis only for economics magnitude).
13. **[T1 project]** AGENT_BRIEF — near/far 0 until ~15:55; RT NOII ~$199/mo not purchased; champion +2.5/+12.5; holdout concentration.

#### Queries used
- Nasdaq closing cross MOC LOC order cutoff times 15:50 15:55
- Alpaca trading MOC LOC market on close order support retail
- retail broker MOC LOC availability Interactive Brokers Schwab Fidelity cutoffs
- closing auction arbitrage crowding decay adverse selection NOII
- Nasdaq NOII near far price dissemination 15:50 15:55 Early Order Imbalance Indicator
- "closing auction" arbitrage "adverse selection" continuous market last 5 minutes
- Schwab Fidelity market on close MOC order cutoff retail
- Bogousslavsky Muravyev who trades at the close price discovery auction inefficiency
- Nasdaq Late LOC after 3:55 retail broker availability
- closing auction basis trade continuous market convergence adverse selection last 5 minutes
- Fidelity MOC market on close order deadline 3:40 cutoff
- closing auction price deviation reversion overnight Jegadeesh Wu 2022
- effective spread last 5 minutes trading day equity market toxic flow adverse selection close
- Alpaca CLS order 3:50 reject late LOC MOC routing primary exchange
- site:nasdaqtrader.com Closing Cross FAQ MOC LOC cutoff 3:50 3:55
- Wu Jegadeesh closing auction trading strategy profitable reversal bps
- Databento Nasdaq NOII near price zero until 15:55 EOII excludes indicative
- Interactive Brokers LOC limit on close late order cutoff 3:58 Nasdaq
