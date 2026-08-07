"""Build the earnings-event calendar (data/external/earnings_calendar.parquet).

M21 anchor dataset (registered M21-earnings-reaction-regime-v1). One row per quarterly
earnings release for a frozen 25-name semis + megacap-tech universe (+ ARM from its 2023
IPO), 2018-01-01 .. 2026-07-21. Each row carries the 8-K/6-K acceptance instant, a BMO/AMC
tag, and the day-0 trading session the news first trades into.

Deterministic / offline: the acceptance timestamps below are EMBEDDED literal tables,
verified from SEC EDGAR (fetched 2026-07-22). The build only reads those tables + the NVDA
daily-bar session index (to map each event onto a real trading session). No network access
at build time. `--refresh` prints the fetch/verification methodology. Run:
`uv run python scripts/build_earnings_calendar.py`.

------------------------------------------------------------------------------------------
METHOD (PIT, per the house DR-X2 recipe)
------------------------------------------------------------------------------------------
Source. SEC EDGAR submissions API per company (data.sec.gov/submissions/CIK##########.json,
older pages CIK..-submissions-001.json for pre-2020). Domestic filers: form 8-K (8-K/A
excluded) whose `items` include 2.02 (Results of Operations). CIK lookup via
sec.gov/files/company_tickers.json. Fetched with curl + a declared UA (repo landmine L8:
sec.gov WAF-blocks python clients and any UA containing "naver"); rate <= 8 req/s.

Timestamp timezone -- verified, load-bearing. The submissions API `acceptanceDateTime`
carries a spurious trailing 'Z' but is NOT UTC: the digits are US/Eastern wall-clock,
matching EDGAR's authoritative SGML <ACCEPTANCE-DATETIME> header (checked INTC 2018-01-25 =
16:06:34 ET on the header AND the human-readable index "Accepted" line, and INTC 2025-07-24 =
16:04 ET, a known post-close release). We therefore read the wall-clock AS Eastern (no UTC
conversion). Converting from UTC would shift every BMO/AMC call by 4-5 hours.

Timing rule. accept-time-of-day (ET): >= 16:00 -> AMC (day-0 = strictly-next session);
< 16:00 -> BMO / same session (day-0 = the acceptance-date session). This EXTENDS the
registration's frozen "09:00-16:00 = ambiguous -> exclude" band to "same session": empirically
every surviving 09:00-16:00 event is a LAGGED 8-K/6-K filing of a pre-market (ADI 07:00 ET,
ASML ~01:00 ET, onsemi pre-2026) or prior-after-close (NXP) wire release -- not an intraday
release -- so its day-0 is well defined (the acceptance-date session), and excluding them
would drop ADI/ON/NXPI/ASML wholesale and fail the registration's own per-name coverage QA.
Pre-announcement / operating-metric Item-2.02 filings in this band are removed by the dedup
step below; the two genuine intraday releases (results furnished during market hours alongside
a same-day M&A 8-K: AMD 2020-10-27, AVGO 2022-05-26) are excluded outright via EXCLUDE_INTRADAY
(their day-0 opening gap pre-dates the news, so the gap-sign variable is undefined for them).
(Timing labels are the session-mapping semantics: BMO == day-0 is the
acceptance-date session, AMC == day-0 is the next session. NXP releases after the prior
close but files the 8-K/6-K the next morning, so it reads BMO here while day-0 -- the field
M21 conditions on -- is the correct post-release session.)

Dedup to one row per fiscal quarter. Companies file extra Item-2.02 8-Ks that are NOT the
quarterly report: Tesla production/delivery flashes (dropped: Item-2.02 8-Ks in a quarter's
first six days of Jan/Apr/Jul/Oct), preliminary revenue pre-announcements, business updates,
and non-earnings 8-Ks that merely carry Item 2.02 (AMD 2018-02-27 ASC-606 adoption; AVGO
2018-01-31 Qualcomm-bid guidance; SMCI 2020-04-02 FQ3 update slides; NFLX 2019-12-16 recast
furnish). Rule: cluster a symbol's events within 30 days and keep the LATEST (the full report
follows any pre-announcement); the four named non-earnings filings that survive that rule are
dropped by hand (verified individually). AMAT 2024-05-16 (Q2 FY2024) is the reverse case --
its 8-K body declares Item 2.02 but EDGAR mis-tagged the metadata "2.01", so it is added back.

Foreign private issuers (6-K, no item codes).
  ASML -- INCLUDED. Earnings 6-Ks identified by primary-doc filename (form6kq<N>results* for
      2018-2020, form6-kquarterlyfilings* for 2021+, plus the two generic form6k.htm on
      2020-10-14 and 2021-01-20 verified by ASML's quarterly cadence). Releases ~01:00 ET
      pre-US-market; the 6-K posts ~10:00 ET (BMO, same session). 35 events.
  ARM  -- INCLUDED from its Sep-2023 IPO. 11 quarterly-results 6-Ks (the announcement 6-K
      whose filename date == acceptance date; the paired quarter-end-dated financials 6-K and
      corporate 6-Ks excluded). Reports after the US close (AMC). 11 events.
  NXP  -- INCLUDED full range, but hybrid: filed results as 6-K (no Item 2.02) through Q2
      2019, then 8-K Item 2.02 from Q3 2019. The 7 pre-switch earnings 6-Ks were each verified
      by press-release title ("NXP Semiconductors Reports <Quarter> Results"); the 2018-07-27
      Qualcomm-deal-termination 6-K is deliberately excluded.
  TSM  -- DROPPED (reported). TSMC furnishes ~monthly revenue + quarterly results + many
      corporate items all as bare 6-K with identical metadata and shifting filenames; the
      quarterly-earnings 6-K is not reliably machine-separable from the submissions API, and
      the registration's FPI provision permits dropping-with-reason over unreliable filling.

Session index. Real US trading sessions == the ET dates of the NVDA daily bars
(data/raw/sip/bars1d/NVDA.parquet), which begin 2019-11-01 and were verified to match the
NYSE calendar exactly over their span (1686/1686, incl. the 2018-12-05 Bush-mourning closure
handled by the calendar). The pre-2019-11 gap is filled from the same NYSE calendar
(enginev51.data.calendar, pandas_market_calendars) so 2018-01 .. 2019-10 events map correctly.

Validation. 20 events across 20 symbols and 2018/2020/2022/2023/2024/2026 were cross-checked
against company IR / press coverage (see the build report / the module's git note); all 20
matched on date and BMO/AMC. Six are pinned as literal test assertions in the test module.
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

ET = ZoneInfo("America/New_York")
NVDA_BARS = PROJECT_ROOT / "data" / "raw" / "sip" / "bars1d" / "NVDA.parquet"
OUT_PARQUET = PROJECT_ROOT / "data" / "external" / "earnings_calendar.parquet"

COVERAGE_START = date(2018, 1, 1)
COVERAGE_END = date(2026, 7, 21)
_FETCHED = "2026-07-22"

# True intraday earnings releases -- furnished DURING regular market hours (not before the
# open, not after the close). The day-0 opening gap pre-dates the news, so the registered
# gap-sign bucketing variable is undefined w.r.t. earnings for these; excluded per orchestrator
# ratification (2026-07-22), reason "true_intraday_release". Both were results furnished
# alongside a same-day M&A announcement:
#   AMD  2020-10-27 10:34 ET -- Q3 2020 results, filed with the Xilinx acquisition 8-K
#   AVGO 2022-05-26 11:28 ET -- Q2 FY2022 results, filed with the VMware acquisition 8-K
EXCLUDE_INTRADAY = {
    ("AMD", "2020-10-27T10:34"),   # true_intraday_release
    ("AVGO", "2022-05-26T11:28"),  # true_intraday_release
}

# Symbols dropped from the frozen universe, with reason (reported honestly per registration).
DROPPED_NAMES = {
    "TSM": "TSMC files monthly-revenue + quarterly + corporate items all as bare 6-K with "
           "identical submissions metadata; the quarterly-earnings 6-K is not reliably "
           "machine-identifiable (registration FPI drop-with-reason provision).",
}

# Fiscal-year-end (MMDD) from each issuer's SEC submissions `fiscalYearEnd`, for fiscal_note.
FYE = {
    "NVDA": "0131", "AMD": "1226", "MU": "0903", "AVGO": "1101", "QCOM": "0927",
    "TXN": "1231", "INTC": "1231", "AMAT": "1026", "LRCX": "0628", "KLAC": "0630",
    "MRVL": "0130", "ON": "1231", "MCHP": "0331", "ADI": "1101", "NXPI": "1231",
    "ASML": "1231", "SMCI": "0630", "AAPL": "0926", "MSFT": "0630", "GOOGL": "1231",
    "AMZN": "1231", "META": "1231", "TSLA": "1231", "NFLX": "1231", "ARM": "0331",
}
# Provenance class per symbol (short).
SIX_K = {"ASML", "ARM"}


def source_for(symbol: str) -> str:
    if symbol == "NXPI":
        return f"SEC EDGAR 8-K 2.02 + pre-2019Q3 6-K ({_FETCHED})"
    if symbol in SIX_K:
        return f"SEC EDGAR 6-K quarterly results ({_FETCHED})"
    return f"SEC EDGAR 8-K Item 2.02 ({_FETCHED})"


# --------------------------------------------------------------------------- embedded data
# Verified 8-K/6-K acceptance instants (US/Eastern wall-clock, minute precision), one list
# per symbol, chronological. See the module docstring for provenance, timezone proof, the
# BMO/AMC rule, the dedup rule, and the dropped/added-by-hand events. Regenerate via the
# `--refresh` methodology (offline fetch scripts live in the research scratchpad), not here.

EVENTS: dict[str, list[str]] = {
    'NVDA': [
        '2018-02-08T21:23', '2018-05-10T20:25', '2018-08-16T20:20', '2018-11-15T21:21', '2019-02-14T21:23', '2019-05-16T20:22',
        '2019-08-15T20:27', '2019-11-14T21:21', '2020-02-13T21:21', '2020-05-21T20:22', '2020-08-19T20:21', '2020-11-18T21:21',
        '2021-02-24T21:22', '2021-05-26T20:20', '2021-08-18T20:21', '2021-11-17T21:20', '2022-02-16T21:21', '2022-05-25T20:22',
        '2022-08-24T20:24', '2022-11-16T21:21', '2023-02-22T21:52', '2023-05-24T20:22', '2023-08-23T20:21', '2023-11-21T21:22',
        '2024-02-21T21:22', '2024-05-22T20:21', '2024-08-28T20:21', '2024-11-20T21:21', '2025-02-26T21:21', '2025-05-28T20:21',
        '2025-08-27T20:22', '2025-11-19T21:20', '2026-02-25T21:31', '2026-05-20T20:21',
    ],
    'AMD': [
        '2018-01-30T21:06', '2018-04-25T20:17', '2018-07-25T20:41', '2018-10-24T20:32', '2019-01-29T21:19', '2019-04-30T20:21',
        '2019-07-30T20:21', '2019-10-29T21:11', '2020-01-28T21:17', '2020-04-28T20:29', '2020-07-28T20:20', '2020-10-27T10:34',
        '2021-01-26T21:14', '2021-04-27T20:12', '2021-07-27T20:39', '2021-10-26T20:17', '2022-02-01T21:17', '2022-05-03T20:11',
        '2022-08-02T20:08', '2022-11-01T20:17', '2023-01-31T21:55', '2023-05-02T20:17', '2023-08-01T20:16', '2023-10-31T20:16',
        '2024-01-30T21:16', '2024-04-30T20:16', '2024-07-30T20:17', '2024-10-29T20:16', '2025-02-04T21:17', '2025-05-06T20:16',
        '2025-08-05T20:16', '2025-11-04T21:16', '2026-02-03T21:16', '2026-05-05T20:16',
    ],
    'MU': [
        '2018-03-22T20:01', '2018-06-20T20:06', '2018-09-20T20:00', '2018-12-18T21:00', '2019-03-20T20:00', '2019-06-25T20:01',
        '2019-09-26T20:00', '2019-12-18T21:00', '2020-03-25T20:00', '2020-06-29T20:02', '2020-09-29T20:00', '2021-01-07T21:00',
        '2021-03-31T20:00', '2021-06-30T20:00', '2021-09-28T20:01', '2021-12-20T21:00', '2022-03-29T20:00', '2022-06-30T20:00',
        '2022-09-29T20:00', '2022-12-21T21:00', '2023-03-28T20:01', '2023-06-28T20:00', '2023-09-27T20:00', '2023-12-20T21:00',
        '2024-03-20T20:00', '2024-06-26T20:00', '2024-09-25T20:00', '2024-12-18T21:00', '2025-03-20T20:00', '2025-06-25T20:03',
        '2025-09-23T20:02', '2025-12-17T21:03', '2026-03-18T20:02', '2026-06-24T20:02',
    ],
    'AVGO': [
        '2018-03-15T16:08', '2018-06-07T20:05', '2018-09-06T20:22', '2018-12-06T21:23', '2019-03-14T20:23', '2019-06-13T20:23',
        '2019-09-12T20:25', '2019-12-12T21:39', '2020-03-12T20:23', '2020-06-04T20:29', '2020-09-03T20:17', '2020-12-10T21:19',
        '2021-03-04T21:18', '2021-06-03T20:19', '2021-09-02T20:18', '2021-12-09T21:26', '2022-03-03T21:18', '2022-05-26T11:28',
        '2022-09-01T20:26', '2022-12-08T21:21', '2023-03-02T21:16', '2023-06-01T20:17', '2023-08-31T21:18', '2023-12-07T21:18',
        '2024-03-07T21:18', '2024-06-12T20:19', '2024-09-05T20:21', '2024-12-12T21:23', '2025-03-06T21:19', '2025-06-05T20:27',
        '2025-09-04T20:19', '2025-12-11T21:17', '2026-03-04T21:16', '2026-06-03T20:21',
    ],
    'QCOM': [
        '2018-01-31T21:06', '2018-04-25T20:04', '2018-07-25T20:05', '2018-11-07T21:06', '2019-01-30T21:03', '2019-05-01T20:04',
        '2019-07-31T20:06', '2019-11-06T21:03', '2020-02-05T21:04', '2020-04-29T20:12', '2020-07-29T20:05', '2020-11-04T21:06',
        '2021-02-03T21:02', '2021-04-28T20:01', '2021-07-28T20:01', '2021-11-03T20:05', '2022-02-02T21:03', '2022-04-27T20:02',
        '2022-07-27T20:02', '2022-11-02T20:01', '2023-02-02T21:03', '2023-05-03T20:04', '2023-08-02T20:01', '2023-11-01T20:09',
        '2024-01-31T21:01', '2024-05-01T20:05', '2024-07-31T20:01', '2024-11-06T21:07', '2025-02-05T21:04', '2025-04-30T20:04',
        '2025-07-30T20:01', '2025-11-05T21:01', '2026-02-04T21:00', '2026-04-29T20:02',
    ],
    'TXN': [
        '2018-01-23T21:27', '2018-04-24T20:11', '2018-07-24T20:25', '2018-10-23T20:15', '2019-01-23T21:12', '2019-04-23T20:18',
        '2019-07-23T20:13', '2019-10-22T20:05', '2020-01-22T21:03', '2020-04-21T20:08', '2020-07-21T20:08', '2020-10-20T20:05',
        '2021-01-26T21:06', '2021-04-27T20:05', '2021-07-21T20:08', '2021-10-26T20:12', '2022-01-25T21:02', '2022-04-26T20:04',
        '2022-07-26T20:04', '2022-10-25T20:04', '2023-01-24T21:03', '2023-04-25T20:03', '2023-07-25T20:03', '2023-10-24T20:03',
        '2024-01-23T21:03', '2024-04-23T20:04', '2024-07-23T20:03', '2024-10-22T20:03', '2025-01-23T21:05', '2025-04-23T20:04',
        '2025-07-22T20:03', '2025-10-21T20:05', '2026-01-27T21:05', '2026-04-22T20:03',
    ],
    'INTC': [
        '2018-01-25T16:06', '2018-04-26T16:05', '2018-07-26T16:05', '2018-10-25T16:08', '2019-01-24T16:06', '2019-04-25T16:05',
        '2019-07-25T16:10', '2019-10-24T16:08', '2020-01-23T16:07', '2020-04-23T16:07', '2020-07-23T16:07', '2020-10-22T16:07',
        '2021-01-21T16:04', '2021-04-22T16:05', '2021-07-22T16:05', '2021-10-21T16:09', '2022-01-26T16:08', '2022-04-28T16:09',
        '2022-07-28T16:06', '2022-10-27T16:02', '2023-01-26T16:06', '2023-04-27T16:09', '2023-07-27T16:07', '2023-10-26T16:09',
        '2024-01-25T16:07', '2024-04-25T16:09', '2024-08-01T16:08', '2024-10-31T16:07', '2025-01-30T16:13', '2025-04-24T16:05',
        '2025-07-24T16:04', '2025-10-23T16:10', '2026-01-22T16:10', '2026-04-23T16:07',
    ],
    'AMAT': [
        '2018-02-14T21:09', '2018-05-17T20:03', '2018-08-16T20:07', '2018-11-15T21:05', '2019-02-14T21:03', '2019-05-16T20:04',
        '2019-08-15T20:03', '2019-11-14T21:21', '2020-02-12T21:03', '2020-05-14T20:12', '2020-08-13T20:06', '2020-11-12T21:04',
        '2021-02-18T21:05', '2021-05-20T20:11', '2021-08-19T20:04', '2021-11-18T21:03', '2022-02-16T21:03', '2022-05-19T20:04',
        '2022-08-18T20:04', '2022-11-17T21:03', '2023-02-16T21:05', '2023-05-18T20:05', '2023-08-17T20:03', '2023-11-16T21:04',
        '2024-02-15T21:03', '2024-05-16T20:03', '2024-08-15T20:04', '2024-11-14T21:04', '2025-02-13T21:05', '2025-05-15T20:03',
        '2025-08-14T20:05', '2025-11-13T21:03', '2026-02-12T21:03', '2026-05-14T20:03',
    ],
    'LRCX': [
        '2018-01-24T21:07', '2018-04-17T20:05', '2018-07-26T20:14', '2018-10-16T20:07', '2019-01-23T21:07', '2019-04-24T20:11',
        '2019-07-31T20:12', '2019-10-23T20:08', '2020-01-29T21:07', '2020-04-22T20:08', '2020-07-29T20:18', '2020-10-21T20:08',
        '2021-01-27T21:09', '2021-04-21T20:09', '2021-07-28T20:08', '2021-10-20T20:08', '2022-01-26T21:08', '2022-04-20T20:08',
        '2022-07-27T20:11', '2022-10-19T20:11', '2023-01-25T21:13', '2023-04-19T20:14', '2023-07-26T20:08', '2023-10-18T20:09',
        '2024-01-24T21:09', '2024-04-24T20:12', '2024-07-31T20:09', '2024-10-23T20:07', '2025-01-29T21:07', '2025-04-23T20:07',
        '2025-07-30T20:07', '2025-10-22T20:08', '2026-01-28T21:06', '2026-04-22T20:09',
    ],
    'KLAC': [
        '2018-01-25T21:33', '2018-04-26T20:32', '2018-07-30T20:30', '2018-10-29T20:34', '2019-01-29T21:27', '2019-05-06T20:24',
        '2019-08-05T20:22', '2019-10-30T20:16', '2020-02-04T21:11', '2020-05-05T20:22', '2020-08-03T20:16', '2020-10-28T20:39',
        '2021-02-03T21:42', '2021-04-29T20:40', '2021-07-29T20:38', '2021-10-27T20:39', '2022-01-27T21:25', '2022-04-28T20:26',
        '2022-07-28T20:12', '2022-10-26T20:47', '2023-01-26T21:24', '2023-04-26T20:41', '2023-07-27T20:08', '2023-10-25T20:06',
        '2024-01-25T21:07', '2024-04-25T20:14', '2024-07-24T20:13', '2024-10-30T20:07', '2025-01-30T21:06', '2025-04-30T20:08',
        '2025-07-31T20:08', '2025-10-29T20:11', '2026-01-29T21:06', '2026-04-29T20:06',
    ],
    'MRVL': [
        '2018-03-08T16:07', '2018-05-31T16:06', '2018-09-06T16:06', '2018-12-04T16:06', '2019-03-07T16:08', '2019-05-30T16:13',
        '2019-08-29T16:15', '2019-12-03T16:08', '2020-03-04T16:47', '2020-05-28T16:07', '2020-08-27T16:11', '2020-12-03T16:06',
        '2021-03-03T16:06', '2021-06-07T20:07', '2021-08-26T20:06', '2021-12-02T21:09', '2022-03-03T21:06', '2022-05-26T20:06',
        '2022-08-25T20:06', '2022-12-01T21:06', '2023-03-02T21:07', '2023-05-25T20:06', '2023-08-24T20:06', '2023-11-30T21:06',
        '2024-03-07T21:07', '2024-05-30T20:06', '2024-08-29T20:06', '2024-12-03T21:06', '2025-03-05T21:09', '2025-05-29T20:06',
        '2025-08-28T20:06', '2025-12-02T21:11', '2026-03-05T21:06', '2026-05-27T20:06',
    ],
    'ON': [
        '2018-02-05T11:08', '2018-04-30T10:09', '2018-07-30T10:09', '2018-10-29T10:12', '2019-02-01T22:06', '2019-04-29T10:08',
        '2019-08-05T10:04', '2019-10-28T10:10', '2020-02-03T11:12', '2020-05-11T10:17', '2020-08-10T10:11', '2020-11-02T11:15',
        '2021-02-01T13:05', '2021-05-03T12:00', '2021-08-02T12:06', '2021-11-01T12:06', '2022-02-07T13:06', '2022-05-02T12:05',
        '2022-08-01T12:05', '2022-10-31T12:05', '2023-02-06T13:05', '2023-05-01T12:05', '2023-07-31T12:06', '2023-10-30T12:05',
        '2024-02-05T13:06', '2024-04-29T12:07', '2024-07-29T12:08', '2024-10-28T12:05', '2025-02-10T13:05', '2025-05-05T12:05',
        '2025-08-04T12:05', '2025-11-03T13:05', '2026-02-09T21:21', '2026-05-04T20:10',
    ],
    'MCHP': [
        '2018-02-06T21:16', '2018-05-08T12:02', '2018-08-09T20:18', '2018-11-07T21:17', '2019-02-05T21:13', '2019-05-08T00:55',
        '2019-08-06T20:14', '2019-11-05T21:13', '2020-02-04T21:14', '2020-05-07T20:13', '2020-08-04T20:25', '2020-11-05T21:29',
        '2021-02-04T20:56', '2021-05-06T20:18', '2021-08-03T20:17', '2021-11-04T20:19', '2022-02-03T21:17', '2022-05-09T20:18',
        '2022-08-02T20:17', '2022-11-03T20:18', '2023-02-02T21:17', '2023-05-04T20:18', '2023-08-03T20:17', '2023-11-02T20:17',
        '2024-02-01T21:12', '2024-05-06T20:17', '2024-08-01T20:12', '2024-11-05T21:17', '2025-02-06T21:16', '2025-05-08T20:17',
        '2025-08-07T20:20', '2025-11-06T21:21', '2026-01-05T21:27', '2026-02-05T21:16', '2026-05-07T20:19',
    ],
    'ADI': [
        '2018-02-28T13:11', '2018-05-30T12:11', '2018-08-22T12:11', '2018-11-20T13:09', '2019-02-20T13:10', '2019-05-22T11:31',
        '2019-08-21T12:02', '2019-11-26T13:03', '2020-02-19T13:03', '2020-05-20T11:33', '2020-08-19T12:03', '2020-11-24T13:04',
        '2021-02-17T13:03', '2021-05-19T11:02', '2021-08-18T11:04', '2021-11-23T12:03', '2022-02-16T12:04', '2022-05-18T11:02',
        '2022-08-17T11:02', '2022-11-22T12:03', '2023-02-15T12:04', '2023-05-24T11:02', '2023-08-23T11:02', '2023-11-21T12:02',
        '2024-02-21T12:05', '2024-05-22T11:03', '2024-08-21T11:01', '2024-11-26T12:04', '2025-02-19T12:11', '2025-05-22T11:04',
        '2025-08-20T11:02', '2025-11-25T12:03', '2026-02-18T12:02', '2026-05-20T11:01',
    ],
    'NXPI': [
        '2018-02-08T11:18', '2018-05-03T10:07', '2018-07-26T10:46', '2018-11-01T10:25', '2019-02-07T11:20', '2019-04-30T10:06',
        '2019-07-30T10:01', '2019-10-29T11:17', '2020-02-04T11:16', '2020-04-28T10:26', '2020-07-28T10:16', '2020-10-27T11:20',
        '2021-02-02T11:09', '2021-04-27T10:13', '2021-08-03T10:09', '2021-11-02T11:42', '2022-02-01T11:10', '2022-05-03T10:05',
        '2022-07-26T10:00', '2022-11-01T10:05', '2023-01-31T11:06', '2023-05-02T10:12', '2023-07-25T10:05', '2023-11-07T11:09',
        '2024-02-06T11:08', '2024-04-30T10:04', '2024-07-23T10:08', '2024-11-05T11:04', '2025-02-04T11:02', '2025-04-28T20:16',
        '2025-07-22T10:33', '2025-10-28T10:41', '2026-02-03T11:05', '2026-04-28T20:19',
    ],
    'ASML': [
        '2018-01-17T12:10', '2018-04-18T10:12', '2018-07-18T10:13', '2018-10-17T10:29', '2019-01-23T11:25', '2019-04-17T10:16',
        '2019-07-17T10:16', '2019-10-16T10:09', '2020-01-22T11:03', '2020-04-15T10:03', '2020-07-15T10:19', '2020-10-14T10:02',
        '2021-01-20T11:03', '2021-04-21T10:01', '2021-07-21T10:04', '2021-10-20T10:04', '2022-01-19T11:02', '2022-04-20T10:02',
        '2022-07-20T10:02', '2022-10-19T10:02', '2023-01-25T11:01', '2023-04-19T10:01', '2023-07-19T10:01', '2023-10-18T10:01',
        '2024-01-24T11:01', '2024-04-17T10:01', '2024-07-17T10:02', '2024-10-15T15:34', '2025-01-29T11:02', '2025-04-16T10:02',
        '2025-07-16T10:02', '2025-10-15T10:01', '2026-01-28T11:03', '2026-04-15T10:02', '2026-07-15T10:05',
    ],
    'SMCI': [
        '2018-01-30T21:16', '2018-05-03T20:18', '2018-08-21T20:27', '2018-11-15T21:53', '2019-02-14T21:24', '2019-05-17T01:26',
        '2019-08-15T20:16', '2019-11-14T21:21', '2020-02-06T21:41', '2020-05-07T20:11', '2020-08-11T20:07', '2020-11-03T21:08',
        '2021-02-02T21:39', '2021-05-04T20:10', '2021-08-10T20:08', '2021-11-02T20:14', '2022-02-01T21:28', '2022-05-03T20:08',
        '2022-08-09T20:17', '2022-11-01T20:18', '2023-01-31T21:40', '2023-05-02T20:12', '2023-08-08T20:10', '2023-11-01T20:23',
        '2024-01-29T21:16', '2024-04-30T20:17', '2024-08-06T20:26', '2024-11-05T21:19', '2025-02-11T21:25', '2025-05-06T20:07',
        '2025-08-05T20:08', '2025-11-04T21:08', '2026-02-03T21:51', '2026-05-05T20:08', '2026-07-21T20:10',
    ],
    'AAPL': [
        '2018-02-01T21:30', '2018-05-01T20:30', '2018-07-31T20:30', '2018-11-01T20:30', '2019-01-29T21:30', '2019-04-30T20:30',
        '2019-07-30T20:30', '2019-10-30T20:30', '2020-01-28T21:30', '2020-04-30T20:30', '2020-07-30T22:55', '2020-10-29T20:30',
        '2021-01-27T21:30', '2021-04-28T20:30', '2021-07-27T20:35', '2021-10-28T20:30', '2022-01-27T21:30', '2022-04-28T20:32',
        '2022-07-28T20:31', '2022-10-27T20:30', '2023-02-02T21:30', '2023-05-04T20:30', '2023-08-03T20:30', '2023-11-02T20:30',
        '2024-02-01T21:30', '2024-05-02T20:30', '2024-08-01T20:30', '2024-10-31T20:30', '2025-01-30T21:30', '2025-05-01T20:30',
        '2025-07-31T20:30', '2025-10-30T20:30', '2026-01-29T21:30', '2026-04-30T20:30',
    ],
    'MSFT': [
        '2018-01-31T21:05', '2018-04-26T20:04', '2018-07-19T20:02', '2018-10-24T20:03', '2019-01-30T21:03', '2019-04-24T20:04',
        '2019-07-18T20:03', '2019-10-23T20:06', '2020-01-29T21:03', '2020-04-29T20:03', '2020-07-22T20:03', '2020-10-27T20:12',
        '2021-01-26T21:04', '2021-04-27T20:04', '2021-07-27T20:41', '2021-10-26T20:04', '2022-01-25T21:03', '2022-04-26T20:03',
        '2022-07-26T20:02', '2022-10-25T20:02', '2023-01-24T21:28', '2023-04-25T20:03', '2023-07-25T20:02', '2023-10-24T20:03',
        '2024-01-30T21:03', '2024-04-25T20:03', '2024-07-30T20:03', '2024-10-30T20:04', '2025-01-29T21:08', '2025-04-30T20:06',
        '2025-07-30T20:08', '2025-10-29T20:07', '2026-01-28T21:04', '2026-04-29T20:03',
    ],
    'GOOGL': [
        '2018-02-01T21:01', '2018-04-23T20:01', '2018-07-23T20:02', '2018-10-25T20:01', '2019-02-04T21:01', '2019-04-29T20:01',
        '2019-07-25T20:01', '2019-10-28T20:03', '2020-02-03T21:02', '2020-04-28T20:01', '2020-07-30T22:40', '2020-10-29T20:01',
        '2021-02-02T21:01', '2021-04-27T20:01', '2021-07-27T20:36', '2021-10-26T20:01', '2022-02-01T21:01', '2022-04-26T20:01',
        '2022-07-26T20:02', '2022-10-25T20:01', '2023-02-02T21:01', '2023-04-25T20:01', '2023-07-25T20:01', '2023-10-24T20:01',
        '2024-01-30T21:01', '2024-04-25T20:01', '2024-07-23T20:01', '2024-10-29T20:01', '2025-02-04T21:01', '2025-04-24T20:01',
        '2025-07-23T20:01', '2025-10-29T20:01', '2026-02-04T21:01', '2026-04-29T20:01',
    ],
    'AMZN': [
        '2018-02-01T21:15', '2018-04-26T20:16', '2018-07-26T20:14', '2018-10-25T20:18', '2019-01-31T21:30', '2019-04-25T20:10',
        '2019-07-25T20:33', '2019-10-24T23:53', '2020-01-30T21:46', '2020-04-30T20:42', '2020-07-30T23:05', '2020-10-29T20:42',
        '2021-02-02T21:30', '2021-04-29T20:31', '2021-07-29T20:34', '2021-10-28T20:07', '2022-02-03T21:11', '2022-04-28T20:27',
        '2022-07-28T20:09', '2022-10-27T20:09', '2023-02-02T21:08', '2023-04-27T20:10', '2023-08-03T20:09', '2023-10-26T20:14',
        '2024-02-01T21:06', '2024-04-30T20:10', '2024-08-01T20:06', '2024-10-31T20:13', '2025-02-06T21:09', '2025-05-01T20:15',
        '2025-07-31T20:13', '2025-10-30T20:13', '2026-02-05T21:25', '2026-04-29T20:18',
    ],
    'META': [
        '2018-01-31T21:10', '2018-04-25T20:18', '2018-07-25T20:08', '2018-10-30T20:14', '2019-01-30T21:16', '2019-04-24T20:09',
        '2019-07-24T20:27', '2019-10-30T20:13', '2020-01-29T21:10', '2020-04-29T20:10', '2020-07-30T23:18', '2020-10-29T20:07',
        '2021-01-27T21:08', '2021-04-28T20:09', '2021-07-28T20:08', '2021-10-25T20:08', '2022-02-02T21:08', '2022-04-27T20:07',
        '2022-07-27T20:07', '2022-10-26T20:19', '2023-02-01T21:22', '2023-04-26T20:18', '2023-07-26T20:06', '2023-10-25T20:20',
        '2024-02-01T21:10', '2024-04-24T20:07', '2024-07-31T20:11', '2024-10-30T20:08', '2025-01-29T21:47', '2025-04-30T20:16',
        '2025-07-30T20:13', '2025-10-29T20:08', '2026-01-28T21:04', '2026-04-29T20:05',
    ],
    'TSLA': [
        '2018-02-07T21:11', '2018-05-02T20:12', '2018-08-01T20:32', '2018-10-24T20:27', '2019-01-30T21:17', '2019-04-24T21:15',
        '2019-07-24T20:56', '2019-10-23T21:25', '2020-01-29T22:12', '2020-04-29T20:56', '2020-07-22T20:54', '2020-10-21T20:38',
        '2021-01-27T22:11', '2021-04-26T20:53', '2021-07-26T20:25', '2021-10-20T21:14', '2022-01-26T21:26', '2022-04-20T20:12',
        '2022-07-20T20:43', '2022-10-19T21:15', '2023-01-25T21:41', '2023-04-19T21:25', '2023-07-19T20:46', '2023-10-18T20:15',
        '2024-01-24T22:24', '2024-04-23T20:09', '2024-07-23T20:32', '2024-10-23T20:09', '2025-01-29T21:09', '2025-04-22T20:10',
        '2025-07-23T20:14', '2025-10-22T20:06', '2026-01-28T21:11', '2026-04-22T20:10',
    ],
    'NFLX': [
        '2018-01-22T21:09', '2018-04-16T20:16', '2018-07-16T20:13', '2018-10-16T20:21', '2019-01-17T21:08', '2019-04-16T20:07',
        '2019-07-17T20:40', '2019-10-16T20:39', '2020-01-21T21:03', '2020-04-21T20:02', '2020-07-16T20:57', '2020-10-20T20:07',
        '2021-01-19T21:02', '2021-04-20T20:06', '2021-07-20T20:04', '2021-10-19T20:02', '2022-01-20T21:01', '2022-04-19T20:03',
        '2022-07-19T20:02', '2022-10-18T20:06', '2023-01-19T21:51', '2023-04-18T20:03', '2023-07-19T20:04', '2023-10-18T20:01',
        '2024-01-23T21:02', '2024-04-18T20:02', '2024-07-18T20:01', '2024-10-17T20:01', '2025-01-21T21:02', '2025-04-17T20:04',
        '2025-07-17T20:04', '2025-10-21T20:02', '2026-01-20T21:07', '2026-04-16T20:01', '2026-07-16T20:03',
    ],
    'ARM': [
        '2023-11-08T21:06', '2024-02-07T21:06', '2024-05-08T20:06', '2024-07-31T20:01', '2024-11-06T21:02', '2025-02-05T21:02',
        '2025-05-07T20:01', '2025-07-30T20:02', '2025-11-05T21:02', '2026-02-04T21:02', '2026-05-06T20:02',
    ],
}


# --------------------------------------------------------------------------- build helpers


def load_sessions() -> list[date]:
    """Real US equity trading sessions. NVDA daily bars are the authoritative source over
    their span (2019-11-01+, verified == NYSE calendar exactly); the same NYSE calendar
    (enginev51.data.calendar) fills the pre-bars 2018-01..2019-10 gap and extends one month
    past the window end so the last AMC events resolve their next session. NVDA sessions are
    asserted to be a subset of the NYSE calendar (they are all real NYSE sessions)."""
    nv = pd.read_parquet(NVDA_BARS, columns=["ts"])
    nvda = set(pd.to_datetime(nv["ts"], unit="ns", utc=True).dt.tz_convert(ET).dt.date)
    from enginev51.data import calendar as cal  # NYSE calendar (pandas_market_calendars)
    back = set(cal.trading_days(COVERAGE_START, min(nvda) - timedelta(days=1)))
    fwd = set(cal.trading_days(max(nvda) + timedelta(days=1), COVERAGE_END + timedelta(days=45)))
    assert nvda <= set(cal.trading_days(min(nvda), max(nvda))), "NVDA bars diverge from NYSE calendar"
    return sorted(nvda | back | fwd)


def timing_and_day0(dt: datetime, sessions: list[date]) -> tuple[str, date]:
    """AMC (accept-time >= 16:00 ET) -> next session; else BMO -> the acceptance-date session
    (or next session if the acceptance day itself is not a trading day)."""
    import bisect
    d = dt.date()
    if dt.hour >= 16:
        return "AMC", sessions[bisect.bisect_right(sessions, d)]
    return "BMO", sessions[bisect.bisect_left(sessions, d)]


def fiscal_note(report_day: date, fye_mmdd: str) -> str:
    """Best-effort 'Q<n> FY<yyyy>' from the issuer's fiscal-year-end month/day: the fiscal
    quarter whose end falls 0-75 days before the report. FY is labelled by the calendar year
    the fiscal YEAR ends (the dominant US convention). '' if no quarter-end fits. Enumerates
    each candidate fiscal year's four quarter-ends directly (Q4 at FYE, Q3/Q2/Q1 at FYE minus
    3/6/9 months) so the FY label follows the quarter-end unambiguously across year rollovers."""
    fm, fd = int(fye_mmdd[:2]), int(fye_mmdd[2:])
    best = None
    for fy in (report_day.year - 1, report_day.year, report_day.year + 1):
        for q, back in ((4, 0), (3, 3), (2, 6), (1, 9)):
            m, yy = fm - back, fy
            while m <= 0:
                m += 12
                yy -= 1
            d = fd
            while True:
                try:
                    qe = date(yy, m, d)
                    break
                except ValueError:
                    d -= 1
            lag = (report_day - qe).days
            if 0 <= lag <= 75 and (best is None or lag < best[0]):
                best = (lag, q, fy)
    return f"Q{best[1]} FY{best[2]}" if best else ""


def build_calendar() -> pd.DataFrame:
    """Expand the embedded acceptance timestamps into calendar rows."""
    sessions = load_sessions()
    rows: list[dict] = []
    for symbol, stamps in EVENTS.items():
        for iso in stamps:
            if (symbol, iso) in EXCLUDE_INTRADAY:  # true_intraday_release (see EXCLUDE_INTRADAY)
                continue
            dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M").replace(tzinfo=ET)
            if not (COVERAGE_START <= dt.date() <= COVERAGE_END):
                continue
            timing, day0 = timing_and_day0(dt, sessions)
            rows.append({
                "event_id": f"{symbol}-{day0.isoformat()}",
                "symbol": symbol,
                "fiscal_note": fiscal_note(dt.date(), FYE[symbol]),
                "accept_ts_et": dt,
                "timing": timing,
                "day0_session": day0,
                "source": source_for(symbol),
            })
    df = pd.DataFrame(rows).sort_values(["symbol", "day0_session"]).reset_index(drop=True)
    df["accept_ts_et"] = pd.to_datetime(df["accept_ts_et"], utc=True).dt.tz_convert(ET)
    df["day0_session"] = pd.to_datetime(df["day0_session"])
    return df


def validate(df: pd.DataFrame, sessions: set) -> None:
    assert df["event_id"].is_unique, "event_id not unique"
    assert not df.duplicated(["symbol", "day0_session"]).any(), "(symbol, day0_session) not unique"
    assert set(df["timing"]) <= {"BMO", "AMC"}, "timing not in {BMO, AMC}"
    assert str(df["accept_ts_et"].dt.tz) == "America/New_York", "accept_ts_et not ET"
    lo = pd.Timestamp(COVERAGE_START)
    hi = pd.Timestamp(COVERAGE_END)
    acc = df["accept_ts_et"].dt.tz_localize(None)
    assert (acc >= lo).all() and (acc <= hi + pd.Timedelta(days=1)).all(), "accept_ts out of window"
    assert df["day0_session"].dt.date.map(lambda d: d in sessions).all(), "day0 not a trading session"


def main() -> None:
    if "--refresh" in sys.argv:
        print(__doc__)
        print("The embedded tables were built offline from SEC EDGAR (curl + declared UA; "
              "submissions API + filing headers for the timezone proof). The one-off fetch / "
              "dedup / cross-validation scripts live in the research scratchpad. This build "
              "does not hit the network -- edit EVENTS to update.")
        return

    df = build_calendar()
    sessions = set(load_sessions())
    validate(df, sessions)
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)

    print(f"[build_earnings_calendar] wrote {OUT_PARQUET} "
          f"({len(df)} rows, {df['symbol'].nunique()} symbols)")
    print(f"coverage {df['day0_session'].min().date()} .. {df['day0_session'].max().date()}")
    print(f"timing: {df['timing'].value_counts().to_dict()}")
    print(f"dropped names: {sorted(DROPPED_NAMES)}")

    print("\nper-symbol x per-year counts (by day0_session year):")
    piv = (
        df.assign(year=df["day0_session"].dt.year)
        .pivot_table(index="symbol", columns="year", values="event_id", aggfunc="count", fill_value=0)
    )
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(piv)


if __name__ == "__main__":
    main()
