set(LCD_SRC "lcd_init.c")

if("$ENV{QEMU_BUILD}" STREQUAL "1")
    message(STATUS "Using QEMU LCD driver")
    set(LCD_SRC "lcd_qemu.c")
endif()

idf_component_register(
    SRCS
        "main.c"
        "${LCD_SRC}"
        "dash_ui.c"

    INCLUDE_DIRS
        "."

    REQUIRES
        esp_lcd
        driver
        nvs_flash
        freertos
        esp_lvgl_port
        lvgl
)

target_link_libraries(${COMPONENT_LIB} INTERFACE m)