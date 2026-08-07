# M12 name-selectivity mechanism horse race — Cell A (single-stock LETF leg) RESULT 2026-07-17

Registered BEFORE economics (ledger `M12-mechanism-horse-race-v1`; spec M3_REGISTRATION.md).
This is the single-stock complex leg only (w=1, exactly as specified). Index-LETF leg (A2)
and PassiveForce (Cell B) + joint horse race (Cell C) remain pending the holdings archive.

Data: `data/external/letf_aum_anchors.csv` (454 dated anchors, 393 T1 N-PORT; era-correct
leverage parsed from as-filed seriesNames; AUM step function strictly t−1, no interpolation).
Panels: M6 5-name 2020-2026 (near-vs-mid) + M11 26-name 2023-2026 (near-vs-ref), pooled;
event-level F written to `cellA_events.parquet` for Cell C.
Documented deviations (decided pre-run): r endpoint = open→15:55:10 mid (not 15:50);
current-leverage fallback where anchors lack as-filed names.

## (ii) Event-level alignment — REGISTERED THRESHOLD: PASS

Aligned = side matches sign(F) (= sign of day return where a complex exists).

| Group | aligned n / net / dir | anti n / net / dir | lift |
|---|---|---|---|
| **F=0 control (no complex)** | 12,760 / −2.29 / 0.414 | 8,468 / −1.91 / 0.428 | **−0.38** |
| T1 low \|F\|/ADV | 847 / −0.48 / 0.466 | 646 / −0.34 / 0.475 | −0.14 |
| T2 mid | 887 / +1.38 / 0.515 | 606 / −0.55 / 0.446 | +1.93 |
| **T3 high** | 903 / **+3.76 / 0.561** | 589 / +0.85 / 0.514 | **+2.91** |
| Registered headline (complex>0 pooled) | 2,637 / +1.60 / 0.515 | 1,841 / −0.03 / 0.478 | **+1.63 bps / +3.7 pts** |

Registered bar: ≥ +1.5 bps AND ≥ +2 pts dir at n≥250/side → **PASS (+1.63 / +3.7, n=2,637/1,841)**.
The decisive structure: the lift is **monotone in intensity and ZERO on the zero-complex
control** — "basis aligned with day return" carries no edge on names without LETF complexes
(−0.38), so the momentum confound is rejected; the effect loads specifically on predicted
LETF-flow intensity.

## (i) Name-year rank alignment — REGISTERED THRESHOLD: PASS

136 name-year cells (≥50 events): TOP intensity tercile dir 0.464 / net −0.71 vs BOTTOM
0.419 / −2.27 → **+4.5 pts (bar: ≥ +3)**. (Levels sit below 0.5 because the pooled panel is
dominated by M11 dead names on the handicapped near-vs-ref proxy; the registered quantity is
the spread.) The top-8 intensity cells are exactly the alive cells: TSLA-2025/26, NVDA-2024/25/26,
**MU-2026 (dir 0.657, net +8.74 — the holdout anomaly, now predicted by an ex-ante variable)**,
AMD-2026.

## (iii) GOOGL clause — no misspecification trigger, one honest flag

GOOGL complex intensity is materially below NVDA/TSLA same-era (2026: 27 vs 56/93 bps-of-ADV;
2025: 11 vs ~50/106), so the clause's misspecification condition (comparable F with dead
GOOGL) does NOT trigger. Honest flag: GOOGL-2026 intensity (27) is no longer trivial (GOU
launched 2025-12) yet dir is 0.373 (n=102) — either the detectability threshold sits around
~35-40 bps-of-ADV, or GOOGL carries an offsetting idiosyncrasy. Cell C controls will address it.

## Caveats (carried into Cell C)

1. Aligned/anti n asymmetry on high-|F| days is mechanical (big |r| days tilt basis
   momentum-directional); the F=0 control shows the tilt alone is worthless, but Cell C
   should still control day-|r|.
