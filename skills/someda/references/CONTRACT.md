# The CircuitPlan contract

The planner (Claude) writes this JSON. The engine validates it strictly, then owns ALL geometry deterministically.

## Schema

```jsonc
{
  // required
  "name": "short project name",
  "description": "one-line description",
  "components": [
    {
      "reference": "R1",              // unique refdes, required
      "value": "10k",                 // part value; may carry power ("3W LED")
      "lib_id": "Device:R",           // KiCad symbol convention (schematic only)
      "footprint": "Resistor_SMD:R_0402_1005Metric",  // real KiCad footprint "Lib:Name"
      "power_w": 0.25,                // optional: dissipation in watts
      "position": "left_edge",        // optional: top_left, top, top_right, left, center, right,
                                      //   bottom_left, bottom, bottom_right, or an edge:
                                      //   left_edge, right_edge, top_edge, bottom_edge
      "edge_at": 0.3,                 // optional, edges only: 0.0 = left/top end … 1.0 = right/bottom end
      "rotation": 270,                // optional: 0/90/180/270, KiCad sense (CCW on screen)
      "near": "U1"                    // optional: hug this reference, on the side of the pins they share
    }
  ],
  "nets": [
    {
      "name": "GND",                  // power nets: "VCC"/"GND" on 2-layer boards; real rail names otherwise
      "pins": ["U1:1", "R1:1"],       // "REFDES:PAD_NUMBER", required; pad numbers as in the footprint
      "freq_hz": 2400000000,          // optional: highest frequency carried
      "role": "rf",                   // optional: power|ground|clock|rf|highspeed|analog|digital
      "termination": "series"         // optional: series|parallel|on-chip|none (a ≤100 Ω two-pin resistor on the net is detected)
    }
  ],
  // differential pairs (optional): routed as ONE coupled pair — same layer, constant gap,
  // intra-pair length matched; both nets must connect the same two components
  "pairs": [
    {"p": "USB_DP", "n": "USB_DM", "z_diff": 90},                 // z_diff default 100 Ω
    {"p": "CAM_D0P", "n": "CAM_D0N", "z_diff": 100, "skew_mm": 0.15}   // skew budget default by interface class
  ],
  // multilayer (optional)
  "layers": 6,                        // 2 (default), 4 or 6 (even, up to 12)
  "board": {"width_mm": 90, "height_mm": 60},   // fixed outline; absent = area budget from courtyards
  "planes": [                         // copper pours on inner layers (never F.Cu/B.Cu)
    {"net": "GND",  "layer": "In1.Cu"},
    {"net": "+3V3", "layer": "In3.Cu"},
    {"net": "+1V2", "layer": "In4.Cu", "priority": 0},
    {"net": "+1V8", "layer": "In4.Cu", "region": "auto", "priority": 1}   // island under its pins; or [x0,y0,x1,y1] mm
  ]
}
```

## Validation rules (all enforced)

