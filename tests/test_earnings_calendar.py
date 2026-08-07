"""QA gates for data/external/earnings_calendar.parquet (scripts/build_earnings_calendar.py).

The calendar anchors registered experiment M21; a wrong day-0 shifts the whole drift window,
so these gates guard schema, per-name/per-year coverage, the BMO/AMC -> session mapping,
uniqueness, the acceptance window, six spot-pinned famous events, and universe coverage.
"""

from __future__ import annotations

import bisect
import importlib.util
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CALENDAR = PROJECT_ROOT / "data" / "external" / "earnings_calendar.parquet"
BUILD = PROJECT_ROOT / "scripts" / "build_earnings_calendar.py"
ET = ZoneInfo("America/New_York")

WINDOW_LO = pd.Timestamp("2018-01-01").date()
WINDOW_HI = pd.Timestamp("2026-07-21").date()
FULL_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

SEMIS = ["NVDA", "AMD", "MU", "AVGO", "QCOM", "TXN", "INTC", "AMAT", "LRCX", "KLAC",
         "MRVL", "ON", "MCHP", "ADI", "NXPI", "TSM", "ASML", "SMCI"]
MEGACAP = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NFLX"]
CORE_25 = SEMIS + MEGACAP                       # the frozen 25 (gate-6 population)
DROPPED = {"TSM"}                               # 6-K, not machine-separable (reason logged)
# ARM listed at its Sep-2023 IPO -> 2023 is a partial (H2) year, exempt from the 3-5 band.
FIRST_FULL_YEAR = {"ARM": 2024}

# Six famous events pinned as literal assertions (a subset of the validated 20): event_id,
# accept ET date, timing, day0 session. Each was cross-checked against company IR / press.
PINNED = [
    ("NVDA-2023-05-25", "2023-05-24", "AMC", "2023-05-25"),  # Q1 FY2024 blowout, +26% AH
    ("META-2022-02-03", "2022-02-02", "AMC", "2022-02-03"),  # Q4 2021, -26% next day
    ("NFLX-2022-04-20", "2022-04-19", "AMC", "2022-04-20"),  # Q1 2022 subscriber loss
    ("ADI-2024-02-21", "2024-02-21", "BMO", "2024-02-21"),   # 07:00 ET pre-open release
    ("ARM-2024-02-08", "2024-02-07", "AMC", "2024-02-08"),   # first big beat, +48%
    ("SMCI-2024-08-07", "2024-08-06", "AMC", "2024-08-07"),  # Q4 FY2024, 10:1 split
]


@pytest.fixture(scope="module")
def cal() -> pd.DataFrame:
    assert CALENDAR.exists(), f"missing {CALENDAR} -- run scripts/build_earnings_calendar.py"
    return pd.read_parquet(CALENDAR)


