# DR-X3 — Independent REFUTER pass 2 (wave claims)

**Role:** Independent refuter (no coordination with other lanes/refuters).  
**Standard (AGENT_BRIEF §6 + harness §5):** Attempt to REFUTE via T1/T2 primary sources.  
**Default:** `refuted=true` if T1/T2 cannot be located. CONFIRMED-class survival requires an actual primary hit.  
**Date:** 2026-07-18  
**Scope:** Six load-bearing claims from DR-X3 retail execution quality wave 1.

---

## Summary table

| # | Claim (short) | refuted | Tier found | One-line reason |
|---|---------------|---------|------------|-----------------|
| 1 | Wholesaler Rule 605 E/Q ≈ 0.76 full sample (Dyhrberg) | **false** | T2 | AEA Dec-2023 WP Table 2 prints effective/quoted = 0.76 (53.16 / 69.60 bps) for WHOL. |
| 2 | May 2026 wholesaler 605: sub-bp half-effective on megacap 100–499 MKT | **false** | T1 | JNST/NITE May-2026 605: NVDA/AAPL/MSFT/AMZN/GOOGL/TSLA half-eff ≈ 0.16–0.41 bps (MKT 100–499). |
| 3 | Modernized 605 odd-lot compliance date = Aug 1 2026 | **false** | T1 | SEC Release 34-104147 extends Rule 605 Amendments compliance to **August 1, 2026** (odd-lot buckets are in the amendments). |
| 4 | Alpaca → Virtu/Citadel/JNST; PFOF 12% spread marketable; no auction PFOF | **false** | T1 | Alpaca 606 Q3 2025 material aspects name NITE/CDRG/JNST; marketable core PFOF = 12% of spread cap $0.05; auctions: no rebate (Citadel close = 12 mil charge to Alpaca). |
| 5 | Field experiment: large broker PI dispersion; IBKR worst tier | **false** | T2 | Schwarz et al. JoF 2025: PI 19–47% of NBBO across 6 accounts; IBKR Pro 18.8% / Lite 19.5% bottom; FEDS 2024-080 IBKR Lite E/Q ≈ 0.527 worst named. |
| 6 | NBBO PI overstatement literature (Adams/Ernst class) | **false** | T2 | Adams/Kasten/Kelley JBF 2024: NBBO PI “consistently overstate[s]… in some subsamples by a factor of four or more.” |

**Net:** 0/6 refuted. All six claims survive independent T1/T2 location. Residual risk is **scope/generalization** (equal-weight vs liquid, round-lot vs odd-lot, experiment clip size, TOD), not fabrication of the cited numbers.

---

## Claim-by-claim

### C1 — Wholesaler Rule 605 E/Q ≈ 0.76 full sample (Dyhrberg et al.)

**refuted: false**

**Attack vector tried:** (i) abstract-only / table misread; (ii) E/Q defined on half-spread rather than full; (iii) figure applies only to S&P 500; (iv) unreproducible secondary summary.

**Primary hit (T2):** Dyhrberg, Shkilko, Werner, “The Retail Execution Quality Landscape,” AEA 2024 program PDF (Dec 18, 2023 WP version). Table 2 (liquidity-demanding / marketable orders, WHOL vs EXCH):

| metric | WHOL | EXCH |
|--------|------|------|
| quoted spread, bps | 69.60 | 52.94 |
| effective spread, bps | 53.16 | 51.31 |
| **effective / quoted** | **0.76** | **0.97** |
| improved, % | 66.10 | 9.00 |

In-text: “In Table 2, this ratio is 0.76 for wholesalers, suggesting that orders executed by them pay 76% of the prevailing quoted spread.”

**URL:** https://www.aeaweb.org/conference/2024/program/paper/5Gtsa7ra  
**Also:** SSRN abstract_id=4313095 ; JFE 2025 print https://www.sciencedirect.com/science/article/pii/S0304405X25000595

**Non-refuting caveats (do not flip status):**  
- Sample is Rule 605 stock-months ~2019–2022; **equal-weight / share-volume-then-equal-weight** construction → wider-spread names inflate levels vs dollar-volume liquid megacaps.  
- S&P 500 retail PI ≈ 47% of *quoted spread* is a **different** statistic (implies E/Q nearer ~0.53 for that slice), not a contradiction of full-sample 0.76.  
- Legacy Rule 605 **excludes odd lots**.  
These limit **external validity** for our $400–$3k Nasdaq clips; they do not falsify the full-sample E/Q print.

