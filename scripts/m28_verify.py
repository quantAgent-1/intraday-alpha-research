"""M28 correctness verification. Run BEFORE any statistic is interpreted.

These are outcome-independent checks: each one can fail regardless of whether the strategy
works, and each targets a specific way a backtest lies to its author.

  T1 LOOK-AHEAD (black box). Multiply every price in every minute bar at or after 09:28 on
     the target session by 1.05, re-run the panel builder against the perturbed copy, and
     require that all 14 signals are BIT-IDENTICAL while the outcome ret_bps MOVES. Perturbing
     rather than deleting is what makes this a real test: the row survives, so every signal is
     actually compared, and the outcome must respond -- proving the perturbation truly reached
     the data the outcome reads. Only the data root is redirected; nothing inside the builder
     is patched, so this exercises the shipped code path.
  T2 INDEPENDENT RECOMPUTE. Recompute ret_bps and pm_ret straight from the parquet files
     with different code, and compare.
  T3 OPEN ANCHOR. The 09:30 minute-bar open must be the same price a market-on-open order
     receives. Cross-checked against the RAW bars1d daily open using WITHIN-DAY RATIOS so
     the raw-vs-adjusted factor cancels.
  T4 HYGIENE. No duplicate (sym,date); no row outside the window; no holdout leakage.

    uv run python scripts/m28_verify.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import m28_panel as P  # noqa: E402

EXP = REPO / "research" / "experiments" / "M28-open-cross-battery"
HOLDOUT_START = "2026-06-01"
N_SAMPLE = 4


def t1_lookahead(panel: pl.DataFrame) -> list[tuple[str, bool, str]]:
    out = []
    rng = np.random.default_rng(7)
    syms = panel["sym"].unique().to_list()
    picks = [syms[i] for i in rng.choice(len(syms), size=min(N_SAMPLE, len(syms)), replace=False)]
    for sym in picks:
        rows = panel.filter(pl.col("sym") == sym).sort("date")
        if rows.height < 5:
            continue
        target = rows["date"][(rows.height // 2 + 37 * len(out)) % rows.height]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "bars1m"
            (root / sym).mkdir(parents=True)
            for f in sorted((P.BARS1M / sym).glob("*.parquet")):
                d = pl.read_parquet(f)
                d = d.with_columns(P._date_expr().alias("_d"), P._sec_expr().alias("_s"))
                # TWO different factors, deliberately: a single factor would cancel in
                # the exit/open ratio and the outcome would not move, making the whole
                # test vacuous. 1.05 on [09:28, 15:40) and 1.10 from 15:40 on means the
                # outcome MUST shift by ~476 bps while every signal must stay identical.
                mid = (pl.col("_d") == target) & (pl.col("_s") >= P.DECISION) & (
                    pl.col("_s") < P.EXIT_LO)
                late = (pl.col("_d") == target) & (pl.col("_s") >= P.EXIT_LO)
                for col in ("open", "high", "low", "close", "vwap"):
                    if col in d.columns:
                        d = d.with_columns(
                            pl.when(mid).then(pl.col(col) * 1.05)
                            .when(late).then(pl.col(col) * 1.10)
                            .otherwise(pl.col(col)).alias(col))
                d.drop(["_d", "_s"]).write_parquet(root / sym / f.name)
            keep = P.BARS1M
            try:
                P.BARS1M = root
                recs, _fn = P.signals_for(sym)
            finally:
                P.BARS1M = keep
        pert = pl.DataFrame(recs).filter(pl.col("date") == target) if recs else pl.DataFrame()
        ref = rows.filter(pl.col("date") == target)
        if pert.height == 0 or ref.height == 0:
            out.append((f"T1 {sym} {target}: perturbed row present", False, "row missing"))
            continue
        bad = []
        for sig in P.SIGNALS:
            a, b = ref[sig][0], pert[sig][0]
            if a is None and b is None:
                continue
            if a is None or b is None or not np.isclose(a, b, rtol=0, atol=0, equal_nan=True):
                bad.append(f"{sig}: {a} != {b}")
        out.append((f"T1 {sym} {target}: all 14 signals bit-identical under a +5% post-09:28 "
                    f"price perturbation", not bad,
                    "; ".join(bad)[:120] if bad else "all 14 bit-identical"))
        moved = abs(float(pert["ret_bps"][0]) - float(ref["ret_bps"][0]))
        out.append((f"T1 {sym} {target}: outcome responded to the perturbation "
                    f"(proves it reached the outcome data)", moved > 100.0,
                    f"ret_bps moved {moved:.0f} bps"))
    return out


def t2_recompute(panel: pl.DataFrame) -> list[tuple[str, bool, str]]:
    out = []
    rng = np.random.default_rng(11)
    idx = rng.choice(panel.height, size=min(6, panel.height), replace=False)
    for i in idx:
        r = panel.row(int(i), named=True)
        sym, date = r["sym"], r["date"]
        f = P.BARS1M / sym / f"{date[:7]}.parquet"
        if not f.exists():
            continue
        d = pl.read_parquet(f).with_columns(P._date_expr().alias("d"), P._sec_expr().alias("s"))
        d = d.filter((pl.col("d") == date) & (pl.col("close") > 0)).sort("s")
        rth = d.filter((pl.col("s") >= P.RTH_OPEN) & (pl.col("s") < P.RTH_CLOSE))
        ex = d.filter((pl.col("s") >= P.EXIT_LO) & (pl.col("s") <= P.EXIT_HI))
        if rth.height == 0 or ex.height == 0:
            continue
        ret = (ex["close"][-1] / rth["open"][0] - 1.0) * 1e4
        ok = np.isclose(ret, r["ret_bps"], rtol=1e-9)
        out.append((f"T2 {sym} {date}: ret_bps independently recomputed", bool(ok),
                    f"{ret:.6f} vs {r['ret_bps']:.6f}"))
        pm = d.filter((pl.col("s") >= P.PM_START) & (pl.col("s") < P.DECISION))
        n_pm = int((pm["volume"] > 0).sum()) if pm.height else 0
        if n_pm < P.MIN_PM_BARS:
            out.append((f"T2 {sym} {date}: pre-market guard agrees (panel marks it unusable)",
                        r["pm_ret"] is None or not np.isfinite(r["pm_ret"]),
                        f"{n_pm} bars with volume (need {P.MIN_PM_BARS}); "
                        f"panel pm_ret={r['pm_ret']}"))
        if n_pm >= P.MIN_PM_BARS and r["pm_ret"] is not None:
            pmr = (pm["close"][-1] / r["close_prev"] - 1.0)
            ok2 = np.isclose(pmr, r["pm_ret"], rtol=1e-9)
            out.append((f"T2 {sym} {date}: pm_ret independently recomputed", bool(ok2),
                        f"{pmr:.8f} vs {r['pm_ret']:.8f}"))
            last_pm_sec = int(pm["s"][-1])
            out.append((f"T2 {sym} {date}: last pre-market bar is before 09:28",
                        last_pm_sec < P.DECISION, f"sec={last_pm_sec} < {P.DECISION}"))
    return out


def t3_open_anchor(panel: pl.DataFrame) -> list[tuple[str, bool, str]]:
    """bars1m 09:30 open vs RAW bars1d open, compared as within-day ratios."""
    out = []
    b1d = REPO / "data" / "raw" / "sip" / "bars1d"
    for sym in ["NVDA", "AAPL", "MSFT", "COST"]:
        p = b1d / f"{sym}.parquet"
        if not p.exists():
            continue
        raw = pl.read_parquet(p, columns=["ts", "open", "close"]).with_columns(
            P._date_expr().alias("date"))
        # Both ratios are open -> 16:00 close INSIDE their own lake, so the
        # raw-vs-adjusted factor cancels exactly and only the OPEN anchor is tested.
        parts = []
        for f in sorted((P.BARS1M / sym).glob("*.parquet")):
            dd = pl.read_parquet(f, columns=["ts", "open", "close"])
            if dd.height:
                parts.append(dd)
        b1m = pl.concat(parts).with_columns(
            P._date_expr().alias("date"), P._sec_expr().alias("s"))
        b1m = b1m.filter(
            (pl.col("s") >= P.RTH_OPEN) & (pl.col("s") < P.RTH_CLOSE)).sort("s")
        agg = b1m.group_by("date").agg(pl.col("open").first().alias("o1m"),
                                       pl.col("close").last().alias("c1m"))
        m = panel.filter(pl.col("sym") == sym).join(raw, on="date").join(agg, on="date")
        if m.height < 20:
            continue
        # Estimate the per-MONTH adjustment factor robustly as median(c1d / c1m) -- a month
        # holds at most one dividend and rarely a split -- then compare the OPEN alone.
        # A ratio-of-ratios test conflates the open with the close, and the close genuinely
        # differs (official auction print vs the last continuous minute bar), so it cannot
        # isolate the entry anchor.
        mm = m.with_columns(pl.col("date").str.slice(0, 7).alias("mo"))
        o_err, c_err = [], []
        for _k, g in mm.partition_by("mo", as_dict=True, maintain_order=True).items():
            if g.height < 10:
                continue
            f = float(np.median(g["close"].to_numpy() / g["c1m"].to_numpy()))
            o_err.extend(np.abs(g["open"].to_numpy() / (f * g["o1m"].to_numpy()) - 1) * 1e4)
            c_err.extend(np.abs(g["close"].to_numpy() / (f * g["c1m"].to_numpy()) - 1) * 1e4)
        if not o_err:
            continue
        mo, mc = float(np.median(o_err)), float(np.median(c_err))
        out.append((f"T3 {sym}: bars1m 09:30 open matches the official bars1d open "
                    f"(entry-price anchor)", mo < 3.0,
                    f"OPEN err median {mo:.2f} bps (p90 {np.percentile(o_err, 90):.1f}); "
                    f"close-side err median {mc:.2f} bps for contrast; n={len(o_err)}"))
    return out


def t4_hygiene(panel: pl.DataFrame) -> list[tuple[str, bool, str]]:
    dup = panel.height - panel.select(["sym", "date"]).unique().height
    mx, mn = panel["date"].max(), panel["date"].min()
    return [
        ("T4 no duplicate (sym,date)", dup == 0, f"{dup} duplicates"),
        ("T4 no holdout leakage (max date < 2026-06-01)", mx < HOLDOUT_START, f"max={mx}"),
        ("T4 window respected (min date >= 2024-01-02)", mn >= P.FIRST_SESSION, f"min={mn}"),
        ("T4 outcome always finite", bool(panel["ret_bps"].is_finite().all()), "ret_bps"),
    ]


def main() -> int:
    panel = pl.read_parquet(EXP / "panel.parquet")
    print(f"panel: {panel.height:,} name-days, {panel['sym'].n_unique()} names, "
          f"{panel['date'].n_unique()} sessions\n")
    results: list[tuple[str, bool, str]] = []
    results += t4_hygiene(panel)
    results += t3_open_anchor(panel)
    results += t2_recompute(panel)
    results += t1_lookahead(panel)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
    bad = sum(1 for _n, ok, _d in results if not ok)
    print(f"\nverification: {len(results) - bad}/{len(results)} passed")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
