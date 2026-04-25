#!/bin/bash
# GST Invoice Extractor — Quick Start
# Usage: bash run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "  🧾  GST Invoice Extractor"
echo "=================================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌  Python 3 is required. Install it from https://python.org"
    exit 1
fi

# Install dependencies if needed
echo "📦  Checking dependencies..."
pip install -r requirements.txt --quiet --break-system-packages 2>/dev/null \
  || pip install -r requirements.txt --quiet

echo "✅  Dependencies ready."
echo ""
echo "🚀  Starting app at http://localhost:8501"
echo "    Press Ctrl+C to stop."
echo ""

streamlit run app.py \
    --server.headless false \
    --server.port 8501 \
    --browser.gatherUsageStats false
