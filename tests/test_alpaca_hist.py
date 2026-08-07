import inspect
import time
from datetime import UTC, datetime, timedelta

from enginev51.config import Settings
from enginev51.data.alpaca_hist import AlpacaHist, RateLimiter, _parse_ts_ns


def test_parse_ts_ns_nanosecond_precision() -> None:
    assert _parse_ts_ns("2026-01-02T14:30:00Z") == 1767364200 * 1_000_000_000
    ns = _parse_ts_ns("2026-01-02T14:30:00.123456789Z")
    assert ns == 1767364200 * 1_000_000_000 + 123_456_789
    micro_only = _parse_ts_ns("2026-01-02T14:30:00.123456Z")
    assert micro_only == 1767364200 * 1_000_000_000 + 123_456_000


def test_rate_limiter_blocks_over_budget() -> None:
    rl = RateLimiter(per_minute=3)
    t0 = time.monotonic()
    for _ in range(3):
        rl.acquire()
    assert time.monotonic() - t0 < 0.5  # first three are free


def test_fetch_bars_multi_defaults_to_raw_adjustment() -> None:
    # S8 / SIM_AUDIT_2026-07-21 F1: the old default was adjustment="all", which
    # silently back-adjusts a bar lake that fills price against the RAW tape. A
    # caller that says nothing must now get raw; total-return needs an explicit ask.
    assert (
        inspect.signature(AlpacaHist.fetch_bars_multi).parameters["adjustment"].default
        == "raw"
    )


def test_fetch_bars_multi_sends_the_requested_adjustment() -> None:
    # the parameter actually reaches the wire (both the new default and an override)
    s = Settings(alpaca_api_key="k", alpaca_api_secret="s")
    api = AlpacaHist(s)
    seen: list[dict] = []

    def _fake_get(path, params):  # noqa: ANN001
        seen.append(dict(params))
        return {"bars": {}, "next_page_token": None}

    api._get = _fake_get  # type: ignore[method-assign]
    start = datetime(2025, 1, 2, tzinfo=UTC)
    end = datetime(2025, 1, 3, tzinfo=UTC)
    api.fetch_bars_multi(["NVDA"], start, end, timeframe="1Day")
    api.fetch_bars_multi(["NVDA"], start, end, timeframe="1Day", adjustment="all")
    api.close()

    assert [p["adjustment"] for p in seen] == ["raw", "all"]


def test_letf_bars_pins_the_adjusted_lake_vintage() -> None:
    # Behaviour-preserving half of S8: every bars1m partition run_letf_bars has
    # written (LETF lake + the R2-A OOS names) came from the old adjustment="all"
    # default, so the writer now pins "all" EXPLICITLY rather than silently
    # flipping vintage under the new raw default. Changing it is a data migration.
    from enginev51.config import Settings as _S
    from enginev51.data import backfill

    captured: list[dict] = []

    class _Api:
        def fetch_bars_multi(self, symbols, start, end, **kw):  # noqa: ANN001, ANN003
            captured.append(kw)
            return {s: [] for s in symbols}

        def close(self) -> None:
            pass

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        backfill.run_letf_bars(_S(data_dir=td), [("SOXL", "2025-01")], api=_Api())
    assert captured == [{"feed": "sip", "adjustment": "all"}]


def test_sip_end_clamped() -> None:
    s = Settings(alpaca_api_key="k", alpaca_api_secret="s")
    api = AlpacaHist(s)
    now = datetime.now(UTC)
    clamped = api.clamp_end_for_feed(now, "sip")
    assert clamped <= now - timedelta(minutes=s.sip_recency_margin_minutes - 1)
    assert api.clamp_end_for_feed(now, "iex") == now
    api.close()
