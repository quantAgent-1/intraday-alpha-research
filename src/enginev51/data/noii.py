"""Databento NOII (Nasdaq closing-cross Net Order Imbalance Indicator) acquisition
and parse — the data layer for the M6 `moc_imbalance_v1` family (PROTOCOL v6.1,
M3_REGISTRATION.md M6 section).

Three jobs, cleanly separated so nothing but `download_noii` ever touches the
network (tests mock the network entirely):

1. ``download_noii`` — pull the XNAS.ITCH ``imbalance`` schema from Databento
   Historical, one request per (symbol, month), and normalize each response into
   our own compact parquet partitions (resumable, atomic). A COST GUARD queries
   the metadata endpoint first, logs the quoted USD cost, and aborts before any
   bytes are downloaded if the projected total exceeds ``max_cost`` (default $60).

2. ``load_noii_session`` — read the 15:45–16:00 ET closing-cross NOII messages for
   one (symbol, session) from those partitions, as a normalized polars frame.

3. ``signal_at`` — evaluate the registered signal at 15:50:10 ET (PIT: the last
   NOII at-or-before that instant) into ``{norm_imb, side, near_price}``.

Databento ``imbalance`` schema field mapping (XNAS.ITCH / Nasdaq TotalView-ITCH
NOII message, type 'I'). Databento's ``ImbalanceMsg`` normalizes the raw ITCH
NOII fields as follows (verified against the databento-python ``ImbalanceMsg``
definition; ``to_df(pretty_px=True, pretty_ts=True)`` yields dollar prices and a
``ts_event`` UTC timestamp):

    our column          databento field            ITCH NOII field
    ----------------    -----------------------    ----------------------------
    ts               <- ts_event                <- (message timestamp, UTC ns)
    side             <- side ('B'/'S'/'N')      <- Imbalance Direction
    imbalance_shares <- total_imbalance_qty     <- Imbalance Shares (magnitude)
    paired_shares    <- paired_qty              <- Paired Shares
    near_price       <- cont_book_clr_price     <- Near (indicative clearing) Price
    far_price        <- auct_interest_clr_price <- Far (indicative clearing) Price
    ref_price        <- ref_price               <- Current Reference Price

Notes on the mapping (documented so the parse is auditable):
  * ITCH ``Imbalance Direction`` is 'B' (buy-side imbalance), 'S' (sell-side),
    'N' (no imbalance), 'O'/'P' (insufficient/paused) — Databento surfaces it in
    the ``side`` field; we keep the raw char and derive the signed direction in
    ``signal_at``. ``Imbalance Shares`` is an UNSIGNED magnitude; the sign lives
    in the direction, so ``net_imbalance_shares = sign(side) * imbalance_shares``.
  * Nasdaq's Near Price is the indicative clearing price computed against BOTH the
    continuous book and closing interest → Databento's ``cont_book_clr_price``.
    The Far Price uses closing/cross interest only → ``auct_interest_clr_price``.
  * Prices can be 0 early in the dissemination window (before an indicative
    clearing price is computable); ``signal_at`` falls back near→ref for that.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl
import structlog

from enginev51.config import PROJECT_ROOT, Settings

log = structlog.get_logger(__name__)

ET = ZoneInfo("America/New_York")
NS_PER_S = 1_000_000_000

DATASET = "XNAS.ITCH"
SCHEMA = "imbalance"

DEFAULT_NOII_DIR = PROJECT_ROOT / "data" / "raw" / "noii"

# Normalized on-disk schema. UTC-ns ``ts``; prices in dollars; share counts as
# floats (magnitudes). ``side`` carries the raw ITCH direction char.
NOII_SCHEMA: dict[str, pl.DataType] = {
    "ts": pl.Int64,
    "side": pl.Utf8,
    "imbalance_shares": pl.Float64,
    "paired_shares": pl.Float64,
    "near_price": pl.Float64,
    "far_price": pl.Float64,
    "ref_price": pl.Float64,
}

# Closing-cross NOII dissemination window (ET). Nasdaq broadcasts the closing
# cross NOII from 15:50; we keep from 15:45 for a small margin.
WINDOW_START_ET = (15, 45, 0)
WINDOW_END_ET = (16, 0, 0)

# End-month coverage floor (code review 2026-07-28 B6): a monthly partition only
# COVERS its request's end day once it carries a message at or after
# ``session_close - 5 min`` (15:55 ET on a regular session). The closing-cross
# NOII this family reads is disseminated from 15:50, so any partition stopping
# earlier is mid-session — a calendar-date test ("some row lands on end_d") would
# lock a partial closing window in forever behind skip-exists.
CLOSE_MARGIN_S = 5 * 60

_MAX_COST_USD = 60.0


# --------------------------------------------------------------------------- time


def et_ns(session_iso: str, h: int, m: int, s: int = 0) -> int:
    """UTC epoch-ns of ``h:m:s`` America/New_York on ``session_iso`` (YYYY-MM-DD)."""
    d = date.fromisoformat(session_iso)
    dt = datetime(d.year, d.month, d.day, h, m, s, tzinfo=ET)
    return int(dt.timestamp()) * NS_PER_S


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

    Databento ``get_range`` end is exclusive, so we pass the first day of the
    NEXT month — the whole calendar month in one request.
    """
    y, m = (int(x) for x in month.split("-"))
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y:04d}-{m:02d}-01", f"{ny:04d}-{nm:02d}-01"


