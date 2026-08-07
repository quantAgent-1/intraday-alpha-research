## DR-X9 — Modality B (primary/venue: release mechanics) findings

Scope: I own all **release-mechanics** claims for LANE 1. This modality does not judge whether
drift is profitable — it judges whether the *clocks* M20 reads are clean. Focus = the exact
publication protocol, embargo/lockup rules, tiered-access history, and dissemination latency of
each release class, sourced to the issuing institution wherever possible. Every mechanics fact is
scored for whether it **biases a frozen 5-minute reaction window** read from 10:00:00 / 13:02:00 /
14:00:00 quotes (and the 8:30-as-of-09:30 read). All URLs retrieved 2026-07-23.

### Verdict recommendation
**Not a trade verdict — a data-integrity verdict on the anchors.** NET: the **10:00:00** and
**14:00:00** anchors are mechanically CLEAN for M20's 2020–2026 sample (simultaneous public post,
no in-sample tiered early access). The **13:02:00** Treasury anchor carries **±1–2 min posting
variance** (fixed-clock misalignment risk, not a leak). The **8:30-as-of-09:30 read is the one
structurally compromised anchor**: it is a ~60-minute-stale signal whose reaction is already
impounded in the pre-market and the opening cross — it does NOT read a clean 8:30:00 impulse and
must not be pooled with the intraday anchors. Confidence HIGH on 10:00/14:00 cleanliness and on the
8:30 staleness; MED on the exact Treasury posting-latency distribution (Treasury's own page gives no
number).
**What would flip it:** discovery that a M20 in-sample (2020–2026) 10:00/14:00 release still ran a
paid subscriber-vs-public lead (e.g., a wire-terminal getting UMich/ISM before the free post),
which would bias the 10:00:00 read the same way the pre-2013 UMich elite tier did.

### Mechanism (dissemination, not payer)
Modern federal macro releases (post-2020 BLS, post-2015 Fed) converged on a **single simultaneous
public post** model precisely because the prior lockup/subscriber-lead architecture *created* the
staggered-dissemination microstructure that biases event studies. The historical two-tier and
elite-HFT tiers (UMich 9:54:58; DOL lockup 8:00–8:30 embargo transmission) are the exact mechanism
that would have contaminated a fixed-clock read — and they were dismantled *before or at the start*
of M20's 2020–2026 window. So the clocks are cleaner in-sample than the folklore implies; the live
residual risk is (a) private-vendor subscriber leads on the 10:00 prints, and (b) posting-latency
jitter on Treasury results — not government leaks.

### Claims (ordered by load-bearingness for M20 bias)

**C1 [CONFIRMED] (T1, BLS/DOL, effective 2020-06-03): The DOL press lockup was permanently
discontinued; 8:30 BLS data (Employment Situation, CPI, PPI) now posts to the BLS website at
8:30:00 a.m. ET simultaneously to all, with NO early press access.** Electronics were first banned
from the lockup effective 2020-03-01; the facility itself was discontinued effective 2020-06-03.
Rationale stated: eliminate premature-disclosure risk and the "unfair competitive advantage given
to lock-up participants." — BLS "Changes to DOL Media Lockup" + Federal Register 2020-11297
(bls.gov, federalregister.gov). *Retrieval note: BLS pages 403 to automated fetch; facts confirmed
via BLS/FedRegister search-result summaries and the Federal Register docket number — tag the exact
date as T1-via-summary, verifiable at the cited URLs.*
→ **M20 impact:** removes any pre-2020 lockup-leak concern from the 8:30 class. But see C2.

