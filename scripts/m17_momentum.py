"""M17 cross-sectional + factor momentum (registered M17-xsect-factor-momentum-v1).

RESEARCH-ONLY side-ledger: overnight holding is out-of-mission for deploy.
Frozen spec (M3_REGISTRATION.md M17). Convention pinned: rebalance at end of month m,
hold month m+1; PRIMARY signal = close(end m-1)/close(end m-12) - 1 (skips month m,
uses the prior 11 monthly returns) == the registered "t-12..t-2, skip t-1" with t=m+1
(the classic 2-12 ranking). SECONDARY: Cell A 6-1 = close(m-1)/close(m-6)-1;
Cell B 6m = close(m)/close(m-6)-1. Secondaries are report-only; primaries decide.

Costs: cost_frac = sum|dw| x (rate per side), rate A=5bps, B=2bps (sum|dw| counts both
buys and sells, i.e. two-way traded notional). Delistings: final partial-month return to
the last available close, then the slot drops at the next rebalance (count reported).
"""
import numpy as np
import polars as pl

BARS = pl.read_parquet("data/external/m17_daily_bars.parquet")
W = pl.read_parquet("data/external/index_weights_monthly.parquet")
ETFS = ["XLK","XLF","XLE","XLV","XLI","XLY","XLP","XLU","XLB","XLRE","XLC",
        "MTUM","VLUE","QUAL","USMV","SIZE","IWF","IWD","IWM","QQQ"]

# ---- monthly close grid ----
B = BARS.with_columns(pl.col("session").str.slice(0, 7).alias("ym"))
ME = (B.sort("session").group_by("symbol", "ym").agg(pl.col("close").last().alias("px"),
                                                     pl.col("session").last().alias("me_date")))
ME = ME.sort(["symbol", "ym"])
months = sorted(ME["ym"].unique().to_list())
mi = {m: i for i, m in enumerate(months)}
px = {(r["symbol"], r["ym"]): r["px"] for r in ME.iter_rows(named=True)}

def close_at(sym, m_idx):
    if m_idx < 0 or m_idx >= len(months):
        return None
    return px.get((sym, months[m_idx]))

def mom(sym, m_idx, back_hi, back_lo):
    a, b = close_at(sym, m_idx - back_lo), close_at(sym, m_idx - back_hi)
    if a is None or b is None or b <= 0:
        return None
    return a / b - 1.0

def fwd_ret(sym, m_idx):
    a, b = close_at(sym, m_idx + 1), close_at(sym, m_idx)
    if b is None or b <= 0:
        return None
    if a is None:  # delisted during holding month: last daily close within that month
        nxt = months[m_idx + 1] if m_idx + 1 < len(months) else None
        if nxt is None:
            return None
        rows = B.filter((pl.col("symbol") == sym) & (pl.col("ym") == nxt)).sort("session")
        if rows.height == 0:
            return None
        return float(rows["close"][-1]) / b - 1.0
    return a / b - 1.0

# ---- PIT membership per month (weights table is monthly) ----
spx = W.filter(pl.col("index") == "SPX").with_columns(
    pl.col("asof_date").str.slice(0, 7).alias("ym"))
members = {m: set(g["ticker"].to_list()) for (m,), g in spx.group_by(["ym"])}
member_months = sorted(members)

def membership_for(m):  # latest weights month <= m
    elig = [x for x in member_months if x <= m]
    return members[elig[-1]] if elig else set()

def run_cell_a(hi, lo, label):
    delist_n = 0
    recs = []
    for m in months:
        i = mi[m]
        if i < 13 or i + 1 >= len(months) or m < "2020-12" or m > "2026-05":
            continue
        mem = membership_for(m)
        sigs = []
        for s in mem:
            v = mom(s, i, hi, lo)
            if v is not None and close_at(s, i) is not None:
                sigs.append((s, v))
        if len(sigs) < 100:
            continue
        sigs.sort(key=lambda x: x[1])
        k = len(sigs) // 10
        d1, d10 = [s for s, _ in sigs[:k]], [s for s, _ in sigs[-k:]]
        rets = {}
        for grp in (d1, d10):
            rs = []
            for s in grp:
                r = fwd_ret(s, i)
                if r is None:
                    delist_n += 1
                    continue
                rs.append(r)
            rets[id(grp)] = float(np.mean(rs)) if rs else 0.0
        uni = [fwd_ret(s, i) for s, _ in sigs]
        uni = [r for r in uni if r is not None]
        recs.append({"m": m, "d10": rets[id(d10)], "d1": rets[id(d1)],
                     "ew": float(np.mean(uni)), "n": len(sigs),
                     "d10_names": set(d10), "d1_names": set(d1)})
    df = recs
    # turnover + costs (EW within decile; sum|dw| ~ 2 x fraction replaced + drift term ignored)
    for j, r in enumerate(df):
        if j == 0:
            r["to10"] = r["to1"] = 2.0  # initial build: buy full book
            continue
        p10, p1 = df[j-1]["d10_names"], df[j-1]["d1_names"]
        r["to10"] = 2.0 * (1 - len(r["d10_names"] & p10) / max(len(r["d10_names"]), 1))
        r["to1"] = 2.0 * (1 - len(r["d1_names"] & p1) / max(len(r["d1_names"]), 1))
    ls = np.array([r["d10"] - r["d1"] - 0.0005 * (r["to10"] + r["to1"]) for r in df])
    lo_net = np.array([r["d10"] - 0.0005 * r["to10"] for r in df])
    ew = np.array([r["ew"] for r in df])
    n = len(ls)
    def t(x):
        return float(np.mean(x) / (np.std(x, ddof=1) / np.sqrt(len(x))))
    ann = 12.0
    print(f"\nCell A [{label}] n={n} months, avg universe {np.mean([r['n'] for r in df]):.0f}, "
          f"delist-handled {delist_n}")
    print(f"  D10-D1 net : {np.mean(ls)*100:+.2f}%/mo  t={t(ls):+.2f}  ann {np.mean(ls)*ann*100:+.1f}%  "
          f"maxDD {min(np.minimum.accumulate(np.cumprod(1+ls))/np.maximum.accumulate(np.cumprod(1+ls)))-0 if n else 0:.2f}")
    print(f"  D10 long net vs EW: {np.mean(lo_net)*100:+.2f}%/mo vs {np.mean(ew)*100:+.2f}%/mo  "
          f"excess ann {(np.mean(lo_net)-np.mean(ew))*ann*100:+.1f}%  t(excess)={t(lo_net-ew):+.2f}")
    yr = {}
    for r, v in zip(df, ls, strict=True):
        yr.setdefault(r["m"][:4], []).append(v)
    print("  L/S by year: " + "  ".join(f"{y}:{np.mean(v)*100:+.1f}%/mo" for y, v in sorted(yr.items())))
    worst = sorted(zip([r['m'] for r in df], ls, strict=True), key=lambda x: x[1])[:3]
    print("  worst L/S months: " + ", ".join(f"{m} {v*100:+.1f}%" for m, v in worst))
    return np.mean(ls), t(ls), (np.mean(lo_net) - np.mean(ew)) * ann

