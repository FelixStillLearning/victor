#!/usr/bin/env bash
# V.I.C.T.O.R. Uninstallation Script
set -euo pipefail

PREFIX="${HOME}/.local"
BIN_FILE="${PREFIX}/bin/victor"
CONFIG_DIR="${HOME}/.config/victor"
STATE_DIR="${HOME}/.local/state/victor"

echo "V.I.C.T.O.R. Uninstaller"
echo "========================"

if [ -L "$BIN_FILE" ] || [ -f "$BIN_FILE" ]; then
    echo "Removing ${BIN_FILE}..."
    rm -f "$BIN_FILE"
fi

if [ -d "$STATE_DIR" ]; then
    echo "Cleaning state directory ${STATE_DIR}..."
    rm -rf "$STATE_DIR"
fi

echo ""
read -p "Do you wish to remove configuration files at ${CONFIG_DIR}? [y/N] " -r REPLY
if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    rm -rf "$CONFIG_DIR"
    echo "Removed ${CONFIG_DIR}."
else
    echo "Kept ${CONFIG_DIR}."
fi

echo "Uninstallation complete."
