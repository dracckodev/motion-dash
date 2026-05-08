// main.c — RS125 TFT Dashboard
// ESP32-S3-DevKitC-1 N8R8  +  16-bit parallel TFT (ILI9488/ST7796)
//
// Task layout:
//   main_task  (this)   — hardware init, then deletes itself
//   lvgl_task           — created by esp_lvgl_port, runs LVGL tick + flush
//   ui_update_task      — reads g_dash, calls dash_ui_update() every 16 ms
//   data_task           — populates g_dash (OBD / demo) — stub here

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "nvs_flash.h"
#include "driver/gpio.h"

#include "board_pins.h"
#include "lcd_init.h"
#include "dash_state.h"
#include "dash_ui.h"
#include "esp_lvgl_port.h"

static const char *TAG = "main";

// ── Global state ──────────────────────────────────────────────────────────────
dash_state_t     g_dash;
SemaphoreHandle_t g_dash_mutex;

// ── Demo data source — ramps RPM and speed cyclically ─────────────────────────
static void data_task(void *arg)
{
    // Simple stub: animate RPM 0→12000→0 in a 10-second loop.
    // Replace this task body with your OBD / K-Line / CAN reader.
    uint32_t t = 0;
    while (1) {
        float phase = (t % 10000) / 10000.0f;   // 0.0 … 1.0 per 10 s
        float rpm   = (phase < 0.5f)
                      ? phase * 2.0f * 12000.0f
                      : (1.0f - phase) * 2.0f * 12000.0f;

        dash_lock();
        g_dash.rpm      = (uint16_t)rpm;
        g_dash.speed    = (uint8_t)(rpm / 12000.0f * 110.0f);
        g_dash.gear     = (g_dash.rpm < 500) ? -1 :
                          (int8_t)(g_dash.rpm / 2000 + 1);
        if (g_dash.gear > 6) g_dash.gear = 6;
        g_dash.temp     = 70 + (int16_t)(rpm / 12000.0f * 15.0f);
        g_dash.volt_mv  = 12400 - (uint16_t)(rpm / 12000.0f * 400.0f);
        g_dash.odo_m   += g_dash.speed / 36;   // rough increment
        g_dash.range_km = 120;
        g_dash.eco      = 8 + (uint8_t)(rpm / 12000.0f * 8.0f);
        g_dash.fuel_pct = 80;
        dash_unlock();

        t += 16;
        vTaskDelay(pdMS_TO_TICKS(16));
    }
}

// ── UI update task — calls dash_ui_update() inside LVGL lock ─────────────────
static void ui_update_task(void *arg)
{
    while (1) {
        if (lvgl_port_lock(0)) {          // non-blocking try
            dash_ui_update();
            lvgl_port_unlock();
        }
        vTaskDelay(pdMS_TO_TICKS(16));    // ~60 Hz
    }
}

// ── Entry point ───────────────────────────────────────────────────────────────
void app_main(void)
{
    ESP_LOGI(TAG, "RS125 Dashboard starting");

    // NVS (needed by WiFi/BT even if unused; harmless to init)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
    }

    // Shared state
    g_dash_mutex = xSemaphoreCreateMutex();
    configASSERT(g_dash_mutex);

    memset(&g_dash, 0, sizeof(g_dash));
    g_dash.gear     = -1;   // neutral
    g_dash.volt_mv  = 12400;
    g_dash.fuel_pct = 100;
    g_dash.brightness = 100;

    // LCD + LVGL
    esp_lcd_panel_handle_t panel;
    lv_disp_t *disp;
    ESP_ERROR_CHECK(lcd_init(&panel, &disp));

    // Build UI
    if (lvgl_port_lock(portMAX_DELAY)) {
        dash_ui_init(disp);
        lvgl_port_unlock();
    }

    // Tasks
    xTaskCreatePinnedToCore(data_task,      "data",      4096, NULL, 5, NULL, 1);
    xTaskCreatePinnedToCore(ui_update_task, "ui_update", 4096, NULL, 4, NULL, 0);

    ESP_LOGI(TAG, "All tasks started — deleting main task");
    vTaskDelete(NULL);
}
