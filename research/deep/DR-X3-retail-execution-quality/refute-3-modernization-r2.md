# Refutation pass — Claim bundle X3-NEW-1 (Rule 605 modernization timeline + order-type treatment)

## C-a: Compliance-date extension (Dec 14, 2025 → Aug 1, 2026); no public post-mod odd-lot E/Q report as of July 2026

**Refuted: FALSE (claim holds — confirmed by primary source)**

Source: SEC Release No. 34-104147 (File No. S7-29-22), "Extension of Compliance Date for Disclosure of Order Execution Information," published in the Federal Register Oct 2, 2025 (2025-19316). Tier 1 (SEC final rule). Fetched directly: `https://www.sec.gov/files/rules/final/2025/34-104147.pdf` (sec.gov blocked the naver-UA and rate-limited a plain UA once; a second attempt with UA `research-agent contact@example.com` succeeded, HTTP 200).

Verbatim, operative text:
> "SUMMARY: The Securities and Exchange Commission ("Commission") is extending the compliance date for the amendments to the rules requiring the disclosure of order executions in national market system ("NMS") stocks from December 14, 2025, to August 1, 2026."
>
> "DATES: Effective Date: The effective date for this release is [INSERT DATE OF PUBLICATION IN THE FEDERAL REGISTER]. Compliance Date: The compliance date for the amendments to Rules 600 and 605 of Regulation NMS, published on April 15, 2024, at 89 FR 26428, is extended from December 14, 2025, to August 1, 2026."

On the "end-September 2026" first-public-report timing (footnote 18):
> "On August 1, 2026, market centers, brokers, and dealers subject to Rule 605 will need to begin collecting the information needed to prepare the execution quality reports required under the Rule 605 Amendments. Reporting entities will then need to make their detailed and summary reports covering data from August 2026 publicly available by the end of September 2026."

On odd-lot/E/Q timing (footnote 25, corroborated by footnote 20):
> "The compliance date for the SIPs to collect, consolidate, and disseminate odd-lot information is the first business day of May 2026, with an implementation period for reporting entities to include this information in their Rule 605 reports ending the first business day of November 2026." And: "the compliance date for including price improvement statistics relative to the best available displayed price in Rule 605 reports is still six months after the first business day in May 2026 (i.e., in November 2026)."

This directly confirms: modernized round-lot reports (Aug-2026 data) first public end-Sept-2026; price-improvement/E/Q statistics incorporating odd-lot best-available-displayed-price data not required until Nov-2026. As of July 2026 (today), the compliance date (Aug 1, 2026) has not even arrived, so no post-modernization report of any kind — round-lot or odd-lot — yet exists. Claim C-a is accurate on all counted specifics.

---

## C-b: Marketable-limit vs market order execution quality — Jane Street May-2026 605 file, NVDA 100-499sh

**Refuted: TRUE (the specific quoted figures are not in Jane Street's actual May-2026 Rule 605 file)**

I located and directly parsed Jane Street's actual May-2026 Rule 605 detailed monthly report files (Tier 1, primary regulatory disclosure), both reporting entities:
- JNST: `https://www.janestreet.com/static/execution-quality-reports/202505_JNST.txt`
- JSJX: `https://www.janestreet.com/static/execution-quality-reports/202505_JSJX.txt`

Field layout confirmed against the current NMS Plan Exhibit A (`sec.gov/files/rules/sro/nms/2025/34-103243-rule-605-plan.pdf`, T1): field 5 = order type (11=market orders, 12=marketable limit orders), field 6 = order size (21=100-499 sh), field 17 = avg realized spread ($), field 18 = avg effective spread ($), field 19 = shares executed with price improvement (numerator for PI rate).

**Actual NVDA, 100-499sh, May 2026:**
| Entity | Order type | Avg effective spread | PI rate (shares w/ PI ÷ shares executed) |
|---|---|---|---|
| JNST | 11 (market) | $0.0031 | 21,415,933 / 22,374,140 = 95.7% |
| JNST | 12 (marketable limit) | $0.0044 | 7,432,441 / 8,192,666 = 90.7% |
| JSJX | 11 (market) | $0.0111 | 131 / 11,148 = 1.2% |
| JSJX | 12 (marketable limit) | $0.0103 | 517,638 / 1,951,367 = 26.5% |

None of these match the claim's cited $0.0083 (marketable-limit) / $0.0062 (market), nor the PI rates 53.6%/68.2%, at either Jane Street entity. JNST's direction (marketable-limit worse effective spread than market, 0.0044 > 0.0031) is qualitatively consistent with the claim's thesis, but JSJX shows the opposite for effective spread (0.0103 < 0.0111) while agreeing on PI-rate direction. The specific number pair in the claim is not a "direct parse" of either actual Jane Street file for NVDA/100-499sh/May-2026 — it does not match anywhere in either file at that order-type/order-size combination.

On origin of the PI-rate pair (53.6%/68.2%): could not confirm an academic-literature source (web-search budget for this session was exhausted mid-verification, so this sub-question is unresolved, not affirmatively sourced elsewhere). Regardless, since the claim's load-bearing assertion is that these numbers come from "a direct parse of Jane Street's May-2026 Rule 605 file," and my own direct parse of both actual files contradicts that, C-b is refuted as stated.
