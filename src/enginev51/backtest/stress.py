"""Stress battery + statistical-power calculator for the causal backtest layer.

Two jobs, both pure (no I/O, no simulation):

1. **Power planning** (`power_table`, `min_n_for_power`, `power_of_test`) — given a
   true per-plan edge (bps) and the per-plan net dispersion (bps), what is the
   probability a one-sided t-test rejects H0: mean <= 0? This is the chance we can
   *prove* an edge that is genuinely there, and it justifies PROTOCOL v6 §4's
   N >= 250 plans / >= 150 sessions floor ("no verdicts below N=150"). Exact
   non-central-t (scipy.stats), no Monte-Carlo.

2. **Robustness stress arms** on a plan-results frame — the engineV5 tail-killers,
   ported. Each arm transforms the taken-plan stream, then a **day-clustered**
   bootstrap CI (`clustered_mean_ci`) is recomputed on `net_bps`. PROTOCOL v6 §4
   requires the edge to survive: top-5 sessions removed, 2x spread, 2x latency,
   with the day (session) as the clustering unit throughout.

Plan-results frame schema (polars), one row per plan decision:
    session          Utf8    ISO date of the trading session (clustering unit)
    symbol           Utf8    underlying ticker
    payer            Utf8    registered named payer ("gap_mr", "letf_window", ...)
    net_bps          Float64 modeled net edge for the plan, after all friction
    gross_mid_bps    Float64 mid-to-mid gross edge over the hold
    latency_drag_bps Float64 bps lost to manual-execution latency (SIGNED:
                             negative = the mid drifted the helpful way)
    spread_cost_bps  Float64 bps paid crossing the spread on the round trip
                             (SIGNED: negative = maker fill earned vs mid —
                             see decompose.plan_pnl)
    fees_bps         Float64 SEC/TAF sell-side fees (bps)
    exit_reason      Utf8    "targets" | "stop" | "hold" | "curfew" | ...
    taken            Boolean whether the k-slot replayer actually took the plan

All CIs are computed over `taken == True` rows only (the gate currency, §4).
Cost/drag columns are SIGNED (decompose.plan_pnl emits maker earn / favorable
drift as negative values). A stress arm therefore subtracts only the POSITIVE
part of the relevant term — subtracting a signed maker-earn column would
IMPROVE the stressed net (code review 2026-07-17 F1: on M3-A0-v1.1 the old
frame arm turned +4.3 base into +9.3 "stressed"). Frame arithmetic cannot
model what a wider book does to maker earn at all; for maker-heavy books the
honest 2x-spread stress is a re-sim through `tape.widen_tape`.
"""

from __future__ import annotations

import math

import numpy as np
import polars as pl
from scipy import stats

# --------------------------------------------------------------------------- #
# 1. Statistical power (pure scipy — non-central t, no simulation)
# --------------------------------------------------------------------------- #


def power_of_test(
    mean_bps: float, sigma_bps: float, n: int, alpha: float = 0.05
) -> float:
    """P(reject H0: mean <= 0) for a one-sided t-test, true edge = `mean_bps`.

    Exact non-central t: effect size d = mean_bps / sigma_bps, non-centrality
    ncp = d * sqrt(n), df = n - 1. Power = P(T' > t_crit) where T' is non-central
    t and t_crit = t.ppf(1 - alpha, df). Returns nan for n < 2 (no df) or
    sigma_bps <= 0.
    """
    if n < 2 or sigma_bps <= 0:
        return float("nan")
    df = n - 1
    ncp = (mean_bps / sigma_bps) * math.sqrt(n)
    t_crit = float(stats.t.ppf(1.0 - alpha, df))
    return float(stats.nct.sf(t_crit, df, ncp))


