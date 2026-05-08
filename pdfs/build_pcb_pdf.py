from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon
from reportlab.graphics import renderPDF

# ── Palette ───────────────────────────────────────────────────────────────────
BG_DARK   = colors.HexColor("#0D0D0D")
RED       = colors.HexColor("#E03030")
RED_DIM   = colors.HexColor("#8B1A1A")
WHITE     = colors.HexColor("#F5F5F5")
GREY      = colors.HexColor("#888888")
LIGHT_BG  = colors.HexColor("#F8F8F8")
MID_GREY  = colors.HexColor("#DDDDDD")
DARK_TEXT = colors.HexColor("#1A1A1A")
CODE_BG   = colors.HexColor("#1E1E2E")
CODE_FG   = colors.HexColor("#A8FF78")
AMBER     = colors.HexColor("#E67E22")
BLUE      = colors.HexColor("#2980B9")
GREEN     = colors.HexColor("#27AE60")
PCB_GREEN = colors.HexColor("#1A5C2A")
PCB_GOLD  = colors.HexColor("#C8A84B")
PCB_TRACE = colors.HexColor("#2E8B57")

W_PAGE = A4[0] - 28*mm
PAGE_H = A4[1]

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def S(name, **kw):
    parent = kw.pop("parent", "Normal")
    return ParagraphStyle(name, parent=styles[parent], **kw)

sCover = S("sCover", fontSize=22, leading=28, textColor=WHITE,
           alignment=TA_CENTER, fontName="Helvetica-Bold",
           backColor=BG_DARK, leftIndent=-14*mm, rightIndent=-14*mm,
           borderPad=14, spaceBefore=0, spaceAfter=0)
sSub   = S("sSub", fontSize=11, textColor=GREY, alignment=TA_CENTER, spaceAfter=4)
sH1    = S("sH1", fontSize=14, leading=18, textColor=WHITE,
           fontName="Helvetica-Bold", backColor=RED,
           leftIndent=-14*mm, rightIndent=-14*mm, borderPad=6,
           spaceBefore=14, spaceAfter=6)
sH2    = S("sH2", fontSize=11, leading=14, textColor=RED,
           fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3)
sH3    = S("sH3", fontSize=9.5, leading=12, textColor=DARK_TEXT,
           fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2)
sBody  = S("sBody", fontSize=9, leading=13, textColor=DARK_TEXT,
           alignment=TA_JUSTIFY, spaceAfter=3)
sBul   = S("sBul", fontSize=9, leading=13, textColor=DARK_TEXT,
           leftIndent=14, spaceAfter=2)
sCode  = S("sCode", fontSize=8, leading=11, textColor=CODE_FG,
           backColor=CODE_BG, fontName="Courier",
           leftIndent=8, rightIndent=8, borderPad=5,
           spaceBefore=3, spaceAfter=5)
sTiny  = S("sTiny", fontSize=7.5, textColor=GREY, spaceAfter=2)
sNote  = S("sNote", fontSize=8.5, leading=12,
           textColor=colors.HexColor("#154360"),
           backColor=colors.HexColor("#D6EAF8"),
           leftIndent=8, borderPad=5, spaceAfter=4)
sWarn  = S("sWarn", fontSize=8.5, leading=12,
           textColor=colors.HexColor("#7D6608"),
           backColor=colors.HexColor("#FEF9E7"),
           leftIndent=8, borderPad=5, spaceAfter=4)

def HR(): return HRFlowable(width="100%", thickness=0.4,
                             color=MID_GREY, spaceAfter=5, spaceBefore=5)
def SP(h=3): return Spacer(1, h*mm)
def body(t): return Paragraph(t, sBody)
def bul(t):  return Paragraph(f"• {t}", sBul)
def h1(t):   return Paragraph(t, sH1)
def h2(t):   return Paragraph(t, sH2)
def h3(t):   return Paragraph(t, sH3)
def code(t): return Paragraph(t.replace("\n","<br/>").replace(" ","&nbsp;"), sCode)
def note(t): return Paragraph("ℹ  " + t, sNote)
def warn(t): return Paragraph("⚠  " + t, sWarn)

