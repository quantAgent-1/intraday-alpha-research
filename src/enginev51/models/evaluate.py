"""Evaluation: per-session rank-IC with day-clustered bootstrap CIs.

IC convention: within each session, Spearman correlation between prediction and
realized forward return over all pooled (symbol, ts) decision rows; the session
is the clustering unit for the bootstrap (PROTOCOL §4).

v5.1: session-decile helpers deliberately not ported (non-causal; engineV5
ledger 2026-07-13). Ranking predictions within a whole session to form deciles
(and the top-decile long-side economics that depended on it) uses end-of-session
information at decision time — harness debt, not a causal signal.
"""

from __future__ import annotations

import numpy as np
import polars as pl


def per_session_ic(preds: pl.DataFrame) -> pl.DataFrame:
    """preds: columns session, pred, label. Returns (session, ic, n)."""
    return (
        preds.group_by("session")
        .agg(
            pl.corr(pl.col("pred").rank(), pl.col("label").rank()).alias("ic"),
            pl.len().alias("n"),
        )
        .filter(pl.col("ic").is_not_null() & pl.col("ic").is_not_nan() & (pl.col("n") >= 30))
        .sort("session")
    )


def bootstrap_mean_ci(
    values: np.ndarray, n_boot: int = 2000, seed: int = 7, ci: float = 0.95
) -> tuple[float, float, float]:
    """(mean, lo, hi) with cluster resampling already applied upstream (one value per session)."""
    rng = np.random.default_rng(seed)
    values = values[~np.isnan(values)]
    if len(values) == 0:
        return float("nan"), float("nan"), float("nan")
    means = np.empty(n_boot)
    n = len(values)
    for b in range(n_boot):
        means[b] = values[rng.integers(0, n, n)].mean()
    alpha = (1 - ci) / 2
    return float(values.mean()), float(np.quantile(means, alpha)), float(np.quantile(means, 1 - alpha))


def ic_summary(preds: pl.DataFrame) -> dict:
    ics = per_session_ic(preds)
    mean, lo, hi = bootstrap_mean_ci(ics["ic"].to_numpy())
    return {
        "sessions": ics.height,
        "rows": preds.height,
        "mean_ic": round(mean, 5),
        "ic_ci95": [round(lo, 5), round(hi, 5)],
        "ic_positive_share": round(float((ics["ic"] > 0).mean()), 4) if ics.height else None,
    }
