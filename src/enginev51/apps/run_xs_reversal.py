"""M7 daily cross-sectional reversal trial runner — trailing-5d-return reversal on
the 12-name bar_signal universe, MOC-to-MOC fills, net-of-cost evidence.

Drives the registered ``daily_xs_reversal_v1`` family (M3_REGISTRATION.md M7 section)
over a date range of NYSE sessions:

    at each rebalance session t (daily cell: every session; weekly cell: the last
    session of each ISO week -- Friday, or the last trading session when Friday is
    a holiday):
      signal = trailing 5-session close-to-close return, RESIDUALIZED by subtracting
        the equal-weight-universe mean of the same return (over eligible names);
      rank the eligible names by the residual;
      LONG the bottom-3, SHORT the top-3, equal $ weight ($10k research notional per
        leg-name);
      ENTRY at session t official close (MOC fill = the daily close, ambiguity-free);
      EXIT at t+1 (daily cell) / t+5 (weekly cell) official close (MOC).

A name is ELIGIBLE only once it has >= 30 trailing sessions of data (universe-entry
gating; documented per-name entry dates in the report). Net per name-trip =
side*(exit-entry)/entry*1e4 - SEC/TAF (0.3 bp on the SELL leg of the round trip:
the exit for longs, the entry for shorts). The per-REBALANCE book return is the mean
of the 6 legs. A MANDATORY borrow-stress arm subtracts 50 bps/yr, pro-rated on the
short-leg holding days, from the short legs only.

--- FILL MODEL (ambiguity-free by construction) ------------------------------
Both fills are the official closing print = the daily bar CLOSE (Nasdaq/NYSE
official close = the closing cross, a single clearing price with no queue). Entry
and exit fills therefore EQUAL the daily-bar closes exactly -- verified in the
report's ground-truth table (PROTOCOL v6.1), not merely asserted.

--- DATA CAVEAT (raw, unadjusted closes) -------------------------------------
The daily bars are ``adjustment=raw`` (matching the 5 auction names already in
``data/raw/sip/bars1d`` and the M7 registration's "official daily closes"). Raw
closes carry split discontinuities: a trailing-5d return whose window straddles a
split date is a ~split-ratio move, NOT a real return. The report flags every
split-suspect leg (|ret5| or |hold return| > 40%) and quantifies its net
contribution so the contamination is visible; it is NOT silently removed (touching
data to change results voids the trial -- PROTOCOL v6 §3). A split-adjusted rerun
is the obvious registered follow-up.

Hard PIT/holdout guard: the run refuses any ``--end`` on/after
``protocol.HOLDOUT_START``, loads only closes strictly before it, and drops any
rebalance whose EXIT session would land in the sealed holdout. Writes NO ledger
row -- the orchestrator owns verdicts.

    uv run python -m enginev51.apps.run_xs_reversal fetch          # one-time bar pull
    uv run python -m enginev51.apps.run_xs_reversal run \
        --trial-id M7-daily-xs-reversal-v1-daily --cell daily \
        --start 2020-01-01 --end 2026-05-31
"""

from __future__ import annotations

import json
import time
from datetime import UTC, date, datetime
from pathlib import Path

import click
import polars as pl
import structlog

from enginev51.backtest import stress
from enginev51.config import Settings, get_settings
from enginev51.protocol import (
    HOLDOUT_START,
    SealViolation,
    experiments_dir,
    refuse_end_on_or_after_holdout,
    split_of,
)

log = structlog.get_logger(__name__)

# --------------------------------------------------------------------------- consts

# The 12-name bar_signal universe (config/settings.toml [universe].bar_signal).
UNIVERSE: tuple[str, ...] = (
    "TSLA", "NVDA", "AMD", "MU", "AVGO", "PLTR", "COIN", "MSTR",
    "SMCI", "META", "AMZN", "GOOGL",
)
# The 5 auction names already have data/raw/sip/bars1d parquet; the other 7 are
# fetched once (fetch_bars_multi 1Day adjustment=raw), same layout.
HAVE_BARS: tuple[str, ...] = ("TSLA", "NVDA", "AMD", "MU", "GOOGL")
NEED_BARS: tuple[str, ...] = ("AVGO", "PLTR", "COIN", "MSTR", "SMCI", "META", "AMZN")

BARS1D_DIR = Path("data/raw/sip/bars1d")
FETCH_START = datetime(2019, 11, 1, tzinfo=UTC)
FETCH_END = datetime(2026, 6, 2, tzinfo=UTC)  # exclusive-ish; > last needed session

