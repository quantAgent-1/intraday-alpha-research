"""Golden-session tests for the causal plan replayer (hand-computed).

Latency is pinned lo==hi==10 s so every action instant is exact by hand.
Slip is 0.5 bp; ns timestamps are built from a base B. Economic identities are
asserted via decompose's residual (its own arithmetic is tested separately in
test_decompose.py) — here we assert FILL FACTS: timestamps, prices, legs,
statuses, exit reasons, slot behavior.
"""

from __future__ import annotations

import numpy as np
import pytest

from enginev51.backtest.replay import (
    STATUS_NOT_TAKEN,
    STATUS_TAKEN,
    STATUS_UNFILLED,
    STATUS_VOID,
    ReplayConfig,
    SessionTape,
    replay_session,
)
from enginev51.plans.schema import EntrySpec, StopSpec, TargetSpec, TradePlan

S = 1_000_000_000  # ns per second
B = 1_700_000_000 * S  # arbitrary session base


def _tape(symbol: str, quotes: list[tuple[int, float, float]], trades: list[tuple[int, float]]):
    q = sorted(quotes)
    t = sorted(trades)
    return SessionTape(
        symbol=symbol,
        q_ts=np.array([B + s * S for s, _, _ in q], dtype=np.int64),
        q_bid=np.array([b for _, b, _ in q], dtype=np.float64),
        q_ask=np.array([a for _, _, a in q], dtype=np.float64),
        t_ts=np.array([B + s * S for s, _ in t], dtype=np.int64),
        t_price=np.array([p for _, p in t], dtype=np.float64),
    )


def _cfg(k: int = 2) -> ReplayConfig:
    return ReplayConfig(k_slots=k, seed=7, lat_lo_s=10.0, lat_hi_s=10.0, slip_bps=0.5)


def _plan(
    symbol: str = "NVDA",
    plan_id: str = "p1",
    authored_s: int = 0,
    side: int = 1,
    entry: EntrySpec | None = None,
    stop: float = 95.0,
    targets: tuple[TargetSpec, ...] = (),
    hold_min: int = 120,
    curfew_s: int = 3600,
    valid_s: int = 300,
) -> TradePlan:
    return TradePlan(
        plan_id=plan_id,
        symbol=symbol,
        ts_authored=B + authored_s * S,
        valid_until=B + (authored_s + valid_s) * S,
        side=side,
        entry=entry or EntrySpec(type="market", limit_price=None, expire_s=0, chase_at_expire=False),
        stop=StopSpec(price=stop, basis="test"),
        targets=targets,
        hold_max_min=hold_min,
        curfew_ts=B + curfew_s * S,
        expected_gross_bps=20.0,
        expected_net_bps=15.0,
        sigma_h_bps=80.0,
        p_win=0.6,
        ev_ratio=3.0,
        confidence=0.6,
        payer="test",
        horizon_min=60,
    )


# --------------------------------------------------------------------------- #
# 1. market entry + full target exit
# --------------------------------------------------------------------------- #
def test_market_entry_target_exit() -> None:
    tape = _tape(
        "NVDA",
        quotes=[(0, 99.99, 100.01), (590, 100.99, 101.01)],
        trades=[(600, 101.02)],
    )
    plan = _plan(targets=(TargetSpec(price=101.00, frac=1.0),))
    (r,) = replay_session([plan], {"NVDA": tape}, _cfg())

    assert r.status == STATUS_TAKEN
    # entry: authored 0s + 10s latency -> action 10s, prevailing quote = (0s) 99.99/100.01
    ef = r.entry_fills[0]
    assert ef.ts == B + 10 * S and ef.leg == "entry" and not ef.maker
    assert abs(ef.price - 100.01 * 1.00005) < 1e-9  # ask * (1 + 0.5bp)
    assert abs(ef.mid_at_decision - 100.00) < 1e-12
    # target armed 20s (entry 10s + 10s latency); print 101.02 > 101.00 at 600s fills
    xf = r.exit_fills[0]
    assert xf.ts == B + 600 * S and xf.leg == "target0" and xf.maker
    assert xf.price == 101.00 and xf.qty_frac == 1.0
    assert r.exit_reason == "targets"
    assert r.pnl is not None and abs(r.pnl.identity_residual_bps) < 1e-6
    # slot reserved at the authored instant (v1.2), released at the last exit
    assert r.slot_acquired == B + 0 * S and r.slot_released == B + 600 * S


