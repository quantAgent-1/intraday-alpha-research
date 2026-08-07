"""BJZ quote-free retail fade — prong-0 (Phase 1) and OOS (Phase 3) runner.

Spec frozen in `research/experiments/BJZ-prong0/PREDECLARATION.md` (ledgered before any
computation). One rule, two panels:

    uv run python scripts/bjz_prong0.py discovery   # Phase 1: method validation, 10 names
    uv run python scripts/bjz_prong0.py oos         # Phase 3: decisive test, 16 virgin names

Signal: session t-1 RTH off-exchange ('D') prints, ALL sizes, signed by the
Boehmer-Jones-Zhang sub-penny rule (frac = (px*100) mod 1; BUY if 0.6<frac<1, SELL if
0<frac<=0.4; midpoint band unclassified). RIMB = signed volume imbalance over classified
prints, >=30 required. Fire when |RIMB| >= that name's own Q3(|RIMB|). Position
-sign(RIMB) entered at the day-t opening cross, exit 15:40-15:45.

Prices come ONLY from bars1m via `m28_panel.daily_frame` (the one-lake rule): entry =
09:30 bar open, exit = last close <= 15:45. Cost = flat 3.0 bps half-spread + 0.206 SEC
fee per fire (Amendment-1 convention); 0.85 / 6.0 bps sensitivities reported non-gating.

Primary statistic (from birth): mean of the DAILY equal-weight portfolio of fires, net,
session-bootstrap 95% CI (seed 7, 2000 reps).

The oos mode REFUSES to run until (a) the discovery run has produced METHOD-VALIDATED and
(b) the family registration row exists (checked via a marker file written by the
registration step) — Phase 3 is the single sanctioned look of `retail_fade_daily_v1`.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from m28_panel import LAST_SESSION, _sec_expr, daily_frame  # noqa: E402

TRADES = REPO / "data" / "raw" / "sip" / "trades"
EXP = REPO / "research" / "experiments" / "BJZ-prong0"

DISCOVERY = ["NVDA", "TSLA", "AMD", "MU", "GOOGL", "KLAC", "MRVL", "LRCX", "TXN", "AMAT"]
OOS = ["VRTX", "BKNG", "ISRG", "AMGN", "HON", "INTU", "TMUS", "GILD",
       "MDLZ", "COST", "PEP", "ADBE", "CMCSA", "SBUX", "CSCO", "QCOM"]

RTH_OPEN_SEC = 9 * 3600 + 30 * 60
RTH_CLOSE_SEC = 16 * 3600
CAP_DATE = "2026-06-01"                 # sealed holdout never read
MIN_CLASSIFIED = 30
COST_PRIMARY = 3.0 + 0.206              # flat half-spread + SEC fee, bps per fire
COST_OPT = 0.85 + 0.206
COST_DOUBLE = 6.0 + 0.206
SEED, REPS = 7, 2000
POINT_FLOOR_OOS = 6.0                   # NOT-CONFIRMED vs PARK-UNDERPOWERED boundary


def bjz_sign(px: np.ndarray) -> np.ndarray:
    """Sub-penny fraction -> +1 retail buy / -1 retail sell / 0 unclassified."""
    frac = np.round((px * 100.0) % 1.0, 4)
    out = np.zeros(px.shape[0], dtype=np.int64)
    out[(frac > 0.6) & (frac < 1.0 - 1e-4)] = 1
    out[(frac > 1e-4) & (frac <= 0.4)] = -1
    return out


def day_imbalance(sym: str, date: str) -> dict | None:
    """RIMB for one session's off-exchange prints, or None if unusable."""
    p = TRADES / sym / f"{date}.parquet"
    if not p.exists():
        return None
    d = pl.read_parquet(p, columns=["ts", "price", "size", "exchange"])
    d = d.filter((pl.col("exchange") == "D") & (pl.col("price") > 0))
    if d.height == 0:
        return None
    d = d.with_columns(_sec_expr().alias("_s")).filter(
        (pl.col("_s") >= RTH_OPEN_SEC) & (pl.col("_s") < RTH_CLOSE_SEC))
    if d.height == 0:
        return None
    px = d["price"].to_numpy()
    sz = d["size"].to_numpy()
    sign = bjz_sign(px)
    m = sign != 0
    n_cls = int(m.sum())
    if n_cls < MIN_CLASSIFIED:
        return {"n_classified": n_cls, "rimb": None, "rimb_odd": None}
    buy = float(sz[sign > 0].sum())
    sell = float(sz[sign < 0].sum())
    if buy + sell <= 0:
        return {"n_classified": n_cls, "rimb": None, "rimb_odd": None}
    odd = m & (sz < 100)
    ob = float(sz[odd & (sign > 0)].sum())
    os_ = float(sz[odd & (sign < 0)].sum())
    return {
        "n_classified": n_cls,
        "rimb": (buy - sell) / (buy + sell),
        "rimb_odd": (ob - os_) / (ob + os_) if (ob + os_) > 0 else None,
    }


