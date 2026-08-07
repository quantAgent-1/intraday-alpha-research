"""Scheduled-macro / earnings HARD-GATE calendar (framework P2).

A *static, config-driven* economic + TSLA-event calendar that sets a hard
reversion-OFF window around scheduled events — **zero model risk, zero look-ahead**
(everything here is knowable in advance, so there is no leakage). This is the most
defensible piece of the whole framework on first principles alone (Lee 2012: FOMC is
the single strongest jump predictor; macro releases raise jump probability ~22%;
~86% of intraday jumps occur before 11:00 ET).

What it covers:
* **Recurring macro releases** — FOMC decision (14:00 ET), CPI / NFP / jobless-claims
  (08:30 ET). Modeled as a window ``[release - pre, release + post]`` in ET.
* **TSLA event days** — earnings dates (whole RTH session OFF) and ad-hoc event days
  (delivery numbers, shareholder meeting, AI/robotaxi day).
* **Opening-hour caution** — the first ~90 min of RTH (jumps are front-loaded).

It is intentionally a hand-maintained list (a few dates/quarter); the dates below are
SEED/PLACEHOLDER values the user must confirm/update (FOMC/CPI/NFP schedules and TSLA's
next earnings date change every quarter). ``calendar.json`` next to this module, if
present, overrides the built-in defaults so the user can edit dates without touching
code.

Output is a small ``BlackoutState`` the gate folds into ``flow_context`` as
``regime_blackout`` — a SECOND flag distinct from the news ``not_fade`` gate. Like
everything in this build it is DISPLAY + RECORD ONLY (never changes a decision yet).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)

_ET = ZoneInfo("America/New_York")
# v5.1: local-file override discovery kept verbatim — no DB / config / network.
# `calendar.json` is looked up next to this module and simply no-ops (defaults
# used) when absent, so the module stays pure-compute in this repo.
_CFG_PATH = Path(__file__).with_name("calendar.json")


# ----------------------------------------------------------------------------
# SEED data — USER MUST CONFIRM/UPDATE each quarter (placeholders, not authoritative).
# Recurring macro releases are given as explicit dates so there is no ambiguity; a
# longer-lived deployment should refresh these from a calendar source.
# ----------------------------------------------------------------------------

# (date ISO, release time ET, label). Pre/post windows applied per-kind below.
_DEFAULT_MACRO: list[tuple[str, str, str]] = [
    # --- FOMC decision days (14:00 ET) — SEED, confirm against the Fed calendar
    ("2026-06-17", "14:00", "FOMC"),
    ("2026-07-29", "14:00", "FOMC"),
    ("2026-09-16", "14:00", "FOMC"),
    # --- CPI releases (08:30 ET) — SEED
    ("2026-06-10", "08:30", "CPI"),
    ("2026-07-14", "08:30", "CPI"),
    # --- Nonfarm payrolls (08:30 ET, first Friday) — SEED
    ("2026-06-05", "08:30", "NFP"),
    ("2026-07-02", "08:30", "NFP"),
    # Weekly jobless claims (Thursdays 08:30 ET) are added programmatically below.
]

# TSLA event days (whole RTH session treated as elevated) — SEED, confirm.
_DEFAULT_TSLA_EVENTS: list[tuple[str, str]] = [
    ("2026-07-22", "TSLA Q2 earnings (after close)"),  # SEED — confirm exact date
    ("2026-07-02", "TSLA Q2 deliveries"),              # SEED
]

# Window sizes (minutes) by macro kind. Negative = before the release.
_MACRO_WINDOWS: dict[str, tuple[int, int]] = {
    "FOMC": (15, 60),       # 15 min before → 60 min after the 14:00 decision
    "CPI": (5, 30),         # pre-open release; mostly gates the 09:30 open
    "NFP": (5, 30),
    "JOBLESS": (5, 20),
    "DEFAULT": (5, 30),
}

# Opening-hour caution window after the RTH open (minutes).
_OPENING_CAUTION_MIN = 90
_RTH_OPEN = time(9, 30)
_RTH_CLOSE = time(16, 0)


@dataclass(slots=True)
class BlackoutWindow:
    start_ns: int
    end_ns: int
    label: str
    kind: str  # macro | earnings | event | opening

    def contains(self, ts_ns: int) -> bool:
        return self.start_ns <= ts_ns <= self.end_ns


@dataclass(slots=True, frozen=True)
class BlackoutState:
    active: bool
    label: str | None
    kind: str | None
    ends_in_s: int | None  # seconds until the active window ends (None if inactive)

    def as_flow_context(self) -> dict[str, Any]:
        return {
            "regime_blackout": self.active,
            "regime_blackout_label": self.label,
            "regime_blackout_kind": self.kind,
            "regime_blackout_ends_in_s": self.ends_in_s,
        }


def _et_dt_to_ns(d: date, t: time) -> int:
    dt = datetime.combine(d, t, tzinfo=_ET)
    return int(dt.timestamp() * 1_000_000_000)


def _weekly_jobless_claims(start: date, weeks: int = 8) -> list[tuple[str, str, str]]:
    """Thursdays 08:30 ET for the next `weeks` weeks (jobless claims are weekly)."""
    out: list[tuple[str, str, str]] = []
    d = start
    # advance to the next Thursday (weekday 3)
    d += timedelta(days=(3 - d.weekday()) % 7)
    for _ in range(weeks):
        out.append((d.isoformat(), "08:30", "JOBLESS"))
        d += timedelta(days=7)
    return out


@dataclass
class MacroCalendar:
    """Builds blackout windows from the macro + TSLA-event lists and answers
    ``blackout(now_ns) -> BlackoutState`` in O(#windows) (a handful)."""

    macro: list[tuple[str, str, str]] = field(default_factory=list)
    tsla_events: list[tuple[str, str]] = field(default_factory=list)
    opening_caution_min: int = _OPENING_CAUTION_MIN
    _windows: list[BlackoutWindow] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self._build()

    # ---------------------------------------------------------------- build

    def _build(self) -> None:
        windows: list[BlackoutWindow] = []
        for iso, hhmm, label in self.macro:
            try:
                d = date.fromisoformat(iso)
                hh, mm = (int(x) for x in hhmm.split(":"))
                t = time(hh, mm)
            except (ValueError, TypeError):
                log.warning("calendar: bad macro row %r", (iso, hhmm, label))
                continue
            pre, post = _MACRO_WINDOWS.get(label.upper(), _MACRO_WINDOWS["DEFAULT"])
            rel = _et_dt_to_ns(d, t)
            windows.append(
                BlackoutWindow(
                    start_ns=rel - pre * 60 * 1_000_000_000,
                    end_ns=rel + post * 60 * 1_000_000_000,
                    label=label,
                    kind="macro",
                )
            )
        for iso, label in self.tsla_events:
            try:
                d = date.fromisoformat(iso)
            except (ValueError, TypeError):
                log.warning("calendar: bad tsla event row %r", (iso, label))
                continue
            # Whole RTH session for TSLA event days.
            windows.append(
                BlackoutWindow(
                    start_ns=_et_dt_to_ns(d, _RTH_OPEN),
                    end_ns=_et_dt_to_ns(d, _RTH_CLOSE),
                    label=label,
                    kind="earnings" if "earnings" in label.lower() else "event",
                )
            )
        windows.sort(key=lambda w: w.start_ns)
        self._windows = windows

    # ---------------------------------------------------------------- query

    def _opening_window(self, now_ns: int) -> BlackoutWindow | None:
        """Opening-hour caution for the session containing now (computed on the fly)."""
        now_et = datetime.fromtimestamp(now_ns / 1e9, tz=_ET)
        if now_et.weekday() >= 5:
            return None
        d = now_et.date()
        start = _et_dt_to_ns(d, _RTH_OPEN)
        end = start + self.opening_caution_min * 60 * 1_000_000_000
        if start <= now_ns <= end:
            return BlackoutWindow(start, end, "RTH open caution", "opening")
        return None

    def blackout(self, now_ns: int) -> BlackoutState:
        active: BlackoutWindow | None = None
        for w in self._windows:
            if w.contains(now_ns):
                active = w
                break
        if active is None:
            active = self._opening_window(now_ns)
        if active is None:
            return BlackoutState(active=False, label=None, kind=None, ends_in_s=None)
        return BlackoutState(
            active=True,
            label=active.label,
            kind=active.kind,
            ends_in_s=max(0, int((active.end_ns - now_ns) / 1e9)),
        )

    def windows(self) -> list[BlackoutWindow]:
        return list(self._windows)


def load_calendar(*, with_weekly_jobless: bool = True, today: date | None = None) -> MacroCalendar:
    """Construct the calendar from ``calendar.json`` if present, else built-in seeds.

    ``calendar.json`` schema (all optional)::

        {"macro": [["2026-06-17","14:00","FOMC"], ...],
         "tsla_events": [["2026-07-22","TSLA Q2 earnings"], ...],
         "opening_caution_min": 90}
    """
    macro = list(_DEFAULT_MACRO)
    tsla = list(_DEFAULT_TSLA_EVENTS)
    opening = _OPENING_CAUTION_MIN
    if _CFG_PATH.exists():
        try:
            cfg = json.loads(_CFG_PATH.read_text())
            macro = [tuple(r) for r in cfg.get("macro", macro)]
            tsla = [tuple(r) for r in cfg.get("tsla_events", tsla)]
            opening = int(cfg.get("opening_caution_min", opening))
            log.info("calendar: loaded overrides from %s", _CFG_PATH)
        except (ValueError, OSError, TypeError) as e:
            log.warning("calendar: failed to read %s (%r) — using defaults", _CFG_PATH, e)
    if with_weekly_jobless:
        macro = macro + _weekly_jobless_claims(today or date.today())
    return MacroCalendar(macro=macro, tsla_events=tsla, opening_caution_min=opening)
