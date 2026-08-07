Purpose: independently verify the four academic claims cited by modality agents for lane DR-X11.
Method: located and read primary sources directly (full-text PDFs, not secondary summaries) for
all four papers. Every quote below was extracted by me from the actual PDF text.

---

## R2-C1: Challet & Gourianov (2018), "Dynamical regularities of US equities opening and closing auctions"

**Paper identity:** CONFIRMED. Damien Challet & Nikita Gourianov, arXiv:1802.01921v2 [q-fin.TR],
first submitted 2018-02-06, revised 2018-10-05. Published in *Market Microstructure and Liquidity*
(World Scientific), DOI 10.1142/S2382626619500011.
URL: https://arxiv.org/abs/1802.01921 (full PDF: https://arxiv.org/pdf/1802.01921)

**Sample period:** Three distinct datasets, NOT a single "~2010–2016" window as the claim implies:
1. Order-by-order ARCA auction data: 2009-02-10 to 2014-07-01 (16.2M orders).
2. Daily matched auction volumes, all 3 exchanges (ARCA/NASDAQ/NYSE): 2010-01-01 to 2016-11-30.
3. **Real-time pre-auction indicative-price/imbalance feed — the dataset actually used for the
   mean-reversion analysis in §4 (Section 4, "Pre-auction dynamics")**: 2016-09-28 to 2018-01-12,
   1076 assets, mostly ARCA-listed (i.e., mostly ETFs — the paper's own conclusion states "our
   results on pre-auction periods are mostly about NYSE Arca, i.e., mostly about ETFs").
   So the mean-reversion evidence is drawn from a ~16-month window (late 2016–early 2018), not a
   multi-year 2010–2016 span, and is ETF-heavy rather than a broad "liquid US equities" sample.
   This sample ends before the modern era (pre-2020 NYSE floor closure, pre-COVID volatility
   regime, pre-decade of PFOF/zero-commission retail growth).

**Clause (a) — "pre-cross order flow opposes/fades the imbalance a large majority of the time
(50–65% or ~95% quoted)":** REFUTED AS STATED / CORRECTED. This is a conflation of two different
statistics in the paper.

- Section 4.2 ("Mean-reversion and sub-diffusive prices," pp. 11–12) defines
  P[sign(I_t × δI_{t+1}) = −1] — the probability that a *new order/cancellation event* opposes
  the current imbalance sign — and states: *"this probability is smaller for the opening auction
  than the closing auction for about 95% of the assets."* **This 95% is a cross-sectional
  comparison statistic** (for 95% of assets, the opening-auction value of this probability is
  *lower than* the closing-auction value) — it is **not** "flow opposes the imbalance 95% of the
  time." Using it as a magnitude of mean-reversion is a direct misread.
- The paper's one **named numeric example for the opening auction** (SPY, its most liquid/most-
  studied ticker): *"this probability is about 1/2 for SPY during the opening auction, and about
  0.53 (and roughly constant) during the closing auction."* A probability of ~0.50 means new order
  arrivals are, for this asset, statistically indistinguishable from a coin flip with respect to
  opposing the imbalance — the opposite of "a large majority of the time." The "50–65%" figure
  floated by some research agents is roughly consistent with the *range* shown in the Figure 8
  histogram of per-ticker averages (~0.5–0.8 across ARCA tickers, open vs. close), but is not
  itself stated as a headline number in the paper, and even at its low end (~0.5–0.53 for the
  paper's own opening-auction example) does not support "large majority."
- The paper's stronger, better-supported mean-reversion evidence is a **different metric**: Hurst-
  exponent sub-diffusion of the indicative price (§4.2, Fig. 7). Result: *"the indicative price of
  the opening auction is sub-diffusive for 73% of the assets for the opening auction and 93% of
  the assets for the closing auction"* (H≈0.45 opening vs. H≈0.23 closing, for the SPY example).
  **This is the opposite emphasis of what the claim needs**: by the paper's own numbers, the
  *closing* auction shows the stronger/more prevalent mean-reversion signature (93% of assets,
  H≈0.23, well below the H=0.5 random-walk benchmark), while the *opening* auction — the one
  DR-X11 cares about — shows a substantially weaker effect (73% of assets, H≈0.45, only mildly
  below random-walk).

**Clause (b) — "the paper establishes NO post-open return predictability from imbalance
magnitude":** REFUTED AS STATED / must be corrected to "never tested." I read the complete paper
(Introduction through Conclusion, all of §3 "Matched volumes" and §4 "Pre-auction dynamics": §4.1
Typical activity, §4.2 Mean-reversion, §4.3 Response functions, §4.4 Indicative price vs. limit
order book). **At no point does the paper analyze returns after the auction executes.** Every
analysis is confined to the pre-auction window (indicative price up to auction time, for opening;
up to 4pm, for closing) or to the auction execution price itself. Direct textual confirmation:
- §4.3: *"during the auction process, no trade originates from the auction book building-up; as
  a consequence, usual price efficiency conditions do not apply here."*
- Conclusion (§5): *"Because [of] data availability, our results on pre-auction periods are mostly
  about NYSE Arca, i.e., mostly about ETFs. Future work will use better data in order to check if
  the above findings also hold for more usual equities."* — the paper explicitly flags
  continuous-market/broader-equity extensions as **future work it has not done**, let alone
  post-open continuous-session return regressions, which are simply absent from the paper.
  There is no post-9:30 (or post-4pm) return variable, no regression of subsequent returns on
  imbalance, anywhere in the text.

**Confirmed / corrected / unverifiable:** (a) corrected — headline "mean-reverting" claim is real
but its commonly-quoted magnitudes are misapplied, and the OPENING-auction-specific evidence is
the *weaker* half of the paper's own two-auction comparison. (b) corrected from "tested, found
null" to "never tested at all" — confirmed directly from full-text read, not an inference.

**Lane consequence:** This paper cannot be used to assert either "no continuation exists" (it
never looked) or "imbalance strongly fades pre-cross" (its own opening-auction numbers show a
weak-to-negligible effect, weaker than its closing-auction numbers) — its evidentiary weight for
DR-X11's opening-cross-continuation question is close to zero either way, and any framing that
treats it as having tested post-open returns must be struck from the lane writeup.

---

## R2-C2: Bogousslavsky & Muravyev, "Who Trades at the Close? Implications for Price Discovery and Liquidity"

**Paper identity:** CONFIRMED. Vincent Bogousslavsky (Boston College) & Dmitriy Muravyev (Michigan
State). Working paper dated June 2, 2021; published *Journal of Financial Markets* 66 (2023).
URL (working paper PDF, fetched and read in full):
https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf
SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840 (abstract-page corroboration only, blocked by bot-check for full text; full text obtained from the author's own hosted PDF above)

**Sample period:** TAQ data, January 2010 – December 2018 (§2, Data). NYSE + Nasdaq common stocks,
price > $5, market cap > $100M. Final sample: 5,720,876 stock-day observations (1,887 NYSE-listed,
2,946 Nasdaq-listed). Ends 2018 — predates the 2020 NYSE floor closure, COVID volatility regime,
and the 2020s PFOF/zero-commission retail-trading boom.

**Clause 1 — "auction-price deviations revert ~110% in large caps":** CONFIRMED, exactly, for the
**closing auction**. Main text, §3.3 ("Do closing price deviations reflect information or noise?"),
Table 7: full-sample reversal coefficient b = **−0.845** (85% reversed by next morning). Then,
verbatim: *"For large and small stocks, 110% and 85% of the price deviation is reversed (reported
in Table IA.2 in the Internet Appendix)."* I also read Table IA.2 directly: large-stock
coefficients are **−1.096*** / −1.088*** (≈109–110%)**; small-stock coefficients are −0.849*** /
−0.888*** (≈85–89%). The "110% in large caps" figure the claim cites is accurate, verbatim, and
correctly attributed to large-cap stocks (not small-cap, not the reverse).

**Clause 2 — "this result applies to the OPENING auction":** REFUTED. I read the entire paper
(Introduction through Conclusion, ~30 pages plus the ~10-page Internet Appendix, all 9 tables and
2 internet-appendix tables). The paper studies **exclusively the closing auction**. The word
"opening" appears only in two contexts, neither of which is an opening-auction price-deviation or
reversal analysis: (i) background citations to other papers' work on opening-auction order
consolidation (Barclay, Hendershott & Jones (2008)) and NYSE/Nasdaq opening-auction imbalance-
dissemination mechanics (Hu & Murphy (2020)); (ii) the paper's own §5 finding that *liquidity at
the open* (turnover, effective spread, NBBO depth, WPC/volatility) deteriorates over 2010–2018 as
a side-effect of the *closing*-auction volume boom ("liquidity begets liquidity") — this is a
statement about intraday liquidity conditions at the open, not about opening-auction price
deviations or reversal coefficients. There is no equivalent-to-Table-7 regression, no equivalent-
to-Table-IA.2 breakdown, and no reversal-coefficient estimate anywhere for the opening auction.
The underlying ~110%/close-only result is genuine and well-documented; its extension to the open
is fabricated by whoever asserted it.

**Confirmed / corrected / unverifiable:** Clause 1 confirmed exactly (number, direction,
attribution to large caps all correct). Clause 2 refuted outright — direct read of the complete
paper finds zero opening-auction content of this kind.

**Lane consequence:** The ~110% reversal fact is real and citable — for the CLOSE. It is
irrelevant to DR-X11 (which is about the opening cross) and must not be imported into the lane's
opening-auction reasoning; any prior verdict language treating it as opening-auction evidence
should be struck.

---

## R2-C3: Brown (2025/2026), "The Quote Not Taken: Inefficient Price Discovery in Opening Auctions"

**Paper identity:** CONFIRMED. Thomas K. Brown, McCombs School of Business, UT Austin (job market
paper; incoming Assistant Professor, BYU, Fall 2026). SSRN posting dated Sept 17, 2025; the PDF I
read is the "March 2026" revision (linked from the author's site as "Latest Version").
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5498938 (SSRN blocked full-text
rendering via bot-check; full text obtained via the author's own Google Drive-hosted PDF linked
from https://sites.google.com/view/thomaskbrown/about, and read in full — all 30 main pages, 6
tables, 10 figures, plus Appendices A–C).

**Sample period:** TAQ + CRSP/COMPUSTAT, **2013–2022** (§3.4, Data Sources: "I limit my sample
from 2013-2022"). Rule 605 wholesaler-report comparison restricted to **07/2019–12/2022** (data
availability). The odd-lot retail-flow proxy is only available from 2013 onward (stated
explicitly: "the measure used in this paper, odd lot order volume, has only been publicly
available since 2013"). This is a reasonably modern, decade-spanning sample (through 2022,
covering the 2020 NYSE floor closure and post-COVID period), though it stops short of 2023–2026.

**Clause "predicts REVERSAL (not continuation)":** CONFIRMED, with an important signal-
construction caveat for DR-X11's applicability (below). Abstract/Introduction: *"if a stock had an
abnormally large volume of retail buys (sells) on date t−1, then the stock price will increase
(decrease) from market close on date t−1 until market open on date t. Subsequently, the price will
then reverse, decreasing (increasing) during market hours on date t."* Table 2 confirms the sign
pattern precisely: the long-short "flow reversal" portfolio (long high-buy-imbalance stocks, short
high-sell-imbalance stocks, sorted on t−1 imbalance) earns **positive** alpha overnight (t−1 close
→ t open: 9.38 bps EW / 5.65 bps VW, t≈8.7/5.0) and **negative** alpha both in the first 5 minutes
after open (−3.92/−3.35 bps) and over the full intraday session (−12.27/−6.84 bps, t≈−13.3/−7.2).
**Nearly half of the total intraday reversal occurs within the first 5 minutes of trading**
(explicitly stated in the Introduction and visible in Table 2's 5-minute column).
**Critical caveat on applicability to DR-X11's exact hypothesis:** the paper's predictor is
**date t−1's off-exchange odd-lot order-flow imbalance** (yesterday's retail activity, from TAQ),
**not** the opening cross's own contemporaneous displayed/disseminated imbalance quantity (the
pre-9:30 NASDAQ/NYSE imbalance feed value for day t itself). The paper never constructs or tests
the latter. So while "reversal, not continuation" is an accurate description of *this specific
paper's* finding, it is evidence about a related-but-distinct signal (lagged retail flow →
overnight run-up → post-open correction), not a direct test of "does the auction's own displayed
unpaired-imbalance quantity predict subsequent continuation." Treat as informative context, not
as a direct empirical test of DR-X11's registered hypothesis.

