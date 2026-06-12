from rich.text import Text
from textual.widgets import Static

from src.services.weather_open_meteo import get_weather
from src.tui.gradient import apply_gradient

WHITE = (255, 255, 255)
GRAY = (136, 136, 136)


class WeatherWidget(Static):
    def on_mount(self) -> None:
        self.temp = "--"
        self.description = "cargando..."
        self.lat = 7.3742
        self.lon = -72.6477
        self.set_interval(15, self.fetch_weather)
        self.fetch_weather()

    def fetch_weather(self) -> None:
        self.temp, self.description = get_weather(self.lat, self.lon)
        self.render_content()

    def set_coords(self, lat: float, lon: float) -> None:
        self.lat = lat
        self.lon = lon
        self.fetch_weather()

    def render_content(self) -> None:
        text = f"{self.temp} C  Pamplona  {self.description}"
        self.update(apply_gradient(text, *WHITE, *GRAY))
