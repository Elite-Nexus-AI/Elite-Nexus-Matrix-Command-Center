#!/usr/bin/env python3
# Matrix OS Global Hotkey - Ctrl+Space to focus HUD
import subprocess, time, os
try:
    from pynput import keyboard
except ImportError:
    print('pynput not installed. Run: pip install pynput --break-system-packages')
    exit(1)

HOTKEY_COMBO = {keyboard.Key.ctrl_l, keyboard.Key.space}
pressed = set()

def on_press(key):
    pressed.add(key)
    if all(k in pressed for k in HOTKEY_COMBO):
        print('Ctrl+Space: Focusing Matrix HUD')
        os.system('xdg-open http://localhost:8765 2>/dev/null')
        subprocess.Popen(['wmctrl', '-a', 'Matrix HUD'], stderr=subprocess.DEVNULL)

def on_release(key):
    pressed.discard(key)

print('Global hotkey active: Ctrl+Space = focus Matrix HUD')
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()