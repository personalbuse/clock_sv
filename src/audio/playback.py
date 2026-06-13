import threading


class AudioPlayback:
    def __init__(self, device: str = "default", sample_rate: int = 24000,
                 volume_gain: float = 1.0):
        self.device = device
        self.sample_rate = sample_rate
        self.volume_gain = volume_gain
        self._stream = None
        self._playback_thread = None

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

    def play_async(self, audio_bytes: bytes, sample_rate: int | None = None) -> None:
        """Play audio in background thread (non-blocking)."""
        if self._playback_thread and self._playback_thread.is_alive():
            self.stop()
        self._playback_thread = threading.Thread(
            target=self.play, args=(audio_bytes, sample_rate), daemon=True
        )
        self._playback_thread.start()

    def stop(self) -> None:
        """Stop current playback."""
        import sounddevice as sd
        try:
            sd.stop()
        except Exception:
            pass
        if self._playback_thread and self._playback_thread is not threading.current_thread():
            self._playback_thread.join(timeout=2)

    def play_blocking(self, audio_bytes: bytes, sample_rate: int = 24000) -> None:
        self.play(audio_bytes, sample_rate)
