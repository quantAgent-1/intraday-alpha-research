# Solution-Space Exhaustion Map — enginev5.1

Maintained per `research/deep/HARNESS.md` (seeded 2026-07-17 from ledger + experiments +
OPEN_QUESTIONS.md + the 2026-07-16 frontier sweep). One row per cell of the solution space;
verdicts use the skill's fixed vocabulary. `Qn` = research/OPEN_QUESTIONS.md item.
Champion benchmark: closing-auction basis, +2.5 bps/event dev / +12.5 holdout (31 sessions,
MU-concentrated), M8 meta-filter on top; judged forward by M10 (paper) + M11 (28-name OOS).

Taxonomy axes: **execution regime** (continuous-taker | continuous-maker | single-print
auction | scheduled event window) × **horizon** (<15 min | intraday minutes–hours | at-close |
overnight/1–5 d) × **mechanism** (forced/scheduled flow | behavioral | structural |
liquidity-provision | information). The program's core empirical lesson: only cells with
single-print execution + scheduled timing + a forced payer have survived honest fills.

## Continuous-market intraday (RTH) — regime effectively CLOSED

| Cell | Verdict | Receipt |
|---|---|---|
| Sub-15-min single-name taker, any signal | EXHAUSTED-BY-US | engineV2: 0/75 cells; mid-neutral, spread was the loss |
| Bar-tier ML (30 m–4 h) forecast → economics | EXHAUSTED-BY-US | engineV5 (IC real, alpha ~0); A1 3 variants |
| NN/sequence models on bars/events | EXHAUSTED-BY-US | engineV5 TCN; M4 TCN/TST; M9 (auction tier) |
| Passive maker spread-capture, single names | EXHAUSTED-BY-US | M3 v1.4: edge was phantom fills; books −1.4..−4.1 |
| Intraday payer detectors (vwap/letf/pin/gap/cascade) | EXHAUSTED-BY-US | M3/M5 family closed under v1.4 |
| Uncertainty/toxicity skip-filters | EXHAUSTED-BY-US | engineV5 + M4 (anti-select winners) |
| LOB deep learning for economics | EXHAUSTED-BY-FIELD | frontier 07-16: dead without colocation |
| Intraday PEAD, megacaps | EXHAUSTED-BY-FIELD | frontier 07-16 (inverse PEAD in optioned names noted) |
| Event-day intraday taker | EXHAUSTED-BY-FIELD | frontier 07-16 |
| "More/better L1 data" as unlock | EXHAUSTED-BY-FIELD | frontier 07-16 |
| Intraday reversion, incl. flow-conditioned (M19 premise) | EXHAUSTED-BY-US + EXHAUSTED-BY-FIELD | M18 obituary (system −3.46/trade n=1,494) + wave-4 DR-X7 4/4 + 2 refuters: re-hedge is close-only (415 filings/5 families template; Direxion-only discretionary escape; Barbon: zero intraday impact any window); EOD reversal payer = retail/shorts (caveat: test pre-dates single-stock era). `WAVE4_SYNTHESIS.md` |
| Maker-rebate capture at retail tiers | NOT-VIABLE-STRUCTURAL | wave-4 DR-X8: sell-side reg fees ($0.0037/sh @$170) > entire base rebate ($0.0013); Alpaca retains; IBKR commission > accessible rebates (top tiers need >1.5% consolidated volume) |
| **Bar-derived signal battery at the OPEN-CROSS structure (pre-09:28 inputs, MOO entry, 15:40-45 exit), 176 names** | **EXHAUSTED-BY-US (HIGH, directly measured) — M28 NULL-AT-ADMISSION 2026-07-27** | 14 pre-declared signals (9 prior-session + 5 pre-market), 100,271 name-days over 604 sessions. 0/14 cleared BH-FDR q=0.10; smallest p 0.158 vs 0.0071 required (~22× miss); largest \|IC\| 0.0138 vs a ~0.02–0.03 tradeability floor and a 0.0207 detection threshold. **Effects are too small to trade even taken at face value.** Breadth was NOT binding: mean pairwise ρ +0.040, N_eff 9.21/14. First adequately-powered null in this direction; validate window deliberately unread. `research/experiments/M28-open-cross-battery/RESULT.md` |
| Maker-entry-on-signal (spread saving) | EXHAUSTED-BY-US | M18 receipt + wave-4 DR-X8: touch=fill phantom (favorable-subset fills ~2–15%; markout −0.5..−1 bp ≈ entire gross); ember most-likely-phantom. One door: M16 Phase-0 resting arm (pre-thresholded) |

