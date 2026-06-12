from rich.text import Text
from rich.style import Style


def apply_gradient(text_str: str, r1: int, g1: int, b1: int,
                   r2: int, g2: int, b2: int, reverse: bool = False) -> Text:
    text = Text(text_str if not reverse else text_str)
    n = max(len(text_str) - 1, 1)
    for i, ch in enumerate(text_str):
        t = i / n
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        text.stylize(Style(color=f"#{r:02x}{g:02x}{b:02x}"), i, i + 1)
    return text


def gradient_lines(lines: list[str], r1: int, g1: int, b1: int,
                   r2: int, g2: int, b2: int, reverse: bool = False) -> list[Text]:
    result = []
    n = max(len(lines) - 1, 1)
    for i, line in enumerate(lines):
        t = i / n
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        result.append(Text(line, style=Style(color=f"#{r:02x}{g:02x}{b:02x}")))
    return result
