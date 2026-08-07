"""M9 Cell B — calibrated sizing overlay for the ``moc_meta_v1`` family
(M3_REGISTRATION.md, "M9 auction-evolution features + calibrated sizing", Cell B).

DEPLOY-LENS ONLY. This is a REPORT + deploy-lens view — **never a gate, never a
promotion claim, never a training objective** (PROTOCOL v6 §3; the registration is
explicit: "Deploy-lens only — no promotion claim"). It answers one question: if we
had sized the SAME meta OOS event stream by calibrated conviction instead of taking
every |basis|>=10 event flat, would the per-notional-unit return and its Sharpe
improve versus (a) flat-all and (b) the M8 flat gate (P>=0.55)?

Two pieces, both pure over the M8 OOS frame (no disk, no network, no model refit
here — the OOS ``p_win`` predictions already exist):

1. ``isotonic_calibrate_oos`` — turn the raw meta ``p_win`` into a calibrated
   ``p_win_cal`` with NO LEAKAGE, reusing the walk-forward ``fold`` column already
   in ``research/experiments/M8-meta-v1/oos_predictions.parquet``. For each fold
   (in chronological order) an ``sklearn.isotonic.IsotonicRegression`` is fit on the
   pooled OOS rows of STRICTLY EARLIER folds (the "train tail" — themselves already
   out-of-sample, each carrying a realized ``y_meta`` label) and APPLIED to this
   fold's rows. A fold's calibrator therefore never sees its own rows, and the
   earliest fold (no prior folds) falls back to identity (``p_win_cal = p_win``),
   flagged by ``cal_fitted=False``. This is the honest expanding-window calibration:
   fit-train / apply-test, exactly as registered.

2. ``calibrated_sizing`` — the per-event weight
   ``w_raw = clip(p_win_cal * |basis_bps|, 0, cap)`` normalized per book to mean 1
   (a pure reallocation of a fixed total notional toward higher-conviction events),
   and the three-stream comparison (flat-all, flat-gated P>=0.55, calibrated-sized)
   on the SAME OOS events, plus the pre/post-isotonic calibration curve.

Sizing conventions (documented, deterministic):
  * Weight ``w_i = w_raw_i / mean(w_raw)`` so mean(w)=1 ("normalized per book"): the
    average deployed notional is unchanged, only its allocation shifts. A zero-mean
    edge case (all weights 0) falls back to equal weights.
  * ``cap`` clips the raw ``p_win_cal * |basis_bps|`` product so a handful of
    extreme-basis events cannot dominate the book. Default 100.0 (clips ~the top
    decile of the product on the M8 OOS frame); report-only, so it is a documented
    engineering default, not a pre-registered gate threshold.
  * net-per-notional-unit = ``sum(w * net_bps) / sum(w)`` — the notional-weighted
    mean net_bps (for flat streams w=1, so this is just the mean).
  * Sharpe of a sized stream = ``mean(x)/std(x)`` of the sized per-event pnl
    ``x_i = w_i * net_bps_i`` (for flat streams x=net_bps, matching the M8 Sharpe).
    Because mean(w)=1, ``mean(x) == net_per_notional``.
"""

from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.isotonic import IsotonicRegression

from enginev51.backtest import stress

# Column names on the M8 OOS frame (research/experiments/M8-meta-v1/oos_predictions.parquet).
PRED_COL = "p_win"
CAL_COL = "p_win_cal"
LABEL_COL = "y_meta"
NET_COL = "net_bps"
BASIS_COL = "basis_bps"
FOLD_COL = "fold"

# M8 registered headline gate (the +4.0 bps reference stream) — used here ONLY as
# the flat comparison stream, never as a sizing gate.
GATE_Q: float = 0.55

# Report-only deploy-lens sizing knobs (documented defaults; not gate thresholds).
CAP: float = 100.0
BOOK_NOTIONAL: float = 10_000.0  # research book $10k/plan (PROTOCOL v6 §3), for the $ view

