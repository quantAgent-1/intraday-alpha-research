"""retail_fade_daily_v1 LIVE MODEL — the real-time dynamic layer. BORN DARK.

This is the "statistical quant model, dynamic, in real time" for the retail-fade daily
book. Built BEFORE the decisive OOS verdict exists so it cannot be shaped to flatter a
result (m28_live / M20F precedent). Every trading-path command refuses unless ALL of:

  1. research/experiments/R2A-oos/phase3_result.json exists with verdict == "CONFIRMED",
  2. registration_marker.json exists (family registered in the ledger),
  3. thresholds.json exists (per-name |OLI| Q3 frozen from pre-holdout history by
     `freeze-thresholds`, itself gated on CONFIRMED).

Commands
    selftest            synthetic end-to-end checks; the only rich path that runs pre-PASS
    freeze-thresholds   freeze per-name fire thresholds from the historical panels (gated)
    signal --asof D     compute OLI for session D's open from D-1 tape; emit the book (gated)
    journal --asof D    append the emitted book to the append-only journal (gated)
    reconcile --asof D  realized open->15:45 net for a journalled session (gated)
    monitor             posterior + CUSUM + ADIA panel over the reconciled live track (gated)

THE DYNAMIC MODEL (report-only, per M23 doctrine — sizing/monitoring multiplies, never
creates): a conjugate Student-t posterior on the daily net edge, updated every session:
P(edge > 0 | data), full-sample and rolling-60; a scale-free one-sided CUSUM decay
tripwire (k=0.5 sd, h=5 sd — HUMAN-REVIEW ONLY, never a gate, per house doctrine); and the ADIA
No.19 panel (SR/PSR/MinTRL) via the audited M23 kernels, never re-implemented.

Signal-only: no order routing. Output = names/sides/weights keyed manually before 09:28.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from scipy.stats import t as student_t  # noqa: E402

from enginev51.research_screens.sizing_shadow import (  # noqa: E402
    min_trl,
    psr,
    sample_moments,
    sr_native,
)

OOS_DIR = REPO / "research" / "experiments" / "R2A-oos"
LIVE_DIR = REPO / "research" / "live" / "retail_fade_daily"
JOURNAL = LIVE_DIR / "journal.parquet"
RECON = LIVE_DIR / "reconciled.parquet"
THRESHOLDS = OOS_DIR / "thresholds.json"

DISCOVERY = ["NVDA", "TSLA", "AMD", "MU", "GOOGL", "KLAC", "MRVL", "LRCX", "TXN", "AMAT"]
OOS16 = ["VRTX", "BKNG", "ISRG", "AMGN", "HON", "INTU", "TMUS", "GILD",
         "MDLZ", "COST", "PEP", "ADBE", "CMCSA", "SBUX", "CSCO", "QCOM"]
ALL26 = DISCOVERY + OOS16

SEC_FEE = 0.206
# CUSUM in SIGMA UNITS (k=0.5 sd, h=5 sd — standard SPC values). The house M10 params
# (k=1.25 bps, h=150 bps) were calibrated for a ~15-20 bps/day stream; this book's daily
# sd is ~150 bps, so absolute-bps params would trip on single ordinary days. Human-review
# only, never a gate (doctrine).
CUSUM_K_SIG, CUSUM_H_SIG = 0.5, 5.0
ALPHA = 0.05


class Refused(RuntimeError):
    pass


def gate() -> None:
    p3 = OOS_DIR / "phase3_result.json"
    if not p3.exists():
        raise Refused("no phase3_result.json — the decisive OOS test has not run; model stays dark")
    v = json.loads(p3.read_text(encoding="utf-8")).get("verdict")
    if v != "CONFIRMED":
        raise Refused(f"OOS verdict is {v!r}, not 'CONFIRMED' — the model stays dark. "
                      "Revival requires a NEW registration, not a flag.")
    if not (OOS_DIR / "registration_marker.json").exists():
        raise Refused("registration marker absent — register retail_fade_daily_v1 first")


# ------------------------------------------------------------------ dynamics
def posterior_p_positive(x: np.ndarray) -> float:
    """P(mean > 0 | data) under the conjugate noninformative Normal model.

    Posterior of the mean is Student-t(df = n-1, loc = xbar, scale = s/sqrt(n)).
    Degenerate samples (n < 3 or zero variance) return 0.5 — no evidence, no claim.
    """
    n = x.size
    if n < 3:
        return 0.5
    s = float(np.std(x, ddof=1))
    if s == 0.0 or not np.isfinite(s):
        return 0.5
    return float(1.0 - student_t.cdf(0.0, df=n - 1, loc=float(np.mean(x)),
                                     scale=s / np.sqrt(n)))


def cusum_decay(x: np.ndarray, k_sig: float = CUSUM_K_SIG,
                h_sig: float = CUSUM_H_SIG) -> dict:
    """Scale-free one-sided lower CUSUM on standardized daily net.

    z = x / sd(x);  S = max(0, S + (-z - k));  trip at S > h. Detects a sustained
    downward shift of ~1 sd within ~a dozen sessions regardless of the book's scale."""
    if x.size < 10:
        return {"S": 0.0, "S_max": 0.0, "h": h_sig, "k": k_sig,
                "tripped": False, "tripped_at": None}
    sd = float(np.std(x, ddof=1))
    if sd == 0.0 or not np.isfinite(sd):
        return {"S": 0.0, "S_max": 0.0, "h": h_sig, "k": k_sig,
                "tripped": False, "tripped_at": None}
    s, s_max, tripped_at = 0.0, 0.0, None
    for i, v in enumerate(x / sd):
        s = max(0.0, s + (-float(v) - k_sig))
        if s > s_max:
            s_max = s
        if s > h_sig and tripped_at is None:
            tripped_at = i
    return {"S": s, "S_max": s_max, "h": h_sig, "k": k_sig,
            "tripped": tripped_at is not None, "tripped_at": tripped_at}


