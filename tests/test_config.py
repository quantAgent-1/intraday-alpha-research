"""Config sanity tests: research config loads and matches config/settings.toml,
and the cross-layer contracts import cleanly with the frozen/hashable shapes
that let them cross layer boundaries safely.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from enginev51 import contracts
from enginev51.config import (
    _engineV2_env_path,
    _legacy_data_dir_path,
    get_research_config,
    get_settings,
)


def test_research_config_loads() -> None:
    cfg = get_research_config()
    assert cfg.universe_tick == ("NVDA", "TSLA", "AMD", "MU")
    assert cfg.k_slots == 2
    assert cfg.latency_s == (5.0, 25.0)
    assert cfg.notional_research_usd == 10000.0
    assert cfg.deploy_equity_usd == 1000.0


def test_contracts_import_cleanly() -> None:
    assert contracts.Bar is not None
    assert contracts.TradeTick is not None
    assert contracts.QuoteTick is not None
    assert contracts.DetectorState is not None


def test_detector_state_frozen_and_hashable() -> None:
    state = contracts.DetectorState(
        symbol="NVDA",
        ts=0,
        payer="gap_mr",
        active=True,
        direction=1,
        strength=0.5,
        horizon_min=15,
    )
    try:
        state.strength = 0.9  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        pass
    else:
        raise AssertionError("DetectorState should be frozen")

    hash(state)
    assert {state, state} == {state}


def test_extra_env_path_override_wins(monkeypatch) -> None:
    monkeypatch.setenv("ENGINEV51_EXTRA_ENV", r"D:\somewhere\custom.env")
    assert _engineV2_env_path() == r"D:\somewhere\custom.env"


def test_extra_env_path_legacy_alias_wins(monkeypatch) -> None:
    monkeypatch.delenv("ENGINEV51_EXTRA_ENV", raising=False)
    monkeypatch.setenv("ENGINEV51_ENGINEV2_ENV", r"D:\somewhere\legacy_alias.env")
    assert _engineV2_env_path() == r"D:\somewhere\legacy_alias.env"


def test_extra_env_path_default_empty(monkeypatch) -> None:
    monkeypatch.delenv("ENGINEV51_EXTRA_ENV", raising=False)
    monkeypatch.delenv("ENGINEV51_ENGINEV2_ENV", raising=False)
    assert _engineV2_env_path() == ""


def test_legacy_data_dir_path_override_wins(monkeypatch) -> None:
    monkeypatch.setenv("ENGINEV51_LEGACY_DATA_DIR", r"D:\somewhere\legacy")
    assert _legacy_data_dir_path() == r"D:\somewhere\legacy"


def test_legacy_data_dir_path_default_empty(monkeypatch) -> None:
    monkeypatch.delenv("ENGINEV51_LEGACY_DATA_DIR", raising=False)
    monkeypatch.delenv("LEGACY_DATA_DIR", raising=False)
    assert _legacy_data_dir_path() == ""


def test_get_settings_legacy_data_dir_override_wins(monkeypatch, tmp_path) -> None:
    override = tmp_path / "custom_legacy"
    monkeypatch.setenv("ENGINEV51_LEGACY_DATA_DIR", str(override))
    assert get_settings().legacy_data_dir == override


def test_get_settings_legacy_data_dir_default_empty(monkeypatch) -> None:
    monkeypatch.delenv("ENGINEV51_LEGACY_DATA_DIR", raising=False)
    monkeypatch.delenv("LEGACY_DATA_DIR", raising=False)
    assert get_settings().legacy_data_dir == Path("")


def test_field_name_env_var_is_honored_when_prefixed_one_is_absent(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.delenv("ENGINEV51_LEGACY_DATA_DIR", raising=False)
    field_route = tmp_path / "field_name_route"
    monkeypatch.setenv("LEGACY_DATA_DIR", str(field_route))
    assert _legacy_data_dir_path() == str(field_route)
    assert get_settings().legacy_data_dir == field_route
