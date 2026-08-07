"""Tests for data/noii.py — NOII parse, PIT signal, and a FULLY MOCKED Databento
download (no network). Synthetic frames only; every expected value is derived
from literals so the tests cannot merely echo the implementation.
"""

from __future__ import annotations

import polars as pl
import pytest
from structlog.testing import capture_logs

from enginev51.config import Settings
from enginev51.data import noii
from enginev51.data.noii import (
    NOII_SCHEMA,
    download_noii,
    et_ns,
    load_noii_session,
    normalize_imbalance_df,
    partition_path,
    signal_at,
)

# --------------------------------------------------------------------------- frames


def _noii_frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=NOII_SCHEMA, orient="row")


def _row(ts, side, imb, near, ref=None, paired=0.0, far=0.0) -> dict:
    return {
        "ts": ts,
        "side": side,
        "imbalance_shares": imb,
        "paired_shares": paired,
        "near_price": near,
        "far_price": far,
        "ref_price": ref if ref is not None else near,
    }


# --------------------------------------------------------------------------- signal_at


def test_signal_formula_hand_check() -> None:
    # +1 buy imbalance, 100_000 shares, near 150.0, ADV$ 3e9.
    # norm = +1 * 100000 * 150 / 3e9 = 15_000_000 / 3e9 = 0.005
    f = _noii_frame([_row(et_ns("2025-06-02", 15, 50, 5), "B", 100_000.0, 150.0)])
    sig = signal_at(f, et_ns("2025-06-02", 15, 50, 10), 3_000_000_000.0)
    assert sig is not None
    assert sig["side"] == 1
    assert sig["near_price"] == pytest.approx(150.0)
    assert sig["norm_imb"] == pytest.approx(0.005, abs=1e-12)


def test_signal_sell_side_is_negative() -> None:
    f = _noii_frame([_row(et_ns("2025-06-02", 15, 50, 5), "S", 40_000.0, 200.0)])
    sig = signal_at(f, et_ns("2025-06-02", 15, 50, 10), 4_000_000_000.0)
    # norm = -1 * 40000 * 200 / 4e9 = -8_000_000/4e9 = -0.002
    assert sig["side"] == -1
    assert sig["norm_imb"] == pytest.approx(-0.002, abs=1e-12)


def test_signal_pit_takes_last_at_or_before() -> None:
    d = "2025-06-02"
    f = _noii_frame(
        [
            _row(et_ns(d, 15, 49, 0), "B", 10_000.0, 100.0),
            _row(et_ns(d, 15, 50, 5), "S", 50_000.0, 100.0),  # <- PIT winner @155010
            _row(et_ns(d, 15, 50, 20), "B", 90_000.0, 100.0),  # future: must be ignored
        ]
    )
    sig = signal_at(f, et_ns(d, 15, 50, 10), 1_000_000_000.0)
    # last at-or-before 15:50:10 is the 15:50:05 SELL row (50_000 @ 100)
    assert sig["side"] == -1
    assert sig["norm_imb"] == pytest.approx(-1 * 50_000.0 * 100.0 / 1e9, abs=1e-12)


def test_signal_none_when_no_message_at_or_before() -> None:
    d = "2025-06-02"
    f = _noii_frame([_row(et_ns(d, 15, 50, 20), "B", 10_000.0, 100.0)])
    assert signal_at(f, et_ns(d, 15, 50, 10), 1e9) is None


def test_signal_none_on_empty_or_none_frame() -> None:
    assert signal_at(None, 123, 1e9) is None
    assert signal_at(_noii_frame([]), 123, 1e9) is None


def test_signal_near_price_falls_back_to_ref_when_zero() -> None:
    d = "2025-06-02"
    f = _noii_frame([_row(et_ns(d, 15, 50, 5), "B", 20_000.0, 0.0, ref=125.0)])
    sig = signal_at(f, et_ns(d, 15, 50, 10), 5e9)
    assert sig["near_price"] == pytest.approx(125.0)
    assert sig["norm_imb"] == pytest.approx(20_000.0 * 125.0 / 5e9, abs=1e-12)


def test_signal_no_imbalance_direction_is_flat() -> None:
    d = "2025-06-02"
    f = _noii_frame([_row(et_ns(d, 15, 50, 5), "N", 20_000.0, 100.0)])
    sig = signal_at(f, et_ns(d, 15, 50, 10), 5e9)
    assert sig["side"] == 0
    assert sig["norm_imb"] == 0.0


# --------------------------------------------------------------------------- normalize


