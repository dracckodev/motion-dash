"use strict";

const THROTTLE_GLOW_SCALE = 0;

const DEMO_IDLE_RPM = 1800;
const DEMO_HOT_TEMP = 82;
const DEMO_BASE_TEMP = 14;
const DEMO_BASE_VOLT = 13.8;
const DEMO_ODO_START = 1234.56;
const DEMO_SHIFT_RPM = 3500;
const DEMO_TOP_SPEED = 110;
const DEMO_GEAR_RPMS = [0, 10500, 10500, 10500, 10500, 10500, 10200];

const MENU_ARC_ANGLE_TOP = -105.6;
const MENU_ARC_ANGLE_BOT = -113.5;
const MENU_SEPARATION = 62.0;
const MENU_LINE_ANGLE_TOP = -20.0;
const MENU_LINE_ANGLE_BOT = 35.0;
const MENU_LINE_LEN_TOP = 82.0;
const MENU_LINE_LEN_BOT = 58.0;
const MENU_OUTER_ARC_R = 235.0;
const MENU_CIRCLE_SEPARATION = 10.0;
const MENU_CIRCLE_SWEEP = 13.5;

const W = 800;
const H = 480;
const FPS = 60;
const SCALE = W / 600.0;

const TICK_LABEL_GLOBAL_OFFSET = [10, -28];
const TICK_LABEL_OVERRIDES = {
  2000: [0, 0],
  4000: [0, 0],
  6000: [-4, 3.5],
  8000: [-4, 3.5],
  10000: [-4, 3.5],
};

const MAX_RPM = 12000;
const REDLINE_RPM = 9500;
const GLOW_BLEED_PX = 32;
const GLOW_BLEED_ALPHA = 42;
const RPM_SMOOTHNESS = 10.0;
const SPEED_SMOOTHNESS = 8.0;
const TICK_LIGHT_WIDTH_RPM = 600;

const THEMES = [
  { name: "Dark Red", tick_contrast: false, BG: [8, 0, 0], RED: [255, 49, 49], RED_MED: [173, 31, 31], RED_DIM: [84, 15, 15], RED_DARK: [20, 3, 3], WHITE: [255, 255, 255], GREY: [150, 150, 150] },
  { name: "Dark Blue", tick_contrast: false, BG: [0, 0, 10], RED: [49, 140, 255], RED_MED: [31, 90, 173], RED_DIM: [15, 40, 84], RED_DARK: [3, 10, 22], WHITE: [255, 255, 255], GREY: [130, 150, 170] },
  { name: "Dark Green", tick_contrast: true, BG: [0, 8, 0], RED: [49, 230, 90], RED_MED: [31, 150, 60], RED_DIM: [15, 70, 25], RED_DARK: [3, 18, 6], WHITE: [255, 255, 255], GREY: [130, 170, 140] },
  { name: "Dark Amber", tick_contrast: false, BG: [8, 4, 0], RED: [255, 160, 0], RED_MED: [180, 100, 0], RED_DIM: [90, 45, 0], RED_DARK: [22, 10, 0], WHITE: [255, 255, 220], GREY: [170, 150, 100] },
  { name: "Dark Purple", tick_contrast: false, BG: [5, 0, 10], RED: [200, 80, 255], RED_MED: [130, 40, 180], RED_DIM: [60, 15, 90], RED_DARK: [15, 3, 22], WHITE: [255, 240, 255], GREY: [160, 130, 180] },
  { name: "Dark Mono", tick_contrast: true, BG: [5, 5, 5], RED: [220, 220, 220], RED_MED: [140, 140, 140], RED_DIM: [60, 60, 60], RED_DARK: [18, 18, 18], WHITE: [255, 255, 255], GREY: [150, 150, 150] },
  { name: "Light Red", tick_contrast: false, BG: [245, 232, 232], RED: [200, 20, 20], RED_MED: [160, 60, 60], RED_DIM: [210, 170, 170], RED_DARK: [232, 215, 215], WHITE: [30, 20, 20], GREY: [110, 80, 80] },
  { name: "Light Blue", tick_contrast: true, BG: [228, 238, 252], RED: [20, 80, 210], RED_MED: [60, 110, 185], RED_DIM: [170, 195, 232], RED_DARK: [212, 223, 243], WHITE: [15, 25, 50], GREY: [75, 100, 135] },
  { name: "Light Green", tick_contrast: false, BG: [228, 248, 233], RED: [20, 170, 55], RED_MED: [50, 130, 75], RED_DIM: [170, 220, 180], RED_DARK: [212, 238, 218], WHITE: [10, 35, 18], GREY: [70, 120, 85] },
  { name: "Light Amber", tick_contrast: true, BG: [252, 244, 225], RED: [190, 110, 0], RED_MED: [200, 150, 50], RED_DIM: [232, 207, 155], RED_DARK: [244, 230, 200], WHITE: [35, 22, 0], GREY: [125, 100, 50] },
  { name: "Light Purple", tick_contrast: true, BG: [240, 230, 252], RED: [150, 30, 210], RED_MED: [170, 80, 200], RED_DIM: [210, 175, 238], RED_DARK: [232, 218, 248], WHITE: [30, 10, 50], GREY: [120, 90, 150] },
  { name: "Light Mono", tick_contrast: true, BG: [240, 240, 240], RED: [40, 40, 40], RED_MED: [100, 100, 100], RED_DIM: [185, 185, 185], RED_DARK: [220, 220, 220], WHITE: [0, 0, 0], GREY: [110, 110, 110] },
];

let themeIndex = 0;
let CURRENT = {};
let TICK_CONTRAST = false;
let menuPolyCache = null;

function applyTheme(idx) {
  themeIndex = ((idx % THEMES.length) + THEMES.length) % THEMES.length;
  CURRENT = THEMES[themeIndex];
  TICK_CONTRAST = CURRENT.tick_contrast;
  menuPolyCache = null;
}
applyTheme(0);

const ARC_CX_O = 788.9;
const ARC_CY_O = 1545.1;
const ARC_R_UPPER = 1483.4;
const ARC_CX_I = 799.4;
const ARC_CY_I = 1609.4;
const ARC_R_LOWER = 1495.2;
const STEPS = 600;
const LINE_W = 3;
const _ARC_ANGLE_AT_ZERO = -122.38;
const _ARC_ANGLE_AT_MAX = -89.5713;
const ARC_A_START = _ARC_ANGLE_AT_ZERO;
const ARC_A_END = _ARC_ANGLE_AT_MAX;

const CIRCLE_CX = -16;
const CIRCLE_CY = 239;
const CIRCLE_R = 262;

const ROW1_Y = 346;
const ROW2_Y = 406;
const STRIP_L = 216;
const VCOL_A = 454;
const VCOL_B = 630;
const VCOL_C = 381;
const VCOL_D = 575;
const TICK_LABEL_R = ARC_R_LOWER + 18;
const UNIT_OFFSET_Y = -4;
const BRIGHTNESS = { value: 1.0 };
const HEX_GRID_SKEW_X = 0;
const ALERT_RECT = { x: 242, y: 316, w: 538, h: 27 };
const ALERT_EDGE_SKEW = 18;
const ALERT_LEVELS = {
  info: { label: "INFO", color: [80, 180, 255] },
  warning: { label: "WARNING", color: [255, 190, 40] },
  serious: { label: "SERIOUS", color: [255, 112, 32] },
  critical: { label: "CRITICAL", color: [255, 49, 49] },
};

const FONTS = {
  speed: '700 italic 162px "RSRobotoBI", Roboto, Arial, sans-serif',
  kmh: 'italic 28px "RSOpenSans", "Open Sans", Arial, sans-serif',
  gearVal: '700 96px "RSOpenSauceOne", Arial, sans-serif',
  gearLbl: '700 italic 25px "RSRobotoBI", Roboto, Arial, sans-serif',
  val: '700 26px "RSOpenSans", "Open Sans", Arial, sans-serif',
  lbl: '400 20px "RSOpenSans", "Open Sans", Arial, sans-serif',
  unit: '400 17px "RSOpenSans", "Open Sans", Arial, sans-serif',
  tick: '700 italic 20px "RSRobotoBI", Roboto, Arial, sans-serif',
  menu: '700 18px "RSOpenSans", "Open Sans", Arial, sans-serif',
  alertLabel: '700 13px "RSOpenSans", "Open Sans", Arial, sans-serif',
  alertText: '700 17px "RSOpenSans", "Open Sans", Arial, sans-serif',
};