**Clause "~$16bn/yr transferred from retail to wholesalers/internalizers":** REFUTED / CORRECTED
on the "/yr" framing. The paper states (Introduction and §4.3 "Loss estimation," Table 4, Panel
A): *"I estimate that these predictable deviations in pricing have contributed to $16 billion in
losses to retail traders and more than $50 billion in losses for off-exchange traders"* and,
precisely, *"I find that off-exchange investors lost a total of $53.16 billion... I estimate a
$15.95 billion loss to retail investors specifically"* (Table 4, Panel A: Odd Lot −$1.53bn, Round
Lot −$51.63bn, Retail Estimate −$15.95bn). **Nowhere does the paper state an annual run-rate.**
Table 4 presents single, undated aggregate totals with no per-day or per-year breakdown, and the
underlying sample spans roughly nine years (2013–2022; regression tables show Obs.=2265, ≈9
years of trading days). A $53bn *single-day* off-exchange loss from a ~6bp-average mispricing is
not plausible at any scale consistent with the rest of the paper (average TTC ≈5.71bps, Table 4
Panel B), so this is almost certainly a **cumulative total across the full ~2013–2022 sample**,
not an annual figure — the paper's own wording ("lost ... on the following day" / "over the course
of a single day") is the author's shorthand for the *t-to-(t+1)-close* estimation methodology
applied and summed across all sample days, not a literal one-day total. If annualized evenly
across ~9–10 years, the run-rate would be roughly an order of magnitude smaller than $16bn/yr
(~$1.6–1.8bn/yr). The "$16bn" figure itself is accurately transcribed; the "/yr" is not supported
by the text and should be struck or replaced with "cumulative, ~2013–2022."

