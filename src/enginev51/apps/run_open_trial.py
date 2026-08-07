"""M6b OPENING-cross imbalance trial runner — opening-NOII signal -> MOO entry ->
market-out exit -> net-bps evidence.

Drives the registered ``open_imbalance_v1`` family (M3_REGISTRATION.md M6b section)
over a date range of NYSE sessions, per symbol:

    load_noii_opening -> signal_at(09:28:30 ET) -> (if |norm_imb| >= threshold)
      -> MOO entry AT the official opening print (daily bar OPEN, ts 09:30:00,
         zero spread/slip — the Nasdaq official open IS the opening cross, the
         same fill-ambiguity-free logic as the M6 MOC exit)
      -> market-out exit at 09:45 or 10:00 ET + latency draw crossing the
         prevailing bbo-1s BBO + slip -> net bps

and accumulates a per-event results frame + a ``report.md`` under
``research/experiments/<trial_id>/``. Pooled / per-symbol / by-year net-bps CIs
are day-clustered (``stress.clustered_mean_ci``); a 10-event stratified
ground-truth table verifies each sampled event's official open against the first
bbo-1s mid at 09:30:00-09:30:05 (deviations > 20 bps flagged) and each exit fill
against the prevailing BBO (PROTOCOL v6.1).

--- DESIGN NOTES (flagged per the task) --------------------------------------
* The ``load_noii_opening`` helper lives HERE (not in data/noii.py) to keep the
  footprint self-contained and avoid mutating a module several other trials
  import. It reuses ``noii.noii_root`` / ``noii.partition_path`` and returns the
  SAME ``NOII_SCHEMA`` frame as ``load_noii_session``, just filtered to the
  opening dissemination window instead of the closing one.

* MESSAGE WINDOW (verified 2026-07-17 on NVDA 2025-05): opening-cross NOII
  messages disseminate 09:25-09:30 ET in the owned ``imbalance``-schema
  partitions (hour-9 messages: 09:25..09:29 heavy, a few at 09:30; ZERO before
  09:25). ``near_price`` (indicative clearing price) is 0 until ~09:28 and
  populates from 09:28 on; before that ``signal_at`` falls back near->ref exactly
  as on the closing side. We load [09:00:00, 09:30:00] ET (generous lower margin)
  and let ``signal_at`` pick the LAST message at-or-before 09:28:30 ET (PIT).

* The signal, ADV20$, and net-bps decomposition all reuse the EXISTING M6
  primitives unchanged: ``noii.signal_at`` (same norm_imb formula, near->ref
  fallback), ``auction_replay.adv20_dollars`` (minute-bar ADV with daily
  fallback), ``fills.market_fill`` / ``latency.latency_ns`` / ``decompose.plan_pnl``.
  Only the entry/exit wiring is new (mirror of ``replay_moc_event``: the fixed
  price is now the ENTRY (open) rather than the EXIT (cross)).

Hard PIT/holdout guard: the run refuses any ``--end`` on/after
``protocol.HOLDOUT_START`` and hard-filters every session strictly before it.
This app writes NO ledger row — the orchestrator owns verdicts.

    uv run python -m enginev51.apps.run_open_trial --trial-id M6b-open-imbalance-v1-t05-0945 \
        --symbols NVDA,TSLA,AMD,MU,GOOGL --start 2020-01-02 --end 2026-05-31 \
        --threshold 0.0005 --exit 0945 --seed 7
"""

from __future__ import annotations

import functools
import json
import time
from datetime import UTC, date, datetime
from pathlib import Path

import click
import numpy as np
import polars as pl
import structlog

