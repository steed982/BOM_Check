param(
    [Parameter(Mandatory = $true)]
    [string]$PublicKey,
    [string]$TargetPath = "C:\ProgramData\ssh\administrators_authorized_keys"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$TargetDir = Split-Path -Parent $TargetPath
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

if (-not (Test-Path -LiteralPath $TargetPath)) {
    New-Item -ItemType File -Force -Path $TargetPath | Out-Null
}

$existing = Get-Content -LiteralPath $TargetPath -Raw -ErrorAction SilentlyContinue
if ($existing -and $existing.Contains($PublicKey)) {
    Write-Host "SSH key already present: $TargetPath"
} else {
    Add-Content -LiteralPath $TargetPath -Value $PublicKey
    Write-Host "SSH key added: $TargetPath"
}

icacls $TargetPath /inheritance:r | Out-Null
icacls $TargetPath /grant "SYSTEM:F" "Administrators:F" | Out-Null

Write-Host "ACL:"
icacls $TargetPath
