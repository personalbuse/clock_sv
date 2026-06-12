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
echo "=== Reinstalling systemd service ==="
SVC_FILE=$(mktemp)
cat > "$SVC_FILE" << SVC
[Unit]
Description=Clock Voice Assistant
After=network-online.target sound.target
Wants=network-online.target sound.target

[Service]
Type=forking
ExecStartPre=-/usr/bin/screen -S clock -X quit
ExecStartPre=/usr/bin/pulseaudio --start
ExecStart=/home/dabuma/${DEST}/scripts/run_clock.sh
ExecStop=/usr/bin/screen -S clock -X quit
User=dabuma
Group=dabuma
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVC
rsync "$SVC_FILE" "$HOST:/tmp/clock.service"
rm "$SVC_FILE"
ssh "$HOST" "echo 1234 | sudo -S mv /tmp/clock.service /etc/systemd/system/clock.service"
ssh "$HOST" "echo 1234 | sudo -S systemctl daemon-reload"
ssh "$HOST" "echo 1234 | sudo -S systemctl enable clock.service"
ssh "$HOST" "echo 1234 | sudo -S systemctl restart clock.service"

echo ""
echo "=== Done ==="
echo "Connect: ssh -t $HOST screen -r clock"
echo "Detach:  Ctrl+A, D"
