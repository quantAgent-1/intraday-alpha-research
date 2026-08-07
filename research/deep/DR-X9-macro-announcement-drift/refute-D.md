## DR-X9 — Refuter pass on Modality D (adversarial / prior-art)

Lane DR-X9-REFUTE. Per AGENT_BRIEF.md: unsourced/unreachable claims default REFUTED, not
PLAUSIBLE; maximum scrutiny because this verdict would BAN a registered family (M20 Stage-2).
Cross-checked against modality-D's own 10 claims via independent search + fetch, AND against
the actual M20 registered-trial primary source (`research/ledger.jsonl`,
`research/experiments/M20-sched-window/atlas_{train,validate}.md`) which modality-D did not
itself re-derive but which turns out to be the single most decisive, on-point piece of evidence
in this entire dossier. Also cross-read `refute-A.md` and `refute-BC.md` (already-completed
refuter passes on the sibling modalities) to avoid duplicated verification and to reconcile
citation conflicts across modalities.

### Verdict on modality-D's verdict

Modality-D's headline claims are **largely accurate at the abstract/headline level** — every
paper cited exists, is by the stated authors, in the stated venue (mostly), with numbers that
triangulate across 3+ independent secondary summaries each. But the **synthesis overstates how
directly these sources bear on the specific object** (single-name megacap **cash equity**
continuation at 15 min–4 h). Five of modality-D's ten claims are evidence from **index futures**
(ES, Treasury futures), not cash equities, and the report's executive summary blurs this
instrument-class boundary. One claim (C5/Rosa) is materially mis-described (wrong asset, wrong
signal). One claim (C4) silently splices numbers from two different papers under one citation.
The extrapolation from "≤1 s delay costs 3–7% of return" (C1) to "5–25 s residual is ~nil" is not
literally tested in the source. None of this changes the overall directional conclusion — but it
does mean modality-D's own claimed academic literature, read strictly, does **not** independently
clear the ≥2-unrefuted-on-point-kills bar for the **10:00 cluster** specifically. What *does*
clear it — and this is the single biggest finding of this refuter pass — is the **M20 registered
trial's own VALIDATE-stage sign reversal**, a direct, on-point, single-name-megacap-cash-equity,
pre-registered OOS test that modality-D did not incorporate into its claims list at all.

---

### C1 — Scholtus, van Dijk, Frijns (2014, JBF): 300ms→3.08%, 1s→7.33%, SPY cash ETF

**CONFIRMED (headline numbers) / EXTRAPOLATION FLAGGED (the "5–25s residual ~nil" inference).**

Triangulated across 6 independent search-summary sources (SSRN abstract page via search,
IDEAS/RePEc, EconPapers, AEA conference listing, and two independent WebSearch syntheses) — all
converge on the identical figures: "a delay of 300 milliseconds (1 second) significantly reduces
returns... by 3.08% (7.33%) compared to instantaneous execution," using **order-level data on the
S&P 500 ETF (SPY) traded on NASDAQ**, sample **January 6, 2009 – December 12, 2011**. Journal of
Banking & Finance 38 (2014): 89–105. This confirms modality-D's C1 numbers, asset class (cash ETF,
not futures), and sample period exactly.

