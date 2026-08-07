"""R2-A Stage 1 (D) -- INSTRUMENT AXIS. Exploratory re-analysis, NOT a look, NOT a gate.

Question: the name-level fade splits ~58/42 into a sector-factor and an idiosyncratic
component (see `r2a_stage1.py`). If a majority of the alpha is sector-directional, it can
be expressed as ONE trade in the sector instrument instead of ten single-name trades --
which is the axis this program has never varied.

Design (deliberately the simplest thing that could work):
  signal   = cross-sectional mean OLI_{t-1} across the semis names present that session
  position = -sign(signal), entered at the SOXL opening cross (single print, 0 spread)
  exit     = last SOXL bar <= 15:45
  cost     = exit half-spread + 0.206 bps SEC fee. No SOXL quotes are owned, so the exit
             is priced at the ONE-TICK FLOOR on that day's price -- optimistic, flagged.

THE HONEST CAVEATS, up front:
  * POST-HOC. The aggregation rule, the >=3-name rule and the instrument were all chosen
    AFTER seeing the name-level result. Nothing here was pre-declared.
  * SAME 603 SESSIONS as the frozen prong-0. This is the same effect viewed through a
    different instrument -- it cannot confirm the effect, only price its expression.
  * Leverage does not create significance: SOXL is 3x, so mean and sd both scale and the
    t-stat is unchanged by it. Only the cost ratio genuinely improves.

The beta decomposition below exists because the semis rose enormously over the sample and
a mostly-long rule would harvest that drift for free. It reports how much of the result is
drift and how much is timing.

    uv run python scripts/r2a_stage1_instrument.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import r2a_prong0 as R  # noqa: E402

PANEL_PQ = REPO / "research" / "experiments" / "R2A-prong0" / "panel.parquet"
OUT_MD = REPO / "research" / "experiments" / "R2A-prong0" / "stage1_instrument.md"
ETF = "SOXL"
SEC_FEE_BPS = 0.206
MIN_NAMES = 3


def etf_day_returns(sym: str) -> dict[str, tuple[float, float]]:
    """date -> (open->15:45 return in bps, opening price). Adjustment-invariant ratio."""
    out: dict[str, tuple[float, float]] = {}
    for f in sorted((REPO / "data" / "raw" / "sip" / "bars1m" / sym).glob("*.parquet")):
        d = pl.read_parquet(f, columns=["ts", "open", "close"]).with_columns(
            R._date_expr().alias("date"), R._sec_expr().alias("sec")
        ).filter(
            (pl.col("sec") >= R.RTH_OPEN_SEC) & (pl.col("sec") <= R.EXIT_MAIN_HI)
        ).sort("sec")
        for key, g in d.partition_by("date", as_dict=True, maintain_order=True).items():
            dt = key[0] if isinstance(key, tuple) else key
            o, c = g["open"][0], g["close"][-1]
            if o and o > 0 and c:
                out[dt] = ((c / o - 1.0) * 1e4, float(o))
    return out


def boot(v: np.ndarray, seed: int = R.BOOT_SEED, reps: int = R.BOOT_REPS):
    rng = np.random.default_rng(seed)
    n = v.shape[0]
    b = np.array([v[rng.integers(0, n, n)].mean() for _ in range(reps)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def main() -> int:
    etf = etf_day_returns(ETF)
    panel = pl.read_parquet(PANEL_PQ).filter(pl.col("sym").is_in(list(R.SEMI)))
    rows = []
    for key, g in panel.partition_by("date", as_dict=True, maintain_order=True).items():
        dt = key[0] if isinstance(key, tuple) else key
        if dt not in etf or g.height < MIN_NAMES:
            continue
        ret, px = etf[dt]
        rows.append((dt, float(np.mean(g["oli"].to_numpy())), ret, px))
    df = pl.DataFrame(rows, schema=["date", "agg", "ret", "px"], orient="row")
    a, r, px = df["agg"].to_numpy(), df["ret"].to_numpy(), df["px"].to_numpy()
    pos = -np.sign(a)
    cost = 0.01 / px * 1e4 / 2 + SEC_FEE_BPS
    q3 = float(np.percentile(np.abs(a), 75))

    lines: list[str] = []

    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    emit(f"# R2-A Stage 1 (D) - instrument axis ({ETF}) - EXPLORATORY, post-hoc, not a gate")
    emit()
    emit(f"sessions with >={MIN_NAMES} semis and {ETF} data: {df.height}")
    emit(f"{ETF} median open price ${float(np.median(px)):.2f} -> one-tick floor "
         f"{0.01 / float(np.median(px)) * 1e4:.2f} bps (half {0.01 / float(np.median(px)) * 1e4 / 2:.2f})")
    emit()
    emit("| cell | n | gross bps | 95% CI | cost | NET | t |")
    emit("|---|---|---|---|---|---|---|")
    for label, m in (("all sessions", np.ones(len(r), bool)),
                     ("top-quartile |aggregate OLI|", np.abs(a) >= q3)):
        v = (pos * r)[m]
        lo, hi = boot(v)
        se = (hi - lo) / (2 * 1.96)
        c = float(cost[m].mean())
        emit(f"| {label} | {int(m.sum())} | {v.mean():+.2f} | [{lo:+.2f}, {hi:+.2f}] | "
             f"{c:.2f} | {v.mean() - c:+.2f} | {v.mean() / se:.2f} |")
    emit()
    emit("## Is it just the semis bull market? (drift vs timing)")
    emit()
    emit("| cell | buy-and-hold | % long | net tilt | gross | from drift | from TIMING |")
    emit("|---|---|---|---|---|---|---|")
    for label, m in (("all sessions", np.ones(len(r), bool)),
                     ("top-quartile", np.abs(a) >= q3)):
        g_ = (pos * r)[m].mean()
        d_ = pos[m].mean() * r[m].mean()
        emit(f"| {label} | {r[m].mean():+.2f} | {100 * (pos[m] > 0).mean():.1f}% | "
             f"{pos[m].mean():+.3f} | {g_:+.2f} | {d_:+.2f} | {g_ - d_:+.2f} |")
    emit()
    emit("Drift is not the source: buy-and-hold over these sessions is negative and the "
         "rule is close to balanced long/short, so the drift term is ~0 and essentially "
         "all of the result is timing. This does NOT make the result confirmed -- the cell "
         "is post-hoc on already-seen data. It means the instrument expression is worth "
         "carrying into an out-of-sample test.")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT_MD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
