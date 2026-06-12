import webrtcvad


class VAD:
    def __init__(self, aggressiveness: int = 2, sample_rate: int = 16000,
                 frame_ms: int = 20):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.frame_size = sample_rate * frame_ms // 1000

    def is_speech(self, frame: bytes) -> bool:
        return self.vad.is_speech(frame, self.sample_rate)

    def is_speech_chunk(self, chunk: bytes) -> bool:
        if len(chunk) != self.frame_size * 2:
            return False
        return self.vad.is_speech(chunk, self.sample_rate)
