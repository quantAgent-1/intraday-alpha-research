## DR-X9 — Modality D (adversarial / prior-art) findings

### Verdict recommendation

**EXHAUSTED-BY-FIELD (confidence MED-HIGH)** for minutes–hours *post-release* continuation in
US large-cap **cash** equities, for the FOMC-14:00 and the 8:30/10:00 macro-release classes.
The kill is *convergent* rather than a pristine matched pair: the price reaction to scheduled
macro news completes in the **first second** in cash SPY (a manual 5–25 s trader captures none of
it — Scholtus 2014); ~**40 %** of the total adjustment happens in the **30 min BEFORE** the
release (Kurov et al. 2019), so there is little left to run afterward; the documented *post*-FOMC
behavior is **reversal, not continuation** (Baglioni–Ribeiro); the closest published pre-FOMC
equity drift **decayed to insignificance after 2015** (Kurov–Gilbert–Wolfe); and the single most
parsimonious mundane read of the M20 screen — intraday momentum on macro-news days — **fails
out-of-sample** (Rosa 2022 on the very effect that Gao et al. show is *stronger* on macro days).
Two release classes are NOT covered by a clean kill: **Treasury-auction→equity spillover** (thin
literature — UNKNOWN) and the *exact* object M20 targets (single-name megacap continuation at
15 min–4 h), which is **essentially unstudied** — itself corroborating, because the field treats
post-release drift as a seconds-scale *futures* phenomenon, not a minutes-scale cash-equity one.

**What would flip it:** a primary source showing a **positive, OOS-surviving, cost-net**
post-release *continuation* in single-name cash equities at 15 min–4 h that is NOT reducible to
(a) index beta to the seconds-scale futures reaction or (b) already-killed intraday momentum —
i.e., a distinct, timed, slow payer paying at minutes. None found; the burden sits with the
survival modalities (A/C).

### Mechanism (kill lens)

No coherent *minutes-scale* payer found in the adversarial literature. The efficient-market /
crowding account dominates: (1) macro numbers are disseminated to everyone simultaneously
(post-2020 the DOL lock-up that gave media/vendors early access was **discontinued 3 Jun 2020**),
(2) latency-arb HFT and news-reading algos impound the surprise into ES/NQ/SPY within **sub-second
to ~1 s**, (3) whatever informed pre-positioning exists front-runs the print by ~30 min. The
residual "drift" that older studies found was largely (i) *pre*-release leakage (now curbed) or
(ii) an artifact of the reaction not yet being complete at coarse (5–30 min) sampling — not a slow
payer a retail trader can harvest at 10:00:25. A single-name megacap expression of a market-wide
reaction is, on this view, **index beta plus idiosyncratic noise**; the "continuation" is the tail
of a fast reaction plus intraday-momentum autocorrelation, both of which decay OOS.

### Claims (ordered by load-bearingness)

**C1 [CONFIRMED]** (T2, JBF 2014, sample Jan 2009–Dec 2011): For a macro-news trading strategy in
the **cash S&P 500 ETF (SPY)**, a **300 ms** execution delay cuts the return by **3.08 %** and a
**1 s** delay by **7.33 %** vs instantaneous — stronger for high-impact news and high-vol days;
"speed is crucially important." *At 5–25 s manual latency the residual is ~nil.* This is the
on-point crowding/speed kill in CASH equity. — Scholtus, van Dijk, Frijns, *J. Banking & Finance*
38:89–105. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2174901 (NO single-stock horizon
beyond seconds tested — but that is the point: nothing is left to test at minutes.)

**C2 [CONFIRMED]** (T2, JFQA 2019, sample 2008–2014): Across ~30 US macro announcements
(incl. ISM, consumer confidence, GDP, employment — our 8:30/10:00 classes), in **E-mini S&P and
10y Treasury futures**, prices begin moving in the correct direction **~30 min before** release;
pre-announcement drift is on average **~40 % of the total price adjustment**. Implication: the
public-release *reaction* is small and near-complete at t=0, leaving little post-release
continuation. — Kurov, Sancetta, Strasser, Wolfe, "Price Drift before U.S. Macroeconomic News."
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2637528

**C3 [CONFIRMED]** (T3/T2, SSRN 2022, sample 1997–2020, 180 FOMC): Post-FOMC the equity index
**reverses** the pre-announcement move (strong negative pre-vs-post relationship, independent of
regime); a *reversal* strategy on E-mini S&P earns Sharpe **>2.5×** the pre-FOMC drift. Directly
contradicts a *continuation* thesis for the FOMC-14:00 class. — Baglioni & Ribeiro, "The FOMC
Announcement Reversal." https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4182628 (T2-track,
working paper — flag: not yet journal-published; sign result robust across their subsamples.)

