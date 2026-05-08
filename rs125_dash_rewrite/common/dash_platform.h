#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Implemented per-platform in esp32/sim main files */
uint32_t platform_millis(void);
void     platform_lock(void);
void     platform_unlock(void);
void     platform_disp_init(void);   /* sets up lv_display_t */

#ifdef __cplusplus
}
#endif