---

### C2 — May 2026 wholesaler 605 shows sub-bp half-effective spreads on megacap 100–499 market orders

**refuted: false** (for classic megacaps; see scope caveats)

**Attack vector tried:** (i) files not public / wrong month; (ii) effective $ not sub-bp when converted; (iii) “half-effective” definitional error; (iv) only odd lots matter so 100–499 is irrelevant.

**Primary hit (T1):** Independent re-parse of local May 2026 legacy Rule 605 extracts (same public series as Jane Street / Virtu downloads):

- Jane Street: `202605_JNST.txt` (workspace `_tmp/JNST_605_202605.txt`)  
- Virtu Americas NITE: `TVIRTU202605.dat` (from `TVIRTU202605.zip`)

**Market orders, size bucket 100–499 shares — share-weighted avg effective $ and half-effective bps** (half-eff = ½ × effective_spread_$ / approx May-2026 mid × 10⁴):

| Name | Venue | eff $ | half-eff bps | % shares PI |
|------|-------|-------|--------------|-------------|
| NVDA | JNST | 0.0062 | **0.26** | 96.4% |
| NVDA | NITE | 0.0064 | **0.27** | 92.8% |
| AAPL | JNST | 0.0068 | **0.17** | 96.6% |
| AAPL | NITE | 0.0063 | **0.16** | 92.8% |
| MSFT | JNST | 0.0181 | **0.22** | 98.0% |
| AMZN | JNST | 0.0065 | **0.17** | 97.7% |
| GOOGL | JNST | 0.0118 | **0.35** | 96.8% |
| TSLA | JNST | 0.0203 | **0.41** | 97.4% |
| SPY  | JNST | 0.0068 | **0.06** | 92.8% |
| QQQ  | JNST | 0.0094 | **0.10** | 93.0% |

Classic megacap/ETF set is **sub-1 bp** one-sided half-effective under this conversion.

**Public file URLs (T1 publishers):**  
- https://www.janestreet.com/static/execution-quality-reports/202605_JNST.txt  
- Virtu portal → monthly zip: https://www.virtu.com/about/transparency/rule-605-and-606-reporting/

**Non-refuting caveats:**  
1. **Not all “liquid” names are sub-bp:** MU half-eff ≈ 5.2–5.6 bps; AMD ≈ 2.3–2.5 bps; INTC ≈ 1.6–1.8 bps. Share-weighted 14-name basket MKT 100–499 half-eff ≈ **1.40 (JNST) / 1.48 (NITE) bps** — so “sub-bp” is a **megacap/ETF conditional** claim, not a basket claim.  
2. **bps use external mids** (605 reports dollars, not bps). Ordering and ranking are robust; absolute bps move if mid is wrong by ~10–20%.  
3. **Legacy 605 excludes odd lots**; our $400–$3k clips are often &lt;100 sh on high-price names — claim does not prove odd-lot economics.  
4. **Marketable-limit is worse** on same files (NITE MKT half-eff ~1.48 vs MLIM ~2.34 bps share-weighted across 14 names). Claim is restricted to **market** orders — correct as worded.  
5. Rule 605 is **monthly stock×type×size** — no 15:45–16:00 slice.

None of (1)–(5) falsifies the megacap MKT 100–499 sub-bp statement.

---

### C3 — Modernized 605 odd-lot reporting compliance date = Aug 1 2026

**refuted: false**

**Attack vector tried:** (i) still Dec 14 2025; (ii) Aug 1 is only FAQ effective date, not compliance; (iii) odd-lots delayed separately beyond Aug 1.

**Primary hit (T1):** SEC *Disclosure of Order Execution Information* extension page and Release 34-104147:

> “The compliance date for the amendments to Rules 600 and 605 of Regulation NMS, published on April 15, 2024, at 89 FR 26428, is extended from December 14, 2025, to **August 1, 2026**.”

Adopted amendments (34-99679 / 89 FR 26428) explicitly add **odd-lot and fractional** order-size categories, E/Q, average quoted spread, broker-dealer reporters, summary report.

**URLs:**  
- https://www.sec.gov/rules-regulations/2025/09/disclosure-order-execution-information  
- https://www.sec.gov/files/rules/final/2025/34-104147.pdf  
- Federal Register: https://www.federalregister.gov/documents/2025/10/02/2025-19316/extension-of-compliance-date-for-disclosure-of-order-execution-information  
- Staff FAQs (effective with compliance date): https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/frequently-asked-questions-rule-605-regulation-nms  

