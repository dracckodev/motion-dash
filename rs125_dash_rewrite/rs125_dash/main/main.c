#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "lvgl.h"
#include "esp_lvgl_port.h"
#include "lcd_init.h"
#include "dash_ui.h"
#include "dash_state.h"
#include <math.h>
#include <time.h>
#include <sys/time.h>
#include <string.h>
#include <stdio.h>

static const char *TAG = "main";

#define RPM_SMOOTHNESS   10.0f
#define SPEED_SMOOTHNESS  8.0f
#define REDLINE_RPM     9500.0f
#define MAX_RPM         12000.0f

static SemaphoreHandle_t state_mutex;

/* ── Platform impl ───────────────────────────────────────────────────────── */
uint32_t platform_millis(void) {
    return (uint32_t)(esp_timer_get_time() / 1000ULL);
}
void platform_lock(void)   { xSemaphoreTake(state_mutex, portMAX_DELAY); }
void platform_unlock(void) { xSemaphoreGive(state_mutex); }
void platform_disp_init(void) { lcd_init(); }

/* ── Demo player (mirrors DemoPlayer in sim.py) ───────────────────────────── */
/* For production replace this task with real OBD/CAN data reads */
static void data_task(void *arg) {
    /* Simple idle demo: ramp RPM 0→12000 and back, update clock */
    float  t   = 0;
    float  rpm = 1800;
    int    dir = 1;
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(16));
        t += 0.016f;

        rpm += dir * 150.0f;
        if (rpm > MAX_RPM) { rpm = MAX_RPM; dir = -1; }
        if (rpm < 0)       { rpm = 0;       dir =  1; }

        /* wall clock */
        struct timeval tv; gettimeofday(&tv, NULL);
        struct tm *tm_info = localtime(&tv.tv_sec);

        platform_lock();
        g_state.rpm   = rpm;
        g_state.speed = rpm / MAX_RPM * 110.0f;
        g_state.temp  = 85.0f;
        g_state.volt  = 13.8f;
        g_state.fuel  = 0.75f;
        snprintf(g_state.time_str, sizeof(g_state.time_str),
                 "%02d:%02d", tm_info->tm_hour, tm_info->tm_min);
        platform_unlock();
    }
}

/* ── UI update task ──────────────────────────────────────────────────────── */
static void ui_update_task(void *arg) {
    const float dt = 1.0f / 60.0f;
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(16));

        platform_lock();
        dash_state_t snap = g_state;
        platform_unlock();

        /* exponential smoothing */
        float ar = 1.0f - expf(-RPM_SMOOTHNESS   * dt);
        float as = 1.0f - expf(-SPEED_SMOOTHNESS * dt);
        snap.disp_rpm   += (snap.rpm   - snap.disp_rpm)   * ar;
        snap.disp_speed += (snap.speed - snap.disp_speed) * as;
        if (snap.disp_rpm < 50.0f) snap.disp_rpm = 0.0f;

        /* blink */
        snap.blink_t += dt;
        snap.blink_on = (snap.disp_rpm >= REDLINE_RPM) &&
                        (((int)(snap.blink_t * 6)) % 2 == 0);

        /* write smoothed values back */
        platform_lock();
        g_state.disp_rpm   = snap.disp_rpm;
        g_state.disp_speed = snap.disp_speed;
        g_state.blink_t    = snap.blink_t;
        g_state.blink_on   = snap.blink_on;
        platform_unlock();

        /* LVGL update under lock */
        if (lvgl_port_lock(0)) {
            dash_ui_update(&snap);
            lv_task_handler();
            lvgl_port_unlock();
        }
    }
}

void app_main(void) {
    ESP_LOGI(TAG, "RS125 Dash starting");
    state_mutex = xSemaphoreCreateMutex();

    platform_disp_init();
    lv_init();
    dash_ui_init();
    dash_ui_rebuild_hex(&g_state);

    xTaskCreatePinnedToCore(data_task,      "data",  4096, NULL, 5, NULL, 0);
    xTaskCreatePinnedToCore(ui_update_task, "ui",    8192, NULL, 4, NULL, 1);
}
