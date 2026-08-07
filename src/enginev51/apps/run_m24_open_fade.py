"""M24 opening-auction dislocation fade runner (family ``open_auction_fade_v1``).

Wires the frozen harness in ``research_screens.open_fade`` to the real data lake and
executes the family's SINGLE registered look (M3_REGISTRATION.md section M24). Flow
(ordering enforced): ``assert_before_holdout`` -> ``assert_look_not_spent`` ->
``build_events`` (opening-basis signal at 09:28:30 ET, fade AGAINST, exit at the
same-session official close, raw bars1d both legs) -> cell_stats t25/t50 (t50 nested)
-> ADIA No.19 panel -> rho vs champion -> report-only strata (incl. the gap_mr fence)
-> v6.1 ground truth -> ``write_outputs`` -> ``mark_look_spent``. The one look is the
ORCHESTRATOR's to execute; a second run is refused unless it is a ledgered
``--defect-rerun --reason ...`` fix. There is NO --out-dir option (B1 lesson): the
one-look gate is hard-anchored to the canonical experiments dir.

Console note: on Windows set ``PYTHONIOENCODING=utf-8`` (no non-ascii is printed).

    uv run python -m enginev51.apps.run_m24_open_fade --trial-id M24-open-fade \
        --start 2020-01-02 --end 2026-05-31
"""

from __future__ import annotations

import json
import subprocess
import time
from datetime import date

import click
import polars as pl

from enginev51.config import PROJECT_ROOT, get_settings
from enginev51.research_screens import open_fade as of


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
@click.option("--trial-id", default="M24-open-fade", help="Experiment id -> research/experiments/<id>/.")
@click.option("--start", default="2020-01-02", help="First session (ISO date), inclusive.")
@click.option("--end", default="2026-05-31", help="Last session (ISO date), inclusive; < holdout.")
@click.option("--seed", default=7, type=int, help="CI/bootstrap seed (registration-pinned).")
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
    settings = get_settings()
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)

    of.assert_before_holdout(end_d)
    # The look-state directory is NEVER caller-relocatable (no --out-dir option): the
    # one-look gate is anchored to the canonical experiments dir so a fresh path can
    # never sidestep the single-registered-look guarantee (reviewer B1).
    resolved_out = of.out_dir_for()
    assert resolved_out == of.canonical_out_dir(), "M24 look state must be canonical"
    of.assert_look_not_spent(defect_rerun=defect_rerun, reason=reason)

    t0 = time.time()
    events, funnel = of.build_events(settings, start=start_d, end=end_d)

    t25 = of.cell_stats(events, thresh=of.THRESH_T25)
    t50 = of.cell_stats(events, thresh=of.THRESH_T50)
    adia = of.adia_panel(events)
    champion_daily = of.load_champion_daily()
    rho = of.rho_panel(events, champion_daily)
    strata = of.build_strata(events)
    gt = of.ground_truth(events)

    cells = {"t25": t25, "t50": t50, "adia": adia, "rho": rho, "strata": strata}
    atlas_md = of.build_atlas_md(
        trial_id, events, funnel, t25, t50, adia, rho, strata, seed=seed,
    )
    paths = of.write_outputs(resolved_out, trial_id, events, cells, atlas_md, gt)
    of.mark_look_spent(trial_id=trial_id, git_sha=_git_sha())
    wall_s = time.time() - t0

    click.echo(f"trial: {trial_id}  {start}..{end}  seed={seed}")
    click.echo(f"funnel: {json.dumps(funnel['counts'], default=str)}  "
               f"candidates={funnel['candidates']}  reconciles={funnel['reconciles']}")
    click.echo(f"coverage: {funnel['coverage']['n_present']}/{funnel['coverage']['n_total']} "
               f"NOII names present")
    click.echo(f"t25: n={t25['n_fired']}  sessions={t25['n_sessions']}  "
               f"mean={t25['mean_net_bps']}  PASS={t25['pass']}  "
               f"UNDERPOWERED={t25['underpowered']}  BETWEEN={t25['between_the_bars']}")
    click.echo(f"t50: n={t50['n_fired']}  sessions={t50['n_sessions']}  "
               f"mean={t50['mean_net_bps']}  PASS={t50['pass']}  "
               f"UNDERPOWERED={t50['underpowered']}  BETWEEN={t50['between_the_bars']}")
    click.echo(f"ADIA: SR={adia['sr_native']}  PSR[SR0=0]={adia['psr_sr0_0']}  "
               f"MinTRL={adia['min_trl']}  T={adia['T']}")
    click.echo(f"rho vs champion: {json.dumps(rho, default=str)}")
    click.echo(f"gap_mr fence corr(basis,gap): {strata['corr_basis_gap']}")
    click.echo(f"atlas:   {paths['atlas']}")
    click.echo(f"cells:   {paths['cells']}")
    click.echo(f"look_state written; look SPENT. wall: {wall_s:.1f}s")


if __name__ == "__main__":
    main()
