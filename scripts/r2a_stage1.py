"""R2-A Stage 1 -- EXPLORATORY RE-ANALYSIS of an existing measurement. NOT a look.

Reads the cached panel (`r2a_panel_build.py`) and answers three questions the original
prong-0 could not, because it priced one instrument, one exposure and one flat cost floor:

  B. HEDGE     -- how much of gate (b)'s error bar is unwanted market exposure?
  C. DECOMPOSE -- is the +14.87 bps a sector-factor bet or an idiosyncratic one?
  D. COST      -- what is the effect NET of the real exit-leg cost, per name?

METHOD FIDELITY: every statistic is computed by `r2a_prong0.gate_a_stats` /
`gate_b_stats` VERBATIM (same residualisation, same winsorisation, same seed-7
session-clustered bootstrap, 2000 reps). Only the return column changes.

STATUS DISCIPLINE: this re-analyses the SAME 4,356 name-days that produced the frozen
prong-0 result. It therefore CANNOT overturn that adjudication and no threshold here is
a gate. It is a power-and-cost diagnostic whose sole purpose is to decide whether an
out-of-sample panel expansion is worth building. Any confirmation must come from names
this panel has never seen.

    uv run python scripts/r2a_stage1.py
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import r2a_prong0 as R  # noqa: E402

PANEL_PQ = REPO / "research" / "experiments" / "R2A-prong0" / "panel.parquet"
OUT_MD = REPO / "research" / "experiments" / "R2A-prong0" / "stage1.md"

# Published prong-0 values (research/experiments/R2A-prong0/summary.md) -- fidelity anchors.
PUB_RHO_A = 0.0067
PUB_MEAN_B = 14.8744

# Unlevered sector proxies (M13 precedent: "F3 SOXL/3 (semis proxy)").
HEDGE_FOR = {"semi": ("SOXL", 3.0), "mega": ("TQQQ", 3.0)}
SEC_FEE_BPS = 0.206          # COST_MODEL v1, sell side
MIN_BETA_OBS = 60            # past-only beta warm-up


# --------------------------------------------------------------------------- #
def hedge_returns(sym: str, lev: float) -> dict[str, float]:
    """open(09:30 bar) -> close(last bar <= 15:45) return in bps, / leverage, by ET date.

    bars1m is split/dividend adjusted; a within-day ratio is invariant to that factor.
    """
    out: dict[str, float] = {}
    for f in sorted(glob.glob(str(REPO / "data" / "raw" / "sip" / "bars1m" / sym / "*.parquet"))):
        d = pl.read_parquet(f, columns=["ts", "open", "close"])
        if d.height == 0:
            continue
        d = d.with_columns(
            R._date_expr().alias("date"),      # canonical ET expressions (Int32-safe)
            R._sec_expr().alias("sec"),
        ).filter((pl.col("sec") >= R.RTH_OPEN_SEC) & (pl.col("sec") <= R.EXIT_MAIN_HI))
        for date, g in d.sort("sec").group_by("date", maintain_order=True):
            key = date[0] if isinstance(date, tuple) else date
            o, c = g["open"][0], g["close"][-1]
            if o and c and o > 0:
                out[key] = (c / o - 1.0) * 1e4 / lev
    return out


def exit_half_spread_bps() -> dict[str, float]:
    """Median quoted spread in the 15:40-15:45 exit window -> half-spread, per name."""
    out: dict[str, float] = {}
    for sym in R.PANEL:
        vals: list[float] = []
        for f in sorted(glob.glob(str(REPO / "data" / "raw" / "bbo1s" / sym / "*.parquet"))):
            d = pl.read_parquet(f, columns=["ts", "bid", "ask"]).filter(
                (pl.col("bid") > 0) & (pl.col("ask") > pl.col("bid"))
            )
            if d.height == 0:
                continue
            d = d.with_columns(R._sec_expr().alias("sec")).filter(
                (pl.col("sec") >= R.EXIT_MAIN_LO) & (pl.col("sec") <= R.EXIT_MAIN_HI)
            )
            if d.height:
                vals.append(float(
                    ((d["ask"] - d["bid"]) / ((d["ask"] + d["bid"]) / 2) * 1e4).median()
                ))
        out[sym] = float(np.median(vals)) / 2.0 if vals else float("nan")
    return out


def se_of(d: dict) -> float:
    return (d["ci_hi"] - d["ci_lo"]) / (2 * 1.96)


def betas(recs: list[dict], past_only: bool) -> None:
    """Attach 'beta' to each record: OLS of ret on the tier hedge return."""
    by: dict[str, list[dict]] = {}
    for r in recs:
        by.setdefault(r["sym"], []).append(r)
    for _sym, rows in by.items():
        rows.sort(key=lambda r: r["date"])
        y = np.array([r["ret"] for r in rows])
        x = np.array([r["h"] for r in rows])
        if not past_only:
            b = float(np.polyfit(x, y, 1)[0]) if len(rows) >= 2 else 1.0
            for r in rows:
                r["beta"] = b
            continue
        for i, r in enumerate(rows):                      # strictly prior rows only
            if i < MIN_BETA_OBS:
                r["beta"] = float("nan")
            else:
                r["beta"] = float(np.polyfit(x[:i], y[:i], 1)[0])


def main() -> int:
    if not PANEL_PQ.exists():
        print("panel missing -- run scripts/r2a_panel_build.py first")
        return 1
    recs = pl.read_parquet(PANEL_PQ).to_dicts()
    print(f"panel: {len(recs)} name-days, {len({r['date'] for r in recs})} sessions\n")

    # ---- fidelity gate ---------------------------------------------------- #
    a0 = R.gate_a_stats(recs, "ret")
    b0 = R.gate_b_stats(recs, "ret")
    ok = (abs(a0["rho"] - PUB_RHO_A) < 5e-5) and (abs(b0["mean"] - PUB_MEAN_B) < 5e-4)
    print("FIDELITY vs published prong-0")
    print(f"  gate (a) rho  {a0['rho']:+.4f}   published {PUB_RHO_A:+.4f}")
    print(f"  gate (b) mean {b0['mean']:+.4f}   published {PUB_MEAN_B:+.4f}")
    print(f"  -> {'MATCH' if ok else 'MISMATCH -- refusing to interpret'}\n")
    if not ok:
        return 2

    # ---- hedge series ------------------------------------------------------ #
    hedges = {tier: hedge_returns(sym, lev) for tier, (sym, lev) in HEDGE_FOR.items()}
    miss = 0
    for r in recs:
        h = hedges[r["tier"]].get(r["date"])
        if h is None:
            miss += 1
        r["h"] = h if h is not None else float("nan")
    recs_h = [r for r in recs if np.isfinite(r["h"])]
    print(f"hedge coverage: {len(recs_h)}/{len(recs)} name-days "
          f"(SOXL/3 for semis, TQQQ/3 for megacaps); {miss} unmatched\n")

    rows_out = []
    for label, past in (("in-sample beta (upper bound)", False),
                        ("past-only expanding beta (implementable)", True)):
        rr = [dict(r) for r in recs_h]
        betas(rr, past_only=past)
        rr = [r for r in rr if np.isfinite(r["beta"])]
        for r in rr:
            r["ret_fac"] = r["beta"] * r["h"]          # factor component
            r["ret_idio"] = r["ret"] - r["ret_fac"]    # residual component

        braw = R.gate_b_stats(rr, "ret")
        bfac = R.gate_b_stats(rr, "ret_fac")
        bidi = R.gate_b_stats(rr, "ret_idio")
        print(f"=== {label}  (n={len(rr)} name-days) ===")
        hdr = f"{'component':34} {'mean':>9} {'95% CI':>22} {'se':>7} {'t':>6}"
        print(hdr)
        for nm, d in (("signed fade, RAW (as published)", braw),
                      ("  = factor component (sector)", bfac),
                      ("  + idiosyncratic component", bidi)):
            se = se_of(d)
            print(f"{nm:34} {d['mean']:+9.2f} "
                  f"[{d['ci_lo']:+8.2f},{d['ci_hi']:+8.2f}] {se:7.2f} {d['mean'] / se:6.2f}")
        print(f"  SE ratio raw/idio: {se_of(braw) / se_of(bidi):.2f}x "
              f"(= {(se_of(braw) / se_of(bidi)) ** 2:.1f}x effective data)\n")
        rows_out.append((label, len(rr), braw, bfac, bidi))

    # ---- cost ------------------------------------------------------------- #
    hs = exit_half_spread_bps()
    print("=== NET OF REAL EXIT COST (entry at the opening cross = 0 spread) ===")
    print(f"{'name':6} {'topq n':>7} {'gross fade':>11} {'half-spr':>9} {'fee':>5} {'NET':>8}")
    pn = b0["per_name"]
    tot_n = tot_net = 0.0
    for sym in R.PANEL:
        d = pn.get(sym, {})
        n, g = d.get("topq_n", 0), d.get("topq_mean", float("nan"))
        c = hs.get(sym, float("nan")) + SEC_FEE_BPS
        net = g - c
        if n:
            tot_n += n
            tot_net += net * n
        print(f"{sym:6} {n:7d} {g:+11.2f} {hs.get(sym, float('nan')):9.2f} "
              f"{SEC_FEE_BPS:5.2f} {net:+8.2f}")
    print(f"{'POOLED':6} {int(tot_n):7d} {b0['mean']:+11.2f} "
          f"{'':9} {'':5} {tot_net / tot_n:+8.2f}  (n-weighted)\n")

    with OUT_MD.open("w", encoding="utf-8") as fh:
        fh.write("# R2-A Stage 1 - exploratory re-analysis (NOT a look, NOT a gate)\n\n")
        fh.write("Same 4,356 name-days as the frozen prong-0 result; cannot overturn it. "
                 "Statistics computed by `r2a_prong0.gate_b_stats` verbatim (seed 7, 2000 "
                 "session-clustered reps). Purpose: decide whether an out-of-sample panel "
                 "expansion is worth building.\n\n")
        fh.write(f"Fidelity: gate (a) rho {a0['rho']:+.4f} vs published {PUB_RHO_A:+.4f}; "
                 f"gate (b) mean {b0['mean']:+.4f} vs published {PUB_MEAN_B:+.4f} -> MATCH\n\n")
        for label, n, braw, bfac, bidi in rows_out:
            fh.write(f"## Decomposition - {label} (n={n})\n\n")
            fh.write("| component | mean bps | 95% CI | se | t |\n|---|---|---|---|---|\n")
            for nm, d in (("signed fade RAW", braw), ("factor (sector)", bfac),
                          ("idiosyncratic", bidi)):
                se = se_of(d)
                fh.write(f"| {nm} | {d['mean']:+.2f} | [{d['ci_lo']:+.2f}, "
                         f"{d['ci_hi']:+.2f}] | {se:.2f} | {d['mean'] / se:.2f} |\n")
            fh.write(f"\nSE ratio raw/idio {se_of(braw) / se_of(bidi):.2f}x\n\n")
        fh.write("## Net of real exit cost (entry at the opening cross = 0 spread)\n\n")
        fh.write("| name | top-q n | gross fade | half-spread 15:40-45 | SEC fee | NET |\n")
        fh.write("|---|---|---|---|---|---|\n")
        for sym in R.PANEL:
            d = pn.get(sym, {})
            g = d.get("topq_mean", float("nan"))
            c = hs.get(sym, float("nan")) + SEC_FEE_BPS
            fh.write(f"| {sym} | {d.get('topq_n', 0)} | {g:+.2f} | "
                     f"{hs.get(sym, float('nan')):.2f} | {SEC_FEE_BPS:.3f} | {g - c:+.2f} |\n")
        fh.write(f"| **POOLED** | {int(tot_n)} | {b0['mean']:+.2f} | | | "
                 f"**{tot_net / tot_n:+.2f}** |\n")
    print(f"wrote {OUT_MD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
