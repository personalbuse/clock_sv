import json
import re

from groq import Groq

from src.services.web_search import TOOL_DEF, search

SYSTEM_PROMPT = (
    "Eres un asistente de voz servidor inteligente. Responde siempre en "
    "espanol, de forma breve y directa. Tus respuestas no deben exceder "
    "3 oraciones para minimizar el tiempo de sintesis de voz. "
    "Si necesitas informacion actualizada, usa la herramienta web_search "
    "en lugar de escribir codigo o etiquetas. "
    "NUNCA incluyas <web_search>, JSON ni HTML en tu respuesta."
)


def _extract_inline_query(text: str) -> str | None:
    m = re.search(r'<web_search\s+query=["\']([^"\']+)["\']\s*/>', text)
    if m:
        return m.group(1)
    m = re.search(r'web_search\s*[\(\[{]?\s*query\s*[=:]\s*["\']([^"\']+)["\']', text)
    if m:
        return m.group(1)
    return None


def ask(prompt: str, api_key: str, model: str = "llama-3.1-8b-instant",
        temperature: float = 0.7, max_tokens: int = 512,
        timeout: int = 20) -> str:
    client = Groq(api_key=api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    searched = False

    try:
        for _ in range(3):
            kw = {} if searched else {"tools": [TOOL_DEF]}
            response = client.chat.completions.create(
                model=model, messages=messages,
                temperature=temperature, max_tokens=max_tokens,
                timeout=timeout, **kw,
            )
            msg = response.choices[0].message
            content = (msg.content or "").strip()

            # Check for inline <web_search query="..."> in text response
            if not searched:
                inline_q = _extract_inline_query(content)
                if inline_q:
                    content = re.sub(r'<web_search\s+query=["\'][^"\']+["\']\s*/>', "", content).strip()
                    result = search(inline_q)
                    searched = True
                    messages.append({"role": "assistant", "content": content or "(buscando...)"})
                    messages.append({"role": "user", "content": f"Resultado de busqueda:\n{result}\n\nResponde basandote en esto."})
                    continue

            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                searched = True
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name,
                                      "arguments": tc.function.arguments}}
                        for tc in tool_calls
                    ],
                })

                for tc in tool_calls:
                    if tc.function.name == "web_search":
                        args = json.loads(tc.function.arguments)
                        result = search(args["query"])
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        })

                continue

            if content:
                return content

        # última llamada sin tools
        messages.append({"role": "user",
                         "content": "Resume el resultado en español, máximo 3 oraciones."})
        response = client.chat.completions.create(
            model=model, messages=messages,
            temperature=temperature, max_tokens=max_tokens, timeout=timeout)
        result = (response.choices[0].message.content or "").strip()
        return result or "No tengo informacion suficiente para responder."
    except Exception as e:
        raise RuntimeError(f"LLM failed: {e}") from e
