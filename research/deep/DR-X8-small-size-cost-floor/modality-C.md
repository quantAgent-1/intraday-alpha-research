## DR-X8 — modality C (practitioner/vendor) findings

### Verdict recommendation
**NOT-VIABLE-STRUCTURAL** (confidence HIGH) — Maker-first intraday cannot rescue fee-boundary
embers (M18's NVDA/MU streams) at our size, and the reason is not the explicit fee floor. The
explicit all-in floor is already trivial at both accessible brokers (~$0 at Alpaca, ~$0.0005–
0.0015/sh net at IBKR-Pro-tiered), i.e. well below the M18 ~$0.0090/sh ($1.27/side @ 141 sh)
sign-flip line on paper. But the binding cost of a resting-limit program is **adverse selection
on the fills you actually get plus the winners you miss** — a cost that appears in no fee
schedule and that every practitioner source rates as *dominant* over the fraction-of-a-cent
rebate. Because M18's "+$1.79 gross at mid" already credits the half-spread you would earn by
posting, switching to maker does not add that spread again; it merely converts a *known* taker
cost into a *worse, unknown, adversely-selected* fill-quality cost. Maker economics are also on
§1's structural-exclusion list ("maker rebates, queue position, continuous quote management →
OUT"). The constructive output is the cost table below: **keep costing every future intraday
registration at the taker floor (~$0.005/sh/side + slip); never model a net maker credit.**

**What would flip it:** an audited, condition-code-ground-truthed *retail* fill log on
NVDA-class names at 60–210 sh clips showing ≥85% touch-fill with near-zero filled-return
correlation (fills not concentrated on adverse moves) — AND a broker passing a *net* stock maker
credit at the zero-volume tier. Neither exists in the practitioner record; the evidence points
the opposite way.

### Mechanism
Who would pay us in a maker-first structure? The taker who crosses the spread to hit our resting
limit. But that counterparty crosses to us *disproportionately when informed* — the canonical
adverse-selection problem. So there is **no coherent price-insensitive payer** for a retail
resting-limit program on liquid megacaps: the flow that fills us is precisely the flow that is
about to move against us. The maker *rebate* (a genuine price-insensitive payment from the
exchange) is the only clean payer here, and it is (a) not passed to the client at Alpaca and (b)
smaller than IBKR's per-share stock commission, so it never nets to a credit at our scale. This
is the inverse of the champion, whose payer (indexed MOC/rebalance flow into a single-print
auction) is price-insensitive *and* reaches us without an adverse-selection filter.

### Claims
C1 [CONFIRMED] (T3 vendor/practitioner, 2025–2026, no dated sample): **Adverse selection
dominates the rebate at retail scale** — "a fill that loses 2 cents of inventory is not saved by
a fraction-of-a-cent rebate"; adverse selection "can vaporize months of rebate income"; the
rebate is "gravy, not the meal." For passive orders deep in queue "the expected fill rate drops
and most fills occur only when price moves against the order." This is the decisive practitioner
consensus. — axon.trade "Fees, Rebates & Maker/Taker Math" (2025-09-25); mlquants Substack;
Nasdaq "Quantifying the Cost of Maker-Taker Markets" (2020-10-08).

C2 [CONFIRMED] (T3, Rob Carver / ex-AHL, 2014-10-24): A named systematic practitioner running a
*passive-first* execution algo on **liquid futures** measured a passive fill rate of **≈2/3
(~67%)**, not 90–98%, over a resting window of up to 5 min before turning aggressive; this cut
execution cost ~80% vs market orders (paying ≈1/10 of the spread). He explicitly books the
adverse-selection tail: when the market has already moved against you, crossing then "costs more
than if we'd just submitted a market order initially." — qoppac.blogspot.com "The world's
simplest execution algorithm." *Caveat: futures, automated, tiny-vs-touch size — an optimistic
analog for our case, and it still lands at ~67%, far under M18's 90–98%.*

C3 [PLAUSIBLE→CONFIRMED, corroborating] (T2 academic, cross-ref sibling A): Filled retail/passive
limit orders are systematically adversely selected — filled **buys correlate −0.3 to −0.6** with
subsequent returns and filled **sells +0.3 to +0.5**; a bid-resting buy fills when price moves
*down* (against you) and only sometimes when it moves up. "The Negative Drift of a Limit Order
Fill" formalizes that a fill is *induced by* adverse price movement. This is the mechanism behind
C1/C2 and quantifies "filled only when wrong." — arXiv 2407.16527 (2024); Anand-Samadi-Sokobin
"Retail Limit Orders" (Rev. of Finance, 2026). *Sibling A owns the depth here; cited as anchor.*

C4 [CONFIRMED] (T3 broker content + T1 606, 2021-11-04 / 2025Q3): **Alpaca does not pass the
maker rebate to the client.** Resting non-marketable limits are routed by Alpaca to rebate-paying
venues and the rebate accrues to *Alpaca*; marketable flow is sold to Virtu Americas, Citadel,
and Jane Street for PFOF. No client maker-rebate capture is possible at Alpaca — the zero
commission *is* the deal, financed by the rebate/PFOF you forgo. — alpaca.markets PFOF explainer;
Alpaca SEC 606a1 2025Q3.

C5 [CONFIRMED] (T1 IBKR + T3 vendor, 2026 vintage): At IBKR Pro **Tiered**, the US-stock
commission (**$0.0035/sh, $0.35/order min**, plus exchange pass-through) *exceeds* the stock
maker rebate (top-tier ~$0.0020–0.0030/sh; less at zero-volume tiers), so a stock maker fill nets
a **small cost (~$0.0005–0.0015/sh), never a credit** — unlike *options*, where per-contract
economics can flip to a net credit. IBKR states Cost-Plus/SMART-MaxRebate pass-through is
"best-efforts," "not guaranteed," and "rebates passed to customers may be less than IB receives";
volume-tier rebate *enhancements* are explicitly withheld from small accounts. — IBKR
commissions-stocks / IBKRATS / SmartRouting docs.

C6 [CONFIRMED] (T3, StockBrokers.com, 2026-05-22): **Named broker-comparison shootouts do not
measure resting-limit fill quality.** They score order-type breadth, routing transparency, and
(via Rule 605) *marketable-order* price improvement — never limit-order fill rates. Per-order
outcome is opaque ("100 occasions → 100 different results; only averages are published"). So the
direct Q1 ask — a practitioner Alpaca-vs-IBKR resting-limit fill-rate number — is **UNKNOWN from
the shootout literature**; it simply isn't measured or published for retail.

C7 [CONFIRMED] (T1 broker docs): **Real order-rate/cancel throttles exist and bind an automated
maker-churn variant (not a 5–25 s manual trader).** Alpaca: 200 req/min (HTTP 429) and a hard
**wash-trade rejection (HTTP 403) whenever your own buy and sell could cross** — a direct blocker
for a high-count strategy that flips direction on the same name intraday. IBKR: 50 msg/s cap,
**Order Efficiency Ratio** monitoring (penalizes high submit-to-fill churn — i.e. post-and-cancel
maker tactics), ≤20 active orders/side/contract. — docs.alpaca.markets user-protection;
interactivebrokers.github.io order_limitations / OER guide.

C8 [CONFIRMED] (T3 tax-practitioner vendors, 2022–2026): **Wash-sale bookkeeping is a severe,
documented burden at high trade count.** Worked example: an actual **net loss of $110,022 forced
to a reported taxable gain of $7,023** via wash-sale deferrals; complexity "branches like a tree"
across partial-lot repurchases. Remedy: **Trader Tax Status + IRC §475(f) mark-to-market
election**, which *eliminates* wash-sale accounting (traders report saving $5k–30k+/yr) — but
requires qualification and a *timely* (pre-year) election. Any research-only high-count
side-ledger must plan for MTM, not naïve lot accounting. — TradeLog "Wash Sales for Traders";
Fairmark "Traders and Wash Sales."

C9 [PLAUSIBLE] (T3 comparison vendor, 2025): For algo strategies needing genuine multi-venue
smart routing / actual exchange posting, practitioners recommend **IBKR over Alpaca**; Alpaca's
only edge is zero commission via wholesaler routing, at the cost of venue control and any
rebate capture. — brokerchooser Alpaca-vs-IBKR; techjockey/tradingview comparisons (thin).

### Constraint gates
| # | Gate | Verdict | Clause |
|---|------|---------|--------|
| 1 | Latency | N-A (PASS) | Cost-model charge; note the maker-first *strategy* it evaluates FAILS §1 (queue/continuous-quote exclusions). |
| 2 | Access | PASS/FAIL-split | Alpaca-as-taker PASS; the maker-*rebate* expression FAILS — Alpaca can't pass it, IBKR's stock commission eats it. |
| 3 | Session | N-A | Cost model applies to any session structure. |
| 4 | Data | PARTIAL | Explicit-fee floor knowable from owned data; honest maker-fill probability needs L2/queue + condition codes we lack cheaply. |
| 5 | Fill realism | **FAIL** (for maker assumption) | Practitioner consensus: touch fills are adversely selected; M18's 90–98%/60 s sim is the exact §7 maker-fill trap. |
| 6 | Statistics | N-A | Not an event-study; a cost-model input. |
| 7 | Protocol | PASS (as cost model) | Feeds every future intraday registration's fee/fill assumptions; introduces no new payer. |

**Survivor-profile score for "maker-first revival of fee-boundary embers": 0/5** —
(1) single-print/auction? No, continuous-market maker fills = 0; (2) scheduled instant? No,
continuous quote management = 0; (3) named price-insensitive payer? No, the taker who fills you is
adversely informed; the clean payer (rebate) is uncapturable = 0; (4) cheaply testable honestly?
No, needs queue/L2 + condition codes = 0; (5) effect ≥ 2× cost? No, rebate < adverse-selection
cost; effect turns negative once selection is priced = 0.

### Economics sketch
Practitioner-informed per-share cost/rebate table (my modality; sibling B holds the *authoritative*
fee-schedule fetch — dates are the schedules I could verify):

| Structure (141 sh clip) | Commission | Rebate captured? | Regulatory pass-through | Net explicit / side | Binding hidden cost |
|---|---|---|---|---|---|
| **Alpaca taker** (marketable) | $0 (promo→2026-12-31) | No (Alpaca keeps PFOF/rebate) | SEC+TAF sell-side ≈ sub-$0.001/sh | ≈ $0 + half-spread crossed | — |
| **Alpaca maker** (resting limit) | $0 | **No** — rebate → Alpaca | SEC+TAF sell-side | ≈ $0 explicit | **adverse selection + missed winners**; wash-trade 403 on self-cross |
| **IBKR-Pro-tiered taker** | $0.0035/sh (min $0.35) | N-A | + taker fee ~$0.0030/sh (venue) | ≈ $0.0065/sh + half-spread (retail reports <$0.005/sh net on SMART) | — |
| **IBKR-Pro-tiered maker** | $0.0035/sh (min $0.35) | **Partial** rebate ~$0.0020–0.0030/sh (never > commission on stocks) | — | **≈ $0.0005–0.0015/sh net COST** | adverse selection; OER churn limit; $0.35 min binds <100 sh |

Fee-schedule dates: IBKR Tiered US-stock $0.0035/sh + $0.35 min (IBKR published, 2026); maker/taker
ranges & Rule 610 $0.0030/sh cap (Databento microstructure; Convex 2026-05-16); Alpaca zero-comm +
PFOF (Alpaca 606 2025Q3; explainer 2021-11-04).

**Read:** Expected gross for the target structure is M18's mid-alpha (+$1.79/trade @141 sh on the
NVDA stream) — *already computed at mid*, so it already embeds the half-spread a maker would earn.
Our cost burden is therefore **not** reducible by "posting instead of crossing": at Alpaca you
can't earn the rebate, and at IBKR the rebate is < commission on stocks. The only *reliable* fill
path is the taker cross, which the registered **$0.005/sh/side + 0.5 bps** model already prices —
and which is a *fair, slightly conservative* estimate of the true all-in floor once adverse
selection makes maker fills illusory. Comparison line: **champion = +2.5 bps/event dev / +12.5
bps holdout** via single-print auction execution (no fill ambiguity, no spread) — the structural
opposite of, and the reason we prefer it to, any continuous-market maker scheme.

