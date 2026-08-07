## DR-X9 — Refuter pass on Modality B (mechanics) and Modality C (payer timing)

Lane DR-X9, agent DR-X9-REFUTE. Adversarial re-verification of the 7 load-bearing claims named in
the charge, against primary sources fetched directly where possible. Per AGENT_BRIEF.md refuter
rule: unsourced/unreachable claims default REFUTED, not PLAUSIBLE. All fetches/searches run
2026-07-23.

### Verdict table (7 items)

| # | Claim | Verdict | Confidence |
|---|---|---|---|
| 1 | FOMC 14:00 standardization (Mar 2013) + 2:30 presser | **CONFIRMED** | HIGH |
| 2 | DOL/BLS lockup: electronics ban 2020-03-01, facility discontinued 2020-06-03 | **CONFIRMED** | HIGH |
| 3 | TreasuryDirect no committed minute (qualitative); ±1–2 min (specific number) | **CONFIRMED** (qual.) / **UNVERIFIABLE** (number) | HIGH / — |
| 4 | UMich two-tier end dates: 2013-07-08 Schneiderman; Bloomberg Jan 2015 | **CONFIRMED** | HIGH |
| 5 | S&P 10% Vol Control rebalance = T+2 business days after trigger | **PLAUSIBLE** (primary blocked, T3-corroborated) | MED |
| 6 | Vol-control/target-vol funds execute at close/MOC for NAV, per SSGA | **PARTIALLY REFUTED** (citation mismatch; underlying mechanism independently confirmed) | MED |
| 7a | GS CTA ~$33bn/week flow claim | **CONFIRMED** (as-cited, current vintage) | HIGH |
| 7b | JPM "continues for several more days" claim | **REFUTED** (source cited does not say this) | HIGH |

No genuine contradiction found between B and C, or between either and the M20 registration's
frozen anchors — see "Cross-checks" below; they are complementary, not conflicting.

---

### 1. FOMC 14:00:00 standardization (March 2013) + 2:30 presser contamination

**CONFIRMED, T1, direct primary fetch.** Fetched
`federalreserve.gov/newsevents/pressreleases/monetary20130313a.htm` directly (not via search
summary). Exact text: *"Committee policy statements for all regularly scheduled meetings will now
be released at 2 p.m. Eastern Time"* and, for projection meetings, *"the Chairman's news conference
will begin at approximately 2:30 p.m. Eastern Time."* Dated **2013-03-13** — matches modality B's
"March 2013" exactly (B did not have the exact day; I do). This upgrades B's C5 from
search-summary-backed to directly-fetched T1.

Cross-check: current-vintage FOMC statement PDFs (`monetary20260617a1.pdf`,
`monetary20260128a1.pdf`) are headed "For release at 2:00 p.m." per WebSearch result titles,
confirming the 2013 standardization is still in force through 2026 — i.e., in force across the
entirety of M20's 2020–2026 sample. The 2:30 presser is likewise confirmed live in 2026 (search
hit: "Tomorrow at 2:30 p.m. ET: Chair Powell hosts... FOMC press conference"). One search snippet
noised a "July 2026 press conference at 2:00 p.m." claim; I could not reproduce this from a direct
fetch (404 on the specific presser page) and treat it as a search-summary artifact, not a real
schedule change — does not undermine the 2:30 finding, which has multiple independent
corroborations including a live 2026 example.

Source: https://www.federalreserve.gov/newsevents/pressreleases/monetary20130313a.htm (T1, fetched
directly, 2026-07-23).

### 2. DOL/BLS lockup discontinuation dates (electronics 2020-03-01, facility 2020-06-03)

**CONFIRMED, T1, direct primary fetch of the actual Federal Register text** (not a 403'd summary).
`govinfo.gov/content/pkg/FR-2020-05-27/html/2020-11297.htm` fetched successfully and states
verbatim: *"As of June 3, 2020, DOL will permanently discontinue use of the lock-up facility"* and
*"This Federal Register Notice supersedes the previous Notice issued on February 7, 2020, which
announced the DOL's intent to eliminate use of electronic devices in the lock-up room."* This is a
materially better source than B's own citation chain (B flagged bls.gov as 403-to-fetch and relied
on search-result summaries for the FR docket; I obtained the govinfo.gov mirror of the *same*
Federal Register text directly, at T1, with no summary layer).

