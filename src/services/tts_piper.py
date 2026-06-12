import io
import wave

from piper import PiperVoice


class PiperTTS:
    def __init__(self, model_path: str):
        self.voice = PiperVoice.load(model_path)
        self.sample_rate = self.voice.config.sample_rate

    def synthesize(self, text: str) -> bytes:
        chunks = []
        for chunk in self.voice.synthesize(text):
            chunks.append(chunk.audio_int16_bytes)
        return b"".join(chunks)
