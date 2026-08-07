"""Round-trip cost model (bps) per symbol, for taker manual execution.

Primary model (promo economics, PROTOCOL §3):
RT cost = median RTH **NBBO** spread (entry at ask, exit at bid ⇒ one full
spread) + SEC/TAF sell-side fees (bps) + market-order slip (bps), with **zero
commission** (broker promo). The three research constants come from
`enginev51.config.get_research_config()` (commission_usd, sec_taf_sell_bps,
slippage_market_bps).

Spread source hierarchy:
1. `nbbo_sampled` — median over short SIP-quote windows sampled on recent
   sessions (free tier allows historical SIP; windows keep it cheap).
2. `fallback` — conservative constants.
IEX top-of-book is deliberately NOT used: IEX quotes ~2-3% of volume and its
book is several times wider than the NBBO — measured 24 bps on META vs ~1-2
real — so it overstates costs and would kill true edges (2026-07-13 lesson).

The post-promo non-US commission ladder is NOT part of the default
model; it lives in `stress_post_promo_ladder()` as a report-only annotation.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

import polars as pl
import structlog

from enginev51.config import Settings, get_research_config
from enginev51.data import calendar as cal
from enginev51.data.alpaca_hist import AlpacaHist

log = structlog.get_logger(__name__)
ET = ZoneInfo("America/New_York")

# v5.1: post-promo (non-promo) non-US-broker round-trip commission ladder, in
# bps. Report annotation only — never applied by the default cost model. Carried
# over from engineV5's ladder/causal_select stress arms (extra_cost_bps=14.0).
POST_PROMO_RT_COMMISSION_BPS = 14.0

FALLBACK_SPREAD_BPS: dict[str, float] = {
    "TSLA": 2.0, "NVDA": 1.5, "AMD": 2.0, "MU": 2.5, "AVGO": 2.0, "META": 2.0,
    "AMZN": 1.5, "GOOGL": 1.5, "PLTR": 3.0, "COIN": 4.0, "MSTR": 6.0, "SMCI": 5.0,
    "QQQ": 1.0, "SMH": 1.5, "SOXX": 2.0, "SPY": 0.5,
}
DEFAULT_SPREAD_BPS = 5.0


def _nbbo_cache_path(settings: Settings):
    p = settings.data_dir / "costs"  # v5.1: enginev5_data_dir -> data_dir
    p.mkdir(parents=True, exist_ok=True)
    return p / "nbbo_spreads.json"


def sample_nbbo_spreads(
    settings: Settings,
    symbols: list[str],
    n_days: int = 2,
    window_minutes: int = 3,
    window_starts_et: tuple[tuple[int, int], ...] = ((10, 0), (12, 30), (15, 0)),
    refresh: bool = False,
) -> dict[str, float]:
    """Median NBBO spread (bps) per symbol from short SIP-quote windows; cached."""
    cache = _nbbo_cache_path(settings)
    if cache.exists() and not refresh:
        stored = json.loads(cache.read_text())
        if all(s.upper() in stored["spreads"] for s in symbols):
            return {s.upper(): stored["spreads"][s.upper()] for s in symbols}

    today = datetime.now(UTC).date()
    days = cal.trading_days(today - timedelta(days=14), today - timedelta(days=1))[-n_days:]
    api = AlpacaHist(settings)
    spreads: dict[str, float] = {}
    for sym in symbols:
        sym = sym.upper()
        vals: list[float] = []
        for d in days:
            for hh, mm in window_starts_et:
                start = datetime.combine(d, dtime(hh, mm), tzinfo=ET)
                end = start + timedelta(minutes=window_minutes)
                for page in api.fetch_quotes(sym, start, end, feed="sip"):
                    df = pl.DataFrame(page).filter(
                        (pl.col("bid") > 0) & (pl.col("ask") > pl.col("bid"))
                    )
                    if df.height:
                        vals.extend(
                            df.select(
                                (
                                    (pl.col("ask") - pl.col("bid"))
                                    / ((pl.col("ask") + pl.col("bid")) / 2)
                                    * 1e4
                                ).alias("s")
                            )["s"].to_list()
                        )
        if len(vals) >= 500:
            ser = pl.Series(vals)
            spreads[sym] = round(float(ser.filter(ser < 100).median()), 3)
            log.info("nbbo_sampled", symbol=sym, n=len(vals), median_bps=spreads[sym])
        else:
            log.warning("nbbo_sample_thin", symbol=sym, n=len(vals))
    api.close()

    merged = {}
    if cache.exists():
        merged = json.loads(cache.read_text()).get("spreads", {})
    merged.update(spreads)
    cache.write_text(
        json.dumps(
            {"sampled_at": datetime.now(UTC).isoformat(), "days": [str(d) for d in days],
             "windows_et": list(window_starts_et), "window_minutes": window_minutes,
             "spreads": merged},
            indent=2,
        )
    )
    return {s.upper(): merged[s.upper()] for s in symbols if s.upper() in merged}


def cost_table(
    settings: Settings, symbols: list[str], *, sample_nbbo: bool = True
) -> dict[str, dict]:
    # v5.1: cost constants are protocol-bound; read them from research config
    # rather than the module-level SLIPPAGE_BPS that engineV5 hard-coded.
    rc = get_research_config()
    nbbo: dict[str, float] = {}
    if sample_nbbo:
        try:
            nbbo = sample_nbbo_spreads(settings, symbols)
        except Exception as exc:  # cost sampling must never block an experiment
            log.warning("nbbo_sampling_failed", error=str(exc))
    out: dict[str, dict] = {}
    for s in symbols:
        s = s.upper()
        if s in nbbo:
            spread, source = nbbo[s], "nbbo_sampled"
        else:
            spread, source = FALLBACK_SPREAD_BPS.get(s, DEFAULT_SPREAD_BPS), "fallback"
        # v5.1: zero commission (promo) + NBBO spread + SEC/TAF sell-side bps +
        # market-order slip bps. commission_usd is a per-trade dollar figure
        # (0.0 under the promo) surfaced for transparency; it adds no bps here.
        rt_cost_bps = round(spread + rc.sec_taf_sell_bps + rc.slippage_market_bps, 3)
        out[s] = {
            "spread_bps": round(spread, 3),
            "sec_taf_sell_bps": round(rc.sec_taf_sell_bps, 3),
            "slippage_market_bps": round(rc.slippage_market_bps, 3),
            "commission_usd": round(rc.commission_usd, 4),
            "rt_cost_bps": rt_cost_bps,
            "source": source,
        }
        log.info("cost", symbol=s, **out[s])
    return out


def stress_post_promo_ladder(
    table: dict[str, dict], extra_bps: float = POST_PROMO_RT_COMMISSION_BPS
) -> dict[str, dict]:
    """Report-only stress: annotate a `cost_table()` output with the non-US
    broker post-promo round-trip commission ladder (default 14 bps RT). NEVER
    used by the default cost model — this is a report annotation, so callers must
    opt in explicitly (engineV5 ledger 2026-07-13). Returns a new dict; the
    input table is left unmodified.

    v5.1: engineV5 kept this figure only as an ad-hoc `extra_cost_bps=14.0` in
    its ladder/causal_select stress arms; consolidated here as a named helper.
    """
    out: dict[str, dict] = {}
    for s, row in table.items():
        stressed = dict(row)
        stressed["post_promo_commission_bps"] = round(extra_bps, 3)
        stressed["rt_cost_bps_post_promo"] = round(row["rt_cost_bps"] + extra_bps, 3)
        out[s] = stressed
    return out
