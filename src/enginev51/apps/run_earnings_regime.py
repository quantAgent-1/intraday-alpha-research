"""M21 earnings-reaction-regime diagnostic runner (family ``earnings_reaction_regime_v1``).

Three subcommands:

    uv run python -m enginev51.apps.run_earnings_regime atlas
        -> THE single estimation pass (orchestrator's to run). Assembles the sealed
           event frame, freezes the tercile/percentile cuts, computes bucket base
           rates, and writes atlas.md + events.parquet + cuts.json + base_rates.json
           under research/experiments/M21-earnings-regime/.

    uv run python -m enginev51.apps.run_earnings_regime score --symbol NVDA --date 2024-02-21
        -> READ-ONLY differentiator: places one (symbol, date) event into its frozen
           bucket, prints feature percentiles + historical base rates (both windows) +
           nearest analogs. Works for ANY date (incl. forward). Writes NOTHING.

    uv run python -m enginev51.apps.run_earnings_regime selftest
        -> the ONLY pre-estimation invocation: runs the whole pipeline on synthetic
           fixtures in a temp dir (no lake, no real writes).

DATA / ADJUSTMENT: this is a multi-year daily RETURNS diagnostic, so the daily
series is split/dividend adjusted (adjustment='all'). The owned data/raw/sip/bars1d
lake is RAW (verified 2026-07-22 via NVDA's 2024-06-10 10:1 split) and therefore
NOT used for returns by default — it would inject fake ~-90% split-day returns. The
bar getter resolves each symbol from data/external/m21_bars/{SYM}.parquet (the
adjusted, offline-reproducible cache) or an Alpaca 1Day adjustment='all' fetch that
populates it. Pre-populate the cache (26 names + SMH) before the one atlas pass.

Console note: on Windows set PYTHONIOENCODING=utf-8.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import click
import polars as pl

from enginev51.config import PROJECT_ROOT, get_settings
from enginev51.research_screens import earnings_regime as er

DEFAULT_CALENDAR = "data/external/earnings_calendar.parquet"
DEFAULT_CACHE_DIR = PROJECT_ROOT / "data" / "external" / "m21_bars"
DEFAULT_BARS1D_DIR = PROJECT_ROOT / "data" / "raw" / "sip" / "bars1d"
# Warm the 252-session momentum lookback well before the 2018-01 estimation start.
FETCH_START = datetime(2016, 6, 1, tzinfo=UTC)


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


# --------------------------------------------------------------------------- real bar getter


def make_bar_getter(
    *,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    bars1d_dir: Path = DEFAULT_BARS1D_DIR,
    allow_alpaca: bool = True,
    write_cache: bool = True,
    allow_raw_bars1d: bool = False,
):
    """Adjusted daily-bar getter for the real lake.

    Resolution order per symbol: (1) the adjusted cache m21_bars/{SYM}.parquet;
    (2) an Alpaca 1Day adjustment='all' fetch (cached when ``write_cache``); (3) —
    only if ``allow_raw_bars1d`` — the RAW bars1d lake, with a loud warning (returns
    across splits are wrong). Returns a (session, open, close) frame or None. Results
    are memoized so a run touches each symbol's disk/API once.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    memo: dict[str, pl.DataFrame | None] = {}
    api_box: dict[str, object] = {}

    def _api():
        if "api" not in api_box:
            from enginev51.data.alpaca_hist import AlpacaHist

            api_box["api"] = AlpacaHist(get_settings())
        return api_box["api"]

    def getter(symbol: str) -> pl.DataFrame | None:
        sym = symbol.upper()
        if sym in memo:
            return memo[sym]
        cache = cache_dir / f"{sym}.parquet"
        if cache.exists():
            memo[sym] = er.normalize_daily(pl.read_parquet(cache))
            return memo[sym]
        if allow_alpaca:
            try:
                end = datetime.now(UTC)
                res = _api().fetch_bars_multi(
                    [sym], FETCH_START, end, feed="sip", timeframe="1Day", adjustment="all"
                )
                bars = res.get(sym, [])
                if bars:
                    df = pl.DataFrame(bars).select(
                        pl.col("ts"), pl.col("open"), pl.col("close")
                    )
                    df = er.normalize_daily(df)
                    if write_cache:
                        df.write_parquet(cache)
                    memo[sym] = df
                    return df
            except Exception as exc:  # noqa: BLE001 — fetch is best-effort here
                click.echo(f"  [warn] Alpaca fetch failed for {sym}: {exc}")
        if allow_raw_bars1d:
            raw = bars1d_dir / f"{sym}.parquet"
            if raw.exists():
                click.echo(
                    f"  [WARN] {sym}: using RAW bars1d (UNADJUSTED — split-day returns "
                    "are wrong). Enable only for a smoke run, never the atlas."
                )
                memo[sym] = er.normalize_daily(pl.read_parquet(raw))
                return memo[sym]
        memo[sym] = None
        return None

    return getter


