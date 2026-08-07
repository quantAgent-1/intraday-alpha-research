"""M8 meta-labeling cell of the ``moc_meta_v1`` family (M3_REGISTRATION.md,
"M8 meta-labeling on the classical basis rule — registered 2026-07-17").

The PRIMARY signal is UNCHANGED and classical: |basis| >= 10 bps at 15:55:10 ET,
direction = sign(near - mid). Those are the candidate trades and their realized
``net_bps`` — the M6-FINAL |basis|>=10 events. This module adds a META-LABEL
model on TOP of that rule: a LightGBM BINARY classifier that predicts
``P(net_bps > 0)`` per candidate from RELIABILITY signals (NOT a re-prediction of
direction). A registered gate then keeps only candidates whose P(win) clears a
threshold.

Layering: this is the FEATURE + MODEL layer; ``apps/run_meta_trial.py`` is the
orchestration + report layer. Nothing here writes a ledger row or a verdict.

Walk-forward: the fold builder is ``moc_gbm.walk_forward_folds_calendar`` reused
EXACTLY (expanding calendar, >=2y initial train, 6-month test blocks, 1-session
embargo). Because the meta frame is the |basis|>=10 candidate universe, the folds
tile that universe; every candidate beyond the initial-train span receives exactly
one OOS P(win), and the classical baseline is those SAME OOS rows ungated — so the
gated and ungated streams live on an identical OOS span by construction.

Registered feature list (reliability signals, all PIT at 15:55:10 ET, already
materialized in the M6-FINAL events frame):
    basis_bps, near_far_bps (indicative instability), near_ref_bps, paired_ratio,
    norm_imb, imb_growth_53, imb_growth_51, msg_count, vol20, log_adv20,
    symbol one-hot. NOTE: ``side`` is deliberately absent — the meta model scores
    reliability, it does not re-predict the classical direction.

POST-HOLDOUT (the seal was spent by M6-FINAL): this cell's OOS evidence is
walk-forward only; forward paper is the sole clean validation. The events frame is
entirely < 2026-06-01 and ``build_meta_frame`` hard-asserts it.
"""

from __future__ import annotations

import lightgbm as lgb
import numpy as np
import polars as pl

from enginev51.models import lgbm as lgbm_model
from enginev51.models.moc_gbm import Fold, walk_forward_folds_calendar

# Registered universe (symbol one-hot columns are in this fixed order).
UNIVERSE: tuple[str, ...] = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")

# Candidate trades = the winning classical cell: |basis_bps| >= this threshold.
CANDIDATE_BASIS_BPS: float = 10.0

# Registered reliability feature set (order is fixed + documented). ``side`` is
# intentionally excluded (meta-labeling scores reliability, not direction).
NUMERIC_FEATURES: tuple[str, ...] = (
    "basis_bps",
    "near_far_bps",
    "near_ref_bps",
    "paired_ratio",
    "norm_imb",
    "imb_growth_53",
    "imb_growth_51",
    "msg_count",
    "vol20",
    "log_adv20",
)
ONEHOT_FEATURES: tuple[str, ...] = tuple(f"oh_{s}" for s in UNIVERSE)
FEATURE_COLS: tuple[str, ...] = NUMERIC_FEATURES + ONEHOT_FEATURES

# Binary meta-label column and the realized-economics column it is derived from.
LABEL_COL = "y_meta"
NET_COL = "net_bps"
PRED_COL = "p_win"

# Registered a-priori gates on P(win): TAKE iff P(win) >= q.
GATES: tuple[float, ...] = (0.50, 0.55, 0.60)

# CANON (code review 2026-07-28 S5 / 2026-08-01 J3c): the HEADLINE meta gate — the
# one of the three registered GATES that every downstream reader means when it says
# "the M8 gate" (the +4.0 bps reference stream, forward_paper.META_GATE_Q, the M11
# transfer gate, live_cockpit's meta stream, the M23 sizing tier floor). This module
# is its canonical home. SIX other modules carry their own frozen literal 0.55
# (apps.forward_paper, apps.run_m11, apps.run_m9, models.m8v2_run, models.sizing,
# research_screens.sizing_shadow), and this module's own GATES[1] is a seventh copy;
# `protocol.assert_protocol_consistent()` pins all seven against THIS constant, so a
# drift in any of them fails the suite. Frozen modules are NOT rewired to import it —
# their registered literals stay, they are merely pinned. Modules that DO inherit the
# number by import (apps.live_cockpit) are not pinned: they cannot drift.
HEADLINE_GATE: float = 0.55

