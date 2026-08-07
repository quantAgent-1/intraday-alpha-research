"""R2-A prong 0 -- off-exchange odd-lot retail-flow -> open-print intraday fade.

PRE-DECLARED DIAGNOSTIC. Spec frozen in research ledger row
`R2A-prong0-predeclaration` (ts 2026-07-23T17:43Z), declared BEFORE any
computation. This script implements that row verbatim; no gated definition,
threshold, or window is altered. Where the spec is silent on an implementation
detail the simplest faithful option is chosen and documented in summary.md
(Implementation notes) and here.

HYPOTHESIS (reversal, incremental to the gap): day t-1 off-exchange odd-lot
retail imbalance predicts a day-t open-print -> intraday REVERSAL that survives
controlling for the overnight gap (else it is M27-redundant).

STATE (gated):
  OLI_{t-1} = (buy_vol - sell_vol)/(buy_vol + sell_vol) over day t-1 prints with
  exchange=='D' AND size<100 AND price>0, RTH 09:30-16:00 ET only, signed by the
  quote rule vs the prevailing bbo1s mid (guarded searchsorted, completed-second,
  never wraps to a future quote), tick-rule fallback when price==mid (vs the
  previous odd-lot print price), carry-last sign on a further tie -- exactly the
  f1_prong0 signing machinery. Require >=30 SIGNED odd-lot prints on t-1 else the
  day is dropped (counted).

OUTCOME (gated):
  ret_t   = (exit_mid / open_t - 1) * 1e4
  open_t  = bars1d RAW open for session t (data/raw/sip/bars1d/{SYM}.parquet).
  exit_mid= last bbo1s mid with ts_ET <= 15:45:00 ET (require >= 15:40:00 else
            drop). mid = (bid+ask)/2 with bid>0 AND ask>bid.

CONTROLS (bars1d raw):
  gap_t     = (open_t / close_{t-1} - 1) * 1e4
  ret_{t-1} = (close_{t-1} / close_{t-2} - 1) * 1e4
  (t-1, t-2 are that name's prior SESSIONS from its own bars1d, not calendar days)

PANEL: 10 names = NVDA TSLA AMD MU GOOGL KLAC MRVL LRCX TXN AMAT. A name-day (t)
enters iff trades exist for t-1 AND bbo1s+bars1d legs exist for t; sessions
strictly < 2026-06-01 ET; early-close sessions dropped (last bbo1s quote of day t
< 15:45 ET). The only two gated drop guards are (i) the >=30 signed-print guard
on t-1 and (ii) the early-close guard on t; data-availability drops (missing
trades/bbo legs) and a missing exit are reported in the funnel but are not extra
scientific guards.

GATES (mechanical PASS/FAIL; the three-way label is a pre-declared field, not a
verdict):
  (a) INCREMENTAL INFO: within each name OLS-residualize BOTH OLI_{t-1} and ret_t
      on [1, gap_t, ret_{t-1}] (per-name intercepts and slopes); pool residuals
      across names; winsorize both pooled residual series at 1%/99%; Pearson rho.
      PASS iff rho <= -0.03 AND session-clustered bootstrap 95% CI-hi < 0.
  (b) MAGNITUDE: per-name top-quartile |OLI_{t-1}| (|OLI| >= that name's Q3);
      signed_fade = -sign(OLI_{t-1}) * ret_t RAW; pool. PASS iff mean >= +6.0 bps
      AND session-clustered bootstrap 95% CI-lo > 0. A 1/99-winsorized mean+CI is
      reported as non-gating robustness.

Bootstrap (both gates, fresh numpy default_rng(7) each): resample the SET of
distinct session dates with replacement, n_sessions draws/rep (a drawn date
brings ALL its names' rows, as many times as drawn), 2000 reps, percentile CI
(2.5/97.5). Gate (a) reuses the ORIGINAL pooled winsor bounds and the ORIGINAL
per-name residualization coefficients per rep (residuals + winsorization are
computed ONCE; reps resample the fixed winsorized residuals -- no refit).

ADJUDICATION (pre-declared, mechanical): pass_a, pass_b, and label = PASS if
both; KILL if (residual rho point >= 0) OR (top-quartile mean <= 0); else
PARK-UNDERPOWERED.

SUPPORTING (all non-gating): raw (unresidualized) winsorized rho + clustered CI;
horizons open->10:00 and open->11:00; megacap-5 vs semi-5 tier split; 4x4 table
of mean ret_t by (gap_t quartile x OLI_{t-1} quartile, per-name quartiles);
first-stage pooled rho(OLI_{t-1}, gap_t); per-name rows; coverage/sparsity.

REFUSAL GUARD (prevents partial-panel peeks): unless --selftest, the script
counts daily trade files per semi in [2024-01, 2026-05] and REFUSES to run
(nonzero exit) if any of KLAC/MRVL/LRCX/TXN/AMAT has fewer than 200 daily files.
Only --force-partial overrides it, with a loud non-canonical warning.

OUTPUT (real run only, not --selftest): research/experiments/R2A-prong0/{
result.json, summary.md}. Self-contained, seeded, ASCII-only. Touches no other
file.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import OrderedDict
from datetime import date as _date
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
REPO = Path(__file__).resolve().parents[1]
TRADES_DIR = REPO / "data" / "raw" / "sip" / "trades"
BBO_DIR = REPO / "data" / "raw" / "bbo1s"
BARS_DIR = REPO / "data" / "raw" / "sip" / "bars1d"
OUT_DIR = REPO / "research" / "experiments" / "R2A-prong0"

ET = ZoneInfo("America/New_York")

PANEL = ["NVDA", "TSLA", "AMD", "MU", "GOOGL",
         "KLAC", "MRVL", "LRCX", "TXN", "AMAT"]
MEGA = ["NVDA", "TSLA", "AMD", "MU", "GOOGL"]
SEMI = ["KLAC", "MRVL", "LRCX", "TXN", "AMAT"]
SEMI_SET = set(SEMI)

CAP_DATE = "2026-06-01"          # keep ET session date strictly before this
MIN_SIGNED = 30                  # >=30 signed odd-lot prints on t-1, else drop
MIN_RESID = 5                    # per-name rows needed to residualize (3 params+dof)
REFUSE_MIN_FILES = 200           # semi daily-file floor before a canonical run

BOOT_SEED = 7
BOOT_REPS = 2000
GATE_A_RHO = -0.03               # residual rho PASS threshold (<=)
GATE_B_BPS = 6.0                 # top-quartile signed-fade PASS threshold (>=)
WINSOR_LO_PCT = 1.0
WINSOR_HI_PCT = 99.0

# ET seconds-of-day boundaries.
RTH_OPEN_SEC = 9 * 3600 + 30 * 60           # 09:30:00
RTH_CLOSE_SEC = 16 * 3600                    # 16:00:00 (exclusive)
EXIT_MAIN_LO = 15 * 3600 + 40 * 60           # 15:40:00 (exit must be >= this)
EXIT_MAIN_HI = 15 * 3600 + 45 * 60           # 15:45:00 (last mid <= this)
EARLY_CLOSE_SEC = 15 * 3600 + 45 * 60        # last quote < this => early close

# Supporting horizons: label -> (required_lo, exit_hi). exit = last mid <= hi,
# required >= lo (within the prior 5 min).
SUP_HORIZONS: dict[str, tuple[int, int]] = {
    "1000": (9 * 3600 + 55 * 60, 10 * 3600),          # 09:55 .. 10:00
    "1100": (10 * 3600 + 55 * 60, 11 * 3600),          # 10:55 .. 11:00
}


def tier_of(sym: str) -> str:
    return "semi" if sym in SEMI_SET else "mega"


# --------------------------------------------------------------------------- #
# Time helpers
# --------------------------------------------------------------------------- #
def _sec_expr() -> pl.Expr:
    dt = pl.from_epoch(pl.col("ts"), time_unit="ns").dt.convert_time_zone(
        "America/New_York"
    )
    return (
        dt.dt.hour().cast(pl.Int32) * 3600
        + dt.dt.minute().cast(pl.Int32) * 60
        + dt.dt.second().cast(pl.Int32)
    )


def _date_expr() -> pl.Expr:
    return (
        pl.from_epoch(pl.col("ts"), time_unit="ns")
        .dt.convert_time_zone("America/New_York")
        .dt.strftime("%Y-%m-%d")
    )


# --------------------------------------------------------------------------- #
# Pure statistics
# --------------------------------------------------------------------------- #
def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.shape[0] < 3:
        return float("nan")
    xd = x - x.mean()
    yd = y - y.mean()
    denom = math.sqrt(float((xd * xd).sum()) * float((yd * yd).sum()))
    if denom == 0.0:
        return float("nan")
    return float((xd * yd).sum() / denom)


def _winsor_bounds(a: np.ndarray) -> tuple[float, float]:
    return (
        float(np.percentile(a, WINSOR_LO_PCT)),
        float(np.percentile(a, WINSOR_HI_PCT)),
    )


def residualize(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """OLS residual of y on design X (intercept included). Returns (resid, beta)."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ beta, beta