def process_symbol(sym: str) -> tuple[list[dict], dict]:
    df = daily_frame(sym)
    funnel = {"no_bars": 0, "no_trades_tm1": 0, "few_classified": 0, "no_exit": 0,
              "bad_open": 0}
    if df is None:
        return [], {"sym": sym, "kept": 0, **funnel}
    d = df.to_dicts()
    recs: list[dict] = []
    for i in range(1, len(d)):
        r = d[i]
        date_t, date_tm1 = r["date"], d[i - 1]["date"]
        if date_t >= CAP_DATE or date_t > LAST_SESSION:
            continue
        imb = day_imbalance(sym, date_tm1)
        if imb is None:
            funnel["no_trades_tm1"] += 1
            continue
        if imb["rimb"] is None:
            funnel["few_classified"] += 1
            continue
        if r["exit_px"] is None or not np.isfinite(r["exit_px"]):
            funnel["no_exit"] += 1
            continue
        o = r["o"]
        if o is None or not np.isfinite(o) or o <= 0:
            funnel["bad_open"] += 1
            continue
        recs.append({
            "sym": sym, "date": date_t, "rimb": imb["rimb"],
            "rimb_odd": imb["rimb_odd"], "n_classified": imb["n_classified"],
            "ret": (r["exit_px"] / o - 1.0) * 1e4,
        })
    return recs, {"sym": sym, "kept": len(recs), **funnel}


