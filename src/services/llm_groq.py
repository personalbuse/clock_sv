from groq import Groq

from src.services.web_search import TOOL_DEF, search

SYSTEM_PROMPT = (
    "Eres un asistente de voz servidor inteligente. Responde siempre en "
    "espanol, de forma breve y directa. Tus respuestas no deben exceder "
    "3 oraciones para minimizar el tiempo de sintesis de voz. "
    "Si necesitas informacion actualizada, usa la herramienta web_search."
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
        for _ in range(3):
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=[TOOL_DEF],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            choice = response.choices[0]
            msg = choice.message

            tool_calls = getattr(msg, "tool_calls", None)
            if not tool_calls:
                return msg.content.strip()

            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name,
                                  "arguments": tc.function.arguments}}
                    for tc in tool_calls
                ],
            })

            for tc in tool_calls:
                if tc.function.name == "web_search":
                    import json
                    args = json.loads(tc.function.arguments)
                    result = search(args["query"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"LLM failed: {e}") from e
