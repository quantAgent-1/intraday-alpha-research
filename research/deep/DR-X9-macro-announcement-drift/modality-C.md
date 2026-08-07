## DR-X9 — Modality C (practitioner: vol-target / risk-parity / CTA execution practice) findings

### Verdict recommendation
**NOT-VIABLE-STRUCTURAL** (confidence MED-HIGH) — for the specific charge (a named, TIMED, slow
payer at **minutes-to-hours** after a macro release, in cash equities). A large, named,
price-insensitive systematic re-levering payer absolutely exists (vol-target / vol-control /
risk-parity / CTA, ~$0.3–2 tn AUM). But every documented mechanic places its clock at the
**wrong horizon**: it is triggered by a *multi-week realized-volatility* estimate (not by the
release event), it fires on a **T+1 to T+2 business-day lag**, it executes **at the close (MOC)**,
and the flow is deliberately **spread over several days to weeks** to minimize impact. There is no
documented systematic program that re-levers in the *minutes-to-hours* window after a release —
that window is explicitly ceded to HFT/automated flow (inaccessible at 5–25 s manual latency). The
only point where this payer's clock intersects our mission (RTH, flat by/at close) is the **closing
auction** — which is exactly where the champion already trades.
**What would flip it:** a primary/measured source showing a systematic program that mechanically
re-levers *intraday within minutes-to-hours of a scheduled release* (not at the next close, not
over days) with a stated magnitude — i.e., a same-session, release-conditioned rebalance rule in a
prospectus/methodology. Nothing found supports this; the practitioner literature affirmatively
contradicts it.

