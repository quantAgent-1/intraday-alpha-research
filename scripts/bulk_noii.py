"""One-shot BULK NOII fetch: ONE request per symbol for the full window, then
split to the monthly partitions the rest of the code expects. ~50x fewer
requests than the per-month loop (same data, same cost). Cost-guarded; skips
symbols already fully present.

    uv run python scripts/bulk_noii.py --max-cost 46
"""
from __future__ import annotations

import sys

import databento as db
import polars as pl

from enginev51.config import get_settings
from enginev51.data.noii import (
    DATASET,
    SCHEMA,
    _month_range,
    _write_atomic,
    noii_root,
    normalize_imbalance_df,
    partition_path,
)

NEW = [
    "AAPL", "MSFT", "AVGO", "QCOM", "AMAT", "MRVL", "LRCX", "KLAC", "ADBE", "CSCO",
    "INTC", "TXN", "INTU", "META", "NFLX", "TMUS", "CMCSA", "PEP", "COST", "SBUX",
    "MDLZ", "AMGN", "GILD", "VRTX", "ISRG", "HON", "BKNG", "PLTR",
]
START, END_EXCL = "2023-01-03", "2026-07-16"  # 3.5y window (ample OOS, ~half the data)
MONTHS = _month_range(__import__("datetime").date(2023, 1, 3),
                      __import__("datetime").date(2026, 7, 15))


def main() -> None:
    max_cost = float(sys.argv[sys.argv.index("--max-cost") + 1]) if "--max-cost" in sys.argv else 46.0
    s = get_settings()
    client = db.Historical(s.databento_api_key)
    root = noii_root()

    todo = [
        sym for sym in NEW
        if not all(partition_path(root, sym, m).exists() for m in MONTHS)
    ]
    print(f"symbols needing data: {len(todo)}/{len(NEW)} -> {todo}", flush=True)
    if not todo:
        print("ALL PRESENT", flush=True)
        return

    quoted = float(client.metadata.get_cost(
        dataset=DATASET, symbols=todo, schema=SCHEMA, start=START, end=END_EXCL))
    print(f"BULK quote for {len(todo)} symbols: ${quoted:.2f} (guard ${max_cost:.2f})", flush=True)
    if quoted > max_cost:
        raise SystemExit(f"quote ${quoted:.2f} > guard ${max_cost:.2f} — aborting, $0 charged")

    for i, sym in enumerate(todo, 1):
        data = client.timeseries.get_range(
            dataset=DATASET, symbols=[sym], schema=SCHEMA, start=START, end=END_EXCL)
        raw = data.to_df(price_type="float", pretty_ts=True)
        norm = normalize_imbalance_df(pl.from_pandas(raw.reset_index())) if raw.shape[0] else None
        if norm is None or norm.height == 0:
            print(f"[{i}/{len(todo)}] {sym}: EMPTY", flush=True)
            continue
        norm = norm.with_columns(
            pl.from_epoch(pl.col("ts"), time_unit="ns").dt.convert_time_zone("America/New_York")
            .dt.strftime("%Y-%m").alias("_m"))
        for m in norm["_m"].unique().to_list():
            part = norm.filter(pl.col("_m") == m).drop("_m").sort("ts")
            _write_atomic(part, partition_path(root, sym, m))
        print(f"[{i}/{len(todo)}] {sym}: {norm.height:,} msgs -> {norm['_m'].n_unique()} months", flush=True)
    print("BULK COMPLETE", flush=True)


if __name__ == "__main__":
    main()
