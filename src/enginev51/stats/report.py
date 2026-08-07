"""The house report-shaped clustered CI — one wrapper for FUTURE families.

Fourteen closed screens each grew their own private ``_ci`` around the SAME
``backtest.stress.clustered_mean_ci`` call and the same 5-field report shape
(mean / lo / hi / n / n_sessions, with an all-NaN + zeros row for an empty
frame). The 2026-08-01 structural review (J3b) ruled: the clones in CLOSED,
REGISTERED screens are frozen artifacts and STAY — re-pointing a published
number's code path buys no science and risks the numbers. This module exists so
the NEXT family writes zero lines of CI plumbing.

The extracted consensus shape (verified against every clone before writing this):

    def _ci(df) -> tuple[float, float, float, int, int]:
        if df.height == 0:
            return nan, nan, nan, 0, 0
        m, lo, hi = stress.clustered_mean_ci(df[value].to_numpy(), df["session"].to_numpy())
        return m, lo, hi, df.height, df["session"].n_unique()

Clones surveyed: apps/run_basis_trial, run_m11, run_m9, run_meta_trial,
run_moc_gbm, run_moc_trial, run_open_trial, run_xs_reversal (array-shaped, 4-tuple);
models/m8v2_run; research_screens/earnings_close, gap_day (array-shaped),
open_fade; research_screens/sched_window.cluster_ci (a DIFFERENT estimator — CR0
closed form, not a bootstrap — deliberately NOT unified here); forward_paper's
``_ci`` is a formatter, not an estimator.

``ReportCI`` is a NamedTuple, so a future migration of any clone is a drop-in:
``m, lo, hi, n, ns = report_ci(df)`` unpacks exactly like the tuples above, while
``ci.mean`` / ``ci.n_sessions`` read better in new code.
"""

from __future__ import annotations

from typing import NamedTuple

import polars as pl

from enginev51.backtest import stress

# The repo reproducibility constants every screen re-declared (_CI_SEED / SEED and
# _CI_N_BOOT / N_BOOT); identical to `stress.clustered_mean_ci`'s own defaults.
CI_SEED = 7
CI_N_BOOT = 2000


class ReportCI(NamedTuple):
    """(mean, lo, hi, n, n_sessions) — the house report row for a cell."""

    mean: float
    lo: float
    hi: float
    n: int
    n_sessions: int

    def fmt(self, ndigits: int = 3) -> str:
        """The house one-line rendering (the ``_fmt_ci`` half of the clone pair)."""
        if self.n == 0:
            return "n=0"
        return (
            f"mean={self.mean:.{ndigits}f}  "
            f"95%CI=[{self.lo:.{ndigits}f}, {self.hi:.{ndigits}f}]  "
            f"n={self.n}  sessions={self.n_sessions}"
        )


def report_ci(
    df: pl.DataFrame,
    value_col: str = "net_bps",
    cluster_col: str = "session",
    *,
    n_boot: int = CI_N_BOOT,
    seed: int = CI_SEED,
    ci: float = 0.95,
) -> ReportCI:
    """Day-clustered mean CI of ``value_col``, clustered on ``cluster_col``.

    Wraps ``stress.clustered_mean_ci`` (cluster bootstrap over unequal cluster
    sizes; within-session correlation preserved) and adds the two report counts.
    Deterministic in ``seed``.

    EMPTY FRAME is handled explicitly and is NOT an error: an empty cell is a
    legitimate research answer ("this gate fired zero times"), so it reports
    ``(nan, nan, nan, 0, 0)`` — the same convention all fourteen clones chose —
    rather than raising or returning a fake zero-width interval. A missing column
    on a NON-empty frame still raises: that is a wiring bug, not a result.
    """
    if df.height == 0:
        return ReportCI(float("nan"), float("nan"), float("nan"), 0, 0)
    mean, lo, hi = stress.clustered_mean_ci(
        df[value_col].to_numpy(),
        df[cluster_col].to_numpy(),
        n_boot=n_boot,
        seed=seed,
        ci=ci,
    )
    return ReportCI(mean, lo, hi, int(df.height), int(df[cluster_col].n_unique()))
