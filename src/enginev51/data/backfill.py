"""Backfill library: plan + run raw-lake downloads (ticks and LETF bars).

Design contracts (see DESIGN.md / PROTOCOL.md):
- Writes ALWAYS land in `settings.raw_dir` (the primary lake). The legacy engineV5
  lake (`settings.read_roots[1]`) is consumed READ-ONLY and is never written here.
- A present partition file marks that (symbol, day, kind) complete — this is what
  makes backfill resumable. An empty session is written as a zero-row partition
  (that is the completeness marker for a genuinely empty day, not a gap). To keep
  that contract true, a session whose close is not yet past the SIP recency
  margin is never fetched or written (see `_fetch_window_final`) — otherwise a
  same-day run would freeze a truncated (or empty) partial day in forever.
- Planning is union-aware: a work item is MISSING only if no partition exists in
  ANY read root. So NVDA/TSLA days already in the legacy lake are skipped, while
  AMD/MU (no legacy ticks) and TSLA's quote-only gaps surface as work.
- All tick reads/writes go through `store`, which tolerates the reduced legacy
  schema; here we only ever *write* full-schema rows normalized by AlpacaHist.

HEALING A BAD PARTITION (code review 2026-07-28 B4/B5). Presence-is-complete has
no way back once a truncated / empty / corrupt PRIMARY day is on disk: plain
`force=True` still skips anything the primary lake already holds. Two OPT-IN
knobs close that, and neither changes any default:

- `force_overwrite=True` — every session in range is refetched and the PRIMARY
  partition is REWRITTEN, whatever exists in either root. This is the explicit
  heal path (CLI: `--force-overwrite`); it is the only way to replace a primary
  file short of deleting it.
- `require_complete=True` — planning switches from "a file exists" to CONTENT
  completeness (`partition_complete`): rows must reach the session close window
  (`max(ts) >= close - CLOSE_EPSILON_S`, the close coming from the NYSE calendar
  so listed half-days resolve to their real 13:00 ET close), and a zero-row
  partition only counts when an `.empty_ok` sidecar declares it intentional
  (store module docs). Corrupt/unreadable ⇒ incomplete.

COMPATIBILITY, deliberately: both default to False, so the existing lake is
never re-verdicted. Completeness is a forward pull-planning decision (and the
heal path), never a retroactive judgment that re-downloads history.
"""

from __future__ import annotations

import shutil
from datetime import UTC, date, datetime, timedelta
from datetime import time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import structlog

from enginev51.config import Settings, get_research_config
from enginev51.data import calendar as cal
from enginev51.data import store
from enginev51.data.alpaca_hist import AlpacaHist

log = structlog.get_logger(__name__)

ET = ZoneInfo("America/New_York")

TICK_KINDS: tuple[str, ...] = ("trades", "quotes")
STATUS_KINDS: tuple[str, ...] = ("trades", "quotes", "bars1m", "event_bars1s")

# A work item is (symbol, session_iso "YYYY-MM-DD", kind).
WorkItem = tuple[str, str, str]

# Extended-hours envelope used only when rth_only=False (04:00-20:00 ET).
_EXT_OPEN_ET = dtime(4, 0)
_EXT_CLOSE_ET = dtime(20, 0)

NS_PER_S = 1_000_000_000

# Content-completeness tolerance (B4): a tick partition covers its session once
# max(ts) reaches within this many seconds of the RTH close. Five minutes is the
# closing-auction run-in — every liquid RTH name prints and quotes throughout it,
# and a partition truncated by the SIP recency clamp always stops far earlier.
# The bound is stated against the RTH close, so it also holds for extended-hours
# fetches (which run past it to 20:00 ET).
CLOSE_EPSILON_S = 300


# --------------------------------------------------------------------------- disk

def disk_floor_guard(settings: Settings) -> float:
    """Abort if free disk on the data_dir drive is below the research floor.

    Called before every fetch batch. Returns free GiB (for logging/tests).
    """
    floor_gb = get_research_config().disk_floor_gb
    probe = settings.data_dir
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    free_gb = shutil.disk_usage(probe).free / (1024**3)
    if free_gb < floor_gb:
        raise RuntimeError(
            f"disk floor breached: {free_gb:.1f} GiB free < {floor_gb:.1f} GiB floor "
            f"on {probe}"
        )
    return free_gb


# --------------------------------------------------------------------------- ticks

