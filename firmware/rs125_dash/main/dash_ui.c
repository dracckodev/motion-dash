// dash_ui.c
// LVGL implementation of the RS125 TFT dashboard.
// Layout matches the pygame version exactly:
//   • Large RPM arc band (canvas-drawn)
//   • Speed numeral + km/h
//   • Gear circle + GEAR label + character
//   • Fuel gauge arc
//   • Data strip (ODO / TEMP / VOLT / RANGE / ECO / TIME)
//   • MENU button
//   • Hexagon background pattern
//
// Rendering approach:
//   LVGL canvas objects are used for the arc bands and hex grid
//   (just as pygame used direct pixel drawing).  LVGL label/arc
//   widgets handle text and simple geometry.

#include "dash_ui.h"
#include "dash_state.h"
#include "fonts_config.h"
#include "board_pins.h"
#include "lcd_init.h"

#include "lvgl.h"
#include "esp_log.h"
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

static const char *TAG = "dash_ui";

// ── Colour palette (Dark Red theme — matches Python default) ─────────────────
#define C_BG        lv_color_make(8,   0,   0)
#define C_RED       lv_color_make(255, 49,  49)
#define C_RED_MED   lv_color_make(173, 31,  31)
#define C_RED_DIM   lv_color_make(84,  15,  15)
#define C_RED_DARK  lv_color_make(20,   3,   3)
#define C_WHITE     lv_color_make(255, 255, 255)
#define C_GREY      lv_color_make(150, 150, 150)

// ── Screen dimensions ─────────────────────────────────────────────────────────
#define W  800
#define H  480

// ── Arc geometry (mirrors Python constants exactly) ───────────────────────────
#define ARC_CX_O  788.9f
#define ARC_CY_O  1545.1f
#define ARC_R_UPPER 1483.4f
#define ARC_CX_I  799.4f
#define ARC_CY_I  1609.4f
#define ARC_R_LOWER 1495.2f
#define ARC_A_START (-122.2284f)
#define ARC_A_END   (-89.5713f)
#define MAX_RPM  12000.0f

// ── Data strip row positions ──────────────────────────────────────────────────
#define ROW1_Y  346
#define ROW2_Y  406
#define STRIP_L 216
#define VCOL_A  454
#define VCOL_B  630
#define VCOL_C  381
#define VCOL_D  575

// ── Widget handles ────────────────────────────────────────────────────────────
static lv_obj_t *scr;
static lv_obj_t *canvas_bg;     // hexagon grid (redrawn on theme change)
static lv_obj_t *canvas_rpm;    // RPM arc band
static lv_obj_t *canvas_fuel;   // fuel gauge arc
static lv_obj_t *lbl_speed;
static lv_obj_t *lbl_kmh;
static lv_obj_t *lbl_gear_val;
static lv_obj_t *lbl_gear_lbl;
static lv_obj_t *lbl_odo_val, *lbl_odo_lbl;
static lv_obj_t *lbl_temp_val;
static lv_obj_t *lbl_volt_val;
static lv_obj_t *lbl_range_val;
static lv_obj_t *lbl_eco_val;
static lv_obj_t *lbl_time;
static lv_obj_t *btn_menu;
static lv_obj_t *lbl_rpm[5];    // 2k 4k 6k 8k 10k tick labels

// Canvas pixel buffers (PSRAM-allocated)
static lv_color_t *rpm_buf  = NULL;
static lv_color_t *fuel_buf = NULL;
static lv_color_t *bg_buf   = NULL;

// ── Math helpers ──────────────────────────────────────────────────────────────
static inline float rpm_angle(float rpm)
{
    float frac = rpm / MAX_RPM;
    if (frac < 0) frac = 0;
    if (frac > 1) frac = 1;
    return ARC_A_START + frac * (ARC_A_END - ARC_A_START);
}

static inline void upper_xy(float deg, float *x, float *y)
{
    float a = deg * (float)M_PI / 180.0f;
    *x = ARC_CX_O + ARC_R_UPPER * cosf(a);
    *y = ARC_CY_O + ARC_R_UPPER * sinf(a);
}