from enginev51.backtest import fills as fk
from enginev51.backtest import latency as lat
from enginev51.backtest import stress
from enginev51.backtest.auction_replay import adv20_dollars, tape_from_bbo
from enginev51.backtest.decompose import PlanPnl, plan_pnl
from enginev51.backtest.fills import prevailing_idx
from enginev51.backtest.replay import SessionTape
from enginev51.config import Settings, get_settings
from enginev51.data import calendar
from enginev51.data.bbo1s import load_bbo_session
from enginev51.data.noii import (
    et_ns,
    noii_root,
    partition_path,
    signal_at,
)
from enginev51.protocol import (
    HOLDOUT_START,
    experiments_dir,
    refuse_end_on_or_after_holdout,
    split_of,
)

log = structlog.get_logger(__name__)

NS_PER_S = 1_000_000_000
SYMBOLS_DEFAULT = "NVDA,TSLA,AMD,MU,GOOGL"

# Opening-cross NOII dissemination window (ET). Verified: messages fall in
# 09:25-09:30; we load from 09:00 for a generous lower margin. The registered
# signal instant is 09:28:30 ET (last message at-or-before it, PIT).
OPEN_WINDOW_START_ET = (9, 0, 0)
OPEN_WINDOW_END_ET = (9, 30, 0)
OPEN_SIGNAL_ET = (9, 28, 30)  # registered: last opening-NOII at-or-before this
ENTRY_ET = (9, 30, 0)  # MOO fill instant = the official open
# First-print window for the ground-truth open-vs-mid check.
OPEN_MID_LO_ET = (9, 30, 0)
OPEN_MID_HI_ET = (9, 30, 5)

# Registered exit cells: market-out at 09:45 or 10:00 ET.
EXIT_TIMES_ET: dict[str, tuple[int, int, int]] = {
    "0945": (9, 45, 0),
    "1000": (10, 0, 0),
}

OPEN_RESULTS_SCHEMA: dict[str, pl.DataType] = {
    "session": pl.Utf8,
    "symbol": pl.Utf8,
    "side": pl.Int64,
    "norm_imb": pl.Float64,
    "adv20_dollars": pl.Float64,
    "near_price": pl.Float64,
    "open_px": pl.Float64,
    "entry_ts": pl.Int64,
    "exit_signal_ts": pl.Int64,
    "exit_ts": pl.Int64,
    "exit_px": pl.Float64,
    "exit_bid": pl.Float64,
    "exit_ask": pl.Float64,
    "exit_reason": pl.Utf8,
    "open_bbo_mid": pl.Float64,
    "net_bps": pl.Float64,
    "hold_s": pl.Float64,
}


# --------------------------------------------------------------------------- guard


def assert_before_holdout(end: date) -> None:
    """Refuse any run reaching the sealed holdout boundary (PROTOCOL v6 §1).

    Raises SealViolation (never a bare assert: ``python -O`` strips those)."""
    refuse_end_on_or_after_holdout(end)


# ------------------------------------------------------------------ opening NOII


def load_noii_opening(
    symbol: str, session: str, *, out_dir: str | Path | None = None
) -> pl.DataFrame | None:
    """The 09:00-09:30 ET OPENING-cross NOII messages for one (symbol, session).

    Reads the SAME (symbol, month) partition written by ``download_noii`` (the
    ``imbalance`` schema carries BOTH the opening- and closing-cross NOII) and
    filters to the opening dissemination window. Returns a ``NOII_SCHEMA`` frame
    sorted by ``ts`` (possibly empty), or ``None`` when the partition does not
    exist at all — so callers can distinguish "no data downloaded yet" from
    "empty window". Mirrors ``noii.load_noii_session`` exactly, only the ET
    window differs (opening vs closing cross).
    """
    root = noii_root(out_dir)
    month = session[:7]
    path = partition_path(root, symbol, month)
    if not path.exists():
        return None
    lo = et_ns(session, *OPEN_WINDOW_START_ET)
    hi = et_ns(session, *OPEN_WINDOW_END_ET)
    df = pl.read_parquet(path)
    if df.height == 0:
        return df
    return df.filter((pl.col("ts") >= lo) & (pl.col("ts") <= hi)).sort("ts")


# ------------------------------------------------------------------ daily open


