"""Tests for the M4 encoder overlay (plans/overlay_m4.py) — synthetic preds + plans.

Covers the REGISTERED M4 arms (M3_REGISTRATION.md M4 section + ledger 2026-07-15):
  * selector mapping EXACT: LONG skipped iff p_dn_0.75x1.25_H >= p_skip; SHORT via
    p_up_1.25x0.75_H; the OTHER side's column is ignored.
  * mode 'legs' never skips (adverse prob is not even read); re-prices via A1-v3.
  * mode 'both' applies selector THEN legs serially.
  * confidence formula EXACT (select|both); legs-only keeps plan values.
  * A1-v3 clamps/fallbacks reused verbatim (stop [A0,2xA0]; targets [10bps,2xA0];
    schema-invariant fallback to the A0 leg).
  * hurdle is ALWAYS the A0 template expected_gross (rule-3 mode a0).
  * pred None -> plan returned unchanged.
  * M4Provider.row_at PIT: last row with ts <= ts, session-scoped.
  * run_trial --arm m4 smoke on ONE real range with a fabricated preds parquet:
    veto-all vs keep-all overlay/drop counts.
"""

from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from enginev51.features.grid import PRED_STAMP_TO_AVAILABILITY_NS
from enginev51.plans import overlay_m4 as _m4
from enginev51.plans.overlay_a1 import denorm_px as _denorm_px
from enginev51.plans.overlay_m4 import M4Provider, apply_m4, denorm_px  # noqa: F401
from enginev51.plans.schema import EntrySpec, StopSpec, TargetSpec, TradePlan

NS = 1_000_000_000
CURFEW = 10_000 * NS
VOL20 = 0.02
ENTRY_REF = 100.0
P_SKIP = 0.45


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
        p_win=0.55,
        ev_ratio=4.0,
        confidence=0.55,
        payer=payer,
        horizon_min=120,
        model_ids=("A0",),
    )


def _pred(**over) -> dict:
    """A full M4 contract row (A1 leg columns + barrier grid); override via kwargs."""
    base = {
        "symbol": "NVDA",
        "session": "2026-04-06",
        "ts": 123 * NS,
        # A1 leg-pricing contract columns
        "pred_fwd60_z": 0.0,
        "pred_fwd120_z": 0.0,
        "pred_mfe60_q50_z": 0.0,
        "pred_mfe60_q75_z": 0.0,
        "pred_mae60_q75_z": 0.0,
        "pred_mfe120_q50_z": 0.0,
        "pred_mfe120_q75_z": 0.0,
        "pred_mae120_q75_z": 0.0,
        "vol20": VOL20,
        # 16-column barrier grid (only the two adverse configs are read; rest present)
        "p_up_0.75x1.25_60": 0.0, "p_dn_0.75x1.25_60": 0.0,
        "p_up_1.25x0.75_60": 0.0, "p_dn_1.25x0.75_60": 0.0,
        "p_up_0.75x1.25_120": 0.0, "p_dn_0.75x1.25_120": 0.0,
        "p_up_1.25x0.75_120": 0.0, "p_dn_1.25x0.75_120": 0.0,
        "fold_id": 0,
        "trained_through": "2026-03-30",
    }
    base.update(over)
    return base


# gap_mr -> H=120, two targets (0.6/0.4). A0 legs: stop 3.0 px, targets +4/+6 px.
A0_STOP_DIST = 3.0
A0_TGT_DISTS = [4.0, 6.0]


def _gap_plan(side: int = 1) -> TradePlan:
    return _plan(
        "gap_mr", side,
        targets=(TargetSpec(ENTRY_REF + side * 4.0, 0.6), TargetSpec(ENTRY_REF + side * 6.0, 0.4)),
        stop_px=ENTRY_REF - side * 3.0,
    )


def _apply(plan, pred, mode, p_skip=P_SKIP, stop_d=A0_STOP_DIST, tgt_d=None, ref=ENTRY_REF, cost=2.0):
    return apply_m4(plan, pred, mode, p_skip, stop_d, tgt_d if tgt_d is not None else A0_TGT_DISTS, ref, cost)


