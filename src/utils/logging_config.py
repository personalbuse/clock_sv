import logging
import sys
from pathlib import Path

NOISY_LOGGERS = [
    "httpx", "urllib3", "requests", "huggingface_hub",
    "faster_whisper", "sounddevice", "google.genai",
    "groq", "httpcore", "openai",
    "google.genai.models", "google",
]


def setup_logging(level: int = logging.DEBUG) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
    )

    fh = logging.FileHandler("clock_sv.log")
    fh.setFormatter(fmt)
    root.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    root.addHandler(sh)

    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
