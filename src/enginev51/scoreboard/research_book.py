"""Research book — THE gate currency (PROTOCOL v6 §3).

$notional_research_usd fixed notional per plan on the underlying stock,
long/short, fractional shares allowed (a scoring convention, not a deploy
claim). Converts replayer PlanResults into the canonical plan-results frame
consumed by backtest/stress.py and every report. Deploy-lens numbers live in
scoreboard/deploy_book.py and may NEVER appear in a promotion rule.
"""

from __future__ import annotations

import polars as pl

from enginev51.backtest.replay import PlanResult
from enginev51.backtest.stress import clustered_mean_ci

RESULTS_SCHEMA: dict[str, pl.DataType] = {
    "session": pl.Utf8,
    "symbol": pl.Utf8,
    "payer": pl.Utf8,
    "plan_id": pl.Utf8,
    "status": pl.Utf8,
    "taken": pl.Boolean,
    "side": pl.Int64,
    "entry_type": pl.Utf8,
    "exit_reason": pl.Utf8,
    "entry_ts": pl.Int64,
    "exit_ts": pl.Int64,
    "hold_min": pl.Float64,
    "net_bps": pl.Float64,
    "gross_mid_bps": pl.Float64,
    "latency_drag_bps": pl.Float64,
    "spread_cost_bps": pl.Float64,
    "fees_bps": pl.Float64,
    "identity_residual_bps": pl.Float64,
    "pnl_usd": pl.Float64,
    "expected_net_bps": pl.Float64,
    "p_win": pl.Float64,
    "confidence": pl.Float64,
}


def results_frame(
    results: list[PlanResult], session_iso: str, notional_usd: float = 10_000.0
) -> pl.DataFrame:
    """One row per plan (taken or not) — foregone breadth is data, not garbage."""
    rows: list[dict] = []
    for r in results:
        p = r.plan
        taken = r.status == "taken"
        entry_ts = r.entry_fills[0].ts if r.entry_fills else None
        exit_ts = max((f.ts for f in r.exit_fills), default=None)
        rows.append(
            {
                "session": session_iso,
                "symbol": p.symbol,
                "payer": p.payer,
                "plan_id": p.plan_id,
                "status": r.status,
                "taken": taken,
                "side": p.side,
                "entry_type": p.entry.type,
                "exit_reason": r.exit_reason,
                "entry_ts": entry_ts,
                "exit_ts": exit_ts,
                "hold_min": (
                    (exit_ts - entry_ts) / 60e9 if entry_ts is not None and exit_ts else None
                ),
                "net_bps": r.pnl.net_bps if r.pnl else None,
                "gross_mid_bps": r.pnl.gross_mid_bps if r.pnl else None,
                "latency_drag_bps": r.pnl.latency_drag_bps if r.pnl else None,
                "spread_cost_bps": r.pnl.spread_cost_bps if r.pnl else None,
                "fees_bps": r.pnl.fees_bps if r.pnl else None,
                "identity_residual_bps": r.pnl.identity_residual_bps if r.pnl else None,
                "pnl_usd": (r.pnl.net_bps * 1e-4 * notional_usd) if r.pnl else None,
                "expected_net_bps": p.expected_net_bps,
                "p_win": p.p_win,
                "confidence": p.confidence,
            }
        )
    return pl.DataFrame(rows, schema=RESULTS_SCHEMA, orient="row") if rows else pl.DataFrame(
        schema=RESULTS_SCHEMA
    )


def book_summary(df: pl.DataFrame) -> dict:
    """Headline economics of a plan-results frame (taken stream only)."""
    taken = df.filter(pl.col("taken"))
    out: dict = {
        "n_plans_authored": df.height,
        "n_taken": taken.height,
        "n_not_taken": df.filter(pl.col("status") == "not_taken").height,
        "n_unfilled": df.filter(pl.col("status") == "unfilled").height,
        "n_void": df.filter(pl.col("status") == "void").height,
        "n_sessions": df["session"].n_unique(),
    }
    if taken.height:
        mean, lo, hi = clustered_mean_ci(
            taken["net_bps"].to_numpy(), taken["session"].to_numpy()
        )
        out.update(
            {
                "net_bps_mean": round(mean, 3),
                "net_bps_ci95": [round(lo, 3), round(hi, 3)],
                "pnl_usd_sum": round(float(taken["pnl_usd"].sum()), 2),
                "win_rate": round(float((taken["net_bps"] > 0).mean()), 4),
                "mean_hold_min": round(float(taken["hold_min"].mean()), 1),
                "worst_identity_residual": float(
                    taken["identity_residual_bps"].abs().max()
                ),
            }
        )
    return out
