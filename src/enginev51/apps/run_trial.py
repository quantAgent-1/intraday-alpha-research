"""A0 trial runner — detector -> plan -> causal replay -> research book (PROTOCOL v6).

Drives the full M3 A0 pipeline over a date range of NYSE sessions, per symbol:

    load_session_context  ->  5 named-payer detectors  ->  plans.constructor
      ->  backtest.replay (causal, k-slot)  ->  scoreboard.research_book

and accumulates the canonical plan-results frame across sessions, then writes
``results.parquet`` + a ``report.md`` under ``research/experiments/<trial_id>/``.

Hard PIT/holdout guard (binding): the run REFUSES any ``--end`` on or after
``protocol.HOLDOUT_START`` and hard-filters every session to strictly before it,
so no code path here can touch the sealed holdout. This app writes NO ledger
row — the orchestrator owns verdicts; this is plumbing that produces evidence.

    uv run python -m enginev51.apps.run_trial --trial-id M3-A0-smoke \
        --symbols NVDA,TSLA --start 2026-05-01 --end 2026-05-15 --k-slots 2 --seed 7
"""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import click
import polars as pl
import structlog

from enginev51.backtest import stress
from enginev51.backtest.replay import ReplayConfig, replay_session
from enginev51.backtest.tape import load_session_tape, widen_tape
from enginev51.config import Settings, get_research_config, get_settings
from enginev51.data import calendar
from enginev51.data.costs import cost_table
from enginev51.events.context import load_session_context
from enginev51.events.detectors import cascade, expiry_pin, gap_mr, letf_window, vwap_magnet
from enginev51.events.entry_quality import features_at as _eq_features_at
from enginev51.events.entry_quality import gate as _eq_gate
from enginev51.plans import overlay_m4 as _m4
from enginev51.plans.constructor import build_plan
from enginev51.plans.overlay_a1 import PredProvider, apply_overlay
from enginev51.plans.overlay_m4 import M4Provider, apply_m4
from enginev51.protocol import (
    HOLDOUT_START,
    experiments_dir,
    refuse_end_on_or_after_holdout,
    split_of,
)
from enginev51.scoreboard.research_book import RESULTS_SCHEMA, results_frame

log = structlog.get_logger(__name__)

# The five registered named-payer detectors (module carries PARAMS + detect()).
DETECTORS = (gap_mr, letf_window, vwap_magnet, cascade, expiry_pin)
PAYERS: tuple[str, ...] = ("gap_mr", "letf_window", "vwap_magnet", "cascade", "expiry_pin")

_DECOMP_COLS = ("gross_mid_bps", "latency_drag_bps", "spread_cost_bps", "fees_bps")


def params_by_payer() -> dict[str, dict]:
    """Frozen PARAMS of every detector, keyed by payer id (report provenance)."""
    return {mod.__name__.rsplit(".", 1)[-1]: dict(mod.PARAMS) for mod in DETECTORS}


# --------------------------------------------------------------------------- guard


def assert_before_holdout(end: date) -> None:
    """Refuse to run past the sealed holdout boundary (PROTOCOL v6 §1).

    The trial evaluates only sessions strictly before HOLDOUT_START; an ``end``
    on or after it raises SealViolation and aborts the run before any data loads
    (a raise, never a bare assert — ``python -O`` strips those).
    """
    refuse_end_on_or_after_holdout(end)


# --------------------------------------------------------------------------- run


