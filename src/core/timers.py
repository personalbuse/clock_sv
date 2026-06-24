import threading
import time
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any


class TimerType(Enum):
    TIMER = auto()
    ALARM = auto()
    REMINDER = auto()


class TimerItem:
    def __init__(self, id: int, kind: TimerType, label: str,
                 target: datetime, message: str = ""):
        self.id = id
        self.kind = kind
        self.label = label
        self.target = target
        self.message = message
        self.active = True
        self.created = datetime.now()

    @property
    def remaining(self) -> timedelta:
        return self.target - datetime.now()

    @property
    def expired(self) -> bool:
        return self.active and datetime.now() >= self.target

    def __repr__(self) -> str:
        return f"[{self.id}] {self.label} -> {self.target.strftime('%H:%M:%S')}"


class TimerManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._timers: list[TimerItem] = []
        self._next_id = 1
        self._running = False
        self._thread: threading.Thread | None = None
        self._on_expire = None

    def set_callback(self, callback):
        self._on_expire = callback

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            expired = []
            with self._lock:
                for t in self._timers:
                    if t.expired:
                        t.active = False
                        expired.append(t)
                self._timers = [t for t in self._timers if t.active]
            for t in expired:
                if self._on_expire:
                    self._on_expire(t)
            time.sleep(1)

    def add_timer(self, minutes: int, label: str = "Temporizador") -> TimerItem:
        target = datetime.now() + timedelta(minutes=minutes)
        with self._lock:
            t = TimerItem(self._next_id, TimerType.TIMER, label, target)
            self._next_id += 1
            self._timers.append(t)
        return t

    def add_alarm(self, hour: int, minute: int, label: str = "Alarma") -> TimerItem | None:
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        with self._lock:
            t = TimerItem(self._next_id, TimerType.ALARM, label, target)
            self._next_id += 1
            self._timers.append(t)
        return t

    def add_reminder(self, minutes: int, message: str) -> TimerItem:
        target = datetime.now() + timedelta(minutes=minutes)
        with self._lock:
            t = TimerItem(self._next_id, TimerType.REMINDER,
                          f"Recordatorio: {message}", target, message)
            self._next_id += 1
            self._timers.append(t)
        return t

    def cancel(self, timer_id: int) -> bool:
        with self._lock:
            for t in self._timers:
                if t.id == timer_id:
                    t.active = False
                    self._timers.remove(t)
                    return True
        return False

    @property
    def active_timers(self) -> list[TimerItem]:
        with self._lock:
            return list(self._timers)

    def parse_command(self, text: str) -> tuple[str, Any] | None:
        t = text.lower().strip()

        m = __import__("re").search(r"temporizador\s+(\d+)\s*(minuto|minutos|segundo|segundos|hora|horas)", t)
        if m:
            val = int(m.group(1))
            unit = m.group(2)
            if unit in ("segundo", "segundos"):
                val = max(1, val // 60)
            elif unit in ("hora", "horas"):
                val *= 60
            timer = self.add_timer(val)
            label = f"{val} min"
            return (f"Temporizador de {label} iniciado, sonara a las {timer.target.strftime('%H:%M:%S')}", timer)

        m = __import__("re").search(r"alarma\s+a\s+las\s*(\d{1,2}):(\d{2})", t)
        if m:
            h, mn = int(m.group(1)), int(m.group(2))
            alarm = self.add_alarm(h, mn)
            if alarm:
                return (f"Alarma a las {h:02d}:{mn:02d}", alarm)
            return ("No se pudo crear la alarma", None)

        m = __import__("re").search(r"(?:recuérdame|recordatorio)\s+(.+?)\s+en\s+(\d+)\s*(minuto|minutos|hora|horas)", t)
        if m:
            msg, val, unit = m.group(1), int(m.group(2)), m.group(3)
            if unit in ("hora", "horas"):
                val *= 60
            reminder = self.add_reminder(val, msg)
            return (f"Recordatorio en {val} minutos: {msg}", reminder)

        m = __import__("re").search(r"(?:cancela|elimina)\s+(temporizador|alarma|recordatorio)", t)
        if m:
            kind = m.group(1)
            active = self.active_timers
            if not active:
                return ("No hay timers activos", None)
            for timer in active:
                if timer.kind.name.lower() == kind or kind == "temporizador":
                    self.cancel(timer.id)
                    return (f"{kind.capitalize()} cancelado", timer)
            return ("No se encontro timer de ese tipo", None)

        m = __import__("re").search(r"qu[eé]\s*(temporizadores|alertas|alarmas|timers) tengo", t)
        if m:
            active = self.active_timers
            if not active:
                return ("No hay timers activos", None)
            lines = [str(t) for t in active]
            return ("Timers activos: " + ", ".join(lines), active)

        return None
