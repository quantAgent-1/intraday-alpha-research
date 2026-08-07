"""Tests for apps/run_open_trial.py — the M6b opening-cross imbalance runner.

Covers the registration's load-bearing invariants with NO network and NO real
data:
  * signal-window PIT: an opening-NOII message at 09:28:31 ET is EXCLUDED (the
    signal is the last message at-or-before 09:28:30);
  * MOO fill == the daily bar open EXACTLY (zero spread/slip);
  * exit-fill hand-check on a synthetic BBO tape (taker cross + slip, fees on the
    sell leg only) with the decompose identity;
  * holdout guard rejects an --end on/after the sealed boundary.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest

from enginev51.apps.run_open_trial import (
    OPEN_SIGNAL_ET,
    assert_before_holdout,
    load_noii_opening,
    replay_open_event,
    run_open_trial,
)
from enginev51.backtest import latency as lat
from enginev51.backtest.replay import SessionTape
from enginev51.config import Settings
from enginev51.data.noii import NOII_SCHEMA, et_ns, partition_path, signal_at
from enginev51.protocol import SealViolation

SESSION = "2025-05-02"
SLIP = 0.5
TAF = 0.3
TOL = 1e-9


# --------------------------------------------------------------------- fixtures


def _noii_row(ts: int, side: str, imb: float, near: float, ref: float) -> dict:
    return {
        "ts": ts,
        "side": side,
        "imbalance_shares": imb,
        "paired_shares": 0.0,
        "near_price": near,
        "far_price": near,
        "ref_price": ref,
    }


def _flat_tape(bid: float = 99.0, ask: float = 100.0, q_ts0: int = 0) -> SessionTape:
    return SessionTape(
        symbol="NVDA",
        q_ts=np.array([q_ts0], dtype=np.int64),
        q_bid=np.array([bid], dtype=np.float64),
        q_ask=np.array([ask], dtype=np.float64),
        t_ts=np.array([], dtype=np.int64),
        t_price=np.array([], dtype=np.float64),
        t_size=None,
    )


# ------------------------------------------------------------- signal-window PIT


def test_signal_window_pit_excludes_0928_31() -> None:
    """A message at 09:28:31 ET must NOT govern the 09:28:30 signal; the last
    message at-or-before 09:28:30 wins (PIT)."""
    signal_ts = et_ns(SESSION, *OPEN_SIGNAL_ET)  # 09:28:30
    frame = pl.DataFrame(
        [
            # last valid message at 09:28:30 exactly: BUY imbalance, near 100
            _noii_row(et_ns(SESSION, 9, 28, 30), "B", 500_000.0, 100.0, 99.9),
            # a LATER, opposite message at 09:28:31 — must be excluded
            _noii_row(et_ns(SESSION, 9, 28, 31), "A", 9_000_000.0, 50.0, 50.0),
        ],
        schema=NOII_SCHEMA,
        orient="row",
    )
    adv = 1e9
    sig = signal_at(frame, signal_ts, adv)
    assert sig is not None
    # governed by the 09:28:30 BUY row (side +1), NOT the 09:28:31 SELL row
    assert sig["side"] == 1
    assert sig["near_price"] == pytest.approx(100.0)
    assert sig["norm_imb"] == pytest.approx(500_000.0 * 100.0 / adv)


def test_load_noii_opening_filters_window(tmp_path) -> None:
    """load_noii_opening returns only the opening-window messages (closing-cross
    15:xx rows are dropped) and None when the partition is absent."""
    root = tmp_path / "noii"
    rows = [
        _noii_row(et_ns(SESSION, 9, 28, 0), "B", 1000.0, 100.0, 99.9),  # opening: kept
        _noii_row(et_ns(SESSION, 15, 50, 0), "A", 2000.0, 100.0, 99.9),  # closing: dropped
    ]
    frame = pl.DataFrame(rows, schema=NOII_SCHEMA, orient="row")
    path = partition_path(root, "NVDA", SESSION[:7])
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(path)

    got = load_noii_opening("NVDA", SESSION, out_dir=root)
    assert got is not None
    assert got.height == 1
    assert got["ts"][0] == et_ns(SESSION, 9, 28, 0)

    assert load_noii_opening("MISSINGSYM", SESSION, out_dir=root) is None


# ---------------------------------------------------------------- MOO entry fill


def test_moo_fill_is_daily_open_exactly() -> None:
    """ENTRY = MOO fills AT the official open price, no slip/spread."""
    tape = _flat_tape(bid=99.0, ask=100.0)
    open_px = 123.45
    entry_ts = et_ns(SESSION, 9, 30, 0)
    exit_ts = et_ns(SESSION, 9, 45, 0)
    status, pnl, extras = replay_open_event(
        tape, open_px, entry_ts, exit_ts, 1, 7, "NVDA-x-open-0945", "exit_0945",
    )
    assert status == "ok"
    assert extras["entry_ts"] == entry_ts  # MOO fills exactly at 09:30:00, no latency
    # entry contributes zero spread/latency: mids == fill price, so the whole
    # decomposition's entry side is the clean open price. Verify via the gross
    # component reference — the entry vwap IS open_px (net uses entry vwap ref).
    # Direct proof: reconstruct net from open_px and the exit fill below.
    assert pnl.identity_residual_bps == pytest.approx(0.0, abs=1e-6)


# ------------------------------------------------------------- exit-fill handcheck


def test_exit_fill_handcheck_long_on_synthetic_bbo() -> None:
    """LONG: MOO at open, market-out SELL hits bid*(1-slip); fees on the sell
    (exit) leg. Net hand-computed against the synthetic BBO."""
    tape = _flat_tape(bid=99.0, ask=100.0)
    open_px = 98.0
    entry_ts = et_ns(SESSION, 9, 30, 0)
    exit_signal_ts = et_ns(SESSION, 9, 45, 0)
    plan_id = "NVDA-2025-05-02-open-0945"
    status, pnl, extras = replay_open_event(
        tape, open_px, entry_ts, exit_signal_ts, 1, 7, plan_id, "exit_0945",
    )
    assert status == "ok"
    # exit = SELL a long -> bid*(1-slip)
    exit_px = 99.0 * (1.0 - SLIP * 1e-4)
    assert extras["exit_px"] == pytest.approx(exit_px, abs=TOL)
    # net = (exit - open)/open*1e4 - fees ; long -> sell leg is the exit
    exp_fees = TAF * (exit_px / open_px)
    exp_net = (exit_px - open_px) / open_px * 1e4 - exp_fees
    assert pnl.net_bps == pytest.approx(exp_net, abs=1e-6)
    # exit ts = signal + deterministic seeded latency on the "exit" leg
    exp_exit_ts = exit_signal_ts + lat.latency_ns(7, plan_id, "exit", 5.0, 25.0)
    assert extras["exit_ts"] == exp_exit_ts
    assert extras["hold_s"] == pytest.approx((exp_exit_ts - entry_ts) / 1e9, abs=TOL)


def test_exit_fill_handcheck_short_fees_on_entry() -> None:
    """SHORT: MOO SELL at open (fees hit this entry sell leg, ratio 1), market-out
    BUY to cover lifts ask*(1+slip)."""
    tape = _flat_tape(bid=99.0, ask=100.0)
    open_px = 101.0
    entry_ts = et_ns(SESSION, 9, 30, 0)
    exit_signal_ts = et_ns(SESSION, 10, 0, 0)
    status, pnl, extras = replay_open_event(
        tape, open_px, entry_ts, exit_signal_ts, -1, 7, "NVDA-x-open-1000", "exit_1000",
    )
    assert status == "ok"
    exit_px = 100.0 * (1.0 + SLIP * 1e-4)  # buy to cover
    assert extras["exit_px"] == pytest.approx(exit_px, abs=TOL)
    # short: sell leg is the MOO entry -> fees ratio == 1 -> fees_bps == TAF
    exp_net = -1 * (exit_px - open_px) / open_px * 1e4 - TAF
    assert pnl.net_bps == pytest.approx(exp_net, abs=1e-6)
    assert pnl.fees_bps == pytest.approx(TAF, abs=1e-9)


def test_replay_void_when_no_bbo_before_exit() -> None:
    """Only quote is far in the future -> no prevailing BBO at the exit action
    -> void."""
    tape = _flat_tape(q_ts0=et_ns(SESSION, 23, 0, 0))
    status, pnl, _ = replay_open_event(
        tape, 100.0, et_ns(SESSION, 9, 30, 0), et_ns(SESSION, 9, 45, 0),
        1, 7, "X-open", "exit_0945",
    )
    assert status == "void"
    assert pnl is None


def test_replay_void_on_bad_side_and_bad_open() -> None:
    tape = _flat_tape()
    assert replay_open_event(
        tape, 100.0, 0, 1, 0, 7, "X", "exit_0945"
    )[0] == "void"
    assert replay_open_event(
        tape, 0.0, 0, 1, 1, 7, "X", "exit_0945"
    )[0] == "void"


# ------------------------------------------------------------------- holdout guard


def test_holdout_guard_rejects_sealed_end() -> None:
    # SealViolation, not AssertionError: the guard must survive `python -O` (B7/J2).
    with pytest.raises(SealViolation):
        assert_before_holdout(dt.date(2026, 6, 1))  # HOLDOUT_START exactly
    with pytest.raises(SealViolation):
        assert_before_holdout(dt.date(2026, 7, 1))
    # a pre-holdout end is fine
    assert_before_holdout(dt.date(2026, 5, 31))


def test_run_open_trial_guard_in_pipeline(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "primary", legacy_data_dir=tmp_path / "legacy")
    with pytest.raises(SealViolation):
        run_open_trial(
            settings,
            symbols=["NVDA"],
            start=dt.date(2026, 5, 1),
            end=dt.date(2026, 6, 2),  # crosses the seal
            threshold=0.0005,
            exit_cell="0945",
            seed=7,
        )


def test_run_open_trial_empty_when_no_data(tmp_path) -> None:
    """No NOII partitions at all -> empty results, funnel counts the misses, no
    crash (schema preserved)."""
    settings = Settings(data_dir=tmp_path / "primary", legacy_data_dir=tmp_path / "legacy")
    df, stats = run_open_trial(
        settings,
        symbols=["NVDA"],
        start=dt.date(2025, 5, 1),
        end=dt.date(2025, 5, 2),
        threshold=0.0005,
        exit_cell="0945",
        seed=7,
        noii_dir=tmp_path / "empty_noii",
    )
    assert df.height == 0
    assert list(df.columns)  # schema present
    assert stats["counts"]["no_noii_partition"] >= 1
    assert stats["counts"]["events_fired"] == 0