**What I could not confirm, after exhausting available access:** the actual full-text
methodology. Direct fetch of the SSRN abstract page (403), the ScienceDirect DOI page (402
paywall), the Erasmus repository working-paper PDF (binary/compressed, unparseable by the fetch
tool), and a targeted re-search for the exact holding-period/exit definition all failed to
surface how "return" is defined in the delay-cost calculation — i.e., whether the reported
3.08%/7.33% reduction implies the price move is **~93–97% complete within 1 second** (which would
support modality-D's reading that nothing is left for a 5–25 s-late trader), or whether it
reflects a longer-horizon strategy return for which a 1-second entry delay is cheap precisely
*because* the position is held for much longer and the entry-price slippage is a small fraction of
total P&L (which would **undermine** the "nothing left" reading and argue the opposite — that
later entries still capture most of a longer-running move). Per AGENT_BRIEF: "never synthesize the
contents of a paywalled/unfetchable source." **The literal source only tests delays up to 1
second — nothing at 5 s or 25 s appears anywhere in any summary I could locate.** Modality-D's
sentence "at 5–25 s manual latency the residual is ~nil" is therefore an **inference beyond the
tested range**, not a reported finding. Downgrade from CONFIRMED to
**CONFIRMED-NUMBERS/UNVERIFIED-EXTRAPOLATION** — the extrapolation is plausible (concave decay
curves are the microstructure norm for macro-news price discovery) but is the author's own
inference layered on top of the paper, and should not be cited as if Scholtus et al. measured it.

### C2 — Kurov, Sancetta, Strasser, Wolfe (2019, JFQA): ~40% pre-release drift

**CONFIRMED, with an instrument-class correction modality-D already partially discloses but
under-weights in its synthesis paragraph.**

Confirmed via the ECB working-paper record (SSRN 2637528/2778549, EconPapers, ideas.repec.org) and
multiple independent search syntheses: sample **2008–2014**, **30 US macro announcements**
examined, of which **7–9 of 18–20 "market-moving" releases** show statistically significant
pre-announcement drift, price begins moving ~30 min before release, and the pre-drift averages
**~40% of the total price adjustment**. Journal of Financial and Quantitative Analysis 54(1):
449–479. This matches modality-D's C2 numbers and sample period.

**Correction:** the tested instruments are **E-mini S&P 500 futures and 10-year Treasury futures**
— confirmed identically across three independent sources — **not cash equities**. Modality-D's
own claim text says this correctly ("in E-mini S&P and 10y Treasury futures"), but the report's
executive-summary paragraph opens with "the price reaction to scheduled macro news completes in
the first second **in cash SPY**" (true only of C1) and then folds C2's futures-only 40%-pre-drift
finding into the same sentence as if both describe the same instrument. The ES/SPX cash-futures
basis is extremely tight (sub-second, continuously arbitraged), so transferring an **index-level**
futures finding to SPY/QQQ cash is a reasonable, low-risk step. Transferring it to **single
megacap names** (NVDA, TSLA, AMD, MU, GOOGL) is a materially bigger inferential leap — an
individual stock's idiosyncratic component is not pinned to the index the way SPY is — and this
is exactly the gap modality-D's own C10 admits ("single-name megacap continuation... is
essentially unstudied"). The correction here is about the summary framing eliding this
distinction, not the underlying claim being wrong.

### C3 — Baglioni & Ribeiro, "The FOMC Announcement Reversal": confirmed, still unpublished

**CONFIRMED (numbers, sample, mechanics) / FLAG STANDS (publication status).**

Confirmed via SSRN (4182628) and independent search: sample **1997–2020, 180 scheduled FOMC
meetings**, strategy is **buy/sell E-mini S&P 500 just before the announcement** (sized off the
sign of the pre-announcement move, contrarian), **closed at end of trading day**, generating
Sharpe ratios **>2.5×** the pre-FOMC drift's own Sharpe. This is a genuine, on-point, long-sample
finding that the pre-2pm move tends to **reverse**, not continue, over the subsequent ~2 hours to
the close — a horizon squarely inside the "minutes–hours" scope this charge cares about.

Two things to weigh: (1) instrument is **E-mini S&P futures**, same index-vs-single-name caveat as
C2 above. (2) I re-searched specifically for a journal placement as of today (2026-07-23) and
found **none** — the paper remains an SSRN working paper roughly 4 years after its August 2022
posting date, with no citation trail to a peer-reviewed venue in any search result. Modality-D
already flags this ("not yet journal-published") — I confirm the flag still holds and, given the
elapsed time, would treat it as slightly weaker T2/T3-boundary evidence than modality-D's citation
tier implies, though not as disqualifying (SSRN-only status after 4 years is more often stalled
submission/co-author inertia than a rejected-for-cause result, and I found no retraction, erratum,
or critical response).

### C4 — Kurov, Wolfe, Gilbert (2021, FRL): pre-FOMC drift decay — CITATION SPLICE FOUND

**CONFIRMED IN SUBSTANCE (decay is real) / MISATTRIBUTED AS SOURCED — the "49 bps" figure and its
"1994–2011" period belong to a *different* paper than the one cited.**

Direct fetch of the PMC open-access mirror (pmc.ncbi.nlm.nih.gov/articles/PMC7525326/) confirms
Kurov, Wolfe, Gilbert's own before/after comparison is: **44.5 bps** mean pre-FOMC return in
**April 2011–December 2015** (press-conference meetings) collapsing to **9.2 bps**, statistically
indistinguishable from non-announcement days, in **January 2016–December 2019**. This matches
`refute-A.md`'s independent fetch of the same paper exactly (44.5→9.2, same sub-periods).

Modality-D's C4 instead writes: "mean 24 h pre-FOMC S&P return fell from **~49 bps (0.49%) in
1994–2011** to **~9 bps (0.09%)**... — Kurov, Wolfe, Gilbert." **The 49 bps / 1994–2011 figure is
not in the Kurov-Wolfe-Gilbert paper at all** — it is Lucca & Moench (2015)'s original whole-sample
average (Sept 1994–March 2011), a separate, earlier paper (confirmed via `refute-A.md`'s direct
quote of the number from the Hu-Pan-Wang-Zhu working paper, and independently via multiple
secondary summaries). Modality-D has spliced Lucca-Moench's headline number and period onto
Kurov-Wolfe-Gilbert's citation, producing an apparent single continuous 25-year decay series
(49→9 bps) that neither individual paper actually reports — KWG's own decay comparison is
44.5→9.2 bps over a much shorter, later window (2011–2019). The **9 bps end-point and the decay
conclusion are correct** in both framings; the **49 bps start-point and its attribution are
wrong as cited.** This is worth fixing before this claim is used as a load-bearing number
elsewhere — cite Lucca-Moench separately for the 49 bps/1994-2011 figure, and Kurov-Wolfe-Gilbert
separately for the 44.5→9.2 bps/2011-2019 decay.

### C5 — Rosa (2022, JFM): OOS failure — WRONG ASSET AND WRONG SIGNAL AS DESCRIBED

**PARTIALLY REFUTED — the OOS-kill finding is real, but modality-D mis-describes both the
instrument and the signal being killed.**

Modality-D's C5 text: "Intraday-momentum predictability (**first-half-hour → last-half-hour
class**) disappears out-of-sample... Rosa, 'Understanding intraday momentum strategies.'"
Independent triangulation (three separate search queries, converging results) establishes that
Rosa (2022), Journal of Futures Markets 42(12): 2218–2234, tests the **overnight return → last
half-hour return** variant (a related but distinct specification — first documented as its own
object, "Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return," is a
*different, earlier* paper), using **5-minute prices on E-mini S&P 500 futures contracts** — not
the cash SPY ETF that the original Gao-Han-Li-Zhou (2018) paper used. A Markov-switching model
finds the predictability is regime-dependent and a naive always-on strategy's predictability
"disappears" in calendar-time OOS evaluation, though a threshold-gated strategy still extracts
returns in the high-signal regime.