def _session_bootstrap_rho(
    dates: np.ndarray, xw: np.ndarray, yw: np.ndarray, seed: int, reps: int
) -> tuple[float, float]:
    """Session-clustered bootstrap CI (2.5/97.5) of Pearson rho on winsorized xy."""
    uniq = np.unique(dates)
    n = uniq.shape[0]
    if n == 0:
        return float("nan"), float("nan")
    idx_list = [np.nonzero(dates == d)[0] for d in uniq]
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
    if n == 0:
        return float("nan"), float("nan")
    idx_list = [np.nonzero(dates == d)[0] for d in uniq]
    rng = np.random.default_rng(seed)
    boot = np.empty(reps)
    for i in range(reps):
        draw = rng.integers(0, n, n)
        sel = np.concatenate([idx_list[j] for j in draw])
        boot[i] = float(v[sel].mean())
    return float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


# --------------------------------------------------------------------------- #
# Trade signing (f1_prong0 machinery)
# --------------------------------------------------------------------------- #
def _ffill_sign(sign: np.ndarray) -> np.ndarray:
    """Replace 0-signs with the most recent non-zero sign at or before them."""
    valid = sign != 0
    if not valid.any():
        return sign
    idx = np.where(valid, np.arange(sign.shape[0]), 0)
    np.maximum.accumulate(idx, out=idx)
    return sign[idx]


def sign_prints(
    t_ts: np.ndarray, t_px: np.ndarray, q_ts: np.ndarray, q_mid: np.ndarray
) -> np.ndarray:
    """Lee-Ready quote rule vs the prevailing completed-second mid, tick-rule
    fallback vs the previous print price, carry-last on a further tie.

    Exactly mirrors f1_prong0.flow_by_bucket: prevailing mid = last quote with
    q_ts <= t_ts (searchsorted right - 1, guarded >= 0, never a future quote);
    px>mid -> +1, px<mid -> -1; px==mid (or no prior quote) -> tick vs previous
    print; remaining ties carry the last non-zero sign forward.
    """
    n = t_ts.shape[0]
    if n == 0:
        return np.zeros(0, dtype=np.int64)
    mid = np.full(n, np.nan)
    if q_ts.shape[0] > 0:
        pos = np.searchsorted(q_ts, t_ts, side="right") - 1
        have = pos >= 0
        mid[have] = q_mid[pos[have]]
    sign = np.zeros(n, dtype=np.int64)
    valid = np.isfinite(mid)
    sign[valid & (t_px > mid)] = 1
    sign[valid & (t_px < mid)] = -1
    prev_px = np.empty(n)
    prev_px[0] = np.nan
    prev_px[1:] = t_px[:-1]
    tick = np.zeros(n, dtype=np.int64)
    tick[t_px > prev_px] = 1
    tick[t_px < prev_px] = -1
    need = sign == 0
    sign[need] = tick[need]
    return _ffill_sign(sign)


# --------------------------------------------------------------------------- #
# Per-symbol data loaders
# --------------------------------------------------------------------------- #
def load_bars1d(sym: str):
    """(dates[list[str]], open[np], close[np]) sorted by session, ET dates."""
    p = BARS_DIR / f"{sym}.parquet"
    if not p.exists():
        return None
    b = pl.read_parquet(p, columns=["ts", "open", "close"])
    b = b.with_columns(_date_expr().alias("_d")).sort("ts")
    return (
        b["_d"].to_list(),
        b["open"].to_numpy().astype(np.float64),
        b["close"].to_numpy().astype(np.float64),
    )


def load_trades_oddlot(sym: str, date_str: str):
    """(ts, price, size) of RTH off-exchange odd-lot prints on a session, sorted.

    None if the file is missing; empty arrays if the file has no such prints.
    """
    p = TRADES_DIR / sym / f"{date_str}.parquet"
    if not p.exists():
        return None
    tr = pl.read_parquet(p, columns=["ts", "price", "size", "exchange"])
    tr = tr.filter(
        (pl.col("exchange") == "D") & (pl.col("size") < 100) & (pl.col("price") > 0)
    )
    tr = tr.with_columns(_sec_expr().alias("_sec"))
    tr = tr.filter(
        (pl.col("_sec") >= RTH_OPEN_SEC) & (pl.col("_sec") < RTH_CLOSE_SEC)
    ).sort("ts")
    if tr.height == 0:
        return (np.zeros(0, dtype=np.int64), np.zeros(0), np.zeros(0))
    return (
        tr["ts"].to_numpy(),
        tr["price"].to_numpy().astype(np.float64),
        tr["size"].to_numpy().astype(np.float64),
    )


class BboCache:
    """Per-symbol bbo1s month loader with a small LRU (only month(t)/month(t-1)
    are ever live). Each day -> (ts, sec, mid) sorted, guarded bid>0 & ask>bid."""

    def __init__(self, sym: str, maxmonths: int = 3) -> None:
        self.dir = BBO_DIR / sym
        self.cache: "OrderedDict[str, dict]" = OrderedDict()
        self.maxmonths = maxmonths

    def _load_month(self, month: str) -> dict:
        p = self.dir / f"{month}.parquet"
        if not p.exists():
            return {}
        df = pl.read_parquet(p, columns=["ts", "bid", "ask"])
        df = df.filter((pl.col("bid") > 0) & (pl.col("ask") > pl.col("bid")))
        if df.height == 0:
            return {}
        df = df.with_columns(
            _sec_expr().alias("_sec"),
            _date_expr().alias("_d"),
            ((pl.col("bid") + pl.col("ask")) / 2.0).alias("_mid"),
        ).sort("ts")
        out: dict = {}
        for key, g in df.partition_by("_d", as_dict=True, maintain_order=True).items():
            d = key[0] if isinstance(key, tuple) else key
            out[d] = (
                g["ts"].to_numpy(),
                g["_sec"].to_numpy(),
                g["_mid"].to_numpy(),
            )
        return out

    def get_day(self, date_str: str):
        month = date_str[:7]
        if month not in self.cache:
            self.cache[month] = self._load_month(month)
        else:
            self.cache.move_to_end(month)
        while len(self.cache) > self.maxmonths:
            self.cache.popitem(last=False)
        return self.cache[month].get(date_str)


