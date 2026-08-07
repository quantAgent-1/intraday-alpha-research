"""Quote-free variant of the R2-A statistic (needed for names without bbo1s).

Two substitutions, and NOTHING else:
  1. signing -- the 1-second quote mid is unavailable, so the prevailing-price reference
     is the `bars1m` VWAP of the minute containing each print (attempt 2, per
     PREDECLARATION_AMENDMENT_1). This is fed to the frozen `r2a_prong0.sign_prints` as the
     quote series, so the classification logic -- price>ref +1, price<ref -1, tick-rule
     fallback, `_ffill_sign` carry-last -- is literally the frozen function and cannot
     drift. Attempt 1 (pure tick rule, no reference) FAILED the pre-declared V1 gate at
     corr 0.4566 and is retained below as `sign_prints_tick` for the record only.
  2. exit -- last `bars1m` close at or before 15:45 ET (require >= 15:40), via the frozen
     `r2a_prong0.exit_mid` (generic over any (sec, value) pair).

RAW-vs-ADJUSTED: `bars1d` is raw, `bars1m` is split/dividend adjusted. Returns here are
computed ENTIRELY inside `bars1m` (open of the 09:30 bar -> last close <= 15:45) so the
adjustment factor cancels within the day. Never divide one lake's price by the other's.

Everything else -- odd-lot/off-exchange/RTH filters, >=30 signed prints, the record
schema -- is the frozen module's own code.

Admissibility of this variant is decided by the pre-declared V1/V2/V3 gate in
`research/experiments/R2A-oos/PREDECLARATION.md`, computed by `r2a_qf_validate.py`.
"""

from __future__ import annotations

import sys
from collections import OrderedDict
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import r2a_prong0 as R  # noqa: E402

BARS1M_DIR = REPO / "data" / "raw" / "sip" / "bars1m"
_EMPTY_TS = np.zeros(0, dtype=np.int64)
_EMPTY_MID = np.zeros(0, dtype=np.float64)


def sign_prints_tick(t_ts: np.ndarray, t_px: np.ndarray) -> np.ndarray:
    """Frozen sign_prints with no quotes -> pure tick rule + carry-last."""
    return R.sign_prints(t_ts, t_px, _EMPTY_TS, _EMPTY_MID)


class Bars1mCache:
    """Per-symbol bars1m month loader -> per-day (sec, close), mirroring BboCache."""

    def __init__(self, sym: str, maxmonths: int = 3) -> None:
        self.dir = BARS1M_DIR / sym
        self.cache: OrderedDict[str, dict] = OrderedDict()
        self.maxmonths = maxmonths

    def _load_month(self, month: str) -> dict:
        p = self.dir / f"{month}.parquet"
        if not p.exists():
            return {}
        df = pl.read_parquet(p, columns=["ts", "open", "close", "vwap"]).filter(
            (pl.col("close") > 0) & (pl.col("vwap") > 0)
        )
        if df.height == 0:
            return {}
        df = df.with_columns(
            R._sec_expr().alias("_sec"), R._date_expr().alias("_d")
        ).sort("ts")
        out: dict = {}
        for key, g in df.partition_by("_d", as_dict=True, maintain_order=True).items():
            d = key[0] if isinstance(key, tuple) else key
            out[d] = {
                "sec": g["_sec"].to_numpy(),
                "ts": g["ts"].to_numpy(),
                "open": g["open"].to_numpy().astype(np.float64),
                "close": g["close"].to_numpy().astype(np.float64),
                "vwap": g["vwap"].to_numpy().astype(np.float64),
            }
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


def _rth_close(day: dict) -> float:
    """Last close at or before 16:00 ET (bars1m carries extended hours)."""
    idx = np.nonzero(day["sec"] < R.RTH_CLOSE_SEC)[0]
    return float(day["close"][idx[-1]]) if idx.size else float("nan")


