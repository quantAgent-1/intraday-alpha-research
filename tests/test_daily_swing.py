"""Tests for the daily_swing_v1 side-ledger (apps/daily_swing.py) — synthetic data,
no LightGBM. Pins the invariants the registered spec requires:

  1. Session-shift label correctness: 1d label = log(next-session close / this close),
     5d = five sessions ahead — computed on SESSION-ROW POSITION, never calendar days
     (a synthetic frame with deliberate weekend/holiday gaps proves no calendar leakage).
  2. Holdout exclusion: sessions >= HOLDOUT_START, and any label that would reference a
     holdout close, are excluded entirely (seal-before-shift).
  3. Embargo >= 6 (> the longest 5d horizon) is enforced by the walk-forward guard.
"""

from __future__ import annotations

import math

import numpy as np
import polars as pl
import pytest

from enginev51.apps import daily_swing
from enginev51.models import cv
from enginev51.protocol import HOLDOUT_START

SYMBOLS = ["AAA", "BBB", "CCC"]


def _synth_daily(sessions: list[str], vol20: float = 0.02) -> pl.DataFrame:
    """One near-close row per (symbol, session) with a known close path.

    close is deterministic per symbol so the shifted-label arithmetic is exact.
    Only the columns add_session_labels touches are populated."""
    rows: list[dict] = []
    for si, sym in enumerate(SYMBOLS):
        for i, sess in enumerate(sessions):
            # distinct, strictly positive, non-linear path per symbol
            close = 100.0 + 10.0 * si + i + 0.5 * (i**1.3)
            rows.append({"symbol": sym, "session": sess, "close": close, "f_vol20": vol20})
    return pl.DataFrame(rows)


# 30 sessions with intentional calendar gaps (weekends + a holiday hole) so that
# "next session" != "next calendar day" — the leakage trap.
def _gappy_sessions(n: int = 30) -> list[str]:
    import datetime as dt

    out: list[str] = []
    d = dt.date(2025, 1, 6)  # a Monday, well before the holdout
    while len(out) < n:
        if d.weekday() < 5 and not (d.month == 1 and d.day == 20):  # skip weekends + one holiday
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


# --------------------------------------------------------------------------- 1. labels


def test_1d_label_is_next_session_close_ratio():
    sessions = _gappy_sessions(30)
    daily = daily_swing.add_session_labels(_synth_daily(sessions))
    d = daily.filter(pl.col("symbol") == "BBB").sort("session")
    closes = d["close"].to_list()
    lbl = d["l_fwd_1d"].to_list()
    for i in range(len(sessions) - 1):
        assert lbl[i] == pytest.approx(math.log(closes[i + 1] / closes[i]))
    assert lbl[-1] is None  # no next session -> null


def test_5d_label_is_five_sessions_ahead():
    sessions = _gappy_sessions(30)
    daily = daily_swing.add_session_labels(_synth_daily(sessions))
    d = daily.filter(pl.col("symbol") == "CCC").sort("session")
    closes = d["close"].to_list()
    lbl = d["l_fwd_5d"].to_list()
    for i in range(len(sessions) - 5):
        assert lbl[i] == pytest.approx(math.log(closes[i + 5] / closes[i]))
    for i in range(len(sessions) - 5, len(sessions)):
        assert lbl[i] is None


def test_shift_is_session_indexed_not_calendar():
    """The label must ignore calendar-day distance: a 3-calendar-day weekend gap
    between two adjacent SESSIONS still yields a 1-session label, not a 3-day one."""
    sessions = _gappy_sessions(10)
    # find an adjacent session pair that straddles a weekend (>1 calendar day apart)
    import datetime as dt

    straddle = next(
        i for i in range(len(sessions) - 1)
        if (dt.date.fromisoformat(sessions[i + 1]) - dt.date.fromisoformat(sessions[i])).days > 1
    )
    daily = daily_swing.add_session_labels(_synth_daily(sessions))
    d = daily.filter(pl.col("symbol") == "AAA").sort("session")
    closes = d["close"].to_list()
    # 1d label at the straddle uses the very next session row regardless of the gap
    assert d["l_fwd_1d"].to_list()[straddle] == pytest.approx(
        math.log(closes[straddle + 1] / closes[straddle])
    )


def test_z_normalization_matches_formula():
    sessions = _gappy_sessions(30)
    vol = 0.03
    daily = daily_swing.add_session_labels(_synth_daily(sessions, vol20=vol))
    d = daily.filter(pl.col("symbol") == "AAA").sort("session")
    for h in (1, 3, 5):
        lbl = d[f"l_fwd_{h}d"].to_list()
        z = d[f"z_{h}d"].to_list()
        for a, b in zip(lbl, z, strict=True):
            if a is None:
                assert b is None
            else:
                assert b == pytest.approx(a / (vol * math.sqrt(h)))