def power_table(
    sigma_bps: float = 130.0,
    means_bps: tuple = (5, 8, 10, 13, 15, 20),
    ns: tuple = (100, 150, 250, 400, 600, 1000),
    alpha: float = 0.05,
) -> pl.DataFrame:
    """Long-format power grid: one row per (true mean, N).

    Columns: mean_bps, n, sigma_bps, alpha, power. `power` is the probability a
    one-sided t-test at level `alpha` rejects zero when the true per-plan edge is
    `mean_bps` and the per-plan net dispersion is `sigma_bps` — the chance we can
    PROVE the edge if it is real. Monotone increasing in both mean and N.
    """
    rows: list[dict] = []
    for m in means_bps:
        for n in ns:
            rows.append(
                {
                    "mean_bps": float(m),
                    "n": int(n),
                    "sigma_bps": float(sigma_bps),
                    "alpha": float(alpha),
                    "power": power_of_test(float(m), sigma_bps, int(n), alpha),
                }
            )
    return pl.DataFrame(
        rows,
        schema={
            "mean_bps": pl.Float64,
            "n": pl.Int64,
            "sigma_bps": pl.Float64,
            "alpha": pl.Float64,
            "power": pl.Float64,
        },
    )


def min_n_for_power(
    mean_bps: float,
    sigma_bps: float,
    power: float = 0.8,
    alpha: float = 0.05,
    n_max: int = 1_000_000,
) -> int | None:
    """Smallest N whose one-sided t-test power reaches `power` for the given edge.

    Inverse of `power_of_test`: the returned n satisfies power_of_test(n) >= power
    and power_of_test(n-1) < power (n >= 2). Returns None if no N <= n_max reaches
    the target (e.g. mean_bps <= 0, where power asymptotes below any target > alpha).
    """
    if sigma_bps <= 0 or mean_bps <= 0:
        return None
    d = mean_bps / sigma_bps
    # Normal-approximation seed, then a guarded exact search around it.
    z_a = float(stats.norm.ppf(1.0 - alpha))
    z_b = float(stats.norm.ppf(power))
    n0 = int(((z_a + z_b) / d) ** 2)
    n = max(2, n0 - 20)
    while n <= n_max:
        if power_of_test(mean_bps, sigma_bps, n, alpha) >= power:
            while n > 2 and power_of_test(mean_bps, sigma_bps, n - 1, alpha) >= power:
                n -= 1
            return n
        n += 1
    return None


# --------------------------------------------------------------------------- #
# 2. Day-clustered bootstrap (generalizes evaluate.bootstrap_mean_ci to
#    unequal cluster sizes)
# --------------------------------------------------------------------------- #


def clustered_mean_ci(
    values: np.ndarray,
    clusters: np.ndarray,
    n_boot: int = 2000,
    seed: int = 7,
    ci: float = 0.95,
) -> tuple[float, float, float]:
    """(mean, lo, hi) via a cluster (session) bootstrap over unequal cluster sizes.

    Resample the SET OF CLUSTERS with replacement (n_clusters draws), pool ALL
    values belonging to the drawn clusters, take that pool's mean; repeat n_boot
    times and read the central-`ci` quantiles. This is the honest generalization
    of `evaluate.bootstrap_mean_ci` (which assumed one pre-aggregated value per
    session): it keeps within-session correlation intact, so autocorrelated days
    correctly widen the interval instead of being counted as independent draws.
    The point estimate is the pooled mean of all values. Deterministic in `seed`.
    NaN values (and their clusters) are dropped pairwise.
    """
    values = np.asarray(values, dtype=float)
    clusters = np.asarray(clusters)
    if values.shape[0] != clusters.shape[0]:
        raise ValueError("values and clusters must be the same length")
    mask = ~np.isnan(values)
    values = values[mask]
    clusters = clusters[mask]
    if values.shape[0] == 0:
        return float("nan"), float("nan"), float("nan")

    uniq = np.unique(clusters)
    idx_by_cluster = [np.flatnonzero(clusters == c) for c in uniq]
    n_clusters = len(uniq)

    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for b in range(n_boot):
        draw = rng.integers(0, n_clusters, n_clusters)
        pool = np.concatenate([idx_by_cluster[j] for j in draw])
        means[b] = values[pool].mean()

    alpha = (1.0 - ci) / 2.0
    return (
        float(values.mean()),
        float(np.quantile(means, alpha)),
        float(np.quantile(means, 1.0 - alpha)),
    )


