"""LightGBM pooled regressors, one per horizon. CPU (9800X3D) is the right tool
at this scale; GPU/NN experiments are gated on this baseline showing value
(DESIGN.md §4). Deterministic seeds; early stopping on the tail of train."""

from __future__ import annotations

import lightgbm as lgb
import numpy as np
import polars as pl

DEFAULT_PARAMS: dict = {
    "objective": "huber",
    "huber_delta": 3.0,          # labels are in log-return; robust to tail prints
    "num_leaves": 63,
    "learning_rate": 0.05,
    "min_data_in_leaf": 300,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l2": 5.0,
    "verbosity": -1,
    "seed": 7,
    "num_threads": 0,
}


def to_matrix(df: pl.DataFrame, feature_cols: tuple[str, ...]) -> np.ndarray:
    return df.select(feature_cols).to_numpy().astype(np.float32)


def train_one(
    df_train: pl.DataFrame,
    feature_cols: tuple[str, ...],
    label_col: str,
    params: dict | None = None,
    num_rounds: int = 600,
    early_stop_frac: float = 0.1,
    val_mode: str = "tail",
) -> lgb.Booster:
    """val_mode 'tail' = chronological last sessions (walk-forward default);
    'random_sessions' = random session subset — used for full-data frozen fits
    where the tail is a single unrepresentative regime (labels are intraday, so
    a session-level random split has no label overlap)."""
    d = df_train.filter(pl.col(label_col).is_not_null())
    sessions = sorted(d["session"].unique().to_list())
    if val_mode == "random_sessions":
        rng = np.random.default_rng(11)
        n_val = max(1, int(len(sessions) * early_stop_frac))
        val_sessions = set(rng.choice(sessions, size=n_val, replace=False).tolist())
        tr = d.filter(~pl.col("session").is_in(list(val_sessions)))
        va = d.filter(pl.col("session").is_in(list(val_sessions)))
    else:
        cut = sessions[int(len(sessions) * (1 - early_stop_frac))]
        tr = d.filter(pl.col("session") < cut)
        va = d.filter(pl.col("session") >= cut)

    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)

    dtrain = lgb.Dataset(
        to_matrix(tr, feature_cols),
        label=tr[label_col].to_numpy(),
        feature_name=list(feature_cols),
        free_raw_data=True,
    )
    dval = lgb.Dataset(
        to_matrix(va, feature_cols),
        label=va[label_col].to_numpy(),
        reference=dtrain,
        free_raw_data=True,
    )
    booster = lgb.train(
        p,
        dtrain,
        num_boost_round=num_rounds,
        valid_sets=[dval],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
    )
    return booster


def predict(booster: lgb.Booster, df: pl.DataFrame, feature_cols: tuple[str, ...]) -> np.ndarray:
    return booster.predict(to_matrix(df, feature_cols), num_iteration=booster.best_iteration)