def run_trial(
    settings: Settings,
    *,
    symbols: list[str],
    start: date,
    end: date,
    k_slots: int,
    seed: int,
    lat_lo_s: float = 5.0,
    lat_hi_s: float = 25.0,
    spread_mult: float = 1.0,
    min_fill_size: float = 100.0,
    arm: str = "a0",
    preds_dir: str | None = None,
    m4_mode: str = "select",
    p_skip: float = 0.45,
    entry_gate: bool = False,
) -> tuple[pl.DataFrame, dict]:
    """Execute the A0 pipeline over [start, end] sessions; return (results_frame, run_stats).

    ``run_stats`` carries plumbing counters (sessions processed, per-reason skip
    counts, detector-state counts per payer) for the smoke headline. The returned
    frame is the pooled canonical plan-results frame (may be empty)."""
    assert_before_holdout(end)
    symbols = [s.strip().upper() for s in symbols]
    rc = get_research_config()

    # Deterministic fallback cost table computed ONCE (no network, PROTOCOL §3).
    costs = cost_table(settings, symbols, sample_nbbo=False)

    cfg = ReplayConfig(
        k_slots=k_slots,
        seed=seed,
        lat_lo_s=lat_lo_s,
        lat_hi_s=lat_hi_s,
        slip_bps=rc.slippage_market_bps,
        sec_taf_sell_bps=rc.sec_taf_sell_bps,
        min_fill_size=min_fill_size,
    )

    sessions = [d for d in calendar.trading_days(start, end) if d < HOLDOUT_START]

    # A1/M4 overlay wiring (additive; arm="a0" leaves every path below byte-identical).
    provider = None
    if arm == "a1":
        pdir = preds_dir or str(settings.data_dir / "preds" / "a1_v1")
        provider = PredProvider(pdir)
    elif arm == "m4":
        _m4.DROP_COUNTS.clear()
        pdir = preds_dir or str(settings.data_dir / "preds" / "m4_v1")
        provider = M4Provider(pdir)
        _m4.MODEL_TAG = provider.arch_tag
    overlay_counts = {"kept": 0, "vetoed": 0, "no_pred": 0}

    # Entry-quality gate (M3-H2-entry-quality-v1): additive, a0 path only. When
    # off, every path below is byte-identical to the ungated baseline.
    gate_counts = {"allowed": 0, "gated": 0, "no_features": 0}

    skip_counts = {"no_context": 0, "no_event_bars": 0, "no_quote": 0}
    state_counts = dict.fromkeys(PAYERS, 0)
    plan_seq = 0
    frames: list[pl.DataFrame] = []
    n_symbol_sessions = 0
    n_symbol_sessions_ok = 0

    for sd in sessions:
        session_iso = sd.isoformat()
        session_plans = []
        contexts: dict[str, object] = {}

        for sym in symbols:
            n_symbol_sessions += 1
            ctx = load_session_context(settings, sym, session_iso)
            if ctx is None:
                skip_counts["no_context"] += 1
                continue
            if ctx.event_bars is None:
                skip_counts["no_event_bars"] += 1
                continue
            n_symbol_sessions_ok += 1
            contexts[sym] = ctx

            states = []
            for mod in DETECTORS:
                states.extend(mod.detect(ctx))
            for st in states:
                if st.active:
                    state_counts[st.payer] = state_counts.get(st.payer, 0) + 1

            for st in states:
                quote = ctx.quote_at(st.ts)
                if quote is None:
                    skip_counts["no_quote"] += 1
                    continue
                bid, ask = quote
                plan = build_plan(
                    st,
                    bid=bid,
                    ask=ask,
                    rt_cost_bps=costs[st.symbol]["rt_cost_bps"],
                    curfew_ts=ctx.curfew_ts,
                    plan_seq=plan_seq,
                )
                plan_seq += 1
                if plan is None:
                    continue
                # Entry-quality authoring gate (a0 path only; additive). f is
                # None -> no evidence, no veto; else veto unless gate() allows.
                if entry_gate and arm == "a0":
                    f = _eq_features_at(ctx.event_bars, st.ts)
                    if f is None:
                        gate_counts["no_features"] += 1
                    elif _eq_gate(f, plan.side):
                        gate_counts["allowed"] += 1
                    else:
                        gate_counts["gated"] += 1
                        continue
                if provider is not None:  # arm == "a1"/"m4": apply the model overlay
                    entry_ref = (
                        plan.entry.limit_price
                        if plan.entry.limit_price is not None
                        else (ask if plan.side > 0 else bid)
                    )
                    pred = provider.row_at(plan.symbol, session_iso, st.ts)
                    a0_stop_distance_px = abs(plan.stop.price - entry_ref)
                    a0_target_distances_px = [abs(t.price - entry_ref) for t in plan.targets]
                    if arm == "m4":
                        plan = apply_m4(
                            plan,
                            pred,
                            m4_mode,
                            p_skip,
                            a0_stop_distance_px,
                            a0_target_distances_px,
                            entry_ref,
                            costs[st.symbol]["rt_cost_bps"],
                        )
                    else:
                        plan = apply_overlay(
                            plan,
                            plan.side,
                            pred,
                            plan.payer,
                            a0_stop_distance_px,
                            a0_target_distances_px,
                            entry_ref,
                            costs[st.symbol]["rt_cost_bps"],
                        )
                    if pred is None:
                        overlay_counts["no_pred"] += 1
                    elif plan is None:
                        overlay_counts["vetoed"] += 1
                    else:
                        overlay_counts["kept"] += 1
                    if plan is None:
                        continue
                session_plans.append(plan)

        if not session_plans:
            continue

        plan_syms = {p.symbol for p in session_plans}
        tapes = {}
        for sym in plan_syms:
            tp = load_session_tape(settings, sym, session_iso)
            if tp is not None:
                tapes[sym] = widen_tape(tp, spread_mult)

        results = replay_session(session_plans, tapes, cfg)
        frames.append(results_frame(results, session_iso, rc.notional_research_usd))

    if frames:
        df = pl.concat(frames, how="vertical")
    else:
        df = pl.DataFrame(schema=RESULTS_SCHEMA)

    is_overlay = arm in ("a1", "m4")
    _default_pdir = "a1_v1" if arm == "a1" else "m4_v1"
    run_stats = {
        "arm": arm,
        "preds_dir": (preds_dir or str(settings.data_dir / "preds" / _default_pdir)) if is_overlay else None,
        "overlay_counts": overlay_counts if is_overlay else None,
        "m4_mode": m4_mode if arm == "m4" else None,
        "p_skip": p_skip if arm == "m4" else None,
        "drop_counts": dict(_m4.DROP_COUNTS) if arm == "m4" else None,
        "entry_gate": entry_gate,
        "gate_counts": gate_counts if entry_gate else None,
        "sessions_in_range": len(sessions),
        "symbol_sessions_seen": n_symbol_sessions,
        "symbol_sessions_ok": n_symbol_sessions_ok,
        "skip_counts": skip_counts,
        "state_counts": state_counts,
        "plans_authored": df.height,
        "symbols": symbols,
        "cost_table": costs,
    }
    return df, run_stats


