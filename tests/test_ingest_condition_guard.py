"""Freshness-guard tests for the live forward-paper ingest (data/noii.py and
data/bbo1s.py) — hardening against the 2026-07-20 incident where an ingest ran
while Databento XNAS.ITCH was still publishing the prior session, wrote a PARTIAL
day into the monthly partition, and skip-exists then locked in the hole.

Both downloaders now PRE-FLIGHT the request's END day via
``metadata.get_dataset_condition`` (mocked here exactly as the databento client is
mocked in test_noii.py / test_bbo1s.py). A non-available condition
(degraded/pending/missing/absent) => the end month is skipped, its partition left
UNTOUCHED so a later run heals it. A metadata *exception* is FAIL-CLOSED (also
skips the end month — code review 2026-07-28 B6); earlier, fully-past months are
final at the vendor and stay fetchable regardless.

Also covers the B6 end-month COVERAGE rule: a present end-month partition only
counts as covering ``end_d`` once its max(ts) reaches the session close window,
not merely the calendar date of ``end_d``.

Every expected value is derived from literals so the tests cannot merely echo the
implementation.
"""

from __future__ import annotations

import polars as pl
import pytest
from structlog.testing import capture_logs

from enginev51.config import Settings
from enginev51.data import bbo1s as bbo_mod
from enginev51.data import noii as noii_mod
from enginev51.data.noii import et_ns

# --------------------------------------------------------------------------- fakes


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
    """databento ``metadata``-shaped mock. ``get_dataset_range`` is intentionally
    ABSENT (mirrors the existing module fakes: the cost guard's probe raises and
    is swallowed, leaving end_excl = end+1). ``get_dataset_condition`` returns the
    real API shape — ``list[dict[str, str | None]]`` — or raises when configured.
    """

    def __init__(self, cost: float, condition: str, condition_raises: bool) -> None:
        self._cost = cost
        self._condition = condition
        self._condition_raises = condition_raises
        self.cost_calls: list[dict] = []
        self.condition_calls: list[dict] = []

    def get_cost(self, **kw):  # noqa: ANN003
        self.cost_calls.append(kw)
        return self._cost

    def get_dataset_condition(self, **kw):  # noqa: ANN003
        self.condition_calls.append(kw)
        if self._condition_raises:
            raise RuntimeError("metadata endpoint down")
        day = kw.get("end_date") or kw.get("start_date")
        return [{"date": str(day), "condition": self._condition,
                 "last_modified_date": "2026-07-21"}]


class _FakeHistorical:
    def __init__(self, df: pl.DataFrame, *, cost: float = 1.0,
                 condition: str = "available", condition_raises: bool = False) -> None:
        self.metadata = _FakeMeta(cost, condition, condition_raises)
        self.timeseries = _FakeTimeseries(df)


def _noii_df() -> pl.DataFrame:
    # databento imbalance to_df shape. Row dates are immaterial to the guard.
    return pl.DataFrame({
        "ts_event": [et_ns("2025-01-15", 15, 50, 5), et_ns("2025-01-15", 15, 50, 6)],
        "side": ["B", "A"],
        "total_imbalance_qty": [10.0, 20.0],
        "paired_qty": [1.0, 2.0],
        "cont_book_clr_price": [100.0, 101.0],
        "auct_interest_clr_price": [99.0, 100.0],
        "ref_price": [100.1, 101.1],
    })


def _bbo_df() -> pl.DataFrame:
    # databento bbo-1s to_df shape. Row dates are immaterial to the guard.
    return pl.DataFrame({
        "ts_recv": [et_ns("2025-01-15", 15, 50, 5), et_ns("2025-01-15", 15, 50, 6)],
        "ts_event": [et_ns("2025-01-15", 15, 50, 5), et_ns("2025-01-15", 15, 50, 6)],
        "bid_px_00": [99.0, 99.5],
        "ask_px_00": [100.0, 100.5],
        "bid_sz_00": [100.0, 200.0],
        "ask_sz_00": [300.0, 400.0],
    })


