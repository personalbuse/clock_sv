from rich.text import Text
from textual.widgets import Static

FILL  = [" █ ", "███", " █ "]
HALF  = [" ▓ ", "▓▓▓", " ▓ "]
EMPTY = [" ░ ", "░█░", " ░ "]

STATUS_MAP = {
    "IDLE":         ("INACTIVO",      "#666666", [FILL],               0),
    "LISTENING":    ("ESCUCHANDO",    "#00ff88", [FILL, EMPTY],        0.3),
    "TRANSCRIBING": ("TRANSCRIBIENDO","#ffcc00", [FILL, HALF, EMPTY, HALF], 0.15),
    "THINKING":     ("PENSANDO",      "#4488ff", [FILL, HALF, EMPTY, HALF], 0.2),
    "SPEAKING":     ("HABLANDO",      "#ffffff", [FILL, EMPTY],        0.25),
}

class StatusWidget(Static):
    def on_mount(self) -> None:
        self.state = "IDLE"
        self._frame = 0
        self._timer = None
        self.update_display()

    def set_state(self, state: str) -> None:
        self.state = state
        self._frame = 0
        self._restart_timer()
        self.update_display()

    def add_log(self, _message: str) -> None:
        pass

    def _restart_timer(self) -> None:
        if self._timer:
            self._timer.remove()
            self._timer = None
        _, _, frames, interval = STATUS_MAP.get(self.state, STATUS_MAP["IDLE"])
        if len(frames) > 1 and interval > 0:
            self._timer = self.set_interval(interval, self._tick)

    def _tick(self) -> None:
        self._frame += 1
        self.update_display()

    def update_display(self) -> None:
        label, color, frames, _ = STATUS_MAP.get(self.state, STATUS_MAP["IDLE"])
        frame_idx = self._frame % len(frames)
        shape = frames[frame_idx]

        content = Text()
        for i, line in enumerate(shape):
            if content:
                content.append("\n")
            content.append(Text(line, style=color))
            if i == 1:
                content.append(" ")
                content.append(Text(label, style=f"bold {color}"))
        self.update(content)
