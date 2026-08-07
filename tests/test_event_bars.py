"""Tests for the 1-second event-bar builder.

The golden case is a hand-built ~6-second synthetic session. Expected values are
computed BY HAND in the comments below and asserted. NS_PER_S = 1_000_000_000.
"""

from __future__ import annotations

import polars as pl
import pytest

from enginev51.events.event_bars import (
    EVENT_BARS_COLUMNS,
    NS_PER_S,
    build_event_bars,
)

T0 = 1_600_000_000 * NS_PER_S  # arbitrary session open (UTC ns)
CLOSE = T0 + 6 * NS_PER_S       # 6 one-second buckets: seconds 0..5


def _ns(sec: float) -> int:
    return T0 + int(round(sec * NS_PER_S))


# --------------------------------------------------------------------------- #
# GOLDEN synthetic session.
#
# QUOTES (q_ts, bid, bid_size, ask, ask_size):
#   q0 sec0 @0.1  10.00 100  10.10 100   first update -> e0 = 0
#   q1 sec0 @0.6  10.00 300  10.10 100   e1 = 300-100-100+100 = +200   -> OFI sec0 = 200 (increase)
#   q2 sec1 @1.5  10.02 200  10.12 150   e2 = 200 - 0 - 0 + 100 = +300 -> OFI sec1 = 300 (increase)
#   q3 sec2 @2.3  10.01  50  10.11  50   e3 = 0 - 200 - 50 + 0 = -250
#   q4 sec2 @2.7  10.14  80  10.11  60   CROSSED (bid>=ask); e4 = 80 - 0 - 60 + 50 = +70
#                                        OFI sec2 = -250+70 = -180 (decrease); locked_crossed_n=1
#   q5 sec3 @3.4  10.05 100  10.09 100   e5 = 0 - 80 - 100 + 0 = -180 -> OFI sec3 = -180 (decrease)
#   (sec4 no quotes; sec5 no quotes)
#
# TRADES (t_ts, price, size):
#   tr0 sec0 @0.2  10.10 200  first trade sign 0; prev quote q0 -> 10.10>=ask10.10 -> at_ask
#   tr1 sec0 @0.7  10.00 100  10.00<10.10 -> sign -1; prev quote q1 -> 10.00<=bid10.00 -> at_bid
#   tr2 sec1 @1.6  10.12 300  10.12>10.00 -> sign +1 (FLIP); prev q2 -> 10.12>=ask10.12 -> at_ask
#   tr3 sec2 @2.4  10.11 100  10.11<10.12 -> sign -1; prev q3 -> 10.11>=ask10.11 -> at_ask
#   tr4 sec2 @2.8  10.12  50  10.12>10.11 -> sign +1; prev q4 CROSSED 10.12>=ask10.11 -> at_ask
#                             (ask precedence over bid); size 50<100 -> ODD LOT
#   tr5 sec3 @3.5  10.06 6000 10.06<10.12 -> sign -1; prev q5 -> not>=10.09, not<=10.05 -> NEITHER
#                             dollar 60360 >= 50_000 -> LARGE trade
#   (sec4 EMPTY: no trades, no quotes)
#   tr6 sec5 @5.2  10.20 100  10.20>10.06 -> sign +1; prev q5 -> 10.20>=ask10.09 -> at_ask
#                             (no quote update in sec5 -> quote state fields stay NULL)
# --------------------------------------------------------------------------- #

QUOTES = [
    (_ns(0.1), 10.00, 100.0, 10.10, 100.0),
    (_ns(0.6), 10.00, 300.0, 10.10, 100.0),
    (_ns(1.5), 10.02, 200.0, 10.12, 150.0),
    (_ns(2.3), 10.01, 50.0, 10.11, 50.0),
    (_ns(2.7), 10.14, 80.0, 10.11, 60.0),
    (_ns(3.4), 10.05, 100.0, 10.09, 100.0),
]
TRADES = [
    (_ns(0.2), 10.10, 200.0),
    (_ns(0.7), 10.00, 100.0),
    (_ns(1.6), 10.12, 300.0),
    (_ns(2.4), 10.11, 100.0),
    (_ns(2.8), 10.12, 50.0),
    (_ns(3.5), 10.06, 6000.0),
    (_ns(5.2), 10.20, 100.0),
]


def _trades_df(rows=None) -> pl.DataFrame:
    return pl.DataFrame(
        rows if rows is not None else TRADES,
        schema={"ts": pl.Int64, "price": pl.Float64, "size": pl.Float64},
        orient="row",
    )


def _quotes_df(rows=None) -> pl.DataFrame:
    return pl.DataFrame(
        rows if rows is not None else QUOTES,
        schema={
            "ts": pl.Int64,
            "bid": pl.Float64,
            "bid_size": pl.Float64,
            "ask": pl.Float64,
            "ask_size": pl.Float64,
        },
        orient="row",
    )