# --------------------------------------------------------------------------- report


def _counts_by_payer(df: pl.DataFrame) -> pl.DataFrame:
    """authored / taken / not_taken / unfilled / void, one row per payer + TOTAL."""
    rows: list[dict] = []
    payers = list(df["payer"].unique().sort()) if df.height else []
    for payer in [*payers, "__ALL__"]:
        sub = df if payer == "__ALL__" else df.filter(pl.col("payer") == payer)
        rows.append(
            {
                "payer": "TOTAL" if payer == "__ALL__" else payer,
                "authored": sub.height,
                "taken": sub.filter(pl.col("status") == "taken").height,
                "not_taken": sub.filter(pl.col("status") == "not_taken").height,
                "unfilled": sub.filter(pl.col("status") == "unfilled").height,
                "void": sub.filter(pl.col("status") == "void").height,
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            "payer": pl.Utf8,
            "authored": pl.Int64,
            "taken": pl.Int64,
            "not_taken": pl.Int64,
            "unfilled": pl.Int64,
            "void": pl.Int64,
        },
        orient="row",
    )


def _split_ci(taken: pl.DataFrame) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n_plans, n_sessions) day-clustered over a taken subset."""
    if taken.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    m, lo, hi = stress.clustered_mean_ci(
        taken["net_bps"].to_numpy(), taken["session"].to_numpy()
    )
    return m, lo, hi, taken.height, taken["session"].n_unique()


def _split_ci_table(df: pl.DataFrame) -> pl.DataFrame:
    """Split-wise (train-period vs validate-period) net CIs, per payer and pooled."""
    taken = df.filter(pl.col("taken"))
    if taken.height and "split" not in taken.columns:
        taken = taken.with_columns(
            pl.col("session")
            .map_elements(split_of, return_dtype=pl.Utf8)
            .alias("split")
        )
    payers = list(taken["payer"].unique().sort()) if taken.height else []
    rows: list[dict] = []
    for payer in [*payers, "__POOLED__"]:
        base = taken if payer == "__POOLED__" else taken.filter(pl.col("payer") == payer)
        for split in ("train", "validate"):
            sub = base.filter(pl.col("split") == split) if base.height else base
            m, lo, hi, n, ns = _split_ci(sub)
            rows.append(
                {
                    "payer": "POOLED" if payer == "__POOLED__" else payer,
                    "split": split,
                    "n_plans": n,
                    "n_sessions": ns,
                    "net_bps_mean": round(m, 3) if n else None,
                    "ci_lo": round(lo, 3) if n else None,
                    "ci_hi": round(hi, 3) if n else None,
                }
            )
    return pl.DataFrame(
        rows,
        schema={
            "payer": pl.Utf8,
            "split": pl.Utf8,
            "n_plans": pl.Int64,
            "n_sessions": pl.Int64,
            "net_bps_mean": pl.Float64,
            "ci_lo": pl.Float64,
            "ci_hi": pl.Float64,
        },
        orient="row",
    )


def _exit_reason_table(df: pl.DataFrame) -> pl.DataFrame:
    taken = df.filter(pl.col("taken"))
    if taken.height == 0:
        return pl.DataFrame(schema={"exit_reason": pl.Utf8, "count": pl.Int64})
    return (
        taken.group_by("exit_reason")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
    )


def _decomp_means(df: pl.DataFrame) -> dict[str, float | None]:
    taken = df.filter(pl.col("taken"))
    out: dict[str, float | None] = {}
    for c in _DECOMP_COLS:
        out[c] = round(float(taken[c].mean()), 3) if taken.height else None
    out["net_bps"] = round(float(taken["net_bps"].mean()), 3) if taken.height else None
    return out


def _fmt_ci5(t: tuple[float, float, float, int, int]) -> str:
    m, lo, hi, n, ns = t
    if n == 0:
        return "n=0"
    return f"mean={m:.3f}  95%CI=[{lo:.3f}, {hi:.3f}]  n={n}  sessions={ns}"


def _ascii(df: pl.DataFrame) -> str:
    """Render a polars frame as an ASCII-markdown table (cp949-safe, no box glyphs)."""
    with pl.Config(
        tbl_formatting="ASCII_MARKDOWN",
        tbl_hide_dataframe_shape=True,
        tbl_hide_column_data_types=True,
        tbl_rows=200,
        tbl_cols=-1,
        tbl_width_chars=200,
    ):
        return str(df)


def build_report_md(
    df: pl.DataFrame,
    trial_id: str,
    params: dict[str, dict],
    costs: dict[str, dict],
    run_stats: dict | None = None,
) -> str:
    """Assemble the full ``report.md`` string from a pooled plan-results frame.

    Pure (no I/O): the test drives this on a small fabricated frame."""
    md: list[str] = [
        f"# A0 trial report — {trial_id}",
        "",
        f"Pooled plan-results rows: {df.height}  "
        f"(taken={df.filter(pl.col('taken')).height})",
        f"Sessions: {df['session'].n_unique() if df.height else 0}",
        f"Splits present: {sorted(set(split_of(s) for s in df['session'].unique())) if df.height else []}",
        "",
        "## 1. Authored / taken / not_taken / unfilled / void — per payer",
        "",
        _ascii(_counts_by_payer(df)),
        "",
        "## 2. Split-wise net_bps day-clustered CIs (per payer + pooled)",
        "",
        "train-period = sessions <= 2026-02-28; validate-period = 2026-03-01..2026-05-31.",
        "",
        _ascii(_split_ci_table(df)),
        "",
        "## 3. Exit-reason distribution (taken)",
        "",
        _ascii(_exit_reason_table(df)),
        "",
        "## 4. Stress battery on the pooled taken frame (stress.stress_report)",
        "",
    ]

    sr = stress.stress_report(df)
    stress_rows = []
    for arm in ("base", "drop_top5", "double_spread", "double_latency", "post_promo"):
        m, lo, hi, n, ns = sr[arm]
        stress_rows.append(
            {
                "arm": arm,
                "n_plans": n,
                "n_sessions": ns,
                "net_bps_mean": round(m, 3) if n else None,
                "ci_lo": round(lo, 3) if n else None,
                "ci_hi": round(hi, 3) if n else None,
            }
        )
    md.append(
        _ascii(
            pl.DataFrame(
                stress_rows,
                schema={
                    "arm": pl.Utf8,
                    "n_plans": pl.Int64,
                    "n_sessions": pl.Int64,
                    "net_bps_mean": pl.Float64,
                    "ci_lo": pl.Float64,
                    "ci_hi": pl.Float64,
                },
                orient="row",
            )
        )
    )
    md += [
        "",
        "Concentration:",
        "",
        "```",
        json.dumps(sr["concentration"], indent=2, default=str),
        "```",
        "",
        "## 5. Decomposition means (taken; bps on entry notional)",
        "",
        "```",
        json.dumps(_decomp_means(df), indent=2, default=str),
        "```",
        "",
        "## 6. Cost table (deterministic fallback, no network)",
        "",
        "```",
        json.dumps(costs, indent=2, default=str),
        "```",
        "",
        "## 7. Detector PARAMS provenance (frozen; mirrors M3_REGISTRATION.md)",
        "",
    ]
    for payer, p in params.items():
        md += [f"### {payer}", "", "```", json.dumps(p, indent=2, default=str), "```", ""]

    if run_stats is not None:
        md += [
            "## 8. Run plumbing counters",
            "",
            "```",
            json.dumps(
                {k: v for k, v in run_stats.items() if k != "cost_table"},
                indent=2,
                default=str,
            ),
            "```",
            "",
        ]
    return "\n".join(md)


def write_outputs(
    df: pl.DataFrame,
    out_dir: Path,
    trial_id: str,
    params: dict[str, dict],
    costs: dict[str, dict],
    run_stats: dict | None = None,
) -> tuple[Path, Path]:
    """Write results.parquet + report.md under ``out_dir``; return their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.parquet"
    report_path = out_dir / "report.md"
    df.write_parquet(results_path)
    report_path.write_text(
        build_report_md(df, trial_id, params, costs, run_stats), encoding="utf-8"
    )
    return results_path, report_path


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--trial-id", required=True, help="Experiment id -> research/experiments/<id>/.")
@click.option("--symbols", default="NVDA,TSLA,AMD,MU", help="Comma-separated tick universe.")
@click.option("--start", required=True, help="First session (ISO date), inclusive.")
@click.option("--end", required=True, help="Last session (ISO date), inclusive; < holdout.")
@click.option("--k-slots", default=2, type=int, help="Portfolio concurrency (registered 2).")
@click.option("--seed", default=7, type=int, help="Replayer latency seed.")
@click.option("--lat-lo", default=5.0, type=float, help="Latency draw lower bound, seconds.")
@click.option("--lat-hi", default=25.0, type=float, help="Latency draw upper bound, seconds.")
@click.option("--spread-mult", default=1.0, type=float, help="Replay-level quote-spread stress multiplier.")
@click.option("--min-fill-size", default=100.0, type=float, help="Min print size counting as limit-fill evidence (odd-lot robustness).")
@click.option("--z-skip", default=0.5, type=float, help="A1 veto threshold; 1e18 = legs-only variant (registered values only).")
@click.option("--a1-rule3", type=click.Choice(["forecast", "a0"]), default="forecast", help="A1 rule-3 mode: forecast (v1) | a0 (v3 legs-only isolation).")
@click.option("--vwap-hold-max", default=None, type=int, help="Registered-variant override of vwap_magnet hold_max_min (ledger M3-A0-vwap-v2-hold75).")
@click.option("--arm", type=click.Choice(["a0", "a1", "m4"]), default="a0", help="a0 = hand-rule plans; a1 = LGBM overlay; m4 = encoder barrier overlay on the same detector states.")
@click.option("--preds-dir", default=None, help="Prediction contract dir (default data/preds/{a1_v1,m4_v1}); only used when --arm a1|m4.")
@click.option("--m4-mode", type=click.Choice(["select", "legs", "both"]), default="select", help="M4 arm: select (barrier veto) | legs (encoder legs) | both; only used when --arm m4.")
@click.option("--p-skip", default=0.45, type=float, help="M4 selector adverse-barrier skip threshold (registered {0.35, 0.45}); only used when --arm m4.")
@click.option("--entry-gate", is_flag=True, default=False, help="Apply the M3-H2-entry-quality-v1 authoring gate on the a0 path (default off; off = byte-identical to baseline).")
def main(trial_id: str, symbols: str, start: str, end: str, k_slots: int, seed: int, lat_lo: float, lat_hi: float, spread_mult: float, min_fill_size: float, z_skip: float, a1_rule3: str, vwap_hold_max: int | None, arm: str, preds_dir: str | None, m4_mode: str, p_skip: float, entry_gate: bool) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    settings = get_settings()
    from enginev51.plans import overlay_a1 as _ov
    _ov.Z_SKIP = z_skip
    _ov.RULE3_MODE = a1_rule3
    _ov.DROP_COUNTS.clear()
    if vwap_hold_max is not None:
        from enginev51.plans import constructor as _pc
        _pc.PAYER_RULES["vwap_magnet"]["hold_max_min"] = vwap_hold_max
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    assert_before_holdout(end_d)

    t0 = time.time()
    df, run_stats = run_trial(
        settings,
        symbols=sym_list,
        start=start_d,
        end=end_d,
        k_slots=k_slots,
        seed=seed,
        lat_lo_s=lat_lo,
        lat_hi_s=lat_hi,
        spread_mult=spread_mult,
        min_fill_size=min_fill_size,
        arm=arm,
        preds_dir=preds_dir,
        m4_mode=m4_mode,
        p_skip=p_skip,
        entry_gate=entry_gate,
    )
    wall_s = time.time() - t0

    out_dir = experiments_dir() / trial_id
    params = params_by_payer()
    results_path, report_path = write_outputs(
        df, out_dir, trial_id, params, run_stats["cost_table"], run_stats
    )

    # ---- stdout headline (ASCII-markdown tables; no box-drawing glyphs) ----
    click.echo(f"trial: {trial_id}  arm={arm}  symbols={','.join(sym_list)}  {start}..{end}")
    if arm == "a1":
        click.echo(f"overlay: preds_dir={run_stats['preds_dir']}  counts={run_stats['overlay_counts']}")
    elif arm == "m4":
        click.echo(f"overlay: preds_dir={run_stats['preds_dir']}  mode={m4_mode}  p_skip={p_skip}  counts={run_stats['overlay_counts']}  drops={run_stats['drop_counts']}")
    click.echo(f"sessions in range (< holdout): {run_stats['sessions_in_range']}")
    click.echo(
        f"symbol-sessions: seen={run_stats['symbol_sessions_seen']} "
        f"ok={run_stats['symbol_sessions_ok']} skips={run_stats['skip_counts']}"
    )
    click.echo(f"detector active states per payer: {run_stats['state_counts']}")
    if entry_gate:
        click.echo(f"entry-gate counts: {run_stats['gate_counts']}")
    click.echo("")
    click.echo(_ascii(_counts_by_payer(df)))
    click.echo("")

    taken = df.filter(pl.col("taken"))
    if taken.height:
        pooled = _split_ci(taken)
        click.echo(f"POOLED taken net_bps (all splits): {_fmt_ci5(pooled)}")
        for split in ("train", "validate"):
            sub = taken.filter(
                pl.col("session").map_elements(split_of, return_dtype=pl.Utf8) == split
            )
            click.echo(f"  {split}: {_fmt_ci5(_split_ci(sub))}")
    else:
        click.echo("POOLED taken net_bps: n=0 (no taken plans)")

    click.echo("")
    click.echo(f"plans authored: {df.height}  taken: {taken.height}")
    click.echo(f"results: {results_path}")
    click.echo(f"report:  {report_path}")
    click.echo(f"wall: {wall_s:.1f}s")


if __name__ == "__main__":
    main()
