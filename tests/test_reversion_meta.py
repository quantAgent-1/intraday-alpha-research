"""M18 §6.6 — meta walk-forward fold boundaries (no leakage).

For every fold: max(train ts) < min(score-month ts). Also checks the calendar
stratum locked definitions and the <13-month no-score fallback.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl

from enginev51.reversion.meta import calendar_stratum, walk_forward


def _synth_events(n_months: int, per_month: int, *, seed: int = 0) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    y, m = 2024, 1
    for _ in range(n_months):
        for _ in range(per_month):
            day = int(rng.integers(1, 27))
            trigger = dt.datetime(y, m, day, int(rng.integers(14, 20)),
                                  int(rng.integers(0, 60)), tzinfo=dt.UTC)
            ts = int(trigger.timestamp() * 1e9)
            eps = float(rng.normal(0, 0.3))
            rows.append({
                "symbol": rng.choice(["TSLA", "MU"]),
                "session": f"{y:04d}-{m:02d}-{day:02d}",
                "side": int(rng.choice([-1, 1])),
                "trigger_ts": ts,
                "eps_trigger": eps,
                "theta": 0.0,
                "kappa": float(rng.uniform(0.005, 0.05)),
                "ou_sigma": float(rng.uniform(0.05, 0.4)),
                "spread_bps": float(rng.uniform(1, 8)),
                "sigma_5m": float(rng.uniform(0.1, 0.6)),
                "ofi_5s": float(rng.normal(0, 3)),
                "micro_dev_bps": float(rng.normal(0, 2)),
                "et_minute": int(rng.integers(600, 940)),
                "maker_filled": True,
                # a learnable-ish label so LightGBM has something to fit
                "net_bps": float(eps * 5 + rng.normal(0, 4)),
            })
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return pl.DataFrame(rows)


def test_fold_boundaries_no_leakage():
    ev = _synth_events(14, 120, seed=1)
    res = walk_forward(ev)
    assert res.trained
    assert len(res.folds) >= 1
    for f in res.folds:
        # THE leakage invariant: every training row precedes every scored row.
        assert f.max_train_ts < f.min_score_ts, (
            f"fold {f.score_month}: max_train_ts {f.max_train_ts} "
            f">= min_score_ts {f.min_score_ts}"
        )
        assert f.n_train > 0 and f.n_score > 0
    # meta columns exist; scored rows carry a probability, veto = p<0.55.
    assert {"meta_p", "meta_kept"}.issubset(res.events.columns)
    scored = res.events.filter(pl.col("meta_p").is_not_nan())
    if scored.height:
        p = scored["meta_p"].to_numpy()
        kept = scored["meta_kept"].to_numpy()
        assert np.array_equal(kept, p >= 0.55)


def test_under_13_months_no_scoring():
    ev = _synth_events(6, 80, seed=2)
    res = walk_forward(ev)
    assert not res.trained
    assert res.folds == []
    # no veto when there is no model (gates-only fallback / smoke).
    assert bool(res.events["meta_kept"].all())
    assert res.events["meta_p"].is_nan().all()  # unscored → NaN sentinel
    assert not bool(res.events["meta_scored"].any())  # nothing scored


def _synth_pooled(seed: int = 7) -> pl.DataFrame:
    """Multi-name pooled events with gate columns and staggered start dates:
    MU present from 2024-01 (anchors months 1-12), NVDA/TSLA only from 2025-09 —
    exactly the M18 pooled-window shape. ~25 % of trades are GATED."""
    rng = np.random.default_rng(seed)
    rows = []
    y, m = 2024, 1
    for _ in range(18):  # 2024-01 .. 2025-06 → first score month (13th) = 2025-01
        for _ in range(200):
            nm = str(rng.choice(["MU", "NVDA", "TSLA"]))
            if nm != "MU" and (y, m) < (2025, 9):
                nm = "MU"  # others have no pre-2025-09 history
            day = int(rng.integers(1, 27))
            trigger = dt.datetime(y, m, day, int(rng.integers(14, 20)),
                                  int(rng.integers(0, 60)), tzinfo=dt.UTC)
            ts = int(trigger.timestamp() * 1e9)
            eps = float(rng.normal(0, 0.3))
            rows.append({
                "symbol": nm, "session": f"{y:04d}-{m:02d}-{day:02d}",
                "side": int(rng.choice([-1, 1])), "trigger_ts": ts, "eps_trigger": eps,
                "theta": 0.0, "kappa": float(rng.uniform(0.005, 0.05)),
                "ou_sigma": float(rng.uniform(0.05, 0.4)), "spread_bps": float(rng.uniform(1, 8)),
                "sigma_5m": float(rng.uniform(0.1, 0.6)), "ofi_5s": float(rng.normal(0, 3)),
                "micro_dev_bps": float(rng.normal(0, 2)), "et_minute": int(rng.integers(600, 940)),
                "maker_filled": True, "passed_G1": bool(rng.random() < 0.5),
                "passed_G2": bool(rng.random() < 0.5),
                "net_bps": float(eps * 5 + rng.normal(0, 4)),
            })
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return pl.DataFrame(rows)


def test_pooled_fold_boundary_invariant():
    ev = _synth_pooled()
    res = walk_forward(ev)
    assert res.trained
    assert len(res.folds) == len(res.boosters) >= 1
    # THE pooled-fold leakage invariant across every fold.
    for f in res.folds:
        assert f.max_train_ts < f.min_score_ts, (
            f"fold {f.score_month}: max_train_ts {f.max_train_ts} >= min_score_ts {f.min_score_ts}"
        )
    # First scored month = the 13th pooled month (pool starts 2024-01 → 2025-01).
    assert res.folds[0].score_month == "2025-01"


def test_pooled_training_population_is_gated_only():
    # BUILD-SPEC §4: only GATED trades are scored; a non-gated maker-filled trade
    # is never assigned a probability (meta_scored stays False).
    ev = _synth_pooled(seed=9)
    res = walk_forward(ev)
    scored = res.events.filter(pl.col("meta_scored"))
    assert scored.height > 0
    assert scored.filter(~(pl.col("passed_G1") & pl.col("passed_G2"))).height == 0
    # scored rows carry a probability; veto = p<0.55.
    p = scored["meta_p"].to_numpy()
    kept = scored["meta_kept"].to_numpy()
    assert np.array_equal(kept, p >= 0.55)


def test_calendar_strata_locked_defs():
    # 3rd Friday of Oct 2025 = 2025-10-17 → MONTHLY_OPEX (non-quarterly month).
    assert calendar_stratum("2025-10-17") == "MONTHLY_OPEX"
    # 3rd Friday of Jun 2025 = 2025-06-20 → QUAD_WITCH (Mar/Jun/Sep/Dec).
    assert calendar_stratum("2025-06-20") == "QUAD_WITCH"
    # Last trading session of Sep 2025 = 2025-09-30 → MONTH_END.
    assert calendar_stratum("2025-09-30") == "MONTH_END"
    # A plain mid-month day → ORDINARY.
    assert calendar_stratum("2025-09-10") == "ORDINARY"
