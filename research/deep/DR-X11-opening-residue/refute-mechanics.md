# DR-X11 — REFUTER report: opening-cross mechanics (R1-C1, R1-C2, R1-C3)

Role: independent T1 verification layer. All quotes below were located and read
directly by this agent (primary source, not the modality agents' summaries).
Access date for every source: **2026-07-23**.

**Headline: R1-C1 (the decisive claim) is REFUTED.** The disseminated "Imbalance"
field is not, in fact, composed exclusively of order interest that cancels at the
cross. Rule 4752(a)(2)'s own definition folds in "Early Market Hours" orders —
ordinary continuous-book DAY/GTC/MIOC interest that merely arrived before 9:28 a.m.
— and Rule 4702(b)(9)(B) explicitly names a mechanism ("Opening Cross/Market Hours
Order," extending to "Cross to Cross Order") by which LOO-priced, continuing-TIF
interest persists into continuous trading, governed by its own order type, if not
filled in the cross. R1-C2 and R1-C3 hold up on substance; R1-C2 carries one
confirmed citation error (wrong SEC release number) traceable to an unread
search-summary in the source modality doc.

No claim required the default-refuted-for-unlocatable-source rule: a primary text
was located and read for all three.

---

## R1-C1 — MOO/LOO/OIO cancellation and the "Imbalance" field definition

### Verdict: **refuted = TRUE**

### Primary-source quotes (verbatim)

**A. "Imbalance" is not limited to cancel-only on-open order types.**

> "(2) 'Imbalance' shall mean the number of shares of buy or sell MOO, LOO or
> Early Market Hours orders that may not be matched with other MOO, LOO, Early
> Market Hours, or OIO order shares at a particular price at any given time."

— Nasdaq Rule 4752(a)(2) (current numbering, post-SR-NASDAQ-2021-004), Nasdaq
Rulebook redline for Rules 4702/4752,
https://listingcenter.nasdaq.com/assets/RuleBook/Nasdaq/rules/Nasdaq%204702%204752%20(SR-NASDAQ-2021-004).pdf,
accessed 2026-07-23 (PDF read directly).

**B. "Early Market Hours orders" are ordinary continuous-book orders, not on-open-only instruments.**

> "'Market Hours Orders' shall mean any order that may be entered into the System
> and designated with a time-in-force of MIOC, MDAY, MGTC. Market Hours Orders
> shall be designated as 'Early Market Hours Orders' if entered into the System
> prior to 9:28 a.m. and shall be treated as MOO and LOO orders, as appropriate,
> for the purposes of the Nasdaq Opening Cross."

— Nasdaq Rule 4752(a)(10) [renumbered from (a)(7) by SR-NASDAQ-2021-004], same
source. Independently corroborated, verbatim, in the SEC's own order: "Market
hours orders means any order that may be entered into the system and designated
with a time-in-force of MIOC, MDAY, and MGTC; market hours orders are designated
as 'early market hours orders' if they are entered into the system prior to 9:28
a.m." — SEC Release No. 34-91461 (see R1-C2), Federal Register Vol. 86, No. 66,
p. 18331 n.12, https://www.govinfo.gov/content/pkg/FR-2021-04-08/pdf/2021-07197.pdf,
accessed 2026-07-23.

**C. LOO-priced interest with a continuing (non-cross-only) Time-in-Force explicitly persists post-cross — it is not cancelled.**

> "If the Participant enters a Time-in-Force that continues after the time of the
> Nasdaq Opening Cross, the Order will participate in the Nasdaq Opening Cross
> like an LOO Order, while operating thereafter in accordance with its designated
> Order Type and Order Attributes (if not executed in full in the Nasdaq Opening
> Cross). Such an Order may be referred to as an 'Opening Cross/Market Hours
> Order.' If such an Order has a Time-in-Force that continues until at least the
> time of the Nasdaq Closing Cross, the Order may be referred to as a 'Cross to
> Cross Order.'"

— Nasdaq Rule 4702(b)(9)(B), same rulebook redline source.

**D. What IS confirmed: pure on-open orders (TIF = "On Open"/IOC) that go unfilled are cancelled, with a cancellation message.**

> "18. If a firm sends in a MOO/MOC or LOO/LOC or IO orders that do not get
> executed, will they receive a cancellation message? Yes. A cancellation message
> will be returned to the firm after the cross occurs."

— The Nasdaq Opening and Closing Crosses, Frequently Asked Questions, © Copyright
2025, Q18 (exact FAQ and question number the claim itself cites),
https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf,
accessed 2026-07-23 (PDF read directly). This is the *correct* document (the
opening/closing cross FAQ, not the separate IPO/halt-cross FAQ — attack angle
"(iii) is the FAQ language about a different cross?" is answered: no).

### Clause-by-clause

| Clause | Status |
|---|---|
| "Unexecuted MOO/LOO/OIO orders... are cancelled" (pure on-open, TIF=On Open/IOC) | **CONFIRMED** — quote D, plus OIO's Time-in-Force clause ("An OIO Order may execute only in the Nasdaq Opening Cross. An OIO Order entered after the time of the execution of the Nasdaq Opening Cross will be rejected" — Rule 4702(b)(10)(B)) gives no continuation path for OIO specifically. |
| "...and do NOT convert into continuous-market orders" (stated as a blanket rule) | **CORRECTED** — false for the "Opening Cross/Market Hours Order" / "Cross to Cross Order" hybrid (quote C) and for the MDAY/MGTC component of Early Market Hours orders: these are continuous orders by TIF, are swept into the cross's pairing calculation, and — if not executed in full — continue operating under their own order type after the cross concludes, exactly as an ordinary resting DAY/GTC order would. |
| "The NOII 'Imbalance' field is defined... as exactly this unmatched on-open interest" | **CORRECTED (load-bearing)** — Rule 4752(a)(2) itself (quote A) defines Imbalance to include Early Market Hours orders, which are not "on-open" instruments in the cancel-only sense (quote B). The field is not a clean proxy for "interest that vanishes at 9:30." |
| "Nasdaq's Crosses FAQ states a cancellation message is returned to the firm after the cross" (© 2025, Q18) | **CONFIRMED VERBATIM** — exact document, exact question number, exact year all match (quote D). |
| Rule citation "4752(a)(2) or successor numbering" | **CONFIRMED** — (a)(2) is the correct *current* paragraph number for "Imbalance" (renumbered from (a)(1) when SR-NASDAQ-2021-004 inserted the new EOII definition ahead of it). |
| No amendment since 2021 altered this definition (staleness check) | **CONFIRMED, as far as located** — SR-NASDAQ-2023-024 (Release 34-97973, Rule 4752(d)(3) execution-priority relabeling) and SR-NASDAQ-2025-109 (terminology-only "Market Hours" → "Regular Market Hours" rename) are the only located post-2021 amendments touching these rules; neither changes the Imbalance definition, the EOII/NOII schedule, or the cancellation/conversion mechanics described above. The 2023 filing's own exhibit could not be directly read (sec.gov 403), so this is confirmed via convergent secondary description rather than a second verbatim read — flagged as the one clause in this claim resting on slightly thinner sourcing. |

### Provenance note

Modality-B's own "Mechanism" narrative (`modality-B.md`) independently surfaces
the same Rule 4702(b)(9)(B) provision quoted above, and argues *economically* that
such resting interest sits "passively on the far side of the cross" and therefore
isn't "directional pressure." That is a legitimate economic argument, but it is
not what R1-C1 (as posed to this refuter) asserts — R1-C1 asserts a **mechanical**
cancel-only premise, and that premise is textually false for this category. This
refuter takes no position on the *economic* question (whether the surviving
resting interest is large/aggressive enough to matter); it only establishes that
the "zero mechanical persistence" premise used to justify collapsing F3's
survivor-profile score is not accurate as stated.

### Consequence for the lane

**R1-C1 does not close the mechanism.** A textually-confirmed, rule-sanctioned
channel exists (Early Market Hours / Opening-Cross-Market-Hours / Cross-to-Cross
orders) through which some same-direction interest counted in the pre-open
Imbalance figure survives past 9:30 as ordinary resting continuous-book liquidity,
rather than vanishing. This reopens — on mechanics alone — the question B/D used
to downgrade F3 to "informational only"; it does not by itself establish that the
surviving residue is economically exploitable (size, aggressiveness, and crowding
are separate, unresolved questions properly owned by modality C/D's economic
analysis, not this refuter).

---

## R1-C2 — SR-NASDAQ-2021-004 / EOII details

### Verdict: **refuted = FALSE** (substance confirmed; one citation error corrected)

### Primary-source quotes (verbatim)

**A. Correct release number (the claim's "34-91480" is wrong).**

> "[Release No. 34–91461; File No. SR–NASDAQ–2021–004] ... Order Approving
> Proposed Rule Change, as Modified by Amendment No. 2, To Disseminate
> Abbreviated Order Imbalance Information for the Nasdaq Opening Cross... April 2,
> 2021."

— Federal Register, Vol. 86, No. 66 (Thursday, April 8, 2021), p. 18330,
https://www.govinfo.gov/content/pkg/FR-2021-04-08/pdf/2021-07197.pdf, accessed
2026-07-23 (PDF read directly — the document's own masthead, not a secondary
description). The precursor Notice carries a *different* number still: "See
Securities Exchange Act Release No. 91096 (February 10, 2021), 86 FR 9972
('Notice')" (same document, footnote 3). Neither 34-91461 (order) nor 34-91096
(notice) is 34-91480. A targeted search for the string "34-91480" turned up no
Nasdaq/opening-cross document of any kind (see queries 9, 11 below) — it does not
appear to refer to a real, alternate filing.

**B. Approval-date / filed-implementation-date / actual-launch-date — three distinct dates, only one matches the claim.**

> "On April 1, 2021, the Exchange also filed and withdrew Amendment No. 1 to the
> proposed rule change. In Amendment No. 2, the Exchange specified April 26, 2021
> as the implementation date for the proposed rule change..."

— same Federal Register document, p. 18330, n.4. This is the SEC order's own
internal text, and it names **April 26, 2021** — not May 17 — as the date Nasdaq
told the Commission it would implement. The order itself is dated **April 2,
2021** (a third date). The date the claim cites, 2021-05-17, is a *fourth*, later
date, confirmed only by Nasdaq's own subsequent, independent announcements:

> "The changes below have been approved, but will not be implemented until May
> 17, 2021."

— Nasdaq Rulebook redline masthead (repeated on every page),
https://listingcenter.nasdaq.com/assets/RuleBook/Nasdaq/rules/Nasdaq%204702%204752%20(SR-NASDAQ-2021-004).pdf,
accessed 2026-07-23 (PDF read directly), corroborated by Nasdaq Equity Trader
Alert #2021-29, "REMINDER: Nasdaq to Implement Enhancements to the Opening Cross
Process" (implementation date stated as "effective May 17, 2021"),
https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2021-29, accessed 2026-07-23
(page fetch, cross-consistent with the rule text on every other checkable detail).
The claim lands on the date that was **actually implemented** — this is the
approval-date-vs-launch-date trap the task flagged, navigated correctly, except
that there is a third intermediate date (the originally-filed April 26 target)
the claim doesn't mention.

**C. EOII schedule and exclusions.**

> "The Exchange proposes to amend Rule 4752 to establish an early opening order
> imbalance indicator ('EOII') that would be disseminated by electronic means
> every 10 seconds beginning at 9:25 a.m. until the NOII begins to disseminate at
> 9:28 a.m. As proposed, the EOII would contain the same information as the NOII,
> except it would exclude information about indicative prices."

— same Federal Register document, p. 18331. Post-adoption rule text:

> "(A) Beginning at 9:25 a.m., Nasdaq shall disseminate by electronic means an
> early Order Imbalance Indicator every 10 seconds until the Order Imbalance
> Indicator begins to disseminate. (B) Beginning at 9:28 a.m., Nasdaq shall
> disseminate by electronic means an Order Imbalance Indicator every second until
> market open."

— Nasdaq Rule 4752(d)(1)(A)–(B), rulebook redline, same source as above.

**D. Pre-2021 baseline (before this rule, dissemination began at 9:28, no earlier stage).**

> "Under the current process... At 9:28 a.m., the Exchange begins to disseminate
> an order imbalance indicator (also known as the net order imbalance indicator
> or 'NOII') every second until market open."

— same Federal Register document, p. 18330–18331 (describing the pre-amendment
regime). Consistent with a stale but corroborating footnote artifact still
present in the *current* (© 2025) Crosses FAQ PDF: "*Pending SEC approval.
Currently, full NOII dissemination leading up to the Opening Cross begins at 9:28
a.m." — this footnote is evidently an un-scrubbed leftover from the FAQ's
original ~2021 draft (the EOII has been live for five years), not evidence the
EOII is unapproved; flagged here as a documentation-hygiene artifact on Nasdaq's
side, not a substantive finding.

### Clause-by-clause

| Clause | Status |
|---|---|
| Filing "SR-NASDAQ-2021-004" exists | **CONFIRMED** |
| "(SEC release 34-91480)" | **CORRECTED** — actual release number is **34-91461**. This exact wrong number also appears in `modality-B.md` (claims C2, C10, sources item 5, stationarity item 1), which discloses it could not directly fetch the SEC/Federal-Register order and relied on "search summary" for this citation — the likely origin of the error. |
| "effective 2021-05-17" | **CONFIRMED** as the real-world operative date, via two independent Nasdaq-native primary sources — but the SEC order's own text names a *different* date (April 26, 2021) as the implementation date Nasdaq specified in Amendment No. 2. Both dates are real; they refer to different things (originally-filed target vs. actual go-live). |
| EOII: 9:25 ET, every 10 seconds, excludes near/far (indicative) prices | **CONFIRMED VERBATIM** |
| Full NOII: every 1 second from 9:28 to the cross/market open | **CONFIRMED VERBATIM** |
| "Before that date, opening imbalance dissemination began at 9:28" | **CONFIRMED VERBATIM** |

### Consequence for the lane

The EOII/NOII regime-break used for panel stationarity treatment (pre- vs.
post-2021-05-17 field availability) is factually sound and needs no revision.
Downstream lane documents should correct the SEC release-number citation from
34-91480 to **34-91461** wherever it appears (`modality-B.md` claims C2/C10,
sources §5, stationarity §1) — a provenance-hygiene fix, not a substantive one.

---

## R1-C3 — Opening cross cutoff times, cancel/modify lock, and price collar

### Verdict: **refuted = FALSE** (fully confirmed, no corrections)

### Primary-source quotes (verbatim)

**A. MOO / LOO entry cutoffs and late-LOO handling.**

> "MOO orders may continue to be entered until immediately prior to 9:28 a.m.;
> LOO orders may be entered until immediately prior to 9:28 a.m. or, in certain
> circumstances as described below, until 9:29:30 a.m.; and OIO orders may
> continue to be entered until the time of execution of the opening cross."

> "The Exchange proposes to amend Rule 4702(b)(9)(A) to permit the entry of LOO
> orders between 9:28 a.m. and 9:29:30 a.m. ('late LOO orders'), provided that
> the security has a first opening reference price or a second opening reference
> price... any LOO order entered after 9:29:30 a.m. that is designated as
> immediate-or-cancel ('IOC') would be rejected."

— SEC Release No. 34-91461, Federal Register Vol. 86, No. 66, pp. 18331,
accessed 2026-07-23 (PDF read directly).

**B. Cancel/modify lock, currently 9:25 a.m. — and confirmation this was a change FROM 9:28 a.m.**

> "In connection with the establishment of the EOII that would begin
> disseminating at 9:25 a.m., the Exchange proposes to amend Rule 4702(b) to
> prohibit participants from cancelling or modifying MOO, LOO, and OIO orders
> beginning at 9:25 a.m.... But any such orders, once entered, may not be
> cancelled or modified at or after 9:25 a.m."

Contrasted, in the same document, with the pre-existing (pre-2021) regime:

> "Under the current process, market-on-open ('MOO') orders and limit-on-open
> ('LOO') orders may be entered, cancelled, or modified between 4:00 a.m. and
> immediately prior to 9:28 a.m. Opening imbalance only ('OIO') orders may be
> entered between 4:00 a.m. until the time of execution of the Nasdaq opening
> cross, and may be cancelled or modified between 4:00 a.m. and immediately prior
> to 9:28 a.m."

— same source, pp. 18330–18331. This resolves what would otherwise be an
ambiguous redline read: the cancel/modify lock for MOO/LOO/OIO moved **earlier**,
from 9:28 a.m. to 9:25 a.m., as part of this same 2021 filing — it is not still
9:28 today.

**C. Price collar.**

> "3. What are the current thresholds for establishing the Nasdaq Opening and
> Closing Cross prices? Today the Opening and Closing Cross threshold is the
> greater of $0.50 or 10%."

— The Nasdaq Opening and Closing Crosses FAQ, © Copyright 2025, Q3,
https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf,
accessed 2026-07-23 (PDF read directly; ETP thresholds differ: 5%/$0.50 for the
opening cross, 3%/5% for the closing cross, per Q4 of the same document).

**D. Additional Opening Cross Price Tests, and cancellation on failure.**

> "(F) Opening Cross Eligibility: In addition to the Nasdaq Opening Cross price
> process of subparagraphs (A) through (E), each security in the Nasdaq Opening
> Cross must also pass one of the Opening Cross Price Tests in subparagraphs (i)
> through (iii) below or all MOO, LOO, OIO, and Early Market Hours orders in the
> Nasdaq Opening Cross in the security will be cancelled back to Participants, no
> Nasdaq Opening Cross in that security will occur, and the security will open
> for regular market hours trading consistent with paragraph (c) above."

— Nasdaq Rule 4752(d)(2)(F), Rulebook redline,
https://listingcenter.nasdaq.com/assets/RuleBook/Nasdaq/rules/Nasdaq%204702%204752%20(SR-NASDAQ-2021-004).pdf,
accessed 2026-07-23 (PDF read directly). Test A/B/C are, respectively, prior-day
NOCP ± threshold, Nasdaq last sale (post-9:15) ± threshold, and Nasdaq best
bid/offer ± threshold, applied sequentially.

### Clause-by-clause

| Clause | Status |
|---|---|
| "MOO entry cutoff 9:28:00 ET" | **CONFIRMED VERBATIM** |
| "LOO accepted until 9:29:30 (late LOO subject to repricing)" | **CONFIRMED VERBATIM** |
| "on-open order cancel/modify locked from 9:25" | **CONFIRMED VERBATIM** — and confirmed *current*, i.e. this is not a stale pre-2021 figure; the SEC order text explicitly frames 9:25 as the replacement for a prior 9:28 lock. |
| "cross price is collared at benchmark ± the greater of $0.50 or 10%" | **CONFIRMED VERBATIM**, current FAQ (© 2025) |
| "(with additional Opening Cross Price Tests)" | **CONFIRMED** — Tests A/B/C, Rule 4752(d)(2)(F) |
| "if the collar/tests fail, on-open orders are cancelled and no cross occurs" | **CONFIRMED VERBATIM** |

### Consequence for the lane

No correction needed. Any timing assumptions in the lane's design (signal sample
point at 9:28:30, entry logic keyed to the 9:25/9:28/9:29:30 cutoffs) rest on
accurately-stated mechanics.

---

## Search queries used (WebSearch)

1. `Nasdaq Rule 4752 opening cross imbalance MOO LOO cancelled`
2. `Nasdaq Rule 4702 order types MOO LOO OIO definition`
3. `SR-NASDAQ-2021-004 Early Order Imbalance Indicator EOII`
4. `Nasdaq Crosses FAQ opening cross cancellation message`
5. `"34-91480" OR "34-91096" NASDAQ SR-NASDAQ-2021-004 approval order imbalance`
6. `Nasdaq Rule 4702 current text listingcenter.nasdaq.com rulebook 2026 MOO LOO OIO cancel modify`
7. `Nasdaq Rule 4752 amendment 2022 2023 2024 2025 opening cross imbalance definition change`
8. `Nasdaq Trader Alert Early Order Imbalance Indicator opening cross launch date 2021`
9. `"Release No. 34-91480"`
10. `Nasdaq "Opening Cross" MOO OIO "9:25" cancel modify current rule 4702 2026`
11. `SEC "Release No. 34-91480" site:sec.gov OR site:federalregister.gov`
12. `Nasdaq Rule 4752 "Opening Cross/Market Hours Order" OR "Cross to Cross Order" amendment since 2021`

## Primary documents fetched/read directly (not search-summary)

- Nasdaq Rulebook redline, Rules 4702 & 4752 (SR-NASDAQ-2021-004) — PDF downloaded
  and read in full (8 pages, verbatim). SUCCESS.
- The Nasdaq Opening and Closing Crosses FAQ, © 2025 — PDF downloaded and read in
  full (4 pages, verbatim). SUCCESS.
- Federal Register Vol. 86 No. 66 (govinfo.gov PDF mirror of SEC Release
  34-91461 / FR Doc. 2021-07197) — PDF downloaded and read in full (4 pages,
  verbatim). SUCCESS. This is the single most load-bearing fetch in this report:
  it independently nails the release number, both candidate implementation
  dates, and the pre/post cancel-modify-lock change.
- Nasdaq Equity Trader Alert #2021-29 — fetched twice via page-read (not a raw
  PDF/text dump); content cross-consistent with the two verbatim-read documents
  above on every checkable point. PARTIAL confidence (page-summarized, not a
  byte-verbatim read), but corroborated.
- federalregister.gov direct fetch — BLOCKED (redirected to an
  unblock.federalregister.gov interstitial with no content).
- sec.gov direct fetches (2023 exhibit-5 redline; Nasdaq Market Center Systems
  Description) — BLOCKED (HTTP 403), consistent with the charge's warning about
  sec.gov's User-Agent filtering. Not load-bearing: the same facts these would
  have supported were independently confirmed via the rulebook redline, the FAQ,
  and the govinfo.gov Federal Register mirror.
- nasdaqtrader.com System Settings page — fetched; did not contain the specific
  cutoff table sought, superseded by source A/B above.
