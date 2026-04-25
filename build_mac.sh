#!/bin/bash
# ============================================================
#  GST Invoice Extractor — macOS .app Builder
#  Run once from inside the gstin_extractor_app folder:
#      bash build_mac.sh
#  Output: dist/GST Invoice Extractor.app
# ============================================================

set -e
cd "$(dirname "$0")"

echo ""
echo "  ================================================="
echo "   GST Invoice Extractor — Building macOS .app"
echo "  ================================================="
echo ""

# ── Check Python 3 ────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "  [ERROR] Python 3 not found."
    echo "  Install from https://www.python.org or via Homebrew: brew install python"
    exit 1
fi
echo "  [1/4] Python found: $(python3 --version)"

# ── Virtual environment ───────────────────────────────────
echo "  [2/4] Creating virtual environment..."
python3 -m venv .build_venv
source .build_venv/bin/activate

# ── Install dependencies ──────────────────────────────────
echo "  [3/4] Installing dependencies (this takes a few minutes)..."
pip install --upgrade pip --quiet
pip install streamlit pdfplumber openpyxl pandas altair pyinstaller --quiet

# ── Build ─────────────────────────────────────────────────
echo "  [4/4] Running PyInstaller..."
pyinstaller gstin_extractor.spec --clean --noconfirm

# ── Cleanup ───────────────────────────────────────────────
deactivate
rm -rf .build_venv build __pycache__ *.log 2>/dev/null || true

echo ""
echo "  ================================================="
echo "   BUILD COMPLETE ✅"
echo ""
echo "   Your app: dist/GST Invoice Extractor.app"
echo ""
echo "   To run: open \"dist/GST Invoice Extractor.app\""
echo "   Or drag it to your Applications folder."
echo "  ================================================="
echo ""
