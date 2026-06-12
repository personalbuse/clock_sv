# Clock Preferences

- Reloj: macro-digitos (█ ancho 6, 7 filas, 3 espacios separacion entre caracteres)
- Color: blanco solido bold (sin gradiente)
- Fecha: bold #cccccc, centrada debajo del reloj

# Deploy & Persistencia

- Remote: dabuma@192.168.1.22, server headless
- Deploy: bash scripts/deploy.sh (rsync, sin systemd)
- App se ejecuta manual: `cd clock_sv && ./run.sh` (wrapper que reinicia PulseAudio + app)
- Persistencia: NO systemd service (manual)
- Linger habilitado para dabuma
- Audio: device "default" via PulseAudio
- Volume gain: 8.0x en settings.yaml (ajustable via audio.volume_gain)
- ALSA hw:0,0 no soporta 16kHz directo; solo PulseAudio default funciona

# Controles TUI

- X: Push-to-Talk (grabar)
- C: Cancelar operación actual (incluso mientras habla)
- Palabra clave: "servidor" (activación automática)
