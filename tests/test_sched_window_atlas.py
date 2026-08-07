"""Tests for the M20 scheduled-macro-window mid-alpha atlas harness
(``research_screens.sched_window``). Synthetic bbo frames only — every expected
value is derived from literals, matching the real bbo-1s schema (ts/bid/ask/
bid_size/ask_size). Covers the registered landmines: PIT completed-bucket poison,
staleness drops, crossed quotes, the early-close guard, the PAST-ONLY C2 gate, the
floor-before-means and validate-gate ordering guards, the seal choke point, CR0
day-clustered CI correctness, determinism, and signed-return sign correctness.
"""

from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
import pytest

from enginev51.data.bbo1s import BBO_SCHEMA, partition_path
from enginev51.data.noii import et_ns
from enginev51.research_screens import sched_window as sw

ET = ZoneInfo("America/New_York")
NS = 1_000_000_000


# --------------------------------------------------------------------------- builders


def _row(ts: int, bid: float, ask: float) -> dict:
    return {"ts": int(ts), "bid": float(bid), "ask": float(ask), "bid_size": 100.0, "ask_size": 100.0}


def _frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=BBO_SCHEMA, orient="row").sort("ts")


def _mid_q(mid: float, half: float = 0.01) -> tuple[float, float]:
    return mid - half, mid + half


def _seconds(session: str, t0: tuple, t1: tuple):
    return range(et_ns(session, *t0), et_ns(session, *t1) + NS, NS)


def _measure_tape(session: str, t0: tuple, t1: tuple, quote_fn, *, marker_mid: float = 100.0) -> pl.DataFrame:
    """Dense 1s tape over [t0, t1] plus a lone 15:00 ET 'close marker' bucket so the
    RTH-close inference sees a bucket ending after 14:00 ET (i.e. NOT an early
    close). ``quote_fn(ts) -> (bid, ask)``."""
    rows = [_row(t, *quote_fn(t)) for t in _seconds(session, t0, t1)]
    rows.append(_row(et_ns(session, 15, 0, 0), *_mid_q(marker_mid)))
    return _frame(rows)


def _calendar(events: list[dict]) -> pl.DataFrame:
    """events: dicts with release_id, cls, session, h, m, (s, subtype)."""
    rows = []
    for e in events:
        y, mo, d = (int(x) for x in e["session"].split("-"))
        anchor = datetime(y, mo, d, e["h"], e["m"], e.get("s", 0), tzinfo=ET)
        rows.append(
            {
                "release_id": e["release_id"],
                "class": e["cls"],
                "subtype": e.get("subtype", ""),
                "session_date": e["session"],
                "sched_ts_et": anchor,
                "anchor_ts_et": anchor,
                "source": "test",
            }
        )
    return pl.DataFrame(rows)


def _getter(mapping: dict):
    def g(symbol: str, session: str):
        return mapping.get((symbol, session))

    return g


def _c1(audit: pl.DataFrame, *, horizon: str = "h30", symbol: str = "NVDA") -> dict:
    sub = audit.filter(
        (pl.col("form") == "C1") & (pl.col("horizon") == horizon) & (pl.col("symbol") == symbol)
    )
    assert sub.height == 1, f"expected 1 C1/{horizon}/{symbol} row, got {sub.height}"
    return sub.row(0, named=True)


# --------------------------------------------------------------------------- 6. CR0 golden


def test_cluster_ci_cr0_golden() -> None:
    # Two clusters, known sums: A=[1,3] (S=4,n=2), B=[5,7,9] (S=21,n=3), mean=5.
    # ss = (4-2*5)^2 + (21-3*5)^2 = 36+36 = 72; se = sqrt(72)/5; CI = 5 +/- 1.96*se.
    values = np.array([1.0, 3.0, 5.0, 7.0, 9.0])
    clusters = np.array(["A", "A", "B", "B", "B"])
    mean, lo, hi, n, ncl = sw.cluster_ci(values, clusters)
    se = (72.0 ** 0.5) / 5.0
    assert (n, ncl) == (5, 2)
    assert mean == pytest.approx(5.0)
    assert lo == pytest.approx(5.0 - 1.96 * se)
    assert hi == pytest.approx(5.0 + 1.96 * se)
    assert se == pytest.approx(1.6970562748477143)


