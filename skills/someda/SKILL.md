---
name: someda
description: "Turn a circuit description in conversation into a fab-ready PCB. Use whenever the user wants to design, build, make, or route a PCB, circuit board, or electronics project; describe a circuit from an idea; check or fix DRC/ERC on KiCad files; export Gerbers for manufacturing; place and autoroute components; or analyze a board's signals, impedance, thermal, or JLCPCB manufacturability — even if they never say the word 'someda'. The compiled Rust engine uses real KiCad library footprints, places by courtyard and connectivity, routes 2/4/6-layer boards with copper planes, escape vias, coupled differential pairs and enforced crosstalk spacing, audits SI/thermal/stability, verifies through kicad-cli DRC and exports the JLCPCB Gerber set."
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
- Real part numbers and values (E12 resistors, standard caps, real ICs); `mpn` on every non-generic part and `lcsc` (LCSC part number) when known — the BOM, the JLCPCB assembly files and the library fetch use them
- Real pin numbers from the part's datasheet pinout — and matching the footprint's pad numbers
- Per-net frequency/role declarations where the intent knows them
- Per-component power where it matters
- Sane circuit design: decoupling, pull-ups where needed, correct topologies
- For 4/6-layer boards: `layers`, `planes` (GND on In1.Cu; the main rail on In3.Cu; a second GND or a split power island with `"region": "auto"` and `priority`), a `board` size, and an edge `position` (+ `edge_at` slot) for every connector on the edge nearest its SoC pins — no `rotation`: the engine reads the connector's opening from the footprint geometry, turns it toward the edge and sets the courtyard flush with the edge (`edge_overhang_mm` when the datasheet wants the shell past the edge, e.g. 0.8 for a USB-C receptacle); it prints each decision
- Every differential interface declared in `pairs` (USB 90 Ω; Ethernet, MIPI, LVDS, PCIe 100 Ω) — one pair per net segment (SoC→ESD and ESD→connector are two pairs); series terminations on fast single-ended clocks (a 22–33 Ω resistor at the driver) or a `termination` declaration

If the user's description is ambiguous about something that changes the plan materially (pinout, supply voltage, part choice), ask ONE focused question. Otherwise make the conventional choice and note it.

# Step 2 — Schematic for approval, libraries, then the build

1. `SOMEDA_STOP_AFTER=schematic SOMEDA_PLAN_FILE=plan.json "$SOMEDA" ai build "<description>"` writes the schematic (readable column layout on the smallest fitting sheet, labelled pins, project symbol library); export it with `kicad-cli sch export pdf` and show the user the PDF path. The user approves or edits the plan.
2. `python3 "$CLAUDE_PLUGIN_ROOT/scripts/fetch-libs.py" --plan plan.json --apply` pulls every footprint and 3D model the plan needs that the local KiCad libraries lack: KiCad's GitLab repositories, LCSC/EasyEDA by `lcsc` (or `mpn` resolved through JLCPCB's parts search), and KiCad zips you downloaded from UltraLibrarian, SnapEDA, Mouser or Digi-Key (`--import`). It never guesses: every part ends FOUND, FETCHED (with its source) or MISSING with the plan edit to make. Do not build with a MISSING footprint.
3. ```bash
   SOMEDA_PLAN_FILE=plan.json "$SOMEDA" ai build "<the user's description>"
   ```
   The engine runs its own repair rounds (`SOMEDA_REPAIR_ROUNDS`, default 3): closest-library-footprint substitution, a 100 nF capacitor added where ERC finds an IC rail without one, output capacitance added where a regulator's datasheet minimum is missing, the board grown (×1.15, at most twice) when parts overlap, connections stay unrouted or a pair fails — only when the plan fixes no `board` size. Within a build it also moves an edge connector that finds no room to an adjacent edge (re-oriented from its footprint) and grows a split-plane island to reach its decoupling capacitors. It prints `repair:` lines for what it changed and `suggest:` lines (exact plan edits) for what it could not; the plan it finally built is `someda-build/plan.built.json`. Apply the `suggest:` edits verbatim to `plan.json` and rebuild; never hand-edit coordinates or rotations — edge connectors are rotated toward their edge by the engine from the footprint geometry.

