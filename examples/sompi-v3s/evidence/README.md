# Build evidence — SomPi-V3s

Unedited outputs of one `someda ai build` run of `../plan.json`, kept here so the result in the
README can be checked rather than believed. Nothing in this directory was hand-edited after the
build. This is the 0.7.0 build: every differential pair routed as a coupled pair with its
measured intra-pair skew, 3W/5W crosstalk spacing enforced by the router and re-measured by the
audit, and the oscillation checks (termination, decoupling loops, regulators, crystals, PDN)
in the stage table.

## Provenance

| What | Value |
|---|---|
| Date | 2026-10-19 |
| Engine | kabidey/someda commit `1d11b951fee7` (Cargo version 0.7.0), `cargo build --release` |
| Plan | `examples/sompi-v3s/plan.json` from `gen_sompi.py` |
| Verifier | kicad-cli 10.0.6 (ERC, DRC with zones refilled, Gerber/drill/position/BOM export with solder mask subtracted from silk, 3D render) |
| Gerber renders | gerbonara 1.6.3 reading the files in `fab/` |
| Pair cross-sections | JLCPCB impedance calculator (jlcpcb.com/pcb-impedance-calculator, 2026-10-19), JLC06161H-3313 L1/L2: 90 Ω w 0.1466 / s 0.1778 mm, 100 Ω w 0.1191 / s 0.2032 mm |
| Command | `SOMEDA_FOOTPRINT_DIRS=../lib SOMEDA_PLAN_FILE=plan.json SOMEDA_PROJECT_DIR=out someda ai build "SomPi-V3s 6-layer SBC"` |

Reproduce: build the engine at that commit, run the command above in `examples/sompi-v3s/`, and
compare `SHA256SUMS` against your `out/fab/` and `out/circuit.kicad_*`. The engine is
deterministic (same plan in, same copper out); kicad-cli output may differ byte-wise between
KiCad versions in comments, timestamps and UUIDs, so compare the DRC summary and the Gerber
geometry rather than hashes when the KiCad version differs.

## Stage table (from `reports/build.log`)

```
  ✓ [plan] 132 components, 114 nets
  ✓ [footprints] 132 real KiCad library footprints, 6 copper layers
  ✓ [pin-coverage] every plan pin has a pad (500 pins across 132 footprints)
  ✓ [placement] placed 132 footprint(s) on 90x60mm, 128 hint(s), 0 courtyard overlap(s)
  ✓ [route] routed 187 of 187 connections (0 unrouted), 225 plane fanouts, 104 escape vias (32 unused)
  ✓ [pairs] 7 pair(s) declared, 7 trunk(s) coupled, 7 within skew budget
  ✓ [si-audit] 0 error(s), 2 warning(s); stray L/C measured per net
  ✓ [thermal-audit] 0 error(s), 1 warning(s)
  ✓ [stability-audit] 0 error(s), 5 warning(s): regulator output capacitance, crystal loads and traces, switch/feedback nodes
  ✓ [pdn-audit] 4 rail(s) swept 100 kHz–200 MHz, 0 above the ΔV/ΔI target (model: MLCC ESR/ESL classes + measured mounting loops; above 200 MHz the package/die decoupling owns the rail)
  ✓ [fab-scope] JLC06161H-3313: trace 0.127/0.127mm, via 0.35/0.2mm inside JLCPCB 6-layer scope (±10% impedance)
  ✓ [generate] wrote out/circuit.kicad_sch and out/circuit.kicad_pcb
  ✓ [kicad-erc] [exit 0]
  ✓ [kicad-drc] 0 error(s), 34 warning(s), 0 unconnected, 0 fab-blocking [silk_edge_clearance×2 via_dangling×32] [report circuit-drc.rpt]
  ✓ [export-gerbers] [exit 0] (13 Gerber layers written: 6 copper + mask/paste/silk/outline)
  ✓ [export-drill] [exit 0]
  ✓ [export-pos] [exit 0]
  ✓ [export-bom] [exit 0] — fab/bom-detailed.csv + fab/bom.md: 54 line items, 128 components, 8 with a part number
  ✓ [jlcpcb-package] fab/jlcpcb/jlcpcb-gerbers.zip (15 files: Protel names, no X2, mask-subtracted silk, merged Excellon + map), jlcpcb-bom.csv (54 lines, 4 with an LCSC part), jlcpcb-cpl.csv (125 SMD parts, rotation corrections on 11: D1 +180°, D2 +180°, Q1 +180°, U1 +270°, U2 +180°, U3 +180°, U4 +180°, U5 +180°, U6 +270°, U8 +180°, Y1 +180°) — check the SMT preview before ordering
  ✓ [render] render/board-top.png render/board-bottom.png render/board-iso.png — component bodies from /usr/share/kicad/3dmodels (128 of 128 referenced models found)
  ✓ [someda-erc] 5 finding(s) [5 = known power-symbol gap (M4)]
  ✓ [someda-drc] 0 error(s), 0 warning(s)
  ✓ [export-preflight] drc=PASS shorts=PASS unrouted=PASS pours=PASS gerbers=PASS drill=PASS
```

## Differential pairs (measured on the routed copper)