def test_cluster_ci_degenerate_guards() -> None:
    assert sw.cluster_ci(np.array([]), np.array([]))[3] == 0
    m, lo, hi, n, ncl = sw.cluster_ci(np.array([2.0, 4.0]), np.array(["A", "A"]))
    assert m == pytest.approx(3.0) and np.isnan(lo) and np.isnan(hi) and ncl == 1


# --------------------------------------------------------------------------- 1. PIT poison


def test_pit_poison_completed_bucket_excludes_decision_instant_and_future() -> None:
    s = "2026-01-15"

    def qf(ts: int):
        if ts <= et_ns(s, 10, 4, 58):
            return _mid_q(100.0)   # anchor level
        if ts <= et_ns(s, 10, 5, 24):
            return _mid_q(101.0)   # react + entry level (last completed bucket at decision)
        return _mid_q(200.0)       # POISON: bucket starting AT decision and 1s after

    tape = _measure_tape(s, (9, 59, 0), (10, 36, 0), qf)
    cal = _calendar([{"release_id": "R1", "cls": "cluster_1000", "session": s, "h": 10, "m": 0}])
    audit = sw.assemble(cal, _getter({("NVDA", s): tape}), universe=("NVDA",))

    r = _c1(audit)
    # entry_mid is the 10:05:24 bucket (end == decision, completed) = 101, NOT the
    # 200 poison bucket that STARTS at decision (end > decision -> not complete).
    assert r["entry_mid"] == pytest.approx(101.0)
    assert r["entry_mid"] != pytest.approx(200.0)
    assert r["staleness_entry_s"] == pytest.approx(0.0)
    assert r["anchor_mid"] == pytest.approx(100.0)
    assert r["reaction"] == pytest.approx(0.01)
    assert r["status"] == "kept"


# --------------------------------------------------------------------------- 2. staleness


def test_staleness_gap_before_decision_drops_stale_entry() -> None:
    s = "2026-01-15"

    def qf(ts: int):
        return _mid_q(100.0) if ts <= et_ns(s, 10, 4, 58) else _mid_q(101.0)

    # anchor/react fresh; then a quote gap until decision (14s stale). A second late
    # segment (14:30-15:00) keeps the session from LOOKING like an early close.
    seg1 = [_row(t, *qf(t)) for t in _seconds(s, (9, 59, 0), (10, 5, 10))]
    seg2 = [_row(t, *_mid_q(101.0)) for t in _seconds(s, (14, 30, 0), (15, 0, 0))]
    tape = _frame(seg1 + seg2)
    cal = _calendar([{"release_id": "R1", "cls": "cluster_1000", "session": s, "h": 10, "m": 0}])
    audit = sw.assemble(cal, _getter({("NVDA", s): tape}), universe=("NVDA",))

    r = _c1(audit)
    assert r["status"] == "stale_entry"
    assert r["drop_level"] == "event"
    assert r["entry_mid"] is None
    assert r["is_early_close"] is False  # the late segment defeats early-close inference


def test_crossed_used_bucket_drops_crossed_quote() -> None:
    s = "2026-01-15"
    decision_bucket = et_ns(s, 10, 5, 24)

    def qf(ts: int):
        if ts == decision_bucket:
            return 100.06, 100.0        # locked/crossed (bid >= ask) at the entry bucket
        return _mid_q(100.0 if ts <= et_ns(s, 10, 4, 58) else 101.0)

    tape = _measure_tape(s, (9, 59, 0), (10, 36, 0), qf)
    cal = _calendar([{"release_id": "R1", "cls": "cluster_1000", "session": s, "h": 10, "m": 0}])
    audit = sw.assemble(cal, _getter({("NVDA", s): tape}), universe=("NVDA",))
    assert _c1(audit)["status"] == "crossed_quote"


# --------------------------------------------------------------------------- 3. early close


def test_early_close_dates_verified_membership() -> None:
    # Locks the web-verified list (primary NYSE/ICE releases, 2026-07-22).
    for d in [
        "2020-11-27", "2020-12-24", "2021-11-26", "2022-11-25", "2023-07-03",
        "2023-11-24", "2024-07-03", "2024-11-29", "2024-12-24", "2025-07-03",
        "2025-11-28", "2025-12-24",
    ]:
        assert d in sw.EARLY_CLOSE_DATES
    # Verified NON-early-closes (full holidays / weekends) must be ABSENT.
    for d in ["2020-07-03", "2021-12-24", "2022-12-23", "2022-12-24", "2023-12-24", "2026-07-03"]:
        assert d not in sw.EARLY_CLOSE_DATES


