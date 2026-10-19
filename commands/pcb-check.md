---
description: "Run someda's DRC/ERC on existing KiCad board or schematic files"
argument-hint: "PATH TO .kicad_pcb OR .kicad_sch"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-someda.sh:*)", "Bash(someda:*)", "Bash(${HOME}/.local/share/someda/bin/someda:*)"]
---

# PCB Check — DRC / ERC on existing files

Check: **$ARGUMENTS**

## 1. Resolve the engine

```!
SOMEDA=$("${CLAUDE_PLUGIN_ROOT}/scripts/setup-someda.sh")
echo "SOMEDA=${SOMEDA}"
```

## 2. Run the check

For a `.kicad_pcb`:

```!
"${SOMEDA}" validate "$ARGUMENTS"
```

For a `.kicad_sch`:

```!
"${SOMEDA}" erc "$ARGUMENTS"
```

## 3. Interpret

Report the findings honestly, classified:
- **Errors** — must be fixed before manufacturing; explain each finding's physical meaning
- **Warnings** — guidance; explain the physics (SI, thermal, decoupling)
- **Env-only findings** (missing KiCad symbol/footprint libraries) — not design problems; say so