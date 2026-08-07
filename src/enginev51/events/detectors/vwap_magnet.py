"""vwap_magnet detector — VWAP reversion on non-trend days (M3_REGISTRATION §3).

Registered a-priori thresholds live in PARAMS and mirror
research/experiments/M3_REGISTRATION.md. Point-in-time: a decision at 1-min bar
``i`` has ts = bars.ts[i] + 60s (the bar CLOSE) and may only read bars[0..i].

Emits one DetectorState per active decision minute (active states only). The A0
constructor (plans/constructor.py) owns entry/expire/EV-hurdle; this module owns
when the payer is active, its direction, and the stop/target anchors.
"""

from __future__ import annotations

import math
from datetime import time as dtime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import numpy as np

from enginev51.contracts import DetectorState

if TYPE_CHECKING:  # avoid a runtime import of the parallel-authored context module
    from enginev51.events.context import SessionContext

ET = ZoneInfo("America/New_York")
NS_PER_S = 1_000_000_000

# Registered (M3 §3) + honest micro-rules (flagged in the return message).
PARAMS: dict = {
    "decision_window_et": ("10:30", "14:30"),
    "sigma_dev_window": 30,          # trailing completed bars for σ_dev
    "sigma_dev_ddof": 1,             # sample std (unspecified in reg → simplest honest)
    "sigma_dev_includes_current_bar": True,  # bar i is completed at its close
    "dev_sigma_mult": 1.5,           # |dev| >= 1.5·σ_dev
    "min_dev_bps": 20.0,             # AND |dev| >= 20 bps
    "range_day_frac": 0.35,          # |ret from open| <= 0.35·(day range so far)
    "stop_dev_mult": 2.5,            # stop where |dev| reaches 2.5× entry |dev|
    "stop_min_bps": 20.0,            # min stop distance beyond decision price
    "expected_gross_mult": 0.8,      # 0.8·|dev| in bps
    "sigma_h_sqrt_horizon": 3.0,     # σ_h = σ_dev·1e4·sqrt(3)
    "rearm_min": 60,                 # suppress same-side re-emits for 60 min (reg re-arm)
    "hold_max_min": 90,              # registered hold_max_min
    "strength_ref_bps": 100.0,       # display-only normalization (NOT registered)
}


def _et_time(ts_ns: int) -> dtime:
    from datetime import datetime

    return datetime.fromtimestamp(ts_ns // NS_PER_S, tz=ET).time()


def _win_bounds() -> tuple[dtime, dtime]:
    a, b = PARAMS["decision_window_et"]
    ha, ma = (int(x) for x in a.split(":"))
    hb, mb = (int(x) for x in b.split(":"))
    return dtime(ha, ma), dtime(hb, mb)


def detect(ctx: SessionContext) -> list[DetectorState]:
    bars = ctx.bars
    n = bars.height
    win = PARAMS["sigma_dev_window"]
    if n < win:
        return []

    ts = bars["ts"].to_numpy()
    close = bars["close"].to_numpy().astype(float)
    open_arr = bars["open"].to_numpy().astype(float)
    cum_vwap = bars["cum_vwap"].to_numpy().astype(float)
    day_high = bars["day_high_run"].to_numpy().astype(float)
    day_low = bars["day_low_run"].to_numpy().astype(float)

    dev = np.where(cum_vwap != 0.0, (close - cum_vwap) / cum_vwap, 0.0)
    open0 = float(open_arr[0])
    w_start, w_end = _win_bounds()

    out: list[DetectorState] = []
    last_emit_ns: dict[int, int] = {}  # direction -> ts of last emit (re-arm)
    rearm_ns = PARAMS["rearm_min"] * 60 * NS_PER_S

    for i in range(win - 1, n):
        decision_ts = int(ts[i]) + 60 * NS_PER_S
        t = _et_time(decision_ts)
        if not (w_start <= t <= w_end):
            continue

        j0 = i - win + 1 if PARAMS["sigma_dev_includes_current_bar"] else i - win
        j1 = i + 1 if PARAMS["sigma_dev_includes_current_bar"] else i
        if j0 < 0:
            continue
        sigma_dev = float(np.std(dev[j0:j1], ddof=PARAMS["sigma_dev_ddof"]))

        dev0 = float(dev[i])
        adev = abs(dev0)
        if dev0 == 0.0:
            continue

        # range-day filter
        day_range = float(day_high[i] - day_low[i])
        if abs(float(close[i]) - open0) > PARAMS["range_day_frac"] * day_range:
            continue

        # activation
        if adev < PARAMS["dev_sigma_mult"] * sigma_dev:
            continue
        if adev * 1e4 < PARAMS["min_dev_bps"]:
            continue

        sgn = 1.0 if dev0 > 0 else -1.0
        direction = int(-sgn)

        # re-arm: suppress same-side within window
        prev = last_emit_ns.get(direction)
        if prev is not None and decision_ts - prev < rearm_ns:
            continue

        p0 = float(close[i])
        v = float(cum_vwap[i])
        # stop: dev extends to 2.5× entry |dev| (adverse), min 20 bps beyond p0
        dev_dist = v * (PARAMS["stop_dev_mult"] - 1.0) * adev
        min_dist = PARAMS["stop_min_bps"] / 1e4 * p0
        stop_dist = max(dev_dist, min_dist)
        stop_px = p0 + sgn * stop_dist

        t0_px = v  # target is session VWAP
        expected_gross_bps = PARAMS["expected_gross_mult"] * adev * 1e4
        sigma_h_bps = sigma_dev * 1e4 * math.sqrt(PARAMS["sigma_h_sqrt_horizon"])
        strength = min(1.0, adev * 1e4 / PARAMS["strength_ref_bps"])

        out.append(
            DetectorState(
                symbol=ctx.symbol,
                ts=decision_ts,
                payer="vwap_magnet",
                active=True,
                direction=direction,
                strength=strength,
                horizon_min=PARAMS["hold_max_min"],
                meta=(
                    ("stop_px", stop_px),
                    ("expected_gross_bps", expected_gross_bps),
                    ("t0_px", t0_px),
                    ("sigma_h_bps", sigma_h_bps),
                    ("dev_bps", dev0 * 1e4),
                    ("sigma_dev_bps", sigma_dev * 1e4),
                ),
            )
        )
        last_emit_ns[direction] = decision_ts

    return out
