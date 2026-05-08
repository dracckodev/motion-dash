#pragma once
// ============================================================
//  RS125 TFT Dashboard — Board Pin Definitions
//  Derived from Netlist_Schematic2_2026-05-07.enet
//  U1 = ESP32-S3-DevKitC-1-N8R8   U4 = 40-pin TFT connector
// ============================================================
//
//  Interface: 16-bit Intel 8080 parallel (i80)
//  Controller: ILI9488 / ST7796 / similar (verify on screen PCB)
//  Resolution: 800 × 480
//
//  How to read this file:
//    Each #define shows  GPIO  (U4 connector pin)  net name
//  ─────────────────────────────────────────────────────────

// ── Control signals ──────────────────────────────────────────
#define TFT_PIN_CS    44   // U4-5   $1N3956   Chip Select  (active low)
#define TFT_PIN_DC    40   // U4-7   $1N4137   Data/Command (RS)
//                         // U4-19  same net  (duplicate pad)
#define TFT_PIN_WR    46   // U4-8   $1N3815   Write strobe (active low)
#define TFT_PIN_RD    41   // U4-9   $1N3881   Read strobe  (active low)
//                         // U4-23  same net  (duplicate pad)
#define TFT_PIN_RST    1   // U4-11  $1N3887   Reset        (active low)
//                         // U4-15  same net  (duplicate pad)

// ── Backlight ────────────────────────────────────────────────
// Routed through R4 (33 Ω), controlled via 2N7002 NMOS (Q1)
// Gate of Q1 driven by LD net.  PWM on this pin = backlight brightness.
// LD net itself appears to be a schematic label — trace to ESP32:
//   U4 pin 4 → LD → R4 → +5V  (R4 is a current-limit / soft-start resistor)
//   The actual PWM GPIO is NOT on U4 pin 4; it's on the Q1 gate.
//   From netlist: Q1 gate = $1N2532 → ESP32 pin 30 = IO2
#define TFT_PIN_BL     2   // IO2  Q1 gate → backlight LED anode via R4

// ── 16-bit data bus (DB0 … DB15) ─────────────────────────────
// Ordered by bit position.  Physical order on connector is scrambled
// (normal for these cheap modules — the PCB re-routes internally).
#define TFT_PIN_D0     8   // U4-28  $1N3742
#define TFT_PIN_D1    16   // U4-32  $1N3802
#define TFT_PIN_D2    38   // U4-34  $1N3808
#define TFT_PIN_D3     3   // U4-33  $1N3695
#define TFT_PIN_D4     4   // U4-31  $1N3707
#define TFT_PIN_D5     5   // U4-29  $1N3826
#define TFT_PIN_D6     6   // U4-27  $1N3728
#define TFT_PIN_D7     7   // U4-25  $1N3735
#define TFT_PIN_D8    15   // U4-14  $1N3796
#define TFT_PIN_D9    39   // U4-12  $1N3872
#define TFT_PIN_D10   14   // U4-16  $1N3787
#define TFT_PIN_D11   13   // U4-18  $1N3774
#define TFT_PIN_D12   12   // U4-20  $1N3767
#define TFT_PIN_D13   11   // U4-22  $1N3760
#define TFT_PIN_D14   10   // U4-24  $1N3754
#define TFT_PIN_D15    9   // U4-26  $1N3748

// ── Tearing Effect (TE/FMARK) ─────────────────────────────────
// Connected but not required for basic operation.
// Useful for vsync-locked frame timing.
#define TFT_PIN_TE    42   // U4-39  $1N3654

// ── Dot clock (only for RGB mode — not used in i80 mode) ──────
#define TFT_PIN_CLK   45   // U4-37  $1N3671

// ── Power rails (for reference — not driven by software) ──────
// U4-6  : +5V  (backlight LED supply)
// U4-38 : 3V3  (logic supply)
// U4-40 : GND

// ── Display parameters ────────────────────────────────────────
#define LCD_H_RES     800
#define LCD_V_RES     480
#define LCD_BIT_WIDTH  16   // parallel bus width

// PCLK for i80: ILI9488/ST7796 supports up to ~33 MHz in 16-bit mode.
// Start conservatively; increase if no glitching.
#define LCD_PCLK_HZ   (20 * 1000 * 1000)

// Double-buffer size in bytes (one full frame = 800*480*2 = 768 kB).
// With 8 MB PSRAM we can afford a full frame buffer.
#define LCD_DRAW_BUFF_SIZE  (LCD_H_RES * LCD_V_RES)  // pixels (2 bytes each)