def exit_mid(sec: np.ndarray, mid: np.ndarray, hi: int, lo: int) -> float | None:
    """Last mid with sec <= hi, required sec >= lo (guarded searchsorted)."""
    j = int(np.searchsorted(sec, hi, side="right")) - 1
    if j >= 0 and sec[j] >= lo:
        return float(mid[j])
    return None


# --------------------------------------------------------------------------- #
# Symbol driver -> per-name-day records + drop funnel
# --------------------------------------------------------------------------- #
DROP_ORDER = ["no_trades_tm1", "no_bbo_tm1", "no_bbo_t", "early_close_t",
              "bars_missing", "few_odd_signs", "no_exit_t"]


def process_symbol(sym: str) -> tuple[list[dict], dict]:
    bars = load_bars1d(sym)
    if bars is None:
        return [], {"n_candidates": 0, "funnel": {k: 0 for k in DROP_ORDER},
                    "oddlot_counts": [], "n_sessions_bars": 0, "n_kept": 0}
    dates, opens, closes = bars
    n = len(dates)
    bbo = BboCache(sym)
    funnel = {k: 0 for k in DROP_ORDER}
    oddlot_counts: list[int] = []
    records: list[dict] = []
    n_candidates = 0

    for i in range(2, n):
        date_t = dates[i]
        if date_t >= CAP_DATE:
            continue
        date_tm1 = dates[i - 1]
        date_tm2 = dates[i - 2]
        n_candidates += 1

        tr = load_trades_oddlot(sym, date_tm1)
        if tr is None or tr[0].shape[0] == 0:
            funnel["no_trades_tm1"] += 1
            continue
        oddlot_counts.append(int(tr[0].shape[0]))

        bday_tm1 = bbo.get_day(date_tm1)
        if bday_tm1 is None:
            funnel["no_bbo_tm1"] += 1
            continue
        bday_t = bbo.get_day(date_t)
        if bday_t is None:
            funnel["no_bbo_t"] += 1
            continue
        q_ts_t, q_sec_t, q_mid_t = bday_t
        if int(q_sec_t[-1]) < EARLY_CLOSE_SEC:
            funnel["early_close_t"] += 1
            continue

        open_t = opens[i]
        close_tm1 = closes[i - 1]
        close_tm2 = closes[i - 2]
        if not (
            np.isfinite(open_t) and open_t > 0
            and np.isfinite(close_tm1) and close_tm1 > 0
            and np.isfinite(close_tm2) and close_tm2 > 0
        ):
            funnel["bars_missing"] += 1
            continue

        t_ts, t_px, t_sz = tr
        q_ts_tm1, _, q_mid_tm1 = bday_tm1
        sign = sign_prints(t_ts, t_px, q_ts_tm1, q_mid_tm1)
        n_signed = int((sign != 0).sum())
        if n_signed < MIN_SIGNED:
            funnel["few_odd_signs"] += 1
            continue
        buy = float(t_sz[sign > 0].sum())
        sell = float(t_sz[sign < 0].sum())
        if buy + sell <= 0:
            funnel["few_odd_signs"] += 1
            continue
        oli = (buy - sell) / (buy + sell)

        ex_main = exit_mid(q_sec_t, q_mid_t, EXIT_MAIN_HI, EXIT_MAIN_LO)
        if ex_main is None:
            funnel["no_exit_t"] += 1
            continue
        ret_t = (ex_main / open_t - 1.0) * 1e4
        gap_t = (open_t / close_tm1 - 1.0) * 1e4
        ret_tm1 = (close_tm1 / close_tm2 - 1.0) * 1e4

        rec = {
            "sym": sym, "tier": tier_of(sym), "date": date_t, "date_tm1": date_tm1,
            "oli": oli, "ret": ret_t, "gap": gap_t, "ret_prev": ret_tm1,
            "n_signed": n_signed, "n_oddlot": int(t_ts.shape[0]),
        }
        for label, (lo, hi) in SUP_HORIZONS.items():
            em = exit_mid(q_sec_t, q_mid_t, hi, lo)
            rec[f"ret_{label}"] = (em / open_t - 1.0) * 1e4 if em is not None else None
        records.append(rec)

    return records, {
        "n_candidates": n_candidates, "funnel": funnel,
        "oddlot_counts": oddlot_counts, "n_sessions_bars": n,
        "n_kept": len(records),
    }


# --------------------------------------------------------------------------- #
# Gate statistics (reusable for main / horizons / tiers)
# --------------------------------------------------------------------------- #
def _by_name(recs: list[dict], ret_key: str) -> "OrderedDict[str, list[dict]]":
    out: "OrderedDict[str, list[dict]]" = OrderedDict()
    for r in recs:
        y = r.get(ret_key)
        if y is None:
            continue
        if not (
            np.isfinite(r["oli"]) and np.isfinite(y)
            and np.isfinite(r["gap"]) and np.isfinite(r["ret_prev"])
        ):
            continue
        out.setdefault(r["sym"], []).append(r)
    return out


def gate_a_stats(
    recs: list[dict], ret_key: str, seed: int = BOOT_SEED, reps: int = BOOT_REPS
) -> dict:
    """Per-name residualize OLI and ret_key on [1, gap, ret_prev]; pool; winsor
    1/99; rho + session-clustered CI. Reuses fixed residuals+bounds in the boot."""
    by = _by_name(recs, ret_key)
    ro_parts, rt_parts, date_parts = [], [], []
    per_name: dict[str, dict] = {}
    skipped: dict[str, int] = {}
    for name, rows in by.items():
        nn = len(rows)
        if nn < MIN_RESID:
            skipped[name] = nn
            continue
        oli = np.array([r["oli"] for r in rows], dtype=np.float64)
        y = np.array([r[ret_key] for r in rows], dtype=np.float64)
        gap = np.array([r["gap"] for r in rows], dtype=np.float64)
        rp = np.array([r["ret_prev"] for r in rows], dtype=np.float64)
        X = np.column_stack([np.ones(nn), gap, rp])
        ro, _ = residualize(oli, X)
        rt, _ = residualize(y, X)
        ro_parts.append(ro)
        rt_parts.append(rt)
        date_parts.append(np.array([r["date"] for r in rows]))
        per_name[name] = {
            "n": nn,
            "raw_rho": _pearson(oli, y),
            "resid_rho": _pearson(ro, rt),
        }
    if not ro_parts:
        return {"rho": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"),
                "n": 0, "n_sessions": 0, "per_name": per_name, "skipped": skipped,
                "winsor_oli": [float("nan")] * 2, "winsor_ret": [float("nan")] * 2}
    ro = np.concatenate(ro_parts)
    rt = np.concatenate(rt_parts)
    dts = np.concatenate(date_parts)
    rlo, rhi = _winsor_bounds(ro)
    tlo, thi = _winsor_bounds(rt)
    rw = np.clip(ro, rlo, rhi)
    tw = np.clip(rt, tlo, thi)
    rho = _pearson(rw, tw)
    ci_lo, ci_hi = _session_bootstrap_rho(dts, rw, tw, seed, reps)
    return {"rho": rho, "ci_lo": ci_lo, "ci_hi": ci_hi, "n": int(ro.shape[0]),
            "n_sessions": int(np.unique(dts).shape[0]), "per_name": per_name,
            "skipped": skipped, "winsor_oli": [rlo, rhi], "winsor_ret": [tlo, thi]}


