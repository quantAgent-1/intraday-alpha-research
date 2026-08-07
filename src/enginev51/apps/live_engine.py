"""Live signal engine CLI (L0/L1) -- SIGNAL-ONLY rehearsal, manual decide, reconcile.

Implements the ``apps/live_engine.py`` click group of
``research/LIVE_SIGNAL_ENGINE_L0L1_DESIGN.md`` (section 1). Five commands over the
``enginev51.live`` core::

    uv run python -m enginev51.apps.live_engine rehearse --asof 2026-07-17
    uv run python -m enginev51.apps.live_engine decide --symbol NVDA --near .. --bid .. --ask ..
    uv run python -m enginev51.apps.live_engine reconcile --sessions 20
    uv run python -m enginev51.apps.live_engine monitor
    uv run python -m enginev51.apps.live_engine selftest

``rehearse`` replays a settled session through the forward clock's own functions for
display + journal (not a research look -- it recomputes already-published pipeline rows;
no gate output). ``decide`` is the L1 manual path (key 3-4 numbers -> full plan +
probability panel). ``reconcile`` joins the journal against the forward ledger (the
byte-agreement acceptance). ``monitor`` prints the ADIA panel. ``selftest`` proves the
plumbing on synthetic in-memory data without touching any real path.

SIGNAL-ONLY: no order routing, no broker/network import; the sole write target is the
signals journal. Windows console note: run with ``PYTHONIOENCODING=utf-8``; all output
is ASCII.
"""

from __future__ import annotations

import json
import tempfile
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import click
import polars as pl

from enginev51.apps import forward_paper as fp
from enginev51.apps import live_cockpit as lc
from enginev51.config import get_settings
from enginev51.live import engine as eng
from enginev51.live import reconcile as rec

ET = ZoneInfo("America/New_York")


# --------------------------------------------------------------------------- render


def _fmt(v: object) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _render_emission_table(scored: pl.DataFrame, journal: pl.DataFrame, session: str) -> str:
    """The rehearse emission table: the just-emitted close-window rows for ``session``."""
    lines = [
        "=" * 80,
        f" LIVE ENGINE :: REHEARSE (replay -> journal)   session {session}",
        "=" * 80,
        " numbers reuse forward_paper.compute_session_events + score_events "
        "(ledger-consistent)",
        "",
    ]
    sub = (
        journal.filter((pl.col("session") == session) & (pl.col("source") == "replay"))
        if journal.height
        else journal
    )
    if sub.height == 0:
        lines.append(" no replay rows emitted for this session (no valid basis + cross).")
        lines.append("=" * 80)
        return "\n".join(lines)
    view = sub.select(
        "symbol", "side", "basis_bps", "p_win", "taken_classical", "taken_meta",
        "tier", "vol_norm", "expected_net_bps", "order_type", "note",
    )
    with pl.Config(
        tbl_formatting="ASCII_MARKDOWN",
        tbl_hide_dataframe_shape=True,
        tbl_hide_column_data_types=True,
        tbl_rows=50,
        tbl_cols=-1,
        tbl_width_chars=200,
    ):
        lines.append(str(view))
    lines.append("=" * 80)
    return "\n".join(lines)


def _render_monitor(panel: dict) -> str:
    lines = [
        "-" * 80,
        " ADIA MONITOR PANEL (taken_classical stream; $10k research lens; SR0=0)",
        "-" * 80,
        f"  T (sessions):        {panel['T']}",
        f"  events:              {panel['n_events']}",
        f"  native SR:           {_fmt(panel['sr_native'])}",
        f"  PSR[SR0=0]:          {_fmt(panel['psr_sr0_0'])}",
        f"  MinTRL(alpha=0.05):  {_fmt(panel['min_trl'])}",
    ]
    if panel.get("ref_sr") is not None:
        lines.append(
            f"  PSR[SR0={panel['ref_sr']:.3f}] (live-testing probe): "
            f"{_fmt(panel['psr_ref'])}"
        )
    lines.append(
        f"  (gamma3, gamma4, rho): ({_fmt(panel['gamma3'])}, {_fmt(panel['gamma4'])}, "
        f"{_fmt(panel['rho'])})"
    )
    lines.append("  display-only: no statistic here gates trading.")
    lines.append("-" * 80)
    return "\n".join(lines)


# --------------------------------------------------------------------------- cli


@click.group()
def main() -> None:
    """Live signal engine (L0/L1) -- SIGNAL-ONLY replay/manual + reconcile/monitor."""
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows console safety


