## DR-Q4-6 — A academic findings
### Verdict recommendation
OPEN-TESTABLE (confidence MED) — Academic T2 impact literature implies single-name MOC self-impact and capacity are non-binding at $1k–$10k notional on liquid Nasdaq names (impact scales as √(%ADV); megacap %ADV is ~10⁻⁶–10⁻⁵). Continuous 15:55 taker cost is dominated by half-spread (~few–8 bps cross-section), with auction exit cheaper than continuous for non-microcaps; retail broker MOC/LOC access/cutoffs are outside academic coverage (T1 gap). What would flip it: owned SIP measurement showing 15:55 signal-day adverse selection systematically exceeds half-spread + 0.5 bp by ≥5 bps/event, or a T1 demonstration that retail cannot place MOC/LOC by the exchange freeze.

### Mechanism
Who pays: passive/index/ETF MOC demand and option-delta hedges that must print at the official close (price-insensitive; documented growth of auction share from ~3%→~10% ADV 2010–2021). Liquidity providers and imbalance-offsetters absorb temporary pressure; ~85% of auction price deviations reverse overnight (large stocks fully). Why persists: exchange monopoly on listing-venue close, high auction fees deterring external LP competition, indexing growth. Capacity intuition: square-root impact in %ADV; at retail size impact is <<1 bp even under conservative λ calibrated to 1% ADV ≈ 4–10 bps on large Nasdaq names. Continuous pre-close book is not “thin” in volume terms (volume migrates to last minutes), but spreads/depth still set the taker bill; marketable limit caps walk-the-book. LOC at near can avoid paying the full continuous spread if the cross lands inside the limit, but academic work does not quantify retail LOC fill rates.

### Claims
C1 [CONFIRMED] (T2, JFQA 2026 / SSRN 2022, sample 2012–2021 US NYSE+Nasdaq common stocks): Closing-auction price impact is lower than continuous-market impact for all size buckets except Nasdaq microcaps; square-root model fits better than linear (linear understates small-size impact). For large stocks, closing impact ≈ 3.2 / 7.2 bps (NYSE / Nasdaq) at 0.5% ADV and ≈ 10.1 / 22.7 bps at 5% ADV; continuous ≈ 6.4 / 8.3 bps at 0.5% ADV and 20.2 / 26.3 at 5% ADV (gross impact, no commission model beyond noting auction fees <0.7 bps). — Goyal, Jegadeesh & Wu, JFQA 2026, https://doi.org/10.1017/S0022109026102592

C2 [CONFIRMED] (T2, same paper/sample): Mean square-root closing impact for 1% ADV is 17.7 bps (median 8.4; x-sec SD 34.6); size-split Model A implies 1% ADV impact of 4.5 / 10.2 bps (NYSE / Nasdaq large), 7.4 / 12.5 (small), 18.2 / 44.7 (micro). Impact defined as (P_close − P_pre-OIAnn)/P_pre-OIAnn vs signed OI/ADV. — Goyal et al. 2026

C3 [CONFIRMED] (T2, JFE 2022, sample ~2010–2020): Nasdaq closing-auction impact ~58% larger than NYSE; temporary component ~85% Nasdaq / ~62% NYSE, fully dissipates in 3–5 days; linear-model average impact cited later as ~2.35 bps for 1% ADV (understates vs square-root). NYSE offers more depth. Strategies exploiting impact reversals profitable in sample (gross). — Jegadeesh & Wu, JFE 2022, https://doi.org/10.1016/j.jfineco.2021.12.003

C4 [CONFIRMED] (T2, J. Financial Markets 2023 / working 2020, sample 2010–2018 US common stocks P>$5, mcap>$100m): Closing auction ~7.5% of daily volume in 2018 (from 3.1% in 2010); mean |auction price − 4pm mid| = 8.1 bps (large stocks 2.66 bps, small 20.6); auction matches pre-close bid or ask in 68.5% of cases; avg half-spread 7.6 bps. ~85% of deviation reverses by next open; one-third to one-half within 30 min after-hours when liquid. Price impact lower than continuous on relative basis; primary payers are passive/ETF/indexing and option hedges (uninformed). — Bogousslavsky & Muravyev, https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840

C5 [CONFIRMED] (T2, arXiv q-fin 2023, sample Euronext Paris 34 liquid stocks 2013–2017, N≈35k stock-days): Instantaneous MOC-style impact at clearing is (i) zero for small volumes (often up to large % of auction volume due to discrete-price peak at pa; P(1% of Qa has zero impact) ≈ 46–74% across names), then (ii) linear over a wide range of residual volume, then (iii) super-linear for extreme sizes. Zero impact on both sides simultaneously is the modal state. NO-COST-MODEL for continuous half-spread; Euronext mechanics, not US. — Salek, Challet & Muni Toke, arXiv:2301.05677

