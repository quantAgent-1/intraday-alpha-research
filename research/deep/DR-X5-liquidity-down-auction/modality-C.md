## DR-X5 — C practitioner findings
### Verdict recommendation
**OPEN-TESTABLE** (confidence **MED**) — Practitioner/vendor and TM/index-desk commentary is coherent: closing-auction |price − mid| scales up sharply as liquidity falls (canonical B&M size-quintile 20.6 bps small vs 2.66 bps large, sample 2010–2018), passive/index MOC is the named price-insensitive payer, and transition managers treat small-cap/illiquid closes as a *pain point* (their impact cost and participation caps are our dislocation prior). SSGA (2026) and BMLL (2025 Russell day) reaffirm that less-liquid names and index events convert the auction from price-revealing to price-forming. The tradeable frontier for a ~20-name liquidity-down NOII probe is **liquid mid/small** (ADV ~$20–200M, not microcap), where absolute |dev| is elevated but auction still clears and half-spread does not fully consume the gap. Capacity at $1k–$10k is irrelevant (<<1% of even thin-name auction size).
What would flip it: 2020–2026 measurement on Nasdaq mid/small names showing that net-of-entry-spread |basis| capture ≤0 after honest half-spread + LOC fill rates, or that NOII near/far is unusable (near=0 past 15:55) on the pilot ADV band so the champion structure does not transfer.

### Mechanism
**Who pays:** Index funds, ETFs, and other NAV-/close-benchmarked passive flow forced to print MOC/LOC (or D-Orders on NYSE) to minimize tracking error. Transition managers and active managers co-locate at the same print when matching pooled-fund NAV pricing or shedding overnight risk. Option market-makers contribute on expiration days (delta-hedge unwind into the close). These payers are price-insensitive at the decision horizon: the mandate is the official close, not a discretionary limit.

**Why price-insensitive:** NAV is struck off the official closing auction print. Tracking-error and IS/T-Charter optics push passive and TM desks to accept auction impact rather than continuous-book risk. Practitioners (SSGA, Macquarie TM, Goldman TM, State Street) treat MOC as structural, not optional, for the indexed sleeve.

**Why it persists:** Passive AUM share and close-volume share keep rising (US close ~13–15% ADV Dec-2025 per Instinet/SSGA; typical day ~$50B / ~9% ADV per BMLL 2024). Exchange monopoly on the primary close + auction fees + execution uncertainty raise the cost of outside liquidity provision (B&M imperfect-LP argument), so residual dislocations remain — larger in small names where continuous depth is thin and tick binding is common.

**Capacity intuition (their pain = our prior):**
- TMs/index desks: MOC is “cheap” only when order ≲ **2% ADV** (MJ Hudson/Webster caution) or ≲ **~10% of closing-auction volume** (State Street Woodward rule of thumb). Above that they expect influence and next-day reversion. Illiquid-skewed baskets get **little or no value** once participation is capped to historical close volume (Macquarie McGee).
- Small-cap transitions: prolong the trading window; hard names are cash-substituted or ETF-proxied (CAPIS). Russell adds can require **many days of ADV** of accumulation by LPs (Nasdaq recon note).
- At our $10k notional on a $20–50M ADV name, participation is **~0.02–0.05% ADV** — noise vs their impact thresholds. We are not competing for capacity; we are harvesting residual basis that their MOC pressure leaves relative to continuous mid.

**Who provides on the small-cap close (MM/prop):**
- **NYSE:** DMMs have positive auction obligations and can delay/seek imbalance-offsetting liquidity; in S&P 600 smallcaps they still only post ≥1,000 sh within 2% of inside **22% of the day** and sit within 10 bps of NBBO **63% of the day** (NYSE DMM paper 2021) — i.e., continuous presence is incomplete, so auction absorption is the residual safety valve.
- **Nasdaq:** No DMM; electronic MM/prop and imbalance-only (IO) interest. SLPs are concentrated in names with **>1M shares ADV** (NYSE equities page on SLP eligibility pattern — analogous thin coverage in smallcaps). External LPs face high auction fees + fill uncertainty → imperfect competition → larger |dev| (B&M).
- **Prop/HFT:** Provide continuous late-day liquidity and some IO offset, but step back under inventory stress; auction remains the venue that *must* clear price-insensitive MOC. On Russell day, BMLL documents one-sided imbalance spikes and elevated mid→close dislocation with stable next-open (price pressure, not permanent information).

