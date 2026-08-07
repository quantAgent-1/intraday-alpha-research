## DR-X10 — Refuter pass (lane DR-X10, buyback intraday execution)

Refuter default honored: any claim I could not locate at a primary (T1) source is marked
UNVERIFIABLE, not asserted as confirmed. Scope: the four decisive claims named in the assignment,
cross-checked against modality-A/B/D files in this lane.

---

### C1 — Rule 10b-18 timing condition for large caps

**Claim tested:** exclusion = last 10 minutes before scheduled close + no opening print, for a
security with ADTV ≥ $1,000,000 and public float value ≥ $150,000,000 (30 minutes for all other
securities).

**Verdict: CONFIRMED** (T1)

Primary source: 17 CFR § 240.10b-18(b)(2), current text, eCFR / Cornell LII mirror
(law.cornell.edu/cfr/text/17/240.10b-18). Verbatim structure confirmed:
- Rule 10b-18 purchases must not be "the opening (regular way) purchase reported in the
  consolidated system."
- For high-volume securities: must not be "effected during the 10 minutes before the scheduled
  close of the primary trading session ... for a security that has an ADTV value of $1 million or
  more and a public float value of $150 million or more."
- For all other securities: the analogous 30-minute exclusion applies.
- ADTV is defined as "the average daily trading volume reported for the security during the four
  calendar weeks preceding the week in which the Rule 10b-18 purchase is to be effected."

This matches modality-A/B's stated mechanics verbatim: 10-minute (not 30-minute) exclusion applies
to megacaps (GOOGL/AAPL/MSFT/NVDA/etc.) because they clear the $1M ADTV / $150M float thresholds
by orders of magnitude. No correction needed.

---

### C2 — SEC 2023 daily/quantitative buyback disclosure rule vacated by the Fifth Circuit, Dec 2023

**Claim tested:** the SEC's Share Repurchase Disclosure Modernization Rule (which would have
required daily buyback data, filed quarterly) was vacated by the Fifth Circuit in Dec 2023, so
only monthly Item 703 aggregates exist publicly today.

**Verdict: CONFIRMED** (T1/court)

Primary/near-primary sources: *Chamber of Commerce of the United States of America v. SEC*, No.
23-60255 (5th Cir.). Sequence, corroborated across multiple contemporaneous law-firm client
memos (Paul Weiss, Davis Polk, Morrison Foerster, Duane Morris, Covington & Burling, Linklaters,
Fried Frank, Vinson & Elkins), all dated Dec 2023–Jan 2024:
- Oct 31, 2023: Fifth Circuit ruled unanimously that the SEC acted arbitrarily and capriciously
  (APA violation — failure to respond to comments, no adequate cost-benefit analysis) and ordered
  the SEC to correct the defects by Nov 30, 2023 (rather than vacating immediately).
- The SEC did not cure the defects by the deadline and requested an extension; the court denied it.
- **Dec 19, 2023: the Fifth Circuit vacated the rule outright.** No daily-buyback disclosure
  regime exists; the pre-existing Item 703 monthly-aggregate regime (Reg S-K Item 703, filed
  quarterly in 10-Q/10-K) is the surviving disclosure standard.

Alphabet's own Item 703 tables (confirmed directly from primary filings below) show monthly
granularity only (e.g., FY2025 Q4 table broken out October/November/December 2025 — see C3
below), consistent with this. Claim CONFIRMED without correction.

---

### C3 — GOOGL repurchases: ~$62B FY2024, declining 2025, ~zero Q1 2026

**Claim tested:** Alphabet repurchased ~$62B in FY2024, a declining amount in FY2025, and
approximately zero in Q1 2026.

**Verdict: CONFIRMED, with one number correction** (T1 — read directly from Alphabet's own SEC
filings, not secondary aggregators)

Primary sources fetched and read in full: Alphabet Inc. Form 10-K for FY2025 (filed 2026-02-04,
signed by Sundar Pichai/Anat Ashkenazi, audited by Ernst & Young) and Form 10-Q for Q1 2026 (period
ended March 31, 2026, filed ~2026-04-29–05).