**Clause "gross or net of costs":** CORRECTED — neither simple label applies; the paper is
explicit and nuanced here. The headline alphas are earned by trading **at the auction execution
price** via Market-On-Open/Limit-On-Open orders, which by construction do not pay the bid-ask
spread; the paper states the average dollar-weighted effective half-spread in-sample was ~5bps
and explicitly: *"if one were to incur transaction costs by trading at the respective bid or ask,
profits would fall to near zero."* Auction participation itself does incur "small fees, unless the
trader is a DMM on the NYSE... usually less than 1 basis point" (footnote 16). So: **gross of the
spread (spread is inapplicable to true at-auction execution) but net of a sub-1bp exchange fee**
— i.e., these are close-to-fully-capturable returns for a trader who can access the auction
directly, but the edge evaporates if captured via ordinary continuous-market bid/ask trading.

**Clause "capturable by an outside taker or only by the internalizing wholesaler":** REFUTED (if
the claim implies wholesaler-exclusivity). The paper's central framing is the opposite: this is a
**publicly observable, outsider-exploitable** inefficiency that competitive market participants
puzzlingly fail to arbitrage away. Direct quotes: *"Using publicly available order flow data, I
present evidence that opening auctions fail to provide efficient prices"*; the retail-flow proxy
(odd-lot volume) has been "publicly available since 2013"; and the author explicitly frames the
paper's contribution as demonstrating that *"competitive traders fail to anticipate foreseeable
uninformed demand"* despite public data availability. The strategy is implementable by any trader
who can submit MOO/LOO orders. The paper does note real capture frictions — thin at-open
liquidity discourages large/scaled funds from exploiting it ("profiting from this strategy relies
on being able to trade at and around the opening auction, when markets are much thinner... This
discourages large funds... where the return on investment isn't sufficiently scalable") — but this
is a liquidity/scalability constraint on outside capture, not evidence that only the internalizing
wholesaler can capture it. Separately, the paper's difference-in-differences section (2020 NYSE
floor closure) shows conflicted-DMM stocks (DMMs that also act as PFOF wholesalers — Citadel,
Virtu) exhibit *materially worse* mispricing when floor-based inter-trader information sharing is
disrupted (65–88bps/day excess reversal during the closure vs. ~0 in ordinary times, Table 6),
implying wholesaler-conflicted auctioneers are implicated in *worsening* the inefficiency under
reduced monitoring — a different claim from "wholesalers are the ones who capture the reversal."

