from datetime import datetime

from rich.text import Text
from textual.widgets import Static

SEP = "   "

DIGITS = {
    "0": ["██████", "██  ██", "██  ██", "██  ██", "██  ██", "██  ██", "██████"],
    "1": ["  ██  ", " ███  ", " ███  ", "  ██  ", "  ██  ", "  ██  ", " ████ "],
    "2": ["██████", "    ██", "    ██", "██████", "██    ", "██    ", "██████"],
    "3": ["██████", "    ██", "    ██", " █████", "    ██", "    ██", "██████"],
    "4": ["██  ██", "██  ██", "██  ██", "██████", "    ██", "    ██", "    ██"],
    "5": ["██████", "██    ", "██    ", "██████", "    ██", "    ██", "██████"],
    "6": ["██████", "██    ", "██    ", "██████", "██  ██", "██  ██", "██████"],
    "7": ["██████", "    ██", "   ██ ", "  ██  ", " ██   ", "██    ", "██    "],
    "8": ["██████", "██  ██", "██  ██", "██████", "██  ██", "██  ██", "██████"],
    "9": ["██████", "██  ██", "██  ██", "██████", "    ██", "    ██", "██████"],
    ":": ["      ", "  ██  ", "  ██  ", "      ", "  ██  ", "  ██  ", "      "],
}

DAYS_ES = [
    "lunes", "martes", "miercoles", "jueves",
    "viernes", "sabado", "domingo"
]


class ClockWidget(Static):
    def on_mount(self) -> None:
        self.set_interval(1, self.update_display)
        self.update_display()

    def update_display(self) -> None:
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")

        day_name = DAYS_ES[now.weekday()]
        date_str = f"{day_name}, {now.strftime('%d-%m-%y')}"

        rows = [""] * 7
        for i, ch in enumerate(time_str):
            glyph = DIGITS.get(ch, DIGITS["8"])
            for line_idx in range(7):
                if i > 0:
                    rows[line_idx] += SEP
                rows[line_idx] += glyph[line_idx]

        clock_text = Text("\n").join(
            Text(line, style="bold white") for line in rows
        )

        max_width = max(len(r) for r in rows)
        date_padded = date_str.center(max_width)
        date_text = Text("\n" + date_padded, style="bold #cccccc")

        self.update(clock_text + date_text)
