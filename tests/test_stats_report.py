"""Tests for ``enginev51.stats.report`` — the shared report-shaped clustered CI.

FUTURE-FACING by ruling (2026-08-01 J3b): the fourteen local ``_ci`` clones inside
CLOSED registered screens are frozen artifacts and are NOT migrated. What is pinned
here is that the shared helper reproduces their consensus shape EXACTLY, so the next
family can adopt it without inventing a new convention.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from enginev51.backtest import stress
from enginev51.stats.report import CI_N_BOOT, CI_SEED, ReportCI, report_ci


def _frame(rows: list[tuple[str, float]]) -> pl.DataFrame:
    return pl.DataFrame(
        {"session": [r[0] for r in rows], "net_bps": [r[1] for r in rows]},
        schema={"session": pl.Utf8, "net_bps": pl.Float64},
    )


def test_nonempty_matches_the_local_clone_shape_exactly():
    """Same numbers the fourteen private ``_ci`` wrappers produce, same 5-field order.

    The clone body is reproduced inline as the oracle: if the shared helper ever
    diverges (different seed, different bootstrap count, n vs n_sessions swapped),
    this fails."""
    df = _frame([
        ("2024-01-02", 10.0), ("2024-01-02", -4.0),
        ("2024-01-03", 6.0),
        ("2024-01-04", 2.0), ("2024-01-04", 8.0), ("2024-01-04", -1.0),
    ])
    m, lo, hi = stress.clustered_mean_ci(
        df["net_bps"].to_numpy(), df["session"].to_numpy()
    )
    oracle = (m, lo, hi, df.height, df["session"].n_unique())

    got = report_ci(df)
    assert tuple(got) == oracle          # unpacks exactly like the clones
    assert got.mean == m and got.lo == lo and got.hi == hi
    assert got.n == 6 and got.n_sessions == 3
    assert got.lo <= got.mean <= got.hi


def test_empty_frame_is_a_result_not_an_error():
    """An empty cell reports (nan, nan, nan, 0, 0) — the convention every clone
    chose — instead of raising or faking a zero-width interval."""
    empty = _frame([])
    got = report_ci(empty)
    assert isinstance(got, ReportCI)
    assert np.isnan(got.mean) and np.isnan(got.lo) and np.isnan(got.hi)
    assert got.n == 0 and got.n_sessions == 0
    assert got.fmt() == "n=0"

    # Empty is decided BEFORE the columns are touched: a frame with no columns at
    # all (a filtered-to-nothing intermediate) still reports, never raises.
    assert report_ci(pl.DataFrame()).n == 0


def test_single_cluster_is_a_degenerate_point_interval():
    """One session = one cluster: every bootstrap draw resamples the same cluster,
    so lo == hi == mean. Reported honestly rather than hidden."""
    df = _frame([("2024-01-02", 5.0), ("2024-01-02", 15.0)])
    got = report_ci(df)
    assert got.n == 2 and got.n_sessions == 1
    assert got.mean == 10.0
    assert got.lo == got.mean == got.hi


def test_deterministic_and_seeded():
    df = _frame([(f"2024-01-{d:02d}", float(d % 7) - 3.0) for d in range(1, 29)])
    assert tuple(report_ci(df)) == tuple(report_ci(df))
    # A different seed moves the interval but not the point estimate.
    other = report_ci(df, seed=CI_SEED + 1)
    assert other.mean == report_ci(df).mean
    assert (other.lo, other.hi) != (report_ci(df).lo, report_ci(df).hi)
    assert (CI_SEED, CI_N_BOOT) == (7, 2000)  # the repo reproducibility constants


def test_custom_value_and_cluster_columns():
    df = pl.DataFrame({
        "entry_session": ["2024-01-02", "2024-01-02", "2024-01-03"],
        "delta_usd": [1.0, 3.0, 5.0],
    })
    got = report_ci(df, "delta_usd", "entry_session")
    assert got.n == 3 and got.n_sessions == 2
    assert got.mean == 3.0


def test_fmt_matches_the_house_one_liner():
    df = _frame([("2024-01-02", 2.0), ("2024-01-03", 4.0)])
    got = report_ci(df)
    s = got.fmt()
    assert s.startswith("mean=3.000  95%CI=[")
    assert s.endswith("n=2  sessions=2")