LOOKBACK = 5              # trailing sessions for the reversal signal
MIN_TRAILING = 30         # universe-entry gate: >= 30 trailing sessions
N_LEGS = 3                # long bottom-3, short top-3
NOTIONAL = 10_000.0       # research book per leg-name ($)
SEC_TAF_SELL_BPS = 0.3    # SEC/TAF on the SELL leg of each round trip
BORROW_BPS_PER_YEAR = 50.0  # HTB borrow-stress proxy, pro-rated on short holding days

HOLD_SESSIONS: dict[str, int] = {"daily": 1, "weekly": 5}

BARS1D_SCHEMA: dict[str, pl.DataType] = {
    "ts": pl.Int64,
    "open": pl.Float64,
    "high": pl.Float64,
    "low": pl.Float64,
    "close": pl.Float64,
    "volume": pl.Float64,
    "trade_count": pl.Int64,
    "vwap": pl.Float64,
}

LEG_SCHEMA: dict[str, pl.DataType] = {
    "entry_session": pl.Utf8,
    "exit_session": pl.Utf8,
    "symbol": pl.Utf8,
    "side": pl.Int64,          # +1 long (bottom-3), -1 short (top-3)
    "rank_in_session": pl.Int64,
    "resid": pl.Float64,       # residualized trailing-5d return (the signal)
    "ret5": pl.Float64,        # raw trailing-5d return
    "entry_close": pl.Float64,
    "exit_close": pl.Float64,
    "hold_days": pl.Int64,     # calendar days held (borrow accrual)
    "gross_bps": pl.Float64,
    "fee_bps": pl.Float64,
    "borrow_bps": pl.Float64,  # >= 0; nonzero only on short legs
    "net_bps": pl.Float64,     # gross - fee (primary)
    "net_bps_borrow": pl.Float64,  # net - borrow (stress arm)
    "split_suspect": pl.Boolean,
    "year": pl.Utf8,
}

REBAL_SCHEMA: dict[str, pl.DataType] = {
    "entry_session": pl.Utf8,
    "exit_session": pl.Utf8,
    "n_legs": pl.Int64,
    "n_eligible": pl.Int64,
    "book_net_bps": pl.Float64,
    "book_net_bps_borrow": pl.Float64,
    "baseline_drift_bps": pl.Float64,  # equal-weight eligible-universe long-only drift
    "year": pl.Utf8,
}


# --------------------------------------------------------------------------- guard


def assert_before_holdout(end: date) -> None:
    """Refuse any run reaching the sealed holdout boundary (PROTOCOL v6 §1).

    Raises SealViolation (never a bare assert: ``python -O`` strips those)."""
    refuse_end_on_or_after_holdout(end)


# --------------------------------------------------------------------------- fetch


def fetch_missing_bars(
    settings: Settings, symbols: list[str], *, out_dir: Path = BARS1D_DIR
) -> dict[str, int]:
    """Fetch daily bars (1Day, adjustment=raw, SIP) for `symbols` and write the
    same data/raw/sip/bars1d/{SYM}.parquet layout as the 5 auction names.

    Called ONCE. Skips symbols whose parquet already exists (idempotent/resumable).
    Returns {symbol: rows_written}. Requires Alpaca creds in the environment.
    """
    from enginev51.data.alpaca_hist import AlpacaHist

    out_dir.mkdir(parents=True, exist_ok=True)
    todo = [s for s in symbols if not (out_dir / f"{s}.parquet").exists()]
    if not todo:
        return {}
    hist = AlpacaHist(settings)
    written: dict[str, int] = {}
    try:
        # One multi-symbol pull; the client paginates internally.
        bars = hist.fetch_bars_multi(
            todo, FETCH_START, FETCH_END,
            feed="sip", timeframe="1Day", adjustment="raw",
        )
        for sym in todo:
            rows = bars.get(sym.upper(), [])
            df = (
                pl.DataFrame(rows, schema=BARS1D_SCHEMA)
                if rows
                else pl.DataFrame(schema=BARS1D_SCHEMA)
            ).sort("ts")
            df.write_parquet(out_dir / f"{sym}.parquet")
            written[sym] = df.height
    finally:
        hist.close()
    return written


# --------------------------------------------------------------------------- data


def load_closes(symbols: list[str], *, bars_dir: Path = BARS1D_DIR) -> pl.DataFrame:
    """Long frame [session, symbol, close] of official daily closes, session < holdout.

    The daily-bar ``ts`` is midnight ET (04:00/05:00 UTC), so its UTC date equals the
    session date -- the same mapping ``auction_replay._daily_closes`` uses. Rows with
    a non-positive close are dropped. Sorted by (symbol, session).
    """
    rows: list[dict] = []
    holdout_iso = HOLDOUT_START.isoformat()
    for sym in symbols:
        p = bars_dir / f"{sym}.parquet"
        if not p.exists():
            continue
        df = pl.read_parquet(p)
        for r in df.iter_rows(named=True):
            c = r.get("close")
            if c is None or float(c) <= 0.0:
                continue
            session = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
            if session >= holdout_iso:
                continue
            rows.append({"session": session, "symbol": sym, "close": float(c)})
    if not rows:
        return pl.DataFrame(schema={"session": pl.Utf8, "symbol": pl.Utf8, "close": pl.Float64})
    return pl.DataFrame(rows).sort(["symbol", "session"])


