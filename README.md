# Servidor Inteligente

Asistente de voz con TUI minimalista, VAD, wake-word local.
Soporta **dos modos** de operacion:

| Modo | STT | LLM | TTS |
|------|-----|-----|-----|
| **Cloud** (local dev) | Groq Whisper | Groq Llama | Gemini |
| **Local** (servidor) | faster-whisper | Ollama (qwen2.5) | Piper |

Seleccion del modo via `LLM_PROVIDER` / `STT_PROVIDER` en `.env` o `settings.yaml`.

---

## Modo Cloud (desarrollo local)

1. `cp .env.example .env` y llenar `GROQ_API_KEY`, `GOOGLE_API_KEY`
2. Verificar que `.env` tenga `LLM_PROVIDER=groq`, `STT_PROVIDER=groq`
3. Ejecutar:
   ```bash
   python src/main.py
   ```

## Modo Local (servidor headless)

1. Instalar Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull qwen2.5:3b
   ```
2. Instalar dependencias Python:
   ```bash
   pip install -r requirements.txt
   ```
3. Verificar audio:
   ```bash
   scripts/check_audio.sh
   ```
4. Ejecutar:
   ```bash
   ./run.sh
   ```

## Configuracion por environment

| Variable | Valores | Default |
|----------|---------|---------|
| `LLM_PROVIDER` | `groq` / `ollama` | `ollama` |
| `STT_PROVIDER` | `groq` / `local` | `local` |
| `TTS_PROVIDER` | `piper` / `gemini` | `piper` |
| `LLM_MODEL` | cualquier modelo | `qwen2.5:3b` (ollama) / `llama-3.1-8b-instant` (groq) |
| `STT_MODEL` | cualquier modelo | `base` (local) / `whisper-large-v3-turbo` (groq) |

## Controles TUI

- `x`: Push-to-Talk (mantener para grabar)
- `C`: Cancelar operacion actual
- `L`: Alternar panel de logs
- `H`: Historial de conversaciones (flechas para navegar, Enter para seleccionar)
- Palabra clave: "servidor" (activacion automatica)

## Deploy a servidor remoto

```bash
bash scripts/deploy.sh              # rsync a dabuma@192.168.1.25
bash scripts/deploy.sh usuario@host  # a otro destino
```

El script sincroniza el codigo via rsync e instala dependencias Python en el remoto.

## Estructura

```
src/
├── main.py                # punto de entrada
├── core/                  # orquestador + maquina de estados
├── tui/                   # interfaz Textual (clock, clima, estado)
├── audio/                 # VAD, wake-word, captura, playback
├── services/              # STT, LLM, TTS, clima, busqueda web
└── utils/                 # config, logging
config/                    # settings.yaml, asound.conf
scripts/                   # entrypoint, diagnostico, deploy
tests/                     # tests unitarios con mocks
```

## Licencia

MIT
