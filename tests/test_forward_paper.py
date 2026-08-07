"""Tests for apps/forward_paper.py — the M10 forward-paper harness.

No live session and no real databento: the ledger append/dedup, status stats, the
holdout-not-applicable guard, and the meta scoring are exercised on fabricated
frames + a tiny in-process LightGBM model; the databento pull is exercised against
a mock Historical client (same fake shape the data-layer tests use). Nothing here
touches the network or the sealed backtest window.
"""

from __future__ import annotations

import textwrap
from datetime import date

import numpy as np
import polars as pl
import pytest

from enginev51.apps import forward_paper as fp
from enginev51.config import Settings
from enginev51.models import moc_meta

UNIVERSE = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")


def _oh(sym: str) -> dict:
    return {f"oh_{s}": (1.0 if s == sym else 0.0) for s in UNIVERSE}


# --------------------------------------------------------------------------- holdout-not-applicable


def test_forward_only_guard_rejects_pre_golive():
    # forward is post-holdout BY CONSTRUCTION: anything before the go-live is refused.
    # It RAISES (SealViolation), never a bare assert: `python -O` strips asserts, and a
    # go-live boundary an env var can switch off is not a boundary (review 2026-08-01).
    from enginev51.protocol import SealViolation

    fp.assert_forward_only(date(2026, 7, 17))  # ok (the go-live)
    fp.assert_forward_only(date(2026, 8, 1))   # ok (later)
    with pytest.raises(SealViolation):
        fp.assert_forward_only(date(2026, 7, 16))  # day before go-live
    with pytest.raises(SealViolation):
        fp.assert_forward_only(date(2026, 5, 31))  # inside the sealed backtest window


def test_forward_only_guard_is_not_a_bare_assert():
    """Source-level pin: the guard must not regress to `assert asof >= FORWARD_START`,
    which PYTHONOPTIMIZE deletes."""
    import ast
    import inspect

    src = inspect.getsource(fp.assert_forward_only)
    tree = ast.parse(textwrap.dedent(src))
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]


# --------------------------------------------------------------------------- ledger schema / rows


def _scored(session: str, symbol: str, *, basis, net, p_win) -> dict:
    r = {
        "session": session, "symbol": symbol, "side": 1 if basis >= 0 else -1,
        "basis_bps": basis, "net_bps": net, "p_win": p_win,
        "entry_px": 100.0, "exit_px": 100.5, "cross_px": 100.5,
        "taken_classical": abs(basis) >= 10.0,
        "taken_meta": abs(basis) >= 10.0 and p_win >= fp.META_GATE_Q,
    }
    r.update(_oh(symbol))
    return r


def test_ledger_rows_projection():
    scored = pl.DataFrame(
        [_scored("2026-07-17", "NVDA", basis=50.0, net=6.0, p_win=0.6)], orient="row"
    )
    rows = fp.ledger_rows(scored, date(2026, 7, 17))
    assert list(rows.columns) == list(fp.LEDGER_SCHEMA)
    assert rows["asof"][0] == "2026-07-17"
    assert rows["taken_classical"][0] is True
    assert rows["taken_meta"][0] is True


# --------------------------------------------------------------------------- append / dedup idempotency


def _ledger_frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=fp.LEDGER_SCHEMA, orient="row")


def _lrow(session, symbol, *, basis=50.0, p_win=0.6, net=3.0, tc=True, tm=True, asof=None):
    return {
        "session": session, "symbol": symbol, "basis_bps": basis, "p_win": p_win,
        "side": 1, "entry_px": 100.0, "exit_px": 100.3, "cross_px": 100.3,
        "net_bps": net, "taken_classical": tc, "taken_meta": tm,
        # M15 shadow columns (values irrelevant to the M10 stream tests here)
        "selected": False, "sel_rank": None, "size_shares": 0,
        "size_notional": 0.0, "implementable": None, "implementable_deploy": None,
        "asof": asof or session,
    }


