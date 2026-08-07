"""Synthetic-frame tests for the data-quality audit.

No lake access here — all frames are built inline so the logic is pinned down
independent of what happens to live on disk.
"""

from __future__ import annotations

import polars as pl

from enginev51.data import qa

NS = 1_000_000_000
# arbitrary RTH window: 2026-01-05 14:30:00Z open, 21:00:00Z close (6.5h)
OPEN_NS = 1_767_623_400 * NS
CLOSE_NS = OPEN_NS + int(6.5 * 3600) * NS
SESSION = "2026-01-05"
BOUNDS = (OPEN_NS, CLOSE_NS)


def _clean_trades() -> pl.DataFrame:
    # one trade every 10s across the whole RTH window, full schema
    ts = list(range(OPEN_NS, CLOSE_NS + 1, 10 * NS))
    n = len(ts)
    return pl.DataFrame(
        {
            "ts": ts,
            "price": [100.0 + (i % 5) * 0.01 for i in range(n)],
            "size": [100.0] * n,
            "exchange": ["V"] * n,
            "conditions": [""] * n,
            "tape": ["C"] * n,
        },
        schema=qa.store.TRADES_SCHEMA,
    )


def _clean_quotes() -> pl.DataFrame:
    ts = list(range(OPEN_NS, CLOSE_NS + 1, 10 * NS))
    n = len(ts)
    return pl.DataFrame(
        {
            "ts": ts,
            "bid": [100.0] * n,
            "bid_size": [5.0] * n,
            "bid_exchange": ["V"] * n,
            "ask": [100.02] * n,
            "ask_size": [5.0] * n,
            "ask_exchange": ["V"] * n,
            "conditions": [""] * n,
            "tape": ["C"] * n,
        },
        schema=qa.store.QUOTES_SCHEMA,
    )


def test_clean_day_passes() -> None:
    res = qa.audit_day(_clean_trades(), _clean_quotes(), SESSION, BOUNDS)
    assert res["rows_trades"] > 0 and res["rows_quotes"] > 0
    assert res["ts_monotonic_trades"] and res["ts_monotonic_quotes"]
    assert res["ts_within_session_trades"] == 1.0
    assert res["ts_within_session_quotes"] == 1.0
    # 10s cadence with edges touching open/close -> max gap ~10s, well under 60
    assert res["max_gap_s_trades"] <= 11.0
    assert res["max_gap_s_quotes"] <= 11.0
    assert res["crossed_or_locked_frac"] == 0.0
    assert res["nonpositive_price_rows"] == 0
    assert res["nonpositive_size_rows"] == 0
    assert res["spread_bps_p50"] is not None and res["spread_bps_p50"] > 0
    # only benign notes (crossed/gap/out-of-session must be absent)
    joined = " ".join(res["notes"])
    assert "crossed" not in joined
    assert "outside RTH" not in joined


def test_dirty_day_is_flagged() -> None:
    # trades: a 90s gap in the middle + one out-of-session tick before the open
    ts = [OPEN_NS - 60 * NS]  # pre-market tick (out of session)
    ts += list(range(OPEN_NS, OPEN_NS + 100 * NS, 10 * NS))
    ts.append(ts[-1] + 90 * NS)  # 90s gap
    ts += list(range(ts[-1] + 10 * NS, CLOSE_NS + 1, 10 * NS))
    n = len(ts)
    trades = pl.DataFrame(
        {
            "ts": ts,
            "price": [100.0] * n,
            "size": [100.0] * n,
            "exchange": [""] * n,
            "conditions": [""] * n,
            "tape": [""] * n,
        },
        schema=qa.store.TRADES_SCHEMA,
    )
    # quotes: inject a crossed quote (bid > ask)
    q = _clean_quotes()
    q = q.with_columns(
        pl.when(pl.arange(0, q.height) == 3)
        .then(pl.lit(100.05))
        .otherwise(pl.col("bid"))
        .alias("bid")
    )

    res = qa.audit_day(trades, q, SESSION, BOUNDS)
    assert res["max_gap_s_trades"] >= 90.0
    assert res["ts_within_session_trades"] < 1.0  # the pre-market tick
    assert res["crossed_or_locked_frac"] > 0.0
    joined = " ".join(res["notes"])
    assert "outside RTH" in joined
    assert "crossed" in joined


def test_reduced_schema_trades() -> None:
    # legacy 3-column trades: ts, price, size only
    ts = list(range(OPEN_NS, CLOSE_NS + 1, 30 * NS))
    n = len(ts)
    trades = pl.DataFrame(
        {"ts": ts, "price": [50.0] * n, "size": [10.0] * n},
        schema={"ts": pl.Int64, "price": pl.Float64, "size": pl.Float64},
    )
    res = qa.audit_day(trades, None, SESSION, BOUNDS)
    assert res["rows_trades"] == n
    assert res["rows_quotes"] == 0
    assert res["ts_monotonic_trades"]
    assert res["max_gap_s_trades"] is not None
    # crossed/spread undefined without quotes
    assert res["crossed_or_locked_frac"] is None
    assert res["spread_bps_p50"] is None
    assert any("reduced schema" in nnote for nnote in res["notes"])


def test_reduced_schema_quotes() -> None:
    # legacy 5-column quotes: ts, bid, ask, bid_size, ask_size
    ts = list(range(OPEN_NS, CLOSE_NS + 1, 30 * NS))
    n = len(ts)
    quotes = pl.DataFrame(
        {
            "ts": ts,
            "bid": [50.0] * n,
            "ask": [50.03] * n,
            "bid_size": [3.0] * n,
            "ask_size": [3.0] * n,
        },
        schema={
            "ts": pl.Int64,
            "bid": pl.Float64,
            "ask": pl.Float64,
            "bid_size": pl.Float64,
            "ask_size": pl.Float64,
        },
    )
    res = qa.audit_day(None, quotes, SESSION, BOUNDS)
    assert res["rows_quotes"] == n
    assert res["crossed_or_locked_frac"] == 0.0
    assert res["spread_bps_p50"] is not None and res["spread_bps_p50"] > 0
    assert any("reduced schema" in nnote for nnote in res["notes"])


def test_empty_frames() -> None:
    empty_t = pl.DataFrame(schema=qa.store.TRADES_SCHEMA)
    empty_q = pl.DataFrame(schema=qa.store.QUOTES_SCHEMA)
    res = qa.audit_day(empty_t, empty_q, SESSION, BOUNDS)
    assert res["rows_trades"] == 0 and res["rows_quotes"] == 0
    assert res["ts_monotonic_trades"] and res["ts_monotonic_quotes"]
    assert res["ts_within_session_trades"] is None
    assert res["ts_within_session_quotes"] is None
    # empty -> whole session counts as the gap
    assert res["max_gap_s_trades"] == (CLOSE_NS - OPEN_NS) / NS
    assert res["crossed_or_locked_frac"] is None
    assert "no trades" in res["notes"] and "no quotes" in res["notes"]


def test_none_frames() -> None:
    res = qa.audit_day(None, None, SESSION, BOUNDS)
    assert res["rows_trades"] == 0 and res["rows_quotes"] == 0
    assert res["max_gap_s_trades"] is not None
    assert res["notes"]
