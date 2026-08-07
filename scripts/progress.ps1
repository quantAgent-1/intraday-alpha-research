# Quick progress view for the detached extension backfill.
#   pwsh -File scripts\progress.ps1
Set-Location (Split-Path -Parent $PSScriptRoot)
"=== last log lines ==="
Get-Content logs\backfill_ext.log -Tail 3 -ErrorAction SilentlyContinue
""
"=== extension coverage (trades partitions) ==="
$targets = @(
    @{sym="MU";    pat="2024-*","2025-0[1-8]*"; total=417},
    @{sym="GOOGL"; pat="2025-*","2026-*";       total=187},
    @{sym="NVDA";  pat="2024-*","2025-0[1-8]*"; total=417}
)
foreach ($t in $targets) {
    $n = 0
    foreach ($p in $t.pat) {
        $n += (Get-ChildItem "data\raw\sip\trades\$($t.sym)\$p.parquet" -ErrorAction SilentlyContinue | Measure-Object).Count
    }
    $pct = [math]::Round(100 * $n / $t.total, 1)
    "{0,-6} {1,4}/{2}  ({3}%)" -f $t.sym, $n, $t.total, $pct
}
""
"=== disk free ==="
"{0} GB" -f [math]::Round((Get-PSDrive C).Free/1GB, 1)
"=== runner alive? ==="
if (Get-Process pwsh -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID }) { "yes" } else { "NO - rerun scripts\backfill_extensions.ps1" }
