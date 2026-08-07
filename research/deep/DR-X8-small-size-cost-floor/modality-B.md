## DR-X8 — modality B (primary/venue) findings

### Verdict recommendation
**NOT-VIABLE-STRUCTURAL** for the maker-*rebate* premise (confidence HIGH) — **but the taker cost *floor* is far below the registered model, and that correction is the actionable deliverable** (confidence HIGH). No retail-accessible venue/broker tier lets our size be *paid* to provide liquidity: on Alpaca the retail customer never sees the venue rebate (Alpaca monetizes the flow via PFOF and retains it), and on IBKR Pro Tiered the $0.0035/sh commission exceeds every base add-rebate reachable without multi-million-share/day volume commitments, so a maker fill nets a *cost*, not a credit. However, the registered cost model ($0.005/sh/side ≈ IBKR **Fixed** pricing) is ~2.4× Alpaca's true all-in floor. Re-pricing the M18 NVDA ember on the actual Alpaca floor moves it from −$0.94 to **≈ break-even (−$0.11 to +$0.15/trade)** — i.e. the ember's negative sign is ~85–100% a fee-model artifact, not an economic loss. A *clean* positive flip then depends entirely on shaving the 0.5 bps taker slip via passive fills, which is a fill-quality/adverse-selection question owned by the sibling modality, not a fee question.

**What would flip it:** (a) On the rebate premise — an accessible venue whose *base* displayed add-rebate exceeds ~$0.0035/sh with no volume commitment (none exists in 2026), OR a broker that passes exchange rebates through on a **zero-commission** account (neither Alpaca nor IBKR Lite do this; IBKR Tiered passes rebates but charges $0.0035). (b) On the ember — the sibling's fill study showing resting limits capture ≥ ~0.3–0.4 bps of the spread at realistic fill rates in NVDA-class names; that alone (on Alpaca's ~$0 explicit fee) pushes net decisively positive.

### Mechanism
There is no price-insensitive payer for the M18 ember itself — the WAVE4 plan already rules that the ember is *motivation*, not evidence (M18 reversion_system_v1 is dead). The mechanism question DR-X8 actually answers is **who captures the maker rebate**, and the answer is structural: (1) Exchanges (Nasdaq/Arca/BX/EDGX) pay an *add* rebate and charge a *remove* fee to the **member broker**, not to the end customer. (2) A **zero-commission** retail broker (Alpaca) funds "free" trading by selling marketable flow to wholesalers (Virtu/Citadel/Jane Street) for PFOF and by keeping any venue rebate on resting flow — the retail customer is deliberately insulated from the maker/taker fee layer and therefore cannot harvest it. (3) A **pass-through** broker (IBKR Pro Tiered) hands the customer the raw exchange economics *but* charges $0.0035/sh, which is set above every base add-rebate; the rebate ladder that would exceed $0.0035 (Nasdaq/Arca top adding tiers ~$0.0031–$0.0034) is gated on 0.20–0.70% of consolidated ADV (tens of millions of shares/day) — categorically unreachable at $1k–$10k. The persistence of this wedge is intentional broker economics: the rebate is the broker's margin, not the retail maker's. Capacity is irrelevant because there is no edge here — only a cost floor.

### Claims
**C1 [CONFIRMED]** (T1, Alpaca Support "Regulatory Fees" + Fee Schedule, accessed 2026-07-20; live broker): On Alpaca's zero-commission equities (through 2026-12-31), the customer's **entire** all-in cost is regulatory pass-throughs — **SEC Section 31 fee (sells only), FINRA TAF (sells only), and CAT (both sides)** — with "Alpaca Securities LLC does not benefit financially from these charges." Alpaca does **not** pass exchange maker/taker fees to the customer; it absorbs them. Net: buy-side ≈ $0; sell-side = SEC + TAF + CAT.

