import logging
import sys

NOISY_LOGGERS = [
    "httpx", "urllib3", "requests", "huggingface_hub",
    "faster_whisper", "sounddevice", "google.genai",
    "groq", "httpcore", "openai",
]


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
