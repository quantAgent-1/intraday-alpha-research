"""Tests for data/bbo1s.py and auction_replay.tape_from_bbo — 1-second BBO parse,
a FULLY MOCKED Databento download (no network), the SessionTape adapter shapes,
and a market_fill round-trip with a hand-computed entry price. Synthetic frames
only; every expected value is derived from literals.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest
from structlog.testing import capture_logs

from enginev51.backtest import fills as fk
from enginev51.backtest.auction_replay import tape_from_bbo
from enginev51.config import Settings
from enginev51.data import bbo1s
from enginev51.data.bbo1s import (
    BBO_SCHEMA,
    download_bbo1s,
    load_bbo_session,
    normalize_bbo_df,
    partition_path,
)
from enginev51.data.noii import et_ns

SESSION = "2025-06-02"
SLIP = 0.5
TOL = 1e-9


# --------------------------------------------------------------------------- frames


def _bbo_frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=BBO_SCHEMA, orient="row")


def _row(ts, bid, ask, bid_size=100.0, ask_size=100.0) -> dict:
    return {"ts": ts, "bid": bid, "ask": ask, "bid_size": bid_size, "ask_size": ask_size}


# --------------------------------------------------------------------------- normalize


def test_normalize_maps_databento_bbo_columns() -> None:
    # databento-shaped bbo-1s to_df frame (pretty px/ts already applied).
    raw = pl.DataFrame(
        {
            "ts_recv": [222, 111],  # deliberately unsorted -> normalize sorts
            "ts_event": [220, 110],
            "bid_px_00": [99.0, 98.0],
            "ask_px_00": [100.0, 99.0],
            "bid_sz_00": [300.0, 100.0],
            "ask_sz_00": [400.0, 200.0],
            "side": ["N", "N"],  # BBOMsg trade field, ignored
            "price": [0.0, 0.0],  # ignored
        }
    )
    out = normalize_bbo_df(raw)
    assert list(out.columns) == list(BBO_SCHEMA)
    # ts is ts_recv, sorted ascending
    assert out["ts"].to_list() == [111, 222]
    assert out["bid"].to_list() == [98.0, 99.0]
    assert out["ask"].to_list() == [99.0, 100.0]
    assert out["bid_size"].to_list() == [100.0, 300.0]
    assert out["ask_size"].to_list() == [200.0, 400.0]


def test_normalize_falls_back_to_ts_event() -> None:
    raw = pl.DataFrame(
        {"ts_event": [5], "bid_px_00": [1.0], "ask_px_00": [2.0],
         "bid_sz_00": [1.0], "ask_sz_00": [1.0]}
    )
    out = normalize_bbo_df(raw)
    assert out["ts"].to_list() == [5]


# --------------------------------------------------------------------------- loader


def test_load_bbo_session_windows_filters_and_sorts(tmp_path) -> None:
    root = tmp_path / "bbo1s"
    frame = _bbo_frame(
        [
            _row(et_ns(SESSION, 15, 50, 5), 99.0, 100.0),  # in session
            _row(et_ns(SESSION, 9, 30, 0), 98.0, 99.0),  # earlier same session
            _row(et_ns(SESSION, 15, 50, 6), 100.0, 99.5),  # crossed -> filtered out
            _row(et_ns(SESSION, 15, 50, 7), 0.0, 5.0),  # bid<=0 -> filtered out
            _row(et_ns("2025-06-03", 10, 0, 0), 50.0, 51.0),  # next day -> excluded
        ]
    )
    p = partition_path(root, "NVDA", "2025-06")
    p.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(p)

    got = load_bbo_session("NVDA", SESSION, out_dir=root)
    assert got is not None
    # only the two valid in-session rows, ts-sorted
    assert got["ts"].to_list() == [et_ns(SESSION, 9, 30, 0), et_ns(SESSION, 15, 50, 5)]
    assert got["bid"].to_list() == [98.0, 99.0]


def test_load_bbo_session_none_when_absent(tmp_path) -> None:
    # absent partition -> None (distinct from an empty in-session frame)
    assert load_bbo_session("TSLA", SESSION, out_dir=tmp_path / "bbo1s") is None


def test_load_bbo_session_none_when_all_filtered(tmp_path) -> None:
    root = tmp_path / "bbo1s"
    frame = _bbo_frame([_row(et_ns(SESSION, 15, 50, 5), 100.0, 99.0)])  # crossed
    p = partition_path(root, "NVDA", "2025-06")
    p.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(p)
    assert load_bbo_session("NVDA", SESSION, out_dir=root) is None


# --------------------------------------------------------------------------- tape_from_bbo


def test_tape_from_bbo_shapes_and_empty_trades() -> None:
    frame = _bbo_frame(
        [
            _row(et_ns(SESSION, 15, 50, 5), 99.0, 100.0),
            _row(et_ns(SESSION, 15, 50, 6), 99.1, 100.1),
        ]
    )
    tape = tape_from_bbo("NVDA", frame)
    assert tape.symbol == "NVDA"
    assert tape.q_ts.dtype == np.int64
    assert tape.q_bid.dtype == np.float64
    assert tape.q_ts.tolist() == [et_ns(SESSION, 15, 50, 5), et_ns(SESSION, 15, 50, 6)]
    assert tape.q_bid.tolist() == [99.0, 99.1]
    assert tape.q_ask.tolist() == [100.0, 100.1]
    # trades intentionally EMPTY; t_size None (quote-only tape)
    assert tape.t_ts.size == 0
    assert tape.t_price.size == 0
    assert tape.t_size is None


def test_tape_from_bbo_market_fill_round_trip_hand_computed() -> None:
    # A single prevailing 1s BBO of 99.00 / 100.00 before the exec instant.
    signal_ts = et_ns(SESSION, 15, 50, 10)
    frame = _bbo_frame([_row(et_ns(SESSION, 15, 50, 9), 99.0, 100.0)])
    tape = tape_from_bbo("NVDA", frame)

    exec_ts = signal_ts + 7 * 1_000_000_000  # 7s later; prevailing quote is the 15:50:09 row
    # BUY: lift ask*(1+slip)
    got = fk.market_fill(tape.q_ts, tape.q_bid, tape.q_ask, exec_ts, 1, SLIP)
    assert got is not None
    price, mid = got
    assert price == pytest.approx(100.0 * (1.0 + SLIP * 1e-4), abs=TOL)
    assert mid == pytest.approx(99.5, abs=TOL)
    # SELL: hit bid*(1-slip)
    price_s, _ = fk.market_fill(tape.q_ts, tape.q_bid, tape.q_ask, exec_ts, -1, SLIP)
    assert price_s == pytest.approx(99.0 * (1.0 - SLIP * 1e-4), abs=TOL)


def test_tape_from_bbo_market_fill_none_before_first_quote() -> None:
    # exec before the only quote -> no prevailing quote -> None (no future-wrap)
    frame = _bbo_frame([_row(et_ns(SESSION, 15, 50, 20), 99.0, 100.0)])
    tape = tape_from_bbo("NVDA", frame)
    got = fk.market_fill(tape.q_ts, tape.q_bid, tape.q_ask, et_ns(SESSION, 15, 50, 10), 1, SLIP)
    assert got is None


# --------------------------------------------------------------------------- download (mocked)


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


def _dbn_df() -> pl.DataFrame:
    # ts on 2025-02-15 (the resumability test's END date) — see test_noii._dbn_df.
    return pl.DataFrame(
        {
            "ts_recv": [1_739_577_600_000_000_000, 1_739_577_660_000_000_000],
            "ts_event": [1_739_577_600_000_000_000, 1_739_577_660_000_000_000],
            "bid_px_00": [99.0, 99.5],
            "ask_px_00": [100.0, 100.5],
            "bid_sz_00": [100.0, 200.0],
            "ask_sz_00": [300.0, 400.0],
        }
    )


def test_download_missing_key_raises(tmp_path) -> None:
    settings = Settings(databento_api_key="", data_dir=tmp_path)
    with pytest.raises(RuntimeError, match="DATABENTO_API_KEY"):
        download_bbo1s(settings, ["NVDA"], "2025-01-02", "2025-01-31", out_dir=tmp_path / "bbo1s")


def test_download_cost_guard_aborts(tmp_path) -> None:
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    fake = _FakeHistorical(cost=100.0, df=_dbn_df())
    with pytest.raises(RuntimeError, match="cost quote"):
        download_bbo1s(
            settings, ["NVDA"], "2025-01-02", "2025-01-31",
            out_dir=tmp_path / "bbo1s", max_cost=75.0, client=fake,
        )
    # aborted BEFORE any timeseries request
    assert fake.timeseries.calls == []
    assert len(fake.metadata.calls) == 1


def test_download_writes_resumable_partitions(tmp_path) -> None:
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / "bbo1s"
    fake = _FakeHistorical(cost=5.0, df=_dbn_df())
    summary = download_bbo1s(
        settings, ["NVDA", "TSLA"], "2025-01-02", "2025-02-15",
        out_dir=out_dir, max_cost=75.0, client=fake,
    )
    # 2 symbols x 2 months = 4 requests / partitions
    assert summary["partitions_written"] == 4
    assert summary["quoted_usd"] == 5.0
    assert len(fake.timeseries.calls) == 4
    for sym in ("NVDA", "TSLA"):
        for month in ("2025-01", "2025-02"):
            p = partition_path(out_dir, sym, month)
            assert p.exists()
            back = pl.read_parquet(p)
            assert list(back.columns) == list(BBO_SCHEMA)
            assert back["bid"].to_list() == [99.0, 99.5]
            assert back["ask"].to_list() == [100.0, 100.5]

    # rerun: everything present -> skipped, no new network calls
    fake2 = _FakeHistorical(cost=5.0, df=_dbn_df())
    summary2 = download_bbo1s(
        settings, ["NVDA", "TSLA"], "2025-01-02", "2025-02-15",
        out_dir=out_dir, max_cost=75.0, client=fake2,
    )
    assert summary2["partitions_written"] == 0
    assert summary2["partitions_skipped"] == 4
    assert fake2.timeseries.calls == []


def test_download_cost_endpoint_receives_full_range(tmp_path) -> None:
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    fake = _FakeHistorical(cost=1.0, df=_dbn_df())
    download_bbo1s(
        settings, ["NVDA"], "2025-01-02", "2025-01-31",
        out_dir=tmp_path / "bbo1s", client=fake,
    )
    call = fake.metadata.calls[0]
    assert call["dataset"] == bbo1s.DATASET
    assert call["schema"] == bbo1s.SCHEMA
    assert call["symbols"] == ["NVDA"]
    # end is exclusive -> one day past the inclusive end
    assert call["end"] == "2025-02-01"


# ------------------------------------- condition-probe escape hatch (2026-08-01 FIX 2)
#
# Mirror of tests/test_noii.py's block — the two downloaders must behave identically.
# The end-day probe is FAIL-CLOSED by default (B6); `require_condition_probe=False`
# (CLI `--skip-condition-probe`) is the operator escape hatch for a DOWN condition
# endpoint. It applies ONLY to a probe that RAISES, never to a degraded/pending verdict.


class _ProbeMeta:
    """``metadata``-shaped fake. ``condition=None`` makes the probe RAISE."""

    def __init__(self, condition: str | None) -> None:
        self._condition = condition
        self.condition_calls: list[dict] = []

    def get_cost(self, **kw):  # noqa: ANN003
        return 1.0

    def get_dataset_condition(self, **kw):  # noqa: ANN003
        self.condition_calls.append(kw)
        if self._condition is None:
            raise RuntimeError("metadata endpoint down")
        day = kw.get("end_date") or kw.get("start_date")
        return [{"date": str(day), "condition": self._condition}]


class _ProbeClient:
    def __init__(self, condition: str | None) -> None:
        self.metadata = _ProbeMeta(condition)
        self.timeseries = _FakeTimeseries(_dbn_df())


def _probe_download(tmp_path, condition: str | None, **kw) -> tuple[dict, object, list]:
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    client = _ProbeClient(condition)
    with capture_logs() as logs:
        summary = download_bbo1s(
            settings, ["NVDA"], "2025-01-02", "2025-01-31",
            out_dir=tmp_path / "bbo1s", client=client, **kw,
        )
    return summary, client, logs


def test_probe_failure_fails_closed_by_default(tmp_path) -> None:
    """Default (no kwarg) is unchanged: a raising probe skips the end month."""
    summary, client, logs = _probe_download(tmp_path, None)
    assert summary["partitions_written"] == 0
    assert summary["partitions_skipped"] == 1
    assert client.timeseries.calls == []
    assert not partition_path(tmp_path / "bbo1s", "NVDA", "2025-01").exists()
    failed = [e for e in logs if e.get("event") == "bbo1s_condition_probe_failed"]
    assert len(failed) == 1
    assert failed[0]["log_level"] == "warning"
    assert "--skip-condition-probe" in failed[0]["detail"]
    assert [e for e in logs if e.get("event") == "bbo1s_condition_probe_override"] == []


def test_probe_failure_override_proceeds_and_writes(tmp_path) -> None:
    """require_condition_probe=False: the raising probe no longer blocks the fetch."""
    summary, client, logs = _probe_download(tmp_path, None, require_condition_probe=False)
    assert summary["partitions_written"] == 1
    assert len(client.timeseries.calls) == 1
    assert partition_path(tmp_path / "bbo1s", "NVDA", "2025-01").exists()
    over = [e for e in logs if e.get("event") == "bbo1s_condition_probe_override"]
    assert len(over) == 1
    assert over[0]["log_level"] == "warning"
    assert "operator override" in over[0]["detail"]
    assert "metadata endpoint down" in over[0]["detail"]  # names the underlying error
    assert [e for e in logs if e.get("event") == "bbo1s_condition_probe_failed"] == []


def test_degraded_verdict_is_not_overridable(tmp_path) -> None:
    """A probe that SUCCEEDS and reports degraded still skips, override or not —
    and its log line is the vendor-verdict one, never the probe-failure one."""
    summary, client, logs = _probe_download(
        tmp_path, "degraded", require_condition_probe=False
    )
    assert summary["partitions_written"] == 0
    assert client.timeseries.calls == []
    verdict = [e for e in logs if e.get("event") == "bbo1s_day_not_available"]
    assert len(verdict) == 1
    assert verdict[0]["condition"] == "degraded"
    assert "degraded/pending" in verdict[0]["detail"]
    assert [e for e in logs if e.get("event").startswith("bbo1s_condition_probe")] == []


def test_probe_failure_and_vendor_verdict_log_different_events(tmp_path) -> None:
    """The two failure modes the reviewer asked to be told apart, side by side."""
    _, _, raised = _probe_download(tmp_path / "a", None)
    _, _, verdict = _probe_download(tmp_path / "b", "pending")
    raised_events = {e["event"] for e in raised if e.get("log_level") == "warning"}
    verdict_events = {e["event"] for e in verdict if e.get("log_level") == "warning"}
    assert raised_events == {"bbo1s_condition_probe_failed"}
    assert verdict_events == {"bbo1s_day_not_available"}
    assert raised_events.isdisjoint(verdict_events)
