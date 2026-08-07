"""A1 overlay trainer — pooled cross-symbol LightGBM forecasts (trial M3-A1-v1).

Implements the REGISTERED "A1 overlay" spec (research/experiments/M3_REGISTRATION.md):
materialize the ported v1_1 38-col feature registry on the 12-name bar universe,
pool every signal symbol, and fit 8 LightGBM heads per expanding walk-forward fold:

    fwd60, fwd120                      (huber)      -> pred_fwd{60,120}_z
    MFE60 q50, MFE60 q75, MAE60 q75    (quantile)   -> pred_mfe60_q50_z, ...
    MFE120 q50, MFE120 q75, MAE120 q75 (quantile)   -> pred_mfe120_q50_z, ...

Labels are vol-normalized per the FROZEN Z-CONVENTION:
    z = label / (f_vol20 * sqrt(H_min/390));  bps_move = z * vol20 * sqrt(H_min/390) * 1e4.
MAE labels are stored as (negative) log drawdowns; the emitted MAE z is a MAGNITUDE (>= 0).

Each prediction row's model is trained ONLY on sessions strictly before its fold
(PIT: trained_through < session). Holdout (>= protocol.HOLDOUT_START) is stripped
before any fold is cut and re-asserted on every emitted row — research code never
touches the seal. Predictions are written per TICK symbol to the frozen contract
parquet (atomic tmp+replace); a _train_report.json carries per-fold/per-horizon
rank-IC diagnostics, params, and wall time.

    uv run python -m enginev51.apps.train_a1 \
        --feature-version v1 --out data/preds/a1_v1 --tick-symbols NVDA,TSLA,AMD,MU
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

import click
import polars as pl
import structlog

from enginev51.config import Settings, get_research_config, get_settings
from enginev51.features import materialize, slow
from enginev51.models import cv, evaluate, lgbm
from enginev51.models.cv import Fold
from enginev51.protocol import HOLDOUT_START, SealViolation, apply_seal

log = structlog.get_logger(__name__)

TRIAL_ID = "M3-A1-v1"
SESSION_MINUTES = 390.0
FEATURE_COLS: tuple[str, ...] = tuple(slow.FEATURE_COLS)

# The de-norm factor column. In the materialized frame f_vol20 == vol20 (slow.py),
# and the Z-CONVENTION is written against f_vol20; we emit it as contract `vol20`.
VOL_COL = "f_vol20"

# --- z-label registry: (z_col, source_label_col, H_min, magnitude) --------------
Z_LABELS: tuple[tuple[str, str, int, bool], ...] = (
    ("z_fwd60", "l_fwd_60m", 60, False),
    ("z_fwd120", "l_fwd_120m", 120, False),
    ("z_mfe60", "l_mfe_60m", 60, False),
    ("z_mfe120", "l_mfe_120m", 120, False),
    ("z_mae60", "l_mae_60m", 60, True),  # stored negative -> emitted magnitude >= 0
    ("z_mae120", "l_mae_120m", 120, True),
)

# --- model heads: out_col -> (z_label_col, objective spec) -----------------------
# fwd heads use the DEFAULT_PARAMS huber objective; quantile heads override the
# LightGBM `alpha` parameter (whose alias in DEFAULT_PARAMS is `huber_delta`).
FWD_HEADS: dict[str, str] = {
    "pred_fwd60_z": "z_fwd60",
    "pred_fwd120_z": "z_fwd120",
}
Q_HEADS: dict[str, tuple[str, float]] = {
    "pred_mfe60_q50_z": ("z_mfe60", 0.5),
    "pred_mfe60_q75_z": ("z_mfe60", 0.75),
    "pred_mae60_q75_z": ("z_mae60", 0.75),
    "pred_mfe120_q50_z": ("z_mfe120", 0.5),
    "pred_mfe120_q75_z": ("z_mfe120", 0.75),
    "pred_mae120_q75_z": ("z_mae120", 0.75),
}
PRED_COLS: tuple[str, ...] = tuple(FWD_HEADS) + tuple(Q_HEADS)

CONTRACT_COLS: tuple[str, ...] = (
    "symbol", "session", "ts",
    "pred_fwd60_z", "pred_fwd120_z",
    "pred_mfe60_q50_z", "pred_mfe60_q75_z", "pred_mae60_q75_z",
    "pred_mfe120_q50_z", "pred_mfe120_q75_z", "pred_mae120_q75_z",
    "vol20", "fold_id", "trained_through",
)


# --------------------------------------------------------------------------- z math


def z_scale(h_min: int) -> float:
    """The de-norm scale factor sqrt(H_min/390) (the vol20-free part of the z map)."""
    return math.sqrt(h_min / SESSION_MINUTES)


def to_z(label: float, vol20: float, h_min: int, *, magnitude: bool = False) -> float:
    """label -> vol-normalized z. MAE labels pass magnitude=True (emit |z| >= 0)."""
    v = abs(label) if magnitude else label
    return v / (vol20 * z_scale(h_min))


def to_bps(z: float, vol20: float, h_min: int) -> float:
    """z -> realized move in basis points (the registered de-norm)."""
    return z * vol20 * z_scale(h_min) * 1e4


def bps_to_z(bps: float, vol20: float, h_min: int) -> float:
    """Inverse of to_bps — used by the round-trip identity test."""
    return bps / (vol20 * z_scale(h_min) * 1e4)


def z_label_expr(source: str, h_min: int, magnitude: bool) -> pl.Expr:
    """Polars expression building one vol-normalized z label column."""
    raw = pl.col(source).abs() if magnitude else pl.col(source)
    denom = pl.col(VOL_COL) * z_scale(h_min)
    return pl.when(pl.col(VOL_COL) > 0).then(raw / denom).otherwise(None)


def add_z_labels(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        [z_label_expr(src, h, mag).alias(zc) for zc, src, h, mag in Z_LABELS]
    )


# --------------------------------------------------------------------------- params


def quantile_params(alpha: float) -> dict:
    """DEFAULT_PARAMS copy retargeted to a quantile head.

    `huber_delta` is LightGBM's alias for `alpha`; overriding it (rather than
    adding a second `alpha` key) sets the quantile level with no alias clash."""
    p = dict(lgbm.DEFAULT_PARAMS)
    p["objective"] = "quantile"
    p["huber_delta"] = alpha  # == alpha (LightGBM alias); the quantile level
    return p


# --------------------------------------------------------------------------- features


def _feature_dir(settings: Settings, version: str) -> Path:
    return settings.data_dir / "features" / version


def ensure_features(settings: Settings, version: str) -> dict[str, int]:
    """Materialize the feature+label matrix if the 12 signal parquets are absent.

    Returns row counts per present signal symbol (post-materialize)."""
    signal = [s.upper() for s in get_research_config().universe_bar_signal]
    fdir = _feature_dir(settings, version)
    present = {s: (fdir / f"{s}.parquet").is_file() for s in signal}
    if not all(present.values()):
        missing = [s for s, ok in present.items() if not ok]
        log.info("materialize_features", version=version, missing=missing)
        materialize.materialize(settings, version=version)
    counts: dict[str, int] = {}
    for s in signal:
        p = fdir / f"{s}.parquet"
        if p.is_file():
            counts[s] = pl.scan_parquet(p).select(pl.len()).collect().item()
    log.info("feature_rows", counts=counts)
    return counts


def load_pool(settings: Settings, version: str) -> pl.DataFrame:
    """Load + concat every signal-symbol feature frame; strip the sealed holdout.

    z labels are attached here so both training and IC use the same convention."""
    signal = [s.upper() for s in get_research_config().universe_bar_signal]
    fdir = _feature_dir(settings, version)
    # VOL_COL (f_vol20) is already part of FEATURE_COLS; dedupe, preserving order.
    want = ["symbol", "session", "ts", VOL_COL, *FEATURE_COLS] + [zc for zc, _, _, _ in Z_LABELS]
    keep = list(dict.fromkeys(want))
    frames: list[pl.DataFrame] = []
    for s in signal:
        p = fdir / f"{s}.parquet"
        if not p.is_file():
            continue
        df = add_z_labels(pl.read_parquet(p))
        frames.append(df.select(keep))
    if not frames:
        raise RuntimeError(f"no feature parquets under {fdir}")
    pool = pl.concat(frames, how="vertical").sort(["session", "ts", "symbol"])
    pool = apply_seal(pool)  # sessions < HOLDOUT_START only
    if not (pool["session"] < HOLDOUT_START.isoformat()).all():
        raise SealViolation("seal failed: holdout row present in the tick pool")
    return pool


# --------------------------------------------------------------------------- folds


def emit_fold_frame(fold_id: int, fold: Fold, tick_pool: pl.DataFrame) -> pl.DataFrame:
    """The rows a fold WOULD emit: tick rows in the fold's test sessions, pre-holdout,
    stamped with fold_id + trained_through (= last train session). Pure — no model
    involved — so PIT / holdout invariants are unit-testable without LightGBM."""
    trained_through = fold.train_sessions[-1]
    test = set(fold.test_sessions)
    out = tick_pool.filter(
        pl.col("session").is_in(list(test)) & (pl.col("session") < HOLDOUT_START.isoformat())
    )
    out = out.with_columns(
        pl.lit(fold_id, dtype=pl.Int64).alias("fold_id"),
        pl.lit(trained_through, dtype=pl.Utf8).alias("trained_through"),
    )
    # PIT: every emitted row must be strictly after the model's training data.
    assert (out["trained_through"] < out["session"]).all() if out.height else True
    return out


def train_fold_models(train_pool: pl.DataFrame) -> dict[str, object]:
    """Fit all 8 heads on one fold's training pool (huber fwd + 6 quantile heads)."""
    boosters: dict[str, object] = {}
    for out_col, z_col in FWD_HEADS.items():
        boosters[out_col] = lgbm.train_one(train_pool, FEATURE_COLS, z_col)
    for out_col, (z_col, alpha) in Q_HEADS.items():
        boosters[out_col] = lgbm.train_one(
            train_pool, FEATURE_COLS, z_col, params=quantile_params(alpha)
        )
    return boosters


