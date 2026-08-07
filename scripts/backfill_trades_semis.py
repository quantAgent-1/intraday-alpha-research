"""Backfill raw SIP trades for the five semis into the EXISTING trades lake.

Purpose (R2-A prong-0 data leg; ledger row `R2A-prong0-predeclaration`,
2026-07-23T17:43Z): the semis-5 (KLAC, MRVL, LRCX, TXN, AMAT) have no `trades`
partitions yet. This script backfills them, session by session, into the same
daily-partition lake used by the existing trades (MU/NVDA/TSLA/AMD/GOOGL) with
byte-identical layout, schema, and time-of-day convention. It NEVER overwrites
an existing partition and touches no other lake file.

VERIFIED lake conventions (read from data/raw/sip/trades/MU/2024-01-02.parquet
and AMD/NVDA samples before writing anything):
  * layout   : data/raw/sip/trades/{SYM}/{YYYY-MM-DD}.parquet, one file/session.
  * schema   : ts(Int64 UTC epoch ns), price(f64), size(f64), exchange(Utf8),
               conditions(Utf8), tape(Utf8) -- exactly store.TRADES_SCHEMA.
  * time span: RTH-ONLY. Existing files span 09:30:00..15:59:59 ET (NOT the
               full 04:00-20:00 pre/post session). This backfill matches that:
               request window = [09:30:00, 16:00:00) ET per session and a
               defensive re-filter to that window keeps the convention exact.
  * conditions encoding: the per-trade condition list is joined with '|'
               (e.g. "@|I", "@|F|I"). Produced verbatim by
               AlpacaHist.fetch_trades ('|'.join(c)); reused here so the
               encoding cannot drift.

IMPLEMENTATION CHOICES where the spec is silent (simplest faithful):
  * Session calendar: ET session dates from data/raw/sip/bars1d/KLAC.parquet in
    [2024-01-02, 2026-05-31] (604 sessions; verified identical set for all five
    semis and the megacaps -- symmetric diff 0 -- so KLAC is a safe reference).
  * Client: reuse enginev51.data.alpaca_hist.AlpacaHist.fetch_trades (paged,
    limit=10000, follows next_page_token, SIP feed, auth from repo Settings/.env
    -- same variable names as engineV2). Its sliding-window limiter is overridden
    to REQ_PER_MIN=150 to stay safely under the ~200 req/min free-tier ceiling.
  * Retries/backoff: AlpacaHist._get already honors Retry-After on 429 and does
    bounded exponential backoff on transport/5xx errors (up to 8 attempts) then
    raises. A per-day try/except turns a persistent failure into a logged skip
    (collected into the end-of-run FAILED list) -- i.e. "retry-with-backoff then
    log-and-skip that day". (The client's cap is 8, not the spec's 5; the
    observable behavior -- back off, then give up and skip -- is identical.)
  * Write path: store.write_partition (atomic tmp+os.replace, zstd, enforces
    TRADES_SCHEMA, sorts by ts). Guarantees schema + ts-sort fidelity for free.
  * Empty day: per spec, write NOTHING and log it (not a zero-row file). These
    liquid semis have no empty RTH sessions in range, so this is defensive only;
    such a day is retried on a later run (not marked complete).
  * dry-run request estimate: per missing day, max(1, ceil(bars1d trade_count /
    10000)). bars1d trade_count ~= raw SIP trade count (measured factor ~1.0 on
    MU 2024-01-02: 139343 vs 136435 raw), so this is a principled per-day page
    count.

Modes:
  --dry-run                 list missing (sym,date) pairs + estimated requests;
                            no network.
  --smoke SYM DATE          fetch exactly one session, write it, print row count,
                            head/tail ts in ET, distinct exchange codes, schema.
  (no flag)                 full resumable backfill over all five semis.

Progress + errors are appended to logs/backfill_trades_semis.log (a FILE, never
piped through tail/head). Console output is ASCII-only and short.
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

from enginev51.config import Settings, get_settings
from enginev51.data import store
from enginev51.data.alpaca_hist import AlpacaHist, RateLimiter

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
REPO = Path(__file__).resolve().parents[1]
BARS1D_DIR = REPO / "data" / "raw" / "sip" / "bars1d"
CALENDAR_REF = BARS1D_DIR / "KLAC.parquet"
LOG_PATH = REPO / "logs" / "backfill_trades_semis.log"

FEED = "sip"
KIND = "trades"
SYMBOLS = ["KLAC", "MRVL", "LRCX", "TXN", "AMAT"]
DATE_LO = "2024-01-02"
DATE_HI = "2026-05-31"          # inclusive; < 2026-06-01 sealed holdout

REQ_PER_MIN = 185              # near the ~200 req/min free-tier ceiling; 429s are honored via Retry-After
PAGE_LIMIT = 10000            # AlpacaHist.fetch_trades page size

ET = ZoneInfo("America/New_York")
RTH_OPEN_SEC = 9 * 3600 + 30 * 60   # 09:30:00
RTH_CLOSE_SEC = 16 * 3600           # 16:00:00 (exclusive)


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def _make_logger() -> logging.Logger:
    log = logging.getLogger("backfill_trades_semis")
    log.setLevel(logging.INFO)
    log.propagate = False
    if not log.handlers:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(fh)
    return log


# --------------------------------------------------------------------------- #
# Calendar + estimates
# --------------------------------------------------------------------------- #
def _et_date_expr() -> pl.Expr:
    return (
        pl.from_epoch(pl.col("ts"), time_unit="ns")
        .dt.convert_time_zone("America/New_York")
        .dt.strftime("%Y-%m-%d")
    )


def session_calendar() -> list[str]:
    """ET session dates in [DATE_LO, DATE_HI] from the KLAC bars1d reference."""
    b = pl.read_parquet(CALENDAR_REF, columns=["ts"])
    b = b.with_columns(_et_date_expr().alias("d"))
    b = b.filter((pl.col("d") >= DATE_LO) & (pl.col("d") <= DATE_HI)).sort("d")
    return b["d"].to_list()


def bars1d_tradecount_by_date(sym: str) -> dict[str, int]:
    """{ET session date -> daily trade_count} for a symbol's bars1d (estimate)."""
    p = BARS1D_DIR / f"{sym}.parquet"
    if not p.exists():
        return {}
    b = pl.read_parquet(p, columns=["ts", "trade_count"])
    b = b.with_columns(_et_date_expr().alias("d"))
    return {d: int(tc) for d, tc in zip(b["d"].to_list(), b["trade_count"].to_list())}


