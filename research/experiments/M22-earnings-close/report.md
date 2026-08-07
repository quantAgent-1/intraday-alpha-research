# M22 — earnings-day closing crosses (`earnings_close_v1`) — REPORT

Registered 2026-07-23 pre-data (M3_REGISTRATION.md § M22 + pre-data clarifications).
Single registered look executed 2026-07-23 by the orchestrator, seed 7, window
2020-01-02..2026-05-31, harness commit b900753. Look SPENT (`look_state.json`).
Artifacts: `atlas.md`, `cells.json`, `cell_a_events.parquet`, `cell_b_events.parquet`,
`cell_c_strata.parquet`, `ground_truth_a.parquet`, `ground_truth_b.parquet`.

## VERDICT: BETWEEN THE BARS (both gated cells) — family CLOSED, no Stage-2

Neither gated cell met its registered PASS bar. Both are point-positive with day-clustered
95% CIs spanning zero at adequate registered power (Cell A n=111 ≥ 50 across 104 ≥ 40
sessions; Cell B n=171 ≥ 60). Per the registration this is the BETWEEN THE BARS class:
report-only, the one look is spent, no iteration, no threshold motion. Revival requires a
NEW registration on materially new evidence (realistically: forward-collected earnings-day0
closes after the M10 gate, alongside the already-planned report-only F/ADV filter path).

## Cell A — amplification on champion-5 day0 closes

| stream | n | sessions | mean net bps | 95% CI |
|---|---|---|---|---|
| day0 | 111 | 104 | **+3.70** | [−1.07, +8.30] |
| baseline (non-day0, same run) | 6,087 | 1,587 | +2.46 | [+1.80, +3.15] |

- Amplification ratio 1.51× (prong bound — baseline mean > 0; bar was 2×). CI-lower prong
  also failed. Point estimate is directionally amplified but not provably.
- Baseline reproduction sanity: +2.46 [1.80, 3.15] vs the published champion dev
  +2.483 [1.854, 3.178] — the wrapper reproduced the champion pipeline faithfully.
- Reported-not-gated rows (registration forbids acting on these): era split 2020-22
  −0.60 [−7.98, +5.72] (n=48) vs 2023-26 **+6.98 [+0.52, +13.46]** (n=63); per-name NVDA
  +8.30 / MU +8.16 / AMD +6.03 / TSLA +2.46 / GOOGL −7.63. The LETF-era and name ordering
  (GOOGL = no complex, negative) echo the M12 mechanism, but they are post-hoc strata of a
  cell that failed its bar — diagnostic color only.

## Cell B — catalyst revival on broad-12 day0 closes

| stream | n | sessions | mean net bps | 95% CI |
|---|---|---|---|---|
| day0 fired (|basis_ref| ≥ 10) | 171 | 133 | +0.98 | [−4.36, +8.15] |

- No confirmed revival. The honest decomposition CUTS AGAINST it: 2023-26 era −2.06
  [−5.99, +1.70] (n=140) — the modern era is flat-to-negative; the pooled positive point
  rides on 31 noisy 2020-22 events (AVGO 2020-03-13 +467 bps tail among them).
- Read against M11's unconditioned −3.0: day0 conditioning moves broad names from clearly
  negative toward zero — the catalyst helps, but not to a provable, or even point-positive,
  modern-era edge under the conservative proxy-priced convention.
- Funnel reconciliation (registered inventory 214 in-coverage): 171 fired + 13 zero_basis
  + 30 inactive = 214 exactly; 96 out_of_range + 96 no_noii_partition = pre-window/
  pre-coverage calendar rows, as expected.

## Cell C — mechanism prong (report-only, no bar)

Complex-present & hi-|F|/ADV: **+7.16 bps** (n=59) vs no-complex & lo: +0.70 (n=223).
Strata collapsed to two cells because complex presence and the F-tercile co-move perfectly
in this pool (complexes exist only on the champion semis). Direction as predicted by M12.
r-window used the registered A5' proxy (day0 open→close, raw bars1d), labeled in the atlas.

## Ground-truthing (PROTOCOL v6.1)

- **Cell A, 10 stratified fills vs raw tape artifacts:** entries at/near the decision-time
  NBBO with latency drift consistent with seeded U[5,25]s draws (both `entry_in_nbbo=false`
  rows are March-2020 latency moves; one favorable); `cross_px == bar_close` exactly in
  10/10; nets reconcile with cross-vs-mid minus modeled costs; no physically implausible
  component. Note: the sampler drew from the full fired pool (day0 + baseline) — same
  machinery, already tape-audited under M6-FINAL/sim-audit; acceptable, noted.
- **Cell B, 9 sampled rows + 1 hand-verified (≥10 satisfied):** `entry_cost_bps == 2.5`
  in 10/10; MSFT 2020-01-30 hand-recompute: entry = ref×(1−2.5e-4) exact to the artifact
  digit, net = gross − 0.3 bps sell-side SEC/TAF exact. Day0 mapping spot-checks (AVGO
  2020-03-13, MRVL 2023-03-03, MSFT 2020-01-30 = AMC+1) correct.

## Coverage note (what was and was not tested)

Tested: day0 closing crosses, 17 NOII-covered names, 2020-01..2026-05, the frozen champion
threshold/timing (|basis| ≥ 10 at 15:55:10), champion-fidelity pricing on 5 names and
proxy-priced conservative pricing on 12. NOT tested (open, would need new registrations):
day1 closes (post-earnings drift flow), other thresholds/timings, earnings-day ETF crosses,
reopen auctions on earnings days, day0 conditioning as a feature inside the M8 gate
(that path is already reserved post-forward-gate and needs no new family).

## Process note

Built via architect → coder → adversarial-reviewer agent chain; reviewer REJECT (one-look
gate relocatable via an out-of-spec `--out-dir`) fixed before the look; all rulings
pre-data and ledgered. 16 harness tests; suite 670 green at the look commit.
