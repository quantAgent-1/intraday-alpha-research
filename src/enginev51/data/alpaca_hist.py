"""Alpaca Market Data v2 historical REST client (sync; used by backfill only).

Free-tier realities this client encodes:
- ~200 req/min → sliding-window limiter at settings.hist_requests_per_minute.
- Historical SIP data is allowed EXCEPT the most recent ~15 min → SIP request
  end-times are clamped to now − sip_recency_margin_minutes.
- 429 → honor Retry-After; 5xx → exponential backoff; both bounded.

Responses are normalized into the store schemas (ts = UTC epoch ns).
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog

from enginev51.config import Settings

log = structlog.get_logger(__name__)

_RFC3339 = "%Y-%m-%dT%H:%M:%SZ"


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime(_RFC3339)


def _parse_ts_ns(t: str) -> int:
    """RFC-3339 with up to ns precision → UTC epoch ns (stdlib fromisoformat handles ns since 3.11)."""
    dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
    epoch_s = int(dt.timestamp())
    return epoch_s * 1_000_000_000 + dt.microsecond * 1_000 + _sub_micro_ns(t)


def _sub_micro_ns(t: str) -> int:
    """fromisoformat truncates below µs; recover the ns residue from the raw string."""
    if "." not in t:
        return 0
    frac = t.split(".", 1)[1].rstrip("Z").split("+", 1)[0].split("-", 1)[0]
    if len(frac) <= 6:
        return 0
    frac = (frac + "000000000")[:9]
    return int(frac[6:9])


class RateLimiter:
    """Sliding-window limiter: at most `per_minute` acquisitions in any 60 s window."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._stamps: deque[float] = deque()

    def acquire(self) -> None:
        now = time.monotonic()
        while self._stamps and now - self._stamps[0] > 60.0:
            self._stamps.popleft()
        if len(self._stamps) >= self.per_minute:
            sleep_for = 60.0 - (now - self._stamps[0]) + 0.05
            time.sleep(max(sleep_for, 0.0))
        self._stamps.append(time.monotonic())


