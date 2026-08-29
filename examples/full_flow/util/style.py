"""Terminal styling helpers."""

from __future__ import annotations


class Style:
    """ANSI color/style escape sequences."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"
    BG_BLUE = "\033[44m"


def color(text: str, *codes: str) -> str:
    """Wrap text in ANSI codes and reset."""
    return "".join(codes) + text + Style.RESET


def banner(text: str, width: int = 72, fill: str = "═") -> str:
    """Return a centered banner line."""
    pad = max(0, width - len(text) - 2)
    left = fill * (pad // 2)
    right = fill * (pad - len(left))
    return f"{left} {text} {right}"