@functools.lru_cache(maxsize=16)
def _daily_opens(symbol: str) -> dict[str, float]:
    """Per-session official OPEN from daily bars (data/raw/sip/bars1d).

    The Nasdaq official open IS the opening-cross print, so the daily bar OPEN is
    the exact MOO fill price (fill-ambiguity-free, mirror of the MOC exit using
    the daily close). The daily-bar ``ts`` is midnight ET, so its UTC date equals
    the session date — the same mapping ``auction_replay._daily_closes`` uses.
    """
    p = Path("data/raw/sip/bars1d") / f"{symbol.upper()}.parquet"
    if not p.exists():
        return {}
    df = pl.read_parquet(p)
    out: dict[str, float] = {}
    for r in df.iter_rows(named=True):
        d = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
        op = r.get("open")
        if op is not None and float(op) > 0.0:
            out[d] = float(op)
    return out


# --------------------------------------------------------------------------- event


def _prevailing_nbbo(tape: SessionTape, ts: int) -> tuple[float | None, float | None]:
    """Prevailing (bid, ask) at ``ts`` from a SessionTape; (None, None) if none."""
    i = prevailing_idx(tape.q_ts, ts)
    if i < 0:
        return None, None
    return float(tape.q_bid[i]), float(tape.q_ask[i])


def _first_bbo_mid(tape: SessionTape, lo_ts: int, hi_ts: int) -> float | None:
    """First BBO mid with ts in [lo_ts, hi_ts]; None if no quote in the window."""
    lo = int(np.searchsorted(tape.q_ts, lo_ts, side="left"))
    hi = int(np.searchsorted(tape.q_ts, hi_ts, side="right"))
    if hi <= lo:
        return None
    return 0.5 * (float(tape.q_bid[lo]) + float(tape.q_ask[lo]))


def replay_open_event(
    tape: SessionTape,
    open_px: float,
    entry_ts: int,
    exit_signal_ts: int,
    side: int,
    seed: int,
    plan_id: str,
    exit_reason: str,
    *,
    lat_lo_s: float = 5.0,
    lat_hi_s: float = 25.0,
    slip_bps: float = 0.5,
    sec_taf_sell_bps: float = 0.3,
) -> tuple[str, PlanPnl | None, dict]:
    """Replay one opening-imbalance event to a net-bps result.

    ENTRY = MOO: fill exactly AT the official opening print ``open_px`` at
    ``entry_ts`` (09:30:00 ET), ZERO spread/slip by construction — the mids are
    set equal to the fill price so the entry contributes no spread/latency term
    (the single opening-cross clearing price has no queue to cross). This is the
    exact mirror of the MOC exit in ``replay_moc_event`` (a fixed known price).

    EXIT = taker MARKET-OUT at ``exit_signal_ts`` (09:45 or 10:00 ET) + a seeded
    U[lat_lo, lat_hi]s latency draw, crossing the prevailing bbo-1s BBO via the
    shared fill kernel (``fills.market_fill``: SELL a long hits bid*(1-slip), BUY
    to cover a short lifts ask*(1+slip)). Honest, slip-bearing — identical
    mechanics to the M6 MOC entry.

    Net bps is decomposed price-to-price minus SEC/TAF on the SELL leg via
    ``decompose.plan_pnl`` (long: sell = exit; short: sell = the MOO entry) — the
    same identity-checked decomposition the main replayer uses.

    Returns ``(status, pnl, extras)`` where status is "ok"/"void"; extras carries
    the exit fill facts for the results frame. Void when no BBO precedes the exit
    action instant.
    """
    if side not in (1, -1):
        return "void", None, {}
    if not open_px > 0.0:
        return "void", None, {}

    # ---- entry: MOO at the official open, zero spread/slip ------------------
    entry_fill = fk.Fill(
        ts=int(entry_ts),
        price=float(open_px),
        qty_frac=1.0,
        leg="moo",
        decision_ts=int(entry_ts),
        mid_at_decision=float(open_px),
        mid_at_action=float(open_px),
        maker=False,
    )

    # ---- exit: taker market-out crossing the bbo-1s BBO + slip --------------
    exit_action = exit_signal_ts + lat.latency_ns(
        seed, plan_id, "exit", lat_lo_s, lat_hi_s
    )
    mk = fk.market_fill(tape.q_ts, tape.q_bid, tape.q_ask, exit_action, -side, slip_bps)
    if mk is None:
        return "void", None, {}
    exit_px, exit_mid_act = mk
    exit_fill = fk.Fill(
        ts=exit_action,
        price=exit_px,
        qty_frac=1.0,
        leg="exit",
        decision_ts=exit_signal_ts,
        mid_at_decision=fk.prevailing_mid(
            tape.q_ts, tape.q_bid, tape.q_ask, exit_signal_ts
        ),
        mid_at_action=exit_mid_act,
        maker=False,
    )

    pnl = plan_pnl(side, (entry_fill,), (exit_fill,), sec_taf_sell_bps)
    exit_bid, exit_ask = _prevailing_nbbo(tape, exit_action)
    extras = {
        "entry_ts": entry_fill.ts,
        "exit_ts": exit_fill.ts,
        "exit_px": exit_fill.price,
        "exit_bid": exit_bid,
        "exit_ask": exit_ask,
        "exit_reason": exit_reason,
        "hold_s": (exit_fill.ts - entry_fill.ts) / NS_PER_S,
    }
    return "ok", pnl, extras


