import requests

WEATHER_CODES = {
    0: "despejado", 1: "mayormente despejado", 2: "parcialmente nublado",
    3: "nublado", 45: "neblina", 48: "niebla helada",
    51: "llovizna ligera", 53: "llovizna", 55: "llovizna densa",
    61: "lluvia ligera", 63: "lluvia", 65: "lluvia fuerte",
    71: "nieve ligera", 73: "nieve", 75: "nieve fuerte",
    80: "chubascos ligeros", 81: "chubascos", 82: "chubascos fuertes",
    95: "tormenta", 96: "tormenta con granizo ligero", 99: "tormenta con granizo",
}


def get_weather(lat: float, lon: float) -> tuple[str, str]:
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current_weather=true"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data["current_weather"]
        temp = str(round(current["temperature"]))
        code = current.get("weathercode", 0)
        desc = WEATHER_CODES.get(code, "")
        return temp, desc
    except requests.RequestException:
        return "--", "error de conexion"
