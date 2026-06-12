import sounddevice as sd
import numpy as np


class AudioPlayback:
    def __init__(self, device: str = "default", sample_rate: int = 24000):
        self.device = device
        self.sample_rate = sample_rate

    def play(self, audio_bytes: bytes, sample_rate: int | None = None) -> None:
        sr = sample_rate or self.sample_rate
        samples = np.frombuffer(audio_bytes, dtype=np.int16)
        sd.play(samples, samplerate=sr, device=self.device)
        sd.wait()

    def play_blocking(self, audio_bytes: bytes, sample_rate: int = 24000) -> None:
        self.play(audio_bytes, sample_rate)
