---
description: "Turn a circuit description into a fab-ready PCB — plan, place, route, physics-audit, verify, export Gerbers"
argument-hint: "DESCRIPTION OF THE CIRCUIT"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-someda.sh:*)", "Bash(someda:*)", "Bash(${HOME}/.local/share/someda/bin/someda:*)"]
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
- 100nF decoupling on every IC power pin
- Never emit coordinates

## 3. Build

```!
SOMEDA_PLAN_FILE=plan.json SOMEDA_PROJECT_DIR=./someda-build "${SOMEDA}" ai build "$ARGUMENTS"
```

## 4. Report honestly

Read the stage table and the physics audit output. Report to the user:
- Routed connections, per-net frequency table, SI/thermal findings with their numbers
- Where files landed (schematic, board, fab/ Gerbers)
- Any stage failure with its physical meaning and the plan edit that would fix it — never claim done when a gate failed