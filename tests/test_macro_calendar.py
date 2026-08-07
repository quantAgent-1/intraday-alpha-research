"""QA gates for data/external/macro_calendar.parquet (built by scripts/build_macro_calendar.py).

The calendar anchors registered experiment M20; wrong dates dilute the signal, so these gates
guard date fidelity, schema, wall-clock correctness, tz round-trip, and coverage.
"""

from __future__ import annotations

import math
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CALENDAR = PROJECT_ROOT / "data" / "external" / "macro_calendar.parquet"
NVDA_BARS = PROJECT_ROOT / "data" / "raw" / "sip" / "bars1d" / "NVDA.parquet"
ET = ZoneInfo("America/New_York")

FULL_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]
PARTIAL_YEAR = 2026
PARTIAL_MONTHS = 7  # 2026 coverage runs through 2026-07-21

CLASS_SUBTYPES = {
    "fomc_stmt": {"FOMC_STMT"},
    "fomc_minutes": {"FOMC_MIN"},
    "cluster_1000": {"ISM_MFG", "ISM_SVC", "UMICH_P", "UMICH_F", "JOLTS", "CB_CONF"},
    "tsy_auction_1300": {"TSY_10Y", "TSY_30Y"},
    "pre_open_0830": {"CPI", "NFP", "PPI", "RETAIL", "GDP_ADV"},
}
CLASS_OF_SUBTYPE = {s: c for c, subs in CLASS_SUBTYPES.items() for s in subs}
CLASS_SCHED_HM = {
    "fomc_stmt": (14, 0), "fomc_minutes": (14, 0), "cluster_1000": (10, 0),
    "tsy_auction_1300": (13, 2), "pre_open_0830": (8, 30),
}

# Full-year count bounds (min, max, nominal). nominal drives the 2026 pro-rata floor.
BOUNDS = {
    "CPI": (11, 13, 12), "NFP": (11, 13, 12), "PPI": (11, 13, 12), "RETAIL": (11, 13, 12),
    "ISM_MFG": (11, 13, 12), "ISM_SVC": (11, 13, 12), "UMICH_P": (11, 13, 12),
    "UMICH_F": (11, 13, 12), "CB_CONF": (11, 13, 12), "JOLTS": (11, 13, 12),
    "GDP_ADV": (3, 5, 4), "FOMC_STMT": (7, 9, 8), "FOMC_MIN": (7, 9, 8),
    "TSY_10Y": (11, 13, 12), "TSY_30Y": (11, 13, 12),
}
# Documented real-world deviations that fall outside the standard bounds. The 2025
# appropriations lapse made BLS skip the October PPI release entirely (its data was folded
# into the Nov PPI on 2026-01-14) -> only 10 PPI releases occurred in calendar 2025.
# See bls.gov/bls/2025-lapse-revised-release-dates.htm.
KNOWN_EXCEPTIONS = {("PPI", 2025): 10}


@pytest.fixture(scope="module")
def cal() -> pd.DataFrame:
    assert CALENDAR.exists(), f"missing {CALENDAR} -- run scripts/build_macro_calendar.py"
    return pd.read_parquet(CALENDAR)


@pytest.fixture(scope="module")
def nvda_sessions() -> set:
    nv = pd.read_parquet(NVDA_BARS, columns=["ts"])
    return set(pd.to_datetime(nv["ts"], unit="ns", utc=True).dt.tz_convert(ET).dt.date)


