from rich.text import Text
from rich.style import Style
from textual.widgets import Static

from src.tui.gradient import apply_gradient

WHITE = (255, 255, 255)
GRAY = (136, 136, 136)


class StatusWidget(Static):
    def on_mount(self) -> None:
        self.state = "IDLE"
        self.log_lines = []
        self.update_display()

    def set_state(self, state: str) -> None:
        self.state = state
        self.update_display()

    def add_log(self, message: str) -> None:
        self.log_lines.append(message)
        if len(self.log_lines) > 10:
            self.log_lines.pop(0)
        self.update_display()

    def update_display(self) -> None:
        separator = Text(f"\n{'─' * 50}\n", style="#555555")
        state_text = apply_gradient(f"[{self.state}]", *WHITE, *GRAY)

        content = Text()
        content.append(separator)
        content.append(state_text)
        content.append("\n")

        for line in self.log_lines[-5:]:
            content.append(apply_gradient(line, *GRAY, *WHITE))
            content.append("\n")

        self.update(content)