# One parametrized case per download module: (download_fn, df_factory, partition_path, prefix).
_CASES = [
    pytest.param(noii_mod.download_noii, _noii_df, noii_mod.partition_path, "noii", id="noii"),
    pytest.param(bbo_mod.download_bbo1s, _bbo_df, bbo_mod.partition_path, "bbo1s", id="bbo1s"),
]


# --------------------------------------------------------------------------- tests


@pytest.mark.parametrize("download, make_df, part_path, prefix", _CASES)
def test_degraded_end_day_skips_month_untouched(
    tmp_path, download, make_df, part_path, prefix
) -> None:
    # (a) end-day degraded -> no partition write, warning logged, clean return.
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / prefix
    fake = _FakeHistorical(make_df(), cost=1.0, condition="degraded")

    with capture_logs() as logs:
        summary = download(settings, ["NVDA"], "2025-01-02", "2025-01-31",
                           out_dir=out_dir, client=fake)

    # end month is the ONLY month -> skipped; nothing fetched, partition untouched
    assert summary["partitions_written"] == 0
    assert summary["partitions_skipped"] == 1
    assert fake.timeseries.calls == []  # no bytes fetched (heal-later property)
    assert not part_path(out_dir, "NVDA", "2025-01").exists()
    # the guard probed exactly the end day, once
    assert len(fake.metadata.condition_calls) == 1
    assert fake.metadata.condition_calls[0]["start_date"] == "2025-01-31"
    assert fake.metadata.condition_calls[0]["end_date"] == "2025-01-31"
    # structured warning names the condition and the as-of day, at warning level
    warns = [e for e in logs if e.get("event") == f"{prefix}_day_not_available"]
    assert len(warns) == 1
    assert warns[0]["condition"] == "degraded"
    assert warns[0]["asof"] == "2025-01-31"
    assert warns[0]["log_level"] == "warning"


@pytest.mark.parametrize("download, make_df, part_path, prefix", _CASES)
def test_available_end_day_proceeds(
    tmp_path, download, make_df, part_path, prefix
) -> None:
    # (b) end-day available -> fetch proceeds (existing behavior unchanged).
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / prefix
    fake = _FakeHistorical(make_df(), cost=1.0, condition="available")

    with capture_logs() as logs:
        summary = download(settings, ["NVDA"], "2025-01-02", "2025-01-31",
                           out_dir=out_dir, client=fake)

    assert summary["partitions_written"] == 1
    assert len(fake.timeseries.calls) == 1
    assert part_path(out_dir, "NVDA", "2025-01").exists()
    assert len(fake.metadata.condition_calls) == 1  # guard still ran
    assert [e for e in logs if e.get("event") == f"{prefix}_day_not_available"] == []


@pytest.mark.parametrize("download, make_df, part_path, prefix", _CASES)
def test_metadata_exception_fails_closed(
    tmp_path, download, make_df, part_path, prefix
) -> None:
    # (c) metadata exception -> the end month is treated as NOT available and left
    # untouched (FAIL-CLOSED, code review 2026-07-28 B6). The old behaviour was
    # fail-open, which proceeded blind on exactly the failure mode the guard
    # exists for; a skip costs one re-run, a partial end month is permanent.
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / prefix
    fake = _FakeHistorical(make_df(), cost=1.0, condition_raises=True)

    with capture_logs() as logs:
        summary = download(settings, ["NVDA"], "2025-01-02", "2025-01-31",
                           out_dir=out_dir, client=fake)

    # 2025-01 is the ONLY month and it is the end month -> nothing fetched/written
    assert summary["partitions_written"] == 0
    assert summary["partitions_skipped"] == 1
    assert fake.timeseries.calls == []
    assert not part_path(out_dir, "NVDA", "2025-01").exists()
    warns = [e for e in logs if e.get("event") == f"{prefix}_condition_probe_failed"]
    assert len(warns) == 1
    assert warns[0]["asof"] == "2025-01-31"
    assert warns[0]["log_level"] == "warning"


