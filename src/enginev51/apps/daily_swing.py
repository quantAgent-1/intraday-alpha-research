"""daily_swing_v1 — the registered daily 1d/3d/5d side-ledger trial.

RESEARCH-ONLY. This is the user-approved (2026-07-15) daily side-ledger family
(PROTOCOL v6 §2; M3_REGISTRATION "Daily side-ledger family"): rank-IC bookkeeping
on overnight-horizon LightGBM forecasts. It makes NO plan-level claim, writes NO
ledger row, and the deployable system never holds overnight — the orchestrator
owns verdicts. Output is a report + an IC table, nothing else.

Pipeline (per the task spec):
  1. For each of the 12 bar_signal symbols, load data/features/<v>/<SYM>.parquet and
     take the LAST row per session (the ~near-close feature vector). The `close` of
     that row is the daily close; f_vol20 is the trailing 20-session daily vol.
  2. Labels are SESSION-INDEXED (calendar-safe): l_fwd_{h}d = log(close[t+h]/close[t])
     where the shift is by session-row position within a symbol, never by calendar
     days. Vol-normalized z_{h}d = l_fwd_{h}d / (f_vol20 * sqrt(h)). The holdout
     (session >= HOLDOUT_START) is stripped BEFORE the shift, so no label can ever
     reference a sealed close; rows AND labels for holdout sessions are excluded
     entirely (asserted).
  3. One pooled cross-symbol LightGBM per horizon (models/lgbm.train_one,
     DEFAULT_PARAMS), fit on a purged expanding walk-forward
     (models/cv.walk_forward_folds) with embargo_sessions=6 (> the longest 5d
     horizon; passed explicitly and guarded).
  4. Evaluate: per-session cross-sectional rank-IC with a day-clustered bootstrap CI
     (pooled across the 12 names), plus per-symbol time-series rank-IC for NVDA and
     TSLA (the grok E5 comparison arm). See CROSS_SECTION_MIN_SYMBOLS note below.

    uv run python -m enginev51.apps.daily_swing --feature-version v1 --out daily-swing-v1
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import click
import numpy as np
import polars as pl
import structlog

from enginev51.config import Settings, get_research_config, get_settings
from enginev51.features import slow
from enginev51.models import cv, evaluate, lgbm
from enginev51.protocol import HOLDOUT_START, SealViolation, apply_seal, experiments_dir

log = structlog.get_logger(__name__)

TRIAL_ID = "daily_swing_v1"
HORIZONS: tuple[int, ...] = (1, 3, 5)
LONGEST_HORIZON = 5
# Embargo strictly greater than the longest label horizon (5 sessions). Passed
# explicitly to walk_forward_folds; guarded at run() entry.
EMBARGO_SESSIONS = 6

FEATURE_COLS: tuple[str, ...] = tuple(slow.FEATURE_COLS)
VOL_COL = "f_vol20"

# per_session_ic (models/evaluate) gates sessions at n >= 30 rows, which is right
# for INTRADAY pooled cross-sections but drops every DAILY cross-section (only 12
# names per session). The pooled metric here is a genuine 12-name cross-sectional
# rank-IC, so we mirror per_session_ic's Spearman-on-ranks formula with a daily-
# appropriate minimum and feed the per-session series to evaluate.bootstrap_mean_ci
# (the day-clustered bootstrap the protocol specifies). Documented judgment call.
CROSS_SECTION_MIN_SYMBOLS = 5

# grok E5's per-symbol time-series IC claims (~43 sessions) we compare against.
GROK_E5_CLAIMS: dict[tuple[str, int], float] = {
    ("TSLA", 1): 0.23,
    ("TSLA", 5): 0.45,
    ("NVDA", 1): 0.27,
}


# --------------------------------------------------------------------------- daily frame


def _feature_dir(settings: Settings, version: str) -> Path:
    return settings.data_dir / "features" / version


def last_row_per_session(df: pl.DataFrame) -> pl.DataFrame:
    """The near-close feature vector: the last (max-ts) row of each session.

    Pure. `df` is one symbol's feature frame; returns one row per session."""
    keep = ["symbol", "session", "ts", "close", VOL_COL, *FEATURE_COLS]
    keep = list(dict.fromkeys(keep))
    return (
        df.sort("ts")
        .group_by("session")
        .agg([pl.col(c).last() for c in keep if c != "session"])
        .select(keep)
        .sort("session")
    )


