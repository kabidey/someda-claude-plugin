"""SomPi-V3s: a 6-layer Linux SBC around the Allwinner V3s (eLQFP-128).

Shaped like an Orange Pi (USB-C power/OTG, RJ45, microSD, SPI NOR, LCD and
camera FPCs, audio jack, GPIO header, UART header) but it is NOT a copy of
any vendor board: every net below is derived from the V3s datasheet pin
table (research/v3s_pins.json, verified 128/128 against five independent
sources) plus the reference-design practices noted in research/v3s_pins.md.

Run:  python3 -I gen_sompi.py   -> plan.json (someda CircuitPlan contract)
"""
import json, math, re, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
PINS = json.load(open(HERE.parent / "research" / "v3s_pins.json"))["pins"]
BY_NAME = {v["name"]: k for k, v in PINS.items()}
FP_DIRS = ["/root/pcb/sompi/lib", "/usr/share/kicad/footprints"]

def soc(name):
    """Pin NUMBER of a V3s pin by datasheet name (hard failure on a typo)."""
    if name not in BY_NAME:
        sys.exit(f"V3s pin name not in the verified table: {name}")
    return f"U1:{BY_NAME[name]}"

# ---------------------------------------------------------------- plan model
comps, nets, notes = [], {}, []
def comp(ref, value, lib, fp, **kw):
    d = {"reference": ref, "value": value, "lib_id": lib, "footprint": fp}
    d.update({k: v for k, v in kw.items() if v is not None})
    comps.append(d); return ref
def net(name, *pins, **kw):
    n = nets.setdefault(name, {"name": name, "pins": []})
    for p in pins:
        if p not in n["pins"]:
            n["pins"].append(p)
    n.update(kw)

# ------------------------------------------------- footprint geometry helper
def fp_path(lib_id):
    lib, name = lib_id.split(":")
    for d in FP_DIRS:
        p = pathlib.Path(d) / f"{lib}.pretty" / f"{name}.kicad_mod"
        if p.is_file():
            return p
    sys.exit(f"footprint missing: {lib_id}")

def opening_rotation(lib_id, edge):
    """Rotation (deg, KiCad CCW/y-down) so the connector's opening faces `edge`.
    Opening direction = from the pad centroid toward the courtyard centre."""
    txt = fp_path(lib_id).read_text()
    pads = [(float(x), float(y)) for x, y in re.findall(r'\(pad "[^"]*" \w+ \w+\s*\(at (-?[\d.]+) (-?[\d.]+)', txt)]
    crt = []
    for m in re.finditer(r'\(fp_(?:line|rect|poly)(.*?)\n\t\)', txt, re.S):
        b = m.group(1)
        if 'F.CrtYd' in b:
            crt += [(float(a), float(c)) for a, c in re.findall(r'\((?:start|end|xy) (-?[\d.]+) (-?[\d.]+)\)', b)]
    px = sum(p[0] for p in pads) / len(pads); py = sum(p[1] for p in pads) / len(pads)
    cx = (min(c[0] for c in crt) + max(c[0] for c in crt)) / 2; cy = (min(c[1] for c in crt) + max(c[1] for c in crt)) / 2
    vx, vy = cx - px, cy - py
    if abs(vx) >= abs(vy):
        opening = (math.copysign(1, vx), 0.0)
    else:
        opening = (0.0, math.copysign(1, vy))
    want = {"left_edge": (-1, 0), "right_edge": (1, 0), "top_edge": (0, -1), "bottom_edge": (0, 1)}[edge]
    for rot in (0, 90, 180, 270):
        r = math.radians(rot)
        ox = opening[0] * math.cos(r) + opening[1] * math.sin(r)
        oy = -opening[0] * math.sin(r) + opening[1] * math.cos(r)
        if abs(ox - want[0]) < 1e-6 and abs(oy - want[1]) < 1e-6:
            notes.append(f"{lib_id}: opening {opening} -> {edge} with rotation {rot}")
            return rot
    return 0

