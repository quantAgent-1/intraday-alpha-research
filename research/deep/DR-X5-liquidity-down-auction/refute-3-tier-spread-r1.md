# Refutation Pass — Claim Bundle X5-NEW-1 (dislocation-per-unit-spread down the liquidity curve)

## C-a: NYSE Data Insights — auction price move as multiple of spread, R1000 vs non-R1000

**Verdict: refuted = FALSE (claim confirmed by primary source)**

Source: NYSE Data Insights, "Closing Auction: Immediate market impact, price drift and transaction
cost of trading" (Part 1), by Choey Li (NYSE Quantitative Research Lead).
URL: https://www.nyse.com/data-insights/closing-auction-immediate-market-impact-price-drift-and-transaction-cost-of-trading
Tier: T1 (exchange research). Published: Aug 22, 2023. Sample: 2023 YTD.

Findings as reported:
- Russell 1000 names: orders ~2.4% of CADV entered 15:55–15:56 produce ~0.34X the **daily average
  spread**; same-size orders entered 15:59–16:00 produce ~0.4X daily average spread.
- Non-Russell-1000 ("other") names: immediate price move is **below 0.3X** daily average spread,
  observed range ~0.2X–0.34X.

This matches the claim's numbers closely (0.34–0.40x for R1000 vs <0.3x for non-R1000) — dislocation
per unit of spread is smaller, not larger, down the liquidity curve, on this NYSE metric. One
correction to the claim's wording: NYSE measures against **"daily average spread"**, not strictly
"quoted spread" at the moment of the auction — a related but distinct denominator. This is a
terminology nuance, not a refutation of the direction or magnitude.

Caveat: on **rebalance days** the pattern differs (R1000 jumps to 1.77X vs 0.72X for others) — i.e.
the "smaller down the curve" result is a standard-trading-day finding, not universal across all auction
day-types. The claim as stated (non-rebalance context implied by "immediate price move") holds.

## C-b: Bogousslavsky & Muravyev — small-cap deviation ≈ half-spread, tick-bound 41.8%

**Verdict: refuted = FALSE (claim confirmed by primary source)**

Source: Bogousslavsky & Muravyev, "Who Trades at the Close? Implications for Price Discovery and
Liquidity," Journal of Financial Markets, 2023. Working paper PDF (June 2021 draft):
https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf
(Published version: https://www.sciencedirect.com/science/article/abs/pii/S1386418123000502 ;
SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840)
Tier: T2 (peer-reviewed journal / SSRN). Sample period: NYSE & Nasdaq common stocks, Jan 2010–Dec 2018.

Findings as extracted from the paper text:
- "Auction price deviations are 8.12 bps on average and range from **20.6 bps for small stocks** to
  2.66 bps for large stocks" — matches the claim's 20.6 bps figure exactly.
- Average half-spread for small stocks is reported at ~22.19 bps (Table 5) — i.e. the 20.6 bps
  small-cap deviation sits just under the half-spread, confirming "approximately equals the
  half-spread for most auctions" and that the deviation is mostly bid-ask-bounce-scale, not a large
  tradeable dislocation.
- "The tick size is binding for 42% of all auctions, which mostly explains why so many auctions
  execute at the half spread." Other secondary summaries round this to 41.8%. Direction and
  magnitude both confirmed (minor 41.8% vs 42% rounding, not a discrepancy of substance).
- "Closing price deviations increased sharply for small stocks after the [2016] Tick Size Pilot
  Program started... highly statistically significant" — confirms the tick-size-causality claim.

## Overall

Both claims in bundle X5-NEW-1 are corroborated by their named primary sources, with numbers matching
closely (C-a) or exactly (C-b, the 20.6 bps figure). Net effect: the underlying thesis that "dislocation
per unit of spread is larger down the liquidity curve" (the thing X5-NEW-1 is meant to push back on)
is NOT supported by these two sources — both indicate the small-cap/non-R1000 dislocation is smaller
relative to spread (NYSE) or roughly spread-sized / tick-bound bid-ask bounce rather than an
incremental tradeable edge (B&M). One nuance flagged on C-a: NYSE's "daily average spread" denominator
differs slightly from "quoted spread," and the smaller-down-the-curve result is specific to standard
(non-rebalance) trading days.