class DemoPlayer {
  constructor() {
    this.active = false;
    this.phase = 0;
    this.t = 0.0;
    this.gear_idx = 0;
    this.gears = ["N", "1", "2", "3", "4", "5", "6"];
    this._rpm_at_shift = 0;
    this._spd_at_shift = 0.0;
  }

  start(s) {
    this.active = true;
    this.phase = 0;
    this.t = 0.0;
    this.gear_idx = 0;
    this._rpm_at_shift = 2200;
    this._spd_at_shift = 0.0;
    s.gear = "N";
    s.rpm = DEMO_IDLE_RPM;
    s.speed = 0;
    s.temp = DEMO_BASE_TEMP;
    s.volt = DEMO_BASE_VOLT;
    s.odo = DEMO_ODO_START;
    s.range = 120;
    s.eco = 0;
  }

  _next(s) {
    this.phase += 1;
    this.t = 0.0;
    this._rpm_at_shift = s.rpm;
    this._spd_at_shift = s.speed;
  }

  _lerp(a, b, t) {
    return a + (b - a) * clamp(t, 0.0, 1.0);
  }

  update(s, dt) {
    if (!this.active) return;
    this.t += dt;
    const p = this.phase;

    if (p === 0) {
      s.throttle = 0.0;
      s.rpm = Math.trunc(this._lerp(DEMO_IDLE_RPM, 2200, this.t / 2.0));
      s.temp = this._lerp(DEMO_BASE_TEMP, DEMO_BASE_TEMP + 5, this.t / 2.0);
      if (this.t >= 2.0) this._next(s);
    } else if (p === 1) {
      if (this.t < 0.3) {
        s.throttle = this._lerp(0.0, 0.6, this.t / 0.3);
        s.rpm = Math.trunc(this._lerp(2200, 7000, this.t / 0.3));
      } else {
        s.throttle = this._lerp(0.6, 0.3, (this.t - 0.3) / 0.5);
        s.rpm = Math.trunc(this._lerp(7000, 4200, (this.t - 0.3) / 0.5));
      }
      if (this.t >= 0.8) {
        this.gear_idx = 1;
        s.gear = "1";
        this._next(s);
      }
    } else if ([2, 4, 6, 8, 10, 12].includes(p)) {
      const gear = Math.trunc(p / 2);
      const duration = [0, 3.5, 3.0, 3.0, 3.0, 3.0, 4.0][gear];
      const rpmStart = p === 2 ? 4200 : DEMO_SHIFT_RPM;
      const rpmEnd = DEMO_GEAR_RPMS[gear];
      const spdStarts = [0, 0, 30, 50, 70, 88, 102];
      const spdEnds = [0, 30, 50, 70, 88, 102, DEMO_TOP_SPEED];
      const frac = this.t / duration;
      s.throttle = this._lerp(0.4, 1.0, Math.min(1.0, this.t / 0.4));
      s.rpm = Math.trunc(this._lerp(rpmStart, rpmEnd, frac));
      s.speed = this._lerp(spdStarts[gear], spdEnds[gear], frac);
      s.temp = this._lerp(s.temp, DEMO_HOT_TEMP, dt * 0.3);
      s.volt = DEMO_BASE_VOLT - 0.4 * frac;
      s.odo += s.speed / 3600.0 * dt;
      s.eco = Math.trunc(this._lerp(10, 16, frac));
      s.range = Math.max(0, Math.trunc(120 - (s.odo - DEMO_ODO_START) * 0.9));
      if (this.t >= duration) this._next(s);
    } else if ([3, 5, 7, 9, 11].includes(p)) {
      s.throttle = this.t < 0.15 ? this._lerp(1.0, 0.0, this.t / 0.15) : this._lerp(0.0, 0.4, (this.t - 0.15) / 0.2);
      if (this.t < 0.15) {
        s.rpm = Math.trunc(this._lerp(this._rpm_at_shift, this._rpm_at_shift * 0.5, this.t / 0.15));
      } else {
        s.rpm = Math.trunc(this._lerp(this._rpm_at_shift * 0.5, DEMO_SHIFT_RPM, (this.t - 0.15) / 0.2));
      }
      s.speed = this._spd_at_shift;
      s.odo += s.speed / 3600.0 * dt;
      if (this.t >= 0.35) {
        this.gear_idx += 1;
        s.gear = this.gears[this.gear_idx];
        this._next(s);
      }
    } else if (p === 13) {
      s.throttle = this._lerp(1.0, 0.35, this.t / 3.0);
      s.rpm = Math.trunc(this._lerp(DEMO_GEAR_RPMS[6], 9800, this.t / 3.0));
      s.speed = this._lerp(DEMO_TOP_SPEED, DEMO_TOP_SPEED - 2, this.t / 3.0);
      s.temp = this._lerp(s.temp, DEMO_HOT_TEMP + 3, dt * 0.1);
      s.volt = DEMO_BASE_VOLT - 0.2;
      s.odo += s.speed / 3600.0 * dt;
      s.eco = 9;
      s.range = Math.max(0, Math.trunc(120 - (s.odo - DEMO_ODO_START) * 0.9));
      if (this.t >= 3.0) this._next(s);
    } else if (p === 14) {
      const duration = 12.0;
      const frac = this.t / duration;
      s.throttle = this._lerp(0.35, 0.0, Math.min(1.0, this.t / 0.5));
      s.speed = this._lerp(DEMO_TOP_SPEED - 2, 0, frac);
      s.rpm = Math.trunc(this._lerp(9800, DEMO_IDLE_RPM, frac ** 0.6));
      const expectedGear = Math.max(1, 6 - Math.trunc(frac * 6));
      if (expectedGear !== this.gear_idx) {
        this.gear_idx = expectedGear;
        s.gear = this.gears[this.gear_idx];
      }
      s.temp = this._lerp(s.temp, DEMO_HOT_TEMP - 5, dt * 0.05);
      s.volt = this._lerp(DEMO_BASE_VOLT - 0.2, DEMO_BASE_VOLT, frac);
      s.odo += s.speed / 3600.0 * dt;
      s.eco = Math.trunc(this._lerp(9, 2, frac));
      s.range = Math.max(0, Math.trunc(120 - (s.odo - DEMO_ODO_START) * 0.9));
      if (this.t >= duration) this._next(s);
    } else if (p === 15) {
      s.throttle = 0.0;
      s.speed = 0;
      s.rpm = Math.trunc(this._lerp(DEMO_IDLE_RPM + 200, DEMO_IDLE_RPM, this.t / 2.0));
      s.gear = "N";
      this.gear_idx = 0;
      s.eco = 0;
      if (this.t >= 2.0) this.active = false;
    }
  }
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

function rgb(c) {
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

function rgba(c, a) {
  return `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${clamp(a, 0, 1)})`;
}

function lerpColor(a, b, t) {
  return [
    Math.trunc(a[0] + (b[0] - a[0]) * t),
    Math.trunc(a[1] + (b[1] - a[1]) * t),
    Math.trunc(a[2] + (b[2] - a[2]) * t),
  ];
}

function tickLitColour() {
  if (!TICK_CONTRAST) return CURRENT.WHITE;
  return CURRENT.WHITE.map((c) => 255 - c);
}

function gaugeSeparatorColour(isFilled) {
  return isFilled ? tickLitColour() : CURRENT.RED;
}

function inkForColor(c) {
  const luma = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  return luma > 150 ? [0, 0, 0] : [255, 255, 255];
}

function rad(deg) {
  return deg * Math.PI / 180;
}

function deg(v) {
  return v * 180 / Math.PI;
}

function rpmAngle(rpm) {
  const frac = clamp(rpm / MAX_RPM, 0.0, 1.0);
  return _ARC_ANGLE_AT_ZERO + frac * (_ARC_ANGLE_AT_MAX - _ARC_ANGLE_AT_ZERO);
}

function upperXy(angleDeg) {
  const a = rad(angleDeg);
  return [ARC_CX_O + ARC_R_UPPER * Math.cos(a), ARC_CY_O + ARC_R_UPPER * Math.sin(a)];
}

function lowerXy(angleDeg) {
  const a = rad(angleDeg);
  return [ARC_CX_I + ARC_R_LOWER * Math.cos(a), ARC_CY_I + ARC_R_LOWER * Math.sin(a)];
}

function lowerAngleForX(x) {
  const cosArg = clamp((x - ARC_CX_I) / ARC_R_LOWER, -1.0, 1.0);
  return clamp(deg(-Math.acos(cosArg)), ARC_A_START, ARC_A_END);
}

function arcPts(fn, a0, a1, n) {
  const pts = [];
  for (let i = 0; i <= n; i += 1) pts.push(fn(a0 + i / n * (a1 - a0)));
  return pts;
}

function ipts(pts) {
  return pts.map((p) => [Math.round(p[0]), Math.round(p[1])]);
}

function tickLabelXy(angleDeg) {
  const a = rad(angleDeg);
  return [ARC_CX_I + TICK_LABEL_R * Math.cos(a), ARC_CY_I + TICK_LABEL_R * Math.sin(a)];
}

function fillPolygon(cx, pts, color) {
  if (!pts.length) return;
  cx.beginPath();
  cx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i += 1) cx.lineTo(pts[i][0], pts[i][1]);
  cx.closePath();
  cx.fillStyle = color;
  cx.fill();
}

function strokeLine(cx, p1, p2, color, width) {
  cx.beginPath();
  cx.moveTo(p1[0], p1[1]);
  cx.lineTo(p2[0], p2[1]);
  cx.strokeStyle = color;
  cx.lineWidth = width;
  cx.lineCap = "butt";
  cx.lineJoin = "round";
  cx.miterLimit = 2;
  cx.stroke();
}

function strokePolyline(cx, pts, color, width, closed = false) {
  if (pts.length < 2) return;
  cx.beginPath();
  cx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i += 1) cx.lineTo(pts[i][0], pts[i][1]);
  if (closed) cx.closePath();
  cx.strokeStyle = color;
  cx.lineWidth = width;
  cx.lineCap = "butt";
  cx.lineJoin = "round";
  cx.miterLimit = 2;
  cx.stroke();
}