Consequence for modality-D's own C5+C6 pairing ("the most parsimonious read of the M20 10:00-
cluster... is intraday momentum on macro days — a known effect that fails OOS"): this chain
requires Rosa's OOS-kill to apply to *the same* signal/asset that Gao et al. document as macro-day-
enhanced. It does not, exactly — Gao et al.'s macro-day-enhancement finding is on the **cash SPY
ETF, first-half-hour signal**; Rosa's OOS-kill is on **E-mini futures, overnight-return signal**.
The two papers are close cousins (same authorship lineage, overlapping literature, and the
overnight return substantially overlaps with Gao's own "first-half-hour-measured-from-prior-close"
definition), so the read is a *reasonable* steelman, not a fabrication — but it is an analogy
across instrument and signal, not a demonstrated OOS failure of the exact cash-equity effect Gao
et al. reported. Downgrade from CONFIRMED to **CONFIRMED-WITH-MISDESCRIPTION** — correct the
asset/signal labels; keep the analogical argument but flag it as analogical.

### C6 — Gao, Han, Li, Zhou (2018, JFE): momentum stronger on macro days

**CONFIRMED, with a useful added detail modality-D doesn't state precisely.**

Confirmed via three independent sources: JFE 129(2): 394–414 (2018), sample **1993–2013**, **S&P
500 ETF (SPY)** — cash — high-frequency data; signal is the **first half-hour return "as measured
from the previous day's market close"** (i.e., includes the overnight gap) predicting the last
half-hour return; effect is stronger on high-volatility, high-volume, recession, and **major
macroeconomic-news-release days**; also replicated on 10 other actively-traded domestic/
international ETFs. R² rises to 3.3% under high first-half-hour volatility. Confirmed:
**index/ETF level only** — no individual-stock test is reported anywhere I could find, which
directly corroborates modality-D's own C10 admission that single-name continuation is
unstudied, and reinforces (rather than weakens) the case that C6's macro-day-enhancement finding
does not, by itself, establish anything about NVDA/TSLA/AMD/MU/GOOGL specifically.

