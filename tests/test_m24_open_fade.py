"""Tests for the M24 opening-auction dislocation fade harness
(``research_screens.open_fade``).

Synthetic fixtures + hand-derived literals ONLY -- no real data lake, no network
(the family's single registered look is the orchestrator's). Mirrors the fixture
style of ``test_m22_earnings_close`` / ``test_m23_sizing_shadow``. Covers all 14
checks in DESIGN.md section 3: the holdout/seal guard, the pinned 33-name universe,
the 09:28:30 signal instant (with March + November DST-boundary coverage), the
near-and-ref requirement, the AGAINST-basis direction (one hand-computed end-to-end
event), the nested 25/50 thresholds, the 0.3 bps fee pin, the raw bars1d open/close
price source, the overnight-gap stratum + gap_mr fence, the PASS/UNDERPOWERED/BETWEEN
cell logic (both n-floors isolated), the unrelocatable one-look gate, the
sizing_shadow helper identity, the session-clustered CI, and the funnel
reconciliation -- plus a writer smoke test through the full assembly.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import polars as pl
import pytest

from enginev51.apps import run_m11
from enginev51.data.noii import NOII_SCHEMA, et_ns
from enginev51.protocol import SealViolation
from enginev51.research_screens import open_fade as of
from enginev51.research_screens import sizing_shadow as ss

# --------------------------------------------------------------------------- builders


def _noii_row(ts: int, near: float, ref: float, side: str = "B",
              imb: float = 1000.0, paired: float = 500.0, far: float = 0.0) -> dict:
    return {
        "ts": ts, "side": side, "imbalance_shares": imb, "paired_shares": paired,
        "near_price": near, "far_price": far, "ref_price": ref,
    }


def _noii(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=NOII_SCHEMA, orient="row").sort("ts")


def _write_partition(noii_dir, sym: str, month: str, rows: list[dict]) -> None:
    d = noii_dir / sym.upper()
    d.mkdir(parents=True, exist_ok=True)
    _noii(rows).write_parquet(d / f"{month}.parquet")


def _utc_noon_ns(session: str) -> int:
    d = date.fromisoformat(session)
    return int(datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=UTC).timestamp()) * 1_000_000_000


def _write_bars(bars_dir, sym: str, bars: list[tuple[str, float, float]]) -> None:
    """bars = [(session_iso, open, close), ...] -> raw bars1d parquet (ts, open, close)."""
    rows = [{"ts": _utc_noon_ns(s), "open": o, "close": c} for s, o, c in bars]
    bars_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        rows, schema={"ts": pl.Int64, "open": pl.Float64, "close": pl.Float64}, orient="row"
    ).write_parquet(bars_dir / f"{sym.upper()}.parquet")


def _ev(session: str, *, symbol: str = "NVDA", basis: float = 30.0, net: float = 5.0,
        gap: float | None = None, imb_agree: bool = False, side: int = -1,
        open_px: float = 100.0, close_px: float = 99.0) -> dict:
    return {
        "session": session, "symbol": symbol, "basis_open_bps": basis, "side": side,
        "open_px": open_px, "close_px": close_px, "gross_bps": net + of.SEC_TAF_SELL_BPS,
        "net_bps": net, "overnight_gap_bps": gap, "imb_side_agrees": imb_agree,
        "imbalance_shares": 1000.0, "is_t50": abs(basis) >= of.THRESH_T50,
    }


def _events(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=of.EVENT_SCHEMA, orient="row")


# =========================================================================== 1


def test_holdout_guard(tmp_path):
    """build_events refuses end >= 2026-06-01; a post-seal session never enters."""
    # SealViolation, not AssertionError: the guard must survive `python -O` (B7/J2).
    with pytest.raises(SealViolation):
        of.assert_before_holdout(date(2026, 6, 1))
    with pytest.raises(SealViolation):
        of.build_events(object(), start=of.START, end=date(2026, 6, 1),
                        universe=("NVDA",), noii_dir=tmp_path / "noii",
                        bars_dir=tmp_path / "bars")

    # A June-2026 partition holds a post-seal session; under the default END the
    # June month is never iterated, so that session is structurally excluded.
    noii_dir, bars_dir = tmp_path / "noii", tmp_path / "bars"
    _write_partition(noii_dir, "NVDA", "2026-06",
                     [_noii_row(et_ns("2026-06-02", 9, 28, 30), near=100.5, ref=100.0)])
    _write_bars(bars_dir, "NVDA", [("2026-06-02", 100.0, 99.0)])
    events, funnel = of.build_events(object(), start=of.START, end=of.END,
                                     universe=("NVDA",), noii_dir=noii_dir, bars_dir=bars_dir)
    assert events.height == 0
    assert funnel["candidates"] == 0


# =========================================================================== 2


def test_universe_pinned():
    """UNIVERSE is the explicit alphabetical 33-tuple (a lake glob is NOT used)."""
    expected = tuple(sorted((
        "AAPL", "ADBE", "AMAT", "AMD", "AMGN", "AVGO", "BKNG", "CMCSA", "COST", "CSCO",
        "GILD", "GOOGL", "HON", "INTC", "INTU", "ISRG", "KLAC", "LRCX", "MDLZ", "META",
        "MRVL", "MSFT", "MU", "NFLX", "NVDA", "PEP", "PLTR", "QCOM", "SBUX", "TMUS",
        "TSLA", "TXN", "VRTX",
    )))
    assert isinstance(of.UNIVERSE, tuple)
    assert len(of.UNIVERSE) == 33
    assert of.UNIVERSE == expected
    assert list(of.UNIVERSE) == sorted(of.UNIVERSE)


# =========================================================================== 3


def test_signal_instant_pin():
    """SIGNAL_HMS == (9,28,30); 09:28:30.000 exact is used, 09:28:31 is ignored (D1).
    March-DST (EDT) and November-DST (EST) sessions both resolve via zoneinfo -- a
    naive UTC-4 offset would mis-place the EST instant."""
    assert of.SIGNAL_HMS == (9, 28, 30)
    for session in ("2024-03-11", "2024-11-04"):  # EDT then EST
        ts_at = et_ns(session, 9, 28, 30)
        ts_after = et_ns(session, 9, 28, 31)
        msgs = _noii([
            _noii_row(ts_at, near=100.20, ref=100.0),        # the governing message
            _noii_row(ts_after, near=200.0, ref=100.0),      # after the instant -> ignored
        ])
        sig, reason = of.open_basis_at(msgs, session)
        assert reason is None
        assert sig["ts"] == ts_at
        assert sig["basis_open_bps"] == pytest.approx(20.0)


# =========================================================================== 4


def test_signal_requires_near_and_ref():
    """near=0 or ref=0 rows are never selected; no_near_ref when nothing qualifies;
    no_msgs on an empty / all-after-cutoff frame."""
    session = "2024-03-11"
    ts = et_ns(session, 9, 28, 0)
    assert of.open_basis_at(_noii([_noii_row(ts, near=0.0, ref=100.0)]), session) == (None, "no_near_ref")
    assert of.open_basis_at(_noii([_noii_row(ts, near=100.0, ref=0.0)]), session) == (None, "no_near_ref")
    assert of.open_basis_at(_noii([]), session) == (None, "no_msgs")
    # only a post-cutoff message -> no_msgs (nothing at-or-before the instant)
    late = _noii([_noii_row(et_ns(session, 9, 29, 0), near=100.2, ref=100.0)])
    assert of.open_basis_at(late, session) == (None, "no_msgs")
    # a valid message qualifies
    sig, reason = of.open_basis_at(_noii([_noii_row(ts, near=100.20, ref=100.0)]), session)
    assert reason is None and sig["basis_open_bps"] == pytest.approx(20.0)


# =========================================================================== 5


def test_direction_pin_fade():
    """Direction is AGAINST the basis. HAND-COMPUTED end-to-end event:

    basis_open = +30 bps (>0) => side = -1 (SELL SHORT at the open).
    open_px=100.00, close_px=99.00 (the cross reverted DOWN into the close):
        gross_bps = side*(close/open - 1)*1e4 = -1*(99/100 - 1)*1e4
                  = -1*(-0.01)*1e4 = +100.0 bps
        net_bps   = 100.0 - 0.3 (sell-side SEC/TAF) = +99.7 bps   (short PROFITS)
    overnight_gap_bps = (open/prev_close - 1)*1e4 = (100/98 - 1)*1e4 = +204.0816 bps
    imb_side_agrees: side_flag 'B' with basis>0 => True ; |30| < 50 => is_t50 False.

    A WITH mutation (side = +1 for basis>0) would give gross = -100 and FAIL here."""
    sig = {"basis_open_bps": 30.0, "side_flag": "B", "imbalance_shares": 1000.0,
           "symbol": "NVDA", "session": "2024-03-11"}
    row = of.fade_event(sig, 100.0, 99.0, prev_close=98.0)
    assert row["side"] == -1
    assert row["gross_bps"] == pytest.approx(100.0)
    assert row["net_bps"] == pytest.approx(99.7)
    assert row["overnight_gap_bps"] == pytest.approx(204.0816, abs=1e-3)
    assert row["imb_side_agrees"] is True
    assert row["is_t50"] is False

    # basis < 0 => side = +1 (BUY); close above open profits.
    sig_neg = {"basis_open_bps": -30.0, "side_flag": "A", "imbalance_shares": 1000.0,
               "symbol": "NVDA", "session": "2024-03-11"}
    row_neg = of.fade_event(sig_neg, 100.0, 101.0)
    assert row_neg["side"] == 1
    assert row_neg["net_bps"] == pytest.approx(99.7)
    assert row_neg["overnight_gap_bps"] is None  # no prior close -> strata null, event kept
    assert row_neg["imb_side_agrees"] is True     # 'A' with basis<0 agrees


# =========================================================================== 6


def test_threshold_pins_nested():
    """THRESH 25/50 pinned; is_t50 == (|basis|>=50) and t50 is a SUBSET of t25 on the
    SAME frame (never a re-scan)."""
    assert of.THRESH_T25 == 25.0 and of.THRESH_T50 == 50.0
    events = _events([
        _ev("2024-01-02", basis=30.0),   # t25 only
        _ev("2024-01-03", basis=60.0),   # t50
        _ev("2024-01-04", basis=-55.0),  # t50 (negative)
        _ev("2024-01-05", basis=26.0),   # t25 only
    ])
    t25 = events.filter(pl.col("basis_open_bps").abs() >= of.THRESH_T25)
    t50 = events.filter(pl.col("basis_open_bps").abs() >= of.THRESH_T50)
    assert t25.height == 4 and t50.height == 2
    # is_t50 flag matches the |basis|>=50 predicate exactly
    assert events["is_t50"].to_list() == [False, True, True, False]
    # nestedness: every t50 session is a t25 session
    assert set(t50["session"].to_list()).issubset(set(t25["session"].to_list()))


# =========================================================================== 7


def test_fee_pin():
    """net = gross - 0.3 exactly; the constant equals run_m11's SEC_TAF_SELL_BPS."""
    assert of.SEC_TAF_SELL_BPS == 0.3
    assert of.SEC_TAF_SELL_BPS == run_m11.SEC_TAF_SELL_BPS == of.M11_SEC_TAF_SELL_BPS
    sig = {"basis_open_bps": 40.0, "side_flag": "B", "imbalance_shares": 0.0}
    row = of.fade_event(sig, 100.0, 98.5)
    assert row["net_bps"] == pytest.approx(row["gross_bps"] - 0.3)