def add_session_labels(daily: pl.DataFrame, horizons: tuple[int, ...] = HORIZONS) -> pl.DataFrame:
    """SESSION-INDEXED forward log returns + vol-normalized z, per symbol.

    The shift is by session-row position WITHIN a symbol (`.over("symbol")` on a
    frame sorted by (symbol, session)), so a calendar gap (weekend/holiday/missing
    session) never leaks: l_fwd_1d is always the *next existing session*, never
    "tomorrow's date". Call AFTER the seal so close[t+h] cannot touch the holdout.
    """
    daily = daily.sort(["symbol", "session"])
    label_exprs = [
        (pl.col("close").shift(-h) / pl.col("close")).log().over("symbol").alias(f"l_fwd_{h}d")
        for h in horizons
    ]
    daily = daily.with_columns(label_exprs)
    z_exprs = [
        pl.when(pl.col(VOL_COL) > 0)
        .then(pl.col(f"l_fwd_{h}d") / (pl.col(VOL_COL) * math.sqrt(h)))
        .otherwise(None)
        .alias(f"z_{h}d")
        for h in horizons
    ]
    return daily.with_columns(z_exprs)


def build_daily_pool(settings: Settings, version: str, symbols: list[str]) -> pl.DataFrame:
    """Load every signal symbol, reduce to near-close daily rows, seal, then label.

    Sealing BEFORE labelling is the calendar-safe, leak-safe order: holdout closes
    can never enter a pre-holdout label. Raises SealViolation if a holdout row
    survives."""
    fdir = _feature_dir(settings, version)
    frames: list[pl.DataFrame] = []
    for s in symbols:
        p = fdir / f"{s}.parquet"
        if not p.is_file():
            log.warning("feature_parquet_absent", symbol=s, path=str(p))
            continue
        frames.append(last_row_per_session(pl.read_parquet(p)))
    if not frames:
        raise RuntimeError(f"no feature parquets under {fdir}")
    daily = pl.concat(frames, how="vertical")
    daily = apply_seal(daily)  # sessions < HOLDOUT_START only
    if not (daily["session"] < HOLDOUT_START.isoformat()).all():
        raise SealViolation("seal failed: holdout row present")
    daily = add_session_labels(daily)
    # Belt-and-suspenders: no label may reference a holdout close (seal-before-shift
    # guarantees this; the invariant is re-checked so refactors cannot silently
    # break it — a raise, not an assert, which ``python -O`` would strip).
    if not (daily["session"] < HOLDOUT_START.isoformat()).all():
        raise SealViolation("seal failed: holdout row survived labeling")
    return daily.sort(["session", "symbol"])


def modal_et_time(settings: Settings, version: str, symbol: str) -> str:
    """Modal ET clock time of the near-close row (reporting only)."""
    p = _feature_dir(settings, version) / f"{symbol}.parquet"
    df = pl.read_parquet(p, columns=["session", "ts"])
    last = (
        df.sort("ts")
        .group_by("session")
        .agg(pl.col("ts").last().alias("ts"))
        .with_columns(
            pl.from_epoch("ts", time_unit="ns")
            .dt.convert_time_zone("America/New_York")
            .dt.strftime("%H:%M:%S")
            .alias("et")
        )
    )
    vc = last["et"].value_counts().sort("count", descending=True)
    return str(vc["et"][0])


# --------------------------------------------------------------------------- IC helpers


def cross_sectional_ic(preds: pl.DataFrame, min_symbols: int = CROSS_SECTION_MIN_SYMBOLS) -> pl.DataFrame:
    """Per-session cross-sectional rank-IC over the pooled names.

    Same Spearman-on-ranks formula as evaluate.per_session_ic; only the row-count
    gate differs (daily cross-sections have ~12 names, not 30+). Columns in:
    session, pred, label. Returns (session, ic, n)."""
    return (
        preds.filter(pl.col("label").is_not_null())
        .group_by("session")
        .agg(
            pl.corr(pl.col("pred").rank(), pl.col("label").rank()).alias("ic"),
            pl.len().alias("n"),
        )
        .filter(
            pl.col("ic").is_not_null() & pl.col("ic").is_not_nan() & (pl.col("n") >= min_symbols)
        )
        .sort("session")
    )


