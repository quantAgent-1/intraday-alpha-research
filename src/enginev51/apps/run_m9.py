"""M9 auction-evolution runner (``moc_meta_v1``, Cell A) — THE DECISIVE PROBE of
the sequence-modeling thesis (M3_REGISTRATION.md, "M9 auction-evolution features +
calibrated sizing — registered 2026-07-17").

Question: does the auction's PATH over the legal decision window
``[15:50:00, 15:55:10]`` ET carry reliability signal the M8 SNAPSHOT throws away?
Cell A adds EXACTLY the five registered path scalars (imb_velocity, imb_accel,
near_conv_slope, near_jitter, paired_frac_slope; winsorized 1/99 per fold) to the
M8 meta feature set and retrains the SAME binary P(win) meta-GBDT under the SAME
walk-forward folds and the SAME gate. Everything else is held fixed.

Pipeline:

    M6-FINAL events.parquet  (already fill-verified, < 2026-06-01)
      -> candidates = |basis_bps| >= 10 (M8 universe), meta-label y=(net_bps>0)
      -> materialize the 5 evolution scalars from the NOII STREAM over
         [15:50, 15:55:10] (side/m0/adv20 taken from the events row so signed_basis
         at 15:55:10 == |basis_bps|; leakage-invariant, unit-tested)
      -> ONE walk-forward loop (moc_gbm folds), per fold training BOTH:
           * snapshot-GBDT  (M8 FEATURE_COLS)                     -> p_win_snap
           * evo-GBDT       (M8 FEATURE_COLS + 5 winsorized evo)  -> p_win_evo
         on IDENTICAL rows -> paired by construction.
      -> gate q>=0.55 (the registered M9 comparison gate) + q in {0.50,0.60} shown.
      -> report.md: baseline vs snapshot-gated vs evo-gated (n, hit, mean + day-
         clustered CI, Sharpe), per-symbol, per-year, evo-GBDT feature importances
         (do the evo features rank above noise? are they used?), and the DECISIVE
         paired table — evo-gated CI-lower vs snapshot-gated mean (registered M9
         success) AND the per-session paired book-delta (evo - snapshot) CI.

Registered M9 success (Cell A): evo-gated (P>=0.55) net_bps CI-lower > the M8
snapshot-GBDT gated MEAN, AND holds across >=3 symbols and >=3 years. Null (<=) =>
the sequence-modeling thesis is dead, documented. This app writes NO ledger row and
NO pass/fail verdict (the orchestrator owns the verdict); the seal is SPENT but the
events are entirely < 2026-06-01 and this app asserts it (walk-forward OOS only).

    uv run python -m enginev51.apps.run_m9 --trial-id M9-evo-v1 \
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
from enginev51.models import lgbm as lgbm_model
from enginev51.models.evolution_features import (
    EVO_FEATURES,
    apply_winsor,
    evo_features,
    fit_winsor_bounds,
)
from enginev51.models.moc_gbm import walk_forward_folds_calendar
from enginev51.models.moc_meta import (
    CANDIDATE_BASIS_BPS,
    FEATURE_COLS,
    LABEL_COL,
    META_PARAMS,
    NET_COL,
    build_meta_frame,
    calibration_table,
)
from enginev51.protocol import HOLDOUT_START, SealViolation, experiments_dir, split_of

log = structlog.get_logger(__name__)

DEFAULT_EVENTS = "research/experiments/M6-FINAL-basis/events.parquet"
BOOK_NOTIONAL = 10_000.0  # research book: $10k fixed notional per plan (PROTOCOL v6 §3)

# The registered M9 comparison gate. q in {0.50, 0.60} are shown for context.
COMPARE_GATE: float = 0.55
GATES: tuple[float, ...] = (0.50, 0.55, 0.60)

P_SNAP = "p_win_snap"
P_EVO = "p_win_evo"

# Combined evo-GBDT feature list (M8 snapshot set + the 5 registered evo scalars).
EVO_MODEL_FEATURES: tuple[str, ...] = FEATURE_COLS + EVO_FEATURES


# --------------------------------------------------------------------------- evo frame


def build_evo_frame(meta: pl.DataFrame, *, noii_dir=None) -> pl.DataFrame:
    """Materialize the 5 raw evolution scalars onto every M8 candidate row.

    ``side``/``m0(=entry_mid)``/``adv20(=adv20_dollars)`` come from the events row
    (decision-instant fixed scalars) so ``signed_basis`` at 15:55:10 equals
    ``|basis_bps|`` — the leakage invariant. The RAW (whole-month) NOII partition is
    read once per (symbol, month) and cached; ``evo_features`` selects the correct
    session by absolute timestamp (``_window_stream`` filters ts to that session's
    [15:50, 15:55:10]), so the month cache is shared safely across its sessions.
    Adds ``EVO_FEATURES`` columns (raw, un-winsorized) + a diagnostic
    ``evo_all_present`` flag."""
    from enginev51.data.noii import noii_root, partition_path

    root = noii_root(noii_dir)
    cache: dict[tuple[str, str], pl.DataFrame | None] = {}

    def _noii(sym: str, session: str) -> pl.DataFrame | None:
        key = (sym, session[:7])
        if key not in cache:
            path = partition_path(root, sym, session[:7])
            cache[key] = pl.read_parquet(path) if path.exists() else None
        return cache[key]

    cols: dict[str, list] = {c: [] for c in EVO_FEATURES}
    present_all: list[bool] = []
    for r in meta.iter_rows(named=True):
        sym = r["symbol"]
        nf = _noii(sym, r["session"])
        f = evo_features(
            sym,
            r["session"],
            adv20=r["adv20_dollars"],
            side=int(r["side"]),
            m0=float(r["entry_mid"]),
            noii_frame=nf,
        )
        for c in EVO_FEATURES:
            cols[c].append(float(f[c]))
        present_all.append(all(f[f"{c}_present"] for c in EVO_FEATURES))

    return meta.with_columns(
        [pl.Series(c, cols[c], dtype=pl.Float64) for c in EVO_FEATURES]
        + [pl.Series("evo_all_present", present_all, dtype=pl.Boolean)]
    )


# --------------------------------------------------------------------------- walk-forward


def run_paired_walk_forward(
    frame: pl.DataFrame,
    *,
    initial_train_years: int = 2,
    test_block_months: int = 6,
    embargo_sessions: int = 1,
) -> tuple[pl.DataFrame, pl.DataFrame, list]:
    """ONE expanding walk-forward producing BOTH models' OOS P(win) on identical rows.

    Reuses ``moc_gbm.walk_forward_folds_calendar`` EXACTLY (>=2y initial train,
    6-month blocks, 1-session embargo) — the same folds M8 used. Per fold:
      * snapshot-GBDT: binary classifier on ``FEATURE_COLS`` (M8) -> ``p_win_snap``;
      * evo-GBDT: winsor bounds FIT on the train fold (1/99) applied to train AND
        test, binary classifier on ``FEATURE_COLS + EVO_FEATURES`` -> ``p_win_evo``.
    Both share the fold's exact PIT train set, so the two OOS streams are paired
    row-for-row. Returns ``(oos_df, evo_importances_df, folds)``."""
    sessions = sorted(frame["session"].unique().to_list())
    folds = walk_forward_folds_calendar(
        sessions,
        initial_train_years=initial_train_years,
        test_block_months=test_block_months,
        embargo_sessions=embargo_sessions,
    )
    oos_parts: list[pl.DataFrame] = []
    imp_accum: dict[str, list[float]] = {c: [] for c in EVO_MODEL_FEATURES}
    for fold in folds:
        tr = frame.filter(pl.col("session").is_in(list(fold.train_sessions)))
        te = frame.filter(pl.col("session").is_in(list(fold.test_sessions)))
        if tr.height == 0 or te.height == 0:
            continue
        # PIT guard (defence in depth): no training row at/after the test-block start.
        assert (tr["session"].max() or "") < fold.test_start, (
            f"leakage: train row >= test_start {fold.test_start}"
        )

        # snapshot-GBDT (identical to M8).
        b_snap = lgbm_model.train_one(tr, FEATURE_COLS, LABEL_COL, params=META_PARAMS)
        p_snap = lgbm_model.predict(b_snap, te, FEATURE_COLS)

        # evo-GBDT: winsorize (train-fit bounds), then train on the extended set.
        bounds = fit_winsor_bounds(tr, EVO_FEATURES)
        tr_w = apply_winsor(tr, bounds)
        te_w = apply_winsor(te, bounds)
        b_evo = lgbm_model.train_one(tr_w, EVO_MODEL_FEATURES, LABEL_COL, params=META_PARAMS)
        p_evo = lgbm_model.predict(b_evo, te_w, EVO_MODEL_FEATURES)

        oos_parts.append(
            te.with_columns(
                pl.Series(P_SNAP, p_snap),
                pl.Series(P_EVO, p_evo),
                pl.lit(fold.test_start).alias("fold"),
            )
        )
        gains = b_evo.feature_importance(importance_type="gain")
        names = b_evo.feature_name()
        for name, g in zip(names, gains, strict=True):
            if name in imp_accum:
                imp_accum[name].append(float(g))

    oos_df = (
        pl.concat(oos_parts)
        if oos_parts
        else frame.head(0).with_columns(
            pl.lit(None, dtype=pl.Float64).alias(P_SNAP),
            pl.lit(None, dtype=pl.Float64).alias(P_EVO),
            pl.lit(None, dtype=pl.Utf8).alias("fold"),
        )
    )
    imp_rows = [
        {
            "feature": c,
            "mean_gain": float(np.mean(imp_accum[c])) if imp_accum[c] else 0.0,
            "n_folds": len(imp_accum[c]),
            "is_evo": c in EVO_FEATURES,
        }
        for c in EVO_MODEL_FEATURES
    ]
    importances_df = pl.DataFrame(
        imp_rows,
        schema={"feature": pl.Utf8, "mean_gain": pl.Float64, "n_folds": pl.Int64, "is_evo": pl.Boolean},
    ).sort("mean_gain", descending=True)
    return oos_df, importances_df, folds


# --------------------------------------------------------------------------- metrics


def _ci(df: pl.DataFrame) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n, n_sessions) day-clustered over net_bps."""
    if df.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    m, lo, hi = stress.clustered_mean_ci(df[NET_COL].to_numpy(), df["session"].to_numpy())
    return m, lo, hi, df.height, df["session"].n_unique()


