"""Build the WIDE minute-bar panel for the M28 open-cross signal battery.

Universe rule (mechanical, outcome-blind, frozen in the M28 pre-registration):
  from `data/external/m17_daily_bars.parquet` (659 free symbols), keep symbols with >= 200
  sessions in **calendar 2023** -- a period strictly PRIOR to the 2024-01..2026-05 test
  window -- rank by median daily dollar volume in 2023, take the top 200.
No return, signal or outcome data of any candidate is examined by the rule.

Of those 200, index/sector ETFs and one duplicate share class are excluded from the
TRADEABLE cross-section (they are baskets, not stocks) but are still fetched, because they
are the factor/hedge references the portfolio layer needs.

Months are hard-capped at 2026-05 so the sealed holdout (>= 2026-06-01) is never fetched.
Coverage starts 2023-10 to give the 21-session lookback features a warm-up before the
first test session (2024-01-02).

    uv run python scripts/backfill_bars1m_wide.py --plan
    uv run python scripts/backfill_bars1m_wide.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from enginev51.config import get_settings  # noqa: E402
from enginev51.data import store  # noqa: E402
from enginev51.data.backfill import run_letf_bars  # noqa: E402
from enginev51.protocol import SealViolation  # noqa: E402

M17 = REPO / "data" / "external" / "m17_daily_bars.parquet"
UNIVERSE_JSON = REPO / "research" / "experiments" / "M28-open-cross-battery" / "universe.json"

RANK_YEAR = ("2023-01-01", "2023-12-31")
MIN_SESSIONS_2023 = 200
TOP_N = 200
FIRST_MONTH = "2023-10"
LAST_MONTH = "2026-05"          # hard cap: the sealed holdout is never fetched

# Non-stocks in the top-200 by the rule above: index/sector ETFs. Kept as factor/hedge
# references, excluded from the tradeable cross-section.
ETFS = {"SPY", "QQQ", "IWM", "IWF", "IWD",
        "XLE", "XLF", "XLV", "XLK", "XLI", "XLU", "XLP", "XLY", "XLB", "XLC"}
# Duplicate share class of an already-included issuer (GOOGL kept, GOOG dropped).
DUP_CLASS = {"GOOG"}


def months(a: str, b: str) -> list[str]:
    out, y, m = [], int(a[:4]), int(a[5:7])
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def universe() -> tuple[list[str], list[str]]:
    d = pl.read_parquet(M17, columns=["symbol", "session", "close", "volume"])
    r = d.filter(
        (pl.col("session") >= RANK_YEAR[0]) & (pl.col("session") <= RANK_YEAR[1])
    ).with_columns((pl.col("close") * pl.col("volume")).alias("dv"))
    g = (r.group_by("symbol")
           .agg(pl.col("dv").median().alias("mdv"), pl.len().alias("n"))
           .filter(pl.col("n") >= MIN_SESSIONS_2023)
           .sort("mdv", descending=True)
           .head(TOP_N))
    allsyms = g["symbol"].to_list()
    tradeable = [s for s in allsyms if s not in ETFS and s not in DUP_CLASS]
    return allsyms, tradeable


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Wide bars1m backfill for M28.")
    ap.add_argument("--plan", action="store_true", help="Print the plan; fetch nothing.")
    args = ap.parse_args(argv)

    allsyms, tradeable = universe()
    UNIVERSE_JSON.parent.mkdir(parents=True, exist_ok=True)
    import json
    UNIVERSE_JSON.write_text(json.dumps(
        {"rank_year": RANK_YEAR, "min_sessions_2023": MIN_SESSIONS_2023, "top_n": TOP_N,
         "first_month": FIRST_MONTH, "last_month": LAST_MONTH,
         "etfs_excluded_from_cross_section": sorted(ETFS),
         "duplicate_class_excluded": sorted(DUP_CLASS),
         "all_fetched": allsyms, "tradeable": tradeable}, indent=1), encoding="utf-8")

    settings = get_settings()
    feed = settings.data_feed_type
    mos = months(FIRST_MONTH, LAST_MONTH)
    if max(mos) > LAST_MONTH:
        raise SealViolation("holdout guard tripped")
    work = [(s, mo) for s in allsyms for mo in mos
            if not any(store.partition_exists(r, feed, "bars1m", s, mo)
                       for r in settings.read_roots)]
    print(f"universe: {len(allsyms)} fetched ({len(tradeable)} tradeable, "
          f"{len(allsyms) - len(tradeable)} reference/excluded)")
    print(f"months  : {len(mos)} ({mos[0]}..{mos[-1]})")
    print(f"missing : {len(work)} partitions  -> wrote universe.json")
    if args.plan or not work:
        return 0
    written = run_letf_bars(settings, work)
    print(f"wrote {written} partitions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
