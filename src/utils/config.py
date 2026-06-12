from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
import os


def load_config() -> dict[str, Any]:
    load_dotenv()

    config_path = Path(__file__).resolve().parents[2] / "config" / "settings.yaml"

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    cfg["groq_api_key"] = os.getenv("GROQ_API_KEY", "")
    cfg["google_api_key"] = os.getenv("GOOGLE_API_KEY", "")

    env_overrides = {
        "llm": ("model", "LLM_MODEL"),
        "stt": ("model", "STT_MODEL"),
        "tts": ("model", "TTS_MODEL"),
    }
    for section, (key, env_var) in env_overrides.items():
        val = os.getenv(env_var)
        if val:
            cfg[section][key] = val

    wake_word = os.getenv("WAKE_WORD")
    if wake_word:
        cfg["wake_word"]["word"] = wake_word

    threshold = os.getenv("WAKE_WORD_THRESHOLD")
    if threshold:
        cfg["wake_word"]["threshold"] = int(threshold)

    aggressiveness = os.getenv("VAD_AGGRESSIVENESS")
    if aggressiveness:
        cfg["vad"]["aggressiveness"] = int(aggressiveness)

    lat = os.getenv("LAT")
    lon = os.getenv("LON")
    if lat:
        cfg["weather"]["lat"] = float(lat)
    if lon:
        cfg["weather"]["lon"] = float(lon)

    return cfg