def build_signal_frame(closes: pl.DataFrame) -> pl.DataFrame:
    """Per (session, symbol): trailing-5d return, eligibility, residual, session rank.

    - ``n_hist`` = number of sessions of data for the symbol up to & including t
      (cumulative count, 1-based). Universe-entry gate: eligible iff n_hist >= 30.
    - ``ret5`` = close_t / close_{t-5} - 1 (within symbol, session-ordered).
    - eligible iff (n_hist >= MIN_TRAILING) AND (ret5 is not null).
    - ``resid`` = ret5 minus the equal-weight mean of ret5 over the ELIGIBLE names of
      that session (the residualization). NaN for ineligible rows.
    - ``rank_in_session`` = ascending dense rank of ``resid`` among eligible names
      (0 = most negative residual = the top long candidate).
    """
    if closes.height == 0:
        return closes.with_columns(
            pl.lit(None).alias(c)
            for c in ("n_hist", "ret5", "eligible", "resid", "rank_in_session")
        )
    df = closes.sort(["symbol", "session"]).with_columns(
        (pl.col("close") / pl.col("close").shift(LOOKBACK).over("symbol") - 1.0).alias("ret5"),
        (pl.col("session").cum_count().over("symbol")).alias("n_hist"),
    )
    df = df.with_columns(
        ((pl.col("n_hist") >= MIN_TRAILING) & pl.col("ret5").is_not_null()).alias("eligible")
    )
    # session mean of ret5 over eligible names only
    sess_mean = (
        df.filter("eligible")
        .group_by("session")
        .agg(pl.col("ret5").mean().alias("_sess_mean_ret5"))
    )
    df = df.join(sess_mean, on="session", how="left").with_columns(
        pl.when(pl.col("eligible"))
        .then(pl.col("ret5") - pl.col("_sess_mean_ret5"))
        .otherwise(None)
        .alias("resid")
    )
    # ascending rank of resid within session among eligible rows
    df = df.with_columns(
        pl.when(pl.col("eligible"))
        .then(pl.col("resid").rank("ordinal").over("session").cast(pl.Int64) - 1)
        .otherwise(None)
        .alias("rank_in_session")
    )
    return df.drop("_sess_mean_ret5")


# --------------------------------------------------------------------------- schedule


def rebalance_sessions(sessions: list[str], cell: str) -> list[str]:
    """The entry sessions for a cell, from an ascending list of trading sessions.

    daily  -> every session.
    weekly -> the LAST session of each ISO (year, week) group = Friday, or the last
              trading session of the week when Friday is a holiday.
    """
    if cell == "daily":
        return list(sessions)
    if cell != "weekly":
        raise ValueError(f"cell must be 'daily' or 'weekly', got {cell!r}")
    last_by_week: dict[tuple[int, int], str] = {}
    for s in sessions:
        y, w, _ = date.fromisoformat(s).isocalendar()
        # sessions ascending, so the last write per week wins (the week's last session)
        last_by_week[(y, w)] = s
    return sorted(last_by_week.values())


# --------------------------------------------------------------------------- legs


def _hold_calendar_days(entry_session: str, exit_session: str) -> int:
    return (date.fromisoformat(exit_session) - date.fromisoformat(entry_session)).days


def compute_leg(
    entry_session: str,
    exit_session: str,
    symbol: str,
    side: int,
    rank_in_session: int,
    resid: float,
    ret5: float,
    entry_close: float,
    exit_close: float,
) -> dict:
    """One name-trip -> net-bps decomposition (MOC entry & exit == daily closes).

    gross_bps = side*(exit-entry)/entry*1e4.
    fee_bps   = SEC/TAF 0.3 bp on the SELL leg dollar value, expressed in bps of the
                $10k entry notional:
                  long  -> sell at EXIT : 0.3 * (exit/entry)
                  short -> sell at ENTRY: 0.3
    borrow_bps (short only) = 50 bps/yr * hold_calendar_days / 365.
    net_bps        = gross - fee ; net_bps_borrow = net - borrow.
    split_suspect flags |ret5| or |hold return| > 40% (a raw-price split artefact).
    """
    hold_days = _hold_calendar_days(entry_session, exit_session)
    hold_ret = (exit_close - entry_close) / entry_close
    gross_bps = side * hold_ret * 1e4
    if side == 1:
        fee_bps = SEC_TAF_SELL_BPS * (exit_close / entry_close)
        borrow_bps = 0.0
    else:
        fee_bps = SEC_TAF_SELL_BPS
        borrow_bps = BORROW_BPS_PER_YEAR * hold_days / 365.0
    net_bps = gross_bps - fee_bps
    net_bps_borrow = net_bps - borrow_bps
    split_suspect = (abs(ret5) > 0.40) or (abs(hold_ret) > 0.40)
    return {
        "entry_session": entry_session,
        "exit_session": exit_session,
        "symbol": symbol,
        "side": int(side),
        "rank_in_session": int(rank_in_session),
        "resid": float(resid),
        "ret5": float(ret5),
        "entry_close": float(entry_close),
        "exit_close": float(exit_close),
        "hold_days": int(hold_days),
        "gross_bps": float(gross_bps),
        "fee_bps": float(fee_bps),
        "borrow_bps": float(borrow_bps),
        "net_bps": float(net_bps),
        "net_bps_borrow": float(net_bps_borrow),
        "split_suspect": bool(split_suspect),
        "year": entry_session[:4],
    }


