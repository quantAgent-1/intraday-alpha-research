# M3 en-bloc registration — named-payer detectors + A0 hand-rule plans (v1)

Registered 2026-07-15, BEFORE any plan-level economics were computed on any split.
Family: `payer_detectors_v1` (new family; DSR accounting adds these to the inherited counts).
All thresholds below are a-priori: derived from the documented mechanisms
(quantresearch wiki: techniques-of-winning-trades §2/§8, liquidity-cascades, speed-vs-prediction)
and general vol/spread scale — NOT from peeking at TRAIN/VALIDATE economics.
Changing any number after results exist = a new registered variant (counted).

Evaluation: A0 = detector → hand-rule TradePlan → causal replayer (k=2, latency 5–25s,
L2-strict limits) on tick-covered sessions ≤ 2026-05-31 (holdout ≥ 2026-06-01 stays sealed).
Research book $10k/plan. Report split-wise (TRAIN-period vs VALIDATE-period sessions),
per payer and pooled, with day-clustered CIs, concentration, and stress arms.

Promotion rule (registered): a payer is ALIVE if VALIDATE-period standalone
net_bps mean > 0 with day-clustered 95% CI lower bound > −5 bps AND pooled
(train+validate period) CI lower bound > 0. DEAD if pooled upper bound < 0.
Else UNDERPOWERED (needs AMD/MU data or more sessions — not a kill).

## Shared plan-construction rules (A0)
- Entry: limit JOIN (buy at prevailing bid / sell at ask), expire per payer, chase per payer.
  Exception: letf_window uses MARKET entry (time-certain documented flow = urgency).
- valid_until = ts_authored + 120 s. Confidence = 0.5 flat (A0 has no model).
- expected_gross_bps = payer template below; expected_net = expected_gross − per-symbol RT cost.
- No entries before 09:45 or after 14:30 ET except letf_window (15:00–15:10 only).
- Curfew 15:50 ET (calendar-aware). One position per symbol; k=2 portfolio slots.
- EV hurdle: author the plan only if expected_gross ≥ max(2 × RT_cost_bps, 8 bps).

## 1. gap_mr — opening gap mean reversion
- Gap g = (open − prev_close)/prev_close. σ_d = 20-session close-to-close vol.
- ACTIVE iff |g| ≥ 0.75·σ_d AND |g| ≥ 30 bps AND first 15 min do NOT extend the move
  beyond 0.35·|g| past the open (extension ⇒ trend day ⇒ stand down).
- Decision time 09:45; direction = −sign(g) (fade). Entry limit join, expire 180 s, chase.
- Stop: post-open adverse extreme ± 0.25·|g| (min distance 25 bps).
- Targets: 50% gap-fill (frac 0.6), full fill at prev_close (frac 0.4). Hold ≤ 120 min.
- expected_gross template: 0.5·|remaining gap to prev_close| in bps.

## 2. letf_window — leveraged-ETF close rebalance pressure
- At 15:00 ET: index day-so-far return r (SOXX for NVDA/AMD/MU; QQQ for TSLA);
  demand = Σ (L²−L)·AUM·r over the complex (config/letf_aum.toml).
- ACTIVE iff |r| ≥ 0.5% (≈ |demand| ≥ ~$0.8B SOXX / ~$2B QQQ).
- Direction = sign(demand) (WITH the flow). MARKET entry 15:00–15:10. No targets;
  hold to curfew 15:50. Stop: 1.2 × avg 20-session 15:00→15:45 adverse range.
- expected_gross template: 10 bps · |r|/0.5% capped at 30 bps.

## 3. vwap_magnet — VWAP reversion on non-trend days
- State at minute t ∈ [10:30, 14:30]: dev = (price − session VWAP)/VWAP.
  σ_dev = 30-min realized vol of dev. Range-day filter: |ret from open| ≤ 0.35 · (day range so far).
- ACTIVE iff |dev| ≥ 1.5·σ_dev AND |dev| ≥ 20 bps AND range-day filter holds.
  Re-arm: one plan per symbol per side per 60 min.
- Direction = −sign(dev) (toward VWAP). Limit join, expire 300 s, no chase.
- Stop: dev extends to 2.5 × entry |dev| (i.e. 1.67× further), min 20 bps. Target: VWAP (frac 1.0).
- Hold ≤ 90 min. expected_gross template: 0.8·|dev| in bps.

## 4. cascade — liquidity-cascade / V-reversal exhaustion
- Flush: move ≤ −2.5·σ_30m within ≤ 30 min AND cumulative volume in the flush ≥ 3× the
  20-session same-clock-time average AND median spread in last 5 min ≥ 2× session median.
- Stabilization (arms the entry): 5 consecutive minutes without a new extreme AND
  5-min OFI (event bars) flips against the flush direction.
- ACTIVE at stabilization, window 09:45–14:30. Direction: against the flush (long a down-cascade).
- Limit join, expire 120 s, chase. Stop: flush extreme ∓ 0.3 × flush amplitude.
- Targets: 38.2% retrace (frac 0.6), 61.8% retrace (frac 0.4). Hold ≤ 120 min.
- expected_gross template: 0.382 × flush amplitude in bps. Both directions allowed.

## 5. expiry_pin — monthly opex pinning (exploratory; no GEX history exists)
- ACTIVE iff monthly-opex Friday (ffcal) AND t ≥ 13:00 AND |price − nearest strike| ≤ 0.3%
  (strike grid $5 for price ≥ $200, else $2.5).
- Direction: toward the strike. Limit join, expire 300 s, no chase.
- Stop: 0.6% beyond the far side. Target: the strike (frac 1.0). Hold to curfew.
- expected_gross template: |price − strike| in bps. SMALLEST budget; exploratory flag.

## Variant budget
≤ 10 registered variants per payer TOTAL (including this v1). Any threshold change
after economics exist is a variant. Obituary after budget exhaustion.

## Daily side-ledger family (`daily_swing_v1`) — registered separately
1d/3d/5d horizon LGBM on the ported v1_1 bar features, 12-name bar universe,
purged walk-forward, rank-IC + day-clustered CI only (no plan-level claim yet).
Research-only; no dashboard, no live, no overnight trades by the system. Runs
after M3 A0 (lower priority). Inherits grok E5's 9 trials in DSR accounting.

## A1 overlay — registered 2026-07-15 BEFORE economics (trial M3-A1-v1)

Model overlay on the SAME registered detector states (no new detectors, no threshold changes).
- Features: ported v1_1 38-col PIT registry, materialized on the 12-name bar universe (5-min grid).
- Models: pooled cross-symbol LightGBM (engineV5 DEFAULT_PARAMS): fwd60/fwd120 (huber) +
  MFE60/120 q50,q75 and MAE60/120 q75 (quantile). Labels vol-normalized: z = label / (f_vol20 · sqrt(H_min/390));
  de-norm inverts identically. Expanding walk-forward (models/cv.py: 21-session test blocks,
  1-session embargo); a prediction row's model is trained only on sessions strictly before its fold.
- Overlay rule (a priori):
  1. SKIP a detector state iff the model OPPOSES it: sign(pred_fwdH_z) != direction AND |pred_fwdH_z| >= 0.5
     (H = 60m for vwap_magnet/letf_window, 120m for gap_mr/cascade/expiry_pin).
  2. Legs: stop distance = de-normed |pred_maeH_q75|, floored at the A0 stop distance's minimum rule
     and capped at 2x the A0 stop distance; targets = de-normed MFE q50 (frac 0.6) and q75 (frac 0.4),
     floored at 10 bps, capped at 2x the A0 target distance. Payers with a single registered target
     use q50 only (frac 1.0). letf_window keeps no targets.
  3. expected_gross_bps = de-normed |pred_fwdH| when the model agrees, else the A0 template.
     EV hurdle unchanged (2x cost, 8 bps floor).
  4. confidence = p_win = 0.5 + 0.2 * min(|pred_fwdH_z|, 2)/2 when agreeing (max 0.7), else 0.5.
- Promotion rule (registered): A1 replaces A0 iff (a) day-clustered CI of the per-session BOOK net
  difference (A1 - A0, identical sessions, k=2 stream) > 0 on VALIDATE-period sessions, AND
  (b) A1 pooled taken CI lower bound > 0. Otherwise A0 stands and A1 gets an obituary.
- Budget: this spec + <= 3 threshold variants (z_skip in {0.3, 0.5, 0.8} counts as the family).

## M4 encoder — registered 2026-07-15 BEFORE any encoder economics (family m4_encoder_v1)

Motivation (measured): A0-v1.1 stop-removal ORACLE = +22.07 [18.60, 25.62] vs base +4.35
(vwap: +27.61 vs +6.20); stop-exits = 21.5% of plans at −60.3 bps mean. Hypothesis: the raw
event stream at decision time (order flow, spread dynamics, imbalance — the tier bar models
never saw) partially predicts which states get run over.
- Data: built decision-point dataset (99,666 points NVDA/TSLA, 271/session, 11:00–15:30 ET,
  PIT norm stats, session-safe labels). AMD/MU appended when their event bars exist (data
  extension of the same trial, not a variant).
- Architecture menu (frozen): (a) dilated TCN ~1–3M params (kernel 5, dilations to cover the
  1080-step receptive field); (b) PatchTST-small (patch 16, d_model 128, 4 layers). bf16,
  AdamW, batch 256, early stop on fold tail. ≤ 4 training runs per arch, ≤ 60 GPU-hours total.
- Heads/losses (weights frozen): H1 pinball q{10,25,50,75,90} fwd{30,60,120,close} (w 1.0);
  H2 pinball q{50,75} MFE/MAE {60,120} (w 1.0); H3 BCE 8-barrier grid (w 1.0);
  H5 huber next-30m RV (w 0.5). H4 fillnet deferred (fill-label builder not yet built).
- Folds: expanding walk-forward on every 3rd A1-LGBM fold boundary (~8 folds), embargo 1
  session; emissions carry trained_through < session (PIT, code-asserted).
- Emission contract: A1 prediction-contract columns (for legs) PLUS 8 barrier-probability
  columns p_{up|dn}first_{a}{b}_{H}; parquet at data/preds/m4_v1/{SYMBOL}.parquet.
