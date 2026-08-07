"""M17 daily-bars dataset build (registered M17-xsect-factor-momentum-v1).

Registered spec: M3_REGISTRATION.md "M17 cross-sectional + factor momentum" (2026-07-19).
Mechanical data assembly only -- no strategy math, no filtering beyond the spec below.

Universe:
  STOCKS = union of all tickers appearing in data/external/index_weights_monthly.parquet
           where index=="SPX" (point-in-time IVV/S&P500 members, 2020-01..2026-06). Includes
           leavers/delistings/renames and a handful of zero-weight data artifacts from the
           source holdings feed (e.g. "-", "OXY WS WI", "MRP-W") -- fetched exactly like any
           other ticker; Alpaca's own validation sorts them into the zero-bar bucket.
  ETFS   = XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC MTUM VLUE QUAL USMV SIZE IWF IWD IWM
           QQQ SPY (11 sector SPDRs + 5 style/factor + 3 broad tilts + QQQ + SPY = 21).

Fetch: enginev51.data.alpaca_hist.AlpacaHist.fetch_bars_multi, feed=sip, timeframe=1Day,
adjustment=all (split+dividend adjusted -- total-return proxy for momentum ranks), window
2019-01-01..2026-07-18 UTC (method clamps recency itself). Chunked ~50 symbols/call.

Symbol normalization: Alpaca formats share classes with a dot (BRK.B, BF.B), but this
repo's own PIT membership table stores them without one (BRKB, BFB) -- confirmed by
inspection. Fetch tries the raw ticker first; on empty result, tries "<base>.<class>" then
"<base>-<class>" (only for tickers ending alpha and length>=2). A successful variant's bars
are stored under the ORIGINAL universe ticker (not the Alpaca-fetched form), so the output
"symbol" column always matches index_weights_monthly.parquet's "ticker" convention -- this is
load-bearing for scripts/m17_momentum.py, which joins bars <-> membership on that literal
string.

Resilience: a handful of universe "tickers" are pure data artifacts from the source holdings
feed and are not valid Alpaca symbol strings at all (contains a space, bare "-", etc.); Alpaca
rejects these with an HTTP 400 for the WHOLE multi-symbol request, not just that symbol
(verified empirically). A chunk that 400s is retried symbol-by-symbol so one bad ticker can't
blank out the other ~49 good ones in its chunk; symbols that individually 400 are recorded as
format-rejected (a subset of the zero-bar bucket) rather than silently dropped.

Outputs:
  data/external/m17_daily_bars.parquet   symbol, session, open, high, low, close, volume, vwap
  data/external/m17_coverage.md          coverage + sanity-check report
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

sys.stdout.reconfigure(encoding="utf-8")

from enginev51.config import get_settings  # noqa: E402
from enginev51.data import calendar as cal  # noqa: E402
from enginev51.data.alpaca_hist import AlpacaHist  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ET = ZoneInfo("America/New_York")

START = datetime(2019, 1, 1, tzinfo=timezone.utc)
END = datetime(2026, 7, 18, tzinfo=timezone.utc)
CHUNK = 50

ETFS: list[str] = [
    "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC",
    "MTUM", "VLUE", "QUAL", "USMV", "SIZE",
    "IWF", "IWD", "IWM",
    "QQQ", "SPY",
]
assert len(ETFS) == 21, f"expected 20 factor/sector ETFs + SPY = 21, got {len(ETFS)}"

WEIGHTS_PATH = PROJECT_ROOT / "data" / "external" / "index_weights_monthly.parquet"
OUT_PARQUET = PROJECT_ROOT / "data" / "external" / "m17_daily_bars.parquet"
OUT_COVERAGE = PROJECT_ROOT / "data" / "external" / "m17_coverage.md"


# --------------------------------------------------------------------------- universe


def load_stock_universe() -> list[str]:
    w = pl.read_parquet(WEIGHTS_PATH)
    spx = w.filter(pl.col("index") == "SPX")
    return sorted(spx["ticker"].unique().to_list())


def chunked(seq: list[str], n: int) -> list[list[str]]:
    return [seq[i : i + n] for i in range(0, len(seq), n)]


def normalize_variants(ticker: str) -> list[str]:
    """Candidate Alpaca symbol forms to try when the raw ticker comes back empty.

    Alpaca's share-class convention is a dot before the trailing class letter
    (BRK.B); dash is tried as a secondary guess. Only generated for tickers that
    are plausible bare class-share concatenations (pure alpha, len>=2) -- garbage
    strings like "-" or "OXY WS WI" get no variants and simply stay zero-bar.
    """
    if len(ticker) < 2 or not ticker.isalpha():
        return []
    base, cls = ticker[:-1], ticker[-1]
    return [f"{base}.{cls}", f"{base}-{cls}"]


# --------------------------------------------------------------------------- fetch


def fetch_chunk_resilient(
    api: AlpacaHist, symbols: list[str], log_prefix: str
) -> tuple[dict[str, list[dict]], set[str]]:
    """fetch_bars_multi for one chunk; on the known 400-invalid-symbol failure mode
    (confirmed: ANY unrecognized-format symbol 400s the WHOLE batch), fall back to
    one request per symbol so the other ~49 good tickers in the chunk aren't lost.
    Returns (results, format_rejected) where format_rejected is the subset that
    itself 400'd even alone (data-artifact tickers, not real delistings).
    """
    try:
        return api.fetch_bars_multi(
            symbols, START, END, feed="sip", timeframe="1Day", adjustment="all"
        ), set()
    except RuntimeError as exc:
        if "Alpaca 400" not in str(exc):
            raise
        print(f"{log_prefix} chunk 400'd, falling back to per-symbol: {exc}")
        out: dict[str, list[dict]] = {}
        rejected: set[str] = set()
        for s in symbols:
            try:
                r = api.fetch_bars_multi(
                    [s], START, END, feed="sip", timeframe="1Day", adjustment="all"
                )
                out.update(r)
            except RuntimeError as exc2:
                out[s.upper()] = []
                rejected.add(s.upper())
                print(f"{log_prefix}   format-rejected: {s!r} ({exc2})")
        return out, rejected


def fetch_universe(
    api: AlpacaHist, symbols: list[str]
) -> tuple[dict[str, list[dict]], set[str]]:
    fetched: dict[str, list[dict]] = {}
    format_rejected: set[str] = set()
    chunks = chunked(symbols, CHUNK)
    for i, chunk in enumerate(chunks, 1):
        print(f"[pass1] chunk {i}/{len(chunks)} ({len(chunk)} symbols)")
        result, rejected = fetch_chunk_resilient(api, chunk, f"[pass1 chunk {i}]")
        fetched.update(result)
        format_rejected |= rejected
    return fetched, format_rejected


def retry_zero_bar_with_normalization(
    api: AlpacaHist, fetched: dict[str, list[dict]], universe: list[str]
) -> tuple[dict[str, list[dict]], dict[str, str]]:
    """For universe tickers with zero bars after pass 1, try dot/dash class-share
    variants. On success, store the bars under the ORIGINAL ticker key (so the
    output symbol column still matches index_weights_monthly.parquet), and record
    the correction (original -> variant actually fetched from Alpaca).
    """
    corrections: dict[str, str] = {}
    zero = [s for s in universe if not fetched.get(s)]
    print(f"[pass2] {len(zero)} zero-bar tickers after pass 1; trying dot/dash variants")
    for orig in zero:
        for variant in normalize_variants(orig):
            try:
                r = api.fetch_bars_multi(
                    [variant], START, END, feed="sip", timeframe="1Day", adjustment="all"
                )
            except RuntimeError:
                continue
            bars = r.get(variant.upper(), [])
            if bars:
                fetched[orig] = bars
                corrections[orig] = variant
                print(f"[pass2]   {orig!r} -> {variant!r} ({len(bars)} bars)")
                break
    return fetched, corrections


# --------------------------------------------------------------------------- rows


def bars_to_df(symbol: str, bars: list[dict]) -> pl.DataFrame:
    if not bars:
        return pl.DataFrame(
            schema={
                "symbol": pl.Utf8, "session": pl.Utf8, "open": pl.Float64,
                "high": pl.Float64, "low": pl.Float64, "close": pl.Float64,
                "volume": pl.Float64, "vwap": pl.Float64,
            }
        )
    rows = []
    for b in bars:
        dt_utc = datetime.fromtimestamp(b["ts"] / 1e9, tz=timezone.utc)
        session = dt_utc.astimezone(ET).date().isoformat()
        rows.append(
            {
                "symbol": symbol,
                "session": session,
                "open": b["open"],
                "high": b["high"],
                "low": b["low"],
                "close": b["close"],
                "volume": b["volume"],
                "vwap": b["vwap"],
            }
        )
    return pl.DataFrame(rows)


# --------------------------------------------------------------------------- sanity checks


def check_aapl_split(bars: pl.DataFrame) -> str:
    aapl = bars.filter(
        (pl.col("symbol") == "AAPL")
        & (pl.col("session") >= "2020-08-20")
        & (pl.col("session") <= "2020-09-05")
    ).sort("session")
    if aapl.height == 0:
        return "AAPL split-week rows NOT FOUND -- cannot verify adjustment."
    closes = aapl["close"].to_list()
    sessions = aapl["session"].to_list()
    rets = [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]
    max_abs_ret = max(abs(r) for r in rets) if rets else 0.0
    verdict = "PASS (no discontinuity)" if max_abs_ret < 0.15 else "FAIL (possible unadjusted split!)"
    lines = [f"AAPL 2020-08-20..2020-09-05 ({aapl.height} sessions), max |daily return| = {max_abs_ret:.4%} -> {verdict}", ""]
    lines.append("| session | close | day/day ret |")
    lines.append("|---|---|---|")
    lines.append(f"| {sessions[0]} | {closes[0]:.4f} |  |")
    for i in range(1, len(closes)):
        lines.append(f"| {sessions[i]} | {closes[i]:.4f} | {rets[i-1]:+.4%} |")
    return "\n".join(lines)


def check_duplicates(bars_before_dedupe: pl.DataFrame) -> tuple[str, int]:
    dup = (
        bars_before_dedupe.group_by(["symbol", "session"])
        .agg(pl.len().alias("n"))
        .filter(pl.col("n") > 1)
    )
    n_dup_pairs = dup.height
    if n_dup_pairs == 0:
        return "PASS -- 0 duplicate (symbol, session) pairs pre-dedupe.", 0
    return f"FOUND {n_dup_pairs} duplicate (symbol, session) pairs pre-dedupe (deduped in output; first kept).", n_dup_pairs


def check_session_alignment(bars: pl.DataFrame) -> str:
    months = ["2020-03", "2024-01"]
    lines = []
    all_ok = True
    for month in months:
        y, m = int(month[:4]), int(month[5:7])
        start_d = date(y, m, 1)
        end_d = date(y + (1 if m == 12 else 0), (1 if m == 12 else m + 1), 1)
        nyse_days = {d.isoformat() for d in cal.trading_days(start_d, end_d - timedelta(days=1))}
        data_days = set(
            bars.filter((pl.col("symbol") == "SPY") & pl.col("session").str.starts_with(month))["session"].to_list()
        )
        missing = nyse_days - data_days
        extra = data_days - nyse_days
        ok = (not missing) and (not extra)
        all_ok = all_ok and ok
        lines.append(
            f"- {month}: NYSE trading days={len(nyse_days)}, SPY sessions in data={len(data_days)}, "
            f"missing={sorted(missing)}, extra={sorted(extra)} -> {'PASS' if ok else 'FAIL'}"
        )
    header = "PASS -- SPY sessions match the NYSE calendar exactly in both spot-checked months." if all_ok else "FAIL -- see mismatches below."
    return header + "\n" + "\n".join(lines)


# --------------------------------------------------------------------------- coverage report


def write_coverage(
    bars: pl.DataFrame,
    stock_universe: list[str],
    fetched: dict[str, list[dict]],
    format_rejected: set[str],
    corrections: dict[str, str],
    dup_check: str,
    n_dup_pairs: int,
    bars_before_dedupe_height: int,
) -> None:
    lines: list[str] = []
    lines.append("# M17 daily-bars dataset -- coverage report")
    lines.append("")
    lines.append(f"Built: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append("Source: `scripts/m17_build_daily_bars.py`")
    lines.append(f"Window requested: {START.date()} .. {END.date()} (UTC; SIP recency-clamped by the client)")
    lines.append("")

    # ---- ETF loud banner (up top per spec) ----
    etf_bars = bars.filter(pl.col("symbol").is_in(ETFS))
    etf_summary = (
        etf_bars.group_by("symbol")
        .agg(
            rows=pl.len(),
            first_session=pl.col("session").min(),
            last_session=pl.col("session").max(),
        )
        .sort("symbol")
    )
    present_etfs = set(etf_summary["symbol"].to_list())
    if etf_bars.height:
        global_first = etf_bars["session"].min()
        global_last = etf_bars["session"].max()
    else:
        # Catastrophic fallback only -- every ETF missing means the ETF alarm below
        # already fires; fall back to whatever the full dataset spans so the stock
        # "full-window" calc below doesn't crash on a None bound.
        global_first = bars["session"].min() if bars.height else "1970-01-01"
        global_last = bars["session"].max() if bars.height else "1970-01-01"
    missing_etfs = [e for e in ETFS if e not in present_etfs]
    incomplete_etfs = []
    if not missing_etfs:
        for r in etf_summary.iter_rows(named=True):
            if r["first_session"] > "2019-01-08" or r["last_session"] < global_last:
                incomplete_etfs.append(r)

    lines.append("## ETF COVERAGE -- READ FIRST")
    lines.append("")
    if missing_etfs or incomplete_etfs:
        lines.append(f"**LOUD WARNING: ETF coverage is INCOMPLETE.** Missing entirely: {missing_etfs or 'none'}. "
                      f"Present but not spanning the full window: {[r['symbol'] for r in incomplete_etfs] or 'none'}.")
    else:
        lines.append(
            f"**ALL 21 ETFs (20 factor/sector + SPY) have complete coverage**, "
            f"{global_first} .. {global_last}, 0 missing, 0 truncated."
        )
    lines.append("")
    lines.append("| symbol | rows | first_session | last_session | status |")
    lines.append("|---|---|---|---|---|")
    for e in ETFS:
        if e in present_etfs:
            r = etf_summary.filter(pl.col("symbol") == e).row(0, named=True)
            status = "ok" if r not in incomplete_etfs else "**TRUNCATED**"
            lines.append(f"| {e} | {r['rows']} | {r['first_session']} | {r['last_session']} | {status} |")
        else:
            lines.append(f"| {e} | **0** | - | - | **MISSING** |")
    lines.append("")

    # ---- stocks coverage ----
    stock_bars = bars.filter(pl.col("symbol").is_in(stock_universe))
    stock_summary = (
        stock_bars.group_by("symbol")
        .agg(rows=pl.len(), first_session=pl.col("session").min(), last_session=pl.col("session").max())
    )
    with_any = set(stock_summary["symbol"].to_list())
    zero_bar = sorted(set(stock_universe) - with_any)
    buffer_last = _shift_iso_date(str(global_last), -10)
    full_window = stock_summary.filter(
        (pl.col("first_session") <= "2019-01-08") & (pl.col("last_session") >= buffer_last)
    )

    lines.append("## Stocks coverage")
    lines.append("")
    lines.append(f"- tickers requested (distinct SPX-membership tickers): **{len(stock_universe)}**")
    lines.append(f"- tickers with >=1 bar: **{len(with_any)}**")
    lines.append(
        f"- tickers with full-window bars (first_session<=2019-01-08 AND last_session>={buffer_last}, "
        f"i.e. within 10 days of the ETF-anchored window end {global_last}): **{full_window.height}**"
    )
    lines.append(f"- zero-bar tickers: **{len(zero_bar)}** (of which {len(format_rejected)} were format-rejected by Alpaca outright -- data artifacts from the source holdings feed, not real symbols)")
    lines.append("")
    lines.append(f"Format-rejected (invalid symbol string, e.g. contains a space or bare '-'): {sorted(format_rejected) or 'none'}")
    lines.append("")
    lines.append("### Zero-bar ticker list (full)")
    lines.append("")
    lines.append(", ".join(zero_bar) if zero_bar else "(none)")
    lines.append("")

    # ---- symbol normalization corrections ----
    lines.append("## Symbol-normalization corrections")
    lines.append("")
    if corrections:
        lines.append("Raw ticker returned 0 bars; Alpaca-recognized variant found and used for the fetch. "
                      "Rows are stored under the ORIGINAL ticker (matching index_weights_monthly.parquet's "
                      "convention), not the Alpaca-side variant.")
        lines.append("")
        lines.append("| universe ticker | Alpaca variant used |")
        lines.append("|---|---|")
        for orig, variant in sorted(corrections.items()):
            lines.append(f"| {orig} | {variant} |")
    else:
        lines.append("(none needed)")
    lines.append("")

    # ---- per-year row counts ----
    lines.append("## Per-year row counts")
    lines.append("")
    by_year = (
        bars.with_columns(pl.col("session").str.slice(0, 4).alias("year"))
        .group_by("year")
        .agg(rows=pl.len(), symbols=pl.col("symbol").n_unique())
        .sort("year")
    )
    lines.append("| year | rows | distinct symbols |")
    lines.append("|---|---|---|")
    for r in by_year.iter_rows(named=True):
        lines.append(f"| {r['year']} | {r['rows']} | {r['symbols']} |")
    lines.append("")

    # ---- sample rows ----
    lines.append("## Sample rows")
    lines.append("")
    n = bars.height
    idx = sorted({0, n // 2, n - 1}) if n else []
    sample = bars.sort(["symbol", "session"])[idx] if idx else bars.head(3)
    with pl.Config(tbl_cols=-1, tbl_width_chars=200):
        lines.append("```")
        lines.append(str(sample))
        lines.append("```")
    lines.append("")

    # ---- sanity checks ----
    lines.append("## Sanity checks")
    lines.append("")
    lines.append("### 1. AAPL 2020-08 split week (adjustment=all correctness)")
    lines.append("")
    lines.append(check_aapl_split(bars))
    lines.append("")
    lines.append("### 2. Duplicate (symbol, session) pairs")
    lines.append("")
    lines.append(dup_check)
    lines.append(f"(rows before dedupe: {bars_before_dedupe_height}, rows after dedupe: {bars.height}, removed: {bars_before_dedupe_height - bars.height})")
    lines.append("")
    lines.append("### 3. Session alignment with NYSE trading calendar (SPY, 2 spot-check months)")
    lines.append("")
    lines.append(check_session_alignment(bars))
    lines.append("")

    OUT_COVERAGE.write_text("\n".join(lines), encoding="utf-8")


def _shift_iso_date(iso: str, days: int) -> str:
    d = date.fromisoformat(iso)
    return (d + timedelta(days=days)).isoformat()


# --------------------------------------------------------------------------- main


def main() -> None:
    stock_universe = load_stock_universe()
    print(f"stock universe: {len(stock_universe)} distinct SPX-membership tickers")
    all_symbols = sorted(set(stock_universe) | set(ETFS))
    print(f"total symbols to fetch (stocks + ETFs, deduped): {len(all_symbols)}")

    settings = get_settings()
    api = AlpacaHist(settings)
    try:
        fetched, format_rejected = fetch_universe(api, all_symbols)
        # Retry over the FULL symbol set (stocks + ETFs): the dot/dash variants only
        # ever help class-share stock tickers, but running it over ETFs too is free
        # insurance against a transient miss on the 21 tickers whose coverage must
        # be loudly flagged as complete or not.
        fetched, corrections = retry_zero_bar_with_normalization(api, fetched, all_symbols)
    finally:
        api.close()

    frames = [bars_to_df(sym, bars) for sym, bars in fetched.items() if bars]
    raw = pl.concat(frames) if frames else pl.DataFrame(
        schema={"symbol": pl.Utf8, "session": pl.Utf8, "open": pl.Float64, "high": pl.Float64,
                "low": pl.Float64, "close": pl.Float64, "volume": pl.Float64, "vwap": pl.Float64}
    )
    raw_height = raw.height
    print(f"raw rows before dedupe: {raw_height}")

    dup_msg, n_dup_pairs = check_duplicates(raw)
    print(dup_msg)

    bars = raw.unique(subset=["symbol", "session"], keep="first").sort(["symbol", "session"])
    print(f"rows after dedupe: {bars.height}")

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    bars.write_parquet(OUT_PARQUET)
    print(f"wrote {OUT_PARQUET} ({bars.height} rows, {bars.width} cols)")

    write_coverage(
        bars, stock_universe, fetched, format_rejected, corrections, dup_msg, n_dup_pairs, raw_height
    )
    print(f"wrote {OUT_COVERAGE}")

    # ---- final console summary ----
    with_any = bars.filter(pl.col("symbol").is_in(stock_universe))["symbol"].n_unique()
    zero_bar = sorted(set(stock_universe) - set(bars["symbol"].unique().to_list()))
    etf_present = set(bars.filter(pl.col("symbol").is_in(ETFS))["symbol"].unique().to_list())
    etf_missing = [e for e in ETFS if e not in etf_present]

    print()
    print("=== SUMMARY ===")
    print(f"stocks requested: {len(stock_universe)}  with-bars: {with_any}  zero-bar: {len(zero_bar)}")
    print(f"ETFs requested: {len(ETFS)}  missing: {etf_missing or 'NONE'}")
    print(f"total rows: {bars.height}")
    print(f"zero-bar tickers (first 10): {zero_bar[:10]}")
    print(f"corrections made: {corrections}")


if __name__ == "__main__":
    main()