@pytest.fixture(scope="module")
def build_mod():
    spec = importlib.util.spec_from_file_location("build_earnings_calendar", BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def sessions(build_mod) -> list:
    return build_mod.load_sessions()


def _accept_date(cal: pd.DataFrame) -> pd.Series:
    return cal["accept_ts_et"].dt.tz_convert(ET).dt.date


def _day0(cal: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(cal["day0_session"]).dt.date


# --------------------------------------------------------------------------- schema


def test_schema(cal: pd.DataFrame) -> None:
    assert list(cal.columns) == [
        "event_id", "symbol", "fiscal_note", "accept_ts_et", "timing", "day0_session", "source",
    ]
    assert str(cal["accept_ts_et"].dt.tz) == "America/New_York"
    assert cal["source"].str.len().gt(0).all(), "empty source string"
    # fiscal_note, where present, is 'Q<n> FY<yyyy>'
    fn = cal.loc[cal["fiscal_note"] != "", "fiscal_note"]
    assert fn.str.match(r"^Q[1-4] FY20[12]\d$").all(), "malformed fiscal_note"


# --------------------------------------------------------------------------- gate 1


def test_counts_per_symbol_per_full_year(cal: pd.DataFrame) -> None:
    """3-5 events per full year for every year each name is listed (ARM from 2024)."""
    yr = _day0(cal).map(lambda d: d.year)
    for sym in sorted(set(cal["symbol"])):
        first = FIRST_FULL_YEAR.get(sym, FULL_YEARS[0])
        for year in [y for y in FULL_YEARS if y >= first]:
            n = int(((cal["symbol"] == sym) & (yr == year)).sum())
            assert 3 <= n <= 5, f"{sym} {year}: {n} outside [3,5]"


def test_partial_2026_present(cal: pd.DataFrame) -> None:
    yr = _day0(cal).map(lambda d: d.year)
    for sym in sorted(set(cal["symbol"])):
        assert int(((cal["symbol"] == sym) & (yr == 2026)).sum()) >= 1, f"{sym} missing 2026"


# --------------------------------------------------------------------------- gate 2


def test_day0_is_a_real_session(cal: pd.DataFrame, sessions: list) -> None:
    sset = set(sessions)
    bad = [eid for eid, d in zip(cal["event_id"], _day0(cal), strict=True) if d not in sset]
    assert not bad, f"day0_session not a trading session: {bad[:10]}"


def test_bmo_amc_session_mapping(cal: pd.DataFrame, sessions: list) -> None:
    """BMO -> the acceptance-date session (first session on/after accept date);
    AMC -> the strictly-next session (first session strictly after accept date)."""
    errs = []
    for eid, ad, timing, d0 in zip(
        cal["event_id"], _accept_date(cal), cal["timing"], _day0(cal), strict=True
    ):
        if timing == "AMC":
            expect = sessions[bisect.bisect_right(sessions, ad)]
        else:
            expect = sessions[bisect.bisect_left(sessions, ad)]
        if d0 != expect:
            errs.append((eid, timing, str(ad), str(d0), str(expect)))
    assert not errs, f"day0 != expected session mapping: {errs[:10]}"


def test_timing_matches_accept_hour(cal: pd.DataFrame) -> None:
    hr = cal["accept_ts_et"].dt.tz_convert(ET).dt.hour
    assert (cal.loc[hr >= 16, "timing"] == "AMC").all(), "accept>=16:00 must be AMC"
    assert (cal.loc[hr < 16, "timing"] == "BMO").all(), "accept<16:00 must be BMO"


# --------------------------------------------------------------------------- gate 3


def test_uniqueness_and_event_id(cal: pd.DataFrame) -> None:
    assert cal["event_id"].is_unique, "event_id not unique"
    assert not cal.duplicated(["symbol", "day0_session"]).any(), "(symbol, day0_session) not unique"
    expect = cal["symbol"] + "-" + _day0(cal).astype(str)
    assert (cal["event_id"] == expect).all(), "event_id != '<symbol>-<day0_session>'"


# --------------------------------------------------------------------------- gate 4


def test_accept_window_and_timing_domain(cal: pd.DataFrame) -> None:
    ad = _accept_date(cal)
    assert (ad >= WINDOW_LO).all() and (ad <= WINDOW_HI).all(), "accept date outside window"
    assert set(cal["timing"]) <= {"BMO", "AMC"}, "timing not in {BMO, AMC}"
    # DST honoured: a winter accept is UTC-5, a summer accept UTC-4
    off = cal["accept_ts_et"].dt.tz_convert(ET)
    win = off[off.dt.month == 1].iloc[0]
    summer = off[off.dt.month == 7].iloc[0]
    assert win.utcoffset().total_seconds() == -5 * 3600
    assert summer.utcoffset().total_seconds() == -4 * 3600


# --------------------------------------------------------------------------- gate 5


def test_pinned_famous_events(cal: pd.DataFrame) -> None:
    by_id = cal.set_index("event_id")
    for eid, accept_date, timing, day0 in PINNED:
        assert eid in by_id.index, f"missing pinned event {eid}"
        row = by_id.loc[eid]
        assert row["timing"] == timing, f"{eid} timing {row['timing']} != {timing}"
        assert str(pd.Timestamp(row["day0_session"]).date()) == day0, f"{eid} day0 mismatch"
        assert str(row["accept_ts_et"].tz_convert(ET).date()) == accept_date, f"{eid} accept mismatch"


# --------------------------------------------------------------------------- gate 6


def test_universe_coverage(cal: pd.DataFrame) -> None:
    present = set(cal["symbol"])
    # TSM dropped-with-reason; every other core name present
    assert DROPPED.isdisjoint(present), f"dropped name present: {DROPPED & present}"
    # >= 22 of the 25 core names present with >= 25 events each
    counts = cal["symbol"].value_counts()
    strong = [s for s in CORE_25 if counts.get(s, 0) >= 25]
    assert len(strong) >= 22, f"only {len(strong)} core names with >=25 events: {sorted(strong)}"
    # ARM (the +1) is present from its 2023 IPO
    assert "ARM" in present, "ARM missing"
    assert counts.get("ARM", 0) >= 8, "ARM under-covered since 2023 IPO"


def test_source_provenance(cal: pd.DataFrame) -> None:
    assert cal["source"].str.startswith("SEC EDGAR").all(), "non-SEC source present"
    # ASML/ARM are 6-K filers; NXP is the documented 8-K+6-K hybrid
    assert cal.loc[cal["symbol"] == "ASML", "source"].str.contains("6-K").all()
    assert cal.loc[cal["symbol"] == "ARM", "source"].str.contains("6-K").all()
    assert cal.loc[cal["symbol"] == "NXPI", "source"].str.contains("6-K").all()