**Confirmed / corrected / unverifiable:** Reversal direction confirmed (with signal-construction
caveat re: DR-X11 relevance). $16bn confirmed as a number but corrected from "/yr" to "cumulative,
~2013–2022 sample." Gross/net corrected to a nuanced "at-auction gross of spread, net of <1bp
fee." Wholesaler-exclusivity refuted — paper frames it as public/outsider-capturable in principle,
constrained by scale rather than information exclusivity.

**Lane consequence:** The paper is real, on-topic, and its headline reversal/mispricing findings
are accurately characterized in direction — but its independent variable is lagged retail flow,
not the opening cross's own displayed imbalance, so it should be cited as supporting context for
"documented opening-window inefficiency exists and is directionally reversal-like," not as a
direct test that forecloses DR-X11's specific continuation hypothesis. The "$16bn/yr" and
"wholesaler-only capture" framings must be corrected before use in the lane verdict.

---

## R2-C4 [bonus]: Heston, Korajczyk & Sadka (2010), "Intraday Patterns in the Cross-section of Stock Returns"

**Paper identity:** CONFIRMED. Steven L. Heston (Maryland), Robert A. Korajczyk (Northwestern),
Ronnie Sadka (Boston College). Published *Journal of Finance* 65(4), 2010, pp. 1369–1407.
URL: https://arxiv.org/abs/1005.3535 (full PDF read directly, arXiv:1005.3535v1).

