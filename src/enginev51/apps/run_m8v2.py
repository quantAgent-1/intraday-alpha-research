"""M8-v2 mechanism-informed meta-gate runner (family ``moc_meta_v1``, THIRD
look) -- M3_REGISTRATION.md "M8-v2 -- mechanism-informed meta-gate"
(REGISTERED 2026-07-20) + M8-v2-FEATURE-DRAFT.md.

Pipeline:

    M6-FINAL events.parquet (same file M8-v1 trains on; < 2026-06-01)
      -> moc_meta.build_meta_frame (UNCHANGED: |basis_bps|>=10 candidates,
         y_meta = net_bps>0)
      -> m8v2_features.build_features_frame (the 6 frozen mechanism features)
      -> pre-model redundancy diagnostic: corr(abs_f_over_adv, each M8-v1
         numeric feature) on the PROTOCOL train span -- EMITTED FIRST
      -> ONE expanding walk-forward (moc_gbm folds, IDENTICAL to M8-v1), per
         fold training THREE things on the SAME PIT train set:
           * baseline1-GBDT  (M8-v1 FEATURE_COLS)                -> p_v1
           * v2-GBDT         (M8-v1 FEATURE_COLS + the 6 new)    -> p_v2
           * Occam boundary  (trailing in-sample top-tercile of
                               abs_f_over_adv, train-fit)         -> occam_gate
      -> streams: ungated baseline, v1/v2 gated at q in {0.50,0.55,0.60},
         Occam-gated -- n, hit-rate, mean net_bps, day-clustered CI, per-trade
         + daily Sharpe, per-symbol/per-year breakdowns (stress.clustered_mean_ci)
      -> cross-checks (report-only, never a gate): p_v1 vs the ALREADY-
         COMPUTED M8-meta-v1/oos_predictions.parquet p_win (corr/n only); the
         recomputed signed F/ADV vs M12's cellA_events.parquet F_adv (corr/n)
      -> per-event parquet + metrics.json. NO pass/fail flags anywhere --
         numbers only; the orchestrator grades bars (i)-(v).

This app and models/m8v2_run.py / models/m8v2_features.py are NEW modules;
M8-v1's own files (models/moc_meta.py, apps/run_meta_trial.py) are untouched.
Determinism: LightGBM seed is fixed in lgbm.DEFAULT_PARAMS (inherited via
moc_meta.META_PARAMS); the ``--seed`` option here is a reproducibility echo
only (matches apps/run_meta_trial.py's own convention). Hard PIT/holdout
guard: refuses any input reaching >= protocol.HOLDOUT_START (dev universe is
<= 2026-05-31); an optional ``--end`` further restricts the session range for
cheap dev/smoke runs WITHOUT touching ``--start`` (the walk-forward's fold
boundaries are anchored to the frame's OWN first session, so truncating only
the END preserves IDENTICAL fold boundaries to the full run -- truncating the
START would shift them).

    uv run python -m enginev51.apps.run_m8v2 --trial-id M8-v2-mechanism-features-v1 \\
        --events research/experiments/M6-FINAL-basis/events.parquet --seed 7

    # cheap diagnostics-only dev run (prints row counts / null rates / fold
    # count ONLY -- never net_bps/hit-rate/Sharpe/CI; writes NO files):
    uv run python -m enginev51.apps.run_m8v2 --end 2023-06-30 --smoke
"""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import click
import polars as pl
import structlog

from enginev51.models import m8v2_features
from enginev51.models import m8v2_run as run
from enginev51.protocol import (
    HOLDOUT_START,
    SealViolation,
    experiments_dir,
    refuse_end_on_or_after_holdout,
)

log = structlog.get_logger(__name__)

DEFAULT_EVENTS = "research/experiments/M6-FINAL-basis/events.parquet"


# --------------------------------------------------------------------------- helpers


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


