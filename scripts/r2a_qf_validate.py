"""Run the pre-declared V1/V2/V3 admissibility gate for the quote-free variant.

Thresholds are frozen in `research/experiments/R2A-oos/PREDECLARATION.md` section 2 and
are duplicated here as constants ONLY so the script is self-checking; they are not to be
edited. If the gate fails, Stage 3 is METHOD-BLOCKED and no OOS statistic may be quoted.

    uv run python scripts/r2a_qf_validate.py
"""

from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import r2a_prong0 as R  # noqa: E402
import r2a_qf as QF  # noqa: E402

PANEL_PQ = REPO / "research" / "experiments" / "R2A-prong0" / "panel.parquet"
OUT_DIR = REPO / "research" / "experiments" / "R2A-oos"
OUT_MD = OUT_DIR / "validation.md"
QF_PANEL = OUT_DIR / "panel_discovery_qf.parquet"

V1_MIN_CORR = 0.90
V2_REF = 14.8744
V2_TOL = 0.30
V3_MAX_MED_ABS_DIFF = 3.0


def _work(sym: str):
    recs, meta = QF.process_symbol_qf(sym)
    return sym, recs, meta


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    qrows: list[dict] = []
    with ProcessPoolExecutor(max_workers=min(len(R.PANEL), 16)) as ex:
        for sym, recs, meta in ex.map(_work, R.PANEL):
            qrows.extend(recs)
            print(f"  {sym:6} qf-kept={meta['n_kept']:5d} / cand={meta['n_candidates']:5d}"
                  f"   funnel={ {k: v for k, v in meta['funnel'].items() if v} }")
    qf = pl.DataFrame(qrows)
    qf.write_parquet(QF_PANEL)
    base = pl.read_parquet(PANEL_PQ)

    j = base.select(["sym", "date", "oli", "ret"]).join(
        qf.select(["sym", "date", pl.col("oli").alias("oli_qf"), pl.col("ret").alias("ret_qf")]),
        on=["sym", "date"], how="inner",
    )
    lines: list[str] = []

    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    emit("# R2-A quote-free variant - pre-declared admissibility gate V1/V2/V3")
    emit()
    emit(f"discovery rows: quote-based {base.height}, quote-free {qf.height}, "
         f"matched on (sym,date) {j.height}")
    emit()

    # V1 -----------------------------------------------------------------
    a, b = j["oli"].to_numpy(), j["oli_qf"].to_numpy()
    v1 = float(np.corrcoef(a, b)[0, 1])
    v1_ok = v1 >= V1_MIN_CORR
    emit(f"**V1** corr(OLI quote-signed, OLI tick-signed) = **{v1:.4f}** "
         f"(threshold >= {V1_MIN_CORR}) -> {'PASS' if v1_ok else 'FAIL'}")
    per = []
    for s in R.PANEL:
        m = j.filter(pl.col("sym") == s)
        if m.height > 2:
            per.append((s, float(np.corrcoef(m['oli'].to_numpy(), m['oli_qf'].to_numpy())[0, 1]),
                        m.height))
    emit()
    emit("| name | corr | n |")
    emit("|---|---|---|")
    for s, c, n in per:
        emit(f"| {s} | {c:.4f} | {n} |")
    emit()

    # V2 -----------------------------------------------------------------
    qrecs = qf.to_dicts()
    gb_qf = R.gate_b_stats(qrecs, "ret")
    lo_b, hi_b = V2_REF * (1 - V2_TOL), V2_REF * (1 + V2_TOL)
    v2_ok = (gb_qf["mean"] > 0) and (lo_b <= gb_qf["mean"] <= hi_b)
    emit(f"**V2** quote-free top-quartile signed fade on the discovery panel = "
         f"**{gb_qf['mean']:+.2f}** bps [{gb_qf['ci_lo']:+.2f}, {gb_qf['ci_hi']:+.2f}] "
         f"n={gb_qf['n']}")
    emit(f"    published quote-based reference {V2_REF:+.2f}; admissible band "
         f"[{lo_b:+.2f}, {hi_b:+.2f}] -> {'PASS' if v2_ok else 'FAIL'}")
    matched = qf.join(j.select(["sym", "date"]), on=["sym", "date"], how="inner")
    gb_i = R.gate_b_stats(matched.to_dicts(), "ret")
    emit(f"    (non-gating, matched rows only: {gb_i['mean']:+.2f} bps n={gb_i['n']})")
    emit()

    # V3 -----------------------------------------------------------------
    d = np.abs(j["ret"].to_numpy() - j["ret_qf"].to_numpy())
    v3 = float(np.median(d))
    v3_ok = v3 <= V3_MAX_MED_ABS_DIFF
    emit(f"**V3** median |bars1m-exit return - bbo1s-exit return| = **{v3:.2f}** bps "
         f"(threshold <= {V3_MAX_MED_ABS_DIFF}) -> {'PASS' if v3_ok else 'FAIL'}")
    emit(f"    mean {float(d.mean()):.2f}, p90 {float(np.percentile(d, 90)):.2f}, "
         f"p99 {float(np.percentile(d, 99)):.2f} bps")
    emit()

    ok = v1_ok and v2_ok and v3_ok
    emit(f"## VERDICT: {'ADMISSIBLE - Stage 3 may proceed' if ok else 'METHOD-BLOCKED - Stage 3 abandoned'}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT_MD.relative_to(REPO)}")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