Confirmed exact figures, straight from the Consolidated Statements of Cash Flows / Note 11
(Stockholders' Equity — Share Repurchases) / MD&A "Share Repurchase Program" sections:

| Period | Repurchases (Class A + Class C), cash-flow-statement basis | Shares |
|---|---|---|
| FY2023 | **$62,184 million** | 528M |
| **FY2024** | **$62,222 million (≈$62.2B)** | 379M |
| **FY2025** | **$45,398 million (≈$45.4B)** | 240M |
| **Q1 2026 (3 mo. ended 3/31/2026)** | **$0** | 0 |
| (Q1 2025, for comparison) | $15,068 million (≈$15.1B) | — |

- FY2024 ≈ $62.2B: **matches modality-A/B's number exactly.** CONFIRMED.
- FY2025: modality-B's C9 states "$45.7B (2025)" — the primary-source figure is **$45,398
  million ≈ $45.4B**, not $45.7B. Small (~$0.3B, <1%) overstatement in modality B; modality A's
  own separate reference to "$45.4 billion" for 2025 is the correct one. **Corrected number:
  $45.4B, not $45.7B.**
- Q1 2026: Alphabet's 10-Q, Note 11 states verbatim: *"In the three months ended March 31, 2026,
  there were no repurchases of the company's Class A or Class C shares."* Item 2 of Part II
  ("Unregistered Sales of Equity Securities... Issuer Purchases of Equity Securities") states
  "None." Cash flow statement line "Repurchases of stock": **$0** (vs. $15,068M in Q1 2025). This
  is an **exact, literal zero**, not an approximation — the modality files' "~zero" framing is if
  anything understated; the true figure is precisely $0. CONFIRMED, and the number is exact: $0.

Context also confirmed from the FY2025 10-K: an additional $70.0B repurchase authorization was
approved in April 2025 (on top of an April 2024 $70.0B authorization), and $69.5B of authorization
remained unused as of both Dec 31, 2025 and Mar 31, 2026 — i.e., authorization was not exhausted;
the company chose not to buy. MD&A explicitly attributes the halt to capital reallocation toward
AI infrastructure (capex $91.4B in FY2025, guided to increase further in 2026; $35.7B capex in Q1
2026 alone, +107% YoY) and large cash acquisitions (Wiz $29.5B, Intersect $5.9B closed in
Q1 2026) and new debt issuance ($31.4B net proceeds in Q1 2026) — consistent with the "AI capex
reallocation" narrative in modality B/D, now confirmed from the primary filing rather than press
paraphrase.

---

### C4 — Hillert, Maug & Obernberger (JFE 2016) and the "seller-initiated" characterization

**Claim tested:** does HMO (JFE 2016) itself characterize repurchase trades as seller-initiated,
and does the paper support the "liquidity provision, not directional support" reading D leans on
as its strongest kill?

**Verdict: CONFIRMED, with an attribution clarification (no error found in the lane's own files)**
(T2)

Two sub-claims, checked separately:

1. **HMO's own finding** — Hillert, A., Maug, E., Obernberger, S. (2016), *Stock Repurchases and
   Liquidity*, Journal of Financial Economics 119(1):186–209. Sample: US, 2004–2010, 50,204
   repurchase-months, comprehensive realized-repurchase data, IV/instrumental-variable causal
   identification. Confirmed via the paper's own abstract (fetched from IDEAS/RePEc, a
   non-paywalled mirror of the SSRN/ScienceDirect abstract; direct SSRN/ScienceDirect fetch was
   blocked by paywall/403): the paper states repurchases **"provide liquidity when other investors
   sell the firm's stock or in times of crisis,"** and finds **"no evidence exists that firms
   reduce liquidity when they trade on private information."** This is a liquidity/depth-provision
   result identified via IV, not a directional-return or "push price up" result — exactly as
   modality-D's Mechanism section and C4 claim characterizes it. CONFIRMED.
2. **The "seller-initiated" / ~60% figure** — this specific number is **not** in HMO. It is
   correctly sourced in the lane's own files (modality-A's C4, modality-D's C3, both citing
   McNally, Smith & Barnes (2006), *The Price Impacts of Open Market Repurchase Trades*, Journal
   of Business Finance & Accounting, a study of 60,000+ individual TSX (Canadian) repurchase
   trades) — confirmed via a separate web search independent of the lane's citations: "~60% [of
   trades] are seller-initiated" and "the average intraday price impact of repurchase trades is
   negative" are McNally/Smith/Barnes' (Canadian, TSX) findings, not Hillert-Maug-Obernberger's
   (US, JFE). **The lane's own modality files do NOT conflate the two** — D's mechanism paragraph
   explicitly attributes the "~60% seller-initiated" figure to "the Canadian daily-data evidence"
   separately from the HMO liquidity-provision citation, and D's Sources section lists McNally et
   al. as a distinct numbered source (their C3) from HMO (their C4). So the combined "D's
   strongest kill" argument — (a) HMO shows repurchases are a liquidity-provision, non-directional
   phenomenon; (b) the McNally/Smith/Barnes Canadian tape shows the underlying trades are
   majority seller-initiated with negative average intraday impact — **is built from two correctly
   separated, correctly attributed T2 papers, not a misattribution.** CONFIRMED as accurately
   represented; no correction to the lane's synthesis is needed on this point.

