# EXT-ML — external momentum + ML suggestions: verification & doctrine (2026-07-19)

Provenance: two research dumps supplied by the user from an external agent conversation
(slow-momentum production framework; ML-for-momentum pipeline). Verified in-session by the orchestrator
against project receipts + targeted web checks. NOT a HARNESS wave (no refuter agents) —
treat external claims as T2, project receipts as their own tier. User decisions recorded:
M17 stays as-is (no M17-b vol overlay); focus moved to intraday expression + ML pipeline.

## Verification of the dumps' load-bearing claims

| Claim | Verdict | Receipt |
|---|---|---|
| Gu–Kelly–Xiu: nonlinear ML improves CS return prediction; momentum/trend features among top importance | CONFIRMED | [RFS 2020](https://academic.oup.com/rfs/article/33/5/2223/5758276); "ML re-weights momentum rather than replacing it" is a fair reading |
| Poh–Lim–Zohren–Roberts: learning-to-rank ~3× Sharpe on CS momentum | CONFIRMED as published; pre-cost/capacity caution stands | [JFDS 3(2) 2021 / arXiv 2012.07149](https://arxiv.org/abs/2012.07149), [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3751012) |
| Meta-labeling: sound architecture, mixed empirical gains, not free alpha | CONFIRMED — and it is ALREADY LIVE here as M8 (P≥0.55 gate, frozen model, forward stream) | M8 registration + M10 streams |
| "Flashy ML-mom papers overstate live after-cost edge" | CONFIRMED WITH NUMBERS (stronger than the dump knew) | Avramov–Cheng–Metzker, [Management Science 69(5) 2023](https://pubsonline.informs.org/doi/10.1287/mnsc.2022.4449), [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3450322): ex-microcaps −64%, ex-unrated −52%, ex-distressed −77%; turnover-driven costs deteriorate further |
| DM crash mechanics / Barroso vol-management for slow mom | CONFIRMED; matches M17-A's crash months (−15.8%, −12.6%) | `research/experiments/M17-momentum/report.md`; M17-b overlay SKIPPED by user decision 2026-07-19 |
| "Momentum edge = book/state scaling, not per-path breakout calls" | ADOPTED AS DOCTRINE (see below) | Consistent with M12 zero-complex control + DR-X4 |

## Mapping the dumps' six ML layers onto this engine

| Dump layer | Engine surface | Status |
|---|---|---|
| 1 CS ranking / 2 horizon blending | monthly = M17 (research-only, frozen); intraday = bar-tier ML | NO IN-MISSION SURFACE — intraday EXHAUSTED-BY-US (engineV5 IC 0.03–0.05, plan α≈0) |
| 3 meta-labeling (filter/size) | **M8 — already live**; upgrade = M8-v2 post-forward-gate | THE sanctioned "ML addition"; candidate features drafted (`research/experiments/M8-v2-FEATURE-DRAFT.md`) |
| 4 cost/impact models | M16 Phase 0 live E/Q audit + entry-shortfall annotation (5/10 bps thresholds) | in motion; ML only if simple models fail |
| 5 regime/crash probability | trailing-PnL gating 3× DEAD; CUSUM human-review only | ML skin does NOT reopen a dead family |
| 6 path/duration/range prediction | none | DOCTRINE-BANNED |

## Intraday-momentum adjudication (why no new intraday momentum family)

1. Pattern harvest (first→last HH, HKS TOD): EXHAUSTED-BY-FIELD — Rosa 2022 OOS kill
   CONFIRMED by DR-X4 refuters (C3/C4).
2. Bar-feature ML book: EXHAUSTED-BY-US + NOT-VIABLE-STRUCTURAL (DR-X4 D). Flip bars
   unchanged and untouched by the dumps: residual hourly IC ≥ 0.15 AND N_eff ≥ 8 AND
   net ≥ 2× RT cost, simultaneously. GKX-class evidence is monthly/thousands-of-names and
   says nothing about retail-latency intraday IC.
3. Deepest: LPS (DR-X4 C5) — continuation pay accrues overnight; intraday leg skews
   reversal/liquidity-provision. An RTH-only mission is structurally on the wrong side.
4. The surviving intraday door (GP method on named flow) took its one look 2026-07-19:
   M16 Stage A REPORT-ONLY, alive-unproven (+1.69/day, CI spans 0); re-registration only
   after material LETF-era data accrual.

## Doctrine adopted 2026-07-19

1. **No breakout / path / duration-range prediction at any horizon** (dump Tier-3/Layer-6,
   now project law).
2. **No ML re-skins of dead families.** A dead verdict is about the information set and the
   payer, not the estimator; only the registered flip bars reopen a cell.
3. **Momentum enters the program only as conditioning features tied to an identified payer**
   (M8-v2 candidate list), never as a standalone signal family.
4. **Any ML addition must name its payer and survive Avramov-class scrutiny** (who pays, and
   does the edge live outside microcaps/turnover?).

## Artifacts

- `research/experiments/M8-v2-FEATURE-DRAFT.md` (design-time candidate features; no data touched)
- `research/deep/EXHAUSTION_MAP.md` — 4 rows + update-log entry (2026-07-19)
- `research/OPEN_QUESTIONS.md` Q18 — meta-labeling-at-small-n wave charge (M8-v2 design input)
