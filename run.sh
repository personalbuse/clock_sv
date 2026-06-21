#!/usr/bin/env bash
set -euo pipefail

# Ensure PulseAudio is running
echo "Checking PulseAudio..."
pulseaudio --kill 2>/dev/null || true
sleep 1
rm -rf /run/user/$(id -u)/pulse /tmp/pulse-* 2>/dev/null || true
pulseaudio --start 2>&1 | grep -i "startup\|error" || true
sleep 2

# faster-whisper / ctranslate2: evitar bad_value(s) in fds_to_keep
export TOKENIZERS_PARALLELISM=0
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activar virtualenv si existe
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

export TZ=America/Bogota
export PYTHONPATH="$SCRIPT_DIR"

echo "Starting Clock Voice Assistant..."
python src/main.py
