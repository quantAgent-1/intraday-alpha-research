## DR-Q16 — B primary/venue findings

### Verdict recommendation
**OPEN-TESTABLE** (confidence **HIGH** on access/mechanics; **MED** on retail fee pass-through exactness) — Venue rules and broker docs allow simultaneous independent MOC/LOC orders across a single-name basket and a short QQQ (or other ETF) in the same session. No T1 exchange rule bans multi-security close strategies for a retail customer; Reg SHO locate applies to the short leg the same as continuous-market shorts and must be obtained before the short sale is effected (including short MOC). Binding constraints are broker-level: MOC cutoff may be earlier than the primary listing venue (Alpaca CLS rejects after 15:50 ET), margin + short eligibility, and per-symbol locate (QQQ is deep-liquidity and typically ETB). Atomic multi-leg auction fill is **not** offered — legs can partially fail independently (especially LOC).

What would flip it: A named retail broker T1 doc stating MOC short sales are blocked for ETFs/baskets, or that multi-symbol MOC submission is refused / treated as program-trade restricted at retail size; or confirmation that CLS/MOC short is rejected while continuous short is allowed.

### Mechanism
This charge is **mechanics**, not a payer claim. A market-neutral closing basket is a risk-control shell around whatever single-name close edge exists (e.g. auction-basis long names hedged with short QQQ). There is **no separate price-insensitive multi-name payer** created by the hedge itself: QQQ MOC is ordinary auction flow on a highly liquid Nasdaq-listed ETF. The structure persists as infrastructure (exchanges run independent per-symbol closing crosses; brokers route MOC/LOC to the primary listing auction). Capacity at $10k both sides is negligible vs auction size. Overnight hold of open-at-close market-neutral positions is **out-of-mission** unless user amends session rules; in-mission use is (a) open earlier → flat both legs via MOC/LOC at 16:00, or (b) champion-style enter near 15:55 continuous → exit at cross, with the hedge leg also MOC'd.

### Claims
C1 [CONFIRMED] (T1, Nasdaq Opening/Closing Cross FAQ ©2025 / current; sample ongoing): Short selling is explicitly permitted in Nasdaq Opening and Closing Crosses, subject to applicable short-sale rules (Reg SHO locate, marking, Rule 201). — https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf

C2 [CONFIRMED] (T1, Nasdaq Rule 4702 / Cross FAQ; sample ongoing): Nasdaq MOC must be received prior to 15:55 ET; LOC until 15:58 ET (with late-LOC reprice rules); IO until 16:00; free cancel/modify of on-close interest generally until 15:50 ET. Crosses do **not** guarantee MOC fill (liquidity must offset imbalance). — same FAQ; Closing Cross FAQ https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf

C3 [CONFIRMED] (T1, SEC Reg SHO overview, modified 2022-05-31; rule continuous): Rule 203(b)(1) requires broker-dealer locate (borrow, bona-fide arrange-to-borrow, or reasonable grounds security can be borrowed for settlement delivery) **prior to** accepting/effecting a short sale in any equity security; documentation required. Same-day cover does **not** eliminate the locate. Retail customer is not the market-maker exception. — https://www.sec.gov/investor/pubs/regsho.htm ; 17 CFR 242.203

C4 [CONFIRMED] (T1, Alpaca Orders docs, current as of crawl 2026-07): Alpaca supports MOC/LOC via `time_in_force=cls` with market/limit; CLS after 15:50 ET and before 19:00 ET is **rejected** (broker cutoff **tighter** than Nasdaq 15:55 MOC). On-close orders route to primary exchange auction. Short sales supported; buying-power check applies to opening shorts. — https://docs.alpaca.markets/docs/orders-at-alpaca

C5 [CONFIRMED] (T1, Alpaca Margin & Short Selling docs, updated ~2026): Shorting requires ≥$2,000 equity margin account. ETB: 5,000+ securities, $0 locate/borrow fees for Trading API users. HTB: locate required before short order (round lots of 100; non-refundable locate fee; single-use). Daily HTB borrow fee if held any time that day. — https://docs.alpaca.markets/docs/margin-and-short-selling