def est_pages(trade_count: int | None) -> int:
    if not trade_count or trade_count <= 0:
        return 1
    return max(1, math.ceil(trade_count / PAGE_LIMIT))


# --------------------------------------------------------------------------- #
# Fetch + validate + write one session
# --------------------------------------------------------------------------- #
def rth_bounds(date_str: str) -> tuple[datetime, datetime]:
    """[09:30:00, 16:00:00) ET as tz-aware datetimes for one session date."""
    y, m, d = (int(x) for x in date_str.split("-"))
    lo = datetime(y, m, d, 9, 30, 0, tzinfo=ET)
    hi = datetime(y, m, d, 16, 0, 0, tzinfo=ET)
    return lo, hi


def fetch_day(hist: AlpacaHist, sym: str, date_str: str) -> list[dict]:
    lo, hi = rth_bounds(date_str)
    rows: list[dict] = []
    for page in hist.fetch_trades(sym, lo, hi, feed=FEED):
        rows.extend(page)
    return rows


def validate_day(rows: list[dict], date_str: str) -> tuple[list[dict], dict]:
    """Enforce schema, keep RTH-window / correct-date / price>0, sort by ts."""
    if not rows:
        return [], {"raw": 0, "kept": 0, "dropped_oob": 0}
    df = pl.DataFrame(rows, schema=store.TRADES_SCHEMA)
    dt = pl.from_epoch(pl.col("ts"), time_unit="ns").dt.convert_time_zone(
        "America/New_York"
    )
    sec = (
        dt.dt.hour().cast(pl.Int32) * 3600
        + dt.dt.minute().cast(pl.Int32) * 60
        + dt.dt.second().cast(pl.Int32)
    )
    df = df.with_columns(sec.alias("_sec"), dt.dt.strftime("%Y-%m-%d").alias("_d"))
    n_raw = df.height
    good = df.filter(
        (pl.col("_d") == date_str)
        & (pl.col("_sec") >= RTH_OPEN_SEC)
        & (pl.col("_sec") < RTH_CLOSE_SEC)
        & (pl.col("price") > 0)
    )
    n_kept = good.height
    good = good.drop(["_sec", "_d"]).sort("ts")
    stats = {"raw": n_raw, "kept": n_kept, "dropped_oob": n_raw - n_kept}
    return good.to_dicts(), stats


