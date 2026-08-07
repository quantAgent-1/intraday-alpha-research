# M10 execution annotation — historical entry-shortfall ground truth — RESULT 2026-07-17

Registered before running (ledger `M10-entry-shortfall-annotation-v1`; NO new family — annotates M10).
Shortfall = side·(entry_px − entry_mid)/entry_mid on the M6 panel (5 names, 2020-2026, n=7,959;
these are the sim taker fills whose cost is ALREADY inside every reported net_bps — this
annotation decomposes it, it does not add a new cost).

## Numbers (bps)

Pooled: **median 1.46, p75 4.85, p90 8.67**; median half-spread 0.73 (median shortfall ≈ 2× touch).

| Name | median | p90 | med half-spread |
|---|---|---|---|
| AMD | 1.27 | 8.37 | 0.63 |
| GOOGL | 1.57 | 7.46 | 0.54 |
| MU | 1.28 | 8.89 | 0.82 |
| NVDA | 1.69 | 9.39 | 0.74 |
| TSLA | 1.64 | 9.76 | 0.83 |

By year: median 0.77-2.03; p90 7.5-10.2 (only 2022 breached 10: p90 10.2).

## Verdict vs DR-Q4-6 locked kill thresholds (median ≥5 or p90 ≥10 kills the deploy story)

**PASS** — median 1.46 ≪ 5; pooled p90 8.67 < 10 (2022 alone touched 10.2; 2025 median 0.77).
The deploy story survives on historical sim fills. Honest caveats:
1. p90 sits near the bar — the cost tail is real; ~10% of entries eat ~4× the expected mean.
   The M8 meta-filter and any M12 filter implicitly help by dropping unreliable events.
2. These are simulated BBO taker fills; the LIVE log (same quantiles, per forward-paper session)
   is the actual judge — wire-in starts with M10 session 1 (2026-07-17 close).

## Standing instruction (annotation)

Every forward-paper daily report appends: session median/p75/p90 realized shortfall vs
15:55:10 mid, and half-spread at decision. Divergence of live vs historical quantiles
(> +2 bps at median for 10 sessions) triggers a deploy-story review.