C6 [PLAUSIBLE] (T3/T1-vendor, NYSE Research 2023 YTD, Russell 1000 + others): Auction-order imbalance changes up to ~2.4–2.5% CADV in 15:55–15:56 produce immediate reference-price moves of only ~0.3× daily average spread (~0.2–0.39× across minutes); last three minutes (15:57–16:00) thresholds for “large persistent” impact ≈ 0.47% / 0.86% / 1.18% CADV. Later entry → higher immediate impact, lower residual drift to close. Conflicted (venue research). — NYSE Data Insights, Choey Li, 2023-08-22, https://www.nyse.com/data-insights/closing-auction-immediate-market-impact-price-drift-and-transaction-cost-of-trading

C7 [CONFIRMED] (T2, same Goyal et al. 2012–2021): Exchange closing-auction fees $0.00085–$0.0027/share → <0.69 bps at sample avg price $39; negligible vs impact for liquid names. Continuous institutional split-order impact (Frazzini–Israel–Moskowitz 2018 live data) exceeds closing-auction impact for large stocks (e.g. combined Large+Small 1% ADV close ≈ 8.2 bps vs institutional continuous curve higher). — Goyal et al. 2026 citing Frazzini et al. 2018

C8 [PLAUSIBLE] (T2, arXiv 2024 Euronext; supporting US descriptive work): As clearing approaches, order-event rate accelerates and indicative-price volatility falls; liquidity builds around indicative price → reduced impact of late orders. Supports “LOC/near-priced limit into auction” as lower-impact than continuous aggressive take, but fill uncertainty not quantified for US retail. — Salek et al. arXiv:2401.06724; consistent with Challet (indicative vol ↓)

C9 [UNVERIFIED] (academic silence): No T2 study of retail-broker MOC/LOC availability, 15:50 vs 15:55 cutoffs as experienced by IBKR/Schwab/Fidelity/Alpaca clients, or manual 5–25 s latency fill quality at 15:55. Exchange cutoffs (Nasdaq MOC historically 15:50 then 15:55; LOC later; IO until 16:00) appear in T1 exchange docs and are only summarized in academic method sections — not a retail-access result.

C10 [PLAUSIBLE] (T2 synthesis): For a $10k MOC in a $5B ADV name, %ADV ≈ 0.0002%; under Goyal large-Nasdaq λ (~10 bps at 1% ADV, square-root), expected self-impact ≈ 10 × √(0.0002) ≈ 0.14 bps — below fee noise and far below champion edge. Self-impact becomes material (~2–5 bps) only near ~0.05–0.25% ADV ($2.5–12.5M on $5B ADV; lower on thinner names). Single-name capacity for the champion is not the binding constraint until multi-million notional.

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | PASS | Decision instant scheduled (15:55:10); 5–25 s is pre-positionable for continuous entry and for pre-cutoff MOC if access exists. |
| 2 | Access | N-A (academic) | T2 does not establish retail MOC/LOC offering; exchange-level types exist. T1 broker verification required. |
| 3 | Session | PASS | Exit AT 16:00 cross is explicitly in-mission. |
| 4 | Data | PASS | Impact models historically testable on owned NOII + SIP; no new data purchase required for capacity bounds. |
| 5 | Fill realism | PASS | Auction exit = single print; continuous entry should use condition-coded BBO (sim already does). |
| 6 | Statistics | PASS | Capacity/impact claims are population estimates (millions of stock-days); not underpowered. |
| 7 | Protocol | PASS | Payer (indexed MOC) is a priori; size/impact thresholds pre-registrable. |

Survivor-profile score: 5/5 for the champion structure’s cost assumptions under academic bounds (1 auction exit, 2 scheduled decision, 3 named payer, 4 owned data, 5 edge ≫ cost at size). Retail access remains the only open structural check.

### Economics sketch
- Expected gross: champion holdout +12.5 bps/event [6.9, 18.5]; dev +2.5 bps/event (given, not re-derived).
- Academic cost burden at our size:
  - MOC/cross exit self-impact: ~0–0.2 bps (C1–C2, C10) + exchange fee ≤0.7 bps if not waived by broker.
  - Continuous 15:55 entry: ≈ half-spread (Bogousslavsky cross-section mean half-spread 7.6 bps; liquid megacaps much tighter, often 1–3 bps) + any adverse selection beyond mid. Sim uses BBO cross + 0.5 bp slip + 0.3 bp SEC/TAF sell ≈ consistent order of magnitude for liquid names.
  - LOC-at-near alternative: theoretically can convert part of entry from continuous-spread cost into auction participation; academic fill/skip rate UNKNOWN.
- Net prior at $1k–$10k: academic literature does not erase the holdout edge; cost burden for exit is negligible; entry half-spread is the main haircut already in sim. Comparison line: champion = +2.5 bps/event dev / +12.5 holdout.