# --------------------------------------------------------------------------- run


def run_open_trial(
    settings: Settings,
    *,
    symbols: list[str],
    start: date,
    end: date,
    threshold: float,
    exit_cell: str,
    seed: int,
    noii_dir: str | Path | None = None,
    bbo_dir: str | Path | None = None,
    lat_lo_s: float = 5.0,
    lat_hi_s: float = 25.0,
) -> tuple[pl.DataFrame, dict]:
    """Execute the M6b pipeline over [start, end] sessions; return (results, stats).

    One event per (symbol, session) whose 09:28:30-ET opening-NOII signal is
    active (``|norm_imb| >= threshold`` and a definite side). ``exit_cell`` is
    "0945" or "1000" (the two registered exit times). Sessions missing any of the
    NOII partition / ADV / active signal / daily open / bbo-1s session are counted
    in the funnel, not hidden.
    """
    assert_before_holdout(end)
    if exit_cell not in EXIT_TIMES_ET:
        raise ValueError(f"exit_cell must be one of {list(EXIT_TIMES_ET)}, got {exit_cell!r}")
    symbols = [s.strip().upper() for s in symbols]

    counts = {
        "no_noii_partition": 0,
        "no_noii_msgs": 0,
        "no_adv": 0,
        "no_signal": 0,
        "inactive": 0,
        "events_fired": 0,
        "skipped_no_open": 0,
        "skipped_no_bbo": 0,
        "void": 0,
    }

    rows: list[dict] = []
    sessions = [d for d in calendar.trading_days(start, end) if d < HOLDOUT_START]
    for sd in sessions:
        session_iso = sd.isoformat()
        for sym in symbols:
            noii = load_noii_opening(sym, session_iso, out_dir=noii_dir)
            if noii is None:
                counts["no_noii_partition"] += 1
                continue
            if noii.height == 0:
                counts["no_noii_msgs"] += 1
                continue

            adv = adv20_dollars(settings, sym, session_iso)
            if adv is None:
                counts["no_adv"] += 1
                continue

            signal_ts = et_ns(session_iso, *OPEN_SIGNAL_ET)
            sig = signal_at(noii, signal_ts, adv)
            if sig is None:
                counts["no_signal"] += 1
                continue
            side = int(sig["side"])
            norm_imb = float(sig["norm_imb"])
            if side == 0 or abs(norm_imb) < threshold:
                counts["inactive"] += 1
                continue

            counts["events_fired"] += 1

            open_px = _daily_opens(sym).get(session_iso)
            if open_px is None:
                counts["skipped_no_open"] += 1
                continue

            bbo = load_bbo_session(sym, session_iso, out_dir=bbo_dir)
            if bbo is None or bbo.height == 0:
                counts["skipped_no_bbo"] += 1
                continue
            tape = tape_from_bbo(sym, bbo)

            entry_ts = et_ns(session_iso, *ENTRY_ET)
            exit_signal_ts = et_ns(session_iso, *EXIT_TIMES_ET[exit_cell])
            plan_id = f"{sym}-{session_iso}-open-{exit_cell}"
            status, pnl, extras = replay_open_event(
                tape, open_px, entry_ts, exit_signal_ts, side, seed, plan_id,
                f"exit_{exit_cell}", lat_lo_s=lat_lo_s, lat_hi_s=lat_hi_s,
                slip_bps=0.5, sec_taf_sell_bps=0.3,
            )
            if status != "ok":
                counts["void"] += 1
                continue

            open_bbo_mid = _first_bbo_mid(
                tape,
                et_ns(session_iso, *OPEN_MID_LO_ET),
                et_ns(session_iso, *OPEN_MID_HI_ET),
            )

            rows.append(
                {
                    "session": session_iso,
                    "symbol": sym,
                    "side": side,
                    "norm_imb": norm_imb,
                    "adv20_dollars": adv,
                    "near_price": float(sig["near_price"]),
                    "open_px": float(open_px),
                    "entry_ts": extras["entry_ts"],
                    "exit_signal_ts": exit_signal_ts,
                    "exit_ts": extras["exit_ts"],
                    "exit_px": extras["exit_px"],
                    "exit_bid": extras["exit_bid"],
                    "exit_ask": extras["exit_ask"],
                    "exit_reason": extras["exit_reason"],
                    "open_bbo_mid": open_bbo_mid,
                    "net_bps": pnl.net_bps,
                    "hold_s": extras["hold_s"],
                }
            )

    df = (
        pl.DataFrame(rows, schema=OPEN_RESULTS_SCHEMA, orient="row")
        if rows
        else pl.DataFrame(schema=OPEN_RESULTS_SCHEMA)
    )
    stats = {
        "symbols": symbols,
        "threshold": threshold,
        "exit_cell": exit_cell,
        "seed": seed,
        "sessions_in_range": len(sessions),
        "counts": counts,
    }
    return df, stats


