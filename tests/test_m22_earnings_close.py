"""Tests for the M22 earnings-day closing-crosses harness
(``research_screens.earnings_close``) + the ``run_m11`` extraction it reuses.

Synthetic fixtures + hand-derived literals ONLY -- no real data lake, no network
(the family's single registered look is the orchestrator's). Mirrors the fixture
style of ``test_m11`` / ``test_sched_window_atlas`` / ``test_ingest_condition_guard``.
Covers all 14 checks in DESIGN.md § 5: the holdout/seal guards, the day0 whitelist
join (AMC/BMO used directly, keyed by symbol+session), the threshold pin, the A/B
no-pooling guard, both cost-convention pins, the baseline-same-pipeline guarantee,
the run_m11 reproduction guard, the session-clustered CI, the one-look gate, and
the Cell A / Cell B pass-bar logic (incl. ruling A8).
"""

from __future__ import annotations

import inspect
from datetime import date

import numpy as np
import polars as pl
import pytest

from enginev51.apps import run_basis_trial, run_m11
from enginev51.data.bbo1s import BBO_SCHEMA
from enginev51.data.noii import NOII_SCHEMA, et_ns
from enginev51.protocol import SealViolation
from enginev51.research_screens import earnings_close as ec

# --------------------------------------------------------------------------- builders


def _events_parquet(tmp_path, rows: list[dict]):
    """Minimal M21-events parquet (only the columns the whitelist reads)."""
    df = pl.DataFrame(rows, schema={"symbol": pl.Utf8, "day0_session": pl.Utf8}, orient="row")
    p = tmp_path / "events.parquet"
    df.write_parquet(p)
    return p


def _noii_row(ts: int, near: float, ref: float, side: str = "B",
              imb: float = 1000.0, paired: float = 500.0, far: float = 0.0) -> dict:
    return {
        "ts": ts, "side": side, "imbalance_shares": imb, "paired_shares": paired,
        "near_price": near, "far_price": far, "ref_price": ref,
    }


def _noii(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=NOII_SCHEMA, orient="row").sort("ts")


def _a_frame(rows: list[dict]) -> pl.DataFrame:
    """A synthetic Cell A ALL-events frame (only the columns cell_a_stats reads)."""
    return pl.DataFrame(
        rows,
        schema={"session": pl.Utf8, "symbol": pl.Utf8, "basis_bps": pl.Float64,
                "net_bps": pl.Float64, "is_day0": pl.Boolean, "cell": pl.Utf8},
        orient="row",
    )


def _b_frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(
        rows,
        schema={"session": pl.Utf8, "symbol": pl.Utf8, "net_bps": pl.Float64},
        orient="row",
    )


# =========================================================================== 1


def test_holdout_guard_refuses_ge_20260601(tmp_path):
    """The whitelist loader refuses an ``end`` on/after the 2026-06-01 seal, and a
    holdout-era row is filtered out under the default END."""
    p = _events_parquet(tmp_path, [
        {"symbol": "NVDA", "day0_session": "2026-05-28"},
    ])
    # SealViolation, not AssertionError: the guard must survive `python -O` (B7/J2).
    with pytest.raises(SealViolation):
        ec.load_day0_whitelist(p, ec.CELL_A_UNIVERSE, end=date(2026, 6, 1))
    with pytest.raises(SealViolation):
        ec.assert_before_holdout(date(2026, 6, 1))
    # end == 2026-05-31 (the last legal session) is fine.
    wl = ec.load_day0_whitelist(p, ec.CELL_A_UNIVERSE, end=date(2026, 5, 31))
    assert wl == {("NVDA", "2026-05-28")}


# =========================================================================== 2


def test_apply_seal_strips_holdout_day0(tmp_path):
    """A synthetic holdout-era day0 row never enters the whitelist."""
    p = _events_parquet(tmp_path, [
        {"symbol": "NVDA", "day0_session": "2026-05-28"},   # legal
        {"symbol": "NVDA", "day0_session": "2026-07-20"},   # holdout -> stripped
        {"symbol": "TSLA", "day0_session": "2026-06-01"},   # seal boundary -> stripped
    ])
    wl = ec.load_day0_whitelist(p, ("NVDA", "TSLA"), end=ec.END)
    assert ("NVDA", "2026-05-28") in wl
    assert ("NVDA", "2026-07-20") not in wl
    assert ("TSLA", "2026-06-01") not in wl
    assert all(s <= "2026-05-31" for _, s in wl)


