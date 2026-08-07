## DR-X1 — B primary/venue findings
### Verdict recommendation
OPEN-TESTABLE (confidence MED) — T1 prospectuses/SAI establish daily end-of-day rebalance via total-return swaps (major bank counterparties) + equity/futures sleeves; Direxion Trust language states Rafferty “ordinarily executes … market-on-close”; ProShares positions “at the close of the U.S. securities markets.” Free SEC N-PORT bulk (2019Q4→2026Q2) + issuer daily holdings/NAV files give AUM and swap-notional anchors for Cheng–Madhavan (L²−L)·AUM·r without paid aggregators. Residual T1 gap: exact hedge venue mix of *swap counterparties* (MOC auction vs continuous vs OTC futures) is not fully prospectus-disclosed and must be inferred from T2/T3 + owned NOII.
What would flip it: a T1 counterparty/brokerage/exchange notice that bulk single-name LETF rehedge is systematically continuous/OTC and *not* close-timed (would break auction-payer linkage).

### Mechanism
Who pays: LETF swap counterparties (and any physical equity sleeve of the fund) must re-set notional exposure each day so fund exposure equals L×AUM at the NAV stamp; rebalance dollar demand ≈ (L²−L)·AUM·r_day (Cheng–Madhavan). Flow is price-insensitive by mandate (daily investment objective language). Persists because product design and AUM (TQQQ alone ~$34–36B; SOXL mid-teens–$20B+; single-stock NVDA/TSLA/MU bull products multi-billion) keep notional large. Capacity: index LETFs distribute pressure across NDX/SOX/SPX baskets; single-stock LETFs concentrate pressure on one name — largest single-name AUMs (NVDL/TSLL/MUU multi-B; AVGO/NFLX/LRCX products typically ≪$0.3B) explain name-selectivity. Hedge path is dual: fund may MOC cash equities; counterparties hedge swaps near close (T2/T3), partially via futures (e.g. NQ e-mini in TQQQ holdings).

### Claims
C1 [CONFIRMED] (T1, 2023-10-01 prospectus, ongoing): TQQQ seeks 3× daily NDX; “seeks to rebalance its portfolio each day”; principal instruments = swap agreements with major global financial institutions + futures + equities; NAV calculation 4:00 p.m. ET. — https://www.sec.gov/Archives/edgar/data/1174610/000168386323006700/f36277d1.htm ; https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq
C2 [CONFIRMED] (T1, ProShares older 497K language, still representative): “At the close of the U.S. securities markets on each trading day, the Fund will seek to position its portfolio so that its exposure to the Index is consistent with the Fund’s investment objective.” — https://www.sec.gov/Archives/edgar/data/1174610/000119312514356432/d768699d497k.htm
C3 [CONFIRMED] (T1, Direxion 485APOS 2025-09-26 Trust materials): “Rafferty ordinarily executes transactions for the Fund ‘market-on-close,’ in which funds purchasing or selling the same security receive the same closing price.” (Trust-level execution policy; not a full counterparty-hedge map.) — https://www.sec.gov/Archives/edgar/data/1424958/000119312525220775/d909538d485apos.htm
C4 [CONFIRMED] (T1, issuer holdings 2026-07): TQQQ net assets ~$34.1B (ProShares site 2026-07-16); exposure dominated by Nasdaq-100 index swaps (BofA, Citi, BNP, JPM, Barclays, SocGen, Nomura, GS, UBS, MS) plus NQ e-mini; cash equity sleeve is partial. — https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq
C5 [CONFIRMED] (T1, SEC DERA, through 2026Q2): Form N-PORT monthly portfolio reports; public bulk ZIP free at sec.gov (2019Q4–2026Q2); includes net assets, full holdings (incl. swap notionals where reported). Current public cadence: generally 3rd month of fiscal quarter public ≤60 days after quarter-end; 2024 monthly-public amendments delayed (compliance ~2027–28); 2026 proposal would keep quarterly public. — https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
C6 [CONFIRMED] (T1, SEC DERA): Form N-CEN annual census free bulk; ETF Part E (APs, creation/redemption practices, service providers); lag ≈ fiscal year + filing window (~75 days); not a daily AUM series. — https://www.sec.gov/data-research/sec-markets-data/form-n-cen-data-sets ; https://www.sec.gov/files/formn-cen.pdf
C7 [CONFIRMED] (T1, issuer sites 2026-07): Daily holdings files available free: ProShares `psdlyhld.csv` + historical NAVs CSV; Direxion per-fund “Daily Fund Holdings (csv)”; GraniteShares NVDL daily XLS. History retention on issuer sites is point-in-time / short-window, not a multi-year free AUM archive — use N-PORT net assets for 2022–2026 AUM history at $0. — https://www.proshares.com/resources/data-downloads ; https://www.direxion.com/product/daily-nvda-bull-and-bear-leveraged-single-stock-etfs ; https://graniteshares.com/etfs/nvdl/
C8 [PLAUSIBLE] (T1+T3 snapshot 2025–2026, sample mid-2024→mid-2026): Universe AUM rank (approx.): TQQQ ~$34–36B (3× NDX, inc. 2010-02-09); SOXL ~$14–26B (3× semi, inc. 2010-03-11); single-stock bull: MUU ~$5.5B, TSLL ~$4–5.7B, NVDL ~$4.0B, GGLL ~$1.1B, NVDU ~$0.6B, AVL/AVGO ~$0.2B, NFXL ~$0.16B — supports single-name pressure rank NVDA-complex + TSLA + MU ≫ AVGO/NFLX/LRCX. — ETF.com/ETFdb/issuer pages (aggregator T3 for exact $; T1 NAVs for verification)
C9 [CONFIRMED] (T2, Cheng–Madhavan 2009; Lenkey survey 2024-12-23; sample literature 2006–2018): Theoretical rebalance demand (L²−L)·AUM·r; literature associates LETF rebalance with late-day returns/vol but economic magnitude often small after flows; sponsors/practitioners describe MOC orders and broker pre-hedging before close. — https://doi.org/10.3934/QFE.2024031
C10 [UNVERIFIED] (T1 gap): Prospectuses do **not** map swap-counterparty hedge inventory to Nasdaq MOC auction vs continuous last-30-min vs OTC futures in a name-level, quantifiable way; venue attribution for single-stock pressure remains empirical (NOII/owned data), not filing-proven.

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | PASS | Close-timed rebalance is scheduled; 5–25 s manual is pre-positionable before 15:55–16:00. |
| 2 Access | PASS | Trade underlyings MOC/LOC or continuous via retail; no need to trade LETF itself. |
| 3 Session | PASS | Auction/AT-close structure is in-mission (flat at 16:00 cross). |
| 4 Data | PASS | AUM/holdings: free N-PORT + issuer daily files; NOII owned; ≤$100 not required for primary/venue. |
| 5 Fill realism | PASS | Test design should use auction single-print or taker-priced legs; continuous fill claims need condition codes. |
| 6 Statistics | PASS | Daily mechanism → n≫250 over 2022–2026 sessions on owned names if evented on |r| or NOII thresholds. |
| 7 Protocol | PASS | Named payer (LETF swap-CP rehedge) pre-statable; (L²−L)·AUM·r rank is a-priori; charges a new close-flow family, not dead M7/M6b. |

