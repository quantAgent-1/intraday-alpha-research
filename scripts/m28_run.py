"""M28 open-cross battery: TRAIN admission, then the single VALIDATE test.

Spec: research/experiments/M28-open-cross-battery/REGISTRATION.md.

Two stages, deliberately separated so the frozen state exists on disk before the test is
computed and cannot be silently revised:

    uv run python scripts/m28_run.py train      -> writes admitted.json (FDR + signs)
    uv run python scripts/m28_run.py validate   -> reads admitted.json, runs ONE test

`validate` REFUSES to run if admitted.json is absent. If no signal clears FDR on train the
outcome is NULL-AT-ADMISSION and the validate period is not consumed.

ADIA Lab No.19 statistics (SR/PSR/MinTRL) are imported BY IDENTITY from the audited M23
kernels -- this file never re-implements them (house rule, see gap_day.py).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from m28_panel import SIGNALS  # noqa: E402

from enginev51.research_screens.sizing_shadow import (  # noqa: E402
    min_trl,
    psr,
    sample_moments,
    sr_native,
)

EXP = REPO / "research" / "experiments" / "M28-open-cross-battery"
ADMITTED = EXP / "admitted.json"

TRAIN = ("2024-01-02", "2025-05-30")
VALID = ("2025-06-02", "2026-05-29")
FDR_Q = 0.10
SEED, REPS = 7, 2000
DECILE = 0.10
GROSS = 1.0
SEC_FEE_BPS = 0.206
ALPHA = 0.05
MIN_NAMES_PER_SESSION = 20

# AMENDMENT_1_COST.md (decided outcome-blind, before any return statistic existed): the
# bars-only half-spread estimator is anti-informative (log-log corr -0.515 vs measured
# quotes; it tracks volatility, not spread), so the PRE-DECLARED flat 3.0 bps stress is
# promoted to the primary cost. A higher cost makes the 2x promotion test strictly harder.
PRIMARY_HS_BPS = 3.0        # primary: the pre-declared conservative stress
OPTIMISTIC_HS_BPS = 0.85    # median of the ten bbo1s-measured names (optimistic bound)
DOUBLE_HS_BPS = 6.0         # 2x the primary


# ---------------------------------------------------------------- cross-section
def zscore_panel(df: pl.DataFrame) -> pl.DataFrame:
    """Per session: winsorise each signal at the 1/99 cross-sectional percentile, z-score."""
    out = df
    for s in SIGNALS:
        lo = pl.col(s).quantile(0.01).over("date")
        hi = pl.col(s).quantile(0.99).over("date")
        w = pl.col(s).clip(lo, hi)
        mu = w.mean().over("date")
        sd = w.std().over("date")
        out = out.with_columns(
            pl.when(sd > 0).then((w - mu) / sd).otherwise(None).alias(f"z_{s}")
        )
    return out


def session_ic(df: pl.DataFrame, sig: str) -> tuple[np.ndarray, np.ndarray]:
    """Per-session Spearman IC between z_<sig> and the outcome. Returns (dates, ics)."""
    d = df.select(["date", f"z_{sig}", "ret_bps"]).drop_nulls().filter(
        pl.col(f"z_{sig}").is_finite() & pl.col("ret_bps").is_finite())
    dates, ics = [], []
    for key, g in d.partition_by("date", as_dict=True, maintain_order=True).items():
        if g.height < MIN_NAMES_PER_SESSION:
            continue
        x = g[f"z_{sig}"].to_numpy()
        y = g["ret_bps"].to_numpy()
        rx = np.argsort(np.argsort(x)).astype(float)
        ry = np.argsort(np.argsort(y)).astype(float)
        if rx.std() == 0 or ry.std() == 0:
            continue
        dates.append(key[0] if isinstance(key, tuple) else key)
        ics.append(float(np.corrcoef(rx, ry)[0, 1]))
    return np.array(dates), np.array(ics)


def boot_mean(v: np.ndarray, seed: int = SEED, reps: int = REPS):
    """Session bootstrap of a mean: (ci_lo, ci_hi, two-sided p vs 0)."""
    if v.size < 2:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    n = v.size
    b = np.array([v[rng.integers(0, n, n)].mean() for _ in range(reps)])
    p = 2.0 * min(float((b <= 0).mean()), float((b >= 0).mean()))
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5)), min(p, 1.0)


def bh_fdr(pvals: list[float], q: float) -> list[bool]:
    """Benjamini-Hochberg: True where the hypothesis is rejected (i.e. admitted)."""
    m = len(pvals)
    order = np.argsort(pvals)
    keep = np.zeros(m, bool)
    kmax = -1
    for rank, idx in enumerate(order, start=1):
        if pvals[idx] <= rank / m * q:
            kmax = rank
    if kmax > 0:
        keep[order[:kmax]] = True
    return keep.tolist()


def load_panel() -> pl.DataFrame:
    """Panel + a FLAT primary exit half-spread (see AMENDMENT_1_COST.md).

    The fitted per-name estimator is deliberately NOT used: it ranks names backwards
    against the only spread ground truth this project owns.
    """
    p = pl.read_parquet(EXP / "panel.parquet").with_columns(
        pl.lit(PRIMARY_HS_BPS).alias("hs"))
    # NaN -> NULL on every signal column. polars propagates NaN through mean/std/quantile
    # and `drop_nulls` does NOT remove NaN, so a single missing name (e.g. a name with no
    # pre-market prints) silently poisons an entire session's z-score and then survives
    # every downstream filter. Converting once here makes null-skipping semantics apply
    # everywhere. Guarded by assert_no_nan_z below.
    p = p.with_columns([
        pl.when(pl.col(c).is_not_null() & pl.col(c).is_nan())
        .then(None).otherwise(pl.col(c)).alias(c)
        for c in SIGNALS
    ])
    z = zscore_panel(p)
    assert_no_nan_z(z)
    return z


def assert_no_nan_z(df: pl.DataFrame) -> None:
    """A z column must never contain NaN -- only null (absent) or a finite number.

    This is the tripwire for the failure that produced five identical pre-market ICs on
    the first train run: NaN ranked as data instead of being excluded.
    """
    bad = []
    for s in SIGNALS:
        col = df[f"z_{s}"]
        n_nan = int(col.fill_null(0.0).is_nan().sum())
        n_fin = int(col.drop_nulls().is_finite().sum())
        if n_nan or n_fin == 0:
            bad.append(f"z_{s}: {n_nan} NaN, {n_fin} finite")
    if bad:
        raise AssertionError("NaN leaked into z-scores -- " + "; ".join(bad))


# ---------------------------------------------------------------- portfolio
def portfolio_daily(df: pl.DataFrame, admitted: list[str], signs: dict[str, float]
                    ) -> pl.DataFrame:
    """Composite -> decile long/short -> daily gross, cost, net (bps of gross)."""
    expr = [pl.col(f"z_{s}") * signs[s] for s in admitted]
    n_avail = sum((e.is_not_null().cast(pl.Int32) for e in expr[1:]), expr[0].is_not_null().cast(pl.Int32))
    comp = sum(e.fill_null(0.0) for e in expr[1:]) + expr[0].fill_null(0.0)
    d = df.with_columns(n_avail.alias("n_sig")).with_columns(
        pl.when(pl.col("n_sig") > 0).then(comp / pl.col("n_sig")).otherwise(None).alias("comp")
    ).drop_nulls(["comp", "ret_bps", "hs"]).filter(
        pl.col("comp").is_finite() & pl.col("ret_bps").is_finite())

    rows = []
    for key, g in d.partition_by("date", as_dict=True, maintain_order=True).items():
        if g.height < MIN_NAMES_PER_SESSION:
            continue
        date = key[0] if isinstance(key, tuple) else key
        comp_v = g["comp"].to_numpy()
        ret = g["ret_bps"].to_numpy()
        hs = g["hs"].to_numpy()
        k = max(1, int(round(g.height * DECILE)))
        order = np.argsort(comp_v)
        short_i, long_i = order[:k], order[-k:]
        half = GROSS / 2.0
        gross_ret = half * ret[long_i].mean() - half * ret[short_i].mean()
        cost = half * hs[long_i].mean() + half * hs[short_i].mean() + SEC_FEE_BPS
        rows.append({
            "date": date, "n_names": g.height, "k": k,
            "gross_bps": gross_ret, "cost_bps": cost, "net_bps": gross_ret - cost,
            "net_bps_2x": gross_ret - (GROSS * DOUBLE_HS_BPS + SEC_FEE_BPS),
            "net_bps_stress": gross_ret - (GROSS * OPTIMISTIC_HS_BPS + SEC_FEE_BPS),
            "long_ret": float(ret[long_i].mean()), "short_ret": float(ret[short_i].mean()),
            "mkt_ret": float(ret.mean()),
            "long_names": [g["sym"][int(i)] for i in long_i],
            "short_names": [g["sym"][int(i)] for i in short_i],
        })
    return pl.DataFrame(rows)


def adia(x: np.ndarray) -> dict:
    g3, g4, rho = sample_moments(x)
    sr = sr_native(x)
    t = int(x.size)
    return {"sr_native": sr, "psr_sr0_0": psr(sr, 0.0, t, rho, g3, g4),
            "min_trl": min_trl(sr, 0.0, ALPHA, rho, g3, g4), "T": t,
            "skew": g3, "kurt": g4, "rho1": rho}


# ---------------------------------------------------------------- stages
def stage_train() -> int:
    df = load_panel()
    tr = df.filter((pl.col("date") >= TRAIN[0]) & (pl.col("date") <= TRAIN[1]))
    print(f"TRAIN {TRAIN[0]}..{TRAIN[1]}: {tr.height:,} name-days, "
          f"{tr['date'].n_unique()} sessions, {tr['sym'].n_unique()} names\n")
    res = []
    for s in SIGNALS:
        _dates, ics = session_ic(tr, s)
        if ics.size < 30:
            res.append({"signal": s, "ic": float("nan"), "p": 1.0, "n_sessions": int(ics.size),
                        "ci_lo": float("nan"), "ci_hi": float("nan")})
            continue
        lo, hi, p = boot_mean(ics)
        res.append({"signal": s, "ic": float(ics.mean()), "ci_lo": lo, "ci_hi": hi,
                    "p": p, "n_sessions": int(ics.size)})
    keep = bh_fdr([r["p"] for r in res], FDR_Q)
    for r, k in zip(res, keep, strict=True):
        r["admitted"] = bool(k)
        r["sign"] = float(np.sign(r["ic"])) if np.isfinite(r["ic"]) and r["ic"] != 0 else 0.0

    print(f"{'signal':14}{'IC':>9}{'95% CI':>20}{'p':>8}{'sess':>6}  admitted")
    for r in sorted(res, key=lambda z: z["p"]):
        print(f"{r['signal']:14}{r['ic']:+9.4f}[{r['ci_lo']:+8.4f},{r['ci_hi']:+8.4f}]"
              f"{r['p']:8.4f}{r['n_sessions']:6d}  {'YES' if r['admitted'] else '.'}")
    admitted = [r["signal"] for r in res if r["admitted"] and r["sign"] != 0]
    print(f"\nBH-FDR q={FDR_Q}: {len(admitted)} admitted -> {admitted}")
    ADMITTED.write_text(json.dumps(
        {"train": TRAIN, "fdr_q": FDR_Q, "per_signal": res, "admitted": admitted,
         "signs": {r["signal"]: r["sign"] for r in res}}, indent=1), encoding="utf-8")
    print(f"wrote {ADMITTED.relative_to(REPO)}")
    if not admitted:
        print("\nOUTCOME: NULL-AT-ADMISSION -- validate is NOT consumed.")
    return 0


def stage_validate() -> int:
    if not ADMITTED.exists():
        print("REFUSING: admitted.json absent -- run `train` first.")
        return 2
    a = json.loads(ADMITTED.read_text(encoding="utf-8"))
    admitted, signs = a["admitted"], a["signs"]
    if not admitted:
        print("REFUSING: NULL-AT-ADMISSION -- validate must not be consumed.")
        return 3
    df = load_panel()
    out: dict = {"admitted": admitted, "signs": {s: signs[s] for s in admitted}}

    for tag, win in (("train", TRAIN), ("validate", VALID)):
        sub = df.filter((pl.col("date") >= win[0]) & (pl.col("date") <= win[1]))
        p = portfolio_daily(sub, admitted, signs)
        net = p["net_bps"].to_numpy()
        gross = p["gross_bps"].to_numpy()
        cost = p["cost_bps"].to_numpy()
        lo, hi, pv = boot_mean(net)
        out[tag] = {
            "sessions": p.height,
            "mean_gross": float(gross.mean()), "mean_cost": float(cost.mean()),
            "mean_net": float(net.mean()), "ci_lo": lo, "ci_hi": hi, "p": pv,
            "mean_net_double_cost": float(p["net_bps_2x"].to_numpy().mean()),
            "mean_net_optimistic_cost": float(p["net_bps_stress"].to_numpy().mean()),
            "adia": adia(net),
            "mean_long": float(p["long_ret"].to_numpy().mean()),
            "mean_short": float(p["short_ret"].to_numpy().mean()),
            "mean_mkt": float(p["mkt_ret"].to_numpy().mean()),
            "median_k": int(np.median(p["k"].to_numpy())),
        }
        p.drop(["long_names", "short_names"]).write_parquet(EXP / f"daily_{tag}.parquet")

    v = out["validate"]
    passes_ci = v["ci_lo"] > 0
    passes_2x = v["mean_gross"] >= 2.0 * v["mean_cost"]
    out["verdict"] = ("PASS" if (passes_ci and passes_2x) else
                      "FAIL" if (v["ci_hi"] < 0 or not passes_2x) else "BETWEEN")
    out["passes_ci_lo_gt_0"] = passes_ci
    out["passes_gross_ge_2x_cost"] = passes_2x
    (EXP / "result.json").write_text(json.dumps(out, indent=1, allow_nan=False), encoding="utf-8")

    for tag in ("train", "validate"):
        r = out[tag]
        print(f"\n=== {tag.upper()} ({r['sessions']} sessions, {r['median_k']} names/leg) ===")
        print(f"  gross {r['mean_gross']:+8.3f}   cost {r['mean_cost']:7.3f}   "
              f"NET {r['mean_net']:+8.3f} bps/day  [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]  p={r['p']:.4f}")
        print(f"  net @6.0bps (2x) {r['mean_net_double_cost']:+8.3f}   "
              f"net @0.85bps (measured median) {r['mean_net_optimistic_cost']:+8.3f}")
        ad = r["adia"]
        print(f"  ADIA: SR(daily) {ad['sr_native']:+.4f}  PSR {ad['psr_sr0_0']:.4f}  "
              f"MinTRL {ad['min_trl']:.0f} sessions  T={ad['T']}")
        print(f"  long {r['mean_long']:+.2f} / short {r['mean_short']:+.2f} / "
              f"universe {r['mean_mkt']:+.2f} bps")
    print(f"\nVERDICT: {out['verdict']}  (CI-lo>0 {passes_ci}; gross>=2x cost {passes_2x})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M28 open-cross battery.")
    ap.add_argument("stage", choices=["train", "validate"])
    args = ap.parse_args(argv)
    return stage_train() if args.stage == "train" else stage_validate()


if __name__ == "__main__":
    sys.exit(main())
