# One-shot API key setup for Nicomachus.
#
#   powershell -ExecutionPolicy Bypass -File scripts\add-key.ps1
#
# Prompts once for a key (input hidden), then:
#   - sets it as a User environment variable on this machine
#   - sets it as a GitHub Actions secret on the nicomachus repo (needs gh auth)
# The key is never written to disk or shown on screen.

param(
    [ValidateSet('anthropic','gemini')]
    [string]$Provider = 'anthropic',
    [string]$Repo = 'tmvarun55-maker/nicomachus'
)

$varName = if ($Provider -eq 'gemini') { 'GEMINI_API_KEY' } else { 'ANTHROPIC_API_KEY' }

Write-Host ""
Write-Host "Paste your $Provider API key and press Enter (it will not be shown):"
$secure = Read-Host -AsSecureString
$key = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))

if ([string]::IsNullOrWhiteSpace($key)) {
    Write-Host "No key entered. Nothing changed." -ForegroundColor Yellow
    exit 1
}

# 1. Local machine (User scope) - survives reboots, picked up by new terminals.
[Environment]::SetEnvironmentVariable($varName, $key, 'User')
Set-Item -Path "env:$varName" -Value $key
Write-Host "  local:  $varName set for your user account" -ForegroundColor Green

# 2. GitHub Actions secret - for the nightly autonomous run.
$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($gh) {
    $key | & gh secret set $varName --repo $Repo 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  github: $varName set as an Actions secret on $Repo" -ForegroundColor Green
        if ($Provider -eq 'gemini') {
            Write-Host "  note:   edit .github/workflows/study.yml -> change ANTHROPIC_API_KEY to GEMINI_API_KEY" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  github: could not set secret (is 'gh auth status' ok?). Set it manually at:" -ForegroundColor Yellow
        Write-Host "          https://github.com/$Repo/settings/secrets/actions"
    }
} else {
    Write-Host "  github: gh CLI not found - set the secret manually at:" -ForegroundColor Yellow
    Write-Host "          https://github.com/$Repo/settings/secrets/actions"
}

$key = $null
Write-Host ""
Write-Host "Done. Close this terminal, open a new one, and run:  nicomachus.bat" -ForegroundColor Cyan
