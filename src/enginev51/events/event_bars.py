"""1-second event-bar builder — the canonical input tier for the GPU encoder.

Pure, deterministic transform: (trades_df, quotes_df, session bounds) -> one
polars DataFrame with EXACTLY one row per second in [session_open, session_close).
Second bucket ``t`` covers events with timestamp in ``[t, t + 1s)``; ``ts`` is the
bucket start (Int64 UTC ns). The column spec is FROZEN (see EVENT_BARS_COLUMNS).

PIT semantics: a column is null until the first event of its kind in the session,
then carries values; empty buckets are NOT forward-filled here (downstream ffills).

Schema tolerance: only numeric columns (trades: ts/price/size; quotes:
ts/bid/ask/bid_size/ask_size) are read, so both the full store schema and the
reduced engineV2-imported schema work unchanged. quotes_df may be None -> all
quote-derived fields null/0 and trades go unclassified (at_ask/at_bid = 0).
"""

from __future__ import annotations

import numpy as np
import polars as pl

NS_PER_S = 1_000_000_000
LARGE_TRADE_USD = 50_000.0
ODD_LOT = 100.0

# FROZEN order — the tensor path depends on it.
EVENT_BARS_COLUMNS: list[str] = [
    "ts",
    # --- trades ---
    "n_trades",
    "volume",
    "dollar_vol",
    "px_open",
    "px_high",
    "px_low",
    "px_close",
    "signed_vol",
    "signed_dollar",
    "at_ask_vol",
    "at_bid_vol",
    "large_trade_vol",
    "odd_lot_frac",
    "max_trade_size",
    # --- quotes ---
    "bid",
    "ask",
    "bid_size",
    "ask_size",
    "mid",
    "spread_bps_close",
    "spread_bps_mean",
    "n_quotes",
    "ofi",
    "imb_close",
    "imb_mean",
    "micro_dev_bps",
    "locked_crossed_n",
]

# ts Int64, everything else Float64 (uniform dtype simplifies the tensor path).
EVENT_BARS_SCHEMA: dict[str, pl.DataType] = {
    c: (pl.Int64 if c == "ts" else pl.Float64) for c in EVENT_BARS_COLUMNS
}

# Columns whose "no event in bucket" value is 0.0 (counts / summed flows).
_TRADE_ZERO_COLS = [
    "n_trades",
    "volume",
    "dollar_vol",
    "signed_vol",
    "signed_dollar",
    "at_ask_vol",
    "at_bid_vol",
    "large_trade_vol",
    "max_trade_size",
    "_odd_vol",
]
_QUOTE_ZERO_COLS = ["n_quotes", "ofi", "locked_crossed_n"]


def _tick_sign(prices: np.ndarray) -> np.ndarray:
    """Tick-rule sign vs the previous DIFFERENT trade price, carried forward.

    First trade of the session -> 0. Ties carry the last nonzero sign forward
    (equivalent to comparing against the previous different price).
    """
    n = prices.size
    if n == 0:
        return np.zeros(0, dtype=np.float64)
    s = np.zeros(n, dtype=np.int64)
    if n > 1:
        s[1:] = np.sign(np.diff(prices)).astype(np.int64)
    # forward-fill zeros with the last nonzero sign (initial carry = 0 at index 0)
    nz = s != 0
    idx = np.where(nz, np.arange(n), 0)
    np.maximum.accumulate(idx, out=idx)
    return s[idx].astype(np.float64)


def _ofi(bid: np.ndarray, ask: np.ndarray, bsz: np.ndarray, asz: np.ndarray) -> np.ndarray:
    """Cont-Kukanov-Stoikov L1 OFI per update (n vs n-1); first update -> 0."""
    n = bid.size
    e = np.zeros(n, dtype=np.float64)
    if n > 1:
        bc, bp = bid[1:], bid[:-1]
        ac, ap = ask[1:], ask[:-1]
        qbc, qbp = bsz[1:], bsz[:-1]
        qac, qap = asz[1:], asz[:-1]
        e[1:] = (
            (bc >= bp) * qbc
            - (bc <= bp) * qbp
            - (ac <= ap) * qac
            + (ac >= ap) * qap
        )
    return e