### Claims
C1 [CONFIRMED] (T2, Bogousslavsky–Muravyev June 2021 / JFM 2023, sample NYSE+Nasdaq common stocks Jan 2010–Dec 2018, price>$5, mcap>$100M): Absolute auction−4pm-mid deviation averages **8.12 bps**, ranging **20.6 bps (small quintile) → 2.66 bps (large quintile)**; average half-spread 7.56 bps so most of the deviation *is* the half-spread, with residual price-impact ~0.55 bps full-sample (large: half-spread 1.47 / impact 1.19). Deviations reverse ~85% overnight (price pressure). — https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf

C2 [CONFIRMED] (T3-asset-manager, SSGA/Instinet, 2026-01-23, Instinet volume through Dec 2025): US close share of daily volume rose to **~13–15%** (Dec 2025 / Q4’25); passive/index NAV mechanics drive MOC concentration. Explicit practitioner caveat: concentration can shift the auction from price-revealing to **price-forming “particularly in less-liquid names or during index events”**; less-liquid stocks need “more hands-on” execution. — https://www.ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure (CONFLICTED: AM marketing)

C3 [CONFIRMED] (T3-vendor, BMLL/Traders Magazine 2025-06-24, 2024 Russell recon + May 2025 venue sample): Typical day ~**$50B** close notional (~9% ADV); rebalance/opex days ~20% ADV. On 2024 Russell day NYSE+Nasdaq final-moments notional $275B+$103B; **>34%** of daily notional in the closing auction; auction dislocation (mid→close) and one-sided notional imbalance spike across Russell adds, with **stable** next-open (consistent with temporary pressure). Nasdaq indicative↔mid converges hard **15:57–15:58**. — https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution (CONFLICTED: data vendor)

C4 [CONFIRMED] (T3-TM, Russell Investments 2025-03-11): MOC is a valid *strategy* (not an IS benchmark) when (a) matching pooled-fund NAV priced at close, or (b) liquid sleeve **≲2% ADV** so price impact is negligible and risk comes off the table. TM industry moved *away* from pure-MOC because it muddies IS; re-adopts selectively when liquidity is deep. — https://russellinvestments.com/uk/blog/the-case-for-moc

C5 [CONFIRMED] (T3-TM, FOW Transition Management Guide 2022-03-15, named desks: Macquarie, Goldman, BlackRock, State Street, Northern Trust, Citi, MJ Hudson): Practitioner consensus on close participation: State Street Woodward ≈ **10% of closing volume** is “definitely not having an impact”; above 15–20% “likely to influence.” MJ Hudson Webster more cautious: hesitant beyond **2% of ADV**. Macquarie McGee: transitions “heavily skewed to illiquid names… a close strategy could add little to no value once you cap your participation based on average closing auction volume.” Northern Trust Blackbourn: too much into the close → next-day reversion. — https://www.fow.com/insights/3698167-trading-the-close-too-good-to-pass-up

C6 [CONFIRMED] (T3-TM, CAPIS undated/current, Bryan Gibbs SVP TM): Domestic equity small-caps “typically introduce the potential for illiquid items that can prolong the trading timeline”; remedies = outgoing manager pre-trim, cash substitute, or ETF proxy — i.e., TMs systematically *avoid* forcing full MOC in the thin tail. — https://capis.com/transition-management-different-asset-classes-different-approaches/