# =========================================================================== 8


def test_price_source_pins(tmp_path):
    """Entry from raw bars1d ``open``, exit from raw bars1d ``close``, same session
    row (no adjusted source). load_daily_bars keeps BOTH columns and past-only
    prev_close ordering; build_events wires open_px/close_px straight from the bar."""
    bars_dir = tmp_path / "bars"
    _write_bars(bars_dir, "NVDA", [
        ("2024-03-08", 90.0, 98.0),    # prior session
        ("2024-03-11", 100.0, 99.0),   # the fired session
    ])
    bars = of.load_daily_bars("NVDA", bars_dir=bars_dir)
    assert bars["session"].to_list() == ["2024-03-08", "2024-03-11"]
    assert bars["open_px"].to_list() == [90.0, 100.0]
    assert bars["close_px"].to_list() == [98.0, 99.0]

    noii_dir = tmp_path / "noii"
    _write_partition(noii_dir, "NVDA", "2024-03",
                     [_noii_row(et_ns("2024-03-11", 9, 28, 30), near=100.30, ref=100.0)])
    events, _funnel = of.build_events(object(), start=date(2024, 3, 1), end=date(2024, 3, 31),
                                      universe=("NVDA",), noii_dir=noii_dir, bars_dir=bars_dir)
    assert events.height == 1
    r = events.row(0, named=True)
    assert r["open_px"] == 100.0 and r["close_px"] == 99.0  # entry=open, exit=close
    assert r["session"] == "2024-03-11" and r["side"] == -1  # basis +30 -> fade short