static inline void lower_xy(float deg, float *x, float *y)
{
    float a = deg * (float)M_PI / 180.0f;
    *x = ARC_CX_I + ARC_R_LOWER * cosf(a);
    *y = ARC_CY_I + ARC_R_LOWER * sinf(a);
}

// Draw a filled trapezoid on the canvas using lv_canvas_draw_polygon
static void canvas_fill_quad(lv_obj_t *canvas,
                              float x0, float y0, float x1, float y1,
                              float x2, float y2, float x3, float y3,
                              lv_color_t col)
{
    lv_draw_rect_dsc_t dsc;
    lv_draw_rect_dsc_init(&dsc);
    // LVGL canvas polygon:
    lv_point_t pts[4] = {
        {(lv_coord_t)x0, (lv_coord_t)y0},
        {(lv_coord_t)x1, (lv_coord_t)y1},
        {(lv_coord_t)x2, (lv_coord_t)y2},
        {(lv_coord_t)x3, (lv_coord_t)y3},
    };
    lv_draw_polygon_dsc_t pdsc;
    lv_draw_polygon_dsc_init(&pdsc);
    pdsc.bg_color = col;
    pdsc.bg_opa   = LV_OPA_COVER;
    lv_canvas_draw_polygon(canvas, pts, 4, &pdsc);
}

// ── Draw RPM arc band onto canvas_rpm ────────────────────────────────────────
#define ARC_STEPS 300

static void draw_rpm_arc(float disp_rpm)
{
    if (!canvas_rpm) return;

    // Clear to transparent
    lv_canvas_fill_bg(canvas_rpm, C_BG, LV_OPA_COVER);

    float target_angle = rpm_angle(disp_rpm);

    // Pre-compute upper/lower arc points
    float ux[ARC_STEPS+1], uy[ARC_STEPS+1];
    float lx[ARC_STEPS+1], ly[ARC_STEPS+1];
    for (int i = 0; i <= ARC_STEPS; i++) {
        float a = ARC_A_START + (float)i / ARC_STEPS * (ARC_A_END - ARC_A_START);
        upper_xy(a, &ux[i], &uy[i]);
        lower_xy(a, &lx[i], &ly[i]);
    }

    // Draw segments
    for (int i = 0; i < ARC_STEPS; i++) {
        float seg_angle = ARC_A_START + (float)i / ARC_STEPS * (ARC_A_END - ARC_A_START);
        bool lit = seg_angle < target_angle;
        lv_color_t col = lit ? C_RED : C_RED_DARK;
        canvas_fill_quad(canvas_rpm,
                         ux[i], uy[i], ux[i+1], uy[i+1],
                         lx[i+1], ly[i+1], lx[i], ly[i],
                         col);
    }

    // Draw upper/lower arc outlines
    lv_draw_line_dsc_t ldsc;
    lv_draw_line_dsc_init(&ldsc);
    ldsc.color = C_RED;
    ldsc.width = 3;
    for (int i = 0; i < ARC_STEPS; i++) {
        lv_point_t p1 = {(lv_coord_t)ux[i],   (lv_coord_t)uy[i]};
        lv_point_t p2 = {(lv_coord_t)ux[i+1], (lv_coord_t)uy[i+1]};
        lv_canvas_draw_line(canvas_rpm, &p1, 2, &ldsc);
        (void)p2; // suppress warning — draw_line takes array
    }

    // Major tick marks + labels at 2k, 4k, 6k, 8k, 10k
    static const int tick_rpms[] = {2000, 4000, 6000, 8000, 10000};
    static const char *tick_lbls[] = {"2", "4", "6", "8", "10"};
    float tick_label_r = ARC_R_LOWER + 18.0f;
    for (int t = 0; t < 5; t++) {
        float ta = rpm_angle((float)tick_rpms[t]);
        float rad = ta * (float)M_PI / 180.0f;
        // Update tick label positions
        if (lbl_rpm[t]) {
            float lx_f = ARC_CX_I + tick_label_r * cosf(rad);
            float ly_f = ARC_CY_I + tick_label_r * sinf(rad);
            lv_obj_set_pos(lbl_rpm[t], (lv_coord_t)(lx_f - 10), (lv_coord_t)(ly_f - 10));
            bool lit = disp_rpm > (float)(tick_rpms[t] - 600);
            lv_obj_set_style_text_color(lbl_rpm[t], lit ? C_WHITE : C_RED, 0);
            lv_label_set_text(lbl_rpm[t], tick_lbls[t]);
        }
    }
}

