---
name: someda
description: "Turn a circuit description in conversation into a fab-ready PCB. Use whenever the user wants to design, build, make, or route a PCB, circuit board, or electronics project; describe a circuit from an idea; check or fix DRC/ERC on KiCad files; export Gerbers for manufacturing; place and autoroute components; or analyze a board's signals, impedance, thermal, or JLCPCB manufacturability — even if they never say the word 'someda'. The compiled Rust engine uses real KiCad library footprints, places by courtyard and connectivity, routes 2/4/6-layer boards with copper planes and escape vias, audits SI/thermal, verifies through kicad-cli DRC and exports the JLCPCB Gerber set."
---

Someda is the deterministic PCB engine. Claude is the circuit planner; someda is the executor. You plan the circuit as a strict JSON contract, and the compiled engine turns it into a verified, fab-ready board — no coordinates from you, no hand-routing, no faked completion: every stage passes its own gate or the build says NOT DONE honestly.

# The contract you plan

Write a `plan.json` (see [CONTRACT.md](references/CONTRACT.md) for the full schema and worked examples):

```json
{
  "name": "555 LED blinker",
  "description": "one-line description",
  "layers": 2,
  "components": [
    {"reference": "U1", "value": "NE555", "lib_id": "Timer:NE555", "footprint": "Package_DIP:DIP-8_W7.62mm"},
    {"reference": "C2", "value": "100nF", "lib_id": "Device:C", "footprint": "Capacitor_SMD:C_0603_1608Metric", "near": "U1"},
    {"reference": "J1", "value": "USB-C", "lib_id": "Connector:USB_C_Receptacle_USB2.0_16P", "footprint": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "position": "left_edge", "edge_at": 0.3, "rotation": 270}
  ],
  "nets": [
    {"name": "VCC", "pins": ["U1:8", "C2:1"]},
    {"name": "RF_OUT", "pins": ["U1:3", "J1:A6"], "freq_hz": 2400000000, "role": "rf"}
  ]
}
```

Rules:
- Every pin is `"REFDES:PIN_NUMBER"` (e.g. `"U1:3"`, `"J1:A6"`, `"J1:SH"`); every pin must belong to a listed component and must exist as a pad of its footprint — the pin-coverage gate rejects a plan whose pin numbers the footprint does not have
- **Footprints are real KiCad library footprints**: `"Lib:Name"` resolved from the installed KiCad footprint libraries (plus any `SOMEDA_FOOTPRINT_DIRS`). Pad numbers come from the footprint, so look them up (`grep '(pad "' /usr/share/kicad/footprints/Lib.pretty/Name.kicad_mod`). A footprint that does not resolve gets synthetic pads and the `footprints` stage reports it as NOT orderable
- Power nets are named `"VCC"`/`"GND"` for 2-layer boards; on 4/6-layer boards name the rails as they are (`"+3V3"`, `"+1V2"`, `"GND"`) and declare `planes`
- **Declare each net's `freq_hz` when the circuit's intent knows it** (clocks, RF, high-speed) and a `role` (`power|ground|clock|rf|highspeed|analog|digital`) when the name alone is ambiguous — the router sizes impedance-controlled traces from this
- **Declare `power_w` for parts that dissipate noticeably** (regulators, SoCs, power LEDs) — the placer separates hot parts and the thermal audit checks junction temps
- Include a 100nF decoupling capacitor on every IC's power pin, `"near"` the IC — the placer puts it next to the pins it shares a net with
- Give connectors a semantic `position` (`left_edge`, `top_edge`, …), an `edge_at` fraction along that edge, and a `rotation` so the opening faces outward; put connectors on the edge nearest the SoC pins they connect to — placement is 80% of routing
- Never output x/y coordinates — the deterministic solver owns all geometry

