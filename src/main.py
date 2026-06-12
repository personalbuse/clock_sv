from src.utils.logging_config import setup_logging
from src.tui.app import AssistantApp


def main() -> None:
    setup_logging()
    app = AssistantApp()
    app.run()


if __name__ == "__main__":
    main()
