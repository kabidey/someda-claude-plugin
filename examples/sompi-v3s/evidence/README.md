# Build evidence — SomPi-V3s

Unedited outputs of one `someda ai build` run of `../plan.json`, kept here so the result in the
README can be checked rather than believed. Nothing in this directory was hand-edited after the
build.

## Provenance

| What | Value |
|---|---|
| Date | 2026-10-19 |
| Engine | kabidey/someda commit `d7713385b6c3` (branch `feat/multilayer-real-footprints`, Cargo version 0.6.0), `cargo build --release` |
| Plugin / plan | kabidey/someda-claude-plugin commit `6c3171bf7ad8` — `examples/sompi-v3s/plan.json` from `gen_sompi.py` |
| Verifier | kicad-cli 10.0.6 (ERC, DRC with zones refilled, Gerber/drill/position/BOM export, 3D render) |
| Gerber renders | gerbonara 1.6.3 reading the files in `fab/` |
| Command | `SOMEDA_FOOTPRINT_DIRS=../lib SOMEDA_PLAN_FILE=plan.json SOMEDA_PROJECT_DIR=out someda ai build "SomPi V3s 6-layer SBC"` |
| Wall time | about 70 s on the build machine (routing plus kicad-cli) |

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
  ✓ [route] routed 192 of 192 connections (0 unrouted), 220 plane fanouts, 130 escape vias
  ✓ [si-audit] 0 error(s), 54 warning(s); stray L/C measured per net
  ✓ [thermal-audit] 0 error(s), 1 warning(s)
  ✓ [fab-scope] JLC06161H-3313: trace 0.127/0.127mm, via 0.35/0.2mm inside JLCPCB 6-layer scope (±10% impedance)
  ✓ [generate] wrote /root/pcb/sompi/board/out/circuit.kicad_sch and /root/pcb/sompi/board/out/circuit.kicad_pcb
  ✓ [kicad-erc] [exit 5]
  ✓ [kicad-drc] 0 error(s), 314 warning(s), 0 unconnected [silk_edge_clearance×3 silk_over_copper×65 silk_overlap×82 via_dangling×32] [report circuit-drc.rpt]
  ✓ [export-gerbers] [exit 0] (13 Gerber layers written: 6 copper + mask/paste/silk/outline)
  ✓ [export-drill] [exit 0]
  ✓ [export-pos] [exit 0]
  ✓ [export-bom] [exit 0]
  ✓ [render] render/board-top.png render/board-bottom.png [exit 0]
  ✓ [someda-erc] 4 finding(s) [4 = known power-symbol gap (M4)]
  ✓ [someda-drc] 0 error(s), 0 warning(s)
  ✓ [export-preflight] drc=PASS shorts=PASS unrouted=PASS pours=PASS gerbers=PASS drill=PASS
```

Export preflight:

```
         drc PASS: 0 error(s)
      shorts PASS: 0 short(s)
    unrouted PASS: 0 unrouted net(s)
       pours PASS: filled
     gerbers PASS: package written
       drill PASS: excellon written
```

## kicad-cli DRC (`reports/circuit-drc.rpt`)

```
** Found 314 DRC violations **
** Found 0 unconnected pads **
** Found 0 Footprint errors **
```

Finding codes: lib_footprint_issues ×132, silk_overlap ×82, silk_over_copper ×65, via_dangling ×32, silk_edge_clearance ×3. Every finding is a warning on the silkscreen layer; there are no clearance,
track, hole, zone or connectivity findings.

## Layout of this directory

- `fab/` — the JLCPCB-ready set: 6 copper Gerbers (`.gtl`, `.g1`–`.g4`, `.gbl`), masks, pastes,
  silkscreens, outline, Gerber job file, Excellon drill + PDF map, `positions.csv`, `bom.csv`
- `kicad/` — the board, schematic and the project file carrying the design rules kicad-cli judged by
- `reports/` — DRC and ERC reports as kicad-cli wrote them, and the engine's full build log
  (plan, footprint resolution, placement, routing, per-net frequency table, SI/thermal audit)
- `gerber-render/` — each Gerber layer rendered to SVG from the files in `fab/`, plus top/bottom composites
- `render/` — kicad-cli 3D renders of `kicad/circuit.kicad_pcb`
- `SHA256SUMS` — checksums of `fab/*` and `kicad/*`

## What this evidence does not show

The board has not been simulated or built. USB, Ethernet and MIPI pairs are routed as
single-ended traces. The RJ45 LED pin order, the LCD pinout and the exposed-pad size are
conventions to confirm against the exact parts before ordering (see `../README.md`).
