"""M15 positioning layer v1 — SHADOW event-portfolio selection over the M10 stream.

Registered 2026-07-18 (ledger ``M15-positioning-v1``) BEFORE any forward session was
collected, so the portfolio stream's history is complete from forward session 1 and
its schema needed no migration. The registered M10 gate is UNTOUCHED: this layer
only adds columns to the forward ledger and a third REPORTED stream to ``status``.

v1 is deliberately selection + risk, not sizing-alpha (M9 Cell B: p_win-proportional
sizing added variance faster than return — equal notional only):

- SELECTION: among a session's ``taken_meta`` events, rank by ``p_win`` desc
  (ties: |basis_bps| desc, then symbol asc — fully deterministic), keep the top
  ``MAX_POSITIONS``. The cap models manual keying bandwidth in the
  15:55:10 -> 15:58 window (signal-only program: a human enters every order).
- SIZING (v1.2): equal notional = ``CAPITAL_USD`` ($10k — the project's
  research-gate currency, brief §1) / n_selected, whole-share floor at
  ``entry_px``; ``implementable`` = shares >= 1 at that capital. The research
  (bps) portfolio stream weights selected events EQUALLY and is size-agnostic.
  ``implementable_deploy`` is the single deploy-lens flag at
  ``DEPLOY_CAPITAL_USD`` ($1,000) — the capital-adequacy fact keeps accruing
  without contaminating the research stats.
- CATASTROPHIC-DEATH TRIPWIRE (reported, gates nothing — v1.1): one-sided lower
  CUSUM on the daily portfolio mean net_bps: S_t = max(0, S_{t-1} +
  (CUSUM_K_BPS - x_t)); alert when S_t > CUSUM_H_BPS. Calibrated on the M8
  walk-forward OOS history (M15-backtest-reference-v1, pre-forward-data):
  k=1.25 / h=150 gives ~5% benign alert time on the ALIVE 2022-2026 stream and
  median ~69-session (100%-rate) detection of a fully dead edge. An alert is a
  HUMAN-REVIEW trigger only. The same reference run showed trailing-performance
  states have NO next-day predictive content here (blocked-day mean +2.9 vs calm
  +3.4) — the third kill of trailing-regime gating in this program — so the
  tripwire must NEVER become a trading filter without a new registration and
  new evidence.

Promotion / kill criteria live in M3_REGISTRATION.md (M15, amended v1.1).
Adoption is a deploy-sizing decision AFTER the M10 gate resolves — never a
change to the frozen signal, the meta gate, or the M10 gate itself.
"""

from __future__ import annotations

import polars as pl

# Frozen parameters (registered v1; CUSUM_H amended to 150 in v1.1, capital basis
# amended to the $10k research-gate currency in v1.2 — both BEFORE forward
# session 1. Do not tune further while the shadow runs).
MAX_POSITIONS = 3
# Primary sizing basis: the project's research-gate currency (brief §1: "$10k
# notional per plan"). All sizing/implementability STATS run at this capital.
CAPITAL_USD = 10_000.0
# Deploy lens only: the actual account. Kept as a single reported flag
# (implementable_deploy) so the capital-adequacy fact keeps accruing.
DEPLOY_CAPITAL_USD = 1000.0
CUSUM_K_BPS = 1.25
CUSUM_H_BPS = 150.0

# Columns this layer adds to the forward ledger (single source of truth; the
# forward_paper LEDGER_SCHEMA merges these in).
PORTFOLIO_COLS: dict[str, pl.DataType] = {
    "selected": pl.Boolean,
    "sel_rank": pl.Int64,
    "size_shares": pl.Int64,
    "size_notional": pl.Float64,
    "implementable": pl.Boolean,
    "implementable_deploy": pl.Boolean,
}


def apply_positioning(
    scored: pl.DataFrame,
    *,
    max_positions: int = MAX_POSITIONS,
    capital_usd: float = CAPITAL_USD,
    deploy_capital_usd: float = DEPLOY_CAPITAL_USD,
) -> pl.DataFrame:
    """Add the portfolio columns to a scored event frame (any number of sessions).

    Selection and sizing are computed independently per session. Sizing/stat columns
    run at ``capital_usd`` (the $10k research-gate currency); ``implementable_deploy``
    is the single deploy-lens flag at ``deploy_capital_usd``. Non-selected rows get
    ``selected=False``, null rank, zero shares/notional, null implementability flags
    (implementability is only meaningful for selected events).
    """
    if scored.height == 0:
        return scored.with_columns(
            [pl.lit(None, dtype=dt).alias(c) for c, dt in PORTFOLIO_COLS.items()]
        )
    cand = (
        scored.filter(pl.col("taken_meta").fill_null(False))
        .with_columns(pl.col("basis_bps").abs().alias("_abs_basis"))
        .sort(
            ["session", "p_win", "_abs_basis", "symbol"],
            descending=[False, True, True, False],
        )
        .with_columns((pl.int_range(pl.len()).over("session") + 1).alias("sel_rank"))
        .filter(pl.col("sel_rank") <= max_positions)
    )
    if cand.height == 0:
        return scored.with_columns(
            pl.lit(False).alias("selected"),
            pl.lit(None, dtype=pl.Int64).alias("sel_rank"),
            pl.lit(0, dtype=pl.Int64).alias("size_shares"),
            pl.lit(0.0).alias("size_notional"),
            pl.lit(None, dtype=pl.Boolean).alias("implementable"),
            pl.lit(None, dtype=pl.Boolean).alias("implementable_deploy"),
        )
    n_sel = cand.group_by("session").agg(pl.len().alias("_n_sel"))
    cand = (
        cand.join(n_sel, on="session")
        .with_columns(
            (pl.lit(capital_usd) / pl.col("_n_sel") / pl.col("entry_px"))
            .floor()
            .cast(pl.Int64)
            .alias("size_shares")
        )
        .with_columns(
            (pl.col("size_shares") * pl.col("entry_px")).alias("size_notional"),
            (pl.col("size_shares") >= 1).alias("implementable"),
            (
                (pl.lit(deploy_capital_usd) / pl.col("_n_sel") / pl.col("entry_px"))
                .floor()
                >= 1
            ).alias("implementable_deploy"),
        )
    )
    sel = cand.select(
        "session", "symbol", "sel_rank", "size_shares", "size_notional",
        "implementable", "implementable_deploy",
    )
    out = scored.join(sel, on=["session", "symbol"], how="left")
    return out.with_columns(
        pl.col("sel_rank").is_not_null().alias("selected"),
        pl.col("size_shares").fill_null(0),
        pl.col("size_notional").fill_null(0.0),
    )


