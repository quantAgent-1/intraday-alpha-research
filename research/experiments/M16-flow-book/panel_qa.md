# M16 Stage A hourly panel -- QA report

Built: 2026-07-18T14:31:46+00:00
Source: `scripts/m16_build_hourly_panel.py`

**Total rows:** 64400
**Columns:** 17 -- symbol, session, clock, quote_ts, gap_s, bid, ask, mid, half_spread_bps, day_open, session_close, r_open_bps, flow_coef, F_usd, ret_next_close_bps, month_end, opex

## Sessions per symbol

| symbol | rows | sessions | first_session | last_session |
|---|---|---|---|---|
| AMD | 12880 | 1610 | 2020-01-02 | 2026-05-29 |
| GOOGL | 12880 | 1610 | 2020-01-02 | 2026-05-29 |
| MU | 12880 | 1610 | 2020-01-02 | 2026-05-29 |
| NVDA | 12880 | 1610 | 2020-01-02 | 2026-05-29 |
| TSLA | 12880 | 1610 | 2020-01-02 | 2026-05-29 |

## Null rates per column

| column | dtype | null_count | null_rate |
|---|---|---|---|
| symbol | String | 0 | 0.0000% |
| session | Date | 0 | 0.0000% |
| clock | String | 0 | 0.0000% |
| quote_ts | Int64 | 64 | 0.0994% |
| gap_s | Float64 | 64 | 0.0994% |
| bid | Float64 | 64 | 0.0994% |
| ask | Float64 | 64 | 0.0994% |
| mid | Float64 | 64 | 0.0994% |
| half_spread_bps | Float64 | 64 | 0.0994% |
| day_open | Float64 | 0 | 0.0000% |
| session_close | Float64 | 0 | 0.0000% |
| r_open_bps | Float64 | 64 | 0.0994% |
| flow_coef | Float64 | 0 | 0.0000% |
| F_usd | Float64 | 64 | 0.0994% |
| ret_next_close_bps | Float64 | 64 | 0.0994% |
| month_end | Boolean | 0 | 0.0000% |
| opex | Boolean | 0 | 0.0000% |

## Match rate by clock

Fraction of (symbol, session) rows with a quote matched within 120s tolerance.

| clock | n | matched | match_rate |
|---|---|---|---|
| 10:00 | 8050 | 8050 | 100.0000% |
| 11:00 | 8050 | 8050 | 100.0000% |
| 12:00 | 8050 | 8050 | 100.0000% |
| 13:00 | 8050 | 8045 | 99.9379% |
| 14:00 | 8050 | 8036 | 99.8261% |
| 15:00 | 8050 | 8035 | 99.8137% |
| 15:30 | 8050 | 8033 | 99.7888% |
| 15:50 | 8050 | 8037 | 99.8385% |

## Match rate by year

| year | n | matched | match_rate |
|---|---|---|---|
| 2020 | 10120 | 10090 | 99.7036% |
| 2021 | 10080 | 10076 | 99.9603% |
| 2022 | 10040 | 10031 | 99.9104% |
| 2023 | 10000 | 9988 | 99.8800% |
| 2024 | 10080 | 10073 | 99.9306% |
| 2025 | 10000 | 9998 | 99.9800% |
| 2026 | 4080 | 4080 | 100.0000% |

## Null clusters (which sessions the 120s-tolerance misses fall on)

64 null rows total, clustered on 11 distinct sessions (none scattered randomly on an otherwise-ordinary day):

| session | n | symbols | clocks |
|---|---|---|---|
| 2020-03-18 | 5 | AMD, GOOGL, MU, NVDA, TSLA | 13:00 |
| 2020-11-27 | 14 | AMD, GOOGL, MU, NVDA | 14:00, 15:00, 15:30, 15:50 |
| 2020-12-24 | 11 | AMD, GOOGL, MU, NVDA | 14:00, 15:00, 15:30, 15:50 |
| 2021-11-26 | 4 | MU | 14:00, 15:00, 15:30, 15:50 |
| 2022-11-25 | 9 | AMD, GOOGL, MU, NVDA | 14:00, 15:00, 15:30, 15:50 |
| 2023-07-03 | 6 | GOOGL, MU | 14:00, 15:00, 15:30, 15:50 |
| 2023-11-24 | 6 | AMD, GOOGL, MU | 14:00, 15:00, 15:30, 15:50 |
| 2024-07-03 | 1 | GOOGL | 15:30 |
| 2024-11-29 | 4 | GOOGL, MU | 15:00, 15:30 |
| 2024-12-24 | 2 | GOOGL, MU | 15:00, 15:50 |
| 2025-12-24 | 2 | AMD | 15:30, 15:50 |

Mechanism, checked against the raw bbo1s ticks: all sessions above are either (a) the scheduled NYSE/Nasdaq half-day calendar (day after Thanksgiving, Jul 3, Christmas Eve) -- quoting past the 13:00 ET early close is real but sporadic, so a clock's forward search occasionally exceeds 120s tolerance in the thin afternoon -- or (b) 2020-03-18, inside the single most volatile week of the COVID crash, where all 5 symbols miss only the 13:00 clock (bbo1s is Nasdaq's own XNAS top-of-book, not consolidated SIP NBBO -- a brief single-venue gap under that week's extreme conditions is consistent with the feed's documented scope, see data/bbo1s.py module docstring). No null falls on an otherwise-ordinary session.