def _rank(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="stable")
    ranks = np.empty(len(x), dtype=np.float64)
    ranks[order] = np.arange(len(x), dtype=np.float64)
    return ranks


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3:
        return float("nan")
    ra, rb = _rank(a), _rank(b)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def timeseries_ic_ci(
    pred: np.ndarray, label: np.ndarray, n_boot: int = 2000, seed: int = 7, ci: float = 0.95
) -> tuple[float, float, float, int]:
    """Per-symbol time-series rank-IC (pred vs realized z across the symbol's
    sessions) with a session-resampled (day-clustered) bootstrap CI. Returns
    (mean_ic, lo, hi, n_sessions)."""
    mask = ~(np.isnan(pred) | np.isnan(label))
    pred, label = pred[mask], label[mask]
    n = len(pred)
    if n < 3:
        return float("nan"), float("nan"), float("nan"), n
    point = _spearman(pred, label)
    rng = np.random.default_rng(seed)
    boots: list[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        ic = _spearman(pred[idx], label[idx])
        if not math.isnan(ic):
            boots.append(ic)
    if not boots:
        return point, float("nan"), float("nan"), n
    alpha = (1 - ci) / 2
    lo = float(np.quantile(boots, alpha))
    hi = float(np.quantile(boots, 1 - alpha))
    return point, lo, hi, n


# --------------------------------------------------------------------------- walk-forward


def horizon_predictions(daily: pl.DataFrame, label_col: str, folds: list[cv.Fold]) -> pl.DataFrame:
    """Fit one pooled LightGBM per fold and collect OOS predictions for `label_col`.

    Each test row's model is trained only on sessions strictly before the fold
    (minus the 6-session embargo). Returns (symbol, session, pred, label)."""
    out: list[pl.DataFrame] = []
    for fold_id, fold in enumerate(folds):
        train = daily.filter(
            pl.col("session").is_in(list(fold.train_sessions)) & pl.col(label_col).is_not_null()
        )
        test = daily.filter(
            pl.col("session").is_in(list(fold.test_sessions)) & pl.col(label_col).is_not_null()
        )
        if train.height < 300 or test.height == 0:
            continue
        booster = lgbm.train_one(train, FEATURE_COLS, label_col)
        preds = lgbm.predict(booster, test, FEATURE_COLS)
        out.append(
            test.select(
                pl.col("symbol"),
                pl.col("session"),
                pl.Series("pred", preds),
                pl.col(label_col).alias("label"),
            ).with_columns(pl.lit(fold_id, dtype=pl.Int64).alias("fold_id"))
        )
    if not out:
        return pl.DataFrame(
            schema={"symbol": pl.Utf8, "session": pl.Utf8, "pred": pl.Float64,
                    "label": pl.Float64, "fold_id": pl.Int64}
        )
    allrows = pl.concat(out, how="vertical")
    # OOS rows can never be in the holdout (seal + fold construction) — enforced.
    if not (allrows["session"] < HOLDOUT_START.isoformat()).all():
        raise SealViolation("seal failed: OOS prediction row in the holdout")
    return allrows


def evaluate_horizon(preds: pl.DataFrame) -> dict:
    """Pooled cross-sectional IC + per-symbol NVDA/TSLA time-series IC for one horizon."""
    ics = cross_sectional_ic(preds)
    mean, lo, hi = evaluate.bootstrap_mean_ci(ics["ic"].to_numpy())
    pooled = {
        "mean_ic": round(mean, 5),
        "ci_lo": round(lo, 5),
        "ci_hi": round(hi, 5),
        "n_sessions": ics.height,
        "n_rows": preds.filter(pl.col("label").is_not_null()).height,
        "ic_positive_share": round(float((ics["ic"] > 0).mean()), 4) if ics.height else None,
    }
    per_symbol: dict[str, dict] = {}
    for sym in ("NVDA", "TSLA"):
        sub = preds.filter((pl.col("symbol") == sym) & pl.col("label").is_not_null()).sort("session")
        m, lo, hi, n = timeseries_ic_ci(sub["pred"].to_numpy(), sub["label"].to_numpy())
        per_symbol[sym] = {
            "mean_ic": round(m, 5), "ci_lo": round(lo, 5), "ci_hi": round(hi, 5), "n_sessions": n,
        }
    return {"pooled": pooled, "per_symbol": per_symbol}


# --------------------------------------------------------------------------- reporting


def _fmt(x: object) -> str:
    if isinstance(x, float):
        return "nan" if math.isnan(x) else f"{x:+.4f}"
    return str(x)


def build_ic_table(results: dict[int, dict], n_folds: int) -> pl.DataFrame:
    rows: list[dict] = []
    for h in HORIZONS:
        p = results[h]["pooled"]
        rows.append({
            "horizon_d": h, "scope": "pooled", "mean_ic": p["mean_ic"],
            "ci_lo": p["ci_lo"], "ci_hi": p["ci_hi"], "n_sessions": p["n_sessions"],
            "n_rows": p["n_rows"], "n_folds": n_folds,
        })
        for sym in ("NVDA", "TSLA"):
            s = results[h]["per_symbol"][sym]
            rows.append({
                "horizon_d": h, "scope": sym, "mean_ic": s["mean_ic"],
                "ci_lo": s["ci_lo"], "ci_hi": s["ci_hi"], "n_sessions": s["n_sessions"],
                "n_rows": s["n_sessions"], "n_folds": n_folds,
            })
    return pl.DataFrame(rows)


def render_report(
    results: dict[int, dict], n_folds: int, n_sessions_pool: int, n_symbols: int,
    modal_et: str, wall_s: float, version: str,
) -> str:
    lines: list[str] = []
    lines.append(f"# {TRIAL_ID} — daily 1d/3d/5d side-ledger (research-only)\n")
    lines.append(
        "Registered daily side-ledger family (PROTOCOL v6 §2). NO plan-level claim, "
        "NO ledger write, NO dashboard; the deployable system never holds overnight. "
        "rank-IC bookkeeping only — the orchestrator owns any verdict.\n"
    )
    lines.append("## Setup\n")
    lines.append(f"- feature_version: {version}")
    lines.append(f"- universe: {n_symbols} bar_signal names, one near-close row per session")
    lines.append(f"- near-close row modal ET time (NVDA): {modal_et}")
    lines.append(f"- pooled pre-holdout sessions: {n_sessions_pool} (holdout >= "
                 f"{HOLDOUT_START.isoformat()} stripped BEFORE label shift)")
    lines.append("- labels: l_fwd_{h}d = log(close[t+h]/close[t]), SESSION-INDEXED "
                 "(calendar-safe); z = label / (f_vol20 * sqrt(h))")
    lines.append(f"- horizons: {list(HORIZONS)}  (longest {LONGEST_HORIZON}d)")
    lines.append("- model: pooled cross-symbol LightGBM per horizon (lgbm.DEFAULT_PARAMS)")
    lines.append(f"- CV: purged expanding walk-forward, embargo_sessions={EMBARGO_SESSIONS} "
                 f"(> longest horizon {LONGEST_HORIZON}), {n_folds} folds")
    lines.append(f"- wall time: {wall_s:.1f}s\n")

    lines.append("## Pooled cross-sectional rank-IC (day-clustered 95% CI)\n")
    lines.append("Per session: Spearman(pred, realized z) across the ~12 names; one value per")
    lines.append("session, bootstrapped over sessions (the day cluster).\n")
    lines.append("| horizon | mean_IC | CI_lo | CI_hi | n_sessions | n_rows | pos_share |")
    lines.append("|---------|---------|-------|-------|------------|--------|-----------|")
    for h in HORIZONS:
        p = results[h]["pooled"]
        lines.append(
            f"| {h}d | {_fmt(p['mean_ic'])} | {_fmt(p['ci_lo'])} | {_fmt(p['ci_hi'])} | "
            f"{p['n_sessions']} | {p['n_rows']} | {_fmt(p['ic_positive_share'])} |"
        )
    lines.append("")

    lines.append("## Per-symbol time-series rank-IC — NVDA / TSLA (grok E5 arm)\n")
    lines.append("Per symbol: Spearman(pred, realized z) across the symbol's OOS sessions;")
    lines.append("session-resampled bootstrap CI.\n")
    lines.append("| horizon | symbol | mean_IC | CI_lo | CI_hi | n_sessions | grok_E5_claim |")
    lines.append("|---------|--------|---------|-------|-------|------------|---------------|")
    for h in HORIZONS:
        for sym in ("NVDA", "TSLA"):
            s = results[h]["per_symbol"][sym]
            claim = GROK_E5_CLAIMS.get((sym, h))
            claim_s = f"{claim:+.2f}" if claim is not None else "-"
            lines.append(
                f"| {h}d | {sym} | {_fmt(s['mean_ic'])} | {_fmt(s['ci_lo'])} | "
                f"{_fmt(s['ci_hi'])} | {s['n_sessions']} | {claim_s} |"
            )
    lines.append("")

    lines.append("## grok E5 comparison\n")
    nvda1 = results[1]["per_symbol"]["NVDA"]["mean_ic"]
    tsla1 = results[1]["per_symbol"]["TSLA"]["mean_ic"]
    tsla5 = results[5]["per_symbol"]["TSLA"]["mean_ic"]
    lines.append(
        "grok E5 reported per-symbol time-series ICs on ~43 sessions: "
        "TSLA 1d 0.23, TSLA 5d 0.45, NVDA 1d 0.27. Pre-registered expectation was that "
        "these are materially LOWER on 450+ OOS sessions (a short, favourable window "
        "over-states IC). Measured here:"
    )
    lines.append(f"- TSLA 1d: {_fmt(tsla1)} vs grok 0.23")
    lines.append(f"- TSLA 5d: {_fmt(tsla5)} vs grok 0.45")
    lines.append(f"- NVDA 1d: {_fmt(nvda1)} vs grok 0.27")
    much_lower = all(
        (not math.isnan(v)) and v < c - 0.05
        for v, c in ((tsla1, 0.23), (tsla5, 0.45), (nvda1, 0.27))
    )
    verdict = (
        "CONFIRMED: every measured per-symbol IC is materially below the grok E5 claim, "
        "consistent with those figures being small-sample (~43 session) over-statements."
        if much_lower else
        "MIXED: at least one measured IC is not materially below the grok E5 claim — see the "
        "table; the small-sample over-statement hypothesis is not uniformly confirmed."
    )
    lines.append(f"\n{verdict}\n")

    lines.append("## Notes / judgment calls\n")
    lines.append("- The holdout is stripped BEFORE the session shift, so no pre-holdout label "
                 "can reference a sealed close; holdout rows and labels are excluded entirely.")
    lines.append("- evaluate.per_session_ic gates sessions at n>=30 rows (intraday-calibrated) "
                 "and returns ZERO daily cross-sections (only ~12 names/session). The pooled "
                 f"metric mirrors its Spearman-on-ranks formula with min_symbols="
                 f"{CROSS_SECTION_MIN_SYMBOLS} and reuses evaluate.bootstrap_mean_ci for the "
                 "day-clustered CI.")
    lines.append("- Per-symbol ICs are time-series (one row/session), so per_session_ic is "
                 "inapplicable there; a session-resampled bootstrap is used.")
    lines.append("- Research-only: no ledger write (orchestrator owns verdicts), no plan-level "
                 "economics, no dashboard.")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- run


def run(settings: Settings, *, version: str, out_name: str) -> dict:
    t0 = time.time()
    assert EMBARGO_SESSIONS > LONGEST_HORIZON, (
        f"embargo {EMBARGO_SESSIONS} must exceed longest horizon {LONGEST_HORIZON}"
    )
    symbols = [s.upper() for s in get_research_config().universe_bar_signal]

    daily = build_daily_pool(settings, version, symbols)
    n_sessions_pool = daily["session"].n_unique()
    n_symbols = daily["symbol"].n_unique()
    log.info("daily_pool_ready", rows=daily.height, sessions=n_sessions_pool, symbols=n_symbols)

    folds = cv.walk_forward_folds(daily, embargo_sessions=EMBARGO_SESSIONS)
    # Guard: every fold purges >= EMBARGO_SESSIONS sessions between train end and
    # test start (session-index gap), i.e. strictly more than the longest horizon.
    all_sessions = sorted(daily["session"].unique().to_list())
    idx = {s: i for i, s in enumerate(all_sessions)}
    for f in folds:
        gap = idx[f.test_sessions[0]] - idx[f.train_sessions[-1]]
        assert gap > LONGEST_HORIZON, f"embargo gap {gap} <= longest horizon {LONGEST_HORIZON}"
    log.info("folds", n=len(folds), embargo=EMBARGO_SESSIONS)

    results: dict[int, dict] = {}
    for h in HORIZONS:
        preds = horizon_predictions(daily, f"z_{h}d", folds)
        results[h] = evaluate_horizon(preds)
        log.info("horizon_done", horizon=h, pooled_ic=results[h]["pooled"]["mean_ic"],
                 n_sessions=results[h]["pooled"]["n_sessions"])

    wall_s = time.time() - t0
    modal_et = modal_et_time(settings, version, "NVDA")

    out_dir = experiments_dir() / out_name
    out_dir.mkdir(parents=True, exist_ok=True)
    ic_table = build_ic_table(results, len(folds))
    ic_table.write_parquet(out_dir / "ic_table.parquet")
    report_md = render_report(
        results, len(folds), n_sessions_pool, n_symbols, modal_et, wall_s, version
    )
    (out_dir / "report.md").write_text(report_md, encoding="utf-8")

    report = {
        "trial": TRIAL_ID,
        "feature_version": version,
        "out_dir": str(out_dir),
        "n_sessions_pool": n_sessions_pool,
        "n_symbols": n_symbols,
        "n_folds": len(folds),
        "embargo_sessions": EMBARGO_SESSIONS,
        "modal_et_time_nvda": modal_et,
        "params": dict(lgbm.DEFAULT_PARAMS),
        "cv": {"test_block_sessions": 21, "min_train_sessions": 250,
               "embargo_sessions": EMBARGO_SESSIONS},
        "results": results,
        "wall_s": round(wall_s, 2),
    }
    (out_dir / "_run_report.json").write_text(json.dumps(report, indent=2, default=str))
    log.info("daily_swing_complete", wall_s=report["wall_s"], out=str(out_dir))
    return report


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--feature-version", default="v1", help="Feature matrix version (data/features/<v>/).")
@click.option("--out", "out_name", default="daily-swing-v1",
              help="Output subdir under research/experiments/.")
def main(feature_version: str, out_name: str) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    settings = get_settings()
    report = run(settings, version=feature_version, out_name=out_name)

    click.echo(f"trial: {TRIAL_ID}  feature_version={feature_version}")
    click.echo(f"pooled sessions: {report['n_sessions_pool']}  symbols: {report['n_symbols']}  "
               f"folds: {report['n_folds']}  embargo: {report['embargo_sessions']}")
    click.echo(f"near-close modal ET time (NVDA): {report['modal_et_time_nvda']}")
    for h in HORIZONS:
        p = report["results"][h]["pooled"]
        nvda = report["results"][h]["per_symbol"]["NVDA"]
        tsla = report["results"][h]["per_symbol"]["TSLA"]
        click.echo(
            f"  {h}d pooled IC={p['mean_ic']:+.4f} CI[{p['ci_lo']:+.4f},{p['ci_hi']:+.4f}] "
            f"n_sess={p['n_sessions']} | NVDA={nvda['mean_ic']:+.4f} TSLA={tsla['mean_ic']:+.4f}"
        )
    click.echo(f"out: {report['out_dir']}")
    click.echo(f"wall: {report['wall_s']}s")


if __name__ == "__main__":
    main()
