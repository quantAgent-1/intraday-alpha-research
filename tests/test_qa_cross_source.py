"""Synthetic-frame tests for the cross-source QA checks (qa.bar_tape_offset /
qa.bbo_quote_agreement).

No lake access, no network — every frame is built inline and the session bounds
are passed explicitly, so the offset math and threshold logic are pinned down
independent of what lives on disk. The public functions load from the lake ONLY
when a frame argument is None, so supplying both frames keeps these tests pure.
"""

from __future__ import annotations

import polars as pl

from enginev51.data import bbo1s, qa, store

NS = 1_000_000_000
NS_MIN = 60 * NS
# Arbitrary but valid 6.5h RTH window: 2026-01-05 14:30:00Z .. 21:00:00Z.
OPEN_NS = 1_767_623_400 * NS
CLOSE_NS = OPEN_NS + int(6.5 * 3600) * NS
SESSION = "2026-01-05"
BOUNDS = (OPEN_NS, CLOSE_NS)


# --------------------------------------------------------------- bar_tape_offset


def _bars(n_min: int, factor: float = 1.0) -> pl.DataFrame:
    """One 1-min bar per minute from OPEN_NS; vwap = raw_price * factor.

    factor 1.0 = raw lake; factor < 1 mimics a dividend-back-adjusted lake (the
    F1 defect), which reads a constant negative bar-vs-tape offset.
    """
    prices = [100.0 + i * 0.10 for i in range(n_min)]
    ts = [OPEN_NS + i * NS_MIN for i in range(n_min)]
    return pl.DataFrame(
        {
            "ts": ts,
            "open": [p * factor for p in prices],
            "high": [p * factor + 0.05 for p in prices],
            "low": [p * factor - 0.05 for p in prices],
            "close": [p * factor for p in prices],
            "volume": [1000.0] * n_min,
            "trade_count": [10] * n_min,
            "vwap": [p * factor for p in prices],
        },
        schema=store.BARS_SCHEMA,
    )


def _trades(n_min: int, start_min: int = 0) -> pl.DataFrame:
    """Three raw prints per minute at the minute's raw price (tape scale, factor 1)."""
    prices = [100.0 + i * 0.10 for i in range(n_min)]
    ts: list[int] = []
    px: list[float] = []
    for i in range(n_min):
        base = OPEN_NS + (start_min + i) * NS_MIN
        for k in (10, 30, 50):
            ts.append(base + k * NS)
            px.append(prices[i])
    n = len(ts)
    return pl.DataFrame(
        {
            "ts": ts,
            "price": px,
            "size": [100.0] * n,
            "exchange": ["V"] * n,
            "conditions": [""] * n,
            "tape": ["C"] * n,
        },
        schema=store.TRADES_SCHEMA,
    )


def test_bar_tape_clean_raw_lake_zero_offset() -> None:
    res = qa.bar_tape_offset(
        "NVDA", SESSION, bars=_bars(30, factor=1.0), trades=_trades(30),
        session_bounds_ns=BOUNDS,
    )
    assert res["n_minutes"] == 30
    assert abs(res["median_offset_bps"]) < 1e-6
    assert res["max_abs_offset_bps"] < 1e-6
    # threshold logic: a raw lake PASSes
    _txt, ok = qa._fmt_bar_tape(res)
    assert ok is True


def test_bar_tape_adjusted_lake_offset_detected() -> None:
    # factor 0.9988 -> (0.9988 - 1) * 1e4 = -12.0 bps constant offset
    res = qa.bar_tape_offset(
        "MU", SESSION, bars=_bars(40, factor=0.9988), trades=_trades(40),
        session_bounds_ns=BOUNDS,
    )
    assert res["n_minutes"] == 40
    assert abs(res["median_offset_bps"] - (-12.0)) < 0.05
    # threshold logic: a -12 bps offset must NOT pass
    _txt, ok = qa._fmt_bar_tape(res)
    assert ok is False


def test_bar_tape_empty_and_missing_clean() -> None:
    empty_b = pl.DataFrame(schema=store.BARS_SCHEMA)
    empty_t = pl.DataFrame(schema=store.TRADES_SCHEMA)
    res = qa.bar_tape_offset(
        "NVDA", SESSION, bars=empty_b, trades=empty_t, session_bounds_ns=BOUNDS
    )
    assert res["n_minutes"] == 0
    assert res["median_offset_bps"] is None
    assert "no bars" in res["notes"] and "no trades" in res["notes"]
    # bars present but trades empty -> only "no trades"
    res2 = qa.bar_tape_offset(
        "NVDA", SESSION, bars=_bars(5), trades=empty_t, session_bounds_ns=BOUNDS
    )
    assert res2["n_minutes"] == 0 and res2["median_offset_bps"] is None
    assert "no trades" in res2["notes"]
    # a WARN (no data) is reported cleanly, not as a pass
    _txt, ok = qa._fmt_bar_tape(res)
    assert ok is False


