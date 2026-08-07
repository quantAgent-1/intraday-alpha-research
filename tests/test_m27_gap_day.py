"""Tests for the M27 gap-day reversion harness (``research_screens.gap_day``).

Synthetic fixtures + hand-derived literals ONLY -- no real data lake, no network
(the family's single registered look is the orchestrator's). Covers all 14 checks
in DESIGN.md section 3: holdout guard; instant pins + DST (EDT/EST); nested
thresholds (t100 subset of t50, same frame); direction pin (fade); latency
determinism (sha256 convention, bounds, legs differ); taker-fill semantics +
hand-computed event; floors-before-means ordering + floor formula; early-close
drop (EARLY_CLOSE_DATES import identity); searchsorted guard; the pass-bar all-of
logic incl. the 3/5-names prong and the UNDERPOWERED band; one-look gate locality;
funnel reconciliation; ADIA helpers imported by identity; writer smoke end-to-end.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
import pytest

from enginev51.data.noii import et_ns
from enginev51.protocol import SealViolation
from enginev51.research_screens import gap_day as gd
from enginev51.research_screens import sizing_shadow
from enginev51.research_screens.sched_window import EARLY_CLOSE_DATES as SW_EARLY_CLOSE

NS = 1_000_000_000
SLIP = gd.SLIP_BPS * 1e-4  # 0.00005


# --------------------------------------------------------------------------- builders


def _bbo(rows: list[tuple[int, float, float]]) -> pl.DataFrame:
    """A synthetic bbo-1s frame (ts_ns, bid, ask) -- the 3 columns gap_day reads."""
    return pl.DataFrame(
        rows, schema={"ts": pl.Int64, "bid": pl.Float64, "ask": pl.Float64}, orient="row"
    ).sort("ts")


def _q(session: str, h: int, m: int, s: int, bid: float, ask: float) -> tuple[int, float, float]:
    return (et_ns(session, h, m, s), bid, ask)


def _bars_loader(bars: dict[str, list[tuple[str, float, float]]]) -> gd.BarsLoader:
    return lambda sym: bars.get(sym, [])


def _bbo_getter(quotes: dict[tuple[str, str], pl.DataFrame]) -> gd.BboGetter:
    return lambda sym, session: quotes.get((sym, session))


def _events_frame(rows: list[dict]) -> pl.DataFrame:
    """A synthetic events frame carrying only the columns cell_stats/adia read."""
    return pl.DataFrame(
        rows,
        schema={
            "symbol": pl.Utf8, "session": pl.Utf8, "net_bps": pl.Float64,
            "is_t100": pl.Boolean, "g_bps": pl.Float64,
        },
        orient="row",
    )


def _write_floors(out_dir, pooled: float) -> None:
    (out_dir / "cost_floors.json").write_text(
        json.dumps({"pooled_floor_bps": pooled, "per_name": {}}), encoding="utf-8"
    )


# =========================================================================== 1


def test_holdout_guard_refuses_ge_seal():
    """assert_before_holdout raises on/after the 2026-06-01 seal, passes below it."""
    # SealViolation, not AssertionError: the guard must survive `python -O` (B7/J2).
    with pytest.raises(SealViolation):
        gd.assert_before_holdout(date(2026, 6, 1))
    gd.assert_before_holdout(date(2026, 5, 31))  # no raise


# =========================================================================== 2


def test_instant_pins_and_dst_both_directions():
    """09:35/15:45 are ET wall-clock, zoneinfo-converted (DST both ways)."""
    assert gd.DECISION_HMS == (9, 35, 0)
    assert gd.EXIT_HMS == (15, 45, 0)
    et = ZoneInfo("America/New_York")

    def expect(session, h, m):
        d = date.fromisoformat(session)
        dt = datetime(d.year, d.month, d.day, h, m, 0, tzinfo=et)
        return int(dt.timestamp()) * NS

    # winter session = EST (UTC-5); summer = EDT (UTC-4). et_ns must match both.
    assert et_ns("2024-01-03", *gd.DECISION_HMS) == expect("2024-01-03", 9, 35)
    assert et_ns("2024-07-01", *gd.DECISION_HMS) == expect("2024-07-01", 9, 35)
    assert et_ns("2024-01-03", *gd.EXIT_HMS) == expect("2024-01-03", 15, 45)
    assert et_ns("2024-07-01", *gd.EXIT_HMS) == expect("2024-07-01", 15, 45)
    # 09:35 ET is a different UTC wall-time across the DST boundary (14:35Z vs 13:35Z).
    assert et_ns("2024-01-03", 9, 35, 0) % (24 * 3600 * NS) != (
        et_ns("2024-07-01", 9, 35, 0) % (24 * 3600 * NS)
    )


# =========================================================================== helpers for events


def _revert_scenario(session: str = "2024-03-15"):
    """One up-gap, quote-reverting-down session -> a winning fade (hand-computed)."""
    sym = "KLAC"
    bars = {sym: [("2024-03-14", 100.0, 100.0), (session, 101.0, 99.0)]}
    quotes = {
        (sym, session): _bbo([
            _q(session, 9, 35, 0, 100.0, 100.2),   # entry prevailing (mid 100.1)
            _q(session, 15, 45, 0, 99.0, 99.2),    # exit prevailing  (mid 99.1)
        ])
    }
    return sym, session, _bars_loader(bars), _bbo_getter(quotes)


# =========================================================================== 4


def test_direction_is_fade():
    """g>0 => side -1 (short the up-gap); g<0 => side +1; a reverting up-gap wins."""
    sym, session, load_bars, get_bbo = _revert_scenario()
    ev, funnel = gd.build_events(
        universe=(sym,), start=date(2023, 8, 1), end=date(2026, 5, 31),
        load_bars=load_bars, get_bbo=get_bbo,
    )
    row = ev.filter(pl.col("session") == session).row(0, named=True)
    assert row["g_bps"] > 0
    assert row["side"] == -1               # FADE the up-gap
    assert row["gross_bps"] > 0            # reverted down => the short profits
    # down-gap => side +1
    down_bars = {sym: [("2024-03-14", 100.0, 100.0), ("2024-03-15", 99.0, 99.0)]}
    down_q = {(sym, "2024-03-15"): _bbo([
        _q("2024-03-15", 9, 35, 0, 98.9, 99.1),
        _q("2024-03-15", 15, 45, 0, 98.9, 99.1),
    ])}
    ev2, _ = gd.build_events(
        universe=(sym,), load_bars=_bars_loader(down_bars), get_bbo=_bbo_getter(down_q),
    )
    assert ev2.row(0, named=True)["side"] == 1


# =========================================================================== 3


def test_nested_thresholds_same_frame(tmp_path):
    """t100 is a subset of t50 flagged in the SAME frame (is_t100)."""
    sym = "KLAC"
    # gaps: +75 bps (t50 only) and +150 bps (t100) on two sessions.
    bars = {sym: [
        ("2024-03-13", 100.0, 100.0),
        ("2024-03-14", 100.75, 100.0),   # g = +75 bps
        ("2024-03-15", 101.5, 100.0),    # g = +150 bps
    ]}
    quotes = {}
    for s in ("2024-03-14", "2024-03-15"):
        quotes[(sym, s)] = _bbo([
            _q(s, 9, 35, 0, 100.0, 100.1),
            _q(s, 15, 45, 0, 100.0, 100.1),
        ])
    ev, _ = gd.build_events(universe=(sym,), load_bars=_bars_loader(bars), get_bbo=_bbo_getter(quotes))
    assert ev.height == 2
    t100_rows = ev.filter(pl.col("is_t100"))
    assert t100_rows.height == 1
    assert abs(t100_rows.row(0, named=True)["g_bps"]) >= gd.THRESH_T100
    assert ev.filter(~pl.col("is_t100")).row(0, named=True)["g_bps"] == pytest.approx(75.0, abs=1e-6)
    # cell_stats: t100 N <= t50 N over the SAME frame.
    _write_floors(tmp_path, 5.0)
    s50 = gd.cell_stats(ev, gd.THRESH_T50, out_dir=tmp_path)
    s100 = gd.cell_stats(ev, gd.THRESH_T100, out_dir=tmp_path)
    assert s50["N"] == 2 and s100["N"] == 1


# =========================================================================== 5


def test_latency_determinism_bounds_and_legs():
    """sha256 seeding convention: deterministic, bounded [5,25]s, legs differ."""
    v1 = gd.latency_ns("KLAC", "2024-01-03", "entry")
    v2 = gd.latency_ns("KLAC", "2024-01-03", "entry")
    assert v1 == v2  # deterministic (never python hash())
    # hand-computed against the repo sha256 convention f"{seed}:{sym}:{session}:{leg}"
    h = hashlib.sha256(b"7:KLAC:2024-01-03:entry").digest()
    u = int.from_bytes(h[:8], "big") / 2**64
    assert v1 == int((5.0 + u * 20.0) * NS)
    assert 5 * NS <= v1 < 25 * NS
    # legs draw independently
    assert gd.latency_ns("KLAC", "2024-01-03", "entry") != gd.latency_ns(
        "KLAC", "2024-01-03", "exit"
    )


# =========================================================================== 6


def test_taker_fill_semantics_and_hand_computed_event():
    """Buy pays ask+slip, sell hits bid-slip; a full event nets the hand value."""
    session = "2024-03-15"
    dts = et_ns(session, *gd.DECISION_HMS)
    ts, bid, ask = np.array([dts]), np.array([100.0]), np.array([100.2])
    buy = gd.taker_fill(ts, bid, ask, dts, +1, "entry", "KLAC", session)
    sell = gd.taker_fill(ts, bid, ask, dts, -1, "entry", "KLAC", session)
    assert buy.price == pytest.approx(100.2 * (1 + SLIP))   # 100.205010
    assert sell.price == pytest.approx(100.0 * (1 - SLIP))  # 99.995
    assert buy.reason is None and sell.reason is None

    # Full reverting event: entry sell @100.0 bid, exit buy @99.2 ask.
    sym, s, load_bars, get_bbo = _revert_scenario(session)
    ev, _ = gd.build_events(universe=(sym,), load_bars=load_bars, get_bbo=get_bbo)
    row = ev.row(0, named=True)
    assert row["entry_fill"] == pytest.approx(99.995)
    assert row["exit_fill"] == pytest.approx(99.20496)
    assert row["gross_bps"] == pytest.approx(79.0079503975194, rel=1e-9)
    assert row["net_bps"] == pytest.approx(79.0079503975194 - gd.FEES_RT_BPS, rel=1e-9)


# =========================================================================== 7


def test_floors_before_means_order_and_formula(tmp_path):
    """cell_stats REFUSES without cost_floors.json; the floor formula is pinned."""
    ev = _events_frame([
        {"symbol": "KLAC", "session": "2024-01-03", "net_bps": 10.0,
         "is_t100": False, "g_bps": 60.0},
    ])
    with pytest.raises(FileNotFoundError):
        gd.cell_stats(ev, gd.THRESH_T50, out_dir=tmp_path)

    # Formula: RT_floor(name) = median(spread@0935 + spread@1545) + 2*SLIP + FEES.
    universe = ("KLAC", "MRVL", "LRCX", "TXN", "AMAT")
    bars, quotes = {}, {}
    session = "2024-01-03"
    per_name_floor_expected = {}
    for i, sym in enumerate(universe):
        d = 0.10 + 0.02 * i  # distinct absolute spread per name
        bid, ask = 100.0, 100.0 + d
        bars[sym] = [("2024-01-02", bid, bid), (session, bid, bid)]
        quotes[(sym, session)] = _bbo([
            _q(session, 9, 35, 0, bid, ask),
            _q(session, 15, 45, 0, bid, ask),
        ])
        spread = (ask - bid) / ((ask + bid) / 2.0) * 1e4
        per_name_floor_expected[sym] = round(2.0 * spread + 2.0 * gd.SLIP_BPS + gd.FEES_RT_BPS, 4)

    out = gd.write_cost_floors_first(
        universe=universe, start=date(2024, 1, 1), end=date(2024, 1, 31),
        load_bars=_bars_loader(bars), get_bbo=_bbo_getter(quotes), out_dir=tmp_path,
    )
    assert (tmp_path / "cost_floors.json").exists()
    for sym in universe:
        assert out["per_name"][sym]["floor_bps"] == pytest.approx(per_name_floor_expected[sym])
    pooled_expected = round(float(np.median(list(per_name_floor_expected.values()))), 4)
    assert out["pooled_floor_bps"] == pytest.approx(pooled_expected)
    # +2*SLIP+FEES == 1.25 over the raw round-trip spread median.
    for sym in universe:
        med = out["per_name"][sym]["median_rt_spread_bps"]
        assert out["per_name"][sym]["floor_bps"] - med == pytest.approx(1.25)


# =========================================================================== 8


def test_early_close_drop_and_import_identity():
    """EARLY_CLOSE_DATES is the M20 object by identity; such sessions are dropped."""
    assert gd.EARLY_CLOSE_DATES is SW_EARLY_CLOSE
    early = "2023-11-24"  # a listed NYSE half-day
    assert early in gd.EARLY_CLOSE_DATES
    sym = "KLAC"
    bars = {sym: [("2023-11-22", 100.0, 100.0), (early, 105.0, 100.0)]}  # g = +500 bps
    quotes = {(sym, early): _bbo([
        _q(early, 9, 35, 0, 100.0, 100.1),
        _q(early, 15, 45, 0, 100.0, 100.1),
    ])}
    ev, funnel = gd.build_events(universe=(sym,), load_bars=_bars_loader(bars), get_bbo=_bbo_getter(quotes))
    assert funnel["early_close"] == 1
    assert funnel["fired"] == 0
    assert ev.height == 0


# =========================================================================== 9


def test_searchsorted_guard_no_wrap():
    """A lookup before the first tick returns a MISS, never numpy's wrap to last."""
    session = "2024-03-15"
    t0 = et_ns(session, 10, 0, 0)
    ts = np.array([t0, t0 + 5 * NS])
    bid = np.array([50.0, 999.0])
    ask = np.array([50.1, 1000.0])
    q, reason = gd.quote_lookup(ts, bid, ask, t0 - NS)  # before the first tick
    assert q is None and reason == "no_quote"
    assert gd.quote_at(ts, bid, ask, t0 - NS) is None
    # the guard must not have wrapped to the future (999/1000) quote.
    ok, _ = gd.quote_lookup(ts, bid, ask, t0)
    assert ok == (50.0, 50.1)