@pytest.mark.parametrize("download, make_df, part_path, prefix", _CASES)
def test_metadata_exception_leaves_earlier_months_fetchable(
    tmp_path, download, make_df, part_path, prefix
) -> None:
    # Fail-closed is scoped to the END month only: fully-past months are final at
    # the vendor and stay fetchable even while the condition endpoint is down.
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / prefix
    fake = _FakeHistorical(make_df(), cost=1.0, condition_raises=True)

    summary = download(settings, ["NVDA"], "2025-01-02", "2025-02-15",
                       out_dir=out_dir, client=fake)

    assert summary["partitions_written"] == 1  # Jan only
    assert part_path(out_dir, "NVDA", "2025-01").exists()
    assert not part_path(out_dir, "NVDA", "2025-02").exists()


def _seed_partition(prefix: str, path, ts_ns: int) -> None:
    """Write a one-row end-month partition whose max(ts) is exactly ``ts_ns``."""
    if prefix == "noii":
        df = pl.DataFrame(
            {"ts": [ts_ns], "side": ["B"], "imbalance_shares": [10.0],
             "paired_shares": [1.0], "near_price": [100.0], "far_price": [99.0],
             "ref_price": [100.1]},
            schema=noii_mod.NOII_SCHEMA,
        )
    else:
        df = pl.DataFrame(
            {"ts": [ts_ns], "bid": [99.0], "ask": [100.0],
             "bid_size": [100.0], "ask_size": [100.0]},
            schema=bbo_mod.BBO_SCHEMA,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)


@pytest.mark.parametrize("download, make_df, part_path, prefix", _CASES)
def test_end_month_midsession_rows_are_not_coverage(
    tmp_path, download, make_df, part_path, prefix
) -> None:
    # B6: 2025-01-31 is a regular session (16:00 ET close). A partition whose last
    # row is 10:00 ET LANDS ON end_d but carries none of the close window. The old
    # rule compared the calendar DATE of max(ts) and called that covered, freezing
    # a partial month behind skip-exists; coverage now means reaching the close.
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / prefix
    _seed_partition(prefix, part_path(out_dir, "NVDA", "2025-01"),
                    et_ns("2025-01-31", 10, 0, 0))
    fake = _FakeHistorical(make_df(), cost=1.0, condition="available")

    with capture_logs() as logs:
        summary = download(settings, ["NVDA"], "2025-01-02", "2025-01-31",
                           out_dir=out_dir, client=fake)

    assert summary["partitions_written"] == 1  # re-fetched, not skipped
    assert len(fake.timeseries.calls) == 1
    assert [e for e in logs if e.get("event") == f"{prefix}_skip_exists"] == []
    extend = [e for e in logs if e.get("event") == f"{prefix}_extend_partial_month"]
    assert len(extend) == 1
    assert extend[0]["need_through"] == "2025-01-31"


@pytest.mark.parametrize("download, make_df, part_path, prefix", _CASES)
def test_end_month_close_window_rows_are_coverage(
    tmp_path, download, make_df, part_path, prefix
) -> None:
    # The other side of the same rule: 15:59:30 ET is inside both floors (close-5min
    # for NOII and, since 2026-08-01 FIX 6, for bbo-1s too) -> nothing re-fetched.
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / prefix
    _seed_partition(prefix, part_path(out_dir, "NVDA", "2025-01"),
                    et_ns("2025-01-31", 15, 59, 30))
    fake = _FakeHistorical(make_df(), cost=1.0, condition="available")

    summary = download(settings, ["NVDA"], "2025-01-02", "2025-01-31",
                       out_dir=out_dir, client=fake)

    assert summary["partitions_written"] == 0
    assert summary["partitions_skipped"] == 1
    assert fake.timeseries.calls == []


