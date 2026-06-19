param(
    [string]$HostAddress = "0.0.0.0",
    [int]$Port = 8088,
    [string]$JobsDir = "var\jobs",
    [int]$MaxUploadMb = 300,
    [int]$Workers = 1
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "Virtual environment not found. Running setup..."
    & (Join-Path $PSScriptRoot "setup_windows.ps1")
}

Set-Location $Root
& $PythonExe -m bomcheck_toolkit.webapp --host $HostAddress --port $Port --jobs-dir $JobsDir --max-upload-mb $MaxUploadMb --workers $Workers
