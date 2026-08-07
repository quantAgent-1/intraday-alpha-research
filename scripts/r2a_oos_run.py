"""THE DECISIVE TEST: the frozen R2-A rule on 16 virgin names (retail_fade_daily_v1).

Governed by R2A-oos PREDECLARATION.md + Amendments 2 and 3. This is the family's single
sanctioned historical look; the 16 names are consumed by this run regardless of outcome.

Refuses to run unless ALL of:
  1. vnb_result.json shows V-NB PASS (the discovery signal survived NBBO signing),
  2. registration_marker.json exists (family registered in the ledger BEFORE this run),
  3. trades + NBBO quote partitions are complete for all 16 names.

Method: `r2a_prong0.process_symbol` VERBATIM per name, quote root redirected to
`data/raw/bbo1s_nbbo`. Primary: mean of the daily equal-weight portfolio of that session's
fires (per-name Q3(|OLI|) rule), NET of measured per-name exit half-spread + 0.206 bps SEC
fee, session-bootstrap 95% CI (seed 7, 2000 reps).

Outcomes (fixed): CONFIRMED (net CI-lo>0 AND gross >= 2x cost) / REFUTED (CI-hi<0) /
NOT-CONFIRMED (CI spans 0, point < +6) / PARK-UNDERPOWERED (CI spans 0, point >= +6).

    uv run python scripts/r2a_oos_run.py
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

OOS = ["VRTX", "BKNG", "ISRG", "AMGN", "HON", "INTU", "TMUS", "GILD",
       "MDLZ", "COST", "PEP", "ADBE", "CMCSA", "SBUX", "CSCO", "QCOM"]
TECH_ADJ = {"QCOM", "ADBE", "INTU"}          # declared split, Amendment 2
NBBO_ROOT = REPO / "data" / "raw" / "bbo1s_nbbo"
TRADES = REPO / "data" / "raw" / "sip" / "trades"
OUT_DIR = REPO / "research" / "experiments" / "R2A-oos"

SEC_FEE = 0.206
SEED, REPS = 7, 2000
POINT_FLOOR = 6.0
PLACEBO_DRAWS, PLACEBO_SEED = 200, 101
EXIT_LO, EXIT_HI = 15 * 3600 + 40 * 60, 15 * 3600 + 45 * 60


def _worker(sym: str):
    import r2a_prong0 as R
    R.BBO_DIR = NBBO_ROOT
    recs, meta = R.process_symbol(sym)
    return sym, recs, meta


def measured_half_spread(sym: str) -> float:
    """Median 15:40-15:45 quoted half-spread (bps) from the name's own NBBO partitions."""
    import r2a_prong0 as R
    vals = []
    for f in sorted((NBBO_ROOT / sym).glob("*.parquet")):
        d = pl.read_parquet(f).filter((pl.col("bid") > 0) & (pl.col("ask") > pl.col("bid")))
        if d.height == 0:
            continue
        d = d.with_columns(R._sec_expr().alias("s")).filter(
            (pl.col("s") >= EXIT_LO) & (pl.col("s") <= EXIT_HI))
        if d.height:
            vals.append(float(((d["ask"] - d["bid"]) /
                               ((d["ask"] + d["bid"]) / 2) * 1e4).median()))
    return float(np.median(vals)) / 2.0 if vals else float("nan")


