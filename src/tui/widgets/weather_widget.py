from rich.text import Text
from textual.widgets import Static

from src.tui.gradient import apply_gradient

WHITE = (255, 255, 255)
GRAY = (136, 136, 136)


class WeatherWidget(Static):
    def on_mount(self) -> None:
        self.temp = "--"
        self.description = "cargando..."
        self.set_interval(15, self.refresh)
        self.refresh()

    def refresh(self) -> None:
        text = f"{self.temp} C  Pamplona  {self.description}"
        self.update(apply_gradient(text, *WHITE, *GRAY))
