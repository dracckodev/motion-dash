#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

// ── Dashboard live data ───────────────────────────────────────────────────────
// All values are written by the data-acquisition task and read by the UI task.
// Access is protected by dash_state_mutex.
typedef struct {
    uint16_t rpm;       // 0 … 12000
    uint8_t  speed;     // 0 … 200  km/h
    int8_t   gear;      // -1 = N,  1-6 = gear number
    int16_t  temp;      // °C  × 1  (integer)
    uint16_t volt_mv;   // millivolts, e.g. 12400 = 12.4 V
    uint32_t odo_m;     // odometer in metres (divide by 1000 for km)
    uint16_t range_km;  // estimated range km
    uint8_t  eco;       // L/100 km × 1
    uint8_t  fuel_pct;  // 0-100
    uint8_t  brightness;// 0-100 (backlight %)
    uint8_t  theme_idx; // 0 … N_THEMES-1
    bool     demo_mode; // true = run built-in demo sequence
} dash_state_t;

extern dash_state_t   g_dash;
extern SemaphoreHandle_t g_dash_mutex;

static inline void dash_lock(void)   { xSemaphoreTake(g_dash_mutex, portMAX_DELAY); }
static inline void dash_unlock(void) { xSemaphoreGive(g_dash_mutex); }