def coverage_floor_ns(end_d: date, margin_s: int) -> int | None:
    """UTC-ns instant a partition's ``max(ts)`` must reach to COVER ``end_d`` (B6).

    Anchored on the session CLOSE of the last NYSE trading day at or before
    ``end_d``, minus ``margin_s``. Two consequences that a calendar-date test
    cannot express: a partition that stops mid-session on ``end_d`` is NOT
    coverage, and a listed half-day resolves to its real 13:00 ET close (the
    calendar wraps pandas_market_calendars) instead of a hard-coded 16:00.
    A weekend/holiday ``end_d`` falls back to the prior session's close, so a
    Saturday request is not perpetually "uncovered".

    Returns ``None`` when no session can be resolved (calendar unavailable or no
    trading day in the lookback) — callers then keep the calendar-date rule.
    ``bbo1s`` imports this, same as ``et_ns``.
    """
    # Local import: pandas_market_calendars is heavy and this module is on the
    # import path of the whole forward/basis stack, which never needs it.
    from enginev51.data import calendar as cal

    try:
        days = cal.trading_days(end_d - timedelta(days=10), end_d)
        if not days:
            return None
        close = cal.session_bounds_utc(days[-1])[1]
    except Exception:  # no calendar / not resolvable -> caller keeps the old rule
        log.warning("coverage_floor_unresolved", asof=end_d.isoformat())
        return None
    return int(close.timestamp()) * NS_PER_S - margin_s * NS_PER_S


# --------------------------------------------------------------------------- paths


def noii_root(out_dir: str | Path | None = None) -> Path:
    """Resolve the NOII lake root; relative paths hang off the project root."""
    if out_dir is None:
        return DEFAULT_NOII_DIR
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


def normalize_imbalance_df(df: pl.DataFrame) -> pl.DataFrame:
    """Map a Databento ``imbalance`` ``to_df()`` frame onto ``NOII_SCHEMA``.

    Tolerant of the two ways ``to_df`` can present the timestamp (a ``ts_event``
    column, or a datetime index materialized as ``ts_event``/``ts_recv``) and of
    missing optional columns (filled with nulls). Side is coerced to a single
    upper-case char. Kept pure so tests exercise it with a hand-built frame — no
    databento import required.
    """
    cols = set(df.columns)

    def _ts_expr() -> pl.Expr:
        src = "ts_event" if "ts_event" in cols else "ts_recv"
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

    side = (
        pl.col("side").cast(pl.Utf8).str.to_uppercase().str.slice(0, 1)
        if "side" in cols
        else pl.lit(None, dtype=pl.Utf8)
    )

    out = df.select(
        _ts_expr(),
        side.alias("side"),
        _num("total_imbalance_qty").alias("imbalance_shares"),
        _num("paired_qty").alias("paired_shares"),
        _num("cont_book_clr_price").alias("near_price"),
        _num("auct_interest_clr_price").alias("far_price"),
        _num("ref_price").alias("ref_price"),
    )
    return out.select(list(NOII_SCHEMA)).sort("ts")