### Mechanism
Who pays: volatility-target funds (managed-vol mutual funds, fixed-index-annuity vol-control
sub-accounts, structured-product indices), risk-parity funds, and CTA trend-followers. Why
price-insensitive: they size by a *risk budget*, not price/value — when realized vol rises they must
cut exposure regardless of level, and their trades are dictated by the model, not discretion. Why
it persists: the flow is mechanical, disclosed, and structural (NAV struck at the close forces
MOC execution). **Why it does NOT create a minutes-to-hours cash-equity drift**, the load-bearing
point: (1) the trigger is a *rolling multi-week* realized-vol denominator (e.g. trailing 13 weeks,
or max of a short + long window) — a single 8:30/10:00/14:00 release moves that denominator only
marginally unless it causes a large *sustained* move, so the release-conditioned rebalance
increment is small; (2) index/fund methodologies observe vol at the close and implement the weight
change on a **1–2 business-day lag** (S&P 10% Vol Control rebalances on the *second* business day
after the trigger; vol-control ETF indices carry a *one*-business-day lag); (3) execution
concentrates in the closing auction and is spread across days. So the payer's decision instant is
the *close on T+1/T+2*, not the minute after the release. Capacity intuition: enormous at the close
(the champion's home), effectively zero as an intraday post-release continuation driver.

### Claims
C1 [CONFIRMED] (T1/T3 index methodology, current): Vol-control index methodologies compute exposure
from a **multi-week realized-vol lookback and implement on a lag** — the S&P 10% Volatility Control
TR Index "rebalances on the **second business day** after the rebalancing is triggered"; vol-control
ETF-linked indices implement daily weights "on a **one business day lag**." Trigger-to-execution is
T+1/T+2 at the close, never intraday-post-release. — S&P DJI / BlackRock / Nasdaq index methodology docs.
C2 [PLAUSIBLE] (T3 sell-side via strategist commentary, 2019–2020): Systematic deleveraging after a
volatility shock **"continues for several more days"** (JPMorgan research cited by Nomura's
McElligott); Goldman models size CTA equity selling over **"this week" (~$33bn)** and up to
**~$80bn "over the next month."** Horizon of the flow is **days-to-weeks**, not minutes-to-hours. —
Heisenberg/SpotGamma summaries of JPM & GS notes; Yahoo/BigGo GS flow estimates.
C3 [PLAUSIBLE] (T3, current): Vol-target and index funds execute heavily via **Market-on-Close**
because NAV is struck at the closing price; systematic rebalance flow "concentrates at day-end
execution windows." — State Street Global Advisors, "Closing time: how passive investing is
reshaping equity market microstructure."
C4 [CONFIRMED] (T3, current): CTAs trade on **multi-day-to-multi-week trend lookbacks** (20–60d fast
sleeves up to 252d), and "many CTAs **avoid trading around economic releases** or during illiquid
hours"; cost-aware execution deliberately **spreads trades to avoid the most illiquid times**. This
is the opposite of a minutes-after-release taker. — kasmcapital / SG Markets / CFA Institute CTA pieces.
C5 [CONFIRMED via ECB] (T2, 2020): Aggregate size is large but the mechanics are daily/rolling:
risk-parity ~**$300bn across ~100 funds**, vol strategies **up to ~$2tn** globally; the ECB's own
model is **daily-rebalanced on one-month rolling vols** — again a slow, close-anchored clock, and
the ECB explicitly notes precise calibration/latency of live funds is *not publicly known*. — ECB
FSR box, "Volatility-targeting strategies and the market sell-off," May 2020.
C6 [UNVERIFIED — FOLKLORE] (T4, blog/prop): The retail "third-wave" narrative — "HFT react
instantly, fast discretionary within minutes, slower institutional money reallocating over
**hours-to-days**, creating the drift... retail may ride the third wave" — is unsourced,
magnitude-free blog/prop-firm content. It is the only practitioner voice placing a payer at
hours-scale, and it fails the refuter bar (no primary source, no measurement). Label: folklore. —
Benzinga / FXEmpire / prop-firm blogs.
C7 [PLAUSIBLE] (T3/T4, current): The **first seconds-to-minutes** post-release are dominated by
HFT/automated liquidity provision; "retail traders cannot compete in the first seconds." Confirms
the accessible-latency window is the *wrong* end of the reaction for a manual trader. — prop/FX
trading writeups; consistent with academic "post-FOMC influence short-lived" (Modality A/D territory).
C8 [UNVERIFIED] (T3, reported-in-search, not fetched): Per-vol-point sensitivity often quoted as
~72 equity + 64 bond contracts per $100m per 1% vol move, and ~$6bn equity / ~$10bn 60-40 vol-target
program ≈ 1% of daily volume. Magnitude only; carries no minutes-to-hours timing and I did not fetch
the primary docs — treat as order-of-magnitude context. — SPGlobal "Indexing Risk Parity" / CME
"Understanding Risk Parity" (via search summary).

### Constraint gates (applied to the minutes-to-hours post-release continuation thesis)
1. **Latency** — FAIL for this window: the systematic payer's decision instant is the *close on
   T+1/T+2*, not the minutes after the release; the minutes-to-hours window has no scheduled
   systematic payer, and its first-mover flow (HFT) is sub-manual-latency.
2. **Access** — N-A: no tradeable minutes-to-hours structure identified to price against a retail broker.
3. **Session** — PASS only if re-anchored to the CLOSE (MOC/LOC), which collapses into the champion;
   FAIL as a genuinely *intraday* minutes-to-hours idea distinct from the close.
4. **Data** — PASS: owned XNAS 1s TOB (5 names, 2020–2026) can measure any release-window reaction;
   no purchase needed to *falsify* the minutes-to-hours payer.
5. **Fill realism** — FAIL as intraday continuous-market taker on a small, lagged, mis-timed flow;
   PASS only at the close (single print) — again, the champion.
6. **Statistics** — N-A: no coherent minutes-to-hours payer to power-test; a release-window
   base-rate study is Modality-A/D's object, not a payer for this modality.
7. **Protocol** — FAIL: the pre-registrable named payer this modality was sent to find does exist,
   but it is **timed to the close and to days**, so it cannot serve as the a-priori mechanism for a
   *minutes-to-hours* family. It *can* serve a close/next-day family (already the champion's turf).

**Survivor-profile score: 2/5** (as a minutes-to-hours release-drift single-name trade):
1. Single-print/auction execution → **0** (continuous-market intraday). 2. Scheduled decision
instant → **1** (the release time is scheduled/pre-positionable). 3. Named price-insensitive payer
*at this horizon* → **0** (payer is real but mis-timed to close/T+1–T+2). 4. Testable on owned/cheap
data → **1** (owned 1s quotes). 5. Effect ≥ 2× cost at our size → **0** (no documented
minutes-to-hours magnitude; folklore only). Note: the *same payer* re-scored at the **close** horizon
would score ~4–5/5 — which is precisely why the champion, not a post-release drift, is the survivor.

### Economics sketch
No creditable gross estimate exists for a minutes-to-hours cash-equity post-release continuation
attributable to systematic re-levering, because the documented flow does not arrive in that window.
The measured flow (days-scale, ~$33bn/week CTA per GS; risk-parity ~$300bn AUM per ECB) lands in
the **closing auction over multiple sessions**. Our cost burden for an intraday continuous-market
taker in a single megacap (spread + impact, ~20 bps/event noise, post-promo fees as stress) would
swamp any small, lagged fraction of that flow reaching the minutes window. Comparison line: champion
= **+2.5 bps/event dev / +12.5 bps/event holdout** at the close — the *same* payer, captured at its
*actual* execution instant (single print, no fill ambiguity). A minutes-to-hours post-release trade
tries to capture the same flow one to two sessions *early* and in the *worst* execution regime; net
prior is at best zero, more likely negative.

### Proposed next test
None from this modality (verdict is NOT-VIABLE-STRUCTURAL, not OPEN-TESTABLE). The practitioner
evidence's only *constructive* implication for M20 Stage-2: if a release-conditioned systematic
flow is to be captured at all, its documented arrival point is the **T+1/T+2 closing auction**, not
the release-minute — i.e. it reduces to the champion's closing-auction basis family, already
registered and live. Recommend Stage-2 treat "systematic re-levering" as a *close* mechanism, not a
minutes-to-hours one; do not register a minutes-window family on this payer's authority.

### Sources
1. [T1/T3] S&P Dow Jones Indices — "Demystifying Volatility Controlled Indices" & S&P 10% Volatility
   Control TR / LVCI methodologies (2nd-business-day rebalance lag; realized-vol lookback).
   https://www.spglobal.com/spdji/en/documents/education/education-demystifying-volatility-controlled-indices.pdf ;
   https://www.spglobal.com/spdji/en/documents/methodologies/LVCI_Index_Methodology.pdf
2. [T1] BlackRock Adaptive U.S. Equity 15% Index Methodology (one-business-day implementation lag).
   https://www.blackrock.com/us/individual/literature/index-methodology/blackrock-adaptive-us-equity-index-15-percent-methodology.pdf
3. [T2] ECB Financial Stability Review box, "Volatility-targeting strategies and the market sell-off,"
   May 2020 (~$300bn risk parity / ~$2tn vol strategies; daily-rebalanced, one-month rolling vols;
   calibration/latency of live funds unknown).
   https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2020/html/ecb.fsrbox202005_02~f6616db9be.en.html
4. [T3] State Street Global Advisors — "Closing time: how passive investing is reshaping equity
   market microstructure" (MOC/close concentration of systematic flow).
   https://www.ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure
5. [T3] Nomura / Charlie McElligott commentary summaries citing JPMorgan (deleveraging "continues
   for several more days"). https://spotgamma.com/nomuras-mcelligott-the-vix-is-broken-again/ ;
   https://heisenbergreport.com/2019/07/16/marko-kolanovic-unless-theres-an-external-volatility-shock-equity-exposure-to-increase/
6. [T3] Goldman Sachs systematic-flow estimates (CTA ~$33bn/week; ~$80bn/month conditional).
   https://finance.yahoo.com/news/goldman-sachs-issues-80b-stock-133215882.html
7. [T3] CTA execution practice — kasmcapital "Understanding CTAs"; SG Markets "Keeping up with the
   Trend-Followers"; CFA Institute "Decoding CTA Allocations by Trend Horizon" (multi-day/week
   lookbacks; avoid trading around releases; spread execution).
   https://kasmcapital.substack.com/p/understanding-ctas-how-systematic ;
   https://rpc.cfainstitute.org/blogs/enterprising-investor/2026/decoding-cta-allocations-by-trend-horizon
8. [T3, order-of-magnitude only, not fetched] SPGlobal "Indexing Risk Parity Strategies"; CME/Clifton
   "Understanding Risk Parity" (per-vol-point contract sensitivities).
   https://www.spglobal.com/spdji/en/documents/research/research-indexing-risk-parity-strategies.pdf ;
   https://www.cmegroup.com/education/files/understanding-risk-parity-2013-06.pdf
9. [T4 — FOLKLORE, hypothesis-generation only] prop/retail "third-wave institutional drift over
   hours-to-days" narratives. Benzinga "Trading Systems and Market News"; FXEmpire news-driven FX
   trading. https://www.benzinga.com/Opinion/26/06/53097073/ ;
   https://www.fxempire.com/education/article/news-driven-fx-trading-how-to-trade-events-like-the-fomc-cpi-and-nfp-1549791

#### Queries used
- `volatility target fund rebalancing latency execution horizon methodology prospectus`
- `risk parity re-levering volatility target flow billions per vol point Kolanovic`
- `CTA trend following execution speed after macro release rebalance multi-day`
- `Kolanovic volatility target funds rebalance "next day" OR "over several days" equity flows systematic`
- `volatility control fund index rebalance T+1 lag observation date effective date methodology`
- `systematic vol target funds rebalance over multiple days spread execution avoid market impact`
- `vol target funds rebalance "at the close" MOC systematic equity flows end of day timing`
- `CTA systematic funds trade in minutes after FOMC announcement execution futures`
- `volatility target funds rebalance "1 to 2 days" OR "over a week" risk parity CTA reaction speed systematic flow`
- `McElligott Nomura / "Charlie McElligott" systematic vol target risk parity flows rebalance days after volatility spike`
- `trading post-FOMC drift retail minutes after announcement blog strategy backtest`
- `vol target funds react fastest 1-2 days risk parity slower weeks CTA slowest deleveraging hierarchy JPMorgan estimate`
- `"target volatility" annuity index fund realized volatility lookback rebalance daily close exposure adjustment lag`
- `Goldman Sachs OR JPMorgan estimate "$" billion systematic selling per volatility point executed over next few days at close`
- `prop trader account trading FOMC CPI drift 30 minutes after release edge gone HFT first seconds forum`
- (WebFetch) ECB FSR vol-targeting box; JPM Market & Volatility Commentary 2019-01-16 (PDF corrupted, not usable)
