"""The test-isolation guard itself (see ``tests/conftest.py``).

These tests pin the guard that keeps the suite from resolving any real external
lake or credentials file. The public portfolio build has no machine-local
absolute defaults — secondary roots and extra env files are opt-in via env vars.
"""

from __future__ import annotations

import os
from pathlib import Path

from enginev51.config import Settings, get_settings

# Fragments that must never appear in anything a test resolves by default.
FOREIGN_PROJECT_FRAGMENTS = ("engineV5", "engineV2")


def _sandbox_legacy_dir() -> Path:
    return Path(os.environ["ENGINEV51_LEGACY_DATA_DIR"])


def _names_a_foreign_project(path: Path) -> bool:
    return any(frag in str(path) for frag in FOREIGN_PROJECT_FRAGMENTS)


def test_get_settings_uses_sandbox_legacy_lake() -> None:
    """The default resolution path must land in the sandbox from conftest."""
    resolved = get_settings().legacy_data_dir
    assert resolved == _sandbox_legacy_dir()
    assert not _names_a_foreign_project(resolved)


def test_bare_settings_does_not_name_a_foreign_project() -> None:
    """A bare ``Settings()`` must not point at a sibling-project path."""
    resolved = Settings().legacy_data_dir
    assert not _names_a_foreign_project(resolved)


def test_read_roots_do_not_union_a_foreign_lake(tmp_path) -> None:
    """With no secondary lake, reads see exactly one root: the primary."""
    roots = Settings(data_dir=tmp_path, legacy_data_dir=Path("")).read_roots
    assert roots == (tmp_path / "raw",)
    assert not any(_names_a_foreign_project(r) for r in roots)


def test_explicit_kwarg_still_wins(tmp_path) -> None:
    """An explicit kwarg outranks the environment."""
    explicit = tmp_path / "explicitly-chosen-lake"
    assert Settings(legacy_data_dir=explicit).legacy_data_dir == explicit


def test_extra_env_file_is_absent_in_sandbox() -> None:
    """No real credentials file sits on the optional extra env path."""
    guarded = Path(os.environ["ENGINEV51_ENGINEV2_ENV"])
    assert not guarded.exists()


def test_config_defaults_have_no_absolute_machine_paths() -> None:
    """Public build: empty defaults — no hard-coded user home paths."""
    from enginev51.config import _EXTRA_ENV_DEFAULT, _LEGACY_DATA_DIR_DEFAULT

    assert _EXTRA_ENV_DEFAULT == ""
    assert _LEGACY_DATA_DIR_DEFAULT == ""
