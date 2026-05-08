// lcd_init.c
// Initialises the 16-bit Intel-8080 parallel LCD panel connected to U4.
// Supports ILI9488 and ST7796 — both use the same i80 interface and
// very similar init sequences.  The correct one is selected by the
// LCD_CONTROLLER_ILI9488 / LCD_CONTROLLER_ST7796 build flag, or you
// can probe at runtime by reading the display ID register (0x04).
//
// References:
//   ESP-IDF esp_lcd programming guide
//   ILI9488 datasheet rev 1.12
//   ST7796S datasheet rev 1.1

#include "lcd_init.h"
#include "board_pins.h"

#include "esp_log.h"
#include "esp_heap_caps.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_commands.h"   // LCD_CMD_* constants
#include "esp_lvgl_port.h"

static const char *TAG = "lcd_init";

// ── ILI9488 init sequence ─────────────────────────────────────────────────────
// Each entry: {cmd, {data bytes...}, data_len}
// data_len = 0xff means delay_ms(data[0])
typedef struct {
    uint8_t  cmd;
    uint8_t  data[16];
    uint8_t  len;   // 0xff = delay in ms
} lcd_init_cmd_t;

static const lcd_init_cmd_t ili9488_init_cmds[] = {
    // Positive / Negative gamma correction
    {0xE0, {0x00,0x07,0x0F,0x0D,0x1B,0x0A,0x3C,0x78,0x4A,0x07,0x0E,0x09,0x1B,0x1E,0x0F}, 15},
    {0xE1, {0x00,0x22,0x24,0x06,0x12,0x07,0x36,0x47,0x47,0x06,0x0A,0x07,0x30,0x37,0x0F}, 15},
    // Power control 1
    {0xC0, {0x10,0x10}, 2},
    // Power control 2
    {0xC1, {0x41}, 1},
    // VCOM control
    {0xC5, {0x00,0x22,0x80}, 3},
    // Memory access control — MY=0 MX=1 MV=1 ML=0 BGR=1 → landscape 800×480
    {0x36, {0x28}, 1},
    // Pixel format: 16-bit (RGB565) on 16-bit bus = 0x55
    {0x3A, {0x55}, 1},
    // Interface mode control
    {0xB0, {0x00}, 1},
    // Frame rate: 60 Hz
    {0xB1, {0xB0}, 1},
    // Display inversion control — 2-dot inversion
    {0xB4, {0x02}, 1},
    // Display function control
    {0xB6, {0x02,0x02,0x3B}, 3},
    // Entry mode
    {0xB7, {0xC6}, 1},
    // HS lanes
    {0xBE, {0x00,0x04}, 2},
    // Set image function
    {0xE9, {0x00}, 1},
    // Sleep out
    {0x11, {0}, 0},
    {0x00, {120}, 0xff},   // delay 120 ms
    // Display on
    {0x29, {0}, 0},
    {0x00, {20}, 0xff},    // delay 20 ms
};

// ── ST7796 init sequence (alternative controller) ─────────────────────────────
static const lcd_init_cmd_t st7796_init_cmds[] = {
    {0x11, {0}, 0},
    {0x00, {120}, 0xff},
    // Command set enable
    {0xF0, {0xC3}, 1},
    {0xF0, {0x96}, 1},
    // Memory access  — landscape BGR
    {0x36, {0x28}, 1},
    // Pixel format 16-bit
    {0x3A, {0x55}, 1},
    // Blank porch
    {0xB4, {0x01}, 1},
    // Display function
    {0xB6, {0x80,0x02,0x3B}, 3},
    // Frame rate
    {0xE8, {0x40,0x8A,0x00,0x00,0x29,0x19,0xA5,0x33}, 8},
    // Power control
    {0xC1, {0x06}, 1},
    {0xC2, {0xA7}, 1},
    {0xC5, {0x18}, 1},
    {0x00, {120}, 0xff},
    // Gamma positive
    {0xE0, {0xF0,0x09,0x0B,0x06,0x04,0x15,0x2F,0x54,0x42,0x3C,0x17,0x14,0x18,0x1B}, 14},
    // Gamma negative
    {0xE1, {0xE0,0x09,0x0B,0x06,0x04,0x03,0x2B,0x43,0x42,0x3B,0x16,0x14,0x17,0x1B}, 14},
    {0x00, {120}, 0xff},
    // Command set disable
    {0xF0, {0x3C}, 1},
    {0xF0, {0x69}, 1},
    {0x00, {120}, 0xff},
    {0x29, {0}, 0},
};

