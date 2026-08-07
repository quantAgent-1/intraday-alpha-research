"""ISO institutional-sweep imbalance prong-0. Spec: ISO-prong0/PREDECLARATION.md (ledgered).

Reuses the FROZEN r2a_prong0 machinery verbatim (bars1d loader, BboCache, sign_prints,
exit_mid) — only the print predicate differs: conditions contain 'F' (ISO), any venue,
all sizes. Hypothesis = CONTINUATION (+sign(IIMB)), fixed pre-data.

    uv run python scripts/iso_prong0.py
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import r2a_prong0 as R  # noqa: E402

EXP = REPO / "research" / "experiments" / "ISO-prong0"
HS = {"NVDA": 0.70, "TSLA": 0.78, "AMD": 0.62, "MU": 0.82, "GOOGL": 0.50,
      "KLAC": 3.60, "MRVL": 0.88, "LRCX": 1.72, "TXN": 0.97, "AMAT": 1.41}
SEC_FEE = 0.206
SEED, REPS = 7, 2000
KILL_CI_HI = 2.0
BLOCK_NOTIONAL = 100_000.0


def load_prints(sym: str, date: str, kind: str):
    """(ts, px, sz) of RTH prints for one session: kind='iso' (cond F) or 'block'."""
    p = R.TRADES_DIR / sym / f"{date}.parquet"
    if not p.exists():
        return None
    d = pl.read_parquet(p, columns=["ts", "price", "size", "exchange", "conditions"])
    d = d.filter(pl.col("price") > 0)
    if kind == "iso":
        d = d.filter(pl.col("conditions").str.split("|").list.contains("F"))
    else:
        d = d.filter((pl.col("price") * pl.col("size")) >= BLOCK_NOTIONAL)
    d = d.with_columns(R._sec_expr().alias("_s")).filter(
        (pl.col("_s") >= R.RTH_OPEN_SEC) & (pl.col("_s") < R.RTH_CLOSE_SEC)).sort("ts")
    if d.height == 0:
        return (np.zeros(0, dtype=np.int64), np.zeros(0), np.zeros(0))
    return (d["ts"].to_numpy(), d["price"].to_numpy().astype(np.float64),
            d["size"].to_numpy().astype(np.float64))


def imb_of(tr, q_ts, q_mid, min_signed: int):
    t_ts, t_px, t_sz = tr
    if t_ts.shape[0] == 0:
        return None, 0
    sign = R.sign_prints(t_ts, t_px, q_ts, q_mid)
    n = int((sign != 0).sum())
    if n < min_signed:
        return None, n
    buy = float(t_sz[sign > 0].sum())
    sell = float(t_sz[sign < 0].sum())
    return ((buy - sell) / (buy + sell) if (buy + sell) > 0 else None), n


def process_symbol(sym: str) -> list[dict]:
    bars = R.load_bars1d(sym)
    if bars is None:
        return []
    dates, opens, _closes = bars
    bbo = R.BboCache(sym)
    recs: list[dict] = []
    for i in range(2, len(dates)):
        date_t, date_tm1 = dates[i], dates[i - 1]
        if date_t >= R.CAP_DATE:
            continue
        iso = load_prints(sym, date_tm1, "iso")
        if iso is None or iso[0].shape[0] == 0:
            continue
        bday_tm1 = bbo.get_day(date_tm1)
        bday_t = bbo.get_day(date_t)
        if bday_tm1 is None or bday_t is None:
            continue
        _q_ts_t, q_sec_t, q_mid_t = bday_t
        if int(q_sec_t[-1]) < R.EARLY_CLOSE_SEC:
            continue
        open_t = opens[i]
        if not (np.isfinite(open_t) and open_t > 0):
            continue
        q_ts_tm1, _s, q_mid_tm1 = bday_tm1
        iimb, n_iso = imb_of(iso, q_ts_tm1, q_mid_tm1, R.MIN_SIGNED)
        if iimb is None:
            continue
        ex = R.exit_mid(q_sec_t, q_mid_t, R.EXIT_MAIN_HI, R.EXIT_MAIN_LO)
        if ex is None:
            continue
        blk = load_prints(sym, date_tm1, "block")
        bimb, _nb = imb_of(blk, q_ts_tm1, q_mid_tm1, 10) if blk is not None else (None, 0)
        recs.append({"sym": sym, "date": date_t, "iimb": iimb, "bimb": bimb,
                     "n_iso": n_iso, "ret": (ex / open_t - 1.0) * 1e4})
    return recs


def boot(v: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    n = v.size
    b = np.array([v[rng.integers(0, n, n)].mean() for _ in range(REPS)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def clustered(dates: np.ndarray, v: np.ndarray) -> tuple[float, float]:
    uniq = np.unique(dates)
    idx = [np.nonzero(dates == u)[0] for u in uniq]
    rng = np.random.default_rng(SEED)
    b = np.array([
        v[np.concatenate([idx[j] for j in rng.integers(0, len(uniq), len(uniq))])].mean()
        for _ in range(REPS)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def portfolio(ev: pl.DataFrame, key: str, direction: float) -> dict:
    fired = []
    for k, g in ev.partition_by("sym", as_dict=True, maintain_order=True).items():
        sym = k[0] if isinstance(k, tuple) else k
        vals = np.array([x if x is not None else np.nan for x in g[key].to_list()])
        ok = np.isfinite(vals)
        if ok.sum() < 20:
            continue
        q3 = float(np.percentile(np.abs(vals[ok]), 75))
        if q3 == 0.0:
            continue
        m = ok & (np.abs(vals) >= q3)
        c = HS[sym] + SEC_FEE
        for d, x, r in zip(g["date"].to_numpy()[m], vals[m], g["ret"].to_numpy()[m],
                           strict=True):
            fired.append({"date": str(d), "sym": sym,
                          "pnl": float(direction * np.sign(x) * r), "cost": c})
    fe = pl.DataFrame(fired)
    if fe.height == 0:
        return {"event_n": 0}
    daily = fe.group_by("date").agg(
        pl.col("pnl").mean().alias("mid"),
        (pl.col("pnl") - pl.col("cost")).mean().alias("net"),
        pl.col("cost").mean().alias("cost"), pl.len().alias("k")).sort("date")
    mid, net = daily["mid"].to_numpy(), daily["net"].to_numpy()
    mlo, mhi = boot(mid)
    nlo, nhi = boot(net)
    elo, ehi = clustered(fe["date"].to_numpy(), fe["pnl"].to_numpy())
    per = fe.group_by("sym").agg(pl.col("pnl").mean().alias("m"), pl.len().alias("n"))
    yr = fe.with_columns(pl.col("date").str.slice(0, 4).alias("y")).group_by("y").agg(
        pl.col("pnl").mean().alias("m"), pl.len().alias("n")).sort("y")
    return {"event_n": fe.height, "T": daily.height,
            "fires_per_day": float(daily["k"].mean()),
            "mean_cost": float(daily["cost"].to_numpy().mean()),
            "daily_mid": {"mean": float(mid.mean()), "ci_lo": mlo, "ci_hi": mhi},
            "daily_net": {"mean": float(net.mean()), "ci_lo": nlo, "ci_hi": nhi},
            "event": {"mean": float(fe["pnl"].to_numpy().mean()), "ci_lo": elo, "ci_hi": ehi},
            "per_name": {r["sym"]: {"mean": round(r["m"], 2), "n": r["n"]}
                         for r in per.iter_rows(named=True)},
            "by_year": {r["y"]: {"mean": round(r["m"], 2), "n": r["n"]}
                        for r in yr.iter_rows(named=True)}}


def show(tag: str, o: dict) -> None:
    if o.get("event_n", 0) == 0:
        print(f"{tag}: no fires")
        return
    print(f"{tag}: fires {o['event_n']:,}  T={o['T']}  {o['fires_per_day']:.2f}/day  "
          f"cost {o['mean_cost']:.2f}")
    print(f"  daily MID {o['daily_mid']['mean']:+7.2f} "
          f"[{o['daily_mid']['ci_lo']:+7.2f}, {o['daily_mid']['ci_hi']:+7.2f}]   "
          f"NET {o['daily_net']['mean']:+7.2f} "
          f"[{o['daily_net']['ci_lo']:+7.2f}, {o['daily_net']['ci_hi']:+7.2f}]")
    print(f"  event {o['event']['mean']:+7.2f} [{o['event']['ci_lo']:+7.2f}, "
          f"{o['event']['ci_hi']:+7.2f}]")
    print("  per-name: " + ", ".join(f"{k} {v['mean']:+.1f}"
                                      for k, v in sorted(o["per_name"].items())))
    print("  years: " + ", ".join(f"{k} {v['mean']:+.1f} (n={v['n']})"
                                   for k, v in o["by_year"].items()))


def main() -> int:
    EXP.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=10) as ex:
        for recs in ex.map(process_symbol, R.PANEL):
            rows.extend(recs)
    ev = pl.DataFrame(rows)
    print(f"panel: {ev.height:,} name-days, {ev['sym'].n_unique()} names, "
          f"{ev['date'].n_unique()} sessions\n")

    main_out = portfolio(ev, "iimb", +1.0)          # the hypothesis: continuation
    show("ISO continuation (PRIMARY)", main_out)
    mirror = portfolio(ev, "iimb", -1.0)            # diagnostic mirror
    print()
    show("ISO fade (mirror, diagnostic)", mirror)
    block = portfolio(ev, "bimb", +1.0)             # diagnostic block variant
    print()
    show("block-print continuation (diagnostic)", block)

    r2a = pl.read_parquet(REPO / "research" / "experiments" / "R2A-prong0" / "panel.parquet")
    j = (ev.drop_nulls("iimb")
           .join(r2a.select(["sym", "date", "oli"]), on=["sym", "date"], how="inner"))
    corr = float(np.corrcoef(j["iimb"].to_numpy(), j["oli"].to_numpy())[0, 1])
    print(f"\ncorr(IIMB, retail OLI) on {j.height:,} matched name-days: {corr:+.4f}")

    m = main_out
    if m["daily_net"]["ci_lo"] > 0 and m["daily_mid"]["mean"] >= 2 * m["mean_cost"]:
        verdict = "PASS-CANDIDATE"
    elif m["daily_mid"]["ci_hi"] < KILL_CI_HI:
        verdict = "KILL"
    else:
        verdict = "PARK-UNDERPOWERED"
    print(f"\nVERDICT: {verdict}")
    (EXP / "result.json").write_text(json.dumps(
        {"primary": main_out, "mirror": mirror, "block": block,
         "corr_iimb_oli": corr, "verdict": verdict}, indent=1, allow_nan=False),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