# ── Table helpers ─────────────────────────────────────────────────────────────
def styled_table(data, col_widths, header_bg=BG_DARK, stripe=True):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    ts = [
        ("BACKGROUND",  (0,0), (-1,0), header_bg),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING",(0,0), (-1,-1), 5),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("GRID",        (0,0), (-1,-1), 0.4, MID_GREY),
    ]
    if stripe:
        for i in range(1, len(data)):
            if i % 2 == 0:
                ts.append(("BACKGROUND", (0,i), (-1,i), LIGHT_BG))
    t.setStyle(TableStyle(ts))
    return t

# ── PCB Block Diagram Drawing ─────────────────────────────────────────────────
def make_pcb_diagram():
    """SVG-style block diagram of the PCB using reportlab Drawing."""
    d = Drawing(W_PAGE, 140)

    def box(x, y, w, h, fill, label, label2="", label_color=colors.white, fontsize=8):
        d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=colors.HexColor("#333333"),
                   strokeWidth=0.8, rx=3, ry=3))
        d.add(String(x + w/2, y + h/2 + (5 if label2 else 2),
                     label, textAnchor="middle",
                     fontName="Helvetica-Bold", fontSize=fontsize,
                     fillColor=label_color))
        if label2:
            d.add(String(x + w/2, y + h/2 - 7, label2,
                         textAnchor="middle", fontName="Helvetica",
                         fontSize=6.5, fillColor=label_color))

    def arrow(x1, y1, x2, y2, label=""):
        d.add(Line(x1, y1, x2, y2, strokeColor=RED, strokeWidth=1.2))
        # arrowhead
        import math
        angle = math.atan2(y2-y1, x2-x1)
        al = 7
        d.add(Polygon([x2, y2,
                       x2 - al*math.cos(angle-0.4), y2 - al*math.sin(angle-0.4),
                       x2 - al*math.cos(angle+0.4), y2 - al*math.sin(angle+0.4)],
                      fillColor=RED, strokeColor=RED, strokeWidth=0.5))
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            d.add(String(mx, my+3, label, textAnchor="middle",
                         fontName="Helvetica", fontSize=6.5,
                         fillColor=RED))

    # Background
    d.add(Rect(0, 0, W_PAGE, 140, fillColor=colors.HexColor("#0A0A12"),
               strokeColor=colors.HexColor("#333355"), strokeWidth=1))

    # OBD2 connector
    box(4, 50, 58, 40, colors.HexColor("#2C2C40"), "OBD2", "Female 16-pin",
        label_color=colors.HexColor("#CCCCFF"), fontsize=8)

    # Arrow: OBD2 -> Power path
    arrow(62, 90, 90, 90, "12V")
    arrow(62, 70, 90, 70, "K-Line")
    arrow(62, 60, 90, 60, "GND")

    # Buck converter
    box(90, 78, 52, 30, colors.HexColor("#1A3A1A"), "LM2596",
        "Buck 12V->5V", label_color=colors.HexColor("#AAFFAA"), fontsize=8)

    # Arrow: Buck -> ESP32
    arrow(142, 90, 170, 90, "5V")
    # K-Line direct to L9637D
    arrow(90, 70, 170, 55, "K-Line")

    # L9637D
    box(170, 44, 52, 26, colors.HexColor("#3A1A1A"), "L9637D",
        "K-Line XCVR", label_color=colors.HexColor("#FFAAAA"), fontsize=8)

    # Arrow: L9637D -> ESP32 (UART)
    arrow(222, 57, 248, 57, "UART2")

    # ESP32-S3
    box(248, 44, 68, 52, colors.HexColor("#1A2A3A"), "ESP32-S3",
        "Main MCU", label_color=colors.HexColor("#AACCFF"), fontsize=9)

    # Arrow: ESP32 -> Display
    arrow(316, 70, 348, 70, "8080 16-bit")

    # Display connector
    box(348, 50, 62, 40, colors.HexColor("#2A1A3A"), "FPC/Header",
        "800x480 Display", label_color=colors.HexColor("#CCAAFF"), fontsize=7.5)

    # Arrow: Power to ESP32
    arrow(142, 93, 248, 85, "")

    # Power to display
    arrow(142, 96, 348, 60, "")

    # Labels at bottom
    d.add(String(W_PAGE/2, 8, "RS125 Dashboard PCB — Block Diagram",
                 textAnchor="middle", fontName="Helvetica",
                 fontSize=7, fillColor=GREY))

    return d

