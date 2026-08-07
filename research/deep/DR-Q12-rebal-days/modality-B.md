## DR-Q12 — B primary/venue findings

### Verdict recommendation
**OPEN-TESTABLE** (confidence **HIGH**) — Official index-provider and exchange primary sources fully pin **event-date definitions** for S&P quarterly rebal, Nasdaq-100 rebal/reconstitution, Russell reconstitution, and quad-witching, and confirm that **closing-auction cutoffs and NOII schedules are unchanged** on those days (operational contingency/staffing only). Calendar-conditioned tests on owned Nasdaq NOII are mechanically feasible with a-priori event flags; month/quarter-end lacks a T1 index-provider calendar (define as last RTH session of calendar month/quarter). No new edge is claimed here — this charge is **calendar infrastructure for a registered trial**.

What would flip it: Discovery that a venue (or broker) **alters MOC/LOC cutoffs or NOII dissemination** on rebal days in a way that invalidates the champion 15:55:10 snapshot protocol (not found in T1; Nasdaq ETA 2026-32 states cutoffs unchanged).

### Mechanism
**Who pays:** Price-insensitive passive / benchmarked AUM (index funds, ETFs, quant mandates) forced to match index membership and weights at the official close used for the rebalance/reconstitution print. On quad-witch days, additional price-insensitive derivatives settlement and delta-hedge flows hit opens (index futures/options) and closes (equity options). Month/quarter-end institutional book rebalancing is real but **not** a venue-defined auction event.

**Why price-insensitive:** Tracking-error minimization and mandate compliance dominate price; execution is concentrated in the closing auction so NAV/index marks align.

**Why persists:** Methodologies are rules-based and publicly scheduled; AUM benchmarked to S&P/Russell/NDX remains enormous (Russell alone cites ~$12T+ historically). Semi-annual Russell (from 2026) doubles reconstitution days without removing the close-print mechanism.

**Capacity intuition:** Event days are few (≈4–8 index rebal days/year + ~12 month-ends + 4 quarter-ends with heavy overlap). Edge for our size is not capacity-bound; power is (n of event-day sessions on owned NOII).

### Claims
C1 [CONFIRMED] (T1, methodology current as of 2026 copyright, sample N/A rules): **S&P U.S. equity index quarterly rebalancing is effective after the close on the third Friday of March, June, September, and December** — that close is the MOC flow day for passive tracking. — S&P DJI U.S. Indices Methodology (quoted across SPDJI methodology family / prospectus extracts): “The index rebalances quarterly, effective after the close on the third Friday of March, June, September, and December.” https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-us-indices.pdf

C2 [CONFIRMED] (T1, 2026 methodology, sample N/A): **Nasdaq-100 reconstitution is annual in December; rebalance is quarterly.** Reference dates: last trading day of Nov (recon) / last trading day of Feb, May, Aug, Nov (rebal). Announcement: after close on the **sixth trading day prior** to effective date. **Effective: at market open on the first trading day following the third Friday** of Mar/Jun/Sep/Dec. Therefore the **MOC trading day for index-fund rebalance is the third Friday** (close used before open effective). — Nasdaq-100 Index Methodology (NDX®), Index Calendar table, p.8. https://indexes.nasdaq.com/docs/Methodology_NDX.pdf

C3 [CONFIRMED] (T1, Mar 2 2026 press + LSEG hub): **Russell US Indexes reconstitution (2026+ semi-annual June & December)** takes effect **after US market close** on the provider-specified Friday; new membership from the next open. **June 2026:** rank day Thu Apr 30; prelims from May 22 (then May 29, Jun 5, 12, 18); lock-down from Mon Jun 8; **final after close Fri Jun 26**; open Mon Jun 29. **December 2026 (revised schedule):** effective after close **second Friday December (Dec 11, 2026)**; reflected open Mon Dec 14. Historically annual fourth Friday of June. FTSE FAQ: “Changes to the Russell Indexes are implemented after the close of US markets on the fourth Friday in June” (June cycle). — https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/russell-reconstitution-2026-schedule ; https://www.lseg.com/en/ftse-russell/russell-reconstitution ; FTSE notice id=2617649

C4 [CONFIRMED] (T1, venue + industry convention): **Quad-witching / triple-witching = third Friday of March, June, September, December** (equity options, index options, index futures expire together; “quadruple” adds single-stock futures where listed). If that Friday is a full market holiday (e.g., Juneteenth when it falls Fri/Sat), expiration may move to the prior business day (e.g., 2026 June often cited as Thu Jun 18). Index futures/options settle off the **open**; single-stock options via **close**. — Nasdaq article on triple witching mechanics; NYSE RM-26-03 Quarterly Expiration Day Mar 20 2026; conventional Cboe/OCC calendars.