### Proposed next test
None (verdict = NOT-VIABLE-STRUCTURAL). Constructive deliverable instead: **(a)** freeze the
cost model at the taker floor ($0.005/sh/side + 0.5 bps) for all M19+ intraday registrations;
never book a maker rebate as revenue. **(b)** Before any future ember is believed, re-run its
fill kernel at a **55–70% adversely-selected touch-fill assumption** (fills drawn preferentially
from bars where price then moves against the entry) rather than the 90–98% unconditional sim, and
require the gross edge to survive that haircut. **(c)** If a high-count research side-ledger is
ever run for bookkeeping, assume IRC §475(f) MTM is mandatory. No trial family is charged (this
sets the cost model that other families are charged against).

---

### Mandated closing deliverables

**Practitioner fill-rate / adverse-selection prior for touch-resting limits at our size:**
The best *named-practitioner* number is Rob Carver's **~2/3 (≈67%) passive-fill rate** on liquid
futures with an active passive-first algo over a multi-minute window (C2) — and that is an
*optimistic* analog (automated, tiny-vs-touch). For NVDA-class equities at 60–210 sh, the honest
prior is **≈55–70% touch-fill within a short (≤60–120 s) window, with the fills strongly
adversely selected** (filled-return correlation on the order of −0.3 to −0.6 for buys / +0.3 to
+0.5 for sells, C3) — i.e. you get filled disproportionately when the trade is about to go against
you and you *miss* the trades where you were right. **M18's 90–98% touch-fill is falsified by
practitioner consensus and should be treated as a ~1.3–1.8× overstatement of realizable fills,
with the additional, worse problem that the realized fills are a biased (losing) subset of
signals.** The clean "how long at the touch on a megacap before a fill" number for our exact clip
is **UNKNOWN** in the practitioner record (retail resting-limit fill quality is unmeasured, C6).

