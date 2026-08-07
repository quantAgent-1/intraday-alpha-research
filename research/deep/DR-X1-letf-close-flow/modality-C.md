## DR-X1 — C practitioner findings
### Verdict recommendation
OPEN-TESTABLE (confidence MED) — Practitioner/vendor and academic-desk consensus is coherent: single-stock LETFs hold exposure via total-return swaps; swap counterparties rebalance notional at the close to hit L× daily return, generating price-insensitive flow of order (L²−L)·AUM·r in the same direction as the day’s stock move. AUM concentration confirms NVDA ≳ TSLA ≫ AVGO/NFLX/LRCX; free AUM history is reconstructible well under $100. Timing is **not pure auction-print**: literature and MOC-volume models place the hedge in the last ~30 minutes / at the close (continuous + MOC mix), so fill realism is weaker than the champion NOII basis trade—but the signal is still scheduled (day return known by ~15:50) and testable on owned SIP/NOII plus free AUM.
What would flip it: clean measurement that single-stock LETF swap re-hedge is ≥70% continuous late-session (not MOC/auction) *and* that predicted rebalance days produce no measurable close-window pressure or auction basis shift on NVDA/TSLA at our size (net ≤0 after costs on n≥250).

### Mechanism
**Who pays:** Swap dealers / broker-dealer counterparties to bull and inverse single-stock LETFs (and, secondarily, index LETFs that hold the name). The fund does not typically hold a full physical stock book; it holds swaps + cash collateral. The counterparty delta-hedges the swap book in the underlying.

**Why price-insensitive:** Contractual daily-reset mandate forces notional to equal L × AUM at the NAV print. Required rebalancing dollar flow (no fund-flow term) is Δ = (L² − L) · AUM · r = L(L−1)·AUM·r (Cheng–Madhavan; Bank of England practitioner note). For L=+2 this is 2·AUM·r; for L=−1 it is 2·AUM·r (same sign as underlying move for both bull and inverse). Flow direction is mechanical once r is known—not discretionary alpha seeking.

**Why it persists:** Daily-reset product design + retail/tactical demand for single-stock leverage (channel ~$31–34B single-stock / ~$170–200B broader levered+inverse as of 2026). Counterparties pass hedge cost into swap spreads; the mandate does not disappear when impact rises.

**Capacity intuition:** On a +2% NVDA day with ~$4.5B long-2× NVDA AUM (NVDL alone ~$4B; NVDX ~$0.46B), Δ ≈ 2 × $4.5B × 0.02 ≈ **$180M** NVDA buy. That is a small fraction of NVDA ADV (multi-billion $) but a non-trivial slice of late-day / MOC. Same math on AVL (~$0.21B) yields ~$8M—noise vs AVGO ADV. Ranking by (L²−L)·AUM is therefore also the ranking of *detectable* close pressure: **NVDA ≳ TSLA ≫ AVGO ≫ NFLX ≈ LRCX**.

### Claims
C1 [CONFIRMED] (T2/T3, 2021–2022 pubs, sample ~2010–2020 index LETFs + options): LETF swap counterparties rebalance **at the close / last half-hour** with little timing discretion; option MM delta-hedge is more flexible and often earlier. End-of-day return coefficient on LETF rebalancing is significant only in the final window. — Barbon/Beckmeyer/Buraschi/Moerke (FMA/SSRN), Alpha Architect practitioner summary (2022-06-01); https://fmai.memberclicks.net/assets/docs/Derivatives2021/beckmeyer_etf_options.pdf ; https://alphaarchitect.com/options-hedging-leveraged-etfs-in-market-swings/

C2 [CONFIRMED] (T2, Cheng–Madhavan 2009/2010; survey 2024): Rebalance demand ΔI = m(m−1)r A = (L²−L)·AUM·r; on a 5% move, modeled LETF flow was historically ~50% of median **MOC** volume (index-era calibration). — Cheng & Madhavan; AIMS survey QFE 2024; https://www.aimspress.com/article/doi/10.3934/QFE.2024031