---

### Summary for the orchestrator

All four claims are CONFIRMED. One numeric correction: Alphabet's FY2025 buyback total is
**$45.4 billion (exactly $45,398 million), not $45.7 billion** as stated in modality-B's C9 —
modality-A's own figure of "$45.4 billion" was the correct one; the $45.7B figure was already an
outlier inside the lane's own files, not something invented by this refuter. Q1 2026 GOOGL
repurchases were confirmed as a literal, exact **$0** (not merely "~zero") directly from
Alphabet's Q1 2026 10-Q cash-flow statement and Note 11 disclosure. Nothing found here changes the
lane's verdict architecture (F2's mechanism-and-magnitude problems stand on their own regardless of
the $45.4B vs $45.7B rounding).

### Sources consulted (this refuter pass)

1. [T1] 17 CFR § 240.10b-18, current text — eCFR / Cornell LII (law.cornell.edu/cfr/text/17/240.10b-18).
2. [T1/court] *Chamber of Commerce of the USA v. SEC*, No. 23-60255, 5th Cir., opinion Oct 31 2023
   / vacatur Dec 19 2023; corroborated via Paul Weiss, Davis Polk, Morrison Foerster, Duane Morris,
   Covington & Burling, Linklaters, Fried Frank, and Vinson & Elkins client memos (Dec 2023–Jan
   2024), and Justia case docket (law.justia.com/cases/federal/appellate-courts/ca5/23-60255/).
3. [T1] Alphabet Inc., Form 10-K for the fiscal year ended December 31, 2025 (filed 2026-02-04;
   SEC file no. 001-37580; audited by Ernst & Young LLP; signed by Sundar Pichai / Anat Ashkenazi),
   fetched directly from Alphabet's investor-relations PDF (s206.q4cdn.com) and read page-by-page.
   Cash flow statement, Note 11 (Stockholders' Equity), and MD&A Share Repurchase Program section.
4. [T1] Alphabet Inc., Form 10-Q for the quarterly period ended March 31, 2026 (filed ~2026-04-29),
   fetched directly from Alphabet's investor-relations PDF and read page-by-page. Cash flow
   statement and Note 11.
5. [T2] Hillert, A., Maug, E., Obernberger, S. (2016), *Stock Repurchases and Liquidity*, Journal
   of Financial Economics 119(1):186–209; abstract confirmed via ideas.repec.org/a/eee/jfinec/v119y2016i1p186-209.html
   (SSRN/ScienceDirect direct fetch blocked by paywall/403 — abstract-only, not synthesized beyond
   what the abstract states).
6. [T2] McNally, W.J., Smith, B.F., Barnes, T. (2006), *The Price Impacts of Open Market Repurchase
   Trades*, Journal of Business Finance & Accounting (TSX, 60,000+ trades; ~60% seller-initiated;
   negative average intraday price impact) — confirmed via independent web search, corroborating
   the lane's own citation and attribution.
7. [T3, corroborating only] 24/7 Wall St (2026-07-22), "Alphabet Just Cut Share Buybacks To $0";
   macrotrends/stock-analysis-on.net Alphabet cash-flow series — used only to triangulate before
   the primary-filing fetch; superseded by items 3–4 above.

#### Queries used

- `Chamber of Commerce v. SEC Fifth Circuit December 2023 share repurchase disclosure rule vacated opinion`
- `Alphabet 10-K 2024 stock repurchases cash flow statement total repurchased`
- `Hillert Maug Obernberger "Stock Repurchases and Liquidity" seller-initiated liquidity provision JFE 2016`
- `"seller-initiated" repurchase trades open market share buybacks intraday price impact Canadian study`
- `Alphabet 10-Q Q1 2026 first quarter 2026 stock repurchases $0 zero buyback`
- `Alphabet 2025 annual report full year stock repurchases total dollar amount 10-K fiscal 2025`
- WebFetch: law.cornell.edu/cfr/text/17/240.10b-18; papers.ssrn.com/sol3/papers.cfm?abstract_id=2369470
  (403, paywalled — not synthesized); ideas.repec.org/a/eee/jfinec/v119y2016i1p186-209.html;
  s206.q4cdn.com GOOG-10-Q-Q1-2026.pdf (full text extracted via PDF read); s206.q4cdn.com
  GOOG-10-K-2025.pdf (full text extracted via PDF read); sec.gov EDGAR company filing browse (403).