- Ablation arms (plan-level only; evaluated via run_trial + compare_arms vs A0-v1.1):
  - A2-select: A0 plans, SKIP a state iff p(adverse barrier 1.25σ first within payer H) ≥ p_skip,
    p_skip ∈ {0.35, 0.45} (2 registered values). Legs/hurdle = A0.
  - A2-legs: A0 selection; encoder MFE/MAE legs (A1-v3 clamps; A0 hurdle).
  - A2-both: selector + legs.
- Promotion (same bar as A1): paired book delta vs A0-v1.1 on VALIDATE sessions CI > 0 AND
  pooled taken CI lower > 0. Diagnostics only: stop-hit AUC, oracle-capture fraction.
- Leg-pricing heads train unconditionally (mission: plan quality); directional/selector arms
  are unlocked (vwap_magnet ALIVE per registered rule).

## M6 auction-imbalance family — registered 2026-07-16 BEFORE any imbalance data was acquired
Family: `moc_imbalance_v1`. Mechanism: the Nasdaq closing-cross Net Order Imbalance Indicator
(NOII, broadcast from 15:50 ET) publishes FORCED terminal flow — index funds/MOC-benchmarked
orders that must trade at the cross. Named payer: the imbalance itself. The closing auction is
the one regime where limit-fill modeling ambiguity vanishes (single clearing price, no queue).
- Universe: NVDA, TSLA, AMD, MU, GOOGL (all Nasdaq-listed; condition-coded ticks in hand).
- Signal at 15:50:10 ET (first stable NOII + human latency): norm_imb =
  net_imbalance_shares × near_price / ADV20_dollars. ACTIVE iff |norm_imb| ≥ threshold.
- Direction: WITH the imbalance. Entry: MARKET at signal + latency draw (5–25 s), honest
  NBBO cross via the existing fill kernel. Exit: MOC — fill AT the official closing-cross
  print (identified by auction condition codes in our own tape), zero spread/slip by
  construction. No stop (bounded ~10-min hold).
- CURFEW EXEMPTION (registered): the 15:50 force-flat exists to guarantee flat-by-close;
  an MOC exit IS flat-by-close by construction. This family is exempt from the 15:50 curfew
  and MUST be flat at 16:00:00 exactly.
- Registered cells (en bloc, ≤4): threshold ∈ {0.05%, 0.10%} of ADV$; persistence prong
  on/off (at 15:55 NOII flips side → immediate market exit, else hold to cross).
- Promotion: pooled net bps/event day-clustered 95% CI lower > 0 AND ≥ 100 events AND
  positive in ≥3 of 5 symbols' point estimates. Fill ground-truthing per PROTOCOL v6.1
  (auction prints verified against the tape).
- ML extension (GBM on NOII features) registered CONDITIONALLY: only if the classical
  cells show life. Deep nets unjustified before a GBM shows net-of-cost edge.
- Data: Databento XNAS.ITCH `imbalance` schema, 2024-01-02 → 2026-05-31, 5 symbols
  (historical only; ~tens of dollars, likely covered by new-account credits). Evaluation
  respects the sealed holdout (≥2026-06-01 excluded).

## M6b opening-cross imbalance family — registered 2026-07-16 BEFORE any economics
Family: `open_imbalance_v1` (sibling of moc_imbalance_v1; opening-cross NOII messages are
already owned — hour-9 messages verified in the purchased data).
- Signal: last opening-NOII message at-or-before 09:28:30 ET; same norm_imb formula
  (imbalance_shares × near_price / ADV20$). ACTIVE iff |norm_imb| ≥ threshold ∈ {0.05%, 0.10%}.
- Direction: WITH the imbalance. ENTRY = MOO — fill AT the official opening print (daily bar
  open; fill-ambiguity-free, same logic as the MOC exit). EXIT cells: market-out at 09:45 or
  10:00 ET (+ latency draw, via bbo-1s BBO cross + slip). 2×2 = 4 registered cells.
- Promotion: identical bar to M6 (pooled day-clustered CI lower > 0, ≥100 events, ≥3/5 symbols
  positive). Fill ground-truthing per PROTOCOL v6.1 (open print vs daily bar open).
- Data: owned NOII + bbo-1s (in flight) + daily bars (owned). No further purchases.

## M6-GBM cell — registered 2026-07-17 BEFORE running (unlock condition met: NVDA & TSLA CI>0)
One cell, no variants without new registration.
- Features (all PIT at 15:50:10 ET, from owned NOII + daily bars): norm_imb, side, paired_ratio
  = paired/(paired+|imb|), imbalance growth (norm_imb@15:50 − @15:48 and − @15:46), near−ref
  spread bps, near−far spread bps, near-price drift 15:46→15:50 bps, NOII message count so far,
  log ADV20$, trailing-20d realized vol (daily closes), symbol one-hot. NO calendar features.
- Model: LightGBM regression on event net_bps (DEFAULT_PARAMS), expanding walk-forward,
  6-month test blocks, ≥2y initial train, 1-session embargo.
- Gate rule (fixed a priori): TAKE an event iff predicted net > 0. No threshold tuning.
- Promotion: on the gated taken stream — pooled day-clustered 95% CI lower > 0 AND n_taken ≥ 800
  AND taken events span ≥3 symbols AND ≥4 distinct years (anti-concentration prongs).
- Report-only extra: prediction-weighted sizing view (weight ∝ clip(pred, 0, 10) bps).

## M6-FINAL cell — near-price basis at 15:55:10 — registered 2026-07-17 BEFORE running
THE FAMILY'S LAST EXPERIMENT (moc_imbalance_v1 CLOSES after this, pass or fail).
Justification: the 15:50:10 design was factually mis-specified (NOII near/far prices populate
~15:55); the mechanism's cleanest expression — the auction's OWN indicative clearing price vs
the market — has never been tested.
- Signal at 15:55:10 ET: basis_bps = 1e4 × (near_price − mid)/mid, near from the last NOII
  message at-or-before 15:55:10, mid from the prevailing bbo-1s BBO.
- Cells (en bloc, 3 total): classical |basis| ≥ {5, 10} bps, direction WITH the basis
  (buy iff near > mid); plus ONE GBM cell at 15:55:10 with the now-populated registered
  feature set + basis_bps (same fixed pred>0 gate).
- Entry: taker market at 15:55:10 + latency (bbo-1s cross + slip). Exit: AT the cross.
- Promotion (stiffened per this round's era lesson): pooled day-clustered CI lower > 0 AND
  ≥3/5 symbols positive point estimates AND positive point estimate in ≥4 of the 7 years.
- Ground-truthing per PROTOCOL v6.1. Sessions < holdout only.

## M7 daily cross-sectional reversal — registered 2026-07-17 BEFORE economics
Family: `daily_xs_reversal_v1`. WITHIN the user-approved research-only daily side-ledger scope.
Basis: (a) our own side-ledger found the project's ONLY positive forecast signal (1d pooled IC
+0.037 [+0.007, +0.068], 429 OOS sessions); (b) frontier research: weekly cross-sectional
reversal on LARGE CAPS is the only published days-horizon lane with measured net-of-cost
returns in our forced universe (30-50 bps/wk institutional).
- Universe: the 12-name bar_signal set. Signal at 15:55 ET Friday (weekly cell) and daily cell:
  rank of trailing 5-session return, residualized vs the equal-weight basket return.
- Portfolio: long bottom-3, short top-3, equal weight, enter MOC (official close fill,
  ambiguity-free), exit MOC +5 sessions (weekly) / +1 session (daily). Zero commission +
  SEC/TAF sells; NO borrow charged — a borrow-stress arm (50bps/yr HTB proxy) is mandatory
  in the report.
- Cells (en bloc, 2): daily rebalance, weekly rebalance. Thresholds: none (rank portfolio).
- Promotion: pooled per-rebalance net CI lower > 0 (day-clustered on entry sessions) AND
  positive in ≥4 of 7 years AND survives the borrow-stress arm. Research-only either way —
  deployment would need the overnight constraint amended by the user.
- Data: owned 1-min/daily bars 2019-11→2026-05 (closes). Sessions < holdout.

## M8 meta-labeling on the classical basis rule — registered 2026-07-17 BEFORE running
Family: `moc_meta_v1`. POST-HOLDOUT (seal spent by M6-FINAL) — this cell's OOS evidence is
walk-forward only; forward paper is the sole clean validation. Post-hoc-search risk acknowledged.
- Primary signal (UNCHANGED, classical): |basis|>=10 at 15:55:10, direction = sign(near-mid).
  This defines the candidate trades and their realized net_bps (the M6-FINAL |basis|>=10 events).
- Meta-model: LightGBM BINARY classifier predicting P(net_bps > 0) per candidate. Features
  (reliability signals, NOT re-predicting direction): basis_bps, near_far_bps (indicative
  instability), near_ref_bps, paired_ratio, norm_imb, imb_growth_53, imb_growth_51, msg_count,
  vol20, log_adv20, symbol one-hot. Expanding walk-forward (6-mo blocks, >=2y train, 1-session
  embargo) — identical folds to M6-GBM. OOS predictions for every candidate beyond initial train.
- Gate (registered a priori): TAKE iff P(win) >= q, q in {0.50, 0.55, 0.60}.
- Success (honest, post-holdout): on the OOS taken stream vs the ungated classical baseline on
  the SAME OOS span — (a) hit-rate improves, AND (b) EITHER net_bps mean CI-lower > classical
  mean OR net_bps Sharpe (mean/std) improves >=20% (accuracy = fewer/smaller losers), AND
  (c) holds across >=3 symbols and >=3 years. Report-only: P(win)-proportional sizing overlay.
- Data: owned (M6-FINAL events + NOII features). No purchases. NO holdout (spent).

## M9 auction-evolution features + calibrated sizing — registered 2026-07-17 BEFORE running
Family: `moc_meta_v1` (extends M8). POST-HOLDOUT: walk-forward OOS only; forward paper is the judge.
Legal feature window is STRICTLY [15:50:00, 15:55:10] (decision instant) — the leakage boundary;
a reconstructed basis_at_decision MUST equal the existing snapshot feature (unit-test).
- Cell A — evolution features into the SAME GBDT (the one registered probe): add to the M8
  feature set exactly these path scalars over [15:50, 15:55:10], winsorized 1/99:
  (1) imb_velocity = slope of imb_shares/adv20 over last 90s; (2) imb_accel = last-30s minus
  prior-30s velocity; (3) near_conv_slope = slope of signed_basis (bps/min); (4) near_jitter =
  std of first-diffs of signed_basis; (5) paired_frac_slope = slope of paired_ratio.
  Success: OOS gated stream (P>=0.55) net_bps CI-lower > the M8 snapshot-GBDT gated mean AND
  holds >=3 symbols/3 years. Null (<=) => sequence-modeling thesis killed, documented.
