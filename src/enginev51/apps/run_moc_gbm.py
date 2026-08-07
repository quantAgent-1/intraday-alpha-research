"""M6-GBM runner — LightGBM on the registered NOII features, expanding calendar
walk-forward, fixed ``pred > 0`` gate, report with the registered anti-concentration
prongs and PROTOCOL v6.1 fill ground-truthing.

Pipeline (M3_REGISTRATION.md "M6-GBM cell"):

    base MOC-max-t10-persist events (realized net_bps)
      -> build_features(symbol, session) PIT@15:50:10  [JOINED onto the base rows]
      -> expanding walk-forward (>=2y train, 6-month test blocks, 1-session embargo)
      -> OOS pred per event beyond the initial-train span
      -> FIXED gate pred>0 -> gated taken stream
      -> report.md: gated-vs-ungated pooled day-clustered CI, anti-concentration
         prongs (n_taken, symbols spanned, years spanned), per-symbol/per-year
         tables, feature importances, prediction-weighted sizing view (report-only),
         10 stratified gated ground-truth fills (entry BBO + cross vs daily close).

Writes NO ledger row (the orchestrator owns verdicts). Holdout stays sealed: the
base events are already < 2026-06-01, and this app hard-asserts it.

    uv run python -m enginev51.apps.run_moc_gbm --trial-id M6-GBM-v1 \
        --base research/experiments/MOC-max-t10-persist/results.parquet --seed 7
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
from enginev51.backtest.auction_replay import adv20_dollars
from enginev51.config import get_settings
from enginev51.models.moc_gbm import (
    FEATURE_COLS,
    _load_daily_closes,
    build_features,
    gate,
    run_walk_forward,
)
from enginev51.protocol import HOLDOUT_START, SealViolation, experiments_dir, split_of

log = structlog.get_logger(__name__)

DEFAULT_BASE = "research/experiments/MOC-max-t10-persist/results.parquet"


# --------------------------------------------------------------------------- features


def build_feature_table(settings, base: pl.DataFrame, noii_dir=None) -> tuple[pl.DataFrame, dict]:
    """Join the registered PIT features onto every base event.

    Reuses the base row's ``adv20_dollars`` (which ``build_features`` reproduces
    exactly) to avoid re-reading the bar store per event, and caches NOII month
    partitions and daily closes per symbol. Returns ``(feat_df, counts)`` where
    ``feat_df`` carries ``session``/``symbol``/``net_bps`` + ``FEATURE_COLS``.
    """
    from enginev51.data.noii import load_noii_session

    if (base["session"].max() or "") >= HOLDOUT_START.isoformat():
        raise SealViolation(
            "base events reach the sealed holdout — refusing (PROTOCOL v6 §1)"
        )

    noii_cache: dict[tuple[str, str], pl.DataFrame | None] = {}
    closes_cache: dict[str, list[tuple[str, float]]] = {}
    counts = {"rows": base.height, "built": 0, "no_features": 0}

    rows: list[dict] = []
    for r in base.iter_rows(named=True):
        sym, sess = r["symbol"], r["session"]
        key = (sym, sess[:7])
        if key not in noii_cache:
            noii_cache[key] = load_noii_session(sym, sess, out_dir=noii_dir)
        frame = noii_cache[key]
        if sym not in closes_cache:
            closes_cache[sym] = _load_daily_closes(sym)

        adv = r.get("adv20_dollars")
        if adv is None or adv <= 0.0:
            adv = adv20_dollars(settings, sym, sess)

        feat = build_features(
            sym, sess,
            settings=settings, noii_dir=noii_dir,
            adv20=adv, noii_frame=frame, closes=closes_cache[sym],
        )
        if feat is None:
            counts["no_features"] += 1
            continue
        feat["net_bps"] = float(r["net_bps"])
        # carry ground-truth context columns straight from the base file
        for c in ("side", "norm_imb", "entry_bid", "entry_ask", "entry_px",
                  "exit_reason", "cross_px", "bar_close"):
            feat[f"_{c}"] = r.get(c)
        rows.append(feat)
        counts["built"] += 1

    feat_df = pl.DataFrame(rows, infer_schema_length=None)
    return feat_df, counts


# --------------------------------------------------------------------------- report helpers


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


def _grouped_ci_table(df: pl.DataFrame, key: str, key_name: str) -> pl.DataFrame:
    rows: list[dict] = []
    keys = sorted(df[key].unique().to_list()) if df.height else []
    for k in [*keys, "__POOLED__"]:
        sub = df if k == "__POOLED__" else df.filter(pl.col(key) == k)
        m, lo, hi, n, ns = _ci(sub)
        rows.append({
            key_name: "POOLED" if k == "__POOLED__" else str(k),
            "n_events": n,
            "n_sessions": ns,
            "net_bps_mean": round(m, 3) if n else None,
            "ci_lo": round(lo, 3) if n else None,
            "ci_hi": round(hi, 3) if n else None,
        })
    return pl.DataFrame(
        rows,
        schema={
            key_name: pl.Utf8, "n_events": pl.Int64, "n_sessions": pl.Int64,
            "net_bps_mean": pl.Float64, "ci_lo": pl.Float64, "ci_hi": pl.Float64,
        },
        orient="row",
    )


def _year_col(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.col("session").str.slice(0, 4).alias("year"))


def _pred_weighted_view(oos: pl.DataFrame, cap: float = 10.0) -> dict:
    """Report-only prediction-weighted sizing: w = clip(pred, 0, cap) bps.

    Weighted mean net_bps over all OOS events (weight zeroes non-positive preds,
    so this is the gated stream sized by predicted edge). Diagnostic only — never
    a gate or training objective (PROTOCOL v6 §3)."""
    if oos.height == 0:
        return {"weighted_mean_net_bps": None, "n_weighted": 0, "sum_weight": 0.0}
    pred = oos["pred"].to_numpy()
    net = oos["net_bps"].to_numpy()
    w = np.clip(pred, 0.0, cap)
    sw = float(w.sum())
    wm = float((w * net).sum() / sw) if sw > 0 else None
    return {
        "weighted_mean_net_bps": round(wm, 3) if wm is not None else None,
        "n_weighted": int((w > 0).sum()),
        "sum_weight": round(sw, 2),
        "cap_bps": cap,
    }


def _anti_concentration(gated: pl.DataFrame) -> dict:
    """Registered promotion prongs on the gated taken stream (diagnostic echo):
    pooled day-clustered CI lower > 0 AND n_taken >= 800 AND >=3 symbols AND
    >=4 distinct years."""
    m, lo, hi, n, ns = _ci(gated)
    symbols = sorted(gated["symbol"].unique().to_list()) if gated.height else []
    years = sorted({s[:4] for s in gated["session"].to_list()}) if gated.height else []
    return {
        "pooled_mean_net_bps": round(m, 3) if n else None,
        "pooled_ci_lo": round(lo, 3) if n else None,
        "pooled_ci_hi": round(hi, 3) if n else None,
        "n_taken": n,
        "n_sessions": ns,
        "symbols_spanned": symbols,
        "n_symbols": len(symbols),
        "years_spanned": years,
        "n_years": len(years),
        "meets_pooled_lo_gt_0": bool(n and lo > 0),
        "meets_n_taken_ge_800": bool(n >= 800),
        "meets_ge_3_symbols": bool(len(symbols) >= 3),
        "meets_ge_4_years": bool(len(years) >= 4),
    }


def _ground_truth(gated: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """10 stratified gated events with the PROTOCOL v6.1 fill audit columns:
    entry BBO context (entry_in_nbbo) + cross vs daily close (cross_vs_close_bps).
    Stratified: biggest winners, biggest losers, largest |imbalance|, highest pred."""
    schema = {
        "session": pl.Utf8, "symbol": pl.Utf8, "side": pl.Int64, "norm_imb": pl.Float64,
        "pred": pl.Float64, "entry_bid": pl.Float64, "entry_ask": pl.Float64,
        "entry_px": pl.Float64, "exit_reason": pl.Utf8, "cross_px": pl.Float64,
        "bar_close": pl.Float64, "cross_vs_close_bps": pl.Float64,
        "entry_in_nbbo": pl.Boolean, "net_bps": pl.Float64,
    }
    if gated.height == 0:
        return pl.DataFrame(schema=schema)
    d = gated.with_columns(pl.arange(0, pl.len()).alias("_idx"))
    winners = d.sort("net_bps", descending=True).head(3)["_idx"].to_list()
    losers = d.sort("net_bps", descending=False).head(3)["_idx"].to_list()
    big_imb = d.sort(pl.col("_norm_imb").abs(), descending=True).head(2)["_idx"].to_list()
    hi_pred = d.sort("pred", descending=True).head(2)["_idx"].to_list()
    picked: list[int] = []
    for i in [*winners, *losers, *big_imb, *hi_pred]:
        if i not in picked:
            picked.append(i)
        if len(picked) >= k:
            break
    sub = d.filter(pl.col("_idx").is_in(picked)).drop("_idx")
    return sub.with_columns(
        pl.when(pl.col("_bar_close").is_not_null() & (pl.col("_bar_close") > 0))
        .then((pl.col("_cross_px") - pl.col("_bar_close")) / pl.col("_bar_close") * 1e4)
        .otherwise(None).alias("cross_vs_close_bps"),
        pl.when(pl.col("_entry_bid").is_not_null() & pl.col("_entry_ask").is_not_null())
        .then(
            (pl.col("_entry_px") >= pl.col("_entry_bid") * 0.999)
            & (pl.col("_entry_px") <= pl.col("_entry_ask") * 1.001)
        )
        .otherwise(None).alias("entry_in_nbbo"),
    ).select(
        pl.col("session"), pl.col("symbol"), pl.col("_side").alias("side"),
        pl.col("_norm_imb").alias("norm_imb"), pl.col("pred"),
        pl.col("_entry_bid").alias("entry_bid"), pl.col("_entry_ask").alias("entry_ask"),
        pl.col("_entry_px").alias("entry_px"), pl.col("_exit_reason").alias("exit_reason"),
        pl.col("_cross_px").alias("cross_px"), pl.col("_bar_close").alias("bar_close"),
        pl.col("cross_vs_close_bps"), pl.col("entry_in_nbbo"), pl.col("net_bps"),
    )


def build_report_md(
    trial_id: str, oos: pl.DataFrame, gated: pl.DataFrame,
    importances: pl.DataFrame, folds, feat_counts: dict, seed: int,
) -> str:
    base_ci = _ci(oos)          # ungated, same OOS span
    gated_ci = _ci(gated)
    oos_years = sorted({s[:4] for s in oos["session"].to_list()}) if oos.height else []
    fold_meta = [
        {"test_start": f.test_start, "test_end": f.test_end,
         "n_train_sessions": len(f.train_sessions), "n_test_sessions": len(f.test_sessions)}
        for f in folds
    ]
    md: list[str] = [
        f"# M6-GBM report — {trial_id}",
        "",
        "Family `moc_imbalance_v1`, M6-GBM cell (registered 2026-07-17). LightGBM "
        "regression on realized closing-auction net_bps of the registered base "
        "events (MOC-max-t10-persist: threshold 0.001, persistence ON), expanding "
        "calendar walk-forward, FIXED gate `pred > 0`.",
        "",
        f"seed={seed}    features={len(FEATURE_COLS)}    "
        f"model=LightGBM(lgbm.DEFAULT_PARAMS, objective=huber) on net_bps",
        "",
        "Base events joined with PIT features (norm_imb & adv20$ reproduce the base "
        "file exactly, so this augments the already-evaluated events).",
        "",
        "DATA-REALITY NOTE: Nasdaq closing-cross NOII disseminates only from "
        "15:50:00 ET and near/far indicative prices are 0 until ~15:55. So at the "
        "registered 15:50:10 PIT instant the growth-vs-15:48/15:46, near-ref/"
        "near-far bps, near-drift and msg_count features are degenerate on real "
        "data (implemented exactly per the registered formula; see feature "
        "importances). Not a deviation — a property of the dissemination clock.",
        "",
        "## 0. Feature-build funnel",
        "```",
        json.dumps(feat_counts, indent=2, default=str),
        "```",
        "",
        "## 1. Walk-forward folds (expanding, >=2y train, 6-month test blocks, 1-session embargo)",
        "```",
        json.dumps(fold_meta, indent=2, default=str),
        "```",
        f"OOS events (beyond initial-train span): {oos.height}    "
        f"OOS years: {oos_years}",
        "",
        "## 2. Gated vs ungated-same-span baseline (pooled, day-clustered 95% CI)",
        "",
        f"- UNGATED baseline (all OOS events):  {_fmt_ci(base_ci)}",
        f"- GATED (pred > 0) taken stream:      {_fmt_ci(gated_ci)}",
        "",
        "## 3. Registered anti-concentration prongs on the gated stream (diagnostic echo)",
        "```",
        json.dumps(_anti_concentration(gated), indent=2, default=str),
        "```",
        "",
        "## 4. Gated per-symbol net_bps day-clustered CIs",
        "",
        _ascii(_grouped_ci_table(gated, "symbol", "symbol")),
        "",
        "## 5. Gated per-year net_bps day-clustered CIs",
        "",
        _ascii(_grouped_ci_table(_year_col(gated), "year", "year")),
        "",
        "## 5b. Gated split-wise (train-period vs validate-period sessions)",
        "",
        _ascii(_grouped_ci_table(
            gated.with_columns(
                pl.col("session").map_elements(split_of, return_dtype=pl.Utf8).alias("split")
            ) if gated.height else gated.with_columns(pl.lit(None).alias("split")),
            "split", "split",
        )) if gated.height else "(no gated events)",
        "",
        "## 6. Feature importances (mean LightGBM gain across folds)",
        "",
        _ascii(importances),
        "",
        "## 7. Prediction-weighted sizing view (REPORT-ONLY; w = clip(pred, 0, 10) bps)",
        "```",
        json.dumps(_pred_weighted_view(oos), indent=2, default=str),
        "```",
        "",
        "## 8. Ground-truth: 10 stratified gated fills (PROTOCOL v6.1)",
        "",
        "entry_in_nbbo: entry fill within the prevailing NBBO at 15:50:10. "
        "cross_vs_close_bps: official cross print vs the session's daily close "
        "(~0 for a real cross; the cross IS the official close by construction).",
        "",
        _ascii(_ground_truth(gated)),
        "",
    ]
    return "\n".join(md)


def write_outputs(out_dir: Path, trial_id: str, oos: pl.DataFrame, gated: pl.DataFrame,
                  importances: pl.DataFrame, folds, feat_counts: dict, seed: int) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    oos_path = out_dir / "oos_predictions.parquet"
    report_path = out_dir / "report.md"
    oos.write_parquet(oos_path)
    report_path.write_text(
        build_report_md(trial_id, oos, gated, importances, folds, feat_counts, seed),
        encoding="utf-8",
    )
    return oos_path, report_path


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--trial-id", default="M6-GBM-v1", help="Experiment id -> research/experiments/<id>/.")
@click.option("--base", default=DEFAULT_BASE, help="Base MOC events results.parquet (with net_bps).")
@click.option("--noii-dir", default=None, help="NOII lake root (default data/raw/noii).")
@click.option("--seed", default=7, type=int, help="Reproducibility echo (model seed is lgbm.DEFAULT_PARAMS).")
def main(trial_id: str, base: str, noii_dir: str | None, seed: int) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")
    settings = get_settings()

    base_df = pl.read_parquet(base)
    t0 = time.time()
    feat_df, feat_counts = build_feature_table(settings, base_df, noii_dir=noii_dir)
    oos, importances, folds = run_walk_forward(feat_df)
    gated = oos.filter(pl.Series(gate(oos["pred"].to_numpy()))) if oos.height else oos
    wall = time.time() - t0

    out_dir = experiments_dir() / trial_id
    oos_path, report_path = write_outputs(
        out_dir, trial_id, oos, gated, importances, folds, feat_counts, seed
    )

    click.echo(f"trial: {trial_id}  base={base}")
    click.echo(f"feature build: {json.dumps(feat_counts, default=str)}")
    click.echo(f"folds: {len(folds)}  OOS events: {oos.height}  gated(pred>0): {gated.height}")
    click.echo("")
    click.echo(f"UNGATED same-span baseline: {_fmt_ci(_ci(oos))}")
    click.echo(f"GATED (pred>0):             {_fmt_ci(_ci(gated))}")
    click.echo("")
    click.echo("anti-concentration prongs:")
    click.echo(json.dumps(_anti_concentration(gated), indent=2, default=str))
    click.echo("")
    click.echo(f"oos:    {oos_path}")
    click.echo(f"report: {report_path}")
    click.echo(f"wall: {wall:.1f}s")


if __name__ == "__main__":
    main()