def test_early_close_guard_drops_late_decisions_only() -> None:
    # INFERRED path: an UNLISTED session whose RTH-only tape ends <= 14:00 ET.
    s = "2026-01-16"

    def qf(ts: int):
        return _mid_q(100.0 if ts <= et_ns(s, 10, 4, 58) else 100.5)

    # RTH ends 12:59:59 (early close = 13:00 <= 14:00). No 15:00 marker on purpose.
    tape = _frame([_row(t, *qf(t)) for t in _seconds(s, (9, 30, 0), (12, 59, 59))])
    cal = _calendar(
        [
            {"release_id": "LATE", "cls": "cluster_1000", "session": s, "h": 12, "m": 30},
            {"release_id": "EARLY", "cls": "cluster_1000", "session": s, "h": 10, "m": 0},
        ]
    )
    audit = sw.assemble(cal, _getter({("NVDA", s): tape}), universe=("NVDA",))

    late = audit.filter((pl.col("release_id") == "LATE") & (pl.col("form") == "C1"))
    early = audit.filter(
        (pl.col("release_id") == "EARLY") & (pl.col("form") == "C1") & (pl.col("horizon") == "h30")
    )
    assert set(late["status"].to_list()) == {"early_close"}
    assert late["is_early_close"].to_list()[0] is True
    assert late["drop_level"].to_list()[0] == "event"
    # 10:00 decision (10:05:25 < close-30min=12:30) survives the guard on the SAME
    # early-close session.
    assert early["status"].to_list()[0] == "kept"
    assert early["is_early_close"].to_list()[0] is True


def _postmarket_halfday_tape(s: str) -> pl.DataFrame:
    """A LISTED 13:00 half-day whose partition ALSO carries post-market prints
    (mid 500 after 13:00) — the exact case bucket-inference gets wrong."""

    def qf(ts: int):
        if ts <= et_ns(s, 11, 4, 58):
            mid = 100.0                    # anchor level
        elif ts <= et_ns(s, 11, 20, 0):
            mid = 101.0                    # react + entry level
        elif ts <= et_ns(s, 12, 59, 59):
            mid = 102.0                    # in-RTH exit level
        else:
            mid = 500.0                    # POST-MARKET poison (must never be read)
        return _mid_q(mid)

    return _frame([_row(t, *qf(t)) for t in _seconds(s, (9, 30, 0), (15, 59, 0))])


def test_early_close_listed_date_forces_1300_close_with_postmarket() -> None:
    # (a) LISTED half-day + post-market quotes: the event-level guard fires off the
    # FORCED 13:00 close even though bucket-inference would call it a full day.
    s = "2024-07-03"
    assert s in sw.EARLY_CLOSE_DATES
    cal = _calendar([{"release_id": "LATE", "cls": "cluster_1000", "session": s, "h": 12, "m": 30}])
    audit = sw.assemble(cal, _getter({("NVDA", s): _postmarket_halfday_tape(s)}), universe=("NVDA",))

    late = audit.filter((pl.col("release_id") == "LATE") & (pl.col("form") == "C1"))
    assert set(late["status"].to_list()) == {"early_close"}
    assert late["drop_level"].to_list()[0] == "event"
    assert late["is_early_close"].to_list()[0] is True
    assert late["close_ts"].to_list()[0] == et_ns(s, 13, 0)  # forced, NOT the ~16:00 inference


