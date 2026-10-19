#!/usr/bin/env bash
# Someda plugin setup: resolve the compiled Rust binary for this platform.
#
# Strategy (in order):
#   1. SOMEDA_BIN env var — explicit override
#   2. `someda` already on PATH — use it
#   3. Download the prebuilt release binary for this OS/arch from GitHub
#      into ~/.local/share/someda/bin/ and report that path
#
# Prints the resolved binary path on stdout; errors to stderr, exit 1.

set -euo pipefail

SOMEDA_REPO="kabidey/someda"
SOMEDA_VERSION="${SOMEDA_VERSION:-v0.8.0}"
INSTALL_DIR="${HOME}/.local/share/someda/bin"

err() { echo "someda-setup: $*" >&2; exit 1; }

# ── Libraries the build needs beyond the engine binary ──────────────────────
# KiCad footprints + 3D models (component bodies in the renders) and the
# LCSC/EasyEDA converter used by scripts/fetch-libs.py. Best effort: each
# step reports what it could not do and the build later says which models
# are missing.
setup_libraries() {
    local data="${HOME}/.local/share/someda"
    mkdir -p "${data}/footprints" "${data}/3dmodels" "${data}/easyeda" "${data}/symbols"
    if [ ! -d /usr/share/kicad/3dmodels ] && [ ! -d /usr/local/share/kicad/3dmodels ] && [ -z "${KICAD10_3DMODEL_DIR:-}${KICAD9_3DMODEL_DIR:-}" ]; then
        if command -v apt-get >/dev/null 2>&1; then
            local sudo=""
            [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1 && sudo="sudo"
            echo "someda-setup: installing kicad-packages3d and kicad-footprints (3D bodies for the renders)" >&2
            DEBIAN_FRONTEND=noninteractive ${sudo} apt-get install -y -q kicad-packages3d kicad-footprints >&2 || echo "someda-setup: could not install kicad-packages3d; renders will show pads without bodies (run: apt-get install kicad-packages3d)" >&2
        else
            echo "someda-setup: no KiCad 3D model library found; install KiCad's packages3D or set KICAD10_3DMODEL_DIR" >&2
        fi
    fi
    if [ ! -x "${data}/venv/bin/easyeda2kicad" ]; then
        if command -v python3 >/dev/null 2>&1; then
            echo "someda-setup: installing easyeda2kicad (LCSC/EasyEDA footprints + 3D models) into ${data}/venv" >&2
            python3 -m venv "${data}/venv" >/dev/null 2>&1 && "${data}/venv/bin/pip" install --quiet easyeda2kicad >&2 || echo "someda-setup: easyeda2kicad not installed (python3 -m venv failed); LCSC fetches unavailable" >&2
        fi
    fi
}


# 1. Explicit override
if [ -n "${SOMEDA_BIN:-}" ]; then
    [ -x "${SOMEDA_BIN}" ] || err "SOMEDA_BIN is set but not executable: ${SOMEDA_BIN}"
    setup_libraries
    echo "${SOMEDA_BIN}"
    exit 0
fi

# 2. On PATH (a binary the user manages; the one this script installs is
#    judged by its version stamp below)
INSTALL_DIR="${HOME}/.local/share/someda/bin"
if command -v someda >/dev/null 2>&1; then
    found="$(command -v someda)"
    case "${found}" in
        "${INSTALL_DIR}"/*) ;;
        *) echo "${found}"; exit 0 ;;
    esac
fi

# 3. Download the release binary for this platform
OS="$(uname -s)"
ARCH="$(uname -m)"
case "${OS}/${ARCH}" in
    Linux/x86_64)  ASSET="someda-linux-x86_64.tar.gz"; BIN="someda" ;;
    Linux/aarch64) ASSET="someda-linux-arm64.tar.gz";  BIN="someda" ;;
    Darwin/arm64)  ASSET="someda-macos-arm64.tar.gz";  BIN="someda" ;;
    Darwin/x86_64) ASSET="someda-macos-x86_64.tar.gz"; BIN="someda" ;;
    MINGW*/*|CYGWIN*/*|MSYS*/*)
        ASSET="someda-windows-x86_64.zip"; BIN="someda.exe" ;;
    *) err "unsupported platform: ${OS}/${ARCH}" ;;
