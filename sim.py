"""
Aprilia RS125 TFT Dashboard Simulator — 800×480
All geometry, fonts and icons extracted directly from the source PDF.

Fonts required (extracted from PDF, place in same folder):
  EAAAAA_Roboto-BoldItalic.ttf       — speed number (subset: digits 0-9 needed)
  AAAAAA_OpenSauceOne-Bold.ttf       — gear character
  BAAAAA_OpenSauceOne-Regular.ttf    — GEAR label
  CAAAAA_OpenSans-Regular.ttf        — km/h, strip labels/units, tick numbers
  DAAAAA_OpenSans-Bold.ttf           — strip values

  Because the PDF subsets only contain glyphs for the literal text shown,
  we fall back to system fonts for any missing glyphs (e.g. full digit set).

Icons required (extracted from PDF, place in same folder):
  icon_temp.png    — temperature icon (RGBA, red-tinted)
  icon_batt.png    — battery icon (RGBA, red-tinted)

Controls: UP/DOWN = RPM,  W/S = Speed,  LEFT/RIGHT = Gear,
          T/Y = Temp,  B/N = Voltage,  Q/ESC = Quit
"""

import tkinter as tk
import threading
import pygame
import math
import sys
import os
from datetime import datetime

# ── Demo constants ────────────────────────────────────────────────────────────

# ── Throttle glow scaling ─────────────────────────────────────────────────────
THROTTLE_GLOW_SCALE = 0

DEMO_IDLE_RPM   = 1800
DEMO_HOT_TEMP   = 82
DEMO_BASE_TEMP  = 14
DEMO_BASE_VOLT  = 13.8
DEMO_ODO_START  = 1234.56
DEMO_SHIFT_RPM  = 3500
DEMO_TOP_SPEED  = 110
DEMO_GEAR_RPMS  = [0, 10500, 10500, 10500, 10500, 10500, 10200]

# ── Menu button geometry constants ────────────────────────────────────────────
# Angles in degrees: 0° = rightmost (3 o'clock), same convention as rpm_angle().
# The RPM arc runs from ~-122° (left) to ~-90° (top-right).
# Both pivot points lie on a circle of radius (ARC_R_LOWER + MENU_SEPARATION)
# centred at (ARC_CX_I, ARC_CY_I).

MENU_ARC_ANGLE_TOP  = -105.6   # arc angle for the top-right pivot (~6000 RPM region)
MENU_ARC_ANGLE_BOT  = -113.5   # arc angle for the bottom-left pivot (~4000 RPM region)
# NOTE: ARC_R_LOWER and ARC_R_UPPER are measured from two *different* circle
# centres (ARC_CX_I/CY_I vs ARC_CX_O/CY_O), so the band's true on-screen width
# is NOT (ARC_R_LOWER - ARC_R_UPPER) (~12px) -- that's the difference of two
# radii measured from different origins, not a real distance. The actual
# physical gap between the inner edge (lower_xy) and outer edge (upper_xy) in
# this part of the dial is ~54px. MENU_SEPARATION has to clear that full
# width, or the button nests inside the band instead of sitting above it.
MENU_SEPARATION     =  62.0    # radial gap (px) from lower arc edge to both pivots
MENU_LINE_ANGLE_TOP = -20.0    # rotation of top line: negative = CCW (outward-up)
MENU_LINE_ANGLE_BOT =  35.0    # rotation of bottom line: positive = CW
MENU_LINE_LEN_TOP   =  82.0    # length of top line (px)
MENU_LINE_LEN_BOT   =  58.0    # length of bottom line (px)
MENU_OUTER_ARC_R    = 235.0    # radius of the outer closing arc (top edge bulge)
MENU_CIRCLE_SEPARATION = 10.0   # radial gap: gear-circle arc offset outward from CIRCLE_R
MENU_CIRCLE_SWEEP      = 13.5   # degrees the circle-side edge sweeps from the join point


class DemoPlayer:
    def __init__(self):
        self.active        = False
        self.phase         = 0
        self.t             = 0.0
        self.gear_idx      = 0
        self.gears         = ["N","1","2","3","4","5","6"]
        self._rpm_at_shift = 0
        self._spd_at_shift = 0.0

    def start(self, state):
        self.active        = True
        self.phase         = 0
        self.t             = 0.0
        self.gear_idx      = 0
        self._rpm_at_shift = 2200
        self._spd_at_shift = 0.0
        state["gear"]  = "N"
        state["rpm"]   = DEMO_IDLE_RPM
        state["speed"] = 0
        state["temp"]  = DEMO_BASE_TEMP
        state["volt"]  = DEMO_BASE_VOLT
        state["odo"]   = DEMO_ODO_START
        state["range"] = 120
        state["eco"]   = 0

    def _next(self, state):
        self.phase        += 1
        self.t             = 0.0
        self._rpm_at_shift = state["rpm"]
        self._spd_at_shift = state["speed"]

    def _lerp(self, a, b, t):
        return a + (b - a) * max(0.0, min(1.0, t))

    def update(self, state, dt):
        if not self.active:
            return
        self.t += dt
        p = self.phase

        if p == 0:
            state["throttle"] = 0.0
            state["rpm"]  = int(self._lerp(DEMO_IDLE_RPM, 2200, self.t / 2.0))
            state["temp"] = self._lerp(DEMO_BASE_TEMP, DEMO_BASE_TEMP + 5, self.t / 2.0)
            if self.t >= 2.0:
                self._next(state)

        elif p == 1:
            if self.t < 0.3:
                state["throttle"] = self._lerp(0.0, 0.6, self.t / 0.3)
                state["rpm"] = int(self._lerp(2200, 7000, self.t / 0.3))
            else:
                state["throttle"] = self._lerp(0.6, 0.3, (self.t - 0.3) / 0.5)
                state["rpm"] = int(self._lerp(7000, 4200, (self.t - 0.3) / 0.5))
            if self.t >= 0.8:
                self.gear_idx = 1
                state["gear"] = "1"
                self._next(state)

        elif p in (2, 4, 6, 8, 10, 12):
            gear = p // 2
            duration  = [0, 3.5, 3.0, 3.0, 3.0, 3.0, 4.0][gear]
            rpm_start = 4200 if p == 2 else DEMO_SHIFT_RPM
            rpm_end   = DEMO_GEAR_RPMS[gear]
            spd_starts = [0, 0, 30, 50, 70, 88, 102]
            spd_ends   = [0, 30, 50, 70, 88, 102, DEMO_TOP_SPEED]
            spd_start  = spd_starts[gear]
            spd_end    = spd_ends[gear]
            frac = self.t / duration
            state["throttle"] = self._lerp(0.4, 1.0, min(1.0, self.t / 0.4))
            state["rpm"]   = int(self._lerp(rpm_start, rpm_end, frac))
            state["speed"] = self._lerp(spd_start, spd_end, frac)
            state["temp"]  = self._lerp(state["temp"], DEMO_HOT_TEMP, dt * 0.3)
            state["volt"]  = DEMO_BASE_VOLT - 0.4 * frac
            state["odo"]  += state["speed"] / 3600.0 * dt
            state["eco"]   = int(self._lerp(10, 16, frac))
            state["range"] = max(0, int(120 - (state["odo"] - DEMO_ODO_START) * 0.9))
            if self.t >= duration:
                self._next(state)

        elif p in (3, 5, 7, 9, 11):
            state["throttle"] = self._lerp(1.0, 0.0, self.t / 0.15) if self.t < 0.15 else self._lerp(0.0, 0.4, (self.t - 0.15) / 0.2)
            if self.t < 0.15:
                state["rpm"] = int(self._lerp(self._rpm_at_shift, self._rpm_at_shift * 0.5, self.t / 0.15))
            else:
                state["rpm"] = int(self._lerp(self._rpm_at_shift * 0.5, DEMO_SHIFT_RPM, (self.t - 0.15) / 0.2))
            state["speed"] = self._spd_at_shift
            state["odo"]  += state["speed"] / 3600.0 * dt
            if self.t >= 0.35:
                self.gear_idx += 1
                state["gear"]  = self.gears[self.gear_idx]
                self._next(state)

        elif p == 13:
            state["throttle"] = self._lerp(1.0, 0.35, self.t / 3.0)
            state["rpm"]   = int(self._lerp(DEMO_GEAR_RPMS[6], 9800, self.t / 3.0))
            state["speed"] = self._lerp(DEMO_TOP_SPEED, DEMO_TOP_SPEED - 2, self.t / 3.0)
            state["temp"]  = self._lerp(state["temp"], DEMO_HOT_TEMP + 3, dt * 0.1)
            state["volt"]  = DEMO_BASE_VOLT - 0.2
            state["odo"]  += state["speed"] / 3600.0 * dt
            state["eco"]   = 9
            state["range"] = max(0, int(120 - (state["odo"] - DEMO_ODO_START) * 0.9))
            if self.t >= 3.0:
                self._next(state)

        elif p == 14:
            duration = 12.0
            frac     = self.t / duration
            state["throttle"] = self._lerp(0.35, 0.0, min(1.0, self.t / 0.5))
            state["speed"] = self._lerp(DEMO_TOP_SPEED - 2, 0, frac)
            state["rpm"]   = int(self._lerp(9800, DEMO_IDLE_RPM, frac ** 0.6))
            expected_gear  = max(1, 6 - int(frac * 6))
            if expected_gear != self.gear_idx:
                self.gear_idx  = expected_gear
                state["gear"]  = self.gears[self.gear_idx]
            state["temp"]  = self._lerp(state["temp"], DEMO_HOT_TEMP - 5, dt * 0.05)
            state["volt"]  = self._lerp(DEMO_BASE_VOLT - 0.2, DEMO_BASE_VOLT, frac)
            state["odo"]  += state["speed"] / 3600.0 * dt
            state["eco"]   = int(self._lerp(9, 2, frac))
            state["range"] = max(0, int(120 - (state["odo"] - DEMO_ODO_START) * 0.9))
            if self.t >= duration:
                self._next(state)

        elif p == 15:
            state["throttle"] = 0.0
            state["speed"] = 0
            state["rpm"]   = int(self._lerp(DEMO_IDLE_RPM + 200, DEMO_IDLE_RPM, self.t / 2.0))
            state["gear"]  = "N"
            self.gear_idx  = 0
            state["eco"]   = 0
            if self.t >= 2.0:
                self.active = False

