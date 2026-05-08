#include "dash_state.h"

dash_state_t g_state = {
    .rpm=4500,.speed=45,.gear="N",.temp=14,.volt=12.4,
    .odo=1234.56,.range=95,.eco=95,.fuel=1.0,.throttle=0,
    .time_str="00:00",.disp_rpm=0,.disp_speed=0,
    .theme_idx=0,.brightness=1.0f,.rebuild_hex=true,
    .blink_on=false,.blink_t=0,.odo_mode=0,.trip_a=0,.trip_b=0,
    .eco_imperial=false
};

const dash_theme_t DASH_THEMES[THEME_COUNT] = {
    {"Dark Red",    false, RGB32(8,0,0),      RGB32(255,49,49),  RGB32(173,31,31),  RGB32(84,15,15),   RGB32(20,3,3),    RGB32(255,255,255), RGB32(150,150,150)},
    {"Dark Blue",   false, RGB32(0,0,10),     RGB32(49,140,255), RGB32(31,90,173),  RGB32(15,40,84),   RGB32(3,10,22),   RGB32(255,255,255), RGB32(130,150,170)},
    {"Dark Green",  true,  RGB32(0,8,0),      RGB32(49,230,90),  RGB32(31,150,60),  RGB32(15,70,25),   RGB32(3,18,6),    RGB32(255,255,255), RGB32(130,170,140)},
    {"Dark Amber",  false, RGB32(8,4,0),      RGB32(255,160,0),  RGB32(180,100,0),  RGB32(90,45,0),    RGB32(22,10,0),   RGB32(255,255,220), RGB32(170,150,100)},
    {"Dark Purple", false, RGB32(5,0,10),     RGB32(200,80,255), RGB32(130,40,180), RGB32(60,15,90),   RGB32(15,3,22),   RGB32(255,240,255), RGB32(160,130,180)},
    {"Dark Mono",   true,  RGB32(5,5,5),      RGB32(220,220,220),RGB32(140,140,140),RGB32(60,60,60),   RGB32(18,18,18),  RGB32(255,255,255), RGB32(150,150,150)},
    {"Light Red",   true,  RGB32(245,232,232),RGB32(200,20,20),  RGB32(160,60,60),  RGB32(210,170,170),RGB32(232,215,215),RGB32(30,20,20),   RGB32(110,80,80)},
    {"Light Blue",  true,  RGB32(228,238,252),RGB32(20,80,210),  RGB32(60,110,185), RGB32(170,195,232),RGB32(212,223,243),RGB32(15,25,50),   RGB32(75,100,135)},
    {"Light Green", false, RGB32(228,248,233),RGB32(20,170,55),  RGB32(50,130,75),  RGB32(170,220,180),RGB32(212,238,218),RGB32(10,35,18),   RGB32(70,120,85)},
    {"Light Amber", true,  RGB32(252,244,225),RGB32(190,110,0),  RGB32(200,150,50), RGB32(232,207,155),RGB32(244,230,200),RGB32(35,22,0),    RGB32(125,100,50)},
    {"Light Purple",true,  RGB32(240,230,252),RGB32(150,30,210), RGB32(170,80,200), RGB32(210,175,238),RGB32(232,218,248),RGB32(30,10,50),   RGB32(120,90,150)},
    {"Light Mono",  true,  RGB32(240,240,240),RGB32(40,40,40),   RGB32(100,100,100),RGB32(185,185,185),RGB32(220,220,220),RGB32(0,0,0),      RGB32(110,110,110)},
};
