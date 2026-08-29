# Register a daily study cycle with Windows Task Scheduler.
#
#   powershell -ExecutionPolicy Bypass -File scripts\install_task.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\install_task.ps1 -At 03:30
#   powershell -ExecutionPolicy Bypass -File scripts\install_task.ps1 -Remove
#
# Runs as the current user, only on AC power by default (change -Settings below
# if you want it on battery too).

param(
    [string]$At = "04:00",
    [string]$TaskName = "Nicomachus study cycle",
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $root "scripts\update.ps1"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed scheduled task '$TaskName'."
    return
}

if (-not (Test-Path $script)) { throw "Not found: $script" }

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`"" `
    -WorkingDirectory $root

$trigger = New-ScheduledTaskTrigger -Daily -At $At

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Nicomachus reads, distils notes, and reindexes once a day." `
    -Force | Out-Null

Write-Host "Registered '$TaskName' — daily at $At."
Write-Host "Check it with:  Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "Run it now with: Start-ScheduledTask -TaskName '$TaskName'"
