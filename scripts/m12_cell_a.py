"""M12 Cell A (single-stock leg): LETF-flow alignment vs champion economics.

Registered: M12-mechanism-horse-race-v1 (ledger 2026-07-17; spec M3_REGISTRATION.md).
This runs the SINGLE-STOCK complex leg only (w=1, exactly specified). The index-LETF leg
(x index-weight proxy) and Cell B (PassiveForce) wait on the holdings archive build.

Implementation notes (documented deviations, decided before looking at results):
- r_i,t endpoint: open -> 15:55:10 mid (M6: entry_mid; M11: ref_price proxy). The registered
  text said open->15:50; the 15:55:10 mid is the decision-instant observable and differs by
  ~5 minutes; F remains computable at decision time.
- Leverage era: parsed per-anchor from as-filed seriesName ("1.5X"/"2X" + Bear/Bull);
  registry leverage as fallback. Mid-series changes (TSLL/GGLL/NVDL/NVDU 1.5->2 etc.)
  are therefore era-correct wherever N-PORT anchors carry the name.
- AUM(t-1): last anchor strictly before session date (step function; no interpolation).
- sign(F) == sign(r) by construction for net-long complexes, so the mechanism discriminator
  is intensity |F|/ADV: alignment lift must SCALE with intensity, with zero-complex
  name-days as the momentum control.
"""
import argparse
import re

import polars as pl

# SIM_AUDIT 2026-07-21 F3 correction: the as-of AUM join can anchor on either the
# N-PORT reporting-period END (asof_date, the ORIGINAL convention -> control leg)
# or the FILING/public date (public_date, ~58-60 d later; the true public instant,
# added by scripts/add_public_dates.py). Default is the corrected public anchor.
_ap = argparse.ArgumentParser(description="M12 Cell A single-stock LETF alignment stats.")
_ap.add_argument(
    "--anchor-mode",
    choices=["period", "public"],
    default="public",
    help="AUM as-of anchor date: 'period'=asof_date (reporting-period end, original "
    "convention); 'public'=public_date (filing date, F3 correction). Default: public.",
)
_args = _ap.parse_args()
_ANCHOR_COL = "asof_date" if _args.anchor_mode == "period" else "public_date"

REG = pl.read_csv("data/external/letf_fund_registry.csv")
ANC = pl.read_csv("data/external/letf_aum_anchors.csv")

# --- era-aware leverage per anchor ---
def lev_from_note(note: str, fallback: float) -> float:
    if not isinstance(note, str):
        return fallback
    m = re.search(r"(\d+(?:\.\d+)?)\s*X", note, re.I)
    if not m:
        return fallback
    mag = float(m.group(1))
    bear = bool(re.search(r"bear|short|inverse", note, re.I))
    return -mag if bear else mag

anc = ANC.join(REG.select("ticker", "underlying", "leverage"), on="ticker", how="inner")
anc = anc.with_columns(
    pl.struct(["note", "leverage"]).map_elements(
        lambda s: lev_from_note(s["note"], s["leverage"]), return_dtype=pl.Float64
    ).alias("lev_era")
)
anc = anc.with_columns((pl.col("lev_era") * (pl.col("lev_era") - 1) * pl.col("aum_usd")).alias("coef"))
anc = anc.with_columns(pl.col(_ANCHOR_COL).str.to_date().alias("adate")).sort("ticker", "adate")

# --- panels ---
def load_panel(path: str, mid_col: str) -> pl.DataFrame:
    ev = pl.read_parquet(path)
    ev = ev.with_columns(pl.col("session").str.to_date().alias("dte"),
                         pl.col("side").cast(pl.Float64).alias("sg"))
    ev = ev.rename({mid_col: "mid1555"}) if mid_col != "mid1555" else ev
    return ev

m6 = load_panel("research/experiments/M6-FINAL-basis/events.parquet", "entry_mid").with_columns(pl.lit("M6").alias("panel"))
m11 = load_panel("research/experiments/M11-oos-28/events.parquet", "ref_price").with_columns(pl.lit("M11").alias("panel"))
cols = ["panel", "session", "dte", "symbol", "sg", "mid1555", "net_bps", "adv20_dollars", "basis_bps"]
ev = pl.concat([m6.select(cols), m11.select(cols)])

# --- day return open -> 15:55 mid ---
opens = []
for sym in ev["symbol"].unique().to_list():
    try:
        b = pl.read_parquet(f"data/raw/sip/bars1d/{sym}.parquet")
    except Exception:
        continue
    b = b.with_columns(
        pl.from_epoch("ts", time_unit="ns").dt.replace_time_zone("UTC")
        .dt.convert_time_zone("America/New_York").dt.date().alias("dte")
    ).select("dte", "open").with_columns(pl.lit(sym).alias("symbol"))
    opens.append(b)
op = pl.concat(opens)
ev = ev.join(op, on=["symbol", "dte"], how="left").with_columns(
    (pl.col("mid1555") / pl.col("open") - 1).alias("r_day")
)

# --- per-name-day flow coefficient sum_j L(L-1)*AUM_j(t-1) ---
sessions = ev.select("symbol", "dte").unique()
fund_rows = []
for row in REG.iter_rows(named=True):
    tkr, und = row["ticker"], row["underlying"]
    if und in ("NDX", "SOX", "SPX"):
        continue  # index leg deferred (A2)
    a = anc.filter(pl.col("ticker") == tkr).select("adate", "coef")
    if len(a) == 0:
        continue
    s = sessions.filter(pl.col("symbol") == und).sort("dte")
    if len(s) == 0:
        continue
    j = s.join_asof(a.sort("adate"), left_on="dte", right_on="adate", strategy="backward",
                    allow_exact_matches=False)
    fund_rows.append(j.select("symbol", "dte", "coef"))
