import io
import threading

from enum import Enum, auto

import numpy as np

from src.audio.capture import AudioCapture
from src.audio.vad import VAD
from src.audio.wakeword import WakeWordDetector
from src.core.events import AssistantEvent
from src.tui.widgets.status_widget import StatusWidget


class State(Enum):
    IDLE = auto()
    LISTENING = auto()
    TRANSCRIBING = auto()
    THINKING = auto()
    SPEAKING = auto()


class Orchestrator:
    def __init__(self, config: dict, status_widget: StatusWidget):
        self.config = config
        self.status = status_widget
        self.state = State.IDLE

        ac = config.get("audio", {})
        vc = config.get("vad", {})
        wc = config.get("wake_word", {})

        self.vad = VAD(
            aggressiveness=vc.get("aggressiveness", 2),
            sample_rate=vc.get("sample_rate", 16000),
            frame_ms=vc.get("frame_ms", 20),
        )
        self.wakeword = WakeWordDetector(
            word=wc.get("word", "servidor"),
            threshold=wc.get("threshold", 80),
            model_size=wc.get("model_size", "tiny"),
            compute_type=wc.get("compute_type", "int8"),
        )
        self.capture = AudioCapture(
            sample_rate=ac.get("sample_rate", 16000),
            device=ac.get("device", "default"),
        )

        self._audio_buffer: list[bytes] = []
        self._speech_frames = 0
        self._silence_frames = 0
        self._silence_timeout = 30

        self._groq_api_key = config.get("groq_api_key", "")
        self._google_api_key = config.get("google_api_key", "")
        self._stt_model = config.get("stt", {}).get(
            "model", "whisper-large-v3-turbo")
        self._llm_model = config.get("llm", {}).get(
            "model", "llama-3.1-8b-instant")

        tts_config = config.get("tts", {})
        self._tts_provider = tts_config.get("provider", "piper")
        self._tts_model = tts_config.get("gemini", {}).get(
            "model", "gemini-2.5-flash-preview-tts")
        self._tts_voice = tts_config.get("gemini", {}).get(
            "voice", "sadachbia")
        self._tts_piper_model_path = tts_config.get("piper", {}).get(
            "model_path", "models/piper/es_ES-carlfm-x_low.onnx")

    def start(self) -> None:
        self.status.set_state("IDLE")
        self.status.add_log("iniciando...")
        ok = self.capture.start(self._on_audio_chunk)
        if not ok:
            self.status.add_log(
                f"audio no disponible: {self.capture.error}")
            self.status.add_log("modo TUI solo visual (sin microfono)")
        else:
            self.status.add_log(
                "esperando palabra clave 'servidor', tecla 'x' (PTT) o 'c' (cancelar)")

    def stop(self) -> None:
        self.capture.stop()

    def _set_state(self, new_state: State) -> None:
        self.state = new_state
        self.status.set_state(new_state.name)

    def _on_audio_chunk(self, chunk: bytes) -> None:
        if self.state == State.IDLE:
            self._idle_loop(chunk)
        elif self.state == State.LISTENING:
            self._listening_loop(chunk)

    def _idle_loop(self, chunk: bytes) -> None:
        if self.vad.is_speech_chunk(chunk):
            if self.wakeword.feed(chunk):
                self._set_state(State.LISTENING)
                self.status.add_log("palabra clave detectada, escuchando...")
                self._audio_buffer = []
                self._speech_frames = 0
                self._silence_frames = 0
        else:
            self.wakeword.reset()

    def _listening_loop(self, chunk: bytes) -> None:
        self._audio_buffer.append(chunk)
        if self.vad.is_speech_chunk(chunk):
            self._speech_frames += 1
            self._silence_frames = 0
        else:
            self._silence_frames += 1

        if self._silence_frames > self._silence_timeout:
            self._on_command_ready()

    def _on_command_ready(self) -> None:
        self._set_state(State.TRANSCRIBING)
        self.status.add_log("silencio detectado, transcribiendo...")
        threading.Thread(target=self._process_pipeline, daemon=True).start()

    def _audio_bytes(self) -> bytes:
        raw = b"".join(self._audio_buffer)
        import struct
        sample_rate = 16000
        duration = len(raw) // (sample_rate * 2)
        if duration < 1:
            duration = 1
        data_size = len(raw)
        wav_header = (
            b"RIFF" +
            struct.pack("<I", 36 + data_size) +
            b"WAVE" +
            b"fmt " +
            struct.pack("<I", 16) +
            struct.pack("<HHIIHH", 1, 1, sample_rate,
                         sample_rate * 2, 2, 16) +
            b"data" +
            struct.pack("<I", data_size) +
            raw
        )
        return wav_header

    def _process_pipeline(self) -> None:
        try:
            from src.services.stt_groq import transcribe as stt_transcribe
            from src.services.llm_groq import ask as llm_ask
            from src.audio.playback import AudioPlayback

            audio_wav = self._audio_bytes()
            text = stt_transcribe(
                audio_wav, api_key=self._groq_api_key,
                model=self._stt_model)
            if not text:
                self.status.add_log("no se detecto voz")
                self._return_to_idle()
                return

            self.status.add_log(f"tu: {text}")
            self._set_state(State.THINKING)
            self.status.add_log("procesando respuesta...")

            reply = llm_ask(text, api_key=self._groq_api_key,
                            model=self._llm_model)
            self.status.add_log(f"asistente: {reply}")

            self._set_state(State.SPEAKING)
            self.status.add_log("hablando...")

            if self._tts_provider == "piper":
                from src.services.tts_piper import PiperTTS
                tts = PiperTTS(self._tts_piper_model_path)
                audio_data = tts.synthesize(reply)
                sample_rate = tts.sample_rate
            else:
                from src.services.tts_gemini import synthesize as tts_synth
                audio_data = tts_synth(
                    reply, api_key=self._google_api_key,
                    model=self._tts_model, voice=self._tts_voice)
                sample_rate = 24000

            playback = AudioPlayback(
                sample_rate=sample_rate,
                volume_gain=self.config.get("audio", {}).get("volume_gain", 1.0),
            )
            playback.play(audio_data)
        except Exception as e:
            self.status.add_log(f"error: {e}")
        finally:
            self._return_to_idle()

    def _return_to_idle(self) -> None:
        self._audio_buffer = []
        self._speech_frames = 0
        self._silence_frames = 0
        self._set_state(State.IDLE)
        self.status.add_log("esperando palabra clave 'servidor' o 'x'/'c'")

    def on_event(self, event: AssistantEvent, data=None) -> None:
        pass

    def press_ptt(self) -> None:
        if self.state == State.IDLE:
            self._set_state(State.LISTENING)
            self.status.add_log("Push-to-Talk activado")
            self._audio_buffer = []
            self._silence_frames = 0

    def release_ptt(self) -> None:
        if self.state == State.LISTENING and len(self._audio_buffer) > 0:
            self._on_command_ready()

    def cancel(self) -> None:
        """Cancel current operation and return to IDLE."""
        if self.state != State.IDLE:
            self.status.add_log("cancelado")
            self._return_to_idle()
