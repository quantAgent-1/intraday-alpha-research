"""Tests for the A0 trial runner (apps/run_trial.py) — no real data required.

Covers the two things TASK C pins down: (1) the holdout guard refuses any run
whose ``--end`` reaches the sealed boundary, and (2) the report writer produces
a results.parquet + a well-formed report.md from a small fabricated frame.
"""

from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from enginev51.apps import run_trial
from enginev51.protocol import HOLDOUT_START, SealViolation
from enginev51.scoreboard.research_book import RESULTS_SCHEMA

# --------------------------------------------------------------------------- guard


def test_refuses_end_on_holdout_start():
    # SealViolation, not AssertionError: the guard must survive `python -O` (B7/J2).
    with pytest.raises(SealViolation):
        run_trial.assert_before_holdout(HOLDOUT_START)


def test_refuses_end_past_holdout_start():
    with pytest.raises(SealViolation):
        run_trial.assert_before_holdout(date(2026, 8, 1))


def test_allows_end_before_holdout_start():
    # last legal session is the day before the seal — must not raise.
    run_trial.assert_before_holdout(date(2026, 5, 31))


# --------------------------------------------------------------------------- fixture


def _row(session, payer, status, net, side=1, **kw):
    taken = status == "taken"
    base = {
        "session": session,
        "symbol": "NVDA",
        "payer": payer,
        "plan_id": f"{payer}-{session}-{net}",
        "status": status,
        "taken": taken,
        "side": side,
        "entry_type": "limit",
        "exit_reason": ("targets" if taken else None),
        "entry_ts": 1 if taken else None,
        "exit_ts": 2 if taken else None,
        "hold_min": 30.0 if taken else None,
        "net_bps": net if taken else None,
        "gross_mid_bps": (net + 3.0) if taken else None,
        "latency_drag_bps": 1.0 if taken else None,
        "spread_cost_bps": 1.5 if taken else None,
        "fees_bps": 0.3 if taken else None,
        "identity_residual_bps": 0.0 if taken else None,
        "pnl_usd": (net * 1e-4 * 10_000.0) if taken else None,
        "expected_net_bps": 12.0,
        "p_win": 0.5,
        "confidence": 0.5,
    }
    base.update(kw)
    return base


def _fabricated_frame() -> pl.DataFrame:
    rows = [
        # train-period taken (<= 2026-02-28), two sessions, two payers
        _row("2026-02-02", "gap_mr", "taken", 14.0, exit_reason="targets"),
        _row("2026-02-02", "vwap_magnet", "taken", -6.0, exit_reason="stop"),
        _row("2026-02-10", "gap_mr", "taken", 9.0, exit_reason="hold"),
        _row("2026-02-10", "cascade", "taken", 22.0, exit_reason="targets"),
        # validate-period taken (2026-03-01..2026-05-31)
        _row("2026-03-16", "gap_mr", "taken", 3.0, exit_reason="curfew"),
        _row("2026-03-16", "letf_window", "taken", 11.0, exit_reason="curfew"),
        _row("2026-04-06", "vwap_magnet", "taken", 7.0, exit_reason="targets"),
        # non-taken statuses (foregone breadth is a row too)
        _row("2026-02-02", "gap_mr", "not_taken", 0.0),
        _row("2026-03-16", "cascade", "unfilled", 0.0),
        _row("2026-04-06", "expiry_pin", "void", 0.0),
    ]
    return pl.DataFrame(rows, schema=RESULTS_SCHEMA, orient="row")


# --------------------------------------------------------------------------- report


def test_report_writer_on_fabricated_frame(tmp_path):
    df = _fabricated_frame()
    params = run_trial.params_by_payer()
    costs = {"NVDA": {"rt_cost_bps": 2.3, "spread_bps": 1.5, "source": "fallback"}}

    results_path, report_path = run_trial.write_outputs(
        df, tmp_path, "unit-trial", params, costs
    )

    assert results_path.exists() and report_path.exists()

    # results.parquet round-trips with the canonical schema.
    back = pl.read_parquet(results_path)
    assert back.height == df.height
    assert set(back.columns) == set(RESULTS_SCHEMA)

    text = report_path.read_text(encoding="utf-8")
    # section headers present
    for header in (
        "Authored / taken",
        "Split-wise net_bps",
        "Exit-reason distribution",
        "Stress battery",
        "Decomposition means",
        "PARAMS provenance",
    ):
        assert header in text, header
    # every payer's provenance block is embedded
    for payer in run_trial.PAYERS:
        assert payer in text
    # split-wise CI table names both split periods
    assert "train" in text and "validate" in text


def test_counts_by_payer_totals():
    df = _fabricated_frame()
    counts = run_trial._counts_by_payer(df)
    total = counts.filter(pl.col("payer") == "TOTAL")
    assert total["authored"][0] == df.height
    assert total["taken"][0] == df.filter(pl.col("taken")).height


def test_split_ci_table_has_both_splits_pooled():
    df = _fabricated_frame()
    tbl = run_trial._split_ci_table(df)
    pooled = tbl.filter(pl.col("payer") == "POOLED")
    assert set(pooled["split"].to_list()) == {"train", "validate"}
    # pooled train n = 4 taken train rows, validate n = 3 taken validate rows
    train_n = pooled.filter(pl.col("split") == "train")["n_plans"][0]
    val_n = pooled.filter(pl.col("split") == "validate")["n_plans"][0]
    assert train_n == 4
    assert val_n == 3


def test_report_writer_on_empty_frame(tmp_path):
    df = pl.DataFrame(schema=RESULTS_SCHEMA)
    params = run_trial.params_by_payer()
    results_path, report_path = run_trial.write_outputs(
        df, tmp_path, "empty-trial", params, {}
    )
    assert results_path.exists() and report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    assert "Pooled plan-results rows: 0" in text