function fillCircle(cx, x, y, r, color) {
  cx.beginPath();
  cx.arc(x, y, r, 0, Math.PI * 2);
  cx.fillStyle = color;
  cx.fill();
}

function strokeCircle(cx, x, y, r, color, width) {
  cx.beginPath();
  cx.arc(x, y, r, 0, Math.PI * 2);
  cx.strokeStyle = color;
  cx.lineWidth = width;
  cx.stroke();
}

function drawTextTopLeft(cx, text, font, color, x, y) {
  cx.font = font;
  cx.fillStyle = color;
  cx.textAlign = "left";
  cx.textBaseline = "alphabetic";
  const ascent = fontBox(font).ascent;
  cx.fillText(text, x, y + ascent);
}

function drawGlowingTextTopLeft(cx, text, font, color, x, y, glowColor) {
  cx.save();
  cx.shadowColor = rgba(glowColor, 0.72);
  cx.shadowOffsetX = 0;
  cx.shadowOffsetY = 0;
  for (const [blur, alpha] of [[18, 0.38], [9, 0.68], [3, 0.95]]) {
    cx.shadowBlur = blur;
    drawTextTopLeft(cx, text, font, rgba(color, alpha), x, y);
  }
  cx.restore();
  drawTextTopLeft(cx, text, font, rgb(color), x, y);
}

function measureText(cx, text, font) {
  cx.font = font;
  const m = cx.measureText(text);
  const { ascent, descent } = fontBox(font);
  return { width: m.width, height: ascent + descent, ascent, descent };
}

function fontBox(font) {
  const size = parseFontPx(font);
  return { ascent: size * 0.8, descent: size * 0.2 };
}

function parseFontPx(font) {
  const m = font.match(/(\d+(?:\.\d+)?)px/);
  return m ? Number(m[1]) : 20;
}

function fillTextCentered(cx, text, font, color, centerX, centerY) {
  const m = measureText(cx, text, font);
  drawTextTopLeft(cx, text, font, color, centerX - m.width / 2, centerY - m.height / 2);
}

function drawTrackedCentered(cx, text, font, color, centerX, centerY, trackingPx) {
  const metrics = [...text].map((ch) => measureText(cx, ch, font));
  const width = metrics.reduce((sum, m) => sum + m.width, 0) + trackingPx * Math.max(0, text.length - 1);
  const height = metrics.reduce((mx, m) => Math.max(mx, m.height), 0);
  let x = centerX - width / 2;
  const y = centerY - height / 2;
  for (let i = 0; i < text.length; i += 1) {
    drawTextTopLeft(cx, text[i], font, color, x, y);
    x += metrics[i].width + trackingPx;
  }
}

function makeHexGrid() {
  const off = document.createElement("canvas");
  off.width = W;
  off.height = H;
  const cx = off.getContext("2d");
  const R = 27;
  const dx = R * Math.sqrt(3);
  const dy = R * 1.5;
  const skewPadCols = Math.ceil(Math.abs(HEX_GRID_SKEW_X) * H / dx) + 4;
  const brightness = (CURRENT.BG[0] + CURRENT.BG[1] + CURRENT.BG[2]) / 3;
  let fill;
  let outline;
  if (brightness < 128) {
    fill = rgba(CURRENT.RED_DARK, 76 / 255);
    outline = rgba(CURRENT.RED_MED, 84 / 255);
  } else {
    const fillCol = CURRENT.BG.map((c) => clamp(c - 15, 0, 255));
    const outlineCol = CURRENT.BG.map((c) => clamp(c - 30, 0, 255));
    fill = rgba(fillCol, 145 / 255);
    outline = rgba(outlineCol, 165 / 255);
  }
  cx.save();
  cx.setTransform(1, 0, HEX_GRID_SKEW_X, 1, -HEX_GRID_SKEW_X * H / 2, 0);
  for (let row = -1; row < Math.trunc(H / dy) + 4; row += 1) {
    for (let ci = -skewPadCols; ci < Math.trunc(W / dx) + skewPadCols + 4; ci += 1) {
      const hx = ci * dx + (row % 2 ? dx / 2 : 0);
      const hy = row * dy;
      const pts = [];
      for (let i = 0; i < 6; i += 1) {
        pts.push([Math.trunc(hx + R * Math.cos(rad(60 * i - 30))), Math.trunc(hy + R * Math.sin(rad(60 * i - 30)))]);
      }
      fillPolygon(cx, pts, fill);
      cx.beginPath();
      cx.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < pts.length; i += 1) cx.lineTo(pts[i][0], pts[i][1]);
      cx.closePath();
      cx.strokeStyle = outline;
      cx.lineWidth = 1;
      cx.stroke();
    }
  }
  cx.restore();
  return off;
}

