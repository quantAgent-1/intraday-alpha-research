"""Sequential per-session state machine: strategy + risk + fills.

BUILD-SPEC §3, A8, A9; REGISTRATION §2-3. Port target: engineV2
``reversion_nb.evaluate`` (entry/exit rule), ``riskgate_nb.risk_tick`` (TP →
hard stop → trailing → deadline on sticky microprice) + ``can_open_entry`` /
``can_strategy_exit``, and ``event_loop_nb.run_day`` (order of operations,
latency fills, curfew force-flat). The engineV2 tick loop is mapped to a 1 s bar
loop — the declared substrate difference the anchor (§7) guards.

Order within bar i (event_loop_nb.run_day):
  1. OU sample (volume>0 bar) → ε ring.
  2. drain pending entry fill → open position.
  3. drain pending exit fill → close + record.
  4. curfew force-flat (once, first bar >= 15:50 ET).
  5. OU recalibrate (every 60 s).
  6. risk_tick (position open, no pending exit) → schedule exit at i+2.
  7. strategy evaluate → schedule entry / strategy-exit at i+2 (taker) or the
     maker touch bar. Risk runs BEFORE strategy; an entry proposal suppresses
     same-bar strategy exit (evaluate returns the first hit).

Canonical entry model is a run parameter: "taker" (anchor / attribution; fills
at trigger+2 BBO, every trigger opens) or "maker" (the system under test; resting
limit at bid/ask, touch within 60 s, unfilled = no trade). The OTHER model is
computed per opened trade as an attribution OVERLAY at the SAME shares and the
SAME canonical exit (BUILD-SPEC §5 "re-price the same trade stream, no
re-simulation"); the maker streams therefore inherit the canonical exit timing.
"""

from __future__ import annotations

import math

import numpy as np

from enginev51.reversion.features import GateBaseline, SessionFeatures, eval_gates
from enginev51.reversion.fills import (
    MAKER_CANCEL_BARS,
    TAKER_LATENCY_BARS,
    attribute,
    keep_hash_50,
    maker_fill_bar,
    size_and_levels,
)
from enginev51.reversion.ou import OUCalibrator, OUThresholds

# Exit-reason codes (engineV2 riskgate_nb EXIT_*).
EXIT_TP = 1
EXIT_HARD = 2
EXIT_TRAILING = 3
EXIT_MAX_HOLD = 4
EXIT_STRATEGY = 5
EXIT_FORCE = 6

# engineV2 ReversionDefaults / RiskDefaults.
RHO_MAX_LONG = -0.2
RHO_MIN_SHORT = 0.2
OFI_NEUTRAL = 1.0
MAX_SPREAD_BPS = 30.0
TREND_THR_BPS = 50.0
TREND_DIRECTIONAL = False
BAND_K = 1.5
TRAIL_ACTIVATE_BPS = 250.0
TRAIL_K_SIGMA = 2.0
MIN_TRAILING_SIGMA_BPS = 20.0
MIN_HOLD_BARS = 30
COOLDOWN_BARS = 5
STOP_COOLDOWN_BARS = 60
DAILY_LOSS_USD = 500.0
BLACKOUTS_ET = ((9 * 60 + 30, 9 * 60 + 40), (15 * 60 + 50, 16 * 60))
CURFEW_MIN_ET = 15 * 60 + 50


def _in_blackout(et_min: int) -> bool:
    for a, b in BLACKOUTS_ET:
        if a <= et_min <= b:
            return True
    return False