def process_symbol_qf(sym: str) -> tuple[list[dict], dict]:
    """Mirror of r2a_prong0.process_symbol: minute-VWAP signing + all-bars1m returns."""
    bars = R.load_bars1d(sym)
    if bars is None:
        return [], {"n_candidates": 0, "funnel": {k: 0 for k in R.DROP_ORDER},
                    "n_kept": 0}
    dates, _opens_raw, closes_raw = bars
    m1 = Bars1mCache(sym)
    funnel = {k: 0 for k in R.DROP_ORDER}
    records: list[dict] = []
    n_candidates = 0

    for i in range(2, len(dates)):
        date_t = dates[i]
        if date_t >= R.CAP_DATE:
            continue
        date_tm1, date_tm2 = dates[i - 1], dates[i - 2]
        n_candidates += 1

        tr = R.load_trades_oddlot(sym, date_tm1)
        if tr is None or tr[0].shape[0] == 0:
            funnel["no_trades_tm1"] += 1
            continue
        day_t = m1.get_day(date_t)
        day_tm1 = m1.get_day(date_tm1)
        day_tm2 = m1.get_day(date_tm2)
        if day_t is None or day_tm1 is None or day_tm2 is None:
            funnel["no_bbo_t"] += 1          # reused key: "no bars1m source"
            continue
        sec_t = day_t["sec"]
        if int(sec_t[-1]) < R.EARLY_CLOSE_SEC:
            funnel["early_close_t"] += 1
            continue

        # All price anchors inside bars1m so the adjustment factor cancels intraday.
        rth_t = sec_t >= R.RTH_OPEN_SEC
        if not rth_t.any():
            funnel["bars_missing"] += 1
            continue
        open_t = float(day_t["open"][np.argmax(rth_t)])
        close_tm1 = _rth_close(day_tm1)     # RTH close, not the last extended-hours bar
        close_tm2 = _rth_close(day_tm2)
        if not (np.isfinite(open_t) and open_t > 0
                and np.isfinite(close_tm1) and close_tm1 > 0
                and np.isfinite(close_tm2) and close_tm2 > 0):
            funnel["bars_missing"] += 1
            continue

        t_ts, t_px, t_sz = tr
        # SCALE GUARD: trade prints are RAW, bars1m is ADJUSTED. Comparing them directly
        # signs every print the same way (KLAC's 10:1 split made OLI constant). Rescale
        # the day t-1 VWAP reference onto the raw scale with that day's own factor.
        # The factor's denominator MUST be the RTH close: bars1m carries extended hours,
        # and after-hours drift in the last bar shifts the whole reference off the raw
        # scale (symptom: |OLI| saturating at 1 for a third of name-days).
        rth_tm1 = np.nonzero(day_tm1["sec"] < R.RTH_CLOSE_SEC)[0]
        if rth_tm1.size == 0:
            funnel["bars_missing"] += 1
            continue
        adj_close_tm1 = float(day_tm1["close"][rth_tm1[-1]])
        if not (np.isfinite(adj_close_tm1) and adj_close_tm1 > 0):
            funnel["bars_missing"] += 1
            continue
        scale_tm1 = closes_raw[i - 1] / adj_close_tm1
        if not (np.isfinite(scale_tm1) and scale_tm1 > 0):
            funnel["bars_missing"] += 1
            continue
        ref_px = day_tm1["vwap"] * scale_tm1
        sign = R.sign_prints(t_ts, t_px, day_tm1["ts"], ref_px)
        n_signed = int((sign != 0).sum())
        if n_signed < R.MIN_SIGNED:
            funnel["few_odd_signs"] += 1
            continue
        buy = float(t_sz[sign > 0].sum())
        sell = float(t_sz[sign < 0].sum())
        if buy + sell <= 0:
            funnel["few_odd_signs"] += 1
            continue

        ex = R.exit_mid(sec_t, day_t["close"], R.EXIT_MAIN_HI, R.EXIT_MAIN_LO)
        if ex is None:
            funnel["no_exit_t"] += 1
            continue

        records.append({
            "sym": sym, "tier": R.tier_of(sym), "date": date_t, "date_tm1": date_tm1,
            "oli": (buy - sell) / (buy + sell),
            "ret": (ex / open_t - 1.0) * 1e4,
            "gap": (open_t / close_tm1 - 1.0) * 1e4,
            "ret_prev": (close_tm1 / close_tm2 - 1.0) * 1e4,
            "n_signed": n_signed, "n_oddlot": int(t_ts.shape[0]),
        })

    return records, {"n_candidates": n_candidates, "funnel": funnel,
                     "n_kept": len(records)}