# =========================================================================== 9


def test_gap_stratum_and_fence(tmp_path):
    """overnight_gap uses the immediately-preceding raw close (off-by-one guard), and
    corr(basis, gap) -- the gap_mr fence -- is present in the strata / cells.json."""
    bars_dir, noii_dir = tmp_path / "bars", tmp_path / "noii"
    _write_bars(bars_dir, "NVDA", [("2024-03-08", 90.0, 98.0), ("2024-03-11", 100.0, 99.0)])
    _write_partition(noii_dir, "NVDA", "2024-03",
                     [_noii_row(et_ns("2024-03-11", 9, 28, 30), near=100.30, ref=100.0)])
    events, _f = of.build_events(object(), start=date(2024, 3, 1), end=date(2024, 3, 31),
                                 universe=("NVDA",), noii_dir=noii_dir, bars_dir=bars_dir)
    # prev_close = 98 (the 03-08 close), NOT 99 (same-day) -> gap = (100/98 - 1)*1e4
    assert events.row(0, named=True)["overnight_gap_bps"] == pytest.approx(204.0816, abs=1e-3)

    strata = of.build_strata(_events([
        _ev("2024-01-02", basis=30.0, gap=50.0, net=5.0),
        _ev("2024-01-03", basis=60.0, gap=-20.0, net=-3.0),
        _ev("2024-01-04", basis=-40.0, gap=10.0, net=2.0),
        _ev("2024-01-05", basis=-55.0, gap=-30.0, net=4.0),
    ]))
    assert "corr_basis_gap" in strata
    assert strata["corr_basis_gap"] is not None
    assert -1.0 <= strata["corr_basis_gap"] <= 1.0
    assert len(strata["gap_x_basis_2x2"]) == 4  # 2x2 gap-sign x basis-sign