# --------------------------------------------------------------------------- #
# 3. Stress transforms on a plan-results frame
# --------------------------------------------------------------------------- #

_NET = "net_bps"


def _taken(df: pl.DataFrame) -> pl.DataFrame:
    """The taken-plan stream — the only rows any CI is computed over (§4)."""
    return df.filter(pl.col("taken"))


def _clustered_ci(
    df: pl.DataFrame,
    *,
    col: str = _NET,
    n_boot: int = 2000,
    seed: int = 7,
    ci: float = 0.95,
) -> tuple[float, float, float, int, int]:
    """Day-clustered CI over `col` for the taken stream: (mean, lo, hi, n_plans, n_sessions)."""
    t = _taken(df)
    if t.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    mean, lo, hi = clustered_mean_ci(
        t[col].to_numpy(),
        t["session"].to_numpy(),
        n_boot=n_boot,
        seed=seed,
        ci=ci,
    )
    return mean, lo, hi, t.height, t["session"].n_unique()


def drop_top_sessions(df: pl.DataFrame, k: int = 5) -> pl.DataFrame:
    """Remove the `k` best sessions (by summed taken `net_bps`) — the tail killer.

    engineV5's tail-concentration gate: a strategy whose edge lives in a handful
    of lucky days is not deployable. Returns `df` with every row of the top-k
    sessions removed. If there are <= k sessions, everything is removed.
    """
    t = _taken(df)
    if t.height == 0:
        return df.clear()
    sess_sum = (
        t.group_by("session")
        .agg(pl.col(_NET).sum().alias("_s"))
        .sort("_s", descending=True)
    )
    top = sess_sum.head(k)["session"].to_list()
    return df.filter(~pl.col("session").is_in(top))


def double_spread(df: pl.DataFrame) -> pl.DataFrame:
    """Charge the paid spread twice: net_bps -= max(spread_cost_bps, 0).

    `spread_cost_bps` is SIGNED (negative = maker earn, decompose.plan_pnl), so
    only the paid (positive) part is doubled — subtracting the signed column
    would credit maker plans with a second helping of earn and IMPROVE the
    stressed net (code review 2026-07-17 F1). Maker earn is left untouched here
    because frame arithmetic cannot say what a 2x-wide book pays a maker; for
    maker-heavy books (mean spread_cost < 0) this arm is a NO-OP on most rows
    and the honest stress is a re-sim through `tape.widen_tape`.
    """
    return df.with_columns(
        (pl.col(_NET) - pl.col("spread_cost_bps").clip(lower_bound=0.0)).alias(_NET)
    )


def double_latency(df: pl.DataFrame) -> pl.DataFrame:
    """Double the manual-latency drag: net_bps -= max(latency_drag_bps, 0).

    `latency_drag_bps` is SIGNED (negative = the mid drifted the helpful way
    while the human acted), so only adverse drag is doubled — doubling a
    favorable drift would improve the stressed net (code review 2026-07-17 F1).

    Approximation: this doubles the *realized* adverse drag already booked per
    plan. The EXACT version re-runs the causal replayer with 2x-widened latency
    draws (uniform [10, 50] s at every leg) — `backtest/replay.py` offers that
    full re-simulation. This arm is the cheap frame-level check used for the §4
    gate; a survived-here result should still be confirmed by a replay run.
    """
    return df.with_columns(
        (pl.col(_NET) - pl.col("latency_drag_bps").clip(lower_bound=0.0)).alias(_NET)
    )


