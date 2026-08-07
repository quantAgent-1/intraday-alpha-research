"""Backfill 1-minute bars for the R2-A Stage-3 exit leg (quote-free variant).

Needed because the quote-free variant prices the exit off `bars1m` instead of `bbo1s`:
  * the 5 discovery SEMIS  -> so validation gate V3 (bars1m exit vs bbo1s exit) can be
    computed on all 10 discovery names, not just the 5 megacaps that already have bars1m;
  * the 16 OOS test names  -> the exit leg for the actual test.

Reuses `enginev51.data.backfill.run_letf_bars`, which issues ONE multi-symbol request per
month (`fetch_bars_multi`) and writes through the standard atomic partition writer -- so
these partitions are schema-identical to the existing bars1m lake.

Months are hard-capped at 2026-05 so the sealed holdout (>= 2026-06-01) is never fetched.

    uv run python scripts/backfill_bars1m_oos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from enginev51.config import get_settings  # noqa: E402
from enginev51.data import store  # noqa: E402
from enginev51.data.backfill import run_letf_bars  # noqa: E402
from enginev51.protocol import SealViolation  # noqa: E402

DISCOVERY_SEMIS = ["KLAC", "MRVL", "LRCX", "TXN", "AMAT"]
OOS = ["VRTX", "BKNG", "ISRG", "AMGN", "HON", "INTU", "TMUS", "GILD",
       "MDLZ", "COST", "PEP", "ADBE", "CMCSA", "SBUX", "CSCO", "QCOM"]
SYMBOLS = DISCOVERY_SEMIS + OOS

FIRST_MONTH = "2024-01"
LAST_MONTH = "2026-05"          # hard cap: the holdout (>= 2026-06-01) is never fetched


def months(a: str, b: str) -> list[str]:
    out, y, m = [], int(a[:4]), int(a[5:7])
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def main() -> int:
    settings = get_settings()
    feed = settings.data_feed_type
    work = [
        (s, mo)
        for s in SYMBOLS
        for mo in months(FIRST_MONTH, LAST_MONTH)
        if not any(store.partition_exists(r, feed, "bars1m", s, mo) for r in settings.read_roots)
    ]
    if not work:
        print("nothing to do -- all partitions present")
        return 0
    mo_set = sorted({m for _, m in work})
    if max(mo_set) > LAST_MONTH:
        raise SealViolation("holdout guard tripped")
    print(f"bars1m backfill: {len({s for s, _ in work})} symbols x {len(mo_set)} months "
          f"= {len(work)} partitions, {len(mo_set)} multi-symbol requests "
          f"({mo_set[0]}..{mo_set[-1]})")
    written = run_letf_bars(settings, work)
    print(f"wrote {written} partitions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
