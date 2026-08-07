"""`backfill` CLI: plan and run raw-lake downloads.

    python -m enginev51.apps.backfill ticks --symbols NVDA,TSLA,AMD,MU \
        --start 2025-09-02 --end 2025-09-05 [--dry-run]
    python -m enginev51.apps.backfill letf-bars [--dry-run]
    python -m enginev51.apps.backfill status

Dry-run prints the work plan (counts per symbol/kind + first/last day) without
touching the network; live mode fetches and writes to the primary lake only.

Healing a bad primary day (code review 2026-07-28 B4): plain `--force` still
skips anything the PRIMARY lake holds, so a truncated/empty/corrupt partition
is otherwise permanent. Use

    ... ticks --symbols NVDA --start D --end D --force-overwrite

to rewrite it, or `--require-complete` to make planning judge CONTENT (rows
through the session close) rather than file presence. Both are opt-in — the
default plan/run path is unchanged and never re-verdicts the existing lake.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import click

from enginev51.config import get_settings
from enginev51.data import backfill


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def _summarize_ticks(work: list[backfill.WorkItem]) -> dict[tuple[str, str], dict]:
    """Group work items into per (symbol, kind): count, first day, last day."""
    agg: dict[tuple[str, str], list[str]] = {}
    for sym, day, kind in work:
        agg.setdefault((sym, kind), []).append(day)
    out: dict[tuple[str, str], dict] = {}
    for key, days in sorted(agg.items()):
        days.sort()
        out[key] = {"count": len(days), "first": days[0], "last": days[-1]}
    return out


@click.group()
def backfill_cli() -> None:
    """Raw-lake backfill commands."""


@backfill_cli.command("ticks")
@click.option("--symbols", required=True, help="Comma-separated symbols, e.g. NVDA,TSLA,AMD,MU")
@click.option("--start", required=True, help="First session date YYYY-MM-DD")
@click.option("--end", default=None, help="Last session date YYYY-MM-DD (default: yesterday UTC)")
@click.option("--force", is_flag=True, help="Re-download even if a legacy-root partition exists (condition-code refresh); primary-lake copies still skip.")
@click.option("--force-overwrite", is_flag=True, help="HEAL: refetch every session in range and REWRITE the primary partition, whatever is on disk (the only way to replace a truncated/corrupt primary day).")
@click.option("--require-complete", is_flag=True, help="Judge coverage by CONTENT (rows through the session close; zero rows only with an .empty_ok sidecar) instead of file presence.")
@click.option("--mark-empty-ok", is_flag=True, help="Declare zero-row results of THIS run intentional (writes the .empty_ok sidecar) — for genuinely unlisted names.")
@click.option("--dry-run", is_flag=True, help="Print the plan; do not fetch.")
@click.option("--rth-only/--extended", default=True, help="RTH session bounds (default) vs 04:00-20:00 ET.")
def ticks(
    symbols: str, start: str, end: str | None, force, force_overwrite: bool,
    require_complete: bool, mark_empty_ok: bool, dry_run: bool, rth_only: bool,
) -> None:
    settings = get_settings()
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    start_d = _parse_date(start)
    end_d = _parse_date(end) if end else (datetime.now(UTC).date() - timedelta(days=1))

    work = backfill.plan_ticks(
        settings, syms, start_d, end_d, force=force,
        force_overwrite=force_overwrite, require_complete=require_complete,
    )
    summary = _summarize_ticks(work)

    click.echo(f"tick plan  symbols={','.join(syms)}  range={start_d}..{end_d}")
    click.echo(f"total missing partitions: {len(work)}")
    click.echo(f"{'symbol':<8}{'kind':<8}{'missing':>9}  {'first':<12}{'last':<12}")
    for sym in syms:
        for kind in backfill.TICK_KINDS:
            row = summary.get((sym, kind))
            if row:
                click.echo(
                    f"{sym:<8}{kind:<8}{row['count']:>9}  "
                    f"{row['first']:<12}{row['last']:<12}"
                )
            else:
                click.echo(f"{sym:<8}{kind:<8}{0:>9}  {'-':<12}{'-':<12}")

    if dry_run:
        click.echo("dry-run: no data fetched.")
        return

    written = backfill.run_ticks(
        settings, work, rth_only=rth_only, force=force,
        force_overwrite=force_overwrite, require_complete=require_complete,
        mark_empty_ok=mark_empty_ok,
    )
    click.echo(f"done: {written} partitions written to {settings.raw_dir}")


@backfill_cli.command("letf-bars")
@click.option("--start", default="2023-07-01", help="First month start date YYYY-MM-DD")
@click.option("--dry-run", is_flag=True, help="Print the plan; do not fetch.")
def letf_bars(start: str, dry_run: bool) -> None:
    settings = get_settings()
    work = backfill.plan_letf_bars(settings, start=start)

    click.echo(f"letf-bars plan  from {start}  total monthly partitions: {len(work)}")
    by_sym: dict[str, list[str]] = {}
    for sym, month in work:
        by_sym.setdefault(sym, []).append(month)
    for sym in sorted(by_sym):
        months = sorted(by_sym[sym])
        click.echo(f"{sym:<8}{len(months):>4} months  {months[0]}..{months[-1]}")

    if dry_run:
        click.echo("dry-run: no data fetched.")
        return

    written = backfill.run_letf_bars(settings, work)
    click.echo(f"done: {written} monthly partitions written to {settings.raw_dir}")


@backfill_cli.command("status")
def status() -> None:
    settings = get_settings()
    rows = backfill.status(settings)
    if not rows:
        click.echo("lake empty (no partitions found under any read root).")
        return
    click.echo(
        f"{'symbol':<8}{'kind':<14}{'present':>8}{'empty':>7}  {'first':<12}{'last':<12}"
    )
    for (sym, kind), r in rows.items():
        click.echo(
            f"{sym:<8}{kind:<14}{r['present']:>8}{r['empty']:>7}  "
            f"{str(r['first']):<12}{str(r['last']):<12}"
        )
    click.echo("roots breakdown (files per root):")
    # roots are identical across rows; print once from any row.
    any_row = next(iter(rows.values()))
    for root in any_row["roots"]:
        click.echo(f"  {root}")


if __name__ == "__main__":
    backfill_cli()
