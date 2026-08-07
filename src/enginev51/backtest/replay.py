"""Causal plan-level replayer — the ONLY source of plan economics (PROTOCOL v6 §3).

Simulates complete TradePlans against one session's quote/trade tape in strict
event time, under deployment reality:
  * manual latency drawn seeded-uniform at EVERY leg (entry, chase, stop,
    target arming, hold/curfew flat) — see backtest/latency.py;
  * k concurrent slots portfolio-wide, one position per symbol, first-come:
    a slot is RESERVED at the plan's authored instant (the human commits
    attention at decision time, before the order lands), so admission is
    causally exact in a single authored-order pass; ties at the same authored
    instant admit the higher registered EV first (PROTOCOL v6 §3). Harness
    v1.2 fix — the earlier acquire-at-action model could admit >k plans when
    same-minute latency draws reordered acquisition (audit 2026-07-16 #1/#2);
  * limit entries fill by the L2-strict trade-through rule (price strictly
    through the limit) — full size, no queue model at the L1 tier; the strict
    rule is the conservatism knob (PROTOCOL v6 §3);
  * stops trigger on quotes and fill by CROSSING after a fresh latency draw —
    gap-through honest (the fill can be far worse than the stop). The trigger is
    a LEVEL check, so a book already through the stop when the bracket arms
    decides AT the arm instant (v1.7, code review 2026-07-28 B3) instead of
    waiting for the next quote update;
  * targets are resting passive limits, armed only after a per-target latency
    draw following the entry fill (a human places brackets one order at a time);
  * the STOP likewise arms only after its own post-fill latency draw ("stoparm")
    — symmetric manual bracket placement (harness v1.2; audit #3: the stop was
    previously live at the fill instant while targets paid arming latency);
  * once a stop triggers, the human abandons resting targets and markets out:
    target prints inside the stop-latency window are deliberately ignored
    (documented conservatism — racing fills are not assumed);
  * any remainder is marketed out at min(hold deadline, curfew), plus latency.

Void/unfilled/not-taken plans are first-class results — foregone breadth is
measured, not hidden. Run with k_slots=10**9 for the unconstrained arm.

Harness v1.5 (code review 2026-07-17 F2/F3/F7): TAKEN now means a FULLY modeled
round trip — a plan whose exit cannot be completed on the tape voids instead of
booking its partial exits; a failed post-stop market-out falls through to the
hard-end market-out instead of abandoning the remainder; one aggressive print
clears every resting target level it trades through (not just the nearest); and
every post-admission failure path records its slot occupancy through the failure
instant so admission never retroactively frees attention.

Harness v1.6 (audit 2026-07-21 F4): the staleness void (entry ACTION lands past
validity/curfew) is decided AFTER slot admission and records occupancy
[authored, action), like the other post-admission voids. The action instant is
drawn from the future latency, so voiding before reservation (the pre-v1.6 order)
let a concurrent plan see a slot a real-time human would still have been holding.
Dead for the shipped population (VALID_FOR_S=120 s > 25 s max latency), fixed
while the branch is economically inert.

Harness v1.7 (code review 2026-07-28 B3): ``fills.stop_trigger_ts`` is a LEVEL
test at ``max(cursor, stop_arm)``, not a transition test strictly after it. An
entry that gaps through its own stop (or a stop armed into an already-breached
book) now stops out at the arm instant + stop latency; before, the position
waited for the next quote update and on a sparse tape could ride to
hold/curfew. The loop is unaffected structurally: the stop branch always
terminates the position (or falls through to the hard-end market-out), so a
trigger at the loop's own cursor cannot re-enter.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from enginev51.backtest import fills as fk
from enginev51.backtest import latency as lat
from enginev51.backtest.decompose import PlanPnl, plan_pnl
from enginev51.plans.schema import TradePlan

NS_PER_MIN = 60_000_000_000

STATUS_TAKEN = "taken"
STATUS_NOT_TAKEN = "not_taken"  # slots full at action time
STATUS_VOID = "void"  # unexecutable (stale before human could act / no tape)
STATUS_UNFILLED = "unfilled"  # limit entry never filled, no chase


@dataclass(slots=True, frozen=True)
class SessionTape:
    """Sane-filtered, ts-sorted numpy arrays for one (symbol, session).

    t_size is optional (legacy monolithic exports lack it in some paths); when
    present it enables odd-lot-robust limit fills (ReplayConfig.min_fill_size).
    """

    symbol: str
    q_ts: np.ndarray
    q_bid: np.ndarray
    q_ask: np.ndarray
    t_ts: np.ndarray
    t_price: np.ndarray
    t_size: np.ndarray | None = None


@dataclass(slots=True, frozen=True)
class PlanResult:
    plan: TradePlan
    status: str
    entry_fills: tuple[fk.Fill, ...]
    exit_fills: tuple[fk.Fill, ...]
    exit_reason: str | None  # "targets" | "stop" | "hold" | "curfew" | None
    slot_acquired: int | None
    slot_released: int | None
    pnl: PlanPnl | None


@dataclass(slots=True)
class _Slot:
    symbol: str
    acquired: int
    released: int  # grows while the position lives; final on close


class ReplayConfig:
    __slots__ = (
        "k_slots", "seed", "lat_lo_s", "lat_hi_s", "slip_bps", "sec_taf_sell_bps",
        "min_fill_size",
    )

    def __init__(
        self,
        k_slots: int = 2,
        seed: int = 7,
        lat_lo_s: float = 5.0,
        lat_hi_s: float = 25.0,
        slip_bps: float = 0.5,
        sec_taf_sell_bps: float = 0.3,
        min_fill_size: float = 100.0,  # v1.1: odd-lot prints are not fill evidence
    ) -> None:
        # A negative reaction time is a look-ahead, not a fast human: every leg's
        # action instant must be at-or-after its decision instant. The terminal
        # market-out relies on this (N3).
        if lat_lo_s < 0.0 or lat_hi_s < lat_lo_s:
            raise ValueError("latency bounds must satisfy 0 <= lat_lo_s <= lat_hi_s")
        self.k_slots = k_slots
        self.seed = seed
        self.lat_lo_s = lat_lo_s
        self.lat_hi_s = lat_hi_s
        self.slip_bps = slip_bps
        self.sec_taf_sell_bps = sec_taf_sell_bps
        self.min_fill_size = min_fill_size


def replay_session(
    plans: list[TradePlan], tapes: dict[str, SessionTape], cfg: ReplayConfig
) -> list[PlanResult]:
    """Replay one session's plans (any mix of symbols) under the slot constraint."""
    slots: list[_Slot] = []
    results: list[PlanResult] = []
    # first-come; ties at one authored instant -> higher registered EV (PROTOCOL v6 §3)
    for plan in sorted(plans, key=lambda p: (p.ts_authored, -p.expected_net_bps, p.plan_id)):
        results.append(_replay_plan(plan, tapes.get(plan.symbol), slots, cfg))
    return results


