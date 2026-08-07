"""M20 scheduled-macro-window mid-alpha atlas runner (family ``sched_window_v1``).

Two-step, ordering-enforced:

    uv run python -m enginev51.apps.run_sched_window_atlas --split train
        -> writes cost_floors.json FIRST, then atlas_train.md + atlas_train_events
           .parquet + train_pass_list.json.

    uv run python -m enginev51.apps.run_sched_window_atlas --include-validate
        -> REFUSED unless cost_floors.json AND train_pass_list.json exist; then
           computes VALIDATE stats ONLY for the TRAIN screen-pass cells.

STAGE-1 SCREEN ONLY (mid-to-mid, no fills, no replay, not economics). The single
real-data TRAIN look is the orchestrator's to execute; this file only wires the
frozen harness in ``research_screens.sched_window`` to the real bbo-1s lake and the
macro calendar. The holdout is stripped inside the assembly path by ``apply_seal``.

Console note: on Windows set ``PYTHONIOENCODING=utf-8``.
"""

from __future__ import annotations

import json
from pathlib import Path

import click
import polars as pl

from enginev51.config import PROJECT_ROOT
from enginev51.research_screens import sched_window as sw

DEFAULT_CALENDAR = "data/external/macro_calendar.parquet"


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


@click.command()
@click.option(
    "--split",
    type=click.Choice(["train", "validate"]),
    default="train",
    help="Which split to compute (default train). --include-validate is the gated alias.",
)
@click.option(
    "--include-validate",
    is_flag=True,
    default=False,
    help="Compute VALIDATE (gated on train_pass_list.json); equivalent to --split validate.",
)
@click.option("--calendar", default=DEFAULT_CALENDAR, help="Macro-anchor calendar parquet.")
@click.option("--bbo-dir", default=None, help="bbo-1s lake root (default data/raw/bbo1s).")
@click.option("--out-dir", default=None, help="Override output dir (default research/experiments/M20-sched-window).")
def main(
    split: str,
    include_validate: bool,
    calendar: str,
    bbo_dir: str | None,
    out_dir: str | None,
) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # cp949 console safety on Windows
    do_validate = include_validate or split == "validate"
    target = "validate" if do_validate else "train"

    cal_path = _resolve(calendar)
    if not cal_path.exists():
        click.echo(
            f"macro calendar not found at {cal_path}. It is a parallel deliverable "
            "(scripts/build_macro_calendar.py). Ship code + tests; run this once the "
            "calendar parquet exists:\n  uv run python -m enginev51.apps."
            "run_sched_window_atlas --split train"
        )
        return

    calendar_df = sw.load_macro_calendar(cal_path)
    get_bbo = sw.make_bbo_getter(out_dir=bbo_dir)

    if do_validate:
        # Friendly pre-checks; compute_atlas re-enforces both as hard guards.
        if not sw.floors_path(out_dir).exists():
            raise click.ClickException(
                "cost_floors.json missing; run --split train first (floors are frozen "
                "before any conditional mean)."
            )
        if not sw.pass_list_path(out_dir).exists():
            raise click.ClickException(
                "train_pass_list.json missing; VALIDATE is gated on the TRAIN "
                "screen-pass list. Refused."
            )
        result = sw.compute_atlas(calendar_df, get_bbo, split="validate", out_dir=out_dir)
    else:
        # Ordering: floors FIRST, then any conditional mean.
        floors = sw.compute_cost_floors(calendar_df, get_bbo, out_dir=out_dir)
        click.echo(f"cost floors (class bar): {json.dumps(floors['class_floor_bps'])}")
        result = sw.compute_atlas(calendar_df, get_bbo, split="train", out_dir=out_dir)

    click.echo(f"split: {target}    cells: {result['n_cells']}    "
               f"audit rows: {result['n_events_rows']}")
    if target == "train":
        click.echo(f"SCREEN-PASS cells ({result['n_passing']}): {result['passing_cells']}")
    click.echo(f"atlas md:     {sw.atlas_md_path(target, out_dir)}")
    click.echo(f"atlas events: {sw.atlas_events_path(target, out_dir)}")
    if target == "train":
        click.echo(f"pass list:    {sw.pass_list_path(out_dir)}")


if __name__ == "__main__":
    main()
