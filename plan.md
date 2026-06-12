# Plan de Desarrollo — Asistente de Voz "Servidor Inteligente"

**Entorno objetivo:** Ubuntu Server 26.04 LTS (headless) — Intel i3-3217U (2 núcleos / 4 hilos, Ivy Bridge, sin AVX2), 6 GB RAM, audio HDA Intel PCH.
**Filosofía de diseño:** mover todo el cómputo pesado (LLM, TTS, STT principal) a APIs en la nube. El hardware local solo se encarga de: TUI, captura/reproducción de audio, VAD, *spotting* ligero de palabra clave y orquestación. Esto es clave para que el equipo responda con fluidez.

---

## 1. Resumen ejecutivo

El sistema es un demonio contenerizado que:

1. Pinta una TUI (hora, fecha, clima de Pamplona, estado del asistente).
2. Escucha de forma continua con VAD + detección local de la palabra "servidor", o espera la tecla `x` (Push-to-Talk).
3. Al activarse, grava el audio del usuario y lo transcribe con **Groq Whisper API**.
4. Envía la transcripción a **Groq LLM API** (petición *stateless*, sin historial).
5. Convierte la respuesta de texto a voz con **Gemini `gemini-2.5-flash-preview-tts`**.
6. Reproduce el audio por la salida HDA Intel PCH.
7. Vuelve al estado de escucha (IDLE).

Cada ciclo es independiente: no se persiste contexto de conversación entre peticiones (requisito de arquitectura *sin estado*).

---

## 2. Arquitectura general

### 2.1 Diagrama de componentes

```
┌──────────────────────────────────────────────────────────────────────┐
│                         CONTENEDOR DOCKER                              │
│                                                                         │
│  ┌────────────┐      ┌────────────────┐      ┌─────────────────────┐ │
│  │   TUI       │◄────►│  Orquestador /  │◄────►│  Audio Manager       │ │
│  │ (Textual)   │      │ Máquina estados │      │ (sounddevice/ALSA)   │ │
│  └────────────┘      └───────┬─────────┘      └──────┬───────────────┘ │
│        ▲                     │                        │                 │
│        │ refresca cada 1s    │                        │ captura/playback│
│  ┌─────┴──────┐              │                        │                 │
│  │ Reloj/Fecha │              │                ┌───────▼───────┐         │
│  │ Clima       │              │                │ VAD (webrtcvad)│         │
│  └─────┬───────┘              │                │ + Wake-word    │         │
│        │ HTTP                 │                │ local (whisper │         │
│        ▼                      │                │ tiny, spotting)│         │
│ ┌────────────────┐            │                └───────┬────────┘         │
│ │ Open-Meteo API  │            │                        │ trigger          │
│ └────────────────┘            │                        ▼                  │
│                                │                ┌────────────────┐        │
│                                ├───────────────►│ STT: Groq       │        │
│                                │                │ Whisper API     │        │
│                                │                └───────┬────────┘        │
│                                │                        │ texto           │
│                                │                        ▼                  │
│                                ├───────────────►┌────────────────┐        │
│                                │                │ LLM: Groq API   │        │
│                                │                │ (stateless)     │        │
│                                │                └───────┬────────┘        │
│                                │                        │ respuesta       │
│                                │                        ▼                  │
│                                └───────────────►┌────────────────┐        │
│                                                  │ TTS: Gemini     │        │
│                                                  │ flash-preview-tts│       │
│                                                  └───────┬────────┘        │
│                                                          │ audio           │
│                                                          ▼                  │
│                                                  Salida ALSA (HDA Intel PCH)│
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 Máquina de estados del orquestador

```
        ┌────────┐   wake-word "servidor"  o tecla 'x'
        │  IDLE  │ ───────────────────────────────────┐
        └───┬────┘                                     │
            │                                          ▼
            │                                   ┌──────────────┐
            │  fin de silencio (VAD) /           │  LISTENING    │
            │  soltar tecla 'x'                  │ (grabando)    │
            │◄────────────────────────────────── └──────┬───────┘
            │                                            │ audio.wav
            ▼                                            ▼
     ┌─────────────┐   texto vacío/error      ┌──────────────────┐
     │   IDLE      │◄──────────────────────── │ TRANSCRIBING (STT)│
     └─────────────┘                          └─────────┬─────────┘
            ▲                                            │ texto
            │                                            ▼
            │                                  ┌──────────────────┐
            │                                  │ THINKING (LLM)    │
            │                                  └─────────┬─────────┘
            │                                            │ respuesta
            │                                            ▼
            │                                  ┌──────────────────┐
            └──────────────────────────────────│ SPEAKING (TTS +  │
                  fin de reproducción           │ reproducción)    │
                                                 └──────────────────┘
