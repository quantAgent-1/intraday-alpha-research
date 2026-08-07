"""Forward labels: multi-horizon mid returns + excursion paths (MFE/MAE).

All labels are mid-to-mid (bar close as mid proxy — adequate at 30 min+ on
liquid names); execution costs are charged by the cost model at evaluation
time, never baked into labels (PROTOCOL §3).

Session safety: forward shifts use .over(session); forward rolling extrema use
the descending-sort trick with an explicit rows-remaining mask, so no label
ever crosses a session boundary. Labels are null when the horizon doesn't fit.
"""

from __future__ import annotations

import polars as pl

HORIZONS_MIN = (30, 60, 120, 240)

LABEL_COLS: tuple[str, ...] = tuple(
    [f"l_fwd_{h}m" for h in HORIZONS_MIN]
    + ["l_fwd_close"]
    + [f"l_mfe_{h}m" for h in HORIZONS_MIN]
    + [f"l_mae_{h}m" for h in HORIZONS_MIN]
)


def add_labels(df: pl.DataFrame) -> pl.DataFrame:
    if df["symbol"].n_unique() > 1:
        raise ValueError("add_labels expects a single-symbol frame")

    df = df.sort("ts").with_columns(
        pl.int_range(pl.len()).over("session").alias("_row"),
        pl.len().over("session").alias("_total"),
    )
    df = df.with_columns((pl.col("_total") - 1 - pl.col("_row")).alias("_rows_after"))

    # forward returns (session-scoped shifts)
    df = df.with_columns(
        [
            (pl.col("close").shift(-h) / pl.col("close")).log().over("session").alias(f"l_fwd_{h}m")
            for h in HORIZONS_MIN
        ]
        + [
            (pl.col("close").last().over("session") / pl.col("close")).log().alias("l_fwd_close"),
        ]
    )

    # forward extrema over (t+1 .. t+h): descending sort, shift(1), trailing rolling
    desc = df.sort("ts", descending=True).with_columns(
        [
            pl.col("high")
            .shift(1)
            .rolling_max(window_size=h, min_samples=h)
            .alias(f"_fmax_{h}")
            for h in HORIZONS_MIN
        ]
        + [
            pl.col("low")
            .shift(1)
            .rolling_min(window_size=h, min_samples=h)
            .alias(f"_fmin_{h}")
            for h in HORIZONS_MIN
        ]
    )
    df = desc.sort("ts")

    for h in HORIZONS_MIN:
        df = df.with_columns(
            pl.when(pl.col("_rows_after") >= h)
            .then((pl.col(f"_fmax_{h}") / pl.col("close")).log())
            .otherwise(None)
            .alias(f"l_mfe_{h}m"),
            pl.when(pl.col("_rows_after") >= h)
            .then((pl.col(f"_fmin_{h}") / pl.col("close")).log())
            .otherwise(None)
            .alias(f"l_mae_{h}m"),
        )

    return df.drop(
        ["_row", "_total", "_rows_after"]
        + [f"_fmax_{h}" for h in HORIZONS_MIN]
        + [f"_fmin_{h}" for h in HORIZONS_MIN]
    )