# --------------------------------------------------------------------------- report


def _ascii(df: pl.DataFrame) -> str:
    with pl.Config(
        tbl_formatting="ASCII_MARKDOWN",
        tbl_hide_dataframe_shape=True,
        tbl_hide_column_data_types=True,
        tbl_rows=200,
        tbl_cols=-1,
        tbl_width_chars=240,
    ):
        return str(df)


def _ci(df: pl.DataFrame) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n_events, n_sessions) day-clustered over net_bps."""
    if df.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    m, lo, hi = stress.clustered_mean_ci(
        df["net_bps"].to_numpy(), df["session"].to_numpy()
    )
    return m, lo, hi, df.height, df["session"].n_unique()


def _fmt_ci(t: tuple[float, float, float, int, int]) -> str:
    m, lo, hi, n, ns = t
    if n == 0:
        return "n=0"
    return f"mean={m:.3f}  95%CI=[{lo:.3f}, {hi:.3f}]  n={n}  sessions={ns}"


def _group_ci_table(df: pl.DataFrame, key: str, values: list[str], label: str) -> pl.DataFrame:
    rows: list[dict] = []
    for v in values:
        sub = df.filter(pl.col(key) == v) if df.height else df
        m, lo, hi, n, ns = _ci(sub)
        rows.append(
            {
                label: v,
                "n_events": n,
                "n_sessions": ns,
                "net_bps_mean": round(m, 3) if n else None,
                "ci_lo": round(lo, 3) if n else None,
                "ci_hi": round(hi, 3) if n else None,
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            label: pl.Utf8,
            "n_events": pl.Int64,
            "n_sessions": pl.Int64,
            "net_bps_mean": pl.Float64,
            "ci_lo": pl.Float64,
            "ci_hi": pl.Float64,
        },
        orient="row",
    )


def _per_symbol_ci_table(df: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []
    syms = sorted(df["symbol"].unique().to_list()) if df.height else []
    for sym in [*syms, "__POOLED__"]:
        sub = df if sym == "__POOLED__" else df.filter(pl.col("symbol") == sym)
        m, lo, hi, n, ns = _ci(sub)
        rows.append(
            {
                "symbol": "POOLED" if sym == "__POOLED__" else sym,
                "n_events": n,
                "n_sessions": ns,
                "net_bps_mean": round(m, 3) if n else None,
                "ci_lo": round(lo, 3) if n else None,
                "ci_hi": round(hi, 3) if n else None,
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            "symbol": pl.Utf8,
            "n_events": pl.Int64,
            "n_sessions": pl.Int64,
            "net_bps_mean": pl.Float64,
            "ci_lo": pl.Float64,
            "ci_hi": pl.Float64,
        },
        orient="row",
    )


def _split_ci_table(df: pl.DataFrame) -> pl.DataFrame:
    if df.height:
        df = df.with_columns(
            pl.col("session").map_elements(split_of, return_dtype=pl.Utf8).alias("split")
        )
    return _group_ci_table(df, "split", ["train", "validate"], "split")


def _by_year_ci_table(df: pl.DataFrame) -> pl.DataFrame:
    years = sorted({s[:4] for s in df["session"].to_list()}) if df.height else []
    if df.height:
        df = df.with_columns(pl.col("session").str.slice(0, 4).alias("year"))
    return _group_ci_table(df, "year", years, "year")


def _stratified_ground_truth(df: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """Sample <=k stratified events (biggest winners/losers, largest |imbalance|)
    and lay out the v6.1 ground-truth: official open vs first bbo-1s mid at
    09:30:00-09:30:05 (deviation > 20 bps flagged), and exit fill vs prevailing
    BBO at the exit instant.
    """
    schema = {
        "session": pl.Utf8, "symbol": pl.Utf8, "side": pl.Int64,
        "norm_imb": pl.Float64, "open_px": pl.Float64, "open_bbo_mid": pl.Float64,
        "open_vs_bbomid_bps": pl.Float64, "open_dev_gt_20bps": pl.Boolean,
        "exit_bid": pl.Float64, "exit_ask": pl.Float64, "exit_px": pl.Float64,
        "exit_in_nbbo": pl.Boolean, "net_bps": pl.Float64,
    }
    if df.height == 0:
        return pl.DataFrame(schema=schema)
    d = df.with_columns(pl.arange(0, pl.len()).alias("_idx"))
    winners = d.sort("net_bps", descending=True).head(3)["_idx"].to_list()
    losers = d.sort("net_bps", descending=False).head(3)["_idx"].to_list()
    big_imb = d.sort(pl.col("norm_imb").abs(), descending=True).head(4)["_idx"].to_list()
    picked: list[int] = []
    for i in [*winners, *losers, *big_imb]:
        if i not in picked:
            picked.append(i)
        if len(picked) >= k:
            break
    sub = d.filter(pl.col("_idx").is_in(picked)).drop("_idx")
    return sub.with_columns(
        (
            pl.when(pl.col("open_bbo_mid").is_not_null() & (pl.col("open_bbo_mid") > 0))
            .then((pl.col("open_px") - pl.col("open_bbo_mid")) / pl.col("open_bbo_mid") * 1e4)
            .otherwise(None)
            .alias("open_vs_bbomid_bps")
        ),
        (
            pl.when(pl.col("exit_bid").is_not_null() & pl.col("exit_ask").is_not_null())
            .then(
                (pl.col("exit_px") >= pl.col("exit_bid") * 0.999)
                & (pl.col("exit_px") <= pl.col("exit_ask") * 1.001)
            )
            .otherwise(None)
            .alias("exit_in_nbbo")
        ),
    ).with_columns(
        (pl.col("open_vs_bbomid_bps").abs() > 20.0).alias("open_dev_gt_20bps")
    ).select(list(schema))


def _promotion_diagnostic(df: pl.DataFrame) -> dict:
    """Registered M6b promotion bar (diagnostic echo, NOT a gate here):
    pooled day-clustered CI lower > 0 AND >=100 events AND positive point
    estimate in >=3 of 5 symbols."""
    m, lo, hi, n, ns = _ci(df)
    sym_pos = 0
    syms = sorted(df["symbol"].unique().to_list()) if df.height else []
    per_sym: dict[str, float | None] = {}
    for sym in syms:
        sub = df.filter(pl.col("symbol") == sym)
        pe = float(sub["net_bps"].mean()) if sub.height else float("nan")
        per_sym[sym] = round(pe, 3) if sub.height else None
        if sub.height and pe > 0:
            sym_pos += 1
    return {
        "pooled_mean_net_bps": round(m, 3) if n else None,
        "pooled_ci_lo": round(lo, 3) if n else None,
        "pooled_ci_hi": round(hi, 3) if n else None,
        "n_events": n,
        "n_sessions": ns,
        "symbols_positive_point_estimate": sym_pos,
        "per_symbol_point_estimate": per_sym,
        "meets_pooled_lo_gt_0": bool(n and lo > 0),
        "meets_n_ge_100": bool(n >= 100),
        "meets_ge_3_of_5_symbols_positive": bool(sym_pos >= 3),
    }


def build_report_md(df: pl.DataFrame, trial_id: str, stats: dict) -> str:
    """Assemble the full report.md string from a per-event results frame (pure)."""
    counts = stats["counts"]
    exit_et = EXIT_TIMES_ET[stats["exit_cell"]]
    md: list[str] = [
        f"# M6b OPENING-imbalance trial report — {trial_id}",
        "",
        "Family: open_imbalance_v1 (M3_REGISTRATION.md M6b section)",
        f"Symbols: {', '.join(stats['symbols'])}",
        f"Threshold (|norm_imb| of ADV$): {stats['threshold']}  "
        f"({stats['threshold'] * 100:.3f}% of ADV$)",
        f"Exit cell: {stats['exit_cell']}  (market-out at "
        f"{exit_et[0]:02d}:{exit_et[1]:02d}:{exit_et[2]:02d} ET + U[5,25]s latency)    "
        f"seed={stats['seed']}",
        "Signal: LAST opening-NOII at-or-before 09:28:30 ET; ENTRY = MOO at daily "
        "bar OPEN (official open = opening cross), ts 09:30:00 ET, zero spread/slip.",
        f"Sessions in range (< holdout): {stats['sessions_in_range']}",
        f"Events evaluated (rows): {df.height}",
        f"Splits present: {sorted(set(split_of(s) for s in df['session'].unique())) if df.height else []}",
        "",
        "Message window verified: opening-cross NOII disseminates 09:25-09:30 ET in "
        "the owned imbalance-schema partitions; near_price populates from ~09:28 "
        "(near->ref fallback before that). Loaded [09:00, 09:30], signal picks the "
        "last message at-or-before 09:28:30 ET (PIT).",
        "",
        "## 1. Event funnel / skipped-session counts",
        "",
        "```",
        json.dumps(counts, indent=2, default=str),
        "```",
        "",
        "## 2. Pooled + per-symbol net_bps day-clustered CIs (stress.clustered_mean_ci)",
        "",
        _ascii(_per_symbol_ci_table(df)),
        "",
        "## 3. Split-wise net_bps day-clustered CIs (train-period vs validate-period)",
        "",
        _ascii(_split_ci_table(df)),
        "",
        "## 3b. By-year net_bps day-clustered CIs",
        "",
        _ascii(_by_year_ci_table(df)),
        "",
        "## 4. Ground-truth table (10 stratified events, PROTOCOL v6.1)",
        "",
        "open_vs_bbomid_bps: official open (= MOO fill) vs the FIRST bbo-1s mid at "
        "09:30:00-09:30:05 ET; open_dev_gt_20bps flags |dev| > 20 bps. exit_in_nbbo: "
        "the market-out fill sits within the prevailing BBO at the exit instant.",
        "",
        _ascii(_stratified_ground_truth(df)),
        "",
        "## 5. Registered promotion bar (diagnostic echo, not a gate in this app)",
        "",
        "```",
        json.dumps(_promotion_diagnostic(df), indent=2, default=str),
        "```",
        "",
        "## 6. Exit-reason / side distribution",
        "",
    ]
    if df.height:
        er = (
            df.group_by(["exit_reason", "side"])
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
        )
        md.append(_ascii(er))
    else:
        md.append("(no events)")
    md.append("")
    return "\n".join(md)


def write_outputs(df: pl.DataFrame, out_dir: Path, trial_id: str, stats: dict) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.parquet"
    report_path = out_dir / "report.md"
    df.write_parquet(results_path)
    report_path.write_text(build_report_md(df, trial_id, stats), encoding="utf-8")
    return results_path, report_path


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--trial-id", required=True, help="Experiment id -> research/experiments/<id>/.")
@click.option("--symbols", default=SYMBOLS_DEFAULT, help="Comma-separated Nasdaq universe.")
@click.option("--start", required=True, help="First session (ISO date), inclusive.")
@click.option("--end", required=True, help="Last session (ISO date), inclusive; < holdout.")
@click.option(
    "--threshold",
    type=click.Choice(["0.0005", "0.001"]),
    required=True,
    help="Registered |norm_imb| cell: 0.0005 (0.05% ADV$) or 0.001 (0.10% ADV$).",
)
@click.option(
    "--exit",
    "exit_cell",
    type=click.Choice(["0945", "1000"]),
    required=True,
    help="Registered exit cell: market-out at 09:45 or 10:00 ET.",
)
@click.option("--seed", default=7, type=int, help="Latency-draw seed.")
@click.option("--noii-dir", default=None, help="NOII lake root (default data/raw/noii).")
@click.option("--bbo-dir", default=None, help="BBO-1s lake root (default data/raw/bbo1s).")
def main(
    trial_id: str,
    symbols: str,
    start: str,
    end: str,
    threshold: str,
    exit_cell: str,
    seed: int,
    noii_dir: str | None,
    bbo_dir: str | None,
) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    settings = get_settings()
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    assert_before_holdout(end_d)

    t0 = time.time()
    df, stats = run_open_trial(
        settings,
        symbols=sym_list,
        start=start_d,
        end=end_d,
        threshold=float(threshold),
        exit_cell=exit_cell,
        seed=seed,
        noii_dir=noii_dir,
        bbo_dir=bbo_dir,
    )
    wall_s = time.time() - t0

    out_dir = experiments_dir() / trial_id
    results_path, report_path = write_outputs(df, out_dir, trial_id, stats)

    click.echo(
        f"trial: {trial_id}  symbols={','.join(sym_list)}  {start}..{end}  "
        f"threshold={threshold}  exit={exit_cell}"
    )
    click.echo(f"sessions in range (< holdout): {stats['sessions_in_range']}")
    click.echo(f"event funnel: {json.dumps(stats['counts'], default=str)}")
    click.echo("")
    click.echo(_ascii(_per_symbol_ci_table(df)))
    click.echo("")
    click.echo(f"POOLED net_bps: {_fmt_ci(_ci(df))}")
    click.echo(f"events: {df.height}")
    click.echo(f"results: {results_path}")
    click.echo(f"report:  {report_path}")
    click.echo(f"wall: {wall_s:.1f}s")


if __name__ == "__main__":
    main()
