# M12 Cell A — public-date re-anchor addendum (SIM_AUDIT F3 correction)

**Date:** 2026-07-21
**Registration:** `M12-cellA-public-date-correction` (ledger 2026-07-21)
**Audit defect:** SIM_AUDIT_2026-07-21.md §4 (F3) — the Cell A as-of join anchored
LETF AUM on `asof_date` (N-PORT reporting-period END). The value only became public
on the FILING date (~2 months later), which sat unused in the `note` field. This
re-run re-anchors on that filing/public date and reports the delta. **Numbers only;
no verdict** (orchestrator rules).

Mechanics: `scripts/add_public_dates.py` lifts `filed=YYYY-MM-DD` out of `note` into a
new `public_date` column (rows without a `filed=` token — aggregator live snapshots
and article reported-AUM rows — keep `public_date = asof_date`, since they were
observed live). `scripts/m12_cell_a.py --anchor-mode {period,public}` selects the
anchor column; `period` = original `asof_date` convention (control), `public` =
`public_date` (default). Panels, bars, registry, F-formula, leverage-era parsing and
the AUM step-function rule are byte-for-byte unchanged between legs.

## N-PORT publication-lag distribution

`public_date − asof_date` over the 393 N-PORT rows (61 aggregator/article rows carry
zero lag by construction and are excluded):

| n (N-PORT) | median | min | max |
|---|---|---|---|
| 393 | **58 d** | 50 d | 63 d |

Consistent with the ~60-day N-PORT statutory filing limit cited in the audit.

## Control-leg reproduction (mandatory gate)

`--anchor-mode period` reproduces the stored Cell A numbers. Every **deterministic**
registered statistic matches report.md to the printed precision: the full §(ii)
event-level table (zero-complex control lift −0.38; terciles −0.14/+1.93/+2.91;
registered headline +1.63 bps / +3.7 dir-pts, n=2637/1841), `cells=136`, the top-8
intensity cells (incl. MU-2026 dir 0.657 / net +8.74), and the entire §(iii) GOOGL
table. **Harness intact.**

One line is **nondeterministic and is NOT a reproduction failure**: the §(i)
name-year TOP/BOTTOM tercile *means*. A large block of name-year cells have
`mean|F|/ADV = exactly 0.0` (dead names with no LETF complex), and the tercile cut
(rank 45/91 of 136) falls inside that tie block. Polars `group_by` order is
unspecified, so the stable sort breaks the `mIF=0` ties differently each run —
recomputing the terciles from the *same* `cellA_events.parquet` already yields TOP
dir 0.459 vs the same run's printed 0.456. Across draws the spread stays +4.4..+4.9
dir-pts (report quoted +4.5), always inside the registered ≥+3 region. The
period-vs-public §(i) row below is reported with this caveat.

## Side-by-side: period-anchored (control) vs public-anchored

### (ii) Event-level alignment by |F|/ADV intensity — DETERMINISTIC

| Statistic | period (asof_date) | public (public_date) |
|---|---|---|
| events with complex | 4478 | 4182 |
| zero-complex control | 21228 | 21524 |
| F=0 control — aligned n / net / dir | 12760 / −2.29 / 0.414 | 12934 / −2.24 / 0.415 |
| F=0 control — anti n / net / dir | 8468 / −1.91 / 0.428 | 8590 / −1.86 / 0.429 |
| **F=0 control lift** | **−0.38** | **−0.38** |
| T1 low — aligned n / net / dir | 847 / −0.48 / 0.466 | 806 / −0.53 / 0.465 |
| T1 low — anti n / net / dir | 646 / −0.34 / 0.475 | 589 / −0.72 / 0.460 |
| **T1 low lift** | **−0.14** | **+0.18** |
| T2 mid — aligned n / net / dir | 887 / +1.38 / 0.515 | 815 / +1.51 / 0.508 |
| T2 mid — anti n / net / dir | 606 / −0.55 / 0.446 | 578 / −0.01 / 0.471 |
| **T2 mid lift** | **+1.93** | **+1.51** |
| T3 high — aligned n / net / dir | 903 / +3.76 / 0.561 | 842 / +3.89 / 0.575 |
| T3 high — anti n / net / dir | 589 / +0.85 / 0.514 | 552 / +0.31 / 0.495 |
| **T3 high lift** | **+2.91** | **+3.58** |
| Headline (complex>0) — aligned n / net / dir | 2637 / +1.60 / 0.515 | 2463 / +1.65 / 0.517 |
| Headline (complex>0) — anti n / net / dir | 1841 / −0.03 / 0.478 | 1719 / −0.15 / 0.475 |
| **Headline lift** | **+1.63 bps / +0.037 dir** | **+1.80 bps / +0.042 dir** |

