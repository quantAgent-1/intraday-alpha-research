"""M29 short_ratio_battery_v1 — FINRA daily short-sale volume at the open-cross structure.

Spec: research/experiments/M29-short-ratio/REGISTRATION.md (ledgered pre-economics).

    uv run python scripts/m29_short_ratio.py fetch      # download FINRA daily files ($0)
    uv run python scripts/m29_short_ratio.py build      # parse -> signals joined to M28 panel
    uv run python scripts/m29_short_ratio.py verify     # black-box PIT test (blocks on fail)
    uv run python scripts/m29_short_ratio.py train      # FDR admission (writes admitted.json)
    uv run python scripts/m29_short_ratio.py validate   # the single test (refuses w/o admission)

Structure, universe, outcomes, costs and split are inherited from the verified M28 panel.
NaN -> null discipline from birth (the Amendment-2-NAN lesson).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date as _date
from datetime import timedelta
from pathlib import Path

import httpx
import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from m28_run import bh_fdr, boot_mean  # noqa: E402  (pure, audited by use)

from enginev51.research_screens.sizing_shadow import (  # noqa: E402
    min_trl,
    psr,
    sample_moments,
    sr_native,
)

EXP = REPO / "research" / "experiments" / "M29-short-ratio"
RAW_DIR = REPO / "data" / "external" / "finra_shvol"
SHV_PQ = REPO / "data" / "external" / "finra_shvol.parquet"
M28_PANEL = REPO / "research" / "experiments" / "M28-open-cross-battery" / "panel.parquet"
ADMITTED = EXP / "admitted.json"

FIRST_FILE = _date(2023, 11, 15)          # warm-up before 2024-01-02
LAST_FILE = _date(2026, 5, 29)            # < holdout
TRAIN = ("2024-01-02", "2025-05-30")
VALID = ("2025-06-02", "2026-05-29")
SIGNALS = ["sr_z21", "sr_d1", "sr_level", "exempt_z21"]
FDR_Q = 0.10
SEED, REPS = 7, 2000
MIN_NAMES = 20
DECILE, GROSS = 0.10, 1.0
HS_FLAT, SEC_FEE = 3.0, 0.206
ALPHA = 0.05
URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d}.txt"


# ------------------------------------------------------------------ fetch
def cmd_fetch() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    days = []
    d = FIRST_FILE
    while d <= LAST_FILE:
        if d.weekday() < 5:
            days.append(d.strftime("%Y%m%d"))
        d += timedelta(days=1)
    todo = [x for x in days if not (RAW_DIR / f"CNMSshvol{x}.txt").exists()]
    print(f"FINRA fetch: {len(todo)} of {len(days)} files missing")
    if not todo:
        return 0

    def get(ds: str) -> tuple[str, int]:
        try:
            r = httpx.get(URL.format(d=ds), timeout=30,
                          headers={"User-Agent": "research-agent/1.0"})
            if r.status_code == 200 and "|" in r.text[:100]:
                (RAW_DIR / f"CNMSshvol{ds}.txt").write_text(r.text, encoding="utf-8")
                return ds, r.status_code
            return ds, r.status_code
        except Exception:  # noqa: BLE001
            return ds, -1

    t0 = time.time()
    got = miss = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, (_ds, code) in enumerate(ex.map(get, todo), 1):
            if code == 200:
                got += 1
            else:
                miss += 1
            if i % 100 == 0:
                print(f"  {i}/{len(todo)}  ok={got} miss={miss}  {time.time() - t0:.0f}s")
    print(f"done: ok={got} miss={miss} (holidays 404 as expected) in {time.time() - t0:.0f}s")
    return 0


# ------------------------------------------------------------------ build
def cmd_build() -> int:
    uni = json.loads((REPO / "research" / "experiments" / "M28-open-cross-battery" /
                      "universe.json").read_text(encoding="utf-8"))["tradeable"]
    uset = set(uni)
    rows = []
    for f in sorted(RAW_DIR.glob("CNMSshvol*.txt")):
        for line in f.read_text(encoding="utf-8").strip().split("\n")[1:]:
            p = line.split("|")
            if len(p) < 5 or p[1] not in uset:
                continue
            try:
                sv, ev, tv = float(p[2]), float(p[3]), float(p[4])
            except ValueError:
                continue
            if tv <= 0:
                continue
            d = p[0]
            rows.append({"date": f"{d[:4]}-{d[4:6]}-{d[6:]}", "sym": p[1],
                         "sr": sv / tv, "ex_share": (ev / sv) if sv > 0 else 0.0})
    shv = pl.DataFrame(rows).unique(subset=["date", "sym"], keep="last").sort(["sym", "date"])
    shv.write_parquet(SHV_PQ)
    print(f"parsed {shv.height:,} (sym,date) short records, "
          f"{shv['sym'].n_unique()} names, {shv['date'].n_unique()} file-days")

    panel = pl.read_parquet(M28_PANEL).select(["sym", "date", "ret_bps"])
    out_rows = []
    for key, g in shv.partition_by("sym", as_dict=True, maintain_order=True).items():
        sym = key[0] if isinstance(key, tuple) else key
        dts = g["date"].to_list()
        sr = g["sr"].to_numpy()
        exs = g["ex_share"].to_numpy()
        idx = {d: i for i, d in enumerate(dts)}
        pdays = panel.filter(pl.col("sym") == sym)["date"].to_list()
        for t in pdays:
            # signal uses files <= session t-1: find the latest file STRICTLY before t
            j = idx.get(t)
            k = (j - 1) if j is not None else None
            if k is None:
                import bisect
                k = bisect.bisect_left(dts, t) - 1
            if k is None or k < 1:
                continue
            base = sr[max(0, k - 21):k]           # baseline strictly before t-1
            we = exs[max(0, k - 21):k]
            rec = {"sym": sym, "date": t,
                   "sr_level": float(sr[k]),
                   "sr_d1": float(sr[k] - sr[k - 1])}
            if base.size >= 15 and np.std(base) > 0:
                rec["sr_z21"] = float((sr[k] - base.mean()) / np.std(base, ddof=1))
            else:
                rec["sr_z21"] = None
            if we.size >= 15 and np.std(we) > 0:
                rec["exempt_z21"] = float((exs[k] - we.mean()) / np.std(we, ddof=1))
            else:
                rec["exempt_z21"] = None
            out_rows.append(rec)
    sig = pl.DataFrame(out_rows)
    m = panel.join(sig, on=["sym", "date"], how="inner")
    # NaN -> null on every signal (Amendment-2-NAN lesson, applied from birth)
    m = m.with_columns([
        pl.when(pl.col(c).is_not_null() & pl.col(c).is_nan()).then(None)
        .otherwise(pl.col(c)).alias(c) for c in SIGNALS
    ])
    m.write_parquet(EXP / "panel.parquet")
    cov = {c: int(m[c].drop_nulls().is_finite().sum()) for c in SIGNALS}
    print(f"M29 panel: {m.height:,} name-days, {m['sym'].n_unique()} names; coverage {cov}")
    return 0


# ------------------------------------------------------------------ verify (PIT)
def cmd_verify() -> int:
    """Black-box: perturb day-t file -> day-t signal UNCHANGED; perturb t-1 -> MOVES."""
    import shutil
    import tempfile
    panel = pl.read_parquet(EXP / "panel.parquet")
    ok: list[tuple[str, bool, str]] = []
    rng = np.random.default_rng(7)
    cand = panel.drop_nulls(["sr_z21"])
    picks = [cand.row(int(i), named=True) for i in
             rng.choice(cand.height, size=3, replace=False)]
    orig_raw = RAW_DIR
    for r in picks:
        sym, t = r["sym"], r["date"]
        shv = pl.read_parquet(SHV_PQ).filter(pl.col("sym") == sym).sort("date")
        dts = shv["date"].to_list()
        import bisect
        k = bisect.bisect_left(dts, t) - 1
        tm1, tday = dts[k], t
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "finra"
            tmp.mkdir()
            for f in orig_raw.glob("CNMSshvol*.txt"):
                shutil.copy(f, tmp / f.name)

            def rewrite(ds: str, factor: float, tmp=tmp, sym=sym) -> None:
                fp = tmp / f"CNMSshvol{ds.replace('-', '')}.txt"
                if not fp.exists():
                    return
                lines = fp.read_text(encoding="utf-8").split("\n")
                out = []
                for ln in lines:
                    p = ln.split("|")
                    if len(p) >= 5 and p[1] == sym:
                        p[2] = str(float(p[2]) * factor)
                        out.append("|".join(p))
                    else:
                        out.append(ln)
                fp.write_text("\n".join(out), encoding="utf-8")

            def signal_at(raw_dir: Path, sym=sym, tday=tday) -> float:
                RAW_local = raw_dir
                rows = []
                for f in sorted(RAW_local.glob("CNMSshvol*.txt")):
                    for line in f.read_text(encoding="utf-8").strip().split("\n")[1:]:
                        p = line.split("|")
                        if len(p) >= 5 and p[1] == sym:
                            try:
                                sv, tv = float(p[2]), float(p[4])
                            except ValueError:
                                continue
                            if tv > 0:
                                d = p[0]
                                rows.append((f"{d[:4]}-{d[4:6]}-{d[6:]}", sv / tv))
                rows.sort()
                ds = [x[0] for x in rows]
                sr = np.array([x[1] for x in rows])
                kk = bisect.bisect_left(ds, tday) - 1
                base = sr[max(0, kk - 21):kk]
                return float((sr[kk] - base.mean()) / np.std(base, ddof=1))

            base_val = signal_at(tmp)
            rewrite(tday, 3.0)                     # perturb the SAME-day file
            same_day = signal_at(tmp)
            ok.append((f"PIT {sym} {t}: day-t file perturbed -> signal UNCHANGED",
                       abs(same_day - base_val) < 1e-12,
                       f"{base_val:.4f} -> {same_day:.4f}"))
            rewrite(tm1, 3.0)                      # perturb the t-1 file
            moved = signal_at(tmp)
            ok.append((f"PIT {sym} {t}: day t-1 file perturbed -> signal MOVES",
                       abs(moved - base_val) > 1e-6, f"{base_val:.4f} -> {moved:.4f}"))
            ok.append((f"PIT {sym} {t}: panel value matches independent recompute",
                       abs(base_val - r["sr_z21"]) < 1e-9,
                       f"{base_val:.6f} vs {r['sr_z21']:.6f}"))
    for name, passed, detail in ok:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}  ({detail})")
    bad = sum(1 for _n, p, _d in ok if not p)
    print(f"verify: {len(ok) - bad}/{len(ok)} passed")
    return 0 if bad == 0 else 1


# ------------------------------------------------------------------ stats
def zscore(df: pl.DataFrame) -> pl.DataFrame:
    out = df
    for s in SIGNALS:
        lo = pl.col(s).quantile(0.01).over("date")
        hi = pl.col(s).quantile(0.99).over("date")
        w = pl.col(s).clip(lo, hi)
        mu, sd = w.mean().over("date"), w.std().over("date")
        out = out.with_columns(
            pl.when(sd > 0).then((w - mu) / sd).otherwise(None).alias(f"z_{s}"))
    return out


def session_ic(df: pl.DataFrame, sig: str):
    d = df.select(["date", f"z_{sig}", "ret_bps"]).drop_nulls().filter(
        pl.col(f"z_{sig}").is_finite() & pl.col("ret_bps").is_finite())
    ics = []
    for _k, g in d.partition_by("date", as_dict=True, maintain_order=True).items():
        if g.height < MIN_NAMES:
            continue
        x, y = g[f"z_{sig}"].to_numpy(), g["ret_bps"].to_numpy()
        rx = np.argsort(np.argsort(x)).astype(float)
        ry = np.argsort(np.argsort(y)).astype(float)
        if rx.std() == 0 or ry.std() == 0:
            continue
        ics.append(float(np.corrcoef(rx, ry)[0, 1]))
    return np.array(ics)


def cmd_train() -> int:
    df = zscore(pl.read_parquet(EXP / "panel.parquet"))
    tr = df.filter((pl.col("date") >= TRAIN[0]) & (pl.col("date") <= TRAIN[1]))
    print(f"TRAIN: {tr.height:,} name-days, {tr['date'].n_unique()} sessions, "
          f"{tr['sym'].n_unique()} names\n")
    res = []
    for s in SIGNALS:
        ics = session_ic(tr, s)
        if ics.size < 30:
            res.append({"signal": s, "ic": float("nan"), "p": 1.0,
                        "ci_lo": float("nan"), "ci_hi": float("nan"),
                        "n_sessions": int(ics.size)})
            continue
        lo, hi, p = boot_mean(ics)
        res.append({"signal": s, "ic": float(ics.mean()), "ci_lo": lo, "ci_hi": hi,
                    "p": p, "n_sessions": int(ics.size)})
    keep = bh_fdr([r["p"] for r in res], FDR_Q)
    for r, k in zip(res, keep, strict=True):
        r["admitted"] = bool(k)
        r["sign"] = float(np.sign(r["ic"])) if np.isfinite(r["ic"]) and r["ic"] else 0.0
    print(f"{'signal':12}{'IC':>9}{'95% CI':>20}{'p':>8}{'sess':>6}  admitted")
    for r in sorted(res, key=lambda z: z["p"]):
        print(f"{r['signal']:12}{r['ic']:+9.4f}[{r['ci_lo']:+8.4f},{r['ci_hi']:+8.4f}]"
              f"{r['p']:8.4f}{r['n_sessions']:6d}  {'YES' if r['admitted'] else '.'}")
    admitted = [r["signal"] for r in res if r["admitted"] and r["sign"] != 0]
    ADMITTED.write_text(json.dumps(
        {"per_signal": res, "admitted": admitted,
         "signs": {r["signal"]: r["sign"] for r in res}}, indent=1), encoding="utf-8")
    print(f"\nBH-FDR q={FDR_Q}: {len(admitted)} admitted -> {admitted}")
    if not admitted:
        print("OUTCOME: NULL-AT-ADMISSION -- validate is NOT consumed.")
    return 0


def cmd_validate() -> int:
    if not ADMITTED.exists():
        print("REFUSING: run train first.")
        return 2
    a = json.loads(ADMITTED.read_text(encoding="utf-8"))
    if not a["admitted"]:
        print("REFUSING: NULL-AT-ADMISSION -- validate must not be consumed.")
        return 3
    df = zscore(pl.read_parquet(EXP / "panel.parquet"))
    admitted, signs = a["admitted"], a["signs"]
    expr = [pl.col(f"z_{s}") * signs[s] for s in admitted]
    n_av = sum((e.is_not_null().cast(pl.Int32) for e in expr[1:]),
               expr[0].is_not_null().cast(pl.Int32))
    comp = sum(e.fill_null(0.0) for e in expr[1:]) + expr[0].fill_null(0.0)
    d = df.with_columns(n_av.alias("n_sig")).with_columns(
        pl.when(pl.col("n_sig") > 0).then(comp / pl.col("n_sig")).otherwise(None)
        .alias("comp")).drop_nulls(["comp", "ret_bps"]).filter(
        pl.col("comp").is_finite() & pl.col("ret_bps").is_finite())
    out = {}
    for tag, win in (("train", TRAIN), ("validate", VALID)):
        sub = d.filter((pl.col("date") >= win[0]) & (pl.col("date") <= win[1]))
        rows = []
        for key, g in sub.partition_by("date", as_dict=True, maintain_order=True).items():
            if g.height < MIN_NAMES:
                continue
            c = g["comp"].to_numpy()
            r = g["ret_bps"].to_numpy()
            k = max(1, int(round(g.height * DECILE)))
            o = np.argsort(c)
            gross = GROSS / 2 * r[o[-k:]].mean() - GROSS / 2 * r[o[:k]].mean()
            cost = GROSS * HS_FLAT + SEC_FEE
            rows.append({"date": key[0] if isinstance(key, tuple) else key,
                         "gross": gross, "net": gross - cost})
        dd = pl.DataFrame(rows)
        net = dd["net"].to_numpy()
        lo, hi, p = boot_mean(net)
        g3, g4, rho = sample_moments(net)
        sr = sr_native(net)
        out[tag] = {"sessions": dd.height, "gross": float(dd["gross"].to_numpy().mean()),
                    "net": float(net.mean()), "ci_lo": lo, "ci_hi": hi, "p": p,
                    "sr": sr, "psr": psr(sr, 0.0, dd.height, rho, g3, g4),
                    "min_trl": min_trl(sr, 0.0, ALPHA, rho, g3, g4)}
        print(f"{tag}: T={dd.height}  gross {out[tag]['gross']:+.2f}  "
              f"NET {out[tag]['net']:+.2f} [{lo:+.2f}, {hi:+.2f}]  SR {sr:+.3f}")
    v = out["validate"]
    cost = GROSS * HS_FLAT + SEC_FEE
    if v["ci_lo"] > 0 and v["gross"] >= 2 * cost:
        verdict = "PASS"
    elif v["ci_hi"] < 0 or v["gross"] < 2 * cost:
        verdict = "FAIL" if v["ci_hi"] < 0 else "BETWEEN"
    else:
        verdict = "BETWEEN"
    out["verdict"] = verdict
    (EXP / "result.json").write_text(json.dumps(out, indent=1, allow_nan=False),
                                     encoding="utf-8")
    print(f"\nVERDICT: {verdict}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M29 short-ratio battery.")
    ap.add_argument("stage", choices=["fetch", "build", "verify", "train", "validate"])
    a = ap.parse_args(argv)
    EXP.mkdir(parents=True, exist_ok=True)
    return {"fetch": cmd_fetch, "build": cmd_build, "verify": cmd_verify,
            "train": cmd_train, "validate": cmd_validate}[a.stage]()


if __name__ == "__main__":
    sys.exit(main())