def partition_complete(
    root: Path, settings: Settings, kind: str, symbol: str, part: str
) -> bool:
    """CONTENT completeness of one tick partition under one lake root (B4/B5).

    Complete iff the file exists AND either
      * it carries rows through the session close window —
        ``max(ts) >= session_close - CLOSE_EPSILON_S``, the close taken from the
        NYSE calendar so a listed half-day resolves to its real 13:00 ET close; or
      * it is zero-row AND an ``.empty_ok`` sidecar declares that intentional
        (store module docs).

    Anything unreadable, truncated short of the close window, or silently empty is
    INCOMPLETE. Used only by the opt-in ``require_complete`` planning path and the
    heal path — never by the default presence check, which is unchanged.
    """
    feed = settings.data_feed_type
    path = store.partition_path(root, feed, kind, symbol, part)
    if not path.exists():
        return False
    try:
        max_ts = store.partition_max_ts(path)
    except Exception as exc:  # corrupt/unreadable file is NOT a completeness marker
        log.warning("partition_unreadable", file=str(path), error=str(exc))
        return False
    if max_ts is None:  # zero rows: complete only when declared empty on purpose
        return store.is_empty_ok(root, feed, kind, symbol, part)
    try:
        close = _session_bounds(date.fromisoformat(part), rth_only=True)[1]
    except ValueError:  # not a trading day -> no close window to reach
        return True
    return max_ts >= int(close.timestamp()) * NS_PER_S - CLOSE_EPSILON_S * NS_PER_S


def _covered(
    settings: Settings,
    kind: str,
    symbol: str,
    part: str,
    *,
    roots: tuple[Path, ...],
    require_complete: bool,
) -> bool:
    """True when ``roots`` already cover this item (presence, or content if asked)."""
    feed = settings.data_feed_type
    for root in roots:
        if require_complete:
            if partition_complete(root, settings, kind, symbol, part):
                return True
        elif store.partition_exists(root, feed, kind, symbol, part):
            return True
    return False


def plan_ticks(
    settings: Settings,
    symbols: list[str] | tuple[str, ...],
    start_date: date,
    end_date: date,
    force: bool = False,
    now: datetime | None = None,
    force_overwrite: bool = False,
    require_complete: bool = False,
) -> list[WorkItem]:
    """Enumerate MISSING (symbol, session, kind) tick work items over a date range.

    For each NYSE session in [start_date, end_date] and each of (trades, quotes),
    an item is emitted iff no partition exists in ANY read root. One planner covers
    AMD/MU from scratch, NVDA/TSLA forward extension, and TSLA's quote-only gaps.

    force=True treats every session as missing UNLESS the PRIMARY lake already has
    it — used to re-download legacy-lake days whose exports were stripped of
    condition codes (the primary copy then shadows the legacy one on reads).

    force_overwrite=True plans EVERY session in range regardless of what is on
    disk; the runner then rewrites the primary partition (the heal path for a
    truncated/corrupt primary day — B4). Implies force.

    require_complete=True swaps the presence test for ``partition_complete``
    (rows through the close window; zero rows only with an ``.empty_ok``
    sidecar). OFF by default: the existing lake is never re-verdicted.

    Sessions whose RTH close is not yet ``sip_recency_margin_minutes`` in the
    past are NEVER planned — fetching them now would write a truncated partition
    that the presence-is-complete contract then freezes forever (F4; see
    ``_fetch_window_final``). That guard holds under force_overwrite too.
    """
    days = [
        d
        for d in cal.trading_days(start_date, end_date)
        if _fetch_window_final(
            _session_bounds(d, rth_only=True)[1],
            settings.sip_recency_margin_minutes,
            now,
        )
    ]
    work: list[WorkItem] = []
    for sym in symbols:
        s = sym.upper()
        for d in days:
            part = d.isoformat()
            for kind in TICK_KINDS:
                if force_overwrite:
                    work.append((s, part, kind))
                    continue
                roots = (settings.raw_dir,) if force else settings.read_roots
                if not _covered(
                    settings, kind, s, part,
                    roots=roots, require_complete=require_complete,
                ):
                    work.append((s, part, kind))
    return work


def _session_bounds(day: date, rth_only: bool) -> tuple[datetime, datetime]:
    if rth_only:
        return cal.session_bounds_utc(day)
    # Extended-hours envelope (matches nothing in the legacy lake; opt-in only).
    op = datetime.combine(day, _EXT_OPEN_ET, tzinfo=ET).astimezone(UTC)
    cl = datetime.combine(day, _EXT_CLOSE_ET, tzinfo=ET).astimezone(UTC)
    return op, cl