# =========================================================================== 10


def _big_pass_frame(net: float = 50.0, n_sessions: int = 300, per_session: int = 2,
                    names=("KLAC", "MRVL", "LRCX", "TXN", "AMAT")) -> pl.DataFrame:
    rows = []
    for si in range(n_sessions):
        session = f"2024-{(si // 28) % 12 + 1:02d}-{si % 28 + 1:02d}-s{si}"
        for j in range(per_session):
            rows.append({
                "symbol": names[(si * per_session + j) % len(names)],
                "session": session, "net_bps": net, "is_t100": True, "g_bps": 120.0,
            })
    return _events_frame(rows)


def test_pass_bar_all_of_and_mutations(tmp_path):
    """Every PASS condition is necessary; UNDERPOWERED and BETWEEN bands are wired."""
    _write_floors(tmp_path, 5.0)  # bar = 2x5 = 10 bps; mean 50 clears it
    base = _big_pass_frame(net=50.0)  # N=600, sessions=300, all names +50
    s = gd.cell_stats(base, gd.THRESH_T50, out_dir=tmp_path)
    assert s["pass"] is True
    assert (s["N"] >= 400 and s["n_sessions"] >= 250 and s["meets_ci_lower_gt_0"]
            and s["meets_2x_floor"] and s["meets_3of5_names"] and not s["underpowered"])

    # (a) sessions floor: same N, only 240 unique sessions -> fail.
    few_sess = base.with_columns(
        (pl.col("session").str.slice(0, 7) + "-fixed").alias("session")
    )  # collapses to ~ up to 12 sessions
    assert gd.cell_stats(few_sess, gd.THRESH_T50, out_dir=tmp_path)["pass"] is False

    # (b) 2x-floor prong: raise the pooled floor so the bar (2x) exceeds the mean.
    _write_floors(tmp_path, 100.0)  # bar = 200 > mean 50
    s_floor = gd.cell_stats(base, gd.THRESH_T50, out_dir=tmp_path)
    assert s_floor["meets_2x_floor"] is False and s_floor["pass"] is False
    _write_floors(tmp_path, 5.0)  # restore

    # (c) CI-lower prong: alternating large +/- so the CI spans 0 (mean stays >0).
    straddle_rows = []
    for si in range(300):
        session = f"2024-str-{si}"
        for j in range(2):
            straddle_rows.append({
                "symbol": ("KLAC", "MRVL", "LRCX", "TXN", "AMAT")[(si * 2 + j) % 5],
                "session": session,
                "net_bps": 500.0 if (si % 2 == 0) else -480.0,
                "is_t100": True, "g_bps": 120.0,
            })
    straddle = _events_frame(straddle_rows)
    s_ci = gd.cell_stats(straddle, gd.THRESH_T50, out_dir=tmp_path)
    assert s_ci["meets_ci_lower_gt_0"] is False and s_ci["pass"] is False
    assert s_ci["between"] is True  # point>0 but CI spans 0 -> report-only

    # (d) 3/5-names prong: 2 names strongly +, 3 names slightly - (pooled mean/CI stay >0).
    name_rows = []
    for si in range(300):
        session = f"2024-nm-{si}"
        # two dominant positive names, many events
        for sym in ("KLAC", "MRVL"):
            name_rows.append({"symbol": sym, "session": session, "net_bps": 80.0,
                              "is_t100": True, "g_bps": 120.0})
        # three faintly-negative names, sparse (every 3rd session)
        if si % 3 == 0:
            for sym in ("LRCX", "TXN", "AMAT"):
                name_rows.append({"symbol": sym, "session": session, "net_bps": -1.0,
                                  "is_t100": True, "g_bps": 120.0})
    names_frame = _events_frame(name_rows)
    s_names = gd.cell_stats(names_frame, gd.THRESH_T50, out_dir=tmp_path)
    assert s_names["n_names_positive"] == 2
    assert s_names["meets_3of5_names"] is False and s_names["pass"] is False
    assert s_names["meets_ci_lower_gt_0"] is True  # only the names prong killed it

    # (e) UNDERPOWERED band: N < 200.
    small = _big_pass_frame(net=50.0, n_sessions=60, per_session=2)  # N=120
    s_small = gd.cell_stats(small, gd.THRESH_T50, out_dir=tmp_path)
    assert s_small["underpowered"] is True and s_small["pass"] is False


