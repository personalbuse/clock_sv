from google import genai


def synthesize(text: str, api_key: str,
               model: str = "gemini-2.5-flash-preview-tts",
               voice: str = "es-ES-Standard-A") -> bytes:
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model,
            contents=text,
            config={
                "response_modality": ["AUDIO"],
                "voice_config": {"voice_name": voice},
            },
        )
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        return audio_data
    except Exception as e:
        raise RuntimeError(f"TTS failed: {e}") from e