Survivor-profile score: **4/5** — (1) auction/single-print path available ✓ (2) scheduled decision ✓ (3) named price-insensitive payer ✓ (4) free/≤$100 testable ✓ (5) expected effect ≥2× cost **unproven here** (venue modality only; econ left to empirical modality).

### Economics sketch
Gross: not measured in this modality. Order-of-magnitude flow only: for L=2, demand ≈ 2·AUM·r (e.g. $4B NVDL → ~$80M per +1% NVDA day); for L=3 index, demand ≈ 6·AUM·r (TQQQ $35B → ~$2.1B basket-wide per +1% NDX day, of which NVDA weight fraction hits the name). Cost burden for champion-style MOC/basis structure ≈ same as live edge (spread+slip to auction). Net prior: UNKNOWN until NOII/return event study. Comparison: champion = +2.5 bps/event dev / +12.5 holdout.

### Proposed next test (only if OPEN-TESTABLE)
Hypothesis: On high-|r| days, single names with top (L²−L)·AUM exposure (aggregate bull+bear single-stock LETFs + index-LETF basket weight) show larger 15:50→16:00 continuation and/or larger |NOII| same-direction vs low-LETF peers.
Named payer: LETF daily rehedge (swap CP + any fund MOC equity sleeve).
Data: owned Databento NOII + SIP returns; free N-PORT month-end AUM (lag-tolerant for ranks); free issuer daily holdings for swap notionals cross-check. $0 incremental.
Universe: NVDA, TSLA, AMD, MU, GOOGL, AVGO, NFLX, LRCX (+ QQQ/SMH anchors).
Expected n: ~500–700 RTH sessions 2023-09→2026 (post single-stock LETF launch wave) if evented on |r|≥1–2% or top-quartile pressure; power OK vs ~20 bps/event noise for ≥5–10 bps mean.
A-priori thresholds: pre-register pressure rank (NVDA-complex ≥ TSLA ≥ MU ≫ AVGO/NFLX/LRCX) and event def before looking at holdout-forward.
Promotion: Stage A mean ≥ +5 bps/event net of honest fills, n≥250, same-sign on ≥2 independent names.
Kill: |effect| < cost after 150 sessions; or pressure rank fails (AVGO/NFLX not ≪ NVDA/TSLA); or NOII shows no close concentration on high-pressure days.
Trial family: new “DR-X1 LETF close-flow” (not reopening dead intraday letf_window).

