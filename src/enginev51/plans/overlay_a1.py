"""A1 model overlay — the REGISTERED overlay on the A0 detector plans (trial M3-A1-v1).

Implements the "A1 overlay" section of research/experiments/M3_REGISTRATION.md
EXACTLY (a-priori, registered 2026-07-15 before economics). Two pieces:

* ``PredProvider`` — PIT lookup into the frozen prediction contract parquets at
  ``data/preds/a1_v1/{SYMBOL}.parquet``. ``row_at`` returns the LAST prediction
  row *available* at the decision instant — ``row.ts <= decision_ts -
  PRED_STAMP_TO_AVAILABILITY_NS`` — for a (symbol, session), or None. Rows are
  stamped at bar OPEN but carry that bar's close, so a row is only knowable one
  bar later; consuming it at ``ts <= decision_ts`` leaked 60 s of future tape on
  decisions landing on a pred-row stamp (SIM_AUDIT_2026-07-21 §3, defect F2).
  The producer guarantees ``trained_through < session`` on every row (PIT).

* ``apply_overlay`` — turn an A0 ``TradePlan`` into the A1 plan (or veto it):
    1. SKIP (return None) iff the model OPPOSES the detector direction:
       sign(pred_fwdH_z) != side AND |pred_fwdH_z| >= 0.5.
       H = 60 for vwap_magnet/letf_window, else 120.
    2. Legs re-priced from the de-normed excursion quantiles:
         stop distance   = de-norm |pred_maeH_q75|, floored at the A0 stop
                           distance and capped at 2x the A0 stop distance;
         targets         = de-norm MFE q50 (first leg) and q75 (second leg),
                           floored at 10 bps and capped at 2x the matching A0
                           target distance. Single-target payers use q50 only;
                           letf_window keeps no targets.
       A re-priced leg that would violate the schema side-ordering falls back to
       the original A0 leg.
    3. expected_gross_bps = de-norm |pred_fwdH| when the model AGREES
       (sign == side), else the A0 template. EV hurdle unchanged (2x cost, 8 bps).
    4. confidence = p_win = 0.5 + 0.2 * min(|pred_fwdH_z|, 2)/2 when agreeing
       (max 0.7), else 0.5.
   model_ids = ("A1", "lgbm_a1_v1"). Returns a NEW frozen TradePlan.

The de-norm is the frozen Z-CONVENTION: bps = z * vol20 * sqrt(H/390) * 1e4;
a px distance is bps/1e4 * entry_ref = |z| * vol20 * sqrt(H/390) * entry_ref.
"""

from __future__ import annotations

import dataclasses
import math
from pathlib import Path

import polars as pl

from enginev51.features.grid import PRED_STAMP_TO_AVAILABILITY_NS
from enginev51.plans.schema import StopSpec, TargetSpec, TradePlan

SESSION_MINUTES = 390.0

# Registered horizon per payer (M3_REGISTRATION.md A1 rule 1).
H_BY_PAYER: dict[str, int] = {
    "vwap_magnet": 60,
    "letf_window": 60,
    "gap_mr": 120,
    "cascade": 120,
    "expiry_pin": 120,
}

DROP_COUNTS: dict = {}  # rule1_veto / hurdle_fail — reset per run by run_trial
Z_SKIP = 0.5              # |pred_fwdH_z| threshold for an opposing veto
RULE3_MODE = "forecast"   # 'forecast' (registered v1) | 'a0' (variant v3, legs-only)
# v2 variant knob (ledger M3-A1-v2): float('inf') disables the veto entirely
# (legs-only mode) while keeping MFE/MAE re-pricing. Registered values only.
TARGET_FLOOR_BPS = 10.0   # registered target-distance floor
MIN_GROSS_BPS = 8.0       # registered EV hurdle floor (unchanged from A0)
HURDLE_COST_MULT = 2.0    # expected_gross >= 2 x RT cost
MODEL_IDS: tuple[str, ...] = ("A1", "lgbm_a1_v1")


def _z_scale(h_min: int) -> float:
    """The vol20-free part of the de-norm map: sqrt(H_min/390)."""
    return math.sqrt(h_min / SESSION_MINUTES)


def denorm_bps(z: float, vol20: float, h_min: int) -> float:
    """z -> realized move in basis points (the registered de-norm)."""
    return z * vol20 * _z_scale(h_min) * 1e4


def denorm_px(z_mag: float, vol20: float, h_min: int, entry_ref: float) -> float:
    """|z| -> a positive price *distance* at ``entry_ref`` (bps/1e4 * ref)."""
    return abs(z_mag) * vol20 * _z_scale(h_min) * entry_ref


# --------------------------------------------------------------------------- provider


