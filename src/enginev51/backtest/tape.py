"""Session tape loader: daily tick partitions -> SessionTape numpy arrays.

Reads across settings.read_roots (primary lake first, legacy engineV5 lake
second), tolerating both the full store schemas and the reduced legacy ones
(trades: ts/price/size only; quotes: ts/bid/ask/bid_size/ask_size only).

Sanity filter for the FILL tape (PROTOCOL v6 §3): trades price>0; quotes
bid>0 AND ask>bid — crossed/locked quotes are excluded here because fills must
never execute against a broken book (event_bars counts them separately as a
signal). Arrays are ts-sorted.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from enginev51.backtest.replay import SessionTape
from enginev51.config import Settings
from enginev51.data import store

# v1.4 excluded sale conditions, as TOKENS (code review 2026-07-28 S1). The lake
# stores conditions as the vendor's code LIST joined with "|"
# (data/alpaca_hist.fetch_trades), so exclusion is token-set membership, not a
# substring scan of the joined string: `contains_any` would drop a hypothetical
# multi-character code merely because one of these letters appears inside it
# (e.g. a code "TW" is not the extended-hours "T"). Every code Alpaca emits today
# is a single character, so on the existing lake the two rules agree exactly —
# this is a robustness fix, not a numeric change.
EXCLUDED_CONDITIONS: tuple[str, ...] = tuple("ZLGU4WPCNRHXMQO569T")
CONDITION_SEP = "|"


def _excluded_conditions(col: str = "conditions") -> pl.Expr:
    """Boolean expr: this row's condition tokens intersect EXCLUDED_CONDITIONS."""
    return (
        pl.col(col)
        .str.split(CONDITION_SEP)
        .list.eval(pl.element().is_in(EXCLUDED_CONDITIONS))
        .list.any()
    )


def _day_frame(settings: Settings, kind: str, symbol: str, session_iso: str) -> pl.DataFrame | None:
    for root in settings.read_roots:
        p = store.partition_path(root, "sip", kind, symbol, session_iso)
        if p.exists():
            df = pl.read_parquet(p)
            return df
    return None


def load_session_tape(settings: Settings, symbol: str, session_iso: str) -> SessionTape | None:
    """Load one (symbol, session)'s fill tape; None if trades or quotes missing/empty."""
    tr = _day_frame(settings, "trades", symbol, session_iso)
    qt = _day_frame(settings, "quotes", symbol, session_iso)
    if tr is None or qt is None or tr.height == 0 or qt.height == 0:
        return None

    t_cols = ["ts", "price"] + (["size"] if "size" in tr.columns else [])
    # v1.4 CONDITION-CODED fill tape: when the download carries condition codes,
    # drop every print that is not regular-way marketable evidence — late/out-of-
    # sequence (Z,L,G,U), derivatively priced (4), average price (W), prior
    # reference (P), cash/next-day (C,N), seller (R), price-variation (H),
    # crosses/officials (X,M,Q,O,5,6,9), extended hours (T). Odd lots (I) are
    # kept here and handled by min_fill_size (they carry real price info for
    # quotes/mids). Legacy data (empty conditions) falls back to the v1.3
    # quote-confirmation belt alone. Ledger 2026-07-16.
    if "conditions" in tr.columns:
        nonempty = tr.filter(pl.col("conditions") != "").height
        if nonempty > 0:
            t_cols = t_cols + ["conditions"]
            tr = tr.filter(~_excluded_conditions())
    tr = tr.select([c for c in t_cols if c != "conditions"]).filter(pl.col("price") > 0).sort("ts")
    qt = (
        qt.select("ts", "bid", "ask")
        .filter((pl.col("bid") > 0) & (pl.col("ask") > pl.col("bid")))
        .sort("ts")
    )
    if tr.height == 0 or qt.height == 0:
        return None
    return SessionTape(
        symbol=symbol,
        q_ts=qt["ts"].to_numpy().astype(np.int64),
        q_bid=qt["bid"].to_numpy().astype(np.float64),
        q_ask=qt["ask"].to_numpy().astype(np.float64),
        t_ts=tr["ts"].to_numpy().astype(np.int64),
        t_price=tr["price"].to_numpy().astype(np.float64),
        t_size=tr["size"].to_numpy().astype(np.float64) if "size" in tr.columns else None,
    )


def widen_tape(tape: SessionTape, spread_mult: float) -> SessionTape:
    """Replay-level spread stress: scale every quote's spread around its own mid.

    bid' = bid - h, ask' = ask + h with h = (ask-bid)(mult-1)/2, so mult=2 doubles
    each quote's spread. This stresses EVERYTHING consistently — market fills,
    limit-join prices are unaffected (they come from event bars), but stop
    triggers and crossing exits see the wider book. The frame-arithmetic
    double_spread stress in backtest/stress.py is only valid for taker books;
    this is the honest maker-book version (ledger 2026-07-15).
    """
    if spread_mult == 1.0:
        return tape
    h = (tape.q_ask - tape.q_bid) * (spread_mult - 1.0) / 2.0
    return SessionTape(
        symbol=tape.symbol,
        q_ts=tape.q_ts,
        q_bid=tape.q_bid - h,
        q_ask=tape.q_ask + h,
        t_ts=tape.t_ts,
        t_price=tape.t_price,
        t_size=tape.t_size,
    )