function drawArcBand(cx, rpm) {
  const tickLit = tickLitColour();
  const upperAll = arcPts(upperXy, ARC_A_START, ARC_A_END, STEPS);
  const lowerAll = arcPts(lowerXy, ARC_A_START, ARC_A_END, STEPS);

  fillPolygon(cx, upperAll.concat([...lowerAll].reverse()), rgb(CURRENT.RED_DARK));

  const targetAngle = rpmAngle(rpm);
  let barEdgeX = null;
  let rgbBase = CURRENT.RED;
  if (targetAngle > ARC_A_START + 1e-6) {
    const spanFrac = (targetAngle - ARC_A_START) / Math.max(1e-6, ARC_A_END - ARC_A_START);
    const nPts = Math.max(3, Math.ceil(STEPS * spanFrac));
    const upperLit = arcPts(upperXy, ARC_A_START, targetAngle, nPts);
    const edgeUp = upperXy(targetAngle);
    const lowerCapAngle = targetAngle >= ARC_A_END - 1e-6 ? targetAngle : lowerAngleForX(edgeUp[0]);
    const lowerLit = arcPts(lowerXy, ARC_A_START, Math.min(targetAngle, lowerCapAngle), nPts);
    const edgeLo = lowerLit[lowerLit.length - 1];
    fillPolygon(cx, upperLit.concat([edgeLo], [...lowerLit].reverse()), rgb(rgbBase));
    barEdgeX = edgeUp[0];
  }

  const upLast = upperAll[upperAll.length - 1];
  const loLast = lowerAll[lowerAll.length - 1];
  fillPolygon(cx, [upLast, loLast, [W, loLast[1]], [W, upLast[1]]], rgb(CURRENT.RED_DARK));

  const tGlow = clamp(rpm / 1000.0, 0.0, 1.0) * THROTTLE_GLOW_SCALE;
  const glowPx = GLOW_BLEED_PX * tGlow;
  const glowAlpha = GLOW_BLEED_ALPHA * tGlow;
  const outlineFade = TICK_LIGHT_WIDTH_RPM * tGlow;

  if (barEdgeX !== null && glowPx > 0) {
    const angleRange = ARC_A_END - ARC_A_START;
    const stepAngle = angleRange / STEPS;
    const glowAngularSpan = glowPx / ARC_R_UPPER * (180 / Math.PI);
    const nGlow = Math.max(2, Math.trunc(glowAngularSpan / stepAngle));
    for (let gi = 0; gi < nGlow; gi += 1) {
      const tG = gi / Math.max(1, nGlow - 1);
      const alpha = Math.trunc(Math.min(255, glowAlpha) * clamp(1.0 - tG, 0.0, 1.0) ** 2);
      if (alpha <= 0) continue;
      let a0 = targetAngle + gi * stepAngle;
      let a1 = targetAngle + (gi + 1) * stepAngle;
      if (a1 > ARC_A_END) a1 = ARC_A_END;
      fillPolygon(cx, [upperXy(a0), upperXy(a1), lowerXy(a1), lowerXy(a0)], rgba(rgbBase, alpha / 255));
    }
  }

  const barFrac = rpm / MAX_RPM;
  const fadeFrac = outlineFade / MAX_RPM;
  function outlineCol(xFrac) {
    if (tGlow <= 0) return null;
    const dist = xFrac - barFrac;
    if (dist <= 0) return CURRENT.WHITE.map((c) => clamp(Math.trunc(c * tGlow), 1, 255));
    if (dist <= fadeFrac) {
      const t = clamp(dist / fadeFrac, 0.0, 1.0);
      return CURRENT.WHITE.map((w, c) => clamp(Math.trunc((w + (CURRENT.RED[c] - w) * t) * tGlow), 1, 255));
    }
    return null;
  }

  strokePolyline(cx, upperAll, rgb(CURRENT.RED), LINE_W);
  strokeLine(cx, upLast, [W, upLast[1]], rgb(CURRENT.RED_DARK), LINE_W);

  strokePolyline(cx, lowerAll, rgb(CURRENT.RED), Math.max(1, LINE_W - 1));
  strokeLine(cx, loLast, [W, loLast[1]], rgb(CURRENT.RED_DARK), Math.max(1, LINE_W - 1));

  for (let i = 0; i < upperAll.length - 1; i += 1) {
    const col = outlineCol(i / Math.max(1, upperAll.length - 2));
    if (col) strokeLine(cx, upperAll[i], upperAll[i + 1], rgb(col), LINE_W);
  }
  for (let i = 0; i < lowerAll.length - 1; i += 1) {
    const col = outlineCol(i / Math.max(1, lowerAll.length - 2));
    if (col) strokeLine(cx, lowerAll[i], lowerAll[i + 1], rgb(col), Math.max(1, LINE_W - 1));
  }

  const tickRpms = [2000, 4000, 6000, 8000, 10000];
  const tickW = Math.max(1, Math.trunc(LINE_W / 2));
  for (const tr of tickRpms) {
    const a = rpmAngle(tr);
    const up = upperXy(a);
    const lo = lowerXy(a);
    const thickness = Math.hypot(up[0] - lo[0], up[1] - lo[1]);
    const outLen = Math.trunc(Math.round(Math.max(4.0, (thickness + 6.0) * 0.5)));
    const x0 = Math.round(lo[0]);
    const y0 = Math.round(lo[1]);
    const t = clamp((rpm - tr + TICK_LIGHT_WIDTH_RPM) / (2 * TICK_LIGHT_WIDTH_RPM), 0.0, 1.0);
    const col = lerpColor(CURRENT.RED, tickLit, t);
    strokeLine(cx, [x0, y0], [x0, y0 - outLen], rgb(col), tickW);
  }

  const majorRpms = new Set(tickRpms);
  for (let tr = 500; tr < MAX_RPM; tr += 500) {
    if (majorRpms.has(tr)) continue;
    const lo = lowerXy(rpmAngle(tr));
    const x0 = Math.round(lo[0]);
    const y0 = Math.round(lo[1]);
    const outLen = tr % 1000 === 0 ? 18 : 10;
    const t = clamp((rpm - tr + TICK_LIGHT_WIDTH_RPM) / (2 * TICK_LIGHT_WIDTH_RPM), 0.0, 1.0);
    const col = lerpColor(CURRENT.RED, tickLit, t);
    strokeLine(cx, [x0, y0], [x0, y0 - outLen], rgb(col), 1);
  }
}

function drawTicks(cx, rpm) {
  const tickLit = tickLitColour();
  for (const [tr, lbl] of [[2000, "2"], [4000, "4"], [6000, "6"], [8000, "8"], [10000, "10"]]) {
    const pt = tickLabelXy(rpmAngle(tr));
    const [gx, gy] = TICK_LABEL_GLOBAL_OFFSET;
    const [ox, oy] = TICK_LABEL_OVERRIDES[tr] || [0, 0];
    const x = pt[0] + gx + ox;
    const y = pt[1] + gy + oy;
    const t = clamp((rpm - tr + TICK_LIGHT_WIDTH_RPM) / (2 * TICK_LIGHT_WIDTH_RPM), 0.0, 1.0);
    fillTextCentered(cx, lbl, FONTS.tick, rgb(lerpColor(CURRENT.RED, tickLit, t)), x, y);
  }
}

function loadIcon(filename, targetH) {
  if (!window.RS125_LOAD_OPTIONAL_ICONS) return Promise.resolve(null);
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const scale = targetH / img.naturalHeight;
      resolve({ img, w: Math.trunc(img.naturalWidth * scale), h: targetH });
    };
    img.onerror = () => resolve(null);
    img.src = filename;
  });
}

function drawStrip(cx, s, iconTemp, iconBatt) {
  const cy1 = (ROW1_Y + ROW2_Y) / 2;
  const cy2 = (ROW2_Y + H) / 2;

  cx.fillStyle = rgb(CURRENT.BG);
  cx.fillRect(170, ROW1_Y, W - 170, ROW2_Y - ROW1_Y);
  cx.fillRect(0, ROW2_Y, W, H - ROW2_Y);

  strokeLine(cx, [STRIP_L, ROW1_Y], [W, ROW1_Y], rgb(CURRENT.RED), LINE_W);
  strokeLine(cx, [0, ROW2_Y], [W, ROW2_Y], rgb(CURRENT.RED), LINE_W);
  strokeLine(cx, [VCOL_A, ROW1_Y], [VCOL_A, ROW2_Y], rgb(CURRENT.RED), LINE_W);
  strokeLine(cx, [VCOL_B, ROW1_Y], [VCOL_B, ROW2_Y], rgb(CURRENT.RED), LINE_W);
  strokeLine(cx, [VCOL_C, ROW2_Y], [VCOL_C, H], rgb(CURRENT.RED), LINE_W);
  strokeLine(cx, [VCOL_D, ROW2_Y], [VCOL_D, H], rgb(CURRENT.RED), LINE_W);

  function cell(label, val, unit, centerX, centerY, unitOffsetY = 0) {
    const sl = measureText(cx, label, FONTS.lbl);
    const sv = measureText(cx, val, FONTS.val);
    const su = unit ? measureText(cx, unit, FONTS.unit) : null;
    const gap = 8;
    let wTotal = sl.width + gap + sv.width;
    if (su) wTotal += 5 + su.width;
    let x = Math.trunc(centerX - wTotal / 2);
    drawTextTopLeft(cx, label, FONTS.lbl, rgb(CURRENT.GREY), x, Math.trunc(centerY - sl.height / 2));
    x += sl.width + gap;
    drawTextTopLeft(cx, val, FONTS.val, rgb(CURRENT.WHITE), x, Math.trunc(centerY - sv.height / 2));
    if (su) drawTextTopLeft(cx, unit, FONTS.unit, rgb(CURRENT.GREY), x + sv.width + 5, Math.trunc(centerY + sv.height / 2 - su.height) + unitOffsetY);
  }

  function iconCell(icon, val, unit, centerX, centerY, unitOffsetY = 0) {
    const sv = measureText(cx, val, FONTS.val);
    const su = unit ? measureText(cx, unit, FONTS.unit) : null;
    const iw = icon ? icon.w : 0;
    const ih = icon ? icon.h : 0;
    const gap = 8;
    let wTotal = iw + gap + sv.width;
    if (su) wTotal += 5 + su.width;
    let x = Math.trunc(centerX - wTotal / 2);
    if (icon) {
      cx.drawImage(icon.img, x, Math.trunc(centerY - ih / 2), iw, ih);
      x += iw + gap;
    }
    drawTextTopLeft(cx, val, FONTS.val, rgb(CURRENT.WHITE), x, Math.trunc(centerY - sv.height / 2));
    if (su) drawTextTopLeft(cx, unit, FONTS.unit, rgb(CURRENT.GREY), x + sv.width + 5, Math.trunc(centerY + sv.height / 2 - su.height) + unitOffsetY);
  }

  cell("ODO", Number(s.odo).toFixed(2), "km", (STRIP_L + VCOL_A) / 2, cy1, UNIT_OFFSET_Y);
  if (iconTemp) iconCell(iconTemp, String(Math.trunc(s.temp)), "°C", (VCOL_A + VCOL_B) / 2, cy1, UNIT_OFFSET_Y - 1);
  else cell("TEMP", String(Math.trunc(s.temp)), "°C", (VCOL_A + VCOL_B) / 2, cy1, UNIT_OFFSET_Y);
  if (iconBatt) iconCell(iconBatt, Number(s.volt).toFixed(1), "V", (VCOL_B + W) / 2, cy1, UNIT_OFFSET_Y);
  else cell("VOLT", Number(s.volt).toFixed(1), "V", (VCOL_B + W) / 2, cy1, UNIT_OFFSET_Y);

  cell("RANGE", String(s.range), "km", (STRIP_L + VCOL_C) / 2, cy2, UNIT_OFFSET_Y);
  cell("ECO", String(s.eco), "L/100km", (VCOL_C + VCOL_D) / 2, cy2, UNIT_OFFSET_Y);
  fillTextCentered(cx, s.time, FONTS.val, rgb(CURRENT.WHITE), (VCOL_D + W) / 2, cy2);
}