esac

mkdir -p "${INSTALL_DIR}"
DEST="${INSTALL_DIR}/${BIN}"
STAMP="${INSTALL_DIR}/.version"
# Reuse the installed binary only when it is the version this plugin
# expects (live-verified: a plugin update to 0.7.0 kept the 0.6.1 binary
# because any executable at DEST was accepted).
if [ -x "${DEST}" ] && [ -f "${STAMP}" ] && [ "$(cat "${STAMP}" 2>/dev/null)" = "${SOMEDA_VERSION}" ]; then
    setup_libraries
    echo "${DEST}"
    exit 0
fi
if [ -x "${DEST}" ]; then
    echo "someda-setup: installed binary is $(cat "${STAMP}" 2>/dev/null || echo 'unstamped'), plugin expects ${SOMEDA_VERSION} — replacing" >&2
fi

URL="https://github.com/${SOMEDA_REPO}/releases/download/${SOMEDA_VERSION}/${ASSET}"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

# 4. Fallback: build from source when no release asset matches
build_from_source() {
    command -v cargo >/dev/null 2>&1 || err "no release asset at ${URL} and cargo is not installed to build from source"
    command -v git >/dev/null 2>&1 || err "git needed to build someda from source"
    local ref="${SOMEDA_GIT_REF:-${SOMEDA_VERSION}}"
    echo "Building someda from source (https://github.com/${SOMEDA_REPO} @ ${ref})..." >&2
    git clone -q --depth 1 --branch "${ref}" "https://github.com/${SOMEDA_REPO}.git" "${TMP}/src" 2>/dev/null \
        || git clone -q "https://github.com/${SOMEDA_REPO}.git" "${TMP}/src" \
        || err "git clone failed"
    (cd "${TMP}/src" && cargo build --release --quiet) || err "cargo build failed"
    install -m 0755 "${TMP}/src/target/release/${BIN}" "${DEST}"
    echo "${SOMEDA_VERSION}" > "${STAMP}"
    setup_libraries
    echo "${DEST}"
    exit 0
}

echo "Downloading someda ${SOMEDA_VERSION} for ${OS}/${ARCH}..." >&2
# An authenticated `gh` reaches release assets of a private repository
# (the plain download URL answers 404 there); curl/wget serve public ones;
# a source build is the last resort (live-verified: curl 404 → silent
# source build, a different binary than the released one).
downloaded=""
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    gh release download "${SOMEDA_VERSION}" --repo "${SOMEDA_REPO}" --pattern "${ASSET}" --dir "${TMP}" >/dev/null 2>&1 && downloaded=1
fi
if [ -z "${downloaded}" ]; then
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL -o "${TMP}/${ASSET}" "${URL}" && downloaded=1
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O "${TMP}/${ASSET}" "${URL}" && downloaded=1
    else
        err "need gh, curl or wget to download the someda binary"
    fi
fi
if [ -z "${downloaded}" ]; then
    echo "someda-setup: release asset not downloadable from ${URL} (private repository without gh auth, or no asset) — building from source" >&2
    build_from_source
fi

case "${ASSET}" in
    *.tar.gz) tar -xzf "${TMP}/${ASSET}" -C "${TMP}" ;;
    *.zip)
        command -v unzip >/dev/null 2>&1 || err "unzip needed for the Windows binary"
        unzip -o -q "${TMP}/${ASSET}" -d "${TMP}"
        ;;
esac

[ -f "${TMP}/${BIN}" ] || err "archive did not contain ${BIN}"
install -m 0755 "${TMP}/${BIN}" "${DEST}"
# the desktop window ships in the same archive since 0.8.0; keep it next to the CLI
APP="${BIN%.exe}-app${BIN#someda}"
if [ -f "${TMP}/${APP}" ]; then
    install -m 0755 "${TMP}/${APP}" "${INSTALL_DIR}/${APP}"
fi
echo "${SOMEDA_VERSION}" > "${STAMP}"
setup_libraries
echo "${DEST}"