# ── Screen ────────────────────────────────────────────────────────────────────
W, H  = 800, 480
FPS   = 60
SCALE = W / 600.0

TICK_LABEL_GLOBAL_OFFSET = (10, -28)
TICK_LABEL_OVERRIDES = {
    2000: (0, 0),
    4000: (0, 0),
    6000: (-4, 3.5),
    8000: (-4, 3.5),
    10000: (-4, 3.5),
}

MAX_RPM = 12000
REDLINE_RPM = 9500

GLOW_BLEED_PX    = 60
GLOW_BLEED_ALPHA = 110

RPM_SMOOTHNESS   = 10.0
SPEED_SMOOTHNESS =  8.0

TICK_LIGHT_WIDTH_RPM = 600

def _tick_lit_colour():
    if not TICK_CONTRAST:
        return WHITE
    return tuple(255 - c for c in WHITE)

# ── Colours ───────────────────────────────────────────────────────────────────
BG        = (8,   0,   0)
RED       = (255,  49,  49)
RED_MED   = (173,  31,  31)
RED_DIM   = (84,   15,  15)
RED_DARK  = (20,    3,   3)
RED_INNER = (52,    8,   8)
WHITE     = (255, 255, 255)
GREY      = (150, 150, 150)

THEMES = [
    {
        "name":          "Dark Red",
        "tick_contrast": False,
        "BG":        (8,   0,   0),
        "RED":       (255,  49,  49),
        "RED_MED":   (173,  31,  31),
        "RED_DIM":   (84,   15,  15),
        "RED_DARK":  (20,    3,   3),
        "WHITE":     (255, 255, 255),
        "GREY":      (150, 150, 150),
    },
    {
        "name":          "Dark Blue",
        "tick_contrast": False,
        "BG":        (0,   0,   10),
        "RED":       (49, 140, 255),
        "RED_MED":   (31,  90, 173),
        "RED_DIM":   (15,  40,  84),
        "RED_DARK":  (3,   10,  22),
        "WHITE":     (255, 255, 255),
        "GREY":      (130, 150, 170),
    },
    {
        "name":          "Dark Green",
        "tick_contrast": True,
        "BG":        (0,   8,   0),
        "RED":       (49, 230,  90),
        "RED_MED":   (31, 150,  60),
        "RED_DIM":   (15,  70,  25),
        "RED_DARK":  (3,   18,   6),
        "WHITE":     (255, 255, 255),
        "GREY":      (130, 170, 140),
    },
    {
        "name":          "Dark Amber",
        "tick_contrast": False,
        "BG":        (8,   4,   0),
        "RED":       (255, 160,   0),
        "RED_MED":   (180, 100,   0),
        "RED_DIM":   (90,   45,   0),
        "RED_DARK":  (22,   10,   0),
        "WHITE":     (255, 255, 220),
        "GREY":      (170, 150, 100),
    },
    {
        "name":          "Dark Purple",
        "tick_contrast": False,
        "BG":        (5,   0,  10),
        "RED":       (200,  80, 255),
        "RED_MED":   (130,  40, 180),
        "RED_DIM":   (60,   15,  90),
        "RED_DARK":  (15,    3,  22),
        "WHITE":     (255, 240, 255),
        "GREY":      (160, 130, 180),
    },
    {
        "name":          "Dark Mono",
        "tick_contrast": True,
        "BG":        (5,   5,   5),
        "RED":       (220, 220, 220),
        "RED_MED":   (140, 140, 140),
        "RED_DIM":   (60,   60,  60),
        "RED_DARK":  (18,   18,  18),
        "WHITE":     (255, 255, 255),
        "GREY":      (150, 150, 150),
    },
    {
        "name":          "Light Red",
        "tick_contrast": True,
        "BG":        (245, 232, 232),
        "RED":       (200,  20,  20),
        "RED_MED":   (160,  60,  60),
        "RED_DIM":   (210, 170, 170),
        "RED_DARK":  (232, 215, 215),
        "WHITE":     (30,   20,  20),
        "GREY":      (110,  80,  80),
    },
    {
        "name":          "Light Blue",
        "tick_contrast": True,
        "BG":        (228, 238, 252),
        "RED":       (20,   80, 210),
        "RED_MED":   (60,  110, 185),
        "RED_DIM":   (170, 195, 232),
        "RED_DARK":  (212, 223, 243),
        "WHITE":     (15,   25,  50),
        "GREY":      (75,  100, 135),
    },
    {
        "name":          "Light Green",
        "tick_contrast": False,
        "BG":        (228, 248, 233),
        "RED":       (20,  170,  55),
        "RED_MED":   (50,  130,  75),
        "RED_DIM":   (170, 220, 180),
        "RED_DARK":  (212, 238, 218),
        "WHITE":     (10,   35,  18),
        "GREY":      (70,  120,  85),
    },
    {
        "name":          "Light Amber",
        "tick_contrast": True,
        "BG":        (252, 244, 225),
        "RED":       (190, 110,   0),
        "RED_MED":   (200, 150,  50),
        "RED_DIM":   (232, 207, 155),
        "RED_DARK":  (244, 230, 200),
        "WHITE":     (35,   22,   0),
        "GREY":      (125, 100,  50),
    },
    {
        "name":          "Light Purple",
        "tick_contrast": True,
        "BG":        (240, 230, 252),
        "RED":       (150,  30, 210),
        "RED_MED":   (170,  80, 200),
        "RED_DIM":   (210, 175, 238),
        "RED_DARK":  (232, 218, 248),
        "WHITE":     (30,   10,  50),
        "GREY":      (120,  90, 150),
    },
    {
        "name":          "Light Mono",
        "tick_contrast": True,
        "BG":        (240, 240, 240),
        "RED":       (40,   40,  40),
        "RED_MED":   (100, 100, 100),
        "RED_DIM":   (185, 185, 185),
        "RED_DARK":  (220, 220, 220),
        "WHITE":     (0,     0,   0),
        "GREY":      (110, 110, 110),
    },
]

_theme_index = 0
TICK_CONTRAST = False