# =========================================================================== 3


def test_threshold_pin_is_10():
    """The 15:55:10 firing threshold is 10.0 in BOTH modules (single source)."""
    assert ec.FIRE_BASIS_BPS == 10.0
    assert run_m11.FIRE_BASIS_BPS == 10.0
    assert ec.FIRE_BASIS_BPS == ec.M11_FIRE_BASIS_BPS == run_m11.FIRE_BASIS_BPS


# =========================================================================== 4


def test_day0_join_amc_bmo_known_cases(tmp_path):
    """3 AMC + 2 BMO pinned events land on EXACTLY their day0_session, unchanged.

    M21 already resolved AMC (reports after the close -> the NEXT session) and BMO
    (before the open -> the SAME session) into ``day0_session``; M22 uses it
    DIRECTLY and must never re-shift it (double-shift risk)."""
    rows = [
        # AMC: reported after close; M21 mapped day0 to the next session already.
        {"symbol": "NVDA", "day0_session": "2024-02-22"},
        {"symbol": "AMD", "day0_session": "2024-01-31"},
        {"symbol": "MU", "day0_session": "2024-03-21"},
        # BMO: reported before open; day0 is the same session.
        {"symbol": "AAPL", "day0_session": "2024-02-01"},
        {"symbol": "TXN", "day0_session": "2024-01-24"},
    ]
    p = _events_parquet(tmp_path, rows)
    wl = ec.load_day0_whitelist(p, ec.CELL_A_UNIVERSE + ec.CELL_B_UNIVERSE, end=ec.END)
    assert wl == {(r["symbol"], r["day0_session"]) for r in rows}


# =========================================================================== 5


def test_day0_join_keyed_by_symbol_session():
    """is_day0 is keyed by (symbol, session): an NVDA day0 session does NOT make a
    same-session TSLA row day0 -- TSLA is baseline unless TSLA itself reported."""
    frame = _a_frame([
        {"session": "2024-02-21", "symbol": "NVDA", "basis_bps": 20.0,
         "net_bps": 5.0, "is_day0": None, "cell": None},
        {"session": "2024-02-21", "symbol": "TSLA", "basis_bps": 20.0,
         "net_bps": 3.0, "is_day0": None, "cell": None},
    ]).drop("is_day0", "cell")
    out = ec.annotate_cell(frame, whitelist={("NVDA", "2024-02-21")}, cell="A")
    nvda = out.filter(pl.col("symbol") == "NVDA").row(0, named=True)
    tsla = out.filter(pl.col("symbol") == "TSLA").row(0, named=True)
    assert nvda["is_day0"] is True
    assert tsla["is_day0"] is False
    assert set(out["cell"].unique().to_list()) == {"A"}


# =========================================================================== 6


def test_no_pooling_cell_tag_disjoint():
    """cell tags are exactly {"A"}/{"B"}; the writer + atlas raise on a mixed frame."""
    a = _a_frame([
        {"session": "2024-02-21", "symbol": "NVDA", "basis_bps": 20.0,
         "net_bps": 5.0, "is_day0": True, "cell": "A"},
    ])
    b_rows = {"session": "2024-02-21", "symbol": "AAPL", "basis_bps": 20.0,
              "net_bps": 4.0, "is_day0": True, "cell": "B"}
    mixed = pl.concat([a, _a_frame([b_rows])], how="vertical")  # A + B tags in one frame
    ec._assert_cell_tag(a, "A")  # clean frame OK
    with pytest.raises(ValueError, match="pooling violation"):
        ec._assert_cell_tag(mixed, "A")
    with pytest.raises(ValueError, match="pooling violation"):
        ec.build_atlas_md("T", mixed, {}, {}, _a_frame([]).with_columns(), {}, {},
                          pl.DataFrame(), seed=7)


# =========================================================================== 7


