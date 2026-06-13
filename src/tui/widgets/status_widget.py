from rich.text import Text
from textual.widgets import Static

STATUS_MAP = {
    "IDLE":         ("INACTIVO",      "#666666"),
    "LISTENING":    ("ESCUCHANDO",    "#00ff88"),
    "TRANSCRIBING": ("TRANSCRIBIENDO","#ffcc00"),
    "THINKING":     ("PENSANDO",      "#4488ff"),
    "SPEAKING":     ("HABLANDO",      "#ffffff"),
}

class StatusWidget(Static):
    def on_mount(self) -> None:
        self.state = "IDLE"
        self._logs: list[str] = []
        self._show_logs = False
        self.update_display()

    def set_state(self, state: str) -> None:
        self.state = state
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

    def update_display(self) -> None:
        label, color = STATUS_MAP.get(self.state, STATUS_MAP["IDLE"])

        content = Text()
        content.append(Text("\u2B24", style=color))
        content.append(" ")
        content.append(Text(label, style=f"bold {color}"))

        if self._show_logs:
            for log in self._logs[-5:]:
                content.append("\n")
                content.append(Text(" " + log, style="#888888"))

        self.update(content)
        if self._show_logs:
            n = min(len(self._logs), 5)
            self.styles.height = 1 + n + 1
        else:
            self.styles.height = 2
