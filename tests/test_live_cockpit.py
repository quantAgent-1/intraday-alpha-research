"""Tests for apps/live_cockpit.py -- the champion decision cockpit (SIGNAL-ONLY).

The pure decision core (basis math, direction, whole-share sizing, gate degradation,
top-3 note, spread-abort) is unit-tested including the boundary cases; the M8 P(win)
path is exercised with a tiny stub booster (no training, no network); and the rehearse
scoring is spot-asserted CONSISTENT with the forward_paper harness on synthetic frames.
Nothing here touches the network, the lake, or the research ledger.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
import pytest

from enginev51.apps import forward_paper as fp
from enginev51.apps import live_cockpit as lc
from enginev51.apps import run_basis_trial as rbt
from enginev51.models import moc_meta

ET = ZoneInfo("America/New_York")


class _StubBooster:
    """Minimal LightGBM-Booster shape for moc_meta.predict_pwin (returns a fixed p)."""

    def __init__(self, p: float) -> None:
        self.p = float(p)
        self.best_iteration = 0

    def predict(self, data, num_iteration=None):  # noqa: ANN001
        return np.full(data.shape[0], self.p, dtype=float)


# --------------------------------------------------------------------------- sizing


def test_size_shares_floor_and_clip_cap():
    # clip = min(capital, cap) = min(1200, 800) = 800; floor(800/100) = 8.
    assert lc.size_shares(1200.0, 800.0, 100.0) == 8
    # capital below the cap binds instead: min(500, 800) = 500; floor(500/100) = 5.
    assert lc.size_shares(500.0, 800.0, 100.0) == 5


def test_size_shares_rounds_to_zero_is_capital_insufficient():
    # MU-like: price ~$854 with an $800 clip cap -> 0 whole shares (honest NO-GO case).
    assert lc.size_shares(1200.0, 800.0, 854.26) == 0


def test_size_shares_nonpositive_price():
    assert lc.size_shares(1200.0, 800.0, 0.0) == 0
    assert lc.size_shares(1200.0, 800.0, None) == 0


# ----------------------------------------------------------------------- basis math


def test_market_mid_and_spread_bps():
    mid = lc.market_mid(99.99, 100.01)
    assert mid == pytest.approx(100.0)
    assert lc.spread_bps(99.99, 100.01, mid) == pytest.approx(2.0, abs=1e-6)


def test_direction_buy_when_near_above_mid():
    d = lc.classify_basis(105.0, 99.99, 100.01)  # near >> mid -> +500 bps
    assert d["direction"] == 1
    assert d["side_word"] == "BUY"
    assert d["basis_bps"] > 0
    assert d["classical_go"] is True


def test_direction_sell_when_near_below_mid():
    d = lc.classify_basis(95.0, 99.99, 100.01)  # near << mid -> -500 bps
    assert d["direction"] == -1
    assert d["side_word"] == "SELL SHORT"
    assert d["basis_bps"] < 0
    assert d["classical_go"] is True


def test_basis_exactly_threshold_is_go():
    # basis exactly +10.0 -> GO (rule is >=, so the boundary qualifies). near/mid chosen
    # so the float basis lands exactly on 10.0 (1001/1000), same >= semantics as the harness.
    d = lc.classify_basis(1001.0, 999.99, 1000.01)
    assert d["basis_bps"] == pytest.approx(10.0, abs=1e-9)
    assert d["basis_bps"] >= lc.BASIS_THRESHOLD_BPS
    assert d["classical_go"] is True


def test_basis_just_below_threshold_is_no_go():
    d = lc.classify_basis(100.09, 99.99, 100.01)  # ~ +9.0 bps
    assert abs(d["basis_bps"]) < lc.BASIS_THRESHOLD_BPS
    assert d["classical_go"] is False


def test_zero_basis_near_equals_mid_no_go():
    d = lc.classify_basis(100.0, 99.99, 100.01)  # near == mid == 100.0
    assert d["direction"] == 0
    assert d["classical_go"] is False
    assert "no tradable basis" in d["classical_reason"]


def test_crossed_quotes_no_go():
    d = lc.classify_basis(100.1, 100.02, 100.01)  # bid > ask
    assert any("crossed" in e for e in d["errors"])
    assert d["classical_go"] is False


def test_near_missing_or_nonpositive_no_go():
    for bad in (0.0, -5.0, None):
        d = lc.classify_basis(bad, 99.99, 100.01)
        assert any("near" in e for e in d["errors"])
        assert d["classical_go"] is False


# ----------------------------------------------------------------- meta degradation


def test_missing_meta_inputs_lists_all_when_none_supplied():
    missing = lc.missing_meta_inputs(
        far=None, ref=None, imbalance=None, paired=None, adv20=None,
        vol20=None, imb_growth_53=None, imb_growth_51=None, msg_count=None,
    )
    # every registered non-basis feature is unbuildable
    names = " ".join(missing)
    for feat in ("near_far_bps", "near_ref_bps", "paired_ratio", "norm_imb",
                 "imb_growth_53", "imb_growth_51", "msg_count", "vol20", "log_adv20"):
        assert feat in names


def test_missing_meta_inputs_empty_when_all_present():
    missing = lc.missing_meta_inputs(
        far=1.0, ref=1.0, imbalance=1.0, paired=1.0, adv20=1.0,
        vol20=1.0, imb_growth_53=1.0, imb_growth_51=1.0, msg_count=1.0,
    )
    assert missing == []


def test_build_meta_row_reuses_frozen_feature_path():
    row = lc.build_meta_row(
        "NVDA", "2026-07-17", near=201.0, mid=203.0,
        far=202.0, ref=202.5, imbalance=-500_000.0, paired=1_000_000.0,
        adv20=5e9, vol20=0.3, imb_growth_53=0.1, imb_growth_51=0.2, msg_count=40.0,
    )
    # exactly the registered feature columns, nothing else
    assert set(row) == set(moc_meta.FEATURE_COLS)
    # snapshot features match the frozen arithmetic
    assert row["basis_bps"] == pytest.approx(rbt.basis_bps_of(201.0, 203.0))
    assert row["oh_NVDA"] == 1.0 and row["oh_TSLA"] == 0.0
    # sell-side (negative) imbalance -> side -1; norm_imb uses the basis near price
    assert row["norm_imb"] == pytest.approx(-1 * 500_000.0 * 201.0 / 5e9)
    assert row["paired_ratio"] == pytest.approx(1_000_000.0 / (1_000_000.0 + 500_000.0))
    assert row["near_ref_bps"] == pytest.approx((201.0 - 202.5) / 202.5 * 1e4)


def test_compute_meta_model_absent_degrades():
    m = lc.compute_meta(None, "NVDA", "2026-07-17", 100.1, 100.0)
    assert m["available"] is False
    assert "model file absent" in m["reason"]


def test_compute_meta_missing_features_unavailable():
    m = lc.compute_meta(_StubBooster(0.7), "NVDA", "2026-07-17", 100.1, 100.0)  # no optional inputs
    assert m["available"] is False
    assert "P(win) unavailable (missing:" in m["reason"]


def test_compute_meta_available_go_and_no_go():
    kw = dict(
        far=202.0, ref=202.5, imbalance=-500_000.0, paired=1_000_000.0, adv20=5e9,
        vol20=0.3, imb_growth_53=0.1, imb_growth_51=0.2, msg_count=40.0,
    )
    go = lc.compute_meta(_StubBooster(0.70), "NVDA", "2026-07-17", 201.0, 203.0, **kw)
    assert go["available"] is True and go["go"] is True
    assert go["p_win"] == pytest.approx(0.70)
    nogo = lc.compute_meta(_StubBooster(0.40), "NVDA", "2026-07-17", 201.0, 203.0, **kw)
    assert nogo["available"] is True and nogo["go"] is False


# ------------------------------------------------------------------- decide_one glue


def test_decide_one_ticket_on_go():
    d = lc.decide_one("NVDA", 105.0, 99.99, 100.01, session_iso="2026-07-17", booster=None)
    assert d["classical_go"] is True
    assert d["ticket_ok"] is True
    assert d["side_word"] == "BUY"
    assert d["shares"] == lc.size_shares(1200.0, 800.0, 100.01)  # size off ask for a buy
    assert d["meta"]["available"] is False  # no model passed


def test_decide_one_spread_abort_blocks_ticket():
    # spread ~99.5 bps > 25 default; basis is a strong BUY, but the abort must block.
    d = lc.decide_one("NVDA", 110.0, 100.0, 101.0, session_iso="2026-07-17", booster=None)
    assert d["classical_go"] is True
    assert d["spread_abort"] is True
    assert d["ticket_ok"] is False
    assert "SPREAD ABORT" in d["ticket_block"]


def test_decide_one_capital_insufficient_blocks_ticket():
    # MU-like price with the $800 clip cap -> 0 whole shares.
    d = lc.decide_one("MU", 900.0, 856.0, 856.5, session_iso="2026-07-17", booster=None)
    assert d["classical_go"] is True
    assert d["shares"] == 0
    assert d["ticket_ok"] is False
    assert "capital insufficient" in d["ticket_block"]


def test_decide_one_below_threshold_no_ticket():
    d = lc.decide_one("NVDA", 100.05, 99.99, 100.01, session_iso="2026-07-17", booster=None)
    assert d["classical_go"] is False
    assert d["ticket_ok"] is False


# ------------------------------------------------------- B2: meta NO-GO blocks the ticket

# near 201.0 vs mid 203.0 -> basis -98.5 bps (classical SELL SHORT GO), spread ~1 bp
# (no abort), bid 202.99 -> 3 whole shares in an $800 clip. The ONLY thing that can
# block a ticket in this fixture is the meta gate.
_META_KW = dict(
    far=202.0, ref=202.5, imbalance=-500_000.0, paired=1_000_000.0, adv20=5e9,
    vol20=0.3, imb_growth_53=0.1, imb_growth_51=0.2, msg_count=40.0,
)


def _decide_with_meta(p_win: float) -> dict:
    return lc.decide_one(
        "NVDA", 201.0, 202.99, 203.01, session_iso="2026-07-17",
        booster=_StubBooster(p_win), **_META_KW,
    )


def test_decide_one_meta_nogo_blocks_ticket():
    # Module contract (header + checklist): with the M8 model loaded the champion
    # ALSO requires P(win) >= 0.55. P(win)=0.40 -> NO-GO -> no ORDER TICKET.
    # PRE-FIX ticket_ok stayed True and the cockpit printed a full ticket for a
    # meta-rejected clip (code review 2026-07-28 B2).
    d = _decide_with_meta(0.40)
    assert d["classical_go"] is True          # classical stream still fires
    assert d["spread_abort"] is False and d["shares"] >= 1  # nothing else blocks
    assert d["meta"]["available"] is True and d["meta"]["go"] is False
    assert d["ticket_ok"] is False
    assert "META NO-GO" in d["ticket_block"]


def test_spread_abort_outranks_meta_nogo_when_both_fire():
    """FIX 7 (code review 2026-08-01): a snapshot that fails BOTH must name the
    mechanical block. bid 200.00 / ask 201.00 -> mid 200.50, spread ~49.9 bps (>25
    abort) and near 195.0 -> basis ~-274 bps (classical SELL SHORT GO); P(win)=0.40
    is also a meta NO-GO. Before the reorder the operator was told the MODEL rejected
    the clip when in fact the BOOK was untradeable."""
    d = lc.decide_one(
        "NVDA", 195.0, 200.0, 201.0, session_iso="2026-07-17",
        booster=_StubBooster(0.40), **_META_KW,
    )
    # both conditions genuinely fire
    assert d["classical_go"] is True
    assert d["spread_abort"] is True
    assert d["meta"]["available"] is True and d["meta"]["go"] is False
    assert d["shares"] >= 1  # sizing is not what blocks it
    # the mechanical block wins the text; the ticket is refused either way
    assert "SPREAD ABORT" in d["ticket_block"]
    assert "META NO-GO" not in d["ticket_block"]
    assert d["ticket_ok"] is False


def test_meta_nogo_still_named_when_spread_is_fine():
    """The reorder must not swallow the B2 fix: with no abort, META NO-GO still
    blocks and still names itself (the pairing that pins the precedence, not just
    the winner)."""
    d = _decide_with_meta(0.40)
    assert d["spread_abort"] is False
    assert "META NO-GO" in d["ticket_block"]
    assert d["ticket_ok"] is False


def test_decide_one_meta_go_keeps_ticket():
    d = _decide_with_meta(0.70)
    assert d["meta"]["available"] is True and d["meta"]["go"] is True
    assert d["ticket_ok"] is True
    assert d["ticket_block"] is None
    assert d["side_word"] == "SELL SHORT"


def test_decide_one_meta_unavailable_stays_classical_only():
    # Model loaded but the registered features cannot be built from the supplied
    # inputs -> meta UNAVAILABLE. An unavailable gate must never block: the
    # cockpit degrades to classical-only exactly as with no model at all.
    d = lc.decide_one(
        "NVDA", 201.0, 202.99, 203.01, session_iso="2026-07-17",
        booster=_StubBooster(0.10),  # would be a hard NO-GO if it could run
    )
    assert d["meta"]["available"] is False
    assert d["classical_go"] is True
    assert d["ticket_ok"] is True


def test_render_decide_meta_nogo_shows_no_ticket():
    d = _decide_with_meta(0.40)
    fixed = datetime(2026, 7, 17, 19, 55, 10, tzinfo=UTC)  # 15:55:10 ET
    out = lc.render_decide(d, exit_mode="auto-note", model_note="test", now_utc=fixed)
    assert "NO TICKET" in out
    assert "META NO-GO" in out
    assert "ORDER TICKET" not in out


# ------------------------------------------------------------------------- the clock


def test_clock_status_inside_and_outside_window():
    inside = datetime(2026, 7, 17, 15, 55, tzinfo=ET)
    ok, msg = lc.clock_status(inside)
    assert ok is True and "OK" in msg
    outside = datetime(2026, 7, 17, 12, 0, tzinfo=ET)
    ok2, msg2 = lc.clock_status(outside)
    assert ok2 is False and "WARNING" in msg2


# ------------------------------------------------------------- model load degradation


def test_load_model_absent_returns_none(tmp_path):
    booster, note = lc.load_model(tmp_path / "does_not_exist.txt")
    assert booster is None
    assert "ABSENT" in note


# --------------------------------------------------- rehearse harness-consistency


def _feature_row(session: str, symbol: str, *, basis: float, net: float) -> dict:
    r = {
        "session": session, "symbol": symbol, "side": 1 if basis >= 0 else -1,
        "net_bps": net, "entry_px": 100.0, "entry_bid": 99.9, "entry_ask": 100.1,
        "entry_mid": 100.0, "cross_px": 100.5,
        # registered numeric features
        "basis_bps": basis, "near_far_bps": 1.0, "near_ref_bps": 1.0, "paired_ratio": 0.5,
        "norm_imb": 0.01, "imb_growth_53": 0.0, "imb_growth_51": 0.0, "msg_count": 40.0,
        "vol20": 0.3, "log_adv20": 22.0,
    }
    r.update({f"oh_{s}": (1.0 if s == symbol else 0.0) for s in lc.UNIVERSE})
    return r


def _synthetic_events() -> pl.DataFrame:
    rows = [
        _feature_row("2026-07-17", "NVDA", basis=50.0, net=6.0),   # classical fires
        _feature_row("2026-07-17", "GOOGL", basis=2.0, net=-0.5),  # below threshold
    ]
    return pl.DataFrame(rows)


def test_rehearse_scored_matches_forward_paper():
    events = _synthetic_events()
    booster = _StubBooster(0.60)  # >= 0.55 gate -> classical fire becomes a meta take
    ref = fp.score_events(events, booster)                 # the harness scoring
    reh = lc.rehearse_scored(events, booster)              # the cockpit path
    # p_win and taken flags are identical to the harness (rehearse is a faithful reuse)
    assert reh["p_win"].to_list() == ref["p_win"].to_list()
    assert reh["taken_classical"].to_list() == ref["taken_classical"].to_list()
    assert reh["taken_meta"].to_list() == ref["taken_meta"].to_list()
    # NVDA (|basis|=50, p_win 0.60) is a meta take; GOOGL (|basis|=2) is not classical
    nvda = reh.filter(pl.col("symbol") == "NVDA").row(0, named=True)
    googl = reh.filter(pl.col("symbol") == "GOOGL").row(0, named=True)
    assert nvda["taken_meta"] is True and googl["taken_classical"] is False


def test_rehearse_scored_degrades_without_model():
    events = _synthetic_events()
    reh = lc.rehearse_scored(events, None)
    assert reh["p_win"].to_list() == [None, None]
    # classical stream still computed from |basis| >= 10
    assert reh.filter(pl.col("symbol") == "NVDA").row(0, named=True)["taken_classical"] is True


def test_rehearse_row_view_sizes_and_scores_pnl():
    row = _feature_row("2026-07-17", "NVDA", basis=50.0, net=6.0)
    row.update({"side": -1, "p_win": 0.5, "taken_classical": True, "taken_meta": False,
                "selected": False, "sel_rank": None})
    v = lc._rehearse_row_view(row, capital_usd=1200.0, clip_cap_usd=800.0)
    # sell -> sizes off the bid; hypo_$ = net_bps/1e4 * notional
    assert v["shares"] == lc.size_shares(1200.0, 800.0, 99.9)
    assert v["hypo_usd"] == pytest.approx(6.0 / 1e4 * v["notional"])


# ------------------------------------------------------------------------- renders


def test_render_decide_go_shows_market_ticket():
    d = lc.decide_one("NVDA", 105.0, 99.99, 100.01, session_iso="2026-07-17", booster=None)
    fixed = datetime(2026, 7, 17, 19, 55, 10, tzinfo=UTC)  # 15:55:10 ET
    out = lc.render_decide(d, exit_mode="auto-note", model_note="test", now_utc=fixed)
    assert "ORDER TICKET" in out
    assert "@ MARKET" in out and "BUY" in out
    assert "late LOC" in out and "marketable exit" in out  # both exit legs shown


def test_render_decide_no_go_shows_no_ticket():
    d = lc.decide_one("NVDA", 100.05, 99.99, 100.01, session_iso="2026-07-17", booster=None)
    fixed = datetime(2026, 7, 17, 19, 55, 10, tzinfo=UTC)
    out = lc.render_decide(d, exit_mode="auto-note", model_note="test", now_utc=fixed)
    assert "NO TICKET" in out


def test_render_checklist_has_key_sections():
    out = lc.render_checklist(
        capital_usd=1200.0, clip_cap_usd=800.0, spread_abort_bps=25.0, exit_mode="auto-note"
    )
    for token in ("15:55:10", "late LOC", "marketable", "25 bps", "NEVER add",
                  "Phase-0 blotter", "FLAT at 16:00:00"):
        assert token in out


# --------------------------------------------------------- signal-only guardrail


def test_module_has_no_order_routing():
    src = Path(lc.__file__).read_text(encoding="utf-8")
    forbidden = (
        "TradingClient", "submit_order", "place_order", "OrderRequest",
        "alpaca.trading", "MarketOrderRequest", "cancel_order",
    )
    for tok in forbidden:
        assert tok not in src, f"cockpit must be signal-only; found {tok!r}"