def pads_of(lib_id):
    return set(re.findall(r'\(pad "([^"]*)"', fp_path(lib_id).read_text()))

# ---------------------------------------------------------------- footprints
R0402 = "Resistor_SMD:R_0402_1005Metric"; R0603 = "Resistor_SMD:R_0603_1608Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"; C0603 = "Capacitor_SMD:C_0603_1608Metric"; C0805 = "Capacitor_SMD:C_0805_2012Metric"
LED0603 = "LED_SMD:LED_0603_1608Metric"
rc = {"R": 0, "C": 0, "L": 0, "D": 0}
def R(value, a, b, near=None, fp=R0402, **kw):
    rc["R"] += 1; ref = f"R{rc['R']}"
    comp(ref, value, "Device:R", fp, near=near, **kw); net(a, f"{ref}:1"); net(b, f"{ref}:2"); return ref
def C(value, a, b, near=None, fp=C0402, **kw):
    rc["C"] += 1; ref = f"C{rc['C']}"
    comp(ref, value, "Device:C", fp, near=near, **kw); net(a, f"{ref}:1"); net(b, f"{ref}:2"); return ref

# ============================================================== the design
plan_name = "SomPi-V3s"
BOARD = (90.0, 60.0)

# --- U1: the SoC ---------------------------------------------------------
U1_FP = "SomPi:eLQFP-128_14x14mm_P0.4mm_EP5.72x5.72mm_ThermalVias"
comp("U1", "Allwinner V3s", "SoC:Allwinner_V3s", U1_FP, position="center", power_w=0.8)
net("GND", "U1:129")                       # exposed pad = the only digital ground
# power pins by domain (names straight from the datasheet table)
dom = {}
for num, v in PINS.items():
    if v["kind"] == "power":
        dom.setdefault(v["domain"], []).append(f"U1:{num}")
rail = {"VDD-CPU": "+1V2", "VDD-SYS": "+1V2", "VCC-DRAM": "+1V8", "VCC-IO": "+3V3", "VCC-PE": "+3V3",
        "VCC-PLL": "+3V0", "AVCC": "+3V0", "HPVCCIN": "+3V3", "VCC-RTC": "+3V3", "VCC-USB": "+3V3",
        "VCC-MCSI": "+3V3", "EPHY_VCC": "+3V3", "EPHY_VDD": "+1V2"}
for d, pins in dom.items():
    if d == "VCC-RTC":
        # VCC-RTC (98) is a rail; RTC-VIO (97) is an internal LDO OUTPUT: cap only
        for p in pins:
            if p == soc("VCC-RTC"): net("+3V3", p)
            if p == soc("RTC-VIO"): net("RTC_VIO", p)
        continue
    for p in pins:
        net(rail[d], p)
net("AGND", soc("AGND"))

# decoupling: one 100nF per pin pair + bulk per rail, all hugging U1
def decouple(rail_name, count, bulk=None, gnd="GND"):
    for _ in range(count):
        C("100nF", rail_name, gnd, near="U1")
    if bulk:
        C(bulk, rail_name, gnd, near="U1", fp=C0603)
decouple("+1V2", 7, "10uF")        # VDD-CPU x8 + VDD-SYS x6 + EPHY_VDD
decouple("+1V8", 6, "10uF")        # VCC-DRAM x12
decouple("+3V3", 7, "10uF")        # VCC-IO x4, VCC-PE x2, RTC, USB, MCSI, EPHY_VCC, HPVCCIN
decouple("+3V0", 2, "10uF", gnd="AGND")   # AVCC + VCC-PLL (3.0 V rail, NOT 3V3: datasheet max 3.3)
C("10uF", "RTC_VIO", "GND", near="U1", fp=C0603)
C("10uF", "HPVCC_BP", "GND", near="U1", fp=C0603); C("100nF", "HPVCC_BP", "GND", near="U1"); net("HPVCC_BP", soc("HPVCCBP"))
# DRAM references: SVREF = VCC-DRAM/2 (2k/2k 1% + 100nF each), ZQ 240R 1%
for n, vref in (("SVREF0", soc("SVREF0")), ("SVREF1", soc("SVREF1"))):
    net(n, vref); R("2k 1%", "+1V8", n, near="U1"); R("2k 1%", n, "GND", near="U1"); C("100nF", n, "GND", near="U1")
