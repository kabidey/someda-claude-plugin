# Allwinner V3s (eLQFP-128) pin research summary

Companion to `v3s_pins.json`. Pin numbers come from the Allwinner V3s Datasheet V1.0 Table 3-1 and were
cross-checked against the Sipeed Lichee Pi Zero schematic and four KiCad V3s symbols (see "Verification" at the end).

Sources (all downloaded under `research/dl/`):

| Source | Used for |
|---|---|
| Allwinner V3s Datasheet V1.0 (linux-sunxi.org/images/2/23/Allwinner_V3s_Datasheet_V1.0.pdf) | Table 3-1 pin list, 3-2 mux, 3-3 descriptions, Table 9-1/9-2 voltages, §4.2 boot, §4.11 LRADC, Appendix pin map + package drawing |
| Sipeed Lichee Pi Zero schematic (dl.sipeed.com/fileList/LICHEE/Zero/HDK/lichee_zero_Schematic.pdf, KiCad export 2021-09-10) | Pin-number cross-check, rail assignment, crystal / reset / SVREF / SZQ / RTX component values |
| Sipeed Lichee Zero Dock schematic (…/lichee_zero_dock_Schematic.pdf, sheet 3) | Ethernet magnetics / termination, LRADC key ladder |
| FunKey-Project/FunKey-S-Hardware (FunKey.lib, FunKey.net, ELQFP-128.kicad_mod) | Pin cross-check, production rail assignment, footprint |
| Allwinner "V3s hardware design guide V1.0" 2015-05-19 (Zepan/lichee-pi-zero, Chinese) | Design rules: ZQ, card CLK, audio grounding, camera, keys, reset cap |
| aep/kicad, TobleMiner/OpenHomelabSwitch, TreeNewbeer/Coonix KiCad libs | Additional symbol cross-checks |

## Package

eLQFP-128 (E-PAD LQFP), body 14.0 x 14.0 mm, lead-tip span 16.0 x 16.0 mm, pitch 0.40 mm, max height 1.60 mm
(datasheet drawing DB128-SW1, JEDEC MS-026 reference). Top view, pin 1 at the upper-left corner, numbering
counter-clockwise: 1-32 left side (top to bottom), 33-64 bottom (left to right), 65-96 right (bottom to top),
97-128 top (right to left). The exposed pad is the only digital ground: Table 3-1 lists no GND pins apart from
AGND (116); it must be soldered to GND. The drawing lists four exposed-pad options (3.61 / 5.72 / 8.00 / 7.75x6.60 mm
REF) without saying which applies to product code DB1283C; the FunKey footprint uses 0.2475 x 1.6 mm lead pads at
+/-7.8 mm with a 3x3 via array (1 mm grid) in the pad. Verify the EPAD size against a physical part before finalising.

## Power domains

Datasheet Table 9-2 recommended operating conditions; "Zero" = Lichee Pi Zero rail (power sheet), "FunKey" = FunKey-S net.

| Domain | Pins | Min / Typ / Max (V) | Powers | Zero | FunKey |
|---|---|---|---|---|---|
| VDD-CPU0..7 | 26, 25, 21, 20, 38, 47, 51, 56 | TBD / 1.2 / TBD | Cortex-A7 core | 1V2 (Vcpu) | +1V25 |
| VDD-SYS0..5 | 80, 108, 126, 19, 58, 64 | TBD / 1.2 / TBD | System logic | 1V2 (Vsys) | +1V25 |
| VCC-DRAM0..11 | 65, 66, 67, 68, 69, 70, 72, 79, 59, 60, 61, 62 | 1.7 / 1.8 / 1.9 | On-package 512 Mbit DDR2 | 1V8 (Vdram) | +1V8 |
| VCC-IO0..3 | 104, 127, 57, 50 | 1.7 / 1.8-3.3 / 3.6 | Ports B, C, F, G | 3V3 (Vio) | +3V3 |
| VCC-PE0/1 | 12, 29 | 1.7 / 1.8-3.3 / 3.6 | Port E (LCD / CSI bus) | 3V3 (Vpe) | +3V3 |
| VCC-PLL | 76 | 2.7 / 3.0 / 3.3 | System PLLs | 3V0 (XC6206 LDO) | +3V0 |
| AVCC | 115 | 2.8 / 3.0 / 3.3 | Audio codec analog, LRADC reference pull-up | 3V0 (XC6206 LDO) | +3V0 |
| HPVCCIN | 122 | not in Table 9-2 | Headphone amplifier (HPVCCBP 123 = its bypass cap) | 3V3 (Vhp) | +3V3 |
| VCC-RTC | 98 | 3.0 / 3.3 / 3.6 | RTC / always-on domain, 32 kHz oscillator | 3V3 via 0R (Vrtc) | +3V3_AO |
| RTC-VIO | 97 | internal LDO output (0.7-1.4 V programmable, §4.12) | Bypass only: 10 uF to GND, do not drive | cap only | - |
| VCC-USB | 109 | 3.0 / 3.3 / 3.45 | USB 2.0 PHY | 3V3 (Vusb) | +3V3 |
| VCC-MCSI | 85 | 3.0 / 3.3 / 3.6 | MIPI CSI-2 receiver | 3V3 (Vmcsi) | +3V3 |
| EPHY_VCC | 93 | 2.8 / 3.3 / 3.6 | Ethernet PHY analog | 3V3 (Vcc_phy) | +3V3 |
| EPHY_VDD | 88 | 1.0 / 1.1 / 1.2 | Ethernet PHY core | 1V2 (Vdd_phy) | +1V25 (above the 1.2 V max) |
| AGND | 116 | - | Codec analog ground; single point to GND through 0R, >= 1 mm trace (design guide) | GND | GND |
| EPAD | - | - | Digital ground | GND | GND (3x3 vias) |

