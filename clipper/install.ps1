# One-time setup for autoclip. Run from this folder:  .\install.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $py) { Write-Host "Python 3.10+ is required: https://www.python.org/downloads/" -ForegroundColor Red; exit 1 }

Write-Host "Installing streamlink and faster-whisper..."
python -m pip install --user --upgrade -r requirements.txt
if (-not $?) { exit 1 }

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "ffmpeg not found - installing with winget..."
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    Write-Host "Open a NEW terminal so ffmpeg is on PATH." -ForegroundColor Yellow
}

python test_detector.py
Write-Host ""
Write-Host "Ready. Examples:" -ForegroundColor Green
Write-Host '  python autoclip.py kaicenat'
Write-Host '  python autoclip.py --game "Grand Theft Auto VI" --top 3 --lang en'
