# One study cycle. Point a scheduler at this.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$log = Join-Path $root "data\logs\study-$(Get-Date -Format 'yyyy-MM-dd').log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

"=== cycle started $(Get-Date -Format 'u') ===" | Add-Content -Encoding utf8 $log
try {
    python -m nicomachus study 2>&1 | Tee-Object -Append -FilePath $log
    "=== cycle finished $(Get-Date -Format 'u') ===" | Add-Content -Encoding utf8 $log
} catch {
    "!!! cycle failed: $_" | Add-Content -Encoding utf8 $log
    exit 1
}
