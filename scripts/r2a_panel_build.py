"""Cache the R2-A per-name-day panel once, in parallel, so downstream analysis is instant.

The original prong-0 run (2026-07-24) read ~9.8 GB of tape, produced its summary and
discarded the per-name-day rows. Every follow-up question (different exit, different
hedge, different cost model) therefore costs another full tape read.

This builder calls `r2a_prong0.process_symbol` VERBATIM -- same signing machinery, same
guards, same records -- fanned out one process per symbol, and writes the resulting panel
to parquet. It computes no statistic and makes no economic claim: it is a cache.

Fidelity is checked by the consumer (`r2a_stage1.py`), which re-derives the published
gate (a)/(b) numbers from this panel and refuses to proceed unless they match.

    uv run python scripts/r2a_panel_build.py
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import polars as pl  # noqa: E402
import r2a_prong0 as R  # noqa: E402

OUT = REPO / "research" / "experiments" / "R2A-prong0" / "panel.parquet"


def _work(sym: str):
    t0 = time.time()
    recs, meta = R.process_symbol(sym)
    return sym, recs, meta, time.time() - t0


def main() -> int:
    t0 = time.time()
    print(f"building R2-A panel: {len(R.PANEL)} symbols, one process each")
    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=min(len(R.PANEL), 16)) as ex:
        for sym, recs, meta, dt in ex.map(_work, R.PANEL):
            rows.extend(recs)
            print(f"  {sym:6} kept={meta['n_kept']:5d} / cand={meta['n_candidates']:5d}"
                  f"   {dt:6.1f}s")
    if not rows:
        print("NO ROWS -- refusing to write")
        return 1

    df = pl.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(OUT)
    print(f"\nwrote {OUT.relative_to(REPO)}  rows={df.height}  "
          f"sessions={df['date'].n_unique()}  in {time.time() - t0:.1f}s total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
