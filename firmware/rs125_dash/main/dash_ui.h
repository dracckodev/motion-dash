#pragma once
#include "lvgl.h"

// Create all LVGL widgets.  Call once after lcd_init().
void dash_ui_init(lv_disp_t *disp);

// Refresh all widget values from g_dash.  Call from LVGL task context
// (inside lvgl_port_lock / lvgl_port_unlock).
void dash_ui_update(void);
