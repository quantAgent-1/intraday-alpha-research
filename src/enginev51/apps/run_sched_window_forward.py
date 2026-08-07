"""M20-FORWARD revival-screen runner (SPENT family ``sched_window_v1``).

Gated daily collector for the forward revival of the two frozen M20 cells
(``cluster_1000|C2|h30/h60``) plus a placebo control arm. It is INERT until the
orchestrator writes a registered config after the DR-X9 wave verdict — every
lake/ledger path calls ``load_registration`` first and refuses otherwise.

    uv run python -m enginev51.apps.run_sched_window_forward run --asof 2026-07-17
    uv run python -m enginev51.apps.run_sched_window_forward status [--json]
    uv run python -m enginev51.apps.run_sched_window_forward selftest

``run`` measures the asof session's real + placebo events through the FROZEN M20
mechanics (lake read-only — it NEVER downloads; run the daily forward_paper
collector first) and appends to the forward ledger/state. ``status`` prints the
running C2-gated tally, gate progress, and the placebo comparison. ``selftest`` is
the ONLY pre-registration invocation: it exercises the whole pipeline on synthetic
fixtures in a temp dir (no lake, no real writes).

Console note: on Windows set ``PYTHONIOENCODING=utf-8``.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import date
from pathlib import Path

import click
import polars as pl

from enginev51.data.bbo1s import BBO_SCHEMA
from enginev51.data.noii import et_ns
from enginev51.research_screens import sched_window_forward as swf

NS = 1_000_000_000


# --------------------------------------------------------------------------- cli


@click.group()
def main() -> None:
    """M20-FORWARD revival screen (sched_window_v1) — gated on the DR-X9 verdict."""
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety


@main.command("run")
@click.option("--asof", required=True, help="Settled forward session (ISO date), >= 2026-07-17.")
@click.option("--calendar", default=swf.DEFAULT_CALENDAR, help="Macro-anchor calendar parquet.")
@click.option("--bbo-dir", default=None, help="bbo-1s lake root (default data/raw/bbo1s).")
def run_cmd(asof: str, calendar: str, bbo_dir: str | None) -> None:
    try:
        summary = swf.run_asof(
            date.fromisoformat(asof), calendar_path=calendar, bbo_dir=bbo_dir
        )
    except swf.RegistrationMissing as exc:
        raise click.ClickException(str(exc)) from exc
    except (swf.BboMissing, swf.CalendarExceeded, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(summary, indent=2, default=str))
    click.echo("")
    _echo_status(bbo_only=False)


@main.command("status")
@click.option("--json", "as_json", is_flag=True, help="Emit the stats dict as JSON.")
def status_cmd(as_json: bool) -> None:
    try:
        _echo_status(bbo_only=False, as_json=as_json)
    except swf.RegistrationMissing as exc:
        raise click.ClickException(str(exc)) from exc


def _echo_status(*, bbo_only: bool, as_json: bool = False) -> None:
    reg = swf.load_registration()  # GATE: refuses unless activated
    stats = swf.status_stats(
        swf.load_ledger(),
        reg,
        train_means=swf.load_train_means(),
        floors=swf.load_class_floors(),
    )
    if as_json:
        click.echo(json.dumps(stats, indent=2, default=str))
    else:
        click.echo(swf.format_status(stats))


@main.command("selftest")
@click.option("--json", "as_json", is_flag=True, help="Emit the check results as JSON.")
def selftest_cmd(as_json: bool) -> None:
    result = run_selftest()
    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        for name, ok in result["checks"].items():
            click.echo(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        click.echo("")
        click.echo(f"SELFTEST {'PASS' if result['ok'] else 'FAIL'} "
                   f"({sum(result['checks'].values())}/{len(result['checks'])} checks)")
    if not result["ok"]:
        raise SystemExit(1)


# --------------------------------------------------------------------------- selftest


def _mid_q(mid: float, half: float = 0.01) -> tuple[float, float]:
    return mid - half, mid + half


def _tape(session: str, anchor_mid: float, react_mid: float, exit_mid: float) -> pl.DataFrame:
    """A dense 1s RTH-morning tape (+ a 15:00 marker so it is NOT an early close).

    anchor(10:00)=anchor_mid, react(10:05)+entry(10:05:25)=react_mid, exits=exit_mid.
    """
    rows: list[dict] = []
    t = et_ns(session, 9, 59, 0)
    end = et_ns(session, 11, 10, 0)
    while t <= end:
        if t <= et_ns(session, 10, 4, 58):
            mid = anchor_mid
        elif t <= et_ns(session, 10, 20, 0):
            mid = react_mid
        else:
            mid = exit_mid
        b, a = _mid_q(mid)
        rows.append({"ts": t, "bid": b, "ask": a, "bid_size": 100.0, "ask_size": 100.0})
        t += NS
    b, a = _mid_q(exit_mid)
    rows.append({"ts": et_ns(session, 15, 0, 0), "bid": b, "ask": a,
                 "bid_size": 100.0, "ask_size": 100.0})
    return pl.DataFrame(rows, schema=BBO_SCHEMA, orient="row").sort("ts")


def _syn_calendar(seed_days: list[str], event_days: list[str], future_day: str) -> pl.DataFrame:
    """cluster_1000 events on seed + event + future days; no rows elsewhere (gaps
    become placebo). ``future_day`` sits past the placebo target so the calendar
    bound admits it."""
    rows: list[dict] = [
        {
            "release_id": f"ISM-{s}",
            "class": "cluster_1000",
            "subtype": "ISM_MFG",
            "session_date": s,
            "sched_ts_et": f"{s}T10:00:00",
            "anchor_ts_et": f"{s}T10:00:00",
            "source": "selftest",
        }
        for s in [*seed_days, *event_days, future_day]
    ]
    cal = pl.DataFrame(rows).with_columns(
        pl.col("session_date").str.to_datetime(),
        pl.col("sched_ts_et").str.to_datetime(time_zone="America/New_York"),
        pl.col("anchor_ts_et").str.to_datetime(time_zone="America/New_York"),
    )
    return cal


def run_selftest() -> dict:
    """Exercise the whole gated pipeline on synthetic fixtures in a temp dir.

    No real lake, no real ledger/state, no writes outside the temp dir. Proves the
    activation gate (all four cases), placebo-day selection, seed-then-run C2
    continuity, ledger idempotence, and status formatting.
    """
    checks: dict[str, bool] = {}
    tmp = Path(tempfile.mkdtemp(prefix="m20f_selftest_"))
    try:
        reg_root = tmp / "reg"
        reg_root.mkdir(parents=True, exist_ok=True)
        reg_json = reg_root / "registration.json"
        ledger_p = tmp / "ledger.parquet"
        state_p = tmp / "state.parquet"
        cal_p = tmp / "cal.parquet"
        pass_p = tmp / "train_pass_list.json"
        floors_p = tmp / "cost_floors.json"

        # --- gate: refusal without file --------------------------------------
        checks["gate_refuses_missing"] = _raises_missing(reg_root)

        # --- gate: refusal with registered:false -----------------------------
        reg_json.write_text(json.dumps(_template_cfg()), encoding="utf-8")
        checks["gate_refuses_unregistered"] = _raises_missing(reg_root)

        # --- gate: refusal with null gate numbers ----------------------------
        half = _template_cfg()
        half.update(registered=True, trial_id="M20F-DRX9-selftest", family="sched_window_fwd_v1")
        reg_json.write_text(json.dumps(half), encoding="utf-8")
        checks["gate_refuses_null_gate"] = _raises_missing(reg_root)

        # --- gate: acceptance with a complete config -------------------------
        cfg = _complete_cfg()
        reg_json.write_text(json.dumps(cfg), encoding="utf-8")
        try:
            loaded = swf.load_registration(reg_root)
            checks["gate_accepts_complete"] = loaded["registered"] is True
        except swf.RegistrationMissing:
            checks["gate_accepts_complete"] = False

        # --- frozen artifacts (fixture copies) -------------------------------
        pass_p.write_text(json.dumps({
            "cells": ["cluster_1000|C2|h30", "cluster_1000|C2|h60"],
            "train_means": {"cluster_1000|C2|h30": 9.2675, "cluster_1000|C2|h60": 12.9287},
        }), encoding="utf-8")
        floors_p.write_text(json.dumps({"class_floor_bps": {"cluster_1000": 4.0477}}),
                            encoding="utf-8")

        # --- synthetic calendar + bbo (single name) --------------------------
        universe = ("NVDA",)
        # pre-holdout (< 2026-06-01) so the STRICT seed boundary (SEED_END = HOLDOUT_START)
        # admits these priors; the holdout window feeds nothing.
        seed_days = [f"2026-05-{d:02d}" for d in (1, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 18)]
        event_day = "2026-07-17"
        placebo_day = "2026-07-20"
        future_day = "2026-07-29"
        cal = _syn_calendar(seed_days, [event_day], future_day)
        cal.write_parquet(cal_p)

        tapes: dict[tuple[str, str], pl.DataFrame] = {}
        for s in seed_days:
            tapes[("NVDA", s)] = _tape(s, 100.0, 100.5, 100.5)  # +0.5% prior reactions
        tapes[("NVDA", event_day)] = _tape(event_day, 100.0, 101.0, 102.0)  # +1% react, up exit
        tapes[("NVDA", placebo_day)] = _tape(placebo_day, 100.0, 100.7, 101.4)

        def getter(sym: str, session: str) -> pl.DataFrame | None:
            return tapes.get((sym, session))

        common = dict(
            calendar_path=cal_p, ledger_path=ledger_p, state_path=state_p,
            reg_root=reg_root, pass_list_path=pass_p, universe=universe, get_bbo=getter,
        )

        # --- run the forward EVENT day (seeds first) -------------------------
        r1 = swf.run_asof(date.fromisoformat(event_day), **common)
        led1 = swf.load_ledger(ledger_p)
        real_kept = led1.filter((pl.col("arm") == "real") & (pl.col("status") == "kept"))
        checks["seed_then_run_c2_kept"] = real_kept.height > 0
        checks["event_day_not_placebo"] = r1["placebo_session"] is False

        # --- run the PLACEBO day ---------------------------------------------
        r2 = swf.run_asof(date.fromisoformat(placebo_day), **common)
        led2 = swf.load_ledger(ledger_p)
        checks["placebo_day_selected"] = r2["placebo_session"] is True
        checks["placebo_rows_present"] = (
            led2.filter(pl.col("arm") == "placebo").height > 0
        )

        # --- idempotent re-run ------------------------------------------------
        before = swf.load_ledger(ledger_p).height
        r3 = swf.run_asof(date.fromisoformat(event_day), **common)
        checks["idempotent_rerun"] = (
            r3["ledger"]["appended"] == 0 and swf.load_ledger(ledger_p).height == before
        )

        # --- calendar-exceeded guard -----------------------------------------
        try:
            swf.run_asof(date.fromisoformat("2026-07-30"), **common)
            checks["calendar_exceeded_guard"] = False
        except swf.CalendarExceeded:
            checks["calendar_exceeded_guard"] = True

        # --- status formats ---------------------------------------------------
        stats = swf.status_stats(
            swf.load_ledger(ledger_p), cfg,
            train_means=json.loads(pass_p.read_text())["train_means"],
            floors=json.loads(floors_p.read_text())["class_floor_bps"],
        )
        text = swf.format_status(stats)
        checks["status_formats"] = "M20-FORWARD" in text and "placebo comparison" in text
        checks["sizing_report_only"] = any(
            c.get("sizing_usd_REPORT_ONLY") == 20000.0
            for c in stats["cells"] if c["arm"] == "real"
        )

        return {"ok": all(checks.values()), "checks": checks, "tmp": str(tmp)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _raises_missing(reg_root: Path) -> bool:
    try:
        swf.load_registration(reg_root)
        return False
    except swf.RegistrationMissing:
        return True


def _template_cfg() -> dict:
    return {
        "registered": False,
        "trial_id": None,
        "family": None,
        "cells": ["cluster_1000|C2|h30", "cluster_1000|C2|h60"],
        "gate": {"min_sessions": None, "min_events": None,
                 "rule": "TO BE FROZEN AT REGISTRATION AFTER DR-X9"},
        "placebo_kill": {"rule": "TO BE FROZEN AT REGISTRATION"},
        "sizing_form": "clip(E_train/floor, 0, 2) * 10000 USD -- report-only",
    }


def _complete_cfg() -> dict:
    cfg = _template_cfg()
    cfg.update(
        registered=True,
        trial_id="M20F-DRX9-selftest",
        family="sched_window_fwd_v1",
        gate={"min_sessions": 40, "min_events": 150, "rule": "frozen-at-registration"},
    )
    return cfg


if __name__ == "__main__":
    main()
