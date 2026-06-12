from groq import Groq


SYSTEM_PROMPT = (
    "Eres un asistente de voz servidor inteligente. Responde siempre en "
    "espanol, de forma breve y directa. Tus respuestas no deben exceder "
    "3 oraciones para minimizar el tiempo de sintesis de voz."
)


def ask(prompt: str, api_key: str, model: str = "llama-3.1-8b-instant",
        temperature: float = 0.7, max_tokens: int = 256,
        timeout: int = 15) -> str:
    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"LLM failed: {e}") from e
