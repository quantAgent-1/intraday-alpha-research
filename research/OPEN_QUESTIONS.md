# Open Research Questions — enginev5.1 (2026-07-17)

> Deep-research harness (tool-agnostic): `research/deep/HARNESS.md` — orchestrator protocol;
> every research agent must receive `research/deep/AGENT_BRIEF.md` verbatim. Verdicts accumulate
> in `research/deep/EXHAUSTION_MAP.md` (the open-vs-exhausted state of the solution space).
> In Claude Code: `/engine-deep-research <#|map>` is an opt-in launcher only — plain deep-research
> requests use the generic skill.

Areas that warrant more inquiry, each written as a hand-off brief for a research agent.
Context every agent needs: we found ONE holdout-confirmed edge — a Nasdaq closing-auction
"basis" trade (at 15:55:10 the NOII indicative near-price vs the market mid; |basis|>=10bps ->
trade toward near, exit at the 16:00 official cross; ~+2.5 bps/event, 63% directional, holdout
+12.5 on 31 sealed sessions). A LightGBM meta-filter modestly improves hit-rate (53.6->57.7%).
Everything else (intraday taker signals, both ML tiers, daily reversal, opening cross) is dead.
Operating assumptions: manual, example ~$1,000 capital lens, 5-25s latency, no PDT, US equities.

---

## A. MECHANISM — why does the closing-auction basis edge exist, and who pays it?
1. **Who is the payer at the close?** Decompose Nasdaq closing-cross participation: index-fund
   MOC orders, LOC/MOC retail, portfolio rebalancers, ETF creation/redemption. Which of these is
   the price-insensitive forced flow that the near-vs-mid gap captures? Is there academic or
   practitioner literature on closing-cross imbalance predictability (SSRN/quant blogs 2020-2026)?
2. **Does the edge scale with index-membership / passive ownership?** Prediction: names with more
   index-fund ownership have larger, more predictable MOC flow. Testable with % passive ownership
   or index weight as a conditioning variable.
3. **Auction microstructure**: exact Nasdaq closing-cross mechanics, the NOII dissemination
   schedule (near/far populate ~15:55), the LOC order cutoff (15:50) and its late-order rules —
   does the 15:55 vs 15:50 vs 15:58 signal timing matter? What is the theoretical best decision
   instant given the order-entry deadlines?

## B. EXECUTION REALITY — can a manual retail trader actually capture this?
4. **MOC/LOC order access at retail brokers** (IBKR, Schwab, Fidelity, Alpaca): can a manual
   trader submit a market-on-close order by the 15:50 cutoff? Does the taker entry at 15:55 need
   to be a marketable limit? What are the real fill mechanics and costs of MOC participation at
   small size?
5. **Slippage/impact of the 15:55 taker entry** at 5-25s manual latency: our sim crosses the
   spread once; is that realistic into a thinning pre-close book? Would a marketable-limit reduce
   adverse selection? Is there a better entry (LOC order priced at near) that avoids the taker
   cost entirely?
