# Refutation Report — Claim Bundle X3-NEW-1 (Rule 605 modernization timeline + order-type treatment)

## C-a: Compliance-date extension (Dec 14, 2025 → Aug 1, 2026)

**Refuted: FALSE (claim confirmed).**

Primary source: SEC Release No. 34-104147, File No. S7-29-22, "Extension of Compliance Date for Disclosure of Order Execution Information" (T1 — SEC final rule). Fetched directly from `https://www.sec.gov/files/rules/final/2025/34-104147.pdf` (sec.gov WAF blocked default/naver-tagged UA with 403; succeeded via curl with an EDGAR-style contact UA string). Also cross-confirmed via Federal Register listing (2025-19316, published 2025-10-02).

Verbatim quotes:
> "the Commission is extending the compliance date for the amendments to the rules requiring the disclosure of order executions in national market system ("NMS") stocks from December 14, 2025, to August 1, 2026."

> "Compliance Date: The compliance date for the amendments to Rules 600 and 605 of Regulation NMS, published on April 15, 2024, at 89 FR 26428, is extended from December 14, 2025, to August 1, 2026."

> "On August 1, 2026, market centers, brokers, and dealers subject to Rule 605 must begin to collect the information needed to prepare the execution quality reports required under the Rule 605 Amendments... Reporting entities will then need to make their detailed and summary reports covering data from August 2026 publicly available by the end of September 2026." (footnote 18; also body text ~p.4)

On the odd-lot/E-Q sub-claim: the release confirms (footnote 20) that price-improvement statistics relative to the best available displayed price (which require odd-lot best-price data) remain due "six months after the first business day in May 2026 (i.e., in November 2026)" — the compliance-date extension explicitly did NOT extend this sub-component. This matches the claim's ~Nov 2026 estimate for odd-lot E/Q data. So both the round-lot (~end-Sept 2026) and odd-lot (~Nov 2026) timing claims check out, and no modernized odd-lot E/Q report exists as of July 2026 (today).

## C-b: Marketable-limit vs. market order execution quality (NVDA, Jane Street May-2026 605 file)

**Refuted: TRUE (claim as stated is false/misleading — mixes two unrelated sources).**

**Effective-spread sub-claim — verified accurate.** Downloaded Jane Street's actual May-2026 legacy Rule 605(a)(1) monthly file directly (`https://www.janestreet.com/static/execution-quality-reports/202605_JNST.txt`, T1 — SEC-mandated regulatory disclosure, self-published by the reporting entity). Parsed NVDA rows for order type 11 (market) and 12 (marketable limit), size bucket 21 (100–499 sh):
```
T|TJNST|202605|NVDA|11|21|...|0.0051|0.0062|...   (market: realized 0.0051, effective 0.0062)
T|TJNST|202605|NVDA|12|21|...|0.0253|0.0083|...   (marketable limit: realized 0.0253, effective 0.0083)
```
These exactly match the claim's figures: market $0.0062, marketable-limit $0.0083. This part of the claim is a genuine, accurate direct parse.

**Price-improvement-rate sub-claim (53.6% / 68.2%) — NOT from the 605 file; misattributed.** These exact figures do not appear anywhere derivable from the Jane Street file's columns. Web search + direct fetch traced them to SEC "Table V-9C: Net Price Improvement Rates in 3/8 Point Markets by Exchange and Order Size for Market and Marketable Limit Orders in NYSE-Listed Issues" (`https://www.sec.gov/news/studies/prefrep/v-9c.htm`, T1 — SEC published study, dated **1997-04-15**). Verbatim extract:
> "100 Shares — Market Orders: NYSE 68.2 ... Marketable Limits: NYSE 53.6"

This is a ~29-year-old SEC "Preferencing" study using **fractional (eighths, "3/8 point") pre-decimalization pricing**, aggregated across NYSE-listed issues on legacy exchanges (NYSE/BSE/CHX/CSE/PHLX/PSE) — it predates decimalized quoting, Reg NMS, modern wholesalers, and Rule 605 itself in its current form. It has no connection to NVDA, to Jane Street, or to May 2026. It is neither the 605 file nor academic/SSRN literature — it is a distinct, obsolete-market-structure SEC historical study.

**Conclusion:** the claim bundle presents these PI-rate numbers as if co-located with (implicitly sourced from) "a direct parse of Jane Street's May-2026 Rule 605 file" alongside the (accurate) effective-spread figures. That attribution is false — the PI-rate pair is lifted from a 1997 SEC study of a defunct fractional-pricing market structure. Overall C-b is refuted as a unified claim due to this fabricated/anachronistic sourcing, despite the effective-spread half being accurate.