- Cell B — calibrated sizing overlay (report + deploy-lens, NEVER a gate): isotonic-calibrate
  P(win) on each fold's train tail; size weight = clip(P_win_cal * |basis_bps|, 0, cap)
  normalized; report per-notional-unit net and Sharpe vs flat and vs the M8 gate. Compares
  Sharpe(sized) vs Sharpe(flat gated). Deploy-lens only — no promotion claim.
- Data: owned. No purchases. No holdout.

## M11 cross-sectional out-of-sample generalization — registered 2026-07-17 BEFORE download
Family: `moc_imbalance_v1`. The FASTEST clean-ish validation available now: apply the FROZEN rule
to 35 Nasdaq names it was NEVER fit on. Not a search — zero parameter changes.
- FROZEN signal (near-vs-ref variant, verified equivalent: corr 0.9999, 98.5% trigger agreement
  vs the near-vs-mid rule): at 15:55:10 ET, basis_bps = 1e4*(near-ref)/ref from the NOII message
  (ref_price as the mid proxy — NO quote feed needed). |basis|>=10 => trade toward near, exit AT
  the official close (daily bar close, free). Entry: taker at ref +/- half a conservative fixed
  spread proxy (2bps each side, > the ~1bps these liquid names run) + 0.5bp slip. This entry cost
  is CONSERVATIVE vs the bbo-1s taker fill used on the 5 original names.
- Universe (35, NONE in the original 5): AAPL MSFT AMZN META AVGO NFLX ADBE CSCO INTC QCOM INTU
  TXN AMAT MRVL LRCX KLAC PLTR AMGN GILD VRTX REGN ISRG PEP COST SBUX MDLZ TMUS CMCSA HON ADP
  BKNG ABNB PANW CDNS SNPS. Sector-diverse (not just semis): consumer, health, comm, industrial.
- Meta transfer test: apply the M8 meta-model TRAINED ONLY ON THE ORIGINAL 5 NAMES to these 35 —
  does the learned reliability filter generalize to unseen symbols? (retrain forbidden; frozen.)
- Pass (registered): classical pooled net_bps CI-lower > 0 on the 35-name pool (pure OOS) AND
  positive in a MAJORITY of the sectors represented AND >= 500 events. Meta-transfer bonus: does
  gating by the 5-name-trained meta improve the 35-name hit rate?
- Sessions < 2026-06-01 (holdout untouched). Data: NOII only (~$48 credits, quoted). No bbo/no purchases beyond NOII.

## M12 name-selectivity mechanism horse race (LETF flow vs passive weight) — registered 2026-07-17 BEFORE economics (wave-2 synthesis)
Family: `moc_mechanism_v1` (NEW family; ONE charge covers the joint design). Purpose: M11
falsified broad-Nasdaq + vol; this adjudicates the two surviving name-selectivity mechanisms
(DR-X1 / DR-Q1-3 sketches; refuter-verified inputs).
- Cell A (LEAD) — LETF-flow alignment: F_{i,t} = sum_j (L_j^2-L_j) * AUM_{j,t-1} * r_{i, open->15:50};
  single-stock funds weight 1; index LETFs (NDX/semis/SPX complexes) x name index-weight proxy.
  Normalize: F/ADV20 (primary), F/trailing-median cross_size (secondary).
  AUM(t) build: monthly-or-better 2022-2026 from SEC N-PORT bulk + dated public anchors +
  NAV-growth interpolation; provenance file mandatory; kill build if coverage <80% of 2023-26 sessions.
  Tests: (i) name x era rank alignment - top-tercile mean F/ADV names/eras dir >= +3pts vs bottom;
  (ii) event-level - sign-aligned (F, basis) events >= +1.5 bps net AND >= +2pts dir vs anti-aligned,
  n>=250/side; (iii) GOOGL clause - report GOOGL F/ADV vs NVDA same-era; comparable F with dead
  GOOGL = misspecification, reported as such.
- Cell B — PassiveForce: z(passive-share proxy: 13F + N-PORT quarterly) + z(log index-weight proxy:
  archived QQQ/SPY holdings). Same tercile tests. Null field prior documented (B&M absorption;
  ~23% internalization censoring) — kill-oriented.
- Cell C — horse race: event net_bps ~ CellA + CellB + controls (log ADV, spread, vol20);
  rebal/OpEx strata separated via M14 flags. Winner = survives jointly.
- Promotion: winner becomes an M10 forward-book name/event FILTER only; no standalone book;
  holdout spent. Kill: neither variable separates; or <=2-name concentration; or build-coverage fail.
- Data: $0 (owned NOII/bars/events + free SEC bulk + archived holdings + dated public AUM anchors).

## M13 close-factor residualization (Q16 offline) — registered 2026-07-17 BEFORE running
Family: `moc_method_v1` (method/reporting transform; NO promotion family). Gate integrity: the
registered M10 gate is untouched; the residual metric is SECONDARY reporting only.
- Factors (locked; owned-data substitution for unowned QQQ/SMH documented here BEFORE economics):
  F1 = leave-one-out same-session cross-name mean net_bps (>=2 other names; full 2020-2026);
  F2 = NDX proxy: TQQQ 1m return 15:55->16:00 / 3 (subsample 2023-07 -> 2026-07);
  F3 = semis proxy: SOXL 1m return 15:55->16:00 / 3 (same subsample).
- Regressions: event net_bps on side-signed factors; report R^2, residual mean/sd, per-name.
- Adopt as secondary M10 reporting iff R^2 >= 0.20 AND residual mean >= +2.0 bps.
  Kill iff R^2 < 0.10 OR residual mean < +1.0 bps. Between: report only, no adoption.

## M14 calendar-flag diagnostic (Q12 + monthly OpEx) — registered 2026-07-17 BEFORE running
Family: `moc_diagnostic_v1` (diagnostic; UNDERPOWERED-BY-DESIGN for rare cells; NO standalone
promotion — strata reporting that also feeds M12 Cell C).
- Flags (locked): QUAD_WITCH = 3rd Friday of Mar/Jun/Sep/Dec; MONTHLY_OPEX = 3rd Friday of all
  other months; RUSSELL_RECON = last Friday of June, shifted to the prior Friday when day > 28
  (2020-06-26, 2021-06-25, 2022-06-24, 2023-06-23, 2024-06-28, 2025-06-27); MONTH_END = last
  session of the calendar month within the owned session set; COMPOSITE = QUAD_WITCH u RUSSELL_RECON.
- Hypotheses: flagged days differ from ordinary in (a) |basis|>=10 fire rate, (b) signed event
  net_bps / dir. Panels: M6 5-name 2020-2026 near-vs-mid (primary); M11 26-name 2023-2026
  near-vs-ref (secondary).
- Report per-flag n / net / dir + concentration (top-name and top-session share of PnL).
  Kill narrative: flagged <= ordinary, or lift driven by 1 name/session.

## M10 execution annotation — historical entry-shortfall ground truth (registered 2026-07-17 BEFORE running; NO new family — annotates M10)
- On the M6 panel: realized entry shortfall = side*(entry_px - entry_mid)/entry_mid (bps) vs
  contemporaneous half-spread = (entry_ask - entry_bid)/(2*entry_mid). Report median/p75/p90
  by name and year.
- DR-Q4-6 locked kill thresholds: the deploy story dies if median shortfall >= 5 bps or
  p90 >= 10 bps on the liquid names. The same quantiles get appended to every forward-paper
  daily report from M10 session 1 onward.

## M15 positioning layer v1 (SHADOW) — registered 2026-07-18 BEFORE forward session 1
Family: `moc_meta_v1` operational overlay (a derived stream of already-gated events; NO new
signal content, NO new mechanism family). Code: `src/enginev51/positioning.py`, wired into the
M10 harness as a third REPORTED stream. The registered M10 gate is UNTOUCHED and never reads
the portfolio columns.
- SELECTION (frozen): among taken_meta events per session, rank p_win desc (ties |basis| desc,
  symbol asc), keep top MAX_POSITIONS=3 (manual keying bandwidth 15:55:10->15:58).
- SIZING (frozen; M9 Cell B null respected — no p_win-proportional sizing): equal notional at
  DEPLOY_CAPITAL_USD=1200, whole-share floor at entry_px; implementable = shares>=1. Research
  bps stream weights selected events equally (size-agnostic); shares/notional columns measure
  what the $1,000 whole-share account could actually express.
- EDGE-DEATH MONITOR (frozen; reported, gates nothing in shadow): one-sided lower CUSUM on
  daily portfolio mean, S_t = max(0, S_{t-1} + (1.25 - x_t)), ALERT at S > 30. Rationale:
  k = half the +2.5 classical reference (detects decay toward 0); h = 30 gives ~24-session
  minimum path to alert on a fully dead edge vs a multi-hundred-session false-alarm horizon
  at ~12 bps/day noise. Parameters may not be tuned while the shadow runs.
- PROMOTION (only AFTER the M10 gate resolves; adoption = deploy sizing decision, never a
  signal change): (a) portfolio mean >= meta-stream mean - 0.5 bps (selection must not hurt),
  (b) implementable_rate >= 0.80, (c) any CUSUM alert episode forces review before adoption.
- KILL/REDESIGN: portfolio mean < meta mean - 2 bps at n>=100 selected events (p_win ordering
  anti-selects — echoes the engineV5 anti-selection lesson and kills v1), or
  implementable_rate < 0.50 (capital/slot mismatch; informs MAX_POSITIONS or capital, not the
  signal).