net("SZQ", soc("SZQ")); R("240R 1%", "SZQ", "GND", near="U1")
# codec references (values fixed by the design guide), single-point AGND
net("VRA1", soc("VRA1")); net("VRA2", soc("VRA2"))
C("1uF", "VRA1", "AGND", near="U1"); C("10uF", "VRA2", "AGND", near="U1", fp=C0603); R("200k 1%", "VRA2", "VRA1", near="U1")
R("0R", "AGND", "GND", near="U1", fp=R0603)
# Ethernet PHY bias
net("EPHY_RTX", soc("EPHY_RTX")); R("6.04k 1%", "EPHY_RTX", "GND", near="U1")

# --- crystals ------------------------------------------------------------
comp("Y1", "24MHz", "Device:Crystal_GND24", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", near="U1")
net("X24M_IN", soc("X24MIN"), "Y1:1", freq_hz=24e6, role="clock"); net("X24M_OUT", soc("X24MOUT"), "Y1:3", freq_hz=24e6, role="clock")
net("GND", "Y1:2", "Y1:4"); C("18pF", "X24M_IN", "GND", near="Y1"); C("18pF", "X24M_OUT", "GND", near="Y1")
comp("Y2", "32.768kHz", "Device:Crystal", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", near="U1")
net("X32K_IN", soc("X32KIN"), "Y2:1", freq_hz=32768, role="clock"); net("X32K_OUT", soc("X32KOUT"), "Y2:2", freq_hz=32768, role="clock")
C("6pF", "X32K_IN", "GND", near="Y2"); C("6pF", "X32K_OUT", "GND", near="Y2"); R("10M", "X32K_IN", "X32K_OUT", near="Y2")

# --- reset and key ---------------------------------------------------------
net("RESET_N", soc("RESET")); R("47k", "+3V3", "RESET_N", near="U1"); C("1uF", "RESET_N", "GND", near="U1")
comp("SW1", "RESET", "Switch:SW_Push", "Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92", position="top_edge", edge_at=0.86)
net("RESET_N", "SW1:1"); net("GND", "SW1:2")
net("LRADC0", soc("LRADC0")); R("100k 1%", "+3V0", "LRADC0", near="U1"); C("1nF", "LRADC0", "GND", near="U1")
comp("SW2", "KEY1", "Switch:SW_Push", "Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92", position="top_edge", edge_at=0.95)
net("KEY1", "SW2:1"); net("GND", "SW2:2"); R("6.8k 1%", "LRADC0", "KEY1", near="SW2")

# --- LEDs ------------------------------------------------------------------
comp("D1", "PWR red", "Device:LED", LED0603); net("PWR_LED", "D1:2"); net("GND", "D1:1"); R("1k", "+3V3", "PWR_LED", near="D1")
comp("D2", "STAT green", "Device:LED", LED0603); net("STAT_LED", "D2:2"); net("GND", "D2:1")
net("PB3_LED", soc("PB3")); R("1k", "PB3_LED", "STAT_LED", near="D2")

# --- USB-C: 5 V power in + USB 2.0 OTG ----------------------------------
J1_FP = "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
comp("J1", "USB-C 16P", "Connector:USB_C_Receptacle_USB2.0_16P", J1_FP, position="top_edge", edge_at=0.30, rotation=opening_rotation(J1_FP, "top_edge"))
for p in ("A1", "A12", "B1", "B12", "SH"): net("GND", f"J1:{p}")
for p in ("A4", "A9", "B4", "B9"): net("VBUS_IN", f"J1:{p}", role="power")
net("CC1", "J1:A5"); net("CC2", "J1:B5"); R("5.1k", "CC1", "GND", near="J1"); R("5.1k", "CC2", "GND", near="J1")
net("USB_DP_J", "J1:A6", "J1:B6"); net("USB_DM_J", "J1:A7", "J1:B7")
comp("F1", "2A fuse", "Device:Polyfuse", "Fuse:Fuse_1206_3216Metric", near="J1"); net("VBUS_IN", "F1:1"); net("VBUS", "F1:2", role="power")
C("10uF", "VBUS", "GND", near="F1", fp=C0805)
# ESD array on the data lines (USBLC6-2SC6: 1/6 = I/O1, 3/4 = I/O2, 2 GND, 5 VBUS)
comp("U8", "USBLC6-2SC6", "Power_Protection:USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", near="J1")
net("USB_DP_J", "U8:1"); net("USB_DP", "U8:6", soc("USB-DP"), freq_hz=480e6, role="highspeed")
net("USB_DM_J", "U8:3"); net("USB_DM", "U8:4", soc("USB-DM"), freq_hz=480e6, role="highspeed")
net("GND", "U8:2"); net("VBUS", "U8:5")
notes.append("USB D+/D- declared as 90 ohm differential pairs (J1-U8 and U8-U1): coupled routing on the GND-referenced outer layer, intra-pair skew budget 1.1 mm (Toradex 102492 USB 2.0 table)")

# --- 3V3 and 1V2 bucks: TPS562200 (1 GND, 2 SW, 3 VIN, 4 VFB, 5 EN, 6 VBST), 0.765 V FB
def buck(ref, vout_name, r_top, r_bot, pos):
    comp(ref, "TPS562200", "Regulator_Switching:TPS562200", "Package_TO_SOT_SMD:SOT-23-6", power_w=0.35, position=pos)
    net("GND", f"{ref}:1"); net("VBUS", f"{ref}:3", f"{ref}:5")
    sw, fb, bst = f"{ref}_SW", f"{ref}_FB", f"{ref}_BST"
    net(sw, f"{ref}:2", role="power"); net(fb, f"{ref}:4"); net(bst, f"{ref}:6")
    C("100nF", bst, sw, near=ref)
    rc["L"] += 1; lref = f"L{rc['L']}"
    comp(lref, "4.7uH 3A", "Device:L", "Inductor_SMD:L_Taiyo-Yuden_NR-40xx", near=ref)
    net(sw, f"{lref}:1"); net(vout_name, f"{lref}:2")
    C("10uF", "VBUS", "GND", near=ref, fp=C0805)
    C("22uF", vout_name, "GND", near=lref, fp=C0805); C("22uF", vout_name, "GND", near=lref, fp=C0805)
    R(r_top, vout_name, fb, near=ref); R(r_bot, fb, "GND", near=ref)
buck("U2", "+3V3", "33.2k 1%", "10k 1%", "bottom_right")  # 0.765*(1+33.2/10) = 3.30 V
buck("U3", "+1V2", "5.62k 1%", "10k 1%", "bottom_right")  # 0.765*(1+5.62/10) = 1.195 V
# 1V8 LDO (DRAM) and 3V0 LDO (AVCC / VCC-PLL) from 3V3
comp("U4", "ME6211C18M5G", "Regulator_Linear:ME6211C18M5", "Package_TO_SOT_SMD:SOT-23-5", power_w=0.22)
net("+3V3", "U4:1", "U4:3"); net("GND", "U4:2"); net("+1V8", "U4:5", role="power")
C("1uF", "+3V3", "GND", near="U4", fp=C0603); C("10uF", "+1V8", "GND", near="U4", fp=C0603)
comp("U5", "XC6206P302MR", "Regulator_Linear:XC6206PxxxMR", "Package_TO_SOT_SMD:SOT-23", power_w=0.03)
net("GND", "U5:1"); net("+3V0", "U5:2", role="power"); net("+3V3", "U5:3")
C("1uF", "+3V3", "GND", near="U5", fp=C0603); C("1uF", "+3V0", "GND", near="U5", fp=C0603)

# --- Ethernet: internal PHY -> HR911105A magjack (1 TD+, 2 TD-, 3 RD+, 4 TCT, 5 RCT, 6 RD-, 8 GND, 9-12 LEDs, SH)
J2_FP = "Connector_RJ:RJ45_Hanrun_HR911105A_Horizontal"
comp("J2", "RJ45 HR911105A", "Connector:RJ45_Hanrun_HR911105A_Horizontal", J2_FP, position="right_edge", edge_at=0.32, rotation=opening_rotation(J2_FP, "right_edge"))
net("ETH_TXP", soc("EPHY_TXP"), "J2:1", freq_hz=125e6, role="highspeed"); net("ETH_TXN", soc("EPHY_TXN"), "J2:2", freq_hz=125e6, role="highspeed")
net("ETH_RXP", soc("EPHY_RXP"), "J2:3", freq_hz=125e6, role="highspeed"); net("ETH_RXN", soc("EPHY_RXN"), "J2:6", freq_hz=125e6, role="highspeed")
net("ETH_VCC", "J2:4", "J2:5", role="power"); net("GND", "J2:8", "J2:SH")
rc["L"] += 1; comp(f"L{rc['L']}", "10uH", "Device:L", "Inductor_SMD:L_0805_2012Metric", near="J2"); net("+3V3", f"L{rc['L']}:1"); net("ETH_VCC", f"L{rc['L']}:2")
C("100nF", "ETH_VCC", "GND", near="J2"); C("100nF", "ETH_VCC", "GND", near="J2")
for n in ("ETH_TXP", "ETH_TXN", "ETH_RXP", "ETH_RXN"): R("51R 1%", n, "ETH_VCC", near="J2")
net("ETH_LED_LINK", "J2:10", soc("EPHY_LINK_LED")); net("ETH_LED_SPD", "J2:12", soc("EPHY_SPD_LED"))
net("ETH_LED_A1", "J2:9"); net("ETH_LED_A2", "J2:11"); R("330R", "+3V3", "ETH_LED_A1", near="J2"); R("330R", "+3V3", "ETH_LED_A2", near="J2")
notes.append("RJ45 LED pins 9/10 and 11/12 assumed anode/cathode order; verify against the HR911105A drawing")
notes.append("Ethernet TX/RX declared as 100 ohm differential pairs, intra-pair skew budget 0.25 mm (Toradex 102492 Ethernet table)")

# --- microSD (SDC0): DM3AT 1 DAT2, 2 DAT3/CD, 3 CMD, 4 VDD, 5 CLK, 6 VSS, 7 DAT0, 8 DAT1, 9 DET_B, 10 DET_A, SH
J3_FP = "Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5"
comp("J3", "microSD", "Connector:Micro_SD_Card_Det_Hirose_DM3AT", J3_FP, position="top_edge", edge_at=0.58, rotation=opening_rotation(J3_FP, "top_edge"))
sd = {"SD_D2": (soc("PF5"), "J3:1"), "SD_D3": (soc("PF4"), "J3:2"), "SD_CMD": (soc("PF3"), "J3:3"),
      "SD_D0": (soc("PF1"), "J3:7"), "SD_D1": (soc("PF0"), "J3:8")}
for n, (a, b) in sd.items():
    net(n, a, b, freq_hz=50e6, role="digital"); R("10k", "+3V3", n, near="J3")
net("SD_CLK_SOC", soc("PF2"), freq_hz=50e6, role="clock"); net("SD_CLK", "J3:5", freq_hz=50e6, role="clock"); R("33R", "SD_CLK_SOC", "SD_CLK", near="U1")
net("+3V3", "J3:4"); net("GND", "J3:6", "J3:10", "J3:SH"); C("100nF", "+3V3", "GND", near="J3")
net("SD_CD", "J3:9", soc("PF6")); R("10k", "+3V3", "SD_CD", near="J3")

# --- SPI NOR boot flash (W25Q128JVS SOIC-8: 1 CS, 2 DO, 3 WP, 4 GND, 5 DI, 6 CLK, 7 HOLD, 8 VCC)
comp("U6", "W25Q128JVSIQ", "Memory_Flash:W25Q128JVS", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", near="U1")
net("SPI0_CS", soc("PC2"), "U6:1", role="digital"); net("SPI0_MISO", soc("PC0"), "U6:2", freq_hz=50e6, role="digital")
net("SPI0_MOSI", soc("PC3"), "U6:5", freq_hz=50e6, role="digital"); net("SPI0_CLK", soc("PC1"), "U6:6", freq_hz=50e6, role="clock")
net("+3V3", "U6:3", "U6:7", "U6:8"); net("GND", "U6:4"); C("100nF", "+3V3", "GND", near="U6")

# --- LCD: 40-pin 0.5 mm RGB TFT FPC (common 40P RGB pinout), 18-bit RGB666 from LCD_D2..D23
J4_FP = "Connector_FFC-FPC:Hirose_FH12-40S-0.5SH_1x40-1MP_P0.50mm_Horizontal"
comp("J4", "LCD 40P RGB", "Connector_Generic:Conn_01x40", J4_FP, position="left_edge", edge_at=0.5, rotation=opening_rotation(J4_FP, "left_edge"))
lcd_pads = pads_of(J4_FP)
net("LCD_LEDK", "J4:1"); net("VBUS", "J4:2"); net("GND", "J4:3", "J4:29", "J4:36"); net("+3V3", "J4:4")
for p in sorted(lcd_pads - {str(i) for i in range(1, 41)}): net("GND", f"J4:{p}")   # MP shield pads
lcd_bits = {7: "PE4", 8: "PE5", 9: "PE6", 10: "PE7", 11: "PE8", 12: "PE9",          # R2..R7 = LCD_D2..D7
            15: "PE10", 16: "PE11", 17: "PE12", 18: "PE13", 19: "PE14", 20: "PE15",  # G2..G7 = LCD_D10..D15
            23: "PE16", 24: "PE17", 25: "PE18", 26: "PE19", 27: "PE23", 28: "PE24"}  # B2..B7 = LCD_D18..D23
for pin, pe in lcd_bits.items():
    net(f"LCD_{pe}", soc(pe), f"J4:{pin}", freq_hz=33e6, role="digital")
net("LCD_CLK_SOC", soc("PE0"), freq_hz=33e6, role="clock"); net("LCD_CLK", "J4:30", freq_hz=33e6, role="clock"); R("33R", "LCD_CLK_SOC", "LCD_CLK", near="U1")
net("LCD_DISP", soc("PB2"), "J4:31"); net("LCD_HSYNC", soc("PE2"), "J4:32", role="digital"); net("LCD_VSYNC", soc("PE3"), "J4:33", role="digital"); net("LCD_DE", soc("PE1"), "J4:34", role="digital")
# backlight: NMOS low side on LEDK, PWM0 (PB4) drives the gate
comp("Q1", "AO3400A", "Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23", near="J4")
net("LCD_LEDK", "Q1:3"); net("GND", "Q1:2"); net("BL_GATE", "Q1:1"); net("BL_PWM", soc("PB4"))
R("1k", "BL_PWM", "BL_GATE", near="Q1"); R("10k", "BL_GATE", "GND", near="Q1")
notes.append("LCD connector uses the common 40-pin 0.5 mm RGB TFT pinout (LEDK/LEDA/GND/VDD, R0-7, G0-7, B0-7, GND, CLK, DISP, HSYNC, VSYNC, DE, NC, GND, touch); LSBs left open")

# --- camera: 24-pin 0.5 mm FPC carrying MIPI CSI-2 (2 lanes) + control (SomPi pinout)
J5_FP = "Connector_FFC-FPC:Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal"
comp("J5", "CAM MIPI 24P", "Connector_Generic:Conn_01x24", J5_FP, position="right_edge", edge_at=0.78, rotation=opening_rotation(J5_FP, "right_edge"))
for p in sorted(pads_of(J5_FP) - {str(i) for i in range(1, 25)}): net("GND", f"J5:{p}")
for p in (1, 4, 7, 10, 17, 19): net("GND", f"J5:{p}")
# P on the lower-numbered pin of each pair: with the connector on the right edge this keeps the
# P/N order the same as at the SoC's pins 81-87, so the pairs route without a crossover. A camera
# module with the opposite order still routes: the engine crosses the far tails through a via.
mipi = {2: "MCSI-D0P", 3: "MCSI-D0N", 5: "MCSI-D1P", 6: "MCSI-D1N", 8: "MCSI-CKP", 9: "MCSI-CKN"}
for pin, name in mipi.items():
    net(f"CAM_{name.replace('-', '_')}", soc(name), f"J5:{pin}", freq_hz=500e6, role="highspeed")
net("CAM_MCLK_SOC", soc("PE20"), freq_hz=24e6, role="clock"); net("CAM_MCLK", "J5:11", freq_hz=24e6, role="clock"); R("33R", "CAM_MCLK_SOC", "CAM_MCLK", near="U1")
net("CAM_PWDN", soc("PG3"), "J5:12"); net("CAM_RESET", soc("PG2"), "J5:13")
net("CAM_SCL", soc("PE21"), "J5:14"); net("CAM_SDA", soc("PE22"), "J5:15")
R("4.7k", "+3V3", "CAM_SCL", near="J5"); R("4.7k", "+3V3", "CAM_SDA", near="J5")
net("+3V3", "J5:16"); net("+1V8", "J5:18"); C("100nF", "+3V3", "GND", near="J5"); C("100nF", "+1V8", "GND", near="J5")
notes.append("MIPI CSI-2 lanes declared as 100 ohm differential pairs, intra-pair skew budget 0.15 mm (Toradex 102492 CSI table); clock-to-data skew not yet enforced. The 24-pin camera FPC pinout is a convention (GND/D0/GND/D1/GND/CK/GND/MCLK/PWDN/RESET/SCL/SDA/3V3/GND/1V8/GND); P sits on the lower pin number of each pair so the P/N order matches the SoC side — check against the camera module, a swapped module routes with a via crossover")

# --- audio: 3.5 mm jack (capless headphone output with HPCOM virtual ground)
J6_FP = "Connector_Audio:Jack_3.5mm_CUI_SJ-3523-SMT_Horizontal"
comp("J6", "3.5mm jack", "Connector_Audio:AudioJack3", J6_FP, position="top_edge", edge_at=0.10, rotation=opening_rotation(J6_FP, "top_edge"))
net("HP_L", soc("HPOUTL"), "J6:T", role="analog"); net("HP_R", soc("HPOUTR"), "J6:R", role="analog")
net("HPCOM_OUT", "J6:S", role="analog"); net("HPCOM", soc("HPCOM")); net("HPCOMFB", soc("HPCOMFB"))
R("22R", "HPCOM", "HPCOM_OUT", near="U1"); R("0R", "HPCOMFB", "HPCOM_OUT", near="U1"); C("100nF", "HPCOM_OUT", "GND", near="U1")

# --- GPIO header 2x13 (Pi-26 style power rails; V3s spare GPIO)
J7_FP = "Connector_PinHeader_2.54mm:PinHeader_2x13_P2.54mm_Vertical"
comp("J7", "GPIO 2x13", "Connector_Generic:Conn_02x13_Odd_Even", J7_FP, position="bottom_edge", edge_at=0.5, rotation=90)
hdr = {1: "+3V3", 2: "VBUS", 3: ("I2C0_SDA", "PB7"), 4: "VBUS", 5: ("I2C0_SCL", "PB6"), 6: "GND",
       7: ("GPIO_PG0", "PG0"), 8: ("UART2_TX", "PB0"), 9: "GND", 10: ("UART2_RX", "PB1"), 11: ("GPIO_PG1", "PG1"),
       12: ("PWM1", "PB5"), 13: ("GPIO_PG4", "PG4"), 14: "GND", 15: ("GPIO_PG5", "PG5"), 17: "+3V3", 20: "GND", 25: "GND"}
for pin, v in hdr.items():
    if isinstance(v, tuple): net(v[0], soc(v[1]), f"J7:{pin}", role="digital")
    else: net(v, f"J7:{pin}")
R("4.7k", "+3V3", "I2C0_SDA", near="J7"); R("4.7k", "+3V3", "I2C0_SCL", near="J7")
# --- debug UART0 header
comp("J8", "UART0 debug", "Connector_Generic:Conn_01x03", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", position="bottom_edge", edge_at=0.12, rotation=90)
net("GND", "J8:1"); net("UART0_TX", soc("PB8"), "J8:2", role="digital"); net("UART0_RX", soc("PB9"), "J8:3", role="digital")

# --- mounting holes
for i, pos in enumerate(("top_left", "top_right", "bottom_left", "bottom_right"), 1):
    comp(f"H{i}", "M2.5", "Mechanical:MountingHole", "MountingHole:MountingHole_2.7mm_M2.5", position=pos)

# ---------------------------------------------------------------- emit
# sanity: every plan pin exists on its footprint
fp_of = {c["reference"]: c["footprint"] for c in comps}
for n in nets.values():
    for p in n["pins"]:
        ref, num = p.split(":")
        if num not in pads_of(fp_of[ref]):
            sys.exit(f"pin {p} is not a pad of {fp_of[ref]}")
# no component may be referenced by zero nets except mounting holes
used = {p.split(":")[0] for n in nets.values() for p in n["pins"]}
for c in comps:
    if c["reference"] not in used and not c["reference"].startswith("H"):
        sys.exit(f"{c['reference']} has no net")
plan = {"name": plan_name, "description": "6-layer Linux SBC: Allwinner V3s, USB-C OTG/power, 10/100 Ethernet, microSD, SPI NOR, RGB LCD + MIPI camera FPCs, audio, GPIO header",
        "layers": 6, "board": {"width_mm": BOARD[0], "height_mm": BOARD[1]},
        "planes": [{"net": "GND", "layer": "In1.Cu"}, {"net": "+3V3", "layer": "In3.Cu"},
                   {"net": "+1V2", "layer": "In4.Cu", "priority": 0},
                   # +1V8 island on In4 under the DRAM pins: right half of the SoC and below its centre line
                   {"net": "+1V8", "layer": "In4.Cu", "region": "auto", "priority": 1}],
        "pairs": [{"p": "USB_DP_J", "n": "USB_DM_J", "z_diff": 90}, {"p": "USB_DP", "n": "USB_DM", "z_diff": 90},
                  {"p": "ETH_TXP", "n": "ETH_TXN", "z_diff": 100}, {"p": "ETH_RXP", "n": "ETH_RXN", "z_diff": 100},
                  {"p": "CAM_MCSI_D0P", "n": "CAM_MCSI_D0N", "z_diff": 100}, {"p": "CAM_MCSI_D1P", "n": "CAM_MCSI_D1N", "z_diff": 100},
                  {"p": "CAM_MCSI_CKP", "n": "CAM_MCSI_CKN", "z_diff": 100}],
        "components": comps, "nets": list(nets.values())}
json.dump(plan, open(HERE / "plan.json", "w"), indent=1)
open(HERE / "design-notes.txt", "w").write("\n".join(notes) + "\n")
print(f"{len(comps)} components, {len(nets)} nets, {sum(len(n['pins']) for n in nets.values())} pins")
for n in notes: print("note:", n)