function drawSpeed(cx, speed, blinkOn = false) {
  const speedText = String(Math.trunc(speed));
  const unitText = "km/h";
  const s = measureText(cx, speedText, FONTS.speed);
  const u = measureText(cx, unitText, FONTS.kmh);
  const spdX = 683 - s.width;
  const spdY = 233 - Math.trunc(s.height / 2);
  const kmhX = 682;
  const kmhY = 271 - Math.trunc(u.height / 2);
  const spdCx = spdX + Math.trunc(s.width / 2);
  const spdCy = 233;
  const kmhCx = kmhX + u.width / 2;
  const kmhCy = 271;

  let spdCol = CURRENT.WHITE;
  let kmhCol = CURRENT.GREY;
  if (blinkOn) {
    const warningRed = [255, 49, 49];
    drawGlowingTextTopLeft(cx, speedText, FONTS.speed, warningRed, spdX, spdY, warningRed);
    drawGlowingTextTopLeft(cx, unitText, FONTS.kmh, warningRed, kmhX, kmhY, warningRed);
    return;
  }
  drawTextTopLeft(cx, speedText, FONTS.speed, rgb(spdCol), spdX, spdY);
  drawTextTopLeft(cx, unitText, FONTS.kmh, rgb(kmhCol), kmhX, kmhY);
}

function drawAlert(cx, alert) {
  if (!alert || !alert.message) return;
  const level = ALERT_LEVELS[alert.level] || ALERT_LEVELS.info;
  const r = ALERT_RECT;
  const pts = [
    [r.x + ALERT_EDGE_SKEW, r.y],
    [r.x + r.w, r.y],
    [r.x + r.w - 8, r.y + r.h],
    [r.x, r.y + r.h],
  ];
  const bgLuma = (CURRENT.BG[0] + CURRENT.BG[1] + CURRENT.BG[2]) / 3;
  const panelBg = bgLuma < 128 ? rgba(CURRENT.BG.map((c) => clamp(c + 10, 0, 255)), 0.92) : rgba(CURRENT.BG.map((c) => clamp(c - 14, 0, 255)), 0.92);
  const accent = level.color;

  fillPolygon(cx, pts, panelBg);
  strokePolyline(cx, pts, rgba(accent, 0.9), 1.5, true);
  fillPolygon(cx, [[r.x + ALERT_EDGE_SKEW, r.y], [r.x + 88, r.y], [r.x + 72, r.y + r.h], [r.x, r.y + r.h]], rgba(accent, 0.95));

  cx.save();
  cx.beginPath();
  cx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i += 1) cx.lineTo(pts[i][0], pts[i][1]);
  cx.closePath();
  cx.clip();
  fillTextCentered(cx, level.label, FONTS.alertLabel, rgb(inkForColor(accent)), r.x + 43, r.y + r.h / 2);
  const textX = r.x + 104;
  const maxTextW = r.w - 124;
  const rawMsg = String(alert.message).toUpperCase();
  let msg = rawMsg;
  let msgLen = rawMsg.length;
  cx.font = FONTS.alertText;
  while (msgLen > 1 && cx.measureText(msg).width > maxTextW) {
    msgLen -= 1;
    msg = `${rawMsg.slice(0, msgLen)}...`;
  }
  drawTextTopLeft(cx, msg, FONTS.alertText, rgb(CURRENT.WHITE), textX, r.y + 5);
  cx.restore();
}

function drawGear(cx, gear) {
  fillTextCentered(cx, "GEAR", FONTS.gearLbl, rgb(CURRENT.WHITE), 86, 57);
  const col = gear === "N" ? CURRENT.RED : CURRENT.WHITE;
  fillTextCentered(cx, gear, FONTS.gearVal, rgb(col), 86, 127);
}

function menuPolygon() {
  const cx = ARC_CX_I;
  const cy = ARC_CY_I;
  const rInner = ARC_R_LOWER + MENU_SEPARATION;
  const gcx = CIRCLE_CX;
  const gcy = CIRCLE_CY;
  const rGear = CIRCLE_R + MENU_CIRCLE_SEPARATION;

  function pivot(angleDeg) {
    const a = rad(angleDeg);
    return [cx + rInner * Math.cos(a), cy + rInner * Math.sin(a)];
  }

  function circleIntersection(c1, r1, c2, r2) {
    const dx = c2[0] - c1[0];
    const dy = c2[1] - c1[1];
    const d = Math.hypot(dx, dy);
    const a = (r1 * r1 - r2 * r2 + d * d) / (2 * d);
    const h = Math.sqrt(Math.max(0.0, r1 * r1 - a * a));
    const xm = c1[0] + a * dx / d;
    const ym = c1[1] + a * dy / d;
    const rx = -dy / d;
    const ry = dx / d;
    return [[xm + h * rx, ym + h * ry], [xm - h * rx, ym - h * ry]];
  }

  function arc(center, r, a0, a1, n = 24) {
    const pts = [];
    for (let i = 0; i <= n; i += 1) {
      const a = rad(a0 + (a1 - a0) * i / n);
      pts.push([center[0] + r * Math.cos(a), center[1] + r * Math.sin(a)]);
    }
    return pts;
  }

  const vTop = pivot(MENU_ARC_ANGLE_TOP);
  const approxBot = pivot(MENU_ARC_ANGLE_BOT);
  const [p1, p2] = circleIntersection([cx, cy], rInner, [gcx, gcy], rGear);
  const vJoin = Math.hypot(p1[0] - approxBot[0], p1[1] - approxBot[1]) < Math.hypot(p2[0] - approxBot[0], p2[1] - approxBot[1]) ? p1 : p2;
  const aJoinArc = deg(Math.atan2(vJoin[1] - cy, vJoin[0] - cx));
  const aJoinGear = deg(Math.atan2(vJoin[1] - gcy, vJoin[0] - gcx));
  const aV3 = aJoinGear - MENU_CIRCLE_SWEEP;
  const v3 = [gcx + rGear * Math.cos(rad(aV3)), gcy + rGear * Math.sin(rad(aV3))];

  function closingArc(pa, pb, r) {
    const mx = (pa[0] + pb[0]) / 2;
    const my = (pa[1] + pb[1]) / 2;
    const ddx = pb[0] - pa[0];
    const ddy = pb[1] - pa[1];
    const d = Math.hypot(ddx, ddy);
    const h = Math.sqrt(Math.max(0.0, r * r - (d / 2) ** 2));
    const px = -ddy / d;
    const py = ddx / d;
    const c1 = [mx + h * px, my + h * py];
    const c2 = [mx - h * px, my - h * py];
    const d1 = Math.hypot(c1[0] - cx, c1[1] - cy);
    const d2 = Math.hypot(c2[0] - cx, c2[1] - cy);
    const oc = d1 < d2 ? c1 : c2;
    const a1 = Math.atan2(pa[1] - oc[1], pa[0] - oc[0]);
    const a2 = Math.atan2(pb[1] - oc[1], pb[0] - oc[0]);
    let da = a2 - a1;
    if (da > Math.PI) da -= 2 * Math.PI;
    if (da < -Math.PI) da += 2 * Math.PI;
    const pts = [];
    for (let i = 0; i <= 24; i += 1) pts.push([oc[0] + r * Math.cos(a1 + da * i / 24), oc[1] + r * Math.sin(a1 + da * i / 24)]);
    return pts;
  }

  return ipts(arc([cx, cy], rInner, MENU_ARC_ANGLE_TOP, aJoinArc).concat(arc([gcx, gcy], rGear, aJoinGear, aV3), closingArc(v3, vTop, MENU_OUTER_ARC_R)));
}

