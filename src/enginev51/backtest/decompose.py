"""P&L decomposition with an exact reconciliation identity.

The replayer (`backtest/replay.py`) hands each taken plan its entry and exit
`Fill` objects (see `backtest/fills.py`). This module splits what the book
actually netted into four attributable components plus a residual that MUST be
~0 -- the residual is the audit: if the parts do not sum to the whole, the
decomposition (or the fills) are wrong.

Everything is expressed per unit of original plan size and quoted in basis
points on the *entry VWAP* (the notional reference). Signed so that

    net_bps == gross_mid_bps - latency_drag_bps - spread_cost_bps - fees_bps

holds to floating-point tolerance. The identity is algebraic: the four mid
aggregates (decision/action x entry/exit) cancel pairwise, leaving exactly
side*(exit_vwap - entry_vwap)/entry_vwap*1e4, which is net_bps + fees_bps. So
the residual is identically zero by construction whenever every mid is finite;
it is stored anyway so a non-zero value flags a coding/data fault.

nan discipline: net_bps and fees_bps read *fill prices only* and so always
compute. gross/latency/spread read mids; a nan mid propagates through the
arithmetic to make that component nan (and hence the residual nan) without
touching net_bps -- exactly the required fallback, no special-casing needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:  # Fill is duck-typed at runtime; imported only for type hints.
    from enginev51.backtest.fills import Fill

LONG = 1
SHORT = -1
# Basis points per unit fraction (multiply a fractional return by this to get
# bps). Deliberately NOT named BPS: fills.py's FRAC_PER_BP is the inverse
# (1e-4), and the shared name invited copy-paste mistakes (code review F16).
BPS_SCALE = 1e4


@dataclass(slots=True, frozen=True)
class PlanPnl:
    net_bps: float          # what the book actually made, on entry notional, fees included
    gross_mid_bps: float    # mid(decision->decision) alpha: the signal's own move
    latency_drag_bps: float  # adverse mid drift decision_ts -> action, both legs
    spread_cost_bps: float  # crossing cost (negative = maker earn), both legs
    fees_bps: float         # SEC/TAF on sell notional legs (config sec_taf_sell_bps)
    identity_residual_bps: float  # net - (gross - latency - spread - fees); MUST be ~0


@dataclass(slots=True, frozen=True)
class _Leg:
    """Qty-weighted aggregates for one side of the round trip."""

    vwap: float       # sum(price*qty) / sum(qty)
    mid_dec: float    # sum(mid_at_decision*qty) / sum(qty)
    mid_act: float    # sum(mid_at_action*qty)   / sum(qty)
    notional: float   # sum(price*qty)  (per unit of plan size)


def _aggregate(fills: tuple[Fill, ...]) -> _Leg:
    """Collapse a leg's fills to qty-weighted VWAP / mids / notional.

    Each aggregate is normalized by *this leg's own* filled fraction, so the
    identity holds even if entry and exit filled fractions differ slightly.
    A nan in any mid propagates into that aggregate (numpy semantics), which is
    the intended fallback.
    """
    if not fills:
        raise ValueError("leg has no fills")
    price = np.fromiter((f.price for f in fills), dtype=np.float64, count=len(fills))
    qty = np.fromiter((f.qty_frac for f in fills), dtype=np.float64, count=len(fills))
    mid_dec = np.fromiter((f.mid_at_decision for f in fills), dtype=np.float64, count=len(fills))
    mid_act = np.fromiter((f.mid_at_action for f in fills), dtype=np.float64, count=len(fills))
    f = float(qty.sum())
    if not f > 0.0:
        raise ValueError(f"leg filled fraction must be > 0, got {f}")
    notional = float((price * qty).sum())
    return _Leg(
        vwap=notional / f,
        mid_dec=float((mid_dec * qty).sum()) / f,
        mid_act=float((mid_act * qty).sum()) / f,
        notional=notional,
    )


def plan_pnl(
    side: int,
    entry_fills: tuple[Fill, ...],
    exit_fills: tuple[Fill, ...],
    sec_taf_sell_bps: float,
) -> PlanPnl:
    """Decompose one plan's realized P&L into attributable bps components.

    `side` is +1 long / -1 short. Fills are per unit of original plan size;
    entry and exit `qty_frac` each sum to the filled fraction F (<= 1). All bps
    are on the entry VWAP as the notional reference. SEC/TAF hits the SELL legs:
    exit legs for a long, entry legs for a short.
    """
    if side not in (LONG, SHORT):
        raise ValueError(f"side must be +1/-1, got {side}")

    en = _aggregate(entry_fills)
    ex = _aggregate(exit_fills)

    # bps conversion factor on the entry-VWAP notional reference.
    k = side / en.vwap * BPS_SCALE

    # Fees: SEC/TAF * (sell notional / entry notional). Long sells the exit,
    # short sells the entry (ratio == 1 there). Prices only -> always finite.
    sell_notional = ex.notional if side == LONG else en.notional
    fees_bps = sec_taf_sell_bps * (sell_notional / en.notional)

    # net: realized price-to-price move less fees. Prices only -> always finite.
    net_bps = side * (ex.vwap - en.vwap) / en.vwap * BPS_SCALE - fees_bps

    # gross alpha: mid(decision) -> mid(decision), the signal's own move.
    gross_mid_bps = k * (ex.mid_dec - en.mid_dec)

    # latency drag: adverse mid drift while the human acts, both legs, signed so
    # the identity holds (entry drift up hurts a buyer; exit drift down hurts a
    # seller -> subtract the exit term).
    latency_drag_bps = k * ((en.mid_act - en.mid_dec) - (ex.mid_act - ex.mid_dec))

    # spread/crossing cost: price paid vs mid at the moment of action, both legs.
    # Buying above mid (or selling below) costs; a maker fill lands on the
    # favorable side of mid and flips the term negative == earn.
    spread_cost_bps = k * ((en.vwap - en.mid_act) - (ex.vwap - ex.mid_act))

    # Audit residual: 0 to fp when mids are finite, nan if any component is nan.
    identity_residual_bps = net_bps - (
        gross_mid_bps - latency_drag_bps - spread_cost_bps - fees_bps
    )

    return PlanPnl(
        net_bps=net_bps,
        gross_mid_bps=gross_mid_bps,
        latency_drag_bps=latency_drag_bps,
        spread_cost_bps=spread_cost_bps,
        fees_bps=fees_bps,
        identity_residual_bps=identity_residual_bps,
    )


def _net_of(result: object) -> float:
    """Pull net_bps off a replay result, PlanPnl, or mapping. Deliberately dumb.

    A result that carries NO pnl and no net_bps — every VOID / NOT_TAKEN /
    UNFILLED `PlanResult` — contributes nan rather than raising AttributeError
    (code review 2026-07-28 N2). The aggregate is nan-aware, so a mixed list of
    taken and void plans summarizes instead of crashing; a void is a real,
    countable outcome (foregone breadth), not a missing field.
    """
    if isinstance(result, PlanPnl):
        return result.net_bps
    if isinstance(result, dict):
        pnl = result.get("pnl")
        if pnl is not None:
            return _net_of(pnl)
        net = result.get("net_bps")
        return float("nan") if net is None else float(net)
    pnl = getattr(result, "pnl", None)
    if pnl is not None:
        return _net_of(pnl)
    net = getattr(result, "net_bps", None)
    return float("nan") if net is None else float(net)


def _reason_of(result: object) -> str:
    """Exit reason label; absent OR None (voids carry no reason) -> "unknown"."""
    reason = (
        result.get("exit_reason") if isinstance(result, dict)
        else getattr(result, "exit_reason", None)
    )
    return "unknown" if reason is None else str(reason)


def session_summary(results: list) -> dict:
    """Aggregate per-plan results: net mean/sum and per-exit-reason counts.

    Kept intentionally dumb (no polars): `results` items expose net either
    directly (`net_bps`), via a `pnl` PlanPnl, or as a mapping, plus an
    `exit_reason`. Missing reasons bucket as "unknown".
    """
    nets: list[float] = []
    reason_counts: dict[str, int] = {}
    for r in results:
        nets.append(_net_of(r))
        reason = _reason_of(r)
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    n = len(nets)
    total = float(np.nansum(nets)) if n else 0.0
    # nanmean over an all-nan list (every plan voided) is nan but warns; the
    # answer is the same and the warning is noise in a report (N2).
    priced = n and bool(np.any(np.isfinite(nets)))
    mean = float(np.nanmean(nets)) if priced else float("nan")
    return {
        "n_plans": n,
        "sum_net_bps": total,
        "mean_net_bps": mean,
        "exit_reason_counts": reason_counts,
    }