C5 [CONFIRMED] (T1, Nasdaq ETA 2026-32, Jun 23 2026): **On Russell reconstitution day Nasdaq does not change Closing Cross cut-off times or threshold percentages.** Standard timeline restated: 3:50 ET early NOII / freeze cancel-modify of MOC·LOC·IO; 3:55 full NOII + stop MOC; LOC until 3:58; IO until 4:00; cross 4:00. Contingency plan published for capacity failure; no Market-Wide Call. Same pattern historically for S&P rebal + quad-witch alerts (e.g., ETA 2020-83). — https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2026-32

C6 [CONFIRMED] (T1, Nasdaq Opening/Closing Cross FAQs ©2025 + trader.aspx openclose): **Nasdaq Closing Cross NOII:** disseminate 3:50–4:00 ET (every 10s 3:50–3:55; every 1s 3:55–4:00 with Near/Far indicative). MOC must be received prior to 3:55; LOC prior to 3:58 (late LOC re-priced vs 3:50/3:55 refs); IO until 4:00; cancel/modify of on-close orders freezes at 3:50. Cross sets Nasdaq Official Closing Price (NOCP). — https://www.nasdaqtrader.com/trader.aspx?id=openclose ; openclose_faqs.pdf

C7 [CONFIRMED] (T1, NYSE auctions page + RM-26-03 Mar 20 2026): **NYSE closing auction cutoffs are the same on quarterly expiration days as on ordinary days** (Rule 7.35B). MOC/LOC entry cutoff = Closing Auction Imbalance Freeze Time = **10 minutes before scheduled end of Core Trading Hours** (3:50 on full days). After 3:50: only MOC/LOC opposite a published Significant Closing Imbalance; Closing IO both sides until 4:00; no cancel/reduce after 3:50 (limited legitimate-error exception). Significant Closing Imbalance: notional ≥ $200k **and** ≥30% of 20-day avg closing size (S&P 500), 50% (S&P 400/600), 70% (other). Memo emphasizes staffing/volume, not rule changes. — https://www.nyse.com/trade/auctions ; https://www.nyse.com/publicdocs/nyse/markets/nyse/rule-interpretations/2026/Q1_2026_Quarterly_Expiration_RM_3.20.2026.pdf

C8 [CONFIRMED] (T1, S&P methodology / prospectus extracts of share-IWF freeze): **S&P share/IWF freeze** begins after close on the Tuesday prior to the second Friday of the rebalancing month and ends after close on the third Friday; pro-forma files generally after close first Friday of rebal month (~two weeks before effective). Membership adds/deletes typically announced ~five trading days before effective (practice; corporate-action adds may differ). Suspended freeze-period changes announced on third Friday and implemented **five business days after** quarterly rebal effective date. — SPDJI methodology language as quoted in structured-product prospectuses / S&P consultation docs.

C9 [PLAUSIBLE] (T1 fee schedule language + industry practice; not a mechanics change): Nasdaq trading **price list flags elevated/special treatment days** including third Friday of Mar/Jun/Sep/Dec (options/futures expiration), MSCI rebalance dates, S&P 400/500/600 rebal dates, Nasdaq-100/Biotech rebal dates, and Russell reconstitution date — confirming venue treats these as known high-volume closes without changing auction algorithm cutoffs. Month/quarter-end portfolio rebalancing is **not** a T1 exchange-calendar event; define operationally as last RTH trading day of calendar month (ME) / Mar·Jun·Sep·Dec (QE). — nasdaqtrader.com PriceListTrading2

C10 [CONFIRMED] (T1, FTSE Russell FAQ on LSEG reconstitution hub): **Russell reconstitution day closing volume is extreme** — June 2025: ~$114.7B NYSE + ~$102.5B Nasdaq in closing moments (provider-stated). Mechanism = forced passive MOC at the reconstitution close. — https://www.lseg.com/en/ftse-russell/russell-reconstitution

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **PASS** | Decision instant is scheduled (15:55:10 NOII vs mid on pre-flagged event calendar); 5–25 s manual is pre-positionable. |
| 2 Access | **PASS** | Same MOC/LOC/taker path as champion; retail brokers offer on-close types (cutoffs broker-specific — verify separately). |
| 3 Session | **PASS** | Flat at 16:00 cross via on-close / taker-to-cross; in-mission. |
| 4 Data | **PASS** | Owned Databento Nasdaq NOII 2020→2026 + SIP history; event flags free from public calendars (no new $). |
| 5 Fill realism | **PASS** | Same single-print closing cross as champion; no continuous-fill ambiguity. |
| 6 Statistics | **PASS** (event-stratified) / **UNDERPOWERED-BY-DESIGN** if only rare days | Full history: ~1,500 sessions; rebal/witch subset ~4–16 days/year → n≈40–100 event days on 2020–2026 NOII (power thin for rare strata alone; use as **conditioning factor** on full n, not standalone). Month-end ~12/yr better powered. |
| 7 Protocol | **PASS** | Named payer (index MOC rebal / expiry hedge / calendar book rebal) stateable a priori; pre-register event definitions below; charges calendar-conditioning / auction-meta family. |

