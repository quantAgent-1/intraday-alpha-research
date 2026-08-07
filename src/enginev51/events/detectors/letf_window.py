"""letf_window — leveraged-ETF close-rebalance pressure detector (M3_REGISTRATION §2).

Single decision at the 15:00 ET bar close. On a large index day-move the
daily-reset leveraged-ETF complex must trade WITH the move into the close; the
detector trades that documented flow (market entry, hold to curfew, no target).

PIT: the 15:00 decision (ts = 14:59 bar OPEN + 60s) uses the traded symbol's and
the mapped index's bars up to that instant only. The rebalance-demand estimate
is a pure function of the observed intraday index return.
"""

from __future__ import annotations

from enginev51.contracts import DetectorState
from enginev51.events.context import NS_PER_S, SessionContext, et_close_ns
from enginev51.flows import letf

# Registered thresholds (M3_REGISTRATION §2). Frozen.
PARAMS: dict = {
    "min_index_ret": 0.005,             # ACTIVE iff |r| >= 0.5%
    "stop_range_mult": 1.2,             # stop = price -/+ 1.2 * avg 15:00-15:45 range
    "expected_gross_per_unit_bps": 10.0,  # 10 bps per 0.5% of |r|
    "expected_gross_cap_bps": 30.0,     # capped at 30 bps
    "hold_max_min": 55,                 # registered hold_max_min (== horizon_min)
    "decision_et": (15, 0),             # 15:00 ET decision bar CLOSE
}


def detect(ctx: SessionContext) -> list[DetectorState]:
    if ctx.index_bars is None:
        return []
    idx_label = _index_label(ctx.symbol)
    if idx_label is None:
        return []

    avg_range = ctx.avg_range_1500_1545_bps
    if avg_range != avg_range or avg_range <= 0:  # NaN or non-positive -> no stop
        return []

    h, m = PARAMS["decision_et"]
    decision_close_ns = et_close_ns(ctx.session, h, m)
    decision_open_ns = decision_close_ns - NS_PER_S * 60  # 14:59 bar OPEN

    bars = ctx.bars
    dec = bars.filter(bars["ts"] == decision_open_ns)
    if dec.height == 0:
        return []  # no 15:00 bar (e.g. half day)
    p1500 = float(dec["close"][0])

    ib = ctx.index_bars
    idx_dec = ib.filter(ib["ts"] == decision_open_ns)
    if idx_dec.height == 0:
        return []
    idx_open0 = float(ib["open"][0])
    if idx_open0 <= 0:
        return []
    idx_close = float(idx_dec["close"][0])
    r = (idx_close - idx_open0) / idx_open0
    if abs(r) < PARAMS["min_index_ret"]:
        return []

    complex_out = letf.complex_demand(None, {idx_label: r})
    bucket = complex_out.get(idx_label)
    if bucket is None:
        return []
    demand = float(bucket["demand_usd"])
    if demand == 0.0:
        return []
    direction = 1 if demand > 0 else -1

    if direction > 0:  # buy-side flow: adverse is down -> stop below
        stop_px = p1500 * (1.0 - PARAMS["stop_range_mult"] * avg_range / 1e4)
    else:              # sell-side flow: adverse is up -> stop above
        stop_px = p1500 * (1.0 + PARAMS["stop_range_mult"] * avg_range / 1e4)

    expected_gross_bps = min(
        PARAMS["expected_gross_per_unit_bps"] * abs(r) / PARAMS["min_index_ret"],
        PARAMS["expected_gross_cap_bps"],
    )
    sigma_h_bps = avg_range
    strength = min(1.0, expected_gross_bps / PARAMS["expected_gross_cap_bps"])

    meta = (
        ("stop_px", stop_px),
        ("expected_gross_bps", expected_gross_bps),
        ("sigma_h_bps", sigma_h_bps),
        ("index_ret_bps", r * 1e4),
        ("demand_usd", demand),
    )
    return [
        DetectorState(
            symbol=ctx.symbol,
            ts=decision_close_ns,
            payer="letf_window",
            active=True,
            direction=direction,
            strength=strength,
            horizon_min=PARAMS["hold_max_min"],
            meta=meta,
        )
    ]


def _index_label(symbol: str) -> str | None:
    from enginev51.events.context import INDEX_MAP

    return INDEX_MAP.get(symbol.upper())
