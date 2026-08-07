"""Reconciler for the live signals journal vs the forward ledger (design L1).

Implements ``research/LIVE_SIGNAL_ENGINE_L0L1_DESIGN.md`` section 1 (``reconcile.py``).
This is the ADIA "live testing" T+1 divergence check: yesterday's live emissions are
joined against ``forward_paper``'s replay of the same session, and any per-field drift
beyond the source's tolerance is FLAGGED as a data/keying alarm. Display-only -- it
gates nothing (sequential monitors never gate trading in this program).

The ledger is READ ONLY (``forward_paper.load_ledger`` in the CLI, or a frame passed
in here). This module imports NO ledger-write API -- it never touches the forward
clock's ledger-append function or any lake path (design R5; test 8).

Tolerances (design section 1): a ``replay`` row was produced by the forward clock's
OWN functions, so it must match to ``tol_replay`` = 1e-9 (byte-agreement). A ``manual``
row was human-keyed, so it gets a keying tolerance: ``tol_manual`` = 1.0 bps on basis
and 0.01 on p_win. The net-relevant field (journal ``expected_net_bps`` vs ledger
``net_bps``) is reconciled for replay only -- a manual row has no realized outcome at
the decision instant, so its ``expected_net_bps`` is null and is skipped.
"""

from __future__ import annotations

import polars as pl

FLAGS_SCHEMA: dict[str, pl.DataType] = {
    "session": pl.Utf8,
    "symbol": pl.Utf8,
    "source": pl.Utf8,
    "window": pl.Utf8,
    "source_side": pl.Utf8,   # "matched" | "journal_only" | "ledger_only"
    "field": pl.Utf8,
    "journal_val": pl.Float64,
    "ledger_val": pl.Float64,
    "diff": pl.Float64,
    "tol": pl.Float64,
    "flagged": pl.Boolean,
}

# journal column -> ledger column, reconciled per (session, symbol) match.
_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("basis_bps", "led_basis_bps", "basis_bps"),
    ("p_win", "led_p_win", "p_win"),
    ("expected_net_bps", "led_net_bps", "net_bps"),
)


def _tol_for(
    source: str, field: str, *, tol_replay: float, tol_manual: float, tol_manual_pwin: float
) -> float | None:
    """The comparison tolerance for a (source, field), or None when not reconciled."""
    if source == "replay":
        return tol_replay
    # manual: human-keyed keying tolerances; net-relevant field is not reconciled.
    if field == "p_win":
        return tol_manual_pwin
    if field == "basis_bps":
        return tol_manual
    return None