class AlpacaHist:
    def __init__(self, settings: Settings) -> None:
        if not settings.alpaca_api_key or not settings.alpaca_api_secret:
            raise RuntimeError("ALPACA_API_KEY / ALPACA_API_SECRET missing from .env")
        self.settings = settings
        # v5.1: limiter honors settings.hist_requests_per_minute (Algo Trader Plus
        # default 2000/min; REST cap is 10k/min).
        self.limiter = RateLimiter(settings.hist_requests_per_minute)
        self.client = httpx.Client(
            base_url=settings.alpaca_data_url,
            headers={
                "APCA-API-KEY-ID": settings.alpaca_api_key,
                "APCA-API-SECRET-KEY": settings.alpaca_api_secret,
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    # ------------------------------------------------------------------ core

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        backoff = 2.0
        for attempt in range(8):
            self.limiter.acquire()
            try:
                resp = self.client.get(path, params=params)
            except httpx.TransportError as exc:
                log.warning("transport_error", path=path, attempt=attempt, error=str(exc))
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", "5"))
                log.warning("rate_limited", retry_after=retry_after)
                time.sleep(retry_after + 0.5)
                continue
            if resp.status_code >= 500:
                log.warning("server_error", status=resp.status_code, attempt=attempt)
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            # 4xx other than 429: unrecoverable for this request
            raise RuntimeError(f"Alpaca {resp.status_code} on {path}: {resp.text[:300]}")
        raise RuntimeError(f"Alpaca request failed after retries: {path}")

    def clamp_end_for_feed(self, end: datetime, feed: str) -> datetime:
        if feed.lower() != "sip":
            return end
        latest = datetime.now(UTC) - timedelta(
            minutes=self.settings.sip_recency_margin_minutes
        )
        return min(end, latest)

    # ------------------------------------------------------------------ bars

    def fetch_bars_multi(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        feed: str = "sip",
        timeframe: str = "1Min",
        adjustment: str = "raw",
    ) -> dict[str, list[dict]]:
        """All 1-min bars for `symbols` in [start, end), normalized per symbol.

        ``adjustment`` defaults to ``"raw"`` (S8 / SIM_AUDIT_2026-07-21 F1): fills
        execute on the raw tape, so a silently split+dividend back-adjusted bar
        lake puts every derived price anchor on the wrong scale. Total-return
        studies (e.g. momentum ranks) must ask for ``"all"`` EXPLICITLY.
        """
        end = self.clamp_end_for_feed(end, feed)
        if end <= start:
            return {s: [] for s in symbols}
        out: dict[str, list[dict]] = {s.upper(): [] for s in symbols}
        params: dict[str, Any] = {
            "symbols": ",".join(s.upper() for s in symbols),
            "timeframe": timeframe,
            "start": _iso(start),
            "end": _iso(end),
            "limit": 10000,
            "adjustment": adjustment,
            "feed": feed,
            "sort": "asc",
        }
        while True:
            data = self._get("/v2/stocks/bars", params)
            for sym, bars in (data.get("bars") or {}).items():
                rows = out.setdefault(sym.upper(), [])
                for b in bars:
                    rows.append(
                        {
                            "ts": _parse_ts_ns(b["t"]),
                            "open": float(b["o"]),
                            "high": float(b["h"]),
                            "low": float(b["l"]),
                            "close": float(b["c"]),
                            "volume": float(b["v"]),
                            "trade_count": int(b.get("n", 0)),
                            "vwap": float(b.get("vw", 0.0)),
                        }
                    )
            token = data.get("next_page_token")
            if not token:
                return out
            params["page_token"] = token

    # ----------------------------------------------------------------- ticks

    def fetch_trades(
        self, symbol: str, start: datetime, end: datetime, feed: str = "sip"
    ) -> Iterator[list[dict]]:
        """Yield pages of normalized trade rows for one symbol in [start, end)."""
        # v5.1: default feed SIP (market-data API access).
        end = self.clamp_end_for_feed(end, feed)
        if end <= start:
            return
        params: dict[str, Any] = {
            "start": _iso(start),
            "end": _iso(end),
            "limit": 10000,
            "feed": feed,
            "sort": "asc",
        }
        while True:
            data = self._get(f"/v2/stocks/{symbol.upper()}/trades", params)
            rows = [
                {
                    "ts": _parse_ts_ns(t["t"]),
                    "price": float(t["p"]),
                    "size": float(t["s"]),
                    "exchange": str(t.get("x", "")),
                    "conditions": "|".join(t.get("c") or []),
                    "tape": str(t.get("z", "")),
                }
                for t in (data.get("trades") or [])
            ]
            if rows:
                yield rows
            token = data.get("next_page_token")
            if not token:
                return
            params["page_token"] = token

    def fetch_quotes(
        self, symbol: str, start: datetime, end: datetime, feed: str = "sip"
    ) -> Iterator[list[dict]]:
        """Yield pages of normalized quote rows for one symbol in [start, end)."""
        # v5.1: default feed SIP (market-data API access).
        end = self.clamp_end_for_feed(end, feed)
        if end <= start:
            return
        params: dict[str, Any] = {
            "start": _iso(start),
            "end": _iso(end),
            "limit": 10000,
            "feed": feed,
            "sort": "asc",
        }
        while True:
            data = self._get(f"/v2/stocks/{symbol.upper()}/quotes", params)
            rows = [
                {
                    "ts": _parse_ts_ns(q["t"]),
                    "bid": float(q.get("bp", 0.0)),
                    "bid_size": float(q.get("bs", 0.0)),
                    "bid_exchange": str(q.get("bx", "")),
                    "ask": float(q.get("ap", 0.0)),
                    "ask_size": float(q.get("as", 0.0)),
                    "ask_exchange": str(q.get("ax", "")),
                    "conditions": "|".join(q.get("c") or []),
                    "tape": str(q.get("z", "")),
                }
                for q in (data.get("quotes") or [])
            ]
            if rows:
                yield rows
            token = data.get("next_page_token")
            if not token:
                return
            params["page_token"] = token

    def close(self) -> None:
        self.client.close()
