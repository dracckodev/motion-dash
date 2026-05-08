/*
 * dash_sim — Windows/Linux desktop simulator using LVGL SDL backend.
 * Reproduces the full demo sequence from sim.py DemoPlayer.
 */

#include "lvgl.h"
#include "dash_ui.h"
#include "dash_state.h"
#include "dash_platform.h"

#define SDL_MAIN_HANDLED
#include <SDL2/SDL.h>

#include <math.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#define W 800
#define H 480
#define FPS 60
#define RPM_SMOOTHNESS   10.0f
#define SPEED_SMOOTHNESS  8.0f
#define MAX_RPM         12000.0f
#define REDLINE_RPM      9500.0f
#define DEMO_IDLE_RPM    1800.0f
#define DEMO_SHIFT_RPM   3500.0f

uint32_t platform_millis(void) { return (uint32_t)SDL_GetTicks(); }
void platform_lock(void) {}
void platform_unlock(void) {}
void platform_disp_init(void) {}

typedef struct {
    int   active;
    int   phase;
    float t;
    int   gear_idx;
    float rpm_at_shift;
    float spd_at_shift;
} demo_t;

static const char* GEARS[] = { "N","1","2","3","4","5","6" };
static const float DEMO_GEAR_RPMS[7] = { 0,10500,10500,10500,10500,10500,10200 };
static const float SPD_STARTS[7] = { 0,0,30,50,70,88,102 };
static const float SPD_ENDS[7] = { 0,30,50,70,88,102,110 };

static float lerp(float a, float b, float t) {
    if (t < 0) t = 0;
    if (t > 1) t = 1;
    return a + (b - a) * t;
}

static void demo_start(demo_t* d) {
    d->active = 1;
    d->phase = 0;
    d->t = 0;
    d->gear_idx = 0;
    d->rpm_at_shift = 2200;
    d->spd_at_shift = 0;

    strncpy(g_state.gear, "N", 4);
    g_state.rpm = DEMO_IDLE_RPM;
    g_state.speed = 0;
    g_state.temp = 14;
    g_state.volt = 13.8f;
    g_state.odo = 1234.56;
    g_state.range = 120;
    g_state.eco = 0;
    g_state.fuel = 1.0f;
}

static void demo_next(demo_t* d) {
    d->phase++;
    d->t = 0;
    d->rpm_at_shift = g_state.rpm;
    d->spd_at_shift = g_state.speed;
}

static void demo_update(demo_t* d, float dt) {
    if (!d->active) return;
    d->t += dt;
    int p = d->phase;

    if (p == 0) {
        g_state.rpm = (int)lerp(DEMO_IDLE_RPM, 2200, d->t / 2.0f);
        if (d->t >= 2.0f) demo_next(d);

    }
    else if (p == 1) {
        if (d->t < 0.3f) {
            g_state.throttle = lerp(0, 0.6f, d->t / 0.3f);
            g_state.rpm = lerp(2200, 7000, d->t / 0.3f);
        }
        else {
            g_state.throttle = lerp(0.6f, 0.3f, (d->t - 0.3f) / 0.5f);
            g_state.rpm = lerp(7000, 4200, (d->t - 0.3f) / 0.5f);
        }
        if (d->t >= 0.8f) {
            d->gear_idx = 1;
            strncpy(g_state.gear, "1", 4);
            demo_next(d);
        }
    }
}

int main(int argc, char* argv[]) {
    (void)argc; (void)argv;

    SDL_SetMainReady();

    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        printf("SDL_Init failed: %s\n", SDL_GetError());
        return -1;
    }

    lv_init();

    lv_display_t* disp = lv_sdl_window_create(800, 480);
    if (!disp) {
        printf("lv_sdl_window_create failed\n");
        return -1;
    }

    lv_display_set_default(disp);

    dash_ui_init();

    demo_t demo = { 0 };
    demo_start(&demo);
    dash_ui_rebuild_hex(&g_state);

    float disp_rpm = 0;
    float disp_speed = 0;
    float blink_t = 0;

    uint32_t last_ms = SDL_GetTicks();
    int running = 1;

    while (running) {
        uint32_t now = SDL_GetTicks();
        float dt = (now - last_ms) / 1000.0f;
        if (dt <= 0) dt = 0.001f;
        last_ms = now;

        SDL_Event ev;
        while (SDL_PollEvent(&ev)) {
            if (ev.type == SDL_QUIT) running = 0;
        }

        time_t now_t = time(NULL);
        struct tm* tm_i = localtime(&now_t);
        snprintf(g_state.time_str, sizeof(g_state.time_str),
            "%02d:%02d", tm_i->tm_hour, tm_i->tm_min);

        if (!demo.active) demo_start(&demo);
        demo_update(&demo, dt);

        float ar = 1.0f - expf(-RPM_SMOOTHNESS * dt);
        float as = 1.0f - expf(-SPEED_SMOOTHNESS * dt);

        disp_rpm += (g_state.rpm - disp_rpm) * ar;
        disp_speed += (g_state.speed - disp_speed) * as;

        g_state.disp_rpm = disp_rpm;
        g_state.disp_speed = disp_speed;

        blink_t += dt;
        g_state.blink_on = (disp_rpm >= REDLINE_RPM) && (((int)(blink_t * 6)) % 2 == 0);

        dash_ui_update(&g_state);

        lv_tick_inc((uint32_t)(dt * 1000));
        lv_timer_handler();

        uint32_t elapsed = SDL_GetTicks() - now;
        if (elapsed < 16) SDL_Delay(16 - elapsed);
    }

    SDL_Quit();
    return 0;
}