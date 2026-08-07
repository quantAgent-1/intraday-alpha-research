"""M15 backtest reference (registered M15-backtest-reference-v1, 2026-07-18).

Simulates the FROZEN M15 portfolio policy on honest historical p_win:
  Panel A: M8 walk-forward OOS classifier predictions (M8-meta-v1 oos_predictions,
           2022-2026; the |basis|>=10 candidate set carrying the honest p_win).
  Panel B: the frozen forward model scored on the holdout events (post-seal OOS
           by construction — the exact forward-harness procedure).

CORRECTED 2026-07-20: Panel A previously loaded M6-FINAL-basis/oos_predictions and
renamed its `pred` column (the M6-GBM CONTINUOUS bps regression, range ~-3.3..+6.8)
to `p_win`, then gated at 0.55 — a category error that gated a bps forecast as if it
were a probability. Fixed to the honest M8 classifier p_win (M8-meta-v1). Panel B was
NEVER affected (it always scored the real frozen model). See report.md correction
block for the reproduced-vs-corrected numbers.
Outputs: portfolio stream mean/CI vs the meta stream (selection-effect check),
implementability by year at $1,000 whole shares, and the DIAGNOSTIC CUSUM run
(params frozen; miscalibration would be documented, never tuned).
"""

import polars as pl

from enginev51 import positioning as pos
from enginev51.apps import forward_paper as fp
from enginev51.backtest import stress
from enginev51.models import moc_meta

# ---------------- Panel A: walk-forward OOS ----------------
# The honest classifier p_win is the M8 meta model's walk-forward OOS output
# (M8-meta-v1/oos_predictions.parquet: the |basis|>=10 candidate set, real `p_win`
# in [0.35, 0.75]). NOT the M6-GBM `pred` (a continuous bps regression) — renaming
# that to p_win and gating at 0.55 was the pre-2026-07-20 bug (see module docstring).
# Same events and net_bps as M6-FINAL; classical (|basis|>=10) is unchanged (+2.21,
# n=4,735). Only the meta/portfolio gate column is corrected.
oos = pl.read_parquet("research/experiments/M8-meta-v1/oos_predictions.parquet")
print(f"Panel A: n={oos.height}  span {oos['session'].min()}..{oos['session'].max()}  "
      f"min|basis|={oos['basis_bps'].abs().min():.1f}")
a = oos.with_columns(
    (pl.col("basis_bps").abs() >= 10.0).alias("taken_classical"),
).with_columns(
    (pl.col("taken_classical") & (pl.col("p_win") >= fp.META_GATE_Q)).alias("taken_meta"),
)
a = pos.apply_positioning(a)

def stream_stats(df: pl.DataFrame, flag: str) -> tuple[float, float, float, int, int]:
    s = df.filter(pl.col(flag).fill_null(False))
    m, lo, hi = stress.clustered_mean_ci(s["net_bps"].to_numpy(), s["session"].to_numpy())
    return m, lo, hi, s.height, int(s["session"].n_unique())

for label, flag in [("classical", "taken_classical"), ("meta", "taken_meta"),
                    ("portfolio", "selected")]:
    m, lo, hi, n, ns = stream_stats(a, flag)
    print(f"A {label:9s}: mean {m:+.2f} [{lo:+.2f},{hi:+.2f}]  n={n}  sessions={ns}")

sel = a.filter(pl.col("selected"))
print("\nA portfolio by year (net / dir / implementable rate / n):")
yr = sel.with_columns(pl.col("session").str.slice(0, 4).alias("yr")).group_by("yr").agg(
    net=pl.col("net_bps").mean().round(2),
    dir=(pl.col("net_bps") > 0).mean().round(3),
    impl=pl.col("implementable").fill_null(False).mean().round(3),
    n=pl.len(),
).sort("yr")
print(yr)

# diagnostic CUSUM over the historical daily portfolio series
daily = pos.cusum_series(pos.portfolio_daily(a))
alerts = daily.filter(pl.col("cusum_alert"))
print(f"\nA CUSUM: alert sessions={alerts.height}/{daily.height}  max S={daily['cusum_S'].max():.1f}")
if alerts.height:
    d = daily.with_columns(
        (pl.col("cusum_alert") & ~pl.col("cusum_alert").shift(1).fill_null(False)).alias("start")
    )
    starts = d.filter(pl.col("start"))["session"].to_list()
    ends = []
    inA = False
    for s_, al in zip(daily["session"].to_list(), daily["cusum_alert"].to_list(), strict=True):
        if al:
            inA = True
            last = s_
        elif inA:
            ends.append(last)
            inA = False
    if inA:
        ends.append(last)
    print("A CUSUM episodes:", list(zip(starts, ends, strict=False)))

# ---------------- Panel B: holdout, frozen model ----------------
hold = pl.read_parquet("research/experiments/M6-FINAL-HOLDOUT/events.parquet")
booster, note = fp.get_or_train_model()
print(f"\nPanel B: holdout n={hold.height}  model={note}")
pw = moc_meta.predict_pwin(booster, hold)
b = hold.with_columns(pl.Series("p_win", pw)).with_columns(
    (pl.col("basis_bps").abs() >= 10.0).alias("taken_classical"),
).with_columns(
    (pl.col("taken_classical") & (pl.col("p_win") >= fp.META_GATE_Q)).alias("taken_meta"),
)
b = pos.apply_positioning(b)
for label, flag in [("classical", "taken_classical"), ("meta", "taken_meta"),
                    ("portfolio", "selected")]:
    m, lo, hi, n, ns = stream_stats(b, flag)
    print(f"B {label:9s}: mean {m:+.2f} [{lo:+.2f},{hi:+.2f}]  n={n}  sessions={ns}")
selb = b.filter(pl.col("selected"))
print(f"B implementable rate: {selb['implementable'].fill_null(False).mean():.3f}")
dailyb = pos.cusum_series(pos.portfolio_daily(b))
print(f"B CUSUM: alert sessions={dailyb.filter(pl.col('cusum_alert')).height}/{dailyb.height}  "
      f"max S={dailyb['cusum_S'].max():.1f}")