### C7 — McLean & Pontiff (2016, JF): 26%/58% decay

**CONFIRMED exactly.** Journal of Finance 71(1): 5–32 (2016), 97 cross-sectional return
predictors, portfolio returns **26% lower out-of-sample**, **58% lower post-publication**
(implying ~32 points attributable to publication-informed trading beyond pure overfitting).
Matches modality-D precisely; no correction needed.

### C8 — DOL/BLS lock-up discontinuation (2020)

**CONFIRMED — and independently upgraded to direct T1 by `refute-BC.md`, which I cross-checked.**
`refute-BC.md` fetched the actual Federal Register text (govinfo.gov mirror) directly and quotes
verbatim: *"As of June 3, 2020, DOL will permanently discontinue use of the lock-up facility"*,
which supersedes a Feb 7, 2020 notice of intent to ban electronics effective March 1, 2020, with
an intervening COVID-driven facility suspension around March 20, 2020. Modality-D's "suspended 20
Mar 2020, made permanent 3 Jun 2020" phrasing matches this timeline once the electronics-ban vs.
facility-suspension vs. permanent-discontinuation steps are correctly sequenced. No correction
needed beyond noting the fuller T1 chain now available in `refute-BC.md`.

### C9 — "Drift Begone!" (Kurov, Sancetta, Wolfe, JIMF 2022)

**UNVERIFIABLE BEYOND ABSTRACT, as modality-D already flags.** I independently attempted the
Skidmore working-paper PDF mirror and hit the same wall modality-D disclosed (binary/compressed,
unparseable). No magnitudes extracted; the qualitative claim (ending early-access release policies
weakened pre-announcement drift) is consistent with the broader literature (C3, C4) but stays
**PLAUSIBLE**, not CONFIRMED, exactly as modality-D already labeled it. No change.

### C10 — Treasury-auction spillover / single-name continuation: genuinely UNKNOWN

**CONFIRMED as a genuine gap — independently corroborated three separate ways.** (1) My own
search pass for Treasury-auction-result (13:01–13:03 ET) → equity minutes-hours spillover
surfaced nothing beyond bond-market-only studies. (2) `refute-A.md` ran a dedicated 8-query search
specifically for this object and reports the same null result, with two near-misses
(Fleming-Liu-Nguyen: bond-market-only; Phillot 2025: auction-*announcement* shocks via local
projection at macro, not sub-day, horizons) that don't satisfy the claim. (3) The M20 registered
trial's own `tsy_auction_1300` cells (single-name cash equities, the actual object) never
screen-passed at TRAIN — directionally positive at every horizon (C2 h60 +24.3 bps) but every CI
spans zero (e.g. [-8.1, +56.8]) — and consequently never reached the VALIDATE stage at all. Three
independent lines (external academic, external academic, internal registered trial) all land on
"not found / underpowered," not "killed." This class is correctly labeled UNKNOWN, and should stay
that way — it is the one class where the field genuinely has nothing to say, for or against.

---

### The claim modality-D omitted: the M20 registered trial's own VALIDATE result