# --------------------------------------------------------------------------- cli


@click.group()
def main() -> None:
    """M21 earnings-reaction-regime DIAGNOSTIC (no trading path; no costs)."""
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety


@main.command("atlas")
@click.option("--calendar", default=DEFAULT_CALENDAR, help="Earnings calendar parquet.")
@click.option("--out-dir", default=None, help="Override output dir.")
@click.option("--cache-dir", default=None, help="Adjusted daily-bar cache (m21_bars).")
@click.option("--no-alpaca", is_flag=True, default=False, help="Cache-only (no network fetch).")
@click.option(
    "--allow-raw-bars1d",
    is_flag=True,
    default=False,
    help="DANGER: fall back to the RAW bars1d lake (unadjusted; corrupts split-day returns).",
)
def atlas_cmd(
    calendar: str, out_dir: str | None, cache_dir: str | None, no_alpaca: bool, allow_raw_bars1d: bool
) -> None:
    cal_path = _resolve(calendar)
    if not cal_path.exists():
        click.echo(
            f"earnings calendar not found at {cal_path}. It is a parallel deliverable "
            "(schema: event_id, symbol, fiscal_note, accept_ts_et, timing, day0_session, "
            "source). Ship code + tests; run this once the calendar parquet exists."
        )
        return
    cal_df = pl.read_parquet(cal_path)
    getter = make_bar_getter(
        cache_dir=Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR,
        allow_alpaca=not no_alpaca,
        allow_raw_bars1d=allow_raw_bars1d,
    )
    res = er.compute_atlas(cal_df, getter, out_dir=out_dir)
    click.echo(
        f"events(sealed): {res['n_events']}   feature-ok: {res['n_ok']}   "
        f"cells: {res['n_cells']}   ref: {res['ref_source']}"
    )
    click.echo(f"atlas md:   {er.atlas_md_path(out_dir)}")
    click.echo(f"events:     {er.events_path(out_dir)}")
    click.echo(f"cuts:       {er.cuts_path(out_dir)}")
    click.echo(f"base rates: {er.base_rates_path(out_dir)}")


@main.command("score")
@click.option("--symbol", required=True, help="Ticker (e.g. NVDA).")
@click.option("--date", "date_", required=True, help="day0 session (ISO date).")
@click.option("--calendar", default=DEFAULT_CALENDAR, help="Earnings calendar parquet (streak history).")
@click.option("--out-dir", default=None, help="Atlas artifacts dir.")
@click.option("--cache-dir", default=None, help="Adjusted daily-bar cache (m21_bars).")
def score_cmd(
    symbol: str, date_: str, calendar: str, out_dir: str | None, cache_dir: str | None
) -> None:
    cal_path = _resolve(calendar)
    cal_df = pl.read_parquet(cal_path) if cal_path.exists() else pl.DataFrame(
        schema={"symbol": pl.Utf8, "day0_session": pl.Utf8}
    )
    # READ-ONLY: never write the cache from score (it must write NOTHING).
    getter = make_bar_getter(
        cache_dir=Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR, write_cache=False
    )
    try:
        res = er.score_event(symbol, date_, getter, cal_df, out_dir=out_dir)
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(er.format_score(res))