def test_append_ledger_dedup_idempotent(tmp_path):
    path = tmp_path / "ledger.parquet"
    day1 = _ledger_frame([
        _lrow("2026-07-17", "NVDA"),
        _lrow("2026-07-17", "TSLA"),
    ])
    r1 = fp.append_ledger(day1, path)
    assert r1 == {"appended": 2, "skipped": 0, "total": 2}

    # re-running the SAME day appends nothing (dedup by (session, symbol))
    r2 = fp.append_ledger(day1, path)
    assert r2 == {"appended": 0, "skipped": 2, "total": 2}
    assert fp.load_ledger(path).height == 2

    # a partial overlap: one new symbol same day + a fresh day
    mixed = _ledger_frame([
        _lrow("2026-07-17", "NVDA"),   # dup
        _lrow("2026-07-17", "AMD"),    # new (same day, new symbol)
        _lrow("2026-07-20", "NVDA"),   # new day
    ])
    r3 = fp.append_ledger(mixed, path)
    assert r3 == {"appended": 2, "skipped": 1, "total": 4}

    led = fp.load_ledger(path)
    keys = set(zip(led["session"].to_list(), led["symbol"].to_list(), strict=True))
    assert keys == {
        ("2026-07-17", "NVDA"), ("2026-07-17", "TSLA"),
        ("2026-07-17", "AMD"), ("2026-07-20", "NVDA"),
    }
    # append-only: the ORIGINAL rows are never rewritten (net_bps preserved)
    assert led.filter(
        (pl.col("session") == "2026-07-17") & (pl.col("symbol") == "NVDA")
    )["net_bps"][0] == 3.0


def test_append_empty_is_noop(tmp_path):
    path = tmp_path / "ledger.parquet"
    fp.append_ledger(_ledger_frame([_lrow("2026-07-17", "NVDA")]), path)
    r = fp.append_ledger(pl.DataFrame(schema=fp.LEDGER_SCHEMA), path)
    assert r == {"appended": 0, "skipped": 0, "total": 1}


def test_append_ledger_write_is_atomic(tmp_path, monkeypatch):
    """S6: a crash mid-write must not eat the forward validation clock.

    The ledger is APPEND-ONLY but is rewritten whole on every append, so the old
    in-place ``write_parquet(path)`` put every already-collected forward session
    at risk of a single interrupted write — and forward sessions cannot be
    re-derived, they are collected once as they settle. The write now goes to a
    ``.tmp`` sibling + ``os.replace`` (same idiom as ``live/engine._write_atomic``).
    """
    from pathlib import Path

    path = tmp_path / "ledger.parquet"
    fp.append_ledger(
        _ledger_frame([_lrow("2026-07-17", "NVDA"), _lrow("2026-07-17", "TSLA")]), path
    )
    before = pl.read_parquet(path)

    def _crash_mid_write(self, target, *a, **k):  # noqa: ANN001, ANN002, ANN003
        Path(target).write_bytes(b"PAR1-truncated")  # partial file on disk
        raise OSError("simulated crash during write")

    monkeypatch.setattr(pl.DataFrame, "write_parquet", _crash_mid_write)
    with pytest.raises(OSError):
        fp.append_ledger(_ledger_frame([_lrow("2026-07-20", "AMD")]), path)
    monkeypatch.undo()

    # the ledger itself is untouched: the wreckage landed on the tmp sibling
    assert pl.read_parquet(path).equals(before)
    assert fp.load_ledger(path).height == 2

    # and a subsequent good append still lands, clearing the stale tmp
    r = fp.append_ledger(_ledger_frame([_lrow("2026-07-20", "AMD")]), path)
    assert r["appended"] == 1
    assert not (tmp_path / "ledger.parquet.tmp").exists()


# --------------------------------------------------------------------------- status stats


