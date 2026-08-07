"""Build the historical US macro-release calendar (data/external/macro_calendar.parquet).

M20 anchor dataset. Scheduled release instants for the macro events the engine gates on,
2020-01-01 .. 2026-07-21, one row per (subtype, session_date). Times are wall-clock ET.

Deterministic / offline: the release dates below are EMBEDDED literal tables (verified from
the authoritative sources listed per class, fetched 2026-07-22). The build only reads those
tables + the NVDA daily-bar session index (to drop releases that land on a closed market).
No network access at build time. `--refresh` prints the fetch/verification methodology used
to produce the tables (the one-off fetch scripts live in the research scratchpad, not here).

Classes / subtypes / scheduled time-of-day (ET):
  fomc_stmt          FOMC_STMT                                   14:00
  fomc_minutes       FOMC_MIN                                    14:00
  cluster_1000       ISM_MFG ISM_SVC UMICH_P UMICH_F JOLTS CB_CONF  10:00
  tsy_auction_1300   TSY_10Y TSY_30Y                             13:02  (results ~13:01-13:03 after the 13:00 bid close)
  pre_open_0830      CPI NFP PPI RETAIL GDP_ADV                  08:30
anchor_ts_et == sched_ts_et for every class EXCEPT pre_open_0830, whose anchor is the same
date 09:30 ET (the cash open the pre-open print is traded into).

Per-class provenance (all fetched 2026-07-22):
  FOMC_STMT / FOMC_MIN  federalreserve.gov/monetarypolicy/fomccalendars.htm (statements =
      meeting end date; minutes = the listed "(Released ...)" date) + fomchistorical2020.htm
      for 2020. FOMC_STMT excludes the cancelled Mar-2020 meeting and the two 2020 emergency
      actions (not 14:00 / Sunday). FOMC_MIN 2020-04-08 is the emergency Mar-15 meeting's
      minutes (a genuine 14:00 trading-day release).
  ISM_MFG / ISM_SVC     ismworld.org ROB report calendar via web.archive.org (first / third
      business day, 10:00; captures ISM's holiday shifts, e.g. every January +1 business day).
  UMICH_P / UMICH_F     University of Michigan Surveys of Consumers annual release-date PDFs
      (data.sca.isr.umich.edu docids 65450/68030/70659/73945/76841/79628 for 2021-2026) plus
      the cumulative "Historical Prelim/Final Release Dates" doc (docid 39424) for 2020, via
      web.archive.org.
  JOLTS / CPI / NFP / PPI  bls.gov/bls/news-release/<rel>.htm archive listings via
      web.archive.org (each archived release filename <rel>_MMDDYYYY.htm IS its release date;
      unioned across yearly snapshots). Sep-Dec 2025 gaps are the real 2025 appropriations
      lapse (bls.gov/bls/2025-lapse-revised-release-dates.htm): BLS skipped the Oct PPI/NFP
      and one CPI/JOLTS release.
  CB_CONF               Conference Board (conference-board.org/topics/consumer-confidence).
      December dates are the verified pre-holiday actuals; Jan-Nov follow the Conference
      Board's documented last-Tuesday-of-month @10:00 schedule (rule, verified against 18
      sampled actual releases with zero mismatches) -> source tagged RECONSTRUCTED-VERIFY.
  TSY_10Y / TSY_30Y     treasurydirect.gov TA_WS/securities/search (originalSecurityTerm
      10-Year Note / 30-Year Bond incl. reopenings; auctionDate = session_date).
  RETAIL                census.gov Advance Monthly Retail (MARTS): MARTSreleasedates.xls for
      2020-2025 + retail/release_schedule.html for the 2025-2026 shutdown-shifted dates.
  GDP_ADV               bea.gov GDP advance/first estimate, release dates confirmed from each
      release's embargo line. Q3-2025 = the Dec-23-2025 "initial estimate" that replaced the
      shutdown-cancelled advance estimate.

Releases that fall on a closed market (BLS still prints 08:30 on Good Friday) are DROPPED,
not shifted, and logged (see main()). Run: `uv run python scripts/build_macro_calendar.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ET = ZoneInfo("America/New_York")
NVDA_BARS = PROJECT_ROOT / "data" / "raw" / "sip" / "bars1d" / "NVDA.parquet"
OUT_PARQUET = PROJECT_ROOT / "data" / "external" / "macro_calendar.parquet"

COVERAGE_START = pd.Timestamp("2020-01-01").date()
COVERAGE_END = pd.Timestamp("2026-07-21").date()

# --------------------------------------------------------------------------- class config

CLASS_OF_SUBTYPE = {
    "FOMC_STMT": "fomc_stmt",
    "FOMC_MIN": "fomc_minutes",
    "ISM_MFG": "cluster_1000", "ISM_SVC": "cluster_1000",
    "UMICH_P": "cluster_1000", "UMICH_F": "cluster_1000",
    "JOLTS": "cluster_1000", "CB_CONF": "cluster_1000",
    "TSY_10Y": "tsy_auction_1300", "TSY_30Y": "tsy_auction_1300",
    "CPI": "pre_open_0830", "NFP": "pre_open_0830", "PPI": "pre_open_0830",
    "RETAIL": "pre_open_0830", "GDP_ADV": "pre_open_0830",
}
SCHED_HM = {  # scheduled release wall-clock time (ET) per class
    "fomc_stmt": (14, 0), "fomc_minutes": (14, 0), "cluster_1000": (10, 0),
    "tsy_auction_1300": (13, 2), "pre_open_0830": (8, 30),
}
_FETCHED = "2026-07-22"
SOURCE = {
    "FOMC_STMT": f"federalreserve.gov/fomccalendars+fomchistorical2020 ({_FETCHED})",
    "FOMC_MIN": f"federalreserve.gov/fomccalendars+fomchistorical2020 ({_FETCHED})",
    "ISM_MFG": f"ismworld.org ROB report calendar via web.archive.org ({_FETCHED})",
    "ISM_SVC": f"ismworld.org ROB report calendar via web.archive.org ({_FETCHED})",
    "UMICH_P": f"sca.isr.umich.edu release-date docs (+historical via web.archive.org) ({_FETCHED})",
    "UMICH_F": f"sca.isr.umich.edu release-date docs (+historical via web.archive.org) ({_FETCHED})",
    "JOLTS": f"bls.gov/bls/news-release archives via web.archive.org ({_FETCHED})",
    "TSY_10Y": f"treasurydirect.gov TA_WS/securities/search ({_FETCHED})",
    "TSY_30Y": f"treasurydirect.gov TA_WS/securities/search ({_FETCHED})",
    "CPI": f"bls.gov/bls/news-release archives via web.archive.org ({_FETCHED})",
    "NFP": f"bls.gov/bls/news-release archives via web.archive.org ({_FETCHED})",
    "PPI": f"bls.gov/bls/news-release archives via web.archive.org ({_FETCHED})",
    "RETAIL": f"census.gov MARTSreleasedates.xls + retail/release_schedule.html ({_FETCHED})",
    "GDP_ADV": f"bea.gov GDP advance-estimate embargo lines ({_FETCHED})",
}
CB_DEC_SOURCE = f"conference-board.org consumer-confidence press releases ({_FETCHED})"
CB_RULE_SOURCE = (
    "RECONSTRUCTED-VERIFY: Conference Board last-Tuesday-of-month @10:00 "
    "(documented schedule; verified vs 18 sampled releases, 0 mismatches)"
)


def source_for(subtype: str, session_date) -> str:
    """CB_CONF December dates are verified actuals; its Jan-Nov dates are the last-Tuesday
    schedule rule (tagged RECONSTRUCTED-VERIFY). Everything else has a single fetched source."""
    if subtype == "CB_CONF":
        return CB_DEC_SOURCE if session_date.month == 12 else CB_RULE_SOURCE
    return SOURCE[subtype]


# --------------------------------------------------------------------------- embedded data
# Verified release dates, one list per subtype (ISO YYYY-MM-DD). See module docstring for
# per-class provenance + fetch date. Regenerate via `--refresh` methodology, not at build.

RELEASE_DATES: dict[str, list[str]] = {
    # FOMC_STMT: 51 dates
    "FOMC_STMT": [
        "2020-01-29", "2020-04-29", "2020-06-10", "2020-07-29", "2020-09-16", "2020-11-05",
        "2020-12-16", "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28",
        "2021-09-22", "2021-11-03", "2021-12-15", "2022-01-26", "2022-03-16", "2022-05-04",
        "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14", "2023-02-01",
        "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01",
        "2023-12-13", "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31",
        "2024-09-18", "2024-11-07", "2024-12-18", "2025-01-29", "2025-03-19", "2025-05-07",
        "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10", "2026-01-28",
        "2026-03-18", "2026-04-29", "2026-06-17",
    ],
    # FOMC_MIN: 52 dates
    "FOMC_MIN": [
        "2020-02-19", "2020-04-08", "2020-05-20", "2020-07-01", "2020-08-19", "2020-10-07",
        "2020-11-25", "2021-01-06", "2021-02-17", "2021-04-07", "2021-05-19", "2021-07-07",
        "2021-08-18", "2021-10-13", "2021-11-24", "2022-01-05", "2022-02-16", "2022-04-06",
        "2022-05-25", "2022-07-06", "2022-08-17", "2022-10-12", "2022-11-23", "2023-01-04",
        "2023-02-22", "2023-04-12", "2023-05-24", "2023-07-05", "2023-08-16", "2023-10-11",
        "2023-11-21", "2024-01-03", "2024-02-21", "2024-04-10", "2024-05-22", "2024-07-03",
        "2024-08-21", "2024-10-09", "2024-11-26", "2025-01-08", "2025-02-19", "2025-04-09",
        "2025-05-28", "2025-07-09", "2025-08-20", "2025-10-08", "2025-11-19", "2025-12-30",
        "2026-02-18", "2026-04-08", "2026-05-20", "2026-07-08",
    ],
    # ISM_MFG: 79 dates
    "ISM_MFG": [
        "2020-01-03", "2020-02-03", "2020-03-02", "2020-04-01", "2020-05-01", "2020-06-01",
        "2020-07-01", "2020-08-03", "2020-09-01", "2020-10-01", "2020-11-02", "2020-12-01",
        "2021-01-05", "2021-02-01", "2021-03-01", "2021-04-01", "2021-05-03", "2021-06-01",
        "2021-07-01", "2021-08-02", "2021-09-01", "2021-10-01", "2021-11-01", "2021-12-01",
        "2022-01-04", "2022-02-01", "2022-03-01", "2022-04-01", "2022-05-02", "2022-06-01",
        "2022-07-01", "2022-08-01", "2022-09-01", "2022-10-03", "2022-11-01", "2022-12-01",
        "2023-01-04", "2023-02-01", "2023-03-01", "2023-04-03", "2023-05-01", "2023-06-01",
        "2023-07-03", "2023-08-01", "2023-09-01", "2023-10-02", "2023-11-01", "2023-12-01",
        "2024-01-03", "2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01", "2024-06-03",
        "2024-07-01", "2024-08-01", "2024-09-03", "2024-10-01", "2024-11-01", "2024-12-02",
        "2025-01-03", "2025-02-03", "2025-03-03", "2025-04-01", "2025-05-01", "2025-06-02",
        "2025-07-01", "2025-08-01", "2025-09-02", "2025-10-01", "2025-11-03", "2025-12-01",
        "2026-01-05", "2026-02-02", "2026-03-02", "2026-04-01", "2026-05-01", "2026-06-01",
        "2026-07-01",
    ],
    # ISM_SVC: 79 dates
    "ISM_SVC": [
        "2020-01-07", "2020-02-05", "2020-03-04", "2020-04-03", "2020-05-05", "2020-06-03",
        "2020-07-06", "2020-08-05", "2020-09-03", "2020-10-05", "2020-11-04", "2020-12-03",
        "2021-01-07", "2021-02-03", "2021-03-03", "2021-04-05", "2021-05-05", "2021-06-03",
        "2021-07-06", "2021-08-04", "2021-09-03", "2021-10-05", "2021-11-03", "2021-12-03",
        "2022-01-06", "2022-02-03", "2022-03-03", "2022-04-05", "2022-05-04", "2022-06-03",
        "2022-07-06", "2022-08-03", "2022-09-06", "2022-10-05", "2022-11-03", "2022-12-05",
        "2023-01-06", "2023-02-03", "2023-03-03", "2023-04-05", "2023-05-03", "2023-06-05",
        "2023-07-06", "2023-08-03", "2023-09-06", "2023-10-04", "2023-11-03", "2023-12-05",
        "2024-01-05", "2024-02-05", "2024-03-05", "2024-04-03", "2024-05-03", "2024-06-05",
        "2024-07-03", "2024-08-05", "2024-09-05", "2024-10-03", "2024-11-05", "2024-12-04",
        "2025-01-07", "2025-02-05", "2025-03-05", "2025-04-03", "2025-05-05", "2025-06-04",
        "2025-07-03", "2025-08-05", "2025-09-04", "2025-10-03", "2025-11-05", "2025-12-03",
        "2026-01-07", "2026-02-04", "2026-03-04", "2026-04-06", "2026-05-05", "2026-06-03",
        "2026-07-06",
    ],
    # UMICH_P: 79 dates
    "UMICH_P": [
        "2020-01-17", "2020-02-14", "2020-03-13", "2020-04-09", "2020-05-15", "2020-06-12",
        "2020-07-17", "2020-08-14", "2020-09-18", "2020-10-16", "2020-11-13", "2020-12-11",
        "2021-01-15", "2021-02-12", "2021-03-12", "2021-04-16", "2021-05-14", "2021-06-11",
        "2021-07-16", "2021-08-13", "2021-09-17", "2021-10-15", "2021-11-12", "2021-12-10",
        "2022-01-14", "2022-02-11", "2022-03-11", "2022-04-14", "2022-05-13", "2022-06-10",
        "2022-07-15", "2022-08-12", "2022-09-16", "2022-10-14", "2022-11-11", "2022-12-09",
        "2023-01-13", "2023-02-10", "2023-03-17", "2023-04-14", "2023-05-12", "2023-06-16",
        "2023-07-14", "2023-08-11", "2023-09-15", "2023-10-13", "2023-11-10", "2023-12-08",
        "2024-01-19", "2024-02-16", "2024-03-15", "2024-04-12", "2024-05-10", "2024-06-14",
        "2024-07-12", "2024-08-16", "2024-09-13", "2024-10-11", "2024-11-08", "2024-12-06",
        "2025-01-10", "2025-02-07", "2025-03-14", "2025-04-11", "2025-05-16", "2025-06-13",
        "2025-07-18", "2025-08-15", "2025-09-12", "2025-10-10", "2025-11-07", "2025-12-05",
        "2026-01-09", "2026-02-06", "2026-03-13", "2026-04-10", "2026-05-08", "2026-06-12",
        "2026-07-17",
    ],
    # UMICH_F: 78 dates
    "UMICH_F": [
        "2020-01-31", "2020-02-28", "2020-03-27", "2020-04-24", "2020-05-29", "2020-06-26",
        "2020-07-31", "2020-08-28", "2020-10-02", "2020-10-30", "2020-11-25", "2020-12-23",
        "2021-01-29", "2021-02-26", "2021-03-26", "2021-04-30", "2021-05-28", "2021-06-25",
        "2021-07-30", "2021-08-27", "2021-10-01", "2021-10-29", "2021-11-24", "2021-12-23",
        "2022-01-28", "2022-02-25", "2022-03-25", "2022-04-29", "2022-05-27", "2022-06-24",
        "2022-07-29", "2022-08-26", "2022-09-30", "2022-10-28", "2022-11-23", "2022-12-23",
        "2023-01-27", "2023-02-24", "2023-03-31", "2023-04-28", "2023-05-26", "2023-06-30",
        "2023-07-28", "2023-08-25", "2023-09-29", "2023-10-27", "2023-11-22", "2023-12-22",
        "2024-02-02", "2024-03-01", "2024-03-28", "2024-04-26", "2024-05-24", "2024-06-28",
        "2024-07-26", "2024-08-30", "2024-09-27", "2024-10-25", "2024-11-22", "2024-12-20",
        "2025-01-24", "2025-02-21", "2025-03-28", "2025-04-25", "2025-05-30", "2025-06-27",
        "2025-08-01", "2025-08-29", "2025-09-26", "2025-10-24", "2025-11-21", "2025-12-19",
        "2026-01-23", "2026-02-20", "2026-03-27", "2026-04-24", "2026-05-22", "2026-06-26",
    ],
    # JOLTS: 77 dates
    "JOLTS": [
        "2020-01-17", "2020-02-11", "2020-03-17", "2020-04-07", "2020-05-15", "2020-06-09",
        "2020-07-07", "2020-08-10", "2020-09-09", "2020-10-06", "2020-11-10", "2020-12-09",
        "2021-01-12", "2021-02-09", "2021-03-11", "2021-04-06", "2021-05-11", "2021-06-08",
        "2021-07-07", "2021-08-09", "2021-09-08", "2021-10-12", "2021-11-12", "2021-12-08",
        "2022-01-04", "2022-02-01", "2022-03-09", "2022-03-29", "2022-05-03", "2022-06-01",
        "2022-07-06", "2022-08-02", "2022-08-30", "2022-10-04", "2022-11-01", "2022-11-30",
        "2023-01-04", "2023-02-01", "2023-03-08", "2023-04-04", "2023-05-02", "2023-05-31",
        "2023-07-06", "2023-08-01", "2023-08-29", "2023-10-03", "2023-11-01", "2023-12-05",
        "2024-01-03", "2024-01-30", "2024-03-06", "2024-04-02", "2024-05-01", "2024-06-04",
        "2024-07-02", "2024-07-30", "2024-09-04", "2024-10-01", "2024-10-29", "2024-12-03",
        "2025-01-07", "2025-02-04", "2025-03-11", "2025-04-01", "2025-04-29", "2025-06-03",
        "2025-07-01", "2025-07-29", "2025-09-03", "2025-09-30", "2025-12-09", "2026-01-07",
        "2026-02-05", "2026-03-13", "2026-03-31", "2026-05-05", "2026-06-02",
    ],
    # CB_CONF: 78 dates (December = verified actuals; Jan-Nov = last-Tuesday rule)
    "CB_CONF": [
        "2020-01-28", "2020-02-25", "2020-03-31", "2020-04-28", "2020-05-26", "2020-06-30",
        "2020-07-28", "2020-08-25", "2020-09-29", "2020-10-27", "2020-11-24", "2020-12-22",
        "2021-01-26", "2021-02-23", "2021-03-30", "2021-04-27", "2021-05-25", "2021-06-29",
        "2021-07-27", "2021-08-31", "2021-09-28", "2021-10-26", "2021-11-30", "2021-12-22",
        "2022-01-25", "2022-02-22", "2022-03-29", "2022-04-26", "2022-05-31", "2022-06-28",
        "2022-07-26", "2022-08-30", "2022-09-27", "2022-10-25", "2022-11-29", "2022-12-21",
        "2023-01-31", "2023-02-28", "2023-03-28", "2023-04-25", "2023-05-30", "2023-06-27",
        "2023-07-25", "2023-08-29", "2023-09-26", "2023-10-31", "2023-11-28", "2023-12-20",
        "2024-01-30", "2024-02-27", "2024-03-26", "2024-04-30", "2024-05-28", "2024-06-25",
        "2024-07-30", "2024-08-27", "2024-09-24", "2024-10-29", "2024-11-26", "2024-12-23",
        "2025-01-28", "2025-02-25", "2025-03-25", "2025-04-29", "2025-05-27", "2025-06-24",
        "2025-07-29", "2025-08-26", "2025-09-30", "2025-10-28", "2025-11-25", "2025-12-23",
        "2026-01-27", "2026-02-24", "2026-03-31", "2026-04-28", "2026-05-26", "2026-06-30",
    ],
    # TSY_10Y: 79 dates
    "TSY_10Y": [
        "2020-01-08", "2020-02-12", "2020-03-11", "2020-04-07", "2020-05-12", "2020-06-09",
        "2020-07-08", "2020-08-12", "2020-09-09", "2020-10-07", "2020-11-10", "2020-12-09",
        "2021-01-12", "2021-02-10", "2021-03-10", "2021-04-12", "2021-05-12", "2021-06-09",
        "2021-07-12", "2021-08-11", "2021-09-08", "2021-10-12", "2021-11-09", "2021-12-08",
        "2022-01-12", "2022-02-09", "2022-03-09", "2022-04-12", "2022-05-11", "2022-06-08",
        "2022-07-12", "2022-08-10", "2022-09-12", "2022-10-12", "2022-11-09", "2022-12-12",
        "2023-01-11", "2023-02-08", "2023-03-08", "2023-04-12", "2023-05-10", "2023-06-12",
        "2023-07-12", "2023-08-09", "2023-09-12", "2023-10-11", "2023-11-08", "2023-12-11",
        "2024-01-10", "2024-02-07", "2024-03-12", "2024-04-10", "2024-05-08", "2024-06-11",
        "2024-07-10", "2024-08-07", "2024-09-11", "2024-10-09", "2024-11-05", "2024-12-11",
        "2025-01-07", "2025-02-12", "2025-03-12", "2025-04-09", "2025-05-06", "2025-06-11",
        "2025-07-09", "2025-08-06", "2025-09-10", "2025-10-08", "2025-11-12", "2025-12-09",
        "2026-01-12", "2026-02-11", "2026-03-11", "2026-04-08", "2026-05-12", "2026-06-10",
        "2026-07-08",
    ],
    # TSY_30Y: 79 dates
    "TSY_30Y": [
        "2020-01-09", "2020-02-13", "2020-03-12", "2020-04-08", "2020-05-13", "2020-06-11",
        "2020-07-09", "2020-08-13", "2020-09-10", "2020-10-08", "2020-11-12", "2020-12-10",
        "2021-01-13", "2021-02-11", "2021-03-11", "2021-04-13", "2021-05-13", "2021-06-10",
        "2021-07-13", "2021-08-12", "2021-09-09", "2021-10-13", "2021-11-10", "2021-12-09",
        "2022-01-13", "2022-02-10", "2022-03-10", "2022-04-13", "2022-05-12", "2022-06-09",
        "2022-07-13", "2022-08-11", "2022-09-13", "2022-10-13", "2022-11-10", "2022-12-13",
        "2023-01-12", "2023-02-09", "2023-03-09", "2023-04-13", "2023-05-11", "2023-06-13",
        "2023-07-13", "2023-08-10", "2023-09-13", "2023-10-12", "2023-11-09", "2023-12-12",
        "2024-01-11", "2024-02-08", "2024-03-13", "2024-04-11", "2024-05-09", "2024-06-13",
        "2024-07-11", "2024-08-08", "2024-09-12", "2024-10-10", "2024-11-06", "2024-12-12",
        "2025-01-08", "2025-02-13", "2025-03-13", "2025-04-10", "2025-05-08", "2025-06-12",
        "2025-07-10", "2025-08-07", "2025-09-11", "2025-10-09", "2025-11-13", "2025-12-11",
        "2026-01-13", "2026-02-12", "2026-03-12", "2026-04-09", "2026-05-13", "2026-06-11",
        "2026-07-09",
    ],
    # CPI: 77 dates
    "CPI": [
        "2020-01-14", "2020-02-13", "2020-03-11", "2020-04-10", "2020-05-12", "2020-06-10",
        "2020-07-14", "2020-08-12", "2020-09-11", "2020-10-13", "2020-11-12", "2020-12-10",
        "2021-01-13", "2021-02-10", "2021-03-10", "2021-04-13", "2021-05-12", "2021-06-10",
        "2021-07-13", "2021-08-11", "2021-09-14", "2021-10-13", "2021-11-10", "2021-12-10",
        "2022-01-12", "2022-02-10", "2022-03-10", "2022-04-12", "2022-05-11", "2022-06-10",
        "2022-07-13", "2022-08-10", "2022-09-13", "2022-10-13", "2022-11-10", "2022-12-13",
        "2023-01-12", "2023-02-14", "2023-03-14", "2023-04-12", "2023-05-10", "2023-06-13",
        "2023-07-12", "2023-08-10", "2023-09-13", "2023-10-12", "2023-11-14", "2023-12-12",
        "2024-01-11", "2024-02-13", "2024-03-12", "2024-04-10", "2024-05-15", "2024-06-12",
        "2024-07-11", "2024-08-14", "2024-09-11", "2024-10-10", "2024-11-13", "2024-12-11",
        "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10", "2025-05-13", "2025-06-11",
        "2025-07-15", "2025-08-12", "2025-09-11", "2025-10-24", "2025-12-18", "2026-01-13",
        "2026-02-13", "2026-03-11", "2026-04-10", "2026-05-12", "2026-06-10",
    ],
    # NFP: 78 dates
    "NFP": [
        "2020-01-10", "2020-02-07", "2020-03-06", "2020-04-03", "2020-05-08", "2020-06-05",
        "2020-07-02", "2020-08-07", "2020-09-04", "2020-10-02", "2020-11-06", "2020-12-04",
        "2021-01-08", "2021-02-05", "2021-03-05", "2021-04-02", "2021-05-07", "2021-06-04",
        "2021-07-02", "2021-08-06", "2021-09-03", "2021-10-08", "2021-11-05", "2021-12-03",
        "2022-01-07", "2022-02-04", "2022-03-04", "2022-04-01", "2022-05-06", "2022-06-03",
        "2022-07-08", "2022-08-05", "2022-09-02", "2022-10-07", "2022-11-04", "2022-12-02",
        "2023-01-06", "2023-02-03", "2023-03-10", "2023-04-07", "2023-05-05", "2023-06-02",
        "2023-07-07", "2023-08-04", "2023-09-01", "2023-10-06", "2023-11-03", "2023-12-08",
        "2024-01-05", "2024-02-02", "2024-03-08", "2024-04-05", "2024-05-03", "2024-06-07",
        "2024-07-05", "2024-08-02", "2024-09-06", "2024-10-04", "2024-11-01", "2024-12-06",
        "2025-01-10", "2025-02-07", "2025-03-07", "2025-04-04", "2025-05-02", "2025-06-06",
        "2025-07-03", "2025-08-01", "2025-09-05", "2025-11-20", "2025-12-16", "2026-01-09",
        "2026-02-11", "2026-03-06", "2026-04-03", "2026-05-08", "2026-06-05", "2026-07-02",
    ],
    # PPI: 77 dates
    "PPI": [
        "2020-01-15", "2020-02-19", "2020-03-12", "2020-04-09", "2020-05-13", "2020-06-11",
        "2020-07-10", "2020-08-11", "2020-09-10", "2020-10-14", "2020-11-13", "2020-12-11",
        "2021-01-15", "2021-02-17", "2021-03-12", "2021-04-09", "2021-05-13", "2021-06-15",
        "2021-07-14", "2021-08-12", "2021-09-10", "2021-10-14", "2021-11-09", "2021-12-14",
        "2022-01-13", "2022-02-15", "2022-03-15", "2022-04-13", "2022-05-12", "2022-06-14",
        "2022-07-14", "2022-08-11", "2022-09-14", "2022-10-12", "2022-11-15", "2022-12-09",
        "2023-01-18", "2023-02-16", "2023-03-15", "2023-04-13", "2023-05-11", "2023-06-14",
        "2023-07-13", "2023-08-11", "2023-09-14", "2023-10-11", "2023-11-15", "2023-12-13",
        "2024-01-12", "2024-02-16", "2024-03-14", "2024-04-11", "2024-05-14", "2024-06-13",
        "2024-07-12", "2024-08-13", "2024-09-12", "2024-10-11", "2024-11-14", "2024-12-12",
        "2025-01-14", "2025-02-13", "2025-03-13", "2025-04-11", "2025-05-15", "2025-06-12",
        "2025-07-16", "2025-08-14", "2025-09-10", "2025-11-25", "2026-01-14", "2026-01-30",
        "2026-02-27", "2026-03-18", "2026-04-14", "2026-05-13", "2026-06-11",
    ],
    # RETAIL: 79 dates
    "RETAIL": [
        "2020-01-16", "2020-02-14", "2020-03-17", "2020-04-15", "2020-05-15", "2020-06-16",
        "2020-07-16", "2020-08-14", "2020-09-16", "2020-10-16", "2020-11-17", "2020-12-16",
        "2021-01-15", "2021-02-17", "2021-03-16", "2021-04-15", "2021-05-14", "2021-06-15",
        "2021-07-16", "2021-08-17", "2021-09-16", "2021-10-15", "2021-11-16", "2021-12-15",
        "2022-01-14", "2022-02-16", "2022-03-16", "2022-04-14", "2022-05-17", "2022-06-15",
        "2022-07-15", "2022-08-17", "2022-09-15", "2022-10-14", "2022-11-16", "2022-12-15",
        "2023-01-18", "2023-02-15", "2023-03-15", "2023-04-14", "2023-05-16", "2023-06-15",
        "2023-07-18", "2023-08-15", "2023-09-14", "2023-10-17", "2023-11-15", "2023-12-14",
        "2024-01-17", "2024-02-15", "2024-03-14", "2024-04-15", "2024-05-15", "2024-06-18",
        "2024-07-16", "2024-08-15", "2024-09-17", "2024-10-17", "2024-11-15", "2024-12-17",
        "2025-01-16", "2025-02-14", "2025-03-17", "2025-04-16", "2025-05-15", "2025-06-17",
        "2025-07-17", "2025-08-15", "2025-09-16", "2025-11-25", "2025-12-16", "2026-01-14",
        "2026-02-10", "2026-03-06", "2026-04-01", "2026-04-21", "2026-05-14", "2026-06-17",
        "2026-07-16",
    ],
    # GDP_ADV: 26 dates
    "GDP_ADV": [
        "2020-01-30", "2020-04-29", "2020-07-30", "2020-10-29", "2021-01-28", "2021-04-29",
        "2021-07-29", "2021-10-28", "2022-01-27", "2022-04-28", "2022-07-28", "2022-10-27",
        "2023-01-26", "2023-04-27", "2023-07-27", "2023-10-26", "2024-01-25", "2024-04-25",
        "2024-07-25", "2024-10-30", "2025-01-30", "2025-04-30", "2025-07-30", "2025-12-23",
        "2026-02-20", "2026-04-30",
    ],
}


# --------------------------------------------------------------------------- build


def load_nvda_sessions() -> set:
    """Real US equity trading sessions = the ET dates of the NVDA daily bars."""
    nv = pd.read_parquet(NVDA_BARS, columns=["ts"])
    return set(pd.to_datetime(nv["ts"], unit="ns", utc=True).dt.tz_convert(ET).dt.date)


def build_calendar() -> tuple[pd.DataFrame, list[str]]:
    """Expand the embedded tables into calendar rows, dropping releases that land on a
    non-trading session (logged). Returns (dataframe, dropped-reason-list)."""
    sessions = load_nvda_sessions()
    rows: list[dict] = []
    dropped: list[str] = []
    for subtype, dates in RELEASE_DATES.items():
        cls = CLASS_OF_SUBTYPE[subtype]
        hh, mm = SCHED_HM[cls]
        for iso in dates:
            d = pd.Timestamp(iso).date()
            if not (COVERAGE_START <= d <= COVERAGE_END):
                continue
            if d not in sessions:
                dropped.append(f"{subtype} {iso} ({d.strftime('%a')}): market closed / not a trading session")
                continue
            sched = pd.Timestamp(d.year, d.month, d.day, hh, mm, 0, tz=ET)
            anchor = pd.Timestamp(d.year, d.month, d.day, 9, 30, 0, tz=ET) if cls == "pre_open_0830" else sched
            rows.append({
                "release_id": f"{subtype}-{iso}",
                "class": cls,
                "subtype": subtype,
                "session_date": d,
                "sched_ts_et": sched,
                "anchor_ts_et": anchor,
                "source": source_for(subtype, d),
            })
    df = pd.DataFrame(rows).sort_values(["session_date", "class", "subtype"]).reset_index(drop=True)
    df["session_date"] = pd.to_datetime(df["session_date"])  # naive midnight (a date)
    df["sched_ts_et"] = pd.to_datetime(df["sched_ts_et"], utc=True).dt.tz_convert(ET)
    df["anchor_ts_et"] = pd.to_datetime(df["anchor_ts_et"], utc=True).dt.tz_convert(ET)
    return df, dropped


def validate(df: pd.DataFrame) -> None:
    assert df["release_id"].is_unique, "release_id not unique"
    assert not df.duplicated(["subtype", "session_date"]).any(), "(subtype, session_date) not unique"
    assert set(df["class"]) <= set(SCHED_HM), "unexpected class label"
    assert str(df["sched_ts_et"].dt.tz) == "America/New_York", "sched_ts_et not America/New_York"
    assert str(df["anchor_ts_et"].dt.tz) == "America/New_York", "anchor_ts_et not America/New_York"


def main() -> None:
    if "--refresh" in sys.argv:
        print(__doc__)
        print("The embedded tables were built offline from the sources above; the one-off "
              "fetch/parse scripts (TreasuryDirect JSON, FOMC/BEA/ISM/UMich/Census HTML+PDF+XLS, "
              "BLS+Wayback filename union) live in the research scratchpad. This build does not "
              "hit the network -- edit RELEASE_DATES to update.")
        return

    df, dropped = build_calendar()
    validate(df)
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)

    print(f"[build_macro_calendar] wrote {OUT_PARQUET} ({len(df)} rows, {df['subtype'].nunique()} subtypes)")
    print(f"coverage {df['session_date'].min().date()} .. {df['session_date'].max().date()}")
    print("\ndropped (release on a non-trading session -> not shifted):")
    if dropped:
        for r in dropped:
            print(f"  - {r}")
    else:
        print("  (none)")

    print("\nper-subtype x per-year counts:")
    piv = (
        df.assign(year=df["session_date"].dt.year)
        .pivot_table(index="subtype", columns="year", values="release_id", aggfunc="count", fill_value=0)
    )
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(piv)


if __name__ == "__main__":
    main()
