"""M8 meta-labeling runner (``moc_meta_v1``) — a LightGBM BINARY reliability model
on the classical |basis|>=10 rule, walk-forward OOS only.

Pipeline (M3_REGISTRATION.md "M8 meta-labeling on the classical basis rule"):

    M6-FINAL events.parquet  (all-events basis universe, already fill-verified)
      -> candidates = |basis_bps| >= 10 (the winning classical cell)
      -> meta-label y = (net_bps > 0)
      -> LightGBM binary classifier on the registered reliability features,
         expanding calendar walk-forward (>=2y train, 6-mo blocks, 1-session
         embargo) IDENTICAL to models/moc_gbm folds
      -> OOS P(win) for every candidate beyond the initial-train span
      -> gates q in {0.50, 0.55, 0.60}: TAKE iff P(win) >= q
      -> report.md: on the SAME OOS span, ungated classical baseline vs each gated
         stream — n_taken, hit_rate, net_bps mean + day-clustered CI, net_bps std,
         Sharpe, per-symbol + per-year tables, P(win)-proportional sizing overlay
         ($ view, report-only), feature importances, calibration table, and 10
         stratified gated events ground-truthed (join-correctness confirmation).

Writes NO ledger row and NO pass/fail verdict (the orchestrator owns the verdict).
Holdout stays sealed: the events are already < 2026-06-01 and this app asserts it.

    uv run python -m enginev51.apps.run_meta_trial --trial-id M8-meta-v1 \
        --events research/experiments/M6-FINAL-basis/events.parquet --seed 7
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import click
import numpy as np
import polars as pl
import structlog

from enginev51.backtest import stress
from enginev51.models.moc_meta import (
    CANDIDATE_BASIS_BPS,
    FEATURE_COLS,
    GATES,
    NET_COL,
    PRED_COL,
    build_meta_frame,
    calibration_table,
    gate,
    run_walk_forward,
)
from enginev51.protocol import HOLDOUT_START, SealViolation, experiments_dir, split_of

log = structlog.get_logger(__name__)

DEFAULT_EVENTS = "research/experiments/M6-FINAL-basis/events.parquet"
BOOK_NOTIONAL = 10_000.0  # research book: $10k fixed notional per plan (PROTOCOL v6 §3)


# --------------------------------------------------------------------------- report helpers


def _ascii(df: pl.DataFrame) -> str:
    with pl.Config(
        tbl_formatting="ASCII_MARKDOWN",
        tbl_hide_dataframe_shape=True,
        tbl_hide_column_data_types=True,
        tbl_rows=200,
        tbl_cols=-1,
        tbl_width_chars=260,
    ):
        return str(df)


def _ci(df: pl.DataFrame) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n_events, n_sessions) day-clustered over net_bps."""
    if df.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    m, lo, hi = stress.clustered_mean_ci(
        df[NET_COL].to_numpy(), df["session"].to_numpy()
    )
    return m, lo, hi, df.height, df["session"].n_unique()


def _year_col(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.col("session").str.slice(0, 4).alias("year"))


def _hit_rate(df: pl.DataFrame) -> float:
    if df.height == 0:
        return float("nan")
    return float((df[NET_COL] > 0.0).cast(pl.Float64).mean())


def _sharpe(df: pl.DataFrame) -> tuple[float, float]:
    """(std, Sharpe = mean/std) of per-trade net_bps (sample std, ddof=1)."""
    if df.height < 2:
        return float("nan"), float("nan")
    net = df[NET_COL].to_numpy()
    sd = float(np.std(net, ddof=1))
    mean = float(np.mean(net))
    return sd, (mean / sd if sd > 0 else float("nan"))


def _stream_metrics(label: str, df: pl.DataFrame) -> dict:
    m, lo, hi, n, ns = _ci(df)
    sd, sharpe = _sharpe(df)
    return {
        "stream": label,
        "n_taken": n,
        "n_sessions": ns,
        "hit_rate": round(_hit_rate(df), 4) if n else None,
        "net_bps_mean": round(m, 3) if n else None,
        "ci_lo": round(lo, 3) if n else None,
        "ci_hi": round(hi, 3) if n else None,
        "net_bps_std": round(sd, 3) if n >= 2 else None,
        "sharpe": round(sharpe, 4) if n >= 2 else None,
    }


