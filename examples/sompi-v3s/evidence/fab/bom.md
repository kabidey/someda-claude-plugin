# Bill of materials — SomPi-V3s

54 line items, 128 components. MPN and LCSC columns come from the plan (`mpn`, `lcsc`); empty means a generic part ordered by value and package.

| # | Qty | References | Value | MPN | LCSC | Package | Footprint |
|---|---|---|---|---|---|---|---|
| 1 | 1 | U1 | Allwinner V3s |  |  | eLQFP-128 14x14mm P0.4mm EP5.72x5.72mm ThermalVias | `SomPi:eLQFP-128_14x14mm_P0.4mm_EP5.72x5.72mm_ThermalVias` |
| 2 | 1 | U4 | ME6211C18M5G | ME6211C18M5G |  | SOT-23-5 | `Package_TO_SOT_SMD:SOT-23-5` |
| 3 | 2 | U2, U3 | TPS562200 | TPS562200DDCR |  | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` |
| 4 | 1 | U8 | USBLC6-2SC6 | USBLC6-2SC6 |  | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` |
| 5 | 1 | U6 | W25Q128JVSIQ |  |  | SOIC-8 3.9x4.9mm P1.27mm | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| 6 | 1 | U5 | XC6206P302MR | XC6206P302MR |  | SOT-23 | `Package_TO_SOT_SMD:SOT-23` |
| 7 | 1 | J6 | 3.5mm jack | SJ-3523-SMT | C4991872 | Jack 3.5mm CUI SJ-3523-SMT Horizontal | `Connector_Audio:Jack_3.5mm_CUI_SJ-3523-SMT_Horizontal` |
| 8 | 1 | J5 | CAM MIPI 24P |  |  | Hirose FH12-24S-0.5SH 1x24-1MP P0.50mm Horizontal | `Connector_FFC-FPC:Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal` |
| 9 | 1 | J7 | GPIO 2x13 |  |  | PinHeader 2x13 P2.54mm Vertical | `Connector_PinHeader_2.54mm:PinHeader_2x13_P2.54mm_Vertical` |
| 10 | 1 | J4 | LCD 40P RGB |  |  | Hirose FH12-40S-0.5SH 1x40-1MP P0.50mm Horizontal | `Connector_FFC-FPC:Hirose_FH12-40S-0.5SH_1x40-1MP_P0.50mm_Horizontal` |
| 11 | 1 | J2 | RJ45 HR911105A | HR911105A | C12074 | RJ45 Hanrun HR911105A Horizontal | `Connector_RJ:RJ45_Hanrun_HR911105A_Horizontal` |
| 12 | 1 | J8 | UART0 debug |  |  | PinHeader 1x03 P2.54mm Vertical | `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` |
| 13 | 1 | J1 | USB-C 16P | TYPE-C-31-M-12 | C165948 | USB C Receptacle HRO TYPE-C-31-M-12 | `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` |
| 14 | 1 | J3 | microSD |  |  | microSD HC Hirose DM3AT-SF-PEJM5 | `Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5` |
| 15 | 1 | Y1 | 24MHz |  |  | Crystal SMD 3225-4Pin 3.2x2.5mm | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |
| 16 | 1 | Y2 | 32.768kHz |  |  | Crystal SMD 3215-2Pin 3.2x1.5mm | `Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm` |
| 17 | 1 | L3 | 10uH |  |  | 0805 (2012 metric) | `Inductor_SMD:L_0805_2012Metric` |
| 18 | 2 | L1, L2 | 4.7uH 3A | NR4018T4R7M | C92936 | L Taiyo-Yuden NR-40xx | `Inductor_SMD:L_Taiyo-Yuden_NR-40xx` |
| 19 | 1 | D1 | PWR red |  |  | LED 0603 (1608 metric) | `LED_SMD:LED_0603_1608Metric` |
| 20 | 1 | D2 | STAT green |  |  | LED 0603 (1608 metric) | `LED_SMD:LED_0603_1608Metric` |
| 21 | 1 | Q1 | AO3400A |  |  | SOT-23 | `Package_TO_SOT_SMD:SOT-23` |
| 22 | 1 | SW2 | KEY1 |  |  | SW SPST PTS645Sx43SMTR92 | `Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92` |
| 23 | 1 | SW1 | RESET |  |  | SW SPST PTS645Sx43SMTR92 | `Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92` |
| 24 | 1 | F1 | 2A fuse |  |  | 1206 (3216 metric) | `Fuse:Fuse_1206_3216Metric` |
| 25 | 34 | C1, C2, C3, C4, C5, C6, C7, C9, C10, C11, C12, C13, C14, C16, C17, C18, C19, C20, C21, C22, C24, C25, C29, C30, C31, C41, C45, C53, C54, C55, C56, C57, C58, C59 | 100nF |  |  | 0402 (1005 metric) | `Capacitor_SMD:C_0402_1005Metric` |
| 26 | 8 | C8, C15, C23, C26, C27, C28, C33, C50 | 10uF |  |  | 0603 (1608 metric) | `Capacitor_SMD:C_0603_1608Metric` |
| 27 | 3 | C40, C42, C46 | 10uF |  |  | 0805 (2012 metric) | `Capacitor_SMD:C_0805_2012Metric` |
| 28 | 2 | C34, C35 | 18pF |  |  | 0402 (1005 metric) | `Capacitor_SMD:C_0402_1005Metric` |
| 29 | 1 | C39 | 1nF |  |  | 0402 (1005 metric) | `Capacitor_SMD:C_0402_1005Metric` |
| 30 | 2 | C32, C38 | 1uF |  |  | 0402 (1005 metric) | `Capacitor_SMD:C_0402_1005Metric` |
| 31 | 3 | C49, C51, C52 | 1uF |  |  | 0603 (1608 metric) | `Capacitor_SMD:C_0603_1608Metric` |
| 32 | 4 | C43, C44, C47, C48 | 22uF |  |  | 0805 (2012 metric) | `Capacitor_SMD:C_0805_2012Metric` |
| 33 | 2 | C36, C37 | 6pF |  |  | 0402 (1005 metric) | `Capacitor_SMD:C_0402_1005Metric` |
| 34 | 1 | R41 | 0R |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 35 | 1 | R7 | 0R |  |  | 0603 (1608 metric) | `Resistor_SMD:R_0603_1608Metric` |
| 36 | 1 | R11 | 100k 1% |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 37 | 1 | R9 | 10M |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 38 | 7 | R27, R28, R29, R30, R31, R33, R36 | 10k |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 39 | 2 | R18, R20 | 10k 1% |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 40 | 3 | R13, R14, R35 | 1k |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 41 | 1 | R6 | 200k 1% |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 42 | 1 | R40 | 22R |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 43 | 1 | R5 | 240R 1% |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 44 | 4 | R1, R2, R3, R4 | 2k 1% |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 45 | 1 | R17 | 33.2k 1% |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 46 | 2 | R25, R26 | 330R |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 47 | 3 | R32, R34, R37 | 33R |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 48 | 4 | R38, R39, R42, R43 | 4.7k |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 49 | 1 | R10 | 47k |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 50 | 2 | R15, R16 | 5.1k |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 51 | 1 | R19 | 5.62k 1% |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 52 | 4 | R21, R22, R23, R24 | 51R 1% |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 53 | 1 | R8 | 6.04k 1% |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
| 54 | 1 | R12 | 6.8k 1% |  |  | 0402 (1005 metric) | `Resistor_SMD:R_0402_1005Metric` |
