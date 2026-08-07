"""Tests for the A1 model overlay (plans/overlay_a1.py) — synthetic preds + plans.

Covers the REGISTERED overlay rules (M3_REGISTRATION.md A1 section):
  * veto: opposing forecast with |z| >= 0.5 -> None
  * neutral: weak-opposing |z| < 0.5 -> plan kept, A0 economics, confidence 0.5
  * agree: legs re-priced from de-normed MFE/MAE, floors/caps respected,
    exact confidence formula, expected_gross from de-normed |pred_fwdH|
  * pred None -> plan returned unchanged
  * schema-invariant fallback: a re-priced stop that would sit on the wrong side
    falls back to the A0 stop leg
  * PredProvider.row_at PIT: last row with ts <= ts, never a later one
"""

from __future__ import annotations

import math

import polars as pl
import pytest

from enginev51.features.grid import PRED_STAMP_TO_AVAILABILITY_NS
from enginev51.plans.overlay_a1 import PredProvider, apply_overlay, denorm_px
from enginev51.plans.schema import EntrySpec, StopSpec, TargetSpec, TradePlan

NS = 1_000_000_000
CURFEW = 10_000 * NS
VOL20 = 0.02  # fractional f_vol20
ENTRY_REF = 100.0


# --------------------------------------------------------------------------- helpers


def _plan(payer: str, side: int, *, targets: tuple[TargetSpec, ...], stop_px: float,
          entry_type: str = "limit") -> TradePlan:
    limit_price = ENTRY_REF if entry_type == "limit" else None
    return TradePlan(
        plan_id=f"{payer}-NVDA-{123 * NS}-0",
        symbol="NVDA",
        ts_authored=123 * NS,
        valid_until=123 * NS + 120 * NS,
        side=side,
        entry=EntrySpec(type=entry_type, limit_price=limit_price, expire_s=180, chase_at_expire=True),
        stop=StopSpec(price=stop_px, basis=payer),
        targets=targets,
        hold_max_min=120,
        curfew_ts=CURFEW,
        expected_gross_bps=20.0,
        expected_net_bps=15.0,
        sigma_h_bps=50.0,
        p_win=0.5,
        ev_ratio=4.0,
        confidence=0.5,
        payer=payer,
        horizon_min=120,
        model_ids=("A0",),
    )


def _pred(**over) -> dict:
    """A full A1 contract row; override any field via kwargs."""
    base = {
        "symbol": "NVDA",
        "session": "2026-04-06",
        "ts": 123 * NS,
        "pred_fwd60_z": 0.0,
        "pred_fwd120_z": 0.0,
        "pred_mfe60_q50_z": 0.0,
        "pred_mfe60_q75_z": 0.0,
        "pred_mae60_q75_z": 0.0,
        "pred_mfe120_q50_z": 0.0,
        "pred_mfe120_q75_z": 0.0,
        "pred_mae120_q75_z": 0.0,
        "vol20": VOL20,
        "fold_id": 0,
        "trained_through": "2026-03-30",
    }
    base.update(over)
    return base


# gap_mr -> H=120, two targets (0.6/0.4). A0 legs: stop 3.0 px, targets +4/+6 px.
def _gap_plan(side: int = 1) -> TradePlan:
    return _plan(
        "gap_mr", side,
        targets=(TargetSpec(ENTRY_REF + side * 4.0, 0.6), TargetSpec(ENTRY_REF + side * 6.0, 0.4)),
        stop_px=ENTRY_REF - side * 3.0,
    )


A0_STOP_DIST = 3.0
A0_TGT_DISTS = [4.0, 6.0]


# --------------------------------------------------------------------------- veto


def test_veto_opposing_conviction():
    # long plan, model forecasts a strong DOWN move (opposes, |z| >= 0.5) -> None
    pred = _pred(pred_fwd120_z=-0.8)
    out = apply_overlay(_gap_plan(1), 1, pred, "gap_mr", A0_STOP_DIST, A0_TGT_DISTS, ENTRY_REF, 2.0)
    assert out is None


def test_veto_short_opposing():
    # short plan, model forecasts strong UP -> None
    pred = _pred(pred_fwd120_z=0.8)
    out = apply_overlay(_gap_plan(-1), -1, pred, "gap_mr", A0_STOP_DIST, A0_TGT_DISTS, ENTRY_REF, 2.0)
    assert out is None


