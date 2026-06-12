from datetime import datetime

from rich.text import Text
from textual.widgets import Static

from src.tui.gradient import gradient_lines

DIGITS = {
    "0": [
        "█████",
        "█   █",
        "█   █",
        "█   █",
        "█   █",
        "█   █",
        "█████",
    ],
    "1": [
        "  ██ ",
        " ███ ",
        "  ██ ",
        "  ██ ",
        "  ██ ",
        "  ██ ",
        "█████",
    ],
    "2": [
        "█████",
        "    █",
        "    █",
        "█████",
        "█    ",
        "█    ",
        "█████",
    ],
    "3": [
        "█████",
        "    █",
        "    █",
        " ████",
        "    █",
        "    █",
        "█████",
    ],
    "4": [
        "█   █",
        "█   █",
        "█   █",
        "█████",
        "    █",
        "    █",
        "    █",
    ],
    "5": [
        "█████",
        "█    ",
        "█    ",
        "█████",
        "    █",
        "    █",
        "█████",
    ],
    "6": [
        "█████",
        "█    ",
        "█    ",
        "█████",
        "█   █",
        "█   █",
        "█████",
    ],
    "7": [
        "█████",
        "    █",
        "   █ ",
        "  █  ",
        " █   ",
        "█    ",
        "█    ",
    ],
    "8": [
        "█████",
        "█   █",
        "█   █",
        "█████",
        "█   █",
        "█   █",
        "█████",
    ],
    "9": [
        "█████",
        "█   █",
        "█   █",
        "█████",
        "    █",
        "    █",
        "█████",
    ],
    ":": [
        "     ",
        " ███ ",
        " ███ ",
        "     ",
        " ███ ",
        " ███ ",
        "     ",
    ],
}

WHITE = (255, 255, 255)
DARK = (80, 80, 80)
SEP = "   "

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
            pattern = DIGITS.get(ch, DIGITS["8"])
            for line_idx in range(7):
                if i > 0:
                    rows[line_idx] += SEP
                rows[line_idx] += pattern[line_idx].rstrip()

        gradient_lines_list = gradient_lines(rows, *WHITE, *DARK, reverse=True)
        clock_rich = Text("\n").join(gradient_lines_list)

        date_text = Text("\n" + date_str, style="bold #cccccc")

        self.update(clock_rich + date_text)