def run_cell_b(hi, lo, label):
    recs = []
    for m in months:
        i = mi[m]
        if i < 13 or i + 1 >= len(months) or m < "2020-12" or m > "2026-05":
            continue
        sigs = [(s, mom(s, i, hi, lo)) for s in ETFS]
        sigs = [(s, v) for s, v in sigs if v is not None]
        if len(sigs) < 15:
            continue
        sigs.sort(key=lambda x: x[1])
        top = [s for s, _ in sigs[-3:]]
        rs = [fwd_ret(s, i) for s in top]
        rs = [r for r in rs if r is not None]
        uni = [fwd_ret(s, i) for s, _ in sigs]
        uni = [r for r in uni if r is not None]
        spy = fwd_ret("SPY", i)
        recs.append({"m": m, "top": float(np.mean(rs)), "ew": float(np.mean(uni)),
                     "spy": spy if spy is not None else 0.0, "names": set(top)})
    for j, r in enumerate(recs):
        r["to"] = 2.0 if j == 0 else 2.0 * (1 - len(r["names"] & recs[j-1]["names"]) / 3.0)
    strat = np.array([r["top"] - 0.0002 * r["to"] for r in recs])
    ew = np.array([r["ew"] for r in recs])
    spy = np.array([r["spy"] for r in recs])
    def sh(x):
        return float(np.mean(x) / np.std(x, ddof=1) * np.sqrt(12))
    print(f"\nCell B [{label}] n={len(strat)} months")
    print(f"  top-3 net: {np.mean(strat)*100:+.2f}%/mo  Sharpe {sh(strat):+.2f}  "
          f"| EW: {np.mean(ew)*100:+.2f}%/mo Sharpe {sh(ew):+.2f} | SPY: {np.mean(spy)*100:+.2f}%/mo Sharpe {sh(spy):+.2f}")
    print(f"  excess vs EW ann: {(np.mean(strat)-np.mean(ew))*12*100:+.1f}%  vs SPY: {(np.mean(strat)-np.mean(spy))*12*100:+.1f}%")
    yr = {}
    for r, v in zip(recs, strat - ew, strict=True):
        yr.setdefault(r["m"][:4], []).append(v)
    print("  excess-vs-EW by year: " + "  ".join(f"{y}:{np.mean(v)*100:+.1f}%/mo" for y, v in sorted(yr.items())))
    return np.mean(strat), sh(strat), sh(ew), (np.mean(strat) - np.mean(ew)) * 12

print("=== M17 (research-only side-ledger; deploy out-of-mission) ===")
a_ls, a_t, a_exc = run_cell_a(12, 1, "PRIMARY 12-1")
run_cell_a(6, 1, "secondary 6-1")
b_m, b_sh, b_ew_sh, b_exc = run_cell_b(12, 1, "PRIMARY 12-1")
run_cell_b(6, 0, "secondary 6m")

print("\n=== registered verdicts (primaries only) ===")
print(f"Cell A PASS requires: L/S t>=2 AND long-only excess >= +2%/yr  ->  t={a_t:+.2f}, excess={a_exc*100:+.1f}%/yr")
print(f"Cell A KILL if: t<1 or negative  ->  {'KILL' if (a_t < 1 or a_ls < 0 or a_exc < 0) else ('PASS' if (a_t >= 2 and a_exc >= 0.02) else 'BETWEEN')}")
print(f"Cell B PASS requires: Sharpe > EW Sharpe AND excess >= +2%/yr  ->  Sharpe {b_sh:+.2f} vs EW {b_ew_sh:+.2f}, excess {b_exc*100:+.1f}%/yr")
print(f"Cell B verdict: {'PASS' if (b_sh > b_ew_sh and b_exc >= 0.02) else ('KILL' if (b_sh < b_ew_sh and b_exc < 0) else 'BETWEEN')}")
