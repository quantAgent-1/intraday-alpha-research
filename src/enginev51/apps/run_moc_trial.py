"""M6 MOC-imbalance trial runner — NOII signal -> auction event -> net-bps evidence.

Drives the registered ``moc_imbalance_v1`` family (M3_REGISTRATION.md M6 section)
over a date range of NYSE sessions, per symbol:

    load_noii_session -> signal_at(15:50:10 ET) -> (if |norm_imb| >= threshold)
      -> find_closing_cross(raw tape) -> replay_moc_event -> net bps

and accumulates a per-event results frame + a ``report.md`` under
``research/experiments/<trial_id>/``. Pooled and per-symbol net-bps CIs are
day-clustered (``stress.clustered_mean_ci``); a 10-event stratified ground-truth
table verifies each sampled fill against the raw tape (entry NBBO context + cross
print vs official bar close, PROTOCOL v6.1); skipped sessions (no cross print on
legacy condition-stripped days) are counted, not hidden.

Hard PIT/holdout guard: the run refuses any ``--end`` on/after
``protocol.HOLDOUT_START`` and hard-filters every session strictly before it.
This app writes NO ledger row — the orchestrator owns verdicts.

    uv run python -m enginev51.apps.run_moc_trial --trial-id M6-moc-imbalance-v1-t05 \
        --symbols NVDA,TSLA,AMD,MU,GOOGL --start 2024-01-02 --end 2026-05-31 \
        --threshold 0.0005 --no-persistence --seed 7
"""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import click
import polars as pl
import structlog

from enginev51.backtest import stress
from enginev51.backtest.auction_replay import (
    adv20_dollars,
    cross_price_for,
    load_raw_trades,
    official_daily_closes,
    replay_moc_event,
    tape_from_bbo,
)
from enginev51.backtest.fills import prevailing_idx
from enginev51.backtest.tape import load_session_tape
from enginev51.config import Settings, get_settings
from enginev51.data import calendar, store
from enginev51.data.bbo1s import load_bbo_session
from enginev51.data.noii import ET, et_ns, load_noii_session, signal_at
from enginev51.protocol import (
    HOLDOUT_START,
    experiments_dir,
    refuse_end_on_or_after_holdout,
    split_of,
)

log = structlog.get_logger(__name__)

SYMBOLS_DEFAULT = "NVDA,TSLA,AMD,MU,GOOGL"

MOC_RESULTS_SCHEMA: dict[str, pl.DataType] = {
    "session": pl.Utf8,
    "symbol": pl.Utf8,
    "side": pl.Int64,
    "norm_imb": pl.Float64,
    "adv20_dollars": pl.Float64,
    "entry_ts": pl.Int64,
    "entry_px": pl.Float64,
    "entry_bid": pl.Float64,
    "entry_ask": pl.Float64,
    "exit_ts": pl.Int64,
    "exit_px": pl.Float64,
    "exit_reason": pl.Utf8,
    "cross_px": pl.Float64,
    "cross_size": pl.Float64,
    "bar_close": pl.Float64,
    "net_bps": pl.Float64,
    "hold_s": pl.Float64,
}


# --------------------------------------------------------------------------- guard


def assert_before_holdout(end: date) -> None:
    """Refuse any run reaching the sealed holdout boundary (PROTOCOL v6 §1).

    Raises SealViolation (never a bare assert: ``python -O`` strips those)."""
    refuse_end_on_or_after_holdout(end)


# --------------------------------------------------------------------------- helpers


def _session_closes(settings: Settings, symbol: str) -> dict[str, float]:
    """Per-session OFFICIAL daily close (bars1d), falling back to the last RTH
    1m-bar close only where the daily file lacks the session.

    ``bar_close`` feeds ``cross_vs_close_bps``, the "cross print is sane against
    the official close" validation — so it must BE the official close. The last
    1-minute bar (the old source, code review 2026-07-17 F6) is the 15:59 bar,
    not the closing cross, and validated the cross against the wrong reference.
    """
    feed = settings.data_feed_type
    out: dict[str, float] = {}
    bars = store.load_bars(settings.read_roots, feed, symbol)
    if bars.height > 0:
        per = (
            bars.with_columns(
                pl.from_epoch(pl.col("ts"), time_unit="ns")
                .dt.convert_time_zone(str(ET))
                .dt.date()
                .cast(pl.Utf8)
                .alias("session")
            )
            .sort("ts")
            .group_by("session")
            .agg(pl.col("close").last().alias("close"))
        )
        out = dict(zip(per["session"].to_list(), per["close"].to_list(), strict=True))
    out.update(official_daily_closes(symbol))  # official close wins where present
    return out