**C2 [CONFIRMED — structural] (mechanics inference, T1 clock facts): The 8:30 releases fire ~60 min
before the 09:30 equity open, so M20's "8:30 as of the 09:30 open" read is NOT a 5-min impulse — the
reaction is already impounded in pre-market futures/ETFs and the opening auction.** A 09:30–09:35
cash window therefore measures *residual/opening-cross drift*, a categorically different (and
noisier, gap-contaminated) object than the 10:00/14:00 intraday impulse reads. — derived from the
8:30:00 vs 09:30:00 clock gap; no institutional source needed.
→ **M20 impact: DO NOT pool the 8:30 class with 10:00/14:00.** Treat 8:30 continuation as an
open-to-drift study with its own null, or exclude it.

**C3 [CONFIRMED] (T1/T2, NY AG + press, 2013-07-08): The University of Michigan / Thomson Reuters
elite tier that released consumer sentiment at 09:54:58 ET — two seconds before the 09:55:00
subscriber feed and ~65 s before the 10:00:00 public release — was terminated 2013-07-08 under the
Schneiderman agreement.** Elite HFT clients paid extra for the 2-second head start; trading volume
spiked up to 20× at 09:54:58. — NY AG press release 2013-07-08 (ag.ny.gov, T1); CNN/CNBC
2013-07-08 (secondary). *Elite tier ENDED 2013-07-08; distribution moved Thomson Reuters → Bloomberg
in Jan 2015.*
→ **M20 impact:** the 09:54:58 elite tier and the Thomson-Reuters 09:55 subscriber lead are **pre-
2020, i.e. OUT of M20's sample** — they do not bias a 2020–2026 10:00:00 UMich read. Historically
critical, in-sample benign. Residual: confirm no current Bloomberg terminal-vs-public lead (C4).

**C4 [PLAUSIBLE / partly UNVERIFIED] (T1, UMich): UMich sentiment currently releases at 10:00:00
a.m. ET (preliminary ~2nd Friday, final ~4th Friday), distributed via Bloomberg since Jan 2015; the
public data.sca.isr.umich.edu figures are embargoed and only appear ~4 weeks after the final
release.** — UMich Surveys of Consumers FAQ (data.sca.isr.umich.edu/faq.php, T1, confirms the 4-week
public embargo) + umich.edu news 2014 (Bloomberg partnership). *UNVERIFIED at T1: whether Bloomberg-
terminal subscribers get the 10:00 print microseconds/seconds before non-terminal channels in
2020–2026. No institutional page states a subscriber lead post-2015; treat the 10:00:00 wire instant
as the market clock.*
→ **M20 impact:** treat UMich 10:00:00 as clean in-sample, with a flagged residual (terminal lead)
that would bias the read if present. Sentiment prints are also the **lowest-N** 10:00 class
(twice-monthly), a power concern separate from mechanics.

**C5 [CONFIRMED] (T1, Federal Reserve, since 2013-03): FOMC statements release at 2:00:00 p.m. ET
for every scheduled meeting; the statement posts to federalreserve.gov at 2:00:00 simultaneously
with the physical press-lockup transmission.** SEP released alongside the statement on projection
meetings; Chair press conference ~2:30 p.m. — Federal Reserve monetary-policy release pages
(federalreserve.gov, T1); March 2013 procedural announcement standardizing 2:00 p.m.
→ **M20 impact:** 14:00:00 is the **cleanest anchor** — near-simultaneous website + wire hit,
minimal stagger. Good for a 14:00–14:05 read.

**C6 [CONFIRMED] (T1, Fed OIG, 2015): After a 2015-08-19 embargo break, the Board ceased using its
remote "embargo application" for FOMC-related and other market-moving releases as of 2015-08-21, and
relocated the press lockup room in Sept 2015 — since then FOMC-embargoed material is provided only
via the controlled physical lockup.** — Fed OIG "Board Controls Over Sensitive Economic Information,"
Apr 2016 (oig.federalreserve.gov, T1).
→ **M20 impact:** confirms tightened transmission controls are in force for the entire 2020–2026
sample; reinforces C5 (clean 14:00:00). This is the "mid-sample lockup change" — but it predates the
sample, so no within-sample protocol break on the Fed anchor.