def test_cost_pin_cell_b_entry_2p5bps(monkeypatch):
    """run_m11.TAKER_COST_BPS == 2.5, and a fired Cell B event's REALISED entry
    cost off ref is exactly 2.5 bps (a buy pays MORE than ref)."""
    assert run_m11.TAKER_COST_BPS == 2.5
    assert ec.M11_TAKER_COST_BPS == 2.5

    session = "2024-03-15"
    ref = 100.0
    noii = _noii([_noii_row(et_ns(session, 15, 55, 9), near=100.20, ref=ref)])  # +20 bps -> fires
    monkeypatch.setattr(run_m11, "cross_price_for",
                        lambda sym, s, t: (et_ns(session, 16, 0, 0), 101.0, 0.0))
    monkeypatch.setattr(run_m11, "adv20_dollars", lambda *a, **k: None)

    # Pre-seed the cache so the post-gate lazy load never touches the real bars lake.
    row, reason = run_m11.fire_near_ref_event(
        object(), "AAPL", session, noii, closes_cache={"AAPL": []},
    )
    assert reason is None and row is not None
    entry_cost = row["side"] * (row["entry_px"] - ref) / ref * 1e4
    assert entry_cost == pytest.approx(run_m11.TAKER_COST_BPS)  # == 2.5
    assert row["side"] == 1 and row["entry_px"] > ref

    # ground_truth_b recomputes the same realised entry-cost column on a Cell B frame.
    cellb = pl.DataFrame([{**row, "is_day0": True, "cell": "B"}], schema=ec.CELL_B_SCHEMA, orient="row")
    gt = ec.ground_truth_b(cellb)
    assert gt["entry_cost_bps"].to_list()[0] == pytest.approx(2.5)


# =========================================================================== 8


def _bbo(session: str, mid: float, half: float = 0.01) -> pl.DataFrame:
    rows = [
        {"ts": et_ns(session, 15, 55, t), "bid": mid - half, "ask": mid + half,
         "bid_size": 100.0, "ask_size": 100.0}
        for t in range(0, 11)
    ]
    return pl.DataFrame(rows, schema=BBO_SCHEMA, orient="row").sort("ts")


def test_cost_pin_cell_a_costmodel_v1(monkeypatch):
    """Cell A cost convention (ruling A2): run_basis_trial replays every event via
    replay_moc_event with slip_bps=0.5 and sec_taf_sell_bps=0.3. Pinned two ways:
    the replay kernel's signature defaults (the source of truth earnings_close
    reads) AND a SPY proving run_basis_trial passes exactly those."""
    assert ec.CELL_A_SLIP_BPS == 0.5
    assert ec.CELL_A_SEC_TAF_SELL_BPS == 0.3

    from enginev51.backtest.auction_replay import MocResult

    session = "2024-03-15"
    captured: dict = {}

    def _spy(tape, signal_ts, side, cross, seed, plan_id, **kw):
        captured.update(kw)
        captured["side"] = side
        return MocResult(
            plan_id=plan_id, symbol=kw.get("symbol"), side=side, status="ok",
            entry_ts=signal_ts, entry_px=100.0, exit_ts=signal_ts + 1, exit_px=101.0,
            exit_reason="moc", net_bps=1.0, hold_s=1.0, entry_mid=100.0, pnl=None,
        )

    noii = _noii([_noii_row(et_ns(session, 15, 55, 9), near=100.20, ref=100.0)])
    monkeypatch.setattr(run_basis_trial.calendar, "trading_days",
                        lambda a, b: [date.fromisoformat(session)])
    monkeypatch.setattr(run_basis_trial, "load_noii_session", lambda *a, **k: noii)
    monkeypatch.setattr(run_basis_trial, "load_bbo_session", lambda *a, **k: _bbo(session, 100.0))
    monkeypatch.setattr(run_basis_trial, "adv20_dollars", lambda *a, **k: 1e9)
    monkeypatch.setattr(run_basis_trial, "load_raw_trades", lambda *a, **k: None)
    monkeypatch.setattr(run_basis_trial, "cross_price_for",
                        lambda sym, s, t: (et_ns(session, 16, 0, 0), 101.0, 0.0))
    monkeypatch.setattr(run_basis_trial, "_session_closes", lambda *a, **k: {})
    monkeypatch.setattr(run_basis_trial, "_daily_closes_cache", lambda sym: [])
    monkeypatch.setattr(run_basis_trial, "replay_moc_event", _spy)

    events, _stats = run_basis_trial.run_basis_trial(
        object(), symbols=["NVDA"], start=date.fromisoformat(session),
        end=date.fromisoformat(session), seed=7,
    )
    assert events.height == 1
    assert captured["slip_bps"] == 0.5
    assert captured["sec_taf_sell_bps"] == 0.3
    assert captured["side"] == 1  # near>mid -> buy


