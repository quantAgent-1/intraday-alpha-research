from pathlib import Path

from enginev51.data import store


def test_bars_roundtrip(tmp_path: Path) -> None:
    rows = [
        {"ts": 2, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 100.0,
         "trade_count": 7, "vwap": 1.2},
        {"ts": 1, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0,
         "trade_count": 1, "vwap": 1.0},
    ]
    store.write_partition(tmp_path, "sip", "bars1m", "tsla", "2026-01", rows)
    assert store.partition_exists(tmp_path, "sip", "bars1m", "TSLA", "2026-01")
    df = store.load_bars(tmp_path, "sip", "TSLA")
    assert df.height == 2
    assert df["ts"].to_list() == [1, 2]  # sorted on write


def test_empty_partition_marks_done(tmp_path: Path) -> None:
    store.write_partition(tmp_path, "iex", "trades", "NVDA", "2026-01-01", [])
    assert store.partition_exists(tmp_path, "iex", "trades", "NVDA", "2026-01-01")
    df = store.scan_kind(tmp_path, "iex", "trades", "NVDA").collect()
    assert df.height == 0
    assert set(df.columns) == set(store.TRADES_SCHEMA)


def test_load_bars_range_filter(tmp_path: Path) -> None:
    rows = [
        {"ts": t, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0,
         "trade_count": 1, "vwap": 1.0}
        for t in (10, 20, 30)
    ]
    store.write_partition(tmp_path, "sip", "bars1m", "AMD", "2026-02", rows)
    df = store.load_bars(tmp_path, "sip", "AMD", start_ns=15, end_ns=30)
    assert df["ts"].to_list() == [20]