def _fabricate_ledger(
    n_sessions: int, per_session: int, *, classical_net: float, meta_net: float,
    meta_every: int = 2,
) -> pl.DataFrame:
    rows: list[dict] = []
    for i in range(n_sessions):
        sess = date(2026, 7, 17)
        sess = (sess.replace(day=1) if False else sess)
        # spread sessions out deterministically
        from datetime import timedelta
        sday = (date(2026, 7, 17) + timedelta(days=i)).isoformat()
        for j in range(per_session):
            sym = UNIVERSE[j % len(UNIVERSE)]
            is_meta = (j % meta_every == 0)
            net = meta_net if is_meta else classical_net
            rows.append(_lrow(sday, sym, net=net, tc=True, tm=is_meta))
    return _ledger_frame(rows)


def test_status_stats_fabricated_in_progress():
    # 10 sessions x 4 events = 40 classical events, 2 meta each -> below the gate floors
    led = _fabricate_ledger(10, 4, classical_net=2.0, meta_net=5.0)
    st = fp.status_stats(led)
    assert st["n_sessions"] == 10
    assert st["n_events"] == 40  # classical
    assert st["classical"]["n_events"] == 40
    assert st["meta"]["n_events"] == 20
    # classical mean: half events 5.0 (meta) + half 2.0 -> (5+2)/2 = 3.5; meta = 5.0
    assert st["classical"]["mean_net_bps"] == pytest.approx(3.5, abs=1e-6)
    assert st["meta"]["mean_net_bps"] == pytest.approx(5.0, abs=1e-6)
    # gate not met: too few sessions/events
    assert st["gate"]["sessions_ge_40"] is False
    assert st["gate"]["events_ge_150"] is False
    assert st["gate"]["forward_gate_met"] is False
    assert st["sessions_needed"] == 30
    assert st["events_needed"] == 110
    # format smoke
    assert "forward-paper status" in fp.format_status(st)


def test_status_gate_met_path():
    # 45 sessions x 4 events = 180 classical events (>=150), 45 sessions (>=40).
    # 2 meta events @ 4.0 + 2 non-meta @ 1.0 per session -> classical session mean
    # = (2*4 + 2*1)/4 = 2.5 == REF_CLASSICAL, meta session mean = 4.0 == REF_META.
    # Constant per-session means -> the day-clustered CI is degenerate at the mean,
    # which contains the backtest reference exactly (consistent = True).
    led = _fabricate_ledger(45, 4, classical_net=1.0, meta_net=fp.REF_META_BPS,
                            meta_every=2)
    st = fp.status_stats(led)
    assert st["n_sessions"] == 45
    assert st["n_events"] == 180
    assert st["gate"]["sessions_ge_40"] is True
    assert st["gate"]["events_ge_150"] is True
    assert st["gate"]["classical_mean_gt_0"] is True
    assert st["gate"]["meta_mean_gt_0"] is True
    # constant net at the reference -> degenerate CI [ref, ref] contains the ref
    assert st["classical"]["consistent_with_backtest"] is True
    assert st["meta"]["consistent_with_backtest"] is True
    assert st["gate"]["forward_gate_met"] is True


def test_status_empty_ledger():
    st = fp.status_stats(pl.DataFrame(schema=fp.LEDGER_SCHEMA))
    assert st["n_sessions"] == 0
    assert st["n_events"] == 0
    assert st["classical"]["mean_net_bps"] is None
    assert st["gate"]["forward_gate_met"] is False
    # format must not crash on an empty ledger
    assert "no events yet" in fp.format_status(st)


# --------------------------------------------------------------------------- meta scoring (real tiny model)