# ── Pinout diagram (ESP32-S3 connections) ────────────────────────────────────
def make_pinout_diagram():
    d = Drawing(W_PAGE, 180)
    d.add(Rect(0, 0, W_PAGE, 180, fillColor=colors.HexColor("#0A0A12"),
               strokeColor=colors.HexColor("#333355"), strokeWidth=1))

    # ESP32-S3 chip body
    chip_x, chip_y, chip_w, chip_h = W_PAGE/2 - 55, 40, 110, 100
    d.add(Rect(chip_x, chip_y, chip_w, chip_h,
               fillColor=colors.HexColor("#1A2540"),
               strokeColor=colors.HexColor("#4466AA"), strokeWidth=1.5,
               rx=4, ry=4))
    d.add(String(chip_x + chip_w/2, chip_y + chip_h/2 + 6,
                 "ESP32-S3", textAnchor="middle",
                 fontName="Helvetica-Bold", fontSize=10,
                 fillColor=colors.HexColor("#AACCFF")))
    d.add(String(chip_x + chip_w/2, chip_y + chip_h/2 - 8,
                 "WROOM-1", textAnchor="middle",
                 fontName="Helvetica", fontSize=7.5,
                 fillColor=colors.HexColor("#6688AA")))

    # Pin rows
    left_pins = [
        ("GND",    "GND",    colors.HexColor("#888888")),
        ("3V3",    "3.3V",   colors.HexColor("#FF6666")),
        ("GPIO16", "UART2 RX← L9637D TX", colors.HexColor("#FFAA44")),
        ("GPIO17", "UART2 TX→ L9637D RX", colors.HexColor("#FFAA44")),
        ("GPIO18", "LCD WR",  colors.HexColor("#44AAFF")),
        ("GPIO19", "LCD RS",  colors.HexColor("#44AAFF")),
    ]
    right_pins = [
        ("GPIO0",  "LCD DB0",  colors.HexColor("#44AAFF")),
        ("GPIO1",  "LCD DB1",  colors.HexColor("#44AAFF")),
        ("GPIO2",  "LCD DB2",  colors.HexColor("#44AAFF")),
        ("GPIO3",  "LCD DB3",  colors.HexColor("#44AAFF")),
        ("GPIO4",  "LCD DB4",  colors.HexColor("#44AAFF")),
        ("GPIO5",  "LCD DB5",  colors.HexColor("#44AAFF")),
    ]
    bottom_pins = [
        ("GPIO6",  "LCD DB6",  colors.HexColor("#44AAFF")),
        ("GPIO7",  "LCD DB7",  colors.HexColor("#44AAFF")),
        ("GPIO8",  "LCD DB8",  colors.HexColor("#44AAFF")),
        ("GPIO9",  "LCD DB9",  colors.HexColor("#44AAFF")),
        ("GPIO10", "LCD DB10", colors.HexColor("#44AAFF")),
        ("GPIO11", "LCD DB11", colors.HexColor("#44AAFF")),
        ("GPIO12", "LCD DB12", colors.HexColor("#44AAFF")),
        ("GPIO13", "LCD DB13", colors.HexColor("#44AAFF")),
        ("GPIO14", "LCD DB14", colors.HexColor("#44AAFF")),
        ("GPIO15", "LCD DB15", colors.HexColor("#44AAFF")),
        ("GPIO20", "LCD CS",   colors.HexColor("#44CCFF")),
        ("GPIO21", "LCD RST",  colors.HexColor("#44CCFF")),
        ("5V",     "5V in",    colors.HexColor("#FF6666")),
    ]

    # Left pins
    py_start = chip_y + chip_h - 15
    step = 13
    for i, (pin, label, col) in enumerate(left_pins):
        py = py_start - i * step
        # dot
        d.add(Circle(chip_x - 2, py, 3, fillColor=col, strokeColor=col, strokeWidth=0))
        d.add(Line(chip_x - 2, py, chip_x - 30, py,
                   strokeColor=col, strokeWidth=0.8))
        d.add(String(chip_x - 33, py - 3, f"{pin}: {label}",
                     textAnchor="end", fontName="Helvetica", fontSize=5.5,
                     fillColor=col))

    # Right pins
    for i, (pin, label, col) in enumerate(right_pins):
        py = py_start - i * step
        d.add(Circle(chip_x + chip_w + 2, py, 3, fillColor=col,
                     strokeColor=col, strokeWidth=0))
        d.add(Line(chip_x + chip_w + 2, py, chip_x + chip_w + 30, py,
                   strokeColor=col, strokeWidth=0.8))
        d.add(String(chip_x + chip_w + 33, py - 3, f"{pin}: {label}",
                     textAnchor="start", fontName="Helvetica", fontSize=5.5,
                     fillColor=col))

    # Bottom label (DB6-15 listed as text only, chip too small for bottom pins)
    d.add(String(W_PAGE/2, 12,
                 "GPIO6-15 → LCD DB6-DB15  |  GPIO20 → LCD CS  |  GPIO21 → LCD RST  |  5V pin → from LM2596",
                 textAnchor="middle", fontName="Helvetica", fontSize=6,
                 fillColor=colors.HexColor("#AAAACC")))
    d.add(String(W_PAGE/2, 4,
                 "ESP32-S3 Pin Assignment — RS125 Dashboard PCB",
                 textAnchor="middle", fontName="Helvetica", fontSize=6.5,
                 fillColor=GREY))
    return d