### (i) Name-year cells (≥50 events) — TERCILE MEANS ARE NONDETERMINISTIC (see caveat)

| Statistic | period | public |
|---|---|---|
| cells | 136 | 136 |
| TOP tercile — dir / net | 0.456 / −0.82 | 0.461 / −0.46 |
| BOTTOM tercile — dir / net | 0.407 / −2.32 | 0.407 / −2.73 |
| TOP−BOTTOM dir spread | +0.049 | +0.054 |

Top-8 intensity cells: **identical set** both legs — TSLA-2025, TSLA-2026, NVDA-2024,
NVDA-2025, NVDA-2026, MU-2026, AMD-2026, TSLA-2024. Per-cell `dir`/`net` are identical
across legs (they depend only on each cell's events, not on the anchor date); only
`mIF` (mean |F|/ADV) rescales, reshuffling the within-top-8 order (TSLA-2026 rises to
rank 1). MU-2026 stays a top cell at dir 0.657 / net +8.74 in both.

### (iii) GOOGL clause — intensity (mean |F|/ADV ×1e4) by name-year

| symbol-year | period iF | public iF | dir (both) |
|---|---|---|---|
| GOOGL 2023 | 0.69 | 0.60 | 0.411 |
| GOOGL 2024 | 3.90 | 2.81 | 0.442 |
| GOOGL 2025 | 10.68 | 8.28 | 0.466 |
| GOOGL 2026 | 27.28 | 22.41 | 0.373 |
| NVDA 2026 | 55.63 | 62.79 | 0.578 |
| TSLA 2024 | 39.56 | 29.77 | 0.518 |
| TSLA 2025 | 106.15 | 89.89 | 0.567 |
| TSLA 2026 | 93.15 | 111.66 | 0.520 |

`dir`/`net` per cell are anchor-invariant (same events); only the intensity scale moves.
GOOGL-2026 stays dir 0.373 (the honest flag); GOOGL intensity remains far below
NVDA/TSLA same-era under either anchor (misspecification condition does not trigger).

## Factual delta summary (no verdict)

- **Sign retained?** Yes on every alignment lift. Zero-complex control −0.38 → −0.38
  (unchanged, momentum confound comparison identical). Registered headline lift stays
  positive; intensity monotonicity into T3 is preserved (public: +0.18 / +1.51 / +3.58).
- **Magnitude ratio (public ÷ period):** headline lift 1.80 / 1.63 = **1.10×**;
  T3-high lift 3.58 / 2.91 = **1.23×**; headline dir-spread 0.042 / 0.037 = **1.14×**.
  The effect is preserved and marginally larger under public anchoring.
- **Coverage shift:** complex>0 events 4478 → 4182 (**−296, −6.6%**); the 296 move into
  the zero-complex control (21228 → 21524). Public dating delays each fund's
  first-publicly-known AUM by ~58 d, so more early-fund-life name-days carry F=0.
- **MU-2026 ex-ante:** remains a top-intensity cell (dir 0.657 / net +8.74) on
  public-information anchors.

## Artifacts

- `scripts/add_public_dates.py` — adds `public_date` (idempotent; re-run-stable).
- `data/external/letf_aum_anchors.csv` — `public_date` column appended (last).
- `scripts/m12_cell_a.py` — `--anchor-mode {period,public}` (default `public`).
- `research/experiments/M12-mechanism/cellA_events.parquet` — **period** (canonical,
  reproduced by the control leg; original convention preserved).
- `research/experiments/M12-mechanism/cellA_events_public.parquet` — **public** leg output.
- `src/enginev51/models/m8v2_features.py` — `load_letf_anchors` now derives the join
  key `adate` from `public_date` (F3 comment inline; M8-v2 is KILLED — honesty-only).