def test_no_veto_just_below_threshold():
    # opposing but |z| = 0.49 < 0.5 -> NOT vetoed (kept, neutral economics)
    pred = _pred(pred_fwd120_z=-0.49)
    out = apply_overlay(_gap_plan(1), 1, pred, "gap_mr", A0_STOP_DIST, A0_TGT_DISTS, ENTRY_REF, 2.0)
    assert out is not None


# --------------------------------------------------------------------------- neutral


def test_neutral_keeps_a0_economics_and_confidence():
    # weak opposing (sign != side, |z| < 0.5): kept, expected_gross = A0 template,
    # confidence exactly 0.5. MFE/MAE set to clamp to the A0 legs.
    pred = _pred(
        pred_fwd120_z=-0.2,
        # MAE de-norm below the A0 stop floor -> stop clamps back to A0 distance
        pred_mae120_q75_z=0.0,
        # MFE de-norm below the 10bps floor -> but capped/floored; set to reproduce A0
        pred_mfe120_q50_z=0.0,
        pred_mfe120_q75_z=0.0,
    )
    out = apply_overlay(_gap_plan(1), 1, pred, "gap_mr", A0_STOP_DIST, A0_TGT_DISTS, ENTRY_REF, 2.0)
    assert out is not None
    assert out.confidence == 0.5
    assert out.p_win == 0.5
    # expected_gross falls back to the A0 template (model does not agree)
    assert out.expected_gross_bps == 20.0
    # MAE=0 -> stop distance clamps to the A0 floor (3.0 px) -> stop back at A0
    assert out.stop.price == pytest.approx(ENTRY_REF - 3.0)
    # MFE=0 -> targets clamp to the 10bps floor (0.1 px), not the A0 distance
    assert out.targets[0].price == pytest.approx(ENTRY_REF + 0.1)
    assert out.model_ids == ("A1", "lgbm_a1_v1")


# --------------------------------------------------------------------------- agree


def test_agree_reprices_legs_and_confidence_exact():
    fwd_z = 1.0
    pred = _pred(
        pred_fwd120_z=fwd_z,
        pred_mfe120_q50_z=5.0,   # de-norm px within [floor, 2*A0]
        pred_mfe120_q75_z=7.0,
        pred_mae120_q75_z=3.0,
    )
    out = apply_overlay(_gap_plan(1), 1, pred, "gap_mr", A0_STOP_DIST, A0_TGT_DISTS, ENTRY_REF, 2.0)
    assert out is not None

    # confidence = 0.5 + 0.2 * min(|z|,2)/2  = 0.5 + 0.2*0.5 = 0.6
    assert out.confidence == pytest.approx(0.6)
    assert out.p_win == pytest.approx(0.6)

    # expected_gross = de-normed |pred_fwd120| bps
    scale = math.sqrt(120 / 390.0)
    assert out.expected_gross_bps == pytest.approx(fwd_z * VOL20 * scale * 1e4)
    assert out.expected_net_bps == pytest.approx(out.expected_gross_bps - 2.0)

    # legs re-priced from de-normed excursions (all within floor/cap)
    d_mfe50 = denorm_px(5.0, VOL20, 120, ENTRY_REF)
    d_mfe75 = denorm_px(7.0, VOL20, 120, ENTRY_REF)
    d_mae = denorm_px(3.0, VOL20, 120, ENTRY_REF)
    assert out.targets[0].price == pytest.approx(ENTRY_REF + d_mfe50)
    assert out.targets[1].price == pytest.approx(ENTRY_REF + d_mfe75)
    assert out.stop.price == pytest.approx(ENTRY_REF - d_mae)
    assert out.targets[0].frac == 0.6 and out.targets[1].frac == 0.4


def test_agree_caps_respected():
    # huge excursion preds -> stop capped at 2x A0, target capped at 2x A0 target
    pred = _pred(
        pred_fwd120_z=2.0,
        pred_mfe120_q50_z=1000.0,
        pred_mfe120_q75_z=1000.0,
        pred_mae120_q75_z=1000.0,
    )
    out = apply_overlay(_gap_plan(1), 1, pred, "gap_mr", A0_STOP_DIST, A0_TGT_DISTS, ENTRY_REF, 2.0)
    assert out is not None
    assert out.stop.price == pytest.approx(ENTRY_REF - 2.0 * A0_STOP_DIST)      # cap 2*3=6
    assert out.targets[0].price == pytest.approx(ENTRY_REF + 2.0 * A0_TGT_DISTS[0])  # cap 8
    assert out.targets[1].price == pytest.approx(ENTRY_REF + 2.0 * A0_TGT_DISTS[1])  # cap 12
    # |z|=2 -> confidence capped at 0.7
    assert out.confidence == pytest.approx(0.7)


