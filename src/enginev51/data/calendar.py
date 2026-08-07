"""NYSE trading calendar helpers (sessions, closes, half-days).

Wraps pandas_market_calendars; everything returned in UTC. Used by backfill
(enumerate valid days), labels (to-close horizon), and the live loop (curfew).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from functools import lru_cache

import pandas as pd
import pandas_market_calendars as mcal


@lru_cache(maxsize=1)
def _nyse():
    return mcal.get_calendar("NYSE")


@lru_cache(maxsize=32)
def schedule(start: date, end: date) -> pd.DataFrame:
    """NYSE schedule between dates inclusive; index = session date, cols market_open/market_close (UTC)."""
    return _nyse().schedule(start_date=str(start), end_date=str(end))


def trading_days(start: date, end: date) -> list[date]:
    sched = schedule(start, end)
    return [d.date() for d in sched.index]


def session_bounds_utc(day: date) -> tuple[datetime, datetime]:
    """(market_open, market_close) as tz-aware UTC datetimes for one session date."""
    sched = schedule(day, day)
    if sched.empty:
        raise ValueError(f"{day} is not a trading day")
    row = sched.iloc[0]
    op = row["market_open"].to_pydatetime().astimezone(UTC)
    cl = row["market_close"].to_pydatetime().astimezone(UTC)
    return op, cl


def session_close_ns(day: date) -> int:
    _, cl = session_bounds_utc(day)
    return int(cl.timestamp() * 1_000_000_000)
