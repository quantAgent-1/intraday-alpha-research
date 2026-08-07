"""Unit tests for the backfill planner/status/disk-guard. NO network."""

from __future__ import annotations

import types
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from enginev51.config import Settings
from enginev51.data import backfill, store
from enginev51.data import calendar as cal

FEED = "sip"


@pytest.fixture(autouse=True)
def _isolate_legacy_lake(tmp_path: Path, monkeypatch) -> None:
    """Belt-and-braces: no test in this module may resolve the REAL engineV5 lake.

    This is the only test module that WRITES to the legacy root (to fake a legacy
    partition), so a `legacy_data_dir` that silently falls back to the machine's
    absolute path does not just break isolation — it overwrites live 11 GB
    partitions with the fixtures' zero-row stubs. That happened on 2026-08-01 while
    the field briefly carried a `validation_alias` (which drops the explicit
    kwarg). Pinning the env override too makes the isolation independent of how
    `config` chooses to resolve the path.
    """
    monkeypatch.setenv("ENGINEV51_LEGACY_DATA_DIR", str(tmp_path / "legacy"))


def _settings(tmp_path: Path) -> Settings:
    """Settings whose read roots are two tmp lakes (primary + fake legacy)."""
    return Settings(
        data_dir=tmp_path / "primary",
        legacy_data_dir=tmp_path / "legacy",
    )


def _write(root: Path, kind: str, symbol: str, part: str, rows: list[dict]) -> None:
    store.write_partition(root, FEED, kind, symbol, part, rows)


def _trade_row(ts: int) -> dict:
    return {"ts": ts, "price": 1.0, "size": 1.0, "exchange": "", "conditions": "", "tape": ""}


def _quote_row(ts: int) -> dict:
    return {
        "ts": ts, "bid": 1.0, "bid_size": 1.0, "bid_exchange": "",
        "ask": 1.1, "ask_size": 1.0, "ask_exchange": "", "conditions": "", "tape": "",
    }


