"""M12 Cells A2 / B / C — completing the registered mechanism horse race.

Registered: M12-mechanism-horse-race-v1 (spec M3_REGISTRATION.md). Inputs now on hand:
- cellA_events.parquet (both panels, single-stock F precomputed; 2020-2026)
- data/external/index_weights_monthly.parquet (SPX monthly IVV; NDX quarterly N-PORT)
- data/external/letf_aum_anchors.csv + registry (index complexes incl. TQQQ/SQQQ/QLD/QID/PSQ)
- TQQQ 1m bars (NDX intraday proxy /3; coverage 2023-07 -> 2026-05)

Documented scope limits (decided before results): the A2 index leg covers the NDX
complex only (SOX weights not owned; no owned intraday SPX proxy); B runs the
index-weight component of PassiveForce (13F passive-share aggregation pending a
separate build). Both noted in the ledger result.
"""
import datetime as dt
import re

import numpy as np
import polars as pl

EV = pl.read_parquet("research/experiments/M12-mechanism/cellA_events.parquet")
W = pl.read_parquet("data/external/index_weights_monthly.parquet")
REG = pl.read_csv("data/external/letf_fund_registry.csv")
ANC = pl.read_csv("data/external/letf_aum_anchors.csv")

# ---------------- NDX-complex flow coefficient (t-1 step function) ----------------
def lev_from_note(note, fallback):
    if not isinstance(note, str):
        return fallback
    m = re.search(r"(\d+(?:\.\d+)?)\s*X", note, re.I)
    if not m:
        return fallback
    mag = float(m.group(1))
    return -mag if re.search(r"bear|short|inverse", note, re.I) else mag

idx_funds = REG.filter(pl.col("underlying") == "NDX")["ticker"].to_list()
anc = ANC.filter(pl.col("ticker").is_in(idx_funds)).join(
    REG.select("ticker", "leverage"), on="ticker"
)
anc = anc.with_columns(
    pl.struct(["note", "leverage"]).map_elements(
        lambda s: lev_from_note(s["note"], s["leverage"]), return_dtype=pl.Float64
    ).alias("lev")
).with_columns(
    (pl.col("lev") * (pl.col("lev") - 1) * pl.col("aum_usd")).alias("coef"),
    pl.col("asof_date").str.to_date().alias("adate"),
).sort("adate")
# daily step: total NDX-complex coef effective strictly before each event date
dates = EV.select(pl.col("dte").unique().sort()).to_series().to_list()
coef_rows = []
for d in dates:
    a = anc.filter(pl.col("adate") < d)
    if a.height == 0:
        coef_rows.append({"dte": d, "coef_ndx": 0.0})
        continue
    last = a.group_by("ticker").agg(pl.col("coef").last())
    coef_rows.append({"dte": d, "coef_ndx": float(last["coef"].sum())})
CO = pl.DataFrame(coef_rows)

# ---------------- NDX intraday return proxy (TQQQ open->15:55 / 3) ----------------
t = pl.read_parquet("data/raw/sip/bars1m/TQQQ").with_columns(
    pl.from_epoch("ts", time_unit="ns").dt.replace_time_zone("UTC")
    .dt.convert_time_zone("America/New_York").alias("et")
).with_columns(pl.col("et").dt.date().alias("dte"), pl.col("et").dt.time().alias("tm"))
opens = t.filter(pl.col("tm") >= dt.time(9, 30)).sort("et").group_by("dte").agg(
    pl.col("open").first().alias("tq_open")
)
at1555 = t.filter(pl.col("tm") <= dt.time(15, 55)).sort("et").group_by("dte").agg(
    pl.col("close").last().alias("tq_1555")
)
RNDX = opens.join(at1555, on="dte").with_columns(
    ((pl.col("tq_1555") / pl.col("tq_open") - 1) / 3).alias("r_ndx")
).select("dte", "r_ndx")

# ---------------- index weights (strictly-prior step) ----------------
def weight_join(ev, index_name, out_col):
    w = W.filter(pl.col("index") == index_name).with_columns(
        pl.col("asof_date").str.to_date().alias("adate")
    ).select("ticker", "adate", "weight").sort("adate")
    ev = ev.sort("dte")
    j = ev.join_asof(
        w.rename({"ticker": "symbol"}).sort("adate"),
        left_on="dte", right_on="adate", by="symbol",
        strategy="backward", allow_exact_matches=False,
    )
    return j.rename({"weight": out_col}).drop("adate")

ev = EV.sort("dte")
ev = weight_join(ev, "NDX", "w_ndx")
ev = weight_join(ev, "SPX", "w_spx")
ev = ev.with_columns(pl.col("w_ndx").fill_null(0.0), pl.col("w_spx").fill_null(0.0))
ev = ev.join(CO, on="dte", how="left").join(RNDX, on="dte", how="left")
ev = ev.with_columns(
    (pl.col("coef_ndx").fill_null(0.0) * pl.col("r_ndx").fill_null(0.0) * pl.col("w_ndx"))
    .alias("F_idx_usd")
).with_columns(
    ((pl.col("F_usd").fill_null(0.0) + pl.col("F_idx_usd")) / pl.col("adv20_dollars"))
    .alias("F_tot_adv")
)

