#!/usr/bin/env bash
# setup.sh — Verify environment for NPS
set -e

echo "=== NPS Environment Check ==="
echo

# Python
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1)
    echo "[OK] $PY_VERSION"
else
    echo "[FAIL] Python 3 not found"
    exit 1
fi

# tkinter
if python3 -c "import tkinter" 2>/dev/null; then
    echo "[OK] tkinter available"
else
    echo "[WARN] tkinter not found — GUI mode won't work"
    echo "       Install: sudo apt install python3-tk (Debian/Ubuntu)"
fi

# Project structure
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NPS_DIR="$PROJECT_ROOT/nps"

if [ -f "$NPS_DIR/main.py" ]; then
    echo "[OK] nps/main.py found"
else
    echo "[FAIL] nps/main.py not found — wrong directory?"
    exit 1
fi

# Tests
echo
echo "=== Running Tests ==="
cd "$NPS_DIR"
python3 -m unittest discover tests/ -v