C7 [CONFIRMED] (T3-exchange research, NYSE Choey Li 2023-08-22, 2023 YTD imbalance data): Closing-auction orders as large as **~2.5% CADV** in Russell 1000 names move reference price only **~0.3× daily average spread** immediately; non-R1000 (“other”) names show *less* immediate move (market digests slower) but higher relative CADV tails in imbalance bins (up to ~5% CADV). Impact rises in the last 3 minutes. (CONFLICTED: exchange promoting auction quality.) — https://www.nyse.com/data-insights/closing-auction-immediate-market-impact-price-drift-and-transaction-cost-of-trading

C8 [CONFIRMED] (T3-exchange, NYSE DMM paper Poser 2021-09): DMMs facilitate open/close and can delay close to seek imbalance-offsetting liquidity. In **S&P 600 Smallcap**, DMMs post ≥1,000 sh within 2% of inside only **22% of the time** and provide liquidity within 10 bps of NBBO **63% of the trading day** — continuous small-cap liquidity is incomplete; the close remains the forced clearing event. — https://www.nyse.com/publicdocs/nyse/NYSE_Paper_on_Market_Making_Sept_2021.pdf

C9 [PLAUSIBLE] (T2, Goyal–Jegadeesh–Wu JFQA 2026, sample 2012–2021): Closing-auction price impact is *lower* than continuous for all but **Nasdaq microcaps**, where auction impact can *exceed* continuous (e.g. 0.5% ADV → ~32 bps auction vs ~16 bps continuous on Nasdaq micro). Annualized anomaly-book costs ex-microcap fall to **9–21 bps** in closing auctions. Implication for pilot: **exclude microcaps**; liquid mid/small is the zone where auction remains the cheaper venue and dislocation is still large. — Cambridge/JFQA abstract and figures cited in search; https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/price-impact-in-closing-auctions-opening-auctions-and-continuous-markets-a-benchmark-for-cost-of-trading-on-anomalies/0F72910A79C5B42CF6E85F55164CE846

C10 [PLAUSIBLE] (T3-vendor/exchange, NYSE Bazinas 2023-10-11 + BMLL 2025): D-Orders now >**46%** of NYSE close volume (Aug 2024); ~2/3 submitted in last ~5 minutes. Nasdaq has no D-Order analogue — MOC to 15:55 / LOC to 15:58 / IO to 16:00 only. For a Nasdaq-primary pilot this is simpler (champion structure maps cleanly); for NYSE smallcaps, late D-Order opacity is a measurement confound. Lower-dollar-notional NYSE names show *less* last-10s volatility than Tape C peers in NYSE’s own cut — venue effects matter for tier priors. — https://www.nyse.com/data-insights-blog/the-shifting-dynamics-of-the-nyse-closing-auction-an-inside-view-4w22nu2top

### Constraint gates
| # | Gate | Result | Clause |
|---|------|--------|--------|
| 1 | Latency | **PASS** | Decision instant remains scheduled (15:55:10 NOII snapshot); 5–25 s manual keying still inside Nasdaq LOC to 15:58 if broker allows. |
| 2 | Access | **PASS with caveats** | Same retail MOC/LOC map as champion (IBKR full; Alpaca CLS hard-stop 15:50; Schwab 15:45). Short locate on smallcaps is the real access stress — flag for pilot. |
| 3 | Session | **PASS** | Exit AT 16:00 cross via MOC/LOC is in-mission. |
| 4 | Data | **PASS** | Databento Nasdaq NOII ~$0.45/name-year → ~$15 for ~20-name multi-year pilot (plan figure). Owned SIP for entry mid/spread. Free PIT membership: S&P 400/600 via iShares IJH/IJR asOfDate CSVs / Wayback; Russell lists harder (paid or scrape). |
| 5 | Fill realism | **PASS (exit) / stress (entry)** | Exit = single auction print. Entry = continuous taker at 15:55:10 — half-spread is the binding cost and *scales with tier*; must measure E/Q on the pilot band (feeds DR-X3). Do not trust paper MOC. |
| 6 | Statistics | **PASS** | 20 names × ~250 sessions/year × multi-year NOII → n ≫ 250 easily; power vs ~20 bps event noise still requires mean ≳5–8 bps for Stage A. |
| 7 | Protocol | **PASS** | Named payer = index/ETF MOC + residual continuous LP; a-priori |basis| and ADV-tier thresholds; charges new family **DR-X5 liquidity-down auction** (extension of champion, not a killed family). |

