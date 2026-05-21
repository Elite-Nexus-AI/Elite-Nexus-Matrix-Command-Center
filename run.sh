#!/usr/bin/env bash
# ── Elite Nexus Matrix HUD — Bridge launcher ──────────────
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

[ -f config.sh ] && source config.sh

VENV="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV" ]; then
  echo "→ Creating Python venv…"
  python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"

echo "→ Installing requirements…"
pip install -q -r requirements.txt

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ELITE NEXUS // MATRIX BRIDGE"
echo "  http://localhost:${BRIDGE_PORT:-8765}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 bridge.py