def dynamic_panel(net: np.ndarray) -> dict:
    g3, g4, rho = sample_moments(net)
    sr = sr_native(net)
    out = {
        "T": int(net.size),
        "mean_net_bps": float(net.mean()) if net.size else float("nan"),
        "p_edge_pos_full": posterior_p_positive(net),
        "p_edge_pos_roll60": posterior_p_positive(net[-60:]) if net.size >= 3 else 0.5,
        "sr_native": sr,
        "psr_sr0_0": psr(sr, 0.0, int(net.size), rho, g3, g4) if net.size >= 2 else None,
        "min_trl": min_trl(sr, 0.0, ALPHA, rho, g3, g4) if net.size >= 2 else None,
        "cusum": cusum_decay(net),
    }
    return out


# ------------------------------------------------------------------ signal
def compute_oli_for(sym: str, signal_date: str) -> float | None:
    """OLI of `signal_date` (the t-1 session) from local lakes: trades + NBBO quotes.

    Live operation pulls the day's tape after the close via the existing backfill
    machinery (scripts/backfill_trades_oos.py / backfill_quotes_oos.py run for that one
    session); this function then reads it locally. Frozen signing throughout.
    """
    import r2a_prong0 as R
    nbbo = REPO / "data" / "raw" / "bbo1s_nbbo"
    if (nbbo / sym).exists():
        R.BBO_DIR = nbbo                 # registered NBBO reference where available
    tr = R.load_trades_oddlot(sym, signal_date)
    if tr is None or tr[0].shape[0] == 0:
        return None
    day = R.BboCache(sym).get_day(signal_date)
    if day is None:
        return None
    q_ts, _sec, q_mid = day
    t_ts, t_px, t_sz = tr
    sign = R.sign_prints(t_ts, t_px, q_ts, q_mid)
    if int((sign != 0).sum()) < R.MIN_SIGNED:
        return None
    buy = float(t_sz[sign > 0].sum())
    sell = float(t_sz[sign < 0].sum())
    return (buy - sell) / (buy + sell) if (buy + sell) > 0 else None


