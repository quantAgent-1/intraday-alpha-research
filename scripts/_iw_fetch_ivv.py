"""DR-X6 recipe step A: SPX monthly proxy via BlackRock varnish-api (IVV holdings).

Mechanical data assembly only - no economics, no interpolation beyond what the recipe
specifies. For each calendar month 2020-01..2026-06, uses the NYSE calendar (XNYS via
pandas_market_calendars) to compute the true last trading day of the month, fetches the
IVV holdings CSV for that asOfDate, and if the response is empty/unparseable, steps back
one NYSE trading day and retries (<=3 attempts total per the recipe).

Output: raw per-row CSV (all Asset Class rows, not yet filtered) to the scratchpad, plus
a per-month attempt log. Filtering to Asset Class == Equity and weight computation happen
in the build step (_iw_build.py) so this raw file is a faithful capture of what was fetched.
"""
import csv
import io
import sys
import time

import pandas as pd
import pandas_market_calendars as mcal
import requests

UA = {"User-Agent": "enginev51 research contact@example.com"}
BASE = "https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document"
PORTFOLIO_ID = "239726"  # IVV = iShares Core S&P 500 ETF
SCRATCH = "scratch"
OUT_RAW = f"{SCRATCH}/iw_ivv_raw.csv"
LOG = f"{SCRATCH}/iw_ivv_log.txt"
SLEEP_S = 2.0
MAX_ATTEMPTS = 3

FIELDNAMES = ["req_month", "asof_date", "attempt", "ticker", "name", "sector",
              "asset_class", "weight_pct", "source_url"]


def month_end_trading_days(start="2020-01-01", end="2026-06-30"):
    cal = mcal.get_calendar("XNYS")
    sched = cal.schedule(start_date=start, end_date=end)
    days = list(pd.DatetimeIndex(sched.index))
    df = pd.DataFrame({"d": days})
    df["ym"] = df["d"].dt.to_period("M")
    month_ends = df.groupby("ym")["d"].max().sort_index()
    return month_ends, days  # (Series indexed by Period -> Timestamp, full sorted trading-day list)


def prior_trading_day(d, all_days):
    idx = all_days.index(d)
    if idx == 0:
        return None
    return all_days[idx - 1]


def fetch(asof_str):
    params = {"switchLocale": "y", "siteEntryPassthrough": "true",
              "portfolioId": PORTFOLIO_ID, "asOfDate": asof_str, "component": "holdings"}
    r = requests.get(BASE, params=params, headers=UA, timeout=25)
    return r


def parse_holdings_csv(text):
    """Return list of dict rows (all Asset Class values) or [] if unparseable/empty."""
    reader = csv.reader(io.StringIO(text))
    all_rows = list(reader)
    header_idx = None
    for i, row in enumerate(all_rows):
        if len(row) >= 6 and row[0] == "Ticker" and row[1] == "Name":
            header_idx = i
            break
    if header_idx is None:
        return []
    header = all_rows[header_idx]
    out = []
    for row in all_rows[header_idx + 1:]:
        if len(row) == 0 or (len(row) == 1 and row[0].strip() == ""):
            break
        if len(row) != len(header):
            break
        out.append(dict(zip(header, row)))
    return out


def main():
    month_ends, all_days = month_end_trading_days()
    print(f"months to fetch: {len(month_ends)}", flush=True)

    out_f = open(OUT_RAW, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES)
    writer.writeheader()
    log_f = open(LOG, "w", encoding="utf-8")

    n_ok, n_fail = 0, 0
    for ym, target_day in month_ends.items():
        d = target_day
        got_rows = None
        used_asof = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            asof_str = d.strftime("%Y%m%d")
            url = f"{BASE}?switchLocale=y&siteEntryPassthrough=true&portfolioId={PORTFOLIO_ID}&asOfDate={asof_str}&component=holdings"
            try:
                r = fetch(asof_str)
            except Exception as e:
                log_f.write(f"{ym}\t{asof_str}\tattempt{attempt}\tEXCEPTION {e!r}\n")
                log_f.flush()
                time.sleep(SLEEP_S)
                d = prior_trading_day(d, all_days)
                if d is None:
                    break
                continue
            time.sleep(SLEEP_S)
            if r.status_code != 200:
                log_f.write(f"{ym}\t{asof_str}\tattempt{attempt}\tHTTP{r.status_code}\n")
                log_f.flush()
                d = prior_trading_day(d, all_days)
                if d is None:
                    break
                continue
            rows = parse_holdings_csv(r.text)
            if len(rows) < 10:
                log_f.write(f"{ym}\t{asof_str}\tattempt{attempt}\tEMPTY_OR_UNPARSEABLE len(text)={len(r.text)} rows={len(rows)}\n")
                log_f.flush()
                d = prior_trading_day(d, all_days)
                if d is None:
                    break
                continue
            # success
            got_rows = rows
            used_asof = asof_str
            log_f.write(f"{ym}\t{asof_str}\tattempt{attempt}\tOK rows={len(rows)}\n")
            log_f.flush()
            break

        if got_rows is None:
            n_fail += 1
            print(f"{ym}: FAILED after retries (last tried {d})", flush=True)
            continue

        n_ok += 1
        asof_iso = f"{used_asof[0:4]}-{used_asof[4:6]}-{used_asof[6:8]}"
        for rec in got_rows:
            writer.writerow({
                "req_month": str(ym),
                "asof_date": asof_iso,
                "attempt": used_asof,
                "ticker": rec.get("Ticker", "").strip(),
                "name": rec.get("Name", "").strip(),
                "sector": rec.get("Sector", "").strip(),
                "asset_class": rec.get("Asset Class", "").strip(),
                "weight_pct": rec.get("Weight (%)", "").strip(),
                "source_url": f"{BASE}?portfolioId={PORTFOLIO_ID}&asOfDate={used_asof}&component=holdings",
            })
        out_f.flush()
        print(f"{ym}: OK asof={asof_iso} rows={len(got_rows)}", flush=True)

    out_f.close()
    log_f.close()
    print(f"DONE. months_ok={n_ok} months_fail={n_fail} total={len(month_ends)}")


if __name__ == "__main__":
    sys.exit(main())