def _hit_rate(df: pl.DataFrame) -> float:
    if df.height == 0:
        return float("nan")
    return float((df[NET_COL] > 0.0).cast(pl.Float64).mean())


def _sharpe(df: pl.DataFrame) -> tuple[float, float]:
    if df.height < 2:
        return float("nan"), float("nan")
    net = df[NET_COL].to_numpy()
    sd = float(np.std(net, ddof=1))
    return sd, (float(np.mean(net)) / sd if sd > 0 else float("nan"))


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
            "hit_rate": pl.Float64, "net_bps_mean": pl.Float64, "ci_lo": pl.Float64,
            "ci_hi": pl.Float64, "net_bps_std": pl.Float64, "sharpe": pl.Float64,
        },
        orient="row",
    )


def _year_col(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.col("session").str.slice(0, 4).alias("year"))


def _compare_by_key(streams: dict[str, pl.DataFrame], key: str) -> pl.DataFrame:
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
            row[f"{label}|mean"] = round(float(sub[NET_COL].mean()), 2) if sub.height else None
        rows.append(row)
    return pl.DataFrame(rows, orient="row") if rows else pl.DataFrame({key: []})


# --------------------------------------------------------------------------- paired


def paired_book_delta(oos: pl.DataFrame, q: float) -> dict:
    """The DECISIVE paired comparison: per-session BOOK net delta (evo - snapshot).

    On the SAME OOS session universe, sum the taken ``net_bps`` per session under
    the evo gate (P_evo>=q) and the snapshot gate (P_snap>=q); the per-session
    delta (0 where a gate took nothing) is a paired sample (same sessions), whose
    day-clustered mean CI answers 'does the evo-GBDT capture more book than the
    snapshot-GBDT on identical sessions?'. Positive CI-lower > 0 => evo wins at the
    book level. Also carries the per-notional (bps/plan) point deltas."""
    if oos.height == 0:
        return {"n_sessions": 0}
    sess = sorted(oos["session"].unique().to_list())
    evo_g = oos.filter(pl.col(P_EVO) >= q)
    snap_g = oos.filter(pl.col(P_SNAP) >= q)
    evo_by = dict(
        zip(*evo_g.group_by("session").agg(pl.col(NET_COL).sum()).to_dict(as_series=False).values(), strict=True)
    ) if evo_g.height else {}
    snap_by = dict(
        zip(*snap_g.group_by("session").agg(pl.col(NET_COL).sum()).to_dict(as_series=False).values(), strict=True)
    ) if snap_g.height else {}
    deltas = np.array([float(evo_by.get(s, 0.0)) - float(snap_by.get(s, 0.0)) for s in sess])
    sess_arr = np.array(sess)
    m, lo, hi = stress.clustered_mean_ci(deltas, sess_arr)
    evo_m = float(evo_g[NET_COL].mean()) if evo_g.height else float("nan")
    snap_m = float(snap_g[NET_COL].mean()) if snap_g.height else float("nan")
    return {
        "gate": q,
        "n_sessions": len(sess),
        "evo_gated_n": evo_g.height,
        "snap_gated_n": snap_g.height,
        "per_session_book_delta_mean": round(m, 4),
        "per_session_book_delta_ci_lo": round(lo, 4),
        "per_session_book_delta_ci_hi": round(hi, 4),
        "book_delta_ci_lo_gt_0": bool(lo > 0),
        "evo_gated_bps_mean": round(evo_m, 3) if evo_g.height else None,
        "snap_gated_bps_mean": round(snap_m, 3) if snap_g.height else None,
        "bps_mean_delta_evo_minus_snap": round(evo_m - snap_m, 3)
        if (evo_g.height and snap_g.height) else None,
    }


