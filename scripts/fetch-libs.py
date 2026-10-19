#!/usr/bin/env python3
"""fetch-libs: after the schematic is approved, pull every footprint and 3D model the plan
needs that the local KiCad libraries lack.

Sources, in order, per component:
  1. the local KiCad libraries (system install, SOMEDA_FOOTPRINT_DIRS, ~/.local/share/someda)
  2. KiCad's official repositories on GitLab (kicad-footprints, kicad-packages3D) — raw file download
  3. LCSC / EasyEDA by LCSC id (plan field "lcsc": "C165948") via easyeda2kicad — symbol, footprint, STEP
     (an "mpn" is resolved to an LCSC id through JLCPCB's parts search)
  4. zips you downloaded from UltraLibrarian, SnapEDA, Component Search Engine, Mouser or Digi-Key
     (--import <zip>): their KiCad .kicad_mod / .kicad_sym / .step are unpacked into the someda dirs
  5. Mouser / Digi-Key part lookups (MOUSER_API_KEY, DIGIKEY_CLIENT_ID + DIGIKEY_CLIENT_SECRET):
     manufacturer, lifecycle and datasheet for the report; their CAD models are served through
     UltraLibrarian/SnapEDA logins, so the download itself goes through step 4.

Nothing is silently skipped: every component ends the run as FOUND, FETCHED (with the source) or
MISSING (with what to do). With --apply, LCSC-fetched footprints replace the plan's footprint for
that component (plan.json is rewritten, the original kept as plan.json.bak) and a 3D model fetched
for a KiCad footprint that has none is registered in ~/.local/share/someda/3dmodels/overrides.json.
"""
import argparse, json, os, pathlib, re, shutil, subprocess, sys, urllib.request, zipfile

HOME = pathlib.Path(os.environ.get("HOME", "~")).expanduser()
SOMEDA = HOME / ".local/share/someda"
FP_DIR = SOMEDA / "footprints"
MODEL_DIR = SOMEDA / "3dmodels"
EASYEDA_DIR = SOMEDA / "easyeda"
VENV_BIN = SOMEDA / "venv/bin"
KICAD_FP_RAW = "https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/{lib}.pretty/{name}.kicad_mod"
KICAD_3D_RAW = "https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master/{rel}"
UA = {"User-Agent": "someda-fetch-libs/0.7 (+https://github.com/kabidey/someda-claude-plugin)"}