```

Cada transición se refleja en la TUI (panel de estado) para dar *feedback* visual inmediato al usuario, algo crítico en un servidor headless sin pantalla normalmente conectada.

---

## 3. Selección de stack tecnológico (guía de librerías)

### 3.1 Lenguaje

| Opción | Veredicto | Justificación |
|---|---|---|
| **Python 3.11+** | ✅ Recomendado | Ecosistema maduro para audio (PortAudio, webrtcvad), STT local (faster-whisper sobre CTranslate2 en C++), SDKs oficiales de Groq y Google GenAI, y TUI moderna (Textual). Las partes "pesadas" están escritas en C/C++ con bindings, por lo que el overhead de Python es marginal. |
| Go | ⚠️ Alternativa | Binario más liviano y menor RAM en reposo, TUI excelente (Bubble Tea). Pero requiere bindings CGO para PortAudio/whisper.cpp, sin SDKs oficiales de Groq/Gemini (hay que hablar HTTP a mano) y sin librería VAD tan probada como webrtcvad. Mayor esfuerzo de desarrollo para el mismo resultado. |
| Rust | ⚠️ Alternativa | Rendimiento excelente, pero curva de desarrollo más alta y ecosistema de SDKs de IA menos maduro. |

**Decisión: Python 3.11**, priorizando velocidad de desarrollo y madurez de librerías de audio/IA, compensando el overhead con llamadas a APIs externas para las tareas pesadas (LLM, TTS, STT principal).

### 3.2 TUI

| Librería | Rol | Por qué |
|---|---|---|
| **Textual** (Textualize) | Framework TUI principal | Basado en `asyncio`, ideal para refrescar reloj/clima en *background* sin bloquear la captura de audio. Soporta CSS (`.tcss`), widgets reactivos, funciona perfecto sobre SSH y en consola headless. Footprint en memoria muy bajo (~20-40 MB). |
| **Rich** | Render de texto/tablas | Dependencia de Textual, útil para *logging* formateado. |

Alternativa más ligera si se quisiera minimalismo extremo: `urwid` — pero Textual ofrece mejor productividad y soporte async nativo, esencial aquí.

### 3.3 Captura y reproducción de audio

| Librería | Rol | Por qué |
|---|---|---|
| **sounddevice** (wrapper de PortAudio) | Captura (mic) y reproducción (parlante) | API NumPy-friendly, bajo overhead, soporta selección explícita de dispositivo ALSA (`hw:0,0` / `default`). |
| **numpy** | Buffers de audio | Necesario para manipular frames PCM antes de VAD/STT. |
| `aplay` / `paplay` (CLI, vía `subprocess`) | *Fallback* de reproducción | Útil para pruebas rápidas de hardware (`scripts/check_audio.sh`) sin depender de Python. |

**ALSA vs PulseAudio:** en un servidor headless **no se recomienda PulseAudio** (añade complejidad de sockets/usuarios en Docker). Se configura ALSA directamente con un `asound.conf` que define `dmix`/`dsnoop` sobre `hw:0,0` (HDA Intel PCH), permitiendo acceso concurrente de lectura/escritura sin un *daemon* adicional.

### 3.4 VAD (Voice Activity Detection)

| Librería | Rol | Por qué |
|---|---|---|
| **webrtcvad** | Detección de actividad de voz | Wrapper de la librería VAD de WebRTC (C), procesamiento de frames de 10/20/30 ms, consumo de CPU prácticamente nulo. Ideal para correr 24/7 en un i3. |

### 3.5 Detección de palabra clave "servidor" (wake word)

Dos enfoques posibles; se documenta la decisión y la alternativa:

| Enfoque | Descripción | Pros | Contras |
|---|---|---|---|
| **A. Spotting con `faster-whisper` "tiny" (recomendado)** | webrtcvad detecta inicio de habla → se captura un buffer corto (1.5–2.5 s) → se transcribe localmente con el modelo **tiny** (cuantizado `int8`, CTranslate2) → si el texto contiene "servidor" (con coincidencia difusa para tolerar errores de ASR), se pasa a estado `LISTENING` completo. | No requiere entrenamiento de modelo propio; "servidor" es una palabra en español sin modelos preentrenados de wake-word disponibles. `tiny` int8 corre en ~0.3–1 s para 2 s de audio en un i3 (sin AVX2 pero con AVX). | Algo más de CPU que un motor dedicado de wake-word; falsos negativos posibles si la pronunciación es muy distinta. |
| **B. openWakeWord con modelo custom** | Entrenar un modelo ONNX específico para "servidor" usando datos sintéticos (TTS) + `openwakeword`. | Latencia mínima, CPU casi nula en reposo. | Requiere pipeline de entrenamiento, dataset de voces, y mantenimiento del modelo. Mayor esfuerzo inicial. |

**Decisión para el MVP: Opción A** (faster-whisper "tiny"), dejando la Opción B documentada como mejora futura (Sección 10) si se requiere reducir aún más el uso de CPU en reposo.

> Nota: el modelo `tiny` (≈ 75 MB en `int8`) se descarga una sola vez y se cachea en un volumen Docker (`asr_cache`), evitando descargas repetidas y mantiniendo el footprint de RAM bajo (~150-200 MB en uso).

### 3.6 STT principal (transcripción del comando completo)

| Servicio | Rol | Por qué |
|---|---|---|
| **Groq API – Whisper (`whisper-large-v3-turbo`)** | Transcripción del audio capturado tras la activación | Evita correr modelos grandes localmente; Groq ofrece inferencia muy rápida (segundos) vía endpoint compatible con OpenAI `/audio/transcriptions`. |

### 3.7 LLM

| Servicio | Rol | Por qué |
|---|---|---|
| **Groq API – Chat Completions** (`llama-3.1-8b-instant` por defecto, configurable) | Procesamiento de la petición del usuario | Cumple el requisito explícito. Modelo configurable vía `.env`/`config/settings.yaml` para ajustar velocidad vs. calidad. Cada llamada se hace **sin historial** (mensajes = `[system, user]` únicamente). |

### 3.8 TTS

| Servicio | Rol | Por qué |
|---|---|---|
| **Google Gemini `gemini-2.5-flash-preview-tts`** | Conversión de la respuesta a voz | Cumple el requisito explícito. Se invoca vía SDK `google-genai`, solicitando salida de audio (PCM) que luego se reproduce con `sounddevice`/ALSA. |

> ⚠️ Al ser un modelo *preview*, su firma de API (nombres de parámetros, voces disponibles, formato de muestreo) puede cambiar. El módulo `services/tts_gemini.py` debe aislar esta llamada detrás de una interfaz simple (`def synthesize(text: str) -> bytes`) para minimizar el impacto de futuros cambios.

### 3.9 Clima

| Servicio | Rol | Por qué |
|---|---|---|
| **Open-Meteo API** (sin API key) | Temperatura actual de Pamplona, Norte de Santander (lat ≈ 7.3742, lon ≈ -72.6477) | Gratuita, sin autenticación, baja latencia. Se consulta cada 10–15 min (no cada segundo) para no saturar la API y mantener la TUI responsiva. |

### 3.10 Resumen de dependencias Python (`requirements.txt`)

```
textual
rich
sounddevice
numpy
webrtcvad
faster-whisper
groq
google-genai
requests
python-dotenv
pyyaml
rapidfuzz
```

(`rapidfuzz` se usa para la coincidencia difusa de la palabra clave "servidor" contra la transcripción del modelo `tiny`.)

---

## 4. Estructura de directorios

```
voice-assistant-server/
├── plan.md
├── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .dockerignore
├── config/
│   ├── settings.yaml          # configuración general (idioma, modelos, umbrales VAD)
│   └── asound.conf             # configuración ALSA (dmix/dsnoop sobre HDA Intel PCH)
├── src/
│   ├── main.py                 # punto de entrada, arranca TUI + orquestador
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py      # máquina de estados IDLE→LISTENING→...→SPEAKING
│   │   └── events.py            # definición de eventos internos (Textual messages)
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── app.py                # App Textual principal
│   │   ├── styles.tcss           # estilos de la interfaz
│   │   └── widgets/
│   │       ├── __init__.py
│   │       ├── clock_widget.py    # hora, fecha dd-mm-aa, día de la semana
│   │       ├── weather_widget.py  # temperatura Pamplona (Open-Meteo)
│   │       └── status_widget.py   # estado del asistente + log de actividad
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── capture.py             # captura de audio vía sounddevice/ALSA
│   │   ├── playback.py            # reproducción de audio de respuesta
│   │   ├── vad.py                 # wrapper de webrtcvad
│   │   └── wakeword.py            # spotting local con faster-whisper "tiny"
│   ├── services/
│   │   ├── __init__.py
│   │   ├── stt_groq.py            # cliente STT (Groq Whisper API)
│   │   ├── llm_groq.py            # cliente LLM (Groq Chat Completions, stateless)
│   │   ├── tts_gemini.py          # cliente TTS (Gemini flash-preview-tts)
│   │   └── weather_open_meteo.py  # cliente clima (Open-Meteo)
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # carga de config.yaml + variables de entorno
│       └── logging_config.py      # configuración de logging a archivo/TUI
├── models/
│   └── whisper-tiny/               # cache del modelo tiny (volumen Docker)
├── scripts/
│   ├── entrypoint.sh               # valida dispositivo de audio y lanza la app
│   └── check_audio.sh              # prueba rápida de grabación/reproducción ALSA
└── tests/
    ├── test_vad.py
    ├── test_wakeword.py
    ├── test_services_mock.py       # mocks de Groq/Gemini/Open-Meteo
    └── test_orchestrator.py
