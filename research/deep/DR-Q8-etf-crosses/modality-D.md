## DR-Q8 — D adversarial findings
### Verdict recommendation
**NOT-VIABLE-STRUCTURAL (MED–HIGH)** — The champion edge is residual *single-name* near−mid basis left by price-insensitive indexed MOC. Liquid equity ETFs invert that stack: continuous AP/MM secondary arb keeps mid inside a tight iNAV band; primary create/redeem settles end-of-day against the basket; listing-venue auction share is thin (~2% of Arca ETF volume vs ~9% equities); and residual dislocation is the natural prey of prop/AP desks, not a 5–25 s retail taker. Transferring the 15:55:10 basis rule to QQQ/SPY/IWM/SMH therefore does not improve—and structurally dilutes—the edge. Already-known MU holdout concentration is not cured by moving to ETFs; it is replaced by a different failure mode (no residual payer).

What would flip it: A pre-registered QQQ (Nasdaq-listed, owned NOII) kill test showing |near−mid|≥10 bps events still deliver net ≥+5 bps/event at 15:55:10 with n≥250, hit-rate ≥55%, and no single-name-equivalent concentration artifact — *and* that edge surviving after controlling for underlying-basket close dislocation.

### Mechanism
**No coherent retail-capturable payer on the ETF itself.** Who *would* pay on single-names: index/ETF MOC and rebalance flow that must print the close in the constituent, leaving near−mid basis the continuous book has not fully absorbed by 15:55:10. On the ETF share:

1. **Secondary-market MMs** quote two-sided around iNAV/fair-value continuously; mid *is* the arb-tightened estimate of NAV/near.
2. **APs** create/redeem in large units (typ. 25k–50k shares) against the sponsor; creations follow premiums, redemptions follow discounts; activity clusters around end-of-day P/NAV deviations — i.e., APs *are* the basis-collapsers, not the payers.
3. **Venue mechanics (esp. Arca ETFs):** brokers can MOC the underlying basket and package into the ETF at NAV risk-free (BMLL), so any ETF-level auction imbalance is a second-order residual after primary-basket hedges, not a first-order price-insensitive demand shock.
4. **Crowding:** SPY/QQQ/IWM are the most-watched US instruments; imbalance feeds are industry standard; prop competition compresses auction arb rents (general HFT-competition result).

Persistence: the *arb band* persists (create/redeem costs define a no-trade zone), but that band is sub-retail-edge for mega liquid equity ETFs and is harvested by APs when it breaches. Capacity intuition: absolute $ ADV is huge, but *edge* capacity is worse than single-names because (a) more competitors per bp, (b) thinner auction share of ADV, (c) dual-market arb (ETF + basket + futures) tightens faster than single-name continuous books.

### Claims
C1 [CONFIRMED] (T3, 2015/KCG via ICI, sample domestic equity ETFs as of analysis period): ~90% of domestic equity ETF prices trade *inside* the no-arbitrage band (below creation-basket offer / above redemption-basket bid); inside that band, AP create/redeem is money-losing — i.e., secondary mid already tracks fair value within AP costs. — ICI, *The Role and Activities of Authorized Participants of Exchange-Traded Funds*, https://www.ici.org/pubfile_pdf/ppr_15_aps_etfs.pdf

C2 [CONFIRMED] (T2, Engle & Sarkar 2006, sample mid-2000s domestic ETFs incl. SPY/QQQ/IWM era): end-of-day domestic equity ETF premium mean ~1.1 bps, premium SD ~15–18 bps on average (range ~10–34 bps; QQQ SD ~34 bps in sample); intraday premium SD ~12 bps — tight vs any ≥10 bps retail basis threshold. — Engle & Sarkar, *Premiums-Discounts and Exchange Traded Funds*, J. Derivatives 2006, https://www.stern.nyu.edu/rengle/jod.2006.635418.pdf

C3 [CONFIRMED] (T3, BMLL 2025-06-24, sample May 2025 venue panels + 2024 Russell): NYSE Arca (primary US ETF listing/auction venue for many ETPs incl. SPY) puts only ~**2%** of ETF volume in the closing auction vs ~**9%** for NYSE equities; Arca indicative price is more volatile into the close; **brokers can MOC underlyings and package into the ETF guaranteeing NAV risk-free**. — BMLL / Traders Magazine, *Into the Close…*, https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution

