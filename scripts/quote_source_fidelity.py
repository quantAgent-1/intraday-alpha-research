"""V-QS gate: does Alpaca-downsampled quote data reproduce the owned Databento bbo1s lake?

Pre-declared in R2A-oos PREDECLARATION_AMENDMENT_2.md section 2 BEFORE this script ran.
Five owned (name, day) pairs spanning tiers; for each:

  V-QS1  matched-second mids: median |dmid| <= 0.5 bps AND >= 99% of seconds within 2 bps
  V-QS2  day-level OLI, frozen signing, same trades, each quote source: max |dOLI| <= 0.05
  V-QS3  exit_mid (last valid mid <= 15:45): |d| <= 1.0 bps on every sampled day

Any failure -> the bulk pull may NOT be consumed for a verdict.

    uv run python scripts/quote_source_fidelity.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import backfill_trades_semis as B  # noqa: E402
import r2a_prong0 as R  # noqa: E402
from backfill_quotes_oos import pull_day  # noqa: E402

SAMPLE = [("KLAC", "2025-03-18"), ("TXN", "2024-06-05"), ("MU", "2024-06-05"),
          ("NVDA", "2025-10-15"), ("AMAT", "2025-03-18")]
OUT = REPO / "research" / "experiments" / "R2A-oos" / "quote_source_fidelity.md"
RATE = 40      # gentle: the trades backfill owns most of the 200/min budget


def valid_mid(df: pl.DataFrame) -> pl.DataFrame:
    return (df.filter((pl.col("bid") > 0) & (pl.col("ask") > pl.col("bid")))
              .with_columns(((pl.col("bid") + pl.col("ask")) / 2).alias("mid"))
              .select(["ts", "mid"]))


def day_oli(sym: str, date: str, q_ts: np.ndarray, q_mid: np.ndarray) -> float | None:
    tr = R.load_trades_oddlot(sym, date)
    if tr is None or tr[0].shape[0] == 0:
        return None
    t_ts, t_px, t_sz = tr
    sign = R.sign_prints(t_ts, t_px, q_ts, q_mid)
    buy = float(t_sz[sign > 0].sum())
    sell = float(t_sz[sign < 0].sum())
    return (buy - sell) / (buy + sell) if (buy + sell) > 0 else None


def main() -> int:
    settings = B.get_settings()
    hist = B.AlpacaHist(settings)
    hist.limiter = B.RateLimiter(RATE)
    lines = ["# V-QS quote-source fidelity (Alpaca-downsampled vs owned Databento bbo1s)", ""]
    checks: list[tuple[str, bool, str]] = []
    try:
        for sym, date in SAMPLE:
            own_day = R.BboCache(sym).get_day(date)
            if own_day is None:
                checks.append((f"{sym} {date}: owned bbo1s present", False, "missing"))
                continue
            o_ts, _o_sec, o_mid = own_day
            alp = pull_day(hist, sym, date)
            a = valid_mid(alp)
            if a.height == 0:
                checks.append((f"{sym} {date}: alpaca quotes present", False, "empty"))
                continue
            a_ts, a_mid = a["ts"].to_numpy(), a["mid"].to_numpy()

            # V-QS1: compare on matched second stamps
            common, oi, ai = np.intersect1d(o_ts, a_ts, return_indices=True)
            d = np.abs(o_mid[oi] - a_mid[ai]) / o_mid[oi] * 1e4
            med, within2 = float(np.median(d)), float((d <= 2.0).mean())
            checks.append((f"V-QS1 {sym} {date}: mids match "
                           f"({len(common):,} matched seconds)",
                           med <= 0.5 and within2 >= 0.99,
                           f"median {med:.3f} bps; within 2 bps {100 * within2:.2f}%"))

            # V-QS2: OLI with each source, same trades, frozen signing
            o1 = day_oli(sym, date, o_ts, o_mid)
            o2 = day_oli(sym, date, a_ts, a_mid)
            if o1 is None or o2 is None:
                checks.append((f"V-QS2 {sym} {date}: OLI computable", False,
                               f"own={o1} alp={o2}"))
            else:
                checks.append((f"V-QS2 {sym} {date}: |dOLI| <= 0.05",
                               abs(o1 - o2) <= 0.05,
                               f"own {o1:+.4f} vs alpaca {o2:+.4f} (d={abs(o1 - o2):.4f})"))

            # V-QS3: exit mid (ET seconds via the frozen expressions)
            oe = R.exit_mid(own_day[1], o_mid, R.EXIT_MAIN_HI, R.EXIT_MAIN_LO)
            a_sec = (pl.DataFrame({"ts": a_ts}).with_columns(R._sec_expr().alias("s"))
                     )["s"].to_numpy()
            ae = R.exit_mid(a_sec, a_mid, R.EXIT_MAIN_HI, R.EXIT_MAIN_LO)
            if oe is None or ae is None:
                checks.append((f"V-QS3 {sym} {date}: exit mid computable", False,
                               f"own={oe} alp={ae}"))
            else:
                dbps = abs(oe - ae) / oe * 1e4
                checks.append((f"V-QS3 {sym} {date}: exit mid |d| <= 1 bps",
                               dbps <= 1.0, f"{dbps:.3f} bps"))
    finally:
        hist.close()

    ok = all(p for _n, p, _d in checks)
    for name, passed, detail in checks:
        line = f"- [{'PASS' if passed else 'FAIL'}] {name} — {detail}"
        lines.append(line)
        print(line)
    lines += ["", f"## VERDICT: {'V-QS PASS — bulk pull may be consumed' if ok else 'V-QS FAIL — bulk pull may NOT be consumed'}"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