def dirf(x):
    return float((x["net_bps"] > 0).mean())

print("=== Cell A2: index-LETF leg (NDX complex; TQQQ window 2023-07+) ===")
sub = ev.filter(pl.col("r_ndx").is_not_null() & (pl.col("dte") >= dt.date(2023, 7, 1)))
for label, col in [("A (single-stock)", "F_adv"), ("A2 (+index leg)", "F_tot_adv")]:
    h = sub.filter(pl.col(col).abs() > 0)
    al = h.filter((pl.col("sg") * pl.col(col).sign()) > 0)
    an = h.filter((pl.col("sg") * pl.col(col).sign()) < 0)
    qs = h[col].abs().quantile(2 / 3)
    t3 = h.filter(pl.col(col).abs() > qs)
    t3a, t3n = t3.filter((pl.col("sg") * pl.col(col).sign()) > 0), t3.filter((pl.col("sg") * pl.col(col).sign()) < 0)
    print(f"{label}: aligned n={al.height} net={al['net_bps'].mean():+.2f} | anti n={an.height} "
          f"net={an['net_bps'].mean():+.2f} | lift={al['net_bps'].mean()-an['net_bps'].mean():+.2f} | "
          f"T3 lift={t3a['net_bps'].mean()-t3n['net_bps'].mean():+.2f} (n={t3a.height}/{t3n.height})")

print("\n=== Cell B (partial): index-weight variable ===")
cells = ev.with_columns(pl.col("dte").dt.year().alias("yr")).group_by("symbol", "yr").agg(
    n=pl.len(), w=pl.col("w_ndx").mean(), dir=(pl.col("net_bps") > 0).mean(),
    net=pl.col("net_bps").mean()).filter(pl.col("n") >= 50).sort("w", descending=True)
k = cells.height // 3
print(f"name-year cells={cells.height}: TOP-w tercile dir={cells.head(k)['dir'].mean():.3f} "
      f"net={cells.head(k)['net'].mean():+.2f} | BOTTOM dir={cells.tail(k)['dir'].mean():.3f} "
      f"net={cells.tail(k)['net'].mean():+.2f}")
print("top-8 by NDX weight:")
print(cells.head(8))
g26 = ev.filter((pl.col("symbol").is_in(["GOOGL", "NVDA", "MU"])) & (pl.col("dte").dt.year() >= 2025))
print(g26.group_by("symbol", pl.col("dte").dt.year().alias("yr")).agg(
    w_ndx=pl.col("w_ndx").mean().round(4), F_adv=pl.col("F_adv").abs().mean().round(5),
    dir=(pl.col("net_bps") > 0).mean().round(3)).sort("symbol", "yr"))

print("\n=== Cell C: joint horse race (session-block bootstrap, 1000 reps) ===")
d = ev.with_columns(
    ((pl.col("sg") * pl.col("F_adv").sign()) * pl.col("F_adv").abs().sqrt()).alias("x_flow"),
    (pl.col("w_ndx").log1p()).alias("x_w"),
    pl.col("adv20_dollars").log().alias("x_adv"),
    pl.col("dte").dt.year().alias("yr"),
).select("session", "net_bps", "x_flow", "x_w", "x_adv", "panel").drop_nulls()
for c in ["x_flow", "x_w", "x_adv"]:
    mu, sd = d[c].mean(), d[c].std()
    d = d.with_columns(((pl.col(c) - mu) / sd).alias(c))
X = d.select("x_flow", "x_w", "x_adv").to_numpy()
X = np.column_stack([np.ones(len(X)), X])
y = d["net_bps"].to_numpy()
sess = d["session"].to_numpy()
beta = np.linalg.lstsq(X, y, rcond=None)[0]
uniq = np.unique(sess)
rng = np.random.default_rng(7)
bs = []
for _ in range(1000):
    pick = rng.choice(uniq, size=len(uniq), replace=True)
    idx = np.concatenate([np.flatnonzero(sess == s) for s in pick])
    Xb, yb = X[idx], y[idx]
    bs.append(np.linalg.lstsq(Xb, yb, rcond=None)[0])
bs = np.array(bs)
names = ["const", "flow (sign*sqrt|F/ADV|)", "ln(1+w_ndx)", "ln ADV (control)"]
for i, nm in enumerate(names):
    lo, hi = np.percentile(bs[:, i], [2.5, 97.5])
    print(f"{nm:26s} beta={beta[i]:+.3f}  95%CI=[{lo:+.3f},{hi:+.3f}]  "
          f"{'SURVIVES' if lo > 0 or hi < 0 else 'null'}")
print(f"n={len(y)} events, {len(uniq)} sessions")