### M15 v1.1 amendment — 2026-07-18, PRE-forward-data (registered before forward session 1)
CUSUM h: 30 -> 150 (k unchanged 1.25). Reason: M15-backtest-reference-v1 diagnostic showed v1
h=30 sits BELOW the stationary excursion of S under ~14 bps/day noise (48% of ALIVE 2022-26
history in alert). v1.1 role is narrowed to a catastrophic-death HUMAN-REVIEW tripwire:
~5.2% benign alert time on alive history; dead-edge detection median 69 sessions (20/20).
BINDING FINDING recorded with the amendment: trailing-performance state gating has NO next-day
predictive content on this edge (blocked-day mean +2.5..+3.1 vs calm +3.3..+3.5 across the
parameter grid) — third kill of the trailing-regime idea (engineV5, M4, now portfolio-level).
The tripwire must never become a trading filter without a NEW registration and NEW evidence.
Selection-effect check PASSED (portfolio +3.40 vs meta +3.08 OOS; +18.95 vs +18.00 holdout);
REF_PORTFOLIO_BPS=+3.4 added to the status display (informational only).
Implementability at $1,000: 2026 67.6% / holdout 58.5% — below the 80% promotion bar in the
current price regime; options (fewer slots / more capital / fractional) deferred to adoption
time. Report: research/experiments/M15-positioning/report.md

### M15 v1.2 amendment — 2026-07-18, PRE-forward-data (user decision)
Sizing/implementability capital basis: $1,000 (deploy) -> $10,000 (the research-gate currency,
brief §1 "$10k notional per plan"). All sizing columns and the implementable stat now run at
$10k; the deploy account persists as ONE reported flag column (implementable_deploy @ $1,000)
so the capital-adequacy fact keeps accruing without contaminating research stats. On the $10k
basis historical implementability is 100% (both panels); deploy-lens history unchanged
(85.2% pooled / 67.6% 2026 / 58.5% holdout). Promotion criterion (b) now reads on the research
basis (>=80% @ $10k; a guard for future wider universes); the deploy-lens rate is explicitly
INFORMATIONAL for the separate capital decision at adoption time. Selection, CUSUM, and all
stream statistics are unaffected (sizing capital does not influence selection).

## M16 Phase 0 — live execution-quality audit — registered 2026-07-18 BEFORE any order
Family: cost-model / fill-kernel (NOT alpha; no promotion family). Full protocol:
`research/experiments/M16-phase0/PROTOCOL.md` (frozen). Design per DR-X3: two buckets
(mid-day 13:00-14:30 / last-15 15:45-16:00), market vs marketable-limit contrast (X3 C8),
>=250 clips $400-800, <=$800 exposure, every fill SIP-ground-truthed. Priors: mid-day E/Q
0.55-0.70; last-15 UNKNOWN (stress 0.9-1.5+). Decision rules pre-registered (promote
two-bucket kernel; kill M16 pad if last-15 >= 0.95; bound smallness thesis if mid-day >= 0.95).

## M16 Stage A — GP flow-book method test — registered 2026-07-18 BEFORE economics
Family: `m16_flow_book` (NEW family; ONE registered look; prior LOW and stated).
Per DR-X4: the GP partial-adjustment METHOD applied to NAMED-FLOW aim only — pure intraday
patterns are EXHAUSTED-BY-FIELD (Rosa OOS kill) and hourly stat-arb NOT-VIABLE-STRUCTURAL.
- Universe/panel: 5 core names, hourly panel 2020-2026 from owned bbo1s
  (research/experiments/M16-flow-book/hourly_panel.parquet; clocks 10:00-15:00, 15:30, 15:50).
- Forecast: ret-to-close from each clock; ridge on THREE slow features only:
  z(F_usd/ADV20) [LETF flow, accumulating intraday], MONTH_END, OPEX. Walk-forward by year
  (train <y, predict y). NO price/TOD/momentum features (X4 exclusions binding).
- Control: x_t = (1-theta) x_{t-1} + theta * aim_t, theta=0.25/hr FROZEN; aim = k*yhat/sigma_hour
  scaled so book hourly sd ~15 bps at $10k; no-trade band 0.75*sigma_hour; whole shares;
  max 30 orders/day; FLAT at the 15:50 pass (MOC-exit variant = secondary report only).
- Costs (two-regime per DR-X3, pending Phase 0): mid-day 0.5*quoted*0.65 + 0.3bp;
  15:30/15:50 passes full historical shortfall analog (1.46 bps); sensitivity at E/Q=1.0.
- KILL (pre-registered): pooled net/day <= 0 at n>=250 name-days; OR attribution test fails
  (zeroing F+calendar features leaves >=50% of PnL -> pattern-not-flow, per X4); OR
  required order count > 30/day. Success: net/day CI-lower > 0 AND flow attribution.
- Promotion: forward-SHADOW stage only (a fourth reported stream), never direct deploy.

## M17 cross-sectional + factor momentum (RESEARCH-ONLY side-ledger) — registered 2026-07-19 BEFORE data build and economics
Family: `xsect_factor_momentum_v1` (NEW family; out-of-mission for DEPLOY — overnight holds;
research-only per the daily side-ledger precedent; deployment requires explicit user mission
amendment). Purpose: settle Varma-class slow momentum with receipts instead of assumptions;
frame = POST-PUBLICATION DECAY CHECK on our window (2020-2026), field decades = the prior.

- Cell A — cross-sectional stock momentum:
  Universe: POINT-IN-TIME S&P 500 membership each month from data/external/index_weights_monthly.parquet
  (IVV monthly, 2020-01..2026-06) — kills survivorship by construction; names lacking fetchable
  daily bars are reported as coverage loss, never silently dropped from the denominator.
  Signal (frozen): PRIMARY = 12-1 momentum (cumulative return months t-12..t-2, skip t-1 month);
  SECONDARY (reported, never the verdict) = 6-1. Rebalance: month-end close, equal-weight.
  Portfolios: D10 (top decile) long / D1 short (the classic object) + LONG-ONLY D10 vs
  equal-weight-universe benchmark (the retail-implementable object).
  Costs: 5 bps per side on traded notional (liquid large-caps, generous).
  Window: formation needs 12m -> test 2021-01..2026-06 (~66 months).
  PASS (pre-registered): D10-D1 mean > 0 with plain t >= 2 AND long-only D10 beats EW universe
  by >= 2%/yr net. KILL: t < 1 or either object negative net. Between: report-only.
  Stress reporting: per-year table (2022 momentum regime!), max drawdown, crash months.
- Cell B — factor/sector momentum via tradable ETFs:
  Universe (frozen, 20): XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC (sectors),
  MTUM VLUE QUAL USMV SIZE (styles), IWF IWD IWM QQQ (broad tilts).
  Signal (frozen): PRIMARY = trailing 12-1 total return rank; SECONDARY = 6m rank.
  Hold top-3 equal-weight, monthly rebalance, long-only. Costs 2 bps/side.
  Benchmarks: SPY buy-hold and EW-of-universe.
  PASS: beats EW universe on Sharpe AND annualized excess vs EW >= 2%/yr net over the window.
  KILL: underperforms both benchmarks net. UNDERPOWERED-BY-DESIGN flag: ~66 months.
- No parameter search beyond the two frozen variants per cell; primary variant decides the verdict.
- Data build: Alpaca daily bars (free) for the PIT SPX member union 2019-01..2026-07 (~600-700
  tickers incl. leavers; delisted coverage reported) + the 20 ETFs + SPY. No Databento spend.
- Statistical honesty: charges the family budget (~22 families); n=66 months stated up front;
  "small edge many times" at monthly cadence accrues slowly - this study measures recent
  survival + consistency, not discovery-grade significance.


## M8-v2 — mechanism-informed meta-gate (REGISTERED 2026-07-20, family moc_meta_v1 THIRD look)

Registered BEFORE economics; run EARLY on user instruction 2026-07-20 (supersedes the draft
precondition 'after M10 forward gate'). HARD ADOPTION FENCE: whatever v2 shows, the live
forward streams keep judging frozen M8-v1 until the M10 gate; a v2 PASS is QUEUED for the
adoption decision at gate time; it may not alter forward_paper before then.

