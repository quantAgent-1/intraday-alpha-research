"""Tests for the M25 calendar-flow forward overlay (family ``calendar_overlay_v1``).

Synthetic fixtures ONLY -- no real data lake, no network, no canonical writes (the
family's evaluations are the orchestrator's, and every ``evaluate`` call here passes a
hermetic tmp ``out_dir``). Covers the frozen registration (M3_REGISTRATION.md section
"## M25 -- calendar-flow forward overlay"): the quad-witch date pins, the month-end
owned-session convention vs the business-day fallback, the QW-wins tie rule, the
overlay split + n>=30 eligibility, the one-evaluation-per-cell state gate, the
read-only-on-the-ledger guard, the PASS/FAIL/BETWEEN bar logic, and the CLI ``report``
running clean on an empty ledger.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
from click.testing import CliRunner

from enginev51.apps.run_calendar_overlay import main as cli_main
from enginev51.research_screens import calendar_overlay as co

# The six quad-witch sessions used across the numeric fixtures (all verified 3rd
# Fridays of Mar/Jun/Sep/Dec).
QW_SESSIONS = (
    "2024-03-15", "2024-06-21", "2024-09-20",
    "2024-12-20", "2025-03-21", "2025-06-20",
)

_LEDGER_SCHEMA = {
    "session": pl.Utf8,
    "net_bps": pl.Float64,
    "taken_classical": pl.Boolean,
}


# --------------------------------------------------------------------------- builders


def _ledger(rows: list[dict]) -> pl.DataFrame:
    """Minimal forward ledger (only the columns the overlay reads)."""
    if not rows:
        return pl.DataFrame(schema=_LEDGER_SCHEMA)
    return pl.DataFrame(rows, schema=_LEDGER_SCHEMA, orient="row")


def _ordinary_block(value: float = 0.0) -> list[dict]:
    """Nine ORDINARY events (three each on three mid-Feb-2023 sessions) plus one
    later MONTH_END sink (2023-02-27), so the Feb-06/07/08 sessions are genuinely
    ORDINARY (a later owned session exists in their month) and QW eval has a
    comparator. The sink row is MONTH_END and is ignored by a QUAD_WITCH eval."""
    rows: list[dict] = []
    for s in ("2023-02-06", "2023-02-07", "2023-02-08"):
        rows += [{"session": s, "net_bps": value, "taken_classical": True} for _ in range(3)]
    rows.append({"session": "2023-02-27", "net_bps": value, "taken_classical": True})
    return rows


def _qw_ledger(per_session: dict[str, list[float]], ord_value: float = 0.0) -> pl.DataFrame:
    """A ledger with the given QW net_bps values plus the standard ordinary block."""
    rows: list[dict] = []
    for session, vals in per_session.items():
        rows += [{"session": session, "net_bps": v, "taken_classical": True} for v in vals]
    rows += _ordinary_block(ord_value)
    return _ledger(rows)


# --------------------------------------------------------------------------- flags


def test_quad_witch_date_pins():
    # registration pins: 3rd Friday of Mar/Jun/Sep/Dec
    assert co.flag_of("2024-03-15") == "QUAD_WITCH"
    assert co.flag_of("2025-06-20") == "QUAD_WITCH"
    # 2024-03-08 is the SECOND Friday -> not quad-witch
    assert co.flag_of("2024-03-08") == "ORDINARY"
    # a 3rd Friday of a NON-quad-witch month (Jan) is not quad-witch
    assert co.flag_of("2024-01-19") == "ORDINARY"


def test_month_end_owned_session_convention_vs_business_fallback():
    # June is RESOLVED because a later-month (July) session is owned, so its last
    # owned session (06-27) flags MONTH_END; the July session itself is PENDING.
    owned = ["2024-06-25", "2024-06-26", "2024-06-27", "2024-07-01"]
    assert co.flag_of("2024-06-27", owned) == "MONTH_END"
    assert co.flag_of("2024-06-30", owned) == "ORDINARY"  # not the last owned June session
    assert co.flag_of("2024-07-01", owned) == "PENDING"   # latest owned month, unresolved
    # business-day fallback (owned_sessions=None) differs and NEVER pends: the last
    # WEEKDAY of June 2024 is Fri 06-28 (06-30 is a Sunday), so 06-27 is not the
    # fallback month-end.
    assert co.flag_of("2024-06-28", None) == "MONTH_END"
    assert co.flag_of("2024-06-27", None) == "ORDINARY"


def test_tie_rule_quad_witch_wins_over_month_end():
    # 2024-09-20 is BOTH the 3rd Friday of September AND the last owned Sept session;
    # the registration tie rule makes it QUAD_WITCH.
    owned = ["2024-09-18", "2024-09-19", "2024-09-20"]
    assert co.month_end_session_set(owned) == {"2024-09-20"}
    assert co.flag_of("2024-09-20", owned) == "QUAD_WITCH"


def test_overlay_month_end_uses_ledger_owned_sessions():
    # June is resolved by a later-month (July) session: 06-27 is MONTH_END, 06-25 is
    # ORDINARY, and the July session is PENDING (flags computed against the ledger's
    # distinct sessions).
    led = _ledger([
        {"session": "2024-06-25", "net_bps": 1.0, "taken_classical": True},
        {"session": "2024-06-27", "net_bps": 2.0, "taken_classical": True},
        {"session": "2024-07-05", "net_bps": 3.0, "taken_classical": True},
    ])
    rep = co.overlay_report(led)
    assert rep["by_flag"]["MONTH_END"]["n"] == 1
    assert rep["by_flag"]["ORDINARY"]["n"] == 1
    assert rep["by_flag"]["QUAD_WITCH"]["n"] == 0
    assert rep["n_pending"] == 1 and rep["pending_sessions"] == 1


# --------------------------------------------------------------------------- report


def test_overlay_report_split_and_eligibility_29_vs_30():
    # 29 QW events -> not eligible; 30 -> eligible (untaken rows are excluded).
    five = [1.0] * 5
    four = [1.0] * 4
    led29 = _qw_ledger({s: (five if i else four) for i, s in enumerate(QW_SESSIONS)})
    led29 = pl.concat([
        led29,
        _ledger([{"session": "2024-03-15", "net_bps": 99.0, "taken_classical": False}]),
    ])
    rep29 = co.overlay_report(led29)
    assert rep29["by_flag"]["QUAD_WITCH"]["n"] == 29  # the untaken row is excluded
    assert rep29["eligible_for_evaluation"]["QUAD_WITCH"] is False

    led30 = _qw_ledger({s: five for s in QW_SESSIONS})
    rep30 = co.overlay_report(led30)
    assert rep30["by_flag"]["QUAD_WITCH"]["n"] == 30
    assert rep30["by_flag"]["QUAD_WITCH"]["sessions"] == 6
    assert rep30["eligible_for_evaluation"]["QUAD_WITCH"] is True
    assert rep30["eligible_for_evaluation"]["MONTH_END"] is False


# --------------------------------------------------------------------------- evaluate gate


def test_evaluate_refuses_below_floor_and_second_evaluation(tmp_path):
    # below the n>=30 floor -> refuse, and no state file is written.
    small = _qw_ledger({s: [10.0] * 4 for s in QW_SESSIONS})  # 24 QW events
    with pytest.raises(RuntimeError, match="not eligible"):
        co.evaluate(small, "QUAD_WITCH", out_dir=tmp_path)
    assert not co.eval_state_path("QUAD_WITCH", tmp_path).exists()

    # unknown cell -> ValueError
    with pytest.raises(ValueError, match="unknown M25 cell"):
        co.evaluate(small, "NONSENSE", out_dir=tmp_path)

    # eligible -> evaluates once and writes state; a second call is refused.
    ok = _qw_ledger({s: [10.0] * 5 for s in QW_SESSIONS})  # 30 QW events
    res = co.evaluate(ok, "QUAD_WITCH", out_dir=tmp_path)
    assert res["verdict"] == "PASS"
    assert co.eval_state_path("QUAD_WITCH", tmp_path).exists()
    with pytest.raises(RuntimeError, match="already evaluated"):
        co.evaluate(ok, "QUAD_WITCH", out_dir=tmp_path)


# --------------------------------------------------------------------------- bar logic


def test_bar_logic_pass_fail_between(tmp_path):
    # PASS: flagged mean (+10) > ordinary (0) AND gap CI-lo > 0.
    passing = _qw_ledger({s: [10.0] * 5 for s in QW_SESSIONS}, ord_value=0.0)
    r_pass = co.evaluate(passing, "QUAD_WITCH", out_dir=tmp_path / "pass")
    assert r_pass["verdict"] == "PASS"
    assert r_pass["gap_ci_lo"] > 0 and r_pass["flagged_gt_ordinary"] is True

    # FAIL: flagged mean (-10) clearly below ordinary; gap CI-hi < 0.
    failing = _qw_ledger({s: [-10.0] * 5 for s in QW_SESSIONS}, ord_value=0.0)
    r_fail = co.evaluate(failing, "QUAD_WITCH", out_dir=tmp_path / "fail")
    assert r_fail["verdict"] == "FAIL"
    assert r_fail["gap_ci_hi"] < 0

    # BETWEEN: three QW sessions at +20, three at -18 -> flagged mean +1 (> ordinary)
    # but the day-clustered gap CI straddles 0.
    split = {s: ([20.0] * 5 if i < 3 else [-18.0] * 5) for i, s in enumerate(QW_SESSIONS)}
    mixed = _qw_ledger(split, ord_value=0.0)
    r_btw = co.evaluate(mixed, "QUAD_WITCH", out_dir=tmp_path / "between")
    assert r_btw["verdict"] == "BETWEEN"
    assert r_btw["gap_ci_lo"] < 0 < r_btw["gap_ci_hi"]


# --------------------------------------------------------------------------- pending month


def test_partial_latest_month_sessions_are_pending():
    # (a) the latest owned month (2024-02) is unresolved -> its non-QW sessions are
    # PENDING, not MONTH_END/ORDINARY. The prior month (2024-01) is resolved.
    led = _ledger([
        {"session": "2024-01-10", "net_bps": 1.0, "taken_classical": True},  # ORDINARY
        {"session": "2024-01-31", "net_bps": 1.0, "taken_classical": True},  # MONTH_END
        {"session": "2024-02-05", "net_bps": 1.0, "taken_classical": True},  # PENDING
        {"session": "2024-02-06", "net_bps": 1.0, "taken_classical": True},  # PENDING
    ])
    rep = co.overlay_report(led)
    assert rep["by_flag"]["MONTH_END"]["n"] == 1
    assert rep["by_flag"]["ORDINARY"]["n"] == 1
    assert rep["n_pending"] == 2
    assert rep["pending_sessions"] == 2


def test_pending_resolves_when_later_month_appended():
    # (b) June-only ledger: all three June sessions PEND (latest owned month).
    partial = _ledger([
        {"session": "2024-06-25", "net_bps": 1.0, "taken_classical": True},
        {"session": "2024-06-26", "net_bps": 1.0, "taken_classical": True},
        {"session": "2024-06-27", "net_bps": 1.0, "taken_classical": True},
    ])
    rep0 = co.overlay_report(partial)
    assert rep0["n_pending"] == 3
    assert rep0["by_flag"]["MONTH_END"]["n"] == 0
    assert rep0["by_flag"]["ORDINARY"]["n"] == 0

    # append a later-month session -> June resolves: 06-27 MONTH_END, the rest
    # ORDINARY; only the new July session now pends.
    resolved = pl.concat([
        partial,
        _ledger([{"session": "2024-07-05", "net_bps": 1.0, "taken_classical": True}]),
    ])
    rep1 = co.overlay_report(resolved)
    assert rep1["by_flag"]["MONTH_END"]["n"] == 1
    assert rep1["by_flag"]["ORDINARY"]["n"] == 2
    assert rep1["n_pending"] == 1


def test_current_month_quad_witch_still_flags_qw():
    # (c) the latest owned month (2024-09) is unresolved, but its 3rd-Friday
    # quad-witch date still flags QUAD_WITCH immediately; its other sessions pend.
    led = _ledger([
        {"session": "2024-09-18", "net_bps": 1.0, "taken_classical": True},  # PENDING
        {"session": "2024-09-19", "net_bps": 1.0, "taken_classical": True},  # PENDING
        {"session": "2024-09-20", "net_bps": 1.0, "taken_classical": True},  # QUAD_WITCH
    ])
    rep = co.overlay_report(led)
    assert rep["by_flag"]["QUAD_WITCH"]["n"] == 1
    assert rep["n_pending"] == 2
    assert rep["by_flag"]["MONTH_END"]["n"] == 0
    assert rep["by_flag"]["ORDINARY"]["n"] == 0


def test_evaluate_eligibility_excludes_pending(tmp_path):
    # (d) 25 resolved MONTH_END events + 10 pending-month events. Were pending
    # counted, MONTH_END would reach 35 >= 30; excluding them keeps it at 25, so the
    # cell is NOT eligible and evaluate refuses at the floor.
    rows: list[dict] = []
    for m in range(1, 6):  # 2024-01..2024-05 are resolved (2024-06 is later)
        rows.append({"session": f"2024-0{m}-05", "net_bps": 0.0, "taken_classical": True})
        rows += [
            {"session": f"2024-0{m}-26", "net_bps": 5.0, "taken_classical": True}
            for _ in range(5)  # 5 events on each month's last owned session
        ]
    rows += [
        {"session": "2024-06-10", "net_bps": 5.0, "taken_classical": True}
        for _ in range(10)  # latest owned month -> PENDING
    ]
    led = _ledger(rows)
    rep = co.overlay_report(led)
    assert rep["by_flag"]["MONTH_END"]["n"] == 25
    assert rep["n_pending"] == 10
    assert rep["eligible_for_evaluation"]["MONTH_END"] is False
    with pytest.raises(RuntimeError, match="not eligible"):
        co.evaluate(led, "MONTH_END", out_dir=tmp_path)


# --------------------------------------------------------------------------- read-only guard


def test_screen_is_read_only_on_the_ledger():
    src = Path(co.__file__).read_text(encoding="utf-8")
    # imports load_ledger (read-only) but never append_ledger, and never writes the
    # forward ledger parquet from this module.
    assert "load_ledger" in src
    assert "append_ledger" not in src
    assert "write_parquet" not in src


# --------------------------------------------------------------------------- CLI


def test_cli_report_exits_0_on_empty_ledger(tmp_path):
    runner = CliRunner()
    missing = tmp_path / "no_such_ledger.parquet"  # load_ledger -> empty schema frame
    result = runner.invoke(cli_main, ["report", "--ledger", str(missing)])
    assert result.exit_code == 0, result.output
    assert "M25 calendar-flow overlay" in result.output
