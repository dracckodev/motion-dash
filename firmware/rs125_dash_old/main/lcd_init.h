#pragma once
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lvgl_port.h"

esp_err_t lcd_init(esp_lcd_panel_handle_t *panel_out,
                   lv_disp_t             **disp_out);