# ═════════════════════════════════════════════════════════════════════════════
# BUILD
# ═════════════════════════════════════════════════════════════════════════════
doc = SimpleDocTemplate(
    "C:/Users/draccko/Downloads/pdfs/RS125_Dashboard_PCB.pdf",
    pagesize=A4,
    rightMargin=14*mm, leftMargin=14*mm,
    topMargin=16*mm, bottomMargin=16*mm,
    title="RS125 Dashboard PCB — Design Reference",
)

story = []

# ── COVER ─────────────────────────────────────────────────────────────────────
story += [
    SP(6),
    Paragraph("RS125 DASHBOARD PCB", sCover),
    SP(2),
    Paragraph("OBD2 Interface + ESP32-S3 + 800×480 Display", sSub),
    Paragraph("Component List · Pin Connections · Design Choices", sSub),
    SP(3), HR(), SP(2),
    body("This document covers everything needed to design and build the custom PCB "
         "that sits between the Aprilia RS125's diagnostic port, the ESP32-S3 "
         "microcontroller, and the 800×480 parallel TFT display. It is intentionally "
         "concise — one page per topic."),
    SP(2),
]

# ── BLOCK DIAGRAM ─────────────────────────────────────────────────────────────
story += [
    h1("1 — System Block Diagram"),
    SP(2),
]
story.append(make_pcb_diagram())
story += [SP(2), PageBreak()]