**Non-refuting caveats:**  
- “Compliance date” = when reporters must **begin collecting/reporting under the amendments**; first monthly file covers **August 2026** activity (published after month-end), not “odd-lot E/Q panel exists on calendar day Aug 1.”  
- Price-improvement vs **best available displayed price (incl. odd-lots)** may lag further until odd-lot NMS plan data is live (FAQ Q39 six-month delay language) — that is a *metric* lag, not a separate compliance date for size buckets.  
- Citadel 605 marketing page aligning “modernized reports begin Aug 2026” is T3 corroboration only: https://www.citadelsecurities.com/rule-605-606-statements/

Claim as commonly used in the wave (**odd-lot buckets under modernized 605 → compliance Aug 1 2026**) is **not refuted**.

---

### C4 — Alpaca routes to Virtu/Citadel/JNST with PFOF 12% of spread on marketable; no auction PFOF

**refuted: false**

**Attack vector tried:** (i) different venues in current 606; (ii) 12% is options or outdated; (iii) auctions pay PFOF; (iv) 12% is paid by customer not broker.

**Primary hit (T1):** Alpaca Securities LLC *Held NMS Stocks and Options Order Routing Public Report*, **3rd Quarter 2025** (generated Oct 23 2025), material aspects for equities:

Venues named for non-directed equity flow:  
- **Virtu Americas, LLC (NITE)**  
- **Citadel Securities LLC (CDRG)**  
- **Jane Street Capital, LLC (JNST)**  

S&P 500 non-directed share of routed flow (July month tables in same filing): Virtu ≈ **43.4%**, Citadel ≈ **39.4%**, Jane Street ≈ **17.1%**.

Marketable PFOF language (repeated for each wholesaler material-aspects block):

> “Marketable orders filled during the core session will receive **12% of the spread per share, capped at 5 cents per share**.”

Auction / cross language:

- **Virtu / Jane Street:** market open **and** closing auctions/crosses → **no rebate nor charge**.  
- **Citadel:** primary **opening** auction → no rebate; primary **closing** auctions/crosses → **charge against Alpaca of 12 mils per share** (i.e., opposite of PFOF income).

So “**no auction PFOF**” (no payment *to* Alpaca for auction fills) is accurate; Citadel close is a **fee to Alpaca**, not a rebate.

**URL:** https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2025Q3.pdf  
**Library index:** https://alpaca.markets/disclosures

**Non-refuting caveats:**  
- 12% is **wholesaler → broker** compensation, not a customer line item; material-aspects text explicitly states PI and PFOF draw from the **same** anticipated market-maker profit (conflict language).  
- 606 does **not** disclose customer E/Q or PI $ — routing + PFOF only.  
- Terms can change quarter-to-quarter; this pass locked Q3 2025.

---

### C5 — Field experiment: large broker PI dispersion; IBKR worst tier

**refuted: false**

**Attack vector tried:** (i) no peer-reviewed print; (ii) IBKR not worst; (iii) dispersion only commissions; (iv) PFOF fully explains gap.

**Primary hits (T2):**

1. **Schwarz, Barber, Huang, Jorion, Odean**, “The ‘Actual Retail Price’ of Equity Trades,” *Journal of Finance* 80(5):2507–2541 (2025). Controlled parallel market orders, n≈85,000, six accounts, Dec 2021–Jun 2022:

   - Average PI **$0.03–$0.08/sh ≈ 19–47% of NBBO** across brokers.  
   - Round-trip cost (ex commission) **~7–46 bps** of notional.  
   - **IBKR Pro PI% ≈ 18.8%**; **IBKR Lite ≈ 19.5%** — bottom of the six (TD Ameritrade ~47.2% top).  
   - PFOF ($0.001–$0.003/sh) is **order of magnitude smaller** than PI dispersion; rank order **unrelated** to PFOF.

   URL: https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467  
   WP/slides corroboration: https://cqa.org/wp-content/uploads/2024/04/Huang_Actual-Retail-Price_CQA.pdf  
   Microstructure WP PDF: https://fraconference.com/wp-content/uploads/ninja-forms/2/schwarz_2022-08-31_moedb.pdf