def test_early_close_listed_date_horizon_guard_keeps_short_drops_long() -> None:
    # (b) Same LISTED half-day: an 11:00 event is KEPT; short horizons resolve inside
    # RTH while horizons crossing the 13:00 close drop "early_close" (horizon-level)
    # and NEVER read the post-market 500 mid.
    s = "2024-07-03"
    cal = _calendar([{"release_id": "MORN", "cls": "cluster_1000", "session": s, "h": 11, "m": 0}])
    audit = sw.assemble(cal, _getter({("NVDA", s): _postmarket_halfday_tape(s)}), universe=("NVDA",))

    def morn(hz: str) -> dict:
        return audit.filter(
            (pl.col("release_id") == "MORN") & (pl.col("form") == "C1") & (pl.col("horizon") == hz)
        ).row(0, named=True)

    h30 = morn("h30")
    assert h30["status"] == "kept"
    assert h30["signed_ret_bps"] == pytest.approx(99.0099, abs=0.02)  # 101 -> 102, never 500
    assert morn("h60")["status"] == "kept"
    for hz in ("h120", "to1545"):
        r = morn(hz)
        assert r["status"] == "early_close"
        assert r["drop_level"] == "horizon"
        assert r["exit_mid"] is None  # post-market 500 was never read


def test_normal_day_to1545_computed_and_not_early() -> None:
    # (c) UNLISTED normal session: nothing is early-closed; to1545 reads its real
    # 15:45-capped exit.
    s = "2026-01-15"
    assert s not in sw.EARLY_CLOSE_DATES

    def qf(ts: int):
        return _mid_q(100.0 if ts <= et_ns(s, 10, 4, 58) else 101.0)

    seg1 = [_row(t, *qf(t)) for t in _seconds(s, (9, 59, 0), (10, 36, 0))]
    seg2 = [_row(t, *qf(t)) for t in _seconds(s, (15, 44, 0), (15, 46, 0))]  # covers the 15:45 exit
    tape = _frame(seg1 + seg2)
    cal = _calendar([{"release_id": "R1", "cls": "cluster_1000", "session": s, "h": 10, "m": 0}])
    audit = sw.assemble(cal, _getter({("NVDA", s): tape}), universe=("NVDA",))

    assert "early_close" not in audit.filter(pl.col("form") == "C1")["status"].to_list()
    assert _c1(audit, horizon="h30")["is_early_close"] is False
    to1545 = _c1(audit, horizon="to1545")
    assert to1545["status"] == "kept"
    assert to1545["exit_mid"] == pytest.approx(101.0)


# --------------------------------------------------------------------------- 10. sign


def test_zero_reaction_dropped() -> None:
    s = "2026-01-15"
    tape = _measure_tape(s, (9, 59, 0), (10, 36, 0), lambda ts: _mid_q(100.0))
    cal = _calendar([{"release_id": "R1", "cls": "cluster_1000", "session": s, "h": 10, "m": 0}])
    audit = sw.assemble(cal, _getter({("NVDA", s): tape}), universe=("NVDA",))
    assert _c1(audit)["status"] == "zero_reaction"


def test_short_side_sign_correctness() -> None:
    # Negative reaction (anchor 100 -> react 99), falling exit (99 -> 98):
    # signed = sign(-1%) * (98/99 - 1) * 1e4 = -1 * (-101.0101) = +101.0101 bps.
    s = "2026-01-20"

    def qf(ts: int):
        if ts <= et_ns(s, 10, 4, 58):
            return _mid_q(100.0)
        if ts <= et_ns(s, 10, 20, 0):
            return _mid_q(99.0)    # react + entry level
        return _mid_q(98.0)        # falling exit level

    tape = _measure_tape(s, (9, 59, 0), (10, 36, 0), qf, marker_mid=98.0)
    cal = _calendar([{"release_id": "R1", "cls": "cluster_1000", "session": s, "h": 10, "m": 0}])
    audit = sw.assemble(cal, _getter({("NVDA", s): tape}), universe=("NVDA",))

    r = _c1(audit)
    assert r["reaction"] < 0.0
    assert r["status"] == "kept"
    assert r["signed_ret_bps"] > 0.0
    assert r["signed_ret_bps"] == pytest.approx(101.0101, abs=0.02)


# --------------------------------------------------------------------------- 4. C2 past-only


