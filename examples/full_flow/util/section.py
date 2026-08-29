"""Flow section marker."""

from __future__ import annotations


class PrintSectionName:
    """Marker item that prints a banner when encountered in the flow."""

    def __init__(self, name: str) -> None:
        self.name = name