def _prevailing_nbbo(tape, ts: int) -> tuple[float | None, float | None]:
    """Prevailing (bid, ask) at ``ts`` from a SessionTape; (None, None) if none."""
    i = prevailing_idx(tape.q_ts, ts)
    if i < 0:
        return None, None
    return float(tape.q_bid[i]), float(tape.q_ask[i])


# --------------------------------------------------------------------------- run


def run_moc_trial(
    settings: Settings,
    *,
    symbols: list[str],
    start: date,
    end: date,
    threshold: float,
    persistence: bool,
    seed: int,
    noii_dir: str | Path | None = None,
    entry_source: str = "tick",
    bbo_dir: str | Path | None = None,
    lat_lo_s: float = 5.0,
    lat_hi_s: float = 25.0,
) -> tuple[pl.DataFrame, dict]:
    """Execute the M6 pipeline over [start, end] sessions; return (results, stats).

    One event per (symbol, session) whose 15:50:10-ET NOII signal is active
    (``|norm_imb| >= threshold`` and a definite side). Sessions whose cross print
    is absent (legacy condition-stripped tape) are SKIPPED and counted.

    ``entry_source`` selects the entry-fill quote tape: ``"tick"`` (the tick
    quote/trade SessionTape) or ``"bbo1s"`` (the 1-second BBO via
    ``load_bbo_session`` -> ``tape_from_bbo``; registered data-source extension,
    ledger M6 2026-07-16). Everything downstream is identical — the entry is a
    taker cross of the prevailing quote either way. In bbo1s mode a session is
    counted ``skipped_no_bbo`` when the BBO partition is absent but a tick tape
    exists, and ``skipped_no_tape`` only when BOTH sources are absent.
    """
    assert_before_holdout(end)
    if entry_source not in ("tick", "bbo1s"):
        raise ValueError(f"entry_source must be 'tick' or 'bbo1s', got {entry_source!r}")
    symbols = [s.strip().upper() for s in symbols]

    counts = {
        "no_noii_partition": 0,
        "no_noii_msgs": 0,
        "no_adv": 0,
        "no_signal": 0,
        "inactive": 0,
        "events_fired": 0,
        "skipped_no_cross": 0,
        "skipped_no_bbo": 0,
        "skipped_no_tape": 0,
        "void": 0,
        "persistence_exits": 0,
    }
    per_symbol_skipped_cross: dict[str, int] = dict.fromkeys(symbols, 0)

    closes_cache: dict[str, dict[str, float]] = {}
    rows: list[dict] = []

    sessions = [d for d in calendar.trading_days(start, end) if d < HOLDOUT_START]
    for sd in sessions:
        session_iso = sd.isoformat()
        for sym in symbols:
            noii = load_noii_session(sym, session_iso, out_dir=noii_dir)
            if noii is None:
                counts["no_noii_partition"] += 1
                continue
            if noii.height == 0:
                counts["no_noii_msgs"] += 1
                continue

            adv = adv20_dollars(settings, sym, session_iso)
            if adv is None:
                counts["no_adv"] += 1
                continue

            signal_ts = et_ns(session_iso, 15, 50, 10)
            sig = signal_at(noii, signal_ts, adv)
            if sig is None:
                counts["no_signal"] += 1
                continue
            side = int(sig["side"])
            norm_imb = float(sig["norm_imb"])
            if side == 0 or abs(norm_imb) < threshold:
                counts["inactive"] += 1
                continue

            counts["events_fired"] += 1

            cross = cross_price_for(sym, session_iso, load_raw_trades(settings, sym, session_iso))
            if cross is None:
                counts["skipped_no_cross"] += 1
                per_symbol_skipped_cross[sym] += 1
                continue

            if entry_source == "bbo1s":
                bbo = load_bbo_session(sym, session_iso, out_dir=bbo_dir)
                tape = tape_from_bbo(sym, bbo) if bbo is not None and bbo.height else None
                if tape is None:
                    # skipped_no_tape only when BOTH the BBO and the tick tape are
                    # absent; a present tick tape means this is a bbo-coverage gap.
                    if load_session_tape(settings, sym, session_iso) is None:
                        counts["skipped_no_tape"] += 1
                    else:
                        counts["skipped_no_bbo"] += 1
                    continue
            else:
                tape = load_session_tape(settings, sym, session_iso)
                if tape is None:
                    counts["skipped_no_tape"] += 1
                    continue

            persistence_exit_ts = None
            if persistence:
                p_ts = et_ns(session_iso, 15, 55, 0)
                psig = signal_at(noii, p_ts, adv)
                if psig is not None and psig["side"] != 0 and psig["side"] != side:
                    persistence_exit_ts = p_ts

            plan_id = f"{sym}-{session_iso}-moc"
            res = replay_moc_event(
                tape, signal_ts, side, cross, seed, plan_id,
                symbol=sym, persistence_exit_ts=persistence_exit_ts,
                lat_lo_s=lat_lo_s, lat_hi_s=lat_hi_s,
                slip_bps=0.5, sec_taf_sell_bps=0.3,
            )
            if res.status != "ok":
                counts["void"] += 1
                continue
            if res.exit_reason == "persistence":
                counts["persistence_exits"] += 1

            if sym not in closes_cache:
                closes_cache[sym] = _session_closes(settings, sym)
            bar_close = closes_cache[sym].get(session_iso)
            bid, ask = _prevailing_nbbo(tape, signal_ts)

            rows.append(
                {
                    "session": session_iso,
                    "symbol": sym,
                    "side": side,
                    "norm_imb": norm_imb,
                    "adv20_dollars": adv,
                    "entry_ts": res.entry_ts,
                    "entry_px": res.entry_px,
                    "entry_bid": bid,
                    "entry_ask": ask,
                    "exit_ts": res.exit_ts,
                    "exit_px": res.exit_px,
                    "exit_reason": res.exit_reason,
                    "cross_px": float(cross[1]),
                    "cross_size": float(cross[2]),
                    "bar_close": bar_close,
                    "net_bps": res.net_bps,
                    "hold_s": res.hold_s,
                }
            )

    df = (
        pl.DataFrame(rows, schema=MOC_RESULTS_SCHEMA, orient="row")
        if rows
        else pl.DataFrame(schema=MOC_RESULTS_SCHEMA)
    )
    stats = {
        "symbols": symbols,
        "threshold": threshold,
        "persistence": persistence,
        "seed": seed,
        "entry_source": entry_source,
        "sessions_in_range": len(sessions),
        "counts": counts,
        "per_symbol_skipped_cross": per_symbol_skipped_cross,
    }
    return df, stats