def _fetch_window_final(end: datetime, margin_minutes: int, now: datetime | None = None) -> bool:
    """True when a fetch ending at ``end`` can no longer be recency-clamped.

    AlpacaHist clamps SIP request ends to now − sip_recency_margin_minutes, so a
    session fetched before ``end + margin`` comes back TRUNCATED (or empty). A
    partition file is the completeness marker (module contract above), which
    makes writing a truncated day a SILENT PERMANENT HOLE: the file exists, so
    every later plan/run skips it forever — and the missing region is the close,
    exactly where the MOC/region detectors look (code review 2026-07-17 F4).
    Both the planner and the runner therefore refuse non-final sessions.
    ``now`` is injectable for tests only.
    """
    if now is None:
        now = datetime.now(UTC)
    return now - timedelta(minutes=margin_minutes) >= end


def _fetch_tick_rows(
    api: AlpacaHist, kind: str, symbol: str, start: datetime, end: datetime
) -> list[dict]:
    feed = "sip"
    pages = (
        api.fetch_trades(symbol, start, end, feed=feed)
        if kind == "trades"
        else api.fetch_quotes(symbol, start, end, feed=feed)
    )
    rows: list[dict] = []
    for page in pages:
        rows.extend(page)
    return rows


def run_ticks(
    settings: Settings,
    work: list[WorkItem],
    rth_only: bool = True,
    api: AlpacaHist | None = None,
    force: bool = False,
    now: datetime | None = None,
    force_overwrite: bool = False,
    require_complete: bool = False,
    mark_empty_ok: bool = False,
) -> int:
    """Fetch and store every work item. Writes to settings.raw_dir only.

    Idempotent: re-checks partition existence (across all roots) immediately before
    each fetch, so a resumed run never re-downloads a completed day. An empty
    session is written as a zero-row partition (the completeness marker).
    Sessions whose fetch window is not yet final (see ``_fetch_window_final``)
    are skipped WITHOUT writing — a truncated fetch must never become the
    completeness marker (F4). Returns the number of partitions written this call.

    force_overwrite=True skips every skip-if-exists guard and REWRITES the primary
    partition — the heal path for a truncated/empty/corrupt primary day (B4). The
    not-final guard still applies: healing must never install a fresh truncation.
    require_complete=True re-checks CONTENT completeness instead of presence.
    mark_empty_ok=True declares any zero-row result of THIS run intentional
    (writes the ``.empty_ok`` sidecar); default off, so writes are unchanged.
    """
    feed = settings.data_feed_type
    own_api = api is None
    if own_api:
        api = AlpacaHist(settings)
    written = 0
    try:
        for sym, part, kind in work:
            # Skip-if-exists guard again (idempotent resume). Under force, only a
            # PRIMARY-lake copy skips (legacy stripped partitions get re-fetched);
            # under force_overwrite nothing skips.
            if not force_overwrite:
                roots = (settings.raw_dir,) if force else settings.read_roots
                if _covered(
                    settings, kind, sym, part,
                    roots=roots, require_complete=require_complete,
                ):
                    event = "skip_exists_primary" if force else "skip_exists"
                    log.info(event, symbol=sym, day=part, kind=kind)
                    continue
            day = date.fromisoformat(part)
            start, end = _session_bounds(day, rth_only)
            if not _fetch_window_final(end, settings.sip_recency_margin_minutes, now):
                log.info("skip_not_final", symbol=sym, day=part, kind=kind)
                continue
            disk_floor_guard(settings)  # before every fetch batch
            rows = _fetch_tick_rows(api, kind, sym, start, end)
            store.write_partition(
                settings.raw_dir, feed, kind, sym, part, rows, empty_ok=mark_empty_ok
            )
            written += 1
            log.info("tick_partition", symbol=sym, day=part, kind=kind, rows=len(rows))
    finally:
        if own_api:
            api.close()
    return written


# ----------------------------------------------------------------------- LETF bars

def _month_range(start: date, end: date) -> list[str]:
    """Inclusive list of 'YYYY-MM' month keys from start..end."""
    y, m = start.year, start.month
    out: list[str] = []
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def _month_bounds_utc(month: str) -> tuple[datetime, datetime]:
    y, m = (int(x) for x in month.split("-"))
    start = datetime(y, m, 1, tzinfo=UTC)
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    end = datetime(ny, nm, 1, tzinfo=UTC)
    return start, end