# --------------------------------------------------------------------------- #
# 2. limit entry never fills -> chase converts to market
# --------------------------------------------------------------------------- #
def test_limit_nofill_chase() -> None:
    tape = _tape(
        "NVDA",
        quotes=[(0, 100.00, 100.02), (200, 100.10, 100.12)],
        trades=[(60, 100.05), (90, 100.10)],  # never below the 99.90 limit
    )
    entry = EntrySpec(type="limit", limit_price=99.90, expire_s=120, chase_at_expire=True)
    plan = _plan(entry=entry, targets=(TargetSpec(price=110.0, frac=1.0),), curfew_s=3600)
    (r,) = replay_session([plan], {"NVDA": tape}, _cfg())

    assert r.status == STATUS_TAKEN
    ef = r.entry_fills[0]
    # place 10s, cancel 130s, chase decision 130s + 10s latency -> action 140s;
    # prevailing quote at 140s is the (200s? no) 0s quote... 200s > 140s -> (0s) quote? NO:
    # prevailing = last quote <= 140s = the 0s quote (100.00/100.02).
    assert ef.leg == "chase" and ef.ts == B + 140 * S and not ef.maker
    assert abs(ef.price - 100.02 * 1.00005) < 1e-9
    # no target print, no stop: exits at hold end (120 min) vs curfew 3600s -> curfew first
    assert r.exit_reason == "curfew"


# --------------------------------------------------------------------------- #
# 3. stop gap-through fills at the post-latency touch, not the stop price
# --------------------------------------------------------------------------- #
def test_stop_gap_through() -> None:
    tape = _tape(
        "NVDA",
        quotes=[(0, 100.00, 100.02), (100, 99.60, 99.62), (200, 98.80, 98.90)],
        trades=[],
    )
    plan = _plan(stop=99.50, targets=())
    (r,) = replay_session([plan], {"NVDA": tape}, _cfg())

    assert r.status == STATUS_TAKEN
    # bid 99.60 > stop at 100s (no trigger); 98.80 <= 99.50 at 200s -> decision 200s
    xf = r.exit_fills[0]
    assert xf.leg == "stop" and xf.decision_ts == B + 200 * S and xf.ts == B + 210 * S
    # fill = prevailing bid at 210s (the 200s quote) * (1 - slip): far below the stop
    assert abs(xf.price - 98.80 * 0.99995) < 1e-9
    assert xf.price < 99.50 - 0.5
    assert r.exit_reason == "stop"


def test_stop_already_through_at_arm_stops_at_the_arm_instant() -> None:
    # B3 (code review 2026-07-28): the entry gaps straight through its own stop and
    # the tape then goes SILENT — no quote update ever follows the arm instant.
    # Quotes: 0s 100.00/100.02, 5s 93.00/93.02. Entry action 10s fills at the
    # prevailing (5s) ask; the stop (95.00) arms at 10s + 10s = 20s, where the
    # prevailing book (bid 93.00) is ALREADY through it -> decision 20s, action 30s.
    # PRE-FIX the trigger searched strictly after 20s, found nothing, and the
    # position rode to the 3600s curfew — a free ~200 bp of hindsight.
    tape = _tape(
        "NVDA",
        quotes=[(0, 100.00, 100.02), (5, 93.00, 93.02)],
        trades=[],
    )
    plan = _plan(stop=95.0, targets=())
    (r,) = replay_session([plan], {"NVDA": tape}, _cfg())

    assert r.status == STATUS_TAKEN
    assert r.exit_reason == "stop"
    assert len(r.exit_fills) == 1
    xf = r.exit_fills[0]
    assert xf.leg == "stop"
    assert xf.decision_ts == B + 20 * S      # the arm instant IS the decision
    assert xf.ts == B + 30 * S               # + one 10s stop-latency draw
    # fill = prevailing bid at 30s (the 5s quote) * (1 - 0.5bp slip)
    assert abs(xf.price - 93.00 * 0.99995) < 1e-9
    assert r.slot_released == B + 30 * S


def test_stop_not_through_at_arm_is_unchanged() -> None:
    # Control for the test above: same shape, but the arm-instant book is inside
    # the stop (bid 99.60 > 95.00) and no later quote breaches it -> no stop; the
    # plan exits at the curfew market-out exactly as before.
    tape = _tape(
        "NVDA",
        quotes=[(0, 100.00, 100.02), (5, 99.60, 99.62)],
        trades=[],
    )
    plan = _plan(stop=95.0, targets=(), curfew_s=300)
    (r,) = replay_session([plan], {"NVDA": tape}, _cfg())

    assert r.status == STATUS_TAKEN
    assert r.exit_reason == "curfew"
    xf = r.exit_fills[0]
    assert xf.leg == "curfew" and xf.decision_ts == B + 300 * S and xf.ts == B + 310 * S


