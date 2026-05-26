#!/bin/bash
# Start wake word listener and global hotkey in background
cd ~/Downloads/files/matrix-hud-perfect
source .venv/bin/activate
echo 'Starting wake word listener...'
python3 wake_word.py >> /tmp/wake_word.log 2>&1 &
echo $! > /tmp/wake_word.pid
echo 'Starting global hotkey...'
python3 global_hotkey.py >> /tmp/hotkey.log 2>&1 &
echo $! > /tmp/hotkey.pid
echo 'Wake word + hotkey running'
echo 'Say: Hermes / Matrix / Nexus'
echo 'Hotkey: Ctrl+Space'
