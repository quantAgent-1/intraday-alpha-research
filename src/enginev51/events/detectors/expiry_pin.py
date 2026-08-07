"""expiry_pin detector — monthly-opex pinning (M3_REGISTRATION §5, exploratory).

Registered a-priori thresholds live in PARAMS and mirror
research/experiments/M3_REGISTRATION.md. PIT: a decision at 1-min bar ``i`` has
ts = bars.ts[i] + 60s and reads bars[0..i]. Only fires on monthly-opex sessions
(ctx.is_monthly_opex, from flows/ffcal). Smallest budget; exploratory flag.
"""

from __future__ import annotations

from datetime import time as dtime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from enginev51.contracts import DetectorState

if TYPE_CHECKING:
    from enginev51.events.context import SessionContext

ET = ZoneInfo("America/New_York")
NS_PER_S = 1_000_000_000

# Registered (M3 §5) + honest micro-rules (flagged in the return message).
PARAMS: dict = {
    "decision_window_et": ("13:00", "14:30"),
    "step_min": 5,                   # step every 5 minutes
    "grid_hi": 5.0,                  # $5 strike grid for price >= threshold
    "grid_lo": 2.5,                  # $2.50 grid below
    "grid_price_threshold": 200.0,
    "min_dist_frac": 0.0005,         # 0.05% < |price-strike|/price
    "max_dist_frac": 0.003,          # ... <= 0.30%
    "stop_far_frac": 0.006,          # stop 0.6% beyond the far side
    "rearm_min": 60,                 # suppress same-side re-emits for 60 min
    "hold_max_min": 170,             # registered hold_max_min (hold to curfew)
    "strength_ref_frac": 0.003,      # display-only normalization (NOT registered)
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
    if not ctx.is_monthly_opex:
        return []

    bars = ctx.bars
    n = bars.height
    if n == 0:
        return []

    ts = bars["ts"].to_numpy()
    close = bars["close"].to_numpy().astype(float)
    w_start, w_end = _win_bounds()
    step = PARAMS["step_min"]

    out: list[DetectorState] = []
    last_emit_ns: dict[int, int] = {}
    rearm_ns = PARAMS["rearm_min"] * 60 * NS_PER_S

    for i in range(n):
        decision_ts = int(ts[i]) + 60 * NS_PER_S
        t = _et_time(decision_ts)
        if not (w_start <= t <= w_end):
            continue
        if t.second != 0 or t.minute % step != 0:
            continue

        px = float(close[i])
        grid = PARAMS["grid_hi"] if px >= PARAMS["grid_price_threshold"] else PARAMS["grid_lo"]
        strike = round(px / grid) * grid
        dist = abs(px - strike)
        dist_frac = dist / px

        if not (PARAMS["min_dist_frac"] < dist_frac <= PARAMS["max_dist_frac"]):
            continue

        direction = 1 if strike > px else -1
        prev = last_emit_ns.get(direction)
        if prev is not None and decision_ts - prev < rearm_ns:
            continue

        # stop 0.6% beyond the side AWAY from the strike (opposite the move)
        if direction == 1:
            stop_px = px * (1.0 - PARAMS["stop_far_frac"])
        else:
            stop_px = px * (1.0 + PARAMS["stop_far_frac"])

        t0_px = strike
        expected_gross_bps = dist_frac * 1e4
        strength = min(1.0, dist_frac / PARAMS["strength_ref_frac"])

        out.append(
            DetectorState(
                symbol=ctx.symbol,
                ts=decision_ts,
                payer="expiry_pin",
                active=True,
                direction=direction,
                strength=strength,
                horizon_min=PARAMS["hold_max_min"],
                meta=(
                    ("stop_px", stop_px),
                    ("expected_gross_bps", expected_gross_bps),
                    ("t0_px", t0_px),
                    ("sigma_h_bps", 0.0),
                    ("strike", float(strike)),
                    ("dist_bps", dist_frac * 1e4),
                ),
            )
        )
        last_emit_ns[direction] = decision_ts

    return out
