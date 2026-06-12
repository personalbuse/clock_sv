from duckduckgo_search import DDGS


TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Busca informacion actualizada en la web cuando la pregunta requiere datos recientes o desconocidos",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La consulta de busqueda en espanol",
                }
            },
            "required": ["query"],
        },
    },
}


def search(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No se encontraron resultados."
        lines = [f"Resultado {i+1}: {r['title']} - {r['href']}\n{r['body']}"
                 for i, r in enumerate(results)]
        return "\n\n".join(lines)
    except Exception as e:
        return f"Error en la busqueda: {e}"