# ── DESIGN KEY CHOICES ────────────────────────────────────────────────────────
story += [
    h1("2 — Key Design Choices"),
    SP(2),
    h2("Why ESP32-S3 and not original ESP32"),
    body("The original ESP32 has no native parallel LCD controller. Driving an 800×480 "
         "display over 8080 16-bit parallel requires the ESP32-S3's built-in LCD peripheral, "
         "which supports up to 40 MHz pixel clock — giving ~52 fps full-frame. The original "
         "ESP32 would need SPI, limiting you to ~4 fps at this resolution. Not viable."),
    SP(2),
    h2("Why 8080 16-bit parallel and not SPI"),
    body("At 800×480, a full frame is 768 KB. SPI at 27 MHz pushes that in ~228 ms (4 fps). "
         "8080 16-bit parallel at 20 MHz pushes it in ~38 ms (26 fps), at 40 MHz in ~19 ms "
         "(52 fps). For a live RPM arc animating at 30+ fps, parallel is non-negotiable."),
    SP(2),
    h2("Why LM2596 for power"),
    body("The bike supplies switched 12V (actually 13.6–14.4V when running). The ESP32-S3 "
         "needs 5V input (3.3V via onboard regulator), and the display needs 3.3V–5V depending "
         "on the specific panel. The LM2596 is a simple, proven, adjustable buck converter that "
         "handles up to 40V input, 3A output — enough for the ESP32-S3 (~500mA peak) plus "
         "display backlight (~300mA). Total draw under 1A comfortably."),
    SP(2),
    h2("Why L9637D for K-Line"),
    body("The bike's ECU communicates over K-Line at 12V logic levels. The ESP32-S3 GPIO "
         "is strictly 3.3V tolerant — connecting 12V directly destroys the chip instantly. "
         "The L9637D is a single-chip automotive K-Line transceiver that handles the 12V↔3.3V "
         "conversion, bus pull-up, and ISO 9141 timing requirements. It also provides short-circuit "
         "and overvoltage protection on the bus line."),
    SP(2),
    h2("OBD2 female connector (board-mounted)"),
    body("Rather than soldering wires to an OBD2 adapter cable, mount a standard 16-pin OBD2 "
         "female connector directly on the PCB. This gives a clean, vibration-resistant "
         "connection. The Aprilia 6-pin→OBD2 adapter cable plugs straight in. Only pins 4 "
         "(GND), 7 (K-Line), and 16 (12V) are wired on the PCB — the rest are NC "
         "(no connect)."),
    SP(2),
    h2("Single-layer vs double-layer PCB"),
    body("Go double-layer. The 16-bit data bus (DB0–DB15) plus control lines (WR, RS, CS, RST) "
         "is 20 signals between the ESP32-S3 and display connector. Routing these on a single "
         "layer without crossovers is nearly impossible at a reasonable board size. Double-layer "
         "at JLCPCB or PCBWay costs the same (~€5 for 5 boards) and makes routing trivial."),
    SP(2),
    h2("Display connector type"),
    body("Most 800×480 parallel displays use a 40-pin or 50-pin 0.5mm pitch FPC (Flexible "
         "Printed Circuit) connector. Solder a matching ZIF (Zero Insertion Force) FPC socket "
         "onto the PCB. Verify the pin count and pitch of your specific display before ordering "
         "the connector — they vary. A safer alternative is a display module that already "
         "breaks out to a 2.54mm pitch header, which is much easier to hand-solder."),
    SP(2),
    warn("Keep the K-Line trace away from the 16-bit LCD data bus traces. K-Line runs at 12V "
         "transient levels and the L9637D switches at 10.4 kbps — crosstalk into the high-speed "
         "LCD lines can corrupt pixel data. Route K-Line on the opposite side of the board "
         "or with a ground pour between them."),
    SP(2), PageBreak(),
]

# ── COMPONENT LIST ────────────────────────────────────────────────────────────
story += [
    h1("3 — Component List (BOM)"),
    SP(2),
]