def _meta_events(n_days: int = 60, seed: int = 4) -> pl.DataFrame:
    """A small labeled event frame carrying every registered meta feature."""
    from datetime import timedelta
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    d0 = date(2023, 1, 3)
    for i in range(n_days):
        sess = (d0 + timedelta(days=i)).isoformat()
        for sym in ("NVDA", "TSLA", "AMD"):
            basis = float(rng.choice([-1, 1]) * rng.uniform(12, 200))
            net = float(rng.normal(2, 30))
            r = {
                "session": sess, "symbol": sym, "side": 1 if basis >= 0 else -1,
                "basis_bps": basis, "net_bps": net,
                "near_far_bps": float(rng.normal(0, 5)),
                "near_ref_bps": float(rng.normal(0, 5)),
                "paired_ratio": float(rng.uniform(0.5, 0.9)),
                "norm_imb": float(rng.normal(0, 0.01)),
                "imb_growth_53": float(rng.normal(0, 0.001)),
                "imb_growth_51": float(rng.normal(0, 0.001)),
                "msg_count": 40.0, "vol20": float(rng.uniform(0.01, 0.05)),
                "log_adv20": float(rng.uniform(20, 24)),
                "entry_px": 100.0, "exit_px": 100.2, "cross_px": 100.2,
            }
            r.update(_oh(sym))
            rows.append(r)
    return pl.DataFrame(rows, orient="row")


def test_score_events_flags_and_pwin():
    events = _meta_events()
    meta = moc_meta.build_meta_frame(events)  # |basis|>=10 candidates + y_meta
    booster = moc_meta.train_fold(meta)

    # score the full event universe (include a sub-threshold event to check the flag)
    small = events.head(3).with_columns(pl.lit(5.0).alias("basis_bps"))  # |basis|<10
    scored = fp.score_events(pl.concat([events, small]), booster)

    assert "p_win" in scored.columns
    pw = scored["p_win"].to_numpy()
    assert np.all((pw >= 0.0) & (pw <= 1.0))
    # taken_classical is exactly |basis|>=10
    tc = scored["taken_classical"].to_numpy()
    assert np.array_equal(tc, (np.abs(scored["basis_bps"].to_numpy()) >= 10.0))
    # taken_meta implies taken_classical AND p_win>=gate
    tm = scored.filter(pl.col("taken_meta"))
    assert (tm["basis_bps"].abs() >= 10.0).all()
    assert (tm["p_win"] >= fp.META_GATE_Q).all()


def test_score_events_empty():
    empty = pl.DataFrame(schema={c: pl.Float64 for c in moc_meta.FEATURE_COLS}
                         | {"session": pl.Utf8, "symbol": pl.Utf8, "net_bps": pl.Float64,
                            "basis_bps": pl.Float64})

    class _NoBooster:
        pass

    out = fp.score_events(empty, _NoBooster())  # booster unused on empty
    assert out.height == 0
    assert "p_win" in out.columns


# --------------------------------------------------------------------------- databento mock (download)


class _FakeData:
    def __init__(self, df: pl.DataFrame) -> None:
        self._df = df

    def to_df(self, **kw):  # noqa: ANN003
        return self._df


class _FakeTimeseries:
    def __init__(self, df: pl.DataFrame) -> None:
        self._df = df
        self.calls: list[dict] = []

    def get_range(self, **kw):  # noqa: ANN003
        self.calls.append(kw)
        return _FakeData(self._df)


class _FakeMeta:
    def __init__(self, cost: float) -> None:
        self._cost = cost
        self.calls: list[dict] = []
        self.condition_calls: list[dict] = []

    def get_cost(self, **kw):  # noqa: ANN003
        self.calls.append(kw)
        return self._cost

    def get_dataset_condition(self, **kw):  # noqa: ANN003
        # The end-day freshness probe is now FAIL-CLOSED (B6), so the fake must
        # model the real client's endpoint or every end month would be skipped.
        self.condition_calls.append(kw)
        day = kw.get("end_date") or kw.get("start_date")
        return [{"date": str(day), "condition": "available"}]


class _FakeHistorical:
    def __init__(self, cost: float, df: pl.DataFrame) -> None:
        self.metadata = _FakeMeta(cost)
        self.timeseries = _FakeTimeseries(df)


