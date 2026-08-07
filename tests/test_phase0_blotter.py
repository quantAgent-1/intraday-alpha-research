"""Tests for apps/phase0_blotter.py -- the M16 Phase-0 manual execution blotter.

No network, no broker: `log`/`status`/`plan` are exercised through their pure
business-logic functions (mirroring test_forward_paper.py's convention) against
fabricated rows and a temp CSV; `reconcile` is exercised ONLY at the nearest-quote
selection + markout math layer, against synthetic quote frames -- no AlpacaHist,
no httpx, per the task's test scope.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pytest

from enginev51.apps import phase0_blotter as pb

ET = pb.ET_ZONE


def _dt(h: int, m: int, s: int = 0, d: date = date(2026, 7, 21)) -> datetime:
    return datetime(d.year, d.month, d.day, h, m, s, tzinfo=ET)


# --------------------------------------------------------------------------- bucket derivation


def test_bucket_of_boundaries():
    # MID = [13:00:00, 14:30:00)
    assert pb.bucket_of(time(13, 0, 0)) == "MID"
    assert pb.bucket_of(time(13, 29, 59)) == "MID"
    assert pb.bucket_of(time(14, 30, 0)) == "OTHER"  # end exclusive
    # LAST15 = [15:45:00, 16:00:00)
    assert pb.bucket_of(time(15, 45, 0)) == "LAST15"
    assert pb.bucket_of(time(15, 59, 59)) == "LAST15"
    assert pb.bucket_of(time(16, 0, 0)) == "OTHER"  # end exclusive
    # sanity: clearly outside both
    assert pb.bucket_of(time(12, 0, 0)) == "OTHER"
    assert pb.bucket_of(time(9, 30, 0)) == "OTHER"


def test_champion_window_boundary():
    assert pb.is_champion_window(time(15, 55, 10)) is True  # start inclusive
    assert pb.is_champion_window(time(15, 57, 59)) is True
    assert pb.is_champion_window(time(15, 58, 0)) is False  # end exclusive
    assert pb.is_champion_window(time(15, 55, 9)) is False


# --------------------------------------------------------------------------- E/Q math


def test_compute_spread_fields_hand_computed():
    out = pb.compute_spread_fields(100.00, 100.10, 100.02)
    mid = 100.05
    q_bps = (100.10 - 100.00) / mid * 1e4
    e_bps = 2 * abs(100.02 - mid) / mid * 1e4
    assert out["mid"] == pytest.approx(mid, abs=1e-9)
    assert out["q_bps"] == pytest.approx(q_bps, abs=1e-9)
    assert out["half_spread_bps"] == pytest.approx(q_bps / 2, abs=1e-9)
    assert out["e_bps"] == pytest.approx(e_bps, abs=1e-9)
    assert out["eq_ratio"] == pytest.approx(e_bps / q_bps, abs=1e-9)


def test_compute_spread_fields_unfilled_has_no_e_or_eq():
    out = pb.compute_spread_fields(100.00, 100.10, None)
    assert out["mid"] == pytest.approx(100.05)
    assert out["q_bps"] is not None
    assert out["e_bps"] is None
    assert out["eq_ratio"] is None


def test_compute_spread_fields_guards_degenerate_quotes():
    # locked market: q_bps == 0 -> eq_ratio must not divide by zero
    out = pb.compute_spread_fields(100.00, 100.00, 100.00)
    assert out["q_bps"] == 0.0
    assert out["eq_ratio"] is None
    # non-positive quotes -> everything null, no crash
    out2 = pb.compute_spread_fields(0.0, 0.0, 10.0)
    assert out2 == {"mid": None, "q_bps": None, "half_spread_bps": None, "e_bps": None, "eq_ratio": None}


# --------------------------------------------------------------------------- coin-flip determinism


def test_coin_flip_deterministic_same_ordinal():
    for ordinal in (1, 2, 5, 42, 250):
        first = pb.coin_flip_order_type(ordinal)
        for _ in range(5):
            assert pb.coin_flip_order_type(ordinal) == first
    assert pb.coin_flip_order_type(1) in ("market", "mlim")


def test_coin_flip_roughly_50_50_over_200():
    counts = {"market": 0, "mlim": 0}
    for ordinal in range(1, 201):
        counts[pb.coin_flip_order_type(ordinal)] += 1
    assert counts["market"] + counts["mlim"] == 200
    # generous tolerance -- this is a coin flip, not a strict balance requirement
    assert 70 <= counts["market"] <= 130
    assert 70 <= counts["mlim"] <= 130


# --------------------------------------------------------------------------- validation / warn flags


def test_validate_leg_notional_band_warn_only():
    # below band
    reasons = pb.validate_leg(
        bid=100.0, ask=100.05, size=3, unfilled=False, arm="A", otype="market",
        bucket="MID", notional=300.0,
    )
    assert "notional_out_of_400_800_band" in reasons
    # boundary values are inside the band (inclusive) -> no warn
    for boundary in (400.0, 800.0):
        reasons = pb.validate_leg(
            bid=100.0, ask=100.05, size=3, unfilled=False, arm="A", otype="market",
            bucket="MID", notional=boundary,
        )
        assert "notional_out_of_400_800_band" not in reasons


def test_validate_leg_crossed_and_size_and_bucket():
    reasons = pb.validate_leg(
        bid=100.10, ask=100.00, size=0, unfilled=False, arm="A", otype="market",
        bucket="OTHER", notional=None,
    )
    assert "crossed_or_locked_nbbo" in reasons
    assert "non_positive_size" in reasons
    assert "bucket_other" in reasons


def test_validate_leg_unfilled_only_expected_for_armB_rest():
    reasons = pb.validate_leg(
        bid=100.0, ask=100.05, size=3, unfilled=True, arm="A", otype="market",
        bucket="MID", notional=500.0,
    )
    assert "unfilled_not_armB_rest" in reasons
    reasons_ok = pb.validate_leg(
        bid=100.0, ask=100.05, size=3, unfilled=True, arm="B", otype="rest",
        bucket="MID", notional=500.0,
    )
    assert "unfilled_not_armB_rest" not in reasons_ok


def test_check_fill_args():
    assert pb.check_fill_args(None, None, True) is None  # unfilled, no fill info: ok
    assert pb.check_fill_args(100.0, None, True) is not None  # unfilled + fill info: bad
    assert pb.check_fill_args(100.0, "13:05:00", False) is None  # filled, both given: ok
    assert pb.check_fill_args(None, "13:05:00", False) is not None  # missing price
    assert pb.check_fill_args(100.0, None, False) is not None  # missing time
    assert pb.check_fill_args(None, None, False) is not None  # missing both


# --------------------------------------------------------------------------- log -> status round trip


def test_log_round_trip_on_temp_csv(tmp_path):
    path = tmp_path / "blotter.csv"
    rows: list[dict] = []

    def _log(**kw):
        nonlocal rows
        leg = pb.build_leg_row(rows, **kw)
        pb.append_leg_row(path, leg)
        rows = pb.load_rows(path)
        return leg

    common = dict(session_date=date(2026, 7, 21), venue="", note="")
    # clip 1: arm A market, MID bucket, round trip
    _log(clip_id=1, symbol="nvda", side="buy", arm="A", otype="market", bid=100.00, ask=100.10,
         send_time=_dt(13, 5, 0), fill_price=100.10, fill_time=_dt(13, 5, 1), size=5,
         unfilled=False, **common)
    _log(clip_id=1, symbol="nvda", side="sell", arm="A", otype="market", bid=100.20, ask=100.30,
         send_time=_dt(13, 6, 0), fill_price=100.20, fill_time=_dt(13, 6, 1), size=5,
         unfilled=False, **common)
    # clip 2: arm B rest, LAST15 bucket, round trip
    _log(clip_id=2, symbol="TSLA", side="buy", arm="B", otype="rest", bid=200.00, ask=200.10,
         send_time=_dt(15, 50, 0), fill_price=200.00, fill_time=_dt(15, 50, 30), size=2,
         unfilled=False, **common)
    _log(clip_id=2, symbol="TSLA", side="sell", arm="B", otype="market", bid=200.20, ask=200.30,
         send_time=_dt(15, 51, 0), fill_price=200.20, fill_time=_dt(15, 51, 1), size=2,
         unfilled=False, **common)

    loaded = pb.load_rows(path)
    assert len(loaded) == 4
    assert loaded[0]["symbol"] == "NVDA"  # uppercased
    assert loaded[0]["bucket"] == "MID"
    assert loaded[2]["bucket"] == "LAST15"

    stats = pb.compute_status(loaded)
    assert stats["total_clips"] == 2
    assert stats["bucket_counts"] == {"MID": 1, "LAST15": 1}
    assert stats["arm_counts"] == {"A": 1, "B": 1}
    assert stats["n_sessions"] == 1
    assert stats["open_clips"] == 0
    # format smoke -- must not crash
    text = pb.format_status_text(stats)
    assert "total clips: 2" in text


def test_append_never_rewrites_existing_rows(tmp_path):
    path = tmp_path / "blotter.csv"
    leg1 = pb.build_leg_row(
        [], clip_id=1, symbol="NVDA", side="buy", arm="A", otype="market", bid=100.0, ask=100.1,
        send_time=_dt(13, 5, 0), fill_price=100.1, fill_time=_dt(13, 5, 1), size=5,
        unfilled=False, session_date=date(2026, 7, 21),
    )
    pb.append_leg_row(path, leg1)
    before = path.read_text(encoding="utf-8")
    rows = pb.load_rows(path)
    leg2 = pb.build_leg_row(
        rows, clip_id=1, symbol="NVDA", side="sell", arm="A", otype="market", bid=100.2, ask=100.3,
        send_time=_dt(13, 6, 0), fill_price=100.2, fill_time=_dt(13, 6, 1), size=5,
        unfilled=False, session_date=date(2026, 7, 21),
    )
    pb.append_leg_row(path, leg2)
    after = path.read_text(encoding="utf-8")
    assert after.startswith(before)  # first row's bytes are untouched, only appended to
    assert leg2["leg_id"] == 2


# --------------------------------------------------------------------------- unfilled arm-B post handling


def test_unfilled_armB_post_has_no_eq_and_is_not_a_clip(tmp_path):
    path = tmp_path / "blotter.csv"
    leg = pb.build_leg_row(
        [], clip_id=1, symbol="MU", side="buy", arm="B", otype="rest", bid=50.00, ask=50.05,
        send_time=_dt(13, 10, 0), fill_price=None, fill_time=None, size=10,
        unfilled=True, session_date=date(2026, 7, 21),
    )
    assert leg["e_bps"] is None
    assert leg["eq_ratio"] is None
    assert leg["fill_price"] is None
    assert leg["warn"] is False  # unfilled + armB + rest is the EXPECTED shape
    pb.append_leg_row(path, leg)

    rows = pb.load_rows(path)
    assert pb.closed_clip_pairs(rows) == []  # never became a round trip
    assert pb.open_clips(rows) == []  # NOT "open" either -- it's a post-event
    posts = pb.armB_posts(rows)
    assert len(posts) == 1 and posts[0]["unfilled"] is True

    stats = pb.compute_status(rows)
    assert stats["total_clips"] == 0
    assert stats["armB_n_posts"] == 1
    assert stats["armB_n_filled"] == 0
    assert stats["armB_fill_rate"] == 0.0


def test_filled_armB_post_is_open_until_flattened(tmp_path):
    path = tmp_path / "blotter.csv"
    leg = pb.build_leg_row(
        [], clip_id=1, symbol="MU", side="buy", arm="B", otype="rest", bid=50.00, ask=50.05,
        send_time=_dt(13, 10, 0), fill_price=50.00, fill_time=_dt(13, 10, 45), size=10,
        unfilled=False, session_date=date(2026, 7, 21),
    )
    pb.append_leg_row(path, leg)
    rows = pb.load_rows(path)
    assert len(pb.open_clips(rows)) == 1
    assert len(pb.armB_posts(rows)) == 1
    assert pb.armB_posts(rows)[0]["unfilled"] is False


# --------------------------------------------------------------------------- plan


def test_build_plan_bootstraps_from_empty():
    plan = pb.build_plan([])
    assert plan["action"] == "enter"
    assert plan["clip_id"] == 1
    assert plan["arm"] == "A"  # tie -> A
    assert plan["bucket"] == "MID"  # tie -> MID
    assert plan["symbol"] == "NVDA"  # tie -> first listed
    assert plan["otype"] == pb.coin_flip_order_type(1)
    text = pb.format_plan(plan)
    assert "NEXT CLIP: #1" in text
    assert "LIMITS (frozen)" in text


def test_build_plan_recommends_flatten_when_open():
    entry = pb.build_leg_row(
        [], clip_id=7, symbol="AMD", side="buy", arm="A", otype="market", bid=10.0, ask=10.02,
        send_time=_dt(13, 0, 5), fill_price=10.02, fill_time=_dt(13, 0, 6), size=40,
        unfilled=False, session_date=date(2026, 7, 21),
    )
    plan = pb.build_plan([entry])
    assert plan["action"] == "flatten"
    assert plan["clip_id"] == 7
    assert plan["symbol"] == "AMD"
    assert plan["side"] == "sell"
    text = pb.format_plan(plan)
    assert "FLATTEN clip #7" in text


def test_recommend_bucket_and_arm_pick_undersampled():
    closed = []
    for i in range(3):
        entry = pb.build_leg_row(
            [], clip_id=i, symbol="NVDA", side="buy", arm="A", otype="market", bid=10.0, ask=10.02,
            send_time=_dt(13, 5, 0), fill_price=10.02, fill_time=_dt(13, 5, 1), size=40,
            unfilled=False, session_date=date(2026, 7, 21),
        )
        closed.append({"entry": entry, "exit": entry})
    assert pb.recommend_bucket(closed) == "LAST15"  # all logged MID so far -> recommend LAST15
    assert pb.recommend_arm(closed) == "B"  # all logged A so far -> recommend B


def test_recommend_symbol_prefers_least_logged():
    closed = []
    for sym in ("NVDA", "NVDA", "TSLA"):
        entry = pb.build_leg_row(
            [], clip_id=1, symbol=sym, side="buy", arm="A", otype="market", bid=10.0, ask=10.02,
            send_time=_dt(13, 5, 0), fill_price=10.02, fill_time=_dt(13, 5, 1), size=40,
            unfilled=False, session_date=date(2026, 7, 21),
        )
        closed.append({"entry": entry, "exit": entry})
    # NVDA=2, TSLA=1, AMD=0, MU=0, GOOGL=0 -> least-logged, tie -> AMD (listed before MU/GOOGL)
    assert pb.recommend_symbol(closed) == "AMD"


# --------------------------------------------------------------------------- status: wilson CI


def test_wilson_ci_known_values():
    lo, hi = pb.wilson_ci(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-3)
    assert hi == pytest.approx(0.7634, abs=1e-3)
    nan_lo, nan_hi = pb.wilson_ci(0, 0)
    assert nan_lo != nan_lo  # nan
    assert nan_hi != nan_hi
    lo2, hi2 = pb.wilson_ci(10, 10)
    assert hi2 == pytest.approx(1.0, abs=1e-9)
    assert 0.0 < lo2 < 1.0


def test_status_armB_fill_rate_and_thresholds():
    rows = []
    # 8 filled, 2 unfilled -> fill_rate 0.8 -> reopen candidate
    for i in range(8):
        rows.append(pb.build_leg_row(
            [], clip_id=i, symbol="MU", side="buy", arm="B", otype="rest", bid=50.0, ask=50.05,
            send_time=_dt(13, 10, 0), fill_price=50.0, fill_time=_dt(13, 10, 30), size=10,
            unfilled=False, session_date=date(2026, 7, 21),
        ))
    for i in range(8, 10):
        rows.append(pb.build_leg_row(
            [], clip_id=i, symbol="MU", side="buy", arm="B", otype="rest", bid=50.0, ask=50.05,
            send_time=_dt(13, 10, 0), fill_price=None, fill_time=None, size=10,
            unfilled=True, session_date=date(2026, 7, 21),
        ))
    stats = pb.compute_status(rows)
    assert stats["armB_n_posts"] == 10
    assert stats["armB_n_filled"] == 8
    assert stats["armB_fill_rate"] == pytest.approx(0.8)
    assert stats["armB_reopen_candidate"] is True
    assert stats["armB_close_candidate"] is False


# --------------------------------------------------------------------------- max concurrent exposure


def test_max_concurrent_exposure_sanity_check():
    rows = []
    # clip 1: $500 notional, open 13:00:00 - 13:02:00
    rows.append(pb.build_leg_row(
        [], clip_id=1, symbol="NVDA", side="buy", arm="A", otype="market", bid=99.9, ask=100.1,
        send_time=_dt(13, 0, 0), fill_price=100.0, fill_time=_dt(13, 0, 0), size=5,
        unfilled=False, session_date=date(2026, 7, 21),
    ))
    rows.append(pb.build_leg_row(
        [], clip_id=1, symbol="NVDA", side="sell", arm="A", otype="market", bid=100.1, ask=100.3,
        send_time=_dt(13, 2, 0), fill_price=100.2, fill_time=_dt(13, 2, 0), size=5,
        unfilled=False, session_date=date(2026, 7, 21),
    ))
    # clip 2: overlaps clip 1 (opens 13:01:00, before clip1 flattens at 13:02:00): $600 notional
    rows.append(pb.build_leg_row(
        [], clip_id=2, symbol="TSLA", side="buy", arm="A", otype="market", bid=199.9, ask=200.1,
        send_time=_dt(13, 1, 0), fill_price=200.0, fill_time=_dt(13, 1, 0), size=3,
        unfilled=False, session_date=date(2026, 7, 21),
    ))
    rows.append(pb.build_leg_row(
        [], clip_id=2, symbol="TSLA", side="sell", arm="A", otype="market", bid=200.1, ask=200.3,
        send_time=_dt(13, 3, 0), fill_price=200.2, fill_time=_dt(13, 3, 0), size=3,
        unfilled=False, session_date=date(2026, 7, 21),
    ))
    peak, exceeded = pb.max_concurrent_exposure(rows)
    # overlap window [13:01:00,13:02:00): clip1 $500 (100.0*5) + clip2 $600 (200.0*3) = $1100
    assert peak == pytest.approx(1100.0)
    assert exceeded is True


def test_max_concurrent_exposure_empty():
    assert pb.max_concurrent_exposure([]) == (0.0, False)


# --------------------------------------------------------------------------- reconcile: nearest-quote + markout


def _q(h, m, s, bid, ask, d=date(2026, 7, 21)):
    return {"ts": _dt(h, m, s, d), "bid": bid, "ask": ask}


def test_nearest_quote_at_or_before():
    quotes = [_q(13, 0, 0, 100.0, 100.1), _q(13, 0, 5, 100.1, 100.2), _q(13, 0, 10, 100.2, 100.3)]
    # exact match
    got = pb.nearest_quote_at_or_before(quotes, _dt(13, 0, 5))
    assert got["bid"] == 100.1
    # between two quotes -> the earlier one
    got2 = pb.nearest_quote_at_or_before(quotes, _dt(13, 0, 7))
    assert got2["bid"] == 100.1
    # before all quotes -> None
    assert pb.nearest_quote_at_or_before(quotes, _dt(12, 59, 0)) is None
    # after all quotes -> the last one
    got3 = pb.nearest_quote_at_or_before(quotes, _dt(13, 5, 0))
    assert got3["bid"] == 100.2
    # empty quotes -> None
    assert pb.nearest_quote_at_or_before([], _dt(13, 0, 0)) is None


def test_sip_ground_truth_crossed_flag():
    quotes = [_q(13, 0, 0, 100.10, 100.05)]  # crossed: bid > ask
    gt = pb.sip_ground_truth(quotes, _dt(13, 0, 1))
    assert gt["crossed"] is True
    assert gt["sip_mid"] == pytest.approx(100.075)


def test_markout_bps_formula_buy_and_short():
    # buy: price rises after fill -> positive (favorable) markout
    up = pb.markout_bps("buy", 100.0, 100.10)
    assert up == pytest.approx((100.10 - 100.0) / 100.0 * 1e4)
    down = pb.markout_bps("buy", 100.0, 99.90)
    assert down == pytest.approx((99.90 - 100.0) / 100.0 * 1e4)
    assert down < 0
    # short: price falling after fill is favorable -> positive markout
    short_fav = pb.markout_bps("short", 100.0, 99.90)
    assert short_fav > 0
    assert short_fav == pytest.approx(-1.0 * (99.90 - 100.0) / 100.0 * 1e4)


def test_compute_markout_for_fill_window_rules():
    fill_time = _dt(13, 0, 0)
    # a quote lands at +3s (inside the 1-5s window) -> used
    quotes = [_q(13, 0, 3, 100.0, 100.02)]
    m = pb.compute_markout_for_fill(quotes, "buy", 100.0, fill_time)
    assert m is not None
    assert m == pytest.approx((100.01 - 100.0) / 100.0 * 1e4)

    # only a quote at +0.5s (before the window opens) and nothing after -> None,
    # not a stale pre-window price
    quotes_stale = [{"ts": fill_time + timedelta(seconds=0.5), "bid": 100.0, "ask": 100.02}]
    assert pb.compute_markout_for_fill(quotes_stale, "buy", 100.0, fill_time) is None

    # no quotes at all in range -> None
    assert pb.compute_markout_for_fill([], "buy", 100.0, fill_time) is None


def test_build_reconcile_rows_end_to_end_synthetic():
    quotes = [_q(13, 0, 0, 100.0, 100.02), _q(13, 0, 3, 100.02, 100.04)]
    row_entry = pb.build_leg_row(
        [], clip_id=1, symbol="NVDA", side="buy", arm="B", otype="rest", bid=99.9, ask=100.1,
        send_time=_dt(13, 0, 0), fill_price=100.0, fill_time=_dt(13, 0, 0), size=5,
        unfilled=False, session_date=date(2026, 7, 21),
    )
    row_exit = pb.build_leg_row(
        [row_entry], clip_id=1, symbol="NVDA", side="sell", arm="B", otype="market",
        bid=100.2, ask=100.4, send_time=_dt(13, 5, 0), fill_price=100.3, fill_time=_dt(13, 5, 1),
        size=5, unfilled=False, session_date=date(2026, 7, 21),
    )
    results = pb.build_reconcile_rows([row_entry, row_exit], quotes)
    assert len(results) == 2
    entry_res, exit_res = results
    # entry: arm-B filled buy -> markout computed from the +3s quote
    assert entry_res["markout_bps"] is not None
    # exit leg is not an entry side -> no markout even though arm B
    assert exit_res["markout_bps"] is None
    # screen mid (99.9+100.1)/2=100.0 vs sip mid at send_time (13:00:00) = 100.01 -> within 1 tick
    assert entry_res["flag"] == "ok"


# --------------------------------------------------------------------------- report render smoke


def test_render_reconcile_report_smoke():
    results = [{
        "leg_id": 1, "clip_id": 1, "symbol": "NVDA", "side": "buy", "send_time": _dt(13, 0, 0),
        "screen_mid": 100.0, "sip_mid": 100.01, "diff_ticks": 1.0, "flag": "ok", "markout_bps": None,
    }]
    text = pb.render_reconcile_report("2026-07-21", results, session_dates=["2026-07-21"])
    assert "M16 Phase-0 reconciliation" in text
    assert "legs reconciled: 1" in text


def test_format_status_text_empty_smoke():
    stats = pb.compute_status([])
    text = pb.format_status_text(stats)
    assert "total clips: 0" in text
    assert "n=0" in text
