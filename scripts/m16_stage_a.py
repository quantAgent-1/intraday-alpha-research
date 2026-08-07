"""M16 Stage A — GP partial-adjustment flow book (registered M16-stageA-flow-book-v1).

Frozen spec (M3_REGISTRATION.md): hourly clocks 10:00..15:00 + 15:30 + 15:50; ridge on
THREE slow features (z(F/ADV), MONTH_END, OPEX) walk-forward by year; theta=0.25/hr;
no-trade band (proportional approx: skip |delta| < 0.75 x train mean|pos|); whole shares
at $10k; max 30 orders/day; PRIMARY flat at 15:50; SECONDARY MOC-exit lens (ride the
15:50 residual to the official close, single print, zero exit spread — champion-style).
Costs two-regime per DR-X3: mid-day 0.65 x half-spread + 0.3 bp; 15:30/15:50 passes
1.46 bp flat; sensitivity at E/Q=1.0. Kill: pooled net/day <= 0 at n>=250 name-days;
attribution; >30 orders/day.

Implementation notes for the report: label = ret-to-close as registered, so the PRIMARY
run forfeits the 15:50->close leg by design (the MOC lens restores it); positions are
vol-scaled (pos = c*yhat/sigma, c calibrated on TRAIN to a 15 bps/hr book sd, cap
0.5/name); z-scores/sigma/c/band all from train-fold stats only.
"""
import numpy as np
import polars as pl

CLOCKS = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "15:30", "15:50"]
THETA, BAND_FRAC = 0.25, 0.75
BOOK, TARGET_SD, POS_CAP, RIDGE_L = 10_000.0, 15.0, 0.5, 1.0
LATE, LATE_COST, EQ_MID, RESID = {"15:30", "15:50"}, 1.46, 0.65, 0.3
SYMS = ["NVDA", "TSLA", "AMD", "MU", "GOOGL"]

P = pl.read_parquet("research/experiments/M16-flow-book/hourly_panel.parquet")
P = P.with_columns(pl.col("session").cast(pl.Utf8))
advs = []
for sym in SYMS:
    b = pl.read_parquet(f"data/raw/sip/bars1d/{sym}.parquet").sort("ts")
    b = b.with_columns(
        pl.col("ts").cast(pl.Datetime("ns")).dt.date().cast(pl.Utf8).alias("session"),
        (pl.coalesce(pl.col("vwap"), pl.col("close")) * pl.col("volume")).alias("dollar"),
    ).with_columns(pl.col("dollar").rolling_mean(20).shift(1).alias("adv20")
    ).select("session", "adv20").with_columns(pl.lit(sym).alias("symbol"))
    advs.append(b)
P = P.join(pl.concat(advs), on=["symbol", "session"], how="left")
P = P.filter(pl.col("adv20").is_not_null() & pl.col("mid").is_not_null()
             & pl.col("session_close").is_not_null())
P = P.with_columns(
    (pl.col("F_usd") / pl.col("adv20")).alias("f_adv"),
    pl.col("month_end").cast(pl.Float64), pl.col("opex").cast(pl.Float64),
    pl.col("session").str.slice(0, 4).cast(pl.Int32).alias("yr"),
)

def fit_ridge(X, y):
    Xi = np.column_stack([np.ones(len(X)), X])
    return np.linalg.solve(Xi.T @ Xi + RIDGE_L * np.eye(Xi.shape[1]), Xi.T @ y)

