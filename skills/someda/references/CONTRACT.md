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
      "lib_id": "Device:R",           // KiCad lib convention
      "footprint": "Resistor_SMD:R_0603_1608Metric",  // optional
      "power_w": 0.25                 // optional: dissipation in watts
    }
  ],
  "nets": [
    {
      "name": "VCC",                  // power nets: exactly "VCC"/"GND"
      "pins": ["U1:1", "R1:1"],       // "REFDES:PIN_NUMBER", required
      "freq_hz": 2400000000,          // optional: highest frequency carried
      "role": "rf"                    // optional: power|ground|clock|rf|highspeed|analog|digital
    }
  ]
}
```

## Validation rules (all enforced)

- No duplicate references; every net pin must belong to a listed component
- Pins are `"REFDES:PIN_NUMBER"` — malformed pins rejected
- After generation, EVERY plan pin must exist as a pad (pin-coverage gate) — the plan and the copper cannot disagree
- Components not referenced by any net get pins 1+2 by default

## Frequency awareness

Frequency sources, in priority order:
1. **Plan-declared** `freq_hz` — the circuit's intent knows it (clocks, RF, interfaces)
2. **Component specs** — values like `"2.4GHz"`, `"16MHz crystal"`, part classes (`NE555`→500kHz, `74HC00`→50MHz, `LM358`→1MHz, `STM32`→240MHz)
3. **Net name** — `VCC/VDD/+3V`→power(DC), `GND/VSS`→ground, `*CLK*/XTAL/OSC*`→clock, `RF*/ANT*`→RF, `USB/DDR/PCIE`→highspeed

What it drives:
- **Impedance control**: RF/high-speed/fast-clock nets get a 50Ω target; the router SOLVES the trace width from the microstrip equation on the JLCPCB stackup (2-layer 1.6mm FR-4, Er 4.5 → 2.78mm for 50Ω)
- **Transmission-line checks**: rise-time vs critical length (Tpd ≈ 150ps/inch)
- **Crosstalk spacing**: 3W rule, 5W for RF/high-speed
- **SWR audit**: routed Z0 vs target (error >2, warning >1.5) — JLCPCB impedance tolerance is ±10%
- **Stub resonance**: branch length vs λ/20 at the net's frequency
- **Oscillation risk**: the net's measured LC self-resonance vs its operating frequency

## Power awareness

- `power_w` declared per component, or parsed from the value (`"0.25W"`, `"500mW"`, `"3W LED"`)
- **Placement**: every pair of components ≥0.5W gets apart ≥15mm (the constraint solver enforces it)
- **Thermal audit**: package θ_JA classes (DIP-8 85, SOIC-8 120, SOT-23 250, QFN 40 °C/W) → T_J = T_A + P·θ_JA vs the 125°C limit; ≥0.5W parts get a thermal-via budget (1 via per 1-2mm² of pad)
- **Board area**: high-power parts claim 50% extra courtyard area

## Schematic best practices (ERC-checked)

- **Decoupling**: every IC power net must contain a capacitor — `missing-decoupling` flags with the skill-102 guidance (100nF within 2mm of each IC power pin)
- **Power flags**: nets named like power without a power symbol flag `missing-power-flag` (power symbols are planned work; the flag is honest until then)

## Worked example: 555 LED blinker

```json
{
  "name": "555 LED blinker",
  "description": "555 timer astable blinking an LED at ~1Hz",
  "components": [
    {"reference": "U1", "value": "NE555", "lib_id": "Timer:NE555", "footprint": "Package_DIP:DIP-8_W7.62mm"},
    {"reference": "R1", "value": "10k", "lib_id": "Device:R", "footprint": "Resistor_SMD:R_0603_1608Metric"},
    {"reference": "R2", "value": "470k", "lib_id": "Device:R", "footprint": "Resistor_SMD:R_0603_1608Metric"},
    {"reference": "C1", "value": "1uF", "lib_id": "Device:C", "footprint": "Capacitor_SMD:C_0603_1608Metric"},
    {"reference": "C2", "value": "100nF", "lib_id": "Device:C", "footprint": "Capacitor_SMD:C_0603_1608Metric"},
    {"reference": "D1", "value": "red LED", "lib_id": "Device:LED", "footprint": "LED_SMD:LED_0603_1608Metric"},
    {"reference": "R3", "value": "330R", "lib_id": "Device:R", "footprint": "Resistor_SMD:R_0603_1608Metric"}
  ],
  "nets": [
    {"name": "VCC", "pins": ["U1:8", "R1:1", "R2:1", "C2:1"]},
    {"name": "GND", "pins": ["U1:1", "C1:2", "C2:2", "D1:2"]},
    {"name": "TRIG", "pins": ["U1:2", "R2:2", "C1:1"]},
    {"name": "OUT", "pins": ["U1:3", "R3:1"]},
    {"name": "LED_K", "pins": ["R3:2", "D1:1"]},
    {"name": "DIS", "pins": ["U1:7", "R1:2", "R2:1"]}
  ]
}
```

The 555's real pinout: 1=GND, 2=TRIG, 3=OUT, 4=RESET, 5=CTRL, 6=THRES, 7=DISCH, 8=VCC. Pin 4 ties to VCC, pin 5 optionally gets a 10nF to GND — add them for a complete design.

## Worked example: an RF net with declared frequency

```json
{"name": "RF_IN", "pins": ["J1:1", "U1:1", "C1:1"], "freq_hz": 2400000000, "role": "rf"}
```

This makes the router solve the 50Ω width, the SI audit measure SWR against the target, and — when the solved width exceeds what fine-pitch pads can accept — the build honestly reports the mismatch and counsels the 4-layer thin-dielectric stackup (JLCPCB's recommended flow for 50Ω RF).

## What the engine does with the plan (and never asks the planner to do)

- Board outline from the area budget (with thermal + impedance-corridor headroom)
- Component placement (semantic positions, groups, apart constraints, center-out packing by connectivity)
- Trace widths (solved from physics, neck-downs at fine pitches)
- Routing (A* grid router, power-first, impedance-first, vias with clearance halos)
- The honest-done gate: every stage's output re-checked by the next stage's own rules; the 6-gate export preflight (DRC, shorts, unrouted, pours, Gerbers, drill) is the final word on "orderable"