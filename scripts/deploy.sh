#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-dabuma@192.168.1.25}"
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
echo "=== Installing / updating Python deps ==="
ssh "$HOST" "cd '$DEST' && pip install -r requirements.txt 2>/dev/null || true"

echo ""
echo "=== Done ==="
echo "Sync completado."
echo "Ejecutar en remote:"
echo "  ssh $HOST 'cd $DEST && ./run.sh'"