C3 [CONFIRMED] (T2, Shum et al. 2016, sample 2006–2011 US equities): End-of-day volatility correlates with potential rebalancing / volume; on large-move days LETF rebalancing can account for up to ~50% of MOC volume. — Review of Finance; SSRN abstractid=2161057

C4 [CONFIRMED] (T3 vendor, as-of mid-2026): Single-stock ETF channel ≈ **$31–34B** AUM across hundreds of products; levered sleeve dominates. Issuers: Direxion ~$11.5B, GraniteShares ~$7.6B (channel share). — ETF.com (2026-05-20); ETF Action (2026-02-22); https://www.etf.com/sections/news/nvdl-returned-172-one-year-new-era-leveraged-etfs-working ; https://www.etfaction.com/conviction-rising-levered-strategies-drive-single-stock-etf-aum-to-new-heights/

C5 [CONFIRMED] (T3 issuer/Yahoo/etfdb snapshot ~2026-07): Approximate long-2× AUM by underlying (gross of small inverse books): **NVDA** NVDL ~$3.8–4.2B + NVDX ~$0.46B → ~$4.3–4.7B; **TSLA** TSLL ~$4.1–4.5B + TSLT ~$0.26B + TSLR ~$0.09–0.11B → ~$4.5–4.9B; **AVGO** AVL ~$0.20–0.22B (+ smaller peers e.g. AVGG/AVGX); **NFLX** NFXL ~$0.15B + NFLU ~$0.05B → ~$0.20B; **LRCX** LRCU ~$0.08B. Ranking by (L²−L)·AUM for L=2 is **TSLA ≈ NVDA ≫ AVGO ≳ NFLX > LRCX** (charge’s NVDA>TSLA order is AUM-epoch dependent; both dwarf the rest). — Yahoo Finance net assets; GraniteShares/Direxion product pages; etfdb.

C6 [PLAUSIBLE] (T3 holdings/prospectus): Single-stock LETFs achieve exposure primarily via **equity total-return swaps** (Clear Street / Marex / Cantor etc. appear on holdings), not full physical stock; hedge execution is therefore a **dealer desk** problem in the cash name near NAV time, not pure AP creation basket. — Leverage Shares AVGG holdings example; issuer prospectuses.

C7 [PLAUSIBLE] (T2/T3, no 2024–2026 single-stock-specific T1 desk tape): Fraction of single-stock re-hedge that prints as **MOC vs continuous 15:30–16:00 vs OTC/internalization** is **UNKNOWN**. Index-era work used MOC volume as the capacity yardstick and last-30m TAQ returns as the impact yardstick; neither isolates Nasdaq close-auction share for NVDL/TSLL-class books.

C8 [CONFIRMED] (T1 free data): Historical AUM ≤$100 is available: SEC Form **N-PORT** bulk free (monthly series net assets); issuer **daily holdings CSVs** (Direxion); reconstruct AUM ≈ shares outstanding × NAV from free Yahoo/issuer NAV series. No paid vendor required for Stage A. — https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets ; https://j-kahn.com/nport/

C9 [UNVERIFIED] (T3, conflicted if vendor-sold): Practitioner “build your own LETF rebalance tracker” recipe (sum AUM by underlying × L(L−1)×r) is public (e.g. Damped Spring / desk Twitter 2026) but provides no audited single-stock impact table for 2024–2026. — X/dampedspring (hypothesis-generation tier if used alone).