## Flag / value sanity

- distinct month_end sessions (all symbols): 77 (77 calendar months in range)
- distinct opex sessions (all symbols): 75 (2 of the 77 candidate 3rd-Fridays are themselves market holidays -- Good Friday 2022-04-15 and 2025-04-18 -- so the literal '3rd Friday of the month' rule correctly never fires that month; no row exists on a non-trading day for it to fire on)
- rows with flow_coef > 0: 28992 / 64400
- gap_s among matched rows: mean=0.148s, p50=0.000s, max=119.000s
- half_spread_bps among matched rows: mean=1.227, p50=0.906, max=25.215
- r_open_bps: mean=4.424, min=-1310.400, max=2222.924
- ret_next_close_bps: mean=2.947, min=-1518.506, max=2216.818

## Largest |r_open_bps| moves (sanity check against known market events)

| symbol | session | clock | day_open | mid | r_open_bps |
|---|---|---|---|---|---|
| AMD | 2025-04-09 | 15:50 | 79.22 | 96.83 | +2222.9 |
| AMD | 2025-04-09 | 15:30 | 79.22 | 95.99 | +2116.9 |
| TSLA | 2025-04-09 | 15:50 | 224.69 | 270.88 | +2055.5 |
| TSLA | 2025-04-09 | 15:30 | 224.69 | 268.51 | +1950.5 |
| TSLA | 2020-03-19 | 15:00 | 374.70 | 445.50 | +1889.6 |
| MU | 2025-04-09 | 15:50 | 66.20 | 77.75 | +1744.7 |

Cross-checked against known dates: TSLA 2021-11-09 (-12.9%) is the Musk stock-sale-poll selloff; AMD/TSLA/MU 2025-04-09 (+20-22%) is the tariff-pause rally; TSLA 2020-03-13 (-12.8%) is inside the COVID circuit-breaker week. Extremes line up with real events, not artifacts.

## 3 sample rows

```
shape: (3, 17)
┌────────┬────────────┬───────┬─────────────────────┬───────┬────────┬────────┬─────────┬─────────────────┬──────────┬───────────────┬────────────┬───────────┬───────────────┬────────────────────┬───────────┬───────┐
│ symbol ┆ session    ┆ clock ┆ quote_ts            ┆ gap_s ┆ bid    ┆ ask    ┆ mid     ┆ half_spread_bps ┆ day_open ┆ session_close ┆ r_open_bps ┆ flow_coef ┆ F_usd         ┆ ret_next_close_bps ┆ month_end ┆ opex  │
│ ---    ┆ ---        ┆ ---   ┆ ---                 ┆ ---   ┆ ---    ┆ ---    ┆ ---     ┆ ---             ┆ ---      ┆ ---           ┆ ---        ┆ ---       ┆ ---           ┆ ---                ┆ ---       ┆ ---   │
│ str    ┆ date       ┆ str   ┆ i64                 ┆ f64   ┆ f64    ┆ f64    ┆ f64     ┆ f64             ┆ f64      ┆ f64           ┆ f64        ┆ f64       ┆ f64           ┆ f64                ┆ bool      ┆ bool  │
╞════════╪════════════╪═══════╪═════════════════════╪═══════╪════════╪════════╪═════════╪═════════════════╪══════════╪═══════════════╪════════════╪═══════════╪═══════════════╪════════════════════╪═══════════╪═══════╡
│ AMD    ┆ 2020-01-02 ┆ 10:00 ┆ 1577977200000000000 ┆ 0.0   ┆ 47.49  ┆ 47.5   ┆ 47.495  ┆ 1.052742        ┆ 46.86    ┆ 49.1          ┆ 135.51003  ┆ 0.0       ┆ 0.0           ┆ 337.930308         ┆ false     ┆ false │
│ GOOGL  ┆ 2023-03-15 ┆ 13:00 ┆ 1678899600000000000 ┆ 0.0   ┆ 94.66  ┆ 94.67  ┆ 94.665  ┆ 0.528178        ┆ 93.22    ┆ 96.11         ┆ 155.009655 ┆ 1.6673e7  ┆ 258454.762907 ┆ 152.643532         ┆ false     ┆ false │
│ TSLA   ┆ 2026-05-29 ┆ 15:50 ┆ 1780084201000000000 ┆ 1.0   ┆ 436.36 ┆ 436.89 ┆ 436.625 ┆ 6.069281        ┆ 439.845  ┆ 435.79        ┆ -73.207607 ┆ 1.3686e10 ┆ -1.0019e8     ┆ -19.123962         ┆ true      ┆ false │
└────────┴────────────┴───────┴─────────────────────┴───────┴────────┴────────┴─────────┴─────────────────┴──────────┴───────────────┴────────────┴───────────┴───────────────┴────────────────────┴───────────┴───────┘
```