def plan_letf_bars(
    settings: Settings,
    symbols: tuple[str, ...] = ("SOXL", "SOXS", "TQQQ", "SQQQ"),
    start: str = "2023-07-01",
) -> list[tuple[str, str]]:
    """Plan monthly bars1m work items (symbol, 'YYYY-MM') for the LETF deploy lens.

    A month is planned iff its partition is absent in every read root, EXCEPTION:
    the current (in-progress) month is ALWAYS planned so it can be re-fetched /
    overwritten as new bars accrue — a partial month file is not "complete".
    """
    feed = settings.data_feed_type
    start_d = date.fromisoformat(start)
    today = datetime.now(UTC).date()
    cur_month = f"{today.year:04d}-{today.month:02d}"
    work: list[tuple[str, str]] = []
    for sym in symbols:
        s = sym.upper()
        for month in _month_range(start_d, today):
            present = any(
                store.partition_exists(root, feed, "bars1m", s, month)
                for root in settings.read_roots
            )
            if not present or month == cur_month:
                work.append((s, month))
    return work


def run_letf_bars(
    settings: Settings,
    work: list[tuple[str, str]],
    api: AlpacaHist | None = None,
) -> int:
    """Fetch monthly 1-min bars a month at a time and write monthly partitions.

    The current month is (re)written unconditionally — see plan_letf_bars. Returns
    the number of partitions written.
    """
    feed = settings.data_feed_type
    # Group by month so fetch_bars_multi issues one multi-symbol request per month.
    by_month: dict[str, list[str]] = {}
    for sym, month in work:
        by_month.setdefault(month, []).append(sym.upper())
    own_api = api is None
    if own_api:
        api = AlpacaHist(settings)
    written = 0
    try:
        for month in sorted(by_month):
            syms = sorted(set(by_month[month]))
            disk_floor_guard(settings)  # before every fetch batch
            start, end = _month_bounds_utc(month)
            # VINTAGE PIN (S8). fetch_bars_multi now defaults to adjustment="raw";
            # every bars1m partition this writer has ever produced (the LETF lake
            # and the R2-A OOS names via scripts/backfill_bars1m_oos.py) was fetched
            # under the old adjustment="all" default, so the pin is EXPLICIT here to
            # keep new partitions the same vintage as the ones on disk. Switching
            # this lake to raw is a data migration, not a refactor — it needs a
            # full refetch + ledger entry, exactly as scripts/refetch_bars1m_raw.py
            # did for the signal-symbol bars1m (SIM_AUDIT_2026-07-21 F1).
            result = api.fetch_bars_multi(syms, start, end, feed="sip", adjustment="all")
            for s in syms:
                rows = result.get(s, [])
                store.write_partition(settings.raw_dir, feed, "bars1m", s, month, rows)
                written += 1
                log.info("letf_bars_partition", symbol=s, month=month, rows=len(rows))
    finally:
        if own_api:
            api.close()
    return written


# --------------------------------------------------------------------------- status

def status(settings: Settings) -> dict[tuple[str, str], dict]:
    """Per (symbol, kind): first/last partition, count present, count empty, and a
    roots breakdown (files under each read root). Empty = zero-row partitions.
    """
    feed = settings.data_feed_type
    roots = settings.read_roots

    # Discover the (symbol, kind) universe across all roots.
    keys: set[tuple[str, str]] = set()
    for root in roots:
        for kind in STATUS_KINDS:
            d = root / feed / kind
            if d.is_dir():
                for sym_dir in d.iterdir():
                    if sym_dir.is_dir():
                        keys.add((sym_dir.name.upper(), kind))

    out: dict[tuple[str, str], dict] = {}
    for sym, kind in sorted(keys):
        # Primary-first dedup: first root containing a given partition filename wins.
        winning: dict[str, Path] = {}
        roots_breakdown: dict[str, int] = {}
        for root in roots:
            d = root / feed / kind / sym
            count = 0
            if d.is_dir():
                for f in d.glob("*.parquet"):
                    count += 1
                    winning.setdefault(f.name, f)
            roots_breakdown[str(root)] = count
        parts = sorted(winning)
        empty = 0
        for name in parts:
            try:
                if store.partition_height(winning[name]) == 0:
                    empty += 1
            except Exception as exc:  # unreadable file shouldn't crash status
                log.warning("status_unreadable", file=str(winning[name]), error=str(exc))
        out[(sym, kind)] = {
            "first": parts[0][: -len(".parquet")] if parts else None,
            "last": parts[-1][: -len(".parquet")] if parts else None,
            "present": len(parts),
            "empty": empty,
            "roots": roots_breakdown,
        }
    return out
