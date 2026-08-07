"""Cross-layer contracts.

Frozen slots dataclasses are the only shapes that cross layer boundaries
(engineV2/V5 convention, kept). Timestamps are UTC epoch nanoseconds throughout.
Field shapes for Bar/TradeTick/QuoteTick match engineV5's contracts so its
lake and loaders port unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Bar:
    """One OHLCV bar (1-min unless stated otherwise). ts = bar OPEN time, UTC ns."""

    symbol: str
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: int
    vwap: float


@dataclass(slots=True, frozen=True)
class TradeTick:
    symbol: str
    ts: int
    price: float
    size: float
    exchange: str
    conditions: str  # joined with '|'
    tape: str


@dataclass(slots=True, frozen=True)
class QuoteTick:
    symbol: str
    ts: int
    bid: float
    bid_size: float
    bid_exchange: str
    ask: float
    ask_size: float
    ask_exchange: str
    conditions: str
    tape: str


@dataclass(slots=True, frozen=True)
class DetectorState:
    """Point-in-time named-payer state emitted by events/detectors/*.

    A detector must compute this from data at or before `ts` only.
    `payer` is the registered payer id ("gap_mr", "letf_window", "vwap_magnet",
    "cascade", "expiry_pin"). `direction` is the suggested side (+1 long,
    -1 short, 0 = active but sideless). `strength` is detector-normalized [0,1].
    """

    symbol: str
    ts: int
    payer: str
    active: bool
    direction: int
    strength: float
    horizon_min: int
    meta: tuple[tuple[str, float], ...] = ()
