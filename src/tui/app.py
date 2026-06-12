from textual.app import App, ComposeResult

from src.utils.config import load_config
from src.tui.widgets.clock_widget import ClockWidget
from src.tui.widgets.weather_widget import WeatherWidget
from src.tui.widgets.status_widget import StatusWidget


class AssistantApp(App):
    CSS_PATH = "styles.tcss"

    def __init__(self, config: dict | None = None):
        super().__init__()
        self.config = config or load_config()

    def compose(self) -> ComposeResult:
        yield ClockWidget()
        yield WeatherWidget()
        yield StatusWidget()

    def on_mount(self) -> None:
        weather = self.query_one(WeatherWidget)
        wc = self.config.get("weather", {})
        weather.set_coords(wc.get("lat", 7.3742), wc.get("lon", -72.6477))

    def key_x(self) -> None:
        status = self.query_one(StatusWidget)
        status.set_state("LISTENING")
        status.add_log("Push-to-Talk activado")
