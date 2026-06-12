from groq import Groq


def transcribe(audio_bytes: bytes, api_key: str,
               model: str = "whisper-large-v3-turbo",
               timeout: int = 10) -> str:
    client = Groq(api_key=api_key)
    import io
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.wav"

    try:
        response = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            language="es",
            response_format="text",
            timeout=timeout,
        )
        return response.strip() if response else ""
    except Exception as e:
        raise RuntimeError(f"STT failed: {e}") from e