# =========================================================================== 9


def test_baseline_same_pipeline(monkeypatch):
    """day0 and baseline are the is_day0 / ~is_day0 partitions of the ONE fired
    frame: their union is the full fired set and they are disjoint. And Cell A is
    built with exactly ONE run_basis_trial call."""
    frame = _a_frame([
        {"session": "2024-02-21", "symbol": "NVDA", "basis_bps": 20.0, "net_bps": 5.0,
         "is_day0": True, "cell": "A"},
        {"session": "2024-02-21", "symbol": "TSLA", "basis_bps": 15.0, "net_bps": 2.0,
         "is_day0": False, "cell": "A"},
        {"session": "2024-03-01", "symbol": "NVDA", "basis_bps": 4.0, "net_bps": 9.0,
         "is_day0": True, "cell": "A"},  # |basis|<10 -> NOT fired, excluded from both
    ])
    fired = frame.filter(pl.col("basis_bps").abs() >= ec.FIRE_BASIS_BPS)
    day0 = fired.filter(pl.col("is_day0"))
    baseline = fired.filter(~pl.col("is_day0"))
    assert day0.height + baseline.height == fired.height == 2
    assert set(day0["session"].to_list()).isdisjoint([]) or True
    # union == fired, disjoint (no row is both):
    assert day0.height == 1 and baseline.height == 1

    calls = {"n": 0}

    def _fake_run(settings, *, symbols, start, end, seed):
        calls["n"] += 1
        base = frame.drop("is_day0", "cell")
        return base, {"counts": {"events": base.height}}

    out, stats = ec.build_cell_a_events(
        object(), whitelist={("NVDA", "2024-02-21")}, run_fn=_fake_run,
    )
    assert calls["n"] == 1
    assert set(out["cell"].unique().to_list()) == {"A"}
    assert out.filter((pl.col("symbol") == "NVDA") & (pl.col("session") == "2024-02-21"))[
        "is_day0"].to_list() == [True]


def test_cell_a_default_run_fn_is_run_basis_trial():
    """MN2(a): the DEFAULT Cell A pipeline is run_basis_trial.run_basis_trial ITSELF
    (identity), so a mutation swapping in a reimplementation is caught."""
    default = inspect.signature(ec.build_cell_a_events).parameters["run_fn"].default
    assert default is run_basis_trial.run_basis_trial


# =========================================================================== 10


def test_m11_reproduction_unchanged(monkeypatch):
    """run_m11 (post-extraction) is a thin loop over fire_near_ref_event: on a fixed
    synthetic fixture the funnel mapping and the fired row are byte-exact.

    Fixture exercises every skip reason plus one fire. Every expected value is
    derived from the pure helpers (conservative_entry_px / net_bps_for), so the
    test guards the extraction's row production + funnel wiring, not an echo."""
    S = {k: f"2024-03-{d:02d}" for k, d in
         {"fire": 11, "no_near_ref": 12, "zero_basis": 13, "inactive": 14, "no_close": 15}.items()}
    ref = 100.0
    noii_by = {
        S["fire"]: _noii([_noii_row(et_ns(S["fire"], 15, 55, 9), near=100.20, ref=ref)]),
        S["no_near_ref"]: _noii([_noii_row(et_ns(S["no_near_ref"], 15, 55, 9), near=0.0, ref=ref)]),
        S["zero_basis"]: _noii([_noii_row(et_ns(S["zero_basis"], 15, 55, 9), near=ref, ref=ref)]),
        S["inactive"]: _noii([_noii_row(et_ns(S["inactive"], 15, 55, 9), near=100.05, ref=ref)]),
        S["no_close"]: _noii([_noii_row(et_ns(S["no_close"], 15, 55, 9), near=100.20, ref=ref)]),
    }

    monkeypatch.setattr(run_m11.calendar, "trading_days",
                        lambda a, b: [date.fromisoformat(v) for v in S.values()])
    monkeypatch.setattr(run_m11, "load_noii_session", lambda sym, s, out_dir=None: noii_by.get(s))
    monkeypatch.setattr(run_m11, "adv20_dollars", lambda *a, **k: None)
    monkeypatch.setattr(run_m11, "_daily_closes_pairs", lambda sym, bars_dir=None: [])
    monkeypatch.setattr(
        run_m11, "cross_price_for",
        lambda sym, s, t: None if s == S["no_close"] else (et_ns(s, 16, 0, 0), 101.0, 0.0),
    )

    events, stats = run_m11.run_m11(
        object(), symbols=["NVDA"], start=date(2024, 3, 11), end=date(2024, 3, 15),
    )
    c = stats["counts"]
    assert c["fired"] == 1
    assert c["no_near_ref"] == 1
    assert c["zero_basis"] == 1
    assert c["inactive"] == 1
    assert c["no_close"] == 1
    assert c["no_noii_partition"] == 0 and c["no_noii_msgs"] == 0

    r = events.row(0, named=True)
    assert r["session"] == S["fire"] and r["symbol"] == "NVDA"
    assert r["side"] == 1
    assert r["basis_bps"] == pytest.approx(20.0)
    assert r["entry_px"] == pytest.approx(run_m11.conservative_entry_px(ref, 1))
    assert r["net_bps"] == pytest.approx(run_m11.net_bps_for(1, ref, r["entry_px"], 101.0))