# --------------------------------------------------------------------------- run


def run_xs_reversal(
    *,
    symbols: list[str],
    start: date,
    end: date,
    cell: str,
    bars_dir: Path = BARS1D_DIR,
) -> tuple[pl.DataFrame, pl.DataFrame, dict]:
    """Execute one M7 cell over [start, end] sessions; return (legs, rebalances, stats)."""
    assert_before_holdout(end)
    hold_n = HOLD_SESSIONS[cell]
    symbols = [s.strip().upper() for s in symbols]

    closes = load_closes(symbols, bars_dir=bars_dir)
    start_iso, end_iso = start.isoformat(), end.isoformat()
    sig = build_signal_frame(closes)

    # master ascending session ordering (all names share the NYSE calendar)
    all_sessions = sorted(closes["session"].unique().to_list())
    sess_index = {s: i for i, s in enumerate(all_sessions)}

    # entry-close and exit-close lookup: (session, symbol) -> close
    close_lu: dict[tuple[str, str], float] = {
        (r["session"], r["symbol"]): r["close"] for r in closes.iter_rows(named=True)
    }
    # eligible signal rows keyed by session -> list of dicts
    elig = sig.filter("eligible")
    by_session: dict[str, list[dict]] = {}
    for r in elig.iter_rows(named=True):
        by_session.setdefault(r["session"], []).append(r)

    entry_candidates = [
        s for s in rebalance_sessions(all_sessions, cell) if start_iso <= s <= end_iso
    ]

    counts = {
        "entry_candidates": len(entry_candidates),
        "too_few_eligible": 0,
        "no_exit_session_in_range": 0,
        "rebalances": 0,
    }

    leg_rows: list[dict] = []
    rebal_rows: list[dict] = []
    prev_names: set[str] | None = None
    turnovers: list[float] = []

    for es in entry_candidates:
        cands = by_session.get(es, [])
        if len(cands) < 2 * N_LEGS:
            counts["too_few_eligible"] += 1
            continue
        ei = sess_index[es]
        xi = ei + hold_n
        if xi >= len(all_sessions):
            counts["no_exit_session_in_range"] += 1
            continue
        exit_session = all_sessions[xi]
        # Invariant: all_sessions is holdout-stripped in load_closes, so any entry
        # whose exit would land in the sealed holdout has already fallen into the
        # no_exit_session_in_range branch above. Raise it as defense-in-depth
        # (a raise, not an assert: ``python -O`` strips asserts).
        if exit_session >= HOLDOUT_START.isoformat():
            raise SealViolation(
                f"exit session {exit_session} is in the sealed holdout "
                f"{HOLDOUT_START.isoformat()} (PROTOCOL v6 §1)"
            )

        ordered = sorted(cands, key=lambda d: d["rank_in_session"])
        longs = ordered[:N_LEGS]              # most-negative residual
        shorts = ordered[-N_LEGS:]            # most-positive residual

        # eligible-universe long-only drift baseline (equal weight, same horizon)
        drift_terms: list[float] = []
        for r in cands:
            ec = close_lu.get((es, r["symbol"]))
            xc = close_lu.get((exit_session, r["symbol"]))
            if ec and xc:
                drift_terms.append((xc - ec) / ec * 1e4)
        baseline_drift = sum(drift_terms) / len(drift_terms) if drift_terms else float("nan")

        picks = [(r, 1) for r in longs] + [(r, -1) for r in shorts]
        legs_here: list[dict] = []
        ok = True
        for r, side in picks:
            ec = close_lu.get((es, r["symbol"]))
            xc = close_lu.get((exit_session, r["symbol"]))
            if not ec or not xc:
                ok = False
                break
            legs_here.append(
                compute_leg(
                    es, exit_session, r["symbol"], side,
                    r["rank_in_session"], r["resid"], r["ret5"], ec, xc,
                )
            )
        if not ok or len(legs_here) != 2 * N_LEGS:
            counts["no_exit_session_in_range"] += 1
            continue

        leg_rows.extend(legs_here)
        book_net = sum(lg["net_bps"] for lg in legs_here) / len(legs_here)
        book_net_borrow = sum(lg["net_bps_borrow"] for lg in legs_here) / len(legs_here)
        rebal_rows.append(
            {
                "entry_session": es,
                "exit_session": exit_session,
                "n_legs": len(legs_here),
                "n_eligible": len(cands),
                "book_net_bps": book_net,
                "book_net_bps_borrow": book_net_borrow,
                "baseline_drift_bps": baseline_drift,
                "year": es[:4],
            }
        )
        counts["rebalances"] += 1

        names = {lg["symbol"] for lg in legs_here}
        if prev_names is not None:
            turnovers.append(len(names - prev_names) / len(names))
        prev_names = names

    legs = (
        pl.DataFrame(leg_rows, schema=LEG_SCHEMA, orient="row")
        if leg_rows
        else pl.DataFrame(schema=LEG_SCHEMA)
    )
    rebalances = (
        pl.DataFrame(rebal_rows, schema=REBAL_SCHEMA, orient="row")
        if rebal_rows
        else pl.DataFrame(schema=REBAL_SCHEMA)
    )

    # per-name entry dates (first session the name reaches MIN_TRAILING sessions)
    entry_dates: dict[str, str | None] = {}
    for sym in symbols:
        sub = sig.filter((pl.col("symbol") == sym) & pl.col("eligible")).sort("session")
        entry_dates[sym] = sub["session"][0] if sub.height else None

    stats = {
        "cell": cell,
        "hold_sessions": hold_n,
        "symbols": symbols,
        "start": start_iso,
        "end": end_iso,
        "sessions_with_data": len(all_sessions),
        "universe_entry_dates": entry_dates,
        "counts": counts,
        "avg_name_turnover": (sum(turnovers) / len(turnovers)) if turnovers else float("nan"),
    }
    return legs, rebalances, stats