def process_day(
    settings: Settings, hist: AlpacaHist, sym: str, date_str: str, log: logging.Logger
) -> dict:
    """Resumable single-session fetch->validate->write. Never overwrites."""
    if store.partition_exists(settings.raw_dir, FEED, KIND, sym, date_str):
        log.info("SKIP %s %s (file exists)", sym, date_str)
        return {"status": "skip"}
    try:
        rows = fetch_day(hist, sym, date_str)
    except Exception as exc:  # noqa: BLE001 -- log-and-skip per spec
        msg = f"{type(exc).__name__}: {str(exc)[:250]}"
        log.error("FAIL %s %s %s", sym, date_str, msg)
        return {"status": "fail", "error": msg}
    clean, stats = validate_day(rows, date_str)
    if not clean:
        log.info("EMPTY %s %s (raw=%d) -> nothing written", sym, date_str, stats["raw"])
        return {"status": "empty", **stats}
    store.write_partition(settings.raw_dir, FEED, KIND, sym, date_str, clean)
    log.info(
        "WROTE %s %s rows=%d (raw=%d dropped_oob=%d)",
        sym, date_str, stats["kept"], stats["raw"], stats["dropped_oob"],
    )
    return {"status": "wrote", **stats}


# --------------------------------------------------------------------------- #
# Modes
# --------------------------------------------------------------------------- #
def run_dry(settings: Settings, log: logging.Logger) -> None:
    cal = session_calendar()
    print("DRY-RUN backfill_trades_semis")
    print(f"  calendar: {len(cal)} sessions {cal[0]}..{cal[-1]} (KLAC bars1d ref)")
    print(f"  page_limit={PAGE_LIMIT}  est_pages/day=ceil(bars1d_trade_count/limit)")
    total_missing = 0
    total_req = 0
    for sym in SYMBOLS:
        tc = bars1d_tradecount_by_date(sym)
        missing = [
            d for d in cal
            if not store.partition_exists(settings.raw_dir, FEED, KIND, sym, d)
        ]
        req = sum(est_pages(tc.get(d)) for d in missing)
        total_missing += len(missing)
        total_req += req
        print(f"  {sym:5}: missing={len(missing):4}/{len(cal)}  est_requests~{req}")
        log.info("DRYRUN %s missing=%d est_requests=%d", sym, len(missing), req)
    print(f"TOTAL: missing_pairs={total_missing}  est_requests~{total_req}")
    if total_req:
        mins = total_req / REQ_PER_MIN
        print(
            f"  est wall-clock at {REQ_PER_MIN} req/min ~ {mins:.0f} min "
            f"({mins / 60:.1f} h) (network only; excludes write/validate)"
        )
    log.info("DRYRUN TOTAL missing=%d est_requests=%d", total_missing, total_req)