# =========================================================================== 10


def test_pass_bar_logic():
    """PASS / UNDERPOWERED (n<150) / BETWEEN flags exactly per the registration."""
    # PASS: 300 events across 300 distinct sessions, net=5 constant (CI degenerate
    # lo=5>0), mean 5 >= 2.
    ok = of.cell_stats(_events([_ev(f"2024-s{i:04d}", basis=30.0, net=5.0)
                                for i in range(300)]), thresh=25.0)
    assert ok["n_fired"] == 300 and ok["n_sessions"] == 300
    assert ok["meets_n_fired_floor"] and ok["meets_n_sessions_floor"]
    assert ok["meets_ci_lower_gt_0"] and ok["meets_mean_floor"]
    assert ok["pass"] is True and ok["between_the_bars"] is False

    # UNDERPOWERED: n < 150.
    up = of.cell_stats(_events([_ev(f"2024-u{i:04d}", net=5.0) for i in range(100)]), thresh=25.0)
    assert up["n_fired"] == 100 and up["underpowered"] is True and up["pass"] is False

    # BETWEEN: point > 0 but CI spans 0 (wide +80/-70 dispersion, mean +5).
    wide = [_ev(f"2024-b{i:04d}", net=(80.0 if i % 2 == 0 else -70.0)) for i in range(300)]
    bt = of.cell_stats(_events(wide), thresh=25.0)
    assert bt["n_fired"] == 300 and bt["underpowered"] is False
    assert bt["mean_net_bps"] == pytest.approx(5.0)
    assert bt["meets_ci_lower_gt_0"] is False
    assert bt["between_the_bars"] is True and bt["pass"] is False

    # MEAN FLOOR binds: ci_lo>0 but mean 1 < 2 -> not pass, not between.
    lowmean = of.cell_stats(_events([_ev(f"2024-m{i:04d}", net=1.0) for i in range(300)]), thresh=25.0)
    assert lowmean["meets_ci_lower_gt_0"] is True and lowmean["meets_mean_floor"] is False
    assert lowmean["pass"] is False and lowmean["between_the_bars"] is False

    # n_FIRED FLOOR binds (isolates n_fired>=300): 200 events across 200 distinct
    # sessions, net=5 constant (ci_lo=5>0), mean>=2, and NOT underpowered (n>=150).
    # Only meets_n_fired_floor is False, so deleting it from cell_pass would wrongly
    # PASS this cell.
    nfew = of.cell_stats(_events([_ev(f"2024-n{i:04d}", net=5.0) for i in range(200)]), thresh=25.0)
    assert nfew["n_fired"] == 200 and nfew["n_sessions"] == 200
    assert nfew["underpowered"] is False
    assert nfew["meets_n_fired_floor"] is False and nfew["meets_n_sessions_floor"] is True
    assert nfew["meets_ci_lower_gt_0"] is True and nfew["meets_mean_floor"] is True
    assert nfew["pass"] is False

    # n_SESSIONS FLOOR binds (isolates n_sessions>=150): 300 events packed into 100
    # sessions (3 events/session), net=5 constant (ci_lo=5>0), mean>=2. Only
    # meets_n_sessions_floor is False, so deleting it from cell_pass would wrongly
    # PASS this cell.
    packed = of.cell_stats(
        _events([_ev(f"2024-p{i % 100:03d}", net=5.0) for i in range(300)]), thresh=25.0)
    assert packed["n_fired"] == 300 and packed["n_sessions"] == 100
    assert packed["underpowered"] is False
    assert packed["meets_n_fired_floor"] is True and packed["meets_n_sessions_floor"] is False
    assert packed["meets_ci_lower_gt_0"] is True and packed["meets_mean_floor"] is True
    assert packed["pass"] is False