- No duplicate references; every net pin must belong to a listed component
- Pins are `"REFDES:PAD_NUMBER"` — malformed pins rejected; after generation EVERY plan pin must exist as a pad of the footprint (pin-coverage gate) — a wrong pin number is caught here, a wrong-but-existing one is not
- `layers` must be even, 2..12; `planes` need `layers` ≥ 4 and name inner copper layers and plan nets
- `pairs`: both nets exist, differ, belong to one pair only, share at least two components (the pair's two ends); `z_diff` 20..300 Ω. A chain (SoC → ESD → connector) is two pairs with different net names per segment
- Components referenced by no net (mounting holes) get no schematic pins and no connectivity

## Differential pairs, crosstalk, oscillation gates

- **Pair cross-section** comes from the stackup: JLCPCB's own impedance-calculator table for the 6-layer JLC06161H-3313 and 4-layer JLC04161H-7628 outer layers (90/100 Ω at 5–8 mil spacing, run 2026-10-19), else the Kirschning–Jansen closed form calibrated by the fab's 50 Ω width. The build prints `pair P/N: Z Ω → w / gap, skew budget (source)`.
- **Routing**: pairs go first, as a coupled corridor on one layer over a solid plane (never over a split plane; B.Cu is excluded on 6-layer boards), two offset tracks, short single-ended tails from the pads into the corridor terminals, intra-pair skew compensated with tail detours and trapezoid bumps. The `pairs` stage fails when a trunk is not coupled or its measured skew exceeds the budget (defaults from the Toradex layout guide: USB 2.0 1.1 mm, Ethernet 0.25 mm, MIPI/LVDS/PCIe 0.15 mm).
- **Crosstalk is a routing constraint**: every net with a frequency or a clock/highspeed/rf role keeps the 3W rule (5W for rf, highspeed and ≥100 MHz clocks; W = the board's trace width) edge-to-edge from other nets' traces, except inside breakout zones (1 mm around pads, fine-pitch escape bands). The SI audit measures the routed board with the same zones and reports `crosstalk-violation` (error) outside them and `crosstalk-breakout` (info) inside.
- **Oscillation checks** (`si-audit`, `stability-audit`, `pdn-audit` stages): `unterminated-line` (error) for an electrically long net with no termination; `decoupling-loop` per capacitor from its routed stubs and via pair (error above 6 nH at an IC, warning above 3 nH); regulator output capacitance vs datasheet minimum (TPS5622xx 10 µF, ME6211/XC6206 1 µF); crystal load capacitors and crystal trace length/vias; switch-node and feedback-node length; per-rail PDN |Z(f)| 100 kHz–1 GHz vs the ΔV/ΔI target. Terminated transmission lines are no longer flagged as LC self-resonances.

## Footprints

`footprint` is resolved to `<dir>/<Lib>.pretty/<Name>.kicad_mod` from `SOMEDA_FOOTPRINT_DIRS` (colon separated), `KICAD10_FOOTPRINT_DIR`…`KICAD7_FOOTPRINT_DIR`, then the standard install paths. The library definition is embedded verbatim in the board (silk, fab, courtyard, keep-outs, 3D model), with placement, reference, value and pad nets injected. Pad angles and zone polygons follow KiCad's conventions (verified against kicad-cli). Custom footprints (e.g. an exposed-pad variant) go in your own `.pretty` directory on `SOMEDA_FOOTPRINT_DIRS`.

## Placement

- `position` edges put the courtyard flush to that edge, sliding along it from `edge_at` to the first free slot; semantic positions spiral out from their slot
- Everything else is placed in connectivity order at the free spot nearest the centroid of its already-placed neighbours; `near` aims at the anchor's pads that share a net with the part (a 1V8 cap goes to the 1V8 pins)
- Real courtyards never overlap (0.6mm gap, 0.5mm board margin); fine-pitch ICs get a 3.6mm keep-out ring for escape vias; parts ≥0.5W keep ≥15mm apart

## Frequency awareness

Frequency sources, in priority order:
1. **Plan-declared** `freq_hz` — the circuit's intent knows it (clocks, RF, interfaces)
2. **Component specs** — values like `"2.4GHz"`, `"16MHz crystal"`, part classes (`NE555`→500kHz, `74HC00`→50MHz, `LM358`→1MHz, `STM32`→240MHz)
3. **Net name** — `VCC/VDD/+3V`→power(DC), `GND/VSS`→ground, `*CLK*/XTAL/OSC*`→clock, `RF*/ANT*`→RF, `USB/DDR/PCIE`→highspeed

What it drives:
- **Impedance control**: RF/high-speed/fast-clock nets get a 50Ω target; the router SOLVES the trace width from the microstrip equation on the JLCPCB stackup of the layer count (2-layer 1.6mm FR-4 Er 4.5 → 2.78mm; 4-layer JLC04161H-7628 h 0.21mm; 6-layer JLC06161H-3313 h 0.10mm → ~0.15mm)
- **Transmission-line checks**: rise-time vs critical length (Tpd ≈ 150ps/inch)
- **Crosstalk spacing**: 3W rule, 5W for RF/high-speed
- **SWR audit**: routed Z0 vs target (error >2, warning >1.5) — JLCPCB impedance tolerance is ±10%
- **Stub resonance**: branch length vs λ/20 at the net's frequency
- **Oscillation risk**: the net's measured LC self-resonance vs its operating frequency

## Power awareness

- `power_w` declared per component, or parsed from the value (`"0.25W"`, `"500mW"`, `"3W LED"`)
- **Placement**: every pair of components ≥0.5W gets apart ≥15mm (the constraint solver enforces it)
- **Thermal audit**: package θ_JA classes (DIP-8 85, SOIC-8 120, SOT-23 250, SOT-23-5/6 200, LQFP-100+ 45, QFN/exposed pad 40 °C/W) → T_J = T_A + P·θ_JA vs the 125°C limit
- **Board area**: high-power parts claim 50% extra courtyard area

## Routing (what the engine does with the plan)

- Design rules per layer count: 2-layer 0.25mm trace / 0.2 clearance / 0.6-0.3 via on a 0.5mm grid; 4- and 6-layer 0.127/0.127 / 0.35-0.2 via on a 0.127mm grid, hole-to-hole 0.45, copper-to-edge 0.5 — all inside JLCPCB scope, and written to `circuit.kicad_pro` so kicad-cli judges by them
- Plane nets are never routed pad-to-pad: every SMD pad gets a fanout stub to a through via (preferring sites under the part body); through-hole pads reach the plane by their barrel; a pad with no via site is routed as a trace to the nearest member of its net
- Every fine-pitch signal pin (pitch < 0.65mm) gets a depth-staggered escape via so its connection starts on the inner layers; nothing else may run along a pin row or drop a via next to an escape lane
- Footprint keep-out zones block tracks/vias as declared; NPTH holes and unnetted pads are keep-outs with hole clearance
- Bounded rip-up-and-reroute (whole nets), then plain retries of whatever is still open
- **Not done**: pair-to-pair (clock-to-data) length matching, vias inside a coupled pair section, bottom-side placement, electrical simulation — say so when it matters

## Worked example: 555 LED blinker (2 layers)

```json
{
  "name": "555 LED blinker",
  "description": "555 timer astable blinking an LED at ~1Hz",
  "components": [
    {"reference": "U1", "value": "NE555", "lib_id": "Timer:NE555", "footprint": "Package_DIP:DIP-8_W7.62mm"},
    {"reference": "R1", "value": "10k", "lib_id": "Device:R", "footprint": "Resistor_SMD:R_0603_1608Metric", "near": "U1"},
    {"reference": "R2", "value": "470k", "lib_id": "Device:R", "footprint": "Resistor_SMD:R_0603_1608Metric", "near": "U1"},
    {"reference": "C1", "value": "1uF", "lib_id": "Device:C", "footprint": "Capacitor_SMD:C_0603_1608Metric", "near": "U1"},
    {"reference": "C2", "value": "100nF", "lib_id": "Device:C", "footprint": "Capacitor_SMD:C_0603_1608Metric", "near": "U1"},
    {"reference": "D1", "value": "red LED", "lib_id": "Device:LED", "footprint": "LED_SMD:LED_0603_1608Metric"},
    {"reference": "R3", "value": "330R", "lib_id": "Device:R", "footprint": "Resistor_SMD:R_0603_1608Metric", "near": "D1"}
  ],
  "nets": [
    {"name": "VCC", "pins": ["U1:8", "U1:4", "R1:1", "R2:1", "C2:1"]},
    {"name": "GND", "pins": ["U1:1", "C1:2", "C2:2", "D1:2"]},
    {"name": "TRIG", "pins": ["U1:2", "U1:6", "R2:2", "C1:1"]},
    {"name": "OUT", "pins": ["U1:3", "R3:1"]},
    {"name": "LED_K", "pins": ["R3:2", "D1:1"]},
    {"name": "DIS", "pins": ["U1:7", "R1:2"]}
  ]
}
```

The 555's real pinout: 1=GND, 2=TRIG, 3=OUT, 4=RESET, 5=CTRL, 6=THRES, 7=DISCH, 8=VCC. This plan reaches all six gates with kicad-cli DRC at 0 errors.

## Worked example: a 6-layer SBC

See `examples/sompi-v3s/` in the plugin repository: an Allwinner V3s (eLQFP-128, 0.4mm pitch) Linux SBC with USB-C, Ethernet, microSD, SPI NOR, LCD and camera FPCs, audio and a GPIO header — 132 components, 114 nets, planes GND/+3V3/+1V2 plus a +1V8 island, 220 plane fanouts, 130 escape vias, every connection routed, kicad-cli DRC 0 errors, 13 Gerber layers. Its generator script shows the pattern: look every SoC pin up by name in a verified pin table, derive connector rotations from footprint geometry, and place connectors on the edge facing their pins.
