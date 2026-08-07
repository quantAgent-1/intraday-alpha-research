"""Feature/label correctness — most importantly the point-in-time invariant."""

import math

import polars as pl
import pytest

from enginev51.data import calendar as cal
from enginev51.features import slow
from enginev51.features.grid import (
    NS_PER_MIN,
    PRED_STAMP_TO_AVAILABILITY_NS,
    build_session_grid,
)
from enginev51.labels import forward

SESSIONS = ["2026-01-05", "2026-01-06", "2026-01-07"]  # Mon–Wed, full days


def _synthetic_bars(symbol: str, drift: float = 0.01) -> pl.DataFrame:
    """390 RTH bars per session, linearly drifting close, constant volume."""
    rows = []
    px = 100.0
    for s_i, s in enumerate(SESSIONS):
        from datetime import date

        op, _ = cal.session_bounds_utc(date.fromisoformat(s))
        open_ns = int(op.timestamp() * 1e9)
        px = 100.0 + 2.0 * s_i  # overnight gap of +2 between sessions
        for i in range(390):
            close = px + drift * i
            rows.append(
                {
                    "ts": open_ns + i * NS_PER_MIN,
                    "open": close,
                    "high": close + 0.05,
                    "low": close - 0.05,
                    "close": close,
                    "volume": 1000.0,
                    "trade_count": 10,
                    "vwap": close,
                }
            )
    return pl.DataFrame(rows)


@pytest.fixture(scope="module")
def grid() -> pl.DataFrame:
    return build_session_grid(_synthetic_bars("TEST"), "TEST")


def test_grid_shape_and_sessions(grid: pl.DataFrame) -> None:
    assert grid.height == 390 * 3
    assert grid["session"].n_unique() == 3
    assert grid["is_real"].all()
    # gap for session 2: log(102/ (100+0.01*389))
    s2 = grid.filter(pl.col("session") == SESSIONS[1])
    expected_gap = math.log(102.0 / (100.0 + 0.01 * 389))
    assert abs(s2["gap_open"][0] - expected_gap) < 1e-12
    assert abs(s2["prev_close"][0] - (100.0 + 0.01 * 389)) < 1e-12


def test_grid_ffills_missing_minutes() -> None:
    bars = _synthetic_bars("TEST")
    # remove minutes 10..19 of session 1
    s0 = SESSIONS[0]
    from datetime import date

    op, _ = cal.session_bounds_utc(date.fromisoformat(s0))
    open_ns = int(op.timestamp() * 1e9)
    drop_ts = {open_ns + i * NS_PER_MIN for i in range(10, 20)}
    bars2 = bars.filter(~pl.col("ts").is_in(list(drop_ts)))
    g = build_session_grid(bars2, "TEST")
    assert g.height == 390 * 3  # grid is complete regardless
    hole = g.filter(pl.col("ts").is_in(list(drop_ts)))
    assert (~hole["is_real"]).all()
    assert (hole["volume"] == 0).all()
    # close ffilled from minute 9
    assert (hole["close"] == (100.0 + 0.01 * 9)).all()


def test_grid_open_stamped_and_availability_contract(grid: pl.DataFrame) -> None:
    """F2 producer contract (SIM_AUDIT_2026-07-21 §3): grid rows are stamped at
    bar OPEN — row i.ts == session open + i*60s — and a row is knowable to a
    real-time consumer only at ts + PRED_STAMP_TO_AVAILABILITY_NS (one 60s bar).
    Pinned here so any change to either the stamp or the lag breaks a named test.
    """
    from datetime import date

    # availability lag is exactly one 1-min bar.
    assert PRED_STAMP_TO_AVAILABILITY_NS == 60 * 1_000_000_000
    assert PRED_STAMP_TO_AVAILABILITY_NS == NS_PER_MIN

    # every row's ts is its own bar's OPEN instant (session open + minute_idx).
    for s in SESSIONS:
        op, _ = cal.session_bounds_utc(date.fromisoformat(s))
        open_ns = int(op.timestamp() * 1e9)
        sess = grid.filter(pl.col("session") == s).sort("minute_idx")
        for idx, ts in zip(sess["minute_idx"].to_list(), sess["ts"].to_list(), strict=False):
            assert ts == open_ns + idx * NS_PER_MIN


