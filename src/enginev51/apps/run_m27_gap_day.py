"""M27 gap-day reversion runner (family ``gap_day_reversion_v1``).

Wires the frozen harness in ``research_screens.gap_day`` to the real data lakes
(raw bars1d for prev_close/open, bbo-1s for the intraday quote path) and executes
the family's SINGLE registered look (M3_REGISTRATION.md section M27). Flow, ordering
ENFORCED: ``assert_before_holdout`` -> ``assert_look_not_spent`` -> cost floors
FIRST (frozen to cost_floors.json before any mean) -> build fired events -> t50/t100
cell stats (which REFUSE to run without the floors file) -> ADIA daily panel ->
report-only strata -> v6.1 ground-truth samples -> ``write_outputs`` ->
``mark_look_spent``. The one look is the ORCHESTRATOR's; a second run is refused
unless it is a ledgered ``--defect-rerun --reason ...`` fix.

The look-state directory is NEVER caller-relocatable (no --out-dir option): the
one-look gate is anchored to the canonical experiments dir (reviewer B1).

Console note: on Windows set ``PYTHONIOENCODING=utf-8`` (no non-ascii is printed).

    uv run python -m enginev51.apps.run_m27_gap_day --trial-id M27-gap-day \
        --start 2023-08-01 --end 2026-05-31 --seed 7
"""

from __future__ import annotations

import subprocess
import time
from datetime import date

import click
import polars as pl

from enginev51.config import PROJECT_ROOT
from enginev51.research_screens import gap_day as gd


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


@click.command()
@click.option("--trial-id", default="M27-gap-day", help="Experiment id -> research/experiments/<id>/.")
@click.option("--start", default=gd.START.isoformat(), help="First session (ISO date), inclusive.")
@click.option("--end", default=gd.END.isoformat(), help="Last session (ISO date), inclusive; < holdout.")
@click.option("--seed", default=gd.SEED, type=int, help="Latency/bootstrap seed (registration-pinned).")
@click.option("--defect-rerun", is_flag=True, default=False,
              help="Ledgered code-defect re-run of the ONE look (requires --reason).")
@click.option("--reason", default=None, help="Non-empty reason for a --defect-rerun (ledgered).")
def main(
    trial_id: str,
    start: str,
    end: str,
    seed: int,
    defect_rerun: bool,
    reason: str | None,
) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)

    gd.assert_before_holdout(end_d)
    # The look-state directory is NEVER caller-relocatable (no --out-dir option):
    # the one-look gate is anchored to the canonical experiments dir so a fresh
    # path can never sidestep the single-registered-look guarantee (reviewer B1).
    resolved_out = gd.out_dir_for()
    assert resolved_out == gd.canonical_out_dir(), "M27 look state must be canonical"
    gd.assert_look_not_spent(defect_rerun=defect_rerun, reason=reason)

    load_bars = gd.make_bars_loader()
    get_bbo = gd.make_bbo_getter()

    t0 = time.time()
    # Floors FIRST -- frozen to cost_floors.json BEFORE any conditional mean exists.
    floors = gd.write_cost_floors_first(
        start=start_d, end=end_d, load_bars=load_bars, get_bbo=get_bbo,
    )
    click.echo(f"cost floors frozen: pooled={floors['pooled_floor_bps']} bps")

    events, funnel = gd.build_events(
        start=start_d, end=end_d, load_bars=load_bars, get_bbo=get_bbo, seed=seed,
    )
    click.echo(f"funnel: {funnel}")

    # Stats REFUSE to run without cost_floors.json (floors-before-means guard).
    t50 = gd.cell_stats(events, gd.THRESH_T50)
    t100 = gd.cell_stats(events, gd.THRESH_T100)
    panel = gd.adia_panel(events)
    strata = gd.report_strata(events)
    gt = gd.ground_truth(events)

    atlas_md = gd.build_atlas_md(
        trial_id, t50, t100, panel, strata, funnel, floors, seed=seed,
    )
    paths = gd.write_outputs(
        resolved_out, trial_id, events, t50, t100, panel, strata, funnel, floors, atlas_md, gt,
    )
    gd.mark_look_spent(trial_id=trial_id, git_sha=_git_sha())
    wall_s = time.time() - t0

    click.echo(f"trial: {trial_id}  {start}..{end}  seed={seed}")
    click.echo(f"t50:  N={t50['N']}  sessions={t50['n_sessions']}  "
               f"mean={t50['mean_net_bps']}  PASS={t50['pass']}  "
               f"UNDERPOWERED={t50['underpowered']}  BETWEEN={t50['between']}")
    click.echo(f"t100: N={t100['N']}  sessions={t100['n_sessions']}  "
               f"mean={t100['mean_net_bps']}  PASS={t100['pass']}  "
               f"UNDERPOWERED={t100['underpowered']}  BETWEEN={t100['between']}")
    click.echo(f"ADIA panel (t50): T={panel['T']}  SR={panel['sr_native']}  "
               f"PSR={panel['psr_sr0_0']}  MinTRL={panel['min_trl']}")
    click.echo(f"atlas:   {paths['atlas']}")
    click.echo(f"cells:   {paths['cells']}")
    click.echo(f"look_state written; look SPENT. wall: {wall_s:.1f}s")


if __name__ == "__main__":
    main()
