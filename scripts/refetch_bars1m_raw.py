"""Refetch RAW 1-min bars for the 5 signal symbols into the PRIMARY lake.

Audit F1 correction (research/SIM_AUDIT_2026-07-21.md; ledger trial
``M3-A0-v1.2-raw-correction``): the signal-symbol ``bars1m`` lake was
dividend/split back-adjusted (legacy fetch used ``adjustment="all"``) while
fills execute on the raw tape, so detector price anchors sat on the wrong
scale (measured NVDA ~-12 bps, MU-2024 -82.9 bps; TSLA/AMD ~0 controls).

The fix is data-only: refetch ``adjustment="raw"`` bars into the PRIMARY lake
(``data/raw/sip/bars1m/{SYMBOL}/{YYYY-MM}.parquet``), which ``store.py``'s
primary-first shadowing (scan_kind_multi) then serves in place of the legacy
adjusted copies -- no code, parameter, harness or cost change to any trial.

Three read-only-except-the-lake subcommands:

    uv run python scripts/refetch_bars1m_raw.py fetch [--force]
    uv run python scripts/refetch_bars1m_raw.py gate
    uv run python scripts/refetch_bars1m_raw.py analyze <results.parquet> \
        --symbols NVDA,TSLA,MU,AMD

``fetch`` writes the primary partitions (idempotent; skips months already
present unless ``--force``). ``gate`` reproduces the audit's per-minute
bar-VWAP/tape-VWAP median-offset measurement on OLD (legacy) vs NEW (primary)
bars at the registered probe sessions. ``analyze`` prints day-clustered CIs
(pooled + per-symbol vwap_magnet) from a trial ``results.parquet`` using the
same ``stress.clustered_mean_ci`` the trial runner uses.
"""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import click
import numpy as np
import polars as pl

from enginev51.backtest.stress import clustered_mean_ci
from enginev51.config import get_settings
from enginev51.data import store
from enginev51.data.alpaca_hist import AlpacaHist
from enginev51.protocol import SealViolation

# --- frozen scope (audit F1 / M3-A0-v1.2-raw-correction) --------------------
SYMBOLS: tuple[str, ...] = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")
FEED = "sip"
KIND = "bars1m"
FETCH_START = datetime(2024, 1, 1, tzinfo=UTC)
FETCH_END = datetime(2026, 6, 1, tzinfo=UTC)  # exclusive; == sealed holdout
ET = ZoneInfo("America/New_York")
NS_PER_MIN = 60_000_000_000

# audit probe sessions (SIM_AUDIT_2026-07-21 §2) + the audit's OLD medians so the
# gate self-validates its method by reproducing them on the legacy adjusted bars.
PROBE_SESSIONS = ("2025-10-15", "2026-02-17", "2026-05-15")
AUDIT_OLD_OFFSET_BPS: dict[tuple[str, str], float] = {
    ("NVDA", "2025-10-15"): -12.74, ("NVDA", "2026-02-17"): -12.16, ("NVDA", "2026-05-15"): -11.64,
    ("GOOGL", "2025-10-15"): -19.52, ("GOOGL", "2026-02-17"): -13.01, ("GOOGL", "2026-05-15"): -5.98,
    ("MU", "2025-10-15"): -9.76, ("MU", "2026-02-17"): -5.75, ("MU", "2026-05-15"): -1.51,
    ("AMD", "2025-10-15"): 0.02, ("AMD", "2026-02-17"): 0.01, ("AMD", "2026-05-15"): 0.03,
    ("TSLA", "2025-10-15"): 0.01, ("TSLA", "2026-02-17"): 0.00, ("TSLA", "2026-05-15"): 0.00,
    ("MU", "2024-02-05"): -82.9,
}


