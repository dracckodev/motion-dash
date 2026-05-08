#include "lcd_init.h"

#include "esp_lcd_panel_ops.h"
#include "esp_lcd_qemu_rgb.h"
#include "esp_lvgl_port.h"
#include "esp_log.h"

static const char* TAG = "lcd_qemu";

esp_err_t lcd_init(esp_lcd_panel_handle_t* panel_out, lv_disp_t** disp_out)
{
    esp_lcd_panel_handle_t panel;

    esp_lcd_qemu_rgb_panel_config_t cfg = {
        .panel_config = {
            .reset_gpio_num = -1,
            .color_space = ESP_LCD_COLOR_SPACE_RGB,
            .bits_per_pixel = 16,
        },
        .hres = LCD_H_RES,
        .vres = LCD_V_RES,
    };

    ESP_ERROR_CHECK(
        esp_lcd_new_panel_qemu_rgb(&cfg, &panel)
    );

    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(panel, true));

    *panel_out = panel;

    lvgl_port_cfg_t lvgl_cfg = ESP_LVGL_PORT_INIT_CONFIG();

    ESP_ERROR_CHECK(
        lvgl_port_init(&lvgl_cfg)
    );

    lvgl_port_display_cfg_t disp_cfg = {
        .panel_handle = panel,
        .buffer_size = LCD_H_RES * LCD_V_RES,
        .double_buffer = true,
        .hres = LCD_H_RES,
        .vres = LCD_V_RES,
    };

    lv_disp_t* disp = lvgl_port_add_disp(&disp_cfg);

    if (!disp) {
        return ESP_FAIL;
    }

    *disp_out = disp;

    ESP_LOGI(TAG, "QEMU display initialized");

    return ESP_OK;
}