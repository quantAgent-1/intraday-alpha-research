"""M25 calendar-flow forward-overlay CLI (family ``calendar_overlay_v1``).

Registered 2026-07-23 (M3_REGISTRATION.md, section "## M25 -- calendar-flow forward
overlay"), FORWARD-JUDGED ONLY. Two sub-commands over the M10 forward ledger:

* ``report`` -- split the taken_classical stream by calendar flag (QUAD_WITCH /
  MONTH_END / ORDINARY), print per-flag n / sessions / mean net_bps / day-clustered
  CI and the per-cell eligibility (n_flagged >= 30). Read-only and SAFE any time.
* ``evaluate --cell {MONTH_END,QUAD_WITCH} --confirm`` -- the family's SINGLE
  registered, state-gated evaluation of one frozen cell (refuses below the n >= 30
  floor and refuses a second evaluation via the per-cell state file). The one
  evaluation is the ORCHESTRATOR's; there is NO trading consequence in code.

The evaluation state directory is NOT caller-relocatable (no --out-dir option): the
one-evaluation-per-cell gate is anchored to the canonical experiments dir so a fresh
path can never sidestep it. Console note: on Windows set PYTHONIOENCODING=utf-8 (no
non-ascii is printed).

    uv run python -m enginev51.apps.run_calendar_overlay report
    uv run python -m enginev51.apps.run_calendar_overlay evaluate --cell MONTH_END --confirm
"""

from __future__ import annotations

import json
import subprocess

import click
import polars as pl

from enginev51.apps.forward_paper import LEDGER_PATH, load_ledger
from enginev51.config import PROJECT_ROOT
from enginev51.research_screens import calendar_overlay as co


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def _fmt_cell(name: str, c: dict) -> str:
    if not c["n"]:
        return f"  {name:<12} n=0 (no events yet)"
    return (
        f"  {name:<12} mean={c['mean_net_bps']:+.3f}  "
        f"95%CI=[{c['ci_lo']:+.3f}, {c['ci_hi']:+.3f}]  "
        f"n={c['n']}  sessions={c['sessions']}"
    )


def format_report(rep: dict) -> str:
    lines = [
        f"M25 calendar-flow overlay -- {rep['family']} (forward-only; display/report-only)",
        "",
        f"sessions collected: {rep['n_sessions_total']}   taken_classical: "
        f"{rep['n_taken_classical']}"
        + (f"   span {rep['asof_span'][0]}..{rep['asof_span'][1]}" if rep["asof_span"] else ""),
        "",
        "per-flag split of the classical stream (net_bps, day-clustered CI):",
        _fmt_cell("QUAD_WITCH", rep["by_flag"]["QUAD_WITCH"]),
        _fmt_cell("MONTH_END", rep["by_flag"]["MONTH_END"]),
        _fmt_cell("ORDINARY", rep["by_flag"]["ORDINARY"]),
        f"  {'PENDING (month unresolved)':<26} "
        f"n={rep['n_pending']}  sessions={rep['pending_sessions']}",
        "",
        f"eligibility (n_flagged >= {rep['min_flagged']} -> one evaluation unlocked):",
    ]
    for cell, ok in rep["eligible_for_evaluation"].items():
        n = rep["by_flag"][cell]["n"]
        lines.append(f"  {cell:<12} eligible={ok}  (n_flagged={n})")
    return "\n".join(lines)


@click.group()
def main() -> None:
    """M25 calendar-flow forward overlay (calendar_overlay_v1)."""
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety


@main.command("report")
@click.option("--ledger", "ledger_path", default=str(LEDGER_PATH),
              help="Forward ledger parquet (M10 clock).")
@click.option("--json", "as_json", is_flag=True, help="Emit the report dict as JSON.")
def report_cmd(ledger_path: str, as_json: bool) -> None:
    """Per-flag split + eligibility (read-only; safe any time)."""
    ledger = load_ledger(ledger_path)
    rep = co.overlay_report(ledger)
    if as_json:
        click.echo(json.dumps(rep, indent=2, default=str))
    else:
        click.echo(format_report(rep))


@main.command("evaluate")
@click.option("--cell", required=True, type=click.Choice(list(co.CELLS)),
              help="The frozen cell to evaluate (one evaluation per cell).")
@click.option("--ledger", "ledger_path", default=str(LEDGER_PATH),
              help="Forward ledger parquet (M10 clock).")
@click.option("--confirm", is_flag=True, default=False,
              help="Required: spend the ONE registered evaluation for this cell.")
def evaluate_cmd(cell: str, ledger_path: str, confirm: bool) -> None:
    """The SINGLE registered, state-gated evaluation of one cell (canonical state)."""
    if not confirm:
        click.echo(
            "refusing: evaluate spends the ONE registered evaluation for this cell. "
            "Re-run with --confirm once the report shows eligible=True."
        )
        return
    # The one-evaluation gate is anchored to the canonical dir (no --out-dir); the
    # state directory is unrelocatable in production.
    ledger = load_ledger(ledger_path)
    result = co.evaluate(ledger, cell)
    result["_git_sha"] = _git_sha()
    click.echo(json.dumps(result, indent=2, default=str))
    click.echo("")
    click.echo(f"cell {cell}: verdict={result['verdict']}  (evaluation SPENT; state written)")


if __name__ == "__main__":
    main()