The engine runs:
1. Plan validation, **footprint resolution** (real library geometry or reported synthetic fallback) and **pin coverage** — every plan pin must exist as a pad
2. **Deterministic placement** — real courtyards, connectors flush to their edges, parts next to the pins they connect to, keep-out ring around fine-pitch ICs for escape vias, hot parts ≥15mm apart; no courtyard overlaps
3. **Routing** — design rules per layer count (2-layer: 0.25/0.2mm, 0.6/0.3 via; 4/6-layer: 0.127/0.127mm, 0.35/0.2 via — JLCPCB scope); copper planes on inner layers with per-pad fanout vias; depth-staggered escape vias for every fine-pitch signal pin; keep-out zones from footprints honoured; **differential pairs first** as coupled corridors over a solid plane with matched lengths (fab-table cross-sections); **3W/5W crosstalk spacing enforced** for every fast net outside pad/escape breakouts; impedance nets at widths solved from the stackup, confined to plane-referenced layers; rip-up and reroute
4. **Physics audit** — per-net frequency table; stray L/C measured from routed geometry; SWR vs targets; λ/20 stubs; unterminated transmission lines; crosstalk measured on the routed copper with the router's breakout zones; per-capacitor decoupling loop inductance; regulator/crystal/switch-node stability checks; per-rail PDN |Z(f)| vs target; thermal junction temps; JLCPCB fab-scope check
5. **kicad-cli verification**: ERC, DRC with zones refilled (judged from the report file: errors and unconnected items fail, warnings are listed), Gerber set for every copper layer + mask/paste/silk/outline, drill + map, position file, kicad-cli BOM plus the detailed BOM (`fab/bom-detailed.csv`, `fab/bom.md`: qty, references, value, MPN, LCSC, package), the **JLCPCB order package** (`fab/jlcpcb/`: Gerber zip with Protel names and no X2, merged Excellon drill, assembly BOM and CPL with per-package rotation corrections — the build lists the corrections; check JLCPCB's SMT preview), and **3D renders with component bodies** (`render/board-iso.png`, top, bottom; the stage fails when a referenced 3D model is missing — fetch-libs is the fix)
6. **The 6-gate export preflight** — DRC + shorts + unrouted + pours + Gerbers + drill; all six pass = orderable, anything else = NOT DONE, honestly

Output lands in `./someda-build/` (override with `SOMEDA_PROJECT_DIR`): `circuit.kicad_sch`, `circuit.kicad_pcb`, `circuit.kicad_pro` (the rules kicad-cli judged by), `fab/` with Gerbers + drill + BOM + positions, `render/` with PNGs.

# Step 3 — Read the honest results

The build prints a stage table. Interpret it for the user:
- **All ✓**: present the board summary — components, nets, routed connections, fanouts and escape vias, per-net frequency table, SI/thermal findings (warnings are guidance; errors mean fix the plan), the Gerber outputs, and what the physics audit measured
- **`footprints` ✗**: a footprint name did not resolve; fix the `Lib:Name` (list the library directory) and rebuild
- **`placement` ✗ (courtyard overlap)**: the board is too small for the parts; grow `board` or drop parts
- **Unrouted connections**: the build prints every failed connection with its endpoints; `SOMEDA_ROUTE_DEBUG=2` prints occupancy maps around them. Usual causes: a connector on the wrong edge for its pins, too many parts `near` one IC, or a board too small. Move the connector, give parts `edge_at` slots, or grow the board
- **`kicad-drc` ✗**: read the codes in the stage detail (`clearance`, `hole_clearance`, `items_not_allowed`…) — these are KiCad's own findings on the written board
- **`pairs` ✗**: a declared pair was not routed as a coupled pair, or its measured intra-pair skew exceeds the budget — the build prints each trunk's coupled length, tails, lengths and skew. Give the pair's components room (`edge_at`, `near`), keep the two ends on the same side of the board, or relax `skew_mm` only when the interface really allows it
- **Physics errors** (`swr-error`, `crosstalk-violation`, `unterminated-line`, `decoupling-loop`, `regulator-output-cap`, `crystal-load`, `thermal-overlimit`): explain the physics honestly and propose the plan edit (a series resistor, a capacitor moved `near` its IC, a larger output capacitor)

What the engine does NOT do, and you must say so when it matters: pair-to-pair (clock-to-data) length matching across different pairs; vias inside the coupled section (a pair stays on one layer, its tails may change layer); no electrical simulation or timing; pinouts are only as right as the plan — a wrong but consistent pin number passes every gate.

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
