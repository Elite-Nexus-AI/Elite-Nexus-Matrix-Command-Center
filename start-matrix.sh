#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ELITE NEXUS // MATRIX HUD BOOT SEQUENCE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ -f config.sh ] && source config.sh

if ! pgrep -x ollama > /dev/null; then
  echo "→ Starting Ollama..."
  ollama serve &>/tmp/ollama.log &
  sleep 4
else
  echo "✓ Ollama already running"
fi

echo "→ Waiting for Ollama..."
for i in {1..15}; do
  if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama online"; break
  fi
  sleep 1
done

if lsof -t -i:8765 > /dev/null 2>&1; then
  echo "→ Clearing port 8765..."
  kill $(lsof -t -i:8765) 2>/dev/null
  sleep 1
fi

echo "→ Starting Matrix Bridge..."
source "$SCRIPT_DIR/.venv/bin/activate"
python3 bridge.py &>/tmp/matrix-bridge.log &
BRIDGE_PID=$!
sleep 3

if curl -sf http://localhost:8765/health > /dev/null 2>&1; then
  echo "✓ Bridge online at http://localhost:8765"
else
  echo "⚠ Bridge starting..."
fi

sleep 2
xdg-open http://localhost:8765 &>/dev/null &

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MATRIX HUD LIVE — PID: $BRIDGE_PID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

wait $BRIDGE_PID

# Fix USB audio source on startup
sleep 3
pactl set-default-source alsa_input.usb-ZIMHOME_ZTD39_Device_20250915A-00.mono-fallback 2>/dev/null || true
wpctl set-default 54 2>/dev/null || true

# Start vLLM (Qwen2.5-72B AWQ)
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
sudo docker stop $(sudo docker ps -q --filter 'publish=8880') 2>/dev/null
bash $DIR/start_vllm.sh &