def test_agree_target_floor_10bps():
    # tiny MFE -> target distance floored at 10 bps (0.1 px at ref 100)
    pred = _pred(pred_fwd120_z=2.0, pred_mfe120_q50_z=1e-6, pred_mfe120_q75_z=1e-6,
                 pred_mae120_q75_z=3.0)
    out = apply_overlay(_gap_plan(1), 1, pred, "gap_mr", A0_STOP_DIST, A0_TGT_DISTS, ENTRY_REF, 2.0)
    assert out is not None
    assert out.targets[0].price == pytest.approx(ENTRY_REF + 0.1)
    assert out.targets[1].price == pytest.approx(ENTRY_REF + 0.1)


def test_agree_hurdle_vetoes_tiny_gross():
    # agreeing but de-normed |fwd| gross below the 8 bps / 2x-cost hurdle -> None
    # fwd_z tiny: gross = z*vol20*sqrt(120/390)*1e4; pick z so gross < 8
    scale = math.sqrt(120 / 390.0)
    z = 7.0 / (VOL20 * scale * 1e4)  # -> ~7 bps gross < 8
    pred = _pred(pred_fwd120_z=z, pred_mae120_q75_z=3.0)
    out = apply_overlay(_gap_plan(1), 1, pred, "gap_mr", A0_STOP_DIST, A0_TGT_DISTS, ENTRY_REF, 2.0)
    assert out is None


# --------------------------------------------------------------------------- pred None


def test_pred_none_returns_plan_unchanged():
    plan = _gap_plan(1)
    out = apply_overlay(plan, 1, None, "gap_mr", A0_STOP_DIST, A0_TGT_DISTS, ENTRY_REF, 2.0)
    assert out is plan
    assert out.model_ids == ("A0",)


# --------------------------------------------------------------------------- fallback


def test_schema_invariant_fallback_keeps_a0_stop():
    # a0_stop_distance_px = 0 -> re-priced stop clamps to 0 distance -> would sit
    # AT the entry (wrong side) -> falls back to the A0 stop leg.
    plan = _gap_plan(1)
    pred = _pred(pred_fwd120_z=1.0, pred_mae120_q75_z=5.0,
                 pred_mfe120_q50_z=5.0, pred_mfe120_q75_z=7.0)
    out = apply_overlay(plan, 1, pred, "gap_mr", 0.0, A0_TGT_DISTS, ENTRY_REF, 2.0)
    assert out is not None
    assert out.stop.price == plan.stop.price          # A0 stop preserved
    assert out.stop.basis == plan.stop.basis
    # targets still re-priced normally
    assert out.targets[0].price != plan.targets[0].price


# --------------------------------------------------------------------------- single-target + letf


def test_single_target_payer_uses_q50():
    # vwap_magnet: H=60, one target frac 1.0, uses MFE q50 only.
    plan = _plan("vwap_magnet", 1, targets=(TargetSpec(ENTRY_REF + 4.0, 1.0),), stop_px=ENTRY_REF - 3.0)
    pred = _pred(pred_fwd60_z=1.0, pred_mfe60_q50_z=5.0, pred_mfe60_q75_z=99.0, pred_mae60_q75_z=3.0)
    out = apply_overlay(plan, 1, pred, "vwap_magnet", 3.0, [4.0], ENTRY_REF, 2.0)
    assert out is not None
    assert len(out.targets) == 1 and out.targets[0].frac == 1.0
    d = denorm_px(5.0, VOL20, 60, ENTRY_REF)  # q50, H=60
    assert out.targets[0].price == pytest.approx(ENTRY_REF + d)


def test_letf_market_entry_no_targets():
    # letf_window: H=60, market entry, no targets; stop re-priced from MAE60.
    plan = _plan("letf_window", 1, targets=(), stop_px=ENTRY_REF - 3.0, entry_type="market")
    pred = _pred(pred_fwd60_z=1.0, pred_mae60_q75_z=5.0)  # de-norm ~3.9px, within [3,6]
    out = apply_overlay(plan, 1, pred, "letf_window", 3.0, [], 100.0, 2.0)
    assert out is not None
    assert out.targets == ()
    d = denorm_px(5.0, VOL20, 60, 100.0)
    assert 3.0 <= d <= 6.0  # within the clamp band
    assert out.stop.price == pytest.approx(100.0 - d)