class PredProvider:
    """Lazy per-symbol reader for the frozen A1 prediction contract parquets.

    One parquet per tick symbol under ``preds_dir``; each is read at most once
    and cached (None caches a missing file). ``row_at`` does the PIT lookup:
    the LAST row *available* at the decision instant — ``row.ts <= decision_ts -
    PRED_STAMP_TO_AVAILABILITY_NS`` — inside the requested ``session`` (F2).
    """

    def __init__(self, preds_dir: str | Path) -> None:
        self.preds_dir = Path(preds_dir)
        self._cache: dict[str, pl.DataFrame | None] = {}

    def _frame(self, symbol: str) -> pl.DataFrame | None:
        symbol = symbol.upper()
        if symbol not in self._cache:
            path = self.preds_dir / f"{symbol}.parquet"
            self._cache[symbol] = (
                pl.read_parquet(path).sort("ts") if path.is_file() else None
            )
        return self._cache[symbol]

    def row_at(self, symbol: str, session: str, ts: int) -> dict | None:
        """LAST prediction row AVAILABLE at decision instant ``ts``, else None.

        A pred row is stamped at bar OPEN but its contents include that bar's
        close, so it is knowable only at ``row.ts + PRED_STAMP_TO_AVAILABILITY_NS``.
        A decision at ``ts`` may therefore consume only rows stamped at or before
        ``ts - PRED_STAMP_TO_AVAILABILITY_NS`` (SIM_AUDIT_2026-07-21 §3, F2).
        """
        df = self._frame(symbol)
        if df is None or df.height == 0:
            return None
        avail_ts = ts - PRED_STAMP_TO_AVAILABILITY_NS
        sub = df.filter((pl.col("session") == session) & (pl.col("ts") <= avail_ts))
        if sub.height == 0:
            return None
        return sub.row(sub.height - 1, named=True)  # last (frame is ts-sorted)


# --------------------------------------------------------------------------- overlay


def _clamp(x: float, lo: float, hi: float) -> float:
    """Floor then cap. Cap wins when a degenerate cap < floor is supplied."""
    return min(max(x, lo), hi)


def apply_overlay(
    plan: TradePlan,
    state_direction: int,
    pred: dict | None,
    payer: str,
    a0_stop_distance_px: float,
    a0_target_distances_px: list[float],
    entry_ref: float,
    rt_cost_bps: float,
) -> TradePlan | None:
    """Apply the registered A1 overlay to an A0 ``plan``; None = vetoed/hurdle-fail.

    ``pred is None`` returns the A0 plan UNCHANGED (no model, no veto). Otherwise
    the four registered rules run in order (skip, re-price legs, expected_gross,
    confidence) and a NEW frozen TradePlan is returned.
    """
    if pred is None:
        return plan  # no prediction -> A0 stands, unchanged

    side = state_direction
    h = H_BY_PAYER[payer]
    vol20 = float(pred["vol20"])
    fwd_z = float(pred[f"pred_fwd{h}_z"])

    # 1. SKIP iff the model opposes the detector with conviction.
    z_side = 1 if fwd_z > 0 else (-1 if fwd_z < 0 else 0)
    if z_side != side and abs(fwd_z) >= Z_SKIP:
        DROP_COUNTS["rule1_veto"] = DROP_COUNTS.get("rule1_veto", 0) + 1
        return None
    agrees = z_side == side

    # 2. Re-price the stop from de-normed MAE q75, clamped to [A0, 2xA0].
    mae_z = float(pred[f"pred_mae{h}_q75_z"])
    stop_dist = _clamp(
        denorm_px(mae_z, vol20, h, entry_ref),
        a0_stop_distance_px,
        2.0 * a0_stop_distance_px,
    )
    stop_price = entry_ref - side * stop_dist
    stop_ok = (side > 0 and stop_price < entry_ref) or (side < 0 and stop_price > entry_ref)
    new_stop = (
        StopSpec(price=stop_price, basis=f"mae{h}_q75")
        if stop_ok
        else plan.stop  # schema-invariant fallback: keep the A0 stop leg
    )

    # 2. Re-price targets from de-normed MFE quantiles (q50 first leg, q75 second).
    q_z_cols = (f"pred_mfe{h}_q50_z", f"pred_mfe{h}_q75_z")
    floor_px = (TARGET_FLOOR_BPS / 1e4) * entry_ref
    new_targets: list[TargetSpec] = []
    for i, t in enumerate(plan.targets):
        mfe_z = float(pred[q_z_cols[0 if i == 0 else 1]])
        cap_px = 2.0 * a0_target_distances_px[i]
        dist = _clamp(denorm_px(mfe_z, vol20, h, entry_ref), floor_px, cap_px)
        price = entry_ref + side * dist
        ok = (side > 0 and price > entry_ref) or (side < 0 and price < entry_ref)
        new_targets.append(TargetSpec(price=price, frac=t.frac) if ok else t)

    # 3. expected_gross: de-normed |pred_fwdH| when agreeing, else A0 template.
    # RULE3_MODE 'a0' (variant M3-A1-v3): ALWAYS keep the A0 template for the
    # hurdle — isolates the MFE/MAE leg heads from forecast-magnitude selection
    # (v1 finding: the forecast-hurdle, not the veto, was the destructive term).
    if RULE3_MODE == "a0":
        expected_gross = plan.expected_gross_bps
    elif agrees:
        expected_gross = denorm_bps(abs(fwd_z), vol20, h)
    else:
        expected_gross = plan.expected_gross_bps
    if expected_gross < max(HURDLE_COST_MULT * rt_cost_bps, MIN_GROSS_BPS):
        DROP_COUNTS["hurdle_fail"] = DROP_COUNTS.get("hurdle_fail", 0) + 1
        return None  # EV hurdle unchanged

    # 4. confidence = p_win.
    confidence = 0.5 + 0.2 * min(abs(fwd_z), 2.0) / 2.0 if agrees else 0.5

    return dataclasses.replace(
        plan,
        stop=new_stop,
        targets=tuple(new_targets),
        expected_gross_bps=expected_gross,
        expected_net_bps=expected_gross - rt_cost_bps,
        p_win=confidence,
        ev_ratio=expected_gross / max(rt_cost_bps, 1e-9),
        confidence=confidence,
        model_ids=MODEL_IDS,
    )