def _row(df: pl.DataFrame, sec: int) -> dict:
    return df.filter(pl.col("ts") == T0 + sec * NS_PER_S).to_dicts()[0]


# --------------------------------------------------------------------------- shape
def test_shape_and_columns():
    df = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    assert df.height == 6
    assert df.columns == EVENT_BARS_COLUMNS
    assert df["ts"].dtype == pl.Int64
    for c in EVENT_BARS_COLUMNS[1:]:
        assert df[c].dtype == pl.Float64
    # exactly one row per second, sorted
    assert df["ts"].to_list() == [T0 + s * NS_PER_S for s in range(6)]


# --------------------------------------------------------------------------- golden
def test_golden_sec0():
    df = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    r = _row(df, 0)
    # trades: tr0(10.10x200 at_ask, sign0), tr1(10.00x100 at_bid, sign-1)
    assert r["n_trades"] == 2.0
    assert r["volume"] == 300.0
    assert r["dollar_vol"] == pytest.approx(10.10 * 200 + 10.00 * 100)  # 3020
    assert r["px_open"] == 10.10
    assert r["px_high"] == 10.10
    assert r["px_low"] == 10.00
    assert r["px_close"] == 10.00
    assert r["signed_vol"] == pytest.approx(-100.0)      # 0*200 + (-1)*100
    assert r["signed_dollar"] == pytest.approx(-1000.0)  # (-1)*10.00*100
    assert r["at_ask_vol"] == 200.0
    assert r["at_bid_vol"] == 100.0
    assert r["large_trade_vol"] == 0.0
    assert r["odd_lot_frac"] == 0.0
    assert r["max_trade_size"] == 200.0
    # quotes: close state = q1 (10.00/10.10, 300/100)
    assert r["bid"] == 10.00
    assert r["ask"] == 10.10
    assert r["bid_size"] == 300.0
    assert r["ask_size"] == 100.0
    assert r["mid"] == pytest.approx(10.05)
    assert r["spread_bps_close"] == pytest.approx(1e4 * 0.10 / 10.05)
    assert r["n_quotes"] == 2.0
    assert r["ofi"] == pytest.approx(200.0)
    assert r["imb_close"] == pytest.approx((300 - 100) / 400)  # 0.5
    assert r["locked_crossed_n"] == 0.0


def test_golden_sec1_flip():
    df = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    r = _row(df, 1)
    # tr2: sign flips -1 -> +1
    assert r["n_trades"] == 1.0
    assert r["signed_vol"] == pytest.approx(300.0)
    assert r["signed_dollar"] == pytest.approx(10.12 * 300)
    assert r["at_ask_vol"] == 300.0
    assert r["at_bid_vol"] == 0.0
    assert r["ofi"] == pytest.approx(300.0)
    assert r["n_quotes"] == 1.0
    assert r["imb_close"] == pytest.approx((200 - 150) / 350)


def test_golden_sec2_crossed_and_odd():
    df = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    r = _row(df, 2)
    # trades tr3(10.11x100 sign-1 at_ask) tr4(10.12x50 sign+1 at_ask, odd lot)
    assert r["n_trades"] == 2.0
    assert r["volume"] == 150.0
    assert r["signed_vol"] == pytest.approx(-50.0)          # -100 + 50
    assert r["signed_dollar"] == pytest.approx(-10.11 * 100 + 10.12 * 50)
    assert r["at_ask_vol"] == 150.0                          # crossed: ask precedence
    assert r["at_bid_vol"] == 0.0
    assert r["odd_lot_frac"] == pytest.approx(50 / 150)      # tr4 size 50 < 100
    assert r["max_trade_size"] == 100.0
    # quotes: q3 then q4(crossed). OFI -180, locked 1, close = q4
    assert r["ofi"] == pytest.approx(-180.0)
    assert r["locked_crossed_n"] == 1.0
    assert r["n_quotes"] == 2.0
    assert r["bid"] == 10.14
    assert r["ask"] == 10.11
    assert r["spread_bps_close"] == pytest.approx(1e4 * (10.11 - 10.14) / 10.125)  # negative
    # spread_bps_mean over q3,q4
    sp3 = 1e4 * (10.11 - 10.01) / ((10.11 + 10.01) / 2)
    sp4 = 1e4 * (10.11 - 10.14) / ((10.14 + 10.11) / 2)
    assert r["spread_bps_mean"] == pytest.approx((sp3 + sp4) / 2)
    # imb_mean over q3(0), q4(20/140)
    assert r["imb_mean"] == pytest.approx((0.0 + (80 - 60) / 140) / 2)
    # micro_dev at close (q4)
    micro = (10.11 * 80 + 10.14 * 60) / 140
    assert r["micro_dev_bps"] == pytest.approx(1e4 * (micro - 10.125) / 10.125)