def comparison_table(streams: dict[str, pl.DataFrame]) -> pl.DataFrame:
    rows = [_stream_metrics(label, df) for label, df in streams.items()]
    return pl.DataFrame(
        rows,
        schema={
            "stream": pl.Utf8, "n_taken": pl.Int64, "n_sessions": pl.Int64,
            "hit_rate": pl.Float64, "net_bps_mean": pl.Float64,
            "ci_lo": pl.Float64, "ci_hi": pl.Float64, "net_bps_std": pl.Float64,
            "sharpe": pl.Float64,
        },
        orient="row",
    )


def _compare_by_key(streams: dict[str, pl.DataFrame], key: str) -> pl.DataFrame:
    """Per-key (symbol / year) n + mean net_bps for every stream, side by side."""
    present = [df for df in streams.values() if df.height]
    keyvals: set = set()
    for df in present:
        keyvals |= set(df[key].unique().to_list())
    rows: list[dict] = []
    for kv in sorted(keyvals):
        row: dict = {key: str(kv)}
        for label, df in streams.items():
            sub = df.filter(pl.col(key) == kv)
            row[f"{label}|n"] = sub.height
            row[f"{label}|mean"] = (
                round(float(sub[NET_COL].mean()), 2) if sub.height else None
            )
        rows.append(row)
    return pl.DataFrame(rows, orient="row") if rows else pl.DataFrame({key: []})


