# Refuter R2 — Claim bundle X5-NEW-1 (dislocation-per-unit-spread declines down liquidity curve)

## C-a: NYSE Data Insights — auction dislocation vs spread, R1000 vs non-R1000

**Refuted: FALSE** (claim is an accurate representation of the primary source)

**Source:** NYSE Data Insights, "Closing Auction: Immediate Market Impact, Price Drift and
Transaction Cost of Trading," by Choey Li (Quantitative Research Lead, NYSE), published
Aug 22, 2023.
URL: https://www.nyse.com/data-insights/closing-auction-immediate-market-impact-price-drift-and-transaction-cost-of-trading
Tier: T1 (exchange research). Sample: closing-auction orders submitted 15:55–16:00, 2023 YTD
(as of publication), NYSE-listed names, methodology bins imbalance-update reference-price
changes across 100 order-size buckets over the final 5 minutes.

**Verified figures (direct quotes):**
- Russell 1000: "closing auction orders as large as 2.5% of CADV for Russell 1000 stocks
  results in an immediate price move of around 0.3X the daily average spread." Elsewhere the
  piece reports 0.34X as the headline impact figure, with intraday variation across the last
  5 minutes: 0.3X at 15:55–15:56 rising to 0.4X at 15:59–16:00 (i.e., the 0.34–0.40X range in
  the claim is directly attested).
- Non-Russell 1000: "In stocks not in the Russell 1000, we actually see less immediate price
  move (below 0.3X the daily average spread)" — despite non-R1000 orders reaching up to 5.3%
  of CADV (larger relative size than the R1000 comparison).

**Verdict on the underlying thesis:** Confirmed as described. Down the liquidity curve
(non-Russell-1000 names), immediate dislocation per unit of spread is SMALLER, not larger,
than for Russell 1000 names, despite non-R1000 orders being larger as a fraction of CADV.
This directly supports "dislocation-per-unit-spread declines down the liquidity curve" (for
this specific NYSE immediate-impact metric).

---

## C-b: Bogousslavsky & Muravyev — small-cap deviation ≈ half-spread, tick-binding 41.8%

**Refuted: FALSE** (claim is an accurate representation of the primary source)

**Source:** Vincent Bogousslavsky (Boston College) & Dmitriy Muravyev (Michigan State),
"Who Trades at the Close? Implications for Price Discovery and Liquidity."
Working paper text fetched: https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf
(dated June 2, 2021); published version: Journal of Financial Markets 66 (2023).
SSRN abstract: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840
Tier: T2 (peer-reviewed, Journal of Financial Markets). Sample: NYSE + Nasdaq common stocks,
Jan 2010–Dec 2018 (5,720,876 stock-day observations), price>$5, market cap>$100mm.

**Verified figures (direct quotes/values):**
- Small-cap (bottom size quintile) mean absolute auction deviation = **20.60 bps** (Table 4).
- Small-cap mean half-spread = **22.19 bps**, mean price impact = **−1.60 bps** (Table 5a/b) —
  i.e., for small caps the deviation is on average essentially fully explained by (in fact
  slightly less than) the half-spread; price impact beyond the spread is negative/near-zero
  on average. Full-sample deviation (8.12 bps) vs full-sample half-spread (7.56 bps) shows the
  same pattern market-wide: "the price deviation equals the half spread for most auctions."
- Tick-size binding: exact text (p.4): **"The tick size is binding in 41.8% of all auctions."**
  This is the precise figure the claim cites (rounded to 42% elsewhere in the paper, e.g.
  Figure 4 caption and the Conclusion, but 41.8% is the exact number given in the main text).
- Tick Size Pilot (2016) causal test: "closing price deviations increase sharply for small
  stocks after the 2016 Tick Size Pilot program increased tick size for small stocks" (Figure
  5 shows a discontinuous jump for small-cap deviations at the Pilot start date, while large-cap
  deviations trend down over the same window) — confirms deviations RISE when tick size is
  raised, supporting a causal tick-size (mechanical bid-ask-bounce) origin rather than a
  tradeable-convergence interpretation.
- Additional corroborating detail: 68.5% of all auctions close exactly at the pre-close best
  bid/ask (deviation = half-spread); deviations exceed the half-spread in only 23.4% of cases.

**Verdict on the underlying thesis:** Confirmed as described. The ~20.6 bps small-cap
deviation is quantitatively close to (and, on the mean, fully subsumed by) the half-spread,
with tick-size bindingness (41.8% of auctions) as the documented mechanical driver, and the
2016 Tick Size Pilot provides quasi-causal evidence that raising tick size increases
deviations. This supports reading the small-cap "20.6 bps deviation" as predominantly
bid-ask bounce/tick-size artifact rather than economically tradeable mispricing.

---

## Bundle-level conclusion

Both claims in X5-NEW-1 are supported by their cited primary sources — refuted=false for
both C-a and C-b. Neither source was found to overstate, misquote, or selectively cite; the
NYSE piece is a T1 primary exchange research note and the Bogousslavsky-Muravyev paper is a
T2 peer-reviewed paper, both fetched and read directly (not via secondary summaries) for this
verification.