C4 [CONFIRMED] (T1/T3, Databento 2025-08-14 + BMLL 2025): Arca imbalance disseminates from **15:00** ET (vs Nasdaq/NYSE from 15:50), every second — earlier public information → more time for prop/AP offset → less residual 15:55:10 basis. Real-time Arca imbalance license starts ~$1,000/mo exchange fees (not owned). — https://databento.com/blog/NYSE-imbalance-feeds ; BMLL same as C3

C5 [CONFIRMED] (T3, SSGA undated/current education; standard industry mech.): APs create on premium / redeem on discount by buying (selling) basket and selling (buying) ETF; this is the designed force that keeps market price ≈ value of underlyings; mature liquid ETFs trade inside an “arbitrage band” set by AP costs. — SSGA, *Master the mechanics of ETF trading*, https://www.ssga.com/us/en/intermediary/insights/master-the-mechanics-of-etf-trading

C6 [PLAUSIBLE] (T2/T3, Gorbatikov–Sikorskaya / Petajisto line, equity ETF panels ~2019–2020): mean daily equity-ETF |mispricing| ~7 bps with large cross-sectional SD; primary-market AP activity rises with |premium| — consistent with residual mispricing being AP inventory/cost band, not free retail alpha. — abstract/summaries: https://portal.northernfinanceassociation.org/viewp.php?n=2240033544 ; microstr.exchange paper

C7 [CONFIRMED] (T1, Nasdaq Trader / BMLL): QQQ is Nasdaq-listed → Closing Cross + NOII (owned data path exists); SPY and most IWM/sector ETPs are Arca-primary → different cutoffs, D-order-free Arca mechanics, earlier imbalance, thinner auction share. Venue heterogeneity is not a free diversifier; it is a data and mechanism split. — Nasdaq open/close FAQ; BMLL C3; Databento C4

C8 [PLAUSIBLE] (T3, Greenwich/Traders Mag 2017 + general HFT-competition lit.): ~70% of surveyed traders say real-time imbalance data influences close trading; liquid names are most crowded; price competition among arbitrageurs reduces rents (Budish/Hasbrouck–line). Mega-ETFs are the *most* crowded auction tape in US equities. — https://www.tradersmagazine.com/departments/buyside/auction-imbalance-data-affects-traders/

C9 [UNVERIFIED as structural kill; nuance] (T3, IBKR/Alpaca retail short docs): SPY/QQQ/IWM are typically **easy-to-borrow** at low annualized fee (SPY ~0.30%/yr cited on IBKR; Alpaca ETB list covers major ETFs; HTB locates now exist on Alpaca as of 2026-06). “Retail cannot short ETFs easily” is **overstated** for mega liquid ETFs on a same-day open-to-cross hold. Real retail frictions: (i) locate/ETB policy variance by broker, (ii) some brokers historically blocked simultaneous long+short in one account, (iii) sector/less-liquid ETFs can be HTB. Both-sides *is* available for QQQ/SPY at our size; this is not the load-bearing kill. — Alpaca short/ETB docs; IBKR short-sale cost page; Reddit/practitioner borrow anecdotes (T4 only for color)

