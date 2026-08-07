# intraday-research-engine — Research Protocol (v6.0)

Inherits engineV5 `PROTOCOL.md` v5.0 (and through it engineV2's `research_loop/PROTOCOL.md` v1)
verbatim unless amended below. These rules bind every strategy/model claim in this repo.
Violations void results. Enforced in code by `src/enginev51/protocol.py`.

## 1. Data splits (inherited seal — do not re-cut)

| Split | Range | Use |
|---|---|---|
| TRAIN | ≤ 2026-02-28 | model fitting, feature search, anything |
| VALIDATE | 2026-03-01 → 2026-05-31 | walk-forward evaluation, selection |
| **HOLDOUT** | **≥ 2026-06-01, growing forward** | **SEALED. Inherited intact from engineV5 (never consumed there). Research code never touches it. Consumed once, by a single frozen finalist, on user sign-off.** |

- Purging & embargo: every CV fold purged of samples whose label window overlaps the test fold;
  embargo ≥ the longest label horizon (to-close → 1 full session).
- `apply_seal` strips holdout rows; unsealing requires `ENGINEV51_UNSEAL_TOKEN=I_UNDERSTAND_ONE_SHOT`
  and writes a ledger note. One ceremony, ever.
- Every result report includes a last-6-months recency slice.

## 2. Pre-registration & the ledger

- `research/ledger.jsonl` is append-only. Every experiment gets a `registered` row — hypothesis,
  **named payer/mechanism**, feature set, thresholds, promotion rule, trial budget — BEFORE results exist.
- Detector/threshold families register **en bloc** with a-priori parameter values; every variant counts.
- Inherited trial families (in `protocol.INHERITED_TRIAL_FAMILIES`, used in DSR/PBO):
  sub-hour microstructure ~160 (engineV2); bar-tier 30m–4h 33 (engineV5 18 + grok ~15);
  daily-swing 9 (grok E5). New trials append to their family.
- The **daily 1d–5d side-ledger** (user-approved 2026-07-15) is a separate registered family:
  research bookkeeping only — no dashboard, no live, the deployable system never holds overnight.
- ~10 variants per idea, then a 3-line obituary. Banned output: "no profitable strategy exists" —
  write a coverage note instead.

## 3. Simulation & cost realism (amended for plan-level evaluation)

- **The unit of evidence is the complete TradePlan under deployment reality**, evaluated by the
  causal replayer (`backtest/replay.py`): strict event-time; k=2 slots (first-come, ties → higher
  registered EV); manual latency drawn seeded-uniform [5, 25] s **at every leg** (entry, stop,
  target, curfew-flat); last entry 14:30 ET; force-flat 15:50 ET; no position survives the close.
- **Fills:** market = cross prevailing NBBO after latency + 0.5 bp slip. Limit = L1 quote-tape
  trade-through rule with the **L2 strict variant (price strictly through the limit) as the primary**;
  L1-touch reported as the optimistic bound. Unfilled limits cancel/chase only if the plan says so.
  Stops trigger on quotes and fill at the post-latency touch — gap-through honesty (fill can be
  worse than the stop). Targets are passive limits with the mirrored strict rule.
- **Costs (primary, per mission):** zero commission (US promo through 2026-12-31) + NBBO-sampled
  per-symbol spreads from the quote tape (never assumed constant) + SEC/TAF ~0.3 bp on sells.
  **Post-promo/Korean fee-ladder economics MUST appear in every report as a stress annotation**;
  an edge that dies there is labeled PROMO-ONLY in the report (disclosure, not a Stage A gate —
  amendment of V5 §3, per mission's primary cost model).
- **Research book = the gate currency:** $10k fixed notional per plan on the underlying stock,
  **long AND short** (amends V5's long-only rule, per mission). The small-account lens
  (default $1000, whole-share, LETF translation) is report-only; **no deploy-lens metric may
  ever appear in a promotion rule or training objective.**
- Once results exist, only strategies may change. Touching fills/costs/data to improve results
  voids everything after.
- **Fill ground-truthing (v6.1, 2026-07-16):** before any trial's economics are reported, ≥10
  sampled fills (stratified: biggest winners, biggest losers, maker entries, target exits) MUST
  be verified against the raw tape — the prevailing NBBO at each fill instant must be consistent
  with the fill. Any physically implausible decomposition component (e.g. spread capture
  exceeding the quoted spread) must be traced to individual fills before any narrative is
  accepted. Lesson: two expert reviews and 30+ aggregate stress tests missed late-reported
  off-market prints being counted as fills; one hand-checked trade ticket caught it.

## 4. Gates

- **Stage A PASS** (all required, on the k-slot **taken** plan stream, walk-forward OOS):
  1. N ≥ 250 plans across ≥ 150 sessions (power-justified; no verdicts below N=150);
  2. mean net ≥ +10 bps/plan with 95% day-clustered CI > 0;
  3. per-session mean net (flat days included) CI > 0;
  4. survives: top-5 sessions removed ≥ 0; 2× spread stress > 0; 2× latency stress > 0;
  5. ≥ 1 named payer standalone CI > 0 (no unattributable blends);
  6. DSR ≥ 0.95 at honest family counts; confidence calibration within ±10 pp;
  7. fresh-eyes adversarial review (subagent; code+data only) — its kill is final.
  Pass → user sign-off → single holdout ceremony (pre-registered: holdout mean > 0, no session
  tail < −3σ of backtest; confirmation, not discovery). Fail → obituary + coverage note.
- **Stage B forward gate** (pre-registered at M6): ≥ 4 weeks and ≥ 100 forward plans;
  live-vs-backtest expectancy CI overlap; calibration within ±10 pp.
- **GPU promotion gate:** a learned component ships only if it beats the incumbent on **plan-level
  net EV** (paired, identical event windows, day-clustered Δ CI > 0). IC deltas never promote.
  Directional encoder arms run only if a classical payer is alive or A1 > A0. Ablation budget
  ≤ 60 GPU-hours per registered family.

## 5. Standing prohibitions

Inherited: no 30s–15min single-name fades; no exit-redesign on mid-neutral signals; no published
calendar anomalies without a mechanism prong; separability ≠ profitability (net expectancy or it
didn't happen); no synthetic leveraged-ETF prices; signal-only — no code path routes orders.

New in v6:
- No session-decile economics anywhere (non-causal; engineV5 harness debt).
- No forward-collected-only features (e.g. GEX snapshots) in any Stage A gated result.
- No deploy-book metrics in promotion rules or training objectives.
- No NN promotion via IC; plan-level paired EV only.
- Kalman stretch-fade, textbook anchor/overnight factors, TCN-on-bars: closed families.