def reconcile(
    journal: pl.DataFrame,
    ledger: pl.DataFrame,
    *,
    tol_replay: float = 1e-9,
    tol_manual: float = 1.0,
    tol_manual_pwin: float = 0.01,
) -> pl.DataFrame:
    """Per-field diff flags for the journal reconciled to the ledger on (session, symbol).

    Matched rows (inner join) yield one flag row per reconciled field where both values
    are present (``source_side="matched"``); ``flagged`` iff ``|journal - ledger| > tol``
    for the row's source (replay 1e-9; manual keying tolerances). ONE-SIDED rows are
    surfaced, never dropped (M2): a journal row with no ledger match is a
    ``journal_only`` flag, a ledger row with no journal match a ``ledger_only`` flag --
    both ``flagged=True``. Returns a FLAGS_SCHEMA frame (empty only when BOTH inputs are
    empty).
    """
    if journal.height == 0 and ledger.height == 0:
        return pl.DataFrame(schema=FLAGS_SCHEMA)

    rows: list[dict] = []

    # --- matched: per-field diffs on the inner join ---
    if journal.height and ledger.height:
        led = ledger.select(
            pl.col("session"),
            pl.col("symbol"),
            pl.col("basis_bps").alias("led_basis_bps"),
            pl.col("p_win").alias("led_p_win"),
            pl.col("net_bps").alias("led_net_bps"),
        )
        joined = journal.join(led, on=["session", "symbol"], how="inner")
        for r in joined.iter_rows(named=True):
            source = r["source"]
            for jcol, lcol, field in _FIELDS:
                tol = _tol_for(
                    source,
                    field,
                    tol_replay=tol_replay,
                    tol_manual=tol_manual,
                    tol_manual_pwin=tol_manual_pwin,
                )
                if tol is None:
                    continue
                jv = r.get(jcol)
                lv = r.get(lcol)
                if jv is None or lv is None:
                    continue
                diff = float(jv) - float(lv)
                rows.append(
                    {
                        "session": r["session"], "symbol": r["symbol"], "source": source,
                        "window": r.get("window"), "source_side": "matched", "field": field,
                        "journal_val": float(jv), "ledger_val": float(lv), "diff": diff,
                        "tol": float(tol), "flagged": bool(abs(diff) > tol),
                    }
                )

    # --- journal_only: journal rows with no ledger match (anti-join) ---
    if journal.height:
        keyed = journal if ledger.height == 0 else journal.join(
            ledger.select("session", "symbol"), on=["session", "symbol"], how="anti"
        )
        for r in keyed.iter_rows(named=True):
            rows.append(
                {
                    "session": r["session"], "symbol": r["symbol"], "source": r.get("source"),
                    "window": r.get("window"), "source_side": "journal_only",
                    "field": "unmatched", "journal_val": None, "ledger_val": None,
                    "diff": None, "tol": None, "flagged": True,
                }
            )

    # --- ledger_only: ledger rows with no journal match (anti-join) ---
    if ledger.height:
        keyed = ledger if journal.height == 0 else ledger.join(
            journal.select("session", "symbol"), on=["session", "symbol"], how="anti"
        )
        for r in keyed.iter_rows(named=True):
            rows.append(
                {
                    "session": r["session"], "symbol": r["symbol"], "source": None,
                    "window": None, "source_side": "ledger_only", "field": "unmatched",
                    "journal_val": None, "ledger_val": None, "diff": None, "tol": None,
                    "flagged": True,
                }
            )

    if not rows:
        return pl.DataFrame(schema=FLAGS_SCHEMA)
    return pl.DataFrame(rows, schema=FLAGS_SCHEMA)


def reconcile_report(flags: pl.DataFrame) -> str:
    """ASCII summary: matched-diff counts + BOTH one-sided counts + flagged rows.

    "ALL CLEAN" prints ONLY when every matched diff is within tolerance AND both
    one-sided counts (journal_only, ledger_only) are zero (M2).
    """
    lines: list[str] = ["LIVE RECONCILE :: journal vs forward ledger (T+1 divergence)"]
    if flags.height == 0:
        lines.append("  no rows to reconcile (both journal and ledger empty).")
        return "\n".join(lines)

    matched = flags.filter(pl.col("source_side") == "matched")
    j_only = flags.filter(pl.col("source_side") == "journal_only")
    l_only = flags.filter(pl.col("source_side") == "ledger_only")
    n_matched = matched.height
    n_matched_flagged = int(matched.filter(pl.col("flagged")).height)
    n_j_only = j_only.height
    n_l_only = l_only.height

    lines.append(
        f"  matched fields: {n_matched}   FLAGGED: {n_matched_flagged}   "
        f"clean: {n_matched - n_matched_flagged}"
    )
    lines.append(
        f"  one-sided: journal_only={n_j_only}   ledger_only={n_l_only}"
    )
    if n_matched:
        by_src = (
            matched.group_by("source")
            .agg(pl.len().alias("compared"), pl.col("flagged").sum().alias("flagged"))
            .sort("source")
        )
        for r in by_src.iter_rows(named=True):
            lines.append(
                f"    source={r['source']:<8} compared={r['compared']:<5} "
                f"flagged={r['flagged']}"
            )

    flagged = flags.filter(pl.col("flagged"))
    all_clean = n_matched_flagged == 0 and n_j_only == 0 and n_l_only == 0
    if not all_clean:
        lines.append("")
        lines.append("  FLAGGED ROWS (matched-out-of-tolerance and/or one-sided):")
        with pl.Config(
            tbl_formatting="ASCII_MARKDOWN",
            tbl_hide_dataframe_shape=True,
            tbl_hide_column_data_types=True,
            tbl_rows=200,
            tbl_cols=-1,
            tbl_width_chars=200,
        ):
            lines.append(str(flagged))
    else:
        lines.append("  ALL CLEAN (replay within 1e-9; manual within keying tolerance; "
                     "no one-sided rows).")
    return "\n".join(lines)
