"""M22 earnings-day closing-crosses runner (family ``earnings_close_v1``).

Wires the frozen harness in ``research_screens.earnings_close`` to the real data
lake and executes the family's SINGLE registered look (M3_REGISTRATION.md § M22).
Flow (ordering enforced): ``assert_before_holdout`` -> ``assert_look_not_spent``
-> day0 whitelists (champion 5 / broad 12) -> Cell A build+stats (run_basis_trial
VERBATIM) -> Cell B build+stats (run_m11.fire_near_ref_event behind the whitelist)
-> Cell C strata (report-only) -> v6.1 ground-truth samples -> ``write_outputs``
-> ``mark_look_spent``. The one look is the ORCHESTRATOR's to execute; a second
run is refused unless it is a ledgered ``--defect-rerun --reason ...`` fix.

Console note: on Windows set ``PYTHONIOENCODING=utf-8`` (no non-ascii is printed).

    uv run python -m enginev51.apps.run_m22_earnings_close --trial-id M22-earnings-close \
        --start 2020-01-02 --end 2026-05-31 --seed 7
"""

from __future__ import annotations

import json
import subprocess
import time
from datetime import date
from pathlib import Path

import click
import polars as pl

from enginev51.config import PROJECT_ROOT, get_settings
from enginev51.research_screens import earnings_close as ec


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


@click.command()
@click.option("--trial-id", default="M22-earnings-close", help="Experiment id -> research/experiments/<id>/.")
@click.option("--start", default="2020-01-02", help="First session (ISO date), inclusive.")
@click.option("--end", default="2026-05-31", help="Last session (ISO date), inclusive; < holdout.")
@click.option("--seed", default=7, type=int, help="Latency/bootstrap seed (registration-pinned).")
@click.option("--events", default=ec.EVENTS_PARQUET, help="M21 earnings events.parquet (calendar data only).")
@click.option("--defect-rerun", is_flag=True, default=False,
              help="Ledgered code-defect re-run of the ONE look (requires --reason).")
@click.option("--reason", default=None, help="Non-empty reason for a --defect-rerun (ledgered).")
def main(
    trial_id: str,
    start: str,
    end: str,
    seed: int,
    events: str,
    defect_rerun: bool,
    reason: str | None,
) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    settings = get_settings()
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)

    ec.assert_before_holdout(end_d)
    # The look-state directory is NEVER caller-relocatable (no --out-dir option):
    # the one-look gate is anchored to the canonical experiments dir so a fresh
    # path can never sidestep the single-registered-look guarantee (reviewer B1).
    resolved_out = ec.out_dir_for()
    assert resolved_out == ec.canonical_out_dir(), "M22 look state must be canonical"
    ec.assert_look_not_spent(defect_rerun=defect_rerun, reason=reason)

    events_path = _resolve(events)
    if not events_path.exists():
        click.echo(f"M21 events.parquet not found at {events_path}; ship code + tests.")
        return

    wl_a = ec.load_day0_whitelist(events_path, ec.CELL_A_UNIVERSE, end=end_d)
    wl_b = ec.load_day0_whitelist(events_path, ec.CELL_B_UNIVERSE, end=end_d)
    click.echo(f"day0 whitelist: champion-5={len(wl_a)}  broad-12={len(wl_b)}")

    t0 = time.time()
    cell_a_events, a_funnel = ec.build_cell_a_events(
        settings, whitelist=wl_a, start=start_d, end=end_d, seed=seed,
    )
    a_stats = ec.cell_a_stats(cell_a_events)

    cell_b_events, b_funnel = ec.build_cell_b_events(
        settings, whitelist=wl_b, start=start_d, end=end_d,
    )
    b_stats = ec.cell_b_stats(cell_b_events)

    cell_c = ec.cell_c_strata(cell_a_events, cell_b_events)

    gt_a = ec.ground_truth_a(cell_a_events)
    gt_b = ec.ground_truth_b(cell_b_events)

    atlas_md = ec.build_atlas_md(
        trial_id, cell_a_events, a_stats, a_funnel,
        cell_b_events, b_stats, b_funnel, cell_c, seed=seed,
    )
    paths = ec.write_outputs(
        resolved_out, trial_id, cell_a_events, cell_b_events, cell_c,
        a_stats, b_stats, atlas_md, gt_a, gt_b,
    )
    ec.mark_look_spent(trial_id=trial_id, git_sha=_git_sha())
    wall_s = time.time() - t0

    click.echo(f"trial: {trial_id}  {start}..{end}  seed={seed}")
    click.echo(f"Cell A: fired day0={a_stats['n_fired_day0']}  "
               f"mean={a_stats['day0_mean_net_bps']}  PASS={a_stats['pass']}  "
               f"UNDERPOWERED={a_stats['underpowered']}")
    click.echo(f"  baseline mean={a_stats['baseline_mean_net_bps']}  "
               f"amp_ratio={a_stats['amp_ratio_day0_over_baseline']}  "
               f"amp_prong_binds={a_stats['amp_prong_binds']}")
    click.echo(f"Cell B: fired={b_stats['n_fired']}  mean={b_stats['mean_net_bps']}  "
               f"PASS={b_stats['pass']}  UNDERPOWERED={b_stats['underpowered']}")
    click.echo(f"Cell B funnel: {json.dumps(b_funnel, default=str)}")
    click.echo(f"atlas:   {paths['atlas']}")
    click.echo(f"cells:   {paths['cells']}")
    click.echo(f"look_state written; look SPENT. wall: {wall_s:.1f}s")


if __name__ == "__main__":
    main()