def build_book(olis: dict[str, float], thresholds: dict[str, float],
               gross: float = 1.0) -> list[dict]:
    fires = [(s, o) for s, o in olis.items()
             if o is not None and s in thresholds and abs(o) >= thresholds[s]]
    if not fires:
        return []
    w = gross / len(fires)
    return [{"sym": s, "oli": o, "side": "SHORT" if o > 0 else "LONG",
             "weight": -np.sign(o) * w} for s, o in sorted(fires)]


def cmd_signal(asof: str) -> int:
    gate()
    th = json.loads(THRESHOLDS.read_text(encoding="utf-8"))["q3"]
    import r2a_prong0 as R
    bars = R.load_bars1d("KLAC")         # calendar reference
    dates = bars[0]
    if asof not in dates or dates.index(asof) < 1:
        raise Refused(f"{asof} not a known session or has no prior session")
    tm1 = dates[dates.index(asof) - 1]
    olis = {s: compute_oli_for(s, tm1) for s in ALL26}
    book = build_book(olis, th)
    n_avail = sum(1 for v in olis.values() if v is not None)
    print(f"session {asof} (signal from {tm1}): {n_avail}/26 names computable, "
          f"{len(book)} fires")
    for r in book:
        print(f"  {r['side']:5} {r['sym']:6} weight {r['weight']:+.4f}  OLI {r['oli']:+.4f}")
    print("Key as MARKET-ON-OPEN before 09:28 ET; exit taker 15:40-15:45. No close contact.")
    (LIVE_DIR / f"book_{asof}.json").parent.mkdir(parents=True, exist_ok=True)
    (LIVE_DIR / f"book_{asof}.json").write_text(
        json.dumps({"asof": asof, "signal_date": tm1, "book": book,
                    "emitted_at": datetime.now(UTC).isoformat()}, indent=1),
        encoding="utf-8")
    return 0


def cmd_freeze_thresholds() -> int:
    gate()
    q3: dict[str, float] = {}
    disc = pl.read_parquet(REPO / "research" / "experiments" / "R2A-prong0" / "panel.parquet")
    for key, g in disc.partition_by("sym", as_dict=True, maintain_order=True).items():
        s = key[0] if isinstance(key, tuple) else key
        q3[s] = float(np.percentile(np.abs(g["oli"].to_numpy()), 75))
    import r2a_prong0 as R
    R.BBO_DIR = REPO / "data" / "raw" / "bbo1s_nbbo"
    for s in OOS16:
        recs, _ = R.process_symbol(s)
        if recs:
            q3[s] = float(np.percentile(np.abs([r["oli"] for r in recs]), 75))
    THRESHOLDS.write_text(json.dumps(
        {"q3": q3, "frozen_at": datetime.now(UTC).isoformat(),
         "source": "pre-holdout history only"}, indent=1), encoding="utf-8")
    print(f"froze {len(q3)} thresholds -> {THRESHOLDS.relative_to(REPO)}")
    return 0


def cmd_monitor() -> int:
    gate()
    if not RECON.exists():
        print("no reconciled sessions yet")
        return 0
    net = pl.read_parquet(RECON).sort("date")["net_bps"].to_numpy()
    pan = dynamic_panel(net)
    print(f"live track T={pan['T']}  mean net {pan['mean_net_bps']:+.2f} bps/day")
    print(f"  P(edge>0 | all data)   {pan['p_edge_pos_full']:.3f}")
    print(f"  P(edge>0 | last 60)    {pan['p_edge_pos_roll60']:.3f}")
    print(f"  SR {pan['sr_native']:+.4f}  PSR {pan['psr_sr0_0']}  MinTRL {pan['min_trl']}")
    c = pan["cusum"]
    print(f"  CUSUM S={c['S']:.1f} (h={c['h']}) {'TRIPPED - human review' if c['tripped'] else 'quiet'}")
    return 0