// ── Draw hex grid background ──────────────────────────────────────────────────
static void draw_hex_bg(void)
{
    if (!canvas_bg) return;
    lv_canvas_fill_bg(canvas_bg, C_BG, LV_OPA_COVER);

    float R  = 27.0f;
    float dx = R * 1.732f;
    float dy = R * 1.5f;

    lv_draw_polygon_dsc_t fill_dsc, out_dsc;
    lv_draw_polygon_dsc_init(&fill_dsc);
    lv_draw_polygon_dsc_init(&out_dsc);
    fill_dsc.bg_color   = C_RED_DARK;
    fill_dsc.bg_opa     = LV_OPA_50;
    out_dsc.bg_color    = C_RED_MED;
    out_dsc.bg_opa      = LV_OPA_50;
    out_dsc.border_color = C_RED_MED;
    out_dsc.border_width = 1;

    for (int row = -1; row < (int)(H / dy) + 4; row++) {
        for (int ci = -1; ci < (int)(W / dx) + 4; ci++) {
            float hx = ci * dx + ((row % 2) ? dx / 2.0f : 0.0f);
            float hy = row * dy;
            lv_point_t pts[6];
            for (int k = 0; k < 6; k++) {
                float a = (float)(60 * k - 30) * (float)M_PI / 180.0f;
                pts[k].x = (lv_coord_t)(hx + R * cosf(a));
                pts[k].y = (lv_coord_t)(hy + R * sinf(a));
            }
            lv_canvas_draw_polygon(canvas_bg, pts, 6, &fill_dsc);
            lv_canvas_draw_polygon(canvas_bg, pts, 6, &out_dsc);
        }
    }
}

// ── Draw fuel gauge ───────────────────────────────────────────────────────────
static void draw_fuel_gauge(uint8_t fuel_pct)
{
    if (!canvas_fuel) return;
    lv_canvas_fill_bg(canvas_fuel, lv_color_make(0,0,0), LV_OPA_TRANSP);

    // Simplified fuel gauge: 6-segment arc on the left side of the gear circle
    // Matching the Python draw_fuel_gauge geometry:
    //   gear circle centre = (-16, 239), R = 262
    //   fuel band from 0° to 65° (LINE_BOT_ANGLE to LINE_TOP_ANGLE)
    float fuel = fuel_pct / 100.0f;
    int   n_lit = (int)(fuel * 6 + 0.5f);
    bool  low   = fuel < 0.2f;

    float cx = -16.0f, cy = 239.0f, r_right = 262.0f - 15.0f;
    float r_inner = r_right - 35.0f;
    float a_bot = 65.0f, a_top = 0.0f;

#define FUEL_SEGS 6
    for (int i = 0; i < FUEL_SEGS; i++) {
        float flo = (float)i / FUEL_SEGS;
        float fhi = (float)(i + 1) / FUEL_SEGS;
        float a0 = a_bot + flo * (a_top - a_bot);
        float a1 = a_bot + fhi * (a_top - a_bot);
        float r0 = a0 * (float)M_PI / 180.0f;
        float r1 = a1 * (float)M_PI / 180.0f;
        float ox0 = cx + r_right * cosf(r0), oy0 = cy + r_right * sinf(r0);
        float ox1 = cx + r_right * cosf(r1), oy1 = cy + r_right * sinf(r1);
        float ix0 = cx + r_inner * cosf(r0), iy0 = cy + r_inner * sinf(r0);
        float ix1 = cx + r_inner * cosf(r1), iy1 = cy + r_inner * sinf(r1);
        bool lit  = i < n_lit;
        lv_color_t col = (low && lit) ? C_RED : (lit ? C_RED : C_RED_DARK);
        canvas_fill_quad(canvas_fuel, ox0, oy0, ox1, oy1, ix1, iy1, ix0, iy0, col);
    }
}