def _session_dates(cal: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(cal["session_date"]).dt.date


# --------------------------------------------------------------------------- gate 1


def test_schema(cal: pd.DataFrame) -> None:
    assert list(cal.columns) == [
        "release_id", "class", "subtype", "session_date", "sched_ts_et", "anchor_ts_et", "source",
    ]
    assert set(cal["subtype"]) == set(CLASS_OF_SUBTYPE)
    assert set(cal["class"]) == set(CLASS_SUBTYPES)
    # every subtype maps to its correct class
    for st, cls in cal[["subtype", "class"]].drop_duplicates().itertuples(index=False):
        assert CLASS_OF_SUBTYPE[st] == cls, f"{st} mapped to {cls}"


def test_counts_full_years(cal: pd.DataFrame) -> None:
    yr = pd.to_datetime(cal["session_date"]).dt.year
    for subtype, (lo, hi, _) in BOUNDS.items():
        for year in FULL_YEARS:
            n = int(((cal["subtype"] == subtype) & (yr == year)).sum())
            if (subtype, year) in KNOWN_EXCEPTIONS:
                assert n == KNOWN_EXCEPTIONS[(subtype, year)], (
                    f"{subtype} {year}: expected documented {KNOWN_EXCEPTIONS[(subtype, year)]}, got {n}"
                )
            else:
                assert lo <= n <= hi, f"{subtype} {year}: {n} outside [{lo},{hi}]"


def test_counts_partial_2026(cal: pd.DataFrame) -> None:
    yr = pd.to_datetime(cal["session_date"]).dt.year
    for subtype, (_, _, nominal) in BOUNDS.items():
        n = int(((cal["subtype"] == subtype) & (yr == PARTIAL_YEAR)).sum())
        floor = max(0, math.floor(PARTIAL_MONTHS * nominal / 12) - 2)
        assert n >= floor, f"{subtype} 2026: {n} < pro-rata floor {floor}"


# --------------------------------------------------------------------------- gate 2


def test_every_session_is_a_trading_day(cal: pd.DataFrame, nvda_sessions: set) -> None:
    bad = [
        (rid, str(d))
        for rid, d in zip(cal["release_id"], _session_dates(cal), strict=True)
        if d not in nvda_sessions
    ]
    assert not bad, f"non-trading session_dates present (should be dropped): {bad[:10]}"


def test_known_market_holiday_releases_are_dropped(cal: pd.DataFrame, nvda_sessions: set) -> None:
    # Good Friday 08:30 prints (market closed) must be absent, and really are non-sessions.
    for rid, iso in [("CPI-2020-04-10", "2020-04-10"), ("NFP-2021-04-02", "2021-04-02"),
                     ("NFP-2023-04-07", "2023-04-07"), ("NFP-2026-04-03", "2026-04-03")]:
        assert rid not in set(cal["release_id"]), f"{rid} should have been dropped"
        assert pd.Timestamp(iso).date() not in nvda_sessions, f"{iso} unexpectedly a trading day"


# --------------------------------------------------------------------------- gate 3


def test_uniqueness(cal: pd.DataFrame) -> None:
    assert cal["release_id"].is_unique, "release_id not unique"
    assert not cal.duplicated(["subtype", "session_date"]).any(), "(subtype, session_date) not unique"
    # release_id is exactly subtype-<session_date>
    expect = cal["subtype"] + "-" + _session_dates(cal).astype(str)
    assert (cal["release_id"] == expect).all(), "release_id != '<subtype>-<session_date>'"


# --------------------------------------------------------------------------- gate 4


def test_wall_clock(cal: pd.DataFrame) -> None:
    sched = cal["sched_ts_et"]
    anchor = cal["anchor_ts_et"]
    for cls, (hh, mm) in CLASS_SCHED_HM.items():
        m = cal["class"] == cls
        assert (sched[m].dt.hour == hh).all() and (sched[m].dt.minute == mm).all(), f"{cls} sched time"
    # sched and anchor share the session date
    assert (sched.dt.date == anchor.dt.date).all()
    assert (sched.dt.date == _session_dates(cal)).all()
    # anchor == sched for all classes except pre_open_0830 -> 09:30
    pre = cal["class"] == "pre_open_0830"
    assert (anchor[~pre] == sched[~pre]).all(), "anchor != sched off pre_open"
    assert (anchor[pre].dt.hour == 9).all() and (anchor[pre].dt.minute == 30).all(), "pre-open anchor != 09:30"


# --------------------------------------------------------------------------- gate 5


def test_tz_awareness_and_roundtrip(cal: pd.DataFrame) -> None:
    for col in ("sched_ts_et", "anchor_ts_et"):
        assert str(cal[col].dt.tz) == "America/New_York", f"{col} tz != America/New_York"
    # DST is honoured (a winter 10:00 is UTC-5, a summer 10:00 is UTC-4)
    cb = cal[cal["subtype"] == "CB_CONF"].set_index(pd.to_datetime(cal[cal["subtype"] == "CB_CONF"]["session_date"]))
    jan = cb[cb.index.month == 1]["sched_ts_et"].iloc[0]
    jul = cb[cb.index.month == 7]["sched_ts_et"].iloc[0]
    assert jan.utcoffset().total_seconds() == -5 * 3600
    assert jul.utcoffset().total_seconds() == -4 * 3600
    # every stored instant is exactly the ET wall-clock it claims
    assert (cal["sched_ts_et"].dt.tz_convert(ET).dt.hour == cal["sched_ts_et"].dt.hour).all()


# --------------------------------------------------------------------------- gate 6


def test_coverage_all_classes_all_years(cal: pd.DataFrame) -> None:
    yr = pd.to_datetime(cal["session_date"]).dt.year
    years = FULL_YEARS + [PARTIAL_YEAR]
    for cls in CLASS_SUBTYPES:
        present = set(yr[cal["class"] == cls].unique())
        missing = set(years) - present
        assert not missing, f"class {cls} missing years {sorted(missing)}"
    # and coverage window itself
    sd = _session_dates(cal)
    assert min(sd) >= pd.Timestamp("2020-01-01").date()
    assert max(sd) <= pd.Timestamp("2026-07-21").date()


def test_source_is_non_empty(cal: pd.DataFrame) -> None:
    assert cal["source"].str.len().gt(0).all(), "empty source string"
    # the only rule-reconstructed rows are Conference Board Jan-Nov (last-Tuesday schedule)
    recon = cal[cal["source"].str.startswith("RECONSTRUCTED-VERIFY")]
    assert set(recon["subtype"]) == {"CB_CONF"}, "unexpected reconstructed subtypes"
    assert (pd.to_datetime(recon["session_date"]).dt.month != 12).all(), "December CB should be actual"
