# Servidor Inteligente

Asistente de voz contenerizado con TUI minimalista, VAD, wake-word local y APIs cloud (Groq + Gemini).

## Requisitos

- Ubuntu Server 26.04 LTS (o similar con ALSA)
- Docker + Docker Compose plugin
- Dispositivo de audio ALSA (HDA Intel PCH)
- Conexion a internet

## Configuracion

1. Copiar `.env.example` a `.env` y rellenar claves:
   ```
   GROQ_API_KEY=gsk_...
   GOOGLE_API_KEY=AIza...
   ```

2. Verificar audio:
   ```bash
   scripts/check_audio.sh
   ```

## Uso

```bash
docker compose up -d
docker attach clock_sv-assistant-1   # ver TUI
```

Tecla `x`: Push-to-Talk (toggle).
Palabra clave: "servidor".

## Estructura

```
src/
├── main.py                # punto de entrada
├── core/                  # orquestador + maquina de estados
├── tui/                   # interfaz Textual (clock, clima, estado)
├── audio/                 # VAD, wake-word, captura, playback
├── services/              # STT (Groq), LLM (Groq), TTS (Gemini), clima
└── utils/                 # config, logging
config/                    # settings.yaml, asound.conf
scripts/                   # entrypoint, diagnostico
tests/                     # tests unitarios con mocks
```

## Licencia

MIT