# =========================================================================== 11


def test_one_look_gate_not_relocatable(tmp_path, monkeypatch):
    """No CLI out-dir; the gate is anchored to the canonical dir; a spent look refuses
    a second no-arg invocation; --defect-rerun requires --reason."""
    # (i) the CLI exposes no out-dir escape hatch.
    from enginev51.apps import run_m24_open_fade as cli
    assert "out_dir" not in {p.name for p in cli.main.params}

    # (ii) explicit-dir gate behaviour (defect-rerun rules).
    of.assert_look_not_spent(tmp_path)  # unspent -> allowed
    of.mark_look_spent(tmp_path, trial_id="M24-open-fade", git_sha="deadbeef")
    assert of.look_state_path(tmp_path).exists()
    with pytest.raises(RuntimeError, match="already spent"):
        of.assert_look_not_spent(tmp_path)
    with pytest.raises(ValueError, match="reason"):
        of.assert_look_not_spent(tmp_path, defect_rerun=True, reason=None)
    with pytest.raises(ValueError, match="reason"):
        of.assert_look_not_spent(tmp_path, defect_rerun=True, reason="   ")
    notes: list = []
    monkeypatch.setattr(of, "ledger_append", lambda kind, payload: notes.append((kind, payload)))
    of.assert_look_not_spent(tmp_path, defect_rerun=True, reason="fix off-by-one in exit ts")
    assert notes and notes[0][1]["event"] == "M24_DEFECT_RERUN"

    # (iii) the gate defaults to canonical_out_dir(); spend there, a no-arg re-check
    #       refuses (the only path the CLI uses). experiments_dir redirected.
    monkeypatch.setattr(of, "experiments_dir", lambda: tmp_path / "exp")
    assert of.canonical_out_dir() == tmp_path / "exp" / of.OUT_SUBDIR
    of.assert_look_not_spent()
    of.mark_look_spent(trial_id="M24-open-fade")
    with pytest.raises(RuntimeError, match="already spent"):
        of.assert_look_not_spent()


