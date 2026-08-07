"""PIT fill primitives — the causal fill kernel for the replayer.

Pure numpy functions: quote/trade arrays in, fill facts out. No I/O, no state,
deterministic. Every timestamp is UTC ns; sides are +1 long/buy, -1 short/sell.
All input arrays are ts-sorted, sane-filtered numpy arrays for ONE
(symbol, session).

Point-in-time discipline (audited, ported from engineV5 maker_study):
  * "Prevailing" = last quote/trade at-or-before t == `searchsorted(side='right')
    - 1`. That index is -1 when nothing precedes t, and numpy `arr[-1]` WRAPS to
    the final (future) element, so every prevailing lookup is guarded `>= 0`
    before use. Unguarded, a lookup before the first quote would silently read
    the session's LAST quote — a look-ahead bug. `prevailing_idx` returns the
    raw (possibly -1) index; callers here all guard it.
  * TRADE fill windows open STRICTLY AFTER the placement/arm/decision instant
    (`searchsorted(side='right')` = first strictly-later ts): a print landing
    exactly at placement can never fill us. Windows close inclusively at their
    stated bound (`cancel_ts` / `to_ts`); no function reads past that bound.
  * Stops trigger on QUOTES (the market can no longer be exited the good side of
    the stop) and return the decision ts — the caller applies latency and takes
    the post-latency touch, so a gap-through fills worse than the stop
    (gap-through honesty, PROTOCOL v6 §3). A stop is a LEVEL, not a transition:
    `stop_trigger_ts` first checks the PREVAILING quote at the arm instant, so a
    book already through the stop when the bracket goes live decides at the arm
    instant itself rather than waiting for the next quote update (code review
    2026-07-28 B3). This is the one place a prevailing (at-or-before) read is a
    trigger and not just context — it reads no future tape.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Fraction per basis point (multiply a bps quantity by this to get a fraction).
# Deliberately NOT named BPS: decompose.py's BPS_SCALE is the inverse (1e4), and
# the shared name invited copy-paste sign/scale mistakes (code review F16).
FRAC_PER_BP = 1e-4


@dataclass(slots=True, frozen=True)
class Fill:
    ts: int
    price: float
    qty_frac: float
    leg: str
    decision_ts: int  # when the trigger/decision happened (pre-latency)
    mid_at_decision: float  # prevailing mid at decision_ts (nan if no quote yet)
    mid_at_action: float  # prevailing mid at action/placement ts (nan if none)
    maker: bool  # True = passive limit fill at our price


def prevailing_idx(ts_arr: np.ndarray, t: int) -> int:
    """Index of the last element with ts <= t; -1 if none.

    `searchsorted(side='right') - 1`. MUST be guarded `>= 0` at every call site:
    numpy `arr[-1]` reads the final (future) element rather than raising.
    """
    return int(np.searchsorted(ts_arr, t, side="right")) - 1


def prevailing_mid(q_ts: np.ndarray, q_bid: np.ndarray, q_ask: np.ndarray, t: int) -> float:
    """Mid of the last quote at-or-before t; nan if no quote precedes t."""
    i = prevailing_idx(q_ts, t)
    if i < 0:
        return float("nan")
    return 0.5 * (float(q_bid[i]) + float(q_ask[i]))


def _first_print(
    t_ts: np.ndarray,
    t_price: np.ndarray,
    after_ts: int,
    to_ts: int,
    limit: float,
    *,
    want_above: bool,
    strict: bool,
    t_size: np.ndarray | None = None,
    min_size: float = 0.0,
    q_ts: np.ndarray | None = None,
    q_bid: np.ndarray | None = None,
    q_ask: np.ndarray | None = None,
) -> int | None:
    """First trade STRICTLY after `after_ts`, ts <= `to_ts`, on the wanted side of
    `limit`. `want_above` picks price > / >= limit (else < / <=); `strict` picks
    the through (>/<) vs touch (>=/<=) boundary. Returns the trade ts or None.

    `min_size` (with `t_size`): only prints of at least this size count as fill
    evidence. The legacy tick data carries no condition codes, so ODD-LOT prints
    (which do not set or clear the NBBO) are indistinguishable from round lots;
    requiring >= 100 shares keeps a through-print meaning "the level actually
    cleared" (harness-hardening v1.1, ledger 2026-07-15).
    """
    lo = int(np.searchsorted(t_ts, after_ts, side="right"))  # first ts strictly after
    hi = int(np.searchsorted(t_ts, to_ts, side="right"))  # first ts past the bound
    if hi <= lo:
        return None
    prices = t_price[lo:hi]
    if want_above:
        mask = (prices > limit) if strict else (prices >= limit)
    else:
        mask = (prices < limit) if strict else (prices <= limit)
    if min_size > 0.0 and t_size is not None:
        mask = mask & (t_size[lo:hi] >= min_size)
    if not mask.any():
        return None
    if q_ts is None or q_ts.size == 0:
        return int(t_ts[lo + int(np.argmax(mask))])
    # v1.3 QUOTE-CONFIRMED fills: the legacy tape has no condition codes, so
    # late-reported/off-market prints (e.g. a block printed $3 through a resting
    # level while the NBBO never moved) are indistinguishable from real trades.
    # A print only counts as level-clearing evidence if the PREVAILING NBBO at
    # that instant actually reached the limit: sell-limit needs ask >= limit,
    # buy-limit needs bid <= limit. Conservative: legit fills during quote lag
    # are dropped; fake fills through a distant book are killed (ledger
    # 2026-07-16, case study NVDA 2025-11-25 13:23 'fill' 172.59 vs mid ~176).
    cand = np.flatnonzero(mask)
    for rel in cand:
        pt = int(t_ts[lo + rel])
        qi = int(np.searchsorted(q_ts, pt, side="right")) - 1
        if qi < 0:
            continue
        if want_above:
            if float(q_ask[qi]) >= limit:
                return pt
        else:
            if float(q_bid[qi]) <= limit:
                return pt
    return None


def limit_fill_ts(
    t_ts: np.ndarray,
    t_price: np.ndarray,
    place_ts: int,
    cancel_ts: int,
    limit: float,
    side: int,
    *,
    strict: bool = True,
    t_size: np.ndarray | None = None,
    min_size: float = 0.0,
    q_ts: np.ndarray | None = None,
    q_bid: np.ndarray | None = None,
    q_ask: np.ndarray | None = None,
) -> int | None:
    """First trade that fills a resting aggressive limit ENTRY, or None.

    BUY (side=+1): first trade STRICTLY after place_ts, ts <= cancel_ts, with
    price < limit (strict / L2 through) or <= limit (touch / L1).
    SELL (side=-1): mirrored — price > limit (strict) or >= limit (touch).
    A print AT place_ts never fills; nothing past cancel_ts is read.
    `min_size`: see _first_print (odd-lot-robust fill evidence).
    """
    return _first_print(
        t_ts, t_price, place_ts, cancel_ts, limit, want_above=side < 0, strict=strict,
        t_size=t_size, min_size=min_size, q_ts=q_ts, q_bid=q_bid, q_ask=q_ask,
    )


def market_fill(
    q_ts: np.ndarray,
    q_bid: np.ndarray,
    q_ask: np.ndarray,
    exec_ts: int,
    side: int,
    slip_bps: float,
) -> tuple[float, float] | None:
    """Cross the prevailing NBBO at exec_ts. BUY (+1) lifts ask*(1+slip); SELL
    (-1) hits bid*(1-slip). Returns (fill_price, mid_at_exec) or None when no
    quote precedes exec_ts (guarded: never crosses a wrapped future quote).
    """
    i = prevailing_idx(q_ts, exec_ts)
    if i < 0:
        return None
    bid = float(q_bid[i])
    ask = float(q_ask[i])
    mid = 0.5 * (bid + ask)
    slip = slip_bps * FRAC_PER_BP
    price = ask * (1.0 + slip) if side > 0 else bid * (1.0 - slip)
    return price, mid


def stop_trigger_ts(
    q_ts: np.ndarray,
    q_bid: np.ndarray,
    q_ask: np.ndarray,
    from_ts: int,
    to_ts: int,
    stop: float,
    side: int,
) -> int | None:
    """Decision ts in [from_ts, to_ts] at which a position can no longer be
    exited the good side of its stop, or None.

    LONG (side=+1): bid <= stop (can't sell above the stop).
    SHORT (side=-1): ask >= stop (can't cover below the stop).

    LEVEL semantics, not transition semantics (code review 2026-07-28 B3): the
    PREVAILING quote at `from_ts` (last quote with ts <= from_ts) is checked
    first, so a book ALREADY through the stop when the stop arms — a gap entry
    or an immediate breach — decides at `from_ts` itself. The old strict-after
    window waited for a LATER quote update, which on a sparse tape let a
    through position ride to hold/curfew (optimistic vs a human who markets out
    the moment the bracket is live and already breached). Failing that, the
    first quote in (from_ts, to_ts] that is through the stop triggers.

    Returns the decision ts (never < from_ts, never > to_ts); the caller applies
    latency and takes the post-latency touch (a gap-through fills worse than
    `stop`). None when the window is inverted, no quote precedes/lies in it, or
    the book is never through.
    """
    if to_ts < from_ts:
        return None
    # already-through at the arm instant -> the decision IS the arm instant
    i = prevailing_idx(q_ts, from_ts)
    if i >= 0 and ((float(q_bid[i]) <= stop) if side > 0 else (float(q_ask[i]) >= stop)):
        return int(from_ts)
    lo = int(np.searchsorted(q_ts, from_ts, side="right"))  # strictly after from_ts
    hi = int(np.searchsorted(q_ts, to_ts, side="right"))  # first past to_ts
    if hi <= lo:
        return None
    mask = (q_bid[lo:hi] <= stop) if side > 0 else (q_ask[lo:hi] >= stop)
    if not mask.any():
        return None
    return int(q_ts[lo + int(np.argmax(mask))])


def target_fill_ts(
    t_ts: np.ndarray,
    t_price: np.ndarray,
    arm_ts: int,
    to_ts: int,
    price: float,
    side: int,
    *,
    strict: bool = True,
    t_size: np.ndarray | None = None,
    min_size: float = 0.0,
    q_ts: np.ndarray | None = None,
    q_bid: np.ndarray | None = None,
    q_ask: np.ndarray | None = None,
) -> int | None:
    """First trade that fills a passive profit-take on an OPEN position, or None.

    LONG (side=+1) exits via a resting SELL limit at `price`: first trade
    STRICTLY after arm_ts, ts <= to_ts, with price > limit (strict) or >= (touch)
    — a buyer must lift through our offer.
    SHORT (side=-1) exits via a resting BUY limit: mirrored (< / <=).
    `min_size`: see _first_print (odd-lot-robust fill evidence).
    """
    return _first_print(
        t_ts, t_price, arm_ts, to_ts, price, want_above=side > 0, strict=strict,
        t_size=t_size, min_size=min_size, q_ts=q_ts, q_bid=q_bid, q_ask=q_ask,
    )
