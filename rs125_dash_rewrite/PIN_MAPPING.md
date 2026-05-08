# GPIO Pin Mapping — RS125 Dash

Decoded from netlist by matching U4 (TFT connector) nets → U1 (ESP32-S3-DevKit-N8R8) pins → GPIOs.
**Verify every entry against your physical PCB before flashing.**

## Display — SSD1963 16-bit 8080 parallel

| Signal | GPIO    | U4 Pin | Net        | Notes                        |
|--------|---------|--------|------------|------------------------------|
| D0     | GPIO15  | 26     | $1N3748    |                              |
| D1     | GPIO16  | 24     | $1N3754    |                              |
| D2     | GPIO17  | 22     | $1N3760    |                              |
| D3     | GPIO18  | 20     | $1N3767    |                              |
| D4     | GPIO19  | 18     | $1N3774    | ⚠ shared USB D- on some modules |
| D5     | GPIO20  | 16     | $1N3787    |                              |
| D6     | GPIO46  | 11/15  | $1N3887    | shared on two U4 pins        |
| D7     | GPIO9   | 9/23   | $1N3881    | shared on two U4 pins        |
| D8     | GPIO13  | 28     | $1N3742    |                              |
| D9     | GPIO14  | 8      | $1N3815    |                              |
| D10    | GPIO12  | 33     | $1N3695    |                              |
| D11    | GPIO7   | 34     | $1N3808    |                              |
| D12    | GPIO11  | 35     | $1N3684    | ⚠ strapping pin — confirm    |
| D13    | GPIO10  | 37     | $1N3671    |                              |
| D14    | GPIO5   | 39     | $1N3654    |                              |
| D15    | GPIO6   | 27     | $1N3728    |                              |
| CS     | GPIO3   | 5      | $1N3956    | ⚠ JTAG on some configs       |
| RS/DC  | GPIO4   | 7      | $1N4137    |                              |
| WR     | GPIO2   | 21     | $1N3965    |                              |
| RD     | GPIO48  | —      | spare      | hold HIGH; not traced in netlist |
| RST    | GPIO40  | 29     | $1N3826    |                              |
| BL PWM | GPIO38 | 25     | $1N3735    | via LEDC, 5 kHz              |

## Other peripherals

| Signal      | GPIO    | Component | Notes                       |
|-------------|---------|-----------|------------------------------|
| OBD TX (K-Line) | GPIO? | U5 L9637 | pin 1 = $1N2177 → U1 pin 10 → GPIO? (DevKit right row) |
| CAN TX      | GPIO?   | U6 SN65HVD230 | $1N6401 → U1 pin 38 → GPIO? |
| CAN RX      | GPIO?   | U6 SN65HVD230 | $1N6394 → U1 pin 39 → GPIO? |
| IMU SDA     | GPIO?   | U8/U9 MPU6050 | $1N6462 → J1 pin 3 → U1?   |
| IMU SCL     | GPIO?   | U8/U9 MPU6050 | $1N6467 → J1 pin 4 → U1?   |
| BL gate     | GPIO?   | Q1 2N7002 | $1N2532 → U1 pin 30 → GPIO? |

> The ESP32-S3-DevKit-N8R8 right-side header pin numbering is needed for final
> resolution of the rows above. Cross-reference with Espressif's official
> ESP32-S3-DevKitC-1 pinout diagram.