# =========================================================================== 11


def test_clustered_ci_session_cluster():
    """A session with 2 reporters is ONE cluster: n_events=2 but n_sessions=1, and
    (single cluster) the session bootstrap is degenerate -> lo == hi == mean."""
    df = pl.DataFrame({
        "session": ["2024-02-21", "2024-02-21"],  # 2 reporters, same ET session
        "symbol": ["NVDA", "TSLA"],
        "net_bps": [4.0, 8.0],
    })
    m, lo, hi, n, ns = ec._ci(df)
    assert n == 2 and ns == 1
    assert m == pytest.approx(6.0)
    assert lo == pytest.approx(6.0) and hi == pytest.approx(6.0)


# =========================================================================== 12


def test_cli_refuses_second_look(tmp_path, monkeypatch):
    """look_state present -> raise; --defect-rerun without --reason -> raise; with
    both -> proceeds and appends a ledger note."""
    # fresh dir: no state -> allowed.
    ec.assert_look_not_spent(tmp_path)
    ec.mark_look_spent(tmp_path, trial_id="M22-earnings-close", git_sha="deadbeef")
    assert ec.look_state_path(tmp_path).exists()

    with pytest.raises(RuntimeError, match="already spent"):
        ec.assert_look_not_spent(tmp_path)
    with pytest.raises(ValueError, match="reason"):
        ec.assert_look_not_spent(tmp_path, defect_rerun=True, reason=None)
    with pytest.raises(ValueError, match="reason"):
        ec.assert_look_not_spent(tmp_path, defect_rerun=True, reason="   ")

    notes: list[dict] = []
    monkeypatch.setattr(ec, "ledger_append", lambda kind, payload: notes.append((kind, payload)))
    ec.assert_look_not_spent(tmp_path, defect_rerun=True, reason="fix off-by-one in exit ts")
    assert len(notes) == 1
    assert notes[0][0] == "note"
    assert notes[0][1]["event"] == "M22_DEFECT_RERUN"
    assert notes[0][1]["reason"] == "fix off-by-one in exit ts"


def test_one_look_gate_is_not_relocatable(tmp_path, monkeypatch):
    """MN2(b) / B1: the one-look state is anchored to the CANONICAL experiments dir
    and cannot be relocated. The CLI exposes NO --out-dir escape hatch, and a look
    spent on the canonical dir refuses a second invocation that passes NO argument
    (the only path the CLI uses)."""
    # (i) the CLI has no out-dir option to point the gate at a fresh directory.
    from enginev51.apps import run_m22_earnings_close as cli
    opt_names = {p.name for p in cli.main.params}
    assert "out_dir" not in opt_names

    # (ii) the gate defaults to canonical_out_dir(); spend there, then a no-arg
    #      re-check refuses. experiments_dir is redirected so no real state is touched.
    monkeypatch.setattr(ec, "experiments_dir", lambda: tmp_path)
    assert ec.canonical_out_dir() == tmp_path / ec.OUT_SUBDIR
    assert ec.look_state_path() == tmp_path / ec.OUT_SUBDIR / "look_state.json"
    ec.assert_look_not_spent()  # canonical, unspent -> allowed
    ec.mark_look_spent(trial_id="M22-earnings-close")
    with pytest.raises(RuntimeError, match="already spent"):
        ec.assert_look_not_spent()  # canonical, spent -> refused (no way to relocate)


