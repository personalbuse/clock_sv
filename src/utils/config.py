from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
import os


def load_config() -> dict[str, Any]:
    load_dotenv(override=True)

    config_path = Path(__file__).resolve().parents[2] / "config" / "settings.yaml"

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    cfg["groq_api_key"] = os.getenv("GROQ_API_KEY", "")
    cfg["google_api_key"] = os.getenv("GOOGLE_API_KEY", "")

    env_overrides = [
        ("llm", "provider", "LLM_PROVIDER"),
        ("stt", "provider", "STT_PROVIDER"),
        ("tts", "provider", "TTS_PROVIDER"),
        ("llm", "model", "LLM_MODEL"),
        ("stt", "model", "STT_MODEL"),
        ("tts", "model", "TTS_MODEL"),
    ]
    for section, key, env_var in env_overrides:
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

    tts_voice = os.getenv("TTS_VOICE")
    if tts_voice:
        cfg.setdefault("tts", {}).setdefault("gemini", {})["voice"] = tts_voice

    lat = os.getenv("LAT")
    lon = os.getenv("LON")
    if lat:
        cfg["weather"]["lat"] = float(lat)
    if lon:
        cfg["weather"]["lon"] = float(lon)

    email_username = os.getenv("EMAIL_USERNAME")
    email_password = os.getenv("EMAIL_PASSWORD")
    if email_username:
        cfg.setdefault("email", {})["username"] = email_username
    if email_password:
        cfg.setdefault("email", {})["password"] = email_password

    email_enabled = os.getenv("EMAIL_ENABLED")
    if email_enabled:
        cfg.setdefault("email", {})["enabled"] = email_enabled.lower() == "true"

    return cfg