fc = pl.concat(fund_rows).group_by("symbol", "dte").agg(pl.col("coef").sum().alias("flow_coef"))
ev = ev.join(fc, on=["symbol", "dte"], how="left").with_columns(pl.col("flow_coef").fill_null(0.0))
ev = ev.with_columns(
    (pl.col("flow_coef") * pl.col("r_day")).alias("F_usd"),
).with_columns(
    (pl.col("F_usd") / pl.col("adv20_dollars")).alias("F_adv"),
    (pl.col("sg") * pl.col("r_day").sign() > 0).alias("aligned"),
    pl.col("dte").dt.year().alias("yr"),
)
# period mode writes the canonical artifact (reproduces the original); public mode
# writes a sibling so the committed period-anchored parquet is never clobbered.
_out_parquet = (
    "research/experiments/M12-mechanism/cellA_events.parquet"
    if _args.anchor_mode == "period"
    else "research/experiments/M12-mechanism/cellA_events_public.parquet"
)
ev.write_parquet(_out_parquet)

def dirf(x: pl.DataFrame) -> float:
    return float((x["net_bps"] > 0).mean())

print(f"=== M12 Cell A (single-stock leg) [anchor-mode={_args.anchor_mode} ({_ANCHOR_COL})] ===")
has = ev.filter(pl.col("flow_coef") > 0)
zero = ev.filter(pl.col("flow_coef") == 0)
print(f"events with complex: {len(has)} | zero-complex control: {len(zero)}")

# (ii) event-level alignment, intensity terciles vs zero-complex control
print("\n-- alignment lift by |F|/ADV intensity (both panels pooled) --")
zc_al, zc_an = zero.filter(pl.col("aligned")), zero.filter(~pl.col("aligned"))
print(f"F=0 control : aligned n={len(zc_al)} net={zc_al['net_bps'].mean():+.2f} dir={dirf(zc_al):.3f} | anti n={len(zc_an)} net={zc_an['net_bps'].mean():+.2f} dir={dirf(zc_an):.3f} | lift={zc_al['net_bps'].mean()-zc_an['net_bps'].mean():+.2f}")
h = has.with_columns(pl.col("F_adv").abs().alias("iF"))
qs = h["iF"].quantile(1/3), h["iF"].quantile(2/3)
for lab, lo, hi in [("T1 low", 0.0, qs[0]), ("T2 mid", qs[0], qs[1]), ("T3 high", qs[1], 1e9)]:
    t = h.filter((pl.col("iF") > lo) & (pl.col("iF") <= hi))
    al, an = t.filter(pl.col("aligned")), t.filter(~pl.col("aligned"))
    if min(len(al), len(an)) < 30:
        continue
    print(f"{lab:8s}: aligned n={len(al)} net={al['net_bps'].mean():+.2f} dir={dirf(al):.3f} | anti n={len(an)} net={an['net_bps'].mean():+.2f} dir={dirf(an):.3f} | lift={al['net_bps'].mean()-an['net_bps'].mean():+.2f}")

# registered headline comparison: aligned vs anti among complex>0
al, an = has.filter(pl.col("aligned")), has.filter(~pl.col("aligned"))
print(f"\nregistered headline (complex>0): aligned n={len(al)} net={al['net_bps'].mean():+.2f} dir={dirf(al):.3f} vs anti n={len(an)} net={an['net_bps'].mean():+.2f} dir={dirf(an):.3f} -> lift {al['net_bps'].mean()-an['net_bps'].mean():+.2f} bps / {dirf(al)-dirf(an):+.3f} dir")

# (i) name-year cells: mean intensity tercile vs dir (cells with >=50 events)
print("\n-- name-year cells (>=50 events), mean |F|/ADV vs dir --")
cells = ev.group_by("symbol", "yr").agg(n=pl.len(), mIF=pl.col("F_adv").abs().mean(),
                                        dir=(pl.col("net_bps") > 0).mean(), net=pl.col("net_bps").mean()).filter(pl.col("n") >= 50)
cells = cells.sort("mIF", descending=True)
k = len(cells) // 3
top, bot = cells.head(k), cells.tail(k)
print(f"cells={len(cells)}; TOP tercile mean dir={top['dir'].mean():.3f} net={top['net'].mean():+.2f} | BOTTOM dir={bot['dir'].mean():.3f} net={bot['net'].mean():+.2f}")
print("top-8 cells by intensity:")
print(cells.head(8))

# (iii) GOOGL clause
print("\n-- GOOGL clause: complex intensity (mean |F|/ADV, x1e4) and dir by year --")
gc = ev.filter(pl.col("symbol").is_in(["GOOGL", "NVDA", "MU", "TSLA"])).group_by("symbol", "yr").agg(
    n=pl.len(), iF=(pl.col("F_adv").abs().mean() * 1e4).round(2), dir=(pl.col("net_bps") > 0).mean().round(3),
    net=pl.col("net_bps").mean().round(2)).sort("symbol", "yr")
print(gc.filter(pl.col("yr") >= 2023))