# =========================================================================== 11


def test_one_look_gate_locality(tmp_path, monkeypatch):
    """A present look_state.json refuses a second look; state is per-directory."""
    a = tmp_path / "A"
    b = tmp_path / "B"
    gd.assert_look_not_spent(a)  # empty dir -> no raise
    gd.mark_look_spent(a, trial_id="M27-gap-day")
    assert (gd.out_dir_for(a) / "look_state.json").exists()
    with pytest.raises(RuntimeError):
        gd.assert_look_not_spent(a)
    gd.assert_look_not_spent(b)  # a different dir is unaffected (locality)
    # defect rerun requires a non-empty reason (checked before any ledger write).
    with pytest.raises(ValueError):
        gd.assert_look_not_spent(a, defect_rerun=True, reason=" ")
    # a valid defect rerun appends a ledger note (monkeypatched -- no real ledger write).
    calls = []
    monkeypatch.setattr(gd, "ledger_append", lambda kind, payload: calls.append((kind, payload)))
    gd.assert_look_not_spent(a, defect_rerun=True, reason="fix seed bug")
    assert calls and calls[0][1]["event"] == "M27_DEFECT_RERUN"


# =========================================================================== 12


def test_funnel_reconciles():
    """skips + below + fired == candidates, each candidate in exactly one bucket."""
    sym = "KLAC"
    bars = {sym: [
        ("2024-03-11", 100.0, 100.0),  # predecessor of the first candidate (in window)
        ("2024-03-12", 100.2, 100.0),  # g=+20 bps -> below_t50
        ("2024-03-13", 101.0, 100.0),  # g=+100 -> fired
        ("2024-03-14", 102.0, 100.0),  # g=+200 -> no quotes -> no_quote_entry
        ("2023-11-24", 105.0, 100.0),  # early_close (out of monotone order ok)
    ]}
    # only supply quotes for the fired session
    quotes = {(sym, "2024-03-13"): _bbo([
        _q("2024-03-13", 9, 35, 0, 100.0, 100.1),
        _q("2024-03-13", 15, 45, 0, 100.0, 100.1),
    ])}
    ev, f = gd.build_events(universe=(sym,), load_bars=_bars_loader(bars), get_bbo=_bbo_getter(quotes))
    skip_sum = (f["no_bar"] + f["early_close"] + f["below_t50"]
                + f["no_quote_entry"] + f["no_quote_exit"] + f["stale_quote"] + f["fired"])
    assert skip_sum == f["candidates"]
    assert f["fired"] == 1 and ev.height == 1
    assert f["below_t50"] == 1 and f["early_close"] == 1 and f["no_quote_entry"] == 1


