"""Tests for enginev51/positioning.py — the M15 shadow positioning layer.

Everything runs on fabricated frames: deterministic selection/ranking, whole-share
sizing at deploy capital (incl. the unaffordable case), per-session independence,
the CUSUM edge-death monitor's arithmetic, and the forward-ledger integration
(portfolio columns survive the ledger round-trip; status carries the third stream
without touching the M10 gate keys).
"""

from __future__ import annotations

from datetime import date

import polars as pl

from enginev51 import positioning as pos
from enginev51.apps import forward_paper as fp


def _ev(session, symbol, *, p_win, basis=50.0, entry=100.0, net=3.0, tm=True):
    return {
        "session": session, "symbol": symbol, "basis_bps": basis, "p_win": p_win,
        "side": 1, "entry_px": entry, "exit_px": entry * 1.003,
        "cross_px": entry * 1.003, "net_bps": net,
        "taken_classical": True, "taken_meta": tm,
    }


def _frame(rows):
    return pl.DataFrame(rows, orient="row")


# --------------------------------------------------------------------------- selection


def test_selection_top_k_by_pwin_deterministic():
    rows = [
        _ev("2026-07-17", "NVDA", p_win=0.70),
        _ev("2026-07-17", "TSLA", p_win=0.65),
        _ev("2026-07-17", "AMD", p_win=0.60),
        _ev("2026-07-17", "MU", p_win=0.58),
        _ev("2026-07-17", "GOOGL", p_win=0.56),
    ]
    out = pos.apply_positioning(_frame(rows))
    sel = out.filter(pl.col("selected")).sort("sel_rank")
    assert sel["symbol"].to_list() == ["NVDA", "TSLA", "AMD"]  # top-3 by p_win
    assert sel["sel_rank"].to_list() == [1, 2, 3]
    dropped = out.filter(~pl.col("selected"))
    assert set(dropped["symbol"].to_list()) == {"MU", "GOOGL"}
    assert dropped["size_shares"].to_list() == [0, 0]


def test_selection_tiebreak_abs_basis_then_symbol():
    rows = [
        _ev("2026-07-17", "TSLA", p_win=0.60, basis=30.0),
        _ev("2026-07-17", "NVDA", p_win=0.60, basis=80.0),   # bigger |basis| wins tie
        _ev("2026-07-17", "MU", p_win=0.60, basis=30.0),     # ties TSLA -> symbol asc
        _ev("2026-07-17", "AMD", p_win=0.59, basis=500.0),   # lower p_win loses anyway
    ]
    out = pos.apply_positioning(_frame(rows))
    sel = out.filter(pl.col("selected")).sort("sel_rank")
    assert sel["symbol"].to_list() == ["NVDA", "MU", "TSLA"]


def test_non_meta_events_never_selected():
    rows = [
        _ev("2026-07-17", "NVDA", p_win=0.90, tm=False),  # not meta-gated
        _ev("2026-07-17", "TSLA", p_win=0.56),
    ]
    out = pos.apply_positioning(_frame(rows))
    sel = out.filter(pl.col("selected"))
    assert sel["symbol"].to_list() == ["TSLA"]


def test_sessions_are_independent():
    rows = [
        _ev("2026-07-17", s, p_win=p)
        for s, p in [("NVDA", 0.7), ("TSLA", 0.69), ("AMD", 0.68), ("MU", 0.67)]
    ] + [
        _ev("2026-07-20", s, p_win=p)
        for s, p in [("NVDA", 0.6), ("MU", 0.72)]
    ]
    out = pos.apply_positioning(_frame(rows))
    d1 = out.filter((pl.col("session") == "2026-07-17") & pl.col("selected"))
    d2 = out.filter((pl.col("session") == "2026-07-20") & pl.col("selected"))
    assert d1.height == 3 and d2.height == 2
    assert d2.sort("sel_rank")["symbol"].to_list() == ["MU", "NVDA"]


def test_empty_frame_gets_schema_columns():
    out = pos.apply_positioning(pl.DataFrame())
    assert set(pos.PORTFOLIO_COLS) <= set(out.columns)


# --------------------------------------------------------------------------- sizing


def test_equal_notional_whole_share_sizing():
    rows = [
        _ev("2026-07-17", "NVDA", p_win=0.70, entry=100.0),
        _ev("2026-07-17", "TSLA", p_win=0.65, entry=150.0),
        _ev("2026-07-17", "AMD", p_win=0.60, entry=90.0),
    ]
    out = pos.apply_positioning(_frame(rows))  # capital 10000 / 3 = 3333.33 target
    sel = out.filter(pl.col("selected")).sort("sel_rank")
    assert sel["size_shares"].to_list() == [33, 22, 37]  # floor(3333.33 / px)
    assert sel["size_notional"].to_list() == [3300.0, 3300.0, 3330.0]
    assert sel["implementable"].to_list() == [True, True, True]
    # deploy lens ($1,000 / 3 = $400 per slot): 4 / 2 / 4 shares -> all expressible
    assert sel["implementable_deploy"].to_list() == [True, True, True]


