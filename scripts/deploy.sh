#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-dabuma@192.168.1.22}"
DEST="${2:-clock_sv}"

echo "=== Syncing code to $HOST:$DEST ==="
rsync -avz --delete \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='models' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='*.wav' \
    ./ "$HOST:$DEST/"

echo ""
echo "=== Done ==="
echo "Sync completado."
echo "Ejecutar en remote:"
echo "  ssh $HOST 'cd $DEST && ./run.sh'"
