# Phase 2: re-download NVDA/TSLA 2025-09..2026-05 WITH condition codes (--force
# shadows the stripped legacy copies). Resumable; safe to re-run.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:HIST_REQUESTS_PER_MINUTE = "250"
$env:PYTHONIOENCODING = "utf-8"
$log = "logs\backfill_phase2.log"
New-Item -ItemType Directory -Force logs | Out-Null
"=== phase2 started $(Get-Date -Format o) ===" | Add-Content $log
uv run python -m enginev51.apps.backfill ticks --symbols TSLA --start 2025-09-02 --end 2026-05-31 --force 2>&1 | Add-Content $log
"=== TSLA re-download done $(Get-Date -Format o) ===" | Add-Content $log
uv run python -m enginev51.apps.backfill ticks --symbols NVDA --start 2025-09-02 --end 2026-05-31 --force 2>&1 | Add-Content $log
"=== NVDA re-download done $(Get-Date -Format o) ===" | Add-Content $log