2. AUM anchors sparse pre-2025 for small funds; 2026Q2 N-PORT lag bounded by 2026-07-17
   snapshots (self-heals ~2026-08).
3. F(t−1) uses N-PORT-anchored AUM with real-world publication lag; a deploy version would
   use issuer daily files (same-day public).
4. Panels pooled across two basis constructions (near-vs-mid / near-vs-ref).

## Status

Cell A (single-stock leg): **registered thresholds PASSED; mechanism evidence strong**.
NOT yet a family verdict — A2 (index leg), Cell B (PassiveForce), Cell C (joint horse race +
controls) pending the holdings archive build. Promotion path unchanged: winner variable
becomes an M10 forward-book name/event FILTER only.


---

# M12 Cells A2 / B / C — FAMILY VERDICT 2026-07-18

Inputs: PIT index weights (42,046 rows; IVV monthly SPX 78/78, QQQ N-PORT quarterly NDX 27/27,
all QA sums in [0.98,1.02]; FB->META and AMAT crosswalks era-correct). NDX-complex AUM from
the anchors table; NDX intraday via TQQQ/3 (2023-07+). Scope limits decided pre-run: A2 =
NDX complex only (no owned SOX weights / SPX intraday); B = index-weight component
(13F passive-share aggregation not built).

## Cell A2 — index-LETF leg: REJECTED (dilutes)

2023-07+ window, alignment lift: single-stock F = +1.02; F + index leg = +0.08. The index
leg assigns nonzero F to every NDX name daily (n with F!=0: 3.9k -> 18.9k), and index flow
x 5-9% weights is noise vs ADV — it floods the variable with market-sign events the
zero-complex control already proved worthless. F stays SINGLE-STOCK ONLY.

## Cell B — index weight: NULL after confound control

Raw tercile spread (+4.3 pts) is an artifact: weight correlates with panel membership
(M6 names all have NDX weight; many M11 names have zero) and the M11 near-vs-ref handicap.
The top-weight cells are themselves damning: AAPL-2025 (w 8.7%, dir 0.391), MSFT-2025
(8.3%, 0.390) — the HIGHEST-weight names are dead. GOOGL (w 2.7-3.6%) dead at 2-4x MU's
weight while MU-2026 (w 1.9%, top F) runs dir 0.657.

## Cell C — joint horse race (session-block bootstrap, n=25,706 / 1,598 sessions)

| Variable | beta (bps per 1 sd) | 95% CI | Verdict |
|---|---|---|---|
| flow: sign x sqrt(F/ADV), single-stock | **+0.510** | [+0.093, +0.883] | **SURVIVES** |
| ln(1+w_ndx) | +0.065 | [-0.316, +0.442] | null |
| ln ADV (control) | +0.771 | [+0.277, +1.245] | survives (control) |
| panel/method dummy (M6) | +3.457 | [+2.594, +4.258] | survives (confound, absorbed) |

Without the panel dummy the weight coefficient is spuriously NEGATIVE (-0.756) — the
confound check mattered.

## Family verdict (registered horse race)

**WINNER: single-stock LETF rebalance flow.** It passed Cell A's registered bars with a
21k-event zero-complex control, predicted MU-2026 ex-ante, and survives the joint
specification with panel/ADV/weight controls. **PassiveForce (index weight) is NULL** —
the wave-2 field prior (absorption + internalization censoring) confirmed in our own data;
the 13F passive-share variant is NOT pursued (prior now very low; would need fresh
justification). Index-LETF leg rejected.

Promotion path per registration: F/ADV (single-stock, t-1 AUM step) becomes the forward
name/event FILTER candidate — reported alongside the M10 streams; trading adoption only
via an M8-v2 registration after the forward gate resolves.

Caveats carried: AUM(t-1) uses N-PORT publication-lagged anchors (deploy version = issuer
daily files); 2026H2 anchors refresh ~2026-08 (MUU N-PORT); GOOGL-2026 residual flag from
Cell A stands (intensity nontrivial, dir 0.373, n=102).