# --------------------------------------------------------------------------- PredProvider PIT


def _write_preds(tmp_path):
    rows = [
        _pred(ts=100 * NS, pred_fwd120_z=0.1),
        _pred(ts=200 * NS, pred_fwd120_z=0.2),
        _pred(ts=300 * NS, pred_fwd120_z=0.3),
        # a different session
        _pred(ts=250 * NS, session="2026-04-07", pred_fwd120_z=0.9),
    ]
    df = pl.DataFrame(rows)
    d = tmp_path / "preds"
    d.mkdir()
    df.write_parquet(d / "NVDA.parquet")
    return d


def test_provider_row_at_pit_last_le_ts(tmp_path):
    # F2 (SIM_AUDIT_2026-07-21 §3): pred rows are stamped at bar OPEN but carry
    # that bar's close, so a row stamped at ts is only AVAILABLE at
    # ts + PRED_STAMP_TO_AVAILABILITY_NS. row_at returns the last row with
    # row.ts <= decision_ts - PRED_STAMP_TO_AVAILABILITY_NS — never a coincident
    # row (the previous convention `ts <= decision_ts` leaked 60 s of future tape).
    d = _write_preds(tmp_path)
    prov = PredProvider(d)
    lag = PRED_STAMP_TO_AVAILABILITY_NS
    # decision ON the 200s stamp: that row is not yet available -> last is 100s row.
    assert prov.row_at("NVDA", "2026-04-06", 200 * NS)["pred_fwd120_z"] == pytest.approx(0.1)
    # decision between stamps -> last row whose availability instant has passed.
    assert prov.row_at("NVDA", "2026-04-06", 250 * NS)["pred_fwd120_z"] == pytest.approx(0.1)
    # decision ON the 300s stamp -> coincident row excluded; previous (200s) served.
    assert prov.row_at("NVDA", "2026-04-06", 300 * NS)["pred_fwd120_z"] == pytest.approx(0.2)
    # the 300s row becomes available EXACTLY one lag later.
    assert prov.row_at("NVDA", "2026-04-06", 300 * NS + lag)["pred_fwd120_z"] == pytest.approx(0.3)
    # far after all rows -> last row.
    assert prov.row_at("NVDA", "2026-04-06", 10_000 * NS)["pred_fwd120_z"] == pytest.approx(0.3)


def test_provider_5min_mark_decision_selects_previous_row(tmp_path):
    # F2: a1 pred grids are 5-minute (verified on data/preds/a1_v1). A decision
    # landing exactly on a 5-min mark must select the PREVIOUS 5-min row, not the
    # row stamped at that same instant (its features contain that bar's close =
    # 60 s of future tape). With a 60 s availability lag on a 300 s grid this
    # steps the arm back a full 5-min bar.
    five_min = 300 * NS
    rows = [
        _pred(ts=five_min, pred_fwd120_z=0.3),      # 05:00 mark
        _pred(ts=2 * five_min, pred_fwd120_z=0.6),  # 10:00 mark == decision instant
    ]
    d = tmp_path / "preds"
    d.mkdir()
    pl.DataFrame(rows).write_parquet(d / "NVDA.parquet")
    prov = PredProvider(d)
    r = prov.row_at("NVDA", "2026-04-06", 2 * five_min)
    assert r is not None
    assert r["pred_fwd120_z"] == pytest.approx(0.3)  # previous row, not the coincident 0.6


def test_provider_row_at_before_first_is_none(tmp_path):
    prov = PredProvider(_write_preds(tmp_path))
    assert prov.row_at("NVDA", "2026-04-06", 50 * NS) is None


def test_provider_session_scoped(tmp_path):
    prov = PredProvider(_write_preds(tmp_path))
    # session filter isolates rows: 2026-04-07 has only ts=250 (decision 400s
    # leaves it available past the 60 s lag: avail=340 >= 250).
    r = prov.row_at("NVDA", "2026-04-07", 400 * NS)
    assert r["pred_fwd120_z"] == pytest.approx(0.9)
    # a session with no rows -> None
    assert prov.row_at("NVDA", "2026-01-01", 400 * NS) is None


def test_provider_missing_symbol_is_none(tmp_path):
    prov = PredProvider(_write_preds(tmp_path))
    assert prov.row_at("TSLA", "2026-04-06", 300 * NS) is None
