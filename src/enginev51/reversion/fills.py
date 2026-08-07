"""Fill models, sizing/stop/TP, and the REALISTIC cost/attribution model.

BUILD-SPEC §3, A9, A10. Port target: engineV2 ``riskgate_nb._size_entry_fp`` /
``_take_profit_fp`` / ``_round_tick_fp`` (sizing + tick-rounded stop/TP) and
``archive/research/goal_run/costs.py`` (REALISTIC net PnL).

Fills on the 1 s substrate:
  * MAKER ENTRY  post limit at current bid (long) / ask (short) at t0; fill at
    the limit at the FIRST bar in (t0, t0+60] whose px_low<=limit (long) /
    px_high>=limit (short) — "touch". Cancel after 60 s → no trade. B5 knobs:
    strict "through" (px_low<limit / px_high>limit) and a deterministic 50 %
    keep-hash of (sym, ts).
  * TAKER  fill at bar trigger+2 (~2 s >= engineV2's 1500 ms latency) at the
    crossing quote — entry: ask (long)/bid (short); exit: bid (long)/ask (short).
  * Fees $0.005/share each leg (both legs); +0.5 bps slippage on TAKER legs only
    (maker leg price = the limit, no slippage).
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import numpy as np

# engineV2 RiskDefaults / costs.py REALISTIC / fixed_point tick.
TICK = 0.01
FEE_PER_SHARE = 0.005
SLIP_BPS_PER_SIDE = 0.5
FRAC_PER_BP = 1e-4
HARD_STOP_BPS = 75.0
MIN_STOP_VOL_MULT = 1.5
TP_BPS = 10.0
TARGET_NOTIONAL_USD = 200.0
MIN_SHARES = 1
MAX_SHARES = 5000
TAKER_LATENCY_BARS = 2      # BUILD-SPEC §3: trigger+2 (~2 s)
MAKER_CANCEL_BARS = 60      # cancel-if-unfilled window (60 s)
PRICE_SCALE = 10_000        # engineV2 fixed_point.PRICE_SCALE (round stop_dist to 1e-4)


def _floor_tick(price: float) -> float:
    return math.floor(round(price / TICK, 9)) * TICK


def _ceil_tick(price: float) -> float:
    return math.ceil(round(price / TICK, 9)) * TICK


@dataclass(slots=True, frozen=True)
class SizedEntry:
    shares: int
    hard_stop: float
    take_profit: float
    stop_dist_usd: float


def size_and_levels(entry: float, side: int, sigma_5m: float) -> SizedEntry:
    """engineV2 _size_entry_fp + _take_profit_fp (stop_bps=0 default path).

    stop_dist = max(entry·75bps, 1.5·σ_5m); shares = floor(200/stop_dist) clamped
    [1, 5000]. Stop/TP tick-rounded (floor long-stop / ceil short-stop; floor
    long-TP / ceil short-TP). σ_5m may be 0/NaN → the bps floor governs.
    """
    sig = sigma_5m if (sigma_5m is not None and math.isfinite(sigma_5m) and sigma_5m > 0.0) else 0.0
    stop_dist = max(entry * HARD_STOP_BPS / 1e4, MIN_STOP_VOL_MULT * sig)
    stop_dist = round(stop_dist * PRICE_SCALE) / PRICE_SCALE  # fixed-point (1e-4) round
    shares_raw = TARGET_NOTIONAL_USD / max(stop_dist, 1e-9)
    shares = int(math.floor(shares_raw))
    shares = max(MIN_SHARES, min(MAX_SHARES, shares))
    if side > 0:
        hard_stop = _floor_tick(entry - stop_dist)
        take_profit = _floor_tick(entry + entry * TP_BPS / 1e4)
    else:
        hard_stop = _ceil_tick(entry + stop_dist)
        take_profit = _ceil_tick(entry - entry * TP_BPS / 1e4)
    return SizedEntry(shares, hard_stop, take_profit, stop_dist)


def maker_fill_bar(
    px_low: np.ndarray, px_high: np.ndarray, t0: int, side: int, limit: float,
    *, strict: bool = False, cancel_bars: int = MAKER_CANCEL_BARS,
) -> int | None:
    """First bar j in (t0, t0+cancel_bars] with a touch (or through, if strict)
    of ``limit``. Long fills when px_low<=limit (touch) / <limit (through);
    short when px_high>=limit / >limit. Returns j or None (cancelled)."""
    n = px_low.size
    lo = t0 + 1
    hi = min(t0 + cancel_bars, n - 1)
    if lo > hi or not math.isfinite(limit):
        return None
    for j in range(lo, hi + 1):
        if side > 0:
            low = px_low[j]
            if low == low and low > 0.0:  # not NaN
                if (low < limit) if strict else (low <= limit):
                    return j
        else:
            high = px_high[j]
            if high == high and high > 0.0:
                if (high > limit) if strict else (high >= limit):
                    return j
    return None


def keep_hash_50(symbol: str, ts_ns: int) -> bool:
    """Deterministic 50 % keep of a (sym, ts) pair for the B5 queue-priority
    haircut. Even low-bit of a stable md5 digest."""
    h = hashlib.md5(f"{symbol}:{int(ts_ns)}".encode()).digest()  # noqa: S324 (non-crypto, determinism only)
    return (h[0] & 1) == 0


@dataclass(slots=True, frozen=True)
class Attribution:
    gross_usd: float
    mid_to_mid_usd: float
    spread_usd: float       # mid_to_mid − gross (paid>0 / earned<0)
    fees_usd: float
    slippage_usd: float
    net_usd: float
    ret_bps: float          # net on entry notional


def attribute(
    *, side: int, shares: int,
    entry_fill: float, exit_fill: float, entry_mid: float, exit_mid: float,
    entry_is_taker: bool, exit_is_taker: bool,
) -> Attribution:
    """REALISTIC decomposition (costs.py + engineV2 REPORT convention).

    gross = side·(exit_fill − entry_fill)·shares  (spread already crossed)
    mid_to_mid = side·(exit_mid − entry_mid)·shares
    spread = mid_to_mid − gross ; fees = 0.005·shares·2
    slippage = 0.5bps·(taker-leg notionals) ; net = gross − slippage − fees.
    """
    gross = side * (exit_fill - entry_fill) * shares
    mid_to_mid = side * (exit_mid - entry_mid) * shares
    spread = mid_to_mid - gross
    fees = FEE_PER_SHARE * shares * 2.0
    slip_notional = 0.0
    if entry_is_taker:
        slip_notional += entry_fill * shares
    if exit_is_taker:
        slip_notional += exit_fill * shares
    slippage = SLIP_BPS_PER_SIDE * FRAC_PER_BP * slip_notional
    net = gross - slippage - fees
    entry_notional = entry_fill * shares
    ret_bps = (net / entry_notional * 1e4) if entry_notional > 0 else float("nan")
    return Attribution(gross, mid_to_mid, spread, fees, slippage, net, ret_bps)