**C2 [CONFIRMED]** (T1, SEC Fee Rate Advisory FY2026 #2026-2 / NYSE IM-26-01 dated 2026-03-02, read in full): Section 31 fee = **$0.00/million through Apr 3 2026, then $20.60/million on/after Apr 4 2026** = **0.206 bps of sell notional**, sells only. Currently (2026-07-20) in force at $20.60/M. At a $187 megacap this is **$0.00385/sh on the sell** — the dominant component of Alpaca's floor and price-scaling.

**C3 [CONFIRMED]** (T1, FINRA Information Notice 2026-03-17; FINRA TAF FAQ; eff. 2026-01-01): FINRA **TAF = $0.000195/share** on covered-equity **sells only** (raised from $0.000166 on 2026-01-01), per-trade **cap $9.79**. At 141 sh = $0.0275 → rounds up to **$0.03/trade**. Trivial vs the SEC fee.

**C4 [CONFIRMED]** (T1/T3, Alpaca PFOF disclosure + "Inside PFOF" page, read; SEC Rule 606): Alpaca receives **PFOF from Virtu Americas, Citadel Execution Services, and Jane Street**; "customers are not charged." The only rebate *sharing* Alpaca discloses is **50% to its clearing/correspondent (Broker-API) customers**, i.e. B2B partners — **not** the retail end-trader. Conclusion: **a resting limit on Alpaca earns the customer no venue rebate**; going maker changes only the market-slip term, never the explicit fee.

**C5 [CONFIRMED]** (T1, IBKR "Commissions – Stocks" pricing, accessed 2026-07-20): IBKR **Pro Tiered = $0.0035/sh** (lowest tier ≤300k sh/mo), **min $0.35/order, max 1% of trade value**, *plus* pass-through exchange/reg/clearing fees and **full maker-rebate pass-through** ("the full rebate will be passed through to Tiered-commission customers"). IBKR **Pro Fixed = $0.005/sh** (min $1) — **this equals the registered cost model's $0.005/sh/side**, i.e. the registered model is IBKR's most expensive mainstream retail tier. **IBKR Lite = $0 commission** but routes marketable flow for PFOF and does **not** pass venue rebates to the client. IBKR also states Tiered pass-through "may be greater than the costs IBKR pays" and that volume-tier rebate *enhancements* are not passed on.

**C6 [CONFIRMED]** (T1, NYSE Arca Fees & Charges eff. 2026-07-01, read in full; Nasdaq Equity Price List, 2026 update per Equity Trader Alert 2026-19 eff. 2026-04-01): For our **Nasdaq-listed megacaps (Tape C)**, the **base/standard displayed add-rebate is $0.0020/sh (Arca) / ~$0.0013/sh (Nasdaq)** and the standard **remove fee is $0.0030/sh**; closing-auction (MOC/LOC) fee = **$0.0012/sh (Arca) / ~$0.0011–0.0016/sh (Nasdaq)**. Every base add-rebate is **below** IBKR's $0.0035/sh commission; the rebates that beat it (Arca Tape-C Adding Tier 1 $0.0034, Nasdaq top tiers ~$0.0031) require **0.20–0.70% of consolidated ADV** — tens of millions of shares/day — so are unreachable at retail. Net IBKR Tiered maker fill = **−$0.0015 to −$0.0022/sh (a cost)**.

**C7 [CONFIRMED]** (T1, CAT NMS Plan / FINRA Rule 6897; NYSE-Arca schedule §CAT read in full): **CAT Fee 2026-1 = $0.000001/executed share** (invoiced from June 2026), plus residual Historical CAT Assessment 1 ($0.000013) and 1A ($0.000002) → **≈ $0.000016/sh total, both buy and sell**. At 141 sh ≈ $0.0023/side — negligible; both Alpaca and IBKR pass it through.

**C8 [CONFIRMED]** (T1 primary SR-FINRA-2025-017 / SEC Release 34-105226 approved 2026-04-14, eff. 2026-06-04; corroborated by Schwab/NerdWallet/Yahoo, T3): The **Pattern Day Trader regime (FINRA Rule 4210) is eliminated** — the $25,000 minimum-equity requirement, the "pattern day trader" definition, and day-trading buying power are removed, **effective June 4, 2026** (broker implementation deadline Oct 20, 2027), replaced by an intraday-margin framework tying required equity to actual intraday market exposure. Independently, **cash accounts were never subject to PDT**. Either way, PDT does **not** bind our small-account lens.

**C9 [CONFIRMED]** (T1, Reg T / FINRA cash-account rules; T+1 settlement since 2024-05-28): A **$1,000 account is functionally a cash account** (Reg T requires ≥$2,000 for any margin loan). The operative small-size constraint that *replaces* PDT is **T+1 settlement recycling + free-riding/Good-Faith-Violation rules**: you may buy-and-sell the same name intraday with **settled** cash, and T+1 lets a single tranche recycle to ~**one round-trip per trading day**; but a **second same-day buy funded by that day's unsettled sale proceeds is a Good-Faith Violation** (repeat GFVs → 90-day settled-cash-only lockout). So a 1-trade/day sleeve (e.g. the champion's single close-window trade) is unconstrained; an M18-style **multi-round-trip-per-day** sleeve **binds** at $1k unless capital is split into per-day tranches.

