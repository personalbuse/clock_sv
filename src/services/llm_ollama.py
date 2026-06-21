import json
import re

import requests

from src.services.web_search import TOOL_DEF, search

SYSTEM_PROMPT = (
    "Eres un asistente de voz servidor inteligente. Responde siempre en "
    "espanol, de forma breve y directa. Tus respuestas no deben exceder "
    "3 oraciones para minimizar el tiempo de sintesis de voz. "
    "Si necesitas informacion actualizada, usa la herramienta web_search "
    "en lugar de escribir codigo o etiquetas. "
    "NUNCA incluyas <web_search>, JSON ni HTML en tu respuesta."
)


def warmup(endpoint: str = "http://localhost:11434",
           model: str = "qwen2.5:3b") -> None:
    try:
        requests.post(
            f"{endpoint}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "hola"}],
                "stream": False,
                "keep_alive": -1,
            },
            timeout=120,
        )
    except Exception:
        pass


def _extract_inline_query(text: str) -> str | None:
    m = re.search(r'<web_search\s+query=["\']([^"\']+)["\']\s*/>', text)
    if m:
        return m.group(1)
    m = re.search(r'web_search\s*[\(\[{]?\s*query\s*[=:]\s*["\']([^"\']+)["\']', text)
    if m:
        return m.group(1)
    return None


def ask(prompt: str, endpoint: str = "http://localhost:11434",
        model: str = "qwen2.5:3b", temperature: float = 0.7,
        max_tokens: int = 256, timeout: int = 120) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    searched = False

    try:
        for _ in range(3):
            body = {
                "model": model,
                "messages": messages,
                "stream": False,
                "keep_alive": -1,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
            if not searched:
                body["tools"] = [TOOL_DEF]

            resp = requests.post(
                f"{endpoint}/api/chat",
                json=body,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            msg = data["message"]
            content = (msg.get("content") or "").strip()

            if not searched:
                inline_q = _extract_inline_query(content)
                if inline_q:
                    content = re.sub(
                        r'<web_search\s+query=["\'][^"\']+["\']\s*/>',
                        "", content
                    ).strip()
                    result = search(inline_q)
                    searched = True
                    messages.append({
                        "role": "assistant",
                        "content": content or "(buscando...)"
                    })
                    messages.append({
                        "role": "user",
                        "content": (
                            f"Resultado de busqueda:\n{result}\n\n"
                            "Responde basandote en esto."
                        ),
                    })
                    continue

            tool_calls = msg.get("tool_calls")
            if tool_calls:
                searched = True
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [
                        {
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"],
                            }
                        }
                        for tc in tool_calls
                    ],
                })

                for tc in tool_calls:
                    if tc["function"]["name"] == "web_search":
                        args = tc["function"]["arguments"]
                        result = search(args["query"])
                        messages.append({
                            "role": "tool",
                            "content": result,
                        })
                continue

            if content:
                return content

        messages.append({
            "role": "user",
            "content": "Resume el resultado en espanol, maximo 3 oraciones.",
        })
        body = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        resp = requests.post(f"{endpoint}/api/chat", json=body, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        result = (data["message"].get("content") or "").strip()
        return result or "No tengo informacion suficiente para responder."
    except Exception as e:
        raise RuntimeError(f"Ollama LLM failed: {e}") from e