# Timestamps must reach the session's CLOSE WINDOW on the requested date: the
# downloaders' end-month coverage check (B6) re-fetches a partition whose max ts
# stops short of `session_close - margin`, not merely one whose max ts predates
# end_d. 2026-07-17 19:59:00 / 19:59:30 UTC = 15:59:00 / 15:59:30 ET, inside the
# close-5min floor both downloaders use (bbo-1s widened 60s -> 300s, FIX 6).
_TS_ON_DAY = [1_784_318_340_000_000_000, 1_784_318_370_000_000_000]


def _noii_dbn() -> pl.DataFrame:
    return pl.DataFrame({
        "ts_event": _TS_ON_DAY, "side": ["B", "A"],
        "total_imbalance_qty": [10.0, 20.0], "paired_qty": [1.0, 2.0],
        "cont_book_clr_price": [100.0, 101.0], "auct_interest_clr_price": [99.0, 100.0],
        "ref_price": [100.1, 101.1],
    })


def _bbo_dbn() -> pl.DataFrame:
    return pl.DataFrame({
        "ts_recv": _TS_ON_DAY, "bid_px_00": [99.0, 99.5], "ask_px_00": [100.0, 100.5],
        "bid_sz_00": [100.0, 100.0], "ask_sz_00": [100.0, 100.0],
    })


def test_download_session_mock_and_noop(tmp_path):
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    noii_dir = tmp_path / "noii"
    bbo_dir = tmp_path / "bbo1s"
    fake_noii = _FakeHistorical(cost=0.5, df=_noii_dbn())
    fake_bbo = _FakeHistorical(cost=0.5, df=_bbo_dbn())

    # First call downloads one month x 5 symbols for each schema.
    # (download_session shares one client; use a single fake carrying a NOII-shaped
    # frame is not enough for bbo parse, so drive the two schemas separately.)
    from enginev51.data.bbo1s import download_bbo1s
    from enginev51.data.noii import download_noii

    n1 = download_noii(settings, list(UNIVERSE), "2026-07-17", "2026-07-17",
                       out_dir=noii_dir, max_cost=5.0, client=fake_noii)
    b1 = download_bbo1s(settings, list(UNIVERSE), "2026-07-17", "2026-07-17",
                        out_dir=bbo_dir, max_cost=5.0, client=fake_bbo)
    assert n1["partitions_written"] == 5  # 5 symbols x 1 month
    assert b1["partitions_written"] == 5

    # Re-run: everything present -> skipped, NO new network calls (idempotent no-op).
    fake_noii2 = _FakeHistorical(cost=0.5, df=_noii_dbn())
    fake_bbo2 = _FakeHistorical(cost=0.5, df=_bbo_dbn())
    n2 = download_noii(settings, list(UNIVERSE), "2026-07-17", "2026-07-17",
                       out_dir=noii_dir, max_cost=5.0, client=fake_noii2)
    b2 = download_bbo1s(settings, list(UNIVERSE), "2026-07-17", "2026-07-17",
                        out_dir=bbo_dir, max_cost=5.0, client=fake_bbo2)
    assert n2["partitions_written"] == 0 and n2["partitions_skipped"] == 5
    assert b2["partitions_written"] == 0 and b2["partitions_skipped"] == 5
    assert fake_noii2.timeseries.calls == []
    assert fake_bbo2.timeseries.calls == []


def test_download_session_cost_guard(tmp_path):
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    fake = _FakeHistorical(cost=999.0, df=_noii_dbn())
    with pytest.raises(RuntimeError, match="cost quote"):
        fp.download_session(settings, date(2026, 7, 17),
                            noii_dir=tmp_path / "noii", bbo_dir=tmp_path / "bbo1s",
                            client=fake)
    assert fake.timeseries.calls == []  # aborted before any bytes


# --------------------------------------------------------------------------- bars1d raw-adjustment contract


