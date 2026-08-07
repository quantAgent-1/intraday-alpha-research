# Data-quality report — 20260715T054005Z

Symbols: NVDA, TSLA  |  kinds: trades, quotes  |  feed: sip
Read roots: <repo-root>\data\raw, <legacy-lake>\data\raw
Total audited (symbol, session) rows: 392

## Coverage

### NVDA coverage

- range: 2025-09-02 -> 2026-07-10
- expected calendar sessions: 215
- sessions with all requested kinds non-empty: 198

| kind | partitions present | non-empty | missing |
|---|---|---|---|
| trades | 198 | 198 | 17 |
| quotes | 198 | 198 | 17 |

- **trades** missing 17 sessions: 2026-06-01, 2026-06-02, 2026-06-03, 2026-06-04, 2026-06-05, 2026-06-08 ... 2026-06-16, 2026-06-17, 2026-06-18, 2026-06-22, 2026-06-23, 2026-06-24
- **quotes** missing 17 sessions: 2026-06-01, 2026-06-02, 2026-06-03, 2026-06-04, 2026-06-05, 2026-06-08 ... 2026-06-16, 2026-06-17, 2026-06-18, 2026-06-22, 2026-06-23, 2026-06-24

### TSLA coverage

- range: 2025-09-02 -> 2026-07-10
- expected calendar sessions: 215
- sessions with all requested kinds non-empty: 194

| kind | partitions present | non-empty | missing |
|---|---|---|---|
| trades | 194 | 194 | 21 |
| quotes | 194 | 194 | 21 |

- **trades** missing 21 sessions: 2026-05-26, 2026-05-27, 2026-05-28, 2026-05-29, 2026-06-01, 2026-06-02 ... 2026-06-16, 2026-06-17, 2026-06-18, 2026-06-22, 2026-06-23, 2026-06-24
- **quotes** missing 21 sessions: 2026-05-26, 2026-05-27, 2026-05-28, 2026-05-29, 2026-06-01, 2026-06-02 ... 2026-06-16, 2026-06-17, 2026-06-18, 2026-06-22, 2026-06-23, 2026-06-24

## Worst 10 sessions by max intra-RTH gap

**trades**

| symbol | session | max_gap_s_trades |
|---|---|---|
| TSLA | 2025-09-10 | 2.4 |
| TSLA | 2026-04-14 | 2.2 |
| TSLA | 2026-05-05 | 2.1 |
| TSLA | 2026-07-10 | 2.1 |
| TSLA | 2025-09-09 | 2.0 |
| TSLA | 2026-04-09 | 1.9 |
| TSLA | 2026-07-08 | 1.9 |
| NVDA | 2026-04-02 | 1.9 |
| TSLA | 2026-05-20 | 1.9 |
| TSLA | 2026-07-07 | 1.9 |

**quotes**

| symbol | session | max_gap_s_quotes |
|---|---|---|
| TSLA | 2026-07-09 | 10.5 |
| TSLA | 2025-09-19 | 8.8 |
| TSLA | 2025-10-08 | 8.7 |
| TSLA | 2025-12-31 | 8.5 |
| TSLA | 2025-10-29 | 8.3 |
| TSLA | 2026-07-07 | 8.3 |
| TSLA | 2025-12-10 | 8.1 |
| TSLA | 2026-07-08 | 7.9 |
| TSLA | 2026-07-10 | 7.9 |
| TSLA | 2026-07-01 | 7.6 |

## Crossed / locked quote outliers

| symbol | session | crossed_or_locked_frac | rows_quotes |
|---|---|---|---|
| NVDA | 2026-02-18 | 0.11919 | 4518438 |
| NVDA | 2026-02-20 | 0.11407 | 6114778 |
| NVDA | 2026-02-12 | 0.11402 | 7558324 |
| NVDA | 2026-03-18 | 0.11380 | 3301043 |
| NVDA | 2026-03-25 | 0.10964 | 3027119 |
| NVDA | 2026-02-26 | 0.10790 | 5955175 |
| NVDA | 2026-03-13 | 0.10762 | 4826498 |
| NVDA | 2026-03-30 | 0.10603 | 4359579 |
| NVDA | 2025-09-18 | 0.10460 | 2328053 |
| NVDA | 2026-03-26 | 0.10419 | 3927740 |

## bars1m coverage

### NVDA bars1m

- months: 2023-07 -> 2026-07  | missing months: 0  | suspicious (<300 RTH bars) sessions: 0

### TSLA bars1m

- months: 2023-07 -> 2026-07  | missing months: 0  | suspicious (<300 RTH bars) sessions: 0
