# RS125 TFT Dashboard — ESP32-S3 Firmware

ESP-IDF project driving the 16-bit parallel TFT display connected via U4
on the RS125 dashboard PCB.  Replicates the pygame simulator UI.

---

## Hardware connections (from netlist)

| TFT function | GPIO | U4 pin | Net        |
|--------------|------|--------|------------|
| CS           | 44   | 5      | $1N3956    |
| DC / RS      | 40   | 7, 19  | $1N4137    |
| WR           | 46   | 8      | $1N3815    |
| RD           | 41   | 9, 23  | $1N3881    |
| RST          | 1    | 11, 15 | $1N3887    |
| Backlight    | 2    | —      | Q1 gate    |
| D0           | 8    | 28     | $1N3742    |
| D1           | 16   | 32     | $1N3802    |
| D2           | 38   | 34     | $1N3808    |
| D3           | 3    | 33     | $1N3695    |
| D4           | 4    | 31     | $1N3707    |
| D5           | 5    | 29     | $1N3826    |
| D6           | 6    | 27     | $1N3728    |
| D7           | 7    | 25     | $1N3735    |
| D8           | 15   | 14     | $1N3796    |
| D9           | 39   | 12     | $1N3872    |
| D10          | 14   | 16     | $1N3787    |
| D11          | 13   | 18     | $1N3774    |
| D12          | 12   | 20     | $1N3767    |
| D13          | 11   | 22     | $1N3760    |
| D14          | 10   | 24     | $1N3754    |
| D15          | 9    | 26     | $1N3748    |
| TE/FMARK     | 42   | 39     | $1N3654    |
| +5V          | —    | 6      | power      |
| 3V3          | —    | 38     | power      |
| GND          | —    | 40     | power      |

---

## Prerequisites

- ESP-IDF v5.1 or later
- Python 3.8+ (for idf.py and font conversion)

```bash
. $IDF_PATH/export.sh
```

---

## Build & flash

```bash
cd rs125_dash
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

---

## First run — identify your display controller

Look at the screen PCB silkscreen or markings.  Common options:

- **ST7796S** — most 4.0" 800×480 displays from AliExpress
- **ILI9488** — most 3.5" 480×320 (but some 4" too)

In `lcd_init.c`, the `send_init_cmds(...)` call near the bottom selects the
init sequence.  The ST7796 sequence is active by default; swap the comment
to use ILI9488 if your display shows garbage.

You can also read the display ID at startup:

```c
uint8_t id[4];
esp_lcd_panel_io_rx_param(panel_io, 0x04, id, 4);
ESP_LOGI("ID", "%02x %02x %02x %02x", id[0], id[1], id[2], id[3]);
// ST7796: 00 77 96 xx
// ILI9488: 00 54 88 xx
```

---

## Fonts — making it look identical to the pygame version

The pygame version uses:
- **Roboto Bold Italic** 162 px — speed digits
- **Open Sans Bold** 26 px — strip values
- **Open Sans Regular** 20/17/28 px — labels, units, km/h
- **OpenSauce One Bold** 96 px — gear character
- **OpenSauce One Regular** 25 px — GEAR label

### Step 1 — get the font files

The fonts used in the PDF are embedded subsets.  You need the full TTF:
- Roboto: https://fonts.google.com/specimen/Roboto
- Open Sans: https://fonts.google.com/specimen/Open+Sans
- OpenSauce One: https://github.com/marcologous/OpenSauce-Fonts

### Step 2 — install lv_font_conv

```bash
npm install -g lv_font_conv
```

### Step 3 — convert each font

```bash
# Example: speed digits (only need 0-9 and space)
lv_font_conv \
  --ttf fonts/Roboto-BoldItalic.ttf \
  --size 162 \
  --bpp 4 \
  --format lvgl \
  --range 0x20,0x30-0x39 \
  -o main/font_roboto_bolditalic_162.c

# Strip values
lv_font_conv \
  --ttf fonts/OpenSans-Bold.ttf \
  --size 26 \
  --bpp 4 \
  --format lvgl \
  --range 0x20-0x7E,0xB0 \
  -o main/font_opensans_bold_26.c

# Gear character (needs 0-9, N, space)
lv_font_conv \
  --ttf fonts/OpenSauceOne-Bold.ttf \
  --size 96 \
  --bpp 4 \
  --format lvgl \
  --range 0x20,0x30-0x39,0x4E \
  -o main/font_opensauce_bold_96.c
```

Repeat for each size listed in `fonts_config.h`.

### Step 4 — enable them

In `fonts_config.h`, uncomment the `LV_FONT_DECLARE(...)` lines and remove
the fallback `lv_font_montserrat_*` returns.

Add each generated `.c` file to the `SRCS` list in `main/CMakeLists.txt`.

---

## Screen controller — if yours is different

If the display uses a different controller, check `lcd_init.c` and swap the
`send_init_cmds` call.  The i80 bus configuration (GPIO pins, bus width,
PCLK frequency) stays the same regardless of controller.

---

## Next steps (not yet implemented)

- K-Line / OBD-II reader (U5 L9637 already wired) → `data_task()`
- CAN bus (U6 SN65HVD230 already wired)
- Touch input (if your screen has a touch controller)
- NVS-backed settings persistence (theme, brightness)
- SNTP time sync over WiFi