def test_session_vwap_and_returns(grid: pl.DataFrame) -> None:
    base = slow.compute_base(grid)
    row = base.filter(
        (pl.col("session") == SESSIONS[0]) & (pl.col("minute_idx") == 30)
    )
    # ret_30m = log(close_30 / close_0)
    expected = math.log((100.0 + 0.01 * 30) / 100.0)
    assert abs(row["ret_30m"][0] - expected) < 1e-12
    # vwap of equal-volume linear prices = mean of closes 0..30
    mean_px = sum(100.0 + 0.01 * i for i in range(31)) / 31
    assert abs(row["vwap_sess"][0] - mean_px) < 1e-9
    # rv_30m = sqrt(sum of 30 one-minute log-return squares)
    r1s = [
        math.log((100.0 + 0.01 * (i + 1)) / (100.0 + 0.01 * i)) ** 2 for i in range(30)
    ]
    assert abs(row["rv_30m"][0] - math.sqrt(sum(r1s))) < 1e-12


def test_labels_forward_and_excursions(grid: pl.DataFrame) -> None:
    df = grid.with_columns(pl.lit("TEST").alias("symbol"))
    lab = forward.add_labels(df)
    row = lab.filter((pl.col("session") == SESSIONS[0]) & (pl.col("minute_idx") == 100))
    c100 = 100.0 + 0.01 * 100
    # fwd 30m
    assert abs(row["l_fwd_30m"][0] - math.log((100.0 + 0.01 * 130) / c100)) < 1e-12
    # MFE over t+1..t+30 = high at minute 130 (rising drift)
    assert abs(row["l_mfe_30m"][0] - math.log((100.0 + 0.01 * 130 + 0.05) / c100)) < 1e-12
    # MAE = low at minute 101
    assert abs(row["l_mae_30m"][0] - math.log((100.0 + 0.01 * 101 - 0.05) / c100)) < 1e-12
    # near close: horizon doesn't fit → null
    tail = lab.filter((pl.col("session") == SESSIONS[0]) & (pl.col("minute_idx") == 380))
    assert tail["l_fwd_30m"][0] is None
    assert tail["l_mfe_30m"][0] is None
    # to-close label exists everywhere
    assert tail["l_fwd_close"][0] is not None


def _full_features(bars: pl.DataFrame) -> pl.DataFrame:
    g = build_session_grid(bars, "TEST")
    base = slow.compute_base(g)
    mkt = slow.compute_base(build_session_grid(_synthetic_bars("QQQ", drift=0.005), "QQQ"))
    return slow.compute_features(base, mkt, None)


def test_no_lookahead() -> None:
    """THE point-in-time invariant: truncating future data never changes past features."""
    bars = _synthetic_bars("TEST")
    full = _full_features(bars)

    # cutoff: mid-session-2 (minute 200 of 2026-01-06)
    from datetime import date

    op, _ = cal.session_bounds_utc(date.fromisoformat(SESSIONS[1]))
    cutoff_ns = int(op.timestamp() * 1e9) + 200 * NS_PER_MIN

    truncated = _full_features(bars.filter(pl.col("ts") <= cutoff_ns))

    cols = [c for c in slow.FEATURE_COLS]
    a = full.filter(pl.col("ts") <= cutoff_ns).sort("ts").select(cols)
    b = truncated.filter(pl.col("ts") <= cutoff_ns).sort("ts").select(cols)
    assert a.height == b.height and a.height > 0
    for c in cols:
        av, bv = a[c].to_list(), b[c].to_list()
        for i, (x, y) in enumerate(zip(av, bv, strict=False)):
            if x is None and y is None:
                continue
            assert x is not None and y is not None, f"{c}[{i}]: null mismatch {x} vs {y}"
            assert math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12), f"{c}[{i}]: {x} != {y}"