**C7 [CONFIRMED — contamination flag] (T1 clock facts): The ~2:30 p.m. Chair press conference is a
second, often larger, information event ~30 min after the statement.** A 14:00–14:05 window is
clean, but ANY FOMC continuation window extending past ~14:25 is contaminated by the presser, not by
slow drift. — Fed release schedule (federalreserve.gov, T1).
→ **M20 impact:** cap FOMC continuation horizons at ≤25 min, or the "drift" is really presser
repricing. Directly relevant to a "minutes-to-hours" continuation thesis.

**C8 [CONFIRMED] (T1, TreasuryDirect): Competitive bidding for notes/bonds/TIPS closes at 1:00:00
p.m. ET; results post to TreasuryDirect "on a real-time basis as soon as available" — no embargo,
no lockup, a simultaneous public post.** Noncompetitive close is 12:00 noon ET. — TreasuryDirect
"Auctions In Depth" + "Today's Auction Results" (treasurydirect.gov, T1).
→ **M20 impact:** no leak/tier risk; the risk is posting-latency jitter (C9).

**C9 [PLAUSIBLE — variance flag] (T3 secondary; T1 gives no number): Treasury auction results
typically post within ~1–3 minutes of the 1:00 p.m. close (~13:01–13:03), with documented day-to-day
variance; TreasuryDirect's own pages state only "real-time as soon as available" and give NO fixed
latency.** — practitioner/aggregator sources cite "by 1:03" and "within 2–5 minutes"
(pagecrawl.io etc., secondary/T3). *TreasuryDirect (T1) does not commit to a minute.*
→ **M20 impact: a fixed 13:02:00 anchor can lead OR lag the actual post by 1–2 min on a given day.**
Prefer detecting the first-print/quote-dislocation timestamp per auction date over a hard-coded
13:02:00. Also: bill auctions and some cash-management bills close 11:30 a.m., and 10y/30y are often
*reopenings* on a Wed/Thu refunding cycle — the auctioned tenor and close time vary by security;
verify each date's schedule rather than assuming a 1:00 close.

**C10 [CONFIRMED] (T1): ISM Manufacturing PMI releases 10:00:00 a.m. ET (1st business day; ISM
Services 3rd business day) via the ISM site + PR Newswire; Conference Board Consumer Confidence
releases 10:00:00 a.m. ET (last Tuesday) via PR Newswire; BLS JOLTS releases 10:00:00 a.m. ET — all
simultaneous public posts, no documented tiered early access.** — ismworld.org, conference-board.org,
bls.gov release calendars (T1). *Note JOLTS is BLS but a **10:00** print (post-open, clean intraday),
unlike the 8:30 BLS class — it belongs with the 10:00 group, not the 8:30 group.*
→ **M20 impact:** 10:00:00 is a clean, well-populated anchor (ISM/CB/JOLTS give the most events).
Watch cross-contamination when two 10:00 releases land the same day (rare — different day-of-month
rules), and the ADP-day / same-morning 8:30-then-10:00 stacking.

**C11 [CONFIRMED — incidents, non-biasing for M20] (T2, DOL OIG via press, 2024): Three 2024 BLS
release failures were audited — (a) April CPI subset posted ~31 min early (2024-05-15); (b) Aug 2024
preliminary payroll-benchmark revision posted 34 min late but verbally given to users who called;
(c) methodology shared with external "super users" before publication.** BLS since closed IT gaps
and revised procedures. — Fox Business / PYMNTS / Bloomberg reporting on the DOL OIG report
(secondary; underlying = T2 OIG). *Little unusual pre-release tape on the CPI early post, per BLS.*
→ **M20 impact:** these are one-off anomalies on specific dates, not a systematic 8:30-tier. They do
not bias the fixed clock but argue for a per-date sanity check (drop dates with known early/late
posts). The 8:30 class is already de-prioritized by C2 regardless.

