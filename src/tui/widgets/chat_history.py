from rich.text import Text
from textual.widgets import Static


class ChatHistoryWidget(Static):
    def on_mount(self) -> None:
        self._visible = False
        self._conversations: list = []
        self._selected = 0
        self._manager = None
        self.update_display()

    def set_manager(self, manager) -> None:
        self._manager = manager

    def toggle(self) -> None:
        self._visible = not self._visible
        if self._visible:
            self.refresh_list()
        else:
            self.update_display()

    @property
    def is_visible(self) -> bool:
        return self._visible

    @property
    def selected_id(self) -> int | None:
        if not self._conversations:
            return None
        return self._conversations[self._selected].id

    def refresh_list(self) -> None:
        if not self._manager:
            return
        self._conversations = self._manager.conversations
        self._selected = 0
        self.update_display()

    def cursor_up(self) -> None:
        if self._conversations:
            self._selected = max(0, self._selected - 1)
            self.update_display()

    def cursor_down(self) -> None:
        if self._conversations:
            self._selected = min(len(self._conversations) - 1, self._selected + 1)
            self.update_display()

    def update_display(self) -> None:
        if not self._visible:
            self.update("")
            return
        lines = []
        lines.append("─" * 30)
        lines.append(" HISTORIAL (Enter=seleccionar, H=cerrar)")
        lines.append("─" * 30)
        for i, conv in enumerate(self._conversations):
            prefix = "\u25B6 " if i == self._selected else "  "
            text = f"{prefix}#{conv.id} {conv.summary}"
            style = "bold white" if i == self._selected else "#888888"
            lines.append(str(Text(text, style=style)))
        lines.append("─" * 30)
        self.update("\n".join(lines))
        self.styles.height = len(lines) + 1