def test_negative_latency_config_rejected() -> None:
    # N3: the terminal market-out no longer retries at hard_end after a None at
    # hard_end + latency; that retry was dead code ONLY because latency >= 0.
    # The invariant is now enforced at config time rather than assumed.
    with pytest.raises(ValueError):
        ReplayConfig(lat_lo_s=-1.0, lat_hi_s=10.0)
    with pytest.raises(ValueError):
        ReplayConfig(lat_lo_s=10.0, lat_hi_s=5.0)


# --------------------------------------------------------------------------- #
# 4. partial target then curfew remainder
# --------------------------------------------------------------------------- #
def test_partial_target_then_curfew() -> None:
    tape = _tape(
        "NVDA",
        quotes=[(0, 100.00, 100.02), (295, 100.49, 100.51), (1795, 100.20, 100.22)],
        trades=[(300, 100.52)],
    )
    plan = _plan(
        targets=(TargetSpec(price=100.50, frac=0.5), TargetSpec(price=103.0, frac=0.5)),
        curfew_s=1800,
        hold_min=600,
    )
    (r,) = replay_session([plan], {"NVDA": tape}, _cfg())

    assert r.status == STATUS_TAKEN
    assert len(r.exit_fills) == 2
    t0, cf = r.exit_fills
    assert t0.leg == "target0" and t0.qty_frac == 0.5 and t0.price == 100.50
    # curfew decision 1800s + 10s latency; prevailing quote = (1795s) 100.20/100.22
    assert cf.leg == "curfew" and cf.ts == B + 1810 * S and cf.qty_frac == 0.5
    assert abs(cf.price - 100.20 * 0.99995) < 1e-9
    assert r.exit_reason == "mixed"
    # residual must reconcile with partial fills
    assert r.pnl is not None and abs(r.pnl.identity_residual_bps) < 1e-6


# --------------------------------------------------------------------------- #
# 5. slots: k=1 excludes the second plan; same-symbol excludes at any k
# --------------------------------------------------------------------------- #
def test_slot_exclusion_and_release() -> None:
    q = [(0, 100.00, 100.02), (3590, 100.00, 100.02)]
    nvda, tsla = _tape("NVDA", q, []), _tape("TSLA", q, [])
    p1 = _plan(symbol="NVDA", plan_id="p1", authored_s=0)
    p2 = _plan(symbol="TSLA", plan_id="p2", authored_s=5)  # action 15s: p1 holds the slot
    r1, r2 = replay_session([p1, p2], {"NVDA": nvda, "TSLA": tsla}, _cfg(k=1))
    assert r1.status == STATUS_TAKEN
    assert r2.status == STATUS_NOT_TAKEN

    # same symbol busy blocks even with free slots
    p3 = _plan(symbol="NVDA", plan_id="p3", authored_s=5)
    r1, r3 = replay_session([p1, p3], {"NVDA": nvda}, _cfg(k=2))
    assert r1.status == STATUS_TAKEN and r3.status == STATUS_NOT_TAKEN

    # unfilled limit releases its slot at cancel -> later plan takes it
    lim = EntrySpec(type="limit", limit_price=90.0, expire_s=60, chase_at_expire=False)
    pl = _plan(symbol="NVDA", plan_id="pl", authored_s=0, entry=lim, stop=85.0)
    p4 = _plan(symbol="TSLA", plan_id="p4", authored_s=100)  # action 110s > cancel 70s
    rl, r4 = replay_session([pl, p4], {"NVDA": nvda, "TSLA": tsla}, _cfg(k=1))
    assert rl.status == STATUS_UNFILLED
    assert rl.slot_acquired == B + 0 * S and rl.slot_released == B + 70 * S
    assert r4.status == STATUS_TAKEN


# --------------------------------------------------------------------------- #
# 6. void when the human cannot act inside validity; missing tape voids
# --------------------------------------------------------------------------- #
def test_void_paths() -> None:
    tape = _tape("NVDA", [(0, 100.0, 100.02)], [])
    stale = _plan(valid_s=5)  # entry action at 10s > valid_until 5s
    (r,) = replay_session([stale], {"NVDA": tape}, _cfg())
    assert r.status == STATUS_VOID

    (r2,) = replay_session([_plan()], {}, _cfg())
    assert r2.status == STATUS_VOID