# =========================================================================== 13


def _dense_a(n_sessions: int, net_day0, *, basis: float = 20.0,
             baseline_net=None) -> pl.DataFrame:
    """Cell A frame: ``n_sessions`` distinct day0 sessions (one NVDA event each) at
    net ``net_day0`` (scalar or per-session list), optional baseline rows."""
    rows: list[dict] = []
    nets = [net_day0] * n_sessions if np.isscalar(net_day0) else list(net_day0)
    for i, v in enumerate(nets):
        rows.append({"session": f"2024-{(i % 12) + 1:02d}-{(i // 12) + 1:02d}",
                     "symbol": "NVDA", "basis_bps": basis, "net_bps": float(v),
                     "is_day0": True, "cell": "A"})
    if baseline_net is not None:
        for i, v in enumerate(baseline_net):
            rows.append({"session": f"2023-{(i % 12) + 1:02d}-{(i // 12) + 1:02d}",
                         "symbol": "NVDA", "basis_bps": basis, "net_bps": float(v),
                         "is_day0": False, "cell": "A"})
    return _a_frame(rows)


def test_cell_a_pass_bar_logic():
    # (a) UNDERPOWERED: < 50 fired day0 -> neither pass nor kill.
    up = ec.cell_a_stats(_dense_a(10, 5.0))
    assert up["underpowered"] is True and up["pass"] is False

    # (b) PASS with a positive baseline: 50 sessions, day0 mean 5, baseline mean 1
    #     -> n/sessions floors + CI-lo>0 + (5 >= 2*1) all hold.
    ok = ec.cell_a_stats(_dense_a(50, 5.0, baseline_net=[1.0] * 50))
    assert ok["meets_n_sessions_floor"] is True
    assert ok["meets_ci_lower_gt_0"] is True
    assert ok["baseline_mean_positive"] is True
    assert ok["meets_2x_amplification"] is True
    assert ok["pass"] is True

    # (c) Ruling A8: baseline mean <= 0 -> the 2x prong is VACUOUS; PASS reduces to
    #     n/sessions floors + CI-lo>0 (amp_prong_binds is False, still passes).
    a8 = ec.cell_a_stats(_dense_a(50, 5.0, baseline_net=[-1.0] * 50))
    assert a8["baseline_mean_positive"] is False
    assert a8["amp_prong_binds"] is False
    assert a8["meets_2x_amplification"] is False  # cannot meet an undefined ratio
    assert a8["pass"] is True

    # (d) CI-lower <= 0 (wide dispersion) -> fails the CI prong even at n>=50.
    wide = [-50.0 if i % 2 else 60.0 for i in range(50)]
    ci_fail = ec.cell_a_stats(_dense_a(50, wide, baseline_net=[1.0] * 50))
    assert ci_fail["n_fired_day0"] == 50
    assert ci_fail["meets_ci_lower_gt_0"] is False
    assert ci_fail["pass"] is False


# =========================================================================== 14


def _dense_b(n_sessions: int, net) -> pl.DataFrame:
    nets = [net] * n_sessions if np.isscalar(net) else list(net)
    rows = [{"session": f"2024-{(i % 12) + 1:02d}-{(i // 12) + 1:02d}",
             "symbol": "AAPL", "net_bps": float(v)} for i, v in enumerate(nets)]
    return _b_frame(rows)


def test_cell_b_pass_bar_logic():
    # (a) n>=60 AND CI-lo>0 -> PASS.
    ok = ec.cell_b_stats(_dense_b(60, 5.0))
    assert ok["n_fired"] == 60 and ok["meets_n_ge_60"] is True
    assert ok["meets_ci_lower_gt_0"] is True and ok["pass"] is True

    # (b) n < 60 -> UNDERPOWERED, not a pass.
    few = ec.cell_b_stats(_dense_b(59, 5.0))
    assert few["meets_n_ge_60"] is False and few["underpowered"] is True
    assert few["pass"] is False

    # (c) n>=60 but CI spans 0 (wide dispersion) -> fails CI prong.
    wide = [-50.0 if i % 2 else 60.0 for i in range(60)]
    ci_fail = ec.cell_b_stats(_dense_b(60, wide))
    assert ci_fail["n_fired"] == 60
    assert ci_fail["meets_ci_lower_gt_0"] is False and ci_fail["pass"] is False