### Sources
1. [T1] ProShares UltraPro QQQ Summary Prospectus, 2023-10-01 — https://www.sec.gov/Archives/edgar/data/1174610/000168386323006700/f36277d1.htm
2. [T1] ProShares UltraPro QQQ product page / holdings / net assets, as-of 2026-07-16 — https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq
3. [T1] ProShares 497K historical close-of-markets rebalance language — https://www.sec.gov/Archives/edgar/data/1174610/000119312514356432/d768699d497k.htm
4. [T1] Direxion Shares ETF Trust 485APOS, 2025-09-26 (MOC ordinary execution) — https://www.sec.gov/Archives/edgar/data/1424958/000119312525220775/d909538d485apos.htm
5. [T1] SEC Form N-PORT Data Sets (bulk free, 2019Q4–2026Q2) — https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
6. [T1] SEC Form N-CEN Data Sets + Form N-CEN PDF — https://www.sec.gov/data-research/sec-markets-data/form-n-cen-data-sets ; https://www.sec.gov/files/formn-cen.pdf
7. [T1] ProShares Data Downloads (daily holdings + historical NAV CSV) — https://www.proshares.com/resources/data-downloads
8. [T1] Direxion NVDU/NVDD product page (daily holdings link; inc. 2023-09-13) — https://www.direxion.com/product/daily-nvda-bull-and-bear-leveraged-single-stock-etfs
9. [T1] GraniteShares NVDL product page (daily holdings XLS) — https://graniteshares.com/etfs/nvdl/
10. [T1] Direxion SOXL product (inc. 2010-03-11; 3× semi) — https://www.direxion.com/product/daily-semiconductor-bull-bear-3x-etfs
11. [T2] Lenkey (2024-12-23), “The market impact of leveraged ETFs: A Survey of the literature,” QFE — https://www.aimspress.com/article/doi/10.3934/QFE.2024031
12. [T2] Cheng & Madhavan (2009), JOIM; Tuzun Fed working paper on LETF rebalancing
13. [T1/T3] N-PORT rule status: 2024 amendments delayed; 2026 proposal to restore quarterly public — e.g. https://www.sec.gov/rules-regulations/2025/04/s7-26-22 ; K&L Gates / Dechert notes 2026-02/03
14. [T3] AUM snapshots ETFdb/ETF.com/issuer (NVDL ~$4B, TSLL multi-B, MUU ~$5.5B, GGLL ~$1.1B, NFXL ~$0.16B, AVL ~$0.2B) — rank only; verify via N-PORT

#### Queries used
- Direxion TQQQ prospectus SAI rebalance daily leverage swap MOC auction
- ProShares SSO UPRO prospectus daily rebalancing execution timing hedges
- SEC N-PORT N-CEN leveraged ETF AUM holdings bulk access lag cadence
- single stock leveraged ETF NVDA TSLA Direxion GraniteShares AUM rebalance
- Cheng Madhavan leveraged ETF rebalancing flow close auction MOC
- TQQQ SOXL AUM 2024 2025 2026 leverage inception ProShares Direxion
- "market on close" OR "closing auction" OR "end of day" rebalancing swap counterparty leveraged ETF prospectus
- SEC EDGAR N-PORT bulk download free API etf net assets historical
- Direxion daily holdings AUM historical download NVDL TSLL NVDU prospectus swap
- Tuzun Fed leveraged ETF rebalancing impact market close
- NVDL TSLL AUM 2025 2026 GraniteShares Direxion single stock leveraged ETF assets
- ProShares TQQQ prospectus "swap agreements" rebalance daily investment results site:sec.gov
- ProShares daily holdings download history retention TQQQ AUM historical
- Form N-CEN contents annual report ETF total assets free bulk download SEC
- Direxion ProShares prospectus "does not disclose" OR "market-on-close" OR "closing auction" rebalancing hedge counterparty
- Cheng Madhavan rebalancing formula (L^2 - L) AUM return MOC volume
- ETFDB TSLL NVDL AMDL GGLL MUU NFLX leveraged single stock AUM July 2026
- N-PORT public lag 60 days quarterly third month only current rules 2026
- TSLL AUM Direxion GGLL AVGO leveraged ETF single stock assets under management
