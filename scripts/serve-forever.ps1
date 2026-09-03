# Supervisor: keeps the Nicomachus web server up. If it ever exits - crash or
# clean - this waits a moment and starts it again. The Scheduled Task runs
# this, not the server directly, so a one-off failure never leaves it down.

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$port = if ($env:NICOMACHUS_PORT) { $env:NICOMACHUS_PORT } else { 8422 }
$log  = Join-Path $root 'data\logs\server.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

while ($true) {
    "$(Get-Date -Format 'u')  starting server on port $port" | Add-Content -Encoding utf8 $log
    try {
        & python -m nicomachus serve --no-open --host 127.0.0.1 --port $port *>> $log
    } catch {
        "$(Get-Date -Format 'u')  supervisor caught: $_" | Add-Content -Encoding utf8 $log
    }
    "$(Get-Date -Format 'u')  server exited, restarting in 5s" | Add-Content -Encoding utf8 $log
    Start-Sleep -Seconds 5
}
