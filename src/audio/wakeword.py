import pickle
import threading
from pathlib import Path

import numpy as np
from openwakeword.utils import AudioFeatures

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "wakeword" / "servidor_voz.pkl"
MODEL_FALLBACK = Path(__file__).parent.parent.parent / "models" / "wakeword" / "servidor_v0.1.pkl"
MIN_SAMPLES = 48000
CHECK_INTERVAL = 20
DEFAULT_THRESHOLD = 0.7


class WakeWordDetector:
    def __init__(self, word: str = "servidor", threshold: int = 80,
                 model_size: str = "", compute_type: str = ""):
        self.word = word.lower()
        self.threshold = max(0.1, min(0.99, threshold / 100.0))
        self._clf = None
        self._preprocessor = None
        self._lock = threading.Lock()
        self._score = 0.0
        self._load_error = None
        self._ring: list[bytes] = []
        self._ring_samples = 0
        self._counter = 0

    def _load(self) -> bool:
        if self._clf is not None:
            return True
        if self._load_error:
            return False
        try:
            model_file = MODEL_PATH
            if not model_file.exists():
                alt = Path("models/wakeword/servidor_voz.pkl")
                if alt.exists():
                    model_file = alt
                elif MODEL_FALLBACK.exists():
                    model_file = MODEL_FALLBACK
                else:
                    alt2 = Path("models/wakeword/servidor_v0.1.pkl")
                    if alt2.exists():
                        model_file = alt2
                    else:
                        self._load_error = f"modelo no encontrado"
                        return False
            with open(model_file, "rb") as f:
                self._clf = pickle.load(f)
            self._preprocessor = AudioFeatures()
            return True
        except Exception as e:
            self._load_error = str(e)
            return False

    def _get_audio(self) -> np.ndarray | None:
        if not self._ring:
            return None
        samples_bytes = b"".join(self._ring)
        audio = np.frombuffer(samples_bytes, dtype=np.int16)
        if len(audio) < MIN_SAMPLES:
            audio = np.pad(audio, (MIN_SAMPLES - len(audio), 0))
        return audio

    def feed(self, chunk: bytes) -> bool:
        if not self._load():
            return False
        self._ring.append(chunk)
        self._ring_samples += len(chunk) // 2
        while self._ring_samples > MIN_SAMPLES:
            dropped = self._ring.pop(0)
            self._ring_samples -= len(dropped) // 2
        self._counter += 1
        if self._counter % CHECK_INTERVAL != 0:
            return False
        audio = self._get_audio()
        if audio is None:
            return False
        rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
        if rms < 100:
            return False
        emb = self._preprocessor._get_embeddings(audio)
        if emb is None or emb.size == 0:
            return False
        proba = self._clf.predict_proba(emb.flatten().reshape(1, -1))[0]
        self._score = float(proba[1])
        return self._score >= self.threshold

    def reset(self) -> None:
        self._score = 0.0
        self._ring = []
        self._ring_samples = 0
        self._counter = 0

    @property
    def score(self) -> float:
        return self._score