def test_c2_expanding_median_is_strictly_past_only() -> None:
    n = 12
    # priors |reaction|: five 1.0 then five 100.0 (median of first 10 = 50.5).
    reaction = [-1.0] * 5 + [100.0] * 5 + [-40.0, 60.0]
    frame = pl.DataFrame(
        {
            "class": ["cluster_1000"] * n,
            "symbol": ["NVDA"] * n,
            "anchor_ts": [i * NS for i in range(1, n + 1)],  # strictly increasing
            "reaction": reaction,
        }
    )
    out = sw.c2_membership(frame)

    r9 = out.row(9, named=True)   # 10th event -> only 9 priors -> excluded on priors
    assert r9["n_priors"] == 9 and r9["c2_reason"] == "c2_priors" and r9["in_c2"] is False

    r10 = out.row(10, named=True)  # |r|=40 vs PAST median 50.5 -> excluded (past-only)
    assert r10["n_priors"] == 10
    assert r10["past_median"] == pytest.approx(50.5)
    assert r10["in_c2"] is False and r10["c2_reason"] == "c2_magnitude"
    # Flip check: had the CURRENT event entered its own median, median would be 40
    # and 40 >= 40 -> included. Past-only correctly EXCLUDES it.

    r11 = out.row(11, named=True)  # |r|=60 vs past median (of 11 priors) 40 -> included
    assert r11["n_priors"] == 11 and r11["in_c2"] is True and r11["c2_reason"] is None


# --------------------------------------------------------------------------- 7. seal


def test_seal_strips_holdout_events() -> None:
    train_s, hold_s = "2026-01-15", "2026-07-20"  # holdout >= 2026-06-01

    def qf(ts_session):
        def f(ts: int):
            return _mid_q(100.0 if ts <= et_ns(ts_session, 10, 4, 58) else 101.0)

        return f

    tapes = {
        ("NVDA", train_s): _measure_tape(train_s, (9, 59, 0), (10, 36, 0), qf(train_s)),
        ("NVDA", hold_s): _measure_tape(hold_s, (9, 59, 0), (10, 36, 0), qf(hold_s)),
    }
    cal = _calendar(
        [
            {"release_id": "T", "cls": "cluster_1000", "session": train_s, "h": 10, "m": 0},
            {"release_id": "H", "cls": "cluster_1000", "session": hold_s, "h": 10, "m": 0},
        ]
    )
    audit = sw.assemble(cal, _getter(tapes), universe=("NVDA",))
    assert audit.filter(pl.col("session") == hold_s).height == 0  # holdout vanished
    assert audit.filter(pl.col("session") == train_s).height == 8  # 4 horizons x 2 forms
    assert set(audit["split"].unique().to_list()) == {"train"}


# --------------------------------------------------------------------------- 9. determinism


def test_assemble_is_deterministic() -> None:
    s = "2026-01-15"

    def qf(ts: int):
        if ts <= et_ns(s, 10, 4, 58):
            return _mid_q(100.0)
        if ts <= et_ns(s, 10, 20, 0):
            return _mid_q(101.0)
        return _mid_q(102.0)

    tape = _measure_tape(s, (9, 59, 0), (10, 36, 0), qf, marker_mid=102.0)
    cal = _calendar([{"release_id": "R1", "cls": "cluster_1000", "session": s, "h": 10, "m": 0}])
    getter = _getter({("NVDA", s): tape, ("TSLA", s): tape})
    a1 = sw.assemble(cal, getter, universe=("NVDA", "TSLA"))
    a2 = sw.assemble(cal, getter, universe=("NVDA", "TSLA"))
    assert a1.equals(a2)


# --------------------------------------------------------------------------- 5 & 8. ordering guards


def test_compute_atlas_refuses_without_floors(tmp_path) -> None:
    cal = _calendar([{"release_id": "R1", "cls": "cluster_1000", "session": "2026-01-15", "h": 10, "m": 0}])
    with pytest.raises(FileNotFoundError, match="cost_floors"):
        sw.compute_atlas(cal, _getter({}), split="train", out_dir=tmp_path)


def test_validate_refused_without_pass_list(tmp_path) -> None:
    # floors present, pass list ABSENT -> validate refused with a clear error.
    (tmp_path / "cost_floors.json").write_text(
        json.dumps({"class_floor_bps": {"cluster_1000": 3.0}, "per_symbol": {}}), encoding="utf-8"
    )
    cal = _calendar([{"release_id": "R1", "cls": "cluster_1000", "session": "2026-01-15", "h": 10, "m": 0}])
    with pytest.raises(FileNotFoundError, match="train_pass_list"):
        sw.compute_atlas(cal, _getter({}), split="validate", out_dir=tmp_path)


# --------------------------------------------------------------------------- loader + converter