// ── Backlight PWM ─────────────────────────────────────────────────────────────
static void backlight_init(void)
{
    ledc_timer_config_t timer = {
        .speed_mode      = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_10_BIT,   // 0-1023
        .timer_num       = LEDC_TIMER_0,
        .freq_hz         = 20000,               // 20 kHz — above audible range
        .clk_cfg         = LEDC_AUTO_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer));

    ledc_channel_config_t ch = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel    = LEDC_CHANNEL_0,
        .timer_sel  = LEDC_TIMER_0,
        .intr_type  = LEDC_INTR_DISABLE,
        .gpio_num   = TFT_PIN_BL,
        .duty       = 1023,   // 100% at startup
        .hpoint     = 0,
    };
    ESP_ERROR_CHECK(ledc_channel_config(&ch));
    ESP_LOGI(TAG, "Backlight PWM on GPIO %d", TFT_PIN_BL);
}

void lcd_set_backlight(uint8_t percent)
{
    uint32_t duty = (1023u * percent) / 100u;
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, duty);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}

// ── Send init commands to panel ───────────────────────────────────────────────
static void send_init_cmds(esp_lcd_panel_io_handle_t io,
                           const lcd_init_cmd_t *cmds, size_t n)
{
    for (size_t i = 0; i < n; i++) {
        if (cmds[i].len == 0xff) {
            // Delay
            vTaskDelay(pdMS_TO_TICKS(cmds[i].data[0]));
        } else if (cmds[i].len == 0) {
            // Command with no data
            esp_lcd_panel_io_tx_param(io, cmds[i].cmd, NULL, 0);
        } else {
            esp_lcd_panel_io_tx_param(io, cmds[i].cmd,
                                      cmds[i].data, cmds[i].len);
        }
    }
}

// ── LVGL flush callback ───────────────────────────────────────────────────────
// (handled by esp_lvgl_port — we just need to pass the panel handle)