def apply_theme(idx):
    global BG, RED, RED_MED, RED_DIM, RED_DARK, WHITE, GREY, TICK_CONTRAST, _theme_index
    global _menu_poly_cache
    _theme_index = idx % len(THEMES)
    t = THEMES[_theme_index]
    BG            = t["BG"]
    RED           = t["RED"]
    RED_MED       = t["RED_MED"]
    RED_DIM       = t["RED_DIM"]
    RED_DARK      = t["RED_DARK"]
    WHITE         = t["WHITE"]
    GREY          = t["GREY"]
    TICK_CONTRAST = t["tick_contrast"]
    _menu_poly_cache = None  # shape is theme-independent but clear for safety

apply_theme(0)

# ── RPM Arc geometry ──────────────────────────────────────────────────────────────
ARC_CX_O = 788.9;  ARC_CY_O = 1545.1;  ARC_R_UPPER = 1483.4
ARC_CX_I = 799.4;  ARC_CY_I = 1609.4;  ARC_R_LOWER = 1495.2

STEPS  = 600
LINE_W = 3

_ARC_ANGLE_AT_ZERO = -122.2284
_ARC_ANGLE_AT_MAX  =  -89.5713

def rpm_angle(rpm: float) -> float:
    frac = max(0.0, min(1.0, rpm / MAX_RPM))
    return _ARC_ANGLE_AT_ZERO + frac * (_ARC_ANGLE_AT_MAX - _ARC_ANGLE_AT_ZERO)

ARC_A_START = _ARC_ANGLE_AT_ZERO
ARC_A_END   = _ARC_ANGLE_AT_MAX

def _upper_xy(deg: float):
    a = math.radians(deg)
    return (ARC_CX_O + ARC_R_UPPER * math.cos(a),
            ARC_CY_O + ARC_R_UPPER * math.sin(a))

def _lower_xy(deg: float):
    a = math.radians(deg)
    return (ARC_CX_I + ARC_R_LOWER * math.cos(a),
            ARC_CY_I + ARC_R_LOWER * math.sin(a))

def _arc_pts(fn, a0, a1, n):
    return [fn(a0 + i / n * (a1 - a0)) for i in range(n + 1)]

def _ipts(pts):
    return [(int(round(p[0])), int(round(p[1]))) for p in pts]

# ── Gear circle ───────────────────────────────────────────────────────────────
CIRCLE_CX = -16
CIRCLE_CY = 239
CIRCLE_R  = 262

# ── Strip geometry ────────────────────────────────────────────────────────────
ROW1_Y = 346
ROW2_Y = 406
STRIP_L = 216
VCOL_A  = 454
VCOL_B  = 630
VCOL_C  = 381
VCOL_D  = 575

# ── Tick label radius ─────────────────────────────────────────────────────────
TICK_LABEL_R = ARC_R_LOWER + 18

def _tick_label_xy(deg: float):
    a = math.radians(deg)
    return (ARC_CX_I + TICK_LABEL_R * math.cos(a),
            ARC_CY_I + TICK_LABEL_R * math.sin(a))

# ── Hexagon grid ──────────────────────────────────────────────────────────────
def make_hex_grid() -> pygame.Surface:
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    R  = 27
    dx = R * math.sqrt(3)
    dy = R * 1.5
    brightness = sum(BG) / 3
    if brightness < 128:
        fill    = (*RED_DARK, 128)
        outline = (*RED_MED,  128)
    else:
        fill_col    = tuple(max(0, min(255, c - 15)) for c in BG)
        outline_col = tuple(max(0, min(255, c - 30)) for c in BG)
        fill    = (*fill_col,    210)
        outline = (*outline_col, 255)
    for row in range(-1, int(H / dy) + 4):
        for ci in range(-1, int(W / dx) + 4):
            hx = ci * dx + (dx / 2 if row % 2 else 0)
            hy = row * dy
            pts = [
                (int(hx + R * math.cos(math.radians(60 * i - 30))),
                 int(hy + R * math.sin(math.radians(60 * i - 30))))
                for i in range(6)
            ]
            pygame.draw.polygon(surf, fill, pts)
            pygame.draw.polygon(surf, outline, pts, 1)
    return surf