# --------------------------------------------------------------------------- report


def _ascii(df: pl.DataFrame) -> str:
    with pl.Config(
        tbl_formatting="ASCII_MARKDOWN",
        tbl_hide_dataframe_shape=True,
        tbl_hide_column_data_types=True,
        tbl_rows=200,
        tbl_cols=-1,
        tbl_width_chars=240,
    ):
        return str(df)


def _ci(df: pl.DataFrame) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n_events, n_sessions) day-clustered over net_bps."""
    if df.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    m, lo, hi = stress.clustered_mean_ci(
        df["net_bps"].to_numpy(), df["session"].to_numpy()
    )
    return m, lo, hi, df.height, df["session"].n_unique()


def _fmt_ci(t: tuple[float, float, float, int, int]) -> str:
    m, lo, hi, n, ns = t
    if n == 0:
        return "n=0"
    return f"mean={m:.3f}  95%CI=[{lo:.3f}, {hi:.3f}]  n={n}  sessions={ns}"


def _per_symbol_ci_table(df: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []
    syms = sorted(df["symbol"].unique().to_list()) if df.height else []
    for sym in [*syms, "__POOLED__"]:
        sub = df if sym == "__POOLED__" else df.filter(pl.col("symbol") == sym)
        m, lo, hi, n, ns = _ci(sub)
        rows.append(
            {
                "symbol": "POOLED" if sym == "__POOLED__" else sym,
                "n_events": n,
                "n_sessions": ns,
                "net_bps_mean": round(m, 3) if n else None,
                "ci_lo": round(lo, 3) if n else None,
                "ci_hi": round(hi, 3) if n else None,
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            "symbol": pl.Utf8,
            "n_events": pl.Int64,
            "n_sessions": pl.Int64,
            "net_bps_mean": pl.Float64,
            "ci_lo": pl.Float64,
            "ci_hi": pl.Float64,
        },
        orient="row",
    )


def _split_ci_table(df: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []
    if df.height:
        df = df.with_columns(
            pl.col("session").map_elements(split_of, return_dtype=pl.Utf8).alias("split")
        )
    for split in ("train", "validate"):
        sub = df.filter(pl.col("split") == split) if df.height else df
        m, lo, hi, n, ns = _ci(sub)
        rows.append(
            {
                "split": split,
                "n_events": n,
                "n_sessions": ns,
                "net_bps_mean": round(m, 3) if n else None,
                "ci_lo": round(lo, 3) if n else None,
                "ci_hi": round(hi, 3) if n else None,
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            "split": pl.Utf8,
            "n_events": pl.Int64,
            "n_sessions": pl.Int64,
            "net_bps_mean": pl.Float64,
            "ci_lo": pl.Float64,
            "ci_hi": pl.Float64,
        },
        orient="row",
    )


def _by_year_ci_table(df: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []
    years = (
        sorted({s[:4] for s in df["session"].to_list()}) if df.height else []
    )
    for yr in years:
        sub = df.filter(pl.col("session").str.starts_with(yr))
        m, lo, hi, n, ns = _ci(sub)
        rows.append(
            {
                "year": yr,
                "n_events": n,
                "n_sessions": ns,
                "net_bps_mean": round(m, 3) if n else None,
                "ci_lo": round(lo, 3) if n else None,
                "ci_hi": round(hi, 3) if n else None,
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            "year": pl.Utf8,
            "n_events": pl.Int64,
            "n_sessions": pl.Int64,
            "net_bps_mean": pl.Float64,
            "ci_lo": pl.Float64,
            "ci_hi": pl.Float64,
        },
        orient="row",
    )


def _stratified_ground_truth(df: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """Sample <=k stratified events (biggest winners/losers, largest |imbalance|)
    and lay out the tape ground-truth: entry NBBO context + cross vs bar close.

    PROTOCOL v6.1 fill ground-truthing: every sampled event's entry price must sit
    inside/at the prevailing NBBO, and the cross print must be sane against the
    session's official bar close (``cross_vs_close_bps`` near 0 for a real cross).
    """
    if df.height == 0:
        return pl.DataFrame(
            schema={
                "session": pl.Utf8, "symbol": pl.Utf8, "side": pl.Int64,
                "norm_imb": pl.Float64, "entry_bid": pl.Float64, "entry_ask": pl.Float64,
                "entry_px": pl.Float64, "exit_reason": pl.Utf8, "cross_px": pl.Float64,
                "bar_close": pl.Float64, "cross_vs_close_bps": pl.Float64,
                "entry_in_nbbo": pl.Boolean, "net_bps": pl.Float64,
            }
        )
    d = df.with_columns(pl.arange(0, pl.len()).alias("_idx"))
    winners = d.sort("net_bps", descending=True).head(3)["_idx"].to_list()
    losers = d.sort("net_bps", descending=False).head(3)["_idx"].to_list()
    big_imb = d.sort(pl.col("norm_imb").abs(), descending=True).head(4)["_idx"].to_list()
    picked: list[int] = []
    for i in [*winners, *losers, *big_imb]:
        if i not in picked:
            picked.append(i)
        if len(picked) >= k:
            break
    sub = d.filter(pl.col("_idx").is_in(picked)).drop("_idx")
    return sub.with_columns(
        (
            pl.when(pl.col("bar_close").is_not_null() & (pl.col("bar_close") > 0))
            .then((pl.col("cross_px") - pl.col("bar_close")) / pl.col("bar_close") * 1e4)
            .otherwise(None)
            .alias("cross_vs_close_bps")
        ),
        (
            pl.when(pl.col("entry_bid").is_not_null() & pl.col("entry_ask").is_not_null())
            .then(
                (pl.col("entry_px") >= pl.col("entry_bid") * 0.999)
                & (pl.col("entry_px") <= pl.col("entry_ask") * 1.001)
            )
            .otherwise(None)
            .alias("entry_in_nbbo")
        ),
    ).select(
        "session", "symbol", "side", "norm_imb", "entry_bid", "entry_ask", "entry_px",
        "exit_reason", "cross_px", "bar_close", "cross_vs_close_bps", "entry_in_nbbo",
        "net_bps",
    )


def _promotion_diagnostic(df: pl.DataFrame) -> dict:
    """Registered M6 promotion bar (diagnostic echo, NOT a gate here):
    pooled day-clustered CI lower > 0 AND >=100 events AND positive point estimate
    in >=3 of 5 symbols."""
    m, lo, hi, n, ns = _ci(df)
    sym_pos = 0
    syms = sorted(df["symbol"].unique().to_list()) if df.height else []
    per_sym: dict[str, float | None] = {}
    for sym in syms:
        sub = df.filter(pl.col("symbol") == sym)
        pe = float(sub["net_bps"].mean()) if sub.height else float("nan")
        per_sym[sym] = round(pe, 3) if sub.height else None
        if sub.height and pe > 0:
            sym_pos += 1
    return {
        "pooled_mean_net_bps": round(m, 3) if n else None,
        "pooled_ci_lo": round(lo, 3) if n else None,
        "pooled_ci_hi": round(hi, 3) if n else None,
        "n_events": n,
        "n_sessions": ns,
        "symbols_positive_point_estimate": sym_pos,
        "per_symbol_point_estimate": per_sym,
        "meets_pooled_lo_gt_0": bool(n and lo > 0),
        "meets_n_ge_100": bool(n >= 100),
        "meets_ge_3_of_5_symbols_positive": bool(sym_pos >= 3),
    }


def build_report_md(df: pl.DataFrame, trial_id: str, stats: dict) -> str:
    """Assemble the full report.md string from a per-event results frame (pure)."""
    counts = stats["counts"]
    md: list[str] = [
        f"# M6 MOC-imbalance trial report — {trial_id}",
        "",
        f"Symbols: {', '.join(stats['symbols'])}",
        f"Threshold (|norm_imb| of ADV$): {stats['threshold']}  "
        f"({stats['threshold'] * 100:.3f}% of ADV$)",
        f"Persistence prong: {'ON' if stats['persistence'] else 'OFF'}    seed={stats['seed']}",
        f"Entry-fill source: {stats.get('entry_source', 'tick')}",
        f"Sessions in range (< holdout): {stats['sessions_in_range']}",
        f"Events evaluated (rows): {df.height}",
        f"Splits present: {sorted(set(split_of(s) for s in df['session'].unique())) if df.height else []}",
        "",
        "NOTE: sessions whose official closing-cross print is absent (legacy "
        "condition-stripped NVDA/TSLA tick exports) are SKIPPED and counted below "
        "under 'skipped_no_cross' — they resolve once the conditioned re-download "
        "completes. Not a result, a coverage gap.",
        "",
        "## 1. Event funnel / skipped-session counts",
        "",
        "```",
        json.dumps(counts, indent=2, default=str),
        "```",
        "",
        "Per-symbol skipped (no cross print):",
        "",
        "```",
        json.dumps(stats["per_symbol_skipped_cross"], indent=2, default=str),
        "```",
        "",
        "## 2. Pooled + per-symbol net_bps day-clustered CIs (stress.clustered_mean_ci)",
        "",
        _ascii(_per_symbol_ci_table(df)),
        "",
        "## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)",
        "",
        _ascii(_split_ci_table(df)),
        "",
        "## 3b. By-year net_bps day-clustered CIs",
        "",
        _ascii(_by_year_ci_table(df)),
        "",
        "## 4. Cross-print ground-truth table (10 stratified events, PROTOCOL v6.1)",
        "",
        "entry_in_nbbo: entry fill sits within the prevailing NBBO at the signal "
        "instant. cross_vs_close_bps: official cross print vs the session's last "
        "1m-bar close (should be ~0 for a real cross).",
        "",
        _ascii(_stratified_ground_truth(df)),
        "",
        "## 5. Registered promotion bar (diagnostic echo, not a gate in this app)",
        "",
        "```",
        json.dumps(_promotion_diagnostic(df), indent=2, default=str),
        "```",
        "",
        "## 6. Exit-reason distribution",
        "",
    ]
    if df.height:
        er = df.group_by("exit_reason").agg(pl.len().alias("count")).sort("count", descending=True)
        md.append(_ascii(er))
    else:
        md.append("(no events)")
    md.append("")
    return "\n".join(md)


def write_outputs(df: pl.DataFrame, out_dir: Path, trial_id: str, stats: dict) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.parquet"
    report_path = out_dir / "report.md"
    df.write_parquet(results_path)
    report_path.write_text(build_report_md(df, trial_id, stats), encoding="utf-8")
    return results_path, report_path


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--trial-id", required=True, help="Experiment id -> research/experiments/<id>/.")
@click.option("--symbols", default=SYMBOLS_DEFAULT, help="Comma-separated Nasdaq universe.")
@click.option("--start", required=True, help="First session (ISO date), inclusive.")
@click.option("--end", required=True, help="Last session (ISO date), inclusive; < holdout.")
@click.option(
    "--threshold",
    type=click.Choice(["0.0005", "0.001"]),
    required=True,
    help="Registered |norm_imb| cell: 0.0005 (0.05% ADV$) or 0.001 (0.10% ADV$).",
)
@click.option("--persistence/--no-persistence", default=False,
              help="15:55 NOII side-flip -> immediate market exit (registered prong on/off).")
@click.option("--seed", default=7, type=int, help="Latency-draw seed.")
@click.option("--noii-dir", default=None, help="NOII lake root (default data/raw/noii).")
@click.option(
    "--entry-source",
    type=click.Choice(["tick", "bbo1s"]),
    default="tick",
    help="Entry-fill quote tape: tick SessionTape or 1-second BBO (ledger M6).",
)
@click.option("--bbo-dir", default=None, help="BBO-1s lake root (default data/raw/bbo1s).")
def main(
    trial_id: str,
    symbols: str,
    start: str,
    end: str,
    threshold: str,
    persistence: bool,
    seed: int,
    noii_dir: str | None,
    entry_source: str,
    bbo_dir: str | None,
) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    settings = get_settings()
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    assert_before_holdout(end_d)

    t0 = time.time()
    df, stats = run_moc_trial(
        settings,
        symbols=sym_list,
        start=start_d,
        end=end_d,
        threshold=float(threshold),
        persistence=persistence,
        seed=seed,
        noii_dir=noii_dir,
        entry_source=entry_source,
        bbo_dir=bbo_dir,
    )
    wall_s = time.time() - t0

    out_dir = experiments_dir() / trial_id
    results_path, report_path = write_outputs(df, out_dir, trial_id, stats)

    click.echo(
        f"trial: {trial_id}  symbols={','.join(sym_list)}  {start}..{end}  "
        f"threshold={threshold}  persistence={persistence}  entry_source={entry_source}"
    )
    click.echo(f"sessions in range (< holdout): {stats['sessions_in_range']}")
    click.echo(f"event funnel: {json.dumps(stats['counts'], default=str)}")
    click.echo("")
    click.echo(_ascii(_per_symbol_ci_table(df)))
    click.echo("")
    click.echo(f"POOLED net_bps: {_fmt_ci(_ci(df))}")
    click.echo(f"events: {df.height}")
    click.echo(f"results: {results_path}")
    click.echo(f"report:  {report_path}")
    click.echo(f"wall: {wall_s:.1f}s")


if __name__ == "__main__":
    main()
