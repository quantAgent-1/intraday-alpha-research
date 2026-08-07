"""Repo-wide test isolation: no test may resolve a real external lake or secrets.

The suite redirects secondary-lake and optional-env defaults to a throwaway
sandbox for the whole session. Explicit ``Settings(legacy_data_dir=...)`` kwargs
still win (pydantic-settings: init kwargs outrank env).

The sandbox has no ``raw/`` subdirectory and no real ``.env``, so tests cannot
union a foreign lake or load live API credentials by accident.
"""

from __future__ import annotations

import atexit
import os
import shutil
import tempfile
from pathlib import Path

import pytest

# Set at IMPORT time (config may read env at class-definition / first import).
ISOLATION_ROOT = Path(tempfile.mkdtemp(prefix="enginev51-test-isolation-"))
atexit.register(shutil.rmtree, ISOLATION_ROOT, ignore_errors=True)

SANDBOX_LEGACY_DATA_DIR = ISOLATION_ROOT / "legacy_lake"
SANDBOX_LEGACY_DATA_DIR.mkdir(parents=True, exist_ok=True)  # exists, but has no raw/
SANDBOX_EXTRA_ENV = ISOLATION_ROOT / "extra.env"  # deliberately absent

_GUARDED_ENV: dict[str, str] = {
    "ENGINEV51_LEGACY_DATA_DIR": str(SANDBOX_LEGACY_DATA_DIR),
    "ENGINEV51_ENGINEV2_ENV": str(SANDBOX_EXTRA_ENV),  # legacy alias for extra env
    "ENGINEV51_EXTRA_ENV": str(SANDBOX_EXTRA_ENV),
    "LEGACY_DATA_DIR": str(SANDBOX_LEGACY_DATA_DIR),
}

os.environ.update(_GUARDED_ENV)


@pytest.fixture(autouse=True)
def _legacy_lake_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-affirm the sandbox before every test."""
    for key, value in _GUARDED_ENV.items():
        monkeypatch.setenv(key, value)