## Auctions & single-print — the LIVE regime

| Cell | Verdict | Receipt / pointer |
|---|---|---|
| Nasdaq closing basis, 5 semis | **ALIVE (champion)** | M6-FINAL holdout +12.5 [6.9, 18.5] |
| Meta-filter on champion | ALIVE (ceiling reached) | M8 PASS; M9 NULL (snapshot GBDT = ceiling) |
| Champion on 28 unseen Nasdaq names | **FAILED (edge is narrow)** | M11 2026-07-17: net −3.0 bps, dir 0.470, all 6 sectors negative; vol-mechanism falsified same day |
| Champion forward validity | IN-FLIGHT (0 sessions) | M10 harness live; forward window opens 2026-07-16 (holdout consumed through 07-15); collection NOT started |
| Mechanism: who pays the close (payer identity) | **ANSWERED (wave-2)** | DR-Q1-3: passive/index MOC confirmed payer at T1/T2; feed censored (~23% internalized + ~30% echo prints). `DR-Q1-3-payer-mechanism/report.md` |
| Mechanism: name-selectivity — passive-weight scaling | **NULL (M12 Cell B/C, 2026-07-18)** | Weight beta +0.065 [-0.32,+0.44] with panel confound controlled; highest-weight AAPL/MSFT dead; 13F variant not pursued. Field prior confirmed in-house |
| Mechanism: name-selectivity — LETF-AUM(t) flow | **WINNER — M12 FAMILY VERDICT (2026-07-18)** | Cell A bars passed (zero-complex control); Cell C joint: +0.510 bps/sd [0.093,0.883] surviving ADV/weight/panel controls; index leg rejected (dilutes). MU holdout + NVDA-2023+ + GOOGL/AAPL/MSFT deadness all explained. Promotion: F/ADV forward filter (report-only) → M8-v2 post-gate. `research/experiments/M12-mechanism/report.md` |
| Retail MOC/LOC execution reality (cutoffs, fills, costs) | OPEN-TESTABLE (T1 doc study) | Q4–Q6 — decision-relevant pre-deploy |
| ETF closing crosses (QQQ/SMH/IWM/sector) | OPEN-TESTABLE | Q8 — NOII purchasable ~tens of $ |
| Rebal/reconstitution-day amplification | OPEN-TESTABLE | Q12 — calendar-conditioned, owned data |
| Market-neutral closing basket (variance cut) | OPEN-TESTABLE | Q16 — owned data |
| Earnings-day closing crosses | **BETWEEN THE BARS — family CLOSED (M22, 2026-07-23)** | Q13 ran as `earnings_close_v1`: Cell A champion-5 day0 +3.70 [−1.07,+8.30] n=111 (amp 1.51× vs 2× bar); Cell B broad-12 day0 +0.98 [−4.36,+8.15] n=171, modern era −2.06 — no revival. Mechanism echoes (LETF-era/complex strata) M12-consistent, reported-not-gated. Look spent; revival = NEW registration on forward data only. `research/experiments/M22-earnings-close/report.md` |
| Regime on/off predictability (2022-23 weak) | OPEN-TESTABLE | Q9 — owned data |
| LULD halt/reopen auctions | OPEN-TESTABLE but **$-BLOCKED** (2026-07-22 scout) | Q11 — owned NOII lake holds open/close windows ONLY (0 midday msgs, NVDA 2024 Q1 checked); reopen imbalance needs a re-download + ingest change; rare-event power flag stands |
| Opening cross, smarter structure | **CLOSED — Q10 FULLY ADJUDICATED: price axis (M24) + quantity axis (DR-X11 + F3 prong-0, 2026-07-23)** | Price axis: M24 `open_auction_fade_v1` (fade near-vs-ref at 09:28:30, open→close print) BETWEEN THE BARS, look spent: t25 +3.16 [−14.2,+20.8] n=1,392; t50 +37.1 [−4.6,+82.6] n=324; durable ρ vs champion −0.073; post-hoc structure reported-not-gated. Quantity axis: F3 KILLED at pre-declared prong 0 — ρ(residue, 09:35→11:00) = −0.0004 [−0.022,+0.021] n=11,487/1,608 sess/10 names; top-q +2.86 [−3.66,+10.01] vs ≥+6 bar; BOTH directions dead; first direct test of the cell (field never tested it — refuter-corrected C&G). Mechanics (T1, refuter-verified): pure on-open interest CANCELS at the cross; persisting Early-Market-Hours interest = resting limit liquidity; no continuation payer exists. Panel facts banked: 2021-05-17 EOII break (SEC 34-91461), 09:25/10s + 09:28/1s cadence, MOO 09:28 / late-LOO 09:29:30 / lock 09:25, $0.50-or-10% collar. Successor candidate (UNCHARTERED, ideation round-2 fence audit): prior-day retail flow → open-print reversal (Brown 2013–2022, decay-unknown). `DR-X11-opening-residue/report.md` + `research/experiments/F3-prong0/` |
| NYSE closing auctions (D-orders) | **NOT-VIABLE-STRUCTURAL (HIGH)** | DR-Q7 wave-2: no post-signal on-close order (15:50 cutoff); no near (IndicativeMatchPrice=0 by spec); D-Orders rewrite until 15:59:50 (~46-60% of close). Data itself cheap ($15.58-57.79 quoted, autopsy parked). Reopen only on a state-freezing rule change. `DR-Q7-nyse-close/report.md` |
| Live NOII stack for deployment | OPEN-BLOCKED (~$199/mo, decision pending edge size) | Q14 |
| Closing-book depth (MBP-10) | OPEN-BLOCKED, low prior | Q15 |
| LETF close flow as standalone front-run family | EXHAUSTED-BY-FIELD | DR-X1 wave-2: no net-profitable front-run in literature; continuous expression re-enters dead M3/M5 regime (conditioner path lives in the row above) |
| Quad-witching closes (3rd Fri Mar/Jun/Sep/Dec) | UNMAPPED | largest known scheduled close flow; subset testable on owned NOII |
| Half-day 13:00 crosses (Jul 3, Black Friday, Christmas Eve) | UNMAPPED | different flow density; owned data |
| Month/quarter-end pension-rebal closes | UNMAPPED | distinct from index reconstitution (Q12) |
| Index ADD/DELETE announcement → effective-date close | UNMAPPED | announcement-conditioned forced flow |
| IPO/direct-listing opening crosses | UNMAPPED | data availability doubtful; low prior |