def registered_success_echo(oos: pl.DataFrame, q: float = COMPARE_GATE) -> dict:
    """Diagnostic echo of the registered M9 Cell-A success (NOT a verdict).

    Success: evo-gated (P>=q) net_bps CI-LOWER > the snapshot-gated MEAN, AND the
    evo-gated stream holds across >=3 symbols and >=3 years. Also reports the
    snapshot-gated CI-lower vs baseline for context."""
    evo_g = oos.filter(pl.col(P_EVO) >= q)
    snap_g = oos.filter(pl.col(P_SNAP) >= q)
    e_m, e_lo, _e_hi, e_n, _ = _ci(evo_g)
    s_m, s_lo, _s_hi, s_n, _ = _ci(snap_g)
    _e_sd, e_sh = _sharpe(evo_g)
    _s_sd, s_sh = _sharpe(snap_g)
    syms = sorted(evo_g["symbol"].unique().to_list()) if evo_g.height else []
    years = sorted({s[:4] for s in evo_g["session"].to_list()}) if evo_g.height else []
    return {
        "gate": q,
        "snapshot_gated": {
            "n": s_n, "hit_rate": round(_hit_rate(snap_g), 4) if s_n else None,
            "net_mean": round(s_m, 3) if s_n else None,
            "ci_lo": round(s_lo, 3) if s_n else None,
            "sharpe": round(s_sh, 4) if s_n >= 2 else None,
        },
        "evo_gated": {
            "n": e_n, "hit_rate": round(_hit_rate(evo_g), 4) if e_n else None,
            "net_mean": round(e_m, 3) if e_n else None,
            "ci_lo": round(e_lo, 3) if e_n else None,
            "sharpe": round(e_sh, 4) if e_n >= 2 else None,
            "n_symbols": len(syms), "n_years": len(years),
        },
        "evo_ci_lo_gt_snapshot_mean": bool(e_n and s_n and e_lo > s_m),
        "spans_ge_3_symbols_and_3_years": bool(len(syms) >= 3 and len(years) >= 3),
        "REGISTERED_M9_SUCCESS": bool(
            e_n and s_n and e_lo > s_m and len(syms) >= 3 and len(years) >= 3
        ),
    }


