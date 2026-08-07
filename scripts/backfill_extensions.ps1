# Detached extension-download runner (ledger: M3-A0-v1.1-ext-2024, -ext-googl).
# Sequential (shares the ~200 req/min account cap anyway); each stage resumes
# from existing partitions, so re-running after any interruption is safe.
# Launch detached:  Start-Process pwsh -ArgumentList '-File', 'scripts\backfill_extensions.ps1' -WindowStyle Hidden
$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:HIST_REQUESTS_PER_MINUTE = "250"
$env:PYTHONIOENCODING = "utf-8"
$log = "logs\backfill_ext.log"
New-Item -ItemType Directory -Force logs | Out-Null

"=== extension backfill started $(Get-Date -Format o) ===" | Add-Content $log
uv run python -m enginev51.apps.backfill ticks --symbols MU    --start 2024-01-02 --end 2025-08-29 2>&1 | Add-Content $log
"=== MU done $(Get-Date -Format o) ===" | Add-Content $log
uv run python -m enginev51.apps.backfill ticks --symbols GOOGL --start 2025-09-02 --end 2026-05-31 2>&1 | Add-Content $log
"=== GOOGL done $(Get-Date -Format o) ===" | Add-Content $log
uv run python -m enginev51.apps.backfill ticks --symbols NVDA  --start 2024-01-02 --end 2025-08-29 2>&1 | Add-Content $log
"=== ALL DONE $(Get-Date -Format o) ===" | Add-Content $log