```
pair USB_DP_J/USB_DM_J: coupled 10.5 mm on F.Cu, tails ≤ 1.5 mm, len P 12.71 / N 13.35 mm, skew -0.649 mm (budget 1.100), 3 corner(s), 0 bump(s)
pair USB_DP/USB_DM: coupled 9.7 mm on F.Cu, tails ≤ 7.6 mm, len P 19.20 / N 18.67 mm, skew +0.522 mm (budget 1.100), 5 corner(s), 0 bump(s), P/N order differs at the two ends: far tails cross through a via
pair ETH_TXP/ETH_TXN: coupled 16.1 mm on F.Cu, tails ≤ 4.1 mm, len P 20.92 / N 20.91 mm, skew +0.010 mm (budget 0.250), 3 corner(s), 0 bump(s)
pair ETH_RXP/ETH_RXN: coupled 14.6 mm on F.Cu, tails ≤ 10.5 mm, len P 32.61 / N 32.60 mm, skew +0.010 mm (budget 0.250), 3 corner(s), 0 bump(s)
pair CAM_MCSI_D0P/CAM_MCSI_D0N: coupled 46.1 mm on F.Cu, tails ≤ 1.7 mm, len P 48.92 / N 48.92 mm, skew +0.000 mm (budget 0.150), 4 corner(s), 1 bump(s)
pair CAM_MCSI_D1P/CAM_MCSI_D1N: coupled 45.3 mm on F.Cu, tails ≤ 1.1 mm, len P 47.53 / N 47.53 mm, skew -0.000 mm (budget 0.150), 8 corner(s), 0 bump(s)
pair CAM_MCSI_CKP/CAM_MCSI_CKN: coupled 38.7 mm on F.Cu, tails ≤ 8.4 mm, len P 48.16 / N 48.16 mm, skew +0.000 mm (budget 0.150), 4 corner(s), 0 bump(s)
```

## Audit findings (errors and warnings, from `reports/build.log`)

```
[warning] decoupling-loop C14 (GND/+1V8): 3.90nH mounting loop — stubs 0.1mm (0.04nH) + 5.1mm (1.73nH), via pair 2.12nH; via / via
[warning] decoupling-loop C58 (GND/+1V8): 7.37nH mounting loop — stubs 0.1mm (0.04nH) + 22.7mm (4.16nH), via pair 3.17nH; via / via
[warning] density-too-high (board): density 147% > 70% — thermal crowding and router pain
[warning] switch-node U2_SW: 23.9 mm of copper, 2 via(s) — the di/dt loop: keep short (≤ 15 mm) and away from FB
[warning] crystal-trace X24M_IN: 10.7 mm, 2 via(s) — crystal nets: ≤ 10 mm, no vias, nothing fast nearby (18 pF load)
[warning] crystal-trace X24M_OUT: 14.4 mm, 3 via(s) — crystal nets: ≤ 10 mm, no vias, nothing fast nearby (18 pF load)
[warning] crystal-trace X32K_IN: 16.5 mm, 4 via(s) — crystal nets: ≤ 10 mm, no vias, nothing fast nearby (6 pF load)
[warning] crystal-trace X32K_OUT: 12.6 mm, 3 via(s) — crystal nets: ≤ 10 mm, no vias, nothing fast nearby (6 pF load)
```

## PDN per rail

```
[info] pdn +1V2: peak |Z| 0.191 Ω at 200.0 MHz vs target 0.480 Ω (10 capacitor(s))
[info] pdn +1V8: peak |Z| 0.390 Ω at 200.0 MHz vs target 1.034 Ω (8 capacitor(s))
[info] pdn +3V3: peak |Z| 0.127 Ω at 200.0 MHz vs target 2.853 Ω (13 capacitor(s))
[info] pdn VBUS: peak |Z| 0.601 Ω at 200.0 MHz vs target 3.571 Ω (1 capacitor(s))
```

## Contents

- `fab/` — the Gerber set (6 copper + mask/paste/silk/outline), Excellon drill + map, position file, kicad-cli BOM, and the detailed BOM `bom-detailed.csv` / `bom.md` (quantity, references, value, MPN, LCSC, package, footprint)
- `fab/jlcpcb/` — the JLCPCB order package: `jlcpcb-gerbers.zip` (Protel names, no X2, mask-subtracted silk, merged Excellon drill + map), `jlcpcb-bom.csv` (Comment, Designator, Footprint, LCSC Part #), `jlcpcb-cpl.csv` (Designator, Mid X, Mid Y, Layer, Rotation with the package rotation corrections the build log lists)
- `render/board-iso.png` — isometric 3D render with component bodies (KiCad packages3D plus the LCSC/EasyEDA models fetch-libs pulled for the USB-C, RJ45, audio jack and inductors; those four are flagged alignment-unverified)
- `kicad/` — the schematic, board and project kicad-cli judged
- `schematic/` — the schematic as kicad-cli exports it: PDF, per-sheet SVG, and the netlist it carries (the same connectivity the board was routed from)
- `reports/` — the build log and the kicad-cli DRC report
- `render/` — kicad-cli PNG renders, top and bottom
- `gerber-render/` — per-layer SVGs rendered from `fab/` by gerbonara
- `SHA256SUMS` — checksums of everything above
