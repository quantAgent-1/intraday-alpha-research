"""GEX snapshot collector CLI.

Pulls a live OPRA option-chain snapshot per symbol, writes contract rows +
a GammaMap summary (see flows.gex_collect), and prints the summary line.

Intended cadence: twice daily, 15:00 ET (pre-close positioning read) and
16:05 ET (settled EOD map). Scheduling is wired at M6; until then run manually
with --once.

PROTOCOL v6 §5: this collector produces FORWARD-ONLY data. GEX snapshots are
BANNED from any Stage A gated result — deploy-lens / named-payer mechanism input
only, never gate currency.

    uv run python -m enginev51.apps.collect_gex --symbols NVDA,TSLA,AMD,MU --once
"""

from __future__ import annotations

import click

from enginev51.config import get_settings
from enginev51.flows.gex_collect import fetch_option_chain_snapshot, snapshot_to_parquet


def _fmt(x: float) -> str:
    return "nan" if x != x else f"{x:.2f}"


@click.command()
@click.option("--symbols", default="NVDA,TSLA,AMD,MU", help="Comma-separated underlyings.")
@click.option("--once", is_flag=True, help="Take one snapshot per symbol and exit.")
@click.option("--expiry-within-days", default=45, show_default=True, type=int)
@click.option("--strike-band-pct", default=0.25, show_default=True, type=float)
def main(symbols: str, once: bool, expiry_within_days: int, strike_band_pct: float) -> None:
    """Snapshot the GEX map for each symbol and print the GammaMap summary."""
    if not once:
        raise click.UsageError("only --once is supported until M6 scheduling wiring.")

    settings = get_settings()
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]

    for sym in syms:
        try:
            chain = fetch_option_chain_snapshot(
                settings,
                sym,
                expiry_within_days=expiry_within_days,
                strike_band_pct=strike_band_pct,
            )
        except Exception as exc:  # noqa: BLE001 — surface the exact API error to the operator
            click.echo(f"{sym}: FETCH FAILED - {exc}")
            continue

        ts = chain["ts"]
        path, gm = snapshot_to_parquet(settings, sym, chain, ts)
        click.echo(
            f"{sym}: n_contracts={len(chain['strike'])} spot={_fmt(gm.spot)} "
            f"net_gex={gm.net_gex:+.3e} regime={gm.regime:+d} "
            f"flip={_fmt(gm.gamma_flip)} call_wall={_fmt(gm.call_wall)} "
            f"put_wall={_fmt(gm.put_wall)} pin={_fmt(gm.pin)}"
        )
        click.echo(f"     -> {path}")


if __name__ == "__main__":
    main()