# A fold's calibrator needs enough prior OOS rows (both classes present) to fit.
_MIN_CAL_ROWS = 50


# --------------------------------------------------------------------------- calibration


def isotonic_calibrate_oos(
    oos: pl.DataFrame,
    *,
    pred_col: str = PRED_COL,
    label_col: str = LABEL_COL,
    fold_col: str = FOLD_COL,
    out_col: str = CAL_COL,
) -> pl.DataFrame:
    """Add a no-leakage isotonic-calibrated ``p_win_cal`` column to the OOS frame.

    Expanding-window calibration keyed on the walk-forward ``fold`` column: folds
    are ordered chronologically; for fold *k* an ``IsotonicRegression`` is fit on
    the pooled rows of folds ``0..k-1`` (predicted ``p_win`` -> realized
    ``y_meta``) and applied to fold *k*'s ``p_win``. The calibrator for a fold
    never touches that fold's own rows (no leakage). The earliest fold has no prior
    data -> identity (``p_win_cal = p_win``), flagged ``cal_fitted=False``; a fold
    whose train tail is too thin or single-class also falls back to identity.

    Returns ``oos`` with two added columns (original row order preserved):
    ``out_col`` (calibrated probability, clipped to [0,1]) and ``cal_fitted``
    (bool: was a real isotonic map applied). Pure over ``oos``.
    """
    if oos.height == 0:
        return oos.with_columns(
            pl.lit(None, dtype=pl.Float64).alias(out_col),
            pl.lit(None, dtype=pl.Boolean).alias("cal_fitted"),
        )
    folds = sorted(oos[fold_col].unique().to_list())
    d = oos.with_row_index("_ri")
    parts: list[pl.DataFrame] = []
    for i, f in enumerate(folds):
        te = d.filter(pl.col(fold_col) == f)
        prior = d.filter(pl.col(fold_col).is_in(folds[:i])) if i else d.head(0)
        can_fit = (
            prior.height >= _MIN_CAL_ROWS
            and prior[label_col].n_unique() > 1
        )
        if can_fit:
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            iso.fit(
                prior[pred_col].to_numpy().astype(float),
                prior[label_col].to_numpy().astype(float),
            )
            cal = np.clip(iso.predict(te[pred_col].to_numpy().astype(float)), 0.0, 1.0)
            fitted = True
        else:
            cal = te[pred_col].to_numpy().astype(float)
            fitted = False
        parts.append(
            te.with_columns(
                pl.Series(out_col, cal),
                pl.lit(fitted).alias("cal_fitted"),
            )
        )
    return pl.concat(parts).sort("_ri").drop("_ri")