@pytest.mark.parametrize("download, make_df, part_path, prefix", _CASES)
def test_end_month_coverage_honors_early_close(
    tmp_path, download, make_df, part_path, prefix
) -> None:
    # 2024-11-29 is a listed NYSE half-day: the session closes 13:00 ET. A
    # partition whose last row is 12:59:30 ET therefore COVERS it. A floor pinned
    # to a fixed 16:00 close would call every half-day partial and re-fetch the
    # month on every run forever; the floor comes from the calendar instead.
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / prefix
    _seed_partition(prefix, part_path(out_dir, "NVDA", "2024-11"),
                    et_ns("2024-11-29", 12, 59, 30))
    fake = _FakeHistorical(make_df(), cost=1.0, condition="available")

    summary = download(settings, ["NVDA"], "2024-11-01", "2024-11-29",
                       out_dir=out_dir, client=fake)

    assert summary["partitions_written"] == 0
    assert summary["partitions_skipped"] == 1
    assert fake.timeseries.calls == []


@pytest.mark.parametrize("download, make_df, part_path, prefix", _CASES)
def test_degraded_end_day_leaves_earlier_months_and_heals(
    tmp_path, download, make_df, part_path, prefix
) -> None:
    # earlier FULLY-past months are unaffected; the end month heals on a later run
    # once the vendor marks the day available.
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / prefix

    fake = _FakeHistorical(make_df(), cost=1.0, condition="degraded")
    summary = download(settings, ["NVDA"], "2025-01-02", "2025-02-15",
                       out_dir=out_dir, client=fake)
    # Jan (fully past) fetched; Feb (the end month) skipped and left untouched
    assert summary["partitions_written"] == 1
    assert len(fake.timeseries.calls) == 1
    assert part_path(out_dir, "NVDA", "2025-01").exists()
    assert not part_path(out_dir, "NVDA", "2025-02").exists()

    # heal-later: a re-run with the day now available fills the previously-skipped
    # end month, leaving the finalized Jan partition alone.
    fake2 = _FakeHistorical(make_df(), cost=1.0, condition="available")
    summary2 = download(settings, ["NVDA"], "2025-01-02", "2025-02-15",
                        out_dir=out_dir, client=fake2)
    assert part_path(out_dir, "NVDA", "2025-02").exists()  # now healed
    assert summary2["partitions_written"] == 1  # only Feb; Jan skipped as present


def test_both_downloaders_share_the_same_close_margin() -> None:
    """FIX 6 (code review 2026-08-01): bbo-1s used a 60 s close margin while NOII used
    300 s. A month whose last 1s snapshot lands 2 minutes before the bell was therefore
    judged INCOMPLETE forever and re-downloaded whole on every run — the expensive
    failure mode with credits nearly exhausted. Both floors are now 5 minutes."""
    assert bbo_mod.CLOSE_MARGIN_S == noii_mod.CLOSE_MARGIN_S == 300


@pytest.mark.parametrize("download, make_df, part_path, prefix", _CASES)
def test_last_snapshot_minutes_before_the_bell_is_coverage(
    tmp_path, download, make_df, part_path, prefix
) -> None:
    """15:57:00 ET on a 16:00 close: 3 minutes short of the bell. Under the old 60 s
    bbo-1s floor this re-fetched the whole month on every run; under the shared 300 s
    floor it is coverage and nothing is fetched."""
    settings = Settings(databento_api_key="TESTKEY", data_dir=tmp_path)
    out_dir = tmp_path / prefix
    _seed_partition(prefix, part_path(out_dir, "NVDA", "2025-01"),
                    et_ns("2025-01-31", 15, 57, 0))
    fake = _FakeHistorical(make_df(), cost=1.0, condition="available")

    summary = download(settings, ["NVDA"], "2025-01-02", "2025-01-31",
                       out_dir=out_dir, client=fake)

    assert summary["partitions_written"] == 0
    assert summary["partitions_skipped"] == 1
    assert fake.timeseries.calls == []