Notes
- AVCC and VCC-PLL: 3.3 V is the datasheet *maximum*; both reference boards derive a dedicated 3.0 V LDO rail. Do not tie them to 3V3.
- The datasheet does not state which VCC-IOn feeds which port. aep.lib annotates VCC-IO0=PB, IO1=PC, IO2=PF, IO3=PG, but this is unsourced and conflicts with physical adjacency on the pin map (104 among PF, 127 beside PG, 50 beside PB, 57 beside PC). Treat VCC-IO0..3 (+ VCC-PE) as one rail unless deliberately split.
- Design guide: VCC-PE, the camera MIPI IOVCC and the LCD IO supply must be one rail.
- There is no VDD-ADC / VRP pin on the V3s; the LRADC is referenced to AVCC on the reference boards.
- Absolute maxima (Table 9-1): 3.6 V on all 3.3 V-class rails, 1.98 V on VCC-DRAM, 1.3 V on VDD-CPU / VDD-SYS / EPHY_VDD; +/-40 mA per IO.
- Power sequencing (§9.5) exists only as figures that do not extract to text; not reproduced here.
- Decoupling on the Zero: 10 uF + several 1 uF / 100 nF per rail, placed on the back side under the pins (design guide).

DRAM reference pins
- SVREF0 (71), SVREF1 (63): DDR2 VREF = VCC-DRAM / 2, generated externally. Zero: 2k / 2k 1% divider from Vdram to GND with two 100 nF; FunKey: R25 / R28 + C80.
- SZQ (73): 240 R 1% to GND, close to the pin (design guide and both boards).

## IO electrical (Table 9-3)

VIH >= 0.7 x VCC-IO, VIL <= 0.3 x VCC-IO, programmable pull-up / pull-down 50-150 k (100 k typ), 20 mA buffer strength on
all GPIO, no pulls at reset, PF0/PF1/PF3/PF5 default to JTAG MS/DI/DO/CK at reset, all other GPIO high-Z.

## Interfaces

### USB0 (OTG, integrated HS PHY)
| Signal | Pin |
|---|---|
| USB-DP | 111 |
| USB-DM | 110 |
| VCC-USB | 109 |

90 R differential, < 4000 mil, <= 2 vias (design guide). No dedicated ID pin: the design guide uses PG4 as ID input
with a pull-up to 3V3 (low = device, high = host) and gates VBUS with a power switch that is off by default.

### Ethernet (internal 10/100 PHY)
| Signal | Pin | Notes |
|---|---|---|
| EPHY_TXP / EPHY_TXN | 92 / 91 | transmit pair |
| EPHY_RXP / EPHY_RXN | 90 / 89 | receive pair |
| EPHY_RTX | 94 | bias resistor to GND: 6 k 1% (Lichee Zero R2; printed "6K-1%") |
| EPHY_LINK_LED / EPHY_SPD_LED | 77 / 78 | LED outputs (output supply domain not stated) |
| EPHY_VCC / EPHY_VDD | 93 / 88 | 3.3 V analog / 1.1 V core |

The datasheet gives no termination spec. Lichee Zero Dock reference (sheet 3): HR911105A RJ45 with integrated
magnetics; TD+/TD-/RD+/RD- each pulled to 3V3 through 51 R (R8-R11); both transformer centre taps tied to the same
3V3 node through L1 10 uH, with 100 nF to GND at each centre tap (C8, C9); pairs routed as 100 R differential. On the
Zero module the four lines run straight from the SoC to the edge pads with no series parts.