C6 [CONFIRMED] (T1, IBKR Campus shorting + MOC lessons, current): IBKR allows MOC (Nasdaq stop accepting MOC 15:55; NYSE 15:50 per IBKR Desktop lesson). Short sales require locate inventory (TWS shortable indicator); order to sell short transmits if locates available; otherwise held/alerted. Pre-borrow available. — https://www.interactivebrokers.com/campus/trading-lessons/shorting-stocks-on-ibkrs-trader-workstation-tws/ ; IBKR Desktop Market on Close lesson

C7 [CONFIRMED] (T1, SEC Aug 2015 market structure research note; listing): QQQ primary listing is **Nasdaq** (closing auction = Nasdaq Closing Cross); SPY is NYSE Arca. Multi-leg MOC across Nasdaq single names + QQQ is same-venue family for listing auctions but still **independent per-symbol crosses**, not a linked basket match. — https://www.sec.gov/marketstructure/research/equity_market_volatility.pdf

C8 [CONFIRMED] (T1, Nasdaq Price List Trading, current): Nasdaq Closing Cross MOC/LOC fees **$0.0008–$0.0016 per share executed** by member volume tier (Tier A $0.0008 … Tier F $0.0016; Tier G options-linked $0.0010); Imbalance-only and continuous book in cross $0.0011. Retail customers do not pay Nasdaq schedule directly — fees are absorbed/passed by introducing broker; **UNKNOWN** exact Alpaca/IBKR pass-through of cross code-C fees at retail size. — https://www.nasdaqtrader.com/trader.aspx?id=pricelisttrading2

C9 [CONFIRMED] (T1, SEC Fee Rate Advisory FY2026, 2026-02-27; FINRA TAF schedule): Section 31 fee $20.60 per $1,000,000 of covered sales notional effective 2026-04-04 (was $0.00 mid-FY2025 window). FINRA Trading Activity Fee on covered equity sells ~$0.000166/share (2025) rising to ~$0.000195/share (2026), capped per trade. Applies to **sell** legs (long MOC sell and short MOC open both are sells). — https://www.sec.gov/rules-regulations/fee-rate-advisories/2026-2 ; FINRA fee adjustment schedule

C10 [CONFIRMED] (T1 search coverage, Nasdaq/NYSE rules + FINRA 5320 family): **No** exchange rule found that prohibits a single customer from entering MOC/LOC on multiple securities in one session, or that couples single-name MOC with ETF hedge MOC. FINRA 5320 (trading ahead) is firm-vs-customer proprietary, not a retail multi-symbol ban. Crosses remain per-symbol; no retail “market-neutral basket MOC” product. Rule 201 (10% down short-sale circuit breaker) can impede **short** MOC if restriction active and cross price not above NBB (Nasdaq short-marked auction orders can be rejected under Rule 201 compliance designs). — Nasdaq Equity Rules / SEC Rule 201 FAQ family; negative search result on multi-security close ban

### Constraint gates
| Gate | Result | Clause |
|------|--------|--------|
| 1 Latency | **PASS** | Cutoffs scheduled (15:50–15:55); 5–25 s manual OK if orders pre-keyed before hard stop. |
| 2 Access | **PASS** (with broker nuance) | Alpaca CLS + shorting (margin ≥$2k); IBKR MOC + locate UI; Schwab/Fidelity short + MOC exist at T3/product level. Verify live shortable flag for QQQ and each name. |
| 3 Session | **PASS** if MOC used to **flatten**; **FAIL / needs amendment** if both legs **open** at 16:00 and hold overnight | Flat AT close is in-mission; overnight market-neutral shell is not. |
| 4 Data | **PASS** for mechanics | No new data needed to confirm access. Alpha test of hedged auction edge uses owned NOII/SIP. |
| 5 Fill realism | **PASS** with caveat | Auction single-print preferred; multi-leg is **non-atomic** — LOC miss, MOC imbalance non-fill, or Rule 201 short reject can leave residual beta. |
| 6 Statistics | **N-A** for pure mechanics | Power applies only if promoting a hedged-edge trial (n≥250 events). |
| 7 Protocol | **PASS** for mechanics pre-reg; alpha needs named payer | Mechanics pre-register as access check; any edge trial must name payer before results and charge a trial family. |

