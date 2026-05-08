#pragma once
// ============================================================
//  Font Strategy for the RS125 Dashboard on LVGL
// ============================================================
//
//  The Python/pygame version loads TTF fonts at runtime from the filesystem.
//  On ESP32-S3 (no filesystem for fonts by default) we have two options:
//
//  OPTION A — Embed fonts as C arrays (recommended, used here)
//  ─────────────────────────────────────────────────────────
//  Use the LVGL font converter tool to convert each TTF to a C source file,
//  then declare it as extern lv_font_t here.
//
//  Tool:  https://lvgl.io/tools/fontconverter
//  Or:    pip install lv_font_conv  →  lv_font_conv --ttf <file> ...
//
//  Steps for each font:
//    1. Run lv_font_conv (or the web tool) with:
//         --ttf  <font>.ttf
//         --size <size>
//         --bpp  4          ← 4-bit anti-aliasing (good balance)
//         --format lvgl
//         -o     font_<name>_<size>.c
//         --range 0x20-0x7E,0xB0,0xB2  ← ASCII + ° + ²
//    2. Add the .c file to the CMakeLists SRCS list below.
//    3. Declare it with LV_FONT_DECLARE below.
//
//  OPTION B — SPIFFS / LittleFS + lv_freetype
//  ─────────────────────────────────────────────────────────
//  Flash a SPIFFS partition with the TTF files, then use the LVGL
//  FreeType renderer (CONFIG_LV_USE_FREETYPE=y).  Renders at any size
//  but uses ~80 kB extra RAM per face and is slower.
//
//  We use Option A here because:
//   • Deterministic RAM use
//   • No filesystem dependency
//   • Faster glyph rendering
//
//  Required font files (generate and add to main/ then CMakeLists):
//  ──────────────────────────────────────────────────────────────────
//  font_roboto_bolditalic_162.c   — speed digits (0-9, used at 162 px)
//  font_roboto_bolditalic_20.c    — RPM tick labels
//  font_opensans_bold_26.c        — data strip values
//  font_opensans_regular_20.c     — data strip labels
//  font_opensans_regular_17.c     — data strip units (km/h, °C etc.)
//  font_opensans_regular_28.c     — "km/h" label
//  font_opensauce_bold_96.c       — gear character (large)
//  font_opensauce_regular_25.c    — "GEAR" label
//
//  Until you generate these, the code falls back to the built-in
//  LVGL fonts (LV_FONT_MONTSERRAT_*) — the layout will be correct
//  but the typefaces will differ from the pygame version.
// ============================================================

#include "lvgl.h"

// Declare generated font symbols here (after generating .c files):
// LV_FONT_DECLARE(font_roboto_bolditalic_162);
// LV_FONT_DECLARE(font_roboto_bolditalic_20);
// LV_FONT_DECLARE(font_opensans_bold_26);
// LV_FONT_DECLARE(font_opensans_regular_20);
// LV_FONT_DECLARE(font_opensans_regular_17);
// LV_FONT_DECLARE(font_opensans_regular_28);
// LV_FONT_DECLARE(font_opensauce_bold_96);
// LV_FONT_DECLARE(font_opensauce_regular_25);

// ── Font accessor — returns best available font for each role ──
// Replace the lv_font_default() fallbacks once you add the .c files.

static inline const lv_font_t *font_speed_large(void) {
    // return &font_roboto_bolditalic_162;
    return &lv_font_montserrat_48;  // fallback
}
static inline const lv_font_t *font_rpm_tick(void) {
    // return &font_roboto_bolditalic_20;
    return &lv_font_montserrat_20;
}
static inline const lv_font_t *font_strip_value(void) {
    // return &font_opensans_bold_26;
    return &lv_font_montserrat_24;
}
static inline const lv_font_t *font_strip_label(void) {
    // return &font_opensans_regular_20;
    return &lv_font_montserrat_20;
}
static inline const lv_font_t *font_strip_unit(void) {
    // return &font_opensans_regular_17;
    return &lv_font_montserrat_16;
}
static inline const lv_font_t *font_kmh(void) {
    // return &font_opensans_regular_28;
    return &lv_font_montserrat_28;
}
static inline const lv_font_t *font_gear_large(void) {
    // return &font_opensauce_bold_96;
    return &lv_font_montserrat_48;
}
static inline const lv_font_t *font_gear_label(void) {
    // return &font_opensauce_regular_25;
    return &lv_font_montserrat_24;
}