# --------------------------------------------------------------------------- #
# 6b. v1.5 (code review 2026-07-17): same-print multi-target, full-exit-or-void,
#     stop-fail fall-through, slot occupancy on post-admission void
# --------------------------------------------------------------------------- #
def test_multi_target_same_print() -> None:
    # F3: one aggressive print at 101.02 trades strictly through BOTH resting
    # sell targets (100.50 and 101.00, quote-confirmed by the 590s ask 101.01).
    # Both must fill at that print's ts — the old cursor advance filled only the
    # nearest and left the second waiting for a later print that never came.
    tape = _tape(
        "NVDA",
        quotes=[(0, 99.99, 100.01), (590, 100.99, 101.01)],
        trades=[(600, 101.02)],
    )
    plan = _plan(
        targets=(TargetSpec(price=100.50, frac=0.5), TargetSpec(price=101.00, frac=0.5)),
    )
    (r,) = replay_session([plan], {"NVDA": tape}, _cfg())

    assert r.status == STATUS_TAKEN
    assert r.exit_reason == "targets"
    assert len(r.exit_fills) == 2
    t0, t1 = r.exit_fills
    assert t0.leg == "target0" and t0.price == 100.50 and t0.qty_frac == 0.5
    assert t1.leg == "target1" and t1.price == 101.00 and t1.qty_frac == 0.5
    assert t0.ts == t1.ts == B + 600 * S  # the SAME print fills both
    assert r.pnl is not None and abs(r.pnl.identity_residual_bps) < 1e-6


def test_stop_fill_failure_falls_through_to_hard_end(monkeypatch) -> None:
    # F2: if the post-stop market-out finds no quote (defensive path), the plan
    # must fall through to the hard-end market-out — the old `break` abandoned
    # the position. market_fill never returns None on a real tape once entry
    # filled (a prevailing quote always exists), so the failure is injected.
    from enginev51.backtest import fills as fk

    tape = _tape(
        "NVDA",
        quotes=[(0, 100.00, 100.02), (100, 99.40, 99.42)],
        trades=[],
    )
    real = fk.market_fill
    stop_action = B + 110 * S  # stop trigger 100s + 10s latency

    def flaky(q_ts, q_bid, q_ask, exec_ts, side, slip_bps):
        if exec_ts == stop_action:
            return None
        return real(q_ts, q_bid, q_ask, exec_ts, side, slip_bps)

    monkeypatch.setattr(fk, "market_fill", flaky)
    plan = _plan(stop=99.50, targets=(), curfew_s=300)
    (r,) = replay_session([plan], {"NVDA": tape}, _cfg())

    assert r.status == STATUS_TAKEN
    assert len(r.exit_fills) == 1
    xf = r.exit_fills[0]
    # curfew (300s) + 10s latency; prevailing = the 100s quote
    assert xf.leg == "curfew" and xf.ts == B + 310 * S and xf.qty_frac == 1.0
    assert abs(xf.price - 99.40 * 0.99995) < 1e-9
    assert r.exit_reason == "curfew"


def test_replay_partial_exit_not_taken(monkeypatch) -> None:
    # F2: a plan whose remainder cannot be exited (tape edge, injected) must
    # VOID, not book its partial target fills as a TAKEN round trip.
    from enginev51.backtest import fills as fk

    tape = _tape(
        "NVDA",
        quotes=[(0, 100.00, 100.02), (295, 100.49, 100.51)],
        trades=[(300, 100.52)],
    )
    real = fk.market_fill
    dead_after = B + 1800 * S  # curfew decision instant

    def flaky(q_ts, q_bid, q_ask, exec_ts, side, slip_bps):
        if exec_ts >= dead_after:
            return None  # kills the terminal market-out (hard_end + latency)
        return real(q_ts, q_bid, q_ask, exec_ts, side, slip_bps)

    monkeypatch.setattr(fk, "market_fill", flaky)
    plan = _plan(
        targets=(TargetSpec(price=100.50, frac=0.5), TargetSpec(price=103.0, frac=0.5)),
        curfew_s=1800,
        hold_min=600,
    )
    (r,) = replay_session([plan], {"NVDA": tape}, _cfg())

    assert r.status == STATUS_VOID
    assert r.pnl is None and r.exit_reason is None
    # the partial fill is preserved as evidence, and the slot stayed occupied
    # through the last modeled instant (the target fill).
    assert len(r.exit_fills) == 1 and r.exit_fills[0].leg == "target0"
    assert r.slot_released == B + 300 * S


