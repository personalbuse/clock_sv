# Clock Preferences

- Reloj: macro-digitos (█ ancho 6, 7 filas, 3 espacios separacion entre caracteres)
- Color: blanco solido bold (sin gradiente)
- Fecha: bold #cccccc, centrada debajo del reloj

# Deploy & Persistencia

- Remote: dabuma@192.168.1.22, server headless
- Deploy: bash scripts/deploy.sh (rsync + systemd restart)
- App corre en screen session "clock" (ssh -t dabuma@... screen -r clock)
- Persistencia via systemd system service clock.service
  - ExecStartPre: pulseaudio --start
  - ExecStart: scripts/run_clock.sh (wrapper que exporta XDG_RUNTIME_DIR, TZ, PYTHONPATH)
  - Restart=always (se resucita sola si crashea)
  - Linger habilitado para dabuma
- Audio device: "default" via PulseAudio (único que soporta 16kHz input+output con PortAudio)
- Volume gain: 8.0x en settings.yaml (ajustable via audio.volume_gain)
- ALSA hw:0,0 no soporta 16kHz directo; sysdefault solo funciona para input