```

---

## 5. Fases de desarrollo

### Fase 0 — Setup del entorno (1-2 días)

- Preparar Ubuntu Server 26.04: actualizar paquetes, instalar Docker + Docker Compose plugin.
- Verificar el dispositivo de audio: `aplay -l` / `arecord -l` deben mostrar `HDA Intel PCH` como `card 0`.
- Crear `config/asound.conf` y validarlo en el host con `scripts/check_audio.sh` (grabar 3s y reproducir).
- Inicializar repositorio con la estructura de directorios de la Sección 4.
- Crear `.env` a partir de `.env.example` con `GROQ_API_KEY` y `GOOGLE_API_KEY` (Gemini).
- **Entregable:** repo con estructura vacía + scripts de diagnóstico de audio funcionando en el host.

### Fase 1 — Lógica de TUI (2-3 días)

- Implementar `tui/app.py` con layout base (Textual `Grid`/`Vertical`): panel superior (reloj/fecha), panel lateral (clima), panel inferior (estado del asistente + log).
- `widgets/clock_widget.py`: actualización cada segundo, formato `dd-mm-aa` + día de la semana (usar `locale`/`babel` o mapeo manual para nombres en español).
- `widgets/weather_widget.py`: consulta a `services/weather_open_meteo.py` cada 10-15 min en background (worker de Textual), muestra temperatura actual de Pamplona.
- `widgets/status_widget.py`: muestra el estado actual de la máquina de estados (IDLE/LISTENING/...) y un log de los últimos eventos (transcripción, respuesta LLM, etc.).
- Implementar manejo de tecla `x` para Push-to-Talk (key down = empieza a grabar, key up o segunda pulsación = detiene grabación — Textual entrega eventos `key`, se puede simular mantener con *toggle* si el terminal no distingue press/release).
- **Entregable:** TUI funcional mostrando reloj, fecha y clima reales, con un panel de estado que aún no reacciona a audio.

### Fase 2 — Pipeline de audio: VAD, wake word y PTT (3-4 días)

- `audio/capture.py`: stream continuo de `sounddevice` a 16 kHz mono, en chunks de 20 ms (formato requerido por webrtcvad).
- `audio/vad.py`: wrapper de `webrtcvad` con nivel de agresividad configurable (recomendado: 2 o 3 para entornos con ruido de servidor).
- `audio/wakeword.py`: al detectar inicio de habla (VAD), acumula ~2 s de audio, transcribe con `faster-whisper` (`tiny`, `int8`, `compute_type="int8"`, `device="cpu"`), compara con "servidor" usando `rapidfuzz.fuzz.partial_ratio` (umbral configurable, ej. 80).
- `core/orchestrator.py`: implementa la máquina de estados de la Sección 2.2, escuchando eventos de `audio/vad.py`, `audio/wakeword.py` y la tecla `x`.
- Integrar logs de cada transición de estado en `status_widget`.
- **Entregable:** el sistema detecta "servidor" o `x`, graba el comando hasta silencio (VAD) o liberación de tecla, y guarda un `.wav` temporal — visible en la TUI.

### Fase 3 — Integración STT (Groq Whisper) (1-2 días)

- `services/stt_groq.py`: función `transcribe(audio_bytes) -> str` usando el SDK `groq` (`client.audio.transcriptions.create(model="whisper-large-v3-turbo", ...)`).
- Manejo de errores de red (timeouts, reintentos con backoff corto, 1-2 intentos máximo para no bloquear la TUI).
- Conectar al orquestador: estado `TRANSCRIBING` → llama a `stt_groq.transcribe()` → si texto vacío, vuelve a `IDLE` con mensaje en el log.
- **Entregable:** al decir "servidor, ¿qué hora es?", la TUI muestra la transcripción correcta en el panel de estado.

### Fase 4 — Integración LLM (Groq) (1-2 días)

- `services/llm_groq.py`: función `ask(prompt: str) -> str`, usando `client.chat.completions.create(model=..., messages=[{"role":"system","content":SYSTEM_PROMPT}, {"role":"user","content":prompt}])`.
- `SYSTEM_PROMPT` definido en `config/settings.yaml` (tono, idioma español, brevedad de respuestas — importante para minimizar latencia de TTS).
- **Sin estado**: no se guarda `messages` entre invocaciones; cada llamada es independiente (cumpliendo el requisito 5).
- Conectar al orquestador: estado `THINKING` → `llm_groq.ask()` → respuesta de texto.
- **Entregable:** el asistente responde coherentemente (texto visible en TUI) a preguntas simples.

### Fase 5 — Integración TTS (Gemini) (2-3 días)

- `services/tts_gemini.py`: función `synthesize(text: str) -> bytes` (PCM/WAV), usando `google-genai` con `model="gemini-2.5-flash-preview-tts"` y configuración de voz en español.
- `audio/playback.py`: reproduce el audio recibido vía `sounddevice.play()` apuntando al dispositivo ALSA configurado (`hw:0,0` / `default` según `asound.conf`).
- Conectar al orquestador: estado `SPEAKING` → `tts_gemini.synthesize()` → `playback.play()` → vuelta a `IDLE`.
- Manejo de fallback: si Gemini TTS falla (cuota, error de red), registrar el error y mostrar la respuesta solo en texto (no bloquear el ciclo).
- **Entregable:** ciclo completo end-to-end: "servidor" → pregunta → respuesta hablada por el parlante.

### Fase 6 — Orquestación, robustez y configuración (2 días)

- Centralizar configuración en `config/settings.yaml` + `.env` (claves API, coordenadas de Pamplona, umbrales VAD, palabra clave, modelo LLM, voz TTS).
- Añadir *timeouts* globales por etapa (STT, LLM, TTS) para evitar que el asistente se quede "colgado" en un estado.
- Manejo de errores unificado: cualquier excepción en `services/*` se captura, se registra en el log de la TUI y el orquestador regresa a `IDLE`.
- Pruebas unitarias (`tests/`) con mocks de las APIs externas para validar transiciones de la máquina de estados sin gastar cuota de API.
- **Entregable:** sistema resiliente — fallos de red/API no detienen el loop principal.

### Fase 7 — Dockerización (2 días)

- Escribir `Dockerfile` (imagen `python:3.11-slim`, dependencias de sistema para audio: `alsa-utils`, `libasound2`, `portaudio19-dev`, `ffmpeg`, `libsndfile1`).
- Escribir `docker-compose.yml`: mapeo de `/dev/snd`, `group_add: audio`, `env_file: .env`, volumen para cache de modelos (`models/`), límites de memoria/CPU (`mem_limit`, `cpus`) acordes al hardware.
- Montar `config/asound.conf` dentro del contenedor (`/etc/asound.conf`).
- `scripts/entrypoint.sh`: valida que `/dev/snd` exista y que `aplay -l` detecte la tarjeta antes de lanzar `python -m src.main`.
- Probar `docker compose up` en el servidor real, validando TUI por SSH (`docker compose attach` o `docker attach`) y audio físico.
- **Entregable:** `docker compose up -d` levanta el asistente completo, persistente y reiniciable (`restart: unless-stopped`).

### Fase 8 — Pruebas, optimización y despliegue (2-3 días)

- Medir consumo de CPU/RAM en reposo (target: < 300 MB RAM, < 10% CPU promedio en `IDLE` con VAD activo).
- Ajustar nivel de agresividad de VAD y tamaño de buffer de wake-word para minimizar falsos positivos/negativos en ambiente real (ruido de ventiladores del servidor).
- Ajustar `SYSTEM_PROMPT` para respuestas cortas (reduce tiempo de TTS y reproducción).
- Documentar en `README.md`: instalación, configuración de `.env`, comandos de arranque/parada, *troubleshooting* de audio.
- Configurar `docker-compose.yml` con `restart: unless-stopped` y, opcionalmente, un `systemd` unit que ejecute `docker compose up -d` al boot del servidor.
- **Entregable:** sistema en producción, documentado, con métricas base de rendimiento registradas.

---

## 6. Configuración de audio (ALSA, host + Docker)

1. **En el host (Ubuntu Server 26.04):**
   ```bash
   aplay -l   # confirmar "HDA Intel PCH" como card 0
   arecord -l # confirmar dispositivo de captura disponible
   sudo usermod -aG audio $USER
   ```

2. **`config/asound.conf`** (montado como `/etc/asound.conf` en el contenedor): define `dmix`/`dsnoop` sobre `hw:0,0` a 16 kHz / S16_LE, de modo que captura y reproducción puedan coexistir sin PulseAudio.

3. **Docker:** se evita PulseAudio. El contenedor accede directamente al hardware vía:
   ```yaml
   devices:
     - /dev/snd:/dev/snd
   group_add:
     - audio
   ```
   y el usuario `appuser` dentro del contenedor se crea con `--group-add audio` en el `Dockerfile`.

4. **Diagnóstico rápido (`scripts/check_audio.sh`):** grabación de 3 s + reproducción inmediata, para validar el *pipeline* completo antes de depender de Python.

---

## 7. Variables de entorno (`.env`)

| Variable | Descripción | Ejemplo |
|---|---|---|
| `GROQ_API_KEY` | API key de Groq (STT + LLM) | `gsk_...` |
| `GOOGLE_API_KEY` | API key de Google AI (Gemini TTS) | `AIza...` |
| `LLM_MODEL` | Modelo de Groq para chat | `llama-3.1-8b-instant` |
| `STT_MODEL` | Modelo de Groq para transcripción | `whisper-large-v3-turbo` |
| `TTS_MODEL` | Modelo de Gemini TTS | `gemini-2.5-flash-preview-tts` |
| `TTS_VOICE` | Voz Gemini (español) | `es-ES-...` (verificar voces disponibles) |
| `WAKE_WORD` | Palabra clave | `servidor` |
| `WAKE_WORD_THRESHOLD` | Umbral de similitud (rapidfuzz) | `80` |
| `PTT_KEY` | Tecla Push-to-Talk | `x` |
| `LAT` / `LON` | Coordenadas Pamplona, N. de Santander | `7.3742` / `-72.6477` |
| `VAD_AGGRESSIVENESS` | 0-3, sensibilidad VAD | `2` |
| `TZ` | Zona horaria | `America/Bogota` |

---

## 8. Consideraciones de rendimiento para el hardware (i3-3217U / 6 GB RAM)

- **Sin modelos LLM/TTS locales**: toda la carga pesada va a Groq/Gemini, dejando CPU/RAM disponibles para audio + TUI.
- **`faster-whisper "tiny" int8`** es el único modelo local; su footprint (~150-200 MB RAM en uso, picos breves de CPU) es aceptable en 6 GB.
- **VAD continuo (`webrtcvad`)** consume CPU despreciable (microsegundos por frame de 20 ms), por lo que puede correr indefinidamente sin afectar la TUI.
- **Textual** usa renderizado diferencial; con refresco de 1 Hz para reloj/clima el impacto es mínimo.
- **Límites en `docker-compose.yml`** (`mem_limit: 1.5g`, `cpus: 2.0`) actúan como salvaguarda para que el contenedor nunca agote la RAM del host (deja ~4.5 GB libres para el sistema operativo y otros servicios).
- **Evitar AVX2**: al compilar/instalar `faster-whisper` (CTranslate2), confirmar que la rueda (`wheel`) instalada use solo instrucciones AVX (Ivy Bridge no soporta AVX2); el paquete oficial de PyPI ya distribuye binarios compatibles.

---

## 9. Roadmap futuro (mejoras opcionales)

1. **Wake word dedicada (openWakeWord/Porcupine)** entrenada para "servidor", reduciendo aún más el uso de CPU en reposo (Opción B de la Sección 3.5).
2. **Cache de respuestas de clima** persistente para sobrevivir reinicios sin esperar el primer fetch.
3. **Modo "conversación con contexto"** opcional (fuera del alcance *stateless* actual), activable por configuración, manteniendo un historial corto en memoria por sesión de uso.
4. **Métricas Prometheus** (latencia por etapa: STT/LLM/TTS) expuestas en un endpoint interno para monitoreo.
5. **Soporte multi-idioma** dinámico (detección de idioma en STT → ajustar `SYSTEM_PROMPT` y voz TTS).
