---
name: someda
description: "Turn a circuit description in conversation into a fab-ready PCB. Use whenever the user wants to design, build, make, or route a PCB, circuit board, or electronics project; describe a circuit from an idea; check or fix DRC/ERC on KiCad files; export Gerbers for manufacturing; place and autoroute components; or analyze a board's signals, impedance, thermal, or JLCPCB manufacturability — even if they never say the word 'someda'. The compiled Rust engine does deterministic placement, physics-aware routing (per-net frequency, 50-ohm-where-needed, stray L/C measured), JLCPCB scope checks, kicad-cli verification, and Gerber export."
---

Someda is the deterministic PCB engine. Claude is the circuit planner; someda is the executor. You plan the circuit as a strict JSON contract, and the compiled engine turns it into a verified, fab-ready board — no coordinates from you, no hand-routing, no faked completion: every stage passes its own gate or the build says NOT DONE honestly.

# The contract you plan

Write a `plan.json` (see [CONTRACT.md](references/CONTRACT.md) for the full schema and worked examples):

```json
{
  "name": "555 LED blinker",
  "description": "one-line description",
  "components": [
    {"reference": "U1", "value": "NE555", "lib_id": "Timer:NE555", "footprint": "Package_DIP:DIP-8_W7.62mm"},
    {"reference": "R1", "value": "10k", "lib_id": "Device:R", "footprint": "Resistor_SMD:R_0603_1608Metric", "power_w": 0.25}
  ],
  "nets": [
    {"name": "VCC", "pins": ["U1:1", "R1:1"]},
    {"name": "RF_OUT", "pins": ["U1:3", "J1:1"], "freq_hz": 2400000000, "role": "rf"}
  ]
}
```

Rules:
- Every pin is `"REFDES:PIN_NUMBER"` (e.g. `"U1:3"`); every pin must belong to a listed component
- Power nets are named `"VCC"` and `"GND"`
- **Declare each net's `freq_hz` when the circuit's intent knows it** (clocks, RF, high-speed) and a `role` (`power|ground|clock|rf|highspeed|analog|digital`) when the name alone is ambiguous — the router sizes impedance-controlled traces from this
- **Declare `power_w` for parts that dissipate noticeably** (regulators, power LEDs, resistors in power paths) — the placer separates hot parts ≥15mm and the thermal audit checks junction temps
- Include a 100nF decoupling capacitor on every IC's power pin (the ERC flags missing decoupling per skill-102 best practice)
- Never output x/y coordinates — the deterministic solver owns all geometry

# Step 0 — Resolve the engine

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/setup-someda.sh"
```

This finds `someda` on PATH, honors `SOMEDA_BIN`, or downloads the compiled release binary for the user's platform (Linux x86_64/arm64, macOS arm64/x86_64, Windows x86_64). Use the returned path as `$SOMEDA` below.

# Step 1 — Plan (you are the planner)

Read the user's description carefully and write `plan.json`:
- Real part numbers and values (E12 resistors, standard caps, real ICs)
- Real pin numbers from the part's datasheet pinout
- Per-net frequency/role declarations where the intent knows them
- Per-component power where it matters
- Sane circuit design: decoupling, pull-ups where needed, correct topologies

If the user's description is ambiguous about something that changes the plan materially (pinout, supply voltage, part choice), ask ONE focused question. Otherwise make the conventional choice and note it.

# Step 2 — Build (the engine does everything else)

```bash
SOMEDA_PLAN_FILE=plan.json "$SOMEDA" ai build "<the user's description>"
```

The engine runs:
1. Plan validation + **pin coverage** — every plan pin must exist as a pad
2. **Deterministic placement** — the solver owns geometry; ≥0.5W parts get ≥15mm apart
3. **Physics-aware routing** — per-net widths solved from the microstrip equation on the JLCPCB stackup (50Ω → 2.78mm on 2-layer 1.6mm FR-4); impedance nets route first; neck-downs at fine-pitch pads; power-first ordering
4. **Physics audit** — every net's frequency table; stray L/C measured from routed geometry; SWR vs impedance targets; λ/20 stub resonance; LC self-resonance oscillation risk; crosstalk parallel-runs; thermal junction temps; JLCPCB fab-scope check
5. **kicad-cli verification** (if installed): ERC, DRC, and Gerber/drill/BOM exports
6. **The 6-gate export preflight** — DRC + shorts + unrouted + pours + Gerbers + drill; all six pass = orderable, anything else = NOT DONE, honestly

Output lands in `./someda-build/` (override with `SOMEDA_PROJECT_DIR`): `circuit.kicad_sch`, `circuit.kicad_pcb`, `fab/` with Gerbers + drill + BOM.

# Step 3 — Read the honest results

The build prints a stage table. Interpret it for the user:
- **All ✓**: present the board summary — components, nets, routed connections, per-net frequency table, SI/thermal findings (warnings are guidance; errors mean fix the plan), the Gerber outputs, and what the physics audit measured
- **Physics errors** (SWR, thermal-overlimit): explain the physics honestly. Common cases:
  - `swr-error` on an RF net: single-ended 50Ω on 2-layer 1.6mm FR-4 needs 2.78mm traces that cannot land on fine-pitch pads. The harness counsels the 4-layer thin-dielectric stackup — tell the user this is a real stackup decision, not a bug
  - `thermal-overlimit`: the part genuinely needs heatsinking/vias or a bigger package — suggest the fix in the plan (bigger package, lower power, thermal vias)
  - `missing-decoupling`: add the 100nF cap to the plan and rebuild — one plan edit, no rerouting
- **Unrouted nets**: congestion is a placement conversation — the engine reports it honestly. Simplify the plan (fewer parts per net, different topology) or accept the unrouted report

# Commands

- `/pcb-build <description>` — idea to fab-ready PCB in one shot
- `/pcb-plan <description>` — write and show the plan JSON for review, no build
- `/pcb-check <board or schematic>` — run someda's DRC/ERC on existing KiCad files

# What you must never do

- Never emit x/y coordinates in the plan — the solver owns geometry
- Never split a net into star links or shrink the board to help the router — fix the placement intent instead
- Never claim done when a stage failed — read the stage table and report honestly
- Never invent pin numbers — look them up from the part's real pinout
- Never fabricate measurements — read the engine's printed values and cite them