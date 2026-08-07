"""cascade detector — liquidity-cascade / V-reversal exhaustion (M3_REGISTRATION §4).

Registered a-priori thresholds live in PARAMS and mirror
research/experiments/M3_REGISTRATION.md. PIT: a decision at 1-min bar ``i`` has
ts = bars.ts[i] + 60s and may read bars[0..i] and event_bars seconds < that ts.

A flush is a signed move from a rolling extreme to the current extreme with
|move| >= 2.5·σ_30m AND flush-window volume >= 3× the same-clock 20-session
average increment AND median event-bar spread (last 5 min) >= 2× session median.
The entry ARMS at stabilization: 5 bars with no new flush extreme AND trailing
5-min OFI opposing the flush. Emits against the flush. If event_bars is None the
spread/OFI prongs are unevaluable → emit nothing (structlog note).
"""

from __future__ import annotations

import math
from datetime import time as dtime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import numpy as np
import structlog

from enginev51.contracts import DetectorState

if TYPE_CHECKING:
    from enginev51.events.context import SessionContext

ET = ZoneInfo("America/New_York")
NS_PER_S = 1_000_000_000
log = structlog.get_logger(__name__)

# Registered (M3 §4) + honest micro-rules (flagged in the return message).
PARAMS: dict = {
    "decision_window_et": ("09:45", "14:30"),
    "lookback_bars": 30,             # flush search window (<= 30 min)
    "sigma_30m_window": 30,          # last 30 1-min log returns
    "sigma_30m_ddof": 1,             # sample std (unspecified in reg)
    "flush_sigma_mult": 2.5,         # |move| >= 2.5·σ_30m
    "volume_mult": 3.0,              # flush vol >= 3× avg same-clock increment
    "spread_mult": 2.0,              # last-5-min median spread >= 2× session median
    "spread_window_min": 5,
    "stabilize_bars": 5,             # bars with no new extreme to arm
    "ofi_window_min": 5,             # trailing OFI window
    "stop_amp_frac": 0.3,            # stop = extreme -/+ 0.3·amplitude
    "t0_retrace": 0.382,             # first target retrace
    "t1_retrace": 0.618,             # second target retrace
    "expected_gross_retrace": 0.382, # 0.382·amplitude in bps
    "episode_reset_retrace": 0.5,    # episode resets on 50% retrace
    "episode_reset_min": 60,         # ...or after 60 min
    "hold_max_min": 120,             # registered hold_max_min
    "strength_ref_bps": 150.0,       # display-only normalization (NOT registered)
}


