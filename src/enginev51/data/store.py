"""Parquet lake for raw market data.

Layout (all under settings.raw_dir):
    {feed}/bars1m/{SYMBOL}/{YYYY-MM}.parquet          monthly partitions
    {feed}/event_bars1s/{SYMBOL}/{YYYY-MM-DD}.parquet daily partitions
    {feed}/trades/{SYMBOL}/{YYYY-MM-DD}.parquet       daily partitions
    {feed}/quotes/{SYMBOL}/{YYYY-MM-DD}.parquet       daily partitions

All timestamps are UTC epoch nanoseconds (Int64 column "ts").
Files are written atomically (tmp + os.replace); a present file marks that
partition complete, which is what makes backfill resumable. An empty partition
(holiday / not-yet-listed) is written as a zero-row parquet with full schema.

ZERO-ROW RULE (code review 2026-07-28 B5). Presence alone is the resume marker,
so an ACCIDENTAL zero-row primary (a bad response on a liquid RTH session) would
permanently hole that name-day under primary-first dual-root reads. The lake
therefore carries an explicit intent marker beside the partition:

    {feed}/{kind}/{SYMBOL}/{part}.parquet.empty_ok

Written only when a caller declares the emptiness INTENTIONAL
(``write_partition(..., empty_ok=True)`` / ``mark_empty_ok``). The rule:

  * zero rows + sidecar  -> genuinely empty (unlisted name, no prints): COMPLETE
  * zero rows, no sidecar -> UNKNOWN, treated as incomplete by content-completeness
    checks (``backfill.partition_complete``) — never by the default presence check

Nothing here re-verdicts the existing lake: no sidecar is written unless asked
for, and the default presence-based path (``partition_exists``) is unchanged.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import polars as pl

# Sidecar suffix marking a zero-row partition as intentionally empty (see docs).
EMPTY_OK_SUFFIX = ".empty_ok"

BARS_SCHEMA: dict[str, pl.DataType] = {
    "ts": pl.Int64,
    "open": pl.Float64,
    "high": pl.Float64,
    "low": pl.Float64,
    "close": pl.Float64,
    "volume": pl.Float64,
    "trade_count": pl.Int64,
    "vwap": pl.Float64,
}

TRADES_SCHEMA: dict[str, pl.DataType] = {
    "ts": pl.Int64,
    "price": pl.Float64,
    "size": pl.Float64,
    "exchange": pl.Utf8,
    "conditions": pl.Utf8,
    "tape": pl.Utf8,
}

QUOTES_SCHEMA: dict[str, pl.DataType] = {
    "ts": pl.Int64,
    "bid": pl.Float64,
    "bid_size": pl.Float64,
    "bid_exchange": pl.Utf8,
    "ask": pl.Float64,
    "ask_size": pl.Float64,
    "ask_exchange": pl.Utf8,
    "conditions": pl.Utf8,
    "tape": pl.Utf8,
}

# v5.1: event_bars1s — 1-second event bars share the OHLCV bar shape but are
# stored in daily partitions (like trades/quotes), same zstd/atomic-write path.
_SCHEMAS = {
    "bars1m": BARS_SCHEMA,
    "event_bars1s": BARS_SCHEMA,
    "trades": TRADES_SCHEMA,
    "quotes": QUOTES_SCHEMA,
}


def partition_path(raw_dir: Path, feed: str, kind: str, symbol: str, part: str) -> Path:
    """part = 'YYYY-MM' for bars1m, 'YYYY-MM-DD' for event_bars1s/trades/quotes."""
    return raw_dir / feed / kind / symbol.upper() / f"{part}.parquet"


def empty_ok_path(raw_dir: Path, feed: str, kind: str, symbol: str, part: str) -> Path:
    """Sidecar marking a zero-row partition as INTENTIONALLY empty (see module docs).

    Sits next to the partition as ``{part}.parquet.empty_ok`` — outside the
    ``*.parquet`` glob every scanner uses, so it can never enter a read path.
    """
    p = partition_path(raw_dir, feed, kind, symbol, part)
    return p.parent / (p.name + EMPTY_OK_SUFFIX)


def month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def write_partition(
    raw_dir: Path,
    feed: str,
    kind: str,
    symbol: str,
    part: str,
    rows: list[dict],
    *,
    empty_ok: bool = False,
) -> Path:
    """Write one partition atomically. Empty rows → zero-row file with full schema.

    ``empty_ok=True`` additionally declares a ZERO-ROW result intentional and drops
    the ``.empty_ok`` sidecar (module docs / B5). Default ``False`` leaves the write
    byte-identical to the historical behaviour — no sidecar, nothing re-verdicted.
    A non-empty write always clears any stale sidecar.
    """
    schema = _SCHEMAS[kind]
    df = pl.DataFrame(rows, schema=schema) if rows else pl.DataFrame(schema=schema)
    if df.height:
        df = df.sort("ts")
    path = partition_path(raw_dir, feed, kind, symbol, part)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".parquet.tmp")
    df.write_parquet(tmp, compression="zstd")
    os.replace(tmp, path)
    if df.height:
        empty_ok_path(raw_dir, feed, kind, symbol, part).unlink(missing_ok=True)
    elif empty_ok:
        mark_empty_ok(raw_dir, feed, kind, symbol, part)
    return path


def mark_empty_ok(raw_dir: Path, feed: str, kind: str, symbol: str, part: str) -> Path:
    """Declare an existing zero-row partition intentionally empty (writes the sidecar)."""
    p = empty_ok_path(raw_dir, feed, kind, symbol, part)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()
    return p


def is_empty_ok(raw_dir: Path, feed: str, kind: str, symbol: str, part: str) -> bool:
    """True when this partition's emptiness has been declared intentional."""
    return empty_ok_path(raw_dir, feed, kind, symbol, part).exists()