def post_promo(df: pl.DataFrame, extra_bps: float = 14.0) -> pl.DataFrame:
    """Post-promo / Korean fee-ladder annotation: net_bps -= extra_bps (RT commission).

    Report annotation only (PROTOCOL v6 §3; `data/costs.py`
    POST_PROMO_RT_COMMISSION_BPS = 14.0). An edge that dies here is labeled
    PROMO-ONLY in the report — disclosure, NOT a Stage A gate condition.
    """
    return df.with_columns((pl.col(_NET) - float(extra_bps)).alias(_NET))


def concentration_report(df: pl.DataFrame) -> dict:
    """Where the net edge concentrates: top-5-session / top-symbol / top-payer share
    of total net, plus the effective number of independent sessions.

    effective_n = (sum w)^2 / sum(w^2) over per-session summed net (Kish-style
    effective sample size): near n_sessions when net is spread evenly, near 1 when
    one day carries the book. Shares are of total taken net; when total net is 0
    they are returned as nan.
    """
    t = _taken(df)
    n_sessions = t["session"].n_unique() if t.height else 0
    if t.height == 0:
        return {
            "n_plans": 0,
            "n_sessions": 0,
            "total_net_bps": 0.0,
            "top5_session_share": float("nan"),
            "top_symbol_share": float("nan"),
            "top_payer_share": float("nan"),
            "effective_n": float("nan"),
        }

    total = float(t[_NET].sum())

    def _top_share(by: str, k: int) -> float:
        g = (
            t.group_by(by)
            .agg(pl.col(_NET).sum().alias("_s"))
            .sort("_s", descending=True)
        )
        if total == 0.0:
            return float("nan")
        return float(g.head(k)["_s"].sum()) / total

    sess_sums = (
        t.group_by("session").agg(pl.col(_NET).sum().alias("_s"))["_s"].to_numpy()
    )
    sq = float(np.sum(sess_sums**2))
    effective_n = (float(np.sum(sess_sums)) ** 2 / sq) if sq > 0 else float("nan")

    return {
        "n_plans": t.height,
        "n_sessions": n_sessions,
        "total_net_bps": total,
        "top5_session_share": _top_share("session", 5),
        "top_symbol_share": _top_share("symbol", 1),
        "top_payer_share": _top_share("payer", 1),
        "effective_n": effective_n,
    }


def stress_report(
    df: pl.DataFrame,
    *,
    n_boot: int = 2000,
    seed: int = 7,
    ci: float = 0.95,
    drop_k: int = 5,
    post_promo_bps: float = 14.0,
) -> dict:
    """Full stress battery with day-clustered CIs, keyed by arm name plus 'base'.

    Each CI arm maps to a 5-tuple (mean, lo, hi, n_plans, n_sessions) over the
    taken stream: 'base' (untouched), 'drop_top5' (top-`drop_k` sessions removed),
    'double_spread', 'double_latency', 'post_promo'. A 'concentration' key carries
    `concentration_report(df)` (a dict, not an arm). The §4 gate reads lo > 0 on
    base, drop_top5, double_spread, double_latency (post_promo is disclosure only).

    MAKER-BOOK CAVEAT (code review 2026-07-17 F1): the cost arms stress only the
    POSITIVE part of each signed cost column, so on a maker-heavy book (mean
    taken spread_cost_bps < 0) 'double_spread' barely moves and MUST NOT be read
    as spread robustness — gate such books on a `tape.widen_tape` re-sim instead.
    """
    kw = {"n_boot": n_boot, "seed": seed, "ci": ci}
    arms = {
        "base": df,
        "drop_top5": drop_top_sessions(df, k=drop_k),
        "double_spread": double_spread(df),
        "double_latency": double_latency(df),
        "post_promo": post_promo(df, extra_bps=post_promo_bps),
    }
    out: dict = {name: _clustered_ci(frame, **kw) for name, frame in arms.items()}
    out["concentration"] = concentration_report(df)
    return out