Survivor-profile score: **3/5**
1. Single-print/auction execution → **+1** (each leg)
2. Scheduled decision instant → **+1**
3. Named price-insensitive payer → **0** (hedge is not a payer; inherits champion payer only if attached to basis trade)
4. Historically testable cheaply → **+1** (owned SIP/NOII + paper MOC)
5. Expected effect ≥2× cost burden → **0** until alpha hypothesized (mechanics alone have no edge)

### Economics sketch
- **Gross:** not applicable to mechanics-only; any edge is the single-name (or basis) gross minus hedge residual, not a new gross from “being market-neutral.”
- **Cost burden (two-leg close, order-of-magnitude at $10k both sides):**
  - Exchange MOC/LOC (if fully passed): ~$0.0008–$0.0016/sh × shares. At ~$100/sh, ~0.08–0.16 bps **per leg** of that leg’s notional; **two legs ~0.16–0.32 bps** of combined notional if both pay top-of-schedule. Retail may see $0 commission promo absorbing venue fees — **UNKNOWN pass-through**.
  - Section 31 (post 2026-04-04): **$20.60 / $1M** on **sell** notional only. Two sell legs totaling $10k → ~$0.21 (~0.21 bps of $10k one-side).
  - FINRA TAF: ~$0.00017–0.00020/sh on sells, capped — cents at this size.
  - Locate/borrow: **$0** if QQQ and names are ETB and short is opened and covered same day (no overnight HTB hold). HTB locate fees non-refundable if used.
  - Commission: $0 through 2026-12-31 promo (stress post-promo separately).
  - **All-in structural friction sketch:** ~0.3–1.0 bps of one-side notional in a full fee-pass-through world; near-zero under pure $0 commission + ETB if venue fees not broken out. Still well below champion’s +2.5 bps/event dev / +12.5 holdout **if** the hedge does not destroy the single-name auction edge (basis correlation risk is the real cost, not fees).
- Comparison line: **champion = +2.5 bps/event dev / +12.5 holdout**. Two-leg fee stack is **not** the killer; residual beta / non-atomic fill / overnight (if mis-specified) are.

### Proposed next test (only if OPEN-TESTABLE)
**Hypothesis (access, not alpha):** At the production broker (Alpaca primary), a human can submit in one session before 15:50 ET: (i) MOC/LOC on N≥3 Nasdaq single names and (ii) short MOC on QQQ, with locates succeeding for QQQ and any short names, and receive auction prints (or documented rejects) for each leg.

**Named payer:** none for access test; if later alpha-tested as “basis long basket + QQQ short,” payer remains indexed MOC/rebalance flow on the **names**, not on QQQ.

**Data needed:** $0 — paper or live micro-size one session; optional broker fee blotter export.

**Universe:** 5 core NOII names + QQQ; $1k–$10k notional both sides, whole shares.

**Expected n & power:** Access test n=1–5 sessions sufficient (binary can/can’t). Alpha variant would need n≥250 hedged events vs ~20 bps noise — **UNDERPOWERED** unless multi-year.

**A-priori thresholds (access):**
- PASS if ≥90% of intended legs accept pre-cutoff and ≥1 full session both sides print at official close.
- FAIL if short MOC systematically rejected when continuous short works, or multi-symbol CLS refused.

**Promotion rule:** Access PASS → may attach market-neutral shell as **risk annotation** on champion/M11; does **not** alone promote a new trial family.

**Kill criteria:** Broker or clearing policy blocks short MOC; locate fails on QQQ on normal days; residual overnight forced by one-leg reject with no same-session continuous exit path.