// ── Main init function ────────────────────────────────────────────────────────
esp_err_t lcd_init(esp_lcd_panel_handle_t *panel_out,
                   lv_disp_t             **disp_out)
{
    ESP_LOGI(TAG, "Initialising 16-bit i80 parallel LCD");

    // ── 1. Backlight ─────────────────────────────────────────
    backlight_init();

    // ── 2. Reset panel ───────────────────────────────────────
    gpio_config_t rst_cfg = {
        .pin_bit_mask = (1ULL << TFT_PIN_RST),
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    gpio_config(&rst_cfg);
    gpio_set_level(TFT_PIN_RST, 0);
    vTaskDelay(pdMS_TO_TICKS(10));
    gpio_set_level(TFT_PIN_RST, 1);
    vTaskDelay(pdMS_TO_TICKS(120));

    // ── 3. Create i80 bus ─────────────────────────────────────
    esp_lcd_i80_bus_handle_t i80_bus;
    esp_lcd_i80_bus_config_t bus_cfg = {
        .dc_gpio_num       = TFT_PIN_DC,
        .wr_gpio_num       = TFT_PIN_WR,
        .clk_src           = LCD_CLK_SRC_DEFAULT,
        .data_gpio_nums    = {
            TFT_PIN_D0,  TFT_PIN_D1,  TFT_PIN_D2,  TFT_PIN_D3,
            TFT_PIN_D4,  TFT_PIN_D5,  TFT_PIN_D6,  TFT_PIN_D7,
            TFT_PIN_D8,  TFT_PIN_D9,  TFT_PIN_D10, TFT_PIN_D11,
            TFT_PIN_D12, TFT_PIN_D13, TFT_PIN_D14, TFT_PIN_D15,
        },
        .bus_width         = LCD_BIT_WIDTH,
        .max_transfer_bytes = LCD_H_RES * 40 * sizeof(uint16_t), // ~40 lines/DMA
        .psram_trans_align  = 64,
        .sram_trans_align   = 4,
    };
    ESP_ERROR_CHECK(esp_lcd_new_i80_bus(&bus_cfg, &i80_bus));

    // ── 4. Create panel IO ────────────────────────────────────
    esp_lcd_panel_io_handle_t panel_io;
    esp_lcd_panel_io_i80_config_t io_cfg = {
        .cs_gpio_num         = TFT_PIN_CS,
        .pclk_hz             = LCD_PCLK_HZ,
        .trans_queue_depth   = 10,
        .on_color_trans_done = NULL,  // esp_lvgl_port sets this internally
        .user_ctx            = NULL,
        .lcd_cmd_bits        = 8,
        .lcd_param_bits      = 8,
        .dc_levels = {
            .dc_idle_level   = 0,
            .dc_cmd_level    = 0,
            .dc_dummy_level  = 0,
            .dc_data_level   = 1,
        },
        .flags = {
            .swap_color_bytes = 1,  // RGB565 byte-swap for display endianness
        },
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_i80(i80_bus, &io_cfg, &panel_io));

    // ── 5. Create panel (ST7796 init; swap for ILI9488 if needed) ──
    esp_lcd_panel_handle_t panel;
    esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = -1,    // reset already handled manually above
        .color_space    = ESP_LCD_COLOR_SPACE_BGR,
        .bits_per_pixel = 16,
    };
    // Use generic vendor init — we send our own init sequence below
    ESP_ERROR_CHECK(esp_lcd_new_panel_st7796(panel_io, &panel_cfg, &panel));

    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel));

    // Send extended init commands (gamma, power, etc.)
    // Comment out one block depending on your controller:
    send_init_cmds(panel_io, st7796_init_cmds,
                   sizeof(st7796_init_cmds) / sizeof(st7796_init_cmds[0]));
    // send_init_cmds(panel_io, ili9488_init_cmds,
    //                sizeof(ili9488_init_cmds) / sizeof(ili9488_init_cmds[0]));

    ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(panel, true));

    ESP_LOGI(TAG, "Panel initialised — %d × %d", LCD_H_RES, LCD_V_RES);
    *panel_out = panel;

    // ── 6. Initialise LVGL via esp_lvgl_port ─────────────────
    lvgl_port_cfg_t lvgl_cfg = ESP_LVGL_PORT_INIT_CONFIG();
    lvgl_cfg.task_priority   = 4;
    lvgl_cfg.task_stack      = 8192;
    lvgl_cfg.timer_period_ms = 5;   // ~200 Hz LVGL tick
    ESP_ERROR_CHECK(lvgl_port_init(&lvgl_cfg));

    // Allocate framebuffer in PSRAM (full-frame double buffer)
    lvgl_port_display_cfg_t disp_cfg = {
        .io_handle     = panel_io,
        .panel_handle  = panel,
        .buffer_size   = LCD_DRAW_BUFF_SIZE,
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
            .buff_dma    = false,  // use PSRAM, not internal DMA SRAM
            .buff_spiram = true,
            .sw_rotate   = false,
        },
    };
    lv_disp_t *disp = lvgl_port_add_disp(&disp_cfg);
    if (!disp) {
        ESP_LOGE(TAG, "Failed to add LVGL display");
        return ESP_FAIL;
    }
    *disp_out = disp;

    ESP_LOGI(TAG, "LVGL display registered");
    return ESP_OK;
}