# ── RPM arc band ──────────────────────────────────────────────────────────────
def draw_arc_band(surf: pygame.Surface, rpm: float):
    TICK_LIT = _tick_lit_colour()

    upper_all = _arc_pts(_upper_xy, ARC_A_START, ARC_A_END, STEPS)
    lower_all = _arc_pts(_lower_xy, ARC_A_START, ARC_A_END, STEPS)

    fill_surf = pygame.Surface((W, H), pygame.SRCALPHA)

    n_all = len(upper_all)
    for i in range(n_all - 1):
        p1 = upper_all[i]; p2 = upper_all[i + 1]
        q1 = lower_all[i]; q2 = lower_all[i + 1]
        poly = _ipts([p1, p2, q2, q1])
        pygame.draw.polygon(fill_surf, RED_DARK, poly)

    target_angle = rpm_angle(rpm)
    bar_edge_x = None

    if target_angle > ARC_A_START + 1e-6:
        span_frac = (target_angle - ARC_A_START) / max(1e-6, ARC_A_END - ARC_A_START)
        n_pts = max(3, int(math.ceil(STEPS * span_frac)))

        upper_lit = _arc_pts(_upper_xy, ARC_A_START, target_angle, n_pts)
        lower_lit = _arc_pts(_lower_xy, ARC_A_START, target_angle, n_pts)

        poly_pts = upper_lit + list(reversed(lower_lit))
        poly = _ipts(poly_pts)

        rgb_base = RED
        pygame.draw.polygon(fill_surf, rgb_base, poly)

        edge_up = _upper_xy(target_angle)
        edge_lo = _lower_xy(target_angle)
        bar_edge_x = (edge_up[0] + edge_lo[0]) / 2.0

    up_last = upper_all[-1]
    lo_last = lower_all[-1]
    ext_poly = _ipts((up_last, lo_last, (W, lo_last[1]), (W, up_last[1])))
    pygame.draw.polygon(fill_surf, RED_DARK, ext_poly)

    surf.blit(fill_surf, (0, 0))

    t_glow       = max(0.0, min(1.0, rpm / 1000.0)) * THROTTLE_GLOW_SCALE
    glow_px      = GLOW_BLEED_PX    * t_glow
    glow_alpha   = GLOW_BLEED_ALPHA * t_glow
    outline_fade = TICK_LIGHT_WIDTH_RPM * t_glow

    if bar_edge_x is not None and glow_px > 0:
        glow_col  = rgb_base
        glow_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        angle_range       = ARC_A_END - ARC_A_START
        step_angle        = angle_range / STEPS
        glow_angular_span = (glow_px / ARC_R_UPPER) * (180 / math.pi)
        n_glow  = max(2, int(glow_angular_span / step_angle))
        for gi in range(n_glow):
            t_g   = gi / max(1, n_glow - 1)
            alpha = int(min(255, glow_alpha) * max(0.0, min(1.0, (1.0 - t_g))) ** 2)
            if alpha <= 0:
                continue
            a0 = target_angle + gi * step_angle
            a1 = target_angle + (gi + 1) * step_angle
            if a1 > ARC_A_END:
                a1 = ARC_A_END
            u0 = _ipts([_upper_xy(a0)])[0]
            u1 = _ipts([_upper_xy(a1)])[0]
            l0 = _ipts([_lower_xy(a0)])[0]
            l1 = _ipts([_lower_xy(a1)])[0]
            pygame.draw.polygon(glow_surf, (*glow_col, alpha), [u0, u1, l1, l0])
        surf.blit(glow_surf, (0, 0))

    bar_frac  = rpm / MAX_RPM
    fade_frac = outline_fade / MAX_RPM

    def _outline_col(x_frac: float):
        if t_glow <= 0:
            return None
        dist = x_frac - bar_frac
        if dist <= 0:
            return tuple(max(1, min(255, int(WHITE[c] * t_glow))) for c in range(3))
        elif dist <= fade_frac:
            t = max(0.0, min(1.0, dist / fade_frac))
            brightness = t_glow
            return tuple(max(1, min(255, int((WHITE[c] + (RED[c] - WHITE[c]) * t) * brightness))) for c in range(3))
        else:
            return None

    n = len(upper_all)
    for i in range(n - 1):
        pygame.draw.line(surf, RED,
                         (int(upper_all[i][0]),     int(upper_all[i][1])),
                         (int(upper_all[i + 1][0]), int(upper_all[i + 1][1])),
                         LINE_W)
    pygame.draw.line(surf, RED_DARK,
                     (int(up_last[0]), int(up_last[1])),
                     (W, int(up_last[1])), LINE_W)

    n2 = len(lower_all)
    for i in range(n2 - 1):
        pygame.draw.line(surf, RED,
                         (int(lower_all[i][0]),     int(lower_all[i][1])),
                         (int(lower_all[i + 1][0]), int(lower_all[i + 1][1])),
                         max(1, LINE_W - 1))
    pygame.draw.line(surf, RED_DARK,
                     (int(lo_last[0]), int(lo_last[1])),
                     (W, int(lo_last[1])), max(1, LINE_W - 1))

    n = len(upper_all)
    for i in range(n - 1):
        x_frac = i / max(1, n - 2)
        col = _outline_col(x_frac)
        if col is None:
            continue
        pygame.draw.line(surf, col,
                         (int(upper_all[i][0]),     int(upper_all[i][1])),
                         (int(upper_all[i + 1][0]), int(upper_all[i + 1][1])),
                         LINE_W)

    n2 = len(lower_all)
    for i in range(n2 - 1):
        x_frac = i / max(1, n2 - 2)
        col = _outline_col(x_frac)
        if col is None:
            continue
        pygame.draw.line(surf, col,
                         (int(lower_all[i][0]),     int(lower_all[i][1])),
                         (int(lower_all[i + 1][0]), int(lower_all[i + 1][1])),
                         max(1, LINE_W - 1))

    tick_rpms = [2000, 4000, 6000, 8000, 10000]
    tick_w = max(1, LINE_W // 2)
    for tr in tick_rpms:
        a   = rpm_angle(tr)
        up  = _upper_xy(a)
        lo  = _lower_xy(a)
        ux, uy = up
        lx, ly = lo
        thickness = math.hypot(ux - lx, uy - ly)
        out_len = int(round(max(4.0, (thickness + 6.0) * 0.5)))
        x0, y0 = int(round(lx)), int(round(ly))
        t = max(0.0, min(1.0, (rpm - tr + TICK_LIGHT_WIDTH_RPM) / (2 * TICK_LIGHT_WIDTH_RPM)))
        col = tuple(int(RED[c] + (TICK_LIT[c] - RED[c]) * t) for c in range(3))
        pygame.draw.line(surf, col, (x0, y0), (x0, y0 - out_len), tick_w)

    subtick_rpms = range(500, MAX_RPM, 500)
    major_rpms   = {2000, 4000, 6000, 8000, 10000}
    for tr in subtick_rpms:
        if tr in major_rpms:
            continue
        a   = rpm_angle(tr)
        lo  = _lower_xy(a)
        lx, ly = lo
        x0, y0 = int(round(lx)), int(round(ly))
        out_len = 18 if tr % 1000 == 0 else 10
        t = max(0.0, min(1.0, (rpm - tr + TICK_LIGHT_WIDTH_RPM) / (2 * TICK_LIGHT_WIDTH_RPM)))
        col = tuple(int(RED[c] + (TICK_LIT[c] - RED[c]) * t) for c in range(3))
        pygame.draw.line(surf, col, (x0, y0), (x0, y0 - out_len), 1)


# ── Tick labels ───────────────────────────────────────────────────────────────
def draw_ticks(surf: pygame.Surface, font: pygame.font.Font, rpm: float):
    TICK_LIT = _tick_lit_colour()
    for tr, lbl in ((2000, "2"), (4000, "4"), (6000, "6"), (8000, "8"), (10000, "10")):
        lx, ly = _tick_label_xy(rpm_angle(tr))

        gx, gy = TICK_LABEL_GLOBAL_OFFSET
        ox, oy = TICK_LABEL_OVERRIDES.get(tr, (0, 0))
        lx += gx + ox
        ly += gy + oy

        t = max(0.0, min(1.0, (rpm - tr + TICK_LIGHT_WIDTH_RPM) / (2 * TICK_LIGHT_WIDTH_RPM)))
        col = tuple(int(RED[c] + (TICK_LIT[c] - RED[c]) * t) for c in range(3))
        t_surf = font.render(lbl, True, col)
        surf.blit(t_surf, (int(lx - t_surf.get_width() / 2), int(ly - t_surf.get_height() / 2)))

# ── Icon loader ────────────────────────────────────────────────────────────────
def load_icon(filename: str, target_h: int) -> pygame.Surface | None:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    try:
        img = pygame.image.load(path).convert_alpha()
    except Exception:
        return None
    ow, oh = img.get_size()
    tw = int(ow * target_h / oh)
    return pygame.transform.smoothscale(img, (tw, target_h))

# ── Unit label vertical offset ────────────────────────────────────────────────
UNIT_OFFSET_Y = -4

# ── Data strip ────────────────────────────────────────────────────────────────
def draw_strip(surf, f_lbl, f_val, f_unit, state, icon_temp, icon_batt):
    cy1 = (ROW1_Y + ROW2_Y) / 2
    cy2 = (ROW2_Y + H) / 2

    pygame.draw.rect(surf, BG, (170, ROW1_Y, W - 170, ROW2_Y - ROW1_Y))
    pygame.draw.rect(surf, BG, (0,   ROW2_Y, W,       H - ROW2_Y))

    pygame.draw.line(surf, RED, (STRIP_L, ROW1_Y), (W,      ROW1_Y), LINE_W)
    pygame.draw.line(surf, RED, (0,       ROW2_Y), (W,      ROW2_Y), LINE_W)
    pygame.draw.line(surf, RED, (VCOL_A,  ROW1_Y), (VCOL_A, ROW2_Y), LINE_W)
    pygame.draw.line(surf, RED, (VCOL_B,  ROW1_Y), (VCOL_B, ROW2_Y), LINE_W)
    pygame.draw.line(surf, RED, (VCOL_C,  ROW2_Y), (VCOL_C, H),      LINE_W)
    pygame.draw.line(surf, RED, (VCOL_D,  ROW2_Y), (VCOL_D, H),      LINE_W)

    def cell(label, val, unit, cx, cy, unit_offset_y=0):
        sl = f_lbl.render(label, True, GREY)
        sv = f_val.render(val,   True, WHITE)
        su = f_unit.render(unit, True, GREY) if unit else None
        gap = 8
        w_total = sl.get_width() + gap + sv.get_width()
        if su:
            w_total += 5 + su.get_width()
        x = int(cx - w_total / 2)
        surf.blit(sl, (x, int(cy - sl.get_height() / 2)))
        x += sl.get_width() + gap
        surf.blit(sv, (x, int(cy - sv.get_height() / 2)))
        if su:
            surf.blit(su, (x + sv.get_width() + 5,
                           int(cy + sv.get_height() / 2 - su.get_height()) + unit_offset_y))

    def icon_cell(icon, val, unit, cx, cy, unit_offset_y=0):
        sv  = f_val.render(val,  True, WHITE)
        su  = f_unit.render(unit, True, GREY) if unit else None
        iw  = icon.get_width()  if icon else 0
        ih  = icon.get_height() if icon else 0
        gap = 8
        w_total = iw + gap + sv.get_width()
        if su:
            w_total += 5 + su.get_width()
        x = int(cx - w_total / 2)
        if icon:
            surf.blit(icon, (x, int(cy - ih / 2)))
            x += iw + gap
        surf.blit(sv, (x, int(cy - sv.get_height() / 2)))
        if su:
            surf.blit(su, (x + sv.get_width() + 5,
                           int(cy + sv.get_height() / 2 - su.get_height()) + unit_offset_y))

    cell("ODO", f"{state['odo']:.2f}", "km", (STRIP_L + VCOL_A) / 2, cy1, unit_offset_y=UNIT_OFFSET_Y)
    if icon_temp:
        icon_cell(icon_temp, str(int(state["temp"])), "°C", (VCOL_A + VCOL_B) / 2, cy1, unit_offset_y=UNIT_OFFSET_Y-1)
    else:
        cell("TEMP", str(int(state["temp"])), "°C", (VCOL_A + VCOL_B) / 2, cy1, unit_offset_y=UNIT_OFFSET_Y)
    if icon_batt:
        icon_cell(icon_batt, f"{state['volt']:.1f}", "V", (VCOL_B + W) / 2, cy1, unit_offset_y=UNIT_OFFSET_Y)
    else:
        cell("VOLT", f"{state['volt']:.1f}", "V", (VCOL_B + W) / 2, cy1, unit_offset_y=UNIT_OFFSET_Y)

    cell("RANGE", str(state["range"]), "km",      (STRIP_L + VCOL_C) / 2, cy2, unit_offset_y=UNIT_OFFSET_Y)
    cell("ECO",   str(state["eco"]),   "L/100km", (VCOL_C + VCOL_D) / 2,  cy2, unit_offset_y=UNIT_OFFSET_Y)
    t = f_val.render(state["time"], True, WHITE)
    cx_t = (VCOL_D + W) / 2
    surf.blit(t, (int(cx_t - t.get_width() / 2), int(cy2 - t.get_height() / 2)))

# ── Speed ─────────────────────────────────────────────────────────────────────
def draw_speed(surf, f_spd, f_kmh, speed: float, blink_on: bool = False):
    s = f_spd.render(str(int(speed)), True, WHITE)
    u = f_kmh.render("km/h", True, GREY)

    spd_x = 683 - s.get_width()
    spd_y = 233 - s.get_height() // 2
    kmh_x = 682
    kmh_y = 271 - u.get_height() // 2

    spd_cx = spd_x + s.get_width() // 2
    spd_cy = 233
    kmh_cx = kmh_x + u.get_width() // 2
    kmh_cy = 271

    if blink_on:
        glow_surf = pygame.Surface((W, H), pygame.SRCALPHA)

        max_r = 130
        for r in range(max_r, 0, -1):
            t     = r / max_r
            alpha = int(80 * (1.0 - t) ** 2)
            if alpha <= 0:
                continue
            w_el = int(r * 2 * (s.get_width() / 160.0))
            rect = pygame.Rect(0, 0, max(1, w_el), r * 2)
            rect.center = (spd_cx, spd_cy)
            pygame.draw.ellipse(glow_surf, (255, 49, 49, alpha), rect)

        max_kr = 45
        for r in range(max_kr, 0, -1):
            t     = r / max_kr
            alpha = int(60 * (1.0 - t) ** 2)
            if alpha <= 0:
                continue
            w_el = int(r * 2 * (u.get_width() / 55.0))
            rect = pygame.Rect(0, 0, max(1, w_el), r * 2)
            rect.center = (kmh_cx, kmh_cy)
            pygame.draw.ellipse(glow_surf, (255, 49, 49, alpha), rect)

        surf.blit(glow_surf, (0, 0))
        spd_col = (255, 49, 49)
        kmh_col = (255, 49, 49)
    else:
        spd_col = WHITE
        kmh_col = GREY

    s = f_spd.render(str(int(speed)), True, spd_col)
    u = f_kmh.render("km/h", True, kmh_col)
    surf.blit(s, (spd_x, spd_y))
    surf.blit(u, (kmh_x, kmh_y))

# ── Gear label + character ─────────────────────────────────────────────────────
def draw_gear(surf, f_g, f_glbl, gear: str):
    lbl = f_glbl.render("GEAR", True, WHITE)
    surf.blit(lbl, (86 - lbl.get_width() // 2, 57 - lbl.get_height() // 2))
    col = RED if gear == "N" else WHITE
    g = f_g.render(gear, True, col)
    surf.blit(g, (86 - g.get_width() // 2, 127 - g.get_height() // 2))

# ── Font loader ────────────────────────────────────────────────────────────────
def load_font(names, size_px: int, bold=False, italic=False) -> pygame.font.Font:
    fonts_dir = os.path.join(".", "fonts")
    for name in names:
        path = os.path.join(fonts_dir, name)
        if os.path.isfile(path):
            try:
                return pygame.font.Font(path, size_px)
            except Exception:
                pass
        try:
            f = pygame.font.SysFont(name, size_px, bold=bold, italic=italic)
            if f:
                return f
        except Exception:
            pass
    return pygame.font.Font(None, size_px)


# ── Menu button polygon ────────────────────────────────────────────────────────
def _menu_polygon() -> list[tuple[int, int]]:
    """
    Rounded 3-sided polygon:
      Edge 1 – RPM-arc side   : circle (ARC_CX_I, ARC_CY_I, ARC_R_LOWER + MENU_SEPARATION)
      Edge 2 – gear-circle side: circle (CIRCLE_CX, CIRCLE_CY, CIRCLE_R + MENU_CIRCLE_SEPARATION)
      Edge 3 – closing arc     : chosen radius, bulging outward
    Edge 1 and Edge 2 meet exactly at the real intersection of those two circles
    (no straight seam needed there).
    """
    cx, cy   = ARC_CX_I, ARC_CY_I
    r_inner  = ARC_R_LOWER + MENU_SEPARATION
    gcx, gcy = CIRCLE_CX, CIRCLE_CY
    r_gear   = CIRCLE_R + MENU_CIRCLE_SEPARATION

    def pivot(angle_deg):
        a = math.radians(angle_deg)
        return cx + r_inner * math.cos(a), cy + r_inner * math.sin(a)

    def circle_intersection(c1, r1, c2, r2):
        dx, dy = c2[0] - c1[0], c2[1] - c1[1]
        d = math.hypot(dx, dy)
        a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
        h = math.sqrt(max(0.0, r1 * r1 - a * a))
        xm, ym = c1[0] + a * dx / d, c1[1] + a * dy / d
        rx, ry = -dy / d, dx / d
        return (xm + h * rx, ym + h * ry), (xm - h * rx, ym - h * ry)

    def arc(center, r, a0, a1, n=24):
        return [(center[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 center[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
                for i in range(n + 1)]

    v_top = pivot(MENU_ARC_ANGLE_TOP)

    # shared vertex: true intersection of the RPM circle and the gear circle,
    # picked as the one nearer the old MENU_ARC_ANGLE_BOT region
    approx_bot = pivot(MENU_ARC_ANGLE_BOT)
    p1, p2 = circle_intersection((cx, cy), r_inner, (gcx, gcy), r_gear)
    v_join = p1 if math.hypot(p1[0]-approx_bot[0], p1[1]-approx_bot[1]) < \
                   math.hypot(p2[0]-approx_bot[0], p2[1]-approx_bot[1]) else p2

    a_join_arc  = math.degrees(math.atan2(v_join[1] - cy,  v_join[0] - cx))
    a_join_gear = math.degrees(math.atan2(v_join[1] - gcy, v_join[0] - gcx))
    a_v3   = a_join_gear - MENU_CIRCLE_SWEEP
    v3     = (gcx + r_gear * math.cos(math.radians(a_v3)),
              gcy + r_gear * math.sin(math.radians(a_v3)))

    def closing_arc(pa, pb, r):
        mx, my   = (pa[0]+pb[0])/2, (pa[1]+pb[1])/2
        ddx, ddy = pb[0]-pa[0], pb[1]-pa[1]
        d = math.hypot(ddx, ddy)
        h = math.sqrt(max(0.0, r*r - (d/2)**2))
        px, py = -ddy/d, ddx/d
        c1, c2 = (mx+h*px, my+h*py), (mx-h*px, my-h*py)
        d1 = math.hypot(c1[0]-cx, c1[1]-cy)
        d2 = math.hypot(c2[0]-cx, c2[1]-cy)
        ocx, ocy = c1 if d1 < d2 else c2   # nearer centre -> bulges outward
        a1 = math.atan2(pa[1]-ocy, pa[0]-ocx)
        a2 = math.atan2(pb[1]-ocy, pb[0]-ocx)
        da = a2 - a1
        if da >  math.pi: da -= 2 * math.pi
        if da < -math.pi: da += 2 * math.pi
        return [(ocx + r*math.cos(a1 + da*i/24), ocy + r*math.sin(a1 + da*i/24))
                for i in range(25)]

    edge_rpm    = arc((cx, cy),   r_inner, MENU_ARC_ANGLE_TOP, a_join_arc)
    edge_circle = arc((gcx, gcy), r_gear,  a_join_gear,         a_v3)
    edge_close  = closing_arc(v3, v_top, MENU_OUTER_ARC_R)

    poly_f = edge_rpm + edge_circle + edge_close
    return [(int(round(p[0])), int(round(p[1]))) for p in poly_f]


_menu_poly_cache: list[tuple[int, int]] | None = None


def _get_menu_poly() -> list[tuple[int, int]]:
    global _menu_poly_cache
    if _menu_poly_cache is None:
        _menu_poly_cache = _menu_polygon()
    return _menu_poly_cache


# ── Point-in-polygon (ray casting) ───────────────────────────────────────────
def point_in_poly(px: float, py: float, poly: list[tuple[int, int]]) -> bool:
    n      = len(poly)
    inside = False
    j      = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and \
           (px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def draw_menu_button(surf: pygame.Surface, mouse_pos: tuple[int, int] | None = None):
    poly = _get_menu_poly()
    if not poly:
        return

    hovered = point_in_poly(*mouse_pos, poly) if mouse_pos else False

    col_bg  = RED_MED if hovered else RED_DARK
    col_brd = RED     if hovered else RED_MED

    pygame.draw.polygon(surf, col_bg, poly)
    n = len(poly)
    for i in range(n):
        pygame.draw.line(surf, col_brd, poly[i], poly[(i + 1) % n], 1)

    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    label_cx = (min(xs) + max(xs)) // 2
    label_cy = (min(ys) + max(ys)) // 2 - 2

    f = load_font(["OpenSans-Bold.ttf", "Open Sans", "Arial"], 18, bold=True)
    lbl = _render_tracked(f, "MENU", WHITE, tracking_px=3)
    surf.blit(lbl, (label_cx - lbl.get_width() // 2,
                    label_cy - lbl.get_height() // 2))


def _render_tracked(font: pygame.font.Font, text: str, color, tracking_px: int = 0) -> pygame.Surface:
    """Render text with extra letter-spacing (tracking) for a more deliberate,
    designed look on short HMI labels than pygame's default cramped kerning."""
    glyphs = [font.render(ch, True, color) for ch in text]
    total_w = sum(g.get_width() for g in glyphs) + tracking_px * (len(glyphs) - 1)
    height = max(g.get_height() for g in glyphs)
    out = pygame.Surface((total_w, height), pygame.SRCALPHA)
    x = 0
    for g in glyphs:
        out.blit(g, (x, 0))
        x += g.get_width() + tracking_px
    return out


BRIGHTNESS = [1.0]
MENU_ITEMS = ["Theme", "Brightness"]

def draw_menu_screen(surf, menu_state, fonts):
    f_lbl  = fonts["lbl"]
    f_val  = fonts["val"]
    f_unit = fonts["unit"]

    surf.fill(BG)

    pygame.draw.line(surf, RED, (0, 60), (W, 60), 2)
    title = f_val.render("SETTINGS", True, WHITE)
    surf.blit(title, (W // 2 - title.get_width() // 2, 18))

    back_r = pygame.Rect(16, 14, 72, 32)
    pygame.draw.rect(surf, RED_DARK, back_r, border_radius=4)
    pygame.draw.rect(surf, RED,      back_r, 1, border_radius=4)
    bk = f_lbl.render("< BACK", True, WHITE)
    surf.blit(bk, (back_r.centerx - bk.get_width() // 2,
                   back_r.centery - bk.get_height() // 2))
    menu_state["_back_btn"] = back_r

    sec_y = 90
    sec_lbl = f_val.render("THEME", True, RED)
    surf.blit(sec_lbl, (40, sec_y))
    pygame.draw.line(surf, RED_DIM, (40, sec_y + 30), (W - 40, sec_y + 30), 1)

    arrow_l = pygame.Rect(40,  sec_y + 44, 48, 48)
    arrow_r = pygame.Rect(712, sec_y + 44, 48, 48)
    for r, ch in ((arrow_l, "<"), (arrow_r, ">")):
        pygame.draw.rect(surf, RED_MED, r, border_radius=6)
        pygame.draw.rect(surf, RED,     r, 2, border_radius=6)
        s = f_val.render(ch, True, WHITE)
        surf.blit(s, (r.centerx - s.get_width() // 2,
                      r.centery - s.get_height() // 2))

    t_name = fonts["val"].render(THEMES[_theme_index]["name"], True, WHITE)
    surf.blit(t_name, (W // 2 - t_name.get_width() // 2, sec_y + 56))

    n = len(THEMES)
    dot_total = n * 14
    dot_x0 = W // 2 - dot_total // 2
    for i in range(n):
        col = RED if i == _theme_index else RED_DIM
        pygame.draw.circle(surf, col, (dot_x0 + i * 14 + 7, sec_y + 108), 4)

    menu_state["_arrow_l"] = arrow_l
    menu_state["_arrow_r"] = arrow_r

    preview_y = sec_y + 122
    preview_h = 28
    t = THEMES[_theme_index]
    preview_cols = [t["RED_DARK"], t["RED_DIM"], t["RED_MED"], t["RED"], t["WHITE"]]
    seg_w = (W - 80) // len(preview_cols)
    for i, col in enumerate(preview_cols):
        rx = 40 + i * seg_w
        pygame.draw.rect(surf, col, (rx, preview_y, seg_w, preview_h))
    pygame.draw.rect(surf, RED, (40, preview_y, seg_w * len(preview_cols), preview_h), 1)

    br_y = 290
    br_lbl = f_val.render("BRIGHTNESS", True, RED)
    surf.blit(br_lbl, (40, br_y))
    pygame.draw.line(surf, RED_DIM, (40, br_y + 30), (W - 40, br_y + 30), 1)

    bar_x = 40
    bar_w = W - 80
    bar_h = 16
    bar_y = br_y + 54
    bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)

    pygame.draw.rect(surf, RED_DARK, bar_rect, border_radius=8)
    pygame.draw.rect(surf, RED_DIM,  bar_rect, 1, border_radius=8)

    fill_w = max(8, int(bar_w * BRIGHTNESS[0]))
    pygame.draw.rect(surf, RED, (bar_x, bar_y, fill_w, bar_h), border_radius=8)

    knob_x = bar_x + fill_w
    pygame.draw.circle(surf, WHITE, (knob_x, bar_y + bar_h // 2), 14)
    pygame.draw.circle(surf, RED,   (knob_x, bar_y + bar_h // 2), 14, 2)

    pct = f_val.render(f"{int(BRIGHTNESS[0] * 100)}%", True, WHITE)
    surf.blit(pct, (W // 2 - pct.get_width() // 2, bar_y + 26))

    menu_state["_bright_bar"]     = bar_rect
    menu_state["_bright_knob_cx"] = knob_x
    menu_state["_bright_knob_cy"] = bar_y + bar_h // 2

    for pct_t in (0.25, 0.5, 0.75):
        tx = int(bar_x + bar_w * pct_t)
        pygame.draw.line(surf, RED_MED, (tx, bar_y + bar_h + 2), (tx, bar_y + bar_h + 8), 1)

    pygame.draw.line(surf, RED_DIM, (0, H - 36), (W, H - 36), 1)
    hint = f_unit.render("", True, GREY)
    surf.blit(hint, (W // 2 - hint.get_width() // 2, H - 22))

def start_control_panel(state, demo):
    def run():
        root = tk.Tk()
        root.title("RS125 Live Control")

        def mk(name, frm, to, key, resolution=1):
            tk.Label(root, text=name).pack()
            def on(val, k=key):
                if k in ("throttle", "fuel"):
                    state[k] = round(float(val), 2)
                elif k == "volt":
                    state[k] = round(float(val), 1)
                else:
                    state[k] = int(float(val))
            s = tk.Scale(root, from_=frm, to=to,
                         orient="horizontal",
                         resolution=resolution,
                         command=on)
            s.set(state[key])
            s.pack()

        mk("RPM",      0,     MAX_RPM, "rpm")
        mk("Speed",    0,     200,     "speed")
        mk("Temp",    -20,    120,     "temp")
        mk("Voltage",  10,    15,      "volt",     resolution=0.1)
        mk("Eco",      0,     200,     "eco")
        mk("Range",    0,     300,     "range")
        mk("Throttle", 0.0,   1.0,     "throttle", resolution=0.01)
        mk("Fuel",     0.0,   1.0,     "fuel",     resolution=0.01)

        tk.Label(root, text="").pack()

        theme_label = tk.Label(root, text=f"Theme: {THEMES[_theme_index]['name']}",
                               font=("Arial", 10, "bold"))
        theme_label.pack()

        def next_theme():
            apply_theme(_theme_index + 1)
            theme_label.config(text=f"Theme: {THEMES[_theme_index]['name']}")
            state["_rebuild_hex"] = True

        tk.Button(root, text="NEXT THEME", command=next_theme,
                  bg="navy", fg="white", font=("Arial", 11, "bold"),
                  padx=10, pady=4).pack(pady=4)

        tk.Label(root, text="").pack()

        def start_demo():
            if not demo.active:
                demo.start(state)
        tk.Button(root, text="START DEMO", command=start_demo,
                  bg="darkred", fg="white", font=("Arial", 12, "bold"),
                  padx=10, pady=6).pack(pady=8)

        root.mainloop()

    threading.Thread(target=run, daemon=True).start()

def draw_fuel_gauge(surf, f_lbl, f_tick, fuel: float):
    GEAR_CX = CIRCLE_CX
    GEAR_CY = CIRCLE_CY
    GEAR_R  = CIRCLE_R

    LINE_TOP_ANGLE = 0.0
    LINE_TOP_DIR   = -23.0
    LINE_TOP_DIST  = 15
    LINE_TOP_LEN   = 75

    LINE_BOT_ANGLE = 65.0
    LINE_BOT_DIR   = 65.0
    LINE_BOT_DIST  = 15
    LINE_BOT_LEN   = 35

    BAND_SPACING   = 35
    LEFT_ARC_R     = GEAR_R
    SEP_EXTEND     = 2

    N_SEG     = 6
    STEPS_ARC = 40

    def pt_on_circle(r, a_deg):
        a = math.radians(a_deg)
        return (GEAR_CX + r * math.cos(a), GEAR_CY + r * math.sin(a))

    def pt_along(origin, a_deg, length):
        a = math.radians(a_deg)
        return (origin[0] - length * math.cos(a), origin[1] - length * math.sin(a))

    def ipt(p):
        return (int(round(p[0])), int(round(p[1])))

    def left_arc_centre(p1, p2, r):
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        d  = math.hypot(dx, dy)
        h  = math.sqrt(max(0.0, r * r - (d / 2) ** 2))
        px = -dy / d
        py =  dx / d
        c1 = (mx + h * px, my + h * py)
        c2 = (mx - h * px, my - h * py)
        return c1 if c1[0] < c2[0] else c2

    def left_arc_pts(p1, p2, r):
        cx2, cy2 = left_arc_centre(p1, p2, r)
        a1 = math.atan2(p1[1] - cy2, p1[0] - cx2)
        a2 = math.atan2(p2[1] - cy2, p2[0] - cx2)
        da = a2 - a1
        if da > math.pi:  da -= 2 * math.pi
        if da < -math.pi: da += 2 * math.pi
        steps = 60
        return [ipt((cx2 + r * math.cos(a1 + da * s / steps),
                     cy2 + r * math.sin(a1 + da * s / steps)))
                for s in range(steps + 1)]

    def draw_left_arc(p1, p2, r, col, width):
        pts = left_arc_pts(p1, p2, r)
        for s in range(len(pts) - 1):
            pygame.draw.line(surf, col, pts[s], pts[s + 1], width)

    def sample_arc(pts, frac):
        if len(pts) < 2:
            return pts[0]
        idx = frac * (len(pts) - 1)
        i   = int(idx)
        t   = idx - i
        if i >= len(pts) - 1:
            return pts[-1]
        p1, p2 = pts[i], pts[i + 1]
        return (int(p1[0] + (p2[0] - p1[0]) * t), int(p1[1] + (p2[1] - p1[1]) * t))

    r_right       = GEAR_R - LINE_TOP_DIST
    r_right_inner = r_right - BAND_SPACING

    top_right_outer = pt_on_circle(r_right,       LINE_TOP_ANGLE)
    top_right_inner = pt_on_circle(r_right_inner, LINE_TOP_ANGLE)
    top_left_outer  = pt_along(top_right_outer, LINE_TOP_DIR, LINE_TOP_LEN)
    top_left_inner  = pt_along(top_right_inner, LINE_TOP_DIR, LINE_TOP_LEN - BAND_SPACING)

    bot_right_outer = pt_on_circle(r_right,       LINE_BOT_ANGLE)
    bot_right_inner = pt_on_circle(r_right_inner, LINE_BOT_ANGLE)
    bot_left_outer  = pt_along(bot_right_outer, LINE_BOT_DIR, LINE_BOT_LEN)
    bot_left_inner  = pt_along(bot_right_inner, LINE_BOT_DIR, LINE_BOT_LEN - BAND_SPACING)

    fuel  = max(0.0, min(1.0, fuel))
    low   = fuel < 0.2
    n_lit = int(round(fuel * N_SEG))

    outer_left_pts = left_arc_pts(bot_left_outer, top_left_outer, LEFT_ARC_R)

    segs = []
    for i in range(N_SEG):
        frac_lo = i / N_SEG
        frac_hi = (i + 1) / N_SEG

        a_lo = LINE_BOT_ANGLE + frac_lo * (LINE_TOP_ANGLE - LINE_BOT_ANGLE)
        a_hi = LINE_BOT_ANGLE + frac_hi * (LINE_TOP_ANGLE - LINE_BOT_ANGLE)

        ro_lo = ipt(pt_on_circle(r_right, a_lo))
        ro_hi = ipt(pt_on_circle(r_right, a_hi))

        lo_lo = sample_arc(outer_left_pts, frac_lo)
        lo_hi = sample_arc(outer_left_pts, frac_hi)

        segs.append((ro_lo, ro_hi, lo_lo, lo_hi))

    for i, (ro_lo, ro_hi, lo_lo, lo_hi) in enumerate(segs):
        col = (255, 49, 49) if (low and i < n_lit) else RED if i < n_lit else RED_DARK
        pygame.draw.polygon(surf, col, [ro_lo, ro_hi, lo_hi, lo_lo])

    for i in range(STEPS_ARC):
        a0 = LINE_BOT_ANGLE + i       / STEPS_ARC * (LINE_TOP_ANGLE - LINE_BOT_ANGLE)
        a1 = LINE_BOT_ANGLE + (i + 1) / STEPS_ARC * (LINE_TOP_ANGLE - LINE_BOT_ANGLE)
        pygame.draw.line(surf, RED, ipt(pt_on_circle(r_right, a0)),
                                    ipt(pt_on_circle(r_right, a1)), LINE_W)

    pygame.draw.line(surf, RED, ipt(top_right_outer), ipt(top_left_outer), LINE_W)
    pygame.draw.line(surf, RED, ipt(bot_right_outer), ipt(bot_left_outer), LINE_W)

    draw_left_arc(top_left_outer, bot_left_outer, LEFT_ARC_R, RED, LINE_W)

    for i, (ro_lo, ro_hi, lo_lo, lo_hi) in enumerate(segs):
        if i == 0:
            continue
        div_col = WHITE if i < n_lit + 1 else RED
        dx = lo_lo[0] - ro_lo[0]
        dy = lo_lo[1] - ro_lo[1]
        d  = math.hypot(dx, dy)
        if d > 0:
            ex = int(SEP_EXTEND * dx / d)
            ey = int(SEP_EXTEND * dy / d)
            p1 = (ro_lo[0] - ex, ro_lo[1] - ey)
            p2 = (lo_lo[0] + ex, lo_lo[1] + ey)
        else:
            p1, p2 = ro_lo, lo_lo
        pygame.draw.line(surf, div_col, p1, p2, 1)

    col_f = WHITE
    col_e = (255, 49, 49) if low else RED

    f_s = f_tick.render("F", True, col_f)
    e_s = f_tick.render("E", True, col_f)

    f_pos = sample_arc(outer_left_pts, 1.0)
    e_pos = sample_arc(outer_left_pts, 0.0)

    fx = f_pos[0] - f_s.get_width() - 15
    fy = f_pos[1] - f_s.get_height() + 30
    ex = e_pos[0] - e_s.get_width() + 5
    ey = e_pos[1] - e_s.get_height() - 15

    surf.blit(f_s, (fx, fy))
    surf.blit(e_s, (ex, ey))


def main():
    state = dict(rpm=4500, speed=45, gear="N",
                 temp=14, volt=12.4,
                 odo=1234.56, range=95, eco=95, time="19:22",
                 throttle=0.0, fuel=1.0,
                 _rebuild_hex=False)
    gears = ["N", "1", "2", "3", "4", "5", "6"]

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("RS125 TFT Dash — 800×480")
    clock = pygame.time.Clock()

    demo = DemoPlayer()
    start_control_panel(state, demo)

    f_spd      = load_font(["Roboto-BoldItalic.ttf", "Roboto", "Arial"], 162, bold=True, italic=True)
    f_kmh      = load_font(["OpenSans-Regular.ttf", "Open Sans", "Arial"], 28)
    f_kmh.set_italic(True)
    f_gear_val = load_font(["OpenSauceOne-Bold.ttf", "OpenSauceOne", "Arial"], 96, bold=True)
    f_gear_lbl = load_font(["Roboto-BoldItalic.ttf", "Roboto", "Arial"], 25, bold=True, italic=True)
    f_val      = load_font(["OpenSans-Bold.ttf", "Open Sans", "Arial"], 26, bold=True)
    f_lbl      = load_font(["OpenSans-Regular.ttf", "Open Sans", "Arial"], 20)
    f_unit     = load_font(["OpenSans-Regular.ttf", "Open Sans", "Arial"], 17)
    f_tick     = load_font(["Roboto-BoldItalic.ttf", "Roboto", "Arial"], 20, bold=True, italic=True)

    hex_grid  = make_hex_grid()
    icon_temp = load_icon("icon_temp.png", 30)
    icon_batt = load_icon("icon_batt.png", 30)

    gi           = 0
    blink_t      = 0.0
    disp_rpm     = float(state["rpm"])
    disp_speed   = float(state["speed"])
    menu_state   = {"open": False, "sel": 0, "drag_bright": False}
    odo_mode     = 0
    eco_imperial = False
    trip_a       = 0.0
    trip_b       = 0.0

    running = True
    while running:
        dt_ms = clock.tick(FPS)
        dt    = dt_ms / 1000.0
        state["time"] = datetime.now().strftime("%H:%M")

        if state.get("_rebuild_hex"):
            hex_grid = make_hex_grid()
            state["_rebuild_hex"] = False

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            if ev.type == pygame.MOUSEBUTTONUP:
                menu_state["drag_bright"] = False

            if ev.type == pygame.MOUSEMOTION and menu_state.get("drag_bright"):
                bar = menu_state.get("_bright_bar")
                if bar:
                    rel = (ev.pos[0] - bar.left) / bar.width
                    BRIGHTNESS[0] = max(0.05, min(1.0, rel))

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos

                if menu_state["open"]:
                    if menu_state.get("_back_btn") and menu_state["_back_btn"].collidepoint(mx, my):
                        menu_state["open"] = False

                    elif menu_state.get("_arrow_l") and menu_state["_arrow_l"].collidepoint(mx, my):
                        apply_theme(_theme_index - 1)
                        state["_rebuild_hex"] = True

                    elif menu_state.get("_arrow_r") and menu_state["_arrow_r"].collidepoint(mx, my):
                        apply_theme(_theme_index + 1)
                        state["_rebuild_hex"] = True

                    elif menu_state.get("_bright_bar"):
                        bar      = menu_state["_bright_bar"]
                        knob_cx  = menu_state.get("_bright_knob_cx", bar.left)
                        knob_cy  = menu_state.get("_bright_knob_cy", bar.centery)
                        if math.hypot(mx - knob_cx, my - knob_cy) < 20:
                            menu_state["drag_bright"] = True
                        elif bar.inflate(0, 24).collidepoint(mx, my):
                            rel = (mx - bar.left) / bar.width
                            BRIGHTNESS[0] = max(0.05, min(1.0, rel))

                else:
                    if mx < 170 and 57 < my < 200:
                        if not demo.active:
                            gi = (gi + 1) % len(gears)
                            state["gear"] = gears[gi]

                    elif STRIP_L < mx < VCOL_A and ROW1_Y < my < ROW2_Y:
                        odo_mode = (odo_mode + 1) % 3

                    elif VCOL_C < mx < VCOL_D and ROW2_Y < my < H:
                        eco_imperial = not eco_imperial

            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if k in (pygame.K_q, pygame.K_ESCAPE):
                    if menu_state["open"]:
                        menu_state["open"] = False
                    else:
                        running = False
                elif not demo.active and not menu_state["open"]:
                    if   k == pygame.K_UP:    state["rpm"]   = min(MAX_RPM, state["rpm"]   + 500)
                    elif k == pygame.K_DOWN:  state["rpm"]   = max(0,       state["rpm"]   - 500)
                    elif k == pygame.K_w:     state["speed"] = min(200,     state["speed"] + 5)
                    elif k == pygame.K_s:     state["speed"] = max(0,       state["speed"] - 5)
                    elif k == pygame.K_RIGHT: gi = min(len(gears)-1, gi+1); state["gear"] = gears[gi]
                    elif k == pygame.K_LEFT:  gi = max(0, gi-1);            state["gear"] = gears[gi]
                    elif k == pygame.K_t:     state["temp"]  = max(-20,     state["temp"]  - 1)
                    elif k == pygame.K_y:     state["temp"]  = min(120,     state["temp"]  + 1)
                    elif k == pygame.K_b:     state["volt"]  = max(10.0,    round(state["volt"] - 0.1, 1))
                    elif k == pygame.K_n:     state["volt"]  = min(15.0,    round(state["volt"] + 0.1, 1))

        demo.update(state, dt)

        alpha_rpm   = 1.0 - math.exp(-RPM_SMOOTHNESS   * dt) if dt > 0 else 1.0
        alpha_speed = 1.0 - math.exp(-SPEED_SMOOTHNESS * dt) if dt > 0 else 1.0
        disp_rpm   += (state["rpm"]   - disp_rpm)   * alpha_rpm
        disp_speed += (state["speed"] - disp_speed) * alpha_speed

        if disp_rpm < 50:
            disp_rpm = 0.0

        blink_t += dt
        blink_on = disp_rpm >= REDLINE_RPM and (int(blink_t * 6) % 2 == 0)

        if not menu_state["open"]:
            trip_a += state["speed"] / 3600.0 * dt
            trip_b += state["speed"] / 3600.0 * dt

        odo_labels = ["ODO", "TRIP A", "TRIP B"]
        odo_values = [
            f"{state['odo']:.2f}",
            f"{trip_a:.2f}",
            f"{trip_b:.2f}",
        ]
        state["_odo_label"] = odo_labels[odo_mode]
        state["_odo_value"] = odo_values[odo_mode]

        if eco_imperial:
            mpg = (282.5 / state["eco"]) if state["eco"] > 0 else 0
            state["_eco_value"] = f"{mpg:.1f}"
            state["_eco_unit"]  = "mpg"
        else:
            state["_eco_value"] = str(state["eco"])
            state["_eco_unit"]  = "L/100km"

        if menu_state["open"]:
            screen.fill(BG)
            screen.blit(hex_grid, (0, 0))
            draw_menu_screen(screen, menu_state, {
                "lbl":  f_lbl,
                "val":  f_val,
                "unit": f_unit,
            })

        else:
            screen.fill(BG)
            screen.blit(hex_grid, (0, 0))

            draw_strip(screen, f_lbl, f_val, f_unit, state, icon_temp, icon_batt)

            pygame.draw.circle(screen, BG,  (CIRCLE_CX, CIRCLE_CY), CIRCLE_R)
            pygame.draw.circle(screen, RED, (CIRCLE_CX, CIRCLE_CY), CIRCLE_R, LINE_W)

            draw_arc_band(screen, disp_rpm)
            draw_ticks(screen, f_tick, disp_rpm)

            draw_speed(screen, f_spd, f_kmh, disp_speed, blink_on)
            draw_fuel_gauge(screen, f_lbl, f_tick, state["fuel"])
            draw_gear(screen, f_gear_val, f_gear_lbl, state["gear"])

            if BRIGHTNESS[0] < 1.0:
                dim = pygame.Surface((W, H), pygame.SRCALPHA)
                dim.fill((0, 0, 0, int((1.0 - BRIGHTNESS[0]) * 255)))
                screen.blit(dim, (0, 0))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()