# ``lgbm.DEFAULT_PARAMS`` adapted to a probability classifier: swap the huber
# regression objective for ``binary`` (which emits calibrated-ish P(class=1)).
# Depth/leaves and every regularizer are kept per the registration ("keep
# depth/leaves"). ``huber_delta`` is inert under objective=binary (verbosity=-1
# silences the unused-param warning); METRIC is binary_logloss for early stopping.
META_PARAMS: dict = {"objective": "binary", "metric": "binary_logloss"}


# --------------------------------------------------------------------------- frame


def candidates(events: pl.DataFrame, threshold_bps: float = CANDIDATE_BASIS_BPS) -> pl.DataFrame:
    """The classical candidate trades: rows with ``|basis_bps| >= threshold_bps``."""
    return events.filter(pl.col("basis_bps").abs() >= threshold_bps)


def build_meta_frame(
    events: pl.DataFrame, threshold_bps: float = CANDIDATE_BASIS_BPS
) -> pl.DataFrame:
    """Assemble the meta-training frame from the |basis|>=threshold candidates.

    Adds the binary meta-label ``y_meta = 1 iff net_bps > 0`` and keeps every
    column already present in the events frame (features + ground-truth context).
    Hard-enforces the holdout seal (PROTOCOL v6 §1) with a SealViolation: the
    frame must be strictly before 2026-06-01. Rows with a null ``net_bps`` cannot
    be labeled and are dropped (counted by the caller via the height delta).
    """
    from enginev51.protocol import HOLDOUT_START, SealViolation

    if events.height and (events["session"].max() or "") >= HOLDOUT_START.isoformat():
        raise SealViolation(
            "events reach the sealed holdout — refusing (PROTOCOL v6 §1); "
            "the seal is SPENT but research code still never touches >=2026-06-01"
        )
    cand = candidates(events, threshold_bps).filter(pl.col(NET_COL).is_not_null())
    return cand.with_columns(
        (pl.col(NET_COL) > 0.0).cast(pl.Int8).alias(LABEL_COL)
    )


def assert_features_present(df: pl.DataFrame) -> None:
    """Every registered feature column must exist in the frame (fail loud)."""
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise KeyError(f"meta frame missing registered features: {missing}")


# --------------------------------------------------------------------------- model


def gate(p_win: np.ndarray | float, q: float) -> np.ndarray | bool:
    """The registered gate: TAKE iff P(win) >= q. Deterministic, pure."""
    if np.isscalar(p_win):
        return bool(p_win >= q)
    return np.asarray(p_win, dtype=float) >= q


def train_fold(df_train: pl.DataFrame, params: dict | None = None) -> lgb.Booster:
    """Fit one LightGBM BINARY classifier on ``y_meta`` with the adapted params."""
    p = dict(META_PARAMS)
    if params:
        p.update(params)
    return lgbm_model.train_one(df_train, FEATURE_COLS, LABEL_COL, params=p)


def predict_pwin(booster: lgb.Booster, df: pl.DataFrame) -> np.ndarray:
    """P(win) = P(net_bps > 0) for each row (binary objective → class-1 prob)."""
    return lgbm_model.predict(booster, df, FEATURE_COLS)


