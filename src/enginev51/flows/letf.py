"""Leveraged/inverse-ETF close-rebalance demand estimator (named payer).

Mechanism (documented flow state, PROTOCOL §Named payers): a daily-reset
leveraged ETF must hold `L ×` its net assets in index exposure. When the index
moves `r` on the day, the fund's exposure drifts to `L·(1+r)·AUM` but its equity
becomes `(1 + L·r)·AUM`, so to restore the `L×` target for tomorrow it must hold
`L·(1 + L·r)·AUM`. The exposure it must ADD into the close is

    ΔExposure = L·(1 + L·r)·AUM − L·(1 + r)·AUM = (L² − L)·AUM·r

This is `rebalance_demand_usd`. Sign convention: **positive = the ETF complex
must BUY the underlying index into the close** (and negative = must SELL).

Key non-obvious property: because the driver is `L² − L`, BOTH bull and inverse
funds buy when the index rises. For a +3x fund L=3 → L²−L = 6 (>0, buys on a
rally). For a −3x fund L=−3 → L²−L = 12 (>0, ALSO buys on a rally): it is short
3x, a rally makes it more short in delta terms, so it too must buy the index
back. The two same-index funds therefore ADD rather than cancel — the complex
demand aggregates them.

Deploy-lens / mechanism magnitude only. PROTOCOL v6 §5 bars this (a
forward/deploy-flavoured series) from any Stage A gated result.
"""

from __future__ import annotations

import tomllib
from datetime import date, datetime
from pathlib import Path
from typing import Any

import structlog

from enginev51.config import PROJECT_ROOT, Settings

log = structlog.get_logger(__name__)

_DEFAULT_TABLE = PROJECT_ROOT / "config" / "letf_aum.toml"
STALE_DAYS = 90


def rebalance_demand_usd(leverage: float, aum_usd: float, r_day: float) -> float:
    """USD of index exposure the fund must trade into the close.

    Returns ``(L² − L) · AUM · r``. Positive = the fund must BUY the index,
    negative = must SELL. Works for inverse funds (L < 0) unchanged.

    Example (SOXL, L=3, AUM=$10B, index +2% on the day):
        (9 − 3) · 10e9 · 0.02 = +$1.2B  → the fund buys $1.2B of semis into 16:00.
    """
    L = float(leverage)
    return (L * L - L) * float(aum_usd) * float(r_day)


def _table_path(source: Settings | Path | str | None) -> Path:
    if source is None or isinstance(source, Settings):
        return _DEFAULT_TABLE
    return Path(source)


def load_aum_table(source: Settings | Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Load config/letf_aum.toml → {TICKER: {leverage, aum_usd, index, as_of, source}}.

    `source` may be a Settings (uses the repo default), a path/str to a toml
    file, or None (repo default).
    """
    with open(_table_path(source), "rb") as f:
        raw = tomllib.load(f)
    return dict(raw.get("etf", {}))


def _as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def staleness_check(
    table: dict[str, dict[str, Any]], *, today: date | None = None
) -> list[tuple[str, date, int]]:
    """Warn (structlog) for every ETF whose `as_of` is older than STALE_DAYS.

    Returns the list of stale entries as (ticker, as_of_date, age_days), so
    callers/tests can assert on it without scraping logs.
    """
    ref = today or date.today()
    stale: list[tuple[str, date, int]] = []
    for ticker, row in table.items():
        as_of = _as_date(row.get("as_of"))
        if as_of is None:
            log.warning("letf_aum_missing_as_of", ticker=ticker)
            continue
        age = (ref - as_of).days
        if age > STALE_DAYS:
            stale.append((ticker, as_of, age))
            log.warning(
                "letf_aum_stale",
                ticker=ticker,
                as_of=as_of.isoformat(),
                age_days=age,
                stale_days=STALE_DAYS,
            )
    return stale


def complex_demand(
    source: Settings | Path | str | None,
    index_returns: dict[str, float],
) -> dict[str, dict[str, Any]]:
    """Aggregate close-rebalance demand per index basket.

    `index_returns` maps an index label (matching the table's `index` field,
    e.g. "SOXX", "QQQ") to that basket's day return. Returns

        {index: {"demand_usd": <net $ to buy(+)/sell(−)>,
                 "per_etf": {TICKER: <$ demand>, ...}}}

    Only indices present in `index_returns` are returned; ETFs whose index has
    no supplied return are skipped.
    """
    table = load_aum_table(source)
    staleness_check(table)
    out: dict[str, dict[str, Any]] = {}
    for ticker, row in table.items():
        index = row["index"]
        if index not in index_returns:
            continue
        demand = rebalance_demand_usd(
            row["leverage"], row["aum_usd"], index_returns[index]
        )
        bucket = out.setdefault(index, {"demand_usd": 0.0, "per_etf": {}})
        bucket["demand_usd"] += demand
        bucket["per_etf"][ticker] = demand
    return out
