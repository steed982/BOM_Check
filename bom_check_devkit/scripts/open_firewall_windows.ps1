param(
    [int]$Port = 8088,
    [string]$RuleName = "BOM Check Web"
)

$ErrorActionPreference = "Stop"
$DisplayName = "$RuleName $Port"

$Existing = Get-NetFirewallRule -DisplayName $DisplayName -ErrorAction SilentlyContinue
if ($Existing) {
    Write-Host "Firewall rule already exists: $DisplayName"
    return
}

New-NetFirewallRule `
    -DisplayName $DisplayName `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort $Port `
    -Action Allow | Out-Null

Write-Host "Firewall rule created: $DisplayName"
