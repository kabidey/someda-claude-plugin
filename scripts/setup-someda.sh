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
SOMEDA_VERSION="${SOMEDA_VERSION:-v0.6.1}"
INSTALL_DIR="${HOME}/.local/share/someda/bin"

err() { echo "someda-setup: $*" >&2; exit 1; }

# 1. Explicit override
if [ -n "${SOMEDA_BIN:-}" ]; then
    [ -x "${SOMEDA_BIN}" ] || err "SOMEDA_BIN is set but not executable: ${SOMEDA_BIN}"
    echo "${SOMEDA_BIN}"
    exit 0
fi

# 2. On PATH
if command -v someda >/dev/null 2>&1; then
    command -v someda
    exit 0
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
if [ -x "${DEST}" ]; then
    echo "${DEST}"
    exit 0
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
    echo "${DEST}"
    exit 0
}

echo "Downloading someda ${SOMEDA_VERSION} for ${OS}/${ARCH}..." >&2
if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "${TMP}/${ASSET}" "${URL}" || build_from_source
elif command -v wget >/dev/null 2>&1; then
    wget -q -O "${TMP}/${ASSET}" "${URL}" || build_from_source
else
    err "need curl or wget to download the someda binary"
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
echo "${DEST}"