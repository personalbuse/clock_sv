from datetime import datetime

import pyfiglet
from rich.text import Text
from textual.widgets import Static

from src.tui.gradient import gradient_lines

WHITE = (255, 255, 255)
DARK = (80, 80, 80)
SEP = "  "

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

        fig = pyfiglet.Figlet(font="banner3")
        char_arts = []
        for ch in time_str:
            art = fig.renderText(ch).rstrip("\n")
            char_arts.append(art.split("\n"))

        nlines = len(char_arts[0])
        rows = [""] * nlines
        for i, char_lines in enumerate(char_arts):
            for line_idx in range(nlines):
                if i > 0:
                    rows[line_idx] += SEP
                rows[line_idx] += char_lines[line_idx].rstrip()

        gradient_lines_list = gradient_lines(rows, *WHITE, *DARK, reverse=True)
        clock_rich = Text("\n").join(gradient_lines_list)

        max_width = max(len(r) for r in rows)
        date_padded = date_str.center(max_width)
        date_text = Text("\n" + date_padded, style="bold #cccccc")

        self.update(clock_rich + date_text)