function getMenuPoly() {
  if (!menuPolyCache) menuPolyCache = menuPolygon();
  return menuPolyCache;
}

function pointInPoly(px, py, poly) {
  let inside = false;
  let j = poly.length - 1;
  for (let i = 0; i < poly.length; i += 1) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if ((yi > py) !== (yj > py) && px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi) inside = !inside;
    j = i;
  }
  return inside;
}

function drawMenuButton(cx, mousePos = null) {
  const poly = getMenuPoly();
  if (!poly.length) return;
  const hovered = mousePos ? pointInPoly(mousePos[0], mousePos[1], poly) : false;
  fillPolygon(cx, poly, rgb(hovered ? CURRENT.RED_MED : CURRENT.RED_DARK));
  for (let i = 0; i < poly.length; i += 1) strokeLine(cx, poly[i], poly[(i + 1) % poly.length], rgb(hovered ? CURRENT.RED : CURRENT.RED_MED), 1);
  const xs = poly.map((p) => p[0]);
  const ys = poly.map((p) => p[1]);
  drawTrackedCentered(cx, "MENU", FONTS.menu, rgb(CURRENT.WHITE), (Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2 - 2, 3);
}

function drawMenuScreen(cx, menuState) {
  cx.fillStyle = rgb(CURRENT.BG);
  cx.fillRect(0, 0, W, H);
  strokeLine(cx, [0, 60], [W, 60], rgb(CURRENT.RED), 2);
  fillTextCentered(cx, "SETTINGS", FONTS.val, rgb(CURRENT.WHITE), W / 2, 31);

  const backR = { x: 16, y: 14, w: 72, h: 32 };
  roundRect(cx, backR, rgb(CURRENT.RED_DARK), rgb(CURRENT.RED), 1, 4);
  fillTextCentered(cx, "< BACK", FONTS.lbl, rgb(CURRENT.WHITE), backR.x + backR.w / 2, backR.y + backR.h / 2);
  menuState._backBtn = backR;

  const secY = 90;
  drawTextTopLeft(cx, "THEME", FONTS.val, rgb(CURRENT.RED), 40, secY);
  strokeLine(cx, [40, secY + 30], [W - 40, secY + 30], rgb(CURRENT.RED_DIM), 1);

  const arrowL = { x: 40, y: secY + 44, w: 48, h: 48 };
  const arrowR = { x: 712, y: secY + 44, w: 48, h: 48 };
  for (const [r, ch] of [[arrowL, "<"], [arrowR, ">"]]) {
    roundRect(cx, r, rgb(CURRENT.RED_MED), rgb(CURRENT.RED), 2, 6);
    fillTextCentered(cx, ch, FONTS.val, rgb(CURRENT.WHITE), r.x + r.w / 2, r.y + r.h / 2);
  }

  fillTextCentered(cx, THEMES[themeIndex].name, FONTS.val, rgb(CURRENT.WHITE), W / 2, secY + 69);
  const n = THEMES.length;
  const dotTotal = n * 14;
  const dotX0 = W / 2 - Math.trunc(dotTotal / 2);
  for (let i = 0; i < n; i += 1) fillCircle(cx, dotX0 + i * 14 + 7, secY + 108, 4, rgb(i === themeIndex ? CURRENT.RED : CURRENT.RED_DIM));
  menuState._arrowL = arrowL;
  menuState._arrowR = arrowR;

  const previewY = secY + 122;
  const previewH = 28;
  const previewCols = [CURRENT.RED_DARK, CURRENT.RED_DIM, CURRENT.RED_MED, CURRENT.RED, CURRENT.WHITE];
  const segW = Math.trunc((W - 80) / previewCols.length);
  for (let i = 0; i < previewCols.length; i += 1) {
    cx.fillStyle = rgb(previewCols[i]);
    cx.fillRect(40 + i * segW, previewY, segW, previewH);
  }
  cx.strokeStyle = rgb(CURRENT.RED);
  cx.lineWidth = 1;
  cx.strokeRect(40, previewY, segW * previewCols.length, previewH);

  const brY = 290;
  drawTextTopLeft(cx, "BRIGHTNESS", FONTS.val, rgb(CURRENT.RED), 40, brY);
  strokeLine(cx, [40, brY + 30], [W - 40, brY + 30], rgb(CURRENT.RED_DIM), 1);
  const bar = { x: 40, y: brY + 54, w: W - 80, h: 16 };
  roundRect(cx, bar, rgb(CURRENT.RED_DARK), rgb(CURRENT.RED_DIM), 1, 8);
  const fillW = Math.max(8, Math.trunc(bar.w * BRIGHTNESS.value));
  roundRect(cx, { x: bar.x, y: bar.y, w: fillW, h: bar.h }, rgb(CURRENT.RED), null, 0, 8);
  const knobX = bar.x + fillW;
  fillCircle(cx, knobX, bar.y + bar.h / 2, 14, rgb(CURRENT.WHITE));
  strokeCircle(cx, knobX, bar.y + bar.h / 2, 14, rgb(CURRENT.RED), 2);
  fillTextCentered(cx, `${Math.trunc(BRIGHTNESS.value * 100)}%`, FONTS.val, rgb(CURRENT.WHITE), W / 2, bar.y + 39);

  menuState._brightBar = bar;
  menuState._brightKnobCx = knobX;
  menuState._brightKnobCy = bar.y + bar.h / 2;
  for (const pct of [0.25, 0.5, 0.75]) {
    const tx = Math.trunc(bar.x + bar.w * pct);
    strokeLine(cx, [tx, bar.y + bar.h + 2], [tx, bar.y + bar.h + 8], rgb(CURRENT.RED_MED), 1);
  }
  strokeLine(cx, [0, H - 36], [W, H - 36], rgb(CURRENT.RED_DIM), 1);
}

function roundRect(cx, r, fill, stroke, strokeWidth = 1, radius = 4) {
  cx.beginPath();
  cx.roundRect(r.x, r.y, r.w, r.h, radius);
  if (fill) {
    cx.fillStyle = fill;
    cx.fill();
  }
  if (stroke) {
    cx.strokeStyle = stroke;
    cx.lineWidth = strokeWidth;
    cx.stroke();
  }
}

function drawFuelGauge(cx, fuel) {
  const GEAR_CX = CIRCLE_CX;
  const GEAR_CY = CIRCLE_CY;
  const GEAR_R = CIRCLE_R;
  const LINE_TOP_ANGLE = 0.0;
  const LINE_TOP_DIR = -23.0;
  const LINE_TOP_DIST = 15;
  const LINE_TOP_LEN = 75;
  const LINE_BOT_ANGLE = 65.0;
  const LINE_BOT_DIR = 65.0;
  const LINE_BOT_DIST = 15;
  const LINE_BOT_LEN = 35;
  const BAND_SPACING = 35;
  const LEFT_ARC_R = GEAR_R;
  const SEP_EXTEND = 0.75;
  const SEP_W = 1.25;
  const N_SEG = 6;
  const STEPS_ARC = 40;

  function ptOnCircle(r, aDeg) {
    const a = rad(aDeg);
    return [GEAR_CX + r * Math.cos(a), GEAR_CY + r * Math.sin(a)];
  }
  function ptAlong(origin, aDeg, length) {
    const a = rad(aDeg);
    return [origin[0] - length * Math.cos(a), origin[1] - length * Math.sin(a)];
  }
  function ipt(p) {
    return [p[0], p[1]];
  }
  function leftArcCentre(p1, p2, r) {
    const mx = (p1[0] + p2[0]) / 2;
    const my = (p1[1] + p2[1]) / 2;
    const dx = p2[0] - p1[0];
    const dy = p2[1] - p1[1];
    const d = Math.hypot(dx, dy);
    const h = Math.sqrt(Math.max(0.0, r * r - (d / 2) ** 2));
    const px = -dy / d;
    const py = dx / d;
    const c1 = [mx + h * px, my + h * py];
    const c2 = [mx - h * px, my - h * py];
    return c1[0] < c2[0] ? c1 : c2;
  }
  function leftArcPts(p1, p2, r) {
    const [cx2, cy2] = leftArcCentre(p1, p2, r);
    const a1 = Math.atan2(p1[1] - cy2, p1[0] - cx2);
    const a2 = Math.atan2(p2[1] - cy2, p2[0] - cx2);
    let da = a2 - a1;
    if (da > Math.PI) da -= 2 * Math.PI;
    if (da < -Math.PI) da += 2 * Math.PI;
    const pts = [];
    for (let s = 0; s <= 60; s += 1) pts.push([cx2 + r * Math.cos(a1 + da * s / 60), cy2 + r * Math.sin(a1 + da * s / 60)]);
    return pts;
  }
  function drawLeftArc(p1, p2, r, col, width) {
    strokePolyline(cx, leftArcPts(p1, p2, r), col, width);
  }
  function sampleArc(pts, frac) {
    if (pts.length < 2) return pts[0];
    const idx = frac * (pts.length - 1);
    const i = Math.trunc(idx);
    const t = idx - i;
    if (i >= pts.length - 1) return pts[pts.length - 1];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    return [p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t];
  }

  const rRight = GEAR_R - LINE_TOP_DIST;
  const rRightInner = rRight - BAND_SPACING;
  const topRightOuter = ptOnCircle(rRight, LINE_TOP_ANGLE);
  const topRightInner = ptOnCircle(rRightInner, LINE_TOP_ANGLE);
  const topLeftOuter = ptAlong(topRightOuter, LINE_TOP_DIR, LINE_TOP_LEN);
  const topLeftInner = ptAlong(topRightInner, LINE_TOP_DIR, LINE_TOP_LEN - BAND_SPACING);
  const botRightOuter = ptOnCircle(rRight, LINE_BOT_ANGLE);
  const botRightInner = ptOnCircle(rRightInner, LINE_BOT_ANGLE);
  const botLeftOuter = ptAlong(botRightOuter, LINE_BOT_DIR, LINE_BOT_LEN);
  const botLeftInner = ptAlong(botRightInner, LINE_BOT_DIR, LINE_BOT_LEN - BAND_SPACING);

  fuel = clamp(fuel, 0.0, 1.0);
  const lowFuelThreshold = 1 / N_SEG;
  const low = fuel > 0 && fuel < lowFuelThreshold;
  const nLit = fuel <= 0 ? 0 : Math.ceil(fuel * N_SEG - 1e-9);
  const outerLeftPts = leftArcPts(botLeftOuter, topLeftOuter, LEFT_ARC_R);
  const segs = [];
  for (let i = 0; i < N_SEG; i += 1) {
    const fracLo = i / N_SEG;
    const fracHi = (i + 1) / N_SEG;
    const aLo = LINE_BOT_ANGLE + fracLo * (LINE_TOP_ANGLE - LINE_BOT_ANGLE);
    const aHi = LINE_BOT_ANGLE + fracHi * (LINE_TOP_ANGLE - LINE_BOT_ANGLE);
    segs.push([ipt(ptOnCircle(rRight, aLo)), ipt(ptOnCircle(rRight, aHi)), sampleArc(outerLeftPts, fracLo), sampleArc(outerLeftPts, fracHi)]);
  }

  for (let i = 0; i < segs.length; i += 1) {
    const [roLo, roHi, loLo, loHi] = segs[i];
    const col = low && i < nLit ? [255, 49, 49] : i < nLit ? CURRENT.RED : CURRENT.RED_DARK;
    fillPolygon(cx, [roLo, roHi, loHi, loLo], rgb(col));
  }

  const rightArcPts = [];
  for (let i = 0; i <= STEPS_ARC; i += 1) {
    const a = LINE_BOT_ANGLE + i / STEPS_ARC * (LINE_TOP_ANGLE - LINE_BOT_ANGLE);
    rightArcPts.push(ptOnCircle(rRight, a));
  }

  strokePolyline(cx, rightArcPts, rgb(CURRENT.RED), LINE_W);
  strokeLine(cx, ipt(topRightOuter), ipt(topLeftOuter), rgb(CURRENT.RED), LINE_W);
  strokeLine(cx, ipt(botRightOuter), ipt(botLeftOuter), rgb(CURRENT.RED), LINE_W);
  drawLeftArc(topLeftOuter, botLeftOuter, LEFT_ARC_R, rgb(CURRENT.RED), LINE_W);

  for (let i = 0; i < segs.length; i += 1) {
    if (i === 0) continue;
    const [roLo,, loLo] = segs[i];
    const divOnFilledArea = i < nLit;
    const divCol = low && i === nLit ? [255, 49, 49] : gaugeSeparatorColour(divOnFilledArea);
    const dx = loLo[0] - roLo[0];
    const dy = loLo[1] - roLo[1];
    const d = Math.hypot(dx, dy);
    let p1 = roLo;
    let p2 = loLo;
    if (d > 0) {
      const ex = SEP_EXTEND * dx / d;
      const ey = SEP_EXTEND * dy / d;
      p1 = [roLo[0] - ex, roLo[1] - ey];
      p2 = [loLo[0] + ex, loLo[1] + ey];
    }
    strokeLine(cx, p1, p2, rgb(divCol), SEP_W);
  }

  const fPos = sampleArc(outerLeftPts, 1.0);
  const ePos = sampleArc(outerLeftPts, 0.0);
  const fM = measureText(cx, "F", FONTS.tick);
  const eM = measureText(cx, "E", FONTS.tick);
  drawTextTopLeft(cx, "F", FONTS.tick, rgb(CURRENT.WHITE), fPos[0] - fM.width - 15, fPos[1] - fM.height + 30);
  drawTextTopLeft(cx, "E", FONTS.tick, rgb(CURRENT.WHITE), ePos[0] - eM.width + 5, ePos[1] - eM.height - 15);
}

const state = {
  rpm: 4500,
  speed: 45,
  gear: "N",
  temp: 14,
  volt: 12.4,
  odo: 1234.56,
  range: 95,
  eco: 95,
  time: "19:22",
  throttle: 0.0,
  fuel: 1.0,
  alert: null,
  _rebuildHex: false,
};
const gears = ["N", "1", "2", "3", "4", "5", "6"];
const demo = new DemoPlayer();
const menuState = { open: false, sel: 0, dragBright: false };
let canvas;
let ctx;
let hexGrid = null;
let iconTemp = null;
let iconBatt = null;
let gi = 0;
let blinkT = 0.0;
let dispRpm = state.rpm;
let dispSpeed = state.speed;
let odoMode = 0;
let ecoImperial = false;
let tripA = 0.0;
let tripB = 0.0;
let lastFrameTime = null;
let ws = null;

function rectContains(r, x, y) {
  return x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h;
}

function rectInflateContains(r, dx, dy, x, y) {
  const ix = r.x - dx / 2;
  const iy = r.y - dy / 2;
  const iw = r.w + dx;
  const ih = r.h + dy;
  return x >= ix && x < ix + iw && y >= iy && y < iy + ih;
}

function handleClick(mx, my) {
  if (menuState.open) {
    if (menuState._backBtn && rectContains(menuState._backBtn, mx, my)) {
      menuState.open = false;
    } else if (menuState._arrowL && rectContains(menuState._arrowL, mx, my)) {
      applyTheme(themeIndex - 1);
      state._rebuildHex = true;
    } else if (menuState._arrowR && rectContains(menuState._arrowR, mx, my)) {
      applyTheme(themeIndex + 1);
      state._rebuildHex = true;
    } else if (menuState._brightBar) {
      const bar = menuState._brightBar;
      const knobCx = menuState._brightKnobCx !== undefined ? menuState._brightKnobCx : bar.x;
      const knobCy = menuState._brightKnobCy !== undefined ? menuState._brightKnobCy : bar.y + bar.h / 2;
      if (Math.hypot(mx - knobCx, my - knobCy) < 20) {
        menuState.dragBright = true;
      } else if (rectInflateContains(bar, 0, 24, mx, my)) {
        BRIGHTNESS.value = clamp((mx - bar.x) / bar.w, 0.05, 1.0);
      }
    }
  } else {
    if (mx < 170 && my > 57 && my < 200) {
      if (!demo.active) {
        gi = (gi + 1) % gears.length;
        state.gear = gears[gi];
      }
    } else if (mx > STRIP_L && mx < VCOL_A && my > ROW1_Y && my < ROW2_Y) {
      odoMode = (odoMode + 1) % 3;
    } else if (mx > VCOL_C && mx < VCOL_D && my > ROW2_Y && my < H) {
      ecoImperial = !ecoImperial;
    }
  }
}

function handleKeyDown(k) {
  if (k === "q" || k === "Escape") {
    if (menuState.open) menuState.open = false;
  } else if (!demo.active && !menuState.open) {
    if (k === "ArrowUp") state.rpm = Math.min(MAX_RPM, state.rpm + 500);
    else if (k === "ArrowDown") state.rpm = Math.max(0, state.rpm - 500);
    else if (k === "w") state.speed = Math.min(200, state.speed + 5);
    else if (k === "s") state.speed = Math.max(0, state.speed - 5);
    else if (k === "ArrowRight") { gi = Math.min(gears.length - 1, gi + 1); state.gear = gears[gi]; }
    else if (k === "ArrowLeft") { gi = Math.max(0, gi - 1); state.gear = gears[gi]; }
    else if (k === "t") state.temp = Math.max(-20, state.temp - 1);
    else if (k === "y") state.temp = Math.min(120, state.temp + 1);
    else if (k === "b") state.volt = Math.max(10.0, Math.round((state.volt - 0.1) * 10) / 10);
    else if (k === "n") state.volt = Math.min(15.0, Math.round((state.volt + 0.1) * 10) / 10);
  }
}

function connectWebSocket() {
  try {
    ws = new WebSocket("ws://localhost:8765");
    ws.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data);
        Object.assign(state, payload);
        syncControls();
      } catch (_) {
        // Ignore malformed frames from experimental senders.
      }
    };
    ws.onclose = () => { setTimeout(connectWebSocket, 2000); };
    ws.onerror = () => { ws.close(); };
  } catch (_) {
    // Dev controls remain available without a local data server.
  }
}

