# M17 cross-sectional + factor momentum — RESULT 2026-07-19 (RESEARCH-ONLY side-ledger)

Registered before data build (`M17-xsect-factor-momentum-v1`); frozen spec M3_REGISTRATION.md.
Deploy remains OUT-OF-MISSION (overnight holds) — any live use requires explicit mission
amendment. Data: PIT S&P 500 membership (own IVV table, survivorship-safe), 638/645 tickers
with Alpaca adjusted daily bars (0.6% genuine coverage loss, documented), all 21 ETFs complete.
n = 66 months (2021-01..2026-06). Decay-check framing: field decades = prior; this measures
"does it still pay, here, recently, after costs."

## Cell A — cross-sectional stock momentum (PRIMARY 12-1): BETWEEN

| Object | Result |
|---|---|
| D10−D1 long/short, net | **+0.73%/mo (+8.8%/yr), t = +1.01** (avg universe 499, deciles of ~50) |
| Long-only D10 vs EW universe, net | +1.66 vs +1.03 %/mo → **excess +7.7%/yr, t = +1.39** |
| Worst months | 2022-12 −15.8%, 2021-01 −12.6%, 2023-11 −9.0% (the signature crashes) |
| By year (L/S) | 2020 −2.4, 2021 −2.1, 2022 +0.7, 2023 +0.4, 2024 +2.1, 2025 −0.1, **2026 +7.7 %/mo** |

Registered bars: PASS needed t≥2 (miss); KILL needed t<1 or negative (t=1.01 — skated past
the kill bar by 0.01, noted honestly). Secondary 6-1 confirms shape (+0.66%/mo, t=0.88).
Reading: the textbook point estimate at textbook violence; at n=66 months this cannot be
distinguished from luck — the field's decades are doing all the epistemic work.

## Cell B — factor/sector momentum, top-3 of 20 ETFs (PRIMARY 12-1): PASS (its modest bars)

| Object | Result |
|---|---|
| Strategy net | +1.41%/mo, **Sharpe 1.05** (26% one-way turnover/mo) |
| EW-of-universe | +1.15%/mo, Sharpe 0.95 → **excess +3.1%/yr** (bar: ≥2) |
| SPY buy-hold | +1.26%/mo, Sharpe 0.99 → excess +1.7%/yr |
| Honesty stats | excess t = +0.86, monthly hit-rate 0.53, UNDERPOWERED-BY-DESIGN flag stands |
| Robustness | secondary 6m variant: +3.0%/yr excess, Sharpe 1.06 — insensitive to formation window |

Both registered PASS conditions met (Sharpe > EW AND excess ≥ +2%/yr). This is a REPLICATION
of the field's factor-momentum result at modest scale — not a discovery; the t=0.86 says 66
months cannot prove it alone, which is exactly why the bars were set as replication bars.

## Disposition

- Side-ledger verdicts recorded: **Cell A BETWEEN (report-only), Cell B PASS (replication).**
- No deployment path exists under the current mission. IF the user ever amends: Cell B's
  shape is operationally trivial (3 ETF positions, monthly rotation, ~26% turnover, long-only,
  no locates) and its risk is equity-like; Cell A's L/S at retail is NOT recommended
  (50-name short leg, crash months of −16%).
- Interaction with the main program: none (different horizon, different capital); the auction
  book and forward clock are unaffected.

## Files

`scripts/m17_momentum.py` (frozen spec inline), data `data/external/m17_daily_bars.parquet`
+ coverage doc; universe from `data/external/index_weights_monthly.parquet`.