Modality-D's gate-6 clause reads: *"M20 3-mo VALIDATE confirmed same-sign at ~zero power (N≈43/15
sess, se≈18 bps)."* I read the primary source directly — `research/ledger.jsonl` (trial
`M20-sched-window-atlas-v1`) and `research/experiments/M20-sched-window/atlas_{train,validate}.md`
— which are fully accessible (not paywalled) and give the exact numbers behind this clause.

**The N/session/se figures are correct** (N=43, 15 sessions, VALIDATE CI half-width implies
se≈18 bps at h30). **The characterization "confirmed same-sign" is factually wrong — the ledger's
own result entry states the opposite:**

> `train`: SCREEN-PASS 2/40 cells — **cluster_1000|C2|h30 mean +9.27 bps [0.16, 18.37], N=1136/366
> sessions; cluster_1000|C2|h60 +12.93 bps [0.63, 25.22], N=1138/366.**
> `validate`: h30 **-3.84 bps** [-39.1, +31.5]; h60 **-7.44 bps** [-50.9, +36.0], N=43/15 sessions.
> **"validate_confirm=false on the SAME-SIGN prong per the frozen rule."**
> `disposition`: "Family closed... no Stage-2 registration permitted."

The TRAIN screen was **positive** (barely — CI lower bound 0.16 and 0.63 bps, i.e. grazing zero);
the VALIDATE look **flipped sign to negative** and explicitly failed on the same-sign prong, per
the ledger's own words — not "same sign but underpowered," but a genuine reversal. This is a
**stronger** kill of the 10:00-cluster continuation hypothesis than modality-D's own mischaracter-
ization suggests, and it is far more on-point than any external paper cited in modality-D's ten
claims: it is (a) single-name megacap (NVDA/TSLA/AMD/MU/GOOGL — the exact universe), (b) cash
equity, (c) a pre-registered TRAIN/VALIDATE split with frozen thresholds, (d) exactly the 10:00
release cluster (ISM/UMich/JOLTS/CB-confidence) at 30–60 min horizons. Nothing in modality-D's
external literature comes this close to the actual object.

I also pulled the other three classes' TRAIN cells for completeness, since they bear directly on
the decisive question below:

- **`fomc_stmt`** (FOMC 14:00): every TRAIN cell **negative mean** at every horizon (e.g. C2|h60:
  **-51.07 bps** [-119.9, +17.8]); ledger's own annotation: **"reversal shape."** This directly
  corroborates Baglioni-Ribeiro's academic reversal finding (C3) — but this time in cash
  single-name equities, not futures — materially strengthening class (a) beyond what the
  external literature alone establishes.
- **`pre_open_0830`**: TRAIN means cluster near zero at every horizon (e.g. C1|h30: **+1.25 bps**
  [-7.3, +9.8], N=1471/301 sessions) — flat/null, never screen-passing. Corroborates the
  "stale, already-impounded" story for class (b) directly on cash single names, where the
  external literature (futures-only pre-drift studies) is at best an inferential match.
- **`tsy_auction_1300`**: see C10 above — positive-lean, never significant, never validated.

Per the WAVE5_PLAN pre-commitment text itself, this Stage-1 screen is nominally meant to stand as
"coverage documentation only," with the field verdict supposed to rest on external literature. In
practice it is the single most decisive fact available to answer the charge's question, and no
adversarial review of this charge should omit it.

---

### Decisive question: does the ≥2-unrefuted-OOS-kill bar hold, per class?

**(a) FOMC 14:00 — HOLDS (confidence MED-HIGH).** Baglioni-Ribeiro's 180-meeting, 23-year reversal
finding (futures, unpublished-after-4-years caveat) + Scholtus's cash-equity speed/crowding
argument + Kurov-Wolfe-Gilbert's confirmed pre-drift decay, **now corroborated by M20's own
single-name cash-equity TRAIN data showing a uniform negative/reversal shape at every horizon**
— this is the best-supported of the four classes, combining external and internal, futures and
cash, evidence that all point the same direction.