**Sample period:** All NYSE-listed common stocks (CRSP share codes 10/11), January 2001 – December
2005 (1,715 firms), matched to TAQ. Supplementary pre-decimalization comparison periods: 1993–1997
(1/8-dollar tick) and 1997–2000 (1/16-dollar tick). **This is a dated sample by 2026 standards —
pre-Reg-NMS (2007), pre-modern-HFT-dominant market structure, over two decades old** — a caveat
worth noting even though this claim is used only for a narrow mechanism point.

**Clause "explicitly NOT explained by order imbalance":** CONFIRMED, directly and repeatedly, via
an explicit multivariate test (not merely an unconditional correlation). Abstract: *"Volume, order
imbalance, volatility, and bid-ask spreads exhibit similar patterns, but do not explain the return
patterns."* Section III.A: order imbalance (signed volume via a Lee-Ready-type classification)
*"exhibit[s] periodicity similar to but less pronounced than the periodicity in returns and
volume."* Section III.C, the key test: the authors re-run the return-continuation regression
**with order-imbalance changes (plus volume and volatility changes) included as covariates**
(Eq. 4: r_{i,t} = α + γ·r_{i,t-k} + δ'·V_{i,t-k} + e, where V includes Δorder-imbalance) and find:
*"Surprisingly, Figure 6 shows that the daily pattern of cross-sectional return predictability is
unaffected by including the additional regressors. In other words, volume, order imbalance, and
volatility have similar patterns of intraday predictability, but these variables do not explain
daily return predictability."* Conclusion (§V) repeats this verbatim: *"Changes in trading volume,
order imbalances, and volatility exhibit similar patterns, but do not explain the return
patterns."* This is a genuine controlled test (order imbalance included as a direct regressor
alongside lagged returns), not a passive observation — the strongest possible confirmation.

**Framing clause "driven by systematic trading periodicity":** Largely consistent with the
paper's own framing, with a hedge worth noting: the paper does not claim to have definitively
identified the causal mechanism. It *postulates* institutional fund-flow autocorrelation and
algorithmic-trading-cycle effects as the motivating hypothesis (Introduction), and its conclusion
is phrased cautiously — *"The results are consistent with investors having a predictable demand
for immediacy at certain times of the day"* — rather than as a proven causal claim. So "driven by"
should be read as "consistent with / motivated by," which is how the paper itself hedges it.

**Confirmed / corrected / unverifiable:** Order-imbalance-non-explanation clause fully confirmed
via an explicit regression test. Mechanism-attribution clause is a fair paraphrase of the paper's
stated (but explicitly hedged, not definitively proven) hypothesis.

