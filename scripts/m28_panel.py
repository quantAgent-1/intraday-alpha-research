"""M28 panel builder: per-name-day signals + outcome, sourced ONLY from bars1m.

Spec: research/experiments/M28-open-cross-battery/REGISTRATION.md sections 3, 6, 7.

Every price here comes from `data/raw/sip/bars1m` and nothing else. That is deliberate:
bars1d is RAW, bars1m is ADJUSTED, trades are RAW, and mixing them produced three separate
large spurious results on 2026-07-26. Sourcing one lake makes that class impossible.

Nothing in this file may read a price at or after 09:28:00 ET except the OUTCOME columns
(the 09:30 opening bar and the 15:40-15:45 exit), which are never inputs to any signal.

    uv run python scripts/m28_panel.py
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
BARS1M = REPO / "data" / "raw" / "sip" / "bars1m"
EXP = REPO / "research" / "experiments" / "M28-open-cross-battery"
OUT = EXP / "panel.parquet"

ET = "America/New_York"
PM_START = 4 * 3600                      # 04:00:00 pre-market window start
DECISION = 9 * 3600 + 28 * 60            # 09:28:00 -- inputs must be strictly before this
PM_LATE = 8 * 3600 + 58 * 60             # 08:58:00 -- late pre-market leg
RTH_OPEN = 9 * 3600 + 30 * 60            # 09:30:00
RTH_CLOSE = 16 * 3600                    # 16:00:00
EXIT_LO = 15 * 3600 + 40 * 60            # exit window 15:40..15:45
EXIT_HI = 15 * 3600 + 45 * 60

FIRST_SESSION = "2024-01-02"             # test window start (lookback comes from 2023-10+)
LAST_SESSION = "2026-05-31"              # holdout >= 2026-06-01 is never read

MIN_RTH_BARS = 300
MIN_PRIOR_SESSIONS = 22
MIN_PM_BARS = 5

SIGNALS_A = ["ret1", "ret5", "ret21", "clv", "dvol_z", "rvol21",
             "ret1_x_dvol", "on_prev", "id_minus_on"]
SIGNALS_B = ["pm_ret", "pm_vol_z", "pm_range", "pm_late", "pm_accel"]
SIGNALS = SIGNALS_A + SIGNALS_B


def _sec_expr() -> pl.Expr:
    dt = pl.from_epoch(pl.col("ts"), time_unit="ns").dt.convert_time_zone(ET)
    return (dt.dt.hour().cast(pl.Int32) * 3600
            + dt.dt.minute().cast(pl.Int32) * 60
            + dt.dt.second().cast(pl.Int32))


def _date_expr() -> pl.Expr:
    return (pl.from_epoch(pl.col("ts"), time_unit="ns")
            .dt.convert_time_zone(ET).dt.strftime("%Y-%m-%d"))


def daily_frame(sym: str) -> pl.DataFrame | None:
    """Aggregate every owned minute bar of `sym` into one row per ET session."""
    files = sorted((BARS1M / sym).glob("*.parquet"))
    if not files:
        return None
    parts = []
    for f in files:
        d = pl.read_parquet(f, columns=["ts", "open", "high", "low", "close", "volume", "vwap"])
        if d.height:
            parts.append(d)
    if not parts:
        return None
    d = pl.concat(parts).with_columns(_date_expr().alias("date"), _sec_expr().alias("sec")).sort(
        ["date", "sec"])
    d = d.filter((pl.col("close") > 0) & (pl.col("date") <= LAST_SESSION))

    rth = d.filter((pl.col("sec") >= RTH_OPEN) & (pl.col("sec") < RTH_CLOSE))
    pm = d.filter((pl.col("sec") >= PM_START) & (pl.col("sec") < DECISION))
    ex = d.filter((pl.col("sec") >= EXIT_LO) & (pl.col("sec") <= EXIT_HI))

    g_rth = rth.group_by("date").agg(
        pl.col("open").first().alias("o"),
        pl.col("close").last().alias("c"),
        pl.col("high").max().alias("h"),
        pl.col("low").min().alias("l"),
        pl.col("volume").sum().alias("vol"),
        (pl.col("vwap") * pl.col("volume")).sum().alias("dv"),
        pl.len().alias("n_rth"),
    )
    g_pm = pm.group_by("date").agg(
        pl.col("close").last().alias("pm_last"),
        pl.col("high").max().alias("pm_h"),
        pl.col("low").min().alias("pm_l"),
        pl.col("volume").sum().alias("pm_vol"),
        (pl.col("volume") > 0).sum().alias("pm_nbars"),
    )
    g_late = pm.filter(pl.col("sec") < PM_LATE).group_by("date").agg(
        pl.col("close").last().alias("pm_ref_0858"))
    g_ex = ex.group_by("date").agg(pl.col("close").last().alias("exit_px"))

    out = (g_rth.join(g_pm, on="date", how="left")
                .join(g_late, on="date", how="left")
                .join(g_ex, on="date", how="left")
                .sort("date"))
    return out.with_columns(pl.lit(sym).alias("sym"))


def signals_for(sym: str) -> tuple[list[dict], dict]:
    df = daily_frame(sym)
    if df is None or df.height < MIN_PRIOR_SESSIONS + 2:
        return [], {"sym": sym, "sessions": 0, "kept": 0}
    d = df.to_dicts()
    n = len(d)
    c = np.array([r["c"] for r in d], dtype=float)
    o = np.array([r["o"] for r in d], dtype=float)
    dv = np.array([r["dv"] for r in d], dtype=float)
    pmv = np.array([(r["pm_vol"] if r["pm_vol"] is not None else 0.0) for r in d], dtype=float)
    cc = np.full(n, np.nan)
    cc[1:] = c[1:] / c[:-1] - 1.0

    funnel = {"n_sessions": n, "pre_window": 0, "few_rth": 0, "no_exit": 0,
              "no_hist": 0, "bad_price": 0, "no_pm": 0}
    recs: list[dict] = []
    for i in range(n):
        r = d[i]
        date = r["date"]
        if date < FIRST_SESSION or date > LAST_SESSION:
            funnel["pre_window"] += 1
            continue
        if i < MIN_PRIOR_SESSIONS:
            funnel["no_hist"] += 1
            continue
        if (r["n_rth"] or 0) < MIN_RTH_BARS:
            funnel["few_rth"] += 1
            continue
        if r["exit_px"] is None or not np.isfinite(r["exit_px"]):
            funnel["no_exit"] += 1
            continue
        if not (np.isfinite(o[i]) and o[i] > 0 and np.isfinite(c[i - 1]) and c[i - 1] > 0):
            funnel["bad_price"] += 1
            continue

        w_dv = dv[i - 21:i]                                    # trailing 21 completed sessions
        w_pv = pmv[i - 21:i]
        sd_dv, sd_pv = float(np.std(w_dv)), float(np.std(w_pv))
        ret1 = c[i - 1] / o[i - 1] - 1.0
        dvol_z = (dv[i - 1] - float(np.mean(w_dv))) / sd_dv if sd_dv > 0 else np.nan
        hl = d[i - 1]["h"] - d[i - 1]["l"]
        on_prev = o[i - 1] / c[i - 2] - 1.0 if c[i - 2] > 0 else np.nan

        rec = {
            "sym": sym, "date": date,
            # ---- group A: completed prior sessions ----
            "ret1": ret1,
            "ret5": c[i - 1] / c[i - 6] - 1.0 if c[i - 6] > 0 else np.nan,
            "ret21": c[i - 1] / c[i - 22] - 1.0 if c[i - 22] > 0 else np.nan,
            "clv": ((d[i - 1]["c"] - d[i - 1]["l"]) / hl - 0.5) if hl > 0 else np.nan,
            "dvol_z": dvol_z,
            "rvol21": float(np.nanstd(cc[i - 21:i])),
            "ret1_x_dvol": ret1 * dvol_z if np.isfinite(dvol_z) else np.nan,
            "on_prev": on_prev,
            "id_minus_on": ret1 - on_prev if np.isfinite(on_prev) else np.nan,
            # ---- outcome (never an input) ----
            "ret_bps": (r["exit_px"] / o[i] - 1.0) * 1e4,
            "open_px": o[i], "exit_px": r["exit_px"],
            "dollar_vol_prev": dv[i - 1], "close_prev": c[i - 1],
            "rng_prev": hl / c[i - 1] if c[i - 1] > 0 else np.nan,
        }
        # ---- group B: current-session pre-market, strictly before 09:28 ----
        pm_ok = (r["pm_nbars"] or 0) >= MIN_PM_BARS and r["pm_last"] is not None
        if not pm_ok:
            funnel["no_pm"] += 1
        pm_ret = (r["pm_last"] / c[i - 1] - 1.0) if pm_ok else np.nan
        pm_late = (r["pm_last"] / r["pm_ref_0858"] - 1.0) if (
            pm_ok and r["pm_ref_0858"] and r["pm_ref_0858"] > 0) else np.nan
        rec["pm_ret"] = pm_ret
        rec["pm_vol_z"] = ((r["pm_vol"] - float(np.mean(w_pv))) / sd_pv
                           if pm_ok and sd_pv > 0 else np.nan)
        rec["pm_range"] = ((r["pm_h"] - r["pm_l"]) / c[i - 1]) if pm_ok else np.nan
        rec["pm_late"] = pm_late
        rec["pm_accel"] = (pm_late - (pm_ret - pm_late)) if np.isfinite(pm_late) else np.nan
        recs.append(rec)
    funnel["sym"] = sym
    funnel["kept"] = len(recs)
    return recs, funnel


def main() -> int:
    uni = json.loads((EXP / "universe.json").read_text(encoding="utf-8"))
    syms = uni["tradeable"]
    t0 = time.time()
    print(f"M28 panel: {len(syms)} tradeable symbols")
    rows, funnels = [], []
    with ProcessPoolExecutor(max_workers=12) as ex:
        for i, (recs, fn) in enumerate(ex.map(signals_for, syms), 1):
            rows.extend(recs)
            funnels.append(fn)
            if i % 40 == 0:
                print(f"  {i}/{len(syms)}  rows={len(rows):,}  {time.time() - t0:.0f}s")
    if not rows:
        print("NO ROWS -- refusing to write")
        return 1
    df = pl.DataFrame(rows)
    df.write_parquet(OUT)
    pl.DataFrame(funnels).write_parquet(EXP / "panel_funnel.parquet")
    print(f"\nwrote {OUT.relative_to(REPO)}  rows={df.height:,}  "
          f"names={df['sym'].n_unique()}  sessions={df['date'].n_unique()}  "
          f"{df['date'].min()}..{df['date'].max()}  in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