**(b) 8:30-at-open — HOLDS (confidence MED).** The external literature here is thin and
futures/pre-market-mismatched for the specific cash gap-at-open mechanic (SPY/single-name
pre-market liquidity is much thinner than the ES/Treasury-futures venues the pre-drift papers
actually use, a caveat modality-D does not raise). The bar holds mainly because **M20's own
`pre_open_0830` cash single-name data is flat/null across 1,471+ events / 301 sessions on TRAIN**
— direct, on-point, negative evidence — not because the external academic citations transfer
cleanly to this specific mechanic.

**(c) 10:00 cluster — HOLDS, but NOT on modality-D's academic citations alone (confidence MED, not
MED-HIGH).** Read strictly, modality-D's own external sources deliver **at most one** genuinely
on-point OOS-kill paper for this class (Rosa 2022), and it is instrument- and signal-mismatched as
detailed in C5 above (E-mini futures, overnight-return signal, not cash SPY, first-half-hour).
Kurov 2019 (C2) documents pre-drift, not a post-hoc kill; Gao et al. (C6) is a *positive* finding,
not a kill. So the academic literature alone does not cleanly clear "≥2 unrefuted OOS kills"
*specifically* for this class. What clears it is the **M20 registered trial's own VALIDATE-stage
sign reversal** — a direct, pre-registered, on-point OOS kill in exactly this asset class and
release cluster, which the WAVE5 protocol nominally treats as "coverage documentation" separate
from the field-verdict, but which functionally is by far the strongest evidence available. Net:
the *conclusion* (no continuation to harvest at 10:00-cluster minutes-hours) is well-supported;
the *route* modality-D takes to reach it (via external OOS kills) is weaker than claimed, and the
real load-bearing evidence sits inside the project's own already-spent Stage-1 screen.

**(d) 13:02 Treasury results — DOES NOT HOLD; remains genuinely UNKNOWN, not killed.** Zero
academic sources found (three independent search efforts, including a dedicated one in
`refute-A.md`, agree). The internal `tsy_auction_1300` cells are directionally positive at every
horizon but never reach significance and never reach VALIDATE. This class has 0, not ≥2, kills —
modality-D already labels it UNKNOWN correctly and I confirm that label stands; any future work on
this class should be flagged UNDERPOWERED-BY-DESIGN / genuinely open, not folded into the
"exhausted" verdict for the other three classes.

### Sources (this pass; numbered, tiered, dated — searches/fetches run 2026-07-23)

1. Scholtus, van Dijk, Frijns (2014), *J. Banking & Finance* 38:89–105 — T2, headline numbers
   confirmed via 6 independent secondary summaries (SSRN 2174901, IDEAS/RePEc, EconPapers, AEA
   conference page); full text unobtainable (SSRN 403, ScienceDirect 402, Erasmus repub.eur.nl
   working-paper PDF binary/unparseable) — methodology detail behind the 5–25s extrapolation
   UNVERIFIED.
2. Kurov, Sancetta, Strasser, Wolfe (2019), *JFQA* 54(1): 449–479 — T2, confirmed via SSRN
   2637528/2778549, ECB WP 1901, EconPapers; futures-only instrument confirmed.
3. Baglioni & Ribeiro, "The FOMC Announcement Reversal," SSRN 4182628 (posted Aug 2022) — T2/T3
   working paper; re-confirmed still unpublished as of 2026-07-23, no journal venue located.
4. Kurov, Wolfe, Gilbert (2021), *Finance Research Letters* 40 — T2, full text via PMC mirror
   (pmc.ncbi.nlm.nih.gov/articles/PMC7525326/), directly fetched; 44.5→9.2 bps confirmed; 49
   bps/1994-2011 figure identified as belonging to a different paper (Lucca & Moench 2015), not
   this one — citation splice found in modality-D's C4.
5. Rosa (2022), *J. Futures Markets* 42(12): 2218–2234 — T2, confirmed via econpapers.repec.org
   and independent search triangulation; instrument = E-mini S&P 500 futures, signal =
   overnight-return→last-half-hour, NOT cash SPY first-half-hour as modality-D's C5 states.
6. Gao, Han, Li, Zhou (2018), *J. Financial Economics* 129(2): 394–414 — T2, confirmed via SSRN
   2440866 and independent search; SPY ETF cash, 1993–2013, first-half-hour-from-prior-close
   signal, index/ETF-level only (no individual stocks tested).
