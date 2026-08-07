# compare_arms — B(M3-A1-v2-legsonly) vs A(M3-A0-v1.1)

Intersection sessions: 159  (A sessions=185, B sessions=159)

## 1. Per-session BOOK net headline (intersection sessions)

| arm                   | n_sessions | total_book_net_bps | mean_per_session_bps | ci_lo   | ci_hi  |
|-----------------------|------------|--------------------|----------------------|---------|--------|
| A = M3-A0-v1.1        | 159        | 3528.64            | 22.193               | 3.121   | 39.207 |
| B = M3-A1-v2-legsonly | 159        | 1031.081           | 6.485                | -12.579 | 24.021 |

## 2. Paired per-session BOOK delta (B - A), day/session-clustered CI

delta_j = book_B(session_j) - book_A(session_j); sessions are the bootstrap clusters.

| split    | n_sessions | mean_delta_bps | ci_lo   | ci_hi  |
|----------|------------|----------------|---------|--------|
| train    | 103        | -14.63         | -36.103 | 4.9    |
| validate | 56         | -17.69         | -43.237 | 6.597  |
| pooled   | 159        | -15.708        | -31.256 | -0.111 |

## 3. Plan-level pairing (symbol, session, payer, side, authored-ts-minute)

'n_only_a_vetoed_by_b' = detector states authored in A but not B (B's vetoes).

| n_authored_a | n_authored_b | n_unique_keys_a | n_unique_keys_b | n_matched | n_only_a_vetoed_by_b | n_only_b | pairing_rate |
|--------------|--------------|-----------------|-----------------|-----------|----------------------|----------|--------------|
| 1034         | 493          | 1034            | 493             | 493       | 541                  | 0        | 0.4768       |

## 4. Leg-repricing signature (taken stream) — A0 vs A1

Authored leg px are not persisted in results.parquet; these realized / authored-claim columns are the observable re-pricing proxy.

| arm | metric           | n   | p10     | p50    | p90    | mean   |
|-----|------------------|-----|---------|--------|--------|--------|
| A   | gross_mid_bps    | 827 | -65.124 | 3.192  | 52.339 | -0.713 |
| A   | expected_net_bps | 827 | 13.731  | 25.664 | 67.823 | 34.371 |
| A   | confidence       | 827 | 0.5     | 0.5    | 0.5    | 0.5    |
| B   | gross_mid_bps    | 386 | -88.937 | 1.035  | 70.661 | -3.979 |
| B   | expected_net_bps | 386 | 13.677  | 26.36  | 73.826 | 36.88  |
| B   | confidence       | 386 | 0.5     | 0.5    | 0.5    | 0.5    |

### Exit-reason mix

| arm | exit_reason | count | share  |
|-----|-------------|-------|--------|
| A   | targets     | 348   | 0.4208 |
| A   | curfew      | 179   | 0.2164 |
| A   | stop        | 178   | 0.2152 |
| A   | hold        | 115   | 0.1391 |
| A   | mixed       | 7     | 0.0085 |
| B   | targets     | 115   | 0.2979 |
| B   | hold        | 112   | 0.2902 |
| B   | curfew      | 92    | 0.2383 |
| B   | stop        | 60    | 0.1554 |
| B   | mixed       | 7     | 0.0181 |