// ── Create strip cell (label + value + unit) ──────────────────────────────────
// Returns the label widget for the value so it can be updated later.
static lv_obj_t *make_strip_cell(lv_obj_t *parent,
                                  const char *label_text,
                                  lv_coord_t cx, lv_coord_t cy)
{
    // Label (grey, left of value)
    lv_obj_t *lbl = lv_label_create(parent);
    lv_label_set_text(lbl, label_text);
    lv_obj_set_style_text_color(lbl, C_GREY, 0);
    lv_obj_set_style_text_font(lbl, font_strip_label(), 0);
    lv_obj_set_style_text_align(lbl, LV_TEXT_ALIGN_RIGHT, 0);
    lv_obj_set_pos(lbl, cx - 90, cy - 12);

    // Value (white, right of label)
    lv_obj_t *val = lv_label_create(parent);
    lv_label_set_text(val, "--");
    lv_obj_set_style_text_color(val, C_WHITE, 0);
    lv_obj_set_style_text_font(val, font_strip_value(), 0);
    lv_obj_set_pos(val, cx, cy - 14);

    return val;
}

// ── Initialise all UI widgets ─────────────────────────────────────────────────
void dash_ui_init(lv_disp_t *disp)
{
    ESP_LOGI(TAG, "Building dashboard UI");

    scr = lv_disp_get_scr_act(disp);
    lv_obj_set_style_bg_color(scr, C_BG, 0);
    lv_obj_set_style_bg_opa(scr, LV_OPA_COVER, 0);

    // ── Allocate canvas buffers in PSRAM ─────────────────────
    size_t sz = W * H * sizeof(lv_color_t);
    bg_buf   = heap_caps_malloc(sz, MALLOC_CAP_SPIRAM);
    rpm_buf  = heap_caps_malloc(sz, MALLOC_CAP_SPIRAM);
    fuel_buf = heap_caps_malloc(sz / 4, MALLOC_CAP_SPIRAM); // fuel is small

    if (!bg_buf || !rpm_buf || !fuel_buf) {
        ESP_LOGE(TAG, "Failed to allocate canvas buffers in PSRAM");
        return;
    }

    // ── Hexagon background canvas ─────────────────────────────
    canvas_bg = lv_canvas_create(scr);
    lv_canvas_set_buffer(canvas_bg, bg_buf, W, H, LV_IMG_CF_TRUE_COLOR);
    lv_obj_set_pos(canvas_bg, 0, 0);
    draw_hex_bg();

    // ── RPM arc canvas ────────────────────────────────────────
    canvas_rpm = lv_canvas_create(scr);
    lv_canvas_set_buffer(canvas_rpm, rpm_buf, W, H, LV_IMG_CF_TRUE_COLOR_ALPHA);
    lv_obj_set_pos(canvas_rpm, 0, 0);

    // ── Fuel gauge canvas (left quarter only) ─────────────────
    canvas_fuel = lv_canvas_create(scr);
    lv_canvas_set_buffer(canvas_fuel, fuel_buf, 200, H, LV_IMG_CF_TRUE_COLOR_ALPHA);
    lv_obj_set_pos(canvas_fuel, 0, 0);

    // ── Gear circle ───────────────────────────────────────────
    // Drawn as LVGL arc widget
    lv_obj_t *gear_circle = lv_arc_create(scr);
    lv_arc_set_angles(gear_circle, 0, 360);
    lv_arc_set_bg_angles(gear_circle, 0, 360);
    lv_obj_set_size(gear_circle, 262*2, 262*2);
    lv_obj_set_pos(gear_circle, -16 - 262, 239 - 262);
    lv_obj_set_style_arc_color(gear_circle, C_RED, LV_PART_INDICATOR);
    lv_obj_set_style_arc_color(gear_circle, C_BG,  LV_PART_MAIN);
    lv_obj_set_style_arc_width(gear_circle, 3,     LV_PART_INDICATOR);
    lv_obj_set_style_arc_width(gear_circle, 3,     LV_PART_MAIN);
    lv_obj_clear_flag(gear_circle, LV_OBJ_FLAG_CLICKABLE);

    // ── "GEAR" label ──────────────────────────────────────────
    lbl_gear_lbl = lv_label_create(scr);
    lv_label_set_text(lbl_gear_lbl, "GEAR");
    lv_obj_set_style_text_font(lbl_gear_lbl, font_gear_label(), 0);
    lv_obj_set_style_text_color(lbl_gear_lbl, C_WHITE, 0);
    lv_obj_set_pos(lbl_gear_lbl, 60, 42);

    // ── Gear character ────────────────────────────────────────
    lbl_gear_val = lv_label_create(scr);
    lv_label_set_text(lbl_gear_val, "N");
    lv_obj_set_style_text_font(lbl_gear_val, font_gear_large(), 0);
    lv_obj_set_style_text_color(lbl_gear_val, C_RED, 0);
    lv_obj_set_pos(lbl_gear_val, 55, 80);

    // ── Speed numeral ─────────────────────────────────────────
    lbl_speed = lv_label_create(scr);
    lv_label_set_text(lbl_speed, "0");
    lv_obj_set_style_text_font(lbl_speed, font_speed_large(), 0);
    lv_obj_set_style_text_color(lbl_speed, C_WHITE, 0);
    lv_obj_set_style_text_align(lbl_speed, LV_TEXT_ALIGN_RIGHT, 0);
    lv_obj_set_pos(lbl_speed, 480, 150);
    lv_obj_set_width(lbl_speed, 200);

    // ── km/h label ────────────────────────────────────────────
    lbl_kmh = lv_label_create(scr);
    lv_label_set_text(lbl_kmh, "km/h");
    lv_obj_set_style_text_font(lbl_kmh, font_kmh(), 0);
    lv_obj_set_style_text_color(lbl_kmh, C_GREY, 0);
    lv_obj_set_pos(lbl_kmh, 685, 256);

    // ── RPM tick labels ───────────────────────────────────────
    for (int i = 0; i < 5; i++) {
        lbl_rpm[i] = lv_label_create(scr);
        lv_obj_set_style_text_font(lbl_rpm[i], font_rpm_tick(), 0);
        lv_obj_set_style_text_color(lbl_rpm[i], C_RED, 0);
        lv_label_set_text(lbl_rpm[i], "");
    }

    // ── Data strip separator lines ────────────────────────────
    // Drawn as thin LVGL line objects
    static const lv_point_t strip_lines[][2] = {
        {{STRIP_L, ROW1_Y}, {W, ROW1_Y}},
        {{0,       ROW2_Y}, {W, ROW2_Y}},
        {{VCOL_A,  ROW1_Y}, {VCOL_A, ROW2_Y}},
        {{VCOL_B,  ROW1_Y}, {VCOL_B, ROW2_Y}},
        {{VCOL_C,  ROW2_Y}, {VCOL_C, H}},
        {{VCOL_D,  ROW2_Y}, {VCOL_D, H}},
    };
    for (int i = 0; i < 6; i++) {
        lv_obj_t *line = lv_line_create(scr);
        lv_line_set_points(line, strip_lines[i], 2);
        lv_obj_set_style_line_color(line, C_RED, 0);
        lv_obj_set_style_line_width(line, 3, 0);
    }

    // ── Strip cells ───────────────────────────────────────────
    lv_coord_t cy1 = (ROW1_Y + ROW2_Y) / 2;
    lv_coord_t cy2 = (ROW2_Y + H)      / 2;
    lv_coord_t cx_odo   = (STRIP_L + VCOL_A) / 2;
    lv_coord_t cx_temp  = (VCOL_A  + VCOL_B) / 2;
    lv_coord_t cx_volt  = (VCOL_B  + W)      / 2;
    lv_coord_t cx_range = (STRIP_L + VCOL_C) / 2;
    lv_coord_t cx_eco   = (VCOL_C  + VCOL_D) / 2;
    lv_coord_t cx_time  = (VCOL_D  + W)      / 2;

    lbl_odo_val   = make_strip_cell(scr, "ODO",   cx_odo,   cy1);
    lbl_temp_val  = make_strip_cell(scr, "TEMP",  cx_temp,  cy1);
    lbl_volt_val  = make_strip_cell(scr, "VOLT",  cx_volt,  cy1);
    lbl_range_val = make_strip_cell(scr, "RANGE", cx_range, cy2);
    lbl_eco_val   = make_strip_cell(scr, "ECO",   cx_eco,   cy2);

    lbl_time = lv_label_create(scr);
    lv_label_set_text(lbl_time, "--:--");
    lv_obj_set_style_text_font(lbl_time, font_strip_value(), 0);
    lv_obj_set_style_text_color(lbl_time, C_WHITE, 0);
    lv_obj_align(lbl_time, LV_ALIGN_BOTTOM_MID, cx_time - W/2, -(H - cy2) + 14);

    // ── MENU button ───────────────────────────────────────────
    btn_menu = lv_btn_create(scr);
    lv_obj_set_size(btn_menu, 74, 28);
    lv_obj_set_pos(btn_menu, 30, 350);
    lv_obj_set_style_bg_color(btn_menu, C_RED_DARK, 0);
    lv_obj_set_style_bg_color(btn_menu, C_RED_MED,  LV_STATE_PRESSED);
    lv_obj_set_style_border_color(btn_menu, C_RED_MED, 0);
    lv_obj_set_style_border_width(btn_menu, 1, 0);
    lv_obj_set_style_radius(btn_menu, 4, 0);
    lv_obj_t *lbl_menu = lv_label_create(btn_menu);
    lv_label_set_text(lbl_menu, "MENU");
    lv_obj_set_style_text_font(lbl_menu, font_strip_label(), 0);
    lv_obj_set_style_text_color(lbl_menu, C_WHITE, 0);
    lv_obj_center(lbl_menu);

    // Initial render
    draw_rpm_arc(0.0f);
    draw_fuel_gauge(100);

    ESP_LOGI(TAG, "Dashboard UI ready");
}