def _classify(
    tp: np.ndarray, tt: np.ndarray, qt: np.ndarray, qa: np.ndarray, qb: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Classify each trade against its prevailing quote (last q_ts <= trade_ts).

    Guarded searchsorted(right)-1; index < 0 -> unclassified. Ask precedence:
    price >= ask -> at_ask; elif price <= bid -> at_bid; else neither.
    """
    n = tp.size
    if n == 0 or qt.size == 0:
        return np.zeros(n, dtype=bool), np.zeros(n, dtype=bool)
    idx = np.searchsorted(qt, tt, side="right") - 1
    valid = idx >= 0
    safe = np.clip(idx, 0, qt.size - 1)
    ask_at = qa[safe]
    bid_at = qb[safe]
    at_ask = valid & (tp >= ask_at)
    at_bid = valid & ~at_ask & (tp <= bid_at)
    return at_ask, at_bid


def _prep_quotes(
    quotes_df: pl.DataFrame | None, open_ns: int, n_sec: int
) -> tuple[pl.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """Filter/sort/bucket in-session quotes. Returns (per-update frame, qt, qa, qb).

    The per-update frame carries the columns needed for group-by aggregation; the
    numpy arrays (sorted ts / ask / bid) feed trade classification.
    """
    empty = np.zeros(0, dtype=np.float64)
    if quotes_df is None or quotes_df.height == 0:
        return pl.DataFrame(), empty, empty, empty

    q = (
        quotes_df.select("ts", "bid", "ask", "bid_size", "ask_size")
        .filter((pl.col("bid") > 0) & (pl.col("ask") > 0))
        .sort("ts")
        .with_columns(((pl.col("ts") - open_ns) // NS_PER_S).alias("b"))
        .filter((pl.col("b") >= 0) & (pl.col("b") < n_sec))
    )
    if q.height == 0:
        return pl.DataFrame(), empty, empty, empty

    qt = q["ts"].to_numpy()
    qa = q["ask"].to_numpy()
    qb = q["bid"].to_numpy()
    qbs = q["bid_size"].to_numpy()
    qas = q["ask_size"].to_numpy()

    q = q.with_columns(pl.Series("e_ofi", _ofi(qb, qa, qbs, qas)))
    denom = pl.col("bid_size") + pl.col("ask_size")
    q = q.with_columns(
        ((pl.col("bid") + pl.col("ask")) / 2.0).alias("mid"),
        (1e4 * (pl.col("ask") - pl.col("bid")) / ((pl.col("bid") + pl.col("ask")) / 2.0)).alias(
            "spread_bps"
        ),
        pl.when(denom > 0)
        .then((pl.col("bid_size") - pl.col("ask_size")) / denom)
        .otherwise(None)
        .alias("imb"),
        (pl.col("bid") >= pl.col("ask")).cast(pl.Float64).alias("locked"),
    )
    micro = pl.when(denom > 0).then(
        (pl.col("ask") * pl.col("bid_size") + pl.col("bid") * pl.col("ask_size")) / denom
    ).otherwise(None)
    q = q.with_columns(
        pl.when(micro.is_not_null())
        .then(1e4 * (micro - pl.col("mid")) / pl.col("mid"))
        .otherwise(None)
        .alias("micro_dev")
    )
    return q, qt, qa, qb


def build_event_bars(
    trades_df: pl.DataFrame,
    quotes_df: pl.DataFrame | None,
    session_open_ns: int,
    session_close_ns: int,
) -> pl.DataFrame:
    """Build 1-second event bars over [session_open_ns, session_close_ns).

    One row per second; bounds come from the caller (half-days included). The
    result is sorted by ts and has exactly EVENT_BARS_COLUMNS in frozen order.
    """
    open_ns = int(session_open_ns)
    close_ns = int(session_close_ns)
    n_sec = (close_ns - open_ns) // NS_PER_S
    if n_sec <= 0:
        raise ValueError(f"non-positive session length: open={open_ns} close={close_ns}")

    grid = pl.DataFrame({"idx": np.arange(n_sec, dtype=np.int64)}).with_columns(
        (open_ns + pl.col("idx") * NS_PER_S).alias("ts")
    )

    # ---------------------------------------------------------------- quotes
    q, qt, qa, qb = _prep_quotes(quotes_df, open_ns, n_sec)
    if q.height:
        quote_agg = q.group_by("b", maintain_order=True).agg(
            pl.col("bid").last(),
            pl.col("ask").last(),
            pl.col("bid_size").last(),
            pl.col("ask_size").last(),
            pl.col("mid").last(),
            pl.col("spread_bps").last().alias("spread_bps_close"),
            pl.col("spread_bps").mean().alias("spread_bps_mean"),
            pl.len().alias("n_quotes"),
            pl.col("e_ofi").sum().alias("ofi"),
            pl.col("imb").last().alias("imb_close"),
            pl.col("imb").mean().alias("imb_mean"),
            pl.col("micro_dev").last().alias("micro_dev_bps"),
            pl.col("locked").sum().alias("locked_crossed_n"),
        ).rename({"b": "idx"})
    else:
        quote_agg = None

    # ---------------------------------------------------------------- trades
    t = (
        trades_df.select("ts", "price", "size")
        .filter((pl.col("price") > 0) & (pl.col("size") >= 0))
        .sort("ts")
        .with_columns(((pl.col("ts") - open_ns) // NS_PER_S).alias("b"))
        .filter((pl.col("b") >= 0) & (pl.col("b") < n_sec))
    )
    if t.height:
        tt = t["ts"].to_numpy()
        tp = t["price"].to_numpy()
        tsz = t["size"].to_numpy()
        sign = _tick_sign(tp)
        at_ask, at_bid = _classify(tp, tt, qt, qa, qb)
        dollar = tp * tsz
        twork = pl.DataFrame(
            {
                "b": t["b"].to_numpy(),
                "price": tp,
                "size": tsz,
                "dollar": dollar,
                "signed": sign * tsz,
                "signed_dollar": sign * dollar,
                "at_ask_size": np.where(at_ask, tsz, 0.0),
                "at_bid_size": np.where(at_bid, tsz, 0.0),
                "large_size": np.where(dollar >= LARGE_TRADE_USD, tsz, 0.0),
                "odd_size": np.where(tsz < ODD_LOT, tsz, 0.0),
            }
        )
        trade_agg = twork.group_by("b", maintain_order=True).agg(
            pl.len().alias("n_trades"),
            pl.col("size").sum().alias("volume"),
            pl.col("dollar").sum().alias("dollar_vol"),
            pl.col("price").first().alias("px_open"),
            pl.col("price").max().alias("px_high"),
            pl.col("price").min().alias("px_low"),
            pl.col("price").last().alias("px_close"),
            pl.col("signed").sum().alias("signed_vol"),
            pl.col("signed_dollar").sum().alias("signed_dollar"),
            pl.col("at_ask_size").sum().alias("at_ask_vol"),
            pl.col("at_bid_size").sum().alias("at_bid_vol"),
            pl.col("large_size").sum().alias("large_trade_vol"),
            pl.col("odd_size").sum().alias("_odd_vol"),
            pl.col("size").max().alias("max_trade_size"),
        ).rename({"b": "idx"})
    else:
        trade_agg = None

    # ---------------------------------------------------------------- assemble
    out = grid
    if trade_agg is not None:
        out = out.join(trade_agg, on="idx", how="left")
    if quote_agg is not None:
        out = out.join(quote_agg, on="idx", how="left")

    # ensure every expected column exists (all-empty inputs)
    present = set(out.columns)
    missing_zero = [c for c in _TRADE_ZERO_COLS + _QUOTE_ZERO_COLS if c not in present]
    null_cols = [
        "px_open", "px_high", "px_low", "px_close",
        "bid", "ask", "bid_size", "ask_size", "mid",
        "spread_bps_close", "spread_bps_mean", "imb_close", "imb_mean", "micro_dev_bps",
    ]
    missing_null = [c for c in null_cols if c not in present]
    add = [pl.lit(0.0).alias(c) for c in missing_zero]
    add += [pl.lit(None, dtype=pl.Float64).alias(c) for c in missing_null]
    if add:
        out = out.with_columns(add)

    # empty-bucket fills: counts / summed flows -> 0.0; state / means stay null
    out = out.with_columns(
        [pl.col(c).fill_null(0.0) for c in _TRADE_ZERO_COLS + _QUOTE_ZERO_COLS]
    )
    out = out.with_columns(
        pl.when(pl.col("volume") > 0)
        .then(pl.col("_odd_vol") / pl.col("volume"))
        .otherwise(0.0)
        .alias("odd_lot_frac")
    )

    out = out.select(
        [
            (pl.col(c).cast(pl.Int64) if c == "ts" else pl.col(c).cast(pl.Float64))
            for c in EVENT_BARS_COLUMNS
        ]
    )
    return out