def build_metrics(ev: dict, trial_id: str, seed: int, events_path: str) -> dict:
    """Assemble metrics.json. Redundancy diagnostic is FIRST (registered:
    "computed and emitted FIRST"). NO pass/fail flags -- numbers only."""
    fold_meta = [
        {
            "test_start": f.test_start, "test_end": f.test_end,
            "n_train_sessions": len(f.train_sessions), "n_test_sessions": len(f.test_sessions),
        }
        for f in ev["folds"]
    ]
    streams = {k: run.stream_block(v) for k, v in ev["streams"].items()}
    v1_gated = streams.get(f"baseline1_v1_gated_q{run.COMPARE_GATE:.2f}", {})
    v2_gated = streams.get(f"v2_gated_q{run.COMPARE_GATE:.2f}", {})
    occam_gated = streams.get("occam_gated", {})

    def _delta(a: dict, b: dict, key: str):
        av, bv = a.get(key), b.get(key)
        return round(av - bv, 4) if (av is not None and bv is not None) else None

    return {
        "trial_id": trial_id,
        "seed": seed,
        "events_path": events_path,
        "meta_counts": ev["meta_counts"],
        # ---- pre-model redundancy diagnostic: EMITTED FIRST (registered) ----
        "pre_model_redundancy_diagnostic": ev["redundancy_diagnostic"],
        "feature_funnel": ev["feature_funnel"],
        "occam_gate_definition": {
            "formula": "flow_aligned > 0 AND abs_f_over_adv >= trailing_in_sample_top_tercile_boundary",
            "boundary": "2/3 quantile of abs_f_over_adv, fit on the fold's TRAIN rows "
            "restricted to abs_f_over_adv > 0 (M12 Cell A's own tercile population) "
            "-- FLAGGED CHOICE, see models/m8v2_run.py module docstring",
        },
        "folds": fold_meta,
        "n_folds": len(ev["folds"]),
        "streams": streams,
        "deltas_v2_minus_v1_gated_q0.55": {
            "net_bps_mean": _delta(v2_gated, v1_gated, "net_bps_mean"),
            "hit_rate": _delta(v2_gated, v1_gated, "hit_rate"),
            "sharpe_per_trade": _delta(v2_gated, v1_gated, "sharpe_per_trade"),
            "ci_lo": _delta(v2_gated, v1_gated, "ci_lo"),
        },
        "deltas_v2_minus_occam_gated": {
            "sharpe_per_trade": _delta(v2_gated, occam_gated, "sharpe_per_trade"),
            "net_bps_mean": _delta(v2_gated, occam_gated, "net_bps_mean"),
        },
        "cross_check_v1_reproduction_vs_M8_meta_v1": ev["cross_check_v1_reproduction"],
        "cross_check_f_adv_vs_m12_cellA": ev["cross_check_f_adv_vs_m12"],
        "v2_feature_importances": ev["v2_importances"].to_dicts(),
    }


