"""M10 forward-paper harness for the ``moc_imbalance_v1`` / ``moc_meta_v1`` family
(M3_REGISTRATION.md M8/M9: "POST-HOLDOUT ... forward paper is the sole clean
validation"). The seal was spent by M6-FINAL, so walk-forward OOS is no longer a
clean out-of-sample read; the ONLY uncontaminated evidence left is genuinely
forward sessions, collected one day at a time as they settle. This app does that
collection and keeps the running forward tally against the pre-registered gate.

It is deliberately SMALL and idempotent so it can run daily from cron:

    uv run python -m enginev51.apps.forward_paper run --asof 2026-07-17
    uv run python -m enginev51.apps.forward_paper status

``run --asof <YYYY-MM-DD>`` (a settled session on/after the go-live 2026-07-17):
  1. download that session's NOII + bbo-1s (``data/noii.download_noii`` +
     ``data/bbo1s.download_bbo1s``) — cost-guarded (~cents) and a no-op when the
     month partition already exists;
  2. compute the FROZEN signals via the exact M6-FINAL / M8 code:
       * classical: the |basis_bps| >= 10 events at 15:55:10 ET
         (``apps.run_basis_trial.run_basis_trial``, the same event scan, run on the
         single forward session);
       * meta: P(win) from the FROZEN M8 LightGBM binary model — persisted at
         ``research/forward/m8_model.txt``; if absent it is retrained ONCE,
         deterministically, on all labeled history available at the seal boundary
         (the M6-FINAL |basis|>=10 candidates, < 2026-06-01) and saved. Freezing the
         model at the boundary is the point: the forward test judges a FIXED
         strategy, so the model must not drift as forward data arrives.
  3. append per-event rows to ``research/forward/ledger.parquet`` — APPEND-ONLY and
     deduplicated by (session, symbol), so re-running a day is a no-op.

``status`` prints the running forward stats: n sessions, n events, forward mean net
+ day-clustered CI for the classical and meta-gated (P>=0.55) streams, the backtest
reference (+2.5 classical / +4.0 meta), and progress toward the registered forward
gate (>= 40 sessions, >= 150 events, mean > 0, forward CI consistent with the
backtest expectancy).

M15 SHADOW POSITIONING (``enginev51.positioning``, registered 2026-07-18): each
run also stamps portfolio columns (top-K selection by p_win, equal-notional
whole-share sizing at deploy capital, implementability) and ``status`` reports the
resulting third stream plus a pre-registered CUSUM edge-death monitor. Reported
ONLY — the M10 gate above never reads any of it.

HOLDOUT NOTE: forward sessions are >= 2026-07-17 — POST-holdout by construction, so
the sealed backtest window is never touched here (the seal protects < 2026-06-01
research; this harness only ever reads sessions strictly after it). ``run`` asserts
``asof >= FORWARD_START``.
"""

from __future__ import annotations

import datetime as _dtmod
import json
import os
from datetime import date
from pathlib import Path

import click
import lightgbm as lgb
import numpy as np
import polars as pl
import structlog

from enginev51 import positioning
from enginev51.backtest import stress
from enginev51.config import PROJECT_ROOT, Settings, get_settings
from enginev51.models import moc_meta

log = structlog.get_logger(__name__)

# Go-live: the first forward session this harness may collect. Everything here is
# strictly after the sealed holdout boundary (2026-06-01), by construction.
FORWARD_START = date(2026, 7, 17)

# Frozen signal parameters (UNCHANGED from M6-FINAL / M8 — do not tune here).
CANDIDATE_BASIS_BPS = moc_meta.CANDIDATE_BASIS_BPS  # 10.0
META_GATE_Q = 0.55  # the M8 headline gate (the +4.0 bps reference stream)

