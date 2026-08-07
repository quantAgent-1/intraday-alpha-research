"""TradePlan — the single contract between constructor, replayer, and dashboard.

A plan is COMPLETE by construction: a human (or the causal replayer) can execute
it without inventing any leg. Frozen slots dataclasses; timestamps UTC ns.
This schema is versioned (SCHEMA_VERSION) — the dashboard and the journal store
it as JSON via `to_json_dict`.

Field semantics that carry protocol weight:
- `valid_until`: after this instant the plan is void (never execute a stale plan);
  PROTOCOL v6 requires valid_until - ts_authored >= plan_valid_min_s.
- `entry.expire_s`: limit entries cancel after this many seconds unfilled;
  `chase_at_expire` converts the remnant to a market order instead (modeled and
  charged honestly by the replayer).
- `stop.basis` names the invalidation logic ("mae_q75", "vwap", "gap_fill",
  "cascade_low", ...) so the human knows WHY the stop sits where it does.
- `targets`: profit-takes with size fractions summing to <= 1.0; any remainder
  exits at hold expiry / curfew.
- `expected_*` and `p_win`/`confidence` are the model's own claims, recorded at
  authoring time — calibration is scored against them later (PROTOCOL v6 §4).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

SCHEMA_VERSION = 1

LONG = 1
SHORT = -1


@dataclass(slots=True, frozen=True)
class EntrySpec:
    type: str  # "limit" | "market"
    limit_price: float | None  # required iff type == "limit"
    expire_s: int  # limit lifetime before cancel/chase (ignored for market)
    chase_at_expire: bool  # True: unfilled limit converts to market at expiry


@dataclass(slots=True, frozen=True)
class StopSpec:
    price: float
    basis: str  # named invalidation ("mae_q75", "vwap", "gap_fill", ...)


@dataclass(slots=True, frozen=True)
class TargetSpec:
    price: float
    frac: float  # fraction of position to take off at this level, (0, 1]

    def __post_init__(self) -> None:
        if not (0.0 < self.frac <= 1.0 + 1e-9):
            raise ValueError(f"frac must be in (0, 1], got {self.frac}")


@dataclass(slots=True, frozen=True)
class TradePlan:
    plan_id: str
    symbol: str
    ts_authored: int  # UTC ns
    valid_until: int  # UTC ns — void after this
    side: int  # LONG (+1) or SHORT (-1)
    entry: EntrySpec
    stop: StopSpec
    targets: tuple[TargetSpec, ...]
    hold_max_min: int  # vertical bar: force-exit this many minutes after fill
    curfew_ts: int  # UTC ns session force-flat (from calendar, handles half-days)
    expected_gross_bps: float  # model's mid-to-mid claim over the hold
    expected_net_bps: float  # after modeled friction
    sigma_h_bps: float  # expected vol over the hold window
    p_win: float  # model's probability the plan nets > 0
    ev_ratio: float  # expected gross / modeled RT cost
    confidence: float  # calibrated take-strength in [0, 1]
    payer: str  # registered named payer ("gap_mr", "letf_window", ...)
    horizon_min: int  # payer's natural horizon (info; hold_max_min governs)
    model_ids: tuple[str, ...] = ()
    schema_version: int = SCHEMA_VERSION
    meta: tuple[tuple[str, float], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.side not in (LONG, SHORT):
            raise ValueError(f"side must be +1/-1, got {self.side}")
        if self.entry.type not in ("limit", "market"):
            raise ValueError(f"entry.type must be limit|market, got {self.entry.type}")
        if self.entry.type == "limit" and self.entry.limit_price is None:
            raise ValueError("limit entry requires limit_price")
        if self.valid_until <= self.ts_authored:
            raise ValueError("valid_until must be after ts_authored")
        total = sum(t.frac for t in self.targets)
        if total > 1.0 + 1e-9:
            raise ValueError(f"target fracs sum to {total} > 1")
        if not (0.0 <= self.p_win <= 1.0 and 0.0 <= self.confidence <= 1.0):
            raise ValueError("p_win/confidence must be in [0,1]")
        # Stop must sit on the losing side of entry reference, targets on the
        # winning side. Entry reference: limit price if set, else stop/target
        # ordering alone (market entries have no anchor until fill).
        ref = self.entry.limit_price
        if ref is not None:
            if self.side == LONG and not self.stop.price < ref:
                raise ValueError("long plan: stop must be below entry")
            if self.side == SHORT and not self.stop.price > ref:
                raise ValueError("short plan: stop must be above entry")
            for t in self.targets:
                if self.side == LONG and not t.price > ref:
                    raise ValueError("long plan: targets must be above entry")
                if self.side == SHORT and not t.price < ref:
                    raise ValueError("short plan: targets must be below entry")

    def to_json_dict(self) -> dict:
        return asdict(self)
