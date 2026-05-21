#!/usr/bin/env bash
# Wait for PipeWire to fully initialize
sleep 5

# Set USB headset as default input
pactl set-default-source alsa_input.usb-ZIMHOME_ZTD39_Device_20250915A-00.mono-fallback 2>/dev/null

# Set correct output 
pactl set-default-sink alsa_output.pci-0000_0c_00.6.analog-stereo 2>/dev/null

echo "Audio routing fixed"
