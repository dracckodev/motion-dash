#include "lcd_init.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_ssd1963.h"   /* idf-component: espressif/esp_lcd_ssd1963 */
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_log.h"
#include "lvgl.h"
#include "esp_lvgl_port.h"
#include <string.h>

static const char *TAG = "lcd";

#define LCD_H_RES   800
#define LCD_V_RES   480
#define LCD_BIT_WIDTH 16   /* 8080 16-bit parallel */
#define LCD_BUF_LINES 20   /* LVGL draw buffer height in lines */

static lv_display_t      *s_disp   = NULL;
static esp_lcd_panel_handle_t s_panel = NULL;

/* Backlight PWM */
static void bl_init(void) {
    ledc_timer_config_t t = {
        .speed_mode      = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_10_BIT,
        .timer_num       = LEDC_TIMER_0,
        .freq_hz         = 5000,
        .clk_cfg         = LEDC_AUTO_CLK,
    };
    ledc_timer_config(&t);
    ledc_channel_config_t c = {
        .gpio_num   = LCD_PIN_BL,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel    = LEDC_CHANNEL_0,
        .timer_sel  = LEDC_TIMER_0,
        .duty       = 1023,   /* 100% */
        .hpoint     = 0,
    };
    ledc_channel_config(&c);
}

static bool lvgl_flush_cb(esp_lcd_panel_io_handle_t io,
                          esp_lcd_panel_io_event_data_t *edata,
                          void *user_ctx) {
    lv_display_flush_ready((lv_display_t *)user_ctx);
    return false;
}

esp_err_t lcd_init(void) {
    /* ── GPIO for RD (active-high idle) ── */
    gpio_config_t io = {
        .pin_bit_mask = 1ULL << LCD_PIN_RD,
        .mode         = GPIO_MODE_OUTPUT,
    };
    gpio_config(&io);
    gpio_set_level(LCD_PIN_RD, 1);

    /* ── 8080 bus ── */
    esp_lcd_i80_bus_handle_t bus;
    esp_lcd_i80_bus_config_t bus_cfg = {
        .dc_gpio_num       = LCD_PIN_RS,
        .wr_gpio_num       = LCD_PIN_WR,
        .clk_src           = LCD_CLK_SRC_DEFAULT,
        .data_gpio_nums    = {
            LCD_PIN_D0,  LCD_PIN_D1,  LCD_PIN_D2,  LCD_PIN_D3,
            LCD_PIN_D4,  LCD_PIN_D5,  LCD_PIN_D6,  LCD_PIN_D7,
            LCD_PIN_D8,  LCD_PIN_D9,  LCD_PIN_D10, LCD_PIN_D11,
            LCD_PIN_D12, LCD_PIN_D13, LCD_PIN_D14, LCD_PIN_D15,
        },
        .bus_width          = LCD_BIT_WIDTH,
        .max_transfer_bytes = LCD_H_RES * LCD_BUF_LINES * 2,
        .psram_trans_align  = 64,
        .sram_trans_align   = 4,
    };
    ESP_ERROR_CHECK(esp_lcd_new_i80_bus(&bus_cfg, &bus));

    /* ── Panel IO ── */
    esp_lcd_panel_io_handle_t io_handle;
    esp_lcd_panel_io_i80_config_t io_cfg = {
        .cs_gpio_num       = LCD_PIN_CS,
        .pclk_hz           = 10 * 1000 * 1000,
        .trans_queue_depth = 10,
        .on_color_trans_done = lvgl_flush_cb,
        .user_ctx          = NULL,   /* filled after lv_display_t created */
        .lcd_cmd_bits      = 16,
        .lcd_param_bits    = 16,
        .dc_levels = {
            .dc_idle_level  = 0,
            .dc_cmd_level   = 0,
            .dc_dummy_level = 0,
            .dc_data_level  = 1,
        },
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_i80(bus, &io_cfg, &io_handle));

    /* ── SSD1963 panel ── */
    esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = LCD_PIN_RST,
        .color_space    = ESP_LCD_COLOR_SPACE_RGB,
        .bits_per_pixel = 16,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_ssd1963(io_handle, &panel_cfg, &s_panel));
    ESP_ERROR_CHECK(esp_lcd_panel_reset(s_panel));
    ESP_ERROR_CHECK(esp_lcd_panel_init(s_panel));
    ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(s_panel, true));

    /* ── LVGL port ── */
    const lvgl_port_cfg_t lv_cfg = ESP_LVGL_PORT_INIT_CONFIG();
    lvgl_port_init(&lv_cfg);

    const lvgl_port_display_cfg_t disp_cfg = {
        .io_handle     = io_handle,
        .panel_handle  = s_panel,
        .buffer_size   = LCD_H_RES * LCD_BUF_LINES,
        .double_buffer = true,
        .hres          = LCD_H_RES,
        .vres          = LCD_V_RES,
        .monochrome    = false,
        .rotation = {
            .swap_xy  = false,
            .mirror_x = false,
            .mirror_y = false,
        },
        .flags = {
            .buff_dma    = true,
            .swap_bytes  = true,
        },
    };
    s_disp = lvgl_port_add_disp(&disp_cfg);

    bl_init();
    ESP_LOGI(TAG, "SSD1963 800x480 init OK");
    return ESP_OK;
}