def test_normalize_maps_databento_columns() -> None:
    # databento-shaped imbalance to_df frame (pretty px/ts already applied).
    raw = pl.DataFrame(
        {
            "ts_event": [111, 222],
            "side": ["B", "s"],  # mixed case tolerated
            "total_imbalance_qty": [1000.0, 2000.0],
            "paired_qty": [500.0, 600.0],
            "cont_book_clr_price": [10.0, 11.0],
            "auct_interest_clr_price": [9.5, 10.5],
            "ref_price": [10.1, 11.1],
            "extra_col": ["x", "y"],  # ignored
        }
    )
    out = normalize_imbalance_df(raw)
    assert list(out.columns) == list(NOII_SCHEMA)
    assert out["ts"].to_list() == [111, 222]
    assert out["side"].to_list() == ["B", "S"]
    assert out["imbalance_shares"].to_list() == [1000.0, 2000.0]
    assert out["near_price"].to_list() == [10.0, 11.0]
    assert out["far_price"].to_list() == [9.5, 10.5]
    assert out["ref_price"].to_list() == [10.1, 11.1]


def test_normalize_fills_missing_optional_columns_with_null() -> None:
    raw = pl.DataFrame({"ts_event": [5], "side": ["B"], "total_imbalance_qty": [1.0]})
    out = normalize_imbalance_df(raw)
    assert out["paired_shares"].to_list() == [None]
    assert out["near_price"].to_list() == [None]


# --------------------------------------------------------------------------- load session


def test_load_noii_session_windows_and_missing(tmp_path) -> None:
    d = "2025-06-02"
    root = tmp_path / "noii"
    # write a normalized partition with one in-window and one out-of-window msg.
    frame = _noii_frame(
        [
            _row(et_ns(d, 15, 30, 0), "B", 1.0, 100.0),  # before 15:45 -> excluded
            _row(et_ns(d, 15, 50, 5), "B", 2.0, 100.0),  # in window
            _row(et_ns(d, 16, 10, 0), "B", 3.0, 100.0),  # after 16:00 -> excluded
        ]
    )
    p = partition_path(root, "NVDA", "2025-06")
    p.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(p)

    got = load_noii_session("NVDA", d, out_dir=root)
    assert got is not None
    assert got.height == 1
    assert got["imbalance_shares"].to_list() == [2.0]

    # absent partition -> None (distinct from an empty in-window frame)
    assert load_noii_session("TSLA", d, out_dir=root) is None


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
    # ts on 2025-02-15 (the resumability test's END date): the downloader's
    # end-month coverage check re-fetches a partition whose max ts predates the
    # requested end (partial-current-month contract; data/noii.py).
    return pl.DataFrame(
        {
            "ts_event": [1_739_577_600_000_000_000, 1_739_577_660_000_000_000],
            "side": ["B", "S"],
            "total_imbalance_qty": [10.0, 20.0],
            "paired_qty": [1.0, 2.0],
            "cont_book_clr_price": [100.0, 101.0],
            "auct_interest_clr_price": [99.0, 100.0],
            "ref_price": [100.1, 101.1],
        }
    )


def test_download_missing_key_raises(tmp_path) -> None:
    settings = Settings(databento_api_key="", data_dir=tmp_path)
    with pytest.raises(RuntimeError, match="DATABENTO_API_KEY"):
        download_noii(settings, ["NVDA"], "2025-01-02", "2025-01-31", out_dir=tmp_path / "noii")


def test_download_cost_guard_aborts(tmp_path) -> None:
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    fake = _FakeHistorical(cost=100.0, df=_dbn_df())
    with pytest.raises(RuntimeError, match="cost quote"):
        download_noii(
            settings, ["NVDA"], "2025-01-02", "2025-01-31",
            out_dir=tmp_path / "noii", max_cost=60.0, client=fake,
        )
    # aborted BEFORE any timeseries request
    assert fake.timeseries.calls == []
    assert len(fake.metadata.calls) == 1