### Constraint gates (mechanics lens — PASS = "anchor clock is trustworthy")
| Gate | Result | Clause |
|---|---|---|
| 1 Latency | N-A | Mechanics modality; scheduled instant is the point — pre-positionable. |
| 2 Access | N-A | No order-type question here. |
| 3 Session | PASS/FLAG | 10:00 & 14:00 are RTH-clean; 8:30 is pre-open (Gate-3 tension — read is at/after 09:30 open). |
| 4 Data | PASS | Release timestamps are public/free; no purchase needed to fix the anchors. |
| 5 Fill realism | N-A | — |
| 6 Statistics | FLAG | UMich lowest-N (twice-monthly); 8:30 class should not be pooled → per-class N shrinks. |
| 7 Protocol | PASS | Each anchor's exact publication protocol is now stated at T1, as PROTOCOL requires. |

Survivor-profile score: **N-A** (mechanics modality returns no trade candidate; it conditions the
anchors other modalities' claims rest on). The one point I can assert cleanly is #2 (scheduled
decision instant) — every release here is a fixed-clock event, so 5–25 s manual latency is
pre-positionable, not a cost — *provided the anchor clock is the true dissemination instant, which
holds for 10:00/14:00 and holds for Treasury only within ±1–2 min.*

### Economics sketch (mechanics caveat only)
No gross/net estimate from this modality. The load-bearing contribution: **if M20 pooled the 8:30
class with the intraday anchors, any measured "continuation" would blend a clean 10:00/14:00 impulse
with a stale open-gap artifact — inflating or masking the true intraday effect.** Champion reference
for the lane (+2.5 bps/event dev, +12.5 holdout) is unaffected by this modality; my job is to ensure
the M20 numbers that feed the Stage-2 decision are read off trustworthy clocks. Bottom line for
synthesis: **trust the 10:00:00 and 14:00:00 event studies; treat 13:02:00 as ±1–2 min soft; quarantine
the 8:30/09:30 read.**

### Proposed next test
N-A (mechanics modality — no trade hypothesis). Operational recommendation to the orchestrator: (1)
split M20's release classes into {8:30-open-drift} vs {10:00/14:00 intraday impulse} with separate
nulls; (2) for Treasury, replace the hard 13:02:00 anchor with a per-date first-dislocation timestamp
and record the auctioned tenor/close-time; (3) add a per-date exclusion for the known 2024 BLS
early/late-post dates and any pre-2015 UMich date (moot for 2020–2026); (4) confirm at T1 whether any
2020–2026 10:00 print (UMich via Bloomberg, ISM) carried a paid-terminal lead over the free post —
the only live way a 10:00:00 read could still be biased.

