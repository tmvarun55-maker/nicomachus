# Run Nicomachus as an always-on background web server on this machine.
#
#   powershell -ExecutionPolicy Bypass -File scripts\service.ps1 install
#   powershell -ExecutionPolicy Bypass -File scripts\service.ps1 status
#   powershell -ExecutionPolicy Bypass -File scripts\service.ps1 restart
#   powershell -ExecutionPolicy Bypass -File scripts\service.ps1 stop
#   powershell -ExecutionPolicy Bypass -File scripts\service.ps1 uninstall
#
# 'install' drops a shortcut in your Startup folder (no admin needed) so the
# server launches hidden at every logon and stays up (supervisor loop). After
# that it is always at http://localhost:8422 whenever you are logged in.

param(
    [Parameter(Position = 0)]
    [ValidateSet('install','uninstall','status','restart','start','stop')]
    [string]$Cmd = 'status',
    [int]$Port = 8422
)

$root    = Split-Path -Parent $PSScriptRoot
$vbs     = Join-Path $root 'scripts\hidden-launch.vbs'
$startup = [Environment]::GetFolderPath('Startup')
$link    = Join-Path $startup 'Nicomachus server.lnk'
$url     = "http://localhost:$Port/"

function Stop-Server {
    Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*serve-forever.ps1*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*nicomachus serve*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

function Start-Server {
    & wscript.exe "$vbs"
}

switch ($Cmd) {

    'install' {
        [Environment]::SetEnvironmentVariable('NICOMACHUS_PORT', "$Port", 'User')
        $env:NICOMACHUS_PORT = "$Port"

        $ws = New-Object -ComObject WScript.Shell
        $sc = $ws.CreateShortcut($link)
        $sc.TargetPath       = "$env:SystemRoot\System32\wscript.exe"
        $sc.Arguments        = "`"$vbs`""
        $sc.WorkingDirectory = $root
        $sc.WindowStyle      = 7
        $sc.Description       = 'Nicomachus local web server'
        $sc.Save()

        Stop-Server
        Start-Sleep -Seconds 1
        Start-Server
        Start-Sleep -Seconds 6

        Write-Host "Installed." -ForegroundColor Green
        Write-Host "  $url"
        Write-Host "  launches hidden at every logon"
        Write-Host "  manage with: scripts\service.ps1 status | restart | stop | uninstall"
    }

    'uninstall' {
        if (Test-Path $link) { Remove-Item $link -Force }
        Stop-Server
        Write-Host "Removed the startup shortcut and stopped the server." -ForegroundColor Yellow
    }

    'start'   { Start-Server; Write-Host "Started." }
    'stop'    { Stop-Server;  Write-Host "Stopped." }
    'restart' { Stop-Server; Start-Sleep -Seconds 2; Start-Server; Write-Host "Restarted." }

    'status' {
        $auto = if (Test-Path $link) { 'installed (Startup shortcut)' } else { 'NOT installed - run: service.ps1 install' }
        Write-Host "autostart: $auto"
        $proc = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandLine -like '*nicomachus serve*' }
        if ($proc) { Write-Host "process  : running (pid $($proc.ProcessId))" }
        else       { Write-Host "process  : not running" }
        try {
            $r = Invoke-WebRequest -UseBasicParsing -Uri ($url + 'api/status') -TimeoutSec 4
            $j = $r.Content | ConvertFrom-Json
            Write-Host "server   : UP at $url" -ForegroundColor Green
            Write-Host "corpus   : $($j.corpus.documents) documents, $($j.chunks) passages"
            $prov = if ($j.provider) { $j.provider } else { 'offline - no API key' }
            Write-Host "provider : $prov"
        } catch {
            Write-Host "server   : not responding on $url yet" -ForegroundColor Yellow
        }
    }
}