**Survivor-profile score: 5/5**
1. Single-print auction execution — **yes** (same as champion)
2. Scheduled decision instant — **yes** (calendar + 15:55:10)
3. Named price-insensitive payer — **yes** (indexed MOC / expiry)
4. Testable on owned/≤$100 data — **yes** (owned NOII)
5. Expected effect ≥2× cost burden — **unknown a priori** (this charge is date definition, not edge estimate); test decides

### Economics sketch
Expected gross: **UNKNOWN from T1** (this modality is calendars/rules only; economics require NOII stratification — other modalities / own trial). Cost burden: identical to champion structure (taker into close / MOC path; zero commission through 2026-12-31 promo). Net prior: no independent prior; champion = **+2.5 bps/event dev / +12.5 bps/event holdout**. Hypothesis for trial: event days change basis distribution / hit-rate / meta-filter value (amplify, mute, or leave unchanged) — not a new standalone mean claim.

### Proposed next test (OPEN-TESTABLE)
**Hypothesis:** On pre-registered calendar event days, the champion 15:55:10 NOII basis signal has a **different mean bps/event and/or hit-rate** than non-event days (direction a priori open: “different,” not “better”). Named payer: indexed MOC rebalance flow (S&P/NDX/Russell) and/or quad-witch equity-option close hedge; secondary: month-end institutional book flow.

**Data needed:** Owned Databento Nasdaq NOII + owned SIP mid at 15:55:10; $0 incremental.

**Universe:** Same 5 core + M11 28-name Nasdaq-listed set (where NOII owned).

**Event flags (a-priori definitions for trial registration — use MOC trading day):**
1. **SPX_REBAL** = session date is third Friday of {Mar, Jun, Sep, Dec}, or prior RTH day if that Friday is a full market holiday.
2. **NDX_REBAL** = same calendar rule as SPX_REBAL (MOC day = third Friday; index effective next open). December also = NDX annual reconstitution.
3. **RUSSELL_RECON** = provider published reconstitution effective close date (historically fourth Friday of June; 2026: Jun 26 and Dec 11; thereafter FTSE semi-annual schedule).
4. **QUAD_WITCH** = third Friday Mar/Jun/Sep/Dec (or prior business day if holiday); often **equals** SPX_REBAL and NDX_REBAL.
5. **MONTH_END** = last RTH trading day of calendar month.
6. **QUARTER_END** = last RTH trading day of Mar/Jun/Sep/Dec (subset of MONTH_END).
7. **COMPOSITE_INDEX_EVENT** = SPX_REBAL ∨ NDX_REBAL ∨ RUSSELL_RECON (primary stratification).

**Expected n & power:** On 2020–2026 NOII: COMPOSITE_INDEX_EVENT ≈ 4–8 days/year × ~6–7 years ≈ 25–55 sessions (UNDERPOWERED alone for ~20 bps noise); MONTH_END ≈ 70–80 sessions (marginal); full panel interaction with continuous basis features preferred. Report strata descriptively even if underpowered.

**A-priori thresholds:** Primary = difference in mean bps/event (event vs non-event) with block-bootstrap CI; secondary = hit-rate and |basis| distribution shift. No promotion on rare-day subset alone.

**Promotion rule:** Event-day mean net ≥ champion non-event mean **and** pooled CI lower bound > 0 after cost, with pre-registered multiple-testing charge; else keep as risk/meta feature only.

**Kill criteria:** (i) no distributional difference at α after multiplicity; (ii) event days strictly worse economics and kill-as-filter fails; (iii) n after 2026 forward too thin to update.

**Trial family charged:** Auction / NOII meta-conditioning (calendar stratum); not a new continuous-market family.