### Crystals
| Signal | Pin | Reference design |
|---|---|---|
| X24MIN / X24MOUT | 75 / 74 | 24.000 MHz fundamental, +/-40 ppm, <= 50 uW drive; Zero: 4-pad crystal with 18 pF to GND each side; FunKey: 24 MHz 18 pF crystal. Keep >= 25 mm from board edge, shield with GND (guide) |
| X32KIN / X32KOUT | 96 / 95 | 32.768 kHz; Zero: 6 pF each side + 10 M parallel resistor; FunKey: 12.5 pF crystal with feedback resistor |

### SDC0 (microSD / boot) and JTAG, port F, VCC-IO (pin 104 adjacent)
| Function | GPIO | Pin | Other function |
|---|---|---|---|
| SDC0_D1 | PF0 | 107 | JTAG_MS (default at reset) |
| SDC0_D0 | PF1 | 106 | JTAG_DI (default at reset) |
| SDC0_CLK | PF2 | 105 | UART0_TX |
| SDC0_CMD | PF3 | 103 | JTAG_DO (default at reset) |
| SDC0_D3 | PF4 | 102 | UART0_RX |
| SDC0_D2 | PF5 | 101 | JTAG_CK (default at reset) |
| (GPIO only) | PF6 | 100 | no alt function; card detect on the Zero |

Design guide: 33 R series on CLK near the SoC, no pull-up on CLK, <= 15 pF on CLK, ESD on the card socket.

### SPI0 (boot NOR / NAND), port C, VCC-IO (pin 57 adjacent)
| Function | GPIO | Pin | Other function |
|---|---|---|---|
| SPI0_MISO | PC0 | 52 | SDC2_CLK |
| SPI0_CLK | PC1 | 53 | SDC2_CMD |
| SPI0_CS | PC2 | 54 | SDC2_RST |
| SPI0_MOSI | PC3 | 55 | SDC2_D0 |

### SDC1 (SDIO WiFi), port G, VCC-IO (pin 127 adjacent)
PG0 (5) SDC1_CLK, PG1 (4) SDC1_CMD, PG2 (3) SDC1_D0, PG3 (2) SDC1_D1, PG4 (1) SDC1_D2, PG5 (128) SDC1_D3; all also PG_EINT0..5.

### UART
| UART | TX | RX | RTS | CTS |
|---|---|---|---|---|
| UART0 (mux A) | PB8 (48) | PB9 (49) | - | - |
| UART0 (mux B) | PF2 (105) | PF4 (102) | - | - |
| UART1 | PE21 (9) | PE22 (8) | PE23 (7) | PE24 (6) |
| UART2 | PB0 (39) | PB1 (40) | PB2 (41) | PB3 (42) |

Lichee Zero exposes UART0 on PB8/PB9 (header marked "I2C1"). Design guide asks for test points on UART2.

### TWI and PWM
| Bus | SCK | SDA |
|---|---|---|
| TWI0 | PB6 (45) | PB7 (46) |
| TWI1 (mux A) | PB8 (48) | PB9 (49) |
| TWI1 (mux B, CSI_SCK/SDA) | PE21 (9) | PE22 (8) |

PWM0 = PB4 (43), PWM1 = PB5 (44). Design guide: use the CSI TWI (PE21/PE22) for the camera, not the system TWI.

### Audio codec
| Signal | Pin | Reference design |
|---|---|---|
| HPOUTL / HPOUTR | 121 / 120 | keep the RC to GND before any PA input (guide) |
| HPCOM / HPCOMFB | 125 / 124 | headphone common (virtual ground) output / feedback input; Dock: 22 R + 100 nF, 0 R feedback |
| HBIAS | 119 | mic bias; Dock: 2 k to mic, 1 uF |
| MICIN1P / MICIN1N | 113 / 114 | differential mic input |
| VRA1 / VRA2 | 117 / 118 | internal references: Zero VRA2 10 uF, 200 k 1% VRA2-VRA1, VRA1 1 uF (values "must not be changed", guide) |
| HPVCCIN / HPVCCBP | 122 / 123 | amp supply (3V3) / bypass 10 uF + 100 nF |
| AVCC / AGND | 115 / 116 | 3.0 V analog supply / analog ground |

There is no VRP pin on the V3s (the second reference is VRA2). VRA1/VRA2/AGND return to one point and then through 0 R to GND.

