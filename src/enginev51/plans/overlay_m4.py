"""M4 encoder overlay — the REGISTERED barrier-model arms on the A0 detector plans.

Implements the "M4 encoder" section of research/experiments/M3_REGISTRATION.md
(family ``m4_encoder_v1``, registered 2026-07-15 before any encoder economics).
The encoder emits the A1 leg-pricing prediction-contract columns PLUS a barrier
probability grid; this module turns an A0 ``TradePlan`` into an M4 plan (or vetoes
it) using three registered, a-priori arms selected by ``mode``:

* ``select`` (A2-select): SKIP a state iff the adverse-barrier probability at the
  payer horizon is >= ``p_skip``. Legs and hurdle stay A0.
* ``legs`` (A2-legs): A0 selection (never skips); re-price stop/targets from the
  encoder MFE/MAE heads with EXACTLY the A1-v3 clamps; A0 hurdle.
* ``both`` (A2-both): selector THEN legs, applied serially.

Pieces:

* ``M4Provider`` — PIT lookup into the frozen prediction parquets at
  ``data/preds/m4_v1/{SYMBOL}.parquet`` (A1 columns + 16 barrier probability
  columns ``p_{up|dn}_{a}x{b}_{H}``). ``row_at`` returns the LAST row *available*
  at the decision instant — ``row.ts <= decision_ts -
  PRED_STAMP_TO_AVAILABILITY_NS`` — for a (symbol, session), or None; identical
  PIT contract to ``overlay_a1.PredProvider``, including the one-bar availability
  lag that closes defect F2 (SIM_AUDIT_2026-07-21 §3). ``arch_tag`` is read once
  from a ``_train_report`` in the preds dir when cheaply available, else ``"m4_v1"``.

* ``apply_m4`` — apply the selected arm; None = vetoed/hurdle-fail; ``pred is
  None`` returns the plan UNCHANGED.

Selector barrier columns (registered, per M3_REGISTRATION M4 + ledger 2026-07-15):
  LONG  p_adverse = ``p_dn_075x125_{H}``  (down 1.25 sigma before up 0.75)
  SHORT p_adverse = ``p_up_125x075_{H}``  (up 1.25 sigma before down 0.75)
  H = 60 for vwap_magnet/letf_window, else 120 (same horizons as A1).

Legs use the frozen Z-CONVENTION de-norm (bps = z * vol20 * sqrt(H/390) * 1e4),
shared with overlay_a1. The hurdle is ALWAYS the A0 template expected_gross
(rule-3 mode ``a0``): the v1 forecast-hurdle was measured to be an anti-selector.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import polars as pl

from enginev51.features.grid import PRED_STAMP_TO_AVAILABILITY_NS
from enginev51.plans.overlay_a1 import (
    H_BY_PAYER,
    HURDLE_COST_MULT,
    MIN_GROSS_BPS,
    TARGET_FLOOR_BPS,
    _clamp,
    denorm_px,
)
from enginev51.plans.schema import StopSpec, TargetSpec, TradePlan

# selector_skip / hurdle_fail — reset per run by run_trial.
DROP_COUNTS: dict = {}

# Registered selector threshold default (variant values {0.35, 0.45}).
P_SKIP_DEFAULT = 0.45

# Arch tag appended to model_ids; overridden from the preds _train_report when a
# provider is constructed (see M4Provider.arch_tag). Default is the frozen family.
MODEL_TAG = "m4_v1"

_MODES = ("select", "legs", "both")


def _adverse_col(side: int, h: int) -> str:
    """Registered adverse-barrier column for a plan side at horizon ``h``.

    Column naming follows the trainer's emission (dotted a x b): LONG's adverse
    event is DOWN 1.25 sigma before UP 0.75 (pair a=0.75, b=1.25); SHORT mirrors.
    """
    return f"p_dn_0.75x1.25_{h}" if side > 0 else f"p_up_1.25x0.75_{h}"


# --------------------------------------------------------------------------- provider


class M4Provider:
    """Lazy per-symbol reader for the frozen M4 prediction-contract parquets.

    One parquet per tick symbol under ``preds_dir``; each is read at most once and
    cached (None caches a missing file). ``row_at`` does the PIT lookup: the LAST
    row *available* at the decision instant — ``row.ts <= decision_ts -
    PRED_STAMP_TO_AVAILABILITY_NS`` — inside the requested ``session`` (F2; the
    producer also guarantees ``trained_through < session`` on every row).
    """

    def __init__(self, preds_dir: str | Path) -> None:
        self.preds_dir = Path(preds_dir)
        self._cache: dict[str, pl.DataFrame | None] = {}
        self.arch_tag = self._read_arch_tag()

    def _read_arch_tag(self) -> str:
        """Best-effort arch tag from a ``_train_report`` in the preds dir."""
        p = self.preds_dir / "_train_report.json"
        if p.is_file():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                for k in ("arch", "architecture", "arch_tag", "model_arch"):
                    v = d.get(k)
                    if v:
                        return str(v)
            except (ValueError, OSError):
                pass
        return "m4_v1"

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

        Rows are stamped at bar OPEN but carry that bar's close, so a decision at
        ``ts`` may consume only rows stamped at or before
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


def _reprice_legs(
    plan: TradePlan,
    pred: dict,
    side: int,
    h: int,
    a0_stop_distance_px: float,
    a0_target_distances_px: list[float],
    entry_ref: float,
) -> tuple[StopSpec, tuple[TargetSpec, ...]]:
    """A1-v3 leg re-pricing: MAE q75 stop, MFE q50/q75 targets, same clamps/fallbacks."""
    vol20 = float(pred["vol20"])

    # Stop from de-normed MAE q75, clamped to [A0, 2xA0]; schema-invariant fallback.
    mae_z = float(pred[f"pred_mae{h}_q75_z"])
    stop_dist = _clamp(
        denorm_px(mae_z, vol20, h, entry_ref),
        a0_stop_distance_px,
        2.0 * a0_stop_distance_px,
    )
    stop_price = entry_ref - side * stop_dist
    stop_ok = (side > 0 and stop_price < entry_ref) or (side < 0 and stop_price > entry_ref)
    new_stop = (
        StopSpec(price=stop_price, basis=f"mae{h}_q75") if stop_ok else plan.stop
    )

    # Targets from de-normed MFE quantiles (q50 first leg, q75 second), floor 10bps,
    # cap 2x the matching A0 target distance; per-leg schema-invariant fallback.
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

    return new_stop, tuple(new_targets)


def apply_m4(
    plan: TradePlan,
    pred: dict | None,
    mode: str,
    p_skip: float,
    a0_stop_distance_px: float,
    a0_target_distances_px: list[float],
    entry_ref: float,
    rt_cost_bps: float,
) -> TradePlan | None:
    """Apply the registered M4 arm ``mode`` to an A0 ``plan``; None = vetoed/hurdle-fail.

    ``pred is None`` returns the plan UNCHANGED (no encoder row -> A0 stands). Side
    and payer are read from the plan. ``mode`` is one of select|legs|both.
    """
    if pred is None:
        return plan  # no prediction -> A0 stands, unchanged
    if mode not in _MODES:
        raise ValueError(f"mode must be one of {_MODES}, got {mode!r}")

    side = plan.side
    h = H_BY_PAYER[plan.payer]
    do_select = mode in ("select", "both")
    do_legs = mode in ("legs", "both")

    # --- SELECTOR: skip iff the adverse barrier probability >= p_skip. ---
    p_adverse = None
    if do_select:
        p_adverse = float(pred[_adverse_col(side, h)])
        if p_adverse >= p_skip:
            DROP_COUNTS["selector_skip"] = DROP_COUNTS.get("selector_skip", 0) + 1
            return None

    # --- LEGS: A1-v3 re-pricing (else keep the A0 legs). ---
    if do_legs:
        new_stop, new_targets = _reprice_legs(
            plan, pred, side, h, a0_stop_distance_px, a0_target_distances_px, entry_ref
        )
    else:
        new_stop, new_targets = plan.stop, plan.targets

    # --- HURDLE: ALWAYS the A0 template expected_gross (rule-3 mode a0). ---
    expected_gross = plan.expected_gross_bps
    if expected_gross < max(HURDLE_COST_MULT * rt_cost_bps, MIN_GROSS_BPS):
        DROP_COUNTS["hurdle_fail"] = DROP_COUNTS.get("hurdle_fail", 0) + 1
        return None

    # --- CONFIDENCE. ---
    if do_select:
        # more headroom below p_skip => more confident (cap 0.9).
        confidence = min(0.9, 0.5 + 0.4 * max(0.0, p_skip - p_adverse) / p_skip)
        p_win = confidence
    else:  # legs-only: keep the incoming plan's confidence/p_win.
        confidence = plan.confidence
        p_win = plan.p_win

    model_ids = tuple(plan.model_ids) + ("M4", MODEL_TAG)

    return dataclasses.replace(
        plan,
        stop=new_stop,
        targets=new_targets,
        expected_gross_bps=expected_gross,
        expected_net_bps=expected_gross - rt_cost_bps,
        p_win=p_win,
        ev_ratio=expected_gross / max(rt_cost_bps, 1e-9),
        confidence=confidence,
        model_ids=model_ids,
    )
