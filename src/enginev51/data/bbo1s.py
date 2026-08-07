"""Databento BBO-1s (1-second subsampled top-of-book) acquisition and parse — a
registered data-source extension for the M6 ``moc_imbalance_v1`` family (PROTOCOL
v6.1, ledger M6 2026-07-16).

Purpose: an ENTRY-FILL source for ``backtest/auction_replay.py`` that is
independent of the tick quote tape. The MOC event replay needs only a prevailing
quote to cross at signal+latency (a taker market fill) and the closing-cross price
for the exit — it never needs the trade tape. The 1-second BBO gives exactly that
prevailing quote at 1s granularity: coarser than tick, but an UNBIASED sample of
the prevailing book (it is the actual last BBO as of each 1s boundary, not an
interpolation), and available over the full 2020→2026 span where the tick tape is
not. See ``auction_replay.tape_from_bbo`` for the SessionTape adapter.

WHAT THIS BOOK IS (code review 2026-07-17 F5): the XNAS.ITCH ``bbo-1s`` schema is
Nasdaq's OWN top-of-book, NOT the consolidated SIP NBBO the tick quote tape
carries. On Nasdaq-listed megacaps in the closing window the two are usually
close, but they are different economic objects — fills priced off this book must
be labeled XNAS TOB, and XNAS-entry nets must not be pooled with SIP-NBBO-entry
nets without an explicit adjustment/bridge arm.

Three jobs, cleanly separated so nothing but ``download_bbo1s`` ever touches the
network (tests mock the network entirely):

1. ``download_bbo1s`` — pull the XNAS.ITCH ``bbo-1s`` schema from Databento
   Historical, one request per (symbol, month), normalizing each response into
   compact parquet partitions (resumable, atomic). A COST GUARD queries the
   metadata endpoint first, logs the quoted USD cost, and aborts before any bytes
   are downloaded if the projected total exceeds ``max_cost`` (default $75).

2. ``load_bbo_session`` — read one (symbol, session)'s 1s BBO rows from those
   partitions as a normalized, sane-filtered (bid>0 & ask>bid), ts-sorted polars
   frame, or ``None`` when the partition is absent.

Databento ``bbo-1s`` schema field mapping (XNAS.ITCH). The DBN record is
``BBOMsg`` — an MBP-1-shaped top-of-book snapshot taken at each 1-second boundary.
Verified against ``databento_dbn.BBOMsg._ordered_fields``:
``[ts_recv, ts_event, rtype, publisher_id, instrument_id, side, price, size,
flags, sequence, bid_px_00, ask_px_00, bid_sz_00, ask_sz_00, bid_ct_00,
ask_ct_00]``. ``to_df(price_type="float", pretty_ts=True)`` yields dollar prices
and UTC-datetime ``ts_recv``/``ts_event`` columns.

    our column    databento field   meaning
    -----------   ---------------   ------------------------------------------
    ts         <- ts_recv          <- the 1-second SUBSAMPLE boundary (the instant
                                      the snapshot represents). Falls back to
                                      ts_event only if ts_recv is absent.
    bid        <- bid_px_00         <- best (level-0) bid price, dollars
    ask        <- ask_px_00         <- best (level-0) ask price, dollars
    bid_size   <- bid_sz_00         <- best bid displayed size (shares)
    ask_size   <- ask_sz_00         <- best ask displayed size (shares)

Notes on the mapping (documented so the parse is auditable):
  * ``ts_recv`` is chosen as the canonical timestamp because a bbo-1s record at
    ``ts_recv = T`` IS the book as of second boundary ``T``; a prevailing-quote
    lookup ``searchsorted(ts, exec_ts)`` then returns the correct 1s snapshot.
  * The ``price``/``size``/``side`` trade fields of ``BBOMsg`` (last trade in the
    interval) are intentionally DROPPED — the auction replay's entry uses quotes
    only, and the exit is the official cross, so trade info is unused.
  * Zero/crossed snapshots (bid<=0 or ask<=bid) are kept on disk verbatim and
    filtered at read time in ``load_bbo_session`` (a fill must never cross a broken
    book — same discipline as ``backtest/tape.load_session_tape``).
"""

from __future__ import annotations

import datetime as _dt
import os
from datetime import date, timedelta
from pathlib import Path

import polars as pl
import structlog