def test_loader_preserves_crossed_and_drops_broken(tmp_path) -> None:
    sw._read_month.cache_clear()
    s = "2026-01-15"
    root = tmp_path / "bbo1s"
    frame = _frame(
        [
            _row(et_ns(s, 4, 0, 0), 98.0, 99.0),    # pre-market kept (A5 anchor needs it)
            _row(et_ns(s, 10, 0, 0), 99.0, 100.0),  # normal
            _row(et_ns(s, 10, 0, 1), 100.05, 100.0),  # crossed -> KEPT (must be visible)
            _row(et_ns(s, 10, 0, 2), 0.0, 100.0),   # broken bid<=0 -> dropped
        ]
    )
    p = partition_path(root, "NVDA", "2026-01")
    p.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(p)

    got = sw.load_bbo_for_session("NVDA", s, out_dir=root)
    assert got is not None
    ts = got["ts"].to_list()
    assert et_ns(s, 4, 0, 0) in ts  # pre-market retained
    assert et_ns(s, 10, 0, 1) in ts  # crossed retained
    assert et_ns(s, 10, 0, 2) not in ts  # broken dropped
    assert sw.load_bbo_for_session("TSLA", s, out_dir=root) is None  # absent partition


def test_anchor_conversion_handles_all_forms() -> None:
    s = "2026-01-15"
    target = et_ns(s, 14, 0, 0)
    assert sw._anchor_utc_ns(target, s) == target  # int passthrough (UTC ns)
    assert sw._anchor_utc_ns(datetime(2026, 1, 15, 14, 0, 0), s) == target  # naive -> ET
    assert sw._anchor_utc_ns(datetime(2026, 1, 15, 14, 0, 0, tzinfo=ET), s) == target  # ET aware
    utc = ZoneInfo("UTC")
    assert sw._anchor_utc_ns(datetime(2026, 1, 15, 19, 0, 0, tzinfo=utc), s) == target  # UTC->ET
    assert sw._anchor_utc_ns("14:00:00", s) == target  # HH:MM:SS string


# --------------------------------------------------------------------------- floors + end-to-end


def test_cost_floors_then_atlas_end_to_end(tmp_path) -> None:
    # Two names, one class, one session: floors must be written FIRST and the atlas
    # then loads them. Exercises the full floors -> atlas ordering + outputs.
    s = "2026-01-15"

    def qf(ts: int):
        if ts <= et_ns(s, 10, 4, 58):
            return _mid_q(100.0)
        if ts <= et_ns(s, 10, 20, 0):
            return _mid_q(101.0)
        return _mid_q(102.0)

    tapes = {(sym, s): _measure_tape(s, (9, 59, 0), (10, 36, 0), qf, marker_mid=102.0)
             for sym in ("NVDA", "TSLA")}
    cal = _calendar([{"release_id": "R1", "cls": "cluster_1000", "session": s, "h": 10, "m": 0}])
    getter = _getter(tapes)

    floors = sw.compute_cost_floors(cal, getter, out_dir=tmp_path, universe=("NVDA", "TSLA"))
    assert sw.floors_path(tmp_path).exists()
    # spread = 0.02 on a ~100 mid -> ~2 bps; floor = 2 + 1.0 + 0.25 ~ 3.25.
    per = floors["per_symbol"]["cluster_1000"]["NVDA"]
    assert per["floor_bps"] == pytest.approx(per["median_spread_bps"] + 1.25)
    assert floors["class_floor_bps"]["cluster_1000"] is not None

    res = sw.compute_atlas(cal, getter, split="train", out_dir=tmp_path, universe=("NVDA", "TSLA"))
    assert sw.atlas_md_path("train", tmp_path).exists()
    assert sw.atlas_events_path("train", tmp_path).exists()
    assert sw.pass_list_path(tmp_path).exists()
    # 5 classes x 2 forms x 4 horizons = 40 cells always reported.
    assert res["n_cells"] == 40
    # tiny synthetic N -> nothing can pass the N>=150/sessions>=40 floor.
    assert res["n_passing"] == 0
    kept = pl.read_parquet(sw.atlas_events_path("train", tmp_path)).filter(pl.col("status") == "kept")
    assert kept.height > 0  # the h30/h60/h120 C1 rows for both names are kept