def test_plan_ticks_missing_detection(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    primary = settings.raw_dir
    legacy = settings.legacy_data_dir / "raw"

    start, end = date(2026, 1, 5), date(2026, 1, 9)
    days = cal.trading_days(start, end)
    assert len(days) == 5  # full trading week, no holidays

    # NVDA: day0 covered in the LEGACY lake, day1 covered in PRIMARY (both kinds).
    for kind in ("trades", "quotes"):
        _write(legacy, kind, "NVDA", days[0].isoformat(), [])
        _write(primary, kind, "NVDA", days[1].isoformat(), [])

    # TSLA: trades present for ALL days; quotes present for all days EXCEPT one
    # -> a single quote-only gap (the TSLA quote-gap case).
    gap_day = days[2]
    for d in days:
        _write(primary, "trades", "TSLA", d.isoformat(), [])
        if d != gap_day:
            _write(primary, "quotes", "TSLA", d.isoformat(), [])

    # AMD: nothing on disk anywhere -> fully missing.
    work = backfill.plan_ticks(settings, ["NVDA", "TSLA", "AMD"], start, end)

    nvda = [w for w in work if w[0] == "NVDA"]
    tsla = [w for w in work if w[0] == "TSLA"]
    amd = [w for w in work if w[0] == "AMD"]

    # NVDA: 2 of 5 days covered (both kinds) -> 3 days * 2 kinds missing.
    assert len(nvda) == 3 * 2
    covered = {days[0].isoformat(), days[1].isoformat()}
    assert all(w[1] not in covered for w in nvda)

    # TSLA: exactly one missing item, and it is a QUOTE on the gap day.
    assert tsla == [("TSLA", gap_day.isoformat(), "quotes")]

    # AMD: every session, both kinds.
    assert len(amd) == 5 * 2
    assert {w[2] for w in amd} == {"trades", "quotes"}


def test_plan_ticks_empty_when_all_present(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    start, end = date(2026, 1, 5), date(2026, 1, 6)
    days = cal.trading_days(start, end)
    for d in days:
        for kind in ("trades", "quotes"):
            _write(settings.raw_dir, kind, "MU", d.isoformat(), [_trade_row(1)])
    assert backfill.plan_ticks(settings, ["MU"], start, end) == []


def test_backfill_today_incomplete_not_planned(tmp_path: Path) -> None:
    # F4 regression (code review 2026-07-17): a session whose close is not yet
    # sip_recency_margin_minutes in the past must never be planned — the fetch
    # would come back truncated by the recency clamp, and the written partition
    # (presence == completeness) would freeze the partial day in forever.
    settings = _settings(tmp_path)
    day = date(2026, 7, 16)  # regular Thursday session: 16:00 ET = 20:00 UTC close

    # mid-session (14:00 ET): nothing planned for that day
    mid = datetime(2026, 7, 16, 18, 0, tzinfo=UTC)
    assert backfill.plan_ticks(settings, ["NVDA"], day, day, now=mid) == []

    # close + margin passed (20:30 UTC >= 20:00 + 20min): planned as usual
    after = datetime(2026, 7, 16, 20, 30, tzinfo=UTC)
    work = backfill.plan_ticks(settings, ["NVDA"], day, day, now=after)
    assert {w[2] for w in work} == {"trades", "quotes"}
    assert len(work) == 2


def test_run_ticks_skips_not_final_session(tmp_path: Path) -> None:
    # F4: even if a non-final item reaches the runner (stale plan), it must be
    # skipped WITHOUT fetching or writing — the API here raises if touched.
    settings = _settings(tmp_path)
    day = "2026-07-16"

    class BoomApi:
        def fetch_trades(self, *a, **k):
            raise AssertionError("fetched a non-final session")

        def fetch_quotes(self, *a, **k):
            raise AssertionError("fetched a non-final session")

        def close(self) -> None:
            pass

    mid = datetime(2026, 7, 16, 18, 0, tzinfo=UTC)
    written = backfill.run_ticks(
        settings, [("NVDA", day, "trades")], api=BoomApi(), now=mid
    )
    assert written == 0
    assert not store.partition_exists(settings.raw_dir, FEED, "trades", "NVDA", day)


def test_disk_floor_guard_raises_on_impossible_floor(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        backfill, "get_research_config",
        lambda: types.SimpleNamespace(disk_floor_gb=1_000_000.0),
    )
    with pytest.raises(RuntimeError, match="disk floor breached"):
        backfill.disk_floor_guard(settings)


def test_disk_floor_guard_passes_on_zero_floor(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        backfill, "get_research_config",
        lambda: types.SimpleNamespace(disk_floor_gb=0.0),
    )
    free = backfill.disk_floor_guard(settings)
    assert free > 0


# --------------------------------------------------------- B4/B5 heal + completeness
#
# Presence-is-complete has no way back: a truncated / zero-row / corrupt PRIMARY
# partition is skipped forever, including under `force`. These pin the two opt-in
# escapes (`force_overwrite`, `require_complete`) AND that neither one alters the
# default plan/run path, which must keep judging the existing lake by presence.

# 2026-07-16 is a regular Thursday session: 09:30-16:00 ET = 13:30-20:00 UTC.
_SESSION = date(2026, 7, 16)
_SESSION_ISO = _SESSION.isoformat()
_AFTER = datetime(2026, 7, 16, 21, 0, tzinfo=UTC)  # past close + recency margin
_NS = 1_000_000_000


def _et_ns(day: date, h: int, m: int, s: int = 0) -> int:
    from zoneinfo import ZoneInfo
    et = ZoneInfo("America/New_York")
    return int(datetime(day.year, day.month, day.day, h, m, s, tzinfo=et).timestamp()) * _NS


class _FakeApi:
    """AlpacaHist-shaped stub: yields one page of `rows` per tick fetch."""

    def __init__(self, rows: list[dict] | None = None) -> None:
        self.rows = rows or []
        self.calls: list[tuple[str, str]] = []

    def _pages(self, kind: str, symbol: str):
        self.calls.append((kind, symbol))
        if self.rows:
            yield list(self.rows)

    def fetch_trades(self, symbol, start, end, feed="sip"):  # noqa: ANN001
        return self._pages("trades", symbol)

    def fetch_quotes(self, symbol, start, end, feed="sip"):  # noqa: ANN001
        return self._pages("quotes", symbol)

    def close(self) -> None:
        pass


@pytest.fixture()
def _no_disk_floor(monkeypatch):
    monkeypatch.setattr(
        backfill, "get_research_config",
        lambda: types.SimpleNamespace(disk_floor_gb=0.0),
    )


def test_force_skips_primary_but_force_overwrite_rewrites_it(
    tmp_path: Path, _no_disk_floor
) -> None:
    # B4: a TRUNCATED primary day (last print 10:00 ET) is invisible to `force` —
    # only --force-overwrite can replace it.
    settings = _settings(tmp_path)
    truncated_ts = _et_ns(_SESSION, 10, 0)
    _write(settings.raw_dir, "trades", "NVDA", _SESSION_ISO, [_trade_row(truncated_ts)])

    # legacy semantics untouched: force still skips anything the primary holds
    assert backfill.plan_ticks(
        settings, ["NVDA"], _SESSION, _SESSION, force=True, now=_AFTER
    ) == [("NVDA", _SESSION_ISO, "quotes")]

    api = _FakeApi([_trade_row(truncated_ts)])
    assert backfill.run_ticks(
        settings, [("NVDA", _SESSION_ISO, "trades")], api=api, force=True, now=_AFTER
    ) == 0
    assert api.calls == []  # nothing fetched

    # force_overwrite plans every session and REWRITES the primary partition
    work = backfill.plan_ticks(
        settings, ["NVDA"], _SESSION, _SESSION, force_overwrite=True, now=_AFTER
    )
    assert sorted(w[2] for w in work) == ["quotes", "trades"]

    good_ts = _et_ns(_SESSION, 15, 58)
    api2 = _FakeApi([_trade_row(good_ts)])
    assert backfill.run_ticks(
        settings, [("NVDA", _SESSION_ISO, "trades")], api=api2,
        force_overwrite=True, now=_AFTER,
    ) == 1
    path = store.partition_path(settings.raw_dir, FEED, "trades", "NVDA", _SESSION_ISO)
    assert store.partition_max_ts(path) == good_ts  # healed in place


def test_force_overwrite_still_refuses_a_non_final_session(tmp_path: Path) -> None:
    # The heal path must not install a FRESH truncation: the F4 recency guard wins.
    settings = _settings(tmp_path)
    mid = datetime(2026, 7, 16, 18, 0, tzinfo=UTC)  # mid-session
    assert backfill.plan_ticks(
        settings, ["NVDA"], _SESSION, _SESSION, force_overwrite=True, now=mid
    ) == []
    api = _FakeApi([_trade_row(_et_ns(_SESSION, 14, 0))])
    assert backfill.run_ticks(
        settings, [("NVDA", _SESSION_ISO, "trades")], api=api,
        force_overwrite=True, now=mid,
    ) == 0
    assert api.calls == []


def test_require_complete_flags_truncated_primary(tmp_path: Path) -> None:
    # B4: content completeness = rows reaching the session close window.
    settings = _settings(tmp_path)
    _write(settings.raw_dir, "trades", "NVDA", _SESSION_ISO,
           [_trade_row(_et_ns(_SESSION, 10, 0))])
    _write(settings.raw_dir, "quotes", "NVDA", _SESSION_ISO,
           [_quote_row(_et_ns(_SESSION, 15, 58))])

    # DEFAULT path is presence-only and must not change: nothing planned.
    assert backfill.plan_ticks(settings, ["NVDA"], _SESSION, _SESSION, now=_AFTER) == []

    # opt-in: only the truncated trades day surfaces
    assert backfill.plan_ticks(
        settings, ["NVDA"], _SESSION, _SESSION, require_complete=True, now=_AFTER
    ) == [("NVDA", _SESSION_ISO, "trades")]

    root = settings.raw_dir
    assert not backfill.partition_complete(root, settings, "trades", "NVDA", _SESSION_ISO)
    assert backfill.partition_complete(root, settings, "quotes", "NVDA", _SESSION_ISO)


def test_require_complete_honors_early_close(tmp_path: Path) -> None:
    # 2024-11-29 is a listed NYSE half-day (13:00 ET close). A tape ending 12:58 ET
    # is COMPLETE there; a floor pinned to 16:00 would re-plan every half-day.
    settings = _settings(tmp_path)
    half = date(2024, 11, 29)
    iso = half.isoformat()
    after = datetime(2024, 11, 29, 19, 0, tzinfo=UTC)  # past 18:00 UTC close + margin
    for kind, row in (("trades", _trade_row), ("quotes", _quote_row)):
        _write(settings.raw_dir, kind, "NVDA", iso, [row(_et_ns(half, 12, 58))])

    assert backfill.plan_ticks(
        settings, ["NVDA"], half, half, require_complete=True, now=after
    ) == []

    # the same 12:58 tape on a REGULAR session is truncated by three hours
    for kind, row in (("trades", _trade_row), ("quotes", _quote_row)):
        _write(settings.raw_dir, kind, "NVDA", _SESSION_ISO, [row(_et_ns(_SESSION, 12, 58))])
    assert len(backfill.plan_ticks(
        settings, ["NVDA"], _SESSION, _SESSION, require_complete=True, now=_AFTER
    )) == 2


def test_zero_row_primary_needs_empty_ok_sidecar(tmp_path: Path) -> None:
    # B5: an accidental empty primary permanently holes a liquid name-day. Under
    # content completeness a zero-row partition only counts when DECLARED empty.
    settings = _settings(tmp_path)
    for kind in ("trades", "quotes"):
        _write(settings.raw_dir, kind, "NVDA", _SESSION_ISO, [])

    # default presence path unchanged: a zero-row file is still the marker
    assert backfill.plan_ticks(settings, ["NVDA"], _SESSION, _SESSION, now=_AFTER) == []

    assert len(backfill.plan_ticks(
        settings, ["NVDA"], _SESSION, _SESSION, require_complete=True, now=_AFTER
    )) == 2

    for kind in ("trades", "quotes"):
        store.mark_empty_ok(settings.raw_dir, FEED, kind, "NVDA", _SESSION_ISO)
    assert backfill.plan_ticks(
        settings, ["NVDA"], _SESSION, _SESSION, require_complete=True, now=_AFTER
    ) == []


def test_write_partition_sidecar_lifecycle(tmp_path: Path) -> None:
    # The sidecar is opt-in on write and is cleared the moment real rows land.
    root = tmp_path / "raw"
    store.write_partition(root, FEED, "trades", "NVDA", _SESSION_ISO, [])
    assert not store.is_empty_ok(root, FEED, "trades", "NVDA", _SESSION_ISO)

    store.write_partition(root, FEED, "trades", "NVDA", _SESSION_ISO, [], empty_ok=True)
    assert store.is_empty_ok(root, FEED, "trades", "NVDA", _SESSION_ISO)
    # and it never enters a read path (scan globs *.parquet only)
    assert store.scan_kind(root, FEED, "trades", "NVDA").collect().height == 0

    store.write_partition(
        root, FEED, "trades", "NVDA", _SESSION_ISO,
        [_trade_row(_et_ns(_SESSION, 15, 58))], empty_ok=True,
    )
    assert not store.is_empty_ok(root, FEED, "trades", "NVDA", _SESSION_ISO)


def test_run_ticks_marks_empty_ok_only_when_asked(
    tmp_path: Path, _no_disk_floor
) -> None:
    settings = _settings(tmp_path)
    item = [("NVDA", _SESSION_ISO, "trades")]

    assert backfill.run_ticks(settings, item, api=_FakeApi([]), now=_AFTER) == 1
    assert not store.is_empty_ok(settings.raw_dir, FEED, "trades", "NVDA", _SESSION_ISO)

    assert backfill.run_ticks(
        settings, item, api=_FakeApi([]), now=_AFTER,
        force_overwrite=True, mark_empty_ok=True,
    ) == 1
    assert store.is_empty_ok(settings.raw_dir, FEED, "trades", "NVDA", _SESSION_ISO)
    assert backfill.partition_complete(
        settings.raw_dir, settings, "trades", "NVDA", _SESSION_ISO
    )


def test_require_complete_is_union_aware_and_rejects_corrupt(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    legacy = settings.legacy_data_dir / "raw"
    # a COMPLETE legacy copy still covers the item (union-aware planning holds)
    _write(legacy, "trades", "NVDA", _SESSION_ISO, [_trade_row(_et_ns(_SESSION, 15, 59))])
    _write(legacy, "quotes", "NVDA", _SESSION_ISO, [_quote_row(_et_ns(_SESSION, 15, 59))])
    assert backfill.plan_ticks(
        settings, ["NVDA"], _SESSION, _SESSION, require_complete=True, now=_AFTER
    ) == []

    # a CORRUPT primary shadowing it is not a completeness marker
    p = store.partition_path(settings.raw_dir, FEED, "trades", "NVDA", _SESSION_ISO)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"not a parquet file")
    assert not backfill.partition_complete(
        settings.raw_dir, settings, "trades", "NVDA", _SESSION_ISO
    )


def test_status_shape(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    primary = settings.raw_dir

    # Two non-empty trade days + one empty (zero-row) trade day + one quote day.
    _write(primary, "trades", "AMD", "2026-01-05", [_trade_row(1)])
    _write(primary, "trades", "AMD", "2026-01-06", [_trade_row(2)])
    _write(primary, "trades", "AMD", "2026-01-07", [])  # empty marker
    _write(primary, "quotes", "AMD", "2026-01-05", [_quote_row(1)])

    st = backfill.status(settings)

    assert ("AMD", "trades") in st
    assert ("AMD", "quotes") in st

    trades = st[("AMD", "trades")]
    assert trades["present"] == 3
    assert trades["empty"] == 1
    assert trades["first"] == "2026-01-05"
    assert trades["last"] == "2026-01-07"
    assert set(trades.keys()) == {"first", "last", "present", "empty", "roots"}
    assert isinstance(trades["roots"], dict)

    quotes = st[("AMD", "quotes")]
    assert quotes["present"] == 1
    assert quotes["empty"] == 0
