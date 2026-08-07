"""gap_mr — opening-gap mean-reversion detector (M3_REGISTRATION §1).

Single decision at the 09:45 ET bar close. The gap is faded (direction opposite
the gap) only when it is statistically large AND the first 15 minutes did not
extend the move (an extended move reads as a trend day and stands the payer
down). All thresholds below mirror M3_REGISTRATION.md and are frozen.

PIT: the decision at the 09:45 bar close (ts = 09:44 bar OPEN + 60s) uses only
bars whose OPEN is <= the decision bar open (the first 15 minutes, indices
0..14 on complete data). Prior-session stats come from the SessionContext,
which sealed them to sessions strictly before this one.
"""

from __future__ import annotations

from enginev51.contracts import DetectorState
from enginev51.events.context import NS_PER_S, SessionContext, et_close_ns

# Registered thresholds (M3_REGISTRATION §1). Micro-details unspecified there are
# resolved to the simplest honest rule and flagged in the agent return message.
PARAMS: dict = {
    "sigma_mult": 0.75,            # |gap| >= 0.75 * sigma_d
    "min_gap_bps": 30.0,           # and |gap| >= 30 bps
    "extension_frac": 0.35,        # trend-day kill: first-15m extension past open
    "stop_gap_mult": 0.25,         # stop = adverse extreme +/- 0.25*|gap| (price)
    "min_stop_bps": 25.0,          # minimum stop distance from the 09:45 price
    "target0_halfway": 0.5,        # t0 = halfway 09:45-price -> prev_close
    "expected_gross_mult": 0.5,    # 0.5 * |dist(09:45 price, prev_close)| bps
    "sigma_h_div": 4.0,            # sigma_h = sigma_d / 4
    "hold_max_min": 120,           # registered hold_max_min (== horizon_min)
    "decision_et": (9, 45),        # 09:45 ET decision bar CLOSE
    "min_window_bars": 2,          # judgment call: minimum first-15m bars to act
    "strength_norm_bps": 100.0,    # judgment call: |gap_bps| -> strength scaler
}


def detect(ctx: SessionContext) -> list[DetectorState]:
    prev_close = ctx.prev_close
    if prev_close <= 0:
        return []

    h, m = PARAMS["decision_et"]
    decision_close_ns = et_close_ns(ctx.session, h, m)
    decision_open_ns = decision_close_ns - NS_PER_S * 60  # 09:44 bar OPEN

    bars = ctx.bars
    if bars.height == 0:
        return []
    dec = bars.filter(bars["ts"] == decision_open_ns)
    if dec.height == 0:
        return []  # decision bar (09:44 open) not present in the tape
    window = bars.filter(bars["ts"] <= decision_open_ns)  # first 15 minutes
    if window.height < PARAMS["min_window_bars"]:
        return []

    open0 = float(bars["open"][0])
    gap_px = open0 - prev_close
    gap = gap_px / prev_close
    gap_bps = gap * 1e4
    abs_gap_bps = abs(gap_bps)

    if abs_gap_bps < PARAMS["min_gap_bps"]:
        return []
    if abs_gap_bps < PARAMS["sigma_mult"] * ctx.sigma_d_bps:
        return []

    abs_gap_px = abs(gap_px)
    hi = float(window["high"].max())
    lo = float(window["low"].min())
    if gap_px > 0:  # gapped up: extension = highest print above the open
        extension = hi - open0
        adverse_extreme = hi          # adverse for a fade-short = upside
    else:           # gapped down: extension = lowest print below the open
        extension = open0 - lo
        adverse_extreme = lo          # adverse for a fade-long = downside
    if extension > PARAMS["extension_frac"] * abs_gap_px:
        return []  # move extended -> trend day -> stand down

    p945 = float(dec["close"][0])
    direction = -1 if gap_px > 0 else 1

    if direction < 0:  # fade short (gap up): stop above
        stop_px = adverse_extreme + PARAMS["stop_gap_mult"] * abs_gap_px
        stop_px = max(stop_px, p945 * (1.0 + PARAMS["min_stop_bps"] / 1e4))
    else:              # fade long (gap down): stop below
        stop_px = adverse_extreme - PARAMS["stop_gap_mult"] * abs_gap_px
        stop_px = min(stop_px, p945 * (1.0 - PARAMS["min_stop_bps"] / 1e4))

    t0_px = (p945 + prev_close) / 2.0  # halfway 09:45 price -> prev_close
    t1_px = prev_close

    expected_gross_bps = PARAMS["expected_gross_mult"] * abs(p945 - prev_close) / p945 * 1e4
    sigma_h_bps = ctx.sigma_d_bps / PARAMS["sigma_h_div"]
    strength = min(1.0, abs_gap_bps / PARAMS["strength_norm_bps"])

    meta = (
        ("stop_px", stop_px),
        ("expected_gross_bps", expected_gross_bps),
        ("t0_px", t0_px),
        ("t1_px", t1_px),
        ("sigma_h_bps", sigma_h_bps),
        ("gap_bps", gap_bps),
    )
    return [
        DetectorState(
            symbol=ctx.symbol,
            ts=decision_close_ns,
            payer="gap_mr",
            active=True,
            direction=direction,
            strength=strength,
            horizon_min=PARAMS["hold_max_min"],
            meta=meta,
        )
    ]