Survivor-profile score: **5/5**
1. Single-print/auction execution — **1** (same structure as champion).
2. Scheduled decision instant — **1**.
3. Named price-insensitive payer — **1** (index/ETF MOC; TM pain confirms).
4. Historically testable owned/≤$100 — **1** (~$15 NOII for 20 names).
5. Expected effect ≥2× cost at our size — **1** (conditional): absolute |dev| rises faster than megacap, and capacity cost ≈0 at $10k; **net** still requires spread not to eat the whole gap (the registration question).

### Economics sketch
**Expected gross (cited, absolute |auction−mid| priors by size — B&M 2010–18, NO-COST-MODEL for strategy PnL):**

| Tier (practitioner proxy) | |dev| prior (bps) | Half-spread prior (bps, order-of-mag) | Cross share of ADV (typical day) | Notes |
|---|---|---|---|---|
| Large / R1000 / megacap | **~2.5–3** (B&M large 2.66; champion measured ~2.5 mean signed when |b|≥10) | ~0.5–2 | ~8–12% | Champion domain; holdout +12.5 on filtered events |
| Mid (S&P 400 / liquid mid) | **~6–12** (interpolate B&M Q2–Q4; SSGA “less-liquid” narrative) | ~3–8 | ~8–12% | Primary pilot target |
| Small (S&P 600 / liquid R2000) | **~15–21** (B&M small 20.6) | ~8–20+ | ~8–15%; recon days 30%+ | Elevated |dev|; spread risk high |
| Micro (below ~20th NYSE %-ile) | **>20, unstable** | wide / odd-lot NBBO | thin, skip days | Goyal et al.: auction impact ≥ continuous — **exclude** |

**Dislocation-per-unit-spread:** B&M full-sample |dev| ≈ half-spread + 0.55 bps impact; for large names half-spread ≈ impact. For small names most of the 20.6 bps *is* the wider half-spread. The **tradeable residual** is the portion of |basis| at 15:55 that (a) exceeds entry half-spread and (b) is directionally predicted by NOII near−mid. That residual is UNKNOWN for 2020–2026 mid/small — it is the registered quantity.

**Our cost burden at $10k:**
- Entry: cross half-spread at 15:55 (tier-dependent; stress 0.5×–1.0× quoted).
- Exit MOC/LOC: 0 spread vs official close if true auction fill; residual = LOC miss → overnight (mission violation) or forced continuous exit.
- Self-impact: ≪0.1 bp at 0.02–0.05% ADV (below TM “no impact” thresholds).
- Commissions: $0 through 2026-12-31; post-promo annotation only.
- NOII data: ~$15 one-time for pilot universe-decade.

**Net prior:** If mid-tier residual signed edge after half-spread is **≥ +5 bps/event** on |basis|≥X filter, structure beats cost 2× and is promotion-eligible. If residual collapses to ~0 once half-spread is paid, lane dies on economics not mechanism. Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout**.