7. McLean & Pontiff (2016), *J. Finance* 71(1): 5–32 — T2, confirmed exactly (26%/58%).
8. Federal Register 2020-11297 (DOL lock-up discontinuation) — T1, cross-confirmed via
   `refute-BC.md`'s direct govinfo.gov fetch; timeline (electronics ban intent Feb 7 2020 → Mar 1
   2020 planned effective → Mar 20 2020 COVID suspension → Jun 3 2020 permanent) matches
   modality-D's dates once correctly sequenced.
9. Kurov, Sancetta, Wolfe, "Drift Begone!," *J. Int'l Money & Finance* — T2, abstract-only;
   Skidmore working-paper PDF mirror re-attempted and confirmed unparseable, same limitation
   modality-D already disclosed.
10. `research/ledger.jsonl` (trial `M20-sched-window-atlas-v1`, registered 2026-07-22, closed
    2026-07-22) and `research/experiments/M20-sched-window/atlas_train.md`,
    `atlas_validate.md` — T1 (in-house primary data), fetched directly, not paywalled. Source of
    the VALIDATE sign-reversal finding and the per-class TRAIN cell breakdown used in the
    decisive-question section above.
11. `research/deep/DR-X9-macro-announcement-drift/refute-A.md`, `refute-BC.md` — sibling
    refuter passes, cross-read to reconcile citation conflicts (C4's Lucca-Moench/Kurov-Wolfe-
    Gilbert splice; C8's DOL timeline) and to avoid duplicated verification of Modality A/B/C's
    own claims (out of this charge's scope).
12. `research/deep/WAVE5_PLAN.md` — primary source for the exact pre-commitment bar text
    ("≥2 unrefuted OOS kills covering our release classes") being adjudicated here.

#### Queries used
- `Scholtus van Dijk Frijns "Speed, algorithmic trading, and market quality around macroeconomic news announcements" SPY 300ms 1 second delay`
- `"Scholtus" "van Dijk" "Frijns" 2014 macroeconomic news announcements strategy "five minutes after" OR "5 minutes after" OR "one minute" return abnormal`
- `"Scholtus" "van Dijk" macroeconomic news "cumulative return" "t + 1 second" OR "within 1 second" OR "1000 milliseconds" price adjustment complete`
- `Kurov Sancetta Strasser Wolfe "Price Drift before U.S. Macroeconomic News" JFQA E-mini S&P Treasury futures 40 percent pre-announcement`
- `"Kurov" "Sancetta" "Strasser" "Wolfe" JFQA 2019 "18" announcements "7" significant pre-announcement drift stock index Treasury futures`
- `Baglioni Ribeiro "FOMC Announcement Reversal" SSRN 4182628 ES futures 1997 2020 180 meetings Sharpe`
- `"Baglioni" "Ribeiro" FOMC announcement reversal published journal 2023 2024 SSRN working paper not yet published`
- `Rosa 2022 "Journal of Futures Markets" intraday momentum out-of-sample "42" "2218" fails predictability`
- `Rosa "Understanding intraday momentum strategies" abstract "first half-hour" OR "overnight" return "last half-hour" S&P 500 futures sample 1998`
- `"Rosa" 2022 intraday momentum "first half-hour" "opening" return predicts "closing half-hour" E-mini S&P 500 futures sample period out-of-sample`
- `Gao Han Li Zhou "Market Intraday Momentum" Journal of Financial Economics 2018 macroeconomic news announcement days stronger`
- `Gao Han Li Zhou 2018 "market intraday momentum" "individual stocks" OR "individual equities" tested robustness macroeconomic announcement magnitude R-squared`
- `McLean Pontiff "Does Academic Research Destroy Stock Return Predictability" 26 percent 58 percent decay in-sample out-of-sample post-publication`
- `DOL lock-up facility discontinued news media 2020 BLS economic data release "suspended" "permanent" embargo effective date`
- `Kurov Sancetta Strasser Wolfe JFQA 2019 pre-announcement drift "after the announcement" OR "post-announcement" price adjustment continues reversal`
