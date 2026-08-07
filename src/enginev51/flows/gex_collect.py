"""Forward-only GEX snapshot collector (option chain → GammaMap rows on disk).

No historical option open-interest exists for the universe, so dealer-gamma
maps can only be built from snapshots taken from M1 forward. This module pulls a
live OPRA option-chain snapshot from Alpaca's v1beta1 option-snapshots endpoint,
parses each contract to the (strike, τ, sign, OI, IV, mult) arrays that
`flows.gex.compute_gamma_map` consumes, and persists both the contract-level
rows and a one-line GammaMap summary.

Self-contained httpx client on purpose — it must not touch `data.alpaca_hist`
(which is the historical-bars/ticks path). Read-only: the OI fallback hits the
`/v2/options/contracts` reference GET only; NO order endpoint is ever called.

PROTOCOL v6 §5: forward-collected features (GEX snapshots included) are BANNED
from any Stage A gated result. This data is a deploy-lens / named-payer
mechanism input, never a gate currency.
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import polars as pl
import structlog

from enginev51.config import Settings
from enginev51.flows import bs
from enginev51.flows.gex import GammaMap, compute_gamma_map

log = structlog.get_logger(__name__)

_ET = ZoneInfo("America/New_York")
_NS_PER_DAY = 86_400 * 1_000_000_000
_YEAR_NS = 365.25 * _NS_PER_DAY
DEFAULT_MULT = 100.0

# Contract-row parquet schema (fixed so empty/partial chains still write cleanly).
_CONTRACT_SCHEMA: dict[str, pl.DataType] = {
    "symbol": pl.Utf8,
    "strike": pl.Float64,
    "tau_years": pl.Float64,
    "sign": pl.Int64,
    "oi": pl.Float64,
    "iv": pl.Float64,
    "mult": pl.Float64,
    "expiry": pl.Utf8,
}


# --------------------------------------------------------------------------- parse


def _occ_parse(symbol: str) -> tuple[date, int, float] | None:
    """OCC option symbol → (expiry_date, sign, strike).

    Layout: <root><YYMMDD><C|P><strike*1000, 8 digits>. The trailing 15 chars
    are fixed-width regardless of root length, so we read from the end.
    sign = +1 call, −1 put.
    """
    tail = symbol[-15:]
    if len(tail) != 15 or not tail[:6].isdigit() or not tail[7:].isdigit():
        return None
    yy, mm, dd = int(tail[0:2]), int(tail[2:4]), int(tail[4:6])
    cp = tail[6].upper()
    if cp not in ("C", "P"):
        return None
    try:
        expiry = date(2000 + yy, mm, dd)
    except ValueError:
        return None
    sign = 1 if cp == "C" else -1
    strike = int(tail[7:]) / 1000.0
    return expiry, sign, strike


def _first(d: dict[str, Any], *keys: str) -> Any:
    """First present, non-None value among `keys` (camelCase/snake_case tolerant)."""
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _expiry_ns(expiry: date) -> int:
    """Expiry at 16:00 ET → UTC epoch ns."""
    dt = datetime(expiry.year, expiry.month, expiry.day, 16, 0, tzinfo=_ET)
    return int(dt.astimezone(UTC).timestamp() * 1_000_000_000)


def parse_option_snapshots(
    underlying: str,
    snapshots: dict[str, dict[str, Any]],
    spot: float,
    now_ns: int,
    *,
    expiry_within_days: int = 45,
    strike_band_pct: float = 0.25,
    oi_map: dict[str, float] | None = None,
    mult_default: float = DEFAULT_MULT,
) -> dict[str, Any]:
    """Pure parser: raw Alpaca option-snapshot dict → per-contract arrays.

    `snapshots` maps OCC symbol → snapshot payload. Open interest is taken from
    the snapshot (`openInterest`) when present, else from `oi_map` (the
    reference-contract fallback). Implied vol from `impliedVolatility`.

    Filters (all applied): OI > 0, IV > 0, |strike/spot − 1| ≤ strike_band_pct,
    0 < τ, expiry within `expiry_within_days` of now. Returns arrays aligned by
    contract plus scalar spot/ts. No network, no side effects.
    """
    oi_map = oi_map or {}
    max_expiry_ns = now_ns + int(expiry_within_days) * _NS_PER_DAY
    band = float(strike_band_pct)
    spot = float(spot)

    syms: list[str] = []
    strikes: list[float] = []
    taus: list[float] = []
    signs: list[int] = []
    ois: list[float] = []
    ivs: list[float] = []
    mults: list[float] = []
    expiries: list[str] = []

    for sym, snap in snapshots.items():
        if not isinstance(snap, dict):
            continue
        parsed = _occ_parse(sym)
        if parsed is None:
            continue
        expiry, sign, strike = parsed

        exp_ns = _expiry_ns(expiry)
        tau = (exp_ns - now_ns) / _YEAR_NS
        if tau <= 0.0 or exp_ns > max_expiry_ns:
            continue

        if spot > 0 and abs(strike / spot - 1.0) > band:
            continue

        iv_raw = _first(snap, "impliedVolatility", "implied_volatility", "iv")
        iv = float(iv_raw) if iv_raw is not None else 0.0
        if not (iv > 0.0):
            continue

        oi_raw = _first(snap, "openInterest", "open_interest", "oi")
        if oi_raw is None:
            oi_raw = oi_map.get(sym)
        oi = float(oi_raw) if oi_raw is not None else 0.0
        if not (oi > 0.0):
            continue

        mult_raw = _first(snap, "size", "multiplier", "mult")
        mult = float(mult_raw) if mult_raw is not None else float(mult_default)

        syms.append(sym)
        strikes.append(strike)
        taus.append(tau)
        signs.append(sign)
        ois.append(oi)
        ivs.append(iv)
        mults.append(mult)
        expiries.append(expiry.isoformat())

    return {
        "underlying": underlying.upper(),
        "spot": spot,
        "ts": int(now_ns),
        "symbol": syms,
        "strike": strikes,
        "tau_years": taus,
        "sign": signs,
        "oi": ois,
        "iv": ivs,
        "mult": mults,
        "expiry": expiries,
    }


# --------------------------------------------------------------------------- IO


def _headers(settings: Settings) -> dict[str, str]:
    return {
        "APCA-API-KEY-ID": settings.alpaca_api_key,
        "APCA-API-SECRET-KEY": settings.alpaca_api_secret,
        "Accept": "application/json",
    }


def _get_json(client: httpx.Client, url: str, params: dict[str, Any]) -> dict[str, Any]:
    resp = client.get(url, params=params)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Alpaca {resp.status_code} on {url}: {resp.text[:400]}"
        )
    return resp.json()


def _spot_from_snapshot(data: dict[str, Any]) -> float | None:
    trade = data.get("latestTrade") or {}
    px = trade.get("p")
    if px:
        return float(px)
    quote = data.get("latestQuote") or {}
    bid, ask = quote.get("bp"), quote.get("ap")
    if bid and ask:
        return (float(bid) + float(ask)) / 2.0
    return None


def _fetch_spot(client: httpx.Client, data_url: str, underlying: str, feeds: tuple[str, ...]) -> float:
    """Latest trade price (fallback: quote midpoint) for the underlying.

    Tries feeds in order — real-time SIP snapshots require a higher entitlement
    than tick history, so we fall back to iex (a spot reference is all we need).
    """
    url = f"{data_url}/v2/stocks/{underlying.upper()}/snapshot"
    last_err: Exception | None = None
    for feed in feeds:
        try:
            data = _get_json(client, url, {"feed": feed})
        except RuntimeError as exc:
            last_err = exc
            continue
        spot = _spot_from_snapshot(data)
        if spot is not None:
            return spot
        last_err = RuntimeError(f"no spot in {feed} snapshot for {underlying}")
    raise RuntimeError(f"spot fetch failed for {underlying}: {last_err}")


def _fetch_option_snapshots(
    client: httpx.Client,
    data_url: str,
    underlying: str,
    *,
    feed: str,
    expiry_within_days: int,
    spot: float,
    strike_band_pct: float,
) -> dict[str, dict[str, Any]]:
    """All OPRA option snapshots for `underlying`, server-side prefiltered + paged."""
    today = datetime.now(_ET).date()
    exp_lte = today.fromordinal(today.toordinal() + int(expiry_within_days)).isoformat()
    params: dict[str, Any] = {
        "feed": feed,
        "limit": 1000,
        "expiration_date_lte": exp_lte,
    }
    if spot > 0:
        params["strike_price_gte"] = round(spot * (1.0 - strike_band_pct), 2)
        params["strike_price_lte"] = round(spot * (1.0 + strike_band_pct), 2)

    url = f"{data_url}/v1beta1/options/snapshots/{underlying.upper()}"
    out: dict[str, dict[str, Any]] = {}
    while True:
        data = _get_json(client, url, params)
        out.update(data.get("snapshots") or {})
        token = data.get("next_page_token")
        if not token:
            return out
        params["page_token"] = token


def _fetch_oi_map(
    underlying: str, api_key: str, api_secret: str
) -> dict[str, float]:
    """Read-only OI fallback: /v2/options/contracts reference data, joined by symbol.

    Hits the trading-API contracts reference endpoint (GET only). Never an order
    endpoint. Uses the live trading host; paper host works identically for reads.
    """
    url = "https://paper-api.alpaca.markets/v2/options/contracts"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
        "Accept": "application/json",
    }
    params: dict[str, Any] = {"underlying_symbols": underlying.upper(), "limit": 10000}
    out: dict[str, float] = {}
    with httpx.Client(headers=headers, timeout=httpx.Timeout(30.0, connect=10.0)) as c:
        while True:
            data = _get_json(c, url, params)
            for row in data.get("option_contracts") or []:
                sym = row.get("symbol")
                oi = row.get("open_interest")
                if sym and oi is not None:
                    out[sym] = float(oi)
            token = data.get("next_page_token")
            if not token:
                return out
            params["page_token"] = token


def _mid_from_snapshot(snap: dict[str, Any]) -> float | None:
    q = snap.get("latestQuote") or {}
    bid, ask = q.get("bp"), q.get("ap")
    if bid and ask and float(bid) > 0 and float(ask) > 0:
        return (float(bid) + float(ask)) / 2.0
    t = snap.get("latestTrade") or {}
    px = t.get("p")
    return float(px) if px else None


def _recover_iv_inplace(
    snaps: dict[str, dict[str, Any]], spot: float, now_ns: int, r: float = 0.045
) -> int:
    """For snapshots lacking IV, invert Black-Scholes from the option mid.

    Mutates each snapshot dict, setting `impliedVolatility` when recoverable
    (bs.implied_vol returns nan for un-invertible mids → left unset → dropped by
    the OI/IV filter). This is the documented fallback for feeds (e.g. Alpaca
    `indicative`) that omit greeks. Returns the count recovered.
    """
    n = 0
    for sym, snap in snaps.items():
        if not isinstance(snap, dict):
            continue
        if _first(snap, "impliedVolatility", "implied_volatility", "iv") is not None:
            continue
        parsed = _occ_parse(sym)
        if parsed is None:
            continue
        expiry, sign, strike = parsed
        tau = (_expiry_ns(expiry) - now_ns) / _YEAR_NS
        if tau <= 0.0:
            continue
        mid = _mid_from_snapshot(snap)
        if mid is None or mid <= 0.0:
            continue
        iv = bs.implied_vol(mid, spot, strike, tau, r=r, is_call=(sign > 0))
        if iv == iv and iv > 0.0:  # not nan
            snap["impliedVolatility"] = float(iv)
            n += 1
    return n


def fetch_option_chain_snapshot(
    settings: Settings,
    underlying: str,
    *,
    expiry_within_days: int = 45,
    strike_band_pct: float = 0.25,
    feed: str = "opra",
) -> dict[str, Any]:
    """Live pull: spot + option-chain snapshot → parsed per-contract arrays.

    Primary feed is OPRA (greeks/IV/OI on the payload). If the account lacks the
    OPRA entitlement (403 subscription error), falls back to the free
    `indicative` feed and recovers IV from the option mid via Black-Scholes
    (bs.implied_vol) — real, delayed data, never synthesized. Open interest is
    joined from the read-only contracts reference endpoint whenever the snapshot
    payload omits it. Returns the dict produced by `parse_option_snapshots`.
    """
    underlying = underlying.upper()
    used_feed = feed
    with httpx.Client(
        headers=_headers(settings), timeout=httpx.Timeout(30.0, connect=10.0)
    ) as client:
        spot = _fetch_spot(
            client, settings.alpaca_data_url, underlying, feeds=("sip", "iex")
        )
        try:
            snaps = _fetch_option_snapshots(
                client, settings.alpaca_data_url, underlying, feed=feed,
                expiry_within_days=expiry_within_days, spot=spot,
                strike_band_pct=strike_band_pct,
            )
        except RuntimeError as exc:
            if feed == "opra" and "subscription" in str(exc).lower():
                log.warning("gex_opra_denied_fallback_indicative", underlying=underlying,
                            error=str(exc)[:200])
                used_feed = "indicative"
                snaps = _fetch_option_snapshots(
                    client, settings.alpaca_data_url, underlying, feed="indicative",
                    expiry_within_days=expiry_within_days, spot=spot,
                    strike_band_pct=strike_band_pct,
                )
            else:
                raise

    now_ns = time.time_ns()

    has_iv = any(
        _first(s, "impliedVolatility", "implied_volatility", "iv") is not None
        for s in snaps.values() if isinstance(s, dict)
    )
    if not has_iv:
        n_iv = _recover_iv_inplace(snaps, spot, now_ns)
        log.info("gex_iv_recovered", underlying=underlying, feed=used_feed, n=n_iv)

    has_oi = any(
        _first(s, "openInterest", "open_interest", "oi") is not None
        for s in snaps.values() if isinstance(s, dict)
    )
    oi_map: dict[str, float] | None = None
    if not has_oi:
        log.info("gex_oi_fallback", underlying=underlying, n_snapshots=len(snaps))
        oi_map = _fetch_oi_map(
            underlying, settings.alpaca_api_key, settings.alpaca_api_secret
        )

    return parse_option_snapshots(
        underlying,
        snaps,
        spot,
        now_ns,
        expiry_within_days=expiry_within_days,
        strike_band_pct=strike_band_pct,
        oi_map=oi_map,
    )


# --------------------------------------------------------------------------- persist


def _gex_dir(settings: Settings, underlying: str) -> Path:
    return settings.data_dir / "flows" / "gex" / underlying.upper()


def chain_to_gamma_map(underlying: str, chain: dict[str, Any], ts: int) -> GammaMap:
    """Build a GammaMap from a parsed chain dict."""
    return compute_gamma_map(
        symbol=underlying.upper(),
        ts=ts,
        spot=chain["spot"],
        strike=chain["strike"],
        tau=chain["tau_years"],
        sign=chain["sign"],
        oi=chain["oi"],
        sigma=chain["iv"],
        mult=chain["mult"],
    )


def snapshot_to_parquet(
    settings: Settings, underlying: str, chain: dict[str, Any], ts: int
) -> tuple[Path, GammaMap]:
    """Persist a chain snapshot: contract-level parquet + one GammaMap jsonl row.

    Writes data/flows/gex/{UNDERLYING}/{YYYY-MM-DD}T{HHMM}.parquet (ET-stamped,
    atomic tmp+replace) and appends the GammaMap summary to maps.jsonl. Returns
    (parquet_path, gamma_map).
    """
    underlying = underlying.upper()
    out_dir = _gex_dir(settings, underlying)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = {k: chain[k] for k in _CONTRACT_SCHEMA}
    df = pl.DataFrame(rows, schema=_CONTRACT_SCHEMA)
    if df.height:
        df = df.sort(["expiry", "strike", "sign"])

    stamp = datetime.fromtimestamp(ts / 1e9, tz=_ET).strftime("%Y-%m-%dT%H%M")
    path = out_dir / f"{stamp}.parquet"
    tmp = path.with_suffix(".parquet.tmp")
    df.write_parquet(tmp, compression="zstd")
    os.replace(tmp, path)

    gm = chain_to_gamma_map(underlying, chain, ts)
    summary = {
        "ts": int(ts),
        "spot": gm.spot,
        "net_gex": gm.net_gex,
        "regime": gm.regime,
        "gamma_flip": gm.gamma_flip,
        "call_wall": gm.call_wall,
        "put_wall": gm.put_wall,
        "pin": gm.pin,
        "n_contracts": int(len(chain["strike"])),
    }
    with open(out_dir / "maps.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")

    return path, gm