# --------------------------------------------------------------------------- selector mapping


def test_denorm_shared_with_a1():
    # the M4 module re-exports the A1 de-norm; identical numbers.
    assert denorm_px(3.0, VOL20, 120, ENTRY_REF) == _denorm_px(3.0, VOL20, 120, ENTRY_REF)


def test_selector_long_skips_on_p_dn_075x125():
    # LONG: adverse = p_dn_0.75x1.25_120 (gap_mr H=120). >= p_skip -> SKIP (None).
    _m4.DROP_COUNTS.clear()
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.5, "p_up_1.25x0.75_120": 0.99})  # up col high but IGNORED for long
    out = _apply(_gap_plan(1), pred, "select")
    assert out is None
    assert _m4.DROP_COUNTS["selector_skip"] == 1


def test_selector_long_keeps_below_threshold():
    # LONG adverse just below p_skip -> kept; the up-config (short's column) is ignored.
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.4499, "p_up_1.25x0.75_120": 0.99})
    out = _apply(_gap_plan(1), pred, "select")
    assert out is not None


def test_selector_short_skips_on_p_up_125x075():
    # SHORT: adverse = p_up_1.25x0.75_120. dn col high but ignored for short.
    _m4.DROP_COUNTS.clear()
    pred = _pred(**{"p_up_1.25x0.75_120": 0.6, "p_dn_0.75x1.25_120": 0.99})
    out = _apply(_gap_plan(-1), pred, "select")
    assert out is None
    assert _m4.DROP_COUNTS["selector_skip"] == 1


def test_selector_short_keeps_when_up_config_low():
    pred = _pred(**{"p_up_1.25x0.75_120": 0.10, "p_dn_0.75x1.25_120": 0.99})
    out = _apply(_gap_plan(-1), pred, "select")
    assert out is not None


def test_selector_horizon_60_for_vwap():
    # vwap_magnet uses H=60 -> reads the _60 adverse column, not _120.
    plan = _plan("vwap_magnet", 1, targets=(TargetSpec(ENTRY_REF + 4.0, 1.0),), stop_px=ENTRY_REF - 3.0)
    # _120 high (ignored), _60 high (used) -> skipped
    pred = _pred(**{"p_dn_0.75x1.25_60": 0.9, "p_dn_0.75x1.25_120": 0.0})
    assert _apply(plan, pred, "select", tgt_d=[4.0]) is None
    # inverse: _60 low -> kept even though _120 high
    pred2 = _pred(**{"p_dn_0.75x1.25_60": 0.0, "p_dn_0.75x1.25_120": 0.9})
    assert _apply(plan, pred2, "select", tgt_d=[4.0]) is not None


# --------------------------------------------------------------------------- mode legs never skips


def test_mode_legs_never_skips():
    # adverse prob maxed, but mode=legs must NOT read it / skip.
    _m4.DROP_COUNTS.clear()
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.99, "pred_mae120_q75_z": 3.0, "pred_mfe120_q50_z": 5.0, "pred_mfe120_q75_z": 7.0})
    out = _apply(_gap_plan(1), pred, "legs")
    assert out is not None
    assert "selector_skip" not in _m4.DROP_COUNTS
    # legs-only keeps the incoming plan's confidence / p_win
    assert out.confidence == 0.55 and out.p_win == 0.55


def test_mode_legs_reprices_via_a1v3():
    pred = _pred(pred_mae120_q75_z=3.0, pred_mfe120_q50_z=5.0, pred_mfe120_q75_z=7.0)
    out = _apply(_gap_plan(1), pred, "legs")
    d_mfe50 = denorm_px(5.0, VOL20, 120, ENTRY_REF)
    d_mfe75 = denorm_px(7.0, VOL20, 120, ENTRY_REF)
    d_mae = denorm_px(3.0, VOL20, 120, ENTRY_REF)
    assert out.targets[0].price == pytest.approx(ENTRY_REF + d_mfe50)
    assert out.targets[1].price == pytest.approx(ENTRY_REF + d_mfe75)
    assert out.stop.price == pytest.approx(ENTRY_REF - d_mae)
    assert out.model_ids == ("A0", "M4", "m4_v1")