# Step 0 — Resolve the engine

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/setup-someda.sh"
```

This finds `someda` on PATH, honors `SOMEDA_BIN`, downloads the compiled release binary for the user's platform (Linux x86_64/arm64, macOS arm64/x86_64, Windows x86_64), or builds it from source with cargo when no release matches. Use the returned path as `$SOMEDA` below. The engine needs `kicad-cli` (KiCad 8+) and the KiCad footprint libraries installed for DRC, Gerbers and real footprints.

# Step 1 — Plan (you are the planner)

Read the user's description carefully and write `plan.json`:
- Real part numbers and values (E12 resistors, standard caps, real ICs)
- Real pin numbers from the part's datasheet pinout — and matching the footprint's pad numbers
- Per-net frequency/role declarations where the intent knows them
- Per-component power where it matters
- Sane circuit design: decoupling, pull-ups where needed, correct topologies
- For 4/6-layer boards: `layers`, `planes` (GND on In1.Cu; the main rail on In3.Cu; a second GND or a split power island with `"region": "auto"` and `priority`), a `board` size, and edge positions for every connector

If the user's description is ambiguous about something that changes the plan materially (pinout, supply voltage, part choice), ask ONE focused question. Otherwise make the conventional choice and note it.

# Step 2 — Build (the engine does everything else)

```bash
SOMEDA_PLAN_FILE=plan.json "$SOMEDA" ai build "<the user's description>"
```

The engine runs:
1. Plan validation, **footprint resolution** (real library geometry or reported synthetic fallback) and **pin coverage** — every plan pin must exist as a pad
2. **Deterministic placement** — real courtyards, connectors flush to their edges, parts next to the pins they connect to, keep-out ring around fine-pitch ICs for escape vias, hot parts ≥15mm apart; no courtyard overlaps
3. **Routing** — design rules per layer count (2-layer: 0.25/0.2mm, 0.6/0.3 via; 4/6-layer: 0.127/0.127mm, 0.35/0.2 via — JLCPCB scope); copper planes on inner layers with per-pad fanout vias; depth-staggered escape vias for every fine-pitch signal pin; keep-out zones from footprints honoured; impedance nets at widths solved from the stackup; rip-up and reroute
4. **Physics audit** — per-net frequency table; stray L/C measured from routed geometry; SWR vs targets; λ/20 stubs; LC self-resonance; crosstalk parallel-runs; thermal junction temps; JLCPCB fab-scope check
5. **kicad-cli verification**: ERC, DRC with zones refilled (judged from the report file: errors and unconnected items fail, warnings are listed), Gerber set for every copper layer + mask/paste/silk/outline, drill + map, position file, BOM, top/bottom PNG renders
6. **The 6-gate export preflight** — DRC + shorts + unrouted + pours + Gerbers + drill; all six pass = orderable, anything else = NOT DONE, honestly

Output lands in `./someda-build/` (override with `SOMEDA_PROJECT_DIR`): `circuit.kicad_sch`, `circuit.kicad_pcb`, `circuit.kicad_pro` (the rules kicad-cli judged by), `fab/` with Gerbers + drill + BOM + positions, `render/` with PNGs.

# Step 3 — Read the honest results

The build prints a stage table. Interpret it for the user:
- **All ✓**: present the board summary — components, nets, routed connections, fanouts and escape vias, per-net frequency table, SI/thermal findings (warnings are guidance; errors mean fix the plan), the Gerber outputs, and what the physics audit measured
- **`footprints` ✗**: a footprint name did not resolve; fix the `Lib:Name` (list the library directory) and rebuild
- **`placement` ✗ (courtyard overlap)**: the board is too small for the parts; grow `board` or drop parts
- **Unrouted connections**: the build prints every failed connection with its endpoints; `SOMEDA_ROUTE_DEBUG=2` prints occupancy maps around them. Usual causes: a connector on the wrong edge for its pins, too many parts `near` one IC, or a board too small. Move the connector, give parts `edge_at` slots, or grow the board
- **`kicad-drc` ✗**: read the codes in the stage detail (`clearance`, `hole_clearance`, `items_not_allowed`…) — these are KiCad's own findings on the written board
- **Physics errors** (`swr-error`, `thermal-overlimit`, `missing-decoupling`): explain the physics honestly and propose the plan edit

What the engine does NOT do, and you must say so when it matters: differential pairs are routed as two single-ended traces (USB, Ethernet, MIPI, LVDS get no pair coupling or length matching); no electrical simulation or timing; pinouts are only as right as the plan — a wrong but consistent pin number passes every gate.

# Commands

- `/pcb-build <description>` — idea to fab-ready PCB in one shot
- `/pcb-plan <description>` — write and show the plan JSON for review, no build
- `/pcb-check <board or schematic>` — run someda's DRC/ERC on existing KiCad files

# What you must never do

- Never emit x/y coordinates in the plan — the solver owns geometry
- Never split a net into star links or shrink the board to help the router — fix the placement intent instead
- Never claim done when a stage failed — read the stage table and report honestly
- Never invent pin numbers — look them up from the part's real pinout and the footprint's pad list
- Never fabricate measurements — read the engine's printed values and cite them
