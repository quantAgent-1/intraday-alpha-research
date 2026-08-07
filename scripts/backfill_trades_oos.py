"""Backfill SIP trades for the 16 OUT-OF-SAMPLE test names (R2-A Stage 3).

Thin wrapper over the VERIFIED `backfill_trades_semis.py`. It overrides exactly two
module globals -- the symbol list and the log path -- and then calls that module's own
`run_full`. The fetch, filter, schema-enforcement and atomic-write path are reused
byte-for-byte, so the new partitions cannot drift from the existing lake convention.

Universe and window are frozen in `research/experiments/R2A-oos/PREDECLARATION.md`
(written before this script was first executed). Do not edit the symbol list here;
edit nothing here. If the universe must change, that is a new pre-declaration.

    uv run python scripts/backfill_trades_oos.py --dry-run
    uv run python scripts/backfill_trades_oos.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import backfill_trades_semis as B  # noqa: E402

# Frozen by PREDECLARATION.md section 1. 16 names, none in the discovery panel.
OOS_SYMBOLS = [
    "VRTX", "BKNG", "ISRG", "AMGN", "HON", "INTU", "TMUS", "GILD",
    "MDLZ", "COST", "PEP", "ADBE", "CMCSA", "SBUX", "CSCO", "QCOM",
]
LOG_PATH = REPO / "logs" / "backfill_trades_oos.log"


def _logger() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("backfill_oos")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    h = logging.FileHandler(LOG_PATH, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(h)
    return log


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Backfill SIP trades for the 16 OOS names.")
    ap.add_argument("--dry-run", action="store_true",
                    help="List missing (sym,date) pairs + estimated requests; no fetch.")
    args = ap.parse_args(argv)

    overlap = set(OOS_SYMBOLS) & set(B.SYMBOLS) & {
        "NVDA", "TSLA", "AMD", "MU", "GOOGL", "KLAC", "MRVL", "LRCX", "TXN", "AMAT"}
    if overlap:
        print(f"REFUSING: test universe overlaps the discovery panel: {sorted(overlap)}")
        return 2

    B.SYMBOLS = OOS_SYMBOLS          # the only behavioural override
    log = _logger()
    settings = B.get_settings()

    if args.dry_run:
        B.run_dry(settings, log)
        return 0

    try:
        hist = B.AlpacaHist(settings)
    except Exception as exc:  # noqa: BLE001
        print("CREDENTIAL/CLIENT ERROR -- stopping (no auth improvisation):")
        print(f"  {type(exc).__name__}: {exc}")
        return 2
    hist.limiter = B.RateLimiter(B.REQ_PER_MIN)
    try:
        return B.run_full(settings, hist, log)
    finally:
        hist.close()


if __name__ == "__main__":
    sys.exit(main())