def kicad_dirs():
    dirs = []
    for v in ("SOMEDA_FOOTPRINT_DIRS",):
        for d in os.environ.get(v, "").split(":"):
            if d:
                dirs.append(pathlib.Path(d))
    dirs.append(FP_DIR)
    for v in ("KICAD10_FOOTPRINT_DIR", "KICAD9_FOOTPRINT_DIR", "KICAD8_FOOTPRINT_DIR"):
        if os.environ.get(v):
            dirs.append(pathlib.Path(os.environ[v]))
    dirs += [pathlib.Path("/usr/share/kicad/footprints"), pathlib.Path("/usr/local/share/kicad/footprints"),
             pathlib.Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")]
    return [d for d in dirs if d.is_dir()]


def model_dirs():
    dirs = [MODEL_DIR]
    for v in ("SOMEDA_3DMODEL_DIR", "KICAD10_3DMODEL_DIR", "KICAD9_3DMODEL_DIR"):
        if os.environ.get(v):
            dirs.append(pathlib.Path(os.environ[v]))
    dirs += [pathlib.Path("/usr/share/kicad/3dmodels"), pathlib.Path("/usr/local/share/kicad/3dmodels")]
    return [d for d in dirs if d.is_dir()]


def find_footprint(lib_name):
    lib, _, name = lib_name.partition(":")
    for d in kicad_dirs():
        f = d / f"{lib}.pretty" / f"{name}.kicad_mod"
        if f.is_file():
            return f
    return None


def fetch(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except Exception as e:  # 404 and friends
        return False, str(e)[:80]
    if len(data) < 40:
        return False, "empty"
    dest.write_bytes(data)
    return True, url


def models_of(fp_file):
    text = fp_file.read_text(errors="replace")
    return re.findall(r'\(model\s+"([^"]+)"', text)


def model_rel(path):
    m = re.search(r"3DMODEL_DIR\}/(.*)$", path)
    return m.group(1) if m else None


def model_present(rel):
    return any((d / rel).is_file() for d in model_dirs())


def easyeda_search(mpn):
    """Manufacturer part number → LCSC id through JLCPCB's parts search (the
    public endpoint their order page uses). Prefers the manufacturer's own
    listing over JLCPCB Assembly duplicates and exact model matches."""
    url = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
    body = json.dumps({"keyword": mpn, "currentPage": 1, "pageSize": 10}).encode()
    try:
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
    except Exception:
        return None
    lst = ((d.get("data") or {}).get("componentPageInfo") or {}).get("list") or []
    norm = lambda t: (t or "").lower().replace("-", "").replace(" ", "")
    best = None
    for x in lst:
        code, model, brand = x.get("componentCode"), x.get("componentModelEn") or "", x.get("componentBrandEn") or ""
        if not code:
            continue
        exact = norm(model) == norm(mpn) or norm(model).startswith(norm(mpn))
        assembly = "jlcpcb assembly" in brand.lower()
        score = (2 if exact else 0) + (0 if assembly else 1)
        if best is None or score > best[0]:
            best = (score, code)
    return best[1] if best and best[0] >= 2 else None


def easyeda2kicad(lcsc):
    exe = VENV_BIN / "easyeda2kicad"
    if not exe.exists():
        return None, "easyeda2kicad not installed (run scripts/setup-someda.sh)"
    EASYEDA_DIR.mkdir(parents=True, exist_ok=True)
    out = EASYEDA_DIR / "easyeda2kicad"
    p = subprocess.run([str(exe), "--full", "--lcsc_id", lcsc, "--output", str(out), "--overwrite"], capture_output=True, text=True, timeout=180)
    if p.returncode != 0 and "already" not in (p.stdout + p.stderr):
        return None, (p.stderr or p.stdout).strip()[-200:]
    pretty = EASYEDA_DIR / "easyeda2kicad.pretty"
    fps = sorted(pretty.glob("*.kicad_mod"), key=lambda f: f.stat().st_mtime, reverse=True)
    text = p.stdout + p.stderr
    m = re.search(r"3D model path \(step\): (\S+)", text)
    step = pathlib.Path(m.group(1)) if m else None
    fp = None
    if fps:
        # the footprint written by this run: the newest file whose model line names the step
        for f in fps:
            if step and step.name.split(".")[0] in f.read_text(errors="replace"):
                fp = f
                break
        fp = fp or fps[0]
    return (fp, step), None


def import_zip(zpath):
    """UltraLibrarian / SnapEDA / Component Search Engine / vendor KiCad zips."""
    n = {"fp": 0, "sym": 0, "model": 0}
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            name = pathlib.Path(info.filename).name
            low = name.lower()
            if low.endswith(".kicad_mod"):
                dest = FP_DIR / "imported.pretty" / name
                n["fp"] += 1
            elif low.endswith(".kicad_sym"):
                dest = SOMEDA / "symbols" / name
                n["sym"] += 1
            elif low.endswith((".step", ".stp", ".wrl")):
                dest = MODEL_DIR / "imported.3dshapes" / name
                n["model"] += 1
            else:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(info))
    return n


def vendor_lookup(mpn):
    """Mouser / Digi-Key metadata when API keys are present (no CAD files from these APIs)."""
    notes = []
    key = os.environ.get("MOUSER_API_KEY")
    if key:
        try:
            body = json.dumps({"SearchByPartRequest": {"mouserPartNumber": mpn}}).encode()
            req = urllib.request.Request(f"https://api.mouser.com/api/v1/search/partnumber?apiKey={key}", data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            parts = d.get("SearchResults", {}).get("Parts", [])
            if parts:
                p = parts[0]
                notes.append(f"Mouser: {p.get('Manufacturer')} {p.get('ManufacturerPartNumber')} lifecycle={p.get('LifecycleStatus')} datasheet={p.get('DataSheetUrl')}")
        except Exception as e:
            notes.append(f"Mouser lookup failed: {str(e)[:60]}")
    cid, sec = os.environ.get("DIGIKEY_CLIENT_ID"), os.environ.get("DIGIKEY_CLIENT_SECRET")
    if cid and sec:
        try:
            tok_req = urllib.request.Request("https://api.digikey.com/v1/oauth2/token", data=f"client_id={cid}&client_secret={sec}&grant_type=client_credentials".encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(tok_req, timeout=30) as r:
                tok = json.load(r)["access_token"]
            req = urllib.request.Request(f"https://api.digikey.com/products/v4/search/{urllib.request.quote(mpn)}/productdetails", headers={"Authorization": f"Bearer {tok}", "X-DIGIKEY-Client-Id": cid})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            p = d.get("Product", {})
            notes.append(f"Digi-Key: {p.get('Manufacturer', {}).get('Name')} {p.get('ManufacturerProductNumber')} status={p.get('ProductStatus', {}).get('Status')} datasheet={p.get('DatasheetUrl')}")
        except Exception as e:
            notes.append(f"Digi-Key lookup failed: {str(e)[:60]}")
    return notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", default="plan.json")
    ap.add_argument("--apply", action="store_true", help="rewrite plan.json with fetched LCSC footprints and register model overrides")
    ap.add_argument("--import", dest="imports", action="append", default=[], help="KiCad zip from UltraLibrarian/SnapEDA/vendor to unpack first")
    ap.add_argument("--no-network", action="store_true")
    a = ap.parse_args()
    for d in (FP_DIR, MODEL_DIR, EASYEDA_DIR):
        d.mkdir(parents=True, exist_ok=True)
    for z in a.imports:
        print("import", z, import_zip(z))
    plan = json.load(open(a.plan))
    overrides_file = MODEL_DIR / "overrides.json"
    overrides = json.load(open(overrides_file)) if overrides_file.exists() else {}
    report = []
    changed = False
    for c in plan["components"]:
        ref, fp_name = c["reference"], c.get("footprint") or ""
        status, how = "FOUND", ""
        fp_file = find_footprint(fp_name) if fp_name else None
        if fp_name and not fp_file and not a.no_network:
            lib, _, name = fp_name.partition(":")
            ok, how = fetch(KICAD_FP_RAW.format(lib=lib, name=name), FP_DIR / f"{lib}.pretty" / f"{name}.kicad_mod")
            if ok:
                fp_file, status = FP_DIR / f"{lib}.pretty" / f"{name}.kicad_mod", "FETCHED footprint from kicad-footprints"
        # the footprint's 3D model
        missing_models = []
        if fp_file:
            for m in models_of(fp_file):
                rel = model_rel(m)
                if rel and not model_present(rel) and rel not in overrides and not (m.startswith("/") and pathlib.Path(m).exists()):
                    if not a.no_network:
                        ok, how2 = fetch(KICAD_3D_RAW.format(rel=rel), MODEL_DIR / rel)
                        if ok:
                            status, how = "FETCHED 3D model from kicad-packages3D", how2
                            continue
                    missing_models.append(rel)
        # LCSC / EasyEDA: a part id, or an MPN resolved through EasyEDA search
        lcsc = c.get("lcsc")
        if not lcsc and c.get("mpn") and (not fp_file or missing_models) and not a.no_network:
            lcsc = easyeda_search(c["mpn"])
            if lcsc:
                how = f"EasyEDA search resolved {c['mpn']} → {lcsc}"
        if lcsc and (not fp_file or missing_models) and not a.no_network:
            res, err = easyeda2kicad(lcsc)
            if res:
                fp, step = res
                if not fp_file and fp:
                    status, how = f"FETCHED footprint + 3D from LCSC {lcsc} (easyeda2kicad)", str(fp)
                    if a.apply:
                        c["footprint"] = f"easyeda2kicad:{fp.stem}"
                        changed = True
                    fp_file = fp
                    missing_models = []
                elif missing_models and step and step.exists():
                    for rel in missing_models:
                        overrides[rel] = str(step)
                    status, how = f"FETCHED 3D model from LCSC {lcsc} for a KiCad footprint without one — alignment unverified", str(step)
                    missing_models = []
            else:
                how = f"LCSC {lcsc}: {err}"
        notes = vendor_lookup(c["mpn"]) if c.get("mpn") and not a.no_network else []
        if not fp_file:
            status = "MISSING footprint"
            how = how or f"no '{fp_name}' in the local libraries or kicad-footprints; add \"lcsc\": \"C…\" to the plan, or --import a vendor KiCad zip and set the footprint to imported:<name>"
        elif missing_models:
            status = "MISSING 3D model"
            how = how or f"{', '.join(missing_models)} is not in kicad-packages3D; add \"lcsc\": \"C…\" (the EasyEDA STEP will be attached) or --import a vendor zip"
        report.append((ref, fp_name, status, how, notes))
    if a.apply and changed:
        shutil.copy2(a.plan, a.plan + ".bak")
        json.dump(plan, open(a.plan, "w"), indent=1)
    if overrides:
        json.dump(overrides, open(overrides_file, "w"), indent=1)
    counts = {}
    for ref, fp_name, status, how, notes in report:
        key = status.split(" ")[0]
        counts[key] = counts.get(key, 0) + 1
        if key != "FOUND":
            print(f"{ref:>5} {fp_name:<60} {status}: {how}")
        for n in notes:
            print(f"      {n}")
    print("fetch-libs:", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), f"— footprints in {FP_DIR}, models in {MODEL_DIR}, LCSC parts in {EASYEDA_DIR}")
    missing = counts.get("MISSING", 0)
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