# =========================================================================== 12


def test_adia_helpers_imported():
    """psr / min_trl / sr_native (and sample_moments) are sizing_shadow's OBJECTS
    (identity), never local reimplementations."""
    assert of.psr is ss.psr
    assert of.min_trl is ss.min_trl
    assert of.sr_native is ss.sr_native
    assert of.sample_moments is ss.sample_moments

    # and the panel actually runs them on a fired stream.
    panel = of.adia_panel(_events([_ev(f"2024-p{i:04d}", net=(3.0 if i % 2 else 4.0))
                                   for i in range(40)]))
    assert panel["T"] == 40 and panel["sr_native"] is not None


# =========================================================================== 13


def test_clustered_ci_session_cluster():
    """A session with 2 reporters is ONE cluster: n=2 but n_sessions=1, and the
    single-cluster bootstrap is degenerate -> lo == hi == mean."""
    df = _events([
        _ev("2024-02-21", symbol="NVDA", net=4.0),
        _ev("2024-02-21", symbol="TSLA", net=8.0),
    ])
    m, lo, hi, n, ns = of._ci(df)
    assert n == 2 and ns == 1
    assert m == pytest.approx(6.0) and lo == pytest.approx(6.0) and hi == pytest.approx(6.0)


# =========================================================================== 14


def test_funnel_reconciles(tmp_path):
    """Synthetic month: every examined (sym, session) lands in exactly one bucket, so
    sum(counts) == candidates, with per-reason counts exact."""
    noii_dir, bars_dir = tmp_path / "noii", tmp_path / "bars"
    rows = [
        _noii_row(et_ns("2024-03-11", 9, 28, 30), near=100.30, ref=100.0),  # fired (+30)
        _noii_row(et_ns("2024-03-12", 9, 28, 0), near=0.0, ref=100.0),      # no_near_ref
        _noii_row(et_ns("2024-03-13", 9, 28, 0), near=100.0, ref=100.0),    # zero_basis
        _noii_row(et_ns("2024-03-14", 9, 28, 0), near=100.10, ref=100.0),   # below_t25 (+10)
        _noii_row(et_ns("2024-03-15", 9, 28, 0), near=100.50, ref=100.0),   # no_bar (+50)
        _noii_row(et_ns("2024-03-18", 9, 29, 0), near=100.30, ref=100.0),   # no_msgs (post-cutoff)
    ]
    _write_partition(noii_dir, "NVDA", "2024-03", rows)
    # bars present ONLY for the fired session and the below_t25 session.
    _write_bars(bars_dir, "NVDA", [("2024-03-11", 100.0, 99.0), ("2024-03-14", 100.0, 99.5)])

    events, funnel = of.build_events(object(), start=date(2024, 3, 1), end=date(2024, 3, 31),
                                     universe=("NVDA",), noii_dir=noii_dir, bars_dir=bars_dir)
    c = funnel["counts"]
    assert c == {"no_msgs": 1, "no_near_ref": 1, "zero_basis": 1,
                 "no_bar": 1, "below_t25": 1, "fired_t25": 1}
    assert funnel["candidates"] == 6
    assert sum(c.values()) == funnel["candidates"]
    assert funnel["reconciles"] is True
    assert events.height == 1 and events.row(0, named=True)["session"] == "2024-03-11"