@main.command("selftest")
@click.option("--json", "as_json", is_flag=True, help="Emit the check results as JSON.")
def selftest_cmd(as_json: bool) -> None:
    result = run_selftest()
    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        for name, ok in result["checks"].items():
            click.echo(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        click.echo(f"\nSELFTEST {'PASS' if result['ok'] else 'FAIL'} "
                   f"({sum(result['checks'].values())}/{len(result['checks'])} checks)")
    if not result["ok"]:
        raise SystemExit(1)


# --------------------------------------------------------------------------- selftest


def _weekdays(start: str, n: int) -> list[str]:
    d = date.fromisoformat(start)
    out: list[str] = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _series(sessions: list[str], closes: list[float], gaps: dict[int, float] | None = None) -> pl.DataFrame:
    gaps = gaps or {}
    opens = [closes[0]]
    for i in range(1, len(closes)):
        opens.append(closes[i - 1] * (1.0 + gaps.get(i, 0.0)))
    return pl.DataFrame({"session": sessions, "open": opens, "close": closes})


def run_selftest() -> dict:
    """Exercise atlas + score on synthetic fixtures in a temp dir (no lake/network)."""
    checks: dict[str, bool] = {}
    tmp = Path(tempfile.mkdtemp(prefix="m21_selftest_"))
    try:
        sess = _weekdays("2019-01-01", 900)
        # SMH flat -> runup60_rel ~ the name's own 60d return.
        bars: dict[str, pl.DataFrame] = {"SMH": _series(sess, [100.0] * len(sess))}
        # one strong-uptrend name (T3-ish) + one flat filler (T1/T2).
        up = [100.0 * (1.003 ** i) for i in range(len(sess))]
        flat = [100.0 + (i % 7) * 0.01 for i in range(len(sess))]
        gaps_up = {i: 0.02 for i in range(300, len(sess), 45)}
        bars["NVDA"] = _series(sess, up, gaps_up)
        bars["AMD"] = _series(sess, flat)

        def getter(sym: str) -> pl.DataFrame | None:
            return bars.get(sym.upper())

        cal_rows = []
        for sym in ("NVDA", "AMD"):
            s = er.DailySeries(bars[sym])
            for k, idx in enumerate(range(300, len(s.sessions) - 25, 45)):
                cal_rows.append({
                    "event_id": f"{sym}-{k}", "symbol": sym, "fiscal_note": f"Q{k % 4 + 1}",
                    "accept_ts_et": f"{s.sessions[idx]}T16:05:00", "timing": "AMC",
                    "day0_session": s.sessions[idx], "source": "selftest",
                })
        cal = pl.DataFrame(cal_rows)

        res = er.compute_atlas(cal, getter, out_dir=tmp, universe=er.UNIVERSE)
        checks["atlas_writes_4_files"] = all(
            p.exists() for p in (er.atlas_md_path(tmp), er.events_path(tmp),
                                 er.cuts_path(tmp), er.base_rates_path(tmp))
        )
        checks["atlas_24_cells"] = res["n_cells"] == 24
        checks["no_cost_model_in_md"] = er.NO_COST_MODEL in er.atlas_md_path(tmp).read_text(encoding="utf-8")

        ev = cal_rows[-1]
        before = sorted(p.name for p in tmp.iterdir())
        sc = er.score_event(ev["symbol"], ev["day0_session"], getter, cal, out_dir=tmp)
        after = sorted(p.name for p in tmp.iterdir())
        checks["score_writes_nothing"] = before == after
        checks["score_has_bucket"] = bool(sc["bucket_id"]) and sc["note"] == er.NO_COST_MODEL
        checks["score_format_ok"] = er.NO_COST_MODEL in er.format_score(sc)

        return {"ok": all(checks.values()), "checks": checks, "tmp": str(tmp)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