# --------------------------------------------------------------------------- mode both serial


def test_mode_both_skips_then_would_reprice():
    # both: selector runs first; a skip short-circuits before legs.
    _m4.DROP_COUNTS.clear()
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.9, "pred_mae120_q75_z": 3.0, "pred_mfe120_q50_z": 5.0, "pred_mfe120_q75_z": 7.0})
    assert _apply(_gap_plan(1), pred, "both") is None
    assert _m4.DROP_COUNTS["selector_skip"] == 1


def test_mode_both_kept_reprices_and_selector_confidence():
    # kept by selector -> legs re-priced AND confidence from the selector formula.
    p_adverse = 0.25
    pred = _pred(**{"p_dn_0.75x1.25_120": p_adverse, "pred_mae120_q75_z": 3.0, "pred_mfe120_q50_z": 5.0, "pred_mfe120_q75_z": 7.0})
    out = _apply(_gap_plan(1), pred, "both")
    assert out is not None
    # legs re-priced (A1-v3)
    assert out.stop.price == pytest.approx(ENTRY_REF - denorm_px(3.0, VOL20, 120, ENTRY_REF))
    assert out.targets[0].price == pytest.approx(ENTRY_REF + denorm_px(5.0, VOL20, 120, ENTRY_REF))
    # confidence from selector formula (NOT the plan's 0.55)
    expect = 0.5 + 0.4 * (P_SKIP - p_adverse) / P_SKIP
    assert out.confidence == pytest.approx(expect)
    assert out.p_win == pytest.approx(expect)


# --------------------------------------------------------------------------- confidence formula


def test_confidence_formula_exact_select():
    p_adverse = 0.15
    pred = _pred(**{"p_dn_0.75x1.25_120": p_adverse})
    out = _apply(_gap_plan(1), pred, "select")
    expect = 0.5 + 0.4 * (P_SKIP - p_adverse) / P_SKIP
    assert out.confidence == pytest.approx(expect)
    assert out.p_win == pytest.approx(expect)


def test_confidence_zero_adverse_hits_max_0p9():
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.0})
    out = _apply(_gap_plan(1), pred, "select")
    assert out.confidence == pytest.approx(0.9)


def test_confidence_capped_at_0p9():
    # a negative "prob" would push above 0.9 -> hard cap at 0.9.
    pred = _pred(**{"p_dn_0.75x1.25_120": -1.0})
    out = _apply(_gap_plan(1), pred, "select")
    assert out.confidence == pytest.approx(0.9)


def test_select_keeps_a0_legs_unchanged():
    # mode=select must NOT re-price legs (leg preds present but ignored).
    plan = _gap_plan(1)
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.1, "pred_mae120_q75_z": 99.0, "pred_mfe120_q50_z": 99.0})
    out = _apply(plan, pred, "select")
    assert out.stop.price == plan.stop.price
    assert out.targets[0].price == plan.targets[0].price
    assert out.targets[1].price == plan.targets[1].price


# --------------------------------------------------------------------------- hurdle is A0


def test_hurdle_always_a0_template():
    # even a huge de-normed forecast never lifts the hurdle: expected_gross == A0.
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.1, "pred_fwd120_z": 99.0, "pred_mae120_q75_z": 3.0, "pred_mfe120_q50_z": 5.0, "pred_mfe120_q75_z": 7.0})
    out = _apply(_gap_plan(1), pred, "both")
    assert out.expected_gross_bps == 20.0  # the A0 template value
    assert out.expected_net_bps == pytest.approx(20.0 - 2.0)


# --------------------------------------------------------------------------- A1-v3 clamps / fallbacks


