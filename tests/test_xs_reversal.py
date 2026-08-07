"""Tests for apps/run_xs_reversal.py — the M7 cross-sectional reversal runner.

Pure-function coverage (no network): residualized-rank correctness on a hand frame;
universe-entry gating (a name with < 30 sessions never trades); fee sides (SEC/TAF
on the SELL leg + borrow only on shorts); the holdout guard; weekly-boundary
selection. Plus one end-to-end run on a synthetic daily-bar lake exercising the
exit-in-holdout drop and the MOC-fill == daily-close identity.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import polars as pl
import pytest

from enginev51.apps.run_xs_reversal import (
    SEC_TAF_SELL_BPS,
    assert_before_holdout,
    build_signal_frame,
    compute_leg,
    load_closes,
    rebalance_sessions,
    run_xs_reversal,
)
from enginev51.data import calendar
from enginev51.protocol import HOLDOUT_START, SealViolation

TOL = 1e-9


# --------------------------------------------------------------------------- helpers


def _sessions(n: int, start: str = "2024-01-02") -> list[str]:
    """`n` real NYSE sessions on/after `start`."""
    days = calendar.trading_days(date.fromisoformat(start), date(2026, 5, 31))
    return [d.isoformat() for d in days[:n]]


def _closes_frame(series: dict[str, list[float]], sessions: list[str]) -> pl.DataFrame:
    """Long [session, symbol, close]; each series may be shorter than `sessions`
    (a late-listing name), aligned to the TAIL is not assumed — aligned to the head."""
    rows: list[dict] = []
    for sym, closes in series.items():
        for i, c in enumerate(closes):
            rows.append({"session": sessions[i], "symbol": sym, "close": float(c)})
    return pl.DataFrame(rows).sort(["symbol", "session"])


def _write_bars(bars_dir, series: dict[str, list[float]], sessions: list[str]) -> None:
    for sym, closes in series.items():
        rows = []
        for i, c in enumerate(closes):
            d = date.fromisoformat(sessions[i])
            ts = int(datetime(d.year, d.month, d.day, 5, tzinfo=UTC).timestamp() * 1e9)
            rows.append(
                {"ts": ts, "open": float(c), "high": float(c), "low": float(c),
                 "close": float(c), "volume": 1.0e6, "trade_count": 1, "vwap": float(c)}
            )
        pl.DataFrame(rows).write_parquet(bars_dir / f"{sym}.parquet")


# --------------------------------------------------------------------------- 1. rank


def test_residualized_rank_on_hand_frame():
    """resid = ret5 − eligible-universe mean(ret5); ascending rank picks longs/shorts."""
    sessions = _sessions(36)
    n = len(sessions)
    # 6 symbols, flat 100 until the last session, where each gets a controlled
    # trailing-5d return via close_last = 100*(1+r) (close_{last-5} = 100).
    rmap = {"A": -0.05, "B": -0.03, "C": -0.01, "D": 0.01, "E": 0.03, "F": 0.05}
    series = {s: [100.0] * (n - 1) + [100.0 * (1 + r)] for s, r in rmap.items()}
    sig = build_signal_frame(_closes_frame(series, sessions))

    last = sessions[-1]
    at = sig.filter((pl.col("session") == last) & pl.col("eligible")).sort("symbol")
    assert at.height == 6
    # mean of the r's is 0 → resid == ret5 == r
    got = {r["symbol"]: r["resid"] for r in at.iter_rows(named=True)}
    for s, r in rmap.items():
        assert abs(got[s] - r) < 1e-6, (s, got[s], r)

    # ascending rank: most-negative residual = rank 0
    ranks = {r["symbol"]: r["rank_in_session"] for r in at.iter_rows(named=True)}
    assert ranks["A"] == 0 and ranks["F"] == 5
    ordered = sorted(rmap, key=lambda s: ranks[s])
    assert ordered[:3] == ["A", "B", "C"]   # longs (bottom-3 residual)
    assert ordered[-3:] == ["D", "E", "F"]  # shorts (top-3 residual)


def test_residual_is_demeaned_when_universe_biased():
    """A common drift cancels: residual = idiosyncratic part only."""
    sessions = _sessions(36)
    n = len(sessions)
    # add +0.10 to everyone → residuals unchanged (mean subtracted)
    rmap = {"A": 0.05, "B": 0.07, "C": 0.09, "D": 0.11, "E": 0.13, "F": 0.15}
    series = {s: [100.0] * (n - 1) + [100.0 * (1 + r)] for s, r in rmap.items()}
    sig = build_signal_frame(_closes_frame(series, sessions))
    last = sessions[-1]
    at = sig.filter((pl.col("session") == last) & pl.col("eligible"))
    mean_r = sum(rmap.values()) / len(rmap)
    got = {r["symbol"]: r["resid"] for r in at.iter_rows(named=True)}
    for s, r in rmap.items():
        assert abs(got[s] - (r - mean_r)) < 1e-6


# --------------------------------------------------------------------------- 2. gating


def test_universe_entry_gating_below_30_never_eligible(tmp_path):
    """A name with < 30 trailing sessions is never eligible and never trades."""
    sessions = _sessions(40)
    n = len(sessions)
    full = {s: [100.0 + i * 0.1 + 2 * k for i in range(n)]
            for k, s in enumerate(["A", "B", "C", "D", "E", "F"])}
    # G lists late (a COIN/PLTR-style IPO): only the last 20 sessions have data,
    # so n_hist maxes at 20 < 30 and G is never eligible.
    g_sessions = sessions[n - 20:]
    late = [100.0 + i for i in range(20)]

    rows: list[dict] = []
    for s, closes_list in full.items():
        for i, c in enumerate(closes_list):
            rows.append({"session": sessions[i], "symbol": s, "close": float(c)})
    for j, c in enumerate(late):
        rows.append({"session": g_sessions[j], "symbol": "G", "close": float(c)})
    closes = pl.DataFrame(rows).sort(["symbol", "session"])

    sig = build_signal_frame(closes)
    g = sig.filter(pl.col("symbol") == "G")
    assert g["eligible"].sum() == 0, "G has < 30 sessions everywhere → never eligible"
    assert g["n_hist"].max() == 20

    # and it never appears as a leg in a real run
    _write_bars(tmp_path, full, sessions)
    _write_bars(tmp_path, {"G": late}, g_sessions)

    legs, rebal, stats = run_xs_reversal(
        symbols=["A", "B", "C", "D", "E", "F", "G"],
        start=date.fromisoformat(sessions[30]),
        end=date.fromisoformat(sessions[-2]),
        cell="daily", bars_dir=tmp_path,
    )
    assert legs.height > 0
    assert "G" not in legs["symbol"].to_list()
    assert stats["universe_entry_dates"]["G"] is None


# --------------------------------------------------------------------------- 3. fees


def test_fee_sides_long_sells_at_exit_short_sells_at_entry():
    """SEC/TAF is on the SELL leg: long → exit price, short → entry; borrow shorts only."""
    entry, exit_px = 100.0, 110.0
    lng = compute_leg("2024-03-01", "2024-03-04", "X", 1, 0, -0.02, -0.02, entry, exit_px)
    sht = compute_leg("2024-03-01", "2024-03-04", "Y", -1, 5, 0.02, 0.02, entry, exit_px)

    # long: gross = +1000 bps; fee = 0.3 * exit/entry = 0.33; borrow 0
    assert abs(lng["gross_bps"] - 1000.0) < TOL
    assert abs(lng["fee_bps"] - SEC_TAF_SELL_BPS * (exit_px / entry)) < TOL
    assert lng["borrow_bps"] == 0.0
    assert abs(lng["net_bps"] - (1000.0 - SEC_TAF_SELL_BPS * (exit_px / entry))) < TOL
    assert lng["net_bps_borrow"] == lng["net_bps"]

    # short: gross = -1000 bps; fee = 0.3 (flat, sell at entry); borrow > 0 over 3 cal days
    assert abs(sht["gross_bps"] - (-1000.0)) < TOL
    assert abs(sht["fee_bps"] - SEC_TAF_SELL_BPS) < TOL
    assert sht["borrow_bps"] > 0.0
    assert abs(sht["borrow_bps"] - 50.0 * 3 / 365.0) < TOL
    assert abs(sht["net_bps"] - (-1000.0 - SEC_TAF_SELL_BPS)) < TOL
    assert abs(sht["net_bps_borrow"] - (sht["net_bps"] - sht["borrow_bps"])) < TOL


def test_split_suspect_flag():
    # args: (..., resid, ret5, entry_close, exit_close). |ret5| 0.75 > 0.40 → suspect.
    leg = compute_leg("2024-03-01", "2024-03-04", "X", 1, 0, -0.75, -0.75, 100.0, 99.0)
    assert leg["split_suspect"] is True
    # a big HOLDING move (split during the hold) also flags: exit 40 vs entry 100.
    leg_hold = compute_leg("2024-03-01", "2024-03-04", "X", 1, 0, -0.02, -0.02, 100.0, 40.0)
    assert leg_hold["split_suspect"] is True
    leg2 = compute_leg("2024-03-01", "2024-03-04", "X", 1, 0, -0.02, -0.02, 100.0, 99.0)
    assert leg2["split_suspect"] is False


# --------------------------------------------------------------------------- 4. holdout


def test_holdout_guard_rejects_end_in_holdout():
    # SealViolation, not AssertionError: the guard must survive `python -O` (B7/J2).
    with pytest.raises(SealViolation):
        assert_before_holdout(HOLDOUT_START)
    with pytest.raises(SealViolation):
        assert_before_holdout(date(2026, 6, 15))
    assert_before_holdout(date(2026, 5, 31))  # ok, no raise


def test_run_drops_rebalances_whose_exit_is_in_holdout(tmp_path):
    """A weekly entry whose t+5 exit lands >= holdout is dropped (never uses sealed data)."""
    # sessions straddling the holdout boundary
    days = calendar.trading_days(date(2026, 4, 1), date(2026, 6, 30))
    sessions = [d.isoformat() for d in days]
    n = len(sessions)
    series = {s: [100.0 + (i % 5) + k for i in range(n)]
              for k, s in enumerate(["A", "B", "C", "D", "E", "F"])}
    # ensure >=30 trailing sessions: prepend history
    hist_days = calendar.trading_days(date(2026, 1, 2), date(2026, 3, 31))
    hist = [d.isoformat() for d in hist_days]
    all_sessions = hist + sessions
    series = {s: [100.0 + (i % 5) + k for i in range(len(all_sessions))]
              for k, s in enumerate(["A", "B", "C", "D", "E", "F"])}
    _write_bars(tmp_path, series, all_sessions)

    legs, rebal, stats = run_xs_reversal(
        symbols=["A", "B", "C", "D", "E", "F"],
        start=date(2026, 5, 1), end=date(2026, 5, 31),
        cell="weekly", bars_dir=tmp_path,
    )
    # every entry AND exit session must be strictly before the holdout (sealed data
    # never enters the frame: load_closes strips it, so late entries whose t+5 exit
    # would be in the holdout fall into no_exit_session_in_range and are dropped).
    assert rebal.height > 0
    assert all(s < HOLDOUT_START.isoformat() for s in rebal["exit_session"].to_list())
    assert all(s < HOLDOUT_START.isoformat() for s in rebal["entry_session"].to_list())
    assert stats["counts"]["no_exit_session_in_range"] >= 1


# --------------------------------------------------------------------------- 5. weekly


def test_weekly_boundary_selection_picks_last_session_of_week():
    # 2024-01-02 (Tue) .. include a full week; Fridays are the week's last session
    days = calendar.trading_days(date(2024, 1, 2), date(2024, 1, 31))
    sessions = [d.isoformat() for d in days]
    weekly = rebalance_sessions(sessions, "weekly")
    # Jan 2024 Fridays: 5, 12, 19, 26 (all full trading days)
    assert "2024-01-05" in weekly
    assert "2024-01-12" in weekly
    assert "2024-01-19" in weekly
    assert "2024-01-26" in weekly
    # non-Friday mid-week sessions are NOT rebalance points
    assert "2024-01-10" not in weekly
    # each picked session is the max of its ISO week
    for s in weekly:
        y, w, _ = date.fromisoformat(s).isocalendar()
        same_week = [x for x in sessions if date.fromisoformat(x).isocalendar()[:2] == (y, w)]
        assert s == max(same_week)


def test_weekly_boundary_uses_last_session_when_friday_missing():
    # Good Friday 2024-03-29 is a holiday → Thursday 03-28 is the week's last session
    days = calendar.trading_days(date(2024, 3, 25), date(2024, 3, 29))
    sessions = [d.isoformat() for d in days]
    weekly = rebalance_sessions(sessions, "weekly")
    assert "2024-03-29" not in sessions          # holiday
    assert weekly == ["2024-03-28"]              # Thursday is the week's last session


def test_daily_cell_rebalances_every_session():
    sessions = _sessions(10)
    assert rebalance_sessions(sessions, "daily") == sessions


# --------------------------------------------------------------------------- 6. e2e fill identity


def test_moc_fills_equal_daily_closes(tmp_path):
    sessions = _sessions(40)
    n = len(sessions)
    series = {s: [100.0 + i * 0.5 + 3 * k for i in range(n)]
              for k, s in enumerate(["A", "B", "C", "D", "E", "F"])}
    _write_bars(tmp_path, series, sessions)
    legs, rebal, stats = run_xs_reversal(
        symbols=["A", "B", "C", "D", "E", "F"],
        start=date.fromisoformat(sessions[30]),
        end=date.fromisoformat(sessions[-2]),
        cell="daily", bars_dir=tmp_path,
    )
    closes = load_closes(["A", "B", "C", "D", "E", "F"], bars_dir=tmp_path)
    lu = {(r["session"], r["symbol"]): r["close"] for r in closes.iter_rows(named=True)}
    assert legs.height == 6 * rebal.height
    for r in legs.iter_rows(named=True):
        assert abs(lu[(r["entry_session"], r["symbol"])] - r["entry_close"]) < TOL
        assert abs(lu[(r["exit_session"], r["symbol"])] - r["exit_close"]) < TOL
    # book return == mean of the 6 legs' net_bps
    for rb in rebal.iter_rows(named=True):
        sub = legs.filter(pl.col("entry_session") == rb["entry_session"])
        assert abs(sub["net_bps"].mean() - rb["book_net_bps"]) < 1e-6
