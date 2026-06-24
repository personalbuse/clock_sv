from groq import Groq

SYSTEM_PROMPT = (
    "Eres un asistente de voz servidor inteligente. Responde siempre en "
    "espanol, de forma breve y directa. Tus respuestas no deben exceder "
    "3 oraciones para minimizar el tiempo de sintesis de voz."
)


def ask(prompt: str, api_key: str, model: str = "llama-3.1-8b-instant",
        temperature: float = 0.7, max_tokens: int = 512,
        timeout: int = 20) -> str:
    client = Groq(api_key=api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        response = client.chat.completions.create(
            model=model, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
            timeout=timeout,
        )
        result = (response.choices[0].message.content or "").strip()
        return result or "No tengo informacion suficiente para responder."
    except Exception as e:
        raise RuntimeError(f"LLM failed: {e}") from e
