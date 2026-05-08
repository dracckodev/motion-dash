#pragma once
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

esp_err_t lcd_init(void);

/* GPIO assignments — verify against your PCB before flashing!
 * Derived from netlist by overlaying ESP32-S3-DevKit-N8R8 pinout.
 *
 * U1 connector pin → GPIO:
 *   DevKit-N8R8 left  header (top→bot): 3V3,3V3,RST,3V3,GPIO4,GPIO5,GPIO6,GPIO7,GPIO15,GPIO16,GPIO17,GPIO18,GPIO8,GPIO3,GPIO46,GPIO9,GPIO10,GPIO11,GPIO12,GPIO13,GND
 *   DevKit-N8R8 right header (top→bot): GND,5V,GPIO43,GPIO44,GPIO0,GPIO45,GPIO48,GPIO47,GPIO21,GPIO14,GPIO47,GPIO38,GPIO39,GPIO40,GPIO41,GPIO42,GPIO2,GPIO1,GND,GND
 */
#define LCD_PIN_D0   GPIO_NUM_15   /* U4-26, net $1N3748 */
#define LCD_PIN_D1   GPIO_NUM_16   /* U4-24, net $1N3754 */
#define LCD_PIN_D2   GPIO_NUM_17   /* U4-22, net $1N3760 */
#define LCD_PIN_D3   GPIO_NUM_18   /* U4-20, net $1N3767 */
#define LCD_PIN_D4   GPIO_NUM_19   /* U4-18, net $1N3774 */ /* NOTE: GPIO19=USB- on some boards */
#define LCD_PIN_D5   GPIO_NUM_20   /* U4-16, net $1N3787 */
#define LCD_PIN_D6   GPIO_NUM_46   /* U4-11/15, net $1N3887 */
#define LCD_PIN_D7   GPIO_NUM_9    /* U4-9/23, net $1N3881 */
#define LCD_PIN_D8   GPIO_NUM_13   /* U4-28, net $1N3742 */
#define LCD_PIN_D9   GPIO_NUM_14   /* U4-8,  net $1N3815 */
#define LCD_PIN_D10  GPIO_NUM_12   /* U4-33, net $1N3695 */
#define LCD_PIN_D11  GPIO_NUM_7    /* U4-34, net $1N3808 */
#define LCD_PIN_D12  GPIO_NUM_11   /* U4-35, net $1N3684 */  /* ⚠ verify: strapping */
#define LCD_PIN_D13  GPIO_NUM_10   /* U4-37, net $1N3671 */
#define LCD_PIN_D14  GPIO_NUM_5    /* U4-39, net $1N3654 */
#define LCD_PIN_D15  GPIO_NUM_6    /* U4-27, net $1N3728 */

#define LCD_PIN_CS   GPIO_NUM_3    /* U4-5,  net $1N3956  ⚠ GPIO3 = JTAG on some */
#define LCD_PIN_RS   GPIO_NUM_4    /* U4-7,  net $1N4137 */  /* RS = D/C */
#define LCD_PIN_WR   GPIO_NUM_2    /* U4-21, net $1N3965 */
#define LCD_PIN_RD   GPIO_NUM_48   /* U4 not traced — assign spare; check TP1=$1N3977 */
#define LCD_PIN_RST  GPIO_NUM_40   /* U4-29, net $1N3826 */
#define LCD_PIN_BL   GPIO_NUM_38   /* U4-25, net $1N3735; PWM via LEDC */

#ifdef __cplusplus
}
#endif
