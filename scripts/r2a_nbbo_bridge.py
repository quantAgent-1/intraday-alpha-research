"""V-NB bridge gate (R2A-oos Amendment 3): does the discovery result survive NBBO signing?

Rebuilds the 5 discovery-semis panel rows with `r2a_prong0.process_symbol` VERBATIM but
with the quote root redirected to the Alpaca-derived NBBO lake (`data/raw/bbo1s_nbbo`),
splices them with the owned-quote megacap rows from the cached panel, and recomputes the
discovery daily-portfolio mid (reference object: +22.36 [+4.28, +40.36], T=513).

GATE (pre-declared in PREDECLARATION_AMENDMENT_3.md before this script existed):
  same sign AND within +/-40% of +22.36 (i.e. in [+13.4, +31.3]) AND CI-lo > 0.

PASS -> the orchestrator registers `retail_fade_daily_v1` (ledger row + marker) and the
        decisive OOS runner may execute.
FAIL -> the discovery signal is partly a quote-source artifact: OOS cancelled, virgin
        names stay unconsumed, family not registered. That outcome is itself reportable.

    uv run python scripts/r2a_nbbo_bridge.py
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

SEMIS = ["KLAC", "MRVL", "LRCX", "TXN", "AMAT"]
MEGA = ["NVDA", "TSLA", "AMD", "MU", "GOOGL"]
NBBO_ROOT = REPO / "data" / "raw" / "bbo1s_nbbo"
PANEL_PQ = REPO / "research" / "experiments" / "R2A-prong0" / "panel.parquet"
OUT_DIR = REPO / "research" / "experiments" / "R2A-oos"

REF_MEAN = 22.36                 # discovery daily-portfolio mid (owned quotes)
BAND = (13.4, 31.3)              # +/-40% band, fixed in Amendment 3
SEED, REPS = 7, 2000


def _worker(sym: str) -> list[dict]:
    """Rebuild one semi's panel rows with the quote root redirected to NBBO."""
    import r2a_prong0 as R
    R.BBO_DIR = NBBO_ROOT        # patch inside the worker process, before any BboCache
    recs, _meta = R.process_symbol(sym)
    return recs


def daily_portfolio(rows: list[dict]) -> pl.DataFrame:
    ev = pl.DataFrame(rows)
    fired = []
    for key, g in ev.partition_by("sym", as_dict=True, maintain_order=True).items():
        sym = key[0] if isinstance(key, tuple) else key
        a = np.abs(g["oli"].to_numpy())
        q3 = float(np.percentile(a, 75))
        if q3 == 0.0:
            continue
        m = a >= q3
        for d, o, r in zip(g["date"].to_numpy()[m], g["oli"].to_numpy()[m],
                           g["ret"].to_numpy()[m], strict=True):
            fired.append({"date": str(d), "sym": sym, "fade": float(-np.sign(o) * r)})
    fe = pl.DataFrame(fired)
    return fe.group_by("date").agg(pl.col("fade").mean().alias("mid"),
                                   pl.len().alias("k")).sort("date")


def boot(v: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    n = v.size
    b = np.array([v[rng.integers(0, n, n)].mean() for _ in range(REPS)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def main() -> int:
    missing = [s for s in SEMIS
               if not (NBBO_ROOT / s).exists() or len(list((NBBO_ROOT / s).glob("*.parquet"))) < 25]
    if missing:
        print(f"REFUSING: NBBO quote partitions incomplete for {missing} "
              f"(need >=25 monthly files each). Wait for the backfill chain.")
        return 2

    base = pl.read_parquet(PANEL_PQ)
    mega_rows = base.filter(pl.col("sym").is_in(MEGA)).select(
        ["sym", "date", "oli", "ret"]).to_dicts()
    semi_rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=5) as ex:
        for recs in ex.map(_worker, SEMIS):
            semi_rows.extend(
                {k: r[k] for k in ("sym", "date", "oli", "ret")} for r in recs)
    print(f"NBBO semis rows: {len(semi_rows):,}   owned mega rows: {len(mega_rows):,}")

    daily = daily_portfolio(mega_rows + semi_rows)
    mid = daily["mid"].to_numpy()
    lo, hi = boot(mid)
    mean = float(mid.mean())

    # diagnostic: per-name OLI agreement, owned vs NBBO, on matched name-days
    nb = pl.DataFrame(semi_rows)
    own = base.filter(pl.col("sym").is_in(SEMIS)).select(
        ["sym", "date", pl.col("oli").alias("oli_own")])
    j = nb.join(own, on=["sym", "date"], how="inner")
    diag = {}
    for key, g in j.partition_by("sym", as_dict=True, maintain_order=True).items():
        s = key[0] if isinstance(key, tuple) else key
        diag[s] = {"n": g.height,
                   "corr": round(float(np.corrcoef(g["oli"].to_numpy(),
                                                   g["oli_own"].to_numpy())[0, 1]), 4)}

    ok = (mean > 0) and (BAND[0] <= mean <= BAND[1]) and (lo > 0)
    verdict = "V-NB PASS" if ok else "V-NB FAIL"
    res = {"daily_mid_nbbo": {"mean": mean, "ci_lo": lo, "ci_hi": hi, "T": daily.height,
                              "fires_per_day": float(daily["k"].mean())},
           "reference": {"mean": REF_MEAN, "band": BAND},
           "oli_agreement_semis": diag, "verdict": verdict}
    (OUT_DIR / "vnb_result.json").write_text(
        json.dumps(res, indent=1, allow_nan=False), encoding="utf-8")

    print(f"discovery daily mid under NBBO signing: {mean:+.2f} [{lo:+.2f}, {hi:+.2f}] "
          f"T={daily.height}  (reference {REF_MEAN:+.2f}, band [{BAND[0]}, {BAND[1]}])")
    print("semis OLI corr owned-vs-NBBO: "
          + ", ".join(f"{k} {v['corr']:+.3f} (n={v['n']})" for k, v in diag.items()))
    print(f"\nVERDICT: {verdict}")
    if ok:
        print("Next: orchestrator registers retail_fade_daily_v1 (ledger row + "
              "registration_marker.json), then scripts/r2a_oos_run.py")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
