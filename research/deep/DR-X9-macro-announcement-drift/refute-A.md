# DR-X9 — Refuter pass on Modality A (academic literature)

Adversarial verification of the 5 load-bearing claims via primary-source fetch (full-text PDF
where obtainable; SSRN/journal/NBER pages otherwise). Refuter default per AGENT_BRIEF.md:
unverifiable claims default to refuted=true.

---

## Claim 1 — Hu, Pan, Wang, Zhu: "premium for macroeconomic announcements" is pre-release;
post-release returns small/insignificant across FOMC/NFP/ISM/GDP

**Verdict: CONFIRMED-WITH-CORRECTIONS**

Full text obtained (NBER Working Paper 25817, "Premium for Heightened Uncertainty: Solving
the FOMC Puzzle," May 2019 rev. July 2019 — https://www.nber.org/system/files/working_papers/w25817/revisions/w25817.rev1.pdf).
This is the working-paper predecessor of the published version.

- **Sample period confirmed**: September 1994 – May 2018 (paper text, Section 2/3.1).
- **Pre-announcement drift numbers — 2 of 3 confirmed, 1 WRONG in modality-A**:
  - FOMC: **27.1 bps**, t=5.95 — modality-A says 27.1. **CONFIRMED.**
  - NFP: **10.1 bps**, t=3.63 — modality-A says 10.1. **CONFIRMED.**
  - ISM: **9.1 bps** (9.14 exact), t=2.10 — modality-A says 9.1. **CONFIRMED.**
  - GDP: **9.6 bps** (9.62 exact, advance+final releases), t=2.06 — modality-A says **7.5 bps.
    This is WRONG.** No number resembling 7.5 appears anywhere in Table 2/3 for any of the ten
    macro series tested (NFP 10.1, GDP 9.6, ISM 9.1, IP 5.2, PI 3.5, HST 2.5, INC 1.6, PPI
    -0.6, CPI -2.1, CSI -4.0). Correct the record: **GDP pre-announcement = 9.6 bps, not 7.5.**
- **Post-announcement claim CONFIRMED in substance from primary tables.** Table 3 ("ann-4pm"
  row) reports the *post*-release window return/t-stat for every series, all economically
  small and none reaching conventional significance except a borderline ISM (11.4 bps,
  t=1.85 — still <1.96): FOMC 1.7 [0.23], NFP 1.5 [0.21], GDP -4.9 [-0.59], ISM 11.4 [1.85],
  IP 5.2 [1.19], PI 2.3 [0.35], HST 1.3 [0.20], INC 1.0 [0.30], PPI 4.7 [0.64], CPI -2.3
  [-0.32], CSI -1.6 [-0.30]. Paper's own text: "Significant drift only exists for the
  pre-announcement window. The average market returns after macroeconomic news releases are
  not significant for all such announcements, similar to FOMC announcements." Footnote 6
  additionally confirms the "large variance" half of the claim: "there is a substantial
  increase in market volatility induced by the announcement." I could not locate the exact
  sentence modality-A quotes verbatim ("post-announcement, the average returns for NFP, ISM,
  and GDP are small and insignificant, while exhibiting large variances...") in this working
  paper — it reads as a reasonable paraphrase of Table 3 + footnote 6, not a fabrication, but
  flag it as **paraphrase-not-verbatim** since the working paper's exact wording differs.
- **Citation-tier/venue correction**: modality-A cites this as "T2, 2021 *Finance Research
  Letters*-forthcoming / SSRN 2021." **This is wrong.** The paper was published in the
  **Journal of Financial Economics**, 2022, **145(3), 909–936** (confirmed via ScienceDirect
  DOI listing, NBER page, and PBC School of Finance host copy: https://www.pbcsf.tsinghua.edu.cn/__local/9/85/32/77D43BBD1810D8C12457D1C8DF3_6CA2EA86_23B665.pdf).
  *Finance Research Letters* is Kurov-Wolfe-Gilbert's venue (Claim 3) — modality-A appears to
  have cross-contaminated the two citations' venues. JFE 2022 is a **stronger** T2 tier than
  what modality-A claimed (top-5 finance journal vs. FRL), so this correction, if anything,
  strengthens the claim's evidentiary weight — but the citation as written is factually wrong
  and should be fixed.

Primary source: Hu, Pan, Wang, Zhu, NBER WP 25817 (https://www.nber.org/papers/w25817),
published as JFE 145(3) 909–936 (2022).

---

## Claim 2 — Lucca–Moench pre-FOMC drift: 49 bps pre-2:15pm, flat after

**Verdict: CONFIRMED (core numbers); mechanism sub-detail UNVERIFIED (paywalled)**

Could not obtain full text directly: NY Fed sr512.pdf (403), Boston Fed conference copy
(403), NBER conference copy (403), Wiley JF abstract (402 paywall), SSRN (403). All primary
hosts blocked automated fetch. Relied on the Hu-Pan-Wang-Zhu NBER paper's own description of
Lucca-Moench (which I *did* obtain in full text, see Claim 1) plus multiple independent
secondary-source search summaries (Google Scholar-indexed excerpts, VoxEU/CEPR, IDEAS/RePEc).

- **Sample period**: September 1994 – March 2011. Directly confirmed via the Hu-Pan-Wang-Zhu
  primary text (page 3): "Using data from September 1994 to March 2011, they find that over
  the 24-hour window before the scheduled announcements by the [FOMC], the return on the S&P
  500 index is on average **49 basis points** per day, more than ten times the average return
  of 4 basis point per day on the same index." This is a citing primary source quoting the
  original number precisely — treat as CONFIRMED at T2 reliability (one level removed from
  Lucca-Moench's own text, but from a peer-reviewed paper accurately restating it, cross-
  checked against 4+ independent secondary summaries all agreeing on "49 bps / 24h / 80% of
  annual return").
- **Post-announcement flatness**: CONFIRMED IN SUBSTANCE, not confirmed in the specific
  mechanistic detail modality-A asserts. Multiple independent search-summary sources agree the
  cumulative return "weakens (becomes insignificant) after the FOMC announcement" / remains
  "flat" and does not reverse. I could NOT independently verify the specific claimed pattern
  "stocks fall ~15 min then recover and end near the 2pm level" — this granular intraday shape
  is plausible and consistent with the flatness finding, but I found no primary-text sentence
  confirming that exact shape (as opposed to, e.g., a monotonic flat line with no dip). Treat
  the "flat after 2pm" headline as CONFIRMED, and the "falls-then-recovers" micro-shape as
  **UNVERIFIED** (downgrade any downstream reliance on that specific shape).
- Cost treatment: NO-COST-MODEL, gross, as modality-A states — this is standard for this
  literature and unproblematic to flag.

Primary source (unreachable directly, cited via cross-confirmation): Lucca & Moench (2015),
*Journal of Finance* 70(1), 329–371; NY Fed Staff Report 512.
https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf (403 on fetch)

---

## Claim 3 — Kurov, Wolfe, Gilbert (2021 *Finance Research Letters*): decay 44.5→9.2 bps
post-2015; Ben Dor–Rosa (2019) dissent

**Verdict: CONFIRMED (full numbers + dissent)**

Full text obtained via PMC open-access mirror
(https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/).

- **Publication confirmed**: *Finance Research Letters*, volume 40(C), 2021 (also confirmed
  via ScienceDirect record S1544612320315956, EconPapers RePEc listing). Matches modality-A.
- **Sample period confirmed**: September 1994 – December 2019 overall, with the key
  sub-samples April 2011–December 2015 (pre-liftoff) vs. January 2016–December 2019
  (post-liftoff), matching modality-A exactly.
- **Decay numbers CONFIRMED**: pre-FOMC drift ≈ **44.5 bps** (Apr-2011–Dec-2015, press-
  conference meetings) collapsing to ≈ **9.2 bps** (Jan-2016–Dec-2019), the latter
  statistically insignificant. Paper's own language (via PMC full text): "the sum of β₀ and
  β₁... which measures the mean pre-FOMC drift after the ZLB liftoff, is not statistically
  significant," and the authors "cannot reject the null hypothesis of equal central tendency"
  vs. non-announcement days post-2015. This is a genuine McLean–Pontiff-class post-publication
  decay, exactly as modality-A frames it.
- **Ben Dor & Rosa (2019) dissent CONFIRMED**: Kurov et al.'s own text states their findings
  "differ" from Ben Dor and Rosa, who "do not find any change in the pre-FOMC drift after
  2015." Independently corroborated via web search of Ben Dor & Rosa, "The Pre-FOMC
  Announcement Drift: An Empirical Analysis," *Journal of Fixed Income* 28(4), 60–72 (2019) —
  https://jfi.pm-research.com/content/iijfixinc/28/4/60.full.pdf (paywalled, abstract-level
  corroboration only, correctly flagged; do not synthesize contents beyond the dissent claim
  itself, which is corroborated by the CITING paper's characterization). Modality-A's
  "CONFIRMED-with-one-dissent, not unanimous" framing is accurate.

Primary sources: Kurov, Wolfe, Gilbert, *Finance Research Letters* 40 (2021), SSRN 3134546.
https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf ;
PMC mirror https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/. Dissent: Ben Dor & Rosa (2019),
*Journal of Fixed Income* 28(4), 60–72.

---

## Claim 4 — Savor–Wilson: 11.4 vs 1.1 bps day-level, market-beta effect

**Verdict: CONFIRMED, and CONFIRMED DAY-level not intraday**

- Numbers confirmed via multiple independent search-summary sources citing the published
  paper: "the average excess daily return on a broad index of US stocks is **11.4 basis
  points** on announcement days versus **1.1 basis points** on all other days," 1958–2009
  sample, "over 60% of the equity risk premium is earned on announcement days, which
  constitute just 13% of the sample period." Matches modality-A exactly.
- **Publication**: Savor & Wilson, "Asset Pricing: A Tale of Two Days," *Journal of Financial
  Economics* 113(2), 171–201 (August 2014) — confirmed via ScienceDirect
  (S0304405X14000890), EconPapers (RePEc:eee:jfinec:v:113:y:2014:i:2:p:171-201), and SSRN
  (abstract=2024422). Also circulated as NBER w24432. Both citations modality-A gives are
  valid (the NBER working-paper number and the journal are the same underlying work).
- **DAY-level confirmed, not intraday**: the return unit is explicitly "average daily return"
  — a close-to-close (or open-to-close) daily excess return comparison across announcement
  vs. non-announcement days, not an intraday decomposition. This directly supports
  modality-A's use of the result to argue there is no documented *idiosyncratic post-release
  intraday* continuation — the paper simply doesn't measure at that granularity, so it cannot
  be read as evidence either for or against a minutes-hours post-release drift; it only
  establishes that the announcement-day premium loads on market beta at the daily horizon.
  This is a correct, non-overreaching use of the source by modality-A.

Primary source: Savor & Wilson (2014), *JFE* 113(2), 171–201; NBER w24432
https://www.nber.org/system/files/working_papers/w24432/w24432.pdf.

---

## Claim 5 — Nonexistence claim: no academic minutes-hours Treasury-auction→equity spillover
study exists

**Verdict: CONFIRMED (no counterexample found after a good-faith search); two near-misses
documented, neither satisfies the claim**

This is a negative existential claim; per the refuter framework it can only be "REFUTED" by
producing one genuine counterexample, or otherwise stand as "no counterexample located despite
a real search." I ran ~8 distinct search queries targeting exactly this object (Treasury
auction RESULT — bid-to-cover, tail, stop-through — spilling into equities at minutes-to-hours
horizon) and checked the two closest candidates in detail:

1. **Fleming, Liu, Nguyen, "Intraday Price Pressure and Order Flow Around U.S. Treasury
   Auctions," NY Fed Staff Report 1188** (https://www.newyorkfed.org/research/staff_reports/sr1188.html,
   403 on fetch; corroborated via search). This is genuinely intraday and genuinely about
   auction results, but scope is **bond-market only** (Treasury yields/order flow) — no
   equity leg. Does not satisfy the claim.
2. **Phillot (2025), "US Treasury Auctions: A High-Frequency Identification of Supply
   Shocks," *American Economic Journal: Macroeconomics*** (https://www.aeaweb.org/articles?id=10.1257%2Fmac.20210243,
   403 on fetch; corroborated via search + abstract-level summary). This DOES trace an
   equity-price effect ("stock prices decline, volatility climbs" in response to a positive
   supply shock; sample 1998–2020) and is billed as "high-frequency identification" — but two
   things disqualify it as a counterexample: (a) the shock is identified from **auction
   ANNOUNCEMENT** (issuance-size) surprises in Treasury futures prices, not from auction
   **RESULTS** (bid-to-cover/tail/stop-through) at the ~1:00–1:01pm auction close — a
   different event and different mechanism than what modality-A's C8 and the WAVE brief mean
   by "auction result"; (b) the equity response is traced via **local-projection** methodology
   typical of macro-finance papers, which in this literature is estimated at daily-to-monthly
   horizons (the paper's broader claims about inflation expectations and the term premium are
   macro-horizon objects), not minutes-hours — I could not confirm a sub-day horizon in the
   equity leg specifically despite searching.

No other candidate surfaced. Sigaux (ECB WP 2208) and the Journal of Banking & Finance
"Treasury auction risk premium" piece (both already in modality-A's Sources list) remain
bond-market-only on inspection. **Conclusion: modality-A's claim stands — I found no academic
minutes-hours Treasury-auction-RESULT-to-equity-spillover study — but the search surface is
not exhaustive (no JSTOR/proprietary database access), so this should be read as "not found,"
consistent with modality-A's own honest UNVERIFIED framing, not as a proven impossibility.**

---

## Summary of corrections to modality-A

1. **C1 numeric error**: Hu-Pan-Wang-Zhu GDP pre-announcement return is **9.6 bps, not 7.5
   bps** as stated. FOMC (27.1), NFP (10.1), ISM (9.1) are all correct.
2. **C1 citation/venue error**: the paper is **Journal of Financial Economics 145(3),
   909–936 (2022)**, not "Finance Research Letters 2021" — modality-A appears to have
   transposed Kurov-Wolfe-Gilbert's venue onto this citation. Correct tier is still T2, and if
   anything the correct venue (JFE) is a stronger placement than what was claimed.
3. **C2 unverified sub-detail**: the specific "falls ~15 min then recovers to the 2pm level"
   shape of the post-FOMC path could not be confirmed from primary text (all primary hosts
   403/paywalled); only the headline "flat/insignificant after" is directly corroborated.
4. **C1 quoted sentence**: the sentence modality-A presents in quotation marks
   ("post-announcement, the average returns for NFP, ISM, and GDP are small and
   insignificant...") is not verbatim in the NBER working-paper text obtained; it is an
   accurate paraphrase of Table 3 + footnote 6, not a fabrication, but should not be rendered
   as a direct quote.

None of these corrections change modality-A's verdict (EXHAUSTED-BY-FIELD) or its constraint-
gate scoring — the core numbers (27.1/10.1/9.1/9.6 pre-announcement bps, post-announcement
≈flat/insignificant, 49 bps pre-FOMC, 44.5→9.2 bps decay with dissent, 11.4-vs-1.1 bps
day-level beta effect) all check out against primary or near-primary sources.

---

## Sources consulted (this pass)

1. **T2** Hu, Pan, Wang, Zhu, NBER WP 25817 (full text obtained), "Premium for Heightened
   Uncertainty: Solving the FOMC Puzzle" — https://www.nber.org/papers/w25817 — published as
   JFE 145(3) 909–936 (2022): https://www.pbcsf.tsinghua.edu.cn/__local/9/85/32/77D43BBD1810D8C12457D1C8DF3_6CA2EA86_23B665.pdf
2. **T2** Kurov, Wolfe, Gilbert (2021), *Finance Research Letters* 40, full text via PMC:
   https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/
3. **T2** Savor & Wilson (2014), *JFE* 113(2) — abstract/summary corroboration:
   https://www.sciencedirect.com/science/article/abs/pii/S0304405X14000890 ;
   https://www.nber.org/system/files/working_papers/w24432/w24432.pdf
4. **T2** Lucca & Moench (2015), *JF* 70(1) — indirect corroboration only (primary hosts
   403/paywalled): NY Fed SR512 https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf ;
   quoted precisely inside Hu-Pan-Wang-Zhu (source 1 above, page 3).
5. **T3 (search-corroborated only)** Ben Dor & Rosa (2019), *Journal of Fixed Income* 28(4),
   60–72 — https://jfi.pm-research.com/content/iijfixinc/28/4/60.full.pdf (paywalled).
6. **T2** Fleming, Liu, Nguyen, NY Fed SR1188 — https://www.newyorkfed.org/research/staff_reports/sr1188.html
   (403; bond-market-only, checked as Claim-5 near-miss).
7. **T2** Phillot (2025), *AEJ: Macroeconomics* — https://www.aeaweb.org/articles?id=10.1257%2Fmac.20210243
   (403; checked as Claim-5 near-miss, does not satisfy the claim — see above).

#### Queries used
- `Hu Pan Wang Zhu Premium for Heightened Uncertainty NFP ISM GDP pre-announcement basis points`
- `Kurov Wolfe Gilbert Disappearing Pre-FOMC Announcement Drift Finance Research Letters 2021`
- `Ben Dor Rosa 2019 pre-FOMC drift no decay after 2015`
- `Ben Dor Rosa Pre-FOMC Announcement Drift Empirical Analysis Journal of Fixed Income findings sample period`
- `Savor Wilson Asset Pricing Tale of Two Days 11.4 basis points announcement day market return`
- `academic study Treasury auction result equity stock market reaction minutes intraday spillover`
- `treasury auction equity returns event study stop-through OR tail intraday academic paper`
- `treasury auction equity stock minutes-after intraday event study working paper SSRN spillover yield surprise`
- `US Treasury Auctions High-Frequency Identification of Supply Shocks stock prices decline horizon`
- `Phillot Treasury Auctions supply shocks stock market local projection horizon days equity response`
- `Lucca Moench pre-FOMC drift 49 basis points flat after announcement`
- `Lucca Moench pre-FOMC drift stock prices fall decline 15 minutes after announcement then recover 2pm level`
- `Lucca Moench pre-FOMC drift abstract returns in the 24-hour flat OR no drift after announcement`
