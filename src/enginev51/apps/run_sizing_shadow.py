"""M23 dynamic-sizing shadow runner (family ``sizing_shadow_v1``).

Wires the frozen kernels in ``research_screens.sizing_shadow`` to the real data lake.
REPORT-ONLY: no gate, no look-state, no promotion rule -- stateless and idempotent, so
every run simply overwrites the derived artifacts. Two subcommands, never pooled:

  * ``dev-reference`` -- the ONE expectation-setting computation on the published dev
    event stream (<= 2026-05-31, ruling A1 OOS walk-forward p_win). No bar attached.
  * ``forward`` -- recomputed after each banked session as a DERIVED report; READS
    ``research/forward/ledger.parquet`` (via forward_paper.load_ledger) and NEVER writes
    it. Also emits the display-only PSR/MinTRL panel for the three M10 streams.

Console note: on Windows set ``PYTHONIOENCODING=utf-8`` (no non-ascii is printed).

    uv run python -m enginev51.apps.run_sizing_shadow dev-reference
    uv run python -m enginev51.apps.run_sizing_shadow forward
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import click
import polars as pl

from enginev51.config import PROJECT_ROOT
from enginev51.research_screens import sizing_shadow as ss

DEV_END = date(2026, 5, 31)  # last legal dev session (strictly < the 2026-06-01 seal)


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


@click.group()
def main() -> None:
    """M23 dynamic-sizing shadow (report-only measurement instrument)."""


@main.command("dev-reference")
@click.option("--events", default=ss.DEV_EVENTS_PARQUET,
              help="Dev OOS event stream (M8-meta-v1/oos_predictions.parquet).")
def dev_reference(events: str) -> None:
    """The single dev-reference computation (expectation-setting; no bar)."""
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    # Dev reference is pinned strictly before the seal (the dev stream ends 2026-05-31).
    ss.assert_before_holdout(DEV_END)
    events_path = _resolve(events)
    if not events_path.exists():
        click.echo(f"dev events parquet not found at {events_path}; ship code + tests.")
        return

    evs = ss.load_dev_events(events_path)
    closes = {s: ss.load_raw_closes(s) for s in ss.UNIVERSE}
    evs = ss.attach_weights(evs, closes)

    panel = ss.sizing_panel(evs, ss.SOURCE_DEV)
    out = ss.write_source_panel(panel, ss.SOURCE_DEV)

    click.echo(f"dev-reference: classical events={evs.height}  T={panel['T']}")
    click.echo(f"  mean_usd={panel['mean_usd']}  SR={panel['sr_native']}  "
               f"PSR[SR0=0]={panel['psr_sr0_0']}  MinTRL={panel['min_trl']}")
    click.echo(f"  degenerate/single/multi sessions: {panel['n_degenerate_sessions']}/"
               f"{panel['n_single_event_sessions']}/{panel['n_multi_event_sessions']}")
    click.echo(f"panel: {out}")


@main.command("forward")
def forward() -> None:
    """Recompute the forward-to-date report from the ledger (READ-ONLY)."""
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety

    classical = ss.load_forward_classical()
    if classical.height == 0:
        click.echo("forward ledger empty (no banked classical champion-5 events yet).")
        # Still refresh the combined doc so panel.md reflects the empty forward section.
        panel = ss.sizing_panel(classical, ss.SOURCE_FWD)
        ss.write_source_panel(panel, ss.SOURCE_FWD, streams=[])
        return

    closes = {s: ss.load_raw_closes(s) for s in ss.UNIVERSE}
    classical = ss.attach_weights(classical, closes)
    panel = ss.sizing_panel(classical, ss.SOURCE_FWD)

    # Display-only M10 stream panel: the FULL ledger, all three streams, gate untouched.
    full = ss.load_ledger().with_columns(pl.lit(ss.SOURCE_FWD).alias("source"))
    streams = ss.stream_psr_panel(full)

    out = ss.write_source_panel(panel, ss.SOURCE_FWD, streams=streams)

    click.echo(f"forward: classical champion-5 events={classical.height}  T={panel['T']}")
    click.echo(f"  mean_usd={panel['mean_usd']}  SR={panel['sr_native']}  "
               f"PSR[SR0=0]={panel['psr_sr0_0']}  MinTRL={panel['min_trl']}")
    for s in streams:
        click.echo(f"  stream {s['stream']}: T={s['T']}  SR={s['sr_native']}  "
                   f"PSR={s['psr_sr0_0']}  MinTRL={s['min_trl']}")
    click.echo(f"panel: {out}")


if __name__ == "__main__":
    main()