@main.command("rehearse")
@click.option("--asof", required=True, help="Settled session (ISO date) to replay from the lake.")
@click.option("--seed", type=int, default=7, show_default=True, help="Frozen latency-draw seed.")
@click.option("--ref-sr", type=float, default=None, help="Dev reference SR for the PSR probe.")
def rehearse_cmd(asof: str, seed: int, ref_sr: float | None) -> None:
    """Replay a settled session: emit the close-window rows + show the monitor panel."""
    settings = get_settings()
    asof_d = date.fromisoformat(asof)
    scored = eng.replay_session(settings, asof_d, seed=seed)
    journal = eng.load_journal()
    click.echo(_render_emission_table(scored, journal, asof))
    click.echo("")
    click.echo(_render_monitor(eng.monitor_panel(journal, ref_sr=ref_sr)))


@main.command("decide")
@click.option("--symbol", required=True, type=click.Choice(list(eng.UNIVERSE), case_sensitive=False))
@click.option("--near", required=True, type=float, help="NOII near (indicative clearing) price.")
@click.option("--bid", required=True, type=float, help="Prevailing NBBO bid.")
@click.option("--ask", required=True, type=float, help="Prevailing NBBO ask.")
@click.option("--far", type=float, default=None, help="NOII far price (-> near_far_bps).")
@click.option("--ref", type=float, default=None, help="NOII reference price (-> near_ref_bps).")
@click.option("--imbalance", type=float, default=None, help="SIGNED imbalance shares (buy +, sell -).")
@click.option("--paired", type=float, default=None, help="Paired shares (-> paired_ratio).")
@click.option("--adv20", type=float, default=None, help="ADV20 dollars (-> log_adv20, norm_imb).")
@click.option("--vol20", type=float, default=None, help="Trailing 20d realized vol (-> vol20).")
@click.option("--imb-growth-53", type=float, default=None, help="norm_imb(15:55) - norm_imb(15:53).")
@click.option("--imb-growth-51", type=float, default=None, help="norm_imb(15:55) - norm_imb(15:51).")
@click.option("--msg-count", type=float, default=None, help="NOII messages seen by 15:55:10.")
@click.option("--capital", type=float, default=lc.DEFAULT_CAPITAL_USD, show_default=True)
@click.option("--clip-cap", type=float, default=lc.DEFAULT_CLIP_CAP_USD, show_default=True)
@click.option("--spread-abort-bps", type=float, default=lc.DEFAULT_SPREAD_ABORT_BPS, show_default=True)
@click.option("--exit-mode", type=click.Choice(lc.EXIT_MODES), default="auto-note", show_default=True)
@click.option("--session", default=None, help="Session ISO date (default: today ET).")
@click.option("--model", "model_path", default=str(lc.MODEL_PATH), show_default=True)
def decide_cmd(
    symbol: str, near: float, bid: float, ask: float,
    far: float | None, ref: float | None, imbalance: float | None, paired: float | None,
    adv20: float | None, vol20: float | None, imb_growth_53: float | None,
    imb_growth_51: float | None, msg_count: float | None,
    capital: float, clip_cap: float, spread_abort_bps: float, exit_mode: str,
    session: str | None, model_path: str,
) -> None:
    """L1 manual path: key the screen values -> plan + probability panel; emit the row."""
    session_iso = session or datetime.now(ET).date().isoformat()
    kw = dict(
        far=far, ref=ref, imbalance=imbalance, paired=paired, adv20=adv20, vol20=vol20,
        imb_growth_53=imb_growth_53, imb_growth_51=imb_growth_51, msg_count=msg_count,
        capital_usd=capital, clip_cap_usd=clip_cap, spread_abort_bps=spread_abort_bps,
    )
    # n7: on a NYSE half-day the close-window emission is refused (R3). The ticket is
    # still valuable, so render it with do_emit=False and a labeled warning; exit 0.
    warn: str | None = None
    try:
        d = eng.manual_decide(
            symbol, near, bid, ask, session_iso=session_iso, model_path=model_path,
            do_emit=True, **kw,
        )
    except ValueError as exc:
        d = eng.manual_decide(
            symbol, near, bid, ask, session_iso=session_iso, model_path=model_path,
            do_emit=False, **kw,
        )
        warn = f"EARLY CLOSE - not journaled ({exc})"
    click.echo(lc.render_decide(d, exit_mode=exit_mode, model_note=d["model_note"]))
    click.echo("")
    if warn is not None:
        click.echo(f" [WARNING] {warn}")
    click.echo(
        f" TIER/VOL PANEL (M23 display-only):  tier={_fmt(d.get('tier'))}  "
        f"vol_norm={_fmt(d.get('vol_norm'))} "
        "(vol_norm n/a from a single keyed snapshot -- no trailing lake window)"
    )


