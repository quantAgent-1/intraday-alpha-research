# EXECUTED 2026-07-28 — registration completed after V-NB PASS (+24.82 [+7.79, +43.31]); ledger row M30-retail-fade-daily-v1 + marker written. Historical record only.

Prepared 2026-07-28 while the quote chain runs, so the post-bridge registration step is a
verbatim paste, not an improvisation. Status markers:

- [x] V-NB bridge PASS (+24.82 [+7.79, +43.31] T=508) (`vnb_result.json`, gate: same sign, mean in [+13.4, +31.3], CI-lo > 0)
- [x] Ledger row appended (M30-retail-fade-daily-v1)
- [x] `registration_marker.json` written
- [ ] `scripts/r2a_oos_run.py` — BLOCKED on OOS data completion (trades 5.5 names + quotes 16 names)

## Ledger row text (paste on V-NB PASS)

kind: registered · trial_id: M30-retail-fade-daily-v1 · family: retail_fade_daily_v1

hypothesis: Prior-session off-exchange odd-lot retail imbalance (quote-signed vs prevailing
NBBO mid) predicts a fade-direction open-print → 15:40–15:45 return, expressed as a DAILY
EQUAL-WEIGHT PORTFOLIO of that session's top-quartile |OLI| fires. The daily-portfolio unit
is primary FROM BIRTH in this family (the discovery event-level gate failed and stays
failed; the daily unit was post-hoc there, which is exactly why this family exists). Payer:
prior-day attention-driven retail whose overnight-queued flow overprices the open
(Brown-class; zero independent replications exist — DR-C — so this program's evidence
stands on its own).

spec: research/experiments/R2A-oos/PREDECLARATION.md + Amendments 2–3 (all frozen before
any OOS return existed). Signal machinery = r2a_prong0.process_symbol VERBATIM; quote
reference = consolidated NBBO (bbo1s_nbbo root); V-NB bridge passed [FILL: numbers].
Historical look = ONE run on the 16 virgin names (r2a_oos_run.py, outcomes
CONFIRMED / REFUTED / NOT-CONFIRMED / PARK-UNDERPOWERED at the pre-fixed thresholds,
measured per-name exit half-spreads + 0.206 bps SEC fee). On CONFIRMED: forward T+1 accrual
on the 26-name panel via scripts/rfd_live.py (born dark; hard-gated on verdict==CONFIRMED +
marker + frozen thresholds; posterior P(edge>0) full+rolling-60, scale-free CUSUM
human-review tripwire, ADIA No.19 panel from the audited M23 kernels). Deploy-lens
expressions (report-only): SOXL sector variant. Sizing stays report-only per M23 doctrine.

why_now: DR-E survivor scan confirms this is the only in-scope post-2020 candidate in the
field; the quote unlock (Alpaca free historical quotes) plus the XNAS→NBBO bridge made the
decisive test runnable at $0.

## marker file content (write on PASS)

{"family": "retail_fade_daily_v1", "registered_at": "[FILL ISO ts]",
 "ledger_row": "M30-retail-fade-daily-v1", "vnb": "PASS"}
