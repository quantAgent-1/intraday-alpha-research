# DR-X2 — Earnings-calendar source scout (for Q13)

**Date:** 2026-07-17
**Mode:** Wave-2 light lane (data scout, modality B only per WAVE2_PLAN)
**Agents:** 1 modality (B primary/venue). No refuters (recipe verdict; verification is local/build-time by design).
**Orchestrator synthesis — not delegated**

### Synthesis

Single-lane charge; no dissents to reconcile. B probed candidate sources live and returned a
two-source recipe with a paid fallback and an explicit validation plan. Orchestrator E-probe
(this repo, 2026-07-17): `data.sec.gov` returned **HTTP 403 from this environment** (Databento
egress works, so it is SEC-side bot filtering of this client/IP, not a network fault);
`yfinance` is not installed in the project venv. Neither blocks the verdict — the submissions
API + bulk `submissions.zip` route is documented T1 and B's own live probe succeeded — but the
recipe is **not yet locally reproduced**; re-verify at build time (proper UA, backoff, or the
bulk zip which is a plain HTTPS file download).

### Verdict (orchestrator)

**`OPEN-TESTABLE`** (confidence **HIGH**) — as a data-unblocking recipe, not a trade.

**Recipe (deliverable):**
1. **Primary ($0, T1):** SEC EDGAR Form 8-K **Item 2.02** `acceptanceDateTime` via
   `data.sec.gov/submissions/CIK##########.json` (recent ≤1000 filings) + archived
   `filings.files[]` parts or the nightly bulk `submissions.zip` for heavy filers.
   Session rule (a-priori): accept-time ET < 09:30 → BMO; ≥ 16:00 → AMC; else DURING.
   Multi-2.02 filers (TSLA-class, ~8/yr) need an earnings-vs-other-2.02 filter
   (quarterly cadence + EX-99.1 keyword check). DIY effort honest: 1-2 days.
2. **Bootstrap/fill ($0, T3):** `yfinance get_earnings_dates` — tz-aware ET timestamps,
   session-bucket-correct on B's 13-name probe, history well before 2020. Never overrides
   SEC when both exist and disagree.
3. **Fallback (≤$20):** EODHD Corporate Events Calendar (~$19.99 one month, explicit
   `before_after_market` field) if SEC DIY stalls or coverage < 90%.

**Mandatory validation before any Q13 gate:** 20 stratified name-quarters vs company IR
press-release times; promote source only if date agreement ≥19/20 AND session agreement ≥19/20.

What would flip it: >5% session-bucket disagreement vs IR on the stratified sample, or >15% of
name-quarters lacking a clean Item 2.02 8-K → promote the EODHD fallback to primary.

### Rejected sources (B, probed)

Finnhub free (1-month history), Alpha Vantage (no historical announcement time), FMP free
(timing field premium-gated, unverified), Nasdaq/Zacks web (bot-walled UI, no bulk).

### Claims

Single-modality lane; claims C1-C10 in `modality-B.md` stand as reported (C1-C3 live probes,
C4-C8 T1/T3 doc checks). No refuter pass — the load-bearing claim (SEC acceptance timestamps
separate BMO/AMC correctly) is re-verified by the mandatory 20-sample IR validation step above,
which is stronger than a web refuter for this kind of claim.

### Constraint gates

Gates 1-3, 5-7: **N-A** (data prep, not a trade). Gate 4: **PASS** ($0 primary; ≤$20 fallback).

### Economics

No alpha claim. Unlocks the Q13 earnings-day diagnostic ($0 on owned NOII, 33 names ×
~26 quarters ≈ 850 name-quarters; AMC/BMO distinction protects pre- vs post-gap close
assignment from date poisoning). Champion comparison line unchanged: +2.5 bps/event dev /
+12.5 holdout.

### Next step (user decides)

Build the calendar per recipe → run the 20-sample validation → only then register the Q13
diagnostic (calendar-flag family shared with DR-Q12 flags, per Q12 report's "no new
freestanding family" framing).

### Ledger-note suggestion (user only)

> `DR-X2 2026-07-17: earnings-calendar recipe OPEN-TESTABLE $0 (SEC 8-K Item 2.02 acceptance + yfinance fill, EODHD <=\$20 fallback); 20-sample IR validation mandatory before Q13 use; SEC 403s this box - re-verify at build.`