The March 1, 2020 electronics-ban date is corroborated by the BLS page's own URL slug
(`changes-to-dol-media-lockup-effective-march-1-2020`, confirmed to exist via search but 403 to
fetch) and is internally consistent with the govinfo.gov text's timeline (Feb 7, 2020 notice of
intent → March 1, 2020 planned effective date → March 20, 2020 facility suspended for COVID →
June 3, 2020 permanent discontinuation). No contradiction found in the chain; upgrade B's C1 to
directly-fetched T1 (govinfo.gov) rather than search-summary-only.

Sources: https://www.govinfo.gov/content/pkg/FR-2020-05-27/html/2020-11297.htm (T1, fetched
directly); https://www.bls.gov/bls/changes-to-dol-media-lockup-effective-march-1-2020.htm (T1,
existence/date confirmed via search, 403 to direct fetch — same limitation B disclosed).

### 3. TreasuryDirect results-posting variance (±1–2 min, no committed minute)

**Split verdict, as B itself split it.** Direct fetch of
`treasurydirect.gov/auctions/announcements-data-results/announcement-results-press-releases/auction-results/`
confirms the *qualitative* half at T1: results are *"updated on a real-time basis as soon as
[they] are made available"* with an explicit instruction to manually refresh — i.e., TreasuryDirect
itself commits to no fixed minute. **CONFIRMED.**

The *specific* "±1–2 min" **magnitude** is not stated anywhere on TreasuryDirect's own pages (I
looked; it isn't there) — it is a T3 aggregator estimate (pagecrawl.io), exactly as B already
labeled it. I could not independently locate a second T1/T2 source for the specific number, so per
the refuter default it stays **UNVERIFIABLE at T1/T2** — but note B never claimed otherwise; B's
own C9 explicitly flags this as "T3 secondary; T1 gives no number." No refutation of B here, just
confirmation that B's own hedge was correctly calibrated — this is a claim B got right by *not*
overclaiming.

Separately verified and useful: direct fetch of `.../auctions-indepth/` (the second TreasuryDirect
URL B cited) confirms verbatim: *"In most cases, the close time is 12 noon Eastern Time for receipt
of noncompetitive bids and 1 PM Eastern Time for receipt of competitive bids"* — matches B's C8
exactly, including the "most cases, not absolute" hedge B itself carried into C9's caveat about
bills/CMBs closing 11:30 a.m.

Sources: treasurydirect.gov auction-results page and auctions-indepth page (T1, both fetched
directly, 2026-07-23).

### 4. UMich two-tier end dates (2013-07-08 Schneiderman; Bloomberg takeover Jan 2015)

**CONFIRMED, T1, direct primary fetch — upgrade from B's T1-via-secondary.** Fetched
`ag.ny.gov/press-release/2013/ag-schneiderman-secures-agreement-thomson-reuters-stop-offering-early-access`
directly. Exact text: *"High-frequency traders were able to access and act on this information two
seconds earlier than other Thomson Reuters subscribers"*; Thomson Reuters agreed to *"immediately
discontinue"* the practice. Release dated **2013-07-08**, matching B exactly. This is a direct fetch
of the actual NY AG page, not a CNN/CNBC secondary summary as B used.

Bloomberg takeover: confirmed via `news.umich.edu`/`record.umich.edu` — University of Michigan's
own announcement states the Bloomberg partnership begins **January 2015**, non-exclusive, contract
through 2019, replacing Thomson Reuters (sponsor since 2007). **CONFIRMED**, matches B's C3/C4.

