"""Graveyard re-price: published mid-alphas under corrected denominators.

No new signal, no new threshold, no $1k lens. Statistical edge only.

Outputs: research/experiments/graveyard-reprice/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from enginev51.research_screens.sizing_shadow import (  # noqa: E402
    min_trl,
    psr,
    sample_moments,
    sr_native,
)

OUT = REPO / "research" / "experiments" / "graveyard-reprice"
OUT.mkdir(parents=True, exist_ok=True)

SEED, REPS = 7, 2000
SEC_FEE = 0.206
SLIP_LEG = 0.5

# Measured 2025-06..2026-05 medians (bbo1s), half-spread approx = full/2
# Full-spread medians at clocks from BREAKTHROUGH_ANALYSIS + M27 floors.
# We use half-spread RT = full_entry_hs + full_exit_hs with hs = full/2.
SPREAD_FULL = {
    # name: (0935_full, 1200_full, 1540_full) bps — from breakthrough memo
    "NVDA": (0.8, 0.6, 0.6),
    "GOOGL": (1.6, 0.7, 0.6),
    "TSLA": (2.8, 1.3, 1.0),
    "AMD": (5.4, 2.4, 1.5),
    "MU": (6.9, 3.4, 2.4),
    "MRVL": (8.2, 3.2, 2.2),
    "LRCX": (9.5, 4.6, 2.0),
    "TXN": (12.1, 4.3, 1.9),
    "AMAT": (14.0, 6.3, 3.7),
    "KLAC": (30.0, 11.9, 7.5),
}

LIQUID = {"NVDA", "GOOGL", "TSLA", "AMD", "MU", "AAPL", "MSFT", "META", "AMZN", "NFLX", "AVGO"}


def day_cluster_ci(sessions: np.ndarray, values: np.ndarray, seed=SEED, reps=REPS):
    """Bootstrap CI on mean by resampling sessions."""
    rng = np.random.default_rng(seed)
    # map session -> values
    order = np.argsort(sessions)
    sessions = sessions[order]
    values = values[order]
    # unique sessions
    uniq, inv = np.unique(sessions, return_inverse=True)
    buckets = [values[inv == i] for i in range(len(uniq))]
    n = len(uniq)
    if n == 0:
        return float("nan"), float("nan"), float("nan"), 0
    means = []
    for _ in range(reps):
        pick = rng.integers(0, n, size=n)
        parts = [buckets[i] for i in pick]
        means.append(np.concatenate(parts).mean())
    means = np.asarray(means)
    return float(values.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)), int(n)


def adia_daily(sessions: np.ndarray, values: np.ndarray) -> dict:
    """Equal-weight mean per session then ADIA stats on daily series."""
    df = pl.DataFrame({"session": sessions.astype(str), "v": values.astype(float)})
    daily = (
        df.group_by("session")
        .agg(pl.col("v").mean().alias("d"))
        .sort("session")["d"]
        .to_numpy()
    )
    if len(daily) < 5:
        return {"T": len(daily), "sr": None, "psr0": None, "mintrl": None, "mean_d": None}
    g3, g4, rho = sample_moments(daily)
    sr = sr_native(daily)
    t = int(len(daily))
    p = psr(sr, 0.0, t, rho, g3, g4)
    mt = min_trl(sr, 0.0, 0.05, rho, g3, g4)
    return {
        "T": t,
        "mean_d": float(daily.mean()),
        "sd_d": float(daily.std(ddof=1)),
        "sr": float(sr),
        "psr0": float(p) if p == p else None,
        "mintrl": float(mt) if mt == mt and mt != float("inf") else None,
    }


def rt_cost_open_entry_late_exit(sym: str) -> float:
    """Entry at open print (0 spread) + taker exit at 15:40 half-spread + slip + fee."""
    full = SPREAD_FULL.get(sym)
    if full is None:
        # conservative large-cap proxy if unknown
        exit_hs = 1.5
    else:
        exit_hs = full[2] / 2.0
    return exit_hs + SLIP_LEG + SEC_FEE


def rt_cost_taker_both(sym: str, entry_clock="0935") -> float:
    full = SPREAD_FULL.get(sym)
    if full is None:
        e, x = 5.0, 1.5
    else:
        e = full[0] if entry_clock == "0935" else full[1]
        x = full[2]
    # pay half each leg of full spread
    return e / 2 + x / 2 + 2 * SLIP_LEG + SEC_FEE


# --------------------------------------------------------------------------- M27
def reprice_m27() -> dict:
    path = REPO / "research/experiments/M27-gap-day/events.parquet"
    df = pl.read_parquet(path)
    # File gross already uses taker fills. Reconstruct mid-alpha:
    # pay ~half entry full-spread + half exit full-spread + slips already in fills.
    # entry_spread_bps / exit_spread_bps are full quoted spreads at decision.
    mid = (
        df["gross_bps"]
        + 0.5 * df["entry_spread_bps"]
        + 0.5 * df["exit_spread_bps"]
        + 1.0  # 0.5 slip * 2 legs baked into fills
    )
    df = df.with_columns(mid.alias("mid_alpha_bps"))

    rows = []
    for label, sub in [
        ("all_t50", df),
        ("all_t100", df.filter(pl.col("is_t100"))),
    ]:
        for name in sorted(sub["symbol"].unique().to_list()) + ["POOLED"]:
            s = sub if name == "POOLED" else sub.filter(pl.col("symbol") == name)
            if s.height == 0:
                continue
            sess = s["session"].to_numpy()
            mid_a = s["mid_alpha_bps"].to_numpy()
            mu, lo, hi, ns = day_cluster_ci(sess, mid_a)
            # expression A: open entry free + late exit cost (counterfactual)
            if name == "POOLED":
                costs = np.array([rt_cost_open_entry_late_exit(sym) for sym in s["symbol"]])
            else:
                costs = np.full(s.height, rt_cost_open_entry_late_exit(name))
            net_a = mid_a - costs
            mu_n, lo_n, hi_n, _ = day_cluster_ci(sess, net_a)
            # expression B: measured 0935 taker both ways with SPREAD_FULL
            if name == "POOLED":
                costs_b = np.array([rt_cost_taker_both(sym) for sym in s["symbol"]])
            else:
                costs_b = np.full(s.height, rt_cost_taker_both(name))
            net_b = mid_a - costs_b
            mu_b, lo_b, hi_b, _ = day_cluster_ci(sess, net_b)
            mean_c_a = float(costs.mean())
            mean_c_b = float(costs_b.mean())
            rows.append(
                {
                    "family": "M27",
                    "cell": label,
                    "scope": name,
                    "n": s.height,
                    "n_sess": ns,
                    "mid_mean": mu,
                    "mid_ci": [lo, hi],
                    "mid_ci_lo_gt0": lo > 0,
                    "expr_open_late": {
                        "cost_mean": mean_c_a,
                        "net_mean": mu_n,
                        "net_ci": [lo_n, hi_n],
                        "net_ci_lo_gt0": lo_n > 0,
                        "gross_ge_2x_cost": mu >= 2 * mean_c_a,
                    },
                    "expr_taker_0935": {
                        "cost_mean": mean_c_b,
                        "net_mean": mu_b,
                        "net_ci": [lo_b, hi_b],
                        "net_ci_lo_gt0": lo_b > 0,
                        "gross_ge_2x_cost": mu >= 2 * mean_c_b,
                    },
                    "adia_mid_daily": adia_daily(sess, mid_a),
                    "adia_net_open_late": adia_daily(sess, net_a),
                }
            )

    # dollar-neutral within session: long fades + short opposite? M27 is already signed.
    # Hedged: subtract session equal-weight basket of same-side residuals.
    # Simpler hedge: daily mean mid_alpha minus cross-sectional mean that day (residual).
    df2 = df.with_columns(
        (pl.col("mid_alpha_bps") - pl.col("mid_alpha_bps").mean().over("session")).alias(
            "resid"
        )
    )
    sess = df2["session"].to_numpy()
    resid = df2["resid"].to_numpy()
    mu, lo, hi, ns = day_cluster_ci(sess, resid)
    costs = np.array([rt_cost_open_entry_late_exit(s) for s in df2["symbol"]])
    # hedge leg cost proxy ~0.3 bps (index)
    net_h = resid - costs - 0.5
    mu_n, lo_n, hi_n, _ = day_cluster_ci(sess, net_h)
    rows.append(
        {
            "family": "M27",
            "cell": "t50_cs_resid",
            "scope": "POOLED",
            "n": df2.height,
            "n_sess": ns,
            "mid_mean": mu,
            "mid_ci": [lo, hi],
            "mid_ci_lo_gt0": lo > 0,
            "expr_open_late": {
                "cost_mean": float(costs.mean() + 0.5),
                "net_mean": mu_n,
                "net_ci": [lo_n, hi_n],
                "net_ci_lo_gt0": lo_n > 0,
                "gross_ge_2x_cost": mu >= 2 * float(costs.mean() + 0.5),
            },
            "note": "session-demeaned mid-alpha (removes common factor)",
        }
    )
    return {"rows": rows}


# --------------------------------------------------------------------------- M24
def reprice_m24() -> dict:
    path = REPO / "research/experiments/M24-open-fade/events.parquet"
    df = pl.read_parquet(path)
    # open print -> close print: already single-print entry+exit style; cost ~ fees only
    # Optional: exit continuous 15:40 instead of close — we only have close_px.
    # Primary: treat gross as mid (print-to-print). Cost = SEC fee only (0.206) both legs ~0.2
    fee = SEC_FEE  # one sell-side fee on the flat

    rows = []
    subsets = [
        ("t25_all", df),
        ("t50_all", df.filter(pl.col("is_t50"))),
        ("t25_liquid", df.filter(pl.col("symbol").is_in(list(LIQUID)))),
        ("t50_liquid", df.filter(pl.col("is_t50") & pl.col("symbol").is_in(list(LIQUID)))),
        (
            "t25_bbo10",
            df.filter(pl.col("symbol").is_in(list(SPREAD_FULL.keys()))),
        ),
        (
            "t50_bbo10",
            df.filter(pl.col("is_t50") & pl.col("symbol").is_in(list(SPREAD_FULL.keys()))),
        ),
    ]
    for label, sub in subsets:
        if sub.height < 10:
            continue
        sess = sub["session"].to_numpy()
        gross = sub["gross_bps"].to_numpy()
        mu, lo, hi, ns = day_cluster_ci(sess, gross)
        net = gross - fee
        mu_n, lo_n, hi_n, _ = day_cluster_ci(sess, net)
        # continuous late exit stress: if we had to exit taker at 15:40 instead of close print
        # charge exit hs from SPREAD_FULL when known else 1.5
        costs_x = []
        for sym in sub["symbol"].to_list():
            if sym in SPREAD_FULL:
                costs_x.append(SPREAD_FULL[sym][2] / 2 + SLIP_LEG + SEC_FEE)
            else:
                costs_x.append(1.5 + SLIP_LEG + SEC_FEE)
        costs_x = np.asarray(costs_x)
        net_x = gross - costs_x
        mu_x, lo_x, hi_x, _ = day_cluster_ci(sess, net_x)
        rows.append(
            {
                "family": "M24",
                "cell": label,
                "n": sub.height,
                "n_sess": ns,
                "mid_mean": mu,
                "mid_ci": [lo, hi],
                "mid_ci_lo_gt0": lo > 0,
                "print_to_print_net": {
                    "cost_mean": fee,
                    "net_mean": mu_n,
                    "net_ci": [lo_n, hi_n],
                    "net_ci_lo_gt0": lo_n > 0,
                    "gross_ge_2x_cost": mu >= 2 * fee,
                },
                "stress_taker_exit_1540": {
                    "cost_mean": float(costs_x.mean()),
                    "net_mean": mu_x,
                    "net_ci": [lo_x, hi_x],
                    "net_ci_lo_gt0": lo_x > 0,
                    "gross_ge_2x_cost": mu >= 2 * float(costs_x.mean()),
                },
                "adia_mid_daily": adia_daily(sess, gross),
                "adia_net_print": adia_daily(sess, net),
            }
        )

    # session CS residual
    for cell_name, sub in [
        ("t25_cs_resid", df),
        ("t50_cs_resid", df.filter(pl.col("is_t50"))),
    ]:
        if sub.height < 20:
            continue
        sub = sub.with_columns(
            (pl.col("gross_bps") - pl.col("gross_bps").mean().over("session")).alias("resid")
        )
        # need sessions with >=2 names
        cnt = sub.group_by("session").len()
        keep = cnt.filter(pl.col("len") >= 2)["session"]
        sub = sub.filter(pl.col("session").is_in(keep))
        sess = sub["session"].to_numpy()
        resid = sub["resid"].to_numpy()
        mu, lo, hi, ns = day_cluster_ci(sess, resid)
        net = resid - fee
        mu_n, lo_n, hi_n, _ = day_cluster_ci(sess, net)
        rows.append(
            {
                "family": "M24",
                "cell": cell_name,
                "n": sub.height,
                "n_sess": ns,
                "mid_mean": mu,
                "mid_ci": [lo, hi],
                "mid_ci_lo_gt0": lo > 0,
                "print_to_print_net": {
                    "cost_mean": fee,
                    "net_mean": mu_n,
                    "net_ci": [lo_n, hi_n],
                    "net_ci_lo_gt0": lo_n > 0,
                    "gross_ge_2x_cost": mu >= 2 * fee if abs(mu) > 0 else False,
                },
                "note": "session-demeaned; kills common market day",
            }
        )
    return {"rows": rows}


# --------------------------------------------------------------------------- R2-A
def reprice_r2a() -> dict:
    path = REPO / "research/experiments/R2A-prong0/panel.parquet"
    df = pl.read_parquet(path)
    # signed fade = -sign(oli) * ret ; ret is open->15:45 mid-to-mid
    df = df.with_columns(
        (-pl.col("oli").sign() * pl.col("ret")).alias("fade_bps"),
        pl.col("oli").abs().alias("abs_oli"),
    )
    # per-name top quartile |OLI|
    q3 = df.group_by("sym").agg(pl.col("abs_oli").quantile(0.75).alias("q3"))
    df = df.join(q3, on="sym").filter(pl.col("abs_oli") >= pl.col("q3"))

    rows = []
    subsets = [
        ("topq_all", df),
        ("topq_mega", df.filter(pl.col("tier") == "mega")),
        ("topq_semi", df.filter(pl.col("tier") == "semi")),
        ("topq_liquid5", df.filter(pl.col("sym").is_in(["NVDA", "GOOGL", "TSLA", "AMD", "MU"]))),
    ]
    for label, sub in subsets:
        if sub.height < 30:
            continue
        sess = sub["date"].to_numpy()
        fade = sub["fade_bps"].to_numpy()
        mu, lo, hi, ns = day_cluster_ci(sess, fade)
        # expression: open print entry (0) + late exit cost
        costs = np.array([rt_cost_open_entry_late_exit(s) for s in sub["sym"].to_list()])
        net = fade - costs
        mu_n, lo_n, hi_n, _ = day_cluster_ci(sess, net)
        # taker both (0935 entry) stress
        costs_t = np.array([rt_cost_taker_both(s) for s in sub["sym"].to_list()])
        net_t = fade - costs_t
        mu_t, lo_t, hi_t, _ = day_cluster_ci(sess, net_t)
        mean_c = float(costs.mean())
        rows.append(
            {
                "family": "R2A",
                "cell": label,
                "n": sub.height,
                "n_sess": ns,
                "mid_mean": mu,
                "mid_ci": [lo, hi],
                "mid_ci_lo_gt0": lo > 0,
                "expr_open_late": {
                    "cost_mean": mean_c,
                    "net_mean": mu_n,
                    "net_ci": [lo_n, hi_n],
                    "net_ci_lo_gt0": lo_n > 0,
                    "gross_ge_2x_cost": mu >= 2 * mean_c,
                    "pass_stat_edge": bool(lo_n > 0 and mu >= 2 * mean_c and sub.height >= 250 and ns >= 150),
                },
                "expr_taker_0935": {
                    "cost_mean": float(costs_t.mean()),
                    "net_mean": mu_t,
                    "net_ci": [lo_t, hi_t],
                    "net_ci_lo_gt0": lo_t > 0,
                    "gross_ge_2x_cost": mu >= 2 * float(costs_t.mean()),
                },
                "adia_mid_daily": adia_daily(sess, fade),
                "adia_net_open_late": adia_daily(sess, net),
                "names_pos": _names_pos(sub),
            }
        )

    # CS residual top-q
    sub = df.with_columns(
        (pl.col("fade_bps") - pl.col("fade_bps").mean().over("date")).alias("resid")
    )
    cnt = sub.group_by("date").len()
    keep = cnt.filter(pl.col("len") >= 2)["date"]
    sub = sub.filter(pl.col("date").is_in(keep))
    sess = sub["date"].to_numpy()
    resid = sub["resid"].to_numpy()
    mu, lo, hi, ns = day_cluster_ci(sess, resid)
    costs = np.array([rt_cost_open_entry_late_exit(s) for s in sub["sym"].to_list()])
    net = resid - costs - 0.5
    mu_n, lo_n, hi_n, _ = day_cluster_ci(sess, net)
    rows.append(
        {
            "family": "R2A",
            "cell": "topq_cs_resid",
            "n": sub.height,
            "n_sess": ns,
            "mid_mean": mu,
            "mid_ci": [lo, hi],
            "mid_ci_lo_gt0": lo > 0,
            "expr_open_late": {
                "cost_mean": float(costs.mean() + 0.5),
                "net_mean": mu_n,
                "net_ci": [lo_n, hi_n],
                "net_ci_lo_gt0": lo_n > 0,
                "gross_ge_2x_cost": mu >= 2 * float(costs.mean() + 0.5),
                "pass_stat_edge": bool(
                    lo_n > 0
                    and mu >= 2 * float(costs.mean() + 0.5)
                    and sub.height >= 250
                    and ns >= 150
                ),
            },
            "note": "session-demeaned fade",
        }
    )

    # Dollar-neutral CS portfolio: each day long bottom-OLI tercile fade direction
    # = already signed per name; form equal long/short by ranking fade signal = -sign(oli)
    # Actually portfolio: weight proportional to -sign(oli) among top-q, demean to net 0
    full = pl.read_parquet(path)
    full = full.with_columns(
        (-pl.col("oli").sign()).alias("side"),
        pl.col("oli").abs().alias("abs_oli"),
    )
    q3 = full.group_by("sym").agg(pl.col("abs_oli").quantile(0.75).alias("q3"))
    full = full.join(q3, on="sym").filter(pl.col("abs_oli") >= pl.col("q3"))
    # per day: w = side - mean(side); pnl = sum(w * ret) / sum(|w|)
    daily_pnls = []
    daily_dates = []
    for date, g in full.group_by("date"):
        d = date[0] if isinstance(date, tuple) else date
        side = g["side"].to_numpy().astype(float)
        ret = g["ret"].to_numpy()
        if len(side) < 2:
            continue
        w = side - side.mean()
        denom = np.abs(w).sum()
        if denom < 1e-12:
            continue
        w = w / denom  # gross = 1
        # cost: sum |w_i| * c_i
        syms = g["sym"].to_list()
        c = np.array([rt_cost_open_entry_late_exit(s) for s in syms])
        gross_p = float((w * ret).sum())
        cost_p = float((np.abs(w) * c).sum())
        daily_pnls.append(gross_p - cost_p)
        daily_dates.append(d)
    if daily_pnls:
        daily_pnls = np.asarray(daily_pnls)
        daily_dates = np.asarray(daily_dates)
        mu, lo, hi, ns = day_cluster_ci(daily_dates, daily_pnls)
        # for daily series, each day is one observation — CI on daily mean
        rows.append(
            {
                "family": "R2A",
                "cell": "topq_cs_dollar_neutral_daily",
                "n": int(len(daily_pnls)),
                "n_sess": ns,
                "mid_mean": float(daily_pnls.mean()),  # already net of open-late costs
                "mid_ci": [lo, hi],
                "mid_ci_lo_gt0": lo > 0,
                "expr_open_late": {
                    "cost_mean": "embedded",
                    "net_mean": float(daily_pnls.mean()),
                    "net_ci": [lo, hi],
                    "net_ci_lo_gt0": lo > 0,
                    "gross_ge_2x_cost": None,
                    "pass_stat_edge": bool(lo > 0 and len(daily_pnls) >= 150),
                },
                "adia_net_daily": adia_daily(daily_dates, daily_pnls),
                "note": "gross=1 dollar-neutral among top-q names; open entry + late exit cost embedded",
            }
        )
    return {"rows": rows}


def _names_pos(sub: pl.DataFrame) -> dict:
    out = {}
    for sym in sub["sym"].unique().to_list():
        s = sub.filter(pl.col("sym") == sym)
        out[sym] = {
            "n": s.height,
            "mean_fade": float(s["fade_bps"].mean()),
        }
    return out


def main():
    report = {
        "criteria": "research/experiments/graveyard-reprice/SUCCESS_CRITERIA.md",
        "phase": "statistical_edge_only_no_deploy_book",
        "M27": reprice_m27(),
        "M24": reprice_m24(),
        "R2A": reprice_r2a(),
    }
    # flatten pass scan
    passes = []
    for fam in ("M27", "M24", "R2A"):
        for row in report[fam]["rows"]:
            for k, v in row.items():
                if isinstance(v, dict) and v.get("pass_stat_edge") is True:
                    passes.append({"family": fam, "cell": row.get("cell"), "expr": k, **v})
                if isinstance(v, dict) and v.get("net_ci_lo_gt0") and row.get("mid_ci_lo_gt0"):
                    passes.append(
                        {
                            "family": fam,
                            "cell": row.get("cell"),
                            "expr": k,
                            "note": "mid+net CI-lo>0 (not full pass flags)",
                            "net_mean": v.get("net_mean"),
                            "net_ci": v.get("net_ci"),
                        }
                    )
    report["pass_scan"] = passes

    out_json = OUT / "reprice_results.json"
    out_json.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    _write_report(report)
    print(f"wrote {out_json}")
    print(f"pass_scan entries: {len(passes)}")
    for p in passes[:20]:
        print(p)


def _write_report(report: dict) -> None:
    lines = [
        "# Graveyard re-price — statistical edge only",
        "",
        "Generated by `scripts/graveyard_reprice.py`. No $1k lens. No new thresholds.",
        "Criteria: `SUCCESS_CRITERIA.md`.",
        "",
        "## Method",
        "",
        "- **M27:** reconstruct mid-alpha ≈ file gross + ½ entry spread + ½ exit spread + 1 bp slip RT; "
        "re-price under (a) open-print entry + 15:40 exit cost from measured surface, (b) 09:35 taker both legs.",
        "- **M24:** print-to-print gross as mid; fee-only net; stress continuous 15:40 exit; liquid / bbo10 filters; CS residual.",
        "- **R2-A:** top-quartile |OLI| signed fade (pre-declared gate b object); open+late cost; mega/semi split; CS daily book.",
        "- CIs: session-clustered bootstrap, seed=7, 2000 reps.",
        "",
        "## Headline table",
        "",
        "| family | cell | n | sess | mid mean [CI] | best net mean [CI] | mid CI>0 | net CI>0 | ≥2×cost |",
        "|---|---|---:|---:|---|---|:---:|:---:|:---:|",
    ]

    def fmt_row(fam, r, net_key):
        mid = r.get("mid_mean")
        mci = r.get("mid_ci", [None, None])
        block = r.get(net_key) or {}
        nm = block.get("net_mean")
        nci = block.get("net_ci", [None, None])
        if nm is None:
            return
        lines.append(
            f"| {fam} | {r.get('cell')}/{r.get('scope','')} | {r.get('n')} | {r.get('n_sess')} | "
            f"{mid:.2f} [{mci[0]:.2f},{mci[1]:.2f}] | "
            f"{nm:.2f} [{nci[0]:.2f},{nci[1]:.2f}] | "
            f"{'Y' if r.get('mid_ci_lo_gt0') else 'n'} | "
            f"{'Y' if block.get('net_ci_lo_gt0') else 'n'} | "
            f"{'Y' if block.get('gross_ge_2x_cost') else 'n'} |"
        )

    for r in report["M27"]["rows"]:
        fmt_row("M27", r, "expr_open_late")
    for r in report["M24"]["rows"]:
        fmt_row("M24", r, "print_to_print_net")
    for r in report["R2A"]["rows"]:
        fmt_row("R2A", r, "expr_open_late")

    lines += [
        "",
        "## Pass scan (mechanical)",
        "",
    ]
    if not report["pass_scan"]:
        lines.append("**No cell fully cleared the statistical-edge PASS bar.**")
    else:
        for p in report["pass_scan"]:
            lines.append(f"- `{p}`")

    lines += [
        "",
        "## Interpretation (orchestrator)",
        "",
        "See auto-filled bullets below after run; edit if needed.",
        "",
    ]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
