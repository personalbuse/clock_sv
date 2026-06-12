#!/usr/bin/env bash
set -euo pipefail

echo "=== ALSA Audio Diagnostics ==="
echo ""

echo "--- Playback devices ---"
aplay -l 2>/dev/null || echo "No playback devices found"

echo ""
echo "--- Capture devices ---"
arecord -l 2>/dev/null || echo "No capture devices found"

echo ""
echo "--- Recording 3-second test ---"
arecord -d 3 -f S16_LE -r 16000 -c 1 /tmp/test_audio.wav
echo "Saved /tmp/test_audio.wav"

echo ""
echo "--- Playing back test ---"
aplay /tmp/test_audio.wav
echo "Done."
