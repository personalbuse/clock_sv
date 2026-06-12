class AudioPlayback:
    def __init__(self, device: str = "default", sample_rate: int = 24000,
                 volume_gain: float = 1.0):
        self.device = device
        self.sample_rate = sample_rate
        self.volume_gain = volume_gain

    def play(self, audio_bytes: bytes, sample_rate: int | None = None) -> None:
        import numpy as np
        import sounddevice as sd
        sr = sample_rate or self.sample_rate
        samples = np.frombuffer(audio_bytes, dtype=np.int16)
        if self.volume_gain != 1.0:
            samples = np.clip(
                samples.astype(np.float32) * self.volume_gain,
                -32768, 32767
            ).astype(np.int16)
        sd.play(samples, samplerate=sr, device=self.device)
        sd.wait()

    def play_blocking(self, audio_bytes: bytes, sample_rate: int = 24000) -> None:
        self.play(audio_bytes, sample_rate)
