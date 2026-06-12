#!/usr/bin/env bash
set -euo pipefail

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export TZ=America/Bogota
export PYTHONPATH=/home/dabuma/clock_sv

cd /home/dabuma/clock_sv
source venv/bin/activate

exec screen -dmS clock python src/main.py
