## DR-X3 — modality B (primary/venue) findings

### Verdict recommendation
OPEN-TESTABLE (confidence HIGH) — Primary Rule 605 files from major wholesalers (Jane Street TJNST, Virtu NITE, May 2026 legacy format), Alpaca 606 Q3 2025 material aspects, IBKR Lite/Pro routing docs, and SEC 605 modernization T1 establish that small marketable retail flow on liquid Nasdaq via PFOF wholesalers pays well inside the half-spread mid-day: effective/quoted (E/Q) roughly 0.50–0.70, one-sided cost often 0.2–0.7 bps on megacaps in the 100–499 bucket, with ≥90% of shares price-improved. Post-modernization odd-lot E/Q is not yet published (compliance **August 1, 2026**); last-15-minute survival of improvement is **UNKNOWN** from 605 (monthly aggregates only). Recommend M16 Phase 0 cost prior: E/Q 0.55–0.70 overall RTH; stress E/Q 0.80–1.0 in 15:45–16:00 until SIP-tagged paper fills calibrate TOD.

What would flip it: A month of Alpaca marketable clips ($400–$3,000) on NVDA/TSLA/AMD/MU/GOOGL with SIP NBBO at send time showing median E/Q ≥ 0.95 in the last 15 minutes (i.e., PI dies near the close for our flow).

### Mechanism
Who pays: Uninformed / less-toxic retail order flow is segmented by retail brokers and sold (PFOF) to OTC wholesalers (Citadel CDRG, Virtu NITE, Jane Street JNST, G1X). Wholesalers internalize against proprietary inventory and institutional flow, returning a fraction of the quoted spread as price improvement (PI) while remitting PFOF to the broker from the residual. Why price-insensitive: retail held market/marketable-limit orders demand immediacy; they do not post or chase midpoint systematically. Why it persists: Reg NMS best-ex duty + competition among ~4 wholesalers for broker allocations sustains PI; brokers reallocate share on execution quality (Fed Huang–Jorion–Lee–Schwarz 2024; Dyhrberg–Shkilko–Werner JFE 2025). Capacity intuition: our $400–$3,000 clips are deep in the odd-lot / 100–499 regime wholesalers already absorb at scale (millions of shares/month per liquid name in 605); no capacity binding at $10k notional. Auction caveat: Alpaca 606 material aspects state primary **closing auction** fills receive **no PFOF rebate** (Citadel: Alpaca pays 12 mils/share on primary close) — continuous-market PI economics do not transfer 1:1 to MOC.

### Claims
C1 [CONFIRMED] (T1, May 2026 sample month, gross of commission — RE-VERIFIED by direct field-parse of the raw 605 file this session; field 18 = effective spread, empirically confirmed as the always-≥0 column vs field 17 realized which goes negative): On Jane Street (TJNST) legacy Rule 605, MARKET orders (type 11), 100–499 bucket (size code 21 — the smallest legacy bucket; **legacy 605 has no odd-lot bucket**), share-weighted average **effective spread ($/sh) and %shares price-improved**:
NVDA $0.0062 / 96.4% · AAPL $0.0068 / 96.6% · AMZN $0.0065 / 97.6% · GOOGL $0.0118 / 96.8% · MSFT $0.0181 / 98.0% · TSLA $0.0203 / 97.4% · SPY $0.0068 / 92.8% · QQQ $0.0094 / 93.0% · INTC $0.0082 / 97.0% · SOXX $0.0254 / 96.8% · SMH $0.0350 / 96.8% · **AMD $0.0509 / 98.4%** · **MU $0.1036 / 96.1%** (widest). At approximate May-2026 mids this is one-sided half-effective ≈ **0.06 bps (SPY) to ~0.35 bps (GOOGL/TSLA)** on the tight megacaps/ETFs, rising to **~2.1 bps (AMD)** and **~4.7 bps (MU)**; %PI **93–98%**; avg PI $0.011–$0.15/sh. — Jane Street May 2026 605 `202605_JNST.txt` (parsed 129,111 rows); Virtu May 2026 605 `TVIRTU202605.dat` (NITE MPID) corroborates direction; primary parse this charge.