C10 [PLAUSIBLE] (T3 2026 ETF.com): NVDL-class products have material **secondary-market footprint** (multi-million share ADV on the ETF; multi-billion AUM) but that is ETF-share liquidity, not proof of proportional cash-stock MOC impact—swap hedge still routes through dealer books. Gross impact claims without TAQ condition codes should be treated as NO-COST-MODEL / fill-ambiguous (project trap §7).

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | PASS | Day return r known by ~15:50; decision is scheduled; 5–25 s manual OK for MOC/LOC or late taker. |
| 2 | Access | PASS | Trade underlying (NVDA/TSLA/…) via retail broker; MOC/LOC at Alpaca/IBKR need T1 cutoff verify before deploy—not a research block. |
| 3 | Session | PASS | Flat at close via MOC/LOC is in-mission; continuous 15:50–15:59 exit is also flat-by-close if forced. |
| 4 | Data | PASS | Own SIP + NOII; AUM free (N-PORT / issuer CSV / Yahoo) ≪ $100 one-time. |
| 5 | Fill realism | FAIL→conditional | If edge requires continuous last-30m mid fills → same trap family as M3. If edge is auction basis / single print WITH predicted LETF MOC → closer to champion. Split unknown (C7). |
| 6 | Statistics | PASS | Daily events on 2–5 names × multi-year single-stock LETF life (NVDL from 2022-12; TSLL from 2022-08) → n≫250 sessions easily. |
| 7 | Protocol | PASS | Named payer = swap CP rebalance; a-priori threshold on predicted |Δ| / ADV or / auction size; charges a **new** close-flow family (not the killed intraday letf_window of M3/M5). |

Survivor-profile score: **3/5**
1. Single-print/auction execution — **0** (mix continuous+MOC; not pure auction unless test restricts to MOC/LOC).
2. Scheduled decision instant — **1**
3. Named price-insensitive payer — **1**
4. Historically testable owned/≤$100 — **1**
5. Expected effect ≥2× cost at our size — **0** (unmeasured; megacap ADV likely dilutes bps; may fail).

### Economics sketch
Expected gross: literature reports **large relative** end-of-day return effects on high-rebalance days (e.g. 1σ LETF rebalance ≈ several× average last-30m return in index-era samples) but **no clean net-of-spread single-stock 2024–2026 table** (NO-COST-MODEL for strategy PnL). Order-of-magnitude notional: (L²−L)·AUM·r ≈ $50–200M on big NVDA/TSLA days; as % of name ADV often **low single-digit %**, so impact may be **sub-5–15 bps** of continuous mid—possibly **below** retail half-spread + slippage on a taker plan.
Our cost burden: taker cross ~1–5 bps typical megacap; MOC/LOC avoids continuous exit spread but pays auction uncertainty. Net prior: **~0 to low-single-digit bps/event** until measured—**well below** champion = **+2.5 bps/event dev / +12.5 holdout** unless rebalance concentrates in the auction and co-moves NOII basis.

### Proposed next test (only if OPEN-TESTABLE)
- **Hypothesis:** On days when predicted single-stock LETF rebalance |Δ| = Σ_funds |(L²−L)·AUM·r| exceeds a fixed ADV fraction (e.g. ≥0.5% of 20d ADV), the underlying’s **15:55 NOII basis** (near − mid) and/or **15:30→close return** is biased in the direction of Δ, with partial overnight reversal (mechanical pressure).
- **Named payer:** Swap counterparties to NVDA/TSLA (±AVGO) single-stock LETFs.
- **Data:** Owned Databento NOII + Alpaca SIP; free daily AUM from issuer holdings / N-PORT / shares×NAV. $0 incremental if restricted to free AUM; optional paid AUM vendor only if free reconstruction fails (state $ before buy).
- **Universe:** NVDA, TSLA primary; AVGO secondary control (low AUM); NFLX/LRCX power-check (expect null).
- **Expected n & power:** ≥400 sessions post each fund’s AUM>$100M threshold; mean effect need ≳5–8 bps vs ~20 bps event noise for Stage A power.
- **A-priori thresholds:** Primary = sign(Δ) matches sign(15:30→close) hit-rate >55% on |Δ|/ADV top tercile; secondary = |NOII basis| larger on top-tercile |Δ| days. Gross mean ≥ +5 bps/event before costs.
- **Promotion rule:** Holdout-forward only (M10-style); sealed holdout already spent—no re-use.
- **Kill criteria:** Net ≤0 after honest taker/MOC costs; or effect only in continuous last-30m with condition-code phantom fills; or concentrated in top 5 sessions.
- **Trial family charged:** new family **DR-X1 close-rebalance** (distinct from dead intraday letf_window).