# =========================================================================== 15 (writer smoke)


def test_writer_end_to_end(tmp_path, monkeypatch):
    """Synthetic end-to-end: build_events -> cell_stats (t25+t50) -> adia_panel ->
    build_atlas_md -> write_outputs into a REDIRECTED experiments dir. Asserts the
    four artifacts exist, ground_truth is <=10 rows on the documented schema,
    atlas.md is pure ASCII, and cells.json parses with disjoint t25/t50 keys."""
    import json

    noii_dir, bars_dir = tmp_path / "noii", tmp_path / "bars"
    _write_partition(noii_dir, "NVDA", "2024-03", [
        _noii_row(et_ns("2024-03-11", 9, 28, 30), near=100.30, ref=100.0),  # t25 (+30)
        _noii_row(et_ns("2024-03-12", 9, 28, 30), near=100.60, ref=100.0),  # t50 (+60)
    ])
    _write_bars(bars_dir, "NVDA", [
        ("2024-03-08", 90.0, 98.0), ("2024-03-11", 100.0, 99.0), ("2024-03-12", 100.0, 101.0),
    ])
    events, funnel = of.build_events(object(), start=date(2024, 3, 1), end=date(2024, 3, 31),
                                     universe=("NVDA",), noii_dir=noii_dir, bars_dir=bars_dir)
    assert events.height == 2 and bool(events["is_t50"].to_list() == [False, True])

    t25 = of.cell_stats(events, thresh=of.THRESH_T25)
    t50 = of.cell_stats(events, thresh=of.THRESH_T50)
    adia = of.adia_panel(events)
    rho = of.rho_panel(events, None)  # no champion stream -> rho None, still writes
    strata = of.build_strata(events)
    gt = of.ground_truth(events)
    cells = {"t25": t25, "t50": t50, "adia": adia, "rho": rho, "strata": strata}
    atlas = of.build_atlas_md("M24-open-fade", events, funnel, t25, t50, adia, rho, strata, seed=7)

    # redirect the canonical experiments dir (like the gate-locality test).
    monkeypatch.setattr(of, "experiments_dir", lambda: tmp_path / "exp")
    out = of.out_dir_for()
    assert out == tmp_path / "exp" / of.OUT_SUBDIR
    paths = of.write_outputs(out, "M24-open-fade", events, cells, atlas, gt)

    for key in ("atlas", "cells", "events", "ground_truth"):
        assert paths[key].exists(), key
    # ground_truth: <= 10 rows on the documented schema.
    gt_disk = pl.read_parquet(paths["ground_truth"])
    assert gt_disk.height <= 10
    assert gt_disk.columns == [
        "session", "symbol", "basis_open_bps", "side", "open_px", "close_px",
        "gross_bps", "net_bps", "overnight_gap_bps", "is_t50",
    ]
    # atlas.md is pure ASCII (no non-ascii console/file output).
    assert paths["atlas"].read_text(encoding="utf-8").isascii()
    # cells.json parses; t25 / t50 are DISJOINT top-level keys (never pooled).
    parsed = json.loads(paths["cells"].read_text(encoding="utf-8"))
    assert {"t25", "t50", "adia", "rho", "strata"} <= set(parsed)
    assert parsed["t25"]["thresh_bps"] == 25.0 and parsed["t50"]["thresh_bps"] == 50.0
    assert parsed["t50"]["n_fired"] <= parsed["t25"]["n_fired"]  # nested subset
