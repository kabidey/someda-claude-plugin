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
  table; a typo fails the script, never the copper. It declares no connector rotations: the
  engine turns each edge connector's opening (courtyard/fab overhang beyond the pads) toward its
  edge and puts it on the edge (`edge_overhang_mm` 0.8 for the USB-C shell).
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

Result with someda 0.7.0 (2026-10-19): 187 of 187 connections routed, 225 plane fanouts,
104 escape vias (32 unused); 7 of 7 declared differential pairs routed as coupled pairs within
their intra-pair skew budgets (USB 90 Ω: J1↔U8 skew −0.65 mm of 1.1, U8↔U1 +0.52 mm with a via
crossover because its P/N order differs at the two ends; Ethernet 100 Ω ≤ 0.01 mm of 0.25; MIPI
CSI-2 100 Ω 0.00 mm of 0.15; coupled 10–46 mm each, single-ended tails up to 10.5 mm); 0 crosstalk
violations outside breakout zones; kicad-cli DRC 0 errors / 0 unconnected / 0 fab-blocking, all six
export gates pass, 13 Gerber layers in `out/fab/` plus the JLCPCB order package in `out/fab/jlcpcb/`.
The engine rotated every edge connector from its footprint geometry (USB-C shell 0.8 mm proud of
the top edge, RJ45 and camera FPC on the right, LCD FPC on the left, headers on the bottom), moved
the 3.5 mm jack to the bottom edge because the top edge had no 18 mm-deep slot left (two `repair:`
lines), and grew the +1V8 island 4 mm to reach six of its capacitors. Full outputs, the per-pair
table and the remaining warnings (crystal traces of 11–17 mm with vias, the camera connector's +1V8
capacitor 23 mm from the island, three +1V8 capacitors beyond the island's 6 mm growth limit, board
density 147 %) in `evidence/`.

## What "orderable" does not mean

The board passes design-rule and connectivity checks. It has not been simulated or built.
USB D+/D− (90 Ω), the Ethernet TX/RX pairs and the MIPI CSI-2 lanes (100 Ω) are declared as
`pairs` and routed as coupled pairs with measured intra-pair skew (see `evidence/README.md`);
pair-to-pair (clock-to-data) matching is not enforced, and a pair whose P/N order differs at its
two ends is crossed through a via at the far tails. The HR911105A LED pin
polarity and the 40-pin LCD pinout follow common conventions and must be checked against the
parts you buy. The TPS562200 feedback dividers (33.2k/10k → 3.30 V, 5.62k/10k → 1.195 V) and
the V3s rail assignments follow the datasheet table; AVCC and VCC-PLL are on a dedicated 3.0 V
LDO because 3.3 V is their datasheet maximum.