def load_noii_session(
    symbol: str, session: str, *, out_dir: str | Path | None = None
) -> pl.DataFrame | None:
    """The 15:45–16:00 ET closing-cross NOII messages for one (symbol, session).

    Reads the (symbol, month) partition written by ``download_noii`` and filters
    to the ET dissemination window. Returns a ``NOII_SCHEMA`` frame sorted by
    ``ts`` (possibly empty), or ``None`` when the partition does not exist at all
    (so callers can distinguish "no data downloaded yet" from "empty window").
    """
    root = noii_root(out_dir)
    month = session[:7]
    path = partition_path(root, symbol, month)
    if not path.exists():
        return None
    lo = et_ns(session, *WINDOW_START_ET)
    hi = et_ns(session, *WINDOW_END_ET)
    df = pl.read_parquet(path)
    if df.height == 0:
        return df
    return df.filter((pl.col("ts") >= lo) & (pl.col("ts") <= hi)).sort("ts")


# --------------------------------------------------------------------------- signal


def _side_sign(side: str | None) -> int:
    """+1 buy-side imbalance, -1 sell-side, 0 for none/insufficient/unknown.

    Databento normalizes ITCH Imbalance Direction to its Side enum: 'B' (bid =
    buy-side imbalance), 'A' (ask = SELL-side imbalance), 'N' (none). Raw ITCH
    'S' is kept for robustness but real data carries 'A' (verified 2026-07-16:
    B 15,732 / A 10,980 / N 5,533 on sampled NVDA months).
    """
    if side == "B":
        return 1
    if side in ("S", "A"):
        return -1
    return 0


