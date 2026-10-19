---
description: "Write and show the circuit plan JSON for review — no build, no API key"
argument-hint: "DESCRIPTION OF THE CIRCUIT"
allowed-tools: ["Write"]
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

Show the plan to the user with a short explanation of the circuit topology and the key declarations (frequencies, power, impedance-controlled nets). Note anything you chose conventionally that the user may want to change.

Do NOT build — the user reviews first, then runs `/pcb-build`.