### LCD RGB (port E, VCC-PE), RGB666 subset of a 24-bit bus
| LCD | GPIO | Pin | LCD | GPIO | Pin |
|---|---|---|---|---|---|
| LCD_CLK | PE0 | 37 | LCD_D13 | PE13 | 18 |
| LCD_DE | PE1 | 36 | LCD_D14 | PE14 | 17 |
| LCD_HSYNC | PE2 | 35 | LCD_D15 | PE15 | 16 |
| LCD_VSYNC | PE3 | 34 | LCD_D18 | PE16 | 15 |
| LCD_D2 | PE4 | 33 | LCD_D19 | PE17 | 14 |
| LCD_D3 | PE5 | 32 | LCD_D20 | PE18 | 13 |
| LCD_D4 | PE6 | 31 | LCD_D21 | PE19 | 11 |
| LCD_D5 | PE7 | 30 | LCD_D22 | PE23 | 7 |
| LCD_D6 | PE8 | 28 | LCD_D23 | PE24 | 6 |
| LCD_D7 | PE9 | 27 | | | |
| LCD_D10 | PE10 | 24 | | | |
| LCD_D11 | PE11 | 23 | | | |
| LCD_D12 | PE12 | 22 | | | |

Only D2-D7, D10-D15, D18-D23 exist (18-bit). Design guide: 33 R on LCD_CLK near the SoC, cap near the connector, CLK guarded by GND.

### CSI (parallel, port E) and MIPI CSI-2
Parallel: CSI_PCLK PE0 (37), CSI_MCLK PE1 (36), CSI_HSYNC PE2 (35), CSI_VSYNC PE3 (34), CSI_D0..D15 = PE4..PE19
(33, 32, 31, 30, 28, 27, 24, 23, 22, 18, 17, 16, 15, 14, 13, 11), CSI_FIELD PE20 (10), CSI_SCK PE21 (9), CSI_SDA PE22 (8).
MIPI: MCSI-D0P/D0N 81/82, MCSI-D1P/D1N 83/84, MCSI-CKP/CKN 86/87, VCC-MCSI 85, CSI_MIPI_MCLK on PE20 (10).
Design guide: 33 R in series with MCLK near the SoC plus an NC cap pad near the connector; 100 R differential for MIPI; 33 R on parallel data for EMC.

## Boot, reset and keys

- Boot ROM order (§4.2): SDC0 -> SPI0 NOR -> SPI0 NAND -> USB (FEL). A boot-select pin with an internal 50 k pull-up
  forces USB boot when low (readable as VER_REG bit 8 "UBOOT_SEL_PAD_STA"), but Tables 3-1/3-3 do not name that pin,
  so it is not identified here. In practice (linux-sunxi wiki) FEL is entered by removing the SD card when the SPI
  flash is empty; the Lichee Zero provides a "BOOT" option R5 (0 R, not fitted) from SPI0_MISO (PC0, 52) to GND to
  defeat SPI boot. No other boot-strap resistors are documented.
- RESET (99): active-low input, no internal pull (Table 3-1). Zero: 47 k to 3V3, 1 uF to GND, push-button to GND.
  FunKey: pull-up + cap, also driven by the AXP209 PMIC. Design guide: 10 nF to GND close to the SoC, keep away from board edge.
- LRADC0 (112): 6-bit key ADC, 0-2.0 V input range, up to 250 Hz. Zero: 100 k 1% to AVCC + 1 nF to GND; Dock ladder
  6k8 / 8k2 / 10 k / 11 k 1% giving 0.2 / 0.4 / 0.6 / 0.8 V key levels. Guide: keep pressed-key levels within 0-1.6 V and >= 0.15 V apart.
- USB ID: no SoC pin; use PG4 with pull-up to 3V3 (guide).
- ESD devices required on USB, mic and card connectors (guide).

## Verification

- Datasheet Table 3-1 parsed programmatically: 128 pins, numbers 1-128 each exactly once, every pin named.
- Datasheet Appendix pin map (page 419, rendered and inspected): same names on all four sides, EPAD in the centre.
- Lichee Pi Zero schematic (KiCad PDF, word bounding boxes paired per package side): 128/128 pin numbers agree,
  127/128 names identical; pin 62 is spelled "VCC-DARM11" (typo for VCC-DRAM11). Pin 129 = EGND/GND (exposed pad).
- FunKey.lib V3S: 128/128. aep.lib AllWinner-V3s(eLQFP-128): 128/128. TobleMiner Allwinner_V3S: 127/128 (pin 107
  "PF0MS" typo). Coonix V3s: 127/128 (pin 89 "EPHY-RTN" typo). Every pin is therefore confirmed by at least four
  sources besides the datasheet. The Sipeed / FunKey / Coonix symbols share spelling conventions and are probably one
  lineage; aep and TobleMiner are separate transcriptions.
- FunKey.net (ref U3) confirms the rail assignment for every power pin and the USB / crystal / SD / reset / audio nets.

Unconfirmed items (not pin numbers): exact EPAD dimension; exact value behind "6K-1%" on EPHY_RTX; which VCC-IOn index
feeds which port; supply domain of the 24 MHz oscillator cell, RESET input and PHY LED outputs (not stated in datasheet).