// ── Update all widgets from g_dash ───────────────────────────────────────────
void dash_ui_update(void)
{
    dash_lock();
    uint16_t rpm     = g_dash.rpm;
    uint8_t  speed   = g_dash.speed;
    int8_t   gear    = g_dash.gear;
    int16_t  temp    = g_dash.temp;
    uint16_t volt_mv = g_dash.volt_mv;
    uint32_t odo_m   = g_dash.odo_m;
    uint16_t range   = g_dash.range_km;
    uint8_t  eco     = g_dash.eco;
    uint8_t  fuel    = g_dash.fuel_pct;
    dash_unlock();

    // Speed
    char buf[32];
    snprintf(buf, sizeof(buf), "%d", speed);
    lv_label_set_text(lbl_speed, buf);

    // Gear
    if (gear < 0) {
        lv_label_set_text(lbl_gear_val, "N");
        lv_obj_set_style_text_color(lbl_gear_val, C_RED, 0);
    } else {
        snprintf(buf, sizeof(buf), "%d", gear);
        lv_label_set_text(lbl_gear_val, buf);
        lv_obj_set_style_text_color(lbl_gear_val, C_WHITE, 0);
    }

    // ODO
    snprintf(buf, sizeof(buf), "%.2f km", odo_m / 1000.0f);
    lv_label_set_text(lbl_odo_val, buf);

    // Temp
    snprintf(buf, sizeof(buf), "%d\xc2\xb0""C", temp);
    lv_label_set_text(lbl_temp_val, buf);

    // Volt
    snprintf(buf, sizeof(buf), "%.1fV", volt_mv / 1000.0f);
    lv_label_set_text(lbl_volt_val, buf);

    // Range
    snprintf(buf, sizeof(buf), "%d km", range);
    lv_label_set_text(lbl_range_val, buf);

    // ECO
    snprintf(buf, sizeof(buf), "%d L/100", eco);
    lv_label_set_text(lbl_eco_val, buf);

    // Time
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    snprintf(buf, sizeof(buf), "%02d:%02d", t->tm_hour, t->tm_min);
    lv_label_set_text(lbl_time, buf);

    // RPM arc (most expensive — only redraw when changed)
    static uint16_t last_rpm = 0xFFFF;
    if (abs((int)rpm - (int)last_rpm) > 50) {
        draw_rpm_arc((float)rpm);
        last_rpm = rpm;
    }

    // Fuel gauge
    static uint8_t last_fuel = 0xFF;
    if (fuel != last_fuel) {
        draw_fuel_gauge(fuel);
        last_fuel = fuel;
    }
}