C2 [CONFIRMED] (T1, May 2026 — RE-VERIFIED direct parse): Marketable-limit (type 12) 100–499 is **worse** than market (type 11) on every target name in the Jane Street file: effective spread MKT→MLIM: NVDA $0.0062→$0.0083, AAPL $0.0068→$0.0104, MSFT $0.0181→$0.0321, TSLA $0.0203→$0.0288, MU $0.1036→$0.1555; %PI also falls (e.g. MSFT 98.0%→91.6%, MU 96.1%→92.3%). Virtu NITE corroborates: share-weighted half-effective ≈ **1.48 bps (MKT) vs 2.34 bps (MLIM)** across 14 liquid names. **Takeaway for M16: send MARKET, not marketable-limit.** — Jane Street `202605_JNST.txt` (direct parse) + Virtu NITE 605.

C3 [CONFIRMED] (T1, Mar 6 2024 adopt / Jun 14 2024 effective; compliance extended to Aug 1 2026): SEC modernized Rule 605 (Release 34-99679) adds **odd-lot and fractional** size buckets, **average quoted spread**, **E/Q** (avg effective / avg quoted), notional size categories, larger broker-dealer reporters, and a public summary report. **No post-modernization odd-lot E/Q files are required until August 1, 2026**; Citadel’s 605 page explicitly states modernized reports begin Aug 2026. Legacy 605 **excludes odd lots**. — https://www.sec.gov/files/rules/final/2024/34-99679.pdf ; https://www.sec.gov/rules-regulations/2025/09/disclosure-order-execution-information ; https://www.citadelsecurities.com/rule-605-606-statements/

C4 [CONFIRMED] (T2, sample ~2019–2022 Rule 605, gross): Wholesaler liquidity-demanding orders: E/Q ≈ **0.76** full sample (effective 53.2 bps / quoted 69.6 bps); S&P 500 retail receives PI ≈ **47% of quoted spread** (E/Q ≈ 0.53); exchanges PI only ~3–5%. FIF odd-lot stats (cited) ≈ similar quality to 100–499. — Dyhrberg, Shkilko, Werner, “The Retail Execution Quality Landscape,” *J. Financial Economics* 2025 / SSRN 4313095.

C5 [CONFIRMED] (T1, Alpaca 606 Q3 2025 July month): Alpaca non-directed S&P 500 equity flow routes ≈ **Virtu 43% / Citadel 39% / Jane Street 17%**. Material aspects: marketable core-session PFOF = **12% of the spread per share, capped at $0.05/share**; non-marketable ≥$1 = 20 mils/share; **opening/closing primary auction fills: no rebate** (Citadel: Alpaca charged 12 mils on primary close). Explicit conflict language: PFOF and PI compete for the same wholesaler expected profit. — https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2025Q3.pdf

C6 [CONFIRMED] (T1 + T2, sample Dec 2021–May 2023 parallel market orders): IBKR Lite routes to wholesalers with PFOF; IBKR Pro uses SmartRouting (exchanges/ATS, no PFOF). Controlled experiment PI% of NBBO: IBKR Lite **19.5%**, IBKR Pro **18.8%** (Robinhood 26.8% better); IBKR Pro midpoint-or-better only ~16% of trades. Round-trip cost dispersion across brokers 7–46 bps of notional in that (broader-universe) sample — **not** a liquid-Nasdaq-only number. IBKR own disclosure: Lite PFOF “potential effect… reduced price improvement… in proportion to the payment.” — Schwarz, Barber, Huang, Jorion, Odean, *Journal of Finance* 2025; IBKR order-routing disclosure https://gdcdyn.interactivebrokers.com/Universal/servlet/Registration_v2.formSampleView?formdb=3074

C7 [CONFIRMED] (T2, Fed FEDS 2024-080, ~150k parallel trades): Within-broker E/Q dispersion across wholesalers is large and persistent (max–min 42–151% of broker mean). Broker-level E/Q examples: IBKR Lite ~58%, Robinhood ~42%, Fidelity ~151% of its own mean scale (table of deviations). Proportional routers often send more flow to *worse* wholesalers; selective routers do reallocate. — Huang, Jorion, Lee, Schwarz, FEDS 2024-080 https://www.federalreserve.gov/econres/feds/files/2024080pap.pdf

