"""M18 reversion_system_v1 CLI (harness only — no economics interpretation).

Usage:
    uv run python -m enginev51.apps.run_reversion_system --validate-anchor
    uv run python -m enginev51.apps.run_reversion_system --cell MU:30m
    uv run python -m enginev51.apps.run_reversion_system --all

Cells: NAME:HOLD with NAME in {NVDA,TSLA,AMD,MU}, HOLD in {30m,2h,4h}. The
system-under-test uses maker-first entry; the anchor uses taker bare-rule.
Windows: MU 2024-01-02..2026-05-31; NVDA/TSLA/AMD 2025-09-02..2026-05-31.
"""

from __future__ import annotations

import click
import structlog

from enginev51.reversion.runner import (
    CELL_START,
    DEV_END,
    HOLD_BARS,
    POOL_UNIVERSE,
    run_all_cells,
    run_anchor,
    run_cell,
)

log = structlog.get_logger(__name__)

UNIVERSE = POOL_UNIVERSE


def _log_cell(s: dict) -> None:
    log.info("cell_done", cell=f"{s['symbol']}:{s['hold']}", n_triggers=s["n_triggers"],
             n_opened=s.get("n_opened", 0), n_posted=s.get("n_posted", 0),
             maker_fill_rate=round(s.get("maker_fill_rate", 0.0), 3),
             meta_trained=s.get("meta_trained", False))


def _run_one_cell(spec: str) -> None:
    sym, _, hold = spec.partition(":")
    sym = sym.upper()
    if sym not in CELL_START or hold not in HOLD_BARS:
        raise click.BadParameter(f"bad cell {spec!r}; NAME in {UNIVERSE}, HOLD in {sorted(HOLD_BARS)}")
    res = run_cell(sym, hold, entry_model="maker", start=CELL_START[sym], end=DEV_END)
    _log_cell(res.summary)


@click.command()
@click.option("--cell", "cell", default=None, help="NAME:HOLD, e.g. MU:30m")
@click.option("--all", "run_all", is_flag=True, help="Run all 12 cells (4 names × 3 holds)")
@click.option("--validate-anchor", "validate_anchor", is_flag=True, help="Run the §7 harness anchor")
def main(cell: str | None, run_all: bool, validate_anchor: bool) -> None:
    if validate_anchor:
        res = run_anchor()
        click.echo("HARNESS VALIDATION ANCHOR (TSLA, taker bare-rule, 2025-09-02..2026-03-01, REALISTIC)")
        click.echo(f"{'metric':<22} {'band':<16} {'observed':>12}  pass")
        for row in res.table:
            obs = row["observed"]
            obs_s = f"{obs:.4g}" if isinstance(obs, float) else str(obs)
            click.echo(f"{row['metric']:<22} {row['band']:<16} {obs_s:>12}  {'PASS' if row['pass'] else 'FAIL'}")
        click.echo(f"\nANCHOR: {'PASS' if res.passed else 'FAIL'}")
        return
    if run_all:
        # One pooled walk-forward per hold ceiling (shared across the 4 names),
        # writing all 12 cells; cells are still emitted one at a time.
        for res in run_all_cells():
            _log_cell(res.summary)
        return
    if cell:
        _run_one_cell(cell)
        return
    raise click.UsageError("pass one of --validate-anchor / --cell NAME:HOLD / --all")


if __name__ == "__main__":
    main()
