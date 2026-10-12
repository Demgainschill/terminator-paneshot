#!/usr/bin/env bash
# termreport installer — sets up the renderer and Terminator plugin

set -euo pipefail

echo "========================================"
echo "  termreport Installer"
echo "========================================"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $EUID -eq 0 ]]; then
   echo "[!] Warning: running as root. Installing for the root user."
fi

echo "[*] Installing system packages..."
if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y python3-pil fonts-dejavu-core
elif command -v dnf &>/dev/null; then
    sudo dnf install -y python3-pillow dejavu-sans-mono-fonts
elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm python-pillow ttf-dejavu
else
    echo "[!] Package manager not detected. Install python3-pil and a monospaced font manually."
fi

echo "[*] Creating directories..."
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.config/terminator/plugins"
mkdir -p "$HOME/reports"

echo "[*] Installing renderer..."
cp "$SCRIPT_DIR/termreport.py" "$HOME/.local/bin/termreport.py"
chmod +x "$HOME/.local/bin/termreport.py"

echo "[*] Installing Terminator plugin..."
cp "$SCRIPT_DIR/report_shot.py" "$HOME/.config/terminator/plugins/report_shot.py"

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo
    echo "[!] ~/.local/bin is not on your PATH."
    echo "    Add the following line to your shell rc file:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo
fi

echo
echo "========================================"
echo "  Installation finished"
echo "========================================"
echo
echo "Next steps:"
echo "  1. Fully restart Terminator"
echo "  2. Right-click → Preferences → Plugins"
echo "  3. Enable 'ReportShot'"
echo "  4. Right-click in a pane → Capture for Report..."
echo
echo "Images are saved under: ~/reports/<tool_name>/"
echo
echo "Command-line example:"
echo "  termreport.py -t nmap -f scrollback.txt"
echo