def signal_at(
    noii_frame: pl.DataFrame | None,
    ts_et_155010: int,
    adv20_dollars: float,
) -> dict | None:
    """The registered M6 signal at 15:50:10 ET, PIT.

    Point-in-time: the LAST NOII message at-or-before ``ts_et_155010`` governs;
    ``None`` if there is no such message (no NOII yet ⇒ no event).

    Formula (registered): ``norm_imb = net_imbalance_shares * near_price /
    ADV20_dollars`` where ``net_imbalance_shares = sign(direction) *
    imbalance_shares``. Direction = ``sign(norm_imb)`` (WITH the imbalance).

    Price fallback: ``near_price`` is used when > 0, else ``ref_price`` (the near
    indicative clearing price can be 0 before it is computable). The returned
    ``near_price`` is the price actually used in the formula, for the caller's
    entry-context / ground-truth sanity checks.

    Returns ``{"norm_imb": float, "side": int(-1|0|+1), "near_price": float}`` or
    ``None`` when there is no message at-or-before the instant. A 'N'/insufficient
    direction yields ``side=0`` and ``norm_imb=0.0`` (no tradable imbalance).
    """
    if noii_frame is None or noii_frame.height == 0:
        return None
    prior = noii_frame.filter(pl.col("ts") <= ts_et_155010)
    if prior.height == 0:
        return None
    row = prior.sort("ts").row(-1, named=True)

    sign = _side_sign(row["side"])
    near = row["near_price"]
    ref = row["ref_price"]
    price = near if (near is not None and near > 0.0) else ref
    if price is None or not price > 0.0 or adv20_dollars is None or adv20_dollars <= 0.0:
        return None
    shares = row["imbalance_shares"] or 0.0
    norm_imb = sign * float(shares) * float(price) / float(adv20_dollars)
    return {"norm_imb": norm_imb, "side": sign, "near_price": float(price)}


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
    partial closing-cross session that ``skip-exists`` then locks in (the
    2026-07-20 incident).

    FAIL-CLOSED (code review 2026-07-28 B6). A metadata *exception* also returns
    ``False`` by default. The old fail-open behaviour proceeded blind on exactly
    the failure mode the guard exists for, and the downside is asymmetric:
    skipping costs one re-run, while a partial end-month partition is permanent
    under skip-exists. Nothing is downloaded and nothing should be ledgered for
    that session.

    ESCAPE HATCH (code review 2026-08-01): ``require_probe=False`` — reached from
    the CLI as ``--skip-condition-probe`` — restores the pre-2026-08-01 fail-open
    on a probe EXCEPTION, now explicit and operator-chosen, for the case where the
    condition endpoint is down/unsupported but the data itself is fine. It does
    NOT override an explicit degraded/pending verdict: a probe that SUCCEEDS and
    says the day is bad still skips the month, whatever the flag says. The two
    failure modes therefore log distinctly (``noii_condition_probe_failed`` /
    ``noii_condition_probe_override`` vs ``noii_day_not_available``).
    """
    day_iso = end_d.isoformat()
    try:
        rows = client.metadata.get_dataset_condition(  # type: ignore[attr-defined]
            dataset=DATASET, start_date=day_iso, end_date=day_iso
        )
    except Exception as exc:  # endpoint down / unsupported
        if not require_probe:
            log.warning(
                "noii_condition_probe_override",
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
            "noii_condition_probe_failed",
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
            "noii_day_not_available",
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


def download_noii(
    settings: Settings,
    symbols: list[str] | tuple[str, ...],
    start: str,
    end: str,
    out_dir: str | Path = "data/raw/noii",
    *,
    max_cost: float = _MAX_COST_USD,
    stype_in: str = "raw_symbol",
    require_condition_probe: bool = True,
    client: object | None = None,
) -> dict:
    """Download XNAS.ITCH ``imbalance`` (NOII) for ``symbols`` over [start, end].

    One request per (symbol, month); each response is normalized to
    ``NOII_SCHEMA`` and written as an atomic, resumable parquet partition under
    ``out_dir/{SYMBOL}/{YYYY-MM}.parquet`` — a present partition is skipped, so a
    re-run only fetches what is missing.

    COST GUARD (PROTOCOL: cheap historical study, ~tens of dollars): before any
    timeseries bytes are fetched, ``metadata.get_cost`` is queried for the whole
    (symbols × range) request; the quoted USD figure is logged and the run ABORTS
    if it exceeds ``max_cost`` (default $60).

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
            f"{PROJECT_ROOT / '.env'} (never commit it) to acquire NOII data."
        )

    syms = [s.strip().upper() for s in symbols if s.strip()]
    root = noii_root(out_dir)
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)

    if client is None:  # pragma: no cover - real network path, never hit in tests
        import databento as db

        client = db.Historical(key=api_key)

    # ---- cost guard (metadata endpoint) ------------------------------------
    # end is exclusive; add a day so the quote covers the inclusive [start, end].
    # Clamp to the dataset's available end (Databento 422s if end is in the
    # future — e.g. requesting through 'today' before that session settles).
    end_excl = (end_d + timedelta(days=1)).isoformat()
    try:
        avail_end = client.metadata.get_dataset_range(dataset=DATASET)["end"][:10]
        if end_excl > avail_end:
            end_excl = avail_end
    except Exception:  # metadata probe is best-effort; the get_cost 422 still guards
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
    log.info("noii_cost_quote", dataset=DATASET, schema=SCHEMA, symbols=syms,
             start=start, end=end, quoted_usd=round(quoted, 4), max_cost=max_cost)
    if quoted > max_cost:
        raise RuntimeError(
            f"Databento cost quote ${quoted:.2f} exceeds the guard ${max_cost:.2f}. "
            "Raise --max-cost only if this is expected (PROTOCOL: NOII study is "
            "meant to cost tens of dollars)."
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
                # A present partition is final for any FULLY-EARLIER month. For
                # the request's END month only, verify the partition actually
                # covers end_d: a partial current-month partition (downloaded
                # mid-month by an earlier study) must be RE-FETCHED, or daily
                # forward collection silently sees no new sessions.
                if month != end_month:
                    skipped += 1
                    log.info("noii_skip_exists", symbol=sym, month=month)
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
                    datetime.fromtimestamp(have_max / 1e9, tz=ZoneInfo("UTC"))
                    .date()
                    .isoformat()
                    if have_max is not None
                    else ""
                )
                # B6: coverage means reaching INTO the closing-cross window on
                # end_d, not merely landing on its calendar date. floor=None
                # (calendar unresolvable) falls back to the date rule.
                floor_ns = coverage_floor_ns(end_d, CLOSE_MARGIN_S)
                covered = (
                    have_max is not None and have_max >= floor_ns
                    if floor_ns is not None
                    else have_date >= end_d.isoformat()
                )
                if covered:
                    skipped += 1
                    log.info("noii_skip_exists", symbol=sym, month=month)
                    continue
                log.info(
                    "noii_extend_partial_month",
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
                normalize_imbalance_df(df)
                if df.height
                else pl.DataFrame(schema=NOII_SCHEMA)
            )
            _write_atomic(norm, path)
            written += 1
            log.info("noii_partition", symbol=sym, month=month, rows=norm.height)

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
    # pandas DataFrame: reset any datetime index so ts_event/ts_recv are columns.
    reset = raw.reset_index() if hasattr(raw, "reset_index") else raw  # type: ignore[attr-defined]
    return pl.from_pandas(reset)