def run_smoke(
    settings: Settings, hist: AlpacaHist, sym: str, date_str: str, log: logging.Logger
) -> int:
    sym = sym.upper()
    print(f"SMOKE {sym} {date_str}")
    res = process_day(settings, hist, sym, date_str, log)
    path = store.partition_path(settings.raw_dir, FEED, KIND, sym, date_str)
    if res["status"] == "fail":
        print(f"  FAILED: {res['error']}")
        return 1
    if res["status"] == "empty":
        print(f"  EMPTY (raw rows={res.get('raw', 0)}) -> nothing written")
        return 1
    if not path.exists():
        print("  ERROR: no file present after process_day")
        return 1
    df = pl.read_parquet(path)
    dt = pl.from_epoch(pl.col("ts"), time_unit="ns").dt.convert_time_zone(
        "America/New_York"
    )
    et = df.with_columns(dt.dt.strftime("%Y-%m-%d %H:%M:%S%.3f").alias("_et"))
    exch = sorted(x for x in df["exchange"].unique().to_list() if x is not None)
    print(f"  status={res['status']}  rows={df.height}")
    print(f"  head ts ET: {et['_et'][0]}")
    print(f"  tail ts ET: {et['_et'][-1]}")
    print(f"  distinct exchanges ({len(exch)}): {exch}")
    print(f"  distinct tape: {sorted(df['tape'].unique().to_list())}")
    print(f"  conditions sample: {df['conditions'][0]!r} .. {df['conditions'][df.height // 2]!r}")
    print(f"  schema: {[(k, str(v)) for k, v in df.schema.items()]}")
    print(f"  file: {path}")
    return 0


def run_full(settings: Settings, hist: AlpacaHist, log: logging.Logger) -> int:
    cal = session_calendar()
    log.info("FULL start: %d symbols x %d sessions", len(SYMBOLS), len(cal))
    print(f"FULL backfill: {len(SYMBOLS)} symbols x {len(cal)} sessions "
          f"{cal[0]}..{cal[-1]}")
    tallies = {s: {"wrote": 0, "skip": 0, "empty": 0, "fail": 0} for s in SYMBOLS}
    failed: list[tuple[str, str, str]] = []
    for sym in SYMBOLS:
        for i, date_str in enumerate(cal, 1):
            res = process_day(settings, hist, sym, date_str, log)
            tallies[sym][res["status"]] = tallies[sym].get(res["status"], 0) + 1
            if res["status"] == "fail":
                failed.append((sym, date_str, res.get("error", "")))
            if i % 25 == 0:
                t = tallies[sym]
                print(f"  {sym}: {i}/{len(cal)} "
                      f"(wrote={t['wrote']} skip={t['skip']} "
                      f"empty={t['empty']} fail={t['fail']})")
        t = tallies[sym]
        line = (f"{sym} DONE wrote={t['wrote']} skip={t['skip']} "
                f"empty={t['empty']} fail={t['fail']}")
        print(f"  {line}")
        log.info(line)
    print("=" * 60)
    print("BACKFILL COMPLETE")
    for sym in SYMBOLS:
        t = tallies[sym]
        print(f"  {sym:5}: wrote={t['wrote']} skip={t['skip']} "
              f"empty={t['empty']} fail={t['fail']}")
    if failed:
        print(f"FAILED days ({len(failed)}) -- re-run to retry:")
        for sym, d, err in failed:
            print(f"  {sym} {d}: {err}")
        log.info("FULL end: %d failed days", len(failed))
    else:
        print("No failed days.")
        log.info("FULL end: no failed days")
    return 1 if failed else 0


# --------------------------------------------------------------------------- #
# Entry
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Backfill SIP trades for the semis-5.")
    ap.add_argument("--dry-run", action="store_true",
                    help="List missing (sym,date) pairs + estimated requests; no fetch.")
    ap.add_argument("--smoke", nargs=2, metavar=("SYM", "DATE"),
                    help="Fetch/write exactly one session and print diagnostics.")
    args = ap.parse_args(argv)

    log = _make_logger()
    settings = get_settings()

    if args.dry_run:
        run_dry(settings, log)
        return 0

    # Modes below need the network client; construct it now so cred errors STOP us.
    try:
        hist = AlpacaHist(settings)
    except Exception as exc:  # noqa: BLE001
        print("CREDENTIAL/CLIENT ERROR -- stopping (no auth improvisation):")
        print(f"  {type(exc).__name__}: {exc}")
        log.error("CLIENT INIT FAIL %s: %s", type(exc).__name__, exc)
        return 2
    hist.limiter = RateLimiter(REQ_PER_MIN)  # cap under ~200 req/min

    try:
        if args.smoke:
            return run_smoke(settings, hist, args.smoke[0], args.smoke[1], log)
        return run_full(settings, hist, log)
    finally:
        hist.close()


if __name__ == "__main__":
    sys.exit(main())