C10 [PLAUSIBLE] (T3, Nadig 2025-04-11, single extreme day abstract-level): rare catastrophic ETF closing misprints (SPY Apr 9 2025 claimed ~90 bps premium / $42M mispricing) exist but are (a) not a systematic edge, (b) contested by issuer NAV reporting, (c) the kind of event APs/prop own, not a 15:55:10 retail schedule. Does **not** rehabilitate a day-to-day ETF basis rule. — https://www.nadig.com/p/spy-mispriced-42-million-nobody-cares (paywall beyond lede; lede only used)

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | PASS | 15:55:10 decision remains scheduled; 5–25 s OK |
| 2 | Access | PASS (QQQ) / FAIL-partial (Arca ETFs) | Alpaca supports short + CLS/MOC-LOC on SPY/QQQ; Arca-primary names need venue-correct routing knowledge |
| 3 | Session | PASS | Exit at 16:00 cross is in-mission |
| 4 | Data | FAIL for SPY/IWM/Arca ETPs; PASS for QQQ only | Owned: Nasdaq NOII. Arca/NYSE Pillar imbalance **not purchased**; RT Arca imbalance ≥~$1k/mo exchange fees (Databento) — exceeds ≤$100 one-time research gate without user approval |
| 5 | Fill realism | PASS | Still single-print auction exit |
| 6 | Statistics | PASS on calendar, FAIL on expected effect | n≥250 easy on liquid ETFs; problem is expected mean → 0 under AP arb, not sample size |
| 7 | Protocol | FAIL | Named *payer* on the ETF share is not pre-statable the way single-name index MOC is; the natural agents (APs/MMs) are basis *collapsers*. Multiple-testing: new family would charge ~1 more trial against ~18 registered |

**Survivor-profile score: 2 / 5**
1. Single-print/auction execution → **+1**
2. Scheduled decision instant → **+1**
3. Named price-insensitive payer → **0** (AP/MM are collapsers; Arca auction share thin; package-underlying-MOC path removes ETF-level payer)
4. Historically testable on owned / ≤$100 data → **0** (QQQ only partial; SPY/IWM blocked on venue data)
5. Expected effect ≥2× cost at our size → **0** (prior mean near 0 after costs; champion was +2.5 dev / +12.5 holdout)

### Economics sketch
- **Expected gross (cited field priors):** domestic equity ETF end-of-day |premium| mean order ~0–7 bps with SD ~15 bps (C2, C6). That is the *full* P−NAV distribution, not a conditioned |near−mid|≥10 bps tradeable subset, and not net of taker entry. Conditioning on |basis|≥10 bps selects the tail of an already-arbed series → adverse selection vs APs likely.
- **Our cost burden:** taker entry (spread/half-spread + impact) on QQQ/SPY is small in absolute bps (sub-penny spreads common) but **not zero**; at $10k notional, 1–3 bps round-trip is material against a collapsed gross. Short borrow on mega ETFs ≈0 on a same-day open-to-cross hold.
- **Net prior:** ≈ 0 to slightly negative after costs under the structural prior; **not** competitive with champion **+2.5 bps/event dev / +12.5 holdout**.
- Capacity at our $1k–$10k is not the binding constraint; **edge existence** is.

### Proposed next test (only if OPEN-TESTABLE)
**N/A under NOT-VIABLE-STRUCTURAL.** Optional *cheap null confirmation only* (does not promote; kill-only, does not charge a promotion family if pre-registered as adversarial falsification):

- **Hypothesis (kill):** QQQ 15:55:10 |near−mid| ≥ 10 bps events do **not** deliver net ≥ +2 bps/event OOS.
- **Payer claimed:** none structural; test is existence check only.
- **Data:** owned Databento Nasdaq NOII + SIP for QQQ (no new $).
- **Universe:** QQQ only (Nasdaq-listed). Do **not** extend to SPY/IWM without Arca Pillar purchase.
- **Expected n:** easy ≥250 over multi-year NOII history.
- **Power:** vs ~20 bps/event noise; detecting champion-class +10 bps needs far fewer events than detecting +2 bps — design for kill of +5 bps mean.
- **A-priori thresholds:** promote-never; kill if CI upper bound < +5 bps net or hit-rate ≤52% at n≥250.
- **Trial family:** adversarial DR-Q8 kill; do not charge a new promotion family unless an independent modality returns OPEN-TESTABLE with a *named* ETF-level payer.

