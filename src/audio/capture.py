import queue
import threading

import numpy as np
import sounddevice as sd


class AudioCapture:
    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 device: str = "default", dtype: str = "int16"):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.dtype = dtype
        self.stream: sd.InputStream | None = None
        self.callback_fn = None
        self._event = threading.Event()
        self._error = None

    def start(self, callback_fn) -> bool:
        self.callback_fn = callback_fn
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device,
                dtype=self.dtype,
                callback=self._audio_callback,
                blocksize=320,
            )
            self.stream.start()
            return True
        except Exception as e:
            self._error = str(e)
            return False

    @property
    def error(self) -> str | None:
        return self._error

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            return
        chunk = indata.flatten().tobytes()
        if self.callback_fn:
            self.callback_fn(chunk)

    def stop(self) -> None:
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