2. **Huang, Jorion, Lee, Schwarz**, FEDS 2024-080, “Who is Minding the Store?…” (~150k parallel trades through May 2023): broker-level **E/Q** with **IBKR Lite ≈ 0.527** among the worst named zero-commission accounts; within-broker wholesaler E/Q max–min gaps **42–151% of broker mean**.

   URL: https://www.federalreserve.gov/econres/feds/files/2024080pap.pdf

**Non-refuting caveats:**  
- “Worst tier” = worst **among the six tested retail accounts**, not a universe ranking of all US brokers.  
- Main experiment clips ~**$100** (robustness $1k/$5k exist but headline ranks use small clips).  
- FEDS sample **stops by 15:50 ET** — no last-10-minute PI ranking.  
- **Alpaca is not in either experiment.** Mapping Alpaca → “mid-tier PFOF” is inference, not a measured rank.  
- IBKR **Pro** SmartRouting is exchange/ATS-oriented; “worst PI” is not the same as “worst all-in cost for large active traders.”

Caveats constrain **transfer** to our broker/size/TOD; they do not refute dispersion or IBKR’s bottom-tier PI in the published experiments.

---

### C6 — NBBO PI overstatement literature (Adams/Ernst class)

**refuted: false** (literature class exists; Adams is the cleanest T2 load-bearer)

**Attack vector tried:** (i) claim is only vendor blog (BestEx); (ii) no peer-reviewed “4×” statement; (iii) Ernst papers do not address NBBO bias.

**Primary hit (T2):** Adams, Kasten, Kelley, “How free is free? Retail trading costs with zero commissions,” *Journal of Banking & Finance* 165 (2024). ScienceDirect abstract/body (accessible snippet):

> “Price improvement relative to the NBBO may overstate the true economic cost savings of an order for multiple reasons. First, the NBBO does not account for either hidden or odd-lot liquidity available on the exchanges within the quote. Second, effective spreads for trades on the exchanges are also generally smaller than quoted spreads so the NBBO is likely the wrong counter-factual… **NBBO-based price improvement measures consistently overstate economic savings, in some subsamples by a factor of four or more.**”

**URLs:**  
- https://www.sciencedirect.com/science/article/abs/pii/S0378426624001432  
- SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4403011

**Related T2 (Ernst class / adjacent, not identical 4× claim):**  
- Ernst & Spatt, NBER w29883 (2022), “Payment for Order Flow and Asset Choice” — documents equity PI vs PFOF magnitudes and asset-class differences; not the primary “4× overstatement” citation. https://www.nber.org/system/files/working_papers/w29883/w29883.pdf  
- SEC Rule 605 modernization itself (T1) adds E/Q and best-available-displayed-price (odd-lot-aware) benchmarks precisely because legacy NBBO-relative stats were incomplete — institutional acknowledgment of the measurement channel: https://www.sec.gov/files/rules/final/2024/34-99679.pdf

**Partial scope note (not a refutation of the class):** Attributing the exact “400%” headline solely to **Ernst** is sloppy historiography; the **peer-reviewed quantitative overstatement language is Adams/Kasten/Kelley**. “Adams/Ernst class” as a **family of critiques** (NBBO too soft a benchmark; exchange already inside quote; odd-lot/hidden ignored) is still real and T2-supported.

---

## Cross-claim stress (where a *synthesis* could still over-claim)

These do **not** flip any single claim to `refuted=true`, but they are the refuter’s residual objections for report synthesis:

1. **Full-sample E/Q 0.76 ≠ liquid-Nasdaq E/Q.** Dyhrberg S&P / Brown volume-weighted work point lower (~0.45–0.55). Using 0.76 as the prior for NVDA@15:55 is a **mis-application**, not a false paper number.  
2. **May-2026 sub-bp half-eff is round-lot market, monthly, not odd-lot, not last-15-min.** Odd-lot economics for $400–$3k high-price names remain **unmeasured in legacy 605**.  
3. **Aug 1 2026 is compliance start, not “we already have modernized odd-lot E/Q files today.”** As of this pass, post-mod odd-lot E/Q panels are **not yet** a substitute for own fills.  
4. **Alpaca 606 proves routing + PFOF, not customer PI.** 12% PFOF competes with PI in the same surplus pool.  
5. **IBKR worst is experiment-conditional.** Does not rank Alpaca.  
6. **NBBO overstatement haircuts PI dollars more than it necessarily drives E/Q to 1.0.** Overstatement of *savings vs a soft benchmark* ≠ proof that retail pays full half-spread.

---

