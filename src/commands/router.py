import re
import subprocess
import threading


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        out = r.stdout.strip()
        err = r.stderr.strip()
        return out or err or "ok"
    except subprocess.TimeoutExpired:
        return "comando tardó demasiado"
    except FileNotFoundError:
        return "comando no encontrado"
    except Exception as e:
        return str(e)


def _parse_duration(text: str) -> int | None:
    m = re.search(r"(\d+)\s*(minuto|minutos|m|hora|horas|h|segundo|segundos|s)", text)
    if not m:
        return None
    val = int(m.group(1))
    unit = m.group(2)
    if unit in ("hora", "horas", "h"):
        return val * 60
    if unit in ("segundo", "segundos", "s"):
        return max(1, val // 60)
    return val


def dispatch(text: str) -> tuple[str, bool] | None:
    t = text.lower().strip().strip(".,!¿?¡")

    if re.search(r"\bapágate\b", t) and not re.search(r"en\s+\d+", t):
        def _do():
            _run(["sudo", "-n", "shutdown", "-h", "now"])
        threading.Thread(target=_do, daemon=True).start()
        return ("Apagando el sistema ahora", True)

    m = re.search(r"\bapágate\s+en\b", t)
    if m:
        mins = _parse_duration(t)
        if mins:
            def _do(m=mins):
                _run(["sudo", "-n", "shutdown", "-h", f"+{m}"])
            threading.Thread(target=_do, daemon=True).start()
            return (f"Apagando el sistema en {mins} minutos", True)

    if re.search(r"\bcancela\s*(apagado|shutdown)\b", t):
        _run(["sudo", "-n", "shutdown", "-c"])
        return ("Apagado cancelado", True)

    if re.search(r"\b(dime|cuál\s*es|cuál es|muestra|dame|muéstrame)\s*mi\s*ip\b", t):
        out = _run(["ip", "-4", "a", "show"])
        ips = [ip for ip in re.findall(r"inet\s+(\d+\.\d+\.\d+\.\d+)", out) if not ip.startswith("127.")]
        wifi = [ip for ip in re.findall(r"inet\s+(\d+\.\d+\.\d+\.\d+)", _run(["ip", "-4", "a", "show", "wlp"])) if not ip.startswith("127.")]
        if wifi:
            return (f"Tu IP wifi es {wifi[0]}", True)
        if ips:
            return (f"Tu IP es {ips[0]}", True)
        return ("No pude obtener la IP", True)

    return None