def partition_exists(raw_dir: Path, feed: str, kind: str, symbol: str, part: str) -> bool:
    return partition_path(raw_dir, feed, kind, symbol, part).exists()


def partition_height(path: Path) -> int:
    """Row count of one partition file (0 = the zero-row completeness marker)."""
    return int(pl.scan_parquet(path).select(pl.len()).collect().item())


def partition_max_ts(path: Path) -> int | None:
    """max(ts) of one partition file (UTC epoch ns), or None when it has no rows."""
    v = pl.scan_parquet(path).select(pl.col("ts").max()).collect().item()
    return None if v is None else int(v)


def scan_kind(raw_dir: Path, feed: str, kind: str, symbol: str) -> pl.LazyFrame:
    """Lazy scan over every partition of one symbol/kind (empty LazyFrame if none)."""
    root = raw_dir / feed / kind / symbol.upper()
    files = sorted(root.glob("*.parquet"))
    if not files:
        return pl.DataFrame(schema=_SCHEMAS[kind]).lazy()
    return pl.scan_parquet([str(f) for f in files])


def scan_kind_multi(
    roots: tuple[Path, ...], feed: str, kind: str, symbol: str
) -> pl.LazyFrame:
    """Lazy scan across multiple lake roots (e.g. new lake + engineV5's, read-only).

    Roots are searched in order; the FIRST root containing a given partition
    filename wins (primary-first dedup), so a repaired/re-downloaded partition in
    the new lake shadows the legacy copy without touching it.
    """
    seen: dict[str, Path] = {}
    for root in roots:
        d = root / feed / kind / symbol.upper()
        if not d.is_dir():
            continue
        for f in d.glob("*.parquet"):
            seen.setdefault(f.name, f)
    if not seen:
        return pl.DataFrame(schema=_SCHEMAS[kind]).lazy()
    return pl.scan_parquet([str(seen[name]) for name in sorted(seen)])


def load_bars(
    raw_dir: Path | tuple[Path, ...],
    feed: str,
    symbol: str,
    start_ns: int | None = None,
    end_ns: int | None = None,
) -> pl.DataFrame:
    roots = raw_dir if isinstance(raw_dir, tuple) else (raw_dir,)
    lf = scan_kind_multi(roots, feed, "bars1m", symbol)
    if start_ns is not None:
        lf = lf.filter(pl.col("ts") >= start_ns)
    if end_ns is not None:
        lf = lf.filter(pl.col("ts") < end_ns)
    return lf.sort("ts").collect()