def predict_fold(boosters: dict[str, object], emit: pl.DataFrame) -> pl.DataFrame:
    """Attach the 8 head predictions to a fold's emit frame."""
    preds = {out_col: lgbm.predict(bst, emit, FEATURE_COLS) for out_col, bst in boosters.items()}
    out = emit.with_columns([pl.Series(c, preds[c]) for c in PRED_COLS])
    # MAE heads are magnitudes by contract; quantile output can dip slightly < 0.
    out = out.with_columns(
        [pl.col(c).clip(lower_bound=0.0).alias(c) for c in ("pred_mae60_q75_z", "pred_mae120_q75_z")]
    )
    return out.with_columns(pl.col(VOL_COL).alias("vol20"))


# --------------------------------------------------------------------------- io


def atomic_write_parquet(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.write_parquet(tmp, compression="zstd")
    os.replace(tmp, path)


def _fold_ic(rows: pl.DataFrame) -> dict:
    """Per-horizon rank-IC of pred_fwd vs realized z (evaluate.per_session_ic)."""
    out: dict[str, dict] = {}
    for pred_col, z_col, tag in (
        ("pred_fwd60_z", "z_fwd60", "fwd60"),
        ("pred_fwd120_z", "z_fwd120", "fwd120"),
    ):
        sub = rows.select(
            pl.col("session"),
            pl.col(pred_col).alias("pred"),
            pl.col(z_col).alias("label"),
        ).filter(pl.col("label").is_not_null())
        out[tag] = evaluate.ic_summary(sub) if sub.height else {}
    return out


# --------------------------------------------------------------------------- run


def run(
    settings: Settings,
    *,
    version: str,
    out_dir: Path,
    tick_symbols: list[str],
) -> dict:
    """Full A1 training pass. Returns the report dict (also written to _train_report.json)."""
    t0 = time.time()
    tick_symbols = [s.strip().upper() for s in tick_symbols]

    feat_counts = ensure_features(settings, version)
    pool = load_pool(settings, version)
    log.info("pool_ready", rows=pool.height, sessions=pool["session"].n_unique(),
             symbols=pool["symbol"].n_unique())

    present_ticks = [s for s in tick_symbols if s in set(pool["symbol"].unique().to_list())]
    for s in tick_symbols:
        if s not in present_ticks:
            log.warning("tick_symbol_absent", symbol=s)
    tick_pool = pool.filter(pl.col("symbol").is_in(present_ticks))

    folds = cv.walk_forward_folds(pool)
    log.info("folds", n=len(folds))

    emitted: list[pl.DataFrame] = []
    fold_reports: list[dict] = []
    for fold_id, fold in enumerate(folds):
        f_t0 = time.time()
        train_pool = pool.filter(pl.col("session").is_in(list(fold.train_sessions)))
        emit = emit_fold_frame(fold_id, fold, tick_pool)
        if emit.height == 0:
            log.info("fold_skip_no_tick_rows", fold_id=fold_id,
                     trained_through=fold.train_sessions[-1])
            continue
        boosters = train_fold_models(train_pool)
        rows = predict_fold(boosters, emit)
        emitted.append(rows)
        fold_reports.append({
            "fold_id": fold_id,
            "trained_through": fold.train_sessions[-1],
            "n_train_sessions": len(fold.train_sessions),
            "n_train_rows": train_pool.height,
            "test_sessions": list(fold.test_sessions),
            "n_tick_rows": rows.height,
            "ic": _fold_ic(rows),
            "wall_s": round(time.time() - f_t0, 2),
        })
        log.info("fold_done", fold_id=fold_id, trained_through=fold.train_sessions[-1],
                 tick_rows=rows.height, wall_s=round(time.time() - f_t0, 1))

    pred_rows_per_symbol: dict[str, int] = {}
    if emitted:
        allrows = pl.concat(emitted, how="vertical")
        # Final belt-and-suspenders holdout + PIT checks on the emitted stream.
        if not (allrows["session"] < HOLDOUT_START.isoformat()).all():
            raise SealViolation("seal failed: holdout row in the emitted prediction stream")
        assert (allrows["trained_through"] < allrows["session"]).all()
        for s in present_ticks:
            sym_df = allrows.filter(pl.col("symbol") == s).select(CONTRACT_COLS).sort(["session", "ts"])
            if sym_df.height == 0:
                log.warning("no_pred_rows", symbol=s)
                continue
            atomic_write_parquet(sym_df, out_dir / f"{s}.parquet")
            pred_rows_per_symbol[s] = sym_df.height
            log.info("preds_written", symbol=s, rows=sym_df.height, out=str(out_dir / f"{s}.parquet"))
        pooled_ic = _fold_ic(allrows)
    else:
        pooled_ic = {}

    report = {
        "trial": TRIAL_ID,
        "feature_version": version,
        "out_dir": str(out_dir),
        "tick_symbols_requested": tick_symbols,
        "tick_symbols_present": present_ticks,
        "materialized_feature_rows": feat_counts,
        "pool_rows": pool.height,
        "pool_sessions": pool["session"].n_unique(),
        "n_folds": len(folds),
        "n_folds_emitted": len(fold_reports),
        "pred_rows_per_symbol": pred_rows_per_symbol,
        "params": {
            "fwd_huber": dict(lgbm.DEFAULT_PARAMS),
            "quantile_q50": quantile_params(0.5),
            "quantile_q75": quantile_params(0.75),
            "cv": {"test_block_sessions": 21, "min_train_sessions": 250, "embargo_sessions": 1},
        },
        "pooled_ic": pooled_ic,
        "folds": fold_reports,
        "wall_s": round(time.time() - t0, 2),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_train_report.json").write_text(json.dumps(report, indent=2, default=str))
    log.info("train_complete", wall_s=report["wall_s"], folds_emitted=len(fold_reports),
             pred_rows=pred_rows_per_symbol)
    return report


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--feature-version", default="v1", help="Feature matrix version (data/features/<v>/).")
@click.option("--out", default="data/preds/a1_v1", help="Output dir for contract parquets.")
@click.option("--tick-symbols", default="NVDA,TSLA,AMD,MU", help="Symbols to emit predictions for.")
def main(feature_version: str, out: str, tick_symbols: str) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    settings = get_settings()
    out_dir = Path(out)
    if not out_dir.is_absolute():  # resolve relative paths against the repo root
        out_dir = settings.data_dir.parent / out
    ticks = [s.strip().upper() for s in tick_symbols.split(",") if s.strip()]

    report = run(settings, version=feature_version, out_dir=out_dir, tick_symbols=ticks)

    click.echo(f"trial: {TRIAL_ID}  feature_version={feature_version}")
    click.echo(f"materialized feature rows: {report['materialized_feature_rows']}")
    click.echo(f"pool rows: {report['pool_rows']}  sessions: {report['pool_sessions']}")
    click.echo(f"folds: {report['n_folds']}  emitted: {report['n_folds_emitted']}")
    click.echo(f"pred rows per symbol: {report['pred_rows_per_symbol']}")
    click.echo(f"pooled rank-IC: {report['pooled_ic']}")
    click.echo(f"out: {report['out_dir']}")
    click.echo(f"wall: {report['wall_s']}s")


if __name__ == "__main__":
    main()
