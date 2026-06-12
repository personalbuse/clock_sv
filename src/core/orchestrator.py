from enum import Enum, auto

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

    def start(self) -> None:
        self.status.set_state("IDLE")
        self.status.add_log("esperando palabra clave 'servidor' o tecla 'x'")
        self.capture.start(self._on_audio_chunk)

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