def gate_b_stats(
    recs: list[dict], ret_key: str, seed: int = BOOT_SEED, reps: int = BOOT_REPS,
    winsor: bool = False,
) -> dict:
    """Per-name top-quartile |OLI| signed_fade = -sign(OLI)*ret_key; pool; mean +
    session-clustered CI. Names with Q3(|OLI|)==0 are dropped (counted)."""
    by = _by_name(recs, ret_key)
    signed: list[float] = []
    sdates: list[str] = []
    dropped: list[str] = []
    q3_by: dict[str, float] = {}
    per_name: dict[str, dict] = {}
    for name, rows in by.items():
        absoli = np.array([abs(r["oli"]) for r in rows], dtype=np.float64)
        q3 = float(np.percentile(absoli, 75))
        q3_by[name] = q3
        if q3 == 0.0:
            dropped.append(name)
            per_name[name] = {"topq_n": 0, "topq_mean": float("nan"), "q3": q3}
            continue
        sub = [-np.sign(r["oli"]) * r[ret_key] for r in rows if abs(r["oli"]) >= q3]
        sub_d = [r["date"] for r in rows if abs(r["oli"]) >= q3]
        signed.extend(sub)
        sdates.extend(sub_d)
        per_name[name] = {
            "topq_n": len(sub),
            "topq_mean": float(np.mean(sub)) if sub else float("nan"),
            "q3": q3,
        }
    arr = np.array(signed, dtype=np.float64)
    darr = np.array(sdates)
    wb = [float("nan"), float("nan")]
    if winsor and arr.shape[0]:
        lo, hi = _winsor_bounds(arr)
        wb = [lo, hi]
        arr = np.clip(arr, lo, hi)
    nb = int(arr.shape[0])
    mean = float(arr.mean()) if nb else float("nan")
    if nb:
        ci_lo, ci_hi = _session_bootstrap_mean(darr, arr, seed, reps)
    else:
        ci_lo = ci_hi = float("nan")
    return {"mean": mean, "ci_lo": ci_lo, "ci_hi": ci_hi, "n": nb,
            "dropped_q3zero": dropped, "q3_by_name": q3_by, "per_name": per_name,
            "winsor_bounds": wb, "n_sessions": int(np.unique(darr).shape[0]) if nb else 0}


# --------------------------------------------------------------------------- #
# Adjudication predicates (pure)
# --------------------------------------------------------------------------- #
def pass_a_rule(rho: float, ci_hi: float) -> bool:
    return bool(
        np.isfinite(rho) and rho <= GATE_A_RHO and np.isfinite(ci_hi) and ci_hi < 0.0
    )


def pass_b_rule(mean: float, ci_lo: float) -> bool:
    return bool(
        np.isfinite(mean) and mean >= GATE_B_BPS and np.isfinite(ci_lo) and ci_lo > 0.0
    )


def adjudicate(pass_a: bool, pass_b: bool, rho: float, mean: float) -> str:
    if pass_a and pass_b:
        return "PASS"
    if (np.isfinite(rho) and rho >= 0.0) or (np.isfinite(mean) and mean <= 0.0):
        return "KILL"
    return "PARK-UNDERPOWERED"


# --------------------------------------------------------------------------- #
# Supporting: 4x4 table and first-stage
# --------------------------------------------------------------------------- #
def table_4x4(recs: list[dict]) -> dict:
    """mean ret_t per (gap-quartile x OLI-quartile) cell, per-name quartile bins,
    pooled cell means + n. Bins 0..3 via searchsorted on each name's [25,50,75]."""
    cells: dict[str, list[float]] = {
        f"{gi}_{oi}": [] for gi in range(4) for oi in range(4)
    }
    by = _by_name(recs, "ret")
    for _, rows in by.items():
        gap = np.array([r["gap"] for r in rows], dtype=np.float64)
        oli = np.array([r["oli"] for r in rows], dtype=np.float64)
        ret = np.array([r["ret"] for r in rows], dtype=np.float64)
        gq = np.percentile(gap, [25, 50, 75])
        oq = np.percentile(oli, [25, 50, 75])
        gbin = np.searchsorted(gq, gap, side="right")
        obin = np.searchsorted(oq, oli, side="right")
        for k in range(len(rows)):
            cells[f"{int(gbin[k])}_{int(obin[k])}"].append(float(ret[k]))
    return {
        key: {"mean": float(np.mean(v)) if v else float("nan"), "n": len(v)}
        for key, v in cells.items()
    }


def first_stage_rho(recs: list[dict]) -> tuple[float, int]:
    by = _by_name(recs, "ret")
    oli = np.array([r["oli"] for rows in by.values() for r in rows], dtype=np.float64)
    gap = np.array([r["gap"] for rows in by.values() for r in rows], dtype=np.float64)
    return _pearson(oli, gap), int(oli.shape[0])


def raw_rho_winsor(recs: list[dict], ret_key: str, seed: int, reps: int) -> dict:
    """Pooled raw (unresidualized) winsorized rho(OLI, ret_key) + clustered CI."""
    by = _by_name(recs, ret_key)
    oli = np.array([r["oli"] for rows in by.values() for r in rows], dtype=np.float64)
    ret = np.array([r[ret_key] for rows in by.values() for r in rows], dtype=np.float64)
    dts = np.array([r["date"] for rows in by.values() for r in rows])
    if oli.shape[0] < 3:
        return {"rho": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"),
                "n": int(oli.shape[0])}
    olo, ohi = _winsor_bounds(oli)
    rlo, rhi = _winsor_bounds(ret)
    ow = np.clip(oli, olo, ohi)
    rw = np.clip(ret, rlo, rhi)
    ci_lo, ci_hi = _session_bootstrap_rho(dts, ow, rw, seed, reps)
    return {"rho": _pearson(ow, rw), "ci_lo": ci_lo, "ci_hi": ci_hi,
            "n": int(oli.shape[0]), "n_sessions": int(np.unique(dts).shape[0])}


# --------------------------------------------------------------------------- #
# Refusal guard
# --------------------------------------------------------------------------- #
def semi_file_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for sym in SEMI:
        d = TRADES_DIR / sym
        c = 0
        if d.exists():
            for f in d.glob("*.parquet"):
                m = f.stem[:7]
                if "2024-01" <= m <= "2026-05":
                    c += 1
        counts[sym] = c
    return counts