# --------------------------------------------------------------------------- report


def _ascii(df: pl.DataFrame) -> str:
    with pl.Config(
        tbl_formatting="ASCII_MARKDOWN",
        tbl_hide_dataframe_shape=True,
        tbl_hide_column_data_types=True,
        tbl_rows=400,
        tbl_cols=-1,
        tbl_width_chars=240,
    ):
        return str(df)


def _ci(values, clusters) -> tuple[float, float, float, int]:
    """(mean, lo, hi, n) day-clustered over `values`, clustered on `clusters`."""
    import numpy as np

    v = np.asarray(values, dtype=float)
    if v.shape[0] == 0:
        return float("nan"), float("nan"), float("nan"), 0
    m, lo, hi = stress.clustered_mean_ci(v, np.asarray(clusters))
    return m, lo, hi, v.shape[0]


def _rebalance_ci(rebal: pl.DataFrame, col: str) -> tuple[float, float, float, int]:
    if rebal.height == 0:
        return float("nan"), float("nan"), float("nan"), 0
    return _ci(rebal[col].to_numpy(), rebal["entry_session"].to_numpy())


def _fmt_ci(t: tuple[float, float, float, int]) -> str:
    m, lo, hi, n = t
    if n == 0:
        return "n=0"
    return f"mean={m:.3f}  95%CI=[{lo:.3f}, {hi:.3f}]  n_rebalances={n}"


def _by_year_table(rebal: pl.DataFrame) -> pl.DataFrame:
    years = [str(y) for y in range(2020, 2027)]
    rows: list[dict] = []
    for y in years:
        sub = rebal.filter(pl.col("year") == y) if rebal.height else rebal
        m, lo, hi, n = _rebalance_ci(sub, "book_net_bps")
        mb, lob, hib, _ = _rebalance_ci(sub, "book_net_bps_borrow")
        rows.append(
            {
                "year": y,
                "n_rebalances": n,
                "book_net_mean": round(m, 3) if n else None,
                "ci_lo": round(lo, 3) if n else None,
                "ci_hi": round(hi, 3) if n else None,
                "positive_point": bool(n and m > 0),
                "borrow_net_mean": round(mb, 3) if n else None,
                "borrow_positive": bool(n and mb > 0),
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            "year": pl.Utf8, "n_rebalances": pl.Int64,
            "book_net_mean": pl.Float64, "ci_lo": pl.Float64, "ci_hi": pl.Float64,
            "positive_point": pl.Boolean,
            "borrow_net_mean": pl.Float64, "borrow_positive": pl.Boolean,
        },
        orient="row",
    )


