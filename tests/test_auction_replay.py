"""Tests for backtest/auction_replay.py — the MOC auction evaluator.

find_closing_cross on synthetic condition-coded trades; adv20 from a tmp bars
lake; replay_moc_event hand-computed net (market entry via the shared kernel incl.
slip; exit exactly at the cross price, fees on the sell leg only) plus the
persistence-exit branch. No network.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from enginev51.backtest import latency as lat
from enginev51.backtest.auction_replay import (
    adv20_dollars,
    find_closing_cross,
    replay_moc_event,
)
from enginev51.backtest.replay import SessionTape
from enginev51.config import Settings
from enginev51.data import store
from enginev51.data.noii import et_ns

SESSION = "2025-06-02"
SLIP = 0.5
TAF = 0.3
TOL = 1e-9


# --------------------------------------------------------------------------- cross


def _trade(ts, price, size, cond) -> dict:
    return {"ts": ts, "price": price, "size": size, "conditions": cond}


def _trades(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(
        rows,
        schema={"ts": pl.Int64, "price": pl.Float64, "size": pl.Float64, "conditions": pl.Utf8},
        orient="row",
    )


def test_find_closing_cross_picks_big_six_print() -> None:
    df = _trades(
        [
            _trade(et_ns(SESSION, 15, 58, 0), 100.0, 900_000.0, "@6"),  # before window -> excluded
            _trade(et_ns(SESSION, 15, 59, 58), 99.5, 300.0, "@"),  # regular, not cross
            _trade(et_ns(SESSION, 16, 0, 0), 100.0, 500_000.0, "@6"),  # THE cross (big "6")
            _trade(et_ns(SESSION, 16, 0, 5), 100.01, 100.0, "M"),  # late "M" dupe, smaller
        ]
    )
    cross = find_closing_cross(df)
    assert cross is not None
    ts, price, size = cross
    assert ts == et_ns(SESSION, 16, 0, 0)
    assert price == pytest.approx(100.0)
    assert size == pytest.approx(500_000.0)


def test_find_closing_cross_none_when_conditions_stripped() -> None:
    # legacy exports: condition codes blanked -> cannot identify the cross -> None
    df = _trades(
        [
            _trade(et_ns(SESSION, 16, 0, 0), 100.0, 500_000.0, ""),
            _trade(et_ns(SESSION, 16, 0, 5), 100.01, 100.0, ""),
        ]
    )
    assert find_closing_cross(df) is None


def test_find_closing_cross_none_when_no_conditions_column() -> None:
    df = pl.DataFrame(
        {"ts": [et_ns(SESSION, 16, 0, 0)], "price": [100.0], "size": [500_000.0]}
    )
    assert find_closing_cross(df) is None


def test_find_closing_cross_none_outside_window() -> None:
    df = _trades([_trade(et_ns(SESSION, 15, 30, 0), 100.0, 500_000.0, "@6")])
    assert find_closing_cross(df) is None


def test_find_closing_cross_none_on_empty() -> None:
    assert find_closing_cross(None) is None
    assert find_closing_cross(_trades([])) is None


# --------------------------------------------------------------------------- adv20


def _bar(ts, vwap, volume) -> dict:
    return {
        "ts": ts,
        "open": vwap,
        "high": vwap,
        "low": vwap,
        "close": vwap,
        "volume": float(volume),
        "trade_count": 1,
        "vwap": float(vwap),
    }


def test_adv20_trailing_dollar_volume_pit(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "primary", legacy_data_dir=tmp_path / "legacy")
    feed = settings.data_feed_type
    rows = [
        _bar(et_ns("2025-03-03", 10, 0), 100.0, 1000),  # prior: $100k
        _bar(et_ns("2025-03-04", 10, 0), 200.0, 1000),  # prior: $200k
        _bar(et_ns("2025-03-05", 10, 0), 999.0, 9999),  # target day: must NOT leak in
    ]
    store.write_partition(settings.raw_dir, feed, "bars1m", "AMD", "2025-03", rows)

    adv = adv20_dollars(settings, "AMD", "2025-03-05")
    # trailing sessions strictly before 03-05: (100k + 200k)/2 = 150k
    assert adv == pytest.approx(150_000.0)


def test_adv20_none_when_no_prior_bars(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "primary", legacy_data_dir=tmp_path / "legacy")
    # v1.5 coverage extension: minute-bar absence falls back to DAILY bars
    # (bars1d), so a real symbol now returns its daily ADV; None only when
    # BOTH sources are absent.
    assert adv20_dollars(settings, "ZZFAKEZZ", "2025-03-05") is None


# --------------------------------------------------------------------------- replay


def _flat_tape(bid=99.0, ask=100.0, q_ts0=0) -> SessionTape:
    return SessionTape(
        symbol="NVDA",
        q_ts=np.array([q_ts0], dtype=np.int64),
        q_bid=np.array([bid], dtype=np.float64),
        q_ask=np.array([ask], dtype=np.float64),
        t_ts=np.array([], dtype=np.int64),
        t_price=np.array([], dtype=np.float64),
        t_size=None,
    )


def test_replay_moc_event_hand_computed_net_long() -> None:
    tape = _flat_tape(bid=99.0, ask=100.0)
    plan_id = "NVDA-2025-06-02-moc"
    signal_ts = 0
    cross_ts = 600 * 1_000_000_000
    cross_price = 101.0
    res = replay_moc_event(
        tape, signal_ts, 1, (cross_ts, cross_price, 500_000.0), 7, plan_id, symbol="NVDA",
    )
    assert res.status == "ok"
    assert res.exit_reason == "moc"

    # entry: market BUY lifts ask*(1+slip); slip 0.5 bps
    entry_px = 100.0 * (1.0 + SLIP * 1e-4)
    assert res.entry_px == pytest.approx(entry_px, abs=TOL)
    # exit is exactly the cross print price (zero spread/slip)
    assert res.exit_px == pytest.approx(101.0, abs=TOL)

    # net = (cross - entry)/entry*1e4 - fees ; fees = TAF * (sell_notional/entry_notional)
    #   long -> sell leg is the exit (cross); entry notional = entry_px
    exp_fees = TAF * (cross_price / entry_px)
    exp_net = (cross_price - entry_px) / entry_px * 1e4 - exp_fees
    assert res.net_bps == pytest.approx(exp_net, abs=1e-6)

    # entry_ts is signal_ts + a deterministic seeded latency draw
    entry_ts = lat.latency_ns(7, plan_id, lat.LEG_ENTRY, 5.0, 25.0)
    assert res.entry_ts == entry_ts
    assert res.exit_ts == cross_ts
    assert res.hold_s == pytest.approx((cross_ts - entry_ts) / 1e9, abs=TOL)


def test_replay_moc_event_short_fees_on_entry() -> None:
    # SHORT: sell entry at bid*(1-slip); buy back at the cross. Fees hit the SELL
    # (entry) leg, so fees ratio == 1 exactly -> fees_bps == TAF.
    tape = _flat_tape(bid=99.0, ask=100.0)
    plan_id = "NVDA-2025-06-02-moc-s"
    cross_price = 98.0
    res = replay_moc_event(tape, 0, -1, (600_000_000_000, cross_price, 1.0), 7, plan_id)
    entry_px = 99.0 * (1.0 - SLIP * 1e-4)
    assert res.entry_px == pytest.approx(entry_px, abs=TOL)
    exp_net = -1 * (cross_price - entry_px) / entry_px * 1e4 - TAF
    assert res.net_bps == pytest.approx(exp_net, abs=1e-6)


def test_replay_moc_event_persistence_branch() -> None:
    tape = _flat_tape(bid=99.0, ask=100.0)
    plan_id = "NVDA-2025-06-02-moc"
    persist_ts = 300 * 1_000_000_000
    res = replay_moc_event(
        tape, 0, 1, (600_000_000_000, 101.0, 1.0), 7, plan_id, symbol="NVDA",
        persistence_exit_ts=persist_ts,
    )
    assert res.status == "ok"
    assert res.exit_reason == "persistence"
    # exit is a taker market SELL (long unwind): bid*(1-slip), NOT the cross price
    exit_px = 99.0 * (1.0 - SLIP * 1e-4)
    assert res.exit_px == pytest.approx(exit_px, abs=TOL)
    entry_px = 100.0 * (1.0 + SLIP * 1e-4)
    exp_fees = TAF * (exit_px / entry_px)
    exp_net = (exit_px - entry_px) / entry_px * 1e4 - exp_fees
    assert res.net_bps == pytest.approx(exp_net, abs=1e-6)
    exit_ts = persist_ts + lat.latency_ns(7, plan_id, "persist", 5.0, 25.0)
    assert res.exit_ts == exit_ts


def test_replay_moc_event_void_when_no_quote_before_entry() -> None:
    # only quote is far in the future -> no prevailing quote at entry action -> void
    tape = _flat_tape(q_ts0=500 * 1_000_000_000)
    res = replay_moc_event(tape, 0, 1, (600_000_000_000, 101.0, 1.0), 7, "X-moc")
    assert res.status == "void"
    assert res.net_bps is None


def test_replay_moc_event_void_on_missing_cross_without_persistence() -> None:
    tape = _flat_tape()
    res = replay_moc_event(tape, 0, 1, None, 7, "X-moc")
    assert res.status == "void"


def test_replay_moc_event_void_on_bad_side() -> None:
    tape = _flat_tape()
    res = replay_moc_event(tape, 0, 0, (600_000_000_000, 101.0, 1.0), 7, "X-moc")
    assert res.status == "void"