def boot_mean(v: np.ndarray, seed: int = SEED, reps: int = REPS):
    rng = np.random.default_rng(seed)
    n = v.size
    b = np.array([v[rng.integers(0, n, n)].mean() for _ in range(reps)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def clustered_event_ci(dates: np.ndarray, v: np.ndarray, seed: int = SEED, reps: int = REPS):
    uniq = np.unique(dates)
    idx = [np.nonzero(dates == u)[0] for u in uniq]
    rng = np.random.default_rng(seed)
    b = np.array([
        v[np.concatenate([idx[j] for j in rng.integers(0, len(uniq), len(uniq))])].mean()
        for _ in range(reps)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def run_panel(names: list[str], tag: str, imb_key: str = "rimb") -> dict:
    rows, funnels = [], []
    with ProcessPoolExecutor(max_workers=min(len(names), 12)) as ex:
        for recs, fn in ex.map(process_symbol, names):
            rows.extend(recs)
            funnels.append(fn)
    ev = pl.DataFrame(rows)
    print(f"[{tag}] name-days kept: {ev.height:,}  names: {ev['sym'].n_unique()}")

    # fires: per-name top-quartile of |imbalance|
    fired = []
    for key, g in ev.partition_by("sym", as_dict=True, maintain_order=True).items():
        sym = key[0] if isinstance(key, tuple) else key
        a = np.abs(np.array([x if x is not None else np.nan for x in g[imb_key].to_list()]))
        ok = np.isfinite(a)
        if ok.sum() < 20:
            continue
        q3 = float(np.percentile(a[ok], 75))
        if q3 == 0.0:
            continue
        m = ok & (a >= q3)
        imb = np.array([x if x is not None else np.nan for x in g[imb_key].to_list()])[m]
        ret = g["ret"].to_numpy()[m]
        for dd, ii, rr in zip(g["date"].to_numpy()[m], imb, ret, strict=True):
            fired.append({"date": str(dd), "sym": sym, "fade": float(-np.sign(ii) * rr)})
    fe = pl.DataFrame(fired)
    daily = fe.group_by("date").agg(pl.col("fade").mean().alias("mid"),
                                    pl.len().alias("k")).sort("date")
    mid = daily["mid"].to_numpy()
    out = {"tag": tag, "imb_key": imb_key, "event_n": fe.height, "T": daily.height,
           "fires_per_day": float(daily["k"].mean()),
           "funnels": funnels}
    lo, hi = boot_mean(mid)
    out["daily_mid"] = {"mean": float(mid.mean()), "ci_lo": lo, "ci_hi": hi}
    for lbl, c in (("primary", COST_PRIMARY), ("optimistic", COST_OPT), ("double", COST_DOUBLE)):
        net = mid - c
        nlo, nhi = boot_mean(net)
        out[f"daily_net_{lbl}"] = {"cost": c, "mean": float(net.mean()),
                                   "ci_lo": nlo, "ci_hi": nhi}
    ed, evv = fe["date"].to_numpy(), fe["fade"].to_numpy()
    elo, ehi = clustered_event_ci(ed, evv)
    out["event_mid"] = {"mean": float(evv.mean()), "ci_lo": elo, "ci_hi": ehi}
    per = fe.group_by("sym").agg(pl.col("fade").mean().alias("m"), pl.len().alias("n"))
    out["per_name"] = {r["sym"]: {"mean": round(r["m"], 2), "n": r["n"]}
                       for r in per.iter_rows(named=True)}
    yr = fe.with_columns(pl.col("date").str.slice(0, 4).alias("y")).group_by("y").agg(
        pl.col("fade").mean().alias("m"), pl.len().alias("n")).sort("y")
    out["by_year"] = {r["y"]: {"mean": round(r["m"], 2), "n": r["n"]}
                      for r in yr.iter_rows(named=True)}
    return out


def fmt(out: dict) -> list[str]:
    L = [f"## {out['tag']} ({out['imb_key']})",
         f"- name-days {out['event_n']:,} fires; T={out['T']} sessions; "
         f"{out['fires_per_day']:.2f} fires/day",
         f"- daily MID  {out['daily_mid']['mean']:+7.2f}  "
         f"[{out['daily_mid']['ci_lo']:+7.2f}, {out['daily_mid']['ci_hi']:+7.2f}]"]
    for lbl in ("primary", "optimistic", "double"):
        d = out[f"daily_net_{lbl}"]
        L.append(f"- daily NET ({lbl}, cost {d['cost']:.2f})  {d['mean']:+7.2f}  "
                 f"[{d['ci_lo']:+7.2f}, {d['ci_hi']:+7.2f}]")
    e = out["event_mid"]
    L.append(f"- event-level mid {e['mean']:+7.2f} [{e['ci_lo']:+7.2f}, {e['ci_hi']:+7.2f}]")
    L.append("- per-name means: " + ", ".join(
        f"{k} {v['mean']:+.1f}" for k, v in sorted(out["per_name"].items())))
    L.append("- by year: " + ", ".join(
        f"{k} {v['mean']:+.1f} (n={v['n']})" for k, v in out["by_year"].items()))
    return L


def cmd_discovery() -> int:
    EXP.mkdir(parents=True, exist_ok=True)
    main_out = run_panel(DISCOVERY, "discovery-10", "rimb")
    odd_out = run_panel(DISCOVERY, "discovery-10 odd-lot variant", "rimb_odd")

    # support: corr(BJZ RIMB, quote-signed OLI) on matched name-days
    r2a = pl.read_parquet(REPO / "research" / "experiments" / "R2A-prong0" / "panel.parquet")
    rows = []
    for sym in DISCOVERY:
        recs, _ = process_symbol(sym)
        rows.extend(recs)
    bj = pl.DataFrame(rows).select(["sym", "date", "rimb"])
    j = r2a.select(["sym", "date", "oli"]).with_columns(pl.col("date").cast(pl.Utf8)).join(
        bj, on=["sym", "date"], how="inner").drop_nulls()
    corr = float(np.corrcoef(j["oli"].to_numpy(), j["rimb"].to_numpy())[0, 1])

    g1 = main_out["daily_net_primary"]["ci_lo"] > 0
    g2 = main_out["daily_mid"]["mean"] >= 2 * COST_PRIMARY
    verdict = "METHOD-VALIDATED" if (g1 and g2) else "METHOD-FAILED"

    L = ["# BJZ prong-0 — Phase 1 (discovery 10) — METHOD VALIDATION ONLY", "",
         "Gates pre-declared in PREDECLARATION.md before any computation. A pass here can",
         "NEVER confirm the effect (design-only panel, third expression of one phenomenon);",
         "it only licenses the Phase-3 virgin-name test.", ""]
    L += fmt(main_out) + [""]
    L += [f"- corr(BJZ RIMB, quote-signed odd-lot OLI) on {j.height:,} matched name-days: "
          f"**{corr:+.4f}** (support, non-gating)", ""]
    L += fmt(odd_out) + ["", "## GATES",
                         f"- G1 daily net (primary cost) CI-lo > 0: "
                         f"{main_out['daily_net_primary']['ci_lo']:+.2f} -> "
                         f"{'PASS' if g1 else 'FAIL'}",
                         f"- G2 gross >= 2x cost ({2 * COST_PRIMARY:.2f}): "
                         f"{main_out['daily_mid']['mean']:+.2f} -> {'PASS' if g2 else 'FAIL'}",
                         "", f"## VERDICT: {verdict}"]
    (EXP / "phase1_result.json").write_text(json.dumps(
        {"main": main_out, "oddlot": odd_out, "corr_vs_quote_oli": corr,
         "g1": bool(g1), "g2": bool(g2), "verdict": verdict}, indent=1,
        allow_nan=False), encoding="utf-8")
    (EXP / "phase1.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


def cmd_oos() -> int:
    p1 = EXP / "phase1_result.json"
    if not p1.exists() or json.loads(p1.read_text(encoding="utf-8"))["verdict"] != "METHOD-VALIDATED":
        print("REFUSING: Phase 1 has not produced METHOD-VALIDATED.")
        return 2
    marker = EXP / "registration_marker.json"
    if not marker.exists():
        print("REFUSING: retail_fade_daily_v1 is not registered (marker absent). "
              "Phase 3 is the family's single sanctioned look and cannot run pre-registration.")
        return 3
    missing = [s for s in OOS if not (TRADES / s).exists()
               or len(list((TRADES / s).glob("*.parquet"))) < 400]
    if missing:
        print(f"REFUSING: OOS trades incomplete for {missing} (need >=400 session files each).")
        return 4
    out = run_panel(OOS, "OOS-16 (virgin names)", "rimb")
    d = out["daily_net_primary"]
    if d["ci_lo"] > 0 and out["daily_mid"]["mean"] >= 2 * COST_PRIMARY:
        verdict = "CONFIRMED"
    elif d["ci_hi"] < 0:
        verdict = "REFUTED"
    elif d["mean"] < POINT_FLOOR_OOS:
        verdict = "NOT-CONFIRMED"
    else:
        verdict = "PARK-UNDERPOWERED"
    L = ["# BJZ Phase 3 — decisive OOS test (16 virgin names)", ""]
    L += fmt(out) + ["", f"## VERDICT: {verdict}"]
    (EXP / "phase3_result.json").write_text(json.dumps(
        {"main": out, "verdict": verdict}, indent=1, allow_nan=False), encoding="utf-8")
    (EXP / "phase3.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="BJZ quote-free retail fade runner.")
    ap.add_argument("stage", choices=["discovery", "oos"])
    a = ap.parse_args(argv)
    return cmd_discovery() if a.stage == "discovery" else cmd_oos()


if __name__ == "__main__":
    sys.exit(main())