- Features (frozen; removal allowed at run time only for data defects, never addition):
  abs_f_over_adv, flow_aligned, complex_intensity, range_pos_1555, month_end, day_vol_ratio —
  exact definitions per M8-v2-FEATURE-DRAFT.md table, all strictly observable at 15:55:10.
  F(t) r-window PINNED = prior official close -> last bbo-1s quote <= 15:55:10 (wave-4 DR-X7
  disclosure-pinned since-prior-close; M12's open->15:50 variant = report-only cross-check).
- Model/eval (frozen): LightGBM binary P(net_bps>0), M8 frozen hyperparameters, NO search;
  identical expanding walk-forward folds (6-mo blocks, >=2y train, 1-session embargo);
  universe = M8 dev universe, dev <= 2026-05-31; holdout untouched. One spec, one look.
  Drop-column ablation report-only.
- Pre-model redundancy diagnostic (inside the one look): corr(abs_f_over_adv, the NOII
  imbalance features already in the M8 frame) on the training span; if > 0.8 -> REDUNDANT,
  automatic KILL (the M9 snapshot-ceiling outcome), model comparison still reported.
- PASS requires ALL, on the identical OOS span: (i) gated hit-rate improvement vs baseline 1
  (M8-v1 P>=0.55 stream); (ii) CI-lower improvement OR >=20% gated-stream Sharpe improvement
  vs baseline 1; (iii) incremental net >= +1.0 bps/event on the gated stream (materiality
  floor); (iv) beats baseline 2 (Occam: the single-feature abs_f_over_adv+flow_aligned
  filter) on gated-stream Sharpe; (v) breadth: improvement holds in >=3 symbols and >=3
  calendar years. KILL: any of (i)-(v) fails -> M8-v1 stands; F/ADV stays report-only.
- Charges: moc_meta_v1 third look (raised bar embodied in the ALL-of conjunction + floor).
  Data $0 (owned). Build per standing delegation rule; orchestrator executes the one look and owns
  the verdict.


## M20 — scheduled-macro-window mid-alpha atlas — registered 2026-07-22 BEFORE any conditional mean exists

Family: `sched_window_v1` (NEW). Program context: explicit user directive 2026-07-22 — research
the non-LETF continuous-intraday space (minutes–hours holds, forecast-then-size, no speed
competition) and keep searching under protocol. This registration is STAGE 1: a conditional
MID-ALPHA SCREEN (mid-to-mid, no fills, no replay, explicitly NOT economics). Its sole output
is which cells, if any, carry conditional mid-alpha >= 2x the taker cost floor. Stage 2
(plan-level economics via the replayer, sizing from registered expectation) requires a SEPARATE
registration citing this section and may cover at most the 2 best surviving cells. Two-stage
structure = M18-corollary compliance: demonstrated conditional mid-alpha BEFORE any
conditioning/execution family.

Scope vs standing kills (pre-stated for the fresh-eyes reviewer):
- NOT "event-day intraday taker" (frontier 07-16 scope = single-name catalyst/earnings days;
  this family = MARKET-WIDE scheduled macro releases; anchor sets disjoint).
- NOT DR-X4 pattern harvest (no TOD/seasonality/first->last-HH cell; anchors are exogenous
  release instants, not clock patterns).
- NOT hourly stat-arb / bar-tier IC re-skin (no cross-sectional residual, no bar features,
  no learned forecast; the conditioning variable is the post-release reaction sign — an
  information set no prior family used).
- Adjacency disclosed: gap_mr (dead, M3/M5) = unconditional overnight-gap FADE at bar tier.
  Cell class A5 here = macro-release-day-only morning CONTINUATION from the open. Different
  anchor set, opposite hypothesis class, disjoint conditioning. A5 inherits no gap_mr variant.
- Survivor profile 3/5: scheduled instant YES; owned-data $0 YES; named payer YES-provisional;
  single-print NO (taker-priced evidence per brief gate 5 — no maker assumptions anywhere);
  effect >= 2x cost UNKNOWN (that is the screen's question). Extraordinary-reason clause
  engaged: user directive above.

Mechanism (named before results): post-release repositioning by institutions constrained to
react to scheduled macro information slowly — (i) mandate-constrained rebalancers digesting
macro state changes over minutes-to-hours (macro-announcement drift / underreaction
literature), (ii) vol-target / risk-parity re-levering after scheduled-uncertainty resolution
(mechanical, price-insensitive, executed gradually by design). Payer prong is PROVISIONAL:
wave-5 lane DR-X9 (research/deep/WAVE5_PLAN.md) must return its prior-art/decay verdict
BEFORE any Stage-2 registration; Stage 2 without that verdict is a protocol violation.

Anchors: `data/external/macro_calendar.parquet` (scripts/build_macro_calendar.py; provenance
from authoritative schedule sources; QA gates in tests — counts/yr, RTH placement, trading-day
join, no dupes). Classes (5, en bloc):
- A1 `fomc_stmt` — FOMC statement, anchor 14:00:00 ET (~8/yr)
- A2 `fomc_minutes` — FOMC minutes, anchor 14:00:00 ET (~8/yr)
- A3 `cluster_1000` — 10:00:00 ET releases pooled: ISM Mfg, ISM Services, UMich prelim+final,
  JOLTS, CB Consumer Confidence. Class verdict is pooled; per-subtype rows reported, never
  the verdict.
- A4 `tsy_auction_1300` — 10y and 30y auction RESULTS, anchor 13:02:00 ET
- A5 `pre_open_0830` — CPI, NFP, PPI, Retail Sales, GDP-advance (8:30 releases), anchor
  09:30:00 ET (the open embeds the futures reaction; A5 tests macro-day morning drift).
Names: NVDA TSLA AMD MU GOOGL. Price object: owned XNAS bbo-1s mid, completed-bucket
convention (events/context.quote_at semantics; landmines L4/L9 acknowledged — all-XNAS
internally consistent, never pooled with SIP).

Frozen measurement (per event x name):
- W_react = 5 min from anchor. reaction = mid(anchor+W)/mid(anchor) − 1.
- decision_ts = anchor + W + 25 s (p-max manual latency). entry_mid = last completed 1s
  bucket <= decision_ts, staleness <= 5 s else the event-name row is DROPPED WITH REASON
  (dropped rows reported; never silently).
- Horizons H in {30m, 60m, 120m, TO-1545} measured from decision_ts; exit_mid at
  min(decision_ts + H, 15:45:00 ET), same staleness rule. Nothing at or after 15:45 ever
  (champion territory + close-flow contamination). Early-close sessions: drop events whose
  decision_ts >= close − 30 min (reported).
- Hypothesis, every cell: CONTINUATION. signed_ret_bps = sign(reaction) x
  (exit_mid/entry_mid − 1) x 1e4. reaction == 0 -> dropped (reported).
- Condition forms (2): C1 sign-only (all events). C2 magnitude-gated:
  |reaction| >= expanding PAST-ONLY median of |reaction| within (class, name), min 10 prior
  events else excluded from C2 (PIT quantile by construction).
- Cell grid = 5 classes x 4 horizons x 2 forms = 40 cells, registered en bloc. Every cell is
  a counted variant. No cell additions, removals, or definitional motion after the first
  real-data run — a changed cell is a NEW family.

Cost floor (computed then FROZEN before any conditional mean exists; ordering enforced in
code and by test): RT_floor(class, name) = median quoted spread in bps over TRAIN inside
[decision_ts − 60 s, decision_ts + 60 s] + 1.0 bps (taker slip, 0.5 x 2 legs, COST_MODEL v1)
+ 0.25 bps (SEC 0.206 sell-side + TAF/CAT at the $10k research clip). The harness writes
`research/experiments/M20-sched-window/cost_floors.json` FIRST and only then computes any
return. Class-level floor for the bar = median across the 5 names.

Splits and looks:
- TRAIN = sessions <= 2026-02-28 (dev). VALIDATE = 2026-03-01..2026-05-31, ONE look,
  computed ONLY for cells that SCREEN-PASS on TRAIN (enforced by stored pass-list; the CLI
  refuses --include-validate without it). HOLDOUT stripped by apply_seal in the assembly
  path (mandatory choke point). Forward sessions (>= 2026-07-17) untouched by this family.
- ONE TRAIN pass total, executed by the orchestrator after tests are green. Re-runs only for
  code-defect fixes, each with a ledger note; never threshold motion.

A-priori bars (pooled across names, day-clustered by ET session):
- SCREEN-PASS (TRAIN): mean signed_ret_bps >= 2 x RT_floor(class) AND day-clustered 95%
  CI-lower > 0 AND N >= 150 event-name rows across >= 40 distinct sessions. Cells below the
  N/sessions floor report UNDERPOWERED-BY-DESIGN and cannot pass.
- VALIDATE confirm (for TRAIN passers): same sign AND day-clustered 95% CI does not sit
  entirely below zero. Cells with VALIDATE N < 30 carry VALIDATE-UNDERPOWERED (structural:
  ~8 FOMC events/yr) — such cells may still proceed to Stage-2 REGISTRATION, but Stage-2
  ECONOMIC promotion then requires the forward-shadow stream, never TRAIN alone.
- FAMILY KILL: zero cells SCREEN-PASS on TRAIN -> obituary + coverage note (cells x bars x
  N), no grid extension, no threshold motion, family closed. Kill is final per protocol.
- Multiple-testing: the family charges 40 variants en bloc; inherited debt per
  protocol.INHERITED_TRIAL_FAMILIES; any Stage-2 DSR runs at honest counts including this
  atlas.

Sizing pre-commitment (Stage-2 form, per user directive "size by expectation"): plan size
proportional to clip(E_hat[cell]/RT_floor, 0, 2) x $10k research clip. The FORM is registered
now; constants freeze at Stage-2 registration from published atlas numbers only (sequential
registration; no unpublished peeking).

Ops: $0 data. Harness = src/enginev51/research_screens/sched_window.py +
apps/run_sched_window_atlas.py + tests (PIT poison-quote guard, seal guard, staleness-drop,
floor-before-means ordering, clustered-CI correctness on synthetic clusters, validate-gate
refusal). Builds delegated (calendar: mechanical agent; harness: complex agent) per the
standing rule; orchestrator audits diffs, executes the one TRAIN look, owns the verdict. All
timestamps UTC ns in data, ET wall-clock anchors converted via America/New_York.


## M22 — earnings-day closing crosses (Q13) — registered 2026-07-23 BEFORE any economics exist

Family: `earnings_close_v1` (NEW). Program context: standing user directive (2026-07-22/23:
keep opening mechanism-backed families; goal = a SECOND independent stream — breadth-first
under the multi-signal doctrine of 2026-07-20). This is the one catalyst × auction
intersection never tested (OPEN_QUESTIONS Q13; EXHAUSTION_MAP row OPEN-TESTABLE, unblocked
by the DR-X2 recipe + the M21 SEC-stamped calendar).

Scope vs standing kills (pre-stated for the fresh-eyes reviewer):
- NOT event-day intraday taker (frontier 07-16 kill): the decision instant is the frozen
  15:55:10 auction snapshot and execution is the single-print closing cross. No intraday path.
- NOT an M11 re-run: M11 killed the UNCONDITIONED broad-name rule on ordinary days
  (net −3.0 bps, dir 0.470). M22 Cell B tests the catalyst-conditioned subset (day0 closes
  only) — an information set M11 never conditioned on. M11's kill stands regardless of outcome.
- NOT the banned M21 descendant: M21's fenced descendant = daily-horizon (1–5 d)
  earnings-reaction trading (out-of-mission, needs mission amendment). M22 trades the day0
  CLOSING CROSS — RTH, flat at 16:00, the live auction regime, squarely in-mission. M21
  artifacts enter as CALENDAR DATA ONLY (event_id, symbol, day0_session, timing); no M21
  regime/crowding feature enters any gate or bar.
- NOT M14 (its strata were month-end/rebalance days on champion names; earnings day0 was
  not a stratum there).
- Survivor profile 5/5: single-print YES; scheduled instant YES (SEC acceptance-stamped
  calendar + fixed 15:55:10); named payer YES (below); testable cheaply YES ($0, all owned);
  effect ≥ 2× cost = the question this family asks.

Mechanism / named payer (before results): LETF issuers MUST trade ΔExposure = (L²−L)·AUM·r
at the close (M12 family winner; Cell C flow beta +0.510 bps/sd surviving ADV/weight/panel
controls). day0 |r| is typically the largest daily return a name prints all year → mechanically
the largest forced F of the year, on a date scheduled months ahead. Secondary unconditional
payer: passive/index MOC flow (DR-Q1-3). Ex-ante prediction: the basis edge AMPLIFIES on day0
closes, concentrated in names/eras where single-stock LETF complexes exist (Cell C prong).

Event set: `research/experiments/M21-earnings-regime/events.parquet` (SEC 8-K/6-K acceptance
stamps, ET-verified, 20/20 IR cross-validation banked by M21). Include every event with
day0_session ≤ 2026-05-31 AND NOII coverage at day0: 342 events total — champion-5 = 128
(coverage 2020-01→), broad-12 = 214. M21 `status` flags are irrelevant here (they concern the
d1_20 forward window; M22's outcome completes at the day0 cross itself) — pre-stated so
including `outcome_crosses_seal` rows is not motion. Calendar max day0 = 2026-05-28 →
holdout structurally untouchable; `assert_before_holdout` still enforced in code.

Cells (en bloc; 2 gated + 1 report-only):
- **Cell A — AMPLIFICATION**, champion 5 (NVDA TSLA AMD MU GOOGL), 2020-01..2026-05-31,
  day0 sessions only. The frozen champion rule VERBATIM: basis = near/mid − 1 at 15:55:10
  (bbo1s completed-bucket mid), |basis| ≥ 10 bps → taker WITH the basis, exit at the 16:00
  cross via `backtest/auction_replay` (conventions untouched; COST_MODEL v1 fees). Baseline
  row (report-only, produced by the SAME run/pipeline): identical rule on all non-day0
  sessions, same names and window.
- **Cell B — CATALYST REVIVAL**, broad 12 (AAPL AVGO MSFT QCOM from 2020-01; AMAT INTC KLAC
  LRCX META MRVL NFLX TXN from 2023-01), day0 sessions only. The M11 apparatus VERBATIM:
  basis_ref = (near/ref − 1)×1e4 from the same last NOII message with near>0 AND ref>0 at or
  before 15:55:10; |basis_ref| ≥ 10; conservative fixed taker entry 2.5 bps off ref; exit at
  the day0 raw bars1d close print; M11 fee conventions. Evidence class: proxy-priced /
  conservative-cost (the ledgered ~2.3 directional-point ref-proxy handicap acknowledged) —
  NEVER pooled with Cell A numbers (L9-class separation, enforced by test).
- **Cell C — MECHANISM PRONG** (report-only, no bar): day0 events stratified by single-stock
  complex presence and |F|/ADV tercile (AUM anchors on public_date — L5). Prediction:
  amplification concentrates in complex names. No promotion consequence; feeds the
  F/ADV-forward-filter / M8-v2 path only.

Looks and splits: ONE pooled look over TRAIN+VALIDATE (≤ 2026-05-31); per-era rows
(2020-22 / 2023-26) and per-name rows reported, never gated. Rationale (pre-stated):
quarterly event cadence makes any 3-month confirm window ~zero-power — the M20 lesson;
confirmation authority is assigned FORWARD. A PASS's only consequence is a Stage-2
forward-judged registration (M20F pattern); never direct trading, never a champion change.
Re-runs only for ledgered code-defect fixes; no threshold motion ever.

A-priori bars (95% CI day-clustered by ET session; a session with 2+ reporters = 1 cluster):
- Cell A PASS: n_fired ≥ 50 across ≥ 40 distinct sessions AND CI-lower > 0 AND day0 mean ≥
  2× the same-run non-day0 baseline mean. n_fired < 50 → UNDERPOWERED (can neither pass nor
  count as a kill; reported with the coverage note).
- Cell B PASS: n_fired ≥ 60 AND CI-lower > 0 (any confirmed positive flip against M11's
  unconditioned −3.0 baseline is the finding; the handicap makes this bar conservative).
- BETWEEN THE BARS: point > 0, CI spans 0 → report-only, the look is spent.
- FAMILY KILL: both gated cells fail their bars at adequate power → obituary + coverage
  note; kill final. Multiple-testing: family charges en bloc; variant budget 8 (any motion
  in threshold/timing/exit/universe = a counted variant); DSR at honest inherited counts.

ρ-hypothesis (multi-signal doctrine): Cell A is a CONDITIONER of the existing champion
stream (overlap ρ→1 on shared events; adoption path = calendar/flow feature post-forward-gate,
not a sleeve). Cell B is the breadth candidate: hypothesized realized daily-P&L ρ ≈ 0 vs the
champion book (disjoint names, ~4 day0/yr/name); any adoption must clear S_new > ρ̂·S_book on
realized P&L at its own forward stage.

Fill ground-truthing (v6.1): Cell A ≥ 10 stratified fills vs the raw tape (biggest winners,
biggest losers, entries, cross prints). Cell B (no owned tape): ≥ 10 sampled events
hand-verified — NOII near/ref extraction vs the raw partition, exit close vs an independent
raw daily bar, entry-cost convention asserted in the artifact.


## M23 — dynamic-sizing shadow (probability-scaled allocation) — registered 2026-07-23 pre-data

Family: `sizing_shadow_v1` (M23). Context: user directive 2026-07-23 (dynamic trade/position
management from realtime probability) + the 2026-07-21 recommendation on file. Doctrine
honored: sizing MULTIPLIES edge, it cannot create it (M18); M15 measured the conviction
signal as thin (+0.03 dev lift). Therefore this family is a REPORT-ONLY measurement
instrument riding beside the M10 forward clock — **no gate, no trading consequence, no
promotion rule exists inside this family**. The only adoption path is a NEW registration
after BOTH the M10 forward gate and M16 Phase-0, citing this family's accumulated forward
evidence at a MinTRL-satisfying track length.

Reference standard (ADOPTED here and for all future result reports in this program):
ADIA Lab Research Paper No. 19 — López de Prado, Lipton & Zoonekynd (2026), "How to Use the
Sharpe Ratio" (PDF at repo root). Concretely: (i) SR reported at NATIVE frequency, never
annualized; (ii) PSR under the generalized sampling variance for non-Normal AR(1) returns:
σ²[SR₀] = (1/T)·[ (1+ρ̂)/(1−ρ̂) − ((1+ρ̂+ρ̂²)/(1−ρ̂²))·γ̂₃·SR₀ + ((1+ρ̂²)/(1−ρ̂²))·((γ̂₄−1)/4)·SR₀² ];
(iii) MinTRL at α=0.05 reported next to any significance claim; (iv) multiple-testing context
at honest inherited counts (protocol.INHERITED_TRIAL_FAMILIES + the ~23 in-house families).
The companion PDF (arXiv 2511.12490, "13-Sharpe OOS factor") is filed as an ANTI-PATTERN
reference: survivorship-selected universe interacting with the regime filter, 3 hand-picked
bull-market test years presented as 20-year walk-forward, 0.6 bp costs against 42% daily
turnover, internally inconsistent return arithmetic. No design element is imported from it.

Sizing form (FROZEN; every constant is a counted variant; budget 6):
- p = P(win) from the frozen forward artifact `research/forward/m8_model.txt` (the same
  model the meta stream displays; never retrained or re-calibrated inside this family).
- Tier T(p): p < 0.55 → 0.0 ; 0.55 ≤ p < 0.60 → 1.0 ; p ≥ 0.60 → 1.5.
- Vol-normalization v = clip(σ_med5/σ_i, 0.5, 2.0); σ_i = stdev of RAW close-to-close daily
  returns over the trailing 20 completed sessions ending t−1 (PAST-ONLY; raw bars1d — L2);
  σ_med5 = same-window median across the champion 5.
- Event weight w = T(p)·v, then per-session renormalization so the sized book's gross equals
  the equal-notional classical stream's gross that session — the paired difference isolates
  pure allocation (zero leverage/gross effect by construction).
- Books: $10k research basis (gate-currency conventions). Deploy lens ($1k whole-share)
  report-only, never in any comparison statistic.

Measurement (all report-only):
- Primary object: daily paired P&L difference Δt = sized − equal at matched gross. Report:
  mean, day-clustered CI, native-frequency SR, PSR[SR₀=0] with (γ̂₃, γ̂₄, ρ̂) estimated on Δt,
  MinTRL(α=0.05), and T-to-date. A PSR/MinTRL panel is ALSO computed for the three existing
  M10 display streams — display-only; the registered M10 gate is UNTOUCHED (no gate motion).
- Dev reference: ONE pooled computation on the published dev event stream ≤ 2026-05-31
  (expectation-setting; no bar attached; holdout stripped by the standard guards).
- Forward: recomputed after each banked session as a DERIVED report. The instrument READS
  research/forward/ledger.parquet and NEVER writes it; forward_paper itself is not modified.

Ops: $0 data. Harness: `research_screens/sizing_shadow.py` + `apps/run_sizing_shadow.py`.
Tests: PAST-ONLY vol-window pin; tier/clip constant pins; matched-gross invariant (Δt ≡ 0
when T≡1 and v≡1); read-only guard on the forward ledger; raw-bars pin (L2); holdout guard;
PSR/MinTRL golden tests against the paper's worked example — (μ̂,σ̂,γ̂₃,γ̂₄,ρ̂,T) =
(0.036%, 0.079%, −2.448, 10.164, 0.2, 24) must yield SR*=0.456, σ[SR*]≈0.379, PSR(SR₀=0)≈0.966,
MinTRL(α=.05, SR₀=0)≈19.54 — an exact external validation anchor. Builds delegated
(architect → coder → reviewer); orchestrator audits diffs, runs the dev reference, owns interpretation.

Pre-data clarifications (ruled 2026-07-23 on the architect's ambiguity list; no economics
exist; design doc `research/experiments/M23-sizing-shadow/DESIGN.md`):
- Dev-reference p_win = the leakage-free OOS walk-forward column already published in
  `research/experiments/M8-meta-v1/oos_predictions.parquet` (honesty over object-identity;
  in-sample scoring by the frozen model would be optimistic — the anti-pattern). The panel
  carries a one-line note that the FORWARD path uses the frozen model's stored p_win.
- Vol returns = SIMPLE close-to-close, ddof=1; trailing-20 = 20 returns from 21 prior closes.
- Degenerate session (all events p<0.55 → Σw=0): sized book FALLS BACK TO EQUAL (Δt=0).
  Rationale: participation is the meta-family's measured object; this family measures pure
  allocation. Count of such sessions reported.
- Three-M10-stream PSR/MinTRL display panel: DAILY-aggregated session P&L (ρ̂ well-defined);
  SR₀=0 everywhere in this family; display-only, gate untouched.
- Base universe = classical (`taken_classical`, |basis|≥10, all p); tiers zero out p<0.55
  inside the sized book only.
- CI on Δt: `stress.clustered_mean_ci` by session (degenerates to ordinary bootstrap on the
  one-row-per-session series — intended).
- Coder must add the architect's off-anchor PSR unit case (SR₀≠0, ρ≠0, hand-derived) so a
  bracket(SR₀)/bracket(SR̂) swap cannot pass the golden suite.
- Insufficient vol history (< 21 prior closes → σ undefined): v = 1.0 NEUTRAL and the event
  is counted/reported as a vol-history skip — never the max clip (reviewer M3: a NaN σ had
  mapped to the 2.0 boost, i.e. maximum conviction exactly when we know least; ruled to
  neutral pre-data, before any economics exist).


## M24 — opening-auction dislocation fade (auction sandwich) — registered 2026-07-23 BEFORE any economics exist

Family: `open_auction_fade_v1` (NEW; M24). Context: standing breadth mandate — a second
low-ρ stream is the binding constraint. This exercises the ONE sanctioned remaining look on
the opening cross (EXHAUSTION_MAP: "Opening cross, smarter structure | OPEN-TESTABLE (one
registered look max)"). Q10's open question was whether M6b's failure was the signal or the
structure; this family changes BOTH, in the direction the surviving doctrine points.

Scope vs standing kills (pre-stated for the fresh-eyes reviewer):
- NOT an M6b re-test (family `open_imbalance_v1`, 4 cells, CLOSED): M6b = WITH-imbalance
  drift, signal norm_imb = imbalance_shares×near/ADV20$ at thresholds {0.05%,0.10%}, MOO
  entry, TIMED TAKER exits 09:45/10:00, champion-5. M24 differs on every axis: signal object
  = the auction's own near-vs-ref dislocation (the champion's basis, at the open); direction
  = AGAINST (fade); exit = the CLOSING cross (single print, no intraday taker leg — the leg
  most suspect in M6b's design); universe = the full 33-name NOII lake. M6b's cells stay closed.
- NOT gap_mr (dead M3 family: unconditional overnight close→open GAP fade at bar tier with
  taker legs): M24's conditioning object is the auction-INTERNAL dislocation — indicative
  near vs the CONCURRENT pre-open reference price — not the overnight gap; ref already
  embeds the gap, so basis_open measures where the cross clears relative to the pre-market,
  orthogonal by construction to gap direction. The atlas must report corr(basis_open,
  overnight gap) and gap-sign strata as the fence diagnostic. Execution is two single
  prints, not bar-tier takers.
- NOT the overnight-premium family (out-of-mission): the hold is open→close, RTH only,
  flat at 16:00 by construction — the intraday complement.
- Survivor profile 5/5: single-print execution BOTH legs; scheduled instants (09:30 and
  16:00 crosses, decision frozen at 09:28:30); named payer below; $0 owned data; effect ≥2×
  cost is nearly free to clear (no spread — cost floor is fees only).

Mechanism / named payer (before results): price-insensitive market-on-open flow — retail
attention orders queued overnight (Barber-Odean attention class; Berkman et al.: attention-
driven opening price pressure reverting intraday) and fund/ETF opens — pushes the opening
cross away from the concurrent pre-market price. The dislocation is measured by the
auction's own indicative divergence (near vs ref). We supply liquidity AT the cross against
that flow and unwind at the day's other single print. Production note (PLAYBOOK-class
fill-in, mirrors the champion's exit-leg question): plain MOO/LOO close at 09:28, before
the signal; the against-imbalance side remains reachable via Imbalance-Only orders after
09:28 — IO exists precisely to add liquidity against the published imbalance. Research
economics price both legs AT the official prints; the IO-fill reality is a Phase-0-class
audit item at any Stage-2, never resolved by simulation.

Signal and rule (frozen):
- Decision instant 09:28:30 ET (near/far live from ~09:28:00 across lake vintages —
  scouted 2026-07-23 on 2020/2023/2024 partitions). Last opening-NOII message at-or-before
  09:28:30 with near>0 AND ref>0: basis_open_bps = 1e4·(near−ref)/ref. No message with
  near>0 by then → skip with reason (funnel-reported).
- Side = AGAINST: basis_open > 0 → SELL SHORT at the open cross; < 0 → BUY. Entry = the
  official OPEN print (raw bars1d `open`; the Nasdaq official open IS the cross print —
  M6b convention). Exit = the official CLOSE print same session (raw bars1d `close` — L2
  raw both legs). Fees: sell-side SEC/TAF 0.3 bps once per round trip (M11 convention);
  zero spread/slip both legs by construction.
- Gated cells (en bloc, 2, NESTED and disclosed as such): t25 = |basis_open| ≥ 25 bps;
  t50 = |basis_open| ≥ 50 bps (t50 ⊂ t25).
- Universe: all 33 NOII-covered names (9 from 2020-01, 24 from 2023-01), sessions
  ≤ 2026-05-31, holdout guards enforced in code; coverage funnel-reported. Champion-5 vs
  broad-28 rows REPORTED, never gated.
- Report-only strata (no bars): gap-sign × basis-sign; imbalance-side agreement;
  per-year; per-name-group; corr(basis_open, overnight gap).

Looks and bars: ONE pooled look ≤ 2026-05-31 (per-era rows reported not gated; quarterly
confirm windows are the M20 trap). A-priori bars per cell (95% day-clustered CI, cluster =
ET session): PASS = n_fired ≥ 300 across ≥ 150 sessions AND CI-lower > 0 AND mean net ≥
2 bps (≥ ~4× the fee floor). n_fired < 150 → UNDERPOWERED (neither pass nor kill).
BETWEEN THE BARS = point > 0, CI spans 0 → report-only, look spent. FAMILY KILL = both
cells fail at adequate power → obituary + coverage note; kill final. PASS consequence =
Stage-2 FORWARD-JUDGED registration only (M20F/M22 pattern) — never direct trading.
Variant budget 8; any motion in instant/threshold/direction/exit/universe = counted.
Multiple-testing at honest inherited counts; ADIA No.19 panel (native-frequency SR on the
daily aggregated fired stream, PSR[SR₀=0], MinTRL) reported per the adopted standard.

ρ-hypothesis (multi-signal doctrine): TRUE breadth candidate — different auction, different
hold window, mostly different name-days; hypothesized realized daily-P&L ρ vs the champion
book ≈ 0 (measured and reported at the look). Adoption at any future stage must clear
S_new > ρ̂·S_book on realized P&L.

Ground-truthing (v6.1): ≥ 10 stratified events hand-verified — NOII extraction vs raw
partition, open/close prints vs an independent raw daily bar read, fee convention asserted;
plus tape spot-check of the open print against condition-coded trades where the tape is
owned (5 names, post-2025-09 dates).

Ops: $0. Harness `research_screens/open_fade.py` + `apps/run_m24_open_fade.py`; PSR/MinTRL
helpers IMPORTED from `research_screens.sizing_shadow` (already golden-tested — no
re-implementation). One-look gate hard-anchored to the canonical experiments dir (M22 B1
lesson: no relocatable out-dir, gate-locality test mandatory). orchestrator architects and audits;
coder + adversarial reviewer agents per the amended standing rule; orchestrator executes the one
look and owns the verdict.


## M25 — calendar-flow forward overlay — registered 2026-07-23, FORWARD-JUDGED ONLY

Family: `calendar_overlay_v1` (M25). Motivating prior, DISCLOSED AS SEEN: the M14
diagnostic (family `moc_diagnostic_v1`, 2026-07-17) measured MONTH_END champion events at
+5.55 bps vs ordinary +1.27, QUAD_WITCH distinct fire behavior — on the FULL historical
panel, diagnostically, with no bars. Those numbers are consumed; therefore this family
takes NO historical look of any kind. It freezes the cells now and is judged EXCLUSIVELY
on forward sessions accruing via the M10 clock (the M20F pattern). $0; no data purchases;
no champion-rule motion.

Frozen cells (definitions VERBATIM from the M14 registration, no motion):
- C1 MONTH_END: last owned session of the calendar month.
- C2 QUAD_WITCH: 3rd Friday of Mar/Jun/Sep/Dec.
Flags computed by pure calendar functions; a session is exactly one of {MONTH_END,
QUAD_WITCH, ORDINARY} (a month-end quad-witch — rare — counts QUAD_WITCH; disclosed).
Pre-data clarification (2026-07-23, ruled at first display, before any flagged evaluation
data existed): on the ACCRUING forward ledger, MONTH_END is resolvable only once a
later-month session exists (else the newest session of the current month false-flags as
month-end). Unresolved current-month sessions are PENDING — excluded from every flagged
AND ordinary count until their month closes. QUAD_WITCH is calendar-pure and never pends.
[FAMILY WITHDRAWN 2026-07-23 pre-evaluation — user decision terminating the close-auction
direction. No look was ever spent. Code retained inert.]


## M26 — Treasury-auction-results intraday window — registered 2026-07-23, FORWARD-ONLY

Family: `tsy_results_forward_v1` (M26). The sole surviving DR-X9 class (lane report
2026-07-23: FOMC/8:30/10:00 continuation EXHAUSTED post-refutation and Stage-2-banned per
the WAVE5 pre-commitment; Treasury results = zero prior art either way, refuter-confirmed).
First family of the intraday-only era (user decision 2026-07-23). Disclosed-as-seen: M20
TRAIN glimpsed `tsy_auction_1300` as positive-lean/high-variance, never significant, never
validated — that look is charged; therefore NO historical look of any kind here.

Provisional payer (labeled provisional per protocol precedent): post-auction dealer
inventory / rate-vol re-hedging transmitting into equity risk premia — dealer risk premium
documented bond-side; the equity leg is unstudied (that absence is WHY the class is open).

Frozen design:
- Anchor: per-date FIRST-DISLOCATION timestamp inside [13:00:30, 13:05:00] ET, fallback
  13:02:00 (DR-X9 modality-B soft-anchor correction: Treasury commits to no minute; ±1–2
  min variance documented). Real arm = 10y/30y note/bond auction RESULT dates incl.
  reopenings (TreasuryDirect, M20-calendar-QA-grade verification). Placebo arm = the same
  clock on no-auction sessions.
- Measurement: M20 sched_window kernel conventions verbatim — W_react 5 min, decision
  +25 s, C1 sign-only continuation, horizons {h30, h60}, exits capped at 15:45 ET (no
  close-auction contact anywhere — banned direction), XNAS bbo-1s mid, champion-5 names,
  cost floor per M20's frozen RT_floor construction.
- FORWARD-ONLY accrual from sessions ≥ 2026-07-24 via a daily bbo-1s pull (5 names,
  ~cents/day, within the $30 budget; NOII is NOT pulled — the clock's NOII spend is gone
  with the terminated direction).
- SINGLE evaluation at the first crossing of n ≥ 240 event-names AND ≥ 40 auction dates
  (est. ~2 years; the slow burn is pre-stated). PASS = pooled net-of-floor mean > 0 with
  day-clustered CI-lo > 0 AND the placebo arm consistent with 0. ADIA No.19 panel
  (native SR, PSR, MinTRL) at evaluation. UNDERPOWERED/BETWEEN classes per house vocab.
  Evaluation is one-shot, state-gated, canonical-dir (M22 B1 idiom).
- Variant budget 4. ρ-hypothesis: n/a (no live book exists in the new direction; this
  family IS the first candidate stream).
- Harness: NEW thin module reusing `research_screens.sched_window` measurement kernels;
  the M20F `sched_window_forward` instrument stays PERMANENTLY DARK — its
  pass-list∩registration cell rule (correctly) cannot express a class that never passed
  TRAIN, and widening it would be exactly the post-hoc motion the rule exists to prevent.
orchestrator architects; coder + adversarial reviewer build; the daily pull joins the routine;
the single evaluation is the orchestrator's, ~2 years out.
[2026-07-23 amendment: registration STANDS but harness build DEFERRED by user direction
(event families = side support); forward accrual begins whenever a pull first runs.]


## M27 — every-day gap-day reversion, low-liquidity broad names — registered 2026-07-23 BEFORE data download

Family: `gap_day_reversion_v1` (M27). THE main-goal candidate under the user's redefined
objective (an every-day intraday quant strategy + live stat model; close-auction direction
banned; event windows = side support).

Lineage, disclosed and charged: `gap_mr` (M3) closed UNPROVABLE-at-feasible-N — an
UNCONDITIONAL bar-tier gap fade on the 5 megacaps with taker exits. The new-evidence
trigger reopening this space as a NEW family: M24's reported-not-gated raw structure
(n=1,392, 33 names, 2020–2026): broad names ran −18/−41 bps open→close on up-gap days and
+28/+37 on down-gap days (day-scale gap REVERSION), while the champion-5 showed the
opposite lean (efficient opens). That M24 look is in the family debt. This family tests a
DIFFERENT object: the intraday quote path (entry 09:35, exit 15:45 — no auction print
legs, no close contact) on names with NEWLY PURCHASED quotes.

Universe (exogenous, outcome-blind, mechanism-aligned): the 5 LEAST-liquid of the 12
broad NOII names by median dollar-ADV from owned daily bars — **KLAC, MRVL, LRCX, TXN,
AMAT** (probe 2026-07-23; ranking in ledger). Rationale: the mechanism (attention/fund
MOO flow mispricing opens) predicts reversion concentrates DOWN the liquidity curve.
The 7 remaining broad names and the megacaps are an explicit coverage gap (no quotes).

Data: XNAS bbo-1s, 5 names, 2023-08-01..2026-05-31, quoted $15.70 (user-approved
2026-07-23 against $18 remaining credits; download AFTER this registration, cost-guarded).
Bars: raw bars1d (L2) for prev_close/open. HOLDOUT ≥ 2026-06-01 untouched.

Frozen rule:
- g = open_print/prev_close_raw − 1 (both known by 09:31). Gated cells (en bloc, nested):
  t50 = |g| ≥ 50 bps; t100 = |g| ≥ 100 bps.
- Direction: AGAINST the gap (fade). Decision instant 09:35:00 ET; entry TAKER at the
  prevailing quote (bid for shorts / ask for longs) + latency draw U[5,25]s + slip per
  COST_MODEL; exit TAKER 15:45:00 ET same conventions. Early-close sessions dropped
  (EARLY_CLOSE_DATES). Fees per COST_MODEL v1.
- Cost floor: frozen BEFORE any conditional mean exists (M20 ordering): RT_floor(name) =
  median quoted spread at 09:35 + 15:45 over the sample + 1.0 bps slip + 0.25 bps fees;
  written to cost_floors.json first (enforced by test).
- ONE pooled look over the purchased window (2023-08..2026-05). A-priori bars per cell:
  n_fired ≥ 400 across ≥ 250 sessions AND day-clustered CI-lo > 0 (net) AND mean net ≥
  2× the pooled RT floor AND ≥ 3/5 names with positive point estimates. UNDERPOWERED if
  n_fired < 200. BETWEEN per house vocab (point>0, CI spans 0 → report-only, look spent).
  FAMILY KILL: both cells fail at power. PASS consequence: forward-judged Stage-2
  registration ONLY (daily live accrual, the M20F pattern) — never direct trading.
- LIVE STAT MODEL form (pre-committed for Stage-2, constants frozen then from the
  published atlas only): P(reversion | morning state) via LightGBM/logistic on
  {|g| percentile PAST-ONLY, gap sign, trailing-20 vol, spread state at 09:35}, gating a
  fixed-size plan; plan-level paired EV vs ungated is the only promotion currency.
- Variant budget 8 (any motion in instants/thresholds/exit/universe = counted). ADIA
  No.19 panel at the look. Ground-truthing v6.1: ≥10 fills vs raw quotes. Multiple-testing
  at honest counts incl. the M24 charge.
- Pre-look clarification (2026-07-23, reviewer-prompted, before any economics): a cell with
  200 ≤ n_fired < 400 (or sessions < 250) whose CI-lower > 0 is classed
  UNDERPOWERED-AT-BAR — report-only, can neither PASS nor contribute to a kill (the floors
  are power requirements, not evidence against). The registered classes are therefore
  exhaustive: PASS / BETWEEN / UNDERPOWERED (<200) / UNDERPOWERED-AT-BAR / FAIL (CI-hi<0
  at adequate power).
orchestrator architects and audits; coder + adversarial reviewer build; orchestrator runs the one look
and owns the verdict.

Object: the M10 classical stream's per-event net, split by flag, reported next to the M10
status streams (display/report-only). Judged when the FORWARD flagged sample first reaches
n_flagged ≥ 30 events in a cell (expected ~12-18 months; slow burn is the price of
forward-only honesty — pre-stated, no interim claims):
- Cell PASS: forward flagged mean > forward ordinary mean AND day-clustered CI-lower of
  the flagged-minus-ordinary difference > 0 at that first n ≥ 30 evaluation (ONE evaluation
  per cell; no peeking cadence — the harness refuses evaluation below the floor).
- Consequence of PASS: a calendar boost becomes an ADMISSIBLE feature for the
  post-forward-gate M8-v2/adoption registration — never a standalone trading change.
- FAIL/BETWEEN: the flag stays a display column; family closes at the evaluation.
Variant budget 4 (the two cells + the two bar prongs; any definitional motion = counted).
ρ-hypothesis: pure conditioner of the champion stream (ρ→1; no sleeve claim ever).

Display (immediate, no-look): the live engine and forward reports MAY show the session's
calendar flag as context from day one — a flag is a calendar fact, not a result. ADIA
panel conventions apply at evaluation time. orchestrator architects; coder + adversarial reviewer
build the tiny harness; the single evaluation is the orchestrator's.

Ops: $0 data (all owned). Harness: `apps/run_m22_earnings_close.py`, reusing
`run_basis_trial.basis_pit_features` + `auction_replay` (Cell A) and the M11 extraction path
behind a date-whitelist (Cell B; refactor of run_m11 internals allowed, UNIVERSE_28 and its
conventions untouched). Tests: seal/holdout guard; day0-join correctness (AMC→next-session
mapping spot-checks); threshold pin 10.0; A/B no-pooling guard; cost-convention pins;
baseline-vs-day0 same-pipeline guard. Builds delegated (architect → coder → reviewer agents
per the standing rule); orchestrator audits every diff, executes the one look, owns the verdict.

Pre-data clarifications (ruled 2026-07-23 by the orchestrator on the architect's ambiguity
list, BEFORE any economics exist; design doc `research/experiments/M22-earnings-close/DESIGN.md`):
- CI = `backtest.stress.clustered_mean_ci` (session-bootstrap; the same function the reused
  Cell A/B pipelines already use), cluster key = ET session string.
- "Completed-bucket mid" in the Cell A clause = the champion's audited quote lookup verbatim
  (`fills.prevailing_mid`, last 1s-bucket quote at or before 15:55:10 — the M6-FINAL
  convention that passed holdout and the sim audit). No new quote convention is introduced.
- Baseline row has no minimum-N floor (report-only comparator).
- Cell C consumes the M12 dated AUM anchor series joined on `public_date` (the F3-corrected
  artifact); F per M12 Cell A verbatim: F = Σ(L²−L)·AUM·r with r = open→15:50 day0 return;
  complex membership from the LETF fund registry. Report-only, no bar.
- The 342/128/214 counts are the registration-time inventory; realized counts reconcile via
  the reported funnel (coverage/skip reasons), never a hard assert.
- Cell A latency-draw seed = 7 (the repo reproducibility constant), pinned for the one look.
- Amplification-prong edge case: the "day0 mean ≥ 2× baseline mean" prong BINDS only if
  baseline mean > 0; if baseline mean ≤ 0 the prong is vacuous-ill-defined and Cell A PASS
  reduces to the remaining conditions (n/sessions floors + CI-lower > 0), with the ratio
  reported unGated. Ruled before any number exists.
- Cell C r-window (ruled 2026-07-23 post-build, still pre-data; reviewer M1 ratification):
  r = day0 open→close daily return (raw bars1d) as the pool-wide consistent proxy for
  open→15:50 — the broad-12 have no owned intraday quotes and a mixed-precision pool is
  worse than a uniform proxy; the day0 |r| (5-15%) dwarfs any close-auction endogeneity
  (~bps). Report-only prong, no bar; atlas labels the proxy; `r_by_event` override kept.
