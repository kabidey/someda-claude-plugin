# Someda — Claude Code Plugin

**Make a PCB through vibe.** Describe a circuit in conversation; Claude plans it as a strict JSON contract (per-net frequencies, per-component power, real pinouts), and the compiled someda Rust engine does everything else — deterministic placement, physics-aware autorouting, JLCPCB scope checks, kicad-cli verification, and Gerber export. Every stage passes its own gate or the build says **NOT DONE** honestly.

```
you: /pcb-build a 555 timer blinking an LED at 1Hz with a proper power decoupling

claude: (plans the circuit: NE555 + timing RC + LED + 100nF decoupling, real pinouts)
someda: pin coverage ✓ placement ✓ routed 395/395 ✓ physics audit ✓
        preflight: DRC/shorts/unrouted/pours/gerbers/drill = ALL PASS
→ someda-build/circuit.kicad_pcb + fab/ Gerbers ready to send to JLCPCB
```

## Install

```bash
claude plugin marketplace add kabidey/someda-claude-plugin
claude plugin install someda@someda
```

The plugin resolves the compiled engine automatically: `someda` on PATH, the `SOMEDA_BIN` override, or it downloads the prebuilt release binary for your platform (Linux x86_64/arm64, macOS arm64/x86_64, Windows x86_64) on first use.

## Commands

| Command | What it does |
|---|---|
| `/pcb-build <description>` | Idea → fab-ready PCB: plan → place → route → physics audit → verify → Gerbers |
| `/pcb-plan <description>` | Write and show the plan JSON for review — no build |
| `/pcb-check <file>` | someda DRC/ERC on existing KiCad `.kicad_pcb` / `.kicad_sch` |

## The division of labor

**Claude is the planner** — real parts, datasheet pinouts, frequency and power declarations, sane circuit topology. No coordinates, ever.

**The compiled engine is the executor** — it owns all geometry:
- Placement: semantic constraints, connectivity packing, ≥0.5W parts separated ≥15mm
- Routing: trace widths solved from the microstrip equation on the JLCPCB stackup (50Ω → 2.78mm on 2-layer 1.6mm FR-4), impedance nets first, neck-downs at fine-pitch pads
- Physics audit: per-net frequency table, stray L/C measured from routed geometry, SWR vs targets, λ/20 stubs, oscillation risk, crosstalk, thermal junction temps
- Verification: kicad-cli ERC/DRC + the 6-gate export preflight — all six pass = orderable

## Why it's honest

Someda implements the honest-done contract: a build only claims done when its own re-verification agrees. Unrouted nets are reported with causes, SWR mismatches explain the stackup physics, thermal overloads say which part is cooking. Nothing is silently dropped.

## The engine

The binary is [someda](https://github.com/kabidey/someda) — a clean-room, KiCad-compatible EDA core in Rust (154 tests, live-probed KiCad format authority, physics validated against JLCPCB's published materials). The plugin is a thin orchestration layer: Claude plans, someda acts.

## License

MIT