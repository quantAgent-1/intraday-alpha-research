"""Decision-time entry-quality features + the fixed a-priori authoring gate.

Registered en bloc as ``M3-H2-entry-quality-v1`` (research/ledger.jsonl):
decision-time quote-state features predict clean-join vs run-over maker entries
well enough that a fixed gate yields a positive honest-fill book. This module is
the sole owner of that spec — no thresholds are tunable here.

Everything is read from COMPLETED 1-second event bars only. An event-bar row's
``ts`` is the bucket START covering ``[ts, ts + 1s)``; a bucket is completed for a
decision instant ``ts`` iff its END is at or before ``ts`` (i.e. bucket start
``<= ts - 1s``). A bucket that merely *starts* at ``ts`` is NOT completed and is
excluded — the same point-in-time rule ``context.SessionContext.quote_at`` uses,
so the gate can leak no future quote state (PROTOCOL v6 §3, PIT discipline).

The 28-column source schema is ``events.event_bars.EVENT_BARS_COLUMNS``; only
``ts``, ``spread_bps_close``, ``n_quotes``, ``ofi`` and ``locked_crossed_n`` are
read. ``n_quotes``/``ofi``/``locked_crossed_n`` are zero-filled on empty buckets;
``spread_bps_close`` is null on a second with no quote update.
"""

from __future__ import annotations

import numpy as np
import polars as pl

NS_PER_S = 1_000_000_000

# Registered feature-window / warmup constants (a priori; not tunable).
WARMUP_SECONDS = 60   # < this many completed seconds -> None (no evidence)
WINDOW = 10           # rolling flow window, seconds

# Registered gate thresholds (fixed a priori; M3-H2-entry-quality-v1).
F1_MAX = 1.5          # spread ratio ceiling
F2_MAX = 3.0          # quote-churn ratio ceiling
F3_ABS_MAX = 2.0      # OFI z magnitude below which direction is unconstrained


def _rolling_window_sums(x: np.ndarray, w: int) -> np.ndarray:
    """Full-window (length-``w``) sliding sums of ``x``; empty if ``x.size < w``.

    Value at output index ``s`` is ``x[s:s+w].sum()``; there are
    ``len(x) - w + 1`` of them (the "rolling 10s sums over the session so far").
    """
    if x.size < w:
        return np.zeros(0, dtype=np.float64)
    c = np.cumsum(np.concatenate(([0.0], x.astype(np.float64))))
    return c[w:] - c[:-w]


def features_at(ev: pl.DataFrame, ts: int) -> dict | None:
    """Entry-quality features from completed event-bar seconds at instant ``ts``.

    Uses only rows whose bucket has fully closed (``ts_row <= ts - 1s``). Returns
    ``None`` during warmup (fewer than ``WARMUP_SECONDS`` completed seconds) or
    when event bars are absent. Otherwise a dict with:

    * ``f1`` spread ratio: current (most-recent non-null) ``spread_bps_close`` of
      the last completed second / session-so-far median of ``spread_bps_close``
      (completed seconds, nulls dropped). ``None`` if no non-null spread / zero
      median (no evidence).
    * ``f2`` quote-churn ratio: ``sum(n_quotes)`` over the last 10 completed
      seconds / median of the rolling-10s ``n_quotes`` sums so far. ``None`` on a
      zero median (div0 guard).
    * ``f3`` OFI z: ``sum(ofi)`` over the last 10 completed seconds / population
      std of the rolling-10s ``ofi`` sums so far. ``0.0`` when that std is 0
      (degenerate-flow guard).
    * ``f4`` ``sum(locked_crossed_n)`` over the last 10 completed seconds.
    """
    if ev is None or ev.height == 0:
        return None
    cutoff = int(ts) - NS_PER_S
    completed = ev.filter(pl.col("ts") <= cutoff).sort("ts")
    if completed.height < WARMUP_SECONDS:
        return None

    # f1 — spread ratio (current spread vs session-so-far median).
    spread = completed["spread_bps_close"].drop_nulls().to_numpy()
    if spread.size == 0:
        f1: float | None = None
    else:
        med_spread = float(np.median(spread))
        f1 = float(spread[-1]) / med_spread if med_spread != 0.0 else None

    nq = completed["n_quotes"].to_numpy().astype(np.float64)
    ofi = completed["ofi"].to_numpy().astype(np.float64)
    lck = completed["locked_crossed_n"].to_numpy().astype(np.float64)

    # Numerators — flow over the last WINDOW completed seconds (contiguous by
    # construction: event bars have exactly one row per second).
    nq_last = float(nq[-WINDOW:].sum())
    ofi_last = float(ofi[-WINDOW:].sum())
    f4 = float(lck[-WINDOW:].sum())

    # Denominators — the session-so-far distribution of rolling-WINDOW sums.
    nq_roll = _rolling_window_sums(nq, WINDOW)
    ofi_roll = _rolling_window_sums(ofi, WINDOW)

    nq_med = float(np.median(nq_roll))
    f2: float | None = nq_last / nq_med if nq_med != 0.0 else None

    ofi_std = float(np.std(ofi_roll))  # population std (ddof=0), per spec
    f3 = ofi_last / ofi_std if ofi_std != 0.0 else 0.0

    return {"f1": f1, "f2": f2, "f3": f3, "f4": f4}


def _sign(x: float) -> int:
    """Sign of ``x`` as -1 / 0 / +1 (comparable to a plan direction of +/-1)."""
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def gate(f: dict | None, direction: int) -> bool:
    """Registered authoring gate — ``True`` allows the plan to be authored.

    ``f is None`` -> ``True``: no decision-time evidence, so no veto. Otherwise
    allow iff ``f1 <= 1.5`` AND ``f2 <= 3.0`` AND ``f4 == 0`` AND
    (``|f3| <= 2.0`` OR ``sign(f3) == direction``). A sub-feature that could not
    be computed (``None`` from a div0 / no-evidence guard) does not veto its own
    clause — same "no evidence, no veto" principle applied per dimension.
    """
    if f is None:
        return True
    f1, f2, f3, f4 = f["f1"], f["f2"], f["f3"], f["f4"]
    c1 = f1 is None or f1 <= F1_MAX
    c2 = f2 is None or f2 <= F2_MAX
    c4 = f4 == 0
    c3 = f3 is None or abs(f3) <= F3_ABS_MAX or _sign(f3) == direction
    return bool(c1 and c2 and c3 and c4)