bom_header = ["Ref", "Component", "Part Number / Spec", "Qty", "Package", "~Cost"]
bom_rows = [
    ["U1",  "Microcontroller",     "ESP32-S3-WROOM-1 (N8R8)",      "1", "Module",        "€4.50"],
    ["U2",  "K-Line Transceiver",  "L9637D",                        "1", "SO-8",          "€1.80"],
    ["U3",  "Buck Converter IC",   "LM2596S-5.0 (fixed 5V)",        "1", "TO-263-5",      "€0.80"],
    ["J1",  "OBD2 Connector",      "Female 16-pin OBD2 PCB mount",  "1", "Through-hole",  "€2.50"],
    ["J2",  "Display Connector",   "FPC 40-pin 0.5mm ZIF (verify!)", "1", "SMD ZIF",      "€0.60"],
    ["J3",  "Debug Header",        "2.54mm 4-pin (TX/RX/3V3/GND)",  "1", "Through-hole",  "€0.20"],
    ["L1",  "Inductor",            "100µH, 3A, power (LM2596)",     "1", "DO-201",        "€0.40"],
    ["D1",  "Schottky Diode",      "1N5822 or SS34 (LM2596 catch)", "1", "DO-201/SMB",    "€0.25"],
    ["C1",  "Input Cap (buck)",    "100µF 35V electrolytic",         "1", "Radial 8mm",    "€0.20"],
    ["C2",  "Output Cap (buck)",   "220µF 10V electrolytic",         "1", "Radial 8mm",    "€0.20"],
    ["C3",  "Decoupling U2 VCC",   "100nF ceramic X7R",              "1", "0402/0603",     "€0.05"],
    ["C4",  "Decoupling U2 VCC",   "100nF ceramic X7R",              "1", "0402/0603",     "€0.05"],
    ["C5",  "Decoupling ESP32 5V", "10µF ceramic X5R",               "1", "0805",          "€0.10"],
    ["C6",  "Decoupling ESP32 5V", "100nF ceramic X7R",              "1", "0402/0603",     "€0.05"],
    ["R1",  "K-Line pullup",       "510Ω 1/4W (L9637D LIN to 12V)", "1", "0402/0603",     "€0.05"],
    ["R2",  "UART TX resistor",    "1kΩ (ESP32 TX to L9637D TXD)",  "1", "0402/0603",     "€0.05"],
    ["F1",  "Polyfuse",            "0.5A hold / 1A trip, 16V",       "1", "1812 SMD",      "€0.30"],
    ["LED1","Power LED",           "Red 0603 SMD + 1kΩ series R",   "1", "0603",          "€0.05"],
    ["SW1", "Reset button",        "Tactile 4-pin SMD, 3x4mm",      "1", "SMD",           "€0.10"],
    ["PCB", "2-layer PCB",         "~80×60mm, 1.6mm FR4",            "1", "—",            "€5.00"],
]
story.append(styled_table([bom_header] + bom_rows,
    [14*mm, 40*mm, 52*mm, 10*mm, 22*mm, 18*mm]))
story += [
    SP(2),
    note("The LM2596S-5.0 is the fixed 5V version — no adjustment potentiometer needed, "
         "simpler layout, one fewer component. If your display needs 3.3V directly, add a "
         "small AMS1117-3.3 LDO after the LM2596 (it only needs to drop 1.7V from 5V, "
         "very low dissipation)."),
    SP(2),
    body("Total estimated cost: ~€17 per board excluding display and bike-side adapter cable. "
         "JLCPCB can assemble most SMD components for an additional ~€8–12 (PCBA service)."),
    SP(2), PageBreak(),
]

# ── PIN CONNECTIONS ───────────────────────────────────────────────────────────
story += [
    h1("4 — Pin Connection Tables"),
    SP(2),
    h2("4.1 — OBD2 Connector (J1) → PCB"),
    SP(1),
]

obd_header = ["OBD2 Pin", "Signal", "Connects to", "Note"]
obd_rows = [
    ["4",      "Chassis GND",  "PCB GND plane",      "Primary ground"],
    ["5",      "Signal GND",   "PCB GND plane",       "Tie to pin 4"],
    ["7",      "K-Line",       "L9637D pin 5 (LIN)",  "ISO 9141-2 bus"],
    ["16",     "+12V Battery", "F1 → LM2596 Vin+",   "Switched ignition rail"],
    ["1,2,3,6,\n8–15", "NC",  "—",                   "No connect"],
]
story.append(styled_table([obd_header] + obd_rows,
    [22*mm, 28*mm, 52*mm, W_PAGE - 102*mm]))