### Sources
1. **T1** — BLS, "Changes to DOL Media Lockup" (electronics eliminated 2020-03-01); Federal Register
2020-11297, "Announcing Discontinuation of the DOL Lock-Up Facility" (discontinued eff. 2020-06-03).
bls.gov/bls/changes-to-dol-media-lockup-effective-march-1-2020.htm; federalregister.gov/documents/
2020/05/27/2020-11297/... *(BLS/FedRegister 403 automated fetch; date + docket confirmed via search
summaries — verifiable at URLs.)* Retrieved 2026-07-23.
2. **T1** — NY Attorney General, "A.G. Schneiderman Secures Agreement By Thomson Reuters To Stop
Offering Early Access To Market-Moving Information," 2013-07-08. ag.ny.gov/press-release/2013/
ag-schneiderman-secures-agreement-thomson-reuters-stop-offering-early-access. Retrieved 2026-07-23.
(Confirms 2-second elite tier; discontinued immediately 2013-07-08.)
3. **T2/secondary** — CNN Money & CNBC, 2013-07-08, on the 09:55 subscriber feed and 09:54:58 elite
tier. money.cnn.com/2013/07/08/investing/thomson-reuters-consumer-sentiment/; cnbc.com/2013/07/08/...
Retrieved 2026-07-23.
4. **T1** — University of Michigan Surveys of Consumers FAQ (public data embargoed 4 weeks after
final release). data.sca.isr.umich.edu/faq.php. Retrieved 2026-07-23. + umich.edu 2014 Bloomberg-
partnership announcement (news.umich.edu/bloomberg-to-release-u-m-surveys-of-consumers-starting-in-2015).
5. **T1** — Federal Reserve monetary-policy release pages (FOMC statement 2:00 p.m. ET; SEP; ~2:30
presser). federalreserve.gov/monetarypolicy/fomccalendars.htm and dated statement pages. Retrieved
2026-07-23.
6. **T1** — Federal Reserve OIG, "The Board Can Enhance Its Controls Over Sensitive Economic
Information," Apr 2016 (embargo-app ceased 2015-08-21 after 2015-08-19 break; lockup relocated Sept
2015). oig.federalreserve.gov/reports/board-controls-sensitive-economic-information-apr2016.htm.
Retrieved 2026-07-23. (PDF is binary-unreadable to fetch; HTML summary used.)
7. **T1** — TreasuryDirect, "Auctions In Depth" (competitive close 1:00 p.m. ET, noncompetitive 12
noon) & "Today's Auction Results" (real-time posting, no fixed latency). treasurydirect.gov/research-
center/history-of-marketable-securities/auctions/auctions-indepth/; treasurydirect.gov/auctions/
announcements-data-results/announcement-results-press-releases/auction-results/. Retrieved 2026-07-23.
8. **T3/secondary** — Treasury-auction timing aggregators citing ~13:01–13:03 / "within 2–5 min"
posting (pagecrawl.io). Labeled secondary; Treasury (T1) gives no minute. Retrieved 2026-07-23.
9. **T1** — ISM release calendar (10:00 a.m. ET, 1st business day mfg). ismworld.org/supply-management-
news-and-reports/reports/rob-report-calendar/. Conference Board Consumer Confidence 10:00 a.m. ET
(conference-board.org). BLS JOLTS 10:00 a.m. ET (bls.gov). Retrieved 2026-07-23.
10. **T2/secondary** — DOL OIG report on 2024 BLS release failures, via Fox Business / PYMNTS /
Bloomberg (April CPI ~31 min early 2024-05-15; Aug 2024 payroll-benchmark 34 min late; "super users"
methodology sharing). foxbusiness.com/economy/bls-took-steps-fix-data-release-failures-...;
bloomberg.com/news/articles/2024-05-16/us-bls-says-april-cpi-data-inadvertently-posted-30-min-early.
Retrieved 2026-07-23.

#### Queries used
- `University of Michigan consumer sentiment Thomson Reuters early access 2 seconds Schneiderman settlement 2013`
- `BLS press lockup ended 2023 embargo economic data release procedure change`
- `ISM Manufacturing PMI report release time 10:00 a.m. ET dissemination`
- `FOMC statement release 2:00 p.m. Federal Reserve media lockup embargo procedure`
- `Treasury auction results release time 1:00 pm 1:01 pm TreasuryDirect competitive results posting`
- `Conference Board Consumer Confidence Index release 10:00 AM ET distribution`
- `BLS CPI data released 30 minutes early 2024 accidental technical error website`
- `University of Michigan consumer sentiment release time 10:00 am preliminary 9:55 Bloomberg subscribers`
- `Federal Reserve Board embargo application press lockup economic data release procedures news organizations`
- `Treasury note auction close 1:00 pm results released within two minutes 13:02`
- `Federal Reserve 2013 FOMC statement early transmission Chicago changed release procedure self-release website 2:00:00`
- `Treasury marketable securities auction competitive bidding close 1:00 p.m. eastern results announced`
- Fetches: NY AG 2013 release; Fed OIG 2016 HTML; TreasuryDirect Auctions-In-Depth & Results;
  UMich FAQ; Fox Business 2024-incidents; Federal Register 2020-11297 (403/redirect).