def test_legs_caps_respected():
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.0, "pred_mfe120_q50_z": 1000.0, "pred_mfe120_q75_z": 1000.0, "pred_mae120_q75_z": 1000.0})
    out = _apply(_gap_plan(1), pred, "both")
    assert out.stop.price == pytest.approx(ENTRY_REF - 2.0 * A0_STOP_DIST)
    assert out.targets[0].price == pytest.approx(ENTRY_REF + 2.0 * A0_TGT_DISTS[0])
    assert out.targets[1].price == pytest.approx(ENTRY_REF + 2.0 * A0_TGT_DISTS[1])


def test_legs_target_floor_10bps():
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.0, "pred_mfe120_q50_z": 1e-6, "pred_mfe120_q75_z": 1e-6, "pred_mae120_q75_z": 3.0})
    out = _apply(_gap_plan(1), pred, "legs")
    assert out.targets[0].price == pytest.approx(ENTRY_REF + 0.1)
    assert out.targets[1].price == pytest.approx(ENTRY_REF + 0.1)


def test_legs_stop_floor_to_a0():
    # MAE de-norm below the A0 stop distance -> clamps back up to the A0 distance.
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.0, "pred_mae120_q75_z": 0.0, "pred_mfe120_q50_z": 5.0, "pred_mfe120_q75_z": 7.0})
    out = _apply(_gap_plan(1), pred, "legs")
    assert out.stop.price == pytest.approx(ENTRY_REF - A0_STOP_DIST)


def test_schema_invariant_fallback_keeps_a0_stop():
    # a0_stop_distance_px = 0 -> re-priced stop clamps to 0 -> at entry (wrong side)
    # -> falls back to the A0 stop leg; targets still re-price.
    plan = _gap_plan(1)
    pred = _pred(**{"p_dn_0.75x1.25_120": 0.0, "pred_mae120_q75_z": 5.0, "pred_mfe120_q50_z": 5.0, "pred_mfe120_q75_z": 7.0})
    out = _apply(plan, pred, "legs", stop_d=0.0)
    assert out.stop.price == plan.stop.price
    assert out.stop.basis == plan.stop.basis
    assert out.targets[0].price != plan.targets[0].price


def test_single_target_payer_uses_q50():
    plan = _plan("vwap_magnet", 1, targets=(TargetSpec(ENTRY_REF + 4.0, 1.0),), stop_px=ENTRY_REF - 3.0)
    pred = _pred(**{"p_dn_0.75x1.25_60": 0.0, "pred_mfe60_q50_z": 5.0, "pred_mfe60_q75_z": 99.0, "pred_mae60_q75_z": 3.0})
    out = _apply(plan, pred, "both", tgt_d=[4.0])
    assert len(out.targets) == 1 and out.targets[0].frac == 1.0
    assert out.targets[0].price == pytest.approx(ENTRY_REF + denorm_px(5.0, VOL20, 60, ENTRY_REF))


def test_letf_market_entry_no_targets():
    plan = _plan("letf_window", 1, targets=(), stop_px=ENTRY_REF - 3.0, entry_type="market")
    pred = _pred(**{"p_dn_0.75x1.25_60": 0.0, "pred_mae60_q75_z": 5.0})
    out = _apply(plan, pred, "legs", stop_d=3.0, tgt_d=[], ref=100.0)
    assert out.targets == ()
    d = denorm_px(5.0, VOL20, 60, 100.0)
    assert 3.0 <= d <= 6.0
    assert out.stop.price == pytest.approx(100.0 - d)


# --------------------------------------------------------------------------- pred None


def test_pred_none_returns_plan_unchanged():
    plan = _gap_plan(1)
    out = _apply(plan, None, "both")
    assert out is plan
    assert out.model_ids == ("A0",)


def test_bad_mode_raises():
    with pytest.raises(ValueError):
        _apply(_gap_plan(1), _pred(), "nonsense")


# --------------------------------------------------------------------------- M4Provider PIT


