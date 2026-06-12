from faster_whisper import WhisperModel
from rapidfuzz import fuzz


class WakeWordDetector:
    def __init__(self, word: str = "servidor", threshold: int = 80,
                 model_size: str = "tiny", compute_type: str = "int8"):
        self.word = word.lower()
        self.threshold = threshold
        self.model = WhisperModel(model_size, device="cpu",
                                  compute_type=compute_type)
        self.buffer: list[bytes] = []
        self.buffer_ms = 2000
        self.sample_rate = 16000

    def feed(self, chunk: bytes) -> bool:
        self.buffer.append(chunk)
        total_ms = len(self.buffer) * 20
        if total_ms < self.buffer_ms:
            return False
        audio = b"".join(self.buffer)
        self.buffer = []
        import numpy as np
        samples = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(samples, beam_size=1)
        text = " ".join(seg.text for seg in segments).lower()
        score = fuzz.partial_ratio(self.word, text)
        return score >= self.threshold

    def reset(self) -> None:
        self.buffer = []