from enginev51.config import PROJECT_ROOT, Settings
from enginev51.data.noii import (  # ET session-boundary helpers (UTC-ns)
    coverage_floor_ns,
    et_ns,
)

log = structlog.get_logger(__name__)

DATASET = "XNAS.ITCH"
SCHEMA = "bbo-1s"

DEFAULT_BBO_DIR = PROJECT_ROOT / "data" / "raw" / "bbo1s"

# Normalized on-disk schema. UTC-ns ``ts``; prices in dollars; sizes as floats.
BBO_SCHEMA: dict[str, pl.DataType] = {
    "ts": pl.Int64,
    "bid": pl.Float64,
    "ask": pl.Float64,
    "bid_size": pl.Float64,
    "ask_size": pl.Float64,
}

# End-month coverage floor (code review 2026-07-28 B6): a monthly partition only
# COVERS its request's end day once its last 1s snapshot reaches the close window.
# The auction replay prices entries right up to 16:00 ET, so a partition that stops
# mid-session is not coverage — and the calendar-date test it replaces would lock
# that partial session in forever behind skip-exists.
# 60 s -> 300 s (code review 2026-08-01 FIX 6), matching noii's margin: a thin book
# whose LAST 1s snapshot lands a few minutes before the bell is normal, and a 60 s
# floor would condemn the whole month to a re-download on every single run. With
# credits nearly exhausted, a perpetual whole-month refetch is the expensive failure;
# 5 minutes is still deep inside the closing window this family reads.
CLOSE_MARGIN_S = 5 * 60

_MAX_COST_USD = 75.0


# --------------------------------------------------------------------------- time


def _month_range(start: date, end: date) -> list[str]:
    """Inclusive 'YYYY-MM' month keys spanning [start, end]."""
    y, m = start.year, start.month
    out: list[str] = []
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def _month_bounds(month: str) -> tuple[str, str]:
    """(inclusive-start-date, exclusive-end-date) ISO strings for a 'YYYY-MM' key.

    Databento ``get_range`` end is exclusive, so we pass the first day of the NEXT
    month — the whole calendar month in one request.
    """
    y, m = (int(x) for x in month.split("-"))
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y:04d}-{m:02d}-01", f"{ny:04d}-{nm:02d}-01"


# --------------------------------------------------------------------------- paths


def bbo_root(out_dir: str | Path | None = None) -> Path:
    """Resolve the BBO lake root; relative paths hang off the project root."""
    if out_dir is None:
        return DEFAULT_BBO_DIR
    p = Path(out_dir)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def partition_path(root: Path, symbol: str, month: str) -> Path:
    return root / symbol.upper() / f"{month}.parquet"


def _write_atomic(df: pl.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".parquet.tmp")
    df.write_parquet(tmp, compression="zstd")
    os.replace(tmp, path)
    return path


# --------------------------------------------------------------------------- parse


def normalize_bbo_df(df: pl.DataFrame) -> pl.DataFrame:
    """Map a Databento ``bbo-1s`` ``to_df()`` frame onto ``BBO_SCHEMA``.

    Tolerant of the two ways ``to_df`` can present the snapshot timestamp (a
    ``ts_recv`` column, or a datetime index materialized as ``ts_recv``) and of a
    fallback to ``ts_event``. Prices/sizes are the level-0 top-of-book fields.
    Kept pure so tests exercise it with a hand-built frame — no databento import
    required.
    """
    cols = set(df.columns)

    def _ts_expr() -> pl.Expr:
        src = "ts_recv" if "ts_recv" in cols else "ts_event"
        c = pl.col(src)
        # Datetime (any unit / tz, as `to_df(pretty_ts=True)` yields) -> UTC ns int;
        # an already-integer epoch-ns column passes straight through.
        if isinstance(df.schema.get(src), pl.Datetime):
            return c.dt.cast_time_unit("ns").cast(pl.Int64).alias("ts")
        return c.cast(pl.Int64).alias("ts")

    def _num(name: str) -> pl.Expr:
        if name in cols:
            return pl.col(name).cast(pl.Float64)
        return pl.lit(None, dtype=pl.Float64)

    out = df.select(
        _ts_expr(),
        _num("bid_px_00").alias("bid"),
        _num("ask_px_00").alias("ask"),
        _num("bid_sz_00").alias("bid_size"),
        _num("ask_sz_00").alias("ask_size"),
    )
    return out.select(list(BBO_SCHEMA)).sort("ts")


