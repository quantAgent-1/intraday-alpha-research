"""Fill-tape loader tests (backtest/tape.py) — condition-code filtering. NO network.

The v1.4 fill tape drops every print that is not regular-way marketable evidence.
The lake stores a trade's condition CODE LIST joined with "|"
(data/alpaca_hist.fetch_trades), so the exclusion is a token-set test: a code is
dropped iff one of its tokens is in ``EXCLUDED_CONDITIONS`` (code review
2026-07-28 S1). The previous rule scanned the joined string for any excluded
CHARACTER, which also drops a multi-character code that merely contains one.

Expectations are written from the literal code lists, not read back from the
implementation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from enginev51.backtest import tape
from enginev51.config import Settings
from enginev51.data import store

FEED = "sip"
SESSION = "2026-07-16"
SYM = "NVDA"


@pytest.fixture(autouse=True)
def _isolate_legacy_lake(tmp_path: Path, monkeypatch) -> None:
    """Belt-and-braces: the loader reads across read_roots, so pin the legacy root
    to a tmp dir independently of how ``config`` resolves it (a real legacy lake
    would shadow-feed these fixtures)."""
    monkeypatch.setenv("ENGINEV51_LEGACY_DATA_DIR", str(tmp_path / "legacy"))


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "primary", legacy_data_dir=tmp_path / "legacy")


def _trade(ts: int, cond: str) -> dict:
    return {
        "ts": ts, "price": 100.0 + ts, "size": 100.0,
        "exchange": "V", "conditions": cond, "tape": "C",
    }


def _quote(ts: int) -> dict:
    return {
        "ts": ts, "bid": 99.0, "bid_size": 100.0, "bid_exchange": "V",
        "ask": 101.0, "ask_size": 100.0, "ask_exchange": "V",
        "conditions": "", "tape": "C",
    }


def _load(tmp_path: Path, trades: list[dict]):
    settings = _settings(tmp_path)
    store.write_partition(settings.raw_dir, FEED, "trades", SYM, SESSION, trades)
    store.write_partition(
        settings.raw_dir, FEED, "quotes", SYM, SESSION, [_quote(1), _quote(9)]
    )
    return tape.load_session_tape(settings, SYM, SESSION)


def test_excluded_codes_are_dropped_kept_codes_survive(tmp_path: Path) -> None:
    trades = [
        _trade(1, "@"),        # regular way -> kept
        _trade(2, "@|I"),      # odd lot: kept here, handled by min_fill_size
        _trade(3, "T"),        # extended hours -> dropped
        _trade(4, "@|Z"),      # late/out-of-sequence -> dropped
        _trade(5, "F|@"),      # intermarket sweep -> kept
        _trade(6, "M"),        # official close -> dropped
    ]
    st = _load(tmp_path, trades)
    assert st is not None
    assert st.t_ts.tolist() == [1, 2, 5]


def test_multichar_code_containing_an_excluded_letter_is_kept(tmp_path: Path) -> None:
    # S1 regression. "TW" is a single TOKEN that is not in the exclusion list; the
    # old character-wise `contains_any` dropped it because "T" (and "W") appear
    # inside it. Same for "@|4A" vs the excluded "4".
    trades = [
        _trade(1, "TW"),
        _trade(2, "@|4A"),
        _trade(3, "@|T"),   # the real single-token "T" is still excluded
    ]
    st = _load(tmp_path, trades)
    assert st is not None
    assert st.t_ts.tolist() == [1, 2]


def test_legacy_all_empty_conditions_skips_the_filter(tmp_path: Path) -> None:
    # Legacy exports carry no codes at all -> the v1.3 quote-confirmation belt
    # alone governs; nothing may be dropped for lack of evidence.
    st = _load(tmp_path, [_trade(1, ""), _trade(2, "")])
    assert st is not None
    assert st.t_ts.tolist() == [1, 2]


def test_empty_conditions_row_survives_a_coded_day(tmp_path: Path) -> None:
    # On a coded symbol-day an uncoded print carries no exclusion token, so it is
    # kept (unchanged from the substring rule — pinned so the token split, which
    # yields [""] for an empty string, cannot start matching something).
    st = _load(tmp_path, [_trade(1, ""), _trade(2, "Z")])
    assert st is not None
    assert st.t_ts.tolist() == [1]


def test_exclusion_list_is_the_registered_v14_set() -> None:
    assert set(tape.EXCLUDED_CONDITIONS) == set("ZLGU4WPCNRHXMQO569T")
    assert "I" not in tape.EXCLUDED_CONDITIONS  # odd lots are kept
    assert "@" not in tape.EXCLUDED_CONDITIONS  # regular way is kept