def _et_time(ts_ns: int) -> dtime:
    from datetime import datetime

    return datetime.fromtimestamp(ts_ns // NS_PER_S, tz=ET).time()


def _win_bounds() -> tuple[dtime, dtime]:
    a, b = PARAMS["decision_window_et"]
    ha, ma = (int(x) for x in a.split(":"))
    hb, mb = (int(x) for x in b.split(":"))
    return dtime(ha, ma), dtime(hb, mb)


def _median_nonnan(a: np.ndarray) -> float | None:
    a = a[~np.isnan(a)]
    if a.size == 0:
        return None
    return float(np.median(a))


def detect(ctx: SessionContext) -> list[DetectorState]:
    if ctx.event_bars is None:
        log.info("cascade.skip_no_event_bars", symbol=ctx.symbol, session=ctx.session)
        return []

    bars = ctx.bars
    n = bars.height
    sw = PARAMS["sigma_30m_window"]
    if n <= sw:  # need sw+1 closes for sw returns
        return []

    ts = bars["ts"].to_numpy()
    high = bars["high"].to_numpy().astype(float)
    low = bars["low"].to_numpy().astype(float)
    close = bars["close"].to_numpy().astype(float)
    volume = bars["volume"].to_numpy().astype(float)
    minute_idx = bars["minute_idx"].to_numpy().astype(int)

    logret = np.zeros(n, dtype=float)
    logret[1:] = np.log(close[1:] / close[:-1])

    avg_cum = np.asarray(ctx.avg_cum_volume_by_minute, dtype=float)

    eb = ctx.event_bars
    eb_ts = eb["ts"].to_numpy()
    eb_spread = eb["spread_bps_close"].to_numpy().astype(float)
    eb_ofi = eb["ofi"].to_numpy().astype(float)

    w_start, w_end = _win_bounds()
    lookback = PARAMS["lookback_bars"]
    stab = PARAMS["stabilize_bars"]
    spread_win_ns = PARAMS["spread_window_min"] * 60 * NS_PER_S
    ofi_win_ns = PARAMS["ofi_window_min"] * 60 * NS_PER_S
    reset_ns = PARAMS["episode_reset_min"] * 60 * NS_PER_S

    out: list[DetectorState] = []
    # episode per direction: (emit_ts, extreme_px, amplitude)
    episodes: dict[int, tuple[int, float, float]] = {}

    for i in range(sw, n):
        decision_ts = int(ts[i]) + 60 * NS_PER_S
        t = _et_time(decision_ts)
        if not (w_start <= t <= w_end):
            continue

        sigma_30m = float(
            np.std(logret[i - sw + 1 : i + 1], ddof=PARAMS["sigma_30m_ddof"])
        ) * math.sqrt(sw)
        if sigma_30m <= 0.0:
            continue

        w0 = max(0, i - lookback + 1)

        # spread/OFI prongs share the trailing windows; compute once per bar
        sess_mask = eb_ts < decision_ts
        last5_mask = (eb_ts >= decision_ts - spread_win_ns) & (eb_ts < decision_ts)
        ofi_mask = (eb_ts >= decision_ts - ofi_win_ns) & (eb_ts < decision_ts)
        med_sess = _median_nonnan(eb_spread[sess_mask])
        med_last5 = _median_nonnan(eb_spread[last5_mask])
        sum_ofi = float(np.nansum(eb_ofi[ofi_mask]))
        spread_ok = (
            med_sess is not None
            and med_last5 is not None
            and med_sess > 0.0
            and med_last5 >= PARAMS["spread_mult"] * med_sess
        )

        for flush_dir in (-1, 1):  # -1 = down-flush (peak→trough), +1 = up-flush
            if flush_dir == -1:
                p = w0 + int(np.argmax(high[w0 : i + 1]))
                tr = p + int(np.argmin(low[p : i + 1]))
                if tr <= p:
                    continue
                extreme_px = float(low[tr])
                amplitude = float(high[p]) - float(low[tr])
                new_extreme_idx = tr
                win_start = p
                trade_dir = 1  # against a down-flush = long
                ofi_ok = sum_ofi > 0.0
            else:
                tr = w0 + int(np.argmin(low[w0 : i + 1]))
                p = tr + int(np.argmax(high[tr : i + 1]))
                if p <= tr:
                    continue
                extreme_px = float(high[p])
                amplitude = float(high[p]) - float(low[tr])
                new_extreme_idx = p
                win_start = tr
                trade_dir = -1  # against an up-flush = short
                ofi_ok = sum_ofi < 0.0

            if amplitude <= 0.0:
                continue

            flush_ret = math.log(float(high[p]) / float(low[tr]))
            if flush_ret < PARAMS["flush_sigma_mult"] * sigma_30m:
                continue

            # volume prong: flush-window volume vs 3× avg same-clock increment
            flush_vol = float(np.sum(volume[win_start : i + 1]))
            m_lo = int(minute_idx[win_start])
            m_hi = int(minute_idx[i])
            base = float(avg_cum[m_lo - 1]) if m_lo > 0 else 0.0
            sum_inc = float(avg_cum[m_hi]) - base
            if flush_vol < PARAMS["volume_mult"] * sum_inc:
                continue

            if not spread_ok:
                continue

            # stabilization: extreme is >= stab bars old, OFI opposes the flush
            if (i - new_extreme_idx) < stab:
                continue
            if not ofi_ok:
                continue

            # episode hygiene: one state per direction per episode
            ep = episodes.get(trade_dir)
            if ep is not None:
                emit_ts, ep_ex, ep_amp = ep
                reset_level = (
                    ep_ex + PARAMS["episode_reset_retrace"] * ep_amp
                    if trade_dir == 1
                    else ep_ex - PARAMS["episode_reset_retrace"] * ep_amp
                )
                crossed = (
                    float(close[i]) >= reset_level
                    if trade_dir == 1
                    else float(close[i]) <= reset_level
                )
                if (decision_ts - emit_ts) < reset_ns and not crossed:
                    continue  # still inside the live episode

            s = PARAMS["stop_amp_frac"] * amplitude
            r0 = PARAMS["t0_retrace"] * amplitude
            r1 = PARAMS["t1_retrace"] * amplitude
            if trade_dir == 1:  # long
                stop_px = extreme_px - s
                t0_px = extreme_px + r0
                t1_px = extreme_px + r1
            else:  # short
                stop_px = extreme_px + s
                t0_px = extreme_px - r0
                t1_px = extreme_px - r1

            expected_gross_bps = (
                PARAMS["expected_gross_retrace"] * amplitude / float(close[i]) * 1e4
            )
            sigma_h_bps = sigma_30m * 1e4
            strength = min(1.0, amplitude / float(close[i]) * 1e4 / PARAMS["strength_ref_bps"])

            out.append(
                DetectorState(
                    symbol=ctx.symbol,
                    ts=decision_ts,
                    payer="cascade",
                    active=True,
                    direction=trade_dir,
                    strength=strength,
                    horizon_min=PARAMS["hold_max_min"],
                    meta=(
                        ("stop_px", stop_px),
                        ("expected_gross_bps", expected_gross_bps),
                        ("t0_px", t0_px),
                        ("t1_px", t1_px),
                        ("sigma_h_bps", sigma_h_bps),
                        ("amplitude", amplitude),
                        ("flush_ret_bps", flush_ret * 1e4),
                    ),
                )
            )
            episodes[trade_dir] = (decision_ts, extreme_px, amplitude)

    return out