def _write_preds(tmp_path):
    rows = [
        _pred(**{"ts": 100 * NS, "p_dn_0.75x1.25_120": 0.1}),
        _pred(**{"ts": 200 * NS, "p_dn_0.75x1.25_120": 0.2}),
        _pred(**{"ts": 300 * NS, "p_dn_0.75x1.25_120": 0.3}),
        _pred(**{"ts": 250 * NS, "session": "2026-04-07", "p_dn_0.75x1.25_120": 0.9}),
    ]
    d = tmp_path / "preds"
    d.mkdir()
    pl.DataFrame(rows).write_parquet(d / "NVDA.parquet")
    return d


def test_provider_row_at_pit_last_le_ts(tmp_path):
    # F2 (SIM_AUDIT_2026-07-21 §3): rows are bar-OPEN-stamped but carry the bar
    # close, so a row stamped at ts is AVAILABLE only at
    # ts + PRED_STAMP_TO_AVAILABILITY_NS. row_at returns the last row with
    # row.ts <= decision_ts - PRED_STAMP_TO_AVAILABILITY_NS — never a coincident row.
    prov = M4Provider(_write_preds(tmp_path))
    lag = PRED_STAMP_TO_AVAILABILITY_NS
    # decision ON the 200s stamp -> not yet available -> 100s row.
    assert prov.row_at("NVDA", "2026-04-06", 200 * NS)["p_dn_0.75x1.25_120"] == pytest.approx(0.1)
    # between stamps -> last available, never later.
    assert prov.row_at("NVDA", "2026-04-06", 250 * NS)["p_dn_0.75x1.25_120"] == pytest.approx(0.1)
    # decision ON the 300s stamp -> coincident excluded; previous (200s) served.
    assert prov.row_at("NVDA", "2026-04-06", 300 * NS)["p_dn_0.75x1.25_120"] == pytest.approx(0.2)
    # 300s row available exactly one lag later.
    assert prov.row_at("NVDA", "2026-04-06", 300 * NS + lag)["p_dn_0.75x1.25_120"] == pytest.approx(0.3)
    assert prov.row_at("NVDA", "2026-04-06", 10_000 * NS)["p_dn_0.75x1.25_120"] == pytest.approx(0.3)


def test_provider_1min_mark_decision_selects_previous_row(tmp_path):
    # F2: m4 pred grids are 1-minute (verified on data/preds/m4_v1). Every
    # minute-mark decision has a coincident row; the 60 s availability lag makes
    # it select the immediately-prior minute's row (1-min effective step-back).
    one_min = 60 * NS
    rows = [
        _pred(**{"ts": one_min, "p_dn_0.75x1.25_120": 0.3}),      # 01:00
        _pred(**{"ts": 2 * one_min, "p_dn_0.75x1.25_120": 0.6}),  # 02:00 == decision instant
    ]
    d = tmp_path / "preds"
    d.mkdir()
    pl.DataFrame(rows).write_parquet(d / "NVDA.parquet")
    prov = M4Provider(d)
    r = prov.row_at("NVDA", "2026-04-06", 2 * one_min)
    assert r is not None
    assert r["p_dn_0.75x1.25_120"] == pytest.approx(0.3)  # previous minute, not coincident 0.6


def test_provider_before_first_is_none(tmp_path):
    prov = M4Provider(_write_preds(tmp_path))
    assert prov.row_at("NVDA", "2026-04-06", 50 * NS) is None


def test_provider_session_scoped(tmp_path):
    prov = M4Provider(_write_preds(tmp_path))
    # 2026-04-07 has only ts=250; decision 400s leaves it available (avail=340>=250).
    assert prov.row_at("NVDA", "2026-04-07", 400 * NS)["p_dn_0.75x1.25_120"] == pytest.approx(0.9)
    assert prov.row_at("NVDA", "2026-01-01", 400 * NS) is None


def test_provider_missing_symbol_is_none(tmp_path):
    prov = M4Provider(_write_preds(tmp_path))
    assert prov.row_at("TSLA", "2026-04-06", 300 * NS) is None