def run_walk_forward(
    meta_df: pl.DataFrame,
    *,
    initial_train_years: int = 2,
    test_block_months: int = 6,
    embargo_sessions: int = 1,
    params: dict | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, list[Fold]]:
    """Expanding calendar walk-forward over the candidate meta frame.

    Mirrors ``moc_gbm.run_walk_forward`` EXACTLY (same fold builder, same fold loop,
    same PIT rule: a fold model trains strictly on sessions before its test block,
    minus a 1-session embargo) but fits a BINARY classifier and emits ``p_win``.

    Returns ``(oos_df, importances_df, folds)``:
      * ``oos_df`` — every candidate beyond the initial-train span with an added
        ``p_win`` (OOS P(win)) and ``fold`` (test-block start) column;
      * ``importances_df`` — mean LightGBM gain per feature across folds;
      * ``folds`` — the fold objects (train/test session tuples).
    """
    assert_features_present(meta_df)
    sessions = sorted(meta_df["session"].unique().to_list())
    folds = walk_forward_folds_calendar(
        sessions,
        initial_train_years=initial_train_years,
        test_block_months=test_block_months,
        embargo_sessions=embargo_sessions,
    )
    oos_parts: list[pl.DataFrame] = []
    imp_accum: dict[str, list[float]] = {c: [] for c in FEATURE_COLS}
    for fold in folds:
        tr = meta_df.filter(pl.col("session").is_in(list(fold.train_sessions)))
        te = meta_df.filter(pl.col("session").is_in(list(fold.test_sessions)))
        if tr.height == 0 or te.height == 0:
            continue
        # PIT guard (defence in depth): no training row may be dated at/after the
        # test-block start — the walk-forward's whole point.
        assert (tr["session"].max() or "") < fold.test_start, (
            f"leakage: train row >= test_start {fold.test_start}"
        )
        booster = train_fold(tr, params=params)
        preds = predict_pwin(booster, te)
        oos_parts.append(
            te.with_columns(
                pl.Series(PRED_COL, preds),
                pl.lit(fold.test_start).alias("fold"),
            )
        )
        gains = booster.feature_importance(importance_type="gain")
        names = booster.feature_name()
        for name, g in zip(names, gains, strict=True):
            if name in imp_accum:
                imp_accum[name].append(float(g))

    oos_df = (
        pl.concat(oos_parts)
        if oos_parts
        else meta_df.head(0).with_columns(
            pl.lit(None, dtype=pl.Float64).alias(PRED_COL),
            pl.lit(None, dtype=pl.Utf8).alias("fold"),
        )
    )
    imp_rows = [
        {
            "feature": c,
            "mean_gain": float(np.mean(imp_accum[c])) if imp_accum[c] else 0.0,
            "n_folds": len(imp_accum[c]),
        }
        for c in FEATURE_COLS
    ]
    importances_df = pl.DataFrame(
        imp_rows,
        schema={"feature": pl.Utf8, "mean_gain": pl.Float64, "n_folds": pl.Int64},
    ).sort("mean_gain", descending=True)
    return oos_df, importances_df, folds


# --------------------------------------------------------------------------- calibration


def calibration_table(
    oos: pl.DataFrame,
    *,
    pred_col: str = PRED_COL,
    label_col: str = LABEL_COL,
    n_bins: int = 10,
) -> pl.DataFrame:
    """Reliability curve: equal-count P(win) deciles vs the realized win rate.

    Bins the OOS candidates into ``n_bins`` equal-count groups by predicted P(win)
    (rank-based, so tied-probability plateaus never collapse the edges), and
    reports each bin's predicted-probability range, mean predicted P(win), and the
    REALIZED fraction of winners (``y_meta`` mean). A well-calibrated / monotone
    model has ``realized_win_rate`` rising with the bin index and tracking
    ``pred_mean``. Pure over ``oos``.
    """
    schema = {
        "bin": pl.Int64,
        "n": pl.Int64,
        "pred_lo": pl.Float64,
        "pred_hi": pl.Float64,
        "pred_mean": pl.Float64,
        "realized_win_rate": pl.Float64,
    }
    d = oos.select([pred_col, label_col]).drop_nulls()
    if d.height == 0:
        return pl.DataFrame(schema=schema)
    n = d.height
    d = (
        d.sort(pred_col)
        .with_row_index("_i")
        .with_columns(
            (pl.col("_i") * n_bins // n).clip(0, n_bins - 1).alias("bin")
        )
    )
    grp = (
        d.group_by("bin")
        .agg(
            pl.len().alias("n"),
            pl.col(pred_col).min().alias("pred_lo"),
            pl.col(pred_col).max().alias("pred_hi"),
            pl.col(pred_col).mean().alias("pred_mean"),
            pl.col(label_col).cast(pl.Float64).mean().alias("realized_win_rate"),
        )
        .sort("bin")
    )
    return grp.select(list(schema)).cast(schema)  # type: ignore[arg-type]
