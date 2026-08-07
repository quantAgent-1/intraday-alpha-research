# DR-X3 refute-1 — retail execution quality claims

Agent role: REFUTER. Evidence standard per `research/deep/AGENT_BRIEF.md` §6 (T1/T2 required to leave claim un-refuted). Default: `refuted=true` if no primary/T1/T2 source located. Current date context: 2026-07-18.

Sources attempted (n≥12): SSRN/AEA/JFE Dyhrberg–Shkilko–Werner; ScienceDirect abstract; Jane Street 605 May 2026; Virtu 605 May 2026 + local parse; SEC Release 34-104147 / sec.gov compliance extension; FINRA Info Notice 6/17/26; SEC Rule 605 staff FAQs; Alpaca 606 2025Q3 PDF; Schwarz et al. JF / working paper; Adams–Kasten–Kelley JBF ScienceDirect; NBER Ernst–Spatt WP; Federal Register extension notice.

---

## Claim-by-claim verdicts

- **Claim 1 — Dyhrberg/Shkilko/Werner (JFE/SSRN): wholesaler liq-demanding E/Q ≈ 0.76 vs exchanges 0.97; S&P 500 retail PI ≈ 47% of quoted spread (sample ~2019–2022 Rule 605).**
  - **refuted: false**
  - **reason:** T2 primary paper tables/text match the numbers. Liquidity-demanding WHOL vs EXCH: effective/quoted = **0.76 vs 0.97**; full-sample wholesaler PI ≈ 24% of quoted spread; **S&P 500 retail PI ≈ 47%** of quoted spread (working/conference draft text). JFE published abstract (ScienceDirect snippet) restates S&P 500 PI as **51%** in one crawl — minor publish-vs-WP drift, not a refute of the ~½-spread order. Sample: Rule 605, **Jan 2019–Dec 2022** (JFE/ScienceDirect; earlier WP used through Mar 2022). Venue: *Journal of Financial Economics* 168 (2025) 104051; SSRN abstract_id=4313095.
  - **sources:** https://www.aeaweb.org/conference/2024/program/paper/5Gtsa7ra ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4313095 ; https://www.sciencedirect.com/science/article/pii/S0304405X25000595 ; https://ideas.repec.org/a/eee/jfinec/v168y2025ics0304405x25000595.html

- **Claim 2 — Jane Street / Virtu May 2026 Rule 605: market orders 100–499 on liquid Nasdaq (NVDA etc.) half-effective spreads ~0.16–0.41 bps with ~93–97% shares price-improved.**
  - **refuted: false** (with scope caveat; not a numerical refute)
  - **reason:** T1 monthly Rule 605 files for **May 2026** (JNST; Virtu NITE MPID) re-parsed this charge (`_tmp/compute_bps.py` on `JNST_605_202605.txt` / `TVIRTU202605.dat`). Market (ot=11) size 100–499 (osz=21): **NVDA** half-eff ≈ **0.26–0.27 bps**, **AAPL** ≈ **0.16–0.17**, **TSLA** ≈ **0.35–0.41**, **AMZN** ≈ **0.17–0.20**, **MSFT** ≈ **0.22–0.23** at approximate May-2026 mids — inside the claimed **0.16–0.41 bps** band for those liquid names. **% shares PI** ≈ **92.8–98.4%** on those names (claim’s 93–97% is a fair central band; SPY NITE ~88.5% is slightly outside if SPY is included). **Caveats (do not flip verdict):** (i) half-bps converts Rule 605 $ effective spread via *approximate* mids (not T1 price feed); (ii) share-weighted across 14 mixed-liquidity names is ~**1.4–1.5 bps** (MU ~5 bps, AMD ~2.3–2.5 bps) — claim correctly restricts to *liquid* names.
  - **sources:** https://www.janestreet.com/execution-quality-reports/ (May 2026 `202605_JNST.txt`); https://www.virtu.com/about/transparency/rule-605-and-606-reporting/ (May 2026 `TVIRTU202605.zip`); local parse under `research/deep/DR-X3-retail-execution-quality/_tmp/`

- **Claim 3 — SEC Rule 605 modernization compliance for odd-lot E/Q reports is August 1, 2026 (not yet required).**
  - **refuted: false**
  - **reason:** T1 SEC: compliance date for the 2024 Rule 600/605 amendments extended from Dec 14, 2025 to **August 1, 2026** (Release 34-104147; effective Oct 2, 2025). Those amendments **explicitly expand order-size categories to fractional shares, odd lots, and larger sizes** (odd-lot E/Q stats are part of the modernized package). As of 2026-07-18, compliance is **not yet required**. FINRA aligns the amended 605 Plan effective date to **August 1, 2026**; first amended monthly reports (Aug 2026) due end of Sep 2026. Staff FAQs also state FAQs effective on the Aug 1, 2026 compliance date.
  - **sources:** https://www.sec.gov/rules-regulations/2025/09/disclosure-order-execution-information ; https://www.sec.gov/files/rules/final/2025/34-104147.pdf ; https://www.federalregister.gov/documents/2025/10/02/2025-19316/extension-of-compliance-date-for-disclosure-of-order-execution-information ; https://www.finra.org/rules-guidance/notices/information-notice-20260617 ; https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/frequently-asked-questions-rule-605-regulation-nms

