#!/usr/bin/env bash
set -euo pipefail

# Ensure PulseAudio is running
echo "Checking PulseAudio..."
pulseaudio --kill 2>/dev/null || true
sleep 1
rm -rf /run/user/$(id -u)/pulse /tmp/pulse-* 2>/dev/null || true
pulseaudio --start 2>&1 | grep -i "startup\|error" || true
sleep 2

echo "Starting Clock Voice Assistant..."
export TZ=America/Bogota
export PYTHONPATH=.
cd "$(dirname "$0")"
python src/main.py
