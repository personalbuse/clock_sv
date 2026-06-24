import threading

import numpy as np
import sounddevice as sd

_CHUNK = 2048


class AudioPlayback:
    def __init__(self, device: str = "default", sample_rate: int = 24000,
                 volume_gain: float = 1.0):
        self.device = device
        self.sample_rate = sample_rate
        self.volume_gain = volume_gain
        self._playback_thread = None
        self._stop_event = threading.Event()

    def play(self, audio_bytes: bytes, sample_rate: int | None = None) -> None:
        sr = sample_rate or self.sample_rate
        samples = np.frombuffer(audio_bytes, dtype=np.int16)
        if self.volume_gain != 1.0:
            samples = np.clip(
                samples.astype(np.float32) * self.volume_gain,
                -32768, 32767
            ).astype(np.int16)

        self._stop_event.clear()

        try:
            stream = sd.OutputStream(
                samplerate=sr, device=self.device,
                channels=1, dtype="int16",
            )
            stream.start()
        except Exception:
            return

        try:
            for i in range(0, len(samples), _CHUNK):
                if self._stop_event.is_set():
                    break
                chunk = samples[i:i + _CHUNK]
                stream.write(chunk)
        except Exception:
            pass
        finally:
            try:
                stream.stop()
            except Exception:
                pass
            try:
                stream.close()
            except Exception:
                pass

    def play_async(self, audio_bytes: bytes, sample_rate: int | None = None) -> None:
        if self._playback_thread and self._playback_thread.is_alive():
            self.stop()
        self._playback_thread = threading.Thread(
            target=self.play, args=(audio_bytes, sample_rate), daemon=True
        )
        self._playback_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._playback_thread and self._playback_thread is not threading.current_thread():
            self._playback_thread.join(timeout=5)

    def play_blocking(self, audio_bytes: bytes, sample_rate: int = 24000) -> None:
        self.play(audio_bytes, sample_rate)
