#!/usr/bin/env bash
# V.I.C.T.O.R. Interactive Installer Script
set -euo pipefail

PREFIX="${HOME}/.local"
BIN_DIR="${PREFIX}/bin"
CONFIG_DIR="${HOME}/.config/victor"
STATE_DIR="${HOME}/.local/state/victor"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "V.I.C.T.O.R. Installer"
echo "======================"

# 1. Verify Python Version
PYTHON_BIN="$(which python3 2>/dev/null || true)"
if [ -z "$PYTHON_BIN" ]; then
    echo "Error: python3 was not found on your system PATH." >&2
    exit 1
fi

PY_VER="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Detected Python: ${PY_VER}"

# 2. Setup Configuration Directories
mkdir -p "${CONFIG_DIR}" "${STATE_DIR}" "${BIN_DIR}"

if [ ! -f "${CONFIG_DIR}/config.toml" ]; then
    echo "Creating default configuration at ${CONFIG_DIR}/config.toml..."
    cp "${REPO_DIR}/config/config.example.toml" "${CONFIG_DIR}/config.toml"
    chmod 600 "${CONFIG_DIR}/config.toml"
fi

# 3. Create Symlink in ~/.local/bin
echo "Installing victor executable to ${BIN_DIR}/victor..."
ln -sf "${REPO_DIR}/victor" "${BIN_DIR}/victor"
chmod +x "${REPO_DIR}/victor"

# 4. Verify system dependencies
echo "Checking recommended system tools:"
for tool in piper parec pw-play hyprctl pactl wl-paste wl-copy; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "  [OK] $tool"
    else
        echo "  [OPTIONAL] $tool (not found)"
    fi
done

echo ""
echo "Installation complete."
echo "Execute 'victor --help' or 'victor brief' to verify."