# =========================================================================== 13


def test_adia_helpers_imported_by_identity():
    """The ADIA No.19 kernels are the M23 objects (never re-implemented)."""
    assert gd.sr_native is sizing_shadow.sr_native
    assert gd.psr is sizing_shadow.psr
    assert gd.min_trl is sizing_shadow.min_trl
    assert gd.sample_moments is sizing_shadow.sample_moments
    ev = _events_frame([
        {"symbol": "KLAC", "session": f"2024-01-{d:02d}", "net_bps": 40.0 + d,
         "is_t100": True, "g_bps": 120.0}
        for d in range(1, 20)
    ])
    panel = gd.adia_panel(ev)
    assert panel["T"] == 19 and panel["n_events"] == 19
    assert panel["sr_native"] is not None and panel["mean_usd"] is not None


# =========================================================================== 14


def test_writer_smoke_end_to_end(tmp_path):
    """Floors-first -> build -> stats -> panel -> strata -> ground-truth -> write."""
    sym = "KLAC"
    bars = {sym: [("2024-03-11", 100.0, 100.0)]}
    quotes = {}
    # 6 fired sessions with reverting quotes (winning fades) + varied gaps/spreads.
    prev = 100.0
    for i in range(6):
        s = f"2024-03-{12 + i:02d}"
        openp = prev * (1 + (0.010 + 0.002 * i))  # +100..+200 bps gaps
        bars[sym].append((s, openp, prev * 0.99))
        quotes[(sym, s)] = _bbo([
            _q(s, 9, 35, 0, openp - 0.1, openp + 0.1),
            _q(s, 15, 45, 0, prev - 0.1, prev + 0.1),  # reverts toward prev_close
        ])
        prev = prev * 0.99

    load_bars, get_bbo = _bars_loader(bars), _bbo_getter(quotes)
    floors = gd.write_cost_floors_first(
        universe=(sym,), start=date(2024, 1, 1), end=date(2024, 12, 31),
        load_bars=load_bars, get_bbo=get_bbo, out_dir=tmp_path,
    )
    ev, funnel = gd.build_events(
        universe=(sym,), start=date(2024, 1, 1), end=date(2024, 12, 31),
        load_bars=load_bars, get_bbo=get_bbo,
    )
    assert ev.height == 6
    t50 = gd.cell_stats(ev, gd.THRESH_T50, out_dir=tmp_path)
    t100 = gd.cell_stats(ev, gd.THRESH_T100, out_dir=tmp_path)
    panel = gd.adia_panel(ev)
    strata = gd.report_strata(ev)
    gt = gd.ground_truth(ev)
    assert gt.height <= 10
    atlas = gd.build_atlas_md("M27-gap-day", t50, t100, panel, strata, funnel, floors, seed=7)
    assert atlas.isascii()  # ASCII console/report safety

    paths = gd.write_outputs(
        tmp_path, "M27-gap-day", ev, t50, t100, panel, strata, funnel, floors, atlas, gt,
    )
    for key in ("atlas", "cells", "events", "ground_truth"):
        assert paths[key].exists()
    assert (tmp_path / "cost_floors.json").exists()
    # cells.json round-trips as valid JSON with the flag keys (not verdicts).
    cells = json.loads(paths["cells"].read_text(encoding="utf-8"))
    assert "t50" in cells and "t100" in cells and "adia_panel" in cells