### Sources
1. **[T3]** Investment Company Institute (citing KCG analysis), *The Role and Activities of Authorized Participants of Exchange-Traded Funds*, ~2015. https://www.ici.org/pubfile_pdf/ppr_15_aps_etfs.pdf — 90% domestic equity ETFs inside no-arb band.
2. **[T2]** Engle, R. & Sarkar, D., *Premiums-Discounts and Exchange Traded Funds*, Journal of Derivatives 13(4), 2006. https://www.stern.nyu.edu/rengle/jod.2006.635418.pdf — domestic premium mean ~1.1 bps, SD ~15–18 bps.
3. **[T3]** BMLL (Laible & Thakur), *Into the Close: Unpacking U.S. Closing Auction Dynamics and the Impact of the Russell Reconstitution*, 2025-06-24 (also Traders Magazine). https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution — Arca ETF auction ~2% vol; package-underlying-MOC path; 15:00 Arca imbalance.
4. **[T1/T3]** Databento, *Introducing real-time NYSE imbalance data*, 2025-08-14. https://databento.com/blog/NYSE-imbalance-feeds — ARCX.PILLAR for SPY; fee table; not owned.
5. **[T3]** State Street Global Advisors, *Master the mechanics of ETF trading* (current education page). https://www.ssga.com/us/en/intermediary/insights/master-the-mechanics-of-etf-trading — AP create-on-premium / redeem-on-discount; arbitrage band.
6. **[T3]** Invesco / industry, *Understanding ETF trading and liquidity: Arbitrage, premiums, and discounts*, 2024-07-05. https://www.invesco.com/apac/en/institutional/insights/etf/understanding-etf-trading-and-liquidity-etf-arbitrage-premiums-and-discounts.html — MM/AP keep price ≈ fair value.
7. **[T1]** Nasdaq Trader, Opening and Closing Crosses / NOII schedule. https://www.nasdaqtrader.com/trader.aspx?id=openclose — 15:50–16:00 NOII; QQQ on Nasdaq path.
8. **[T3]** Traders Magazine / Greenwich (Nasdaq partnership), *Auction Imbalance Data Affects Traders*, 2017-02-10. https://www.tradersmagazine.com/departments/buyside/auction-imbalance-data-affects-traders/ — 70% of traders influenced by imbalance data.
9. **[T2 abstract / T3 summary]** Gorbatikov & Sikorskaya line / Petajisto (2017) equity-ETF mispricing ~7 bps mean |premium|; AP activity responds to premium. Various SSRN/NFA summaries 2021–2022.
10. **[T3 lede only]** Dave Nadig, *SPY Mispriced $42 Million. Nobody cares.*, 2025-04-11. https://www.nadig.com/p/spy-mispriced-42-million-nobody-cares — extreme single-day print; not a systematic edge.
11. **[T1/T3]** Alpaca Markets docs: short ETB + CLS/MOC; HTB locates launch 2026-06. https://alpaca.markets/stocks ; https://alpaca.markets/blog/htb-trading-api-locates
12. **[T3]** BIS / ESRB bond-ETF arb anatomy (contrast class): equity baskets ≈ holdings (tight arb) vs bond baskets decoupled — reinforces that *equity* ETFs are the tightly arbed case. https://www.bis.org/publ/qtrpdf/r_qt2103d.pdf

#### Queries used
- ETF creation redemption arbitrage closing auction basis collapse
- ETF NAV premium discount arbitrage speed AP authorized participant closing cross
- QQQ SPY closing auction NOII imbalance trading edge prop firms
- ETF mid price tracks indicative near price closing auction
- retail short ETFs hard to borrow locate MOC LOC both sides basis trade
- IWM QQQ SPY auction dynamics different from single stocks closing cross
- NYSE Arca ETF closing auction imbalance feed QQQ SPY listing venue
- equity ETF premium discount basis points average tight arbitrage efficiency
- closing auction imbalance arbitrage crowded prop HFT competition decay
- creation unit size SPY QQQ IWM 50,000 shares minimum arbitrage capacity
- KCG analysis 90 percent domestic equity ETF prices inside creation redemption band
- Alpaca short sell ETF MOC LOC order availability retail broker
- "closing auction" ETF basis OR "indicative" premium discount arbitrage site:ssrn.com OR site:arxiv.org
- Nasdaq closing cross ETF QQQ auction volume fraction of ADV
- QQQ listing exchange Nasdaq or Arca closing auction share volume percent
- ETF secondary market makers continuous arbitrage keep mid near iNAV closing
- retail short SPY QQQ IWM easy to borrow borrow fee basis points