def test_extend_bars1d_pins_raw_adjustment(tmp_path, monkeypatch):
    """_extend_bars1d MUST fetch with adjustment='raw' (SIM_AUDIT_2026-07-21 F1).

    bars1d is a raw-adjustment lake (run_m11.py:257, run_xs_reversal.py:172). The
    AlpacaHist default is adjustment='all', which on an ex-dividend fetch day back-
    adjusts the appended prior-session official close and creates a mixed-vintage
    lake. This pins the fetch contract (adjustment + timeframe) with a stub client,
    so it never touches the network or the real lake.
    """
    captured: list[dict] = []

    class _CapturingHist:
        def __init__(self, settings):  # noqa: ANN001
            self.settings = settings

        def fetch_bars_multi(self, symbols, start, end, **kwargs):  # noqa: ANN001, ANN003
            captured.append(
                {"symbols": list(symbols), "start": start, "end": end, **kwargs}
            )
            return {}  # no rows -> _extend_bars1d is a clean no-op (no lake writes)

        def close(self):
            pass

    import enginev51.data.alpaca_hist as ah

    monkeypatch.setattr(ah, "AlpacaHist", _CapturingHist)

    n = fp._extend_bars1d(
        Settings(), ["NVDA", "TSLA"], date(2026, 7, 20), bars_dir=tmp_path
    )

    assert n == 0  # empty fetch -> nothing appended
    assert len(captured) == 1
    call = captured[0]
    assert call["adjustment"] == "raw"   # the fix: raw, NOT the client 'all' default
    assert call["timeframe"] == "1Day"
    assert call["symbols"] == ["NVDA", "TSLA"]


# ------------------------------------------ condition-probe escape hatch CLI plumbing


def test_skip_condition_probe_flag_is_store_false():
    """`--skip-condition-probe` is the operator escape hatch's only CLI surface
    (neither data/noii.py nor data/bbo1s.py has a CLI of its own; forward_paper's
    `run` is the command that drives both downloaders). Default = fail-closed."""
    from click.testing import CliRunner

    opt = next(p for p in fp.run_cmd.params if p.name == "require_condition_probe")
    assert "--skip-condition-probe" in opt.opts
    assert opt.default is True and opt.flag_value is False  # argparse store_false

    seen: list[dict] = []

    def _fake_run_asof(settings, asof, **kw):  # noqa: ANN001, ANN003
        seen.append(kw)
        return {"asof": asof.isoformat()}

    runner = CliRunner()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(fp, "run_asof", _fake_run_asof)
        mp.setattr(fp, "load_ledger", lambda *a, **k: pl.DataFrame())
        mp.setattr(fp, "status_stats", lambda *a, **k: {})
        mp.setattr(fp, "format_status", lambda *a, **k: "")
        r1 = runner.invoke(fp.run_cmd, ["--asof", "2026-07-17", "--no-download"])
        r2 = runner.invoke(
            fp.run_cmd,
            ["--asof", "2026-07-17", "--no-download", "--skip-condition-probe"],
        )
    assert r1.exit_code == 0 and r2.exit_code == 0, (r1.output, r2.output)
    assert seen[0]["require_condition_probe"] is True    # default: fail-closed
    assert seen[1]["require_condition_probe"] is False   # operator override


def test_download_session_forwards_the_probe_flag(monkeypatch, tmp_path):
    """The flag must reach BOTH downloaders, not just the first one."""
    calls: list[tuple[str, bool]] = []

    def _fake_noii(*a, **kw):  # noqa: ANN002, ANN003
        calls.append(("noii", kw["require_condition_probe"]))
        return {}

    def _fake_bbo(*a, **kw):  # noqa: ANN002, ANN003
        calls.append(("bbo1s", kw["require_condition_probe"]))
        return {}

    import enginev51.data.bbo1s as bbo_mod
    import enginev51.data.noii as noii_mod

    monkeypatch.setattr(noii_mod, "download_noii", _fake_noii)
    monkeypatch.setattr(bbo_mod, "download_bbo1s", _fake_bbo)

    fp.download_session(
        Settings(data_dir=tmp_path), date(2026, 7, 17),
        require_condition_probe=False, client=object(),
    )
    assert calls == [("noii", False), ("bbo1s", False)]