def write_outputs(
    out_dir: Path, oos: pl.DataFrame, metrics: dict
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    events_path = out_dir / "events.parquet"
    metrics_path = out_dir / "metrics.json"
    per_event = oos.with_columns(
        (pl.col("symbol") + "|" + pl.col("session")).alias("event_id")
    )
    per_event.write_parquet(events_path)
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    return events_path, metrics_path


def _print_smoke(ev: dict, wall_s: float) -> None:
    """SMOKE-ONLY stdout: row counts, feature null rates, fold count. NEVER
    net_bps / hit_rate / Sharpe / CI / any per-stream economics. The F-vs-M12
    cross-check corr is printed (a feature-collinearity diagnostic, not an
    economics number -- no net_bps/hit-rate/mean/Sharpe anywhere in it)."""
    click.echo("=== M8-v2 SMOKE (diagnostics only; NO economics printed, NO files written) ===")
    click.echo(f"meta funnel: {json.dumps(ev['meta_counts'], default=str)}")
    click.echo(f"feature rows (candidates): {ev['features_df'].height}")
    click.echo("")
    click.echo("feature null-rate table:")
    for c in m8v2_features.FEATURE_COLS:
        rate = ev["feature_funnel"]["feature_null_rates"][c]
        click.echo(f"  {c:20s} null_rate={rate}")
    click.echo(f"adv20_source: {ev['feature_funnel']['adv20_source']}")
    click.echo(f"vol20_source: {ev['feature_funnel']['vol20_source']}")
    click.echo(f"no_p_1555_or_bbo: {ev['feature_funnel']['no_p_1555_or_bbo']}")
    click.echo(f"no_r_pinned: {ev['feature_funnel']['no_r_pinned']}")
    click.echo(f"no_day_range: {ev['feature_funnel']['no_day_range']}")
    click.echo(f"no_day_vol_ratio: {ev['feature_funnel']['no_day_vol_ratio']}")
    click.echo("")
    click.echo(f"fold count: {len(ev['folds'])}")
    for f in ev["folds"]:
        click.echo(
            f"  test_start={f.test_start} test_end={f.test_end} "
            f"n_train_sessions={len(f.train_sessions)} n_test_sessions={len(f.test_sessions)}"
        )
    click.echo(f"OOS rows produced: {ev['oos'].height}")
    click.echo("")
    fadv = ev["cross_check_f_adv_vs_m12"]
    click.echo(
        "F/ADV vs M12 cellA_events.parquet cross-check (feature corr, not economics): "
        f"available={fadv.get('available')} n_overlap={fadv.get('n_overlap')} corr={fadv.get('corr')}"
    )
    click.echo(f"wall: {wall_s:.1f}s")


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--trial-id", default="M8-v2-mechanism-features-v1", help="Experiment id -> research/experiments/<id>/.")
@click.option("--events", default=DEFAULT_EVENTS, help="M6-FINAL events.parquet (same file M8-v1 trains on).")
@click.option("--bbo-dir", default=None, help="BBO-1s lake root (default data/raw/bbo1s).")
@click.option("--registry", default=m8v2_features.DEFAULT_REGISTRY_PATH, help="LETF fund registry CSV.")
@click.option("--anchors", default=m8v2_features.DEFAULT_ANCHORS_PATH, help="LETF AUM anchors CSV.")
@click.option("--end", default=None, help="Optional session cutoff (ISO date, inclusive); must stay "
              "< holdout. Restricts the LAST test block only (--start is never touched, so fold "
              "boundaries stay identical to the full run) -- used for cheap --smoke dev runs.")
@click.option("--seed", default=7, type=int, help="Reproducibility echo (model seed is lgbm.DEFAULT_PARAMS).")
@click.option("--smoke", is_flag=True, help="Diagnostics-only dev run: row counts / feature null "
              "rates / fold count ONLY. NEVER prints net_bps/hit-rate/Sharpe/CI. Writes NOTHING to "
              "research/experiments/.")
def main(
    trial_id: str, events: str, bbo_dir: str | None, registry: str, anchors: str,
    end: str | None, seed: int, smoke: bool,
) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety

    events_df = pl.read_parquet(events)
    if (events_df["session"].max() or "") >= HOLDOUT_START.isoformat():
        raise SealViolation(
            "events reach the sealed holdout -- refusing (PROTOCOL v6 par1); the M8-v2 dev "
            "universe is <= 2026-05-31, identical to M8-v1's"
        )
    if end:
        end_d = date.fromisoformat(end)
        refuse_end_on_or_after_holdout(end_d)
        events_df = events_df.filter(pl.col("session") <= end)

    t0 = time.time()
    ev = run.evaluate(events_df, bbo_dir=bbo_dir, registry_path=registry, anchors_path=anchors)
    wall_s = time.time() - t0

    if smoke:
        _print_smoke(ev, wall_s)
        return

    metrics = build_metrics(ev, trial_id, seed, events)
    out_dir = experiments_dir() / trial_id
    events_path, metrics_path = write_outputs(out_dir, ev["oos"], metrics)

    click.echo(f"trial: {trial_id}  events={events}  seed={seed}")
    click.echo(f"meta funnel: {json.dumps(ev['meta_counts'], default=str)}")
    click.echo(f"folds: {len(ev['folds'])}  OOS candidates: {ev['oos'].height}")
    click.echo("")
    click.echo("pre-model redundancy diagnostic (emitted first; orchestrator applies the >0.8 kill rule):")
    click.echo(json.dumps(ev["redundancy_diagnostic"], indent=2, default=str))
    click.echo("")
    stream_table = pl.DataFrame(
        [
            {"stream": k, "n": v["n"], "hit_rate": v["hit_rate"], "net_bps_mean": v["net_bps_mean"],
             "ci_lo": v["ci_lo"], "ci_hi": v["ci_hi"], "sharpe_per_trade": v["sharpe_per_trade"],
             "sharpe_daily": v["sharpe_daily"]}
            for k, v in metrics["streams"].items()
        ]
    )
    click.echo(_ascii(stream_table))
    click.echo("")
    click.echo(f"events:  {events_path}")
    click.echo(f"metrics: {metrics_path}")
    click.echo(f"wall: {wall_s:.1f}s")


if __name__ == "__main__":
    main()
