#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-dabuma@192.168.1.22}"

echo "=== Ensamblando service file ==="
SVC_NAME="clock.service"
cat > /tmp/clock.service << 'SVC'
[Unit]
Description=Clock Voice Assistant
After=network-online.target sound.target
Wants=network-online.target sound.target

[Service]
Type=forking
ExecStartPre=/usr/bin/pulseaudio --start
ExecStart=/usr/bin/screen -dmS clock bash -c '
  export XDG_RUNTIME_DIR=/run/user/$(id -u)
  export TZ=America/Bogota
  export PYTHONPATH=/home/dabuma/clock_sv
  cd /home/dabuma/clock_sv
  source venv/bin/activate
  exec python src/main.py
'
ExecStop=/usr/bin/screen -S clock -X quit
User=dabuma
Group=dabuma
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVC

echo "=== Subiendo service ==="
rsync /tmp/clock.service "$HOST:/tmp/$SVC_NAME"

echo "=== Instalando en remote ==="
ssh "$HOST" "
  echo 1234 | sudo -S mv /tmp/$SVC_NAME /etc/systemd/system/$SVC_NAME
  echo 1234 | sudo -S systemctl daemon-reload
  echo 1234 | sudo -S systemctl enable $SVC_NAME
  echo 1234 | sudo -S systemctl restart $SVC_NAME
  sleep 2
  systemctl status $SVC_NAME --no-pager | head -10
"

echo "=== Conectate ==="
echo "  ssh -t $HOST screen -r clock"
echo "  Ctrl+A D para detachar"