def _months(start: datetime, end: datetime) -> list[tuple[int, int]]:
    """Every (year, month) whose first day is in [start, end)."""
    out: list[tuple[int, int]] = []
    y, m = start.year, start.month
    while datetime(y, m, 1, tzinfo=UTC) < end:
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _month_bounds(y: int, m: int) -> tuple[datetime, datetime]:
    lo = datetime(y, m, 1, tzinfo=UTC)
    hi = datetime(y + 1, 1, 1, tzinfo=UTC) if m == 12 else datetime(y, m + 1, 1, tzinfo=UTC)
    return lo, min(hi, FETCH_END)


# --------------------------------------------------------------------------- fetch


@click.group()
def cli() -> None:
    """Audit-F1 raw-bars correction utilities."""


@cli.command()
@click.option("--force", is_flag=True, default=False, help="Re-fetch months already present.")
def fetch(force: bool) -> None:
    """Fetch raw 1-min bars for the 5 signal symbols into the primary lake."""
    if FETCH_END > datetime(2026, 6, 1, tzinfo=UTC):
        raise SealViolation("fetch would reach the sealed holdout")
    settings = get_settings()
    raw_dir = settings.raw_dir
    hist = AlpacaHist(settings)
    grand = 0
    try:
        for (y, m) in _months(FETCH_START, FETCH_END):
            mkey = f"{y:04d}-{m:02d}"
            lo, hi = _month_bounds(y, m)
            todo = [
                s for s in SYMBOLS
                if force or not store.partition_exists(raw_dir, FEED, KIND, s, mkey)
            ]
            if not todo:
                click.echo(f"{mkey}: all present, skip")
                continue
            bars = hist.fetch_bars_multi(
                todo, lo, hi, feed=FEED, timeframe="1Min", adjustment="raw"
            )
            for s in todo:
                rows = bars.get(s.upper(), [])
                store.write_partition(raw_dir, FEED, KIND, s, mkey, rows)
                grand += len(rows)
                click.echo(f"{s} {mkey}: {len(rows)} rows")
    finally:
        hist.close()
    click.echo(f"TOTAL rows written: {grand}")


# ----------------------------------------------------------------------- gate


def _session_utc_bounds(session_iso: str) -> tuple[int, int]:
    """RTH [09:30, 16:00) ET for a session, as UTC epoch-ns (DST-correct)."""
    d = datetime.fromisoformat(session_iso).date()
    open_et = datetime(d.year, d.month, d.day, 9, 30, tzinfo=ET)
    close_et = datetime(d.year, d.month, d.day, 16, 0, tzinfo=ET)
    to_ns = lambda t: int(t.astimezone(UTC).timestamp() * 1e9)  # noqa: E731
    return to_ns(open_et), to_ns(close_et)


