Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  AI-for-Education - Local Start    " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$app = Join-Path $PSScriptRoot "app.py"

if (-not (Test-Path $python)) {
    Write-Host "ERROR: Missing local venv interpreter: $python" -ForegroundColor Red
    Write-Host "Please create or repair .venv first." -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "Python: $python" -ForegroundColor Green
Write-Host "App:    http://localhost:5000" -ForegroundColor Green
Write-Host "Admin:  http://localhost:5000/admin" -ForegroundColor Green
Write-Host ""

& $python $app