def test_post_admission_void_keeps_slot_occupied() -> None:
    # F7: p1 is admitted at its authored instant (attention reserved) but its
    # entry market-out finds no quote (tape starts later) -> VOID. The slot
    # must still read occupied over [authored, failure), so p2 (authored inside
    # that window, k=1) is NOT_TAKEN — the old code freed p1 retroactively.
    nvda = _tape("NVDA", quotes=[(60, 100.00, 100.02)], trades=[])
    tsla = _tape("TSLA", quotes=[(0, 50.00, 50.02), (3590, 50.00, 50.02)], trades=[])
    p1 = _plan(symbol="NVDA", plan_id="p1", authored_s=0)  # entry action 10s: no quote yet
    p2 = _plan(symbol="TSLA", plan_id="p2", authored_s=5)
    r1, r2 = replay_session([p1, p2], {"NVDA": nvda, "TSLA": tsla}, _cfg(k=1))

    assert r1.status == STATUS_VOID
    assert r1.slot_acquired == B + 0 * S and r1.slot_released == B + 10 * S
    assert r2.status == STATUS_NOT_TAKEN


def test_pre_admission_stale_void_keeps_slot_occupied() -> None:
    # F4 (audit 2026-07-21): pA is admitted at its authored instant (attention
    # reserved) but its entry ACTION — authored 0s + 10s latency = 10s — lands
    # past its 5 s validity, so it voids before filling. The slot must still read
    # occupied over [authored, action) = [0s, 10s), so pB (authored 5s, inside
    # that window, k=1) is NOT_TAKEN. Before the fix the staleness void returned
    # BEFORE slot reservation, so pB took a slot a live human would still hold —
    # the void decision consumed the future latency draw. Mirrors the
    # post-admission occupancy test one branch earlier.
    nvda = _tape("NVDA", quotes=[(0, 100.00, 100.02)], trades=[])
    tsla = _tape("TSLA", quotes=[(0, 50.00, 50.02), (3590, 50.00, 50.02)], trades=[])
    pA = _plan(symbol="NVDA", plan_id="pA", authored_s=0, valid_s=5)  # action 10s > valid 5s
    pB = _plan(symbol="TSLA", plan_id="pB", authored_s=5)
    rA, rB = replay_session([pA, pB], {"NVDA": nvda, "TSLA": tsla}, _cfg(k=1))

    assert rA.status == STATUS_VOID
    assert rA.slot_acquired == B + 0 * S and rA.slot_released == B + 10 * S
    assert rB.status == STATUS_NOT_TAKEN


def test_pre_admission_stale_void_releases_slot_at_action() -> None:
    # F4 (audit 2026-07-21): same stale pA, but pB is authored at 15s — AFTER
    # pA's entry action (10s), i.e. outside pA's [0s, 10s) occupancy. The reserved
    # slot is released at the action instant, so pB (k=1) takes it and completes.
    nvda = _tape("NVDA", quotes=[(0, 100.00, 100.02)], trades=[])
    tsla = _tape("TSLA", quotes=[(0, 50.00, 50.02), (3590, 50.00, 50.02)], trades=[])
    pA = _plan(symbol="NVDA", plan_id="pA", authored_s=0, valid_s=5)
    pB = _plan(symbol="TSLA", plan_id="pB", authored_s=15, stop=45.0)  # bid 50 > stop: no early stop
    rA, rB = replay_session([pA, pB], {"NVDA": nvda, "TSLA": tsla}, _cfg(k=1))

    assert rA.status == STATUS_VOID
    assert rA.slot_acquired == B + 0 * S and rA.slot_released == B + 10 * S
    assert rB.status == STATUS_TAKEN
    assert rB.slot_acquired == B + 15 * S  # pB won the slot at its authored instant


# --------------------------------------------------------------------------- #
# 7. determinism
# --------------------------------------------------------------------------- #
def test_deterministic() -> None:
    tape = _tape(
        "NVDA",
        quotes=[(0, 99.99, 100.01), (590, 100.99, 101.01)],
        trades=[(600, 101.02)],
    )
    plan = _plan(targets=(TargetSpec(price=101.00, frac=1.0),))
    cfg = ReplayConfig(k_slots=2, seed=42, lat_lo_s=5.0, lat_hi_s=25.0)
    a = replay_session([plan], {"NVDA": tape}, cfg)
    b = replay_session([plan], {"NVDA": tape}, cfg)
    assert [x.status for x in a] == [x.status for x in b]
    assert [x.entry_fills for x in a] == [x.entry_fills for x in b]
    assert [x.exit_fills for x in a] == [x.exit_fills for x in b]