**C4 [CONFIRMED]** (T2, Finance Research Letters 2021, sample Sep 1994–Dec 2019): The pre-FOMC
equity drift **disappeared after Jan 2016** — mean 24 h pre-FOMC S&P return fell from **~49 bps
(0.49 %)** in 1994–2011 to **~9 bps (0.09 %)**, statistically **indistinguishable** from the
non-announcement mean (~5 bps); Wilcoxon rejects equality at 1 %. Attributed to reduced
uncertainty (VIX 17.7→14.7). The best-known *scheduled-announcement* equity effect decayed OOS. —
Kurov, Wolfe, Gilbert, "The Disappearing Pre-FOMC Announcement Drift."
https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/ (CAVEAT: this is the *pre*-window, not M20's
*post*-window — adjacent object; load-bearing as a decay precedent, not a direct post-drift kill.)

**C5 [CONFIRMED]** (T2, JFM 2022, vol 42(12):2218–2234): Intraday-momentum predictability
(first-half-hour → last-half-hour class) **disappears out-of-sample**; calendar-time evaluation of
such anomalies gives false positives when returns are regime/signal-strength dependent. — Rosa,
"Understanding intraday momentum strategies."
https://onlinelibrary.wiley.com/doi/abs/10.1002/fut.22375 (This is the OOS kill our EXHAUSTION_MAP
already logs as CONFIRMED for TOD momentum.)

**C6 [CONFIRMED]** (T2, JFE 2018, sample 1993–2013): Market intraday momentum is **stronger on
major macroeconomic-news-release days**. Combined with C5, the most parsimonious read of the M20
10:00-cluster 30–60 min continuation is *intraday momentum on macro days* — a known effect that
fails OOS — NOT a distinct macro payer. This is the steelman against M20. — Gao, Han, Li, Zhou,
"Market Intraday Momentum." https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866

**C7 [CONFIRMED]** (T2, JF 2016, 97 predictors): Published cross-sectional predictors decay
**26 % out-of-sample** and **58 % post-publication**. Base-rate prior: a screen-discovered
2020–2026 effect should be *deeply* haircut forward; +9–13 bps at 30–60 m in a 2-of-40-cells
screen is inside the range that vanishes on this base rate alone. — McLean & Pontiff, "Does
Academic Research Destroy Stock Return Predictability?"
https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365

**C8 [CONFIRMED]** (T1, Federal Register 2020, effective 3 Jun 2020): The DOL/BLS media **lock-up
was discontinued** (suspended 20 Mar 2020, made permanent 3 Jun 2020); data now hit the public
"seconds after release with negligible degradation." For the 8:30 BLS class this removes the
vendor/media early-access channel — reinforcing simultaneous, instantly-crowded dissemination and
undercutting any leakage-based residual. — Federal Register 2020-11297; BLS notice.
https://www.federalregister.gov/documents/2020/05/27/2020-11297/announcing-discontinuation-of-the-dol-lock-up-facility-for-participating-news-media-organizations

**C9 [PLAUSIBLE]** (T2, JIMF 2022): "Drift Begone!" — ending early-access **release policies**
(UK 2017; and the US lock-up change) **weakened preannouncement drift**, evidencing that the
residual pre-print move was informed early-access trading now curbed, not a structural equity
payer. — Kurov, Sancetta, Wolfe, *J. International Money & Finance*.
https://www.sciencedirect.com/science/article/abs/pii/S0261560622001218 (PDF unparseable via
fetch — abstract-level only; magnitudes not extracted.)

**C10 [UNVERIFIED / GAP]** (—): **No** primary source found testing **Treasury-auction-result
(13:01–13:03 ET) → equity** continuation at minutes–hours, and **none** testing single-name
megacap post-macro continuation at 15 min–4 h. The auction-spillover class is genuinely **UNKNOWN**;
the single-name object's near-total absence in the literature is corroborating (the field models
this as a seconds-scale futures reaction) but is not itself a kill.

### Constraint gates (as the kill evidence bears on a post-release continuation trade)

| # | Gate | Verdict | Clause |
|---|------|---------|--------|
| 1 | Latency (5–25 s) | **FAIL** | C1: reaction complete in ~1 s in cash SPY; 5–25 s captures ~none. |
| 2 | Access ($1k–10k retail) | N-A | executable, but moot if no edge survives latency. |
| 3 | Session (RTH) | PASS | 10:00/14:00 windows are intraday RTH. |
| 4 | Data (owned/≤$100) | PASS | owned 1 s TOB suffices for the screen; kill needs no new data. |
| 5 | Fill realism | FAIL-adjacent | continuous-market taker into a just-moved book; slippage highest right after news. |
| 6 | Statistics (n≥250) | **FAIL (as run)** | M20 3-mo VALIDATE confirmed same-sign at ~zero power (N≈43/15 sess, se≈18 bps) — the screen's own confirm already failed. |
| 7 | Protocol (named payer a-priori) | **FAIL** | no confirmed minutes-scale slow payer; mechanism prong unmet from the kill side. |