def calibration_curve(
    oos: pl.DataFrame,
    *,
    pred_col: str = PRED_COL,
    cal_col: str = CAL_COL,
    label_col: str = LABEL_COL,
    n_bins: int = 10,
) -> pl.DataFrame:
    """Pre/post-isotonic reliability curve (equal-count deciles by raw ``p_win``).

    Each bin reports the mean RAW predicted probability, the mean CALIBRATED
    probability, and the REALIZED win rate (``y_meta`` mean). A well-calibrated map
    pulls ``cal_mean`` onto ``realized_win_rate``; the row-level absolute deviation
    ``|pred - realized|`` should shrink from ``raw`` to ``cal``. Pure over ``oos``.
    """
    schema = {
        "bin": pl.Int64, "n": pl.Int64,
        "raw_mean": pl.Float64, "cal_mean": pl.Float64,
        "realized_win_rate": pl.Float64,
        "abs_err_raw": pl.Float64, "abs_err_cal": pl.Float64,
    }
    d = oos.select([pred_col, cal_col, label_col]).drop_nulls()
    if d.height == 0:
        return pl.DataFrame(schema=schema)
    n = d.height
    d = (
        d.sort(pred_col)
        .with_row_index("_i")
        .with_columns((pl.col("_i") * n_bins // n).clip(0, n_bins - 1).alias("bin"))
    )
    grp = (
        d.group_by("bin")
        .agg(
            pl.len().alias("n"),
            pl.col(pred_col).mean().alias("raw_mean"),
            pl.col(cal_col).mean().alias("cal_mean"),
            pl.col(label_col).cast(pl.Float64).mean().alias("realized_win_rate"),
        )
        .sort("bin")
    )
    grp = grp.with_columns(
        (pl.col("raw_mean") - pl.col("realized_win_rate")).abs().alias("abs_err_raw"),
        (pl.col("cal_mean") - pl.col("realized_win_rate")).abs().alias("abs_err_cal"),
    )
    return grp.select(list(schema)).cast(schema)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- sizing


def sizing_weights(
    df: pl.DataFrame,
    *,
    cap: float = CAP,
    cal_col: str = CAL_COL,
    basis_col: str = BASIS_COL,
) -> tuple[np.ndarray, np.ndarray]:
    """(normalized weights, raw pre-normalization weights) for the sized stream.

    ``w_raw = clip(p_win_cal * |basis_bps|, 0, cap)``; ``w = w_raw / mean(w_raw)``
    so mean(w)=1 (normalized per book). All-zero raw weights -> equal weights.
    Pure over ``df``.
    """
    if df.height == 0:
        return np.array([]), np.array([])
    raw = np.clip(
        df[cal_col].to_numpy().astype(float) * np.abs(df[basis_col].to_numpy().astype(float)),
        0.0,
        cap,
    )
    m = float(raw.mean())
    w = raw / m if m > 0 else np.ones_like(raw)
    return w, raw


def _sharpe(x: np.ndarray) -> tuple[float, float]:
    """(std, Sharpe=mean/std) of a per-event series, sample std (ddof=1)."""
    if x.size < 2:
        return float("nan"), float("nan")
    sd = float(np.std(x, ddof=1))
    mean = float(np.mean(x))
    return sd, (mean / sd if sd > 0 else float("nan"))


def _stream_row(
    label: str,
    df: pl.DataFrame,
    weights: np.ndarray | None,
) -> dict:
    """One comparison-table row. ``weights=None`` -> flat (equal-weight) stream."""
    if df.height == 0:
        return {
            "stream": label, "n": 0, "n_sessions": 0, "hit_rate": None,
            "net_per_notional_bps": None, "ci_lo": None, "ci_hi": None,
            "pnl_std_bps": None, "sharpe": None,
        }
    net = df[NET_COL].to_numpy().astype(float)
    w = np.ones_like(net) if weights is None else weights
    pnl = w * net  # sized per-event pnl (bps per unit of average notional)
    total_w = float(w.sum())
    net_per_notional = float((w * net).sum() / total_w) if total_w > 0 else float("nan")
    sd, sharpe = _sharpe(pnl)
    # Day-clustered CI on the sized per-event pnl (session = cluster unit, §4).
    m, lo, hi = stress.clustered_mean_ci(pnl, df["session"].to_numpy())
    return {
        "stream": label,
        "n": df.height,
        "n_sessions": int(df["session"].n_unique()),
        "hit_rate": round(float((net > 0).mean()), 4),
        "net_per_notional_bps": round(net_per_notional, 3),
        "ci_lo": round(lo, 3),
        "ci_hi": round(hi, 3),
        "pnl_std_bps": round(sd, 3),
        "sharpe": round(sharpe, 4),
    }


def calibrated_sizing(
    oos: pl.DataFrame,
    *,
    cap: float = CAP,
    gate_q: float = GATE_Q,
    pred_col: str = PRED_COL,
) -> dict:
    """M9 Cell B deploy-lens report over the M8 OOS predictions frame.

    Steps: (1) no-leakage isotonic calibration of ``p_win`` -> ``p_win_cal``;
    (2) three streams on the SAME OOS events — ``flat_all`` (every event, equal
    weight), ``flat_gated`` (raw P(win) >= ``gate_q``, equal weight — the M8 gate),
    ``calibrated_sized`` (every event, weight = clip(p_win_cal*|basis|,0,cap)
    normalized per book); (3) the pre/post-isotonic calibration curve.

    Returns a dict:
      * ``sized`` — the OOS frame + ``p_win_cal``/``cal_fitted``/``weight`` columns;
      * ``table`` — the three-stream comparison (net-per-notional-unit + Sharpe,
        day-clustered CI on the sized pnl);
      * ``calibration_curve`` — pre/post-isotonic reliability deciles;
      * ``summary`` — headline scalars (Sharpe & net/unit per stream, the deploy
        verdict Sharpe(sized) vs Sharpe(flat gated), calibration MAE pre/post).

    NEVER a gate: this function returns a report; nothing here selects trades or
    feeds a training objective (PROTOCOL v6 §3, M9 Cell B registration).
    """
    cal = isotonic_calibrate_oos(oos, pred_col=pred_col)
    w, _raw = sizing_weights(cal, cap=cap)
    sized = cal.with_columns(pl.Series("weight", w) if cal.height else pl.lit(None).alias("weight"))

    gated = (
        cal.filter(pl.col(pred_col) >= gate_q) if cal.height else cal
    )

    rows = [
        _stream_row("flat_all", cal, None),
        _stream_row(f"flat_gated_P>={gate_q:.2f}", gated, None),
        _stream_row("calibrated_sized", cal, w),
    ]
    table = pl.DataFrame(
        rows,
        schema={
            "stream": pl.Utf8, "n": pl.Int64, "n_sessions": pl.Int64,
            "hit_rate": pl.Float64, "net_per_notional_bps": pl.Float64,
            "ci_lo": pl.Float64, "ci_hi": pl.Float64, "pnl_std_bps": pl.Float64,
            "sharpe": pl.Float64,
        },
        orient="row",
    )
    curve = calibration_curve(cal)

    def _get(label: str, field: str):
        r = next((x for x in rows if x["stream"] == label), None)
        return r[field] if r else None

    gated_label = f"flat_gated_P>={gate_q:.2f}"
    sharpe_sized = _get("calibrated_sized", "sharpe")
    sharpe_gated = _get(gated_label, "sharpe")
    sharpe_flat = _get("flat_all", "sharpe")
    mae_raw = float(curve["abs_err_raw"].mean()) if curve.height else float("nan")
    mae_cal = float(curve["abs_err_cal"].mean()) if curve.height else float("nan")

    summary = {
        "cap": cap,
        "gate_q": gate_q,
        "n_events": cal.height,
        "n_folds": int(cal[FOLD_COL].n_unique()) if cal.height else 0,
        "n_cal_fitted_events": int(cal.filter(pl.col("cal_fitted")).height) if cal.height else 0,
        "weight_clip_fraction": round(float((_raw >= cap).mean()), 4) if _raw.size else None,
        "sharpe_flat_all": sharpe_flat,
        "sharpe_flat_gated": sharpe_gated,
        "sharpe_calibrated_sized": sharpe_sized,
        "net_per_unit_flat_all": _get("flat_all", "net_per_notional_bps"),
        "net_per_unit_flat_gated": _get(gated_label, "net_per_notional_bps"),
        "net_per_unit_calibrated_sized": _get("calibrated_sized", "net_per_notional_bps"),
        "sized_beats_flat_gated_sharpe": bool(
            sharpe_sized is not None and sharpe_gated is not None
            and np.isfinite(sharpe_sized) and np.isfinite(sharpe_gated)
            and sharpe_sized > sharpe_gated
        ),
        "calibration_mae_raw": round(mae_raw, 4) if np.isfinite(mae_raw) else None,
        "calibration_mae_cal": round(mae_cal, 4) if np.isfinite(mae_cal) else None,
        "calibration_improved": bool(
            np.isfinite(mae_raw) and np.isfinite(mae_cal) and mae_cal < mae_raw
        ),
    }
    return {
        "sized": sized,
        "table": table,
        "calibration_curve": curve,
        "summary": summary,
    }
