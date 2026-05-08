# RS125 TFT Dashboard

Pixel-faithful LVGL port of the Aprilia RS125 dashboard Python simulator.

## Quick start — simulator

```bash
# 1. Clone LVGL 9.x next to this repo
git clone --depth=1 --branch v9.2.0 https://github.com/lvgl/lvgl.git lvgl
cp lv_conf.h lvgl/

# 2. Install SDL2
#   Windows (MinGW): pacman -S mingw-w64-x86_64-SDL2
#   Linux:           sudo apt install libsdl2-dev

# 3. Convert fonts (requires Node + lv_font_conv)
npm install -g lv_font_conv
# Place TTF files in source_fonts/
.\tools\convert_fonts.ps1   # PowerShell
# or: bash tools/convert_fonts.sh  (TODO: add .sh wrapper if needed)

# 4. Build + run
.\tools\build_sim.ps1
```

Keys in simulator:
- `T` — cycle theme
- `D` — restart demo sequence
- `UP/DOWN` — RPM
- `W/S` — speed
- `ESC` — quit

## Quick start — ESP32

```bash
# In ESP-IDF PowerShell environment:
.\tools\build_esp32.ps1 -Port COM3
```

## Folder structure

```
common/          Single source of UI truth (dash_ui.c)
rs125_dash/      ESP-IDF firmware project
dash_sim/        SDL desktop simulator
tools/           Build + font conversion scripts
source_fonts/    Place TTF files here
lvgl/            Clone LVGL 9.x here
lv_conf.h        LVGL config (copy into lvgl/)
PIN_MAPPING.md   Hardware GPIO reference — verify before flashing
```

## Architecture

All rendering lives in `common/dash_ui.c`. The ESP32 and simulator only differ
in display init and data source. Visual output must be identical on both targets.
