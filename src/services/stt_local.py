import os

os.environ.setdefault("TOKENIZERS_PARALLELISM", "0")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("HUGGINGFACE_HUB_DISABLE_PROGRESS_BARS", "1")

import io
import wave

import numpy as np
from faster_whisper import WhisperModel

_model = None
_model_name = ""
_warmed = False


def _patch_tqdm_lock() -> None:
    import threading
    try:
        import tqdm.std
        lock = threading.RLock()
        tqdm.std.TqdmDefaultWriteLock.mp_lock = lock
        tqdm.std.TqdmDefaultWriteLock.th_lock = lock
        tqdm.std.TqdmDefaultWriteLock.create_mp_lock = staticmethod(lambda: None)
    except Exception:
        pass


def warmup(model_name: str = "base", device: str = "cpu",
           compute_type: str = "int8") -> None:
    global _model, _model_name, _warmed
    if _warmed:
        return
    _patch_tqdm_lock()
    _model = WhisperModel(model_name, device=device, compute_type=compute_type)
    _model_name = model_name
    _warmed = True


def transcribe(audio_bytes: bytes, model_name: str = "base",
               device: str = "cpu", compute_type: str = "int8",
               timeout: int = 30) -> str:
    global _model, _model_name, _warmed

    if not _warmed or _model_name != model_name:
        warmup(model_name, device, compute_type)

    try:
        with io.BytesIO(audio_bytes) as buf:
            with wave.open(buf, "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

        segments, _ = _model.transcribe(audio, language="es", beam_size=5)
        result = " ".join(seg.text for seg in segments)
        return result.strip()
    except Exception as e:
        raise RuntimeError(f"Local STT failed: {e}") from e
