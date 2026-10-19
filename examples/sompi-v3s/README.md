# SomPi-V3s — a 6-layer Linux SBC built with someda

An Orange-Pi-shaped single-board computer that is not a copy of any vendor board: Allwinner V3s
(Cortex-A7, 64 MB DDR2 in package, eLQFP-128 at 0.4 mm pitch), USB-C power/OTG with ESD, 10/100
Ethernet through the SoC's internal PHY and a HR911105A magjack, microSD boot, 16 MB SPI NOR,
40-pin RGB LCD FPC with PWM backlight, 24-pin MIPI CSI-2 camera FPC, headphone jack on the
codec, 2x13 GPIO header, UART0 debug header, two bucks (3V3, 1V2) and two LDOs (1V8 DRAM, 3V0
analog/PLL), reset and user keys, LEDs, four M2.5 holes. 90 x 60 mm, 6 layers
(SIG / GND / SIG / +3V3 / +1V2 with a +1V8 island / SIG), JLCPCB JLC06161H-3313 stackup.

## Files

- `gen_sompi.py` — writes `plan.json`. Every SoC pin is looked up BY NAME in the verified pin
  table; a typo fails the script, never the copper. Connector rotations are derived from each
  footprint's own geometry (pad centroid → courtyard centre = opening direction).
- `plan.json` — the someda CircuitPlan: 132 components, 114 nets, 500 pins.
- `lib/SomPi.pretty/eLQFP-128_…_EP5.72x5.72mm_ThermalVias.kicad_mod` — the stock KiCad LQFP-128
  plus the exposed pad (the V3s's only digital ground) with a 3x3 thermal via array. The EPAD
  size is the middle of the datasheet's listed options; verify against a physical part.
- `research/v3s_pins.json`, `research/v3s_pins.md` — the pin table (128/128 agree between the
  datasheet and five independent symbol sources) and the power-domain / interface notes.
- `design-notes.txt` — what the generator assumed (RJ45 LED pin order, LCD pinout, pairs).
- `render/` — kicad-cli renders of the built board.

## Build

```bash
python3 -I gen_sompi.py
SOMEDA_FOOTPRINT_DIRS=$PWD/lib SOMEDA_PLAN_FILE=plan.json SOMEDA_PROJECT_DIR=out \
  someda ai build "SomPi V3s 6-layer SBC"
```

Result with someda 0.6.1 (2026-10-19): 192 of 192 connections routed, 220 plane fanouts,
130 escape vias (32 unused), kicad-cli DRC 0 errors / 0 unconnected / 0 silkscreen findings,
all six export gates pass, 13 Gerber layers in `out/fab/`. Full outputs in `evidence/`.

## What "orderable" does not mean

The board passes design-rule and connectivity checks. It has not been simulated or built.
USB D+/D−, the Ethernet TX/RX pairs and the MIPI CSI-2 lanes are routed as single-ended traces
(someda has no differential-pair routing or length matching yet). The HR911105A LED pin
polarity and the 40-pin LCD pinout follow common conventions and must be checked against the
parts you buy. The TPS562200 feedback dividers (33.2k/10k → 3.30 V, 5.62k/10k → 1.195 V) and
the V3s rail assignments follow the datasheet table; AVCC and VCC-PLL are on a dedicated 3.0 V
LDO because 3.3 V is their datasheet maximum.