One gap B correctly flagged as unverified remains unverified by me too: no institutional page
states whether Bloomberg-terminal subscribers get the 10:00:00 print measurably before non-terminal
channels post-2015. I found nothing to confirm or refute this residual — it stays **UNKNOWN**, as
B honestly labeled it (C4 "partly UNVERIFIED").

Sources: https://ag.ny.gov/press-release/2013/ag-schneiderman-secures-agreement-thomson-reuters-stop-offering-early-access
(T1, fetched directly); https://news.umich.edu/bloomberg-to-release-u-m-surveys-of-consumers-starting-in-2015
(T1, university's own announcement, confirmed via search, 2026-07-23).

### 5. S&P 10% Vol Control rebalance = T+2 business days after trigger

**PLAUSIBLE, not fully CONFIRMED — primary document unreachable to me too.** Direct fetch attempts
against `spglobal.com/spdji/.../LVCI_Index_Methodology.pdf`,
`spglobal.com/spdji/.../education-demystifying-volatility-controlled-indices.pdf`, and the S&P DJI
index landing page all returned **403 Forbidden** — the same wall modality C itself hit and
disclosed (C's own sourcing for this claim is "S&P DJI / BlackRock / Nasdaq index methodology
docs" via search summary, not a fetch). I could not do better than C did here.

What I *did* find, independently: a WebSearch summary of an HSBC structured-note index supplement
(a bank's own reproduction of the S&P methodology for a listed product) states *"a two-day lag
between the calculation of the leverage factor... and the implementation of that leverage factor in
the Index"* — an independent corroboration from a different document than C cited, landing on the
same number. A separate Schroders paper on vol-control backtesting references a "1 working day lag"
as a *generic* implementation-delay convention — this is a different, unnamed index family, not a
contradiction of the S&P-specific 2-day figure (C separately and correctly attributes the
**1-day** lag to BlackRock's *different* index, not to S&P).

Net: the specific "T+2 business days" figure for the *named* S&P 10% Vol Control index has two
independent T3-level corroborations (search-summary of S&P's own page, plus the HSBC supplement)
but zero T1 documents I could actually open. Per refuter defaults this is **PLAUSIBLE**, not
CONFIRMED — flag it for anyone with non-automated (human) access to the spglobal.com PDF to close
out at T1.

Sources: HSBC index supplement (search-summary only, PDF not text-extractable by fetch — labeled
binary/compressed on retrieval); Schroders "Managing investment outcomes with volatility control"
(search-summary only). Both T3-adjacent, neither independently fetched to full text.

### 6. Vol-control/target-vol funds execute at close/MOC for NAV — SSGA citation

**PARTIALLY REFUTED as cited — citation-scope mismatch, though the underlying mechanism holds.**
Direct fetch of the SSGA article
(`ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure`, dated
2026-01-23) confirms the MOC/NAV mechanism is real, but the article's own text is about **index
funds and ETFs generically** — *"Index funds and ETFs are structurally incentivized to execute
trades at the closing auction because official net asset values (NAVs) are calculated using closing
prices."* The piece does **not** mention volatility-target, vol-control, or risk-parity funds by
name anywhere in the fetched content. Modality C's C3 cites this SSGA piece specifically in support
of "**vol-target and index funds** execute heavily via MOC" — the "index funds" half is directly
supported; the "vol-target" half is not directly supported by *this* source. This is a citation
overreach, not a factual error in the underlying claim.

The underlying mechanism is independently **CONFIRMED** via a stronger, more general T1 source I
located myself: **SEC Rule 22c-1** (the forward-pricing rule, 17 CFR § 270.22c-1) requires every
registered '40-Act fund (which includes vol-control mutual funds and fixed-index-annuity vol-control
sub-accounts, both named as payers in C's mechanism section) to strike NAV once daily, and
industry-standard practice ties that strike to the 4:00 p.m. NYSE close — per ICI/SEC-summarized
guidance, *"most funds compute NAV right after the New York Stock Exchange closes at 4:00 PM
Eastern."* This is a *structural/regulatory* reason any NAV-linked fund (vol-target included) would
trade at/near the close, independent of and stronger than the SSGA citation. Net verdict: the
**conclusion** in C3 is right; the **specific citation** to SSGA for the vol-target-fund half is
imprecise and should be swapped for the Rule 22c-1 / ICI source, or for a vol-target-specific
prospectus (neither B nor C located one).

Sources: SSGA "Closing time..." (T3, fetched directly, confirms index/ETF half only);
SEC Rule 22c-1 / ICI "Mutual Fund Share Pricing FAQs" (T1/T1-summary, via search, confirms the
general NAV-at-close mechanism), 2026-07-23.

### 7. GS CTA ~$33bn/week and JPM "continues for several days" flow claims

**Split verdict — the GS figure is real and correctly cited; the JPM framing is not supported by
the source cited for it.**

**7a — GS $33bn/week: CONFIRMED.** Modality C's own source (Yahoo Finance,
`finance.yahoo.com/news/goldman-sachs-issues-80b-stock-133215882.html`) was fetched directly and
confirms: *"The bank estimates that a renewed decline could lead CTAs to sell roughly $33 billion of
U.S. equities this week"* and *"as much as $80 billion of additional selling could be unlocked over
the next month."* This is a real, current (dated **2026-02-09**, per the article's own content —
triggered by the S&P breaching a short-term CTA technical level), correctly-sourced, correctly
gross/no-cost-model-labeled figure. C did not misattribute this one. Note for synthesis: this is a
**2026-vintage, single-episode** estimate, not a stable structural constant — treat as an
order-of-magnitude anecdote, not a calibrated parameter, exactly as C's own framing ("PLAUSIBLE, T3
sell-side commentary") already implies.

**7b — JPM "continues for several more days": REFUTED as cited.** I fetched C's own cited source
directly — `heisenbergreport.com/2019/07/16/marko-kolanovic-...` — and it does **not** contain the
claim C attributes to it. The actual text in that article says the *opposite*-oriented thing:
re-leveraging (increasing exposure), not deleveraging, *"tends to continue until there is an
external volatility shock"* — a statement about the build-up phase before a shock, not the unwind
"for several more days" after one. I could not locate, via independent search, any JPM/Kolanovic
primary statement using the "continues for several more days" framing for post-shock deleveraging;
the closest verifiable JPM material I found is a different, later, and differently-scoped claim
(Panigirtzoglou-era commentary about a "three more months" deleveraging estimate in a distinct
episode, and general "extended process... rather than all at once" framing) — none of which matches
C's specific quote or its cited source. Per the refuter default (unsourced/unreachable-as-cited
claims default refuted): **REFUTED as sourced.** The broader qualitative point in C — that
systematic flow is slow/multi-day rather than minutes-scale — is *separately* well-supported by C1
(S&P T+2 lag), C4 (CTA multi-week lookbacks), and C5 (ECB daily-rebalanced-on-rolling-vol) without
needing this specific McElligott/Kolanovic quote; C's verdict does not actually depend on C2 surviving
this check (C2 is corroborating color, not the load-bearing claim), so this refutation does not flip
C's NOT-VIABLE-STRUCTURAL verdict, but the specific citation should be pulled or re-sourced.

Sources: finance.yahoo.com Goldman article (T3, fetched directly, confirms 7a);
heisenbergreport.com 2019-07-16 (T3, fetched directly, does **not** confirm 7b — refutes the
attribution).

---

### Cross-checks: B vs. C vs. M20 frozen anchors — no contradiction found

Read the M20 registration directly (`research/ledger.jsonl`, trial `M20-sched-window-atlas-v1`) to
check both modalities against the actual frozen anchors and the actual empirical result, per the
charge's instruction to flag any conflict.

- **Anchor classes match B's mechanics claims exactly.** M20's registered hypothesis names five
  classes: "FOMC statement/minutes 14:00, 10:00 cluster ISM/UMich/JOLTS/CB-conf, 10y/30y Treasury
  auction results 13:02, and 8:30 releases anchored at the 09:30 open" — this is a verbatim match to
  B's five anchor groups (C5/C10 for 14:00 and 10:00, C8/C9 for 13:02, C2 for 8:30-as-09:30). No
  drift between what B audited and what M20 actually froze.
- **B's "do not pool 8:30 with 10:00/14:00" recommendation was already followed.** M20's spec keeps
  `pre_open_0830` as its own graded cell, not pooled with the intraday anchors — consistent with B's
  C2, not contradicted by it.
- **C's structural verdict is corroborated, not contradicted, by M20's actual empirical result.**
  M20's ledgered result (2026-07-22, "SCREEN-POSITIVE, CONFIRM FAILED") shows: `fomc_stmt`
  NEGATIVE-LEAN at h60 (a reversal, not continuation — 60 min after 14:00 = 15:00, well past the
  ~14:30 presser B's C7 flags as a *second* information event contaminating any window past
  ~14:25); `pre_open_0830` flat null (consistent with B's C2 — a stale, already-impounded signal);
  `tsy_auction_1300` positive-lean but high-variance/underpowered; the one screen-pass
  (`cluster_1000`, the 10:00 group) failed CONFIRM on the validate look. This is exactly the pattern
  C's NOT-VIABLE-STRUCTURAL verdict predicts for a minutes-to-hours horizon (no coherent
  release-minute payer) and exactly the pattern B's C7 predicts for the FOMC window specifically (a
  ~14:30 presser repricing, not slow drift, dominates any window reaching past ~14:25). **B and C
  are complementary, not in tension: B says the clocks are clean; C says the payer isn't in that
  window anyway; M20's own data lands where both predict it should.**
- **No internal B/C contradiction identified.** B's claim that public dissemination is
  simultaneous/leak-free (C1, C5, C10) is not in tension with C's claim that HFT wins the first
  seconds-to-minutes race (C7) — one is about *information* access (no leak), the other is about
  *speed* of reaction to already-public information. Both can be, and are, true at once.

### Sources (numbered, this document)

1. Federal Reserve, press release 2013-03-13 (2:00 p.m. statement / 2:30 p.m. presser
   standardization). T1, fetched directly.
   https://www.federalreserve.gov/newsevents/pressreleases/monetary20130313a.htm
2. Federal Register 2020-11297 via govinfo.gov mirror (DOL lock-up facility discontinued
   2020-06-03; supersedes 2020-02-07 electronics notice). T1, fetched directly.
   https://www.govinfo.gov/content/pkg/FR-2020-05-27/html/2020-11297.htm
3. BLS, "Changes to Department of Labor Media Lockup" (electronics ban effective 2020-03-01).
   T1, existence/URL/date confirmed via search; 403 to direct fetch.
   https://www.bls.gov/bls/changes-to-dol-media-lockup-effective-march-1-2020.htm
4. TreasuryDirect, "Today's Auction Results" (real-time posting, no committed minute). T1, fetched
   directly. https://www.treasurydirect.gov/auctions/announcements-data-results/announcement-results-press-releases/auction-results/
5. TreasuryDirect, "Auctions In Depth" (noon noncompetitive / 1pm competitive close, "in most
   cases"). T1, fetched directly. https://www.treasurydirect.gov/research-center/history-of-marketable-securities/auctions/auctions-indepth/
6. NY Attorney General, press release 2013-07-08 (Thomson Reuters 2-second UMich early-access
   agreement to stop). T1, fetched directly.
   https://ag.ny.gov/press-release/2013/ag-schneiderman-secures-agreement-thomson-reuters-stop-offering-early-access
7. University of Michigan, "Bloomberg to release U-M Surveys of Consumers starting in 2015." T1,
   confirmed via search. https://news.umich.edu/bloomberg-to-release-u-m-surveys-of-consumers-starting-in-2015
8. S&P DJI LVCI methodology PDF and "Demystifying Volatility Controlled Indices" education PDF —
   403 Forbidden to direct fetch (both attempts); claim corroborated only via search-summary of an
   HSBC index supplement, T3-adjacent, not independently opened to full text.
   https://www.spglobal.com/spdji/en/documents/methodologies/LVCI_Index_Methodology.pdf ;
   https://www.spglobal.com/spdji/en/documents/education/education-demystifying-volatility-controlled-indices.pdf
9. State Street Global Advisors, "Closing time: how passive investing is reshaping equity market
   microstructure," dated 2026-01-23. T3, fetched directly — confirms index/ETF MOC mechanism,
   does NOT mention vol-target/vol-control funds by name.
   https://www.ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure
10. SEC Rule 22c-1 (forward pricing) / ICI "Mutual Fund Share Pricing FAQs" — general NAV-at-close
    mechanism for '40 Act funds. T1/T1-summary via search.
    https://www.sec.gov/rules-regulations/2003/12/amendments-rules-governing-pricing-mutual-fund-shares ;
    https://www.ici.org/faqs/faq/mfs/faqs_navs
11. Yahoo Finance, "Goldman Sachs issues $80B stock warning," dated 2026-02-09. T3, fetched
    directly — confirms $33bn/week and $80bn/month figures as-cited by modality C.
    https://finance.yahoo.com/news/goldman-sachs-issues-80b-stock-133215882.html
12. Heisenberg Report, 2019-07-16, Kolanovic commentary. T3, fetched directly — does NOT contain
    the "continues for several more days" deleveraging claim modality C attributes to it; contains
    the reverse-oriented re-leveraging statement instead.
    https://heisenbergreport.com/2019/07/16/marko-kolanovic-unless-theres-an-external-volatility-shock-equity-exposure-to-increase/
13. research/ledger.jsonl — M20-sched-window-atlas-v1 registration + result entries (frozen
    anchors, empirical SCREEN-POSITIVE/CONFIRM-FAILED outcome used for the cross-check section).

#### Queries used
- `"federalreserve.gov" FOMC statement "2:00 p.m." release site:federalreserve.gov`
- `FOMC statement release time changed "2:00 p.m." history 2011 2013 standardize announcement time`
- `Federal Reserve press conference "2:30 p.m." Chair FOMC schedule federalreserve.gov`
- `Federal Register "2020-11297" DOL lock-up facility discontinuation`
- `"BLS" "media lockup" discontinued "June 3, 2020" electronics banned March 2020`
- `S&P 10% Daily Risk Control Index methodology "second business day" rebalance`
- `"S&P 500 Daily Risk Control" methodology "Index Business Day" trigger rebalance lag pdf`
- `"volatility control" index methodology "one business day lag" OR "T+1" implementation observation date`
- `University of Michigan consumer sentiment Bloomberg replaces Thomson Reuters distribution January 2015`
- `SSGA "Closing time" passive investing reshaping microstructure vol-target funds MOC NAV`
- `SEC Rule 22c-1 forward pricing mutual fund NAV struck at close 4pm requirement`
- `Goldman Sachs CTA "$33 billion" per week systematic selling volatility note`
- `JPMorgan Kolanovic systematic deleveraging "continues for several" days after volatility shock`
- Direct fetches (not searches): federalreserve.gov (2013-03-13 release, fomccalendars.htm, 2
  statement PDFs, 1 presser page — 404), govinfo.gov FR-2020-05-27, treasurydirect.gov (auction
  results + auctions-in-depth), data.sca.isr.umich.edu/faq.php, ag.ny.gov 2013 release, oig.federalreserve.gov
  Apr-2016 report, ssga.com Closing-time article, finance.yahoo.com GS article, heisenbergreport.com
  2019-07-16, spglobal.com LVCI PDF (403), spglobal.com education PDF (403), spglobal.com index page
  (403), blackrock.com methodology PDF (403), us.hsbc.com index supplement PDF (unreadable/binary),
  bls.gov 2 PDFs (403 x2), indexes.nasdaqomx.com methodology PDF (unreadable/binary),
  federalregister.gov direct (redirect-blocked, CAPTCHA wall).