**Survivor-profile score: 2/5** — (1) single-print execution: **0** (continuous market);
(2) scheduled decision instant: **1** (release time is scheduled); (3) named price-insensitive
payer: **0** (folklore only at minutes; no confirmed payer); (4) historically testable on owned
data: **1**; (5) effect ≥2× cost: **0** (screen number is contested and confirm-failed). A ≤2
score "needs an extraordinary reason to research at all" — the kill evidence supplies none.

### Economics sketch

Screen gross (contested): +9–13 bps/event at 30–60 m (M20 TRAIN, 2-of-40 cells, confirm-failed).
Cost burden for a continuous taker into a fresh post-news book at our size: spread + adverse
selection are *elevated* exactly in the reaction window (C1/C2 imply the informative move is
already gone; what remains for a 25 s-late taker is disproportionately noise + cost). Net prior:
**≤0 after cost and OOS decay** — McLean–Pontiff (C7) alone haircuts a screen effect by 26–58 %,
and the reversal/crowding kills push the central estimate to zero-or-negative. Comparison line:
**champion = +2.5 bps/event dev / +12.5 holdout** on a *single-print auction* with a *named*
price-insensitive payer — the structural opposite of this continuous, payer-less, latency-exposed
cell.

### Proposed next test

None from the kill side (verdict is EXHAUSTED-BY-FIELD, not OPEN-TESTABLE). If the survival
modalities force a Stage-2, the *only* defensible pre-registration is a **differencing test that
strips the two mundane explanations before any economics**: regress each name's post-release
30–60 m return on (a) the contemporaneous SPY/index 30–60 m return (index-beta control) and (b) the
09:30–10:00 morning return (intraday-momentum control), and require the **macro-day residual
intercept** to be positive, OOS-stable across a fresh forward window, and ≥2× cost — charging the
`sched_window_v1` trial family. Kill criterion: residual intercept CI spans 0 forward (as the
3-mo VALIDATE already suggests). Absent that residual, M20 = index beta + killed intraday momentum.

### Sources

1. Scholtus, van Dijk, Frijns (2014), *J. Banking & Finance* 38:89–105 — T2 — SSRN 2174901.
2. Kurov, Sancetta, Strasser, Wolfe (2019), *J. Financial & Quantitative Analysis* 54(1):449–479 — T2 — SSRN 2637528.
3. Baglioni & Ribeiro (2022), "The FOMC Announcement Reversal" — T2/T3 working paper — SSRN 4182628.
4. Kurov, Wolfe, Gilbert (2021), *Finance Research Letters* 40 — T2 — PMC7525326 / SSRN 3134546.
5. Rosa (2022), *J. Futures Markets* 42(12):2218–2234 — T2 — doi 10.1002/fut.22375.
6. Gao, Han, Li, Zhou (2018), *J. Financial Economics* — T2 — SSRN 2440866.
7. McLean & Pontiff (2016), *J. Finance* 71(1) — T2 — doi 10.1111/jofi.12365.
8. Federal Register 2020-11297 (2020); BLS lock-up discontinuation notice — T1.
9. Kurov, Sancetta, Wolfe (2022), "Drift Begone!", *J. International Money & Finance* — T2 — S0261560622001218 (abstract-only; PDF unparseable).
10. Neuhierl & Weber (2018), "Monetary Momentum", NBER w24748 — T2 — *context only:* a
    **multi-day** (up to +15 d) post-FOMC drift → OUT-OF-MISSION horizon, not a minutes–hours
    cash-equity claim; noted so it is not mistaken for in-scope survival evidence.

#### Queries used
- `Lucca Moench pre-FOMC announcement drift decay disappeared after 2015 out-of-sample`
- `pre-FOMC drift reversal post-publication decay 2016 2017 2018 equity returns`
- `Scholtus van Dijk speed high-frequency trading macroeconomic news announcements price adjustment seconds`
- `Neuhierl Weber monetary momentum post-FOMC drift replication out-of-sample decay`
- `Bollerslev Li Xue announcement jumps price discovery seconds S&P 500 no drift after macro news`
- `ISM manufacturing release 10:00 stock market reaction speed drift decayed high frequency`
- `Kurov Sancetta Strasser Wolfe price drift before macroeconomic news announcements information leakage minutes before release`
- `announcement drift trading strategy failed practitioner post-mortem macro news retail can't profit slippage`
- `McLean Pontiff does academic research destroy stock return predictability out-of-sample decay 58 percent`
- `Heston Korajczyk Sadka intraday momentum first half hour predicts last half hour decay out-of-sample Gao 2018`
- `Rosa 2022 intraday momentum time-of-day patterns out-of-sample fails disappears trading strategy`
- `"market intraday momentum" Gao Han Zhou out-of-sample decay weakened recent sample S&P 500 predictability`
- `"FOMC announcement reversal" post-announcement stock returns reverse drift equity intraday`
- `Department of Labor lock-up reform 2020 ended media transmission early access BLS macroeconomic release pre-announcement drift`