**C10 [CONFIRMED]** (T1, IRC §1091 / §475(f); IRS Topic 429): At thousands of same-name trades/year the **wash-sale rule applies pervasively** (disallowed losses roll into replacement-share basis; broker reports within-account via **1099-B Box 1g**) — a bookkeeping burden and a year-end-boundary loss-deferral risk, *not* a permanent loss. The standard neutralizer is the **§475(f) mark-to-market election** (requires Trader Tax Status; must be filed by the **prior-year return due date, ~Apr 15**), which **exempts the trader from §1091 entirely** and converts gains/losses to ordinary MTM. This removes the wash-sale problem for a high-frequency same-name program; it is a tax-structure decision, not a trading constraint.

### Constraint gates
| Gate | Verdict | Clause |
|---|---|---|
| 1 Latency | N-A | Cost-model charge, not a latency-bearing edge; the fee floor is latency-invariant. |
| 2 Access | **PASS** | Everything priced is executable at $1k–$10k on Alpaca (live) and IBKR (available); order types (limit/MOC/LOC) are standard. |
| 3 Session | N-A | Floor applies to any session; closing-auction (MOC/LOC) fees documented at T1 for the champion's structure. |
| 4 Data | **PASS** | All schedules/rates are public T1 at $0; no data purchase to establish the cost model. |
| 5 Fill realism | **FAIL (for the maker premise)** | The maker-first idea hinges on ambiguous continuous-market fills; the *fee* finding is clean, but net profitability of resting fills is a fill/adverse-selection question owned by the sibling. |
| 6 Statistics | N-A | No new event study proposed here; deliverable is a deterministic fee table. |
| 7 Protocol | **PASS** | The corrected cost model is fully stateable and pre-registrable as the a-priori fee input for future M19+ registrations. |