## Sources (≥6; tiered)

1. **[T2]** Dyhrberg, Shkilko, Werner (Dec 18, 2023 WP / JFE 2025). “The Retail Execution Quality Landscape.” Table 2 E/Q = 0.76. https://www.aeaweb.org/conference/2024/program/paper/5Gtsa7ra ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4313095  
2. **[T1]** Jane Street Rule 605 May 2026 (JNST). https://www.janestreet.com/static/execution-quality-reports/202605_JNST.txt (local re-parse `_tmp/JNST_605_202605.txt`)  
3. **[T1]** Virtu Americas Rule 605 May 2026 (NITE/VIRT). https://www.virtu.com/about/transparency/rule-605-and-606-reporting/ → `TVIRTU202605.zip` / `TVIRTU202605.dat`  
4. **[T1]** SEC Release 34-104147 / extension page (Sep 30 / Oct 2 2025). Compliance date **August 1, 2026**. https://www.sec.gov/rules-regulations/2025/09/disclosure-order-execution-information ; https://www.sec.gov/files/rules/final/2025/34-104147.pdf  
5. **[T1]** SEC Rule 605 Amendments Release 34-99679 (Mar 6 2024; FR Apr 15 2024). Odd-lot/fractional buckets, E/Q. https://www.sec.gov/files/rules/final/2024/34-99679.pdf  
6. **[T1]** Alpaca Securities Rule 606(a) Q3 2025. Virtu/Citadel/JNST; marketable PFOF 12% of spread; auction no-rebate / Citadel close 12 mil charge. https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2025Q3.pdf  
7. **[T2]** Schwarz, Barber, Huang, Jorion, Odean (JoF 2025). “The ‘Actual Retail Price’ of Equity Trades.” PI 19–47%; IBKR bottom. https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467  
8. **[T2]** Huang, Jorion, Lee, Schwarz (FEDS 2024-080). Broker E/Q; IBKR Lite ~0.527. https://www.federalreserve.gov/econres/feds/files/2024080pap.pdf  
9. **[T2]** Adams, Kasten, Kelley (JBF 2024). “How free is free?” NBBO PI overstates up to 4×+. https://www.sciencedirect.com/science/article/abs/pii/S0378426624001432 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4403011  
10. **[T2]** Ernst & Spatt (NBER w29883, 2022). PFOF / PI asset-class structure (adjacent to “Ernst class”). https://www.nber.org/system/files/working_papers/w29883/w29883.pdf  
11. **[T1]** SEC Staff FAQs Rule 605 (effective Aug 1 2026 with amendments). https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/frequently-asked-questions-rule-605-regulation-nms  

### Queries used

```
Dyhrberg Shkilko Werner Retail Execution Quality Landscape E/Q 0.76 wholesaler
SEC Rule 605 amendments compliance date August 1 2026 odd-lot
Alpaca Rule 606 PFOF 12% of spread Virtu Citadel Jane Street
Schwarz Barber Huang Jorion Odean Actual Retail Price IBKR price improvement
Adams Kasten Kelley How free is free retail trading costs NBBO overstates price improvement
Ernst Spatt Payment for Order Flow price improvement overstates NBBO
site:wifpr.wharton.upenn.edu price improvement overstates NBBO Ernst
"How free is free" Adams Kasten Kelley "factor of four" price improvement
```

Local recompute (not web): `python parse_605.py` / `python compute_bps.py` on `_tmp/JNST_605_202605.txt` + `_tmp/TVIRTU202605.dat`.

---

## Verdict for orchestrator

All six wave-1 claims **survive** independent T1/T2 location (`refuted=false` ×6).  
Refuter does **not** endorse unconstrained transfer of (0.76 E/Q, sub-bp megacap 605, experiment IBKR ranks) into a 15:45–16:00 Alpaca odd-lot cost prior — that is a **scope** problem for synthesis, not a source-fabrication problem.

**What would flip individual claims next pass:**  
- C1: revised Dyhrberg table in final JFE with materially different full-sample E/Q.  
- C2: official 605 field dictionary showing our eff$ column mis-mapped, or megacap mid prices off by &gt;3×.  
- C3: further SEC release moving compliance off Aug 1 2026.  
- C4: later 606 quarter removing 12% marketable PFOF or auction rebates.  
- C5: JoF erratum / replication with IBKR mid-pack.  
- C6: Adams paper retracting the 4× NBBO language without replacement literature.