def load_bbo_session(
    symbol: str, session_iso: str, *, out_dir: str | Path | None = None
) -> pl.DataFrame | None:
    """One (symbol, session)'s 1s BBO rows as a normalized polars frame.

    Reads the (symbol, month) partition written by ``download_bbo1s``, restricts to
    the ET session day (midnight-to-midnight ET), applies the fill sanity filter
    (bid>0 AND ask>bid — never cross a broken book, same rule as
    ``backtest/tape``), and returns a ``BBO_SCHEMA`` frame sorted by ``ts``. Returns
    ``None`` when the partition does not exist at all (so callers can distinguish
    "no data downloaded" from "empty/filtered session"), or when the filtered frame
    is empty.
    """
    root = bbo_root(out_dir)
    month = session_iso[:7]
    path = partition_path(root, symbol, month)
    if not path.exists():
        return None
    lo = et_ns(session_iso, 0, 0, 0)  # midnight ET (inclusive)
    hi = et_ns((date.fromisoformat(session_iso) + timedelta(days=1)).isoformat(), 0, 0, 0)
    df = pl.read_parquet(path)
    if df.height == 0:
        return None
    df = df.filter(
        (pl.col("ts") >= lo)
        & (pl.col("ts") < hi)
        & (pl.col("bid") > 0.0)
        & (pl.col("ask") > pl.col("bid"))
    ).sort("ts")
    return df if df.height else None


# --------------------------------------------------------------------------- download


def _day_condition(rows: object, day_iso: str) -> str:
    """The vendor ``condition`` for ``day_iso`` in a Databento
    ``get_dataset_condition`` response (rows of ``{date, condition, ...}``), or
    ``"absent"`` when that day has no row at all. Tolerant of dict rows (the real
    API shape, ``list[dict[str, str | None]]``) and attribute-style objects, so
    tests can hand-build either.
    """
    for r in rows or []:
        d = r.get("date") if isinstance(r, dict) else getattr(r, "date", None)
        if d is not None and str(d)[:10] == day_iso:
            c = (
                r.get("condition")
                if isinstance(r, dict)
                else getattr(r, "condition", None)
            )
            return str(c) if c else "absent"
    return "absent"


def _end_day_available(
    client: object, end_d: date, *, require_probe: bool = True
) -> bool:
    """Pre-flight the request's END day before fetching the month that holds it.

    Queries ``metadata.get_dataset_condition`` for ``end_d`` alone (its inclusive
    single-day range). Returns ``False`` — meaning SKIP that month, leaving its
    partition untouched to heal on a later run — on an explicit non-available
    condition (degraded/pending/missing/absent): fetching such a day writes a
    partial session that ``skip-exists`` then locks in (the 2026-07-20 incident).

    FAIL-CLOSED (code review 2026-07-28 B6), mirroring ``data/noii.py``: a
    metadata *exception* also returns ``False`` by default. Proceeding blind on a
    probe failure is exactly the case the guard exists for, and the downside is
    asymmetric — a skip costs one re-run, a partial end month is permanent.

    ESCAPE HATCH (code review 2026-08-01): ``require_probe=False`` — reached from
    the CLI as ``--skip-condition-probe`` — restores the pre-2026-08-01 fail-open
    on a probe EXCEPTION, now explicit and operator-chosen, for the case where the
    condition endpoint is down/unsupported but the data itself is fine. It does
    NOT override an explicit degraded/pending verdict: a probe that SUCCEEDS and
    says the day is bad still skips the month, whatever the flag says. The two
    failure modes therefore log distinctly (``bbo1s_condition_probe_failed`` /
    ``bbo1s_condition_probe_override`` vs ``bbo1s_day_not_available``).
    """
    day_iso = end_d.isoformat()
    try:
        rows = client.metadata.get_dataset_condition(  # type: ignore[attr-defined]
            dataset=DATASET, start_date=day_iso, end_date=day_iso
        )
    except Exception as exc:  # endpoint down / unsupported
        if not require_probe:
            log.warning(
                "bbo1s_condition_probe_override",
                dataset=DATASET,
                asof=day_iso,
                error=str(exc),
                detail=(
                    f"condition probe unavailable: {exc}; proceeding without vendor "
                    "degradation check — operator override"
                ),
            )
            return True
        log.warning(
            "bbo1s_condition_probe_failed",
            dataset=DATASET,
            asof=day_iso,
            error=str(exc),
            detail=(
                "probe raised — treated as incomplete; rerun later or pass "
                "--skip-condition-probe"
            ),
        )
        return False
    cond = _day_condition(rows, day_iso)
    if cond != "available":
        log.warning(
            "bbo1s_day_not_available",
            dataset=DATASET,
            asof=day_iso,
            condition=cond,
            detail=(
                "vendor reports degraded/pending — end month skipped so a later run "
                "can heal it (not overridable by --skip-condition-probe)"
            ),
        )
        return False
    return True