**Practitioner verdict — Alpaca vs IBKR for maker-first intraday at $1k–$10k:**
**Neither broker lets a trader our size earn a net maker rebate, so maker-first has no economic
upside over taking at either.** *Alpaca* is effectively a zero-explicit-cost **taker/wholesaler**
venue: the promo removes commission, but Alpaca keeps the venue rebate, sells marketable flow
(Virtu/Citadel/Jane Street), gives you no venue control, and adds high-count frictions (200/min
throttle; hard **wash-trade 403** when your own orders could cross). *IBKR Pro Tiered* is the only
retail path that actually posts you at the exchange and passes *some* rebate — but on **stocks**
the $0.0035/sh commission (+$0.35/order min) exceeds the rebate, so a maker fill is a small net
*cost*, never a credit, and OER monitoring penalizes post-and-cancel churn. **Recommendation:** if
control and honest maker mechanics ever matter, IBKR-Pro-tiered > Alpaca; but for our program the
correct move is to **stop treating maker-first as a cost lever entirely** — cost intraday
registrations at the taker floor, and let the single-print auction champion (which sidesteps both
spread and adverse selection) remain the only structure where our execution assumptions are safe.

### Sources
1. (T3, conflicted — order-routing tech vendor) axon.trade, "Fees, Rebates, and Maker/Taker Math," 2025-09-25 — https://axon.trade/fees-rebates-and-maker-taker-math
2. (T3, named practitioner) Rob Carver, "The world's simplest execution algorithm," qoppac.blogspot.com, 2014-10-24 — https://qoppac.blogspot.com/2014/10/the-worlds-simplest-execution-algorithim.html
3. (T3, conflicted — broker being evaluated) Alpaca, "Inside Payment for Order Flow…," 2021-11-04 — https://alpaca.markets/learn/love-it-or-hate-it-inside-payment-for-order-flow-and-commission-free-trading-apps ; SEC 606a1 2025Q3 — https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2025Q3.pdf
4. (T3, conflicted — trader-tax software) TradeLog, "Wash Sales for Traders," ©2022–2026 — https://tradelog.com/education/wash-sales-for-traders/ ; Fairmark, "Traders and Wash Sales" — https://fairmark.com/investment-taxation/capital-gain/wash/traders/
5. (T3, conflicted — data vendor / AI-written) Databento microstructure, "Maker-taker rebate model" — https://databento.com/microstructure/maker-taker-rebate-model ; Convex, "Maker-Taker Fees Explained," 2026-05-16 — https://convextrade.com/glossary/maker-taker-fees
6. (T3, broker-comparison vendor) StockBrokers.com, "Best Brokers for Order Execution 2026," 2026-05-22 — https://www.stockbrokers.com/guides/order-execution ; brokerchooser Alpaca-vs-IBKR — https://brokerchooser.com/compare/alpaca-trading-vs-interactive-brokers
7. (T1, broker docs — mechanics) IBKR order limitations / OER — https://interactivebrokers.github.io/tws-api/order_limitations.html ; IBKRATS fees & rebates — https://www.interactivebrokers.com/en/accounts/fees/IBKRATSFees.php ; Alpaca user-protection (wash-trade 403) — https://docs.alpaca.markets/us/docs/user-protection
8. (T2, academic — cross-ref sibling A, corroboration only) "The Negative Drift of a Limit Order Fill," arXiv 2407.16527 (2024) — https://arxiv.org/html/2407.16527v1 ; Anand, Samadi, Sokobin, "Retail Limit Orders," Rev. of Finance 30(2):459 (2026)
9. (T3, venue) Nasdaq, "Quantifying the Cost of Maker-Taker Markets," 2020-10-08 — https://www.nasdaq.com/articles/quantifying-the-cost-of-maker-taker-markets-2020-10-08 ; mlquants, "Market Making without Adverse Selection" (Substack)
10. (T4 — hypothesis/color ONLY, not evidence) Alpaca Community Forum threads on wash-trade flags ("Frustrated with Alpaca's Wash Trade Flags on My HFT Strategy"); Elite Trader / Bogleheads IBKR tiered-cost anecdotes (unverified real-account "≈<$0.005/sh net on SMART, min $0.35/order").

