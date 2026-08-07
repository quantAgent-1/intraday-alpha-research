# M3-A0-v1.2-raw-correction — raw-bars re-run (orchestrator report, 2026-07-21)

Registration: `M3-A0-v1.2-raw-correction` (ledger, 2026-07-21; frozen decision rules).
Executor: one Opus agent (fetch + gate + re-runs); ruling by the orchestrator per the
registered rules. Per-trial artifacts written by `run_trial` itself sit under
`v1.1/`, `4sym/`, `ext2024-MU/` in this directory.

## 1. Lake correction (permanent asset)

`scripts/refetch_bars1m_raw.py`: raw SIP 1-min bars, NVDA/TSLA/AMD/MU/GOOGL,
2024-01-01 → 2026-06-01 (excl), 145 monthly partitions, 2,465,240 rows, written to
`data/raw/sip/bars1m/{SYM}/` (primary lake; store.py primary-first shadowing now
resolves signal-symbol bars RAW). Holdout (≥2026-06-01) untouched.

**Acceptance gate — PASS on all 16 probes** (per-minute bar-VWAP ÷ tape-VWAP, median
across RTH; the measurement reproduced the audit's OLD offsets to the digit before
the swap, self-validating the method):

| symbol | old offsets (audit) | new (raw lake) |
|---|---|---|
| NVDA | −12.74 / −12.16 / −11.64 bps | ≤ +0.032 |
| GOOGL | −19.52 / −13.01 / −5.98 | ≤ ±0.014 |
| MU | −9.76 / −5.75 / −1.51; 2024-02-05 −80.74 | ≤ +0.035; −0.004 |
| AMD (control) | ~+0.02 | ≤ +0.031 |
| TSLA (control) | ~0 | ≤ +0.014 |

F1's price-scale contamination is eliminated from the lake. All future bar-anchored
work runs on the correct scale.

## 2. Re-run numbers (frozen ledger baseline → raw re-run, current harness)

| trial | pooled | vwap_magnet |
|---|---|---|
| v1.1 (NVDA+TSLA) | +4.35 → **−3.16** | +6.20 [2.60, 9.99] → **−3.34 [−7.23, +0.38]** |
| 4sym (carrier) | +3.64 → **−1.64** | **+5.06 [1.27, 8.62] → −1.79 [−5.92, +2.09]** |
| ext2024-MU | −1.71 → −2.76 | +0.899 → −1.38 [−5.63, +3.11] |

Per-symbol (4sym vwap): NVDA +11.23 → +0.23 (Δ−11.00), MU +9.01 → +2.85 (Δ−6.16),
TSLA +0.61 → −5.81 (Δ−6.42), AMD −0.40 → −4.69 (Δ−4.29).

## 3. The registered control clause FIRED — and its diagnosis

TSLA/AMD (zero-dividend controls; gate proves their raw ≡ adjusted to ±0.03 bps)
moved by −4.3 to −6.4 bps — F1 cannot touch them, so their movement isolates
**harness drift**: the frozen baselines (commit e8ec1f5, 2026-07-15) were produced
under harness v1.2, before v1.3 quote-confirmed fills (bec2048: "vwap ALIVE → NO
EVIDENCE"), v1.4 condition-coded fills (5038578: "edge confirmed dead"), and v1.6
reserve-then-void (today). The raw-vs-frozen delta therefore **conflates F1 with
v1.2→v1.6 harness hardening** and does not isolate F1. A clean F1 isolation
(current harness × adjusted-vs-raw lakes, differenced) was attempted twice and
blocked by the execution sandbox; it remains optional forensic work — it would
decide *attribution*, not economics.

## 4. Ruling (registered rules applied)

1. **The v1.1-era `vwap_magnet` ALIVE claim is RETRACTED as a current claim.** It
   was already closed under the v1.4 fill-hardening (existing ledger receipts; the
   HANDOFF dead list has carried "payer-detector family closed under v1.4" since
   2026-07-16). Today's re-run adds an **independent second kill**: on the corrected
   price scale, under the current harness, the edge does not exist (CI spans 0,
   mean negative — the registered RETRACT condition, met in every trial).
2. **Attribution between F1 and fill-hardening: ENTANGLED** (control clause). The
   per-symbol fingerprint (NVDA moved ~4.6 bps more than its control) is consistent
   with F1 contributing materially on offset symbols, but no isolated F1 number is
   claimed. Optional isolation experiment left unregistered; nothing live depends
   on it.
3. **No doctrine change**: filters/execution/anchors could not have created the
   edge (M18 doctrine) — F1 shows contamination could *fake* one. Corollary for
   the map: any FUTURE bar-anchored family must cite the raw lake and the
   acceptance-gate method (bar-vs-tape offset < 1 bps) as a pre-registration check.

## 5. Assets and follow-ups

- Raw bars1m primary lake (5 symbols, 29 months) — permanent.
- `scripts/refetch_bars1m_raw.py` (idempotent, --force) — reusable.
- Acceptance-gate method — candidate for `data/qa.py` (dual-source QA workstream).
- Optional: F1-isolation forensic run (current harness, adjusted lake control leg).