### Proposed next test (only if OPEN-TESTABLE)
- **Hypothesis:** On Nasdaq primary mid/small names in an ADV band of **$20–200M**, the 15:55:10 NOII near−mid basis has the same sign as (close − mid_1555) more often than chance, with gross mean residual after half-spread **≥ +5 bps/event** on |basis| ≥ a tier-specific threshold (start: 10 bps mid / 15 bps small), and effect is not concentrated in top-5 sessions or recon/opex days only.
- **Named payer:** Index/ETF MOC and other close-benchmarked flow (same family as champion; size-tier extension).
- **Data needed:** Databento Nasdaq NOII for ~20 pilot names, 2020→2026 (~$15); owned Alpaca SIP for mid/spread/entry. Free membership screen: S&P 400/600 via IJH/IJR holdings snapshots + price floor + primary listing = Nasdaq. $0 beyond NOII if free membership path works.
- **Universe recipe (practitioner-consistent, anti-survivorship):**
  1. Start from point-in-time S&P 400 (mid) + S&P 600 (small) Nasdaq-primary constituents (or Russell 2000 Nasdaq-primary if free list available). Free PIT membership now available beyond iShares snapshots: GitHub `alemicheli/pyndex` reconstructs Russell 1000/2000/3000 back to 1989, and `fja05680/sp500` / `hanshof/sp500_constituents` give dated S&P membership from 1996 — corroborate against IJH/IJR holdings archives to de-survivorship the list.
  2. Screen: 20d ADV ∈ **[$20M, $200M]**; price ≥ **$10** (whole-share friendly at $10k; avoid sub-$5 tick-noise); average daily close-auction volume > 0 on ≥90% of sessions (NOII usable).
  3. Drop: microcaps below band, hard-to-borrow names for short side (flag), recent IPO <6 months, LULD frequent-halt names.
  4. Target **~20 names** balanced mid/small; freeze list for registration (no look-ahead rebalance).
- **Expected n & power:** 20 names × ≥200 sessions/year × 3–5 years → n ≫ 1,000 events pre-filter; after |basis| filter expect n≥250. Need mean ≳5–8 bps vs ~20 bps sd for Stage A power.
- **A-priori thresholds:**
  - Primary: signed residual (close − entry_mid − 0.5×spread_1555) mean ≥ **+5 bps/event** on filtered set; hit-rate ≥55%.
  - Secondary: |dev| and residual scale **monotonically** mid < small within sample (tier prior check).
  - Stability: effect not confined to top-5 sessions or Russell/opex days (report with and without).
- **Promotion rule:** Stage A pass → forward paper only (holdout spent); never re-use sealed champion holdout.
- **Kill criteria:** Net ≤0 after honest half-spread; NOII near zero-rate too high on pilot band to form signals; effect only on recon days (rare-event UNDERPOWERED); short-locate failure rate >30% of short signals.
- **Trial family charged:** **DR-X5 liquidity-down auction** (new; champion extension by liquidity tier).

