# DR-X1 — LETF / single-stock-LETF rebalance flow at the close

**Date:** 2026-07-17
**Mode:** Wave-2 deep-dive (new cell; adjacent to OPEN_QUESTIONS #1-#2)
**Agents:** 4 modality (A academic, B primary/venue, C practitioner, D adversarial) + 4 claim-refuters (2×2 bundles; all completed)
**Orchestrator synthesis — not delegated**

### Synthesis

| Lane | Verdict rec | Core thrust |
|------|-------------|-------------|
| A | OPEN-TESTABLE (MED) | Payer real, formulaic ((L²−L)·AUM·r), late-day concentrated; field average impact economically small post-flows; single-stock era (2022-26) is an academic GAP |
| B | OPEN-TESTABLE (MED) | T1 prospectus/N-PORT data paths; AUM ranks NVDA/TSLA/MU ≫ AVGO/NFLX/LRCX; "Rafferty executes MOC" trust language |
| C | OPEN-TESTABLE (MED) | Swap-dealer hedge near NAV time; free AUM ≤$100; venue mix (MOC vs continuous) UNKNOWN; survivor 3/5 |
| D | NOT-VIABLE-STRUCTURAL (HIGH) as new signal | Anticipated/sunshine flow; field nulls; if MOC it's already in near; "AUM concentrates in TSLA/NVDA not MU" |

**Dissents resolved by refuters:**
1. **The B-vs-D MU conflict was a DATE artifact, and its resolution is the wave's key finding.** Both refuters (independent, T1 N-PORT anchors): MU complex = $22M (2025-04-30) → ~$0.6B (2025-12-31) → $1.42B (2026-04-30, T1) → crossed $5B ~2026-05-28 → ~$5.8-6.4B mid-July 2026, ranking **MU > TSLA ≈ NVDA ≫ AVGO ($0.6B) ≫ NFLX ($0.2B) > LRCX ($0.06B)**. D's "not MU" was correct for 2025 and stale for 2026. LETF-flow intensity must be treated as **AUM(t), a time-varying regressor**, not a static name rank.
2. **B's T1 "executes MOC" anchor was a scope error** (refuter, filing text read): the Direxion language is trade-aggregation boilerplate recurring in 44 filings since 2013, covers the adviser's own portfolio trades, and the specific accession registers an S&P 500 fund. It does NOT establish that swap-counterparty hedges print MOC. **Venue-of-flow (auction vs continuous vs OTC) is UNVERIFIED** — C's C7 was right.
3. D's field-null anchors survive but with degraded force: Lenkey 2024 survey is **ProShares-funded (conflicted)** and its no-front-run conclusion rests on two pre-2020 studies; Ivanov-Lenkey's flow-offset sample (2006-2014 index LETFs) **predates the single-stock era entirely**; the broker-pre-hedge mechanism is an anecdotal footnote. None of these tested anything like the champion structure or 2022-26 single-stock concentrations.

### Verdict (orchestrator)

**Split verdict (do not flatten):**

1. **As a new standalone alpha / front-run family:** `EXHAUSTED-BY-FIELD` (confidence **MED-HIGH**). No published net-profitable front-run; average impact small after flow offsets; a continuous-market expression would re-enter the dead M3/M5 fill regime. Do not register a front-run family.

2. **As the name-selectivity MECHANISM for the champion (+ conditioning overlay):** `OPEN-TESTABLE` (confidence **MED-HIGH**) — **the strongest mechanism candidate now on the table.** The refuter-established AUM(t) chronology matches the champion's alive/dead split across name AND time on owned data (orchestrator E-probe, near-vs-mid 2020-2026):
   - NVDA: +2.12 bps (2020-22) → **+3.45, dir 0.572** (2023-26) — strengthens exactly as NVDL (Dec-2022 launch) scales to $4B+.
   - MU: +0.83 full-sample (dir 0.495, complex nonexistent pre-late-2025) → **holdout +52 in Jun-Jul 2026** — exactly the window the MU complex went #1 (~$6B).
   - TSLA: positive both eras (TSLL multi-B since 2022).
   - LRCX/AVGO/NFLX: dead (complexes $0.06-0.6B) despite NVDA-class vol — fits.
   - **GOOGL is the named counter-example to beat:** GGLL is ~$1.1B (billion-scale) yet GOOGL is champion-dead (dir 0.431 post-2023). Any registered test must normalize predicted flow by ADV/close-volume and must beat this case, not ignore it.

3. **Venue-of-execution:** `UNVERIFIED` — flow may print MOC (in NOII near by 15:55), continuous late-session (moves mid), or net OTC. The alignment test below is deliberately venue-agnostic (it conditions on basis alignment, whichever side of near-vs-mid the flow moves).

What would flip #2: ADV-normalized predicted flow F/ADV failing to separate alive from dead names (esp. failing the GOOGL case); or event-level conditioning adding nothing to the champion at n≥250; or the MU-2026 coincidence dissolving under the time-series test (e.g., MU high-F events in 2026 no better than MU low-F events).

### Mechanism

LETF sponsors (and swap counterparties) must reset exposure to L×AUM at the daily NAV stamp; both leveraged and inverse funds trade **in the direction of the day's return**, size ≈ (L²−L)·AUM·r, price-insensitive by mandate, known by ~15:50 from public inputs. Single-stock LETFs concentrate 100% of this on one name (index LETFs dilute by weight). Capital flows offset part of gross demand (Ivanov-Lenkey; index-era estimate, single-stock era untested; −1x funds may amplify). Whether the hedge prints in the closing cross or continuous 15:30-16:00 is unverified — either way it shapes the 15:55:10 near-vs-mid geometry the champion trades.

### Claims (load-bearing, post-refute)

| ID | Status | Claim |
|----|--------|-------|
| C1 | **CONFIRMED** (T1 N-PORT + dated T3 chain; 2 refuters) | MU complex: $22M (2025-04) → $516M (2026-01-01) → $1.42B (2026-04-30, T1) → ~$5.4B (2026-05-28) → $5.8-6.4B (2026-07). Mid-2026 rank: MU > TSLA ≈ NVDA (~$5B each) ≫ AVGO $0.6B ≫ NFLX $0.2B > LRCX $0.06B. GGLL (GOOGL) also billion-scale. Tier list volatile — use AUM(t), never static ranks |
| C2 | **CONFIRMED** (T2; 2 refuters; scope caveats) | Ivanov-Lenkey JFM 2018: flows cut rebal demand (−85%/−66% top-|r| quintile for +3x/+2x); post-adjustment LETF rebal explains <2% of late-day returns. Sample = 72 INDEX LETFs 2006-2014 — predates single-stock era; −1x funds' flows may ADD demand |
| C3 | **CONFIRMED w/ CONFLICT TAG** (T2, ProShares-funded; 2 refuters) | Lenkey QFE 2024 survey: no published net-profitable LETF front-run; sponsors may submit MOC through the day and brokers pre-hedge/spread it (anecdotal fn.6). Basis: two pre-2020 studies; DECAY-UNKNOWN; not champion-structure |
| C4 | **REFUTED as evidence of MOC venue** (T1 filing read; refuter) | Direxion "Rafferty ordinarily executes ... market-on-close" = fair-allocation boilerplate (44 filings since 2013), adviser's own trades only, accession registers an SPX fund. Venue of swap-hedge flow UNVERIFIED |
| C5 | **CONFIRMED** (T1/T3, refuter + live probes) | Free AUM(t) reconstructible: SEC N-PORT bulk (2019Q4→; effectively QUARTERLY public granularity for most of the archive), REX issuer pages live T1, Direxion/GraniteShares pages bot-gated, dated aggregator articles as anchors, NAV-growth interpolation between anchors |
| C6 | CONFIRMED (T2, unrefuted, consistent across A/D) | Field: late-day concentration of LETF-attributable pressure (Barbon et al. last-30-min); average impact small on liquid names; Cheng-Madhavan identity standard |

### Constraint gates (mechanism/conditioner path)

| # | Gate | Result |
|---|------|--------|
| 1 Latency | **PASS** | F computable by 15:50; decision instant unchanged (15:55:10) |
| 2 Access | **PASS** | Trades the same champion structure on underlyings |
| 3 Session | **PASS** | Flat at the 16:00 cross |
| 4 Data | **PASS** | Owned NOII/SIP/bars + free AUM anchors ($0; ≤$20 contingency for an aggregator pull) |
| 5 Fill realism | **PASS** (conditioner) / FAIL (any continuous front-run variant — do not build) |
| 6 Statistics | **PASS** | n≫250 champion events for conditioning; rank test across 33 names × eras; UNDERPOWERED flag only for |r|>3% tail-only variants |
| 7 Protocol | **PASS** | Named payer + a-priori F construction and GOOGL counter-example; charges new family (close-LETF mechanism/conditioner); does NOT reopen dead M3/M5 intraday letf_window |

**Survivor-profile score (conditioner): 4/5** (single-print structure inherited from champion; effect-size ≥2× cost unproven — that is the test).

### Economics sketch (bps per event)

| Object | Prior |
|--------|-------|
| Champion | +2.5 dev / +12.5 holdout (MU-carried) |
| Field avg LETF late-day impact (index era, flow-adjusted) | ≪1 bp — bearish for unconditional overlays |
| Conditional target (pre-registered) | alignment lift ≥ +1.5 bps and dir +2pts on aligned vs anti-aligned events |
| Cost | $0 data; same execution as champion |

The mechanism's value is not a new mean — it is (a) a principled forward-book name filter replacing tournament-winner picking, and (b) an explanation that makes the MU holdout anomaly *predictable rather than embarrassing*.

### Proposed next test (user decides registration) — "M12-LETF alignment"

**Hypothesis:** Champion event economics improve with pre-computed LETF-flow alignment. F_{i,t} = Σ_j (L_j²−L_j)·AUM_{j,t-1}·r_{i,t→15:50}, single-stock w=1 + index-LETF basket × weight, normalized by ADV20 (primary) and by trailing median cross_size (secondary).
**A-priori (lock before run):** (i) cross-section×era: top-tercile F̄/ADV names/eras have dir ≥ +3pts vs bottom tercile; (ii) event-level: sign-aligned (F, basis) events beat anti-aligned by ≥1.5 bps net and ≥2pts dir at n≥250/side; (iii) **GOOGL clause:** GOOGL's F/ADV must be materially below NVDA's in the same era, or the hypothesis is misspecified — report explicitly.
**Kill:** no monotonicity; or alignment lift <0.5 bps; or all lift concentrated in |r|>3% days with n<100; or AUM(t) reconstruction coverage <80% of 2023-26 sessions.
**Data:** owned NOII/bars + free AUM anchors (N-PORT bulk, issuer pages, dated articles). $0.
**Family charged:** DR-X1 close-LETF mechanism/conditioner (new).
**Promotion:** conditioner into M10 forward-paper name/event filter only — never a standalone book from backtest.

### Ledger-note suggestion (user only)

> `DR-X1 2026-07-17: front-run family EXHAUSTED-BY-FIELD; LETF flow as champion name-selectivity mechanism OPEN-TESTABLE $0 (M12-LETF alignment sketch). Refuters: MU complex $22M(2025-04)->$5.8-6.4B(2026-07, T1 anchor 1.42B@04-30) = holdout window; venue-of-flow UNVERIFIED (Direxion MOC quote = allocation boilerplate); GOOGL/GGLL is the named counter-example; Lenkey survey ProShares-funded (conflict-tagged).`

### Sources / modality files

`modality-A.md` … `modality-D.md` in this directory; refuter outputs summarized in Claims above (4 refuter agents, 2026-07-17; MU-AUM pair resolved the B/D conflict with T1 N-PORT accession 0001193125-26-287370).