function frame(now) {
  if (lastFrameTime === null) lastFrameTime = now;
  const dt = Math.min(0.25, (now - lastFrameTime) / 1000.0);
  lastFrameTime = now;

  state.time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
  if (state._rebuildHex) {
    hexGrid = makeHexGrid();
    state._rebuildHex = false;
  }

  demo.update(state, dt);

  const alphaRpm = dt > 0 ? 1.0 - Math.exp(-RPM_SMOOTHNESS * dt) : 1.0;
  const alphaSpeed = dt > 0 ? 1.0 - Math.exp(-SPEED_SMOOTHNESS * dt) : 1.0;
  dispRpm += (state.rpm - dispRpm) * alphaRpm;
  dispSpeed += (state.speed - dispSpeed) * alphaSpeed;
  if (dispRpm < 50) dispRpm = 0.0;

  blinkT += dt;
  const blinkOn = dispRpm >= REDLINE_RPM && Math.trunc(blinkT * 6) % 2 === 0;

  if (!menuState.open) {
    tripA += state.speed / 3600.0 * dt;
    tripB += state.speed / 3600.0 * dt;
  }

  const odoLabels = ["ODO", "TRIP A", "TRIP B"];
  const odoValues = [Number(state.odo).toFixed(2), tripA.toFixed(2), tripB.toFixed(2)];
  state._odoLabel = odoLabels[odoMode];
  state._odoValue = odoValues[odoMode];
  if (ecoImperial) {
    const mpg = state.eco > 0 ? 282.5 / state.eco : 0;
    state._ecoValue = mpg.toFixed(1);
    state._ecoUnit = "mpg";
  } else {
    state._ecoValue = String(state.eco);
    state._ecoUnit = "L/100km";
  }

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = rgb(CURRENT.BG);
  ctx.fillRect(0, 0, W, H);
  if (hexGrid) ctx.drawImage(hexGrid, 0, 0);

  if (menuState.open) {
    drawMenuScreen(ctx, menuState);
  } else {
    drawStrip(ctx, state, iconTemp, iconBatt);
    fillCircle(ctx, CIRCLE_CX, CIRCLE_CY, CIRCLE_R, rgb(CURRENT.BG));
    strokeCircle(ctx, CIRCLE_CX, CIRCLE_CY, CIRCLE_R, rgb(CURRENT.RED), LINE_W);
    drawArcBand(ctx, dispRpm);
    drawTicks(ctx, dispRpm);
    drawSpeed(ctx, dispSpeed, blinkOn);
    drawAlert(ctx, state.alert);
    drawFuelGauge(ctx, state.fuel);
    drawGear(ctx, state.gear);
    if (BRIGHTNESS.value < 1.0) {
      ctx.fillStyle = `rgba(0, 0, 0, ${Math.trunc((1.0 - BRIGHTNESS.value) * 255) / 255})`;
      ctx.fillRect(0, 0, W, H);
    }
  }

  requestAnimationFrame(frame);
}

