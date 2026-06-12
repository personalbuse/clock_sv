from textual.app import App, ComposeResult
from textual.containers import Container

from src.core.orchestrator import Orchestrator
import locale
import subprocess

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
        self._ensure_pulseaudio()
        weather = self.query_one(WeatherWidget)
        wc = self.config.get("weather", {})
        weather.set_coords(wc.get("lat", 7.3742), wc.get("lon", -72.6477))

        status = self.query_one(StatusWidget)
        self.orchestrator = Orchestrator(self.config, status)
        self.orchestrator.start()

    @staticmethod
    def _ensure_pulseaudio() -> None:
        try:
            subprocess.run(
                ["pulseaudio", "--check"],
                capture_output=True, timeout=3,
            )
        except Exception:
            pass
        try:
            subprocess.run(
                ["pulseaudio", "--start"],
                capture_output=True, timeout=5,
            )
        except Exception:
            pass

    def key_x(self) -> None:
        if self.orchestrator:
            if self.orchestrator.state.name == "IDLE":
                self.orchestrator.press_ptt()
            elif self.orchestrator.state.name == "LISTENING":
                self.orchestrator.release_ptt()

    def key_c(self) -> None:
        if self.orchestrator:
            self.orchestrator.cancel()