def test_bar_tape_no_overlapping_minutes() -> None:
    # bars in minutes 0..4, trades in minutes 100..104 -> no shared minute
    res = qa.bar_tape_offset(
        "NVDA", SESSION, bars=_bars(5), trades=_trades(5, start_min=100),
        session_bounds_ns=BOUNDS,
    )
    assert res["n_minutes"] == 0
    assert res["median_offset_bps"] is None
    assert "no overlapping RTH minutes" in res["notes"]


# ------------------------------------------------------------ bbo_quote_agreement


def _quotes(mid: float = 100.01, spread: float = 0.02) -> pl.DataFrame:
    """1-min-spaced SIP quotes spanning the whole window, constant mid."""
    ts = [OPEN_NS + i * NS_MIN for i in range(0, 391)]
    n = len(ts)
    bid = round(mid - spread / 2, 4)
    ask = round(mid + spread / 2, 4)
    return pl.DataFrame(
        {
            "ts": ts,
            "bid": [bid] * n,
            "bid_size": [5.0] * n,
            "bid_exchange": ["V"] * n,
            "ask": [ask] * n,
            "ask_size": [5.0] * n,
            "ask_exchange": ["V"] * n,
            "conditions": [""] * n,
            "tape": ["C"] * n,
        },
        schema=store.QUOTES_SCHEMA,
    )


def _bbo(mid: float = 100.01, spread: float = 0.02) -> pl.DataFrame:
    """1s-spaced XNAS bbo-1s snapshots spanning the window, constant mid."""
    ts = list(range(OPEN_NS, CLOSE_NS + 1, NS))
    n = len(ts)
    bid = round(mid - spread / 2, 4)
    ask = round(mid + spread / 2, 4)
    return pl.DataFrame(
        {
            "ts": ts,
            "bid": [bid] * n,
            "ask": [ask] * n,
            "bid_size": [3.0] * n,
            "ask_size": [3.0] * n,
        },
        schema=bbo1s.BBO_SCHEMA,
    )


def test_bbo_quote_agree_within_tick() -> None:
    res = qa.bbo_quote_agreement(
        "NVDA", SESSION, bbo=_bbo(mid=100.01), quotes=_quotes(mid=100.01),
        session_bounds_ns=BOUNDS,
    )
    assert res["n_samples"] == 25  # 15-min marks strictly inside 390-min window
    assert res["median_abs_ticks"] == 0.0
    assert res["n_flagged"] == 0
    _txt, ok = qa._fmt_bbo_quote(res)
    assert ok is True


def test_bbo_quote_disagreement_flagged() -> None:
    # bbo mid 3 ticks above the SIP mid at every sample instant
    res = qa.bbo_quote_agreement(
        "NVDA", SESSION, bbo=_bbo(mid=100.04), quotes=_quotes(mid=100.01),
        session_bounds_ns=BOUNDS,
    )
    assert res["n_samples"] == 25
    assert abs(res["median_abs_ticks"] - 3.0) < 1e-6
    assert res["max_abs_ticks"] >= 3.0
    assert res["n_flagged"] == 25  # every sample exceeds the 2-tick flag
    _txt, ok = qa._fmt_bbo_quote(res)
    assert ok is False


def test_bbo_quote_empty_and_missing_clean() -> None:
    empty_bbo = pl.DataFrame(schema=bbo1s.BBO_SCHEMA)
    empty_q = pl.DataFrame(schema=store.QUOTES_SCHEMA)
    res = qa.bbo_quote_agreement(
        "NVDA", SESSION, bbo=empty_bbo, quotes=empty_q, session_bounds_ns=BOUNDS
    )
    assert res["n_samples"] == 0
    assert res["median_abs_ticks"] is None
    assert "no bbo1s" in res["notes"] and "no quotes" in res["notes"]
    _txt, ok = qa._fmt_bbo_quote(res)
    assert ok is False


def test_bbo_quote_one_sided_book_noted() -> None:
    # all-crossed SIP quotes (bid > ask) -> nothing two-sided to mid
    crossed = _quotes(mid=100.01).with_columns(
        pl.lit(100.05).alias("bid"), pl.lit(100.00).alias("ask")
    )
    res = qa.bbo_quote_agreement(
        "NVDA", SESSION, bbo=_bbo(mid=100.01), quotes=crossed, session_bounds_ns=BOUNDS
    )
    assert res["n_samples"] == 0
    assert res["median_abs_ticks"] is None
    assert any("two-sided" in nnote for nnote in res["notes"])


def test_bad_session_returns_clean_dict() -> None:
    # a non-calendar / malformed session must not raise (no bounds derivable)
    res = qa.bar_tape_offset("NVDA", "not-a-date")
    assert res["n_minutes"] == 0 and res["median_offset_bps"] is None
    assert res["notes"]
    res2 = qa.bbo_quote_agreement("NVDA", "not-a-date")
    assert res2["n_samples"] == 0 and res2["median_abs_ticks"] is None
    assert res2["notes"]