# --------------------------------------------------------------------------- #
# Main (real run)
# --------------------------------------------------------------------------- #
def run_real(force_partial: bool) -> int:
    counts = semi_file_counts()
    short = {s: c for s, c in counts.items() if c < REFUSE_MIN_FILES}
    if short and not force_partial:
        print("REFUSING to run (partial-panel guard):")
        for s in SEMI:
            print(f"  {s}: {counts[s]} daily trade files in [2024-01, 2026-05]"
                  f"{'  << below floor' if s in short else ''}")
        print(f"Floor is {REFUSE_MIN_FILES} files per semi. Run the backfill first")
        print("(scripts/backfill_trades_semis.py), or pass --force-partial to run a")
        print("NON-CANONICAL partial panel.")
        return 3
    if short and force_partial:
        print("!" * 70)
        print("WARNING: --force-partial -- NON-CANONICAL RUN on a partial panel.")
        print(f"  below-floor semis: {short}  (floor {REFUSE_MIN_FILES})")
        print("  Results are NOT the pre-declared single-run adjudication.")
        print("!" * 70)

    all_recs: list[dict] = []
    diags: dict[str, dict] = {}
    for sym in PANEL:
        recs, diag = process_symbol(sym)
        all_recs.extend(recs)
        diags[sym] = diag

    ga = gate_a_stats(all_recs, "ret")
    gb = gate_b_stats(all_recs, "ret")
    gb_w = gate_b_stats(all_recs, "ret", winsor=True)
    pa = pass_a_rule(ga["rho"], ga["ci_hi"])
    pb = pass_b_rule(gb["mean"], gb["ci_lo"])
    label = adjudicate(pa, pb, ga["rho"], gb["mean"])

    raw = raw_rho_winsor(all_recs, "ret", BOOT_SEED, BOOT_REPS)
    horizons = {}
    for h in SUP_HORIZONS:
        key = f"ret_{h}"
        gah = gate_a_stats(all_recs, key)
        gbh = gate_b_stats(all_recs, key)
        horizons[h] = {
            "gate_a": {k: gah[k] for k in ("rho", "ci_lo", "ci_hi", "n", "n_sessions")},
            "gate_b": {k: gbh[k] for k in ("mean", "ci_lo", "ci_hi", "n")},
        }
    tiers = {}
    for tname, members in (("mega", set(MEGA)), ("semi", SEMI_SET)):
        sub = [r for r in all_recs if r["sym"] in members]
        gat = gate_a_stats(sub, "ret")
        gbt = gate_b_stats(sub, "ret")
        tiers[tname] = {
            "gate_a": {k: gat[k] for k in ("rho", "ci_lo", "ci_hi", "n", "n_sessions")},
            "gate_b": {k: gbt[k] for k in ("mean", "ci_lo", "ci_hi", "n")},
        }
    tbl = table_4x4(all_recs)
    fs_rho, fs_n = first_stage_rho(all_recs)

    # per-name rows (raw rho, resid rho, top-q)
    per_name: dict[str, dict] = {}
    for sym in PANEL:
        a = ga["per_name"].get(sym, {})
        b = gb["per_name"].get(sym, {})
        per_name[sym] = {
            "n_kept": diags[sym]["n_kept"],
            "n_resid": a.get("n", 0),
            "raw_rho": a.get("raw_rho", float("nan")),
            "resid_rho": a.get("resid_rho", float("nan")),
            "topq_n": b.get("topq_n", 0),
            "topq_mean_signed_fade": b.get("topq_mean", float("nan")),
        }

    # coverage / sparsity
    coverage: dict[str, dict] = {}
    for sym in PANEL:
        d = diags[sym]
        oc = np.array(d["oddlot_counts"], dtype=np.float64)
        recs_s = [r for r in all_recs if r["sym"] == sym]
        oli_s = np.array([r["oli"] for r in recs_s], dtype=np.float64)
        coverage[sym] = {
            "n_candidates": d["n_candidates"],
            "n_kept": d["n_kept"],
            "funnel": d["funnel"],
            "oddlot_prints_tm1": {
                "p25": float(np.percentile(oc, 25)) if oc.size else float("nan"),
                "p50": float(np.percentile(oc, 50)) if oc.size else float("nan"),
                "p75": float(np.percentile(oc, 75)) if oc.size else float("nan"),
            },
            "oli_dist": {
                "p10": float(np.percentile(oli_s, 10)) if oli_s.size else float("nan"),
                "p50": float(np.percentile(oli_s, 50)) if oli_s.size else float("nan"),
                "p90": float(np.percentile(oli_s, 90)) if oli_s.size else float("nan"),
            },
        }

    result = {
        "spec": "R2A-prong0-predeclaration",
        "spec_ts": "2026-07-23T17:43Z",
        "note": "PRE-DECLARED DIAGNOSTIC. Off-exchange odd-lot OLI_{t-1} vs raw "
                "open->intraday ret_t, incremental to the overnight gap. pass_a, "
                "pass_b and label are mechanical.",
        "non_canonical_partial_run": bool(short and force_partial),
        "config": {
            "panel": PANEL, "megacap5": MEGA, "semi5": SEMI,
            "cap_date_exclusive": CAP_DATE, "min_signed_prints": MIN_SIGNED,
            "min_resid_rows": MIN_RESID, "boot_seed": BOOT_SEED,
            "boot_reps": BOOT_REPS, "winsor_pct": [WINSOR_LO_PCT, WINSOR_HI_PCT],
            "gate_a_rho_max": GATE_A_RHO, "gate_b_bps_min": GATE_B_BPS,
            "windows_et_sec": {
                "rth": [RTH_OPEN_SEC, RTH_CLOSE_SEC],
                "exit_main": [EXIT_MAIN_LO, EXIT_MAIN_HI],
                "early_close_lt": EARLY_CLOSE_SEC,
                "sup_horizons": SUP_HORIZONS,
            },
            "semi_file_counts": counts,
        },
        "analysis_set": {
            "n_name_days": ga["n"], "n_sessions": ga["n_sessions"],
            "winsor_bounds_resid_oli": ga["winsor_oli"],
            "winsor_bounds_resid_ret": ga["winsor_ret"],
            "names_skipped_lt_min_resid": ga["skipped"],
        },
        "adjudication": {"pass_a": pa, "pass_b": pb, "label": label},
        "gate_a_incremental_info": {
            "rho": ga["rho"], "ci95_lo": ga["ci_lo"], "ci95_hi": ga["ci_hi"],
            "n": ga["n"], "n_sessions": ga["n_sessions"],
            "threshold_rho_max": GATE_A_RHO, "pass": pa,
        },
        "gate_b_magnitude": {
            "mean_signed_fade_bps": gb["mean"], "ci95_lo": gb["ci_lo"],
            "ci95_hi": gb["ci_hi"], "topq_n": gb["n"],
            "threshold_bps_min": GATE_B_BPS, "pass": pb,
            "names_dropped_q3zero": gb["dropped_q3zero"],
            "winsor_robustness": {
                "mean_signed_fade_bps": gb_w["mean"], "ci95_lo": gb_w["ci_lo"],
                "ci95_hi": gb_w["ci_hi"], "winsor_bounds": gb_w["winsor_bounds"],
            },
        },
        "support_raw_rho": raw,
        "support_horizons": horizons,
        "support_tier_split": tiers,
        "support_gap_x_oli_4x4": tbl,
        "support_first_stage_rho_oli_gap": {"rho": fs_rho, "n": fs_n},
        "support_per_name": per_name,
        "support_coverage": coverage,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(
        json.dumps(_clean(result), indent=2), encoding="utf-8"
    )
    _write_summary(OUT_DIR / "summary.md", result)
    _print_console(result)
    return 0


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
    cfg = r["config"]
    aset = r["analysis_set"]
    adj = r["adjudication"]
    L.append("# R2-A prong 0 -- off-exchange odd-lot -> open-print intraday fade")
    L.append("")
    L.append("PRE-DECLARED DIAGNOSTIC (ledger row `R2A-prong0-predeclaration`, "
             "ts 2026-07-23T17:43Z). pass_a / pass_b / label below are mechanical "
             "field values, not a verdict.")
    if r["non_canonical_partial_run"]:
        L.append("")
        L.append("> NON-CANONICAL PARTIAL RUN (--force-partial): not the "
                 "pre-declared single full-panel adjudication.")
    L.append("")
    L.append(f"Panel ({len(cfg['panel'])}): {', '.join(cfg['panel'])}  |  cap ts < "
             f"{cfg['cap_date_exclusive']} ET")
    L.append(f"Analysis set: n={aset['n_name_days']} name-days over "
             f"{aset['n_sessions']} sessions.")
    if aset["names_skipped_lt_min_resid"]:
        L.append(f"Names skipped (< {cfg['min_resid_rows']} kept rows): "
                 f"{aset['names_skipped_lt_min_resid']}")
    L.append("")

    L.append("## Adjudication (mechanical)")
    L.append("")
    L.append(f"pass_a = {adj['pass_a']}  |  pass_b = {adj['pass_b']}  |  "
             f"label = {adj['label']}")
    L.append("")

    ga = r["gate_a_incremental_info"]
    L.append("## GATE (a) INCREMENTAL INFO -- pooled residual rho(OLI_{t-1}, ret_t)")
    L.append("")
    L.append(f"rho = {_fmt(ga['rho'])}  |  95% CI (session-clustered) "
             f"[{_fmt(ga['ci95_lo'])}, {_fmt(ga['ci95_hi'])}]  |  "
             f"gate rho<={ga['threshold_rho_max']} AND CI-hi<0  ->  pass_a="
             f"{ga['pass']}")
    L.append(f"(n={ga['n']} name-days, {ga['n_sessions']} sessions; residualized "
             f"per-name on [1, gap_t, ret_(t-1)]; seed {cfg['boot_seed']}, "
             f"{cfg['boot_reps']} reps)")
    L.append("")

    gb = r["gate_b_magnitude"]
    wr = gb["winsor_robustness"]
    L.append("## GATE (b) MAGNITUDE -- per-name top-quartile |OLI| signed fade")
    L.append("")
    L.append(f"signed_fade = -sign(OLI_(t-1)) * ret_t (RAW)")
    L.append(f"mean = {_fmt(gb['mean_signed_fade_bps'])} bps  |  95% CI "
             f"[{_fmt(gb['ci95_lo'])}, {_fmt(gb['ci95_hi'])}]  |  gate mean>="
             f"{gb['threshold_bps_min']} AND CI-lo>0  ->  pass_b={gb['pass']}")
    L.append(f"(top-quartile n={gb['topq_n']}; names dropped Q3==0: "
             f"{gb['names_dropped_q3zero'] or 'none'})")
    L.append(f"non-gating winsor(1/99) mean = {_fmt(wr['mean_signed_fade_bps'])} "
             f"bps  CI [{_fmt(wr['ci95_lo'])}, {_fmt(wr['ci95_hi'])}]")
    L.append("")

    raw = r["support_raw_rho"]
    L.append("## Support -- raw (unresidualized) winsorized rho(OLI, ret_t)")
    L.append("")
    L.append(f"rho = {_fmt(raw['rho'])}  CI [{_fmt(raw['ci_lo'])}, "
             f"{_fmt(raw['ci_hi'])}]  (n={raw['n']})")
    L.append("")

    L.append("## Support -- horizons (open -> exit)")
    L.append("")
    L.append("| horizon | ga_rho | ga_ci_lo | ga_ci_hi | ga_n | gb_mean | gb_ci_lo "
             "| gb_ci_hi | gb_n |")
    L.append("|---------|--------|----------|----------|------|---------|----------"
             "|----------|------|")
    rows_h = [("1545(main)", ga["rho"], ga["ci95_lo"], ga["ci95_hi"], ga["n"],
               gb["mean_signed_fade_bps"], gb["ci95_lo"], gb["ci95_hi"], gb["topq_n"])]
    for h in SUP_HORIZONS:
        hh = r["support_horizons"][h]
        a = hh["gate_a"]
        b = hh["gate_b"]
        rows_h.append((h, a["rho"], a["ci_lo"], a["ci_hi"], a["n"],
                       b["mean"], b["ci_lo"], b["ci_hi"], b["n"]))
    for nm, ar, alo, ahi, an, bm, blo, bhi, bn in rows_h:
        L.append(f"| {nm} | {_fmt(ar)} | {_fmt(alo)} | {_fmt(ahi)} | {an} | "
                 f"{_fmt(bm)} | {_fmt(blo)} | {_fmt(bhi)} | {bn} |")
    L.append("")

    L.append("## Support -- tier split (megacap-5 vs semi-5)")
    L.append("")
    L.append("| tier | ga_rho | ga_ci_lo | ga_ci_hi | ga_n | gb_mean | gb_ci_lo | "
             "gb_ci_hi | gb_n |")
    L.append("|------|--------|----------|----------|------|---------|----------|"
             "----------|------|")
    for tname in ("mega", "semi"):
        t = r["support_tier_split"][tname]
        a = t["gate_a"]
        b = t["gate_b"]
        L.append(f"| {tname} | {_fmt(a['rho'])} | {_fmt(a['ci_lo'])} | "
                 f"{_fmt(a['ci_hi'])} | {a['n']} | {_fmt(b['mean'])} | "
                 f"{_fmt(b['ci_lo'])} | {_fmt(b['ci_hi'])} | {b['n']} |")
    L.append("")

    L.append("## Support -- mean ret_t (bps) by gap-quartile (rows) x OLI-quartile "
             "(cols), per-name quartiles")
    L.append("")
    L.append("| gap\\OLI | Q1 | Q2 | Q3 | Q4 |")
    L.append("|---------|----|----|----|----|")
    tbl = r["support_gap_x_oli_4x4"]
    for gi in range(4):
        cells = []
        for oi in range(4):
            c = tbl[f"{gi}_{oi}"]
            cells.append(f"{_fmt(c['mean'], 2)} (n={c['n']})")
        L.append(f"| gapQ{gi + 1} | " + " | ".join(cells) + " |")
    fs = r["support_first_stage_rho_oli_gap"]
    L.append("")
    L.append(f"first-stage pooled rho(OLI_(t-1), gap_t) = {_fmt(fs['rho'])} "
             f"(n={fs['n']})")
    L.append("")

    L.append("## Support -- per-name")
    L.append("")
    L.append("| name | tier | n_kept | n_resid | raw_rho | resid_rho | topq_n | "
             "topq_mean_fade_bps |")
    L.append("|------|------|--------|---------|---------|-----------|--------|"
             "--------------------|")
    for sym in cfg["panel"]:
        pn = r["support_per_name"][sym]
        L.append(f"| {sym} | {tier_of(sym)} | {pn['n_kept']} | {pn['n_resid']} | "
                 f"{_fmt(pn['raw_rho'])} | {_fmt(pn['resid_rho'])} | {pn['topq_n']} "
                 f"| {_fmt(pn['topq_mean_signed_fade'], 2)} |")
    L.append("")

    L.append("## Support -- coverage / sparsity")
    L.append("")
    L.append("| name | cand | kept | oddlot_p50 | OLI_p10 | OLI_p50 | OLI_p90 |")
    L.append("|------|------|------|------------|---------|---------|---------|")
    for sym in cfg["panel"]:
        cv = r["support_coverage"][sym]
        L.append(f"| {sym} | {cv['n_candidates']} | {cv['n_kept']} | "
                 f"{_fmt(cv['oddlot_prints_tm1']['p50'], 0)} | "
                 f"{_fmt(cv['oli_dist']['p10'], 3)} | "
                 f"{_fmt(cv['oli_dist']['p50'], 3)} | "
                 f"{_fmt(cv['oli_dist']['p90'], 3)} |")
    L.append("")
    L.append("### Drop funnel (first-failing guard; order: " +
             ", ".join(DROP_ORDER) + ")")
    L.append("")
    L.append("| name | " + " | ".join(DROP_ORDER) + " |")
    L.append("|------|" + "|".join(["------"] * len(DROP_ORDER)) + "|")
    for sym in cfg["panel"]:
        f = r["support_coverage"][sym]["funnel"]
        L.append(f"| {sym} | " + " | ".join(str(f[k]) for k in DROP_ORDER) + " |")
    L.append("")

    L.append("## Implementation notes (faithful-simplest choices)")
    L.append("")
    L.append(
        "1. Signing reuses the f1_prong0 machinery verbatim (sign_prints): "
        "prevailing mid = last bbo1s quote (bid>0 AND ask>bid) with ts<=trade ts "
        "(searchsorted right-1, guarded, completed-second, never a future quote); "
        "px>mid=+1, px<mid=-1; px==mid or no-prior-quote -> tick vs the previous "
        "ODD-LOT print price; remaining ties carry the last non-zero sign. The "
        "'previous print' is the previous row of the t-1 off-exchange odd-lot "
        "subset (the gated print universe), sorted by ts. >=30 SIGNED prints "
        "(sign!=0) are required. "
        "2. bars1d RAW open/close columns are the price anchors (this lake is the "
        "raw refetch; column names verified as 'open'/'close'). Session t-1/t-2 "
        "are that name's prior bars1d SESSIONS (rows), not calendar days; ET "
        "session date = bars1d ts converted to America/New_York. "
        "3. bbo1s carries extended hours; the early-close guard (last valid "
        "two-sided quote of day t < 15:45 ET) and all exit windows use ET "
        "seconds-of-day via searchsorted on each session's monotone sec array. "
        "exit_mid = last mid <= 15:45, required >= 15:40 (else drop). "
        "4. A name-day enters iff trades[t-1], bbo[t], bars1d[t] exist; bbo[t-1] "
        "is also required to quote-sign (a day with no valid t-1 quotes is dropped "
        "as no_bbo_tm1 rather than signed purely by tick rule). Only the two "
        "stated scientific guards (>=30 signed prints on t-1; early-close on t) "
        "gate the panel; the other funnel rows are data-availability / missing-exit "
        "attributions. "
        "5. GATE (a): per-name OLS (numpy lstsq) of OLI and ret on [1, gap, "
        "ret_prev]; residuals pooled; both pooled residual series winsorized at "
        "pooled 1/99 (numpy percentile, linear); Pearson rho. A name with < "
        f"{MIN_RESID} kept rows is skipped from (a) (counted). The bootstrap "
        "resamples the FIXED winsorized residuals by session -- residuals and "
        "winsor bounds are computed once and reused (no per-rep refit). "
        "6. GATE (b): per-name Q3 of |OLI| over that name's kept sample; "
        "top-quartile = |OLI| >= Q3; signed_fade = -sign(OLI)*ret RAW; a name with "
        "Q3==0 is dropped (counted). Winsor(1/99) mean is reported non-gating. "
        "7. Bootstrap = fresh numpy default_rng(7) per gate; n_sessions draws of "
        "distinct ET session dates with replacement, each drawn date contributing "
        "all its rows (repeats included); 2000 reps; 2.5/97.5 percentile CI. "
        "8. Supporting horizons refit the per-name residualization on each "
        "horizon's own kept subset (rows with a valid exit for that horizon). Tier "
        "splits reuse the identical per-name residualization (a name's regression "
        "is independent of the pool) and winsorize within the tier. The 4x4 table "
        "bins each name-day by that name's own gap and OLI quartiles "
        "(searchsorted, ties to the upper bin); cells are pooled across names."
    )
    L.append("")
    path.write_text("\n".join(L), encoding="utf-8")


def _print_console(r: dict) -> None:
    adj = r["adjudication"]
    ga = r["gate_a_incremental_info"]
    gb = r["gate_b_magnitude"]
    aset = r["analysis_set"]
    print("=" * 72)
    print("R2-A PRONG 0 -- ODD-LOT -> OPEN-PRINT FADE (PRE-DECLARED DIAGNOSTIC)")
    print("=" * 72)
    if r["non_canonical_partial_run"]:
        print("*** NON-CANONICAL PARTIAL RUN (--force-partial) ***")
    print(f"panel {len(r['config']['panel'])} names; analysis set n="
          f"{aset['n_name_days']} name-days, {aset['n_sessions']} sessions")
    print("-" * 72)
    print(f"GATE(a) resid rho = {_fmt(ga['rho'])}  "
          f"CI[{_fmt(ga['ci95_lo'])},{_fmt(ga['ci95_hi'])}]  "
          f"(<= {ga['threshold_rho_max']} & CI-hi<0) -> pass_a={ga['pass']}")
    print(f"GATE(b) mean fade = {_fmt(gb['mean_signed_fade_bps'])} bps  "
          f"CI[{_fmt(gb['ci95_lo'])},{_fmt(gb['ci95_hi'])}]  "
          f"(>= {gb['threshold_bps_min']} & CI-lo>0) -> pass_b={gb['pass']}  "
          f"(topq_n={gb['topq_n']})")
    print(f"LABEL (mechanical): {adj['label']}")
    print("-" * 72)
    print(f"raw rho = {_fmt(r['support_raw_rho']['rho'])}   "
          f"first-stage rho(OLI,gap) = "
          f"{_fmt(r['support_first_stage_rho_oli_gap']['rho'])}")
    print("=" * 72)
    print(f"wrote {OUT_DIR / 'result.json'}")
    print(f"wrote {OUT_DIR / 'summary.md'}")


# --------------------------------------------------------------------------- #
# Self-test (synthetic only; no file writes)
# --------------------------------------------------------------------------- #
def _fake_dates(n: int) -> list[str]:
    out: list[str] = []
    d = _date(2024, 1, 2)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _synth_panel(n_sessions: int = 160):
    """3 names x n_sessions sharing dates. Planted: OLI=gap+u; ret=S*(beta*gap +
    delta*u + eps). beta<0 => raw rho negative (fade positive); delta<0 => planted
    NEGATIVE residual relationship; gap channel is what residualization removes."""
    rng = np.random.default_rng(20260724)
    dates = _fake_dates(n_sessions)
    names = ["FAKEA", "FAKEB", "FAKEC"]
    beta, delta, S = -1.0, -0.22, 25.0
    recs: list[dict] = []
    for name in names:
        tier = "mega" if name == "FAKEA" else "semi"
        for dt in dates:
            gap = float(rng.normal())
            rp = float(rng.normal())
            u = float(rng.normal())
            eps = float(rng.normal())
            oli = gap + u
            ret = S * (beta * gap + delta * u + eps)
            recs.append({
                "sym": name, "tier": tier, "date": dt, "date_tm1": dt,
                "oli": oli, "ret": ret, "gap": gap, "ret_prev": rp,
                "ret_1000": ret * 0.5, "ret_1100": ret * 0.8,
                "n_signed": 100, "n_oddlot": 200,
            })
    return recs


def selftest() -> int:
    results: list[tuple[str, bool, str]] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        results.append((name, bool(cond), detail))

    # --- (0) signing cases: constant mid=100; 7 prints covering all 4 rules ---
    q_ts = np.array([0], dtype=np.int64)
    q_mid = np.array([100.0])
    t_ts = np.array([1, 2, 3, 4, 5, 6, 7], dtype=np.int64)
    #        above  below  at-mid    at-mid   above  at-mid    at-mid
    #        buy    sell   tickUp+1  tie->+1  buy    tickDn-1  tie->-1
    t_px = np.array([100.5, 99.5, 100.0, 100.0, 100.5, 100.0, 100.0])
    got = sign_prints(t_ts, t_px, q_ts, q_mid)
    exp = np.array([1, -1, 1, 1, 1, -1, -1])
    check("sign_above_mid_buy", got[0] == 1, f"got {got[0]}")
    check("sign_below_mid_sell", got[1] == -1, f"got {got[1]}")
    check("sign_at_mid_tick_up", got[2] == 1, f"got {got[2]}")
    check("sign_at_mid_tie_carry_last_pos", got[3] == 1, f"got {got[3]}")
    check("sign_at_mid_tick_down", got[5] == -1, f"got {got[5]}")
    check("sign_at_mid_tie_carry_last_neg", got[6] == -1, f"got {got[6]}")
    check("sign_full_vector", bool(np.array_equal(got, exp)), f"got {got.tolist()}")

    # --- planted panel ---
    recs = _synth_panel()
    # raw pooled rho(OLI, ret) should be negative (gap channel beta<0 dominates)
    oli_all = np.array([r["oli"] for r in recs])
    ret_all = np.array([r["ret"] for r in recs])
    raw_rho = _pearson(oli_all, ret_all)
    check("panel_raw_rho_negative", raw_rho < -0.2, f"raw_rho={raw_rho:.4f}")

    ga = gate_a_stats(recs, "ret")
    pa = pass_a_rule(ga["rho"], ga["ci_hi"])
    check("gatea_resid_rho_recovers_negative",
          -0.40 < ga["rho"] < -0.05, f"resid_rho={ga['rho']:.4f}")
    check("gatea_resid_separates_from_raw",
          ga["rho"] - raw_rho > 0.15,
          f"resid={ga['rho']:.4f} raw={raw_rho:.4f} (removed gap component)")
    check("gatea_ci_finite",
          math.isfinite(ga["ci_lo"]) and math.isfinite(ga["ci_hi"]),
          f"CI=[{ga['ci_lo']:.4f},{ga['ci_hi']:.4f}]")
    check("gatea_pass_true", pa, f"rho={ga['rho']:.4f} ci_hi={ga['ci_hi']:.4f}")

    gb = gate_b_stats(recs, "ret")
    pb = pass_b_rule(gb["mean"], gb["ci_lo"])
    check("gateb_mean_positive_fade", gb["mean"] > 0, f"mean={gb['mean']:.3f}")
    check("gateb_ci_finite",
          math.isfinite(gb["ci_lo"]) and math.isfinite(gb["ci_hi"]),
          f"CI=[{gb['ci_lo']:.3f},{gb['ci_hi']:.3f}]")
    check("gateb_pass_true", pb, f"mean={gb['mean']:.3f} ci_lo={gb['ci_lo']:.3f}")

    label = adjudicate(pa, pb, ga["rho"], gb["mean"])
    check("panel_label_pass", label == "PASS", f"label={label}")

    # residualization removes the planted gap component: refit ret ~ [1,gap] and
    # confirm OLI's incremental (residual) tie survives while the raw tie is
    # gap-inflated. Also verify the first-stage OLI<->gap link is strong.
    fs_rho, _ = first_stage_rho(recs)
    check("first_stage_oli_gap_positive", fs_rho > 0.3, f"fs_rho={fs_rho:.4f}")

    # --- mechanical gate predicates ---
    check("pass_a_threshold_ok", pass_a_rule(-0.05, -0.01) is True)
    check("pass_a_rho_too_high", pass_a_rule(-0.02, -0.01) is False)
    check("pass_a_ci_not_below_zero", pass_a_rule(-0.05, 0.01) is False)
    check("pass_b_threshold_ok", pass_b_rule(7.0, 1.0) is True)
    check("pass_b_mean_too_low", pass_b_rule(5.0, 1.0) is False)
    check("pass_b_ci_not_above_zero", pass_b_rule(7.0, -1.0) is False)

    # --- mechanical label branches ---
    check("label_pass", adjudicate(True, True, -0.1, 8.0) == "PASS")
    check("label_kill_rho_nonneg", adjudicate(False, False, 0.05, 8.0) == "KILL")
    check("label_kill_mean_nonpos", adjudicate(False, False, -0.1, -2.0) == "KILL")
    check("label_park_underpowered",
          adjudicate(True, False, -0.1, 3.0) == "PARK-UNDERPOWERED")

    # --- bootstrap sanity on a controlled constant mean ---
    dts = np.array(_fake_dates(50))
    lo, hi = _session_bootstrap_mean(dts, np.full(50, 8.0), BOOT_SEED, 200)
    check("boot_mean_constant", abs(lo - 8.0) < 1e-9 and abs(hi - 8.0) < 1e-9,
          f"[{lo},{hi}]")

    # --- report ---
    print("=" * 60)
    print("R2A-prong0 SELFTEST (synthetic; no files written)")
    print("=" * 60)
    n_fail = 0
    for name, ok, detail in results:
        tag = "PASS" if ok else "FAIL"
        if not ok:
            n_fail += 1
        line = f"[{tag}] {name}"
        if detail and (not ok or True):
            line += f"  ({detail})"
        print(line)
    print("-" * 60)
    print(f"{len(results) - n_fail}/{len(results)} assertions passed")
    print("=" * 60)
    return 1 if n_fail else 0


# --------------------------------------------------------------------------- #
# Entry
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="R2-A prong-0 pre-declared diagnostic.")
    ap.add_argument("--selftest", action="store_true",
                    help="Run synthetic assertions only; write no files.")
    ap.add_argument("--force-partial", action="store_true",
                    help="Override the partial-panel refusal (NON-CANONICAL).")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    return run_real(args.force_partial)


if __name__ == "__main__":
    sys.exit(main())
