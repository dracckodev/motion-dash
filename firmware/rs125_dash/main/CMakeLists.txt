idf_component_register(
    SRCS
        "main.c"
        "lcd_init.c"
        "dash_ui.c"
        # Add generated font .c files here, e.g.:
        # "font_roboto_bolditalic_162.c"
        # "font_opensans_bold_26.c"
        # etc.
    INCLUDE_DIRS
        "."
    REQUIRES
        esp_lcd
        esp_timer
        driver
        nvs_flash
        freertos
        esp_lvgl_port
        lvgl
)

# Math library (needed for sinf/cosf in dash_ui.c)
target_link_libraries(${COMPONENT_LIB} INTERFACE m)
