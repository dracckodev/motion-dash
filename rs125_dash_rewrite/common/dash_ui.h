#pragma once
#include "lvgl.h"
#include "dash_state.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Call once after lv_init() + display init */
void dash_ui_init(void);

/* Call every frame (~16 ms) with current state */
void dash_ui_update(const dash_state_t *s);

/* Rebuild hex grid canvas (call when theme changes) */
void dash_ui_rebuild_hex(const dash_state_t *s);

/* Apply theme palette to all cached lv_color values */
void dash_ui_apply_theme(int theme_idx);

#ifdef __cplusplus
}
#endif
