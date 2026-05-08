#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define RGB32(r,g,b) (0xFF000000u|((uint32_t)(r)<<16)|((uint32_t)(g)<<8)|(uint32_t)(b))

typedef struct {
    const char *name;
    bool        tick_contrast;
    uint32_t    BG, RED, RED_MED, RED_DIM, RED_DARK, WHITE, GREY;
} dash_theme_t;

#define THEME_COUNT 12
extern const dash_theme_t DASH_THEMES[THEME_COUNT];

typedef struct {
    /* vehicle data – written by data_task or sim */
    float   rpm;
    float   speed;
    char    gear[4];
    float   temp;
    float   volt;
    double  odo;
    int     range;
    int     eco;
    float   fuel;
    float   throttle;
    char    time_str[8];

    /* display-smoothed values – written by ui task */
    float   disp_rpm;
    float   disp_speed;

    /* ui flags */
    int     theme_idx;
    float   brightness;
    bool    rebuild_hex;
    bool    blink_on;
    float   blink_t;

    /* odo display mode: 0=ODO 1=TRIP_A 2=TRIP_B */
    int     odo_mode;
    double  trip_a;
    double  trip_b;
    bool    eco_imperial;
} dash_state_t;

extern dash_state_t g_state;

#ifdef __cplusplus
}
#endif