# Backtest reference expectancies (the walk-forward OOS point estimates the forward
# stream is measured against): classical |basis|>=10 baseline ~ +2.5, meta gate ~ +4.0.
REF_CLASSICAL_BPS = 2.5
REF_META_BPS = 4.0
# M15 shadow portfolio reference (M15-backtest-reference-v1: top-3-by-p_win on the
# M8 walk-forward OOS, 2022-2026). CORRECTED 2026-07-20: the original +3.4 gated the
# WRONG column — Panel A renamed the M6-GBM continuous bps `pred` to `p_win` and gated
# it at 0.55. The real M8 classifier p_win gate (M8-meta-v1/oos_predictions.parquet)
# gives the top-3 portfolio pooled event-mean +4.06 [3.14, 5.02] n=2,515 / 1,049
# sessions (superseded +3.40 [2.57, 4.26] n=3,085). Pooled-event-mean convention, same
# as REF_META_BPS. Informational only — the registered M10 gate does not read the
# portfolio stream, and this constant feeds the status DISPLAY only (never CUSUM/gate).
REF_PORTFOLIO_BPS = 4.1

# Pre-registered forward gate thresholds (Stage-B-style; M6 forward gate + M8/M9
# "forward paper is the judge"): enough sessions, enough events, mean > 0, and the
# forward CI consistent with the backtest expectancy.
FWD_MIN_SESSIONS = 40
FWD_MIN_EVENTS = 150

FORWARD_DIR = PROJECT_ROOT / "research" / "forward"
LEDGER_PATH = FORWARD_DIR / "ledger.parquet"
MODEL_PATH = FORWARD_DIR / "m8_model.txt"
# The labeled history the frozen meta model is fit on (< holdout by construction).
M6_FINAL_EVENTS = PROJECT_ROOT / "research" / "experiments" / "M6-FINAL-basis" / "events.parquet"

LEDGER_SCHEMA: dict[str, pl.DataType] = {
    "session": pl.Utf8,
    "symbol": pl.Utf8,
    "basis_bps": pl.Float64,
    "p_win": pl.Float64,
    "side": pl.Int64,
    "entry_px": pl.Float64,
    "exit_px": pl.Float64,
    "cross_px": pl.Float64,
    "net_bps": pl.Float64,
    "taken_classical": pl.Boolean,
    "taken_meta": pl.Boolean,
    # M15 shadow-positioning columns (see enginev51.positioning; the M10 gate
    # never reads these — they carry the third, REPORTED-only portfolio stream).
    **positioning.PORTFOLIO_COLS,
    "asof": pl.Utf8,
}


# --------------------------------------------------------------------------- guards


def assert_forward_only(asof: date) -> None:
    """Refuse any asof before the go-live (forward is post-holdout by construction).

    The forward harness collects only genuinely forward sessions; a date before
    ``FORWARD_START`` would either reach into the sealed backtest window or predate
    the frozen strategy, so it is rejected outright.

    RAISES (code review 2026-08-01, lane-A flag): this used to be a bare ``assert``,
    which ``python -O`` / PYTHONOPTIMIZE compiles out — the go-live boundary must not
    be disable-able by an environment variable any more than the holdout seal is.
    ``SealViolation`` is the module's existing refusal idiom (see
    ``train_frozen_model``) and the failure it prevents is exactly a reach back into
    the sealed backtest window.
    """
    from enginev51.protocol import SealViolation

    if asof < FORWARD_START:
        raise SealViolation(
            f"--asof {asof} is before the forward go-live {FORWARD_START.isoformat()}; "
            "forward paper collects only post-holdout forward sessions (M8/M9 registration)"
        )


# --------------------------------------------------------------------------- model