def run(zero_features: bool = False):
    rows_out = []
    for ty in [y for y in sorted(P["yr"].unique().to_list()) if y >= 2022]:
        tr, te = P.filter(pl.col("yr") < ty), P.filter(pl.col("yr") == ty)
        if tr["session"].n_unique() < 400 or te.height == 0:
            continue
        mu, sd = tr["f_adv"].mean(), tr["f_adv"].std()
        # First fold trains pre-LETF-era (f_adv identically 0): z-score degenerates.
        # Neutralize (z=raw, beta_flow fits ~0) -> that fold runs calendar-only, PIT-honest.
        if mu is None or not np.isfinite(mu):
            mu = 0.0
        if sd is None or not np.isfinite(sd) or sd == 0.0:
            sd = 1.0
        def feats(df):
            X = np.column_stack([((df["f_adv"] - mu) / sd).to_numpy(),
                                 df["month_end"].to_numpy(), df["opex"].to_numpy()])
            return np.zeros_like(X) if zero_features else X
        beta = fit_ridge(feats(tr), tr["ret_next_close_bps"].to_numpy())
        trs = tr.sort(["symbol", "session", "clock"]).with_columns(
            ((pl.col("mid") / pl.col("mid").shift(1).over(["symbol", "session"]) - 1) * 1e4).alias("h"))
        sig = {r["symbol"]: max(float(r["s"]), 5.0) for r in
               trs.drop_nulls("h").group_by("symbol").agg(pl.col("h").std().alias("s")).iter_rows(named=True)}
        yh_tr = np.column_stack([np.ones(tr.height), feats(tr)]) @ beta
        raw = yh_tr / np.array([sig[s] for s in tr["symbol"].to_list()])
        per_sd = np.std(raw) * np.mean(list(sig.values()))
        c = TARGET_SD / (per_sd * np.sqrt(5) + 1e-12)
        band = BAND_FRAC * float(np.mean(np.abs(np.clip(c * raw, -POS_CAP, POS_CAP)))) if not zero_features else 0.0
        te = te.with_columns(pl.Series("yhat", np.column_stack([np.ones(te.height), feats(te)]) @ beta))
        for (sess,), day in te.group_by(["session"], maintain_order=True):
            held: dict[str, float] = {}
            shares: dict[str, float] = {}
            last_mid: dict[str, float] = {}
            close_px: dict[str, float] = {}
            g = c_lo = c_hi = 0.0
            n_ord = 0
            moc_extra = 0.0
            for ck in CLOCKS:
                rows = day.filter(pl.col("clock") == ck)
                for r in rows.iter_rows(named=True):
                    s, mid = r["symbol"], r["mid"]
                    if mid is None or r["half_spread_bps"] is None:
                        continue  # half-day / missing-quote clock: no mark, no trade
                    close_px[s] = r["session_close"]
                    if s in last_mid and shares.get(s, 0.0) != 0.0:
                        g += shares[s] * (mid - last_mid[s]) / BOOK * 1e4
                    last_mid[s] = mid
                    held.setdefault(s, 0.0)
                    shares.setdefault(s, 0.0)
                    if ck == "15:50":
                        if shares[s] != 0.0:
                            # MOC lens: ride to official close, single print, no exit cost
                            moc_extra += shares[s] * (close_px[s] - mid) / BOOK * 1e4
                            # PRIMARY: flatten at mid, pay late-window cost
                            tc = abs(shares[s]) * mid / BOOK
                            c_lo += tc * LATE_COST
                            c_hi += tc * LATE_COST
                            n_ord += 1
                        shares[s] = 0.0
                        held[s] = 0.0
                        continue
                    tgt = float(np.clip(c * r["yhat"] / sig.get(s, 20.0), -POS_CAP, POS_CAP))
                    tgt = (1 - THETA) * held[s] + THETA * tgt
                    if abs(tgt - held[s]) < band:
                        continue
                    new_sh = float(np.floor(abs(tgt) * BOOK / mid) * np.sign(tgt))
                    d_sh = new_sh - shares[s]
                    if d_sh != 0.0:
                        rate_lo = LATE_COST if ck in LATE else (EQ_MID * r["half_spread_bps"] + RESID)
                        rate_hi = LATE_COST if ck in LATE else (1.0 * r["half_spread_bps"] + RESID)
                        c_lo += abs(d_sh) * mid / BOOK * rate_lo
                        c_hi += abs(d_sh) * mid / BOOK * rate_hi
                        n_ord += 1
                    shares[s] = new_sh
                    held[s] = tgt
            rows_out.append({"session": sess, "gross": g, "cost_lo": c_lo, "cost_hi": c_hi,
                             "moc_extra": moc_extra, "orders": n_ord})
    return pl.DataFrame(rows_out)

res = run(False)
res = res.with_columns(
    (pl.col("gross") - pl.col("cost_lo")).alias("net_primary"),
    (pl.col("gross") - pl.col("cost_hi")).alias("net_primary_stress"),
    (pl.col("gross") + pl.col("moc_extra") - pl.col("cost_lo")).alias("net_moc"),
)
rng = np.random.default_rng(7)
def ci(x):
    bs = [np.mean(rng.choice(x, len(x), True)) for _ in range(1000)]
    return np.mean(x), *np.percentile(bs, [2.5, 97.5])
print(f"n_days={res.height}  orders/day mean {res['orders'].mean():.1f} max {res['orders'].max()}")
for col in ["gross", "net_primary", "net_primary_stress", "net_moc"]:
    m, lo, hi = ci(res[col].to_numpy())
    print(f"{col:20s} {m:+.2f} bps/day  CI[{lo:+.2f},{hi:+.2f}]  sd {res[col].std():.1f}")
print(res.with_columns(pl.col("session").str.slice(0, 4).alias("y")).group_by("y").agg(
    net=pl.col("net_primary").mean().round(2), moc=pl.col("net_moc").mean().round(2),
    n=pl.len()).sort("y"))
