# Amendment 3 — V-QS verdict, the XNAS-vs-NBBO finding, and the bridge gate

Written 2026-07-27, after the V-QS fidelity run and **before any OOS return statistic
exists anywhere.** The only numbers seen are the V-QS diagnostics quoted below.

## 1. V-QS verdict: FAILED as declared — cause identified, and it is not the downsampler

`quote_source_fidelity.md` (5 owned name-days):

- **Downsample convention validated**: on the megacaps the Alpaca-derived 1-second series
  reproduces the owned lake essentially exactly (NVDA median Δmid 0.000 bps, 99.99% within
  2 bps; MU 0.000, 99.73%; exit mids 0.000).
- **KLAC fails hard** (median 1.431 bps, only 61.15% within 2 bps, ΔOLI 0.175, exit mid
  2.6 bps), **AMAT marginal** (98.83% vs 99%), TXN passes.
- Diagnosis: the owned `bbo1s` lake is **Databento XNAS — the Nasdaq-venue BBO**, while
  Alpaca serves the **consolidated NBBO**. For tight, Nasdaq-dominant books the two
  coincide; for wide-spread names (KLAC, 30 bps quoted) the venue BBO sits off the NBBO a
  material fraction of the time. The XNAS BBO cannot be reconstructed from NBBO records
  (a venue's quote is invisible whenever it is not the national best), so no downsampling
  convention can close this gap. It is a genuine source difference, now characterized.
- One harness defect of mine, disclosed: the NVDA sample day (2025-10-15) has no trades
  file, so V-QS2 was uncomputable there — sample-selection error, not a source finding.

## 2. The fix (convention-level, outcome-blind)

**The signing reference for everything downstream is the consolidated NBBO mid** — the
canonical Lee–Ready reference, and arguably more correct than a single venue's BBO.
Alpaca-derived quote partitions are written to a **separate root**
`data/raw/bbo1s_nbbo/{SYM}/{YYYY-MM}.parquet` (never touching the owned lake), and runners
point the frozen machinery at that root.

This creates one obligation that MUST be discharged before the OOS test can mean anything:

## 3. V-NB — the bridge gate (pre-declared, runs before registration and before the OOS test)

**Question**: does the discovery result survive the change of quote reference, or was it
partly an artifact of the XNAS venue BBO?

**Procedure**: pull Alpaca NBBO quotes for the **5 discovery semis** (KLAC MRVL LRCX TXN
AMAT — the tier where venue scope matters; the megacaps are shown ≈ identical and their raw
quote volume makes a re-pull disproportionate — disclosed limitation). Rebuild those five
names' R2-A panel rows with `r2a_prong0.process_symbol` **verbatim** (BBO root redirected),
splice with the owned-quote megacap rows, and recompute the discovery **daily equal-weight
portfolio mid** (the +22.36 [+4.28, +40.36] object).

**Gate (fixed now)**: under NBBO signing the discovery daily-portfolio mid must be
(a) same sign, (b) within **±40%** of +22.36 — i.e. in [+13.4, +31.3] — and (c) CI-lo > 0
(seed 7, 2,000 session-bootstrap reps).

- **V-NB PASS** → the reference switch is immaterial; register `retail_fade_daily_v1`
  (ledger row + `registration_marker.json`) and run the decisive OOS test under NBBO.
- **V-NB FAIL** → **the discovery signal is partly a quote-source artifact.** That is a
  major, reportable finding in its own right; the OOS test is cancelled, the 16 virgin
  names stay unconsumed, and the family is not registered. No threshold-softening clause.

## 4. Everything else is unchanged

Universe (16 names), window, daily-portfolio primary, measured-cost convention, outcome
vocabulary (CONFIRMED / REFUTED / NOT-CONFIRMED / PARK-UNDERPOWERED at +6.0), the
single-look rule on the virgin names, and the registration-before-run requirement all
carry over from Amendment 2 verbatim.

## 5. Data plan (chained, free, background)

1. finish OOS trades (running; resumable),
2. semis-5 NBBO quotes (~2.5–5 h — bridge data first),
3. OOS-16 NBBO quotes (~11 h).

All pulls capped < 2026-06-01; the sealed holdout is never fetched.
