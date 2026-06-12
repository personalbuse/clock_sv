from textual.app import App, ComposeResult
from textual.containers import Container

from src.core.orchestrator import Orchestrator
from src.utils.config import load_config
from src.tui.widgets.clock_widget import ClockWidget
from src.tui.widgets.weather_widget import WeatherWidget
from src.tui.widgets.status_widget import StatusWidget


class AssistantApp(App):
    CSS_PATH = "styles.tcss"

    def __init__(self, config: dict | None = None):
        super().__init__()
        self.config = config or load_config()
        self.orchestrator: Orchestrator | None = None

    def compose(self) -> ComposeResult:
        with Container(id="main"):
            yield ClockWidget()
            yield WeatherWidget()
        yield StatusWidget()

    def on_mount(self) -> None:
        weather = self.query_one(WeatherWidget)
        wc = self.config.get("weather", {})
        weather.set_coords(wc.get("lat", 7.3742), wc.get("lon", -72.6477))

        status = self.query_one(StatusWidget)
        self.orchestrator = Orchestrator(self.config, status)
        self.orchestrator.start()

    def key_x(self) -> None:
        if self.orchestrator:
            if self.orchestrator.state.name == "IDLE":
                self.orchestrator.press_ptt()
            elif self.orchestrator.state.name == "LISTENING":
                self.orchestrator.release_ptt()