def train_frozen_model(
    events_path: str | Path = M6_FINAL_EVENTS,
) -> tuple[lgb.Booster, dict]:
    """Retrain-through-latest the frozen M8 meta model on the labeled seed history.

    The M8 model was never persisted (only its OOS predictions were), so we refit
    it ONCE on every labeled |basis|>=10 candidate available at the seal boundary
    (the M6-FINAL events, all < 2026-06-01), with the exact registered features and
    binary objective (``moc_meta.train_fold``). Deterministic (seed fixed in
    ``lgbm.DEFAULT_PARAMS`` / ``moc_meta.META_PARAMS``). Returns (booster, note).
    """
    events = pl.read_parquet(events_path)
    from enginev51.protocol import HOLDOUT_START, SealViolation

    if (events["session"].max() or "") >= HOLDOUT_START.isoformat():
        raise SealViolation(
            "seed history reaches the sealed holdout — refusing (PROTOCOL v6 §1)"
        )
    meta = moc_meta.build_meta_frame(events)
    booster = moc_meta.train_fold(meta)
    note = {
        "retrained_through": events["session"].max(),
        "n_train_candidates": meta.height,
        "n_train_sessions": int(meta["session"].n_unique()),
        "features": len(moc_meta.FEATURE_COLS),
    }
    return booster, note


def get_or_train_model(
    *, model_path: str | Path = MODEL_PATH, events_path: str | Path = M6_FINAL_EVENTS
) -> tuple[lgb.Booster, dict]:
    """Load the persisted frozen model, or train + persist it on first use.

    The persisted model at ``model_path`` is the frozen strategy under forward test;
    it is trained exactly once (through the seal boundary) and then reused verbatim
    every day, so the forward evidence is a clean read on a FIXED model.
    """
    model_path = Path(model_path)
    if model_path.exists():
        return lgb.Booster(model_file=str(model_path)), {"loaded_from": str(model_path)}
    booster, note = train_frozen_model(events_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(model_path))
    note["saved_to"] = str(model_path)
    return booster, note


# --------------------------------------------------------------------------- signals


def compute_session_events(
    settings: Settings,
    asof: date,
    *,
    seed: int = 7,
    noii_dir: str | Path | None = None,
    bbo_dir: str | Path | None = None,
) -> pl.DataFrame:
    """The FROZEN M6-FINAL event scan for the single forward session ``asof``.

    Reuses ``run_basis_trial.run_basis_trial`` verbatim (same near/mid basis, same
    honest taker entry + auction-cross exit, same PIT features) restricted to the
    one session. ``holdout_only=True`` selects the post-2026-06-01 path — forward
    sessions ARE post-holdout, so this is the correct, non-ceremony use of that flag
    (no ledger write, no unseal token: those live only in the run_basis_trial CLI).
    """
    from enginev51.apps.run_basis_trial import run_basis_trial

    events, _stats = run_basis_trial(
        settings,
        symbols=list(moc_meta.UNIVERSE),
        start=asof,
        end=asof,
        seed=seed,
        noii_dir=noii_dir,
        bbo_dir=bbo_dir,
        holdout_only=True,  # forward = post-holdout; scans sessions >= 2026-06-01
    )
    return events


def score_events(events: pl.DataFrame, booster: lgb.Booster) -> pl.DataFrame:
    """Attach the frozen meta ``p_win`` and the two taken flags to the event frame.

    ``taken_classical`` = the classical rule (|basis_bps| >= 10). ``taken_meta`` =
    classical AND P(win) >= the M8 gate (0.55). ``p_win`` is emitted for every event
    (the model applies to any feature vector) so the ledger keeps the full context.
    """
    if events.height == 0:
        return events.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("p_win"),
            pl.lit(None, dtype=pl.Boolean).alias("taken_classical"),
            pl.lit(None, dtype=pl.Boolean).alias("taken_meta"),
        )
    moc_meta.assert_features_present(events)
    pwin = moc_meta.predict_pwin(booster, events)
    out = events.with_columns(pl.Series("p_win", pwin))
    return out.with_columns(
        (pl.col("basis_bps").abs() >= CANDIDATE_BASIS_BPS).alias("taken_classical"),
    ).with_columns(
        (pl.col("taken_classical") & (pl.col("p_win") >= META_GATE_Q)).alias("taken_meta"),
    )