#### Queries used
1. `Alpaca vs Interactive Brokers execution quality resting limit order fill rate comparison`
2. `Ernie Chan maker taker rebate small trader IBKR limit order execution capture`
3. `retail limit order at the touch fill rate adverse selection filled when wrong practitioner`
4. `epchan.blogspot.com transaction cost slippage retail algorithmic trading limit order execution`
5. `Databento blog US equities maker taker fees rebate limit order execution retail`
6. `Alpaca where do limit orders route payment for order flow rebate execution quality 606 report`
7. `wash sale rule thousands of trades per year active trader tax bookkeeping nightmare high frequency`
8. `Interactive Brokers Pro tiered pass-through rebate small volume real account experience net cost per share stocks`
9. `Rob Carver systematic trading execution cost limit order market order slippage Interactive Brokers small account`
10. `Alpaca API order submission rate limit cancel throttle orders per minute wash trade rejection`
11. `Interactive Brokers "Smart Max Rebate" OR "cost plus" limit order net cost per share maker rebate captured real`
12. `limit order fill probability best bid queue "only fills when I'm wrong" adverse selection day trader liquid stock practitioner experience`
13. `Interactive Brokers order rate limit maximum messages per second orders throttle penalty box retail`
14. `Alpaca limit order poor fill quality wholesaler routing algo trader experience versus Interactive Brokers direct exchange execution`
15. `chasing maker rebates not worth it small retail account adverse selection dominates practitioner advice equities`
