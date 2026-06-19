param(
    [string]$ExpectedKey = ""
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

function Show-File {
    param([string]$Path)
    Write-Host "--- $Path ---"
    if (Test-Path -LiteralPath $Path) {
        Get-Item -LiteralPath $Path | Select-Object FullName, Length, LastWriteTime | Format-List
        Write-Host "ACL:"
        icacls $Path
        Write-Host "Content:"
        Get-Content -LiteralPath $Path
        if ($ExpectedKey) {
            $content = Get-Content -LiteralPath $Path -Raw
            Write-Host "Contains expected key: $($content.Contains($ExpectedKey))"
        }
    } else {
        Write-Host "missing"
    }
}

Write-Host "USER=$env:USERNAME"
Write-Host "PROFILE=$env:USERPROFILE"
Write-Host "--- whoami /groups ---"
whoami /groups

Write-Host "--- User .ssh directory ---"
$userSshDir = Join-Path $env:USERPROFILE ".ssh"
if (Test-Path -LiteralPath $userSshDir) {
    Get-ChildItem -Force -LiteralPath $userSshDir | Select-Object Mode, Length, LastWriteTime, Name | Format-Table -AutoSize
    icacls $userSshDir
} else {
    Write-Host "missing"
}

Show-File (Join-Path $userSshDir "authorized_keys")

Write-Host "--- ProgramData ssh directory ---"
if (Test-Path -LiteralPath "C:\ProgramData\ssh") {
    Get-ChildItem -Force -LiteralPath "C:\ProgramData\ssh" | Select-Object Mode, Length, LastWriteTime, Name | Format-Table -AutoSize
} else {
    Write-Host "missing"
}

Show-File "C:\ProgramData\ssh\sshd_config"
Show-File "C:\ProgramData\ssh\administrators_authorized_keys"
