# R2-A quote-free variant - pre-declared admissibility gate V1/V2/V3

discovery rows: quote-based 4356, quote-free 4442, matched on (sym,date) 4341

**V1** corr(OLI quote-signed, OLI tick-signed) = **0.1106** (threshold >= 0.9) -> FAIL

| name | corr | n |
|---|---|---|
| NVDA | -0.0246 | 297 |
| TSLA | -0.0876 | 186 |
| AMD | -0.0338 | 185 |
| MU | 0.0690 | 602 |
| GOOGL | -0.1160 | 185 |
| KLAC | 0.1973 | 576 |
| MRVL | -0.0070 | 580 |
| LRCX | 0.1747 | 578 |
| TXN | 0.1330 | 576 |
| AMAT | 0.1400 | 576 |

**V2** quote-free top-quartile signed fade on the discovery panel = **-2.11** bps [-19.92, +15.99] n=1115
    published quote-based reference +14.87; admissible band [+10.41, +19.34] -> FAIL
    (non-gating, matched rows only: -0.88 bps n=1089)

**V3** median |bars1m-exit return - bbo1s-exit return| = **5.97** bps (threshold <= 3.0) -> FAIL
    mean 8.65, p90 18.78, p99 45.50 bps

## VERDICT: METHOD-BLOCKED - Stage 3 abandoned
