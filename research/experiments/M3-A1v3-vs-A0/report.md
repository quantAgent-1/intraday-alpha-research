# compare_arms — B(M3-A1-v3-legsonly-a0hurdle) vs A(M3-A0-v1.1)

Intersection sessions: 185  (A sessions=185, B sessions=185)

## 1. Per-session BOOK net headline (intersection sessions)

| arm                            | n_sessions | total_book_net_bps | mean_per_session_bps | ci_lo | ci_hi  |
|--------------------------------|------------|--------------------|----------------------|-------|--------|
| A = M3-A0-v1.1                 | 185        | 3593.532           | 19.424               | 2.823 | 35.597 |
| B = M3-A1-v3-legsonly-a0hurdle | 185        | 3410.935           | 18.437               | 1.253 | 35.415 |

## 2. Paired per-session BOOK delta (B - A), day/session-clustered CI

delta_j = book_B(session_j) - book_A(session_j); sessions are the bootstrap clusters.

| split    | n_sessions | mean_delta_bps | ci_lo   | ci_hi  |
|----------|------------|----------------|---------|--------|
| train    | 122        | 1.61           | -13.891 | 16.091 |
| validate | 63         | -6.017         | -20.815 | 9.859  |
| pooled   | 185        | -0.987         | -11.934 | 10.502 |

## 3. Plan-level pairing (symbol, session, payer, side, authored-ts-minute)

'n_only_a_vetoed_by_b' = detector states authored in A but not B (B's vetoes).

| n_authored_a | n_authored_b | n_unique_keys_a | n_unique_keys_b | n_matched | n_only_a_vetoed_by_b | n_only_b | pairing_rate |
|--------------|--------------|-----------------|-----------------|-----------|----------------------|----------|--------------|
| 1034         | 1034         | 1034            | 1034            | 1034      | 0                    | 0        | 1.0          |

## 4. Leg-repricing signature (taken stream) — A0 vs A1

Authored leg px are not persisted in results.parquet; these realized / authored-claim columns are the observable re-pricing proxy.

| arm | metric           | n   | p10     | p50    | p90    | mean   |
|-----|------------------|-----|---------|--------|--------|--------|
| A   | gross_mid_bps    | 827 | -65.124 | 3.192  | 52.339 | -0.713 |
| A   | expected_net_bps | 827 | 13.731  | 25.664 | 67.823 | 34.371 |
| A   | confidence       | 827 | 0.5     | 0.5    | 0.5    | 0.5    |
| B   | gross_mid_bps    | 730 | -87.281 | 1.267  | 72.043 | -1.243 |
| B   | expected_net_bps | 730 | 13.701  | 26.762 | 69.958 | 35.444 |
| B   | confidence       | 730 | 0.5     | 0.5    | 0.501  | 0.5    |

### Exit-reason mix

| arm | exit_reason | count | share  |
|-----|-------------|-------|--------|
| A   | targets     | 348   | 0.4208 |
| A   | curfew      | 179   | 0.2164 |
| A   | stop        | 178   | 0.2152 |
| A   | hold        | 115   | 0.1391 |
| A   | mixed       | 7     | 0.0085 |
| B   | targets     | 218   | 0.2986 |
| B   | hold        | 208   | 0.2849 |
| B   | curfew      | 177   | 0.2425 |
| B   | stop        | 120   | 0.1644 |
| B   | mixed       | 7     | 0.0096 |