## Scheduled event windows, non-auction — NEW REGIME UNDER TEST (2026-07-22)

| Cell | Verdict | Receipt / pointer |
|---|---|---|
| Market-wide scheduled macro releases (FOMC stmt/minutes 14:00; 10:00 cluster ISM/UMich/JOLTS/CB; 10y/30y auction results 13:02; 8:30 class → 09:30 open), 5 megacaps, minutes–hours CONTINUATION | **EXHAUSTED-BY-FIELD + BY-US for FOMC/8:30/10:00 — DR-X9 kill bar HELD post-refutation (2026-07-23); M20F Stage-2 BANNED for those classes per the WAVE5 pre-commitment.** Premium is pre-release (JFE 2022); FOMC reverses; no minutes-hours payer (vol-target/RP/CTA = multi-week trigger, T+1/T+2 lag, days-scale). **Sole survivor: `tsy_auction_1300` — OPEN-UNKNOWN (zero prior art, refuter-confirmed; internal cells underpowered-not-killed) → M26 narrow forward-judged registration via the dark instrument.** | `DR-X9-macro-announcement-drift/report.md` (4 modalities + 3 refuters) |

## Overnight / multi-day — OUT-OF-MISSION (policy cell, not evidence cell)

| Cell | Verdict | Receipt |
|---|---|---|
| Overnight premium harvesting | EXHAUSTED-BY-FIELD + out-of-mission | NightShares real-money failure |
| Daily 1–5 d swing (grok lead) | EXHAUSTED-BY-US | 465 OOS sessions; claimed IC did not replicate |
| Weekly/daily cross-sectional megacap reversal | EXHAUSTED-BY-US | M7 FAIL (was the field's best surviving lane) |
| Cross-sectional stock momentum 12-1 (PIT SPX) | **BETWEEN (M17-A, 2026-07-19; research-only)** | +8.8%/yr L/S at t=1.01, crash months −16%; textbook shape, unprovable at n=66. `research/experiments/M17-momentum/report.md` |
| Factor/sector momentum, top-3 ETFs monthly | **PASS — replication (M17-B, 2026-07-19; research-only)** | Sharpe 1.05 vs EW 0.95, +3.1%/yr excess (t=0.86, UNDERPOWERED flag); robust to formation window. Deploy = mission-amendment decision only |
| ML rank/blend layer on slow CS momentum (GKX / learning-to-rank class) | NOT-PURSUED — out-of-mission + field cost-fragility | EXT-ML 2026-07-19: Avramov MS 2023 (−64% ex-microcaps; turnover costs kill); layers have no in-mission surface. `research/deep/EXT-ML-MOMENTUM-2026-07-19.md` |
| Any other overnight structure | out-of-mission | needs explicit user amendment before research |

## Method / statistics / meta

| Cell | Verdict | Pointer |
|---|---|---|
| Family-wise DSR accounting across all ~18 families | OPEN-TESTABLE (analysis, no new data) | Q17 |
| Variance-reduction framings (hedged/paired at close) | OPEN-TESTABLE | Q16 |
| Real-order fill truth (paper→live calibration) | partially covered by M10; live fills future | frontier 07-16 rec #3 |
| Small retail effective/quoted cost prior ($400–$3k) | **OPEN-TESTABLE** (Phase 0) | DR-X3: mid-day E/Q 0.55–0.70 CONFIRMED class; last-15m **UNKNOWN** (stress 0.9–1.5+; project shortfall 1.46 bps). `DR-X3-retail-execution-quality/report.md` |
| GP / no-trade-band inventory method (named flow only) | **RAN — BETWEEN THE BARS (M16-A, 2026-07-19)** | Not killed (+1.69 bps/day pooled) / not promoted (CI spans 0; sd 44/day). Positive every LETF-era year; costs non-binding. Report-only; new registration needed to revisit after forward data accrues. `research/experiments/M16-stageA/report.md` |
| Hourly stat-arb / published intraday-effects book | **NOT-VIABLE-STRUCTURAL** | DR-X4 D: breadth + crowding + manual lag |
| Pure first→last HH / HKS TOD momentum harvest | **EXHAUSTED-BY-FIELD** | DR-X4: Rosa 2022 OOS kill CONFIRMED |
| Breakout / path duration-range prediction (any horizon) | **DOCTRINE-BANNED (2026-07-19)** | EXT-ML: momentum pays at book/state level, not per-path calls (DM crash mechanics; dump Layer-6). `EXT-ML-MOMENTUM-2026-07-19.md` |
| ML re-skin of dead families (regime gating, bar-tier forecasting) | **CLOSED — reopening condition now DIRECTLY ADJUDICATED (M28, 2026-07-27)** | 3× regime-gate kill + engineV5 IC receipts; estimator swap ≠ new information set. The DR-X4 reopening bar was residual IC≥0.15 + N_eff≥8 + net≥2× cost: on a 176-name panel M28 **MET the breadth leg (N_eff 9.21)** and **missed the IC leg by ~11× (0.0138 vs 0.15)**. Previously closed by inference from a 16-name study; now closed by direct measurement. Reopening requires a new INFORMATION SET, not a wider panel or a different estimator |
| Meta-labeling architecture on champion | ALREADY-LIVE (M8) — upgrade = M8-v2 post-forward-gate | Candidate features drafted (design-time, no data touched): `research/experiments/M8-v2-FEATURE-DRAFT.md` |
| Liquidity-down champion (harvest B&M 20.6 bps tier) | **NOT-VIABLE-STRUCTURAL** | DR-X5: spread eats \|dev\|; M11 already null mid-tier. `DR-X5-liquidity-down-auction/report.md` |
| Mid-band residual-vs-HS measurement (ADV $50–200M) | OPEN-TESTABLE (optional corpse only) | DR-X5: negative-to-flat prior; not deploy family |
| PIT SPX/NDX weights 2020–2026 at $0 | **BUILT + CONSUMED (2026-07-18)** | 42,046 rows, 78/78 SPX months + 27/27 NDX quarters, QA 105/105; PIT join verified strictly-prior in executed code. Consumed by M12 Cells B/C/A2 same day (B NULL, A2 REJECTED). Recipe gap: no forward collector (immaterial — index leg rejected) |

## Ranked next actions (superseded 2026-07-20, post-wave-4; prior post-wave-3 list retired —
items 2/4 executed 2026-07-18, item 3 registered)

