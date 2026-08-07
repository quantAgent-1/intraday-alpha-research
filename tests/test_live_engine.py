"""Tests for the live signal engine (L0/L1) -- ``enginev51.live`` + the CLI app.

Synthetic and hermetic ONLY: every test writes to a ``tmp_path`` journal and, where the
forward-clock kernels are exercised, monkeypatches the engine's bound
``compute_session_events`` / ``score_events`` / ``load_model`` / ``decide_one`` so no
real lake, no real journal/ledger, and no network is ever touched. The 12 tests mirror
``research/LIVE_SIGNAL_ENGINE_L0L1_DESIGN.md`` section 3.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from enginev51.apps import forward_paper as fp
from enginev51.apps import live_cockpit as lc
from enginev51.live import engine as eng
from enginev51.live import reconcile as rec
from enginev51.models import moc_meta
from enginev51.research_screens import sizing_shadow as ss

UNIVERSE = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")
NORMAL_SESSION = "2026-07-20"  # a Monday, not a NYSE half-day
HALF_DAY = "2024-11-29"        # in EARLY_CLOSE_DATES (day after Thanksgiving)


# --------------------------------------------------------------------------- helpers


def _feature_row(session: str, symbol: str, *, basis: float, net: float) -> dict:
    r = {
        "session": session, "symbol": symbol, "side": 1 if basis >= 0 else -1,
        "net_bps": net, "entry_px": 100.0, "entry_bid": 99.9, "entry_ask": 100.1,
        "entry_mid": 100.0, "cross_px": 100.5, "near_price": 100.0 + basis / 100.0,
        "basis_bps": basis, "near_far_bps": 1.0, "near_ref_bps": 1.0, "paired_ratio": 0.5,
        "norm_imb": 0.01, "imb_growth_53": 0.0, "imb_growth_51": 0.0, "msg_count": 40.0,
        "vol20": 0.3, "log_adv20": 22.0,
    }
    r.update({f"oh_{s}": (1.0 if s == symbol else 0.0) for s in UNIVERSE})
    return r


def _emit_row(session: str, symbol: str, window: str = "close") -> dict:
    return {
        "session": session, "symbol": symbol, "window": window,
        "basis_bps": 50.0, "p_win": 0.6, "side": 1,
        "taken_classical": True, "taken_meta": True,
        "tier": 1.5, "vol_norm": 1.0, "size_notional_research": 15000.0,
        "size_shares_deploy": 12, "expected_net_bps": 6.0,
        "order_type": eng.ORDER_TYPE_CLOSE, "limit_px": 100.0,
        "deadline_et": eng.DEADLINE_CLOSE_ET, "spread_abort": False, "note": "",
    }


# ---------------------------------------------------------------- 1. atomic append/dedup


def test_journal_atomic_append_dedup(tmp_path):
    jpath = tmp_path / "signals_journal.parquet"
    rows = [_emit_row(NORMAL_SESSION, "NVDA"), _emit_row(NORMAL_SESSION, "AMD")]
    n1 = eng.emit(rows, source="replay", journal_path=jpath)
    assert n1 == 2
    # re-emitting the same (session, symbol, source, window) keys appends nothing.
    n2 = eng.emit(rows, source="replay", journal_path=jpath)
    assert n2 == 0
    j = eng.load_journal(jpath)
    assert j.height == 2
    # the .tmp sibling never lingers after an atomic replace.
    assert not jpath.with_suffix(jpath.suffix + ".tmp").exists()
    # a manual row for the SAME (session, symbol) is NOT blocked (R1: source in keys).
    n3 = eng.emit([_emit_row(NORMAL_SESSION, "NVDA")], source="manual", journal_path=jpath)
    assert n3 == 1
    assert eng.load_journal(jpath).height == 3


# ---------------------------------------------------------------- 2. schema pin


def test_journal_schema_pin(tmp_path):
    expected_cols = [
        "ts_emit", "session", "symbol", "window", "source", "basis_bps", "p_win", "side",
        "taken_classical", "taken_meta", "tier", "vol_norm", "size_notional_research",
        "size_shares_deploy", "expected_net_bps", "order_type", "limit_px", "deadline_et",
        "spread_abort", "engine_git_sha", "note",
    ]
    assert list(eng.JOURNAL_SCHEMA) == expected_cols
    jpath = tmp_path / "j.parquet"
    eng.emit([_emit_row(NORMAL_SESSION, "NVDA")], source="replay", journal_path=jpath)
    j = eng.load_journal(jpath)
    assert list(j.columns) == expected_cols
    assert j.schema["ts_emit"] == pl.Int64
    assert j.schema["basis_bps"] == pl.Float64
    assert j.schema["taken_meta"] == pl.Boolean
    assert j.schema["size_shares_deploy"] == pl.Int64
    assert j.schema["note"] == pl.Utf8


# ---------------------------------------------------------------- 3. windows: DST + halfday


def test_session_windows_dst_and_halfday():
    # EDT (summer, UTC-4): 09:25 ET -> 13:25 UTC; 15:50 ET -> 19:50 UTC.
    edt = eng.session_windows("2026-07-20")
    assert edt["early_close"] is False and edt["close"] is not None
    from enginev51.data.noii import et_ns
    assert edt["open"]["start_ns"] == et_ns("2026-07-20", 9, 25, 0)
    assert edt["close"]["start_ns"] == et_ns("2026-07-20", 15, 50, 0)
    # EST (winter, UTC-5): the same wall-clock ET maps one hour later in UTC.
    est = eng.session_windows("2026-01-20")
    assert est["close"] is not None
    assert est["open"]["start_ns"] - edt["open"]["start_ns"]  # different absolute instants
    assert (est["open"]["start_ns"] % 86_400_000_000_000) != (
        edt["open"]["start_ns"] % 86_400_000_000_000
    )
    # half-day: close window ABSENT + early_close flag; open unaffected.
    hd = eng.session_windows(HALF_DAY)
    assert hd["early_close"] is True
    assert hd["close"] is None
    assert hd["open"] is not None


# ---------------------------------------------------------------- 4. replay wiring


def test_replay_wiring(tmp_path, monkeypatch):
    asof = date.fromisoformat(NORMAL_SESSION)
    events = pl.DataFrame([
        _feature_row(NORMAL_SESSION, "NVDA", basis=50.0, net=6.0),
        _feature_row(NORMAL_SESSION, "GOOGL", basis=2.0, net=-0.5),
    ])

    def fake_compute(settings, asof_, *, seed=7, noii_dir=None, bbo_dir=None):
        return events

    def fake_score(evs, booster):
        pw = [0.70, 0.40][: evs.height]
        return evs.with_columns(
            pl.Series("p_win", pw),
            (pl.col("basis_bps").abs() >= 10.0).alias("taken_classical"),
        ).with_columns(
            (pl.col("taken_classical") & (pl.col("p_win") >= 0.55)).alias("taken_meta")
        )

    monkeypatch.setattr(eng, "compute_session_events", fake_compute)
    monkeypatch.setattr(eng, "score_events", fake_score)
    monkeypatch.setattr(lc, "load_model", lambda p: (object(), "loaded frozen M8 model"))

    jpath = tmp_path / "j.parquet"
    eng.replay_session(None, asof, journal_path=jpath, bars_dir=tmp_path / "no_bars")
    j = eng.load_journal(jpath)

    assert set(j["source"].unique().to_list()) == {"replay"}
    assert set(j["window"].unique().to_list()) == {"close"}
    nvda = j.filter(pl.col("symbol") == "NVDA").row(0, named=True)
    assert nvda["basis_bps"] == 50.0
    assert nvda["p_win"] == pytest.approx(0.70)
    assert nvda["taken_meta"] is True
    # expected_net_bps carries the replayed realized net (the reconcile column).
    assert nvda["expected_net_bps"] == pytest.approx(6.0)
    # tier from p_win (0.70 -> 1.5); vol_norm null (no bars lake -> vol-history skip).
    assert nvda["tier"] == pytest.approx(ss.tier(0.70))
    assert nvda["vol_norm"] is None
    assert "vol_skip" in nvda["note"]
    assert nvda["order_type"] == eng.ORDER_TYPE_CLOSE
    # git sha stamped consistently for every row.
    assert j["engine_git_sha"].to_list() == [eng._engine_git_sha()] * j.height


def test_replay_degrades_without_model(tmp_path, monkeypatch):
    asof = date.fromisoformat(NORMAL_SESSION)
    events = pl.DataFrame([_feature_row(NORMAL_SESSION, "NVDA", basis=50.0, net=6.0)])
    monkeypatch.setattr(eng, "compute_session_events", lambda s, a, **k: events)
    monkeypatch.setattr(lc, "load_model", lambda p: (None, "model ABSENT"))
    jpath = tmp_path / "j.parquet"
    eng.replay_session(None, asof, journal_path=jpath, bars_dir=tmp_path / "no_bars")
    row = eng.load_journal(jpath).row(0, named=True)
    # R2: classical-only, p_win / taken_meta / tier null, note flags no_model.
    assert row["p_win"] is None and row["taken_meta"] is None and row["tier"] is None
    assert row["taken_classical"] is True
    assert "no_model" in row["note"]


# ---------------------------------------------------------------- 5. manual wiring


def test_manual_wiring(tmp_path, monkeypatch):
    def fake_decide(symbol, near, bid, ask, *, session_iso, booster, **kw):
        return {
            "symbol": symbol.upper(), "basis_bps": 50.0, "direction": 1,
            "classical_go": True, "spread_abort": False, "shares": 11,
            "meta": {"available": True, "p_win": 0.62, "go": True},
        }

    monkeypatch.setattr(eng, "decide_one", fake_decide)
    monkeypatch.setattr(lc, "load_model", lambda p: (None, "model ABSENT"))
    jpath = tmp_path / "j.parquet"
    d = eng.manual_decide(
        "NVDA", 105.0, 99.99, 100.01, session_iso=NORMAL_SESSION,
        journal_path=jpath, model_path=tmp_path / "no_model.txt",
    )
    # returned ticket dict enriched with tier/vol_norm display.
    assert d["tier"] == pytest.approx(ss.tier(0.62))  # 0.62 -> 1.5
    assert d["vol_norm"] is None
    j = eng.load_journal(jpath)
    assert j.height == 1
    row = j.row(0, named=True)
    assert row["source"] == "manual" and row["window"] == "close"
    assert row["taken_classical"] is True and row["taken_meta"] is True
    assert row["side"] == 1 and row["size_shares_deploy"] == 11
    assert row["expected_net_bps"] is None  # no realized outcome at decision time


# ---------------------------------------------------------------- 6. kernel identity


def test_kernel_identity():
    # The engine references the registered kernels BY IDENTITY -- no local reimplementation.
    assert eng.compute_session_events is fp.compute_session_events
    assert eng.score_events is fp.score_events
    assert eng.decide_one is lc.decide_one
    assert eng.predict_pwin is moc_meta.predict_pwin  # transitive M8 scorer
    assert eng.tier is ss.tier
    assert eng.vol_norm is ss.vol_norm
    assert eng.trailing_raw_vol is ss.trailing_raw_vol
    assert eng.psr is ss.psr
    assert eng.min_trl is ss.min_trl
    assert eng.sr_native is ss.sr_native
    assert eng.sample_moments is ss.sample_moments


# ---------------------------------------------------------------- 7. reconcile exact + flags


def _journal_frame(source: str, *, basis: float, p_win: float, exp_net: float | None) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "session": [NORMAL_SESSION], "symbol": ["NVDA"], "source": [source],
            "window": ["close"], "basis_bps": [basis], "p_win": [p_win],
            "expected_net_bps": [exp_net],
        }
    )


def _ledger_frame(*, basis: float, p_win: float, net: float) -> pl.DataFrame:
    return pl.DataFrame(
        {"session": [NORMAL_SESSION], "symbol": ["NVDA"], "basis_bps": [basis],
         "p_win": [p_win], "net_bps": [net]}
    )


def test_reconcile_exact_and_flags():
    ledger = _ledger_frame(basis=50.0, p_win=0.60, net=6.0)
    # identical replay row -> zero flags.
    clean = rec.reconcile(_journal_frame("replay", basis=50.0, p_win=0.60, exp_net=6.0), ledger)
    assert clean.height > 0 and int(clean.filter(pl.col("flagged")).height) == 0
    # manual basis off by 2 bps -> flagged (manual tol 1.0 on basis).
    man = rec.reconcile(_journal_frame("manual", basis=52.0, p_win=0.60, exp_net=None), ledger)
    man_basis = man.filter(pl.col("field") == "basis_bps")
    assert bool(man_basis["flagged"][0]) is True
    # manual p_win identical -> not flagged (within 0.01).
    assert bool(man.filter(pl.col("field") == "p_win")["flagged"][0]) is False
    # replay basis off by 1e-6 -> flagged (replay tol 1e-9).
    rep = rec.reconcile(
        _journal_frame("replay", basis=50.0 + 1e-6, p_win=0.60, exp_net=6.0), ledger
    )
    assert bool(rep.filter(pl.col("field") == "basis_bps")["flagged"][0]) is True
    # the same 1e-6 basis under MANUAL keying tolerance is NOT flagged.
    rep_manual = rec.reconcile(
        _journal_frame("manual", basis=50.0 + 1e-6, p_win=0.60, exp_net=None), ledger
    )
    assert bool(rep_manual.filter(pl.col("field") == "basis_bps")["flagged"][0]) is False


def test_reconcile_one_sided_surfaced():
    # NVDA matches; TSLA is journal-only; AMD is ledger-only -- both must be FLAGGED (M2).
    journal = pl.DataFrame(
        {
            "session": [NORMAL_SESSION, NORMAL_SESSION],
            "symbol": ["NVDA", "TSLA"], "source": ["replay", "replay"],
            "window": ["close", "close"], "basis_bps": [50.0, 12.0],
            "p_win": [0.60, 0.60], "expected_net_bps": [6.0, 1.0],
        }
    )
    ledger = pl.DataFrame(
        {
            "session": [NORMAL_SESSION, NORMAL_SESSION],
            "symbol": ["NVDA", "AMD"], "basis_bps": [50.0, 20.0],
            "p_win": [0.60, 0.60], "net_bps": [6.0, 2.0],
        }
    )
    flags = rec.reconcile(journal, ledger)
    j_only = flags.filter(pl.col("source_side") == "journal_only")
    l_only = flags.filter(pl.col("source_side") == "ledger_only")
    assert j_only.height == 1 and j_only["symbol"][0] == "TSLA"
    assert bool(j_only["flagged"][0]) is True
    assert l_only.height == 1 and l_only["symbol"][0] == "AMD"
    assert bool(l_only["flagged"][0]) is True
    # NVDA matched fields are clean, but the report must NOT say ALL CLEAN.
    report = rec.reconcile_report(flags)
    assert "journal_only=1" in report and "ledger_only=1" in report
    assert "ALL CLEAN" not in report


def test_emit_strict_dtype_raises(tmp_path):
    # m4: a wrong-dtype value (float into the Int64 ``side`` column) must RAISE, not coerce.
    bad = _emit_row(NORMAL_SESSION, "NVDA")
    bad["side"] = 1.7
    with pytest.raises(TypeError, match="side"):
        eng.emit([bad], source="replay", journal_path=tmp_path / "j.parquet")


def test_emit_dedups_within_batch(tmp_path):
    # n6: two same-key rows in ONE emit batch collapse to a single append (keep-first).
    jpath = tmp_path / "j.parquet"
    rows = [_emit_row(NORMAL_SESSION, "NVDA"), _emit_row(NORMAL_SESSION, "NVDA")]
    n = eng.emit(rows, source="replay", journal_path=jpath)
    assert n == 1
    assert eng.load_journal(jpath).height == 1


# ---------------------------------------------------------------- 8. no ledger write path


def _scanned_source_files() -> list[Path]:
    """The live package .py files PLUS the CLI app (M1: a future move breaks loudly)."""
    from enginev51.apps import live_engine as le

    pkg = Path(eng.__file__).parent
    files = sorted(pkg.glob("*.py")) + [Path(le.__file__)]
    # guard: the CLI app must be in the scanned set.
    assert Path(le.__file__) in files
    assert Path(le.__file__).name == "live_engine.py"
    return files


def test_no_ledger_write_path():
    files = _scanned_source_files()
    src = "\n".join(p.read_text(encoding="utf-8") for p in files)
    # neither the live package nor the CLI imports/calls the forward-ledger append API.
    assert "append_ledger" not in src
    # nor any lake/ledger path token.
    assert "ledger.parquet" not in src
    # the SOLE parquet write across the scanned set is the atomic journal writer.
    assert src.count("write_parquet") == 1
    # the sole write target constant is the signals journal.
    assert "signals_journal.parquet" in src


# ---------------------------------------------------------------- 9. monitor panel PSR


def test_monitor_panel_psr():
    nets = [6.0, -1.0, 4.0, 2.5]
    sessions = ["2026-07-17", "2026-07-20", "2026-07-21", "2026-07-22"]
    journal = pl.DataFrame(
        {
            "session": sessions,
            "symbol": ["NVDA"] * 4,
            "taken_classical": [True] * 4,
            "expected_net_bps": nets,
        }
    )
    panel = eng.monitor_panel(journal, ref_sr=0.5)
    x = np.asarray(nets, dtype=float)
    t = x.shape[0]
    g3, g4, rho = ss.sample_moments(x)
    sr = ss.sr_native(x)
    assert panel["T"] == t
    assert panel["sr_native"] == pytest.approx(round(float(sr), 4))
    assert panel["psr_sr0_0"] == pytest.approx(round(ss.psr(sr, 0.0, t, rho, g3, g4), 4))
    assert panel["psr_ref"] == pytest.approx(round(ss.psr(sr, 0.5, t, rho, g3, g4), 4))
    assert panel["min_trl"] == pytest.approx(
        round(ss.min_trl(sr, 0.0, ss.ALPHA, rho, g3, g4), 2)
    )


# ---------------------------------------------------------------- 10. dormancy refusal


def test_dormancy_refusal(tmp_path):
    jpath = tmp_path / "j.parquet"
    bad = _emit_row(NORMAL_SESSION, "NVDA", window="lunch")
    with pytest.raises(ValueError, match="dormant"):
        eng.emit([bad], source="replay", journal_path=jpath)
    # source="feed" refused naming the L2 gate (R6).
    with pytest.raises(ValueError, match="L2"):
        eng.emit([_emit_row(NORMAL_SESSION, "NVDA")], source="feed", journal_path=jpath)
    # unknown source refused too.
    with pytest.raises(ValueError, match="unknown source"):
        eng.emit([_emit_row(NORMAL_SESSION, "NVDA")], source="bogus", journal_path=jpath)


# ---------------------------------------------------------------- 11. no routing imports


def test_no_routing_imports():
    denylist = [
        "requests", "httpx", "websocket", "aiohttp", "alpaca", "ib_insync",
        "ibapi", "databento", "urllib", "import socket",
    ]
    for p in _scanned_source_files():  # live package + the CLI app (M1)
        src = p.read_text(encoding="utf-8")
        for tok in denylist:
            assert tok not in src, f"routing/network token {tok!r} found in {p.name}"


# ---------------------------------------------------------------- 12. half-day close refusal


def test_halfday_close_refusal(tmp_path):
    jpath = tmp_path / "j.parquet"
    # R3: a close-window emit on a listed NYSE half-day is refused with reason early_close.
    with pytest.raises(ValueError, match="early_close"):
        eng.emit([_emit_row(HALF_DAY, "NVDA", window="close")], source="replay", journal_path=jpath)
    # the OPEN window is unaffected on a half-day (the scope-fence slot still exists).
    n = eng.emit([_emit_row(HALF_DAY, "NVDA", window="open")], source="replay", journal_path=jpath)
    assert n == 1


# ---------------------------------------------------------------- CLI (m5, n7)


def test_cli_selftest_and_monitor_exit_zero(monkeypatch):
    from click.testing import CliRunner

    from enginev51.apps import live_engine as le

    runner = CliRunner()
    # selftest uses its own tempdir -- no real path, must exit 0.
    r1 = runner.invoke(le.main, ["selftest"])
    assert r1.exit_code == 0, r1.output
    assert "selftest OK" in r1.output
    # monitor over an empty journal (hermetic: load_journal patched to empty) must exit 0.
    monkeypatch.setattr(eng, "load_journal", lambda *a, **k: pl.DataFrame(schema=eng.JOURNAL_SCHEMA))
    r2 = runner.invoke(le.main, ["monitor"])
    assert r2.exit_code == 0, r2.output


def test_cli_decide_on_halfday_renders_and_warns(tmp_path):
    from click.testing import CliRunner

    from enginev51.apps import live_engine as le

    runner = CliRunner()
    # A half-day close emission is refused; the ticket still renders + a labeled warning,
    # and the command exits 0 (n7). Model absent -> classical-only; no real journal write
    # (emit refuses BEFORE any write, so the real journal path is never touched).
    res = runner.invoke(
        le.main,
        [
            "decide", "--symbol", "NVDA", "--near", "105.0", "--bid", "99.99",
            "--ask", "100.01", "--session", HALF_DAY,
            "--model", str(tmp_path / "no_model.txt"),
        ],
    )
    assert res.exit_code == 0, res.output
    assert "EARLY CLOSE - not journaled" in res.output
    assert "ORDER TICKET" in res.output  # ticket still rendered