def _evaluate(
    *, eps: float, thr: OUThresholds, rho: float, ofi_5s: float, micro: float,
    vwap: float, spread: float, sigma_5m: float, vwap_30m: float, midprice: float,
) -> tuple[int, int]:
    """engineV2 reversion_nb.evaluate → (action, side). action: 0 none, 1 entry,
    2 exit. First hit wins (entry-long → entry-short → exit-long → exit-short)."""
    if thr is None or not thr.is_fresh:
        return 0, 0
    entry_long, exit_long = thr.entry_long, thr.exit_long
    entry_short, exit_short = thr.entry_short, thr.exit_short
    if math.isnan(eps):
        return 0, 0
    if math.isnan(entry_long) or math.isnan(exit_long):
        return 0, 0
    if math.isnan(rho) or math.isnan(ofi_5s) or math.isnan(micro) or math.isnan(vwap):
        return 0, 0
    if not math.isnan(spread) and spread > MAX_SPREAD_BPS:
        return 0, 0

    gate_long = False
    gate_short = False
    # require_positive_kappa (engineV2 params[6]=1); kappa/sigma are the fit
    # values (>0 whenever fresh), so this is a faithful no-op when fresh.
    kappa, ou_sigma = thr.kappa, thr.sigma
    if not math.isnan(kappa) and (not math.isfinite(kappa) or kappa <= 0.0):
        gate_long = gate_short = True
    if not math.isnan(ou_sigma) and (not math.isfinite(ou_sigma) or ou_sigma <= 0.0):
        gate_long = gate_short = True

    # Trend filter (non-directional): |mid − vwap_30m|/vwap_30m·1e4 > 50 bps.
    if (not math.isnan(vwap_30m)) and vwap_30m > 0.0 and (not math.isnan(midprice)):
        drift_bps = 1e4 * (midprice - vwap_30m) / vwap_30m
        if TREND_DIRECTIONAL:
            if drift_bps < -TREND_THR_BPS:
                gate_long = True
            if drift_bps > TREND_THR_BPS:
                gate_short = True
        elif abs(drift_bps) > TREND_THR_BPS:
            gate_long = gate_short = True

    band_up = vwap + BAND_K * sigma_5m if not math.isnan(sigma_5m) else math.nan
    band_lo = vwap - BAND_K * sigma_5m if not math.isnan(sigma_5m) else math.nan

    # ENTRY LONG
    if (not gate_long) and eps <= entry_long and rho > RHO_MAX_LONG and ofi_5s > -OFI_NEUTRAL:
        return 1, 1
    # ENTRY SHORT
    if (
        (not gate_short) and (not math.isnan(entry_short))
        and eps >= entry_short and rho < RHO_MIN_SHORT and ofi_5s < OFI_NEUTRAL
    ):
        return 1, -1
    # EXIT LONG
    if eps >= exit_long or ((not math.isnan(band_up)) and micro >= band_up):
        return 2, 1
    # EXIT SHORT
    if ((not math.isnan(exit_short)) and eps <= exit_short) or (
        (not math.isnan(band_lo)) and micro <= band_lo
    ):
        return 2, -1
    return 0, 0


def _curfew_bar(et_minute: np.ndarray) -> int:
    idx = np.nonzero(et_minute >= CURFEW_MIN_ET)[0]
    return int(idx[0]) if idx.size else et_minute.size