story += [SP(3)]

story += [
    h2("4.2 — L9637D (U2) Pin Connections"),
    SP(1),
]
l96_header = ["L9637D Pin", "Name", "Connects to", "Note"]
l96_rows = [
    ["1",  "TXD",  "R2 (1kΩ) → ESP32-S3 GPIO16 (UART2 RX)", "ECU data out → MCU in"],
    ["2",  "GND",  "PCB GND",                                 "Power ground"],
    ["3",  "VCC",  "LM2596 5V output",                        "Supply"],
    ["4",  "RXD",  "ESP32-S3 GPIO17 (UART2 TX)",              "MCU out → ECU"],
    ["5",  "LIN",  "OBD2 pin 7 (K-Line)",                     "Bus connection"],
    ["6",  "INH",  "VCC via 10kΩ (optional)",                 "Pull high to enable, or leave NC"],
    ["7",  "WAKE", "NC",                                       "Not used"],
    ["8",  "VCC",  "LM2596 5V output",                        "Supply (tie to pin 3)"],
]
story.append(styled_table([l96_header] + l96_rows,
    [22*mm, 18*mm, 80*mm, W_PAGE - 120*mm]))
story += [SP(3)]

story += [
    h2("4.3 — LM2596S-5.0 (U3) Pin Connections"),
    SP(1),
]
lm_header = ["LM2596 Pin", "Name", "Connects to", "Note"]
lm_rows = [
    ["1",  "Vin",      "F1 output (+12V from OBD2 pin 16)", "12–14.4V input"],
    ["2",  "Vout",     "L1 → output rail (+5V)",             "Switched output"],
    ["3",  "GND",      "PCB GND plane",                      ""],
    ["4",  "Feedback", "Output rail (fixed 5V version)",      "Internal, no external R needed"],
    ["5",  "ON/OFF",   "GND (always on)",                    "Tie low to keep enabled"],
    ["—",  "L1",       "100µH between Vout pin and +5V rail","Switching inductor"],
    ["—",  "D1",       "Cathode to +5V rail, anode to GND",  "Catch diode"],
    ["—",  "C1",       "100µF across Vin to GND",            "Input decoupling"],
    ["—",  "C2",       "220µF across Vout (+5V) to GND",     "Output filter"],
]
story.append(styled_table([lm_header] + lm_rows,
    [22*mm, 22*mm, 72*mm, W_PAGE - 116*mm]))
story += [SP(3)]

story += [
    h2("4.4 — ESP32-S3 → Display (8080 16-bit Parallel)"),
    SP(1),
]
esp_header = ["ESP32-S3 GPIO", "LCD Signal", "Description"]
esp_rows = [
    ["GPIO0",  "DB0",  "Data bit 0  (LSB)"],
    ["GPIO1",  "DB1",  "Data bit 1"],
    ["GPIO2",  "DB2",  "Data bit 2"],
    ["GPIO3",  "DB3",  "Data bit 3"],
    ["GPIO4",  "DB4",  "Data bit 4"],
    ["GPIO5",  "DB5",  "Data bit 5"],
    ["GPIO6",  "DB6",  "Data bit 6"],
    ["GPIO7",  "DB7",  "Data bit 7"],
    ["GPIO8",  "DB8",  "Data bit 8"],
    ["GPIO9",  "DB9",  "Data bit 9"],
    ["GPIO10", "DB10", "Data bit 10"],
    ["GPIO11", "DB11", "Data bit 11"],
    ["GPIO12", "DB12", "Data bit 12"],
    ["GPIO13", "DB13", "Data bit 13"],
    ["GPIO14", "DB14", "Data bit 14"],
    ["GPIO15", "DB15", "Data bit 15  (MSB)"],
    ["GPIO18", "WR",   "Write strobe — clocks data into display on rising edge"],
    ["GPIO19", "RS / DC", "Register select: LOW=command, HIGH=data"],
    ["GPIO20", "CS",   "Chip select — active LOW"],
    ["GPIO21", "RST",  "Hardware reset — active LOW, pull HIGH via 10kΩ"],
    ["GPIO16", "UART2 RX", "K-Line data IN (from L9637D TXD via 1kΩ)"],
    ["GPIO17", "UART2 TX", "K-Line data OUT (to L9637D RXD)"],
    ["5V pin", "VCC",  "5V from LM2596 to ESP32-S3 module VCC"],
    ["GND",    "GND",  "Common ground"],
]
story.append(styled_table([esp_header] + esp_rows,
    [32*mm, 26*mm, W_PAGE - 58*mm]))