**Lane consequence:** This is solid, correctly-characterized supporting evidence that periodicity
in order imbalance ≠ periodicity in returns in a NYSE, 2001–2005 sample — useful as a general
microstructure prior that "flow proxies don't mechanically explain return continuation," but dated
and NYSE-only, so it should not be over-extended as direct evidence about modern opening-cross
dynamics.

---

## Summary table

| Claim | Clause | Verdict |
|---|---|---|
| R2-C1 | (a) mean-reversion magnitude | REFUTED/CORRECTED — 95% is a cross-sectional comparison stat, not a within-auction probability; opening-auction's own named example (SPY) is ~0.50 (coin flip); paper's stronger sub-diffusion evidence favors the CLOSE (93%, H≈0.23) over the OPEN (73%, H≈0.45) |
| R2-C1 | (b) no post-open predictability tested | REFUTED AS STATED — paper never tests post-open returns at all; "tested and found null" is an over-read of "never tested" |
| R2-C2 | 110% reversal in large caps | CONFIRMED exactly (Table 7 + Table IA.2) |
| R2-C2 | applies to opening auction | REFUTED — paper is 100% about the closing auction, zero opening-auction price-deviation content |
| R2-C3 | reversal not continuation | CONFIRMED (Table 2), with caveat: predictor is lagged (t−1) retail flow, not the auction's own contemporaneous imbalance feed |
| R2-C3 | $16bn/yr | REFUTED/CORRECTED — figure is real but almost certainly cumulative over ~2013–2022, not annual |
| R2-C3 | gross/net of costs | CORRECTED — gross of spread (inapplicable at true auction execution), net of <1bp exchange fee; collapses to ~zero if captured via continuous-market bid/ask |
| R2-C3 | wholesaler-exclusive capture | REFUTED — paper frames it as publicly/outsider-capturable, constrained by scale not information exclusivity |
| R2-C4 | not explained by order imbalance | CONFIRMED via explicit multivariate regression test (Eq. 4, Fig. 6) |

No claim required a "default refuted=true, could not locate/read" — primary full text was obtained
and read directly (via downloaded PDFs, not proxy-tool paraphrase) for all four papers.

---

## Search queries used

- Challet Gourianov 2018 arXiv opening auction imbalance mean reverting
- arXiv 1802.01921
- Bogousslavsky Muravyev "Who Trades at the Close" auction price reversal
- Brown SSRN retail opening auction order flow reversal wholesalers internalizers
- Heston Korajczyk Sadka 2010 intraday return continuation half hour periodicity order imbalance
- Bogousslavsky Muravyev closing auction reversal coefficient large stocks small stocks percent table
- "Challet" "Gourianov" auctions 2018 sample period 2010 2016 data NASDAQ NYSE imbalance percentage
- "Thomas K. Brown" "Quote Not Taken" opening auctions job market paper pdf
- Bogousslavsky Muravyev "who trades at the close" reversal "110%" OR "85%" OR overshoot overnight
- "Quote Not Taken" Brown opening auctions retail order flow reversal SSRN 2025
- Brown "Quote Not Taken" opening auction NBBO midpoint retail imbalance continuation reversal abstract "we find"
- "Thomas K. Brown" "opening auction" retail wholesalers "$16 billion" OR "16bn" reversal sample period 2020 2021 2022 2023 2024
- Bogousslavsky Muravyev opening auction reversal paper (not closing)
- "Who trades at the open" opening auction reversal price deviation stock

Fetched/read directly (full text, via WebFetch and/or downloaded-PDF Read):
- https://arxiv.org/abs/1802.01921 and https://arxiv.org/pdf/1802.01921 (Challet & Gourianov, full text)
- https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf (Bogousslavsky & Muravyev, full text)
- https://drive.google.com/file/d/1hAkIpmzTxiUxMzD_6uc5bkr199Fl0FoT (Brown 2025/2026, full text, via drive.usercontent.google.com download redirect)
- https://arxiv.org/pdf/1005.3535 (Heston, Korajczyk & Sadka, full text)
- Secondary/abstract-only corroboration: papers.ssrn.com abstract pages for all SSRN-hosted papers (blocked full-text by bot-check, used abstract snippets only), sites.google.com/view/thomaskbrown/about, researchgate.net, worldscientific.com, afajof.org
