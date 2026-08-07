"""Backfill historical SIP quotes for the 16 OOS names into bbo1s-layout partitions.

Purpose: R2A-oos Amendment 2 — the decisive out-of-sample test runs the ORIGINAL frozen
quote-signed rule, which reads `data/raw/bbo1s/{SYM}/{YYYY-MM}.parquet`. This script
manufactures those partitions for the 16 virgin names from Alpaca free-tier historical
quotes, downsampled to the owned lake's 1-second convention.

DOWNSAMPLE CONVENTION (fidelity-gated by `quote_source_fidelity.py` BEFORE any verdict may
consume this data): for each second boundary B, keep the LAST raw quote with ts <= B and
stamp it B ( = ceil(ts / 1s) ). State-at-boundary: a trade inside [B-1, B) can only see
quotes stamped <= B-1, i.e. fully completed seconds — the discovery signing convention.
Rows are NOT validity-filtered here (the owned lake also carries one-sided quotes);
consumers apply bid>0 & ask>bid exactly as they do on the owned lake.

Pull window per session: 09:25–16:00 ET (5-min warm-up so the first RTH trades have a
prevailing quote; half-days naturally end early and trip the frozen early-close guard).
Monthly files are written once complete and skipped on resume. Cap < 2026-06 (holdout).

    uv run python scripts/backfill_quotes_oos.py --dry-run
    uv run python scripts/backfill_quotes_oos.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import backfill_trades_semis as B  # noqa: E402  (verified calendar + client plumbing)

OOS = ["VRTX", "BKNG", "ISRG", "AMGN", "HON", "INTU", "TMUS", "GILD",
       "MDLZ", "COST", "PEP", "ADBE", "CMCSA", "SBUX", "CSCO", "QCOM"]
SEMIS = ["KLAC", "MRVL", "LRCX", "TXN", "AMAT"]      # discovery semis, V-NB bridge data
# SEPARATE ROOT (Amendment 3): Alpaca-derived NBBO partitions never touch the owned
# Databento XNAS lake at data/raw/bbo1s.
BBO_DIR = REPO / "data" / "raw" / "bbo1s_nbbo"
LOG_PATH = REPO / "logs" / "backfill_quotes_oos.log"
ET = ZoneInfo("America/New_York")
NS = 1_000_000_000
SCHEMA = {"ts": pl.Int64, "bid": pl.Float64, "ask": pl.Float64,
          "bid_size": pl.Float64, "ask_size": pl.Float64}


def downsample_1s(rows: list[dict]) -> pl.DataFrame:
    """Raw quote dicts -> one row per second boundary (last quote at/before boundary)."""
    if not rows:
        return pl.DataFrame(schema=SCHEMA)
    df = pl.DataFrame(rows).select(["ts", "bid", "ask", "bid_size", "ask_size"])
    df = df.with_columns(
        (((pl.col("ts") + NS - 1) // NS) * NS).alias("_b")).sort("ts")
    g = df.group_by("_b").agg(
        pl.col("bid").last(), pl.col("ask").last(),
        pl.col("bid_size").last(), pl.col("ask_size").last())
    return (g.rename({"_b": "ts"}).sort("ts")
            .select(["ts", "bid", "ask", "bid_size", "ask_size"])
            .cast(SCHEMA))


def pull_day(hist, sym: str, date_str: str) -> pl.DataFrame:
    """One session's quotes, 09:25-16:00 ET, downsampled to the 1s convention."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    start = d.replace(hour=9, minute=25, tzinfo=ET)
    end = d.replace(hour=16, minute=0, tzinfo=ET) + timedelta(seconds=1)
    raw: list[dict] = []
    for page in hist.fetch_quotes(sym, start, end):
        raw.extend(page)
    return downsample_1s(raw)


def _logger() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("backfill_quotes_oos")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    h = logging.FileHandler(LOG_PATH, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(h)
    return log


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Backfill NBBO quotes into bbo1s_nbbo layout.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--set", choices=["oos", "semis"], default="oos",
                    help="oos = the 16 virgin names; semis = the 5 discovery semis (V-NB)")
    args = ap.parse_args(argv)
    names = OOS if args.set == "oos" else SEMIS

    cal = B.session_calendar()                      # 604 ET sessions, capped < holdout
    months: dict[str, list[str]] = {}
    for dt in cal:
        months.setdefault(dt[:7], []).append(dt)

    work = [(sym, mo) for sym in names for mo in sorted(months)
            if not (BBO_DIR / sym / f"{mo}.parquet").exists()]
    print(f"quotes backfill [{args.set}]: {len(names)} names x {len(months)} months; "
          f"missing partitions = {len(work)}")
    if args.dry_run or not work:
        return 0

    log = _logger()
    settings = B.get_settings()
    try:
        hist = B.AlpacaHist(settings)
    except Exception as exc:  # noqa: BLE001
        print(f"CLIENT ERROR: {type(exc).__name__}: {exc}")
        return 2
    hist.limiter = B.RateLimiter(B.REQ_PER_MIN)
    wrote = 0
    try:
        for sym, mo in work:
            parts = []
            for dt in months[mo]:
                try:
                    day = pull_day(hist, sym, dt)
                except Exception as exc:  # noqa: BLE001
                    log.error("FAIL %s %s %s: %s", sym, dt, type(exc).__name__, exc)
                    continue
                if day.height:
                    parts.append(day)
                log.info("PULLED %s %s rows=%d", sym, dt, day.height)
            if not parts:
                log.warning("EMPTY MONTH %s %s -- not written", sym, mo)
                continue
            out = pl.concat(parts).sort("ts")
            dest = BBO_DIR / sym
            dest.mkdir(parents=True, exist_ok=True)
            tmp = dest / f"{mo}.parquet.tmp"
            out.write_parquet(tmp)
            tmp.replace(dest / f"{mo}.parquet")
            wrote += 1
            log.info("WROTE %s %s rows=%d", sym, mo, out.height)
            print(f"  {sym} {mo}: {out.height:,} rows ({wrote}/{len(work)})")
    finally:
        hist.close()
    print(f"done: wrote {wrote} monthly partitions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
