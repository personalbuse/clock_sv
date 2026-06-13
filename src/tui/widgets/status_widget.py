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
        self._logs: list[str] = []
        self._show_logs = False
        self._flash = False
        self.update_display()

    def set_state(self, state: str) -> None:
        self.state = state
        self._frame = 0
        self._flash = False
        self._restart_timer()
        self.update_display()

    def add_log(self, message: str) -> None:
        self._logs.append(message)
        if len(self._logs) > 15:
            self._logs.pop(0)
        if self._show_logs:
            self.update_display()

    def toggle_logs(self) -> None:
        self._show_logs = not self._show_logs
        self.update_display()

    def flash_cancel(self) -> None:
        if self._timer:
            self._timer.remove()
            self._timer = None
        self._flash = True
        self.set_timer(1.0, self._end_flash)
        self.update_display()

    def _end_flash(self) -> None:
        self._flash = False
        self.set_state(self.state)

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

    def _shape_and_color(self):
        if self._flash:
            return "CANCELADO", "#ff0000", FILL
        label, color, frames, _ = STATUS_MAP.get(self.state, STATUS_MAP["IDLE"])
        frame_idx = self._frame % len(frames)
        return label, color, frames[frame_idx]

    def update_display(self) -> None:
        label, color, shape = self._shape_and_color()
        content = Text()
        for i, line in enumerate(shape):
            if content:
                content.append("\n")
            content.append(Text(line, style=color))
            if i == 1:
                content.append(" ")
                content.append(Text(label, style=f"bold {color}"))

        if self._show_logs:
            for log in self._logs[-5:]:
                content.append("\n")
                content.append(Text(" " + log, style="#888888"))

        self.update(content)
        if self._show_logs:
            n = min(len(self._logs), 5)
            self.styles.height = 4 + n + 1
        else:
            self.styles.height = 4