@main.command("reconcile")
@click.option("--sessions", type=int, default=None, help="Reconcile only the most recent N sessions.")
@click.option("--ref-sr", type=float, default=None, help="Dev reference SR for the PSR probe.")
def reconcile_cmd(sessions: int | None, ref_sr: float | None) -> None:
    """Journal vs forward ledger: print the T+1 divergence report (read-only ledger)."""
    journal = eng.load_journal()
    ledger = fp.load_ledger()  # READ-ONLY (no append API imported)
    if sessions is not None and journal.height:
        keep = sorted(journal["session"].unique().to_list())[-sessions:]
        journal = journal.filter(pl.col("session").is_in(keep))
    # Scope the ledger to the journal's sessions so a not-yet-rehearsed forward session
    # is not mislabeled ledger_only; a ledger_only WITHIN a rehearsed session is a real
    # miss and stays surfaced (M2).
    if journal.height and ledger.height:
        ledger = ledger.filter(pl.col("session").is_in(journal["session"].unique().to_list()))
    flags = rec.reconcile(journal, ledger)
    click.echo(rec.reconcile_report(flags))


@main.command("monitor")
@click.option("--ref-sr", type=float, default=None, help="Dev reference SR for the PSR probe.")
def monitor_cmd(ref_sr: float | None) -> None:
    """Print the ADIA monitor panel over the journal to date."""
    click.echo(_render_monitor(eng.monitor_panel(eng.load_journal(), ref_sr=ref_sr)))


@main.command("selftest")
def selftest_cmd() -> None:
    """Synthetic in-memory round trip (emit -> read -> reconcile clean); no real paths."""
    session = "2026-07-17"  # a normal weekday, not a NYSE half-day
    with tempfile.TemporaryDirectory() as td:
        jpath = Path(td) / "signals_journal.parquet"
        rows = [
            {
                "session": session, "symbol": "NVDA", "window": "close",
                "basis_bps": 50.0, "p_win": 0.60, "side": 1,
                "taken_classical": True, "taken_meta": True,
                "tier": 1.5, "vol_norm": 1.0, "size_notional_research": 15000.0,
                "size_shares_deploy": 12, "expected_net_bps": 6.0,
                "order_type": eng.ORDER_TYPE_CLOSE, "limit_px": 100.0,
                "deadline_et": eng.DEADLINE_CLOSE_ET, "spread_abort": False, "note": "",
            },
            {
                "session": session, "symbol": "AMD", "window": "close",
                "basis_bps": -30.0, "p_win": 0.40, "side": -1,
                "taken_classical": True, "taken_meta": False,
                "tier": 0.0, "vol_norm": 1.0, "size_notional_research": 0.0,
                "size_shares_deploy": 8, "expected_net_bps": -1.0,
                "order_type": eng.ORDER_TYPE_CLOSE, "limit_px": 150.0,
                "deadline_et": eng.DEADLINE_CLOSE_ET, "spread_abort": False, "note": "",
            },
        ]
        n = eng.emit(rows, source="replay", journal_path=jpath)
        journal = eng.load_journal(jpath)
        # A synthetic "ledger" that agrees exactly -> reconcile must be clean.
        ledger = pl.DataFrame(
            {
                "session": [session, session],
                "symbol": ["NVDA", "AMD"],
                "basis_bps": [50.0, -30.0],
                "p_win": [0.60, 0.40],
                "net_bps": [6.0, -1.0],
            }
        )
        flags = rec.reconcile(journal, ledger)
        n_flagged = int(flags.filter(pl.col("flagged")).height) if flags.height else 0
        panel = eng.monitor_panel(journal)
        result = {
            "emitted": n,
            "journal_rows": journal.height,
            "reconcile_fields": flags.height,
            "reconcile_flagged": n_flagged,
            "monitor_T": panel["T"],
            "reconcile_clean": n_flagged == 0,
        }
        click.echo(json.dumps(result, indent=2))
        click.echo(rec.reconcile_report(flags))
        if n_flagged != 0:
            raise click.ClickException("selftest FAILED: synthetic round trip flagged a diff")
        click.echo("selftest OK: emit -> read -> reconcile clean (no real path touched).")


if __name__ == "__main__":
    main()