def ledger_rows(scored: pl.DataFrame, asof: date) -> pl.DataFrame:
    """Project a scored event frame onto the append-only ledger schema.

    Any schema column absent from ``scored`` (e.g. the M15 portfolio columns when
    positioning was not applied) is filled with nulls, so the projection is total.
    """
    if scored.height == 0:
        return pl.DataFrame(schema=LEDGER_SCHEMA)
    out = scored.with_columns(pl.lit(asof.isoformat()).alias("asof"))
    fills = [
        pl.lit(None, dtype=dt).alias(c)
        for c, dt in LEDGER_SCHEMA.items()
        if c not in out.columns
    ]
    if fills:
        out = out.with_columns(fills)
    return out.select(list(LEDGER_SCHEMA)).cast(LEDGER_SCHEMA)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- ledger I/O


def load_ledger(path: str | Path = LEDGER_PATH) -> pl.DataFrame:
    """The forward ledger, or an empty schema-correct frame when none exists yet."""
    path = Path(path)
    if not path.exists():
        return pl.DataFrame(schema=LEDGER_SCHEMA)
    return pl.read_parquet(path)


def _write_atomic(df: pl.DataFrame, path: Path) -> None:
    """Write ``df`` to ``path`` via a ``.tmp`` sibling + os.replace (S6).

    Same idiom as the live journal (``live/engine._write_atomic``). The forward
    ledger IS the validation clock: an in-place ``write_parquet`` interrupted
    mid-write leaves a truncated file where every previously collected forward
    session used to be, and there is no way to re-derive them (forward sessions
    are collected once, as they settle).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.write_parquet(tmp)
    os.replace(tmp, path)


def append_ledger(new_rows: pl.DataFrame, path: str | Path = LEDGER_PATH) -> dict:
    """Append ``new_rows`` to the ledger, deduped by (session, symbol) — idempotent.

    APPEND-ONLY: existing rows are never rewritten or removed; only (session,
    symbol) pairs not already present are added. Re-running a settled day therefore
    appends nothing. The write is ATOMIC (``_write_atomic``). Returns a summary
    (appended / skipped / total).
    """
    path = Path(path)
    existing = load_ledger(path)
    if new_rows.height == 0:
        return {"appended": 0, "skipped": 0, "total": existing.height}
    if existing.height:
        keys = set(
            zip(existing["session"].to_list(), existing["symbol"].to_list(), strict=True)
        )
        mask = [
            (s, y) not in keys
            for s, y in zip(
                new_rows["session"].to_list(), new_rows["symbol"].to_list(), strict=True
            )
        ]
        add = new_rows.filter(pl.Series(mask))
        out = pl.concat([existing, add.select(existing.columns).cast(existing.schema)])  # type: ignore[arg-type]
    else:
        add = new_rows
        out = new_rows
    _write_atomic(out, path)
    return {
        "appended": add.height,
        "skipped": new_rows.height - add.height,
        "total": out.height,
    }


# --------------------------------------------------------------------------- download


def download_session(
    settings: Settings,
    asof: date,
    *,
    noii_dir: str | Path = "data/raw/noii",
    bbo_dir: str | Path = "data/raw/bbo1s",
    max_cost_noii: float = 5.0,
    max_cost_bbo: float = 5.0,
    require_condition_probe: bool = True,
    client: object | None = None,
) -> dict:
    """Cost-guarded NOII + bbo-1s pull for the one session's month (no-op if present).

    Both downloaders are resumable per (symbol, month): a present partition is
    skipped, so re-running a settled day fetches nothing. ``client`` is injectable
    for tests (mock databento). Costs are ~cents for a single month of five symbols.

    ``require_condition_probe=False`` (CLI: ``--skip-condition-probe``) is the
    operator escape hatch for a DOWN vendor condition endpoint — see
    ``data/noii._end_day_available``. It never overrides an explicit
    degraded/pending verdict.
    """
    from enginev51.data import backfill
    from enginev51.data.bbo1s import download_bbo1s
    from enginev51.data.noii import download_noii

    iso = asof.isoformat()
    syms = list(moc_meta.UNIVERSE)
    noii = download_noii(
        settings, syms, iso, iso, out_dir=noii_dir, max_cost=max_cost_noii,
        require_condition_probe=require_condition_probe, client=client,
    )
    bbo = download_bbo1s(
        settings, syms, iso, iso, out_dir=bbo_dir, max_cost=max_cost_bbo,
        require_condition_probe=require_condition_probe, client=client,
    )
    # Exit-price source, in historical parity order: the conditioned cross print
    # from the session's raw trades when present, else the OFFICIAL DAILY CLOSE
    # from bars1d (cross_price_for). On this lake the daily close has been the
    # operative source for 100% of M6 events (cross_size==0 for all 7,959), so
    # BOTH the tick partitions AND the day's bars1d row must be extended daily —
    # either gap alone makes every event die at no_cross (found live 2026-07-18).
    # Skipped automatically when a mock databento client is injected (tests).
    ticks_written = 0
    bars_appended = 0
    if client is None:
        work = backfill.plan_ticks(settings, syms, asof, asof)
        ticks_written = backfill.run_ticks(settings, work) if work else 0
        bars_appended = _extend_bars1d(settings, syms, asof)
    return {
        "noii": noii,
        "bbo1s": bbo,
        "tick_partitions_written": ticks_written,
        "bars1d_rows_appended": bars_appended,
    }


def _extend_bars1d(
    settings: Settings, syms: list[str], asof: date, bars_dir: str | Path = "data/raw/sip/bars1d"
) -> int:
    """Append ``asof``'s official daily bar to each symbol's bars1d parquet.

    bars1d carries the official close that prices the auction exit (and the ADV20
    input). Alpaca keys daily bars at midnight ET — the lake's existing ``ts``
    convention — and rows are deduped by calendar date, so re-runs are no-ops.
    """
    from zoneinfo import ZoneInfo

    from enginev51.data.alpaca_hist import AlpacaHist

    et = ZoneInfo("America/New_York")
    start = _dtmod.datetime.combine(asof, _dtmod.time(0, 0), tzinfo=et)
    end = start + _dtmod.timedelta(days=1)
    api = AlpacaHist(settings)
    try:
        # bars1d is a raw-adjustment lake by convention (run_m11.py:257,
        # run_xs_reversal.py:172). The AlpacaHist default is adjustment="all";
        # on an ex-dividend fetch day that returns the prior session's official
        # close back-adjusted by the dividend factor, corrupting the auction-exit
        # price and creating a mixed-vintage lake (SIM_AUDIT_2026-07-21 F1-class).
        # Pin raw so appended rows match the existing lake vintage.
        got = api.fetch_bars_multi(syms, start, end, timeframe="1Day", adjustment="raw")
    finally:
        api.close()
    appended = 0
    for sym in syms:
        rows = got.get(sym.upper()) or []
        if not rows:
            log.warning("bars1d_no_daily_bar", symbol=sym, asof=asof.isoformat())
            continue
        p = Path(bars_dir) / f"{sym.upper()}.parquet"
        if not p.exists():
            log.warning("bars1d_missing_file", symbol=sym)
            continue
        existing = pl.read_parquet(p)
        new = pl.DataFrame(rows).select(existing.columns).cast(existing.schema)  # type: ignore[arg-type]
        have_dates = set(
            existing.select(pl.col("ts").cast(pl.Datetime("ns")).dt.date().cast(pl.Utf8))
            .to_series()
            .to_list()
        )
        new = new.filter(
            ~pl.col("ts").cast(pl.Datetime("ns")).dt.date().cast(pl.Utf8).is_in(list(have_dates))
        )
        if new.height == 0:
            continue
        pl.concat([existing, new]).sort("ts").write_parquet(p)
        appended += new.height
        log.info("bars1d_appended", symbol=sym, asof=asof.isoformat(), rows=new.height)
    return appended


# --------------------------------------------------------------------------- status


def _stream_ci(df: pl.DataFrame) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n, n_sessions) day-clustered over net_bps for a taken stream."""
    if df.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    m, lo, hi = stress.clustered_mean_ci(
        df["net_bps"].to_numpy(), df["session"].to_numpy()
    )
    return m, lo, hi, df.height, int(df["session"].n_unique())


