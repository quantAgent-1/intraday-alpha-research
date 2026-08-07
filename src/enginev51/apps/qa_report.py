"""Data-quality report CLI.

Runs the tick/quote (and optionally bars1m) audit over the read-only lake and
emits a human-readable ``report.md`` plus a machine-readable ``stats.parquet``
under ``research/experiments/qa_<UTCstamp>/``. Reads only — never writes the lake.

    uv run python -m enginev51.apps.qa_report --symbols NVDA,TSLA --kinds trades,quotes
    uv run python -m enginev51.apps.qa_report --symbols NVDA,TSLA --bars --out auto
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click
import polars as pl
import structlog

from enginev51.config import PROJECT_ROOT, get_settings
from enginev51.data import qa

log = structlog.get_logger(__name__)


def _fmt_opt(v: Any, spec: str = "") -> str:
    if v is None:
        return "-"
    if spec:
        return format(v, spec)
    return str(v)


def _coverage_table(cov: dict[str, Any]) -> list[str]:
    lines = [
        f"### {cov['symbol']} coverage",
        "",
        f"- range: {cov['first_session']} -> {cov['last_session']}",
        f"- expected calendar sessions: {cov['expected_sessions']}",
        f"- sessions with all requested kinds non-empty: {cov['present_nonempty']}",
        "",
        "| kind | partitions present | non-empty | missing |",
        "|---|---|---|---|",
    ]
    for k, d in cov["per_kind"].items():
        lines.append(
            f"| {k} | {d['present']} | {d['nonempty']} | {len(d['missing_sessions'])} |"
        )
    lines.append("")
    for k, d in cov["per_kind"].items():
        miss = d["missing_sessions"]
        if not miss:
            continue
        head = ", ".join(miss[:6])
        tail = ", ".join(miss[-6:])
        if len(miss) <= 12:
            shown = ", ".join(miss)
        else:
            shown = f"{head} ... {tail}"
        lines.append(f"- **{k}** missing {len(miss)} sessions: {shown}")
    lines.append("")
    return lines


def _worst_gaps(df: pl.DataFrame, col: str, n: int = 10) -> list[str]:
    if df.height == 0 or col not in df.columns:
        return []
    sub = (
        df.filter(pl.col(col).is_not_null())
        .sort(col, descending=True)
        .head(n)
        .select("symbol", "session", col)
    )
    lines = [f"| symbol | session | {col} |", "|---|---|---|"]
    for r in sub.iter_rows(named=True):
        lines.append(f"| {r['symbol']} | {r['session']} | {r[col]:.1f} |")
    lines.append("")
    return lines


def _crossed_outliers(df: pl.DataFrame, n: int = 10) -> list[str]:
    if df.height == 0:
        return []
    sub = (
        df.filter(pl.col("crossed_or_locked_frac").fill_null(0.0) > 0)
        .sort("crossed_or_locked_frac", descending=True)
        .head(n)
        .select("symbol", "session", "crossed_or_locked_frac", "rows_quotes")
    )
    if sub.height == 0:
        return ["No crossed/locked quotes observed.", ""]
    lines = ["| symbol | session | crossed_or_locked_frac | rows_quotes |", "|---|---|---|---|"]
    for r in sub.iter_rows(named=True):
        lines.append(
            f"| {r['symbol']} | {r['session']} | {r['crossed_or_locked_frac']:.5f} | {r['rows_quotes']} |"
        )
    lines.append("")
    return lines


@click.command()
@click.option("--symbols", default="NVDA,TSLA", help="Comma-separated symbols.")
@click.option("--kinds", default="trades,quotes", help="Comma-separated: trades,quotes.")
@click.option("--bars", "do_bars", is_flag=True, help="Also audit bars1m coverage.")
@click.option("--feed", default="sip", help="Lake feed (default sip).")
@click.option("--out", default="auto", help="Output dir, or 'auto' for a timestamped one.")
def main(symbols: str, kinds: str, do_bars: bool, feed: str, out: str) -> None:
    settings = get_settings()
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    kind_tuple = tuple(k.strip() for k in kinds.split(",") if k.strip())

    if out == "auto":
        out_dir = PROJECT_ROOT / "research" / "experiments" / f"qa_{qa._now_utc_stamp()}"
    else:
        out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_audit: list[pl.DataFrame] = []
    coverages: list[dict[str, Any]] = []
    bars_reports: list[dict[str, Any]] = []

    for sym in sym_list:
        log.info("audit_symbol_start", symbol=sym, kinds=kind_tuple)
        df, cov = qa.audit_symbol(settings, sym, kinds=kind_tuple, feed=feed)
        all_audit.append(df)
        coverages.append(cov)
        log.info(
            "audit_symbol_done",
            symbol=sym,
            sessions=df.height,
            expected=cov["expected_sessions"],
        )
        if do_bars:
            bars_reports.append(qa.audit_bars(settings, sym, feed=feed))

    stats = (
        pl.concat(all_audit, how="vertical_relaxed")
        if all_audit
        else pl.DataFrame(schema=qa._AUDIT_SCHEMA)
    )
    stats_path = out_dir / "stats.parquet"
    # notes is a List[str] column — parquet handles it fine.
    stats.write_parquet(stats_path)

    # ---- build report.md ----
    md: list[str] = [
        f"# Data-quality report — {qa._now_utc_stamp()}",
        "",
        f"Symbols: {', '.join(sym_list)}  |  kinds: {', '.join(kind_tuple)}  |  feed: {feed}",
        f"Read roots: {', '.join(str(r) for r in settings.read_roots)}",
        f"Total audited (symbol, session) rows: {stats.height}",
        "",
        "## Coverage",
        "",
    ]
    for cov in coverages:
        md += _coverage_table(cov)

    md += ["## Worst 10 sessions by max intra-RTH gap", ""]
    md += ["**trades**", ""]
    md += _worst_gaps(stats, "max_gap_s_trades") or ["(no trade gaps)", ""]
    md += ["**quotes**", ""]
    md += _worst_gaps(stats, "max_gap_s_quotes") or ["(no quote gaps)", ""]

    md += ["## Crossed / locked quote outliers", ""]
    md += _crossed_outliers(stats)

    if do_bars:
        md += ["## bars1m coverage", ""]
        for br in bars_reports:
            md.append(f"### {br['symbol']} bars1m")
            md.append("")
            md.append(
                f"- months: {br['first_month']} -> {br['last_month']}  "
                f"| missing months: {len(br['months_missing'])}  "
                f"| suspicious (<{qa.MIN_RTH_BARS} RTH bars) sessions: {len(br['suspicious_sessions'])}"
            )
            if br["months_missing"]:
                md.append(f"- missing months: {', '.join(br['months_missing'])}")
            susp = br["suspicious_sessions"]
            if susp:
                shown = ", ".join(f"{s['session']}({s['rth_bars']})" for s in susp[:12])
                md.append(f"- thin sessions (first 12): {shown}")
            md.append("")

    report_path = out_dir / "report.md"
    report_path.write_text("\n".join(md), encoding="utf-8")

    # ---- stdout headline ----
    click.echo(f"report: {report_path}")
    click.echo(f"stats:  {stats_path}")
    for cov in coverages:
        tq = cov["per_kind"].get("quotes", {})
        tt = cov["per_kind"].get("trades", {})
        click.echo(
            f"{cov['symbol']}: expected={cov['expected_sessions']} "
            f"present_all_nonempty={cov['present_nonempty']} "
            f"trades_missing={len(tt.get('missing_sessions', []))} "
            f"quotes_missing={len(tq.get('missing_sessions', []))}"
        )
        for k, d in cov["per_kind"].items():
            miss = d["missing_sessions"]
            if miss:
                edge = ", ".join(miss[:3]) + (
                    " ... " + ", ".join(miss[-3:]) if len(miss) > 6 else ""
                )
                click.echo(f"    {k} missing {len(miss)}: {edge}")
    if stats.height:
        for col in ("max_gap_s_trades", "max_gap_s_quotes"):
            v = stats.select(pl.col(col).max()).item()
            click.echo(f"max {col}: {_fmt_opt(v, '.1f')}s")
        xr = stats.filter(pl.col("crossed_or_locked_frac").fill_null(0.0) > 0).height
        click.echo(f"sessions with any crossed/locked quotes: {xr}")


if __name__ == "__main__":
    main()