C8 [PLAUSIBLE] (T1 broker marketing + T3, Q1 2026 / conflicted): Fidelity voluntary stats: avg effective spread **$0.0056**, ~95% shares PI, ~99% at/within NBBO (Q1 2026) — directionally consistent with wholesaler 605 on liquid names but not size-/TOD-bucketed and self-selected. — https://www.fidelity.com/trading/execution-quality/overview

C9 [UNVERIFIED → UNKNOWN] (no T1 time-of-day field): Rule 605 is **monthly, stock×type×size** — **no 15:45–16:00 slice**. Academic/T1 do not publish last-15-minute E/Q for wholesaler marketable retail. Citadel comment letter notes retail arrives when quoted spreads are ~30% wider than non-retail (raises dollar PI capacity, not E/Q). Project-owned fact: megacap half-spread ≈ **0.73 bps at 15:55:10**; entry shortfall median **1.46 bps** (≈ 2× half-spread) — consistent with E/Q near 1 or with adverse mid-move, not with mid-day 0.5 E/Q. Last-15m PI survival = **UNKNOWN** until SIP-tagged fills.

C10 [PLAUSIBLE] (T1 mechanics + C1–C2): For $400–$3,000 marketable clips on liquid Nasdaq, size is mostly **odd-lot** (e.g. NVDA@$120 → 3–25 sh; AAPL@$200 → 2–15 sh); 100–499 only binds on cheaper names (INTC, etc.). Given FIF/Dyhrberg odd-lot ≈ 100–499 quality, and Alpaca routes 100% of this segment to the three wholesalers in C5, predicted continuous-session economics track C1, not exchange half-spread.

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | PASS | Cost measurement / fill-kernel calibration; no sub-5s signal required. |
| 2 Access | PASS | Executable today via Alpaca market/marketable-limit; IBKR Lite/Pro available. |
| 3 Session | PASS / N-A | Continuous RTH cost prior; close/MOC is separate (Alpaca auction PFOF = 0). |
| 4 Data | PASS | Legacy 605 free; SIP ticks already owned; paper clips $0 commission through promo. Post-mod 605 free after Aug 2026. |
| 5 Fill realism | PASS | Taker-priced wholesaler fills; 605 is order-based (not tape phantoms). Still need own SIP ground-truth for TOD and odd lots. |
| 6 Statistics | PASS | M16 cost prior is descriptive (not alpha n); paper-fill n≥250 easy at 1–2 clips/session. |
| 7 Protocol | PASS | Named payer = wholesaler inventory vs segmented retail; pre-register E/Q bands before paper. Charges cost-model family (not alpha family). |

Survivor-profile score: **3/5** (1 single-print/auction? 0 — continuous fills; 2 scheduled decision? 0/partial — cost is always-on; 3 named payer? 1 — wholesaler vs retail; 4 testable ≤$100? 1 — free 605 + owned SIP; 5 effect ≥2× cost? 1 — if true E/Q~0.6, sim half-spread+slip overstates cost ≥2× mid-day). Not a standalone edge; it is an **input** to M16 Phase 0.

### Economics sketch
**Gross (cited, continuous marketable small retail, liquid Nasdaq):**
- Wholesaler 605 market 100–499 (May 2026 JNST/NITE): half-effective ≈ **0.2–0.5 bps** on NVDA/AAPL/MSFT/AMZN/GOOGL/QQQ/SPY; **~1.4–1.5 bps** share-weighted including wider names (MU ~5 bps, AMD ~2.5 bps).
- Academic E/Q: **0.53 (S&P 500) to 0.76 (all)** → one-sided cost = (E/Q)×(half-spread).
- Schwarz broker experiment PI% of NBBO ~19–47% → E/Q ~0.53–0.81 depending on broker (sample not liquid-only).

**Our cost burden (structure = Alpaca marketable taker, $400–$3,000):**
- Commission: $0 through 2026-12-31 promo (stress: post-promo fee as annotation).
- PFOF is paid *to* Alpaca, not charged to us; PI is received *by* us.
- Sim today: full half-spread + 0.5–1 bp slip. Owned observation at 15:55:10: half-spread 0.73 bps, shortfall median 1.46 bps.

