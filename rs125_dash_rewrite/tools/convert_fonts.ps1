<#
.SYNOPSIS
    Converts source TTF fonts to LVGL C font arrays using lv_font_conv.
    Run from repo root: .\tools\convert_fonts.ps1

.REQUIREMENTS
    Node.js + lv_font_conv:  npm install -g lv_font_conv
    Source TTFs in ./source_fonts/
#>

$ErrorActionPreference = "Stop"

$originalDir = Get-Location
Set-Location ..

$out = "common/assets/fonts"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$fonts = @(
    @{ file="Roboto-BoldItalic.ttf"; name="font_roboto_bolditalic_20";  size=20;  bpp=4; range="0x30-0x39,0x41-0x5A" },
    @{ file="OpenSauceOne-Bold.ttf"; name="font_opensauceone_bold_96";  size=96;  bpp=4; range="0x30-0x39,0x41-0x5A,0x4E" },
    @{ file="Roboto-BoldItalic.ttf"; name="font_roboto_bolditalic_162"; size=162; bpp=4; range="0x30-0x39" },
    @{ file="OpenSauceOne-Regular.ttf"; name="font_opensauceone_regular_25"; size=25; bpp=4; range="0x20-0x7E" },
    @{ file="OpenSans-Regular.ttf"; name="font_opensans_regular_28"; size=28; bpp=4; range="0x20-0x7E" },
    @{ file="OpenSans-Regular.ttf"; name="font_opensans_regular_20"; size=20; bpp=4; range="0x20-0x7E" },
    @{ file="OpenSans-Regular.ttf"; name="font_opensans_regular_17"; size=17; bpp=4; range="0x20-0x7E,0xB0" },
    @{ file="OpenSans-Bold.ttf";    name="font_opensans_bold_26";    size=26; bpp=4; range="0x20-0x7E,0xB0" }
)

foreach ($f in $fonts) {
    $src = "source_fonts\$($f.file)"
    $dst = "$out/$($f.name).c"
    if (!(Test-Path $src)) {
        Write-Warning "Missing font: $src - skipping"
        continue
    }
    Write-Host "Converting $($f.name) (size $($f.size))..."
    lv_font_conv `
        --font $src `
        --size $($f.size) `
        --bpp  $($f.bpp) `
        --range $($f.range) `
        --format lvgl `
        --lv-font-name $($f.name) `
        -o $dst
    if ($LASTEXITCODE -ne 0) { throw "lv_font_conv failed for $($f.name)" }
}

Write-Host "Font conversion complete. Files in $out"
Set-Location $originalDir   