### Proposed next test (only if OPEN-TESTABLE)
Hypothesis: On champion signal days (|near−mid|≥10 bps at 15:55:10), realized continuous fill cost (effective vs 15:55:10 mid, condition-coded) averages ≤ half-spread + 1 bp, and MOC/cross exit markout vs near is within ±1 bp of zero after fees — so sim cost model is not optimistic by enough to kill net edge.
Named payer: indexed/ETF MOC + option hedges (unchanged).
Data needed: owned Alpaca SIP + Databento NOII (owned); optional one-time broker paper-trade log of MOC fills ($0 if using promo).
Universe: champion 5 names + M11 28-name frozen set.
Expected n & power: forward M10/M11 already targeting n≥250; cost measurement is a side study on same events (noise of cost ~ few bps, mean estimate needs n~100 for ±1 bp SE).
A-priori thresholds: mean entry cost ≤ 5 bps liquid / ≤ 10 bps mid-cap; mean exit self-impact ≤ 1 bp; kill if entry+exit cost ≥ 0.5 × holdout mean (i.e. ≥6 bps) on forward sealed sample.
Promotion rule: cost model locked if within thresholds; capacity flag green below 0.05% ADV.
Kill criteria: systematic adverse selection > half-spread+3 bp on signal side, or retail cannot submit MOC (T1 fail).
Trial family charged: M10 forward-paper / cost-realism annotation (not a new alpha family).

### Sources
1. [T2] Goyal, A., Jegadeesh, N., Wu, Y. (2026). Price Impact in Closing Auctions, Opening Auctions, and Continuous Markets. *Journal of Financial and Quantitative Analysis*. Sample 2012–2021. https://doi.org/10.1017/S0022109026102592 ; SSRN abstract_id=4300417
2. [T2] Jegadeesh, N., Wu, Y. (2022). Closing auctions: Nasdaq versus NYSE. *Journal of Financial Economics* 143(3), 1120–1139. Sample ~2010–2020. https://doi.org/10.1016/j.jfineco.2021.12.003 ; SSRN abstract_id=3732955
3. [T2] Bogousslavsky, V., Muravyev, D. (2023). Who trades at the close? Implications for price discovery and liquidity. *Journal of Financial Markets* 66. Sample 2010–2018. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840 ; AEA 2020 preliminary https://www.aeaweb.org/conference/2021/preliminary/paper/H9T4hef7
4. [T2] Salek, M., Challet, D., Muni Toke, I. (2023). Price impact in equity auctions: zero, then linear. arXiv:2301.05677. Sample Euronext 2013–2017.
5. [T2] Salek, M., Challet, D., Muni Toke, I. (2024). Equity auction dynamics: latent liquidity models with activity acceleration. arXiv:2401.06724. Euronext closing auctions.
6. [T3/conflicted] Li, C. (2023-08-22). Closing Auction: Immediate market impact, price drift and transaction cost of trading. NYSE Data Insights. 2023 YTD. https://www.nyse.com/data-insights/closing-auction-immediate-market-impact-price-drift-and-transaction-cost-of-trading
7. [T3] ITG (2012-11-07). Trading Around the Close. Practitioner note on MOC/LOC mechanics and pre-announcement trading. https://mrtopstep.com/wp-content/uploads/2024/02/ITG-Trading-Around-The-Close-11-7-2012-1-1.pdf
8. [T2] Frazzini, A., Israel, R., Moskowitz, T. (2018). Trading Costs. SSRN abstract_id=3229719. Live institutional costs 1998–2016; continuous-market benchmark used by Goyal et al.
9. [T1 summary in T2] Nasdaq/NYSE closing-cross mechanics (MOC/LOC cutoffs, near/far, IO) as described in Goyal et al. method section and Nasdaq Closing Cross FAQ (referenced therein).

#### Queries used
1. closing auction MOC market on close impact cost SSRN arXiv
2. Nasdaq closing cross imbalance trading costs capacity academic paper
3. site:ssrn.com closing auction MOC order impact equity
4. site:arxiv.org closing auction market on close price impact
5. "closing auction" "price impact" retail OR institutional MOC basis trade
6. Goyal Jegadeesh Wu price impact closing auctions square root ADV bps
7. "Who Trades at the Close" Bogousslavsky Muravyev closing auction cost
8. closing auction temporary price impact permanent reverse bps sample period
9. Jegadeesh Wu 2022 closing auctions Nasdaq versus NYSE price impact
10. end of day continuous market liquidity thinning 15:55 spread impact retail size
11. site:arxiv.org continuous market liquidity last minutes trading day bid-ask spread price impact
12. "closing auction" capacity OR "percent of ADV" OR "%ADV" MOC impact basis trade
13. Frazzini Israel Moskowitz trading costs continuous market impact ADV bps
14. "near price" OR "far price" OR "indicative" closing cross basis continuous entry academic
15. Jegadeesh Wu closing auctions price impact 2.35 bps temporary permanent 2010-2020 sample