1. **M10 forward clock** — session 1 (2026-07-17) banked; daily routine standing; 39 to gate.
2. **M16 Phase-0 execution audit** — REGISTERED 07-18 + arm B 07-20; awaiting user screen
   time during US RTH (arm A marketable E/Q + arm B resting fill/markout, pre-thresholded).
3. **M8-v2 F_t feature registration** — after the M10 forward gate; thresholds drafted
   (wave-4 note in M8-v2-FEATURE-DRAFT.md).
4. Optional/LOW: A2 SPX-leg $0 completion (hygiene; Alpaca bars free); $0 non-trading
   F-probe diagnostic; legacy Q16/Q12/Q4–6 items where still unconsumed.
5. CLOSED cumulative: reversion incl. conditioned (M18 + wave-4 DR-X7); maker-first
   economics (wave-4 DR-X8); liquidity-down deploy (DR-X5); pattern book (DR-X4);
   dense Wayback holdings path (DR-X6 — NPORT+varnish won).

## Update log

- 2026-07-22 (orchestrator, session 6): user directive — research the non-LETF continuous-intraday
  minutes–hours space. New regime section added: scheduled NON-auction event windows;
  M20 `sched_window_v1` registered pre-data (the one execution-regime cell with no prior
  family, no DR lane, no map row). WAVE5 plan written (DR-X9 gates M20 Stage-2). Q11 LULD
  scout: owned NOII has open/close windows only — cell $-blocked, not free.