def run_session(
    feat: SessionFeatures, symbol: str, session: str,
    calibrator: OUCalibrator, baseline: GateBaseline,
    *, entry_model: str, max_hold_bars: int,
) -> list[dict]:
    """Run one session; return one record per raw entry trigger."""
    if entry_model not in ("taker", "maker"):
        raise ValueError(f"entry_model must be taker|maker, got {entry_model!r}")
    calibrator.reset()
    n = feat.ts.size
    ts = feat.ts
    et = feat.et_minute
    mid = feat.mid
    bid = feat.bid
    ask = feat.ask
    px_low = feat.px_low
    px_high = feat.px_high
    micro = feat.micro
    sigma5 = feat.sigma_5m
    vol = feat.volume
    curfew_bar = _curfew_bar(et)

    records: list[dict] = []

    pos: dict | None = None
    pend_entry: dict | None = None
    pend_exit: dict | None = None
    last_close_bar = -10**9
    last_stop_close_bar = -10**9
    daily_gross = 0.0
    eod_done = False

    def _open(fill_bar: int, side: int, entry_fill: float, ctx: dict) -> None:
        nonlocal pos
        sig = sigma5[fill_bar]
        sized = size_and_levels(entry_fill, side, sig)
        pos = {
            "side": side,
            "entry_fill": entry_fill,
            "entry_mid": mid[fill_bar],
            "entry_bar": fill_bar,
            "shares": sized.shares,
            "hard_stop": sized.hard_stop,
            "take_profit": sized.take_profit,
            "trailing": None,
            "high_water": entry_fill,
            "deadline_bar": fill_bar + max_hold_bars,
            "ctx": ctx,
        }

    def _close(exit_bar: int, reason: int) -> None:
        nonlocal pos, daily_gross, last_close_bar, last_stop_close_bar
        assert pos is not None
        side = pos["side"]
        shares = pos["shares"]
        exit_fill = bid[exit_bar] if side > 0 else ask[exit_bar]
        exit_mid = mid[exit_bar]
        ctx = pos["ctx"]
        t0 = ctx["trigger_bar"]

        # Canonical attribution (entry per entry_model; exit taker).
        canon = attribute(
            side=side, shares=shares,
            entry_fill=pos["entry_fill"], exit_fill=exit_fill,
            entry_mid=pos["entry_mid"], exit_mid=exit_mid,
            entry_is_taker=(entry_model == "taker"), exit_is_taker=True,
        )

        # Taker overlay (or canonical, if taker mode).
        tk_bar = t0 + TAKER_LATENCY_BARS
        if tk_bar < n:
            tk_entry = ask[tk_bar] if side > 0 else bid[tk_bar]
            tk_entry_mid = mid[tk_bar]
        else:
            tk_entry = pos["entry_fill"]
            tk_entry_mid = pos["entry_mid"]
        taker = attribute(
            side=side, shares=shares, entry_fill=tk_entry, exit_fill=exit_fill,
            entry_mid=tk_entry_mid, exit_mid=exit_mid, entry_is_taker=True, exit_is_taker=True,
        )

        # Maker overlay (or canonical, if maker mode): resting limit at bid/ask@t0.
        mk_limit = bid[t0] if side > 0 else ask[t0]
        mk_touch = maker_fill_bar(px_low, px_high, t0, side, mk_limit, strict=False)
        mk_through = maker_fill_bar(px_low, px_high, t0, side, mk_limit, strict=True)
        maker_filled = mk_touch is not None and mk_touch <= exit_bar
        maker_through = mk_through is not None and mk_through <= exit_bar and maker_filled
        if maker_filled:
            mk_entry_mid = mid[mk_touch]
            maker = attribute(
                side=side, shares=shares, entry_fill=mk_limit, exit_fill=exit_fill,
                entry_mid=mk_entry_mid, exit_mid=exit_mid, entry_is_taker=False, exit_is_taker=True,
            )
            fill_wait_s = int(mk_touch - t0)
        else:
            maker = None
            fill_wait_s = -1

        daily_gross += canon.gross_usd

        last_close_bar = exit_bar
        if reason in (EXIT_HARD, EXIT_TRAILING):
            last_stop_close_bar = exit_bar

        rec = dict(ctx)
        rec.update({
            "opened": True,
            "entry_open_bar": int(pos["entry_bar"]),
            "entry_ts": int(ts[pos["entry_bar"]]),
            "shares": int(shares),
            "hard_stop": float(pos["hard_stop"]),
            "take_profit": float(pos["take_profit"]),
            "exit_bar": int(exit_bar),
            "exit_ts": int(ts[exit_bar]),
            "exit_reason": int(reason),
            "hold_s": float(ts[exit_bar] - ts[pos["entry_bar"]]) / 1e9,
            "taker_entry_px": float(tk_entry),
            "taker_exit_px": float(exit_fill),
            "taker_gross": taker.gross_usd,
            "taker_mid_to_mid": taker.mid_to_mid_usd,
            "taker_spread": taker.spread_usd,
            "taker_fees": taker.fees_usd,
            "taker_slippage": taker.slippage_usd,
            "taker_net": taker.net_usd,
            "taker_ret_bps": taker.ret_bps,
            # maker_posted: a real resting maker order existed at t0 only in maker
            # mode (in taker mode the maker columns are an attribution overlay, not
            # a posted order). Drives the §3/§5 fill rate = filled / posted.
            "maker_posted": bool(entry_model == "maker"),
            "maker_filled": bool(maker_filled),
            "maker_fill_wait_s": fill_wait_s,
            "maker_fill_through": bool(maker_through),
            "keep_50": keep_hash_50(symbol, ctx["trigger_ts"]),
            "maker_entry_px": float(mk_limit) if maker_filled else math.nan,
            "maker_exit_px": float(exit_fill) if maker_filled else math.nan,
            "maker_gross": maker.gross_usd if maker else math.nan,
            "maker_mid_to_mid": maker.mid_to_mid_usd if maker else math.nan,
            "maker_spread": maker.spread_usd if maker else math.nan,
            "maker_fees": maker.fees_usd if maker else math.nan,
            "maker_slippage": maker.slippage_usd if maker else math.nan,
            "maker_net": maker.net_usd if maker else math.nan,
            "maker_ret_bps": maker.ret_bps if maker else math.nan,
            "canon_net": canon.net_usd,
            "canon_gross": canon.gross_usd,
            # latency cost: adverse decision→fill mid drift on the canonical entry.
            "latency_usd": side * (pos["entry_mid"] - ctx["decision_mid"]) * shares,
            # meta label uses the maker-entry system trade (§4).
            "net_bps": (maker.ret_bps if maker else math.nan),
        })
        records.append(rec)
        pos = None

    for i in range(n):
        ts_i = int(ts[i])
        # 1. OU sample on trade activity.
        if vol[i] > 0.0:
            calibrator.sample(ts_i, mid[i], feat.vwap_5m[i])

        # 2. drain pending entry.
        if pend_entry is not None and i >= pend_entry["resolve_bar"]:
            if pend_entry["is_fill"]:
                _open(pend_entry["resolve_bar"], pend_entry["side"], pend_entry["entry_fill"], pend_entry["ctx"])
            else:
                # maker cancel — a posted order that went unfilled after 60 s.
                rec = dict(pend_entry["ctx"])
                rec.update({"opened": False, "maker_posted": True,
                            "maker_filled": False, "maker_fill_wait_s": -1})
                records.append(rec)
            pend_entry = None

        # 3. drain pending exit.
        if pend_exit is not None and pos is not None and i >= pend_exit["fill_bar"]:
            _close(i, pend_exit["reason"])
            pend_exit = None

        # 4. curfew force-flat.
        if (not eod_done) and i >= curfew_bar:
            if pos is not None:
                fb = max(curfew_bar - 1, pos["entry_bar"])
                _close(fb, EXIT_FORCE)
            pend_entry = None
            pend_exit = None
            eod_done = True

        # 5. OU recalibrate.
        thr = calibrator.maybe_calibrate(ts_i)

        if eod_done:
            continue

        # 6. risk tick (position open, no pending exit).
        if pos is not None and pend_exit is None:
            m = micro[i]
            if not math.isnan(m):
                reason = _risk_tick(pos, m, sigma5[i], i)
                if reason > 0:
                    fb = i + TAKER_LATENCY_BARS
                    if fb < curfew_bar:
                        pend_exit = {"reason": reason, "fill_bar": fb}

        # 7. strategy evaluate.
        if not feat.warm[i] or not calibrator.is_warm:
            continue
        action, side = _evaluate(
            eps=calibrator.latest_eps, thr=thr, rho=feat.rho_t[i], ofi_5s=feat.ofi_5s[i],
            micro=micro[i], vwap=feat.vwap_5m[i], spread=feat.spread_bps[i],
            sigma_5m=sigma5[i], vwap_30m=feat.vwap_30m[i], midprice=mid[i],
        )
        if action == 0 or pend_entry is not None or pend_exit is not None:
            continue

        if action == 1:  # ENTRY proposal
            if pos is not None:
                continue  # can_open_entry: already in a position
            if _in_blackout(int(et[i])):
                continue
            if daily_gross <= -DAILY_LOSS_USD:
                continue
            if (i - last_close_bar) < COOLDOWN_BARS:
                continue
            if (i - last_stop_close_bar) < STOP_COOLDOWN_BARS:
                continue
            # RAW TRIGGER — build the decision-time context.
            g1, g2 = eval_gates(
                side=side, micro_dev_bps=feat.micro_dev_bps[i], ofi_5s=feat.ofi_5s[i],
                spread_bps=feat.spread_bps[i], sigma_5m=sigma5[i], baseline=baseline,
            )
            ctx = {
                "symbol": symbol, "session": session, "side": int(side),
                "trigger_bar": int(i), "trigger_ts": ts_i, "decision_mid": float(mid[i]),
                "eps_trigger": float(calibrator.latest_eps),
                "entry_long": float(thr.entry_long), "exit_long": float(thr.exit_long),
                "entry_short": float(thr.entry_short), "exit_short": float(thr.exit_short),
                "kappa": float(thr.kappa), "theta": float(thr.theta), "ou_sigma": float(thr.sigma),
                "rho_t": float(feat.rho_t[i]), "ofi_5s": float(feat.ofi_5s[i]),
                "spread_bps": float(feat.spread_bps[i]), "sigma_5m": float(sigma5[i]),
                "micro_dev_bps": float(feat.micro_dev_bps[i]), "et_minute": int(et[i]),
                "passed_G1": bool(g1), "passed_G2": bool(g2),
            }
            # schedule the entry fill.
            if entry_model == "taker":
                fb = i + TAKER_LATENCY_BARS
                if fb < curfew_bar:
                    pend_entry = {"is_fill": True, "resolve_bar": fb, "side": side,
                                  "entry_fill": (ask[fb] if side > 0 else bid[fb]), "ctx": ctx}
                # if fill would be past curfew: dropped (engineV2); log as unopened.
                else:
                    rec = dict(ctx)
                    rec.update({"opened": False, "maker_posted": False,
                                "maker_filled": False, "maker_fill_wait_s": -1})
                    records.append(rec)
            else:  # maker
                limit = bid[i] if side > 0 else ask[i]
                m = maker_fill_bar(px_low, px_high, i, side, limit, strict=False)
                if m is not None and m < curfew_bar:
                    pend_entry = {"is_fill": True, "resolve_bar": m, "side": side,
                                  "entry_fill": limit, "ctx": ctx}
                else:
                    cancel_bar = min(i + MAKER_CANCEL_BARS, curfew_bar - 1)
                    pend_entry = {"is_fill": False, "resolve_bar": max(cancel_bar, i + 1),
                                  "side": side, "entry_fill": limit, "ctx": ctx}
        elif action == 2:  # strategy EXIT proposal
            if pos is not None and pos["side"] == side and (i - pos["entry_bar"]) >= MIN_HOLD_BARS:
                fb = i + TAKER_LATENCY_BARS
                if fb < curfew_bar:
                    pend_exit = {"reason": EXIT_STRATEGY, "fill_bar": fb}

    # EOD fallback: force-flat any still-open position at the last bar.
    if pos is not None:
        _close(n - 1, EXIT_FORCE)

    return records