def status_stats(ledger: pl.DataFrame) -> dict:
    """Running forward stats + gate progress for the classical and meta streams.

    ``consistent`` per stream = the backtest reference expectancy falls inside the
    forward 95% day-clustered CI (Stage-B live-vs-backtest CI overlap). The gate is
    met when both streams have mean > 0 and are consistent AND the sample floors
    (>= 40 sessions, >= 150 classical events) are cleared.
    """
    classical = ledger.filter(pl.col("taken_classical")) if ledger.height else ledger
    meta = ledger.filter(pl.col("taken_meta")) if ledger.height else ledger

    c_m, c_lo, c_hi, c_n, c_ns = _stream_ci(classical)
    m_m, m_lo, m_hi, m_n, m_ns = _stream_ci(meta)

    n_sessions = int(ledger["session"].n_unique()) if ledger.height else 0
    n_events = c_n  # classical candidate events

    def _consistent(lo: float, hi: float, ref: float) -> bool:
        return bool(np.isfinite(lo) and np.isfinite(hi) and lo <= ref <= hi)

    classical_stats = {
        "n_events": c_n, "n_sessions": c_ns,
        "mean_net_bps": round(c_m, 3) if c_n else None,
        "ci_lo": round(c_lo, 3) if c_n else None,
        "ci_hi": round(c_hi, 3) if c_n else None,
        "ref_backtest": REF_CLASSICAL_BPS,
        "mean_gt_0": bool(c_n and c_m > 0),
        "ci_lo_gt_0": bool(c_n and c_lo > 0),
        "consistent_with_backtest": _consistent(c_lo, c_hi, REF_CLASSICAL_BPS),
    }
    meta_stats = {
        "n_events": m_n, "n_sessions": m_ns,
        "mean_net_bps": round(m_m, 3) if m_n else None,
        "ci_lo": round(m_lo, 3) if m_n else None,
        "ci_hi": round(m_hi, 3) if m_n else None,
        "ref_backtest": REF_META_BPS,
        "mean_gt_0": bool(m_n and m_m > 0),
        "ci_lo_gt_0": bool(m_n and m_lo > 0),
        "consistent_with_backtest": _consistent(m_lo, m_hi, REF_META_BPS),
    }
    gate = {
        "sessions_ge_40": n_sessions >= FWD_MIN_SESSIONS,
        "events_ge_150": n_events >= FWD_MIN_EVENTS,
        "classical_mean_gt_0": classical_stats["mean_gt_0"],
        "meta_mean_gt_0": meta_stats["mean_gt_0"],
        "classical_ci_consistent": classical_stats["consistent_with_backtest"],
        "meta_ci_consistent": meta_stats["consistent_with_backtest"],
    }
    gate["forward_gate_met"] = bool(
        gate["sessions_ge_40"]
        and gate["events_ge_150"]
        and gate["classical_mean_gt_0"]
        and gate["meta_mean_gt_0"]
        and gate["classical_ci_consistent"]
        and gate["meta_ci_consistent"]
    )
    return {
        "n_sessions": n_sessions,
        "n_events": n_events,
        "sessions_needed": max(0, FWD_MIN_SESSIONS - n_sessions),
        "events_needed": max(0, FWD_MIN_EVENTS - n_events),
        "classical": classical_stats,
        "meta": meta_stats,
        # M15 shadow portfolio stream — REPORTED only; the gate above never reads it.
        "portfolio": positioning.portfolio_stats(ledger),
        "gate": gate,
        "asof_span": (
            [ledger["session"].min(), ledger["session"].max()] if ledger.height else []
        ),
    }