def sizing_overlay(streams: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """REPORT-ONLY P(win)-proportional sizing $ view (PROTOCOL v6 §3 — never a gate
    or objective). Two sizings per stream on the $10k research book:

      * equal:  every taken plan gets $10k notional;
      * p_win:  notional_i = $10k * P(win)_i / mean(P(win)) so the AVERAGE notional
                stays $10k (a pure reallocation toward higher-confidence plans).

    ``pnl_$`` = sum(notional_i * net_bps_i / 1e4); ``bps`` = notional-weighted mean
    net_bps. The p_win column shows whether conviction-sizing the SAME taken stream
    improves the dollar outcome — diagnostic only.
    """
    rows: list[dict] = []
    for label, df in streams.items():
        if df.height == 0:
            rows.append({"stream": label, "n": 0, "equal_pnl_$": None,
                         "pwin_pnl_$": None, "equal_bps": None, "pwin_bps": None})
            continue
        net = df[NET_COL].to_numpy()
        pw = df[PRED_COL].to_numpy()
        equal_notional = np.full(net.shape, BOOK_NOTIONAL)
        equal_pnl = float(np.sum(equal_notional * net / 1e4))
        mean_pw = float(np.mean(pw))
        pwin_notional = BOOK_NOTIONAL * pw / mean_pw if mean_pw > 0 else equal_notional
        pwin_pnl = float(np.sum(pwin_notional * net / 1e4))
        rows.append({
            "stream": label,
            "n": df.height,
            "equal_pnl_$": round(equal_pnl, 2),
            "pwin_pnl_$": round(pwin_pnl, 2),
            "equal_bps": round(float(np.mean(net)), 3),
            "pwin_bps": round(float(np.sum(pwin_notional * net / 1e4)
                                   / np.sum(pwin_notional) * 1e4), 3),
        })
    return pl.DataFrame(
        rows,
        schema={"stream": pl.Utf8, "n": pl.Int64, "equal_pnl_$": pl.Float64,
                "pwin_pnl_$": pl.Float64, "equal_bps": pl.Float64,
                "pwin_bps": pl.Float64},
        orient="row",
    )


def registered_success_echo(base: pl.DataFrame, streams: dict[str, pl.DataFrame]) -> dict:
    """Diagnostic echo of the registered M8 success criteria (NOT a verdict — the
    orchestrator owns pass/fail). Per gated stream vs the ungated baseline on the
    SAME OOS span: hit-rate improved? net mean CI-lower > classical mean? Sharpe
    improved >=20%? spans >=3 symbols and >=3 years?"""
    b_m, _b_lo, _b_hi, _b_n, _b_ns = _ci(base)
    b_hit = _hit_rate(base)
    _b_sd, b_sharpe = _sharpe(base)
    out: dict = {
        "baseline": {
            "hit_rate": round(b_hit, 4), "net_bps_mean": round(b_m, 3),
            "sharpe": round(b_sharpe, 4),
        },
        "gates": {},
    }
    for label, df in streams.items():
        m, lo, _hi, n, _ns = _ci(df)
        hit = _hit_rate(df)
        _sd, sharpe = _sharpe(df)
        symbols = sorted(df["symbol"].unique().to_list()) if df.height else []
        years = sorted({s[:4] for s in df["session"].to_list()}) if df.height else []
        out["gates"][label] = {
            "n_taken": n,
            "hit_rate": round(hit, 4) if n else None,
            "hit_rate_improved": bool(n and hit > b_hit),
            "net_mean_ci_lo": round(lo, 3) if n else None,
            "ci_lo_gt_classical_mean": bool(n and lo > b_m),
            "sharpe": round(sharpe, 4) if n >= 2 else None,
            "sharpe_improved_ge_20pct": bool(
                n >= 2 and np.isfinite(sharpe) and np.isfinite(b_sharpe)
                and b_sharpe > 0 and sharpe >= 1.2 * b_sharpe
            ),
            "n_symbols": len(symbols),
            "n_years": len(years),
            "spans_ge_3_symbols_and_3_years": bool(len(symbols) >= 3 and len(years) >= 3),
        }
    return out


def _ground_truth(gated: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """10 stratified gated events with the PROTOCOL v6.1 join-correctness columns.

    The economics were fill-verified upstream (M6-FINAL); here we CONFIRM the join
    is correct — every gated row still carries a coherent fill: entry within the
    prevailing NBBO, and the cross print matching the official daily close
    (cross_vs_close_bps ~ 0). Stratified: biggest winners, biggest losers, largest
    |basis|, highest P(win)."""
    schema = {
        "session": pl.Utf8, "symbol": pl.Utf8, "side": pl.Int64,
        "basis_bps": pl.Float64, "p_win": pl.Float64, "entry_mid": pl.Float64,
        "entry_bid": pl.Float64, "entry_ask": pl.Float64, "entry_px": pl.Float64,
        "entry_in_nbbo": pl.Boolean, "cross_px": pl.Float64, "bar_close": pl.Float64,
        "cross_vs_close_bps": pl.Float64, "net_bps": pl.Float64, "y_meta": pl.Int8,
    }
    if gated.height == 0:
        return pl.DataFrame(schema=schema)
    d = gated.with_columns(pl.arange(0, pl.len()).alias("_idx"))
    winners = d.sort(NET_COL, descending=True).head(3)["_idx"].to_list()
    losers = d.sort(NET_COL, descending=False).head(3)["_idx"].to_list()
    big = d.sort(pl.col("basis_bps").abs(), descending=True).head(2)["_idx"].to_list()
    hi_p = d.sort(PRED_COL, descending=True).head(2)["_idx"].to_list()
    picked: list[int] = []
    for i in [*winners, *losers, *big, *hi_p]:
        if i not in picked:
            picked.append(i)
        if len(picked) >= k:
            break
    sub = d.filter(pl.col("_idx").is_in(picked)).drop("_idx")
    return sub.with_columns(
        pl.when(pl.col("entry_bid").is_not_null() & pl.col("entry_ask").is_not_null())
        .then(
            (pl.col("entry_px") >= pl.col("entry_bid") * 0.999)
            & (pl.col("entry_px") <= pl.col("entry_ask") * 1.001)
        )
        .otherwise(None).alias("entry_in_nbbo"),
        pl.when(pl.col("bar_close").is_not_null() & (pl.col("bar_close") > 0))
        .then((pl.col("cross_px") - pl.col("bar_close")) / pl.col("bar_close") * 1e4)
        .otherwise(None).alias("cross_vs_close_bps"),
    ).select(list(schema))


# --------------------------------------------------------------------------- report


def build_streams(oos: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Ordered streams: the ungated classical baseline + each registered gate, all
    on the SAME OOS span (the gates are subsets of the baseline)."""
    streams: dict[str, pl.DataFrame] = {"baseline": oos}
    for q in GATES:
        streams[f"q>={q:.2f}"] = (
            oos.filter(pl.Series(gate(oos[PRED_COL].to_numpy(), q)))
            if oos.height else oos
        )
    return streams


def build_report_md(
    trial_id: str, oos: pl.DataFrame, streams: dict[str, pl.DataFrame],
    importances: pl.DataFrame, folds, meta_counts: dict, seed: int,
) -> str:
    base = streams["baseline"]
    oos_years = sorted({s[:4] for s in oos["session"].to_list()}) if oos.height else []
    oos_symbols = sorted(oos["symbol"].unique().to_list()) if oos.height else []
    fold_meta = [
        {"test_start": f.test_start, "test_end": f.test_end,
         "n_train": len(f.train_sessions), "n_test": len(f.test_sessions)}
        for f in folds
    ]
    gated_streams = {k: v for k, v in streams.items() if k != "baseline"}
    # ground-truth from the tightest gate that still has >=10 taken (else q=0.55).
    gt_stream = streams.get("q>=0.55", base)
    for q in ("q>=0.60", "q>=0.55", "q>=0.50"):
        if q in streams and streams[q].height >= 10:
            gt_stream = streams[q]
            break
    md: list[str] = [
        f"# M8 meta-labeling report — {trial_id}",
        "",
        "Family `moc_meta_v1` (registered 2026-07-17). META-LABELING on the classical "
        f"|basis|>={CANDIDATE_BASIS_BPS:.0f}bps rule at 15:55:10 ET (direction "
        "UNCHANGED = sign(near-mid)). A LightGBM BINARY classifier predicts "
        "P(net_bps>0) per candidate from reliability features; a registered gate "
        "TAKEs iff P(win) >= q, q in {0.50, 0.55, 0.60}. Walk-forward OOS only "
        "(POST-HOLDOUT: the seal was spent by M6-FINAL; forward paper is the sole "
        "clean validation). NO ledger writes; NO pass/fail verdict.",
        "",
        f"seed={seed}    features={len(FEATURE_COLS)} (reliability set, NO `side`)    "
        "model=LightGBM(lgbm.DEFAULT_PARAMS, objective=binary) on y=(net_bps>0)",
        f"OOS span: {oos.height} candidates    symbols {oos_symbols}    years {oos_years}",
        f"Splits present: "
        f"{sorted({split_of(s) for s in oos['session'].unique()}) if oos.height else []}",
        "",
        "## 0. Meta-frame funnel",
        "```",
        json.dumps(meta_counts, indent=2, default=str),
        "```",
        "",
        "## 1. Walk-forward folds (expanding, >=2y train, 6-mo blocks, 1-session embargo)",
        "",
        "Identical fold builder to models/moc_gbm (reused, not re-implemented); a "
        "fold model trains strictly on candidate sessions before its test block "
        "(minus the 1-session embargo).",
        "```",
        json.dumps(fold_meta, indent=2, default=str),
        "```",
        "",
        "## 2. Comparison — baseline (ungated classical) vs each gate, SAME OOS span",
        "",
        "net_bps mean CI is day-clustered (session = cluster unit). Sharpe = per-trade "
        "mean/std. hit_rate = fraction with net_bps > 0.",
        "",
        _ascii(comparison_table(streams)),
        "",
        "## 3. Registered success criteria (diagnostic echo — orchestrator owns the verdict)",
        "",
        "Registered M8 success (honest, post-holdout): hit-rate improves AND (net "
        "mean CI-lower > classical mean OR Sharpe improves >=20%) AND holds across "
        ">=3 symbols and >=3 years.",
        "```",
        json.dumps(registered_success_echo(base, gated_streams), indent=2, default=str),
        "```",
        "",
        "## 4. Per-symbol (n + mean net_bps per stream)",
        "",
        _ascii(_compare_by_key(streams, "symbol")),
        "",
        "## 5. Per-year (n + mean net_bps per stream)",
        "",
        _ascii(_compare_by_key(
            {k: _year_col(v) for k, v in streams.items()}, "year"
        )),
        "",
        "## 6. P(win)-proportional sizing overlay (REPORT-ONLY $ view; PROTOCOL v6 §3)",
        "",
        "$10k research book. equal = flat $10k/plan; p_win = notional proportional to "
        "P(win), average notional held at $10k (pure reallocation of the SAME taken "
        "stream toward higher-confidence plans). Never a gate or training objective.",
        "",
        _ascii(sizing_overlay(streams)),
        "",
        "## 7. Feature importances (mean LightGBM gain across folds)",
        "",
        _ascii(importances),
        "",
        "## 8. Calibration — predicted P(win) decile vs realized win rate (baseline OOS)",
        "",
        "Equal-count deciles by predicted P(win); realized_win_rate is the realized "
        "fraction of winners in the bin. Monotone rising ⇒ the score ranks reliability.",
        "",
        _ascii(calibration_table(oos)),
        "",
        "## 9. PROTOCOL v6.1 ground-truthing — 10 stratified gated events (join-correctness)",
        "",
        f"Confirming the join for the `{[k for k, v in streams.items() if v is gt_stream][0]}` "
        "gated stream (economics already fill-verified upstream in M6-FINAL). "
        "entry_in_nbbo: entry fill within the prevailing NBBO at 15:55:10. "
        "cross_vs_close_bps: cross print vs the official daily close (~0 confirms the "
        "cross IS the official close). net_bps + y_meta echo the labeled economics.",
        "",
        _ascii(_ground_truth(gt_stream)),
        "",
    ]
    return "\n".join(md)


def write_outputs(
    out_dir: Path, trial_id: str, oos: pl.DataFrame, report_md: str,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    oos_path = out_dir / "oos_predictions.parquet"
    report_path = out_dir / "report.md"
    oos.write_parquet(oos_path)
    report_path.write_text(report_md, encoding="utf-8")
    return oos_path, report_path


def evaluate(events: pl.DataFrame) -> dict:
    """Build the meta frame, run the walk-forward, assemble the streams. Pure over
    ``events`` (the LightGBM seed is fixed in lgbm.DEFAULT_PARAMS)."""
    n_cand_raw = events.filter(pl.col("basis_bps").abs() >= CANDIDATE_BASIS_BPS).height
    meta = build_meta_frame(events)
    meta_counts = {
        "events_rows": events.height,
        "candidates_basis_ge_10": n_cand_raw,
        "candidates_labeled": meta.height,
        "candidates_dropped_null_net": n_cand_raw - meta.height,
        "win_rate_all_candidates": round(float((meta[NET_COL] > 0).mean()), 4)
        if meta.height else None,
    }
    oos, importances, folds = run_walk_forward(meta)
    streams = build_streams(oos)
    return {
        "meta": meta, "meta_counts": meta_counts, "oos": oos,
        "importances": importances, "folds": folds, "streams": streams,
    }


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--trial-id", default="M8-meta-v1", help="Experiment id -> research/experiments/<id>/.")
@click.option("--events", default=DEFAULT_EVENTS, help="M6-FINAL events.parquet (candidates + features).")
@click.option("--seed", default=7, type=int, help="Reproducibility echo (model seed is lgbm.DEFAULT_PARAMS).")
def main(trial_id: str, events: str, seed: int) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety

    events_df = pl.read_parquet(events)
    if (events_df["session"].max() or "") >= HOLDOUT_START.isoformat():
        raise SealViolation(
            "events reach the sealed holdout — refusing (PROTOCOL v6 §1)"
        )

    t0 = time.time()
    ev = evaluate(events_df)
    report_md = build_report_md(
        trial_id, ev["oos"], ev["streams"], ev["importances"], ev["folds"],
        ev["meta_counts"], seed,
    )
    wall = time.time() - t0

    out_dir = experiments_dir() / trial_id
    oos_path, report_path = write_outputs(out_dir, trial_id, ev["oos"], report_md)

    click.echo(f"trial: {trial_id}  events={events}  seed={seed}")
    click.echo(f"meta funnel: {json.dumps(ev['meta_counts'], default=str)}")
    click.echo(f"folds: {len(ev['folds'])}  OOS candidates: {ev['oos'].height}")
    click.echo("")
    click.echo(_ascii(comparison_table(ev["streams"])))
    click.echo("")
    click.echo(f"oos:    {oos_path}")
    click.echo(f"report: {report_path}")
    click.echo(f"wall: {wall:.1f}s")


if __name__ == "__main__":
    main()