def _per_name_table(legs: pl.DataFrame) -> pl.DataFrame:
    if legs.height == 0:
        return pl.DataFrame(
            schema={
                "symbol": pl.Utf8, "n_trips": pl.Int64, "n_long": pl.Int64, "n_short": pl.Int64,
                "net_bps_mean": pl.Float64, "net_bps_sum": pl.Float64,
                "long_net_mean": pl.Float64, "short_net_mean": pl.Float64,
            }
        )
    agg = (
        legs.group_by("symbol")
        .agg(
            pl.len().alias("n_trips"),
            (pl.col("side") == 1).sum().alias("n_long"),
            (pl.col("side") == -1).sum().alias("n_short"),
            pl.col("net_bps").mean().alias("net_bps_mean"),
            pl.col("net_bps").sum().alias("net_bps_sum"),
            pl.col("net_bps").filter(pl.col("side") == 1).mean().alias("long_net_mean"),
            pl.col("net_bps").filter(pl.col("side") == -1).mean().alias("short_net_mean"),
        )
        .sort("net_bps_sum", descending=True)
    )
    return agg.with_columns(pl.col(pl.Float64).round(3))


def _ground_truth_table(legs: pl.DataFrame, closes: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """<=k stratified leg-trips vs the raw daily bars: verify entry/exit fills EQUAL
    the daily closes exactly (fill-ambiguity-free, by construction) -- PROTOCOL v6.1.
    Strata: biggest winners, biggest losers, largest |resid| (signal extremes)."""
    schema = {
        "entry_session": pl.Utf8, "exit_session": pl.Utf8, "symbol": pl.Utf8,
        "side": pl.Int64, "resid": pl.Float64,
        "entry_close": pl.Float64, "bar_entry_close": pl.Float64, "entry_match": pl.Boolean,
        "exit_close": pl.Float64, "bar_exit_close": pl.Float64, "exit_match": pl.Boolean,
        "net_bps": pl.Float64, "split_suspect": pl.Boolean,
    }
    if legs.height == 0:
        return pl.DataFrame(schema=schema)
    bar_lu: dict[tuple[str, str], float] = {
        (r["session"], r["symbol"]): r["close"] for r in closes.iter_rows(named=True)
    }
    d = legs.with_columns(pl.arange(0, pl.len()).alias("_idx"))
    winners = d.sort("net_bps", descending=True).head(3)["_idx"].to_list()
    losers = d.sort("net_bps", descending=False).head(3)["_idx"].to_list()
    extremes = d.sort(pl.col("resid").abs(), descending=True).head(4)["_idx"].to_list()
    picked: list[int] = []
    for i in [*winners, *losers, *extremes]:
        if i not in picked:
            picked.append(i)
        if len(picked) >= k:
            break
    sub = d.filter(pl.col("_idx").is_in(picked)).drop("_idx")
    rows: list[dict] = []
    for r in sub.iter_rows(named=True):
        be = bar_lu.get((r["entry_session"], r["symbol"]))
        bx = bar_lu.get((r["exit_session"], r["symbol"]))
        rows.append(
            {
                "entry_session": r["entry_session"], "exit_session": r["exit_session"],
                "symbol": r["symbol"], "side": r["side"], "resid": round(r["resid"], 5),
                "entry_close": r["entry_close"], "bar_entry_close": be,
                "entry_match": be is not None and abs(be - r["entry_close"]) < 1e-9,
                "exit_close": r["exit_close"], "bar_exit_close": bx,
                "exit_match": bx is not None and abs(bx - r["exit_close"]) < 1e-9,
                "net_bps": round(r["net_bps"], 3), "split_suspect": r["split_suspect"],
            }
        )
    return pl.DataFrame(rows, schema=schema, orient="row")


def _split_diagnostic(legs: pl.DataFrame) -> dict:
    if legs.height == 0:
        return {"n_legs": 0, "n_split_suspect": 0}
    susp = legs.filter("split_suspect")
    return {
        "n_legs": legs.height,
        "n_split_suspect": susp.height,
        "split_suspect_pct": round(100.0 * susp.height / legs.height, 2),
        "split_suspect_net_bps_mean": round(float(susp["net_bps"].mean()), 3) if susp.height else None,
        "clean_net_bps_mean": round(float(legs.filter(~pl.col("split_suspect"))["net_bps"].mean()), 3),
        "note": (
            "Raw (unadjusted) closes: a leg is split-suspect when |trailing-5d return| "
            "or |holding return| exceeds 40% -- almost certainly a split discontinuity, "
            "not a real move. Reported, not removed (removing would void the trial)."
        ),
    }


def _promotion_diagnostic(rebal: pl.DataFrame) -> dict:
    """Registered M7 bar (diagnostic echo, NOT a gate here): pooled per-rebalance
    day-clustered CI lower > 0 AND positive in >=4 of 7 years AND survives the
    borrow-stress arm (borrow-net pooled CI lower > 0)."""
    m, lo, hi, n = _rebalance_ci(rebal, "book_net_bps")
    mb, lob, hib, _ = _rebalance_ci(rebal, "book_net_bps_borrow")
    yt = _by_year_table(rebal)
    years_present = yt.filter(pl.col("n_rebalances") > 0)
    years_positive = int(years_present.filter("positive_point").height)
    return {
        "pooled_book_net_mean": round(m, 3) if n else None,
        "pooled_ci_lo": round(lo, 3) if n else None,
        "pooled_ci_hi": round(hi, 3) if n else None,
        "n_rebalances": n,
        "borrow_stress_mean": round(mb, 3) if n else None,
        "borrow_stress_ci_lo": round(lob, 3) if n else None,
        "years_with_data": int(years_present.height),
        "years_positive_point": years_positive,
        "meets_pooled_lo_gt_0": bool(n and lo > 0),
        "meets_ge_4_of_7_years_positive": bool(years_positive >= 4),
        "meets_borrow_stress_lo_gt_0": bool(n and lob > 0),
    }


def build_report_md(
    legs: pl.DataFrame, rebal: pl.DataFrame, closes: pl.DataFrame, trial_id: str, stats: dict
) -> str:
    counts = stats["counts"]
    entry_dates = stats["universe_entry_dates"]
    ed_rows = [
        {"symbol": s, "entry_date": entry_dates.get(s), "split": split_of(entry_dates[s]) if entry_dates.get(s) else None}
        for s in stats["symbols"]
    ]
    ed_df = pl.DataFrame(
        ed_rows, schema={"symbol": pl.Utf8, "entry_date": pl.Utf8, "split": pl.Utf8}, orient="row"
    )
    base = _rebalance_ci(rebal, "book_net_bps")
    borrow = _rebalance_ci(rebal, "book_net_bps_borrow")
    drift = _rebalance_ci(rebal, "baseline_drift_bps")

    md: list[str] = [
        f"# M7 daily cross-sectional reversal report -- {trial_id}",
        "",
        "Family: daily_xs_reversal_v1 (M3_REGISTRATION.md M7 section). Research-only "
        "(the deployable system never holds overnight; deployment would need the "
        "overnight constraint amended by the user).",
        f"Cell: {stats['cell']}  (hold = {stats['hold_sessions']} session(s), MOC->MOC)",
        f"Universe (12): {', '.join(stats['symbols'])}",
        f"Signal: trailing 5-session close-to-close return, residualized vs the "
        f"equal-weight eligible-universe mean; LONG bottom-3, SHORT top-3, ${NOTIONAL:,.0f}/leg.",
        f"Costs: zero commission + SEC/TAF {SEC_TAF_SELL_BPS} bp on the SELL leg. "
        f"Borrow-stress arm: {BORROW_BPS_PER_YEAR:.0f} bps/yr pro-rated on short-leg calendar days.",
        f"Universe-entry gate: a name trades only once it has >= {MIN_TRAILING} trailing sessions.",
        f"Range: {stats['start']} .. {stats['end']}  (sessions with data < holdout: {stats['sessions_with_data']})",
        f"Splits present: {sorted({split_of(s) for s in rebal['entry_session'].unique()}) if rebal.height else []}",
        "",
        "Fills are the official closing print = the daily-bar CLOSE (closing cross = a "
        "single clearing price, no queue). Entry and exit fills EQUAL the daily closes "
        "exactly, by construction -- verified in section 7 (PROTOCOL v6.1).",
        "",
        "## 0. Universe-entry dates (first session with >= 30 trailing sessions)",
        "",
        _ascii(ed_df),
        "",
        "## 1. Rebalance funnel",
        "",
        "```",
        json.dumps(counts, indent=2, default=str),
        "```",
        "",
        "## 2. Pooled per-rebalance net CI (day-clustered on entry session)",
        "",
        f"BASE (net of SEC/TAF):        {_fmt_ci(base)}",
        f"BORROW-STRESS (−50bps/yr HTB): {_fmt_ci(borrow)}",
        "",
        f"Long-only eligible-universe drift baseline (context only): {_fmt_ci(drift)}",
        f"Average per-rebalance name turnover: {stats['avg_name_turnover']:.3f}"
        if stats["avg_name_turnover"] == stats["avg_name_turnover"] else
        "Average per-rebalance name turnover: n/a",
        "",
        "## 3. Per-year table (>=4/7-year prong)",
        "",
        _ascii(_by_year_table(rebal)),
        "",
        "## 4. Per-name contribution (leg-trips)",
        "",
        _ascii(_per_name_table(legs)),
        "",
        "## 5. Borrow-stress arm (mandatory)",
        "",
        f"Pooled BASE:          {_fmt_ci(base)}",
        f"Pooled BORROW-STRESS: {_fmt_ci(borrow)}",
        "Per-year borrow columns are in section 3 (borrow_net_mean / borrow_positive).",
        "",
        "## 6. Split-contamination diagnostic (raw-close caveat)",
        "",
        "```",
        json.dumps(_split_diagnostic(legs), indent=2, default=str),
        "```",
        "",
        "## 7. Ground-truth: 10 stratified leg-trips vs the raw daily bars (PROTOCOL v6.1)",
        "",
        "entry_match / exit_match: the MOC fill EQUALS the daily-bar close exactly. "
        "By construction the fills ARE the closes, so every row must match -- this "
        "table verifies that identity holds on sampled winners/losers/signal-extremes.",
        "",
        _ascii(_ground_truth_table(legs, closes)),
        "",
        "## 8. Registered promotion bar (diagnostic echo, not a gate in this app)",
        "",
        "```",
        json.dumps(_promotion_diagnostic(rebal), indent=2, default=str),
        "```",
        "",
    ]
    return "\n".join(md)


def write_outputs(
    legs: pl.DataFrame, rebal: pl.DataFrame, closes: pl.DataFrame,
    out_dir: Path, trial_id: str, stats: dict,
) -> tuple[Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    legs_path = out_dir / "legs.parquet"
    rebal_path = out_dir / "rebalances.parquet"
    report_path = out_dir / "report.md"
    legs.write_parquet(legs_path)
    rebal.write_parquet(rebal_path)
    report_path.write_text(build_report_md(legs, rebal, closes, trial_id, stats), encoding="utf-8")
    return legs_path, rebal_path, report_path


# --------------------------------------------------------------------------- cli


@click.group()
def cli() -> None:
    """M7 daily cross-sectional reversal (daily_xs_reversal_v1)."""


@cli.command("fetch")
@click.option("--symbols", default=",".join(NEED_BARS), help="Names to fetch daily bars for.")
def fetch_cmd(symbols: str) -> None:
    """One-time daily-bar pull (1Day, adjustment=raw, SIP) for the 7 new names."""
    settings = get_settings()
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    written = fetch_missing_bars(settings, sym_list)
    if not written:
        click.echo("nothing to fetch (all parquets already present).")
        return
    for sym, n in written.items():
        click.echo(f"{sym:<8}{n:>6} daily bars -> {BARS1D_DIR / (sym + '.parquet')}")


@cli.command("run")
@click.option("--trial-id", required=True, help="Experiment id -> research/experiments/<id>/.")
@click.option("--cell", type=click.Choice(["daily", "weekly"]), required=True)
@click.option("--symbols", default=",".join(UNIVERSE), help="Comma-separated 12-name universe.")
@click.option("--start", required=True, help="First entry session (ISO date), inclusive.")
@click.option("--end", required=True, help="Last entry session (ISO date), inclusive; < holdout.")
def run_cmd(trial_id: str, cell: str, symbols: str, start: str, end: str) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    assert_before_holdout(end_d)

    missing = [s for s in sym_list if not (BARS1D_DIR / f"{s}.parquet").exists()]
    if missing:
        raise click.ClickException(
            f"missing daily bars for {missing}; run `... run_xs_reversal fetch` first."
        )

    t0 = time.time()
    legs, rebal, stats = run_xs_reversal(
        symbols=sym_list, start=start_d, end=end_d, cell=cell
    )
    closes = load_closes(sym_list)
    wall_s = time.time() - t0

    out_dir = experiments_dir() / trial_id
    legs_path, rebal_path, report_path = write_outputs(
        legs, rebal, closes, out_dir, trial_id, stats
    )

    base = _rebalance_ci(rebal, "book_net_bps")
    borrow = _rebalance_ci(rebal, "book_net_bps_borrow")
    click.echo(f"trial: {trial_id}  cell={cell}  {start}..{end}")
    click.echo(f"rebalance funnel: {json.dumps(stats['counts'], default=str)}")
    click.echo(f"universe entry dates: {json.dumps(stats['universe_entry_dates'], default=str)}")
    click.echo("")
    click.echo(f"POOLED book net (base):    {_fmt_ci(base)}")
    click.echo(f"POOLED book net (borrow):  {_fmt_ci(borrow)}")
    click.echo("")
    click.echo(_ascii(_by_year_table(rebal)))
    click.echo("")
    click.echo(f"legs:       {legs_path}")
    click.echo(f"rebalances: {rebal_path}")
    click.echo(f"report:     {report_path}")
    click.echo(f"wall: {wall_s:.1f}s")


if __name__ == "__main__":
    cli()
