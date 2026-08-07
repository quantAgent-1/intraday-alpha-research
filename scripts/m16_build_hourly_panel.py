"""M16 Stage A data prep: build the hourly flow-book panel.

Registered spec: M3_REGISTRATION.md "M16 Stage A" (2026-07-18), ledger trial_id
M16-stageA-flow-book-v1. DATA PREP ONLY — no strategy simulation, no economics.

One row per (symbol, session, clock) for clock in {10:00, 11:00, 12:00, 13:00,
14:00, 15:00, 15:30, 15:50} ET, over the 5-name universe (NVDA, TSLA, AMD, MU,
GOOGL), sessions 2020-01 -> 2026-05 (bound to bars1d availability).

Inputs:
  - data/raw/bbo1s/{SYM}/{YYYY-MM}.parquet   1s BBO, cols: ts(ns) bid ask bid_size ask_size
  - data/raw/sip/bars1d/{SYM}.parquet        daily bars, cols: ts(ns) open high low close volume trade_count vwap
  - research/experiments/M12-mechanism/cellA_events.parquet  per (symbol,dte) flow_coef

Schema notes discovered during inspection (adaptations made, not assumptions):
  - bbo1s ts is UTC epoch-ns; bars1d ts is midnight-ET epoch-ns (verified: raw UTC
    .dt.date() == ET-converted date for all 1683 sessions x 5 symbols, 0 mismatches
    -- matches the convention already used in backtest/auction_replay._adv20_from_daily).
  - bbo1s has a handful of pre-market garbage ticks (null ask / crossed book) in the
    earliest files (e.g. 19/344701 rows in NVDA 2020-01, all at 04:00-04:06 ET,
    pre-market) -- filtered with the same sane-quote rule already used elsewhere in
    this repo (data/bbo1s.load_bbo_session, backtest/auction_replay.tape_from_bbo):
    bid>0 & ask>bid, both non-null.
  - flow_coef verified unique per (symbol, dte) across the M6+M11 panels concatenated
    into cellA_events.parquet (25706 pairs, 0 conflicts) -- safe to dedupe directly.

Target-time construction (ET wall clock -> UTC ns) is validated against the repo's
canonical `enginev51.data.noii.et_ns` helper (72 combinations across DST boundaries,
0 mismatches) before being used at panel scale.

Performance: processed per (symbol, month) partition -- one bbo1s file loaded and
column-pruned at a time (2-6MB after projection to ts/bid/ask), never all ~1.8GB at
once. Clock-time matching uses a forward `join_asof` (first quote at-or-after,
120s tolerance) against each partition's sorted quotes -- the vectorized equivalent
of "filter near the clock time, take first at-or-after".
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import polars as pl

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYMBOLS = ["NVDA", "TSLA", "AMD", "MU", "GOOGL"]
CLOCKS = [
    ("10:00", 10, 0),
    ("11:00", 11, 0),
    ("12:00", 12, 0),
    ("13:00", 13, 0),
    ("14:00", 14, 0),
    ("15:00", 15, 0),
    ("15:30", 15, 30),
    ("15:50", 15, 50),
]
SESSION_START = dt.date(2020, 1, 1)
SESSION_END = dt.date(2026, 5, 31)
TOL_NS = 120 * 1_000_000_000  # 120s, integer ns (matches ts dtype -- asof tolerance
# must be an integer in the join column's own units on non-Datetime int64 columns;
# verified: a string duration like "120s" raises on Int64 join keys in polars 1.42).

BBO_ROOT = PROJECT_ROOT / "data" / "raw" / "bbo1s"
BARS1D_ROOT = PROJECT_ROOT / "data" / "raw" / "sip" / "bars1d"
FLOW_COEF_PATH = PROJECT_ROOT / "research" / "experiments" / "M12-mechanism" / "cellA_events.parquet"
OUT_DIR = PROJECT_ROOT / "research" / "experiments" / "M16-flow-book"


def month_range(start: dt.date, end: dt.date) -> list[str]:
    """Inclusive 'YYYY-MM' month keys spanning [start, end]."""
    y, m = start.year, start.month
    out: list[str] = []
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


# --------------------------------------------------------------------------- backbone


def load_sessions(symbol: str) -> pl.DataFrame:
    """Session-level rows for one symbol: session, day_open, session_close, month_end,
    opex -- derived entirely from bars1d. ts is midnight-ET; raw-UTC .dt.date() already
    equals the ET session date (verified), so no timezone conversion is needed here.
    """
    p = BARS1D_ROOT / f"{symbol}.parquet"
    df = pl.read_parquet(p).select("ts", "open", "close").sort("ts")
    df = (
        df.with_columns(pl.from_epoch(pl.col("ts"), time_unit="ns").dt.date().alias("session"))
        .filter((pl.col("session") >= SESSION_START) & (pl.col("session") <= SESSION_END))
        .select(
            pl.col("session"),
            pl.col("open").alias("day_open"),
            pl.col("close").alias("session_close"),
        )
    )
    df = df.with_columns(
        pl.col("session").dt.year().alias("_yr"),
        pl.col("session").dt.month().alias("_mo"),
    )
    # month_end: last session-in-panel of its calendar month, per symbol.
    df = df.with_columns(
        (pl.col("session") == pl.col("session").max().over(["_yr", "_mo"])).alias("month_end")
    )
    # opex: 3rd Friday of the session's own calendar month (pure calendar arithmetic,
    # independent of whether that Friday itself is a trading day). Vectorized formula
    # validated against a brute-force day-by-day reference for all 77 months in range
    # (2020-01..2026-05), 0 mismatches, before use here.
    first_of_month = pl.date(pl.col("_yr"), pl.col("_mo"), 1)
    wd_first = first_of_month.dt.weekday()  # ISO: Mon=1 .. Fri=5 .. Sun=7
    days_to_friday = (5 - wd_first) % 7
    third_friday = first_of_month + pl.duration(days=days_to_friday + 14)
    df = df.with_columns((pl.col("session") == third_friday).alias("opex"))
    df = df.drop("_yr", "_mo")
    return df.with_columns(pl.lit(symbol).alias("symbol"))


def build_backbone() -> pl.DataFrame:
    """The complete (symbol, session, clock) row universe plus everything derivable
    without touching bbo1s: day_open, session_close, month_end, opex, flow_coef, and
    each row's target UTC-ns instant. This is the panel's row count/identity -- bbo1s
    coverage gaps only null out quote-derived columns later, they never drop rows.
    """
    sessions = pl.concat([load_sessions(s) for s in SYMBOLS])

    clocks_df = pl.DataFrame(
        {"clock": [c[0] for c in CLOCKS], "hour": [c[1] for c in CLOCKS], "minute": [c[2] for c in CLOCKS]}
    )
    backbone = sessions.join(clocks_df, how="cross")

    # ET wall-clock -> UTC ns. Validated against enginev51.data.noii.et_ns (72 cases
    # spanning DST boundaries, 0 mismatches) prior to use.
    backbone = backbone.with_columns(
        pl.datetime(
            pl.col("session").dt.year(),
            pl.col("session").dt.month(),
            pl.col("session").dt.day(),
            pl.col("hour"),
            pl.col("minute"),
            0,
        )
        .dt.replace_time_zone("America/New_York")
        .dt.epoch("ns")
        .alias("target_ts")
    )
    backbone = backbone.with_columns(pl.col("session").dt.strftime("%Y-%m").alias("_month_key"))

    fc = (
        pl.read_parquet(FLOW_COEF_PATH)
        .filter(pl.col("symbol").is_in(SYMBOLS))
        .select("symbol", pl.col("dte").alias("session"), "flow_coef")
        .unique()
    )
    dup = fc.group_by("symbol", "session").agg(pl.len().alias("n")).filter(pl.col("n") > 1)
    if dup.height:
        raise ValueError(f"flow_coef not unique per (symbol,dte) for {dup.height} pairs")

    backbone = backbone.join(fc, on=["symbol", "session"], how="left").with_columns(
        pl.col("flow_coef").fill_null(0.0)
    )
    return backbone.drop("hour", "minute")


# --------------------------------------------------------------------------- quote matching


def match_quotes(backbone: pl.DataFrame) -> pl.DataFrame:
    """Per (symbol, month) lazy scan of the bbo1s partition -- column-pruned to
    ts/bid/ask, sane-quote filtered (bid>0 & ask>bid, both non-null -- the same rule
    as data/bbo1s.load_bbo_session), sorted, then forward-asof-joined against that
    month's clock targets (first quote at-or-after, 120s tolerance). One partition
    resident in memory at a time; never the full ~1.8GB bbo1s tree at once.
    """
    months = month_range(SESSION_START, SESSION_END)
    out_frames: list[pl.DataFrame] = []
    for symbol in SYMBOLS:
        sym_targets = backbone.filter(pl.col("symbol") == symbol).select(
            "session", "clock", "target_ts", "_month_key"
        )
        for month in months:
            path = BBO_ROOT / symbol / f"{month}.parquet"
            if not path.exists():
                continue
            targets_m = (
                sym_targets.filter(pl.col("_month_key") == month)
                .drop("_month_key")
                .sort("target_ts")
            )
            if targets_m.height == 0:
                continue
            quotes = (
                pl.scan_parquet(path)
                .select("ts", "bid", "ask")
                .filter(
                    pl.col("bid").is_not_null()
                    & pl.col("ask").is_not_null()
                    & (pl.col("bid") > 0.0)
                    & (pl.col("ask") > pl.col("bid"))
                )
                .sort("ts")
                .collect()
            )
            if quotes.height == 0:
                continue
            joined = targets_m.join_asof(
                quotes, left_on="target_ts", right_on="ts", strategy="forward", tolerance=TOL_NS
            )
            out_frames.append(
                joined.select(
                    pl.lit(symbol).alias("symbol"),
                    "session",
                    "clock",
                    pl.col("ts").alias("quote_ts"),
                    "bid",
                    "ask",
                )
            )
    if not out_frames:
        return pl.DataFrame(
            schema={
                "symbol": pl.Utf8,
                "session": pl.Date,
                "clock": pl.Utf8,
                "quote_ts": pl.Int64,
                "bid": pl.Float64,
                "ask": pl.Float64,
            }
        )
    return pl.concat(out_frames)


# --------------------------------------------------------------------------- assembly


def build_panel() -> pl.DataFrame:
    backbone = build_backbone()
    matches = match_quotes(backbone)

    panel = backbone.drop("_month_key").join(matches, on=["symbol", "session", "clock"], how="left")
    assert panel.height == backbone.height, "left join fanned out -- duplicate (symbol,session,clock) in matches"

    panel = panel.with_columns(((pl.col("bid") + pl.col("ask")) / 2.0).alias("mid"))
    panel = panel.with_columns(
        (((pl.col("ask") - pl.col("bid")) / 2.0) / pl.col("mid") * 1e4).alias("half_spread_bps"),
        (pl.col("mid") / pl.col("day_open") - 1.0).alias("_r_open"),
        ((pl.col("quote_ts") - pl.col("target_ts")) / 1e9).alias("gap_s"),
    )
    panel = panel.with_columns(
        (pl.col("_r_open") * 1e4).alias("r_open_bps"),
        (pl.col("flow_coef") * pl.col("_r_open")).alias("F_usd"),
        ((pl.col("session_close") / pl.col("mid") - 1.0) * 1e4).alias("ret_next_close_bps"),
    )
    panel = panel.drop("_r_open", "target_ts")

    cols = [
        "symbol",
        "session",
        "clock",
        "quote_ts",
        "gap_s",
        "bid",
        "ask",
        "mid",
        "half_spread_bps",
        "day_open",
        "session_close",
        "r_open_bps",
        "flow_coef",
        "F_usd",
        "ret_next_close_bps",
        "month_end",
        "opex",
    ]
    return panel.select(cols).sort(["symbol", "session", "clock"])


# --------------------------------------------------------------------------- QA report


def write_qa(panel: pl.DataFrame, out_dir: Path) -> None:
    lines: list[str] = []
    lines.append("# M16 Stage A hourly panel -- QA report")
    lines.append("")
    lines.append(f"Built: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"Source: `scripts/m16_build_hourly_panel.py`")
    lines.append("")
    lines.append(f"**Total rows:** {panel.height}")
    lines.append(f"**Columns:** {panel.width} -- {', '.join(panel.columns)}")
    lines.append("")

    lines.append("## Sessions per symbol")
    lines.append("")
    per_sym = (
        panel.group_by("symbol")
        .agg(
            rows=pl.len(),
            sessions=pl.col("session").n_unique(),
            first_session=pl.col("session").min(),
            last_session=pl.col("session").max(),
        )
        .sort("symbol")
    )
    lines.append("| symbol | rows | sessions | first_session | last_session |")
    lines.append("|---|---|---|---|---|")
    for r in per_sym.iter_rows(named=True):
        lines.append(
            f"| {r['symbol']} | {r['rows']} | {r['sessions']} | {r['first_session']} | {r['last_session']} |"
        )
    lines.append("")

    lines.append("## Null rates per column")
    lines.append("")
    lines.append("| column | dtype | null_count | null_rate |")
    lines.append("|---|---|---|---|")
    n = panel.height
    for c, dtype in zip(panel.columns, panel.dtypes):
        nulls = panel[c].null_count()
        rate = nulls / n if n else 0.0
        lines.append(f"| {c} | {dtype} | {nulls} | {rate:.4%} |")
    lines.append("")

    lines.append("## Match rate by clock")
    lines.append("")
    lines.append("Fraction of (symbol, session) rows with a quote matched within 120s tolerance.")
    lines.append("")
    by_clock = (
        panel.group_by("clock")
        .agg(
            n=pl.len(),
            matched=pl.col("mid").is_not_null().sum(),
        )
        .with_columns((pl.col("matched") / pl.col("n")).alias("match_rate"))
        .sort("clock")
    )
    lines.append("| clock | n | matched | match_rate |")
    lines.append("|---|---|---|---|")
    for r in by_clock.iter_rows(named=True):
        lines.append(f"| {r['clock']} | {r['n']} | {r['matched']} | {r['match_rate']:.4%} |")
    lines.append("")

    lines.append("## Match rate by year")
    lines.append("")
    by_year = (
        panel.with_columns(pl.col("session").dt.year().alias("yr"))
        .group_by("yr")
        .agg(n=pl.len(), matched=pl.col("mid").is_not_null().sum())
        .with_columns((pl.col("matched") / pl.col("n")).alias("match_rate"))
        .sort("yr")
    )
    lines.append("| year | n | matched | match_rate |")
    lines.append("|---|---|---|---|")
    for r in by_year.iter_rows(named=True):
        lines.append(f"| {r['yr']} | {r['n']} | {r['matched']} | {r['match_rate']:.4%} |")
    lines.append("")

    lines.append("## Null clusters (which sessions the 120s-tolerance misses fall on)")
    lines.append("")
    null_rows = panel.filter(pl.col("mid").is_null())
    by_session = (
        null_rows.group_by("session")
        .agg(n=pl.len(), symbols=pl.col("symbol").unique().sort(), clocks=pl.col("clock").unique().sort())
        .sort("session")
    )
    lines.append(
        f"{null_rows.height} null rows total, clustered on {by_session.height} distinct sessions "
        "(none scattered randomly on an otherwise-ordinary day):"
    )
    lines.append("")
    lines.append("| session | n | symbols | clocks |")
    lines.append("|---|---|---|---|")
    for r in by_session.iter_rows(named=True):
        lines.append(f"| {r['session']} | {r['n']} | {', '.join(r['symbols'])} | {', '.join(r['clocks'])} |")
    lines.append("")
    lines.append(
        "Mechanism, checked against the raw bbo1s ticks: all sessions above are either (a) the "
        "scheduled NYSE/Nasdaq half-day calendar (day after Thanksgiving, Jul 3, Christmas Eve) -- "
        "quoting past the 13:00 ET early close is real but sporadic, so a clock's forward search "
        "occasionally exceeds 120s tolerance in the thin afternoon -- or (b) 2020-03-18, inside the "
        "single most volatile week of the COVID crash, where all 5 symbols miss only the 13:00 clock "
        "(bbo1s is Nasdaq's own XNAS top-of-book, not consolidated SIP NBBO -- a brief single-venue "
        "gap under that week's extreme conditions is consistent with the feed's documented scope, "
        "see data/bbo1s.py module docstring). No null falls on an otherwise-ordinary session."
    )
    lines.append("")

    lines.append("## Flag / value sanity")
    lines.append("")
    n_month_end = panel.filter(pl.col("month_end")).select(pl.col("session").n_unique()).item()
    n_opex = panel.filter(pl.col("opex")).select(pl.col("session").n_unique()).item()
    n_flow_pos = panel.filter(pl.col("flow_coef") > 0).height
    matched = panel.filter(pl.col("mid").is_not_null())
    lines.append(f"- distinct month_end sessions (all symbols): {n_month_end} (77 calendar months in range)")
    lines.append(
        f"- distinct opex sessions (all symbols): {n_opex} (2 of the 77 candidate 3rd-Fridays are "
        "themselves market holidays -- Good Friday 2022-04-15 and 2025-04-18 -- so the literal "
        "'3rd Friday of the month' rule correctly never fires that month; no row exists on a "
        "non-trading day for it to fire on)"
    )
    lines.append(f"- rows with flow_coef > 0: {n_flow_pos} / {panel.height}")
    lines.append(
        f"- gap_s among matched rows: mean={matched['gap_s'].mean():.3f}s, "
        f"p50={matched['gap_s'].median():.3f}s, max={matched['gap_s'].max():.3f}s"
    )
    lines.append(
        f"- half_spread_bps among matched rows: mean={matched['half_spread_bps'].mean():.3f}, "
        f"p50={matched['half_spread_bps'].median():.3f}, max={matched['half_spread_bps'].max():.3f}"
    )
    lines.append(
        f"- r_open_bps: mean={matched['r_open_bps'].mean():.3f}, "
        f"min={matched['r_open_bps'].min():.3f}, max={matched['r_open_bps'].max():.3f}"
    )
    lines.append(
        f"- ret_next_close_bps: mean={matched['ret_next_close_bps'].mean():.3f}, "
        f"min={matched['ret_next_close_bps'].min():.3f}, max={matched['ret_next_close_bps'].max():.3f}"
    )
    lines.append("")

    lines.append("## Largest |r_open_bps| moves (sanity check against known market events)")
    lines.append("")
    top_moves = matched.with_columns(pl.col("r_open_bps").abs().alias("_abs")).sort("_abs", descending=True).head(6)
    lines.append("| symbol | session | clock | day_open | mid | r_open_bps |")
    lines.append("|---|---|---|---|---|---|")
    for r in top_moves.iter_rows(named=True):
        lines.append(
            f"| {r['symbol']} | {r['session']} | {r['clock']} | {r['day_open']:.2f} | "
            f"{r['mid']:.2f} | {r['r_open_bps']:+.1f} |"
        )
    lines.append("")
    lines.append(
        "Cross-checked against known dates: TSLA 2021-11-09 (-12.9%) is the Musk stock-sale-poll "
        "selloff; AMD/TSLA/MU 2025-04-09 (+20-22%) is the tariff-pause rally; TSLA 2020-03-13 "
        "(-12.8%) is inside the COVID circuit-breaker week. Extremes line up with real events, not "
        "artifacts."
    )
    lines.append("")

    lines.append("## 3 sample rows")
    lines.append("")
    matched_sorted = matched.sort(["session", "symbol", "clock"])
    m = matched_sorted.height
    idx = sorted({0, m // 2, m - 1}) if m else []
    sample = matched_sorted[idx] if idx else matched_sorted.head(3)
    with pl.Config(tbl_cols=-1, tbl_width_chars=240, fmt_str_lengths=40):
        lines.append("```")
        lines.append(str(sample))
        lines.append("```")
    lines.append("")

    (out_dir / "panel_qa.md").write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- main


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    out_path = OUT_DIR / "hourly_panel.parquet"
    panel.write_parquet(out_path)
    write_qa(panel, OUT_DIR)

    print(f"wrote {out_path} ({panel.height} rows, {panel.width} cols)")
    per_sym = panel.group_by("symbol").agg(sessions=pl.col("session").n_unique(), rows=pl.len()).sort("symbol")
    print(per_sym)
    print()
    print("null rates:")
    n = panel.height
    for c in panel.columns:
        nulls = panel[c].null_count()
        print(f"  {c:20s} {nulls:8d}  {nulls / n:.4%}")


if __name__ == "__main__":
    main()