# --------------------------------------------------------------------------- report


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


def build_streams(oos: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Ordered streams on the SAME OOS span: baseline (ungated) + snapshot/evo gated
    at the registered comparison gate + the {0.50, 0.60} context gates."""
    streams: dict[str, pl.DataFrame] = {"baseline (ungated)": oos}
    if oos.height:
        streams[f"snapshot q>={COMPARE_GATE:.2f}"] = oos.filter(pl.col(P_SNAP) >= COMPARE_GATE)
        streams[f"evo q>={COMPARE_GATE:.2f}"] = oos.filter(pl.col(P_EVO) >= COMPARE_GATE)
        for q in (0.50, 0.60):
            streams[f"snapshot q>={q:.2f}"] = oos.filter(pl.col(P_SNAP) >= q)
            streams[f"evo q>={q:.2f}"] = oos.filter(pl.col(P_EVO) >= q)
    return streams


def build_report_md(
    trial_id: str, oos: pl.DataFrame, streams: dict[str, pl.DataFrame],
    importances: pl.DataFrame, folds, counts: dict, seed: int,
) -> str:
    oos_years = sorted({s[:4] for s in oos["session"].to_list()}) if oos.height else []
    oos_symbols = sorted(oos["symbol"].unique().to_list()) if oos.height else []
    fold_meta = [
        {"test_start": f.test_start, "test_end": f.test_end,
         "n_train": len(f.train_sessions), "n_test": len(f.test_sessions)}
        for f in folds
    ]
    # gate-focused streams for the headline comparison table.
    headline = {k: v for k, v in streams.items() if COMPARE_GATE == 0.55 and (
        k == "baseline (ungated)" or k.endswith("q>=0.55")
    )}
    evo_rank = None
    if importances.height:
        ir = importances.with_row_index("rank")
        evo_ranks = ir.filter(pl.col("is_evo")).select(["rank", "feature", "mean_gain"])
        evo_rank = evo_ranks.to_dicts()
    used = [r["feature"] for r in importances.filter(pl.col("mean_gain") > 0).to_dicts()] \
        if importances.height else []
    evo_used = [c for c in EVO_FEATURES if c in used]

    md: list[str] = [
        f"# M9 auction-evolution report — {trial_id}",
        "",
        "Family `moc_meta_v1`, Cell A (registered 2026-07-17) — THE DECISIVE PROBE "
        "of the sequence-modeling thesis. The M8 meta-GBDT scores the classical "
        f"|basis|>={CANDIDATE_BASIS_BPS:.0f}bps rule from a SNAPSHOT at 15:55:10 ET. "
        "M9 adds EXACTLY 5 registered PATH scalars over the legal decision window "
        "[15:50:00, 15:55:10] ET (imb_velocity, imb_accel, near_conv_slope, "
        "near_jitter, paired_frac_slope; winsorized 1/99 per fold) and retrains the "
        "SAME binary P(win) GBDT on the SAME walk-forward folds with the SAME gate. "
        "Snapshot-GBDT is the M8 baseline (identical folds/gate). Walk-forward OOS "
        "only (POST-HOLDOUT; forward paper is the sole clean validation). NO ledger "
        "writes; NO pass/fail verdict.",
        "",
        f"seed={seed}    snapshot_features={len(FEATURE_COLS)}    "
        f"evo_features=+{len(EVO_FEATURES)} ({', '.join(EVO_FEATURES)})    "
        "model=LightGBM(objective=binary) on y=(net_bps>0)",
        f"OOS span: {oos.height} candidates    symbols {oos_symbols}    years {oos_years}",
        f"Splits present: "
        f"{sorted({split_of(s) for s in oos['session'].unique()}) if oos.height else []}",
        "",
        "## 0. Funnel",
        "```",
        json.dumps(counts, indent=2, default=str),
        "```",
        "",
        "## 1. Walk-forward folds (expanding, >=2y train, 6-mo blocks, 1-session embargo)",
        "",
        "Identical fold builder to models/moc_gbm (reused). Each fold trains BOTH "
        "models on the SAME PIT train set, so the snapshot and evo OOS streams are "
        "paired row-for-row. Evo winsor bounds (1/99) are FIT on the train fold and "
        "applied to train+test — no test statistic touches a training bound.",
        "```",
        json.dumps(fold_meta, indent=2, default=str),
        "```",
        "",
        "## 2. Headline comparison (q>=0.55) — baseline vs snapshot-GBDT vs evo-GBDT",
        "",
        "SAME OOS span. net_bps mean CI day-clustered (session = cluster). Sharpe = "
        "per-trade mean/std. hit_rate = fraction net_bps>0.",
        "",
        _ascii(comparison_table(headline if headline else streams)),
        "",
        "## 3. DECISIVE paired ablation (evo-GBDT vs snapshot-GBDT, same OOS)",
        "",
        "Registered M9 success (Cell A): evo-gated (P>=0.55) net_bps CI-LOWER > the "
        "snapshot-gated MEAN, AND holds across >=3 symbols and >=3 years. Plus the "
        "per-session BOOK delta (evo - snapshot) on identical sessions (paired; "
        "day-clustered CI). If evo does NOT beat snapshot here, the sequence-"
        "modeling thesis is dead (documented, not hidden).",
        "```",
        json.dumps(registered_success_echo(oos, COMPARE_GATE), indent=2, default=str),
        "```",
        "",
        "Per-session paired book-delta (evo - snapshot), each registered/context gate:",
        "```",
        json.dumps([paired_book_delta(oos, q) for q in GATES], indent=2, default=str)
        if oos.height else "[]",
        "```",
        "",
        "## 4. All gates side-by-side (snapshot vs evo at q in {0.50, 0.55, 0.60})",
        "",
        _ascii(comparison_table(streams)),
        "",
        "## 5. Per-symbol (n + mean net_bps per stream)",
        "",
        _ascii(_compare_by_key(streams, "symbol")),
        "",
        "## 6. Per-year (n + mean net_bps per stream)",
        "",
        _ascii(_compare_by_key({k: _year_col(v) for k, v in streams.items()}, "year")),
        "",
        "## 7. evo-GBDT feature importances (mean LightGBM gain across folds)",
        "",
        "Do the evo features rank above noise (the symbol one-hots / the weakest "
        "snapshot features are the noise floor)? Are they used at all?",
        f"evo features USED (gain>0): {evo_used}",
        f"evo feature ranks: {json.dumps(evo_rank, default=str)}",
        "",
        _ascii(importances),
        "",
        "## 8. Calibration — evo P(win) decile vs realized win rate (OOS)",
        "",
        "Equal-count deciles by predicted evo P(win); realized_win_rate is the "
        "realized fraction of winners. Monotone rising => the score ranks reliability.",
        "",
        _ascii(calibration_table(oos, pred_col=P_EVO)) if oos.height else "(no OOS)",
        "",
    ]
    return "\n".join(md)


def write_outputs(out_dir: Path, oos: pl.DataFrame, report_md: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    oos_path = out_dir / "oos_predictions.parquet"
    report_path = out_dir / "report.md"
    oos.write_parquet(oos_path)
    report_path.write_text(report_md, encoding="utf-8")
    return oos_path, report_path


def evaluate(events: pl.DataFrame, *, noii_dir=None) -> dict:
    """Build the meta frame, materialize evo features, run the paired walk-forward.

    Pure over ``events`` given the data lake (LightGBM seed fixed in META_PARAMS/
    DEFAULT_PARAMS)."""
    n_cand_raw = events.filter(pl.col("basis_bps").abs() >= CANDIDATE_BASIS_BPS).height
    meta = build_meta_frame(events)
    evo = build_evo_frame(meta, noii_dir=noii_dir)
    counts = {
        "events_rows": events.height,
        "candidates_basis_ge_10": n_cand_raw,
        "candidates_labeled": meta.height,
        "candidates_dropped_null_net": n_cand_raw - meta.height,
        "evo_all_present_rows": int(evo["evo_all_present"].sum()),
        "win_rate_all_candidates": round(float((meta[NET_COL] > 0).mean()), 4)
        if meta.height else None,
    }
    oos, importances, folds = run_paired_walk_forward(evo)
    streams = build_streams(oos)
    return {
        "meta": meta, "evo": evo, "counts": counts, "oos": oos,
        "importances": importances, "folds": folds, "streams": streams,
    }


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--trial-id", default="M9-evo-v1", help="Experiment id -> research/experiments/<id>/.")
@click.option("--events", default=DEFAULT_EVENTS, help="M6-FINAL events.parquet (candidates + snapshot features).")
@click.option("--noii-dir", default=None, help="NOII lake root (default data/raw/noii).")
@click.option("--seed", default=7, type=int, help="Reproducibility echo (model seed is lgbm.DEFAULT_PARAMS).")
def main(trial_id: str, events: str, noii_dir: str | None, seed: int) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety

    events_df = pl.read_parquet(events)
    if (events_df["session"].max() or "") >= HOLDOUT_START.isoformat():
        raise SealViolation(
            "events reach the sealed holdout — refusing (PROTOCOL v6 §1); walk-forward "
            "evaluation uses < 2026-06-01 only"
        )

    t0 = time.time()
    ev = evaluate(events_df, noii_dir=noii_dir)
    report_md = build_report_md(
        trial_id, ev["oos"], ev["streams"], ev["importances"], ev["folds"],
        ev["counts"], seed,
    )
    wall = time.time() - t0

    out_dir = experiments_dir() / trial_id
    oos_path, report_path = write_outputs(out_dir, ev["oos"], report_md)

    click.echo(f"trial: {trial_id}  events={events}  seed={seed}")
    click.echo(f"funnel: {json.dumps(ev['counts'], default=str)}")
    click.echo(f"folds: {len(ev['folds'])}  OOS candidates: {ev['oos'].height}")
    click.echo("")
    click.echo(_ascii(comparison_table(ev["streams"])))
    click.echo("")
    click.echo("registered M9 success echo:")
    click.echo(json.dumps(registered_success_echo(ev["oos"], COMPARE_GATE), indent=2, default=str))
    click.echo("")
    click.echo(f"oos:    {oos_path}")
    click.echo(f"report: {report_path}")
    click.echo(f"wall: {wall:.1f}s")


if __name__ == "__main__":
    main()
