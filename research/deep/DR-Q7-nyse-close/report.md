# DR-Q7 — NYSE closing auction: does the champion port?

**Date:** 2026-07-17
**Mode:** Wave-2 deep-dive (OPEN_QUESTIONS #7)
**Agents:** 4 modality + 3 claim-refuters completed (D-Order/rules bundle 1/2 — twin lost to a session limit after its pair confirmed all T1 rules; spec/Hu-Murphy bundle 2/2) + orchestrator E-probe (Databento cost quote)
**Orchestrator synthesis — not delegated**

### Synthesis

| Lane | Verdict rec | Core thrust |
|------|-------------|-------------|
| A | OPEN-TESTABLE (MED) | Same payer family; NYSE has MORE temporary pressure; all samples pre-2024 rules |
| B | OPEN-TESTABLE (MED) | T1 mechanics mapped; ContinuousBookClearingPrice as near-analog; data cheap |
| C | NOT-VIABLE-STRUCTURAL (HIGH) | D-Orders are the institutional edge; retail cannot re-arm after 15:50 |
| D | NOT-VIABLE-STRUCTURAL (HIGH) | Rewrite-until-15:59:50 makes any outsider snapshot adversarially incomplete; (data-cost argument wrong, see below) |

**Dissents & refuter/E-probe resolutions:**
1. **A/B's "testable" and C/D's "structural fail" are both right about different things.** The historical DATA is cheap and the mechanics are mappable (B correct); the deployable STRATEGY fails gates no data can fix (C/D correct). The verdict below scores the deployable port, with the autopsy explicitly parked.
2. **D's Gate-4 kill was based on the wrong product.** NYSE TAQ Order Imbalances ($1,000/content-month) is not the relevant path. Orchestrator E-probe (Databento metadata API, 2026-07-17): `XNYS.PILLAR` `imbalance`, 20 liquid NYSE names × 2020-2026 = **$57.79**; 10 names × 2023-2026 = **$15.58**. Gate 4 passes for a historical autopsy.
3. **The 2024 regime break is confirmed twice at T1** (SEC SR-NYSE-2024-13 / Release 34-100327, and independently in the Pillar spec's own change log v2.2k, 2024-07-25): Closing D-Orders included in ALL closing imbalance messages from 15:50 (previously only from 15:55), effective 2024-08-12; Significant Closing Imbalance regime (30/50/70% of 20-day avg close size + $200k floor) live 2024-10-28. Consequence: **pre-Aug-2024 history tests a dead information regime; post-Aug-2024 history is short AND the late-entry channel grew** (floor-broker OMS automation: final-10-second D-Order share 4.45%→13.4% by Sep 2025).
4. **Hu-Murphy magnitudes are downgraded.** Bibliography confirmed (Hu & Murphy, Management Science 72(5):3974-3996, online 2025-09-02; COVID floor closure = 2020-03-23→05-26). Qualitative core confirmed from the abstract (NYSE closes reverse more; floor-closure causal support). But the widely-quoted magnitudes ("~40 bps near-error improvement at D-inclusion", "~2x overnight reversals") could not be located in any readable primary text (paywalled everywhere) → **PLAUSIBLE, abstract-only**; and B&M's own (refuter-read) regressions find large-stock overnight reversals similar across venues with NYSE excess ≈ +1.2 bps deviations — do not quote "2x".

### Verdict (orchestrator)

**`NOT-VIABLE-STRUCTURAL`** (confidence **HIGH**) for porting the champion as a deployable strategy. Three current-T1, refuter-confirmed grounds, each independently sufficient:

1. **No post-signal on-close instrument.** Retail MOC/LOC cuts off at 15:50 (offset-only vs a Significant Imbalance afterwards; Alpaca CLS rejects at 15:50 for all symbols). The champion's sequencing — observe an indicative price at 15:55:10, then act — has no NYSE on-close expression at all. (On Nasdaq, LOC survives to 15:58 post-signal.)
2. **No locked auction state at any retail decision instant.** Floor-broker-only D-Orders (~46-60% of close volume) enter/modify/cancel with no side restriction until **15:59:50**, with >60% of their volume arriving after 15:57:30 and a tripling final-10-second share; a DMM prices the close with discretion inside the published band (lane-B T1, unrefuted). Any snapshot an outsider can act on is adversarially incomplete by construction.
3. **No near price.** `IndicativeMatchPrice` is literally "For NYSE, set to 0" (spec v2.2j and current v2.2n, both read by refuters); the analog fields default to 0 until crossable, quantities are computed at the ReferencePrice and round-lot truncated. The champion's signal object does not exist on this venue in comparable form.

**Parked (not chartered):** a ≤$16 instrument-only base-rate study (10 names × 2023-2026: imbalance/side flip rates 15:55→15:59:50, ContinuousBookClearingPrice zero-rates, pre/post-2024-08-12 split) — no trial family, run only if some future decision needs the number. With ~$30 credits left and the champion forward-paper unstarted, do not spend now.

What would flip the verdict: an SEC-approved NYSE rule change freezing auction interest at or before a public snapshot (e.g., D-Order cutoff moved to ≤15:55 with full inclusion), or the parked base-rate study showing post-2024 flip rates are negligible on megacap names (low prior given NYSE's own 2025 timing data).

### Mechanism (the useful by-product)

The same indexed-MOC payer exists on NYSE, but the residual it leaves at the close is captured by the venue's own late-flexibility holders (floor D-Order clients), not by feed readers. **Corollary for the champion:** the Nasdaq edge lives where the venue design freezes the auction state at the decision instant — MOC locked at 15:55, a true indicative clearing price published at 1s cadence, no discretionary rewrite channel. This is the cleanest structural statement yet of *why* the champion's 15:55:10 snapshot can be a sufficient statistic on Nasdaq and provably cannot be on NYSE. It strengthens the champion's mechanism narrative and sharpens the deployment doctrine: only trade auctions whose state is frozen at your decision instant.

### Claims (load-bearing, post-refute)

| ID | Status | Claim |
|----|--------|-------|
| C1 | **CONFIRMED** (T1, refuter) | MOC/LOC cutoff 15:50; offset-only vs Significant Imbalance after; D-Orders floor-only, no side restriction, until 15:59:50 |
| C2 | **CONFIRMED** (T1, refuter) | SR-NYSE-2024-13 / Rel. 34-100327: D-Orders in public imbalance from 15:50 (was 15:55), eff. 2024-08-12; Significant Imbalance 30/50/70% + $200k, live 2024-10-28. Independently in Pillar spec change log v2.2k. No later rule change alters these through 2026-07 |
| C3 | **CONFIRMED** (T1 NYSE research, refuter) | D-Orders ≈46%+ of executed close volume (Aug 2024); ~60% of auction interest (Sep 2025); >60% after 15:57:30; final-10s share 4.45%→13.4% (OMS automation) |
| C4 | **CONFIRMED** (T1 spec v2.2j + v2.2n read in full, 2 refuters) | IndicativeMatchPrice "For NYSE, set to 0"; ContinuousBookClearingPrice / AuctionInterestClearingPrice default 0; quantities at ReferencePrice; 1s-on-change from 15:50; round-lot truncation attested in spec doc-history (v2.1c). Pre-2019: 15:45 start, 5s cadence — backtests must not assume current cadence |
| C5 | **PLAUSIBLE (abstract-only)** (T2, 2 refuters) | Hu-Murphy Mgmt Sci 2025: NYSE closes reverse more than Nasdaq; COVID floor closure (2020-03-23→05-26) supports causal D-Order channel. Magnitudes ("2x", "~40 bps") UNVERIFIED — paywalled; B&M counter-evidence on large-stock reversals |
| C6 | **CONFIRMED** (E-probe, metadata API) | Databento XNYS.PILLAR imbalance history: $57.79 (20 names, 2020-2026) / $15.58 (10 names, 2023-2026). D's $12k TAQ figure = wrong product. RT remains ~$1k+/mo (not needed, not approved) |
| C7 | CONFIRMED (T1, lane B + wave-1) | Alpaca CLS rejects after 15:50 all symbols; IBKR D-Quote = brokered floor agency hop, not self-directed |

### Constraint gates (deployable port)

| # | Gate | Result |
|---|------|--------|
| 1 Latency | **FAIL** | Auction state not frozen at any retail-visible instant; rewrites until T-10s |
| 2 Access | **FAIL** | No post-signal on-close order; D-Orders floor-only |
| 3 Session | PASS (narrow) | Close-flat structure would be in-mission if reachable |
| 4 Data | **PASS for autopsy** ($15.58-57.79 quoted) / FAIL for RT deploy (~$1k+/mo) |
| 5 Fill realism | **FAIL** | No locked near → entry/exit model unsound; exit-at-cross not securable post-signal |
| 6 Statistics | N-A | Structural kills precede power |
| 7 Protocol | **FAIL** | Cannot pre-register a stable-payer rule against a discretionary rewrite channel |

**Survivor-profile score: 1/5.**

### Economics sketch

No outsider gross exists to cite; structural prior ≤0 net after the late-rewrite channel. Champion comparison line: +2.5 bps/event dev / +12.5 holdout — earned on a venue whose design freezes the state it prices. Data autopsy cost if ever wanted: $15.58 (quoted). RT feed: ~$1,000+/mo (fails everything at our size).

### Ledger-note suggestion (user only)

> `DR-Q7 2026-07-17: NYSE port NOT-VIABLE-STRUCTURAL (HIGH) — no post-signal on-close order (15:50 cutoff), no locked near (IndicativeMatchPrice=0 by spec), D-Orders rewrite until 15:59:50 (46-60% of close, final-10s share tripled 2025); 2024 rule change killed the pre-2024 info regime for backtests; Hu-Murphy magnitudes downgraded to abstract-only. Databento autopsy quoted $15.58-57.79 (parked, no family). By-product: champion mechanism sharpened — trade only auctions whose state freezes at the decision instant.`

### Sources / modality files

`modality-A.md` … `modality-D.md`; refuter reports summarized in Claims (3 completed agents, 2026-07-17: NYSE rules/2024-change bundle confirmed at T1; Pillar spec v2.2j AND current v2.2n read in full; Hu-Murphy bibliography via Crossref/INFORMS). E-probe: Databento `metadata.get_cost`, 2026-07-17.
