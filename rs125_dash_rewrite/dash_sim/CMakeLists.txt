cmake_minimum_required(VERSION 3.16)

project(dash_sim C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# -----------------------------
# Paths
# -----------------------------
set(ROOT_DIR ${CMAKE_CURRENT_LIST_DIR}/..)
set(COMMON_DIR ${ROOT_DIR}/common)
set(LVGL_DIR ${ROOT_DIR}/lvgl)

# -----------------------------
# Source files
# -----------------------------
file(GLOB_RECURSE DASH_SIM_SRC
    ${CMAKE_CURRENT_LIST_DIR}/*.c
)

file(GLOB_RECURSE COMMON_SRC
    ${COMMON_DIR}/*.c
)

file(GLOB_RECURSE LVGL_SRC
    ${LVGL_DIR}/src/*.c
)

# -----------------------------
# Executable
# -----------------------------
add_executable(dash_sim
    ${DASH_SIM_SRC}
    ${COMMON_SRC}
    ${LVGL_SRC}
)

# -----------------------------
# Include directories
# -----------------------------
target_include_directories(dash_sim PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
    ${COMMON_DIR}
    ${COMMON_DIR}/assets/fonts
    ${LVGL_DIR}
    ${LVGL_DIR}/src
)

# -----------------------------
# SDL2 (vcpkg)
# -----------------------------
find_package(SDL2 CONFIG REQUIRED)

target_link_libraries(dash_sim PRIVATE SDL2::SDL2 SDL2::SDL2main)

# -----------------------------
# LVGL config FIX (IMPORTANT)
# -----------------------------
target_compile_definitions(dash_sim PRIVATE
    LV_CONF_INCLUDE_SIMPLE=1
)

# Force LVGL to find lv_conf.h in project root or common/
target_include_directories(dash_sim PRIVATE
    ${ROOT_DIR}
    ${COMMON_DIR}
)