"""Tests for the A1 overlay trainer (apps/train_a1.py) — no real data / no LightGBM.

Pins the four invariants the FROZEN contract + registered spec require:
  1. z-normalize/de-norm round trip: z -> bps -> z is the identity.
  2. MAE magnitude convention: a negatively-stored MAE label yields a POSITIVE z.
  3. Fold PIT: every emitted row satisfies trained_through < session.
  4. Holdout guard: sessions >= HOLDOUT_START are never emitted.

Fold logic is exercised through emit_fold_frame, the pure core factored out of
the training loop, so no model is fit here.
"""

from __future__ import annotations

import polars as pl
import pytest

from enginev51.apps import train_a1
from enginev51.models.cv import Fold
from enginev51.protocol import HOLDOUT_START

H60, H120 = 60, 120


# --------------------------------------------------------------------------- 1. z round trip


@pytest.mark.parametrize("z", [-2.5, -0.3, 0.0, 0.75, 1.9, 4.2])
@pytest.mark.parametrize("vol20", [0.005, 0.02, 0.08])
@pytest.mark.parametrize("h", [H60, H120])
def test_z_bps_round_trip_identity(z, vol20, h):
    bps = train_a1.to_bps(z, vol20, h)
    back = train_a1.bps_to_z(bps, vol20, h)
    assert back == pytest.approx(z, rel=1e-12, abs=1e-12)


def test_to_z_inverts_to_bps():
    # label -> z -> bps recovers the label move in bps for a non-magnitude head.
    label, vol20, h = 0.013, 0.02, H60
    z = train_a1.to_z(label, vol20, h)
    assert train_a1.to_bps(z, vol20, h) == pytest.approx(label * 1e4, rel=1e-12)


def test_z_scale_matches_registered_formula():
    assert train_a1.z_scale(H60) == pytest.approx((60 / 390.0) ** 0.5)
    assert train_a1.z_scale(H120) == pytest.approx((120 / 390.0) ** 0.5)


# --------------------------------------------------------------------------- 2. MAE magnitude


def test_mae_negative_label_becomes_positive_z():
    # MAE is stored as a negative log-drawdown; the emitted z must be a magnitude.
    stored_mae = -0.011
    z = train_a1.to_z(stored_mae, vol20=0.02, h_min=H60, magnitude=True)
    assert z > 0
    assert z == pytest.approx(abs(stored_mae) / (0.02 * train_a1.z_scale(H60)))


def test_add_z_labels_mae_is_nonnegative():
    df = pl.DataFrame(
        {
            "f_vol20": [0.02, 0.02],
            "l_fwd_60m": [0.01, -0.01],
            "l_fwd_120m": [0.01, -0.01],
            "l_mfe_60m": [0.015, 0.02],
            "l_mfe_120m": [0.02, 0.03],
            "l_mae_60m": [-0.012, -0.02],  # stored negative
            "l_mae_120m": [-0.018, -0.03],
        }
    )
    out = train_a1.add_z_labels(df)
    assert (out["z_mae60"] >= 0).all()
    assert (out["z_mae120"] >= 0).all()
    # sign of fwd is preserved (not a magnitude head)
    assert out["z_fwd60"][1] < 0


def test_add_z_labels_null_vol_yields_null():
    df = pl.DataFrame(
        {
            "f_vol20": [0.0],  # guarded -> null
            "l_fwd_60m": [0.01], "l_fwd_120m": [0.01],
            "l_mfe_60m": [0.01], "l_mfe_120m": [0.01],
            "l_mae_60m": [-0.01], "l_mae_120m": [-0.01],
        }
    )
    out = train_a1.add_z_labels(df)
    assert out["z_fwd60"][0] is None


# --------------------------------------------------------------------------- 3/4. fold PIT + holdout


def _tick_pool(sessions: list[str]) -> pl.DataFrame:
    """Minimal tick pool: one row per session, only the cols emit_fold_frame touches."""
    return pl.DataFrame(
        {
            "symbol": ["NVDA"] * len(sessions),
            "session": sessions,
            "ts": list(range(len(sessions))),
            "f_vol20": [0.02] * len(sessions),
        }
    )


def test_emit_fold_frame_pit_holds():
    sessions = [f"2026-04-{d:02d}" for d in range(1, 11)]
    pool = _tick_pool(sessions)
    fold = Fold(train_sessions=tuple(sessions[:5]), test_sessions=tuple(sessions[5:]))
    emit = train_a1.emit_fold_frame(3, fold, pool)
    assert emit.height == 5
    assert (emit["trained_through"] < emit["session"]).all()
    assert (emit["fold_id"] == 3).all()
    assert emit["trained_through"][0] == sessions[4]


def test_emit_fold_frame_strips_holdout():
    # test block straddles the seal; holdout sessions must never be emitted.
    sessions = ["2026-05-28", "2026-05-29", "2026-06-01", "2026-06-02"]
    pool = _tick_pool(sessions)
    fold = Fold(
        train_sessions=("2026-05-26", "2026-05-27"),
        test_sessions=tuple(sessions),
    )
    emit = train_a1.emit_fold_frame(0, fold, pool)
    assert emit.height == 2
    assert (emit["session"] < HOLDOUT_START.isoformat()).all()
    assert set(emit["session"].to_list()) == {"2026-05-28", "2026-05-29"}


def test_emit_fold_frame_empty_when_no_tick_rows_in_block():
    pool = _tick_pool(["2026-04-01", "2026-04-02"])
    fold = Fold(train_sessions=("2026-04-01",), test_sessions=("2026-04-10",))
    emit = train_a1.emit_fold_frame(1, fold, pool)
    assert emit.height == 0


# --------------------------------------------------------------------------- params


def test_quantile_params_sets_alpha_alias():
    p = train_a1.quantile_params(0.75)
    assert p["objective"] == "quantile"
    # huber_delta is LightGBM's alias for alpha -> carries the quantile level.
    assert p["huber_delta"] == 0.75
    assert p["seed"] == train_a1.lgbm.DEFAULT_PARAMS["seed"]


def test_contract_columns_frozen():
    assert train_a1.CONTRACT_COLS == (
        "symbol", "session", "ts",
        "pred_fwd60_z", "pred_fwd120_z",
        "pred_mfe60_q50_z", "pred_mfe60_q75_z", "pred_mae60_q75_z",
        "pred_mfe120_q50_z", "pred_mfe120_q75_z", "pred_mae120_q75_z",
        "vol20", "fold_id", "trained_through",
    )