def _risk_tick(pos: dict, micro: float, sigma_5m: float, i: int) -> int:
    """engineV2 riskgate_nb.risk_tick on sticky microprice. Priority
    TP → hard stop → trailing → deadline. Returns exit reason (0 = none)."""
    side = pos["side"]
    entry = pos["entry_fill"]
    # high water
    if side > 0 and micro > pos["high_water"]:
        pos["high_water"] = micro
    elif side < 0 and micro < pos["high_water"]:
        pos["high_water"] = micro
    # trailing activation
    pnl_bps = 1e4 * (micro - entry) / entry if side > 0 else 1e4 * (entry - micro) / entry
    if pnl_bps > TRAIL_ACTIVATE_BPS:
        sig = sigma_5m if (not math.isnan(sigma_5m) and sigma_5m > 0.0) else 0.0
        min_sigma = entry * MIN_TRAILING_SIGMA_BPS / 1e4
        if sig < min_sigma:
            sig = min_sigma
        offset = TRAIL_K_SIGMA * sig
        ts_new = pos["high_water"] - offset if side > 0 else pos["high_water"] + offset
        cur = pos["trailing"]
        if cur is None:
            pos["trailing"] = ts_new
        elif side > 0 and ts_new > cur:
            pos["trailing"] = ts_new
        elif side < 0 and ts_new < cur:
            pos["trailing"] = ts_new
    # TP
    tp = pos["take_profit"]
    if (side > 0 and micro >= tp) or (side < 0 and micro <= tp):
        return EXIT_TP
    # hard stop
    hs = pos["hard_stop"]
    if (side > 0 and micro <= hs) or (side < 0 and micro >= hs):
        return EXIT_HARD
    # trailing
    tr = pos["trailing"]
    if tr is not None and ((side > 0 and micro <= tr) or (side < 0 and micro >= tr)):
        return EXIT_TRAILING
    # deadline
    if i >= pos["deadline_bar"]:
        return EXIT_MAX_HOLD
    return 0
