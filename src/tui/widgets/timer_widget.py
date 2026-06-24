import threading
from datetime import datetime

from rich.text import Text
from textual.widgets import Static


class TimerWidget(Static):
    def on_mount(self) -> None:
        self._items: list[dict] = []
        self.set_interval(1, self._refresh)
        self._update_widget()

    def set_timers(self, timers: list) -> None:
        self._items = [
            {
                "id": t.id,
                "label": t.label,
                "target": t.target,
            }
            for t in timers
        ]
        self._schedule_update()

    def _refresh(self) -> None:
        if self._items:
            self._schedule_update()

    def _schedule_update(self) -> None:
        if threading.current_thread() is threading.main_thread():
            self._update_widget()
        else:
            self.app.call_from_thread(self._update_widget)

    def _update_widget(self) -> None:
        if not self._items:
            self.update("")
            return
        lines = []
        for t in self._items:
            remaining = t["target"] - datetime.now()
            if remaining.total_seconds() <= 0:
                continue
            total_secs = int(remaining.total_seconds())
            h, r = divmod(total_secs, 3600)
            m, s = divmod(r, 60)
            if h > 0:
                time_str = f"{h}:{m:02d}:{s:02d}"
            else:
                time_str = f"{m}:{s:02d}"
            lines.append(f"  \u23F1 {t['label']} {time_str}")
        if lines:
            text = Text("\n").join(Text(line, style="bold #ff8800") for line in lines)
            self.update("\n" + str(text))
        else:
            self.update("")
