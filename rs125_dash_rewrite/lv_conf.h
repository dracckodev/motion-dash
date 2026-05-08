#ifndef LV_CONF_H
#define LV_CONF_H

#ifndef LV_CONF_INCLUDE_SIMPLE
#define LV_CONF_INCLUDE_SIMPLE 1
#endif


/* =========================
 * BASIC SETTINGS
 * ========================= */

#define LV_COLOR_DEPTH 32
#define LV_COLOR_16_SWAP 0

#define LV_MEM_CUSTOM 0
#define LV_MEM_SIZE (48U * 1024U)

 /* Enable asserts (helps debugging linker/config issues) */
#define LV_USE_ASSERT_NULL   1
#define LV_USE_ASSERT_MALLOC 1

/* =========================
 * TICK / TIMER
 * ========================= */
#define LV_TICK_CUSTOM 0

 /* =========================
  * RENDER SETTINGS
  * ========================= */
#define LV_USE_DRAW_SW 1

  /* =========================
   * INPUT DEVICES (SDL handles this)
   * ========================= */
#define LV_USE_POINTER 1
#define LV_USE_KEYBOARD 1

   /* =========================
	* FONTS (enable basic built-in)
	* ========================= */
#define LV_FONT_MONTSERRAT_14 1
#define LV_FONT_MONTSERRAT_20 1
#define LV_FONT_MONTSERRAT_24 1
#define LV_FONT_MONTSERRAT_28 1
#define LV_FONT_MONTSERRAT_32 1
#define LV_FONT_DEFAULT &lv_font_montserrat_14

	/* =========================
	 * LOGGING (optional but useful)
	 * ========================= */
#define LV_USE_LOG 1
#define LV_LOG_LEVEL LV_LOG_LEVEL_WARN

	 /* =========================
	  * DISABLE UNWANTED DRIVERS (IMPORTANT)
	  * ========================= */

	  /* You ONLY want SDL */
#define LV_USE_SDL 1

/* Disable everything else that is leaking into your build */
#define LV_USE_WAYLAND 0
#define LV_USE_WINDOWS 0
#define LV_USE_LINUX_FBDEV 0
#define LV_USE_NUTTX 0
#define LV_USE_EVDEV 0

/* =========================
 * MISC
 * ========================= */
#define LV_USE_PERF_MONITOR 0
#define LV_USE_MEM_MONITOR 0

 /* =========================
  * INCLUDE GUARD REQUIRED BY LVGL
  * ========================= */
#endif /* LV_CONF_H */