def download_bbo1s(
    settings: Settings,
    symbols: list[str] | tuple[str, ...],
    start: str,
    end: str,
    out_dir: str | Path = "data/raw/bbo1s",
    *,
    max_cost: float = _MAX_COST_USD,
    stype_in: str = "raw_symbol",
    require_condition_probe: bool = True,
    client: object | None = None,
) -> dict:
    """Download XNAS.ITCH ``bbo-1s`` for ``symbols`` over [start, end].

    One request per (symbol, month); each response is normalized to ``BBO_SCHEMA``
    and written as an atomic, resumable parquet partition under
    ``out_dir/{SYMBOL}/{YYYY-MM}.parquet`` — a present partition is skipped, so a
    re-run only fetches what is missing.

    COST GUARD (PROTOCOL: cheap historical study, ~tens of dollars): before any
    timeseries bytes are fetched, ``metadata.get_cost`` is queried for the whole
    (symbols × range) request; the quoted USD figure is logged and the run ABORTS
    if it exceeds ``max_cost`` (default $75). Mirrors ``data/noii.download_noii``.

    The API key comes from ``settings.databento_api_key`` (``.env`` only); it is
    NEVER logged or printed. A missing key raises a clear ``RuntimeError``.

    ``require_condition_probe`` (default True, the fail-closed behaviour) governs
    ONLY what happens when the vendor condition probe itself RAISES: True skips
    the end month, False proceeds and logs an operator-override warning. An
    explicit degraded/pending verdict skips the end month either way. Opt-in
    escape hatch in the shape of ``backfill.require_complete``; the CLI spells it
    ``--skip-condition-probe``.

    ``client`` is injectable (a ``databento.Historical``-shaped object) purely so
    tests can mock the network; in production it is constructed from the key.
    Returns a summary dict (quoted cost, partitions written/skipped).
    """
    api_key = settings.databento_api_key
    if not api_key:
        raise RuntimeError(
            "DATABENTO_API_KEY is not set. Put DATABENTO_API_KEY=<your key> in "
            f"{PROJECT_ROOT / '.env'} (never commit it) to acquire BBO-1s data."
        )

    syms = [s.strip().upper() for s in symbols if s.strip()]
    root = bbo_root(out_dir)
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)

    if client is None:  # pragma: no cover - real network path, never hit in tests
        import databento as db

        client = db.Historical(key=api_key)

    # ---- cost guard (metadata endpoint) ------------------------------------
    # end is exclusive; add a day so the quote covers the inclusive [start, end].
    # Clamp to the dataset's available end (avoid a 422 on not-yet-settled days).
    end_excl = (end_d + timedelta(days=1)).isoformat()
    try:
        avail_end = client.metadata.get_dataset_range(dataset=DATASET)["end"][:10]
        if end_excl > avail_end:
            end_excl = avail_end
    except Exception:
        pass
    if end_excl <= start:
        raise RuntimeError(
            f"{DATASET} {SCHEMA} not yet available for {start} (dataset ends at "
            f"{end_excl}); the session has not settled at the vendor. Retry later — "
            "nothing was downloaded and nothing should be ledgered for this session."
        )
    quoted = float(
        client.metadata.get_cost(  # type: ignore[attr-defined]
            dataset=DATASET,
            symbols=syms,
            schema=SCHEMA,
            stype_in=stype_in,
            start=start,
            end=end_excl,
        )
    )
    log.info("bbo1s_cost_quote", dataset=DATASET, schema=SCHEMA, symbols=syms,
             start=start, end=end, quoted_usd=round(quoted, 4), max_cost=max_cost)
    if quoted > max_cost:
        raise RuntimeError(
            f"Databento cost quote ${quoted:.2f} exceeds the guard ${max_cost:.2f}. "
            "Raise --max-cost only if this is expected (PROTOCOL: the BBO-1s study "
            "is meant to cost tens of dollars)."
        )

    # ---- freshness pre-flight: the request's END day at the vendor ---------
    # Only the month containing end_d can still be mid-publication; earlier months
    # are final. If XNAS.ITCH marks end_d as anything but "available" (degraded/
    # pending/missing/absent), fetching that month writes a PARTIAL session that
    # skip-exists then locks in (the 2026-07-20 incident) -- so leave that month
    # untouched and let a later run heal it. A metadata ERROR is fail-closed too
    # (B6), unless the operator passes require_condition_probe=False.
    end_month = f"{end_d.year:04d}-{end_d.month:02d}"
    end_month_ok = _end_day_available(
        client, end_d, require_probe=require_condition_probe
    )

    # ---- per (symbol, month) resumable download ----------------------------
    # Dataset ceiling for clamping the LAST month's exclusive end (a not-yet-
    # settled current month would otherwise 422). end_excl was set above.
    _avail = end_excl  # already clamped to the dataset range in the cost guard
    written = 0
    skipped = 0
    months = _month_range(start_d, end_d)
    for sym in syms:
        for month in months:
            if month == end_month and not end_month_ok:
                # End-day not published cleanly: skip the whole end month so its
                # partition is never partially rewritten (heal on a later run).
                skipped += 1
                continue
            path = partition_path(root, sym, month)
            if path.exists():
                # Present partition is final for fully-earlier months; for the
                # request's END month verify coverage through end_d (mirrors
                # noii.py — daily forward collection depends on this).
                if month != end_month:
                    skipped += 1
                    log.info("bbo1s_skip_exists", symbol=sym, month=month)
                    continue
                try:
                    have_max = (
                        pl.scan_parquet(path)
                        .select(pl.col("ts").max())
                        .collect()
                        .item()
                    )
                except Exception:
                    have_max = None  # unreadable partition -> re-fetch
                have_date = (
                    _dt.datetime.fromtimestamp(have_max / 1e9, tz=_dt.UTC)
                    .date()
                    .isoformat()
                    if have_max is not None
                    else ""
                )
                # B6: coverage means reaching the session CLOSE on end_d, not just
                # landing on its calendar date. floor=None (calendar unresolvable)
                # falls back to the date rule.
                floor_ns = coverage_floor_ns(end_d, CLOSE_MARGIN_S)
                covered = (
                    have_max is not None and have_max >= floor_ns
                    if floor_ns is not None
                    else have_date >= end_d.isoformat()
                )
                if covered:
                    skipped += 1
                    log.info("bbo1s_skip_exists", symbol=sym, month=month)
                    continue
                log.info(
                    "bbo1s_extend_partial_month",
                    symbol=sym,
                    month=month,
                    have_through=have_date,
                    need_through=end_d.isoformat(),
                )
            m_start, m_end = _month_bounds(month)
            if m_end > _avail:  # clamp the final partial month to available data
                m_end = _avail
            if m_start >= m_end:  # month entirely beyond the available range
                skipped += 1
                continue
            data = client.timeseries.get_range(  # type: ignore[attr-defined]
                dataset=DATASET,
                symbols=[sym],
                schema=SCHEMA,
                stype_in=stype_in,
                start=m_start,
                end=m_end,
            )
            raw = data.to_df(price_type='float', pretty_ts=True)
            df = _to_polars(raw)
            norm = (
                normalize_bbo_df(df) if df.height else pl.DataFrame(schema=BBO_SCHEMA)
            )
            _write_atomic(norm, path)
            written += 1
            log.info("bbo1s_partition", symbol=sym, month=month, rows=norm.height)

    return {
        "quoted_usd": round(quoted, 4),
        "partitions_written": written,
        "partitions_skipped": skipped,
        "symbols": syms,
        "months": months,
    }


def _to_polars(raw: object) -> pl.DataFrame:
    """Coerce a databento ``to_df`` result (pandas) into polars without assuming
    pandas is importable in the test path. A polars frame passes through.
    """
    if isinstance(raw, pl.DataFrame):
        return raw
    # pandas DataFrame: reset any datetime index so ts_recv/ts_event are columns.
    reset = raw.reset_index() if hasattr(raw, "reset_index") else raw  # type: ignore[attr-defined]
    return pl.from_pandas(reset)