6. **Capacity**: at what $ size does a single-name MOC basis trade start moving the cross against
   itself? (Bounds the strategy's scalability and whether $1,000 -> larger ever matters.)

## C. GENERALIZATION & CAPACITY (partly in-flight as M11)
7. **Cross-listing**: does the same mechanism exist on NYSE closing auctions (different auction
   design, D-Order mechanics)? Would need NYSE imbalance data (Databento XNYS pillar).
8. **ETF closing crosses** (QQQ, SMH, IWM, sector ETFs): where indexed MOC flow is MOST
   concentrated — is the basis edge larger and more reliable on ETFs than single names?
9. **Regime dependence**: the edge was strong 2020-21, weak 2022-23, back 2024-26. What macro/vol
   conditions turn it on/off? Is it a volatility-of-imbalance effect? Can the on/off state be
   predicted from the morning?

## D. ADJACENT AUCTION/EVENT EDGES (new families, mechanism-first)
10. **Opening cross** — we tested a naive version (M6b) and it FAILED. But was the failure the
    signal or the execution (MOO fill + timed exit)? Is there a smarter opening-auction structure
    (e.g. opening imbalance vs overnight gap) worth one more registered look?
    **→ RESOLVED-EXHAUSTED (2026-07-23):** the one sanctioned look ran as M24 (price-dislocation
    fade, BETWEEN THE BARS, family closed); the remaining quantity axis (unpaired residue) was
    KILLED at pre-declared F3 prong-0 (ρ −0.0004 [−0.022,+0.021], n=11,487, both directions;
    first direct test of the cell) with mechanics adjudicated at T1 by DR-X11 (pure on-open
    interest cancels at the cross; the persisting component is resting limit liquidity — no
    continuation payer). Successor question (different information set, unchartered, round-2
    fence audit first): does PRIOR-DAY off-exchange retail flow predict opening-PRINT reversal
    capturable via a pre-positioned on-open order (Brown-class)? See
    `research/deep/DR-X11-opening-residue/report.md`.
11. **LULD halt/reopen auctions**: forced-liquidity reopenings after volatility halts — the
    imbalance messages are in the NOII schema we own. Rare but potentially large edge. Feasibility
    + base-rate study.
12. **Index reconstitution / rebalance days** (quarterly S&P/Nasdaq rebal, Russell June): the
    largest scheduled forced-flow events of the year. Does the closing-auction basis edge amplify
    on rebal days? Free to test on owned data (calendar-conditioned).
13. **Earnings-day closing auctions**: after an earnings gap, does the closing cross carry
    predictable rebalancing flow? The one catalyst x auction intersection untested.

## E. DATA & VENDOR (for when/if the edge deploys)
14. **Real-time NOII for live execution**: exact cost and latency of a live NOII feed (Databento
    live ~$199/mo, or broker-provided TotalView). What's the minimum viable live data stack for a
    manual MOC trader, and is it justified by the edge size?
15. **Depth (MBP-10)**: would closing-book depth improve the fill model / capacity estimate enough
    to matter? (Deferred; low prior for signal, real for execution realism.)

## F. STATISTICAL / METHOD
16. **The n-vs-noise ceiling**: per-event PnL std ~20bps; the ML increment over naive selectivity
    is ~1 SE. Is there a variance-reduction framing (pairs/hedged closing baskets, market-neutral
    at the close) that cuts the 20bps noise rather than chasing the small mean? A market-neutral
    long-imbalance/short-index closing book could raise Sharpe by removing beta.
17. **Multiple-testing honesty**: formal deflated-Sharpe / family-wise accounting across ALL ~18
    registered families in this project — what is the honestly-deflated significance of the
    surviving auction edge given everything we tried?
18. **Meta-labeling at small n (M8-v2 design input; added 2026-07-19)**: empirical best practice
    for gating classifiers trained on O(10^3) events with a 55-60% base hit-rate — calibration
    choice at small n (isotonic vs Platt), feature-count discipline vs overfit, threshold transfer
    across regimes, and when a learned gate actually beats a single-feature filter (our F/ADV
    alternative from M12). Deliverable: parameter priors + an honest go/no-go heuristic for the
    M8-v2 registration. Wave-charge candidate; provenance `research/deep/EXT-ML-MOMENTUM-2026-07-19.md`.

---

## Priority ranking (updated 2026-07-17 after wave-2: DR-Q1-3 / DR-X1 / DR-Q7 / DR-X2)

Wave-1 reports: `research/deep/DR-Q4-6-retail-moc/`, `DR-Q8-etf-crosses/`, `DR-Q12-rebal-days/`,
`DR-Q16-mkt-neutral/`. Wave-2 reports: `DR-Q1-3-payer-mechanism/`, `DR-X1-letf-close-flow/`,
`DR-Q7-nyse-close/`, `DR-X2-earnings-calendar/`. Wave-3: `DR-X3-retail-execution-quality/`,
`DR-X4-dynamic-trading-and-intraday-map/`, `DR-X5-liquidity-down-auction/`,
`DR-X6-holdings-archive-scout/`. Map: `research/deep/EXHAUSTION_MAP.md`.

- **THE CLOCK**: M10 forward-paper — session 1 = 2026-07-17 banked (daily routine standing);
  39 sessions to the gate.
- **DONE 2026-07-18** (bullets retired 2026-07-20): DR-X6 weights BUILT (42,046 rows, QA
  105/105, PIT join verified) and CONSUMED by M12 Cells B/C/A2 the same day — Cell B NULL,
  A2 REJECTED (dilutes), family verdict: single-stock LETF flow WINS. Closure deviations
  ruled 2026-07-20 (ledger M12-cellB-A2-closure-ruling): 13F leg and SPX/semis legs not
  required; A2 SPX-leg completion = optional LOW hygiene.
- **NOW / Phase 0 cost**: M16 Phase-0 audit REGISTERED 2026-07-18 (+ resting arm B
  2026-07-20, pre-thresholded); awaiting user screen time during US RTH. Priors: mid-day
  E/Q 0.55–0.70; last-15m UNKNOWN (do not assume PI; project shortfall 1.46 bps).
- **M16 (wave-3 DR-X4)**: GP partial-adjust method OK **only** on named flow/calendar aim;
  pure intraday patterns EXHAUSTED-BY-FIELD; hourly stat-arb NOT-VIABLE-STRUCTURAL.
- **CLOSED wave-3**: liquidity-down deploy (DR-X5 NOT-VIABLE-STRUCTURAL — spread eats |dev|);
  first→last HH / published TOD harvest; dense free daily Wayback holdings as primary path.
- **NOW / free / analysis (prior)**: #16 residualization; #12 calendar flags; #4–#5 entry-cost log.
- **Optional cheap null**: #8 Nasdaq ETFs. **Still open**: #9 regime; #14 live NOII.
- **CLOSED wave-4 (2026-07-20, in-session)**: intraday reversion PERMANENTLY (M18 obituary +
  DR-X7 4/4 field/structural kill, refuter-verified; M19 killed pre-registration — $0, no
  trial charged); maker-first economics (DR-X8: rebates structurally unreachable; touch=fill
  phantom; M18 ember most-likely-phantom). Residues: `research/COST_MODEL.md` v1 (Alpaca
  floor ≈ 2.4× below old proxy); M16 Phase-0 resting-limit arm w/ pre-registered
  reopen/close thresholds; F_t-as-champion-feature thresholds folded into M8-v2 draft;
  optional $0 non-trading F-probe (LOW). PDT abolished 2026-06-04; small-acct binding
  constraint = cash T+1 recycling + odd-lots. `research/deep/WAVE4_SYNTHESIS.md`.
- **Doctrine**: only trade auctions whose state freezes at the decision instant. Corollary
  (M18/wave-4): a mid-neutral trigger cannot be conditioned or executed into positive
  expectancy — demand demonstrated conditional mid-alpha before any conditioning family.