def test_download_writes_resumable_partitions(tmp_path) -> None:
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / "noii"
    fake = _FakeHistorical(cost=5.0, df=_dbn_df())
    summary = download_noii(
        settings, ["NVDA", "TSLA"], "2025-01-02", "2025-02-15",
        out_dir=out_dir, max_cost=60.0, client=fake,
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
            assert list(back.columns) == list(NOII_SCHEMA)
            assert back["side"].to_list() == ["B", "S"]
            assert back["near_price"].to_list() == [100.0, 101.0]

    # rerun: everything present -> skipped, no new network calls
    fake2 = _FakeHistorical(cost=5.0, df=_dbn_df())
    summary2 = download_noii(
        settings, ["NVDA", "TSLA"], "2025-01-02", "2025-02-15",
        out_dir=out_dir, max_cost=60.0, client=fake2,
    )
    assert summary2["partitions_written"] == 0
    assert summary2["partitions_skipped"] == 4
    assert fake2.timeseries.calls == []


def test_download_cost_endpoint_receives_full_range(tmp_path) -> None:
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    fake = _FakeHistorical(cost=1.0, df=_dbn_df())
    download_noii(
        settings, ["NVDA"], "2025-01-02", "2025-01-31",
        out_dir=tmp_path / "noii", client=fake,
    )
    call = fake.metadata.calls[0]
    assert call["dataset"] == noii.DATASET
    assert call["schema"] == noii.SCHEMA
    assert call["symbols"] == ["NVDA"]
    # end is exclusive -> one day past the inclusive end
    assert call["end"] == "2025-02-01"


# ------------------------------------- condition-probe escape hatch (2026-08-01 FIX 2)
#
# The end-day probe is FAIL-CLOSED by default (B6). The reviewer's objection: a vendor
# condition endpoint that is merely DOWN then blocks acquisition with no operator way
# out. `require_condition_probe=False` (CLI `--skip-condition-probe`) is that way out —
# it applies ONLY to a probe that RAISES, never to an explicit degraded/pending verdict,
# and the two cases must be distinguishable in the log.


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
        summary = download_noii(
            settings, ["NVDA"], "2025-01-02", "2025-01-31",
            out_dir=tmp_path / "noii", client=client, **kw,
        )
    return summary, client, logs


def test_probe_failure_fails_closed_by_default(tmp_path) -> None:
    """Default (no kwarg) is unchanged: a raising probe skips the end month."""
    summary, client, logs = _probe_download(tmp_path, None)
    assert summary["partitions_written"] == 0
    assert summary["partitions_skipped"] == 1
    assert client.timeseries.calls == []
    assert not partition_path(tmp_path / "noii", "NVDA", "2025-01").exists()
    failed = [e for e in logs if e.get("event") == "noii_condition_probe_failed"]
    assert len(failed) == 1
    assert failed[0]["log_level"] == "warning"
    assert "--skip-condition-probe" in failed[0]["detail"]
    assert [e for e in logs if e.get("event") == "noii_condition_probe_override"] == []


def test_probe_failure_override_proceeds_and_writes(tmp_path) -> None:
    """require_condition_probe=False: the raising probe no longer blocks the fetch."""
    summary, client, logs = _probe_download(tmp_path, None, require_condition_probe=False)
    assert summary["partitions_written"] == 1
    assert len(client.timeseries.calls) == 1
    assert partition_path(tmp_path / "noii", "NVDA", "2025-01").exists()
    over = [e for e in logs if e.get("event") == "noii_condition_probe_override"]
    assert len(over) == 1
    assert over[0]["log_level"] == "warning"
    assert "operator override" in over[0]["detail"]
    assert "metadata endpoint down" in over[0]["detail"]  # names the underlying error
    assert [e for e in logs if e.get("event") == "noii_condition_probe_failed"] == []


def test_degraded_verdict_is_not_overridable(tmp_path) -> None:
    """A probe that SUCCEEDS and reports degraded still skips, override or not —
    and its log line is the vendor-verdict one, never the probe-failure one."""
    summary, client, logs = _probe_download(
        tmp_path, "degraded", require_condition_probe=False
    )
    assert summary["partitions_written"] == 0
    assert client.timeseries.calls == []
    verdict = [e for e in logs if e.get("event") == "noii_day_not_available"]
    assert len(verdict) == 1
    assert verdict[0]["condition"] == "degraded"
    assert "degraded/pending" in verdict[0]["detail"]
    assert [e for e in logs if e.get("event").startswith("noii_condition_probe")] == []


def test_probe_failure_and_vendor_verdict_log_different_events(tmp_path) -> None:
    """The two failure modes the reviewer asked to be told apart, side by side."""
    _, _, raised = _probe_download(tmp_path / "a", None)
    _, _, verdict = _probe_download(tmp_path / "b", "pending")
    raised_events = {e["event"] for e in raised if e.get("log_level") == "warning"}
    verdict_events = {e["event"] for e in verdict if e.get("log_level") == "warning"}
    assert raised_events == {"noii_condition_probe_failed"}
    assert verdict_events == {"noii_day_not_available"}
    assert raised_events.isdisjoint(verdict_events)


def test_side_sign_databento_ask_convention():
    # databento normalizes ITCH sell-imbalance 'S' to Side.ASK == 'A' (real data
    # carries B/A/N). 'A' must map to -1 or every sell event silently vanishes.
    from enginev51.data.noii import _side_sign
    assert _side_sign("B") == 1
    assert _side_sign("A") == -1
    assert _side_sign("S") == -1
    assert _side_sign("N") == 0
