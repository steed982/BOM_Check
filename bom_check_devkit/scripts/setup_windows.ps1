param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Venv = Join-Path $Root ".venv"

Set-Location $Root

if (-not (Test-Path $Venv)) {
    Write-Host "Creating virtual environment..."
    Invoke-Expression "$Python -m venv `"$Venv`""
}

$PythonExe = Join-Path $Venv "Scripts\python.exe"
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -e .

Write-Host "Setup complete."
Write-Host "Run: .\scripts\run_web_windows.ps1"