def _lat(cfg: ReplayConfig, plan: TradePlan, leg: str) -> int:
    return lat.latency_ns(cfg.seed, plan.plan_id, leg, cfg.lat_lo_s, cfg.lat_hi_s)


def _occupied(slots: list[_Slot], t: int) -> int:
    return sum(1 for s in slots if s.acquired <= t < s.released)


def _symbol_busy(slots: list[_Slot], symbol: str, t: int) -> bool:
    return any(s.symbol == symbol for s in slots if s.acquired <= t < s.released)


def _no_result(plan: TradePlan, status: str) -> PlanResult:
    return PlanResult(plan, status, (), (), None, None, None, None)


def _replay_plan(
    plan: TradePlan, tape: SessionTape | None, slots: list[_Slot], cfg: ReplayConfig
) -> PlanResult:
    if tape is None or tape.q_ts.size == 0:
        return _no_result(plan, STATUS_VOID)

    # ---- entry decision -> action -------------------------------------------------
    entry_action = plan.ts_authored + _lat(cfg, plan, lat.LEG_ENTRY)
    # v1.2: slot admission at the AUTHORED instant (attention reserved at decision
    # time) — acquire-at-action allowed >k concurrency under latency reordering.
    # v1.6 (audit 2026-07-21 F4): admission is decided BEFORE the staleness void so
    # a plan that cannot win a slot records no occupancy, while a plan that does win
    # one keeps it even when voided.
    if _occupied(slots, plan.ts_authored) >= cfg.k_slots or _symbol_busy(
        slots, plan.symbol, plan.ts_authored
    ):
        return _no_result(plan, STATUS_NOT_TAKEN)
    if entry_action > plan.valid_until or entry_action >= plan.curfew_ts:
        # v1.6: the slot was reserved at the authored instant, so a staleness void
        # discovered via the (future) latency draw still occupies [authored,
        # entry_action) — mirroring the v1.5 post-admission void paths. Voiding
        # before reservation (pre-v1.6) freed a slot a real-time human still held.
        slots.append(_Slot(plan.symbol, plan.ts_authored, entry_action))
        return PlanResult(
            plan, STATUS_VOID, (), (), None, plan.ts_authored, entry_action, None
        )

    mid_at_decision = fk.prevailing_mid(tape.q_ts, tape.q_bid, tape.q_ask, plan.ts_authored)

    # ---- entry fill ----------------------------------------------------------------
    entry_fill: fk.Fill | None = None
    slot_acquired = plan.ts_authored  # v1.2: reservation at decision time
    if plan.entry.type == "market":
        mk = fk.market_fill(tape.q_ts, tape.q_bid, tape.q_ask, entry_action, plan.side, cfg.slip_bps)
        if mk is None:
            # v1.5: attention was reserved at the authored instant, so a
            # post-admission failure still occupies the slot until discovered.
            slots.append(_Slot(plan.symbol, slot_acquired, entry_action))
            return PlanResult(plan, STATUS_VOID, (), (), None, slot_acquired, entry_action, None)
        px, mid_act = mk
        entry_fill = fk.Fill(
            ts=entry_action, price=px, qty_frac=1.0, leg=lat.LEG_ENTRY,
            decision_ts=plan.ts_authored, mid_at_decision=mid_at_decision,
            mid_at_action=mid_act, maker=False,
        )
    else:
        limit = float(plan.entry.limit_price)  # type: ignore[arg-type]
        cancel_ts = entry_action + plan.entry.expire_s * 1_000_000_000
        cancel_ts = min(cancel_ts, plan.curfew_ts)
        f_ts = fk.limit_fill_ts(
            tape.t_ts, tape.t_price, entry_action, cancel_ts, limit, plan.side, strict=True,
            t_size=tape.t_size, min_size=cfg.min_fill_size,
            q_ts=tape.q_ts, q_bid=tape.q_bid, q_ask=tape.q_ask,
        )
        if f_ts is not None:
            entry_fill = fk.Fill(
                ts=f_ts, price=limit, qty_frac=1.0, leg=lat.LEG_ENTRY,
                decision_ts=plan.ts_authored, mid_at_decision=mid_at_decision,
                mid_at_action=fk.prevailing_mid(tape.q_ts, tape.q_bid, tape.q_ask, entry_action),
                maker=True,
            )
        elif plan.entry.chase_at_expire:
            chase_action = cancel_ts + _lat(cfg, plan, lat.LEG_CHASE)
            if chase_action >= plan.curfew_ts:
                slots.append(_Slot(plan.symbol, slot_acquired, cancel_ts))
                return PlanResult(
                    plan, STATUS_UNFILLED, (), (), None, slot_acquired, cancel_ts, None
                )
            mk = fk.market_fill(
                tape.q_ts, tape.q_bid, tape.q_ask, chase_action, plan.side, cfg.slip_bps
            )
            if mk is None:
                # v1.5: same post-admission occupancy rule as the market path.
                slots.append(_Slot(plan.symbol, slot_acquired, chase_action))
                return PlanResult(
                    plan, STATUS_VOID, (), (), None, slot_acquired, chase_action, None
                )
            px, mid_act = mk
            entry_fill = fk.Fill(
                ts=chase_action, price=px, qty_frac=1.0, leg=lat.LEG_CHASE,
                decision_ts=cancel_ts, mid_at_decision=fk.prevailing_mid(
                    tape.q_ts, tape.q_bid, tape.q_ask, cancel_ts
                ),
                mid_at_action=mid_act, maker=False,
            )
        else:
            slots.append(_Slot(plan.symbol, slot_acquired, cancel_ts))
            return PlanResult(plan, STATUS_UNFILLED, (), (), None, slot_acquired, cancel_ts, None)

    # ---- exits ---------------------------------------------------------------------
    entry_ts = entry_fill.ts
    hold_end = entry_ts + plan.hold_max_min * NS_PER_MIN
    hard_end = min(hold_end, plan.curfew_ts)  # decision time of the terminal market-out
    hard_leg = lat.LEG_HOLD if hold_end <= plan.curfew_ts else lat.LEG_CURFEW

    # brackets armed after per-order latency (human places them one by one);
    # v1.2: the stop pays its own arming draw too — symmetric with targets.
    target_arm = [
        entry_ts + _lat(cfg, plan, f"{lat.LEG_TARGET}{i}") for i in range(len(plan.targets))
    ]
    target_open = [True] * len(plan.targets)
    stop_arm = entry_ts + _lat(cfg, plan, "stoparm")

    exit_fills: list[fk.Fill] = []
    remaining = 1.0
    cursor = entry_ts
    exit_reason: str | None = None

    while remaining > 1e-9:
        # candidate events, all bounded by hard_end
        stop_ts = fk.stop_trigger_ts(
            tape.q_ts, tape.q_bid, tape.q_ask, max(cursor, stop_arm), hard_end,
            plan.stop.price, plan.side,
        )
        tgt_hits: list[tuple[int, int]] = []  # (fill_ts, target_idx)
        for i, tgt in enumerate(plan.targets):
            if not target_open[i]:
                continue
            arm = max(target_arm[i], cursor)
            t_ts = fk.target_fill_ts(
                tape.t_ts, tape.t_price, arm, hard_end, tgt.price, plan.side, strict=True,
                t_size=tape.t_size, min_size=cfg.min_fill_size,
                q_ts=tape.q_ts, q_bid=tape.q_bid, q_ask=tape.q_ask,
            )
            if t_ts is not None:
                tgt_hits.append((t_ts, i))
        first_tgt = min(tgt_hits) if tgt_hits else None

        stop_wins = stop_ts is not None and (first_tgt is None or stop_ts <= first_tgt[0])
        if stop_wins:
            # stop wins: market out everything remaining, targets abandoned
            action = stop_ts + _lat(cfg, plan, lat.LEG_STOP)
            mk = fk.market_fill(tape.q_ts, tape.q_bid, tape.q_ask, action, -plan.side, cfg.slip_bps)
            if mk is not None:
                px, mid_act = mk
                exit_fills.append(
                    fk.Fill(
                        ts=action, price=px, qty_frac=remaining, leg=lat.LEG_STOP,
                        decision_ts=stop_ts,
                        mid_at_decision=fk.prevailing_mid(tape.q_ts, tape.q_bid, tape.q_ask, stop_ts),
                        mid_at_action=mid_act, maker=False,
                    )
                )
                remaining = 0.0
                exit_reason = "stop" if not exit_fills[:-1] else "mixed"
                break
            # defensive: no quote after the stop trigger — targets stay abandoned
            # and control falls through to the terminal hard-end market-out below
            # (v1.5; the old `break` here could return a partial exit as TAKEN).
        elif first_tgt is not None:
            f_ts = first_tgt[0]
            # v1.5: one aggressive print can clear SEVERAL resting target levels —
            # every open target whose first fill is this same print fills here,
            # not just the nearest (the old cursor advance skipped the rest past
            # the shared print and they waited for a later one).
            mid_here = fk.prevailing_mid(tape.q_ts, tape.q_bid, tape.q_ask, f_ts)
            for t_ts, i in sorted(tgt_hits):
                if t_ts != f_ts or remaining <= 1e-9:
                    break
                tgt = plan.targets[i]
                frac = min(tgt.frac, remaining)
                exit_fills.append(
                    fk.Fill(
                        ts=f_ts, price=tgt.price, qty_frac=frac, leg=f"{lat.LEG_TARGET}{i}",
                        decision_ts=f_ts, mid_at_decision=mid_here, mid_at_action=mid_here,
                        maker=True,
                    )
                )
                target_open[i] = False
                remaining -= frac
            cursor = f_ts
            if remaining <= 1e-9:
                exit_reason = "targets"
            continue

        # terminal market-out: no stop/target before hard_end, or the stop
        # market-out found no quote (fell through from the stop branch).
        # Latency is non-negative: `ReplayConfig.__init__` validates the bounds AT
        # CONSTRUCTION (the object is a plain mutable holder — nothing stops a caller
        # writing cfg.lat_lo_s afterwards, and no caller in this package does). So
        # action >= hard_end, and the prevailing-quote lookup at `action` can only see
        # MORE quotes than one at `hard_end`: a retry at hard_end after a None here
        # was dead code (code review 2026-07-28 N3) and is not attempted.
        action = hard_end + _lat(cfg, plan, hard_leg)
        mk = fk.market_fill(tape.q_ts, tape.q_bid, tape.q_ask, action, -plan.side, cfg.slip_bps)
        if mk is None:
            break  # tape exhausted — should not happen intra-RTH; plan voids below
        px, mid_act = mk
        exit_fills.append(
            fk.Fill(
                ts=action, price=px, qty_frac=remaining, leg=hard_leg,
                decision_ts=hard_end,
                mid_at_decision=fk.prevailing_mid(tape.q_ts, tape.q_bid, tape.q_ask, hard_end),
                mid_at_action=mid_act, maker=False,
            )
        )
        remaining = 0.0
        exit_reason = (
            ("hold" if hard_leg == lat.LEG_HOLD else "curfew")
            if len(exit_fills) == 1
            else "mixed"
        )

    if remaining > 1e-9:
        # could not model a FULL round trip (tape exhausted mid-exit) — VOID,
        # never TAKEN with unexited size (v1.5, code review F2: partial target
        # fills used to book as a complete plan). Slot stays occupied through
        # the last modeled instant.
        released = max((f.ts for f in exit_fills), default=entry_ts)
        slots.append(_Slot(plan.symbol, slot_acquired, released))
        return PlanResult(
            plan, STATUS_VOID, (entry_fill,), tuple(exit_fills), None,
            slot_acquired, released, None,
        )

    slot_released = max(f.ts for f in exit_fills)
    slots.append(_Slot(plan.symbol, slot_acquired, slot_released))
    pnl = plan_pnl(plan.side, (entry_fill,), tuple(exit_fills), cfg.sec_taf_sell_bps)
    return PlanResult(
        plan, STATUS_TAKEN, (entry_fill,), tuple(exit_fills), exit_reason,
        slot_acquired, slot_released, pnl,
    )