function toCanvasXY(ev) {
  const r = canvas.getBoundingClientRect();
  return [((ev.clientX - r.left) / r.width) * W, ((ev.clientY - r.top) / r.height) * H];
}

function buildDevControls() {
  const bindings = [
    ["rpm", (v) => { state.rpm = Math.trunc(Number(v)); }],
    ["speed", (v) => { state.speed = Math.trunc(Number(v)); }],
    ["temp", (v) => { state.temp = Math.trunc(Number(v)); }],
    ["volt", (v) => { state.volt = Math.round(Number(v) * 10) / 10; }],
    ["eco", (v) => { state.eco = Math.trunc(Number(v)); }],
    ["range", (v) => { state.range = Math.trunc(Number(v)); }],
    ["throttle", (v) => { state.throttle = Math.round(Number(v) * 100) / 100; }],
    ["fuel", (v) => { state.fuel = Math.round(Number(v) * 100) / 100; }],
  ];
  for (const [id, setter] of bindings) {
    const el = document.getElementById(id);
    if (!el) continue;
    el.addEventListener("input", () => {
      if (id !== "fuel" && id !== "throttle") demo.active = false;
      setter(el.value);
    });
  }
  document.getElementById("demoBtn")?.addEventListener("click", () => demo.start(state));
  document.getElementById("themeBtn")?.addEventListener("click", () => {
    applyTheme(themeIndex + 1);
    state._rebuildHex = true;
  });
  document.getElementById("menuBtn")?.addEventListener("click", () => {
    menuState.open = !menuState.open;
  });
  document.getElementById("sendAlertBtn")?.addEventListener("click", () => {
    const levelEl = document.getElementById("alertLevel");
    const msgEl = document.getElementById("alertMessage");
    const level = ALERT_LEVELS[levelEl?.value] ? levelEl.value : "info";
    const message = String(msgEl?.value || "").trim();
    state.alert = message ? { level, message } : null;
  });
  document.getElementById("clearAlertBtn")?.addEventListener("click", () => {
    state.alert = null;
  });
}

function syncControls() {
  for (const id of ["rpm", "speed", "temp", "volt", "eco", "range", "throttle", "fuel"]) {
    const el = document.getElementById(id);
    if (el && state[id] !== undefined) el.value = String(state[id]);
  }
}

async function init() {
  canvas = document.getElementById("dash");
  ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = true;

  if (document.fonts) await document.fonts.ready;
  hexGrid = makeHexGrid();
  iconTemp = await loadIcon("../icon_temp.png", 30);
  iconBatt = await loadIcon("../icon_batt.png", 30);

  canvas.addEventListener("mousedown", (ev) => {
    const [mx, my] = toCanvasXY(ev);
    handleClick(mx, my);
  });
  window.addEventListener("mouseup", () => { menuState.dragBright = false; });
  canvas.addEventListener("mousemove", (ev) => {
    if (!menuState.dragBright) return;
    const [mx] = toCanvasXY(ev);
    const bar = menuState._brightBar;
    if (bar) BRIGHTNESS.value = clamp((mx - bar.x) / bar.w, 0.05, 1.0);
  });
  window.addEventListener("keydown", (ev) => handleKeyDown(ev.key));

  buildDevControls();
  connectWebSocket();
  requestAnimationFrame(frame);
}

window.addEventListener("DOMContentLoaded", init);

window.RS125 = {
  state,
  demo,
  BRIGHTNESS,
  THEMES,
  menuState,
  applyTheme(i) {
    applyTheme(i);
    state._rebuildHex = true;
  },
  setAlert(level, message) {
    state.alert = message ? { level: ALERT_LEVELS[level] ? level : "info", message: String(message) } : null;
  },
  clearAlert() {
    state.alert = null;
  },
  get themeIndex() {
    return themeIndex;
  },
  toggleMenu() {
    menuState.open = !menuState.open;
  },
};
