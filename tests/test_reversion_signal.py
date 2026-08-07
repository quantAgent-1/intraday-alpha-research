"""M18 §6.7 exit priority + curfew / min-hold / blackout causality."""

from __future__ import annotations

from datetime import date

import numpy as np
import polars as pl

from enginev51.data import calendar
from enginev51.reversion.features import GateBaseline, compute_session_features
from enginev51.reversion.ou import OUCalibrator
from enginev51.reversion.signal import (
    CURFEW_MIN_ET,
    EXIT_FORCE,
    EXIT_HARD,
    EXIT_STRATEGY,
    EXIT_TP,
    EXIT_TRAILING,
    MIN_HOLD_BARS,
    _risk_tick,
    run_session,
)

NS = 1_000_000_000


def _pos(**kw):
    base = dict(side=1, entry_fill=100.0, high_water=100.0, trailing=None,
                take_profit=200.0, hard_stop=0.0, deadline_bar=10**9)
    base.update(kw)
    return base


# ---- §6.7 exit priority: TP > hard > trailing > deadline (riskgate_nb order) ----

def test_priority_tp_beats_hard():
    # Degenerate co-trigger: micro satisfies BOTH TP(>=99) and hard(<=101) → TP wins.
    r = _risk_tick(_pos(take_profit=99.0, hard_stop=101.0), 100.0, 0.5, 0)
    assert r == EXIT_TP


def test_priority_hard_beats_trailing():
    # micro 99 hits hard_stop 100 AND armed trailing 100 → hard wins.
    r = _risk_tick(_pos(hard_stop=100.0, trailing=100.0, take_profit=500.0), 99.0, 0.5, 0)
    assert r == EXIT_HARD


def test_priority_trailing_beats_deadline():
    # trailing armed & hit; deadline also passed → trailing wins.
    r = _risk_tick(
        _pos(hard_stop=90.0, take_profit=500.0, trailing=100.0, deadline_bar=0),
        99.0, 0.5, 100,
    )
    assert r == EXIT_TRAILING


def test_deadline_only():
    r = _risk_tick(_pos(deadline_bar=50), 100.0, 0.5, 50)
    from enginev51.reversion.signal import EXIT_MAX_HOLD
    assert r == EXIT_MAX_HOLD


def test_trailing_activation_then_trigger():
    # call1: micro 105 → pnl 500 bps > 250 → arm trailing = 105 − 2·max(0.5,0.2)=104.
    pos = _pos()
    assert _risk_tick(pos, 105.0, 0.5, 0) == 0  # no exit yet (above trailing)
    assert pos["trailing"] is not None and abs(pos["trailing"] - 104.0) < 1e-9
    # call2: micro 103.9 <= trailing 104 → trailing exit.
    assert _risk_tick(pos, 103.9, 0.5, 1) == EXIT_TRAILING


# ---- §6.5/§6.7 curfew / min-hold / blackout on a synthetic reverting session ----

def _reverting_session(seed: int = 3) -> pl.DataFrame:
    """A full RTH day whose ε = mid − vwap_5m oscillates across the OU band, so
    run_session actually opens/closes positions (and spans the 15:50 curfew)."""
    op, _cl = calendar.session_bounds_utc(date(2025, 9, 3))
    open_ns = int(op.timestamp()) * NS
    n = 23400
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    mid = 100.0 + 0.6 * np.sin(2 * np.pi * t / 200.0) + rng.normal(0, 0.05, n)
    bid = mid - 0.01
    ask = mid + 0.01
    bs = rng.integers(1, 40, n).astype(float)
    as_ = rng.integers(1, 40, n).astype(float)
    vol = rng.integers(50, 500, n).astype(float)
    px = mid + rng.normal(0, 0.01, n)
    denom = bs + as_
    return pl.DataFrame({
        "ts": (open_ns + t * NS).astype(np.int64),
        "mid": mid, "bid": bid, "ask": ask, "bid_size": bs, "ask_size": as_,
        "spread_bps_close": 1e4 * (ask - bid) / mid,
        "imb_close": (bs - as_) / denom,
        "micro_dev_bps": 1e4 * ((bs * ask + as_ * bid) / denom - mid) / mid,
        "ofi": rng.normal(0, 5, n),
        "volume": vol, "dollar_vol": px * vol,
        "px_open": px, "px_high": np.maximum(mid, px) + 0.03,
        "px_low": np.minimum(mid, px) - 0.03, "px_close": px,
        "n_quotes": rng.integers(5, 50, n).astype(float),
    })


def test_curfew_minhold_blackout_on_synthetic_session():
    feat = compute_session_features(_reverting_session())
    cal = OUCalibrator()
    base = GateBaseline(float("nan"), float("nan"), float("nan"))
    recs = run_session(feat, "SYN", "2025-09-03", cal, base, entry_model="taker", max_hold_bars=1800)
    opened = [r for r in recs if r.get("opened")]
    assert len(opened) > 5  # the synthetic reverts enough to trade

    curfew_bar = int(np.nonzero(feat.et_minute >= CURFEW_MIN_ET)[0][0])

    for r in opened:
        # min-hold: strategy exits cannot occur within 30 s of entry.
        if r["exit_reason"] == EXIT_STRATEGY:
            assert (r["exit_bar"] - r["entry_open_bar"]) >= MIN_HOLD_BARS
        # blackout: no entry triggers inside 09:30-09:40 or 15:50-16:00 ET.
        assert not (570 <= r["et_minute"] <= 580)
        assert not (950 <= r["et_minute"] <= 960)
        # curfew: nothing opens at/after the curfew bar.
        assert r["entry_open_bar"] < curfew_bar
        # any force exit is stamped at the curfew boundary.
        if r["exit_reason"] == EXIT_FORCE:
            assert r["exit_bar"] <= curfew_bar
