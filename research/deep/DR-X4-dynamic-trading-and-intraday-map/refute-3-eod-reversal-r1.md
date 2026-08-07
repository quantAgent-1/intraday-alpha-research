# Refute R1 — Claim X4-NEW-1 (end-of-day reversal, ~24bps/day gross)

**Verdict: REFUTED (magnitude/framing false; paper's mechanism and existence are TRUE).**

## Primary source
- Baltussen, Guido; Da, Zhi; Soebhag, Amar. "End-of-Day Reversal." Working paper, April 2025 (SSRN #5039009; PDF fetched and read in full via https://academicweb.nd.edu/~zda/EOD.pdf).
- Tier: T2 (SSRN working paper; also EFMA 2024 conference paper — same authors/title). SSRN abstract page itself 403'd to WebFetch, but the full PDF (Notre Dame mirror) was fetched and read directly with pdftotext — not abstract-only.
- Sample period: **January 1993 – December 2019** (NYSE/AMEX/NASDAQ, share codes 10/11, price > $5).

## (1) Does the paper exist as described?
Yes, author list and title are exactly correct: Guido Baltussen (Erasmus/Northern Trust AM), Zhi Da (Notre Dame), Amar Soebhag (Erasmus/Robeco). Title "End-of-Day Reversal." No correction needed on authors/title. Year: dated April 2025 (the claim's "~2024" is close — an EFMA 2024 conference version exists; the SSRN/working-paper version circulating is dated April 2025).

## (2) Actual magnitude, window, sample
- **The claim's "+24 bps/day" figure is wrong.** The paper's actual headline long-short (bottom-minus-top quintile, low-minus-high ROD3) spread in the last-half-hour (LH) window is **3.78 bps/day (value-weighted)** and **6.86 bps/day (equal-weighted)**, i.e. ~9.5%/yr and ~17.3%/yr respectively — gross. These are quintile sorts, not decile sorts, in the headline table.
- A **decile**-level cut is not reported as a single headline number; instead a size-conditional bivariate sort shows the long-short 6-factor alpha is **14.71 bps/day** in the smallest-20%-of-firms quintile bucket, and **3.41 bps/day** in the largest-20%-of-firms bucket. No reported cut reaches ~24 bps/day anywhere in the paper (checked all "bps" occurrences).
- Window definition: sort variable is "ROD3" = cumulative return from prior close through 30 minutes before close (i.e., close-to-close minus last 30 min, NOT "previous-close→15:30" exactly — it is close-to-(close-30min), which for a 4:00pm close approximates 9:30am–3:30pm, consistent with the claim's 15:30 cutoff). Outcome window is the **last 30 minutes (LH)**, i.e. 15:30–16:00 ET — this part of the claim is correct.

## (3) Cost treatment
- The paper explicitly states these numbers are **gross**: "The effect is very sizable in gross terms with a 3.78 bps reversal per day... and 6.86 bps per day... for the equal-weighted L-S portfolio." So "gross" framing in the claim is directionally right, but the gross number itself (24bps) is roughly 3.5–6x too high vs. the actual headline gross value-weighted number.
- Authors explicitly caution: "the strategy as presented might not be exploitable by many investors after accounting for transaction costs," given it requires **frequent (daily) rebalancing**. They do NOT publish a net-of-cost number; they only speculate the effect may be exploitable by market makers/prop desks with very low per-trade costs, or via opportunistic execution-timing of already-planned trades. No net-return figure is given anywhere in the paper.

## (4) Post-publication OOS/replication/critique (2024–2026)
- Won 2nd place at Quantpedia Awards 2025 (Soebhag/Baltussen), per Erasmus University news — a form of community validation, not an independent replication.
- No independent published replication or critique found in this search (searches did not surface a rebuttal paper). This is a working paper, not yet in a peer-reviewed journal as of the version read.

## (5) Size/liquidity concentration — decisive for a 5-33 megacap book
- The effect is **NOT** decile/small-cap-only: it "occurs among the most liquid, most traded, and least volatile stocks" and is "present across size groups," including "the 20% largest firms" (6-factor alpha 3.41 bps/day, t=10.61). However it is **materially stronger for small/illiquid names**: equal-weighted (small-cap-tilted) spread (6.86 bps) is ~1.8x the value-weighted spread (3.78 bps), and the smallest-quintile bucket (14.71 bps) is ~4.3x the largest-quintile bucket (3.41 bps).
- **Implication for a 5–33 megacap book:** the effect is real and statistically significant in large/liquid names too, but at ~3.4 bps/day gross for the largest-quintile long-short — not the claimed 24 bps/day — and that number itself is a diversified quintile spread, not a single-name expected edge. This is a much thinner edge in megacaps than the claim implies, and daily-rebalanced with a 30-min holding window, cost sensitivity is high.

## Summary of refutation
Claim confirmed true on: paper existence/authors/title, mechanism (retail attention + short-covering), gross framing, and effect surviving in large/liquid names. Claim refuted on: the **~24 bps/day magnitude is not supported anywhere in the source** — actual gross headline is 3.78 bps/day (VW) / 6.86 bps/day (EW), and even the strongest reported decile/quintile cut (smallest-20%-of-firms) is 14.71 bps/day, still below 24. No net-of-cost figure exists in the paper.