def format_status(stats: dict) -> str:
    """Human-readable status block (the daily console view)."""
    c, m, g = stats["classical"], stats["meta"], stats["gate"]

    def _ci(s: dict) -> str:
        if not s["n_events"]:
            return "n=0 (no events yet)"
        return (
            f"mean={s['mean_net_bps']:+.3f}  95%CI=[{s['ci_lo']:+.3f}, {s['ci_hi']:+.3f}]  "
            f"n={s['n_events']}  sessions={s['n_sessions']}  "
            f"(backtest ref {s['ref_backtest']:+.1f}; consistent={s['consistent_with_backtest']})"
        )

    p = stats["portfolio"]
    if p["n_events"]:
        impl = (
            f"{p['implementable_rate']:.0%}"
            if p["implementable_rate"] is not None
            else "n/a"
        )
        impl_dep = (
            f"{p['implementable_deploy_rate']:.0%}"
            if p.get("implementable_deploy_rate") is not None
            else "n/a"
        )
        port_line = (
            f"mean={p['mean_net_bps']:+.3f}  95%CI=[{p['ci_lo']:+.3f}, {p['ci_hi']:+.3f}]  "
            f"n={p['n_events']}  sessions={p['n_sessions']}  impl@"
            f"${p['capital_usd']:.0f}={impl}  deploy@${p['deploy_capital_usd']:.0f}={impl_dep}"
            f"  (backtest ref {REF_PORTFOLIO_BPS:+.1f}; corrected 2026-07-20, "
            f"superseded +3.4 mislabeled gate)"
        )
        cusum_line = (
            f"CUSUM S={p['cusum_S']:.1f} (k={p['cusum_k']}, h={p['cusum_h']})  "
            f"ALERT={p['cusum_alert']}  alert-sessions={p['n_alert_sessions']}"
        )
    else:
        port_line = "n=0 (no events yet)"
        cusum_line = f"CUSUM idle (k={p['cusum_k']}, h={p['cusum_h']})"

    lines = [
        "M10 forward-paper status — moc_meta_v1 (POST-HOLDOUT; the sole clean validation)",
        "",
        f"sessions collected: {stats['n_sessions']}   classical events: {stats['n_events']}"
        + (f"   span {stats['asof_span'][0]}..{stats['asof_span'][1]}" if stats["asof_span"] else ""),
        "",
        f"classical (|basis|>=10):  {_ci(c)}",
        f"meta-gated (P>=0.55):     {_ci(m)}",
        f"portfolio SHADOW top-{p['max_positions']} (M15, reported only): {port_line}",
        f"  edge-death monitor:     {cusum_line}",
        "",
        "registered forward gate (>=40 sessions, >=150 events, mean>0, CI consistent w/ backtest):",
        f"  sessions >= 40:            {g['sessions_ge_40']}  ({stats['sessions_needed']} to go)",
        f"  events   >= 150:           {g['events_ge_150']}  ({stats['events_needed']} to go)",
        f"  classical mean > 0:        {g['classical_mean_gt_0']}",
        f"  meta mean > 0:             {g['meta_mean_gt_0']}",
        f"  classical CI consistent:   {g['classical_ci_consistent']}",
        f"  meta CI consistent:        {g['meta_ci_consistent']}",
        f"  >>> FORWARD GATE MET:      {g['forward_gate_met']}",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- run


def run_asof(
    settings: Settings,
    asof: date,
    *,
    seed: int = 7,
    noii_dir: str | Path = "data/raw/noii",
    bbo_dir: str | Path = "data/raw/bbo1s",
    ledger_path: str | Path = LEDGER_PATH,
    model_path: str | Path = MODEL_PATH,
    do_download: bool = True,
    require_condition_probe: bool = True,
    download_client: object | None = None,
) -> dict:
    """Collect one forward session end-to-end: download -> signals -> ledger append.

    Returns a summary dict (download counts, events scanned/candidates, model note,
    ledger append result). Idempotent: a second call for the same settled ``asof``
    downloads nothing new and appends nothing new.
    """
    assert_forward_only(asof)
    dl: dict = {}
    if do_download:
        dl = download_session(
            settings, asof, noii_dir=noii_dir, bbo_dir=bbo_dir,
            require_condition_probe=require_condition_probe, client=download_client,
        )
    booster, model_note = get_or_train_model(model_path=model_path)
    events = compute_session_events(
        settings, asof, seed=seed, noii_dir=noii_dir, bbo_dir=bbo_dir
    )
    scored = score_events(events, booster)
    scored = positioning.apply_positioning(scored)  # M15 shadow columns (reported only)
    rows = ledger_rows(scored, asof)
    append = append_ledger(rows, ledger_path)
    n_sel = int(scored.filter(pl.col("selected").fill_null(False)).height) if scored.height else 0
    n_impl = (
        int(scored.filter(pl.col("implementable").fill_null(False)).height)
        if scored.height
        else 0
    )
    return {
        "asof": asof.isoformat(),
        "download": dl,
        "n_events_scanned": events.height,
        "n_candidates": int(scored.filter(pl.col("taken_classical")).height) if scored.height else 0,
        "n_meta_taken": int(scored.filter(pl.col("taken_meta")).height) if scored.height else 0,
        "n_selected": n_sel,
        "n_implementable": n_impl,
        "model_note": model_note,
        "ledger": append,
    }


# --------------------------------------------------------------------------- cli


@click.group()
def main() -> None:
    """M10 forward-paper harness (moc_meta_v1) — run daily as sessions settle."""
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety


@main.command("run")
@click.option("--asof", required=True, help="Settled forward session (ISO date), >= 2026-07-17.")
@click.option("--seed", default=7, type=int, help="Latency-draw seed (frozen).")
@click.option("--noii-dir", default="data/raw/noii", help="NOII lake root.")
@click.option("--bbo-dir", default="data/raw/bbo1s", help="BBO-1s lake root.")
@click.option("--no-download", is_flag=True, help="Skip the databento pull (use already-present partitions).")
@click.option("--skip-condition-probe", "require_condition_probe", flag_value=False,
              default=True, type=bool,
              help="OPERATOR OVERRIDE: if the vendor condition endpoint is DOWN, proceed without the degradation check instead of skipping the end month. An explicit degraded/pending verdict still skips.")
def run_cmd(asof: str, seed: int, noii_dir: str, bbo_dir: str, no_download: bool,
            require_condition_probe: bool) -> None:
    settings = get_settings()
    asof_d = date.fromisoformat(asof)
    summary = run_asof(
        settings, asof_d, seed=seed, noii_dir=noii_dir, bbo_dir=bbo_dir,
        do_download=not no_download, require_condition_probe=require_condition_probe,
    )
    click.echo(json.dumps(summary, indent=2, default=str))
    click.echo("")
    click.echo(format_status(status_stats(load_ledger())))


@main.command("status")
@click.option("--ledger", "ledger_path", default=str(LEDGER_PATH), help="Forward ledger parquet.")
@click.option("--json", "as_json", is_flag=True, help="Emit the stats dict as JSON.")
def status_cmd(ledger_path: str, as_json: bool) -> None:
    ledger = load_ledger(ledger_path)
    stats = status_stats(ledger)
    if as_json:
        click.echo(json.dumps(stats, indent=2, default=str))
    else:
        click.echo(format_status(stats))


if __name__ == "__main__":
    main()
