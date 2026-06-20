import io
import struct
import threading
from enum import Enum, auto

import numpy as np

from src.audio.capture import AudioCapture
from src.audio.vad import VAD
from src.audio.wakeword import WakeWordDetector
from src.commands.router import dispatch as cmd_dispatch
from src.core.conversation import ConversationManager
from src.core.events import AssistantEvent
from src.core.timers import TimerManager
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
        self._lock = threading.Lock()
        self._cancel_event = threading.Event()
        self._playback = None

        ac = config.get("audio", {})
        vc = config.get("vad", {})
        wc = config.get("wake_word", {})

        self.vad = VAD(
            aggressiveness=vc.get("aggressiveness", 2),
            sample_rate=vc.get("sample_rate", 16000),
            frame_ms=vc.get("frame_ms", 20),
        )

        wake_enabled = wc.get("enabled", True)
        if wake_enabled:
            self.wakeword = WakeWordDetector(
                word=wc.get("word", "servidor"),
                threshold=wc.get("threshold", 80),
                model_size=wc.get("model_size", "tiny"),
                compute_type=wc.get("compute_type", "int8"),
            )
        else:
            self.wakeword = None

        self.capture = AudioCapture(
            sample_rate=ac.get("sample_rate", 16000),
            device=ac.get("device", "default"),
        )

        self._audio_buffer: list[bytes] = []
        self._speech_frames = 0
        self._silence_frames = 0
        self._silence_timeout = 30
        self._max_listen_frames = 150

        self._groq_api_key = config.get("groq_api_key", "")
        self._google_api_key = config.get("google_api_key", "")
        self._system_prompt = config.get("system_prompt",
                                          "Eres un asistente de voz servidor inteligente. Responde siempre en espanol, de forma breve y directa.")

        llm_cfg = config.get("llm", {})
        stt_cfg = config.get("stt", {})
        self._llm_provider = llm_cfg.get("provider", "ollama")
        self._stt_provider = stt_cfg.get("provider", "local")
        self._llm_model = llm_cfg.get("groq", {}).get("model", "llama-3.1-8b-instant")
        self._stt_model = stt_cfg.get("groq", {}).get("model", "whisper-large-v3-turbo")
        self._llm_temp = llm_cfg.get("temperature", 0.7)
        self._llm_max_tokens = llm_cfg.get("max_tokens", 512)

        tts_config = config.get("tts", {})
        self._tts_provider = tts_config.get("provider", "piper")
        self._tts_model = tts_config.get("gemini", {}).get("model", "gemini-2.5-flash-preview-tts")
        self._tts_voice = tts_config.get("gemini", {}).get("voice", "sadachbia")
        self._tts_piper_model_path = tts_config.get("piper", {}).get("model_path", "models/piper/es_ES-carlfm-x_low.onnx")

        self.timers = TimerManager()
        self.timers.set_callback(self._on_timer_expire)

        self.conversations = ConversationManager()

    def set_timer_widget(self, widget) -> None:
        self._timer_widget = widget

    def set_chat_widget(self, widget) -> None:
        self._chat_widget = widget
        if widget:
            widget.set_manager(self.conversations)

    def _on_timer_expire(self, timer) -> None:
        self.status.add_log(f"timer expirado: {timer.label}")
        self._play_notification()

    def _play_notification(self) -> None:
        try:
            duration = 0.5
            sample_rate = 16000
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = np.sin(2 * np.pi * 880 * t) * 0.3
            tone[:int(sample_rate * 0.05)] *= np.linspace(0, 1, int(sample_rate * 0.05))
            tone[-int(sample_rate * 0.05):] *= np.linspace(1, 0, int(sample_rate * 0.05))
            audio = (tone * 32767).astype(np.int16).tobytes()
            from src.audio.playback import AudioPlayback
            p = AudioPlayback(sample_rate=sample_rate, volume_gain=1.0)
            p.play_blocking(audio)
        except Exception:
            pass

    def start(self) -> None:
        self.status.set_state("IDLE")
        self.status.add_log("iniciando...")
        self.timers.start()
        ok = self.capture.start(self._on_audio_chunk)
        if not ok:
            self.status.set_state("ERROR")
            self.status.add_log(f"error audio: {self.capture.error}")
        else:
            self.status.add_log("listo, esperando tecla X (PTT) o C")

    def stop(self) -> None:
        self.capture.stop()
        self.timers.stop()

    def _set_state(self, new_state: State) -> None:
        with self._lock:
            self.state = new_state
        self.status.set_state(new_state.name)

    def _on_audio_chunk(self, chunk: bytes) -> None:
        if self.state == State.IDLE:
            self._idle_loop(chunk)
        elif self.state == State.LISTENING:
            self._listening_loop(chunk)

    def _idle_loop(self, chunk: bytes) -> None:
        if not self.wakeword or not self.vad.is_speech_chunk(chunk):
            if self.wakeword:
                self.wakeword.reset()
            return
        if self.wakeword.feed(chunk):
            self._set_state(State.LISTENING)
            self._audio_buffer = []
            self._speech_frames = 0
            self._silence_frames = 0

    def _listening_loop(self, chunk: bytes) -> None:
        self._audio_buffer.append(chunk)
        if self.vad.is_speech_chunk(chunk):
            self._speech_frames += 1
            self._silence_frames = 0
        else:
            self._silence_frames += 1
        total_frames = self._speech_frames + self._silence_frames
        if self._silence_frames > self._silence_timeout or total_frames > self._max_listen_frames:
            self._on_command_ready()

    def _on_command_ready(self) -> None:
        if self._cancel_event.is_set():
            return
        self._set_state(State.TRANSCRIBING)
        self.status.add_log("transcribiendo...")
        threading.Thread(target=self._process_pipeline, daemon=True).start()

    def _audio_bytes(self) -> bytes:
        raw = b"".join(self._audio_buffer)
        sample_rate = 16000
        data_size = len(raw)
        wav_header = (
            b"RIFF"
            + struct.pack("<I", 36 + data_size)
            + b"WAVE"
            + b"fmt "
            + struct.pack("<I", 16)
            + struct.pack("<HHIIHH", 1, 1, sample_rate, sample_rate * 2, 2, 16)
            + b"data"
            + struct.pack("<I", data_size)
            + raw
        )
        return wav_header

    def _process_pipeline(self) -> None:
        try:
            self._cancel_event.clear()

            from src.audio.playback import AudioPlayback

            audio_wav = self._audio_bytes()

            if self._stt_provider == "local":
                from src.services.stt_local import transcribe as stt_transcribe
                local_cfg = self.config.get("stt", {}).get("local", {})
                text = stt_transcribe(
                    audio_wav,
                    model_name=local_cfg.get("model", "base"),
                    device=local_cfg.get("device", "cpu"),
                    compute_type=local_cfg.get("compute_type", "int8"),
                    timeout=self.config.get("stt", {}).get("timeout", 10),
                )
            else:
                from src.services.stt_groq import transcribe as stt_transcribe
                text = stt_transcribe(
                    audio_wav, api_key=self._groq_api_key,
                    model=self._stt_model, timeout=10)

            if self._cancel_event.is_set():
                return

            if not text:
                self.status.add_log("no se detecto voz")
                self._return_to_idle()
                return

            self.status.add_log(f"tu: {text}")
            self.conversations.add_message("user", text)

            cmd_result = cmd_dispatch(text)
            if cmd_result:
                reply, _ = cmd_result
                if self._cancel_event.is_set():
                    return
                self.status.add_log(f"asistente: {reply}")
                self._tts_and_speak(reply)
                return

            timer_result = self.timers.parse_command(text)
            if timer_result:
                reply, _ = timer_result
                if self._cancel_event.is_set():
                    return
                self.status.add_log(f"asistente: {reply}")
                self._tts_and_speak(reply)
                if self._timer_widget:
                    self._timer_widget.set_timers(self.timers.active_timers)
                return

            self._set_state(State.THINKING)
            self.status.add_log("procesando respuesta...")

            ctx = self.conversations.get_llm_context(self._system_prompt)
            ctx.append({"role": "user", "content": text})

            llm_cfg = self.config.get("llm", {})
            if self._llm_provider == "ollama":
                from src.services.llm_ollama import ask as llm_ask
                ollama_cfg = llm_cfg.get("ollama", {})
                reply = llm_ask(text,
                    endpoint=ollama_cfg.get("endpoint", "http://localhost:11434/v1"),
                    model=ollama_cfg.get("model", "qwen2.5:3b"),
                    temperature=llm_cfg.get("temperature", 0.7),
                    max_tokens=llm_cfg.get("max_tokens", 512),
                    timeout=llm_cfg.get("timeout", 15))
            else:
                from src.services.llm_groq import ask as llm_ask
                reply = llm_ask(text, api_key=self._groq_api_key,
                                model=self._llm_model, timeout=20)

            if self._cancel_event.is_set():
                return

            self.conversations.add_message("assistant", reply)
            self.status.add_log(f"asistente: {reply}")
            self._tts_and_speak(reply)

        except Exception as e:
            self.status.add_log(f"error: {e}")
        finally:
            self._return_to_idle()

    def _tts_and_speak(self, reply: str) -> None:
        from src.audio.playback import AudioPlayback
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
        self._playback = playback
        self._set_state(State.SPEAKING)
        playback.play_async(audio_data)
        if playback._playback_thread:
            playback._playback_thread.join(timeout=30)
            if playback._playback_thread.is_alive():
                playback.stop()

    def _return_to_idle(self) -> None:
        self._audio_buffer = []
        self._speech_frames = 0
        self._silence_frames = 0
        self._set_state(State.IDLE)
        if self._timer_widget:
            self._timer_widget.set_timers(self.timers.active_timers)

    def on_event(self, event: AssistantEvent, data=None) -> None:
        pass

    def press_ptt(self) -> None:
        if self.state == State.IDLE:
            self._set_state(State.LISTENING)
            self.status.add_log("escuchando...")
            self._audio_buffer = []
            self._speech_frames = 0
            self._silence_frames = 0

    def release_ptt(self) -> None:
        if self.state == State.LISTENING:
            if len(self._audio_buffer) > 0:
                self._on_command_ready()
            else:
                self._cancel_event.set()
                self._return_to_idle()
                self.status.add_log("cancelado")

    def cancel(self) -> None:
        try:
            with self._lock:
                if self.state == State.SPEAKING and self._playback:
                    self._playback.stop()
        except Exception:
            pass
        try:
            self._cancel_event.set()
            self._return_to_idle()
            self.status.add_log("cancelado")
        except Exception:
            pass