def _bar_vwap_minutes(root, symbol: str, session_iso: str) -> pl.DataFrame | None:
    """Per-RTH-minute (minute, bar_vwap) from a specific lake root, or None."""
    mkey = session_iso[:7]
    p = store.partition_path(root, FEED, KIND, symbol, mkey)
    if not p.exists():
        return None
    o, c = _session_utc_bounds(session_iso)
    df = (
        pl.read_parquet(p)
        .filter((pl.col("ts") >= o) & (pl.col("ts") < c) & (pl.col("vwap") > 0))
        .select(((pl.col("ts") - o) // NS_PER_MIN).alias("minute"), pl.col("vwap").alias("bar_vwap"))
    )
    return df if df.height else None


def _tape_vwap_minutes(settings, symbol: str, session_iso: str) -> pl.DataFrame | None:
    """Per-minute tape VWAP = sum(px*sz)/sum(sz) over the raw trade tape."""
    o, _ = _session_utc_bounds(session_iso)
    for r in settings.read_roots:
        p = store.partition_path(r, FEED, "trades", symbol, session_iso)
        if p.exists():
            tr = pl.read_parquet(p)
            break
    else:
        return None
    if "size" not in tr.columns:
        return None
    tr = tr.filter((pl.col("price") > 0) & (pl.col("size") > 0))
    if tr.height == 0:
        return None
    return (
        tr.select(
            ((pl.col("ts") - o) // NS_PER_MIN).alias("minute"),
            (pl.col("price") * pl.col("size")).alias("_pv"),
            pl.col("size").alias("_v"),
        )
        .group_by("minute")
        .agg((pl.col("_pv").sum() / pl.col("_v").sum()).alias("tape_vwap"))
    )


def _median_offset_bps(bar: pl.DataFrame | None, tape: pl.DataFrame | None) -> tuple[float | None, int]:
    """Median over RTH minutes of (bar_vwap/tape_vwap - 1) * 1e4, and n minutes."""
    if bar is None or tape is None:
        return None, 0
    j = bar.join(tape, on="minute", how="inner").filter(pl.col("tape_vwap") > 0)
    if j.height == 0:
        return None, 0
    ratio = (j["bar_vwap"] / j["tape_vwap"]).to_numpy()
    return float((np.median(ratio) - 1.0) * 1e4), int(j.height)


@cli.command()
def gate() -> None:
    """Acceptance gate: OLD (legacy) vs NEW (primary) median bar/tape VWAP offset."""
    settings = get_settings()
    primary = settings.raw_dir
    legacy = settings.legacy_data_dir / "raw"
    probes = [(s, sess) for sess in PROBE_SESSIONS for s in SYMBOLS] + [("MU", "2024-02-05")]
    click.echo(f"{'symbol':6} {'session':12} {'audit_old':>10} {'meas_old':>10} {'meas_new':>10} {'n_min':>6} {'pass':>5}")
    worst = 0.0
    for sym, sess in probes:
        tape = _tape_vwap_minutes(settings, sym, sess)
        old, n_old = _median_offset_bps(_bar_vwap_minutes(legacy, sym, sess), tape)
        new, n_new = _median_offset_bps(_bar_vwap_minutes(primary, sym, sess), tape)
        cited = AUDIT_OLD_OFFSET_BPS.get((sym, sess))
        ok = new is not None and abs(new) < 1.0
        worst = max(worst, abs(new)) if new is not None else worst
        c_s = f"{cited:+.2f}" if cited is not None else "-"
        o_s = f"{old:+.2f}" if old is not None else "NA"
        n_s = f"{new:+.3f}" if new is not None else "NA"
        click.echo(
            f"{sym:6} {sess:12} {c_s:>10} {o_s:>10} {n_s:>10} "
            f"{max(n_old, n_new):>6} {('YES' if ok else 'NO'):>5}"
        )
    click.echo(f"worst |new offset| = {worst:.3f} bps  (gate requires < 1.0 on all)")


# -------------------------------------------------------------------- analyze


def _ci(sub: pl.DataFrame) -> str:
    if sub.height == 0:
        return "n=0"
    m, lo, hi = clustered_mean_ci(sub["net_bps"].to_numpy(), sub["session"].to_numpy())
    return f"mean={m:+.2f} [{lo:+.2f}, {hi:+.2f}] n={sub.height} sess={sub['session'].n_unique()}"


@cli.command()
@click.argument("results_path")
@click.option("--symbols", default="NVDA,TSLA,MU,AMD", help="Per-symbol vwap_magnet split.")
def analyze(results_path: str, symbols: str) -> None:
    """Pooled + per-symbol vwap_magnet day-clustered CIs from a results.parquet."""
    df = pl.read_parquet(results_path)
    taken = df.filter(pl.col("taken"))
    vwap = taken.filter(pl.col("payer") == "vwap_magnet")
    click.echo(f"results: {results_path}  (taken={taken.height})")
    click.echo(f"POOLED all-payers  : {_ci(taken)}")
    click.echo(f"POOLED vwap_magnet : {_ci(vwap)}")
    for s in [x.strip().upper() for x in symbols.split(",") if x.strip()]:
        click.echo(f"  vwap {s:5}: {_ci(vwap.filter(pl.col('symbol') == s))}")
    for payer in sorted(taken["payer"].unique().to_list()):
        if payer != "vwap_magnet":
            click.echo(f"POOLED {payer:12}: {_ci(taken.filter(pl.col('payer') == payer))}")


if __name__ == "__main__":
    cli()