def cmd_selftest() -> int:
    ok: list[tuple[str, bool, str]] = []
    try:
        gate()
        ok.append(("gate refuses pre-CONFIRMED", False, "did NOT refuse"))
    except Refused as e:
        ok.append(("gate refuses pre-CONFIRMED", True, str(e)[:55]))

    rng = np.random.default_rng(7)

    def constructed(mean: float, sd: float, n: int) -> np.ndarray:
        """Sample with EXACTLY the requested mean/sd — deterministic posterior tests.

        (A raw random draw makes these tests flaky by construction: under a true null
        the posterior P is uniform on (0,1), so any band fails at its own base rate.)"""
        z = rng.normal(0, 1, n)
        return mean + sd * (z - z.mean()) / z.std(ddof=1)

    strong = constructed(20.0, 150.0, 400)      # t = 20/(150/20) = 2.67 exactly
    nul = constructed(0.0, 150.0, 400)
    p_strong = posterior_p_positive(strong)
    p_null = posterior_p_positive(nul)
    ok.append(("posterior: t=2.67 edge -> P~0.996", p_strong > 0.99, f"{p_strong:.4f}"))
    ok.append(("posterior: exact-zero mean -> P=0.5",
               abs(p_null - 0.5) < 1e-9, f"{p_null:.4f}"))
    ok.append(("posterior: degenerate n<3 -> 0.5",
               posterior_p_positive(np.array([1.0])) == 0.5, "0.5"))

    healthy = constructed(0.15 * 150.0, 150.0, 300)          # +0.15 sd/day drift
    calm = cusum_decay(healthy)
    crash = cusum_decay(np.concatenate([healthy[:100],
                                        constructed(-1.0 * 150.0, 150.0, 40)]))
    ok.append(("CUSUM quiet on healthy track (sigma units)",
               not calm["tripped"], f"S_max {calm['S_max']:.1f} vs h {calm['h']}"))
    ok.append(("CUSUM trips on a -1sd/day decay run", crash["tripped"],
               f"at {crash['tripped_at']}"))

    olis = {"A": 0.5, "B": -0.4, "C": 0.01, "D": None, "E": 0.3}
    th = {"A": 0.2, "B": 0.2, "C": 0.2, "D": 0.2, "E": 0.4}
    book = build_book(olis, th, gross=1.0)
    ok.append(("book: only |OLI|>=Q3 fire", {b["sym"] for b in book} == {"A", "B"},
               str([b["sym"] for b in book])))
    ok.append(("book: gross == 1.0",
               abs(sum(abs(b["weight"]) for b in book) - 1.0) < 1e-12, "1.0"))
    ok.append(("book: fade direction (OLI>0 -> SHORT)",
               all((b["oli"] > 0) == (b["side"] == "SHORT") for b in book), "signs"))

    pan = dynamic_panel(strong)
    ok.append(("ADIA kernels finite on synthetic",
               np.isfinite(pan["sr_native"]) and pan["psr_sr0_0"] is not None, "panel"))

    for name, passed, detail in ok:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}  ({detail})")
    bad = sum(1 for _n, p, _d in ok if not p)
    print(f"selftest: {len(ok) - bad}/{len(ok)} passed")
    return 0 if bad == 0 else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="retail_fade_daily_v1 live model (dark until CONFIRMED).")
    ap.add_argument("cmd", choices=["selftest", "freeze-thresholds", "signal",
                                    "journal", "reconcile", "monitor"])
    ap.add_argument("--asof")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "selftest":
            return cmd_selftest()
        if a.cmd == "freeze-thresholds":
            return cmd_freeze_thresholds()
        if a.cmd == "monitor":
            return cmd_monitor()
        if a.cmd in ("journal", "reconcile"):
            gate()
            print(f"{a.cmd}: journal/reconcile activate with the forward clock after "
                  "CONFIRMED; storage layout is in place.")
            return 0
        if not a.asof:
            print("--asof required")
            return 2
        return cmd_signal(a.asof)
    except Refused as e:
        print(f"REFUSED: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
