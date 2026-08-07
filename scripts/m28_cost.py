"""M28 exit-cost model: a bars-only half-spread estimator, calibrated on measured quotes.

Spec: REGISTRATION.md section 8. The exit leg crosses one half-spread at 15:40-15:45.
No quotes exist for 184 names, so the half-spread must be estimated from minute bars.

ESTIMATOR (one free parameter, so 10 calibration names cannot overfit it):
    raw_r  = 25th percentile over the 15:40-15:45 minute bars of (high - low) / close, bps
    hs_est = k * raw_r
A minute bar's high-low range is bounded below by the quoted spread; taking a low quantile
across the window strips the minutes that contain genuine price movement, leaving a
spread-dominated statistic. `k` is fitted by least squares in LOG space against the ten
names whose true 15:40-15:45 quoted half-spread is measured from `bbo1s`.

Quality is reported honestly, including leave-one-out error, because the registration makes
the primary statistic's dependence on this estimator visible rather than assumed (a flat
3.0 bps stress is reported alongside it in the main run).

    uv run python scripts/m28_cost.py
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from m28_panel import (  # noqa: E402
    EXIT_HI,
    EXIT_LO,
    FIRST_SESSION,
    LAST_SESSION,
    _date_expr,
    _sec_expr,
)

BARS1M = REPO / "data" / "raw" / "sip" / "bars1m"
BBO = REPO / "data" / "raw" / "bbo1s"
EXP = REPO / "research" / "experiments" / "M28-open-cross-battery"
OUT = EXP / "cost.parquet"

# Truth set: median QUOTED half-spread in 15:40-15:45, measured from bbo1s
# (research/experiments/R2A-prong0/stage1.md, 2026-07-26).
MEASURED_HALF_SPREAD_BPS = {
    "NVDA": 0.70, "TSLA": 0.78, "AMD": 0.62, "MU": 0.82, "GOOGL": 0.50,
    "KLAC": 3.60, "MRVL": 0.88, "LRCX": 1.72, "TXN": 0.97, "AMAT": 1.41,
}
Q = 25          # percentile of the minute-bar range used as the spread-dominated statistic


def raw_range_stat(sym: str) -> tuple[str, list[dict]]:
    """Per session: the Q-th percentile of minute-bar (high-low)/close in the exit window."""
    files = sorted((BARS1M / sym).glob("*.parquet"))
    if not files:
        return sym, []
    parts = []
    for f in files:
        d = pl.read_parquet(f, columns=["ts", "high", "low", "close"])
        if d.height:
            parts.append(d)
    if not parts:
        return sym, []
    d = pl.concat(parts).with_columns(_date_expr().alias("date"), _sec_expr().alias("sec"))
    d = d.filter(
        (pl.col("close") > 0) & (pl.col("sec") >= EXIT_LO) & (pl.col("sec") <= EXIT_HI)
        & (pl.col("date") >= FIRST_SESSION) & (pl.col("date") <= LAST_SESSION)
    ).with_columns(((pl.col("high") - pl.col("low")) / pl.col("close") * 1e4).alias("r"))
    if d.height == 0:
        return sym, []
    g = d.group_by("date").agg(
        pl.col("r").quantile(Q / 100, interpolation="linear").alias("raw_r"),
        pl.len().alias("n_bars"),
    ).filter(pl.col("n_bars") >= 3)
    return sym, [{"sym": sym, **r} for r in g.sort("date").to_dicts()]


def main() -> int:
    uni = json.loads((EXP / "universe.json").read_text(encoding="utf-8"))
    syms = sorted(set(uni["tradeable"]) | set(MEASURED_HALF_SPREAD_BPS))
    t0 = time.time()
    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=12) as ex:
        for i, (_s, rr) in enumerate(ex.map(raw_range_stat, syms), 1):
            rows.extend(rr)
            if i % 50 == 0:
                print(f"  {i}/{len(syms)}  {time.time() - t0:.0f}s")
    df = pl.DataFrame(rows)

    # ---- calibrate k on the ten measured names ---------------------------- #
    per = df.group_by("sym").agg(pl.col("raw_r").median().alias("raw_med"))
    cal = per.filter(pl.col("sym").is_in(list(MEASURED_HALF_SPREAD_BPS)))
    x = cal["raw_med"].to_numpy()
    y = np.array([MEASURED_HALF_SPREAD_BPS[s] for s in cal["sym"].to_list()])
    k = float(np.exp(np.mean(np.log(y) - np.log(x))))          # LS in log space, 1 parameter

    pred = k * x
    ape = np.abs(pred - y) / y
    loo = []
    for j in range(len(x)):
        m = np.ones(len(x), bool)
        m[j] = False
        kj = float(np.exp(np.mean(np.log(y[m]) - np.log(x[m]))))
        loo.append(abs(kj * x[j] - y[j]) / y[j])

    lines = ["# M28 exit-cost calibration (bars-only half-spread estimator)", "",
             f"estimator: hs_est = k * P{Q}[(high-low)/close] over 15:40-15:45 minute bars",
             f"fitted k = **{k:.4f}** (single parameter, log-space least squares, n=10 names)",
             "",
             "| name | raw P25 range (bps) | predicted half-spread | MEASURED | abs % err | LOO % err |",
             "|---|---|---|---|---|---|"]
    for j, s in enumerate(cal["sym"].to_list()):
        lines.append(f"| {s} | {x[j]:.2f} | {pred[j]:.2f} | {y[j]:.2f} | "
                     f"{100 * ape[j]:.0f}% | {100 * loo[j]:.0f}% |")
    corr = float(np.corrcoef(np.log(x), np.log(y))[0, 1])
    lines += ["",
              f"log-log correlation **{corr:.3f}**; median abs err **{100 * np.median(ape):.0f}%**; "
              f"median leave-one-out err **{100 * np.median(loo):.0f}%**", ""]

    df = df.with_columns((pl.col("raw_r") * k).alias("half_spread_bps"))
    uni_hs = df.filter(pl.col("sym").is_in(uni["tradeable"])).group_by("sym").agg(
        pl.col("half_spread_bps").median().alias("hs"))
    q = uni_hs["hs"].to_numpy()
    lines += ["## Estimated half-spread across the 184 tradeable names", "",
              f"median **{np.median(q):.2f}** bps; p10 {np.percentile(q, 10):.2f}; "
              f"p90 {np.percentile(q, 90):.2f}; max {q.max():.2f}", ""]
    df.write_parquet(OUT)
    (EXP / "cost_calibration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"wrote {OUT.relative_to(REPO)} rows={df.height:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