def portfolio_daily(ledger: pl.DataFrame) -> pl.DataFrame:
    """Per-session equal-weight portfolio mean net_bps over the selected events."""
    if ledger.height == 0 or "selected" not in ledger.columns:
        return pl.DataFrame(
            schema={"session": pl.Utf8, "n_sel": pl.UInt32, "port_net_bps": pl.Float64}
        )
    sel = ledger.filter(pl.col("selected").fill_null(False))
    if sel.height == 0:
        return pl.DataFrame(
            schema={"session": pl.Utf8, "n_sel": pl.UInt32, "port_net_bps": pl.Float64}
        )
    return (
        sel.group_by("session")
        .agg(pl.len().alias("n_sel"), pl.col("net_bps").mean().alias("port_net_bps"))
        .sort("session")
    )


def cusum_series(
    daily: pl.DataFrame, *, k: float = CUSUM_K_BPS, h: float = CUSUM_H_BPS
) -> pl.DataFrame:
    """One-sided lower CUSUM over the daily portfolio means (chronological order).

    S_t = max(0, S_{t-1} + (k - x_t)); ``cusum_alert`` = S_t > h. Reported only —
    in shadow mode an alert gates nothing; it is the pre-registered edge-death
    detector whose parameters cannot be tuned after the fact.
    """
    if daily.height == 0:
        return daily.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("cusum_S"),
            pl.lit(None, dtype=pl.Boolean).alias("cusum_alert"),
        )
    s = 0.0
    ss: list[float] = []
    alerts: list[bool] = []
    for x in daily["port_net_bps"].to_list():
        s = max(0.0, s + (k - float(x)))
        ss.append(s)
        alerts.append(s > h)
    return daily.with_columns(
        pl.Series("cusum_S", ss), pl.Series("cusum_alert", alerts)
    )


def portfolio_stats(ledger: pl.DataFrame) -> dict:
    """Running shadow-portfolio stats for ``status`` (day-clustered CI like M10)."""
    from enginev51.backtest import stress

    empty = {
        "n_events": 0,
        "n_sessions": 0,
        "mean_net_bps": None,
        "ci_lo": None,
        "ci_hi": None,
        "implementable_rate": None,
        "implementable_deploy_rate": None,
        "cusum_S": None,
        "cusum_alert": False,
        "n_alert_sessions": 0,
        "max_positions": MAX_POSITIONS,
        "capital_usd": CAPITAL_USD,
        "deploy_capital_usd": DEPLOY_CAPITAL_USD,
        "cusum_k": CUSUM_K_BPS,
        "cusum_h": CUSUM_H_BPS,
    }
    if ledger.height == 0 or "selected" not in ledger.columns:
        return empty
    sel = ledger.filter(pl.col("selected").fill_null(False))
    if sel.height == 0:
        return empty
    m, lo, hi = stress.clustered_mean_ci(
        sel["net_bps"].to_numpy(), sel["session"].to_numpy()
    )
    daily = cusum_series(portfolio_daily(ledger))
    impl = sel.filter(pl.col("implementable").fill_null(False)).height / sel.height
    if "implementable_deploy" in sel.columns:
        impl_dep = (
            sel.filter(pl.col("implementable_deploy").fill_null(False)).height
            / sel.height
        )
    else:  # pre-v1.2 frames
        impl_dep = None
    return {
        "n_events": sel.height,
        "n_sessions": int(sel["session"].n_unique()),
        "mean_net_bps": round(float(m), 3),
        "ci_lo": round(float(lo), 3),
        "ci_hi": round(float(hi), 3),
        "implementable_rate": round(impl, 3),
        "implementable_deploy_rate": round(impl_dep, 3) if impl_dep is not None else None,
        "cusum_S": round(float(daily["cusum_S"][-1]), 2),
        "cusum_alert": bool(daily["cusum_alert"][-1]),
        "n_alert_sessions": int(daily.filter(pl.col("cusum_alert")).height),
        "max_positions": MAX_POSITIONS,
        "capital_usd": CAPITAL_USD,
        "deploy_capital_usd": DEPLOY_CAPITAL_USD,
        "cusum_k": CUSUM_K_BPS,
        "cusum_h": CUSUM_H_BPS,
    }
