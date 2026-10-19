---
description: "Write and show the circuit plan JSON for review — no build, no API key"
argument-hint: "DESCRIPTION OF THE CIRCUIT"
allowed-tools: ["Write", "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-someda.sh:*)", "Bash(someda:*)", "Bash(${HOME}/.local/share/someda/bin/someda:*)", "Bash(kicad-cli:*)"]
---

# PCB Plan — review before building

You are the circuit planner. Write `plan.json` for: **$ARGUMENTS**

Follow the [someda contract](../skills/someda/references/CONTRACT.md) exactly:
- Real parts with datasheet pinouts (`"REFDES:PIN"` references)
- `freq_hz`/`role` declarations where the circuit's intent knows the frequency
- `power_w` on dissipating parts
- 100nF decoupling on every IC power pin, `near` the IC
- Real KiCad `Lib:Name` footprints with matching pad numbers
- Connector edges (`position`, `edge_at`, `rotation`), `layers`/`planes`/`board` for multilayer boards
- Never coordinates

Then generate the schematic for review (no board, no network):

```!
SOMEDA=$("${CLAUDE_PLUGIN_ROOT}/scripts/setup-someda.sh")
SOMEDA_STOP_AFTER=schematic SOMEDA_PLAN_FILE=plan.json SOMEDA_PROJECT_DIR=./someda-build "${SOMEDA}" ai build "$ARGUMENTS"
kicad-cli sch export pdf --output ./someda-build/schematic.pdf ./someda-build/circuit.kicad_sch
```

Show the plan to the user with a short explanation of the circuit topology, the key declarations (frequencies, pairs, terminations, power, part numbers) and the schematic PDF path (`someda-build/schematic.pdf`). Note anything you chose conventionally that the user may want to change.

Do NOT build the board — the user approves the schematic first, then runs `/pcb-build`, which fetches the libraries and builds.