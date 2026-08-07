"""Build 1-second event bars from the trades/quotes lake.

Usage:
    uv run python -m enginev51.apps.build_event_bars \
        --symbols NVDA,TSLA,AMD,MU [--start 2026-05-29 --end 2026-05-29] [--force]

For each (symbol, session) that has a trades partition somewhere in the read
roots (primary lake first, engineV5 legacy second), this loads that day's
trades + quotes, computes the event bars, and writes an ``event_bars1s`` daily
partition to the PRIMARY raw_dir.

event_bars1s uses its own wider schema, so this bypasses store._SCHEMAS and
writes with the frame's own schema via the same atomic tmp + os.replace pattern.
Resumable: an existing partition is skipped unless --force. Quotes may be missing
for some days (e.g. TSLA) -> build with quotes_df=None and log a note.
"""

from __future__ import annotations

import os
import time
from datetime import date
from pathlib import Path

import click
import polars as pl
import structlog

from enginev51.config import get_settings
from enginev51.data import calendar
from enginev51.data.store import partition_path
from enginev51.events.event_bars import build_event_bars

log = structlog.get_logger(__name__)

FEED = "sip"


def _find_partition(
    roots: tuple[Path, ...], kind: str, symbol: str, day: str
) -> Path | None:
    """First existing partition file for (kind, symbol, day), primary root first."""
    for root in roots:
        p = partition_path(root, FEED, kind, symbol, day)
        if p.exists():
            return p
    return None


def _available_days(roots: tuple[Path, ...], symbol: str) -> list[str]:
    """Sorted union of trades-partition day keys (YYYY-MM-DD) across roots."""
    days: set[str] = set()
    for root in roots:
        d = root / FEED / "trades" / symbol.upper()
        if d.is_dir():
            for f in d.glob("*.parquet"):
                days.add(f.stem)
    return sorted(days)


def _session_bounds_ns(day: date) -> tuple[int, int]:
    op, cl = calendar.session_bounds_utc(day)
    return int(op.timestamp() * 1e9), int(cl.timestamp() * 1e9)


def _write_event_bars(raw_dir: Path, symbol: str, day: str, df: pl.DataFrame) -> Path:
    """Atomic write with the frame's own (wider) schema; bypasses store._SCHEMAS."""
    path = partition_path(raw_dir, FEED, "event_bars1s", symbol, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".parquet.tmp")
    df.write_parquet(tmp, compression="zstd")
    os.replace(tmp, path)
    return path


def _build_one(
    settings, symbol: str, day: str, force: bool
) -> str:
    """Build+write one (symbol, day). Returns a status string for the caller."""
    roots = settings.read_roots
    out_path = partition_path(settings.raw_dir, FEED, "event_bars1s", symbol, day)
    if out_path.exists() and not force:
        return "skip_exists"

    tpath = _find_partition(roots, "trades", symbol, day)
    if tpath is None:
        return "no_trades"

    try:
        d = date.fromisoformat(day)
    except ValueError:
        log.warning("bad_day_key", symbol=symbol, day=day)
        return "bad_day"
    try:
        open_ns, close_ns = _session_bounds_ns(d)
    except ValueError:
        log.warning("not_trading_day", symbol=symbol, day=day)
        return "not_trading_day"

    trades_df = pl.read_parquet(tpath)
    qpath = _find_partition(roots, "quotes", symbol, day)
    if qpath is None:
        quotes_df = None
        log.info("quotes_missing", symbol=symbol, day=day, note="quote fields null/0")
    else:
        quotes_df = pl.read_parquet(qpath)

    t0 = time.perf_counter()
    bars = build_event_bars(trades_df, quotes_df, open_ns, close_ns)
    dt_s = time.perf_counter() - t0
    path = _write_event_bars(settings.raw_dir, symbol, day, bars)
    log.info(
        "built",
        symbol=symbol,
        day=day,
        rows=bars.height,
        trades=trades_df.height,
        quotes=(0 if quotes_df is None else quotes_df.height),
        seconds=round(dt_s, 2),
        path=str(path),
    )
    return "ok"


@click.command()
@click.option("--symbols", required=True, help="Comma-separated, e.g. NVDA,TSLA,AMD,MU")
@click.option("--start", default=None, help="First session YYYY-MM-DD (inclusive)")
@click.option("--end", default=None, help="Last session YYYY-MM-DD (inclusive)")
@click.option("--force", is_flag=True, help="Rebuild even if the partition exists")
def main(symbols: str, start: str | None, end: str | None, force: bool) -> None:
    settings = get_settings()
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    counts: dict[str, int] = {}
    for symbol in syms:
        days = _available_days(settings.read_roots, symbol)
        if start:
            days = [d for d in days if d >= start]
        if end:
            days = [d for d in days if d <= end]
        if not days:
            log.warning("no_days", symbol=symbol, start=start, end=end)
            continue
        for day in days:
            status = _build_one(settings, symbol, day, force)
            counts[status] = counts.get(status, 0) + 1
    log.info("done", **counts)


if __name__ == "__main__":
    main()