- **Claim 4 — Alpaca 606 (recent): marketable flow routes primarily Virtu/Citadel/Jane Street; marketable PFOF = 12% of spread capped $0.05; no PFOF on primary closing auction.**
  - **refuted: false** (minor venue nuance on Citadel closing fee)
  - **reason:** T1 Alpaca Rule 606(a)(1) Q3 2025 (generated Oct 23, 2025): S&P 500 non-directed marketable flow routes almost entirely to **Virtu (~43–45%), Citadel (~38–50% by order type), Jane Street (~16–25%)** — the three named wholesalers. Material aspects for all three: marketable core-session fills → **“12% of the spread per share, capped at 5 cents per share”** ($0.05). Virtu and Jane Street: primary open/close auctions/crosses → **no rebate nor charge**. **Nuance (not a refute of “no PFOF”):** Citadel material aspects state primary **closing** auctions incur a **12 mils/share charge against Alpaca** (still no positive PFOF rebate to Alpaca on the close; claim’s “no PFOF” is accurate for payment *to* the broker).
  - **sources:** https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2025Q3.pdf ; https://alpaca.markets/disclosures ; https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2024Q4.pdf

- **Claim 5 — Schwarz et al. JF experiment: IBKR Lite/Pro among worst PI (~19% of NBBO) vs TD ~47%.**
  - **refuted: false**
  - **reason:** T2 *Journal of Finance* published paper (“The ‘Actual Retail Price’ of Equity Trades,” Schwarz / Barber / Battalio / Jennings et al., 2025 online): across six accounts, average PI ranges **$0.03–$0.08/share ≈ 19%–47% of NBBO**, with IBKR at the low end and TD at the high end. Working-paper tables (same experiment, ~85k simultaneous market orders): **TD Ameritrade PI% of spread ≈ 47.2%**; **IBKR Lite ≈ 19.5%**; **IBKR Pro ≈ 18.8%** — claim’s “~19% vs ~47%” and “IBKR among worst” match exactly. Authors include Schwarz as lead; “Schwarz et al.” is correct attribution.
  - **sources:** https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467 ; https://microstructure.exchange/papers/Schwartz_et_al_,_2022_WP,_The_%27Actual_Retail_Price%27_of_Equity_Trades.pdf ; https://fraconference.com/wp-content/uploads/ninja-forms/2/schwarz_2022-08-31_moedb.pdf

- **Claim 6 — Adams/Kasten/Kelley or Ernst: NBBO-based PI can overstate true economic savings by large factors (up to ~4×).**
  - **refuted: false** (for Adams–Kasten–Kelley; Ernst does not carry the 4× figure)
  - **reason:** T2 Adams, Kasten, Kelley, *Journal of Banking & Finance* 165 (2024), “How free is free? Retail trading costs with zero commissions”: ScienceDirect abstract/body state **“NBBO-based price improvement measures consistently overstate economic savings, in some subsamples by a factor of four or more.”** Exact match to claim. **Ernst & Spatt** (NBER w29883 / SSRN) document PFOF vs PI tradeoffs across stocks/options but **do not** supply the “up to ~4×” overstatement result — the “or Ernst” limb is weak, but the claim is disjunctive and Adams et al. alone sustains it.
  - **sources:** https://www.sciencedirect.com/science/article/abs/pii/S0378426624001432 ; https://ideas.repec.org/a/eee/jbfina/v165y2024ics0378426624001432.html ; https://www.nber.org/system/files/working_papers/w29883/w29883.pdf (Ernst—no 4×)

---

## Summary

| # | Claim (short) | refuted | Tier supporting leave-as-unrefuted |
|---|---------------|---------|-------------------------------------|
| 1 | DSW E/Q 0.76/0.97; S&P PI ~47% | **false** | T2 JFE/SSRN |
| 2 | JNST/Virtu May-26 half-eff 0.16–0.41 bps; 93–97% PI | **false** | T1 Rule 605 + local parse |
| 3 | Rule 605 odd-lot modernization compliance Aug 1, 2026 | **false** | T1 SEC/FINRA |
| 4 | Alpaca 606 → Virtu/Citadel/JS; 12% spread cap $0.05; no close PFOF | **false** | T1 Alpaca 606 |
| 5 | Schwarz JF: IBKR ~19% vs TD ~47% PI | **false** | T2 JF |
| 6 | Adams et al.: NBBO PI overstates up to ~4× | **false** | T2 JBF |

**None of the six claims is refuted under AGENT_BRIEF T1/T2 standards.** Residual risks are scope/wording only: (C1) published S&P PI may read 51% vs WP 47%; (C2) half-bps uses approximate mids and applies to liquid-name subset not share-weighted all-names; (C4) Citadel closes with a fee *to Alpaca* rather than pure zero; (C6) Ernst is not the 4× source.
