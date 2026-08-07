# Refutation Pass: Claim Bundle X3-NEW-2 ("PI headlines overstate reality")

Access note: SSRN blocked all automated fetch attempts (direct + jina.ai proxy) with
Cloudflare CAPTCHA on every relevant paper (3975667, 4189658, 4313095, 4300505 delivery
links). Findings below rely on: (1) author-hosted mirrors/personal sites where fetchable,
(2) a Wharton research-spotlight page (fetchable, non-SSRN), (3) search-engine snippet
synthesis of abstracts where no full text was fetchable. Flagged per-item below. No full
paper PDF was successfully read end-to-end for any of the four candidate sources.

## C-a: NBBO benchmark overstates PI by ~4x due to odd-lot/hidden-liquidity exclusion

**Verdict: refuted = FALSE (claim substantially holds, but attribution in the bundle is
imprecise)**

Two distinct real papers were located, not one:

1. **Levy (Bradford Lynch Levy), "Price Improvement and Payment for Order Flow: Evidence
   from a Randomized Controlled Trial,"** SSRN 4189658, first posted ~June 2022 (T2,
   working paper). Confirmed via the author's own site (www.bradfordlynch.com, fetched
   directly, non-paywalled) which states verbatim: *"the national best bid and offer
   overstates PI by as much as 400%."* Wharton's WIFPR research-spotlight page (fetched
   directly) adds: prior literature estimated PI at 5–9bp; correcting for the NBBO bias
   drops true PI to 1–5bp; direct-market-access orders get ~4bp PI on average. **This is
   the actual primary source of the clean "400%" figure** — not Ernst. Design: an RCT
   trading random U.S. common stocks with ≥$10M average daily dollar volume and price
   ≥$5.00, at random times in normal market hours, routed simultaneously through a DMA
   broker, TD Ameritrade, and Robinhood. This is a broad liquid/mid-large-cap filter
   (not micro-cap/penny-stock driven), so the 4x figure is not obviously a small-cap
   artifact by design — but I could not obtain a megacap-specific subsample breakdown
   (full text inaccessible).

2. **Adams, Kasten, Kelley, "Do Investors Save When Market Makers Pay? Retail Execution
   Costs Under Payment for Order Flow Models,"** SSRN 3975667, posted Dec 2021 (T2).
   Search-engine synthesis of the abstract (SSRN full text inaccessible) states:
   *"NBBO-based price improvement measures consistently overstate economic savings, in
   some subsamples by a factor of four or more."* The "some subsamples" phrasing is the
   authors' own hedge — it implies the 4x figure is NOT uniform across the sample, which
   cuts against reading it as a broad megacap-applicable number. I could not confirm
   which subsamples (large vs. small, wide- vs. tight-spread) drive it — full text
   blocked.

**Ernst** (Ernst/Spatt/Sun, "Would Order-By-Order Auctions Be Competitive?", fetched
successfully via jina.ai proxy of an ASU-hosted PDF mirror) does **not** contain this
overstatement claim or a 4x/400% figure — it discusses odd-lot sub-penny trade sizing in
a different context (RLP vs. off-exchange comparison). The claim bundle's "Ernst" leg of
the attribution appears to be a misattribution; the correct paper is Levy.

Net: the qualitative claim (NBBO benchmark materially overstates PI; magnitude in the
neighborhood of 4x in at least some conditions) is real and traceable to two independent
T2 sources. The bundle's authorship label is partly wrong (should read "Levy (2022) and/or
Adams-Kasten-Kelley," not "Adams et al. and/or Ernst"). Whether 4x is a liquid-megacap
number or concentrated in wide-spread/small names is **not resolved** by what I could
access — Levy's sample design argues against a pure small-cap artifact; Adams et al.'s own
"some subsamples" wording argues the opposite. Treat as open, not settled either way.

## C-b: honest E/Q ≈ 0.70–1.00 overall, 0.90–2.0 in 15:45–16:00 window for odd-lot clips

