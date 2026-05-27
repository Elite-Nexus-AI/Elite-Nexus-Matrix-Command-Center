#!/bin/bash
# Matrix OS Full Startup Script
cd ~/Downloads/files/matrix-hud-perfect
source config.sh
source .venv/bin/activate

echo "Starting bridge..."
python3 bridge.py >> /tmp/matrix-bridge.log 2>&1 &
sleep 2

echo "Starting wake word listener..."
CUDA_VISIBLE_DEVICES="" PULSE_RUNTIME_PATH=/run/user/1000/pulse DISPLAY=:1 python3 -u wake_word.py >> /tmp/wake_word.log 2>&1 &

echo "Starting global hotkey..."
python3 global_hotkey.py >> /tmp/hotkey.log 2>&1 &

echo "Matrix OS online. Opening HUD..."
sleep 2
DISPLAY=:1 xdg-open http://localhost:8765