def boot(v: np.ndarray, seed: int = SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = v.size
    b = np.array([v[rng.integers(0, n, n)].mean() for _ in range(REPS)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def main() -> int:
    vnb = OUT_DIR / "vnb_result.json"
    if not vnb.exists() or json.loads(vnb.read_text(encoding="utf-8"))["verdict"] != "V-NB PASS":
        print("REFUSING: V-NB bridge gate has not passed.")
        return 2
    if not (OUT_DIR / "registration_marker.json").exists():
        print("REFUSING: retail_fade_daily_v1 not registered (marker absent).")
        return 3
    bad = [s for s in OOS
           if len(list((TRADES / s).glob("*.parquet"))) < 400
           or len(list((NBBO_ROOT / s).glob("*.parquet"))) < 25]
    if bad:
        print(f"REFUSING: data incomplete for {bad}.")
        return 4

    rows, funnels = [], {}
    with ProcessPoolExecutor(max_workers=8) as ex:
        for sym, recs, meta in ex.map(_worker, OOS):
            rows.extend(recs)
            funnels[sym] = {"kept": meta["n_kept"], **meta["funnel"]}
            print(f"  {sym:6} kept={meta['n_kept']:5d}")
    ev = pl.DataFrame(rows)
    hs = {s: measured_half_spread(s) for s in OOS}
    print("measured exit half-spreads (bps): "
          + ", ".join(f"{s} {v:.2f}" for s, v in sorted(hs.items())))

    fired = []
    for key, g in ev.partition_by("sym", as_dict=True, maintain_order=True).items():
        sym = key[0] if isinstance(key, tuple) else key
        a = np.abs(g["oli"].to_numpy())
        q3 = float(np.percentile(a, 75))
        if q3 == 0.0:
            continue
        m = a >= q3
        c = hs[sym] + SEC_FEE
        for d, o, r in zip(g["date"].to_numpy()[m], g["oli"].to_numpy()[m],
                           g["ret"].to_numpy()[m], strict=True):
            fired.append({"date": str(d), "sym": sym, "sign": float(-np.sign(o)),
                          "fade": float(-np.sign(o) * r), "ret": float(r), "cost": c})
    fe = pl.DataFrame(fired)
    daily = fe.group_by("date").agg(
        pl.col("fade").mean().alias("mid"),
        (pl.col("fade") - pl.col("cost")).mean().alias("net"),
        pl.col("cost").mean().alias("cost"), pl.len().alias("k")).sort("date")
    mid, net = daily["mid"].to_numpy(), daily["net"].to_numpy()
    mlo, mhi = boot(mid)
    nlo, nhi = boot(net)
    mean_cost = float(daily["cost"].to_numpy().mean())

    if nlo > 0 and mid.mean() >= 2 * mean_cost:
        verdict = "CONFIRMED"
    elif nhi < 0:
        verdict = "REFUTED"
    elif net.mean() < POINT_FLOOR:
        verdict = "NOT-CONFIRMED"
    else:
        verdict = "PARK-UNDERPOWERED"

    # ---- mandatory diagnostics (non-gating) ---- #
    per = fe.group_by("sym").agg(pl.col("fade").mean().alias("m"), pl.len().alias("n"))
    pos_names = int((per["m"].to_numpy() > 0).sum())
    yr = fe.with_columns(pl.col("date").str.slice(0, 4).alias("y")).group_by("y").agg(
        pl.col("fade").mean().alias("m"), pl.len().alias("n")).sort("y")
    tech = fe.filter(pl.col("sym").is_in(list(TECH_ADJ)))["fade"].to_numpy()
    rest = fe.filter(~pl.col("sym").is_in(list(TECH_ADJ)))["fade"].to_numpy()

    univ = ev.group_by("date").agg(pl.col("ret").mean().alias("mkt")).sort("date")
    dd = daily.join(univ, on="date", how="left").drop_nulls()
    bkt, mk = dd["mid"].to_numpy(), dd["mkt"].to_numpy()
    beta, alpha = np.polyfit(mk, bkt, 1)
    hedged = bkt - beta * mk                      # intercept-preserving
    hlo, hhi = boot(hedged)

    rng = np.random.default_rng(PLACEBO_SEED)
    fades = fe.select(["date", "ret"]).to_dicts()
    draws = []
    for _ in range(PLACEBO_DRAWS):
        sgn = rng.choice([-1.0, 1.0], size=len(fades))
        pf = pl.DataFrame({"date": [r["date"] for r in fades],
                           "f": [s * r["ret"] for s, r in zip(sgn, fades, strict=True)]})
        draws.append(float(pf.group_by("date").agg(pl.col("f").mean())["f"].mean()))
    draws = np.array(draws)
    pct = float((draws < mid.mean()).mean())

    res = {
        "event_n": fe.height, "T": daily.height, "fires_per_day": float(daily["k"].mean()),
        "daily_mid": {"mean": float(mid.mean()), "ci_lo": mlo, "ci_hi": mhi},
        "daily_net": {"mean": float(net.mean()), "ci_lo": nlo, "ci_hi": nhi},
        "mean_cost": mean_cost,
        "net_flat3": float((mid - (3.0 + SEC_FEE)).mean()),
        "net_flat6": float((mid - (6.0 + SEC_FEE)).mean()),
        "per_name": {r["sym"]: {"mean": round(r["m"], 2), "n": r["n"]}
                     for r in per.iter_rows(named=True)},
        "n_names_positive": pos_names,
        "by_year": {r["y"]: {"mean": round(r["m"], 2), "n": r["n"]}
                    for r in yr.iter_rows(named=True)},
        "tech_adj_mean": float(tech.mean()) if tech.size else None,
        "rest_mean": float(rest.mean()) if rest.size else None,
        "beta_vs_universe": float(beta),
        "hedged_mid": {"mean": float(hedged.mean()), "ci_lo": hlo, "ci_hi": hhi},
        "placebo": {"mean": float(draws.mean()), "sd": float(draws.std()),
                    "real_percentile": pct},
        "half_spreads": {k: round(v, 2) for k, v in hs.items()},
        "funnels": funnels,
        "verdict": verdict,
    }
    (OUT_DIR / "phase3_result.json").write_text(
        json.dumps(res, indent=1, allow_nan=False), encoding="utf-8")

    print("\n=== DECISIVE OOS RESULT (16 virgin names) ===")
    print(f"fires {fe.height:,}  T={daily.height}  {res['fires_per_day']:.2f}/day  "
          f"mean cost {mean_cost:.2f} bps")
    print(f"daily MID {mid.mean():+7.2f}  [{mlo:+7.2f}, {mhi:+7.2f}]")
    print(f"daily NET {net.mean():+7.2f}  [{nlo:+7.2f}, {nhi:+7.2f}]")
    print(f"names positive: {pos_names}/16   tech-adj {res['tech_adj_mean'] or 0:+.1f} "
          f"vs rest {res['rest_mean'] or 0:+.1f}")
    print(f"beta {beta:+.3f}; hedged mid {hedged.mean():+.2f} [{hlo:+.2f}, {hhi:+.2f}]")
    print(f"placebo: real sits at {100 * pct:.1f}th percentile of {PLACEBO_DRAWS} sign-shuffles")
    print(f"\nVERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