**Net prior vs champion:**
- Mid-day liquid marketable: **realistic one-sided ≈ 0.3–0.7 bps** (E/Q 0.55–0.70 × half-spread 0.5–1.0 bps) — **sim overstates by ~1–2 bps** vs 605.
- Near-close (15:45–16:00): half-spread elevates; E/Q **UNKNOWN** — use stress **0.8–1.0 × half-spread** (≈ 0.6–1.5 bps one-sided) until paper data.
- Champion = +2.5 bps/event dev / +12.5 holdout (auction, single print, no continuous exit spread). Continuous-market edges must clear a **lower** cost bar than sim currently assumes mid-day, but **not** a free pass near 15:55.

**Predicted E/Q for $400–$3,000 marketable clips on liquid Nasdaq:**
| Window | Predicted E/Q | One-sided cost (bps) | Basis |
|--------|---------------|----------------------|--------|
| Overall RTH | **0.55–0.70** | **0.25–0.70** (at 0.5–1.0 bps half-spread) | C1–C4, C10; Alpaca→wholesaler path |
| Last 15 min (15:45–16:00) | **UNKNOWN** (stress **0.80–1.00**) | **UNKNOWN** (stress 0.6–1.5) | C9; project 15:55 shortfall 1.46 bps |

### Proposed next test (only if OPEN-TESTABLE)
**Hypothesis:** Alpaca marketable clips of $400–$3,000 on {NVDA, TSLA, AMD, MU, GOOGL} receive E/Q ≤ 0.70 mid-day and E/Q ≤ 0.90 in 15:45–16:00 when measured vs SIP NBBO at broker-ack time.

**Named payer:** Wholesaler internalization of segmented retail (Virtu/Citadel/Jane Street per Alpaca 606).

**Data needed:** Owned Alpaca historical SIP + 50–100 live/paper marketable clips stratified by TOD bucket (10:00–15:00 vs 15:45–16:00). Cost $0 (commission promo) + researcher time. Optional: request Alpaca 606(b)(1) customer-specific routing for 6 months (free, T1).

**Universe / n / power:** 5 names × 2 TOD buckets × ≥25 clips = n≥250; power is for mean E/Q (sd of single-order E/Q ~0.3–0.5), not for 20 bps alpha noise.

**A-priori thresholds:**
- Promote cost-model update if mid-day median E/Q ∈ [0.40, 0.75] and last-15m median E/Q ∈ [0.50, 1.10].
- Kill “PI dies at close” scare if last-15m median E/Q ≤ 0.90.
- Kill “sim is fine” if mid-day median E/Q ≤ 0.60 (then cut sim half-spread charge).

**Promotion rule:** Replace sim entry cost with `0.5 × quoted_spread × E/Q_bucket` using the two TOD buckets above; keep +0.3 bp residual slip for latency/adverse selection.

**Kill criteria:** If paper E/Q ≥ 0.95 both buckets, retain full half-spread sim; if Alpaca routing leaves wholesaler path (e.g. exchange-only), re-measure.

**Trial family charged:** Cost-model / fill-kernel family (not alpha). Does **not** spend the sealed holdout.

