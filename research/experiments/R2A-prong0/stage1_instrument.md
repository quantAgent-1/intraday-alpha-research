# R2-A Stage 1 (D) - instrument axis (SOXL) - EXPLORATORY, post-hoc, not a gate

sessions with >=3 semis and SOXL data: 578
SOXL median open price $35.08 -> one-tick floor 2.85 bps (half 1.43)

| cell | n | gross bps | 95% CI | cost | NET | t |
|---|---|---|---|---|---|---|
| all sessions | 578 | +33.17 | [-10.88, +78.07] | 1.82 | +31.35 | 1.46 |
| top-quartile |aggregate OLI| | 145 | +90.34 | [+4.26, +181.15] | 1.73 | +88.61 | 2.00 |

## Is it just the semis bull market? (drift vs timing)

| cell | buy-and-hold | % long | net tilt | gross | from drift | from TIMING |
|---|---|---|---|---|---|---|
| all sessions | -3.99 | 57.1% | +0.142 | +33.17 | -0.57 | +33.73 |
| top-quartile | -25.00 | 58.6% | +0.172 | +90.34 | -4.31 | +94.65 |

Drift is not the source: buy-and-hold over these sessions is negative and the rule is close to balanced long/short, so the drift term is ~0 and essentially all of the result is timing. This does NOT make the result confirmed -- the cell is post-hoc on already-seen data. It means the instrument expression is worth carrying into an out-of-sample test.
