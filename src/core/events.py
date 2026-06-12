from enum import Enum, auto


class AssistantEvent(Enum):
    WAKE_WORD_DETECTED = auto()
    PTT_PRESSED = auto()
    PTT_RELEASED = auto()
    SILENCE_DETECTED = auto()
    TRANSCRIPTION_READY = auto()
    TRANSCRIPTION_FAILED = auto()
    LLM_RESPONSE_READY = auto()
    LLM_FAILED = auto()
    TTS_READY = auto()
    TTS_FAILED = auto()
    PLAYBACK_FINISHED = auto()
    ERROR = auto()
