"""F3 prong 0 -- opening-imbalance -> intraday-return pre-check (PRE-DECLARED).

Spec frozen in research ledger row `F3-prong0-predeclaration`
(ts 2026-07-23T13:24:06Z), pre-declared BEFORE any computation. This script
implements that row verbatim; no gated definition, threshold, or window is
altered. Where the spec is silent on an implementation detail the simplest
faithful option is chosen and documented in summary.md (Implementation notes).

STATE (gated):
  snapshot = LAST NOII opening-window row with 09:27:30 <= ts_ET <= 09:28:35
             (targets the 09:28:30 dissemination). No row -> drop the day.
  side_sign = +1 if side=='B', -1 if side=='S', 0 otherwise.
  ADV20     = mean of the strictly-prior 20 sessions' daily volume (bars1d).
  R         = side_sign * imbalance_shares / ADV20.

  DATA NOTE (documented, not a spec change): this vendor's NOII `side` column
  encodes {B, A, N} and never 'S'. 'B'=buy imbalance, 'N'=no imbalance
  (imbalance_shares==0), and the sell/ask side is coded 'A' (Nasdaq imbalance
  direction 'S' remapped to 'A'). The gated definition "sell side -> -1" is
  therefore realized as A -> -1. Implementing the literal token 'S' would map
  every sell-imbalance day to R=0 (a degenerate half-signal); mapping the
  data's sell token is the faithful reading. Snapshot side-code counts are
  reported so the mapping is fully auditable.

FORWARD (gated):
  anchor mid = first bbo1s mid with ts_ET >= 09:35:00, required <= 09:35:30.
  exit  mid  = last  bbo1s mid with ts_ET <= 11:00:00, required >= 10:55:00.
  fwd_bps    = (exit_mid/anchor_mid - 1) * 1e4.   (raw, same session)
  mid = (bid+ask)/2 with guard bid>0 AND ask>bid (crossed/locked excluded).

GATES (both computed; PASS/FAIL is mechanical, no interpretation):
  (a) INFO: pooled Pearson rho(R, fwd_bps) over ALL kept name-days (R=0 days
      included) after winsorizing BOTH variables at the pooled 1%/99% pctiles.
      Gate: rho >= +0.03 AND session-clustered bootstrap 95% CI-lo > 0.
  (b) MAGNITUDE: per-name |R| top-quartile (|R| >= that name's Q3, zeros incl.;
      a name with Q3==0 is dropped from (b)). signed_fwd = sign(R)*fwd_bps.
      Gate: mean(signed_fwd) >= +6.0 bps AND bootstrap 95% CI-lo > 0
      (signed_fwd RAW for the gate; a 1/99-winsorized mean+CI is reported as
      non-gating robustness).

Bootstrap (both gates): resample the SET of distinct session dates with
replacement, n_sessions draws/rep (a drawn date brings ALL its names' rows),
2000 reps, numpy seed 7, percentile CI (2.5/97.5). Gate (a) re-uses the
ORIGINAL full-sample winsor bounds per rep (no per-rep re-winsorize).

Supporting outputs (non-gating): horizons 10:05/10:35/15:45; R_paired variant;
final-pre-cross (<=09:29:55) snapshot variant; per-name table; coverage/sparsity;
contemporaneous open->anchor sanity rho.

Universe = symbols in BOTH the NOII lake (opening rows) and the bbo1s lake,
with >= 100 usable name-days. HARD CAP ts < 2026-06-01 ET (sealed holdout).
Self-contained, seeded, ASCII-only output. Writes result.json + summary.md
under research/experiments/F3-prong0/. Touches no other file.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
REPO = Path(__file__).resolve().parents[1]
NOII_DIR = REPO / "data" / "raw" / "noii"
BBO_DIR = REPO / "data" / "raw" / "bbo1s"
BARS_DIR = REPO / "data" / "raw" / "sip" / "bars1d"
OUT_DIR = REPO / "research" / "experiments" / "F3-prong0"

ET = ZoneInfo("America/New_York")

# bbo1s roster (10 names); universe is the intersection with the NOII lake.
BBO_SYMBOLS = ["AMAT", "AMD", "GOOGL", "KLAC", "LRCX", "MRVL", "MU", "NVDA",
               "TSLA", "TXN"]

CAP_DATE = "2026-06-01"          # keep ET session date strictly before this
MIN_NAME_DAYS = 100              # drop names with fewer usable (main) name-days

# ET seconds-of-day boundaries (hour*3600 + minute*60 + second).
OPEN_BAND_LO = 9 * 3600                       # 09:00:00  (isolate opening rows)
OPEN_BAND_HI = 9 * 3600 + 35 * 60             # 09:35:00  (exclusive)
SNAP_LO = 9 * 3600 + 27 * 60 + 30             # 09:27:30
SNAP_HI = 9 * 3600 + 28 * 60 + 35             # 09:28:35
PRECROSS_HI = 9 * 3600 + 29 * 60 + 55         # 09:29:55
ANCHOR_LO = 9 * 3600 + 35 * 60                # 09:35:00 (first mid >= this)
ANCHOR_HI = 9 * 3600 + 35 * 60 + 30           # 09:35:30 (required <=)
OPEN_MID_LO = 9 * 3600 + 30 * 60 + 5          # 09:30:05 (first mid >= this)
OPEN_MID_HI = 9 * 3600 + 30 * 60 + 35         # 09:30:35 (required <=)
EARLY_CLOSE_SEC = 15 * 3600 + 45 * 60         # 15:45:00 (last quote < this=drop)

# Forward horizons: label -> (required_lo, exit_hi). Exit = last mid <= exit_hi,
# required >= required_lo. '1100' is the MAIN gated horizon.
HORIZONS: dict[str, tuple[int, int]] = {
    "1100": (10 * 3600 + 55 * 60, 11 * 3600),                 # 10:55 .. 11:00
    "1005": (10 * 3600, 10 * 3600 + 5 * 60),                  # 10:00 .. 10:05
    "1035": (10 * 3600 + 30 * 60, 10 * 3600 + 35 * 60),       # 10:30 .. 10:35
    "1545": (15 * 3600 + 40 * 60, 15 * 3600 + 45 * 60),       # 15:40 .. 15:45
}
MAIN_H = "1100"

BOOT_SEED = 7
BOOT_REPS = 2000
GATE_A_RHO = 0.03
GATE_B_BPS = 6.0
WINSOR_LO_PCT = 1.0
WINSOR_HI_PCT = 99.0


# --------------------------------------------------------------------------- #
# Time helpers
# --------------------------------------------------------------------------- #
def _sec_date_exprs() -> tuple[pl.Expr, pl.Expr]:
    """(ET seconds-of-day int32, ET date string) from int64 ns UTC ts."""
    dt = pl.from_epoch(pl.col("ts"), time_unit="ns").dt.convert_time_zone(
        "America/New_York"
    )
    sec = (
        dt.dt.hour().cast(pl.Int32) * 3600
        + dt.dt.minute().cast(pl.Int32) * 60
        + dt.dt.second().cast(pl.Int32)
    )
    date = dt.dt.strftime("%Y-%m-%d")
    return sec, date


def _side_sign(side: str | None) -> int:
    # Gated: +1 for buy ('B'), -1 for sell, 0 otherwise. This vendor codes the
    # sell/ask side 'A' (see module docstring); 'S' also honored if ever present.
    if side == "B":
        return 1
    if side in ("A", "S"):
        return -1
    return 0


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.shape[0] < 3:
        return float("nan")
    xd = x - x.mean()
    yd = y - y.mean()
    denom = math.sqrt(float((xd * xd).sum()) * float((yd * yd).sum()))
    if denom == 0.0:
        return float("nan")
    return float((xd * yd).sum() / denom)


# --------------------------------------------------------------------------- #
# Per-month primitives
# --------------------------------------------------------------------------- #
def bbo_primitives(path: Path) -> dict[str, dict]:
    """Per ET-session forward primitives from one bbo1s month file."""
    df = pl.read_parquet(path, columns=["ts", "bid", "ask"])
    df = df.filter((pl.col("bid") > 0) & (pl.col("ask") > pl.col("bid")))
    if df.height == 0:
        return {}
    sec, date = _sec_date_exprs()
    df = df.with_columns(
        sec.alias("sec"),
        date.alias("d"),
        ((pl.col("bid") + pl.col("ask")) / 2.0).alias("mid"),
    ).sort("ts")
    out: dict[str, dict] = {}
    for key, g in df.partition_by("d", as_dict=True, maintain_order=True).items():
        d = key[0] if isinstance(key, tuple) else key
        s = g["sec"].to_numpy()
        m = g["mid"].to_numpy()
        rec: dict = {"last_quote_sec": int(s[-1])}
        # anchor: first mid with sec >= ANCHOR_LO, required <= ANCHOR_HI
        i = int(np.searchsorted(s, ANCHOR_LO, side="left"))
        rec["anchor_mid"] = (
            float(m[i]) if (i < s.shape[0] and s[i] <= ANCHOR_HI) else None
        )
        # open->anchor base: first mid >= OPEN_MID_LO, required <= OPEN_MID_HI
        i = int(np.searchsorted(s, OPEN_MID_LO, side="left"))
        rec["open_mid"] = (
            float(m[i]) if (i < s.shape[0] and s[i] <= OPEN_MID_HI) else None
        )
        # exits: last mid <= hi, required >= lo
        for h, (lo, hi) in HORIZONS.items():
            j = int(np.searchsorted(s, hi, side="right")) - 1
            rec[f"exit_{h}"] = (
                float(m[j]) if (j >= 0 and s[j] >= lo) else None
            )
        out[d] = rec
    return out


def noii_primitives(path: Path) -> tuple[dict[str, dict], dict[str, int]]:
    """Per ET-session opening snapshot + pre-cross state from one NOII month."""
    df = pl.read_parquet(
        path, columns=["ts", "side", "imbalance_shares", "paired_shares"]
    )
    sec, date = _sec_date_exprs()
    df = df.with_columns(sec.alias("sec"), date.alias("d"))
    df = df.filter(
        (pl.col("sec") >= OPEN_BAND_LO) & (pl.col("sec") < OPEN_BAND_HI)
    ).sort("ts")
    out: dict[str, dict] = {}
    side_codes: dict[str, int] = {}
    if df.height == 0:
        return out, side_codes
    for key, g in df.partition_by("d", as_dict=True, maintain_order=True).items():
        d = key[0] if isinstance(key, tuple) else key
        s = g["sec"].to_numpy()
        side = g["side"].to_list()
        imb = g["imbalance_shares"].to_numpy()
        prd = g["paired_shares"].to_numpy()
        rec: dict = {"opening_row_count": int(s.shape[0])}
        # snapshot: LAST row with SNAP_LO <= sec <= SNAP_HI
        mask = (s >= SNAP_LO) & (s <= SNAP_HI)
        idx = np.nonzero(mask)[0]
        if idx.shape[0] > 0:
            k = int(idx[-1])
            rec["has_snapshot"] = True
            rec["side"] = side[k]
            iv = imb[k]
            rec["imb"] = None if (iv is None or not np.isfinite(iv)) else float(iv)
            pv = prd[k]
            rec["paired"] = None if (pv is None or not np.isfinite(pv)) else float(pv)
            code = side[k] if side[k] is not None else "None"
            side_codes[code] = side_codes.get(code, 0) + 1
        else:
            rec["has_snapshot"] = False
        # pre-cross: LAST row with sec <= PRECROSS_HI
        maskp = s <= PRECROSS_HI
        idxp = np.nonzero(maskp)[0]
        if idxp.shape[0] > 0:
            k = int(idxp[-1])
            rec["has_precross"] = True
            rec["side_pc"] = side[k]
            iv = imb[k]
            rec["imb_pc"] = None if (iv is None or not np.isfinite(iv)) else float(iv)
        else:
            rec["has_precross"] = False
        out[d] = rec
    return out, side_codes


def build_adv_map(sym: str) -> dict[str, float]:
    """{ET session date -> ADV20 = mean of strictly-prior 20 daily volumes}."""
    path = BARS_DIR / f"{sym}.parquet"
    if not path.exists():
        return {}
    df = pl.read_parquet(path, columns=["ts", "volume"]).sort("ts")
    _, date = _sec_date_exprs()
    df = df.with_columns(date.alias("d")).with_columns(
        pl.col("volume").shift(1).rolling_mean(window_size=20, min_samples=20)
        .alias("adv20")
    )
    out: dict[str, float] = {}
    for d, a in zip(df["d"].to_list(), df["adv20"].to_list()):
        if a is not None and np.isfinite(a):
            out[d] = float(a)
    return out


# --------------------------------------------------------------------------- #
# Symbol driver -> per-candidate records
# --------------------------------------------------------------------------- #
def process_symbol(sym: str) -> tuple[list[dict], dict[str, int]]:
    adv_map = build_adv_map(sym)
    noii_dir = NOII_DIR / sym
    bbo_dir = BBO_DIR / sym
    if not noii_dir.exists() or not bbo_dir.exists():
        return [], {}
    months = sorted(
        f.stem for f in bbo_dir.glob("*.parquet") if f.stem < "2026-06"
    )
    records: list[dict] = []
    side_codes: dict[str, int] = {}
    for mo in months:
        bpath = bbo_dir / f"{mo}.parquet"
        npath = noii_dir / f"{mo}.parquet"
        bbo = bbo_primitives(bpath)
        noii, sc = (noii_primitives(npath) if npath.exists() else ({}, {}))
        for c, n in sc.items():
            side_codes[c] = side_codes.get(c, 0) + n
        for d, bp in bbo.items():
            if d >= CAP_DATE:
                continue
            np_ = noii.get(d, {})
            snap = np_.get("has_snapshot", False)
            side = np_.get("side")
            ss = _side_sign(side) if snap else 0
            imb = np_.get("imb")
            paired = np_.get("paired")
            adv = adv_map.get(d)
            has_pc = np_.get("has_precross", False)
            side_pc = np_.get("side_pc")
            ss_pc = _side_sign(side_pc) if has_pc else 0
            imb_pc = np_.get("imb_pc")
            rec = {
                "sym": sym,
                "date": d,
                "last_quote_sec": bp["last_quote_sec"],
                "early_close": bp["last_quote_sec"] < EARLY_CLOSE_SEC,
                "opening_row_count": int(np_.get("opening_row_count", 0)),
                "has_snapshot": snap,
                "side": side,
                "side_sign": ss,
                "imb": imb,
                "paired": paired,
                "has_precross": has_pc,
                "side_sign_pc": ss_pc,
                "imb_pc": imb_pc,
                "adv20": adv,
                "anchor_mid": bp["anchor_mid"],
                "open_mid": bp["open_mid"],
            }
            for h in HORIZONS:
                rec[f"exit_{h}"] = bp[f"exit_{h}"]
            records.append(rec)
    return records, side_codes


# --------------------------------------------------------------------------- #
# Funnel + derived quantities
# --------------------------------------------------------------------------- #
def run_funnel(records: list[dict]) -> dict:
    """Attribute each candidate to the first guard it fails (fixed order)."""
    order = ["early_close", "no_snapshot", "imb_null", "no_adv", "no_anchor",
             "no_exit_1100"]
    counts = {k: 0 for k in order}
    n_candidates = len(records)
    base_kept: list[dict] = []   # passed through anchor (all supporting horizons)
    main_kept: list[dict] = []   # base_kept AND has exit_1100
    for r in records:
        if r["early_close"]:
            counts["early_close"] += 1
            continue
        if not r["has_snapshot"]:
            counts["no_snapshot"] += 1
            continue
        if r["imb"] is None:
            counts["imb_null"] += 1
            continue
        if r["adv20"] is None:
            counts["no_adv"] += 1
            continue
        if r["anchor_mid"] is None:
            counts["no_anchor"] += 1
            continue
        # derive R and forward returns
        r = dict(r)
        r["R"] = r["side_sign"] * r["imb"] / r["adv20"]
        pr = r["paired"] if (r["paired"] is not None) else 0.0
        r["R2"] = r["side_sign"] * r["imb"] / max(pr, 1.0)
        for h in HORIZONS:
            ex = r[f"exit_{h}"]
            r[f"fwd_{h}"] = (
                (ex / r["anchor_mid"] - 1.0) * 1e4 if ex is not None else None
            )
        r["o2a"] = (
            (r["anchor_mid"] / r["open_mid"] - 1.0) * 1e4
            if r["open_mid"] is not None
            else None
        )
        base_kept.append(r)
        if r[f"exit_{MAIN_H}"] is None:
            counts["no_exit_1100"] += 1
            continue
        main_kept.append(r)
    return {
        "n_candidates": n_candidates,
        "drop_order": order,
        "drop_counts": counts,
        "base_kept": base_kept,
        "main_kept": main_kept,
    }


def _winsor_bounds(a: np.ndarray) -> tuple[float, float]:
    return (
        float(np.percentile(a, WINSOR_LO_PCT)),
        float(np.percentile(a, WINSOR_HI_PCT)),
    )


def _session_bootstrap_rho(
    dates: np.ndarray, xw: np.ndarray, yw: np.ndarray, seed: int, reps: int
) -> tuple[float, float]:
    """Session-clustered bootstrap CI (2.5/97.5) of Pearson rho on winsorized xy."""
    uniq = np.unique(dates)
    n = uniq.shape[0]
    idx_by_date = {d: np.nonzero(dates == d)[0] for d in uniq}
    idx_list = [idx_by_date[d] for d in uniq]
    rng = np.random.default_rng(seed)
    boot = np.empty(reps)
    for i in range(reps):
        draw = rng.integers(0, n, n)
        sel = np.concatenate([idx_list[j] for j in draw])
        boot[i] = _pearson(xw[sel], yw[sel])
    boot = boot[np.isfinite(boot)]
    if boot.shape[0] == 0:
        return float("nan"), float("nan")
    return float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def _session_bootstrap_mean(
    dates: np.ndarray, v: np.ndarray, seed: int, reps: int
) -> tuple[float, float]:
    """Session-clustered bootstrap CI (2.5/97.5) of the mean of v."""
    uniq = np.unique(dates)
    n = uniq.shape[0]
    idx_by_date = {d: np.nonzero(dates == d)[0] for d in uniq}
    idx_list = [idx_by_date[d] for d in uniq]
    rng = np.random.default_rng(seed)
    boot = np.empty(reps)
    for i in range(reps):
        draw = rng.integers(0, n, n)
        sel = np.concatenate([idx_list[j] for j in draw])
        boot[i] = float(v[sel].mean())
    return float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def rho_winsorized(R: np.ndarray, fwd: np.ndarray) -> tuple[float, np.ndarray,
                                                            np.ndarray, tuple,
                                                            tuple]:
    """Winsorize both at pooled 1/99 and return rho + winsorized arrays+bounds."""
    rlo, rhi = _winsor_bounds(R)
    flo, fhi = _winsor_bounds(fwd)
    Rw = np.clip(R, rlo, rhi)
    fw = np.clip(fwd, flo, fhi)
    return _pearson(Rw, fw), Rw, fw, (rlo, rhi), (flo, fhi)


def top_quartile_signed(
    kept: list[dict], hcol: str, rcol: str = "R"
) -> tuple[np.ndarray, np.ndarray, dict, list[str]]:
    """Per-name |R|>=Q3 subset; return signed_fwd, dates, per-name Q3, dropped."""
    by_name: dict[str, list[dict]] = {}
    for r in kept:
        by_name.setdefault(r["sym"], []).append(r)
    signed: list[float] = []
    sdates: list[str] = []
    q3_by_name: dict[str, float] = {}
    dropped: list[str] = []
    for name, rows in by_name.items():
        absR = np.array([abs(r[rcol]) for r in rows])
        q3 = float(np.percentile(absR, 75))
        q3_by_name[name] = q3
        if q3 == 0.0:
            dropped.append(name)
            continue
        for r in rows:
            if abs(r[rcol]) >= q3:
                signed.append(np.sign(r[rcol]) * r[hcol])
                sdates.append(r["date"])
    return (np.array(signed), np.array(sdates), q3_by_name, dropped)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    all_records: dict[str, list[dict]] = {}
    side_codes: dict[str, dict[str, int]] = {}
    for sym in BBO_SYMBOLS:
        recs, sc = process_symbol(sym)
        all_records[sym] = recs
        side_codes[sym] = sc

    # per-symbol funnels
    funnels = {sym: run_funnel(all_records[sym]) for sym in BBO_SYMBOLS}

    # roster: names with >= MIN_NAME_DAYS usable (main) name-days
    name_days = {sym: len(funnels[sym]["main_kept"]) for sym in BBO_SYMBOLS}
    roster = [s for s in BBO_SYMBOLS if name_days[s] >= MIN_NAME_DAYS]
    dropped_names = {s: name_days[s] for s in BBO_SYMBOLS if s not in roster}

    # ----- pooled MAIN analysis set (11:00) -----
    main_all = [r for s in roster for r in funnels[s]["main_kept"]]
    R = np.array([r["R"] for r in main_all], dtype=np.float64)
    fwd = np.array([r[f"fwd_{MAIN_H}"] for r in main_all], dtype=np.float64)
    dates = np.array([r["date"] for r in main_all])
    names = np.array([r["sym"] for r in main_all])
    n_main = R.shape[0]
    n_sessions_main = int(np.unique(dates).shape[0])

    # ----- GATE (a) -----
    rho_a, Rw, fw, rbnds, fbnds = rho_winsorized(R, fwd)
    ci_a_lo, ci_a_hi = _session_bootstrap_rho(dates, Rw, fw, BOOT_SEED, BOOT_REPS)
    gate_a_pass = bool(
        np.isfinite(rho_a) and rho_a >= GATE_A_RHO and np.isfinite(ci_a_lo)
        and ci_a_lo > 0.0
    )

    # ----- GATE (b) -----
    signed, sdates, q3_by_name, dropped_b = top_quartile_signed(
        main_all, f"fwd_{MAIN_H}"
    )
    n_b = signed.shape[0]
    mean_b = float(signed.mean()) if n_b else float("nan")
    ci_b_lo, ci_b_hi = (
        _session_bootstrap_mean(sdates, signed, BOOT_SEED, BOOT_REPS)
        if n_b else (float("nan"), float("nan"))
    )
    gate_b_pass = bool(
        np.isfinite(mean_b) and mean_b >= GATE_B_BPS and np.isfinite(ci_b_lo)
        and ci_b_lo > 0.0
    )
    # non-gating winsorized robustness on signed_fwd
    if n_b:
        sblo, sbhi = _winsor_bounds(signed)
        signed_w = np.clip(signed, sblo, sbhi)
        mean_b_w = float(signed_w.mean())
        ci_bw_lo, ci_bw_hi = _session_bootstrap_mean(
            sdates, signed_w, BOOT_SEED, BOOT_REPS
        )
    else:
        mean_b_w = float("nan")
        ci_bw_lo = ci_bw_hi = float("nan")
        sblo = sbhi = float("nan")

    # ----- supporting 1: other horizons (point estimates only) -----
    horizon_support: dict[str, dict] = {}
    for h in HORIZONS:
        kept_h = [
            r for s in roster for r in funnels[s]["base_kept"]
            if r[f"fwd_{h}"] is not None
        ]
        Rh = np.array([r["R"] for r in kept_h], dtype=np.float64)
        fh = np.array([r[f"fwd_{h}"] for r in kept_h], dtype=np.float64)
        rho_h = (
            rho_winsorized(Rh, fh)[0] if Rh.shape[0] >= 3 else float("nan")
        )
        sg, _, _, drp = top_quartile_signed(kept_h, f"fwd_{h}")
        horizon_support[h] = {
            "n": int(Rh.shape[0]),
            "rho_winsor": rho_h,
            "topq_n": int(sg.shape[0]),
            "topq_mean_signed_bps": float(sg.mean()) if sg.shape[0] else float("nan"),
            "topq_names_dropped_q3zero": drp,
        }

    # ----- supporting 2: R_paired variant (11:00) -----
    R2 = np.array([r["R2"] for r in main_all], dtype=np.float64)
    rho_r2 = rho_winsorized(R2, fwd)[0] if n_main >= 3 else float("nan")

    # ----- supporting 3: final pre-cross snapshot variant (11:00) -----
    precross = []
    for s in roster:
        for r in all_records[s]:
            if r["early_close"] or not r["has_precross"]:
                continue
            if r["imb_pc"] is None or r["adv20"] is None:
                continue
            adv = r["adv20"]
            anc = r["anchor_mid"]
            # need main-horizon exit + anchor for fwd
            if anc is None:
                continue
            bp_exit = None
            # find this candidate's main exit from stored record
            ex = r.get(f"exit_{MAIN_H}")
            if ex is None:
                continue
            rr = {
                "sym": s,
                "date": r["date"],
                "R": r["side_sign_pc"] * r["imb_pc"] / adv,
                f"fwd_{MAIN_H}": (ex / anc - 1.0) * 1e4,
            }
            precross.append(rr)
    if len(precross) >= 3:
        Rpc = np.array([r["R"] for r in precross], dtype=np.float64)
        fpc = np.array([r[f"fwd_{MAIN_H}"] for r in precross], dtype=np.float64)
        rho_pc = rho_winsorized(Rpc, fpc)[0]
        sg_pc, _, _, drp_pc = top_quartile_signed(precross, f"fwd_{MAIN_H}")
        precross_support = {
            "n": int(Rpc.shape[0]),
            "rho_winsor": rho_pc,
            "topq_n": int(sg_pc.shape[0]),
            "topq_mean_signed_bps": (
                float(sg_pc.mean()) if sg_pc.shape[0] else float("nan")
            ),
            "topq_names_dropped_q3zero": drp_pc,
        }
    else:
        precross_support = {"n": len(precross), "rho_winsor": float("nan"),
                            "topq_n": 0, "topq_mean_signed_bps": float("nan"),
                            "topq_names_dropped_q3zero": []}

    # ----- supporting 4: per-name table (uses pooled winsor bounds for rho) -----
    per_name: dict[str, dict] = {}
    for s in roster:
        mnamemask = names == s
        Rn = Rw[mnamemask]
        fn = fw[mnamemask]
        rho_n = _pearson(Rn, fn) if Rn.shape[0] >= 3 else float("nan")
        rows = funnels[s]["main_kept"]
        absR = np.array([abs(r["R"]) for r in rows])
        q3 = q3_by_name.get(s, float("nan"))
        if s in dropped_b or (isinstance(q3, float) and q3 == 0.0):
            topq_n = 0
            topq_mean = float("nan")
        else:
            sub = [r for r in rows if abs(r["R"]) >= q3]
            sv = np.array([np.sign(r["R"]) * r[f"fwd_{MAIN_H}"] for r in sub])
            topq_n = int(sv.shape[0])
            topq_mean = float(sv.mean()) if sv.shape[0] else float("nan")
        per_name[s] = {
            "n_main_days": int(mnamemask.sum()),
            "rho_winsor_11": rho_n,
            "q3_absR": q3,
            "topq_n": topq_n,
            "topq_mean_signed_bps": topq_mean,
        }

    # ----- supporting 5: coverage / sparsity per name -----
    coverage: dict[str, dict] = {}
    for s in BBO_SYMBOLS:
        recs = all_records[s]
        f = funnels[s]
        cand = f["n_candidates"]
        with_noii = [r for r in recs if r["opening_row_count"] > 0]
        oc = np.array([r["opening_row_count"] for r in with_noii]) if with_noii \
            else np.array([])
        # sparsity of the used state among MAIN kept days
        mk = f["main_kept"]
        if mk:
            zero_state = sum(
                1 for r in mk if r["side_sign"] == 0 or r["imb"] == 0.0
            )
            absR = np.array([abs(r["R"]) for r in mk])
            frac_zero = zero_state / len(mk)
            absR_q = {
                "p50": float(np.percentile(absR, 50)),
                "p75": float(np.percentile(absR, 75)),
                "p90": float(np.percentile(absR, 90)),
                "p99": float(np.percentile(absR, 99)),
            }
        else:
            frac_zero = float("nan")
            absR_q = {"p50": float("nan"), "p75": float("nan"),
                      "p90": float("nan"), "p99": float("nan")}
        dc = f["drop_counts"]
        coverage[s] = {
            "candidates": cand,
            "sessions_with_opening_noii": len(with_noii),
            "opening_rows_per_day": {
                "min": int(oc.min()) if oc.size else 0,
                "p25": float(np.percentile(oc, 25)) if oc.size else float("nan"),
                "median": float(np.percentile(oc, 50)) if oc.size else float("nan"),
                "p75": float(np.percentile(oc, 75)) if oc.size else float("nan"),
                "max": int(oc.max()) if oc.size else 0,
            },
            "frac_state_zero_among_main": frac_zero,
            "drop_frac": {
                k: (dc[k] / cand if cand else float("nan")) for k in dc
            },
            "absR_quantiles_main": absR_q,
            "main_days": len(mk),
        }

    # ----- supporting 6: contemporaneous open->anchor sanity (raw rho) -----
    o2a_rows = [r for r in main_all if r["o2a"] is not None]
    if len(o2a_rows) >= 3:
        Ro = np.array([r["R"] for r in o2a_rows], dtype=np.float64)
        oo = np.array([r["o2a"] for r in o2a_rows], dtype=np.float64)
        rho_o2a = _pearson(Ro, oo)
    else:
        rho_o2a = float("nan")
    n_o2a = len(o2a_rows)

    # ----------------------------------------------------------------------- #
    # Assemble result
    # ----------------------------------------------------------------------- #
    result = {
        "spec": "F3-prong0-predeclaration",
        "spec_ts": "2026-07-23T13:24:06Z",
        "note": "PRE-DECLARED DIAGNOSTIC. Opening-imbalance state R vs raw "
        "same-session forward mid return. PASS/FAIL is mechanical.",
        "side_mapping": {
            "B": 1, "A": -1, "S": -1, "N_or_other": 0,
            "comment": "vendor codes sell/ask side 'A' (never 'S'); see summary",
        },
        "snapshot_side_code_counts": side_codes,
        "config": {
            "universe_candidates": BBO_SYMBOLS,
            "roster": roster,
            "dropped_names_lt_100": dropped_names,
            "cap_date_exclusive": CAP_DATE,
            "min_name_days": MIN_NAME_DAYS,
            "windows_et_sec": {
                "opening_band": [OPEN_BAND_LO, OPEN_BAND_HI],
                "snapshot": [SNAP_LO, SNAP_HI],
                "precross_hi": PRECROSS_HI,
                "anchor": [ANCHOR_LO, ANCHOR_HI],
                "open_mid": [OPEN_MID_LO, OPEN_MID_HI],
                "early_close_lt": EARLY_CLOSE_SEC,
                "horizons": HORIZONS,
            },
            "boot_seed": BOOT_SEED,
            "boot_reps": BOOT_REPS,
            "winsor_pct": [WINSOR_LO_PCT, WINSOR_HI_PCT],
            "gate_a_rho_min": GATE_A_RHO,
            "gate_b_bps_min": GATE_B_BPS,
        },
        "analysis_set_main": {
            "n_name_days": n_main,
            "n_sessions": n_sessions_main,
            "winsor_bounds_R": list(rbnds),
            "winsor_bounds_fwd": list(fbnds),
        },
        "gate_a_info": {
            "rho_winsor": rho_a,
            "ci95_lo": ci_a_lo,
            "ci95_hi": ci_a_hi,
            "n": n_main,
            "n_sessions": n_sessions_main,
            "threshold": GATE_A_RHO,
            "pass": gate_a_pass,
        },
        "gate_b_magnitude": {
            "topq_n": n_b,
            "mean_signed_bps": mean_b,
            "ci95_lo": ci_b_lo,
            "ci95_hi": ci_b_hi,
            "threshold_bps": GATE_B_BPS,
            "pass": gate_b_pass,
            "names_dropped_q3zero": dropped_b,
            "q3_absR_by_name": q3_by_name,
            "winsor_robustness": {
                "mean_signed_bps": mean_b_w,
                "ci95_lo": ci_bw_lo,
                "ci95_hi": ci_bw_hi,
                "winsor_bounds": [sblo, sbhi],
            },
        },
        "support_horizons": horizon_support,
        "support_R_paired_11": {"rho_winsor": rho_r2, "n": n_main},
        "support_precross_11": precross_support,
        "support_per_name": per_name,
        "support_coverage": coverage,
        "support_open_to_anchor_sanity": {"rho_raw": rho_o2a, "n": n_o2a},
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(
        json.dumps(_clean(result), indent=2), encoding="utf-8"
    )
    _write_summary(OUT_DIR / "summary.md", result)
    _print_console(result)


# --------------------------------------------------------------------------- #
# Serialization + reporting
# --------------------------------------------------------------------------- #
def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        f = float(o)
        return None if not math.isfinite(f) else f
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def _fmt(x, nd: int = 4) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "n/a"
    return f"{x:.{nd}f}"


def _write_summary(path: Path, r: dict) -> None:
    L: list[str] = []
    L.append("# F3 prong 0 -- opening-imbalance -> intraday-return pre-check")
    L.append("")
    L.append("PRE-DECLARED DIAGNOSTIC (ledger row `F3-prong0-predeclaration`, "
             "ts 2026-07-23T13:24:06Z). PASS/FAIL below is mechanical.")
    L.append("")
    cfg = r["config"]
    L.append(f"Roster ({len(cfg['roster'])}): {', '.join(cfg['roster'])}  |  "
             f"cap ts < {cfg['cap_date_exclusive']} ET  |  "
             f"dropped (<100 days): {cfg['dropped_names_lt_100'] or 'none'}")
    am = r["analysis_set_main"]
    L.append(f"Main analysis set (11:00): n={am['n_name_days']} name-days over "
             f"{am['n_sessions']} sessions.")
    L.append("")

    # side codes
    L.append("## Snapshot side-code counts (state variable)")
    L.append("")
    L.append("| name | B (+1) | A (-1) | N (0) | other |")
    L.append("|------|--------|--------|-------|-------|")
    for s in cfg["universe_candidates"]:
        sc = r["snapshot_side_code_counts"].get(s, {})
        other = sum(v for k, v in sc.items() if k not in ("B", "A", "N"))
        L.append(f"| {s} | {sc.get('B',0)} | {sc.get('A',0)} | "
                 f"{sc.get('N',0)} | {other} |")
    L.append("")

    # gate a
    ga = r["gate_a_info"]
    L.append("## GATE (a) INFO -- pooled winsorized rho(R, fwd_bps 11:00)")
    L.append("")
    L.append(f"rho = {_fmt(ga['rho_winsor'])}  |  95% CI (session-clustered) "
             f"[{_fmt(ga['ci95_lo'])}, {_fmt(ga['ci95_hi'])}]  |  "
             f"gate rho>={ga['threshold']} AND CI-lo>0  ->  "
             f"{'PASS' if ga['pass'] else 'FAIL'}")
    L.append(f"(n={ga['n']} name-days, {ga['n_sessions']} sessions; "
             f"seed {cfg['boot_seed']}, {cfg['boot_reps']} reps)")
    L.append("")

    # gate b
    gb = r["gate_b_magnitude"]
    L.append("## GATE (b) MAGNITUDE -- per-name |R| top-quartile signed fwd (11:00)")
    L.append("")
    L.append(f"mean signed_fwd = {_fmt(gb['mean_signed_bps'])} bps  |  95% CI "
             f"[{_fmt(gb['ci95_lo'])}, {_fmt(gb['ci95_hi'])}]  |  "
             f"gate mean>={gb['threshold_bps']} AND CI-lo>0  ->  "
             f"{'PASS' if gb['pass'] else 'FAIL'}")
    L.append(f"(top-quartile n={gb['topq_n']}; names dropped for Q3==0: "
             f"{gb['names_dropped_q3zero'] or 'none'})")
    wr = gb["winsor_robustness"]
    L.append(f"non-gating winsor(1/99) mean = {_fmt(wr['mean_signed_bps'])} bps  "
             f"CI [{_fmt(wr['ci95_lo'])}, {_fmt(wr['ci95_hi'])}]")
    L.append("")

    # supporting horizons
    L.append("## Support 1 -- other horizons (point estimates, no CI)")
    L.append("")
    L.append("| horizon | n | rho_winsor | topq_n | topq_mean_signed_bps |")
    L.append("|---------|---|-----------|--------|----------------------|")
    for h in ["1100", "1005", "1035", "1545"]:
        hh = r["support_horizons"][h]
        tag = h if h != "1100" else "1100(main)"
        L.append(f"| {tag} | {hh['n']} | {_fmt(hh['rho_winsor'])} | "
                 f"{hh['topq_n']} | {_fmt(hh['topq_mean_signed_bps'])} |")
    L.append("")

    # R_paired + precross
    rp = r["support_R_paired_11"]
    pc = r["support_precross_11"]
    L.append("## Support 2-3 -- R_paired variant and pre-cross snapshot (11:00)")
    L.append("")
    L.append(f"R_paired rho_winsor = {_fmt(rp['rho_winsor'])} (n={rp['n']})")
    L.append(f"pre-cross(<=09:29:55) rho_winsor = {_fmt(pc['rho_winsor'])} "
             f"(n={pc['n']}); topq mean = {_fmt(pc['topq_mean_signed_bps'])} bps "
             f"(topq_n={pc['topq_n']})")
    L.append("")

    # per-name
    L.append("## Support 4 -- per-name (main 11:00)")
    L.append("")
    L.append("| name | n_days | rho_winsor | q3_absR | topq_n | topq_mean_bps |")
    L.append("|------|--------|-----------|--------|--------|---------------|")
    for s in cfg["roster"]:
        pn = r["support_per_name"][s]
        L.append(f"| {s} | {pn['n_main_days']} | {_fmt(pn['rho_winsor_11'])} | "
                 f"{_fmt(pn['q3_absR'], 6)} | {pn['topq_n']} | "
                 f"{_fmt(pn['topq_mean_signed_bps'])} |")
    L.append("")

    # coverage
    L.append("## Support 5 -- coverage / sparsity")
    L.append("")
    L.append("| name | cand | w/opening | oc med | frac_state0 | absR_p50 | "
             "absR_p90 | absR_p99 |")
    L.append("|------|------|-----------|--------|-------------|-------|"
             "-------|-------|")
    for s in cfg["universe_candidates"]:
        cv = r["support_coverage"][s]
        oc = cv["opening_rows_per_day"]
        aq = cv["absR_quantiles_main"]
        L.append(f"| {s} | {cv['candidates']} | "
                 f"{cv['sessions_with_opening_noii']} | "
                 f"{_fmt(oc['median'],0)} | "
                 f"{_fmt(cv['frac_state_zero_among_main'],3)} | "
                 f"{_fmt(aq['p50'],6)} | {_fmt(aq['p90'],6)} | "
                 f"{_fmt(aq['p99'],6)} |")
    L.append("")
    L.append("### Drop fractions (first-failing guard, order: early_close, "
             "no_snapshot, imb_null, no_adv, no_anchor, no_exit_1100)")
    L.append("")
    L.append("| name | cand | early_close | no_snapshot | imb_null | no_adv | "
             "no_anchor | no_exit_1100 | main_days |")
    L.append("|------|------|-------------|-------------|----------|--------|"
             "-----------|--------------|-----------|")
    for s in cfg["universe_candidates"]:
        cv = r["support_coverage"][s]
        df = cv["drop_frac"]
        L.append(f"| {s} | {cv['candidates']} | "
                 f"{_fmt(df['early_close'],3)} | {_fmt(df['no_snapshot'],3)} | "
                 f"{_fmt(df['imb_null'],3)} | {_fmt(df['no_adv'],3)} | "
                 f"{_fmt(df['no_anchor'],3)} | {_fmt(df['no_exit_1100'],3)} | "
                 f"{cv['main_days']} |")
    L.append("")

    # sanity
    so = r["support_open_to_anchor_sanity"]
    L.append("## Support 6 -- contemporaneous sanity")
    L.append("")
    L.append(f"rho_raw(R, open->anchor return) = {_fmt(so['rho_raw'])} "
             f"(n={so['n']}) -- labels how much state is already spent by 09:35.")
    L.append("")

    # implementation notes
    L.append("## Implementation notes (faithful-simplest choices)")
    L.append("")
    L.append(
        "1. NOII `side` is coded {B, A, N}; 'S' never appears. 'N' rows have "
        "imbalance_shares==0. The gated 'sell -> -1' is realized as A -> -1 "
        "('A'=ask/sell side); the literal token 'S' is also honored but is "
        "absent. Snapshot side-code counts are reported for audit. "
        "2. Opening rows are isolated by ET time-of-day [09:00:00, 09:35:00) "
        "before applying the snapshot [09:27:30, 09:28:35] and pre-cross "
        "(<=09:29:55) sub-windows; closing-auction rows (15:5x) and any stray "
        "rows are thereby excluded. On this tape opening NOII disseminates "
        "~every 10s from 09:25 and ~every 1s from 09:28. "
        "3. bbo1s carries EXTENDED HOURS (valid two-sided quotes ~04:00-20:00 "
        "ET; ~17:00 on exchange half-days). The early-close guard (last valid "
        "quote < 15:45 ET) therefore fires only on truly truncated sessions and "
        "does NOT exclude exchange half-days, whose post-market quotes run past "
        "15:45. All gated intraday windows sit inside RTH and are unaffected. "
        "'Last quote of the day' uses the last valid two-sided mid. "
        "4. mid=(bid+ask)/2 with bid>0 AND ask>bid. anchor/exit found via "
        "searchsorted on the per-session ET-seconds array (monotone within a "
        "session), guarded against index -1 wrap. "
        "5. ADV20 = shift(1).rolling_mean(20, min_samples=20) of daily bars1d "
        "volume (bars1d ts is ET-midnight; date via America/New_York); a session "
        "date not present in bars1d, or with <20 prior bars, drops (no_adv). "
        "6. Session date = ET calendar date; joins across NOII/bbo1s/bars1d are "
        "by that date string. Candidates = bbo1s sessions with ET date < "
        "2026-06-01. Duplicate NOII ts within the snapshot window -> last by ts "
        "order. "
        "7. Winsorization = numpy clip at pooled 1st/99th percentiles "
        "(numpy linear interpolation). Per-name and per-horizon rho re-use the "
        "pooled winsor bounds where a pooled set exists; supporting-horizon "
        "top-quartile Q3 breakpoints are recomputed over each horizon's own kept "
        "set. The open->anchor sanity rho is raw (spec did not request winsor). "
        "8. Bootstrap: a fresh numpy default_rng(7) per gate; n_sessions draws of "
        "distinct session dates with replacement, each drawn date contributing "
        "all its rows; 2000 reps; 2.5/97.5 percentile CI."
    )
    L.append("")
    path.write_text("\n".join(L), encoding="utf-8")


def _print_console(r: dict) -> None:
    ga = r["gate_a_info"]
    gb = r["gate_b_magnitude"]
    cfg = r["config"]
    print("=" * 72)
    print("F3 PRONG 0 -- OPENING-IMBALANCE PRE-CHECK (PRE-DECLARED DIAGNOSTIC)")
    print("=" * 72)
    print(f"roster ({len(cfg['roster'])}): {', '.join(cfg['roster'])}")
    print(f"main set n={r['analysis_set_main']['n_name_days']} name-days, "
          f"{r['analysis_set_main']['n_sessions']} sessions")
    print("-" * 72)
    print(f"GATE(a) rho_winsor = {_fmt(ga['rho_winsor'])}  "
          f"CI[{_fmt(ga['ci95_lo'])},{_fmt(ga['ci95_hi'])}]  "
          f"(>= {ga['threshold']} & CI-lo>0) -> "
          f"{'PASS' if ga['pass'] else 'FAIL'}")
    print(f"GATE(b) mean_signed = {_fmt(gb['mean_signed_bps'])} bps  "
          f"CI[{_fmt(gb['ci95_lo'])},{_fmt(gb['ci95_hi'])}]  "
          f"(>= {gb['threshold_bps']} & CI-lo>0) -> "
          f"{'PASS' if gb['pass'] else 'FAIL'}  (topq_n={gb['topq_n']})")
    print("-" * 72)
    print("horizons rho_winsor / topq_mean_bps:")
    for h in ["1100", "1005", "1035", "1545"]:
        hh = r["support_horizons"][h]
        print(f"  {h}: rho={_fmt(hh['rho_winsor'])} "
              f"topq_mean={_fmt(hh['topq_mean_signed_bps'])} (n={hh['n']})")
    print(f"R_paired rho={_fmt(r['support_R_paired_11']['rho_winsor'])}  "
          f"precross rho={_fmt(r['support_precross_11']['rho_winsor'])}  "
          f"o2a-sanity rho={_fmt(r['support_open_to_anchor_sanity']['rho_raw'])}")
    print("=" * 72)
    print(f"wrote {OUT_DIR / 'result.json'}")
    print(f"wrote {OUT_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()
