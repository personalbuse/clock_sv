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
echo "=== Restarting app on remote ==="
ssh "$HOST" "cd $DEST && source venv/bin/activate && nohup python src/main.py > /tmp/clock_sv.log 2>&1 &"

echo ""
echo "=== Done ==="
echo "Logs: ssh $HOST 'tail -f /tmp/clock_sv.log'"