### Sources
1. **[T1]** SEC, *Disclosure of Order Execution Information*, Release 34-99679 (Mar 6, 2024; effective Jun 14, 2024). https://www.sec.gov/files/rules/final/2024/34-99679.pdf
2. **[T1]** SEC, extension of Rule 605 amendments compliance date to **August 1, 2026** (Release 34-104147 / Sep 30, 2025). https://www.sec.gov/rules-regulations/2025/09/disclosure-order-execution-information ; https://www.sec.gov/files/rules/final/2025/34-104147.pdf
3. **[T1]** SEC Staff FAQs Rule 605 (Apr 1, 2026; effective with compliance date). https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/frequently-asked-questions-rule-605-regulation-nms
4. **[T1]** Citadel Securities Rule 605/606 statements (legacy format; notes modernized reports start Aug 2026). https://www.citadelsecurities.com/rule-605-606-statements/
5. **[T1]** Jane Street Rule 605 May 2026 (JNST). https://www.janestreet.com/static/execution-quality-reports/202605_JNST.txt
6. **[T1]** Virtu Americas Rule 605 May 2026 (NITE/VIRT). https://www.virtu.com/about/transparency/rule-605-and-606-reporting/ → `TVIRTU202605.zip`
7. **[T1]** Alpaca Securities Rule 606(a) Q3 2025 (venues + material aspects PFOF 12% of spread). https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2025Q3.pdf
8. **[T1]** Alpaca disclosures library / PFOF notice. https://alpaca.markets/disclosures ; https://files.alpaca.markets/disclosures/library/PFOF.pdf
9. **[T1]** FINRA AWC SD-2436 Alpaca (Mar 6, 2025) — 606 PFOF disclosure failures. https://www.finra.org/sites/default/files/2025-03/SD-2436-Alpaca-03-06-2025.pdf
10. **[T1]** IBKR Lite vs Pro comparison; SmartRouting / order-routing & PFOF disclosure. https://www.interactivebrokers.com/en/general/compare-lite-pro.php ; IBKR formdb=3074 routing disclosure
11. **[T1]** FINRA Rule 605 reports portal / NMS Plan. https://www.finra.org/filing-reporting/regulation-nms/sec-rule-605-reports
12. **[T2]** Dyhrberg, Shkilko, Werner (2025), “The Retail Execution Quality Landscape,” *JFE*. SSRN 4313095 / AEA 2024 paper. Wholesaler E/Q 0.76; S&P 500 PI 47% of quote.
13. **[T2]** Schwarz, Barber, Huang, Jorion, Odean (2025), “The ‘Actual Retail Price’ of Equity Trades,” *Journal of Finance* 80:2507–2541. IBKR Lite/Pro PI% table.
14. **[T2]** Huang, Jorion, Lee, Schwarz (2024), “Who is Minding the Store?…,” FEDS 2024-080. https://www.federalreserve.gov/econres/feds/files/2024080pap.pdf
15. **[T1/T3]** Fidelity execution quality page (Q1 2026 voluntary stats; conflicted marketing). https://www.fidelity.com/trading/execution-quality/overview
16. **[T3]** Citadel comment on Order Competition / realized-spread critique (retail arrives at ~30% wider spreads). https://www.citadelsecurities.com/wp-content/uploads/sites/2/2023/03/Citadel-Securities-Response-to-the-Auctions-Proposal-Final.pdf

#### Queries used
- SEC Rule 605 modernization adopting release 2024 order execution quality
- Rule 605 report wholesaler Citadel Virtu Jane Street odd lot 100-499 shares effective spread 2024 2025
- Alpaca Rule 606 payment for order flow price improvement disclosure
- IBKR Lite vs Pro Rule 605 execution quality price improvement statistics
- "effective/quoted" OR "E/Q" Rule 605 marketable orders small size Nasdaq 2024 2025
- Citadel Securities Rule 605 report download effective spread odd lot
- Alpaca Securities Rule 606 report 2024 2025 PFOF venues
- FIF retail execution quality statistics E/Q price improvement 2024 2025
- Rule 605 compliance date December 2025 odd-lot size buckets effective quoted spread
- Virtu Citadel Jane Street G1X Rule 605 marketable order E/Q 100-499 shares S&P 500
- Retail Execution Quality Landscape E/Q 0.76 wholesaler S&P 500 47% price improvement
- "actual retail price" IBKR Lite Pro PI% E/Q basis points round-trip Schwarz Jorion
- price improvement time of day end of day last 15 minutes retail wholesaler 15:45 16:00
- Dyhrberg Shkilko Werner retail execution quality S&P 500 E/Q size bucket odd lot
- SEC Rule 605 modernization compliance date August 1 2026 extension
- site:interactivebrokers.com Rule 605 execution quality regulatory reports
- Schwarz Jorion "Actual Retail Price" Journal of Finance 2025 table price improvement percent IBKR
- Who is Minding the Store Order Routing Competition Retail Huang FEDS E/Q
