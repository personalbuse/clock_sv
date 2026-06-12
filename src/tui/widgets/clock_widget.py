from datetime import datetime

import pyfiglet
from rich.text import Text
from textual.widgets import Static

from src.tui.gradient import gradient_lines

WHITE = (255, 255, 255)
DARK = (80, 80, 80)

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

        fig = pyfiglet.Figlet(font="big")
        clock_art = fig.renderText(time_str).rstrip("\n")
        lines = clock_art.split("\n")

        gradient_lines_list = gradient_lines(lines, *WHITE, *DARK, reverse=True)
        clock_rich = Text("\n").join(gradient_lines_list)

        max_width = max(len(l) for l in lines)
        date_padded = date_str.center(max_width)
        date_text = Text("\n" + date_padded, style="bold #aaaaaa")

        self.update(clock_rich + date_text)
