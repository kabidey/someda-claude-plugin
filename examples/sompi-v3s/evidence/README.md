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
| Engine | kabidey/someda commit `6aff8dd0c8b5` (Cargo version 0.7.0), `cargo build --release` |
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
  ✓ [route] routed 194 of 194 connections (0 unrouted), 218 plane fanouts, 101 escape vias (31 unused)
  ✓ [pairs] 7 pair(s) declared, 7 trunk(s) coupled, 7 within skew budget
  ✓ [si-audit] 0 error(s), 5 warning(s); stray L/C measured per net
  ✓ [thermal-audit] 0 error(s), 1 warning(s)
  ✓ [stability-audit] 0 error(s), 5 warning(s): regulator output capacitance, crystal loads and traces, switch/feedback nodes
  ✓ [pdn-audit] 5 rail(s) swept 100 kHz–200 MHz, 0 above the ΔV/ΔI target (model: MLCC ESR/ESL classes + measured mounting loops; above 200 MHz the package/die decoupling owns the rail)
  ✓ [fab-scope] JLC06161H-3313: trace 0.127/0.127mm, via 0.35/0.2mm inside JLCPCB 6-layer scope (±10% impedance)
  ✓ [generate] wrote out/circuit.kicad_sch and out/circuit.kicad_pcb
  ✓ [kicad-erc] [exit 5]
  ✓ [kicad-drc] 0 error(s), 31 warning(s), 0 unconnected, 0 fab-blocking [via_dangling×31] [report circuit-drc.rpt]
  ✓ [export-gerbers] [exit 0] (13 Gerber layers written: 6 copper + mask/paste/silk/outline)
  ✓ [export-drill] [exit 0]
  ✓ [export-pos] [exit 0]
  ✓ [export-bom] [exit 0]
  ✓ [render] render/board-top.png render/board-bottom.png [exit 0]
  ✓ [someda-erc] 4 finding(s) [4 = known power-symbol gap (M4)]
  ✓ [someda-drc] 0 error(s), 0 warning(s)
  ✓ [export-preflight] drc=PASS shorts=PASS unrouted=PASS pours=PASS gerbers=PASS drill=PASS
```

## Differential pairs (measured on the routed copper)

```
pair USB_DP_J/USB_DM_J: coupled 4.4 mm on F.Cu, tails ≤ 7.1 mm, len P 12.32 / N 12.72 mm, skew -0.395 mm (budget 1.100), 1 corner(s), 0 bump(s)
pair USB_DP/USB_DM: coupled 20.2 mm on F.Cu, tails ≤ 5.3 mm, len P 25.55 / N 25.53 mm, skew +0.014 mm (budget 1.100), 3 corner(s), 0 bump(s), P/N order differs at the two ends: far tails cross through a via
pair ETH_TXP/ETH_TXN: coupled 16.9 mm on F.Cu, tails ≤ 4.3 mm, len P 21.94 / N 21.93 mm, skew +0.010 mm (budget 0.250), 1 corner(s), 0 bump(s)
pair ETH_RXP/ETH_RXN: coupled 15.2 mm on F.Cu, tails ≤ 10.5 mm, len P 34.01 / N 34.12 mm, skew -0.117 mm (budget 0.250), 3 corner(s), 0 bump(s)
pair CAM_MCSI_D0P/CAM_MCSI_D0N: coupled 29.8 mm on F.Cu, tails ≤ 1.7 mm, len P 32.54 / N 32.54 mm, skew +0.000 mm (budget 0.150), 4 corner(s), 1 bump(s)
pair CAM_MCSI_D1P/CAM_MCSI_D1N: coupled 27.2 mm on F.Cu, tails ≤ 17.1 mm, len P 46.00 / N 45.88 mm, skew +0.127 mm (budget 0.150), 4 corner(s), 0 bump(s)
pair CAM_MCSI_CKP/CAM_MCSI_CKN: coupled 25.4 mm on F.Cu, tails ≤ 9.4 mm, len P 40.41 / N 40.41 mm, skew +0.000 mm (budget 0.150), 8 corner(s), 0 bump(s)
```

## Audit findings (errors and warnings, from `reports/build.log`)

```
[warning] decoupling-loop C12 (GND/+1V8): 4.40nH mounting loop — stubs 0.1mm (0.04nH) + 6.2mm (2.12nH), via pair 2.23nH; via / via
[warning] decoupling-loop C13 (GND/+1V8): 7.66nH mounting loop — stubs 0.1mm (0.04nH) + 15.6mm (5.33nH), via pair 2.28nH; via / via
[warning] decoupling-loop C14 (GND/+1V8): 5.59nH mounting loop — stubs 0.1mm (0.04nH) + 8.8mm (2.99nH), via pair 2.56nH; via / via
[warning] decoupling-loop C50 (GND/+1V8): 3.41nH mounting loop — stubs 0.1mm (0.04nH) + 7.7mm (2.64nH), via pair 0.73nH; via / no via
[warning] decoupling-loop C58 (GND/+1V8): 6.25nH mounting loop — stubs 0.1mm (0.04nH) + 16.4mm (5.59nH), via pair 0.61nH; via / no via
[warning] density-too-high (board): density 147% > 70% — thermal crowding and router pain
[warning] switch-node U2_SW: 16.6 mm of copper, 3 via(s) — the di/dt loop: keep short (≤ 15 mm) and away from FB
[warning] crystal-trace X24M_IN: 28.7 mm, 4 via(s) — crystal nets: ≤ 10 mm, no vias, nothing fast nearby (18 pF load)
[warning] crystal-trace X24M_OUT: 18.4 mm, 3 via(s) — crystal nets: ≤ 10 mm, no vias, nothing fast nearby (18 pF load)
[warning] crystal-trace X32K_IN: 16.9 mm, 4 via(s) — crystal nets: ≤ 10 mm, no vias, nothing fast nearby (6 pF load)
[warning] crystal-trace X32K_OUT: 9.8 mm, 3 via(s) — crystal nets: ≤ 10 mm, no vias, nothing fast nearby (6 pF load)
```

## PDN per rail

```
[info] pdn +1V2: peak |Z| 0.194 Ω at 200.0 MHz vs target 0.480 Ω (10 capacitor(s))
[info] pdn +1V8: peak |Z| 0.400 Ω at 200.0 MHz vs target 1.034 Ω (9 capacitor(s))
[info] pdn +3V0: peak |Z| 0.378 Ω at 200.0 MHz vs target 6.000 Ω (4 capacitor(s))
[info] pdn +3V3: peak |Z| 0.115 Ω at 200.0 MHz vs target 2.853 Ω (15 capacitor(s))
[info] pdn VBUS: peak |Z| 0.688 Ω at 200.0 MHz vs target 3.571 Ω (3 capacitor(s))
```

## Contents

- `fab/` — the Gerber set (6 copper + mask/paste/silk/outline), Excellon drill + map, position file, BOM
- `kicad/` — the schematic, board and project kicad-cli judged
- `reports/` — the build log and the kicad-cli DRC report
- `render/` — kicad-cli PNG renders, top and bottom
- `gerber-render/` — per-layer SVGs rendered from `fab/` by gerbonara
- `SHA256SUMS` — checksums of everything above
