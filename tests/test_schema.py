"""Tests for enginev51.plans.schema — TargetSpec.frac validation.

Code review 2026-07-28 N1: ``TargetSpec.frac`` (the fraction of the position
to take off at this level) was documented as ``(0, 1]`` but never enforced at
construction. ``TradePlan.__post_init__`` only checks that the *sum* of target
fracs across a plan does not exceed 1.0 — a single out-of-range frac (0,
negative, > 1) could still slip through if the sum happened to stay <= 1.0.
"""

from __future__ import annotations

import pytest

from enginev51.plans.schema import TargetSpec


def test_target_spec_accepts_frac_one() -> None:
    TargetSpec(price=101.0, frac=1.0)


def test_target_spec_accepts_frac_half() -> None:
    TargetSpec(price=101.0, frac=0.5)


def test_target_spec_rejects_zero_frac() -> None:
    with pytest.raises(ValueError, match=r"frac must be in \(0, 1\]"):
        TargetSpec(price=101.0, frac=0.0)


def test_target_spec_rejects_negative_frac() -> None:
    with pytest.raises(ValueError, match=r"frac must be in \(0, 1\]"):
        TargetSpec(price=101.0, frac=-0.1)


def test_target_spec_rejects_frac_above_one() -> None:
    with pytest.raises(ValueError, match=r"frac must be in \(0, 1\]"):
        TargetSpec(price=101.0, frac=1.5)
