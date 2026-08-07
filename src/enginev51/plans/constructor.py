"""A0 plan constructor: DetectorState -> TradePlan per the REGISTERED templates.

Every numeric rule here is registered in research/experiments/M3_REGISTRATION.md
(2026-07-15, a-priori). Changing any of them after economics exist is a new
counted variant — do not "tune" this file casually.

Contract with detectors: a DetectorState carries payer-specific anchors in its
`meta` tuple (prices in absolute $ unless suffixed _bps):
  required: 'stop_px', 'expected_gross_bps'
  targets:  't0_px' (+ optional 't1_px'), fracs default to the registered
            per-payer split; letf_window has no targets.
The constructor owns: entry style (limit-join vs market), expire/chase, windows,
EV hurdle, valid_until, curfew, and schema assembly. Detectors own: when a payer
is active, direction, and where the payer's own structure puts stop/targets.
"""

from __future__ import annotations

from datetime import datetime
from datetime import time as dtime
from zoneinfo import ZoneInfo

from enginev51.contracts import DetectorState
from enginev51.plans.schema import EntrySpec, StopSpec, TargetSpec, TradePlan

ET = ZoneInfo("America/New_York")
NS_PER_S = 1_000_000_000

# Registered per-payer construction constants (M3_REGISTRATION.md).
PAYER_RULES: dict[str, dict] = {
    "gap_mr": {
        "entry": "limit_join", "expire_s": 180, "chase": True,
        "hold_max_min": 120, "target_fracs": (0.6, 0.4),
        "window": (dtime(9, 45), dtime(14, 30)),
    },
    "letf_window": {
        "entry": "market", "expire_s": 0, "chase": False,
        "hold_max_min": 55, "target_fracs": (),
        "window": (dtime(15, 0), dtime(15, 10)),
    },
    "vwap_magnet": {
        "entry": "limit_join", "expire_s": 300, "chase": False,
        "hold_max_min": 90, "target_fracs": (1.0,),
        "window": (dtime(10, 30), dtime(14, 30)),
    },
    "cascade": {
        "entry": "limit_join", "expire_s": 120, "chase": True,
        "hold_max_min": 120, "target_fracs": (0.6, 0.4),
        "window": (dtime(9, 45), dtime(14, 30)),
    },
    "expiry_pin": {
        "entry": "limit_join", "expire_s": 300, "chase": False,
        "hold_max_min": 170, "target_fracs": (1.0,),
        "window": (dtime(13, 0), dtime(14, 30)),
    },
}

VALID_FOR_S = 120  # registered: plans are executable for 120 s
MIN_GROSS_BPS = 8.0  # registered EV hurdle floor
HURDLE_COST_MULT = 2.0  # expected_gross >= 2 x RT cost


def _meta_get(state: DetectorState, key: str) -> float | None:
    for k, v in state.meta:
        if k == key:
            return float(v)
    return None


def _in_window(ts: int, window: tuple[dtime, dtime]) -> bool:
    t_et = datetime.fromtimestamp(ts / 1e9, tz=ET).time()
    return window[0] <= t_et <= window[1]


def build_plan(
    state: DetectorState,
    *,
    bid: float,
    ask: float,
    rt_cost_bps: float,
    curfew_ts: int,
    plan_seq: int,
) -> TradePlan | None:
    """Assemble the A0 TradePlan for an active DetectorState, or None if gated.

    `bid`/`ask` are the prevailing NBBO at the decision time (the detector's
    ts). Gates, in registered order: active+direction, entry window, EV hurdle.
    """
    if not state.active or state.direction == 0:
        return None
    rules = PAYER_RULES.get(state.payer)
    if rules is None:
        raise ValueError(f"unregistered payer: {state.payer}")
    if not _in_window(state.ts, rules["window"]):
        return None

    expected_gross = _meta_get(state, "expected_gross_bps")
    stop_px = _meta_get(state, "stop_px")
    if expected_gross is None or stop_px is None:
        raise ValueError(f"{state.payer} detector must supply stop_px and expected_gross_bps")
    if expected_gross < max(HURDLE_COST_MULT * rt_cost_bps, MIN_GROSS_BPS):
        return None

    side = state.direction
    if rules["entry"] == "market":
        entry = EntrySpec(type="market", limit_price=None, expire_s=0, chase_at_expire=False)
        entry_ref = ask if side > 0 else bid
    else:  # limit JOIN: buy at bid / sell at ask (earn the spread if it comes to us)
        limit = bid if side > 0 else ask
        entry = EntrySpec(
            type="limit", limit_price=limit, expire_s=rules["expire_s"],
            chase_at_expire=rules["chase"],
        )
        entry_ref = limit

    # sanity vs schema invariants; a detector anchor on the wrong side is a bug
    if (side > 0 and stop_px >= entry_ref) or (side < 0 and stop_px <= entry_ref):
        return None

    targets: list[TargetSpec] = []
    fracs = rules["target_fracs"]
    for i, frac in enumerate(fracs):
        px = _meta_get(state, f"t{i}_px")
        if px is None:
            return None
        if (side > 0 and px <= entry_ref) or (side < 0 and px >= entry_ref):
            return None  # target on wrong side (e.g. gap already filled past it)
        targets.append(TargetSpec(price=px, frac=frac))

    return TradePlan(
        plan_id=f"{state.payer}-{state.symbol}-{state.ts}-{plan_seq}",
        symbol=state.symbol,
        ts_authored=state.ts,
        valid_until=state.ts + VALID_FOR_S * NS_PER_S,
        side=side,
        entry=entry,
        stop=StopSpec(price=stop_px, basis=state.payer),
        targets=tuple(targets),
        hold_max_min=rules["hold_max_min"],
        curfew_ts=curfew_ts,
        expected_gross_bps=expected_gross,
        expected_net_bps=expected_gross - rt_cost_bps,
        sigma_h_bps=_meta_get(state, "sigma_h_bps") or 0.0,
        p_win=0.5,  # A0 has no model; calibration scored from here
        ev_ratio=expected_gross / max(rt_cost_bps, 1e-9),
        confidence=0.5,
        payer=state.payer,
        horizon_min=state.horizon_min,
        model_ids=("A0",),
        meta=state.meta,
    )