def test_unaffordable_share_is_flagged_not_hidden():
    rows = [
        _ev("2026-07-17", "NVDA", p_win=0.70, entry=6000.0),  # > per-slot capital
        _ev("2026-07-17", "TSLA", p_win=0.65, entry=100.0),
    ]
    out = pos.apply_positioning(_frame(rows))  # 10000 / 2 = 5000 per slot
    sel = out.filter(pl.col("selected")).sort("sel_rank")
    assert sel.filter(pl.col("symbol") == "NVDA")["size_shares"][0] == 0
    assert sel.filter(pl.col("symbol") == "NVDA")["implementable"][0] is False
    assert sel.filter(pl.col("symbol") == "TSLA")["size_shares"][0] == 50
    # still SELECTED (the research bps stream keeps it; sizing lens records the gap)
    assert sel.height == 2
    # deploy lens at $600/slot: NVDA no, TSLA yes (6 shares)
    assert sel.filter(pl.col("symbol") == "NVDA")["implementable_deploy"][0] is False
    assert sel.filter(pl.col("symbol") == "TSLA")["implementable_deploy"][0] is True


# --------------------------------------------------------------------------- CUSUM


def test_cusum_stays_quiet_while_edge_alive():
    daily = pl.DataFrame({
        "session": [f"2026-08-{d:02d}" for d in range(1, 21)],
        "n_sel": [3] * 20,
        "port_net_bps": [2.5] * 20,  # at the backtest reference
    })
    out = pos.cusum_series(daily)
    assert out["cusum_S"].to_list() == [0.0] * 20  # k - x = -1.25 -> clamped at 0
    assert not out["cusum_alert"].any()


def test_cusum_fires_on_dead_edge():
    n = 130
    daily = pl.DataFrame({
        "session": [f"s{d:03d}" for d in range(1, n + 1)],
        "n_sel": [3] * n,
        "port_net_bps": [0.0] * n,  # edge dead: S grows by k each day
    })
    out = pos.cusum_series(daily)
    # S_t = 1.25 * t; crosses h=150 strictly after day 120
    assert out["cusum_S"][119] == 150.0 and out["cusum_alert"][119] is False
    assert out["cusum_alert"][120] is True
    assert int(out.filter(pl.col("cusum_alert")).height) == n - 120


def test_cusum_resets_on_recovery():
    xs = [0.0] * 10 + [20.0] + [2.5] * 5  # bad run, one big win, then healthy
    daily = pl.DataFrame({
        "session": [f"2026-09-{d:02d}" for d in range(1, len(xs) + 1)],
        "n_sel": [3] * len(xs),
        "port_net_bps": xs,
    })
    out = pos.cusum_series(daily)
    assert out["cusum_S"][9] == 12.5          # 10 * 1.25
    assert out["cusum_S"][10] == 0.0          # max(0, 12.5 + 1.25 - 20)
    assert not out["cusum_alert"].any()


# --------------------------------------------------------------------------- ledger integration


def test_portfolio_columns_survive_ledger_roundtrip(tmp_path):
    rows = [
        _ev("2026-07-17", "NVDA", p_win=0.70, net=5.0),
        _ev("2026-07-17", "TSLA", p_win=0.65, net=-1.0),
        _ev("2026-07-17", "GOOGL", p_win=0.40, net=2.0, tm=False),
    ]
    scored = pos.apply_positioning(_frame(rows))
    ledger_path = tmp_path / "ledger.parquet"
    fp.append_ledger(fp.ledger_rows(scored, date(2026, 7, 17)), ledger_path)
    led = fp.load_ledger(ledger_path)
    assert set(pos.PORTFOLIO_COLS) <= set(led.columns)
    assert led.filter(pl.col("selected")).height == 2

    st = fp.status_stats(led)
    p = st["portfolio"]
    assert p["n_events"] == 2 and p["n_sessions"] == 1
    assert p["mean_net_bps"] == 2.0  # (5 - 1) / 2
    assert p["implementable_rate"] == 1.0
    assert p["implementable_deploy_rate"] == 1.0  # $600/slot buys 6 shares @ $100
    assert p["cusum_alert"] is False
    # the M10 gate never reads the portfolio stream
    assert "portfolio" not in st["gate"]
    # status text carries the shadow stream + monitor
    txt = fp.format_status(st)
    assert "portfolio SHADOW" in txt and "edge-death monitor" in txt


def test_ledger_rows_fill_missing_portfolio_columns():
    # a scored frame WITHOUT positioning applied still projects onto the schema
    scored = _frame([_ev("2026-07-17", "NVDA", p_win=0.70)])
    rows = fp.ledger_rows(scored, date(2026, 7, 17))
    assert list(rows.columns) == list(fp.LEDGER_SCHEMA)
    assert rows["selected"][0] is None


def test_portfolio_stats_empty_paths():
    assert pos.portfolio_stats(pl.DataFrame(schema=fp.LEDGER_SCHEMA))["n_events"] == 0
    st = fp.status_stats(pl.DataFrame(schema=fp.LEDGER_SCHEMA))
    assert st["portfolio"]["n_events"] == 0
    assert "no events yet" in fp.format_status(st)