- 2026-07-17 seeded (orchestrator): 10 continuous cells closed, auction regime live, 5 UNMAPPED
  candidates added (quad-witching, half-days, month-end, add/delete, IPO crosses).
- 2026-07-17 wave-2 plan (orchestrator): `WAVE2_PLAN.md` — lanes DR-Q1-3 (payer/passive-ownership
  mechanism), DR-X1 (LETF close flow, new UNMAPPED row above), DR-Q7 (NYSE close), DR-X2
  (earnings-calendar scout). Verdicts land here on synthesis.
- 2026-07-17 wave-2 SYNTHESIS (orchestrator): 13 modality agents + 10 completed refuter reports.
  Q7 NYSE closed structural; LETF front-run closed by field; LETF-AUM(t) promoted to LEAD
  name-selectivity mechanism (MU complex 10x ramp = holdout window; T1 N-PORT anchors);
  payer identity answered; joint M12 family sketched; X2 recipe delivered; XNYS autopsy
  quoted $15.58-57.79 and parked. Housekeeping: M11 row updated to FAILED; M10 row shows
  0 sessions. Reports in `DR-*/report.md`; champion doctrine sharpened: only trade auctions
  whose state freezes at the decision instant.
- 2026-07-18 wave-3 SYNTHESIS: 13 modality agents + refuters on X3/X4/X5 (X6 scout self-probed).
  DR-X3 OPEN-TESTABLE Phase-0 two-regime cost prior; DR-X4 patterns EXHAUSTED / hourly
  stat-arb NOT-VIABLE / GP+flow method OPEN; DR-X5 liquidity-down NOT-VIABLE-STRUCTURAL;
  DR-X6 $0 PIT weights UNBLOCKED (IVV monthly + QQQ NPORT). Reports under `DR-X3…X6/`.
  No ledger writes.