**Trial family charged:** none for pure access; if alpha, charge a **new** “auction-hedged / market-neutral close” family (do not smuggle into M10/M11 without registration).

### Sources
1. **[T1]** Nasdaq, *The Nasdaq Opening and Closing Crosses — FAQ* (©2025, doc 1608-25). https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf
2. **[T1]** Nasdaq, *Nasdaq Closing Cross FAQ* (PDF). https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf
3. **[T1]** Nasdaq Trader, *Price List — Trading* (Closing Cross tiers A–G). https://www.nasdaqtrader.com/trader.aspx?id=pricelisttrading2
4. **[T1]** SEC, *Key Points About Regulation SHO* (modified 2022-05-31). https://www.sec.gov/investor/pubs/regsho.htm
5. **[T1]** SEC / eCFR, Regulation SHO Rule 203 (locate). 17 CFR 242.203
6. **[T1]** Alpaca Docs, *Placing Orders* (CLS/MOC/LOC, cutoffs). https://docs.alpaca.markets/docs/orders-at-alpaca
7. **[T1]** Alpaca Docs, *Margin and Short Selling* (ETB/HTB locate workflow). https://docs.alpaca.markets/docs/margin-and-short-selling
8. **[T1]** IBKR Campus, *Shorting Stocks on IBKR’s TWS*; *IBKR Desktop Market on Close Order*. https://www.interactivebrokers.com/campus/trading-lessons/shorting-stocks-on-ibkrs-trader-workstation-tws/
9. **[T1]** SEC, *Research Note: Equity Market Volatility on August 24, 2015* (QQQ Nasdaq primary listing). https://www.sec.gov/marketstructure/research/equity_market_volatility.pdf
10. **[T1]** SEC, *Section 31 Transaction Fee Rate Advisory for Fiscal Year 2026* (2026-02-27; $20.60/mm from 2026-04-04). https://www.sec.gov/rules-regulations/fee-rate-advisories/2026-2
11. **[T1]** FINRA, Trading Activity Fee adjustment schedule (equity per-share TAF). https://www.finra.org/rules-guidance/rule-filings/sr-finra-2024-019/fee-adjustment-schedule
12. **[T1]** NYSE, Opening and Closing Auctions Fact Sheet (NYSE MOC/LOC 15:50 cutoff). https://www.nyse.com/publicdocs/nyse/markets/nyse/NYSE_Opening_and_Closing_Auctions_Fact_Sheet.pdf
13. **[T1]** Federal Register / Nasdaq (SR filings) on short sale marking in closing-cross order types / Rule 201 compliance (e.g. EMOC short handling). https://www.federalregister.gov/documents/2020/07/22/2020-15792/self-regulatory-organizations-the-nasdaq-stock-market-llc-notice-of-filing-of-proposed-rule-change
14. **[T3]** BMLL, *Into the Close* (2025-06-24) — venue cutoff color (Nasdaq 15:55/15:58; NYSE 15:50; Arca ETF imbalance from 15:00). Not used as load-bearing mechanics.

#### Queries used
- Nasdaq MOC LOC order entry cutoff retail broker requirements
- short sale locate requirements FINRA Rule 203 Regulation SHO MOC
- Alpaca short selling locate MOC market on close order types
- Interactive Brokers MOC LOC short stock locate requirements closing auction
- Nasdaq closing cross MOC order fees short sale
- Nasdaq closing cross fee MOC LOC per share price list 2024 2025
- QQQ easy to borrow short ETF retail MOC closing auction
- FINRA Rule 5320 OR multi-security MOC basket hedging regulation exchange
- QQQ primary listing exchange closing auction venue
- Schwab Fidelity short sell MOC market on close order locate ETB
- Regulation SHO short sale circuit breaker MOC closing auction permitted
- NYSE Arca closing auction MOC LOC cutoff fees ETF
- SEC Rule 201 short sale auction MOC exception OR closing cross short sale
- retail SEC fee TAF fee per share equity trade 2025 2026
- Invesco QQQ Nasdaq listed shortable easy to borrow