def test_zero_vol_yields_null_z():
    sessions = _gappy_sessions(8)
    daily = daily_swing.add_session_labels(_synth_daily(sessions, vol20=0.0))
    assert daily["z_1d"].is_null().all()


# --------------------------------------------------------------------------- 2. holdout


def test_holdout_rows_and_labels_excluded(tmp_path, monkeypatch):
    """build_daily_pool strips holdout BEFORE the shift: no holdout row survives and
    no surviving label references a holdout close."""
    # pre-holdout sessions ... then holdout sessions straddling the seal
    pre = ["2026-05-26", "2026-05-27", "2026-05-28", "2026-05-29"]
    post = ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05", "2026-06-08"]
    sessions = pre + post

    fdir = tmp_path / "features" / "v1"
    fdir.mkdir(parents=True)
    base = _synth_daily(sessions)
    for sym in SYMBOLS:
        # write a minimal feature parquet with ts + all FEATURE_COLS present
        sub = base.filter(pl.col("symbol") == sym).with_row_index("k")
        sub = sub.with_columns(pl.col("k").cast(pl.Int64).alias("ts"))
        for c in daily_swing.FEATURE_COLS:
            if c not in sub.columns:
                sub = sub.with_columns(pl.lit(0.0).alias(c))
        sub.drop("k").write_parquet(fdir / f"{sym}.parquet")

    class _S:
        data_dir = tmp_path

    daily = daily_swing.build_daily_pool(_S(), "v1", SYMBOLS)
    # no holdout row survives
    assert (daily["session"] < HOLDOUT_START.isoformat()).all()
    assert daily["session"].unique().sort().to_list() == pre
    # the last pre-holdout session's 1d label would need a holdout close -> must be null
    last_pre = daily.filter(pl.col("session") == "2026-05-29")
    assert last_pre["l_fwd_1d"].is_null().all()
    # 5d labels: none of the 4 pre-holdout sessions have 5 sessions ahead in-sample
    assert daily["l_fwd_5d"].is_null().all()


# --------------------------------------------------------------------------- 3. embargo


def test_embargo_constant_exceeds_longest_horizon():
    assert daily_swing.EMBARGO_SESSIONS >= 6
    assert daily_swing.EMBARGO_SESSIONS > daily_swing.LONGEST_HORIZON


def test_walk_forward_gap_exceeds_longest_horizon():
    """With embargo_sessions=6 every fold purges >5 sessions between train end and
    test start (guards against a 5d label window bleeding into training)."""
    # need > min_train_sessions (250) for any fold to exist
    import datetime as dt

    sessions = [(dt.date(2024, 1, 1) + dt.timedelta(days=i)).isoformat() for i in range(320)]
    df = pl.DataFrame({"symbol": ["X"] * len(sessions), "session": sessions})
    folds = cv.walk_forward_folds(df, embargo_sessions=daily_swing.EMBARGO_SESSIONS)
    assert folds
    idx = {s: i for i, s in enumerate(sessions)}
    for f in folds:
        gap = idx[f.test_sessions[0]] - idx[f.train_sessions[-1]]
        assert gap > daily_swing.LONGEST_HORIZON
        assert gap >= daily_swing.EMBARGO_SESSIONS


def test_run_asserts_embargo_gt_horizon(monkeypatch):
    """A misconfigured embargo (<= longest horizon) must fail fast in run()."""
    monkeypatch.setattr(daily_swing, "EMBARGO_SESSIONS", 5)
    with pytest.raises(AssertionError):
        daily_swing.run(object(), version="v1", out_name="should-not-write")


# --------------------------------------------------------------------------- IC helpers


def test_cross_sectional_ic_perfect_rank():
    # 12-name session, pred order == label order -> IC == 1 (passes the min_symbols gate)
    preds = pl.DataFrame({
        "session": ["2026-01-05"] * 12,
        "pred": list(range(12)),
        "label": [float(x) for x in range(12)],
    })
    ic = daily_swing.cross_sectional_ic(preds)
    assert ic.height == 1
    assert ic["ic"][0] == pytest.approx(1.0)


def test_timeseries_ic_monotone():
    pred = np.arange(50, dtype=float)
    label = np.arange(50, dtype=float) * 2.0
    m, lo, hi, n = daily_swing.timeseries_ic_ci(pred, label, n_boot=200)
    assert n == 50
    assert m == pytest.approx(1.0)
    assert lo <= m <= hi