**Survivor-profile score (of the "maker-first fee-boundary intraday" premise): 1/5** — (1) single-print/auction execution: **0** (M18 is continuous-market; only the champion's close is single-print); (2) scheduled decision instant: **0** (intraday reversion is not scheduled); (3) named price-insensitive payer: **0** (the ember has no payer — it is residual); (4) testable on owned/≤$100 data: **1** (fee schedules are free/public); (5) effect ≥ 2× cost burden: **0** (best case is break-even). The cost-model *deliverable* is valuable; the maker-first *edge* premise is not.

### Economics sketch

**Per-share / per-side all-in cost table — our clips (Tape C = Nasdaq-listed megacaps: NVDA/AMD/TSLA/MU/GOOGL).**
Rebates shown as (credit); costs positive. Schedule vintages: SEC §31 eff **2026-04-04**; FINRA TAF eff **2026-01-01**; NYSE Arca eff **2026-07-01**; Nasdaq per ETA-2026-19 eff **2026-04-01**; CAT 2026-1 from **2026-06**. SEC fee shown at a $187 reference megacap (scales at 0.206 bps of notional).

| Component (per share) | **Alpaca** (live, $0 commission) | **IBKR Pro Tiered** ($0.0035/sh) | Notes |
|---|---|---|---|
| Commission — buy | $0.00000 | $0.00350 | IBKR min **$0.35/order** bites at ≤100 sh (→ effective $0.0058/sh at 60 sh) |
| Commission — sell | $0.00000 | $0.00350 | IBKR Fixed alt = $0.005/sh = the registered proxy |
| Exchange add-rebate (maker, Tape C) | **not passed** (Alpaca keeps it) | (**$0.0020**) Arca / (**$0.0013**) Nasdaq | rebate < commission → no net credit possible |
| Exchange remove-fee (taker, Tape C) | **not passed** | $0.00300 | pass-through, IBKR only |
| Closing-auction fee (MOC/LOC) | **not passed** | $0.00120 Arca / ~$0.0011–0.0016 Nasdaq | pass-through, IBKR only |
| SEC §31 (sell only) | $0.00385 | $0.00385 | 0.206 bps × price; both brokers pass |
| FINRA TAF (sell only) | $0.000195 | $0.000195 | cap $9.79/trade; both pass |
| CAT (both sides) | ~$0.000016 | ~$0.000016 | negligible; both pass |

**Round-trip totals at the M18 clip (141 sh NVDA, taker entry + close exit):**
- **Alpaca:** buy ≈ $0.00002/sh + sell ≈ $0.00406/sh ⇒ **≈ $0.0041/sh ⇒ $0.58/round-trip** (SEC fee dominates; scales with price).
- **IBKR Pro Tiered, maker/maker (best case, Arca base):** ≈ **−$0.0071/sh ⇒ $1.00/round-trip cost** (commission swamps the $0.0020 rebate) — *worse* than Alpaca and nowhere near a net credit.
- **IBKR Pro Tiered, taker/taker:** ≈ **$1.87/round-trip** — much worse.
- **Registered model ($0.005/sh/side):** $0.01/sh ⇒ **$1.41/round-trip** — i.e. ~2.4× Alpaca's true floor; overstatement ≈ **$0.83/round-trip**, almost entirely on the buy leg (registered charges $0.005 buy; Alpaca ≈ $0).

**Where the M18 NVDA ember lands (gross +$1.79/trade round-trip at 141 sh):**
- Registered fees: net **−$0.94** (given).
- **Re-priced on Alpaca's true fee floor, keeping the full 0.5 bps taker slip:** net ≈ −0.94 + 0.83 = **−$0.11** (slip one-sided, ~$26k notional) to **+$0.15** (slip two-sided, ~$13k notional) ⇒ **essentially break-even.** The negative sign in the registered result is ~85–100% a **fee-model artifact** (the IBKR-Fixed-equivalent $0.005/sh proxy applied to a $0-commission broker), not an economic loss.
- **At which accessible tier does it flip clearly positive?** **None on the fee axis alone.** No accessible tier yields a *net maker rebate* (Alpaca retains it; IBKR's commission exceeds every base rebate). The Alpaca zero-commission taker floor gets to break-even; the residual is the **0.5 bps taker slip — a market-microstructure cost, not a fee** — removable only by resting maker fills (Alpaca charges ~$0 explicit either way). Whether that clears the ember positive is governed by realized fill rate / adverse selection (engineV5's +2.21 bps passive-vs-cross fact is the optimistic ceiling on that slip recapture; the sibling's fill-realism prior is the arbiter). **Champion comparison: this ember at break-even is ~0 bps/event vs the champion's +2.5 bps dev / +12.5 holdout — it is not a competitor even fully fee-corrected.**

**Settlement / PDT verdict for the $1k small-account lens:** **PDT does not bind** — it was eliminated 2026-06-04 (SR-FINRA-2025-017) and never applied to cash accounts anyway. The **binding replacement constraint is cash-account T+1 settlement recycling + free-riding/GFV**: **one round-trip per day per settled-cash tranche is safe** (covers the champion's single close-window trade); **multiple intraday round-trips/day at $1k trigger Good-Faith Violations** unless capital is pre-split into independent per-day tranches. Wash-sale bookkeeping at thousands of trades/year is real but **neutralized by a §475(f) MTM election** (Trader Tax Status; file by ~Apr 15 of the election year).

### Proposed next test (cost-model specification — the charge's actual deliverable)
Not an edge test; this is the **fee input every future M19+ intraday registration must adopt**, replacing the $0.005/sh/side proxy:
- **Live-broker (Alpaca) taker cost model:** per side = **$0 commission** + (sell only) **SEC §31 0.206 bps × notional** + (sell only) **TAF $0.000195/sh** + **CAT $0.000016/sh** both sides. Round-trip ≈ **0.206 bps of one-side notional + ~$0.03 fixed** (≈ $0.30–$0.60 at $13–26k clips) — *plus* the separately-modeled market slip (0.5 bps taker on marketable legs; **0** on MOC/LOC single-print exits).
- **Maker legs:** model explicit fee = **$0** on Alpaca (no rebate, no commission); do **not** credit any maker rebate for the live broker. Model the *slip* as a fill-conditional spread capture handed to the sibling's realized-fill prior — never as a guaranteed rebate.
- **Do not use IBKR Tiered/Fixed numbers for the live cost model** — they are strictly worse at our size; keep IBKR only as the "if we ever needed rebate pass-through" reference, which this charge shows is a dead end at retail scale.
- **a-priori promotion rule for any fee-boundary stream:** require gross ≥ **2×** the Alpaca-floor round-trip cost *before* crediting any slip recapture (per §1 profile point 5), and require the sibling's fill prior to certify the slip assumption. **Kill criterion:** if a stream is positive only under a net-maker-rebate assumption, kill it — that assumption is falsified for our size by C4/C6. Charges the intraday-cost-model family (shared input; not a new trial family).

### Sources
1. **[T1]** SEC Fee Rate Advisory FY2026 (#2026-2) & Order 34-104909, 2026-02-27; **$20.60/M** eff 2026-04-04 ($0.00 before). https://www.sec.gov/rules-regulations/fee-rate-advisories/2026-2
2. **[T1, read in full]** NYSE Information Memo **IM-26-01**, 2026-03-02 — confirms §31 = $0.00/M through Apr 3 2026, **$20.60/M** on/after Apr 4 2026. https://www.nyse.com/publicdocs/nyse/markets/nyse/rule-interpretations/2026/NYSE_Exchanges_-_Regulatory_Transaction_Fee_Adjustment_Effective_April_4_2026.pdf
3. **[T1]** FINRA Information Notice 2026-03-17 & TAF FAQ — **TAF $0.000195/sh** sells, cap $9.79, eff 2026-01-01. https://www.finra.org/rules-guidance/guidance/faqs/trading-activity-fee
4. **[T1]** Alpaca Support — "What are the regulatory fees?" (SEC/TAF sells-only, CAT both sides, pure pass-through). https://alpaca.markets/support/regulatory-fees
5. **[T1/T3]** Alpaca PFOF disclosure & "Inside PFOF" (Virtu/Citadel/Jane Street; customer not charged; 50% rebate share to clearing correspondents only). https://alpaca.markets/learn/love-it-or-hate-it-inside-payment-for-order-flow-and-commission-free-trading-apps
6. **[T1, read in full, 29 pp]** NYSE Arca Equities Fees & Charges, **eff 2026-07-01** — Tape A/C add ($0.0020), Tape B ($0.0016), remove $0.0030, closing $0.0012; retail-add ($0.0032); adding tiers gated on % CADV; CAT 2026-1 $0.000001/sh + historical assessments. https://www.nyse.com/publicdocs/nyse/markets/nyse-arca/NYSE_Arca_Marketplace_Fees.pdf
7. **[T1]** Nasdaq Equity Price List (Trading) + Equity Trader Alert **2026-19** (pricing update eff 2026-04-01) — Tape C base add ~$0.0013, remove $0.0030, MOC/LOC tiers ~$0.0008–$0.0016. https://nasdaqtrader.com/Trader.aspx?id=PriceListTrading2
8. **[T1]** Interactive Brokers — Commissions, Stocks (Pro Tiered $0.0035/sh, min $0.35, max 1%, rebate pass-through; Pro Fixed $0.005/sh; Lite $0 no pass-through). https://www.interactivebrokers.com/en/pricing/commissions-stocks.php
9. **[T1]** CAT NMS Plan / FINRA Rule 6897 — CAT Fee 2026-1 = $0.000001/executed share. https://www.finra.org/rules-guidance/rulebooks/finra-rules/6897-0
10. **[T1 primary, T3 corroborated]** SR-FINRA-2025-017 / SEC Release **34-105226** approved 2026-04-14, PDT eliminated eff 2026-06-04 (impl. deadline 2027-10-20). https://www.sec.gov/files/rules/sro/finra/2026/34-105226.pdf ; Schwab summary https://www.schwab.com/learn/story/sec-approves-scrapping-25000-day-trader-minimum
11. **[T1]** IRS Topic 429 (Traders in Securities) & §475(f) MTM election — wash-sale (§1091) exemption for MTM traders; election due ~Apr 15 of election year. https://www.irs.gov/taxtopics/tc429

#### Queries used
- `SEC Section 31 fee rate fiscal year 2026 fee rate advisory`
- `FINRA Trading Activity Fee TAF rate 2026 equity per share sell`
- `Nasdaq equity trading price list 2026 add liquidity rebate remove liquidity fee per share`
- `Interactive Brokers IBKR Pro tiered commission US stocks exchange rebate pass through maker`
- `Alpaca Rule 606 order routing disclosure payment for order flow does Alpaca keep rebates`
- `FINRA CAT fee 2026 rate per share equity executing broker consolidated audit trail`
- `pattern day trader rule $25000 cash account exempt settlement T+1 free riding good faith violation small account`
- `IBKR Pro tiered US stock commission $0.0035 per share minimum $0.35 maximum 1% IBKR Lite fixed zero`
- `SEC approves eliminating pattern day trader $25,000 rule 2026 FINRA rule filing effective date`
- `Nasdaq closing cross MOC LOC order fee per share 2026 price list market on close`
- `wash sale rule active day trader thousands trades 1099-B same security 30 days disallowed loss year end`
- `section 475(f) mark-to-market election trader tax status exempt wash sale rule deadline April 15`