def test_provider_arch_tag_default_and_from_report(tmp_path):
    d = _write_preds(tmp_path)
    assert M4Provider(d).arch_tag == "m4_v1"  # no report -> default
    (d / "_train_report.json").write_text('{"arch": "tcn_dilated"}', encoding="utf-8")
    assert M4Provider(d).arch_tag == "tcn_dilated"


# --------------------------------------------------------------------------- run_trial smoke


SMOKE_START = date(2026, 5, 18)
SMOKE_END = date(2026, 5, 29)
SMOKE_SESSIONS = [
    "2026-05-18", "2026-05-19", "2026-05-20", "2026-05-21", "2026-05-22",
    "2026-05-26", "2026-05-27", "2026-05-28", "2026-05-29",
]


def _write_smoke_preds(preds_dir, adverse: float):
    """One PIT-early (ts=1) row per session per symbol; both adverse configs set."""
    preds_dir.mkdir(parents=True, exist_ok=True)
    for sym in ("NVDA", "TSLA"):
        rows = []
        for sess in SMOKE_SESSIONS:
            rows.append(_pred(**{"symbol": sym, "session": sess, "ts": 1, "p_dn_0.75x1.25_60": adverse, "p_up_1.25x0.75_60": adverse, "p_dn_0.75x1.25_120": adverse, "p_up_1.25x0.75_120": adverse, "pred_mae60_q75_z": 1.0, "pred_mfe60_q50_z": 2.0, "pred_mfe60_q75_z": 3.0}))
        pl.DataFrame(rows).write_parquet(preds_dir / f"{sym}.parquet")


def test_run_trial_arm_m4_smoke(tmp_path):
    from enginev51.apps import run_trial
    from enginev51.config import get_settings

    settings = get_settings()

    # baseline A0 authored count over the same range.
    df_a0, _ = run_trial.run_trial(
        settings, symbols=["NVDA", "TSLA"], start=SMOKE_START, end=SMOKE_END, k_slots=2, seed=7,
    )
    n_a0 = df_a0.height
    assert n_a0 > 0, "smoke range must author at least one A0 plan"

    # veto-all: adverse prob 0.9 >= p_skip 0.45 -> every predicted state is skipped.
    veto_dir = tmp_path / "m4_veto"
    _write_smoke_preds(veto_dir, adverse=0.9)
    df_v, st_v = run_trial.run_trial(
        settings, symbols=["NVDA", "TSLA"], start=SMOKE_START, end=SMOKE_END, k_slots=2, seed=7,
        arm="m4", preds_dir=str(veto_dir), m4_mode="select", p_skip=0.45,
    )
    assert st_v["arm"] == "m4" and st_v["m4_mode"] == "select" and st_v["p_skip"] == 0.45
    assert st_v["overlay_counts"]["vetoed"] > 0
    assert st_v["overlay_counts"]["no_pred"] == 0  # every state had a PIT pred row
    assert st_v["drop_counts"]["selector_skip"] == st_v["overlay_counts"]["vetoed"]
    assert df_v.height < n_a0  # vetoed plans never reach replay

    # keep-all: adverse prob 0.0 < p_skip -> nothing skipped; authored == A0 baseline.
    keep_dir = tmp_path / "m4_keep"
    _write_smoke_preds(keep_dir, adverse=0.0)
    df_k, st_k = run_trial.run_trial(
        settings, symbols=["NVDA", "TSLA"], start=SMOKE_START, end=SMOKE_END, k_slots=2, seed=7,
        arm="m4", preds_dir=str(keep_dir), m4_mode="select", p_skip=0.45,
    )
    assert st_k["overlay_counts"]["vetoed"] == 0
    assert st_k["overlay_counts"]["kept"] > 0
    assert st_k["drop_counts"].get("selector_skip", 0) == 0
    assert df_k.height == n_a0  # selector kept every A0 plan, legs untouched (mode=select)