### Sources
1. [T2] Bogousslavsky & Muravyev — *Who Trades at the Close? Implications for Price Discovery and Liquidity* (June 2021 working paper / J. Financial Markets 2023). Sample 2010–2018. Size-quintile |dev| 20.6→2.66 bps. https://static1.squarespace.com/static/6310c0b9bb63a25599f4418c/t/634ffc92f81e226b2c30654f/1666186387645/who-trades-at-the-close_June2021.pdf
2. [T3 CONFLICTED AM] SSGA (Elise Ryan) — *Closing time: How passive investing is reshaping equity market microstructure* (2026-01-23); Instinet volume to Dec 2025; less-liquid / index-event price-forming caveat. https://www.ssga.com/us/en/institutional/insights/how-passive-investing-reshaping-microstructure
3. [T3 CONFLICTED vendor] BMLL (Laible & Thakur) / Traders Magazine — *Into the Close: Unpacking U.S. Closing Auction Dynamics and the Impact of the Russell Reconstitution* (2025-06-24). https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution
4. [T3 TM] Russell Investments — *The case for MOC as a TM trading strategy* (2025-03-11). Liquid sleeve ≲2% ADV. https://russellinvestments.com/uk/blog/the-case-for-moc
5. [T3 TM multi-desk] FOW / Global Investor — *Trading the close: too good to pass up?* Transition Management Guide 2022 (2022-03-15). Macquarie, GS, BlackRock, State Street, Northern Trust, Citi, MJ Hudson participation rules. https://www.fow.com/insights/3698167-trading-the-close-too-good-to-pass-up
6. [T3 TM] CAPIS (Bryan Gibbs) — *Transition Management: Different Asset Classes, Different Approaches* (current). Small-cap illiquidity prolongs TM timeline. https://capis.com/transition-management-different-asset-classes-different-approaches/
7. [T3 CONFLICTED exchange] NYSE (Choey Li) — *Closing Auction: Immediate market impact, price drift and transaction cost of trading* Part 1 (2023-08-22). R1000 vs non-R1000 impact vs CADV. https://www.nyse.com/data-insights/closing-auction-immediate-market-impact-price-drift-and-transaction-cost-of-trading
8. [T3 CONFLICTED exchange] NYSE (Steven W. Poser) — *Market Makers in Financial Markets… and the NYSE DMM Difference* (2021-09). S&P 600 DMM presence stats. https://www.nyse.com/publicdocs/nyse/NYSE_Paper_on_Market_Making_Sept_2021.pdf
9. [T3 CONFLICTED exchange] NYSE (Stefanos Bazinas) — *The shifting dynamics of the NYSE Closing Auction: An inside view* (2023-10-11). D-Order share/timing; lower-notional volatility. https://www.nyse.com/data-insights-blog/the-shifting-dynamics-of-the-nyse-closing-auction-an-inside-view-4w22nu2top
10. [T2] Goyal, Jegadeesh & Wu — *Price Impact in Closing Auctions, Opening Auctions, and Continuous Markets* (JFQA 2026; sample 2012–2021). Auction cheaper except Nasdaq microcaps. https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/price-impact-in-closing-auctions-opening-auctions-and-continuous-markets-a-benchmark-for-cost-of-trading-on-anomalies/0F72910A79C5B42CF6E85F55164CE846
11. [T3] CME Group — Russell reconstitution / RTY BTIC as escape from small-cap cash MOC pain (2024–2025 notes). https://www.cmegroup.com/openmarkets/equity-index/2025/How-Does-the-Russell-Reconstitution-Impact-Equity-Markets.html
12. [T3] Nasdaq.com — *Russell Recon Is a Big Day for Small-Cap Companies* (2024-06-20): R2000 adds often need multi-day ADV of LP accumulation. https://www.nasdaq.com/articles/russell-recon-big-day-small-cap-companies
13. [Tooling, free PIT membership] GitHub `alemicheli/pyndex` (Russell 1000/2000/3000 reconstruction, 1989+); `fja05680/sp500` & `hanshof/sp500_constituents` (dated S&P membership, 1996+) — de-survivorship the pilot universe against iShares IJH/IJR daily-holdings archives.

#### Queries used
- small-cap closing auction MOC execution pain transition manager index fund
- market maker proprietary trading small cap close auction imbalance liquidity
- Russell reconstitution small cap closing auction impact transition management
- SSGA OR BlackRock OR State Street "closing auction" small cap OR midcap MOC cost
- Bogousslavsky Muravyev closing auction price deviation small cap bps
- transition manager small cap MOC implementation shortfall "closing auction" cost
- Virtu OR Citadel OR Jane Street OR "market maker" "closing auction" small-cap OR "less liquid" OR Russell 2000
- "trading around the close" small cap OR midcap OR "ADV" OR liquidity tier MOC impact
- "small-cap" OR "less liquid" OR "illiquid" "closing auction" OR MOC "implementation shortfall" OR "market impact" OR "price impact" bps OR basis
- NYSE "closing auction" "price discovery" D-Orders small OR Russell OR "less liquid" market impact
- ITG OR FlexTrade OR Liquidnet OR "agency broker" "closing auction" small cap OR "ADV quintile" OR midcap MOC
- "liquidity provision" OR "market maker" OR prop OR HFT "closing auction" OR "closing cross" small-cap OR "Russell 2000" OR "less liquid" inventory
- site:nyse.com closing auction last 5 minutes order impact CADV Russell
- Bogousslavsky Muravyev "20.6" OR "2.66" closing auction deviation small-cap large-cap