- 2026-07-21 wave-3 VERIFICATION pass (orchestrator, in-session): 13 Opus re-verify agents + 8
  refuters. ALL FOUR Jul-18 verdicts STAND; addenda appended to each report.md. Key
  adjudications: 605-modernization timeline CONFIRMED verbatim (odd-lot E/Q public only
  ~Nov 2026 → Phase 0 is the sole near-term cost resolver); EOD-reversal (Baltussen/Da/
  Soebhag) magnitude REFUTED 2/2 (+24 → actual 3.78 VW/6.86 EW bps/day gross, megacap
  slice ~3.4, NO-COST-MODEL, sample ends 2019 — feature candidate at most); NYSE 2023 tier
  data CONFIRMED 2/2 (dislocation-per-spread DECLINES down-curve on standard days but
  INVERTS on rebalance days — event-conditioned small-cap cell stays distinct from the
  dead tier-conditioned cell); skeptic E/Q 0.70–2.0 range REFUTED as empirical (stress
  prior only); today's JNST single-parse numbers STRUCK (parses disagree; PI-rate pair was
  a 1997-study conflation). New redundancy: Wayback IVV .ajax JSON (185 as-of dates)
  backs up varnish-api. No ledger writes.
- 2026-07-19 EXT-ML verification (orchestrator): two external momentum dumps (slow-mom framework;
  ML-for-momentum) verified in-session — claims accurate; Avramov MS 2023 added as the
  after-cost receipt (−64% ex-microcaps). 4 rows added (ML-rank layer NOT-PURSUED; path
  prediction DOCTRINE-BANNED; ML re-skins CLOSED-BY-PRECEDENT; meta-labeling ALREADY-LIVE
  via M8). User decisions: M17 stands as-is (no vol-overlay look); momentum enters only as
  M8-v2 conditioning features. Draft: `research/experiments/M8-v2-FEATURE-DRAFT.md`;
  note: `EXT-ML-MOMENTUM-2026-07-19.md`; OPEN_QUESTIONS Q18 added. No ledger writes.

- 2026-07-27 (session 9): **M28 `open_cross_battery_v1` NULL-AT-ADMISSION** — the first
  adequately-powered null in the continuous-intraday direction. Two rows above updated. The
  durable transferable finding is the EXECUTION STRUCTURE, not the signals: entry at the
  opening cross costs zero spread and the 15:40–15:45 exit is the day's cheapest minute
  (~1–3 bps all-in vs the 16–38 bps that killed M27). Assets left behind: a free 1.2 GB
  200-symbol minute-bar lake (2023-10..2026-05), a generic battery harness taking a signal list
  + frozen combination rule, a 32/32 verification suite including a black-box look-ahead test,
  and a live instrument built and correctly DARK. Also priced this session: R2-A open-print
  retail fade METHOD-BLOCKED out of sample — trade-side classification cannot be reconstructed
  without contemporaneous quotes, so flow/tape families are quote-limited to the 10-name panel
  while bar-anchored families are free and wide.
