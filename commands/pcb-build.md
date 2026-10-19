---
description: "Turn a circuit description into a fab-ready PCB — plan, place, route, physics-audit, verify, export Gerbers"
argument-hint: "DESCRIPTION OF THE CIRCUIT"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-someda.sh:*)", "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/fetch-libs.py:*)", "Bash(someda:*)", "Bash(${HOME}/.local/share/someda/bin/someda:*)", "Bash(kicad-cli:*)"]
---

# PCB Build — idea to fab-ready board

You are the circuit planner. The someda engine executes. Follow the [someda skill](../skills/someda/SKILL.md) contract exactly.

## 1. Resolve the engine

```!
SOMEDA=$("${CLAUDE_PLUGIN_ROOT}/scripts/setup-someda.sh")
echo "SOMEDA=${SOMEDA}"
```

## 2. Plan the circuit

Write `plan.json` for: **$ARGUMENTS**

Follow the contract in [CONTRACT.md](../skills/someda/references/CONTRACT.md):
- Real parts, real datasheet pinouts, `"REFDES:PIN"` pin references
- Declare `freq_hz`/`role` on nets whose frequency the intent knows
- Declare `power_w` on parts that dissipate
- 100nF decoupling on every IC power pin, `near` the IC
- Footprints are real KiCad `Lib:Name` footprints; pin numbers must match their pads
- Connectors get an edge `position`, an `edge_at` slot and a `rotation` facing outward, on the edge nearest their SoC pins
- 4/6-layer boards declare `layers`, `planes` and a `board` size
- Never emit coordinates

## 3. Fetch the libraries the plan needs (after the schematic is approved)

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch-libs.py" --plan plan.json --apply
```

Every component ends as FOUND, FETCHED (KiCad GitLab, LCSC/EasyEDA by `lcsc`/`mpn`, or an imported vendor zip) or MISSING with what to do. For a MISSING part: add `"lcsc": "C…"` or `"mpn"` to the plan, or download the KiCad zip from UltraLibrarian / SnapEDA / Mouser / Digi-Key and run `fetch-libs.py --import <zip> --apply`; then re-run. Never build with a MISSING footprint.

## 4. Build (the engine repairs and retries by itself)

```!
SOMEDA_PLAN_FILE=plan.json SOMEDA_PROJECT_DIR=./someda-build "${SOMEDA}" ai build "$ARGUMENTS"
```

The engine runs up to `SOMEDA_REPAIR_ROUNDS` (default 3) repair rounds on its own: footprint names corrected to the closest library footprint, a 100 nF capacitor added where ERC finds an IC rail without one, output capacitance added where a regulator's datasheet minimum is missing, the board grown (×1.15, at most twice) when parts overlap, connections stay unrouted or a pair fails — only when the plan fixes no `board` size. Inside a build it also moves an edge connector that finds no room to an adjacent edge and grows a split-plane island to reach its capacitors. Each change is a `repair:` line; the final plan it built is `someda-build/plan.built.json`. What it cannot fix it prints as `suggest:` lines with the exact plan edit (a bigger `board`, a part to move, a footprint to fetch) — apply those to `plan.json` verbatim and rebuild.

Custom footprints live in your own `.pretty` directory: add it with `SOMEDA_FOOTPRINT_DIRS=/path/to/lib`. If connections stay unrouted, rerun with `SOMEDA_ROUTE_DEBUG=2` to get occupancy maps around the failed pins, then fix the placement intent (edge, `edge_at`, `near`, board size).

```!
true
```

## 4. Report honestly

Read the stage table and the physics audit output. Report to the user:
- Routed connections, per-net frequency table, SI/thermal findings with their numbers
- Where files landed (schematic, board, fab/ Gerbers)
- Any stage failure with its physical meaning and the plan edit that would fix it — never claim done when a gate failed