"""Tests for the M20-FORWARD revival screen (``research_screens.sched_window_forward``
+ ``apps.run_sched_window_forward``). Synthetic bbo frames + temp dirs only — no real
lake, no real ledger/state, no network. Covers the hard activation gate (all four
refusal/acceptance cases), placebo-day selection, real/placebo prior separation,
seed-then-run C2 continuity, ledger idempotence, forward PIT-poison, the report-only
sizing column, and the missing-bbo / calendar-exceeded refusals.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from enginev51.apps import run_sched_window_forward as app
from enginev51.data.bbo1s import BBO_SCHEMA
from enginev51.data.noii import et_ns
from enginev51.research_screens import sched_window_forward as swf

ET = ZoneInfo("America/New_York")
NS = 1_000_000_000


# --------------------------------------------------------------------------- builders


def _row(ts: int, bid: float, ask: float) -> dict:
    return {"ts": int(ts), "bid": float(bid), "ask": float(ask),
            "bid_size": 100.0, "ask_size": 100.0}


def _frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=BBO_SCHEMA, orient="row").sort("ts")


def _mid_q(mid: float, half: float = 0.01) -> tuple[float, float]:
    return mid - half, mid + half


def _seconds(session: str, t0: tuple, t1: tuple):
    return range(et_ns(session, *t0), et_ns(session, *t1) + NS, NS)


def _tape(session: str, anchor: float, react: float, exit_: float) -> pl.DataFrame:
    """Dense 1s morning tape + a 15:00 marker (so it is NOT an early close)."""
    rows = []
    for t in _seconds(session, (9, 59, 0), (11, 10, 0)):
        if t <= et_ns(session, 10, 4, 58):
            mid = anchor
        elif t <= et_ns(session, 10, 20, 0):
            mid = react
        else:
            mid = exit_
        rows.append(_row(t, *_mid_q(mid)))
    rows.append(_row(et_ns(session, 15, 0, 0), *_mid_q(exit_)))
    return _frame(rows)


def _poison_tape(session: str) -> pl.DataFrame:
    """anchor 100 -> react/entry 101 -> POISON 200 from the bucket starting AT decision."""
    rows = []
    for t in _seconds(session, (9, 59, 0), (11, 10, 0)):
        if t <= et_ns(session, 10, 4, 58):
            mid = 100.0
        elif t <= et_ns(session, 10, 5, 24):
            mid = 101.0
        else:
            mid = 200.0
        rows.append(_row(t, *_mid_q(mid)))
    rows.append(_row(et_ns(session, 15, 0, 0), *_mid_q(200.0)))
    return _frame(rows)


def _cal_rows(events: list[dict]) -> pl.DataFrame:
    rows = []
    for e in events:
        y, mo, d = (int(x) for x in e["session"].split("-"))
        anchor = datetime(y, mo, d, e.get("h", 10), e.get("m", 0), e.get("s", 0), tzinfo=ET)
        rows.append(
            {
                "release_id": e["release_id"],
                "class": e["cls"],
                "subtype": e.get("subtype", "ISM_MFG"),
                "session_date": datetime(y, mo, d),
                "sched_ts_et": anchor,
                "anchor_ts_et": anchor,
                "source": "test",
            }
        )
    return pl.DataFrame(rows)


def _with_session(raw: pl.DataFrame) -> pl.DataFrame:
    return raw.with_columns(pl.col("session_date").cast(pl.Date).cast(pl.Utf8).alias("_session"))


def _write_cal(tmp_path, events: list[dict]):
    p = tmp_path / "cal.parquet"
    _cal_rows(events).write_parquet(p)
    return p


def _getter(mapping: dict):
    def g(symbol: str, session: str):
        return mapping.get((symbol, session))

    return g


def _complete_reg(reg_root, *, min_sessions=40, min_events=150) -> dict:
    reg_root.mkdir(parents=True, exist_ok=True)
    cfg = {
        "registered": True,
        "trial_id": "M20F-TEST",
        "family": "sched_window_fwd_v1",
        "cells": ["cluster_1000|C2|h30", "cluster_1000|C2|h60"],
        "gate": {"min_sessions": min_sessions, "min_events": min_events, "rule": "frozen"},
        "placebo_kill": {"rule": "frozen"},
        "sizing_form": "clip(E_train/floor, 0, 2) * 10000 USD -- report-only",
    }
    (reg_root / "registration.json").write_text(json.dumps(cfg), encoding="utf-8")
    return cfg


def _fixtures(tmp_path):
    pass_p = tmp_path / "train_pass_list.json"
    floors_p = tmp_path / "cost_floors.json"
    pass_p.write_text(json.dumps({
        "cells": ["cluster_1000|C2|h30", "cluster_1000|C2|h60"],
        "train_means": {"cluster_1000|C2|h30": 9.2675, "cluster_1000|C2|h60": 12.9287},
    }), encoding="utf-8")
    floors_p.write_text(json.dumps({"class_floor_bps": {"cluster_1000": 4.0477}}),
                        encoding="utf-8")
    return pass_p, floors_p


# Pre-holdout (train+validate, < 2026-06-01) so the STRICT seed boundary admits them.
_SEED_DAYS = [f"2026-05-{d:02d}" for d in (1, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 18)]  # 12


def _seed_events(days: list[str]) -> list[dict]:
    return [{"release_id": f"ISM-{s}", "cls": "cluster_1000", "session": s} for s in days]


# ======================================================================= 1-4. GATE


def test_gate_refuses_without_file(tmp_path):
    with pytest.raises(swf.RegistrationMissing, match="DR-X9"):
        swf.load_registration(tmp_path / "reg")


def test_gate_refuses_registered_false(tmp_path):
    reg = tmp_path / "reg"
    reg.mkdir()
    (reg / "registration.json").write_text(json.dumps({
        "registered": False, "trial_id": "x", "family": "y",
        "gate": {"min_sessions": 40, "min_events": 150},
    }), encoding="utf-8")
    with pytest.raises(swf.RegistrationMissing, match="registered is not true"):
        swf.load_registration(reg)


def test_gate_refuses_null_gate_numbers(tmp_path):
    reg = tmp_path / "reg"
    reg.mkdir()
    (reg / "registration.json").write_text(json.dumps({
        "registered": True, "trial_id": "x", "family": "y",
        "gate": {"min_sessions": None, "min_events": None, "rule": "TBD"},
    }), encoding="utf-8")
    with pytest.raises(swf.RegistrationMissing, match="null gate fields"):
        swf.load_registration(reg)


def test_gate_accepts_complete_config(tmp_path):
    reg = tmp_path / "reg"
    cfg = _complete_reg(reg)
    got = swf.load_registration(reg)
    assert got == cfg
    assert got["registered"] is True


def test_run_asof_refuses_without_registration(tmp_path):
    # the run entry point itself must refuse pre-registration (touches lake/ledger).
    cal = _write_cal(tmp_path, _seed_events(["2026-07-17"]))
    with pytest.raises(swf.RegistrationMissing):
        swf.run_asof(date(2026, 7, 17), calendar_path=cal, reg_root=tmp_path / "reg",
                     get_bbo=_getter({}))


def test_template_file_shipped():
    # the module ships an inert template with the exact gate skeleton.
    p = swf.template_path()
    assert p.exists()
    tmpl = json.loads(p.read_text(encoding="utf-8"))
    assert tmpl["registered"] is False
    assert tmpl["gate"]["min_sessions"] is None and tmpl["gate"]["min_events"] is None
    assert tmpl["cells"] == ["cluster_1000|C2|h30", "cluster_1000|C2|h60"]


# ======================================================================= 5. PLACEBO SELECT


def test_placebo_day_selection_exact(tmp_path):
    cal = _with_session(_cal_rows([
        {"release_id": "E1", "cls": "cluster_1000", "session": "2026-07-17"},
        {"release_id": "E2", "cls": "fomc_stmt", "session": "2026-07-29", "h": 14},
    ]))
    # gap sessions become placebo; event days never do.
    assert swf.is_placebo_session(cal, "2026-07-20") is True
    assert swf.is_placebo_session(cal, "2026-07-21") is True
    assert swf.is_placebo_session(cal, "2026-07-17") is False
    assert swf.is_placebo_session(cal, "2026-07-29") is False  # any class blocks placebo

    ev = swf.placebo_event("2026-07-20")
    assert ev["release_id"] == "PLACEBO-2026-07-20"
    assert ev["class"] == "placebo_1000"
    assert ev["anchor_ts"] == et_ns("2026-07-20", 10, 0, 0)

    # real arm only picks up cluster_1000 (not the fomc_stmt day).
    assert len(swf.real_events_on(cal, "2026-07-17", {"cluster_1000"})) == 1
    assert len(swf.real_events_on(cal, "2026-07-29", {"cluster_1000"})) == 0


# ======================================================================= 6. PRIOR SEPARATION


def test_real_and_placebo_prior_pools_never_cross():
    # real NVDA: 11 priors |r|=1.0 then R12 |r|=1.5 (past median 1.0 -> in_c2 TRUE).
    # placebo NVDA: 11 priors |r|=100.0 at the SAME earlier anchors. If the pools were
    # pooled by symbol only, R12 would see 22 priors (median 50.5) and FLIP to False.
    rows = []
    for i in range(1, 12):
        rows.append({"release_id": f"R{i}", "class": "cluster_1000", "symbol": "NVDA",
                     "session": "s", "anchor_ts": i * NS, "reaction": 0.01})
        rows.append({"release_id": f"P{i}", "class": "placebo_1000", "symbol": "NVDA",
                     "session": "s", "anchor_ts": i * NS, "reaction": 1.00})
    rows.append({"release_id": "R12", "class": "cluster_1000", "symbol": "NVDA",
                 "session": "s", "anchor_ts": 20 * NS, "reaction": 0.015})
    out = swf.attach_c2(pl.DataFrame(rows, schema=swf.STATE_SCHEMA))

    r12 = out.filter(pl.col("release_id") == "R12").row(0, named=True)
    assert r12["n_priors"] == 11          # ONLY real priors, not 22
    assert r12["past_median"] == pytest.approx(0.01)  # not ~0.5 -> placebo never crossed
    assert r12["in_c2"] is True

    # symmetric: a placebo event is gated against its OWN pool.
    p11 = out.filter(pl.col("release_id") == "P11").row(0, named=True)
    assert p11["class"] == "placebo_1000"
    assert p11["past_median"] == pytest.approx(1.00)


# ============================================= 7. STATE CONTINUITY / STRICT SEAL BOUNDARY


def test_seed_then_run_strict_boundary_excludes_holdout(tmp_path):
    # The seal is LITERAL (orchestrator ruling): the real pool seeds from train+validate
    # ONLY (session < HOLDOUT_START). A holdout-window event must NEVER become a prior.
    # The priors are built so that ADMITTING the holdout event would FLIP the forward
    # C2 membership — pinning that its exclusion is load-bearing, not cosmetic.
    reg = tmp_path / "reg"
    _complete_reg(reg)
    pass_p, _ = _fixtures(tmp_path)

    # 10 pre-holdout priors: five |reaction|=0.001, five |reaction|=0.010 -> median 0.0055.
    lo_days = ["2026-05-01", "2026-05-04", "2026-05-05", "2026-05-06", "2026-05-07"]
    hi_days = ["2026-05-08", "2026-05-11", "2026-05-12", "2026-05-13", "2026-05-14"]
    holdout = "2026-06-15"   # in-holdout (>= HOLDOUT_START): MUST be excluded from priors
    event = "2026-07-17"     # forward: |reaction|=0.008, between 0.0055 and 0.010

    cal = _write_cal(tmp_path, _seed_events(lo_days + hi_days) + [
        {"release_id": f"ISM-{holdout}", "cls": "cluster_1000", "session": holdout},
        {"release_id": f"ISM-{event}", "cls": "cluster_1000", "session": event},
    ])
    tapes = {("NVDA", s): _tape(s, 100.0, 100.1, 100.1) for s in lo_days}   # +0.10%
    tapes |= {("NVDA", s): _tape(s, 100.0, 101.0, 101.0) for s in hi_days}  # +1.00%
    tapes[("NVDA", holdout)] = _tape(holdout, 100.0, 101.0, 101.0)          # +1.00% outlier
    tapes[("NVDA", event)] = _tape(event, 100.0, 100.8, 102.0)             # +0.80% react, up exit
    getter = _getter(tapes)

    # PATH A: seed-then-run under the strict boundary.
    swf.run_asof(date.fromisoformat(event), calendar_path=cal,
                 ledger_path=tmp_path / "l.parquet", state_path=tmp_path / "s.parquet",
                 reg_root=reg, pass_list_path=pass_p, universe=("NVDA",), get_bbo=getter)
    state = swf.load_state(tmp_path / "s.parquet")
    led = swf.load_ledger(tmp_path / "l.parquet")
    fwd = led.filter((pl.col("session") == event) & (pl.col("horizon") == "h30")).row(0, named=True)

    # the holdout-window event NEVER entered state (seed stopped at HOLDOUT_START).
    assert state.filter(pl.col("session") == holdout).height == 0
    assert holdout not in state["session"].to_list()

    # PATH B: single-pass over the CORRECT (holdout-free) union == seed-then-run.
    measured_ok: list[dict] = []
    for s in [*lo_days, *hi_days, event]:
        measured_ok += swf.measure_events(
            [{"release_id": f"ISM-{s}", "class": "cluster_1000", "subtype": "ISM_MFG",
              "anchor_ts": et_ns(s, 10, 0, 0)}], getter, s, ("NVDA",), fail_on_missing=False)
    ok = swf.attach_c2(swf._state_rows(measured_ok))
    ref = ok.filter(pl.col("release_id") == f"ISM-{event}").row(0, named=True)

    assert fwd["n_priors"] == ref["n_priors"] == 10          # 10 pre-holdout priors, NOT 11
    assert fwd["in_c2"] == ref["in_c2"] is True              # 0.008 >= median 0.0055
    assert ref["past_median"] == pytest.approx(0.0055)

    # PIN: had the holdout event been (wrongly) admitted, the C2 membership FLIPS.
    measured_wrong = measured_ok + swf.measure_events(
        [{"release_id": f"ISM-{holdout}", "class": "cluster_1000", "subtype": "ISM_MFG",
          "anchor_ts": et_ns(holdout, 10, 0, 0)}], getter, holdout, ("NVDA",),
        fail_on_missing=False)
    wrong = swf.attach_c2(swf._state_rows(measured_wrong))
    wref = wrong.filter(pl.col("release_id") == f"ISM-{event}").row(0, named=True)
    assert wref["n_priors"] == 11
    assert wref["past_median"] == pytest.approx(0.010)       # median shifts 0.0055 -> 0.010
    assert wref["in_c2"] is False                            # 0.008 < 0.010 -> FLIP


# ======================================================================= 8. IDEMPOTENCE


def test_ledger_idempotent_same_asof(tmp_path):
    reg = tmp_path / "reg"
    cfg = _complete_reg(reg)
    pass_p, floors_p = _fixtures(tmp_path)
    event = "2026-07-17"
    cal = _write_cal(tmp_path, _seed_events(_SEED_DAYS) + [
        {"release_id": f"ISM-{event}", "cls": "cluster_1000", "session": event}])
    tapes = {("NVDA", s): _tape(s, 100.0, 100.5, 100.5) for s in _SEED_DAYS}
    tapes[("NVDA", event)] = _tape(event, 100.0, 101.0, 102.0)
    common = dict(calendar_path=cal, ledger_path=tmp_path / "l.parquet",
                  state_path=tmp_path / "s.parquet", reg_root=reg, pass_list_path=pass_p,
                  universe=("NVDA",), get_bbo=_getter(tapes))

    r1 = swf.run_asof(date.fromisoformat(event), **common)
    assert r1["ledger"]["appended"] > 0
    h1 = swf.load_ledger(tmp_path / "l.parquet").height
    tm = json.loads(pass_p.read_text())["train_means"]
    fl = json.loads(floors_p.read_text())["class_floor_bps"]
    st1 = swf.status_stats(swf.load_ledger(tmp_path / "l.parquet"), cfg, train_means=tm, floors=fl)

    r2 = swf.run_asof(date.fromisoformat(event), **common)  # re-run
    assert r2["ledger"]["appended"] == 0 and r2["ledger"]["skipped"] == h1
    assert r2["state"]["appended"] == 0
    assert swf.load_ledger(tmp_path / "l.parquet").height == h1
    st2 = swf.status_stats(swf.load_ledger(tmp_path / "l.parquet"), cfg, train_means=tm, floors=fl)
    assert st1 == st2  # identical status


# ======================================================================= 9. PIT POISON


def test_forward_pit_poison_entry_excludes_decision_instant(tmp_path):
    reg = tmp_path / "reg"
    _complete_reg(reg)
    pass_p, _ = _fixtures(tmp_path)
    event = "2026-07-17"
    cal = _write_cal(tmp_path, _seed_events(_SEED_DAYS) + [
        {"release_id": f"ISM-{event}", "cls": "cluster_1000", "session": event}])
    tapes = {("NVDA", s): _tape(s, 100.0, 100.5, 100.5) for s in _SEED_DAYS}
    tapes[("NVDA", event)] = _poison_tape(event)

    swf.run_asof(date.fromisoformat(event), calendar_path=cal,
                 ledger_path=tmp_path / "l.parquet", state_path=tmp_path / "s.parquet",
                 reg_root=reg, pass_list_path=pass_p, universe=("NVDA",), get_bbo=_getter(tapes))
    fwd = swf.load_ledger(tmp_path / "l.parquet").filter(
        (pl.col("session") == event) & (pl.col("horizon") == "h30")).row(0, named=True)

    # entry is the 10:05:24 completed bucket (101), NEVER the 200 bucket that STARTS
    # at decision (end > decision -> not complete). A future quote cannot move entry.
    assert fwd["entry_mid"] == pytest.approx(101.0)
    assert fwd["entry_mid"] != pytest.approx(200.0)
    assert fwd["in_c2"] is True  # 12 priors, |1%| >= median 0.5%
    assert fwd["status"] == "kept"


# ======================================================================= 10. SIZING


def test_sizing_report_only_exact_formula(tmp_path):
    # frozen train_pass_list values: both cells clip at 2.0 -> $20,000.
    assert swf.sizing_usd(9.2675, 4.0477) == 20000.0
    assert swf.sizing_usd(12.9287, 4.0477) == 20000.0
    # un-clipped + lower-clip cases.
    assert swf.sizing_usd(3.0, 3.0) == 10000.0
    assert swf.sizing_usd(4.5, 3.0) == 15000.0
    assert swf.sizing_usd(-1.0, 3.0) == 0.0
    assert swf.sizing_usd(1.0, None) is None

    # surfaced through status against the fixture artifacts.
    pass_p, floors_p = _fixtures(tmp_path)
    cfg = _complete_reg(tmp_path / "reg")
    tm = json.loads(pass_p.read_text())["train_means"]
    fl = json.loads(floors_p.read_text())["class_floor_bps"]
    stats = swf.status_stats(swf.load_ledger(tmp_path / "none.parquet"), cfg,
                             train_means=tm, floors=fl)
    real = [c for c in stats["cells"] if c["arm"] == "real"]
    assert {c["cell_id"] for c in real} == {"cluster_1000|C2|h30", "cluster_1000|C2|h60"}
    assert all(c["sizing_usd_REPORT_ONLY"] == 20000.0 for c in real)


# ======================================================================= 11. REFUSALS


def test_missing_bbo_refusal_message(tmp_path):
    reg = tmp_path / "reg"
    _complete_reg(reg)
    pass_p, _ = _fixtures(tmp_path)
    event = "2026-07-17"
    cal = _write_cal(tmp_path, [{"release_id": f"ISM-{event}", "cls": "cluster_1000",
                                 "session": event}])
    with pytest.raises(swf.BboMissing, match="forward_paper"):
        swf.run_asof(date.fromisoformat(event), calendar_path=cal,
                     ledger_path=tmp_path / "l.parquet", state_path=tmp_path / "s.parquet",
                     reg_root=reg, pass_list_path=pass_p, universe=("NVDA",),
                     get_bbo=_getter({}), do_seed=False)


def test_calendar_exceeded_refusal_message(tmp_path):
    reg = tmp_path / "reg"
    _complete_reg(reg)
    pass_p, _ = _fixtures(tmp_path)
    # calendar max is 2026-07-17; asof 2026-07-20 runs past it.
    cal = _write_cal(tmp_path, [{"release_id": "ISM-2026-07-17", "cls": "cluster_1000",
                                 "session": "2026-07-17"}])
    with pytest.raises(swf.CalendarExceeded, match="build_macro_calendar"):
        swf.run_asof(date(2026, 7, 20), calendar_path=cal, ledger_path=tmp_path / "l.parquet",
                     state_path=tmp_path / "s.parquet", reg_root=reg, pass_list_path=pass_p,
                     universe=("NVDA",), get_bbo=_getter({}))


def test_forward_only_guard(tmp_path):
    reg = tmp_path / "reg"
    _complete_reg(reg)
    pass_p, _ = _fixtures(tmp_path)
    cal = _write_cal(tmp_path, [{"release_id": "ISM-2026-07-17", "cls": "cluster_1000",
                                 "session": "2026-07-17"}])
    with pytest.raises(ValueError, match="forward go-live"):
        swf.run_asof(date(2026, 5, 31), calendar_path=cal, reg_root=reg,
                     pass_list_path=pass_p, get_bbo=_getter({}))


# ======================================================================= placebo warming + arms


def test_placebo_measured_through_identical_path_and_warms(tmp_path):
    reg = tmp_path / "reg"
    cfg = _complete_reg(reg)
    pass_p, floors_p = _fixtures(tmp_path)
    # calendar: seed cluster_1000 history + a future event so the placebo day is admitted.
    placebo_day = "2026-07-20"
    cal = _write_cal(tmp_path, _seed_events(_SEED_DAYS) + [
        {"release_id": "FUT", "cls": "cluster_1000", "session": "2026-07-29"}])
    tapes = {("NVDA", s): _tape(s, 100.0, 100.5, 100.5) for s in _SEED_DAYS}
    tapes[("NVDA", placebo_day)] = _tape(placebo_day, 100.0, 100.7, 101.4)

    res = swf.run_asof(date.fromisoformat(placebo_day), calendar_path=cal,
                       ledger_path=tmp_path / "l.parquet", state_path=tmp_path / "s.parquet",
                       reg_root=reg, pass_list_path=pass_p, universe=("NVDA",),
                       get_bbo=_getter(tapes))
    assert res["placebo_session"] is True
    led = swf.load_ledger(tmp_path / "l.parquet")
    placebo = led.filter(pl.col("arm") == "placebo")
    assert placebo.height > 0
    assert set(placebo["class"].unique().to_list()) == {"placebo_1000"}
    assert placebo["release_id"][0] == f"PLACEBO-{placebo_day}"
    # placebo priors start empty -> first placebo event is warming (c2_priors), not kept.
    assert placebo.filter(pl.col("status") == "kept").height == 0
    assert set(placebo["status"].unique().to_list()) == {"c2_priors"}

    tm = json.loads(pass_p.read_text())["train_means"]
    fl = json.loads(floors_p.read_text())["class_floor_bps"]
    stats = swf.status_stats(led, cfg, train_means=tm, floors=fl)
    placebo_cells = [c for c in stats["cells"] if c["arm"] == "placebo"]
    assert all(c["warming"] for c in placebo_cells)


# ======================================================================= selftest


def test_selftest_all_green():
    result = app.run_selftest()
    assert result["ok"] is True, result["checks"]
    assert all(result["checks"].values())
