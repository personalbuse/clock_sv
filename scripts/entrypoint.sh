#!/usr/bin/env bash
set -euo pipefail

echo "=== Servidor Inteligente ==="
echo ""

if [ ! -d /dev/snd ]; then
    echo "ERROR: /dev/snd not found. Audio device not mapped."
    echo "Ensure docker-compose maps /dev/snd into the container."
    exit 1
fi

echo "--- Audio devices ---"
aplay -l 2>/dev/null || echo "WARNING: No playback devices"

echo ""
echo "Starting assistant..."
exec python -m src.main
