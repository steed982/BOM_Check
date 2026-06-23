param(
    [string]$TaskName = "BOM Check Web",
    [string]$HostAddress = "0.0.0.0",
    [int]$Port = 8088,
    [string]$JobsDir = "var\jobs",
    [int]$MaxUploadMb = 300,
    [int]$Workers = 1
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$RunScript = Join-Path $Root "scripts\run_web_windows.ps1"

if (-not (Test-Path $RunScript)) {
    throw "Cannot find run script: $RunScript"
}

$Args = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$RunScript`"",
    "-HostAddress", $HostAddress,
    "-Port", $Port,
    "-JobsDir", "`"$JobsDir`"",
    "-MaxUploadMb", $MaxUploadMb,
    "-Workers", $Workers
) -join " "

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $Args
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description "BOM Check LAN web service" `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName

Write-Host "Scheduled task installed and started: $TaskName"
Write-Host "URL: http://<server-ip>:$Port"
