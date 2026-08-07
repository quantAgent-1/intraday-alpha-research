"""Settings for enginev5.1.

Two layers, deliberately separate:
- `Settings` (pydantic-settings): secrets + operational knobs from `.env`
  (standard Alpaca / Databento variable names).
- `ResearchConfig`: research constants from `config/settings.toml`. These are
  protocol-bound — changing [splits] after results exist voids them (PROTOCOL v6).

Public portfolio build: no machine-local absolute paths. Credentials come only from
the project `.env` (or process environment). An optional secondary lake root can be
set via ``ENGINEV51_LEGACY_DATA_DIR`` / ``LEGACY_DATA_DIR`` for multi-root reads.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Optional extra env-file path (for multi-project setups). Empty by default —
# the project-local `.env` is always the primary credential source.
_EXTRA_ENV_DEFAULT = ""
# Optional read-only secondary lake. Empty by default (single-root primary only).
_LEGACY_DATA_DIR_DEFAULT = ""


def _extra_env_path() -> str:
    """Optional secondary env file path.

    Precedence: ``ENGINEV51_EXTRA_ENV`` > ``ENGINEV51_ENGINEV2_ENV`` (legacy alias)
    > empty (project `.env` only).
    """
    for var in ("ENGINEV51_EXTRA_ENV", "ENGINEV51_ENGINEV2_ENV"):
        value = os.environ.get(var)
        if value:
            return value
    return _EXTRA_ENV_DEFAULT


# Back-compat alias used by older tests / call sites.
def _engineV2_env_path() -> str:
    return _extra_env_path()


def _legacy_data_dir_path() -> str:
    """Path to an optional secondary lake root (read-only).

    Precedence, highest first:

    1. ``ENGINEV51_LEGACY_DATA_DIR`` — project-prefixed override;
    2. ``LEGACY_DATA_DIR`` — pydantic field-name variable (``env_prefix=""``);
    3. empty string → no secondary root.

    An explicit ``Settings(legacy_data_dir=...)`` kwarg still outranks all three.
    """
    for var in ("ENGINEV51_LEGACY_DATA_DIR", "LEGACY_DATA_DIR"):
        value = os.environ.get(var)
        if value:
            return value
    return _LEGACY_DATA_DIR_DEFAULT


def _env_files() -> tuple[str, ...]:
    """Ordered env files for pydantic-settings (later entries win)."""
    files: list[str] = []
    extra = _extra_env_path()
    if extra:
        files.append(extra)
    files.append(str(PROJECT_ROOT / ".env"))
    return tuple(files)


class Settings(BaseSettings):
    # No secrets are stored in this repo. Put keys in a local `.env` (gitignored)
    # or export them in the process environment.
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="",
    )

    # --- Market data (historical REST; no order routing in this project) ---
    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""
    alpaca_data_url: str = "https://data.alpaca.markets"
    alpaca_stream_url_stocks: str = "wss://stream.data.alpaca.markets/v2/sip"
    data_feed_type: str = "sip"

    # Stay well under typical REST caps.
    hist_requests_per_minute: int = 2000
    # SIP recency clamp for historical requests (leave margin behind real-time).
    sip_recency_margin_minutes: int = 20

    # --- Databento (optional NOII / BBO acquisition) ---
    # Secret; read from .env only. NEVER logged or printed.
    databento_api_key: str = ""

    # --- paths ---
    data_dir: Path = PROJECT_ROOT / "data"
    log_dir: Path = PROJECT_ROOT / "logs"
    # Optional secondary lake root (read-only). New partitions always land in
    # data_dir; reads union both roots when the secondary exists, primary first.
    # Unset = empty Path("") — never Path(".") (cwd), which could accidentally
    # pick up a local raw/ directory.
    legacy_data_dir: Path = Path(_LEGACY_DATA_DIR_DEFAULT)

    tz_display: str = "UTC"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def read_roots(self) -> tuple[Path, ...]:
        """Raw-lake roots for READS, primary first. Writes go to raw_dir only."""
        secondary = self.legacy_data_dir
        # Path("") and Path(".") are both "unset" for public/default builds.
        if str(secondary) in ("", "."):
            return (self.raw_dir,)
        legacy_raw = secondary / "raw"
        return (self.raw_dir, legacy_raw) if legacy_raw.is_dir() else (self.raw_dir,)


@dataclass(slots=True, frozen=True)
class ResearchConfig:
    """Protocol-bound constants from config/settings.toml."""

    universe_tick: tuple[str, ...]
    universe_bar_signal: tuple[str, ...]
    universe_bar_anchor: tuple[str, ...]
    letf_deploy: tuple[str, ...]

    k_slots: int
    latency_s: tuple[float, float]
    curfew_et: str
    last_entry_et: str
    plan_valid_min_s: int

    train_end: str
    validate_end: str
    holdout_start: str

    notional_research_usd: float
    deploy_equity_usd: float

    disk_floor_gb: float

    commission_usd: float
    sec_taf_sell_bps: float
    slippage_market_bps: float


@lru_cache(maxsize=1)
def get_research_config(path: Path | None = None) -> ResearchConfig:
    p = path or (PROJECT_ROOT / "config" / "settings.toml")
    with open(p, "rb") as f:
        t = tomllib.load(f)
    return ResearchConfig(
        universe_tick=tuple(t["universe"]["tick"]),
        universe_bar_signal=tuple(t["universe"]["bar_signal"]),
        universe_bar_anchor=tuple(t["universe"]["bar_anchor"]),
        letf_deploy=tuple(t["universe"]["letf_deploy"]),
        k_slots=int(t["execution"]["k_slots"]),
        latency_s=tuple(float(x) for x in t["execution"]["latency_s"]),  # type: ignore[arg-type]
        curfew_et=str(t["execution"]["curfew_et"]),
        last_entry_et=str(t["execution"]["last_entry_et"]),
        plan_valid_min_s=int(t["execution"]["plan_valid_min_s"]),
        train_end=str(t["splits"]["train_end"]),
        validate_end=str(t["splits"]["validate_end"]),
        holdout_start=str(t["splits"]["holdout_start"]),
        notional_research_usd=float(t["books"]["notional_research_usd"]),
        deploy_equity_usd=float(t["books"]["deploy_equity_usd"]),
        disk_floor_gb=float(t["storage"]["disk_floor_gb"]),
        commission_usd=float(t["costs"]["commission_usd"]),
        sec_taf_sell_bps=float(t["costs"]["sec_taf_sell_bps"]),
        slippage_market_bps=float(t["costs"]["slippage_market_bps"]),
    )


def get_settings() -> Settings:
    legacy = _legacy_data_dir_path()
    return Settings(
        _env_file=_env_files(),
        legacy_data_dir=Path(legacy) if legacy else Path(""),
    )