def test_golden_sec3_large_and_neither():
    df = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    r = _row(df, 3)
    # tr5: 6000 @ 10.06 -> dollar 60360 >= 50k large; unclassified (neither)
    assert r["large_trade_vol"] == 6000.0
    assert r["at_ask_vol"] == 0.0
    assert r["at_bid_vol"] == 0.0
    assert r["signed_vol"] == pytest.approx(-6000.0)
    assert r["ofi"] == pytest.approx(-180.0)
    assert r["n_quotes"] == 1.0
    assert r["imb_close"] == pytest.approx(0.0)


def test_golden_sec4_empty():
    df = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    r = _row(df, 4)
    # fully empty second
    assert r["n_trades"] == 0.0
    assert r["volume"] == 0.0
    assert r["dollar_vol"] == 0.0
    assert r["signed_vol"] == 0.0
    assert r["at_ask_vol"] == 0.0
    assert r["large_trade_vol"] == 0.0
    assert r["odd_lot_frac"] == 0.0
    assert r["max_trade_size"] == 0.0
    assert r["px_open"] is None
    assert r["px_close"] is None
    # quote state null, counts/ofi 0
    assert r["bid"] is None
    assert r["ask"] is None
    assert r["mid"] is None
    assert r["spread_bps_close"] is None
    assert r["spread_bps_mean"] is None
    assert r["imb_close"] is None
    assert r["imb_mean"] is None
    assert r["micro_dev_bps"] is None
    assert r["n_quotes"] == 0.0
    assert r["ofi"] == 0.0
    assert r["locked_crossed_n"] == 0.0


def test_golden_sec5_quote_state_not_ffilled():
    df = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    r = _row(df, 5)
    # tr6 present and classified against prevailing q5, but NO quote update in sec5
    assert r["n_trades"] == 1.0
    assert r["at_ask_vol"] == 100.0
    assert r["signed_vol"] == pytest.approx(100.0)
    # quote state must NOT be forward-filled here
    assert r["bid"] is None
    assert r["ask"] is None
    assert r["spread_bps_close"] is None
    assert r["n_quotes"] == 0.0
    assert r["ofi"] == 0.0


# --------------------------------------------------------------------------- determinism
def test_determinism():
    a = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    b = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    assert a.equals(b)


# --------------------------------------------------------------------------- PIT / truncation
def test_pit_no_future_leakage():
    # T = start of sec3 (a mid-session second boundary)
    T = T0 + 3 * NS_PER_S
    full = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    trades_trunc = [r for r in TRADES if r[0] < T]
    quotes_trunc = [r for r in QUOTES if r[0] < T]
    trunc = build_event_bars(_trades_df(trades_trunc), _quotes_df(quotes_trunc), T0, CLOSE)
    # rows with ts < T - 1s must be byte-identical (no future leakage into the past)
    guard = T - NS_PER_S
    full_past = full.filter(pl.col("ts") < guard)
    trunc_past = trunc.filter(pl.col("ts") < guard)
    assert full_past.equals(trunc_past)
    assert full_past.height == 2  # sec0, sec1


# --------------------------------------------------------------------------- reduced schema / None
def test_quotes_none_builds():
    df = build_event_bars(_trades_df(), None, T0, CLOSE)
    assert df.height == 6
    assert df.columns == EVENT_BARS_COLUMNS
    # no quotes -> no classification, all quote fields null/0
    assert df["at_ask_vol"].sum() == 0.0
    assert df["at_bid_vol"].sum() == 0.0
    assert df["n_quotes"].sum() == 0.0
    assert df["ofi"].sum() == 0.0
    assert df["bid"].null_count() == 6
    # trade-only fields still correct
    assert df.filter(pl.col("ts") == T0)["volume"].item() == 300.0


def test_reduced_trades_schema_builds():
    # reduced trades (engineV2 import): only ts, price, size — plus reduced quotes.
    df = build_event_bars(_trades_df(), _quotes_df(), T0, CLOSE)
    # already reduced-shaped in these helpers; assert a build with extra cols too
    trades_full = _trades_df().with_columns(
        pl.lit("").alias("exchange"),
        pl.lit("").alias("conditions"),
        pl.lit("").alias("tape"),
    )
    quotes_full = _quotes_df().with_columns(
        pl.lit("").alias("bid_exchange"),
        pl.lit("").alias("ask_exchange"),
        pl.lit("").alias("conditions"),
        pl.lit("").alias("tape"),
    )
    df2 = build_event_bars(trades_full, quotes_full, T0, CLOSE)
    assert df.equals(df2)


def test_empty_inputs_build():
    empty_t = _trades_df([]).clear()
    df = build_event_bars(empty_t, None, T0, CLOSE)
    assert df.height == 6
    assert df.columns == EVENT_BARS_COLUMNS
    assert df["n_trades"].sum() == 0.0
    assert df["px_close"].null_count() == 6
