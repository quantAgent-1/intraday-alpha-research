"""Dedicated MOC (market-on-close) auction evaluator for the M6
``moc_imbalance_v1`` family — the fill-ambiguity-free replayer.

The registered mechanism (M3_REGISTRATION.md, M6): enter WITH the published
closing-cross imbalance via an honest taker market order (the existing NBBO fill
kernel, latency + slip), then exit AT the official Nasdaq closing-cross print.
The closing auction is the one regime where limit-fill modeling ambiguity
vanishes — a single clearing price, no queue — so the exit is priced exactly at
the cross with zero spread/slip by construction.

This module is deliberately SEPARATE from ``backtest/replay.py`` (which the task
forbids touching): that replayer models resting-limit queue ambiguity and a
15:50 curfew; the MOC family is curfew-EXEMPT (an auction fill IS flat-by-close)
and needs neither the k-slot admission nor the limit-fill machinery. It reuses
the shared primitives instead — ``backtest/fills`` (market_fill / prevailing_mid),
``backtest/latency`` (seeded U[5,25]s draws), ``backtest/decompose`` (plan_pnl).

Registered data-source extension (ledger M6, 2026-07-16): ``tape_from_bbo`` builds
a ``SessionTape`` from a 1-second BBO frame (``data/bbo1s.load_bbo_session``)
instead of the tick quote/trade tape. The entry semantics are IDENTICAL — a taker
market order crossing the prevailing BBO at signal+latency plus slip — the only
difference is that the prevailing quote is sampled at 1-second granularity rather
than at every tick. That is a COARSER but UNBIASED prevailing quote: each 1s row
is the real last BBO as of that second boundary, not an interpolation, so the
market_fill lookup at signal+latency is honest; it merely rounds the fill instant's
quote to its ≤1s-stale predecessor. NOTE (code review 2026-07-17 F5): that BBO is
the XNAS.ITCH venue top-of-book, NOT the consolidated SIP NBBO the tick tape
carries — close on Nasdaq megacaps but a different economic object; keep
XNAS-entry and SIP-entry nets labeled apart (see ``data/bbo1s.py``). Trades are unused on this path (entry is
quote-only, exit is the official cross), so ``tape_from_bbo`` leaves ``t_ts`` /
``t_price`` empty and ``t_size`` None. The 1s BBO extends fill coverage over the
full 2020→2026 span where the tick tape is absent.

Three public entry points:
  * ``find_closing_cross`` — pick the official cross print off our condition-coded
    tape (the SessionTape used for entry has these prints STRIPPED, so the cross
    is found on the RAW trades frame).
  * ``adv20_dollars`` — trailing-20-session dollar ADV from the bars store, PIT.
  * ``replay_moc_event`` — one event: taker entry + auction (or persistence) exit,
    decomposed to net bps price-to-price minus SEC/TAF on the sell leg.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from datetime import UTC, date, timedelta
from pathlib import Path as _Path

import numpy as np
import polars as pl

from enginev51.backtest import fills as fk
from enginev51.backtest import latency as lat
from enginev51.backtest.decompose import PlanPnl, plan_pnl
from enginev51.backtest.replay import SessionTape
from enginev51.config import Settings
from enginev51.data import store
from enginev51.data.noii import ET, et_ns

NS_PER_S = 1_000_000_000

# Official closing-cross print condition codes on our condition-coded SIP tape:
#   "6" — Closing Prints (the Nasdaq closing cross print)
#   "M" — Market Center Official Close
# (Both are among the cross/official codes the fill tape STRIPS in
# backtest/tape.py, which is exactly why the cross must be recovered from the raw
# trades here.) Window: 15:59:55–16:00:30 ET — the cross prints just after 16:00
# but late-reported/out-of-sequence copies can land seconds later; taking the
# LARGEST such print in the window is the cross itself (the auction is by far the
# biggest single print of the day; odd late "M" dupes are smaller).
CROSS_CONDITIONS = ("6", "M")
CROSS_WINDOW_START_ET = (15, 59, 55)
CROSS_WINDOW_END_ET = (16, 0, 30)


# --------------------------------------------------------------------------- cross


def _tod_seconds(ts_col: str) -> pl.Expr:
    """ET wall-clock seconds-of-day for a UTC-ns ``ts`` column.

    hour/minute/second come back as Int8 in polars; cast to Int32 BEFORE scaling
    so ``hour * 3600`` (up to 86_399) cannot overflow the narrow integer type.
    """
    et = pl.from_epoch(pl.col(ts_col), time_unit="ns").dt.convert_time_zone(str(ET))
    return (
        et.dt.hour().cast(pl.Int32) * 3600
        + et.dt.minute().cast(pl.Int32) * 60
        + et.dt.second().cast(pl.Int32)
    )


def find_closing_cross(trades_df: pl.DataFrame | None) -> tuple[int, float, float] | None:
    """The official Nasdaq closing cross print, or ``None``.

    RULE: among trades in the 15:59:55–16:00:30 ET window whose condition string
    contains "6" (Closing Prints) or "M" (Market Center Official Close), return
    the LARGEST by size as ``(ts, price, size)``. The closing cross is the single
    largest print of the session, so max-size disambiguates it from a smaller
    late-reported "M" duplicate in the same window.

    Returns ``None`` when the frame is missing, carries no ``conditions`` column,
    or has no qualifying print — the legacy tick exports were stripped of
    condition codes, so those sessions cannot be MOC-evaluated and MUST be skipped
    and counted (until the conditioned re-download completes; the NVDA/TSLA legacy
    days are the known-affected set).
    """
    if trades_df is None or trades_df.height == 0:
        return None
    if "conditions" not in trades_df.columns or "size" not in trades_df.columns:
        return None
    lo = CROSS_WINDOW_START_ET[0] * 3600 + CROSS_WINDOW_START_ET[1] * 60 + CROSS_WINDOW_START_ET[2]
    hi = CROSS_WINDOW_END_ET[0] * 3600 + CROSS_WINDOW_END_ET[1] * 60 + CROSS_WINDOW_END_ET[2]
    tod = _tod_seconds("ts")
    cand = trades_df.filter(
        (tod >= lo)
        & (tod <= hi)
        & pl.col("conditions").fill_null("").str.contains_any(list(CROSS_CONDITIONS))
        & (pl.col("price") > 0.0)
    )
    if cand.height == 0:
        return None
    # Largest print wins; break ties by the later ts (the settled cross print).
    row = cand.sort(["size", "ts"], descending=[True, True]).row(0, named=True)
    return int(row["ts"]), float(row["price"]), float(row["size"])


def load_raw_trades(
    settings: Settings, symbol: str, session_iso: str
) -> pl.DataFrame | None:
    """The RAW (unfiltered, condition-carrying) trades partition for one session.

    Unlike ``backtest/tape.load_session_tape`` (which strips cross/official prints
    for the FILL tape), this keeps every column so ``find_closing_cross`` can see
    the "6"/"M" auction prints. Reads across ``settings.read_roots`` (primary lake
    first). ``None`` if the partition is absent.
    """
    feed = settings.data_feed_type
    for root in settings.read_roots:
        p = store.partition_path(root, feed, "trades", symbol, session_iso)
        if p.exists():
            return pl.read_parquet(p)
    return None


# --------------------------------------------------------------------------- ADV20


def _adv20_from_daily(symbol: str, session_iso: str, lookback: int = 20) -> float | None:
    """Trailing dollar ADV from DAILY bars, strictly before ``session_iso`` (PIT)."""
    from pathlib import Path as _P

    p = _P("data/raw/sip/bars1d") / f"{symbol.upper()}.parquet"
    if not p.exists():
        return None
    df = pl.read_parquet(p).sort("ts")
    df = df.with_columns(
        pl.from_epoch(pl.col("ts"), time_unit="ns").dt.date().cast(pl.Utf8).alias("d"),
        (pl.coalesce(pl.col("vwap"), pl.col("close")) * pl.col("volume")).alias("dollar"),
    ).filter(pl.col("d") < session_iso)
    if df.height == 0:
        return None
    mean = float(df.tail(lookback)["dollar"].mean())
    return mean if mean > 0.0 else None


def adv20_dollars(
    settings: Settings, symbol: str, session_iso: str, *, lookback: int = 20
) -> float | None:
    """Trailing-``lookback``-session dollar ADV, strictly before ``session_iso`` (PIT).

    Per-session dollar volume is ``sum(vwap * volume)`` over the 1-minute bars of
    that ET session (falling back to ``close * volume`` where ``vwap`` is null),
    averaged over the last ``lookback`` sessions that END before the target
    session's midnight-ET (so nothing from the event day itself leaks in).

    Returns ``None`` when no prior bars exist. Uses whatever prior sessions are
    available (up to ``lookback``); with fewer than ``lookback`` it averages what
    is present — callers may treat a thin history as they see fit.
    """
    target = date.fromisoformat(session_iso)
    feed = settings.data_feed_type
    end_ns = et_ns(session_iso, 0, 0, 0)  # midnight ET of the event day (exclusive upper)
    start_ns = et_ns((target - timedelta(days=90)).isoformat(), 0, 0, 0)
    bars = store.load_bars(settings.read_roots, feed, symbol, start_ns, end_ns)
    if bars.height == 0:
        # Coverage extension (ledger 2026-07-17): minute bars start 2023-07, so
        # 2020-2023 NOII events had no ADV and never fired. Fall back to DAILY
        # bars (data/raw/sip/bars1d, 2019-11+) ONLY when minute bars are absent —
        # events evaluated under the minute-bar ADV keep their exact numbers.
        return _adv20_from_daily(symbol, session_iso, lookback)
    per_session = (
        bars.with_columns(
            pl.from_epoch(pl.col("ts"), time_unit="ns")
            .dt.convert_time_zone(str(ET))
            .dt.date()
            .alias("session"),
            (pl.coalesce(pl.col("vwap"), pl.col("close")) * pl.col("volume")).alias("dollar"),
        )
        .group_by("session")
        .agg(pl.col("dollar").sum().alias("dollar_vol"))
        .sort("session")
    )
    if per_session.height == 0:
        return None
    tail = per_session.tail(lookback)
    mean = float(tail["dollar_vol"].mean())
    if not mean > 0.0:
        return None
    return mean


# --------------------------------------------------------------------------- event


@dataclass(slots=True, frozen=True)
class MocResult:
    plan_id: str
    symbol: str
    side: int
    status: str  # "ok" | "void"
    entry_ts: int | None
    entry_px: float | None
    exit_ts: int | None
    exit_px: float | None
    exit_reason: str | None  # "moc" | "persistence"
    net_bps: float | None
    hold_s: float | None
    entry_mid: float | None  # prevailing mid at the signal instant (ground-truth context)
    pnl: PlanPnl | None


def tape_from_bbo(symbol: str, bbo_frame: pl.DataFrame) -> SessionTape:
    """Build a quote-only ``SessionTape`` from a 1-second BBO frame.

    ``bbo_frame`` is a ``data/bbo1s.BBO_SCHEMA`` frame (columns ``ts``/``bid``/
    ``ask``/``bid_size``/``ask_size``) as returned by ``load_bbo_session`` — already
    sane-filtered (bid>0 & ask>bid) and ts-sorted, but this re-applies both so a
    hand-built frame is safe too.

    The MOC event replay uses only quotes for entry (``market_fill``: cross the
    prevailing BBO at signal+latency + slip) and the official cross price for exit,
    so the trade arrays are intentionally EMPTY (``t_ts``/``t_price`` size-0,
    ``t_size`` None). Entry semantics are identical to the tick tape; the BBO is a
    1s-granular — coarser but unbiased — prevailing quote (see module docstring;
    registered data-source extension, ledger M6 2026-07-16).
    """
    df = bbo_frame.filter((pl.col("bid") > 0.0) & (pl.col("ask") > pl.col("bid"))).sort("ts")
    return SessionTape(
        symbol=symbol,
        q_ts=df["ts"].to_numpy().astype(np.int64),
        q_bid=df["bid"].to_numpy().astype(np.float64),
        q_ask=df["ask"].to_numpy().astype(np.float64),
        t_ts=np.array([], dtype=np.int64),
        t_price=np.array([], dtype=np.float64),
        t_size=None,
    )


def _void(plan_id: str, symbol: str, side: int) -> MocResult:
    return MocResult(
        plan_id, symbol, side, "void", None, None, None, None, None, None, None, None, None,
    )


def replay_moc_event(
    tape: SessionTape,
    signal_ts: int,
    side: int,
    cross: tuple[int, float, float] | None,
    seed: int,
    plan_id: str,
    *,
    symbol: str | None = None,
    persistence_exit_ts: int | None = None,
    lat_lo_s: float = 5.0,
    lat_hi_s: float = 25.0,
    slip_bps: float = 0.5,
    sec_taf_sell_bps: float = 0.3,
) -> MocResult:
    """Replay one MOC imbalance event to a net-bps result.

    ENTRY (always): a taker MARKET order at ``signal_ts`` + a seeded U[lat_lo,
    lat_hi]s latency draw (leg "entry"), crossing the prevailing NBBO via the
    existing fill kernel (``fills.market_fill``: lifts ask*(1+slip) long / hits
    bid*(1-slip) short). This is the honest, slip-bearing entry — identical
    mechanics to ``backtest/replay.py``.

    EXIT — two mutually exclusive branches:
      * AUCTION (``persistence_exit_ts is None``): fill AT the official closing
        cross price (``cross[1]``), leg "moc", ``maker=False``, ZERO spread/slip
        by construction. In the decomposition the exit mids are set equal to the
        cross price so the exit contributes no spread/latency term — the honest
        representation of a single-clearing-price auction fill. ``cross`` must be
        supplied (from ``find_closing_cross``); a ``None`` cross voids the event.
      * PERSISTENCE (``persistence_exit_ts`` given): the 15:55 NOII flipped side,
        so exit as a taker MARKET order at ``persistence_exit_ts`` + a latency
        draw (leg "persist"), crossing the NBBO like any market-out. The cross is
        not used on this branch.

    Net bps is computed price-to-price minus SEC/TAF on the SELL leg (exit for a
    long, entry for a short) via ``decompose.plan_pnl`` on the two ``Fill``
    objects — the same identity-checked decomposition the main replayer uses.

    Returns a ``MocResult``; ``status == "void"`` when there is no quote before an
    action instant (entry or persistence exit) or the auction cross is missing.
    """
    sym = symbol or tape.symbol
    if side not in (1, -1):
        return _void(plan_id, sym, side)

    # ---- entry: taker market at signal + latency ----------------------------
    entry_action = signal_ts + lat.latency_ns(seed, plan_id, lat.LEG_ENTRY, lat_lo_s, lat_hi_s)
    mk = fk.market_fill(tape.q_ts, tape.q_bid, tape.q_ask, entry_action, side, slip_bps)
    if mk is None:
        return _void(plan_id, sym, side)
    entry_px, entry_mid_act = mk
    entry_mid_dec = fk.prevailing_mid(tape.q_ts, tape.q_bid, tape.q_ask, signal_ts)
    entry_fill = fk.Fill(
        ts=entry_action,
        price=entry_px,
        qty_frac=1.0,
        leg=lat.LEG_ENTRY,
        decision_ts=signal_ts,
        mid_at_decision=entry_mid_dec,
        mid_at_action=entry_mid_act,
        maker=False,
    )

    # ---- exit: persistence market-out OR the auction cross ------------------
    if persistence_exit_ts is not None:
        exit_action = persistence_exit_ts + lat.latency_ns(
            seed, plan_id, "persist", lat_lo_s, lat_hi_s
        )
        mk = fk.market_fill(tape.q_ts, tape.q_bid, tape.q_ask, exit_action, -side, slip_bps)
        if mk is None:
            return _void(plan_id, sym, side)
        exit_px, exit_mid_act = mk
        exit_fill = fk.Fill(
            ts=exit_action,
            price=exit_px,
            qty_frac=1.0,
            leg="persist",
            decision_ts=persistence_exit_ts,
            mid_at_decision=fk.prevailing_mid(
                tape.q_ts, tape.q_bid, tape.q_ask, persistence_exit_ts
            ),
            mid_at_action=exit_mid_act,
            maker=False,
        )
        exit_reason = "persistence"
    else:
        if cross is None:
            return _void(plan_id, sym, side)
        cross_ts, cross_price, _cross_size = cross
        # Zero spread/slip: fill exactly at the single clearing price. Setting the
        # exit mids equal to the fill price makes the exit's spread & latency terms
        # identically zero in decompose — the auction has no queue to cross.
        exit_fill = fk.Fill(
            ts=int(cross_ts),
            price=float(cross_price),
            qty_frac=1.0,
            leg="moc",
            decision_ts=int(cross_ts),
            mid_at_decision=float(cross_price),
            mid_at_action=float(cross_price),
            maker=False,
        )
        exit_reason = "moc"

    pnl = plan_pnl(side, (entry_fill,), (exit_fill,), sec_taf_sell_bps)
    hold_s = (exit_fill.ts - entry_fill.ts) / NS_PER_S
    return MocResult(
        plan_id=plan_id,
        symbol=sym,
        side=side,
        status="ok",
        entry_ts=entry_fill.ts,
        entry_px=entry_fill.price,
        exit_ts=exit_fill.ts,
        exit_px=exit_fill.price,
        exit_reason=exit_reason,
        net_bps=pnl.net_bps,
        hold_s=hold_s,
        entry_mid=entry_mid_dec if np.isfinite(entry_mid_dec) else None,
        pnl=pnl,
    )


# --------------------------------------------------------------- daily-close cross
# The RTH tick fetch window is [09:30, 16:00) EXCLUSIVE, so the 16:00:00.x cross
# print is systematically absent from every download (measured 2026-07-16: tapes
# end ~15:59:59.9). The official DAILY close IS the closing-cross price by
# definition (Nasdaq official close = closing cross), so data/raw/sip/bars1d
# serves as the exact cross-price source. `find_closing_cross` stays preferred
# whenever a conditioned 16:00 print exists (future extended-window fetches).


def official_daily_closes(symbol: str) -> dict[str, float]:
    """Per-session OFFICIAL daily close (bars1d) — the closing-cross price by
    definition. This, not the last RTH 1-minute bar, is the ground truth any
    column named "official close" must carry (code review 2026-07-17 F6)."""
    return _daily_closes(symbol)


@functools.lru_cache(maxsize=16)
def _daily_closes(symbol: str) -> dict[str, float]:
    from datetime import datetime

    p = _Path("data/raw/sip/bars1d") / f"{symbol.upper()}.parquet"
    if not p.exists():
        return {}
    df = pl.read_parquet(p)
    out: dict[str, float] = {}
    for r in df.iter_rows(named=True):
        d = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
        out[d] = float(r["close"])
    return out


def cross_price_for(symbol: str, session_iso: str, trades_df: pl.DataFrame | None) -> tuple[int, float, float] | None:
    """Cross price: conditioned 16:00 print when present, else the official daily close.

    Returns (ts_ns, price, size); size 0.0 and a synthetic 16:00:00 ET ts when the
    daily-close source is used."""
    hit = find_closing_cross(trades_df)
    if hit is not None:
        return hit
    px = _daily_closes(symbol).get(session_iso)
    if px is None:
        return None
    from datetime import datetime
    from zoneinfo import ZoneInfo

    ts = int(datetime.fromisoformat(f"{session_iso}T16:00:00").replace(
        tzinfo=ZoneInfo("America/New_York")).timestamp() * 1e9)
    return (ts, px, 0.0)