**Verdict: refuted = TRUE (specific numeric range is unsupported inference-stacking, not
a primary-source finding)**

- Dyhrberg, Shkilko, Werner, "The Retail Execution Quality Landscape," SSRN 4313095 →
  Journal of Financial Economics 2025 (T2/T1-adjacent, published). Abstract fetched
  directly (SSRN + IDEAS/RePEc + Macquarie mirrors) confirms the paper exists and finds
  wholesaler executions provide "significant cost savings," largest wholesalers cheapest,
  small-stock traders benefit most. The abstract itself does **not** state an E/Q number.
  A wholesaler-wide **E/Q ≈ 0.76** figure appears consistently across search-engine
  synthesis of the paper's content (moderate confidence — not a direct read of the PDF
  body, which was unfetchable/binary-garbled in every attempt), consistent with the
  bundle's citation. This part of the bundle's premise is plausible but not verified by
  me at primary-source, full-text level.
- I could **not locate any primary-source figure for "~0.48 for liquid names"** specifically
  attributed to this paper or any other. One low-confidence AI-search synthesis mentioned
  a "0.44 percentage-point difference" between exchange and wholesaler E/Q for S&P 500
  names, but the arithmetic doesn't reconcile with 0.76/0.97 baselines cleanly, and this
  was a second-hand search-snippet synthesis, not a document I read directly — I do not
  trust it as a primary-source confirmation and flag it as unverified.
- I found **zero primary sources** — academic, SEC/FINRA, or Rule 605-derived — discussing
  E/Q or effective/quoted spread degradation specifically in the 15:45–16:00 window, or
  specifically for $400–$3,000 odd-lot marketable clips on NVDA/TSLA/AMD/MU/GOOGL-class
  names. No paper located models this exact intersection (odd-lot size × megacap ticker
  set × last-15-minutes-of-RTH).
- Conclusion: the 0.70–1.00 baseline range is a plausible-sounding but **unsourced
  widening** applied on top of the one number I could half-verify (0.76 wholesaler-wide,
  which is already inside that range only by coincidence, not derivation). The 0.90–2.0
  close-window figure has **no located empirical support at all** — it reads as a
  worst-case stack (illiquidity + odd-lot exclusion + closing-auction imbalance effects)
  asserted by inference rather than measured. Per the default rule, absent a primary
  source I could fetch and read, this is marked refuted.

## Sources located (with tier/date/access notes)
- Levy (2022), SSRN 4189658 — T2, working paper, posted ~2022-06-27. Full text
  CAPTCHA-blocked; confirmed via author's own site (bradfordlynch.com, fetched) + Wharton
  WIFPR spotlight (wffi.wharton.upenn.edu, fetched directly).
- Adams/Kasten/Kelley (2021), SSRN 3975667 — T2, posted 2021-12-01. Full text
  CAPTCHA-blocked both directly and via proxy; abstract known only via search-engine
  synthesis, not directly read.
- Adams/Kasten/Kelley, "How Free is Free?", SSRN 4403011 → J. Banking & Finance 2024,
  vol.165 — T2→T1 (published). Not directly relevant to the 4x claim (different paper,
  focuses on zero-commission transition); full text inaccessible (ScienceDirect
  paywalled/403, SSRN CAPTCHA-blocked).
- Ernst/Spatt/Sun, "Would Order-By-Order Auctions Be Competitive?" — T2 working paper.
  PDF fetched successfully (ASU conference mirror via jina.ai proxy); does not contain
  the overstatement claim.
- Dyhrberg/Shkilko/Werner, "The Retail Execution Quality Landscape," SSRN 4313095 →
  Journal of Financial Economics 2025, vol.168 — T1 (published). Abstract fetched
  (multiple mirrors); E/Q=0.76 figure not confirmed at full-text level, only via
  search-snippet synthesis.
