"""Regular RTH minute grid per session.

Raw 1-min bars are irregular (minutes with no trades are absent). Every feature
and label in the slow family is computed on a *complete* per-session grid so that
row-shifts equal minute-shifts exactly and no window ever spans two sessions.

Notes:
- Bars are fetched with adjustment=all (split+dividend back-adjusted), so
  cross-day price ratios (gaps, multi-day returns) are consistent. This is the
  standard mild point-in-time impurity (a future split rescales history); all
  intraday-relative features are unaffected.
- `is_real` marks minutes with an actual bar; synthetic minutes carry the
  forward-filled close (degenerate OHLC) and zero volume.
- Rows are stamped at bar OPEN (`_session_skeleton`: ``ts = open_ns + i*NS_PER_MIN``)
  but their feature contents include that same bar's CLOSE, so a row is only
  *available* to a real-time consumer one bar later. See
  ``PRED_STAMP_TO_AVAILABILITY_NS`` for the producer->consumer lag contract
  (research/SIM_AUDIT_2026-07-21.md §3, defect F2).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import polars as pl

from enginev51.data import calendar as cal

NS_PER_MIN = 60_000_000_000

# Producer->consumer availability contract (SIM_AUDIT_2026-07-21 §3, defect F2).
#
# Grid/pred rows are stamped at bar OPEN (`_session_skeleton`:
# ``ts = open_ns + i * NS_PER_MIN``), but a row's feature contents include that
# same bar's CLOSE and are therefore knowable — available to any real-time
# consumer — only at ``ts + PRED_STAMP_TO_AVAILABILITY_NS`` (one bar later).
# The shipped pred parquets under data/preds/ keep the open stamp (they are NOT
# regenerated); consumers (plans/overlay_a1, plans/overlay_m4) MUST lag their
# lookup by this constant so a decision at instant T only reads rows stamped at
# or before T - one bar.
PRED_STAMP_TO_AVAILABILITY_NS = 60 * 1_000_000_000  # one 1-min bar


def _session_skeleton(days: list[date]) -> pl.DataFrame:
    """Rows (session, minute_idx, n_minutes, ts) for every RTH minute of every session."""
    sessions: list[str] = []
    minute_idx: list[int] = []
    n_minutes_col: list[int] = []
    ts: list[int] = []
    for d in days:
        op, clse = cal.session_bounds_utc(d)
        open_ns = int(op.timestamp() * 1e9)
        n = int((clse - op).total_seconds() // 60)
        for i in range(n):
            sessions.append(d.isoformat())
            minute_idx.append(i)
            n_minutes_col.append(n)
            ts.append(open_ns + i * NS_PER_MIN)
    return pl.DataFrame(
        {
            "session": sessions,
            "minute_idx": minute_idx,
            "n_minutes": n_minutes_col,
            "ts": ts,
        },
        schema={"session": pl.Utf8, "minute_idx": pl.Int32, "n_minutes": pl.Int32, "ts": pl.Int64},
    )


def _ts_date_utc(ns: int) -> date:
    return datetime.fromtimestamp(ns / 1e9, tz=UTC).date()


def build_session_grid(bars: pl.DataFrame, symbol: str) -> pl.DataFrame:
    """bars (raw lake schema, any hours) → complete RTH grid with ffilled prices.

    Output columns: symbol, session, minute_idx, n_minutes, ts, open/high/low/close,
    volume, trade_count, vwap, dollar_vol, is_real, prev_close, gap_open,
    premarket_dv.
    """
    if bars.height == 0:
        raise ValueError(f"no bars for {symbol}")

    days = cal.trading_days(_ts_date_utc(bars["ts"].min()), _ts_date_utc(bars["ts"].max()))
    skel = _session_skeleton(days)

    joined = (
        skel.join(bars, on="ts", how="left")
        .sort("ts")
        .with_columns(
            pl.col("close").forward_fill().over("session"),
            pl.col("vwap").forward_fill().over("session"),
            pl.col("volume").fill_null(0.0),
            pl.col("trade_count").fill_null(0),
            pl.col("open").is_not_null().alias("is_real"),
        )
        .with_columns(
            pl.col("open").fill_null(pl.col("close")),
            pl.col("high").fill_null(pl.col("close")),
            pl.col("low").fill_null(pl.col("close")),
            # per-bar vwap of 0.0 (missing) → close
            pl.when((pl.col("vwap").is_null()) | (pl.col("vwap") <= 0.0))
            .then(pl.col("close"))
            .otherwise(pl.col("vwap"))
            .alias("vwap"),
        )
        # leading minutes of a session before the first trade: drop (no price yet)
        .filter(pl.col("close").is_not_null())
        .with_columns((pl.col("vwap") * pl.col("volume")).alias("dollar_vol"))
    )

    # previous-session RTH close and the overnight gap
    sess_last = (
        joined.group_by("session")
        .agg(pl.col("close").last().alias("_sess_close"))
        .sort("session")
        .with_columns(pl.col("_sess_close").shift(1).alias("prev_close"))
        .drop("_sess_close")
    )

    # pre-market dollar volume (04:00 ET → open) per session, from the raw bars
    et_expr = pl.from_epoch(pl.col("ts"), time_unit="ns").dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York")
    pre = (
        bars.with_columns(
            et_expr.dt.date().cast(pl.Utf8).alias("session"),
            (et_expr.dt.hour() * 60 + et_expr.dt.minute()).alias("_et_min"),
            (pl.col("close") * pl.col("volume")).alias("_dv"),
        )
        .filter((pl.col("_et_min") >= 4 * 60) & (pl.col("_et_min") < 9 * 60 + 30))
        .group_by("session")
        .agg(pl.col("_dv").sum().alias("premarket_dv"))
    )

    out = (
        joined.join(sess_last, on="session", how="left")
        .join(pre, on="session", how="left")
        .with_columns(
            pl.col("premarket_dv").fill_null(0.0),
            pl.lit(symbol.upper()).alias("symbol"),
            (pl.col("close") / pl.col("prev_close")).log().alias("gap_open_raw"),
        )
        .with_columns(
            pl.when(pl.col("minute_idx") == 0)
            .then(pl.col("gap_open_raw"))
            .otherwise(None)
            .forward_fill()
            .over("session")
            .alias("gap_open"),
        )
        .drop("gap_open_raw")
        .sort("ts")
    )
    return out