### Sources
1. **[T1]** Nasdaq-100 Index® Methodology (NDX®), Index Calendar — Reconstitution & Rebalancing Schedule (©2026 Nasdaq). https://indexes.nasdaq.com/docs/Methodology_NDX.pdf
2. **[T1]** FTSE Russell / LSEG — Russell Reconstitution hub + 2026 schedule press (2026-03-02). https://www.lseg.com/en/ftse-russell/russell-reconstitution ; https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/russell-reconstitution-2026-schedule
3. **[T1]** FTSE Russell notice — Russell US Semi-Annual Reconstitution schedule update (Dec 2026 = second Friday). https://research.ftserussell.com/products/index-notices/home/getnotice/?id=2617649
4. **[T1]** S&P Dow Jones Indices — S&P U.S. Indices Methodology (quarterly rebalance after close third Friday Mar/Jun/Sep/Dec). https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-us-indices.pdf
5. **[T1]** Nasdaq Trader — Opening and Closing Crosses. https://www.nasdaqtrader.com/trader.aspx?id=openclose
6. **[T1]** Nasdaq — The Nasdaq Opening and Closing Crosses FAQs (©2025). https://www.nasdaqtrader.com/content/ProductsServices/Trading/Crosses/openclose_faqs.pdf
7. **[T1]** Nasdaq Equity Trader Alert #2026-32 — Russell Reconstitution Jun 26 2026 (cutoffs unchanged). https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2026-32
8. **[T1]** Nasdaq Equity Trader Alert #2020-83 — Quad Witch + S&P rebal Dec 18 2020. https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2020-83
9. **[T1]** NYSE — Auctions timelines (Closing Auction). https://www.nyse.com/trade/auctions
10. **[T1]** NYSE Regulatory Memo RM-26-03 — Quarterly Expiration Day Mar 20 2026 (Rule 7.35B unchanged). https://www.nyse.com/publicdocs/nyse/markets/nyse/rule-interpretations/2026/Q1_2026_Quarterly_Expiration_RM_3.20.2026.pdf
11. **[T1]** Nasdaq Price List — Trading (flags rebal/expiration as special pricing days). https://www.nasdaqtrader.com/trader.aspx?id=PriceListTrading2
12. **[T1]** FTSE Russell reconstitution FAQ (close volume Jun 2025). Same as [2].
13. **[T3]** Nasdaq.com — “The Powerful Impact of Triple Witching” (mechanics of open vs close settlement). https://www.nasdaq.com/articles/the-powerful-impact-of-triple-witching-2021-06-10

#### Queries used
- S&P 500 quarterly rebalance effective date calendar official
- Nasdaq-100 rebalance reconstitution schedule official calendar
- FTSE Russell reconstitution effective date official calendar
- quad witching triple witching third Friday March June September December auction rules
- Nasdaq closing cross special procedures rebalance month-end site:nasdaqtrader.com
- S&P Dow Jones Indices methodology quarterly rebalancing third Friday effective date site:spglobal.com
- Nasdaq Equity 7 closing cross MOC LOC entry cutoff 3:50 3:55 Rule
- NYSE closing auction MOC cutoff time month end rebalance special procedures site:nyse.com
- S&P 500 "rebalances quarterly" "third Friday" "effective after the close" methodology site:spglobal.com
- Russell US Indexes December reconstitution 2026 second Friday schedule FTSE
- Nasdaq closing cross MOC LOC cutoff time special procedures rebalance site:nasdaqtrader.com OR site:listingcenter.nasdaq.com
- month end quarter end portfolio rebalance MOC flow last trading day calendar
- Nasdaq Closing Cross special procedures Russell reconstitution OR rebalance day site:nasdaqtrader.com
- S&P Dow Jones Indices "quarterly rebalancing" "announced" "five business days" OR "effective after the close" S&P 500 membership

#### Event-date cheat sheet (for trial code)
| Flag | Rule (MOC session) |
|------|---------------------|
| SPX_REBAL / NDX_REBAL / QUAD_WITCH | 3rd Friday Mar/Jun/Sep/Dec (prior RTH day if holiday) |
| RUSSELL_RECON | FTSE published effective-close Friday (2026: 2026-06-26, 2026-12-11; historical ≈ 4th Fri June) |
| MONTH_END | last RTH day of calendar month |
| QUARTER_END | last RTH day of Mar/Jun/Sep/Dec |

**Critical distinction:** NDX “effective at open Monday after 3rd Friday” ⇒ **trade day = 3rd Friday close**. S&P/Russell “effective after the close” ⇒ **same calendar day is the MOC day**. Do not flag the Monday open as the rebal session for NOII tests.