### Sources
1. [T2] Barbon, Beckmeyer, Buraschi, Moerke — *The Role of Leveraged ETFs and Option Market Imbalances on End-of-Day Price Dynamics* (FMA/SSRN ~2021). https://fmai.memberclicks.net/assets/docs/Derivatives2021/beckmeyer_etf_options.pdf
2. [T3] Alpha Architect — Options Hedging & Leveraged ETFs in Market Swings (2022-06-01). https://alphaarchitect.com/options-hedging-leveraged-etfs-in-market-swings/
3. [T2] Shum, Hejazi, Haryanto, Rodier — Intraday Share Price Volatility and Leveraged ETF Rebalancing, *Review of Finance* 2016 (sample 2006–2011). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2161057
4. [T2] Cheng & Madhavan — Dynamics of Leveraged and Inverse ETFs (2009/2010); formula and MOC % calibration as restated in AIMS QFE survey 2024. https://www.aimspress.com/article/doi/10.3934/QFE.2024031
5. [T3] Bank Underground (BoE) — Leveraged and inverse ETFs… (2023-08-31); table of rebalance = N·D·(L²−L). https://bankunderground.co.uk/2023/08/31/leveraged-and-inverse-etfs-the-exotic-side-of-exchange-traded-funds/
6. [T3] ETF.com — NVDL Returned 172%… single-stock levered >$31B (2026-05-20). https://www.etf.com/sections/news/nvdl-returned-172-one-year-new-era-leveraged-etfs-working
7. [T3] ETF Action — Single Stock ETF channel $34.3B / issuer league (2026-02-22). https://www.etfaction.com/conviction-rising-levered-strategies-drive-single-stock-etf-aum-to-new-heights/
8. [T3] Yahoo Finance / issuer pages — NVDL, TSLL, NVDX, TSLT, TSLR, AVL, NFXL, NFLU, LRCU net assets (~2026-07). e.g. https://finance.yahoo.com/quote/NVDL/ ; https://finance.yahoo.com/quote/TSLL/
9. [T1] SEC Form N-PORT Data Sets (free bulk AUM/holdings). https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
10. [T3] Leverage Shares / REX / Direxion / GraniteShares product & holdings pages (swap structure, product list). e.g. https://leverageshares.com/us/etfs/leverage-shares-2x-long-avgo-daily-etf/
11. [T2] Who trades at the close? (J. Fin. Markets abstract)—index/LETF contribution to closing volume. https://www.sciencedirect.com/science/article/abs/pii/S1386418123000502

#### Queries used
- LETF rebalance hedge flow MOC close auction swap dealer delta hedge practitioner
- NVDL TSLL single stock leveraged ETF AUM market footprint 2024 2025
- leveraged ETF rebalancing end of day continuous trading vs closing auction
- single stock LETF AUM tracker Direxion GraniteShares T-Rex 2024 2025 2026
- LETF rebalancing flow formula (L^2 - L) AUM daily rebalance notional
- NVDL TSLL AUM historical ETF.com etfdb free data single stock leveraged
- AVL AVGO leveraged ETF AUM LRCX NFLX single stock 2x ETF assets
- "swap counterparty" OR "total return swap" LETF rebalance MOC OR "market on close" practitioner OR desk
- NFLX LRCX 2x leveraged ETF AUM NVDX TSLR CONL single stock
- free historical ETF AUM data download Yahoo Finance shares outstanding ETF
- Shum Hejazi Haryanto Rodier leveraged ETF rebalancing MOC volume 50%
- LRCU NFXL NVDX TSLT AUM Yahoo Finance net assets
- single stock leveraged ETF swap hedge stock continuous market last 30 minutes close
- ETF AUM historical free dataset SEC N-PORT shares outstanding NAV reconstruct
- Cheng Madhavan leveraged ETF rebalancing demand formula L(L-1)
- TSLR GraniteShares TSLA AUM AMDL MULL net assets 2026
