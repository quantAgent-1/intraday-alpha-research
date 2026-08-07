# Refutation Report: Claim X4-NEW-1 (End-of-Day Reversal)

**Verdict: REFUTED = TRUE** (paper exists and mechanism is real, but the stated magnitude
"+24 bps/day gross" is not supported by the primary source — actual gross spreads are
3.78–6.86 bps/day at the quintile level, materially lower than claimed)

## Primary source
- Baltussen, G., Da, Z., Soebhag, A. "End-of-Day Reversal." Working paper, version **April 2025**
  (first posted SSRN Dec 17, 2024; FEMA-RN Research Paper No. 77/2025).
- Full text fetched directly: https://academicweb.nd.edu/~zda/EOD.pdf (T2, non-paywalled full PDF,
  read via pdftotext, not abstract-only). SSRN abstract page (papers.ssrn.com/sol3/papers.cfm?abstract_id=5039009)
  returned 403 but the identical full-text PDF is mirrored on the corresponding author's (Zhi Da,
  Notre Dame) academic site and confirmed as the same manuscript.
- Sample: NYSE/AMEX/NASDAQ common stocks (share code 10/11), Jan 1993–Dec 2019 (27 years),
  price > $5, excludes bottom 10% NYSE market-cap percentile.

## (1) Does the paper exist with these authors?
Yes, confirmed — Guido Baltussen (Erasmus/Northern Trust AM), Zhi Da (Notre Dame), Amar Soebhag
(Erasmus/Robeco). Title exactly "End-of-Day Reversal." Author list and title in the claim are correct.
Year: originally posted Dec 2024 as claimed; current version dated April 2025.

## (2) Actual magnitude, window definition, sample period
- **Predictor is NOT "previous-close→15:30."** It is ROD3 = return from prior close to **15:00**
  (3:00pm). The authors deliberately insert a skipped gap (SLH, 15:00–15:30) between the predictor
  and the holding window specifically to purge bid-ask-bounce/microstructure noise. This is a
  meaningful correction to the claim's window definition.
- Holding/realization window: **15:30–16:00** (last half hour, "LH") — this part of the claim is correct.
- Magnitude (main result, quintile sorts, value-weighted, gross): low-minus-high (loser-minus-winner)
  spread = **3.78 bps/day** (t=10.69), 9.5%/yr annualized (×252, since position held once/day for 30 min).
  Equal-weighted spread = **6.86 bps/day** (t=17.30), 17.3%/yr.
  Six-factor alphas: full sample 3.71 bps/day (VW); smallest-20%-cap quintile 14.71 bps/day
  (t=27.20); largest-20%-cap quintile 3.41 bps/day (t=10.61).
- **No figure of "~24 bps/day" appears anywhere in the paper** (verified via full-text search of
  abstract, results section, all six tables, and footnotes). The paper explicitly states deciles are
  "stronger" than quintiles and shows a bottom-decile cumulative return of ~400% over 27 years in a
  chart (Fig. 4), but never reports a decile-portfolio bps/day spread figure. 24 bps/day is roughly
  3.5–6x the paper's own headline quintile numbers and exceeds even the smallest-cap-quintile alpha
  (14.71 bps/day) — there is no primary-source support for that specific figure.

## (3) Cost treatment
Paper explicitly frames its 3.78–6.86 bps/day numbers as **"very sizable in gross terms"** — i.e.,
gross of costs, confirming the claim's "gross" framing is directionally correct for the paper's own
(smaller) numbers. But the authors are explicit that the strategy "as presented might **not be
exploitable by many investors after accounting for transaction costs**" given the daily rebalancing
requirement, and that only low-cost participants (market makers, prop/HFT desks) or smarter
execution (netting against already-planned trades) could plausibly capture it net of costs. They do
NOT claim the effect survives costs for a typical institutional investor — this is the opposite of
an implied "survives costs" framing.

## (4) Post-publication OOS evidence / critique 2024–2026
No peer-reviewed critique or independent replication found. The paper won **2nd place, Quantpedia
Awards 2025** (practitioner-community recognition, not an independent academic replication) —
Erasmus School of Economics news release, May 2025. No contradicting or corroborating out-of-sample
academic paper located via search (2024–2026 window). Treat as single-source, not yet independently
replicated.

## (5) Small/illiquid concentration vs. liquid megacaps
Effect is present across the size/liquidity spectrum but is **strongly size-graded**: smallest-20%
quintile six-factor alpha 14.71 bps/day vs largest-20%-cap quintile 3.41 bps/day (both t>10, so
statistically robust even for large caps) — roughly a 4.3x attenuation from smallest to largest.
Paper states effect "also occurs among the most liquid, most traded, and least volatile stocks," so
it is NOT purely a small/illiquid-name artifact — but it is meaningfully weaker there. For a
5–33-name megacap book, the realistic gross edge implied by the paper's own numbers is closer to the
~3.4 bps/day largest-cap-quintile figure, not 24 bps/day, and turnover (100%/day, single name in/out
of a 30-min position) makes cost survival for a megacap-only implementation doubtful per the authors'
own caveat.

## Bottom line
Refuted=true on the specific quantitative claim (+24 bps/day gross decile spread). The paper is real,
correctly attributed, and the qualitative mechanism (retail buy-the-dip + short-seller de-risking
driving reversal in intraday losers during the last half hour) is accurately described in the claim.
But the magnitude is overstated by roughly 3.5–7x relative to the primary source's own reported
numbers, the sort window is mis-specified (15:00 predictor cutoff + skipped 15:00–15:30 gap, not a
continuous close→15:30 window), costs are explicitly flagged by the authors as likely prohibitive for
non-specialist traders, and the megacap-specific edge (~3.4 bps/day) is far below the claimed figure.
