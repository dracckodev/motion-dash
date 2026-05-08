<#
.SYNOPSIS
    Builds the ESP32-S3 firmware using ESP-IDF v5.x.
    Run from repo root: .\tools\build_esp32.ps1

.REQUIREMENTS
    ESP-IDF v5.x installed and idf.py on PATH (run ESP-IDF PowerShell env first).
    Optional: pass -Port COM3 to flash after build.
#>

param(
    [string]$Port = ""
)

$ErrorActionPreference = "Stop"
Push-Location rs125_dash

Write-Host "=== Building rs125_dash (ESP32-S3) ===" -ForegroundColor Cyan
idf.py build
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Build failed" }

if ($Port -ne "") {
    Write-Host "=== Flashing to $Port ===" -ForegroundColor Yellow
    idf.py -p $Port flash monitor
}

Pop-Location
Write-Host "Done." -ForegroundColor Green