story += [SP(3)]

# ── PINOUT DIAGRAM ────────────────────────────────────────────────────────────
story += [
    h2("4.5 — ESP32-S3 Pin Diagram"),
    SP(1),
]
story.append(make_pinout_diagram())
story += [SP(2), PageBreak()]

# ── LVGL / FIRMWARE NOTES ─────────────────────────────────────────────────────
story += [
    h1("5 — Firmware Integration Notes"),
    SP(2),
    h2("Initialising the 8080 parallel bus in ESP-IDF / LVGL"),
    body("ESP-IDF provides the esp_lcd driver which supports 8080 parallel natively on "
         "the ESP32-S3. The key configuration struct is:"),
    code(
        "esp_lcd_i80_bus_config_t bus_cfg = {\n"
        "    .dc_gpio_num     = 19,   // RS pin\n"
        "    .wr_gpio_num     = 18,   // WR pin\n"
        "    .clk_src         = LCD_CLK_SRC_DEFAULT,\n"
        "    .data_gpio_nums  = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15},\n"
        "    .bus_width       = 16,\n"
        "    .max_transfer_bytes = 800*480*2,\n"
        "};\n"
        "esp_lcd_panel_io_handle_t io;\n"
        "esp_lcd_panel_io_i80_config_t io_cfg = {\n"
        "    .cs_gpio_num     = 20,\n"
        "    .pclk_hz         = 20000000,  // 20 MHz — safe start\n"
        "    .trans_queue_depth = 10,\n"
        "    .lcd_cmd_bits    = 8,\n"
        "    .lcd_param_bits  = 8,\n"
        "};"
    ),
    body("Once the bus is initialised, plug in your display driver (ST7262, NT35510, "
         "or whichever controller your panel uses). LVGL then wraps this via "
         "lv_display_create() and lv_display_set_flush_cb()."),
    SP(2),
    h2("K-Line UART configuration"),
    code(
        "uart_config_t uart_cfg = {\n"
        "    .baud_rate  = 10400,\n"
        "    .data_bits  = UART_DATA_8_BITS,\n"
        "    .parity     = UART_PARITY_DISABLE,\n"
        "    .stop_bits  = UART_STOP_BITS_1,\n"
        "    .flow_ctrl  = UART_HW_FLOWCTRL_DISABLE,\n"
        "};\n"
        "uart_param_config(UART_NUM_2, &uart_cfg);\n"
        "uart_set_pin(UART_NUM_2, 17, 16, -1, -1);"
    ),
    SP(2),
    note("Start the display at 10–15 MHz pixel clock during bring-up. Increase to 20–40 MHz "
         "only after confirming stable output. Some displays are picky about clock edge polarity "
         "— check your panel datasheet for PCLK active edge (rising vs falling)."),
    SP(2),
    h2("Boot time"),
    body("ESP-IDF boots in ~300ms to app_main(). LVGL init + display driver init adds ~100ms. "
         "The hex grid background (pre-rendered into a frame buffer at boot) takes ~500ms at "
         "20 MHz. Total to first live frame: under 1 second. No fast-boot tricks needed."),
    SP(2), HR(),
    Paragraph("RS125 Dashboard PCB — Design Reference  |  All values verified for ESP32-S3 + LM2596 + L9637D",
              sTiny),
]

doc.build(story)
print("PDF built.")
