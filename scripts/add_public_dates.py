"""Add a ``public_date`` column to ``data/external/letf_aum_anchors.csv``
(SIM_AUDIT 2026-07-21 defect F3).

The as-of join in M12 Cell A / M8-v2 anchored LETF AUM on ``asof_date`` = the
N-PORT reporting-PERIOD END. That value only became public on the FILING date
(~58-60 days later), which sits unused inside the ``note`` field as
``...;filed=YYYY-MM-DD``; AUM moves 3-10x inside that lag. This script lifts the
filing date into an explicit ``public_date`` column so the join can anchor on the
true public instant.

Rule (per row):
  * ``note`` contains ``filed=YYYY-MM-DD``  -> ``public_date`` = that filing date
    (the N-PORT rows).
  * otherwise (aggregator live-snapshot rows, article reported-AUM rows) ->
    ``public_date`` = ``asof_date`` (they were observed live on ``asof_date``).

Idempotent: re-running recomputes ``public_date`` from scratch (any existing
column is dropped, then re-appended LAST), preserving the original column order
and the file's verbatim field values + line endings. Safe to run repeatedly.
"""

from __future__ import annotations

import csv
import re
import statistics
from datetime import date
from pathlib import Path

CSV_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "external" / "letf_aum_anchors.csv"
)

_FILED_RE = re.compile(r"filed=(\d{4}-\d{2}-\d{2})")


def public_date_for(note: str | None, asof_date: str) -> tuple[str, bool]:
    """Return ``(public_date, filed_parsed)``. A ``filed=YYYY-MM-DD`` token in the
    note yields the filing date (N-PORT); otherwise the row is treated as observed
    live on ``asof_date`` (aggregator / article rows)."""
    m = _FILED_RE.search(note or "")
    if m:
        return m.group(1), True
    return asof_date, False


def add_public_dates(path: Path = CSV_PATH) -> dict:
    """Rewrite ``path`` in place with a trailing ``public_date`` column. Returns a
    summary dict (row counts + N-PORT publication-lag distribution in days)."""
    # Preserve the file's existing line-ending style verbatim.
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Drop any pre-existing public_date so a re-run is idempotent and the
        # column always lands LAST in canonical order.
        src_cols = [c for c in (reader.fieldnames or []) if c != "public_date"]
        rows = list(reader)

    lags: list[int] = []
    n_filed = 0
    for r in rows:
        pub, filed = public_date_for(r.get("note", ""), r["asof_date"])
        r["public_date"] = pub
        if filed:
            n_filed += 1
            lags.append((date.fromisoformat(pub) - date.fromisoformat(r["asof_date"])).days)

    out_cols = [*src_cols, "public_date"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols, lineterminator=newline, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    return {
        "n_rows": len(rows),
        "n_filed_parsed": n_filed,
        "n_asof_fallback": len(rows) - n_filed,
        "lag_median_days": statistics.median(lags) if lags else None,
        "lag_min_days": min(lags) if lags else None,
        "lag_max_days": max(lags) if lags else None,
    }


def main() -> None:
    s = add_public_dates()
    print(f"[add_public_dates] {CSV_PATH}")
    print(f"  rows              : {s['n_rows']}")
    print(f"  filed= parsed     : {s['n_filed_parsed']}  (N-PORT -> public_date = filing date)")
    print(f"  asof_date fallback: {s['n_asof_fallback']}  (live snapshot / article rows)")
    print(
        "  N-PORT lag (days) : "
        f"median={s['lag_median_days']} min={s['lag_min_days']} max={s['lag_max_days']}"
    )


if __name__ == "__main__":
    main()
